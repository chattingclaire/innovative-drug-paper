#!/usr/bin/env python3
"""Independent exact-arithmetic math checks. Reads synthetic local fixtures only.

This file does not discover project data, sample units, call a model, or assign
real labels. Import analytical_bounds / enumerate_bounds / confusion_metrics /
paired_report, or consume the adjacent fixture JSON from a parent test suite.
"""

import argparse
import itertools
import json
from fractions import Fraction
from pathlib import Path


DIMENSIONS = 5
VALID_OUTPUT = "valid_output"
UNRETURNED_STATUSES = {"execution_failure", "not_returned"}


def frac(value):
    return Fraction(str(value))


def divide(numerator, denominator):
    return numerator / denominator if denominator else None


def jsonable(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


def effective_labels(output):
    status = output["status"]
    if status == VALID_OUTPUT:
        labels = output["labels"]
        if not isinstance(labels, list) or len(labels) != DIMENSIONS:
            raise ValueError("A valid output must have exactly five dimensions")
        if any(value is not None and (type(value) is not int or value not in (0, 1)) for value in labels):
            raise ValueError("Semantic values must be integer 0/1 or null")
        return labels
    if status in UNRETURNED_STATUSES:
        if output.get("labels") is not None:
            raise ValueError("A whole-output failure/nonreturn cannot retain purported valid labels")
        # Expansion is epistemic only; original status remains independently counted.
        return [None] * DIMENSIONS
    raise ValueError("Unrecognized output status")


def totals(rows):
    ids = [row["id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate assigned unit IDs")
    weights = [frac(row["weight"]) for row in rows]
    if any(weight < 0 for weight in weights):
        raise ValueError("Bounds require nonnegative fixed weights")
    labels = [effective_labels(row) for row in rows]
    k = [sum((weight for weight, label in zip(weights, labels) if label[d] == 1), Fraction(0)) for d in range(DIMENSIONS)]
    u = [sum((weight for weight, label in zip(weights, labels) if label[d] is None), Fraction(0)) for d in range(DIMENSIONS)]
    return weights, labels, k, u


def analytical_bounds(rows):
    weights, labels, k, u = totals(rows)
    N = sum(weights, Fraction(0))
    H = sum(k, Fraction(0))
    U = sum(u, Fraction(0))
    coverage = [[divide(k[d], N), divide(k[d] + u[d], N)] for d in range(DIMENSIONS)]
    share = []
    for d in range(DIMENSIONS):
        other = U - u[d]
        if H > 0:
            share.append([k[d] / (H + other), (k[d] + u[d]) / (H + u[d])])
        elif U == 0:
            share.append(None)
        elif u[d] == 0:
            share.append([Fraction(0), Fraction(0)])
        elif other == 0:
            share.append([Fraction(1), Fraction(1)])
        else:
            share.append([Fraction(0), Fraction(1)])
    return {
        "assigned_count": len(rows), "assigned_weight": N,
        "known_hits": k, "unresolved_mass": u,
        "coverage": coverage, "share_conditional_positive": share,
        "zero_hit_completion_possible": H == 0,
        "positive_hit_completion_possible": H + U > 0,
        "semantic_null_counts": [sum(row["status"] == VALID_OUTPUT and labels[i][d] is None for i, row in enumerate(rows)) for d in range(DIMENSIONS)],
        "execution_failure_count": sum(row["status"] == "execution_failure" for row in rows),
        "not_returned_count": sum(row["status"] == "not_returned" for row in rows),
    }


def enumerate_bounds(rows):
    """Brute-force each unresolved binary cell; no analytical bound formula used."""
    weights, labels, k, _ = totals(rows)
    N = sum(weights, Fraction(0))
    unknown_cells = [(i, d) for i, label in enumerate(labels) for d, value in enumerate(label) if value is None]
    coverage_values = [set() for _ in range(DIMENSIONS)]
    share_values = [set() for _ in range(DIMENSIONS)]
    has_zero = False
    has_positive = False
    completions = 0
    for bits in itertools.product((0, 1), repeat=len(unknown_cells)):
        hits = k.copy()
        for (i, d), bit in zip(unknown_cells, bits):
            if bit:
                hits[d] += weights[i]
        H = sum(hits, Fraction(0))
        completions += 1
        has_zero |= H == 0
        has_positive |= H > 0
        for d in range(DIMENSIONS):
            if N:
                coverage_values[d].add(hits[d] / N)
            if H:
                share_values[d].add(hits[d] / H)
    # Coverage of an empty/zero-weight domain is undefined.
    coverage = [[min(values), max(values)] if values else [None, None] for values in coverage_values]
    share = [[min(values), max(values)] if values else None for values in share_values]
    return {
        "coverage": coverage, "share_conditional_positive": share,
        "zero_hit_completion_possible": has_zero,
        "positive_hit_completion_possible": has_positive,
        "completion_count": completions,
    }


def confusion_metrics(a, b, c, d):
    """a=TP, b=FP, c=FN, d=TN; rows reference A, columns prediction B."""
    a, b, c, d = map(frac, (a, b, c, d))
    if min(a, b, c, d) < 0:
        raise ValueError("Confusion counts/masses must be nonnegative")
    n = a + b + c + d
    ao = divide(a + d, n)
    pe = divide((a + b) * (a + c) + (c + d) * (b + d), n * n)
    kappa = None if pe is None or pe == 1 else (ao - pe) / (1 - pe)
    return {
        "n": n, "agreement": ao, "expected_agreement": pe, "kappa": kappa,
        "precision": divide(a, a + b), "recall": divide(a, a + c),
        "f1": divide(2 * a, 2 * a + b + c),
        "positive_agreement": divide(2 * a, 2 * a + b + c),
        "negative_agreement": divide(2 * d, 2 * d + b + c),
    }


def state(output, dimension):
    if output["status"] == VALID_OUTPUT:
        label = effective_labels(output)[dimension]
        return "null" if label is None else str(label)
    effective_labels(output)  # Validate full-output failure handling.
    return output["status"]


def paired_report(rows):
    """Outer-assignment-led joint table; per-coder margins never used as pair n."""
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate assigned unit IDs")
    weights = [frac(row["weight"]) for row in rows]
    if any(weight < 0 for weight in weights):
        raise ValueError("Nonnegative fixed weights required")
    result = {"assigned_count": len(rows), "assigned_weight": sum(weights, Fraction(0))}
    for coder in ("A", "B"):
        result[coder + "_valid_count"] = [sum(state(row[coder], d) in ("0", "1") for row in rows) for d in range(DIMENSIONS)]
        result[coder + "_valid_weight"] = [sum((weight for row, weight in zip(rows, weights) if state(row[coder], d) in ("0", "1")), Fraction(0)) for d in range(DIMENSIONS)]
        for status_name in sorted(UNRETURNED_STATUSES):
            key = coder + "_" + status_name
            result[key + "_count"] = sum(row[coder]["status"] == status_name for row in rows)
            result[key + "_weight"] = sum((weight for row, weight in zip(rows, weights) if row[coder]["status"] == status_name), Fraction(0))
    result["pair_count"] = [sum(state(row["A"], d) in ("0", "1") and state(row["B"], d) in ("0", "1") for row in rows) for d in range(DIMENSIONS)]
    result["pair_weight"] = [sum((weight for row, weight in zip(rows, weights) if state(row["A"], d) in ("0", "1") and state(row["B"], d) in ("0", "1")), Fraction(0)) for d in range(DIMENSIONS)]
    all_five_pairs = [all(state(row["A"], d) in ("0", "1") and state(row["B"], d) in ("0", "1") for d in range(DIMENSIONS)) for row in rows]
    result["all_five_pair_count"] = sum(all_five_pairs)
    result["all_five_pair_weight"] = sum((weight for weight, valid in zip(weights, all_five_pairs) if valid), Fraction(0))
    states3 = ("0", "1", "null")
    tables = []
    for dim in range(DIMENSIONS):
        cells = {}
        for row, weight in zip(rows, weights):
            pair = (state(row["A"], dim), state(row["B"], dim))
            if pair not in cells:
                cells[pair] = {"count": 0, "weight": Fraction(0)}
            cells[pair]["count"] += 1
            cells[pair]["weight"] += weight
        tables.append({"|".join(pair): cell for pair, cell in sorted(cells.items())})
    result["all_state_pair_tables"] = tables
    d1 = tables[0]
    def cell(a, b):
        return d1.get(a + "|" + b, {"count": 0, "weight": Fraction(0)})
    result["D1_3x3_count"] = [[cell(a, b)["count"] for b in states3] for a in states3]
    result["D1_3x3_weight"] = [[cell(a, b)["weight"] for b in states3] for a in states3]
    one_unknown = [cell(a, b) for a, b in (("null", "0"), ("null", "1"), ("0", "null"), ("1", "null"))]
    result["D1_one_semantic_unknown_count"] = sum(item["count"] for item in one_unknown)
    result["D1_one_semantic_unknown_weight"] = sum((item["weight"] for item in one_unknown), Fraction(0))
    result["D1_both_semantic_unknown_count"] = cell("null", "null")["count"]
    result["D1_both_semantic_unknown_weight"] = cell("null", "null")["weight"]
    result["D1_outside_3x3_count"] = len(rows) - sum(sum(row) for row in result["D1_3x3_count"])
    result["D1_outside_3x3_weight"] = sum(weights, Fraction(0)) - sum((sum(row, Fraction(0)) for row in result["D1_3x3_weight"]), Fraction(0))
    return result


def assert_expected(actual, expected, label):
    for key, value in expected.items():
        if jsonable(actual[key]) != value:
            raise AssertionError(f"{label}.{key}: actual={jsonable(actual[key])!r}, expected={value!r}")


def assert_matches_enumeration(rows, label):
    analytic = analytical_bounds(rows)
    enumerated = enumerate_bounds(rows)
    for key in ("coverage", "share_conditional_positive", "zero_hit_completion_possible", "positive_hit_completion_possible"):
        if analytic[key] != enumerated[key]:
            raise AssertionError(f"Enumeration mismatch {label}.{key}")
    return enumerated["completion_count"]


def systematic_sweep(full=False):
    """All 3-state patterns in stated synthetic schemas, with exact enumeration."""
    patterns = completions = 0
    for values in itertools.product((0, 1, None), repeat=DIMENSIONS):
        rows = [{"id": "sweep-1", "weight": 1, "status": VALID_OUTPUT, "labels": list(values)}]
        completions += assert_matches_enumeration(rows, "one-record-five-dimensions")
        patterns += 1
    active = DIMENSIONS if full else 3
    tails = [[]] if full else [[0, 0], [1, 0]]
    for tail in tails:
        for values in itertools.product((0, 1, None), repeat=2 * active):
            rows = [
                {"id": "sweep-1", "weight": 1, "status": VALID_OUTPUT, "labels": list(values[:active]) + tail},
                {"id": "sweep-2", "weight": 2, "status": VALID_OUTPUT, "labels": list(values[active:]) + [0] * (DIMENSIONS - active)},
            ]
            completions += assert_matches_enumeration(rows, "two-record-weighted")
            patterns += 1
    return {"base_patterns_checked": patterns, "binary_completions_enumerated": completions, "full_two_record_five_dimension_sweep": full}


def run_checks(fixtures, full=False):
    boundary_results = []
    for case in fixtures["boundary_cases"]:
        actual = analytical_bounds(case["rows"])
        assert_expected(actual, case["expected"], case["case_id"])
        completion_count = assert_matches_enumeration(case["rows"], case["case_id"])
        boundary_results.append({"case_id": case["case_id"], "pass": True, "completion_count": completion_count, "actual": actual})
    metric_results = []
    for case in fixtures["confusion_cases"]:
        actual = confusion_metrics(case["a"], case["b"], case["c"], case["d"])
        assert_expected(actual, case["expected"], case["case_id"])
        metric_results.append({"case_id": case["case_id"], "pass": True, "actual": actual})
    paired = paired_report(fixtures["paired_case"]["rows"])
    assert_expected(paired, fixtures["paired_case"]["expected"], fixtures["paired_case"]["case_id"])
    # Empty/zero-weight assigned domain guard, independent of any corpus.
    for rows in ([], [{"id": "zero", "weight": 0, "status": VALID_OUTPUT, "labels": [None] * DIMENSIONS}]):
        assert_matches_enumeration(rows, "zero_weight_domain")
        assert analytical_bounds(rows)["coverage"] == [[None, None]] * DIMENSIONS
    # Strict input guards: no Boolean/string surrogate label and no negative weight.
    invalid_rows = [
        [{"id": "bad", "weight": -1, "status": VALID_OUTPUT, "labels": [0] * DIMENSIONS}],
        [{"id": "bad", "weight": 1, "status": VALID_OUTPUT, "labels": [True, 0, 0, 0, 0]}],
        [{"id": "bad", "weight": 1, "status": VALID_OUTPUT, "labels": ["1", 0, 0, 0, 0]}],
        [{"id": "bad", "weight": 1, "status": "execution_failure", "labels": [0] * DIMENSIONS}],
        [{"id": "bad", "weight": 1, "status": "not_returned", "labels": [0] * DIMENSIONS}],
    ]
    for rows in invalid_rows:
        try:
            analytical_bounds(rows)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid synthetic interface was accepted")
    acceptance_results = []
    for case in fixtures["acceptance_cases"]:
        gates = case["metric_pass"] and case["credible_human_identity"] and case["frozen_independent_process"]
        # Failure of any necessary gate is rejection; passing these does not claim sufficiency.
        actual = None if gates else False
        assert actual == case["expected_formal_acceptance"]
        acceptance_results.append({"case_id": case["case_id"], "pass": True, "formal_acceptance": actual})
    return {
        "status": "passed_synthetic_checks_only_no_actual_acceptance",
        "input_source": "adjacent synthetic fixture JSON only",
        "real_label_records_read": 0, "real_labels_computed": 0, "model_calls": 0,
        "boundary_cases": boundary_results, "confusion_cases": metric_results,
        "paired_case": {"pass": True, "actual": paired},
        "acceptance_cases": acceptance_results,
        "systematic_sweep": systematic_sweep(full=full),
        "strict_input_guard_cases_passed": len(invalid_rows),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-sweep", action="store_true", help="Enumerate all two-record five-dimension 0/1/null base patterns too")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("toy-enumeration-result.json"))
    args = parser.parse_args()
    # Fixed adjacent path prevents implicit discovery of real project labels.
    fixture_path = Path(__file__).with_name("toy-boundary-cases.json")
    fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
    result = run_checks(fixtures, full=args.full_sweep)
    args.output.write_text(json.dumps(jsonable(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "boundary_cases": len(result["boundary_cases"]), "confusion_cases": len(result["confusion_cases"]), "systematic_sweep": result["systematic_sweep"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
