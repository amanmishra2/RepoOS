# Roadmap

The detailed dependency graph is [VALIDATED_ISSUE_BACKLOG.md](implementation/VALIDATED_ISSUE_BACKLOG.md).

## Foundation

- Complete Phase 1/ZIP/portfolio validation.
- Establish version, package, schemas, public registry, manifest, read-only CLI, active Codex repair, hosted CI, and neutral semantic tests.

## Controlled update fixtures

- Completed locally: transaction records, atomic approved-path backups, managed/generated/text-section
  apply, bounded validation, automatic/manual rollback, explicit stale-lock recovery, and
  public-safe outcomes.
- Completed locally: dirty/stale/conflict/symlink/lock/pause/limit/interruption/fault-injection,
  concurrency, idempotency, integrity, and byte-restoration fixtures.

## Canary

- Completed locally: guarded real-worktree manifest bootstrap with exact authorization,
  multi-worktree protection, and synthetic rollback proof.
- In a later run, revalidate GitHub `main` and create a new isolated P08 worktree while preserving
  P08-W1 and P08-W2.
- Review dry run; stop for execute approval; apply only the manifest; validate and roll back.
- Stop for reapplication approval; create only a local manifest commit after all gates.
- Push, PR, and any bounded component remain separately authorized future work.

## Later

- Add release artifact integrity and compatibility migration before relaxing exact source-version
  matching.
- Consider deletion, force recovery, or richer section support only through separate bounded
  issues with new safety evidence.
- Broad rollout one repository at a time.
- Release artifact integrity/retention.
- Evidence-backed overlays.
- Optional global installer, GitHub governance, or scheduled learning only after separate authorization and measured need.
