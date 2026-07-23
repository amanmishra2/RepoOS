from __future__ import annotations

import json
import socket
import threading
from pathlib import Path
from typing import Any

import pytest
from conftest import create_repoos_fixture, git

from repoos import __version__
from repoos.apply import execute_plan, rollback_transaction
from repoos.backup import validate_backup
from repoos.errors import ExitCode, RepoOSError
from repoos.git import inspect_git
from repoos.locks import RepositoryLock, repository_lock_path
from repoos.planning import (
    SafetyLimits,
    build_update_plan,
    canonical_plan_id,
)
from repoos.transactions import TransactionStore
from repoos.validation import validate_document

START = "# repoos:start fixture"
END = "# repoos:end fixture"


def _source_root(tmp_path: Path, files: dict[str, bytes]) -> Path:
    source = tmp_path / f"source-{len(list(tmp_path.glob('source-*')))}"
    source.mkdir()
    for relative, content in files.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return source


def _plan(
    repository: Path,
    source: Path,
    mappings: list[str],
    *,
    generated: list[str] | None = None,
    sections: list[str] | None = None,
    preserve: list[str] | None = None,
    limits: SafetyLimits | None = None,
) -> dict[str, Any]:
    return build_update_plan(
        repository,
        source,
        mappings,
        target_version=__version__,
        generated_mappings=generated,
        section_mappings=sections,
        preserve_specs=preserve,
        safety_limits=limits,
    )


def _snapshot(repository: Path) -> dict[str, tuple[bytes, int]]:
    value: dict[str, tuple[bytes, int]] = {}
    for path in sorted(repository.rglob("*")):
        if ".git" in path.relative_to(repository).parts:
            continue
        if path.is_file() and not path.is_symlink():
            value[path.relative_to(repository).as_posix()] = (
                path.read_bytes(),
                path.stat().st_mode & 0o7777,
            )
    return value


def _resign(plan: dict[str, Any]) -> dict[str, Any]:
    body = dict(plan)
    body.pop("plan_id")
    plan["plan_id"] = canonical_plan_id(body)
    return plan


def test_fully_managed_apply_backup_and_manual_rollback(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed value\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    state = tmp_path / "state"
    before = _snapshot(repoos_fixture)

    result = execute_plan(plan, repoos_fixture, source, state_directory=state)
    transaction_id = result["transaction_id"]
    assert result["state"] == "completed"
    assert (repoos_fixture / "managed" / "value.txt").read_bytes() == b"managed value\n"

    store = TransactionStore(state)
    record = store.load(transaction_id)
    assert record["state"] == "completed"
    backup = validate_backup(Path(record["backup_location"]), transaction_record=record)
    assert backup["entries"][0]["existed"] is False
    assert (
        validate_document(
            store.directory(transaction_id) / "observation.json",
            "transaction-observation",
        )
        == []
    )

    rollback = rollback_transaction(transaction_id, state_directory=state)
    assert rollback["state"] == "rolled_back"
    assert _snapshot(repoos_fixture) == before
    assert inspect_git(repoos_fixture).clean

    repeated = rollback_transaction(transaction_id, state_directory=state)
    assert repeated["already_rolled_back"] is True
    assert _snapshot(repoos_fixture) == before


def test_generated_file_and_preserved_ownership_modes(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    for relative, content in {
        "managed/extension.txt": b"repository extension\n",
        "managed/override.txt": b"local override\n",
        "managed/excluded.txt": b"excluded\n",
        "managed/owned.txt": b"repository owned\n",
    }.items():
        path = repoos_fixture / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    git(repoos_fixture, "add", "managed")
    git(repoos_fixture, "commit", "-m", "Add preserved ownership fixtures")
    source = _source_root(tmp_path, {"generated.txt": b"generated\n"})
    plan = _plan(
        repoos_fixture,
        source,
        [],
        generated=["generated.txt=generated/result.txt"],
        preserve=[
            "managed/extension.txt=repository_extension",
            "managed/override.txt=local_override",
            "managed/excluded.txt=excluded",
            "managed/owned.txt=repository_owned",
        ],
    )
    preserved_before = {
        path: (repoos_fixture / path).read_bytes()
        for path in (
            "managed/extension.txt",
            "managed/override.txt",
            "managed/excluded.txt",
            "managed/owned.txt",
        )
    }
    result = execute_plan(plan, repoos_fixture, source, state_directory=tmp_path / "state")
    assert (repoos_fixture / "generated" / "result.txt").read_bytes() == b"generated\n"
    for path, content in preserved_before.items():
        assert (repoos_fixture / path).read_bytes() == content
    record = TransactionStore(tmp_path / "state").load(result["transaction_id"])
    assert len(record["affected_files"]) == 1
    assert record["affected_files"][0]["ownership"] == "generated_file"


def test_managed_section_preserves_repository_owned_bytes_and_mode(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    target = repoos_fixture / "managed" / "section.txt"
    target.parent.mkdir()
    original = (
        b"owner prefix\r\n"
        + START.encode()
        + b"\r\nold value\r\n"
        + END.encode()
        + b"\r\nowner suffix\r\n"
    )
    target.write_bytes(original)
    target.chmod(0o640)
    git(repoos_fixture, "add", "managed/section.txt")
    git(repoos_fixture, "commit", "-m", "Add section fixture")
    source = _source_root(tmp_path, {"body.txt": b"new\nvalue\n"})
    plan = _plan(
        repoos_fixture,
        source,
        [],
        sections=[f"body.txt=managed/section.txt::{START}::{END}"],
    )
    result = execute_plan(plan, repoos_fixture, source, state_directory=tmp_path / "state")
    assert target.read_bytes() == (
        b"owner prefix\r\n"
        + START.encode()
        + b"\r\nnew\r\nvalue\r\n"
        + END.encode()
        + b"\r\nowner suffix\r\n"
    )
    assert target.stat().st_mode & 0o777 == 0o640
    rollback_transaction(result["transaction_id"], state_directory=tmp_path / "state")
    assert target.read_bytes() == original
    assert target.stat().st_mode & 0o777 == 0o640


@pytest.mark.parametrize(
    ("location", "expected"), [("inside", "inside_changed"), ("outside", "outside_changed")]
)
def test_managed_section_detects_local_inside_and_outside_changes(
    repoos_fixture: Path,
    tmp_path: Path,
    location: str,
    expected: str,
) -> None:
    target = repoos_fixture / "managed" / "section.txt"
    target.parent.mkdir()
    original = b"prefix\n" + START.encode() + b"\nold\n" + END.encode() + b"\nsuffix\n"
    target.write_bytes(original)
    git(repoos_fixture, "add", "managed/section.txt")
    git(repoos_fixture, "commit", "-m", "Add section fixture")
    source = _source_root(tmp_path, {"body.txt": b"new\n"})
    plan = _plan(
        repoos_fixture,
        source,
        [],
        sections=[f"body.txt=managed/section.txt::{START}::{END}"],
    )
    changed = (
        original.replace(b"old", b"local")
        if location == "inside"
        else original.replace(b"prefix", b"local prefix")
    )
    target.write_bytes(changed)
    from repoos.planning import apply_dry_run

    preview = apply_dry_run(
        plan,
        repoos_fixture,
        source,
        state_directory=tmp_path / "state",
    )
    assert any(expected in failure for failure in preview["failures"])


def test_dirty_repository_records_failed_attempt_without_target_write(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    (repoos_fixture / "user-work.txt").write_text("preserve\n", encoding="utf-8")
    state = tmp_path / "state"
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=state)
    assert caught.value.code is ExitCode.DIRTY_REPOSITORY
    assert not (repoos_fixture / "managed" / "value.txt").exists()
    records = TransactionStore(state).list()
    assert len(records) == 1
    assert records[0]["state"] == "failed"
    assert not (state / "transactions" / records[0]["transaction_id"] / "backup").exists()


def test_changed_head_source_and_target_are_stale_plans(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    target = repoos_fixture / "managed" / "value.txt"
    target.parent.mkdir()
    target.write_text("old\n", encoding="utf-8")
    git(repoos_fixture, "add", "managed/value.txt")
    git(repoos_fixture, "commit", "-m", "Add managed fixture")

    for scenario in ("head", "source", "target"):
        source = _source_root(tmp_path, {"value.txt": b"new\n"})
        plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
        if scenario == "head":
            marker = repoos_fixture / f"{scenario}.txt"
            marker.write_text("advance\n", encoding="utf-8")
            git(repoos_fixture, "add", marker.name)
            git(repoos_fixture, "commit", "-m", "Advance fixture")
        elif scenario == "source":
            (source / "value.txt").write_text("changed source\n", encoding="utf-8")
        else:
            target.write_text("changed target\n", encoding="utf-8")
        with pytest.raises(RepoOSError) as caught:
            execute_plan(
                plan,
                repoos_fixture,
                source,
                state_directory=tmp_path / f"state-{scenario}",
            )
        assert caught.value.code is ExitCode.STALE_PLAN
        if scenario == "target":
            target.write_text("old\n", encoding="utf-8")
        elif scenario == "head":
            # A later plan is created from the new clean HEAD; no history rewrite is needed.
            pass


@pytest.mark.parametrize("manifest_change", ["missing", "invalid"])
def test_missing_or_invalid_manifest_is_recorded_as_stale(
    repoos_fixture: Path,
    tmp_path: Path,
    manifest_change: str,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    manifest = repoos_fixture / ".repoos" / "project.yaml"
    if manifest_change == "missing":
        manifest.unlink()
    else:
        manifest.write_text("invalid: [", encoding="utf-8")
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=tmp_path / "state")
    assert caught.value.code is ExitCode.STALE_PLAN
    assert not (repoos_fixture / "managed" / "value.txt").exists()


def test_unsupported_repoos_source_version_is_stale_without_writes(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    plan["repoos_source_version"] = "9.9.9"
    _resign(plan)
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=tmp_path / "state")
    assert caught.value.code is ExitCode.STALE_PLAN
    assert not (repoos_fixture / "managed" / "value.txt").exists()


def test_tampered_but_schema_valid_plan_records_failed_attempt(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    plan["to_version"] = "0.2.1"
    state = tmp_path / "state"
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=state)
    assert caught.value.code is ExitCode.STALE_PLAN
    assert "plan_digest_mismatch" in caught.value.details["failed_preconditions"]
    record = TransactionStore(state).list()[0]
    assert record["state"] == "failed"
    assert not (repoos_fixture / "managed" / "value.txt").exists()


def test_path_traversal_and_symlink_escape_are_refused_during_planning(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    with pytest.raises(RepoOSError):
        _plan(repoos_fixture, source, ["value.txt=../outside.txt"])
    outside = tmp_path / "outside"
    outside.mkdir()
    (repoos_fixture / "managed").symlink_to(outside, target_is_directory=True)
    with pytest.raises(RepoOSError):
        _plan(repoos_fixture, source, ["value.txt=managed/escape.txt"])
    assert not (outside / "escape.txt").exists()


def test_active_lock_refuses_concurrent_apply_and_records_attempt(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    state = tmp_path / "state"
    git_state = inspect_git(repoos_fixture)
    lock = RepositoryLock(
        state,
        str(git_state.common_dir),
        target=str(repoos_fixture),
        transaction_id="tx-active",
    )
    lock.acquire()
    try:
        with pytest.raises(RepoOSError) as caught:
            execute_plan(plan, repoos_fixture, source, state_directory=state)
        assert caught.value.code is ExitCode.LOCKED
    finally:
        lock.release()
    records = TransactionStore(state).list()
    assert len(records) == 1
    assert records[0]["state"] == "failed"
    assert not (repoos_fixture / "managed" / "value.txt").exists()


def test_stale_lock_requires_flag_and_explicit_recovery_succeeds(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    state = tmp_path / "state"
    common = str(inspect_git(repoos_fixture).common_dir)
    path = repository_lock_path(state, common)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "pid": 999_999,
                "hostname": socket.gethostname(),
                "start_time": "2026-07-23T00:00:00Z",
                "target": str(repoos_fixture),
                "transaction_id": "tx-interrupted",
                "kind": "repository",
                "owner_token": "dead-owner",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=state)
    assert caught.value.error_type == "stale_lock"
    result = execute_plan(
        plan,
        repoos_fixture,
        source,
        state_directory=state,
        recover_stale_lock=True,
    )
    assert result["state"] == "completed"
    assert list(path.parent.glob(f"{path.name}.recovered.*"))


def test_safety_limit_is_enforced_before_writes_and_override_is_recorded(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed content\n"})
    limits = SafetyLimits(max_total_bytes_changed=1)
    plan = _plan(
        repoos_fixture,
        source,
        ["value.txt=managed/value.txt"],
        limits=limits,
    )
    state = tmp_path / "state"
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=state)
    assert caught.value.code is ExitCode.SAFETY_LIMIT
    assert not (repoos_fixture / "managed" / "value.txt").exists()

    tampered = json.loads(json.dumps(plan))
    tampered["safety"]["measurements"]["total_bytes_changed"] = 0
    tampered["safety"]["violations"] = []
    _resign(tampered)
    with pytest.raises(RepoOSError) as recomputed:
        execute_plan(
            tampered,
            repoos_fixture,
            source,
            state_directory=tmp_path / "tampered-state",
        )
    assert recomputed.value.code is ExitCode.STALE_PLAN
    assert "stale_safety_measurements" in recomputed.value.details["failed_preconditions"]
    assert not (repoos_fixture / "managed" / "value.txt").exists()

    result = execute_plan(
        plan,
        repoos_fixture,
        source,
        state_directory=state,
        safety_overrides=("max_total_bytes_changed",),
    )
    record = TransactionStore(state).load(result["transaction_id"])
    assert record["safety"]["overrides"] == ["max_total_bytes_changed"]


def test_backup_failure_prevents_first_target_write(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    state = tmp_path / "state"

    def fail(point: str) -> None:
        if point == "backup_before_finalize":
            raise OSError("injected backup failure")

    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=state, fault=fail)
    assert caught.value.code is ExitCode.BACKUP_FAILURE
    assert not (repoos_fixture / "managed" / "value.txt").exists()
    record = TransactionStore(state).list()[0]
    assert record["state"] == "failed"
    transaction_directory = TransactionStore(state).directory(record["transaction_id"])
    assert list(transaction_directory.glob(".backup-incomplete-*"))


def test_write_failure_after_one_file_automatically_restores_every_byte(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"one.txt": b"one\n", "two.txt": b"two\n"})
    limits = SafetyLimits(max_percentage_repository_files_touched=100.0)
    plan = _plan(
        repoos_fixture,
        source,
        ["one.txt=managed/one.txt", "two.txt=managed/two.txt"],
        limits=limits,
    )
    before = _snapshot(repoos_fixture)
    writes = 0

    def fail(point: str) -> None:
        nonlocal writes
        if point.startswith("apply_after_write:"):
            writes += 1
            if writes == 1:
                raise OSError("injected write failure")

    state = tmp_path / "state"
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=state, fault=fail)
    assert caught.value.code is ExitCode.APPLY_FAILURE
    transaction_id = str(caught.value.details["transaction_id"])
    record = TransactionStore(state).load(transaction_id)
    assert record["state"] == "rolled_back"
    assert record["rollback"]["state"] == "succeeded"
    assert _snapshot(repoos_fixture) == before
    assert inspect_git(repoos_fixture).clean


def test_validation_failure_automatically_rolls_back(
    tmp_path: Path,
) -> None:
    repository = create_repoos_fixture(
        tmp_path / "repository",
        validation_argv=["python3", "-c", "raise SystemExit(7)"],
    )
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repository, source, ["value.txt=managed/value.txt"])
    before = _snapshot(repository)
    state = tmp_path / "state"
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repository, source, state_directory=state)
    assert caught.value.code is ExitCode.VALIDATION_ROLLED_BACK
    record = TransactionStore(state).load(str(caught.value.details["transaction_id"]))
    assert record["state"] == "rolled_back"
    assert record["failure"]["classification"] == "validation_failure"
    assert record["validation_results"][0]["exit_code"] == 7
    assert record["rollback"]["state"] == "succeeded"
    assert _snapshot(repository) == before


def test_rollback_failure_is_terminal_and_preserves_backup(
    tmp_path: Path,
) -> None:
    repository = create_repoos_fixture(
        tmp_path / "repository",
        validation_argv=["python3", "-c", "raise SystemExit(1)"],
    )
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repository, source, ["value.txt=managed/value.txt"])
    state = tmp_path / "state"

    def fail(point: str) -> None:
        if point.startswith("rollback_before_restore:"):
            raise OSError("injected rollback failure")

    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repository, source, state_directory=state, fault=fail)
    assert caught.value.code is ExitCode.ROLLBACK_FAILURE
    transaction_id = str(caught.value.details["transaction_id"])
    record = TransactionStore(state).load(transaction_id)
    assert record["state"] == "rollback_failed"
    assert Path(record["backup_location"]).is_dir()
    assert "manual_recovery" in caught.value.details
    with pytest.raises(RepoOSError) as repeated:
        rollback_transaction(transaction_id, state_directory=state)
    assert repeated.value.code is ExitCode.ROLLBACK_FAILURE


def test_interrupted_transaction_can_be_manually_rolled_back(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    before = _snapshot(repoos_fixture)
    state = tmp_path / "state"

    def interrupt(point: str) -> None:
        if point.startswith("apply_after_write:"):
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        execute_plan(plan, repoos_fixture, source, state_directory=state, fault=interrupt)
    record = TransactionStore(state).list()[0]
    assert record["state"] == "applying"
    transaction_id = str(record["transaction_id"])
    result = rollback_transaction(transaction_id, state_directory=state)
    assert result["state"] == "rolled_back"
    assert _snapshot(repoos_fixture) == before


def test_manual_rollback_refuses_unexpected_target_or_unrelated_changes(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    state = tmp_path / "state"
    result = execute_plan(plan, repoos_fixture, source, state_directory=state)
    target = repoos_fixture / "managed" / "value.txt"
    target.write_text("unexpected\n", encoding="utf-8")
    with pytest.raises(RepoOSError) as changed_target:
        rollback_transaction(result["transaction_id"], state_directory=state)
    assert changed_target.value.code is ExitCode.STALE_PLAN
    assert TransactionStore(state).load(result["transaction_id"])["state"] == "completed"

    target.write_text("managed\n", encoding="utf-8")
    (repoos_fixture / "unrelated.txt").write_text("unexpected\n", encoding="utf-8")
    with pytest.raises(RepoOSError) as unrelated:
        rollback_transaction(result["transaction_id"], state_directory=state)
    assert unrelated.value.code is ExitCode.STALE_PLAN


def test_backup_integrity_tamper_blocks_manual_rollback(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    target = repoos_fixture / "managed" / "value.txt"
    target.parent.mkdir()
    target.write_text("old\n", encoding="utf-8")
    git(repoos_fixture, "add", "managed/value.txt")
    git(repoos_fixture, "commit", "-m", "Add managed target")
    source = _source_root(tmp_path, {"value.txt": b"new\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    state = tmp_path / "state"
    result = execute_plan(plan, repoos_fixture, source, state_directory=state)
    record = TransactionStore(state).load(result["transaction_id"])
    backup = Path(record["backup_location"])
    for relative in ("files/0000.bin", "transaction.json", "target-state.json"):
        path = backup / relative
        original = path.read_bytes()
        path.write_bytes(b"tampered\n")
        with pytest.raises(RepoOSError) as caught:
            rollback_transaction(result["transaction_id"], state_directory=state)
        assert caught.value.code is ExitCode.BACKUP_FAILURE
        assert TransactionStore(state).load(result["transaction_id"])["state"] == "completed"
        path.write_bytes(original)
    validate_backup(backup, transaction_record=record)


def test_repeated_apply_is_a_stable_refusal_without_second_write(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    state = tmp_path / "state"
    first = execute_plan(plan, repoos_fixture, source, state_directory=state)
    target = repoos_fixture / "managed" / "value.txt"
    first_bytes = target.read_bytes()
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=state)
    assert caught.value.code is ExitCode.STALE_PLAN
    assert target.read_bytes() == first_bytes
    summaries = TransactionStore(state).list()
    assert {item["state"] for item in summaries} == {"completed", "failed"}
    assert first["state"] == "completed"


def test_concurrent_same_target_apply_is_refused_by_filesystem_lock(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    state = tmp_path / "state"
    first_holds_lock = threading.Event()
    release_first = threading.Event()
    outcomes: list[object] = []

    def block(point: str) -> None:
        if point.startswith("apply_before_write:"):
            first_holds_lock.set()
            assert release_first.wait(timeout=5)

    def run_first() -> None:
        try:
            outcomes.append(
                execute_plan(
                    plan,
                    repoos_fixture,
                    source,
                    state_directory=state,
                    fault=block,
                )
            )
        except Exception as exc:  # pragma: no cover - asserted through outcomes
            outcomes.append(exc)

    thread = threading.Thread(target=run_first)
    thread.start()
    assert first_holds_lock.wait(timeout=5)
    try:
        with pytest.raises(RepoOSError) as second:
            execute_plan(plan, repoos_fixture, source, state_directory=state)
        assert second.value.code is ExitCode.LOCKED
    finally:
        release_first.set()
        thread.join(timeout=10)
    assert not thread.is_alive()
    assert len(outcomes) == 1
    assert isinstance(outcomes[0], dict)


def test_different_fixture_repositories_apply_concurrently(
    tmp_path: Path,
) -> None:
    first_repo = create_repoos_fixture(tmp_path / "repo-a")
    second_repo = create_repoos_fixture(tmp_path / "repo-b")
    first_source = _source_root(tmp_path, {"a.txt": b"a\n"})
    second_source = _source_root(tmp_path, {"b.txt": b"b\n"})
    first_plan = _plan(first_repo, first_source, ["a.txt=managed/a.txt"])
    second_plan = _plan(second_repo, second_source, ["b.txt=managed/b.txt"])
    state = tmp_path / "state"
    barrier = threading.Barrier(2)
    outcomes: list[object] = []

    def wait_at_write(point: str) -> None:
        if point.startswith("apply_before_write:"):
            barrier.wait(timeout=5)

    def run(plan: dict[str, Any], repository: Path, source: Path) -> None:
        try:
            outcomes.append(
                execute_plan(
                    plan,
                    repository,
                    source,
                    state_directory=state,
                    fault=wait_at_write,
                )
            )
        except Exception as exc:  # pragma: no cover - asserted through outcomes
            outcomes.append(exc)

    threads = [
        threading.Thread(target=run, args=(first_plan, first_repo, first_source)),
        threading.Thread(target=run, args=(second_plan, second_repo, second_source)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert all(not thread.is_alive() for thread in threads)
    assert len(outcomes) == 2
    assert all(isinstance(item, dict) for item in outcomes)
    assert (first_repo / "managed" / "a.txt").read_bytes() == b"a\n"
    assert (second_repo / "managed" / "b.txt").read_bytes() == b"b\n"


def test_schema_reserved_deletion_is_explicitly_unsupported(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    operation = plan["operations"][0]
    operation.update(
        {
            "action": "delete",
            "source": None,
            "source_sha256": None,
            "after_sha256": None,
            "after_mode": None,
            "after_size_bytes": 0,
        }
    )
    _resign(plan)
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=tmp_path / "state")
    assert caught.value.code is ExitCode.UNSAFE_STATE
    assert any(
        failure.startswith("unsupported_delete:")
        for failure in caught.value.details["failed_preconditions"]
    )
    assert not (repoos_fixture / "managed" / "value.txt").exists()


def test_pause_precondition_records_failure_without_target_write(
    repoos_fixture: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source_root(tmp_path, {"value.txt": b"managed\n"})
    plan = _plan(repoos_fixture, source, ["value.txt=managed/value.txt"])
    monkeypatch.setenv("REPOOS_PAUSED", "1")
    state = tmp_path / "state"
    with pytest.raises(RepoOSError) as caught:
        execute_plan(plan, repoos_fixture, source, state_directory=state)
    assert caught.value.code is ExitCode.PAUSED
    assert TransactionStore(state).list()[0]["state"] == "failed"
    assert not (repoos_fixture / "managed" / "value.txt").exists()
