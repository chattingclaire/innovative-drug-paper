"""Keep the earliest technically valid whole batch; never score or splice."""
import argparse
import json
from pathlib import Path
from common import campaign, route, selected_dir, check_prior, binding, check, load, save, put, module, now


def receive(run, condition, batch, attempt):
    run, doc = campaign(run)
    item = route(doc, condition, batch, attempt)
    directory, slot = selected_dir(doc, condition, batch), Path(item["output_directory"])
    check_prior(directory, attempt)
    check(item["assignment"])
    completion = load(slot / "ROOT-cli-process-completion.json")
    assert completion["status"] == "actual_cli_process_terminal", "Uncertain/live process cannot become technical retry"
    assert (completion["condition"], completion["batch_number"], completion["attempt_number"]) == (condition, batch, attempt)
    for key in ("start", "raw_cli_events", "stderr"):
        check(completion[key])
    start = load(completion["start"]["path"])
    assert start["assignment"] == item["assignment"] and start["fixed_request"] == item["fixed_request"]
    check(start["prompt"])
    check(start["GO"])
    validator = module(doc["validator"], "unchanged_production_validator")
    receipt = {"artifact_type": "ROOT_diagnostic_whole_batch_technical_reception", "at_utc": now(), "run_id": doc["run_id"], "condition": condition, "batch_id": item["batch_id"], "batch_number": batch, "attempt_number": attempt, "completion": binding(slot / "ROOT-cli-process-completion.json"), "assignment": item["assignment"], "validator": doc["validator"], "semantic_correctness_checked": False, "reference_or_accuracy_comparison_performed": False, "attempt_files": [binding(p) for p in sorted(slot.iterdir()) if p.is_file()]}
    first, report = slot / "first.json", slot / "report.txt"
    try:
        assert completion["returncode"] == 0, "Actual CLI transport failure"
        assert len(completion["actual_cli_thread_ids"]) == 1 and completion["actual_cli_thread_ids"][0], "Missing genuine fresh CLI thread identity"
        seal = validator.load_strict(slot / "seal.json")
        assert seal["run_id"] == doc["run_id"] and seal["batch_id"] == item["batch_id"], "Actor seal identity mismatch"
        assert not seal.get("template_only", False) and seal["actual_completion_claimed"] is True, "Empty actor seal"
        assert seal["first_binding"] == binding(first) and seal["report_binding"] == binding(report), "Actor original byte seal mismatch"
        for bound in seal.get("actual_input_bindings", []):
            validator.check_binding(bound)
        receipt["validation"] = validator.verify(item["assignment"]["path"], first)
        receipt["state"] = "technical_valid_whole_batch"
    except Exception as error:
        receipt["state"] = "technical_invalid_whole_batch"
        receipt["error"] = {"type": type(error).__name__, "message": str(error)}
        save(directory / f"root-attempt-reception-{attempt:04d}.json", receipt)
        return {"state": receipt["state"], "attempt": attempt, "terminal_exhausted": attempt == 3}
    receipt_binding = save(directory / f"root-attempt-reception-{attempt:04d}.json", receipt)
    mirror = put(directory / "first.json", first.read_bytes())
    assert mirror["sha256"] == binding(first)["sha256"]
    save(directory / "root-selection.json", {"state": "selected", "condition": condition, "batch_number": batch, "selected_attempt_number": attempt, "original_whole_batch_first": binding(first), "canonical_whole_byte_mirror": mirror, "technical_reception": receipt_binding, "original_report": binding(report), "original_actor_seal": binding(slot / "seal.json"), "cross_attempt_record_combination": False, "label_based_selection": False, "legal_null_is_terminal_valid": True})
    return {"state": "selected", "condition": condition, "batch_number": batch, "attempt": attempt, "record_N": receipt["validation"]["record_N"]}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    p.add_argument("--condition", required=True)
    p.add_argument("--batch", type=int, required=True)
    p.add_argument("--attempt", type=int, choices=(1, 2, 3), required=True)
    a = p.parse_args()
    print(json.dumps(receive(a.run, a.condition, a.batch, a.attempt), ensure_ascii=False, indent=2))
