from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / "当前真人参照40条.jsonl"
PREDICTION = HERE / "40条规则实际输出-dc26-relation-candidate-02.jsonl"
DIMENSIONS = ("S", "E", "Ec", "I", "F")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def ratio(a: int, b: int):
    return None if b == 0 else a / b


def metric(tp: int, fp: int, fn: int, tn: int) -> dict:
    n = tp + fp + fn + tn
    po = ratio(tp + tn, n)
    pe = ratio((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn), n * n)
    kappa = None if po is None or pe == 1 else (po - pe) / (1 - pe)
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    f1 = None if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {"n": n, "TP": tp, "FP": fp, "FN": fn, "TN": tn, "kappa": kappa,
            "precision": precision, "recall": recall, "F1": f1}


pred_rows = read_jsonl(PREDICTION)
ref_rows = read_jsonl(REFERENCE)
pred = {row["material_id"]: row for row in pred_rows}
ref = {row["material_id"]: row for row in ref_rows}
assert len(pred) == len(ref) == 40 and set(pred) == set(ref)

metrics = []
differences = []
for dimension in DIMENSIONS:
    tp = fp = fn = tn = 0
    for material_id in sorted(ref):
        expected = ref[material_id]["labels"][dimension]
        observed = pred[material_id]["prediction"]["labels"][dimension]
        if expected == observed == 1:
            tp += 1
        elif expected == 0 and observed == 1:
            fp += 1
        elif expected == 1 and observed == 0:
            fn += 1
        else:
            tn += 1
        if expected != observed:
            differences.append({
                "material_id": material_id,
                "dimension": dimension,
                "reference": expected,
                "prediction": observed,
                "reference_reason": ref[material_id].get("reasons", {}).get(dimension),
                "prediction_evidence": [e for e in pred[material_id]["prediction"]["evidence"] if e["dimension"] == dimension],
                "prediction_exclusions": pred[material_id]["prediction"]["exclusions"],
            })
    metrics.append({"dimension": dimension, **metric(tp, fp, fn, tn)})

report = {
    "kind": "evaluation_only_after_prediction_freeze",
    "prediction_path": str(PREDICTION),
    "prediction_sha256": sha(PREDICTION),
    "reference_path": str(REFERENCE),
    "reference_sha256": sha(REFERENCE),
    "prediction_was_generated_without_reference": True,
    "metrics": metrics,
    "difference_n": len(differences),
    "differences": differences,
    "interpretation": "40条是有目的开发材料；指标仅描述同材料同手册执行。21/F和36/F按共同手册的明示关系门槛严格判0，未为匹配参照放宽。",
    "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
(HERE / "冻结预测后评估.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"difference_n": len(differences), "differences": [(x["material_id"], x["dimension"]) for x in differences], "metrics": metrics}, ensure_ascii=False))
