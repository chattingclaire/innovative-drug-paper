"""Expose original record pointers only after every planned condition is terminal."""
import argparse
import json
from receiver import validate_selection
from transport_common import campaign, CONDITIONS, selected_dir, binding, check, load, save


def build_projection(run):
    run, doc = campaign(run)
    # Inspect only execution state and sealed bindings until all 435 batches
    # are terminal. No label values, pairs or triple statistics before this.
    states = {}
    for condition in CONDITIONS:
        states[condition] = []
        for batch in range(1, doc["batch_N"] + 1):
            directory = selected_dir(doc, condition, batch)
            if (directory / "root-selection.json").exists():
                selection = load(directory / "root-selection.json")
                validate_selection(doc, condition, batch, selection)
                assert selection["state"] == "selected" and selection["condition"] == condition and selection["batch_number"] == batch
                for k in ("original_whole_batch_first", "canonical_whole_byte_mirror", "technical_reception"):
                    check(selection[k])
                assert selection["original_whole_batch_first"]["sha256"] == selection["canonical_whole_byte_mirror"]["sha256"]
                receipt = load(selection["technical_reception"]["path"])
                assert receipt["state"] == "technical_valid_whole_batch"
                assert (receipt["condition"], receipt["batch_number"], receipt["attempt_number"]) == (condition, batch, selection["selected_attempt_number"])
                assert receipt["validation"]["submission_sha256"] == selection["original_whole_batch_first"]["sha256"]
                check(receipt["completion"])
                for earlier in range(1, selection["selected_attempt_number"]):
                    assert load(directory / f"root-attempt-reception-{earlier:04d}.json")["state"] == "technical_invalid_whole_batch"
                states[condition].append({"state": "selected", "selection": binding(directory / "root-selection.json")})
            elif (directory / "root-zero-call-block.json").exists():
                block = load(directory / "root-zero-call-block.json")
                assert block["actual_model_calls"] == 0 and block["reason"].strip()
                assert not any((directory / f"attempt-{a:04d}/ROOT-dispatch-start.json").exists() for a in (1, 2, 3))
                states[condition].append({"state": "not_called", "block": binding(directory / "root-zero-call-block.json")})
            else:
                for a in (1, 2, 3):
                    receipt = load(directory / f"root-attempt-reception-{a:04d}.json")
                    assert receipt["state"] == "technical_invalid_whole_batch"
                    assert (receipt["condition"], receipt["batch_number"], receipt["attempt_number"]) == (condition, batch, a)
                    check(receipt["completion"])
                states[condition].append({"state": "technical_fail", "receipts": [binding(directory / f"root-attempt-reception-{a:04d}.json") for a in (1, 2, 3)]})
    result = {"all_five_conditions_all_batches_terminal": True, "conditions": {}, "source_metadata": doc["sample_metadata_coordinator_only"], "statistics_computed": False, "classification_accuracy_claimed": False}
    for condition in CONDITIONS:
        result["conditions"][condition] = []
        for batch, state in zip(doc["batches"], states[condition]):
            if state["state"] == "selected":
                selection = load(state["selection"]["path"])
                raw = load(selection["original_whole_batch_first"]["path"])
                assert [x["source_id"] for x in raw["records"]] == batch["members"]
                for n, record in enumerate(raw["records"]):
                    result["conditions"][condition].append({"source_id": record["source_id"], "status": "valid", "labels": {d: x["value"] for d, x in record["dimensions"].items()}, "whole_batch_original": selection["original_whole_batch_first"], "json_pointer": f"/records/{n}", "terminal_evidence": state})
            else:
                result["conditions"][condition].extend({"source_id": i, "status": state["state"], "labels": None, "terminal_evidence": state} for i in batch["members"])
    return result


def project(run):
    run, _ = campaign(run)
    out = save(run / "terminal-all-five-original-record-projection.json", build_projection(run))
    return {"projection": out, "statistics_computed": False}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    print(json.dumps(project(p.parse_args().run), ensure_ascii=False, indent=2))
