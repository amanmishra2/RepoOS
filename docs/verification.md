# Verification

Authoritative full local verification:

```bash
make verify
```

Equivalent quality gates:

```bash
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src/repoos
python3 -m pytest
PYTHONPATH=src python3 -m repoos --format json validate --all
PYTHONPATH=src python3 -m repoos --help
PYTHONPATH=src python3 -m repoos apply --help
PYTHONPATH=src python3 -m repoos rollback --help
PYTHONPATH=src python3 -m repoos transaction --help
PYTHONPATH=src python3 -m repoos --format json doctor
PYTHONPATH=src python3 -m repoos --format json check-update --project .
python3 -m build --no-isolation
```

An isolated `python3 -m build` may require network access to provision build dependencies.
`--no-isolation` is the verified offline local path when the declared backend is installed.

## Transaction proofs

All target-write tests use temporary synthetic Git repositories:

```bash
python3 -m pytest tests/unit/test_ownership.py
python3 -m pytest tests/unit/test_pause_and_locks.py
python3 -m pytest tests/unit/test_safety_limits.py
python3 -m pytest tests/unit/test_transactions.py
python3 -m pytest tests/integration/test_transactional_apply.py
python3 -m pytest tests/cli/test_cli.py
python3 -m pytest tests/schema/test_schemas.py
python3 -m pytest tests/security
```

These suites prove valid/invalid lifecycle transitions; marker ambiguity and outside-byte
preservation; active/stale/malformed locks and explicit recovery; same-target refusal and
different-target concurrency; every safety-limit class; backup failure/integrity; failure after one
write; bounded validation failure; automatic and manual rollback; rollback failure terminality;
interruption recovery; symlink/traversal refusal; dry-run no-write behavior; repeat apply refusal;
repeat rollback idempotency; file-mode and byte-for-byte restoration; and transaction observation
schema safety.

## Installed-wheel smoke

Build the wheel, install it without dependencies into a fresh temporary virtual environment that
can see the already verified dependencies, and run:

```bash
repoos --version
repoos --format json doctor
repoos apply --help
repoos rollback --help
repoos transaction --help
```

The full installed-wheel proof additionally creates a temporary marked Git fixture and executes
plan, dry-run, apply, transaction show/list, manual rollback, and repeat rollback. It must not use a
real repository.

## Required evidence

Record command, exit status, test count, relevant proof, skipped checks, and failure classification.
Do not claim real-repository, canary CI, release compatibility, deletion, force rollback, external,
or user-global behavior from fixture tests.

## CI

GitHub Actions uses hosted ephemeral runners, Python 3.11/3.13, read-only permissions, full-SHA
action pins, concurrency cancellation, and timeouts. Local success is not evidence that an
unobserved remote run passed.

## Safety confirmation

Confirm no downstream repository, dirty tree, user-global file, GitHub setting, runner, issue,
branch push, PR, release, or merge was changed unless the exact action was separately authorized
and recorded.
