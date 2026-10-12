"""Disposable corruption tests; no canonical checker/native verification calls."""

import copy
import math
import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checker
import independent as ind
import replay


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
            r = ind.rates(inputs, 1.0)
            return dict(
                status="feasible",
                feasibility_certificate="synthetic-test-only",
                a_star=1.0,
                **r,
                **kw,
            )

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
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
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


if __name__ == "__main__":
    unittest.main()
