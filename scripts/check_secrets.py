"""Fail if the committed file inventory contains newly detected secrets."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    baseline = Path(directory) / "scan.json"
    scanner = Path(sys.executable).parent / (
        "detect-secrets.exe" if sys.platform == "win32" else "detect-secrets"
    )
    result = subprocess.run(
        [
            str(scanner),
            "scan",
            "--exclude-files",
            r"(^|[\\/])(\.git|\.venv|\.cache|\.tools|vendor|external)[\\/]|uv\.lock|docs[\\/]evidence[\\/]|tests[\\/]evals[\\/]results\.jsonl|\.secrets\.baseline",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode:
        print(result.stderr)
        raise SystemExit(result.returncode)
    baseline.write_text(result.stdout, encoding="utf-8", newline="\n")
    found = json.loads(result.stdout)["results"]
    allowed = {
        p.replace("\\", "/"): v
        for p, v in json.loads((ROOT / ".secrets.baseline").read_text(encoding="utf-8"))[
            "results"
        ].items()
    }
    failures = []
    for path, entries in found.items():
        known = {
            x["hashed_secret"]
            for x in allowed.get(path.replace("\\", "/"), [])
            if x.get("is_secret") is False
        }
        failures += [
            (path, x["line_number"], x["type"]) for x in entries if x["hashed_secret"] not in known
        ]
    print(json.dumps({"status": "FAIL" if failures else "PASS", "findings": failures}))
    raise SystemExit(bool(failures))
