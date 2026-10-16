"""Only invented fixtures; reproduce the three independent static findings.

Run with the bundled Python -B. Actual temporary source/candidate files and
the unchanged real source authenticator are used. No policy inputs are read.
"""
from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "runtime"))
from selftest_common_if_extensions03 import prose
from common_if_current_relations05 import inspect_current_relations


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def one(root, name, previous, current, fallback=False):
    record = prose(root / name, current, prefix=previous)
    if fallback:
        Path(record["source"]).write_text(
            current + "本合成来源没有所声称的前句范围。", encoding="utf-8")
        record["source_sha256"] = record["unit_source_sha256"] = file_sha(record["source"])
        record["paragraph_context"][0]["verification"] = {
            "verified": True, "method": "self_asserted_negative_fixture"}
        record["llm_v29_shared_context"]["paragraph_context"] = copy.deepcopy(record["paragraph_context"])
    before = copy.deepcopy(record)
    error = None
    evidence = None
    try:
        evidence = inspect_current_relations(record, {})
    except ValueError as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
    assert record == before
    if fallback:
        assert error and "requires actual literal or layout source reproduction" in error["message"]
        assert evidence is None
    else:
        assert error is None and evidence == []
    source = Path(record["source"]).read_text(encoding="utf-8")
    return {
        "name": name,
        "invented_previous_sentence": previous,
        "invented_current_unit": current,
        "source_contains_current_unit": current in source,
        "source_contains_claimed_full_paragraph": record["paragraph_context"][0]["text"] in source,
        "source_sha256": file_sha(record["source"]),
        "candidate_sha256": file_sha(record["candidate_file"]),
        "source_authenticators_mocked": False,
        "actual_evidence": evidence,
        "explicit_source_error": error,
        "silent_zero_on_source_failure": False,
        "record_unchanged": True,
        "passed": True,
    }


def main():
    with tempfile.TemporaryDirectory(prefix="static-fix05-only-invented-") as tmp:
        folder = Path(tmp)
        cases = [
            one(folder, "evaluation_topic_switch", "此前仅存档药品的创新性评价，现转入设备评价工作。",
                "开展创新性评价，应当说明评价依据。"),
            one(folder, "numeric_channel_topic_switch", "药品审批机制另行规定，本款仅涉及物流配送通道。",
                "创新药品种将纳入18日通道。"),
            one(folder, "nonliteral_self_reported_certificate", "药品的创新性评价应当依法开展。",
                "开展创新性评价，应当说明评价依据。", True),
        ]
    print(json.dumps({"synthetic_only": True, "cases": cases, "passed": True,
                      "real_policy_units_executed": 0, "reference_labels_loaded": False,
                      "authenticators_mocked": False, "full_pipeline_executed": False},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
