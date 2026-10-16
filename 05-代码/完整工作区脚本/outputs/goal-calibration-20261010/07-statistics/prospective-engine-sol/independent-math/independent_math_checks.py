#!/usr/bin/env python3
"""Independent, deterministic, synthetic math checks; no mother-engine imports.

This module reads no task data and calls no annotator, rule system, or LLM.
All ranges below denote artificial population positions, never real sample IDs.
Only standard-library modules are used. Run in this directory:
    python3 independent_math_checks.py
The default JSON is written beside this source.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path


TOL = 1e-10


def validate_stratum(N: int, n: int) -> None:
    if isinstance(N, bool) or isinstance(n, bool) or not isinstance(N, int) or not isinstance(n, int):
        raise ValueError("N and n must be integers")
    if not 1 <= n <= N:
        raise ValueError("Require 1 <= n <= N")
    if n == 1 and n < N:
        raise ValueError("Non-census singleton is invalid for this bootstrap")


def rw_factors(N: int, n: int, counts: tuple[int, ...] | None = None) -> tuple[float, ...]:
    """m=n-1, SRSWR multiplicities; census handled before any n-1 division."""
    validate_stratum(N, n)
    if n == N:
        return (1.0,) * n
    m = n - 1
    if counts is None or len(counts) != n or sum(counts) != m:
        raise ValueError("Multiplicity vector must have length n and sum n-1")
    if any(isinstance(k, bool) or not isinstance(k, int) or k < 0 for k in counts):
        raise ValueError("Multiplicities must be nonnegative integers")
    root_fpc = math.sqrt(1.0 - n / N)
    return tuple(1.0 + root_fpc * (n * k / m - 1.0) for k in counts)


def all_rw_replicates(N: int, n: int):
    """Every ordered resampling outcome, each with its exact probability."""
    validate_stratum(N, n)
    if N == n:
        yield (1.0,) * n, Fraction(1)
        return
    m = n - 1
    probability = Fraction(1, n**m)
    for sequence in itertools.product(range(n), repeat=m):
        counts = tuple(sequence.count(i) for i in range(n))
        yield rw_factors(N, n, counts), probability


def mean(values):
    return math.fsum(values) / len(values)


def sample_cov(x, y):
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Sample covariance requires paired n>=2")
    mx, my = mean(x), mean(y)
    return math.fsum((a - mx) * (b - my) for a, b in zip(x, y)) / (len(x) - 1)


def weighted_mean_cov(vectors, probabilities):
    d = len(vectors[0])
    mu = [math.fsum(float(p) * v[j] for p, v in zip(probabilities, vectors)) for j in range(d)]
    cov = [[math.fsum(float(p) * (v[j] - mu[j]) * (v[k] - mu[k])
                       for p, v in zip(probabilities, vectors)) for k in range(d)] for j in range(d)]
    return mu, cov


def max_matrix_error(a, b):
    return max(abs(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def assert_close(a, b, tolerance=TOL):
    assert abs(a - b) <= tolerance * max(1.0, abs(a), abs(b)), (a, b)


def compositions(total: int, cells: int):
    if cells == 1:
        yield (total,)
    else:
        for first in range(total + 1):
            for remainder in compositions(total - first, cells - 1):
                yield (first,) + remainder


def choose(N: int, n: int) -> int:
    return math.comb(N, n) if 0 <= n <= N else 0


def hypergeom_pmf(N: int, K: int, n: int, x: int) -> Fraction:
    if not 0 <= K <= N or not 0 <= n <= N:
        raise ValueError("Invalid hypergeometric parameters")
    return Fraction(choose(K, x) * choose(N - K, n - x), choose(N, n))


def p_zero(N: int, n: int, K: int) -> Fraction:
    return hypergeom_pmf(N, K, n, 0)


def zero_upper(N: int, n: int, alpha=Fraction(1, 20)) -> int:
    """For a fixed category and x=0; retain equality for conservatism.

    A complete zero-only upper-bound procedure returns N when x>0.
    This is an auxiliary upper bound, not a replacement bootstrap CI.
    """
    if not 0 < alpha < 1 or not 1 <= n <= N:
        raise ValueError("Invalid zero-guard arguments")
    return max(K for K in range(N + 1) if p_zero(N, n, K) >= alpha)


def stratified_zero_envelope(strata):
    """Exact DP: worst miss probability over integer allocations of total K."""
    envelope = {0: Fraction(1)}
    witnesses = {0: ()}
    for N, n in strata:
        if not 1 <= n <= N:
            raise ValueError("Invalid SRSWOR stratum")
        updated, updated_witnesses = {}, {}
        for previous_K, previous_p in envelope.items():
            for K_h in range(N - n + 1):
                K = previous_K + K_h
                candidate = previous_p * p_zero(N, n, K_h)
                if K not in updated or candidate > updated[K]:
                    updated[K] = candidate
                    updated_witnesses[K] = witnesses[previous_K] + (K_h,)
        envelope, witnesses = updated, updated_witnesses
    return envelope, witnesses


def joint_zero_only_coverage(N, n, population_cells, per_cell_alpha):
    """Exact four-cell coverage of zero-only marginal bounds by inclusion-exclusion."""
    if len(population_cells) != 4 or sum(population_cells) != N:
        raise ValueError("Four mutually exclusive cells must sum to N")
    u = zero_upper(N, n, per_cell_alpha)
    bad = [j for j, K in enumerate(population_cells) if K > u]
    failure = Fraction(0)
    for size in range(1, len(bad) + 1):
        for subset in itertools.combinations(bad, size):
            union_K = sum(population_cells[j] for j in subset)
            failure += (-1) ** (size + 1) * p_zero(N, n, union_K)
    return 1 - failure


def multivariate_hypergeom_pmf(population_cells, sample_cells):
    N, n = sum(population_cells), sum(sample_cells)
    numerator = math.prod(choose(K, x) for K, x in zip(population_cells, sample_cells))
    return Fraction(numerator, choose(N, n))


def exact_discrete_quantile(values, probabilities, q):
    """Inf{x:F(x)>=q}; deliberately no unstated interpolation."""
    distribution = {}
    for value, probability in zip(values, probabilities):
        distribution[value] = distribution.get(value, Fraction(0)) + probability
    running = Fraction(0)
    for value in sorted(distribution):
        running += distribution[value]
        if running >= q:
            return value
    raise AssertionError("Probability mass must sum to one")


def check_factors():
    details = []
    for n in range(2, 6):
        for N in (n + 1, 2 * n + 3):
            outcomes = list(all_rw_replicates(N, n))
            vectors, probs = zip(*outcomes)
            mu, cov = weighted_mean_cov(vectors, probs)
            expected = [[(1 - n / N) if j == k else -(1 - n / N) / (n - 1)
                         for k in range(n)] for j in range(n)]
            for v in vectors:
                assert_close(sum(v), n)
                assert min(v) > 0
            for value in mu:
                assert_close(value, 1)
            error = max_matrix_error(cov, expected)
            assert error < TOL
            details.append({"N": N, "n": n, "ordered_outcomes": len(outcomes),
                            "max_factor_covariance_error": error,
                            "minimum_factor": min(map(min, vectors))})
    return details


def check_linear_conditional_variance():
    N, values = 7, (1.0, 3.0, 8.0, 12.0)
    n = len(values)
    outcomes = list(all_rw_replicates(N, n))
    totals = [(N / n) * math.fsum(a * y for a, y in zip(factors, values))
              for factors, _ in outcomes]
    mu, cov = weighted_mean_cov([(x,) for x in totals], [p for _, p in outcomes])
    analytic = N * N * (1 - n / N) * sample_cov(values, values) / n
    assert_close(mu[0], N * mean(values))
    assert_close(cov[0][0], analytic)
    no_fpc = N * N * sample_cov(values, values) / n
    return {"N": N, "n": n, "conditional_bootstrap_variance": cov[0][0],
            "analytic_fpc_variance": analytic,
            "unscaled_with_replacement_variance": no_fpc,
            "no_fpc_over_fpc_ratio": no_fpc / analytic}


def check_common_five_label_weights():
    # Columns: synthetic A, B, adjudication, rule, LLM. No project labels are read.
    strata = [
        (4, ((0, 0, 0, 0, 1), (1, 0, 1, 1, 1))),
        (6, ((0, 1, 0, 0, 0), (1, 1, 1, 0, 1), (1, 0, 0, 1, 0))),
        (1, ((1, 1, 1, 1, 1),)),
    ]
    N_total = sum(N for N, _ in strata)
    outcome_sets = [list(all_rw_replicates(N, len(rows))) for N, rows in strata]
    vectors, probabilities = [], []
    for joint in itertools.product(*outcome_sets):
        totals = [0.0] * 5
        p = math.prod(outcome[1] for outcome in joint)
        for (N, rows), (factors, _) in zip(strata, joint):
            weights = tuple(N / len(rows) * a for a in factors)
            assert_close(sum(weights), N)
            for j in range(5):
                totals[j] += math.fsum(w * row[j] for w, row in zip(weights, rows))
        vectors.append(tuple(total / N_total for total in totals))
        probabilities.append(p)
    mu, cov = weighted_mean_cov(vectors, probabilities)
    analytic = [[0.0] * 5 for _ in range(5)]
    for N, rows in strata:
        n = len(rows)
        if N == n:
            continue
        for j in range(5):
            for k in range(5):
                analytic[j][k] += (N / N_total) ** 2 * (1 - n / N) / n * sample_cov(
                    [row[j] for row in rows], [row[k] for row in rows])
    error = max_matrix_error(cov, analytic)
    assert error < TOL
    # Paired contrast rule minus adjudication requires the covariance term.
    paired_var = cov[3][3] + cov[2][2] - 2 * cov[3][2]
    independently_resampled_var = cov[3][3] + cov[2][2]
    assert abs(paired_var - independently_resampled_var) > 1e-6
    return {"synthetic_columns": ["A", "B", "adjudication", "rule", "LLM"],
            "ordered_joint_outcomes": len(vectors), "N_total": N_total,
            "maximum_covariance_error": error, "means": mu,
            "common_weight_covariance": cov,
            "rule_minus_adjudication_variance": paired_var,
            "wrong_independent_weight_variance": independently_resampled_var}


def check_design_unbiased_variance():
    populations = [(0.0, 1.0, 1.0, 4.0), (-2.0, 0.0, 3.0, 5.0, 5.0), (7.0,)]
    n_values = (2, 3, 1)
    sample_sets = [list(itertools.combinations(population, n))
                   for population, n in zip(populations, n_values)]
    totals, conditional_variances = [], []
    for sample in itertools.product(*sample_sets):
        estimate = sum(len(pop) * mean(values) for pop, values in zip(populations, sample))
        totals.append(estimate)
        replicates = [list(all_rw_replicates(len(pop), len(values)))
                      for pop, values in zip(populations, sample)]
        boot_values, probs = [], []
        for joint in itertools.product(*replicates):
            total = sum(len(pop) / len(values) * math.fsum(a * y for a, y in zip(factors, values))
                        for pop, values, (factors, _) in zip(populations, sample, joint))
            boot_values.append((total,))
            probs.append(math.prod(p for _, p in joint))
        _, boot_cov = weighted_mean_cov(boot_values, probs)
        conditional_variances.append(boot_cov[0][0])
    true_total = sum(map(sum, populations))
    design_variance = mean([(t - true_total) ** 2 for t in totals])
    theoretical = sum(len(pop) ** 2 * (1 - n / len(pop)) / n * sample_cov(pop, pop)
                      for pop, n in zip(populations, n_values) if n < len(pop))
    assert_close(mean(totals), true_total)
    assert_close(design_variance, theoretical)
    assert_close(mean(conditional_variances), design_variance)
    return {"original_design_samples": len(totals), "true_population_total": true_total,
            "mean_HT_total": mean(totals), "exact_design_variance": design_variance,
            "analytic_population_variance": theoretical,
            "average_conditional_bootstrap_variance": mean(conditional_variances),
            "conditional_variance_range": [min(conditional_variances), max(conditional_variances)]}


def check_census_and_illegal_singleton():
    assert rw_factors(1, 1) == (1.0,)
    assert rw_factors(4, 4) == (1.0,) * 4
    rejected = []
    for N, n in ((2, 1), (10, 1), (2, 0), (2, 3)):
        try:
            validate_stratum(N, n)
        except ValueError:
            rejected.append([N, n])
        else:
            raise AssertionError("Invalid stratum accepted")
    return {"singleton_census_factor": 1, "census_variance": 0,
            "illegal_pairs_rejected": rejected}


def check_single_zero_guards():
    max_failure = Fraction(0)
    checked = 0
    for N in range(2, 17):
        for n in range(1, N + 1):
            upper = zero_upper(N, n)
            assert upper <= N - n
            for K in range(N + 1):
                assert sum((hypergeom_pmf(N, K, n, x) for x in range(n + 1)), Fraction(0)) == 1
                if K > upper:
                    max_failure = max(max_failure, p_zero(N, n, K))
                    assert p_zero(N, n, K) < Fraction(1, 20)
                checked += 1
    assert zero_upper(5, 5) == 0
    strata = ((8, 3), (5, 2), (1, 1))
    envelope, witnesses = stratified_zero_envelope(strata)
    brute = {}
    for allocation in itertools.product(*(range(N - n + 1) for N, n in strata)):
        K = sum(allocation)
        p = math.prod(p_zero(N, n, k) for (N, n), k in zip(strata, allocation))
        brute[K] = max(brute.get(K, Fraction(0)), p)
    assert envelope == brute
    upper = max(K for K, p in envelope.items() if p >= Fraction(1, 20))
    return {"single_category_parameter_combinations": checked,
            "maximum_false_zero_only_upper_bound_probability": float(max_failure),
            "single_N20_n5_upper95": zero_upper(20, 5),
            "census_zero_upper": zero_upper(5, 5),
            "stratified_example": {"strata_N_n": strata, "upper95_total_count": upper,
                "envelope": {str(K): {"miss_probability": str(p), "allocation": witnesses[K]}
                             for K, p in envelope.items()}}}


def check_joint_four_cell_guards():
    N, n, population = 16, 8, (4, 4, 4, 4)
    alpha = Fraction(1, 20)
    marginal_upper = zero_upper(N, n, alpha)
    bonferroni_upper = zero_upper(N, n, alpha / 4)
    unadjusted = joint_zero_only_coverage(N, n, population, alpha)
    adjusted = joint_zero_only_coverage(N, n, population, alpha / 4)
    # Independent check via full multivariate sample-table enumeration.
    table_mass = Fraction(0)
    table_coverage = Fraction(0)
    feasible_tables = 0
    for sample in compositions(n, 4):
        p = multivariate_hypergeom_pmf(population, sample)
        if p:
            feasible_tables += 1
        table_mass += p
        if all(x > 0 or K <= marginal_upper for K, x in zip(population, sample)):
            table_coverage += p
    assert table_mass == 1 and table_coverage == unadjusted
    assert unadjusted < 1 - alpha
    minima = []
    for N, n in ((12, 6), (16, 8)):
        min_raw, min_bonf = Fraction(1), Fraction(1)
        raw_witness, bonf_witness = None, None
        count = 0
        for population in compositions(N, 4):
            count += 1
            raw = joint_zero_only_coverage(N, n, population, alpha)
            bonf = joint_zero_only_coverage(N, n, population, alpha / 4)
            if raw < min_raw:
                min_raw, raw_witness = raw, population
            if bonf < min_bonf:
                min_bonf, bonf_witness = bonf, population
            assert bonf >= 1 - alpha
        minima.append({"N": N, "n": n, "population_tables_exhausted": count,
                       "minimum_unadjusted_joint_coverage": float(min_raw),
                       "unadjusted_witness": raw_witness,
                       "minimum_Bonferroni_joint_coverage": float(min_bonf),
                       "Bonferroni_witness": bonf_witness})
    return {"counterexample": {"N": 16, "n": 8, "true_four_cells": [4, 4, 4, 4],
                "zero_upper_at_alpha_0_05": marginal_upper,
                "each_marginal_coverage": float(1 - p_zero(16, 8, 4)),
                "joint_coverage_of_four_unadjusted_bounds": float(unadjusted),
                "joint_coverage_exact_fraction": str(unadjusted),
                "zero_upper_at_alpha_0_0125": bonferroni_upper,
                "Bonferroni_joint_coverage": float(adjusted),
                "feasible_sample_tables_enumerated": feasible_tables},
            "small_population_exhaustions": minima}


def check_sparse_percentile_limitation():
    N, n, population = 10, 3, (1,) + (0,) * 9
    true_proportion = Fraction(1, 10)
    covered = 0
    all_zero_samples = 0
    sample_count = 0
    zero_interval = None
    for sample in itertools.combinations(population, n):
        sample_count += 1
        outcomes = list(all_rw_replicates(N, n))
        values = [math.fsum(a * y for a, y in zip(factors, sample)) / n
                  for factors, _ in outcomes]
        probabilities = [p for _, p in outcomes]
        low = exact_discrete_quantile(values, probabilities, Fraction(1, 40))
        high = exact_discrete_quantile(values, probabilities, Fraction(39, 40))
        covered += low <= float(true_proportion) <= high
        if sum(sample) == 0:
            all_zero_samples += 1
            zero_interval = [low, high]
    coverage = Fraction(covered, sample_count)
    assert coverage == Fraction(3, 10)
    assert zero_interval == [0.0, 0.0]
    assert Fraction(all_zero_samples, sample_count) == p_zero(N, n, 1)
    return {"N": N, "n": n, "true_category_count": 1,
            "true_category_proportion": float(true_proportion),
            "all_original_SRSWOR_samples": sample_count,
            "exact_percentile_95_design_coverage": float(coverage),
            "all_zero_sample_probability": float(p_zero(N, n, 1)),
            "percentile_interval_when_sample_all_zero": zero_interval,
            "interpretation": "Counterexample to exact finite-sample percentile coverage, not a project result."}


def main():
    checks = {
        "factor_moments_and_mass": check_factors(),
        "linear_conditional_FPC": check_linear_conditional_variance(),
        "common_five_label_weights": check_common_five_label_weights(),
        "design_unbiasedness_full_enumeration": check_design_unbiased_variance(),
        "census_singleton_validation": check_census_and_illegal_singleton(),
        "single_category_hypergeometric_zero_guard": check_single_zero_guards(),
        "joint_four_cell_hypergeometric_zero_guard": check_joint_four_cell_guards(),
        "sparse_percentile_counterexample": check_sparse_percentile_limitation(),
    }
    source = Path(__file__).resolve()
    result = {
        "status": "PASS",
        "scope": "Independent synthetic exact enumeration only; no prospective mother engine executed.",
        "reads_real_data": False,
        "uses_or_draws_real_sample_IDs": False,
        "calls_rule_or_LLM": False,
        "imports_mother_engine": False,
        "monte_carlo_used": False,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "tolerance": TOL,
        "checks": checks,
    }
    output = source.with_name("independent_math_results.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(output),
                      "check_groups": len(checks), "source_sha256": result["source_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
