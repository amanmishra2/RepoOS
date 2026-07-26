# Capability matrix

Legend: `fact` is directly observed, `inference` requires confirmation, `unknown` was not inspected, and `blocked` prohibits writes.

| Alias | Git/safety | Instruction evidence | Operating capability | Codex/workflow validation | Initial disposition |
|---|---|---|---|---|---|
| P01 | Dirty; blocked | No root guide discovered | Unknown | Unknown | Inventory only |
| P02 | Dirty; blocked | Root and nested guides | Rich docs routing and local checks | Unknown | Preserve; compare only |
| P03 | Non-Git | No guide | Bootstrap ZIP asset | ZIP audited; runtime files invalid or weak | Reference only |
| P04-A | Dirty; blocked | Root guide | AgentOps map, evidence and offline/live policies | Unknown | Resolve drift; no writes |
| P04-B | Conditional linked worktree | Root guide | Earlier RepoOS experiment | Unknown | Not an isolated canary |
| P05 | Non-Git archive | Nested guides | Historical patterns | Unknown | Exclude |
| P06 | Clean implementation candidate | Root guide and registries | Static AgentOps template, not yet a control plane | Deep audit completed; material repairs required | Implement locally first |
| P07 | Dirty; blocked | Root guide | Exact runtime and external-service constraints | Unknown | Preserve; no writes |
| P08 | Conditional; upstream gone | Root guide | Strong ownership and stop conditions | Unknown | Reconcile base first |
| P09 | Non-Git first level | Nested governed guide | Strong external-mutation safety | Unknown | Classify nested project separately |
| P10 | Non-Git | No guide | Unknown | Unknown | Exclude pending classification |
| P11 | Non-Git | Root guide | Documentation/knowledge-routing pattern | Unknown | Reference only |
| P12 | Non-Git | No root guide | Shared-tooling role inferred | Unknown | Separate global-layer decision |
| P13 | Empty non-Git | None | None | Not applicable | Exclude |

## Reusable candidates

Short instruction entry maps, explicit source hierarchies, minimal context loading, offline/live boundaries, stop conditions, ownership contracts, and evidence-based handoffs recur across multiple repositories. Product scope, external-service restrictions, exact validation commands, database choices, runner labels, and branch conventions remain repository-owned.

## Evidence limitation

Only P06 and the supplied ZIP received a deep Codex/workflow static audit. Other allowlisted operating-layer surfaces remain unknown rather than being inferred from file presence.
