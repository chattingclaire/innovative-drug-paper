"""Audit two sealed AI development submissions; never substitute for human validation."""
from pathlib import Path
import argparse
import hashlib
import json
from fractions import Fraction
from datetime import datetime, timezone

DIMENSIONS = ("S", "E", "Ec", "I", "F")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_jsonl(path):
    rows = [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    by_id = {r["id"]: r for r in rows}
    if len(rows) != len(by_id):
        raise ValueError(f"Duplicate IDs in {path}")
    return by_id

def div(numerator, denominator):
    return None if denominator == 0 else float(Fraction(numerator, denominator))

def statistics(a, b, c, d):
    # Rows A0/A1, columns B0/B1. Four integers, no directional reference claim.
    n = a + b + c + d
    if n == 0:
        return {"n": 0, "kappa": None, "agreement": None,
                "positive_specific_agreement": None, "negative_specific_agreement": None}
    po = Fraction(a + d, n)
    pe = Fraction((a + b) * (a + c) + (c + d) * (b + d), n * n)
    kappa = None if pe == 1 else (po - pe) / (1 - pe)
    # Independent closed form in terms of the determinant and discordant margins.
    denom = (a + b) * (b + d) + (a + c) * (c + d)
    alternative = None if denom == 0 else Fraction(2 * (a * d - b * c), denom)
    if kappa != alternative:
        raise ArithmeticError("Kappa formulas disagree")
    return {"n": n, "A_0": a + b, "A_1": c + d, "B_0": a + c, "B_1": b + d,
            "cells": {"A0_B0": a, "A0_B1": b, "A1_B0": c, "A1_B1": d},
            "agreement": float(po), "chance_agreement": float(pe),
            "kappa": None if kappa is None else float(kappa),
            "kappa_exact_fraction": None if kappa is None else str(kappa),
            "positive_specific_agreement": div(2 * d, 2 * d + b + c),
            "negative_specific_agreement": div(2 * a, 2 * a + b + c),
            "formula_crosscheck": "exact rational marginal formula equals 2(ad-bc)/discordant-margin formula"}

def validate_submission(coder, packet, submission):
    problems = []
    if set(packet) != set(submission):
        raise ValueError(f"{coder} missing/extra IDs")
    for ident, row in submission.items():
        labels = row.get("labels", {})
        evidence = row.get("evidence", {})
        if set(labels) != set(DIMENSIONS) or set(evidence) != set(DIMENSIONS):
            raise ValueError(f"{coder} {ident} invalid dimensions")
        current = packet[ident]["text"]
        contexts = {c["context_id"]: c["text"] for c in packet[ident]["contexts"]}
        for dim in DIMENSIONS:
            label = labels[dim]
            if label is not None and (type(label) is not int or label not in (0, 1)):
                raise ValueError(f"{coder} {ident} {dim} invalid binary label")
            e = evidence[dim]
            if not isinstance(e.get("reason"), str) or not e["reason"].strip():
                problems.append({"coder": coder, "id": ident, "dimension": dim, "issue": "missing_reason"})
            quote = e.get("current_quote", "")
            if label == 1 and not quote:
                problems.append({"coder": coder, "id": ident, "dimension": dim, "issue": "positive_without_current_anchor"})
            if quote and quote not in current:
                problems.append({"coder": coder, "id": ident, "dimension": dim, "issue": "current_quote_not_exact", "quote": quote})
            for c in e.get("contexts_used", []):
                if c.get("context_id") not in contexts:
                    problems.append({"coder": coder, "id": ident, "dimension": dim, "issue": "unknown_context_id", "context": c})
                elif not c.get("quote") or c["quote"] not in contexts[c["context_id"]]:
                    problems.append({"coder": coder, "id": ident, "dimension": dim, "issue": "context_quote_not_exact", "context": c})
    return problems

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trial", type=Path)
    args = parser.parse_args()
    trial = args.trial.resolve()
    paths = {coder: {name: trial / coder / name for name in ("packet.jsonl", "labels.jsonl", "manual.md", "submission.json")}
             for coder in ("A", "B")}
    for code_paths in paths.values():
        for path in code_paths.values():
            if not path.exists():
                raise FileNotFoundError(f"Both complete submissions are required: {path}")
    packets = {coder: read_jsonl(code_paths["packet.jsonl"]) for coder, code_paths in paths.items()}
    assert packets["A"] == packets["B"]
    assert digest(paths["A"]["manual.md"]) == digest(paths["B"]["manual.md"])
    labels = {coder: read_jsonl(code_paths["labels.jsonl"]) for coder, code_paths in paths.items()}
    quality = [issue for coder in ("A", "B") for issue in validate_submission(coder, packets[coder], labels[coder])]
    mapping = {r["blind_id"]: r for r in json.loads((trial / "admin/private_mapping.json").read_text())}
    metrics, differences = {}, []
    for dim in DIMENSIONS:
        cells = [0, 0, 0, 0]
        pending = []
        for ident in sorted(packets["A"]):
            aa, bb = labels["A"][ident]["labels"][dim], labels["B"][ident]["labels"][dim]
            if aa is None or bb is None:
                pending.append({"blind_id": ident, "A": aa, "B": bb, "frame_id": mapping[ident]["frame_id"]})
            else:
                cells[2 * aa + bb] += 1
            if aa != bb or aa is None or bb is None:
                differences.append({"blind_id": ident, "frame_id": mapping[ident]["frame_id"],
                                    "department": mapping[ident]["department"], "dimension": dim,
                                    "A": aa, "B": bb, "text": packets["A"][ident]["text"],
                                    "A_evidence": labels["A"][ident]["evidence"][dim],
                                    "B_evidence": labels["B"][ident]["evidence"][dim]})
        metric = statistics(*cells)
        metric.update({"total_n": len(packets["A"]), "both_determinate_n": sum(cells),
                       "pending_n": len(pending), "pending": pending,
                       "A_positive_all_available": sum(row["labels"][dim] == 1 for row in labels["A"].values()),
                       "B_positive_all_available": sum(row["labels"][dim] == 1 for row in labels["B"].values()),
                       "A_pending": sum(row["labels"][dim] is None for row in labels["A"].values()),
                       "B_pending": sum(row["labels"][dim] is None for row in labels["B"].values()),
                       "population_CI": None, "CI_reason": "purposively selected known development cases; no probability-sample population inference"})
        metrics[dim] = metric
    audit = {"status": "AI_development_diagnostics_not_human_or_final_validation",
             "n": len(packets["A"]), "same_material_and_manual": True,
             "inputs": {coder: {name: {"path": str(path), "sha256": digest(path)} for name, path in code_paths.items()}
                        for coder, code_paths in paths.items()},
             "computed_at_utc": datetime.now(timezone.utc).isoformat(),
             "quality_issues": quality, "metrics": metrics,
             "disagreements_and_pending": differences,
             "historical_labels_modified": False,
             "reference_direction": "A/B agreement is symmetric; neither coder is treated as gold",
             "final_acceptance_claim": False}
    output = trial / "admin/diagnostics.json"
    if output.exists():
        raise FileExistsError("Preserve first audit; use another run folder for changes")
    output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    lines = ["# 开发试判01：协商前真实提交诊断", "",
             "A/B均为GPT-6.1 Sol、ultra独立AI。41条来自已曝光边界材料，无抽样权重，不能外推总体或视为真人验收。标签未改写，待定不填0/1。四格为A0B0、A0B1、A1B0、A1B1。", "",
             "|维度|可比n/全部n|四格|A/B正例|待定记录n|观察一致率|κ|正类一致性|负类一致性|", "|---|---|---|---|---|---|---|---|---|"]
    fmt = lambda value: "NA" if value is None else f"{value:.4f}"
    for dim, m in metrics.items():
        lines.append(f"|{dim}|{m['n']}/{m['total_n']}|{list(m['cells'].values())}|{m['A_positive_all_available']}/{m['B_positive_all_available']}|{m['pending_n']}|{fmt(m['agreement'])}|{fmt(m['kappa'])}|{fmt(m['positive_specific_agreement'])}|{fmt(m['negative_specific_agreement'])}|")
    lines.extend(["", "注：n为该维两方都可判的记录数；正例列为各方所有可用判断。κ与正负类一致性仅在两方可判子集计算，NA为无定义。开发材料不报告总体95%区间；此表不是最终验收表。正类一致性与二元同表F1是同一数学量，不作为第二份分类效度证据。", "",
                  f"证据格式核查发现{len(quality)}项问题；应另存更正/说明，不能覆盖初始答案。待定及分歧逐条见diagnostics.json。"])
    (trial / "admin/diagnostics.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"n": audit["n"], "quality_issues": len(quality),
                      "metrics": {d: {k: m[k] for k in ("n", "pending_n", "kappa")} for d, m in metrics.items()}}, ensure_ascii=False))

if __name__ == "__main__":
    main()
