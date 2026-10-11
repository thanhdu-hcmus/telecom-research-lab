"""Declared P5 aggregation and published OMA-subset reproduction, no gate action."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import exp1

from lab.io import load, save, sha256
from lab.simulation import manifest_output, validate_runs, verify_manifest
from lab.verification import average_ci, outage_ci


def ci(a):
    a = np.asarray(a, dtype=float)
    return average_ci(a) if len(a) >= 2 else None


def aggregate(project):
    validate_runs(project)
    groups = defaultdict(list)
    oracle_counts = defaultdict(int)
    input_hashes = {}
    oracle_differences = []
    for mf in sorted((project / "results/runs").glob("*/manifest.json")):
        m = verify_manifest(project, load(mf))
        raw = np.genfromtxt(
            manifest_output(project, m, "channels.csv"),
            delimiter=",",
            names=True,
            dtype=None,
            encoding="utf-8",
        )
        groups[m.scenario].append((m, raw))
        input_hashes[mf.relative_to(project).as_posix()] = sha256(mf)
        for row in load(manifest_output(project, m, "oracle.json"))["checks"]:
            o = row["oracle"]
            oracle_counts[o["status"]] += 1
            v = o.get("sum_rate")
            if row["analytic_sum"] is not None and v is not None:
                oracle_differences.append(abs(row["analytic_sum"] - v))
    summary = []
    references = []
    for scenario, runs in sorted(groups.items()):
        data = np.concatenate([r for _, r in runs])
        params = runs[0][0].params
        categories = data["category"]
        counts = {
            k: int(np.sum(categories == k)) for k in ("n00", "n01", "n10", "n11", "unresolved")
        }
        N = len(data)
        resolved = N - counts["unresolved"]
        both = categories == "n11"
        deterministic = params["kind"] == "deterministic"
        sums = {
            k: ci(data[k][both]) if not deterministic else None
            for k in ("sum_rate", "oma_sum", "paired_difference")
        }
        empirical = {}
        if not deterministic and resolved:
            for name, events in (
                ("noma_infeasibility", counts["n00"] + counts["n01"]),
                ("oma_infeasibility", counts["n00"] + counts["n10"]),
                ("oma_only", counts["n01"]),
            ):
                empirical[name] = outage_ci(events, resolved)
        loss = {}
        for method in ("fixed", "grid"):
            joint = (data["status"] == "feasible") & np.isfinite(data[method + "_sum"])
            delta = data["sum_rate"][joint] - data[method + "_sum"][joint]
            loss[method] = {
                "paired_n": len(delta),
                "mean_loss": float(np.mean(delta)) if len(delta) else None,
                "minimum_loss": float(np.min(delta)) if len(delta) else None,
                "found_feasible_count": int(
                    np.sum(data["fixed_feasible" if method == "fixed" else "grid_found_feasible"])
                ),
            }
        rate_precision = (
            {k: bool(v and v["relative_halfwidth"] <= 0.01) for k, v in sums.items()}
            if not deterministic
            else {}
        )
        record = {
            "scenario": scenario,
            "params": params,
            "N_total": N,
            "N_resolved": resolved,
            "counts": counts,
            "paired_denominator": counts["n11"],
            "paired_statistics": sums,
            "rate_precision": rate_precision,
            "event_statistics": empirical,
            "ablations": loss,
            "noma_feasibility_fraction": (counts["n10"] + counts["n11"]) / resolved
            if resolved
            else None,
            "oma_feasibility_fraction": (counts["n01"] + counts["n11"]) / resolved
            if resolved
            else None,
            "negative_paired_count": int(np.sum(data["paired_difference"][both] < -1e-9)),
            "candidate_violation_count": int(np.sum(data["candidate_violation"])),
            "runtime_s": sum(m.runtime_s for m, _ in runs),
            "deterministic_replicates_not_independent": deterministic,
        }
        summary.append(record)
        if not deterministic and params["qw"] == params["qs"] == 0:
            P = params["P"]
            e1, e2 = np.exp(1 / P) * exp1(1 / P), np.exp(2 / P) * exp1(2 / P)
            expected = {"oma_rw": e2 / (2 * np.log(2)), "oma_rs": (2 * e1 - e2) / (2 * np.log(2))}
            actual = {k: ci(data[k]) for k in expected}
            differences = {k: abs(actual[k]["mean"] / v - 1) for k, v in expected.items()}
            references.append(
                {
                    "scenario": scenario,
                    "P_db": params["P_db"],
                    "reference": expected,
                    "actual": actual,
                    "relative_error": differences,
                    "agreement": all(x <= 0.05 for x in differences.values()),
                }
            )
    references.sort(key=lambda x: x["P_db"])
    ordering = all(
        x["actual"]["oma_rs"]["mean"] > x["actual"]["oma_rw"]["mean"] for x in references
    )
    trend = all(
        all(
            references[j + 1]["actual"][k]["mean"] > references[j]["actual"][k]["mean"]
            for j in range(len(references) - 1)
        )
        for k in ("oma_rw", "oma_rs")
    )
    output = {
        "status": "computed; independent P6 verification pending",
        "input_manifest_hashes": input_hashes,
        "scenarios": summary,
        "oracle_status_counts": dict(oracle_counts),
        "maximum_oracle_sum_difference": max(oracle_differences, default=None),
        "baseline_reproduction": {
            "source": "TVT2017 Fair-NOMA Figure1 OMA subset; eq6-8",
            "points": references,
            "ordering": ordering,
            "trend": trend,
            "agreement": len(references) == 6
            and ordering
            and trend
            and all(x["agreement"] for x in references),
        },
    }
    save(project / "results/statistics.json", output)
    fig, ax = plt.subplots(figsize=(8, 5))
    x = [r["P_db"] for r in references]
    for k, label, color in [("oma_rw", "Weak OMA", "#b54732"), ("oma_rs", "Strong OMA", "#2363a2")]:
        ax.plot(
            x,
            [r["reference"][k] for r in references],
            color=color,
            label=label + " published equation",
        )
        ax.errorbar(
            x,
            [r["actual"][k]["mean"] for r in references],
            yerr=[r["actual"][k]["halfwidth"] for r in references],
            fmt="o",
            capsize=4,
            color=color,
            label=label + " MC, 95% CI",
        )
    ax.set(
        xlabel="Normalized transmit SNR (dB)",
        ylabel="Rate (bit/s/Hz)",
        title="Fair-NOMA Figure 1: reproduction of OMA curves only",
    )
    ax.grid(alpha=0.25)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(project / "results/oma-reference-overlay.svg")
    fig.savefig(project.parents[1] / ".cache/m11-oma-overlay.png", dpi=150)
    plt.close(fig)
    print(
        {
            "scenarios": len(summary),
            "blocks": sum(r["N_total"] for r in summary),
            "baseline_agreement": output["baseline_reproduction"]["agreement"],
            "oracle_status_counts": output["oracle_status_counts"],
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    aggregate(parser.parse_args().project.resolve())
