import argparse

from tools.agentops.common import load_json, main_check, require_file

parser = argparse.ArgumentParser()
parser.add_argument("--smoke", action="store_true")
args = parser.parse_args()

checks = [
    require_file(".codex/hooks.json"),
    require_file("docs/agentops/hook-registry.md"),
    load_json(".codex/hooks.json"),
]
if args.smoke:
    print("hook smoke mode: config parse and registry presence only")
raise SystemExit(main_check("audit_hooks", checks))
