"""Read-only, non-semantic validation of a native v17 whole-batch submission."""
import argparse
import hashlib
import json
from pathlib import Path

import jsonschema


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def reject_nonfinite(value):
    raise ValueError(f"Non-finite JSON number: {value}")


def load_strict(path):
    return json.loads(
        Path(path).read_bytes().decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_nonfinite,
    )


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_binding(item):
    path = Path(item["path"])
    assert path.is_absolute() and path.is_file(), "Missing bound input"
    assert type(item["bytes"]) is int and path.stat().st_size == item["bytes"], "Input byte mismatch"
    assert digest(path) == item["sha256"], "Input SHA mismatch"


def pointer_value(packet, pointer):
    assert isinstance(pointer, str) and pointer.startswith("/"), "Invalid packet JSON pointer"
    current = packet
    for part in pointer[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            assert part.isdigit() and str(int(part)) == part, "Invalid array pointer index"
            current = current[int(part)]
        else:
            current = current[part]
    return current


def covers(intervals, start, end):
    cursor = start
    for left, right in sorted(intervals):
        if left > cursor:
            return False
        cursor = max(cursor, right)
    return cursor >= end


def verify(assignment_path, submission_path):
    assignment_path = Path(assignment_path).resolve()
    submission_path = Path(submission_path).resolve()
    assignment = load_strict(assignment_path)
    directory = Path(assignment["output_directory"]).resolve()
    assert assignment_path == directory / "assignment.json", "Assignment output directory mismatch"
    assert directory in submission_path.parents, "Submission outside its assigned output directory"
    schema_binding = assignment["output_schema"]
    required_inputs = [assignment[k] for k in ("manual", "execution_prompt", "actor_instructions", "packet_schema", "output_schema", "output_validation_contract", "strict_technical_validator", "read_manifest_template", "response_retention_policy", "output_seal_template", "technical_failure_template", "run_scope_binding", "legacy_locator_alias_table_binding", "delivery_manifest_order_metadata_only", "attempt_output_routing")]
    for item in [*required_inputs, *assignment["packets"], *assignment["source_asset_bindings"]]:
        check_binding(item)
    first = load_strict(submission_path)
    schema = load_strict(schema_binding["path"])
    jsonschema.Draft202012Validator(schema).validate(first)
    for key in ("run_id", "batch_id", "requested_model", "requested_reasoning_effort", "context_unit", "scope"):
        assert first[key] == assignment[key], f"Top-level {key} mismatch"
    assert first["manual_binding"] == assignment["manual"], "Top-level manual binding mismatch"
    assert first["execution_prompt_binding"] == assignment["execution_prompt"], "Top-level execution prompt binding mismatch"
    records = first["records"]
    assert len(records) == assignment["expected_N"], "Whole-batch record count mismatch"
    assert [record["source_id"] for record in records] == assignment["source_ids"], "Whole-batch record coverage/order mismatch"
    packet_bindings = {item["source_id"]: item for item in assignment["packets"]}
    source_ids = set(assignment["source_ids"])
    asset_bindings = {item["path"]: item for item in assignment["source_asset_bindings"]}
    for record in records:
        packet_binding = packet_bindings[record["source_id"]]
        assert record["output_id"] == packet_binding["output_id"], "Record output identity mismatch"
        assert record["packet_sha256"] == packet_binding["sha256"], "Record packet identity mismatch"
        packet = load_strict(packet_binding["path"])
        assert set(record["dimensions"]) == {"S", "E", "Ec", "I", "F"}, "Dimension coverage mismatch"
        for decision in record["dimensions"].values():
            value = decision["value"]
            assert value is None or type(value) is int and value in (0, 1), "Value must be exact integer 0/1 or null; bool/float rejected"
            assert decision["reason"].strip(), "Empty reason"
            for evidence in decision["evidence"]:
                if "pointer" in evidence:
                    field = pointer_value(packet, evidence["pointer"])
                    assert isinstance(field, str) and evidence["quote"] and evidence["quote"] in field, "Packet exact quote mismatch"
                else:
                    asset = asset_bindings.get(evidence["asset_path"])
                    assert asset and evidence["asset_sha256"] == asset["sha256"], "Supplemental asset outside frozen assignment"
                    assert record["source_id"] in asset["source_ids"], "Supplemental asset outside record source binding"
    allowed_reads = {item["path"]: item for item in [*required_inputs, *assignment["packets"], *assignment["source_asset_bindings"]]}
    allowed_reads[str(assignment_path)] = {"path": str(assignment_path), "bytes": assignment_path.stat().st_size, "sha256": digest(assignment_path)}
    presented = {}
    for entry in first["read_manifest"]["files"]:
        bound = allowed_reads.get(entry["path"])
        assert bound and all(entry[k] == bound[k] for k in ("path", "bytes", "sha256")), "Unbound read-manifest identity"
        assert set(entry["source_ids"]) <= source_ids, "Read-manifest source IDs outside batch"
        assert entry["not_truncated"] is True and entry["read_method"].strip(), "Read-manifest must record actual bounded presentation"
        for interval in entry["actual_presented_ranges"]:
            assert interval.get("presentation_event", "").strip(), "Missing actual presentation event reference"
            if interval["range_kind"] == "full_image":
                assert interval["start"] is None and interval["end"] is None, "Full image must use null start/end"
            else:
                assert type(interval["start"]) is int and type(interval["end"]) is int, "Noninteger read range"
                assert interval["end"] >= interval["start"], "Inverted read range"
        presented.setdefault(entry["path"], []).extend(entry["actual_presented_ranges"])
    for required in [assignment["manual"], assignment["execution_prompt"], *assignment["packets"]]:
        text = Path(required["path"]).read_bytes().decode("utf-8")
        ranges = presented.get(required["path"], [])
        characters = [(i["start"], i["end"]) for i in ranges if i["range_kind"] == "unicode_code_points"]
        lines = [(i["start"], i["end"] + 1) for i in ranges if i["range_kind"] == "lines"]
        assert all(0 <= left <= right <= len(text) for left, right in characters), "Character range outside file"
        assert all(1 <= left <= right <= len(text.splitlines()) + 1 for left, right in lines), "Line range outside file"
        assert covers(characters, 0, len(text)) or covers(lines, 1, len(text.splitlines()) + 1), "Required whole manual/prompt/packet presentation coverage absent"
    return {
        "state": "technical_valid_whole_batch_submission",
        "run_id": assignment["run_id"],
        "batch_id": assignment["batch_id"],
        "record_N": len(records),
        "context_unit": "batch",
        "submission_bytes": submission_path.stat().st_size,
        "submission_sha256": digest(submission_path),
        "semantic_correctness_checked": False,
        "actual_model_or_tool_presentations_independently_verified": False,
        "provider_wire_capture_claimed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assignment", required=True)
    parser.add_argument("--submission", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.assignment, args.submission), ensure_ascii=False, indent=2))
