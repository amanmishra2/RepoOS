# Architecture overview

The authoritative architecture is [VALIDATED_ARCHITECTURE.md](../implementation/VALIDATED_ARCHITECTURE.md). RepoOS separates user-global Codex, the RepoOS control plane, eligibility-gated overlays, and repository-local authority.

The shipped `0.3.0` boundary is a Python CLI, 11 strict schemas, public-safe evidence, read-only
discovery/validation, marked-fixture transactions, and one authorization-bound real-worktree
operation that creates an absent `.repoos/project.yaml`. Every other real-repository write,
releases, overlays, downstream adoption, and external governance remain deferred.

Machine behavior is controlled by `src/repoos/` and `schemas/`.
