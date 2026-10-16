"""Post-run diagnostics against current saved posthoc references; no inference."""
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
RULE = ROOT / "06-coding/rule-v18-overall-health-boundary-development-root"
RUN = RULE / "run77-first"
OUT = ROOT / "07-statistics/rule-v18-current-posthoc-reference-root"


def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


seal = json.loads((RUN / "seal.json").read_text())
checked = 0
for key in ("implementation_files", "material_bindings", "control_inputs", "output_files"):
    for expected in seal[key]:
        actual = bind(expected["path"])
        assert actual == expected
        checked += 1
execution = json.loads((RUN / "execution.json").read_text())
assert execution["actual_record_N"] == 77 and execution["actual_dimension_N"] == 385
assert execution["technical_failure_dimension_N"] == execution["lawful_null_N"] == 0
predictions = [json.loads(line) for line in (RUN / "predictions.jsonl").read_text().splitlines()]
assert len(predictions) == len({row["id"] for row in predictions}) == 77
reference_paths = [ROOT / "09-delivery/agent-review-20261010" / name
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
    references.append(reference)
assert references[0] == references[1]
reference = references[0]
math_path = ROOT / "scripts/verify_native_v16_campaign.py"
spec = importlib.util.spec_from_file_location("native_v16_math", math_path)
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
old_path = ROOT / "06-coding/rule-v17-bounded-role-merge-development-sol/run77-first/predictions.jsonl"
old = {row["id"]: row for row in [json.loads(line) for line in old_path.read_text().splitlines()]}
changed = [{"id": row["id"], "dimension": dim, "old": old[row["id"]]["labels"][dim], "new": value}
           for row in predictions for dim, value in row["labels"].items() if value != old[row["id"]]["labels"][dim]]
report = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "reference_identity": "Current delivered AI-seeded A/B with targeted human posthoc corrections; not independent human initial coding",
    "reference_bindings": [bind(path) for path in reference_paths],
    "prediction_binding": bind(RUN / "predictions.jsonl"), "old_prediction_binding": bind(old_path),
    "run_seal_binding": bind(RUN / "seal.json"), "verified_binding_N": checked,
    "calculation_script_binding": bind(__file__), "formula_script_binding": bind(math_path),
    "assigned_records_N": 77, "actual_complete_records_N": 77, "actual_binary_slots_N": 385,
    "technical_failure_slots_N": 0, "semantic_null_slots_N": 0,
    "dimensions": dimensions, "binary_disagreements": differences,
    "changed_dimensions_vs_old_v17": changed,
    "sklearn_crosscheck": {"version": sklearn.__version__, "interpreter": sys.executable,
                           "five_dimensions": crosschecks, "all_passed": True},
    "formal_acceptance": False, "human_independent_coding_reliability": False,
    "population_CI95_calculated": False, "p_values_calculated": False,
    "raw_first_predictions_modified": False, "thresholds_changed": False,
}
OUT.mkdir(exist_ok=False)
with (OUT / "metrics.json").open("x") as stream:
    stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
all_pass = all(all(item["point_targets"].values()) for item in dimensions.values())
summary = ("规则v18已完整重跑77条开发材料、385项判断，无失败或待定。\n"
           f"五维四项点指标全部达到项目0.8目标：{all_pass}。分歧维度数：{len(differences)}。\n"
           "本结果是开发校准，不是独立人类编码信度或总体效度证明。未计算总体置信区间或编码合格p值。\n"
           "与旧v17变化：" + json.dumps(changed, ensure_ascii=False) + "\n")
with (OUT / "说明.txt").open("x") as stream:
    stream.write(summary)
with (OUT / "seal.json").open("x") as stream:
    stream.write(json.dumps({"members": [bind(OUT / "metrics.json"), bind(OUT / "说明.txt")]}, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"binding_checks": checked, "sklearn": sklearn.__version__,
                  "metrics": {key: value["metrics"] for key, value in dimensions.items()},
                  "changed": changed, "differences": differences, "formal_acceptance": False}, ensure_ascii=False))
