"""Validate project skills using the Skill Creator validator plus local links."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
validator = Path("C:/Users/ADMIN/.codex/skills/.system/skill-creator/scripts/quick_validate.py")
failures = []
for path in (ROOT / ".agents/skills").glob("*/SKILL.md"):
    if validator.exists():
        result = subprocess.run(
            [sys.executable, str(validator), str(path.parent)], capture_output=True, text=True
        )
        if result.returncode:
            failures.append({"skill": path.parent.name, "error": result.stdout + result.stderr})
    for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        if not link.startswith(("https:", "http:", "#")) and not (path.parent / link).exists():
            failures.append({"skill": path.parent.name, "missing_link": link})
print({"skills": len(list((ROOT / ".agents/skills").glob("*/SKILL.md"))), "failures": failures})
raise SystemExit(bool(failures))
