"""Isolated exact source-material correction; no labels, models or coders.

Inputs are fixed by SHA. Only the already visually reviewed unit/paragraph and
explicit candidate identity links may change. Unchanged JSONL lines are copied
byte for byte; old files are never overwritten.
"""
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def ptr_child(pointer, key):
    return pointer + "/" + str(key).replace("~", "~0").replace("/", "~1")


def leaves(value, pointer=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, ptr_child(pointer, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, ptr_child(pointer, index))
    else:
        yield pointer, value


def transform(value, substitutions, changes, pointer=""):
    if isinstance(value, dict):
        return {k: transform(v, substitutions, changes, ptr_child(pointer, k)) for k, v in value.items()}
    if isinstance(value, list):
        return [transform(v, substitutions, changes, ptr_child(pointer, i)) for i, v in enumerate(value)]
    if isinstance(value, str) and value in substitutions:
        replacement, kind = substitutions[value]
        changes.append({"json_pointer": pointer, "change_kind": kind,
                        "before": value, "after": replacement,
                        "before_text_sha256": text_sha(value), "after_text_sha256": text_sha(replacement)})
        return replacement
    return value


def verify_semantic_diff(before, after, expected_changes):
    b, a = dict(leaves(before)), dict(leaves(after))
    assert set(b) == set(a), "No structure/key/list-length change is permitted"
    changed = {p: (b[p], a[p]) for p in b if b[p] != a[p]}
    expected = {c["json_pointer"]: (c["before"], c["after"]) for c in expected_changes}
    assert changed == expected
    # Every primitive not explicitly logged remains exact, including all status,
    # authentication, metadata opinions, other sources, and positional fields.


def write_json_new(path, data):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def build():
    design_path = HERE / "material_revision_design01.json"
    audit_path = HERE / "old_occurrence_audit01.json"
    design, audit = json.loads(design_path.read_text()), json.loads(audit_path.read_text())
    edit = design["permitted_edit"]
    rule_path = Path(design["rule_input"]["path"])
    llm_path = Path(design["llm_input_candidate"]["path"])
    candidate_path = Path(audit["candidate"]["path"])
    txt_path = Path(audit["generic_txt"]["path"])
    original_hashes = {str(rule_path): design["rule_input"]["sha256"],
        str(llm_path): design["llm_input_candidate"]["sha256"],
        str(candidate_path): audit["candidate"]["sha256"], str(txt_path): audit["generic_txt"]["sha256"],
        design["image_evidence"]["path"]: design["image_evidence"]["sha256"],
        design["image_evidence"]["independent_transcripts_path"]: design["image_evidence"]["independent_transcripts_sha256"]}
    assert all(sha(p) == s for p, s in original_hashes.items())
    # No image-derived paragraph occurs in the generic TXT: never insert it or
    # pretend that a derived image transcription was a literal TXT paragraph.
    generic = txt_path.read_text()
    assert all(generic.count(edit[k]) == 0 for k in ("old_phrase", "old_unit_exact", "old_paragraph_exact"))
    substitutions = {
        edit["old_unit_exact"]: (edit["new_unit_expected"], "source_phrase_correction"),
        edit["old_paragraph_exact"]: (edit["new_paragraph_expected"], "source_phrase_correction")}
    for old, (new, _) in substitutions.items():
        assert old.count(edit["old_phrase"]) == 1
        assert new == old.replace(edit["old_phrase"], edit["new_phrase"])
    candidate = json.loads(candidate_path.read_text())
    candidate_changes = []
    revised_candidate = transform(candidate, substitutions, candidate_changes)
    assert {c["json_pointer"] for c in candidate_changes} == {m["pointer"] for m in audit["candidate"]["target_matches"]}
    assert len(candidate_changes) == 4
    verify_semantic_diff(candidate, revised_candidate, candidate_changes)
    assert not any(isinstance(v, str) and edit["old_phrase"] in v for _, v in leaves(revised_candidate))
    sources = HERE / "derived_sources"
    sources.mkdir(exist_ok=False)
    revised_candidate_path = sources / "NHC-全面提升医疗质量行动-2023-image03-corrected01.json"
    write_json_new(revised_candidate_path, revised_candidate)
    revised_candidate_sha = sha(revised_candidate_path)
    substitutions[str(candidate_path)] = (str(revised_candidate_path), "candidate_path_rebinding")
    substitutions[audit["candidate"]["sha256"]] = (revised_candidate_sha, "candidate_sha256_rebinding")

    all_changes, outputs, before_rows, after_rows = [], {}, {}, {}
    for kind, input_path, output_name in (
        ("rule", rule_path, "rule_inputs_shared_material_revision01.jsonl"),
        ("llm", llm_path, "effective_blind_inputs_material_revision01.jsonl")):
        output_path = HERE / output_name
        records_before, records_after, changed_ids = [], [], []
        untouched_line_n = 0
        with output_path.open("xb") as sink:
            for line_no, original_line in enumerate(input_path.read_bytes().splitlines(keepends=True), 1):
                old = json.loads(original_line)
                changes = []
                new = transform(old, substitutions, changes)
                verify_semantic_diff(old, new, changes)
                records_before.append(old)
                records_after.append(new)
                if changes:
                    changed_ids.append(old["id"])
                    sink.write((json.dumps(new, ensure_ascii=False) + "\n").encode())
                    all_changes.extend({"input_kind": kind, "id": old["id"], "line": line_no, **c} for c in changes)
                else:
                    untouched_line_n += 1
                    sink.write(original_line)
        assert len(records_before) == len(records_after) == 4924
        assert [r["id"] for r in records_before] == [r["id"] for r in records_after]
        assert len({r["id"] for r in records_after}) == 4924
        assert not any(isinstance(v, str) and edit["old_phrase"] in v for r in records_after for _, v in leaves(r))
        before_rows[kind], after_rows[kind] = records_before, records_after
        outputs[kind] = {"path": str(output_path), "sha256": sha(output_path), "n": len(records_after),
                         "changed_record_n": len(changed_ids), "changed_ids": changed_ids,
                         "unchanged_lines_byte_copied_n": untouched_line_n}

    for stage, rows in (("before", before_rows), ("after", after_rows)):
        assert [r["id"] for r in rows["rule"]] == [r["id"] for r in rows["llm"]]
        for rule, llm in zip(rows["rule"], rows["llm"]):
            assert rule["input"]["unit_text"] == llm["text"]
            assert rule["input"]["llm_v29_shared_context"] == llm["contexts"]
    expected_text_counts = {"rule": 5, "llm": 3}
    for kind in expected_text_counts:
        text_changes = [c for c in all_changes if c["input_kind"] == kind and c["change_kind"] == "source_phrase_correction"]
        assert len(text_changes) == expected_text_counts[kind]
        assert {(c["id"], c["json_pointer"]) for c in text_changes} == {(c["id"], c["pointer"]) for c in audit["input_target_matches"][kind]}
    candidate_ref_ids = {x["id"] for x in audit["all_explicit_candidate_txt_references"]["rule"] if x["reference_kind"] == "candidate_path"}
    rebound_ids = set()
    for row in after_rows["rule"]:
        inp = row["input"]
        if inp.get("candidate_file") == str(revised_candidate_path):
            assert inp["candidate_sha256"] == revised_candidate_sha
            rebound_ids.add(row["id"])
    assert rebound_ids == candidate_ref_ids and len(rebound_ids) == 131
    assert all(sha(p) == s for p, s in original_hashes.items())
    result = {"at_utc": datetime.now(timezone.utc).isoformat(),
        "design_sha256": sha(design_path), "pre_revision_occurrence_audit_sha256": sha(audit_path),
        "builder_sha256": sha(__file__), "ai_visual_evidence": design["image_evidence"],
        "identity": design["identity"],
        "derived_candidate": {"path": str(revised_candidate_path), "sha256": revised_candidate_sha,
                              "original_path": str(candidate_path), "original_sha256": audit["candidate"]["sha256"],
                              "text_field_changes": candidate_changes},
        "generic_txt": {"path": str(txt_path), "sha256": sha(txt_path), "derived_copy_created": False,
                        "reason": "exact old unit/paragraph/phrase absent; unit source remains actual PNG; no guessed TXT supplementation"},
        "output_inputs": outputs, "input_changes": all_changes,
        "checks": {"both_methods_4924_ordered_unique_ids_preserved": True,
                   "both_methods_current_equal_all_4924_before_and_after": True,
                   "both_methods_shared_context_equal_all_4924_before_and_after": True,
                   "all_131_candidate_links_consistently_rebound": True,
                   "all_unlogged_values_and_structure_exactly_unchanged": True,
                   "other_source_links_and_generic_txt_unchanged": True,
                   "authentication_flags_not_promoted_or_changed": True,
                   "old_phrase_no_longer_present_in_derived_candidate_or_inputs": True,
                   "original_files_unchanged": True},
        "original_files_sha256_after": original_hashes,
        "no_labels_read_or_modified": True, "no_coder_or_model_executed": True,
        "new_actual_source_authentication_claim": False,
        "formal_input_readiness_claim": False,
        "status": "isolated shared-material revision only; awaiting root and independent08 review"}
    write_json_new(HERE / "material_revision_result01.json", result)
    return result


if __name__ == "__main__":
    result = build()
    print(json.dumps({"candidate_sha256": result["derived_candidate"]["sha256"],
        "outputs": {k: {f: v[f] for f in ("path", "sha256", "n", "changed_record_n")} for k, v in result["output_inputs"].items()},
        "candidate_text_change_n": len(result["derived_candidate"]["text_field_changes"]),
        "rule_text_change_n": sum(c["input_kind"] == "rule" and c["change_kind"] == "source_phrase_correction" for c in result["input_changes"]),
        "llm_text_change_n": sum(c["input_kind"] == "llm" and c["change_kind"] == "source_phrase_correction" for c in result["input_changes"]),
        "result_sha256": sha(HERE / "material_revision_result01.json")}, ensure_ascii=False))
