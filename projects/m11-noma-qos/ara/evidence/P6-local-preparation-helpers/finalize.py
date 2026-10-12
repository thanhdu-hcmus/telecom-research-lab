"""Record local P6 preparation without launching a review or scientific verifier."""

from pathlib import Path

from lab.io import load, now, save, sha256
from lab.state import provenance

r = Path.cwd()
p = r / "projects/m11-noma-qos"
prep = load(p / "analysis/supplement/preparation.json")
tests = load(p / "analysis/supplement/unit-test-results.json")
payload = load(p / "analysis/P6-code-review-payload.json")
assert tests["status"] == "PASS" and not prep["canonical_execution_performed"]
assert payload["packet_sha256"] == sha256(p / payload["packet"])
for name, digest in prep["sources"].items():
    assert sha256(p / "analysis/supplement" / name) == digest, name
for name, digest in prep["inputs"].items():
    assert sha256(p / name) == digest, name
lock = load(p / "sim/lock.json")
for name, digest in lock["input_hashes"].items():
    assert sha256(r / name) == digest, name
receipt = {
    "timestamp": now(),
    "status": "LOCAL_PREPARATION_COMPLETE; EXTERNAL_SOURCE_REVIEW_PENDING",
    "phase": "P6",
    "locked_input_byte_check": {"status": "PASS", "inputs": len(lock["input_hashes"])},
    "local_helpers_lint": {
        "status": "PASS",
        "initial_errors": 22,
        "resolution": "Four import fixes plus formatting of three local-only helper sources; final Ruff check passed",
    },
    "helpers": {
        f.name: sha256(f) for f in (p / "ara/evidence/P6-local-preparation-helpers").glob("*.py")
    },
    "gates": {k: v["status"] for k, v in load(p / "research-state.yaml")["gates"].items()},
    "tests": tests,
    "expected_full_execution": prep["expected"],
    "supplement_lint": load(p / "analysis/supplement/lint-results.json"),
    "synthetic_timing_only": load(p / "analysis/supplement/synthetic-timing.json"),
    "failed_trials": load(p / "analysis/supplement/failed-trials.json"),
    "canonical_scientific_verifier_executed": False,
    "supplement_canonical_execution_performed": False,
    "independent_review_rounds": 0,
    "source_review_open_items": [
        "Top-level oracle_status_counts and maximum_oracle_sum_difference reconciliation remains to be reviewed.",
        "Explicit oracle objective versus independent bracket optimum reconciliation remains to be reviewed.",
        "Full canonical runtime is unmeasured; synthetic tracing estimates omit guards/IO/hash/replays.",
    ],
    "gate_G6_requested": False,
    "parent_engineering_feedback": "Local source inspection and feedback were not an enforced independent review.",
    "review_payload": payload,
    "evidence": {
        name: sha256(p / name)
        for name in [
            "analysis/supplement/preparation.json",
            "analysis/supplement/unit-test-results.json",
            "analysis/supplement/README.md",
            "analysis/supplement/lint-results.json",
            "analysis/supplement/synthetic-timing.json",
            "analysis/supplement/failed-trials.json",
            "analysis/supplement/synthetic-timing-before-grid-vectorization.json",
            "analysis/P6-code-review-packet.json",
            "analysis/P6-code-review-payload.json",
            "to_human/P6-code-review-authorization.md",
        ]
    },
    "failed_action": {
        "action": "Create helper for external Codex source review",
        "outcome": "AUTOMATIC APPROVAL REVIEW REJECTED",
        "reason": "The helper would transmit private project source, protocol, model and result artifacts to a separate Codex/OpenAI session. General independent-review authorization did not specifically authorize this sensitive payload and destination.",
        "resolution": "Rejected helper was not created. Only a local bounded packet was prepared; no external review launched. Exact packet/destination approval is required before transmission.",
    },
}
save(p / "ara/staging/P6-local-preparation.json", receipt)
state = load(r / "implementation-state.json")
state["status"] = "m11_p6_external_source_review_authorization_pending"
state["m11_p5"]["independent_P6_verification"] = (
    "NOT RUN; G5 approved, P6 source review prerequisite pending"
)
state["m11_p6"].update(
    status=receipt["status"],
    scientific_verification="NOT RUN",
    local_supplement_preparation="complete; not independently reviewed",
    isolated_tests=tests["tests_run"],
    isolated_test_status=tests["status"],
    independent_review_rounds=0,
    external_review_authorization="Pending exact bounded private artifact packet/destination approval after automatic approval rejection",
    review_authorization_packet="projects/m11-noma-qos/to_human/P6-code-review-authorization.md",
    preparation_receipt="projects/m11-noma-qos/ara/staging/P6-local-preparation.json",
)
save(r / "implementation-state.json", state)
with (p / "findings.md").open("a", encoding="utf-8", newline="\n") as f:
    f.write("\n## Current P6: local checker prepared; source review authorization pending\n\n")
    f.write(
        "Canonical G5 approval commit398f26d230b7de0194091a36617e0ca0b157f952 was verified, and native P6 phase start passed. G1-G5 are approved; G6-G7 remain invalidated. Earlier G5-pending sections are historical.\n\n"
    )
    f.write(
        f"The supplemental checker was prepared under analysis/supplement, with {tests['tests_run']} isolated tests passing. Its preparation binds 145 planned jobs and 4,718,692 stored rows; preparation is not execution. The shared pinned oracle replay is separately labelled. Parent engineering feedback is not an independent review.\n\n"
    )
    f.write(
        "Automatic approval review rejected creating the external review helper because the private source/model/protocol/results payload and separate authenticated OpenAI Codex destination were not specifically authorized. The helper was not created and no review session was launched. A bounded local packet and exact authorization scope are in to_human/P6-code-review-authorization.md. Native and supplemental canonical scientific verification await enforced independent source review. No G6 request or scientific acceptance is claimed.\n"
    )
result = provenance(
    p,
    "P6 local independent-calculation checker preparation and isolated tests completed. Automatic approval review rejected the external transmission helper; no external review or canonical scientific verification ran. Prepared the exact bounded local source packet and destination/scope for PI authorization. Parent engineering feedback is not enforced independence; G6/G7 remain invalidated.",
    [
        "ara/staging/P6-local-preparation.json",
        "analysis/P6-code-review-payload.json",
        "analysis/supplement/preparation.json",
        "analysis/supplement/unit-test-results.json",
        "to_human/P6-code-review-authorization.md",
    ],
    "ai",
)
print({"status": receipt["status"], "tests": tests["tests_run"], "provenance": result})
