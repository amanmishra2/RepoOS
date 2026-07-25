# File ownership model

Status: authoritative for RepoOS `0.3.0`

## Ownership classes

| Class | Owner | RepoOS behavior |
|---|---|---|
| `managed_file` | RepoOS component | Fixture-only full-file render under update-plan v2 |
| `generated_file` | RepoOS generator | Fixture-only deterministic render with exact inputs |
| `managed_section` | RepoOS component | Fixture-only uniquely bounded UTF-8 interior rewrite |
| `adoption_manifest` | Target repository | Real-worktree bootstrap may create one absent manifest; never replace |
| `repository_owned` | Target repository | Preserve; never overwrite through fixture update |
| `repository_extension` | Target repository within an extension point | Preserve exactly; validate boundary only |
| `local_override` | Target repository with named governance | Preserve; surface review; never normalize |
| `excluded` | Target repository | Do not inspect beyond needed metadata or mutate |

Unknown and unadopted paths are `repository_owned`.

## Manifest bootstrap

`adoption_manifest` is a one-transaction creation ownership class, not continuing RepoOS
management. It permits exactly `.repoos/project.yaml` when absent. The installed file becomes
repository-owned desired state. The bootstrap plan must declare one create, zero edits, zero
deletes, mode `0644`, exact bytes, and a fixed safety contract.

The plan may create `.repoos` if absent. Rollback may remove it only when the transaction created
it and it remains empty. A pre-existing directory and all unrelated entries are preserved.
Symlinked destinations/parents, traversal, ignored destinations, submodules, and bare/detached
targets are refused.

The first manifest may document repository-owned/excluded component identifiers, but managed,
generated, and extension lists must be empty. Thus bootstrap records governance without acquiring
additional file ownership.

## Fixture managed sections

Update-plan v2 supports managed sections only in marked disposable fixtures and only with:

- UTF-8 text and exact non-empty whole-line start/end markers;
- exactly one section operation per file;
- unique, ordered, nonnested markers;
- separately approved interior/outside hashes;
- byte-for-byte preservation outside the section;
- existing mode and LF/CRLF preservation.

TOML, JSON, YAML, workflows, binary files, multiple sections, and real repositories are never
section-managed.

## Path and worktree safety

- Every writable component has one explicit portable relative path; mutation globs are prohibited.
- Resolved paths must remain beneath the canonical target root.
- Symlink components and parent escapes are rejected.
- `.git`, dependency, build, cache, worktree, database, secret, log, and generated-data paths are
  excluded by default.
- A common Git directory is the lock identity, but each worktree has independent target state.
- Sibling paths are never writable; dirty siblings are protected rather than normalized.

## Adoption and transfer

Similarity and manifest creation are not ownership transfer. Any later adoption requires explicit
component identity, baseline, version, ownership, target, reviewed plan, backup, approval, isolated
worktree, repository validation, and a recorded new baseline. No such real-repository component
update is implemented.

Leaving RepoOS uses a forward repository proposal; files do not disappear automatically.

## Conflict behavior and authority

Stop on existing manifest, missing baseline, local edit/deletion conflict, malformed metadata,
generated-file edit, ownership overlap, unsafe path, or stale plan. Do not select “ours” or
“theirs” automatically.

Schemas control field validity; executable semantic gates narrow what valid documents may do.
Target manifests declare desired governance, and repository-local instructions/validation remain
authoritative.
