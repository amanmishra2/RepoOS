# Runbook

## Read-only health

```bash
repoos --format json doctor
repoos --format json validate --all
repoos --format json audit --all
```

## Choose the exact operation

- Use `plan-update` only for a disposable repository carrying a regular `.repoos-fixture` marker.
- Use `plan-manifest-bootstrap` only to create an absent `.repoos/project.yaml` in one explicitly
  approved clean real worktree.
- Refuse every other real-repository write.

The full bootstrap eligibility, approval, and mutation boundary is centralized in
[Onboard an existing repository](ONBOARD_EXISTING_REPOSITORY.md).

## Transaction inspection

```bash
repoos --state-dir /path/to/local/repoos-state transaction list
repoos --state-dir /path/to/local/repoos-state transaction show <transaction-id>
```

Records show lifecycle history, operation kind, approved paths/ownership, hashes, validation,
rollback, failure classification, duration, and applicable safety authority. Bootstrap records add
authorization digests and content-free protected-worktree/common-Git evidence. File bodies,
untracked names, credentials, authorization identity text, environment values, and unbounded
command output are not recorded publicly.

## Verification

```bash
make verify
```

Use [Verification](../verification.md) for targeted commands. Every mutation, interruption,
rollback, concurrency, and dirty-worktree test must use synthetic temporary Git repositories.

## Failure triage

Classify failures as invalid manifest/input, existing destination, dirty/stale target, sibling
ambiguity, lock/pause, authorization lifecycle, backup/install/validation/preservation, rollback,
fixture safety limit, environment, or unsupported operation. Preserve target and state evidence;
do not mutate a repository to make a check pass. Stable exits and actions are in
[Troubleshooting](../reference/TROUBLESHOOTING.md).

## Incident stop

Set `REPOOS_PAUSED=1`, preserve the state directory, and stop before the next write boundary.
Inspect the exact transaction, target/common-Git identity, content-free sibling summaries, backup,
authorization lifecycle, and lock metadata. Do not open protected sibling file bodies.

If the process is gone, retry only the bounded apply or rollback command with
`--recover-stale-lock`. Recovery preserves the previous lock record and never overrides a live
owner.

## `rollback_failed`

Do not loop. Preserve the backup and transaction, validate their integrity, and inspect only the
approved restore path. Do not use Git reset, clean, checkout, stash, worktree prune, or sibling
mutation as a recovery mechanism.

## Escalation

Request separate authority for target identity, sensitivity, manifest content, execute,
post-rollback reapplication, local commit, push, pull request, release, GitHub settings,
user-global files, or any operation outside the fixed bootstrap boundary. One approval never
implies another.
