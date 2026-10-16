"""Source-only, strict material projection. No corpus/export CLI is provided.

Pure functions accept in-memory records. This revision is tested only with
invented structures. Source hashes are metadata bindings, not authentication
of a literal policy leaf. Externally frozen leaf bindings are named as such;
verification/role/usage fields are never consumed as proof or emitted.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import tempfile
from pathlib import Path

VERSION = "source-only-material-projection01"
KINDS = {
    "paragraph_context": "paragraph",
    "nearest_preceding_heading": "heading",
    "immediately_preceding_paragraph": "preceding_paragraph",
    "verified_parent_context": "parent_paragraph",
    "verified_scope_qualifications_v28": "source_paragraph",
    "structured_following_units": "ordered_members",
    "complete_following_list_v11": "ordered_list",
    "verified_table_header": "table_header",
    "explicitly_cited_qualifications_v12": "cited_reference_group",
    "explicitly_cited_articles_v10": "cited_article",
    "resolved_material_supplement": "source_paragraph",
    "verified_document_object_v9": "document_context",
    "verified_table_context_v4": "table_row",
    "source_local_list_family_v14": "source_list",
    "structured_following_units_v5": "ordered_members",
    "following_condition_head_v5": "list_parent",
    "source_component_boundary_v14": "component",
    "source_local_list_family_v13": "source_list",
    "structured_following_units_v6": "ordered_members",
    "verified_scope_context_v8": "source_paragraph",
    "verified_following_list_v27": "ordered_list",
    "verified_parent_list_v7": "source_list",
    "verified_parent_list_v8": "source_list",
    "verified_innovation_scope_v27": "source_paragraph",
    "verified_object_scope": "source_paragraph",
    "verified_rule_branch_context": "source_paragraph",
    "verified_supplemental_context": "supplemental_group",
    "verified_table_context": "table_row",
    # Only its actual next_boundary child is admitted; status/head prose is not.
    "following_context_status_v11": "boundary_container",
}
DROP = {
    "labels", "prediction", "evidence", "rule", "basis", "subtype",
    "expected_labels", "expected_auxiliary_fields", "content_role",
    "content_role_basis", "context_usage", "parent_context_basis", "role",
    "semantic_role", "usage", "selection", "selection_basis", "verification",
    "authentication_v34", "source_checks", "review", "review_path",
    "department", "bucket", "exposure", "protection", "repair_version",
    "repair_status", "status", "following_list_usage_v10",
    "following_list_use_v6", "cited_article_usage_v10",
}
TEXT_FIELDS = ("text", "original_unit_text", "required_branch_text",
               "next_paragraph_text", "next_candidate_paragraph_text",
               "next_component_boundary_text")
AMBIGUOUS_TEXT = ("next_structure", "boundary", "next_boundary")
LOCATORS = (
    "paragraph_id", "unit_id", "current_unit_id", "source_unit_id",
    "target_paragraph_id", "pages", "source_pages", "source_lines", "line_ids",
    "candidate_line_ids", "reference_address", "article", "first_paragraph",
    "last_paragraph", "first_paragraph_id", "last_paragraph_id",
    "next_paragraph_id", "next_candidate_paragraph_id",
    "component_first_paragraph", "component_last_paragraph",
    "row_index_zero_based",
)
# These are declared structural children, not unrestricted recursive harvesting.
CHILDREN = {
    "contexts": "ordered_members",
    "references": "cited_reference",
    "incorporated_explicit_reference": "cited_article",
    "actual_heading": "heading",
    "actual_component_heading": "heading",
    "actual_parent_predicate": "list_parent",
    "actual_list_siblings": "ordered_members",
    "complete_source_structure": "source_list",
    "structure_boundary": "boundary_container",
    "next_structure": "boundary",
    "next_boundary": "boundary",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_manifest_files(entries):
    """Pure SHA check; never implies that a text leaf is literally in a file."""
    results = []
    for entry in entries:
        actual = file_sha(entry["path"])
        results.append({"path": entry["path"], "expected_sha256": entry["sha256"],
                        "actual_sha256": actual,
                        "hash_equal": actual == entry["sha256"]})
    return results


def source_pair(node, inherited=None):
    """Never mix source-layer paths/hashes or infer a source from a filename."""
    inherited = dict(inherited or {})
    for path_key, hash_key in (
        ("unit_source", "unit_source_sha256"),
        ("source_path", "source_sha256"),
        ("source", "source_sha256"),
    ):
        if node.get(path_key) and node.get(hash_key):
            inherited.update(source_path=node[path_key],
                             source_sha256=node[hash_key],
                             source_pair_fields=[path_key, hash_key])
            break
    for key in ("candidate_path", "candidate_file"):
        if node.get(key) and node.get("candidate_sha256"):
            inherited.update(candidate_path=node[key],
                             candidate_sha256=node["candidate_sha256"])
            break
    if node.get("source_structured_sha256"):
        inherited["table_source_structured_sha256"] = node["source_structured_sha256"]
    for key in ("source_image", "source_image_sha256"):
        if node.get(key):
            inherited[key] = node[key]
    return inherited


def scalar_locator(value):
    """Only neutral scalar/list locators; arbitrary nested dictionaries dropped."""
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        return copy.deepcopy(value)
    if isinstance(value, list) and all(
        isinstance(x, (str, int)) and not isinstance(x, bool) for x in value
    ):
        return copy.deepcopy(value)
    return None


class Projector:
    def __init__(self, row_id, bindings=None, manifest_sha256=None):
        self.row_id = row_id
        self.bindings = bindings or {}
        self.manifest_sha256 = manifest_sha256
        self.nodes = []
        self.leaves = []
        self.issues = []
        self.omitted_paths = []

    def context_id(self, pointer):
        return "CTX-" + sha_text(self.row_id + "\0" + pointer)[:20]

    def literal(self, value, pointer, origin, context_id, output_field):
        if not isinstance(value, str) or not value:
            return
        proof = self.bindings.get(pointer)
        expected_source = origin.get("table_source_structured_sha256") or origin.get("source_sha256")
        valid = (
            isinstance(proof, dict)
            and proof.get("text_sha256") == sha_text(value)
            and proof.get("source_sha256") == expected_source
            and HEX64.fullmatch(str(expected_source or "")) is not None
            and HEX64.fullmatch(str(self.manifest_sha256 or "")) is not None
            and proof.get("manifest_sha256") == self.manifest_sha256
            and proof.get("proof_kind") in {
                "source_literal_span", "source_table_cell",
                "source_heading_span", "reviewed_source_image_region"
            }
            and isinstance(proof.get("locator"), dict)
            and bool(proof["locator"])
        )
        self.leaves.append({
            "raw_pointer": pointer, "context_id": context_id,
            "output_field": output_field, "text_sha256": sha_text(value),
            "character_n": len(value), "source_binding": copy.deepcopy(origin),
            "binding_status": ("externally_manifest_bound_not_reauthenticated"
                               if valid else "unbound_policy_leaf_candidate"),
            "manifest_sha256": self.manifest_sha256 if valid else None,
        })
        if not valid:
            self.issues.append({"code": "unbound_policy_leaf", "raw_pointer": pointer})
        # No verification flags, opinions or proof prose are copied.
        return valid

    def emit_node(self, value, pointer, kind, inherited, parent=None, order=None):
        if isinstance(value, list):
            ids = []
            for index, item in enumerate(value):
                ids.extend(self.emit_node(item, f"{pointer}/{index}", kind,
                                          inherited, parent, index))
            return ids
        if not isinstance(value, dict):
            self.omitted_paths.append(pointer)
            return []
        origin = source_pair(value, inherited)
        cid = self.context_id(pointer)
        out = {"context_id": cid, "kind": kind,
               "source_document": ("D-" + origin["source_sha256"][:16]
                                   if origin.get("source_sha256") else "UNBOUND"),
               "structure": {}}
        if parent is not None:
            out["structure"]["parent_context_id"] = parent
        if order is not None:
            out["structure"]["sequence_index"] = order
        for key in LOCATORS:
            loc = scalar_locator(value.get(key))
            if loc is not None:
                out["structure"][key] = loc
        locator = value.get("locator")
        if isinstance(locator, dict):
            for key in ("paragraph_id", "article", "line", "physical_pages", "source_lines"):
                loc = scalar_locator(locator.get(key))
                if loc is not None:
                    out["structure"][key] = loc
        # Raw table values take precedence over assembled certificate text.
        table_arrays = any(k in value for k in
                           ("column_names", "header_cells", "headers", "raw_row_cells", "row_cells"))
        if kind == "boundary_container":
            text_fields = tuple(k for k in TEXT_FIELDS if k.startswith("next_"))
        elif table_arrays:
            text_fields = tuple(k for k in TEXT_FIELDS if k != "text")
        else:
            text_fields = TEXT_FIELDS
        for key in text_fields:
            text = value.get(key)
            if isinstance(text, str) and text:
                if key == "text" and "text" not in out:
                    out["text"] = text
                    self.literal(text, f"{pointer}/{key}", origin, cid, "text")
                else:
                    # Distinct actual text fields remain distinct occurrences.
                    child_id = self.context_id(f"{pointer}/{key}")
                    child = {"context_id": child_id, "kind": "boundary" if key.startswith("next_") else "source_paragraph",
                             "source_document": out["source_document"], "text": text,
                             "structure": {"parent_context_id": cid, "position": key}}
                    if key == "next_paragraph_text" and value.get("next_paragraph_id"):
                        child["structure"]["paragraph_id"] = value["next_paragraph_id"]
                    if key == "next_candidate_paragraph_text" and value.get("next_candidate_paragraph_id"):
                        child["structure"]["paragraph_id"] = value["next_candidate_paragraph_id"]
                    self.nodes.append(child)
                    self.literal(text, f"{pointer}/{key}", origin, child_id, "text")
                    out["structure"].setdefault("text_child_context_ids", []).append(child_id)
        for raw, visible in (("table_title", "title"), ("caption", "caption")):
            text = value.get(raw)
            if isinstance(text, str) and text:
                out[visible] = text
                self.literal(text, f"{pointer}/{raw}", origin, cid, visible)
        headers_key = next((k for k in ("column_names", "header_cells", "headers")
                            if isinstance(value.get(k), list)), None)
        cells_key = next((k for k in ("raw_row_cells", "row_cells")
                          if isinstance(value.get(k), list)), None)
        for raw, visible in ((headers_key, "headers"), (cells_key, "row_cells")):
            if raw is None:
                continue
            vals = value[raw]
            if not all(isinstance(x, str) for x in vals):
                self.issues.append({"code": "nonstring_table_value", "raw_pointer": f"{pointer}/{raw}"})
                continue
            out[visible] = copy.deepcopy(vals)
            for index, text in enumerate(vals):
                if not text:
                    continue  # Preserve the blank cell in-place; never invent a quote.
                raw_pointer = f"{pointer}/{raw}/{index}"
                cell_id = self.context_id(raw_pointer)
                # The frozen validator does not yield direct strings in arrays.
                # Keep the ordered arrays AND a quotable text occurrence per cell.
                cell = {"context_id": cell_id,
                        "kind": "table_header_cell" if visible == "headers" else "table_row_cell",
                        "source_document": out["source_document"], "text": text,
                        "structure": {"parent_context_id": cid, "column_index": index,
                                      "position": visible}}
                if "row_index_zero_based" in value:
                    cell["structure"]["row_index_zero_based"] = value["row_index_zero_based"]
                self.nodes.append(cell)
                self.literal(text, raw_pointer, origin, cell_id, "text")
                self.leaves[-1]["additional_output_occurrence"] = {
                    "context_id": cid, "field": f"{visible}/{index}"}
                out["structure"].setdefault("table_text_context_ids", []).append(cell_id)
        if cells_key:
            if not headers_key or len(out.get("headers", [])) != len(out.get("row_cells", [])):
                self.issues.append({"code": "table_header_cell_count_mismatch", "raw_pointer": pointer})
            else:
                out["structure"]["column_indices"] = list(range(len(out["headers"])))
                out["structure"]["row_cell_column_pairs"] = [
                    {"column_index": i, "header_index": i, "cell_index": i}
                    for i in range(len(out["headers"]))
                ]
        # Flattening order is not semantic order: retain explicit membership links.
        self.nodes.append(out)
        for key, child_kind in CHILDREN.items():
            child = value.get(key)
            if isinstance(child, (dict, list)):
                child_ids = self.emit_node(child, f"{pointer}/{key}", child_kind,
                                           origin, cid)
                if child_ids:
                    out["structure"].setdefault("child_groups", []).append(
                        {"position": key, "ordered_context_ids": child_ids})
        # A scalar boundary description is not assumed to be actual policy words.
        for key in AMBIGUOUS_TEXT:
            text = value.get(key)
            if not isinstance(text, str) or not text:
                continue
            raw_pointer = f"{pointer}/{key}"
            proof = self.bindings.get(raw_pointer)
            if proof is None:
                self.omitted_paths.append(raw_pointer)
                self.issues.append({"code": "ambiguous_boundary_requires_literal_binding",
                                    "raw_pointer": raw_pointer})
                continue
            child_id = self.context_id(raw_pointer)
            valid = self.literal(text, raw_pointer, origin, child_id, "text")
            if valid:
                self.nodes.append({"context_id": child_id, "kind": "boundary",
                                   "source_document": out["source_document"], "text": text,
                                   "structure": {"parent_context_id": cid}})
                out["structure"].setdefault("text_child_context_ids", []).append(child_id)
        # Unknown values are never traversed or copied.
        admitted = set(LOCATORS) | set(TEXT_FIELDS) | set(CHILDREN) | set(AMBIGUOUS_TEXT) | {
            "locator", "table_title", "caption", "column_names", "header_cells",
            "headers", "raw_row_cells", "row_cells", "source", "unit_source",
            "unit_source_sha256", "source_path", "source_sha256", "candidate_path",
            "candidate_file", "candidate_sha256", "source_structured_sha256",
            "source_image", "source_image_sha256",
        }
        self.omitted_paths.extend(f"{pointer}/{k}" for k in value if k not in admitted)
        return [cid]


def project_record(llm_row, rule_record=None, *, literal_bindings=None, manifest_sha256=None):
    """Return a candidate view + metadata sidecar, without I/O or authentication."""
    if not isinstance(llm_row.get("id"), str) or not isinstance(llm_row.get("text"), str):
        raise ValueError("input id/text contract")
    rule = (rule_record or {}).get("input", rule_record or {})
    if rule and (rule.get("unit_text") != llm_row["text"]
                 or (rule_record.get("id", llm_row["id"]) != llm_row["id"])):
        raise ValueError("rule/LLM current binding mismatch")
    current_origin = source_pair(rule)
    p = Projector(llm_row["id"], literal_bindings, manifest_sha256)
    p.literal(llm_row["text"], "/text", current_origin, None, "text")
    context = llm_row.get("contexts")
    if not isinstance(context, dict):
        raise ValueError("contexts must be the declared shared-context object")
    for key, value in context.items():
        if key == "verified_context_certificates" and isinstance(value, dict):
            for name, node in value.items():
                if name in KINDS:
                    p.emit_node(node, f"/contexts/{key}/{name}", KINDS[name], current_origin)
                else:
                    p.omitted_paths.append(f"/contexts/{key}/{name}")
                    if isinstance(node, (dict, list)):
                        p.issues.append({"code": "unmapped_context_family", "raw_pointer": f"/contexts/{key}/{name}"})
        elif key in KINDS:
            if value is not None:
                p.emit_node(value, f"/contexts/{key}", KINDS[key], current_origin)
        else:
            p.omitted_paths.append(f"/contexts/{key}")
            if key not in DROP and isinstance(value, (dict, list)):
                p.issues.append({"code": "unmapped_context_family", "raw_pointer": f"/contexts/{key}"})
    pages = scalar_locator(llm_row.get("pages", []))
    if pages is None:
        p.issues.append({"code": "invalid_current_pages_shape", "raw_pointer": "/pages"})
        pages = []
    visible = {
        "id": llm_row["id"], "text": llm_row["text"],
        "pages": pages, "contexts": p.nodes,
    }
    return {
        "model_visible_candidate": visible,
        "provenance_sidecar": {
            "id": llm_row["id"], "current_source_priority": current_origin,
            "generic_source_identity": {
                k: rule[k] for k in ("source", "source_sha256") if k in rule},
            "unit_source_identity": {
                k: rule[k] for k in ("unit_source", "unit_source_sha256") if k in rule},
            "policy_leaves": p.leaves, "omitted_raw_paths": sorted(set(p.omitted_paths)),
            "issues": p.issues, "binding_complete_for_review": not p.issues,
            "authentication_claim": "none; external manifest bindings are not reauthenticated",
            "full_export_authorized_or_performed": False,
        },
    }


def self_test(validator_path=None):
    """Invented current/list/table/duplicate fixtures only; no corpus reads."""
    checks = []
    fake_sha = "1" * 64
    manifest_sha = "2" * 64
    row = {
        "id": "SYNTH-PROJECTION-01", "text": "构造当前句。", "pages": [1],
        "source_title": "FILENAME_MUST_NOT_BECOME_TITLE",
        "contexts": {
            "complete_following_list_v11": {
                "contexts": [
                    {"paragraph_id": "p1", "text": "构造甲项。"},
                    {"paragraph_id": "p2", "text": "构造乙项。"}],
                "structure_boundary": {
                    "first_paragraph": "p1", "last_paragraph": "p2",
                    "next_paragraph_id": "p3", "next_paragraph_text": "构造下一节。"},
                "usage": "DROP_USAGE", "verification": {"opinion": "DROP_OPINION"}},
            "explicitly_cited_qualifications_v12": {
                "references": [{"reference_address": "第七条第二款", "contexts": [
                    {"paragraph_id": "r1", "text": "构造确指第一段。"},
                    {"paragraph_id": "r2", "text": "构造确指第二段。"}]}]},
            "verified_table_context_v4": [{
                "table_title": "构造表题", "column_names": ["构造列一", "构造列二"],
                "raw_row_cells": ["构造格甲", "构造格乙"], "row_index_zero_based": 3,
                "text": "DROP_ASSEMBLED_CERTIFICATE", "visual_review": "DROP_REVIEW"}],
            "paragraph_context": [
                {"paragraph_id": "dup1", "text": "构造重复段。"},
                {"paragraph_id": "dup2", "text": "构造重复段。"}],
            "source_local_list_family_v13": {
                "actual_heading": {"paragraph_id": "h1", "text": "构造实际标题。"},
                "actual_parent_predicate": {"paragraph_id": "parent", "text": "构造父命题。"},
                "actual_list_siblings": [
                    {"paragraph_id": "child1", "text": "构造成员一。"},
                    {"paragraph_id": "child2", "text": "构造成员二。"}]},
            "content_role_basis": "DROP_REASON",
            "unknown_container": {"text": "DROP_UNKNOWN_TEXT", "labels": {"S": 1}},
        },
    }
    rule = {"id": row["id"], "input": {
        "unit_text": row["text"], "source": "synthetic-general",
        "source_sha256": "3" * 64, "unit_source": "synthetic-unit",
        "unit_source_sha256": fake_sha}}
    original = copy.deepcopy(row)
    result = project_record(row, rule)
    visible = result["model_visible_candidate"]
    nodes = visible["contexts"]
    table = next(n for n in nodes if n["kind"] == "table_row")
    assert table["title"] == "构造表题" and table["headers"] == ["构造列一", "构造列二"]
    assert table["row_cells"] == ["构造格甲", "构造格乙"]
    assert table["structure"]["row_index_zero_based"] == 3
    assert table["structure"]["row_cell_column_pairs"][1]["cell_index"] == 1
    checks.append("table_order_title_row_column_pairing")
    repeated_table = copy.deepcopy(row)
    repeated_table["contexts"]["verified_table_context_v4"][0]["raw_row_cells"] = ["构造重复格", "构造重复格"]
    repeated_nodes = project_record(repeated_table, rule)["model_visible_candidate"]["contexts"]
    repeated_cells = [n for n in repeated_nodes if n["kind"] == "table_row_cell"]
    assert [n["text"] for n in repeated_cells] == ["构造重复格", "构造重复格"]
    assert [n["structure"]["column_index"] for n in repeated_cells] == [0, 1]
    assert len({n["context_id"] for n in repeated_cells}) == 2
    checks.append("repeated_table_values_keep_distinct_column_occurrences")
    listed = next(n for n in nodes if n["kind"] == "ordered_list")
    member_ids = next(g["ordered_context_ids"] for g in listed["structure"]["child_groups"]
                      if g["position"] == "contexts")
    byid = {n["context_id"]: n for n in nodes}
    assert [byid[c]["text"] for c in member_ids] == ["构造甲项。", "构造乙项。"]
    assert any(n.get("text") == "构造下一节。" for n in nodes)
    checks.append("list_order_and_actual_next_boundary")
    ref = next(n for n in nodes if n["kind"] == "cited_reference")
    assert ref["structure"]["reference_address"] == "第七条第二款"
    refs = ref["structure"]["child_groups"][0]["ordered_context_ids"]
    assert [byid[c]["structure"]["paragraph_id"] for c in refs] == ["r1", "r2"]
    checks.append("exact_reference_address_and_order")
    duplicates = [n for n in nodes if n.get("text") == "构造重复段。"]
    assert len(duplicates) == 2 and len({n["context_id"] for n in duplicates}) == 2
    assert {n["structure"]["paragraph_id"] for n in duplicates} == {"dup1", "dup2"}
    checks.append("duplicate_text_distinct_occurrences")
    family = next(n for n in nodes if n["kind"] == "source_list")
    assert [g["position"] for g in family["structure"]["child_groups"]] == [
        "actual_heading", "actual_parent_predicate", "actual_list_siblings"]
    checks.append("heading_parent_member_relationships")
    payload = json.dumps(visible, ensure_ascii=False)
    assert "DROP_" not in payload and "FILENAME_MUST_NOT_BECOME_TITLE" not in payload
    bad_pages = copy.deepcopy(row)
    bad_pages["pages"] = {"opinion": "DROP_PAGES_OPINION"}
    bad_pages_result = project_record(bad_pages, rule)
    assert bad_pages_result["model_visible_candidate"]["pages"] == []
    assert any(i["code"] == "invalid_current_pages_shape"
               for i in bad_pages_result["provenance_sidecar"]["issues"])
    assert "DROP_PAGES_OPINION" not in json.dumps(bad_pages_result["model_visible_candidate"])
    checks.append("no_opinions_unknown_text_or_filename_title")
    assert not result["provenance_sidecar"]["binding_complete_for_review"]
    assert all(x["binding_status"] == "unbound_policy_leaf_candidate"
               for x in result["provenance_sidecar"]["policy_leaves"])
    assert result["provenance_sidecar"]["current_source_priority"]["source_sha256"] == fake_sha
    checks.append("unbound_not_authenticated_and_source_pair_priority")
    registry = {
        x["raw_pointer"]: {
            "text_sha256": x["text_sha256"], "source_sha256": fake_sha,
            "manifest_sha256": manifest_sha, "proof_kind": "source_literal_span",
            "locator": {"synthetic_occurrence": x["raw_pointer"]}}
        for x in result["provenance_sidecar"]["policy_leaves"]
    }
    known_row = copy.deepcopy(row)
    del known_row["contexts"]["unknown_container"]
    bound = project_record(known_row, rule, literal_bindings=registry, manifest_sha256=manifest_sha)
    assert bound["provenance_sidecar"]["binding_complete_for_review"]
    assert not bound["provenance_sidecar"]["full_export_authorized_or_performed"]
    checks.append("external_manifest_binding_named_without_auth_claim")
    bad = copy.deepcopy(row)
    bad["contexts"]["verified_table_context_v4"][0]["raw_row_cells"].pop()
    assert any(i["code"] == "table_header_cell_count_mismatch"
               for i in project_record(bad, rule)["provenance_sidecar"]["issues"])
    checks.append("bad_table_dimensions_block_readiness")
    assert row == original
    checks.append("no_input_mutation")
    with tempfile.TemporaryDirectory(prefix="projection-source-only-synthetic-") as tmp:
        f = Path(tmp) / "synthetic.txt"
        f.write_text("全新构造文件；只用于SHA检查。", encoding="utf-8")
        reports = verify_manifest_files([
            {"path": str(f), "sha256": file_sha(f)},
            {"path": str(f), "sha256": "0" * 64}])
        assert reports[0]["hash_equal"] and not reports[1]["hash_equal"]
    checks.append("real_temporary_file_sha_success_and_mismatch")
    if validator_path:
        spec = importlib.util.spec_from_file_location("projection_validator", validator_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        texts = list(module.iter_context_text(nodes))
        for n in nodes:
            for key in ("text", "title", "caption"):
                if key in n:
                    assert n[key] in texts
            for key in ("headers", "row_cells"):
                for text in n.get(key, []):
                    assert text in texts
        checks.append("actual_validator_context_quote_paths")
    return {"passed": True, "check_n": len(checks), "checks": checks,
            "real_policy_records_read": 0, "real_corpus_projected": False,
            "model_called": False, "rule_predictions_run": False,
            "complete_input_generated": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--validator", type=Path)
    args = parser.parse_args()
    if not args.self_test:
        parser.error("Source-only revision: only --self-test is available; no corpus/export CLI.")
    print(json.dumps(self_test(args.validator), ensure_ascii=False, indent=2))
