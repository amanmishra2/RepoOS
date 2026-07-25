# Schema reference

RepoOS uses JSON Schema Draft 2020-12 with unknown-field rejection. `doctor` and `validate --all`
load all 11 contracts.

Desired-state and learning contracts:

- `project-registry.schema.json`
- `project-manifest.schema.json`
- `observation.schema.json`
- `candidate-pattern.schema.json`
- `adoption-record.schema.json`

Transactional contracts:

- `update-plan.schema.json` — immutable marked-fixture update-plan v2;
- `manifest-bootstrap-plan.schema.json` — immutable one-file real-worktree bootstrap plan v1;
- `manifest-bootstrap-authorization.schema.json` — expiring local exact-binding approval v1;
- `transaction.schema.json` — lifecycle, operation kind, affected paths, validation, and failure;
- `backup-manifest.schema.json` — operation-specific original/absence and restoration evidence;
- `transaction-observation.schema.json` — bounded public-safe transaction outcome.

Fixture plan IDs are canonical SHA-256 digests of every field except `plan_id`. Bootstrap plans
carry both a canonical plan ID and explicit plan digest; both bind every other plan field.
Bootstrap authorization IDs digest their immutable exact-target/plan/manifest binding while
lifecycle fields record reservation and consumption.

Backup manifests have a canonical integrity digest plus hashes for the exact plan, manifest,
transaction, and target-state snapshots. Bootstrap backups additionally prove destination absence,
parent state, authorization/manifest digests, and protected sibling/common-Git summaries. Code
enforces cross-field invariants including operation kind, restore order, path state, transaction
identity, clean target, ownership, modes, hashes, and absence.

The project-manifest schema remains compatible with existing manifests; its optional
`sensitivity_classification` field is required by the stricter manifest-bootstrap semantic gate.
Bootstrap also requires exact RepoOS version `0.3.0`, no managed/generated/extension components,
no overlays or local overrides, and denied mutation permissions.

Validate a document:

```bash
repoos validate path/to/document.json --schema manifest-bootstrap-plan
```

Validate all RepoOS surfaces:

```bash
repoos --format json validate --all
```

Transaction, backup, plan, and authorization artifacts belong in local state and are not committed
automatically. Public-safe observations exclude target paths, sibling paths, file/untracked names
and bodies, authorization identity text, environment values, credentials, and unbounded output.
