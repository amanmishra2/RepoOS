# User confirmation required

Date: 2026-07-23

Identity, canonical GitHub repository, active lifecycle, live default branch, current worktree count,
validation commands, and P04-B's shared remote/common-Git relationship are established facts. They
do not need reconfirmation.

The remaining material decisions are:

1. **Sensitivity:** Should P08 be governed as a personal-data-risk/high-sensitivity canary, with
   local-only transaction evidence and no raw learning ingestion?
2. **Candidate:** Should P08 remain the selected provisional canary after repository hygiene and
   the RepoOS engine prerequisite are complete?
3. **Active work:** Who owns P08-W2's untracked implementation work, and what observable event will
   make that worktree inactive? It must remain untouched until then.
4. **Minimal scope:** Do you approve a future first proposal containing only
   `.repoos/project.yaml`, with `project_family: null`, no overlays or managed components, and
   apply/commit/push/external settings denied?
5. **Later mutation boundary:** After a fresh readiness pass, may a separate run create one
   issue-linked P08 branch/worktree and a local manifest-only commit? Push and pull-request
   authority would still require separate approval.

Answering these questions does not authorize cleanup, engine execution, downstream writes, push,
or a pull request in the current run.
