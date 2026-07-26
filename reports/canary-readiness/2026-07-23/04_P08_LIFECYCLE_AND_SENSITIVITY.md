# P08 lifecycle and sensitivity

Date: 2026-07-23

## Lifecycle

Classification: **active development**

Evidence:

- The private repository is not archived, disabled, or a fork.
- The default branch and workflows changed within the prior two days.
- Ten recent pull requests were merged within eight days.
- There are 48 open issues and one open automation pull request.
- The current default-branch documentation describes an early, pre-release product with a large
  versioned implementation roadmap.
- One valid local worktree contains active untracked implementation files for an open issue.
- Product CI and AgentOps both pass on the observed default-branch commit.
- No release exists.

P08 is not a completed showcase, maintenance-only repository, paused project, or superseded
repository. Near-term implementation and operating-layer churn is expected. A small
infrastructure-only pull request could eventually be isolated, but not while its base and active
worktree disposition remain unresolved.

## Sensitivity

Provisional classification: **personal-data risk**, with future credential and operational-data
exposure possible.

Evidence:

- The repository is private and describes a local-first personal research workflow.
- Future profiles and review records may contain personal travel preferences and history.
- Future providers may require credentials, although live providers are currently disabled.
- Policy requires credentials and authorization headers to remain environment-only.
- Raw provider payload retention fails closed unless purpose, fields, duration, and deletion are
  explicitly approved.
- The tracked default branch contains public/reference datasets but no inspected user profile,
  credential, local database, or runtime output.
- `.gitignore` excludes environment files, key/certificate formats, credential/secret files,
  tokens, local/personal configuration, databases, local data, output, and digests.

No likely secret-bearing file, ignored personal configuration, database, or untracked file body was
opened during this audit.

## RepoOS confidentiality controls

| Question | Assessment |
|---|---|
| Are narrow RepoOS backups safe? | Only for explicitly approved low-sensitivity paths. A manifest-only backup is acceptable if retained under ignored local state and never published. |
| May transaction records include local paths? | Local records may bind paths; committed observations and reports must redact them. |
| Do diff reports require redaction? | Yes. Redact absolute paths, remotes, private SHAs, and private issue/branch details. |
| Is a private GitHub pull request acceptable? | Technically yes after user authorization; the manifest must contain no local mapping or secret. |
| Is local-only planning safer? | Yes. Plan, backup, and rollback evidence should remain local even if a later manifest commit is reviewed privately. |
| May raw evidence enter the learning ledger? | No. Only bounded public-safe aggregates may be proposed, and automatic promotion remains prohibited. |

The private overlay retains `risk_level: unknown` until the user approves the final classification.
