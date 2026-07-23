# Architecture overview

The authoritative architecture is [VALIDATED_ARCHITECTURE.md](../implementation/VALIDATED_ARCHITECTURE.md). RepoOS separates user-global Codex, the RepoOS control plane, eligibility-gated overlays, and repository-local authority.

The shipped `0.1.0` boundary is a Python CLI, strict file schemas, public-safe evidence, read-only discovery/validation, and fixture-only planning with dry-run apply revalidation. Real apply, releases, overlays, downstream adoption, and external governance are deferred.

Machine behavior is controlled by `src/repoos/` and `schemas/`.
