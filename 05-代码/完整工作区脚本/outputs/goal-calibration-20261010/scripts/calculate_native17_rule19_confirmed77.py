"""Compare saved development outputs only after all 13 whole batches are sealed."""
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import openpyxl
import sklearn
from sklearn.metrics import cohen_kappa_score, confusion_matrix, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "06-coding/native-llm77-v17-sol"
RULE = ROOT / "06-coding/rule-v19-v15-development77-first-sol/versions/v4/run77-first"
OUT = ROOT / "07-statistics/native-v17-rule-v19-human-confirmed77-root"
DIMS = ("S", "E", "Ec", "I", "F")


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def exclusive_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    manifest = json.loads((NATIVE / "run-manifest.json").read_text())
    # This check happens before any prediction labels or reference file is opened.
    selections = [NATIVE / f"batch-{i:04d}/root-selection.json" for i in range(1, 14)]
    if not all(path.is_file() for path in selections):
        raise RuntimeError("All 13 terminal valid whole-batch selections must exist before comparison.")
    validator = module(NATIVE / "validate-structured-batch.py", "frozen_native17_validator")
    assert binding(NATIVE / "validate-structured-batch.py")["sha256"] == "456c4b51084ba47f6234cec29452242aa6644336d454e7166dac3eb5ecd78f8f"
    native, raw_bindings = [], []
    for index, path in enumerate(selections, 1):
        selection = validator.load_strict(path)
        original = selection["original_whole_batch_first"]
        validator.check_binding(original)
        validator.check_binding(selection["canonical_whole_byte_mirror"])
        assert original["sha256"] == selection["canonical_whole_byte_mirror"]["sha256"]
        directory = path.parent
        validator.verify(directory / "assignment.json", original["path"])
        first = validator.load_strict(original["path"])
        for position, row in enumerate(first["records"]):
            native.append({"id": row["source_id"], "labels": {dim: row["dimensions"][dim]["value"] for dim in DIMS},
                           "derived_record_is_original_response": False,
                           "original_whole_batch_submission": original, "record_pointer": f"/records/{position}"})
        raw_bindings.append({"selection": binding(path), "original": original,
                             "assignment": binding(directory / "assignment.json")})
    assert [row["id"] for row in native] == manifest["global_order"]
    assert len(native) == len({row["id"] for row in native}) == 77
    for row in native:
        assert all(value is None or type(value) is int and value in (0, 1) for value in row["labels"].values())

    rule_seal = json.loads((RULE / "seal.json").read_text())
    for key in ("implementation_files", "material_bindings", "control_inputs", "output_files"):
        for item in rule_seal[key]:
            validator.check_binding(item)
    rules = [json.loads(line) for line in (RULE / "predictions.jsonl").read_text().splitlines()]
    assert len(rules) == 77 and {row["id"] for row in rules} == {row["id"] for row in native}
    assert all(type(value) is int and value in (0, 1) for row in rules for value in row["labels"].values())
    human_paths = [ROOT / "09-delivery/agent-review-20261010/真人4项复核后-v2" / f"编码复核表-{letter}.xlsx" for letter in ("A", "B")]
    declaration_path = ROOT / "logs/user-current77-AB-independent-human-identity-confirmed-20261010.json"
    declaration = json.loads(declaration_path.read_text())
    assert [binding(path) for path in human_paths] == declaration["files"]
    references = []
    for path in human_paths:
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
        reference = {}
        for row in book["编码表"].iter_rows(min_row=7, max_row=391, values_only=True):
            sid, department, dimension, value = row[:4]
            dimension = dimension.split()[0]
            assert dimension in DIMS and type(value) is int and value in (0, 1)
            entry = reference.setdefault(sid, {"department": department, "labels": {}})
            assert dimension not in entry["labels"]
            entry["labels"][dimension] = value
        book.close()
        assert set(reference) == {row["id"] for row in native}
        assert all(set(row["labels"]) == set(DIMS) for row in reference.values())
        references.append(reference)
    assert references[0] == references[1]
    formula_path = ROOT / "scripts/verify_native_v16_campaign.py"
    formula = module(formula_path, "audited_fraction_development_math")
    human_b = [{"id": sid, "labels": row["labels"]} for sid, row in references[1].items()]
    machine_rule_reference = {row["id"]: row for row in rules}
    pairs = {"LLM_vs_confirmed_reference": (native, references[0]),
             "rule_vs_confirmed_reference": (rules, references[0]),
             "saved_A_vs_B": (human_b, references[0]),
             "LLM_vs_rule_diagnostic_only": (native, machine_rule_reference)}
    results = {}
    for name, (predictions, reference) in pairs.items():
        dimensions, disagreements = formula.calculate(predictions, reference)
        checked = []
        for dim, item in dimensions.items():
            joint = [row for row in predictions if row["labels"][dim] is not None and reference[row["id"]]["labels"][dim] is not None]
            truth = [reference[row["id"]]["labels"][dim] for row in joint]
            predicted = [row["labels"][dim] for row in joint]
            if not joint:
                checked.append({"dimension": dim, "joint_binary_N": 0, "NA_retained": True})
                continue
            kappa = cohen_kappa_score(truth, predicted)
            precision, recall, f1, _ = precision_recall_fscore_support(truth, predicted, average="binary", zero_division=0)
            for key, value in {"kappa": kappa, "precision": precision, "recall": recall, "F1": f1}.items():
                expected = item["metrics"][key]
                if expected is not None:
                    assert math.isclose(float(value), expected, abs_tol=1e-12)
            tn, fp, fn, tp = confusion_matrix(truth, predicted, labels=[0, 1]).ravel()
            assert {"TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int(tn)} == item["four_cells"]
            checked.append({"dimension": dim, "joint_binary_N": len(joint), "defined_core_metrics_and_four_cells_match": True})
        results[name] = {"dimensions": dimensions, "binary_disagreements": disagreements, "sklearn_crosscheck": checked}
    OUT.mkdir(exist_ok=False)
    with (OUT / "derived-native-predictions.jsonl").open("x", encoding="utf-8") as stream:
        for row in native:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {"created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "one exposed development77 campaign; 13 batch contexts, not repeats or held-out formal validation",
              "assigned_records_N": 77, "saved_records_N": 77, "assigned_slots_N": 385,
              "LLM_binary_slots_N": sum(v is not None for row in native for v in row["labels"].values()),
              "LLM_semantic_null_slots_N": sum(v is None for row in native for v in row["labels"].values()),
              "LLM_terminal_failed_batches_N": 0, "all_13_whole_batches_selected_before_comparison": True,
              "reference_identity": "Current A/B results confirmed by user as independent human coding; existing assembly/reason authorship and revision history retained.",
              "reference_identity_receipt": binding(declaration_path), "reference_bindings": [binding(path) for path in human_paths],
              "native_run_manifest": binding(NATIVE / "run-manifest.json"), "native_raw_batch_bindings": raw_bindings,
              "rule_run_seal": binding(RULE / "seal.json"), "rule_predictions": binding(RULE / "predictions.jsonl"),
              "manual": manifest["manual"], "execution_prompt": manifest["execution_prompt"], "source_jsonl": manifest["source_jsonl"],
              "calculation_script": binding(__file__), "formula_script": binding(formula_path), "sklearn_version": sklearn.__version__,
              "comparisons": results, "population_CI95_calculated": False, "p_values_calculated": False,
              "formal_acceptance": False, "independent_heldout_accuracy_validation": False,
              "saved_AB_agreement_is_not_proof_of_unrecorded_prediscussion_history": True,
              "raw_first_modified": False, "thresholds_changed": False}
    exclusive_json(OUT / "metrics.json", report)
    lines = ["新版LLM与规则：77条开发校准配套报告", "13批合计一次77条运行；全部整批首答封存后才比较。", "参照：用户确认的当前77条真人A/B结果。材料已用于开发，报告不作未参与调规则材料的验证或总体推断。", "方法\t维度\tTP/FP/FN/TN\tκ\tPrecision\tRecall\tF1"]
    for name in ("LLM_vs_confirmed_reference", "rule_vs_confirmed_reference"):
        for dim, item in results[name]["dimensions"].items():
            cells, metrics = item["four_cells"], item["metrics"]
            values = ["NA" if metrics[key] is None else f"{metrics[key]:.6f}" for key in ("kappa", "precision", "recall", "F1")]
            lines.append("\t".join([name, dim, "/".join(str(cells[k]) for k in ("TP", "FP", "FN", "TN")), *values]))
    lines += [f"LLM二元有效项：{report['LLM_binary_slots_N']}/385；语义待定：{report['LLM_semantic_null_slots_N']}；整批终末失败：0。", "完整JSON同时报告观察/机会一致率、正负类一致性、特异度、负预测值、逐维正负数、分歧条款及保存A/B的一致性。", "未计算总体95%区间或p值；未执行本轮独立重复、正式验证或4481条全量重编码。"]
    with (OUT / "结果说明.txt").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    exclusive_json(OUT / "seal.json", {"members": [binding(OUT / name) for name in ("metrics.json", "derived-native-predictions.jsonl", "结果说明.txt")], "formal_acceptance": False})
    print(json.dumps({"output": str(OUT), "binary_slots_N": report["LLM_binary_slots_N"], "core": {name: {dim: row["metrics"] for dim, row in result["dimensions"].items()} for name, result in results.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
