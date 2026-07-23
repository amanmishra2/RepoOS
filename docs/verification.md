# Verification

Authoritative full local verification:

```bash
make verify
```

Equivalent commands:

```bash
python3 -m ruff format --check .
python3 -m ruff check .
python3 -m mypy src/repoos
python3 -m pytest
PYTHONPATH=src python3 -m repoos --format json validate --all
PYTHONPATH=src python3 -m repoos --help
PYTHONPATH=src python3 -m repoos --format json doctor
PYTHONPATH=src python3 -m repoos --format json check-update --project .
python3 -m build --no-isolation
```

An isolated `python3 -m build` may require network access to provision build dependencies. `--no-isolation` is the verified offline local path when the declared build backend is installed.

## Required evidence

Record command, exit status, relevant count/output, skipped checks, and failure classification. Do not claim backup, rollback, real apply, canary CI, or external behavior from the current dry-run-only test suite.

## CI

GitHub Actions uses hosted ephemeral runners, Python 3.11/3.13, read-only permissions, full-SHA action pins, concurrency cancellation, and timeouts. Local success is not evidence that an unobserved remote run passed.

## Safety confirmation

Confirm no downstream repository, dirty tree, user-global file, GitHub setting, runner, issue, branch push, PR, release, or merge was changed unless the exact action was separately authorized and recorded.
