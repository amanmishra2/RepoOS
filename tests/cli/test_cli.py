from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import git

from repoos import __version__
from repoos.cli import build_parser, main
from repoos.validation import repo_root


def test_top_level_help_lists_minimum_commands() -> None:
    help_text = build_parser().format_help()
    for command in (
        "discover",
        "inventory",
        "status",
        "doctor",
        "validate",
        "diff",
        "audit",
        "check-update",
        "plan-update",
        "plan-manifest-bootstrap",
        "authorize-manifest-bootstrap",
        "apply",
        "rollback",
        "transaction",
        "report",
    ):
        assert command in help_text


def test_doctor_json(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    exit_code = main(
        [
            "--format",
            "json",
            "--root",
            str(tmp_path),
            "--state-dir",
            str(tmp_path / "state"),
            "doctor",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["ok"] is True
    assert captured.err == ""
    assert not (tmp_path / "state").exists()


def test_doctor_missing_root_has_environment_exit(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = main(
        [
            "--format",
            "json",
            "--root",
            str(tmp_path / "missing"),
            "doctor",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 8
    assert json.loads(captured.err)["error"]["type"] == "environment_error"


def test_validate_actual_registry(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--format",
            "json",
            "validate",
            str(repo_root() / "registry" / "projects.yaml"),
            "--schema",
            "project-registry",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["ok"] is True


def test_invalid_document_has_stable_exit_code(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{}", encoding="utf-8")
    exit_code = main(["--format", "json", "validate", str(path), "--schema", "project-registry"])
    captured = capsys.readouterr()
    assert exit_code == 3
    assert json.loads(captured.err)["error"]["type"] == "validation_failed"


def test_apply_execute_requires_an_existing_plan(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    exit_code = main(
        [
            "--format",
            "json",
            "apply",
            "--plan",
            str(tmp_path / "missing.json"),
            "--repository",
            str(tmp_path),
            "--source-root",
            str(tmp_path),
            "--execute",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 2
    assert json.loads(captured.err)["error"]["type"] == "invalid_input"


def test_plan_output_inside_target_is_refused(
    capsys: pytest.CaptureFixture[str],
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "value.txt").write_text("value\n", encoding="utf-8")
    exit_code = main(
        [
            "--format",
            "json",
            "plan-update",
            "--repository",
            str(repoos_fixture),
            "--source-root",
            str(source),
            "--file",
            "value.txt=managed/value.txt",
            "--output",
            str(repoos_fixture / "plan.json"),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 4
    assert json.loads(captured.err)["error"]["type"] == "unsafe_state"
    assert not (repoos_fixture / "plan.json").exists()


def test_report_normalizes_json(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    path.write_text('{"z": 1, "a": 2}', encoding="utf-8")
    exit_code = main(["--format", "json", "report", "--input", str(path)])
    captured = capsys.readouterr()
    value = json.loads(captured.out)
    assert exit_code == 0
    assert value["document"] == {"a": 2, "z": 1}


def test_transactional_cli_end_to_end_json(
    capsys: pytest.CaptureFixture[str],
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "value.txt").write_text("managed\n", encoding="utf-8")
    plan_path = tmp_path / "plan.json"
    state = tmp_path / "state"

    exit_code = main(
        [
            "--format",
            "json",
            "plan-update",
            "--repo",
            str(repoos_fixture),
            "--source-root",
            str(source),
            "--file",
            "value.txt=managed/value.txt",
            "--output",
            str(plan_path),
        ]
    )
    planned = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert planned["operation_count"] == 1

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "apply",
            "--plan",
            str(plan_path),
            "--dry-run",
        ]
    )
    preview = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert preview["would_apply"] is True
    assert preview["state_writes_performed"] == 0
    assert not state.exists()

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "apply",
            "--plan",
            str(plan_path),
            "--execute",
        ]
    )
    applied = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    transaction_id = applied["transaction_id"]
    assert applied["state"] == "completed"

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "transaction",
            "show",
            transaction_id,
        ]
    )
    shown = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert shown["transaction"]["state"] == "completed"
    assert shown["transaction"]["affected_files"][0]["ownership"] == "managed_file"

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "transaction",
            "list",
        ]
    )
    listed = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert listed["count"] == 1

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "rollback",
            "--transaction",
            transaction_id,
        ]
    )
    rolled_back = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert rolled_back["state"] == "rolled_back"
    assert not (repoos_fixture / "managed" / "value.txt").exists()


def test_manifest_bootstrap_cli_end_to_end_json(
    capsys: pytest.CaptureFixture[str],
    git_repository: Path,
    tmp_path: Path,
) -> None:
    (git_repository / "validate.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    git(git_repository, "add", "validate.py")
    git(git_repository, "commit", "-m", "Add synthetic validation")
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "\n".join(
            [
                "manifest_version: 1",
                "project_id: synthetic-cli",
                f"repoos_version: {__version__}",
                "project_family: synthetic-python",
                "sensitivity_classification: internal",
                "additional_overlays: []",
                "components:",
                "  managed: []",
                "  generated: []",
                "  repository_owned: [project-source]",
                "  extensions: []",
                "  excluded: []",
                "adoption_channel: canary",
                "local_overrides: []",
                "verification:",
                "  - name: tests",
                "    argv: [python3, validate.py]",
                "automation_permissions:",
                "  read_only: true",
                "  plan: true",
                "  apply: false",
                "  commit: false",
                "  push: false",
                "  external_settings: false",
                "last_successful_audit: null",
                "",
            ]
        ),
        encoding="utf-8",
    )
    plan = tmp_path / "bootstrap-plan.json"
    state = tmp_path / "state"
    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "plan-manifest-bootstrap",
            "--repo",
            str(git_repository),
            "--manifest-input",
            str(manifest),
            "--output",
            str(plan),
        ]
    )
    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["operation_kind"] == "manifest_bootstrap"

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "apply",
            "--plan",
            str(plan),
            "--dry-run",
        ]
    )
    preview = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert preview["ready_for_authorization"] is True
    assert preview["authorization_status"] == "missing"
    assert not state.exists()

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "apply",
            "--plan",
            str(plan),
            "--execute",
        ]
    )
    missing = json.loads(capsys.readouterr().err)
    assert exit_code == 9
    assert missing["error"]["type"] == "missing_authorization"
    assert not state.exists()

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "authorize-manifest-bootstrap",
            "--plan",
            str(plan),
            "--approve",
            "--expires-in",
            "600",
        ]
    )
    authorization_result = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    authorization = authorization_result["authorization"]

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "apply",
            "--plan",
            str(plan),
            "--authorization",
            authorization,
            "--execute",
        ]
    )
    applied = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert applied["authorization"] == "consumed"
    assert (git_repository / ".repoos" / "project.yaml").is_file()

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "transaction",
            "show",
            applied["transaction_id"],
        ]
    )
    shown = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert shown["transaction"]["operation_kind"] == "manifest_bootstrap"

    exit_code = main(
        [
            "--format",
            "json",
            "--state-dir",
            str(state),
            "rollback",
            "--transaction",
            applied["transaction_id"],
        ]
    )
    rolled_back = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert rolled_back["state"] == "rolled_back"
    assert not (git_repository / ".repoos").exists()


def test_manifest_bootstrap_plan_output_cannot_write_a_sibling_worktree(
    capsys: pytest.CaptureFixture[str],
    git_repository: Path,
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    sibling = tmp_path / "sibling"
    git(git_repository, "worktree", "add", "-b", "bootstrap-target", str(target))
    git(git_repository, "worktree", "add", "-b", "protected-sibling", str(sibling))
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "\n".join(
            [
                "manifest_version: 1",
                "project_id: synthetic-cli",
                f"repoos_version: {__version__}",
                "project_family: null",
                "sensitivity_classification: internal",
                "additional_overlays: []",
                "components:",
                "  managed: []",
                "  generated: []",
                "  repository_owned: []",
                "  extensions: []",
                "  excluded: []",
                "adoption_channel: canary",
                "local_overrides: []",
                "verification:",
                "  - name: tests",
                "    argv: [python3, -m, pytest]",
                "automation_permissions:",
                "  read_only: true",
                "  plan: true",
                "  apply: false",
                "  commit: false",
                "  push: false",
                "  external_settings: false",
                "last_successful_audit: null",
                "",
            ]
        ),
        encoding="utf-8",
    )
    output = sibling / "bootstrap-plan.json"

    exit_code = main(
        [
            "--format",
            "json",
            "plan-manifest-bootstrap",
            "--repo",
            str(target),
            "--manifest-input",
            str(manifest),
            "--output",
            str(output),
        ]
    )
    error = json.loads(capsys.readouterr().err)
    assert exit_code == 4
    assert error["error"]["type"] == "unsafe_state"
    assert not output.exists()
