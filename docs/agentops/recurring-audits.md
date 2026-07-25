# Recurring audits

All initial recurring work is read-only and idempotent.

## Every PR

```bash
make verify
```

Run semantic tests, schema/Codex/workflow validation, lint, format, types, CLI smoke checks, and build.

## Weekly cross-project review

Use redacted reports to identify repeated evidence, exceptions, drift, and false claims. Do not execute project code or modify registries.

## Biweekly proposal review

Generate plans only for explicit clean targets with confirmed ownership and commands. Planning is not approval.

## Monthly architecture audit

Review ownership collisions, exception rate, rollback readiness, action pins, schema compatibility, confidentiality, and whether any overlay still has at least two valid consumers.

No schedule is installed by RepoOS `0.3.0`; operators may invoke these manually or through
read-only CI after review.
