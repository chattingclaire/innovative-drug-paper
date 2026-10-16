#!/usr/bin/env python3
"""Synthetic-only tests; never discover or read real coding/prediction files."""

import copy
from fractions import Fraction
from itertools import product
import json
from math import comb
from pathlib import Path
import unittest

import d668_statistics as ds


def probability(N, M, n, x):
    if x < 0 or x > M or n - x < 0 or n - x > N - M:
        return Fraction(0)
    return Fraction(comb(M, x) * comb(N - M, n - x), comb(N, n))


def exact_inversion(N, n, x, alpha):
    threshold = Fraction(str(alpha)) / 2
    candidates = []
    for M in range(x, N - n + x + 1):
        upper_tail = sum((probability(N, M, n, j) for j in range(x, n + 1)), Fraction(0))
        lower_tail = sum((probability(N, M, n, j) for j in range(x + 1)), Fraction(0))
        if upper_tail >= threshold and lower_tail >= threshold:
            candidates.append(M)
    return min(candidates), max(candidates)


def fixture(design=None, state_function=None):
    if design is None:
        design = dict(population_size=20, sample_size=10,
                      department_sizes={"X": 10, "Y": 10},
                      strata=[dict(stratum_id="R|X", phase="R", department="X", N=6, n=3),
                              dict(stratum_id="D|X", phase="D", department="X", N=4, n=2),
                              dict(stratum_id="R|Y", phase="R", department="Y", N=4, n=2),
                              dict(stratum_id="D|Y", phase="D", department="Y", N=6, n=3)])
    units = []
    for h in design["strata"]:
        for j in range(h["n"]):
            labels = {coder: {dim: (state_function(h, j, coder, dim) if state_function else
                                    ds.STATUSES[(j + k + (coder == "C")) % 3])
                              for k, dim in enumerate(ds.DIMENSIONS)} for coder in ds.CODERS}
            units.append(dict(unit_id=f"SYNTHETIC_ONLY::{h['stratum_id']}::{j}",
                              stratum_id=h["stratum_id"], labels=labels))
    return dict(schema_version=ds.SCHEMA_VERSION, data_kind="synthetic_test",
                design=copy.deepcopy(design), coders=list(ds.CODERS),
                dimensions=list(ds.DIMENSIONS), units=units)


class ExactHypergeometricTests(unittest.TestCase):
    def test_integer_inversion_matches_independent_exact_rational_enumeration(self):
        # Every feasible x for all N<=12, every sample size, and three alpha
        # choices. Fraction+comb is independent of scipy and binary search.
        for N in range(1, 13):
            for n in range(1, N + 1):
                for x in range(n + 1):
                    for alpha in (0.05, 0.2, 0.05 / 580):
                        got = ds.hypergeom_total_interval(N, n, x, alpha)
                        expected = exact_inversion(N, n, x, alpha)
                        self.assertEqual(got, expected, (N, n, x, alpha))

    def test_small_population_exhaustive_design_coverage(self):
        # Enumerate all M and all possible sample results. Each sample result
        # is weighted by its exact number of SRSWOR subsets, not simulation.
        for N in range(1, 15):
            for n in range(1, N + 1):
                for alpha in (0.05, 0.2):
                    intervals = [ds.hypergeom_total_interval(N, n, x, alpha) for x in range(n + 1)]
                    for M in range(N + 1):
                        coverage = sum((probability(N, M, n, x) for x, (a, b) in enumerate(intervals)
                                        if a <= M <= b), Fraction(0))
                        self.assertGreaterEqual(coverage, 1 - Fraction(str(alpha)), (N, n, M, alpha))

    def test_two_strata_exhaustive_aggregate_coverage(self):
        N1, n1, N2, n2 = 7, 3, 8, 4
        alpha = 0.05
        result_intervals = {
            (x, y): ds.aggregate_binary([(N1, n1, x), (N2, n2, y)], N1 + N2)["confidence_interval"]
            for x in range(n1 + 1) for y in range(n2 + 1)
        }
        for M1 in range(N1 + 1):
            for M2 in range(N2 + 1):
                coverage = Fraction(0)
                for (x, y), ci in result_intervals.items():
                    if ci["population_total_lower"] <= M1 + M2 <= ci["population_total_upper"]:
                        coverage += probability(N1, M1, n1, x) * probability(N2, M2, n2, y)
                self.assertGreaterEqual(coverage, Fraction(95, 100))

    def test_zero_all_events_census_and_singleton_census(self):
        for N, n in ((10, 2), (100, 30), (1662, 222)):
            lo, hi = ds.hypergeom_total_interval(N, n, 0, ds.ALPHA)
            self.assertEqual(lo, 0)
            self.assertGreater(hi, 0)
            lo1, hi1 = ds.hypergeom_total_interval(N, n, n, ds.ALPHA)
            self.assertEqual((lo1, hi1), (N - hi, N))
        for N in (1, 4, 30):
            for x in range(N + 1):
                self.assertEqual(ds.hypergeom_total_interval(N, N, x, ds.ALPHA), (x, x))
                self.assertEqual(ds.binary_stratum_summary(N, N, x)["estimated_total_variance"], 0)

    def test_zero_sample_variance_does_not_make_zero_event_interval_degenerate(self):
        result = ds.aggregate_binary([(100, 20, 0), (80, 10, 0)], 180)
        self.assertEqual(result["estimated_design_variance"], 0)
        self.assertEqual(result["proportion"], 0)
        self.assertGreater(result["confidence_interval"]["upper"], 0)

    def test_invalid_hypergeometric_arguments_and_non_census_n_one(self):
        for args in ((0, 1, 0, .05), (10, 11, 0, .05), (10, 3, 4, .05),
                     (10, 3, -1, .05), (10, 3, 0, 0), (10, 3, 0, 1),
                     (True, 1, 0, .05), (10, 3, 0, True)):
            with self.assertRaises(ValueError):
                ds.hypergeom_total_interval(*args)
        with self.assertRaises(ValueError):
            ds.binary_stratum_summary(2, 1, 0)


class EstimatorTests(unittest.TestCase):
    def test_mixed_R_D_weights_and_auxiliary_variance_hand_calculation(self):
        result = ds.aggregate_binary([(6, 3, 1), (10, 2, 1)], 16)
        # HT total 6/3 + 10/2 = 7. Sample s^2 are 1/3 and 1/2;
        # total-variance contributions are 2 and 20 respectively.
        self.assertEqual(result["ht_total"], 7)
        self.assertEqual(result["proportion"], 7 / 16)
        self.assertAlmostEqual(result["estimated_design_variance"], 22 / 256)
        self.assertNotEqual(result["proportion"], 2 / 5)

    def test_unbiased_ht_and_variance_estimator_by_exact_sampling_enumeration(self):
        N1, M1, n1, N2, M2, n2 = 6, 2, 3, 8, 5, 4
        weighted_mean = weighted_var_estimate = actual_variance = 0.0
        true_proportion = (M1 + M2) / (N1 + N2)
        for x, y in product(range(n1 + 1), range(n2 + 1)):
            p = float(probability(N1, M1, n1, x) * probability(N2, M2, n2, y))
            r = ds.aggregate_binary([(N1, n1, x), (N2, n2, y)], N1 + N2)
            weighted_mean += p * r["proportion"]
            weighted_var_estimate += p * r["estimated_design_variance"]
            actual_variance += p * (r["proportion"] - true_proportion)**2
        self.assertAlmostEqual(weighted_mean, true_proportion, places=14)
        self.assertAlmostEqual(weighted_var_estimate, actual_variance, places=14)

    def test_equal_weights_reduce_to_unweighted_sample_proportion(self):
        r = ds.aggregate_binary([(6, 3, 1), (4, 2, 2)], 10)
        self.assertEqual(r["proportion"], 3 / 5)

    def test_three_states_sum_to_one_and_pending_is_not_dropped(self):
        result = ds._analyze_synthetic(fixture())
        rows = result["department_status_estimates"]
        for coder, dim, g in product(ds.CODERS, ds.DIMENSIONS, ("X", "Y")):
            selected = {r["measure"]: r for r in rows if
                        (r["coder"], r["dimension"], r["department"]) == (coder, dim, g)}
            self.assertAlmostEqual(sum(r["proportion"] for r in selected.values()), 1)
            self.assertEqual(sum(r["sample_event_count"] for r in selected.values()), 5)
            potential = next(r for r in result["department_potential_positive_estimates"] if
                             (r["coder"], r["dimension"], r["department"]) == (coder, dim, g))
            self.assertAlmostEqual(potential["proportion"], selected["1"]["proportion"] + selected["pending"]["proportion"])

    def test_full_frozen_shapes_overall_population_weighting_and_family(self):
        result = ds._analyze_synthetic(fixture(ds.frozen_design()))
        metadata = result["metadata"]
        self.assertEqual(metadata["analysis_kind"], "SYNTHETIC_SOFTWARE_TEST_ONLY")
        self.assertEqual(metadata["output_row_counts"], {
            "department_status_estimates": 120,
            "department_potential_positive_estimates": 40,
            "overall_status_estimates": 30,
            "overall_potential_positive_estimates": 10,
            "coder_pairwise_differences": 60,
            "common_robust_directions": 30,
            "stratum_coder_dimension_counts": 290,
        })
        self.assertEqual(metadata["unique_sample_units"], 1268)
        self.assertFalse(metadata["ai_independence_required"])
        self.assertEqual(metadata["family_size"], 580)
        self.assertEqual(metadata["family_per_parameter_alpha"], .05 / 580)
        self.assertEqual(sum(len(r["simultaneous_total_bounds"]) for r in result["stratum_coder_dimension_counts"]), 580)
        self.assertEqual(metadata["marginal_department_strata"], {"GOV": 5, "NHC": 8, "NHSA": 9, "NMPA": 7})
        for row in result["overall_status_estimates"]:
            selected = [r for r in result["department_status_estimates"] if
                        (r["coder"], r["dimension"], r["measure"]) ==
                        (row["coder"], row["dimension"], row["measure"])]
            mean = sum(r["proportion"] * r["fixed_denominator"] / 4924 for r in selected)
            self.assertAlmostEqual(row["proportion"], mean)
            self.assertEqual(row["confidence_interval"]["per_stratum_alpha"], .05 / 29)

    def test_family_size_does_not_shrink_for_absent_pending_or_census(self):
        design = dict(population_size=4, sample_size=4, department_sizes={"X": 2, "Y": 2},
                      strata=[dict(stratum_id="R|X", phase="R", department="X", N=2, n=2),
                              dict(stratum_id="D|Y", phase="D", department="Y", N=2, n=2)])
        result = ds._analyze_synthetic(fixture(design, lambda h, j, c, d: "0"))
        self.assertEqual(result["metadata"]["family_size"], 580)
        for layer in result["stratum_coder_dimension_counts"]:
            for b in layer["simultaneous_total_bounds"].values():
                self.assertEqual(b["alpha"], .05 / 580)
                self.assertEqual((b["total_lower"], b["total_upper"]), (0, 0))

    def test_common_direction_needs_both_AIs_and_pending_worst_completion(self):
        design = dict(population_size=8, sample_size=8, department_sizes={"X": 4, "Y": 4},
                      strata=[dict(stratum_id="R|X", phase="R", department="X", N=4, n=4),
                              dict(stratum_id="D|Y", phase="D", department="Y", N=4, n=4)])
        same = ds._analyze_synthetic(fixture(design, lambda h, j, c, d: "1" if h["department"] == "X" else "0"))
        self.assertTrue(all(r["common_robust_direction"] == "left_greater" for r in same["common_robust_directions"]))
        opposite = ds._analyze_synthetic(fixture(design, lambda h, j, c, d: "1" if
                                                (h["department"] == "X") == (c == "A") else "0"))
        self.assertTrue(all(r["common_robust_direction"] == "not_orderable" for r in opposite["common_robust_directions"]))
        pending = ds._analyze_synthetic(fixture(design, lambda h, j, c, d: "1" if h["department"] == "X" else "pending"))
        for row in pending["coder_pairwise_differences"]:
            self.assertTrue(row["positive_difference_simultaneous_interval"]["excludes_zero"])
            ci = row["worst_pending_completion_simultaneous_interval"]
            self.assertEqual((ci["lower"], ci["upper"]), (0, 1))
            self.assertEqual(ci["direction"], "not_orderable")

    def test_exact_difference_signs_at_touching_zero(self):
        left = dict(fixed_denominator=3, population_total_lower=1, population_total_upper=1)
        right = dict(fixed_denominator=6, population_total_lower=2, population_total_upper=2)
        ci = ds._difference(left, right)
        self.assertEqual(ci["exact_lower_numerator"], 0)
        self.assertEqual(ci["exact_upper_numerator"], 0)
        self.assertFalse(ci["excludes_zero"])


class ValidationTests(unittest.TestCase):
    def test_duplicate_unit_missing_unit_missing_AI_dimension_and_invalid_status_rejected(self):
        corruptions = [
            lambda p: p["units"].__setitem__(1, copy.deepcopy(p["units"][0])),
            lambda p: p["units"].pop(),
            lambda p: p["units"][0]["labels"].pop("C"),
            lambda p: p["units"][0]["labels"]["A"].pop("S"),
            lambda p: p["units"][0]["labels"]["A"].__setitem__("S", None),
            lambda p: p["units"][0]["labels"]["A"].__setitem__("S", 1),
            lambda p: p["units"][0]["labels"]["A"].__setitem__("S", "待定"),
            lambda p: p["units"][0].__setitem__("stratum_id", "D|unknown"),
            lambda p: p["units"][0].__setitem__("stratum_id", "D|X"),
            lambda p: p.__setitem__("alpha", .1),
        ]
        for corruption in corruptions:
            p = fixture()
            corruption(p)
            with self.assertRaises(ValueError):
                ds._analyze_synthetic(p)

    def test_observed_entrypoint_requires_exact_29_strata_not_just_totals(self):
        # Only the validator is called with the observed schema. No synthetic
        # result is ever emitted under an observed-analysis label.
        p = fixture(ds.frozen_design())
        p["data_kind"] = "observed_coding"
        ds._validate(p, synthetic=False)
        bad = copy.deepcopy(p)
        bad["design"]["strata"][0]["N"] += 1
        bad["design"]["strata"][1]["N"] -= 1
        with self.assertRaisesRegex(ValueError, "29 frozen"):
            ds._validate(bad, synthetic=False)
        bad = copy.deepcopy(p)
        bad["design"]["strata"][0]["n"] += 1
        bad["design"]["strata"][1]["n"] -= 1
        with self.assertRaisesRegex(ValueError, "29 frozen"):
            ds._validate(bad, synthetic=False)
        with self.assertRaises(ValueError):
            ds.analyze(fixture(ds.frozen_design()))

    def test_frozen_metadata_matches_only_authorized_R_stratum_metadata(self):
        # The only external read in the test suite is this approved metadata
        # key. No raw AI labels or predictions are opened.
        source = Path(__file__).with_name("原4924范围-AI内容编码覆盖与补充设计评估.json")
        if not source.exists():
            self.skipTest("Approved metadata unavailable in standalone distribution")
        r_metadata = json.loads(source.read_text(encoding="utf-8"))["R_strata"]
        wanted = {"R|" + r["stratum"]: (r["N_h"], r["n_h"]) for r in r_metadata}
        got = {h["stratum_id"]: (h["N"], h["n"]) for h in ds.frozen_design()["strata"] if h["phase"] == "R"}
        self.assertEqual(got, wanted)
        design = ds.frozen_design()
        self.assertEqual(sum(h["N"] for h in design["strata"] if h["phase"] == "R"), 1531)
        self.assertEqual(sum(h["n"] for h in design["strata"] if h["phase"] == "R"), 600)
        self.assertEqual(sum(h["N"] for h in design["strata"] if h["phase"] == "D"), 3393)
        self.assertEqual(sum(h["n"] for h in design["strata"] if h["phase"] == "D"), 668)

    def test_input_unchanged_and_deterministic_result(self):
        p = fixture()
        before = copy.deepcopy(p)
        a = ds._analyze_synthetic(p)
        b = ds._analyze_synthetic(p)
        self.assertEqual(p, before)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
