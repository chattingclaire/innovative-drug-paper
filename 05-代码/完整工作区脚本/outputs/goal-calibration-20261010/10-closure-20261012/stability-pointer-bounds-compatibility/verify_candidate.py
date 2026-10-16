"""Print pure read-only checks. Run with python -B; never receives or dispatches."""
import datetime as dt
import importlib.util
import json
import sys
import traceback

sys.dont_write_bytecode = True
import adapter


def outcome(function, packet, pointer):
    try:
        return {"kind": "return", "value": function(packet, pointer)}
    except Exception as error:
        return {"kind": "error", "type": type(error).__name__, "message": str(error)}


def main():
    document = adapter.manifest()
    bound = [value for value in document.values()
             if isinstance(value, dict) and set(value) == {"path", "bytes", "sha256"}]
    for expected in bound:
        adapter.check(expected)
    before = {item["path"]: adapter.binding(item["path"]) for item in bound}
    spec = importlib.util.spec_from_file_location("original_pointer_bounds_control", document["original_validator"]["path"])
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    candidate = adapter.load_readonly_validator()
    cases = [
        ("legal_first", {"x": ["first", "last"]}, "/x/0", False),
        ("legal_last", {"x": ["first", "last"]}, "/x/1", False),
        ("nested_escaped_key", {"a/b": [{"~key": "yes"}]}, "/a~1b/0/~0key", False),
        ("index_equal_length", {"x": ["first", "last"]}, "/x/2", True),
        ("index_above_length", {"x": ["first", "last"]}, "/x/11", True),
        ("empty_array", {"x": []}, "/x/0", True),
        ("missing_key", {"x": []}, "/missing/0", False),
        ("negative_index", {"x": [1]}, "/x/-1", False),
        ("leading_zero_index", {"x": [1]}, "/x/00", False),
        ("nonnumeric_index", {"x": [1]}, "/x/foo", False),
        ("invalid_pointer", {"x": [1]}, "x/0", False),
        ("scalar_traversal", {"x": 3}, "/x/0", False),
    ]
    class UnrelatedListError(list):
        def __getitem__(self, key):
            raise IndexError("unrelated internal error")
    cases.append(("unrelated_IndexError_preserved", {"x": UnrelatedListError([1])}, "/x/0", False))
    rows = []
    for name, packet, pointer, expected_conversion in cases:
        left = outcome(original.pointer_value, packet, pointer)
        right = outcome(candidate.pointer_value, packet, pointer)
        passed = ((left.get("type") == "IndexError" and right.get("type") == "ValueError")
                  if expected_conversion else left == right)
        rows.append({"case": name, "original": left, "candidate": right, "passed": passed})
        assert passed, name
    real = []
    for label, module in (("original", original), ("candidate", candidate)):
        try:
            module.verify(document["real_assignment"]["path"], document["real_first"]["path"])
            result = {"validator": label, "returned": True}
        except Exception as error:
            result = {"validator": label, "error_type": type(error).__name__,
                      "error_message": str(error), "traceback": traceback.format_exc()}
        real.append(result)
    assert real[0].get("error_type") == "IndexError"
    assert real[1].get("error_type") == "ValueError"
    assert "contexts/11/title" in real[1]["error_message"]
    valid_original = original.verify(document["valid_control_assignment"]["path"], document["valid_control_first"]["path"])
    valid_candidate = candidate.verify(document["valid_control_assignment"]["path"], document["valid_control_first"]["path"])
    assert valid_original == valid_candidate
    common_spec = importlib.util.spec_from_file_location("readonly_transport_loader_control", document["original_transport_common"]["path"])
    common = importlib.util.module_from_spec(common_spec)
    common_spec.loader.exec_module(common)
    loader = adapter.wrap_receiver_module_loader(common.module)
    preflight = loader(document["original_validator"], "receiver_runtime_preflight")
    captured = loader(document["original_validator"], "unchanged_production_validator_capture")
    assert preflight.pointer_value.__code__.co_filename == document["original_validator"]["path"]
    assert captured.pointer_value.__code__.co_filename == str(adapter.HERE / "adapter.py")
    assert outcome(preflight.pointer_value, {"x": []}, "/x/0")["type"] == "IndexError"
    assert outcome(captured.pointer_value, {"x": []}, "/x/0")["type"] == "ValueError"
    after = {item["path"]: adapter.binding(item["path"]) for item in bound}
    assert before == after
    print(json.dumps({
        "at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "candidate_only": True, "all_checks_passed": True, "boundary_cases": rows,
        "real_H0041_pure_validation": real, "original_bindings_before": before,
        "valid_whole_batch_control": {"original": valid_original, "candidate": valid_candidate, "identical": True},
        "module_loader_control": {"original_loader_runs": True, "preflight_module_unchanged": True, "exact_capture_validator_adapted": True},
        "original_bindings_after": after, "original_files_unchanged": True,
        "model_calls": 0, "receiving_calls": 0, "lock_acquisitions": 0,
        "campaign_file_writes": 0, "retry_limit_changed": False,
        "execution_authorized_by_this_candidate": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
