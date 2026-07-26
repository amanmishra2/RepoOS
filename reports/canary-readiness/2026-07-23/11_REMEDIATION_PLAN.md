# Canary remediation plan

Date: 2026-07-23

## Required before canary

1. Preserve P08-W2's 18 untracked files and obtain an explicit owner disposition. Do not inspect,
   move, delete, reset, clean, or overwrite them automatically.
2. Retire P08-W1 as a candidate base. A future canary must start from a freshly verified live
   `main` in its own issue-linked checkout.
3. Reach a stable common-Git state: every registered P08 worktree must be assessed immediately
   before planning, and the target plus any active sibling risk must satisfy the approved gate.
4. Complete the separate RepoOS real-repository manifest-bootstrap issue using synthetic
   repositories only.
5. Approve the provisional personal-data risk classification and public-learning exclusion.
6. Approve `.repoos/project.yaml` as the sole first-step file, with no family/overlay or managed
   component and all mutation/external permissions denied.
7. Create a P08 issue/context packet that owns only the adoption manifest.
8. Refresh GitHub base, worktree, open-PR overlap, validation, and permission evidence immediately
   before a dry run.

## Recommended before canary

- Require both Product CI and AgentOps to pass as human review policy even though no visible branch
  protection currently enforces them.
- Keep plans, authorization receipts, backups, and transaction details in ignored local state.
- Bind the RepoOS source commit or wheel digest, not only version `0.2.0`.
- Require the first post-adoption plan to be a no-op before proposing any ordinary component.
- Select a second component only after the manifest proposal is reviewed and rollback is proved.

## Optional cleanup

There are no currently prunable P08 records. The old 15-record cleanup question is obsolete.

Optional later hygiene, each separately authorized:

- decide whether the merged primary branch and checkout should be retired or realigned;
- decide whether obsolete local branch refs should be deleted after recovery evidence is reviewed;
- document why the historical worktree registry changed if external evidence becomes available.

These are not prerequisites if a clean, isolated, trustworthy future base can be established
without touching active work.

## Separate repository-hygiene work

The next run should be read-only first:

- reverify the two current P08 records;
- recheck that P08-W2's status has not changed;
- confirm P08-W1 remains fully reachable from live `main`;
- propose preservation-first disposition choices;
- stop for explicit approval before any branch, worktree, upstream, or metadata action.

No P04 cleanup belongs in that run.

## Separate RepoOS-engine work

Implement the bounded issue defined in
[08_P08_TRANSACTION_COMPATIBILITY.md](08_P08_TRANSACTION_COMPATIBILITY.md). It must not target P08.
Only after its full synthetic verification and local commit should a fresh readiness audit
reclassify P08.

## Authorization-dependent work

The following remain separate approvals:

- any downstream branch or worktree creation;
- creating `.repoos/project.yaml`;
- RepoOS execute against a real repository;
- a downstream local commit;
- pushing a branch;
- opening a draft pull request;
- changing branch protection, rulesets, workflows, secrets, runners, or organization settings;
- user-global installation;
- any P04 action.

No approval is implied by this plan.
