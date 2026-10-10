"""Actual local pipeline in an isolated synthetic Git fixture; no PI gate decision."""

from pathlib import Path
import json
import shutil
import uuid
from unittest.mock import patch
import numpy as np
from lab.io import load, save, git, sha256
from lab import state, simulation, verification, paper, citations, figures

ROOT = Path(__file__).resolve().parents[1]
repo = ROOT / ".cache" / f"writing-smoke-{uuid.uuid4().hex[:8]}"
repo.mkdir(parents=True)
shutil.copytree(ROOT / "templates", repo / "templates")
shutil.copytree(ROOT / "lab", repo / "lab", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copyfile(ROOT / "uv.lock", repo / "uv.lock")
(repo / "config").mkdir()
cfg = load(ROOT / "config/lab.config.yaml")
cfg["latex_bin"] = str(ROOT / ".tools/texlive/bin/windows")
cfg["library_root"] = "library"
save(repo / "config/lab.config.yaml", cfg)
git(repo, "init")
git(repo, "config", "user.name", "Synthetic Fixture")
git(repo, "config", "user.email", "fixture@example.test")
path = repo / "projects/toy"
(path / "sim").mkdir(parents=True)
(path / "model").mkdir()
save(
    path / "research-state.yaml",
    {"project": "toy", "phase": "P5", "gates": {f"G{i}": {} for i in range(1, 8)}},
)
(path / "sim/protocol.md").write_text(
    "# Synthetic software integration fixture\n\nOrdered iid Rayleigh NOMA versus OMA, common gains and equal normalized power/bandwidth; this is not a research gate approval.\n",
    encoding="utf-8",
    newline="\n",
)
save(
    path / "sim/protocol.yaml",
    {
        "version": 1,
        "language": "python",
        "inputs": ["simulator-source.py"],
        "metrics": ["sumrate", "outage"],
        "fairness": dict.fromkeys(
            ["same_power", "same_bandwidth", "same_csi", "common_channels", "same_qos"], True
        ),
        "trial_policy": {"relative_ci_halfwidth": 0.01, "minimum_events": 100},
        "scenarios": [
            {
                "id": "toy",
                "seeds": [1, 2, 3],
                "trials": 100000,
                "params": {
                    "rho_linear": 10,
                    "a_weak": 0.8,
                    "target_rate_weak": 1,
                    "target_rate_strong": 1,
                },
            }
        ],
    },
)
shutil.copyfile(ROOT / "lab/simulation.py", repo / "simulator-source.py")
save(
    path / "model/predictions.yaml",
    [
        {
            "id": "T1",
            "statement": "Synthetic test range for mean sum rate",
            "expression_or_law": "0<=mean<=10",
            "regime": "Fixture only",
            "test_method": "Independent raw-channel recomputation",
            "tolerance": {"metric": "noma_sumrate", "minimum": 0, "maximum": 10},
        }
    ],
)
git(repo, "add", ".")
git(repo, "commit", "-m", "Synthetic committed protocol before outputs")
report = {
    "fixture": str(repo.relative_to(ROOT)),
    "scientific_gates": "All real G1-G7 remain untouched; phase guard mocked only for this isolated software fixture",
}
with patch.object(state, "ensure_phase", lambda *_: None):
    report["lock"] = simulation.lock(path)
    report["run"] = simulation.run(path)
    report["resume"] = simulation.run(path)
    report["collect"] = simulation.collect(path)
    report["verify"] = verification.verify(path)
    if report["verify"]["status"] != "PASS":
        raise RuntimeError("Independent verification failed")
    manifest = next((path / "results/runs").glob("*/manifest.json"))
    mf = manifest.relative_to(path).as_posix()
    data = manifest.parent / "metrics.csv"
    raw = np.genfromtxt(data, delimiter=",", names=True)
    claims = [
        {
            "key": key,
            "value": float(raw[column].mean()),
            "unit": "bit/s/Hz",
            "source_manifest": mf,
            "computation": json.dumps(
                {"op": "mean", "path": data.relative_to(path).as_posix(), "column": column}
            ),
            "used_in": ["paper/main.tex Abstract, Results and Discussion"],
        }
        for key, column in [("nomaMean", "noma_sumrate"), ("omaMean", "oma_sumrate")]
    ]
    save(path / "results/claims.json", claims)
    report["claim_validation"] = verification.validate_verification(path)
    report["init"] = paper.init(path)
    tex = (path / "paper/main.tex").read_text(encoding="utf-8")
    tex = tex.replace(
        "This template organizes a telecom study. Replace this paragraph with the\nproblem, method, verified outcome and explicitly bounded scope.",
        r"This synthetic software fixture reports NOMA mean \res{nomaMean} and OMA mean \res{omaMean} bit/s/Hz. It establishes no research novelty.",
    )
    tex = tex.replace(
        "Report only protocol-bound results using the result macro.",
        r"Verified fixture means are \res{nomaMean} and \res{omaMean} bit/s/Hz.\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{figures/cdf.pdf}\caption{Empirical fixture sum-rate CDF under equal normalized budgets.}\end{figure}",
    )
    (path / "paper/main.tex").write_text(tex, encoding="utf-8", newline="\n")
    records = load(ROOT / "tests/fixtures/citation-real-records.yaml")
    citation = citations.verify_bib(
        path / "paper/refs.bib", lambda doi, arxiv: next(r for r in records if r["doi"] == doi)
    )
    save(path / "paper/citation-check.json", citation)
    report["citations"] = citation
    report["trace"] = paper.trace(path)
    spec = {
        "width_inches": 3.5,
        "xlabel": "Sum rate (bit/s/Hz)",
        "ylabel": "Empirical CDF (probability)",
        "output": "figures/cdf.pdf",
        "curves": [
            {
                "manifest": mf,
                "data": (manifest.parent / "cdf.csv").relative_to(path).as_posix(),
                "x": "rate",
                "y": column,
                "label": label,
            }
            for column, label in [("nomacdf", "NOMA"), ("omacdf", "OMA")]
        ],
    }
    save(path / "paper/figures/cdf.yaml", spec)
    report["figure"] = figures.make(path, path / "paper/figures/cdf.yaml")
    (repo / "library/text").mkdir(parents=True)
    source = next(iter((ROOT / ".cache/m3-live-library/text").glob("*.txt")), None)
    if source:
        shutil.copyfile(source, repo / "library/text/recorded-source.txt")
    else:
        (repo / "library/text/synthetic-source.txt").write_text(
            "This self-authored CC0 source sentence serves only as a bounded overlap fixture and contains no original research claims.",
            encoding="utf-8",
            newline="\n",
        )
    report["overlap"] = paper.overlap(path)
    report["build"] = paper.build(path)
    save(
        path / "paper/review.yaml",
        {
            "reviewer": "Deterministic synthetic fixture, not scientific peer review",
            "independent": True,
            "findings_reviewed": True,
            "findings": [],
        },
    )
    (path / "paper/response.md").write_text(
        "# Synthetic test response\nNo scientific review claimed.\n", encoding="utf-8", newline="\n"
    )
    save(path / "ara/trace/sessions/session_index.yaml", [])
    report["disclosure"] = paper.disclosure(path)
    report["export"] = paper.export(path)
handoff = ROOT / "to_human/framework-overleaf-smoke.zip"
handoff.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(report["export"]["zip"], handoff)
conference = repo / "conference-template"
shutil.copytree(ROOT / "templates/paper/conference", conference)
report["conference_template"] = paper.compile_folder(repo, conference)
if report["conference_template"]["status"] != "PASS":
    raise RuntimeError("Conference template failed actual compilation")
if any(value.get("status") == "FAIL" for value in report.values() if isinstance(value, dict)):
    raise RuntimeError("Integration contains a failed check")
summary = {
    "status": "PASS",
    "fixture": report["fixture"],
    "scientific_gates": report["scientific_gates"],
    "tests": {
        name: value.get("status") for name, value in report.items() if isinstance(value, dict)
    },
    "zip": str(handoff.relative_to(ROOT)),
    "zip_sha256": report["export"]["sha256"],
    "remaining": "PI Overleaf upload/confirmation; real research gates not approved",
}
save(ROOT / "docs/evidence/m8-m10-local-integration.json", summary)
save(repo / "full-receipt.json", report)
print(json.dumps(summary))
