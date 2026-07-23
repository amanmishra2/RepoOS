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

`0.2.0` supports managed sections only in marked neutral fixtures and only with:

- UTF-8 text;
- exact non-empty start and end markers that each occupy a complete line;
- exactly one section operation per file;
- unique, ordered, nonnested markers;
- byte-for-byte preservation outside the section;
- separate approved hashes for the section and outside bytes;
- missing, duplicate, reversed, nested, overlapping, or locally changed boundary refusal;
- preservation of the existing file mode and LF/CRLF convention.

The source file supplies only the replacement section body. Marker lines stay in the target.
TOML, JSON, YAML (including workflows), binary files, multiple sections in one file, and real
repositories are not section-managed.

## Executable ownership behavior

- `managed_file` and `generated_file` render from one exact source path. Existing file mode is
  preserved; a new file receives the approved source mode.
- `managed_section` rewrites only the approved interior bytes.
- `repository_owned`, `repository_extension`, `local_override`, and `excluded` may appear as
  `preserve` entries for review but never enter backup or write sets.
- `delete` is reserved by the schema for future compatibility and is rejected by the `0.2.0`
  executable engine.
- Unknown ownership, duplicate target ownership, or multiple operations for one target fail closed.

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

Stop on missing baseline, local deletion without recreation policy, local edit conflict,
unsupported section encoding, malformed metadata, generated-file edit, ownership overlap, or
stale plan. Full-file binary content is copied only when it does not require newline conversion;
binary managed sections are unsupported. Emit a conflict bundle; do not pick “ours” or “theirs”
automatically.

## Authority

Schemas control field validity. Component metadata controls adopted paths. The target manifest controls desired adoption. Repository-local instructions and validation commands remain authoritative.
