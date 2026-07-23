# Architecture overview

The authoritative architecture is [VALIDATED_ARCHITECTURE.md](../implementation/VALIDATED_ARCHITECTURE.md). RepoOS separates user-global Codex, the RepoOS control plane, eligibility-gated overlays, and repository-local authority.

The shipped `0.2.0` boundary is a Python CLI, nine strict file schemas, public-safe evidence,
read-only discovery/validation, and transactional apply/backup/validation/rollback restricted to
marked neutral fixtures. Real-repository apply, releases, overlays, downstream adoption, and
external governance are deferred.

Machine behavior is controlled by `src/repoos/` and `schemas/`.
