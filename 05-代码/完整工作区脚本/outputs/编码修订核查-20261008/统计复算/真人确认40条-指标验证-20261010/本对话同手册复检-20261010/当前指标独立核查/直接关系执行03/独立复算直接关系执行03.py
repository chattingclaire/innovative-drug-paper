#!/usr/bin/env python3
"""直接关系执行03的独立完整性、逐字差异和指标核查。仅用显式公式。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
RUN = BASE / "LLM直接关系核验03"
REF_PATH = BASE / "校准17裁定后参照40条.jsonl"
RULE_PATH = BASE / "规则修正/40条规则实际输出-dc26-relation-candidate-04.jsonl"
LLM_EVAL_PATH = RUN / "LLM新执行指标.json"
ROUND_PATH = BASE / "本轮结果/结果数据.json"
FIX_PATH = RUN / "引文序号修正记录.json"
OUT_PATH = HERE / "直接关系执行03独立核查结果.json"
DIMS = ("S", "E", "Ec", "I", "F")
DEPTS = ("药监", "医保", "卫健")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_div(a: float, b: float) -> float | None:
    return a / b if b else None


def calculate(ref: list[int], pred: list[int]) -> dict[str, Any]:
    tp = sum(r == 1 and p == 1 for r, p in zip(ref, pred))
    fp = sum(r == 0 and p == 1 for r, p in zip(ref, pred))
    fn = sum(r == 1 and p == 0 for r, p in zip(ref, pred))
    tn = sum(r == 0 and p == 0 for r, p in zip(ref, pred))
    n = tp + fp + fn + tn
    po = safe_div(tp + tn, n)
    pe = safe_div((tp + fn) * (tp + fp) + (tn + fp) * (tn + fn), n * n)
    kappa = None if po is None or pe is None or pe == 1 else (po - pe) / (1 - pe)
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = None if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {"n": n, "TP": tp, "FP": fp, "FN": fn, "TN": tn, "kappa": kappa, "precision": precision, "recall": recall, "F1": f1}


def unique_map(rows: list[dict[str, Any]], source: str) -> dict[str, dict[str, Any]]:
    ids = [x.get("material_id") for x in rows]
    dup = sorted(k for k, count in Counter(ids).items() if count > 1)
    if dup:
        raise ValueError(f"{source} duplicate IDs: {dup}")
    return {x["material_id"]: x for x in rows}


def completeness(rows: list[dict[str, Any]], label_getter, source: str) -> dict[str, Any]:
    expected = [f"校准{i:02d}" for i in range(1, 41)]
    ids = [x.get("material_id") for x in rows]
    errors = []
    count = 0
    for row in rows:
        labels = label_getter(row)
        if not isinstance(labels, dict):
            errors.append({"material_id": row.get("material_id"), "issue": "labels_not_object"})
            continue
        for dim in DIMS:
            if dim not in labels:
                errors.append({"material_id": row.get("material_id"), "dimension": dim, "issue": "missing"})
            else:
                count += 1
                if labels[dim] not in (0, 1) or isinstance(labels[dim], bool):
                    errors.append({"material_id": row.get("material_id"), "dimension": dim, "issue": "not_integer_binary", "value": labels[dim]})
        extra = sorted(set(labels) - set(DIMS))
        if extra:
            errors.append({"material_id": row.get("material_id"), "issue": "extra_dimensions", "value": extra})
    return {
        "source": source,
        "rows": len(rows),
        "unique_ids": len(set(ids)),
        "same_order_as_expected": ids == expected,
        "missing_ids": sorted(set(expected) - set(ids)),
        "extra_ids": sorted(set(ids) - set(expected)),
        "label_cells": count,
        "errors": errors,
        "complete_40_ids_200_labels": len(rows) == 40 and len(set(ids)) == 40 and set(ids) == set(expected) and count == 200 and not errors,
    }


def recursive_diff(a: Any, b: Any, path: str = "") -> list[dict[str, Any]]:
    out = []
    if type(a) is not type(b):
        return [{"path": path, "original": a, "used": b, "issue": "type"}]
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b), key=str):
            p = f"{path}/{key}"
            if key not in a:
                out.append({"path": p, "original": "<MISSING>", "used": b[key], "issue": "added"})
            elif key not in b:
                out.append({"path": p, "original": a[key], "used": "<MISSING>", "issue": "removed"})
            else:
                out.extend(recursive_diff(a[key], b[key], p))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append({"path": path, "original_length": len(a), "used_length": len(b), "issue": "length"})
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(recursive_diff(x, y, f"{path}/{i}"))
    elif a != b:
        out.append({"path": path, "original": a, "used": b, "issue": "value"})
    return out


def all_metrics(ref: dict[str, dict[str, Any]], pred: dict[str, dict[str, Any]], getter) -> list[dict[str, Any]]:
    rows = []
    groups = [("总体", list(ref))] + [(d, [rid for rid, r in ref.items() if r["department"] == d]) for d in DEPTS]
    for dept, ids in groups:
        for dim in DIMS:
            rows.append({"department": dept, "dimension": dim, **calculate([ref[i]["labels"][dim] for i in ids], [getter(pred[i])[dim] for i in ids])})
    return rows


def values_equal(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-12
    return a == b


def compare_metrics(calculated: list[dict[str, Any]], published: list[dict[str, Any]], method: str | None = None) -> dict[str, Any]:
    if method is not None:
        published = [x for x in published if x.get("method") == method]
    pmap = {(x["department"], x["dimension"]): x for x in published}
    differences = []
    for c in calculated:
        key = (c["department"], c["dimension"])
        p = pmap.get(key)
        if p is None:
            differences.append({"department": key[0], "dimension": key[1], "issue": "missing_row"})
            continue
        for cf, pf in (("n", "n_valid"), ("TP", "TP"), ("FP", "FP"), ("FN", "FN"), ("TN", "TN"), ("kappa", "kappa"), ("precision", "precision"), ("recall", "recall"), ("F1", "F1")):
            if not values_equal(c[cf], p.get(pf)):
                differences.append({"department": key[0], "dimension": key[1], "field": cf, "calculated": c[cf], "published": p.get(pf)})
    extras = sorted([{"department": k[0], "dimension": k[1]} for k in set(pmap) - {(x["department"], x["dimension"]) for x in calculated}], key=lambda x: (x["department"], x["dimension"]))
    return {"published_rows": len(published), "calculated_rows": len(calculated), "differences": differences, "extra_rows": extras, "exact_match": not differences and not extras and len(published) == len(calculated)}


def disagreements(ref: dict[str, dict[str, Any]], pred: dict[str, dict[str, Any]], getter) -> list[dict[str, Any]]:
    out = []
    for rid, rr in ref.items():
        labels = getter(pred[rid])
        for dim in DIMS:
            if rr["labels"][dim] != labels[dim]:
                out.append({"material_id": rid, "department": rr["department"], "dimension": dim, "reference": rr["labels"][dim], "prediction": labels[dim], "error_type": "FP" if labels[dim] else "FN"})
    return out


def main() -> None:
    ref_rows = read_jsonl(REF_PATH)
    rule_rows = read_jsonl(RULE_PATH)
    raw_objects, used_objects, raw_rows, used_rows, file_diffs = [], [], [], [], []
    batch_paths = []
    for i in range(1, 5):
        raw_path = RUN / f"原始输出/批次{i:02d}-首次输出.json"
        used_path = RUN / f"使用输出/批次{i:02d}-首次输出.json"
        raw, used = read_json(raw_path), read_json(used_path)
        raw_objects.append(raw); used_objects.append(used)
        raw_rows.extend(raw.get("rows", [])); used_rows.extend(used.get("rows", []))
        diffs = recursive_diff(raw, used)
        file_diffs.append({"batch": i, "difference_count": len(diffs), "differences": diffs})
        batch_paths.extend([raw_path, used_path])

    ref = unique_map(ref_rows, "reference")
    rule = unique_map(rule_rows, "rule")
    raw = unique_map(raw_rows, "raw")
    used = unique_map(used_rows, "used")
    llm_metrics = all_metrics(ref, used, lambda x: x["labels"])
    rule_metrics = all_metrics(ref, rule, lambda x: x["prediction"]["labels"])
    llm_eval = read_json(LLM_EVAL_PATH)
    round_result = read_json(ROUND_PATH)
    fix_record = read_json(FIX_PATH)

    exact_diffs = [d for b in file_diffs for d in b["differences"]]
    expected_path = "/rows/3/evidence/1/context_index"
    only_expected_diff = len(exact_diffs) == 1 and file_diffs[2]["differences"] == [{"path": expected_path, "original": 1, "used": 2, "issue": "value"}]
    row24_raw, row24_used = raw["校准24"], used["校准24"]
    s_raw = [e for e in row24_raw.get("evidence", []) if e.get("dimension") == "S"]
    s_used = [e for e in row24_used.get("evidence", []) if e.get("dimension") == "S"]
    quote_checks = {
        "calibration24_S_evidence_count_raw": len(s_raw),
        "calibration24_S_evidence_count_used": len(s_used),
        "quotes_identical": [e.get("quote") for e in s_raw] == [e.get("quote") for e in s_used],
        "context_indices_raw": [e.get("context_index") for e in s_raw],
        "context_indices_used": [e.get("context_index") for e in s_used],
        "record_quote_matches_output": bool(s_used) and fix_record["changes"][0].get("quote_unchanged") in [e.get("quote") for e in s_used],
    }

    label_reason_checks = {
        "all_40_labels_identical_raw_vs_used": all(raw[i].get("labels") == used[i].get("labels") for i in ref),
        "all_40_dimension_reasons_byte_identical_raw_vs_used": all(raw[i].get("dimension_reasons") == used[i].get("dimension_reasons") for i in ref),
        "all_40_status_and_issue_note_identical": all((raw[i].get("material_status"), raw[i].get("issue_note")) == (used[i].get("material_status"), used[i].get("issue_note")) for i in ref),
    }

    llm_vs_eval = compare_metrics(llm_metrics, llm_eval.get("metrics", []))
    llm_vs_round = compare_metrics(llm_metrics, round_result.get("metrics", []), "LLM编码")
    rule_vs_round = compare_metrics(rule_metrics, round_result.get("metrics", []), "自动规则编码")
    completeness_checks = [
        completeness(ref_rows, lambda x: x.get("labels"), "reference"),
        completeness(rule_rows, lambda x: x.get("prediction", {}).get("labels"), "rule"),
        completeness(raw_rows, lambda x: x.get("labels"), "llm_raw"),
        completeness(used_rows, lambda x: x.get("labels"), "llm_used"),
    ]

    all_paths = [REF_PATH, RULE_PATH, LLM_EVAL_PATH, ROUND_PATH, FIX_PATH, *batch_paths]
    actual_hashes = {str(p): sha256(p) for p in all_paths}
    fix_binding_checks = []
    for binding in fix_record.get("bindings", []):
        source, used_path = binding.get("source"), binding.get("used")
        fix_binding_checks.append({
            "source": source,
            "source_recorded_sha256": binding.get("source_sha256"),
            "source_actual_sha256": actual_hashes.get(source),
            "source_matches": actual_hashes.get(source) == binding.get("source_sha256"),
            "used": used_path,
            "used_recorded_sha256": binding.get("used_sha256"),
            "used_actual_sha256": actual_hashes.get(used_path),
            "used_matches": actual_hashes.get(used_path) == binding.get("used_sha256"),
        })
    relevant_round_bindings = []
    for binding in round_result.get("bindings", []):
        path = binding.get("path")
        if path in actual_hashes:
            relevant_round_bindings.append({"path": path, "recorded_sha256": binding.get("sha256"), "actual_sha256": actual_hashes[path], "matches": binding.get("sha256") == actual_hashes[path]})
    undefined = {
        "llm": [{"department": m["department"], "dimension": m["dimension"], "undefined": [f for f in ("kappa", "precision", "recall", "F1") if m[f] is None]} for m in llm_metrics if any(m[f] is None for f in ("kappa", "precision", "recall", "F1"))],
        "rule": [{"department": m["department"], "dimension": m["dimension"], "undefined": [f for f in ("kappa", "precision", "recall", "F1") if m[f] is None]} for m in rule_metrics if any(m[f] is None for f in ("kappa", "precision", "recall", "F1"))],
    }
    result = {
        "scope": "仅本对话当前40条直接关系执行03；未读取其他对话",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "formulae": {
            "confusion": "TP=sum(ref=1,pred=1); FP=sum(ref=0,pred=1); FN=sum(ref=1,pred=0); TN=sum(ref=0,pred=0)",
            "kappa": "Po=(TP+TN)/N; Pe=((TP+FN)(TP+FP)+(TN+FP)(TN+FN))/N^2; kappa=(Po-Pe)/(1-Pe); Pe=1时NA(null)",
            "precision": "TP/(TP+FP); 分母0时NA(null)",
            "recall": "TP/(TP+FN); 分母0时NA(null)",
            "F1": "2PR/(P+R); P或R为NA、或P+R=0时NA(null)",
        },
        "source_files": {str(p.relative_to(BASE)): {"path": str(p), "sha256": sha256(p), "bytes": p.stat().st_size} for p in all_paths},
        "binding_hash_checks": {
            "correction_record_bindings": fix_binding_checks,
            "all_correction_record_binding_hashes_match": all(x["source_matches"] and x["used_matches"] for x in fix_binding_checks),
            "round_result_relevant_bindings": relevant_round_bindings,
            "all_round_result_relevant_binding_hashes_match": all(x["matches"] for x in relevant_round_bindings),
            "LLM_metric_reference_sha_matches": llm_eval.get("reference_sha256") == actual_hashes[str(REF_PATH)],
            "round_result_declares_other_chat77_used": round_result.get("other_chat77_used"),
        },
        "completeness": completeness_checks,
        "department_counts": dict(Counter(x["department"] for x in ref_rows)),
        "raw_vs_used": {
            "batch_differences": file_diffs,
            "only_calibration24_S_context_index_1_to_2": only_expected_diff,
            "label_reason_checks": label_reason_checks,
            "calibration24_S_quote_check": quote_checks,
            "fix_record_declares_labels_or_reasons_changed": fix_record.get("labels_or_reasons_changed"),
            "fix_record_declares_originals_preserved": fix_record.get("originals_preserved"),
        },
        "llm_independent_metrics_20": llm_metrics,
        "rule_independent_metrics_20": rule_metrics,
        "metric_comparisons": {
            "llm_vs_LLM新执行指标": llm_vs_eval,
            "llm_vs_本轮结果40行中的LLM20行": llm_vs_round,
            "rule_vs_本轮结果40行中的规则20行": rule_vs_round,
            "本轮结果总机器指标行数": len(round_result.get("metrics", [])),
        },
        "prediction_disagreements": {"llm": disagreements(ref, used, lambda x: x["labels"]), "rule": disagreements(ref, rule, lambda x: x["prediction"]["labels"])},
        "undefined_metrics_preserved_as_null": undefined,
        "missing_items": {
            "incomplete_sources": [x["source"] for x in completeness_checks if not x["complete_40_ids_200_labels"]],
            "llm_published_missing_or_extra_metric_rows": not llm_vs_eval["exact_match"],
            "round_result_llm_missing_or_extra_metric_rows": not llm_vs_round["exact_match"],
            "round_result_rule_missing_or_extra_metric_rows": not rule_vs_round["exact_match"],
            "non_coded_used_rows": [x.get("material_id") for x in used_rows if x.get("material_status") != "coded"],
        },
    }
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT_PATH),
        "all_complete": all(x["complete_40_ids_200_labels"] for x in completeness_checks),
        "only_expected_raw_used_diff": only_expected_diff,
        "labels_and_reasons_identical": all(label_reason_checks.values()),
        "llm_eval_exact_match": llm_vs_eval["exact_match"],
        "round_llm_exact_match": llm_vs_round["exact_match"],
        "round_rule_exact_match": rule_vs_round["exact_match"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
