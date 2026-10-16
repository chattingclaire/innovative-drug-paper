#!/usr/bin/env python3
"""Independent finite-count synthetic comparison QA; never imports main code.

Uses only the earlier independent mathematical helpers in this same directory,
fixed metadata/auxiliary labels, and aggregate synthetic planning JSON. Reads
the parent implementation as bytes for SHA256 binding only. No real reference
labels, ID sampling, model execution, or main-engine execution is performed.
"""
from collections import Counter
from fractions import Fraction as F
from itertools import combinations
import json
import math
from pathlib import Path
from statistics import NormalDist

import independent_full_domain_checks as independent

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "independent-math"
CHECKS = []
SCOPES = ("ALL", "remaining", "exposed")
METRICS = ("kappa", "precision", "recall", "F1")
Z95 = NormalDist().inv_cdf(0.975)


def check(name, condition, detail=None):
    CHECKS.append({"name": name, "passed": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(name)


def close(a, b, rel=2e-10, abs_tol=2e-10):
    return a is None and b is None if a is None or b is None else math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_tol)


def gradients(cells):
    a, b, c, d = map(F, cells)
    p, r, f = a + b, a + c, 2 * a + b + c
    result = {"precision": [b / p**2, -a / p**2, F(0), F(0)] if p else None,
              "recall": [c / r**2, F(0), -a / r**2, F(0)] if r else None,
              "F1": [2 * (b + c) / f**2, -2 * a / f**2, -2 * a / f**2, F(0)] if f else None}
    numerator = 2 * (a * d - b * c)
    denominator = (a + b) * (b + d) + (a + c) * (c + d)
    if denominator:
        dn = [2 * d, -2 * c, -2 * b, 2 * a]
        dd = [b + c + 2 * d, a + 2 * b + d, a + 2 * c + d, 2 * a + b + c]
        result["kappa"] = [(dn[i] * denominator - numerator * dd[i]) / denominator**2 for i in range(4)]
    else:
        result["kappa"] = None
    return result


def continuous_metrics(cells):
    a, b, c, d = cells
    N = a + b + c + d
    po = (a + d) / N
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / N**2
    # Use the agreement/marginal definition, independent of the cross-product
    # formula used for exact point values and closed-form gradient.
    return {"kappa": (po - pe) / (1 - pe), "precision": a / (a + b),
            "recall": a / (a + c), "F1": 2 * a / (2 * a + b + c)}


def numerical_gradients(cells):
    result = {m: {"complex_step": [], "central_five_point": []} for m in METRICS}
    for i in range(4):
        values = [complex(x) for x in cells]
        values[i] += complex(0, 1e-20)
        complex_values = continuous_metrics(values)
        step = max(1.0, cells[i]) * 1e-4
        offsets = []
        for scale in (-2, -1, 1, 2):
            values = [float(x) for x in cells]
            values[i] += scale * step
            offsets.append(continuous_metrics(values))
        for m in METRICS:
            result[m]["complex_step"].append(complex_values[m].imag / 1e-20)
            result[m]["central_five_point"].append((offsets[0][m] - 8 * offsets[1][m] + 8 * offsets[2][m] - offsets[3][m]) / (12 * step))
    return result


def variance(gradient, cov):
    return None if gradient is None else sum(gradient[i] * cov[i][j] * gradient[j] for i in range(4) for j in range(4))


def determinant(matrix):
    work = [list(row) for row in matrix]
    det = F(1)
    for i in range(len(work)):
        pivot = next((k for k in range(i, len(work)) if work[k][i]), None)
        if pivot is None:
            return F(0)
        if pivot != i:
            work[i], work[pivot] = work[pivot], work[i]
            det = -det
        value = work[i][i]
        det *= value
        for k in range(i + 1, len(work)):
            ratio = work[k][i] / value
            for j in range(i + 1, len(work)):
                work[k][j] -= ratio * work[i][j]
            work[k][i] = F(0)
    return det


def psd_exact(matrix):
    if any(matrix[i][j] != matrix[j][i] for i in range(4) for j in range(4)):
        return False
    # A real symmetric matrix is PSD iff every principal minor is nonnegative.
    return all(determinant([[matrix[i][j] for j in subset] for i in subset]) >= 0
               for size in range(1, 5) for subset in combinations(range(4), size))


def scope_keys(scope, strata):
    return [k for k in strata if scope == "ALL" or strata[k]["domain"] == scope]


def evaluate_cells(cells, plan, scope):
    keys = scope_keys(scope, plan)
    total = [sum(cells[k][i] for k in keys) for i in range(4)]
    cov = independent.add_matrices([independent.cell_covariance(cells[k], plan[k]["N"], plan[k]["n"]) for k in keys])
    points = independent.metrics(total)
    grad = gradients(total)
    metric_results = {}
    for m in METRICS:
        var = variance(grad[m], cov)
        assert var is None or var >= 0
        se = math.sqrt(float(var)) if var is not None else None
        metric_results[m] = {"point": points[m], "variance": var, "SE": se,
                             "halfwidth": Z95 * se if se is not None else None}
    return {"cells": total, "N": sum(plan[k]["N"] for k in keys), "cov": cov,
            "expected_raw_reference_positive": sum(F(plan[k]["n"], plan[k]["N"]) * (cells[k][0] + cells[k][2]) for k in keys),
            "metrics": metric_results}


def check_payload(label, payload, expected):
    check(label + ": four cells and population total", payload["synthetic_four_a_b_c_d"] == expected["cells"] and payload["population_N"] == expected["N"])
    a, b, c, _ = expected["cells"]
    check(label + ": both positive margins", payload["prediction_or_A_positive"] == a + b and payload["reference_or_B_positive"] == a + c)
    check(label + ": expected raw reference count", close(payload["anticipated_raw_reference_positive_observations"], expected["expected_raw_reference_positive"]))
    check(label + ": exact FPC covariance", all(close(payload["anticipated_four_cell_total_covariance"][i][j], expected["cov"][i][j]) for i in range(4) for j in range(4)))
    check(label + ": point, closed-form gradient SE and normal .975 quantile", all(close(payload["metrics"][m]["synthetic_population_point"], expected["metrics"][m]["point"]) and close(payload["metrics"][m]["anticipated_linearization_SE"], expected["metrics"][m]["SE"]) and close(payload["metrics"][m]["normal95_planning_halfwidth"], expected["metrics"][m]["halfwidth"]) for m in METRICS))
    check(label + ": width marked synthetic planning diagnostic", "not actual data" in payload["width_role"] and "primary bootstrap CI" in payload["width_role"])


def check_domain_and_budget(label, expected, allocation_results, method=None):
    for name in ("full800", "full1000"):
        e = expected[name]
        check(label + " " + name + ": full cells=sum of domain cells", e["ALL"]["cells"] == [e["remaining"]["cells"][i] + e["exposed"]["cells"][i] for i in range(4)])
        check(label + " " + name + ": full covariance=sum of independent domains", e["ALL"]["cov"] == independent.add_matrices([e["remaining"]["cov"], e["exposed"]["cov"]]))
    remaining_small = allocation_results["full800"]["remaining"]
    remaining_large = allocation_results["full1000"]["remaining"]
    if method:
        remaining_small, remaining_large = remaining_small["methods"][method], remaining_large["methods"][method]
    check(label + ": remaining diagnostics exactly unchanged", remaining_small == remaining_large and expected["full800"]["remaining"] == expected["full1000"]["remaining"])
    for scope in SCOPES:
        small, large = expected["full800"][scope], expected["full1000"][scope]
        diff = [[small["cov"][i][j] - large["cov"][i][j] for j in range(4)] for i in range(4)]
        check(label + " " + scope + ": covariance decrease exact PSD", psd_exact(diff))
        check(label + " " + scope + ": diagnostic variance does not increase", all(small["metrics"][m]["variance"] is None and large["metrics"][m]["variance"] is None or small["metrics"][m]["variance"] is not None and large["metrics"][m]["variance"] <= small["metrics"][m]["variance"] for m in METRICS))


def hypergeom_probability(N, K, n, x):
    if x < max(0, n - N + K) or x > min(K, n):
        return F(0)
    return F(math.comb(K, x) * math.comb(N - K, n - x), math.comb(N, n))


def main():
    state = independent.metadata_checks()
    allocation_path, comparison_path = ROOT / "full-domain-allocation.json", ROOT / "full-domain-comparison.json"
    implementation_path = ROOT / "full_domain_plan.py"
    allocation, comparison = independent.read_json(allocation_path), independent.read_json(comparison_path)
    check("comparison binds unchanged allocation", comparison["allocation_sha256"] == independent.digest(allocation_path) == "a27b6f4228b11714c0f2b3c9ea0d3dc9ec55f9591708ac3d361f33f9b4831a57")
    check("comparison binds current parent script bytes", comparison["script_sha256"] == independent.digest(implementation_path))
    check("comparison planning interval role and no new acceptance gate", comparison["planning_widths_are_not_actual_primary_CIs"] is True and comparison["CI_halfwidth_or_lower_bound_gate_added"] is False and "bootstrap5000 seed20261010" in comparison["actual_primary_CI_contract"])
    plans = {name: {r["key"]: r for r in p["strata"]} for name, p in allocation["plans"].items()}
    for name, summary in comparison["plans"].items():
        check(name + ": plan summary unchanged", summary == {k: v for k, v in allocation["plans"][name].items() if k not in ("strata", "exposed_increment_allocation_trace", "cross_stratum_joint_second_order_probabilities")})
    check("two budgets monotone in every fixed stratum", set(plans["full800"]) == set(plans["full1000"]) and all(plans["full800"][k]["N"] == plans["full1000"][k]["N"] and plans["full800"][k]["n"] <= plans["full1000"][k]["n"] for k in plans["full800"]))
    micro_by_dimension = {d: Counter((independent.full_stratum_key(r), r["rules39"][d], r["LLM03"][d]) for r in state["rows"]) for d in independent.DIMS}
    check("all old positive totals are independently bound metadata counts", all(comparison["population_old_auxiliary_positive_counts"][scope][m][d] == sum(r[m][d] for r in state["rows"] if scope == "ALL" or independent.domain(r) == scope) for scope in SCOPES for m in independent.METHODS for d in independent.DIMS))
    machines = comparison["machine_synthetic_scenarios"]
    humans = comparison["human_synthetic_scenarios"]
    check("90 distinct machine synthetic scenarios", len(machines) == len({s["id"] for s in machines}) == 90 and {s["dimension"] for s in machines} == set(independent.DIMS))
    check("36 distinct human synthetic scenarios", len(humans) == len({s["id"] for s in humans}) == 36)
    independently_anticipated = {}
    for scenario in machines:
        label = "machine " + scenario["id"]
        micro = scenario["joint_micro_counts"]
        seen = [(r["stratum"], r["old_rules39"], r["old_LLM03"]) for r in micro]
        expected_micro = micro_by_dimension[scenario["dimension"]]
        check(label + ": exact joint old prediction micro capacities", len(seen) == len(set(seen)) and set(seen) == set(expected_micro) and all(r["capacity"] == expected_micro[(r["stratum"], r["old_rules39"], r["old_LLM03"])] for r in micro))
        check(label + ": legal shared reference within each capacity", all(type(r["synthetic_reference_positive"]) is int and 0 <= r["synthetic_reference_positive"] <= r["capacity"] for r in micro) and sum(r["synthetic_reference_positive"] for r in micro) == scenario["synthetic_reference_positive_total"])
        check(label + ": exact finite reference target", scenario["synthetic_reference_positive_total"] == round(4481 * scenario["prevalence_grid"]))
        cells = {m: {k: [0, 0, 0, 0] for k in plans["full800"]} for m in independent.METHODS}
        for item in micro:
            for m in independent.METHODS:
                positive, capacity, reference = item["old_" + m], item["capacity"], item["synthetic_reference_positive"]
                contribution = [reference, capacity - reference, 0, 0] if positive else [0, 0, reference, capacity - reference]
                cells[m][item["stratum"]] = [x + y for x, y in zip(cells[m][item["stratum"]], contribution)]
        check(label + ": same reference margin for both methods in every stratum", all(cells["rules39"][k][0] + cells["rules39"][k][2] == cells["LLM03"][k][0] + cells["LLM03"][k][2] for k in plans["full800"]))
        check(label + ": both method cells legal with frozen old prediction margins", all(sum(cells[m][k]) == plans["full800"][k]["N"] and all(type(x) is int and x >= 0 for x in cells[m][k]) and cells[m][k][0] + cells[m][k][1] == sum(r["capacity"] * r["old_" + m] for r in micro if r["stratum"] == k) for m in independent.METHODS for k in plans["full800"]))
        independently_anticipated[scenario["id"]] = {}
        for m in independent.METHODS:
            expected = {name: {scope: evaluate_cells(cells[m], plan, scope) for scope in SCOPES} for name, plan in plans.items()}
            independently_anticipated[scenario["id"]][m] = expected
            for name in plans:
                for scope in SCOPES:
                    check_payload(label + " " + m + " " + name + " " + scope, scenario["allocation_results"][name][scope]["methods"][m], expected[name][scope])
            check_domain_and_budget(label + " " + m, expected, scenario["allocation_results"], m)
        check(label + ": remaining shared count shortfall unchanged", scenario["allocation_results"]["full800"]["remaining"]["raw_reference_positive_count_shortfall"] == scenario["allocation_results"]["full1000"]["remaining"]["raw_reference_positive_count_shortfall"])
    infeasible_nominal = 0
    human_expected = {}
    for scenario in humans:
        label = "human " + scenario["id"]
        cells = scenario["synthetic_stratum_four_cells"]
        check(label + ": all 41 legal integer stratum cells", set(cells) == set(plans["full800"]) and all(len(cells[k]) == 4 and all(type(x) is int and x >= 0 for x in cells[k]) and sum(cells[k]) == plans["full800"][k]["N"] for k in cells))
        total = [sum(cells[k][i] for k in cells) for i in range(4)]
        P, Q, N = scenario["A_positive"], scenario["B_positive"], 4481
        check(label + ": global paired margins and exact actual kappa", total == scenario["synthetic_total_four_a_b_c_d"] and total[0] + total[1] == P and total[0] + total[2] == Q and close(independent.metrics(total)["kappa"], scenario["actual_finite_kappa"]))
        requested_a = (F(str(scenario["requested_kappa"])) * (N * (P + Q) - 2 * P * Q) / 2 + P * Q) / N
        feasible = max(0, P + Q - N) <= requested_a <= min(P, Q)
        check(label + ": requested-kappa feasibility flag", scenario["requested_kappa_feasible_at_margins"] is feasible)
        infeasible_nominal += not feasible
        expected = {name: {scope: evaluate_cells(cells, plan, scope) for scope in SCOPES} for name, plan in plans.items()}
        human_expected[scenario["id"]] = expected
        for name in plans:
            for scope in SCOPES:
                check_payload(label + " " + name + " " + scope, scenario["allocation_results"][name][scope], expected[name][scope])
        check_domain_and_budget(label, expected, scenario["allocation_results"])
    maxima_checked = 0
    for name, scopes in comparison["machine_planning_grid_maxima"].items():
        for scope, dimensions in scopes.items():
            for dimension, methods in dimensions.items():
                for method, maximum_metrics in methods.items():
                    for metric, summary in maximum_metrics.items():
                        candidates = [(s["id"], independently_anticipated[s["id"]][method][name][scope]["metrics"][metric]) for s in machines if s["dimension"] == dimension]
                        defined = [(sid, obj) for sid, obj in candidates if obj["halfwidth"] is not None]
                        sid, obj = max(defined, key=lambda pair: pair[1]["halfwidth"])
                        check("grid maximum " + "|".join((name, scope, dimension, method, metric)), close(summary["max_grid_halfwidth"], obj["halfwidth"]) and close(summary["synthetic_point_at_that_max"], obj["point"]) and summary["scenario"] == sid and summary["undefined_scenarios"] == len(candidates) - len(defined))
                        maxima_checked += 1
    asymmetric = next(s for s in humans if s["A_positive"] != s["B_positive"] and all(s["synthetic_total_four_a_b_c_d"]))
    asym_cells = asymmetric["synthetic_total_four_a_b_c_d"]
    closed, numeric = gradients(asym_cells), numerical_gradients(asym_cells)
    check("asymmetric independent complex-step and five-point gradients match closed form", all(close(closed[m][i], numeric[m]["complex_step"][i], rel=1e-8, abs_tol=1e-12) and close(closed[m][i], numeric[m]["central_five_point"][i], rel=2e-6, abs_tol=2e-11) for m in METRICS for i in range(4)))
    asymmetric_summary = {"scenario": asymmetric["id"], "cells": asym_cells, "closed_form_gradients": closed, "numerical_gradients": numeric, "plans": {}}
    for name in plans:
        cov = human_expected[asymmetric["id"]][name]["ALL"]["cov"]
        asymmetric_summary["plans"][name] = human_expected[asymmetric["id"]][name]["ALL"]["metrics"]
        check(name + ": asymmetric numerical-gradient width agrees with report", all(close(math.sqrt(float(variance(numeric[m]["complex_step"], cov))) * Z95, asymmetric["allocation_results"][name]["ALL"]["metrics"][m]["normal95_planning_halfwidth"], rel=1e-8, abs_tol=1e-10) for m in METRICS))
    shift = comparison["future_prediction_auxiliary_shift_synthetic_example"]
    target = "exposed|NHSA|6_ALL_NEG"
    check("shift example exact synthetic finite table", shift["stratum"] == target and shift["stratum_population_cells_TP_FP_FN_TN"] == [41, 9, 9, 761] and shift["old_auxiliary_positive_in_stratum"] == 0 and shift["future_synthetic_prediction_positive"] == shift["synthetic_reference_positive"] == 50 and plans["full800"][target]["N"] == 820 and plans["full800"][target]["n"] == 30 and plans["full1000"][target]["n"] == 59)
    shift_cells = {k: ([41, 9, 9, 761] if k == target else [0, 0, 0, v["N"]]) for k, v in plans["full800"].items()}
    shift_summary = {}
    for name, plan in plans.items():
        expected = evaluate_cells(shift_cells, plan, "ALL")
        payload = shift["allocation_results"][name]
        check_payload("shift " + name, payload["full"], expected)
        n = plan[target]["n"]
        zero = hypergeom_probability(820, 50, n, 0)
        below5 = sum(hypergeom_probability(820, 50, n, x) for x in range(5))
        check("shift " + name + ": hypergeometric miss/shortfall and expected counts", payload["stratum_n"] == n and close(payload["expected_raw_predicted_positive_observations"], F(n * 50, 820)) and close(payload["no_raw_prediction_positive_observed_probability"], zero) and close(payload["no_raw_reference_positive_observed_probability"], zero) and close(payload["raw_reference_positives_below5_probability"], below5))
        shift_summary[name] = {"n": n, "expected_raw_positive": F(n * 50, 820), "miss_all_probability": zero, "raw_positives_below5_probability": below5, "metrics": expected["metrics"]}
    for risk in comparison["both_old_auxiliary_negative_hidden_positive_risks"]:
        plan = plans[risk["plan"]][risk["stratum"]]
        check("hidden-positive risk " + risk["plan"] + " " + risk["stratum"], risk["N"] == plan["N"] and risk["n"] == plan["n"] and all(close(value, hypergeom_probability(risk["N"], int(K), risk["n"], 0)) for K, value in risk["miss_all_hidden_positives_probability"].items()))
    bindings = {str(p): independent.digest(p) for p in (allocation_path, comparison_path, ROOT / "full-domain-comparison.md", implementation_path, Path(__file__), Path(independent.__file__))}
    result = {"status": "PASS_INDEPENDENT_AGGREGATE_SYNTHETIC_COMPARISON", "date": "2026-10-10", "main_script_imported_or_executed": False,
              "read_scope": "fixed permitted metadata/old labels and aggregate synthetic planning; main script bytes used for hash only",
              "bindings_sha256": {**state["bindings"], **bindings}, "machine_scenarios": len(machines), "human_scenarios": len(humans),
              "infeasible_requested_human_kappa_scenarios_explicitly_flagged": infeasible_nominal, "grid_maxima_checked": maxima_checked,
              "covariance_difference_PSD_check": "all 15 principal minors checked exactly for each 4x4 difference",
              "normal95_z_quantile": Z95,
              "asymmetric_gradient_and_width_check": asymmetric_summary, "auxiliary_shift_check": shift_summary,
              "all_checks_passed": all(c["passed"] for c in CHECKS), "check_count": len(CHECKS), "checks": CHECKS}
    output = OUTDIR / "independent_synthetic_comparison_results.json"
    output.write_text(json.dumps(independent.as_json(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(CHECKS), "machines": len(machines), "humans": len(humans), "maxima": maxima_checked, "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
