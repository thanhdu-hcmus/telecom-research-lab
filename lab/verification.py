"""Independent raw-data recomputation, honest CIs and executable claim lineage."""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, t

from lab.io import LabError, library, load, save, sha256, within
from lab.models import Claim, VerificationItem
from lab.simulation import manifest_output, output_path, protocol, validate_runs, verify_manifest


def evidence_file(path, name):
    if name.startswith("@library/"):
        return within(library(path.parents[1]), name.removeprefix("@library/"))
    if name.startswith("@repo/"):
        return within(path.parents[1], name.removeprefix("@repo/"))
    return within(path, name)


def output_evidence(manifest, filename):
    matches = [o for o in manifest.outputs if Path(o.path).name == filename]
    if len(matches) != 1:
        raise LabError("Missing/ambiguous evidence output")
    o = matches[0]
    return ("@library/" if o.storage == "library" else "") + o.path


def average_ci(values, confidence=0.95):
    a = np.asarray(values, dtype=float)
    if a.size < 2 or not np.all(np.isfinite(a)) or not 0 < confidence < 1:
        raise LabError("Finite independent samples and valid confidence required")
    mean = float(a.mean())
    half = float(t.ppf((1 + confidence) / 2, a.size - 1) * a.std(ddof=1) / np.sqrt(a.size))
    return {
        "mean": mean,
        "low": mean - half,
        "high": mean + half,
        "halfwidth": half,
        "relative_halfwidth": half / max(abs(mean), 1e-12),
        "n": a.size,
        "method": "Student-t; assumes independent draws",
    }


def outage_ci(events, trials, confidence=0.95):
    if (
        type(events) is not int
        or type(trials) is not int
        or not 0 <= events <= trials
        or trials < 1
    ):
        raise LabError("Valid event/trial counts required")
    ci = binomtest(events, trials).proportion_ci(confidence_level=confidence, method="exact")
    return {
        "estimate": events / trials,
        "low": float(ci.low),
        "high": float(ci.high),
        "events": events,
        "trials": trials,
        "conclusive": events >= 100,
        "zero_event_upper_bound": float(ci.high) if events == 0 else None,
    }


def paired_ci(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape:
        raise LabError("Pairwise CI requires matching common-realization arrays")
    return average_ci(a - b)


def bootstrap_ci(values, seed=0, replicates=2000):
    a = np.asarray(values, dtype=float)
    if len(a) < 2 or replicates < 100:
        raise LabError("Insufficient bootstrap samples/replicates")
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(a, size=len(a), replace=True).mean() for _ in range(replicates)])
    low, high = np.quantile(means, [0.025, 0.975])
    return {
        "mean": float(a.mean()),
        "low": float(low),
        "high": float(high),
        "seed": seed,
        "replicates": replicates,
    }


def independent_noma(gains, params):
    """Independent algebra from saved gains; never calls simulator SINR/rates."""
    g = np.asarray(gains)
    rho = params["rho_linear"]
    a = params["a_weak"]
    b = 1 - a
    res = params.get("sic_residual", 0)
    weak = (a * g[:, 0]) / (b * g[:, 0] + 1 / rho)
    decode = (a * g[:, 1]) / (b * g[:, 1] + 1 / rho)
    strong = (b * g[:, 1]) / (res * a * g[:, 1] + 1 / rho)
    return np.column_stack(
        [
            np.log1p(weak) / np.log(2) + np.log1p(strong) / np.log(2),
            (np.log1p(rho * g[:, 0]) + np.log1p(rho * g[:, 1])) / (2 * np.log(2)),
            (weak < np.expm1(params["target_rate_weak"] * np.log(2))).astype(int),
            (
                (decode < np.expm1(params["target_rate_weak"] * np.log(2)))
                | (strong < np.expm1(params["target_rate_strong"] * np.log(2)))
            ).astype(int),
        ]
    )


def verify(path):
    from lab.state import ensure_phase

    ensure_phase(path, "P6")
    validate_runs(path)
    spec = protocol(path)
    items = []
    reports = []
    predictions = load(path / "model/predictions.yaml")
    if not predictions:
        raise LabError("Approved predictions required")
    for manifest_file in sorted((path / "results/runs").glob("*/manifest.json")):
        m = verify_manifest(path, load(manifest_file))
        if spec.get("entrypoint"):
            return custom_verify(path, spec, predictions)
        gains = np.loadtxt(manifest_output(path, m, "channels.csv"), delimiter=",", skiprows=1)
        metrics = np.genfromtxt(manifest_output(path, m, "metrics.csv"), delimiter=",", names=True)
        actual = np.column_stack([metrics[k] for k in metrics.dtype.names])
        expected = independent_noma(gains, m.params)
        if actual.shape != expected.shape:
            raise LabError("Raw metric/channel row mismatch")
        disagreement = float(np.max(np.abs(actual - expected)))
        stats = {
            k: outage_ci(int(metrics[k].sum()), len(metrics))
            if k.endswith("outage")
            else average_ci(metrics[k])
            for k in metrics.dtype.names
        }
        ci_ok = all(
            v["conclusive"]
            if "conclusive" in v
            else v["relative_halfwidth"] <= spec["trial_policy"]["relative_ci_halfwidth"]
            for v in stats.values()
        )
        predictions_here = []
        for pred in predictions:
            # Predictions must name a saved metric and numeric range; no text-only pass.
            tolerance = pred["tolerance"]
            metric = tolerance.get("metric")
            if metric not in stats or "minimum" not in tolerance or "maximum" not in tolerance:
                raise LabError("Prediction tolerance requires metric, minimum and maximum")
            value = stats[metric].get("mean", stats[metric].get("estimate"))
            valid = tolerance["minimum"] <= value <= tolerance["maximum"]
            predictions_here.append({"id": pred["id"], "passed": valid})
            items.append(
                VerificationItem(
                    id=f"{m.run_id}-{pred['id']}",
                    prediction_ref=pred["id"],
                    method="Independent algebra from saved channels, exact binomial/t intervals",
                    metric=metric,
                    value=value,
                    tolerance=tolerance,
                    verdict="PASS"
                    if valid and ci_ok and disagreement < 1e-10
                    else "FAIL"
                    if not valid or disagreement >= 1e-10
                    else "INCONCLUSIVE",
                    triage=None
                    if valid and ci_ok and disagreement < 1e-10
                    else "implementation-bug"
                    if disagreement >= 1e-10
                    else "statistical-noise"
                    if not ci_ok
                    else "theory-error",
                    evidence_paths=[
                        manifest_file.relative_to(path).as_posix(),
                        output_evidence(m, "channels.csv"),
                        output_evidence(m, "metrics.csv"),
                    ],
                ).model_dump(mode="json")
            )
        reports.append(
            {
                "run": m.run_id,
                "max_independent_error": disagreement,
                "statistics": stats,
                "predictions": predictions_here,
            }
        )
    save(path / "analysis/verification.yaml", items)
    receipt = {
        "status": "PASS" if items and all(x["verdict"] == "PASS" for x in items) else "FAIL",
        "runs": reports,
        "input_hashes": {
            p.relative_to(path).as_posix(): sha256(p)
            for p in [
                path / "model/predictions.yaml",
                path / "analysis/verification.yaml",
                *sorted((path / "results/runs").glob("*/*")),
            ]
            if p.is_file()
        },
    }
    save(path / "analysis/verification.json", receipt)
    (path / "analysis/verification-report.md").write_text(
        "# Independent verification\n\n" + json.dumps(receipt, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return receipt


def custom_verify(path, spec, predictions):
    from lab.simulation import locked

    repo = path.parents[1]
    _, lock = locked(path)
    canonical_name = spec.get("verification_entrypoint")
    declared_alias = spec.get("verifier")
    if canonical_name and declared_alias and canonical_name != declared_alias:
        raise LabError("Conflicting verification entrypoint declarations")
    script_name = canonical_name or declared_alias
    if (
        not script_name
        or script_name == spec["entrypoint"]
        or script_name not in lock["input_hashes"]
    ):
        raise LabError(
            "Custom simulations need a distinct independently reviewed verifier pinned in protocol inputs"
        )
    script = within(repo, script_name)
    text = script.read_text(encoding="utf-8")
    if any(token in text for token in ["lab.simkit", Path(spec["entrypoint"]).stem]):
        raise LabError("Independent verifier must not import simulator metric implementation")
    stage = path / "analysis/verifier-output"
    if stage.exists():
        raise LabError(
            "Archive previous custom verifier output before retry; never overwrite evidence"
        )
    stage.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    result = subprocess.run(
        [sys.executable, str(script), "--project", str(path), "--output-dir", str(stage)],
        cwd=stage,
        env=env,
        capture_output=True,
        text=True,
        timeout=3600,
    )
    (stage / "stdout.txt").write_text(result.stdout, encoding="utf-8", newline="\n")
    (stage / "stderr.txt").write_text(result.stderr, encoding="utf-8", newline="\n")
    locked(path)
    validate_runs(path)
    if result.returncode:
        raise LabError("Independent verifier failed; saved logs retained")
    items = load(stage / "verification.yaml")
    checks = load(stage / "checks.yaml")
    required = {
        "independent-recomputation",
        "units",
        "constraints",
        "convergence",
        "fairness",
        "statistical-precision",
        "sensitivity",
        "ablations",
    }
    if set(checks) != required or any(
        not c.get("passed") or not c.get("evidence_paths") for c in checks.values()
    ):
        raise LabError("All custom verification checks need explicit passing evidence")
    for c in checks.values():
        for name in c["evidence_paths"]:
            if not evidence_file(path, name).is_file():
                raise LabError("Custom check refers to missing evidence")
    models = [VerificationItem.model_validate(i) for i in items]
    if (
        not models
        or {p["id"] for p in predictions} != {m.prediction_ref for m in models}
        or any(m.verdict != "PASS" for m in models)
    ):
        raise LabError("Every approved prediction needs a passing independent item")
    save(path / "analysis/verification.yaml", items)
    sources = [
        path / "model/predictions.yaml",
        path / "analysis/verification.yaml",
        script,
        *sorted((path / "results/runs").glob("*/*")),
        *sorted(stage.rglob("*")),
    ]
    report = {
        "status": "PASS",
        "mode": "model-specific independent verifier",
        "verifier": script_name,
        "checks": checks,
        "input_hashes": {
            p.relative_to(path).as_posix()
            if p.is_relative_to(path)
            else "@repo/" + p.relative_to(repo).as_posix(): sha256(p)
            for p in sources
            if p.is_file()
        },
    }
    save(path / "analysis/verification.json", report)
    (path / "analysis/verification-report.md").write_text(
        "# Model-specific independent verification\n\n" + json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def evaluate_claim(path, raw):
    c = Claim.model_validate(raw)
    mf = within(path, c.source_manifest)
    m = verify_manifest(path, load(mf))
    try:
        spec = json.loads(c.computation)
    except json.JSONDecodeError as e:
        raise LabError("Claim computation must be an executable JSON data operation") from e
    matching = [
        o
        for o in m.outputs
        if o.path == spec["path"] and o.storage == spec.get("storage", "project")
    ]
    if len(matching) != 1:
        raise LabError("Claim data must name a unique manifest output")
    target = output_path(path, matching[0])
    if sha256(target) != matching[0].sha256:
        raise LabError("Claim data must be an unchanged manifest output")
    data = np.genfromtxt(target, delimiter=",", names=True)
    values = np.asarray(data[spec["column"]], dtype=float)
    if spec["op"] == "mean":
        value = float(np.mean(values))
    elif spec["op"] == "count":
        value = float(np.sum(values))
    elif spec["op"] == "paired_mean_difference":
        value = float(np.mean(values - data[spec["other_column"]]))
    else:
        raise LabError("Unsupported claim operation")
    if not np.isfinite(value) or not np.isclose(c.value, value, rtol=1e-10, atol=1e-12):
        raise LabError(f"Claim {c.key} does not match raw-data computation")
    return {
        "key": c.key,
        "value": value,
        "manifest_sha256": sha256(mf),
        "data_sha256": sha256(target),
    }


def validate_verification(path):
    validate_runs(path)
    report = load(path / "analysis/verification.json")
    if report.get("status") != "PASS":
        raise LabError("Independent verification must pass")
    for name, digest in report["input_hashes"].items():
        if (
            sha256(
                within(path.parents[1], name.removeprefix("@repo/"))
                if name.startswith("@repo/")
                else within(path, name)
            )
            != digest
        ):
            raise LabError("Verification evidence changed")
    items = load(path / "analysis/verification.yaml")
    if not items:
        raise LabError("Verification items required")
    predictions = {p["id"] for p in load(path / "model/predictions.yaml")}
    if predictions != {item["prediction_ref"] for item in items}:
        raise LabError("Every approved prediction needs verification")
    for raw in items:
        item = VerificationItem.model_validate(raw)
        if item.verdict != "PASS" or item.prediction_ref not in predictions:
            raise LabError("Unresolved/unknown prediction verification")
        for name in item.evidence_paths:
            if not evidence_file(path, name).is_file():
                raise LabError("Missing verification evidence")
    claims = load(path / "results/claims.json")
    if not claims or len({c["key"] for c in claims}) != len(claims):
        raise LabError("Nonempty unique numeric claims required")
    for c in claims:
        evaluate_claim(path, c)
    return {"status": "PASS", "claims": len(claims)}
