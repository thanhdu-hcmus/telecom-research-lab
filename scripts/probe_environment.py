"""M0 checks with bounded execution and evidence; no paid model/API calls.

Run from a Codex sandbox and a normal host terminal separately. A host PASS
does not establish that the same capability works in an agent sandbox.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def redact(text: str) -> str:
    text = re.sub(r"(?im)^\s*-?\s*Token:\s*.*$", "Token: [redacted]", text)
    text = re.sub(r"(?im)^MATLAB License Number:.*$", "MATLAB License Number: [redacted]", text)
    return re.sub(r"(?:gh[pousr]_|sk-)[A-Za-z0-9_\-]{8,}", "[redacted]", text)


def command(argv: list[str], timeout: int = 30, env: dict | None = None) -> dict:
    started = time.monotonic()
    if env is None:
        env = dict(os.environ)
    tex_bin = ROOT / ".tools" / "texlive" / "bin" / "windows"
    if tex_bin.is_dir():
        env["PATH"] = str(tex_bin) + os.pathsep + env.get("PATH", "")
    try:
        result = subprocess.run(
            argv, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace",
            timeout=timeout, env=env, check=False,
        )
        return {"status": "PASS" if result.returncode == 0 else "FAIL",
                "command": argv, "exit_code": result.returncode,
                "stdout": redact(result.stdout), "stderr": redact(result.stderr),
                "elapsed_s": round(time.monotonic() - started, 3)}
    except subprocess.TimeoutExpired:
        return {"status": "FAIL", "command": argv, "reason": "timeout",
                "timeout_s": timeout}
    except (OSError, ValueError) as exc:
        return {"status": "FAIL", "command": argv, "reason": redact(str(exc))}


def executable(name: str) -> list[str] | None:
    found = shutil.which(name)
    if not found:
        local = ROOT / ".tools" / "texlive" / "bin" / "windows" / (name + ".exe")
        if local.is_file():
            return [str(local)]
        return None
    # Invoke npm CLIs directly through Node, avoiding PowerShell wrapper quoting.
    if name in {"codex", "gemini"}:
        suffix = ("@openai/codex/bin/codex.js" if name == "codex"
                  else "@google/gemini-cli/dist/index.js")
        entry = Path(found).parent / "node_modules" / suffix
        node = shutil.which("node")
        if entry.is_file() and node:
            return [node, str(entry)]
    return [found]


def tool(name: str, args: list[str], timeout: int = 30) -> dict:
    argv = executable(name)
    if not argv:
        return {"status": "MISSING", "reason": f"{name} not found on PATH or in local TeX Live"}
    return command(argv + args, timeout=timeout)


def network_check(name: str, url: str) -> dict:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "telecom-research-lab/M0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read(2_000_000)
            if name == "openalex":
                parsed = json.loads(payload)
                assert isinstance(parsed.get("results"), list) and parsed["results"]
            else:
                parsed = ET.fromstring(payload)
                assert parsed.tag == "{http://www.w3.org/2005/Atom}feed"
                assert parsed.find("{http://www.w3.org/2005/Atom}entry") is not None
            return {"status": "PASS", "url": url, "http_status": response.status,
                    "response_sha256": hashlib.sha256(payload).hexdigest()}
    except (urllib.error.URLError, OSError, AssertionError, ValueError, ET.ParseError) as exc:
        return {"status": "FAIL", "url": url, "reason": redact(str(exc))}


def latex_check() -> dict:
    latexmk = executable("latexmk")
    if not latexmk:
        return {"status": "MISSING", "reason": "latexmk not found"}
    work = ROOT / ".cache" / "latex-smoke"
    work.mkdir(parents=True, exist_ok=True)
    source = work / "smoke.tex"
    source.write_text(
        "\\documentclass{article}\n\\begin{document}\nM0 smoke test.\\end{document}\n",
        encoding="utf-8",
    )
    result = command(latexmk + ["-pdf", "-interaction=nonstopmode", "-halt-on-error",
                                f"-outdir={work}", str(source)], timeout=120)
    pdf = work / "smoke.pdf"
    result["pdf_exists"] = pdf.is_file()
    if result["status"] == "PASS" and not pdf.is_file():
        result["status"] = "FAIL"
        result["reason"] = "compiler returned success without a PDF"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", choices=["sandbox", "host"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--network", action="store_true")
    parser.add_argument("--matlab", action="store_true")
    parser.add_argument("--latex", action="store_true")
    args = parser.parse_args()
    checks = {}
    version_jobs = {
        "python": [sys.executable, "--version"],
        "uv": ["uv", "--version"], "git": ["git", "--version"],
        "gh": ["gh", "--version"], "codex": ["codex", "--version"],
        "latexmk": ["latexmk", "-version"], "pdflatex": ["pdflatex", "--version"],
        "gemini": ["gemini", "--version"],
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(tool, name, argv[1:]): name for name, argv in version_jobs.items()}
        for future in concurrent.futures.as_completed(jobs):
            checks[jobs[future] + "_version"] = future.result()
    checks["python_smoke"] = command([sys.executable, "-c", "assert sum([1,2,3]) == 6; print('PYTHON_SMOKE_PASS')"])
    checks["codex_auth"] = tool("codex", ["login", "status"])
    checks["github_auth"] = tool("gh", ["auth", "status"])
    checks["codex_help"] = tool("codex", ["--help"])
    checks["codex_exec_help"] = tool("codex", ["exec", "--help"])
    if args.network:
        checks["openalex"] = network_check("openalex", "https://api.openalex.org/works?per-page=1")
        checks["arxiv"] = network_check("arxiv", "https://export.arxiv.org/api/query?search_query=all:RIS&max_results=1")
    if args.matlab:
        matlab = executable("matlab")
        if matlab:
            checks["matlab_batch"] = command(matlab + ["-wait", "-batch",
                "disp(1); fprintf('MATLAB_RELEASE=%s\\n',version('-release')); ver; fprintf('MATLAB_SMOKE_PASS\\n');"], timeout=120)
            if "MATLAB_SMOKE_PASS" not in checks["matlab_batch"].get("stdout", ""):
                checks["matlab_batch"]["status"] = "FAIL"
        else:
            checks["matlab_batch"] = {"status": "MISSING"}
    if args.latex:
        checks["latex_compile"] = latex_check()
    output = {"recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "context": args.context, "platform": platform.platform(),
              "root": str(ROOT), "checks": checks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value["status"] for key, value in checks.items()}, indent=2))
    required = ["python_smoke", "codex_auth"]
    required += ["openalex", "arxiv"] if args.network else []
    required += ["matlab_batch"] if args.matlab else []
    required += ["latex_compile"] if args.latex else []
    return 0 if all(checks[key]["status"] == "PASS" for key in required) else 1


if __name__ == "__main__":
    raise SystemExit(main())
