"""Validate new blind batch files before comparison; never changes predictions."""
from pathlib import Path
from fractions import Fraction
import json
import hashlib
import csv
import datetime
import argparse

ROOT = Path(__file__).resolve().parent
DIMS = ["S", "E", "Ec", "I", "F"]

def read(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")

def metric(pairs):
    tp = sum(p == r == 1 for p, r in pairs)
    fp = sum(p == 1 and r == 0 for p, r in pairs)
    fn = sum(p == 0 and r == 1 for p, r in pairs)
    tn = sum(p == r == 0 for p, r in pairs)
    n = len(pairs)
    ratio = lambda a, b: float(Fraction(a, b)) if b else None
    po = Fraction(tp + tn, n) if n else None
    pe = Fraction((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp), n * n) if n else None
    return {
        "n_valid": n, "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "reference_positive": tp + fn, "prediction_positive": tp + fp,
        "agreement": float(po) if po is not None else None,
        "kappa": float((po - pe) / (1 - pe)) if pe is not None and pe != 1 else None,
        "precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn),
        "F1": ratio(2 * tp, 2 * tp + fp + fn),
        "specificity": ratio(tn, tn + fp),
        "positive_agreement": ratio(2 * tp, 2 * tp + fp + fn),
        "negative_agreement": ratio(2 * tn, 2 * tn + fp + fn),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction-directory", type=Path, default=ROOT / "LLM新输出")
    parser.add_argument("--reference", type=Path, default=ROOT / "当前真人参照40条.jsonl")
    parser.add_argument("--output-directory", type=Path, default=ROOT)
    parser.add_argument("--contract", type=Path, default=ROOT / "LLM执行契约.json")
    args = parser.parse_args()
    out = args.output_directory.resolve()
    out.mkdir(exist_ok=True)
    frozen = read(ROOT / "无答案输入/输入冻结记录.json")
    assert sha(Path(frozen["manual_file"])) == frozen["manual_sha256"]
    contract = read(args.contract)
    prompt = contract.get("same_prompt_for_4_batches") or contract["prompt_file"]
    assert sha(Path(prompt)) == contract["prompt_sha256"]
    allrows, units, bindings, problems = [], {}, [], []
    pending = []
    for index, batch in enumerate(frozen["batches"], 1):
        inp = Path(batch["file"])
        assert sha(inp) == batch["sha256"]
        incoming = read(inp)
        assert incoming["manual_sha256"] == frozen["manual_sha256"]
        for unit in incoming["units"]:
            units[unit["material_id"]] = unit
        output = args.prediction_directory / f"批次{index:02d}-首次输出.json"
        if not output.exists():
            pending.append(str(output))
            continue
        obj = read(output)
        assert obj["manual_sha256"] == frozen["manual_sha256"], output
        named = Path(obj["batch_file"])
        if named.is_absolute():
            assert named.resolve() == inp.resolve(), output
        else:
            assert named.as_posix() in (inp.name, "无答案输入/" + inp.name), output
        assert [r["material_id"] for r in obj["rows"]] == batch["ids"], output
        bindings.append({"path": str(output), "sha256": sha(output), "batch_input_sha256": sha(inp)})
        for row in obj["rows"]:
            mid = row["material_id"]
            unit = units[mid]
            assert row["material_status"] in ("coded", "material_issue"), mid
            if row["material_status"] == "material_issue":
                assert row["labels"] is None and row.get("issue_note"), mid
                problems.append({"material_id": mid, "issue_note": row["issue_note"]})
            else:
                assert set(row["labels"]) == set(DIMS), mid
                assert all(type(row["labels"][d]) is int and row["labels"][d] in (0, 1) for d in DIMS), mid
                assert set(row["dimension_reasons"]) == set(DIMS), mid
                assert all(isinstance(row["dimension_reasons"][d], str) and row["dimension_reasons"][d].strip() for d in DIMS), mid
                for evidence in row["evidence"]:
                    assert evidence["dimension"] in DIMS, mid
                    assert isinstance(evidence["quote"], str) and evidence["quote"].strip(), mid
                    if evidence["source"] == "unit":
                        assert evidence["context_index"] is None, mid
                        source = unit["current_text"]
                    else:
                        assert evidence["source"] == "context", mid
                        i = evidence["context_index"]
                        assert type(i) is int and 1 <= i <= len(unit["contexts"]), mid
                        source = unit["contexts"][i - 1]
                    assert evidence["quote"] in source, (mid, evidence)
                for dim in DIMS:
                    if row["labels"][dim]:
                        assert any(e["dimension"] == dim and e["source"] == "unit" for e in row["evidence"]), (mid, dim)
            allrows.append(row)
    report = {
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "method": "gpt-5.6-sol native fresh agent batches; fixed prompt; one run per batch",
        "manual_sha256": frozen["manual_sha256"], "assigned_N": 40,
        "rows_received": len(allrows), "coded_N": sum(r["material_status"] == "coded" for r in allrows),
        "pending_files": pending, "material_issues": problems,
        "exact_quote_and_schema_checks": "passed_for_received_rows",
        "semantic_correctness_established_by_quote_check": False,
        "bindings": bindings, "other_chat77_used": False,
        "reference_path": str(args.reference.resolve()),
        "reference_sha256": sha(args.reference),
        "prompt_sha256": contract["prompt_sha256"],
        "independent_population_validation": False,
    }
    save(out / "LLM来源与引文核查.json", report)
    if pending:
        print(json.dumps(report, ensure_ascii=False))
        return
    refs = [json.loads(line) for line in args.reference.read_text().splitlines() if line.strip()]
    reference = {r["material_id"]: r for r in refs}
    assert set(reference) == set(units) and len(allrows) == 40
    results, differences = [], []
    valid = [r for r in allrows if r["material_status"] == "coded"]
    for department in [None, "药监", "医保", "卫健"]:
        selected = [r for r in valid if department is None or reference[r["material_id"]]["department"] == department]
        assigned = sum(department is None or r["department"] == department for r in refs)
        for dim in DIMS:
            m = metric([(r["labels"][dim], reference[r["material_id"]]["labels"][dim]) for r in selected])
            m.update(method="LLM", dimension=dim, department=department or "总体", assigned_N=assigned)
            m["project_0_80_target_pass"] = m["n_valid"] == assigned and all(m[k] is not None and m[k] >= .8 for k in ["kappa", "precision", "recall", "F1"])
            results.append(m)
    for row in valid:
        ref = reference[row["material_id"]]
        for dim in DIMS:
            if row["labels"][dim] != ref["labels"][dim]:
                differences.append({
                    "material_id": row["material_id"], "global_id": ref["global_id"],
                    "dimension": dim, "prediction": row["labels"][dim],
                    "reference": ref["labels"][dim], "current_text": units[row["material_id"]]["current_text"],
                    "model_reason": row["dimension_reasons"][dim],
                    "human_review_notes": {arm: ref["actual_review_notes"][arm][dim] for arm in ["A", "B"]},
                    "reference_adjudication": ref.get("adjudication"),
                    "raw_initial_prediction_changed": False,
                })
    save(out / "LLM新执行指标.json", {"scope": "40条同手册有限开发诊断；部门结果为样本内描述", "reference_path": str(args.reference.resolve()), "reference_sha256": sha(args.reference), "all40_coded": len(valid) == 40, "metrics": results, "disagreements": differences})
    with (out / "LLM新执行逐维指标.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(json.dumps({"accepted": len(valid), "material_issues": problems, "overall_metrics": [r for r in results if r["department"] == "总体"], "disagreements": [{"id": r["material_id"], "dimension": r["dimension"], "prediction": r["prediction"], "reference": r["reference"]} for r in differences]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
