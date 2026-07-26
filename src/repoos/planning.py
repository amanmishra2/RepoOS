"""Deterministic, fixture-bounded update planning and precondition checks."""

from __future__ import annotations

import fnmatch
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from repoos import __version__
from repoos.errors import (
    RepoOSError,
    authorization_required,
    conflict,
    invalid_input,
    unsafe_state,
    validation_error,
)
from repoos.git import inspect_git, is_git_worktree, status_fingerprint
from repoos.locks import repository_lock_path, require_lock_available
from repoos.ownership import (
    PRESERVED_OWNERSHIP,
    OwnershipMode,
    file_mode,
    line_change_counts,
    locate_managed_section,
    render_managed_file,
    render_managed_section,
)
from repoos.paths import contained_path, require_directory, sha256_bytes, sha256_file
from repoos.pause import get_pause_status
from repoos.redaction import contains_secret_like
from repoos.validation import load_document, validate_document, validate_instance

DEFAULT_MAX_FILES = 20
DEFAULT_MAX_BYTES = 1024 * 1024
DEFAULT_ALLOWED_PATH_PREFIXES = ("managed", "generated", "docs/managed")
DEFAULT_FORBIDDEN_PATH_PATTERNS = (
    ".git",
    ".git/*",
    "*/.git/*",
    ".env",
    ".env.*",
    "*/.env*",
    "*secret*",
    "*credential*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.log",
)
DEFAULT_COMPONENT = "fixture-component"


@dataclass(frozen=True, slots=True)
class SafetyLimits:
    max_files_changed: int = DEFAULT_MAX_FILES
    max_files_created: int = 5
    max_files_deleted: int = 0
    max_total_bytes_changed: int = DEFAULT_MAX_BYTES
    max_lines_added: int = 2000
    max_lines_removed: int = 2000
    max_percentage_repository_files_touched: float = 50.0
    allowed_path_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_PATH_PREFIXES
    forbidden_path_patterns: tuple[str, ...] = DEFAULT_FORBIDDEN_PATH_PATTERNS
    max_managed_sections_changed: int = 5

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["allowed_path_prefixes"] = list(self.allowed_path_prefixes)
        value["forbidden_path_patterns"] = list(self.forbidden_path_patterns)
        return value


def parse_file_spec(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise invalid_input("File mapping must use SOURCE=TARGET.", mapping=value)
    source, target = value.split("=", 1)
    if not source or not target:
        raise invalid_input("File mapping requires both source and target.", mapping=value)
    return source, target


def _component_mapping(value: str) -> tuple[str, str, str]:
    source, target = parse_file_spec(value)
    if "|" not in source:
        return DEFAULT_COMPONENT, source, target
    component, source_name = source.split("|", 1)
    if not component or not source_name:
        raise invalid_input("Component mapping must use COMPONENT|SOURCE=TARGET.", mapping=value)
    return component, source_name, target


def parse_section_spec(value: str) -> tuple[str, str, str, str, str]:
    fields = value.split("::")
    if len(fields) != 3:
        raise invalid_input(
            "Managed section must use [COMPONENT|]SOURCE=TARGET::START::END.",
            mapping=value,
        )
    component, source, target = _component_mapping(fields[0])
    start_marker, end_marker = fields[1:]
    if not start_marker or not end_marker:
        raise invalid_input("Managed-section markers cannot be empty.", mapping=value)
    return component, source, target, start_marker, end_marker


def parse_preserve_spec(value: str) -> tuple[str, str, OwnershipMode]:
    target_spec, mode_text = parse_file_spec(value)
    component = DEFAULT_COMPONENT
    target = target_spec
    if "|" in target_spec:
        component, target = target_spec.split("|", 1)
    try:
        mode = OwnershipMode(mode_text)
    except ValueError as exc:
        raise invalid_input("Unknown ownership mode.", ownership=mode_text) from exc
    if mode not in PRESERVED_OWNERSHIP:
        raise invalid_input(
            "Preserve entries require a non-writable ownership mode.",
            ownership=mode.value,
        )
    return component, target, mode


def _manifest(repository: Path) -> tuple[dict[str, Any], Path, bytes]:
    path = repository / ".repoos" / "project.yaml"
    if not path.is_file() or path.is_symlink():
        raise validation_error("Repository manifest is required.", path=str(path))
    findings = validate_document(path, "project-manifest")
    if findings:
        raise validation_error(
            "Repository manifest failed validation.",
            findings=[finding.as_dict() for finding in findings],
        )
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        value = yaml.safe_load(text)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise validation_error("Repository manifest could not be parsed.", reason=str(exc)) from exc
    if contains_secret_like(text):
        raise validation_error(
            "Repository manifest contains secret-like literal data.",
            failed_precondition="manifest_secret_like",
        )
    if not isinstance(value, dict):
        raise validation_error("Repository manifest root must be an object.")
    return value, path, raw


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_plan_id(plan_without_id: dict[str, Any]) -> str:
    return f"plan-{sha256_bytes(canonical_json_bytes(plan_without_id))}"


def plan_sha256(plan: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(plan))


def _operation_id(value: dict[str, Any]) -> str:
    return f"op-{sha256_bytes(canonical_json_bytes(value))[:16]}"


def _repository_file_count(repository: Path, *, maximum: int = 100_000) -> int:
    count = 0
    for root_text, directory_names, file_names in os.walk(repository, followlinks=False):
        root = Path(root_text)
        directory_names[:] = [
            name for name in directory_names if name != ".git" and not (root / name).is_symlink()
        ]
        count += len(file_names)
        count += sum(1 for name in directory_names if (root / name).is_symlink())
        if count > maximum:
            raise unsafe_state(
                "Fixture repository exceeds the bounded file inventory.",
                maximum=maximum,
            )
    return max(1, count)


def _target_bytes(target: Path) -> tuple[bytes | None, str | None, int | None]:
    if target.is_symlink():
        raise unsafe_state("Plan target is a symlink.", target=str(target))
    if not target.exists():
        return None, None, None
    if not target.is_file():
        raise conflict(
            "Plan target is not a regular file.",
            conflict_type="target_not_regular_file",
            target=str(target),
        )
    content = target.read_bytes()
    return content, sha256_bytes(content), file_mode(target)


def _full_file_operation(
    sources: Path,
    target_root: Path,
    mapping: str,
    ownership: OwnershipMode,
) -> dict[str, Any] | None:
    component, source_relative, target_relative = _component_mapping(mapping)
    source = contained_path(sources, source_relative, must_exist=True)
    if source.is_symlink() or not source.is_file():
        raise unsafe_state(
            "Plan sources must be regular non-symlink files.",
            source=source_relative,
        )
    target = contained_path(target_root, target_relative)
    before, before_digest, before_mode = _target_bytes(target)
    source_content = source.read_bytes()
    try:
        source_text = source_content.decode("utf-8")
    except UnicodeDecodeError:
        source_text = ""
    if source_text and contains_secret_like(source_text):
        raise validation_error(
            "Component source contains secret-like literal data.",
            failed_precondition="source_secret_like",
            source=source_relative,
        )
    rendered = render_managed_file(source_content, before)
    after_digest = sha256_bytes(rendered)
    if before_digest == after_digest:
        return None
    before_for_lines = before or b""
    added, removed = line_change_counts(before_for_lines, rendered)
    operation: dict[str, Any] = {
        "action": "replace" if before is not None else "create",
        "ownership": ownership.value,
        "component": component,
        "source": source_relative,
        "target": target_relative,
        "source_sha256": sha256_bytes(source_content),
        "before_sha256": before_digest,
        "after_sha256": after_digest,
        "before_mode": before_mode,
        "after_mode": before_mode if before_mode is not None else file_mode(source),
        "before_size_bytes": len(before_for_lines),
        "after_size_bytes": len(rendered),
        "line_stats": {"added": added, "removed": removed},
        "managed_section": None,
    }
    operation["operation_id"] = _operation_id(operation)
    return operation


def _section_operation(
    sources: Path,
    target_root: Path,
    value: str,
) -> dict[str, Any] | None:
    component, source_relative, target_relative, start_marker, end_marker = parse_section_spec(
        value
    )
    source = contained_path(sources, source_relative, must_exist=True)
    if source.is_symlink() or not source.is_file():
        raise unsafe_state(
            "Section source must be a regular non-symlink file.",
            source=source_relative,
        )
    target = contained_path(target_root, target_relative, must_exist=True)
    before, before_digest, before_mode = _target_bytes(target)
    if before is None or before_digest is None or before_mode is None:
        raise conflict(
            "Managed-section target must already exist.",
            conflict_type="managed_section_target_missing",
            target=target_relative,
        )
    source_content = source.read_bytes()
    try:
        source_text = source_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise conflict(
            "Managed-section source must be UTF-8 text.",
            conflict_type="managed_section_unsupported_encoding",
            source=source_relative,
        ) from exc
    if contains_secret_like(source_text):
        raise validation_error(
            "Managed-section source contains secret-like literal data.",
            failed_precondition="source_secret_like",
            source=source_relative,
        )
    rendered, before_layout = render_managed_section(
        before,
        source_content,
        start_marker,
        end_marker,
    )
    after_layout = locate_managed_section(rendered, start_marker, end_marker)
    after_digest = sha256_bytes(rendered)
    if before_digest == after_digest:
        return None
    added, removed = line_change_counts(before, rendered)
    operation: dict[str, Any] = {
        "action": "section_update",
        "ownership": OwnershipMode.MANAGED_SECTION.value,
        "component": component,
        "source": source_relative,
        "target": target_relative,
        "source_sha256": sha256_bytes(source_content),
        "before_sha256": before_digest,
        "after_sha256": after_digest,
        "before_mode": before_mode,
        "after_mode": before_mode,
        "before_size_bytes": len(before),
        "after_size_bytes": len(rendered),
        "line_stats": {"added": added, "removed": removed},
        "managed_section": {
            "start_marker": start_marker,
            "end_marker": end_marker,
            "before_section_sha256": before_layout.section_sha256,
            "before_outside_sha256": before_layout.outside_sha256,
            "after_section_sha256": after_layout.section_sha256,
        },
    }
    operation["operation_id"] = _operation_id(operation)
    return operation


def _preserve_operation(target_root: Path, value: str) -> dict[str, Any]:
    component, target_relative, ownership = parse_preserve_spec(value)
    target = contained_path(target_root, target_relative)
    before_digest: str | None = None
    before_mode: int | None = None
    before_size = 0
    if target.exists():
        if target.is_symlink():
            raise unsafe_state("Preserved target is a symlink.", target=target_relative)
        if not target.is_file():
            raise conflict(
                "Preserved target is not a regular file.",
                conflict_type="preserved_target_not_regular",
                target=target_relative,
            )
        before_mode = file_mode(target)
        before_size = target.stat().st_size
        if ownership is not OwnershipMode.EXCLUDED:
            before_digest = sha256_file(target)
    operation: dict[str, Any] = {
        "action": "preserve",
        "ownership": ownership.value,
        "component": component,
        "source": None,
        "target": target_relative,
        "source_sha256": None,
        "before_sha256": before_digest,
        "after_sha256": before_digest,
        "before_mode": before_mode,
        "after_mode": before_mode,
        "before_size_bytes": before_size,
        "after_size_bytes": before_size,
        "line_stats": {"added": 0, "removed": 0},
        "managed_section": None,
    }
    operation["operation_id"] = _operation_id(operation)
    return operation


def _safety_measurements(
    operations: list[dict[str, Any]],
    repository_file_count: int,
) -> dict[str, int | float]:
    writable = [item for item in operations if item["action"] != "preserve"]
    changed = len({str(item["target"]) for item in writable})
    created = sum(item["action"] == "create" for item in writable)
    deleted = sum(item["action"] == "delete" for item in writable)
    total_bytes = sum(
        max(int(item["before_size_bytes"]), int(item["after_size_bytes"])) for item in writable
    )
    lines_added = sum(int(item["line_stats"]["added"]) for item in writable)
    lines_removed = sum(int(item["line_stats"]["removed"]) for item in writable)
    sections = sum(item["ownership"] == OwnershipMode.MANAGED_SECTION.value for item in writable)
    percentage = round((changed / repository_file_count) * 100, 6)
    return {
        "files_changed": changed,
        "files_created": created,
        "files_deleted": deleted,
        "total_bytes_changed": total_bytes,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "percentage_repository_files_touched": percentage,
        "managed_sections_changed": sections,
    }


def safety_violations(
    operations: list[dict[str, Any]],
    limits: dict[str, Any],
    measurements: dict[str, Any],
) -> list[str]:
    violations: list[str] = []
    comparisons = {
        "max_files_changed": "files_changed",
        "max_files_created": "files_created",
        "max_files_deleted": "files_deleted",
        "max_total_bytes_changed": "total_bytes_changed",
        "max_lines_added": "lines_added",
        "max_lines_removed": "lines_removed",
        "max_percentage_repository_files_touched": "percentage_repository_files_touched",
        "max_managed_sections_changed": "managed_sections_changed",
    }
    for limit_name, measurement_name in comparisons.items():
        if measurements[measurement_name] > limits[limit_name]:
            violations.append(limit_name)
    prefixes = tuple(str(item).rstrip("/") for item in limits["allowed_path_prefixes"])
    patterns = tuple(str(item) for item in limits["forbidden_path_patterns"])
    for operation in operations:
        if operation["action"] == "preserve":
            continue
        target = str(operation["target"])
        if not any(target == prefix or target.startswith(f"{prefix}/") for prefix in prefixes):
            violations.append("allowed_path_prefixes")
        if any(fnmatch.fnmatchcase(target, pattern) for pattern in patterns):
            violations.append("forbidden_path_patterns")
    return sorted(set(violations))


def build_update_plan(
    repository: str | Path,
    source_root: str | Path,
    file_mappings: list[str],
    *,
    target_version: str,
    max_files: int = DEFAULT_MAX_FILES,
    max_bytes: int = DEFAULT_MAX_BYTES,
    generated_mappings: list[str] | None = None,
    section_mappings: list[str] | None = None,
    preserve_specs: list[str] | None = None,
    safety_limits: SafetyLimits | None = None,
) -> dict[str, Any]:
    """Build an immutable plan without writing the fixture or local state."""

    target_root = require_directory(repository)
    sources = require_directory(source_root)
    marker = target_root / ".repoos-fixture"
    if not marker.is_file() or marker.is_symlink():
        raise authorization_required(
            "Executable RepoOS planning is restricted to marked neutral fixtures.",
            repository=str(target_root),
        )
    if not is_git_worktree(target_root):
        raise validation_error("Fixture target must be a Git working tree.")

    manifest, manifest_path, manifest_raw = _manifest(target_root)
    project_id = manifest.get("project_id")
    from_version = manifest.get("repoos_version")
    manifest_version = manifest.get("manifest_version")
    if (
        not isinstance(project_id, str)
        or not isinstance(from_version, str)
        or not isinstance(manifest_version, int)
    ):
        raise validation_error(
            "Manifest is missing project_id, manifest_version, or repoos_version."
        )

    state = inspect_git(target_root)
    if state.head is None:
        raise validation_error("Fixture repository requires a committed HEAD.")
    conflicts: list[str] = []
    if not state.clean:
        conflicts.append("repository_dirty")
    permissions = manifest.get("automation_permissions")
    if not isinstance(permissions, dict) or permissions.get("apply") is not True:
        conflicts.append("manifest_apply_not_allowed")

    operations: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    mapping_groups = (
        (file_mappings, OwnershipMode.MANAGED_FILE),
        (generated_mappings or [], OwnershipMode.GENERATED_FILE),
    )
    for mappings, ownership in mapping_groups:
        for mapping in mappings:
            operation = _full_file_operation(sources, target_root, mapping, ownership)
            _component, _source, target = _component_mapping(mapping)
            if target in seen_targets:
                raise conflict(
                    "A plan may contain only one ownership operation per target.",
                    conflict_type="ownership_overlap",
                    target=target,
                )
            seen_targets.add(target)
            if operation is not None:
                operations.append(operation)

    for mapping in section_mappings or []:
        _component, _source, target, _start, _end = parse_section_spec(mapping)
        if target in seen_targets:
            raise conflict(
                "Multiple or overlapping managed operations for one file are unsupported.",
                conflict_type="managed_section_overlap",
                target=target,
            )
        seen_targets.add(target)
        operation = _section_operation(sources, target_root, mapping)
        if operation is not None:
            operations.append(operation)

    for value in preserve_specs or []:
        _component, target, _ownership = parse_preserve_spec(value)
        if target in seen_targets:
            raise conflict(
                "Writable and preserved ownership overlap.",
                conflict_type="ownership_overlap",
                target=target,
            )
        seen_targets.add(target)
        operations.append(_preserve_operation(target_root, value))

    operations.sort(key=lambda item: (str(item["target"]), str(item["operation_id"])))
    repository_files = _repository_file_count(target_root)
    limits_value = safety_limits or SafetyLimits(
        max_files_changed=max_files,
        max_total_bytes_changed=max_bytes,
    )
    limits = limits_value.as_dict()
    measurements = _safety_measurements(operations, repository_files)
    violations = safety_violations(operations, limits, measurements)
    verification = manifest.get("verification")
    if not isinstance(verification, list) or not verification:
        raise validation_error("Manifest requires at least one validation command.")

    body: dict[str, Any] = {
        "schema_version": 2,
        "plan_version": "repoos.update-plan.v2",
        "repoos_source_version": __version__,
        "project_id": project_id,
        "target_repository": str(target_root),
        "repository_path_sha256": sha256_bytes(str(target_root).encode("utf-8")),
        "source_root": str(sources),
        "source_root_sha256": sha256_bytes(str(sources).encode("utf-8")),
        "git_common_dir_sha256": sha256_bytes(str(state.common_dir).encode("utf-8")),
        "base_commit": state.head,
        "status_fingerprint": status_fingerprint(target_root),
        "repository_file_count": repository_files,
        "manifest": {
            "version": manifest_version,
            "sha256": sha256_bytes(manifest_raw),
        },
        "from_version": from_version,
        "to_version": target_version,
        "components": sorted({str(item["component"]) for item in operations}),
        "operations": operations,
        "validation_commands": verification,
        "safety": {
            "limits": limits,
            "measurements": measurements,
            "violations": violations,
        },
        "conflicts": sorted(set(conflicts)),
        "dry_run_default": True,
    }
    plan = {"plan_id": canonical_plan_id(body), **body}
    findings = validate_instance(plan, "update-plan", source="<generated-plan>")
    if findings:
        raise validation_error(
            "Generated update plan failed its schema.",
            findings=[finding.as_dict() for finding in findings],
        )
    if manifest_path.is_symlink():  # retained as an explicit defense after schema loading
        raise unsafe_state("Manifest path became a symlink during planning.")
    return plan


def write_plan(path: str | Path, plan: dict[str, Any]) -> Path:
    """Atomically write an explicit plan output outside the target mutation path."""

    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(plan, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, target)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return target


def read_plan(
    path: str | Path,
    *,
    schema_dir: str | Path | None = None,
    verify_digest: bool = True,
) -> dict[str, Any]:
    findings = validate_document(path, "update-plan", directory=schema_dir)
    if findings:
        raise validation_error(
            "Update plan failed schema validation.",
            findings=[finding.as_dict() for finding in findings],
        )
    value = load_document(path)
    if not isinstance(value, dict):
        raise validation_error("Update plan root must be an object.")
    expected = dict(value)
    plan_id = expected.pop("plan_id", None)
    if verify_digest and plan_id != canonical_plan_id(expected):
        raise validation_error("Update plan ID does not match canonical contents.")
    return value


def _operation_preconditions(
    operation: dict[str, Any],
    target_root: Path,
    sources: Path,
) -> list[str]:
    failures: list[str] = []
    source_name = operation.get("source")
    target_name = operation.get("target")
    ownership = operation.get("ownership")
    if not isinstance(target_name, str):
        return ["invalid_operation_path"]
    try:
        target = contained_path(target_root, target_name)
    except RepoOSError:
        return [f"unsafe_target_path:{target_name}"]
    if target.is_symlink():
        return [f"target_symlink:{target_name}"]
    if operation.get("action") == "preserve" and ownership == OwnershipMode.EXCLUDED.value:
        return failures

    if isinstance(source_name, str):
        try:
            source = contained_path(sources, source_name, must_exist=True)
        except RepoOSError:
            failures.append(f"source_missing_or_unsafe:{source_name}")
        else:
            if source.is_symlink() or not source.is_file():
                failures.append(f"source_not_regular:{source_name}")
            elif sha256_file(source) != operation.get("source_sha256"):
                failures.append(f"source_changed:{source_name}")
            elif operation.get("before_mode") is None and file_mode(source) != operation.get(
                "after_mode"
            ):
                failures.append(f"source_mode_changed:{source_name}")

    current_digest: str | None = None
    if target.exists():
        if not target.is_file():
            failures.append(f"target_not_regular:{target_name}")
            return failures
        current_digest = sha256_file(target)
    if current_digest != operation.get("before_sha256"):
        failures.append(f"target_changed:{target_name}")

    section = operation.get("managed_section")
    if (
        ownership == OwnershipMode.MANAGED_SECTION.value
        and isinstance(section, dict)
        and target.is_file()
    ):
        try:
            layout = locate_managed_section(
                target.read_bytes(),
                str(section["start_marker"]),
                str(section["end_marker"]),
            )
        except RepoOSError as exc:
            conflict_type = str(exc.details.get("conflict_type", "invalid_markers"))
            failures.append(f"managed_section_invalid:{target_name}:{conflict_type}")
        else:
            if layout.section_sha256 != section.get("before_section_sha256"):
                failures.append(f"managed_section_inside_changed:{target_name}")
            if layout.outside_sha256 != section.get("before_outside_sha256"):
                failures.append(f"managed_section_outside_changed:{target_name}")
    if operation.get("action") == "delete":
        failures.append(f"unsupported_delete:{target_name}")
    return failures


def _rebuild_operation_contract(
    operation: dict[str, Any],
    target_root: Path,
    sources: Path,
) -> dict[str, Any] | None:
    """Recompute one approved operation from current bytes without trusting its measurements."""

    component = str(operation["component"])
    target_relative = str(operation["target"])
    ownership = OwnershipMode(str(operation["ownership"]))
    target = contained_path(target_root, target_relative)
    before, before_digest, before_mode = _target_bytes(target)

    if operation["action"] == "preserve":
        if ownership not in PRESERVED_OWNERSHIP:
            raise conflict(
                "Preserve action uses a writable ownership mode.",
                conflict_type="ownership_mode_mismatch",
                target=target_relative,
            )
        before_size = len(before) if before is not None else 0
        preserved_digest = None if ownership is OwnershipMode.EXCLUDED else before_digest
        rebuilt: dict[str, Any] = {
            "action": "preserve",
            "ownership": ownership.value,
            "component": component,
            "source": None,
            "target": target_relative,
            "source_sha256": None,
            "before_sha256": preserved_digest,
            "after_sha256": preserved_digest,
            "before_mode": before_mode,
            "after_mode": before_mode,
            "before_size_bytes": before_size,
            "after_size_bytes": before_size,
            "line_stats": {"added": 0, "removed": 0},
            "managed_section": None,
        }
        rebuilt["operation_id"] = _operation_id(rebuilt)
        return rebuilt

    if operation["action"] == "delete":
        return None
    source_relative = operation.get("source")
    if not isinstance(source_relative, str):
        raise unsafe_state(
            "Writable operation has no valid source.",
            target=target_relative,
        )
    source = contained_path(sources, source_relative, must_exist=True)
    if source.is_symlink() or not source.is_file():
        raise unsafe_state(
            "Operation source is not a regular non-symlink file.",
            source=source_relative,
        )
    source_content = source.read_bytes()
    try:
        source_text = source_content.decode("utf-8")
    except UnicodeDecodeError:
        source_text = ""
    if source_text and contains_secret_like(source_text):
        raise validation_error(
            "Operation source contains secret-like literal data.",
            failed_precondition="source_secret_like",
            source=source_relative,
        )

    section_contract: dict[str, Any] | None = None
    if ownership is OwnershipMode.MANAGED_SECTION:
        if before is None or before_digest is None or before_mode is None:
            raise conflict(
                "Managed-section target must already exist.",
                conflict_type="managed_section_target_missing",
                target=target_relative,
            )
        section = operation.get("managed_section")
        if not isinstance(section, dict):
            raise conflict(
                "Managed-section contract is missing.",
                conflict_type="managed_section_contract_missing",
                target=target_relative,
            )
        start_marker = str(section["start_marker"])
        end_marker = str(section["end_marker"])
        rendered, before_layout = render_managed_section(
            before,
            source_content,
            start_marker,
            end_marker,
        )
        after_layout = locate_managed_section(rendered, start_marker, end_marker)
        action = "section_update"
        section_contract = {
            "start_marker": start_marker,
            "end_marker": end_marker,
            "before_section_sha256": before_layout.section_sha256,
            "before_outside_sha256": before_layout.outside_sha256,
            "after_section_sha256": after_layout.section_sha256,
        }
    elif ownership in {OwnershipMode.MANAGED_FILE, OwnershipMode.GENERATED_FILE}:
        rendered = render_managed_file(source_content, before)
        action = "replace" if before is not None else "create"
    else:
        raise conflict(
            "Writable action uses a non-writable ownership mode.",
            conflict_type="ownership_mode_mismatch",
            target=target_relative,
        )

    after_digest = sha256_bytes(rendered)
    if before_digest == after_digest:
        return None
    added, removed = line_change_counts(before or b"", rendered)
    rebuilt = {
        "action": action,
        "ownership": ownership.value,
        "component": component,
        "source": source_relative,
        "target": target_relative,
        "source_sha256": sha256_bytes(source_content),
        "before_sha256": before_digest,
        "after_sha256": after_digest,
        "before_mode": before_mode,
        "after_mode": before_mode if before_mode is not None else file_mode(source),
        "before_size_bytes": len(before or b""),
        "after_size_bytes": len(rendered),
        "line_stats": {"added": added, "removed": removed},
        "managed_section": section_contract,
    }
    rebuilt["operation_id"] = _operation_id(rebuilt)
    return rebuilt


def _revalidated_operation_contracts(
    operations: list[dict[str, Any]],
    target_root: Path,
    sources: Path,
) -> tuple[list[str], list[dict[str, Any]]]:
    failures: list[str] = []
    rebuilt: list[dict[str, Any]] = []
    for operation in operations:
        target_name = str(operation.get("target", "invalid"))
        if operation.get("action") == "delete":
            rebuilt.append(operation)
            continue
        try:
            actual = _rebuild_operation_contract(operation, target_root, sources)
        except RepoOSError as exc:
            failures.append(f"stale_operation_contract:{target_name}:{exc.error_type}")
            continue
        if actual is None or canonical_json_bytes(actual) != canonical_json_bytes(operation):
            failures.append(f"stale_operation_contract:{target_name}:mismatch")
            continue
        rebuilt.append(actual)
    return failures, rebuilt


def precondition_failures(
    plan: dict[str, Any],
    repository: str | Path,
    source_root: str | Path,
    *,
    state_directory: Path,
    safety_overrides: tuple[str, ...] = (),
    check_lock: bool = True,
) -> list[str]:
    """Return stable, content-free precondition identifiers."""

    failures: list[str] = []
    try:
        target_root = require_directory(repository)
        sources = require_directory(source_root)
    except RepoOSError as exc:
        return [f"invalid_input:{exc.error_type}"]

    expected = dict(plan)
    supplied_plan_id = expected.pop("plan_id", None)
    if supplied_plan_id != canonical_plan_id(expected):
        failures.append("plan_digest_mismatch")
    findings = validate_instance(plan, "update-plan", source="<approved-plan>")
    if findings:
        failures.append("plan_schema_invalid")
        return sorted(set(failures))

    pause = get_pause_status(state_directory)
    if pause.paused:
        failures.append(f"paused:{pause.source}")
    if str(target_root) != plan.get("target_repository"):
        failures.append("target_repository_path_mismatch")
    if sha256_bytes(str(target_root).encode("utf-8")) != plan.get("repository_path_sha256"):
        failures.append("target_repository_fingerprint_mismatch")
    if str(sources) != plan.get("source_root"):
        failures.append("source_root_path_mismatch")
    if sha256_bytes(str(sources).encode("utf-8")) != plan.get("source_root_sha256"):
        failures.append("source_root_fingerprint_mismatch")
    marker = target_root / ".repoos-fixture"
    if not marker.is_file() or marker.is_symlink():
        failures.append("fixture_marker_missing")
    if plan.get("repoos_source_version") != __version__:
        failures.append("unsupported_repoos_source_version")
    resolved_state = state_directory.expanduser().resolve()
    if resolved_state.is_relative_to(target_root):
        failures.append("unsafe_state_directory_inside_target")
    if resolved_state.is_relative_to(sources):
        failures.append("unsafe_state_directory_inside_source")

    manifest: dict[str, Any] | None = None
    try:
        manifest, _manifest_path, manifest_raw = _manifest(target_root)
    except RepoOSError as exc:
        failures.append(f"manifest_invalid:{exc.error_type}")
    else:
        if manifest.get("project_id") != plan.get("project_id"):
            failures.append("project_identity_mismatch")
        manifest_contract = plan.get("manifest")
        if not isinstance(manifest_contract, dict):
            failures.append("manifest_contract_invalid")
        else:
            if manifest.get("manifest_version") != manifest_contract.get("version"):
                failures.append("manifest_version_changed")
            if sha256_bytes(manifest_raw) != manifest_contract.get("sha256"):
                failures.append("manifest_changed")
        if manifest.get("repoos_version") != plan.get("from_version"):
            failures.append("manifest_repoos_version_changed")
        permissions = manifest.get("automation_permissions")
        if not isinstance(permissions, dict) or permissions.get("apply") is not True:
            failures.append("manifest_apply_not_allowed")

    if not is_git_worktree(target_root):
        failures.append("target_is_not_git")
        state = None
    else:
        state = inspect_git(target_root)
        if state.root != target_root:
            failures.append("target_git_root_mismatch")
        if not state.clean:
            failures.append("repository_dirty")
        if state.head != plan.get("base_commit"):
            failures.append("stale_base_commit")
        if status_fingerprint(target_root) != plan.get("status_fingerprint"):
            failures.append("status_fingerprint_changed")
        if sha256_bytes(str(state.common_dir).encode("utf-8")) != plan.get("git_common_dir_sha256"):
            failures.append("git_common_dir_changed")
        if check_lock:
            try:
                require_lock_available(repository_lock_path(state_directory, str(state.common_dir)))
            except RepoOSError as exc:
                failures.append(f"lock_conflict:{exc.error_type}")

    for conflict_name in plan.get("conflicts", []):
        failures.append(f"plan_conflict:{conflict_name}")
    safety = plan.get("safety")
    if isinstance(safety, dict):
        for violation in safety.get("violations", []):
            if violation not in safety_overrides:
                failures.append(f"safety_limit:{violation}")
    operations = plan.get("operations", [])
    contract_candidates: list[dict[str, Any]] = []
    for operation in operations:
        if isinstance(operation, dict):
            operation_failures = _operation_preconditions(operation, target_root, sources)
            failures.extend(operation_failures)
            if not operation_failures:
                contract_candidates.append(operation)
        else:
            failures.append("invalid_operation")
    typed_operations = [operation for operation in operations if isinstance(operation, dict)]
    contract_failures, rebuilt_operations = _revalidated_operation_contracts(
        contract_candidates,
        target_root,
        sources,
    )
    failures.extend(contract_failures)
    has_unsupported_delete = any(
        operation.get("action") == "delete" for operation in typed_operations
    )
    if (
        not contract_failures
        and not has_unsupported_delete
        and len(contract_candidates) == len(typed_operations)
        and len(rebuilt_operations) == len(typed_operations)
    ):
        current_file_count = _repository_file_count(target_root)
        if current_file_count != plan.get("repository_file_count"):
            failures.append("stale_repository_file_count")
        actual_measurements = _safety_measurements(rebuilt_operations, current_file_count)
        if not isinstance(safety, dict):
            failures.append("stale_safety_contract")
        else:
            limits = safety.get("limits")
            if not isinstance(limits, dict):
                failures.append("stale_safety_contract")
            else:
                actual_violations = safety_violations(
                    rebuilt_operations,
                    limits,
                    actual_measurements,
                )
                if safety.get("measurements") != actual_measurements:
                    failures.append("stale_safety_measurements")
                if safety.get("violations") != actual_violations:
                    failures.append("stale_safety_violations")
                for violation in actual_violations:
                    if violation not in safety_overrides:
                        failures.append(f"safety_limit:{violation}")
    return sorted(set(failures))


def apply_dry_run(
    plan: dict[str, Any],
    repository: str | Path,
    source_root: str | Path,
    *,
    state_directory: Path,
    safety_overrides: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Fully revalidate an approved plan without writing target or state."""

    failures = precondition_failures(
        plan,
        repository,
        source_root,
        state_directory=state_directory,
        safety_overrides=safety_overrides,
    )
    operations = [
        {
            "target": operation.get("target"),
            "action": operation.get("action"),
            "ownership": operation.get("ownership"),
            "component": operation.get("component"),
        }
        for operation in plan.get("operations", [])
        if isinstance(operation, dict)
    ]
    return {
        "schema_version": "repoos.apply-preview.v2",
        "plan_id": plan.get("plan_id"),
        "project_id": plan.get("project_id"),
        "dry_run": True,
        "would_apply": not failures,
        "operation_count": sum(item["action"] != "preserve" for item in operations),
        "operations": operations,
        "safety_overrides": sorted(set(safety_overrides)),
        "failures": failures,
        "writes_performed": 0,
        "state_writes_performed": 0,
        "commits_performed": 0,
        "pushes_performed": 0,
    }
