"""Save separate corrected grades; never edit original model replies or failures."""

import argparse
import json
from pathlib import Path
from lab.evaluation import grade
from lab.io import load, save, sha256, read_jsonl, write_jsonl, now

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("name")
parser.add_argument("--reason", required=True)
args = parser.parse_args()
reports = []
for file in sorted((ROOT / "docs/evidence/evals").glob(args.name + "-*.json")):
    old = load(file)
    if old.get("regrade_of"):
        continue
    raw = ROOT / old["raw_evidence"] / "reply.json"
    if not raw.exists():
        continue
    before = sha256(raw)
    reply = json.loads(raw.read_text(encoding="utf-8"))
    workspace = ROOT / ".cache/evals" / old["id"]
    result = grade(ROOT / "tests/evals" / args.name, reply, workspace)
    assert sha256(raw) == before
    updated = {
        **old,
        "id": old["id"] + "-rechecked",
        "timestamp": now(),
        "regrade_of": old["id"],
        "original_grader": old["grader"],
        "grader": result,
        "correction_reason": args.reason,
        "unchanged_reply_sha256": before,
        "grader_library_sha256": sha256(ROOT / "lab/eval_graders.py"),
    }
    save(ROOT / "docs/evidence/evals" / (updated["id"] + ".json"), updated)
    reports.append(updated)
index = ROOT / "tests/evals/results.jsonl"
from filelock import FileLock

with FileLock(str(ROOT / ".cache/evals-index.lock"), timeout=15):
    write_jsonl(index, [*read_jsonl(index), *reports])
print(
    json.dumps(
        {
            "evaluation": args.name,
            "rechecked": len(reports),
            "passed": sum(r["grader"]["passed"] for r in reports),
            "reason": args.reason,
        }
    )
)
if args.name == "modeler-derivation":
    passed = next((r for r in reports if r["grader"]["passed"]), None)
    if passed:
        output = load(ROOT / passed["raw_evidence"] / "reply.json")
        save(
            ROOT / "tests/fixtures/modeler-derived-outage.yaml",
            {
                "trial": passed["regrade_of"],
                "reply_sha256": passed["unchanged_reply_sha256"],
                "reference": "https://arxiv.org/pdf/1406.1516",
                "regime": "Two ordered iid Exp(1) gains, perfect SIC, no spatial path loss",
                "samples": output["samples"],
            },
        )
        fixture = ROOT / "tests/fixtures/modeler-derived-outage.yaml"
        lines = fixture.read_text(encoding="utf-8").splitlines()
        fixture.write_text(
            "\n".join(
                line + " # pragma: allowlist secret" if line.startswith("reply_sha256:") else line
                for line in lines
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
