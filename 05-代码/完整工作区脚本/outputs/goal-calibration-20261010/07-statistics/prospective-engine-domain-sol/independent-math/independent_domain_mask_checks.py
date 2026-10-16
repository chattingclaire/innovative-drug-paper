#!/usr/bin/env python3
"""Independent domain-mask math: exact toys and conditional Rao-Wu enumeration.

Standard library only. No imports/executes of either statistics engine, no
project data reads, no actual IDs or labels. All units here are artificial
integer positions. All writes are to this new independent-math directory.
"""
from fractions import Fraction as F
from itertools import combinations, product
from collections import Counter
import json
import math
from pathlib import Path

OUTDIR = Path(__file__).resolve().parent
CHECKS = []


def check(name, passed, detail=None):
    CHECKS.append({"name": name, "passed": bool(passed), "detail": detail})
    if not passed:
        raise AssertionError(name)


def json_value(obj):
    if isinstance(obj, F):
        return {"exact": str(obj), "value": float(obj)}
    if isinstance(obj, dict):
        return {str(k): json_value(v) for k, v in obj.items()}
    if isinstance(obj, (tuple, list)):
        return [json_value(v) for v in obj]
    return obj


def zero_cov(size):
    return [[F(0) for _ in range(size)] for _ in range(size)]


def moments(vectors):
    n, size = len(vectors), len(vectors[0])
    mean = [sum(row[j] for row in vectors) / n for j in range(size)]
    cov = [[sum((row[i] - mean[i]) * (row[j] - mean[j]) for row in vectors) / n
            for j in range(size)] for i in range(size)]
    return mean, cov


def add_vectors(vectors):
    return [sum(v[j] for v in vectors) for j in range(len(vectors[0]))]


def add_covs(matrices):
    return [[sum(v[i][j] for v in matrices) for j in range(len(matrices[0]))]
            for i in range(len(matrices[0]))]


def masked_covariance(strata, vectors, sampled=False):
    size = len(next(iter(vectors.values()))[0])
    V = zero_cov(size)
    for name, h in strata.items():
        N, n = h["N"], h["n"]
        if N == n:
            continue
        values = vectors[name]
        denominator = n - 1 if sampled else N - 1
        mean = [sum(row[j] for row in values) / len(values) for j in range(size)]
        multiplier = F(N * (N - n), n)
        for i in range(size):
            for j in range(size):
                S = sum((row[i] - mean[i]) * (row[j] - mean[j]) for row in values) / denominator
                V[i][j] += multiplier * S
    return V


def metric_values(cells):
    a, b, c, d = map(F, cells)
    return {"Precision": a / (a + b), "Recall": a / (a + c),
            "F1": 2 * a / (2 * a + b + c),
            "kappa": 2 * (a * d - b * c) / ((a + b) * (b + d) + (a + c) * (c + d))}


def matches(h, selection):
    return all(h.get(field) == value for field, value in selection.items())


def census_flag(strata, selection):
    # Global census exhausts the finite frame, so observed population membership
    # is complete even when an old department declaration was absent.
    if all(h["n"] == h["N"] for h in strata.values()):
        return True
    if not selection:
        return False
    if any(not isinstance(h.get(field), str) or not h[field]
           for h in strata.values() for field in selection):
        return False
    members = [h for h in strata.values() if matches(h, selection)]
    return bool(members) and all(h["n"] == h["N"] for h in members)


def full_layer_domain_toy():
    strata = {
        "R_A": {"domain": "remaining", "department": "A", "N": 4, "n": 2, "categories": [0, 1, 2, 3]},
        "R_B": {"domain": "remaining", "department": "B", "N": 3, "n": 2, "categories": [0, 3, 3]},
        "E_A": {"domain": "exposed", "department": "A", "N": 3, "n": 3, "categories": [0, 0, 3]},
        "E_B": {"domain": "exposed", "department": "B", "N": 4, "n": 2, "categories": [0, 1, 3, 3]},
        "E_C": {"domain": "exposed", "department": "C", "N": 1, "n": 1, "categories": [3]},
    }
    selections = {
        "ALL": {}, "remaining": {"domain": "remaining"}, "exposed": {"domain": "exposed"},
        **{"department:" + d: {"department": d} for d in ("A", "B", "C")},
        **{"domain:" + domain + "|department:" + dept: {"domain": domain, "department": dept}
           for domain, dept in (("remaining", "A"), ("remaining", "B"), ("exposed", "A"), ("exposed", "B"), ("exposed", "C"))},
    }
    population_vectors = {name: [[F(int(i == cat)) for i in range(4)] for cat in h["categories"]]
                          for name, h in strata.items()}
    choices = [list(combinations(range(h["N"]), h["n"])) for h in strata.values()]
    design_vectors = {scope: [] for scope in selections}
    for joint in product(*choices):
        chosen = dict(zip(strata, joint))
        for scope, selection in selections.items():
            total = [F(0)] * 4
            for name, h in strata.items():
                if matches(h, selection):
                    w = F(h["N"], h["n"])
                    for position in chosen[name]:
                        total = [a + w * b for a, b in zip(total, population_vectors[name][position])]
            design_vectors[scope].append(total)
    exact_moments = {scope: moments(values) for scope, values in design_vectors.items()}
    for scope, selection in selections.items():
        masked_population = {name: values if matches(strata[name], selection) else [[F(0)] * 4 for _ in values]
                             for name, values in population_vectors.items()}
        true_total = add_vectors([add_vectors(values) for values in masked_population.values()])
        V = masked_covariance(strata, masked_population)
        mean, covariance = exact_moments[scope]
        check(scope + ": unbiased masked HT totals", mean == true_total)
        check(scope + ": exact masked FPC covariance", covariance == V)
        check(scope + ": fixed total sample weights", all(sum(v) == sum(h["N"] for h in strata.values() if matches(h, selection)) for v in design_vectors[scope]))
    groups = (("remaining", "exposed"), ("department:A", "department:B", "department:C"))
    for group in groups:
        check("every realized sample total is partition-additive " + "|".join(group),
              all(design_vectors["ALL"][k] == add_vectors([design_vectors[g][k] for g in group])
                  for k in range(len(design_vectors["ALL"]))))
        check("whole-layer partition covariance is additive " + "|".join(group),
              exact_moments["ALL"][1] == add_covs([exact_moments[g][1] for g in group]))
    joint_remaining = ("domain:remaining|department:A", "domain:remaining|department:B")
    joint_exposed = ("domain:exposed|department:A", "domain:exposed|department:B", "domain:exposed|department:C")
    for scope, group in (("remaining", joint_remaining), ("exposed", joint_exposed)):
        check(scope + ": joint-domain masks partition totals",
              all(design_vectors[scope][k] == add_vectors([design_vectors[g][k] for g in group]) for k in range(len(design_vectors[scope]))))
    # Verify cross-domain covariance directly, not by assuming disjoint units.
    for i in range(4):
        for j in range(4):
            cross = sum((a[i] - exact_moments["remaining"][0][i]) * (b[j] - exact_moments["exposed"][0][j])
                        for a, b in zip(design_vectors["remaining"], design_vectors["exposed"])) / len(design_vectors["ALL"])
            assert cross == 0
    check("remaining/exposed design cross-covariance zero", True)
    # The two masks overlap on R_A: Cov(R, department A) equals that layer's V.
    Rmean, Amean = exact_moments["remaining"][0], exact_moments["department:A"][0]
    cross = [[sum((a[i] - Rmean[i]) * (b[j] - Amean[j])
                  for a, b in zip(design_vectors["remaining"], design_vectors["department:A"])) / len(design_vectors["ALL"])
              for j in range(4)] for i in range(4)]
    check("overlapping domain/department masks retain shared-layer covariance",
          cross == exact_moments["domain:remaining|department:A"][1] and any(v for row in cross for v in row))
    expected_flags = {"ALL": False, "remaining": False, "exposed": False, "department:A": False, "department:B": False,
                      "department:C": True, "domain:remaining|department:A": False, "domain:remaining|department:B": False,
                      "domain:exposed|department:A": True, "domain:exposed|department:B": False, "domain:exposed|department:C": True}
    for scope, selection in selections.items():
        check(scope + ": frozen stratum census logic", census_flag(strata, selection) == expected_flags[scope])
    all_cells, rem_cells, exp_cells = (exact_moments[k][0] for k in ("ALL", "remaining", "exposed"))
    points = {k: metric_values(exact_moments[k][0]) for k in ("ALL", "remaining", "exposed")}
    incorrect_average = {m: F(7, 15) * points["remaining"][m] + F(8, 15) * points["exposed"][m] for m in points["ALL"]}
    check("pooled nonlinear metrics are not population-weighted domain metrics",
          all(points["ALL"][m] != incorrect_average[m] for m in points["ALL"]))
    # Fixed one artificial sample. Enumerate the full conditional RW law:
    # each n=2 noncensus layer has m=1, hence two possible rescaled draws.
    fixed_sample = {name: tuple(range(h["n"])) for name, h in strata.items()}
    sampled_units = [(name, position) for name in strata for position in fixed_sample[name]]
    resample_options = []
    for name, h in strata.items():
        n, N = h["n"], h["N"]
        if n == N:
            resample_options.append([(1.0,) * n])
        else:
            factors = []
            for draws in product(range(n), repeat=n - 1):
                k = Counter(draws)
                factors.append(tuple(1 + math.sqrt(1 - n / N) * (n * k[i] / (n - 1) - 1) for i in range(n)))
            resample_options.append(factors)
    W = []
    for factor_groups in product(*resample_options):
        W.append([strata[name]["N"] / strata[name]["n"] * factors[i]
                  for (name, factors) in zip(strata, factor_groups) for i in range(strata[name]["n"])])
    for scope, selection in selections.items():
        X = [population_vectors[name][position] if matches(strata[name], selection) else [F(0)] * 4
             for name, position in sampled_units]
        reps = [[sum(w * float(row[j]) for w, row in zip(weights, X)) for j in range(4)] for weights in W]
        mean, cov = moments(reps)
        sample_vectors = {name: [population_vectors[name][p] if matches(h, selection) else [F(0)] * 4
                                for p in fixed_sample[name]] for name, h in strata.items()}
        analytic = masked_covariance(strata, sample_vectors, sampled=True)
        check(scope + ": conditional common-W covariance equals sample FPC estimator",
              all(math.isclose(cov[i][j], float(analytic[i][j]), abs_tol=1e-12, rel_tol=1e-12) for i in range(4) for j in range(4)))
        check(scope + ": replicate total equals fixed population-domain N",
              all(math.isclose(sum(row), sum(h["N"] for h in strata.values() if matches(h, selection)), abs_tol=1e-12) for row in reps))
    # Common weights for 5 methods x 5 dimensions, retaining paired covariance.
    X25 = [[F(int((position + method * 2 + dimension + len(name)) % 5 < 2))
            for method in range(5) for dimension in range(5)] for name, position in sampled_units]
    reps25 = [[sum(w * float(row[j]) for w, row in zip(weights, X25)) for j in range(25)] for weights in W]
    _, covariance25 = moments(reps25)
    sampled25 = {name: [X25[i] for i, (hid, _) in enumerate(sampled_units) if hid == name] for name in strata}
    analytic25 = masked_covariance(strata, sampled25, sampled=True)
    check("common W across all 25 method/dimension outputs preserves full covariance",
          all(math.isclose(covariance25[i][j], float(analytic25[i][j]), abs_tol=1e-12, rel_tol=1e-12) for i in range(25) for j in range(25)))
    varying_column = next(j for j in range(25) if len({row[j] for row in reps25}) > 1)
    same_a = [row[varying_column] for row in reps25]
    same_b = list(same_a)
    deliberately_unpaired_b = same_b[1:] + same_b[:1]
    check("common W preserves identically paired total contrast variance zero", all(a == b for a, b in zip(same_a, same_b)))
    check("unpaired replicate rows destroy that paired contrast", any(a != b for a, b in zip(same_a, deliberately_unpaired_b)))
    check("singleton census replicate weights stay one", all(row[-1] == 1 for row in W))
    missing = {k: dict(v) for k, v in strata.items()}
    missing["E_B"]["department"] = None
    check("sample-observed department cannot prove frozen population membership", census_flag(missing, {"department": "C"}) is False)
    missing = {k: dict(v) for k, v in strata.items()}
    missing["R_A"]["domain"] = None
    check("partial domain freeze cannot certify a domain census", census_flag(missing, {"domain": "exposed", "department": "A"}) is False)
    census = {k: {**h, "n": h["N"], "department": None} for k, h in strata.items()}
    check("global census permits legacy observed department subset census", census_flag(census, {"department": "A"}) is True)
    return {"strata": strata, "design_samples_exhaustively_enumerated": len(design_vectors["ALL"]),
            "conditional_rescaled_bootstrap_outcomes_enumerated": len(W), "mask_count": len(selections),
            "true_cells": {"ALL": all_cells, "remaining": rem_cells, "exposed": exp_cells},
            "true_metric_points": points, "incorrect_N_weighted_domain_metric_points": incorrect_average,
            "census_flags": expected_flags}


def split_stratum_counterexample():
    # Legacy design may have mixed departments within a stratum. Fixed masks
    # must stay in the full n-vector; disjoint unit masks do not imply Cov=0.
    vectors = []
    for chosen in combinations(range(4), 2):
        A = F(2) * sum(i < 2 for i in chosen)
        B = F(2) * sum(i >= 2 for i in chosen)
        vectors.append([A, B])
    mean, cov = moments(vectors)
    check("mixed-stratum departments have negative cross covariance", mean == [2, 2] and cov == [[F(4, 3), F(-4, 3)], [F(-4, 3), F(4, 3)]])
    check("mixed-stratum ALL variance requires both cross terms", cov[0][0] + cov[1][1] + 2 * cov[0][1] == 0 and cov[0][0] + cov[1][1] > 0)
    # A fixed sample contains one unit of each department: zero-padded columns
    # have sample covariance -1/2 and the shared source-design estimator is -2.
    strata = {"mixed": {"N": 4, "n": 2}}
    sample_values = {"mixed": [[F(1), F(0)], [F(0), F(1)]]}
    conditional = masked_covariance(strata, sample_values, sampled=True)
    check("zero-padded mask retains original source n and FPC covariance",
          conditional == [[2, -2], [-2, 2]])
    check("masked-zero rows keep full covariance singular with ALL constant", all(sum(row) == 0 for row in conditional))
    return {"artificial_population_N": 4, "source_sample_n": 2, "population_department_N": [2, 2],
            "samples_enumerated": len(vectors), "true_department_covariance": cov,
            "fixed_sample_zero_padded_covariance_estimator": conditional,
            "incorrect_sum_of_department_variances": cov[0][0] + cov[1][1]}


def main():
    full = full_layer_domain_toy()
    split = split_stratum_counterexample()
    result = {"status": "PASS_INDEPENDENT_DOMAIN_MASK_MATH", "date": "2026-10-10",
              "project_input_reads": 0, "statistics_engines_imported_or_executed": False,
              "full_layer_partition_toy": full, "legacy_mixed_department_counterexample": split,
              "check_count": len(CHECKS), "all_passed": all(c["passed"] for c in CHECKS), "checks": CHECKS}
    path = OUTDIR / "independent_domain_mask_results.json"
    path.write_text(json.dumps(json_value(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(CHECKS), "output": str(path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
