# Canary readiness audit

Date: 2026-07-23
Mode: read-only downstream audit and RepoOS-local decision preparation
Decision: no real-repository canary is currently eligible or authorized

## Privacy boundary

This packet is `public_safe`. It uses only the aliases P08, P04-A, and P04-B. Exact local paths,
repository names, remotes, and private commit identifiers are intentionally absent. The
schema-valid mapping is stored only in the ignored `.repoos/local/projects.private.yaml` overlay.

## Outcome

P08 remains the strongest provisional candidate, but its current classification is `blocked`.
Its primary checkout is clean but stale and its second registered worktree contains active
untracked implementation work. RepoOS `0.2.0` also cannot plan or apply a real-repository
manifest bootstrap. P04-B is `unsuitable_as_first_canary` because it shares P04-A's dirty common
Git directory and is materially stale.

No downstream write, cleanup, Git repair, GitHub mutation, or canary adoption was performed.

## Packet

| Document | Purpose |
|---|---|
| [00_EXECUTIVE_DECISION.md](00_EXECUTIVE_DECISION.md) | Decision and next gate |
| [01_P08_IDENTITY_AND_GITHUB.md](01_P08_IDENTITY_AND_GITHUB.md) | Aliased identity and live GitHub evidence |
| [02_P08_GIT_STATE.md](02_P08_GIT_STATE.md) | Local Git and base-authority evidence |
| [03_P08_WORKTREE_AUDIT.md](03_P08_WORKTREE_AUDIT.md) | Every current P08 worktree record |
| [04_P08_LIFECYCLE_AND_SENSITIVITY.md](04_P08_LIFECYCLE_AND_SENSITIVITY.md) | Lifecycle and confidentiality |
| [05_P08_PROJECT_FAMILY.md](05_P08_PROJECT_FAMILY.md) | Family and overlay assessment |
| [06_P08_VALIDATION_PROFILE.md](06_P08_VALIDATION_PROFILE.md) | Repository-owned validation contract |
| [07_P08_FILE_OWNERSHIP_MAP.md](07_P08_FILE_OWNERSHIP_MAP.md) | Proposed adoption boundary |
| [08_P08_TRANSACTION_COMPATIBILITY.md](08_P08_TRANSACTION_COMPATIBILITY.md) | RepoOS engine gap analysis |
| [09_P04B_FALLBACK_ASSESSMENT.md](09_P04B_FALLBACK_ASSESSMENT.md) | Bounded fallback assessment |
| [10_CANARY_SCORECARD.md](10_CANARY_SCORECARD.md) | Criterion-by-criterion decision |
| [11_REMEDIATION_PLAN.md](11_REMEDIATION_PLAN.md) | Required and optional follow-up |
| [12_USER_CONFIRMATION_REQUIRED.md](12_USER_CONFIRMATION_REQUIRED.md) | Remaining human decisions |
| [13_NEXT_CANARY_ADOPTION_PROMPT.md](13_NEXT_CANARY_ADOPTION_PROMPT.md) | Next read-only hygiene prompt; not executed |
| [canary-readiness.json](canary-readiness.json) | Deterministic machine-readable summary |

## Evidence limits

- The old 16-record P08 inventory is retained as stale historical evidence. Current Git metadata
  has two records and no prunable record.
- Git does not retain a reliable audit trail for removed worktree registrations. The discrepancy's
  actor and mechanism therefore remain unknown.
- P08's live default-branch tracked state was validated from a disposable archive, not from either
  registered worktree.
- No likely secret-bearing file, local database, personal configuration, or untracked file body
  was opened.
