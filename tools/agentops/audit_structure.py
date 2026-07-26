from tools.agentops.common import main_check, require_any, require_file

checks = [
    require_file("docs/agentops/folder-structure-map.md"),
    require_any([".codex/config.toml"], "Codex config"),
    require_any([".agents/skills/doc-gardening/SKILL.md"], "repo skills"),
]
raise SystemExit(main_check("audit_structure", checks))
