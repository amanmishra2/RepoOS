# Transaction rollback

The transaction and backup schemas are authoritative for stored fields. This runbook explains the
shipped `0.2.0` fixture behavior.

## Automatic rollback

A target-write, owned-file verification, command-start, timeout, or required-validation failure
after apply begins moves the transaction to `rolling_back`. RepoOS validates the backup, restores
entries in reverse order, removes files created by the transaction, restores original bytes and
modes, and requires the original HEAD/status fingerprint before marking `rolled_back`.

A validation failure with successful restoration exits `14`; an apply failure with successful
restoration exits `13`. Neither state can be reported as `completed`.

## Manual rollback

```bash
repoos --format json --state-dir /tmp/repoos-state \
  rollback --transaction tx-20260723T120000Z-aaaaaaaaaaaa
```

Manual rollback:

- locates and schema-validates the transaction and plan snapshot;
- validates backup manifest, snapshot, and file hashes;
- verifies fixture path, common-Git identity, and unchanged HEAD;
- acquires the per-repository lock;
- permits each owned path to be either the recorded original or intended applied state, which
  supports interrupted partial transactions;
- refuses any other affected-file hash/mode or unrelated working-tree path;
- restores only the backup `restore_order` paths;
- verifies byte-for-byte/mode and clean status restoration.

No force mode is shipped. A second rollback returns a clear `already_rolled_back` result without
writing the target.

## Stale locks and interruption

An interrupted process may leave both a nonterminal transaction and a stale lock. Inspect the
transaction and lock owner first. Recovery requires the explicit flag, which preserves the prior
lock record:

```bash
repoos --state-dir /tmp/repoos-state rollback \
  --transaction <transaction-id> --recover-stale-lock
```

## Rollback failure

`rollback_failed` is terminal. RepoOS stops, retains the backup, reports its location and approved
restore order, and does not retry. Preserve the state directory; restore only those original
bytes/modes manually after inspection. Never use `git reset`, `clean`, `checkout`, or `stash` to
erase unrelated repository state.

Merged changes, real repositories, GitHub settings, and user-global files are outside this local
fixture rollback contract and require forward, separately authorized recovery plans.
