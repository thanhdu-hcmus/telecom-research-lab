"""Disposable corruption tests; no canonical checker/native verification calls."""

import copy
import importlib.util
import json
import math
import os
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checker
import independent as ind
import replay
import run_unit_tests as runner
from independent import OBJECTIVE, RATE, SPLIT, Audit, rates
from replay import check_oracle_original, load_shared, recursive_compare, replay_job


def fixture(inputs=(1.0, 1.0, 4.0, 0.0, 0.0)):
    v = list(inputs)
    ns = ind.noma_adjudicate(v)
    os = ind.oma_adjudicate(v)
    status = ns["status"]
    feasible = status == "feasible"
    raw = {k: "" for k in ind.CHANNEL_COLUMNS}
    raw.update(dict(zip(("P", "gw", "gs", "qw", "qs"), map(str, v))))
    raw.update(
        row="0",
        case_id="fixture",
        status=status,
        feasible=str(float(feasible)) if status != "unresolved" else "nan",
        certificate="none" if status == "unresolved" else "binary64-separated",
        A=str(v[0] * v[1]),
        B=str(v[0] * v[2]),
        exact_split="",
        boundary_flag=str(ns["low"] is not None and abs(ns["high"] - ns["low"]) <= ind.SPLIT),
        numeric_domain="True",
        candidate_violation="False",
        singleton=str(ns.get("singleton", False)),
        optimizer_unique=str(feasible and (v[1] != v[2] or ns.get("singleton", False))),
        nonunique=str(feasible and v[1] == v[2] and not ns.get("singleton", False)),
        oma_status=os,
        oma_feasible=str(float(os == "feasible")) if os != "unresolved" else "nan",
        oma_certificate="none" if os == "unresolved" else "binary64-separated",
    )
    # Boundary fields for fixtures selected to have a resolved full-domain bracket.
    raw["interval_lower"] = str(ns["low"] if ns["low"] is not None else 0.0)
    raw["interval_upper"] = str(ns["high"] if ns["high"] is not None else 1.0)
    od = ind.oma(v)
    raw.update({k: str(x) for k, x in od.items()})
    raw["oma_boundary_flag"] = str(
        any(
            q > 0 and abs(od[k]) <= ind.RATE
            for q, k in zip(v[3:], ("oma_residual_w", "oma_residual_s"))
        )
    )
    raw["category"] = ind.category(status, os)
    if feasible:
        a = ns["high"]
        rd = ind.rates(v, a)
        raw["a_star"] = raw["candidate_a"] = str(a)
        for k, x in rd.items():
            raw[k] = raw["candidate_" + k] = str(x)
        raw.update(
            residual_w=str(rd["rw"] - v[3]),
            residual_s=str(rd["rs"] - v[4]),
            sic_residual=str(rd["cw_at_s"] - rd["rw"]),
        )
        raw["candidate_constraints_pass"] = str(rd["rw"] >= v[3] and rd["rs"] >= v[4])
        raw["candidate_within_rate_tolerance"] = "True"
        raw["paired_difference"] = (
            str(rd["sum_rate"] - od["oma_sum"]) if raw["category"] == "n11" else "nan"
        )
    else:
        for k in ind.FIELDS:
            raw[k] = raw["candidate_" + k] = "nan"
        for k in (
            "a_star",
            "candidate_a",
            "residual_w",
            "residual_s",
            "sic_residual",
            "paired_difference",
        ):
            raw[k] = "nan"
        raw["candidate_constraints_pass"] = raw["candidate_within_rate_tolerance"] = "False"
    ab = ind.ablations(v)
    for k in ("fixed_feasible", "fixed_sum", "grid_found_feasible", "grid_sum"):
        raw[k] = str(ab[k])
    raw["grid_a"] = str(ab["grid_ties"][0]) if ab["grid_ties"] else "nan"
    metric = {k: raw[k] for k in ind.METRIC_COLUMNS}
    return raw, metric


def audit_fixture(raw, metric, inputs=(1.0, 1.0, 4.0, 0.0, 0.0)):
    audit = ind.Audit()
    ind.check_row(raw, metric, list(inputs), "fixture", 0, audit)
    return audit


class PhysicsTests(unittest.TestCase):
    def test_original_powers_sites(self):
        r = ind.rates((2, 1, 4, 0, 0), 0.25)
        self.assertEqual(r["gamma_ww"], 1.0)
        self.assertEqual(r["gamma_ws"], 2.0)
        self.assertEqual(r["gamma_ss"], 2.0)
        self.assertEqual(r["rw_site"], 1.0)
        self.assertAlmostEqual(r["cw_at_s"], math.log2(3))
        self.assertEqual(ind.oma((1, 3, 3, 0, 0))["oma_rw"], 1.0)

    def test_invalid_inputs_and_splits(self):
        for inputs in [
            (1, 2, 1, 0, 0),
            (float("nan"), 1, 2, 0, 0),
            (1, -1, 2, 0, 0),
            (1, 1, 2, -1, 0),
            (1e300, 1e300, 1e300, 0, 0),
        ]:
            with self.assertRaises(ValueError):
                ind.rates(inputs, 0.25)
        for split in (-0.001, 1.001, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                ind.rates((1, 1, 2, 0, 0), split)

    def test_exact_singletons_and_narrow_cases(self):
        self.assertEqual(ind.noma_adjudicate((1, 3, 9, 1, 2))["exact_high"], "1/3")
        self.assertTrue(ind.noma_adjudicate((1, 3, 9, 1, 2))["singleton"])
        self.assertEqual(ind.noma_adjudicate((1, 3, 9.000000000001, 1, 2))["status"], "feasible")
        self.assertEqual(ind.noma_adjudicate((1, 3, 8.999999999999, 1, 2))["status"], "infeasible")

    def test_zero_equal_and_fractional_boundary(self):
        for inputs, status in [
            ((0, 1, 2, 0, 0), "feasible"),
            ((0, 1, 2, 1, 0), "infeasible"),
            ((1, 0, 0, 0, 0), "feasible"),
            ((1, 0, 4, 0, 1), "feasible"),
            ((1, 0, 4, 0.5, 1), "infeasible"),
            ((1, 1, 1, 0.5, 0.5), "unresolved"),
        ]:
            self.assertEqual(ind.noma_adjudicate(inputs)["status"], status)
        self.assertEqual(ind.oma_adjudicate((1, 1, 1, 0.5, 0.5)), "unresolved")
        self.assertEqual(ind.oma_adjudicate((1, 3, 3, 1, 1)), "feasible")
        self.assertEqual(ind.oma_adjudicate((1, 3, 3.000000000001, 1, 1)), "feasible")
        self.assertEqual(ind.oma_adjudicate((1, 2.999999999999, 3, 1, 1)), "infeasible")

    def test_bracket_not_grid_miss(self):
        n = ind.noma_adjudicate((1, 3, 9, 1, 2))
        self.assertEqual(n["status"], "feasible")
        self.assertEqual(ind.ablations((1, 3, 9, 1, 2))["grid_found_feasible"], 0.0)
        self.assertEqual(ind.exact_residuals((1, 3, 9, 1, 2))(Fraction(1, 3)), (0, Fraction(2), 0))

    def test_vector_grid_matches_original_scalar_exhaustive_search(self):
        cases = [(0, 1, 2, 0, 0), (1, 3, 9, 1, 2), (1, 4, 4, 0.5, 0.5), (1, 1e100, 2e100, 1, 1)]
        cases.extend((10.0, float(gw), float(gs), 0.25, 0.25) for gw, gs in ind.seeded(11001, 16))
        for inputs in cases:
            valid = []
            for i in range(101):
                r = ind.rates(inputs, i / 100)
                if r["rw"] >= inputs[3] and r["rs"] >= inputs[4]:
                    valid.append((i / 100, r["sum_rate"]))
            result = ind.ablations(inputs)
            self.assertEqual(bool(result["grid_found_feasible"]), bool(valid))
            if valid:
                best = max(r for a, r in valid)
                self.assertLessEqual(abs(result["grid_sum"] - best), ind.OBJECTIVE)
                self.assertTrue(
                    all(
                        any(a == s and abs(r - best) <= ind.OBJECTIVE for s, r in valid)
                        for a in result["grid_ties"]
                    )
                )

    def test_seed_and_shared_settings(self):
        gains = ind.seeded(11001, 2)
        self.assertEqual(gains[0].tolist(), [0.3557646508449167, 1.1182434120044833])
        self.assertEqual(gains.tolist(), ind.seeded(11001, 2).tolist())
        self.assertNotEqual(gains.tolist(), ind.seeded(11002, 2).tolist())

    def test_oma_published_equations_six_points(self):
        previous = 0
        for P in (1, 10, 100, 1000, 10000, 100000):
            r = ind.reference(P)
            self.assertGreater(r["strong"], r["weak"])
            self.assertGreater(r["weak"], previous)
            self.assertAlmostEqual(r["sum"], r["weak"] + r["strong"])
            previous = r["weak"]
        self.assertAlmostEqual(ind.reference(1)["weak"], 0.2606435018579535)
        self.assertAlmostEqual(ind.reference(1)["strong"], 0.5997038804129333)


class CorruptionTests(unittest.TestCase):
    def test_fixture_clean(self):
        raw, metric = fixture()
        self.assertEqual(audit_fixture(raw, metric).counts, {})

    def test_every_numeric_field_compensation(self):
        raw, metric = fixture()
        for field in ind.FIELDS:
            for prefix in ("", "candidate_"):
                r, m = copy.deepcopy(raw), copy.deepcopy(metric)
                r[prefix + field] = str(float(r[prefix + field]) + 0.2)
                if field == "sum_rate":
                    m[field] = r[field]
                a = audit_fixture(r, m)
                self.assertIn(
                    prefix + field + (".implied_rate" if field.startswith("gamma_") else ""),
                    a.counts,
                    (field, a.counts),
                )
        r, m = fixture()
        r["rw"] = str(float(r["rw"]) + 0.1)
        r["rs"] = str(float(r["rs"]) - 0.1)
        a = audit_fixture(r, m)
        self.assertIn("rw", a.counts)
        self.assertIn("rs", a.counts)

    def test_residuals_and_paired(self):
        for key in (
            "residual_w",
            "residual_s",
            "sic_residual",
            "oma_residual_w",
            "oma_residual_s",
            "paired_difference",
        ):
            r, m = fixture()
            r[key] = str(float(r[key]) + 0.2)
            if key in m:
                m[key] = r[key]
            self.assertIn(key, audit_fixture(r, m).counts)

    def test_bad_oma_coherent_bits_and_category(self):
        r, m = fixture()
        r["oma_status"] = "infeasible"
        r["oma_feasible"] = m["oma_feasible"] = "0.0"
        r["category"] = "n10"
        r["paired_difference"] = m["paired_difference"] = "nan"
        a = audit_fixture(r, m)
        self.assertIn("oma.status", a.counts)
        self.assertIn("independent.category", a.counts)

    def test_row_ids_metrics_alignment(self):
        r, m = fixture()
        r["row"] = "1"
        m["oma_sum"] = "100"
        a = audit_fixture(r, m)
        self.assertIn("row", a.counts)
        self.assertIn("metrics.oma_sum", a.counts)

    def test_seed_gain_corruption(self):
        r, m = fixture()
        r["gw"] = "1.1"
        a = audit_fixture(r, m)
        self.assertIn("gw", a.counts)
        self.assertIn("A", a.counts)

    def test_illegal_splits_and_nans(self):
        for key in ("a_star", "candidate_a", "gamma_ww", "oma_rw", "sum_rate", "grid_sum"):
            r, m = fixture()
            r[key] = "nan" if key not in ("a_star", "candidate_a") else "1.1"
            if key in m:
                m[key] = r[key]
            self.assertFalse(audit_fixture(r, m).ok(), key)

    def test_undefined_zero_substitution(self):
        r, m = fixture((1.0, 3.0, 9.0, 1.0, 2.0))
        self.assertEqual(r["category"], "n10")
        r["paired_difference"] = m["paired_difference"] = "0"
        self.assertIn("paired_difference", audit_fixture(r, m, (1.0, 3.0, 9.0, 1.0, 2.0)).counts)

    def test_bad_rational_witness(self):
        r, m = fixture((1.0, 3.0, 9.0, 1.0, 2.0))
        r["exact_split"] = "1/2"
        a = audit_fixture(r, m, (1.0, 3.0, 9.0, 1.0, 2.0))
        self.assertIn("exact_split.witness", a.counts)

    def test_fixed_and_grid_fields(self):
        for key in ("fixed_feasible", "fixed_sum", "grid_found_feasible", "grid_sum"):
            r, m = fixture()
            r[key] = m[key] = str(float(r[key]) + 0.1)
            self.assertIn(key, audit_fixture(r, m).counts)
        r, m = fixture()
        r["grid_a"] = m["grid_a"] = "0.999"
        self.assertIn("grid_a", audit_fixture(r, m).counts)
        r, m = fixture((1.0, 3.0, 9.0, 1.0, 2.0))
        r["grid_found_feasible"] = m["grid_found_feasible"] = "1"
        self.assertIn("grid_found_feasible", audit_fixture(r, m, (1.0, 3.0, 9.0, 1.0, 2.0)).counts)

    def test_boundary_and_status_indicators(self):
        for key in ("feasible", "oma_feasible"):
            r, m = fixture()
            r[key] = m[key] = "0"
            self.assertIn(key, audit_fixture(r, m).counts)
        r, m = fixture()
        r["interval_upper"] = ".5"
        r["boundary_flag"] = "True"
        a = audit_fixture(r, m)
        self.assertIn("interval_upper.original_crossing", a.counts)
        self.assertIn("boundary_flag", a.counts)

    def test_mask_and_undefined_cannot_pass(self):
        a = ind.Audit()
        a.close("finite", float("nan"), 1)
        a.close("undefined", 0, float("nan"))
        self.assertEqual(set(a.counts), {"finite", "undefined"})

    def test_category_identity(self):
        r, m = fixture()
        r["category"] = "n00"
        self.assertIn("category", audit_fixture(r, m).counts)


class StatisticsTests(unittest.TestCase):
    def test_streaming_moments_and_student_t(self):
        m = ind.Moments()
        for x in (1, 2, 3, 4):
            m.add(x)
        s = m.summary()
        self.assertEqual(s["n"], 4)
        self.assertEqual(s["mean"], 2.5)
        self.assertAlmostEqual(s["variance"], 5 / 3)
        self.assertAlmostEqual(s["halfwidth"], 2.054260256760879, places=9)
        self.assertIsNone(m.summary(True)["ci95"])
        with self.assertRaises(ValueError):
            m.add(float("nan"))

    def test_undefined_and_exact_binomial_semantics(self):
        self.assertIsNone(ind.Moments().summary()["mean"])
        m = ind.Moments()
        m.add(0)
        self.assertIsNone(m.summary()["relative_halfwidth"])
        b = ind.binomial(0, 100)
        self.assertEqual(b["estimate"], 0)
        self.assertAlmostEqual(b["zero_event_upper_bound"], 1 - 0.025**0.01)
        self.assertFalse(b["minimum_events_met"])
        self.assertTrue(ind.binomial(100, 1000)["minimum_events_met"])
        for k, n in ((1, 0), (-1, 100), (101, 100)):
            with self.assertRaises(ValueError):
                ind.binomial(k, n)

    def test_bad_ci_and_paired_denominator(self):
        m = ind.Moments()
        for x in (1, 2, 3, 4):
            m.add(x)
        good = dict(
            mean=2.5,
            low=0.445739743239121,
            high=4.554260256760879,
            halfwidth=2.054260256760879,
            relative_halfwidth=0.8217041027043516,
            n=4,
        )
        a = ind.Audit()
        checker.compare_moments(a, "ci", good, m)
        self.assertTrue(a.ok(), a.counts)
        bad = copy.deepcopy(good)
        bad["n"] = 100
        bad["low"] = 1
        bad["high"] = 2
        a = ind.Audit()
        checker.compare_moments(a, "ci", bad, m)
        self.assertIn("ci.n", a.counts)
        self.assertIn("ci.low", a.counts)
        self.assertIn("ci.high", a.counts)
        a = ind.Audit()
        checker.compare_moments(a, "deterministic", good, m, True)
        self.assertFalse(a.ok())

    def test_empty_missing_duplicate_jobs(self):
        spec = {"scenarios": [{"id": "mc", "seeds": list(range(145)), "params": {"trials": 100}}]}
        manifests = [dict(scenario="mc", seeds=[i], params={"trials": 100}) for i in range(145)]
        ind.check_jobs(manifests, spec)
        for bad in ([], manifests[:-1], manifests[:-1] + [manifests[0]]):
            with self.assertRaises(ValueError):
                ind.check_jobs(bad, spec)
        bad = copy.deepcopy(manifests)
        bad[0]["params"]["trials"] = 101
        with self.assertRaises(ValueError):
            ind.check_jobs(bad, spec)


class ReplayTests(unittest.TestCase):
    def sample(self):
        raw, _ = fixture()
        params = dict(
            oracle_rows=1,
            sensitivity_rows=1,
            rate_tolerance=1e-9,
            split_tolerance=1e-12,
            objective_tolerance=1e-7,
        )

        def solve(*inputs, **kw):
            return oracle_fixture(inputs, 1.0, "feasible", **kw)

        inputs = [1.0, 1.0, 4.0, 0.0, 0.0]
        checks = [
            dict(
                row=0,
                inputs=inputs,
                analytic_status=raw["status"],
                analytic_sum=float(raw["sum_rate"]),
                oracle=solve(
                    *inputs,
                    rate_tolerance=1e-9,
                    split_tolerance=1e-12,
                    objective_tolerance=1e-7,
                    max_root_iterations=96,
                    max_optimizer_iterations=256,
                ),
                tighter_oracle=solve(
                    *inputs,
                    rate_tolerance=1e-10,
                    split_tolerance=1e-13,
                    objective_tolerance=1e-8,
                    max_root_iterations=96,
                    max_optimizer_iterations=256,
                ),
            )
        ]
        return checks, [raw], params, solve

    def test_replay_clean_and_missing_tighter(self):
        c, r, p, s = self.sample()
        a = ind.Audit()
        result = replay.replay_job(c, r, p, s, a)
        self.assertTrue(a.ok(), a.counts)
        self.assertEqual(result["base"], 1)
        self.assertEqual(result["tighter"], 1)
        del c[0]["tighter_oracle"]
        a = ind.Audit()
        replay.replay_job(c, r, p, s, a)
        self.assertIn("oracle.missing.tighter_oracle", a.counts)

    def test_replay_bad_input_coverage_caps_and_certificates(self):
        c, r, p, s = self.sample()
        c[0]["inputs"][0] = 2
        c[0]["oracle"]["max_root_iterations"] = 97
        c[0]["oracle"]["feasibility_certificate"] = "bad"
        a = ind.Audit()
        replay.replay_job(c, r, p, s, a)
        for k in ("oracle.inputs", "oracle.max_root_iterations", "oracle.feasibility_certificate"):
            self.assertIn(k, a.counts)
        c, r, p, s = self.sample()
        c[0]["row"] = 1
        a = ind.Audit()
        replay.replay_job(c, r, p, s, a)
        self.assertIn("oracle.coverage", a.counts)

    def test_tighter_comparison_uses_tighter_policy(self):
        c, r, p, s = self.sample()
        c[0]["tighter_oracle"]["rw"] += 5e-10
        a = ind.Audit()
        replay.replay_job(c, r, p, s, a)
        self.assertIn("tighter_oracle.rw", a.counts)

    def test_replay_compensating_rates_and_mask(self):
        c, r, p, s = self.sample()
        c[0]["oracle"]["rw"] += 1
        c[0]["oracle"]["rs"] -= 1
        a = ind.Audit()
        replay.replay_job(c, r, p, s, a)
        self.assertIn("oracle.rw", a.counts)
        self.assertIn("oracle.rs", a.counts)
        c, r, p, s = self.sample()
        c[0]["oracle"]["sum_rate"] = float("nan")
        a = ind.Audit()
        replay.replay_job(c, r, p, s, a)
        self.assertIn("oracle.sum_rate", a.counts)


class StructuralTests(unittest.TestCase):
    def test_disposable_csv_empty_missing_duplicate_and_schema(self):
        import csv
        import json
        import tempfile
        from types import SimpleNamespace

        c, rows, params, solve = ReplayTests().sample()
        params.update(kind="deterministic", trials=1)
        raw, metric = fixture()
        sampling = dict(
            kind="deterministic",
            seed=11999,
            trials=1,
            bit_generator="PCG64",
            seed_sequence_entropy=[11999, 0],
            stream="none; fixed cases",
            channel_law="fixed case table",
            common_grid_draws=True,
            deterministic_repeats_independent=False,
            no_noise_or_initialization_stream_required=True,
        )
        with tempfile.TemporaryDirectory(
            dir=os.environ.get("TASK_PHYSICS_TEST_TMP", str(Path(__file__).parent))
        ) as tmp:
            root = Path(tmp)

            def write_rows(name, columns, data):
                with (root / name).open("w", encoding="utf8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(data)

            write_rows("channels.csv", ind.CHANNEL_COLUMNS, [raw])
            write_rows("metrics.csv", ind.METRIC_COLUMNS, [metric])
            (root / "sampling.json").write_text(json.dumps(sampling), encoding="utf8")
            (root / "ledger.json").write_text(
                json.dumps(dict(n00=0, n01=0, n10=0, n11=1, unresolved=0, N_total=1, N_resolved=1)),
                encoding="utf8",
            )
            (root / "oracle.json").write_text(json.dumps(dict(checks=c)), encoding="utf8")
            manifest = SimpleNamespace(
                params=params,
                seeds=[11999],
                run_id="unit",
                runtime_s=0.0,
                outputs=[
                    SimpleNamespace(path=name, storage="project")
                    for name in (
                        "channels.csv",
                        "metrics.csv",
                        "sampling.json",
                        "ledger.json",
                        "oracle.json",
                    )
                ],
            )

            def run():
                import io

                audit = ind.Audit()
                record = checker.process_job(
                    root,
                    manifest,
                    [dict(values=[1, 1, 4, 0, 0], id="fixture")],
                    checker.init_scenario(),
                    audit,
                    solve,
                    60,
                    io.StringIO(),
                )
                return record, audit

            record, a = run()
            self.assertTrue(a.ok(), a.counts)
            self.assertEqual(record["rows"], 1)
            (root / "ledger.json").write_text(json.dumps(dict(n00=1)), encoding="utf8")
            self.assertIn("ledger", run()[1].counts)
            write_rows("metrics.csv", ind.METRIC_COLUMNS, [])
            with self.assertRaisesRegex(ValueError, "alignment"):
                run()
            write_rows("channels.csv", ind.CHANNEL_COLUMNS, [])
            with self.assertRaisesRegex(ValueError, "empty"):
                run()
            write_rows("channels.csv", ind.CHANNEL_COLUMNS, [raw, raw])
            write_rows("metrics.csv", ind.METRIC_COLUMNS, [metric, metric])
            with self.assertRaisesRegex(ValueError, "extra row"):
                run()
            write_rows("channels.csv", ind.CHANNEL_COLUMNS, [raw])
            write_rows("metrics.csv", list(reversed(ind.METRIC_COLUMNS)), [metric])
            self.assertIn("metrics.schema", run()[1].counts)

    def test_bad_event_counts_denominators_and_unresolved(self):
        s = checker.init_scenario()
        raw, metric = fixture()
        checked = ind.check_row(raw, metric, [1, 1, 4, 0, 0], "fixture", 0, ind.Audit())
        for _ in range(4):
            checker.update(s, raw, checked)
        scenario = dict(id="unit", params=dict(kind="monte-carlo"))

        def mom(m):
            v = m.summary()
            return dict(
                mean=v["mean"],
                low=v["ci95"][0],
                high=v["ci95"][1],
                halfwidth=v["halfwidth"],
                relative_halfwidth=v["relative_halfwidth"],
                n=v["n"],
            )

        events = {}
        for k in ("noma_infeasibility", "oma_infeasibility", "oma_only"):
            b = ind.binomial(0, 4)
            events[k] = dict(
                events=0,
                trials=4,
                conclusive=False,
                estimate=0,
                low=0,
                high=b["ci95"][1],
                zero_event_upper_bound=b["zero_event_upper_bound"],
            )
        old = dict(
            N_total=4,
            N_resolved=4,
            counts=dict(n00=0, n01=0, n10=0, n11=4, unresolved=0),
            paired_denominator=4,
            paired_statistics={k: mom(m) for k, m in s["pairs"].items()},
            rate_precision={k: True for k in s["pairs"]},
            event_statistics=events,
            ablations={
                k: dict(
                    paired_n=4,
                    found_feasible_count=4,
                    mean_loss=s["loss"][k].mean,
                    minimum_loss=s["min_loss"][k],
                )
                for k in ("fixed", "grid")
            },
            noma_feasibility_fraction=1.0,
            oma_feasibility_fraction=1.0,
            negative_paired_count=0,
            candidate_violation_count=0,
            params=scenario["params"],
            deterministic_replicates_not_independent=False,
        )
        a = ind.Audit()
        checker.compare_scenario(a, old, s, scenario)
        self.assertTrue(a.ok(), a.counts)
        for field, value in (
            ("events", 100),
            ("trials", 100),
            ("conclusive", True),
            ("zero_event_upper_bound", 0.0),
            ("low", 0.5),
            ("high", 0.5),
        ):
            bad = copy.deepcopy(old)
            bad["event_statistics"]["noma_infeasibility"][field] = value
            a = ind.Audit()
            checker.compare_scenario(a, bad, s, scenario)
            self.assertIn("statistics.events.noma_infeasibility." + field, a.counts)
        bad = copy.deepcopy(old)
        bad["counts"]["unresolved"] = 1
        bad["paired_denominator"] = 3
        a = ind.Audit()
        checker.compare_scenario(a, bad, s, scenario)
        self.assertIn("statistics.counts.unresolved", a.counts)
        self.assertIn("statistics.paired_denominator", a.counts)

    def test_oma_reference_corrupt_equation_and_missing_point(self):
        spec = {"scenarios": []}
        scenarios = {}
        points = []
        for db in (0, 10, 20, 30, 40, 50):
            name = f"mc-{db:02d}-q0"
            ref = ind.reference(10 ** (db / 10))
            sc = dict(id=name, params=dict(P_db=db, P=10 ** (db / 10), qw=0, qs=0))
            spec["scenarios"].append(sc)
            s = checker.init_scenario()
            scenarios[name] = s
            actual = {}
            for k, r in (("oma_rw", ref["weak"]), ("oma_rs", ref["strong"])):
                s["reference"][k].add(r - 0.01)
                s["reference"][k].add(r + 0.01)
                v = s["reference"][k].summary()
                actual[k] = dict(
                    mean=v["mean"],
                    low=v["ci95"][0],
                    high=v["ci95"][1],
                    halfwidth=v["halfwidth"],
                    relative_halfwidth=v["relative_halfwidth"],
                    n=2,
                )
            points.append(
                dict(
                    scenario=name,
                    P_db=db,
                    reference=dict(oma_rw=ref["weak"], oma_rs=ref["strong"]),
                    actual=actual,
                    relative_error=dict(oma_rw=0, oma_rs=0),
                    agreement=True,
                )
            )
        old = dict(points=points, ordering=True, trend=True, agreement=True)
        a = ind.Audit()
        checker.compare_reference(a, old, scenarios, spec)
        self.assertTrue(a.ok(), a.counts)
        bad = copy.deepcopy(old)
        bad["points"][0]["reference"]["oma_rw"] *= 2
        a = ind.Audit()
        checker.compare_reference(a, bad, scenarios, spec)
        self.assertIn("reference.equation.oma_rw", a.counts)
        bad = copy.deepcopy(old)
        bad["points"].pop()
        a = ind.Audit()
        checker.compare_reference(a, bad, scenarios, spec)
        self.assertIn("reference.coverage", a.counts)


class PolicyRegressionTests(unittest.TestCase):
    def test_zero_capacity_tiny_positive_targets_are_exactly_infeasible(self):
        for v in (
            (0.0, 1.0, 2.0, 1e-12, 0.0),
            (0.0, 1.0, 2.0, 0.0, 1e-12),
            (1.0, 0.0, 4.0, 1e-12, 0.0),
            (1.0, 0.0, 0.0, 0.0, 1e-12),
        ):
            self.assertEqual(ind.noma_adjudicate(v)["status"], "infeasible")
            self.assertEqual(ind.oma_adjudicate(v), "infeasible")

    def test_attempted_candidate_for_undefined_optimum(self):
        inputs = (1.0, 1.0, 1.0, 0.5, 0.5)
        raw, metric = fixture(inputs)
        a = 0.25
        cr = ind.rates(inputs, a)
        raw["candidate_a"] = str(a)
        for k, v in cr.items():
            raw["candidate_" + k] = str(v)
        raw["candidate_constraints_pass"] = "False"
        raw["candidate_within_rate_tolerance"] = "False"
        raw["candidate_violation"] = "True"
        audit = audit_fixture(raw, metric, inputs)
        self.assertTrue(audit.ok(), audit.counts)
        raw["candidate_rs"] = "1"
        self.assertIn("candidate_rs", audit_fixture(raw, metric, inputs).counts)

    def test_dimensionless_sinr_uses_implied_rate_and_retains_raw_difference(self):
        audit = ind.Audit()
        audit.sinr("huge", 1e100 + 1e88, 1e100)
        self.assertTrue(audit.ok())
        self.assertIn("huge", audit.diagnostic_counts)
        audit.sinr("bad", 4, 1)
        self.assertIn("bad.implied_rate", audit.counts)

    def test_negative_pair_uses_rate_policy(self):
        self.assertTrue(ind.negative_pair(-2e-9))
        self.assertFalse(ind.negative_pair(-5e-10))
        inputs = (1.0, 4.0, 4.0, 0.0, 0.0)
        raw, metric = fixture(inputs)
        raw["paired_difference"] = metric["paired_difference"] = "-5e-9"
        audit = audit_fixture(raw, metric, inputs)
        self.assertIn("negative_paired_difference", audit.counts)

    def test_undefined_replay_nan_is_only_a_declared_null_mask(self):
        audit = ind.Audit()
        replay.recursive_compare(audit, "oracle.a_star", None, float("nan"), 0, undefined=True)
        self.assertTrue(audit.ok())
        replay.recursive_compare(
            audit, "oracle.rate_tolerance", None, float("nan"), 0, undefined=True
        )
        self.assertIn("oracle.rate_tolerance", audit.counts)


def review_original_rates(inputs, a):
    """Test-only physics derived directly from the approved receiver equations."""
    P, gw, gs, _, _ = inputs
    weak_power, strong_power = P * (1 - a), P * a
    ww = weak_power * gw / (1 + strong_power * gw)
    ws = weak_power * gs / (1 + strong_power * gs)
    ss = strong_power * gs
    rw_site, cw_at_s, rs = map(lambda x: math.log2(1 + x), (ww, ws, ss))
    rw = min(rw_site, cw_at_s)
    return dict(
        gamma_ww=ww,
        gamma_ws=ws,
        gamma_ss=ss,
        rw_site=rw_site,
        cw_at_s=cw_at_s,
        rw=rw,
        rs=rs,
        sum_rate=rw + rs,
    )


def review_rewrite_final(raw, metric, inputs, a):
    """Make a coherent scientific corruption, rather than just changing a flag."""
    r = review_original_rates(inputs, a)
    raw["a_star"] = raw["candidate_a"] = str(a)
    for k, value in r.items():
        raw[k] = raw["candidate_" + k] = str(value)
    raw["residual_w"] = str(r["rw"] - inputs[3])
    raw["residual_s"] = str(r["rs"] - inputs[4])
    raw["sic_residual"] = str(r["cw_at_s"] - r["rw"])
    raw["candidate_constraints_pass"] = str(r["rw"] >= inputs[3] and r["rs"] >= inputs[4])
    raw["candidate_within_rate_tolerance"] = str(
        r["rw"] >= inputs[3] - ind.RATE and r["rs"] >= inputs[4] - ind.RATE
    )
    raw["candidate_violation"] = str(min(r["rw"] - inputs[3], r["rs"] - inputs[4]) < -ind.RATE)
    if raw["category"] == "n11":
        # Independent matched OMA half-block rates, without the production helper.
        oma_sum = sum(math.log2(1 + inputs[0] * g) / 2 for g in inputs[1:3])
        raw["paired_difference"] = str(r["sum_rate"] - oma_sum)
    for k in ind.METRIC_COLUMNS:
        metric[k] = raw[k]


class ReviewPhysicsRepairTests(unittest.TestCase):
    def test_F04_accepts_two_representations_of_index_69(self):
        inputs = (1.0, 4.0, 4.0, 0.0, 0.0)
        for split in (0.69, 0.6900000000000001):
            with self.subTest(split=split):
                raw, metric = fixture(inputs)
                raw["grid_a"] = metric["grid_a"] = str(split)
                physical = review_original_rates(inputs, split)
                self.assertAlmostEqual(physical["sum_rate"], math.log2(5))
                self.assertGreaterEqual(physical["rw"], 0)
                self.assertGreaterEqual(physical["rs"], 0)
                audit = audit_fixture(raw, metric, inputs)
                self.assertTrue(audit.ok(), audit.counts)

    def test_F04_rejects_an_off_grid_representation(self):
        inputs = (1.0, 4.0, 4.0, 0.0, 0.0)
        raw, metric = fixture(inputs)
        raw["grid_a"] = metric["grid_a"] = ".69000000001"
        self.assertGreater(abs(float(raw["grid_a"]) - 69 / 100), ind.SPLIT)
        self.assertIn("grid_a", audit_fixture(raw, metric, inputs).counts)

    def test_F06_equal_gain_interior_selection_fails_even_when_sum_is_optimal(self):
        inputs = (1.0, 4.0, 4.0, 0.0, 0.0)
        raw, metric = fixture(inputs)
        review_rewrite_final(raw, metric, inputs, 0.25)
        self.assertAlmostEqual(float(raw["sum_rate"]), math.log2(5))
        self.assertGreater(float(raw["rw"]), 0.0)
        audit = audit_fixture(raw, metric, inputs)
        self.assertIn("selected_endpoint", audit.counts)

    def test_F06_weak_target_activation_is_checked_independently(self):
        inputs = (1.0, 4.0, 4.0, 0.5, 0.5)
        raw, metric = fixture(inputs)
        review_rewrite_final(raw, metric, inputs, 0.25)
        self.assertGreater(float(raw["rw"]), inputs[3] + 0.1)
        self.assertAlmostEqual(float(raw["sum_rate"]), math.log2(5))
        self.assertIn("weak_target_activation", audit_fixture(raw, metric, inputs).counts)

    def test_F06_materially_negative_row_losses_fail(self):
        inputs = (1.0, 1.0, 10.0, 0.0, 0.0)
        raw, metric = fixture(inputs)
        review_rewrite_final(raw, metric, inputs, 0.1)
        fixed = review_original_rates(inputs, 0.25)["sum_rate"]
        best_grid = math.log2(11)
        self.assertLess(float(raw["sum_rate"]) - fixed, -ind.OBJECTIVE)
        self.assertLess(float(raw["sum_rate"]) - best_grid, -ind.OBJECTIVE)
        audit = audit_fixture(raw, metric, inputs)
        self.assertIn("ablation.fixed.negative_loss", audit.counts)
        self.assertIn("ablation.grid.negative_loss", audit.counts)

    def test_F06_exact_singleton_witness_survives_binary64_rounding(self):
        inputs = (1.0, 3.0, 9.0, 1.0, 2.0)
        raw, metric = fixture(inputs)
        raw["exact_split"] = "1/3"
        raw["certificate"] = "exact-rational"
        self.assertNotEqual(Fraction(float(raw["a_star"])), Fraction(1, 3))
        # Hand-evaluated original SINRs at the exact witness are 1, 3/2, 3.
        self.assertEqual((1 - Fraction(1, 3)) * 3 / (1 + Fraction(1, 3) * 3), 1)
        self.assertEqual(Fraction(1, 3) * 9, 3)
        self.assertEqual((1 - Fraction(1, 3)) * 9 / (1 + Fraction(1, 3) * 9), Fraction(3, 2))
        self.assertTrue(audit_fixture(raw, metric, inputs).ok())

    def test_F07_noninteger_touching_and_sub_split_inner_domains_stay_unresolved(self):
        weak_target = math.log2(1.5)
        for strong_target in (2.0, 2.0 - 1e-12, 2.0 - 2e-12):
            with self.subTest(strong_target=strong_target):
                inputs = (1.0, 2.0, 6.0, weak_target, strong_target)
                # At a=.5, original received weak SINR=.5 and strong SINR=3.
                r = review_original_rates(inputs, 0.5)
                self.assertEqual(r["gamma_ww"], 0.5)
                self.assertEqual(r["gamma_ss"], 3.0)
                self.assertAlmostEqual(r["rw"], weak_target)
                self.assertGreaterEqual(r["rs"], strong_target)
                result = ind.noma_adjudicate(inputs)
                self.assertEqual(result["status"], "unresolved")

    def test_F11_positive_received_product_underflow_is_unsupported(self):
        for targets in ((0.0, 0.0), (1e-50, 0.0)):
            with self.subTest(targets=targets):
                inputs = (1e-200, 1e-200, 2e-200, *targets)
                self.assertGreater(Fraction(inputs[0]) * Fraction(inputs[1]), 0)
                self.assertEqual(inputs[0] * inputs[1], 0.0)
                self.assertEqual(ind.noma_adjudicate(inputs)["status"], "unresolved")
                self.assertEqual(ind.oma_adjudicate(inputs), "unresolved")
                with self.assertRaises(ValueError):
                    ind.rates(inputs, 0.5)

    def test_F11_collapsed_nonzero_products_do_not_create_exact_equal_gain_ties(self):
        P = float.fromhex("0x0.0000000000001p-1022")
        inputs = (P, 1.0, math.nextafter(1.0, 2.0), 0.0, 0.0)
        self.assertEqual(P * inputs[1], P * inputs[2])
        self.assertLess(Fraction(P) * Fraction(inputs[1]), Fraction(P) * Fraction(inputs[2]))
        raw, metric = fixture(inputs)
        self.assertEqual(raw["optimizer_unique"], "True")
        self.assertEqual(raw["nonunique"], "False")
        self.assertTrue(audit_fixture(raw, metric, inputs).ok())


SUPPLEMENT = Path(__file__).resolve().parent


def oracle_fixture(inputs, split=1.0, status="feasible", **policy):
    """Complete synthetic solver record, with directly recomputed attempted rates."""
    record = dict(
        status=status,
        feasible=1.0 if status == "feasible" else 0.0 if status == "infeasible" else None,
        feasibility_certificate="synthetic",
        optimality_status="numerical-concavity-bound"
        if status == "feasible"
        else "not-established",
        a_star=None,
        candidate_a=None,
        exact_split="",
        rw=None,
        rs=None,
        sum_rate=None,
        residual_w=None,
        residual_s=None,
        sic_residual=None,
        objective_upper_bound=None,
        objective_gap_bound=None,
        root_iterations=0,
        optimizer_iterations=0,
        optimizer_evaluations=0,
        singleton=False,
        inner_lower=None,
        inner_upper=None,
        outer_lower=None,
        outer_upper=None,
        reason="synthetic isolated fixture",
        rate_tolerance=RATE,
        split_tolerance=SPLIT,
        objective_tolerance=OBJECTIVE,
        max_root_iterations=96,
        max_optimizer_iterations=256,
    )
    record.update(policy)
    p, w, s, qw, qs = inputs
    record.update(
        oma_rw=math.log2(1 + p * w) / 2,
        oma_rs=math.log2(1 + p * s) / 2,
        oma_sum=(math.log2(1 + p * w) + math.log2(1 + p * s)) / 2,
    )
    if split is not None:
        r = rates(inputs, split)
        record.update(candidate_a=split, **{"candidate_" + k: v for k, v in r.items()})
        record.update(
            residual_w=r["rw"] - qw,
            residual_s=r["rs"] - qs,
            sic_residual=r["cw_at_s"] - r["rw"],
            objective_upper_bound=r["sum_rate"],
            objective_gap_bound=0.0,
        )
        if status == "feasible":
            record.update(a_star=split, **r)
    return record


def synthetic_replay(base_split=1.0, tighter_split=1.0, status="feasible", inputs=None):
    inputs = inputs or [1.0, 1.0, 4.0, 0.0, 0.0]
    params = dict(
        oracle_rows=1,
        sensitivity_rows=1,
        rate_tolerance=RATE,
        split_tolerance=SPLIT,
        objective_tolerance=OBJECTIVE,
    )
    raw = dict(zip(("P", "gw", "gs", "qw", "qs"), map(str, inputs)))
    raw.update(status="feasible", sum_rate=str(math.log2(5)))

    def solve(*values, **policy):
        split = base_split if policy["rate_tolerance"] == RATE else tighter_split
        return oracle_fixture(values, split, status, **policy)

    base = solve(*inputs, rate_tolerance=RATE, split_tolerance=SPLIT, objective_tolerance=OBJECTIVE)
    tight = solve(
        *inputs,
        rate_tolerance=RATE / 10,
        split_tolerance=SPLIT / 10,
        objective_tolerance=OBJECTIVE / 10,
    )
    checks = [
        dict(
            row=0,
            inputs=inputs,
            analytic_status="feasible",
            analytic_sum=math.log2(5),
            oracle=base,
            tighter_oracle=tight,
        )
    ]
    return checks, [raw], params, solve


def test_feasible_indicator_drift_fails_exactly():
    audit = Audit()
    recursive_compare(audit, "oracle.feasible", 1.0 - RATE / 2, 1.0, 0)
    assert "oracle.feasible" in audit.counts


@pytest.mark.parametrize("status", ["infeasible", "unresolved"])
def test_nonaccepted_final_rate_is_not_an_attempted_rate(status):
    record = oracle_fixture([1, 1, 4, 0, 0], 0.25, status)
    record["sum_rate"] = record["candidate_sum_rate"]
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert "oracle.sum_rate.mask" in audit.counts


def test_absent_attempt_cannot_keep_candidate_rate():
    record = oracle_fixture([1, 1, 4, 0, 0], None, "unresolved")
    record["candidate_rw"] = 0.0
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert "oracle.candidate_rw.mask" in audit.counts


def test_shared_reproduction_does_not_endorse_poor_accepted_optimum():
    args = synthetic_replay(0.25, 0.25)
    audit = Audit()
    result = replay_job(*args, audit)
    assert "oracle.agreement.analytic_base.objective" in audit.counts
    assert "oracle.agreement.base_independent.objective" in audit.counts
    assert result["comparisons"]["analytic_base"]["objective_max_residual"] > 0.6


def test_direct_base_tighter_sensitivity_is_a_separate_comparison():
    args = synthetic_replay(1.0, 0.75)
    audit = Audit()
    result = replay_job(*args, audit)
    assert "oracle.agreement.base_tighter.objective" in audit.counts
    assert result["comparisons"]["base_tighter"]["accepted_objectives"] == 1


def test_resolved_classification_conflict_fails():
    args = synthetic_replay(None, None, "infeasible")
    audit = Audit()
    replay_job(*args, audit)
    assert "oracle.agreement.analytic_base.status" in audit.counts
    assert "oracle.agreement.base_independent.status" in audit.counts


def test_unresolved_replay_preserves_uncertainty_and_transitions():
    checks, raw, params, solve = synthetic_replay(None, 1.0, "unresolved")

    def transition_solver(*values, **policy):
        return (
            oracle_fixture(values, None, "unresolved", **policy)
            if policy["rate_tolerance"] == RATE
            else oracle_fixture(values, 1.0, **policy)
        )

    checks[0]["tighter_oracle"] = transition_solver(
        *checks[0]["inputs"],
        rate_tolerance=RATE / 10,
        split_tolerance=SPLIT / 10,
        objective_tolerance=OBJECTIVE / 10,
    )
    audit = Audit()
    result = replay_job(checks, raw, params, transition_solver, audit)
    assert result["base_statuses"] == {"unresolved": 1}
    assert result["tighter_statuses"] == {"feasible": 1}
    assert result["statuses"] == {"unresolved": 1, "feasible": 1}
    assert result["unresolved_counts"]["base"] == 1
    assert result["optimality_not_established_counts"]["base"] == 1
    assert result["classification_transitions"] == {"unresolved->feasible": 1}
    assert audit.ok(), audit.errors


def test_tighter_gap_acceptance_uses_tighter_policy():
    checks, raw, params, solve = synthetic_replay()
    checks[0]["tighter_oracle"]["objective_gap_bound"] = OBJECTIVE / 2

    def oversized_gap(*values, **policy):
        record = solve(*values, **policy)
        if policy["rate_tolerance"] < RATE:
            record["objective_gap_bound"] = OBJECTIVE / 2
        return record

    audit = Audit()
    replay_job(checks, raw, params, oversized_gap, audit)
    assert "tighter_oracle.objective_gap_bound.acceptance" in audit.counts


def test_unsupported_independent_boundary_stays_explicit(monkeypatch):
    import replay

    monkeypatch.setattr(
        replay,
        "noma_adjudicate",
        lambda inputs: dict(
            status="unresolved", certificate="synthetic unsupported boundary", low=None, high=None
        ),
    )
    audit = Audit()
    result = replay_job(*synthetic_replay(), audit)
    assert result["unresolved_counts"]["independent"] == 1
    assert result["optimality_not_established_counts"]["independent"] == 1
    assert any(a.get("method") == "independent-oracle-comparison" for a in audit.ambiguities)
    assert audit.ok(), audit.errors


def test_budget_guard_stops_replay_with_deadline_failure():
    checks, raw, params, solve = synthetic_replay()

    def deadline():
        raise TimeoutError("synthetic replay deadline")

    with pytest.raises(TimeoutError, match="synthetic replay deadline"):
        replay_job(copy.deepcopy(checks), raw, params, solve, Audit(), budget_check=deadline)


def test_shared_solver_round_trip_is_only_labelled_reproduction():
    checks, raw, params, _ = synthetic_replay()
    solve = load_shared(SUPPLEMENT.parents[1] / "sim" / "src" / "oracle.py")
    inputs = checks[0]["inputs"]
    for key, factor in (("oracle", 1), ("tighter_oracle", 10)):
        policy = {
            k: params[k] / factor
            for k in ("rate_tolerance", "split_tolerance", "objective_tolerance")
        }
        result = solve(*inputs, **policy)
        checks[0][key] = {
            k: None if isinstance(v, float) and math.isnan(v) else v for k, v in result.items()
        }
    audit = Audit()
    result = replay_job(checks, raw, params, solve, audit)
    assert audit.ok(), audit.errors
    assert result["comparisons"]["base_independent"]["objective_max_residual"] == 0.0
    assert result["base"] == result["tighter"] == 1
    assert result["base_statuses"] == result["tighter_statuses"] == {"feasible": 1}
    assert result["evidence_kind"].startswith("shared-pinned-oracle-reproduction")


@pytest.mark.parametrize(
    "status,bad_mask",
    [("feasible", True), ("feasible", 1 - RATE / 2), ("infeasible", RATE / 2), ("unresolved", 0.0)],
)
def test_status_requires_its_exact_indicator(status, bad_mask):
    record = oracle_fixture([1, 1, 4, 0, 0], 1 if status == "feasible" else None, status)
    record["feasible"] = bad_mask
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert not audit.ok()
    assert any(e["field"].startswith("oracle.feasible") for e in audit.errors)


def test_accepted_optional_final_rate_null_is_a_mask_failure():
    record = oracle_fixture([1, 1, 4, 0, 0], 1.0)
    record["gamma_ww"] = None
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert "oracle.gamma_ww.mask" in audit.counts


def test_unresolved_candidate_retains_attempted_rate_diagnostics():
    record = oracle_fixture([1, 1, 4, 0, 0], 0.25, "unresolved")
    audit = Audit()
    check_oracle_original(audit, "oracle", record, [1, 1, 4, 0, 0], 0)
    assert audit.ok(), audit.errors


def test_budget_guard_checks_after_a_completed_solver_call():
    checks, raw, params, solve = synthetic_replay()
    completed = False

    def completing_solver(*values, **policy):
        nonlocal completed
        result = solve(*values, **policy)
        completed = True
        return result

    def deadline():
        if completed:
            raise TimeoutError("deadline after solver completion")

    with pytest.raises(TimeoutError, match="deadline after solver completion"):
        replay_job(checks, raw, params, completing_solver, Audit(), budget_check=deadline)


def options(**kw):
    d = dict(max_job_seconds=3600.0, max_total_seconds=86400.0, max_memory_mb=1024)
    d.update(kw)
    return SimpleNamespace(**d)


class ParentReviewTests(unittest.TestCase):
    def test_probability_roundoff_interoperation(self):
        for n, k in [(10, 0), (10, 10), (1000, 137), (393216, 0), (393216, 500)]:
            exact = binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
            own = ind.binomial(k, n)["ci95"]
            a = Audit()
            checker.compare_probability(a, "low", exact.low, own[0])
            checker.compare_probability(a, "high", exact.high, own[1])
            self.assertTrue(a.ok(), a.counts)

    def test_probability_corruption_and_invalid_range(self):
        for x in [0.500001, float("nan"), float("inf"), -1e-16, 1 + 1e-15]:
            a = Audit()
            checker.compare_probability(a, "p", x, 0.5)
            self.assertFalse(a.ok())

    def test_limit_validation(self):
        for key in ["max_job_seconds", "max_total_seconds", "max_memory_mb"]:
            for value in [0, -1, float("nan"), float("inf")]:
                with self.assertRaises(ValueError):
                    checker.Budget(options(**{key: value}))

    def test_budget_deadline(self):
        with mock.patch.object(checker.time, "monotonic", return_value=0):
            b = checker.Budget(options(max_total_seconds=1))
        with mock.patch.object(checker.time, "monotonic", return_value=2):
            with self.assertRaises(TimeoutError):
                b.check()

    def test_initial_guard_failure_retains_unique_receipts(self):
        with tempfile.TemporaryDirectory() as t:
            with (
                mock.patch.object(checker, "HERE", Path(t)),
                mock.patch.object(
                    checker, "ensure_phase", side_effect=ValueError("fixture phase guard")
                ),
            ):
                for _ in range(2):
                    with self.assertRaises(ValueError):
                        checker.execute(Path(t), options())
            receipts = list(Path(t).glob("runs/*/execution-report.json"))
            self.assertEqual(len(receipts), 2)
            for f in receipts:
                self.assertIn("fixture phase guard", json.loads(f.read_text())["exception"])

    def test_native_timeout_retains_stdout_and_receipt(self):
        import subprocess

        with tempfile.TemporaryDirectory() as t:
            with (
                mock.patch.object(checker, "HERE", Path(t)),
                mock.patch.object(
                    checker, "require_ready_source_review", return_value={"source_hashes": {}}
                ),
                mock.patch(
                    "lab.verification.verify",
                    side_effect=subprocess.TimeoutExpired(
                        "fixture", 1, output=b"partial-out", stderr=b"partial-err"
                    ),
                ),
            ):
                report = checker.run_native(Path(t))
            self.assertEqual(report["status"], "INCOMPLETE")
            root = Path(report["run_directory"])
            self.assertEqual((root / "stdout.txt").read_text(), "partial-out")
            self.assertEqual((root / "stderr.txt").read_text(), "partial-err")

    def test_combined_keeps_declared_uncertainty_and_native_failure(self):
        native = {"status": "PASS"}
        supp = {
            "status": "CHECKED_WITH_DECLARED_UNRESOLVED",
            "stored_unresolved_rows": 5,
            "error_counts": {},
            "unsupported_resolved_predicates": 0,
        }
        value = checker.combined_assessment(native, supp, [], ["analysis/fixture.json"])
        self.assertEqual(value["status"], "INCONCLUSIVE")
        self.assertFalse(value["eligible_for_gate_request"])
        self.assertTrue(any(i["verdict"] == "INCONCLUSIVE" for i in value["verification_items"]))
        native["status"] = "FAIL"
        native["failure_kind"] = "numerical-contradiction"
        self.assertEqual(
            checker.combined_assessment(native, supp, [], ["analysis/fixture.json"])["status"],
            "FAIL",
        )

    def test_combined_rejects_insufficient_precision(self):
        supp = {
            "status": "CHECKS_COMPLETE",
            "stored_unresolved_rows": 0,
            "error_counts": {},
            "unsupported_resolved_predicates": 0,
            "scenarios": {"x": {"paired": {"sum_rate": {"precision_met": False, "n": 10}}}},
        }
        self.assertEqual(
            checker.combined_assessment({"status": "PASS"}, supp, [], ["analysis/fixture.json"])[
                "status"
            ],
            "INCONCLUSIVE",
        )

    def test_lineage_executable_conditional_mask_and_undefined(self):
        rows = [
            dict(P=1, gw=1, gs=4, qw=0, qs=0, a_star=1, status="feasible"),
            dict(P=1, gw=0, gs=0, qw=1, qs=1, a_star=None, status="infeasible"),
        ]
        recipe = {
            "op": "independent_conditional_mean",
            "column": "sum_rate",
            "mask": "independent_both_feasible",
            "source_kind": "monte-carlo",
        }
        value = checker.lineage_value(rows, recipe)
        self.assertEqual(value["n"], 1)
        self.assertAlmostEqual(value["value"], math.log2(5))
        self.assertEqual(value["rows"], 2)
        empty = checker.lineage_value(rows[1:], recipe)
        self.assertIsNone(empty["value"])
        self.assertEqual(empty["n"], 0)

    def test_lineage_invalid_mask_rejected(self):
        with self.assertRaises(ValueError):
            checker.lineage_value(
                [],
                {
                    "op": "independent_conditional_mean",
                    "column": "sum_rate",
                    "mask": "author_flags_only",
                },
            )


class ApprovedIllustrativeInteropTests(unittest.TestCase):
    def test_approved_twentyfour_illustrative_rows(self):
        # Bounded source/schema interoperability fixture; no canonical inventory run.
        packet = json.loads(
            (SUPPLEMENT.parent / "P6-code-review-packet.json").read_text(encoding="utf-8")
        )
        count = 0
        for example in packet["illustrative_manifest_bound_samples"]:
            for raw in example["illustrative_rows"]:
                metric = {k: raw[k] for k in ind.METRIC_COLUMNS}
                inputs = [float(raw[k]) for k in ("P", "gw", "gs", "qw", "qs")]
                audit = ind.Audit()
                ind.check_row(raw, metric, inputs, raw.get("case_id", ""), int(raw["row"]), audit)
                self.assertTrue(
                    audit.ok(),
                    (
                        example["manifest"]["scenario"],
                        raw.get("case_id"),
                        audit.counts,
                        audit.errors,
                    ),
                )
                count += 1
        self.assertEqual(count, 24)


def native_items():
    return [dict(prediction_ref=f"P{i}", verdict="PASS") for i in range(1, 8)]


def complete():
    return dict(
        status="CHECKS_COMPLETE",
        error_counts={},
        stored_unresolved_rows=0,
        unsupported_resolved_predicates=0,
        bindings_rechecked=True,
        source_bindings_rechecked=True,
        jobs=[dict(rows=4718692, replay=dict(base=4708, tighter=1160))]
        + [dict(rows=0, replay=dict(base=0, tighter=0)) for _ in range(144)],
        scenarios={
            key: {"paired": {}, "events": {}, "deterministic": False}
            for key in ["q"] + [f"fixture-{i}" for i in range(12)]
        },
        oracle_unresolved_counts={},
        oracle_optimality_not_established_counts={},
    )


class AdditionalReceiptTests(unittest.TestCase):
    def test_combined_oracle_uncertainty_is_not_pass(self):
        s = complete()
        s["oracle_unresolved_counts"] = {"base": 1}
        self.assertEqual(
            checker.combined_assessment({"status": "PASS"}, s, native_items(), [])["status"],
            "INCONCLUSIVE",
        )

    def test_combined_missing_binding_or_coverage_is_not_pass(self):
        for field in ["bindings_rechecked", "source_bindings_rechecked", "jobs", "scenarios"]:
            s = complete()
            del s[field]
            self.assertEqual(
                checker.combined_assessment({"status": "PASS"}, s, native_items(), [])["status"],
                "INCONCLUSIVE",
            )

    def test_combined_false_binding_is_fail(self):
        s = complete()
        s["bindings_rechecked"] = False
        self.assertEqual(
            checker.combined_assessment({"status": "PASS"}, s, native_items(), [])["status"], "FAIL"
        )

    def test_combined_positive_low_event_precision_is_inconclusive(self):
        s = complete()
        s["scenarios"]["q"]["events"] = {
            "noma_infeasibility": {
                "events": 50,
                "minimum_events_met": False,
                "zero_event_upper_bound": None,
            }
        }
        self.assertEqual(
            checker.combined_assessment({"status": "PASS"}, s, native_items(), [])["status"],
            "INCONCLUSIVE",
        )

    def test_lineage_rejects_equal_gain_interior_endpoint(self):
        r = dict(P=1, gw=1, gs=1, qw=0, qs=0, a_star=0.5, status="feasible")
        with self.assertRaisesRegex(ValueError, "endpoint"):
            checker.lineage_value(
                [r],
                {
                    "op": "independent_conditional_mean",
                    "column": "sum_rate",
                    "mask": "independent_both_feasible",
                    "source_kind": "monte-carlo",
                },
            )

    def test_lineage_guard_failure_has_unique_receipts(self):
        with tempfile.TemporaryDirectory() as t:
            with (
                mock.patch.object(checker, "HERE", Path(t)),
                mock.patch.object(
                    checker,
                    "require_ready_source_review",
                    side_effect=ValueError("fixture source guard"),
                ),
            ):
                for _ in range(2):
                    with self.assertRaises(ValueError):
                        checker.execute_lineage_recipe(Path(t), {}, options())
            files = list(Path(t).glob("runs/*/lineage-receipt.json"))
            self.assertEqual(len(files), 2)
            self.assertTrue(
                all("fixture source guard" in json.loads(f.read_text())["exception"] for f in files)
            )

    def test_independent_lineage_moment_excludes_unsupported_stored_mask(self):
        inputs = [1.0, 1.0, 4.0, 0.0, 0.0]
        od = ind.oma(inputs)
        nr = rates(inputs, 1.0)
        checked = (
            inputs,
            {"status": "unresolved"},
            "feasible",
            "n11",
            nr["sum_rate"] - od["oma_sum"],
            od,
            {"fixed_feasible": 0, "grid_found_feasible": 0},
        )
        s = checker.init_scenario()
        checker.update(
            s, {"a_star": "1", "candidate_violation": "False", "status": "feasible"}, checked
        )
        self.assertEqual(s["independent_pairs"]["sum_rate"].n, 0)
        self.assertEqual(s["pairs"]["sum_rate"].n, 1)


class FlagBoundaryTests(unittest.TestCase):
    def test_verified_serialized_strict_flag_can_cross_one_ulp(self):
        v = (1.0, 3.0, 9.0, 1.0, 2.0)
        r, m = fixture(v)
        r["candidate_rw"] = repr(math.nextafter(1.0, -math.inf))
        r["candidate_constraints_pass"] = "False"
        audit = audit_fixture(r, m, v)
        self.assertTrue(audit.ok(), audit.counts)
        self.assertGreater(audit.diagnostic_counts.get("candidate_constraints_pass.roundoff", 0), 0)

    def test_material_strict_flag_discrepancy_rejected(self):
        v = (1.0, 3.0, 9.0, 1.0, 2.0)
        r, m = fixture(v)
        r["candidate_rw"] = repr(1.0 - ind.RATE / 2)
        r["candidate_constraints_pass"] = "False"
        self.assertFalse(audit_fixture(r, m, v).ok())

    def test_infeasible_oracle_optimality_is_not_applicable(self):
        v = [1.0, 0.0, 0.0, 1.0, 1.0]
        r, m = fixture(v)

        def solve(*inputs, **kw):
            return oracle_fixture(inputs, status="infeasible", **kw)

        base = solve(
            *v,
            rate_tolerance=ind.RATE,
            split_tolerance=ind.SPLIT,
            objective_tolerance=ind.OBJECTIVE,
            max_root_iterations=96,
            max_optimizer_iterations=256,
        )
        check = dict(row=0, inputs=v, analytic_status="infeasible", analytic_sum=None, oracle=base)
        a = ind.Audit()
        out = replay.replay_job(
            [check],
            [r],
            dict(
                oracle_rows=1,
                sensitivity_rows=0,
                rate_tolerance=ind.RATE,
                split_tolerance=ind.SPLIT,
                objective_tolerance=ind.OBJECTIVE,
            ),
            solve,
            a,
        )
        self.assertEqual(out["optimality_not_established_counts"]["base"], 0)
        self.assertEqual(out["optimality_not_applicable_counts"]["base"], 1)


class SourceCoverageTests(unittest.TestCase):
    def test_ready_review_cannot_omit_source_inventory(self):
        with tempfile.TemporaryDirectory() as t:
            project = Path(t)
            (project / "analysis").mkdir()
            (project / "analysis/source-review-ready.json").write_text(
                json.dumps(
                    dict(recommendation="ready", enforced_independent_review=True, source_hashes={})
                )
            )
            with self.assertRaises(ValueError):
                checker.require_ready_source_review(project)


class RoundTwoTests(unittest.TestCase):
    def test_deterministic_precision_is_not_statistical_failure(self):
        s = complete()
        s["scenarios"]["q"] = {
            "deterministic": True,
            "paired": {"sum_rate": {"n": 5, "ci95": None, "precision_met": False}},
            "events": {},
        }
        v = checker.combined_assessment({"status": "PASS"}, s, native_items(), [])
        self.assertEqual(v["failed_precision"], [])

    def test_native_timeout_does_not_establish_scientific_failure(self):
        self.assertEqual(
            checker.combined_assessment(
                {"status": "INCOMPLETE", "failure_kind": "timeout"}, complete(), native_items(), []
            )["status"],
            "INCONCLUSIVE",
        )

    def test_native_precision_rejection_is_inconclusive(self):
        self.assertEqual(
            checker.combined_assessment(
                {"status": "FAIL", "failure_kind": "statistical-precision"},
                complete(),
                native_items(),
                [],
            )["status"],
            "INCONCLUSIVE",
        )

    def test_actual_constraint_failure_is_scientific_fail(self):
        self.assertEqual(
            checker.combined_assessment(
                {"status": "FAIL", "failure_kind": "numerical-contradiction"},
                complete(),
                native_items(),
                [],
            )["status"],
            "FAIL",
        )

    def test_native_precision_exception_records_structured_reason(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)

            def failure(*args):
                (p / "analysis/verifier-output").mkdir(parents=True)
                (p / "analysis/verifier-output/checks.yaml").write_text(
                    json.dumps(
                        {
                            "statistical-precision": {"passed": False},
                            "constraints": {"passed": True},
                        }
                    )
                )
                raise ValueError("fixture native rejection")

            with (
                mock.patch.object(checker, "HERE", p),
                mock.patch.object(
                    checker, "require_ready_source_review", return_value={"source_hashes": {}}
                ),
                mock.patch("lab.verification.verify", side_effect=failure),
            ):
                v = checker.run_native(p)
            self.assertEqual(v["failure_kind"], "statistical-precision")
            self.assertEqual(v["status"], "INCONCLUSIVE")

    def test_final_inventory_change_detected(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            (p / "results/runs/a").mkdir(parents=True)
            (p / "results/runs/a/manifest.json").write_text("{}")
            before = checker.manifest_path_inventory(p)
            (p / "results/runs/b").mkdir()
            (p / "results/runs/b/manifest.json").write_text("{}")
            self.assertNotEqual(before, checker.manifest_path_inventory(p))

    def test_full_reviewed_dependency_change_detected(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            (p / "analysis").mkdir()
            names = [f"file{i}.py" for i in range(19)]
            hashes = {}
            for name in names:
                (p / name).write_text("before")
                hashes[name] = checker.sha256(p / name)
            (p / "analysis/P6-code-review-payload.json").write_text(
                json.dumps({"artifact_paths": names})
            )
            (p / "analysis/source-review-ready.json").write_text(
                json.dumps(
                    {
                        "recommendation": "ready",
                        "enforced_independent_review": True,
                        "source_hashes": hashes,
                    }
                )
            )
            (p / names[-1]).write_text("after")
            with self.assertRaises(ValueError):
                checker.require_ready_source_review(p)

    def test_empty_statistical_fields_do_not_complete_coverage(self):
        self.assertFalse(checker.assessment_coverage(complete(), {}, {}))

    def test_unit_runner_timeout_retains_output_and_receipt(self):
        import subprocess

        path = Path(checker.HERE / "run_unit_tests.py")
        spec = importlib.util.spec_from_file_location("fixture_runner", path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as t:
            with mock.patch.object(
                runner.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired(
                    "fixture", 1, output=b"partial", stderr=b"err"
                ),
            ):
                v = runner.run_tests(Path(t), timeout=1)
            self.assertEqual(v["status"], "FAIL")
            self.assertIn("TimeoutExpired", v["exception"])
            root = Path(t) / v["run_directory"]
            self.assertEqual((root / "stdout.txt").read_text(), "partial")
            self.assertTrue((root / "receipt.json").is_file())

    def test_unit_runner_missing_junit_retains_receipt(self):
        import subprocess

        path = Path(checker.HERE / "run_unit_tests.py")
        spec = importlib.util.spec_from_file_location("fixture_runner2", path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as t:
            with mock.patch.object(
                runner.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "out", "")
            ):
                v = runner.run_tests(Path(t), timeout=1)
            self.assertEqual(v["status"], "FAIL")
            self.assertIn("FileNotFoundError", v["exception"])
            self.assertTrue((Path(t) / v["run_directory"] / "receipt.json").is_file())


def shaped_coverage():
    jobs = {"a": dict(rows=5, base=2, tighter=1), "b": dict(rows=5, base=2, tighter=1)}
    scens = {"q": dict(rows=10, deterministic=True)}
    counts = dict(n00=0, n01=0, n10=0, n11=10, unresolved=0)
    stat = dict(
        n=10,
        mean=1.0,
        variance=0.0,
        ci95=None,
        halfwidth=None,
        relative_halfwidth=None,
        precision_met=False,
    )
    value = dict(
        deterministic=True,
        N_total=10,
        N_resolved=10,
        unresolved=0,
        counts=counts,
        independent_counts=counts.copy(),
        paired={key: stat.copy() for key in ["sum_rate", "oma_sum", "paired_difference"]},
        events={},
        ablations={"fixed": {}, "grid": {}},
    )
    supp = dict(
        status="CHECKS_COMPLETE",
        jobs=[
            dict(run_id=name, rows=x["rows"], replay=dict(base=x["base"], tighter=x["tighter"]))
            for name, x in jobs.items()
        ],
        scenarios={"q": value},
    )
    return supp, jobs, scens


class RoundTwoCoverageTests(unittest.TestCase):
    def test_shaped_exact_inventory_is_accepted(self):
        s, j, c = shaped_coverage()
        self.assertTrue(checker.assessment_coverage(s, j, c))

    def test_redistributed_job_totals_rejected(self):
        s, j, c = shaped_coverage()
        s["jobs"][0]["rows"] = 6
        s["jobs"][1]["rows"] = 4
        self.assertFalse(checker.assessment_coverage(s, j, c))

    def test_wrong_scenario_identity_rejected(self):
        s, j, c = shaped_coverage()
        s["scenarios"]["wrong"] = s["scenarios"].pop("q")
        self.assertFalse(checker.assessment_coverage(s, j, c))

    def test_empty_scenario_statistics_rejected(self):
        s, j, c = shaped_coverage()
        s["scenarios"]["q"]["paired"] = {}
        self.assertFalse(checker.assessment_coverage(s, j, c))

    def test_stale_native_checks_do_not_describe_new_failed_attempt(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            (p / "analysis/verifier-output").mkdir(parents=True)
            (p / "analysis/verifier-output/checks.yaml").write_text(
                json.dumps({"constraints": {"passed": False}})
            )
            with (
                mock.patch.object(checker, "HERE", p),
                mock.patch.object(
                    checker, "require_ready_source_review", return_value={"source_hashes": {}}
                ),
                mock.patch(
                    "lab.verification.verify", side_effect=ValueError("previous stage exists")
                ),
            ):
                value = checker.run_native(p)
            self.assertEqual(value["status"], "INCOMPLETE")
            self.assertNotEqual(value.get("failure_kind"), "numerical-contradiction")

    def test_final_deadline_is_accounted_and_retained(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            clock = [0.0]
            calls = [0]
            original_load = checker.load

            def snapshots(*args, **kw):
                calls[0] += 1
                if calls[0] == 2:
                    clock[0] = 100.0
                return {}

            with (
                mock.patch.object(checker, "HERE", p),
                mock.patch.object(checker.time, "monotonic", side_effect=lambda: clock[0]),
                mock.patch.object(checker, "ensure_phase"),
                mock.patch.object(
                    checker, "require_ready_source_review", return_value={"source_hashes": {}}
                ),
                mock.patch.object(checker, "locked", return_value=({"scenarios": []}, {})),
                mock.patch.object(checker, "read_inventory", return_value=[]),
                mock.patch.object(checker, "check_jobs"),
                mock.patch.object(checker, "input_snapshot", side_effect=snapshots),
                mock.patch.object(
                    checker,
                    "load",
                    side_effect=lambda f: (
                        {"cases": []} if Path(f).name == "cases.yaml" else original_load(f)
                    ),
                ),
            ):
                with self.assertRaisesRegex(ValueError, "deterministic table coverage"):
                    checker.execute(p, options(max_total_seconds=50))
            report = json.loads(next(p.glob("runs/*/execution-report.json")).read_text())
            self.assertEqual(report["status"], "INCOMPLETE")
            self.assertIn("deadline", report["binding_error"])
            self.assertEqual(report["runtime_s"], 100.0)


class RunnerInitializationTests(unittest.TestCase):
    def test_initial_source_read_failure_retains_receipt(self):
        original = Path.read_bytes

        def fail(file):
            if file.name == "fixture.py":
                raise OSError("fixture unavailable source")
            return original(file)

        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            (p / "fixture.py").write_text("fixture")
            with mock.patch.object(Path, "read_bytes", fail):
                value = runner.run_tests(p)
            self.assertEqual(value["status"], "FAIL")
            self.assertIn("OSError", value["exception"])
            self.assertTrue((p / value["run_directory"] / "receipt.json").is_file())


def lineage_recipe():
    return dict(
        op="independent_conditional_mean",
        column="sum_rate",
        mask="independent_both_feasible",
        source_kind="deterministic",
        source_scenario="x",
    )


def failing_items():
    return [
        dict(
            id=f"fixture-P{i}",
            prediction_ref=f"P{i}",
            method="synthetic check",
            metric="synthetic fixture residual",
            value=0.0,
            tolerance={"rate": RATE},
            verdict="FAIL" if i in [4, 6] else "PASS",
            triage="implementation-bug" if i in [4, 6] else None,
            evidence_paths=["analysis/verifier-output/checks.yaml"],
        )
        for i in range(1, 8)
    ]


class RoundThreeTests(unittest.TestCase):
    def test_deterministic_recipe_has_no_inferential_ci(self):
        rows = [dict(P=1, gw=1, gs=4, qw=0, qs=0, a_star=1, status="feasible")] * 5
        value = checker.lineage_value(rows, lineage_recipe())
        self.assertEqual(value["n"], 5)
        self.assertIsNone(value["statistics"]["ci95"])
        self.assertIsNone(value["statistics"]["halfwidth"])

    def test_lineage_manifest_kind_must_be_compatible(self):
        one = SimpleNamespace(scenario="x", params={"kind": "deterministic"})
        two = SimpleNamespace(scenario="x", params={"kind": "monte-carlo"})
        with self.assertRaises(ValueError):
            checker.validate_lineage_design([one, two], lineage_recipe())

    def test_lineage_design_cannot_claim_mc_for_fixed_cases(self):
        one = SimpleNamespace(scenario="x", params={"kind": "deterministic"})
        r = lineage_recipe()
        r["source_kind"] = "monte-carlo"
        with self.assertRaises(ValueError):
            checker.validate_lineage_design([one], r)

    def test_fresh_prediction_failures_retained_with_passing_checks(self):
        self.check_prediction_failure(False)

    def test_fresh_prediction_failures_retained_with_precision_failure(self):
        self.check_prediction_failure(True)

    def check_prediction_failure(self, precision):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)

            def reject(*args):
                d = p / "analysis/verifier-output"
                d.mkdir(parents=True)
                (d / "checks.yaml").write_text(
                    json.dumps(
                        {
                            "constraints": {"passed": True},
                            "statistical-precision": {"passed": not precision},
                        }
                    )
                )
                (d / "verification.yaml").write_text(json.dumps(failing_items()))
                raise ValueError("fixture native rejected")

            with (
                mock.patch.object(checker, "HERE", p),
                mock.patch.object(
                    checker, "require_ready_source_review", return_value={"source_hashes": {}}
                ),
                mock.patch("lab.verification.verify", side_effect=reject),
            ):
                value = checker.run_native(p)
            self.assertEqual(value["status"], "FAIL")
            self.assertEqual(value["failed_native_prediction_refs"], ["P4", "P6"])
            self.assertEqual(value["failure_kind"], "numerical-contradiction")


class DeterministicLineageExecutionTests(unittest.TestCase):
    def test_written_record_and_executed_recipe_suppress_deterministic_ci(self):
        import csv

        with tempfile.TemporaryDirectory() as t:
            project = Path(t)
            run = project / "results/runs/fixture"
            run.mkdir(parents=True)
            raw = run / "channels.csv"
            row = dict(P=1, gw=1, gs=4, qw=0, qs=0, a_star=1, status="feasible")
            with raw.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                writer.writeheader()
                writer.writerows([row] * 5)
            manifest = dict(
                scenario="fixture",
                params={"kind": "deterministic"},
                outputs=[
                    dict(path=raw.relative_to(project).as_posix(), sha256=checker.sha256(raw))
                ],
            )
            mf = run / "manifest.json"
            checker.save(mf, manifest)
            summary = checker.init_scenario()
            summary["total"] = 5
            summary["independent_counts"]["n11"] = 5
            for moment in summary["independent_pairs"].values():
                for value in range(5):
                    moment.add(float(value))
            out = project / "analysis/lineage-fixture"
            checker.write_lineage(project, [(mf, manifest)], {"fixture": summary}, out, Audit())
            records = checker.load(out / "claim-lineage.json")["records"]
            for record in records:
                self.assertEqual(record["n"], 5)
                self.assertIsNone(record["statistics"]["ci95"])
                self.assertIsNone(record["statistics"]["halfwidth"])
            recipe = checker.load(project / records[0]["recipe_path"])
            with (
                mock.patch.object(checker, "HERE", project / "analysis/supplement"),
                mock.patch.object(
                    checker, "require_ready_source_review", return_value={"source_hashes": {}}
                ),
                mock.patch.object(
                    checker,
                    "verify_manifest",
                    return_value=SimpleNamespace(
                        scenario="fixture", params={"kind": "deterministic"}
                    ),
                ),
                mock.patch.object(checker, "manifest_output", return_value=raw),
            ):
                result = checker.execute_lineage_recipe(project, recipe, options())
            self.assertEqual(result["n"], 5)
            self.assertAlmostEqual(result["value"], math.log2(5))
            self.assertIsNone(result["statistics"]["ci95"])
            self.assertIsNone(result["statistics"]["halfwidth"])
            self.assertTrue(result["deterministic"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
