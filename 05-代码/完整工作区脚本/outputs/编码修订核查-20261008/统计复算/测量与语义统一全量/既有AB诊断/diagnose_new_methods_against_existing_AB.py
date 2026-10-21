#!/usr/bin/env python3
"""Diagnostic comparison of the new rule/LLM outputs with adopted old A/C.

Old C is displayed as B.  This script never loads an old machine output and
never calls statistical_core_r3.load_context.  It uses only the independently
bound A/C references, sampling design, department metadata and mathematical
functions from the adopted binding.

Default mode is a non-producing preflight.  Full points and 5000-replicate
design intervals require ``--mode execute`` and a complete, hash-bound LLM run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path("/PROJECT_ROOT")
W = ROOT / "outputs/编码修订核查-20261008"
HERE = W / "统计复算/测量与语义统一全量/既有AB诊断"
DIMS = ("S", "E", "Ec", "I", "F")
EXPECTED_MANUAL_SHA256 = "24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9"
EXPECTED_N = 4480
EXPECTED_SAMPLE_N = 240
EXPECTED_PROBABILITY_N = 180
EXPECTED_CHALLENGE_N = 60

FIXED = {
    "old_binding": {
        "path": W / "统计复算/最新机器与既有AC参照比较/actual_bindings01.json",
        "sha256": "5b5a3d3c0d24f4b24d753e4cd9b6c66c7485c4708ed2b25fc3a0de1e4920a89a",
    },
    "old_comparison_code": {
        "path": W / "统计复算/最新机器与既有AC参照比较/compare_current_to_adopted_AC01.py",
        "sha256": "152beb57406d075d1be9ef90d7b33bbedd9ff3d0a608a6e0c6a52df61ea414da",
    },
    "rule_input": {
        "path": W / "统计复算/测量与语义统一全量/规则输入4480.jsonl",
        "sha256": "0a0704613e29ca81bc35c25bcdab8c36f5b2367250562d2f5f80a73f0e71fe2d",
    },
    "rule_output": {
        "path": W / "统计复算/测量与语义统一全量/规则全量输出4480.jsonl",
        "sha256": "a15f974a30cbe3d95ff339c88a63c786cdd84fae43a4e8a530509318d7a0cc8e",
    },
    "manual": {
        "path": W / "定义溯源核查/测量与计数统一/共用编码手册.md",
        "sha256": EXPECTED_MANUAL_SHA256,
    },
    "llm_input": {
        "path": W / "LLM编码/测量与语义统一/full4480/frozen_input.jsonl",
        "sha256": "714f299f9e9c23ef3ce4fc5b14fdc5cb4122f31b3b3a046007d3498648f320f6",
    },
    "llm_prompt": {
        "path": W / "LLM编码/测量与语义统一/full4480/frozen_prompt.txt",
        "sha256": "a2263837c009c80cce84ee7e8e39f1e719cd77b92c727a790967f172eaa5ba4d",
    },
    "llm_schema": {
        "path": W / "LLM编码/测量与语义统一/full4480/frozen_schema.json",
        "sha256": "120bec39fc38ba1e234a6c5f60d4298468950fc303617b77b55651b89167a0d4",
    },
    "llm_validator": {
        "path": W / "LLM编码/测量与语义统一/full4480/frozen_validator.py",
        "sha256": "cf38105364f723972b46b6a781ea75c7c8da871bc22455c9cb002b500b6b1e8c",
    },
    "llm_runner": {
        "path": W / "LLM编码/测量与语义统一/full4480/frozen_runner.py",
        "sha256": "145815cd373725dd71beffd2ba6c492347a840da99d833129261d8b295dd6856",
    },
    "llm_plan": {
        "path": W / "LLM编码/测量与语义统一/full4480/run_plan.json",
        "sha256": "f5cda363029b7935dbab218f1c8184b32130088ad6f20420b721d22459d9059c",
    },
}

LLM_DIR = W / "LLM编码/测量与语义统一/full4480"
LLM_OUTPUT = LLM_DIR / "all_predictions.jsonl"
LLM_SUMMARY = LLM_DIR / "execution_summary.json"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_fixed(name):
    item = FIXED[name]
    path = Path(item["path"])
    require(path.is_file(), f"Missing fixed input: {name}: {path}")
    require(sha(path) == item["sha256"], f"Fixed input hash mismatch: {name}: {path}")
    return path


def check_bound(item, name):
    path = Path(item["path"])
    require(path.is_absolute() and path.is_file(), f"Missing bound file: {name}: {path}")
    require(sha(path) == item["sha256"], f"Bound file hash mismatch: {name}: {path}")
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    ordered = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [row.get("id") for row in ordered]
    require(all(isinstance(rid, str) and rid for rid in ids), f"Invalid ID in {path}")
    require(len(ids) == len(set(ids)), f"Duplicate IDs in {path}")
    return ordered, {row["id"]: row for row in ordered}


def labels_of(row):
    if isinstance(row.get("result"), dict):
        return row["result"].get("labels")
    if isinstance(row.get("prediction"), dict):
        return row["prediction"].get("labels")
    return row.get("labels")


def validate_label_rows(rows, name, expected_ids=None):
    ids = [row["id"] for row in rows]
    if expected_ids is not None:
        require(ids == list(expected_ids), f"ID count/order differs: {name}")
    for row in rows:
        labels = labels_of(row)
        require(isinstance(labels, dict) and set(labels) == set(DIMS), f"Label shape differs: {name}: {row['id']}")
        require(all(value is None or type(value) is int and value in (0, 1) for value in labels.values()),
                f"Non-binary/non-unknown label: {name}: {row['id']}")


def label_adapter(byid):
    return {rid: {"labels": labels_of(row)} for rid, row in byid.items()}


def load_fixed_and_old_bindings():
    for name in FIXED:
        check_fixed(name)
    cfg = read_json(check_fixed("old_binding"))
    # Use only independent reference/design/math/department bindings.  In
    # particular, cfg['methods'] and all old machine outputs are never read.
    refs = {"A": check_bound(cfg["references"]["A"], "old reference A"),
            "B": check_bound(cfg["references"]["C"], "old reference C displayed as B")}
    design_path = check_bound(cfg["sampling_design"], "old adopted sampling design")
    department_path = check_bound(cfg["department_metadata"], "department metadata")
    core_binding = cfg["mathematical_sources"]["statistical_core_r3"]
    core_path = check_bound(core_binding, "statistical_core_r3")
    return cfg, refs, design_path, department_path, core_path


def import_math_core(core_path):
    sys.path.insert(0, str(core_path.parent))
    core = importlib.import_module("statistical_core_r3")
    require(Path(core.__file__).resolve() == core_path.resolve(), "Unexpected statistical core import")
    require(tuple(core.DIMS) == DIMS and tuple(core.GROUPS) == ("NMPA", "NHSA", "NHC"),
            "Mathematical core dimensions/groups changed")
    require(core.B == 5000, "Old-design replication count is not 5000")
    # Allowed calls below are binary/cells/metrics/interval/replicate_factors/
    # weighting/safe.  load_context is intentionally never called.
    return core


def verify_common_manual_binding():
    manual_path = check_fixed("manual")
    prompt_path = check_fixed("llm_prompt")
    manual = manual_path.read_text(encoding="utf-8").rstrip("\n")
    prompt = prompt_path.read_text(encoding="utf-8")
    require(f"<common_manual>\n{manual}\n</common_manual>" in prompt,
            "Frozen LLM prompt does not contain the exact current manual")


def load_corpus_inputs_and_rule_output():
    rule_input_rows, rule_inputs = read_jsonl(check_fixed("rule_input"))
    llm_input_rows, llm_inputs = read_jsonl(check_fixed("llm_input"))
    rule_output_rows, rule_outputs = read_jsonl(check_fixed("rule_output"))
    require(len(rule_input_rows) == len(llm_input_rows) == len(rule_output_rows) == EXPECTED_N,
            "New corpus count differs from 4480")
    ids = [row["id"] for row in rule_input_rows]
    require([row["id"] for row in llm_input_rows] == ids, "Rule and LLM input ID order differs")
    require([row["id"] for row in rule_output_rows] == ids, "Rule output ID order differs")
    for rid in ids:
        rtext = rule_inputs[rid]["input"]["unit_text"]
        ltext = llm_inputs[rid]["text"]
        require(rtext == ltext, f"Rule/LLM current text differs: {rid}")
        result = rule_outputs[rid].get("result", {})
        require(rule_outputs[rid].get("status") == "completed", f"Rule output incomplete: {rid}")
        require(result.get("current_manual_sha256") == EXPECTED_MANUAL_SHA256,
                f"Rule output manual binding differs: {rid}")
        require(result.get("unit_text_sha256") == hashlib.sha256(rtext.encode()).hexdigest(),
                f"Rule output text binding differs: {rid}")
    validate_label_rows(rule_output_rows, "new rules", ids)
    return ids, rule_inputs, llm_inputs, rule_outputs


def llm_readiness(expected_ids):
    if not LLM_SUMMARY.is_file() or not LLM_OUTPUT.is_file():
        return {"ready": False, "reason": "execution_summary_or_all_predictions_absent",
                "execution_summary_exists": LLM_SUMMARY.is_file(), "output_exists": LLM_OUTPUT.is_file()}
    plan = read_json(check_fixed("llm_plan"))
    summary = read_json(LLM_SUMMARY)
    checks = {
        "status_complete": summary.get("status") == "complete_actual_calls_structurally_valid",
        "n_4480": summary.get("n") == EXPECTED_N,
        "accepted_all_batches": summary.get("accepted_batch_count") == summary.get("expected_batch_count") == plan.get("batch_count"),
        "recorded_all_batches": summary.get("recorded_batch_count") == plan.get("batch_count"),
        "zero_selected_tool_events": summary.get("selected_tool_event_count") == 0,
        "input_hash_bound": summary.get("input_sha256") == summary.get("source_input_current_sha256") == FIXED["llm_input"]["sha256"],
        "source_unchanged": summary.get("source_unchanged_during_run") is True,
        "prompt_hash_bound": summary.get("prompt_sha256") == FIXED["llm_prompt"]["sha256"],
        "plan_hash_bound": summary.get("plan_sha256") == FIXED["llm_plan"]["sha256"],
        "output_hash_bound": summary.get("output_sha256") == sha(LLM_OUTPUT),
        "selection_not_metric_based": summary.get("metric_or_reference_label_based_selection") is False,
        "structure_not_semantic_claim": summary.get("semantic_validity_not_proven_by_structure") is True,
    }
    if not all(checks.values()):
        return {"ready": False, "reason": "execution_summary_not_complete_or_not_bound", "checks": checks,
                "execution_summary_sha256": sha(LLM_SUMMARY)}
    llm_rows, llm_byid = read_jsonl(LLM_OUTPUT)
    validate_label_rows(llm_rows, "new LLM", expected_ids)
    require(len(llm_rows) == EXPECTED_N, "New LLM output count differs from 4480")
    return {"ready": True, "checks": checks, "summary": summary, "rows": llm_rows, "byid": llm_byid,
            "execution_summary_sha256": sha(LLM_SUMMARY), "output_sha256": sha(LLM_OUTPUT)}


def load_design_and_references(core, refs_paths, design_path, department_path, rule_inputs, expected_ids):
    design = read_json(design_path)
    sample_rows = design.get("sample", [])
    sample_ids = [row.get("original_id") for row in sample_rows]
    require(len(sample_ids) == EXPECTED_SAMPLE_N == len(set(sample_ids)), "Old sample IDs changed or duplicated")
    sample = {row["original_id"]: row for row in sample_rows}
    require(set(sample) <= set(expected_ids), "Old sample includes ID outside new 4480 corpus")
    require(design.get("frame_N_by_group") == core.EXPECTED_ELIGIBLE, "Old design frame changed")
    require(Counter((row["component"], row["group"]) for row in sample_rows) == Counter(
        {("probability_canonical", g): 60 for g in core.GROUPS}
        | {("enriched_challenge", g): 30 for g in ("NMPA", "NHSA")}), "Old sample allocation changed")
    require(sum(row["component"] == "probability_canonical" for row in sample_rows) == EXPECTED_PROBABILITY_N,
            "Probability sample is not 180")
    require(sum(row["component"] == "enriched_challenge" for row in sample_rows) == EXPECTED_CHALLENGE_N,
            "Challenge sample is not 60")

    metadata = read_json(department_path)
    meta = {Path(row["original_file"]).stem: row for row in metadata["rows"]}
    for rid, srow in sample.items():
        current = rule_inputs[rid]["input"]
        text = current["unit_text"]
        require(hashlib.sha256(text.encode()).hexdigest() == srow["unit_text_sha256"],
                f"Sample current text SHA changed: {rid}")
        require(meta[current["original_file_stem"]]["analysis_group"] == srow["group"],
                f"Sample department changed: {rid}")
        if srow["component"] == "probability_canonical":
            require(srow["sample_n"] == 60 and srow["canonical_frame_N"] == core.EXPECTED_ELIGIBLE[srow["group"]],
                    f"Probability design fields changed: {rid}")
            require(abs(srow["analysis_weight"] - srow["canonical_frame_N"] / 60) < 1e-12,
                    f"Probability weight changed: {rid}")
            require(abs(srow["inclusion_probability"] - 60 / srow["canonical_frame_N"]) < 1e-12,
                    f"Probability inclusion probability changed: {rid}")
        else:
            require(srow["analysis_weight"] is None, f"Challenge case unexpectedly population weighted: {rid}")

    refs = {}
    for display, path in refs_paths.items():
        ordered, byid = read_jsonl(path)
        require(set(byid) == set(sample), f"Old reference {display} sample IDs differ")
        validate_label_rows(ordered, f"old reference {display}")
        for rid in sample:
            provenance = byid[rid].get("annotation_provenance", {}).get("effective", {})
            require(provenance.get("unit_text_sha256") == sample[rid]["unit_text_sha256"],
                    f"Old reference {display} text binding differs: {rid}")
        refs[display] = label_adapter(byid)
    return design, sample, refs


def metric_record(core, ctx, ids, component, group, comparison, left, right, left_name, right_name,
                  right_binding, factor_cache):
    weighting = "eligible_design_weighted" if component == "probability_canonical" else "unweighted"
    weights = core.weighting(ctx, ids, weighting)
    mechanism = "department_unit_rescaled_SRSWOR" if component == "probability_canonical" else "department_unit_conditional_WR"
    cache_key = (component, group, mechanism, tuple(ids))
    if cache_key not in factor_cache:
        factor_cache[cache_key] = core.replicate_factors(ctx, ids, component, mechanism)
    factors = factor_cache[cache_key]
    records = []
    for dim in DIMS:
        matrix, valid = core.cells(left, right, dim, ids)
        raw = matrix.sum(axis=0).astype(int)
        weighted = weights @ matrix
        point = core.metrics(weighted)[0]
        boot = core.metrics((factors * weights[None, :]) @ matrix)
        metric_values = {}
        for metric in ("kappa", "precision", "recall", "f1"):
            index = core.METRIC_NAMES.index(metric)
            metric_values[metric] = {
                "estimate": core.safe(point[index]),
                "ci95_5000_old_design": core.interval(boot[:, index]),
            }
        records.append({
            "component": component,
            "group": group,
            "weighting": weighting,
            "bootstrap_mechanism": mechanism,
            "bootstrap_repetitions": core.B,
            "comparison": comparison,
            "left": left_name,
            "right_reference_display": right_name,
            "right_reference_binding": right_binding,
            "dimension": dim,
            "unit_n": len(ids),
            "paired_n": int(valid.sum()),
            "unknown_pairwise_n": int((~valid).sum()),
            "unknown_pairwise_ids": [rid for rid, ok in zip(ids, valid) if not ok],
            "cell_order": ["11", "10", "01", "00"],
            "raw_cells": {"11": int(raw[0]), "10": int(raw[1]), "01": int(raw[2]), "00": int(raw[3])},
            "weighted_cells": {"11": float(weighted[0]), "10": float(weighted[1]),
                               "01": float(weighted[2]), "00": float(weighted[3])},
            "metrics": metric_values,
            "zero_denominator": "NA represented as JSON null and CSV NA",
            "unknown_policy": "dimension-specific pairwise exclusion; unknown is never replaced by 0",
        })
    return records


def write_outputs(records, provenance):
    result_path = HERE / "新规则LLM-既有AB诊断-点估计与5000次区间.json"
    csv_path = HERE / "新规则LLM-既有AB诊断-指标长表.csv"
    completion_path = HERE / "新规则LLM-既有AB诊断-执行清单.json"
    result = {
        "status": "diagnostic_completed_against_existing_post_reviewed_A_B",
        "interpretation": "共同手册变更后的诊断比较；旧 A/B 不是新手册独立参照，本结果不是新验证。",
        "reference_display": {"A": "old binding A", "B": "old binding C displayed as B"},
        "directional_metrics": "机器比较以旧参照为 right；A-B 中 A 为 left、B 为 right。P/R/F1 因此有方向，κ对称。",
        "probability_component": "概率180与挑战60分开；概率总体按原 N_h/60 权重，部门内同一常数权重。",
        "challenge_component": "挑战60为条件性富集样本，不作总体患病率或总体性能外推。",
        "uncertainty": "5000次区间沿用旧设计数学核，条件于固定标签、材料和既有参照，不覆盖手册兼容性或语义真值不确定性。",
        "provenance": provenance,
        "records": records,
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    fields = ["component", "group", "comparison", "left", "right_reference_display", "right_reference_binding",
              "dimension", "unit_n", "paired_n", "unknown_pairwise_n", "n11", "n10", "n01", "n00",
              "weighted11", "weighted10", "weighted01", "weighted00", "kappa", "kappa_low", "kappa_high",
              "precision", "precision_low", "precision_high", "recall", "recall_low", "recall_high",
              "f1", "f1_low", "f1_high", "bootstrap_repetitions", "bootstrap_mechanism", "weighting"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rec in records:
            row = {key: rec.get(key) for key in fields}
            row.update({"n" + key: value for key, value in rec["raw_cells"].items()})
            row.update({"weighted" + key: value for key, value in rec["weighted_cells"].items()})
            for metric in ("kappa", "precision", "recall", "f1"):
                row[metric] = rec["metrics"][metric]["estimate"]
                row[metric + "_low"] = rec["metrics"][metric]["ci95_5000_old_design"]["low"]
                row[metric + "_high"] = rec["metrics"][metric]["ci95_5000_old_design"]["high"]
            writer.writerow({key: "NA" if row.get(key) is None else row.get(key) for key in fields})
    completion = {
        "status": "complete",
        "result_sha256": sha(result_path),
        "csv_sha256": sha(csv_path),
        "script_sha256": sha(Path(__file__)),
        "input_hashes": provenance["input_hashes"],
        "model_calls": 0,
        "labels_modified": False,
        "not_new_validation": True,
    }
    completion_path.write_text(json.dumps(completion, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result_path, csv_path, completion_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "execute"), default="preflight")
    args = parser.parse_args()

    cfg, ref_paths, design_path, department_path, core_path = load_fixed_and_old_bindings()
    core = import_math_core(core_path)
    verify_common_manual_binding()
    ids, rule_inputs, llm_inputs, rule_outputs = load_corpus_inputs_and_rule_output()
    design, sample, refs = load_design_and_references(core, ref_paths, design_path, department_path,
                                                      rule_inputs, ids)
    readiness = llm_readiness(ids)
    preflight = {
        "status": "ready_for_execution" if readiness["ready"] else "waiting_for_complete_llm_output",
        "fixed_inputs_verified": True,
        "rule_output_verified_n": len(rule_outputs),
        "corpus_text_and_id_order_verified_n": len(ids),
        "sample_ids_text_sha_and_department_verified_n": len(sample),
        "sample_counts": {"probability": EXPECTED_PROBABILITY_N, "challenge": EXPECTED_CHALLENGE_N},
        "llm_readiness": {key: value for key, value in readiness.items() if key not in {"rows", "byid", "summary"}},
        "old_machine_outputs_loaded": False,
        "statistical_core_load_context_called": False,
        "results_produced": False,
    }
    if args.mode == "preflight":
        print(json.dumps(preflight, ensure_ascii=False, indent=2))
        return
    require(readiness["ready"], "LLM execution is absent, incomplete, or not hash-bound; refusing diagnosis")

    new_rule = label_adapter(rule_outputs)
    new_llm = label_adapter(readiness["byid"])
    comparisons = [
        ("new_rule_vs_old_A", new_rule, refs["A"], "new_rule", "old_A", "A"),
        ("new_rule_vs_old_B", new_rule, refs["B"], "new_rule", "old_B", "C displayed as B"),
        ("new_LLM_vs_old_A", new_llm, refs["A"], "new_LLM", "old_A", "A"),
        ("new_LLM_vs_old_B", new_llm, refs["B"], "new_LLM", "old_B", "C displayed as B"),
        ("old_A_vs_old_B", refs["A"], refs["B"], "old_A", "old_B", "C displayed as B"),
    ]
    records = []
    factor_cache = {}
    ctx = {"sample": sample}
    for component in ("probability_canonical", "enriched_challenge"):
        component_ids = sorted(rid for rid, row in sample.items() if row["component"] == component)
        groups = ("ALL",) + tuple(group for group in core.GROUPS
                                   if any(sample[rid]["group"] == group for rid in component_ids))
        for group in groups:
            selected = [rid for rid in component_ids if group == "ALL" or sample[rid]["group"] == group]
            require(selected, f"Empty requested analysis cell: {component}: {group}")
            for comparison, left, right, left_name, right_name, right_binding in comparisons:
                records.extend(metric_record(core, ctx, selected, component, group, comparison,
                                             left, right, left_name, right_name, right_binding, factor_cache))

    expected_record_n = (4 * 5 * len(DIMS)) + (3 * 5 * len(DIMS))
    require(len(records) == expected_record_n == 175, "Unexpected diagnostic record count")
    input_hashes = {name: sha(item["path"]) for name, item in FIXED.items()}
    input_hashes.update({
        "old_reference_A": sha(ref_paths["A"]),
        "old_reference_B_binding_C": sha(ref_paths["B"]),
        "old_sampling_design": sha(design_path),
        "department_metadata": sha(department_path),
        "statistical_core_r3": sha(core_path),
        "llm_execution_summary": readiness["execution_summary_sha256"],
        "llm_output": readiness["output_sha256"],
    })
    provenance = {
        "input_hashes": input_hashes,
        "manual_sha256": EXPECTED_MANUAL_SHA256,
        "llm_execution_summary": readiness["summary"],
        "sample_id_text_department_checks": "passed",
        "pairwise_unknown_policy": "per dimension and comparison; excluded only from that pair; never imputed as 0",
        "mathematical_core_functions_used": ["cells", "metrics", "interval", "replicate_factors", "weighting", "safe"],
        "mathematical_core_load_context_used": False,
        "old_machine_outputs_loaded": False,
        "old_reference_role": "diagnostic comparator after common-manual change; not a new validation reference",
    }
    paths = write_outputs(records, provenance)
    print(json.dumps({"status": "completed", "record_n": len(records),
                      "outputs": {path.name: sha(path) for path in paths}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
