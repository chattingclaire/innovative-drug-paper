#!/usr/bin/env python3
"""Build ten synthetic full-entry inputs without copying expected labels."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
SOURCE = (FIXTURES / "合成机制控制-非政府文件.txt").resolve()
CANDIDATE = (FIXTURES / "合成机制控制-非政府文件.candidate.json").resolve()
CONTROLS = HERE / "构造控制.jsonl"
OUTPUT = HERE / "完整入口输入10.jsonl"
SOURCE_SHA256 = "2515890a161cb741ba8547df19124a838b83f514b5f7791f88bc57f56ff3adae"
CANDIDATE_SHA256 = "e398e7b411c39e2882b0e230d10d4d14f7447ae2266766eabb7f14a5f29d9a26"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert sha(SOURCE) == SOURCE_SHA256
    assert sha(CANDIDATE) == CANDIDATE_SHA256
    controls = [json.loads(line) for line in CONTROLS.read_text().splitlines() if line.strip()]
    candidate = json.loads(CANDIDATE.read_text())
    assert candidate["status"] == "synthetic_not_policy_not_human_validation"
    assert candidate["source"] == str(SOURCE) and candidate["source_sha256"] == SOURCE_SHA256
    paragraphs = {row["id"]: row for row in candidate["paragraphs"]}
    units = {row["id"]: row for row in candidate["unit_candidates"]}
    rows = []
    for index, control in enumerate(controls, 1):
        suffix = f"{index:02d}"
        unit_id = f"syn_u{suffix}"
        unit = units[unit_id]
        assert unit["text"] == control["input"]["unit_text"]
        heading = paragraphs[f"p{suffix}00"]
        preceding = paragraphs[f"p{suffix}01"]
        current = paragraphs[f"p{suffix}02"]
        assert current["text"] == unit["text"]
        context = [preceding, current]
        shared = {
            "paragraph_context": context,
            "nearest_preceding_heading": heading,
            "immediately_preceding_paragraph": preceding,
            "verified_parent_context": [],
            "verified_scope_qualifications_v28": [],
            "content_role": "synthetic_development_fixture",
            "content_role_basis": "本地合成机制控制；非政府文件，非人工效度样本。",
            "verified_context_certificates": {},
            "structured_following_units": [],
        }
        code_input = {
            "review_id": f"synthetic_fixture:{unit_id}",
            "original_file_stem": "SYNTHETIC-NOT-POLICY-implementation-controls",
            "source": str(SOURCE),
            "source_sha256": SOURCE_SHA256,
            "candidate_sha256": CANDIDATE_SHA256,
            "candidate_file": str(CANDIDATE),
            "unit_id": unit_id,
            "unit_text": unit["text"],
            "pages": [],
            "unit_type": "synthetic_prose_candidate",
            "paragraph_context": context,
            "nearest_preceding_heading": heading,
            "immediately_preceding_paragraph": preceding,
            "context_usage": "合成开发控制的完整本地语境；不作政策证据，不自动继承标题或前句标签。",
            "status": "synthetic_unlabelled_development_fixture",
            "content_role": "synthetic_development_fixture",
            "content_role_basis": "本地合成机制控制；非政府文件，非人工效度样本。",
            "unit_source": str(SOURCE),
            "unit_source_sha256": SOURCE_SHA256,
            "count_as_analysis_unit": True,
            "llm_v29_shared_context": shared,
        }
        rows.append({"id": control["id"], "original_id": code_input["review_id"],
                     "input": code_input})
    assert len(rows) == len({row["id"] for row in rows}) == 10
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    if OUTPUT.exists():
        assert OUTPUT.read_text() == payload, "Refusing to replace a differing fixture input"
    else:
        OUTPUT.write_text(payload)
    print(json.dumps({"n": len(rows), "output": str(OUTPUT.resolve()),
                      "output_sha256": sha(OUTPUT), "expected_labels_in_input": False},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
