# Project manifest reference

Path: `.repoos/project.yaml`
Schema: `schemas/project-manifest.schema.json`

The reviewed manifest declares project ID, desired RepoOS version, optional family/additive overlays, component ownership classes, adoption channel, local overrides, argv-form verification commands, automation permissions, and an optional last-audit evidence reference.

Operational timestamps are not stored in desired state. Unknown fields are rejected. Adding a manifest to a downstream repository is an adoption write and requires explicit approval.
