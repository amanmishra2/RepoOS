# Transaction rollback

RepoOS `0.3.0` supports rollback for fixture updates and guarded manifest bootstrap. Transaction,
plan, and backup schemas are authoritative; rollback never uses Git reset, clean, checkout, stash,
or worktree cleanup.

## Automatic rollback

After manifest installation or a fixture target write begins, apply/validation/preservation
failure moves the transaction to `rolling_back`. RepoOS validates the backup and restores only the
transaction-owned paths. Validation failure with successful restoration exits `14`; another apply
failure with successful restoration exits `13`. Neither is reported as completed.

For `manifest_bootstrap`, the backup records that `.repoos/project.yaml` was absent, the exact
pre-transaction parent state, target Git state, authorization/plan/manifest digests, and protected
sibling/common-Git summaries. Rollback:

- removes only the manifest created by that transaction;
- removes `.repoos` only when the transaction created it and it is still empty;
- preserves a pre-existing `.repoos` directory and every unrelated entry;
- proves the original target state and protected sibling/common-Git state;
- retains the transaction, plan snapshot, backup, and public-safe observation.

Runtime transaction evidence records whether RepoOS created the parent and the installed
manifest's device/inode. Rollback also requires the exact approved digest and mode. If another
actor races a different file into the destination, RepoOS preserves it and ends `rollback_failed`
rather than treating plan-time absence as deletion authority.

## Manual rollback

```bash
repoos --format json --state-dir /path/to/local/repoos-state \
  rollback --transaction tx-20260725T120000Z-aaaaaaaaaaaa
```

Manual rollback validates the transaction, plan snapshot, backup integrity, target/common-Git
identity, operation kind, HEAD, affected-path state, and protected sibling state before acquiring
the common-Git lock and restoring. Fixture restoration supports original or recorded-applied
states. Bootstrap restoration accepts only the approved created manifest or an already restored
state. Unexpected unrelated target drift, sibling drift, or unsafe parent contents fails closed.

Rollback is idempotent. Repeating a successful rollback returns `already_rolled_back` without
target writes.

## Stale locks and interruption

An interrupted process may leave a nonterminal transaction and stale lock. Inspect both first.
Explicit recovery preserves the previous lock record:

```bash
repoos --state-dir /path/to/local/repoos-state rollback \
  --transaction <transaction-id> --recover-stale-lock
```

Never recover a live owner. Apply and rollback interruption tests prove that a resumable
transaction remains bounded to its recorded operation and paths.

## Rollback failure

`rollback_failed` is terminal. RepoOS stops and preserves all evidence; it does not loop or broaden
the restore set. Keep the state directory and follow only the recorded restore contract after
inspection. Never delete unrelated files or use Git history/worktree cleanup as restoration.

Rollback does not undo commits, pushes, merged changes, GitHub settings, or user-global state;
RepoOS never performs those actions in either supported transaction.
