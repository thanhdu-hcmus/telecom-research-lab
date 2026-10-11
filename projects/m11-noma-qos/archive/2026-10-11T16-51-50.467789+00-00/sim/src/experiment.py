"""Locked P5 entrypoint. Invocation is exclusively through lab sim run."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import analytic
import numpy as np
import oracle

from lab.io import load, save


def channel_draws(seed, trials):
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, 0])))
    return np.sort(rng.exponential(size=(trials, 2)), axis=1)


def ablations(P, gw, gs, qw, qs):
    fixed = analytic.direct_rates(P, gw, gs, np.full(len(gw), 0.25))
    fixed_ok = (fixed["rw"] >= qw) & (fixed["rs"] >= qs)
    grid_best = np.full(len(gw), np.nan)
    grid_a = np.full(len(gw), np.nan)
    for a in np.linspace(0, 1, 101):
        r = analytic.direct_rates(P, gw, gs, np.full(len(gw), a))
        ok = (r["rw"] >= qw) & (r["rs"] >= qs)
        update = ok & (~np.isfinite(grid_best) | (r["sum_rate"] > grid_best))
        grid_best[update], grid_a[update] = r["sum_rate"][update], a
    return {
        "fixed_feasible": fixed_ok.astype(float),
        "fixed_sum": np.where(fixed_ok, fixed["sum_rate"], np.nan),
        "grid_found_feasible": np.isfinite(grid_best).astype(float),
        "grid_sum": grid_best,
        "grid_a": grid_a,
    }


def csv_file(path, columns):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(zip(*columns.values(), strict=True))


def scalar(value):
    if isinstance(value, dict):
        return {k: scalar(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [scalar(v) for v in value]
    if isinstance(value, np.ndarray):
        return scalar(value.item())
    if isinstance(value, np.generic):
        return scalar(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def run(seed, output_dir, params):
    folder = Path(output_dir)
    n = params["trials"]
    cases = []
    if params["kind"] == "deterministic":
        spec = load(Path(__file__).parents[1] / "cases.yaml")
        cases = spec["cases"] * 5
        values = np.asarray([c["values"] for c in cases], dtype=float)
        P, gw, gs, qw, qs = values.T
        if len(values) != n:
            raise ValueError("Fixed case count differs from protocol")
    else:
        gains = channel_draws(seed, n)
        gw, gs = gains.T
        P, qw, qs = [np.full(n, params[k]) for k in ("P", "qw", "qs")]
    r = analytic.solve(
        P,
        gw,
        gs,
        qw,
        qs,
        rate_tolerance=params["rate_tolerance"],
        split_tolerance=params["split_tolerance"],
    )
    ab = ablations(P, gw, gs, qw, qs)
    raw = {"row": np.arange(n), "P": P, "gw": gw, "gs": gs, "qw": qw, "qs": qs}
    if cases:
        raw["case_id"] = [c["id"] for c in cases]
    raw.update(r)
    raw.update(ab)
    csv_file(folder / "channels.csv", raw)
    metrics = {
        k: r[k] for k in ("feasible", "oma_feasible", "sum_rate", "oma_sum", "paired_difference")
    }
    metrics.update(ab)
    csv_file(folder / "metrics.csv", metrics)
    ledger = {
        k: int(np.sum(r["category"] == k)) for k in ("n00", "n01", "n10", "n11", "unresolved")
    }
    ledger.update(N_total=n, N_resolved=n - ledger["unresolved"])
    save(folder / "ledger.json", ledger)
    count = n if cases else params["oracle_rows"]
    checks = []
    for j in range(count):
        inputs = [float(x[j]) for x in (P, gw, gs, qw, qs)]
        result = oracle.solve(
            *inputs,
            rate_tolerance=params["rate_tolerance"],
            split_tolerance=params["split_tolerance"],
            objective_tolerance=params["objective_tolerance"],
        )
        check = {
            "row": j,
            "inputs": inputs,
            "analytic_status": str(r["status"][j]),
            "analytic_sum": scalar(r["sum_rate"][j]),
            "oracle": result,
        }
        if j < params["sensitivity_rows"]:
            check["tighter_oracle"] = oracle.solve(
                *inputs,
                rate_tolerance=params["rate_tolerance"] / 10,
                split_tolerance=params["split_tolerance"] / 10,
                objective_tolerance=params["objective_tolerance"] / 10,
            )
        checks.append(check)
    save(folder / "oracle.json", scalar({"checks": checks}))
    save(
        folder / "sampling.json",
        {
            "kind": params["kind"],
            "seed": seed,
            "trials": n,
            "bit_generator": "PCG64",
            "seed_sequence_entropy": [seed, 0],
            "stream": "channel" if not cases else "none; fixed cases",
            "channel_law": "sorted iid exponential mean 1" if not cases else "fixed case table",
            "common_grid_draws": True,
            "deterministic_repeats_independent": False,
            "no_noise_or_initialization_stream_required": True,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--params", required=True)
    args = parser.parse_args()
    run(args.seed, args.output_dir, json.loads(args.params))
