# RepoOS agent map

This file is an entry map. Put detailed policy in the linked sources.

## Read first

- `README.md`
- `MEMORY.md`
- `docs/implementation/VALIDATED_ARCHITECTURE.md`
- `docs/implementation/VALIDATED_MIGRATION_PLAN.md`
- `docs/implementation/VALIDATED_ISSUE_BACKLOG.md`
- `docs/implementation/AUTHORIZATION_REQUIRED.md`
- `policies/security/COMMAND_SAFETY.md`
- `docs/reference/CLI.md`
- `docs/verification.md`

Read a nested `AGENTS.md` before changing files in its scope.

## Working rules

- Begin with a read-only Git preflight and preserve unrelated changes.
- Use an ROS-linked branch or worktree; keep shared central files under one writer.
- Prefer small, reviewable, issue-bounded changes and neutral fixtures.
- Do not inspect secret-bearing, database, log, generated-data, or unrelated private content.
- Run proportionate verification before claiming completion.
- Update the authoritative document when code, schemas, structure, tools, hooks, runners, or workflows change.
- Keep private portfolio identifiers out of committed reports and fixtures.
- Treat plans and AI recommendations as proposals, never approval.

## Mutation boundary

RepoOS-local source, docs, schemas, and neutral fixtures may be changed for an approved RepoOS task. Downstream repositories, user-global Codex files, GitHub settings, releases, pushes, PRs, merges, and runners require explicit authority for the exact action and target.

Never stash, reset, clean, prune, or switch a dirty repository to make it eligible.

## CI assumption

Initial GitHub Actions use GitHub-hosted ephemeral runners. Self-hosted runners are deferred and authorization-dependent. See `docs/agentops/github-actions-runners.md`.

## Source-of-truth hierarchy

1. Shipped code and semantic tests
2. JSON Schemas and machine-readable contracts
3. `docs/implementation/` validated decisions
4. `docs/architecture/`, `docs/operations/`, and `docs/reference/`
5. AgentOps registries
6. `MEMORY.md`
7. `AGENTS.md`
8. Historical plans, prompt libraries, and chat context

If sources conflict, preserve the higher authority and repair or mark the lower source.

## Done means

- Requested behavior and only that behavior changed.
- Tests, lint, formatting, types, build, CLI smoke checks, and applicable schema checks are recorded.
- Negative fixtures prove material safety claims.
- Documentation describes shipped behavior and limitations.
- Dirty/external/user-global safety is confirmed.
- Commit, push, issue, PR, release, merge, and GitHub setting changes happen only when explicitly authorized.
