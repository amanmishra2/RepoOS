"""Deterministic schema and operating-surface validation."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from repoos.errors import invalid_input, validation_error
from repoos.paths import require_directory

_SCHEMAS = {
    "project-registry": "project-registry.schema.json",
    "project-manifest": "project-manifest.schema.json",
    "observation": "observation.schema.json",
    "candidate-pattern": "candidate-pattern.schema.json",
    "adoption-record": "adoption-record.schema.json",
    "update-plan": "update-plan.schema.json",
    "transaction": "transaction.schema.json",
    "backup-manifest": "backup-manifest.schema.json",
    "transaction-observation": "transaction-observation.schema.json",
}
_HOOK_EVENTS = {
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "Stop",
    "SubagentStop",
    "SessionEnd",
}
_ACTION_SHA = re.compile(r"^[^@\s]+@[0-9a-fA-F]{40}$")
_SKILL_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    path: str
    message: str
    severity: str = "error"

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "message": self.message, "severity": self.severity}


def repo_root() -> Path:
    candidates = (Path.cwd(), Path(__file__).resolve().parents[2])
    for candidate in candidates:
        if (
            (candidate / "VERSION").is_file()
            and (candidate / "schemas").is_dir()
            and (candidate / "registry").is_dir()
        ):
            return candidate.resolve()
    return Path.cwd().resolve()


def schema_directory(override: str | Path | None = None) -> Path:
    if override is not None:
        return require_directory(override)
    candidates = (
        repo_root() / "schemas",
        Path.cwd() / "schemas",
        Path(sys.prefix) / "share" / "repoos" / "schemas",
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    raise validation_error("RepoOS schema directory was not found.")


def load_document(path: str | Path) -> Any:
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise invalid_input("Document does not exist.", path=str(file_path))
    try:
        text = file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() == ".json":
            return json.loads(text)
        if file_path.suffix.lower() == ".toml":
            return tomllib.loads(text)
        if file_path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(text)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
        yaml.YAMLError,
    ) as exc:
        raise validation_error(
            "Document could not be parsed.", path=str(file_path), reason=str(exc)
        ) from exc
    raise invalid_input("Unsupported document format.", path=str(file_path))


def load_schema(name: str, *, directory: str | Path | None = None) -> dict[str, Any]:
    if name not in _SCHEMAS:
        raise invalid_input("Unknown schema name.", schema=name, available=sorted(_SCHEMAS))
    path = schema_directory(directory) / _SCHEMAS[name]
    value = load_document(path)
    if not isinstance(value, dict):
        raise validation_error("Schema root must be an object.", schema=name)
    try:
        jsonschema.Draft202012Validator.check_schema(value)
    except jsonschema.SchemaError as exc:
        raise validation_error(
            "RepoOS schema is invalid.", schema=name, reason=exc.message
        ) from exc
    return value


def validate_document(
    document: str | Path,
    schema_name: str,
    *,
    directory: str | Path | None = None,
) -> list[ValidationFinding]:
    instance = load_document(document)
    return validate_instance(
        instance,
        schema_name,
        directory=directory,
        source=str(Path(document)),
    )


def validate_instance(
    instance: Any,
    schema_name: str,
    *,
    directory: str | Path | None = None,
    source: str = "<memory>",
) -> list[ValidationFinding]:
    """Validate an in-memory value before it is persisted."""

    schema = load_schema(schema_name, directory=directory)
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    findings: list[ValidationFinding] = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        findings.append(
            ValidationFinding(
                source,
                f"{location}: {error.message}",
            )
        )
    return findings


def validate_codex_config(path: Path) -> list[ValidationFinding]:
    """RepoOS intentionally permits no project config keys in v0.1.0."""

    if not path.is_file():
        return [ValidationFinding(str(path), "Required minimal project config is missing.")]
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        return [ValidationFinding(str(path), f"Invalid TOML: {exc}")]
    if value:
        return [
            ValidationFinding(
                str(path),
                f"Unsupported project config keys: {', '.join(sorted(value))}. "
                "RepoOS v0.1.0 keeps project policy in AGENTS.md and RepoOS schemas.",
            )
        ]
    return []


def validate_agents(directory: Path) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    for obsolete in sorted(directory.glob("*.md")):
        findings.append(
            ValidationFinding(str(obsolete), "Markdown custom-agent format is obsolete.")
        )
    for path in sorted(directory.glob("*.toml")):
        try:
            value = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            findings.append(ValidationFinding(str(path), f"Invalid TOML: {exc}"))
            continue
        required = {"name", "description", "developer_instructions"}
        missing = sorted(required - value.keys())
        if missing:
            findings.append(
                ValidationFinding(str(path), f"Missing required keys: {', '.join(missing)}")
            )
        for key in required & value.keys():
            if not isinstance(value[key], str) or not value[key].strip():
                findings.append(ValidationFinding(str(path), f"{key} must be a non-empty string."))
    return findings


def validate_skills(directory: Path) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    for path in sorted(directory.glob("*/SKILL.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(ValidationFinding(str(path), f"Unreadable skill: {exc}"))
            continue
        match = _SKILL_FRONTMATTER.match(text)
        if match is None:
            findings.append(ValidationFinding(str(path), "Missing YAML front matter."))
            continue
        try:
            metadata = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            findings.append(ValidationFinding(str(path), f"Invalid front matter: {exc}"))
            continue
        if not isinstance(metadata, dict):
            findings.append(ValidationFinding(str(path), "Front matter must be a mapping."))
            continue
        for key in ("name", "description"):
            if not isinstance(metadata.get(key), str) or not metadata[key].strip():
                findings.append(ValidationFinding(str(path), f"Missing non-empty {key}."))
    return findings


def validate_hooks(path: Path) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [ValidationFinding(str(path), f"Invalid hook JSON: {exc}")]
    if (
        not isinstance(value, dict)
        or set(value) != {"hooks"}
        or not isinstance(value["hooks"], dict)
    ):
        return [ValidationFinding(str(path), "Expected one top-level 'hooks' object.")]
    for event, groups in value["hooks"].items():
        if event not in _HOOK_EVENTS:
            findings.append(ValidationFinding(str(path), f"Unsupported hook event: {event}"))
            continue
        if not isinstance(groups, list):
            findings.append(ValidationFinding(str(path), f"{event} must be an array."))
            continue
        for group_index, group in enumerate(groups):
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                findings.append(
                    ValidationFinding(str(path), f"{event}[{group_index}] requires a hooks array.")
                )
                continue
            for handler_index, handler in enumerate(group["hooks"]):
                if not isinstance(handler, dict):
                    findings.append(
                        ValidationFinding(
                            str(path),
                            f"{event}[{group_index}].hooks[{handler_index}] must be an object.",
                        )
                    )
                    continue
                if handler.get("type") != "command":
                    findings.append(
                        ValidationFinding(
                            str(path),
                            f"{event}[{group_index}].hooks[{handler_index}] must use type=command.",
                        )
                    )
                if not isinstance(handler.get("command"), str) or not handler["command"].strip():
                    findings.append(
                        ValidationFinding(
                            str(path),
                            f"{event}[{group_index}].hooks[{handler_index}] needs a command.",
                        )
                    )
    return findings


def validate_workflow(path: Path) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [ValidationFinding(str(path), f"Invalid workflow YAML: {exc}")]
    if not isinstance(value, dict):
        return [ValidationFinding(str(path), "Workflow root must be a mapping.")]
    permissions = value.get("permissions")
    if not isinstance(permissions, dict) or permissions.get("contents") != "read":
        findings.append(
            ValidationFinding(str(path), "Top-level permissions must include contents: read.")
        )
    if "concurrency" not in value:
        findings.append(ValidationFinding(str(path), "Workflow requires a concurrency policy."))
    jobs = value.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        findings.append(ValidationFinding(str(path), "Workflow requires at least one job."))
        return findings
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            findings.append(ValidationFinding(str(path), f"Job {job_name} must be a mapping."))
            continue
        runner = job.get("runs-on")
        runner_text = json.dumps(runner).lower()
        if "self-hosted" in runner_text:
            findings.append(
                ValidationFinding(str(path), f"Job {job_name} uses self-hosted runner.")
            )
        if "timeout-minutes" not in job:
            findings.append(
                ValidationFinding(str(path), f"Job {job_name} requires timeout-minutes.")
            )
        steps = job.get("steps", [])
        if not isinstance(steps, list):
            findings.append(ValidationFinding(str(path), f"Job {job_name} steps must be an array."))
            continue
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if (
                isinstance(uses, str)
                and not uses.startswith("./")
                and not _ACTION_SHA.fullmatch(uses)
            ):
                findings.append(
                    ValidationFinding(
                        str(path),
                        f"Job {job_name} step {index} action is not pinned to a full SHA: {uses}",
                    )
                )
    return findings


def validate_markdown_links(repository: Path) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    candidates = [
        repository / "README.md",
        repository / "AGENTS.md",
        repository / "MEMORY.md",
        *sorted((repository / "docs").rglob("*.md")),
        *sorted((repository / "reports").rglob("*.md")),
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(ValidationFinding(str(path), f"Unreadable Markdown: {exc}"))
            continue
        for match in _MARKDOWN_LINK.finditer(text):
            target_text = match.group(1).strip().strip("<>")
            if target_text.startswith(("https://", "http://", "mailto:", "#")):
                continue
            path_text = target_text.split("#", 1)[0]
            if not path_text:
                continue
            target = (path.parent / path_text).resolve()
            try:
                target.relative_to(repository.resolve())
            except ValueError:
                findings.append(
                    ValidationFinding(str(path), f"Local link escapes repository: {target_text}")
                )
                continue
            if not target.exists():
                findings.append(ValidationFinding(str(path), f"Broken local link: {target_text}"))
    return findings


def validate_recurring_specs(directory: Path) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    expected = {
        "daily-health.yaml",
        "weekly-review.yaml",
        "biweekly-proposal.yaml",
        "monthly-architecture-audit.yaml",
    }
    present = {path.name for path in directory.glob("*.yaml")}
    for missing in sorted(expected - present):
        findings.append(ValidationFinding(str(directory / missing), "Recurring spec is missing."))
    for path in sorted(directory.glob("*.yaml")):
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            findings.append(ValidationFinding(str(path), f"Invalid recurring spec: {exc}"))
            continue
        if not isinstance(value, dict):
            findings.append(ValidationFinding(str(path), "Recurring spec root must be a mapping."))
            continue
        if value.get("read_only") is not True:
            findings.append(ValidationFinding(str(path), "Recurring spec must be read_only."))
        if value.get("external_writes") is not False:
            findings.append(
                ValidationFinding(str(path), "Recurring spec must deny external_writes.")
            )
    return findings


def validate_version_sources(repository: Path) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    try:
        version_file = (repository / "VERSION").read_text(encoding="utf-8").strip()
        pyproject = tomllib.loads((repository / "pyproject.toml").read_text(encoding="utf-8"))
        package_text = (repository / "src" / "repoos" / "__init__.py").read_text(encoding="utf-8")
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        return [ValidationFinding(str(repository), f"Version source could not be read: {exc}")]
    project = pyproject.get("project")
    pyproject_version = project.get("version") if isinstance(project, dict) else None
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', package_text, re.MULTILINE)
    package_version = match.group(1) if match else None
    if not version_file or version_file != pyproject_version or version_file != package_version:
        findings.append(
            ValidationFinding(
                str(repository),
                "VERSION, pyproject.toml, and repoos.__version__ must agree.",
            )
        )
    return findings


def validate_all(root: str | Path) -> list[ValidationFinding]:
    repository = require_directory(root)
    findings: list[ValidationFinding] = []

    for schema_name in sorted(_SCHEMAS):
        try:
            load_schema(schema_name, directory=repository / "schemas")
        except Exception as exc:
            findings.append(ValidationFinding(f"schemas/{_SCHEMAS[schema_name]}", str(exc)))

    findings.extend(
        validate_document(
            repository / "registry" / "projects.yaml",
            "project-registry",
            directory=repository / "schemas",
        )
    )
    findings.extend(
        validate_document(
            repository / ".repoos" / "project.yaml",
            "project-manifest",
            directory=repository / "schemas",
        )
    )
    findings.extend(validate_codex_config(repository / ".codex" / "config.toml"))
    findings.extend(validate_agents(repository / ".codex" / "agents"))
    findings.extend(validate_skills(repository / ".agents" / "skills"))
    findings.extend(validate_hooks(repository / ".codex" / "hooks.json"))
    for workflow in sorted((repository / ".github" / "workflows").glob("*.y*ml")):
        findings.extend(validate_workflow(workflow))
    findings.extend(validate_markdown_links(repository))
    findings.extend(validate_recurring_specs(repository / "automation" / "recurring"))
    findings.extend(validate_version_sources(repository))

    learning_schema = {
        "observations": "observation",
        "candidates": "candidate-pattern",
        "accepted": "candidate-pattern",
        "rejected": "candidate-pattern",
        "adoption-ledger": "adoption-record",
    }
    for directory_name, schema_name in learning_schema.items():
        for record in sorted((repository / "learning" / directory_name).glob("*.json")):
            findings.extend(
                validate_document(record, schema_name, directory=repository / "schemas")
            )
    return findings


def available_schemas() -> list[str]:
    return sorted(_SCHEMAS)
