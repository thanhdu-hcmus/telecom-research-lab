"""Phase transitions and evidence-bound PI decisions; no agent approval route."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import shutil
import sys
from pathlib import Path

from lab.io import LabError, git, load, now, save, sha256, within
from lab.models import Deviation, GateDecision, ResearchState, Scope

GATES = [f"G{i}" for i in range(1, 8)]
REQUIRED = {
    1: ["scope.md", "scope.yaml", "research-log.md", "findings.md"],
    2: [
        "literature/query-plan.yaml",
        "literature/candidates.jsonl",
        "literature/screening.yaml",
        "literature/gap-matrix.csv",
        "literature/gaps.md",
        "literature/survey.md",
        "baselines/candidates.yaml",
    ],
    3: ["ideas/ranking.md", "ideas/sensitivity.json"],
    4: [
        "model/model-spec.tex",
        "model/notation.yaml",
        "model/assumptions.yaml",
        "model/predictions.yaml",
        "model/critique.yaml",
        "model/response.md",
    ],
    5: ["sim/protocol.md", "sim/protocol.yaml", "sim/lock.json"],
    6: ["analysis/verification-report.md", "analysis/verification.yaml", "results/claims.json"],
    7: [
        "paper/main.tex",
        "paper/refs.bib",
        "paper/number-map.yaml",
        "paper/review.yaml",
        "paper/response.md",
        "paper/ai-disclosure.md",
    ],
}
PHASE_DIRS = {
    2: ["literature"],
    3: ["ideas"],
    4: ["model"],
    5: ["sim", "results"],
    6: ["analysis"],
    7: ["paper"],
}


def number(value: str, prefix: str) -> int:
    if not re.fullmatch(prefix + "[1-7]", value):
        raise LabError(f"Expected {prefix}1–{prefix}7")
    return int(value[1])


def project(repo: Path, slug: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,59}", slug):
        raise LabError("Project slug must contain lowercase letters, digits and hyphens.")
    path = within(repo / "projects", slug)
    if not (path / "research-state.yaml").exists():
        raise LabError(f"Unknown project: {slug}; use lab project init")
    return path


def state(path: Path) -> dict:
    value = load(path / "research-state.yaml")
    ResearchState.model_validate(value)
    if set(value["gates"]) != set(GATES):
        raise LabError("State must contain exactly seven gates")
    return value


def update(path: Path, value: dict) -> None:
    ResearchState.model_validate(value)
    save(path / "research-state.yaml", value)


def log(path: Path, message: str) -> None:
    with (path / "research-log.md").open("a", encoding="utf-8") as stream:
        stream.write(f"\n- {now()} — {message}\n")


def init(repo: Path, slug: str) -> dict:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,59}", slug):
        raise LabError("Invalid project slug")
    path = within(repo / "projects", slug)
    if path.exists():
        raise LabError("Project already exists; refusing to overwrite")
    for directory in [
        "literature/cards",
        "baselines",
        "ideas/novelty",
        "model/checks",
        "sim/src",
        "sim/tests",
        "results",
        "analysis/independent",
        "paper",
        "gates",
        "to_human",
        "ara/trace/sessions",
        "ara/logic",
        "ara/evidence",
        "ara/staging",
        "archive",
    ]:
        (path / directory).mkdir(parents=True, exist_ok=True)
    value = ResearchState(project=slug, gates={g: {} for g in GATES}).model_dump(mode="json")
    update(path, value)
    save(path / "gates/decisions.yaml", [])
    save(path / "deviations.yaml", [])
    save(path / "ara/trace/sessions/session_index.yaml", [])
    (path / "scope.md").write_text(
        "# Scope\n\nDraft the scope and scope.yaml from the PI's reviewed thesis profile.\n",
        encoding="utf-8",
    )
    (path / "findings.md").write_text(
        "# Findings\n\n## Current understanding\n\nNot researched yet.\n\n## Supported claims\n\nNone.\n\n## Lessons and constraints\n\n## Open questions\n",
        encoding="utf-8",
    )
    (path / "research-log.md").write_text("# Research log\n", encoding="utf-8")
    log(path, "Project initialized; all scientific gates pending PI decisions.")
    return {"status": "PASS", "project": slug, "path": str(path), "phase": "P1"}


def artifact_files(path: Path, index: int) -> list[Path]:
    files = {path / name for name in REQUIRED[index] if (path / name).is_file()}
    for directory in PHASE_DIRS.get(index, []):
        files.update(
            p
            for p in (path / directory).rglob("*")
            if p.is_file()
            and p.name not in {"claims.json", "lock.json"}
            and p.suffix not in {".aux", ".log", ".pdf", ".pyc", ".bbl", ".blg", ".fls", ".out"}
            and "__pycache__" not in p.parts
        )
    if index == 1:
        files = {p for p in files if p.name not in {"research-log.md", "findings.md"}}
        profile = path.parents[1] / "config/thesis-profile.yaml"
        files.add(profile)
    if index == 2:
        files.add(path / "baselines/candidates.yaml")
    return sorted(files)


def snapshot(path: Path, index: int) -> dict:
    repo = path.parents[1]
    return {p.relative_to(repo).as_posix(): sha256(p) for p in artifact_files(path, index)}


def invalidate(path: Path, value: dict, index: int, note: str) -> None:
    for i in range(index, 8):
        value["gates"][f"G{i}"]["status"] = "invalidated"
        value["gates"][f"G{i}"]["checks_passed"] = False
    if index <= 3:
        value["selected_idea"] = None
    if index <= 5:
        value["protocol_hash"] = None
        value["protocol_commit"] = None
    value["phase"] = f"P{index}"
    update(path, value)
    log(path, note)


def require(path: Path, gate: str) -> dict:
    index = number(gate, "G")
    value = state(path)
    decisions(path)  # Verify append-only hash chain before trusting cached state.
    for i in range(1, index + 1):
        item = value["gates"][f"G{i}"]
        if item["status"] != "approved":
            raise LabError(f"G{i} requires PI approval before proceeding")
        history = [r for r in decisions(path) if r["gate"] == f"G{i}"]
        if (
            not history
            or history[-1]["decision"] != "approve"
            or history[-1]["artifact_hashes"] != item["artifact_hashes"]
        ):
            raise LabError(f"G{i} state does not match a recorded PI decision")
        if snapshot(path, i) != item["artifact_hashes"]:
            invalidate(path, value, i, f"G{i} artifact changes invalidated downstream approvals")
            raise LabError(f"G{i} approved evidence changed; request review again")
    return {"status": "PASS", "gate": gate}


def enter(path: Path, phase: str) -> dict:
    index = number(phase, "P")
    if index > 1:
        require(path, f"G{index - 1}")
    value = state(path)
    if index < number(value["phase"], "P"):
        raise LabError("Returning to an earlier phase requires a PI rewind")
    value["phase"] = phase
    update(path, value)
    log(path, f"Entered {phase}")
    return {"status": "PASS", "phase": phase}


def ensure_phase(path: Path, phase: str) -> None:
    index = number(phase, "P")
    if state(path)["phase"] != phase:
        raise LabError(f"This operation belongs to {phase}; use lab phase start first")
    if index > 1:
        require(path, f"G{index - 1}")


def phase_checks(path: Path, index: int) -> list[dict]:
    checks = []
    for name in REQUIRED[index]:
        p = path / name
        checks.append(
            {
                "check": name,
                "passed": p.is_file() and bool(p.read_bytes().strip()),
                "details": "required artifact",
            }
        )
    try:
        if index == 1:
            scope = Scope.model_validate(load(path / "scope.yaml"))
            profile = load(path.parents[1] / "config/thesis-profile.yaml")
            if not scope.thesis_profile_reviewed or not profile.get("pi_reviewed"):
                raise LabError("PI must review the thesis profile and scope")
        elif index == 2:
            from lab.literature import validate_review

            validate_review(path)
        elif index == 3:
            from lab.ideas import validate_ideas

            validate_ideas(path)
        elif index == 4:
            from lab.modeling import validate_model

            validate_model(path)
        elif index == 5:
            from lab.simulation import validate_runs

            validate_runs(path)
        elif index == 6:
            from lab.verification import validate_verification

            validate_verification(path)
        elif index == 7:
            from lab.paper import validate_paper

            validate_paper(path)
        checks.append(
            {
                "check": "runtime-validation",
                "passed": True,
                "details": "schemas and phase invariants",
            }
        )
    except (ValueError, OSError, ImportError, KeyError) as error:
        checks.append({"check": "runtime-validation", "passed": False, "details": str(error)})
    open_deviations = [d["id"] for d in load(path / "deviations.yaml", []) if d["status"] == "open"]
    checks.append(
        {"check": "deviations", "passed": not open_deviations, "details": open_deviations}
    )
    return checks


def request(path: Path, gate: str) -> dict:
    index = number(gate, "G")
    ensure_phase(path, f"P{index}")
    checks = phase_checks(path, index)
    hashes = snapshot(path, index)
    value = state(path)
    value["gates"][gate].update(
        status="pending",
        timestamp=now(),
        artifact_hashes=hashes,
        checks_passed=all(c["passed"] for c in checks),
    )
    update(path, value)
    report = path / f"to_human/{gate}-report.md"
    artifacts = "\n".join(f"- `{name}` — SHA256 `{digest}`" for name, digest in hashes.items())
    rows = "\n".join(
        f"| {c['check']} | {'PASS' if c['passed'] else 'FAIL'} | {c['details']} |" for c in checks
    )
    sample = ""
    if index == 2:
        cards = sorted((path / "literature/cards").glob("*.yaml"))
        chooser = secrets.SystemRandom()
        sample = "\nPI spot-check sample: " + ", ".join(
            p.name for p in chooser.sample(cards, min(5, len(cards)))
        )
    report.write_text(
        f'# {gate} — {path.name}\n\n## Summary\n\nScientific decision pending PI review.{sample}\n\n## Artifacts\n\n{artifacts}\n\n## Automated checks\n\n| Check | Result | Details |\n|---|---|---|\n{rows}\n\n## Findings and deviations\n\nReview phase artifacts, unresolved issues and deviations.yaml.\n\n## Untrusted-content alerts\n\nReview alerts recorded by specialists; absence of a report is not a scan guarantee.\n\n## Provenance and effort\n\nSee ara/trace/sessions; run provenance-epilogue before decision.\n\n## PI checklist\n\n- [ ] Scope and assumptions accepted\n- [ ] Evidence spot-checked\n- [ ] Deviations resolved\n- [ ] Provenance reviewed\n\n## Decide\n\n`lab gate approve {gate} --project {path.name} --note "..."`\n\nAlternatively use gate revise or rewind.\n',
        encoding="utf-8",
    )
    log(
        path,
        f"Requested {gate}; automated checks {'passed' if value['gates'][gate]['checks_passed'] else 'failed'}",
    )
    return {
        "status": "PASS" if value["gates"][gate]["checks_passed"] else "FAIL",
        "gate": gate,
        "checks": checks,
        "report": str(report),
    }


def pi_confirm(action: str) -> None:
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise LabError("PI decisions require an interactive terminal; agents must request review")
    code = secrets.token_hex(3).upper()
    if input(f"PI only: type {action} {code}: ").strip() != f"{action} {code}":
        raise LabError("Confirmation did not match; no decision recorded")


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def decisions(path: Path) -> list[dict]:
    records = load(path / "gates/decisions.yaml", [])
    previous = None
    for record in records:
        GateDecision.model_validate(record)
        material = {k: v for k, v in record.items() if k != "record_hash"}
        if record["previous_hash"] != previous or record["record_hash"] != canonical_hash(material):
            raise LabError("Decision history altered or reordered; restore committed history")
        previous = record["record_hash"]
    return records


def commit_decision(path: Path, message: str) -> None:
    repo = path.parents[1]
    files = [
        str(p.relative_to(repo))
        for p in [
            path / "gates/decisions.yaml",
            path / "research-state.yaml",
            path / "research-log.md",
            path / "deviations.yaml",
        ]
    ]
    git(repo, "add", "--", *files)
    git(repo, "commit", "--only", "-m", message, "--", *files)


def decide(path: Path, gate: str, decision: str, note: str, select: str | None = None) -> dict:
    index = number(gate, "G")
    if decision not in {"approve", "revise"} or not note.strip():
        raise LabError("Decision and explanatory note required")
    value = state(path)
    if value["phase"] != f"P{index}" or value["gates"][gate]["status"] != "pending":
        raise LabError("Request the current phase gate first")
    if index > 1:
        require(path, f"G{index - 1}")
    if decision == "approve":
        if not value["gates"][gate]["checks_passed"] or not all(
            c["passed"] for c in phase_checks(path, index)
        ):
            raise LabError("Automated checks failed; revise artifacts before approval")
        if snapshot(path, index) != value["gates"][gate]["artifact_hashes"]:
            raise LabError("Artifacts changed since request; request a fresh review")
        if gate == "G3":
            from lab.ideas import eligible
            from lab.models import IdeaCard

            cards = [IdeaCard.model_validate(load(p)) for p in (path / "ideas").glob("*.yaml")]
            if not select or not any(c.id == select and eligible(c) for c in cards):
                raise LabError("G3 needs --select naming an eligible idea card")
        elif select:
            raise LabError("--select is only valid at G3")
    records = decisions(path)
    pi_confirm(f"{decision.upper()} {gate}")
    original_state = load(path / "research-state.yaml")
    original_log = (path / "research-log.md").read_text(encoding="utf-8")
    record = {
        "gate": gate,
        "decision": decision,
        "note": note,
        "timestamp": now(),
        "git_user": git(path.parents[1], "config", "user.name") or "PI",
        "selected_idea": select,
        "artifact_hashes": snapshot(path, index),
        "previous_hash": records[-1]["record_hash"] if records else None,
    }
    record["record_hash"] = canonical_hash(record)
    GateDecision.model_validate(record)
    save(path / "gates/decisions.yaml", [*records, record])
    value["gates"][gate].update(
        status="approved" if decision == "approve" else "revise",
        note=note,
        timestamp=record["timestamp"],
    )
    if gate == "G3" and decision == "approve":
        value["selected_idea"] = select
    update(path, value)
    log(path, f"PI {decision} {gate}: {note}")
    try:
        commit_decision(path, f"research(reflect): {path.name} PI {decision} {gate}")
    except LabError:
        save(path / "gates/decisions.yaml", records)
        update(path, original_state)
        (path / "research-log.md").write_text(original_log, encoding="utf-8")
        raise
    return {"status": "PASS", "gate": gate, "decision": decision}


def rewind(path: Path, phase: str, note: str) -> dict:
    index = number(phase, "P")
    if not note.strip():
        raise LabError("Rewind needs a note")
    value = state(path)
    records = decisions(path)
    pi_confirm(f"REWIND {phase}")
    destination = path / "archive" / now().replace(":", "-")
    destination.mkdir(parents=True)
    save(destination / "research-state.yaml", value)
    if index == 1:
        for name in ["scope.md", "scope.yaml"]:
            if (path / name).exists():
                shutil.copy2(path / name, destination / name)
    for i in range(index, 8):
        for directory in PHASE_DIRS.get(i, []):
            source = within(path, directory)
            if source.exists() and any(source.iterdir()):
                shutil.move(str(source), str(destination / directory))
                source.mkdir(parents=True)
    if index <= 2 and (path / "baselines").exists():
        shutil.move(str(path / "baselines"), str(destination / "baselines"))
        (path / "baselines").mkdir()
    record = {
        "gate": f"G{index}",
        "decision": "rewind",
        "note": note,
        "timestamp": now(),
        "git_user": git(path.parents[1], "config", "user.name") or "PI",
        "selected_idea": None,
        "artifact_hashes": {},
        "previous_hash": records[-1]["record_hash"] if records else None,
    }
    record["record_hash"] = canonical_hash(record)
    save(path / "gates/decisions.yaml", [*records, record])
    invalidate(path, value, index, f"PI rewind to {phase}: {note}; archived at {destination.name}")
    # Archive and removals are part of the rewind commit, without unrelated staging.
    repo = path.parents[1]
    relative = str(path.relative_to(repo))
    git(repo, "add", "--all", "--", relative)
    git(
        repo,
        "commit",
        "--only",
        "-m",
        f"research(reflect): {path.name} rewind {phase}",
        "--",
        relative,
    )
    return {"status": "PASS", "phase": phase, "archive": str(destination)}


def deviation_open(path: Path, what: str, why: str, proposed_change: str, impact: str) -> dict:
    records = load(path / "deviations.yaml", [])
    record = Deviation(
        id=f"D{len(records) + 1:03}",
        phase=state(path)["phase"],
        what=what,
        why=why,
        proposed_change=proposed_change,
        impact=impact,
    ).model_dump(mode="json")
    save(path / "deviations.yaml", [*records, record])
    value = state(path)
    value["deviations"].append(record["id"])
    update(path, value)
    log(path, f"Opened {record['id']}: {what}")
    return {"status": "PASS", "deviation": record}


def deviation_resolve(path: Path, identifier: str, decision: str, note: str) -> dict:
    if decision not in {"approved", "rejected"} or not note.strip():
        raise LabError("Deviation resolution requires approved/rejected and note")
    records = load(path / "deviations.yaml", [])
    matches = [r for r in records if r["id"] == identifier and r["status"] == "open"]
    if len(matches) != 1:
        raise LabError("No unique open deviation with this ID")
    pi_confirm(f"RESOLVE {identifier} {decision.upper()}")
    matches[0].update(
        status=decision,
        decision_note=note,
        decided_by=git(path.parents[1], "config", "user.name") or "PI",
    )
    save(path / "deviations.yaml", records)
    log(path, f"PI resolved {identifier} {decision}: {note}")
    if decision == "approved":
        invalidate(
            path,
            state(path),
            number(matches[0]["phase"], "P"),
            f"Approved {identifier}: fresh gate review required",
        )
    commit_decision(path, f"research(reflect): PI resolve {identifier}")
    return {"status": "PASS", "deviation": matches[0]}


def provenance(path: Path, summary: str, files: list[str], tag: str = "ai") -> dict:
    if tag not in {"user", "ai", "joint"}:
        raise LabError("Provenance tag must be user, ai or joint")
    index_path = path / "ara/trace/sessions/session_index.yaml"
    index = load(index_path, [])
    identifier = f"{now()[:10]}-{len(index) + 1:04}"
    record = {
        "id": identifier,
        "timestamp": now(),
        "phase": state(path)["phase"],
        "summary": summary,
        "provenance": tag,
        "evidence": {name: sha256(within(path, name)) for name in files},
    }
    save(path / f"ara/trace/sessions/{identifier}.yaml", record)
    save(index_path, [*index, identifier])
    return {"status": "PASS", "session": record}
