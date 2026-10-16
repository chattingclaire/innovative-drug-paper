#!/usr/bin/env python3
"""Diagnose the final current-material rule/LLM bundle against existing A/B.

The current bundle is assembled by ``build_current_bundle.py`` and contains a
4481-row target frame plus 4480 executable rows. Rule inputs use a context
dictionary while LLM inputs use a pure-source context list. Their serialized
contexts are verified against separate identity hashes in the target frame;
this script never requires those unlike representations to be equal.

Existing A/B are diagnostic comparators. A/B receives symmetric kappa with
the old-design 5000-replicate interval, agreement, both positive rates, and
four cells for mathematical audit. Precision/recall/F1 are emitted only for
machine-versus-reference comparisons.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
from collections import Counter
from pathlib import Path


DIMS = ("S", "E", "Ec", "I", "F")
COMPONENTS = ("probability_canonical", "enriched_challenge")
EXPECTED_COMPONENT_COUNTS = {"probability_canonical": 180, "enriched_challenge": 60}
HERE = Path(__file__).resolve().parent
RESULT_NAME = "最终同材料规则LLM-既有AB诊断-点估计与5000次区间.json"
MACHINE_CSV_NAME = "最终同材料规则LLM-既有AB诊断-机器对参照指标长表.csv"
AB_CSV_NAME = "最终同材料规则LLM-既有AB诊断-AB对称指标长表.csv"
COMPLETION_NAME = "最终同材料规则LLM-既有AB诊断-执行清单.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def canonical_sha256(value):
    return sha256_text(canonical(value))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]
    ids = [row.get("id") for row in rows]
    require(all(isinstance(rid, str) and rid for rid in ids), f"Invalid ID: {path}")
    require(len(ids) == len(set(ids)), f"Duplicate IDs: {path}")
    return rows, {row["id"]: row for row in rows}


def read_jsonl_raw_lines(path):
    """Return parsed rows plus the exact nonblank byte line for every ID."""
    raw_lines = Path(path).read_bytes().splitlines(keepends=True)
    require(raw_lines and all(line.endswith(b"\n") and line.strip() for line in raw_lines),
            f"JSONL must contain only newline-terminated nonblank rows: {path}")
    rows = [json.loads(line) for line in raw_lines]
    ids = [row.get("id") for row in rows]
    require(all(isinstance(rid, str) and rid for rid in ids), f"Invalid ID: {path}")
    require(len(ids) == len(set(ids)), f"Duplicate IDs: {path}")
    return rows, {row["id"]: row for row in rows}, dict(zip(ids, raw_lines))


def bind(binding, name):
    require(isinstance(binding, dict), f"Missing binding: {name}")
    path = Path(binding.get("path", ""))
    expected = binding.get("sha256")
    require(path.is_absolute() and path.is_file(), f"Missing bound file: {name}: {path}")
    require(isinstance(expected, str) and len(expected) == 64, f"Missing SHA-256: {name}")
    require(sha256_file(path) == expected, f"Hash mismatch: {name}: {path}")
    return path


def labels_of(row):
    if isinstance(row.get("result"), dict):
        return row["result"].get("labels")
    if isinstance(row.get("prediction"), dict):
        return row["prediction"].get("labels")
    return row.get("labels")


def validate_labels(rows, name, expected_ids):
    require([row["id"] for row in rows] == list(expected_ids), f"ID order differs: {name}")
    for row in rows:
        labels = labels_of(row)
        require(isinstance(labels, dict) and set(labels) == set(DIMS),
                f"Label shape differs: {name}: {row['id']}")
        require(all(value is None or type(value) is int and value in (0, 1)
                    for value in labels.values()),
                f"Non-binary/non-unknown label: {name}: {row['id']}")


def labels_digest(rows):
    return canonical_sha256([
        {"id": row["id"], "labels": {dim: labels_of(row)[dim] for dim in DIMS}}
        for row in rows
    ])


def label_adapter(by_id):
    return {rid: {"labels": labels_of(row)} for rid, row in by_id.items()}


def source_binding_by_name(bundle, filename):
    matches = [value for path, value in bundle["source_bindings"].items()
               if Path(path).name == filename]
    require(len(matches) == 1, f"Expected exactly one source binding named {filename}")
    return matches[0]


def verify_nested_file_binding(path, expected_sha, name):
    actual = Path(path)
    require(actual.is_absolute() and actual.is_file(), f"Missing nested bound file: {name}: {actual}")
    require(sha256_file(actual) == expected_sha, f"Nested binding mismatch: {name}: {actual}")
    return actual


def validate_visual_correction_chain(bundle, frame_by_id, rule_input_by_id, llm_input_by_id):
    correction_path = bind(bundle["source_correction"], "03875 source correction")
    correction = read_json(correction_path)
    changed_ids = bundle["llm_replaced_source_ids"]
    require(correction.get("impact_scan") == {"LLM": changed_ids, "rule": changed_ids},
            "Source correction impact scan differs")
    require(correction.get("old_visual_certificate_withdrawn") is True,
            "Old 03875 visual certificate is not withdrawn")
    require(correction.get("original_full_run_preserved") is True
            and correction.get("expected_labels") is None,
            "Correction was not isolated from expected labels/full-run preservation")
    revision_ids = [rid for rid, row in frame_by_id.items() if "source_revision" in row]
    require(revision_ids == changed_ids, "Target-frame source revision IDs differ from bundle")
    require(len(changed_ids) == 1, "Bundle does not contain exactly one scanned source correction")
    rid = changed_ids[0]
    frame_row = frame_by_id[rid]
    require(frame_row["source_revision"].get("only_changed_frame_id") == rid,
            "Target-frame source revision identity differs")
    require(frame_row["unit_text_sha256"] == correction["new_text_sha256"],
            "Correction text hash differs from target frame")
    require(sha256_text(rule_input_by_id[rid]["input"]["unit_text"]) == correction["new_text_sha256"],
            "Rule corrected text differs")
    require(sha256_text(llm_input_by_id[rid]["text"]) == correction["new_text_sha256"],
            "LLM corrected text differs")

    independent_path = bind(source_binding_by_name(bundle, "独立视觉校核结论01.json"),
                            "independent visual check")
    visual_cert_path = bind(source_binding_by_name(bundle, "校正后视觉认证记录.json"),
                            "corrected visual certificate")
    independent = read_json(independent_path)
    visual_cert = read_json(visual_cert_path)
    require(independent.get("id") == rid and independent.get("all_visual_and_change_checks_pass") is True,
            "Independent visual check is absent or did not pass")
    require(independent.get("mechanical_exactly_two_recorded_changes_verified") is True,
            "Two recorded visual changes were not mechanically verified")
    require(independent.get("new_unit_text_sha256") == correction["new_text_sha256"],
            "Independent visual check text hash differs")
    require(visual_cert.get("new_text_sha256") == correction["new_text_sha256"]
            and visual_cert.get("source_pdf_sha256") == correction["source_pdf_sha256"],
            "Corrected visual certificate differs from source correction")
    require(visual_cert.get("independent_review_sha256") == sha256_file(independent_path),
            "Visual certificate does not bind the independent check")
    rendered_page = verify_nested_file_binding(
        visual_cert["rendered_page_path"], visual_cert["rendered_page_sha256"], "03875 rendered page")
    source_pdf_matches = [Path(path) for path, item in independent.get("source_bindings", {}).items()
                          if item.get("sha256") == correction["source_pdf_sha256"]]
    require(len(source_pdf_matches) == 1, "Independent visual check lacks unique source-PDF binding")
    source_pdf = verify_nested_file_binding(source_pdf_matches[0], correction["source_pdf_sha256"],
                                            "03875 source PDF")
    return {
        "changed_ids": changed_ids, "correction_path": correction_path,
        "independent_path": independent_path, "visual_certificate_path": visual_cert_path,
        "rendered_page_path": rendered_page, "source_pdf_path": source_pdf,
        "representation_claim": "visual branch correction only; not contiguous literal PDF extraction",
    }


def validate_current_bundle(bundle_path, expected_bundle_sha):
    require(sha256_file(bundle_path) == expected_bundle_sha, "Current bundle manifest hash mismatch")
    bundle = read_json(bundle_path)
    require(bundle.get("status") == "complete_same_material_current_methods_bound_not_human_validated",
            "Current bundle is not complete")
    require(bundle.get("target_n") == 4481 and bundle.get("executed_n") == 4480,
            "Current bundle target/execution counts differ")
    require(bundle.get("label_or_metric_based_selection") is False
            and bundle.get("new_independent_human_validation") is False,
            "Bundle selection/validation claims differ")
    require(bundle.get("original_references_and_formal_paper_edited") is False,
            "Bundle reports edits to protected references or paper")

    critical = {}
    for key in ("frame", "rule_input", "llm_input", "rule_output", "llm_output",
                "rule_base_output", "rule_base_execution", "rule_patch_input",
                "rule_patch_output", "rule_patch_report", "rule_patch_freeze",
                "rule_patch_scope", "rule_patch_delivery", "rule_lineage", "llm_lineage",
                "source_correction", "complete_original_llm_execution_QA",
                "one_row_actual_execution", "assembly_code"):
        critical[key] = bind(bundle[key], key)
    for name, binding in bundle.get("source_bindings", {}).items():
        bind(binding, "bundle source: " + name)

    frame_rows, frame_by_id = read_jsonl(critical["frame"])
    rule_input_rows, rule_input_by_id = read_jsonl(critical["rule_input"])
    llm_input_rows, llm_input_by_id = read_jsonl(critical["llm_input"])
    rule_rows, rule_by_id, rule_raw_by_id = read_jsonl_raw_lines(critical["rule_output"])
    base_rule_rows, base_rule_by_id, base_rule_raw_by_id = read_jsonl_raw_lines(
        critical["rule_base_output"])
    patch_input_rows, patch_input_by_id, _ = read_jsonl_raw_lines(critical["rule_patch_input"])
    patch_rule_rows, patch_rule_by_id, patch_rule_raw_by_id = read_jsonl_raw_lines(
        critical["rule_patch_output"])
    rule_lineage_rows, rule_lineage_by_id = read_jsonl(critical["rule_lineage"])
    llm_rows, llm_by_id = read_jsonl(critical["llm_output"])
    lineage_rows, lineage_by_id = read_jsonl(critical["llm_lineage"])
    frame_ids = [row["id"] for row in frame_rows]
    executed_ids = [row["id"] for row in rule_input_rows]
    require(len(frame_rows) == bundle["target_n"] and len(executed_ids) == bundle["executed_n"],
            "Bundle counts do not match bound files")
    require([row["id"] for row in llm_input_rows] == executed_ids
            and [row["id"] for row in rule_rows] == executed_ids
            and [row["id"] for row in base_rule_rows] == executed_ids
            and [row["id"] for row in llm_rows] == executed_ids
            and [row["id"] for row in rule_lineage_rows] == executed_ids
            and [row["id"] for row in lineage_rows] == executed_ids,
            "Current executable ID order differs between bundle files")
    executed_set = set(executed_ids)
    missing_from_execution = [rid for rid in frame_ids if rid not in executed_set]
    require(missing_from_execution == bundle["known_source_unknown_ids"],
            "4481 target-frame remainder differs from known source-unknown IDs")

    patch_ids = bundle.get("rule_patch_ids")
    require(isinstance(patch_ids, list) and len(patch_ids) == len(set(patch_ids)) == 34,
            "Rule patch ID set is not the fixed 34-row scope")
    require([row["id"] for row in patch_input_rows] == patch_ids
            and [row["id"] for row in patch_rule_rows] == patch_ids,
            "Rule patch input/output ID order differs from the fixed scope")
    require(bundle.get("unchanged_rule_rows_n") == bundle["executed_n"] - len(patch_ids),
            "Unchanged rule row count differs")
    require(isinstance(bundle.get("rule_execution_scope"), str)
            and "34" in bundle["rule_execution_scope"]
            and "not claimed one single run" in bundle["rule_execution_scope"],
            "Rule execution scope does not disclose the full-run plus 34-row rerun composition")
    for rid in executed_ids:
        if rid in patch_rule_by_id:
            require(canonical(rule_by_id[rid]) == canonical(patch_rule_by_id[rid]),
                    f"Assembled rule row differs from actual 34-row rerun: {rid}")
            require(rule_raw_by_id[rid] == patch_rule_raw_by_id[rid],
                    f"Assembled patched rule row is not the actual rerun bytes: {rid}")
        else:
            require(rule_raw_by_id[rid] == base_rule_raw_by_id[rid],
                    f"Unpatched rule row changed bytes from the base full run: {rid}")
        rule_line = rule_lineage_by_id[rid]
        require(rule_line.get("row_sha256") == canonical_sha256(rule_by_id[rid]),
                f"Rule assembled row lineage differs: {rid}")
        if rid in patch_rule_by_id:
            require(rule_line.get("actual_output") == str(critical["rule_patch_output"])
                    and rule_line.get("actual_output_sha256") == sha256_file(
                        critical["rule_patch_output"])
                    and rule_line.get("selection_basis") == "fixed_source_parse_scope",
                    f"Patched rule row lineage differs: {rid}")
        else:
            require(rule_line.get("actual_output") == str(critical["rule_base_output"])
                    and rule_line.get("actual_output_sha256") == sha256_file(
                        critical["rule_base_output"])
                    and rule_line.get("selection_basis") == "unchanged_full_run_row",
                    f"Base rule row lineage differs: {rid}")
    require(sum(row.get("selection_basis") == "unchanged_full_run_row"
                for row in rule_lineage_rows) == bundle["unchanged_rule_rows_n"],
            "Rule lineage unchanged-row count differs")

    manual_sha = bundle["manual_sha256"]
    representation_mismatch_n = 0
    for rid in executed_ids:
        frame = frame_by_id[rid]
        rule_input = rule_input_by_id[rid]["input"]
        llm_input = llm_input_by_id[rid]
        text = frame["unit_text"]
        require(rule_input["unit_text"] == llm_input["text"] == text,
                f"Current text differs between frame/methods: {rid}")
        require(frame["unit_text_sha256"] == sha256_text(text)
                == rule_by_id[rid]["result"]["unit_text_sha256"],
                f"Current text hash differs: {rid}")
        require(rule_by_id[rid].get("status") == "completed"
                and rule_by_id[rid]["result"].get("current_manual_sha256") == manual_sha,
                f"Rule output is incomplete or manual-unbound: {rid}")
        require(llm_input.get("pages", []) == frame.get("pages", []),
                f"LLM page binding differs from frame: {rid}")
        identity = frame["shared_context_identity"]
        rule_context = rule_input.get("llm_v29_shared_context")
        model_contexts = llm_input.get("contexts", [])
        require(canonical_sha256(rule_context) == identity["rule_shared_context_sha256"],
                f"Rule context identity differs: {rid}")
        require(canonical_sha256(model_contexts) == identity["model_contexts_sha256"],
                f"LLM context identity differs: {rid}")
        require(len(model_contexts) == identity["model_context_count"],
                f"LLM context count differs: {rid}")
        if identity["rule_shared_context_sha256"] != identity["model_contexts_sha256"]:
            representation_mismatch_n += 1
        require(lineage_by_id[rid]["row_sha256"] == canonical_sha256(llm_by_id[rid]),
                f"LLM assembled row lineage differs: {rid}")
    validate_labels(rule_rows, "current rule output", executed_ids)
    validate_labels(base_rule_rows, "base full rule output", executed_ids)
    validate_labels(patch_rule_rows, "actual 34-row rule rerun", patch_ids)
    validate_labels(llm_rows, "current LLM output", executed_ids)

    patch_report = read_json(critical["rule_patch_report"])
    patch_freeze = read_json(critical["rule_patch_freeze"])
    patch_scope = read_json(critical["rule_patch_scope"])
    patch_delivery = read_json(critical["rule_patch_delivery"])
    base_execution = read_json(critical["rule_base_execution"])
    require(base_execution.get("n") == base_execution.get("completed") == bundle["executed_n"]
            and base_execution.get("failed") == 0
            and base_execution.get("input_sha256") == sha256_file(critical["rule_input"])
            and base_execution.get("output_sha256") == sha256_file(critical["rule_base_output"]),
            "Base full rule execution summary differs")
    require(patch_report.get("n") == 34
            and patch_report.get("status_counts") == {"completed": 34}
            and patch_report.get("input_sha256") == sha256_file(critical["rule_patch_input"])
            and patch_report.get("full_input_sha256") == sha256_file(critical["rule_input"])
            and patch_report.get("base_full_output_sha256") == sha256_file(
                critical["rule_base_output"])
            and patch_report.get("output_sha256") == sha256_file(critical["rule_patch_output"])
            and patch_report.get("manual_sha256") == bundle["manual_sha256"]
            and patch_report.get("runtime_unchanged_during_run") is True
            and patch_report.get("baseline_runtime_unchanged") is True
            and patch_report.get("protected_source_input_output_manual_unchanged") is True
            and patch_report.get("no_human_or_model_labels_used") is True
            and patch_report.get("no_performance_or_validity_claim") is True,
            "Actual 34-row rule execution report differs")
    require(patch_freeze.get("ids") == patch_ids
            and patch_freeze.get("subset_n") == 34
            and patch_freeze.get("input_sha256") == sha256_file(critical["rule_patch_input"])
            and patch_freeze.get("full_input_sha256") == sha256_file(critical["rule_input"])
            and patch_freeze.get("base_full_output_sha256") == sha256_file(
                critical["rule_base_output"])
            and patch_freeze.get("manual_sha256") == bundle["manual_sha256"]
            and patch_freeze.get("scope_sha256") == sha256_file(critical["rule_patch_scope"])
            and patch_freeze.get("expected_labels_not_used") is True,
            "Rule patch execution freeze differs")
    require(patch_scope.get("input_sha256") == sha256_file(critical["rule_input"])
            and patch_scope.get("input_rows") == bundle["executed_n"]
            and patch_scope.get("conservative_current_paragraph_ids") == patch_ids
            and patch_scope.get("bounded_potential_ids") == bundle.get("rule_changed_label_ids"),
            "Rule static impact scope differs")
    require(patch_delivery.get("scope_ids") == patch_ids
            and patch_delivery.get("subset_n") == 34
            and patch_delivery.get("input_sha256") == sha256_file(critical["rule_patch_input"])
            and patch_delivery.get("full_input_sha256") == sha256_file(critical["rule_input"])
            and patch_delivery.get("output_sha256") == sha256_file(critical["rule_patch_output"])
            and patch_delivery.get("manual_sha256") == bundle["manual_sha256"]
            and patch_delivery.get("one_actual_subset_run") is True
            and patch_delivery.get("no_validity_claim") is True
            and patch_delivery.get("baseline_runtime_unchanged") is True
            and patch_delivery.get("protected_files_unchanged") is True,
            "Rule patch delivery freeze differs")
    require(all(canonical(patch_input_by_id[rid]) == canonical(rule_input_by_id[rid])
                for rid in patch_ids), "Rule patch inputs differ from current full rule inputs")
    changed_label_ids = [rid for rid in patch_ids
                         if labels_of(base_rule_by_id[rid]) != labels_of(patch_rule_by_id[rid])]
    require(changed_label_ids == bundle.get("rule_changed_label_ids")
            == [row["id"] for row in patch_report.get("changed_rows", [])]
            and patch_report.get("rows_with_identical_five_labels") == 34 - len(changed_label_ids),
            "Rule patch label-change accounting differs")
    require(bundle.get("rule_partially_unknown_ids") == [
        row["id"] for row in rule_rows if any(value is None for value in labels_of(row).values())
    ], "Rule partially-unknown ID list differs from assembled output")

    visual = validate_visual_correction_chain(bundle, frame_by_id, rule_input_by_id, llm_input_by_id)
    changed_ids = visual["changed_ids"]
    original_qa = read_json(critical["complete_original_llm_execution_QA"])
    one_summary = read_json(critical["one_row_actual_execution"])
    require(original_qa.get("all_checks_pass") is True
            and original_qa.get("manual_sha256") == manual_sha,
            "Original complete actual LLM run QA did not pass")
    require(one_summary.get("status") == "complete_actual_calls_structurally_valid"
            and one_summary.get("n") == 1 and one_summary.get("source_unchanged_during_run") is True,
            "Corrected one-row actual LLM run is incomplete")
    require(one_summary.get("metric_or_reference_label_based_selection") is False,
            "One-row run reports metric/reference-based selection")
    old_summary = original_qa["llm_summary"]
    for rid in executed_ids:
        line = lineage_by_id[rid]
        if rid in changed_ids:
            require(line["actual_output_sha256"] == one_summary["output_sha256"]
                    and line["actual_input_sha256"] == one_summary["input_sha256"]
                    and line["selection_basis"] == "fixed_source_correction_id",
                    "Corrected LLM row lineage differs")
        else:
            require(line["actual_output_sha256"] == old_summary["output_sha256"]
                    and line["actual_input_sha256"] == old_summary["input_sha256"]
                    and line["selection_basis"] == "unchanged_full_run_row",
                    f"Unchanged LLM row lineage differs: {rid}")
    require(sum(row["selection_basis"] == "unchanged_full_run_row" for row in lineage_rows)
            == bundle["unchanged_llm_rows_n"], "Unchanged LLM row count differs")

    freeze_path = bind(source_binding_by_name(bundle, "执行冻结记录.json"), "execution freeze")
    frame_audit_path = bind(source_binding_by_name(bundle, "目标框材料校核.json"), "target-frame audit")
    freeze = read_json(freeze_path)
    frame_audit = read_json(frame_audit_path)
    require(freeze.get("source_change_ids") == changed_ids
            and freeze.get("llm_recode_ids") == changed_ids
            and freeze.get("same_manual_sha256") == manual_sha,
            "Execution freeze differs from current bundle")
    require(frame_audit.get("changed_ids") == changed_ids
            and frame_audit.get("source_frame_sha256") == sha256_file(critical["frame"])
            and frame_audit.get("current_text_both_methods_frame_equal_n") == bundle["executed_n"],
            "Target-frame material audit differs")
    return {
        "bundle": bundle, "critical": critical, "frame_rows": frame_rows,
        "frame_by_id": frame_by_id, "executed_ids": executed_ids,
        "rule_rows": rule_rows, "rule_by_id": rule_by_id,
        "llm_rows": llm_rows, "llm_by_id": llm_by_id,
        "representation_hashes_differ_n": representation_mismatch_n,
        "visual": visual, "freeze_path": freeze_path,
        "frame_audit_path": frame_audit_path,
    }


def load_old_design_references_and_core(binding_path, expected_binding_sha, current):
    require(sha256_file(binding_path) == expected_binding_sha, "Legacy binding manifest hash mismatch")
    cfg = read_json(binding_path)
    ref_paths = {"A": bind(cfg["references"]["A"], "existing reference A"),
                 "B": bind(cfg["references"]["C"], "existing reference C displayed as B")}
    design_path = bind(cfg["sampling_design"], "old adopted sampling design")
    core_path = bind(cfg["mathematical_sources"]["statistical_core_r3"], "old mathematical core")
    spec = importlib.util.spec_from_file_location("bound_statistical_core_r3", core_path)
    require(spec is not None and spec.loader is not None, "Cannot load old mathematical core")
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    require(tuple(core.DIMS) == DIMS and core.B == 5000,
            "Old mathematical core dimensions/replicate count differ")
    require(tuple(core.METRIC_NAMES) == (
        "kappa", "agreement", "precision", "recall", "f1",
        "left_positive_rate", "right_positive_rate"), "Old metric order differs")

    design = read_json(design_path)
    sample_rows = design["sample"]
    sample_ids = [row["original_id"] for row in sample_rows]
    require(len(sample_ids) == len(set(sample_ids)), "Duplicate old sample IDs")
    require(Counter(row["component"] for row in sample_rows) == Counter(EXPECTED_COMPONENT_COUNTS),
            "Old probability/challenge counts differ")
    require(design.get("frame_N_by_group") == core.EXPECTED_ELIGIBLE,
            "Old design frame sizes differ from old mathematical core")
    sample = {row["original_id"]: row for row in sample_rows}
    require(set(sample_ids) <= set(current["executed_ids"]),
            "Old sample includes an ID outside current executable rows")
    for row in sample_rows:
        rid = row["original_id"]
        require(current["frame_by_id"][rid]["unit_text_sha256"] == row["unit_text_sha256"],
                f"Current frame text differs from old sampled text: {rid}")
        require(current["frame_by_id"][rid]["analysis_group"] == row["group"],
                f"Current frame department differs from old sample: {rid}")
        if row["component"] == "probability_canonical":
            require(row["sample_n"] == 60
                    and row["canonical_frame_N"] == core.EXPECTED_ELIGIBLE[row["group"]],
                    f"Old probability design fields differ: {rid}")
            require(abs(row["analysis_weight"] - row["canonical_frame_N"] / 60) < 1e-12,
                    f"Old probability weight differs: {rid}")
        else:
            require(row["analysis_weight"] is None, f"Challenge row is unexpectedly weighted: {rid}")
    references = {}
    reference_rows = {}
    for display, path in ref_paths.items():
        rows, by_id = read_jsonl(path)
        require(set(by_id) == set(sample_ids), f"Existing reference {display} IDs differ")
        ordered = [by_id[rid] for rid in sample_ids]
        validate_labels(ordered, f"existing reference {display}", sample_ids)
        for rid in sample_ids:
            provenance = by_id[rid].get("annotation_provenance", {}).get("effective", {})
            require(provenance.get("unit_text_sha256") == sample[rid]["unit_text_sha256"],
                    f"Existing reference {display} text binding differs: {rid}")
        references[display] = label_adapter(by_id)
        reference_rows[display] = ordered
    changed_ids = set(current["visual"]["changed_ids"])
    unknown_ids = set(current["bundle"]["known_source_unknown_ids"])
    return {
        "cfg_path": binding_path, "design_path": design_path, "core_path": core_path,
        "ref_paths": ref_paths, "core": core, "sample_rows": sample_rows,
        "sample_ids": sample_ids, "sample": sample, "references": references,
        "reference_rows": reference_rows,
        "source_changed_sample_intersection": [rid for rid in sample_ids if rid in changed_ids],
        "known_unknown_sample_intersection": [rid for rid in sample_ids if rid in unknown_ids],
    }


def factor_set(core, ctx, ids, component, group, cache):
    if component == "probability_canonical":
        weighting = "eligible_design_weighted"
        mechanism = "department_unit_rescaled_SRSWOR"
    else:
        weighting = "unweighted"
        mechanism = "department_unit_conditional_WR"
    weights = core.weighting(ctx, ids, weighting)
    key = (component, group, mechanism, tuple(ids))
    if key not in cache:
        cache[key] = core.replicate_factors(ctx, ids, component, mechanism)
    return weighting, mechanism, weights, cache[key]


def cells_dict(values, cast):
    return {key: cast(value) for key, value in zip(("11", "10", "01", "00"), values)}


def machine_records(core, ctx, ids, component, group, comparison,
                    left, right, machine, reference, cache):
    weighting, mechanism, weights, factors = factor_set(core, ctx, ids, component, group, cache)
    records = []
    for dim in DIMS:
        matrix, valid = core.cells(left, right, dim, ids)
        raw = matrix.sum(axis=0).astype(int)
        weighted = weights @ matrix
        point = core.metrics(weighted)[0]
        boot = core.metrics((factors * weights[None, :]) @ matrix)
        metrics = {}
        for metric in ("kappa", "precision", "recall", "f1"):
            index = core.METRIC_NAMES.index(metric)
            metrics[metric] = {"estimate": core.safe(point[index]),
                               "ci95_5000_old_design": core.interval(boot[:, index])}
        records.append({
            "record_type": "machine_vs_existing_reference",
            "component": component, "group": group, "comparison": comparison,
            "machine": machine, "right_reference": reference, "dimension": dim,
            "unit_n": len(ids), "paired_n": int(valid.sum()),
            "unknown_pairwise_n": int((~valid).sum()),
            "unknown_pairwise_ids": [rid for rid, ok in zip(ids, valid) if not ok],
            "cell_order": ["11", "10", "01", "00"],
            "raw_cells": cells_dict(raw, int), "weighted_cells": cells_dict(weighted, float),
            "metrics": metrics, "weighting": weighting,
            "bootstrap_mechanism": mechanism, "bootstrap_repetitions": core.B,
            "zero_denominator": "JSON null / CSV NA",
            "unknown_policy": "dimension-specific pairwise exclusion; unknown is never replaced by 0",
        })
    return records


def ab_records(core, ctx, ids, component, group, A, B, cache):
    weighting, mechanism, weights, factors = factor_set(core, ctx, ids, component, group, cache)
    records = []
    for dim in DIMS:
        matrix, valid = core.cells(A, B, dim, ids)
        raw = matrix.sum(axis=0).astype(int)
        weighted = weights @ matrix
        point = core.metrics(weighted)[0]
        boot = core.metrics((factors * weights[None, :]) @ matrix)
        index = core.METRIC_NAMES.index
        records.append({
            "record_type": "existing_A_B_symmetric_diagnostic",
            "component": component, "group": group,
            "comparison": "existing_A_vs_existing_B", "dimension": dim,
            "unit_n": len(ids), "paired_n": int(valid.sum()),
            "unknown_pairwise_n": int((~valid).sum()),
            "unknown_pairwise_ids": [rid for rid, ok in zip(ids, valid) if not ok],
            "cell_order": ["11", "10", "01", "00"],
            "raw_cells": cells_dict(raw, int), "weighted_cells": cells_dict(weighted, float),
            "kappa": {"estimate": core.safe(point[index("kappa")]),
                      "ci95_5000_old_design": core.interval(boot[:, index("kappa")])},
            "agreement": core.safe(point[index("agreement")]),
            "A_positive_rate": core.safe(point[index("left_positive_rate")]),
            "B_positive_rate": core.safe(point[index("right_positive_rate")]),
            "weighting": weighting, "bootstrap_mechanism": mechanism,
            "bootstrap_repetitions": core.B, "reference_truth_assigned": False,
            "precision_recall_f1_emitted": False,
            "unknown_policy": "dimension-specific pairwise exclusion; unknown is never replaced by 0",
        })
    return records


def machine_csv(records):
    fields = ["component", "group", "comparison", "machine", "right_reference", "dimension",
              "unit_n", "paired_n", "unknown_pairwise_n", "n11", "n10", "n01", "n00",
              "weighted11", "weighted10", "weighted01", "weighted00", "kappa", "kappa_low",
              "kappa_high", "precision", "precision_low", "precision_high", "recall", "recall_low",
              "recall_high", "f1", "f1_low", "f1_high", "weighting", "bootstrap_mechanism",
              "bootstrap_repetitions"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for record in records:
        row = {key: record.get(key) for key in fields}
        row.update({"n" + key: value for key, value in record["raw_cells"].items()})
        row.update({"weighted" + key: value for key, value in record["weighted_cells"].items()})
        for metric in ("kappa", "precision", "recall", "f1"):
            item = record["metrics"][metric]
            row[metric] = item["estimate"]
            row[metric + "_low"] = item["ci95_5000_old_design"]["low"]
            row[metric + "_high"] = item["ci95_5000_old_design"]["high"]
        writer.writerow({key: "NA" if row.get(key) is None else row.get(key) for key in fields})
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def ab_csv(records):
    fields = ["component", "group", "comparison", "dimension", "unit_n", "paired_n",
              "unknown_pairwise_n", "n11", "n10", "n01", "n00", "weighted11", "weighted10",
              "weighted01", "weighted00", "kappa", "kappa_low", "kappa_high", "agreement",
              "A_positive_rate", "B_positive_rate", "weighting", "bootstrap_mechanism",
              "bootstrap_repetitions"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for record in records:
        row = {key: record.get(key) for key in fields}
        row.update({"n" + key: value for key, value in record["raw_cells"].items()})
        row.update({"weighted" + key: value for key, value in record["weighted_cells"].items()})
        row["kappa"] = record["kappa"]["estimate"]
        row["kappa_low"] = record["kappa"]["ci95_5000_old_design"]["low"]
        row["kappa_high"] = record["kappa"]["ci95_5000_old_design"]["high"]
        writer.writerow({key: "NA" if row.get(key) is None else row.get(key) for key in fields})
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def atomic_write(path, payload):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-manifest", required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--legacy-bindings", required=True)
    parser.add_argument("--legacy-bindings-sha256", required=True)
    parser.add_argument("--mode", choices=("validate", "execute"), default="validate")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    bundle_path = Path(args.bundle_manifest)
    legacy_path = Path(args.legacy_bindings)
    require(bundle_path.is_absolute() and bundle_path.is_file(), "Bundle manifest must be an absolute file")
    require(legacy_path.is_absolute() and legacy_path.is_file(), "Legacy bindings must be an absolute file")

    current = validate_current_bundle(bundle_path, args.bundle_sha256)
    old = load_old_design_references_and_core(legacy_path, args.legacy_bindings_sha256, current)
    preflight = {
        "status": "actual_current_bundle_validated_no_results_written",
        "bundle_manifest_sha256": args.bundle_sha256,
        "target_n": len(current["frame_rows"]), "executed_n": len(current["executed_ids"]),
        "sample_n": len(old["sample_rows"]),
        "sample_component_counts": dict(Counter(row["component"] for row in old["sample_rows"])),
        "source_changed_sample_intersection": old["source_changed_sample_intersection"],
        "known_unknown_sample_intersection": old["known_unknown_sample_intersection"],
        "rule_and_LLM_context_representation_hashes_differ_n": current["representation_hashes_differ_n"],
        "context_claim": "each representation matches its own frame identity; serialization equality is not claimed",
        "old_machine_outputs_loaded": False, "mathematical_core_load_context_called": False,
        "results_written": False, "interpretation": "旧参照诊断，不是当前共同手册下的新验证。",
    }
    if args.mode == "validate":
        print(json.dumps(preflight, ensure_ascii=False, indent=2))
        return

    output_paths = [HERE / name for name in (RESULT_NAME, MACHINE_CSV_NAME, AB_CSV_NAME, COMPLETION_NAME)]
    if not args.replace:
        require(not any(path.exists() for path in output_paths),
                "Final diagnostic output exists; refusing overwrite without --replace")
    core = old["core"]
    methods = {"rules": label_adapter(current["rule_by_id"]),
               "LLM": label_adapter(current["llm_by_id"])}
    comparisons = [
        ("final_rules_vs_existing_A", methods["rules"], old["references"]["A"], "final_rules", "existing_A"),
        ("final_rules_vs_existing_B", methods["rules"], old["references"]["B"], "final_rules", "existing_B"),
        ("final_LLM_vs_existing_A", methods["LLM"], old["references"]["A"], "final_LLM", "existing_A"),
        ("final_LLM_vs_existing_B", methods["LLM"], old["references"]["B"], "final_LLM", "existing_B"),
    ]
    machine = []
    symmetric = []
    cache = {}
    ctx = {"sample": old["sample"]}
    for component in COMPONENTS:
        component_ids = [rid for rid in old["sample_ids"] if old["sample"][rid]["component"] == component]
        groups = ["ALL"] + [group for group in core.GROUPS
                            if any(old["sample"][rid]["group"] == group for rid in component_ids)]
        for group in groups:
            selected = [rid for rid in component_ids
                        if group == "ALL" or old["sample"][rid]["group"] == group]
            for comparison, left, right, machine_name, reference_name in comparisons:
                machine.extend(machine_records(core, ctx, selected, component, group, comparison,
                                               left, right, machine_name, reference_name, cache))
            symmetric.extend(ab_records(core, ctx, selected, component, group,
                                        old["references"]["A"], old["references"]["B"], cache))
    records = machine + symmetric
    require(len(records) == 175 and len(machine) == 140 and len(symmetric) == 35,
            "Unexpected final diagnostic record count")
    require(all("precision" not in row and "recall" not in row and "f1" not in row
                and row["reference_truth_assigned"] is False for row in symmetric),
            "A-B output accidentally contains directional metrics or gold-reference semantics")

    bound_paths = list(current["critical"].values()) + [
        bundle_path, legacy_path, old["design_path"], old["core_path"],
        old["ref_paths"]["A"], old["ref_paths"]["B"], current["freeze_path"],
        current["frame_audit_path"], Path(__file__),
    ]
    before_hashes = {str(path): sha256_file(path) for path in bound_paths}
    result = {
        "status": "final_current_bundle_existing_AB_diagnostic_completed",
        "interpretation": "共同手册及来源图示校正后的机器编码与既有A/B参照诊断；不是新验证。",
        "metric_contract": {
            "machine_vs_reference": "κ/P/R/F1、四格及旧设计5000次区间；参照在right。",
            "A_vs_B": "κ及其旧设计5000次区间、一致率、双方阳性比例、审计四格；无P/R/F1，不设gold。",
            "unknown": "逐维逐比较pairwise排除，不填0；零分母JSON null/CSV NA。"
        },
        "material_binding": {
            "target_n": len(current["frame_rows"]), "executed_n": len(current["executed_ids"]),
            "source_changed_ids": current["visual"]["changed_ids"],
            "source_changed_sample_intersection": old["source_changed_sample_intersection"],
            "known_source_unknown_ids": current["bundle"]["known_source_unknown_ids"],
            "known_unknown_sample_intersection": old["known_unknown_sample_intersection"],
            "rule_context_dictionary_and_LLM_context_list_serialization_equal_claimed": False,
            "representation_hashes_differ_n": current["representation_hashes_differ_n"],
            "binding_basis": "source04 lineage + actual bundle hashes + current text + per-representation frame identities + 03875 visual correction chain"
        },
        "provenance": {
            "bundle_manifest": {"path": str(bundle_path), "sha256": args.bundle_sha256},
            "legacy_bindings": {"path": str(legacy_path), "sha256": args.legacy_bindings_sha256},
            "input_hashes_before": before_hashes,
            "rule_labels_sha256": labels_digest(current["rule_rows"]),
            "LLM_labels_sha256": labels_digest(current["llm_rows"]),
            "A_labels_sha256": labels_digest(old["reference_rows"]["A"]),
            "B_labels_sha256": labels_digest(old["reference_rows"]["B"]),
            "old_machine_outputs_loaded": False, "mathematical_core_load_context_called": False,
            "labels_modified": False,
        },
        "records": records,
    }
    require(all(sha256_file(path) == digest for path, digest in
                ((Path(path), digest) for path, digest in before_hashes.items())),
            "A bound input changed during calculation")
    result_bytes = json.dumps(result, ensure_ascii=False, indent=2,
                              allow_nan=False).encode("utf-8") + b"\n"
    atomic_write(HERE / RESULT_NAME, result_bytes)
    atomic_write(HERE / MACHINE_CSV_NAME, machine_csv(machine))
    atomic_write(HERE / AB_CSV_NAME, ab_csv(symmetric))
    completion = {
        "status": "complete", "record_n": len(records),
        "machine_reference_record_n": len(machine), "A_B_symmetric_record_n": len(symmetric),
        "A_B_kappa_5000_intervals_emitted": True,
        "A_B_precision_recall_f1_emitted": False, "A_B_gold_reference_assigned": False,
        "result_sha256": sha256_file(HERE / RESULT_NAME),
        "machine_csv_sha256": sha256_file(HERE / MACHINE_CSV_NAME),
        "AB_csv_sha256": sha256_file(HERE / AB_CSV_NAME),
        "script_sha256": sha256_file(Path(__file__)),
        "source_changed_sample_intersection": old["source_changed_sample_intersection"],
        "known_unknown_sample_intersection": old["known_unknown_sample_intersection"],
        "model_calls": 0, "labels_modified": False, "not_new_validation": True,
    }
    atomic_write(HERE / COMPLETION_NAME,
                 json.dumps(completion, ensure_ascii=False, indent=2,
                            allow_nan=False).encode("utf-8") + b"\n")
    print(json.dumps({"status": "completed", "record_n": len(records),
                      "outputs": {path.name: sha256_file(path) for path in output_paths}},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
