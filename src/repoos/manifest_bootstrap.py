"""Guarded planning and local authorization for first-time repository manifests."""

from __future__ import annotations

import getpass
import json
import os
import re
import stat
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from repoos import __version__
from repoos.errors import (
    ExitCode,
    RepoOSError,
    dirty_repository,
    invalid_input,
    unsafe_state,
)
from repoos.git import (
    inspect_git,
    inspect_worktree_topology,
    is_git_worktree,
    path_is_ignored,
    run_git,
    status_fingerprint,
    status_paths,
)
from repoos.locks import repository_lock_path, require_lock_available
from repoos.paths import canonical_path, require_directory, sha256_bytes
from repoos.pause import get_pause_status
from repoos.planning import canonical_json_bytes
from repoos.redaction import contains_secret_like
from repoos.transactions import isoformat, utc_now, write_json_atomic
from repoos.validation import load_document, validate_document, validate_instance

PLAN_VERSION = "repoos.manifest-bootstrap-plan.v1"
AUTHORIZATION_VERSION = "repoos.manifest-bootstrap-authorization.v1"
OPERATION_KIND = "manifest_bootstrap"
DESTINATION = ".repoos/project.yaml"
MANIFEST_MODE = 0o644
MAX_MANIFEST_BYTES = 65_536
MAX_MANIFEST_LINES = 1_000
MAX_YAML_NODES = 1_000
MAX_YAML_DEPTH = 20
MAX_AUTHORIZATION_SECONDS = 86_400
MIN_AUTHORIZATION_SECONDS = 60

VALIDATION_REQUIREMENTS = (
    "manifest_schema",
    "manifest_semantics",
    "installed_bytes",
    "repository_commands",
    "target_git_preservation",
    "sibling_worktree_preservation",
)
AUTHORIZATION_REQUIREMENTS = (
    "operation_kind",
    "target_repository",
    "target_worktree_id",
    "git_common_dir",
    "target_head",
    "target_branch",
    "plan_id",
    "plan_digest",
    "manifest_sha256",
    "destination",
    "created_at",
    "expires_at",
    "authorizer",
)
_ALLOWED_VALIDATION_EXECUTABLES = {
    "make",
    "mypy",
    "pytest",
    "ruff",
}
_ALLOWED_PYTHON_MODULES = {"mypy", "pytest", "ruff"}
_PYTHON_EXECUTABLE = re.compile(r"^python(?:3(?:\.[0-9]+)?)?$")
_IMMUTABLE_AUTHORIZATION_FIELDS = (
    "schema_version",
    "authorization_version",
    "operation_kind",
    "target_repository",
    "target_worktree_id",
    "git_common_dir",
    "target_head",
    "target_branch",
    "plan_id",
    "plan_digest",
    "manifest_sha256",
    "destination",
    "created_at",
    "expires_at",
    "authorizer",
)


def _bootstrap_error(
    message: str,
    *,
    code: ExitCode,
    error_type: str,
    **details: Any,
) -> RepoOSError:
    return RepoOSError(message, code, error_type, details)


def _invalid_manifest(message: str, **details: Any) -> RepoOSError:
    return _bootstrap_error(
        message,
        code=ExitCode.VALIDATION_FAILED,
        error_type="invalid_manifest",
        **details,
    )


def _canonical_digest(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _yaml_complexity(value: Any) -> tuple[int, int]:
    nodes = 0
    maximum_depth = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        maximum_depth = max(maximum_depth, depth)
        if nodes > MAX_YAML_NODES or maximum_depth > MAX_YAML_DEPTH:
            break
        if isinstance(current, dict):
            for key, item in current.items():
                stack.append((key, depth + 1))
                stack.append((item, depth + 1))
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)
    return nodes, maximum_depth


def _validation_command_violations(commands: Any) -> list[str]:
    violations: list[str] = []
    if not isinstance(commands, list):
        return ["verification_invalid"]
    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            violations.append(f"verification_command_invalid:{index}")
            continue
        argv = command.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(item, str) for item in argv)
        ):
            violations.append(f"verification_argv_invalid:{index}")
            continue
        executable = Path(argv[0]).name
        if Path(argv[0]).is_absolute():
            violations.append(f"verification_absolute_executable:{index}")
        if contains_secret_like("\n".join(argv)):
            violations.append(f"verification_secret_like:{index}")
        if executable in _ALLOWED_VALIDATION_EXECUTABLES:
            pass
        elif _PYTHON_EXECUTABLE.fullmatch(executable):
            if "-c" in argv[1:] or "-" in argv[1:]:
                violations.append(f"verification_inline_python:{index}")
            if "-m" in argv[1:]:
                module_index = argv.index("-m") + 1
                if (
                    argv.count("-m") != 1
                    or module_index != 2
                    or module_index >= len(argv)
                    or argv[module_index] not in _ALLOWED_PYTHON_MODULES
                ):
                    violations.append(f"verification_python_module:{index}")
        else:
            violations.append(f"verification_executable_not_allowed:{index}")
        for argument_index, argument in enumerate(argv[1:], start=1):
            if argument.startswith("-"):
                if not (
                    _PYTHON_EXECUTABLE.fullmatch(executable)
                    and argument == "-m"
                    and argument_index == 1
                ):
                    violations.append(f"verification_option_not_allowed:{index}")
                continue
            argument_path = Path(argument)
            if argument_path.is_absolute() or ".." in argument_path.parts or "\\" in argument:
                violations.append(f"verification_unsafe_path:{index}")
    return violations


def validate_bootstrap_manifest_bytes(
    raw: bytes,
    *,
    source: str = "<manifest-input>",
) -> dict[str, Any]:
    """Validate exact reviewed bytes and the bootstrap-only governance boundary."""

    if not raw or len(raw) > MAX_MANIFEST_BYTES:
        raise _invalid_manifest(
            "Manifest size is outside the bootstrap limit.",
            source=source,
            maximum_bytes=MAX_MANIFEST_BYTES,
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _invalid_manifest("Manifest must be UTF-8.", source=source) from exc
    if "\x00" in text or len(text.splitlines()) > MAX_MANIFEST_LINES:
        raise _invalid_manifest(
            "Manifest text exceeds the bootstrap complexity limit.",
            source=source,
        )
    if contains_secret_like(text):
        raise _invalid_manifest(
            "Manifest contains credential-like literal data.",
            source=source,
            violation="manifest_secret_like",
        )
    try:
        tokens = yaml.scan(text)
        for token in tokens:
            if type(token).__name__ in {"AliasToken", "AnchorToken", "TagToken"}:
                raise _invalid_manifest(
                    "Manifest YAML aliases, anchors, and explicit tags are unsupported.",
                    source=source,
                    violation="yaml_indirection",
                )
        value = yaml.safe_load(text)
    except RepoOSError:
        raise
    except yaml.YAMLError as exc:
        raise _invalid_manifest(
            "Manifest YAML could not be parsed.",
            source=source,
            exception_type=type(exc).__name__,
        ) from exc
    findings = validate_instance(value, "project-manifest", source=source)
    if findings:
        raise _invalid_manifest(
            "Manifest failed the project-manifest schema.",
            source=source,
            findings=[finding.as_dict() for finding in findings],
        )
    if not isinstance(value, dict):
        raise _invalid_manifest("Manifest root must be an object.", source=source)
    nodes, depth = _yaml_complexity(value)
    if nodes > MAX_YAML_NODES or depth > MAX_YAML_DEPTH:
        raise _invalid_manifest(
            "Manifest YAML exceeds the bounded node or depth limit.",
            source=source,
            nodes=nodes,
            depth=depth,
        )

    violations: list[str] = []
    if value.get("manifest_version") != 1:
        violations.append("unsupported_manifest_version")
    if value.get("repoos_version") != __version__:
        violations.append("unsupported_repoos_version")
    if value.get("adoption_channel") not in {"experimental", "canary"}:
        violations.append("unsupported_adoption_channel")
    if value.get("sensitivity_classification") not in {
        "public",
        "internal",
        "confidential",
        "personal_data",
        "restricted",
    }:
        violations.append("sensitivity_classification_required")
    if value.get("additional_overlays") != []:
        violations.append("bootstrap_overlays_not_allowed")
    if value.get("local_overrides") != []:
        violations.append("bootstrap_local_overrides_not_allowed")
    if value.get("last_successful_audit") is not None:
        violations.append("bootstrap_audit_evidence_not_allowed")

    components = value.get("components")
    if not isinstance(components, dict):
        violations.append("components_invalid")
    else:
        for key in ("managed", "generated", "extensions"):
            if components.get(key) != []:
                violations.append(f"bootstrap_{key}_not_allowed")
        for key in ("repository_owned", "excluded"):
            values = components.get(key)
            if not isinstance(values, list) or len(values) > 32:
                violations.append(f"bootstrap_{key}_too_broad")

    permissions = value.get("automation_permissions")
    expected_permissions = {
        "read_only": True,
        "plan": True,
        "apply": False,
        "commit": False,
        "push": False,
        "external_settings": False,
    }
    if permissions != expected_permissions:
        violations.append("bootstrap_automation_policy")
    violations.extend(_validation_command_violations(value.get("verification")))
    if violations:
        raise _invalid_manifest(
            "Manifest expands beyond the first-bootstrap governance boundary.",
            source=source,
            violations=sorted(set(violations)),
        )
    return value


def validate_bootstrap_manifest_file(path: str | Path) -> tuple[Path, bytes, dict[str, Any]]:
    supplied = Path(path).expanduser()
    if supplied.is_symlink():
        raise _invalid_manifest(
            "Manifest input must be a regular non-symlink file.",
            source=str(supplied),
        )
    candidate = canonical_path(supplied, must_exist=True)
    if not candidate.is_file():
        raise _invalid_manifest(
            "Manifest input must be a regular non-symlink file.",
            source=str(candidate),
        )
    try:
        raw = candidate.read_bytes()
    except OSError as exc:
        raise _invalid_manifest(
            "Manifest input could not be read.",
            source=str(candidate),
            exception_type=type(exc).__name__,
        ) from exc
    return candidate, raw, validate_bootstrap_manifest_bytes(raw, source=str(candidate))


def _repository_file_count(repository: Path, *, maximum: int = 100_000) -> int:
    count = 0
    for directory_text, directory_names, file_names in os.walk(repository, followlinks=False):
        directory = Path(directory_text)
        directory_names[:] = [
            name
            for name in directory_names
            if name != ".git" and not (directory / name).is_symlink()
        ]
        count += len(file_names)
        count += sum(1 for name in directory_names if (directory / name).is_symlink())
        if count > maximum:
            raise unsafe_state(
                "Repository exceeds the bounded manifest-bootstrap inventory.",
                maximum=maximum,
            )
    return max(1, count)


def _parent_entries(parent: Path, *, exclude: str | None = None) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    try:
        with os.scandir(parent) as iterator:
            for entry in iterator:
                if entry.name == exclude:
                    continue
                if entry.is_symlink():
                    kind = "symlink"
                elif entry.is_dir(follow_symlinks=False):
                    kind = "directory"
                elif entry.is_file(follow_symlinks=False):
                    kind = "file"
                else:
                    kind = "other"
                entries.append(
                    {
                        "name_sha256": sha256_bytes(entry.name.encode("utf-8")),
                        "kind": kind,
                    }
                )
    except OSError as exc:
        raise unsafe_state(
            "Manifest parent directory could not be inspected.",
            exception_type=type(exc).__name__,
        ) from exc
    entries.sort(key=lambda item: item["name_sha256"])
    return entries


def _parent_directory_state(repository: Path) -> dict[str, Any]:
    parent = repository / ".repoos"
    if parent.is_symlink():
        raise unsafe_state(
            "Manifest parent directory cannot be a symlink.",
            target=DESTINATION,
        )
    if not parent.exists():
        return {
            "state": "absent",
            "mode": None,
            "entry_count": 0,
            "entries_sha256": None,
        }
    if not parent.is_dir():
        raise unsafe_state(
            "Manifest parent path is not a directory.",
            target=DESTINATION,
        )
    entries = _parent_entries(parent)
    return {
        "state": "existing_directory",
        "mode": stat.S_IMODE(parent.stat(follow_symlinks=False).st_mode),
        "entry_count": len(entries),
        "entries_sha256": _canonical_digest(entries),
    }


def _assert_manifest_absent(repository: Path) -> None:
    destination = repository / DESTINATION
    if destination.is_symlink():
        raise unsafe_state(
            "Manifest destination cannot be a symlink.",
            target=DESTINATION,
        )
    if destination.exists():
        raise _bootstrap_error(
            "Repository manifest already exists and cannot be replaced.",
            code=ExitCode.CONFLICT,
            error_type="existing_manifest",
            destination=DESTINATION,
        )


def _registered_worktree_paths(repository: Path) -> tuple[Path, ...]:
    output = run_git(repository, ["worktree", "list", "--porcelain", "-z"])
    paths: list[Path] = []
    for field in output.split("\0"):
        if field.startswith("worktree "):
            try:
                paths.append(canonical_path(field.removeprefix("worktree "), must_exist=True))
            except RepoOSError as exc:
                raise _bootstrap_error(
                    "Registered worktree metadata is unreadable or malformed.",
                    code=ExitCode.UNSAFE_STATE,
                    error_type="sibling_ambiguity",
                    ambiguity=exc.error_type,
                ) from exc
    return tuple(paths)


def _assert_input_isolated(repository: Path, manifest_input: Path, common_dir: Path) -> None:
    assert_bootstrap_artifact_isolated(
        repository,
        manifest_input,
        common_dir,
        artifact_kind="Manifest input",
    )


def assert_bootstrap_artifact_isolated(
    repository: Path,
    artifact: Path,
    common_dir: Path,
    *,
    artifact_kind: str,
) -> None:
    """Refuse local artifacts beneath any worktree or shared Git metadata."""

    candidate = artifact.expanduser().resolve()
    if candidate.is_relative_to(common_dir):
        raise unsafe_state(f"{artifact_kind} must remain outside common Git metadata.")
    for worktree in _registered_worktree_paths(repository):
        if candidate.is_relative_to(worktree):
            raise unsafe_state(
                f"{artifact_kind} must remain outside every registered worktree.",
                worktree_id=sha256_bytes(str(worktree).encode("utf-8")),
            )


def _assert_supported_repository(repository: Path) -> None:
    if os.path.lexists(repository / ".repoos-fixture"):
        raise _bootstrap_error(
            "Manifest bootstrap is only for unmarked real repositories.",
            code=ExitCode.AUTHORIZATION_REQUIRED,
            error_type="real_repository_operation_refused",
        )
    if not is_git_worktree(repository):
        raise invalid_input("Manifest-bootstrap target must be a Git working tree.")
    if run_git(repository, ["rev-parse", "--is-bare-repository"]).strip() != "false":
        raise unsafe_state("Bare repositories are unsupported for manifest bootstrap.")
    if run_git(
        repository,
        ["rev-parse", "--show-superproject-working-tree"],
        allow_failure=True,
    ).strip():
        raise unsafe_state("Submodule worktrees are unsupported for manifest bootstrap.")
    if path_is_ignored(repository, DESTINATION):
        raise unsafe_state("Manifest destination must not be ignored by Git.", target=DESTINATION)


def _operation_id(operation: dict[str, Any]) -> str:
    return f"op-{_canonical_digest(operation)[:16]}"


def canonical_bootstrap_plan_digest(plan_without_identity: dict[str, Any]) -> str:
    return _canonical_digest(plan_without_identity)


def verify_bootstrap_plan_digest(plan: dict[str, Any]) -> bool:
    body = dict(plan)
    plan_id = body.pop("plan_id", None)
    plan_digest = body.pop("plan_digest", None)
    expected = canonical_bootstrap_plan_digest(body)
    return bool(plan_id == f"plan-{expected}" and plan_digest == expected)


def build_manifest_bootstrap_plan(
    repository: str | Path,
    manifest_input: str | Path,
) -> dict[str, Any]:
    """Build one deterministic, no-write manifest creation plan."""

    target = require_directory(repository)
    _assert_supported_repository(target)
    parent_state = _parent_directory_state(target)
    _assert_manifest_absent(target)
    input_path, raw, manifest = validate_bootstrap_manifest_file(manifest_input)

    state = inspect_git(target)
    if state.root != target:
        raise unsafe_state("Explicit target must be the Git worktree root.")
    if state.branch is None:
        raise unsafe_state("Detached targets are unsupported for manifest bootstrap.")
    if state.head is None:
        raise unsafe_state("Manifest-bootstrap target requires a committed HEAD.")
    if not state.clean:
        raise _bootstrap_error(
            "Manifest-bootstrap target must be clean.",
            code=ExitCode.DIRTY_REPOSITORY,
            error_type="dirty_target",
            tracked_changes=state.tracked_changes,
            untracked_entries=state.untracked_entries,
        )
    _assert_input_isolated(target, input_path, state.common_dir)
    try:
        topology = inspect_worktree_topology(target)
    except RepoOSError as exc:
        raise _bootstrap_error(
            "Sibling worktree state is locked, malformed, prunable, or ambiguous.",
            code=ExitCode.UNSAFE_STATE,
            error_type="sibling_ambiguity",
            ambiguity=exc.details.get("ambiguity", exc.error_type),
        ) from exc
    if topology["target"]["classification"] != "target_clean":
        raise dirty_repository("Manifest-bootstrap target must be clean.")
    if topology["common_git"]["transient_lock_count"] != 0:
        raise _bootstrap_error(
            "Common Git metadata contains an active or stale Git lock.",
            code=ExitCode.LOCKED,
            error_type="lock_conflict",
            lock_scope="common_git",
        )

    line_count = len(raw.decode("utf-8").splitlines())
    operation: dict[str, Any] = {
        "action": "create",
        "ownership": "adoption_manifest",
        "component": "repository-manifest",
        "source": "manifest-input.yaml",
        "target": DESTINATION,
        "source_sha256": sha256_bytes(raw),
        "before_sha256": None,
        "after_sha256": sha256_bytes(raw),
        "before_mode": None,
        "after_mode": MANIFEST_MODE,
        "before_size_bytes": 0,
        "after_size_bytes": len(raw),
        "line_stats": {"added": line_count, "removed": 0},
        "managed_section": None,
    }
    operation["operation_id"] = _operation_id(operation)
    repository_files = _repository_file_count(target)
    body: dict[str, Any] = {
        "schema_version": 1,
        "plan_version": PLAN_VERSION,
        "operation_kind": OPERATION_KIND,
        "repoos_source_version": __version__,
        "project_id": manifest["project_id"],
        "target_repository": str(target),
        "target_worktree": str(target),
        "repository_path_sha256": sha256_bytes(str(target).encode("utf-8")),
        "git_common_dir": str(state.common_dir),
        "git_common_dir_sha256": sha256_bytes(str(state.common_dir).encode("utf-8")),
        "target_branch": state.branch,
        "base_commit": state.head,
        "status_fingerprint": status_fingerprint(target),
        "target_worktree_state": topology["target"],
        "sibling_worktrees": topology["siblings"],
        "common_git_state": topology["common_git"],
        "manifest_input": str(input_path),
        "manifest_input_path_sha256": sha256_bytes(str(input_path).encode("utf-8")),
        "manifest": {
            "version": int(manifest["manifest_version"]),
            "sha256": sha256_bytes(raw),
            "size_bytes": len(raw),
        },
        "destination": DESTINATION,
        "expected_destination_state": "absent",
        "parent_directory": parent_state,
        "repository_file_count": repository_files,
        "components": ["repository-manifest"],
        "operations": [operation],
        "validation_commands": manifest["verification"],
        "safety": {
            "limits": {
                "max_files_changed": 1,
                "max_files_created": 1,
                "max_files_edited": 0,
                "max_files_deleted": 0,
                "max_manifest_bytes": MAX_MANIFEST_BYTES,
                "max_yaml_nodes": MAX_YAML_NODES,
                "max_yaml_depth": MAX_YAML_DEPTH,
                "allowed_destination": DESTINATION,
            },
            "measurements": {
                "files_changed": 1,
                "files_created": 1,
                "files_edited": 0,
                "files_deleted": 0,
                "manifest_bytes": len(raw),
                "manifest_lines": line_count,
            },
            "violations": [],
        },
        "validation_requirements": list(VALIDATION_REQUIREMENTS),
        "authorization_requirements": list(AUTHORIZATION_REQUIREMENTS),
        "dry_run_default": True,
    }
    digest = canonical_bootstrap_plan_digest(body)
    plan = {"plan_id": f"plan-{digest}", "plan_digest": digest, **body}
    findings = validate_instance(
        plan,
        "manifest-bootstrap-plan",
        source="<generated-manifest-bootstrap-plan>",
    )
    if findings:
        raise _bootstrap_error(
            "Generated manifest-bootstrap plan failed its schema.",
            code=ExitCode.VALIDATION_FAILED,
            error_type="invalid_manifest_bootstrap_plan",
            findings=[finding.as_dict() for finding in findings],
        )
    return plan


def read_manifest_bootstrap_plan(
    path: str | Path,
    *,
    verify_digest: bool = True,
) -> dict[str, Any]:
    findings = validate_document(path, "manifest-bootstrap-plan")
    if findings:
        raise _bootstrap_error(
            "Manifest-bootstrap plan failed schema validation.",
            code=ExitCode.VALIDATION_FAILED,
            error_type="invalid_manifest_bootstrap_plan",
            findings=[finding.as_dict() for finding in findings],
        )
    value = load_document(path)
    if not isinstance(value, dict):
        raise _bootstrap_error(
            "Manifest-bootstrap plan root must be an object.",
            code=ExitCode.VALIDATION_FAILED,
            error_type="invalid_manifest_bootstrap_plan",
        )
    if verify_digest and not verify_bootstrap_plan_digest(value):
        raise _bootstrap_error(
            "Manifest-bootstrap plan digest does not match canonical contents.",
            code=ExitCode.STALE_PLAN,
            error_type="stale_target",
            failed_precondition="plan_digest_mismatch",
        )
    return value


def _topology_failures(plan: dict[str, Any], target: Path) -> list[str]:
    try:
        topology = inspect_worktree_topology(target)
    except RepoOSError:
        return ["sibling_ambiguity"]
    failures: list[str] = []
    if topology["target"] != plan.get("target_worktree_state"):
        failures.append("target_worktree_state_changed")
    if topology["siblings"] != plan.get("sibling_worktrees"):
        failures.append("sibling_state_changed")
    if topology["common_git"] != plan.get("common_git_state"):
        failures.append("common_git_state_changed")
    return failures


def manifest_bootstrap_precondition_failures(
    plan: dict[str, Any],
    repository: str | Path,
    manifest_input: str | Path,
    *,
    state_directory: Path,
    check_lock: bool = True,
) -> list[str]:
    """Return stable, content-free bootstrap precondition identifiers."""

    failures: list[str] = []
    if not verify_bootstrap_plan_digest(plan):
        failures.append("plan_digest_mismatch")
    findings = validate_instance(
        plan,
        "manifest-bootstrap-plan",
        source="<approved-manifest-bootstrap-plan>",
    )
    if findings:
        failures.append("plan_schema_invalid")
        return sorted(set(failures))
    try:
        target = require_directory(repository)
        input_path = canonical_path(manifest_input, must_exist=True)
    except RepoOSError:
        return sorted(set([*failures, "invalid_input"]))

    if str(target) != plan.get("target_repository"):
        failures.append("target_repository_path_mismatch")
    if str(target) != plan.get("target_worktree"):
        failures.append("target_worktree_path_mismatch")
    if sha256_bytes(str(target).encode("utf-8")) != plan.get("repository_path_sha256"):
        failures.append("target_repository_fingerprint_mismatch")
    if str(input_path) != plan.get("manifest_input"):
        failures.append("manifest_input_path_mismatch")
    if sha256_bytes(str(input_path).encode("utf-8")) != plan.get("manifest_input_path_sha256"):
        failures.append("manifest_input_path_fingerprint_mismatch")
    if plan.get("repoos_source_version") != __version__:
        failures.append("unsupported_repoos_source_version")
    if (target / ".repoos-fixture").exists():
        failures.append("fixture_marker_present")

    resolved_state = state_directory.expanduser().resolve()
    pause = get_pause_status(resolved_state)
    if pause.paused:
        failures.append(f"paused:{pause.source}")

    try:
        input_path, raw, manifest = validate_bootstrap_manifest_file(input_path)
    except RepoOSError:
        failures.append("manifest_invalid")
        raw = b""
        manifest = {}
    else:
        if sha256_bytes(raw) != plan.get("manifest", {}).get("sha256"):
            failures.append("manifest_input_changed")
        if manifest.get("project_id") != plan.get("project_id"):
            failures.append("project_identity_mismatch")
        if manifest.get("manifest_version") != plan.get("manifest", {}).get("version"):
            failures.append("manifest_version_changed")

    try:
        _assert_manifest_absent(target)
    except RepoOSError as exc:
        failures.append(exc.error_type)
    try:
        parent_state = _parent_directory_state(target)
    except RepoOSError:
        failures.append("unsafe_parent_directory")
    else:
        if parent_state != plan.get("parent_directory"):
            failures.append("parent_directory_changed")

    if not is_git_worktree(target):
        failures.append("target_is_not_git")
        state = None
    else:
        try:
            state = inspect_git(target)
        except RepoOSError:
            failures.append("target_git_ambiguous")
            state = None
    if state is not None:
        if state.root != target:
            failures.append("target_git_root_mismatch")
        if not state.clean:
            failures.append("dirty_target")
        if state.head != plan.get("base_commit"):
            failures.append("target_head_changed")
        if state.branch != plan.get("target_branch"):
            failures.append("target_branch_changed")
        if status_fingerprint(target) != plan.get("status_fingerprint"):
            failures.append("target_status_changed")
        if str(state.common_dir) != plan.get("git_common_dir"):
            failures.append("git_common_dir_changed")
        if sha256_bytes(str(state.common_dir).encode("utf-8")) != plan.get("git_common_dir_sha256"):
            failures.append("git_common_dir_fingerprint_changed")
        if resolved_state.is_relative_to(state.common_dir):
            failures.append("unsafe_state_directory")
        try:
            assert_bootstrap_artifact_isolated(
                target,
                resolved_state,
                state.common_dir,
                artifact_kind="RepoOS state",
            )
        except RepoOSError as exc:
            if exc.error_type == "sibling_ambiguity":
                failures.append("sibling_ambiguity")
            else:
                failures.append("unsafe_state_directory")
        try:
            _assert_input_isolated(target, input_path, state.common_dir)
        except RepoOSError:
            failures.append("manifest_input_not_isolated")
        failures.extend(_topology_failures(plan, target))
        if check_lock:
            try:
                require_lock_available(repository_lock_path(resolved_state, str(state.common_dir)))
            except RepoOSError as exc:
                failures.append(f"lock_conflict:{exc.error_type}")

    if not failures:
        try:
            rebuilt = build_manifest_bootstrap_plan(target, input_path)
        except RepoOSError:
            failures.append("stale_plan_contract")
        else:
            if canonical_json_bytes(rebuilt) != canonical_json_bytes(plan):
                failures.append("stale_plan_contract")
    return sorted(set(failures))


def manifest_bootstrap_precondition_error(
    transaction_id: str,
    failures: list[str],
) -> RepoOSError:
    details = {"transaction_id": transaction_id, "failed_preconditions": failures}
    if "existing_manifest" in failures:
        return _bootstrap_error(
            "Repository manifest already exists.",
            code=ExitCode.CONFLICT,
            error_type="existing_manifest",
            **details,
        )
    if "manifest_invalid" in failures:
        return _invalid_manifest("Manifest input is no longer valid.", **details)
    if "dirty_target" in failures:
        return _bootstrap_error(
            "Manifest-bootstrap target is not clean.",
            code=ExitCode.DIRTY_REPOSITORY,
            error_type="dirty_target",
            **details,
        )
    if "sibling_ambiguity" in failures:
        return _bootstrap_error(
            "Sibling worktree state is locked, malformed, prunable, or ambiguous.",
            code=ExitCode.UNSAFE_STATE,
            error_type="sibling_ambiguity",
            **details,
        )
    if any(failure.startswith("lock_conflict:") for failure in failures):
        lock_type = next(
            failure.split(":", 1)[1] for failure in failures if failure.startswith("lock_conflict:")
        )
        return _bootstrap_error(
            "Another RepoOS operation owns the common-Git lock.",
            code=ExitCode.LOCKED,
            error_type=lock_type,
            **details,
        )
    if any(failure.startswith("paused:") for failure in failures):
        return _bootstrap_error(
            "RepoOS operations are paused.",
            code=ExitCode.PAUSED,
            error_type="paused",
            **details,
        )
    stale_prefixes = (
        "plan_",
        "target_",
        "manifest_input_",
        "manifest_version_",
        "project_identity_",
        "parent_directory_",
        "git_common_",
        "common_git_",
        "sibling_state_",
        "stale_",
        "unsupported_repoos_",
    )
    if any(failure.startswith(stale_prefixes) for failure in failures):
        return _bootstrap_error(
            "Approved manifest-bootstrap target is stale.",
            code=ExitCode.STALE_PLAN,
            error_type="stale_target",
            **details,
        )
    return _bootstrap_error(
        "Manifest-bootstrap preconditions failed.",
        code=ExitCode.UNSAFE_STATE,
        error_type="unsafe_manifest_bootstrap",
        **details,
    )


def manifest_bootstrap_dry_run(
    plan: dict[str, Any],
    repository: str | Path,
    manifest_input: str | Path,
    *,
    state_directory: Path,
    authorization_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    failures = manifest_bootstrap_precondition_failures(
        plan,
        repository,
        manifest_input,
        state_directory=state_directory,
    )
    authorization_status = "missing"
    if authorization_path is not None:
        try:
            validate_manifest_bootstrap_authorization(
                authorization_path,
                plan,
                now=now,
            )
        except RepoOSError as exc:
            authorization_status = exc.error_type
        else:
            authorization_status = "valid"
    return {
        "schema_version": "repoos.manifest-bootstrap-preview.v1",
        "operation_kind": OPERATION_KIND,
        "plan_id": plan.get("plan_id"),
        "plan_digest": plan.get("plan_digest"),
        "manifest_sha256": plan.get("manifest", {}).get("sha256"),
        "destination": DESTINATION,
        "dry_run": True,
        "preconditions_pass": not failures,
        "ready_for_authorization": not failures,
        "authorization_status": authorization_status,
        "would_apply": not failures and authorization_status == "valid",
        "authorization_requirements": list(AUTHORIZATION_REQUIREMENTS),
        "protected_sibling_count": len(plan.get("sibling_worktrees", [])),
        "protected_dirty_sibling_count": sum(
            item.get("classification") == "protected_dirty"
            for item in plan.get("sibling_worktrees", [])
            if isinstance(item, dict)
        ),
        "failures": failures,
        "writes_performed": 0,
        "state_writes_performed": 0,
        "commits_performed": 0,
        "pushes_performed": 0,
    }


def _authorization_binding(value: dict[str, Any]) -> dict[str, Any]:
    return {key: value.get(key) for key in _IMMUTABLE_AUTHORIZATION_FIELDS}


def authorization_digest(value: dict[str, Any]) -> str:
    return _canonical_digest(_authorization_binding(value))


def _authorization_identity() -> dict[str, Any]:
    uid = int(getattr(os, "getuid", lambda: 0)())
    identity = f"{uid}:{getpass.getuser()}"
    return {
        "uid": uid,
        "identity_sha256": sha256_bytes(identity.encode("utf-8")),
    }


def _write_new_authorization(path: Path, value: dict[str, Any]) -> None:
    findings = validate_instance(
        value,
        "manifest-bootstrap-authorization",
        source=str(path),
    )
    if findings:
        raise _bootstrap_error(
            "Generated authorization failed schema validation.",
            code=ExitCode.VALIDATION_FAILED,
            error_type="invalid_authorization",
            findings=[finding.as_dict() for finding in findings],
        )
    if path.parent.is_symlink():
        raise _invalid_authorization("Authorization directory must not be a symlink.")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise _invalid_authorization("Authorization directory is unsafe.")
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def create_manifest_bootstrap_authorization(
    plan: dict[str, Any],
    *,
    state_directory: Path,
    expires_in_seconds: int,
    now: datetime | None = None,
) -> tuple[Path, dict[str, Any]]:
    if not MIN_AUTHORIZATION_SECONDS <= expires_in_seconds <= MAX_AUTHORIZATION_SECONDS:
        raise invalid_input(
            "Authorization lifetime is outside the bounded range.",
            minimum_seconds=MIN_AUTHORIZATION_SECONDS,
            maximum_seconds=MAX_AUTHORIZATION_SECONDS,
        )
    target = str(plan.get("target_repository", ""))
    manifest_input = str(plan.get("manifest_input", ""))
    failures = manifest_bootstrap_precondition_failures(
        plan,
        target,
        manifest_input,
        state_directory=state_directory,
    )
    if failures:
        raise manifest_bootstrap_precondition_error("authorization", failures)
    instant = (now or utc_now()).astimezone(UTC)
    value: dict[str, Any] = {
        "schema_version": 1,
        "authorization_version": AUTHORIZATION_VERSION,
        "operation_kind": OPERATION_KIND,
        "state": "approved",
        "target_repository": plan["target_repository"],
        "target_worktree_id": plan["target_worktree_state"]["worktree_id"],
        "git_common_dir": plan["git_common_dir"],
        "target_head": plan["base_commit"],
        "target_branch": plan["target_branch"],
        "plan_id": plan["plan_id"],
        "plan_digest": plan["plan_digest"],
        "manifest_sha256": plan["manifest"]["sha256"],
        "destination": DESTINATION,
        "created_at": isoformat(instant),
        "expires_at": isoformat(instant + timedelta(seconds=expires_in_seconds)),
        "authorizer": _authorization_identity(),
        "reserved_at": None,
        "reserved_transaction_id": None,
        "consumed_at": None,
        "outcome": None,
    }
    digest = authorization_digest(value)
    value["authorization_id"] = f"authorization-{digest}"
    authorization_root = state_directory.expanduser().resolve() / "authorizations"
    if authorization_root.is_symlink():
        raise _invalid_authorization("Authorization directory must not be a symlink.")
    output = authorization_root / f"{value['authorization_id']}.json"
    _write_new_authorization(output, value)
    return output, value


def _invalid_authorization(message: str, **details: Any) -> RepoOSError:
    return _bootstrap_error(
        message,
        code=ExitCode.AUTHORIZATION_REQUIRED,
        error_type="invalid_authorization",
        **details,
    )


def read_manifest_bootstrap_authorization(path: str | Path) -> tuple[Path, dict[str, Any]]:
    supplied = Path(path).expanduser()
    if supplied.is_symlink():
        raise _invalid_authorization("Authorization must be a regular non-symlink file.")
    candidate = supplied.resolve()
    if not candidate.exists():
        raise _bootstrap_error(
            "Manifest-bootstrap authorization is required.",
            code=ExitCode.AUTHORIZATION_REQUIRED,
            error_type="missing_authorization",
        )
    if candidate.is_symlink() or not candidate.is_file():
        raise _invalid_authorization("Authorization must be a regular non-symlink file.")
    try:
        value = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _invalid_authorization(
            "Authorization could not be parsed.",
            reason="malformed",
            exception_type=type(exc).__name__,
        ) from exc
    if not isinstance(value, dict):
        raise _invalid_authorization("Authorization root must be an object.")
    findings = validate_instance(
        value,
        "manifest-bootstrap-authorization",
        source=str(candidate),
    )
    if findings:
        raise _invalid_authorization(
            "Authorization failed schema validation.",
            findings=[finding.as_dict() for finding in findings],
        )
    digest = authorization_digest(value)
    if value.get("authorization_id") != f"authorization-{digest}":
        raise _invalid_authorization(
            "Authorization identity does not match its immutable binding.",
            reason="authorization_digest_mismatch",
        )
    state = value.get("state")
    lifecycle = (
        value.get("reserved_at"),
        value.get("reserved_transaction_id"),
        value.get("consumed_at"),
        value.get("outcome"),
    )
    if state == "approved" and lifecycle != (None, None, None, None):
        raise _invalid_authorization("Approved authorization has invalid lifecycle fields.")
    if state == "reserved" and (
        lifecycle[0] is None
        or lifecycle[1] is None
        or lifecycle[2] is not None
        or lifecycle[3] is not None
    ):
        raise _invalid_authorization("Reserved authorization has invalid lifecycle fields.")
    if state == "consumed" and (
        lifecycle[0] is None or lifecycle[1] is None or lifecycle[2] is None or lifecycle[3] is None
    ):
        raise _invalid_authorization("Consumed authorization has invalid lifecycle fields.")
    return candidate, value


def validate_manifest_bootstrap_authorization(
    path: str | Path,
    plan: dict[str, Any],
    *,
    now: datetime | None = None,
) -> tuple[Path, dict[str, Any], str]:
    candidate, value = read_manifest_bootstrap_authorization(path)
    expected = {
        "operation_kind": OPERATION_KIND,
        "target_repository": plan.get("target_repository"),
        "target_worktree_id": plan.get("target_worktree_state", {}).get("worktree_id"),
        "git_common_dir": plan.get("git_common_dir"),
        "target_head": plan.get("base_commit"),
        "target_branch": plan.get("target_branch"),
        "plan_id": plan.get("plan_id"),
        "plan_digest": plan.get("plan_digest"),
        "manifest_sha256": plan.get("manifest", {}).get("sha256"),
        "destination": DESTINATION,
    }
    mismatches = sorted(
        key for key, expected_value in expected.items() if value.get(key) != expected_value
    )
    if mismatches:
        raise _invalid_authorization(
            "Authorization does not bind the exact approved target and plan.",
            mismatched_fields=mismatches,
        )
    state = value["state"]
    if state == "consumed":
        raise _bootstrap_error(
            "Authorization has already been consumed.",
            code=ExitCode.AUTHORIZATION_REQUIRED,
            error_type="consumed_authorization",
        )
    if state == "reserved":
        raise _bootstrap_error(
            "Authorization is already reserved by another transaction.",
            code=ExitCode.AUTHORIZATION_REQUIRED,
            error_type="consumed_authorization",
            reserved_transaction_id=value["reserved_transaction_id"],
        )
    try:
        expires_at = datetime.fromisoformat(str(value["expires_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise _invalid_authorization("Authorization expiration is invalid.") from exc
    instant = (now or utc_now()).astimezone(UTC)
    if instant >= expires_at.astimezone(UTC):
        raise _bootstrap_error(
            "Authorization has expired.",
            code=ExitCode.AUTHORIZATION_REQUIRED,
            error_type="expired_authorization",
            expires_at=value["expires_at"],
        )
    return candidate, value, authorization_digest(value)


def reserve_manifest_bootstrap_authorization(
    path: Path,
    plan: dict[str, Any],
    transaction_id: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    candidate, value, _digest = validate_manifest_bootstrap_authorization(path, plan, now=now)
    value["state"] = "reserved"
    value["reserved_at"] = isoformat((now or utc_now()).astimezone(UTC))
    value["reserved_transaction_id"] = transaction_id
    write_json_atomic(
        candidate,
        value,
        schema_name="manifest-bootstrap-authorization",
    )
    return value


def consume_manifest_bootstrap_authorization(
    path: Path,
    transaction_id: str,
    *,
    outcome: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    candidate, value = read_manifest_bootstrap_authorization(path)
    if value["state"] == "consumed" and value["reserved_transaction_id"] == transaction_id:
        if value["outcome"] != outcome:
            value["outcome"] = outcome
            write_json_atomic(
                candidate,
                value,
                schema_name="manifest-bootstrap-authorization",
            )
        return value
    if value["state"] != "reserved" or value["reserved_transaction_id"] != transaction_id:
        raise _invalid_authorization(
            "Authorization is not reserved by this transaction.",
            transaction_id=transaction_id,
        )
    value["state"] = "consumed"
    value["consumed_at"] = isoformat((now or utc_now()).astimezone(UTC))
    value["outcome"] = outcome
    write_json_atomic(
        candidate,
        value,
        schema_name="manifest-bootstrap-authorization",
    )
    return value


def validate_post_install_preservation(plan: dict[str, Any], repository: Path) -> list[str]:
    failures: list[str] = []
    try:
        topology = inspect_worktree_topology(repository)
    except RepoOSError:
        return ["sibling_ambiguity"]
    if topology["siblings"] != plan["sibling_worktrees"]:
        failures.append("sibling_state_changed")
    if topology["common_git"] != plan["common_git_state"]:
        failures.append("common_git_state_changed")
    before = plan["target_worktree_state"]
    after = topology["target"]
    stable_keys = {
        "worktree_id",
        "head",
        "branch_sha256",
        "locked",
        "prunable",
        "git_dir_sha256",
        "head_metadata_sha256",
        "index_sha256",
    }
    if any(before[key] != after[key] for key in stable_keys):
        failures.append("target_git_metadata_changed")
    if after["tracked_changes"] != 0 or status_paths(repository) != (DESTINATION,):
        failures.append("unexpected_target_status")
    parent = repository / ".repoos"
    try:
        remaining = _parent_entries(parent, exclude="project.yaml")
    except RepoOSError:
        failures.append("parent_directory_changed")
    else:
        expected_parent = plan["parent_directory"]
        if expected_parent["state"] == "absent" and remaining:
            failures.append("parent_directory_changed")
        if expected_parent["state"] == "existing_directory" and (
            len(remaining) != expected_parent["entry_count"]
            or _canonical_digest(remaining) != expected_parent["entries_sha256"]
            or stat.S_IMODE(parent.stat(follow_symlinks=False).st_mode) != expected_parent["mode"]
        ):
            failures.append("parent_directory_changed")
    return sorted(set(failures))


def validate_restored_preservation(plan: dict[str, Any], repository: Path) -> list[str]:
    try:
        topology = inspect_worktree_topology(repository)
    except RepoOSError:
        return ["sibling_ambiguity"]
    failures: list[str] = []
    if topology["target"] != plan["target_worktree_state"]:
        failures.append("target_worktree_state_changed")
    if topology["siblings"] != plan["sibling_worktrees"]:
        failures.append("sibling_state_changed")
    if topology["common_git"] != plan["common_git_state"]:
        failures.append("common_git_state_changed")
    try:
        parent_state = _parent_directory_state(repository)
    except RepoOSError:
        failures.append("parent_directory_changed")
    else:
        if parent_state != plan["parent_directory"]:
            failures.append("parent_directory_changed")
    return failures


def remove_created_manifest_parent_if_safe(plan: dict[str, Any], repository: Path) -> bool:
    if plan["parent_directory"]["state"] != "absent":
        return False
    parent = repository / ".repoos"
    if parent.is_symlink():
        raise unsafe_state("Rollback refuses a symlinked manifest parent.")
    if not parent.exists():
        return False
    if not parent.is_dir():
        raise unsafe_state("Rollback manifest parent is not a directory.")
    try:
        parent.rmdir()
    except OSError:
        return False
    return True


def write_rendered_manifest(
    transaction_directory: Path,
    raw: bytes,
) -> Path:
    """Persist reviewed bytes outside the destination before the install boundary."""

    rendered_directory = transaction_directory / "rendered"
    rendered_directory.mkdir(mode=0o700)
    path = rendered_directory / "project.yaml"
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def install_manifest_exclusive(
    repository: Path,
    content: bytes,
    *,
    parent_expected_absent: bool,
    on_parent_created: Callable[[], None],
    on_manifest_created: Callable[[os.stat_result], None],
    fault: Any = None,
) -> tuple[Path, bool]:
    """Create the fixed manifest atomically without any overwrite primitive."""

    parent = repository / ".repoos"
    parent_created = False
    if parent.is_symlink():
        raise unsafe_state("Manifest parent became a symlink.")
    if parent_expected_absent:
        try:
            parent.mkdir(mode=0o755)
        except FileExistsError as exc:
            raise _bootstrap_error(
                "Manifest parent appeared before installation.",
                code=ExitCode.STALE_PLAN,
                error_type="stale_target",
                failed_precondition="parent_directory_changed",
            ) from exc
        else:
            parent_created = True
            on_parent_created()
            if fault is not None:
                fault("manifest_parent_created")
    elif not parent.exists():
        raise _bootstrap_error(
            "Manifest parent disappeared before installation.",
            code=ExitCode.STALE_PLAN,
            error_type="stale_target",
            failed_precondition="parent_directory_changed",
        )
    if not parent.is_dir() or parent.is_symlink():
        raise unsafe_state("Manifest parent is not a safe directory.")
    destination = repository / DESTINATION
    if destination.is_symlink() or destination.exists():
        raise _bootstrap_error(
            "Manifest destination appeared before installation.",
            code=ExitCode.STALE_PLAN,
            error_type="stale_target",
            failed_precondition="existing_manifest",
        )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".project.yaml.repoos-",
        suffix=".tmp",
        dir=parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, MANIFEST_MODE)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if fault is not None:
            fault("manifest_install_before_link")
        try:
            os.link(temporary, destination, follow_symlinks=False)
        except FileExistsError as exc:
            raise _bootstrap_error(
                "Manifest destination appeared during atomic installation.",
                code=ExitCode.STALE_PLAN,
                error_type="stale_target",
                failed_precondition="existing_manifest",
            ) from exc
        os.chmod(destination, MANIFEST_MODE, follow_symlinks=False)
        directory_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        on_manifest_created(destination.stat(follow_symlinks=False))
        if fault is not None:
            fault("manifest_install_after_link")
        return destination, parent_created
    finally:
        temporary.unlink(missing_ok=True)
