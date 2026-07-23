"""Deterministic, fixture-bounded update planning."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from repoos.errors import authorization_required, invalid_input, unsafe_state, validation_error
from repoos.git import inspect_git, is_git_worktree
from repoos.paths import contained_path, require_directory, sha256_bytes, sha256_file
from repoos.pause import get_pause_status
from repoos.validation import load_document, validate_document

DEFAULT_MAX_FILES = 20
DEFAULT_MAX_BYTES = 1024 * 1024


def parse_file_spec(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise invalid_input("File mapping must use SOURCE=TARGET.", mapping=value)
    source, target = value.split("=", 1)
    if not source or not target:
        raise invalid_input("File mapping requires both source and target.", mapping=value)
    return source, target


def _manifest(repository: Path) -> dict[str, Any]:
    path = repository / ".repoos" / "project.yaml"
    if not path.is_file():
        raise validation_error("Repository manifest is required.", path=str(path))
    findings = validate_document(path, "project-manifest")
    if findings:
        raise validation_error(
            "Repository manifest failed validation.",
            findings=[finding.as_dict() for finding in findings],
        )
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise validation_error("Repository manifest could not be parsed.", reason=str(exc)) from exc
    if not isinstance(value, dict):
        raise validation_error("Repository manifest root must be an object.")
    return value


def _canonical_plan_id(plan_without_id: dict[str, Any]) -> str:
    payload = json.dumps(
        plan_without_id,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"plan-{sha256_bytes(payload)}"


def build_update_plan(
    repository: str | Path,
    source_root: str | Path,
    file_mappings: list[str],
    *,
    target_version: str,
    max_files: int = DEFAULT_MAX_FILES,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    """Build a no-write plan. File mappings are intentionally fixture-only in v0.1.0."""

    target_root = require_directory(repository)
    sources = require_directory(source_root)
    manifest = _manifest(target_root)
    project_id = manifest.get("project_id")
    from_version = manifest.get("repoos_version")
    if not isinstance(project_id, str) or not isinstance(from_version, str):
        raise validation_error("Manifest is missing project_id or repoos_version.")

    if file_mappings and not (target_root / ".repoos-fixture").is_file():
        raise authorization_required(
            "RepoOS v0.1.0 permits explicit file planning only for marked neutral fixtures.",
            repository=str(target_root),
        )

    state = inspect_git(target_root) if is_git_worktree(target_root) else None
    conflicts: list[str] = []
    if state is None:
        conflicts.append("target_is_not_git")
        base_commit = None
    else:
        base_commit = state.head
        if not state.clean:
            conflicts.append("repository_dirty")

    operations: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for mapping in file_mappings:
        source_relative, target_relative = parse_file_spec(mapping)
        if target_relative in seen_targets:
            raise invalid_input("Duplicate target in plan.", target=target_relative)
        seen_targets.add(target_relative)
        source = contained_path(sources, source_relative, must_exist=True)
        if source.is_symlink() or not source.is_file():
            raise unsafe_state(
                "Plan sources must be regular non-symlink files.", source=source_relative
            )
        target = contained_path(target_root, target_relative)
        after_digest = sha256_file(source)
        if target.exists() and not target.is_file():
            conflicts.append(f"target_not_regular_file:{target_relative}")
            continue
        before_digest = (
            sha256_file(target) if target.is_file() and not target.is_symlink() else None
        )
        if target.is_symlink():
            conflicts.append(f"target_symlink:{target_relative}")
            continue
        if before_digest == after_digest:
            continue
        operations.append(
            {
                "action": "replace" if before_digest is not None else "create",
                "source": source_relative,
                "target": target_relative,
                "source_sha256": after_digest,
                "before_sha256": before_digest,
                "size_bytes": source.stat().st_size,
            }
        )

    operations.sort(key=lambda item: str(item["target"]))
    total_bytes = sum(int(item["size_bytes"]) for item in operations)
    if len(operations) > max_files:
        conflicts.append("max_files_exceeded")
    if total_bytes > max_bytes:
        conflicts.append("max_bytes_exceeded")

    body: dict[str, Any] = {
        "schema_version": 1,
        "project_id": project_id,
        "base_commit": base_commit,
        "from_version": from_version,
        "to_version": target_version,
        "operations": operations,
        "conflicts": sorted(set(conflicts)),
        "limits": {"max_files": max_files, "max_bytes": max_bytes},
        "dry_run_default": True,
    }
    return {"plan_id": _canonical_plan_id(body), **body}


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


def read_plan(path: str | Path, *, schema_dir: str | Path | None = None) -> dict[str, Any]:
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
    if plan_id != _canonical_plan_id(expected):
        raise validation_error("Update plan ID does not match canonical contents.")
    return value


def apply_dry_run(
    plan: dict[str, Any],
    repository: str | Path,
    source_root: str | Path,
    *,
    state_directory: Path,
) -> dict[str, Any]:
    """Revalidate a plan and report what execution would do without writing."""

    target_root = require_directory(repository)
    sources = require_directory(source_root)
    pause = get_pause_status(state_directory)
    manifest = _manifest(target_root)
    state = inspect_git(target_root) if is_git_worktree(target_root) else None
    failures: list[str] = list(plan.get("conflicts", []))

    if pause.paused:
        failures.append(f"paused:{pause.source}")
    if manifest.get("project_id") != plan.get("project_id"):
        failures.append("project_identity_mismatch")
    if state is None:
        failures.append("target_is_not_git")
    else:
        if not state.clean:
            failures.append("repository_dirty")
        if state.head != plan.get("base_commit"):
            failures.append("stale_base_commit")

    for operation in plan.get("operations", []):
        if not isinstance(operation, dict):
            failures.append("invalid_operation")
            continue
        source_name = operation.get("source")
        target_name = operation.get("target")
        if not isinstance(source_name, str) or not isinstance(target_name, str):
            failures.append("invalid_operation_path")
            continue
        source = contained_path(sources, source_name, must_exist=True)
        target = contained_path(target_root, target_name)
        if sha256_file(source) != operation.get("source_sha256"):
            failures.append(f"source_changed:{source_name}")
        current_digest = (
            sha256_file(target) if target.is_file() and not target.is_symlink() else None
        )
        if current_digest != operation.get("before_sha256"):
            failures.append(f"target_changed:{target_name}")

    unique_failures = sorted(set(failures))
    return {
        "schema_version": "repoos.apply-preview.v1",
        "plan_id": plan.get("plan_id"),
        "project_id": plan.get("project_id"),
        "dry_run": True,
        "would_apply": not unique_failures,
        "operation_count": len(plan.get("operations", [])),
        "failures": unique_failures,
        "writes_performed": 0,
        "commits_performed": 0,
        "pushes_performed": 0,
    }
