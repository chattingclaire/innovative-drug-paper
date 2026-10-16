from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / "校准17裁定后参照40条.jsonl"
PREDICTION = HERE / "40条规则实际输出-dc26-relation-candidate-04.jsonl"
OUTPUT = HERE / "冻结预测后评估-dc26-relation-candidate-04.json"
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
    return {
        "n": n,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "kappa": kappa,
        "precision": precision,
        "recall": recall,
        "F1": f1,
    }


assert not OUTPUT.exists(), f"preserve existing actual evaluation: {OUTPUT.name}"
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
                "prediction_evidence": [
                    item for item in pred[material_id]["prediction"]["evidence"]
                    if item["dimension"] == dimension
                ],
                "prediction_exclusions": pred[material_id]["prediction"]["exclusions"],
            })
    metrics.append({"dimension": dimension, **metric(tp, fp, fn, tn)})

report = {
    "kind": "evaluation_only_after_candidate04_prediction_freeze",
    "development_status": "continued_development_not_independent_validation",
    "prediction_path": str(PREDICTION),
    "prediction_sha256": sha(PREDICTION),
    "reference_path": str(REFERENCE),
    "reference_sha256": sha(REFERENCE),
    "reference_note": "校准17裁定后同一参照；相对原40参照仅校准17/F由0改1，不是独立A/B新初判。",
    "prediction_was_generated_without_reference_file": True,
    "developer_knew_candidate17_adjudication_before_candidate04": True,
    "developer_had_seen_candidate03_evaluation_and_semantic_audits_before_candidate04": True,
    "metrics": metrics,
    "difference_n": len(differences),
    "differences": differences,
    "interpretation": (
        "候选04是同材料、同手册的继续开发结果。它在候选03基础上加入保障资源按需要排序、"
        "基本保障限制与补充目录机会、以及需求评估规则明确承接到跨层级药品供给配置的通用关系；"
        "不能作为独立验证或总体效度估计。"
    ),
    "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({
    "difference_n": len(differences),
    "differences": [(item["material_id"], item["dimension"]) for item in differences],
    "metrics": metrics,
}, ensure_ascii=False))
