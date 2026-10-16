#!/usr/bin/env python3
"""Prepare an exact physical-TXT-line binding for synthetic control 09.

This adds locator metadata only. It creates no policy/authentication claim and
does not run the encoder.
"""

import copy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
ORIGINAL_INPUT = PARENT / "完整入口输入10.jsonl"
ORIGINAL_CANDIDATE = PARENT / "fixtures" / "合成机制控制-非政府文件.candidate.json"
SOURCE = PARENT / "fixtures" / "合成机制控制-非政府文件.txt"
CONTROLS = PARENT / "构造控制.jsonl"
DERIVED_CANDIDATE = HERE / "合成机制控制-09实际TXT源行锚.candidate.json"
DERIVED_INPUT = HERE / "09实际TXT源行锚输入.jsonl"
REPORT = HERE / "准备报告.json"
ORIGINAL_INPUT_SHA = "eb6650ea3cff400c725b157b807abf6a19ef425acc469b2519649c605ca1b031"
ORIGINAL_CANDIDATE_SHA = "e398e7b411c39e2882b0e230d10d4d14f7447ae2266766eabb7f14a5f29d9a26"
SOURCE_SHA = "2515890a161cb741ba8547df19124a838b83f514b5f7791f88bc57f56ff3adae"
CONTROLS_SHA = "05c360a4f3e7c9d5656d4b2d61d24c228a514e8564214e95856ccecf54ef4fdd"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, payload):
    assert not path.exists(), f"refusing overwrite: {path}"
    path.write_text(payload)


def main():
    assert sha(ORIGINAL_INPUT) == ORIGINAL_INPUT_SHA
    assert sha(ORIGINAL_CANDIDATE) == ORIGINAL_CANDIDATE_SHA
    assert sha(SOURCE) == SOURCE_SHA and sha(CONTROLS) == CONTROLS_SHA
    raw_lines = SOURCE.read_text().splitlines()
    original_candidate = json.loads(ORIGINAL_CANDIDATE.read_text())
    derived_candidate = copy.deepcopy(original_candidate)
    physical_lines = {}
    for paragraph in derived_candidate["paragraphs"]:
        positions = paragraph.get("source_lines", [])
        assert positions and all(type(n) is int and 1 <= n <= len(raw_lines) for n in positions)
        assert "".join(raw_lines[n - 1] for n in positions) == paragraph["text"]
        ids = [f"L{n}" for n in positions]
        paragraph["line_ids"] = ids
        for line_id, n in zip(ids, positions):
            item = {"id": line_id, "text": raw_lines[n - 1], "line": n}
            assert line_id not in physical_lines or physical_lines[line_id] == item
            physical_lines[line_id] = item
    derived_candidate["lines"] = [physical_lines[key]
                                  for key in sorted(physical_lines, key=lambda x: int(x[1:]))]
    derived_candidate["method"] = "synthetic_development_fixture_with_actual_txt_line_binding"
    derived_candidate["status"] = "synthetic_not_policy_not_human_validation_locator_repair"
    derived_candidate["notes"] = (original_candidate["notes"] +
        " 本派生件只补入合成TXT逐字物理行锚，不构造认证语义或政策身份。")
    candidate_payload = json.dumps(derived_candidate, ensure_ascii=False, indent=2) + "\n"
    write_new(DERIVED_CANDIDATE, candidate_payload)

    original_rows = [json.loads(line) for line in ORIGINAL_INPUT.read_text().splitlines() if line.strip()]
    original = next(row for row in original_rows if row["id"] == "SYNCTRL-09")
    derived = copy.deepcopy(original)
    candidate_sha = sha(DERIVED_CANDIDATE)
    data = derived["input"]
    data["candidate_file"] = str(DERIVED_CANDIDATE.resolve())
    data["candidate_sha256"] = candidate_sha
    data["status"] = "synthetic_actual_txt_line_anchor_repair_prepared_not_run"
    line_ids = {p["id"]: p["line_ids"] for p in derived_candidate["paragraphs"]}
    for key in ("paragraph_context",):
        for paragraph in data[key]:
            paragraph["line_ids"] = line_ids[paragraph["id"]]
    data["nearest_preceding_heading"]["line_ids"] = line_ids[data["nearest_preceding_heading"]["id"]]
    data["immediately_preceding_paragraph"]["line_ids"] = line_ids[data["immediately_preceding_paragraph"]["id"]]
    shared = data["llm_v29_shared_context"]
    for paragraph in shared["paragraph_context"]:
        paragraph["line_ids"] = line_ids[paragraph["id"]]
    shared["nearest_preceding_heading"]["line_ids"] = line_ids[shared["nearest_preceding_heading"]["id"]]
    shared["immediately_preceding_paragraph"]["line_ids"] = line_ids[shared["immediately_preceding_paragraph"]["id"]]
    assert data.get("verified_parent_context", []) == []
    assert shared["verified_parent_context"] == [] and shared["verified_context_certificates"] == {}
    input_payload = json.dumps(derived, ensure_ascii=False) + "\n"
    assert "expected_labels" not in input_payload
    write_new(DERIVED_INPUT, input_payload)

    expected = next(json.loads(line) for line in CONTROLS.read_text().splitlines()
                    if json.loads(line)["id"] == "SYNCTRL-09")
    report = {
        "kind": "synthetic_control_09_actual_txt_locator_repair_prepared_not_run",
        "source_path": str(SOURCE.resolve()),
        "source_sha256": sha(SOURCE),
        "original_candidate_sha256": sha(ORIGINAL_CANDIDATE),
        "derived_candidate_path": str(DERIVED_CANDIDATE.resolve()),
        "derived_candidate_sha256": sha(DERIVED_CANDIDATE),
        "derived_input_path": str(DERIVED_INPUT.resolve()),
        "derived_input_sha256": sha(DERIVED_INPUT),
        "current_unit_text_unchanged": data["unit_text"] == original["input"]["unit_text"] == expected["input"]["unit_text"],
        "paragraph_context_text_unchanged": [p["text"] for p in data["paragraph_context"]] ==
            [p["text"] for p in original["input"]["paragraph_context"]],
        "heading_text_unchanged": data["nearest_preceding_heading"]["text"] ==
            original["input"]["nearest_preceding_heading"]["text"],
        "expected_labels_unchanged": expected["expected_labels"],
        "expected_labels_absent_from_encoder_input": True,
        "verified_parent_context_empty": True,
        "verified_context_certificates_empty": True,
        "actual_txt_line_bindings": {
            "heading": {"line_ids": ["L35"], "source_lines": [35]},
            "preceding": {"line_ids": ["L36"], "source_lines": [36]},
            "current": {"line_ids": ["L37"], "source_lines": [37]},
        },
        "anticipated_effect_only": ("Removes the candidate line-object absence that caused "
            "'bound source lines absent'; it does not by itself prove that the current pronoun "
            "'该计划' has an authenticated innovative-research object relation."),
        "encoder_run_performed": False,
        "synthetic_not_policy": True,
        "not_human_validation": True,
    }
    write_new(REPORT, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
