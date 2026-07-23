"""Approved-path-only atomic backups and integrity validation."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from repoos.errors import RepoOSError, backup_failure
from repoos.git import inspect_git, status_fingerprint, status_paths
from repoos.ownership import WRITABLE_OWNERSHIP, file_mode
from repoos.paths import contained_path, sha256_bytes
from repoos.planning import canonical_json_bytes
from repoos.redaction import contains_secret_like
from repoos.transactions import TransactionStore, isoformat, utc_now, write_json_atomic
from repoos.validation import validate_instance

FaultHook = Callable[[str], None]


def _inject(fault: FaultHook | None, point: str) -> None:
    if fault is not None:
        fault(point)


def _write_file(path: Path, content: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, mode)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _manifest_integrity(value: dict[str, Any]) -> str:
    body = dict(value)
    body.pop("integrity_sha256", None)
    return sha256_bytes(canonical_json_bytes(body))


def _failure(message: str, **details: Any) -> RepoOSError:
    return backup_failure(message, **details)


def create_backup(
    store: TransactionStore,
    record: dict[str, Any],
    plan: dict[str, Any],
    repository: Path,
    manifest_path: Path,
    *,
    fault: FaultHook | None = None,
) -> Path:
    """Build, validate, and atomically finalize a transaction backup directory."""

    transaction_id = str(record["transaction_id"])
    transaction_directory = store.directory(transaction_id)
    final = transaction_directory / "backup"
    if Path(str(record["backup_location"])).resolve() != final.resolve():
        raise _failure(
            "Backup location is outside the transaction state directory.",
            transaction_id=transaction_id,
        )
    if final.exists():
        raise _failure(
            "Transaction backup already exists.",
            transaction_id=transaction_id,
        )
    temporary = transaction_directory / f".backup-incomplete-{os.getpid()}-{time.time_ns()}"
    try:
        temporary.mkdir(mode=0o700)
        _inject(fault, "backup_directory_created")
        plan_bytes = canonical_json_bytes(plan)
        manifest_bytes = manifest_path.read_bytes()
        transaction_bytes = canonical_json_bytes(record)
        _write_file(temporary / "plan.json", plan_bytes)
        _write_file(temporary / "manifest.yaml", manifest_bytes)
        _write_file(temporary / "transaction.json", transaction_bytes)
        git_state = inspect_git(repository)
        target_state = {
            "target_head": git_state.head,
            "status_fingerprint": status_fingerprint(repository),
            "working_tree_clean": git_state.clean,
            "status_paths": list(status_paths(repository)),
        }
        write_json_atomic(temporary / "target-state.json", target_state)
        target_state_bytes = (temporary / "target-state.json").read_bytes()

        entries: list[dict[str, Any]] = []
        seen_targets: set[str] = set()
        writable_values = {item.value for item in WRITABLE_OWNERSHIP}
        for index, operation in enumerate(plan["operations"]):
            if operation["action"] == "preserve":
                continue
            target_name = str(operation["target"])
            ownership = str(operation["ownership"])
            if ownership not in writable_values:
                raise _failure(
                    "Backup plan includes an unowned write.",
                    target=target_name,
                    ownership=ownership,
                )
            if target_name in seen_targets:
                raise _failure("Backup plan repeats a target.", target=target_name)
            seen_targets.add(target_name)
            try:
                target = contained_path(repository, target_name)
            except RepoOSError as exc:
                raise _failure(
                    "Backup target is outside the fixture.",
                    target=target_name,
                    error_type=exc.error_type,
                ) from exc
            if target.is_symlink():
                raise _failure("Backup refuses a symlink target.", target=target_name)

            existed = target.exists()
            backup_path: str | None = None
            original_sha256: str | None = None
            original_mode: int | None = None
            if existed:
                if not target.is_file():
                    raise _failure(
                        "Backup target is not a regular file.",
                        target=target_name,
                    )
                original = target.read_bytes()
                if contains_secret_like(original.decode("utf-8", errors="ignore")):
                    raise _failure(
                        "Backup refuses secret-like target content.",
                        target=target_name,
                        failed_precondition="backup_secret_like_content",
                    )
                original_sha256 = sha256_bytes(original)
                if original_sha256 != operation["before_sha256"]:
                    raise _failure(
                        "Target changed before backup.",
                        target=target_name,
                        failed_precondition="target_changed",
                    )
                original_mode = file_mode(target)
                backup_path = f"files/{index:04d}.bin"
                _write_file(temporary / backup_path, original)
            elif operation["before_sha256"] is not None:
                raise _failure(
                    "Expected target disappeared before backup.",
                    target=target_name,
                    failed_precondition="target_changed",
                )

            section = operation.get("managed_section")
            entry = {
                "target": target_name,
                "action": operation["action"],
                "ownership": ownership,
                "existed": existed,
                "backup_path": backup_path,
                "original_sha256": original_sha256,
                "original_mode": original_mode,
                "expected_applied_sha256": operation["after_sha256"],
                "expected_applied_mode": operation["after_mode"],
                "managed_section": (
                    {
                        "start_marker": section["start_marker"],
                        "end_marker": section["end_marker"],
                        "before_section_sha256": section["before_section_sha256"],
                        "before_outside_sha256": section["before_outside_sha256"],
                    }
                    if isinstance(section, dict)
                    else None
                ),
            }
            entries.append(entry)
            _inject(fault, f"backup_entry:{target_name}")

        manifest: dict[str, Any] = {
            "schema_version": 1,
            "transaction_id": transaction_id,
            "complete": True,
            "created_at": isoformat(utc_now()),
            "target_head": record["target_head_planned"],
            "target_status_fingerprint": record["target_status_fingerprint"],
            "plan_sha256": sha256_bytes(plan_bytes),
            "manifest_sha256": sha256_bytes(manifest_bytes),
            "transaction_sha256": sha256_bytes(transaction_bytes),
            "target_state_sha256": sha256_bytes(target_state_bytes),
            "entries": entries,
            "restore_order": [entry["target"] for entry in reversed(entries)],
            "retention": {
                "policy": "manual",
                "preserve_until": None,
            },
        }
        manifest["integrity_sha256"] = _manifest_integrity(manifest)
        write_json_atomic(
            temporary / "backup-manifest.json",
            manifest,
            schema_name="backup-manifest",
        )
        validate_backup(
            temporary,
            transaction_record=record,
            allow_incomplete_directory=True,
        )
        _inject(fault, "backup_before_finalize")
        os.replace(temporary, final)
        directory_descriptor = os.open(transaction_directory, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        validate_backup(final, transaction_record=record)
        _inject(fault, "backup_finalized")
        return final
    except RepoOSError:
        raise
    except BaseException as exc:
        raise _failure(
            "Backup creation failed before target writes.",
            transaction_id=transaction_id,
            exception_type=type(exc).__name__,
            incomplete_backup=str(temporary),
        ) from exc


def validate_backup(
    backup_directory: Path,
    *,
    transaction_record: dict[str, Any] | None = None,
    allow_incomplete_directory: bool = False,
) -> dict[str, Any]:
    """Validate schema, manifest digest, snapshots, entry bytes, and restore order."""

    if (
        not backup_directory.is_dir()
        or backup_directory.is_symlink()
        or (
            backup_directory.name.startswith(".backup-incomplete")
            and not allow_incomplete_directory
        )
    ):
        raise _failure("Backup is missing, incomplete, or unsafe.", backup=str(backup_directory))
    manifest_path = backup_directory / "backup-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise _failure("Backup manifest is missing or unsafe.", backup=str(backup_directory))
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _failure(
            "Backup manifest could not be parsed.",
            exception_type=type(exc).__name__,
        ) from exc
    if not isinstance(value, dict):
        raise _failure("Backup manifest root is invalid.")
    findings = validate_instance(value, "backup-manifest", source=str(manifest_path))
    if findings:
        raise _failure(
            "Backup manifest failed schema validation.",
            findings=[finding.as_dict() for finding in findings],
        )
    if value["integrity_sha256"] != _manifest_integrity(value):
        raise _failure("Backup manifest integrity digest does not match.")

    plan_path = backup_directory / "plan.json"
    repository_manifest_path = backup_directory / "manifest.yaml"
    transaction_path = backup_directory / "transaction.json"
    target_state_path = backup_directory / "target-state.json"
    for snapshot in (
        plan_path,
        repository_manifest_path,
        transaction_path,
        target_state_path,
    ):
        if not snapshot.is_file() or snapshot.is_symlink():
            raise _failure("Required backup snapshot is missing.", snapshot=snapshot.name)
    if sha256_bytes(plan_path.read_bytes()) != value["plan_sha256"]:
        raise _failure("Backup plan snapshot digest does not match.")
    if sha256_bytes(repository_manifest_path.read_bytes()) != value["manifest_sha256"]:
        raise _failure("Backup manifest snapshot digest does not match.")
    if sha256_bytes(transaction_path.read_bytes()) != value["transaction_sha256"]:
        raise _failure("Backup transaction snapshot digest does not match.")
    if sha256_bytes(target_state_path.read_bytes()) != value["target_state_sha256"]:
        raise _failure("Backup target-state snapshot digest does not match.")
    try:
        transaction_snapshot = json.loads(transaction_path.read_text(encoding="utf-8"))
        target_state_snapshot = json.loads(target_state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _failure(
            "Backup metadata snapshot could not be parsed.",
            exception_type=type(exc).__name__,
        ) from exc
    if not isinstance(transaction_snapshot, dict) or validate_instance(
        transaction_snapshot,
        "transaction",
        source=str(transaction_path),
    ):
        raise _failure("Backup transaction snapshot is invalid.")
    expected_target_state = {
        "target_head": value["target_head"],
        "status_fingerprint": value["target_status_fingerprint"],
        "working_tree_clean": True,
        "status_paths": [],
    }
    if target_state_snapshot != expected_target_state:
        raise _failure("Backup target-state snapshot is invalid.")

    targets: list[str] = []
    for entry in value["entries"]:
        target = str(entry["target"])
        targets.append(target)
        existed = bool(entry["existed"])
        backup_path = entry["backup_path"]
        original_sha256 = entry["original_sha256"]
        original_mode = entry["original_mode"]
        if existed:
            if not isinstance(backup_path, str) or original_sha256 is None or original_mode is None:
                raise _failure("Existing backup entry lacks restoration metadata.", target=target)
            try:
                content_path = contained_path(
                    backup_directory,
                    backup_path,
                    must_exist=True,
                )
            except RepoOSError as exc:
                raise _failure(
                    "Backup content path is unsafe.",
                    target=target,
                ) from exc
            if content_path.is_symlink() or not content_path.is_file():
                raise _failure("Backup content is not a regular file.", target=target)
            if sha256_bytes(content_path.read_bytes()) != original_sha256:
                raise _failure("Backup content digest does not match.", target=target)
        elif backup_path is not None or original_sha256 is not None or original_mode is not None:
            raise _failure(
                "New-file backup entry contains impossible original metadata.",
                target=target,
            )
    if len(targets) != len(set(targets)):
        raise _failure("Backup contains duplicate target entries.")
    if value["restore_order"] != list(reversed(targets)):
        raise _failure("Backup restore order is not the reverse apply order.")

    if transaction_record is not None:
        if value["transaction_id"] != transaction_record["transaction_id"]:
            raise _failure("Backup transaction identity does not match.")
        if value["plan_sha256"] != transaction_record["plan_sha256"]:
            raise _failure("Backup plan digest does not match the transaction.")
        if value["manifest_sha256"] != transaction_record["manifest_sha256"]:
            raise _failure("Backup manifest digest does not match the transaction.")
        if value["target_head"] != transaction_record["target_head_planned"]:
            raise _failure("Backup target HEAD does not match the transaction.")
        if value["target_status_fingerprint"] != transaction_record["target_status_fingerprint"]:
            raise _failure("Backup target status does not match the transaction.")
        snapshot_contract = {
            "transaction_id": transaction_snapshot.get("transaction_id"),
            "plan_sha256": transaction_snapshot.get("plan_sha256"),
            "manifest_sha256": transaction_snapshot.get("manifest_sha256"),
            "target_head_planned": transaction_snapshot.get("target_head_planned"),
            "target_status_fingerprint": transaction_snapshot.get("target_status_fingerprint"),
        }
        current_contract = {
            "transaction_id": transaction_record["transaction_id"],
            "plan_sha256": transaction_record["plan_sha256"],
            "manifest_sha256": transaction_record["manifest_sha256"],
            "target_head_planned": transaction_record["target_head_planned"],
            "target_status_fingerprint": transaction_record["target_status_fingerprint"],
        }
        if snapshot_contract != current_contract:
            raise _failure("Backup transaction snapshot contract does not match.")
    return value


def backup_entry_map(backup_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(entry["target"]): entry for entry in backup_manifest["entries"]}
