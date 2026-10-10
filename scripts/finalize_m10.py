"""Record acceptance only from real receipts and audited specialist trials."""

from pathlib import Path

from lab.io import load, now, save, sha256

ROOT = Path(__file__).resolve().parents[1]
TRIALS = {
    "novelty-detect": ["6bd209d97c89-1", "c76a15e4f707-2", "b820580be441-3"],
    "idea-card-completeness": ["921912bb7143-1", "8d661d46670e-2", "25998f6624c9-3"],
    "repro-small": ["dff3393d4c44-1", "507ba1b101fa-2", "7b749952ee21-3"],
    "critic-planted-flaws": ["b5b9c19b8b77-1", "f17b20bf2e0d-2", "9f2fd4f08009-3"],
    "modeler-derivation": [
        "c87b48662695-1-rechecked",
        "7dc4200c1959-2-rechecked",
        "4070708efc7e-3-rechecked",
    ],
    "protocol-discipline": ["7ccdcce83e96-1", "29ffd19af492-2", "645512e34495-3"],
    "verifier-planted-bugs": ["5f0c59dd72a7-1", "def831d40076-2", "7083c4970cb1-3"],
    "writer-no-fabrication": [
        "562d739123f8-1-rechecked",
        "7ba41f1839b1-2-rechecked",
        "d8343b577544-3-rechecked",
    ],
    "reviewer-catches-overclaim": ["43930d25899f-1", "3ed58052485a-2", "658d73ced251-3"],
    "orchestrator-gate-respect": [
        "3bac4cb01f1e-1-rechecked",
        "a8ba9b37a121-2-rechecked",
        "b0934eb571b2-3-rechecked",
    ],
}
evaluations = {}
for name, trials in TRIALS.items():
    records = []
    for trial in trials:
        file = ROOT / "docs/evidence/evals" / f"{name}-{trial}.json"
        record = load(file)
        accepted = record["grader"]["passed"] and record["fixture_unchanged"]
        audit_file = ROOT / record["raw_evidence"] / "spawn-audit.json"
        audit = load(audit_file, {"verified": False, "children": []})
        if accepted and not audit["verified"]:
            raise RuntimeError("Unaudited passing trial: " + record["id"])
        records.append(
            {
                "id": record["id"],
                "passed": accepted,
                "grade_receipt_sha256": sha256(file),
                "runtime_verified": audit["verified"],
                "children": audit["children"],
                "audit_sha256": sha256(audit_file) if audit_file.exists() else None,
            }
        )
    count = sum(r["passed"] for r in records)
    if count < 2:
        raise RuntimeError("Evaluation failed threshold: " + name)
    evaluations[name] = {"passed": count, "trials": records}

receipts = {}
for name in [
    "m5-m10-deterministic",
    "m8-matlab-physics",
    "m8-matlab-roundtrip",
    "m8-m10-local-integration",
]:
    file = ROOT / "docs/evidence" / (name + ".json")
    receipt = load(file)
    if receipt["status"] != "PASS":
        raise RuntimeError("Acceptance receipt failed: " + name)
    receipts[name] = {"status": receipt["status"], "sha256": sha256(file)}
integration = load(ROOT / "docs/evidence/m8-m10-local-integration.json")
if sha256(ROOT / integration["zip"]) != integration["zip_sha256"]:
    raise RuntimeError("Handoff ZIP changed")
confirmation_file = ROOT / "docs/evidence/m10-overleaf-confirmation.json"
confirmation = load(confirmation_file, {})
overleaf_confirmed = (
    confirmation.get("status") == "PASS"
    and confirmation.get("confirmed_by") == "PI"
    and confirmation.get("zip_sha256") == integration["zip_sha256"]
    and confirmation.get("pdf_inspection", {}).get("status") == "PASS"
)
if confirmation and not overleaf_confirmed:
    raise RuntimeError("Overleaf confirmation does not match the accepted handoff")
acceptance = {
    "status": "complete" if overleaf_confirmed else "software_acceptance_passed",
    "timestamp": now(),
    "evaluations": evaluations,
    "receipts": receipts,
    "remaining": None
    if overleaf_confirmed
    else "M10 PI confirmation of one actual Overleaf compilation",
}
if overleaf_confirmed:
    acceptance["overleaf_confirmation"] = {
        "receipt": confirmation_file.relative_to(ROOT).as_posix(),
        "sha256": sha256(confirmation_file),
    }
save(ROOT / "docs/evidence/m5-m10-acceptance.json", acceptance)
state = load(ROOT / "implementation-state.json")
state.update(
    updated_at=now(),
    active_milestone="M10",
    status="software_build_complete"
    if overleaf_confirmed
    else "software_complete_pending_pi_overleaf",
    verification_complete=True,
)
state["pi_approval"] = {
    "quote": "Approve M0, continue M1\u2013M10 automatically, and create the new private repository.",
    "scope": "M0 acceptance and software build M1-M10; no scientific gate approval",
}
for milestone in ["M5", "M6", "M7", "M8", "M9"]:
    state["milestones"][milestone] = "complete"
state["milestones"]["M10"] = (
    "complete" if overleaf_confirmed else "software_complete_pending_pi_overleaf"
)
state["unresolved"] = [
    *(
        []
        if overleaf_confirmed
        else ["PI confirms the exported synthetic ZIP compiles on Overleaf once (M10 source plan)"]
    ),
    "PI fills thesis profile and target venues before real P3 ideation",
    "M11/M12 and scientific gates G1-G7 require PI participation",
    "Optional Gemini unavailable; manual independent review packets provided",
    "DL workstation launch route remains unspecified; not required for framework fixtures",
]
state["last_acceptance"] = {
    "tests": load(ROOT / "docs/evidence/m5-m10-deterministic.json")["tests_passed"],
    **{name: f"{receipt['passed']}/3" for name, receipt in evaluations.items()},
    "matlab_physics": "PASS",
    "matlab_mcp_and_batch_dispatch": "PASS",
    "journal_and_conference": "PASS",
    "clean_zip_compilation": "PASS",
    "overleaf_pi_confirmation": "PASS" if overleaf_confirmed else "pending",
}
state["repository"] = "https://github.com/thanhdu-hcmus/telecom-research-lab"
save(ROOT / "implementation-state.json", state)
print(
    "Recorded complete M5-M10 acceptance including PI Overleaf confirmation."
    if overleaf_confirmed
    else "Recorded audited M5-M10 software acceptance; PI Overleaf confirmation remains pending."
)
