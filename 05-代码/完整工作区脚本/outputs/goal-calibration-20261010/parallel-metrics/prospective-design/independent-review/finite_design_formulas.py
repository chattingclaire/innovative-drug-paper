"""Aggregate-only prospective design helpers. No ID sampling or source-text reads.

The supplied N/T/n/cell counts are finite-population scenario counts, not observed
human labels. scipy is used only for deterministic distribution calculations.
"""

import math
import numpy as np
from scipy.stats import hypergeom


def positive_count_tail(Ns, Ts, ns, minimum):
    """Exact P(sum X_h >= minimum), X_h ~ Hypergeom(N_h,T_h,n_h)."""
    distribution = np.array([1.0])
    for N, T, n in zip(Ns, Ts, ns, strict=True):
        if not (0 <= T <= N and 0 <= n <= N):
            raise ValueError("Invalid finite-population counts")
        x = np.arange(n + 1)
        distribution = np.convolve(distribution, hypergeom.pmf(x, N, T, n))
    return float(distribution[max(0, minimum):].sum())


def hypergeom_total_interval(N, n, x, alpha=0.05, two_sided=True):
    """Conservative discrete inversion interval for a binary total T in [0,N].

    Each T is retained if its applicable tail probabilities are >= alpha/2
    (two-sided), or if P_T(X <= x) >= alpha (upper one-sided).
    """
    if not (0 <= x <= n <= N and 0 < alpha < 1):
        raise ValueError("Invalid N, n, x, alpha")
    candidates = np.arange(x, N - n + x + 1)
    cutoff = alpha / 2 if two_sided else alpha
    keep = hypergeom.cdf(x, N, candidates, n) >= cutoff
    if two_sided:
        keep &= hypergeom.sf(x - 1, N, candidates, n) >= cutoff
    values = candidates[keep]
    if not len(values):
        raise ArithmeticError("Empty confidence set")
    return int(values[0]), int(values[-1])


def pooled_zero_error_upper(Ns, ns, alpha=0.05):
    """Exact composite upper total when every stratum has zero observed errors.

    Invert max_{sum E_h=E} product P_{E_h}(X_h=0). The log-probability
    increments are decreasing within each stratum, so a largest-next-increment
    merge maximizes each total-E probability. This is one error category only;
    it is not a joint confidence region for all cells or all metrics.
    """
    if not (0 < alpha < 1):
        raise ValueError("Invalid alpha")
    if any(not 0 <= n <= N for N, n in zip(Ns, ns, strict=True)):
        raise ValueError("Invalid N,n")
    errors = [0] * len(Ns)
    logp = 0.0
    upper = 0
    cutoff = math.log(alpha)
    while True:
        increments = [
            (N - n - e) / (N - e) if e < N - n else 0.0
            for N, n, e in zip(Ns, ns, errors, strict=True)
        ]
        h = max(range(len(increments)), key=increments.__getitem__)
        factor = increments[h]
        if factor == 0:
            return upper
        logp += math.log(factor)
        errors[h] += 1
        if logp < cutoff:
            return upper
        upper += 1


def same_reference_truth_total_range(machine_positive_totals, threshold=0.8):
    """Necessary shared-T range if every machine has both P,R >= threshold."""
    low = max(math.ceil(threshold * M - 1e-12) for M in machine_positive_totals)
    high = min(math.floor(M / threshold + 1e-12) for M in machine_positive_totals)
    return {"lower": low, "upper": high, "feasible_necessary_condition": low <= high}


def two_machine_joint(N, T, M1, M2, A1, A2, positive_overlap, negative_overlap):
    """Joint 8-cell [truth,M1,M2] scenario, checked against integer Frechet bounds.

    A_m is TP_m; positive_overlap is TP shared by both machines;
    negative_overlap is FP shared by both machines.
    """
    if not all(isinstance(x, int) for x in [N,T,M1,M2,A1,A2,positive_overlap,negative_overlap]):
        raise ValueError("Scenario cells must be integer counts")
    F1, F2 = M1 - A1, M2 - A2
    if not (0 <= T <= N and 0 <= A1 <= min(T,M1) and 0 <= A2 <= min(T,M2)
            and 0 <= F1 <= N-T and 0 <= F2 <= N-T):
        raise ValueError("Infeasible marginal machine tables")
    if not max(0,A1+A2-T) <= positive_overlap <= min(A1,A2):
        raise ValueError("Infeasible conditional true-positive overlap")
    if not max(0,F1+F2-(N-T)) <= negative_overlap <= min(F1,F2):
        raise ValueError("Infeasible conditional false-positive overlap")
    result = {
        "1,1,1": positive_overlap,
        "1,1,0": A1-positive_overlap,
        "1,0,1": A2-positive_overlap,
        "1,0,0": T-A1-A2+positive_overlap,
        "0,1,1": negative_overlap,
        "0,1,0": F1-negative_overlap,
        "0,0,1": F2-negative_overlap,
        "0,0,0": N-T-F1-F2+negative_overlap,
    }
    assert min(result.values()) >= 0 and sum(result.values()) == N
    return result


def fixed_machine_pair_threshold_feasibility(N, M1, M2, J, threshold=0.8, kappa_threshold=None):
    """Integer aggregate feasibility on one common reference; no pseudo ID labels.

    Uses known prediction-positive intersection J, and optionally adds Cohen
    kappa >= kappa_threshold. F1 >= threshold follows from P,R >= threshold.
    """
    shared = same_reference_truth_total_range([M1,M2],threshold)
    totals = []
    witness = None
    for T in range(max(1,shared['lower']), min(N,shared['upper'])+1):
        lows = []
        for M in [M1,M2]:
            low = max(math.ceil(threshold*M-1e-12),math.ceil(threshold*T-1e-12))
            if kappa_threshold is not None:
                low = max(low,math.ceil(kappa_threshold*(M+T)/2 +
                          (1-kappa_threshold)*M*T/N - 1e-12))
            lows.append(low)
        found = False
        for A1 in range(lows[0],min(M1,T)+1):
            for A2 in range(lows[1],min(M2,T)+1):
                F1,F2=M1-A1,M2-A2
                L1,U1=max(0,A1+A2-T),min(A1,A2)
                L0,U0=max(0,F1+F2-(N-T)),min(F1,F2)
                lo,hi=max(L1,J-U0),min(U1,J-L0)
                if lo <= hi:
                    if witness is None:
                        witness={'T':T,'TP1':A1,'TP2':A2,
                                 'joint_TP':lo,'joint_FP':J-lo}
                    found=True
                    break
            if found:
                break
        if found:
            totals.append(T)
    return {'feasible':bool(totals),'feasible_T_count':len(totals),
            'minimum_feasible_T':min(totals) if totals else None,
            'maximum_feasible_T':max(totals) if totals else None,
            'aggregate_witness_only':witness}


def anticipated_cell_total_covariance(Ns, ns, cells):
    """Exact design covariance of HT four-cell totals in an integer scenario."""
    covariance = np.zeros((4, 4), dtype=float)
    for N, n, counts in zip(Ns, ns, cells, strict=True):
        if sum(counts) != N or any(x < 0 for x in counts) or not 0 < n <= N:
            raise ValueError("Invalid stratum cells or allocation")
        if n == N:
            continue
        p = np.asarray(counts, dtype=float) / N
        S = N / (N - 1) * (np.diag(p) - np.outer(p, p))
        covariance += N * N * (1 - n/N) / n * S
    return covariance


def ratio_linearized_variance(Ns, ns, residual_population_variances, denominator_total):
    """Delta variance for Y/X: residual is y_i - (Y/X)*x_i, S_h^2 uses N_h-1."""
    if denominator_total <= 0:
        return math.nan
    return sum(N*N*(1-n/N)*S2/n for N,n,S2 in
               zip(Ns,ns,residual_population_variances,strict=True)) / denominator_total**2


def candidate_aggregate_review():
    # These are parent-reported auxiliary-only counts; no hidden labels or IDs.
    negative_N = [536, 348, 91]
    candidates = {}
    for nhc_census in [False,True]:
      rows=[]
      for fraction in [0.50, 0.85, 0.95, 1.0]:
        ns = [math.ceil(fraction*N) for N in negative_N]
        if nhc_census:
            ns[-1]=negative_N[-1]
        rows.append({
            "negative_fraction": fraction,
            "negative_n_by_department_NMPA_NHSA_NHC": ns,
            "total_n_with_469_auxiliary_positive_census": 469 + sum(ns),
            "pooled_zero_category_upper_one_sided_95": pooled_zero_error_upper(negative_N,ns,0.05),
            "pooled_zero_category_upper_upper_tail_of_two_sided_95": pooled_zero_error_upper(negative_N,ns,0.025),
            "sum_stratum_zero_upper_bonferroni_one_sided_95": sum(
                hypergeom_total_interval(N,n,0,alpha=0.05/3,two_sided=False)[1]
                for N,n in zip(negative_N,ns,strict=True)),
        })
      candidates['NHC_census' if nhc_census else 'all_departments_same_fraction']=rows
    prediction_pairs={'S':(140,184,133),'E':(81,110,73),'Ec':(144,162,139),
                      'I':(22,40,12),'F':(55,78,39)}
    return {
        "candidate_assumption": "census all 469 units positive on any of five dimensions in either frozen auxiliary machine; SRSWOR independently in each department all-auxiliary-negative cell; use ceil(f*N); main parent comparison also censes NHC negatives",
        "candidate_tables": candidates,
        "baseline_old_I_22_40_shared_truth": same_reference_truth_total_range([22,40]),
        "baseline_old_F_55_78_shared_truth": same_reference_truth_total_range([55,78]),
        "baseline_old_pair_aggregate_feasibility_P_R_F1_kappa_each_ge_0_8":{
            dim:fixed_machine_pair_threshold_feasibility(1444,*parameters,
                                                       kappa_threshold=0.8)
            for dim,parameters in prediction_pairs.items()},
    }


if __name__ == "__main__":
    import json
    print(json.dumps(candidate_aggregate_review(), ensure_ascii=False, indent=2))
