from __future__ import annotations

from pathlib import Path

import pytest

from repoos.errors import RepoOSError
from repoos.paths import contained_path, sha256_bytes, sha256_file, state_root


def test_contained_path_accepts_regular_child(tmp_path: Path) -> None:
    target = contained_path(tmp_path, "nested/file.txt")
    assert target == tmp_path / "nested" / "file.txt"


@pytest.mark.parametrize("value", ["/tmp/outside", "../outside", "nested/../../outside", "a\\b"])
def test_contained_path_rejects_unsafe_values(tmp_path: Path, value: str) -> None:
    with pytest.raises(RepoOSError):
        contained_path(tmp_path, value)


def test_contained_path_rejects_symlink_parent(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(RepoOSError, match="symlink"):
        contained_path(tmp_path, "link/file.txt")


def test_sha256_file_matches_bytes(tmp_path: Path) -> None:
    path = tmp_path / "value.txt"
    path.write_bytes(b"repoos")
    assert sha256_file(path) == sha256_bytes(b"repoos")


def test_state_root_override_is_not_created(tmp_path: Path) -> None:
    requested = tmp_path / "state"
    assert state_root(requested) == requested
    assert not requested.exists()
