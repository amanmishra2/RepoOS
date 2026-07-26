"""Read-only Git inspection with an explicit command allowlist."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repoos.errors import RepoOSError, environment_error, invalid_input, unsafe_state
from repoos.paths import canonical_path, require_directory, sha256_bytes

_READ_ONLY_COMMANDS = {
    "check-ignore",
    "for-each-ref",
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


def status_fingerprint(repository: str | Path) -> str:
    """Hash the exact branch-aware porcelain state used by plan preconditions."""

    output = run_git(
        repository,
        ["status", "--porcelain=v2", "--branch", "--untracked-files=all"],
    )
    return sha256_bytes(output.encode("utf-8"))


def status_paths(repository: str | Path) -> tuple[str, ...]:
    """Return dirty paths without reading file contents.

    Rename/copy records are conservatively represented by both NUL-delimited path
    fields so rollback cannot mistake an unrelated rename for transaction output.
    """

    output = run_git(
        repository,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    )
    fields = output.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(fields):
        entry = fields[index]
        index += 1
        if not entry:
            continue
        if len(entry) < 4:
            paths.append(entry)
            continue
        status_code = entry[:2]
        path = entry[3:]
        if path:
            paths.append(path)
        if ("R" in status_code or "C" in status_code) and index < len(fields):
            related = fields[index]
            index += 1
            if related:
                paths.append(related)
    return tuple(sorted(set(paths)))


def path_is_ignored(repository: str | Path, relative_path: str) -> bool:
    """Check one explicit path against Git ignore rules without touching the index."""

    output = run_git(
        repository,
        ["check-ignore", "--no-index", "--", relative_path],
        allow_failure=True,
    )
    return bool(output.strip())


_OBJECT_ID = re.compile(r"^[a-f0-9]{40,64}$")


@dataclass(frozen=True, slots=True)
class _WorktreeRecord:
    path: Path
    head: str
    branch: str | None
    detached: bool
    locked: bool
    prunable: bool
    bare: bool


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256_bytes(payload)


def _metadata_file_digest(path: Path) -> str:
    if not path.exists():
        return sha256_bytes(b"missing")
    if path.is_symlink() or not path.is_file():
        raise unsafe_state(
            "Git metadata is not a regular file.",
            metadata_kind=path.name,
        )
    return sha256_bytes(path.read_bytes())


def _resolve_git_dir(worktree: Path) -> Path:
    value = run_git(worktree, ["rev-parse", "--git-dir"]).strip()
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = worktree / candidate
    return canonical_path(candidate, must_exist=True)


def _parse_worktree_records(output: str) -> list[_WorktreeRecord]:
    records: list[_WorktreeRecord] = []
    fields: dict[str, str | bool] = {}

    def finish() -> None:
        nonlocal fields
        if not fields:
            return
        allowed = {"worktree", "HEAD", "branch", "detached", "locked", "prunable", "bare"}
        unknown = sorted(set(fields) - allowed)
        if unknown:
            raise unsafe_state(
                "Git worktree metadata contains unsupported fields.",
                field_count=len(unknown),
            )
        path_text = fields.get("worktree")
        head = fields.get("HEAD")
        branch = fields.get("branch")
        detached = fields.get("detached") is True
        bare = fields.get("bare") is True
        if not isinstance(path_text, str) or not path_text:
            raise unsafe_state("Git worktree metadata has no usable path.")
        if bare:
            head_text = str(head or "0" * 40)
        elif not isinstance(head, str) or _OBJECT_ID.fullmatch(head) is None:
            raise unsafe_state("Git worktree metadata has no valid HEAD.")
        else:
            head_text = head
        if bool(branch) == detached and not bare:
            raise unsafe_state("Git worktree branch metadata is ambiguous.")
        records.append(
            _WorktreeRecord(
                path=Path(path_text).expanduser(),
                head=head_text,
                branch=(
                    str(branch).removeprefix("refs/heads/") if isinstance(branch, str) else None
                ),
                detached=detached,
                locked=fields.get("locked") is not None,
                prunable=fields.get("prunable") is not None,
                bare=bare,
            )
        )
        fields = {}

    for field in output.split("\0"):
        if not field:
            finish()
            continue
        key, separator, value = field.partition(" ")
        if key in fields:
            raise unsafe_state("Git worktree metadata repeats a field.", field=key)
        fields[key] = value if separator else True
    finish()
    if not records:
        raise unsafe_state("Git returned no worktree registrations.")
    return records


def _transient_git_lock_count(common_dir: Path, git_directories: tuple[Path, ...]) -> int:
    roots = tuple(dict.fromkeys((common_dir, *git_directories)))
    count = 0
    visited = 0
    for root in roots:
        for directory_text, directory_names, file_names in os.walk(root, followlinks=False):
            directory = Path(directory_text)
            directory_names[:] = [
                name for name in directory_names if not (directory / name).is_symlink()
            ]
            visited += len(directory_names) + len(file_names)
            if visited > 100_000:
                raise unsafe_state("Git metadata exceeds the bounded lock inventory.")
            count += sum(name.endswith(".lock") for name in file_names)
    return count


def inspect_worktree_topology(repository: str | Path) -> dict[str, Any]:
    """Return content-free target, sibling, and common-Git preservation fingerprints.

    Sibling file bodies are never opened. Git status output is reduced immediately to
    counts and a digest; sibling paths and untracked names are represented only by hashes.
    """

    target = require_directory(repository)
    target_state = inspect_git(target)
    raw_registration = run_git(
        target,
        ["worktree", "list", "--porcelain", "-z"],
    )
    try:
        registrations = _parse_worktree_records(raw_registration)
    except RepoOSError:
        raise
    except Exception as exc:
        raise unsafe_state(
            "Git worktree metadata could not be parsed.",
            exception_type=type(exc).__name__,
        ) from exc

    summaries: list[dict[str, Any]] = []
    git_directories: list[Path] = []
    target_summary: dict[str, Any] | None = None
    seen_ids: set[str] = set()
    for registration in registrations:
        path_id = sha256_bytes(str(registration.path.resolve(strict=False)).encode("utf-8"))
        if registration.locked:
            raise unsafe_state(
                "A registered worktree is locked.",
                worktree_id=path_id,
                ambiguity="locked_worktree",
            )
        if registration.prunable:
            raise unsafe_state(
                "A registered worktree is prunable or missing.",
                worktree_id=path_id,
                ambiguity="prunable_worktree",
            )
        if registration.bare:
            raise unsafe_state(
                "Bare worktree registrations are unsupported.",
                worktree_id=path_id,
                ambiguity="bare_worktree",
            )
        try:
            path = canonical_path(registration.path, must_exist=True)
            state = inspect_git(path)
            git_dir = _resolve_git_dir(path)
        except RepoOSError as exc:
            raise unsafe_state(
                "A registered worktree is unreadable or malformed.",
                worktree_id=path_id,
                ambiguity=exc.error_type,
            ) from exc
        if state.root != path or state.common_dir != target_state.common_dir:
            raise unsafe_state(
                "A registered worktree has an ambiguous Git identity.",
                worktree_id=path_id,
                ambiguity="common_git_mismatch",
            )
        if state.head != registration.head or state.branch != registration.branch:
            raise unsafe_state(
                "A registered worktree changed during inspection.",
                worktree_id=path_id,
                ambiguity="registration_state_mismatch",
            )
        canonical_id = sha256_bytes(str(path).encode("utf-8"))
        if canonical_id in seen_ids:
            raise unsafe_state(
                "Git worktree metadata resolves to a duplicate path.",
                worktree_id=canonical_id,
                ambiguity="duplicate_worktree",
            )
        seen_ids.add(canonical_id)
        git_directories.append(git_dir)
        is_target = path == target
        summary = {
            "worktree_id": canonical_id,
            "classification": (
                ("target_clean" if state.clean else "target_dirty")
                if is_target
                else ("protected_clean" if state.clean else "protected_dirty")
            ),
            "head": state.head,
            "branch_sha256": sha256_bytes((state.branch or "detached").encode("utf-8")),
            "status_fingerprint": status_fingerprint(path),
            "tracked_changes": state.tracked_changes,
            "untracked_entries": state.untracked_entries,
            "clean": state.clean,
            "locked": False,
            "prunable": False,
            "git_dir_sha256": sha256_bytes(str(git_dir).encode("utf-8")),
            "head_metadata_sha256": _metadata_file_digest(git_dir / "HEAD"),
            "index_sha256": _metadata_file_digest(git_dir / "index"),
        }
        if is_target:
            target_summary = summary
        else:
            summaries.append(summary)

    if target_summary is None:
        raise unsafe_state(
            "The explicit target is not present in the common-Git worktree registry.",
            ambiguity="target_registration_missing",
        )

    common_dir = target_state.common_dir
    lock_count = _transient_git_lock_count(common_dir, tuple(git_directories))
    common_git = {
        "common_dir_sha256": sha256_bytes(str(common_dir).encode("utf-8")),
        "worktree_registration_sha256": sha256_bytes(raw_registration.encode("utf-8")),
        "refs_sha256": sha256_bytes(
            run_git(
                target,
                ["for-each-ref", "--format=%(refname)%00%(objectname)"],
            ).encode("utf-8")
        ),
        "config_sha256": _metadata_file_digest(common_dir / "config"),
        "head_sha256": _metadata_file_digest(common_dir / "HEAD"),
        "transient_lock_count": lock_count,
        "worktree_count": len(registrations),
        "worktree_summaries_sha256": _canonical_digest(
            sorted(
                (
                    {
                        "worktree_id": item["worktree_id"],
                        "git_dir_sha256": item["git_dir_sha256"],
                        "head_metadata_sha256": item["head_metadata_sha256"],
                        "index_sha256": item["index_sha256"],
                    }
                    for item in (target_summary, *summaries)
                ),
                key=lambda item: str(item["worktree_id"]),
            )
        ),
    }
    summaries.sort(key=lambda item: str(item["worktree_id"]))
    return {
        "target": target_summary,
        "siblings": summaries,
        "common_git": common_git,
    }
