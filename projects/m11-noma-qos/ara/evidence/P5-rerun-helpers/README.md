# P5 R2 engineering helpers

These are exact retained copies of the scripts used for P5 engineering
recomputation. They are author tooling, not independent P6 verification or
additional locked simulation inputs. The actual command paths were under the
ignored repository `.cache/` directory; their retained source is provided here
for inspection and replay.

From the repository root, the diagnostics and channel audit can be rerun with:

```powershell
.\.venv\Scripts\python.exe projects/m11-noma-qos/ara/evidence/P5-rerun-helpers/diagnostics.py
.\.venv\Scripts\python.exe projects/m11-noma-qos/ara/evidence/P5-rerun-helpers/channel_audit.py
```

Both call ordinary native lock and manifest validation. Replays overwrite the
current derived results, so replay in an isolated checkout with manifest-bound
raw data available. Do not change approved gate artifacts in place.

The pipeline records the exact old/new output-byte comparison and launches
fresh collection, pinned aggregation, diagnostics and channel audit. Its
historical `.cache/` command/receipt paths are retained as executed. It is an
execution record, not a command to rerun during a pending or approved gate.

The conditional aggregate is the unchanged pinned
`projects/m11-noma-qos/sim/src/aggregate.py`; collection uses `lab sim collect`.
No production guard is bypassed by these helpers. Numerical evidence remains
bound to the native simulation manifests and the committed protocol lock.

`compare_derived.py` checks freshly regenerated summaries against archived R1.
It declares the exact lineage/runtime fields excluded from equality. It does
not reuse old summaries to generate fresh results or assert P6 independence.

`report.py`, `gate_request.py` and `finalize.py` retain the report generation,
native G5 request and progress-document update steps. They never approve a
scientific gate. They are historical execution sources; do not execute them
against a pending/approved project or overwrite its preserved review receipts.
