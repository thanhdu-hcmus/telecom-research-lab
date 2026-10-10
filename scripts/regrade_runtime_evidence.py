"""Preserve initial false-negative grades and add verified child-runtime evidence."""

import json
import sys
from pathlib import Path

from lab.evaluation import audit_spawn, grade
from lab.io import load, read_jsonl, save, write_jsonl

ROOT = Path(__file__).resolve().parents[1]
name = sys.argv[1]
folder = ROOT / "tests/evals" / name
index = ROOT / "tests/evals/results.jsonl"
records = read_jsonl(index)
updates = []
for original in [r for r in records if r["evaluation"] == name][-3:]:
    if "no actual child evidence" not in original["grader"].get("reason", ""):
        continue
    workspace = ROOT / ".cache/evals" / original["id"]
    evidence = ROOT / original["raw_evidence"]
    events = [
        json.loads(line)
        for line in (evidence / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.startswith("{")
    ]
    audit = audit_spawn(events, load(folder / "expected.yaml")["role"], workspace)
    save(evidence / "spawn-audit.json", audit)
    updated = {
        **original,
        "initial_grader": original["grader"],
        "runtime_audit": audit,
        "regrade_reason": "CLI omitted child IDs; actual session metadata audited. No model output changed.",
    }
    if audit["verified"] and original["fixture_unchanged"]:
        updated["grader"] = grade(
            folder, json.loads((evidence / "reply.json").read_text(encoding="utf-8")), workspace
        )
    updates.append(updated)
    save(ROOT / "docs/evidence/evals" / (original["id"] + "-audited.json"), updated)
write_jsonl(index, [*records, *updates])
print(
    json.dumps(
        {
            "evaluation": name,
            "audited_trials": len(updates),
            "passing_trials": sum(r["grader"]["passed"] for r in updates),
        }
    )
)
