"""Compare only 14 approved PNG units with separately frozen AI visual text.

No coding labels, coding reasons, prior visually_checked flags or candidate
documents are loaded. Punctuation is never stripped or conflated by category.
"""
import difflib
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = HERE.parents[3] / "coding-revision-20261007-r3/rule_inputs_shared_v14.jsonl"
PUNCTUATION_MAP = {"，": ",", "；": ";", "：": ":", "（": "(", "）": ")", "％": "%"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(text):
    chars, offsets, whitespace = [], [], []
    for index, char in enumerate(text):
        if char.isspace():
            whitespace.append({"offset": index, "character": char, "codepoint": f"U+{ord(char):04X}"})
        else:
            chars.append(PUNCTUATION_MAP.get(char, char))
            offsets.append(index)
    return "".join(chars), offsets, whitespace


def comparison(actual, visual):
    left, li, lw = normalize(actual)
    right, ri, rw = normalize(visual)
    mismatches, punctuation = [], []
    for tag, a, b, c, d in difflib.SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
        if tag == "equal":
            for j, k in zip(range(a, b), range(c, d)):
                if actual[li[j]] != visual[ri[k]]:
                    punctuation.append({"input_offset": li[j], "visual_offset": ri[k],
                        "input_character": actual[li[j]], "visual_character": visual[ri[k]],
                        "mapped_character": left[j],
                        "input_codepoint": f"U+{ord(actual[li[j]]):04X}",
                        "visual_codepoint": f"U+{ord(visual[ri[k]]):04X}"})
        else:
            mismatches.append({"operation_input_to_visual": tag,
                "input_normalized_span": [a, b], "visual_normalized_span": [c, d],
                "input_characters": left[a:b], "visual_characters": right[c:d],
                "input_context": left[max(0, a-12):min(len(left), b+12)],
                "visual_context": right[max(0, c-12):min(len(right), d+12)]})
    return {"input_text": actual, "visual_text": visual, "raw_exact": actual == visual,
            "allowed_normalization_equal": left == right,
            "input_text_sha256": hashlib.sha256(actual.encode()).hexdigest(),
            "visual_text_sha256": hashlib.sha256(visual.encode()).hexdigest(),
            "normalized_input_sha256": hashlib.sha256(left.encode()).hexdigest(),
            "normalized_visual_sha256": hashlib.sha256(right.encode()).hexdigest(),
            "substantive_character_differences": mismatches,
            "punctuation_equivalences": punctuation,
            "input_whitespace_mapping": lw, "visual_whitespace_mapping": rw}


def run():
    transcript_path = HERE / "independent_transcripts01.json"
    transcripts = json.loads(transcript_path.read_text())
    by_name = {Path(t["image_path"]).name: t for t in transcripts["images"]}
    before_input = sha(INPUT)
    selected = []
    # Parse current rows solely to select the five exact unit_source filenames.
    # Do not print or retain other current/paragraph text.
    for line_no, line in enumerate(INPUT.open(), 1):
        row = json.loads(line)
        record = row["input"]
        name = Path(record.get("unit_source", "")).name
        if name in by_name:
            selected.append((line_no, row["id"], record, name))
    assert len(selected) == 14
    images, rows = [], []
    for name, transcript in by_name.items():
        image_rows = [r for r in selected if r[3] == name]
        body = transcript["body_without_visual_linebreaks"]
        sentences = [m for m in re.finditer(r"[^。]+。", body)]
        assert "".join(s.group() for s in sentences) == body
        assert len(sentences) == len(image_rows)
        image_hash_matches = sha(transcript["image_path"]) == transcript["image_sha256"]
        assert image_hash_matches
        for sentence, (line_no, rid, record, _) in zip(sentences, image_rows):
            unit = comparison(record["unit_text"], sentence.group())
            paragraphs = []
            for index, paragraph in enumerate(record["paragraph_context"]):
                paragraphs.append({"json_pointer": f"/input/paragraph_context/{index}/text",
                                   "paragraph_id": paragraph.get("paragraph_id"),
                                   "comparison": comparison(paragraph["text"], body)})
            shared = record.get("llm_v29_shared_context", {})
            shared_paragraphs = []
            for index, paragraph in enumerate(shared.get("paragraph_context", [])):
                shared_paragraphs.append({"json_pointer": f"/input/llm_v29_shared_context/paragraph_context/{index}/text",
                                         "paragraph_id": paragraph.get("paragraph_id"),
                                         "comparison": comparison(paragraph["text"], body)})
            # Heading fields are the only title-carrying fields inspected here.
            heading = record.get("nearest_preceding_heading")
            shared_heading = shared.get("nearest_preceding_heading")
            assert heading is None and shared_heading is None
            rows.append({"id": rid, "input_line": line_no, "image_path": transcript["image_path"],
                "image_sha256": transcript["image_sha256"], "whole_image_region_xyxy": transcript["review_region_xyxy"],
                "declared_unit_source_sha256": record["unit_source_sha256"],
                "declared_image_byte_hash_matches": record["unit_source_sha256"] == transcript["image_sha256"],
                "unit_pointer": "/input/unit_text", "unit_comparison": unit,
                "source_sentence_span_in_transcribed_body": [sentence.start(), sentence.end()],
                "alignment": "within each exact image, ordered full-stop-delimited visual sentences matched to input order; counts must agree; all punctuation retained",
                "paragraph_comparisons": paragraphs, "shared_paragraph_comparisons": shared_paragraphs,
                "source_title": transcript["title"],
                "title_binding_in_inspected_fields": {"nearest_preceding_heading": None,
                    "shared_nearest_preceding_heading": None,
                    "title_in_current_or_paragraph_fields": any(normalize(transcript["title"])[0] in normalize(t)[0]
                        for t in [record["unit_text"]] + [p["text"] for p in record["paragraph_context"]]),
                    "status": "actual_image_title_transcribed_but_absent_from_inspected_current_paragraph_heading_fields"}})
        images.append({"image_path": transcript["image_path"], "image_sha256": transcript["image_sha256"],
                       "title": transcript["title"], "unit_ids": [r[1] for r in image_rows],
                       "visual_sentence_n": len(sentences), "image_hash_unchanged": image_hash_matches})
    assert sha(INPUT) == before_input
    return {"schema_version": "selected-png-visual-transcription-comparison01", "at_utc": datetime.now(timezone.utc).isoformat(),
        "reviewer_identity": "AI代理 /root/autocode_error_audit，非真人或人工金标准",
        "input_path": str(INPUT), "input_sha256_before_and_after": before_input,
        "transcript_path": str(transcript_path), "transcript_sha256": sha(transcript_path),
        "comparison_code_sha256": sha(__file__),
        "normalization": {"explicit_character_map": PUNCTUATION_MAP, "whitespace": "only str.isspace characters map to empty; each event is recorded",
            "not_used": "no punctuation deletion; no Chinese word substitution; no general NFKC; no semantic matching"},
        "images": images, "rows": rows,
        "summary": {"images_actually_viewed": 5, "selected_unit_n": 14,
            "unit_normalized_equal_n": sum(r["unit_comparison"]["allowed_normalization_equal"] for r in rows),
            "paragraph_normalized_equal_n": sum(p["comparison"]["allowed_normalization_equal"] for r in rows for p in r["paragraph_comparisons"]),
            "shared_paragraph_normalized_equal_n": sum(p["comparison"]["allowed_normalization_equal"] for r in rows for p in r["shared_paragraph_comparisons"]),
            "titles_absent_from_inspected_heading_fields_n": 5,
            "all_declared_image_byte_hashes_match": all(r["declared_image_byte_hash_matches"] for r in rows)},
        "limits": "Actual full images visually read, then text compared. Full-image region binding, not per-glyph boxes; AI visual evidence is not human certification. No dimension decisions, no input rewriting, no certification of uninspected fields."}


if __name__ == "__main__":
    result = run()
    path = HERE / "selected14_comparison01.json"
    with path.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"path": str(path), "sha256": sha(path), "summary": result["summary"],
                      "unit_mismatch_ids": [r["id"] for r in result["rows"] if not r["unit_comparison"]["allowed_normalization_equal"]]}, ensure_ascii=False))
