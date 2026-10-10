"""Pinned archives, reviewable scans and evidence-bound reproduction scoring."""

from __future__ import annotations

import io
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from lab.io import LabError, load, now, safe_id, save, sha256, within
from lab.net import Network


def agreement(reference, actual, mode="relative"):
    ref, got = np.asarray(reference, dtype=float), np.asarray(actual, dtype=float)
    if (
        ref.shape != got.shape
        or ref.size < 2
        or not np.all(np.isfinite(ref))
        or not np.all(np.isfinite(got))
    ):
        raise LabError("Agreement requires matching finite curves with at least two points")
    if mode not in {"relative", "db"}:
        raise LabError("Metric must declare relative or db tolerance")
    error = (
        float(np.max(np.abs(got - ref) / np.maximum(np.abs(ref), 1e-12)))
        if mode == "relative"
        else float(np.max(np.abs(got - ref)))
    )
    same_trend = bool(np.array_equal(np.sign(np.diff(ref)), np.sign(np.diff(got))))
    return {
        "passed": error <= (0.05 if mode == "relative" else 0.5) and same_trend,
        "error": error,
        "mode": mode,
        "same_trend": same_trend,
    }


def scan(folder: Path):
    rules = {
        "network": r"\brequests\b|\bhttpx\b|urllib|webread|urlread|wget|curl",
        "process": r"subprocess|os\.system|\bsystem\s*\(|\bunix\s*\(|\b!",
        "dynamic-code": r"\beval\s*\(|\bexec\s*\(|pickle\.load",
        "delete": r"rmtree|os\.remove|unlink\s*\(|\bdelete\s*\(|\brmdir\s*\(",
        "credential-access": r"\.aws|\.ssh|\.codex|keyring|credential|\.env",
    }
    findings = []
    for p in sorted(folder.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() in {".exe", ".dll", ".so", ".pyd", ".mexw64", ".jar", ".bin"}:
            findings.append(
                {"path": p.relative_to(folder).as_posix(), "line": 0, "category": "binary"}
            )
        if p.suffix.lower() in {".py", ".m", ".sh", ".bat", ".ps1", ".js"}:
            for i, line in enumerate(
                p.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                for category, pattern in rules.items():
                    if re.search(pattern, line, re.I):
                        findings.append(
                            {
                                "path": p.relative_to(folder).as_posix(),
                                "line": i,
                                "category": category,
                            }
                        )
    return {
        "status": "PASS",
        "findings": findings,
        "execution_authorized": False,
        "limitation": "Heuristic scan; source, dependencies, data and license still need explicit review.",
    }


def clone(repo: Path, owner_repo: str, commit: str):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", owner_repo) or not re.fullmatch(
        r"[a-f0-9]{40}", commit
    ):
        raise LabError("Use owner/repo and a full immutable commit SHA")
    dest = repo / "external" / safe_id(owner_repo + "@" + commit)
    if dest.exists():
        raise LabError("Destination already exists; inspect its receipt instead of replacing it")
    with Network(repo) as net:
        proof = net.get(f"https://api.github.com/repos/{owner_repo}/commits/{commit}").json()
        if proof.get("sha") != commit:
            raise LabError("GitHub did not verify exact commit")
        response = net.get(f"https://codeload.github.com/{owner_repo}/zip/{commit}")
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        entries = archive.infolist()
        if sum(e.file_size for e in entries) > 200_000_000:
            raise LabError("Expanded archive too large")
        prepared = []
        for entry in entries:
            parts = Path(entry.filename).parts
            if len(parts) < 2 or entry.is_dir():
                continue
            if entry.external_attr >> 16 & 0o170000 == 0o120000:
                raise LabError("Archive symlinks are not permitted")
            target = within(dest, Path(*parts[1:]))
            prepared.append((target, entry))
        for target, entry in prepared:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(entry))
    receipt = {
        "owner_repo": owner_repo,
        "commit": commit,
        "timestamp": now(),
        "files": {
            p.relative_to(dest).as_posix(): sha256(p) for p in dest.rglob("*") if p.is_file()
        },
        "scan": scan(dest),
    }
    save(dest / "lab-source-receipt.json", receipt)
    return {"status": "PASS", "path": str(dest), "commit": commit, "scan": receipt["scan"]}


def environment(folder: Path, review: Path):
    decision = load(review)
    hashes = {
        p.relative_to(folder).as_posix(): sha256(p)
        for p in folder.rglob("*")
        if p.is_file() and ".venv" not in p.parts and p.name != "lab-source-receipt.json"
    }
    if (
        decision.get("reviewed_files") != hashes
        or not decision.get("source_reviewed")
        or not decision.get("dependencies_reviewed")
        or not decision.get("license_permits_research")
        or not decision.get("data_permitted")
    ):
        raise LabError(
            "Current source, dependency, license and data review required before environment setup"
        )
    uv = decision.get("uv_executable", "uv")
    subprocess.run([uv, "venv", str(folder / ".venv")], check=True, timeout=120)
    requirements = folder / "requirements.txt"
    if requirements.exists():
        subprocess.run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(
                    folder / ".venv/Scripts/python.exe"
                    if sys.platform == "win32"
                    else folder / ".venv/bin/python"
                ),
                "-r",
                str(requirements),
            ],
            check=True,
            timeout=300,
        )
    return {"status": "PASS", "environment": str(folder / ".venv")}


def score(record, current_year=None, evidence_root=None):
    current_year = current_year or datetime.now(timezone.utc).year
    rejected = (
        record.get("tutorial", False)
        or not record.get("paper_link_evidence")
        or not record.get("data_permitted", False)
    )
    points = {
        "venue": {"transactions_jsac": 3, "Q1_Q2": 2, "reputable_conference": 1}.get(
            record.get("venue_tier"), 0
        )
    }
    year = record.get("paper_year")
    age = max(1, current_year - year) if isinstance(year, int) and year <= current_year else None
    rate = max(0, record.get("citations") or 0) / age if age else 0
    points["citations"] = 2 if rate >= 10 else 1 if rate >= 3 else 0
    points["official"] = 2 if record.get("official_link_evidence") else 0
    points["license"] = int(
        bool(record.get("license_permits_research") and record.get("license_evidence"))
    )
    recent = False
    if record.get("last_commit"):
        date = datetime.fromisoformat(record["last_commit"].replace("Z", "+00:00"))
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        recent = 0 <= (datetime.now(timezone.utc) - date).days <= 731
    points["maintenance"] = int(recent or bool(record.get("self_contained_evidence")))
    reproduction = record.get("reproduction", {})
    verified = False
    if (
        evidence_root is not None
        and reproduction.get("run_manifest")
        and reproduction.get("figure_ref")
    ):
        from lab.simulation import locked, output_path, verify_manifest

        mf = within(evidence_root, reproduction["run_manifest"])
        manifest = verify_manifest(evidence_root, load(mf))
        _, lock = locked(evidence_root)
        values = []
        for label in ["reference", "actual"]:
            curve = reproduction[label]
            if not isinstance(curve, dict):
                raise LabError("Reproduction curves must name checksum-bound CSV data")
            matching = [
                o
                for o in manifest.outputs
                if o.path == curve["path"] and o.storage == curve.get("storage", "project")
            ]
            if matching:
                p = output_path(evidence_root, matching[0])
                digest = matching[0].sha256
            else:
                p = within(evidence_root, curve["path"])
                digest = lock["input_hashes"].get(
                    p.relative_to(evidence_root.parents[1]).as_posix()
                )
            if digest != sha256(p):
                raise LabError("Reproduction curve must be a manifest output or locked input")
            data = np.genfromtxt(p, delimiter=",", names=True)
            values.append(data[curve["column"]])
        verified = agreement(*values, reproduction.get("mode", "relative"))["passed"]
    total = sum(points.values())
    return {
        "status": "PASS",
        "points": points,
        "total": total,
        "citations_per_year": rate,
        "accepted": not rejected and verified and total >= 3 and bool(points["license"]),
        "reproduction_verified": verified,
        "rejected_by_policy": rejected,
        "acceptance_mode": "verified-data" if evidence_root is not None else "score-preview-only",
    }


def overlay(reference, actual, destination: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    check = agreement(reference, actual)
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    ax.plot(reference, "o-", label="Reference")
    ax.plot(actual, "s--", label="Reproduction")
    ax.set(xlabel="Sample index", ylabel="Declared metric")
    ax.legend()
    fig.tight_layout()
    fig.savefig(destination)
    plt.close(fig)
    return check
