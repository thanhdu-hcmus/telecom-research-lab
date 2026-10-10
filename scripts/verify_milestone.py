"""Fail-fast deterministic milestone checks; no shell command separators."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ruff = Path(sys.executable).parent / ("ruff.exe" if sys.platform == "win32" else "ruff")
commands = [[str(ruff), "check", "lab", "tests/unit", "tests/contracts", "tests/physics"],
            [sys.executable, "-m", "pytest", "-q"],
            [sys.executable, "scripts/check_skills.py"],
            [sys.executable, "scripts/check_secrets.py"],
            ["git", "diff", "--check"]]
for argv in commands:
    subprocess.run(argv, cwd=ROOT, check=True)
