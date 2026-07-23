from __future__ import annotations

from pathlib import Path

import pytest

from repoos.errors import RepoOSError
from repoos.locks import RepositoryLock, lock_key
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
        assert caught.value.error_type == "lock_contended"
    finally:
        first.release()


def test_lock_releases_and_can_be_reacquired(tmp_path: Path) -> None:
    identity = "fixture-common-git-dir"
    with RepositoryLock(tmp_path, identity):
        assert (tmp_path / "locks" / f"{lock_key(identity)}.lock").is_file()
    with RepositoryLock(tmp_path, identity):
        pass
