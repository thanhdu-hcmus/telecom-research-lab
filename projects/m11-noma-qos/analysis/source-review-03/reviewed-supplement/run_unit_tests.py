"""Run isolated supplemental pytest cases with unique exception-safe receipts."""

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


def run_tests(here=HERE, timeout=600):
    run = here / "unit-runs" / uuid.uuid4().hex
    run.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    before = None
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(here / "test_supplement.py"),
        "-q",
        "-p",
        "no:cacheprovider",
        "--junitxml",
        str(run / "junit.xml"),
        "--basetemp",
        str(run / "tmp"),
    ]
    receipt = dict(
        timestamp=datetime.now(timezone.utc).isoformat(),
        command=command,
        status="FAIL",
        tests_run=None,
        failures=None,
        errors=None,
        skipped=None,
        exit_code=None,
        test_ids=[],
        python=platform.python_version(),
        canonical_execution=False,
        native_validation_on_synthetic_fixtures=False,
        run_directory=run.relative_to(here).as_posix(),
        source_hashes=None,
    )
    stdout = stderr = ""
    try:
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob("*.py")}
        receipt["source_hashes"] = before
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", timeout=timeout
        )
        stdout, stderr = result.stdout, result.stderr
        receipt["exit_code"] = result.returncode
        xml = ElementTree.parse(run / "junit.xml")
        suites = list(xml.getroot().iter("testsuite"))
        counts = {
            k: sum(int(s.get(k, 0)) for s in suites)
            for k in ["tests", "failures", "errors", "skipped"]
        }
        receipt.update(
            tests_run=counts["tests"],
            failures=counts["failures"],
            errors=counts["errors"],
            skipped=counts["skipped"],
            test_ids=[
                c.get("classname", "") + "." + c.get("name", "")
                for c in xml.getroot().iter("testcase")
            ],
        )
        if (
            result.returncode == 0
            and counts["tests"] > 0
            and not any(counts[k] for k in ["failures", "errors", "skipped"])
        ):
            receipt["status"] = "PASS"
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout.decode("utf-8", errors="replace")
            if isinstance(exc.stdout, bytes)
            else exc.stdout or ""
        )
        stderr = (
            exc.stderr.decode("utf-8", errors="replace")
            if isinstance(exc.stderr, bytes)
            else exc.stderr or ""
        )
        receipt.update(exception="TimeoutExpired: " + str(exc), timeout_seconds=timeout)
    except Exception as exc:
        receipt["exception"] = type(exc).__name__ + ": " + str(exc)
    finally:
        (run / "stdout.txt").write_text(stdout, encoding="utf-8", newline="\n")
        (run / "stderr.txt").write_text(stderr, encoding="utf-8", newline="\n")
        try:
            after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob("*.py")}
            unchanged = before is not None and before == after
        except Exception as exc:
            unchanged = False
            receipt["source_recheck_exception"] = type(exc).__name__ + ": " + str(exc)
        receipt.update(
            elapsed_s=time.monotonic() - start,
            source_hashes_unchanged=unchanged,
            evidence={
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in run.iterdir()
                if p.is_file()
            },
        )
        if not unchanged:
            receipt["status"] = "FAIL"
        text = json.dumps(receipt, indent=2, allow_nan=False) + "\n"
        (run / "receipt.json").write_text(text, encoding="utf-8", newline="\n")
        (here / "unit-test-results.json").write_text(text, encoding="utf-8", newline="\n")
        (here / "unit-tests.log").write_text(stdout + stderr, encoding="utf-8", newline="\n")
    return receipt


def main():
    receipt = run_tests()
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


if __name__ == "__main__":
    main()
