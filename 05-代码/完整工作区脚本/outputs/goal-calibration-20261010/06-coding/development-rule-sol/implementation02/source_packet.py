"""Read the sealed source fixture without opening judgments or old runtime.

The fixture is the original id/text/context interface, not a blind-packet
schema instance. Source SHA identifies a source document; page SHA identifies
an attached image. Neither identifier is a classification feature.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path


class PacketInterfaceError(ValueError):
    """An input shape or binding needs an explicit interface amendment."""


TOP_KEYS = {"id", "text", "pages", "contexts", "source_page_attachments"}
CONTEXT_KEYS = {
    "context_id", "kind", "source_document", "structure", "source_ref",
    "text", "headers", "title", "row_cells", "caption",
}
CONTEXT_KINDS = {
    "paragraph", "preceding_paragraph", "source_paragraph", "structural_relation",
    "heading", "ordered_list", "ordered_members", "boundary_container", "boundary",
    "parent_paragraph", "source_fragment", "table_header_cell", "table_header",
    "supplemental_group", "cited_reference_group", "cited_reference", "cited_article",
    "document_context", "table_row_cell", "table_row", "source_list", "list_parent",
    "component", "cited_section", "application_scope", "source_chapter_heading",
    "following_heading", "external_source",
}
STRUCTURE_STRING_KEYS = {
    "paragraph_id", "relation_id", "unit_id", "parent_context_id", "first_paragraph",
    "last_paragraph", "position", "next_paragraph_id", "first_paragraph_id",
    "last_paragraph_id", "source_role", "component_id", "candidate_paragraph_id",
    "source_unit_id", "current_unit_id", "reference_address", "next_candidate_paragraph_id",
    "component_first_paragraph", "component_last_paragraph", "image_evidence_ref",
    "target_paragraph_id", "follows_context_id", "table_cell", "source_url",
    "snapshot_attachment_id",
}
STRUCTURE_INT_KEYS = {
    "sequence_index", "candidate_paragraph_start", "candidate_paragraph_end", "column_index",
    "row_index_zero_based",
}
STRUCTURE_STRING_LIST_KEYS = {
    "related_context_ids", "text_child_context_ids", "candidate_line_ids", "paragraph_ids",
    "related_unit_ids", "scope_context_ids",
}
STRUCTURE_INT_LIST_KEYS = {"pages", "physical_pages", "source_pages", "column_indices"}
STRUCTURE_MIXED_LIST_KEYS = {"source_lines", "line_ids", "printed_pages"}
STRUCTURE_SCALAR_KEYS = {"article", "section", "line"}
STRUCTURE_KEYS = (STRUCTURE_STRING_KEYS | STRUCTURE_INT_KEYS | STRUCTURE_STRING_LIST_KEYS
                  | STRUCTURE_INT_LIST_KEYS | STRUCTURE_MIXED_LIST_KEYS
                  | STRUCTURE_SCALAR_KEYS | {"child_groups", "row_cell_column_pairs"})
EXTERNAL_LOCATOR_STRING_KEYS = {
    "document_title", "sections", "local_paragraph_identifier", "section_and_paragraph",
}
EXTERNAL_LOCATOR_INT_KEYS = {
    "txt_line_end_inclusive_1based", "txt_line_start_1based", "html_body_paragraph_index_1based",
}
EXTERNAL_LOCATOR_RANGE_KEYS = {
    "character_range_0based_halfopen", "utf8_byte_range_0based_halfopen",
}
LOCATOR_KEYS = (STRUCTURE_KEYS | EXTERNAL_LOCATOR_STRING_KEYS | EXTERNAL_LOCATOR_INT_KEYS
               | EXTERNAL_LOCATOR_RANGE_KEYS
               | {"character_ranges_0based_halfopen", "dom_occurrences", "html_lines_1based"})
METADATA_KEYS = {
    "document_date", "document_number", "original_url", "republication_date", "source_date",
    "source_document_kind", "source_title", "source_url", "policy_document_date",
    "policy_document_number", "republication_datetime", "source_publication_date",
}
ATTACHMENT_KEYS = {
    "attachment_id", "physical_page", "relative_path", "sha256", "source_pdf_sha256",
}
FORBIDDEN_KEYS = {
    "label", "labels", "prediction", "predictions", "expected", "expected_labels", "gold",
    "reference_label", "reference_labels", "original_coder_answer", "dimension_reasons",
    "innovation_subtypes", "fairness_subtypes", "score", "confidence", "rationale",
    "selection_reasons", "sampling_stratum", "weight", "pi", "manual",
    "verified_context_certificates", "rule_hit", "coder_role", "judgment", "judgement",
}
_SHA = re.compile(r"[a-f0-9]{64}\Z")


def _fail(path, reason):
    raise PacketInterfaceError(f"{path}: {reason}")


def _keys(value, allowed, required, path):
    if not isinstance(value, dict):
        _fail(path, "expected an object")
    unknown = set(value) - allowed
    if unknown:
        _fail(path, f"unknown fields require interface review: {sorted(unknown)}")
    missing = required - set(value)
    if missing:
        _fail(path, f"required fields missing: {sorted(missing)}")


def _string(value, path, *, nonempty=True):
    if not isinstance(value, str) or (nonempty and not value.strip()):
        _fail(path, "expected a nonempty string" if nonempty else "expected a string")


def _integer(value, path, minimum=0):
    if type(value) is not int or value < minimum:
        _fail(path, f"expected an integer >= {minimum}")


def _sha(value, path):
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        _fail(path, "expected a lowercase SHA256")


def _list(value, path):
    if not isinstance(value, list):
        _fail(path, "expected an array")


def _result_guard(value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            if (key in FORBIDDEN_KEYS or key.startswith("machine_")
                    or key.startswith("original_coder_")):
                _fail(path + "/" + key, "result or administrative selection field forbidden")
            _result_guard(child, path + "/" + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _result_guard(child, f"{path}/{index}")
    # Strings are policy/source text. Their words are never filtered.


def _range(value, path):
    _list(value, path)
    if len(value) != 2:
        _fail(path, "expected a two-element half-open range")
    for index, number in enumerate(value):
        _integer(number, f"{path}/{index}")
    if value[0] >= value[1]:
        _fail(path, "range must be nonempty and ordered")


def _structure(value, path, *, locator=False):
    _keys(value, LOCATOR_KEYS if locator else STRUCTURE_KEYS, set(), path)
    for key, child in value.items():
        current = path + "/" + key
        if key in STRUCTURE_STRING_KEYS | EXTERNAL_LOCATOR_STRING_KEYS:
            _string(child, current)
        elif key in STRUCTURE_INT_KEYS | EXTERNAL_LOCATOR_INT_KEYS:
            _integer(child, current, 1 if key in EXTERNAL_LOCATOR_INT_KEYS else 0)
        elif key in STRUCTURE_STRING_LIST_KEYS | {"dom_occurrences"}:
            _list(child, current)
            for index, item in enumerate(child):
                _string(item, f"{current}/{index}")
        elif key in STRUCTURE_INT_LIST_KEYS | {"html_lines_1based"}:
            _list(child, current)
            minimum = 0 if key == "column_indices" else 1
            for index, item in enumerate(child):
                _integer(item, f"{current}/{index}", minimum)
        elif key in STRUCTURE_MIXED_LIST_KEYS:
            _list(child, current)
            for index, item in enumerate(child):
                if type(item) is int:
                    _integer(item, f"{current}/{index}", 1)
                else:
                    _string(item, f"{current}/{index}")
        elif key in STRUCTURE_SCALAR_KEYS:
            if child is not None and type(child) not in {str, int, float}:
                _fail(current, "expected a location scalar, not nested metadata")
        elif key == "child_groups":
            _list(child, current)
            for index, item in enumerate(child):
                at = f"{current}/{index}"
                _keys(item, {"position", "ordered_context_ids"}, {"position", "ordered_context_ids"}, at)
                _string(item["position"], at + "/position")
                _list(item["ordered_context_ids"], at + "/ordered_context_ids")
                for j, cid in enumerate(item["ordered_context_ids"]):
                    _string(cid, f"{at}/ordered_context_ids/{j}")
        elif key == "row_cell_column_pairs":
            _list(child, current)
            for index, item in enumerate(child):
                at = f"{current}/{index}"
                allowed = {"column_index", "cell_index", "header_context_id", "cell_context_id"}
                _keys(item, allowed, allowed, at)
                _integer(item["column_index"], at + "/column_index")
                _integer(item["cell_index"], at + "/cell_index")
                _string(item["header_context_id"], at + "/header_context_id")
                _string(item["cell_context_id"], at + "/cell_context_id")
        elif key in EXTERNAL_LOCATOR_RANGE_KEYS:
            _range(child, current)
        elif key == "character_ranges_0based_halfopen":
            _list(child, current)
            for index, item in enumerate(child):
                _range(item, f"{current}/{index}")


def _ctx_refs(value, path):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _ctx_refs(child, path + "/" + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _ctx_refs(child, f"{path}/{index}")
    elif isinstance(value, str) and value.startswith("CTX-"):
        yield path, value


def _source_ref(value, path):
    _keys(value, {"sha256", "locator", "metadata"}, {"sha256", "locator"}, path)
    _sha(value["sha256"], path + "/sha256")
    _structure(value["locator"], path + "/locator", locator=True)
    if "metadata" in value:
        _keys(value["metadata"], METADATA_KEYS, set(), path + "/metadata")
        for key, child in value["metadata"].items():
            _string(child, path + "/metadata/" + key)


def _row(row, path):
    _result_guard(row, path)
    _keys(row, TOP_KEYS, {"id", "text", "pages", "contexts"}, path)
    _string(row["id"], path + "/id")
    _string(row["text"], path + "/text")
    _list(row["pages"], path + "/pages")
    for index, page in enumerate(row["pages"]):
        _integer(page, f"{path}/pages/{index}", 1)
    _list(row["contexts"], path + "/contexts")
    ids = set()
    for index, context in enumerate(row["contexts"]):
        at = f"{path}/contexts/{index}"
        _keys(context, CONTEXT_KEYS, {"context_id", "kind", "source_ref"}, at)
        _string(context["context_id"], at + "/context_id")
        if context["context_id"] in ids:
            _fail(at, "duplicate context_id")
        ids.add(context["context_id"])
        _string(context["kind"], at + "/kind")
        if context["kind"] not in CONTEXT_KINDS:
            _fail(at + "/kind", "unknown source context kind")
        if context["kind"] != "external_source" and "structure" not in context:
            _fail(at, "ordinary source context requires structure")
        if "structure" in context:
            _structure(context["structure"], at + "/structure")
        if "source_document" in context:
            _string(context["source_document"], at + "/source_document")
        _source_ref(context["source_ref"], at + "/source_ref")
        for key in ("text", "title", "caption"):
            if key in context and context[key] is not None:
                _string(context[key], at + "/" + key, nonempty=False)
        for key in ("headers", "row_cells"):
            if key in context and context[key] is not None:
                _list(context[key], at + "/" + key)
                for j, cell in enumerate(context[key]):
                    _string(cell, f"{at}/{key}/{j}", nonempty=False)
    for index, context in enumerate(row["contexts"]):
        for key in ("structure", "source_ref"):
            for location, cid in _ctx_refs(context.get(key, {}), f"{path}/contexts/{index}/{key}"):
                if cid not in ids:
                    _fail(location, "dangling CTX reference")
    attachments = row.get("source_page_attachments", [])
    _list(attachments, path + "/source_page_attachments")
    attachment_ids = set()
    source_shas = {c["source_ref"]["sha256"] for c in row["contexts"]}
    for index, attachment in enumerate(attachments):
        at = f"{path}/source_page_attachments/{index}"
        _keys(attachment, ATTACHMENT_KEYS, ATTACHMENT_KEYS, at)
        _string(attachment["attachment_id"], at + "/attachment_id")
        if attachment["attachment_id"] in attachment_ids:
            _fail(at, "duplicate page attachment")
        attachment_ids.add(attachment["attachment_id"])
        _integer(attachment["physical_page"], at + "/physical_page", 1)
        _string(attachment["relative_path"], at + "/relative_path")
        _sha(attachment["sha256"], at + "/sha256")
        _sha(attachment["source_pdf_sha256"], at + "/source_pdf_sha256")
        if attachment["source_pdf_sha256"] not in source_shas:
            _fail(at, "page source document is absent from this context graph")


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_loads(text, path):
    def unique_object(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                _fail(path, f"duplicate JSON key is not a source amendment: {key}")
            out[key] = value
        return out

    def finite_constant(value):
        _fail(path, f"nonfinite JSON constant forbidden: {value}")

    return json.loads(text, object_pairs_hook=unique_object, parse_constant=finite_constant)


def _inside(path, root, location):
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(root):
        _fail(location, "file must remain inside the sealed fixture")
    if not resolved.is_file():
        _fail(location, "sealed file is missing")
    return resolved


def load_fixture(source_path, manifest_path):
    """Verify source/manual/pages and return original source rows unchanged.

    Manifest input paths and its reference.jsonl output are metadata only and
    are never opened. The caller's run seal binds the manifest itself.
    """
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent
    source_path = _inside(source_path, root, "source_path")
    if source_path.name != "source.jsonl" or manifest_path.name != "manifest.json":
        _fail("fixture", "expected source.jsonl and manifest.json")
    manifest = _json_loads(manifest_path.read_text(encoding="utf-8"), "manifest")
    if manifest.get("status") != "sealed_development_fixture_not_formal_test_or_human_reference":
        _fail("manifest/status", "fixture is not the sealed development interface")
    outputs = manifest.get("outputs")
    _list(outputs, "manifest/outputs")
    verified_outputs = {}
    # Only these two allowlisted local output files may be opened here.
    for selected in (source_path, root / "manual.md"):
        selected = _inside(selected, root, "manifest/output")
        bindings = [entry for entry in outputs if isinstance(entry, dict)
                    and isinstance(entry.get("path"), str)
                    and Path(entry["path"]).resolve() == selected]
        if len(bindings) != 1:
            _fail("manifest/outputs", f"missing or ambiguous binding for {selected.name}")
        _sha(bindings[0].get("sha256"), "manifest/output/sha256")
        if _digest(selected) != bindings[0]["sha256"]:
            _fail("manifest/outputs", f"sealed {selected.name} SHA mismatch")
        verified_outputs[selected] = bindings[0]["sha256"]
    pages = manifest.get("source_pages")
    _list(pages, "manifest/source_pages")
    page_bindings = {}
    for index, entry in enumerate(pages):
        at = f"manifest/source_pages/{index}"
        _keys(entry, {"path", "sha256"}, {"path", "sha256"}, at)
        _string(entry["path"], at + "/path")
        _sha(entry["sha256"], at + "/sha256")
        page = _inside(entry["path"], root, at)
        if page in page_bindings:
            _fail(at, "duplicate manifest page path")
        if _digest(page) != entry["sha256"]:
            _fail(at, "page image SHA mismatch")
        page_bindings[page] = entry["sha256"]
    rows = []
    with source_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = _json_loads(line, f"source:{line_number}")
            _row(row, f"source:{line_number}")
            for attachment in row.get("source_page_attachments", []):
                relative = Path(attachment["relative_path"])
                if relative.is_absolute():
                    _fail(f"source:{line_number}/attachment", "expected a fixture-relative path")
                page = _inside(root / relative, root, f"source:{line_number}/attachment")
                if page_bindings.get(page) != attachment["sha256"]:
                    _fail(f"source:{line_number}/attachment", "attachment is not bound by sealed page SHA")
            rows.append(row)
    _integer(manifest.get("n"), "manifest/n", 1)
    if len(rows) != manifest["n"] or len({r["id"] for r in rows}) != len(rows):
        _fail("source", "record count or unique source identity differs from seal")
    if any(_digest(path) != sha for path, sha in verified_outputs.items()):
        _fail("fixture", "sealed source/manual changed during loading")
    return rows


def semantic_unit(row):
    """Expose source content/structure; exclude the record selection ID."""
    _row(row, "semantic_unit/source_row")
    return {
        "text": row["text"],
        "pages": copy.deepcopy(row["pages"]),
        "contexts": copy.deepcopy(row["contexts"]),
        "attachments": copy.deepcopy(row.get("source_page_attachments", [])),
    }
