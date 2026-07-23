# Project registry reference

Path: `registry/projects.yaml`
Schema: `schemas/project-registry.schema.json`

The committed registry is `public_safe`. It records RepoOS openly and uses a separately ignored `.repoos/local/projects.private.yaml` overlay for any private path/repository mappings.

Required project fields include ID, path, repository, family, overlays, managed/excluded components, risk, automation policy, adoption state, block state, and last audit. The discovery command proposes evidence but never modifies the registry.
