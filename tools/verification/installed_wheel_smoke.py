"""Offline installed-wheel smoke for fixture update and manifest bootstrap."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import venv
from pathlib import Path
from typing import Any


def _run(
    arguments: list[str],
    *,
    cwd: Path | None = None,
    parse_json: bool = False,
) -> dict[str, Any] | str:
    completed = subprocess.run(
        arguments,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        timeout=120,
    )
    if parse_json:
        value = json.loads(completed.stdout)
        if not isinstance(value, dict):
            raise RuntimeError("Expected a JSON object from installed RepoOS.")
        return value
    return completed.stdout


def _git(repository: Path, *arguments: str) -> str:
    return str(
        _run(
            [
                "git",
                "-c",
                "user.name=RepoOS Wheel Smoke",
                "-c",
                "user.email=repoos-wheel@example.invalid",
                "-c",
                "core.hooksPath=/dev/null",
                "-C",
                str(repository),
                *arguments,
            ]
        )
    )


def _create_repository(path: Path) -> Path:
    path.mkdir()
    _git(path, "init", "-b", "main")
    (path / "README.md").write_text("installed-wheel synthetic repository\n", encoding="utf-8")
    (path / "validate.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    _git(path, "add", "README.md", "validate.py")
    _git(path, "commit", "-m", "Create installed-wheel repository")
    return path


def _manifest(path: Path, version: str, *, apply: bool) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "manifest_version: 1",
                "project_id: installed-wheel-synthetic",
                f"repoos_version: {version}",
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
                f"  apply: {'true' if apply else 'false'}",
                "  commit: false",
                "  push: false",
                "  external_settings: false",
                "last_successful_audit: null",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _fixture_flow(repoos: Path, root: Path, version: str) -> None:
    repository = _create_repository(root / "fixture")
    (repository / ".repoos-fixture").write_text("neutral fixture only\n", encoding="utf-8")
    _manifest(repository / ".repoos" / "project.yaml", version, apply=True)
    _git(repository, "add", ".repoos-fixture", ".repoos/project.yaml")
    _git(repository, "commit", "-m", "Mark installed-wheel fixture")
    source = root / "source"
    source.mkdir()
    (source / "value.txt").write_text("managed\n", encoding="utf-8")
    plan = root / "fixture-plan.json"
    state = root / "fixture-state"
    _run(
        [
            str(repoos),
            "--format",
            "json",
            "plan-update",
            "--repo",
            str(repository),
            "--source-root",
            str(source),
            "--file",
            "value.txt=managed/value.txt",
            "--output",
            str(plan),
        ],
        parse_json=True,
    )
    _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "apply",
            "--plan",
            str(plan),
            "--dry-run",
        ],
        parse_json=True,
    )
    applied = _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "apply",
            "--plan",
            str(plan),
            "--execute",
        ],
        parse_json=True,
    )
    assert isinstance(applied, dict)
    _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "rollback",
            "--transaction",
            str(applied["transaction_id"]),
        ],
        parse_json=True,
    )


def _manifest_bootstrap_flow(repoos: Path, root: Path, version: str) -> None:
    repository = _create_repository(root / "real")
    manifest = _manifest(root / "manifest.yaml", version, apply=False)
    plan = root / "bootstrap-plan.json"
    state = root / "bootstrap-state"
    _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "plan-manifest-bootstrap",
            "--repo",
            str(repository),
            "--manifest-input",
            str(manifest),
            "--output",
            str(plan),
        ],
        parse_json=True,
    )
    preview = _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "apply",
            "--plan",
            str(plan),
            "--dry-run",
        ],
        parse_json=True,
    )
    assert isinstance(preview, dict)
    assert preview["ready_for_authorization"] is True
    assert not state.exists()
    authorization_result = _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "authorize-manifest-bootstrap",
            "--plan",
            str(plan),
            "--expires-in",
            "600",
            "--approve",
        ],
        parse_json=True,
    )
    assert isinstance(authorization_result, dict)
    applied = _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "apply",
            "--plan",
            str(plan),
            "--authorization",
            str(authorization_result["authorization"]),
            "--execute",
        ],
        parse_json=True,
    )
    assert isinstance(applied, dict)
    transaction_id = str(applied["transaction_id"])
    shown = _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "transaction",
            "show",
            transaction_id,
        ],
        parse_json=True,
    )
    assert isinstance(shown, dict)
    assert shown["transaction"]["operation_kind"] == "manifest_bootstrap"
    _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "transaction",
            "list",
        ],
        parse_json=True,
    )
    _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "rollback",
            "--transaction",
            transaction_id,
        ],
        parse_json=True,
    )
    repeated = _run(
        [
            str(repoos),
            "--format",
            "json",
            "--state-dir",
            str(state),
            "rollback",
            "--transaction",
            transaction_id,
        ],
        parse_json=True,
    )
    assert isinstance(repeated, dict)
    assert repeated["already_rolled_back"] is True
    assert _git(repository, "status", "--porcelain=v1", "--untracked-files=all") == ""


def main() -> int:
    repository = Path(__file__).resolve().parents[2]
    version = (repository / "VERSION").read_text(encoding="utf-8").strip()
    wheel = repository / "dist" / f"repoos-{version}-py3-none-any.whl"
    if not wheel.is_file():
        raise RuntimeError(f"Expected built wheel: {wheel}")
    with tempfile.TemporaryDirectory(prefix="repoos-wheel-smoke-") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        venv.EnvBuilder(
            with_pip=True,
            system_site_packages=True,
            clear=True,
        ).create(environment)
        python = environment / "bin" / "python"
        repoos = environment / "bin" / "repoos"
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-deps",
                "--force-reinstall",
                str(wheel),
            ]
        )
        version_output = _run([str(repoos), "--version"])
        assert isinstance(version_output, str)
        assert version_output.strip() == f"repoos {version}"
        _run(
            [
                str(repoos),
                "--format",
                "json",
                "--root",
                str(root),
                "doctor",
            ],
            parse_json=True,
        )
        _fixture_flow(repoos, root, version)
        _manifest_bootstrap_flow(repoos, root, version)
    print("installed wheel smoke passed: fixture_update, manifest_bootstrap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
