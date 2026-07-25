# File ownership

The authoritative model is
[File ownership model](../implementation/FILE_OWNERSHIP_MODEL.md).

RepoOS `0.3.0` has two disjoint executable ownership boundaries:

- marked disposable fixtures may update fully managed/generated files and one uniquely marked
  UTF-8 section under update-plan v2;
- an authorized real-worktree `manifest_bootstrap` may create only the absent
  `.repoos/project.yaml` as `adoption_manifest` ownership.

The created manifest becomes repository-owned desired state. Bootstrap does not transfer
ownership of any component it names, and it semantically rejects managed/generated/extension
claims. Repository-owned, extension, local-override, and excluded paths remain preservation
entries in fixture plans and are never written there.

Unknown ownership is repository-owned. Deletion, structured-file sections, multiple section
ownership, sibling writes, overlays, global files, and ordinary real-repository updates are
unsupported.
