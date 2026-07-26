# P08 validation profile

Date: 2026-07-23
Authority: default-branch `AGENTS.md`, `docs/verification.md`, `Makefile`, `pyproject.toml`, and CI

## Environment

- Python 3.11 or newer.
- The hosted workflows use Python 3.11.
- Editable development dependencies provide Pytest, Ruff, and MyPy.
- Default Pytest excludes `live` tests and installs a pre-collection socket guard.
- No credential or live provider is required for the required gates.
- Dependency installation is environment-mutating and potentially network-dependent; it is setup,
  not a canary validation step when a verified environment already exists.

## Authoritative commands

| Command | Classification | Purpose | Audit evidence |
|---|---|---|---|
| `make product-check` | Required and deterministic | Format, lint, type, product tests, no-network proof, doctor | Passed on the observed live default-branch tracked snapshot |
| `make agentops-check` | Required and deterministic | Static repository contracts, architecture, tool quality, AgentOps tests | Passed on the observed live default-branch tracked snapshot |
| `make check` | Required aggregate; medium cost | Product plus AgentOps | Not rerun because its two constituent gates were run separately |
| `python3 -m flight_finder doctor --json` | Required and deterministic | Offline CLI smoke | Passed as part of `make product-check` |
| `git diff --check` | Required and deterministic | Patch whitespace | Required after a future canary change |
| `git status --short` | Required and deterministic | Confirm exact change scope | Required before and after every future gate |
| Focused command from the owning issue packet | Required and deterministic when applicable | Path-specific proof | No adoption issue or packet exists yet |
| `python3 -m pip install -e '.[dev]'` | Required setup but environment-dependent | Provision tools | Not run; existing dependencies were used |
| `python3 -m build` | Obsolete or undocumented for current gate | Package build | No documented build target or declared build-tool dependency; not invented or run |
| Live provider/source smoke | Optional, network-dependent, and approval-gated | Live integration | Not eligible for a RepoOS canary |
| GitHub issue reconciliation apply or workflow dispatch | Unsafe for automated canary validation | External mutation | Prohibited |
| `make format` | Unsafe as validation because it writes files | Formatting repair | Do not run during readiness proof |

The latest default branch also documents a focused static contract validator for repository and
issue metadata changes. A future manifest-only issue should run that validator before the full
AgentOps gate if its approved packet requires it.

## Validation performed

The live GitHub default-branch SHA matched the local remote-tracking SHA. That exact tracked tree
was exported into a disposable directory outside both registered worktrees. Existing dependencies
were reused; caches and bytecode were redirected or disabled.

Final results:

| Gate | Result |
|---|---|
| Ruff format | Pass; 189 files already formatted |
| Ruff lint | Pass |
| MyPy | Pass; 189 source files |
| Product Pytest | Pass; 339 passed, 1 skipped, 297 deselected |
| No-network focused proof | Pass; 5 passed |
| Doctor | Pass; offline status `ok` |
| Static issue/context validation | Pass; 64 issues and associated contracts validated |
| Product architecture policy | Pass |
| AgentOps Ruff format/lint | Pass; 116-file format scope |
| AgentOps MyPy | Pass; 116 source files |
| AgentOps Pytest | Pass; 297 tests |

An initial audit invocation used `RUFF_NO_CACHE=1`; the installed Ruff version requires
`RUFF_NO_CACHE=true`, so Ruff stopped before substantive checks. After correction, the first
archive run had one environmental failure because `git check-attr` requires a `.git` directory
(338 tests passed before that failure). Initializing Git only in the disposable snapshot supplied
the expected attribute context, and the complete product gate passed. Neither event is a P08
product failure.

No command was executed in the dirty secondary worktree, and no untracked file body was read.

## Future canary order

1. Reconfirm overlay identity, live `main`, clean target, all worktree records, open-PR overlap,
   and exact issue packet.
2. Run the issue packet's focused static/manifest validation.
3. Run RepoOS plan validation and dry-run without target or state writes.
4. Obtain explicit execute approval.
5. Apply only the approved manifest bootstrap after the RepoOS enhancement exists.
6. Run `make agentops-check`.
7. Run `make product-check`.
8. Run `git diff --check` and `git status --short`.
9. Review the exact diff and rollback proof before a local commit.
10. Before push or merge, repeat the required gates against an unchanged base; require both hosted
    workflow conclusions to pass even though branch protection does not currently enforce them.

Build, security-vulnerability scanning, and live-provider checks are not silently added: no
authoritative current command exists for them.
