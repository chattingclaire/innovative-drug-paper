#!/usr/bin/env python3
"""独立复算本对话当前 40 条指标；只使用 Python 标准库和显式公式。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "当前40条独立核查结果.json"
DIMS = ("S", "E", "Ec", "I", "F")
DEPARTMENTS = ("药监", "医保", "卫健")

FILES = {
    "reference_before": BASE / "当前真人参照40条.jsonl",
    "reference_after": BASE / "校准17裁定后参照40条.jsonl",
    "rule_prediction": BASE / "规则修正/40条规则实际输出-dc26-relation-candidate-04.jsonl",
    "rule_published_evaluation": BASE / "规则修正/冻结预测后评估-dc26-relation-candidate-04.json",
    "llm_batch_01": BASE / "LLM执行澄清02/原始输出/批次01-首次输出.json",
    "llm_batch_02": BASE / "LLM执行澄清02/原始输出/批次02-首次输出.json",
    "llm_batch_03": BASE / "LLM执行澄清02/原始输出/批次03-首次输出.json",
    "llm_batch_04": BASE / "LLM执行澄清02/原始输出/批次04-首次输出.json",
    "llm_published_evaluation": BASE / "LLM执行澄清02/LLM新执行指标.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def safe_div(num: float, den: float) -> float | None:
    return num / den if den else None


def metric(ref_values: list[int], pred_values: list[int]) -> dict[str, Any]:
    if len(ref_values) != len(pred_values):
        raise ValueError("reference/prediction length mismatch")
    tp = sum(r == 1 and p == 1 for r, p in zip(ref_values, pred_values))
    fp = sum(r == 0 and p == 1 for r, p in zip(ref_values, pred_values))
    fn = sum(r == 1 and p == 0 for r, p in zip(ref_values, pred_values))
    tn = sum(r == 0 and p == 0 for r, p in zip(ref_values, pred_values))
    n = tp + fp + fn + tn
    po = safe_div(tp + tn, n)
    # 二分类 Cohen's kappa: Pe = 两类边际概率乘积之和。
    pe = safe_div((tp + fn) * (tp + fp) + (tn + fp) * (tn + fn), n * n)
    kappa = None if po is None or pe is None or pe == 1 else (po - pe) / (1 - pe)
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
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


def id_map(rows: list[dict[str, Any]], name: str) -> dict[str, dict[str, Any]]:
    ids = [r.get("material_id") for r in rows]
    duplicates = sorted(k for k, v in Counter(ids).items() if v > 1)
    if duplicates:
        raise ValueError(f"{name}: duplicate IDs: {duplicates}")
    return {r["material_id"]: r for r in rows}


def labels_check(rows: list[dict[str, Any]], labels_getter, name: str) -> dict[str, Any]:
    errors = []
    present = 0
    for row in rows:
        rid = row.get("material_id")
        labels = labels_getter(row)
        if not isinstance(labels, dict):
            errors.append({"material_id": rid, "error": "labels_not_object"})
            continue
        for dim in DIMS:
            if dim not in labels:
                errors.append({"material_id": rid, "dimension": dim, "error": "missing"})
            else:
                present += 1
                if labels[dim] not in (0, 1) or isinstance(labels[dim], bool):
                    errors.append({"material_id": rid, "dimension": dim, "error": "not_integer_0_or_1", "value": labels[dim]})
        extra = sorted(set(labels) - set(DIMS))
        if extra:
            errors.append({"material_id": rid, "error": "extra_label_keys", "keys": extra})
    return {"source": name, "row_count": len(rows), "expected_label_cells": len(rows) * 5, "present_label_cells": present, "errors": errors, "complete": len(rows) == 40 and present == 200 and not errors}


def calculate_all(reference: dict[str, dict[str, Any]], prediction: dict[str, dict[str, Any]], pred_getter) -> list[dict[str, Any]]:
    result = []
    groups = (("总体", list(reference)),) + tuple((d, [i for i, r in reference.items() if r["department"] == d]) for d in DEPARTMENTS)
    for department, ids in groups:
        for dim in DIMS:
            m = metric([reference[i]["labels"][dim] for i in ids], [pred_getter(prediction[i])[dim] for i in ids])
            result.append({"department": department, "dimension": dim, **m})
    return result


def prediction_disagreements(reference: dict[str, dict[str, Any]], prediction: dict[str, dict[str, Any]], pred_getter) -> list[dict[str, Any]]:
    disagreements = []
    for rid, ref in reference.items():
        predicted = pred_getter(prediction[rid])
        for dim in DIMS:
            if ref["labels"][dim] != predicted[dim]:
                disagreements.append({
                    "material_id": rid,
                    "department": ref["department"],
                    "dimension": dim,
                    "reference": ref["labels"][dim],
                    "prediction": predicted[dim],
                    "error_type": "FP" if predicted[dim] == 1 else "FN",
                })
    return disagreements


def compact_metric(m: dict[str, Any]) -> dict[str, Any]:
    return {k: m.get(k) for k in ("n", "TP", "FP", "FN", "TN", "kappa", "precision", "recall", "F1")}


def metric_differences(calc: list[dict[str, Any]], published: list[dict[str, Any]], published_n_key: str) -> list[dict[str, Any]]:
    pmap = {(x.get("department", "总体"), x["dimension"]): x for x in published}
    diffs = []
    for c in calc:
        key = (c["department"], c["dimension"])
        p = pmap.get(key)
        if p is None:
            diffs.append({"department": key[0], "dimension": key[1], "issue": "published_metric_missing"})
            continue
        fields = {"n": published_n_key, "TP": "TP", "FP": "FP", "FN": "FN", "TN": "TN", "kappa": "kappa", "precision": "precision", "recall": "recall", "F1": "F1"}
        for cf, pf in fields.items():
            cv, pv = c[cf], p.get(pf)
            equal = (cv is None and pv is None) or (isinstance(cv, (int, float)) and isinstance(pv, (int, float)) and abs(cv - pv) <= 1e-12)
            if not equal:
                diffs.append({"department": key[0], "dimension": key[1], "field": cf, "calculated": cv, "published": pv})
    return diffs


def main() -> None:
    before_rows = read_jsonl(FILES["reference_before"])
    after_rows = read_jsonl(FILES["reference_after"])
    rule_rows = read_jsonl(FILES["rule_prediction"])
    llm_rows = []
    llm_batches = []
    for i in range(1, 5):
        obj = read_json(FILES[f"llm_batch_{i:02d}"])
        llm_batches.append({"batch": i, "row_count": len(obj.get("rows", [])), "manual_sha256": obj.get("manual_sha256")})
        llm_rows.extend(obj.get("rows", []))

    before = id_map(before_rows, "reference_before")
    after = id_map(after_rows, "reference_after")
    rule = id_map(rule_rows, "rule_prediction")
    llm = id_map(llm_rows, "llm_prediction")
    expected_ids = [f"校准{i:02d}" for i in range(1, 41)]
    id_checks = {}
    for name, rows, mapping in (("reference_before", before_rows, before), ("reference_after", after_rows, after), ("rule_prediction", rule_rows, rule), ("llm_prediction", llm_rows, llm)):
        ids = [r.get("material_id") for r in rows]
        id_checks[name] = {
            "row_count": len(rows),
            "unique_id_count": len(mapping),
            "duplicates": sorted(k for k, v in Counter(ids).items() if v > 1),
            "missing_expected_ids": sorted(set(expected_ids) - set(mapping)),
            "extra_ids": sorted(set(mapping) - set(expected_ids)),
            "same_order_as_expected": ids == expected_ids,
            "complete": len(rows) == 40 and len(mapping) == 40 and set(mapping) == set(expected_ids),
        }

    ref_changes = []
    for rid in expected_ids:
        a, b = before[rid], after[rid]
        label_changes = {d: {"before": a["labels"][d], "after": b["labels"][d]} for d in DIMS if a["labels"][d] != b["labels"][d]}
        non_label_changed_fields = sorted(k for k in set(a) | set(b) if k != "labels" and a.get(k) != b.get(k))
        if label_changes or non_label_changed_fields:
            ref_changes.append({
                "material_id": rid,
                "label_changes": label_changes,
                "actual_review_notes_A_unchanged": a.get("actual_review_notes", {}).get("A") == b.get("actual_review_notes", {}).get("A"),
                "actual_review_notes_B_unchanged": a.get("actual_review_notes", {}).get("B") == b.get("actual_review_notes", {}).get("B"),
                "non_label_changed_fields": non_label_changed_fields,
            })

    label_checks = [
        labels_check(before_rows, lambda x: x.get("labels"), "reference_before"),
        labels_check(after_rows, lambda x: x.get("labels"), "reference_after"),
        labels_check(rule_rows, lambda x: x.get("prediction", {}).get("labels"), "rule_prediction"),
        labels_check(llm_rows, lambda x: x.get("labels"), "llm_prediction"),
    ]

    rule_metrics = calculate_all(after, rule, lambda x: x["prediction"]["labels"])
    llm_metrics = calculate_all(after, llm, lambda x: x["labels"])
    rule_published = read_json(FILES["rule_published_evaluation"])
    llm_published = read_json(FILES["llm_published_evaluation"])
    rule_diffs = metric_differences(rule_metrics, rule_published.get("metrics", []), "n")
    llm_diffs = metric_differences(llm_metrics, llm_published.get("metrics", []), "n_valid")

    source_hashes = {k: sha256(v) for k, v in FILES.items()}
    undefined_metrics = {
        "rule": [{"department": m["department"], "dimension": m["dimension"], "undefined": [k for k in ("kappa", "precision", "recall", "F1") if m[k] is None]} for m in rule_metrics if any(m[k] is None for k in ("kappa", "precision", "recall", "F1"))],
        "llm": [{"department": m["department"], "dimension": m["dimension"], "undefined": [k for k in ("kappa", "precision", "recall", "F1") if m[k] is None]} for m in llm_metrics if any(m[k] is None for k in ("kappa", "precision", "recall", "F1"))],
    }

    result = {
        "scope": "仅本对话当前40条；未读取另一对话77条",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "formulae": {
            "confusion": "TP=sum(ref=1,pred=1); FP=sum(ref=0,pred=1); FN=sum(ref=1,pred=0); TN=sum(ref=0,pred=0)",
            "kappa": "Po=(TP+TN)/N; Pe=((TP+FN)(TP+FP)+(TN+FP)(TN+FN))/N^2; kappa=(Po-Pe)/(1-Pe); Pe=1时为NA(null)",
            "precision": "TP/(TP+FP); 分母为0时NA(null)",
            "recall": "TP/(TP+FN); 分母为0时NA(null)",
            "F1": "2PR/(P+R); P或R为NA、或P+R=0时NA(null)",
        },
        "source_files": {k: {"path": str(v), "sha256": source_hashes[k], "bytes": v.stat().st_size} for k, v in FILES.items()},
        "embedded_hash_consistency": {
            "rule_published_reference_sha_matches": rule_published.get("reference_sha256") == source_hashes["reference_after"],
            "rule_published_prediction_sha_matches": rule_published.get("prediction_sha256") == source_hashes["rule_prediction"],
            "llm_published_reference_sha_matches": llm_published.get("reference_sha256") == source_hashes["reference_after"],
            "all_prediction_manual_sha_values_equal": len({r["prediction"].get("manual_sha256") for r in rule_rows} | {b["manual_sha256"] for b in llm_batches}) == 1,
        },
        "manual_sha256_values_in_predictions": {
            "rule": sorted({r["prediction"].get("manual_sha256") for r in rule_rows}),
            "llm_batches": llm_batches,
        },
        "id_checks": id_checks,
        "label_cell_checks": label_checks,
        "department_counts_after_reference": dict(Counter(r["department"] for r in after_rows)),
        "reference_change_check": {
            "only_label_change_is_calibration17_F_0_to_1": len(ref_changes) == 1 and ref_changes[0]["material_id"] == "校准17" and ref_changes[0]["label_changes"] == {"F": {"before": 0, "after": 1}},
            "A_B_notes_unchanged_for_all_40": all(before[i].get("actual_review_notes") == after[i].get("actual_review_notes") for i in expected_ids),
            "calibration17_new_independent_A_B_submission_claimed": after["校准17"].get("adjudication", {}).get("new_independent_A_B_submission_claimed"),
            "changes": ref_changes,
        },
        "rule_independent_metrics": rule_metrics,
        "llm_independent_metrics": llm_metrics,
        "prediction_disagreements": {
            "rule": prediction_disagreements(after, rule, lambda x: x["prediction"]["labels"]),
            "llm": prediction_disagreements(after, llm, lambda x: x["labels"]),
        },
        "undefined_metrics_preserved_as_null": undefined_metrics,
        "published_comparison": {
            "rule": {
                "published_metric_rows": len(rule_published.get("metrics", [])),
                "independent_metric_rows": len(rule_metrics),
                "differences": rule_diffs,
                "note": "既有规则评估只列总体5维；部门15行会被报告为published_metric_missing。",
            },
            "llm": {
                "published_metric_rows": len(llm_published.get("metrics", [])),
                "independent_metric_rows": len(llm_metrics),
                "differences": llm_diffs,
            },
        },
        "missing_items": {
            "rule_published_department_metrics_absent": len(rule_published.get("metrics", [])) == 5,
            "invalid_or_missing_label_cells": sum(len(x["errors"]) for x in label_checks),
            "id_set_issues": [name for name, check in id_checks.items() if not check["complete"]],
            "llm_non_coded_rows": [r.get("material_id") for r in llm_rows if r.get("material_status") != "coded"],
        },
        "interpretation_guardrail": "0.80仅按既有文件字段名称视为项目目标/判定字段，不称为发表门槛。",
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT),
        "reference_change_ok": result["reference_change_check"]["only_label_change_is_calibration17_F_0_to_1"],
        "A_B_unchanged": result["reference_change_check"]["A_B_notes_unchanged_for_all_40"],
        "all_sources_200_labels": all(x["complete"] for x in label_checks),
        "all_id_sets_complete": all(x["complete"] for x in id_checks.values()),
        "rule_published_differences": len(rule_diffs),
        "llm_published_differences": len(llm_diffs),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
