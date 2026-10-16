#!/usr/bin/env python3
"""Compute development-only diagnostics against the frozen 77-record A/B review sheets.

This is an audit calculation.  It does not alter any coding, prompt, manual, or
review workbook.  Native results are accepted only from root-selected,
whole-batch technical receipts.  The rule results are accepted only from the
sealed v5 receipt-only recovery output.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "07-statistics/current-v5-rule-and-native-complete77-development-diagnostics-root"
REVIEW = ROOT / "09-delivery/agent-review-20261010/真人4项复核后-v2"
RULE = ROOT / "06-coding/rule-full4481-final-v5-receipt-recovery-root"
NATIVE = ROOT / "06-coding/native-full4481-v1-sol"
TARGETED = ROOT / "06-coding/native-reference77-coverage-recovery-v1-sol"
DIMS = ("S", "E", "Ec", "I", "F")
DIM_BY_HEADER = {"S": "S", "E": "E", "Ec": "Ec", "I": "I", "F": "F"}
EXPECTED_SHEETS = {
    "编码复核表-A.xlsx": "2ad1cad77f599bd25dbcb3002e09994ad895ecc85b2c6f3019600d96f10c5cb4",
    "编码复核表-B.xlsx": "6329f4d94a1c667464811326d3a7916be6409a2861da676d69b916aee8a20f4f",
}
EXPECTED_MANUAL = "5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b"
EXPECTED_PROMPT = "69c8291200aa960502c240dc24a6671ca9a8c6b0aad95998e0af611b6ea2ffc9"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def bound(path_s: str, binding: dict) -> Path:
    p = Path(path_s)
    if not p.is_file():
        raise AssertionError(f"missing bound input: {p}")
    if p.stat().st_size != binding["bytes"] or sha(p) != binding["sha256"]:
        raise AssertionError(f"bound input changed: {p}")
    return p


def canon_dim(value: object) -> str:
    s = str(value).strip()
    for d in DIMS:
        if s == d or s.startswith(d + " ") or s.startswith(d + "（") or s.startswith(d + "("):
            return d
    raise AssertionError(f"unrecognized dimension header: {value!r}")


def as_binary(value: object, where: str) -> int:
    if isinstance(value, bool):
        value = int(value)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if str(value).strip() in {"0", "1"}:
        value = int(str(value).strip())
    if value not in (0, 1):
        raise AssertionError(f"nonbinary coding at {where}: {value!r}")
    return value


def read_review(path: Path) -> dict[tuple[str, str], int]:
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb["编码表"]
    headers = [c.value for c in next(ws.iter_rows(min_row=6, max_row=6))]
    ix_id = headers.index("条款编号")
    ix_dim = headers.index("维度")
    ix_val = headers.index("编码值")
    got: dict[tuple[str, str], int] = {}
    for row_no, row in enumerate(ws.iter_rows(min_row=7, values_only=True), start=7):
        if not any(x is not None and str(x).strip() for x in row):
            continue
        raw_id = row[ix_id]
        if raw_id is None:
            raise AssertionError(f"blank clause ID in {path.name}:{row_no}")
        # Excel may expose 00036 as int/float only if its cells lost text formatting.
        clause = str(raw_id).strip()
        if clause.isdigit():
            clause = clause.zfill(5)
        key = ("RECODE25-" + clause if not clause.startswith("RECODE25-") else clause, canon_dim(row[ix_dim]))
        if key in got:
            raise AssertionError(f"duplicate review value: {path.name}:{row_no} {key}")
        got[key] = as_binary(row[ix_val], f"{path.name}:{row_no}")
    if len(got) != 385 or {d for _, d in got} != set(DIMS):
        raise AssertionError(f"unexpected review scope in {path.name}: {len(got)} labels")
    return got


def metric(ref: list[int], pred: list[int]) -> dict:
    if len(ref) != len(pred) or not ref:
        return {"eligible_N": len(ref), "not_estimable": True}
    tp = sum(r == 1 and p == 1 for r, p in zip(ref, pred))
    fp = sum(r == 0 and p == 1 for r, p in zip(ref, pred))
    fn = sum(r == 1 and p == 0 for r, p in zip(ref, pred))
    tn = sum(r == 0 and p == 0 for r, p in zip(ref, pred))
    n = len(ref)
    po = (tp + tn) / n
    ref_pos, pred_pos = tp + fn, tp + fp
    pe = ((ref_pos * pred_pos) + ((n - ref_pos) * (n - pred_pos))) / (n * n)
    precision = None if tp + fp == 0 else tp / (tp + fp)
    recall = None if tp + fn == 0 else tp / (tp + fn)
    f1 = None if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {
        "eligible_N": n,
        "reference_positive_N": ref_pos,
        "prediction_positive_N": pred_pos,
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "observed_agreement": po,
        "chance_agreement": pe,
        "cohen_kappa": None if math.isclose(1 - pe, 0.0) else (po - pe) / (1 - pe),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "p_value": None,
        "p_value_note": "Not computed: this is a post-hoc development diagnostic, not an inferential hypothesis test.",
    }


def load_rule() -> tuple[dict[str, dict[str, object]], dict]:
    exe = json.loads((RULE / "execution.json").read_text())
    seal = json.loads((RULE / "seal.json").read_text())
    if exe["status"] != "completed_receipt_only_recovery" or exe["technical_failure_dimension_N"] != 0:
        raise AssertionError("rule recovery is not complete")
    target = RULE / "recovered-predictions.jsonl"
    seal_members = seal.get("members", seal.get("output_files", []))
    matches = [m for m in seal_members if Path(m.get("path", m.get("relative_path", ""))).name == target.name]
    if not matches:
        # The seal schema permits relative_path rather than path.
        matches = [m for m in seal_members if m.get("relative_path") == target.name]
    if not matches:
        raise AssertionError("rule output absent from its seal")
    m = matches[0]
    if target.stat().st_size != m["bytes"] or sha(target) != m["sha256"]:
        raise AssertionError("sealed rule output changed")
    result = {}
    with target.open() as f:
        for line in f:
            x = json.loads(line)
            labels = x["labels"]
            if set(labels) != set(DIMS):
                raise AssertionError(f"rule dimensions mismatch {x['id']}")
            result[x["id"]] = labels
    if len(result) != 4481:
        raise AssertionError(f"unexpected rule record N {len(result)}")
    return result, exe


def load_native() -> tuple[dict[str, dict[str, object]], list[dict], dict]:
    result: dict[str, dict[str, object]] = {}
    bindings = []
    selections = sorted(NATIVE.glob("batch-*/root-selection.json"))
    for sp in selections:
        s = json.loads(sp.read_text())
        if s.get("artifact_type") != "ROOT_earliest_technically_valid_whole_batch_selection":
            raise AssertionError(f"bad selection type {sp}")
        fp = bound(s["original_whole_batch_first"]["path"], s["original_whole_batch_first"])
        rp = bound(s["technical_reception"]["path"], s["technical_reception"])
        receiver = json.loads(rp.read_text())
        if receiver.get("state") != "technical_valid_whole_batch" or receiver.get("validation", {}).get("state") != "technical_valid_whole_batch_submission":
            raise AssertionError(f"not technically accepted {sp}")
        x = json.loads(fp.read_text())
        if x.get("requested_model") != "gpt-6.1-sol" or x.get("requested_reasoning_effort") != "ultra":
            raise AssertionError(f"unexpected requested model {fp}")
        if x.get("manual_binding", {}).get("sha256") != EXPECTED_MANUAL or x.get("execution_prompt_binding", {}).get("sha256") != EXPECTED_PROMPT:
            raise AssertionError(f"manual/prompt binding mismatch {fp}")
        for rec in x["records"]:
            sid = rec["source_id"]
            if sid in result:
                raise AssertionError(f"native duplicate source: {sid}")
            dims = rec["dimensions"]
            if set(dims) != set(DIMS):
                raise AssertionError(f"native dims mismatch {sid}")
            values = {}
            for d in DIMS:
                v = dims[d].get("value") if isinstance(dims[d], dict) else dims[d]
                if v not in (0, 1, None):
                    raise AssertionError(f"native nonbinary {sid}/{d}: {v!r}")
                values[d] = v
            result[sid] = values
        bindings.append({"selection": str(sp), "selected_first": s["original_whole_batch_first"], "technical_reception": s["technical_reception"]})
    manifest = json.loads((TARGETED / "manifest.json").read_text())
    reception = json.loads((TARGETED / "technical-reception.json").read_text())
    target_ids = manifest["source_ids"]
    if len(target_ids) != 35 or reception.get("technical_valid_N") != len(target_ids):
        raise AssertionError("targeted coverage recovery is incomplete")
    target_rows = {r["source_id"]: r for r in reception["results"]}
    if set(target_rows) != set(target_ids) or any(r["state"] != "technical_valid" for r in target_rows.values()):
        raise AssertionError("targeted coverage recovery has an invalid result")
    for sid in target_ids:
        if sid in result:
            raise AssertionError(f"targeted result overlaps original native result: {sid}")
        first = bound(target_rows[sid]["first"]["path"], target_rows[sid]["first"])
        x = json.loads(first.read_text())
        if x.get("source_id") != sid or x.get("requested_model") != "gpt-6.1-sol" or x.get("requested_reasoning_effort") != "ultra":
            raise AssertionError(f"targeted result identity mismatch: {sid}")
        dims = x["dimensions"]
        if set(dims) != set(DIMS):
            raise AssertionError(f"targeted dimensions mismatch: {sid}")
        result[sid] = {d: dims[d]["value"] for d in DIMS}
        if any(v not in (0, 1, None) for v in result[sid].values()):
            raise AssertionError(f"targeted result nonbinary: {sid}")
        bindings.append({"coverage_recovery_source_id": sid, "first": target_rows[sid]["first"]})
    return result, bindings, {"original_technical_valid_record_N": len(result) - len(target_ids), "coverage_recovery_record_N": len(target_ids), "manifest": str(TARGETED / "manifest.json"), "technical_reception": str(TARGETED / "technical-reception.json")}


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite existing audit output: {OUT}")
    OUT.mkdir(parents=True)
    a_path = REVIEW / "编码复核表-A.xlsx"
    b_path = REVIEW / "编码复核表-B.xlsx"
    for p in (a_path, b_path):
        if sha(p) != EXPECTED_SHEETS[p.name]:
            raise AssertionError(f"review workbook binding changed: {p}")
    a, b = read_review(a_path), read_review(b_path)
    if set(a) != set(b):
        raise AssertionError("A/B review sheet scopes differ")
    disagreements = [(*k, a[k], b[k]) for k in sorted(a) if a[k] != b[k]]
    if disagreements:
        raise AssertionError(f"A/B review values still disagree: {len(disagreements)}")

    rule, rule_execution = load_rule()
    native, native_bindings, native_recovery = load_native()
    ref_ids = sorted({sid for sid, _ in a})
    rows = []
    for sid in ref_ids:
        for d in DIMS:
            rv = a[(sid, d)]
            rule_v = rule[sid][d]
            native_v = native.get(sid, {}).get(d)
            rows.append({"source_id": sid, "dimension": d, "reference_A": rv, "reference_B": b[(sid,d)], "rule_v5": rule_v, "native_existing": native_v,
                         "rule_eligible": rule_v in (0,1), "native_eligible": native_v in (0,1)})

    methods = {}
    for method, col in (("rule_v5", "rule_v5"), ("native_complete_coverage_recovery", "native_existing")):
        per_dim = {}
        combined_ref, combined_pred = [], []
        for d in DIMS:
            eligible = [r for r in rows if r["dimension"] == d and r[col] in (0, 1)]
            per_dim[d] = metric([r["reference_A"] for r in eligible], [r[col] for r in eligible])
            per_dim[d]["reference_scope_N"] = len(ref_ids)
            per_dim[d]["coverage"] = len(eligible) / len(ref_ids)
            combined_ref.extend(r["reference_A"] for r in eligible)
            combined_pred.extend(r[col] for r in eligible)
        methods[method] = {"pooled_labels": metric(combined_ref, combined_pred), "per_dimension": per_dim}
        methods[method]["pooled_labels"]["reference_scope_label_N"] = len(rows)
        methods[method]["pooled_labels"]["coverage"] = len(combined_ref) / len(rows)
        methods[method]["complete_five_dimension_record_N"] = sum(all(next(r for r in rows if r["source_id"] == sid and r["dimension"] == d)[col] in (0,1) for d in DIMS) for sid in ref_ids)

    native_missing_ids = [sid for sid in ref_ids if sid not in native]
    native_partial_ids = [sid for sid in ref_ids if sid in native and any(native[sid][d] not in (0,1) for d in DIMS)]
    summary = {
        "artifact_type": "development_only_machine_vs_frozen_posthoc_77_reference_diagnostics",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "interpretation": {
            "reference": "Two saved A/B 77-record review sheets with identical final binary values. They are post-hoc development reference values, not a newly held-out independent human validation sample.",
            "use": "Descriptive development diagnostic only. It must not be reported as formal validation, inter-rater reliability, generalizable accuracy, or a significance test.",
            "p_values": "No p values or star notation are calculated or appropriate for this diagnostic.",
            "native": "The original native outputs are root-selected, technically valid whole-batch outputs. The 35 missing reference records come from a separate source-at-a-time technical coverage recovery with the same requested gpt-6.1-sol / ultra and frozen manual/prompt. This combined result is a development diagnostic, not a single first-pass full-corpus run. Technical acceptance does not independently verify provider serving model or semantic correctness.",
            "rule": "Uses the sealed full v5 result after a receipt-only recovery of three historically stopped records; no semantic re-judging occurred during recovery.",
        },
        "reference": {"record_N": len(ref_ids), "label_N": len(rows), "A_B_value_disagreement_N": len(disagreements),
                      "workbooks": [{"path": str(p), "sha256": sha(p)} for p in (a_path, b_path)]},
        "rule": {"recovery_output": str(RULE), "execution": rule_execution},
        "native": {"technical_valid_record_N": len(native), "technical_valid_batch_N_or_cases_N": len(native_bindings), "reference_missing_record_N": len(native_missing_ids), "reference_partial_or_null_record_N": len(native_partial_ids),
                   "requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "manual_sha256": EXPECTED_MANUAL, "prompt_sha256": EXPECTED_PROMPT},
        "native_coverage_recovery": native_recovery,
        "methods": methods,
    }
    (OUT / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (OUT / "native-selection-bindings.json").write_text(json.dumps(native_bindings, ensure_ascii=False, indent=2) + "\n")
    (OUT / "native-reference-coverage-gaps.json").write_text(json.dumps({"missing_record_ids": native_missing_ids, "partial_or_null_record_ids": native_partial_ids}, ensure_ascii=False, indent=2) + "\n")
    with (OUT / "comparison-ledger.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    (OUT / "method-note.txt").write_text(
        "This output is a post-hoc development diagnostic. It intentionally does not calculate p values, confidence intervals, or significance stars.\n"
        "No source coding, manual, prompt, A/B workbook, or machine result was modified.\n")
    members = []
    for p in sorted(OUT.iterdir()):
        if p.is_file(): members.append({"relative_path": p.name, "bytes": p.stat().st_size, "sha256": sha(p)})
    (OUT / "seal.json").write_text(json.dumps({"artifact_type": "output_seal", "status": "sealed", "members": members}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "completed", "rule_coverage": methods["rule_v5"]["pooled_labels"]["coverage"], "native_coverage": methods["native_complete_coverage_recovery"]["pooled_labels"]["coverage"], "native_ref_missing": len(native_missing_ids), "out": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
