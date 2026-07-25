"""Persistent transaction state machine and public-safe outcome records."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from repoos import __version__
from repoos.errors import invalid_input, validation_error
from repoos.planning import canonical_json_bytes, plan_sha256
from repoos.validation import validate_instance

TRANSACTION_ID = re.compile(r"^tx-[0-9]{8}T[0-9]{6}Z-[a-f0-9]{12}$")
TERMINAL_STATES = {"completed", "rolled_back", "failed", "rollback_failed"}
TRANSITIONS: dict[str, frozenset[str]] = {
    "planned": frozenset({"validated", "failed"}),
    "validated": frozenset({"locked", "failed"}),
    "locked": frozenset({"backed_up", "failed"}),
    "backed_up": frozenset({"applying", "rolling_back", "failed"}),
    "applying": frozenset({"applied", "rolling_back", "failed"}),
    "applied": frozenset({"validating", "rolling_back"}),
    "validating": frozenset({"completed", "rolling_back"}),
    "completed": frozenset({"rolling_back"}),
    "rolling_back": frozenset({"rolled_back", "rollback_failed"}),
    "rolled_back": frozenset(),
    "failed": frozenset(),
    "rollback_failed": frozenset(),
}


def utc_now() -> datetime:
    return datetime.now(UTC)


def isoformat(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def new_transaction_id(
    plan_id: str,
    *,
    now: datetime | None = None,
    nonce: str | None = None,
) -> str:
    """Create a unique ID with deterministic output when clock and nonce are injected."""

    instant = (now or utc_now()).astimezone(UTC)
    unique = nonce or f"{os.getpid()}:{time.time_ns()}"
    suffix = hashlib.sha256(f"{plan_id}:{isoformat(instant)}:{unique}".encode()).hexdigest()[:12]
    return f"tx-{instant.strftime('%Y%m%dT%H%M%SZ')}-{suffix}"


def _write_bytes_atomic(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def write_json_atomic(
    path: Path,
    value: dict[str, Any],
    *,
    schema_name: str | None = None,
) -> None:
    if schema_name is not None:
        findings = validate_instance(value, schema_name, source=str(path))
        if findings:
            raise validation_error(
                "Generated state record failed schema validation.",
                schema=schema_name,
                findings=[finding.as_dict() for finding in findings],
            )
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _write_bytes_atomic(path, payload)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise invalid_input("Transaction record is missing or unsafe.", path=str(path))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise validation_error(
            "Transaction record could not be parsed.",
            path=str(path),
            exception_type=type(exc).__name__,
        ) from exc
    if not isinstance(value, dict):
        raise validation_error("Transaction record root must be an object.", path=str(path))
    return value


class TransactionStore:
    def __init__(self, state_directory: Path) -> None:
        self.state_directory = state_directory.expanduser().resolve()
        self.transactions_directory = self.state_directory / "transactions"

    def directory(self, transaction_id: str) -> Path:
        if TRANSACTION_ID.fullmatch(transaction_id) is None:
            raise invalid_input("Invalid transaction ID.", transaction_id=transaction_id)
        return self.transactions_directory / transaction_id

    def record_path(self, transaction_id: str) -> Path:
        return self.directory(transaction_id) / "transaction.json"

    def create(
        self,
        plan: dict[str, Any],
        *,
        safety_overrides: tuple[str, ...] = (),
        authorization_digest: str | None = None,
        authorization_path: str | None = None,
        now: datetime | None = None,
        transaction_id: str | None = None,
    ) -> dict[str, Any]:
        started = now or utc_now()
        identifier = transaction_id or new_transaction_id(str(plan["plan_id"]), now=started)
        directory = self.directory(identifier)
        try:
            directory.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise invalid_input(
                "Transaction ID already exists.",
                transaction_id=identifier,
            ) from exc

        affected_files = []
        for operation in plan["operations"]:
            if operation["action"] == "preserve":
                continue
            section = operation.get("managed_section")
            affected_files.append(
                {
                    "target": operation["target"],
                    "action": operation["action"],
                    "ownership": operation["ownership"],
                    "expected_pre_change_sha256": operation["before_sha256"],
                    "intended_post_change_sha256": operation["after_sha256"],
                    "applied_sha256": None,
                    "managed_section": (
                        {
                            "start_marker": section["start_marker"],
                            "end_marker": section["end_marker"],
                        }
                        if isinstance(section, dict)
                        else None
                    ),
                }
            )

        safety = plan["safety"]
        operation_kind = str(plan.get("operation_kind", "fixture_update"))
        record: dict[str, Any] = {
            "schema_version": 1,
            "transaction_id": identifier,
            "repoos_source_version": __version__,
            "target_repository_identifier": plan["project_id"],
            "target_repository_path": plan["target_repository"],
            "target_repository_path_sha256": plan["repository_path_sha256"],
            "target_head_planned": plan["base_commit"],
            "target_status_fingerprint": plan["status_fingerprint"],
            "manifest_version": plan["manifest"]["version"],
            "manifest_sha256": plan["manifest"]["sha256"],
            "update_plan_version": plan["plan_version"],
            "operation_kind": operation_kind,
            "git_common_dir_sha256": plan["git_common_dir_sha256"],
            "target_branch_planned": plan.get("target_branch"),
            "authorization_sha256": authorization_digest,
            "authorization_path": authorization_path,
            "protected_worktrees": plan.get("sibling_worktrees", []),
            "common_git_state": plan.get("common_git_state"),
            "parent_directory": plan.get("parent_directory"),
            "plan_id": plan["plan_id"],
            "plan_sha256": plan_sha256(plan),
            "components": plan["components"],
            "affected_files": affected_files,
            "backup_location": str(directory / "backup"),
            "started_at": isoformat(started),
            "completed_at": None,
            "state": "planned",
            "state_history": [{"state": "planned", "at": isoformat(started)}],
            "validation_commands": plan["validation_commands"],
            "validation_results": [],
            "rollback": {
                "state": "not_required",
                "started_at": None,
                "completed_at": None,
                "restored_files": 0,
                "failure_classification": None,
            },
            "failure": None,
            "safety": {
                "limits": safety["limits"],
                "measurements": safety["measurements"],
                "overrides": sorted(set(safety_overrides)),
                "violations": safety["violations"],
            },
            "duration_ms": None,
        }
        if operation_kind == "manifest_bootstrap":
            record["bootstrap_install"] = {
                "parent_created": False,
                "manifest_created": False,
                "manifest_device": None,
                "manifest_inode": None,
            }
        try:
            _write_bytes_atomic(directory / "plan.json", canonical_json_bytes(plan))
            write_json_atomic(directory / "transaction.json", record, schema_name="transaction")
        except BaseException:
            # The directory is intentionally retained as detectable incomplete state.
            raise
        return record

    def load(self, transaction_id: str) -> dict[str, Any]:
        record = _read_json(self.record_path(transaction_id))
        findings = validate_instance(
            record,
            "transaction",
            source=str(self.record_path(transaction_id)),
        )
        if findings:
            raise validation_error(
                "Transaction record failed schema validation.",
                transaction_id=transaction_id,
                findings=[finding.as_dict() for finding in findings],
            )
        return record

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        transaction_id = record.get("transaction_id")
        if not isinstance(transaction_id, str):
            raise invalid_input("Transaction record has no valid ID.")
        write_json_atomic(
            self.record_path(transaction_id),
            record,
            schema_name="transaction",
        )
        return record

    def update(
        self,
        transaction_id: str,
        updater: Callable[[dict[str, Any]], None],
    ) -> dict[str, Any]:
        record = self.load(transaction_id)
        updater(record)
        return self.save(record)

    def transition(
        self,
        transaction_id: str,
        new_state: str,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        if new_state not in TRANSITIONS:
            raise invalid_input("Unknown transaction state.", state=new_state)
        instant = now or utc_now()
        record = self.load(transaction_id)
        current = str(record["state"])
        if new_state not in TRANSITIONS[current]:
            raise invalid_input(
                "Invalid transaction state transition.",
                transaction_id=transaction_id,
                current_state=current,
                requested_state=new_state,
            )
        record["state"] = new_state
        record["state_history"].append({"state": new_state, "at": isoformat(instant)})
        if new_state in TERMINAL_STATES:
            record["completed_at"] = isoformat(instant)
            started = datetime.fromisoformat(str(record["started_at"]).replace("Z", "+00:00"))
            record["duration_ms"] = max(
                0,
                int((instant.astimezone(UTC) - started.astimezone(UTC)).total_seconds() * 1000),
            )
        self.save(record)
        if new_state in TERMINAL_STATES:
            self.write_observation(record)
        return record

    def mark_failure(
        self,
        transaction_id: str,
        *,
        classification: str,
        message: str,
        failed_precondition: str | None = None,
    ) -> dict[str, Any]:
        record = self.load(transaction_id)
        record["failure"] = {
            "classification": classification,
            "message": message,
            "failed_precondition": failed_precondition,
        }
        self.save(record)
        return self.transition(transaction_id, "failed")

    def set_applied_hash(
        self,
        transaction_id: str,
        target: str,
        applied_sha256: str,
    ) -> dict[str, Any]:
        def updater(record: dict[str, Any]) -> None:
            for item in record["affected_files"]:
                if item["target"] == target:
                    item["applied_sha256"] = applied_sha256
                    return
            raise invalid_input("Applied target is not in transaction.", target=target)

        return self.update(transaction_id, updater)

    def record_bootstrap_parent_created(self, transaction_id: str) -> dict[str, Any]:
        def updater(record: dict[str, Any]) -> None:
            install = record.get("bootstrap_install")
            if record.get("operation_kind") != "manifest_bootstrap" or not isinstance(
                install, dict
            ):
                raise invalid_input(
                    "Transaction does not support bootstrap install evidence.",
                    transaction_id=transaction_id,
                )
            install["parent_created"] = True

        return self.update(transaction_id, updater)

    def record_bootstrap_manifest_created(
        self,
        transaction_id: str,
        target: str,
        applied_sha256: str,
        *,
        device: int,
        inode: int,
    ) -> dict[str, Any]:
        def updater(record: dict[str, Any]) -> None:
            install = record.get("bootstrap_install")
            if record.get("operation_kind") != "manifest_bootstrap" or not isinstance(
                install, dict
            ):
                raise invalid_input(
                    "Transaction does not support bootstrap install evidence.",
                    transaction_id=transaction_id,
                )
            if install.get("manifest_created"):
                raise invalid_input(
                    "Bootstrap manifest creation is already recorded.",
                    transaction_id=transaction_id,
                )
            for item in record["affected_files"]:
                if item["target"] == target:
                    item["applied_sha256"] = applied_sha256
                    install["manifest_created"] = True
                    install["manifest_device"] = device
                    install["manifest_inode"] = inode
                    return
            raise invalid_input("Applied target is not in transaction.", target=target)

        return self.update(transaction_id, updater)

    def set_validation_results(
        self,
        transaction_id: str,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return self.update(
            transaction_id,
            lambda record: record.__setitem__("validation_results", results),
        )

    def update_rollback(
        self,
        transaction_id: str,
        **values: Any,
    ) -> dict[str, Any]:
        def updater(record: dict[str, Any]) -> None:
            record["rollback"].update(values)

        return self.update(transaction_id, updater)

    def write_observation(self, record: dict[str, Any]) -> dict[str, Any]:
        validation_result = "not_run"
        results = record["validation_results"]
        if results:
            if any(item["status"] == "timeout" for item in results):
                validation_result = "timeout"
            elif any(item["status"] == "failed" for item in results):
                validation_result = "failed"
            elif all(item["status"] == "passed" for item in results):
                validation_result = "passed"
        rollback_state = record["rollback"]["state"]
        rollback_result = {
            "succeeded": "succeeded",
            "failed": "failed",
        }.get(rollback_state, "not_required")
        failure = record.get("failure")
        conflict_types: list[str] = []
        if isinstance(failure, dict) and failure.get("failed_precondition"):
            conflict_types.append(str(failure["failed_precondition"]).split(":", 1)[0])
        observation: dict[str, Any] = {
            "schema_version": 1,
            "transaction_id": record["transaction_id"],
            "outcome": record["state"],
            "component_types": sorted(
                {str(item["ownership"]) for item in record["affected_files"]}
            ),
            "file_count": len(record["affected_files"]),
            "conflict_types": conflict_types,
            "validation_result": validation_result,
            "rollback_result": rollback_result,
            "duration_ms": int(record["duration_ms"] or 0),
            "safety_limit_overrides": record["safety"]["overrides"],
            "failure_classification": (
                str(failure["classification"]) if isinstance(failure, dict) else None
            ),
            "recorded_at": record["completed_at"],
            "publishability": "public_safe",
        }
        write_json_atomic(
            self.directory(str(record["transaction_id"])) / "observation.json",
            observation,
            schema_name="transaction-observation",
        )
        return observation

    def list(self) -> list[dict[str, Any]]:
        if not self.transactions_directory.is_dir():
            return []
        summaries: list[dict[str, Any]] = []
        for directory in sorted(self.transactions_directory.iterdir(), key=lambda item: item.name):
            if not directory.is_dir() or TRANSACTION_ID.fullmatch(directory.name) is None:
                continue
            record = self.load(directory.name)
            summaries.append(
                {
                    "transaction_id": record["transaction_id"],
                    "project_id": record["target_repository_identifier"],
                    "state": record["state"],
                    "started_at": record["started_at"],
                    "completed_at": record["completed_at"],
                    "file_count": len(record["affected_files"]),
                    "failure_classification": (
                        record["failure"]["classification"] if record["failure"] else None
                    ),
                }
            )
        return summaries
