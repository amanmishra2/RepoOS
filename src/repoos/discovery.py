"""Bounded first-level repository discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from repoos.git import inspect_git, is_git_worktree
from repoos.paths import require_directory

_SKIP_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".cache",
    "build",
    "dist",
    "target",
}


def discover(root: str | Path, *, privacy: str = "public") -> dict[str, Any]:
    """Inspect only direct child directories beneath an explicit root."""

    portfolio_root = require_directory(root)
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    directories = sorted(
        (
            child
            for child in portfolio_root.iterdir()
            if child.name not in _SKIP_NAMES and (child.is_dir() or child.is_symlink())
        ),
        key=lambda child: child.name.casefold(),
    )
    for index, directory in enumerate(directories, start=1):
        alias = f"P{index:02d}"
        public = privacy == "public"
        item: dict[str, Any] = {
            "project_id": alias,
            "directory": alias if public else directory.name,
            "path": "<redacted-private-path>" if public else str(directory),
            "git_kind": "non_git",
            "proposed_registry_state": "unclassified",
        }
        if directory.is_symlink():
            item["git_kind"] = "symlink_excluded"
            item["proposed_registry_state"] = "blocked_symlink"
            items.append(item)
            continue
        if is_git_worktree(directory):
            try:
                state = inspect_git(directory)
            except Exception as exc:  # normalized into bounded evidence, not a traversal abort
                item["git_kind"] = "git_error"
                item["proposed_registry_state"] = "blocked"
                errors.append(
                    {
                        "project_id": alias,
                        "error": "git_inspection_failed" if public else str(exc),
                    }
                )
            else:
                item["git_kind"] = (
                    "linked_worktree" if (directory / ".git").is_file() else "repository"
                )
                item["git"] = state.as_dict(include_paths=not public)
                if public:
                    git_value = item["git"]
                    if isinstance(git_value, dict):
                        git_value["head"] = "<redacted>"
                        git_value["branch"] = "<redacted>"
                        git_value["upstream"] = "<redacted>" if state.upstream else None
                item["proposed_registry_state"] = "candidate" if state.clean else "blocked_dirty"
        items.append(item)

    return {
        "schema_version": "repoos.discovery.v1",
        "root": "~/<configured-root>" if privacy == "public" else str(portfolio_root),
        "privacy": privacy,
        "read_only": True,
        "directory_count": len(directories),
        "items": items,
        "errors": errors,
        "registry_modified": False,
    }


def inventory_project(project: str | Path, *, privacy: str = "public") -> dict[str, Any]:
    directory = require_directory(project)
    public = privacy == "public"
    result: dict[str, Any] = {
        "schema_version": "repoos.project-inventory.v1",
        "project": directory.name if not public else "P01",
        "path": str(directory) if not public else "<redacted-private-path>",
        "read_only": True,
        "git_kind": "non_git",
    }
    if is_git_worktree(directory):
        state = inspect_git(directory)
        result["git_kind"] = "linked_worktree" if (directory / ".git").is_file() else "repository"
        result["git"] = state.as_dict(include_paths=not public)
        if public and isinstance(result["git"], dict):
            result["git"]["head"] = "<redacted>"
            result["git"]["branch"] = "<redacted>"
            result["git"]["upstream"] = "<redacted>" if state.upstream else None
    return result
