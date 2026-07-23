import argparse

from tools.agentops.common import main_check, require_file

parser = argparse.ArgumentParser()
parser.add_argument("--smoke", action="store_true")
args = parser.parse_args()

checks = [require_file("docs/agentops/mcp-registry.md")]
if args.smoke:
    print("mcp smoke mode: registry presence only")
raise SystemExit(main_check("audit_mcp", checks))
