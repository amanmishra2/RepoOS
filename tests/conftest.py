"""Shared neutral fixtures."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


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
                "repoos_version: 0.1.0",
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
    git(repository, "add", ".repoos-fixture", ".repoos/project.yaml")
    git(repository, "commit", "-m", "Mark neutral RepoOS fixture")
    return repository
