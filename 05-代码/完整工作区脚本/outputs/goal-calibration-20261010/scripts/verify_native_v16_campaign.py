"""Verify new first judgments; compare only after all 13 batches are sealed."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

DIMS = ("S", "E", "Ec", "I", "F")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def bind(path):
    path = Path(path).resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}


def check_binding(item):
    path = Path(item["path"])
    assert path.is_file(), f"missing bound file: {path}"
    assert digest(path) == item["sha256"], f"changed bound file: {path}"
    if "bytes" in item:
        assert path.stat().st_size == item["bytes"], f"changed length: {path}"


def pointer_value(packet, pointer):
    assert isinstance(pointer, str) and pointer.startswith("/"), pointer
    value = packet
    for part in pointer[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def seal_output_bindings(value, directory, key_hint=None):
    found = []
    if isinstance(value, dict):
        if isinstance(value.get("sha256"), str):
            name = value.get("path") or value.get("filename") or value.get("name") or key_hint
            if name:
                path = Path(name)
                if not path.is_absolute():
                    path = directory / path
                if path.is_file() and directory in path.resolve().parents:
                    item = dict(value, path=str(path.resolve()))
                    check_binding(item)
                    found.append(item)
        for key, child in value.items():
            if isinstance(child, (dict, list)):
                found.extend(seal_output_bindings(child, directory, key))
    elif isinstance(value, list):
        for child in value:
            found.extend(seal_output_bindings(child, directory, key_hint))
    return found


def verify_batch(run, batch):
    directory = run / batch["batch_id"]
    assignment_path = Path(batch["assignment_path"])
    assert digest(assignment_path) == batch["assignment_sha256"]
    assignment = load(assignment_path)
    for item in [assignment["manual"], assignment["execution_prompt"], assignment["actor_instructions"], *assignment["packets"]]:
        check_binding(item)
    first_path = directory / "first.json"
    if not first_path.exists() or not (directory / "seal.json").exists():
        return {"batch_id": batch["batch_id"], "state": "incomplete", "expected_N": batch["expected_N"]}, []
    first = load(first_path)
    bindings = seal_output_bindings(load(directory / "seal.json"), directory)
    sealed = {Path(item["path"]).name for item in bindings}
    assert "first.json" in sealed and "report.txt" in sealed, f"unbound final outputs: {directory}"
    records = first["records"]
    assert [record["source_id"] for record in records] == batch["source_ids"], f"coverage/order: {directory}"
    assert len(records) == batch["expected_N"]
    input_bindings = {item["source_id"]: item for item in assignment["packets"]}
    quote_count = 0
    predictions = []
    for record in records:
        sid = record["source_id"]
        input_binding = input_bindings[sid]
        assert record["output_id"] == input_binding["output_id"]
        assert record["packet_sha256"] == input_binding["sha256"]
        assert set(record["dimensions"]) == set(DIMS)
        packet = load(input_binding["path"])
        labels = {}
        for dim in DIMS:
            decision = record["dimensions"][dim]
            value = decision["value"]
            assert value is None or type(value) is int and value in (0, 1), (sid, dim, value)
            assert isinstance(decision.get("reason"), str) and decision["reason"].strip(), (sid, dim, "reason")
            evidence = decision.get("evidence")
            assert isinstance(evidence, list), (sid, dim, "evidence")
            if value is not None:
                assert evidence, (sid, dim, "binary decision without evidence")
            for item in evidence:
                pointer = item.get("pointer") or item.get("json_pointer") or item.get("packet_json_pointer") or item.get("packet_pointer")
                quote = item.get("quote")
                if pointer:
                    field = pointer_value(packet, pointer)
                    assert isinstance(field, str), (sid, dim, pointer, "non-text field")
                    assert isinstance(quote, str) and quote and quote in field, (sid, dim, pointer, "quote mismatch")
                    quote_count += 1
                else:
                    assert item.get("asset_path") and item.get("asset_sha256"), (sid, dim, "unlocated evidence")
                    assert digest(item["asset_path"]) == item["asset_sha256"]
                    assert quote and item.get("page") is not None, (sid, dim, "unlocated asset quote")
            labels[dim] = value
        predictions.append({"id": sid, "labels": labels, "batch_id": batch["batch_id"], "raw_first_binding": bind(first_path)})
    return {
        "batch_id": batch["batch_id"], "state": "sealed_verified", "expected_N": batch["expected_N"],
        "saved_N": len(records), "packet_quote_checks": quote_count, "first_binding": bind(first_path),
        "seal_binding": bind(directory / "seal.json"), "sealed_output_bindings_verified": len(bindings),
        "semantic_correctness_not_inferred_from_hash": True,
        "actor_read_manifest": first.get("read_manifest"),
        "actual_serving_model_independently_verified": False,
    }, predictions


def ratio(numerator, denominator):
    return None if denominator == 0 else float(Fraction(numerator, denominator))


def calculate(predictions, reference):
    results, disagreements = {}, []
    for dim in DIMS:
        tp = fp = fn = tn = 0
        unknown = []
        for row in predictions:
            sid = row["id"]
            pred, ref = row["labels"][dim], reference[sid]["labels"][dim]
            if pred is None or ref is None:
                unknown.append({"id": sid, "prediction": pred, "reference": ref})
                continue
            if pred == 1 and ref == 1:
                tp += 1
            elif pred == 1 and ref == 0:
                fp += 1
            elif pred == 0 and ref == 1:
                fn += 1
            else:
                tn += 1
            if pred != ref:
                disagreements.append({"id": sid, "dimension": dim, "prediction": pred, "reference": ref, "direction": "FP" if pred else "FN"})
        n = tp + fp + fn + tn
        chance = (tp + fp) * (tp + fn) + (tn + fn) * (tn + fp)
        metrics = {
            "kappa": ratio(n * (tp + tn) - chance, n * n - chance),
            "precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn),
            "F1": ratio(2 * tp, 2 * tp + fp + fn), "Po": ratio(tp + tn, n),
            "Pe": ratio(chance, n * n), "Ppos": ratio(2 * tp, 2 * tp + fp + fn),
            "Pneg": ratio(2 * tn, 2 * tn + fp + fn), "specificity": ratio(tn, tn + fp),
            "NPV": ratio(tn, tn + fn),
        }
        results[dim] = {
            "assigned_N": len(reference), "saved_N": len(predictions), "joint_binary_N": n,
            "reference_positive_N": sum(row["labels"][dim] == 1 for row in reference.values()),
            "reference_negative_N": sum(row["labels"][dim] == 0 for row in reference.values()),
            "prediction_positive_N": sum(row["labels"][dim] == 1 for row in predictions),
            "prediction_negative_N": sum(row["labels"][dim] == 0 for row in predictions),
            "null_pairs": unknown, "four_cells": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
            "metrics": metrics,
            "point_targets": {name: None if metrics[name] is None else metrics[name] >= .8 for name in ("kappa", "precision", "recall", "F1")},
            "CI95": None, "CI_reason": "Exposed, nonprobability development77; no population confidence interval claimed.",
        }
    return results, disagreements


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--reference-a", type=Path)
    parser.add_argument("--reference-b", type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    manifest = load(run / "run-manifest.json")
    frozen = load(run / "frozen-inputs-seal.json")
    assert digest(run / "run-manifest.json") == frozen["manifest_sha256"]
    for item in (frozen["manual"], frozen["execution_prompt"], frozen["actor_instructions"]):
        check_binding(item)
    batch_reports, predictions = [], []
    for batch in manifest["batches"]:
        report, rows = verify_batch(run, batch)
        batch_reports.append(report)
        predictions.extend(rows)
    all_complete = all(item["state"] == "sealed_verified" for item in batch_reports)
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(), "run_manifest_binding": bind(run / "run-manifest.json"),
        "expected_N": 77, "saved_verified_N": len(predictions), "complete_77": all_complete,
        "verified_batches_N": sum(item["state"] == "sealed_verified" for item in batch_reports),
        "incomplete_N": 77 - len(predictions), "batches": batch_reports,
        "reference_comparison_unlocked": all_complete, "formal_acceptance": False,
        "human_independent_firsts": False, "old_machine_outputs_modified": False,
        "batching_does_not_count_as_repetition": True,
    }
    args.destination.mkdir(exist_ok=False, parents=True)
    if all_complete:
        assert len(predictions) == 77 and [row["id"] for row in predictions] == manifest["global_order"]
        with (args.destination / "predictions.jsonl").open("x") as stream:
            for row in predictions:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        if args.reference_a and args.reference_b:
            import openpyxl
            references = []
            for path in (args.reference_a, args.reference_b):
                book = openpyxl.load_workbook(path, read_only=True, data_only=True)
                ref = {}
                for row in book["编码表"].iter_rows(min_row=7, max_row=391, values_only=True):
                    sid, dept, dimension, value = row[:4]
                    assert type(value) is int and value in (0, 1)
                    dim = dimension.split()[0]
                    assert dim in DIMS and dim not in ref.setdefault(sid, {"department": dept, "labels": {}})["labels"]
                    ref[sid]["labels"][dim] = value
                assert set(ref) == set(manifest["global_order"])
                assert all(set(row["labels"]) == set(DIMS) for row in ref.values())
                references.append(ref)
            assert references[0] == references[1]
            dims, differences = calculate(predictions, references[0])
            result["reference_bindings"] = [bind(args.reference_a), bind(args.reference_b)]
            result["reference_identity"] = "AI-seeded development tables with targeted human posthoc review; not independent human initial coding"
            result["dimensions"] = dims
            result["binary_disagreements"] = differences
            result["predictions_binding"] = bind(args.destination / "predictions.jsonl")
    with (args.destination / "verification-and-metrics.json").open("x") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("saved_verified_N", "complete_77", "verified_batches_N", "incomplete_N", "formal_acceptance")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
