#!/usr/bin/env python3
"""Counts-only independent risk arithmetic; no IDs, labels, sampling or inference.

Only reads the adjacent synthetic/counts fixture. All four-cell matrices are
abstract arithmetic, never a human/reference ledger. No actual CI is generated.
"""
import json
import math
from fractions import Fraction
from pathlib import Path


def ratio(a, b):
    return a / b if b else None


def metrics(cells):
    # Prediction (or coder A) rows, comparator (or coder B) columns.
    a, b, c, d = (Fraction(x) for x in cells)
    assert min(a, b, c, d) >= 0
    n = a + b + c + d
    po = ratio(a + d, n)
    pe = ratio((a + b) * (a + c) + (c + d) * (b + d), n * n)
    return {
        "n": n, "Po": po, "Pe": pe,
        "kappa": None if pe is None else ratio(po - pe, 1 - pe),
        "Precision": ratio(a, a + b), "Recall": ratio(a, a + c),
        "F1": ratio(2 * a, 2 * a + b + c), "Ppos": ratio(2 * a, 2 * a + b + c),
        "left_positive": a + b, "right_positive": a + c,
        "positive_union": a + b + c,
    }


def probability_zero(N, n, T):
    assert all(type(x) is int for x in (N, n, T))
    assert 0 <= n <= N and 0 <= T <= N
    if n > N - T:
        return Fraction(0)
    out = Fraction(1)
    # Equivalent product over the T hidden category units, avoiding any draw.
    for j in range(T):
        out *= Fraction(N - n - j, N - j)
    return out


def hypergeometric_pmf(N, n, T):
    den = math.comb(N, n)
    return {
        k: Fraction(math.comb(T, k) * math.comb(N - T, n - k), den)
        for k in range(max(0, n - (N - T)), min(n, T) + 1)
    }


def check_expected(actual, expected):
    for key, value in expected.items():
        got = None if actual[key] is None else str(actual[key])
        assert got == value, (key, got, value)


def exact_binary_total_variance(N, n, T):
    # Var(N/n * K) for a binary population category, K~Hypergeom(N,T,n).
    if n == N:
        return Fraction(0)
    return Fraction((N - n) * T * (N - T), (N - 1) * n)


def encode(value):
    if isinstance(value, Fraction):
        return {"exact": str(value), "float": float(value)}
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    return value


def run(fixture):
    assert sum(fixture["metadata_counts"].values()) == 4481
    miss_cases = []
    for name, plan in fixture["plans"].items():
        assert plan["remaining_n"] == 600
        assert plan["assigned_n"] == plan["remaining_n"] + plan["exposed_n"]
        for layer in plan["exposed_all_negative_layers"]:
            N, n = layer["N"], layer["n"]
            assert Fraction(n, N) == Fraction(layer["pi_exact"])
            assert Fraction(N, n) == Fraction(layer["weight_exact"])
            for T in fixture["hidden_category_sizes"]:
                zero = probability_zero(N, n, T)
                pmf = hypergeometric_pmf(N, n, T)
                assert sum(pmf.values(), Fraction(0)) == 1
                assert pmf.get(0, Fraction(0)) == zero
                mean = sum((k * p for k, p in pmf.items()), Fraction(0))
                assert mean == Fraction(n * T, N)
                miss_cases.append({
                    "plan": name, "layer": layer["key"], "N": N, "n": n,
                    "synthetic_hidden_category_T": T,
                    "inclusion_probability": Fraction(n, N),
                    "expected_observed_category_count": mean,
                    "miss_probability_exact_hypergeometric_not_CI": zero,
                })
    assert probability_zero(10, 3, 0) == 1
    assert probability_zero(10, 3, 8) == 0
    four_cases = []
    for case in fixture["four_cell_cases"]:
        value = metrics(case["cells"])
        check_expected(value, case["expected"])
        four_cases.append({"id": case["id"], "purpose": case["purpose"], "cells": case["cells"], "metrics": value})
    toy = fixture["synthetic_population_boundary"]
    pop_cells = toy["full_population_four_cells"]
    assert sum(pop_cells) == 4481
    assert [a + b for a, b in zip(toy["target_layer_four_cells"], toy["other_population_four_cells"])] == pop_cells
    population_metrics = metrics(pop_cells)
    check_expected(population_metrics, toy["expected_full_metrics"])
    fn_toy = fixture["synthetic_false_negative_boundary"]
    fn_population_metrics = metrics(fn_toy["full_population_four_cells"])
    check_expected(fn_population_metrics, fn_toy["expected_full_metrics"])
    assert fn_toy["TP_census_count"] <= fn_toy["old_IF_census_region_capacity"]
    possible_samples = []
    variances = []
    for name, plan in fixture["plans"].items():
        layer = next(x for x in plan["exposed_all_negative_layers"] if x["key"] == toy["target_layer"])
        N, n = layer["N"], layer["n"]
        assert sum(toy["target_layer_four_cells"]) == N
        w = Fraction(N, n)
        sample_n = plan["assigned_n"]
        for count in (0, 1):
            # Both samples are feasible within the synthetic population category capacities.
            in_layer = [count, 0, 0, n - count]
            assert all(s <= p for s, p in zip(in_layer, toy["target_layer_four_cells"]))
            raw = [count, 0, 0, sample_n - count]
            weighted = [w * count, 0, 0, Fraction(4481) - w * count]
            assert sum(raw) == sample_n and sum(weighted) == 4481
            value = metrics(weighted)
            if count == 0:
                assert all(value[k] is None for k in ("kappa", "Precision", "Recall", "F1"))
            else:
                assert all(value[k] == 1 for k in ("kappa", "Precision", "Recall", "F1"))
            possible_samples.append({
                "plan": name, "pattern": "miss_all_24_active_categories" if count == 0 else "one_TP_and_no_FP_FN",
                "in_layer_raw_cells": in_layer, "all_sample_raw_cells": raw,
                "all_domain_HT_cells": weighted, "HT_metrics": value,
                "raw_predicted_positive_units": count, "raw_comparator_positive_units": count,
                "positive_weight_Kish_information_diagnostic_not_CI": None if count == 0 else Fraction(1),
                "miss_active_union_probability": probability_zero(N, n, 24) if count == 0 else None,
            })
        # Complementary sparse-error case: positive margin can be nonzero while hidden FN are missed.
        tp = fn_toy["TP_census_count"]
        observed_no_fn = [tp, 0, 0, 4481 - tp]
        assert all(metrics(observed_no_fn)[key] == 1 for key in ("kappa", "Precision", "Recall", "F1"))
        possible_samples.append({
            "plan": name, "pattern": "80_census_TP_but_miss_all_20_hidden_FN",
            "all_domain_HT_cells": observed_no_fn, "HT_metrics": metrics(observed_no_fn),
            "raw_comparator_positive_units": tp, "miss_FN_probability": probability_zero(N, n, 20),
        })
        # Exact design variance of a SYNTHETIC category total; neither a CI nor a metric width.
        T = 20
        pmf = hypergeometric_pmf(N, n, T)
        estimated_mean = sum((w * k * p for k, p in pmf.items()), Fraction(0))
        assert estimated_mean == T  # Design validity remains despite auxiliary/actual mismatch.
        direct_variance = sum(((w * k - T) ** 2 * p for k, p in pmf.items()), Fraction(0))
        variance = exact_binary_total_variance(N, n, T)
        assert direct_variance == variance
        benchmark = exact_binary_total_variance(4481, sample_n, T)
        variances.append({
            "plan": name, "synthetic_category_T": T,
            "all_category_units_in_low_pi_layer": toy["target_layer"],
            "HT_expectation": estimated_mean,
            "exact_design_variance_of_synthetic_category_total_not_CI": variance,
            "hypothetical_unstratified_same_n_SRS_variance_not_alternative_plan": benchmark,
            "variance_ratio_to_benchmark": variance / benchmark,
        })
    return {
        "status": "passed_independent_counts_only_synthetic_risk_arithmetic",
        "real_ID_draws": 0, "real_human_reference_labels": 0, "new_model_calls": 0,
        "actual_CI_generated": False, "CI_gate_added": False,
        "miss_probability_cases": miss_cases,
        "four_cell_cases": four_cases,
        "synthetic_full_population_boundary": {"cells": pop_cells, "metrics": population_metrics},
        "synthetic_false_negative_boundary": {"cells": fn_toy["full_population_four_cells"], "metrics": fn_population_metrics},
        "legal_synthetic_sample_patterns": possible_samples,
        "auxiliary_mismatch_design_validity_and_efficiency": variances,
        "formal_acceptance": False,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    fixture = json.loads((root / "risk-inputs-and-toy-cases.json").read_text())
    result = run(fixture)
    target = root / "risk-math-results.json"
    target.write_text(json.dumps(encode(result), ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "miss_probability_cases": len(result["miss_probability_cases"]), "four_cell_cases": len(result["four_cell_cases"]), "legal_sample_patterns": len(result["legal_synthetic_sample_patterns"]), "output": str(target)}, ensure_ascii=False))
