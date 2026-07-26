from __future__ import annotations

import json
import os
import socket
from datetime import UTC, datetime
from pathlib import Path

import pytest

from repoos.errors import RepoOSError
from repoos.locks import GlobalLock, RepositoryLock, lock_key, repository_lock_path
from repoos.pause import get_pause_status


def test_environment_pause_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("REPOOS_PAUSED", "true")
    status = get_pause_status(tmp_path)
    assert status.paused
    assert status.source == "environment:REPOOS_PAUSED"


def test_state_file_pause(tmp_path: Path) -> None:
    (tmp_path / "PAUSED").write_text("maintenance\n", encoding="utf-8")
    status = get_pause_status(tmp_path)
    assert status.paused
    assert status.source == "state_file"


def test_false_environment_value_does_not_pause(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("REPOOS_PAUSED", "off")
    assert not get_pause_status(tmp_path).paused


def test_lock_contention_fails_closed(tmp_path: Path) -> None:
    first = RepositoryLock(tmp_path, "fixture-common-git-dir")
    second = RepositoryLock(tmp_path, "fixture-common-git-dir")
    first.acquire()
    try:
        with pytest.raises(RepoOSError) as caught:
            second.acquire()
        assert caught.value.error_type == "lock_conflict"
    finally:
        first.release()


def test_lock_releases_and_can_be_reacquired(tmp_path: Path) -> None:
    identity = "fixture-common-git-dir"
    with RepositoryLock(tmp_path, identity):
        assert (tmp_path / "locks" / "repositories" / f"{lock_key(identity)}.lock").is_file()
    with RepositoryLock(tmp_path, identity):
        pass


def _stale_payload(*, pid: int = 999_999) -> dict[str, object]:
    return {
        "pid": pid,
        "hostname": socket.gethostname(),
        "start_time": datetime(2026, 7, 23, tzinfo=UTC).isoformat(),
        "target": "fixture",
        "transaction_id": "tx-fixture",
        "kind": "repository",
        "owner_token": "stale-owner",
    }


def test_stale_lock_requires_explicit_recovery(tmp_path: Path) -> None:
    identity = "fixture-common-dir"
    path = repository_lock_path(tmp_path, identity)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(_stale_payload()), encoding="utf-8")
    with pytest.raises(RepoOSError) as caught:
        RepositoryLock(tmp_path, identity).acquire()
    assert caught.value.error_type == "stale_lock"
    assert path.is_file()

    lock = RepositoryLock(tmp_path, identity, recover_stale=True)
    lock.acquire()
    try:
        assert path.is_file()
        recovered = list(path.parent.glob(f"{path.name}.recovered.*"))
        assert len(recovered) == 1
    finally:
        lock.release()


def test_malformed_lock_requires_explicit_recovery(tmp_path: Path) -> None:
    identity = "malformed-common-dir"
    path = repository_lock_path(tmp_path, identity)
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(RepoOSError) as caught:
        RepositoryLock(tmp_path, identity).acquire()
    assert caught.value.error_type == "malformed_lock"
    with RepositoryLock(tmp_path, identity, recover_stale=True):
        assert path.is_file()


def test_different_repository_locks_can_coexist(tmp_path: Path) -> None:
    first = RepositoryLock(tmp_path, "common-a", transaction_id="tx-a")
    second = RepositoryLock(tmp_path, "common-b", transaction_id="tx-b")
    first.acquire()
    try:
        second.acquire()
        try:
            assert first.path != second.path
            assert first.path.is_file()
            assert second.path.is_file()
        finally:
            second.release()
    finally:
        first.release()


def test_lock_metadata_contains_required_owner_fields(tmp_path: Path) -> None:
    lock = RepositoryLock(
        tmp_path,
        "fixture",
        target="/tmp/fixture",
        transaction_id="tx-20260723T120000Z-aaaaaaaaaaaa",
    )
    lock.acquire()
    try:
        value = json.loads(lock.path.read_text(encoding="utf-8"))
        assert value["pid"] == os.getpid()
        assert value["hostname"] == socket.gethostname()
        assert value["target"] == "/tmp/fixture"
        assert value["transaction_id"] == "tx-20260723T120000Z-aaaaaaaaaaaa"
        assert value["start_time"]
    finally:
        lock.release()


def test_global_metadata_lock_is_process_visible(tmp_path: Path) -> None:
    with GlobalLock(tmp_path, transaction_id="tx-global") as lock:
        assert lock.path == tmp_path / "locks" / "global.lock"
        assert lock.path.is_file()
