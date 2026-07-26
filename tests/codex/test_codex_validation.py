from __future__ import annotations

import json
from pathlib import Path

from repoos.validation import (
    repo_root,
    validate_agents,
    validate_codex_config,
    validate_hooks,
    validate_markdown_links,
    validate_recurring_specs,
    validate_skills,
    validate_version_sources,
    validate_workflow,
)


def test_repoos_active_codex_surfaces_are_valid() -> None:
    root = repo_root()
    assert validate_codex_config(root / ".codex" / "config.toml") == []
    assert validate_agents(root / ".codex" / "agents") == []
    assert validate_skills(root / ".agents" / "skills") == []
    assert validate_hooks(root / ".codex" / "hooks.json") == []


def test_config_rejects_unknown_project_keys(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[workflow]\nmode = 'unsafe'\n", encoding="utf-8")
    findings = validate_codex_config(path)
    assert any("Unsupported project config keys" in finding.message for finding in findings)


def test_markdown_agent_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "obsolete.md").write_text("# agent\n", encoding="utf-8")
    findings = validate_agents(tmp_path)
    assert any("obsolete" in finding.message for finding in findings)


def test_agent_requires_all_current_fields(tmp_path: Path) -> None:
    (tmp_path / "partial.toml").write_text("name = 'partial'\n", encoding="utf-8")
    findings = validate_agents(tmp_path)
    assert any("description" in finding.message for finding in findings)
    assert any("developer_instructions" in finding.message for finding in findings)


def test_skill_requires_frontmatter(tmp_path: Path) -> None:
    skill = tmp_path / "missing"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Missing metadata\n", encoding="utf-8")
    findings = validate_skills(tmp_path)
    assert any("front matter" in finding.message for finding in findings)


def test_old_hook_shape_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "hooks.json"
    path.write_text(json.dumps({"PreToolUse": []}), encoding="utf-8")
    findings = validate_hooks(path)
    assert any("top-level 'hooks'" in finding.message for finding in findings)


def test_hook_handler_requires_command_type(tmp_path: Path) -> None:
    path = tmp_path / "hooks.json"
    value = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"command": "true"}]}]}}
    path.write_text(json.dumps(value), encoding="utf-8")
    findings = validate_hooks(path)
    assert any("type=command" in finding.message for finding in findings)


def test_repoos_workflow_meets_initial_policy() -> None:
    workflows = (repo_root() / ".github" / "workflows").glob("*.y*ml")
    assert all(validate_workflow(path) == [] for path in workflows)


def test_workflow_rejects_self_hosted_and_floating_action(tmp_path: Path) -> None:
    path = tmp_path / "workflow.yml"
    path.write_text(
        "\n".join(
            [
                "name: unsafe",
                "on: [pull_request]",
                "permissions:",
                "  contents: read",
                "concurrency: unsafe",
                "jobs:",
                "  test:",
                "    runs-on: [self-hosted, macOS]",
                "    timeout-minutes: 10",
                "    steps:",
                "      - uses: actions/checkout@v4",
                "",
            ]
        ),
        encoding="utf-8",
    )
    findings = validate_workflow(path)
    assert any("self-hosted" in finding.message for finding in findings)
    assert any("full SHA" in finding.message for finding in findings)


def test_repoos_internal_links_and_recurring_specs_are_valid() -> None:
    root = repo_root()
    assert validate_markdown_links(root) == []
    assert validate_recurring_specs(root / "automation" / "recurring") == []
    assert validate_version_sources(root) == []


def test_broken_internal_link_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("[missing](docs/missing.md)\n", encoding="utf-8")
    findings = validate_markdown_links(tmp_path)
    assert any("Broken local link" in finding.message for finding in findings)


def test_recurring_spec_must_be_read_only(tmp_path: Path) -> None:
    for name in (
        "daily-health.yaml",
        "weekly-review.yaml",
        "biweekly-proposal.yaml",
        "monthly-architecture-audit.yaml",
    ):
        (tmp_path / name).write_text(
            "schema_version: 1\nread_only: false\nexternal_writes: false\n",
            encoding="utf-8",
        )
    findings = validate_recurring_specs(tmp_path)
    assert len(findings) == 4
    assert all("read_only" in finding.message for finding in findings)
