"""Bounded synthetic preparation timing; never a canonical runtime claim."""

import json
import sys
import time
import tracemalloc
from pathlib import Path

from independent import Audit, check_row
from test_supplement import fixture

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

inputs = (10.0, 1.0, 3.0, 0.25, 0.25)
raw, metric = fixture(inputs)
samples = []
for traced in (False, True):
    if traced:
        tracemalloc.start()
    start = time.monotonic()
    completed = 0
    for _ in range(1000):
        audit = Audit()
        check_row(raw, metric, list(inputs), "fixture", 0, audit)
        if not audit.ok():
            raise AssertionError(audit.counts)
        completed += 1
        if time.monotonic() - start > 50:
            break
    elapsed = time.monotonic() - start
    peak = tracemalloc.get_traced_memory()[1] if traced else None
    if traced:
        tracemalloc.stop()
    samples.append(
        dict(
            traced=traced,
            synthetic_rows=completed,
            elapsed_s=elapsed,
            seconds_per_row=elapsed / completed,
            extrapolated_4718692_rows_s=elapsed / completed * 4718692,
            peak_traced_bytes=peak,
        )
    )
receipt = dict(
    status="MEASURED_SYNTHETIC_ONLY",
    canonical_execution=False,
    inputs=list(inputs),
    samples=samples,
    limitations=[
        "Repeated ordinary feasible synthetic row; distribution mix not represented.",
        "Extrapolation excludes native guards, CSV IO, hashing and shared oracle replay.",
        "This is a cost estimate, not a canonical runtime or completion certificate.",
    ],
)
(HERE / "synthetic-timing.json").write_text(
    json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf8"
)
print(json.dumps(receipt, indent=2))
