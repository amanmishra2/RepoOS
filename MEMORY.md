# RepoOS durable memory

This file contains stable repository facts, not task notes or raw portfolio evidence.

## Current facts

- RepoOS is a deterministic repository control plane, not a copyable whole-tree template.
- Version `0.1.0` implements read-only discovery/validation and fixture-bounded planning with dry-run apply revalidation.
- Apply execution, downstream adoption, user-global installation, external GitHub mutation, release publication, managed sections, real overlays, and AI promotion are not implemented.
- RepoOS is public; committed portfolio evidence uses aliases and redaction.
- Initial CI uses GitHub-hosted ephemeral runners with read-only permissions and immutable action pins.
- The public registry contains RepoOS only; private mappings belong in the ignored local overlay.

## Durable constraints

- Unknown ownership is repository-owned.
- Dirty, paused, locked, stale, conflicted, out-of-root, symlinked, or ambiguous mutation targets fail closed.
- Linked worktrees sharing one common Git directory share safety and lock identity.
- Discovery does not execute project code or modify the registry.
- RepoOS never implicitly commits, pushes, opens PRs, merges, or changes external settings.
- No secret, credential, private customer data, database content, raw trace, or private project identifier belongs in public reports.
- Every shipped guardrail needs a semantic positive and negative fixture.

## Known limitations

- Apply is dry-run-only.
- Backups, operation journal execution, atomic multi-file apply, and rollback are designed but not yet shipped.
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
