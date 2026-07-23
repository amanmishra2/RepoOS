# Schema reference

RepoOS uses JSON Schema Draft 2020-12 with unknown-field rejection.

Desired-state and learning contracts:

- `project-registry.schema.json`
- `project-manifest.schema.json`
- `observation.schema.json`
- `candidate-pattern.schema.json`
- `adoption-record.schema.json`

Transactional contracts:

- `update-plan.schema.json` — immutable plan v2, exact roots/Git/manifest/ownership/hashes/limits
- `transaction.schema.json` — lifecycle, affected paths, validation, rollback, and failure state
- `backup-manifest.schema.json` — approved original bytes/modes, restore order, and integrity digest
- `transaction-observation.schema.json` — bounded public-safe outcome for the learning system

Plan IDs are canonical SHA-256 digests of every plan field except `plan_id`. Backup manifests have
a second canonical integrity digest plus hashes for the exact plan, manifest, transaction, and
target-state snapshots and every stored original file. Code additionally enforces cross-field
invariants such as restore order, existed/backup metadata, transaction identity, clean target
state, and content hashes.

Representative valid and invalid transactional fixtures live under `tests/fixtures/schemas/`.

Validate a document:

```bash
repoos validate path/to/document.json --schema transaction
```

Validate all RepoOS surfaces:

```bash
repoos --format json validate --all
```

Transaction and backup records live in the configured local state directory and are not committed
automatically. The public-safe observation does not contain target paths, full content, environment
values, credentials, or unbounded command output.
