from __future__ import annotations

from pathlib import Path

from conftest import git

from repoos.discovery import discover, inventory_project
from repoos.planning import apply_dry_run, build_update_plan
from repoos.redaction import redact_text


def test_discovery_preserves_git_status(git_repository: Path, tmp_path: Path) -> None:
    before = git(git_repository, "status", "--porcelain=v1", "--untracked-files=all")
    discover(tmp_path, privacy="public")
    after = git(git_repository, "status", "--porcelain=v1", "--untracked-files=all")
    assert before == after == ""


def test_inventory_preserves_git_status(git_repository: Path) -> None:
    before = git(git_repository, "status", "--porcelain=v1", "--untracked-files=all")
    inventory_project(git_repository, privacy="local")
    after = git(git_repository, "status", "--porcelain=v1", "--untracked-files=all")
    assert before == after == ""


def test_dry_run_does_not_create_state_or_target(repoos_fixture: Path, tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "value.txt").write_text("value\n", encoding="utf-8")
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["value.txt=managed/value.txt"],
        target_version="0.1.0",
    )
    state = tmp_path / "state"
    result = apply_dry_run(plan, repoos_fixture, source, state_directory=state)
    assert result["writes_performed"] == 0
    assert not state.exists()
    assert not (repoos_fixture / "managed").exists()


def test_secret_pattern_does_not_survive_output_redaction() -> None:
    secret = "github_" + "pat_" + "abcdefghijklmnopqrstuvwxyz123456"
    assert secret not in redact_text(f"token={secret}")
