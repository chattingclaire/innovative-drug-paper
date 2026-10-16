"""Post-run development diagnostics; never invokes or edits a coder."""
import hashlib
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import sklearn
from sklearn.metrics import cohen_kappa_score, confusion_matrix, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[1]
RUN = Path(sys.argv[1]).resolve()
OUT = ROOT / "07-statistics/rule-v19-v15-human4-reference-root"


def binding(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


seal = json.loads((RUN / "seal.json").read_text())
checked = 0
for key in ("implementation_files", "material_bindings", "control_inputs", "output_files"):
    for item in seal[key]:
        actual = binding(item["path"])
        assert actual["sha256"] == item["sha256"] and actual["bytes"] == item["bytes"]
        checked += 1
execution = json.loads((RUN / "execution.json").read_text())
assert execution["actual_record_N"] == 77 and execution["actual_dimension_N"] == 385
assert execution["technical_failure_dimension_N"] == execution["lawful_null_N"] == 0
predictions = [json.loads(line) for line in (RUN / "predictions.jsonl").read_text().splitlines()]
assert len(predictions) == len({row["id"] for row in predictions}) == 77
assert all(type(value) is int and value in (0, 1) for row in predictions for value in row["labels"].values())
reference_paths = [ROOT / "09-delivery/agent-review-20261010/真人4项复核后-v2" / name
                   for name in ("编码复核表-A.xlsx", "编码复核表-B.xlsx")]
references = []
for path in reference_paths:
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    reference = {}
    for row in book["编码表"].iter_rows(min_row=7, max_row=391, values_only=True):
        sid, dept, dimension, value = row[:4]
        dimension = dimension.split()[0]
        assert type(value) is int and value in (0, 1)
        target = reference.setdefault(sid, {"department": dept, "labels": {}})
        assert dimension not in target["labels"]
        target["labels"][dimension] = value
    book.close()
    references.append(reference)
assert references[0] == references[1]
reference = references[0]
assert set(reference) == {row["id"] for row in predictions}
math_path = ROOT / "scripts/verify_native_v16_campaign.py"
spec = importlib.util.spec_from_file_location("audited_exact_fraction_math", math_path)
formula = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formula)
dimensions, differences = formula.calculate(predictions, reference)
crosschecks = []
for dimension, result in dimensions.items():
    predicted = [row["labels"][dimension] for row in predictions]
    truth = [reference[row["id"]]["labels"][dimension] for row in predictions]
    kappa = cohen_kappa_score(truth, predicted)
    precision, recall, f1, _ = precision_recall_fscore_support(truth, predicted, average="binary", zero_division=0)
    values = {"kappa": float(kappa), "precision": float(precision), "recall": float(recall), "F1": float(f1)}
    for name, value in values.items():
        assert math.isclose(value, result["metrics"][name], abs_tol=1e-12)
    tn, fp, fn, tp = confusion_matrix(truth, predicted, labels=[0, 1]).ravel()
    assert {"TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int(tn)} == result["four_cells"]
    crosschecks.append({"dimension": dimension, "metrics": values, "cells_matched": True})
old_path = ROOT / "06-coding/rule-v18-overall-health-boundary-development-root/run77-first/predictions.jsonl"
old = {row["id"]: row for row in [json.loads(line) for line in old_path.read_text().splitlines()]}
changed = [{"id": row["id"], "dimension": dim, "old": old[row["id"]]["labels"][dim], "new": value}
           for row in predictions for dim, value in row["labels"].items() if value != old[row["id"]]["labels"][dim]]
report = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "77 previously developed records, 385 slots; common v15 materials and human4 clarification candidate",
    "reference_identity": "AI-seeded A/B plus targeted human posthoc corrections, not independent human initial coding",
    "reference_bindings": [binding(path) for path in reference_paths],
    "prediction_binding": binding(RUN / "predictions.jsonl"),
    "old_prediction_binding": binding(old_path),
    "run_seal_binding": binding(RUN / "seal.json"), "verified_binding_N": checked,
    "calculation_script_binding": binding(__file__), "formula_script_binding": binding(math_path),
    "assigned_records_N": 77, "actual_complete_records_N": 77, "actual_binary_slots_N": 385,
    "technical_failure_slots_N": 0, "semantic_null_slots_N": 0,
    "dimensions": dimensions, "binary_disagreements": differences,
    "changes_vs_old_rule_v18": changed,
    "changes_are_joint_manual_source_rule_release_not_isolated_code_effect": True,
    "sklearn_crosscheck": {"version": sklearn.__version__, "interpreter": sys.executable,
                           "five_dimensions": crosschecks, "all_passed": True},
    "all_core_point_targets_pass": all(all(item["point_targets"].values()) for item in dimensions.values()),
    "formal_acceptance": False, "human_independent_coding_reliability": False,
    "population_CI95_calculated": False, "p_values_calculated": False,
    "raw_first_predictions_modified": False, "thresholds_changed": False,
}
OUT.mkdir(exist_ok=False)
with (OUT / "metrics.json").open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
lines = ["新版规则77条开发回归：与真人事后补核参照v2比较", "完整运行77条、385项；技术失败0，语义待定0。",
         "维度\tTP/FP/FN/TN\tκ\tPrecision\tRecall\tF1"]
for dim, item in dimensions.items():
    c, m = item["four_cells"], item["metrics"]
    lines.append(f"{dim}\t{c['TP']}/{c['FP']}/{c['FN']}/{c['TN']}\t{m['kappa']:.9f}\t{m['precision']:.9f}\t{m['recall']:.9f}\t{m['F1']:.9f}")
lines.extend([f"五维四项点指标均达到项目0.8要求：{report['all_core_point_targets_pass']}。",
              f"与当前参照的二元分歧：{len(differences)}。", "与旧v18变化：" + json.dumps(changed, ensure_ascii=False),
              "这是已用于规则修订的77条开发回归，不能替代未参与开发材料上的独立验证。",
              "手册澄清、同版完整补材与规则同步变更，不能把变化全部归因于代码单独效果。",
              "未计算总体95%区间、p值或真人独立编码信度；未完成全量4481编码。"])
with (OUT / "结果说明.txt").open("x", encoding="utf-8") as stream:
    stream.write("\n".join(lines) + "\n")
with (OUT / "seal.json").open("x", encoding="utf-8") as stream:
    json.dump({"members": [binding(OUT / "metrics.json"), binding(OUT / "结果说明.txt")],
               "formal_acceptance": False}, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"binding_checks": checked, "metrics": {k: v["metrics"] for k, v in dimensions.items()},
                  "changed": changed, "differences": differences, "formal_acceptance": False}, ensure_ascii=False))
