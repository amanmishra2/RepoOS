# Runbook

## Read-only health

```bash
repoos --format json doctor
repoos --format json validate --all
repoos --format json audit --all
```

## Verification

```bash
make verify
```

## Failure triage

Classify failures as product, test, environment, dependency, repository policy, authorization, pre-existing, or out of scope. Do not suppress a failure or mutate a target to make a check pass.

## Incident stop

Set `REPOOS_PAUSED=1`, preserve the journal/evidence, stop before the next write boundary, and inspect exact target/common-Git identity. Do not delete locks as “stale” without verifying the owning process and operation.

## Escalation

Request explicit direction for project identity, sensitivity, commands, ownership, release, GitHub settings, user-global files, or rollback ambiguity.
