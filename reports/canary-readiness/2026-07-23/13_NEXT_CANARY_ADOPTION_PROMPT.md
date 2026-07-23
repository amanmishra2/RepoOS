# Next prompt: P08 read-only hygiene and gate preparation

Outcome: executed 2026-07-23 without downstream change. P08 remains blocked.
Execution record:
[canary-hygiene/2026-07-23](../../canary-hygiene/2026-07-23/README.md).

```text
# P08 Read-Only Canary Hygiene and Gate Preparation

Continue in the current RepoOS checkout. Resolve P08 only through the ignored,
schema-valid `.repoos/local/projects.private.yaml` overlay. Use P08, P04-A, and P04-B
aliases in every committed artifact. Do not repeat private paths, repository names,
remotes, or private SHAs in reports.

Authority:

- reports/canary-readiness/2026-07-23/
- docs/implementation/VALIDATED_ARCHITECTURE.md
- docs/implementation/FILE_OWNERSHIP_MODEL.md
- docs/implementation/CANARY_SELECTION.md
- docs/implementation/AUTHORIZATION_REQUIRED.md
- the target repository's current instructions

Objective:

Produce a preservation-first P08 hygiene decision packet. Do not adopt P08 and do not
implement the RepoOS real-repository engine enhancement in this run.

Required sequence:

1. Verify RepoOS root, branch, HEAD, version, clean status, and the expected audit commit.
2. Validate the private overlay and confirm it remains ignored and untracked.
3. Recheck P08 identity through the overlay, local Git, and read-only GitHub access.
4. Require exactly the two authoritative registered P08 worktrees described in the
   2026-07-23 packet. If the count, HEAD, status fingerprint, path existence, lock state,
   or remote/PR state changed, stop and report the delta before proposing action.
5. For P08-W1, confirm that its commit remains reachable from live `main`, its pull
   request remains merged, and its remote branch remains absent.
6. For P08-W2, inspect Git metadata and status only. Do not open untracked file bodies.
   Confirm the owning issue, remote-branch/PR state, tracked-change count, untracked-entry
   count, and unique-commit risk.
7. Re-run `git worktree prune --dry-run --verbose` only. Do not prune.
8. Reconfirm live `main`, open PR overlap, workflow conclusions, and repository access.
9. Draft preservation-first alternatives for:
   - leaving both worktrees untouched and deferring the canary;
   - owner-directed completion/preservation of P08-W2 in a separate run;
   - later retirement or realignment of P08-W1 after explicit approval;
   - creating a fresh issue-linked canary worktree only after all blockers clear.
10. State the exact approval required for each alternative. Recommend no automatic
    cleanup and make no branch/upstream repair.
11. Confirm whether P08 can become `eligible_after_repository_hygiene`. Do not call it
    engine-ready; the separate manifest-bootstrap issue must still complete.

Allowed writes:

- a new date-stamped RepoOS readiness/hygiene report;
- evidence-supported updates under `docs/implementation/`;
- one focused local RepoOS commit after validation.

Prohibited:

- downstream file writes;
- worktree create/remove/prune/repair;
- branch create/delete/switch/reset/rebase/merge;
- remote or upstream changes;
- reading likely secret-bearing files or P08-W2 untracked bodies;
- GitHub mutation;
- user-global changes;
- P04 mutation;
- push or pull request.

Stop if P08 changes during the audit, unique commits cannot be assessed without reading
private content, identity diverges, or any action would risk the untracked work.

Validate the report for private names/paths, run applicable RepoOS docs checks and
`git diff --check`, recheck every downstream HEAD/status, then create one local commit.
Do not push.
```
