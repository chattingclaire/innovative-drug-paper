"""Counts and exact-ratio diagnostics for already sealed AI development rows."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

DIMS = ("S", "E", "Ec", "I", "F")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    items = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    assert len(items) == len({x["id"] for x in items})
    return {x["id"]: x for x in items}


def ratio(a, b):
    return None if b == 0 else float(Fraction(a, b))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--quality-report", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path, required=True)
    args = parser.parse_args()
    quality = json.loads(args.quality_report.read_text())
    adjudication = json.loads(args.adjudication.read_text())
    assert quality["root_quality_passed"] is True
    assert quality["prediction_sha256"] == sha(args.predictions)
    assert adjudication["status"] == "root_nonblind_AI_development_adjudication_complete"
    pred, ref = load(args.predictions), load(args.reference)
    assert set(pred) == set(ref)
    result, errors = {}, []
    for d in DIMS:
        cells = [0, 0, 0, 0]
        unknown = []
        for rid in sorted(pred):
            p, r = pred[rid]["labels"][d], ref[rid]["labels"][d]
            assert p is None or type(p) is int and p in (0, 1)
            assert r is None or type(r) is int and r in (0, 1)
            if p is None or r is None:
                unknown.append({"id": rid, "prediction": p, "reference": r})
                continue
            cells[2 * p + r] += 1
            if p != r:
                errors.append({"id": rid, "dimension": d, "prediction": p,
                               "reference": r, "direction": "FP" if p else "FN"})
        tn, fn, fp, tp = cells
        n = sum(cells)
        chance_numerator = (tp + fp) * (tp + fn) + (tn + fn) * (tn + fp)
        kappa = ratio(n * (tp + tn) - chance_numerator, n * n - chance_numerator)
        metrics = {
            "kappa": kappa, "precision": ratio(tp, tp + fp),
            "recall": ratio(tp, tp + fn), "F1": ratio(2 * tp, 2 * tp + fp + fn),
            "Po": ratio(tp + tn, n), "Ppos": ratio(2 * tp, 2 * tp + fp + fn),
            "Pneg": ratio(2 * tn, 2 * tn + fp + fn),
            "specificity": ratio(tn, tn + fp), "NPV": ratio(tn, tn + fn),
        }
        result[d] = {
            "assigned_n": len(pred), "comparable_n": n,
            "four_cells": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
            "reference_positive_n": sum(x["labels"][d] == 1 for x in ref.values()),
            "reference_negative_n": sum(x["labels"][d] == 0 for x in ref.values()),
            "prediction_positive_n": sum(x["labels"][d] == 1 for x in pred.values()),
            "prediction_negative_n": sum(x["labels"][d] == 0 for x in pred.values()),
            "semantic_unknown": unknown, "metrics": metrics,
            "point_targets": {k: None if metrics[k] is None else metrics[k] >= .8
                              for k in ("kappa", "precision", "recall", "F1")},
            "CI95": None,
            "CI_reason": "Historically exposed, nonprobability development fixture; no population probability CI claimed."
        }
    output = {
        "created_at": datetime.now(timezone.utc).isoformat(), "identity": args.identity,
        "prediction_sha256": sha(args.predictions), "reference_sha256": sha(args.reference),
        "quality_report_sha256": sha(args.quality_report),
        "adjudication_sha256": sha(args.adjudication), "n": len(pred),
        "per_dimension": result, "binary_disagreements": errors,
        "human_validation": False, "formal_acceptance": False,
        "raw_first_judgements_changed": False,
        "point_targets_are_project_criteria_not_universal_method_thresholds": True,
    }
    args.destination.mkdir(parents=True, exist_ok=True)
    with (args.destination / "arithmetic-crosscheck.json").open("x") as stream:
        stream.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"n": len(pred), "errors": errors,
                      "metrics": {d: result[d]["metrics"] for d in DIMS}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
