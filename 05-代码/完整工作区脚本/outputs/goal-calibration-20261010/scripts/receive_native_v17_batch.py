"""Receive sealed v17 batch bytes without inspecting reference labels or accuracy.

The frozen preparation validator remains unchanged. This ROOT-only receiver
preserves each actor attempt, validates the entire batch, and mirrors only the
earliest technically valid attempt. It never combines records across attempts.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "06-coding/native-llm77-v17-sol"
VALIDATOR_SHA = "456c4b51084ba47f6234cec29452242aa6644336d454e7166dac3eb5ecd78f8f"


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def exclusive_json(path, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=int, choices=range(1, 14), required=True)
    parser.add_argument("--attempt", type=int, choices=range(1, 4), required=True)
    parser.add_argument("--actor-completed", action="store_true", required=True)
    args = parser.parse_args()
    directory = RUN / f"batch-{args.batch:04d}"
    slot = directory / f"attempt-{args.attempt:04d}"
    receipt_path = directory / f"root-attempt-reception-{args.attempt:04d}.json"
    if receipt_path.exists():
        raise RuntimeError("Existing immutable reception receipt: do not rerun or replace.")
    if (directory / "root-selection.json").exists():
        raise RuntimeError("A valid first batch is already selected; no further attempts allowed.")
    for previous in range(1, args.attempt):
        prior = json.loads((directory / f"root-attempt-reception-{previous:04d}.json").read_text())
        if prior["state"] != "technical_invalid_whole_batch":
            raise RuntimeError("Earlier attempt is not a terminal whole-batch technical failure.")

    validator_path = RUN / "validate-structured-batch.py"
    if binding(validator_path)["sha256"] != VALIDATOR_SHA:
        raise RuntimeError("Frozen validator changed.")
    spec = importlib.util.spec_from_file_location("native_v17_frozen_validator", validator_path)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    receipt = {
        "artifact_type": "ROOT_whole_batch_technical_reception",
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "run_id": "native-llm77-v17-sol",
        "batch_id": f"batch-{args.batch:04d}",
        "attempt_number": args.attempt,
        "runtime_task_name": f"native_v17_b{args.batch:04d}_a{args.attempt:02d}",
        "context_unit": "batch",
        "actor_completion_received_by_ROOT": True,
        "assignment": binding(directory / "assignment.json"),
        "fixed_dispatch_request": binding(directory / "dispatch-request.txt"),
        "validator": binding(validator_path),
        "semantic_correctness_checked": False,
        "reference_or_accuracy_comparison_performed": False,
        "provider_wire_capture_claimed": False,
        "actual_tool_presentations_independently_verified": False,
        "attempt_files": [binding(p) for p in sorted(slot.rglob("*")) if p.is_file()],
    }
    try:
        first_path, report_path, seal_path = (slot / name for name in ("first.json", "report.txt", "seal.json"))
        seal = validator.load_strict(seal_path)
        assert seal["run_id"] == receipt["run_id"] and seal["batch_id"] == receipt["batch_id"], "Actor seal identity mismatch"
        assert seal["template_only"] is False and seal["actual_completion_claimed"] is True, "Uninstantiated actor seal"
        assert seal["first_binding"] == binding(first_path), "Actor first-byte seal mismatch"
        assert seal["report_binding"] == binding(report_path), "Actor report-byte seal mismatch"
        for item in seal.get("actual_input_bindings", []):
            validator.check_binding(item)
        receipt["validation"] = validator.verify(directory / "assignment.json", first_path)
        receipt["state"] = "technical_valid_whole_batch"
    except Exception as error:
        receipt["state"] = "technical_invalid_whole_batch"
        receipt["error"] = {"type": type(error).__name__, "message": str(error)}
        exclusive_json(receipt_path, receipt)
        print(json.dumps({"state": receipt["state"], "receipt": str(receipt_path), "error": receipt["error"]}, ensure_ascii=False))
        return

    exclusive_json(receipt_path, receipt)
    first_raw = first_path.read_bytes()
    canonical_path = directory / "first.json"
    with canonical_path.open("xb") as stream:
        stream.write(first_raw)
    assert binding(canonical_path)["sha256"] == binding(first_path)["sha256"]
    selection = {
        "artifact_type": "ROOT_earliest_technically_valid_whole_batch_selection",
        "run_id": receipt["run_id"], "batch_id": receipt["batch_id"],
        "selected_attempt_number": args.attempt,
        "original_whole_batch_first": binding(first_path),
        "original_report": binding(report_path), "original_actor_seal": binding(seal_path),
        "technical_reception": binding(receipt_path), "canonical_whole_byte_mirror": binding(canonical_path),
        "cross_attempt_record_combination": False, "label_based_selection": False,
        "first_definition": "Native actor first complete structured whole-batch submission UTF8 file; not provider network response.",
        "all_actual_attempts_retained": True, "legal_null_is_terminal_valid": True,
        "accuracy_comparison_performed": False,
    }
    exclusive_json(directory / "root-selection.json", selection)
    print(json.dumps({"state": receipt["state"], "batch_id": receipt["batch_id"], "selected_attempt_number": args.attempt, "canonical_sha256": binding(canonical_path)["sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
