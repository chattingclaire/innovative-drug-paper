"""Independent exact arithmetic for the fixed180+60 development design.

No text or predictions are printed. No reference or prediction is edited.
The prospective human sample is not used for performance evaluation.
"""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
R3 = ROOT / "outputs/coding-revision-20261007-r3"
DIMS = ("S", "E", "Ec", "I", "F")
GROUPS = ("NMPA", "NHSA", "NHC")

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def rows(p):
    values = [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
    result = {r["id"]: r for r in values}
    assert len(values) == len(result)
    return result

def labels(row):
    return row.get("prediction", row)["labels"]

def packed(q):
    return {"exact": str(q), "estimate": float(q)} if q is not None else {"exact": None, "estimate": None}

def result(machine, ref, ids, dim, weights):
    totals = [Q(0) for _ in range(4)]
    raw = [0] * 4
    valid = []
    excluded = []
    for rid in ids:
        a, b = labels(machine[rid])[dim], labels(ref[rid])[dim]
        if type(a) is not int or type(b) is not int or a not in (0, 1) or b not in (0, 1):
            excluded.append(rid)
            continue
        ix = {(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[a, b]
        totals[ix] += weights[rid]
        raw[ix] += 1
        valid.append(rid)
    tp, fp, fn, tn = totals
    n = sum(totals)
    expected_numerator = (tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)
    denominator = n * n - expected_numerator
    values = {
        "kappa": ((tp + tn) * n - expected_numerator) / denominator if denominator else None,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
        "agreement": (tp + tn) / n if n else None,
    }
    return {"paired_n": len(valid), "excluded_ids": excluded,
            "raw_confusion": dict(zip(("TP", "FP", "FN", "TN"), raw)),
            "weighted_confusion": dict(zip(("TP", "FP", "FN", "TN"), map(str, totals))),
            "metrics": {k: packed(v) for k, v in values.items()}}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-rule")
    ap.add_argument("--new-llm-developed240")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    out = Path(args.output)
    assert not out.exists(), "Do not overwrite a completed audit"
    binding_path = R3 / "statistics/final_bindings_v14_CONFIRMED_r3.json"
    binding = read(binding_path)
    for item in [binding["sampling_design"], binding["metadata"], *binding["references"].values()]:
        assert sha(item["path"]) == item["sha256"]
    design = read(binding["sampling_design"]["path"])
    sample = {r["original_id"]: r for r in design["sample"]}
    assert len(sample) == 240
    assert Counter((r["component"], r["group"]) for r in sample.values()) == Counter({
        ("probability_canonical", "NMPA"): 60, ("probability_canonical", "NHSA"): 60,
        ("probability_canonical", "NHC"): 60,
        ("enriched_challenge", "NMPA"): 30, ("enriched_challenge", "NHSA"): 30})
    old_rule_path = R3 / "rules-v36.2-development/all_predictions_material_v14.jsonl"
    llm_path = R3 / "llm-candidate03-development/full-corpus-candidate03-material-v14-single-unit-reconciled-development/all_predictions.jsonl"
    paths = {"rules-v36.2": old_rule_path, "LLM03-full": llm_path}
    if args.new_rule:
        paths["rules-v37-development"] = Path(args.new_rule).resolve()
    if args.new_llm_developed240:
        paths["LLM05-exposed240-development"] = Path(args.new_llm_developed240).resolve()
    machines = {k: rows(v) for k, v in paths.items()}
    refs = {"A": rows(binding["references"]["A"]["path"]), "B": rows(binding["references"]["C"]["path"]),
            "candidate_T": rows(R3 / "reference/candidate_reference_v14_STAGE.jsonl")}
    for r in refs.values():
        assert set(r) == set(sample)
    for name, m in machines.items():
        assert set(sample) <= set(m), name
        assert len(m) == (240 if name.startswith("LLM05") else 4924)
    comparisons = []
    for component in ("probability_canonical", "enriched_challenge"):
        ids0 = [rid for rid, r in sample.items() if r["component"] == component]
        present = [g for g in GROUPS if any(sample[rid]["group"] == g for rid in ids0)]
        selections = [("ALL", "unweighted")] + [(g, "unweighted") for g in present]
        if component == "probability_canonical":
            selections.append(("ALL", "eligible_design_weighted"))
        for group, weighting in selections:
            ids = [rid for rid in ids0 if group == "ALL" or sample[rid]["group"] == group]
            weights = {rid: Q(sample[rid]["canonical_frame_N"], 60) if weighting == "eligible_design_weighted" else Q(1) for rid in ids}
            for name, machine in machines.items():
                for reference, ref in refs.items():
                    for dim in DIMS:
                        comparisons.append({"component": component, "group": group, "weighting": weighting,
                                            "method": name, "reference": reference, "dimension": dim,
                                            **result(machine, ref, ids, dim, weights)})
    # Prove that the independent rational formula reproduces all80 existing
    # displayed comparisons before it is applied to any new candidate.
    table_path = R3 / "manuscript-update-20261008/proxy-180-table2-binding-20261008/表2与五维κ_代理180权威绑定.json"
    table = read(table_path)
    table_checks = 0
    for item in table["table2_values"]:
        method = "rules-v36.2" if item["method_role"] == "rules" else "LLM03-full"
        for reference, reference_row in item["values"].items():
            selected = [r for r in comparisons if r["component"] == "probability_canonical" and r["group"] == "ALL"
                        and r["weighting"] == "eligible_design_weighted" and r["method"] == method
                        and r["reference"] == reference and r["dimension"] == item["dimension"]]
            assert len(selected) == 1
            for metric in ("kappa", "precision", "recall", "f1"):
                actual = selected[0]["metrics"][metric]
                expected = reference_row["metrics"][metric]
                assert Q(actual["exact"]) == Q(expected["exact_fraction"]), (method, reference, item["dimension"], metric)
                table_checks += 1
    assert table_checks == 80
    # Mechanically count the entire corpus, without displaying or reviewing any
    # reserved unit's text or prediction. These summaries are descriptive and
    # are not a candidate-selection target.
    rule_inputs_path = Path(binding["material"]["rule_inputs"]["path"])
    assert sha(rule_inputs_path) == binding["material"]["rule_inputs"]["sha256"]
    metadata = {Path(r["original_file"]).stem: r["analysis_group"] for r in read(binding["metadata"]["path"])["rows"]}
    input_rows = rows(rule_inputs_path)
    groups = {rid: metadata[r["input"]["original_file_stem"]] for rid, r in input_rows.items()}
    assert Counter(groups.values()) == Counter({"NMPA": 1848, "NHSA": 2100, "NHC": 533, "GOV": 443})
    full_counts = []
    for name, machine in machines.items():
        if len(machine) != 4924:
            continue
        for group in GROUPS:
            ids = [rid for rid, g in groups.items() if g == group]
            count = {d: sum(labels(machine[rid])[d] for rid in ids) for d in DIMS}
            total = sum(count.values())
            both = sum(labels(machine[rid])["Ec"] * labels(machine[rid])["F"] for rid in ids)
            full_counts.append({"method": name, "group": group, "unit_n": len(ids),
                                "dimension_counts": count, "sum_five_label_occurrences": total,
                                "attention_percent": {d: packed(Q(100 * c, total)) for d, c in count.items()},
                                "coverage_percent": {d: packed(Q(100 * c, len(ids))) for d, c in count.items()},
                                "Ec_and_F_n": both,
                                "F_given_Ec_percent": packed(Q(100 * both, count["Ec"])) if count["Ec"] else packed(None)})
    manifest_paths = [binding_path, Path(binding["sampling_design"]["path"]), Path(binding["metadata"]["path"]),
                      *paths.values(), *[Path(x["path"]) for x in binding["references"].values()],
                      R3 / "reference/candidate_reference_v14_STAGE.jsonl", table_path, rule_inputs_path, Path(__file__)]
    report = {"status": "PASS_EXACT_FIXED_DEVELOPMENT_POINT_ARITHMETIC",
              "existing80_exact_fraction_crosschecks": table_checks,
              "comparisons_n": len(comparisons),
              "input_bindings": [{"path": str(p.resolve()), "sha256": sha(p)} for p in manifest_paths],
              "comparisons": comparisons,
              "full_corpus_descriptive_counts": full_counts,
              "scope": "Fixed180 SRSWOR canonical probability development cases and separate60 enriched challenge cases. B aliases original C. AI references are not actual human validation.",
              "new_bootstrap_run": False, "new_confidence_intervals": False,
              "future_human_labels_used": False, "labels_modified": False,
              "decision_rule": "Exact points describe changes; they do not select favorable candidates, prove independent validity or constitute a universal publication threshold."}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "comparisons": len(comparisons), "baseline80_exact_checks": table_checks, "output": str(out.resolve()), "sha256": sha(out)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
