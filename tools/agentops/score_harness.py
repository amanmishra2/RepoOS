from tools.agentops.common import main_check, require_file

checks = [
    require_file("docs/agentops/harness-scorecard.md"),
    require_file("docs/agentops/agent-legibility-scorecard.md"),
]
print(
    "INFO score_harness currently verifies scorecard presence; "
    "customize scoring thresholds per repo."
)
raise SystemExit(main_check("score_harness", checks))
