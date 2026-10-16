#!/usr/bin/env python3
"""Prospective D668 + V600 design-based analysis. No real labels are bundled.

The public ``analyze(payload)`` function has no file I/O and rejects departures
from the frozen 29-stratum design. CLI input is an explicitly supplied JSON
file; no corpus, coding files, or prediction files are discovered or loaded.
``_analyze_synthetic(payload)`` is only for synthetic software tests.

Schema d668-v1:
  data_kind: "observed_coding" (or "synthetic_test" for tests)
  design: {population_size, sample_size, department_sizes,
           strata: [{stratum_id, phase, department, N, n}, ...]}
  coders: ["A", "C"]
  dimensions: ["S", "E", "Ec", "I", "F"]
  units: [{unit_id, stratum_id,
           labels: {"A": {dimension: "0"|"1"|"pending", ...}, "C": ...}}, ...]

Formal coverage conditions: fixed coding functions on a fixed finite frame;
independent SRSWOR within each stratum; complete responses on sampled units.
AI codings may be dependent. No model-error or substantive-validity inference.
"""

from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import platform
from typing import Any, Mapping

import scipy
from scipy.stats import hypergeom


SCHEMA_VERSION = "d668-v1"
METHOD_VERSION = "D668-HT-exact-hypergeometric-bonferroni-v1"
ALPHA = 0.05
CODERS = ("A", "C")
DIMENSIONS = ("S", "E", "Ec", "I", "F")
DEPARTMENTS = ("NMPA", "NHSA", "NHC", "GOV")
STATUSES = ("0", "1", "pending")
POTENTIAL_POSITIVE = "positive_or_pending"
FAMILY_ENDPOINTS = ("1", POTENTIAL_POSITIVE)
FAMILY_SIZE = 580  # 2 coders * 5 dimensions * 29 strata * 2 endpoints.
FAMILY_PURPOSE = (
    "One fixed family of 580 binary stratum parameters covers both positive "
    "and positive-or-pending endpoints, all A/C coders and all five dimensions. "
    "Its simultaneous bounds imply all department bounds, 60 coder-specific "
    "positive differences, 60 worst-pending-completion differences and 30 "
    "cross-coder common-direction decisions. No independence between AI "
    "codings, dimensions, or endpoints is needed for the union bound."
)
TAIL_ABSOLUTE_TOLERANCE = 1e-14
FROZEN_DEPARTMENT_SIZES = {"NMPA": 1848, "NHSA": 2100, "NHC": 533, "GOV": 443}
_R_ROWS = (
    ("NMPA", 2020, 330, 129), ("NMPA", 2021, 58, 23),
    ("NMPA", 2023, 23, 9), ("NMPA", 2024, 35, 14),
    ("NMPA", 2025, 122, 48), ("NMPA", 2026, 203, 80),
    ("NHSA", 2019, 20, 8), ("NHSA", 2020, 62, 24),
    ("NHSA", 2021, 37, 15), ("NHSA", 2022, 39, 15),
    ("NHSA", 2023, 37, 15), ("NHSA", 2024, 38, 15),
    ("NHSA", 2025, 97, 38), ("NHSA", 2026, 108, 42),
    ("NHC", 2018, 47, 18), ("NHC", 2019, 6, 2),
    ("NHC", 2020, 38, 15), ("NHC", 2021, 31, 12),
    ("NHC", 2022, 5, 2), ("NHC", 2023, 70, 27),
    ("NHC", 2024, 7, 3), ("GOV", 2017, 28, 11),
    ("GOV", 2020, 29, 11), ("GOV", 2024, 34, 13),
    ("GOV", 2025, 27, 11),
)
_D_ROWS = (("NMPA", 1077, 133), ("NHSA", 1662, 222),
           ("NHC", 329, 148), ("GOV", 325, 165))

LIMITATIONS = (
    "Intervals quantify finite-population sampling error conditional on fixed "
    "coding functions and the stated sampling design, not AI stochastic error, "
    "shared AI bias, construct validity, or agreement with human truth.",
    "Legacy R and supplementary D are disjoint fixed frame partitions; the "
    "SRSWOR samples in all 29 strata must be design-independent. Coverage is "
    "conditional on the fixed realized frame and on valid probability sampling.",
    "Each marginal interval has at least 95% design coverage individually; "
    "these marginal intervals are not a simultaneous family and must not be "
    "used to claim rankings across departments or dimensions.",
    "The fixed 580-parameter simultaneous family is conservative, especially "
    "for rare events and small strata. Discrete inversion can overcover.",
    "Estimated design variance and SE are auxiliary; zero estimated variance "
    "at all-zero/all-one sample counts is not evidence of population certainty.",
    "Pending is retained as a distinct state. Worst-completion intervals allow "
    "every pending code to resolve to either 0 or 1 without choosing a consensus.",
    "A shared robust direction requires both AI-specific worst-completion "
    "simultaneous intervals to exclude zero in the same direction; otherwise "
    "the pair is not orderable by this rule. No complete ranking is forced.",
    "No year effects, normalized five-dimension shares, significance p-values, "
    "measurement validity tests, or pooled A/C sample-size inflation are made.",
    "Input validation checks IDs, strata and complete labels, but external "
    "auditing must verify ID-to-frame membership, randomization provenance, "
    "record linkage and faithful label transcription.",
)


def canonical_sha256(value: Any) -> str:
    """Deterministic hash of a JSON-compatible object, without file access."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def frozen_design() -> dict[str, Any]:
    """Return a fresh copy of the frozen metadata; never load real labels."""
    strata = [dict(stratum_id=f"R|{g}|{year}", phase="R", department=g, N=N, n=n)
              for g, year, N, n in _R_ROWS]
    strata += [dict(stratum_id=f"D|{g}", phase="D", department=g, N=N, n=n)
               for g, N, n in _D_ROWS]
    return dict(population_size=4924, sample_size=1268,
                department_sizes=dict(FROZEN_DEPARTMENT_SIZES), strata=strata)


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}; got {value!r}")
    return value


def _keys(value: Any, expected: set[str], name: str) -> None:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError(f"{name} must have exactly these keys: {sorted(expected)}")


def _nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{name} must be a nonempty string without outer whitespace")
    return value


@lru_cache(maxsize=65536, typed=True)
def hypergeom_total_interval(N: int, n: int, x: int,
                            alpha: float) -> tuple[int, int]:
    """Invert inclusive equal tails for integer finite-population total M.

    Keep M in [x, N-n+x] when P_M(X>=x) and P_M(X<=x) are both
    >= alpha/2. Monotone binary searches use sf(x-1) and cdf(x).
    A fixed 1e-14 absolute comparison tolerance only enlarges boundary sets.
    Census samples have the deterministic interval [x,x].
    """
    _integer(N, "N", 1)
    _integer(n, "n", 1)
    _integer(x, "x")
    if n > N or x > n:
        raise ValueError("Require 0 <= x <= n <= N")
    if not isinstance(alpha, (int, float)) or isinstance(alpha, bool) or not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between 0 and 1")
    if n == N:
        return x, x
    threshold = alpha / 2

    def included(probability: float) -> bool:
        if not math.isfinite(probability):
            raise ArithmeticError("Nonfinite hypergeometric tail probability")
        return probability + TAIL_ABSOLUTE_TOLERANCE >= threshold

    lo, hi = x, N - n + x
    while lo < hi:
        mid = (lo + hi) // 2
        if included(float(hypergeom.sf(x - 1, N, mid, n))):
            hi = mid
        else:
            lo = mid + 1
    lower = lo
    lo, hi = x, N - n + x
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if included(float(hypergeom.cdf(x, N, mid, n))):
            lo = mid
        else:
            hi = mid - 1
    if lower > lo:
        raise ArithmeticError("Empty hypergeometric confidence set")
    return lower, lo


def binary_stratum_summary(N: int, n: int, x: int) -> dict[str, float | int]:
    """HT total and unbiased SRSWOR variance estimate of the total."""
    _integer(N, "N", 1)
    _integer(n, "n", 1)
    _integer(x, "x")
    if n > N or x > n:
        raise ValueError("Require 0 <= x <= n <= N")
    if n < 2 and n < N:
        raise ValueError("A noncensus stratum must have n >= 2 for variance estimation")
    s2 = x * (n - x) / (n * (n - 1)) if n > 1 else 0.0
    variance = N * (N - n) * s2 / n if n < N else 0.0
    return dict(N=N, n=n, x=x, inclusion_probability=n / N,
                inverse_probability_weight=N / n, ht_total=N * x / n,
                sample_variance=s2, estimated_total_variance=variance)


def _interval(lower: int, upper: int, denominator: int,
              alpha: float, stratum_alpha: float, H: int,
              scope: str) -> dict[str, Any]:
    return dict(lower=lower / denominator, upper=upper / denominator,
                population_total_lower=lower, population_total_upper=upper,
                fixed_denominator=denominator, nominal_coverage=1 - alpha,
                alpha=alpha, per_stratum_alpha=stratum_alpha,
                stratum_count=H, scope=scope,
                method="sum of exact equal-tailed hypergeometric total bounds")


def aggregate_binary(strata_counts: list[tuple[int, int, int]],
                     denominator: int, alpha: float = ALPHA,
                     family_size: int | None = None) -> dict[str, Any]:
    """Pure building block. tuples=(N,n,x); strata must be disjoint."""
    _integer(denominator, "denominator", 1)
    if not strata_counts or sum(N for N, _, _ in strata_counts) != denominator:
        raise ValueError("Stratum populations must sum to the fixed denominator")
    H = len(strata_counts)
    if family_size is not None:
        _integer(family_size, "family_size", H)
    per_alpha = alpha / (family_size if family_size is not None else H)
    summaries = [binary_stratum_summary(N, n, x) for N, n, x in strata_counts]
    bounds = [hypergeom_total_interval(N, n, x, per_alpha) for N, n, x in strata_counts]
    total = math.fsum(s["ht_total"] for s in summaries)
    variance = math.fsum(s["estimated_total_variance"] for s in summaries) / denominator**2
    return dict(sample_size=sum(n for _, n, _ in strata_counts),
                sample_event_count=sum(x for _, _, x in strata_counts),
                ht_total=total, proportion=total / denominator,
                fixed_denominator=denominator,
                estimated_design_variance=variance,
                design_se_auxiliary=math.sqrt(variance),
                confidence_interval=_interval(
                    sum(a for a, _ in bounds), sum(b for _, b in bounds),
                    denominator, alpha, per_alpha, H,
                    "fixed_580_family_simultaneous" if family_size == FAMILY_SIZE
                    else ("synthetic_family_simultaneous" if family_size else "marginal")))


def _validate(payload: Mapping[str, Any], synthetic: bool) -> tuple[dict, list, tuple]:
    _keys(payload, {"schema_version", "data_kind", "design", "coders", "dimensions", "units"}, "payload")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    expected_kind = "synthetic_test" if synthetic else "observed_coding"
    if payload["data_kind"] != expected_kind:
        raise ValueError(f"data_kind must be {expected_kind}")
    if payload["coders"] != list(CODERS) or payload["dimensions"] != list(DIMENSIONS):
        raise ValueError("Coders and five dimensions must match the frozen ordered keys")
    design = payload["design"]
    _keys(design, {"population_size", "sample_size", "department_sizes", "strata"}, "design")
    _integer(design["population_size"], "population_size", 1)
    _integer(design["sample_size"], "sample_size", 1)
    sizes = design["department_sizes"]
    if not isinstance(sizes, Mapping) or not sizes:
        raise ValueError("department_sizes must be a nonempty mapping")
    for g, N in sizes.items():
        _nonempty_string(g, "department")
        _integer(N, f"department_sizes[{g}]", 1)
    raw_strata = design["strata"]
    if not isinstance(raw_strata, list) or not raw_strata:
        raise ValueError("strata must be a nonempty list")
    strata = {}
    department_N = Counter()
    for h in raw_strata:
        _keys(h, {"stratum_id", "phase", "department", "N", "n"}, "stratum")
        hid = _nonempty_string(h["stratum_id"], "stratum_id")
        if hid in strata:
            raise ValueError(f"Duplicate stratum_id: {hid}")
        if h["phase"] not in ("R", "D") or h["department"] not in sizes:
            raise ValueError(f"Invalid phase or department for {hid}")
        binary_stratum_summary(h["N"], h["n"], 0)
        strata[hid] = h
        department_N[h["department"]] += h["N"]
    if dict(department_N) != dict(sizes):
        raise ValueError("Per-department stratum N totals differ from department_sizes")
    if sum(sizes.values()) != design["population_size"]:
        raise ValueError("Department sizes differ from population_size")
    if sum(h["n"] for h in raw_strata) != design["sample_size"]:
        raise ValueError("Stratum n totals differ from sample_size")
    if not synthetic:
        expected = frozen_design()
        expected_strata = {h["stratum_id"]: h for h in expected["strata"]}
        if (strata != expected_strata or dict(sizes) != expected["department_sizes"]
                or design["population_size"] != 4924 or design["sample_size"] != 1268):
            raise ValueError("Design does not exactly match all 29 frozen R25+D4 strata")
    units = payload["units"]
    if not isinstance(units, list):
        raise ValueError("units must be a list")
    seen_ids = set()
    observed_n = Counter()
    for unit in units:
        _keys(unit, {"unit_id", "stratum_id", "labels"}, "unit")
        uid = _nonempty_string(unit["unit_id"], "unit_id")
        if uid in seen_ids:
            raise ValueError(f"Duplicate unit_id: {uid}; A/C are labels on the same unit")
        seen_ids.add(uid)
        hid = unit["stratum_id"]
        if hid not in strata:
            raise ValueError(f"Unknown stratum_id: {hid}")
        observed_n[hid] += 1
        _keys(unit["labels"], set(CODERS), f"labels for {uid}")
        for coder in CODERS:
            _keys(unit["labels"][coder], set(DIMENSIONS), f"{coder} labels for {uid}")
            for dimension, label in unit["labels"][coder].items():
                if not isinstance(label, str) or label not in STATUSES:
                    raise ValueError(f"Invalid/missing state for {uid}/{coder}/{dimension}: {label!r}")
    if len(units) != design["sample_size"]:
        raise ValueError("Unique unit count differs from sample_size; missing labels cannot be dropped")
    for hid, h in strata.items():
        if observed_n[hid] != h["n"]:
            raise ValueError(f"{hid}: observed {observed_n[hid]} units, required {h['n']}")
    departments = tuple(sorted(sizes)) if synthetic else DEPARTMENTS
    ordered_strata = [strata[k] for k in sorted(strata)]
    return design, ordered_strata, departments


def _difference(left: Mapping, right: Mapping) -> dict[str, Any]:
    """Subtract rational finite-population bounds; determine signs exactly."""
    ng, nh = left["fixed_denominator"], right["fixed_denominator"]
    lower_numerator = left["population_total_lower"] * nh - right["population_total_upper"] * ng
    upper_numerator = left["population_total_upper"] * nh - right["population_total_lower"] * ng
    denominator = ng * nh
    return dict(lower=lower_numerator / denominator, upper=upper_numerator / denominator,
                exact_lower_numerator=lower_numerator,
                exact_upper_numerator=upper_numerator, exact_denominator=denominator,
                excludes_zero=lower_numerator > 0 or upper_numerator < 0,
                direction="left_greater" if lower_numerator > 0 else (
                    "left_less" if upper_numerator < 0 else "not_orderable"),
                scope="fixed_580_family_simultaneous", nominal_coverage=1 - ALPHA)


def _analysis(payload: Mapping[str, Any], synthetic: bool) -> dict[str, Any]:
    design, strata, departments = _validate(payload, synthetic)
    counts = {(coder, dim, h["stratum_id"]): Counter({s: 0 for s in STATUSES})
              for coder in CODERS for dim in DIMENSIONS for h in strata}
    for unit in payload["units"]:
        for coder in CODERS:
            for dim in DIMENSIONS:
                counts[coder, dim, unit["stratum_id"]][unit["labels"][coder][dim]] += 1
    # Even a synthetic end-to-end run uses the full fixed 580 family. It does
    # not shrink the correction if an event is absent or a stratum is a census.
    if len(strata) > 29:
        raise ValueError("The fixed 580 family supports at most 29 strata in synthetic tests")
    tables = {"department_status_estimates": [], "department_potential_positive_estimates": [],
              "overall_status_estimates": [], "overall_potential_positive_estimates": []}
    family_department = {}
    stratum_results = []
    for coder in CODERS:
        for dim in DIMENSIONS:
            for h in strata:
                c = counts[coder, dim, h["stratum_id"]]
                bounds = {}
                for endpoint in FAMILY_ENDPOINTS:
                    x = c["1"] if endpoint == "1" else c["1"] + c["pending"]
                    lo, hi = hypergeom_total_interval(h["N"], h["n"], x, ALPHA / FAMILY_SIZE)
                    bounds[endpoint] = dict(sample_count=x, total_lower=lo, total_upper=hi,
                                            alpha=ALPHA / FAMILY_SIZE)
                stratum_results.append(dict(coder=coder, dimension=dim, **h,
                                            status_counts=dict(c), simultaneous_total_bounds=bounds))
            for g in (*departments, "__overall__"):
                group_strata = strata if g == "__overall__" else [h for h in strata if h["department"] == g]
                N_group = design["population_size"] if g == "__overall__" else design["department_sizes"][g]
                for measure in (*STATUSES, POTENTIAL_POSITIVE):
                    triples = []
                    for h in group_strata:
                        c = counts[coder, dim, h["stratum_id"]]
                        x = c["1"] + c["pending"] if measure == POTENTIAL_POSITIVE else c[measure]
                        triples.append((h["N"], h["n"], x))
                    estimate = aggregate_binary(triples, N_group)
                    row = dict(coder=coder, dimension=dim, measure=measure, **estimate)
                    if g != "__overall__":
                        row["department"] = g
                    if measure in FAMILY_ENDPOINTS:
                        bound = aggregate_binary(triples, N_group, family_size=FAMILY_SIZE)["confidence_interval"]
                        row["simultaneous_confidence_interval"] = bound
                        if g != "__overall__":
                            family_department[coder, dim, g, measure] = row
                    prefix = "overall" if g == "__overall__" else "department"
                    suffix = "potential_positive_estimates" if measure == POTENTIAL_POSITIVE else "status_estimates"
                    tables[f"{prefix}_{suffix}"].append(row)
    differences = []
    difference_lookup = {}
    for coder in CODERS:
        for dim in DIMENSIONS:
            for g, h in combinations(departments, 2):
                pg = family_department[coder, dim, g, "1"]
                ph = family_department[coder, dim, h, "1"]
                qg = family_department[coder, dim, g, POTENTIAL_POSITIVE]
                qh = family_department[coder, dim, h, POTENTIAL_POSITIVE]
                pg_ci, ph_ci = pg["simultaneous_confidence_interval"], ph["simultaneous_confidence_interval"]
                qg_ci, qh_ci = qg["simultaneous_confidence_interval"], qh["simultaneous_confidence_interval"]
                positive_ci = _difference(pg_ci, ph_ci)
                # Worst completion lower = L(pos_g)-U(pos+pending_h);
                # upper = U(pos+pending_g)-L(pos_h).
                completion_left = {**pg_ci, "population_total_upper": qg_ci["population_total_upper"]}
                completion_right = {**ph_ci, "population_total_upper": qh_ci["population_total_upper"]}
                completion_ci = _difference(completion_left, completion_right)
                row = dict(coder=coder, dimension=dim, left_department=g, right_department=h,
                           positive_difference_estimate=pg["proportion"] - ph["proportion"],
                           positive_difference_simultaneous_interval=positive_ci,
                           worst_pending_completion_simultaneous_interval=completion_ci)
                differences.append(row)
                difference_lookup[coder, dim, g, h] = row
    directions = []
    for dim in DIMENSIONS:
        for g, h in combinations(departments, 2):
            ai = {coder: difference_lookup[coder, dim, g, h]["worst_pending_completion_simultaneous_interval"]["direction"]
                  for coder in CODERS}
            common = ai["A"] if ai["A"] == ai["C"] and ai["A"] != "not_orderable" else "not_orderable"
            directions.append(dict(dimension=dim, left_department=g, right_department=h,
                                   coder_directions=ai, common_robust_direction=common,
                                   robust_to_design_error_and_pending=common != "not_orderable"))
    metadata = dict(
        schema_version=SCHEMA_VERSION, method_version=METHOD_VERSION,
        analysis_kind="SYNTHETIC_SOFTWARE_TEST_ONLY" if synthetic else "OBSERVED_CODING_DESIGN_ANALYSIS",
        alpha=ALPHA, family_size=FAMILY_SIZE, family_purpose=FAMILY_PURPOSE,
        family_per_parameter_alpha=ALPHA / FAMILY_SIZE,
        family_per_tail_alpha=ALPHA / (2 * FAMILY_SIZE),
        family_components={"coders": 2, "dimensions": 5, "frozen_strata": 29, "endpoints": 2},
        family_keeps_absent_events_and_census_strata=True,
        tail_comparison_absolute_tolerance=TAIL_ABSOLUTE_TOLERANCE,
        tail_comparison_rule="probability + 1e-14 >= alpha/2; conservative boundary inclusion only",
        contrast_zero_comparison="exact integer cross-products; no sign tolerance",
        marginal_department_strata={g: sum(h["department"] == g for h in strata) for g in departments},
        marginal_overall_strata=len(strata),
        point_estimator="HT total / fixed U department N; overall weighted by department N / total N",
        variance_estimator="sum_h N_h^2 (1-n_h/N_h) s_h^2/n_h divided by fixed denominator squared",
        primary_interval="equal-tailed hypergeometric inversion per stratum, Bonferroni allocation, sum total bounds",
        unique_sample_units=len(payload["units"]),
        ai_codings_per_unit=len(CODERS), ai_codings_are_not_independent_sample_units=True,
        ai_independence_required=False, strata_design_independence_required=True,
        complete_ranking_produced=False, p_values_produced=False,
        input_canonical_sha256=canonical_sha256(payload),
        design_canonical_sha256=canonical_sha256(design),
        python_version=platform.python_version(), scipy_version=scipy.__version__,
        output_row_counts={**{k: len(v) for k, v in tables.items()},
                           "coder_pairwise_differences": len(differences),
                           "common_robust_directions": len(directions),
                           "stratum_coder_dimension_counts": len(stratum_results)},
        assumptions_and_limitations=list(LIMITATIONS),
    )
    return dict(metadata=metadata, design=json.loads(json.dumps(design)),
                **tables, coder_pairwise_differences=differences,
                common_robust_directions=directions,
                stratum_coder_dimension_counts=stratum_results)


def analyze(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Analyze complete observed labels, enforcing the full frozen design."""
    return _analysis(payload, synthetic=False)


def _analyze_synthetic(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Testing-only entry point; output is unmistakably marked synthetic."""
    return _analysis(payload, synthetic=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Explicit complete observed-coding JSON")
    parser.add_argument("--output", type=Path, help="New output JSON path (existing files are refused)")
    parser.add_argument("--design-only", action="store_true", help="Print frozen metadata without reading labels")
    args = parser.parse_args()
    if args.design_only:
        if args.input or args.output:
            parser.error("--design-only cannot be combined with --input/--output")
        print(json.dumps(frozen_design(), ensure_ascii=False, indent=2))
        return
    if args.input is None or args.output is None:
        parser.error("Both --input and --output are required for observed analysis")
    if args.output.exists():
        parser.error("Refusing to overwrite an existing output")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze(payload)
    result["metadata"]["program_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["metadata"]["input_file_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(result, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write("\n")


if __name__ == "__main__":
    main()
