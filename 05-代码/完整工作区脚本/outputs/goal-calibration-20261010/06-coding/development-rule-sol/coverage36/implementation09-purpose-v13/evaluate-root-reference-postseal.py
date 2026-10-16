"""Compare only the ROOT-adjudicated AI development reference after both real seals.
No coder import, source reinterpretation or label-driven repair occurs here.
Arithmetic helpers are reused from the archived v05 evaluator; undefined metrics
stay null and all technical/unknown/NA slots remain in the full denominator.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from typing import Any
import datetime as dt
import hashlib
import json
import sys
DIMENSIONS = ("S", "E", "Ec", "I", "F")
BASE = Path(__file__).resolve().parent
VERSION = "development-rule-sol-implementation09-purpose-v13"
class EvaluationError(ValueError):
    """Fail closed on an unsealed, changed, malformed, or incomplete input."""

def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)

def read_jsonl_bytes(payload: bytes, description: str) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        require(isinstance(value, dict), f"{description} line {number} is not an object")
        rows.append(value)
    return rows

def row_id(row: dict[str, Any]) -> str:
    value = row.get("id", row.get("unit_id"))
    require(isinstance(value, str) and bool(value.strip()), "Record identifier is absent")
    return value

def decision_map(row: dict[str, Any]) -> dict[str, Any]:
    """Adapt label/decision shapes at evaluation time without consulting a coder."""
    candidates = [row]
    for key in ("prediction", "reference", "consensus"):
        if isinstance(row.get(key), dict):
            candidates.append(row[key])
    for candidate in candidates:
        for key in ("decisions", "labels", "consensus_labels"):
            value = candidate.get(key)
            if isinstance(value, dict) and set(DIMENSIONS).issubset(value):
                return {dimension: value[dimension] for dimension in DIMENSIONS}
            if isinstance(value, list):
                mapped = {item.get("dimension"): item for item in value if isinstance(item, dict)}
                if set(DIMENSIONS).issubset(mapped):
                    return {dimension: mapped[dimension] for dimension in DIMENSIONS}
        if set(DIMENSIONS).issubset(candidate):
            return {dimension: candidate[dimension] for dimension in DIMENSIONS}
    raise EvaluationError("Unknown decision shape: expected five labels or five dimension decisions")

def label_value(value: Any) -> int | None:
    if isinstance(value, dict):
        for key in ("label", "value", "decision"):
            if key in value:
                value = value[key]
                break
        else:
            raise EvaluationError("Dimension decision has no label/value/decision")
    require(value is None or (type(value) is int and value in (0, 1)),
            f"Invalid binary-or-null decision: {value!r}")
    return value

def explicit_state(value: Any) -> tuple[int | None, str]:
    """Keep explicit NA/unknown separate from absent technical judgments."""
    if isinstance(value, dict):
        for key in ("label", "value", "decision"):
            if key in value:
                value = value[key]
                break
        else:
            raise EvaluationError("Dimension decision has no label/value/decision")
    if isinstance(value, str):
        if value.strip().casefold() in {"na", "n/a", "not_applicable"}:
            return None, "NA"
        if value.strip().casefold() in {"unknown", "undetermined"}:
            return None, "unknown"
    result = label_value(value)
    return result, "unknown" if result is None else "binary"

def divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None

def binary_metrics(counts: Counter[str], total: int) -> dict[str, Any]:
    tp, fp, fn, tn = (counts[key] for key in ("TP", "FP", "FN", "TN"))
    determined = tp + fp + fn + tn
    precision = divide(tp, tp + fp)
    recall = divide(tp, tp + fn)
    specificity = divide(tn, tn + fp)
    f1 = divide(2 * tp, 2 * tp + fp + fn)
    balanced = (recall + specificity) / 2 if recall is not None and specificity is not None else None
    observed = divide(tp + tn, determined)
    expected = divide((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp), determined * determined)
    kappa = (observed - expected) / (1 - expected) if observed is not None and expected != 1 else None
    return {
        "confusion_determined": {key: counts[key] for key in ("TP", "FP", "FN", "TN")},
        "all_source_denominator": total,
        "determined_denominator": determined,
        "prediction_null_n": counts["prediction_null"],
        "reference_null_n": counts["reference_null"],
        "prediction_unknown_n": counts["prediction_unknown"],
        "reference_unknown_n": counts["reference_unknown"],
        "prediction_NA_n": counts["prediction_NA"],
        "reference_NA_n": counts["reference_NA"],
        "technical_failure_n": counts["technical_failure"],
        "misprediction_n": fp + fn,
        "technical_failure_reference_positive_n": counts["technical_positive"],
        "technical_failure_reference_negative_n": counts["technical_negative"],
        "null_prediction_reference_positive_n": counts["null_positive"],
        "null_prediction_reference_negative_n": counts["null_negative"],
        "null_coverage": divide(total - counts["prediction_null"] - counts["technical_failure"], total),
        "coverage": divide(total - counts["prediction_null"] - counts["technical_failure"] - counts["prediction_NA"], total),
        "prediction_null_rate": divide(counts["prediction_null"], total),
        "paired_determined_coverage": divide(determined, total),
        "precision": precision, "recall": recall, "specificity": specificity,
        "F1": f1, "balanced_accuracy": balanced,
        "determined_accuracy": observed,
        "all_source_correct_rate": divide(tp + tn, total),
        "all_source_unresolved_or_error_n": total - tp - tn,
        "recall_all_reference_positives_with_null_unresolved": divide(tp, tp + fn + counts["null_positive"] + counts["technical_positive"] + counts["NA_positive"]),
        "specificity_all_reference_negatives_with_null_unresolved": divide(tn, tn + fp + counts["null_negative"] + counts["technical_negative"] + counts["NA_negative"]),
        "cohens_kappa": kappa,
        "kappa_identity": "Agreement with ROOT-adjudicated AI development labels v2; not human inter-coder reliability",
        "metric_denominator_note": (
            "TP/FP/FN/TN and conventional precision/recall/specificity/F1/balanced accuracy/kappa use "
            "binary predictions paired with binary references. All-source correctness, errors and "
            "coverage retain every case. Rule null/unknown, explicit NA, and technical failure are distinct "
            "unresolved states; none becomes zero or disappears. Technical failure is never FP/FN. "
            "Metrics from a failed attempt are descriptive diagnostic arithmetic, not valid run metrics. "
            "Undefined denominators, n=0, or kappa expected agreement=1 produce null."
        ),
    }

def count_pair(counts: Counter[str], predicted: int | None, reference: int | None) -> str:
    if predicted is None:
        counts["prediction_null"] += 1
    if reference is None:
        counts["reference_null"] += 1
    if predicted is None or reference is None:
        if predicted is None and reference is not None:
            counts["null_positive" if reference else "null_negative"] += 1
        return "null_unresolved"
    category = { (1, 1): "TP", (1, 0): "FP", (0, 1): "FN", (0, 0): "TN" }[(predicted, reference)]
    counts[category] += 1
    return category

def count_states(counts: Counter[str], predicted: int | None, reference: int | None,
                 prediction_state: str, reference_state: str) -> str:
    if reference_state == "NA":
        counts["reference_NA"] += 1
    elif reference_state == "unknown":
        counts["reference_unknown"] += 1
    if prediction_state == "technical_failure":
        counts["technical_failure"] += 1
        if reference is not None:
            counts["technical_positive" if reference else "technical_negative"] += 1
        if reference_state == "unknown":
            counts["reference_null"] += 1
        return "technical_failure"
    if prediction_state == "NA":
        counts["prediction_NA"] += 1
        if reference is not None:
            counts["NA_positive" if reference else "NA_negative"] += 1
        if reference_state == "unknown":
            counts["reference_null"] += 1
        return "NA_unresolved"
    if prediction_state == "unknown":
        counts["prediction_unknown"] += 1
    if reference_state == "NA":
        if prediction_state == "unknown":
            counts["prediction_null"] += 1
        return "NA_unresolved"
    return count_pair(counts, predicted, reference)


def bind(path):
    path=Path(path).resolve();data=path.read_bytes()
    return {"path":str(path),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)}

def write_json(path,value):
    with Path(path).open("x",encoding="utf-8") as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n")

def write_rows(path,values):
    with Path(path).open("x",encoding="utf-8") as stream:
        for value in values:stream.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+"\n")

def main():
    out=BASE/"evaluation-root-v2-postseal-01"
    require(not out.exists(),"Keep the first evaluation output; no repeated overwrite")
    declarations=json.loads((BASE/"finite-execution-scope-before-source.json").read_text())
    expected=declarations["scopes"]["old41"]+declarations["scopes"]["old36"]
    require(len(expected)==77 and len(set(expected))==77,"Only the exact old41/old36 development77 scope")
    bound_runs=[];all_slots=[];predictions={};scope_by_id={}
    # Reference content is inaccessible until BOTH actual first runs are sealed.
    for name in ("old41","old36"):
        directory=BASE/("run-"+name+"-01");seal=json.loads((directory/"seal.json").read_text())
        require(seal["runtime_version"]==VERSION and seal["status"] in ("sealed_development_predictions","sealed_failed_development_attempt"),"First actual run is not sealed for v09")
        require(seal["no_reference_read"] is True,"Reference was not an inference input")
        for item in seal["output_files"]+seal["implementation_files"]:
            require(bind(item["path"])==item,"Actual code/output differs from its first seal: "+item["path"])
        expected_ids=declarations["scopes"][name]
        require(seal["record_ids"]==expected_ids,"Sealed record scope changed")
        slots=read_jsonl_bytes((directory/"all-dimension-slots.jsonl").read_bytes(),"all dimension slots")
        require(len(slots)==len(expected_ids)*5 and len({(x["id"],x["dimension"]) for x in slots})==len(slots),"Full five-slot denominator is absent")
        require({(x["id"],x["dimension"]) for x in slots}=={(rid,dim) for rid in expected_ids for dim in DIMENSIONS},"Unexpected/missing sealed slot")
        for row in read_jsonl_bytes((directory/"predictions.jsonl").read_bytes(),"predictions"):
            require(row["id"] not in predictions,"Duplicate prediction ID")
            predictions[row["id"]]=row
        all_slots+=slots;scope_by_id.update({rid:name for rid in expected_ids})
        bound_runs.append({"scope":name,"seal":bind(directory/"seal.json"),"outputs":seal["output_files"],"implementation_files":seal["implementation_files"]})
    require(set(predictions)==set(expected),"Predictions do not retain the exact 77 IDs")
    # This is the user's authorized new AI development reference, not any A/B/native file.
    reference=BASE.parents[2]/"development-reference77-v12-root-adjudicated-v2/reference.jsonl"
    require(reference.is_file(),"Authorized updated ROOT reference is missing")
    reference_payload=reference.read_bytes();reference_binding={"path":str(reference),"sha256":hashlib.sha256(reference_payload).hexdigest(),"bytes":len(reference_payload)}
    out.mkdir()
    freeze={"status":"both_actual_first_run_seals_verified_before_updated_reference_decode","created_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"evaluator":bind(__file__),"actual_runs":bound_runs,"reference":reference_binding,"expected_unique_record_N":77,"expected_slot_N":385,"reference_identity":"ROOT-adjudicated AI development reference v2; not independent human reference","not_inference_input":True,"no_old_reference_or_AB_native_file_opened":True}
    write_json(out/"freeze-before-reference-decode.json",freeze)
    references={}
    for row in read_jsonl_bytes(reference_payload,"ROOT reference"):
        rid=row_id(row);require(rid not in references,"Duplicate ROOT reference ID");references[rid]=row
    require(set(references)==set(expected),"Updated reference is not the exact authorized 77-record scope")
    comparisons=[];mis=[];unresolved=[];counts=Counter();perdim={d:Counter() for d in DIMENSIONS};perscope={s:{d:Counter() for d in DIMENSIONS} for s in ("old41","old36")};scope_counts={s:Counter() for s in perscope}
    for slot in all_slots:
        rid,dim=slot["id"],slot["dimension"];predrow=predictions[rid];refrow=references[rid]
        refdecision=decision_map(refrow)[dim];refval,refstate=explicit_state(refdecision)
        if slot["technical_failure"]:
            predval,predstate=None,"technical_failure"
        else:
            predval,predstate=explicit_state(slot["retained_rule_decision"])
            require(predval==slot["rule_value"],"Retained slot value differs from its sealed rule decision")
        category=count_states(counts,predval,refval,predstate,refstate)
        count_states(perdim[dim],predval,refval,predstate,refstate)
        count_states(scope_counts[scope_by_id[rid]],predval,refval,predstate,refstate)
        count_states(perscope[scope_by_id[rid]][dim],predval,refval,predstate,refstate)
        comparison={"id":rid,"scope":scope_by_id[rid],"dimension":dim,"prediction":predval,"reference":refval,"prediction_state":predstate,"reference_state":refstate,"category":category,"sealed_slot_status":slot["status"],"rule_decision":slot["retained_rule_decision"],"reference_decision":refdecision,"implementation_errors":predrow["implementation_errors"],"source_requests":predrow["source_requests"],"material_requests":predrow["material_requests"],"reference_row_sha256":hashlib.sha256(json.dumps(refrow,ensure_ascii=False,sort_keys=True,separators=(",",":" )).encode()).hexdigest()}
        comparisons.append(comparison)
        if category in ("FP","FN"):mis.append(comparison)
        if category not in ("TP","FP","FN","TN"):unresolved.append(comparison)
    metrics={"status":"postseal_updated_AI_development_reference_diagnostics_only","unique_record_N":77,"all_dimension_slot_N":385,"reference_identity":"ROOT-adjudicated AI development v2","not_human_reliability_or_generalization_or_final_acceptance":True,"overall":binary_metrics(counts,385),"dimensions":{d:binary_metrics(perdim[d],77) for d in DIMENSIONS},"scopes":{s:{"record_N":len(declarations["scopes"][s]),"overall":binary_metrics(scope_counts[s],len(declarations["scopes"][s])*5),"dimensions":{d:binary_metrics(perscope[s][d],len(declarations["scopes"][s])) for d in DIMENSIONS}} for s in perscope},"misprediction_slot_N":len(mis),"unresolved_slot_N":len(unresolved),"no_repair_or_rerun_after_reference_read":True}
    write_rows(out/"comparison.jsonl",comparisons);write_rows(out/"mispredictions.jsonl",mis);write_rows(out/"unresolved.jsonl",unresolved);write_json(out/"metrics.json",metrics)
    with (out/"reference-input-byte-copy.jsonl").open("xb") as stream:stream.write(reference_payload)
    require(bind(reference)==reference_binding,"Updated reference changed during evaluation")
    for run in bound_runs:
        require(bind(run["seal"]["path"])==run["seal"],"Actual seal changed during evaluation")
        for item in run["outputs"]+run["implementation_files"]:require(bind(item["path"])==item,"Actual first output changed during evaluation")
    outputs=[bind(p) for p in sorted(out.iterdir()) if p.is_file()]
    write_json(out/"evaluation-seal.json",{"status":"sealed_postseal_updated_AI_reference_comparison","created_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"reference":reference_binding,"actual_runs":bound_runs,"evaluator":bind(__file__),"outputs":outputs,"unique_record_N":77,"all_dimension_slot_N":385,"misprediction_slot_N":len(mis),"unresolved_slot_N":len(unresolved),"no_inference_rerun":True})
    print(json.dumps({"status":metrics["status"],"record_N":77,"slot_N":385,"misprediction_N":len(mis),"unresolved_N":len(unresolved),"overall":metrics["overall"]},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
