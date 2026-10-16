"""Seal real whole-batch attempts before the development comparison opens Gold."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "06-coding/native-llm77-v17-sol"
OUT = ROOT / "logs/native-v17-ROOT-complete-campaign-technical-audit-20261010.json"


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    assert not (ROOT / "07-statistics/native-v17-rule-v19-human-confirmed77-root").exists()
    paths = [NATIVE / f"batch-{i:04d}/root-selection.json" for i in range(1, 14)]
    assert all(path.is_file() for path in paths), "All fixed batches must be selected first."
    validator_path = NATIVE / "validate-structured-batch.py"
    assert binding(validator_path)["sha256"] == "456c4b51084ba47f6234cec29452242aa6644336d454e7166dac3eb5ecd78f8f"
    spec = importlib.util.spec_from_file_location("frozen_validator", validator_path)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    manifest = validator.load_strict(NATIVE / "run-manifest.json")
    selections, attempts, ordered_ids = [], [], []
    for selection_path in paths:
        folder = selection_path.parent
        assignment_path = folder / "assignment.json"
        assignment = validator.load_strict(assignment_path)
        selection = validator.load_strict(selection_path)
        for key in ("original_whole_batch_first", "original_report", "original_actor_seal", "technical_reception", "canonical_whole_byte_mirror"):
            validator.check_binding(selection[key])
        selected = selection["selected_attempt_number"]
        assert 1 <= selected <= 3
        assert selection["original_whole_batch_first"]["sha256"] == selection["canonical_whole_byte_mirror"]["sha256"]
        validation = validator.verify(assignment_path, selection["original_whole_batch_first"]["path"])
        first = validator.load_strict(selection["original_whole_batch_first"]["path"])
        ordered_ids.extend(row["source_id"] for row in first["records"])
        dispatch_paths = sorted(folder.glob("attempt-*/ROOT-dispatch-tool-receipt.json"))
        assert len(dispatch_paths) == selected, "No selected-answer rerun may be hidden."
        for number, dispatch_path in enumerate(dispatch_paths, 1):
            dispatch = validator.load_strict(dispatch_path)
            assert dispatch["actual_coding_attempt_number"] == number
            assert dispatch["requested_model"] == "gpt-6.1-sol"
            assert dispatch["requested_reasoning_effort"] == "ultra"
            assert dispatch["fork_turns"] == "none"
            assert dispatch["actual_tool_request_message_equals_frozen_file_text"] is True
            validator.check_binding(dispatch["fixed_request"])
            assert dispatch["fixed_request"] == binding(folder / "dispatch-request.txt")
            receipt_path = folder / f"root-attempt-reception-{number:04d}-v2.json"
            receipt = validator.load_strict(receipt_path)
            assert receipt["actor_completion_received_by_ROOT"] is True
            for item in receipt["attempt_files"]:
                validator.check_binding(item)
            for key in ("assignment", "fixed_dispatch_request", "validator"):
                validator.check_binding(receipt[key])
            expected = "technical_valid_whole_batch" if number == selected else "technical_invalid_whole_batch"
            assert receipt["state"] == expected
            assert receipt["reference_or_accuracy_comparison_performed"] is False
            attempts.append({"batch_id": folder.name, "attempt_number": number,
                             "assigned_records_N": validation["record_N"], "state": expected,
                             "dispatch": binding(dispatch_path), "technical_reception": binding(receipt_path),
                             "original_attempt_files": receipt["attempt_files"],
                             "error": receipt.get("error"), "selected": number == selected})
        selections.append({"selection": binding(selection_path), "assignment": binding(assignment_path),
                           "selected_whole_first": selection["original_whole_batch_first"],
                           "record_N": validation["record_N"]})
    assert ordered_ids == manifest["global_order"]
    assert len(ordered_ids) == len(set(ordered_ids)) == 77
    events_path = ROOT / "logs/native-v17-dispatch-events.jsonl"
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    successes = [event for event in events if event["event"] == "actual_coding_actor_spawn_tool_success"]
    assert len(successes) == len(attempts)
    assert {event["runtime_task_name"] for event in successes} == {
        validator.load_strict(item["dispatch"]["path"])["runtime_task_name"] for item in attempts}
    failures = [item for item in attempts if not item["selected"]]
    value = {"artifact_type": "actual_native_v17_complete_campaign_technical_audit_before_comparison",
             "observed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "run_id": "native-llm77-v17-sol", "context_unit": "batch",
             "assigned_batch_N": 13, "unique_records_N": 77, "selected_valid_batch_N": 13,
             "actual_actor_attempt_N": len(attempts),
             "actual_assigned_record_attempt_N": sum(item["assigned_records_N"] for item in attempts),
             "actual_technical_invalid_whole_batch_attempt_N": len(failures),
             "actual_technical_retry_actor_N": len(attempts) - 13,
             "terminal_failed_batches_N": 0,
             "spawn_tool_failure_events_N": sum(event["event"] == "actual_coding_actor_spawn_tool_failure" for event in events),
             "spawn_errors_are_coding_attempts": False,
             "ROOT_administrative_receiver_v1_error_is_coding_failure": False,
             "attempts_are_independent_repeat_runs": False,
             "cross_attempt_record_rescue": False, "label_based_selection": False,
             "reference_or_accuracy_comparison_started": False,
             "is_heldout_formal_accuracy_validation": False,
             "provider_wire_capture_claimed": False, "actual_model_identity_independently_verified": False,
             "actual_read_presentations_independently_verified": False,
             "first_definition": "Original UTF8 bytes of native actor first complete structured whole-batch submission",
             "frozen_manifest": binding(NATIVE / "run-manifest.json"),
             "frozen_before_dispatch_seal": binding(NATIVE / "before-dispatch-seal.json"),
             "frozen_input_seal": binding(NATIVE / "frozen-inputs-seal.json"),
             "frozen_validator": binding(validator_path), "dispatch_events": binding(events_path),
             "metric_driver_before_comparison": binding(ROOT / "logs/native-v17-rule-v19-metric-driver-before-comparison-20261010.json"),
             "retained_administrative_erratum": binding(ROOT / "logs/native-v17-ROOT-receiver-template-flag-erratum-20261010.json"),
             "selections": selections, "all_actual_attempts": attempts,
             "auditing_script": binding(__file__)}
    with OUT.open("x", encoding="utf8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"audit": str(OUT), "actual_attempts_N": len(attempts),
                      "record_attempts_N": value["actual_assigned_record_attempt_N"],
                      "invalid_whole_batch_attempts_N": len(failures)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
