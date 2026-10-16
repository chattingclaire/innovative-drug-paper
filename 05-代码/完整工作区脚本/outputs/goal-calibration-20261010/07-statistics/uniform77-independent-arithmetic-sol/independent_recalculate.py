"""Read-only independent development77 arithmetic audit.

Rule mode never reads native LLM outputs. Native mode requires an explicit
post-seal authorization flag and checks complete77 before loading predictions.
All writes are confined to this script's new audit directory.
"""
import argparse
import hashlib
import json
import math
import platform
import sys
import warnings
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
import openpyxl
import sklearn
from sklearn.metrics import (
    accuracy_score, cohen_kappa_score, confusion_matrix, f1_score,
    precision_score, recall_score,
)

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
DIMS = ("S", "E", "Ec", "I", "F")
FORMULA = ROOT / "scripts/verify_native_v16_campaign.py"
REFS = [ROOT / "09-delivery/agent-review-20261010" / name
        for name in ("编码复核表-A.xlsx", "编码复核表-B.xlsx")]
METRIC_NAMES = ("kappa", "precision", "recall", "F1", "Po", "Pe",
                "Ppos", "Pneg", "specificity", "NPV")
READ_BINDINGS = {}


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    item = {"path": str(path), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}
    previous = READ_BINDINGS.setdefault(str(path), item)
    assert previous == item, f"Input changed during audit: {path}"
    return item


def load_json(path):
    binding(path)
    return json.loads(Path(path).read_text())


def verify_binding(expected):
    actual = binding(expected["path"])
    assert actual["sha256"] == expected["sha256"], expected["path"]
    if "bytes" in expected:
        assert actual["bytes"] == expected["bytes"], expected["path"]
    return actual


def write_json(name, data):
    path = OUT / name
    with path.open("x") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2,
                                allow_nan=False) + "\n")
    return path


def divide(a, b):
    return None if b == 0 else float(Fraction(a, b))


def own_formula(y_true, y_pred):
    # Explicit sklearn direction: rows = reference, columns = prediction.
    assert len(y_true) == len(y_pred)
    if y_true:
        tn, fp, fn, tp = map(int, confusion_matrix(y_true, y_pred,
                                                  labels=[0, 1]).ravel())
    else:
        # sklearn 1.8 rejects zero-row inputs; the correct four cells are zero.
        tn = fp = fn = tp = 0
    cells = dict(TP=tp, FP=fp, FN=fn, TN=tn)
    n = len(y_true)
    assert n == tp + fp + fn + tn
    predicted_pos, predicted_neg = tp + fp, tn + fn
    reference_pos, reference_neg = tp + fn, tn + fp
    po_exact = None if not n else Fraction(tp + tn, n)
    pe_exact = None if not n else (
        Fraction(predicted_pos, n) * Fraction(reference_pos, n)
        + Fraction(predicted_neg, n) * Fraction(reference_neg, n))
    kappa = (None if po_exact is None or pe_exact == 1 else
             float((po_exact - pe_exact) / (1 - pe_exact)))
    metrics = dict(
        kappa=kappa, precision=divide(tp, predicted_pos),
        recall=divide(tp, reference_pos), F1=divide(2 * tp, 2 * tp + fp + fn),
        Po=None if po_exact is None else float(po_exact),
        Pe=None if pe_exact is None else float(pe_exact),
        Ppos=divide(2 * tp, predicted_pos + reference_pos),
        Pneg=divide(2 * tn, predicted_neg + reference_neg),
        specificity=divide(tn, reference_neg), NPV=divide(tn, predicted_neg))
    if n:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            kappa_sklearn = float(cohen_kappa_score(y_true, y_pred, labels=[0, 1]))
        # sklearn 1.8 supports np.nan for undefined binary precision/recall/F1.
        import numpy as np
        sk = dict(
            kappa=None if math.isnan(kappa_sklearn) else kappa_sklearn,
            precision=float(precision_score(y_true, y_pred, zero_division=np.nan)),
            recall=float(recall_score(y_true, y_pred, zero_division=np.nan)),
            F1=float(f1_score(y_true, y_pred, zero_division=np.nan)),
            Po=float(accuracy_score(y_true, y_pred)))
        sk = {key: None if value is not None and math.isnan(value) else value
              for key, value in sk.items()}
        for key, actual in sk.items():
            assert same(actual, metrics[key]), (key, actual, metrics[key])
        warning_text = [str(item.message) for item in captured]
    else:
        sk = {key: None for key in ("kappa", "precision", "recall", "F1", "Po")}
        warning_text = ["No joint binary observations: sklearn scalar calls skipped."]
    return cells, metrics, {"values": sk, "all_checked_values_match": True,
                            "warnings": warning_text}


def same(left, right):
    if left is None or right is None:
        return left is None and right is None
    return math.isclose(float(left), float(right), rel_tol=0, abs_tol=1e-12)


def formula_audit():
    binding(FORMULA)
    namespace = {"__name__": "synthetic_formula_audit", "__file__": str(FORMULA)}
    # No import cache or writes next to ROOT's original script.
    exec(compile(FORMULA.read_text(), str(FORMULA), "exec"), namespace)
    cases = [
        ("asymmetric_direction", [0, 0, 0, 1, 1, 1, 1], [0, 1, 1, 0, 0, 0, 1]),
        ("empty_joint_sample", [], []),
        ("all_reference_and_prediction_negative", [0, 0], [0, 0]),
        ("all_reference_and_prediction_positive", [1, 1], [1, 1]),
        ("no_predicted_positive", [0, 1], [0, 0]),
        ("no_reference_positive", [0, 0], [0, 1]),
        ("no_predicted_negative", [0, 1], [1, 1]),
        ("no_reference_negative", [1, 1], [0, 1]),
        ("opposed_constant_labels", [1, 1], [0, 0]),
        ("pairwise_null_exclusion", [0, 1, None, 1], [0, None, 1, 1]),
    ]
    checks = []
    for name, reference, prediction in cases:
        rows = [{"id": f"SYNTHETIC-{i}", "labels": dict.fromkeys(DIMS, value)}
                for i, value in enumerate(prediction)]
        refs = {f"SYNTHETIC-{i}": {"labels": dict.fromkeys(DIMS, value)}
                for i, value in enumerate(reference)}
        actual, _ = namespace["calculate"](rows, refs)
        pairs = [(ref, pred) for ref, pred in zip(reference, prediction)
                 if ref is not None and pred is not None]
        cells, metrics, sk = own_formula([ref for ref, _ in pairs],
                                          [pred for _, pred in pairs])
        assert actual["S"]["four_cells"] == cells, name
        assert all(same(actual["S"]["metrics"][key], metrics[key])
                   for key in METRIC_NAMES), name
        assert actual["S"]["joint_binary_N"] == len(pairs), name
        assert len(actual["S"]["null_pairs"]) == len(reference) - len(pairs), name
        checks.append({"case": name, "synthetic_only": True, "four_cells": cells,
                       "metrics": metrics, "sklearn_crosscheck": sk, "passed": True})
    assert checks[0]["four_cells"] == {"TP": 1, "FP": 2, "FN": 3, "TN": 1}
    return {
        "formula_script_binding": binding(FORMULA), "all_cases_passed": True,
        "direction": "reference=y_true; machine=y_pred; confusion rows reference and columns prediction",
        "metric_definitions": {
            "kappa": "(Po-Pe)/(1-Pe)", "precision": "TP/(TP+FP)",
            "recall": "TP/(TP+FN)", "F1": "2TP/(2TP+FP+FN)",
            "Po": "(TP+TN)/N", "Pe": "[(TP+FP)(TP+FN)+(TN+FN)(TN+FP)]/N²",
            "Ppos": "2TP/(2TP+FP+FN)", "Pneg": "2TN/(2TN+FP+FN)",
            "specificity": "TN/(TN+FP)", "NPV": "TN/(TN+FN)"},
        "NA_conditions": {
            "kappa": "N=0 or Pe=1 (N²-chance=0)", "precision": "TP+FP=0",
            "recall": "TP+FN=0", "F1": "2TP+FP+FN=0", "Po": "N=0",
            "Pe": "N=0", "Ppos": "2TP+FP+FN=0", "Pneg": "2TN+FP+FN=0",
            "specificity": "TN+FP=0", "NPV": "TN+FN=0"},
        "NA_semantics": "Null pairs excluded per dimension; denominator zero remains JSON null, never silently zero.",
        "sklearn_zero_division_review": "ROOT rule crosscheck uses zero_division=0; this differs from null at undefined precision/recall/F1, but all current rule77 denominators are nonzero. Independent script uses np.nan and normalizes to null.",
        "helper_preconditions": "calculate assumes callers have validated 0/1/null values, unique ids and reference coverage; the standalone helper does not enforce these itself. This audit validates those preconditions.",
        "marginal_count_review": "reference_positive/negative_N and prediction_positive/negative_N count all available rows, while four cells and all metrics use joint binary pairs. They can differ when null exists; current rule77 has no nulls.",
        "Ppos_F1_relationship": "Numerically identical by definition; positive agreement is symmetric and is not an extra independent performance statistic.",
        "semantic_validity_from_arithmetic": False, "cases": checks}


def read_reference(path):
    binding(path)
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    result = {}
    try:
        for row in workbook["编码表"].iter_rows(min_row=7, max_row=391, values_only=True):
            sid, dept, dimension, value = row[:4]
            assert isinstance(sid, str) and isinstance(dimension, str)
            dim = dimension.split()[0]
            assert dim in DIMS and type(value) is int and value in (0, 1)
            target = result.setdefault(sid, {"department": dept, "labels": {}})
            assert target["department"] == dept and dim not in target["labels"]
            target["labels"][dim] = value
    finally:
        workbook.close()
    assert len(result) == 77
    assert all(set(row["labels"]) == set(DIMS) for row in result.values())
    return result


def independent_dataset(predictions, reference):
    assert len(predictions) == len({row["id"] for row in predictions}) == 77
    assert set(reference) == {row["id"] for row in predictions}
    for row in predictions:
        assert set(row["labels"]) == set(DIMS)
        for value in row["labels"].values():
            assert value is None or type(value) is int and value in (0, 1)
    dimensions, differences = {}, []
    for dim in DIMS:
        pairs, nulls = [], []
        for row in predictions:
            pred, ref = row["labels"][dim], reference[row["id"]]["labels"][dim]
            if pred is None or ref is None:
                nulls.append({"id": row["id"], "prediction": pred, "reference": ref})
            else:
                pairs.append((ref, pred))
                if pred != ref:
                    differences.append({"id": row["id"], "dimension": dim,
                                        "prediction": pred, "reference": ref,
                                        "direction": "FP" if pred == 1 else "FN"})
        cells, metrics, sk = own_formula([ref for ref, _ in pairs],
                                         [pred for _, pred in pairs])
        dimensions[dim] = {
            "assigned_N": len(reference), "saved_N": len(predictions),
            "joint_binary_N": len(pairs),
            "reference_positive_N": sum(row["labels"][dim] == 1 for row in reference.values()),
            "reference_negative_N": sum(row["labels"][dim] == 0 for row in reference.values()),
            "prediction_positive_N": sum(row["labels"][dim] == 1 for row in predictions),
            "prediction_negative_N": sum(row["labels"][dim] == 0 for row in predictions),
            "null_pairs": nulls, "four_cells": cells, "metrics": metrics,
            "sklearn_crosscheck": sk,
            "point_targets": {key: None if metrics[key] is None else metrics[key] >= .8
                              for key in ("kappa", "precision", "recall", "F1")}}
    return dimensions, differences


def compare_existing(actual_dimensions, differences, existing):
    for dim, actual in actual_dimensions.items():
        wanted = existing["dimensions"][dim]
        for key in ("assigned_N", "saved_N", "joint_binary_N", "reference_positive_N",
                    "reference_negative_N", "prediction_positive_N", "prediction_negative_N",
                    "null_pairs", "four_cells", "point_targets"):
            assert actual[key] == wanted[key], (dim, key, actual[key], wanted[key])
        for key in METRIC_NAMES:
            assert same(actual["metrics"][key], wanted["metrics"][key]), (dim, key)
    canonical = lambda rows: sorted((row["id"], row["dimension"], row["prediction"],
                                    row["reference"], row["direction"]) for row in rows)
    assert canonical(differences) == canonical(existing["binary_disagreements"])
    return {"five_dimensions_all_ten_metrics_match": True, "all_four_cells_match": True,
            "all_counts_null_pairs_targets_match": True, "disagreements_match": True,
            "numeric_absolute_tolerance": 1e-12}


def run_rule():
    reported_path = ROOT / "07-statistics/rule-v18-current-posthoc-reference-root/metrics.json"
    reported = load_json(reported_path)
    for key in ("reference_bindings",):
        for item in reported[key]:
            verify_binding(item)
    for key in ("prediction_binding", "old_prediction_binding", "run_seal_binding",
                "calculation_script_binding", "formula_script_binding"):
        verify_binding(reported[key])
    seal = load_json(reported["run_seal_binding"]["path"])
    seal_checked = 0
    for key in ("implementation_files", "material_bindings", "control_inputs", "output_files"):
        for expected in seal[key]:
            verify_binding(expected)
            seal_checked += 1
    prediction_path = Path(reported["prediction_binding"]["path"])
    execution = load_json(prediction_path.parent / "execution.json")
    predictions = [json.loads(line) for line in prediction_path.read_text().splitlines()]
    assert execution["status"] == "completed"
    assert execution["actual_record_N"] == 77 and execution["actual_dimension_N"] == 385
    assert execution["technical_failure_dimension_N"] == execution["lawful_null_N"] == 0
    for row in predictions:
        assert all(row["decisions"][dim]["value"] == row["labels"][dim] for dim in DIMS)
    refs = [read_reference(path) for path in REFS]
    assert refs[0] == refs[1]
    dimensions, differences = independent_dataset(predictions, refs[0])
    comparison = compare_existing(dimensions, differences, reported)
    for key, value in dict(assigned_records_N=77, actual_complete_records_N=77,
                           actual_binary_slots_N=385, technical_failure_slots_N=0,
                           semantic_null_slots_N=0).items():
        assert reported[key] == value
    old = {row["id"]: row for row in
           [json.loads(line) for line in Path(reported["old_prediction_binding"]["path"]).read_text().splitlines()]}
    changes = [{"id": row["id"], "dimension": dim,
                "old": old[row["id"]]["labels"][dim], "new": row["labels"][dim]}
               for row in predictions for dim in DIMS
               if old[row["id"]]["labels"][dim] != row["labels"][dim]]
    assert changes == reported["changed_dimensions_vs_old_v17"]
    assert seal_checked == reported["verified_binding_N"]
    return dict(stage="rule-v18", source_report_binding=binding(reported_path),
                A_B_content_identical=True, execution_coverage={
                    "assigned_records_N": 77, "saved_unique_records_N": 77,
                    "expected_dimension_slots_N": 385, "actual_binary_slots_N": 385,
                    "technical_failure_slots_N": 0, "semantic_null_slots_N": 0,
                    "verified_rule_seal_bindings_N": seal_checked},
                dimensions=dimensions, binary_disagreements=differences,
                disagreement_slots_N=len(differences),
                disagreement_records_N=len({row["id"] for row in differences}),
                changes_vs_rule_v17=changes, comparison_with_ROOT=comparison)


def run_native():
    reported_path = ROOT / "07-statistics/native-v16-current-posthoc-reference-root/verification-and-metrics.json"
    reported = load_json(reported_path)
    assert reported["complete_77"] is True and reported["reference_comparison_unlocked"] is True
    assert reported["saved_verified_N"] == reported["expected_N"] == 77
    assert reported["incomplete_N"] == 0 and reported["verified_batches_N"] == 13
    assert all(batch["state"] == "sealed_verified" for batch in reported["batches"])
    assert len(reported["batches"]) == 13
    prediction_path = reported_path.parent / "predictions.jsonl"
    assert Path(reported["predictions_binding"]["path"]).resolve() == prediction_path.resolve()
    verify_binding(reported["predictions_binding"])
    manifest_binding = reported["run_manifest_binding"]
    verify_binding(manifest_binding)
    manifest = load_json(manifest_binding["path"])
    predictions = [json.loads(line) for line in prediction_path.read_text().splitlines()]
    assert [row["id"] for row in predictions] == manifest["global_order"]
    actual_batches = Counter(row["batch_id"] for row in predictions)
    raw_verified = {}
    for row in predictions:
        raw_path = row["raw_first_binding"]["path"]
        verify_binding(row["raw_first_binding"])
        raw_verified[raw_path] = row["raw_first_binding"]
    for batch in reported["batches"]:
        verify_binding(batch["first_binding"])
        verify_binding(batch["seal_binding"])
        assert actual_batches[batch["batch_id"]] == batch["saved_N"] == batch["expected_N"]
    assert len(raw_verified) == 13
    for item in reported["reference_bindings"]:
        verify_binding(item)
    refs = [read_reference(path) for path in REFS]
    assert refs[0] == refs[1]
    dimensions, differences = independent_dataset(predictions, refs[0])
    comparison = compare_existing(dimensions, differences, reported)
    binary = sum(type(value) is int and value in (0, 1)
                 for row in predictions for value in row["labels"].values())
    nulls = sum(value is None for row in predictions for value in row["labels"].values())
    assert binary + nulls == 385
    mutual = compare_machines(predictions)
    return dict(stage="native-v16", source_report_binding=binding(reported_path),
                predictions_binding=binding(prediction_path), A_B_content_identical=True,
                execution_coverage={"assigned_records_N": 77, "saved_unique_records_N": 77,
                    "expected_dimension_slots_N": 385, "saved_dimension_slots_N": 385,
                    "actual_binary_slots_N": binary, "semantic_null_slots_N": nulls,
                    "missing_record_N": 0, "missing_dimension_slots_N": 0,
                    "verified_batches_N": 13, "verified_unique_raw_first_bindings_N": 13,
                    "batch_saved_counts": dict(actual_batches)},
                dimensions=dimensions, binary_disagreements=differences,
                disagreement_slots_N=len(differences),
                disagreement_records_N=len({row["id"] for row in differences}),
                rule_native_mutual_agreement=mutual,
                comparison_with_ROOT=comparison)


def compare_machines(native_predictions):
    rule_report_path = ROOT / "07-statistics/rule-v18-current-posthoc-reference-root/metrics.json"
    rule_report = load_json(rule_report_path)
    rule_binding = rule_report["prediction_binding"]
    verify_binding(rule_binding)
    rule = {row["id"]: row for row in
            [json.loads(line) for line in Path(rule_binding["path"]).read_text().splitlines()]}
    assert len(rule) == 77 and set(rule) == {row["id"] for row in native_predictions}
    agreement, differences = {}, []
    for dim in DIMS:
        pairs = []
        for row in native_predictions:
            rule_value, native_value = rule[row["id"]]["labels"][dim], row["labels"][dim]
            if rule_value is not None and native_value is not None:
                pairs.append((rule_value, native_value))
                if rule_value != native_value:
                    differences.append({"id": row["id"], "dimension": dim,
                                        "rule_value": rule_value, "native_value": native_value})
        cells, metrics, sk = own_formula([value for value, _ in pairs],
                                         [value for _, value in pairs])
        agreement[dim] = {
            "joint_binary_N": len(pairs), "agreement_N": cells["TP"] + cells["TN"],
            "disagreement_N": cells["FP"] + cells["FN"],
            "four_cells_rule_as_row_native_as_column": cells,
            "Po": metrics["Po"], "Pe": metrics["Pe"], "kappa": metrics["kappa"],
            "Ppos": metrics["Ppos"], "Pneg": metrics["Pneg"],
            "sklearn_kappa_and_accuracy_match": sk["all_checked_values_match"]}
    all_pairs = [(rule[row["id"]]["labels"][dim], row["labels"][dim])
                 for row in native_predictions for dim in DIMS
                 if rule[row["id"]]["labels"][dim] is not None and row["labels"][dim] is not None]
    _, aggregate, _ = own_formula([value for value, _ in all_pairs],
                                 [value for _, value in all_pairs])
    return {
        "rule_prediction_binding": rule_binding,
        "interpretation": "Two-machine descriptive agreement; rule used as matrix rows only, not an independent human truth standard.",
        "dimensions": agreement, "differences": differences,
        "disagreement_slots_N": len(differences),
        "disagreement_records_N": len({row["id"] for row in differences}),
        "all_385_slots_descriptive_agreement": {
            "joint_binary_N": len(all_pairs), "Po": aggregate["Po"], "kappa": aggregate["kappa"],
            "pooled_kappa_is_not_substitute_for_dimension_specific_kappa": True},
        "formal_acceptance": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("rule", "native"))
    parser.add_argument("--root-confirmed-native77-sealed", action="store_true")
    args = parser.parse_args()
    if args.stage == "native":
        assert args.root_confirmed_native77_sealed, "Wait for ROOT's explicit complete77 seal notification."
    audit = formula_audit() if args.stage == "rule" else None
    result = run_rule() if args.stage == "rule" else run_native()
    result.update(created_at_utc=datetime.now(timezone.utc).isoformat(),
                  reference_identity="AI初表+真人局部事后复核；不是独立真人初判",
                  formal_acceptance=False, human_independent_coding_reliability=False,
                  population_CI95_calculated=False, p_values_calculated=False,
                  study_labels_generated_or_modified=False,
                  independent_method="sklearn confusion matrix and scalar metrics; separately implemented exact-Fraction agreement formulas",
                  runtime={"interpreter": sys.executable, "python": platform.python_version(),
                           "sklearn": sklearn.__version__, "openpyxl": openpyxl.__version__},
                  calculation_script_binding=binding(__file__))
    # Verify every observed input's hash again before committing local audit output.
    for expected in list(READ_BINDINGS.values()):
        verify_binding(expected)
    result["all_read_inputs_unchanged"] = True
    result["read_input_bindings"] = list(READ_BINDINGS.values())
    outputs = []
    if audit is not None:
        outputs.append(write_json("formula-audit.json", audit))
    outputs.append(write_json(f"{args.stage}-independent-results.json", result))
    outputs.append(Path(__file__).resolve())
    write_json(f"{args.stage}-audit-seal.json", {
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
        "members": [binding(path) for path in outputs],
        "source_inputs_verified_unchanged": True,
        "write_scope": str(OUT), "formal_acceptance": False})
    print(json.dumps({"stage": args.stage, "all_checks_passed": True,
                      "disagreement_slots_N": result["disagreement_slots_N"],
                      "coverage": result["execution_coverage"],
                      "metrics": {dim: value["metrics"] for dim, value in result["dimensions"].items()},
                      "output_directory": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
