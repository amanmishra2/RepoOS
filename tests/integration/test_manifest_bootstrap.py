from __future__ import annotations

import json
import shutil
import socket
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from conftest import git

from repoos import __version__
from repoos.apply import (
    execute_manifest_bootstrap,
    execute_plan,
    rollback_transaction,
)
from repoos.backup import validate_backup
from repoos.errors import ExitCode, RepoOSError
from repoos.git import inspect_git, inspect_worktree_topology
from repoos.locks import RepositoryLock, repository_lock_path
from repoos.manifest_bootstrap import (
    DESTINATION,
    build_manifest_bootstrap_plan,
    canonical_bootstrap_plan_digest,
    create_manifest_bootstrap_authorization,
    manifest_bootstrap_dry_run,
    manifest_bootstrap_precondition_failures,
    validate_bootstrap_manifest_bytes,
)
from repoos.planning import build_update_plan
from repoos.transactions import TransactionStore
from repoos.validation import validate_instance


def _create_real_repository(path: Path, *, validation_exit: int = 0) -> Path:
    path.mkdir()
    git(path, "init", "-b", "main")
    (path / "README.md").write_text("synthetic repository\n", encoding="utf-8")
    (path / "validate.py").write_text(
        f"raise SystemExit({validation_exit})\n",
        encoding="utf-8",
    )
    git(path, "add", "README.md", "validate.py")
    git(path, "commit", "-m", "Create synthetic repository")
    return path


def _manifest_input(
    path: Path,
    *,
    project_id: str = "synthetic-project",
    managed: list[str] | None = None,
) -> Path:
    path.write_text(
        "\n".join(
            [
                "manifest_version: 1",
                f"project_id: {project_id}",
                f"repoos_version: {__version__}",
                "project_family: synthetic-python",
                "sensitivity_classification: internal",
                "additional_overlays: []",
                "components:",
                f"  managed: {json.dumps(managed or [])}",
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
    return path


def _worktree_repository(
    tmp_path: Path,
    *,
    dirty_sibling: bool = False,
) -> tuple[Path, Path, Path]:
    main = _create_real_repository(tmp_path / "main")
    target = tmp_path / "target"
    sibling = tmp_path / "sibling"
    git(main, "worktree", "add", "-b", "bootstrap-target", str(target))
    git(main, "worktree", "add", "-b", "protected-sibling", str(sibling))
    if dirty_sibling:
        (sibling / "untracked-private-draft.txt").write_text(
            "synthetic body that must never be opened\n",
            encoding="utf-8",
        )
    return main, target, sibling


def _authorize(
    plan: dict[str, Any],
    state: Path,
    *,
    now: datetime | None = None,
    expires: int = 600,
) -> Path:
    path, _receipt = create_manifest_bootstrap_authorization(
        plan,
        state_directory=state,
        expires_in_seconds=expires,
        now=now,
    )
    return path


def _snapshot(repository: Path) -> dict[str, tuple[bytes, int]]:
    snapshot: dict[str, tuple[bytes, int]] = {}
    for path in sorted(repository.rglob("*")):
        relative = path.relative_to(repository)
        if ".git" in relative.parts:
            continue
        if path.is_file() and not path.is_symlink():
            snapshot[relative.as_posix()] = (
                path.read_bytes(),
                path.stat(follow_symlinks=False).st_mode & 0o7777,
            )
    return snapshot


def _resign_bootstrap_plan(plan: dict[str, Any]) -> dict[str, Any]:
    body = dict(plan)
    body.pop("plan_id", None)
    body.pop("plan_digest", None)
    digest = canonical_bootstrap_plan_digest(body)
    plan["plan_id"] = f"plan-{digest}"
    plan["plan_digest"] = digest
    return plan


def test_clean_single_worktree_manifest_bootstrap(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)

    result = execute_manifest_bootstrap(
        plan,
        repository,
        manifest,
        authorization,
        state_directory=state,
    )

    assert result["state"] == "completed"
    assert (repository / DESTINATION).read_bytes() == manifest.read_bytes()
    record = TransactionStore(state).load(result["transaction_id"])
    assert record["operation_kind"] == "manifest_bootstrap"
    assert record["authorization_sha256"]
    assert record["bootstrap_install"]["parent_created"] is True
    assert record["bootstrap_install"]["manifest_created"] is True
    assert isinstance(record["bootstrap_install"]["manifest_device"], int)
    assert isinstance(record["bootstrap_install"]["manifest_inode"], int)
    backup = validate_backup(Path(record["backup_location"]), transaction_record=record)
    assert backup["operation_kind"] == "manifest_bootstrap"
    assert backup["authorization_sha256"] == record["authorization_sha256"]
    assert backup["entries"] == [
        {
            "target": DESTINATION,
            "action": "create",
            "ownership": "adoption_manifest",
            "existed": False,
            "backup_path": None,
            "original_sha256": None,
            "original_mode": None,
            "expected_applied_sha256": plan["manifest"]["sha256"],
            "expected_applied_mode": 0o644,
            "managed_section": None,
        }
    ]
    assert inspect_git(repository).head == plan["base_commit"]


def test_clean_target_allows_dirty_protected_sibling(tmp_path: Path) -> None:
    _main, target, sibling = _worktree_repository(tmp_path, dirty_sibling=True)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    sibling_before = _snapshot(sibling)
    topology_before = inspect_worktree_topology(target)
    plan = build_manifest_bootstrap_plan(target, manifest)

    assert any(item["classification"] == "protected_dirty" for item in plan["sibling_worktrees"])
    result = execute_manifest_bootstrap(
        plan,
        target,
        manifest,
        _authorize(plan, state),
        state_directory=state,
    )
    assert result["state"] == "completed"
    assert _snapshot(sibling) == sibling_before
    topology_after = inspect_worktree_topology(target)
    assert topology_after["siblings"] == topology_before["siblings"]


def test_sibling_untracked_body_is_never_opened_or_persisted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _main, target, sibling = _worktree_repository(tmp_path, dirty_sibling=True)
    body = sibling / "untracked-private-draft.txt"
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path == body:
            raise AssertionError("sibling untracked body was opened")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    plan = build_manifest_bootstrap_plan(target, manifest)
    serialized = json.dumps(plan, sort_keys=True)
    assert body.name not in serialized
    assert "synthetic body that must never be opened" not in serialized


def test_existing_manifest_is_never_replaced(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    destination = repository / DESTINATION
    destination.parent.mkdir()
    destination.write_text("existing: true\n", encoding="utf-8")
    git(repository, "add", DESTINATION)
    git(repository, "commit", "-m", "Add existing manifest")
    before = destination.read_bytes()

    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(
            repository,
            _manifest_input(tmp_path / "manifest.yaml"),
        )
    assert caught.value.error_type == "existing_manifest"
    assert destination.read_bytes() == before


def test_existing_empty_repoos_directory_is_preserved(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    parent = repository / ".repoos"
    parent.mkdir(mode=0o750)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    assert plan["parent_directory"]["state"] == "existing_directory"

    result = execute_manifest_bootstrap(
        plan,
        repository,
        manifest,
        _authorize(plan, state),
        state_directory=state,
    )
    rollback_transaction(result["transaction_id"], state_directory=state)
    assert parent.is_dir()
    assert parent.stat().st_mode & 0o777 == 0o750
    assert list(parent.iterdir()) == []


def test_existing_repoos_directory_unrelated_content_is_preserved(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    parent = repository / ".repoos"
    parent.mkdir()
    unrelated = parent / "README.md"
    unrelated.write_bytes(b"repository-owned metadata\n")
    unrelated.chmod(0o640)
    git(repository, "add", ".repoos/README.md")
    git(repository, "commit", "-m", "Add repository-owned RepoOS metadata")
    before = _snapshot(repository)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)

    result = execute_manifest_bootstrap(
        plan,
        repository,
        manifest,
        _authorize(plan, state),
        state_directory=state,
    )
    rollback_transaction(result["transaction_id"], state_directory=state)
    assert _snapshot(repository) == before


def test_dirty_target_is_refused(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    (repository / "user-work.txt").write_text("preserve\n", encoding="utf-8")
    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(
            repository,
            _manifest_input(tmp_path / "manifest.yaml"),
        )
    assert caught.value.error_type == "dirty_target"
    assert caught.value.code is ExitCode.DIRTY_REPOSITORY


def test_changed_target_head_after_planning_is_stale(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    (repository / "later.txt").write_text("later\n", encoding="utf-8")
    git(repository, "add", "later.txt")
    git(repository, "commit", "-m", "Advance synthetic target")

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "stale_target"
    assert not (repository / DESTINATION).exists()


def test_changed_target_branch_after_planning_is_stale(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    git(repository, "switch", "-c", "other-synthetic-branch")

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "stale_target"


def test_changed_manifest_input_after_planning_is_stale(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    _manifest_input(manifest, project_id="different-synthetic-project")

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "stale_target"


def test_changed_plan_after_authorization_is_invalid_authorization(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    plan["validation_commands"][0]["name"] = "changed-tests"
    _resign_bootstrap_plan(plan)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "invalid_authorization"


def test_expired_authorization_is_refused(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    created = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)
    authorization = _authorize(plan, state, now=created, expires=60)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
            authorization_now=created + timedelta(seconds=61),
        )
    assert caught.value.error_type == "expired_authorization"
    assert not state.joinpath("transactions").exists()


def test_consumed_authorization_cannot_be_reused_after_rollback(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    result = execute_manifest_bootstrap(
        plan,
        repository,
        manifest,
        authorization,
        state_directory=state,
    )
    rollback_transaction(result["transaction_id"], state_directory=state)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "consumed_authorization"


def test_authorization_for_another_worktree_is_refused(tmp_path: Path) -> None:
    _main, first, second = _worktree_repository(tmp_path)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    first_plan = build_manifest_bootstrap_plan(first, manifest)
    authorization = _authorize(first_plan, state)
    second_plan = build_manifest_bootstrap_plan(second, manifest)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            second_plan,
            second,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "invalid_authorization"
    assert "target_repository" in caught.value.details["mismatched_fields"]


def test_authorization_for_another_head_is_refused(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    first_plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(first_plan, state)
    (repository / "later.txt").write_text("later\n", encoding="utf-8")
    git(repository, "add", "later.txt")
    git(repository, "commit", "-m", "Advance target")
    second_plan = build_manifest_bootstrap_plan(repository, manifest)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            second_plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "invalid_authorization"
    assert "target_head" in caught.value.details["mismatched_fields"]


def test_missing_authorization_is_refused_without_transaction_state(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            state / "authorizations" / "missing.json",
            state_directory=state,
        )
    assert caught.value.error_type == "missing_authorization"
    assert not state.exists()


def test_malformed_authorization_is_refused(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    authorization = state / "authorizations" / "malformed.json"
    authorization.parent.mkdir(parents=True)
    authorization.write_text("{not-json", encoding="utf-8")
    plan = build_manifest_bootstrap_plan(repository, manifest)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "invalid_authorization"
    assert caught.value.details["reason"] == "malformed"


def test_active_common_git_repoos_lock_refuses_apply(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    lock = RepositoryLock(
        state,
        str(inspect_git(repository).common_dir),
        target=str(repository),
        transaction_id="synthetic-active",
    )
    lock.acquire()
    try:
        with pytest.raises(RepoOSError) as caught:
            execute_manifest_bootstrap(
                plan,
                repository,
                manifest,
                authorization,
                state_directory=state,
            )
        assert caught.value.code is ExitCode.LOCKED
    finally:
        lock.release()
    assert not (repository / DESTINATION).exists()


def test_stale_repoos_lock_requires_explicit_recovery(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    lock_path = repository_lock_path(state, str(inspect_git(repository).common_dir))
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(
        json.dumps(
            {
                "pid": 999_999,
                "hostname": socket.gethostname(),
                "start_time": "2026-07-23T00:00:00Z",
                "target": str(repository),
                "transaction_id": "synthetic-stale",
                "kind": "repository",
                "owner_token": "dead-owner",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "stale_lock"

    result = execute_manifest_bootstrap(
        plan,
        repository,
        manifest,
        authorization,
        state_directory=state,
        recover_stale_lock=True,
    )
    assert result["state"] == "completed"
    assert list(lock_path.parent.glob(f"{lock_path.name}.recovered.*"))


def test_locked_sibling_worktree_is_ambiguous(tmp_path: Path) -> None:
    main, target, sibling = _worktree_repository(tmp_path)
    git(main, "worktree", "lock", str(sibling))
    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(
            target,
            _manifest_input(tmp_path / "manifest.yaml"),
        )
    assert caught.value.error_type == "sibling_ambiguity"
    assert caught.value.details["ambiguity"] == "locked_worktree"


def test_malformed_worktree_metadata_fails_conservatively(tmp_path: Path) -> None:
    _main, target, sibling = _worktree_repository(tmp_path)
    git_dir = Path(git(sibling, "rev-parse", "--git-dir").strip()).resolve()
    (git_dir / "gitdir").write_text(
        str(tmp_path / "missing-worktree" / ".git") + "\n",
        encoding="utf-8",
    )
    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(
            target,
            _manifest_input(tmp_path / "manifest.yaml"),
        )
    assert caught.value.error_type == "sibling_ambiguity"


def test_symlinked_manifest_destination_is_refused(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    outside = tmp_path / "outside.yaml"
    outside.write_text("outside\n", encoding="utf-8")
    (repository / ".repoos").mkdir()
    (repository / DESTINATION).symlink_to(outside)

    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(
            repository,
            _manifest_input(tmp_path / "manifest.yaml"),
        )
    assert caught.value.code is ExitCode.UNSAFE_STATE
    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_symlinked_parent_escape_is_refused(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    outside = tmp_path / "outside"
    outside.mkdir()
    (repository / ".repoos").symlink_to(outside, target_is_directory=True)

    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(
            repository,
            _manifest_input(tmp_path / "manifest.yaml"),
        )
    assert caught.value.code is ExitCode.UNSAFE_STATE
    assert list(outside.iterdir()) == []


def test_path_traversal_cannot_be_represented_by_bootstrap_plan(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    plan = build_manifest_bootstrap_plan(repository, manifest)
    plan["destination"] = "../project.yaml"
    plan["operations"][0]["target"] = "../project.yaml"
    _resign_bootstrap_plan(plan)

    findings = validate_instance(plan, "manifest-bootstrap-plan")
    assert findings
    failures = manifest_bootstrap_precondition_failures(
        plan,
        repository,
        manifest,
        state_directory=tmp_path / "state",
    )
    assert "plan_schema_invalid" in failures
    assert not (tmp_path / "project.yaml").exists()


def test_validation_failure_after_creation_is_classified(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository", validation_exit=7)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            _authorize(plan, state),
            state_directory=state,
        )
    assert caught.value.error_type == "validation_failed_rolled_back"
    record = TransactionStore(state).load(str(caught.value.details["transaction_id"]))
    assert record["failure"]["classification"] == "validation_failure"
    assert record["validation_results"][0]["exit_code"] == 7


def test_automatic_rollback_restores_prebootstrap_state(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository", validation_exit=1)
    before = _snapshot(repository)
    topology_before = inspect_worktree_topology(repository)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            _authorize(plan, state),
            state_directory=state,
        )
    record = TransactionStore(state).load(str(caught.value.details["transaction_id"]))
    assert record["state"] == "rolled_back"
    assert record["rollback"]["state"] == "succeeded"
    assert _snapshot(repository) == before
    assert inspect_worktree_topology(repository) == topology_before
    assert not (repository / ".repoos").exists()


def test_manual_rollback_restores_bytes_modes_and_metadata(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    before = _snapshot(repository)
    topology_before = inspect_worktree_topology(repository)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    result = execute_manifest_bootstrap(
        plan,
        repository,
        manifest,
        _authorize(plan, state),
        state_directory=state,
    )

    rollback = rollback_transaction(result["transaction_id"], state_directory=state)
    assert rollback["state"] == "rolled_back"
    assert _snapshot(repository) == before
    assert inspect_worktree_topology(repository) == topology_before


def test_manual_rollback_state_cannot_be_relocated_into_a_sibling(tmp_path: Path) -> None:
    _main, target, sibling = _worktree_repository(tmp_path)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(target, manifest)
    result = execute_manifest_bootstrap(
        plan,
        target,
        manifest,
        _authorize(plan, state),
        state_directory=state,
    )
    unsafe_state = sibling / "copied-repoos-state"
    shutil.copytree(state, unsafe_state)

    with pytest.raises(RepoOSError) as caught:
        rollback_transaction(
            result["transaction_id"],
            state_directory=unsafe_state,
        )
    assert caught.value.code is ExitCode.UNSAFE_STATE
    assert (target / DESTINATION).is_file()
    assert not list(unsafe_state.rglob("*.lock"))


def test_repeated_manual_rollback_is_idempotent(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    result = execute_manifest_bootstrap(
        plan,
        repository,
        manifest,
        _authorize(plan, state),
        state_directory=state,
    )
    first = rollback_transaction(result["transaction_id"], state_directory=state)
    second = rollback_transaction(result["transaction_id"], state_directory=state)
    assert first["already_rolled_back"] is False
    assert second["already_rolled_back"] is True
    assert not (repository / DESTINATION).exists()


def test_apply_interruption_can_be_manually_rolled_back(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)

    def interrupt(point: str) -> None:
        if point == f"apply_after_write:{DESTINATION}":
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
            fault=interrupt,
        )
    record = TransactionStore(state).list()[0]
    assert record["state"] == "applying"
    rollback_transaction(record["transaction_id"], state_directory=state)
    assert not (repository / ".repoos").exists()
    assert inspect_git(repository).clean


def test_rollback_interruption_can_resume_safely(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    result = execute_manifest_bootstrap(
        plan,
        repository,
        manifest,
        _authorize(plan, state),
        state_directory=state,
    )

    def interrupt(point: str) -> None:
        if point == f"rollback_after_restore:{DESTINATION}":
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        rollback_transaction(
            result["transaction_id"],
            state_directory=state,
            fault=interrupt,
        )
    assert TransactionStore(state).load(result["transaction_id"])["state"] == "rolling_back"
    resumed = rollback_transaction(result["transaction_id"], state_directory=state)
    assert resumed["state"] == "rolled_back"
    assert not (repository / ".repoos").exists()


def test_sibling_state_drift_fails_validation_and_preserves_evidence(tmp_path: Path) -> None:
    _main, target, sibling = _worktree_repository(tmp_path, dirty_sibling=True)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(target, manifest)

    def drift(point: str) -> None:
        if point == "validation_after:tests":
            (sibling / "new-external-drift.txt").write_text("external drift\n", encoding="utf-8")

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            target,
            manifest,
            _authorize(plan, state),
            state_directory=state,
            fault=drift,
        )
    assert caught.value.code is ExitCode.ROLLBACK_FAILURE
    record = TransactionStore(state).list()[0]
    assert record["state"] == "rollback_failed"
    assert not (target / DESTINATION).exists()
    assert (sibling / "new-external-drift.txt").read_text(encoding="utf-8") == "external drift\n"
    full_record = TransactionStore(state).load(str(record["transaction_id"]))
    assert Path(full_record["backup_location"]).is_dir()


def test_destination_appearing_after_planning_is_refused(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    destination = repository / DESTINATION
    destination.parent.mkdir()
    destination.write_text("appeared\n", encoding="utf-8")

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
        )
    assert caught.value.error_type == "existing_manifest"
    assert destination.read_text(encoding="utf-8") == "appeared\n"


def test_manifest_schema_failure_is_rejected_before_plan(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("manifest_version: 1\nunknown: true\n", encoding="utf-8")
    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(repository, manifest)
    assert caught.value.error_type == "invalid_manifest"
    assert not (repository / DESTINATION).exists()


def test_manifest_input_symlink_is_refused(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    linked = tmp_path / "linked-manifest.yaml"
    linked.symlink_to(manifest)

    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(repository, linked)
    assert caught.value.error_type == "invalid_manifest"
    assert not (repository / DESTINATION).exists()


def test_authorization_symlink_is_refused_before_transaction_state(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    linked = state / "linked-authorization.json"
    linked.symlink_to(authorization)

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            linked,
            state_directory=state,
        )
    assert caught.value.error_type == "invalid_authorization"
    assert not (state / "transactions").exists()
    assert not (repository / DESTINATION).exists()


def test_state_directory_inside_sibling_is_refused_without_writes(tmp_path: Path) -> None:
    _main, target, sibling = _worktree_repository(tmp_path)
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    plan = build_manifest_bootstrap_plan(target, manifest)
    unsafe_state = sibling / ".repoos-local-state"

    with pytest.raises(RepoOSError) as caught:
        create_manifest_bootstrap_authorization(
            plan,
            state_directory=unsafe_state,
            expires_in_seconds=600,
        )
    assert caught.value.code is ExitCode.UNSAFE_STATE
    assert not unsafe_state.exists()
    assert inspect_git(sibling).clean


def test_broken_fixture_marker_is_not_a_real_repository_authority(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    (repository / ".repoos-fixture").symlink_to(repository / "missing-marker-target")
    manifest = _manifest_input(tmp_path / "manifest.yaml")

    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(repository, manifest)
    assert caught.value.error_type == "real_repository_operation_refused"


def test_destination_race_before_transaction_write_is_preserved(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    destination = repository / DESTINATION

    def race(point: str) -> None:
        if point == f"apply_before_write:{DESTINATION}":
            destination.parent.mkdir()
            destination.write_text("external race\n", encoding="utf-8")

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
            fault=race,
        )
    assert caught.value.error_type == "stale_target"
    assert destination.read_text(encoding="utf-8") == "external race\n"
    record = TransactionStore(state).list()[0]
    assert record["state"] == "failed"


def test_destination_race_after_parent_creation_is_never_deleted(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    plan = build_manifest_bootstrap_plan(repository, manifest)
    authorization = _authorize(plan, state)
    destination = repository / DESTINATION

    def race(point: str) -> None:
        if point == "manifest_parent_created":
            destination.write_text("external after parent\n", encoding="utf-8")

    with pytest.raises(RepoOSError) as caught:
        execute_manifest_bootstrap(
            plan,
            repository,
            manifest,
            authorization,
            state_directory=state,
            fault=race,
        )
    assert caught.value.code is ExitCode.ROLLBACK_FAILURE
    assert destination.read_text(encoding="utf-8") == "external after parent\n"
    record = TransactionStore(state).list()[0]
    assert record["state"] == "rollback_failed"


def test_broad_managed_component_declaration_is_rejected(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(
        tmp_path / "manifest.yaml",
        managed=["repoos-workflows"],
    )
    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(repository, manifest)
    assert caught.value.error_type == "invalid_manifest"
    assert "bootstrap_managed_not_allowed" in caught.value.details["violations"]


def test_validation_option_cannot_escape_to_an_absolute_makefile(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "    argv: [python3, validate.py]",
            "    argv: [make, --file=/tmp/unreviewed.mk]",
        ),
        encoding="utf-8",
    )

    with pytest.raises(RepoOSError) as caught:
        build_manifest_bootstrap_plan(repository, manifest)
    assert caught.value.error_type == "invalid_manifest"
    assert "verification_option_not_allowed:0" in caught.value.details["violations"]


def test_next_p08_prompt_contains_the_exact_valid_minimal_manifest() -> None:
    prompt = (
        Path(__file__).resolve().parents[2]
        / "reports"
        / "manifest-bootstrap"
        / "2026-07-25"
        / "NEXT_P08_CANARY_PROMPT.md"
    ).read_text(encoding="utf-8")
    manifest_text = prompt.split("```yaml\n", 1)[1].split("```", 1)[0]
    manifest = validate_bootstrap_manifest_bytes(
        manifest_text.encode("utf-8"),
        source="NEXT_P08_CANARY_PROMPT.md",
    )

    assert manifest["project_id"] == "p08"
    assert manifest["components"] == {
        "managed": [],
        "generated": [],
        "repository_owned": [],
        "extensions": [],
        "excluded": [],
    }
    assert manifest["verification"] == [
        {"name": "agentops-check", "argv": ["make", "agentops-check"]},
        {"name": "product-check", "argv": ["make", "product-check"]},
    ]


def test_general_real_repository_update_remains_blocked(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    source = tmp_path / "source"
    source.mkdir()
    (source / "value.txt").write_text("managed\n", encoding="utf-8")
    with pytest.raises(RepoOSError) as caught:
        build_update_plan(
            repository,
            source,
            ["value.txt=managed/value.txt"],
            target_version=__version__,
        )
    assert caught.value.error_type == "authorization_required"


def test_fixture_update_behavior_remains_unchanged(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "value.txt").write_text("managed\n", encoding="utf-8")
    plan = build_update_plan(
        repoos_fixture,
        source,
        ["value.txt=managed/value.txt"],
        target_version=__version__,
    )
    result = execute_plan(
        plan,
        repoos_fixture,
        source,
        state_directory=tmp_path / "state",
    )
    assert result["state"] == "completed"
    assert (repoos_fixture / "managed" / "value.txt").read_text(encoding="utf-8") == "managed\n"


def test_same_common_git_operations_are_serialized(tmp_path: Path) -> None:
    main = _create_real_repository(tmp_path / "main")
    first = tmp_path / "first"
    second = tmp_path / "second"
    git(main, "worktree", "add", "-b", "first-target", str(first))
    git(main, "worktree", "add", "-b", "second-target", str(second))
    first_manifest = _manifest_input(
        tmp_path / "first-manifest.yaml",
        project_id="synthetic-first",
    )
    second_manifest = _manifest_input(
        tmp_path / "second-manifest.yaml",
        project_id="synthetic-second",
    )
    state = tmp_path / "state"
    first_plan = build_manifest_bootstrap_plan(first, first_manifest)
    second_plan = build_manifest_bootstrap_plan(second, second_manifest)
    first_authorization = _authorize(first_plan, state)
    second_authorization = _authorize(second_plan, state)
    first_holds_lock = threading.Event()
    release_first = threading.Event()
    outcomes: list[object] = []

    def block(point: str) -> None:
        if point == f"apply_before_write:{DESTINATION}":
            first_holds_lock.set()
            assert release_first.wait(timeout=10)

    def run_first() -> None:
        try:
            outcomes.append(
                execute_manifest_bootstrap(
                    first_plan,
                    first,
                    first_manifest,
                    first_authorization,
                    state_directory=state,
                    fault=block,
                )
            )
        except Exception as exc:
            outcomes.append(exc)

    thread = threading.Thread(target=run_first)
    thread.start()
    assert first_holds_lock.wait(timeout=10)
    try:
        with pytest.raises(RepoOSError) as caught:
            execute_manifest_bootstrap(
                second_plan,
                second,
                second_manifest,
                second_authorization,
                state_directory=state,
            )
        assert caught.value.code is ExitCode.LOCKED
    finally:
        release_first.set()
        thread.join(timeout=15)
    assert not thread.is_alive()
    assert len(outcomes) == 1
    assert isinstance(outcomes[0], dict)
    assert not (second / DESTINATION).exists()


def test_unrelated_repository_bootstraps_can_run_concurrently(tmp_path: Path) -> None:
    first = _create_real_repository(tmp_path / "first")
    second = _create_real_repository(tmp_path / "second")
    first_manifest = _manifest_input(
        tmp_path / "first-manifest.yaml",
        project_id="synthetic-first",
    )
    second_manifest = _manifest_input(
        tmp_path / "second-manifest.yaml",
        project_id="synthetic-second",
    )
    state = tmp_path / "state"
    first_plan = build_manifest_bootstrap_plan(first, first_manifest)
    second_plan = build_manifest_bootstrap_plan(second, second_manifest)
    first_authorization = _authorize(first_plan, state)
    second_authorization = _authorize(second_plan, state)
    barrier = threading.Barrier(2)
    outcomes: list[object] = []

    def wait_at_write(point: str) -> None:
        if point == f"apply_before_write:{DESTINATION}":
            barrier.wait(timeout=10)

    def run(
        plan: dict[str, Any],
        repository: Path,
        manifest: Path,
        authorization: Path,
    ) -> None:
        try:
            outcomes.append(
                execute_manifest_bootstrap(
                    plan,
                    repository,
                    manifest,
                    authorization,
                    state_directory=state,
                    fault=wait_at_write,
                )
            )
        except Exception as exc:
            outcomes.append(exc)

    threads = [
        threading.Thread(
            target=run,
            args=(first_plan, first, first_manifest, first_authorization),
        ),
        threading.Thread(
            target=run,
            args=(second_plan, second, second_manifest, second_authorization),
        ),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    assert all(not thread.is_alive() for thread in threads)
    assert len(outcomes) == 2
    assert all(isinstance(item, dict) for item in outcomes)
    assert (first / DESTINATION).is_file()
    assert (second / DESTINATION).is_file()


def test_dry_run_writes_no_target_or_transaction_state(tmp_path: Path) -> None:
    repository = _create_real_repository(tmp_path / "repository")
    manifest = _manifest_input(tmp_path / "manifest.yaml")
    state = tmp_path / "state"
    before = _snapshot(repository)
    plan = build_manifest_bootstrap_plan(repository, manifest)
    result = manifest_bootstrap_dry_run(
        plan,
        repository,
        manifest,
        state_directory=state,
    )
    assert result["ready_for_authorization"] is True
    assert result["authorization_status"] == "missing"
    assert result["writes_performed"] == 0
    assert result["state_writes_performed"] == 0
    assert _snapshot(repository) == before
    assert not state.exists()
