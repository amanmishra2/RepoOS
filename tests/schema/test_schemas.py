from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from repoos.validation import (
    available_schemas,
    load_document,
    load_schema,
    repo_root,
    validate_document,
)


@pytest.mark.parametrize("schema_name", available_schemas())
def test_every_schema_is_valid_draft_2020_12(schema_name: str) -> None:
    jsonschema.Draft202012Validator.check_schema(load_schema(schema_name))


def test_repository_registry_is_valid() -> None:
    findings = validate_document(
        repo_root() / "registry" / "projects.yaml",
        "project-registry",
    )
    assert findings == []


def test_repoos_manifest_is_valid() -> None:
    findings = validate_document(
        repo_root() / ".repoos" / "project.yaml",
        "project-manifest",
    )
    assert findings == []


@pytest.mark.parametrize(
    ("schema_name", "value"),
    [
        ("project-registry", {"schema_version": 1, "unknown": True}),
        ("project-manifest", {"manifest_version": 1, "unknown": True}),
        ("observation", {"schema_version": 1, "unknown": True}),
        ("candidate-pattern", {"schema_version": 1, "unknown": True}),
        ("adoption-record", {"schema_version": 1, "unknown": True}),
        ("update-plan", {"schema_version": 1, "unknown": True}),
        ("transaction", {"schema_version": 1, "unknown": True}),
        ("backup-manifest", {"schema_version": 1, "unknown": True}),
        ("transaction-observation", {"schema_version": 1, "unknown": True}),
    ],
)
def test_invalid_minimal_documents_are_rejected(
    tmp_path: Path,
    schema_name: str,
    value: dict[str, object],
) -> None:
    path = tmp_path / f"{schema_name}.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert validate_document(path, schema_name)


def test_valid_observation_fixture(tmp_path: Path) -> None:
    value = {
        "schema_version": 1,
        "observation_id": "OBS-20260723-abcdef12",
        "kind": "success",
        "summary": "Neutral fixture produced deterministic output.",
        "project_aliases": ["P06"],
        "evidence_refs": ["tests/security/test_no_write.py"],
        "sensitivity": "public",
        "publishability": "public_safe",
        "deduplication_key": "a" * 64,
        "recorded_at": "2026-07-23T12:00:00Z",
    }
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert validate_document(path, "observation") == []


def test_public_registry_rejects_private_mode(tmp_path: Path) -> None:
    value = load_document(repo_root() / "registry" / "projects.yaml")
    assert isinstance(value, dict)
    value["privacy"] = "private"
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    findings = validate_document(path, "project-registry")
    assert any("public_safe" in finding.message for finding in findings)


def test_update_plan_rejects_parent_traversal(tmp_path: Path) -> None:
    plan = {
        "schema_version": 1,
        "plan_id": f"plan-{'a' * 64}",
        "project_id": "neutral-fixture",
        "base_commit": "b" * 40,
        "from_version": "0.1.0",
        "to_version": "0.1.0",
        "operations": [
            {
                "action": "create",
                "source": "../secret",
                "target": "managed/value.txt",
                "source_sha256": "c" * 64,
                "before_sha256": None,
                "size_bytes": 1,
            }
        ],
        "conflicts": [],
        "limits": {"max_files": 20, "max_bytes": 1000},
        "dry_run_default": True,
    }
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    findings = validate_document(path, "update-plan")
    assert findings
    assert any("operations/0/source" in finding.message for finding in findings)


@pytest.mark.parametrize(
    ("schema_name", "fixture_name"),
    [
        ("transaction", "transaction.valid.json"),
        ("backup-manifest", "backup-manifest.valid.json"),
        ("transaction-observation", "transaction-observation.valid.json"),
    ],
)
def test_transactional_schema_fixtures_are_valid(
    schema_name: str,
    fixture_name: str,
) -> None:
    fixture = repo_root() / "tests" / "fixtures" / "schemas" / fixture_name
    assert validate_document(fixture, schema_name) == []


@pytest.mark.parametrize(
    ("schema_name", "fixture_name"),
    [
        ("transaction", "transaction.invalid.json"),
        ("backup-manifest", "backup-manifest.invalid.json"),
        ("transaction-observation", "transaction-observation.invalid.json"),
    ],
)
def test_transactional_invalid_schema_fixtures_are_rejected(
    schema_name: str,
    fixture_name: str,
) -> None:
    fixture = repo_root() / "tests" / "fixtures" / "schemas" / fixture_name
    assert validate_document(fixture, schema_name)
