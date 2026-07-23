from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import git

from repoos.errors import RepoOSError
from repoos.planning import apply_dry_run, build_update_plan, read_plan, write_plan
from repoos.validation import repo_root, validate_document


def _source_root(tmp_path: Path, content: str = "managed content\n") -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "component.txt").write_text(content, encoding="utf-8")
    return source


def test_plan_is_deterministic_and_schema_valid(repoos_fixture: Path, tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    first = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
    )
    second = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
    )
    assert first == second
    assert first["plan_id"].startswith("plan-")
    assert first["operations"][0]["action"] == "create"

    plan_path = write_plan(tmp_path / "plan.json", first)
    assert validate_document(plan_path, "update-plan", directory=repo_root() / "schemas") == []
    assert read_plan(plan_path, schema_dir=repo_root() / "schemas") == first


def test_plan_does_not_write_target(repoos_fixture: Path, tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    before = git(repoos_fixture, "status", "--porcelain=v1", "--untracked-files=all")
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
    )
    after = git(repoos_fixture, "status", "--porcelain=v1", "--untracked-files=all")
    assert before == after == ""
    assert plan["operations"]
    assert not (repoos_fixture / "managed" / "component.txt").exists()


def test_non_fixture_explicit_mapping_requires_authorization(
    git_repository: Path,
    tmp_path: Path,
) -> None:
    manifest = git_repository / ".repoos"
    manifest.mkdir()
    manifest_text = (repo_root() / ".repoos" / "project.yaml").read_text(encoding="utf-8")
    (manifest / "project.yaml").write_text(
        manifest_text.replace("project_id: repoos", "project_id: unapproved"),
        encoding="utf-8",
    )
    source = _source_root(tmp_path)
    with pytest.raises(RepoOSError) as caught:
        build_update_plan(
            git_repository,
            source,
            ["component.txt=managed/component.txt"],
            target_version="0.1.0",
        )
    assert caught.value.error_type == "authorization_required"


def test_dirty_fixture_plan_records_conflict(repoos_fixture: Path, tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    (repoos_fixture / "user-work.txt").write_text("preserve me\n", encoding="utf-8")
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
    )
    assert "repository_dirty" in plan["conflicts"]


def test_plan_enforces_change_limits(repoos_fixture: Path, tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
        max_files=1,
        max_bytes=1,
    )
    assert "max_bytes_exceeded" in plan["conflicts"]


def test_plan_records_directory_target_conflict(repoos_fixture: Path, tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    (repoos_fixture / "managed").mkdir()
    (repoos_fixture / "managed" / "component.txt").mkdir()
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
    )
    assert "target_not_regular_file:managed/component.txt" in plan["conflicts"]


def test_apply_dry_run_revalidates_without_writing(repoos_fixture: Path, tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
    )
    result = apply_dry_run(plan, repoos_fixture, source, state_directory=tmp_path / "state")
    assert result["would_apply"] is True
    assert result["writes_performed"] == 0
    assert not (repoos_fixture / "managed" / "component.txt").exists()


def test_apply_dry_run_detects_changed_source(repoos_fixture: Path, tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
    )
    (source / "component.txt").write_text("changed after plan\n", encoding="utf-8")
    result = apply_dry_run(plan, repoos_fixture, source, state_directory=tmp_path / "state")
    assert result["would_apply"] is False
    assert result["failures"] == ["source_changed:component.txt"]


def test_apply_dry_run_detects_stale_base(repoos_fixture: Path, tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
    )
    (repoos_fixture / "later.txt").write_text("later commit\n", encoding="utf-8")
    git(repoos_fixture, "add", "later.txt")
    git(repoos_fixture, "commit", "-m", "Advance fixture base")
    result = apply_dry_run(plan, repoos_fixture, source, state_directory=tmp_path / "state")
    assert result["would_apply"] is False
    assert "stale_base_commit" in result["failures"]


def test_tampered_plan_id_is_rejected(repoos_fixture: Path, tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["component.txt=managed/component.txt"],
        target_version="0.1.0",
    )
    plan["to_version"] = "0.2.0"
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(RepoOSError, match="plan ID"):
        read_plan(path)
