"""Independent arithmetic from sealed evaluator comparison slots only.

No source/reference judgment is created and reference.jsonl is never opened.
Run after the inference seal and the actual evaluation manifest exist.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import collections
import datetime
import hashlib
import json
import math

AUDIT = Path(__file__).resolve().parent
IMPLEMENTATION = AUDIT.parent
DIMS = ("S", "E", "Ec", "I", "F")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def binding(path):
    path = Path(path)
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def state(value):
    if type(value) is int and value in (0, 1):
        return "binary"
    if value is None:
        return "null"
    if isinstance(value, str) and value == "NA":
        return "NA"
    return "unknown"


def ratio(a, b):
    return float(Fraction(a, b)) if b else None


def recompute(slots):
    n = len(slots)
    cells = collections.Counter({k: 0 for k in ("TP", "FP", "FN", "TN")})
    for slot in slots:
        if slot["arithmetic_category"] in cells:
            cells[slot["arithmetic_category"]] += 1
    tp, fp, fn, tn = (cells[k] for k in ("TP", "FP", "FN", "TN"))
    paired = tp + fp + fn + tn
    recall, specificity = ratio(tp, tp + fn), ratio(tn, tn + fp)
    pnull = sum(s["prediction_state"] == "null" and not s["technical_failure"] for s in slots)
    rnull = sum(s["reference_state"] == "null" for s in slots)
    punknown = sum(s["prediction_state"] == "unknown" and not s["technical_failure"] for s in slots)
    runknown = sum(s["reference_state"] == "unknown" for s in slots)
    pna = sum(s["prediction_state"] == "NA" and not s["technical_failure"] for s in slots)
    rna = sum(s["reference_state"] == "NA" for s in slots)
    technical = sum(s["technical_failure"] for s in slots)
    refpos = sum(s["reference_state"] == "binary" and s["reference"] == 1 for s in slots)
    refneg = sum(s["reference_state"] == "binary" and s["reference"] == 0 for s in slots)
    kappa = None
    if paired:
        observed = Fraction(tp + tn, paired)
        expected = Fraction((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn), paired * paired)
        if expected != 1:
            kappa = float((observed - expected) / (1 - expected))
    return {
        "confusion_determined": dict(cells),
        "all_source_denominator": n,
        "determined_denominator": paired,
        "prediction_null_n": pnull,
        "reference_null_n": rnull,
        "prediction_unknown_n": punknown,
        "reference_unknown_n": runknown,
        "prediction_NA_n": pna,
        "reference_NA_n": rna,
        "technical_failure_n": technical,
        "misprediction_n": fp + fn,
        "technical_failure_reference_positive_n": sum(s["technical_failure"] and s["reference_state"] == "binary" and s["reference"] == 1 for s in slots),
        "technical_failure_reference_negative_n": sum(s["technical_failure"] and s["reference_state"] == "binary" and s["reference"] == 0 for s in slots),
        "null_prediction_reference_positive_n": sum(not s["technical_failure"] and s["prediction_state"] == "null" and s["reference_state"] == "binary" and s["reference"] == 1 for s in slots),
        "null_prediction_reference_negative_n": sum(not s["technical_failure"] and s["prediction_state"] == "null" and s["reference_state"] == "binary" and s["reference"] == 0 for s in slots),
        "null_coverage": ratio(n - pnull, n),
        "coverage": ratio(n - pnull - punknown - pna - technical, n),
        "prediction_null_rate": ratio(pnull, n),
        "paired_determined_coverage": ratio(paired, n),
        "precision": ratio(tp, tp + fp),
        "recall": recall,
        "specificity": specificity,
        "F1": ratio(2 * tp, 2 * tp + fp + fn),
        "balanced_accuracy": (recall + specificity) / 2 if recall is not None and specificity is not None else None,
        "determined_accuracy": ratio(tp + tn, paired),
        "all_source_correct_rate": ratio(tp + tn, n),
        "all_source_unresolved_or_error_n": n - tp - tn,
        "recall_all_reference_positives_with_null_unresolved": ratio(tp, refpos),
        "specificity_all_reference_negatives_with_null_unresolved": ratio(tn, refneg),
        "cohens_kappa": kappa,
    }


def same_number(a, b):
    if a is None or b is None:
        return a is b
    if isinstance(a, dict):
        return a == b
    if type(a) is int:
        return type(b) is int and a == b
    return type(b) in (int, float) and math.isclose(a, b, rel_tol=0, abs_tol=1e-12)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-n", required=True, type=int, choices=(41, 36))
    args = parser.parse_args()
    n = args.expected_n
    EVALUATION = IMPLEMENTATION / f"evaluation{n}-01"
    comparison_path = EVALUATION / "comparison.jsonl"
    metrics_path = EVALUATION / "metrics.json"
    manifest_path = EVALUATION / "evaluation-manifest.json"
    seal_path = IMPLEMENTATION / f"run{n}-01/seal.json"
    comparison = [json.loads(line) for line in comparison_path.read_text().splitlines() if line.strip()]
    metrics = json.loads(metrics_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    seal = json.loads(seal_path.read_text())
    hashcheck = json.loads((AUDIT / "postrun-hashcheck.json").read_text())
    source_rows = [json.loads(line) for line in Path(seal["source_path"]).read_text().splitlines() if line.strip()]
    source_by_id = {row["id"]: row for row in source_rows}
    slots, problems = [], []
    for index, row in enumerate(comparison):
        p, r = row["prediction"], row["reference"]
        ps, rs = state(p), state(r)
        technical = row["technical_failure"]
        if type(technical) is not bool:
            problems.append({"row": index + 1, "problem": "invalid technical flag"})
        if technical:
            category = "technical_failure"
        elif ps == rs == "binary":
            category = {(1, 1): "TP", (1, 0): "FP", (0, 1): "FN", (0, 0): "TN"}[(p, r)]
        else:
            category = "unresolved"
        slot = {"id": row["id"], "dimension": row["dimension"],
                "prediction": p, "reference": r, "prediction_state": ps,
                "reference_state": rs, "technical_failure": technical,
                "arithmetic_category": category}
        slots.append(slot)
        for kind, got, expected in (
            ("prediction_state", row["prediction_state"], ps),
            ("reference_state", row["reference_state"], rs),
            ("binary_category", row["comparison"], category),
            ("binary_correctness", row["correct_binary_pair"], category in ("TP", "TN")),
            ("prediction_record_value", row["prediction_record"]["labels"][row["dimension"]], p),
            ("reference_record_value", row["reference_record"]["labels"][row["dimension"]], r),
        ):
            if got != expected:
                problems.append({"row": index + 1, "problem": kind, "got": got, "expected": expected})
        if row["source_record"] != source_by_id.get(row["id"]):
            problems.append({"row": index + 1, "problem": "source record or original image/geometry changed"})
    record_slots = collections.defaultdict(list)
    for slot in slots:
        record_slots[slot["id"]].append(slot)
    ids = set(record_slots)
    identities_ok = (len(slots) == n * len(DIMS) and len(ids) == n
                     and ids == set(source_by_id)
                     and all(len(group) == 5 and {s["dimension"] for s in group} == set(DIMS)
                             for group in record_slots.values()))
    if not identities_ok:
        problems.append({"problem": "all authorized unique record×5 slots not retained"})
    summaries = {d: recompute([s for s in slots if s["dimension"] == d]) for d in DIMS}
    summaries["all_decisions"] = recompute(slots)
    metric_checks = []
    for dim, computed in summaries.items():
        reported = metrics["all_decisions"] if dim == "all_decisions" else metrics["per_dimension"][dim]
        for key, value in computed.items():
            ok = key in reported and same_number(value, reported[key])
            metric_checks.append({"dimension": dim, "field": key, "passed": ok})
            if not ok:
                problems.append({"dimension": dim, "field": key, "computed": value, "reported": reported.get(key)})
    complete_records = [g for g in record_slots.values() if all(s["arithmetic_category"] in ("TP", "FP", "FN", "TN") for s in g)]
    exact_records = [g for g in record_slots.values() if all(s["arithmetic_category"] in ("TP", "TN") for s in g)]
    disagreed = [g for g in record_slots.values() if any(s["arithmetic_category"] in ("FP", "FN") for s in g)]
    unresolved = [g for g in record_slots.values() if any(s["arithmetic_category"] in ("technical_failure", "unresolved") for s in g)]
    technical_records = [g for g in record_slots.values() if any(s["technical_failure"] for s in g)]
    all36 = {"n": len(ids), "exact_complete_vector_n": len(exact_records),
             "error_or_unresolved_record_n": len(ids) - len(exact_records),
             "known_disagreement_record_n": len(disagreed), "unresolved_record_n": len(unresolved),
             "technical_failure_record_n": len(technical_records),
             "determined_record_denominator": len(complete_records),
             "exact_complete_vector_rate_all_records": ratio(len(exact_records), len(ids)),
             "exact_vector_rate_determined": ratio(len(exact_records), len(complete_records))}
    for key, value in all36.items():
        ok = same_number(value, metrics["all_records"].get(key))
        metric_checks.append({"dimension": "all_records", "field": key, "passed": ok})
        if not ok:
            problems.append({"field": "all_records/" + key, "computed": value, "reported": metrics["all_records"].get(key)})
    output_bindings_ok = all(sha(o["path"]) == o["sha256"] for o in manifest["outputs"])
    seal_bound_ok = sha(seal_path) == manifest["prediction_seal"]["sha256"]
    prediction_bound_ok = sha(seal["prediction_path"]) == seal["prediction_sha256"] == manifest["prediction"]["sha256"]
    evaluator_bound_ok = sha(manifest["evaluator"]["path"]) == manifest["evaluator"]["sha256"]
    hashchecks = {"evaluation_outputs_sha_verified": output_bindings_ok,
                  "prediction_seal_sha_verified": seal_bound_ok,
                  "prediction_sha_verified": prediction_bound_ok,
                  "evaluator_sha_verified": evaluator_bound_ok,
                  "sealed_code_hashes_still_verified": all(sha(f["path"]) == f["sha256"] for f in seal["implementation_files"]),
                  "source_manual_manifest_still_verified": all(sha(seal[k + "_path"]) == seal[k + "_sha256"] for k in ("source", "manual", "fixture_manifest")),
                  "postrun_hashcheck_passed": hashcheck["status"] == "paired_v04_postrun_hashcheck_passed",
                  "evaluation_after_prediction_seal": seal["sealed_at_utc"] < manifest["completed_at_utc"]}
    for key, value in hashchecks.items():
        if not value:
            problems.append({"problem": key})
    report = {"status": "independent_comparison_arithmetic_crosscheck_passed" if not problems else "independent_comparison_arithmetic_crosscheck_failed",
              "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "identity": "comparison_only_AI_development_arithmetic_not_new_reference_or_human_validation",
              "source_of_values": str(comparison_path) + " only; no new semantic judgments",
              "raw_reference_file_not_opened": True, "all_authorized_slots_retained": identities_ok,
              "source_records": len(ids), "dimension_slots": len(slots),
              "all_records": all36, "all_decisions": summaries.pop("all_decisions"), "per_dimension": summaries,
              "slot_categories": dict(collections.Counter(s["arithmetic_category"] for s in slots)),
              "all_authorized_slots": slots, "metric_field_checks": metric_checks,
              "all_metrics_matched": all(c["passed"] for c in metric_checks),
              "hash_and_seal_checks": hashchecks, "problems": problems,
              "bindings": [binding(p) for p in (comparison_path, metrics_path, manifest_path, seal_path, AUDIT / "postrun-hashcheck.json", Path(__file__))],
              "undefined_metric_handling": "Zero denominators remain null; an all-negative dimension has undefined precision/recall/F1/BA/kappa, rather than 0 or 1. Undefined metrics do not change retained slots.",
              "population_CI": None, "CI_reason": "Historically exposed nonprobability AI development fixture",
              "human_validation": False, "final_acceptance": False,
              "semantic_fixes_performed": False,
              "old_material_regression_only": True,
              "updated_common_source_material_requires_separate_future_verification": True}
    output = AUDIT / f"arithmetic-crosscheck{n}.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "all_records": all36,
                      "all_decisions": report["all_decisions"], "all_metrics_matched": report["all_metrics_matched"],
                      "problem_n": len(problems), "output": binding(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
