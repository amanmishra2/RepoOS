"""Read-only Git inspection with an explicit command allowlist."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from repoos.errors import environment_error, invalid_input
from repoos.paths import canonical_path, require_directory

_READ_ONLY_COMMANDS = {
    "rev-parse",
    "status",
    "remote",
    "worktree",
    "symbolic-ref",
}


def is_git_worktree(path: str | Path) -> bool:
    directory = Path(path)
    return directory.is_dir() and (directory / ".git").exists()


def run_git(repository: str | Path, arguments: list[str], *, allow_failure: bool = False) -> str:
    """Run an allowlisted metadata-only Git command with hooks/fsmonitor disabled."""

    root = require_directory(repository)
    if not arguments or arguments[0] not in _READ_ONLY_COMMANDS:
        raise invalid_input("Git command is not in the read-only allowlist.", arguments=arguments)

    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    command = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-C",
        str(root),
        *arguments,
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise environment_error(
            "Read-only Git inspection failed to start.",
            repository=str(root),
            command=arguments[0],
            reason=str(exc),
        ) from exc
    if result.returncode != 0 and not allow_failure:
        raise environment_error(
            "Read-only Git inspection failed.",
            repository=str(root),
            command=arguments[0],
            returncode=result.returncode,
            stderr=result.stderr.strip(),
        )
    return result.stdout


@dataclass(frozen=True, slots=True)
class GitState:
    root: Path
    common_dir: Path
    branch: str | None
    head: str | None
    upstream: str | None
    ahead: int | None
    behind: int | None
    tracked_changes: int
    untracked_entries: int
    remote_names: tuple[str, ...]
    default_branch: str | None
    worktree_records: int

    @property
    def clean(self) -> bool:
        return self.tracked_changes == 0 and self.untracked_entries == 0

    def as_dict(self, *, include_paths: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "branch": self.branch,
            "head": self.head,
            "upstream": self.upstream,
            "ahead": self.ahead,
            "behind": self.behind,
            "tracked_changes": self.tracked_changes,
            "untracked_entries": self.untracked_entries,
            "clean": self.clean,
            "remote_names": list(self.remote_names),
            "default_branch": self.default_branch,
            "worktree_records": self.worktree_records,
        }
        if include_paths:
            value["root"] = str(self.root)
            value["common_dir"] = str(self.common_dir)
        return value


def _parse_status(output: str) -> dict[str, object]:
    branch: str | None = None
    head: str | None = None
    upstream: str | None = None
    ahead: int | None = None
    behind: int | None = None
    tracked = 0
    untracked = 0

    for line in output.splitlines():
        if line.startswith("# branch.oid "):
            value = line.removeprefix("# branch.oid ").strip()
            head = None if value == "(initial)" else value
        elif line.startswith("# branch.head "):
            value = line.removeprefix("# branch.head ").strip()
            branch = None if value == "(detached)" else value
        elif line.startswith("# branch.upstream "):
            upstream = line.removeprefix("# branch.upstream ").strip() or None
        elif line.startswith("# branch.ab "):
            fields = line.removeprefix("# branch.ab ").split()
            if len(fields) == 2:
                ahead = int(fields[0].removeprefix("+"))
                behind = int(fields[1].removeprefix("-"))
        elif line.startswith(("1 ", "2 ", "u ")):
            tracked += 1
        elif line.startswith("? "):
            untracked += 1

    return {
        "branch": branch,
        "head": head,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "tracked_changes": tracked,
        "untracked_entries": untracked,
    }


def inspect_git(repository: str | Path) -> GitState:
    """Inspect one explicit working tree without refreshing or mutating it."""

    candidate = require_directory(repository)
    if not is_git_worktree(candidate):
        raise invalid_input("Directory is not a Git working tree.", repository=str(candidate))

    root_text = run_git(candidate, ["rev-parse", "--show-toplevel"]).strip()
    common_text = run_git(candidate, ["rev-parse", "--git-common-dir"]).strip()
    root = canonical_path(root_text, must_exist=True)
    common_candidate = Path(common_text)
    if not common_candidate.is_absolute():
        common_candidate = root / common_candidate
    common_dir = canonical_path(common_candidate, must_exist=True)

    status = _parse_status(
        run_git(
            candidate,
            ["status", "--porcelain=v2", "--branch", "--untracked-files=all"],
        )
    )
    remotes = tuple(
        line.strip()
        for line in run_git(candidate, ["remote"], allow_failure=True).splitlines()
        if line.strip()
    )
    default_ref = run_git(
        candidate,
        ["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
        allow_failure=True,
    ).strip()
    default_branch = default_ref.removeprefix("refs/remotes/") if default_ref else None
    worktree_text = run_git(candidate, ["worktree", "list", "--porcelain"], allow_failure=True)
    worktree_records = sum(1 for line in worktree_text.splitlines() if line.startswith("worktree "))
    tracked_value = status["tracked_changes"]
    untracked_value = status["untracked_entries"]

    return GitState(
        root=root,
        common_dir=common_dir,
        branch=status["branch"] if isinstance(status["branch"], str) else None,
        head=status["head"] if isinstance(status["head"], str) else None,
        upstream=status["upstream"] if isinstance(status["upstream"], str) else None,
        ahead=status["ahead"] if isinstance(status["ahead"], int) else None,
        behind=status["behind"] if isinstance(status["behind"], int) else None,
        tracked_changes=tracked_value if isinstance(tracked_value, int) else 0,
        untracked_entries=untracked_value if isinstance(untracked_value, int) else 0,
        remote_names=remotes,
        default_branch=default_branch,
        worktree_records=worktree_records,
    )
