# Learning ledger

RepoOS keeps redacted, reviewable learning state in Git:

- `observations/` — schema-valid evidence records
- `candidates/` — proposed reusable patterns
- `accepted/` — human-approved pattern decisions
- `rejected/` — human-rejected or deprecated decisions
- `adoption-ledger/` — explicit project/component adoption records

Raw logs, traces, private identifiers, secrets, databases, and customer/project content stay local. A record must pass its schema and publishability review before commit. AI cannot set approval fields.

Each fixture transaction writes a local `observation.json` conforming to
`transaction-observation.schema.json`. It records only outcome, component types, file count,
conflict classes, bounded validation/rollback results, duration, safety overrides, and failure
classification. It contains no target path or file content and is suitable for later reviewed
ingestion; it is not committed or promoted automatically.

No autonomous collection or promotion is installed in `0.2.0`. A successful fixture apply is not
evidence that a pattern is stable, required, or eligible for real-repository adoption.
