"""Prepare a separate report from sealed machine first judgments; never edit them."""
import hashlib
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
DIMS = ("S", "E", "Ec", "I", "F")


def read(path):
    return json.loads(path.read_text())


def binding(path):
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def main():
    native_path = ROOT / "07-statistics/native-v16-current-posthoc-reference-root/verification-and-metrics.json"
    rule_path = ROOT / "07-statistics/rule-v18-current-posthoc-reference-root/metrics.json"
    native, rule = read(native_path), read(rule_path)
    assert native["complete_77"] and native["saved_verified_N"] == 77
    assert rule["actual_complete_records_N"] == 77
    refs = []
    for side in "AB":
        path = ROOT / f"09-delivery/agent-review-20261010/编码复核表-{side}.xlsx"
        expected = next(x for x in native["reference_bindings"] if x["path"] == str(path))
        assert binding(path)["sha256"] == expected["sha256"]
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        refs.append({(row[0], row[2].split()[0]): row for row in wb["编码表"].iter_rows(min_row=7, max_row=391, values_only=True)})
    assert {k: v[3] for k, v in refs[0].items()} == {k: v[3] for k, v in refs[1].items()}
    raw_native = {}
    for batch in native["batches"]:
        path = Path(batch["first_binding"]["path"])
        assert binding(path)["sha256"] == batch["first_binding"]["sha256"]
        raw_native.update({x["source_id"]: (x, path) for x in read(path)["records"]})
    rule_predictions = Path(rule["prediction_binding"]["path"])
    assert binding(rule_predictions)["sha256"] == rule["prediction_binding"]["sha256"]
    raw_rule = {x["id"]: x for x in jsonl(rule_predictions)}
    order = read(ROOT / "06-coding/native-llm77-v16-sol/run-manifest.json")["global_order"]
    rows = []
    for sid in order:
        packet_path = ROOT / f"06-coding/development77-native-inputs-v14/packets/{sid}.compact.json"
        packet = read(packet_path)
        nr, raw_path = raw_native[sid]
        for dim in DIMS:
            source = refs[0][sid, dim]
            nd, rd = nr["dimensions"][dim], raw_rule[sid]["decisions"][dim]
            # This report has short located excerpts; sealed first.json retains every full quote.
            snippets = []
            for evidence in nd["evidence"]:
                pointer = next((evidence.get(k) for k in ("pointer", "json_pointer", "packet_json_pointer", "packet_pointer") if evidence.get(k)), None)
                location = pointer or f"{Path(evidence['asset_path']).name} 第{evidence.get('page')}页"
                quote = evidence["quote"]
                excerpt = quote if len(quote) <= 180 else quote[:180] + "〔节选；完整引文见初判〕"
                snippets.append(f"{location}\n{excerpt}")
            row = [sid, source[1], source[2], source[3], nd["value"] if nd["value"] is not None else "待定", rd["value"] if rd["value"] is not None else "待定", source[4], nd["reason"], rd["reason"], packet["source_bundle"]["source_record"]["text"], "\n\n".join(snippets), rd["basis_path"], str(raw_path), str(packet_path)]
            assert all(not isinstance(value, str) or len(value) < 32767 for value in row)
            rows.append(row)
    assert len(rows) == 385
    data = {"dimensions": DIMS, "rows": rows, "native_dimensions": native["dimensions"], "rule_dimensions": rule["dimensions"], "native_disagreements": native["binary_disagreements"], "rule_disagreements": rule["binary_disagreements"], "bindings": [binding(native_path), binding(rule_path), binding(rule_predictions), *native["reference_bindings"]], "scope": {"assigned_N": 77, "native_valid_slots": sum(x["joint_binary_N"] for x in native["dimensions"].values()), "rule_valid_slots": rule["actual_binary_slots_N"], "native_null_slots": sum(len(x["null_pairs"]) for x in native["dimensions"].values()), "rule_null_slots": rule["semantic_null_slots_N"], "rule_failure_slots": rule["technical_failure_slots_N"], "independent_human_initial_coding_complete": False, "formal_acceptance": False}}
    destination = ROOT / "logs/uniform-machine77-report-delivery"
    destination.mkdir(exist_ok=False)
    with (destination / "report-inputs.json").open("x") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "LLM_disagreements": len(data["native_disagreements"]), "rule_disagreements": len(data["rule_disagreements"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
