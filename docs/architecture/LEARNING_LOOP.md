# Learning loop

The initial loop is Git-tracked and human-controlled:

1. Record a redacted observation.
2. Deduplicate by a deterministic key.
3. Propose a candidate pattern.
4. Evaluate portability, ownership, risk, exceptions, tests, and rollback.
5. Accept or reject through a human decision record.
6. Track explicit adoption, deferral, exclusion, or rollback.
7. Feed regressions back into tests or policy.

Schemas live in `schemas/observation.schema.json`, `candidate-pattern.schema.json`, and `adoption-record.schema.json`. AI may summarize or cluster approved evidence but cannot approve, promote, or mutate. No service, database, or automatic promotion exists.
