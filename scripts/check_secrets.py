"""Fail if the committed file inventory contains newly detected secrets."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = re.compile(
    r"(^|[\\/])(\.git|\.venv|\.cache|\.tools|vendor|external)[\\/]|uv\.lock|docs[\\/]evidence[\\/]|tests[\\/]evals[\\/]results\.jsonl|\.secrets\.baseline"
)


def check(repo):
    repo = repo.resolve()
    git = ["git", "-c", f"safe.directory={repo.as_posix()}", "-C", str(repo)]
    location = subprocess.run(
        [*git, "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=30
    )
    if location.returncode or Path(location.stdout.strip()).resolve() != repo:
        return {
            "status": "FAIL",
            "error": "Cannot establish the requested repository's Git inventory",
        }
    inventory = subprocess.run([*git, "ls-files", "-z"], capture_output=True, text=True, timeout=30)
    if inventory.returncode or not inventory.stdout:
        return {"status": "FAIL", "error": "Git inventory failed or is empty; no scan accepted"}
    files = sorted(n for n in inventory.stdout.split("\0") if n and not EXCLUDED.search(n))
    if not files:
        return {"status": "FAIL", "error": "Git inventory contains no scannable files"}
    allowed = {
        p.replace("\\", "/"): v
        for p, v in json.loads((repo / ".secrets.baseline").read_text(encoding="utf-8"))[
            "results"
        ].items()
    }
    scanner = Path(sys.executable).parent / (
        "detect-secrets.exe" if sys.platform == "win32" else "detect-secrets"
    )
    failures = []
    # Explicit file arguments avoid the scanner's silent Git discovery failures.
    # Small batches also stay below Windows command-line limits.
    for offset in range(0, len(files), 36):
        batch = files[offset : offset + 36]
        if any(not (repo / n).is_file() for n in batch):
            return {"status": "FAIL", "error": "A tracked scan input is missing"}
        result = subprocess.run(
            [str(scanner), "scan", "--all-files", *batch],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode:
            return {"status": "FAIL", "error": "Secret scanner failed", "exit": result.returncode}
        for path, entries in json.loads(result.stdout)["results"].items():
            known = {
                x["hashed_secret"]
                for x in allowed.get(path.replace("\\", "/"), [])
                if x.get("is_secret") is False
            }
            failures.extend(
                (path, x["line_number"], x["type"])
                for x in entries
                if x["hashed_secret"] not in known
            )
    return {
        "status": "FAIL" if failures else "PASS",
        "files_scanned": len(files),
        "findings": failures,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        report = check(args.root)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        report = {"status": "FAIL", "error": str(error)}
    print(json.dumps(report))
    raise SystemExit(report["status"] != "PASS")
