"""RepoOS command-line interface."""

from __future__ import annotations

import argparse
import difflib
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from repoos import __version__
from repoos.apply import (
    execute_manifest_bootstrap,
    execute_plan,
    precondition_error,
    rollback_transaction,
)
from repoos.discovery import discover, inventory_project
from repoos.errors import (
    ExitCode,
    RepoOSError,
    environment_error,
    invalid_input,
    unsafe_state,
    validation_error,
)
from repoos.git import inspect_git, is_git_worktree
from repoos.manifest_bootstrap import (
    PLAN_VERSION as MANIFEST_BOOTSTRAP_PLAN_VERSION,
)
from repoos.manifest_bootstrap import (
    assert_bootstrap_artifact_isolated,
    build_manifest_bootstrap_plan,
    create_manifest_bootstrap_authorization,
    manifest_bootstrap_dry_run,
    manifest_bootstrap_precondition_error,
    read_manifest_bootstrap_plan,
)
from repoos.paths import require_directory, state_root
from repoos.pause import get_pause_status
from repoos.planning import (
    DEFAULT_ALLOWED_PATH_PREFIXES,
    DEFAULT_FORBIDDEN_PATH_PATTERNS,
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_FILES,
    SafetyLimits,
    apply_dry_run,
    build_update_plan,
    read_plan,
    write_plan,
)
from repoos.redaction import redact_text
from repoos.reporting import render
from repoos.transactions import TransactionStore
from repoos.validation import (
    available_schemas,
    load_document,
    load_schema,
    repo_root,
    validate_all,
    validate_document,
)

Handler = Callable[[argparse.Namespace], dict[str, Any]]


def _default_root() -> str:
    return str(Path.home() / "Coding")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repoos",
        description=(
            "Inspect, validate, plan, and transactionally update marked fixture repositories. "
            "One explicitly authorized real-repository manifest bootstrap is also supported. "
            "Read-only and dry-run behavior remain the default; no command pushes or commits."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--root", default=_default_root(), help="Configured portfolio root.")
    parser.add_argument("--state-dir", help="Override the local RepoOS state directory.")
    parser.add_argument(
        "--format",
        choices=("human", "json"),
        default="human",
        help="Output format.",
    )
    parser.add_argument(
        "--privacy",
        choices=("public", "local"),
        default="public",
        help="Public mode aliases private project paths and identities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser(
        "discover",
        help="Discover direct child projects without modifying the registry.",
    )
    discover_parser.set_defaults(handler=_handle_discover)

    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Inventory one explicit project or the configured root read-only.",
    )
    inventory_parser.add_argument("--project", help="Explicit project directory.")
    inventory_parser.set_defaults(handler=_handle_inventory)

    status_parser = subparsers.add_parser("status", help="Show project Git and pause state.")
    status_parser.add_argument("--project", default=".", help="Explicit project directory.")
    status_parser.set_defaults(handler=_handle_status)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check the local runtime and RepoOS contracts without writing.",
    )
    doctor_parser.set_defaults(handler=_handle_doctor)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate one document or all RepoOS operating surfaces.",
    )
    validate_parser.add_argument("document", nargs="?", help="JSON/YAML document to validate.")
    validate_parser.add_argument("--schema", choices=available_schemas())
    validate_parser.add_argument("--all", action="store_true", help="Validate RepoOS itself.")
    validate_parser.set_defaults(handler=_handle_validate)

    diff_parser = subparsers.add_parser("diff", help="Compare two explicit text files read-only.")
    diff_parser.add_argument("--installed", required=True, help="Installed/local file.")
    diff_parser.add_argument("--target", required=True, help="Proposed file.")
    diff_parser.set_defaults(handler=_handle_diff)

    audit_parser = subparsers.add_parser("audit", help="Run deterministic RepoOS audits.")
    audit_parser.add_argument("--all", action="store_true", help="Audit every implemented surface.")
    audit_parser.set_defaults(handler=_handle_audit)

    check_parser = subparsers.add_parser(
        "check-update",
        help="Compare a repository manifest version with this RepoOS version.",
    )
    check_parser.add_argument("--project", default=".", help="Explicit project directory.")
    check_parser.set_defaults(handler=_handle_check_update)

    plan_parser = subparsers.add_parser(
        "plan-update",
        help="Create a deterministic no-write update plan for a marked fixture.",
    )
    plan_parser.add_argument(
        "--repository",
        "--repo",
        dest="repository",
        required=True,
        help="Explicit target fixture repository.",
    )
    plan_parser.add_argument("--source-root", required=True, help="Explicit component source root.")
    plan_parser.add_argument(
        "--file",
        action="append",
        default=[],
        metavar="SOURCE=TARGET",
        help="Fully managed [COMPONENT|]SOURCE=TARGET mapping; repeat as needed.",
    )
    plan_parser.add_argument(
        "--generated",
        action="append",
        default=[],
        metavar="SOURCE=TARGET",
        help="Generated [COMPONENT|]SOURCE=TARGET mapping; repeat as needed.",
    )
    plan_parser.add_argument(
        "--section",
        action="append",
        default=[],
        metavar="SOURCE=TARGET::START::END",
        help="UTF-8 managed-section mapping with exact single-line markers.",
    )
    plan_parser.add_argument(
        "--preserve",
        action="append",
        default=[],
        metavar="TARGET=OWNERSHIP",
        help="Record repository-owned, extension, local-override, or excluded ownership.",
    )
    plan_parser.add_argument("--target-version", default=__version__)
    plan_parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    plan_parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    plan_parser.add_argument("--max-created", type=int, default=5)
    plan_parser.add_argument("--max-deleted", type=int, default=0)
    plan_parser.add_argument("--max-lines-added", type=int, default=2000)
    plan_parser.add_argument("--max-lines-removed", type=int, default=2000)
    plan_parser.add_argument("--max-percent", type=float, default=50.0)
    plan_parser.add_argument("--max-sections", type=int, default=5)
    plan_parser.add_argument(
        "--allowed-prefix",
        action="append",
        help="Replace the default allowed target prefixes; repeat as needed.",
    )
    plan_parser.add_argument(
        "--forbidden-pattern",
        action="append",
        help="Replace the default forbidden path patterns; repeat as needed.",
    )
    plan_parser.add_argument("--output", help="Atomically write the plan JSON to this path.")
    plan_parser.set_defaults(handler=_handle_plan_update)

    bootstrap_plan_parser = subparsers.add_parser(
        "plan-manifest-bootstrap",
        help="Plan creation of one absent real-repository .repoos/project.yaml.",
    )
    bootstrap_plan_parser.add_argument(
        "--repository",
        "--repo",
        dest="repository",
        required=True,
        help="Explicit clean target worktree.",
    )
    bootstrap_plan_parser.add_argument(
        "--manifest-input",
        required=True,
        help="Exact reviewed project-manifest YAML outside every registered worktree.",
    )
    bootstrap_plan_parser.add_argument(
        "--output",
        required=True,
        help="Plan JSON output outside every worktree and common Git directory.",
    )
    bootstrap_plan_parser.set_defaults(handler=_handle_plan_manifest_bootstrap)

    authorize_parser = subparsers.add_parser(
        "authorize-manifest-bootstrap",
        help="Create one expiring local authorization bound to an exact bootstrap plan.",
    )
    authorize_parser.add_argument("--plan", required=True, help="Reviewed bootstrap-plan JSON.")
    authorize_parser.add_argument(
        "--expires-in",
        type=int,
        default=1800,
        metavar="SECONDS",
        help="Authorization lifetime in seconds (60-86400).",
    )
    authorize_parser.add_argument(
        "--approve",
        action="store_true",
        help="Explicitly approve this exact one-transaction bootstrap binding.",
    )
    authorize_parser.set_defaults(handler=_handle_authorize_manifest_bootstrap)

    apply_parser = subparsers.add_parser(
        "apply",
        help="Dry-run or execute one fixture-update or guarded manifest-bootstrap plan.",
    )
    apply_parser.add_argument("--plan", required=True, help="Explicit immutable plan JSON.")
    apply_parser.add_argument(
        "--repository",
        "--repo",
        dest="repository",
        help="Exact target worktree; defaults to the path bound into the plan.",
    )
    apply_parser.add_argument(
        "--source-root",
        help="Exact component source root; defaults to the path bound into the plan.",
    )
    apply_parser.add_argument(
        "--authorization",
        help="Exact local authorization receipt required by manifest bootstrap execute.",
    )
    mode = apply_parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview only (the default).")
    mode.add_argument("--execute", action="store_true", help="Execute the bounded transaction.")
    apply_parser.add_argument(
        "--override-limit",
        action="append",
        default=[],
        help="Explicitly override one exceeded named safety limit; repeat as needed.",
    )
    apply_parser.add_argument(
        "--recover-stale-lock",
        action="store_true",
        help="Explicitly preserve and recover a stale or malformed lock before execution.",
    )
    apply_parser.add_argument(
        "--validation-timeout",
        type=int,
        default=60,
        help="Per-command validation timeout in seconds.",
    )
    apply_parser.set_defaults(handler=_handle_apply)

    rollback_parser = subparsers.add_parser(
        "rollback",
        help="Restore only the paths owned by one supported transaction.",
    )
    rollback_parser.add_argument("--transaction", required=True, help="Exact transaction ID.")
    rollback_parser.add_argument(
        "--recover-stale-lock",
        action="store_true",
        help="Explicitly preserve and recover a stale or malformed repository lock.",
    )
    rollback_parser.set_defaults(handler=_handle_rollback)

    transaction_parser = subparsers.add_parser(
        "transaction",
        help="Inspect local transaction records.",
    )
    transaction_commands = transaction_parser.add_subparsers(
        dest="transaction_command",
        required=True,
    )
    transaction_show = transaction_commands.add_parser("show", help="Show one transaction.")
    transaction_show.add_argument("transaction_id")
    transaction_show.set_defaults(handler=_handle_transaction_show)
    transaction_list = transaction_commands.add_parser("list", help="List transactions.")
    transaction_list.set_defaults(handler=_handle_transaction_list)

    report_parser = subparsers.add_parser(
        "report",
        help="Load and normalize an explicit JSON or YAML report.",
    )
    report_parser.add_argument("--input", required=True, help="Explicit report document.")
    report_parser.set_defaults(handler=_handle_report)

    return parser


def _handle_discover(args: argparse.Namespace) -> dict[str, Any]:
    return discover(args.root, privacy=args.privacy)


def _handle_inventory(args: argparse.Namespace) -> dict[str, Any]:
    if args.project:
        return inventory_project(args.project, privacy=args.privacy)
    return discover(args.root, privacy=args.privacy)


def _handle_status(args: argparse.Namespace) -> dict[str, Any]:
    project = require_directory(args.project)
    state_directory = state_root(args.state_dir)
    result: dict[str, Any] = {
        "schema_version": "repoos.status.v1",
        "project": project.name if args.privacy == "local" else "P01",
        "path": str(project) if args.privacy == "local" else "<redacted-private-path>",
        "pause": get_pause_status(state_directory).as_dict(),
        "git_kind": "non_git",
        "read_only": True,
    }
    if is_git_worktree(project):
        git_state = inspect_git(project)
        result["git_kind"] = "linked_worktree" if (project / ".git").is_file() else "repository"
        result["git"] = git_state.as_dict(include_paths=args.privacy == "local")
        if args.privacy == "public" and isinstance(result["git"], dict):
            result["git"]["head"] = "<redacted>"
            result["git"]["branch"] = "<redacted>"
            result["git"]["upstream"] = "<redacted>" if git_state.upstream else None
    return result


def _handle_doctor(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).expanduser()
    python_ok = sys.version_info >= (3, 11)
    git_ok = shutil.which("git") is not None
    root_ok = root.is_dir()
    schema_results: dict[str, str] = {}
    for schema_name in available_schemas():
        try:
            load_schema(schema_name)
        except RepoOSError as exc:
            schema_results[schema_name] = f"error:{exc.error_type}"
        else:
            schema_results[schema_name] = "ok"
    checks = {
        "python": {
            "ok": python_ok,
            "version": ".".join(str(item) for item in sys.version_info[:3]),
        },
        "git": {"ok": git_ok},
        "configured_root": {"ok": root_ok, "path": str(root)},
        "schemas": schema_results,
        "state_directory": {
            "path": str(state_root(args.state_dir)),
            "created": False,
        },
    }
    ok = python_ok and git_ok and root_ok
    ok = ok and all(value == "ok" for value in schema_results.values())
    if not ok:
        raise environment_error("RepoOS doctor found environment failures.", checks=checks)
    return {"schema_version": "repoos.doctor.v1", "ok": ok, "read_only": True, "checks": checks}


def _handle_validate(args: argparse.Namespace) -> dict[str, Any]:
    if args.all:
        findings = validate_all(repo_root())
        if findings:
            raise validation_error(
                "RepoOS validation found errors.",
                findings=[finding.as_dict() for finding in findings],
            )
        return {
            "schema_version": "repoos.validation-result.v1",
            "ok": True,
            "scope": "all",
            "findings": [],
        }
    if not args.document or not args.schema:
        raise invalid_input("validate requires DOCUMENT and --schema, or --all.")
    findings = validate_document(args.document, args.schema)
    if findings:
        raise validation_error(
            "Document failed validation.",
            findings=[finding.as_dict() for finding in findings],
        )
    return {
        "schema_version": "repoos.validation-result.v1",
        "ok": True,
        "scope": args.document,
        "schema": args.schema,
        "findings": [],
    }


def _read_text(path: str) -> tuple[Path, str]:
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file() or file_path.is_symlink():
        raise invalid_input("Expected a regular non-symlink text file.", path=str(file_path))
    try:
        return file_path, file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise invalid_input(
            "Text file could not be read.", path=str(file_path), reason=str(exc)
        ) from exc


def _handle_diff(args: argparse.Namespace) -> dict[str, Any]:
    installed_path, installed = _read_text(args.installed)
    target_path, target = _read_text(args.target)
    lines = list(
        difflib.unified_diff(
            installed.splitlines(),
            target.splitlines(),
            fromfile=installed_path.name,
            tofile=target_path.name,
            lineterm="",
        )
    )
    return {
        "schema_version": "repoos.diff.v1",
        "changed": bool(lines),
        "diff": [redact_text(line) for line in lines],
        "read_only": True,
    }


def _handle_audit(args: argparse.Namespace) -> dict[str, Any]:
    findings = validate_all(repo_root())
    if findings:
        raise validation_error(
            "RepoOS audit found errors.",
            findings=[finding.as_dict() for finding in findings],
        )
    return {
        "schema_version": "repoos.audit.v1",
        "ok": True,
        "scope": "all" if args.all else "implemented",
        "findings": [],
        "read_only": True,
    }


def _version_tuple(value: str) -> tuple[int, int, int]:
    core = value.split("-", 1)[0]
    fields = core.split(".")
    if len(fields) != 3 or any(not field.isdigit() for field in fields):
        raise invalid_input("Version is not supported SemVer.", version=value)
    return (int(fields[0]), int(fields[1]), int(fields[2]))


def _handle_check_update(args: argparse.Namespace) -> dict[str, Any]:
    project = require_directory(args.project)
    manifest_path = project / ".repoos" / "project.yaml"
    value = load_document(manifest_path)
    if not isinstance(value, dict) or not isinstance(value.get("repoos_version"), str):
        raise invalid_input("Manifest has no repoos_version.", path=str(manifest_path))
    installed = value["repoos_version"]
    return {
        "schema_version": "repoos.update-check.v1",
        "project_id": value.get("project_id"),
        "installed_version": installed,
        "available_version": __version__,
        "update_available": _version_tuple(installed) < _version_tuple(__version__),
        "read_only": True,
    }


def _handle_plan_update(args: argparse.Namespace) -> dict[str, Any]:
    limits = SafetyLimits(
        max_files_changed=args.max_files,
        max_files_created=args.max_created,
        max_files_deleted=args.max_deleted,
        max_total_bytes_changed=args.max_bytes,
        max_lines_added=args.max_lines_added,
        max_lines_removed=args.max_lines_removed,
        max_percentage_repository_files_touched=args.max_percent,
        allowed_path_prefixes=tuple(args.allowed_prefix or DEFAULT_ALLOWED_PATH_PREFIXES),
        forbidden_path_patterns=tuple(args.forbidden_pattern or DEFAULT_FORBIDDEN_PATH_PATTERNS),
        max_managed_sections_changed=args.max_sections,
    )
    plan = build_update_plan(
        args.repository,
        args.source_root,
        args.file,
        target_version=args.target_version,
        generated_mappings=args.generated,
        section_mappings=args.section,
        preserve_specs=args.preserve,
        safety_limits=limits,
    )
    if args.output:
        output = Path(args.output).expanduser().resolve()
        repository = require_directory(args.repository)
        if output.is_relative_to(repository):
            raise unsafe_state(
                "Plan output must be outside the target repository.",
                output=str(output),
            )
        written = write_plan(args.output, plan)
        return {
            "schema_version": "repoos.plan-write.v1",
            "plan_id": plan["plan_id"],
            "output": str(written),
            "operation_count": len(plan["operations"]),
            "conflicts": plan["conflicts"],
            "target_repository_modified": False,
        }
    return plan


def _handle_plan_manifest_bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    plan = build_manifest_bootstrap_plan(args.repository, args.manifest_input)
    output = Path(args.output).expanduser().resolve()
    repository = require_directory(args.repository)
    common_dir = inspect_git(repository).common_dir
    manifest_input = Path(args.manifest_input).expanduser().resolve()
    assert_bootstrap_artifact_isolated(
        repository,
        output,
        common_dir,
        artifact_kind="Bootstrap plan output",
    )
    if output == manifest_input:
        raise unsafe_state(
            "Bootstrap plan output must not replace the manifest input.",
            output=str(output),
        )
    written = write_plan(output, plan)
    return {
        "schema_version": "repoos.manifest-bootstrap-plan-write.v1",
        "operation_kind": "manifest_bootstrap",
        "plan_id": plan["plan_id"],
        "plan_digest": plan["plan_digest"],
        "manifest_sha256": plan["manifest"]["sha256"],
        "destination": plan["destination"],
        "output": str(written),
        "protected_sibling_count": len(plan["sibling_worktrees"]),
        "protected_dirty_sibling_count": sum(
            item["classification"] == "protected_dirty" for item in plan["sibling_worktrees"]
        ),
        "target_repository_modified": False,
    }


def _handle_authorize_manifest_bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    if not args.approve:
        raise RepoOSError(
            "Exact manifest-bootstrap approval requires --approve.",
            ExitCode.AUTHORIZATION_REQUIRED,
            "authorization_required",
            {},
        )
    plan = read_manifest_bootstrap_plan(args.plan)
    path, authorization = create_manifest_bootstrap_authorization(
        plan,
        state_directory=state_root(args.state_dir),
        expires_in_seconds=args.expires_in,
    )
    return {
        "schema_version": "repoos.manifest-bootstrap-authorization-result.v1",
        "operation_kind": "manifest_bootstrap",
        "authorization_id": authorization["authorization_id"],
        "authorization": str(path),
        "state": authorization["state"],
        "expires_at": authorization["expires_at"],
        "plan_id": authorization["plan_id"],
        "plan_digest": authorization["plan_digest"],
        "manifest_sha256": authorization["manifest_sha256"],
        "destination": authorization["destination"],
        "credentials_stored": False,
    }


def _handle_apply(args: argparse.Namespace) -> dict[str, Any]:
    unvalidated = load_document(args.plan)
    if (
        isinstance(unvalidated, dict)
        and unvalidated.get("plan_version") == MANIFEST_BOOTSTRAP_PLAN_VERSION
    ):
        plan = read_manifest_bootstrap_plan(args.plan, verify_digest=False)
        repository = args.repository or plan["target_repository"]
        if args.source_root:
            raise invalid_input(
                "--source-root is fixture-only; bootstrap binds --manifest-input in its plan."
            )
        if args.override_limit:
            raise invalid_input("Manifest-bootstrap safety limits cannot be overridden.")
        manifest_input = plan["manifest_input"]
        if args.execute:
            if args.validation_timeout < 1:
                raise invalid_input("Validation timeout must be positive.")
            if not args.authorization:
                raise RepoOSError(
                    "Manifest-bootstrap execute requires an authorization receipt.",
                    ExitCode.AUTHORIZATION_REQUIRED,
                    "missing_authorization",
                    {},
                )
            return execute_manifest_bootstrap(
                plan,
                repository,
                manifest_input,
                args.authorization,
                state_directory=state_root(args.state_dir),
                recover_stale_lock=args.recover_stale_lock,
                validation_timeout=args.validation_timeout,
            )
        result = manifest_bootstrap_dry_run(
            plan,
            repository,
            manifest_input,
            state_directory=state_root(args.state_dir),
            authorization_path=args.authorization,
        )
        if result["failures"]:
            raise manifest_bootstrap_precondition_error("dry-run", result["failures"])
        return result

    plan = read_plan(args.plan, verify_digest=False)
    if args.authorization:
        raise invalid_input("--authorization applies only to manifest-bootstrap plans.")
    repository = args.repository or plan["target_repository"]
    source_root = args.source_root or plan["source_root"]
    overrides = tuple(sorted(set(args.override_limit)))
    if args.execute:
        if args.validation_timeout < 1:
            raise invalid_input("Validation timeout must be positive.")
        return execute_plan(
            plan,
            repository,
            source_root,
            state_directory=state_root(args.state_dir),
            safety_overrides=overrides,
            recover_stale_lock=args.recover_stale_lock,
            validation_timeout=args.validation_timeout,
        )
    result = apply_dry_run(
        plan,
        repository,
        source_root,
        state_directory=state_root(args.state_dir),
        safety_overrides=overrides,
    )
    if not result["would_apply"]:
        raise precondition_error("dry-run", result["failures"])
    return result


def _handle_rollback(args: argparse.Namespace) -> dict[str, Any]:
    return rollback_transaction(
        args.transaction,
        state_directory=state_root(args.state_dir),
        recover_stale_lock=args.recover_stale_lock,
    )


def _handle_transaction_show(args: argparse.Namespace) -> dict[str, Any]:
    record = TransactionStore(state_root(args.state_dir)).load(args.transaction_id)
    return {
        "schema_version": "repoos.transaction-show.v1",
        "transaction": record,
    }


def _handle_transaction_list(args: argparse.Namespace) -> dict[str, Any]:
    records = TransactionStore(state_root(args.state_dir)).list()
    return {
        "schema_version": "repoos.transaction-list.v1",
        "count": len(records),
        "transactions": records,
    }


def _handle_report(args: argparse.Namespace) -> dict[str, Any]:
    value = load_document(args.input)
    return {
        "schema_version": "repoos.report-envelope.v1",
        "source": Path(args.input).name,
        "document": value,
        "read_only": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Handler = args.handler
    try:
        result = handler(args)
    except RepoOSError as exc:
        sys.stderr.write(render(exc.as_dict(), args.format))
        return int(exc.code)
    except Exception as exc:  # fail closed and avoid raw traceback/secrets in default output
        error = RepoOSError(
            "Unexpected internal error.",
            ExitCode.INTERNAL_ERROR,
            "internal_error",
            {"exception_type": type(exc).__name__},
        )
        sys.stderr.write(render(error.as_dict(), args.format))
        return int(error.code)
    sys.stdout.write(render(result, args.format))
    return int(ExitCode.OK)
