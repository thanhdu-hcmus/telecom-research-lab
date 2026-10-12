"""Run only isolated supplemental tests and record the actual result."""

import json
import platform
import sys
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def names(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from names(item)
        else:
            yield item.id()


suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_supplement.py")
ids = list(names(suite))
start = time.monotonic()
with (HERE / "unit-tests.log").open("w", encoding="utf8") as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
receipt = dict(
    command="python projects/m11-noma-qos/analysis/supplement/run_unit_tests.py",
    status="PASS" if result.wasSuccessful() else "FAIL",
    tests_run=result.testsRun,
    failures=len(result.failures),
    errors=len(result.errors),
    skipped=len(result.skipped),
    test_ids=ids,
    elapsed_s=time.monotonic() - start,
    python=platform.python_version(),
    canonical_execution=False,
    native_validation_on_synthetic_fixtures=False,
    log="unit-tests.log",
)
(HERE / "unit-test-results.json").write_text(
    json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf8"
)
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if result.wasSuccessful() else 1)
