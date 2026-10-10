"""Fail-fast deterministic milestone checks; no shell command separators."""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from lab.io import now, save, sha256, within

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--receipt", default="docs/evidence/m5-m10-deterministic.json")
parser.add_argument(
    "--temporary-root", help="Repo-relative temporary/cache directory for restricted Windows hosts"
)
args = parser.parse_args()
receipt_path = within(ROOT, args.receipt)
environment = os.environ.copy()
pytest_options = []
if args.temporary_root:
    temporary_root = within(ROOT, args.temporary_root)
    temporary_root.mkdir(parents=True, exist_ok=True)
    environment.update(TMP=str(temporary_root), TEMP=str(temporary_root))
    pytest_options = ["-o", f"cache_dir={temporary_root / 'pytest-cache'}"]
ruff = Path(sys.executable).parent / ("ruff.exe" if sys.platform == "win32" else "ruff")
commands = [
    [str(ruff), "check", "lab", "tests/unit", "tests/contracts", "tests/physics"],
    [sys.executable, "-m", "pytest", "-q", *pytest_options],
    [sys.executable, "scripts/check_skills.py"],
    [sys.executable, "scripts/check_secrets.py"],
    ["git", "-c", f"safe.directory={ROOT.as_posix()}", "diff", "--check"],
]


def source_hashes():
    return {
        p.relative_to(ROOT).as_posix(): sha256(p)
        for directory in [
            "lab",
            "scripts",
            "tests/unit",
            "tests/contracts",
            "tests/physics",
            "tests/m0",
        ]
        for p in sorted((ROOT / directory).rglob("*.py"))
    }


initial_hashes = source_hashes()
receipt = {"started": now(), "checks": [], "status": "FAIL", "source_hashes": initial_hashes}
for argv in commands:
    tick = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, env=environment)
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
    save(receipt_path, receipt)
    if result.returncode:
        raise SystemExit(result.returncode)
unchanged = initial_hashes == source_hashes()
receipt.update(status="PASS" if unchanged else "FAIL", finished=now(), sources_unchanged=unchanged)
if not unchanged:
    receipt["error"] = "Source files changed during verification; rerun on stable sources"
save(receipt_path, receipt)
raise SystemExit(not unchanged)
