#!/usr/bin/env python3
"""Prepare the existing-A/B diagnostic for one actual full4480 rule run.

The frozen run-01 diagnostic implementation remains byte-identical in the
sibling ``既有AB诊断准备`` directory.  This wrapper reuses its mathematical
core and output format, replaces only current-bundle validation, and requires
an explicit separate output directory.  Runtime-freeze semantics are not
guessed here; the bound freeze file will be validated against its actual
contract after the new full run exists and before execution.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
FROZEN_SCRIPT = (HERE.parent / "既有AB诊断准备" /
                 "diagnose_final_methods_against_existing_AB.py")
FROZEN_SCRIPT_SHA256 = "b8f0da309dac992b2dbc6a15e9e317b0b26a0eb45330728091a30565ada995d9"


def load_frozen():
    spec = importlib.util.spec_from_file_location("frozen_existing_ab_diagnostic", FROZEN_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load frozen run-01 diagnostic")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.require(module.sha256_file(FROZEN_SCRIPT) == FROZEN_SCRIPT_SHA256,
                   "Frozen run-01 diagnostic script hash differs")
    return module


m = load_frozen()


def validate_single_full_bundle(bundle_path, expected_bundle_sha):
    m.require(m.sha256_file(bundle_path) == expected_bundle_sha,
              "Current bundle manifest hash mismatch")
    bundle = m.read_json(bundle_path)
    m.require(bundle.get("status") == "complete_same_material_current_methods_bound_not_human_validated",
              "Current bundle is not complete")
    m.require(bundle.get("target_n") == 4481 and bundle.get("executed_n") == 4480,
              "Current bundle target/execution counts differ")
    m.require(bundle.get("label_or_metric_based_selection") is False
              and bundle.get("new_independent_human_validation") is False,
              "Bundle selection/validation claims differ")
    m.require(bundle.get("original_references_and_formal_paper_edited") is False,
              "Bundle reports edits to protected references or paper")
    m.require(bundle.get("rule_patch_ids") == []
              and bundle.get("rule_execution_scope") == "single_complete_actual_full4480_run",
              "Rule bundle is not the explicit single-complete-full4480 branch")
    forbidden = ("rule_base_output", "rule_base_execution", "rule_patch_input",
                 "rule_patch_output", "rule_patch_report", "rule_patch_freeze",
                 "rule_patch_scope", "rule_patch_delivery", "rule_lineage",
                 "unchanged_rule_rows_n")
    m.require(not any(key in bundle for key in forbidden),
              "Single full rule bundle contains patch-composition fields")

    critical = {}
    for key in ("frame", "rule_input", "llm_input", "rule_output", "rule_execution",
                "rule_runtime_freeze", "llm_output", "llm_lineage", "source_correction",
                "complete_original_llm_execution_QA", "one_row_actual_execution",
                "assembly_code"):
        critical[key] = m.bind(bundle[key], key)
    for name, binding in bundle.get("source_bindings", {}).items():
        m.bind(binding, "bundle source: " + name)

    frame_rows, frame_by_id = m.read_jsonl(critical["frame"])
    rule_input_rows, rule_input_by_id = m.read_jsonl(critical["rule_input"])
    llm_input_rows, llm_input_by_id = m.read_jsonl(critical["llm_input"])
    rule_rows, rule_by_id, _ = m.read_jsonl_raw_lines(critical["rule_output"])
    llm_rows, llm_by_id = m.read_jsonl(critical["llm_output"])
    lineage_rows, lineage_by_id = m.read_jsonl(critical["llm_lineage"])
    frame_ids = [row["id"] for row in frame_rows]
    executed_ids = [row["id"] for row in rule_input_rows]
    m.require(len(frame_rows) == bundle["target_n"] and len(executed_ids) == bundle["executed_n"],
              "Bundle counts do not match bound files")
    m.require([row["id"] for row in llm_input_rows] == executed_ids
              and [row["id"] for row in rule_rows] == executed_ids
              and [row["id"] for row in llm_rows] == executed_ids
              and [row["id"] for row in lineage_rows] == executed_ids,
              "Current executable ID order differs between bundle files")
    executed_set = set(executed_ids)
    m.require([rid for rid in frame_ids if rid not in executed_set]
              == bundle["known_source_unknown_ids"],
              "4481 target-frame remainder differs from known source-unknown IDs")

    execution = m.read_json(critical["rule_execution"])
    runtime_freeze = m.read_json(critical["rule_runtime_freeze"])
    expected_execution_keys = {
        "kind", "n", "status_counts", "n_undetermined", "input_sha256",
        "output_path", "output_sha256", "manual_sha256", "entry_VERSION",
        "runtime_before", "runtime_after", "runtime_before_tree_sha256",
        "runtime_after_tree_sha256", "runtime_unchanged", "elapsed_seconds",
        "no_model_run", "no_human_labels_or_metrics_used",
    }
    m.require(expected_execution_keys <= set(execution),
              "NF3 rule execution summary lacks actual executor fields")
    counts = execution.get("status_counts")
    m.require(isinstance(counts, dict)
              and execution.get("n") == bundle["executed_n"]
              and counts.get("completed") == bundle["executed_n"]
              and sum(counts.values()) == bundle["executed_n"]
              and counts.get("failed", 0) == 0
              and isinstance(execution.get("n_undetermined"), int)
              and 0 <= execution["n_undetermined"] <= bundle["executed_n"]
              and execution.get("input_sha256") == m.sha256_file(critical["rule_input"])
              and execution.get("output_sha256") == m.sha256_file(critical["rule_output"])
              and Path(execution["output_path"]).resolve() == critical["rule_output"].resolve()
              and execution.get("manual_sha256") == bundle["manual_sha256"]
              and execution.get("runtime_unchanged") is True
              and execution.get("no_model_run") is True
              and execution.get("no_human_labels_or_metrics_used") is True,
              "NF3 rule execution summary differs")

    fixed_path = m.bind(bundle["rule_runtime_fixed_record"], "NF3 fixed runtime record")
    fixed = m.read_json(fixed_path)
    runtime_path = Path(bundle.get("rule_runtime_dir", ""))
    m.require(runtime_path.is_absolute() and runtime_path.is_dir()
              and runtime_path.resolve() == Path(fixed.get("runtime_path", "")).resolve(),
              "NF3 explicit runtime directory differs from fixed record")
    runtime_before = execution["runtime_before"]
    runtime_after = execution["runtime_after"]
    m.require(isinstance(runtime_before, dict) and runtime_before
              and isinstance(runtime_after, dict)
              and runtime_before == runtime_after
              and runtime_before == fixed.get("runtime_all_files_sha256"),
              "NF3 all-runtime before/after map differs from fixed record")
    for relative, expected_sha in runtime_before.items():
        relative_path = Path(relative)
        m.require(not relative_path.is_absolute() and ".." not in relative_path.parts,
                  "NF3 runtime manifest contains a non-relative member")
        m.verify_nested_file_binding(runtime_path / relative_path, expected_sha,
                                     "NF3 single full rule runtime: " + relative)
    m.require(execution.get("runtime_before_tree_sha256")
              == execution.get("runtime_after_tree_sha256")
              == fixed.get("runtime_tree_sha256")
              and execution.get("entry_VERSION") == fixed.get("entry_VERSION"),
              "NF3 runtime tree/version differs from fixed record")
    m.require(runtime_freeze.get("kind")
              == "one_actual_deterministic4480_run_no_model_no_validity_claim"
              and runtime_freeze.get("n") == bundle["executed_n"]
              and runtime_freeze.get("runtime_before") == runtime_before
              and runtime_freeze.get("runtime_before_tree_sha256")
              == execution["runtime_before_tree_sha256"]
              and runtime_freeze.get("fixed_runtime_record_sha256")
              == m.sha256_file(fixed_path)
              and runtime_freeze.get("entry_VERSION") == execution["entry_VERSION"]
              and Path(runtime_freeze.get("input_path", "")).resolve()
              == critical["rule_input"].resolve()
              and runtime_freeze.get("input_sha256")
              == m.sha256_file(critical["rule_input"])
              and runtime_freeze.get("manual_sha256") == bundle["manual_sha256"],
              "NF3 pre-run freeze differs from execution, bundle, or fixed runtime record")

    manual_sha = bundle["manual_sha256"]
    representation_mismatch_n = 0
    for rid in executed_ids:
        frame = frame_by_id[rid]
        rule_input = rule_input_by_id[rid]["input"]
        llm_input = llm_input_by_id[rid]
        text = frame["unit_text"]
        m.require(rule_input["unit_text"] == llm_input["text"] == text,
                  f"Current text differs between frame/methods: {rid}")
        m.require(frame["unit_text_sha256"] == m.sha256_text(text)
                  == rule_by_id[rid]["result"]["unit_text_sha256"],
                  f"Current text hash differs: {rid}")
        m.require(rule_by_id[rid].get("status") == "completed"
                  and rule_by_id[rid]["result"].get("current_manual_sha256") == manual_sha,
                  f"Rule output is incomplete or manual-unbound: {rid}")
        m.require(llm_input.get("pages", []) == frame.get("pages", []),
                  f"LLM page binding differs from frame: {rid}")
        identity = frame["shared_context_identity"]
        rule_context = rule_input.get("llm_v29_shared_context")
        model_contexts = llm_input.get("contexts", [])
        m.require(m.canonical_sha256(rule_context) == identity["rule_shared_context_sha256"],
                  f"Rule context identity differs: {rid}")
        m.require(m.canonical_sha256(model_contexts) == identity["model_contexts_sha256"],
                  f"LLM context identity differs: {rid}")
        m.require(len(model_contexts) == identity["model_context_count"],
                  f"LLM context count differs: {rid}")
        if identity["rule_shared_context_sha256"] != identity["model_contexts_sha256"]:
            representation_mismatch_n += 1
        m.require(lineage_by_id[rid]["row_sha256"] == m.canonical_sha256(llm_by_id[rid]),
                  f"LLM assembled row lineage differs: {rid}")
    m.validate_labels(rule_rows, "current rule output", executed_ids)
    m.validate_labels(llm_rows, "current LLM output", executed_ids)
    m.require(bundle.get("rule_partially_unknown_ids") == [
        row["id"] for row in rule_rows
        if any(value is None for value in m.labels_of(row).values())
    ], "Rule partially-unknown ID list differs from full output")
    m.require(execution["n_undetermined"] == sum(
        row.get("result", {}).get("judgement_status") == "undetermined"
        for row in rule_rows), "NF3 undetermined count differs from rule output")

    visual = m.validate_visual_correction_chain(bundle, frame_by_id, rule_input_by_id,
                                                llm_input_by_id)
    changed_ids = visual["changed_ids"]
    original_qa = m.read_json(critical["complete_original_llm_execution_QA"])
    one_summary = m.read_json(critical["one_row_actual_execution"])
    m.require(original_qa.get("all_checks_pass") is True
              and original_qa.get("manual_sha256") == manual_sha,
              "Original complete actual LLM run QA did not pass")
    m.require(one_summary.get("status") == "complete_actual_calls_structurally_valid"
              and one_summary.get("n") == 1
              and one_summary.get("source_unchanged_during_run") is True,
              "Corrected one-row actual LLM run is incomplete")
    m.require(one_summary.get("metric_or_reference_label_based_selection") is False,
              "One-row run reports metric/reference-based selection")
    old_summary = original_qa["llm_summary"]
    for rid in executed_ids:
        line = lineage_by_id[rid]
        if rid in changed_ids:
            m.require(line["actual_output_sha256"] == one_summary["output_sha256"]
                      and line["actual_input_sha256"] == one_summary["input_sha256"]
                      and line["selection_basis"] == "fixed_source_correction_id",
                      "Corrected LLM row lineage differs")
        else:
            m.require(line["actual_output_sha256"] == old_summary["output_sha256"]
                      and line["actual_input_sha256"] == old_summary["input_sha256"]
                      and line["selection_basis"] == "unchanged_full_run_row",
                      f"Unchanged LLM row lineage differs: {rid}")
    m.require(sum(row["selection_basis"] == "unchanged_full_run_row" for row in lineage_rows)
              == bundle["unchanged_llm_rows_n"], "Unchanged LLM row count differs")

    freeze_path = m.bind(m.source_binding_by_name(bundle, "执行冻结记录.json"),
                         "source/LLM execution freeze")
    frame_audit_path = m.bind(m.source_binding_by_name(bundle, "目标框材料校核.json"),
                              "target-frame audit")
    freeze = m.read_json(freeze_path)
    frame_audit = m.read_json(frame_audit_path)
    m.require(freeze.get("source_change_ids") == changed_ids
              and freeze.get("llm_recode_ids") == changed_ids
              and freeze.get("same_manual_sha256") == manual_sha,
              "Source/LLM execution freeze differs from current bundle")
    m.require(frame_audit.get("changed_ids") == changed_ids
              and frame_audit.get("source_frame_sha256") == m.sha256_file(critical["frame"])
              and frame_audit.get("current_text_both_methods_frame_equal_n")
              == bundle["executed_n"], "Target-frame material audit differs")
    return {
        "bundle": bundle, "critical": critical, "frame_rows": frame_rows,
        "frame_by_id": frame_by_id, "executed_ids": executed_ids,
        "rule_rows": rule_rows, "rule_by_id": rule_by_id,
        "llm_rows": llm_rows, "llm_by_id": llm_by_id,
        "representation_hashes_differ_n": representation_mismatch_n,
        "visual": visual, "freeze_path": freeze_path,
        "frame_audit_path": frame_audit_path,
    }


def extract_output_dir(argv):
    if "--output-dir" not in argv:
        raise ValueError("--output-dir is required and must name a separate absolute directory")
    index = argv.index("--output-dir")
    if index + 1 >= len(argv):
        raise ValueError("--output-dir lacks a value")
    output_dir = Path(argv[index + 1])
    if not output_dir.is_absolute():
        raise ValueError("--output-dir must be absolute")
    del argv[index:index + 2]
    return output_dir


def main():
    output_dir = extract_output_dir(sys.argv)
    if "--mode" in sys.argv and sys.argv[sys.argv.index("--mode") + 1] == "execute":
        output_dir.mkdir(parents=True, exist_ok=True)
    m.HERE = output_dir
    m.__file__ = str(Path(__file__).resolve())
    m.validate_current_bundle = validate_single_full_bundle
    m.main()


if __name__ == "__main__":
    main()
