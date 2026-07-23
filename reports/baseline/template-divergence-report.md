# Generic template divergence report

Date: 2026-07-23

## Archive safety

- SHA-256: `7dc977d8663abe7209ba00f6ca784ecf6c773dbad1ee8191e527b2c8c5e4b486`
- 49 unique regular-file entries
- 42,389 uncompressed bytes
- Integrity test: passed
- Unsafe paths, duplicate names, symlinks, and special files: none
- The portfolio’s non-Git template directory contains a byte-identical ZIP, not an extracted template tree.
- No bundled hook, script, Make target, test, or workflow was executed.

## Architectural decision

The ZIP is a bootstrap/reference artifact, not an upstream control plane. Its README and bootstrap script use whole-tree `rsync`, which can overwrite same-name repository files without version, ownership, baseline, preview, conflict, backup, or rollback metadata. Static copy is obsolete for ongoing synchronization.

## Grouped dispositions

| Content group | Files | Disposition |
|---|---:|---|
| Skills without valid metadata | 7 | Fix and consolidate before reuse |
| Markdown custom agents | 6 | Replace selected roles with TOML agents |
| Codex config | 1 | Replace and split RepoOS policy from Codex settings |
| Hooks | 1 | Replace and fixture-test |
| Issue/PR forms | 5 | Preserve as reviewed bootstrap candidates |
| CI/docs workflows | 2 | Harden and move behind family/capability eligibility |
| No-op issue hygiene | 1 | Remove or implement |
| Repository-local seeds | 6 | Seed only; never centrally overwrite wholesale |
| Planning/spec scaffolds | 12 | Preserve as optional seeds |
| Prompt library | 1 | Deduplicate into skills/docs |
| Makefile | 1 | Keep runtime-specific |
| Bootstrap updater | 1 | Replace with RepoOS planning/apply |
| Tests | 3 | Expand from presence checks to semantic fixtures |
| Workflow tools | 2 | Replace or harden |

## RepoOS comparison

RepoOS is richer than the ZIP and has valid skill front matter, additional registries, memory, eval, and retrospective scaffolding. It must not import the ZIP wholesale. Both nevertheless share obsolete Markdown agents, unsupported config namespaces, outdated hooks, shallow validation, mutable action tags, and distribution assumptions that Phase 2 must repair.

## Reuse boundary

Preserve the safety/evidence principles, issue and PR intake intent, and planning skeletons as reviewed candidates. Keep repository-specific `AGENTS.md`, README, roadmap, issue map, verification commands, and decision history local. Replace static copying and false enforcement.
