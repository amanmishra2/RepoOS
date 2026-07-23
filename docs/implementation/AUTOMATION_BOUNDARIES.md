# Automation boundaries

Status: authoritative

## Deterministic local automation

Allowed without new external authority:

- read-only discovery and metadata inventory;
- schema and reference validation;
- status, doctor, diff, audit, update check, plan generation, and reporting;
- neutral fixture tests;
- dry-run rendering;
- explicit fixture apply/backup/rollback tests.

Real apply requires an explicit repository and execute switch, clean/common-Git state, lock, fresh plan, backup, limits, and repository-owned validation.

## External actions

RepoOS never implicitly commits, pushes, opens PRs, merges, changes rulesets, registers runners, edits secrets/variables, installs a GitHub App, changes organization settings, or writes user-global Codex configuration. Each requires a separate approved action with its own preview and rollback.

## AI boundary

AI may summarize redacted evidence, cluster observations, or draft candidate records. It may not:

- set approval fields;
- change eligibility or ownership;
- write a target repository;
- weaken a stop condition;
- promote a component/channel;
- operate on secrets or unapproved private content.

The system remains useful with AI disabled.

## Pause and locking

Initial pause precedence, strictest wins:

1. `REPOOS_PAUSED` environment value;
2. local state-root pause file;
3. target-specific block from Git/safety validation.

A process rechecks pause before planning and before each mutation boundary. Already-running jobs stop before the next write boundary and report partial/no-write state.

Locks use the canonical common Git directory identity for repositories and a separate portfolio operation key for multi-repository reads. Lock contention fails closed; stale-lock recovery requires explicit inspection.

## GitHub Actions

Initial CI uses GitHub-hosted ephemeral runners, read-only permissions, full-SHA-pinned third-party actions, concurrency cancellation, timeouts, deterministic commands, and no repository secrets. Scheduled jobs are read-only. Self-hosted runners and organization-wide reuse are authorization-dependent future decisions.

## Recurring work

| Cadence | Initial home | Mutation |
|---|---|---|
| On demand/daily health | Manual CLI or read-only CI | None |
| Weekly cross-project review | Manual/Codex task using redacted reports | None |
| Biweekly update proposal | Manual CLI | Plan only |
| Monthly architecture audit | Manual or read-only CI | None |

No long-running daemon is justified.

## Limits

Plans include maximum files, bytes, and repositories. Initial mutation scope is one explicit repository and one plan. Portfolio-wide write flags do not exist.
