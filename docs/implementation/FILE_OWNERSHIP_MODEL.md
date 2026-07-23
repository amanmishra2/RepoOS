# File ownership model

Status: authoritative

## Ownership classes

| Class | Owner | RepoOS behavior |
|---|---|---|
| `managed_file` | RepoOS component | Compare to installed baseline; plan three-way update; stop on unknown baseline/conflict |
| `generated_file` | RepoOS generator | Verify input digest/generator version; reject unexplained local edits |
| `repository_owned` | Target repository | Never overwrite or include in a mutation plan |
| `repository_extension` | Target repository within an explicit extension point | Preserve exactly; validate boundary only |
| `local_override` | Target repository with named owner/reason/review date | Preserve; surface expiry/review; never silently normalize |
| `excluded` | Target repository | Do not inspect beyond metadata or mutate |

Unknown and unadopted paths are `repository_owned`.

## Managed sections

Managed sections are deferred in the initial release. They may be introduced only for a concrete, text-only use case with:

- a specified comment grammar;
- unique nonnested markers;
- byte-for-byte preservation outside the section;
- malformed/missing/duplicate marker refusal;
- encoding and line-ending fixtures;
- explicit migration and ownership transfer.

TOML, JSON, and workflow YAML are not section-managed.

## Path safety

- Every component declares one explicit relative target path; mutation globs are prohibited.
- Resolved paths must remain beneath the canonical target root.
- Symlink components and symlinked parent escapes are rejected.
- `.git`, dependency, build, cache, worktree, database, secret, log, and generated-data paths are excluded by default.
- A repository’s common Git directory is the lock and safety identity; linked worktrees are not independent repositories.

## Adoption and transfer

Similarity is not adoption. Adoption requires an explicit manifest entry, baseline, component version, ownership class, target path, and reviewed plan.

Ownership transfer:

1. record current owner and digest;
2. preview the proposed new owner and content;
3. obtain human approval;
4. create backup and migration record;
5. apply in an isolated branch/worktree;
6. run repository-owned validation;
7. record the new baseline.

Leaving RepoOS reverses ownership through a forward proposal; files do not disappear automatically.

## Conflict behavior

Stop on missing baseline, local deletion without recreation policy, local edit conflict, binary content, unsupported encoding, malformed metadata, generated-file edit, or stale plan. Emit a conflict bundle; do not pick “ours” or “theirs” automatically.

## Authority

Schemas control field validity. Component metadata controls adopted paths. The target manifest controls desired adoption. Repository-local instructions and validation commands remain authoritative.
