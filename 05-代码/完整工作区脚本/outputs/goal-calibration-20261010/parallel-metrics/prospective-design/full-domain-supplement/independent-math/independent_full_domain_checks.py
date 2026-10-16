#!/usr/bin/env python3
"""Independent metadata-only and exact synthetic SRSWOR checks.

No imports from the planning/statistics engines; no real ID selection, models,
body/context/gold access, or actual new-label estimation.  Toy enumeration uses
artificial integer positions only.  The output contains no real IDs.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import combinations, product
import hashlib
import json
import math
from pathlib import Path

OUTDIR = Path(__file__).resolve().parent
BASE = OUTDIR.parent.parent
DIMS = ("S", "E", "Ec", "I", "F")
METHODS = ("rules39", "LLM03")
PRIORITIES = {"1_I_DISAGREEMENT": 6, "2_F_DISAGREEMENT": 5, "3_OTHER_DISAGREEMENT": 3,
              "4_IF_AGREE_POS": 3, "5_OTHER_AGREE_POS": 2, "6_ALL_NEG": 1}
CHECKS = []


def check(name, condition, detail=None):
    CHECKS.append({"name": name, "passed": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(name)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_json(value):
    if isinstance(value, F):
        return {"exact": str(value), "value": float(value)}
    if isinstance(value, dict):
        return {str(k): as_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_json(v) for v in value]
    return value


def probabilities(N, n):
    assert type(N) is int and type(n) is int and 1 <= n <= N
    return {"pi": F(n, N), "weight": F(N, n),
            "same_stratum_pair_pi": F(n * (n - 1), N * (N - 1)) if N > 1 else None,
            "census": n == N}


def close(left, right):
    return left is None if right is None else math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-12)


def domain(row):
    return "remaining" if row["exposure"] == "remaining" else "exposed"


def stratum_key(row):
    signature = "".join(str(row[m][d]) for d in ("I", "F") for m in METHODS)
    if signature != "0000":
        tag = "IF"
    elif any(row["rules39"][d] != row["LLM03"][d] for d in ("S", "E", "Ec")):
        tag = "OTHER_DISAGREEMENT"
    elif any(row[m][d] for m in METHODS for d in ("S", "E", "Ec")):
        tag = "OTHER_AGREE_POS"
    else:
        tag = "ALL_NEG"
    return f"{row['department']}|{signature}|{tag}"


def full_stratum_key(row):
    if domain(row) == "remaining":
        return "remaining|" + stratum_key(row)
    if row["rules39"]["I"] != row["LLM03"]["I"]:
        tag = "1_I_DISAGREEMENT"
    elif row["rules39"]["F"] != row["LLM03"]["F"]:
        tag = "2_F_DISAGREEMENT"
    elif any(row["rules39"][d] != row["LLM03"][d] for d in ("S", "E", "Ec")):
        tag = "3_OTHER_DISAGREEMENT"
    elif any(row[m][d] for m in METHODS for d in ("I", "F")):
        tag = "4_IF_AGREE_POS"
    elif any(row[m][d] for m in METHODS for d in ("S", "E", "Ec")):
        tag = "5_OTHER_AGREE_POS"
    else:
        tag = "6_ALL_NEG"
    return f"exposed|{row['department']}|{tag}"


def verify_stratum(row, expected_N, label):
    N, n = row["N"], row["n"]
    p = probabilities(N, n)
    check(label + ": N matches independently classified frame", N == expected_N)
    check(label + ": bootstrap-feasible n", n == N or n >= 2)
    for field, value in p.items():
        if field in row:
            check(label + ": " + field, row[field] == value if field == "census" else close(row[field], value))
    check(label + ": exact weight sum", n * p["weight"] == N)
    return p


def metadata_checks():
    path = BASE / "inputs/metadata-and-fixed-labels.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    check("whitelist fields only", all(set(r) == {"id", "department", "family", "exposure", *METHODS} for r in rows))
    check("exact 4481 unique nonempty fixed-frame IDs", len(rows) == 4481 and all(isinstance(r["id"], str) and r["id"] for r in rows) and len({r["id"] for r in rows}) == 4481)
    check("fixed exposure categories only", all(r["exposure"] in {"remaining", "direct", "family_only"} for r in rows))
    check("fixed department categories only", all(r["department"] in {"NHC", "NHSA", "NMPA"} for r in rows))
    check("five fixed old binary labels per method", all(set(r[m]) == set(DIMS) and all(type(r[m][d]) is int and r[m][d] in (0, 1) for d in DIMS) for r in rows for m in METHODS))
    domain_counts = Counter(domain(r) for r in rows)
    department_counts = Counter(r["department"] for r in rows)
    domain_department = Counter((domain(r), r["department"]) for r in rows)
    counts = Counter((domain(r), stratum_key(r)) for r in rows)
    check("disjoint exhaustive two-domain partition", domain_counts == {"remaining": 1444, "exposed": 3037} and sum(counts.values()) == 4481)
    check("full department totals", department_counts == {"NHC": 533, "NHSA": 2100, "NMPA": 1848})
    old_path = BASE / "small-plan-comparison.json"
    old = read_json(old_path)
    old_map = {r["key"]: r for r in old["strata"]}
    rem_keys = {k for d, k in counts if d == "remaining"}
    check("old plan exactly covers 23 remaining strata", len(old_map) == len(old["strata"]) == 23 and set(old_map) == rem_keys)
    for key, item in old_map.items():
        verify_stratum(item, counts[("remaining", key)], "old600 " + key)
    check("old remaining allocation is 600 of 1444", sum(r["N"] for r in old_map.values()) == 1444 and sum(r["n"] for r in old_map.values()) == 600)
    binding_paths = [BASE / "source-bindings.json", BASE / "supplemental-source-bindings.json"]
    binding = read_json(binding_paths[0])
    check("metadata hash matches frozen projection binding", digest(path) == binding["projection"]["sha256"] == old["projected_inputs_sha256"])
    check("old plan source binding hash matches", digest(binding_paths[0]) == old["source_bindings_sha256"])
    old_positive = {m: {d: sum(r[m][d] for r in rows) for d in DIMS} for m in METHODS}
    check("fixed label counts match source binding QA", all(old_positive[m] == binding["QA"][m]["positive_by_dimension"] for m in METHODS))
    return {"counts": counts, "rows": rows, "old_map": old_map,
            "summary": {"N": len(rows), "domain_N": dict(domain_counts), "department_N": dict(department_counts),
                        "domain_department_N": {d: {dep: domain_department[(d, dep)] for dep in sorted(department_counts)} for d in sorted(domain_counts)},
                        "remaining_old_strata": len(rem_keys),
                        "planned_full_audit_domain_strata": dict(Counter(k.split("|")[0] for k in {full_stratum_key(r) for r in rows})),
                        "planned_exposed_minimum_feasible_n": sum(min(2, N) for k, N in Counter(full_stratum_key(r) for r in rows).items() if k.startswith("exposed|"))},
            "bindings": {str(p): digest(p) for p in [path, old_path, *binding_paths]}}


def exact_inclusion_checks():
    designs = 0
    for N in range(1, 9):
        for n in range(1, N + 1):
            samples = list(combinations(range(N), n))
            q = probabilities(N, n)
            for i in range(N):
                assert F(sum(i in s for s in samples), len(samples)) == q["pi"]
                for j in range(i + 1, N):
                    assert F(sum(i in s and j in s for s in samples), len(samples)) == q["same_stratum_pair_pi"]
            designs += 1
    check("exact synthetic first and second-order probabilities", True, {"finite_designs": designs, "artificial_N_max": 8})
    for N1, n1, N2, n2 in ((4, 2, 5, 3), (1, 1, 3, 2), (3, 3, 4, 4)):
        sample_pairs = list(product(combinations(range(N1), n1), combinations(range(N2), n2)))
        actual = F(sum(0 in s1 and 0 in s2 for s1, s2 in sample_pairs), len(sample_pairs))
        assert actual == F(n1, N1) * F(n2, N2)
    check("exact synthetic cross-stratum pi products", True)
    check("singleton census has pi=weight=1 and no distinct pair", probabilities(1, 1) == {"pi": F(1), "weight": F(1), "same_stratum_pair_pi": None, "census": True})
    return {"enumerated_designs": designs}


def cell_covariance(cells, N, n):
    assert len(cells) == 4 and all(type(c) is int and c >= 0 for c in cells) and sum(cells) == N
    if n == N:
        return [[F(0) for _ in cells] for _ in cells]
    multiplier = F(N * (N - n), n * (N - 1))
    return [[multiplier * ((cells[i] if i == j else 0) - F(cells[i] * cells[j], N)) for j in range(4)] for i in range(4)]


def add_matrices(mats):
    return [[sum(m[i][j] for m in mats) for j in range(4)] for i in range(4)]


def metrics(cells):
    a, b, c, d = map(F, cells)
    k_den = (a + b) * (b + d) + (a + c) * (c + d)
    return {"precision": a / (a + b) if a + b else None,
            "recall": a / (a + c) if a + c else None,
            "F1": 2 * a / (2 * a + b + c) if 2 * a + b + c else None,
            "kappa": 2 * (a * d - b * c) / k_den if k_den else None}


def exact_four_cell_checks():
    # These artificial populations have no connection to project IDs or labels.
    strata = [{"domain": "remaining", "N": 5, "n": 3, "cells": [1, 1, 1, 2]},
              {"domain": "exposed", "N": 4, "n": 2, "cells": [2, 1, 0, 1]},
              {"domain": "remaining", "N": 1, "n": 1, "cells": [0, 0, 0, 1]}]
    all_options = []
    for s in strata:
        categories = [i for i, c in enumerate(s["cells"]) for _ in range(c)]
        options = []
        for positions in combinations(range(s["N"]), s["n"]):
            counts = Counter(categories[p] for p in positions)
            options.append([F(s["N"], s["n"]) * counts[j] for j in range(4)])
        all_options.append(options)
    totals = [[sum(v[j] for v in joint) for j in range(4)] for joint in product(*all_options)]
    population = [sum(s["cells"][j] for s in strata) for j in range(4)]
    means = [sum(t[j] for t in totals) / len(totals) for j in range(4)]
    enum_cov = [[sum((t[i] - means[i]) * (t[j] - means[j]) for t in totals) / len(totals) for j in range(4)] for i in range(4)]
    analytic_cov = add_matrices([cell_covariance(s["cells"], s["N"], s["n"]) for s in strata])
    check("legal integer synthetic four cells", all(sum(s["cells"]) == s["N"] for s in strata))
    check("enumerated HT four-cell means equal true totals", means == population)
    check("enumerated true covariance equals exact FPC formula", enum_cov == analytic_cov, {"joint_samples": len(totals)})
    check("four-cell covariance respects fixed total", all(sum(row) == 0 for row in analytic_cov))
    rem = [sum(s["cells"][j] for s in strata if s["domain"] == "remaining") for j in range(4)]
    exp = [sum(s["cells"][j] for s in strata if s["domain"] == "exposed") for j in range(4)]
    rem_metric, exp_metric, full_metric = metrics(rem), metrics(exp), metrics(population)
    weighted_metric = {m: F(6, 10) * rem_metric[m] + F(4, 10) * exp_metric[m] for m in full_metric}
    check("nonlinear pooled metrics differ from N-weighted domain metrics", all(full_metric[m] != weighted_metric[m] for m in full_metric))
    return {"status": "SYNTHETIC_ONLY", "orientation": ["aTP", "bFP", "cFN", "dTN"], "strata": strata,
            "joint_samples": len(totals), "true_full_cells": population, "true_covariance_HT": analytic_cov,
            "domain_metrics": {"remaining": rem_metric, "exposed": exp_metric}, "pooled_full_metrics": full_metric,
            "incorrect_N_weighted_domain_metrics": weighted_metric}


def allocation_checks(state, path):
    check("allocation input is the authorized exact planning file", path == OUTDIR.parent / "full-domain-allocation.json")
    allocation = read_json(path)
    rows, old_map = state["rows"], state["old_map"]
    counts = Counter(full_stratum_key(r) for r in rows)
    check("full-frame independent assignment is 41 nonempty strata", len(counts) == 41 and sum(counts.values()) == 4481)
    check("18 exposed strata independent coverage", sum(k.startswith("exposed|") for k in counts) == 18 and sum(N for k, N in counts.items() if k.startswith("exposed|")) == 3037)
    assignments = [{"id": r["id"], "stratum": full_stratum_key(r)} for r in sorted(rows, key=lambda r: r["id"])]
    assignments_hash = hashlib.sha256(json.dumps(assignments, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
    check("complete deterministic frame assignment hash agrees", assignments_hash == allocation["full_frame_stratum_assignment_hash_only"])
    check("allocation reads the identical metadata projection", allocation["permitted_input_projection"]["sha256"] == state["bindings"][str(BASE / "inputs/metadata-and-fixed-labels.jsonl")])
    check("allocation preserves bound prior remaining plan", allocation["prior_remaining_plan_sha256"] == state["bindings"][str(BASE / "small-plan-comparison.json")])
    check("allocation population headers", allocation["population_N"] == 4481 and allocation["population_department_N"] == state["summary"]["department_N"] and allocation["exposed_domain_N"] == 3037 and allocation["fixed_remaining_design_N"] == 1444 and allocation["fixed_remaining_design_n"] == 600)
    check("allocation priority specification", allocation["priority_factors"] == PRIORITIES)
    check("allocation has no actual draw, new model or human labels", all(allocation[k] is False for k in ("new_human_reference_labels_created", "unseen_body_context_or_real_reference_read", "new_machine_inference", "sample_ID_drawn")))
    check("two budget alternatives exactly", set(allocation["plans"]) == {"full800", "full1000"})
    plan_results = {}
    for name, total_n, exp_n in (("full800", 800, 200), ("full1000", 1000, 400)):
        plan = allocation["plans"][name]
        mapping = {r["key"]: r for r in plan["strata"]}
        check(name + ": every eligible ID has exactly one positive-pi stratum", len(mapping) == len(plan["strata"]) == len(counts) and set(mapping) == set(counts))
        independent_probs = {}
        for key, item in mapping.items():
            p = verify_stratum(item, counts[key], name + " " + key)
            independent_probs[key] = p
            check(name + " " + key + ": domain/department", item["domain"] == key.split("|")[0] and item["department"] == key.split("|")[1])
            check(name + " " + key + ": exact pi/weight/pair", item["pi_exact"] == str(p["pi"]) and item["weight_exact"] == str(p["weight"]) and item["same_stratum_pi_ij_exact"] == (str(p["same_stratum_pair_pi"]) if p["same_stratum_pair_pi"] is not None else None) and close(item["same_stratum_pi_ij"], p["same_stratum_pair_pi"]))
            if item["domain"] == "remaining":
                prior_key = key.removeprefix("remaining|")
                check(name + " " + key + ": old600 N/n unchanged", item["prior_remaining_key"] == prior_key and item["N"] == old_map[prior_key]["N"] and item["n"] == item["fixed_remaining_n"] == old_map[prior_key]["n"])
            else:
                check(name + " " + key + ": fixed priority", item["priority_multiplier"] == PRIORITIES[item["tag"]])
        expected_pairs = {tuple(p) for p in combinations(sorted(mapping), 2)}
        reported_pairs = [(r["first_stratum"], r["second_stratum"]) for r in plan["cross_stratum_joint_second_order_probabilities"]]
        check(name + ": all 820 cross-stratum pairs exactly once", len(reported_pairs) == len(set(reported_pairs)) == 820 and set(reported_pairs) == expected_pairs)
        check(name + ": all cross-stratum probabilities exact products", all(r["pi_ij_exact"] == str(independent_probs[r["first_stratum"]]["pi"] * independent_probs[r["second_stratum"]]["pi"]) and close(r["pi_ij"], independent_probs[r["first_stratum"]]["pi"] * independent_probs[r["second_stratum"]]["pi"]) for r in plan["cross_stratum_joint_second_order_probabilities"]))
        domain_n = Counter()
        dept_n, dept_N = Counter(), Counter()
        domain_dept_n = {d: Counter() for d in ("remaining", "exposed")}
        for item in mapping.values():
            domain_n[item["domain"]] += item["n"]
            domain_dept_n[item["domain"]][item["department"]] += item["n"]
            dept_n[item["department"]] += item["n"]
            dept_N[item["department"]] += item["N"]
        check(name + ": domain and total budgets", domain_n == {"remaining": 600, "exposed": exp_n} and sum(dept_n.values()) == total_n and plan["assigned_n"] == total_n and plan["remaining_n"] == 600 and plan["exposed_n"] == exp_n)
        check(name + ": all department/domain headers", dict(dept_n) == plan["department_n"] and dict(dept_N) == plan["department_population_N"] == state["summary"]["department_N"] and {d: dict(v) for d, v in domain_dept_n.items()} == plan["domain_department_n"] and plan["domain_N"] == {"remaining": 1444, "exposed": 3037})
        weight_sum = sum(item["n"] * independent_probs[key]["weight"] for key, item in mapping.items())
        check(name + ": exact overall sample weight total 4481", weight_sum == 4481 and plan["weight_total_for_constant_one_exact"] == "4481")
        check(name + ": reported minimum pi and maximum weight", close(plan["minimum_unit_inclusion_probability"], min(p["pi"] for p in independent_probs.values())) and close(plan["maximum_weight"], max(p["weight"] for p in independent_probs.values())))
        expected_workload = {"two_independent_people_unit_readings": 2 * total_n,
                             "five_dimension_first_decision_entries_two_people": 10 * total_n,
                             "reference_unit_audits": total_n,
                             "machine_dimension_outputs_two_methods_one_fixed_run": 10 * total_n,
                             "additional_exposed_two_people_readings": 2 * exp_n,
                             "additional_exposed_first_decision_entries": 10 * exp_n}
        check(name + ": expected workload arithmetic", plan["workload"] == expected_workload)
        check(name + ": design not selected or drawn", all(plan[k] is False for k in ("actual_sample_drawn", "actual_sampling_seed_selected", "final_selected_plan")))
        # Compute the fixed quotient allocation independently with exact fractions.
        exposed = {k: v for k, v in mapping.items() if v["domain"] == "exposed"}
        built = {k: min(2, counts[k]) for k in exposed}
        trace = []
        while sum(built.values()) < exp_n:
            scores = {k: F(counts[k] * PRIORITIES[exposed[k]["tag"]], built[k] + 1) for k in built if built[k] < counts[k]}
            best = max(scores.values())
            winner = min(k for k, value in scores.items() if value == best)
            built[winner] += 1
            trace.append({"slot": sum(built.values()), "stratum": winner, "new_n": built[winner], "winning_quotient_exact": str(best)})
        check(name + ": independent quotient allocation and trace", built == {k: v["n"] for k, v in exposed.items()} and trace == plan["exposed_increment_allocation_trace"])
        plan_results[name] = {"N": 4481, "n": total_n, "domain_n": dict(domain_n), "department_n": dict(dept_n),
                              "domain_department_n": {d: dict(v) for d, v in domain_dept_n.items()}, "weight_total_exact": weight_sum,
                              "minimum_pi": min(p["pi"] for p in independent_probs.values()), "maximum_weight": max(p["weight"] for p in independent_probs.values()),
                              "census_strata": sum(v["census"] for v in independent_probs.values()), "singleton_census_strata": sum(v["N"] == 1 for v in mapping.values()),
                              "exposed_baseline_n": sum(min(2, counts[k]) for k in exposed), "cross_stratum_pairs_checked": len(reported_pairs), "workload": expected_workload}
    small, large = allocation["plans"]["full800"], allocation["plans"]["full1000"]
    check("budget allocation sequences share identical first 165 additions", large["exposed_increment_allocation_trace"][:len(small["exposed_increment_allocation_trace"])] == small["exposed_increment_allocation_trace"])
    check("400 exposed allocation is no smaller in any stratum", all(next(t["n"] for t in large["strata"] if t["key"] == s["key"]) >= s["n"] for s in small["strata"]))
    state["bindings"][str(path)] = digest(path)
    return {"status": "PASS_ALLOCATION_ARITHMETIC_AND_FRAME_ELIGIBILITY", "plans": plan_results,
            "caution": "allocation nesting does not select IDs or authorize sequential/adaptive sample expansion"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTDIR / "independent_full_domain_results.json")
    parser.add_argument("--allocation", type=Path)
    args = parser.parse_args()
    check("output constrained to independent-math directory", args.output.resolve().parent == OUTDIR)
    state = metadata_checks()
    allocation_result = allocation_checks(state, args.allocation.resolve()) if args.allocation else None
    result = {"status": "PASS_ALLOCATION_AND_EXACT_SYNTHETIC" if allocation_result else "PASS_METADATA_AND_EXACT_SYNTHETIC__ALLOCATION_PENDING", "date": "2026-10-10",
              "scope": "metadata whitelist and old fixed auxiliary labels; no real sample or new outcomes",
              "independent_of_main_engine": True, "read_bindings": state["bindings"],
              "script_sha256": digest(Path(__file__)), "frame_summary": state["summary"],
              "allocation_review": allocation_result,
              "inclusion_enumeration": exact_inclusion_checks(), "four_cell_enumeration": exact_four_cell_checks(),
              "checks": CHECKS}
    args.output.write_text(json.dumps(as_json(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(CHECKS), "all_passed": all(c["passed"] for c in CHECKS), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
