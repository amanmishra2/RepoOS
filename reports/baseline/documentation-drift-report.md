# Documentation drift report

Date: 2026-07-23

## RepoOS confirmed drift

| Surface | Drift | Disposition |
|---|---|---|
| `README.md` | Defines RepoOS as a generic copy template. | Replace with the implemented control-plane identity. |
| `MEMORY.md` | Records “generic template” as durable identity. | Update only with verified shipped behavior. |
| `docs/agentops/github-actions-runners.md` | Makes a personal Mac self-hosted runner the default. | Replace with GitHub-hosted default and gated future self-hosting. |
| `docs/verification.md` | Presents presence checks as verification and repeats the runner assumption. | Tie claims to real commands and negative fixtures. |
| `docs/agentops/hook-registry.md` | Calls a no-op router a blocking guard. | Remove the false claim; link to tested fixtures. |
| `docs/agentops/folder-structure-map.md` | Lists directories that do not exist and omits the coming package/schemas/tests. | Generate or validate against tracked structure. |
| `docs/issue-map.md` | Contains template/TBD rows rather than the Phase 2 dependency graph. | Replace with the validated local backlog. |
| `docs/ROADMAP.md` | Describes the obsolete static-template roadmap. | Replace with dependency-ordered RepoOS rollout. |
| `AGENTS.md` | Defaults completion to commit, push, and PR. | Require explicit authorization for external writes. |
| `docs/prompt-library.md` | Duplicates workflow guidance already represented by skills. | Consolidate after trigger/output review. |

## Cross-worktree drift

P04-A and P04-B share one Git common directory but contain materially different product-scope instructions: the primary working tree includes a broader offer scope while the linked RepoOS branch describes a narrower banking scope. This must be resolved locally before either branch can be a canary.

## Historical/derived documentation

P02, archived P05 content, and P11 use similar knowledge-routing language. P05 is an archive and P11 is non-Git, so similarity is not evidence that either is authoritative or globally reusable.

## Authority gaps

Several non-Git or unclassified roots lack a root `AGENTS.md`, while one has a nested governed project. This is not automatically a defect; lifecycle and intended entrypoint must be confirmed before adding instructions.

## Unknowns

Portfolio-wide README/index accuracy, broken links, stale issue maps, duplicate plans, memory drift, and source-of-truth declarations remain unvalidated outside RepoOS.
