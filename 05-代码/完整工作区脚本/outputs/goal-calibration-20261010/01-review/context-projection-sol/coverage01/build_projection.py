"""Rebuild coverage development source contexts without reading any coder submissions.

Only the two source snapshots, frame, source-only provenance sidecar, and
pilot administrative ID list are inputs. Original CTX IDs are retained.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import unicodedata
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BASE = ROOT / "00-baseline"
OLD_BASE = ROOT.parent / "编码修订核查-20261008/LLM编码/统一判据编码准备"
SIDE_PATH = OLD_BASE / "共用纯来源材料02/provenance_with_scope02.jsonl"
MODEL_KEYS = {"context_id", "kind", "source_document", "structure", "text", "headers", "title", "row_cells", "caption"}
STRUCTURE_KEYS = {
    "sequence_index", "paragraph_id", "pages", "source_lines", "relation_id",
    "related_context_ids", "unit_id", "parent_context_id", "candidate_line_ids",
    "first_paragraph", "last_paragraph", "line_ids", "position", "next_paragraph_id",
    "text_child_context_ids", "first_paragraph_id", "last_paragraph_id", "physical_pages",
    "source_role", "component_id", "candidate_paragraph_id", "candidate_paragraph_start",
    "candidate_paragraph_end", "column_index", "table_text_context_ids", "source_unit_id",
    "current_unit_id", "reference_address", "next_candidate_paragraph_id", "article",
    "component_first_paragraph", "component_last_paragraph", "row_index_zero_based",
    "column_indices", "row_cell_column_pairs", "image_evidence_ref", "target_paragraph_id",
    "paragraph_ids", "related_unit_ids", "section", "line", "source_pages",
    "scope_context_ids", "follows_context_id", "child_groups",
}
GROUP_KEYS = {"position", "ordered_context_ids"}
PAIR_KEYS = {"column_index", "header_index", "cell_index", "header_context_id", "cell_context_id"}
POLICY_KEYS = ("text", "headers", "title", "row_cells", "caption")
FORBIDDEN_KEYS = {"labels", "prediction", "predictions", "expected_labels", "gold", "dimension_reasons",
                  "fairness_subtypes", "innovation_subtypes", "sampling_stratum", "weight", "pi",
                  "selection_reasons", "manual", "reference_label", "confidence", "score", "rationale"}


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def opaque(prefix, *values):
    return prefix + sha_bytes(json.dumps(values, ensure_ascii=False, sort_keys=True).encode())[:20]


def rows(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def scalar_tree(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return copy.deepcopy(value)
    if isinstance(value, list):
        return [scalar_tree(v) for v in value]
    raise ValueError("Arbitrary nested source metadata is not whitelisted")


def project_structure(structure):
    assert isinstance(structure, dict)
    assert not (set(structure) - STRUCTURE_KEYS), set(structure) - STRUCTURE_KEYS
    out = {}
    for key, value in structure.items():
        if key in {"child_groups", "row_cell_column_pairs"}:
            permitted = GROUP_KEYS if key == "child_groups" else PAIR_KEYS
            assert isinstance(value, list)
            out[key] = []
            for item in value:
                assert isinstance(item, dict) and not (set(item) - permitted), item
                out[key].append({k: scalar_tree(v) for k, v in item.items()})
        else:
            out[key] = scalar_tree(value)
    return out


def context_references(value, pointer=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from context_references(item, pointer + "/" + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from context_references(item, pointer + "/" + str(index))
    elif isinstance(value, str) and value.startswith("CTX-"):
        yield pointer, value


def text_values(node):
    for key in POLICY_KEYS:
        value = node.get(key)
        if isinstance(value, str):
            yield key, value
        elif isinstance(value, list):
            for index, item in enumerate(value):
                assert isinstance(item, str), (key, index)
                yield key + "/" + str(index), item
        elif value is not None:
            raise ValueError(("Unexpected source content shape", key))


def normalized_text(value):
    # Only Unicode width and whitespace are normalized for the audit.
    # Output source text is always the original, unchanged string.
    return "".join(c for c in unicodedata.normalize("NFKC", value) if not c.isspace())


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def extract_snapshot_text(path):
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        result = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            return None, "pdf_extraction_failure"
        return result.stdout, "pdftotext_layout"
    if path.suffix.lower() in {".txt", ".json", ".jsonl"}:
        return path.read_text(encoding="utf-8"), "snapshot_UTF8"
    if path.suffix.lower() in {".html", ".htm"}:
        parser = TextHTML()
        parser.feed(path.read_text(encoding="utf-8"))
        return "\n".join(parser.parts), "HTML_text_nodes"
    if path.suffix.lower() in {".doc", ".docx"}:
        result = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(path)],
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout, "macOS_textutil_stdout_read_only"
        return None, "Word_text_extraction_failure"
    return None, "no_text_extractor_for_format"


def candidate_paragraph_texts(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    paragraphs = value.get("paragraphs", [])
    assert isinstance(paragraphs, list)
    return {
        p.get("id", p.get("paragraph_id")): p.get("text")
        for p in paragraphs if isinstance(p, dict) and isinstance(p.get("text"), str)
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = BASE / "source_files_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    by_path = {r["original"]: r for r in manifest["files"]}
    by_sha = {r["sha256"]: r for r in manifest["files"]}
    by_doc = {"D-" + r["sha256"][:16]: r for r in manifest["files"]}
    # Matches the actual exporter, not a guessed SHA-prefix convention.
    by_doc.update({opaque("D2-", r["original"], r["sha256"]): r for r in manifest["files"]})
    model_entry = next(r for r in manifest["files"] if "model_source_file" in r["roles"])
    rule_entry = next(r for r in manifest["files"] if "rule_input_file" in r["roles"])
    assert sha_file(model_entry["snapshot"]) == model_entry["sha256"]
    assert sha_file(rule_entry["snapshot"]) == rule_entry["sha256"]
    frame_path = BASE / "source-only-frame.jsonl"
    frame = {r["id"]: r for r in rows(frame_path)}
    model = {r["id"]: r for r in rows(model_entry["snapshot"])}
    rule = {r["id"]: r for r in rows(rule_entry["snapshot"])}
    mapping_path = ROOT / "04-calibration/coverage01/admin/selection.json"
    selection = json.loads(mapping_path.read_text())
    selected = sorted({r["frame_id"] for r in selection["records"]})
    assert len(selected) == 36 and set(selected) <= set(frame)
    exposure_path = ROOT / "01-review/exposure-ids.json"
    assert set(selected) <= set(json.loads(exposure_path.read_text())["excluded_ids"])
    # Provenance is copied only after selecting source bindings, never whole old opinions.
    side = {r["id"]: r for r in rows(SIDE_PATH) if r["id"] in selected}
    assert set(side) == set(selected)
    for rid in selected:
        assert frame[rid]["unit_text"] == model[rid]["text"] == rule[rid]["input"]["unit_text"]
    extracted = {}
    candidates = {}
    verified_snapshots = {}
    provenance_audit = []
    output = []
    dangling = []
    counts = Counter()
    unresolved = []
    source_maps = {}
    changed_document_ids = []
    visual_path = OUT / "source-visual-review.json"
    visual = json.loads(visual_path.read_text()) if visual_path.exists() else None
    visual_bindings = {}
    if visual:
        for page in visual["pages"]:
            assert sha_file(page["path"]) == page["sha256"]
        visual_bindings = {(v["record_id"], v["context_id"], v["field"]): v for v in visual["checked_context_occurrences"]}
    for rid in selected:
        row = model[rid]
        sid = side[rid]
        leaf_bindings = defaultdict(list)
        for leaf in sid.get("policy_leaves", []):
            leaf_bindings[leaf.get("context_id")].append(leaf)
        added_bindings = {z["context_id"]: z for z in sid.get("added_component_fragments", [])}
        nodes = []
        node_sources = {}
        node_audit = {}
        for original in row["contexts"]:
            assert not (set(original) - MODEL_KEYS), (rid, set(original) - MODEL_KEYS)
            node = {k: scalar_tree(v) for k, v in original.items() if k in {"context_id", "kind", "source_document"}}
            node["structure"] = project_structure(original["structure"])
            for key in POLICY_KEYS:
                if key in original:
                    node[key] = scalar_tree(original[key])
            cid = node["context_id"]
            source = by_doc.get(node.get("source_document"))
            methods = []
            bindings = leaf_bindings.get(cid, [])
            binding_sha = {z.get("source_binding", {}).get("source_sha256") for z in bindings}
            binding_sha.discard(None)
            for leaf in bindings:
                field = leaf["output_field"]
                actual = dict(text_values(node)).get(field)
                if actual is not None:
                    assert sha_bytes(actual.encode()) == leaf["text_sha256"], (rid, cid, field)
            if source:
                methods.append("exporter_document_identity")
            elif len(binding_sha) == 1:
                source = by_sha.get(next(iter(binding_sha)))
                if source:
                    methods.append("sidecar_policy_leaf_complete_source_pair")
            if cid in added_bindings:
                added = added_bindings[cid]
                expected_doc = opaque("D2-", added["source"]["path"], added["source"]["sha256"])
                assert node.get("source_document") == expected_doc
                assert node["text"] and sha_bytes(node["text"].encode()) == added["text_sha256"]
                assert added["source"]["path"] in by_path
                assert by_path[added["source"]["path"]]["sha256"] == added["source"]["sha256"]
                methods.append("D2_opaque_path_plus_SHA_exact")
            if source:
                node_sources[cid] = source
            node_audit[cid] = {"record_id": rid, "context_id": cid, "old_source_document": node.get("source_document"), "binding_methods": methods, "text_fields": []}
            nodes.append(node)
        by_cid = {n["context_id"]: n for n in nodes}
        assert len(by_cid) == len(nodes)
        for node in nodes:
            for pointer, value in context_references(node["structure"]):
                if value not in by_cid:
                    dangling.append({"record_id": rid, "context_id": node["context_id"], "pointer": pointer, "target": value})
        # Textless containers inherit only an unambiguous connected source identity.
        # This is a source-structure association, never independent literal evidence.
        for _ in range(len(nodes)):
            progress = False
            for node in nodes:
                cid = node["context_id"]
                if cid in node_sources or list(text_values(node)):
                    continue
                refs = [ref for _, ref in context_references(node["structure"])]
                refs += [child["context_id"] for child in nodes if child["structure"].get("parent_context_id") == cid]
                connected = {node_sources[ref]["sha256"] for ref in refs if ref in node_sources}
                if len(connected) == 1:
                    node_sources[cid] = by_sha[next(iter(connected))]
                    node_audit[cid]["binding_methods"].append("textless_structure_unique_linked_source")
                    progress = True
            if not progress:
                break
        for node in nodes:
            cid = node["context_id"]
            record = node_audit[cid]
            source = node_sources.get(cid)
            if source:
                key = source["sha256"]
                if key not in verified_snapshots:
                    assert sha_file(source["snapshot"]) == key
                    verified_snapshots[key] = {"snapshot": source["snapshot"], "sha256": key, "byte_identity_verified": True}
                if key not in extracted:
                    extracted[key] = extract_snapshot_text(source["snapshot"])
                # Add neutral location/hash information. No original machine/coder field.
                node["source_ref"] = {"sha256": key, "locator": copy.deepcopy(node["structure"])}
                if node.get("source_document") in {None, "UNBOUND"} or str(node.get("source_document", "")).startswith("D2-"):
                    changed_document_ids.append({"record_id": rid, "context_id": cid, "old": node.get("source_document"), "canonical_source_sha256": key, "method": record["binding_methods"]})
                record["source_snapshot"] = source["snapshot"]
                record["source_sha256"] = key
                snapshot_text, extraction_method = extracted[key]
                record["source_text_extractor"] = extraction_method
                for field, text in text_values(node):
                    item = {"field": field, "text_sha256": sha_bytes(text.encode()), "literal_check": None}
                    if snapshot_text is not None and text in snapshot_text:
                        item["literal_check"] = "exact_source_extracted_text"
                    elif snapshot_text is not None and normalized_text(text) in normalized_text(snapshot_text):
                        item["literal_check"] = "source_extracted_text_whitespace_NFKC_only"
                    # Candidate paragraph identity is checked even when the PDF extraction differs.
                    candidate_entries = []
                    for leaf in leaf_bindings.get(cid, []):
                        binding = leaf.get("source_binding", {})
                        path = binding.get("candidate_path")
                        if path in by_path:
                            entry = by_path[path]
                            assert entry["sha256"] == binding.get("candidate_sha256")
                            candidate_entries.append(entry)
                    if cid in added_bindings:
                        binding = added_bindings[cid]["candidate"]
                        if binding["path"] in by_path:
                            entry = by_path[binding["path"]]
                            assert entry["sha256"] == binding["sha256"]
                            candidate_entries.append(entry)
                    candidate_matches = []
                    for entry in candidate_entries:
                        csha = entry["sha256"]
                        if csha not in candidates:
                            assert sha_file(entry["snapshot"]) == csha
                            candidates[csha] = candidate_paragraph_texts(entry["snapshot"])
                        declared = node["structure"].get("paragraph_id", node["structure"].get("candidate_paragraph_id"))
                        possible = candidates[csha]
                        if declared in possible and (text == possible[declared] or normalized_text(text) in normalized_text(possible[declared])):
                            candidate_matches.append({"candidate_sha256": csha, "paragraph_id": declared, "match": "declared_paragraph_exact_or_NFKC_whitespace_subspan"})
                    item["candidate_locator_matches"] = candidate_matches
                    visual_binding = visual_bindings.get((rid, cid, field))
                    if visual_binding:
                        assert visual_binding["text_sha256"] == item["text_sha256"]
                        assert visual["source_pdf_sha256"] == key
                        item["visual_source_check"] = "AI_reviewed_complete_snapshot_pages_5_6; transcription_width_whitespace_representation_retained"
                    if item["literal_check"] is None:
                        if not visual_binding:
                            unresolved.append({"record_id": rid, "context_id": cid, "field": field, "source_sha256": key, "issue": "not_exactly_located_in_binary_source_extraction", "candidate_locator_matches": candidate_matches})
                    record["text_fields"].append(item)
            else:
                unresolved.append({"record_id": rid, "context_id": cid, "issue": "source_identity_unresolved", "has_policy_text": bool(list(text_values(node)))})
                node["source_ref"] = {"sha256": None, "locator": copy.deepcopy(node["structure"])}
            record["textless_structural_node"] = not bool(list(text_values(node)))
            counts["contexts"] += 1
            counts["textless_contexts"] += int(record["textless_structural_node"])
            counts["source_identity_resolved"] += int(source is not None)
            counts["policy_leaves"] += len(record["text_fields"])
            for item in record["text_fields"]:
                counts[item["literal_check"] or "not_found_in_text_extraction"] += 1
                counts["AI_visual_source_page_correspondence_checked"] += int("visual_source_check" in item)
            provenance_audit.append(record)
        for original, projected in zip(row["contexts"], nodes):
            # Every original field is unchanged; only source_ref is appended.
            assert {k: v for k, v in projected.items() if k != "source_ref"} == original
        new_row = {"id": rid, "text": row["text"], "pages": copy.deepcopy(row["pages"]), "contexts": nodes}
        if visual and any(node_sources.get(n["context_id"], {}).get("sha256") == visual["source_pdf_sha256"] for n in nodes):
            new_row["source_page_attachments"] = [
                {"attachment_id": "SOURCEPAGE-" + p["sha256"][:20], "sha256": p["sha256"],
                 "relative_path": str(Path(p["path"]).relative_to(OUT)), "source_pdf_sha256": p["source_pdf_sha256"],
                 "physical_page": p["physical_page"]}
                for p in visual["pages"]
            ]
        output.append(new_row)
        source_maps[rid] = {"source_interface_line": frame[rid]["shared_context_identity"]["model_source_line"], "unit_text_sha256": frame[rid]["unit_text_sha256"], "contexts_original_sha256": sha_bytes(canonical(row["contexts"]).encode()), "canonical_source_content_sha256": sha_bytes(canonical(new_row).encode())}
    assert not dangling, dangling
    counts["unresolved_literal_or_source_issues"] = len(unresolved)
    forbidden = []
    def check_result_keys(value, pointer=""):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in FORBIDDEN_KEYS:
                    forbidden.append(pointer + "/" + key)
                check_result_keys(item, pointer + "/" + key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                check_result_keys(item, pointer + "/" + str(index))
    check_result_keys(output)
    assert not forbidden, forbidden
    result_path = OUT / "canonical_source_context.jsonl"
    result_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in output), encoding="utf-8")
    audit = {
        "status": "complete_source_projection_structural_QA; literal_provenance_pending_items_retained",
        "model_or_coder_executed": False, "coder_labels_or_unsealed_submissions_read": False,
        "final_holdout_sample_drawn": False, "old_files_modified": False,
        "selection_role_visible_in_canonical_material": False, "manual_or_dimension_hints_visible": False,
        "selected_record_N": len(selected), "counts": dict(counts),
        "all_original_context_nodes_retained": True,
        "all_original_policy_text_fields_byte_equivalent": True,
        "all_original_source_structure_and_context_IDs_unchanged": True,
        "dangling_context_references": dangling,
        "recursive_forbidden_result_key_check": {"forbidden_keys": sorted(FORBIDDEN_KEYS), "violations": forbidden, "count": len(forbidden)},
        "context_ID_strategy": "retain original CTX IDs; recursively validate all CTX strings in complete nested source structure",
        "source_identity_note": "UNBOUND textual leaves link through source-only sidecar complete source pairs; D2 uses sha256(json.dumps((original_path,sha256),ensure_ascii=False,sort_keys=True))[:20]. Textless unique-child-source derivation is structural identity only.",
        "literal_verification_note": "Byte SHA plus literal extraction/locator checks are distinguished. Pending literal matches are not discarded, silently normalized, or called fully authenticated. NFKC and whitespace changes are audit-only; output source text is unchanged.",
        "inputs": {"model_snapshot": model_entry, "rule_snapshot": rule_entry,
                   "frame": {"path": str(frame_path), "sha256": sha_file(frame_path)},
                   "source_manifest": {"path": str(manifest_path), "sha256": sha_file(manifest_path)},
                   "coverage_ID_selection": {"path": str(mapping_path), "sha256": sha_file(mapping_path)},
                   "source_only_provenance_sidecar02": {"path": str(SIDE_PATH), "sha256": sha_file(SIDE_PATH)}},
        "builder_sha256": sha_file(__file__),
        "source_visual_review": {"path": str(visual_path), "sha256": sha_file(visual_path)} if visual else None,
        "output": {"path": str(result_path), "sha256": sha_file(result_path)},
        "source_snapshot_byte_checks": list(verified_snapshots.values()),
        "exported_document_identity_bindings": changed_document_ids,
        "record_content_bindings": source_maps,
        "context_provenance": provenance_audit,
        "unresolved": unresolved,
        "limits": ["No construct/manual interpretation or coder judgment is added.",
                   "The 36 items are already exposed development materials, not final validation.",
                   "Retention of original source context does not itself establish that every context is required by a future frozen manual.",
                   "All necessary images, ambiguous source glyphs, and literal provenance gaps still need source-specific adjudication; no claim of fully completed human validation."]}
    (OUT / "projection-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"record_N": len(output), "counts": dict(counts), "dangling_N": len(dangling), "unresolved_N": len(unresolved), "output_sha256": audit["output"]["sha256"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
