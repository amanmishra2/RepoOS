from tools.agentops.common import ROOT, main_check

markers = ["DEPRECATED", "STALE", "TODO"]
findings = []
for path in ROOT.rglob("*.md"):
    if ".git" in path.parts:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    for marker in markers:
        if marker in text:
            findings.append((path, marker))

for path, marker in findings:
    print(f"WARN {path.relative_to(ROOT)} contains {marker}")

raise SystemExit(main_check("find_stale_docs", [True]))
