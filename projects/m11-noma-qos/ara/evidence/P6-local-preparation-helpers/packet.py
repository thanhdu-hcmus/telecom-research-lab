"""Prepare a bounded local P6 source artifact package for human inspection."""

import csv
from pathlib import Path

from lab.io import load, now, save, sha256

repo = Path.cwd().resolve()
p = repo / "projects/m11-noma-qos"
s = load(p / "research-state.yaml")
assert s["phase"] == "P6" and s["gates"]["G5"]["status"] == "approved"
names = [
    "model/model-spec.tex",
    "model/notation.yaml",
    "model/assumptions.yaml",
    "model/predictions.yaml",
    "sim/protocol.md",
    "sim/protocol.yaml",
    "sim/protocol-errata.md",
    "sim/cases.yaml",
    "sim/lock.json",
    "sim/src/verifier.py",
    "sim/src/oracle.py",
]
sources = sorted(
    f for f in (p / "analysis/supplement").rglob("*.py") if "__pycache__" not in f.parts
)
assert sources
names.extend(f.relative_to(p).as_posix() for f in sources)
files = {name: (p / name).read_text(encoding="utf-8") for name in names}
files["@repo/lab/verification.py"] = (repo / "lab/verification.py").read_text(encoding="utf-8")
files["@repo/schemas/verification_item.schema.json"] = (
    repo / "schemas/verification_item.schema.json"
).read_text(encoding="utf-8")
samples = []
for f in sorted((p / "results/runs").glob("*/manifest.json")):
    m = load(f)
    if m["scenario"] not in ["deterministic", "mc-00-q0", "mc-20-q2"]:
        continue
    fixed = m["params"]["kind"] == "deterministic"
    if not fixed and m["seeds"] != [11001]:
        continue
    outputs = {Path(o["path"]).name: o for o in m["outputs"]}
    raw = p / outputs["channels.csv"]["path"]
    assert sha256(raw) == outputs["channels.csv"]["sha256"]
    with raw.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = []
        for i, row in enumerate(reader):
            if i >= (20 if fixed else 2):
                break
            rows.append(row)
    samples.append(
        {
            "manifest": m,
            "manifest_sha256": sha256(f),
            "raw_header": list(rows[0]),
            "illustrative_rows": rows,
            "ledger": load(p / outputs["ledger.json"]["path"]),
            "sampling": load(p / outputs["sampling.json"]["path"]),
        }
    )
assert len(samples) == 3
assert sum(len(s["illustrative_rows"]) for s in samples) == 24
packet = {
    "files": files,
    "illustrative_manifest_bound_samples": samples,
    "sample_scope": "The fixed first20 cases and two rows from each of two MC settings illustrate source/schema; they do not replace full145-job verification.",
}
target = p / "analysis/P6-code-review-packet.json"
save(target, packet)
metadata = {
    "timestamp": now(),
    "status": "PREPARED LOCALLY; REVIEW NOT LAUNCHED",
    "packet": "analysis/P6-code-review-packet.json",
    "packet_sha256": sha256(target),
    "packet_bytes": target.stat().st_size,
    "artifact_paths": list(files),
    "original_input_hashes": {name: sha256(p / name) for name in names},
    "repository_input_hashes": {
        name: sha256(repo / name)
        for name in ["lab/verification.py", "schemas/verification_item.schema.json"]
    },
    "raw_examples": {"jobs": 3, "rows": 24, "whole_raw_dataset_included": False},
    "excluded": "Credentials, PDFs, unrelated files, author reasoning, previous reviews, provenance and full raw dataset",
    "requested_destination": "Separate authenticated OpenAI Codex review session using the existing account",
    "requested_scope": "Up to three bounded artifact-only source-review rounds on these sources and routine analysis-only fixes; any later review of numerical results requires a new exact packet",
    "required_policy": "Fresh read-only root, approval never, MCP disabled, one named results_verifier at depth one, reviewer uses no tools or writes; actual permissions/source hashes audited",
    "automatic_review_block": "Creation of the external transmission helper was rejected: general independent-review authorization did not specifically authorize this private payload and destination",
    "local_tests": load(p / "analysis/supplement/unit-test-results.json"),
    "scientific_verification_executed": False,
    "scientific_gate_decision": False,
}
save(p / "analysis/P6-code-review-payload.json", metadata)
rows = "\n".join("- `" + name + "`" for name in files)
human = f"""# P6 independent source review authorization

G5 approval is recorded and P6 phase start passed. The native verifier remains
pinned and the additional checker is under `analysis/supplement/`. Review this
bounded [local packet](../analysis/P6-code-review-packet.json) and its
[file/hash inventory](../analysis/P6-code-review-payload.json).

Local isolated tests: **{metadata["local_tests"]["tests_run"]} PASS**, with
{metadata["local_tests"]["failures"]} failures and {metadata["local_tests"]["errors"]} errors.
The canonical dataset has not been independently verified.

## Exact proposed scope

Send the listed source artifacts and 24 illustrative raw rows to a separate
authenticated OpenAI Codex session using the existing account. The review root
will be read-only with approval disabled and MCP disabled. It will spawn one
fresh named results_verifier, given artifacts only, with no tools or writes.
Actual runtime permissions, source hashes and reviewer tool calls must be audited.
The proposed authorization covers up to three bounded source-review rounds and
routine fixes only within analysis/. Numerical-result review will have its own
concrete packet after execution.

Packet size: **{metadata["packet_bytes"]:,} bytes**.
SHA256: `{metadata["packet_sha256"]}`.
Full raw CSV, PDFs, credentials, author reasoning and previous reviews are excluded.

## Why approval is needed

Automatic approval review rejected creating the external review helper because
the general continuation instruction did not specifically authorize this private
payload and destination. The repository AGENTS.md and lab-orchestrator skill
require an enforced independent review. Local implementation and isolated tests
can proceed while this approval is pending.

## Included source files

{rows}

This packet requests a source review before the full canonical verifier run.
It is not a numerical result, an independent verdict or G6 scientific approval.
"""
(p / "to_human/P6-code-review-authorization.md").write_text(human, encoding="utf-8", newline="\n")
print(
    {
        "status": metadata["status"],
        "bytes": metadata["packet_bytes"],
        "artifacts": len(files),
        "sample_rows": 24,
        "packet_sha256": metadata["packet_sha256"],
    }
)
