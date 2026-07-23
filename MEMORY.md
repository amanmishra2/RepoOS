# RepoOS durable memory

This file contains stable repository facts, not task notes or raw portfolio evidence.

## Current facts

- RepoOS is a deterministic repository control plane, not a copyable whole-tree template.
- Version `0.2.0` implements read-only discovery/validation plus immutable fixture plans,
  process-visible locks, approved-path backups, atomic managed/generated/text-section apply,
  bounded validation, automatic/manual rollback, transaction inspection, and public-safe outcomes.
- Real-repository execution, downstream adoption, user-global installation, external GitHub
  mutation, release publication, structured-file/multiple managed sections, deletion, force
  rollback, real overlays, and AI promotion are not implemented.
- RepoOS is public; committed portfolio evidence uses aliases and redaction.
- Initial CI uses GitHub-hosted ephemeral runners with read-only permissions and immutable action pins.
- The public registry contains RepoOS only; private mappings belong in the ignored local overlay.

## Durable constraints

- Unknown ownership is repository-owned.
- Dirty, paused, locked, stale, conflicted, out-of-root, symlinked, or ambiguous mutation targets fail closed.
- Linked worktrees sharing one common Git directory share safety and lock identity.
- Stale or malformed locks require explicit recovery and are preserved as evidence.
- A transaction cannot enter `applying` until its approved-path backup passes integrity checks.
- Rollback restores only transaction-owned paths; unexpected drift fails closed and
  `rollback_failed` is terminal.
- Discovery does not execute project code or modify the registry.
- RepoOS never implicitly commits, pushes, opens PRs, merges, or changes external settings.
- No secret, credential, private customer data, database content, raw trace, or private project identifier belongs in public reports.
- Every shipped guardrail needs a semantic positive and negative fixture.

## Known limitations

- Executable apply and rollback are restricted to marked disposable fixtures.
- Delete, force apply/rollback, multiple sections per file, and structured-file sections are
  unsupported.
- RepoOS source compatibility is exact for update-plan v2 while the engine is pre-1.0.
- Backups use manual retention metadata; no destructive automatic cleanup is installed.
- No downstream canary is approved.
- Portfolio-wide Codex/workflow deep validation is incomplete outside RepoOS.
- Installed Codex acceptance is not treated as strict schema validation.

## Repeated-failure record format

```md
### Mistake: <name>
- Evidence:
- Correct behavior:
- Prevention mechanism:
- Validation:
- Related issue:
```

## Convention-change format

```md
### <YYYY-MM-DD> — <change>
- Verified behavior:
- Reason:
- Migration/rollback:
- Files:
```
