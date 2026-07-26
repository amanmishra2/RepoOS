# Canary scorecard

Date: 2026-07-23
Status values: `pass`, `partial`, `fail`

| Criterion | P08 status | P08 evidence / blocker | P04-B status | P04-B evidence / blocker |
|---|---|---|---|---|
| Identity confirmed | pass | Overlay, local Git, remote, and GitHub agree | pass | Overlay and independently verified remote agree |
| GitHub repository accessible | pass | Private repository exists; sufficient later PR permissions | pass | Public repository exists; sufficient access |
| Lifecycle confirmed | pass | Active, high-velocity pre-release development | pass | Active development with many open changes |
| Clean worktree | fail | Primary is clean but stale; current-main secondary has 18 untracked entries | pass | P04-B itself is clean |
| Clean common Git state | fail | Active dirty sibling worktree in the same P08 common Git identity | fail | P04-A is dirty in the shared common Git identity |
| Default branch confirmed | pass | Live and local remote-tracking `main` agree | pass | Live `main` confirmed, but P04-B is not aligned |
| Upstream or review path confirmed | partial | PR path exists; current primary upstream was deleted after merge | partial | Remote branch exists but is seven commits ahead and its PR is already merged |
| Worktree state understood | pass | Both current records assessed; zero prunable | partial | Counts/blockers known, but 64 records were not individually audited |
| No unique-commit loss risk | partial | No unique commits; one worktree has unique untracked work | fail | Unique-commit risk across the large shared registry was not cleared |
| Validation commands confirmed | pass | Authoritative gates identified and passed on live tracked state | partial | Stale branch commands identified but not current or safely executable |
| Sensitivity confirmed | partial | Evidence supports personal-data risk; owner confirmation remains | partial | Financial/personal risk needs current owner confirmation |
| Project family confirmed | pass | Standalone Python CLI/application; no overlay yet | pass | Python banking application |
| Ownership boundaries confirmed | partial | Complete proposal exists; manifest transfer not approved | partial | Older operating-layer ownership has drifted |
| Minimal adoption scope available | pass | One manifest-only bootstrap is sufficient in concept | partial | Manifest is absent, but shared-state risk defeats isolation |
| Transaction engine compatible | fail | Real target and manifest bootstrap are unsupported | fail | Same engine gap plus shared dirty common Git state |
| Rollback boundary valid | partial | One-file rollback is representable after the engine/worktree gates | fail | Linked worktree has no independent common-Git boundary |
| Pull-request path available | pass | Private PR path and permissions exist | pass | Public PR path and permissions exist |
| Low interference with active work | fail | Active secondary implementation and high change velocity | fail | 18 open PRs, shared dirty work, and stale branch |
| User confirmations bounded | pass | Five material decisions remain | fail | Broad repository/worktree reconciliation would be required first |

## Totals

| Candidate | Pass | Partial | Fail | Classification |
|---|---:|---:|---:|---|
| P08 | 10 | 5 | 4 | `blocked` |
| P04-B | 7 | 6 | 6 | `unsuitable_as_first_canary` |

P08 would move first through `eligible_after_repository_hygiene`, then
`eligible_after_repoos_enhancement`; it is not assigned either eligibility label while both gates
remain open.

## Selection

P08 remains the only provisional candidate because its identity, lifecycle, default branch,
validation profile, family, and minimal scope are clear. That relative ranking does not grant
write authority. P04-B is not a fallback.

If P08 cannot preserve its active work while producing a fresh isolated base, the next candidate
should be an independent Git repository with one clean authoritative worktree, no private mapping
ambiguity, documented offline gates, low-sensitivity infrastructure scope, a protected review path,
and no active high-risk migration.
