# Codex schema audit

Date: 2026-07-23
Deep-audit scope: RepoOS and the supplied generic template
Portfolio-wide status: partial; uninspected cells remain unknown

Current contracts were checked against the official [Codex configuration reference](https://developers.openai.com/codex/config-reference/), [hooks guide](https://developers.openai.com/codex/hooks/), [custom agents guide](https://developers.openai.com/codex/subagents/), [skills guide](https://developers.openai.com/codex/skills/), and [rules guide](https://developers.openai.com/codex/rules/).

## RepoOS findings

| Surface | Confirmed evidence | Disposition |
|---|---|---|
| `.codex/config.toml` | TOML parses, but custom `[project]`, `[context]`, `[workflow]`, and `[agentops]` tables are not part of the current project-config schema. A model name is hard-coded. | Replace with the smallest supported project configuration; move RepoOS policy to RepoOS-owned schemas/docs. |
| `.codex/hooks.json` | Uses the older direct event-array shape. The current contract has a top-level `hooks` object and typed command handlers. | Replace and validate against event fixtures. |
| Hook router | Reads no hook payload and always succeeds. The registry’s blocking claim is false. | Remove false claims; implement only hooks with tested behavior. |
| `.codex/agents/*.md` | Ten Markdown role files. Current custom agents are standalone TOML with required `name`, `description`, and `developer_instructions`. | Preserve role intent selectively; convert only nonduplicated, evidence-backed agents. |
| `.agents/skills/*/SKILL.md` | All nine skills contain the required `name` and `description` front matter. | Preserve as candidates; add boundaries and discovery tests before promotion. |
| `.codex/rules/*.rules` | Files contain Markdown-like prose, not executable `prefix_rule(...)` policy. | Move useful policy to documentation or replace with parser-tested rules. |

## Supplied ZIP findings

- All six custom agents are obsolete Markdown definitions.
- All seven skills lack required YAML front matter.
- The config uses unsupported custom surfaces.
- The hooks file uses the obsolete shape and repository-relative commands.
- The workflow audit checks file presence and literal snippets, not semantic validity.

## Installed runtime evidence

- Codex CLI: `0.145.0-alpha.30`
- Python: `3.13.9`
- Git: `2.53.0`
- The installed CLI accepts `codex execpolicy check`.
- `codex doctor` did not reject unknown project config tables in the isolated check. RepoOS therefore needs deterministic strict validation instead of treating CLI acceptance as proof of schema validity.
- The current published schema contains an `agents.max_depth` surface for one agent mode, contrary to an older Phase 1 statement. RepoOS will not emit that key in its initial config; the requirement is **confirmed with modification**, not silently accepted or rejected.

## Initial repair boundary

1. Minimal supported project config.
2. Current hook shape with only honest, fixture-tested behavior.
3. Minimal TOML custom-agent set.
4. Parser-valid executable rules or no active rules.
5. Semantic validation and negative fixtures.
6. No propagation to downstream repositories or user-global locations.

## Portfolio limitation

Only root/nested `AGENTS.md` files were inspected broadly. Other projects’ config, hooks, agents, skills, and rules are explicitly `unknown` until a bounded follow-up audit is authorized and useful.
