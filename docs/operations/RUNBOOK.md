# Runbook

## Read-only health

```bash
repoos --format json doctor
repoos --format json validate --all
repoos --format json audit --all
```

## Transaction inspection

```bash
repoos --state-dir /tmp/repoos-state transaction list
repoos --state-dir /tmp/repoos-state transaction show <transaction-id>
```

The record shows lifecycle history, approved paths and ownership, hashes, validation results,
rollback state, failure classification, duration, and safety overrides. Full file contents and
unbounded output are not recorded.

## Verification

```bash
make verify
```

Use the targeted commands in [Verification](../verification.md) when diagnosing a transaction
boundary. All destructive tests must create disposable Git repositories beneath temporary
directories.

## Failure triage

Classify failures as invalid input, schema, dirty repository, stale plan, lock, pause, safety
limit, backup, apply, target validation, rollback, environment, authorization, pre-existing, or
out of scope. Do not suppress a failure or mutate a target to make a check pass.

Stable exits and operator actions are listed in [Troubleshooting](../reference/TROUBLESHOOTING.md).

## Incident stop

Set `REPOOS_PAUSED=1`, preserve the state directory, and stop before the next target write boundary.
Inspect the exact transaction, target/common-Git identity, backup manifest, and lock metadata. Do
not delete locks as stale without verifying the owner.

If the process is gone, retry only the bounded apply or rollback command with
`--recover-stale-lock`. Recovery preserves the previous lock record. Never use the flag against a
live owner.

## `rollback_failed`

Do not loop. Preserve the backup and transaction record, validate the backup, and inspect only its
`restore_order` paths. Follow the manual instructions emitted with exit `15`. Do not use Git
history/worktree cleanup commands as a file-restoration mechanism.

## Escalation

Request explicit direction for real project identity, sensitivity, commands, ownership, canary
eligibility, release, GitHub settings, user-global files, force behavior, or rollback ambiguity.
The fixture marker does not grant authority over a real repository.
