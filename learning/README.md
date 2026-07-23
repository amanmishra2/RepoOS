# Learning ledger

RepoOS keeps redacted, reviewable learning state in Git:

- `observations/` — schema-valid evidence records
- `candidates/` — proposed reusable patterns
- `accepted/` — human-approved pattern decisions
- `rejected/` — human-rejected or deprecated decisions
- `adoption-ledger/` — explicit project/component adoption records

Raw logs, traces, private identifiers, secrets, databases, and customer/project content stay local. A record must pass its schema and publishability review before commit. AI cannot set approval fields.

No autonomous collection or promotion is installed in `0.1.0`.
