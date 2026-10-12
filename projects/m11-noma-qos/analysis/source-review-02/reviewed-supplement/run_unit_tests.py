"""Run isolated supplemental pytest cases with unique retained receipts."""

import hashlib
import json
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
run = HERE / "unit-runs" / uuid.uuid4().hex
run.mkdir(parents=True)
start = time.monotonic()
before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob("*.py")}
command = [
    sys.executable,
    "-m",
    "pytest",
    str(HERE / "test_supplement.py"),
    "-q",
    "-p",
    "no:cacheprovider",
    "--junitxml",
    str(run / "junit.xml"),
    "--basetemp",
    str(run / "tmp"),
]
result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=600)
(run / "stdout.txt").write_text(result.stdout, encoding="utf-8", newline="\n")
(run / "stderr.txt").write_text(result.stderr, encoding="utf-8", newline="\n")
xml = ElementTree.parse(run / "junit.xml")
suites = list(xml.getroot().iter("testsuite"))
counts = {
    k: sum(int(s.get(k, 0)) for s in suites) for k in ["tests", "failures", "errors", "skipped"]
}
after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob("*.py")}
receipt = dict(
    timestamp=datetime.now(timezone.utc).isoformat(),
    command=command,
    status="PASS"
    if result.returncode == 0
    and counts["tests"] > 0
    and not any(counts[k] for k in ["failures", "errors", "skipped"])
    and before == after
    else "FAIL",
    tests_run=counts["tests"],
    failures=counts["failures"],
    errors=counts["errors"],
    skipped=counts["skipped"],
    exit_code=result.returncode,
    test_ids=[
        c.get("classname", "") + "." + c.get("name", "") for c in xml.getroot().iter("testcase")
    ],
    elapsed_s=time.monotonic() - start,
    python=platform.python_version(),
    canonical_execution=False,
    native_validation_on_synthetic_fixtures=False,
    run_directory=run.relative_to(HERE).as_posix(),
    source_hashes=before,
    source_hashes_unchanged=before == after,
    evidence={
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in run.iterdir() if p.is_file()
    },
)
(run / "receipt.json").write_text(
    json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
)
(HERE / "unit-test-results.json").write_text(
    json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
)
# Backward-compatible current log; immutable complete output remains in unique unit-runs.
(HERE / "unit-tests.log").write_text(result.stdout + result.stderr, encoding="utf-8", newline="\n")
print(
    json.dumps(
        {
            k: receipt[k]
            for k in [
                "status",
                "tests_run",
                "failures",
                "errors",
                "skipped",
                "elapsed_s",
                "run_directory",
                "source_hashes_unchanged",
            ]
        }
    )
)
raise SystemExit(0 if receipt["status"] == "PASS" else 1)
