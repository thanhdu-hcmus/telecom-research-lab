"""Repeatable local checks without destroying the historical M0 report."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from lab.io import library, load, now, save
from lab.models import MODELS


def check(repo: Path, full: bool = False) -> dict:
    checks = {"python": {"status": "PASS", "version": sys.version.split()[0]}}
    for name in ["uv", "git", "gh", "codex"]:
        found = shutil.which(name) or shutil.which(name + ".ps1")
        checks[name] = {"status": "PASS" if found else "FAIL", "path": found}
    latex_bin = repo / load(repo / "config/lab.config.yaml")["latex_bin"]
    latex = shutil.which("latexmk") or next(iter(latex_bin.glob("latexmk*")), None)
    checks["latexmk"] = {"status": "PASS" if latex else "FAIL", "path": str(latex)}
    config = tomllib.loads((repo / ".codex/config.toml").read_text(encoding="utf-8"))
    mcp = Path(config["mcp_servers"]["matlab"]["command"])
    checks["matlab_mcp"] = {"status": "PASS" if mcp.exists() else "FAIL", "path": str(mcp)}
    try:
        lib = library(repo)
        lib.mkdir(parents=True, exist_ok=True)
        probe = lib / ".lab-write-probe"
        probe.write_text("probe", encoding="utf-8", newline="\n")
        probe.unlink()
        checks["library"] = {"status": "PASS", "path": str(lib)}
    except OSError as error:
        checks["library"] = {"status": "FAIL", "reason": str(error)}
    for name, model in MODELS.items():
        schema = load(repo / f"schemas/{name}.schema.json")
        checks[f"schema:{name}"] = {
            "status": "PASS" if schema == model.model_json_schema(by_alias=True) else "FAIL"
        }
    evidence = repo / "docs/evidence"
    checks["runtime_workarounds"] = {
        "status": "PASS",
        "evidence": str(evidence),
        "note": "M0 approved: MATLAB MCP; bounded host network; separate reviewer sessions. This is historical evidence, not a fresh network check.",
    }
    if full:
        # Use the established M0 probes; no shell=True and no credentials in output.
        command = [
            sys.executable,
            str(repo / "scripts/probe_environment.py"),
            "--context",
            "host",
            "--output",
            str(repo / "docs/evidence/doctor-full.json"),
            "--network",
            "--latex",
        ]
        result = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=240)
        checks["full_probe"] = {
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "exit_code": result.returncode,
        }
    report = {
        "timestamp": now(),
        "status": "PASS" if all(x["status"] == "PASS" for x in checks.values()) else "FAIL",
        "checks": checks,
    }
    save(repo / "docs/evidence/doctor-latest.json", report)
    (repo / "docs/doctor-report.md").write_text(
        "# Doctor\n\n```json\n" + json.dumps(report, indent=2) + "\n```\n",
        encoding="utf-8",
        newline="\n",
    )
    return report
