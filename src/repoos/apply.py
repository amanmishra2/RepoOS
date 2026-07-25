"""Fixture-only transactional apply, validation, automatic rollback, and manual rollback."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from repoos.backup import backup_entry_map, create_backup, validate_backup
from repoos.errors import (
    ExitCode,
    RepoOSError,
    apply_failure,
    backup_failure,
    dirty_repository,
    invalid_input,
    rollback_failure,
    safety_limit,
    stale_plan,
    unsafe_state,
    validation_rolled_back,
)
from repoos.git import inspect_git, is_git_worktree, status_fingerprint, status_paths
from repoos.locks import GlobalLock, RepositoryLock
from repoos.manifest_bootstrap import (
    DESTINATION,
    OPERATION_KIND,
    assert_bootstrap_artifact_isolated,
    consume_manifest_bootstrap_authorization,
    install_manifest_exclusive,
    manifest_bootstrap_precondition_error,
    manifest_bootstrap_precondition_failures,
    remove_created_manifest_parent_if_safe,
    reserve_manifest_bootstrap_authorization,
    validate_bootstrap_manifest_bytes,
    validate_bootstrap_manifest_file,
    validate_manifest_bootstrap_authorization,
    validate_post_install_preservation,
    validate_restored_preservation,
    write_rendered_manifest,
)
from repoos.ownership import (
    OwnershipMode,
    file_mode,
    locate_managed_section,
    render_managed_file,
    render_managed_section,
)
from repoos.paths import contained_path, require_directory, sha256_bytes, sha256_file
from repoos.pause import get_pause_status
from repoos.planning import canonical_json_bytes, precondition_failures
from repoos.redaction import redact_text
from repoos.transactions import TransactionStore, isoformat, utc_now

FaultHook = Callable[[str], None]
MAX_VALIDATION_OUTPUT = 8192
DEFAULT_VALIDATION_TIMEOUT = 60


def _inject(fault: FaultHook | None, point: str) -> None:
    if fault is not None:
        fault(point)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_replace(target: Path, content: bytes, mode: int) -> None:
    if target.is_symlink():
        raise unsafe_state("Atomic write refuses a symlink target.", target=str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.parent.is_symlink():
        raise unsafe_state("Atomic write refuses a symlink parent.", target=str(target))
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.repoos-",
        suffix=".tmp",
        dir=target.parent,
    )
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, target)
        os.chmod(target, mode, follow_symlinks=False)
        _fsync_directory(target.parent)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def _remove_created_file(target: Path) -> None:
    if target.is_symlink():
        raise unsafe_state("Rollback refuses to remove a symlink.", target=str(target))
    if target.exists():
        if not target.is_file():
            raise unsafe_state("Rollback target is not a regular file.", target=str(target))
        target.unlink()
        _fsync_directory(target.parent)


def _read_plan_snapshot(store: TransactionStore, transaction_id: str) -> dict[str, Any]:
    path = store.directory(transaction_id) / "plan.json"
    if not path.is_file() or path.is_symlink():
        raise backup_failure("Transaction plan snapshot is missing or unsafe.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise backup_failure(
            "Transaction plan snapshot could not be parsed.",
            exception_type=type(exc).__name__,
        ) from exc
    if not isinstance(value, dict):
        raise backup_failure("Transaction plan snapshot root is invalid.")
    return value


def _render_operations(
    store: TransactionStore,
    record: dict[str, Any],
    plan: dict[str, Any],
    repository: Path,
    source_root: Path,
    *,
    fault: FaultHook | None = None,
) -> dict[str, Path]:
    rendered_directory = store.directory(str(record["transaction_id"])) / "rendered"
    try:
        rendered_directory.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise apply_failure("Rendered-output directory already exists.") from exc
    rendered: dict[str, Path] = {}
    for operation in plan["operations"]:
        if operation["action"] == "preserve":
            continue
        target_name = str(operation["target"])
        target = contained_path(repository, target_name)
        if target.is_symlink():
            raise unsafe_state("Render refuses a symlink target.", target=target_name)
        before = target.read_bytes() if target.is_file() else None
        before_digest = sha256_bytes(before) if before is not None else None
        if before_digest != operation["before_sha256"]:
            raise stale_plan(
                "Target changed between approval and rendering.",
                failed_precondition=f"target_changed:{target_name}",
            )
        source_name = operation["source"]
        if not isinstance(source_name, str):
            raise invalid_input("Writable operation has no source.", target=target_name)
        source = contained_path(source_root, source_name, must_exist=True)
        if source.is_symlink() or not source.is_file():
            raise unsafe_state("Render source is not a regular file.", source=source_name)
        source_content = source.read_bytes()
        if sha256_bytes(source_content) != operation["source_sha256"]:
            raise stale_plan(
                "Source changed between approval and rendering.",
                failed_precondition=f"source_changed:{source_name}",
            )
        if operation["ownership"] == OwnershipMode.MANAGED_SECTION.value:
            if before is None:
                raise apply_failure("Managed-section target disappeared.", target=target_name)
            section = operation["managed_section"]
            if not isinstance(section, dict):
                raise invalid_input("Managed-section operation lacks boundary metadata.")
            content, _layout = render_managed_section(
                before,
                source_content,
                str(section["start_marker"]),
                str(section["end_marker"]),
            )
        else:
            content = render_managed_file(source_content, before)
        if sha256_bytes(content) != operation["after_sha256"]:
            raise stale_plan(
                "Rendered output does not match the approved digest.",
                failed_precondition=f"rendered_hash_mismatch:{target_name}",
            )
        output = rendered_directory / f"{operation['operation_id']}.bin"
        descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            output.unlink(missing_ok=True)
            raise
        rendered[target_name] = output
        _inject(fault, f"rendered:{target_name}")
    _fsync_directory(rendered_directory)
    return rendered


def _verify_applied(plan: dict[str, Any], repository: Path) -> list[str]:
    failures: list[str] = []
    for operation in plan["operations"]:
        if operation["action"] == "preserve":
            continue
        target_name = str(operation["target"])
        try:
            target = contained_path(repository, target_name, must_exist=True)
        except RepoOSError:
            failures.append(f"applied_target_missing:{target_name}")
            continue
        if target.is_symlink() or not target.is_file():
            failures.append(f"applied_target_unsafe:{target_name}")
            continue
        if sha256_file(target) != operation["after_sha256"]:
            failures.append(f"applied_hash_mismatch:{target_name}")
        if file_mode(target) != operation["after_mode"]:
            failures.append(f"applied_mode_mismatch:{target_name}")
        section = operation.get("managed_section")
        if isinstance(section, dict):
            try:
                layout = locate_managed_section(
                    target.read_bytes(),
                    str(section["start_marker"]),
                    str(section["end_marker"]),
                )
            except RepoOSError:
                failures.append(f"applied_section_invalid:{target_name}")
            else:
                if layout.section_sha256 != section["after_section_sha256"]:
                    failures.append(f"applied_section_hash_mismatch:{target_name}")
                if layout.outside_sha256 != section["before_outside_sha256"]:
                    failures.append(f"applied_section_outside_changed:{target_name}")
    return sorted(set(failures))


def _bounded_output(value: bytes) -> tuple[str, bool]:
    truncated = len(value) > MAX_VALIDATION_OUTPUT
    excerpt = value[:MAX_VALIDATION_OUTPUT].decode("utf-8", errors="replace")
    return redact_text(excerpt), truncated


def _run_validation_commands(
    commands: list[dict[str, Any]],
    repository: Path,
    *,
    timeout_seconds: int,
    fault: FaultHook | None,
) -> tuple[list[dict[str, Any]], bool]:
    results: list[dict[str, Any]] = []
    for command in commands:
        name = str(command["name"])
        argv = [str(item) for item in command["argv"]]
        _inject(fault, f"validation_before:{name}")
        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv,
                cwd=repository,
                check=False,
                capture_output=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stdout, stdout_truncated = _bounded_output(exc.stdout or b"")
            stderr, stderr_truncated = _bounded_output(exc.stderr or b"")
            results.append(
                {
                    "name": name,
                    "argv": argv,
                    "exit_code": 124,
                    "stdout_excerpt": stdout,
                    "stderr_excerpt": stderr,
                    "output_truncated": stdout_truncated or stderr_truncated,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "status": "timeout",
                }
            )
            return results, False
        except OSError as exc:
            results.append(
                {
                    "name": name,
                    "argv": argv,
                    "exit_code": 127,
                    "stdout_excerpt": "",
                    "stderr_excerpt": f"command_start_failed:{type(exc).__name__}",
                    "output_truncated": False,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "status": "failed",
                }
            )
            return results, False
        stdout, stdout_truncated = _bounded_output(completed.stdout)
        stderr, stderr_truncated = _bounded_output(completed.stderr)
        status = "passed" if completed.returncode == 0 else "failed"
        results.append(
            {
                "name": name,
                "argv": argv,
                "exit_code": completed.returncode,
                "stdout_excerpt": stdout,
                "stderr_excerpt": stderr,
                "output_truncated": stdout_truncated or stderr_truncated,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "status": status,
            }
        )
        _inject(fault, f"validation_after:{name}")
        if completed.returncode != 0:
            return results, False
    return results, True


def _set_failure(
    store: TransactionStore,
    transaction_id: str,
    *,
    classification: str,
    message: str,
    failed_precondition: str | None,
) -> dict[str, Any]:
    def updater(record: dict[str, Any]) -> None:
        record["failure"] = {
            "classification": classification,
            "message": message,
            "failed_precondition": failed_precondition,
        }

    return store.update(transaction_id, updater)


def precondition_error(transaction_id: str, failures: list[str]) -> RepoOSError:
    details = {"transaction_id": transaction_id, "failed_preconditions": failures}
    substantive_stale_prefixes = (
        "stale_base_commit",
        "stale_operation_contract:",
        "target_changed:",
        "source_changed:",
        "source_mode_changed:",
        "manifest_invalid:",
        "manifest_changed",
        "manifest_version_changed",
        "manifest_repoos_version_changed",
        "target_repository_",
        "source_root_",
        "git_common_dir_changed",
        "unsupported_repoos_source_version",
        "plan_digest_mismatch",
    )
    if any(failure.startswith(substantive_stale_prefixes) for failure in failures):
        return stale_plan("Approved update plan is stale.", **details)
    if any(
        failure == "repository_dirty" or failure == "plan_conflict:repository_dirty"
        for failure in failures
    ):
        return dirty_repository("Fixture repository is not clean.", **details)
    if any(failure.startswith("lock_conflict:") for failure in failures):
        lock_type = next(
            failure.split(":", 1)[1] for failure in failures if failure.startswith("lock_conflict:")
        )
        return RepoOSError(
            "Another RepoOS operation owns the fixture lock.",
            ExitCode.LOCKED,
            lock_type,
            details,
        )
    if any(failure.startswith("paused:") for failure in failures):
        return RepoOSError(
            "RepoOS operations are paused.",
            ExitCode.PAUSED,
            "paused",
            details,
        )
    if any(failure.startswith("status_fingerprint_changed") for failure in failures):
        return stale_plan("Approved update plan is stale.", **details)
    if any(failure.startswith("stale_") for failure in failures):
        return stale_plan("Approved update plan is stale.", **details)
    if any(failure.startswith("safety_limit:") for failure in failures):
        return safety_limit("Approved plan exceeds a safety limit.", **details)
    return unsafe_state("Apply preconditions failed.", **details)


def _acquire_repository_lock(
    state_directory: Path,
    identity: str,
    target: str,
    transaction_id: str,
    *,
    recover_stale_lock: bool,
) -> RepositoryLock:
    lock = RepositoryLock(
        state_directory,
        identity,
        target=target,
        transaction_id=transaction_id,
        recover_stale=recover_stale_lock,
    )
    if recover_stale_lock:
        with GlobalLock(
            state_directory,
            transaction_id=transaction_id,
            recover_stale=True,
        ):
            lock.acquire()
    else:
        lock.acquire()
    return lock


def _validate_manual_rollback_state(
    record: dict[str, Any],
    backup_manifest: dict[str, Any],
    repository: Path,
) -> bool:
    """Return true if every path is already restored; reject any unrelated drift."""

    if not is_git_worktree(repository):
        raise stale_plan("Rollback target is no longer a Git repository.")
    state = inspect_git(repository)
    if state.head != record["target_head_planned"]:
        raise stale_plan("Rollback target HEAD changed after the transaction.")
    affected = {str(item["target"]) for item in backup_manifest["entries"]}
    unexpected = sorted(set(status_paths(repository)) - affected)
    if unexpected:
        raise stale_plan(
            "Rollback target contains unrelated changes.",
            unexpected_paths=unexpected,
        )

    all_original = True
    bootstrap_install = record.get("bootstrap_install")
    for entry in backup_manifest["entries"]:
        target_name = str(entry["target"])
        target = contained_path(repository, target_name)
        if target.is_symlink():
            raise stale_plan("Rollback target became a symlink.", target=target_name)
        current_hash = sha256_file(target) if target.is_file() else None
        original_hash = entry["original_sha256"]
        applied_hash = entry["expected_applied_sha256"]
        if current_hash not in {original_hash, applied_hash}:
            raise stale_plan(
                "Rollback target changed unexpectedly.",
                target=target_name,
            )
        if current_hash == original_hash:
            expected_mode = entry["original_mode"]
        else:
            expected_mode = entry["expected_applied_mode"]
            all_original = False
        if expected_mode is not None and target.is_file() and file_mode(target) != expected_mode:
            raise stale_plan(
                "Rollback target mode changed unexpectedly.",
                target=target_name,
            )
        if (
            record.get("operation_kind") == OPERATION_KIND
            and original_hash is None
            and current_hash == applied_hash
            and not _matches_bootstrap_install_identity(bootstrap_install, target)
        ):
            raise stale_plan(
                "Rollback refuses a manifest without transaction creation evidence.",
                target=target_name,
            )
        if original_hash is None and current_hash is None:
            continue
        if current_hash != original_hash:
            all_original = False
    return all_original


def _matches_bootstrap_install_identity(install: Any, target: Path) -> bool:
    if not isinstance(install, dict) or not install.get("manifest_created"):
        return False
    if target.is_symlink() or not target.is_file():
        return False
    metadata = target.stat(follow_symlinks=False)
    return install.get("manifest_device") == int(metadata.st_dev) and install.get(
        "manifest_inode"
    ) == int(metadata.st_ino)


def _restore_backup(
    record: dict[str, Any],
    backup_manifest: dict[str, Any],
    backup_directory: Path,
    repository: Path,
    *,
    plan: dict[str, Any] | None = None,
    fault: FaultHook | None,
) -> int:
    entries = backup_entry_map(backup_manifest)
    restored = 0
    for target_name in backup_manifest["restore_order"]:
        entry = entries[target_name]
        target = contained_path(repository, target_name)
        _inject(fault, f"rollback_before_restore:{target_name}")
        if entry["existed"]:
            backup_path = contained_path(
                backup_directory,
                str(entry["backup_path"]),
                must_exist=True,
            )
            content = backup_path.read_bytes()
            if sha256_bytes(content) != entry["original_sha256"]:
                raise backup_failure("Backup content changed during rollback.", target=target_name)
            _atomic_replace(target, content, int(entry["original_mode"]))
        else:
            if target.exists():
                if (
                    target.is_symlink()
                    or not target.is_file()
                    or sha256_file(target) != entry["expected_applied_sha256"]
                    or file_mode(target) != entry["expected_applied_mode"]
                ):
                    raise rollback_failure(
                        "Rollback refuses to delete an unrelated created-path occupant.",
                        target=target_name,
                    )
                if record.get(
                    "operation_kind"
                ) == OPERATION_KIND and not _matches_bootstrap_install_identity(
                    record.get("bootstrap_install"),
                    target,
                ):
                    raise rollback_failure(
                        "Rollback lacks transaction creation evidence for the manifest.",
                        target=target_name,
                    )
            _remove_created_file(target)
        restored += 1
        _inject(fault, f"rollback_after_restore:{target_name}")

    if record.get("operation_kind") == OPERATION_KIND:
        if plan is None:
            raise rollback_failure("Manifest-bootstrap rollback has no approved plan snapshot.")
        install = record.get("bootstrap_install")
        if isinstance(install, dict) and install.get("parent_created"):
            remove_created_manifest_parent_if_safe(plan, repository)
        _inject(fault, "rollback_after_parent_cleanup")

    for entry in backup_manifest["entries"]:
        target_name = str(entry["target"])
        target = contained_path(repository, target_name)
        if entry["existed"]:
            if (
                not target.is_file()
                or target.is_symlink()
                or sha256_file(target) != entry["original_sha256"]
                or file_mode(target) != entry["original_mode"]
            ):
                raise rollback_failure(
                    "Restored file failed byte or mode verification.",
                    target=target_name,
                )
        elif target.exists():
            raise rollback_failure("Created file still exists after rollback.", target=target_name)
    state = inspect_git(repository)
    if (
        state.head != record["target_head_planned"]
        or status_fingerprint(repository) != record["target_status_fingerprint"]
    ):
        raise rollback_failure(
            "Restored repository state does not match the planned pre-change state.",
            remaining_paths=list(status_paths(repository)),
        )
    if record.get("operation_kind") == OPERATION_KIND:
        assert plan is not None
        preservation_failures = validate_restored_preservation(plan, repository)
        if preservation_failures:
            raise rollback_failure(
                "Rollback could not prove target and sibling preservation.",
                failed_preconditions=preservation_failures,
            )
    _inject(fault, "rollback_verified")
    return restored


def _automatic_rollback(
    store: TransactionStore,
    transaction_id: str,
    repository: Path,
    *,
    fault: FaultHook | None,
) -> dict[str, Any]:
    record = store.load(transaction_id)
    backup_directory = Path(str(record["backup_location"]))
    plan = _read_plan_snapshot(store, transaction_id)
    try:
        backup_manifest = validate_backup(
            backup_directory,
            transaction_record=record,
        )
        store.transition(transaction_id, "rolling_back")
        store.update_rollback(
            transaction_id,
            state="in_progress",
            started_at=isoformat(utc_now()),
            completed_at=None,
            restored_files=0,
            failure_classification=None,
        )
        _inject(fault, "rollback_started")
        restored = _restore_backup(
            record,
            backup_manifest,
            backup_directory,
            repository,
            plan=plan,
            fault=fault,
        )
        store.update_rollback(
            transaction_id,
            state="succeeded",
            completed_at=isoformat(utc_now()),
            restored_files=restored,
            failure_classification=None,
        )
        return store.transition(transaction_id, "rolled_back")
    except Exception as exc:
        current = store.load(transaction_id)
        if current["state"] == "rolling_back":
            store.update_rollback(
                transaction_id,
                state="failed",
                completed_at=isoformat(utc_now()),
                failure_classification=type(exc).__name__,
            )
            store.transition(transaction_id, "rollback_failed")
        raise rollback_failure(
            "Automatic rollback failed; no further rollback loop was attempted.",
            transaction_id=transaction_id,
            backup=str(backup_directory),
            exception_type=type(exc).__name__,
            manual_recovery=(
                "Preserve the backup, inspect only its approved restore_order paths, "
                "restore original bytes/modes manually, and do not use git reset, clean, "
                "checkout, or stash."
            ),
        ) from exc


def execute_plan(
    plan: dict[str, Any],
    repository: str | Path,
    source_root: str | Path,
    *,
    state_directory: Path,
    safety_overrides: tuple[str, ...] = (),
    recover_stale_lock: bool = False,
    validation_timeout: int = DEFAULT_VALIDATION_TIMEOUT,
    fault: FaultHook | None = None,
) -> dict[str, Any]:
    """Apply one approved plan to one marked disposable fixture transactionally."""

    target = require_directory(repository)
    sources = require_directory(source_root)
    resolved_state = state_directory.expanduser().resolve()
    if resolved_state.is_relative_to(target) or resolved_state.is_relative_to(sources):
        raise unsafe_state(
            "RepoOS state must remain outside the target and source roots.",
            state_directory=str(resolved_state),
        )
    state_directory = resolved_state
    store = TransactionStore(state_directory)
    unknown_overrides = sorted(set(safety_overrides) - set(plan["safety"]["limits"]))
    if unknown_overrides:
        raise invalid_input("Unknown safety-limit override.", overrides=unknown_overrides)
    record = store.create(plan, safety_overrides=safety_overrides)
    transaction_id = str(record["transaction_id"])

    failures = precondition_failures(
        plan,
        target,
        sources,
        state_directory=state_directory,
        safety_overrides=safety_overrides,
        check_lock=not recover_stale_lock,
    )
    if failures:
        error = precondition_error(transaction_id, failures)
        store.mark_failure(
            transaction_id,
            classification=error.error_type,
            message=error.message,
            failed_precondition=failures[0],
        )
        raise error
    store.transition(transaction_id, "validated")

    git_state = inspect_git(target)
    try:
        repository_lock = _acquire_repository_lock(
            state_directory,
            str(git_state.common_dir),
            str(target),
            transaction_id,
            recover_stale_lock=recover_stale_lock,
        )
    except RepoOSError as exc:
        store.mark_failure(
            transaction_id,
            classification=exc.error_type,
            message=exc.message,
            failed_precondition=f"lock_conflict:{exc.error_type}",
        )
        exc.details["transaction_id"] = transaction_id
        raise

    try:
        store.transition(transaction_id, "locked")
        raced_failures = precondition_failures(
            plan,
            target,
            sources,
            state_directory=state_directory,
            safety_overrides=safety_overrides,
            check_lock=False,
        )
        if raced_failures:
            error = precondition_error(transaction_id, raced_failures)
            store.mark_failure(
                transaction_id,
                classification=error.error_type,
                message=error.message,
                failed_precondition=raced_failures[0],
            )
            raise error

        manifest_path = target / ".repoos" / "project.yaml"
        try:
            create_backup(
                store,
                store.load(transaction_id),
                plan,
                target,
                manifest_path,
                fault=fault,
            )
        except RepoOSError as exc:
            store.mark_failure(
                transaction_id,
                classification=exc.error_type,
                message=exc.message,
                failed_precondition=str(exc.details.get("failed_precondition"))
                if exc.details.get("failed_precondition")
                else None,
            )
            exc.details["transaction_id"] = transaction_id
            raise
        store.transition(transaction_id, "backed_up")

        try:
            rendered = _render_operations(
                store,
                store.load(transaction_id),
                plan,
                target,
                sources,
                fault=fault,
            )
        except Exception as exc:
            classification = exc.error_type if isinstance(exc, RepoOSError) else "render_failure"
            message = exc.message if isinstance(exc, RepoOSError) else "Rendering failed."
            store.mark_failure(
                transaction_id,
                classification=classification,
                message=message,
                failed_precondition=(
                    str(exc.details.get("failed_precondition"))
                    if isinstance(exc, RepoOSError) and exc.details.get("failed_precondition")
                    else None
                ),
            )
            if isinstance(exc, RepoOSError):
                exc.details["transaction_id"] = transaction_id
                raise
            raise apply_failure(
                "Rendering failed before target writes.",
                transaction_id=transaction_id,
                exception_type=type(exc).__name__,
            ) from exc

        store.transition(transaction_id, "applying")
        phase = "apply"
        try:
            for operation in plan["operations"]:
                if operation["action"] == "preserve":
                    continue
                target_name = str(operation["target"])
                pause = get_pause_status(state_directory)
                if pause.paused:
                    raise RepoOSError(
                        "RepoOS operations were paused before a write boundary.",
                        ExitCode.PAUSED,
                        "paused",
                        {"source": pause.source},
                    )
                destination = contained_path(target, target_name)
                current_hash = sha256_file(destination) if destination.is_file() else None
                if current_hash != operation["before_sha256"]:
                    raise stale_plan(
                        "Target changed immediately before atomic replace.",
                        failed_precondition=f"target_changed:{target_name}",
                    )
                _inject(fault, f"apply_before_write:{target_name}")
                content = rendered[target_name].read_bytes()
                _atomic_replace(destination, content, int(operation["after_mode"]))
                applied_hash = sha256_file(destination)
                if applied_hash != operation["after_sha256"]:
                    raise apply_failure("Atomic replace produced an unexpected hash.")
                store.set_applied_hash(transaction_id, target_name, applied_hash)
                _inject(fault, f"apply_after_write:{target_name}")

            store.transition(transaction_id, "applied")
            phase = "validation"
            owned_failures = _verify_applied(plan, target)
            if owned_failures:
                raise apply_failure(
                    "Owned-file validation failed after apply.",
                    failures=owned_failures,
                )
            store.transition(transaction_id, "validating")
            results, validation_ok = _run_validation_commands(
                plan["validation_commands"],
                target,
                timeout_seconds=validation_timeout,
                fault=fault,
            )
            store.set_validation_results(transaction_id, results)
            if not validation_ok:
                raise apply_failure("Required fixture validation failed.")
            final_record = store.transition(transaction_id, "completed")
            return {
                "schema_version": "repoos.apply-result.v1",
                "transaction_id": transaction_id,
                "state": final_record["state"],
                "files_applied": len(final_record["affected_files"]),
                "operations": [
                    {
                        "target": item["target"],
                        "action": item["action"],
                        "ownership": item["ownership"],
                    }
                    for item in final_record["affected_files"]
                ],
                "validation": "passed",
                "rollback": "not_required",
                "commits_performed": 0,
                "pushes_performed": 0,
            }
        except Exception as exc:
            if phase == "validation":
                classification = "validation_failure"
            else:
                classification = (
                    exc.error_type if isinstance(exc, RepoOSError) else f"{phase}_failure"
                )
            message = exc.message if isinstance(exc, RepoOSError) else f"{phase.title()} failed."
            failed_precondition = (
                str(exc.details.get("failed_precondition"))
                if isinstance(exc, RepoOSError) and exc.details.get("failed_precondition")
                else None
            )
            _set_failure(
                store,
                transaction_id,
                classification=classification,
                message=message,
                failed_precondition=failed_precondition,
            )
            _automatic_rollback(
                store,
                transaction_id,
                target,
                fault=fault,
            )
            if phase == "validation":
                raise validation_rolled_back(
                    "Fixture validation failed and automatic rollback succeeded.",
                    transaction_id=transaction_id,
                ) from exc
            if isinstance(exc, RepoOSError) and exc.code is ExitCode.PAUSED:
                raise RepoOSError(
                    "RepoOS paused during apply; automatic rollback succeeded.",
                    ExitCode.PAUSED,
                    "paused_rolled_back",
                    {"transaction_id": transaction_id},
                ) from exc
            raise apply_failure(
                "Fixture apply failed and automatic rollback succeeded.",
                transaction_id=transaction_id,
                failure_classification=classification,
            ) from exc
    finally:
        repository_lock.release()


def _consume_bootstrap_authorization_after_attempt(
    record: dict[str, Any],
    transaction_id: str,
    *,
    outcome: str,
) -> None:
    path = record.get("authorization_path")
    if not isinstance(path, str):
        return
    with suppress(RepoOSError):
        consume_manifest_bootstrap_authorization(
            Path(path),
            transaction_id,
            outcome=outcome,
        )


def execute_manifest_bootstrap(
    plan: dict[str, Any],
    repository: str | Path,
    manifest_input: str | Path,
    authorization: str | Path,
    *,
    state_directory: Path,
    recover_stale_lock: bool = False,
    validation_timeout: int = DEFAULT_VALIDATION_TIMEOUT,
    fault: FaultHook | None = None,
    authorization_now: Any = None,
) -> dict[str, Any]:
    """Execute exactly one authorized creation of ``.repoos/project.yaml``."""

    target = require_directory(repository)
    input_path, raw, _manifest = validate_bootstrap_manifest_file(manifest_input)
    resolved_state = state_directory.expanduser().resolve()
    git_state = inspect_git(target)
    assert_bootstrap_artifact_isolated(
        target,
        resolved_state,
        git_state.common_dir,
        artifact_kind="RepoOS state",
    )
    authorization_path, _authorization_value, authorization_sha256 = (
        validate_manifest_bootstrap_authorization(
            authorization,
            plan,
            now=authorization_now,
        )
    )
    authorization_root = resolved_state / "authorizations"
    if not authorization_path.is_relative_to(authorization_root):
        raise RepoOSError(
            "Authorization must be stored beneath the local RepoOS state directory.",
            ExitCode.AUTHORIZATION_REQUIRED,
            "invalid_authorization",
            {"authorization_root": str(authorization_root)},
        )

    store = TransactionStore(resolved_state)
    record = store.create(
        plan,
        authorization_digest=authorization_sha256,
        authorization_path=str(authorization_path),
    )
    transaction_id = str(record["transaction_id"])
    failures = manifest_bootstrap_precondition_failures(
        plan,
        target,
        input_path,
        state_directory=resolved_state,
        check_lock=not recover_stale_lock,
    )
    if failures:
        error = manifest_bootstrap_precondition_error(transaction_id, failures)
        store.mark_failure(
            transaction_id,
            classification=error.error_type,
            message=error.message,
            failed_precondition=failures[0],
        )
        raise error
    store.transition(transaction_id, "validated")

    try:
        repository_lock = _acquire_repository_lock(
            resolved_state,
            str(git_state.common_dir),
            str(target),
            transaction_id,
            recover_stale_lock=recover_stale_lock,
        )
    except RepoOSError as exc:
        store.mark_failure(
            transaction_id,
            classification=exc.error_type,
            message=exc.message,
            failed_precondition=f"lock_conflict:{exc.error_type}",
        )
        exc.details["transaction_id"] = transaction_id
        raise

    authorization_reserved = False
    try:
        store.transition(transaction_id, "locked")
        raced_failures = manifest_bootstrap_precondition_failures(
            plan,
            target,
            input_path,
            state_directory=resolved_state,
            check_lock=False,
        )
        if raced_failures:
            error = manifest_bootstrap_precondition_error(transaction_id, raced_failures)
            store.mark_failure(
                transaction_id,
                classification=error.error_type,
                message=error.message,
                failed_precondition=raced_failures[0],
            )
            raise error
        try:
            reserve_manifest_bootstrap_authorization(
                authorization_path,
                plan,
                transaction_id,
                now=authorization_now,
            )
            authorization_reserved = True
            _inject(fault, "manifest_authorization_reserved")
        except RepoOSError as exc:
            store.mark_failure(
                transaction_id,
                classification=exc.error_type,
                message=exc.message,
                failed_precondition="invalid_authorization",
            )
            raise

        try:
            create_backup(
                store,
                store.load(transaction_id),
                plan,
                target,
                input_path,
                fault=fault,
            )
        except RepoOSError as exc:
            store.mark_failure(
                transaction_id,
                classification=exc.error_type,
                message=exc.message,
                failed_precondition=(
                    str(exc.details.get("failed_precondition"))
                    if exc.details.get("failed_precondition")
                    else None
                ),
            )
            _consume_bootstrap_authorization_after_attempt(
                store.load(transaction_id),
                transaction_id,
                outcome="failed",
            )
            exc.details["transaction_id"] = transaction_id
            raise
        store.transition(transaction_id, "backed_up")

        try:
            input_path, raw, _manifest = validate_bootstrap_manifest_file(input_path)
            if sha256_bytes(raw) != plan["manifest"]["sha256"]:
                raise stale_plan(
                    "Manifest input changed before rendering.",
                    failed_precondition="manifest_input_changed",
                )
            rendered_path = write_rendered_manifest(store.directory(transaction_id), raw)
            rendered = rendered_path.read_bytes()
            validate_bootstrap_manifest_bytes(rendered, source="<rendered-manifest>")
            if sha256_bytes(rendered) != plan["manifest"]["sha256"]:
                raise stale_plan(
                    "Rendered manifest does not match the approved digest.",
                    failed_precondition="rendered_manifest_changed",
                )
            _inject(fault, "manifest_rendered")
        except Exception as exc:
            classification = exc.error_type if isinstance(exc, RepoOSError) else "render_failure"
            message = exc.message if isinstance(exc, RepoOSError) else "Manifest rendering failed."
            store.mark_failure(
                transaction_id,
                classification=classification,
                message=message,
                failed_precondition=(
                    str(exc.details.get("failed_precondition"))
                    if isinstance(exc, RepoOSError) and exc.details.get("failed_precondition")
                    else None
                ),
            )
            if authorization_reserved:
                _consume_bootstrap_authorization_after_attempt(
                    store.load(transaction_id),
                    transaction_id,
                    outcome="failed",
                )
            if isinstance(exc, RepoOSError):
                exc.details["transaction_id"] = transaction_id
                raise
            raise apply_failure(
                "Manifest rendering failed before target writes.",
                transaction_id=transaction_id,
                exception_type=type(exc).__name__,
            ) from exc

        store.transition(transaction_id, "applying")
        phase = "manifest_install"
        install_state = {
            "parent_created": False,
            "manifest_created": False,
        }

        def record_parent_created() -> None:
            install_state["parent_created"] = True
            store.record_bootstrap_parent_created(transaction_id)

        def record_manifest_created(metadata: os.stat_result) -> None:
            install_state["manifest_created"] = True
            store.record_bootstrap_manifest_created(
                transaction_id,
                DESTINATION,
                str(plan["manifest"]["sha256"]),
                device=int(metadata.st_dev),
                inode=int(metadata.st_ino),
            )

        try:
            pause = get_pause_status(resolved_state)
            if pause.paused:
                raise RepoOSError(
                    "RepoOS operations were paused before manifest installation.",
                    ExitCode.PAUSED,
                    "paused",
                    {"source": pause.source},
                )
            _inject(fault, f"apply_before_write:{DESTINATION}")
            destination, parent_created = install_manifest_exclusive(
                target,
                rendered,
                parent_expected_absent=plan["parent_directory"]["state"] == "absent",
                on_parent_created=record_parent_created,
                on_manifest_created=record_manifest_created,
                fault=fault,
            )
            expected_parent_created = plan["parent_directory"]["state"] == "absent"
            if parent_created != expected_parent_created:
                raise stale_plan(
                    "Manifest parent state changed during installation.",
                    failed_precondition="parent_directory_changed",
                )
            if (
                destination.is_symlink()
                or not destination.is_file()
                or sha256_file(destination) != plan["manifest"]["sha256"]
                or file_mode(destination) != int(plan["operations"][0]["after_mode"])
            ):
                raise apply_failure("Installed manifest does not match its approved bytes or mode.")
            validate_bootstrap_manifest_file(destination)
            _inject(fault, f"apply_after_write:{DESTINATION}")
            store.transition(transaction_id, "applied")

            phase = "validation"
            owned_failures = _verify_applied(plan, target)
            if owned_failures:
                raise apply_failure(
                    "Installed manifest validation failed.",
                    failures=owned_failures,
                )
            store.transition(transaction_id, "validating")
            results, validation_ok = _run_validation_commands(
                plan["validation_commands"],
                target,
                timeout_seconds=validation_timeout,
                fault=fault,
            )
            store.set_validation_results(transaction_id, results)
            if not validation_ok:
                raise apply_failure("Required repository validation failed.")

            phase = "preservation"
            preservation_failures = validate_post_install_preservation(plan, target)
            if preservation_failures:
                raise apply_failure(
                    "Target or sibling worktree preservation validation failed.",
                    failed_precondition=preservation_failures[0],
                    failures=preservation_failures,
                )
            phase = "authorization"
            consume_manifest_bootstrap_authorization(
                authorization_path,
                transaction_id,
                outcome="completed",
            )
            final_record = store.transition(transaction_id, "completed")
            return {
                "schema_version": "repoos.manifest-bootstrap-result.v1",
                "operation_kind": OPERATION_KIND,
                "transaction_id": transaction_id,
                "state": final_record["state"],
                "files_created": 1,
                "files_edited": 0,
                "files_deleted": 0,
                "destination": DESTINATION,
                "manifest_sha256": plan["manifest"]["sha256"],
                "authorization": "consumed",
                "protected_sibling_count": len(plan["sibling_worktrees"]),
                "validation": "passed",
                "rollback": "not_required",
                "commits_performed": 0,
                "pushes_performed": 0,
            }
        except Exception as exc:
            classification = {
                "manifest_install": "manifest_install_failure",
                "validation": "validation_failure",
                "preservation": "preservation_failure",
                "authorization": "authorization_consumption_failure",
            }.get(phase, "manifest_install_failure")
            message = exc.message if isinstance(exc, RepoOSError) else f"{phase} failed."
            failed_precondition = (
                str(exc.details.get("failed_precondition"))
                if isinstance(exc, RepoOSError) and exc.details.get("failed_precondition")
                else None
            )
            _set_failure(
                store,
                transaction_id,
                classification=classification,
                message=message,
                failed_precondition=failed_precondition,
            )
            if phase == "manifest_install" and not any(install_state.values()):
                _consume_bootstrap_authorization_after_attempt(
                    store.load(transaction_id),
                    transaction_id,
                    outcome="failed",
                )
                store.transition(transaction_id, "failed")
                if isinstance(exc, RepoOSError):
                    exc.details["transaction_id"] = transaction_id
                    raise
                raise apply_failure(
                    "Manifest installation failed before target writes.",
                    transaction_id=transaction_id,
                ) from exc
            _automatic_rollback(
                store,
                transaction_id,
                target,
                fault=fault,
            )
            _consume_bootstrap_authorization_after_attempt(
                store.load(transaction_id),
                transaction_id,
                outcome="rolled_back",
            )
            if phase == "validation":
                raise validation_rolled_back(
                    "Repository validation failed and automatic rollback succeeded.",
                    transaction_id=transaction_id,
                ) from exc
            if phase == "manifest_install":
                raise RepoOSError(
                    "Manifest installation failed and automatic rollback succeeded.",
                    ExitCode.APPLY_FAILURE,
                    "manifest_install_failure",
                    {"transaction_id": transaction_id},
                ) from exc
            raise apply_failure(
                "Manifest bootstrap failed and automatic rollback succeeded.",
                transaction_id=transaction_id,
                failure_classification=classification,
            ) from exc
    finally:
        repository_lock.release()


def rollback_transaction(
    transaction_id: str,
    *,
    state_directory: Path,
    recover_stale_lock: bool = False,
    fault: FaultHook | None = None,
) -> dict[str, Any]:
    """Restore only one transaction's approved paths; force rollback is unsupported."""

    store = TransactionStore(state_directory)
    record = store.load(transaction_id)
    if record["state"] == "rolled_back":
        return {
            "schema_version": "repoos.rollback-result.v1",
            "transaction_id": transaction_id,
            "state": "rolled_back",
            "already_rolled_back": True,
            "restored_files": record["rollback"]["restored_files"],
        }
    if record["state"] == "rollback_failed":
        raise rollback_failure(
            "Rollback previously failed; uncontrolled retry is disabled.",
            transaction_id=transaction_id,
            backup=record["backup_location"],
            manual_recovery=(
                "Preserve and validate the backup, inspect only restore_order paths, and "
                "recover original bytes/modes manually without Git reset, clean, checkout, "
                "or stash."
            ),
        )
    allowed_states = {"backed_up", "applying", "applied", "validating", "completed", "rolling_back"}
    if record["state"] not in allowed_states:
        raise invalid_input(
            "Transaction state is not eligible for rollback.",
            transaction_id=transaction_id,
            state=record["state"],
        )

    plan = _read_plan_snapshot(store, transaction_id)
    if sha256_bytes(canonical_json_bytes(plan)) != record["plan_sha256"]:
        raise backup_failure("Transaction plan snapshot digest does not match.")
    repository = require_directory(str(record["target_repository_path"]))
    operation_kind = record.get("operation_kind", "fixture_update")
    if operation_kind == "fixture_update" and not (repository / ".repoos-fixture").is_file():
        raise unsafe_state("Rollback target is not a marked fixture.")
    if operation_kind not in {"fixture_update", OPERATION_KIND}:
        raise unsafe_state("Rollback transaction has an unsupported operation kind.")
    if not is_git_worktree(repository):
        raise stale_plan("Rollback target is no longer a Git working tree.")
    git_state = inspect_git(repository)
    if sha256_bytes(str(git_state.common_dir).encode("utf-8")) != plan["git_common_dir_sha256"]:
        raise stale_plan("Rollback target common-Git identity changed.")
    if operation_kind == OPERATION_KIND:
        assert_bootstrap_artifact_isolated(
            repository,
            state_directory.expanduser().resolve(),
            git_state.common_dir,
            artifact_kind="RepoOS rollback state",
        )

    lock = _acquire_repository_lock(
        state_directory,
        str(git_state.common_dir),
        str(repository),
        transaction_id,
        recover_stale_lock=recover_stale_lock,
    )
    try:
        current_record = store.load(transaction_id)
        backup_directory = Path(str(current_record["backup_location"]))
        backup_manifest = validate_backup(
            backup_directory,
            transaction_record=current_record,
        )
        already_restored = _validate_manual_rollback_state(
            current_record,
            backup_manifest,
            repository,
        )
        if operation_kind == OPERATION_KIND and not already_restored:
            preservation_failures = [
                failure
                for failure in validate_post_install_preservation(plan, repository)
                if failure != "unexpected_target_status"
            ]
            if preservation_failures:
                raise stale_plan(
                    "Rollback cannot prove sibling and common-Git preservation.",
                    failed_preconditions=preservation_failures,
                )
        if current_record["state"] != "rolling_back":
            store.transition(transaction_id, "rolling_back")
        store.update_rollback(
            transaction_id,
            state="in_progress",
            started_at=current_record["rollback"]["started_at"] or isoformat(utc_now()),
            completed_at=None,
            failure_classification=None,
        )
        if already_restored:
            restored = 0
        else:
            try:
                restored = _restore_backup(
                    current_record,
                    backup_manifest,
                    backup_directory,
                    repository,
                    plan=plan,
                    fault=fault,
                )
            except Exception as exc:
                store.update_rollback(
                    transaction_id,
                    state="failed",
                    completed_at=isoformat(utc_now()),
                    failure_classification=type(exc).__name__,
                )
                store.transition(transaction_id, "rollback_failed")
                raise rollback_failure(
                    "Manual rollback failed; no retry loop was attempted.",
                    transaction_id=transaction_id,
                    backup=str(backup_directory),
                    exception_type=type(exc).__name__,
                    manual_recovery=(
                        "Preserve the backup, inspect only its approved restore_order paths, "
                        "restore original bytes/modes manually, and do not use git reset, clean, "
                        "checkout, or stash."
                    ),
                ) from exc
        if already_restored and operation_kind == OPERATION_KIND:
            install = current_record.get("bootstrap_install")
            if isinstance(install, dict) and install.get("parent_created"):
                remove_created_manifest_parent_if_safe(plan, repository)
            preservation_failures = validate_restored_preservation(plan, repository)
            if preservation_failures:
                store.update_rollback(
                    transaction_id,
                    state="failed",
                    completed_at=isoformat(utc_now()),
                    failure_classification="preservation_failure",
                )
                store.transition(transaction_id, "rollback_failed")
                raise rollback_failure(
                    "Manual rollback could not prove restored worktree preservation.",
                    transaction_id=transaction_id,
                    failed_preconditions=preservation_failures,
                )
        store.update_rollback(
            transaction_id,
            state="succeeded",
            completed_at=isoformat(utc_now()),
            restored_files=restored,
            failure_classification=None,
        )
        final = store.transition(transaction_id, "rolled_back")
        if operation_kind == OPERATION_KIND and isinstance(
            current_record.get("authorization_path"), str
        ):
            with suppress(RepoOSError):
                consume_manifest_bootstrap_authorization(
                    Path(str(current_record["authorization_path"])),
                    transaction_id,
                    outcome="rolled_back",
                )
        return {
            "schema_version": "repoos.rollback-result.v1",
            "transaction_id": transaction_id,
            "state": final["state"],
            "already_rolled_back": already_restored,
            "restored_files": restored,
        }
    finally:
        lock.release()
