from __future__ import annotations

from pathlib import Path

from conftest import git

from repoos.discovery import discover, inventory_project
from repoos.git import inspect_git


def test_inspect_clean_repository(git_repository: Path) -> None:
    state = inspect_git(git_repository)
    assert state.clean
    assert state.branch == "main"
    assert state.head is not None
    assert state.remote_names == ()
    assert state.worktree_records == 1


def test_inspect_dirty_repository_counts_untracked(git_repository: Path) -> None:
    (git_repository / "untracked.txt").write_text("user work\n", encoding="utf-8")
    state = inspect_git(git_repository)
    assert not state.clean
    assert state.tracked_changes == 0
    assert state.untracked_entries == 1


def test_inventory_non_git_directory(tmp_path: Path) -> None:
    project = tmp_path / "nongit"
    project.mkdir()
    result = inventory_project(project, privacy="local")
    assert result["git_kind"] == "non_git"
    assert result["read_only"] is True


def test_public_inventory_redacts_identity(git_repository: Path) -> None:
    result = inventory_project(git_repository, privacy="public")
    assert result["path"] == "<redacted-private-path>"
    assert result["project"] == "P01"
    git_result = result["git"]
    assert isinstance(git_result, dict)
    assert git_result["head"] == "<redacted>"
    assert "root" not in git_result
    assert "common_dir" not in git_result


def test_discover_scans_only_first_level(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    nested = parent / "nested-repository"
    nested.mkdir(parents=True)
    git(nested, "init", "-b", "main")
    result = discover(tmp_path, privacy="local")
    assert result["directory_count"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["directory"] == "parent"
    assert result["items"][0]["git_kind"] == "non_git"


def test_discover_does_not_modify_registry(tmp_path: Path) -> None:
    (tmp_path / "one").mkdir()
    result = discover(tmp_path)
    assert result["registry_modified"] is False
    assert not (tmp_path / "registry").exists()


def test_discover_does_not_follow_symlinked_directory(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    git(outside, "init", "-b", "main")
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    result = discover(tmp_path, privacy="local")
    assert result["items"][0]["git_kind"] == "symlink_excluded"
    assert result["items"][0]["proposed_registry_state"] == "blocked_symlink"


def test_linked_worktree_uses_common_git_identity(git_repository: Path, tmp_path: Path) -> None:
    linked = tmp_path / "linked"
    git(git_repository, "worktree", "add", "-b", "linked-fixture", str(linked))
    primary = inspect_git(git_repository)
    secondary = inspect_git(linked)
    assert secondary.common_dir == primary.common_dir
    assert (linked / ".git").is_file()
