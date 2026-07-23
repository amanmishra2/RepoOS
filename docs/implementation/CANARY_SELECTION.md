# Canary selection

Status: readiness refreshed 2026-07-23; P08 remains provisional and blocked

## Historical foundation assessment

The Phase 2 foundation inventory selected P08 provisionally because its primary checkout was clean
and independent while P04-B shared P04-A's dirty common Git directory. That historical snapshot
recorded 16 P08 worktree registrations, 15 prunable, and left identity, commands, family,
sensitivity, ownership, and remote authority unresolved.

The historical evidence is preserved in
[portfolio-inventory.md](../../reports/baseline/portfolio-inventory.md). Its P08 worktree count is
stale and must not be used as current state.

## Refreshed assessment

The detailed public-safe packet is
[canary-readiness/2026-07-23](../../reports/canary-readiness/2026-07-23/README.md).
Exact mappings remain only in the ignored private overlay.

| Alias | Confirmed positive evidence | Current blockers | Decision |
|---|---|---|---|
| P08 | Identity, private GitHub repository, live `main`, active lifecycle, standalone Python CLI/application family, exact offline gates, proposed ownership boundary, two current worktrees and zero prunable records | Primary checkout is 29 commits behind after its branch merged; second worktree has 18 untracked implementation files; sensitivity and manifest ownership need approval; real-repository manifest bootstrap is unsupported | Provisional rank 1; `blocked` |
| P04-B | Exact remote verified; target worktree clean; GitHub and validation surface identifiable | Shares P04-A's dirty common Git directory; 67 commits behind live `main` and seven behind its remote branch; 64 shared worktree records with 10 prunable; instruction drift; no independent rollback boundary | `unsuitable_as_first_canary` |
| P04-A | Active repository and canonical common-Git owner | Three tracked and 54 untracked changes; large shared worktree registry | Block |
| Other historical candidates | Baseline evidence retained | Not refreshed in this bounded audit | No new eligibility |

The earlier “upstream gone” finding is now resolved: P08's repository and remote are valid; only the
primary local issue branch's remote ref is gone after its pull request merged. It should not be
repaired or reused as the canary base.

## Selection

P08 remains the only provisional candidate. This is a relative ranking, not approval. A real canary
is not authorized.

P08 must first complete:

1. preservation-first repository hygiene for its active secondary worktree;
2. a fresh authoritative base assessment;
3. the separate RepoOS real-repository manifest-bootstrap enhancement;
4. user approval of sensitivity, manifest ownership, and the one-file scope.

The current first-step proposal remains manifest-only. No ordinary managed or generated component
is selected. A second bounded component may be considered only after the manifest proposal,
repository-owned validation, no-op repeat, and forward rollback all succeed.

## Human decisions

Only the unresolved decisions in
[12_USER_CONFIRMATION_REQUIRED.md](../../reports/canary-readiness/2026-07-23/12_USER_CONFIRMATION_REQUIRED.md)
remain. Identity, canonical remote, lifecycle, default branch, validation commands, family
classification, and current worktree count are evidence-backed facts.

## Stop decision

Downstream mutation remains blocked. Do not prune, repair, create a canary worktree, add a manifest,
execute RepoOS, commit downstream, push, or open a pull request under this assessment.
