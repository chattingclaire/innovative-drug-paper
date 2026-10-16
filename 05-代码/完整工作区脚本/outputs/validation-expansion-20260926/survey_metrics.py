"""Design-weighted H600 diagnostics; never infer or manufacture reference labels.

Public API: analyze(payload) -> JSON-serializable dict. CLI:
    python survey_metrics.py --input explicit.json --output new-result.json
The CLI refuses to overwrite an existing result. Importing this module reads no data.

Payload schema (all five dimensions S/E/Ec/I/F are required in each label map):
    {
      "strata": [{"stratum": "NMPA/2021", "N_h": 80, "n_h": 12}, ...],
      "rows": [{"id": "opaque-id", "stratum": "NMPA/2021",
                "N_h": 80, "n_h": 12,
                "A": {"S": 0, "E": 1, "Ec": "待定", "I": 0, "F": 1},
                "C": {...}, "reference": {...}, "dictionary": {...}}, ...],
      "reference_info": {"kind": "AI", "description": "explicit provenance"},
      "dictionary_info": {"description": "explicit frozen prediction version"},
      "population_N": 3781
    }
reference, dictionary and population_N are optional. If a label column is present,
it must be present on every row; missing judgements use the explicit string 待定.
reference_info is mandatory if reference exists (kind AI/human/other), and
dictionary_info is mandatory if dictionary exists. Neither A/C agreement nor
majority voting is ever converted into reference. Without BOTH reference and
dictionary, no classifier-vs-reference results are produced.

The strata manifest is required: each declared stratum must have exactly n_h rows,
repeated N_h/n_h must agree, IDs must be unique, 1<=n_h<=N_h, and noncensus n_h>=2.
The manifest cannot prove that the supplied frame covers all of U*: the caller is
responsible for the frozen department/year mapping, frame and inclusion design.
This tool supports stratified SRS WITHOUT replacement of individual units only,
not clustered, two-stage, unequal-probability-within-stratum or purposive samples.

Base weight is N_h/n_h. Exactly 2000 replicates use seed 2026092603, NumPy PCG64,
with canonical stratum/ID sorting and whole-row resampling across all dimensions.
For noncensus stratum h draw m~Multinomial(n_h-1, 1/n_h) and multiply base weights
by 1+sqrt(1-n_h/N_h)*(n_h*m/(n_h-1)-1). Census factors are identically one.
Algebra: each factor vector sums to n_h; conditional variance of the replicate
stratum mean is (1-f_h)*s_h^2/n_h, exactly the SRSWOR variance estimator.
This establishes the linear variance match, NOT exact coverage for nonlinear
kappa/PRF or rare denominators. Percentile intervals are approximate 95% marginal
(per-metric, per-dimension), never simultaneous five-dimension intervals.

Pending rows stay in coverage and full-sample bounds. Binary ratios/kappa condition
on BOTH definite labels. Completion bounds are sharp for the supplied weighted
sample under arbitrary binary completion of pending cells, conditional on supplied
definite labels; they are NOT confidence intervals, reference truth, or imputation.
PRF bounds range over completions on which the metric is defined. Separate flags
identify whether undefined completions are possible; if ALL completions leave a
metric undefined both bounds are None. No full-sample kappa completion bound is
claimed. Bootstrap CIs for bound endpoints concern the endpoints, not simultaneous
coverage of the partially identified set.

>10% undefined replicates suppresses the interval and labels it unstable. Positive
rescaled weights mean an observed rare class cannot disappear entirely unless its
original support was absent: a low undefined fraction is NOT evidence of adequate
rare-class precision. Sampling intervals do not capture shared coder errors,
unknown text exposure, reference bias, or unsampled classes. Census design variance
is zero but coding and reference error may remain.
"""

from __future__ import annotations

import itertools
import hashlib
import json
import math
from pathlib import Path

import numpy as np

DIMS = ("S", "E", "Ec", "I", "F")
PENDING = "待定"
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 2026092603
UNDEFINED_LIMIT = 0.10


def _positive_int(x, name):
    if type(x) is not int or x < 1:
        raise ValueError(f"{name} must be a positive Python/JSON integer")
    return x


def _label(x):
    if type(x) is int and x in (0, 1):
        return x
    if type(x) is str and x == PENDING:
        return 2
    raise ValueError(f"Expected literal 0/1/{PENDING}; got {x!r}")


def prepare(payload):
    """Validate the explicit frame and labels; return sorted in-memory arrays."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    manifest, rows = payload.get("strata"), payload.get("rows")
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("Nonempty strata manifest required")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Nonempty rows required")
    strata = {}
    for h in manifest:
        if not isinstance(h, dict):
            raise ValueError("Each stratum must be an object")
        key = h.get("stratum")
        if not isinstance(key, str) or not key or key in strata:
            raise ValueError("Stratum keys must be unique nonempty strings")
        N = _positive_int(h.get("N_h"), "N_h")
        n = _positive_int(h.get("n_h"), "n_h")
        if n > N or (n < N and n < 2):
            raise ValueError("Require n_h<=N_h and noncensus n_h>=2")
        strata[key] = (N, n)
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each row must be an object")
        key = row.get("id")
        if not isinstance(key, str) or not key or key in ids:
            raise ValueError("Row IDs must be unique nonempty strings")
        ids.add(key)
        h = row.get("stratum")
        if h not in strata:
            raise ValueError("Row stratum absent from manifest")
        N = _positive_int(row.get("N_h"), "row N_h")
        n = _positive_int(row.get("n_h"), "row n_h")
        if (N, n) != strata[h]:
            raise ValueError("Repeated N_h/n_h disagree with manifest")
    for h, (_, n) in strata.items():
        if sum(row["stratum"] == h for row in rows) != n:
            raise ValueError(f"Actual stratum row count differs from n_h: {h}")
    columns = ["A", "C"]
    for col in ("reference", "dictionary"):
        presence = [col in row for row in rows]
        if any(presence) and not all(presence):
            raise ValueError(f"Partial column {col}; use explicit pending labels")
        if all(presence):
            columns.append(col)
            info = payload.get(f"{col}_info")
            if not isinstance(info, dict) or not isinstance(info.get("description"), str) or not info["description"].strip():
                raise ValueError(f"Explicit {col}_info.description required")
            if col == "reference" and info.get("kind") not in ("AI", "human", "other"):
                raise ValueError("reference_info.kind must be AI/human/other")
    rows = sorted(rows, key=lambda row: (row["stratum"], row["id"]))
    labels = {}
    for col in columns:
        values = []
        for row in rows:
            codes = row.get(col)
            if not isinstance(codes, dict) or set(codes) != set(DIMS):
                raise ValueError(f"{col} must contain exactly the five dimensions")
            values.append([_label(codes[d]) for d in DIMS])
        labels[col] = np.asarray(values, dtype=np.int8)
    population = sum(N for N, _ in strata.values())
    if "population_N" in payload:
        if _positive_int(payload["population_N"], "population_N") != population:
            raise ValueError("population_N differs from the strata manifest")
    groups = []
    weights = np.empty(len(rows), dtype=float)
    for h, (N, n) in sorted(strata.items()):
        idx = np.asarray([i for i, row in enumerate(rows) if row["stratum"] == h])
        groups.append((h, N, n, idx))
        weights[idx] = N / n
    return {"rows": rows, "labels": labels, "groups": groups,
            "weights": weights, "N": population, "n": len(rows),
            "all_census": all(N == n for _, N, n, _ in groups)}


def replicate_weights(prepared):
    """Fixed registered Rao-Wu-style FPC rescaled weights, shape (2000,n)."""
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    out = np.empty((BOOTSTRAP_REPS, prepared["n"]), dtype=float)
    for _, N, n, idx in prepared["groups"]:
        if n == N:
            out[:, idx] = 1.0
            continue
        multiplicities = rng.multinomial(n - 1, np.full(n, 1.0 / n), size=BOOTSTRAP_REPS)
        factors = 1 + math.sqrt(1 - n / N) * (n * multiplicities / (n - 1) - 1)
        out[:, idx] = (N / n) * factors
        if not np.allclose(out[:, idx].sum(axis=1), N, rtol=1e-12, atol=1e-10):
            raise ArithmeticError("Replicate stratum weight total changed")
    if not np.all(np.isfinite(out)) or np.any(out <= 0):
        raise ArithmeticError("Unexpected nonpositive/nonfinite replicate weight")
    return out


def _ratio(num, den):
    return float(num / den) if den > 0 else None


def completion_bounds(table):
    """Sharp weighted PRF/accuracy completion bounds; rows=prediction, cols=ref."""
    tn, fn, y = table[0]
    fp, tp, x = table[1]
    v, z, q = table[2]
    unknown = x + y + z + v + q
    total = float(table.sum())
    possible_tp = tp + x + z + q
    p_low = _ratio(tp, tp + fp + x + v + q)
    if p_low is None and z > 0:
        p_low = 1.0
    p_high = _ratio(possible_tp, possible_tp + fp)
    if p_high is None and v > 0:
        p_high = 0.0
    r_low = _ratio(tp, tp + fn + y + z + q)
    if r_low is None and x > 0:
        r_low = 1.0
    r_high = _ratio(possible_tp, possible_tp + fn)
    if r_high is None and y > 0:
        r_high = 0.0
    f_low = _ratio(2 * tp, 2 * tp + fp + fn + unknown)
    f_high = _ratio(2 * possible_tp, 2 * possible_tp + fp + fn)
    if f_high is None and y + v > 0:
        f_high = 0.0
    return {
        "precision_lower": p_low, "precision_upper": p_high,
        "recall_lower": r_low, "recall_upper": r_high,
        "f1_lower": f_low, "f1_upper": f_high,
        "accuracy_lower": (tp + tn) / total,
        "accuracy_upper": (tp + tn + unknown) / total,
        "precision_can_be_undefined": bool(tp + fp + x == 0),
        "recall_can_be_undefined": bool(tp + fn + z == 0),
        "f1_can_be_undefined": bool(tp + fp + fn + x + z == 0),
    }


def metrics_from_table(table, classification=False):
    """Numerical point metrics plus completion-status flags from a 3x3 table."""
    table = np.asarray(table, dtype=float)
    if table.shape != (3, 3) or not np.isfinite(table).all() or (table < 0).any() or table.sum() <= 0:
        raise ValueError("Nonnegative finite nonempty 3x3 table required")
    N = float(table.sum())
    c00, c01, c10, c11 = (float(table[0, 0]), float(table[0, 1]),
                         float(table[1, 0]), float(table[1, 1]))
    definite = c00 + c01 + c10 + c11
    ldef, rdef = float(table[:2, :].sum()), float(table[:, :2].sum())
    po = _ratio(c00 + c11, definite)
    pa, pb = _ratio(c10 + c11, definite), _ratio(c01 + c11, definite)
    pe = None if pa is None else pa * pb + (1 - pa) * (1 - pb)
    kap = None if pe is None or 1 - pe <= 1e-14 else (po - pe) / (1 - pe)
    bounds = completion_bounds(table)
    inverted = table[np.ix_([1, 0, 2], [1, 0, 2])]
    neg_bounds = completion_bounds(inverted)
    values = {
        "population_weight_total": N,
        **{f"binary_total_{i}{j}": float(table[i, j]) for i in (0, 1) for j in (0, 1)},
        "both_definite_total": definite,
        "left_definite_total": ldef, "right_definite_total": rdef,
        "coverage_both_definite": definite / N,
        "coverage_left": ldef / N, "coverage_right": rdef / N,
        "pending_left_total": float(table[2, :].sum()),
        "pending_right_total": float(table[:, 2].sum()),
        "pending_both_total": float(table[2, 2]),
        "pending_exactly_one_total": float(table[2, :2].sum() + table[:2, 2].sum()),
        "agreement_definite": po, "kappa_definite": kap,
        "positive_agreement_definite": _ratio(2 * c11, 2 * c11 + c01 + c10),
        "negative_agreement_definite": _ratio(2 * c00, 2 * c00 + c01 + c10),
        "positive_rate_left_on_both_definite": pa,
        "positive_rate_right_on_both_definite": pb,
        "positive_rate_left_on_left_definite": _ratio(float(table[1, :].sum()), ldef),
        "positive_rate_right_on_right_definite": _ratio(float(table[:, 1].sum()), rdef),
        "agreement_all_lower": bounds["accuracy_lower"],
        "agreement_all_upper": bounds["accuracy_upper"],
        "positive_agreement_all_lower": bounds["f1_lower"],
        "positive_agreement_all_upper": bounds["f1_upper"],
        "negative_agreement_all_lower": neg_bounds["f1_lower"],
        "negative_agreement_all_upper": neg_bounds["f1_upper"],
    }
    flags = {
        "kappa_undefined_reason": "no_both_definite" if definite == 0 else
            ("degenerate_expected_agreement" if kap is None else None),
        "positive_agreement_completion_can_be_undefined": bounds["f1_can_be_undefined"],
        "negative_agreement_completion_can_be_undefined": neg_bounds["f1_can_be_undefined"],
    }
    if classification:
        values.update({"TP": c11, "FP": c10, "FN": c01, "TN": c00,
            "precision_definite": _ratio(c11, c11 + c10),
            "recall_definite": _ratio(c11, c11 + c01),
            "f1_definite": _ratio(2 * c11, 2 * c11 + c10 + c01),
            "specificity_definite": _ratio(c00, c00 + c10),
            "accuracy_definite": po,
            "reference_positive_lower": float(table[:, 1].sum()) / N,
            "reference_positive_upper": float(table[:, 1:].sum()) / N})
        values.update({f"{k[:-6]}_all_lower" if k.endswith("_lower") else f"{k[:-6]}_all_upper": v
                       for k, v in bounds.items() if k.endswith(("_lower", "_upper"))})
        flags.update({k: v for k, v in bounds.items() if k.endswith("_can_be_undefined")})
    return values, flags


def interval_summary(point, draws, all_census=False):
    """Suppress intervals if >10% replicates undefined; no favorable filtering."""
    arr = np.asarray([np.nan if x is None else x for x in draws], dtype=float)
    ok = np.isfinite(arr)
    missing = int((~ok).sum())
    fraction = missing / len(arr)
    answer = {"estimate": point, "lower": None, "upper": None,
              "defined_replicates": int(ok.sum()), "undefined_replicates": missing,
              "undefined_fraction": fraction, "replicate_se": None,
              "confidence_level": 0.95, "simultaneous": False}
    if fraction > UNDEFINED_LIMIT:
        answer["status"] = "unstable_more_than_10_percent_undefined"
    elif point is None or not math.isfinite(point):
        answer["status"] = "point_undefined"
    elif all_census:
        answer.update(lower=float(point), upper=float(point), replicate_se=0.0,
                      status="census_design_variance_zero")
    else:
        lo, hi = np.quantile(arr[ok], [0.025, 0.975], method="linear")
        answer.update(lower=float(lo), upper=float(hi),
                      replicate_se=float(np.std(arr[ok], ddof=1)) if ok.sum() > 1 else None,
                      status="approximate_percentile_conditional_on_defined" if missing else "approximate_percentile")
    return answer


def linear_design_variance(prepared, y):
    """SRSWOR design variance estimator of full-population weighted mean of y."""
    y = np.asarray(y, dtype=float)
    if y.shape != (prepared["n"],) or not np.isfinite(y).all():
        raise ValueError("y must be finite and match sampled rows")
    variance = 0.0
    for _, N, n, idx in prepared["groups"]:
        if n < N:
            variance += (N / prepared["N"]) ** 2 * (1 - n / N) * float(np.var(y[idx], ddof=1)) / n
    return variance


def _linear_masks(left, right, classification):
    both = (left < 2) & (right < 2)
    same = both & (left == right)
    unknown = ~both
    masks = {
        "coverage_both_definite": both, "coverage_left": left < 2,
        "coverage_right": right < 2,
        "agreement_all_lower": same, "agreement_all_upper": same | unknown,
    }
    if classification:
        masks.update({"accuracy_all_lower": same, "accuracy_all_upper": same | unknown,
                      "reference_positive_lower": right == 1,
                      "reference_positive_upper": right != 0})
    return masks


def analyze(payload):
    """Return diagnostics and registered replicate intervals; reads/writes no files."""
    p = prepare(payload)
    rw = replicate_weights(p)
    comparisons = [("A_vs_C", "A", "C", False)]
    if "dictionary" in p["labels"] and "reference" in p["labels"]:
        comparisons.append(("dictionary_vs_reference", "dictionary", "reference", True))
    result = {
        "method": "stratified_SRSWOR_FPC_rescaled_bootstrap",
        "status": "statistical_tool_output_not_validation_pass",
        "sample_n": p["n"], "population_N_from_manifest": p["N"],
        "sample_size_matches_H600_plan": p["n"] == min(600, p["N"]),
        "all_census": p["all_census"],
        "strata": [{"stratum": h, "N_h": N, "n_h": n, "weight": N / n,
                    "sampling_fraction": n / N} for h, N, n, _ in p["groups"]],
        "bootstrap": {"replicates": BOOTSTRAP_REPS, "seed": BOOTSTRAP_SEED,
                      "generator": "numpy.random.PCG64", "numpy_version": np.__version__,
                      "interval": "percentile_2.5_97.5", "simultaneous": False,
                      "undefined_fraction_limit_strictly_greater_than": UNDEFINED_LIMIT},
        "reference_info": payload.get("reference_info") if "reference" in p["labels"] else None,
        "dictionary_info": payload.get("dictionary_info") if "dictionary" in p["labels"] else None,
        "classification_status": "supplied_dictionary_vs_supplied_reference" if len(comparisons) == 2 else "not_evaluated_without_both_explicit_columns",
        "reference_generated": False,
        "scope": "Supplied finite frame only; excludes coding error, shared AI bias, unknown exposure and external generalization.",
        "bounds_interpretation": "Sharp binary-completion bounds of weighted sample; not confidence intervals or completed labels. PRF excludes undefined completions and reports their possibility.",
        "limitations": [
            "Requires true within-stratum SRSWOR; cannot verify selection from labels or manifest.",
            "Percentile CI coverage is approximate for nonlinear metrics and can be poor with sparse cells.",
            "An undefined fraction <=10% does not establish rare-class adequacy.",
            "All-definite ratios describe the assessable subset; coverage and completion bounds retain pending units.",
            "No full-sample kappa completion bounds or five-dimension simultaneous coverage are claimed.",
            "A supplied AI reference is not a human gold standard. Census removes sampling variance only.",
        ],
        "comparisons": {},
    }
    for name, lcol, rcol, classification in comparisons:
        result["comparisons"][name] = {"left": lcol, "right": rcol, "dimensions": {}}
        for j, dim in enumerate(DIMS):
            left, right = p["labels"][lcol][:, j], p["labels"][rcol][:, j]
            one_hot = np.eye(9)[3 * left + right]
            raw = one_hot.sum(axis=0).reshape(3, 3).astype(int)
            table = (p["weights"] @ one_hot).reshape(3, 3)
            replicate_tables = (rw @ one_hot).reshape(BOOTSTRAP_REPS, 3, 3)
            point, flags = metrics_from_table(table, classification)
            draw_metrics = [metrics_from_table(t, classification)[0] for t in replicate_tables]
            cis = {k: interval_summary(v, [m[k] for m in draw_metrics], p["all_census"])
                   for k, v in point.items()}
            linear_se = {k: math.sqrt(linear_design_variance(p, mask.astype(float)))
                         for k, mask in _linear_masks(left, right, classification).items()}
            result["comparisons"][name]["dimensions"][dim] = {
                "table_axis_order": [0, 1, PENDING],
                "raw_3x3_counts": raw.tolist(),
                "weighted_3x3_estimated_totals": table.tolist(),
                "estimates": point, "completion_and_undefined_flags": flags,
                "marginal_95_intervals": cis,
                "analytic_SRSWOR_standard_errors_for_linear_proportions": linear_se,
            }
    return result


def _synthetic_payload(specs, references=False):
    """QA helper: specs are (stratum,N,list of (left,right) synthetic labels)."""
    rows, strata = [], []
    for h, N, pairs in specs:
        n = len(pairs)
        strata.append({"stratum": h, "N_h": N, "n_h": n})
        for i, (a, c) in enumerate(pairs):
            A, C = ({d: a for d in DIMS}, {d: c for d in DIMS})
            row = {"id": f"{h}-{i:05d}", "stratum": h, "N_h": N, "n_h": n, "A": A, "C": C}
            if references:
                row.update(dictionary=A.copy(), reference=C.copy())
            rows.append(row)
    answer = {"strata": strata, "rows": rows}
    if references:
        answer.update(reference_info={"kind": "other", "description": "synthetic QA reference only"},
                      dictionary_info={"description": "synthetic QA predictions only"})
    return answer


def _check_completion_bounds(pairs, weights):
    table = np.zeros((3, 3))
    for (a, b), w in zip(pairs, weights):
        table[a, b] += w
    expected = completion_bounds(table)
    possible = [[(a if a < 2 else x, b if b < 2 else y)
                 for x in (range(2) if a == 2 else [a])
                 for y in (range(2) if b == 2 else [b])] for a, b in pairs]
    attained = {k: [] for k in ("precision", "recall", "f1", "accuracy")}
    undefined = {k: False for k in attained}
    for completion in itertools.product(*possible):
        t = np.zeros((3, 3))
        for (a, b), w in zip(completion, weights):
            t[a, b] += w
        v, _ = metrics_from_table(t, True)
        for k in attained:
            x = v[k + "_definite"]
            if x is None:
                undefined[k] = True
            else:
                attained[k].append(x)
    for k, values in attained.items():
        lo, hi = expected[k + "_lower"], expected[k + "_upper"]
        if values:
            assert math.isclose(lo, min(values), abs_tol=1e-12), (pairs, k, lo, min(values))
            assert math.isclose(hi, max(values), abs_tol=1e-12), (pairs, k, hi, max(values))
        else:
            assert lo is None and hi is None
        if k != "accuracy":
            assert expected[k + "_can_be_undefined"] == undefined[k]


def self_test():
    """Only synthetic data; return QA evidence without reading or writing files."""
    checks = {}
    t = np.array([[50., 10., 0.], [20., 20., 0.], [0., 0., 0.]])
    m, _ = metrics_from_table(t, True)
    assert math.isclose(m["kappa_definite"], (.7 - .54) / (1 - .54))
    assert math.isclose(m["positive_agreement_definite"], 40 / 70)
    assert math.isclose(m["negative_agreement_definite"], 100 / 130)
    assert m["precision_definite"] == .5 and math.isclose(m["recall_definite"], 2 / 3)
    checks["known_weighted_four_cell_formulas"] = "passed"
    unequal = analyze(_synthetic_payload([
        ("small", 8, [(0, 0), (1, 1)]),
        ("large", 90, [(0, 1), (1, 0), (0, 0)])], True))
    u = unequal["comparisons"]["dictionary_vs_reference"]["dimensions"]["S"]
    assert u["weighted_3x3_estimated_totals"] == [[34., 30., 0.], [30., 4., 0.], [0., 0., 0.]]
    assert math.isclose(u["estimates"]["agreement_definite"], 38 / 98)
    assert not math.isclose(u["estimates"]["agreement_definite"], 3 / 5)
    checks["end_to_end_unequal_stratum_weights"] = "passed"
    pair_types = list(itertools.product(range(3), repeat=2))
    bound_cases = 0
    for a in pair_types:
        _check_completion_bounds([a], [2.5]); bound_cases += 1
        for b in pair_types:
            _check_completion_bounds([a, b], [1.0, 3.0]); bound_cases += 1
    _check_completion_bounds(pair_types, [1., 2., 3., 4., 1., 2., 3., 4., 2.]); bound_cases += 1
    checks["sharp_bounds_exhaustive_binary_completions"] = {"status": "passed", "tables": bound_cases}
    pending = _synthetic_payload([("all9", 9, [(a if a < 2 else PENDING, b if b < 2 else PENDING) for a, b in pair_types])], True)
    result = analyze(pending)
    s = result["comparisons"]["A_vs_C"]["dimensions"]["S"]
    assert s["estimates"]["coverage_both_definite"] == 4 / 9
    assert s["estimates"]["pending_both_total"] == 1
    assert s["estimates"]["agreement_all_lower"] == 2 / 9
    assert s["estimates"]["agreement_all_upper"] == 7 / 9
    assert all(ci["replicate_se"] is None or ci["replicate_se"] == 0 for ci in s["marginal_95_intervals"].values())
    checks["census_and_pending_coverage"] = "passed"
    zero = analyze(_synthetic_payload([("zero", 50, [(0, 0)] * 10)], True))
    z = zero["comparisons"]["dictionary_vs_reference"]["dimensions"]["S"]
    for key in ("kappa_definite", "precision_definite", "recall_definite", "f1_definite"):
        assert z["estimates"][key] is None
        assert z["marginal_95_intervals"][key]["undefined_fraction"] == 1
        assert z["marginal_95_intervals"][key]["lower"] is None
    checks["degenerate_zero_support_not_fabricated"] = "passed"
    rare = analyze(_synthetic_payload([("rare", 100, [(0, 0)] * 19 + [(0, 1)])], True))
    r = rare["comparisons"]["dictionary_vs_reference"]["dimensions"]["S"]
    assert r["estimates"]["precision_definite"] is None
    assert r["estimates"]["recall_definite"] == 0 and r["estimates"]["f1_definite"] == 0
    checks["rare_reference_positive_and_no_predicted_positive"] = "passed"
    p = prepare(_synthetic_payload([("a", 100, [(1, 1)] * 3 + [(0, 0)] * 7),
                                    ("b", 200, [(1, 1)] * 12 + [(0, 0)] * 8)]))
    rw = replicate_weights(p)
    assert np.array_equal(rw, replicate_weights(p))
    for _, N, _, idx in p["groups"]:
        assert np.allclose(rw[:, idx].sum(axis=1), N, atol=1e-10)
    y = p["labels"]["A"][:, 0].astype(float)
    weighted_mean = float(p["weights"] @ y / p["N"])
    assert math.isclose(weighted_mean, float(y.mean())) and weighted_mean == .5
    predicted_variance = linear_design_variance(p, y)
    empirical_variance = float(np.var(rw @ y / p["N"], ddof=1))
    ratio = empirical_variance / predicted_variance
    # 2000 replicates give approx sqrt(2/1999)=3.2% relative MC standard error.
    # A 15% tolerance accommodates nonnormal finite-support replicate distributions.
    assert .85 <= ratio <= 1.15, ratio
    checks["FPC_rescaled_linear_variance_Monte_Carlo"] = {
        "status": "passed", "reps": BOOTSTRAP_REPS,
        "analytic_variance": predicted_variance, "replicate_variance": empirical_variance,
        "ratio": ratio, "accepted_ratio_interval": [.85, 1.15],
        "interpretation": "Monte Carlo validation of linear variance only; not proof of nonlinear CI coverage"}
    checks["self_weighting_mean_stratum_calibration_fixed_seed"] = "passed"
    bad = []
    valid = _synthetic_payload([("h", 10, [(0, 0), (1, 1)])])
    def clone(): return json.loads(json.dumps(valid))
    v = clone(); v["rows"][0]["A"]["S"] = True; bad.append(v)
    v = clone(); v["rows"][0]["A"]["S"] = None; bad.append(v)
    v = clone(); v["rows"][0]["N_h"] = 9; bad.append(v)
    v = clone(); v["rows"].pop(); bad.append(v)
    v = clone(); v["rows"][1]["id"] = v["rows"][0]["id"]; bad.append(v)
    v = clone(); v["strata"].append({"stratum": "missing", "N_h": 20, "n_h": 2}); bad.append(v)
    bad.append(_synthetic_payload([("singleton", 5, [(0, 0)])]))
    v = _synthetic_payload([("h", 10, [(0, 0), (1, 1)])], True); del v["reference_info"]; bad.append(v)
    v = _synthetic_payload([("h", 10, [(0, 0), (1, 1)])], True); del v["rows"][0]["reference"]; bad.append(v)
    for v in bad:
        try: prepare(v)
        except ValueError: pass
        else: raise AssertionError("Invalid input accepted")
    checks["input_frame_and_explicit_reference_validation"] = {"status": "passed", "rejected_cases": len(bad)}
    a = interval_summary(.5, [None] * 201 + [.5] * 1799)
    b = interval_summary(.5, [None] * 200 + [.5] * 1800)
    assert a["lower"] is None and a["status"].startswith("unstable")
    assert b["lower"] == .5 and b["status"].endswith("conditional_on_defined")
    checks["undefined_threshold_strictly_over_10_percent"] = "passed"
    assert analyze(valid)["reference_generated"] is False
    assert "dictionary_vs_reference" not in analyze(valid)["comparisons"]
    checks["no_reference_inference"] = "passed"
    return {"status": "passed_synthetic_QA_only", "real_policy_text_read": False,
            "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "real_labels_read": False, "real_results_generated": False,
            "numpy_version": np.__version__, "checks": checks,
            "formula_audit": {"stratum_weight_total": "exactly N_h in every replicate",
                "replicate_mean_variance": "(1-n_h/N_h)*s_h^2/n_h",
                "scope": "stratified SRSWOR individual units, census strata constant",
                "nonlinear_CI_guarantee": False},
            "limitations": ["Rare nonlinear ratio intervals may have poor coverage.",
                "Positive rescaled weights preserve observed class support.",
                "Intervals exclude shared coding error, reference bias and unknown exposure.",
                "Completion bounds are weighted-sample bounds, not confidence intervals."]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--synthetic-qa", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refusing to overwrite existing output")
    if args.synthetic_qa:
        if args.input is not None:
            parser.error("Synthetic QA never accepts an input file")
        output = self_test()
    else:
        if args.input is None:
            parser.error("Explicit --input required")
        output = analyze(json.loads(args.input.read_text(encoding="utf-8")))
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "status": output["status"]}, ensure_ascii=False))
