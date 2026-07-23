"""Shared neutral fixtures."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from repoos import __version__


def git(repository: Path, *arguments: str) -> str:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        [
            "git",
            "-c",
            "user.name=RepoOS Tests",
            "-c",
            "user.email=repoos-tests@example.invalid",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(repository),
            *arguments,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return result.stdout


def create_repoos_fixture(
    repository: Path,
    *,
    validation_argv: list[str] | None = None,
) -> Path:
    """Create a disposable, committed, explicitly marked fixture repository."""

    repository.mkdir()
    git(repository, "init", "-b", "main")
    (repository / "README.md").write_text("fixture\n", encoding="utf-8")
    git(repository, "add", "README.md")
    git(repository, "commit", "-m", "Initial fixture")
    (repository / ".repoos-fixture").write_text("neutral fixture only\n", encoding="utf-8")
    manifest_directory = repository / ".repoos"
    manifest_directory.mkdir()
    command = validation_argv or ["python3", "-c", "print('fixture')"]
    (manifest_directory / "project.yaml").write_text(
        "\n".join(
            [
                "manifest_version: 1",
                "project_id: neutral-fixture",
                f"repoos_version: {__version__}",
                "project_family: null",
                "additional_overlays: []",
                "components:",
                "  managed: []",
                "  generated: []",
                "  repository_owned: [fixture-source]",
                "  extensions: []",
                "  excluded: []",
                "adoption_channel: experimental",
                "local_overrides: []",
                "verification:",
                "  - name: tests",
                f"    argv: {json.dumps(command)}",
                "automation_permissions:",
                "  read_only: true",
                "  plan: true",
                "  apply: true",
                "  commit: false",
                "  push: false",
                "  external_settings: false",
                "last_successful_audit: null",
                "",
            ]
        ),
        encoding="utf-8",
    )
    git(repository, "add", ".repoos-fixture", ".repoos/project.yaml")
    git(repository, "commit", "-m", "Mark neutral RepoOS fixture")
    return repository


@pytest.fixture
def git_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init", "-b", "main")
    (repository / "README.md").write_text("fixture\n", encoding="utf-8")
    git(repository, "add", "README.md")
    git(repository, "commit", "-m", "Initial fixture")
    return repository


@pytest.fixture
def repoos_fixture(git_repository: Path) -> Path:
    repository = git_repository
    (repository / ".repoos-fixture").write_text("neutral fixture only\n", encoding="utf-8")
    manifest_directory = repository / ".repoos"
    manifest_directory.mkdir()
    (manifest_directory / "project.yaml").write_text(
        "\n".join(
            [
                "manifest_version: 1",
                "project_id: neutral-fixture",
                f"repoos_version: {__version__}",
                "project_family: null",
                "additional_overlays: []",
                "components:",
                "  managed: []",
                "  generated: []",
                "  repository_owned: [fixture-source]",
                "  extensions: []",
                "  excluded: []",
                "adoption_channel: experimental",
                "local_overrides: []",
                "verification:",
                "  - name: tests",
                "    argv: [python3, -c, \"print('fixture')\"]",
                "automation_permissions:",
                "  read_only: true",
                "  plan: true",
                "  apply: true",
                "  commit: false",
                "  push: false",
                "  external_settings: false",
                "last_successful_audit: null",
                "",
            ]
        ),
        encoding="utf-8",
    )
    git(repository, "add", ".repoos-fixture", ".repoos/project.yaml")
    git(repository, "commit", "-m", "Mark neutral RepoOS fixture")
    return repository
