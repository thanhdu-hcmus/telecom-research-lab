"""Inspect only the named fixture child sessions for actual baseline execution."""

import json
import re
from pathlib import Path
from lab.io import load, save, now

ROOT = Path(__file__).resolve().parents[1]
reports = []
for evidence in (ROOT / "docs/evidence/raw/evals").glob("repro-small-*"):
    audit = load(evidence / "spawn-audit.json")
    children = {c["thread_id"] for c in audit["children"]}
    records = []
    for session in (Path.home() / ".codex/sessions").glob(
        f"{now()[:4]}/{now()[5:7]}/{now()[8:10]}/*.jsonl"
    ):
        with session.open(encoding="utf-8") as stream:
            first = json.loads(stream.readline())
            if first.get("payload", {}).get("id") not in children:
                continue
            pending = {}
            for line in stream:
                event = json.loads(line)
                p = event.get("payload", {})
                if event.get("type") != "response_item":
                    continue
                if p.get("type") in {"function_call", "custom_tool_call"}:
                    args = str(p.get("arguments") or p.get("input") or "")
                    if "baseline.py" in args and re.search(
                        r"python(?:\.exe)?['\"]?\s+(?:[-\w.]+\s+)*['\"]?(?:\.\\|\./)?baseline\.py",
                        args,
                        re.I,
                    ):
                        pending[p["call_id"]] = p.get("name")
                if (
                    p.get("type") in {"function_call_output", "custom_tool_call_output"}
                    and p.get("call_id") in pending
                ):
                    output = str(p.get("output", ""))
                    zero = bool(
                        re.search(
                            r"(?:exit_code[\"\\]*\s*:\s*0|Exit code:\s*0|Process exited with code 0)",
                            output,
                            re.I,
                        )
                    )
                    records.append(
                        {
                            "tool": pending[p["call_id"]],
                            "exit_zero": zero,
                            "printed_curve": "outage" in output and "rho" in output,
                        }
                    )
    passed = any(r["exit_zero"] and r["printed_curve"] for r in records)
    reports.append(
        {"id": evidence.name, "execution_records": records, "actual_execution_verified": passed}
    )
result = {
    "status": "PASS"
    if len(reports) >= 3 and all(r["actual_execution_verified"] for r in reports)
    else "FAIL",
    "scope": "Only child sessions matching previously audited reproduction fixture IDs; no unrelated session content copied",
    "trials": reports,
}
save(ROOT / "docs/evidence/m6-execution-audit.json", result)
print(json.dumps(result))
raise SystemExit(result["status"] != "PASS")
