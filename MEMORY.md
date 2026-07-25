# RepoOS durable memory

This file contains stable repository facts, not task notes or raw portfolio evidence.

## Current facts

- RepoOS is a deterministic repository control plane, not a copyable whole-tree template.
- Version `0.3.0` preserves fixture update-plan v2 and adds one separately versioned,
  authorization-bound real-repository operation: create an absent `.repoos/project.yaml`.
- Manifest bootstrap creates one file, never replaces a manifest, has fixed limits, uses
  absence-aware backup/atomic install, validates repository-owned commands, and supports
  automatic/manual idempotent rollback.
- General real-repository update, overlays, component writes, deletion, force, commit, push, PR,
  GitHub mutation, user-global installation, release publication, and AI promotion are not
  implemented.
- RepoOS is public; committed portfolio evidence uses aliases and redaction.
- The public registry contains RepoOS only; private mappings belong in ignored local state.

## Durable constraints

- Unknown ownership is repository-owned.
- A plan is not authorization; bootstrap approval is exact, expiring, one-use local state.
- Dirty target, pause, lock, stale state, unsafe path, or ambiguity fails closed.
- Target cleanliness and sibling preservation are separate. A dirty sibling may be protected, but
  its bodies are not opened and any ambiguity/drift blocks.
- Linked worktrees share common-Git lock identity; sibling paths are never writable.
- A transaction cannot enter `applying` until its operation-specific backup passes integrity.
- Rollback restores only transaction-owned state; `rollback_failed` is terminal.
- Discovery does not execute project code or modify the registry.
- RepoOS never implicitly changes Git refs/worktrees, commits, pushes, opens PRs, merges, or changes
  external settings.
- No secret, credential, private customer data, raw trace, untracked sibling name/body, or private
  project identifier belongs in public evidence.
- Every shipped guardrail needs semantic positive and negative synthetic proof.

## Known limitations

- Fixture update/rollback remains restricted to marked disposable repositories.
- Real execution is only `manifest_bootstrap` for `.repoos/project.yaml`.
- Delete, force, overlays, component updates, multiple sections, and structured-file sections are
  unsupported.
- RepoOS source compatibility is exact for both executable plan versions while pre-1.0.
- Backups use manual retention; no destructive automatic cleanup is installed.
- No downstream canary is approved or executed.
- Installed Codex acceptance is not strict schema validation.

## P08 preservation decision

P08-W2 contains active or potentially active work and remains untouched; its untracked bodies are
excluded from inspection, reports, and learning. P08-W1 also remains unchanged. A later canary
must use a newly created isolated worktree from revalidated current `main`.

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
