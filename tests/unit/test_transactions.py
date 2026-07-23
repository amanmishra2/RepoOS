from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from repoos.errors import RepoOSError
from repoos.planning import build_update_plan
from repoos.transactions import TransactionStore, new_transaction_id
from repoos.validation import validate_document


def _plan(repoos_fixture: Path, tmp_path: Path) -> dict[str, object]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "value.txt").write_text("managed\n", encoding="utf-8")
    return build_update_plan(
        repoos_fixture,
        source,
        ["value.txt=managed/value.txt"],
        target_version="0.2.0",
    )


def test_transaction_id_is_deterministic_with_injected_inputs() -> None:
    instant = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)
    first = new_transaction_id("plan-" + "a" * 64, now=instant, nonce="fixture")
    second = new_transaction_id("plan-" + "a" * 64, now=instant, nonce="fixture")
    assert first == second == "tx-20260723T120000Z-249263296ce4"


def test_transaction_state_machine_and_observation(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    plan = _plan(repoos_fixture, tmp_path)
    store = TransactionStore(tmp_path / "state")
    record = store.create(
        plan,
        now=datetime(2026, 7, 23, 12, 0, tzinfo=UTC),
        transaction_id="tx-20260723T120000Z-aaaaaaaaaaaa",
    )
    assert record["state"] == "planned"
    for state in (
        "validated",
        "locked",
        "backed_up",
        "applying",
        "applied",
        "validating",
        "completed",
    ):
        record = store.transition(record["transaction_id"], state)
    assert record["state"] == "completed"
    observation = store.directory(record["transaction_id"]) / "observation.json"
    assert validate_document(observation, "transaction-observation") == []
    value = json.loads(observation.read_text(encoding="utf-8"))
    assert "full_file_contents" not in value
    assert value["outcome"] == "completed"


def test_invalid_transaction_transition_fails_deterministically(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    plan = _plan(repoos_fixture, tmp_path)
    store = TransactionStore(tmp_path / "state")
    record = store.create(plan)
    with pytest.raises(RepoOSError) as caught:
        store.transition(record["transaction_id"], "completed")
    assert caught.value.error_type == "invalid_input"
    assert store.load(record["transaction_id"])["state"] == "planned"


def test_failed_transaction_is_listed_without_file_contents(
    repoos_fixture: Path,
    tmp_path: Path,
) -> None:
    plan = _plan(repoos_fixture, tmp_path)
    store = TransactionStore(tmp_path / "state")
    record = store.create(plan)
    store.mark_failure(
        record["transaction_id"],
        classification="stale_plan",
        message="Approved plan is stale.",
        failed_precondition="target_changed",
    )
    summaries = store.list()
    assert summaries == [
        {
            "transaction_id": record["transaction_id"],
            "project_id": "neutral-fixture",
            "state": "failed",
            "started_at": record["started_at"],
            "completed_at": store.load(record["transaction_id"])["completed_at"],
            "file_count": 1,
            "failure_classification": "stale_plan",
        }
    ]
