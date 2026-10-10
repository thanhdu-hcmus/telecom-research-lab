"""Fail-fast deterministic milestone checks; no shell command separators."""

import subprocess
import sys
import time
import re
from pathlib import Path

from lab.io import save, sha256, now

ROOT = Path(__file__).resolve().parents[1]
ruff = Path(sys.executable).parent / ("ruff.exe" if sys.platform == "win32" else "ruff")
commands = [
    [str(ruff), "check", "lab", "tests/unit", "tests/contracts", "tests/physics"],
    [sys.executable, "-m", "pytest", "-q"],
    [sys.executable, "scripts/check_skills.py"],
    [sys.executable, "scripts/check_secrets.py"],
    ["git", "-c", f"safe.directory={ROOT.as_posix()}", "diff", "--check"],
]
receipt = {"started": now(), "checks": [], "status": "FAIL"}
for argv in commands:
    tick = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    receipt["checks"].append(
        {
            "command": argv,
            "exit": result.returncode,
            "elapsed_s": time.monotonic() - tick,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    )
    if "pytest" in argv:
        match = re.search(r"(\d+) passed", result.stdout)
        receipt["tests_passed"] = int(match[1]) if match else 0
    save(ROOT / "docs/evidence/m5-m10-deterministic.json", receipt)
    if result.returncode:
        raise SystemExit(result.returncode)
receipt.update(
    status="PASS",
    finished=now(),
    source_hashes={
        p.relative_to(ROOT).as_posix(): sha256(p)
        for directory in ["lab", "tests/unit", "tests/contracts", "tests/physics"]
        for p in sorted((ROOT / directory).rglob("*.py"))
    },
)
save(ROOT / "docs/evidence/m5-m10-deterministic.json", receipt)
