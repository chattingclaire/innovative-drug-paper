"""Thin domain projection into unchanged mathematics, after all five terminal."""
import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import sys
from common import campaign, CONDITIONS, check, load, module, save, binding
from terminal_projection import build_projection


def calculate(run):
    run, doc = campaign(run)
    projection = build_projection(run)  # Raises before importing/scoring if incomplete.
    check(doc["ordered_source_ids"])
    check(doc["sample_metadata_coordinator_only"])
    check(doc["source_locator_findings_metadata_only"])
    metadata = {x["source_id"]: x for x in load(doc["sample_metadata_coordinator_only"]["path"])}
    ids = load(doc["ordered_source_ids"]["path"])
    findings = load(doc["source_locator_findings_metadata_only"]["path"])["findings"]
    missing = {x["source_id"] for x in findings if x["status"] == "missing_declared_locator"}
    assert len(ids) == len(set(ids)) == 800 and set(ids) == set(metadata)
    for row in metadata.values():
        assert 0 < Fraction(row["pi_exact"]) <= 1 and Fraction(row["weight_exact"]) == 1 / Fraction(row["pi_exact"])
    assert doc["statistics_bridge"]["sha256"] == "5c51a23bd4613307295c4b0656aca818a9312c01f10d88ee39a7eea6d6ad8f4c"
    assert doc["statistics_engine"]["sha256"] == "4e4bc00ef8f2d5e9d69b99841c18642bbb8919fbea83601d52c61816aca98e6d"
    check(doc["statistics_engine"])
    sys.path.insert(0, str(Path(doc["statistics_bridge"]["path"]).parent))
    bridge = module(doc["statistics_bridge"], "unchanged_statistics_bridge")
    assert binding(bridge.math_engine.__file__) == doc["statistics_engine"]
    assert list(bridge.PAIRS) == [("R1", "R2"), ("R1", "R3"), ("R2", "R3"), ("W", "R1"), ("H", "R1")]
    selected, firsts = {}, {}
    for condition in CONDITIONS:
        rows = projection["conditions"][condition]
        assert [x["source_id"] for x in rows] == ids
        selected[condition], firsts[condition] = {}, {}
        for row in rows:
            labels = row["labels"]
            if labels is not None:
                assert set(labels) == set(bridge.DIMS)
                assert all(x is None or type(x) is int and x in (0, 1) for x in labels.values())
            state = ("valid_binary" if all(x is not None for x in labels.values()) else "valid_semantic_null") if labels is not None else row["status"]
            i = row["source_id"]
            selected[condition][i] = {"state": state, "labels": labels}
            firsts[condition][i] = None if labels is None else {"whole_batch_original": row["whole_batch_original"], "json_pointer": row["json_pointer"], "condition": condition}
    domains = {"fixed800": ids, "remaining600": [i for i in ids if metadata[i]["domain"] == "remaining"], "exposed200": [i for i in ids if metadata[i]["domain"] == "exposed"]}
    assert [len(domains[k]) for k in domains] == [800, 600, 200]
    result = {"run_id": doc["run_id"], "all_five_conditions_terminal": True, "math_engine": doc["statistics_engine"], "statistics_bridge": doc["statistics_bridge"], "classification_accuracy_or_human_validity_claimed": False, "primary_P_replaced": False, "domains": {}, "source_availability_note": "material_pending_n in the reused engine counts existing missing declared locator flags only; other units are not_separately_declared, not certified semantically complete. Availability does not force null or alter binary eligibility.", "individual_record_states": {r: dict(Counter(x["state"] for x in selected[r].values())) for r in CONDITIONS}, "original_record_projection": projection}
    for name, members in domains.items():
        meta = {"ids": members, "weights": {i: Fraction(metadata[i]["weight_exact"]) for i in members}, "records": {i: {"material_state": "pending" if i in missing else "not_separately_declared"} for i in members}}
        pairs, triple = bridge.statistics({"sample": {"weight_kind": "inverse_probability"}}, meta, selected, firsts)
        result["domains"][name] = {"scheduled_N": len(members), "pairs": pairs, "triple": triple, "scope": "fixed machine diagnostic, exposed identity retained; no independent human holdout claim"}
    output = save(run / "terminal-stability-statistics.json", result)
    return {"output": output, "all_five_conditions_terminal": True}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    print(json.dumps(calculate(p.parse_args().run), ensure_ascii=False, indent=2))
