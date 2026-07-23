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
from repoos.discovery import discover, inventory_project
from repoos.errors import (
    ExitCode,
    RepoOSError,
    authorization_required,
    environment_error,
    invalid_input,
    unsafe_state,
    validation_error,
)
from repoos.git import inspect_git, is_git_worktree
from repoos.paths import require_directory, state_root
from repoos.pause import get_pause_status
from repoos.planning import (
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_FILES,
    apply_dry_run,
    build_update_plan,
    read_plan,
    write_plan,
)
from repoos.redaction import redact_text
from repoos.reporting import render
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
            "Inspect, validate, and plan repository operating-layer changes. "
            "Read-only commands are the default; no command pushes or commits."
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
    plan_parser.add_argument("--repository", required=True, help="Explicit target repository.")
    plan_parser.add_argument("--source-root", required=True, help="Explicit component source root.")
    plan_parser.add_argument(
        "--file",
        action="append",
        default=[],
        metavar="SOURCE=TARGET",
        help="Fixture-only source/target mapping; repeat for multiple files.",
    )
    plan_parser.add_argument("--target-version", default=__version__)
    plan_parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    plan_parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    plan_parser.add_argument("--output", help="Atomically write the plan JSON to this path.")
    plan_parser.set_defaults(handler=_handle_plan_update)

    apply_parser = subparsers.add_parser(
        "apply",
        help="Revalidate and preview an explicit plan; execution is not enabled in v0.1.0.",
    )
    apply_parser.add_argument("--plan", required=True, help="Explicit update-plan JSON.")
    apply_parser.add_argument("--repository", required=True, help="Explicit target repository.")
    apply_parser.add_argument(
        "--source-root", required=True, help="Explicit component source root."
    )
    mode = apply_parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview only (the default).")
    mode.add_argument(
        "--execute", action="store_true", help="Request execution (currently refused)."
    )
    apply_parser.set_defaults(handler=_handle_apply)

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
    plan = build_update_plan(
        args.repository,
        args.source_root,
        args.file,
        target_version=args.target_version,
        max_files=args.max_files,
        max_bytes=args.max_bytes,
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


def _handle_apply(args: argparse.Namespace) -> dict[str, Any]:
    if args.execute:
        raise authorization_required(
            "Apply execution is intentionally disabled in RepoOS v0.1.0. "
            "Only dry-run revalidation is implemented.",
        )
    plan = read_plan(args.plan)
    result = apply_dry_run(
        plan,
        args.repository,
        args.source_root,
        state_directory=state_root(args.state_dir),
    )
    if not result["would_apply"]:
        raise unsafe_state("Apply preview failed safety revalidation.", preview=result)
    return result


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
