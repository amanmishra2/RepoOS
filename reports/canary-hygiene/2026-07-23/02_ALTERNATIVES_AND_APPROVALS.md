# P08 preservation alternatives and approvals

Date: 2026-07-23
Default: no downstream mutation

## Alternatives

| Alternative | Current recommendation | Exact authority required before a later run |
|---|---|---|
| Leave both worktrees untouched and defer | **Selected for this run.** Safest while P08-W2 contains untracked work. | No mutation approval is required. A durable user decision may state: “Defer P08 and preserve P08-W1 and P08-W2 unchanged.” |
| Owner-directed completion or preservation of P08-W2 | Next decision to obtain; do not infer the owner or desired disposition. | First authorize a separate P08-W2 assessment and state whether the 18 untracked file bodies may be inspected. After a bounded plan exists, separately name the exact preservation mutation, approved file set, validation, rollback, and whether a local commit is allowed. Push and pull-request authority remain separate. |
| Later retirement or realignment of P08-W1 | Keep it excluded as a canary base now. Administrative retirement needs no Git change; checkout realignment is optional. | Choose exactly one outcome. Any Git mutation must explicitly name P08-W1, the intended target base, whether the current local branch is retained, whether upstream metadata changes, validation, and recovery. Approval for P08-W1 never authorizes touching P08-W2. |
| Fresh issue-linked canary worktree | Consider only after repository-hygiene and engine gates clear. | Authorize one new P08 worktree and branch from a freshly verified live `main`, name the owning issue and private target in a local-only approval receipt, and limit authority to creation. Manifest planning, apply, commit, push, and pull request remain separate decisions. |

## Required order

1. Preserve the current no-change state.
2. Obtain the P08-W2 owner and disposition.
3. Decide whether P08-W1 is merely excluded or is to be realigned in a separate run.
4. Complete the RepoOS real-repository manifest-bootstrap issue using synthetic repositories.
5. Reaudit every P08 worktree and live GitHub base.
6. Ask separately for authority to create a fresh issue-linked canary worktree.
7. Review a manifest-only plan before considering any downstream content write.

## Approval boundaries

An approval must name the alias, exact action, file or metadata scope, mutation class, validation,
and recovery. Exact private paths and branch details belong in an ignored local approval receipt,
not in committed reports.

None of these approvals combine automatically:

- permission to inspect P08-W2 content;
- permission to modify or commit P08-W2 content;
- permission to switch or alter P08-W1;
- permission to create a new worktree or branch;
- permission to add a manifest;
- permission to run RepoOS against P08;
- permission to commit, push, or open a pull request;
- permission to change GitHub settings or workflows.

P04-A and P04-B are outside every P08 alternative.

## Stop conditions for a later run

Stop before action if a fingerprint, HEAD, worktree count, lock, live default, branch, issue,
pull-request, workflow, access, or overlap field differs; if preservation requires reading content
without authority; or if an operation could overwrite, relocate, or detach P08-W2's untracked
work.
