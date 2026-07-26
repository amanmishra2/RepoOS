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
PYTHONPATH=src python3 -m repoos plan-manifest-bootstrap --help
PYTHONPATH=src python3 -m repoos authorize-manifest-bootstrap --help
PYTHONPATH=src python3 -m repoos apply --help
PYTHONPATH=src python3 -m repoos rollback --help
PYTHONPATH=src python3 -m repoos transaction --help
PYTHONPATH=src python3 -m repoos --format json doctor
PYTHONPATH=src python3 -m repoos --format json check-update --project .
python3 -m build --no-isolation
python3 tools/verification/installed_wheel_smoke.py
git diff --check
```

An isolated `python3 -m build` may require network access to provision build dependencies.
`--no-isolation` is the verified offline path when the declared backend is installed.

## Transaction proofs

Every target-write, rollback, interruption, drift, and concurrency test uses synthetic Git
repositories beneath temporary directories:

```bash
python3 -m pytest tests/integration/test_transactional_apply.py
python3 -m pytest tests/integration/test_manifest_bootstrap.py
python3 -m pytest tests/cli/test_cli.py
python3 -m pytest tests/schema/test_schemas.py
python3 -m pytest tests/security
```

The fixture suite proves existing update-plan v2 behavior, ownership/section boundaries, limits,
locks, backup integrity, atomic writes, validation, interruption, and rollback.

The manifest-bootstrap suite proves single/multi-worktree success; protected dirty sibling
preservation without body opens or persisted untracked names; existing manifest/parent variants;
dirty/stale/changed input/plan refusal; exact authorization expiry/replay/cross-worktree/HEAD
binding; lock and sibling ambiguity; symlink/traversal/submodule/bare/detached limits;
post-install validation and rollback; interrupted apply/rollback; sibling drift evidence;
destination races; schema/broad-ownership refusal; same-common-Git serialization; unrelated-repo
concurrency; fixture compatibility; general real-update refusal; and dry-run zero writes.

## Installed-wheel smoke

`make wheel-smoke` builds the wheel, installs it without dependencies into a fresh temporary
virtual environment with verified site packages, and runs version/doctor/help plus full synthetic
fixture and manifest-bootstrap workflows. Bootstrap smoke includes plan, no-state dry run,
authorization, apply, transaction show/list, manual rollback, and repeated rollback. It never uses
a downstream repository or network service.

## Required evidence

Record command, exit status, test count, protected-worktree proof, no-write proof, rollback proof,
authorization lifecycle, installed-wheel result, skipped checks, and failure classification. Do
not infer downstream canary success from synthetic proof.

## CI and safety confirmation

GitHub Actions uses hosted ephemeral runners, Python 3.11/3.13, read-only permissions, immutable
action pins, concurrency cancellation, and timeouts. Local success is not evidence that an
unobserved remote run passed.

Confirm no downstream repository, protected dirty worktree, user-global file, GitHub resource,
runner, branch push, PR, release, or merge changed unless that exact action was separately
authorized and recorded.
