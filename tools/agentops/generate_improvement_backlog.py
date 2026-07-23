from tools.agentops.common import main_check, require_file

checks = [require_file("docs/agentops/improvement-backlog.md")]
print(
    "INFO generate_improvement_backlog currently verifies backlog presence; "
    "customize extraction from traces and PRs per repo."
)
raise SystemExit(main_check("generate_improvement_backlog", checks))
