"""Read the sealed source fixture without opening judgments or old runtime.

The fixture is the original id/text/context interface, not a blind-packet
schema instance. Source SHA identifies a source document; page SHA identifies
an attached image. Neither identifier is a classification feature.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path


class PacketInterfaceError(ValueError):
    """An input shape or binding needs an explicit interface amendment."""


class UnsupportedSourceGraph(PacketInterfaceError):
    """A retained source graph is outside the frozen semantic input contract."""


TOP_KEYS = {
    "id", "text", "pages", "contexts", "source_page_attachments",
    "source_image_attachments",
    "source_ref", "source_attachments", "source_references",
}
CONTEXT_KEYS = {
    "context_id", "kind", "source_document", "structure", "source_ref",
    "text", "headers", "title", "row_cells", "caption",
}
FROZEN_CONTEXT_KINDS = {
    "paragraph", "preceding_paragraph", "source_paragraph", "structural_relation",
    "heading", "ordered_list", "ordered_members", "boundary_container", "boundary",
    "parent_paragraph", "source_fragment", "table_header_cell", "table_header",
    "supplemental_group", "cited_reference_group", "cited_reference", "cited_article",
    "document_context", "table_row_cell", "table_row", "source_list", "list_parent",
    "component", "cited_section", "application_scope", "source_chapter_heading",
    "following_heading", "external_source",
    "preceding_flattened_table_data_row", "table_group_row",
}
CONTEXT_KINDS = FROZEN_CONTEXT_KINDS | {
    "same_snapshot_referenced_source_paragraph",
    "same_snapshot_source_numbered_group_geometry",
}
STRUCTURE_STRING_KEYS = {
    "paragraph_id", "relation_id", "unit_id", "parent_context_id", "first_paragraph",
    "last_paragraph", "position", "next_paragraph_id", "first_paragraph_id",
    "last_paragraph_id", "source_role", "component_id", "candidate_paragraph_id",
    "source_unit_id", "current_unit_id", "reference_address", "next_candidate_paragraph_id",
    "component_first_paragraph", "component_last_paragraph", "image_evidence_ref",
    "target_paragraph_id", "follows_context_id", "table_cell", "source_url",
    "snapshot_attachment_id",
    "grid_row_index_convention", "source_group_context_id",
    "source_paragraph_id",
}
STRUCTURE_INT_KEYS = {
    "sequence_index", "candidate_paragraph_start", "candidate_paragraph_end", "column_index",
    "row_index_zero_based",
    "physical_grid_row_index_zero_based",
}
STRUCTURE_STRING_LIST_KEYS = {
    "related_context_ids", "text_child_context_ids", "candidate_line_ids", "paragraph_ids",
    "related_unit_ids", "scope_context_ids",
    "table_text_context_ids",
    "heading_path",
}
STRUCTURE_INT_LIST_KEYS = {"pages", "physical_pages", "source_pages", "column_indices"}
STRUCTURE_MIXED_LIST_KEYS = {"source_lines", "line_ids", "printed_pages"}
STRUCTURE_SCALAR_KEYS = {"article", "section", "line"}
STRUCTURE_SHA_KEYS = {"source_image_sha256"}
GEOMETRY_KEYS = {
    "layout_type", "actual_viewed_physical_pages", "table_cells_or_merges",
    "diagram_arrows", "rule1_condition_group", "rule2_due_condition_group",
    "rule2_not_due_adjustment_group", "cross_page_joins",
    "rule2_other_shared_definitions", "global_scope_resources",
}
STRUCTURE_KEYS = (STRUCTURE_STRING_KEYS | STRUCTURE_INT_KEYS | STRUCTURE_STRING_LIST_KEYS
                  | STRUCTURE_INT_LIST_KEYS | STRUCTURE_MIXED_LIST_KEYS
                  | STRUCTURE_SCALAR_KEYS | STRUCTURE_SHA_KEYS
                  | GEOMETRY_KEYS
                  | {"child_groups", "row_cell_column_pairs", "physical_merged_cells"})
EXTERNAL_LOCATOR_STRING_KEYS = {
    "document_title", "sections", "local_paragraph_identifier", "section_and_paragraph",
    "json_pointer",
}
EXTERNAL_LOCATOR_INT_KEYS = {
    "txt_line_end_inclusive_1based", "txt_line_start_1based", "html_body_paragraph_index_1based",
}
EXTERNAL_LOCATOR_RANGE_KEYS = {
    "character_range_0based_halfopen", "utf8_byte_range_0based_halfopen",
}
LOCATOR_KEYS = (STRUCTURE_KEYS | EXTERNAL_LOCATOR_STRING_KEYS | EXTERNAL_LOCATOR_INT_KEYS
               | EXTERNAL_LOCATOR_RANGE_KEYS
               | {"character_ranges_0based_halfopen", "dom_occurrences", "html_lines_1based", "regions"})
METADATA_KEYS = {
    "document_date", "document_number", "original_url", "republication_date", "source_date",
    "source_document_kind", "source_title", "source_url", "policy_document_date",
    "policy_document_number", "republication_datetime", "source_publication_date",
}
ATTACHMENT_KEYS = {
    "attachment_id", "physical_page", "relative_path", "sha256", "source_pdf_sha256",
}
IMAGE_ATTACHMENT_KEYS = {
    "attachment_id", "mime_type", "relative_path", "sha256", "source_url",
}
RAW_ATTACHMENT_KEYS = ATTACHMENT_KEYS | {"render_dpi", "kind"}
SOURCE_REFERENCE_KEYS = {
    "source_resource_id", "context_id", "source_field", "literal_reference",
    "literal_relation_type",
}
RESOURCE_KEYS = {
    "source_resource_id", "source_sha256", "snapshot", "snapshot_sha256",
    "document_title", "document_year", "official_url", "official_publication_date",
    "metadata_status", "source_texts", "source_geometry", "source_page_assets", "scope",
}
RESOURCE_TEXT_KEYS = {
    "source_resource_id", "source_sha256", "source_path", "kind", "text", "text_sha256",
    "heading_path", "source_char_interval_footerless_whitespace_normalized", "source_ref",
}
FORBIDDEN_KEYS = {
    "label", "labels", "prediction", "predictions", "expected", "expected_labels", "gold",
    "reference_label", "reference_labels", "original_coder_answer", "dimension_reasons",
    "innovation_subtypes", "fairness_subtypes", "score", "confidence", "rationale",
    "selection_reasons", "sampling_stratum", "weight", "pi", "manual",
    "verified_context_certificates", "rule_hit", "coder_role", "judgment", "judgement",
}
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_IMAGE_MIME = re.compile(r"image/[A-Za-z0-9][A-Za-z0-9.+-]*\Z")


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


def _string_list(value, path):
    _list(value, path)
    for index, item in enumerate(value):
        _string(item, f"{path}/{index}")


def _page_list(value, path):
    _list(value, path)
    for index, item in enumerate(value):
        _integer(item, f"{path}/{index}", 1)


def _bbox(value, path):
    _list(value, path)
    if len(value) != 4:
        _fail(path, "expected four xyxy coordinates")
    for index, number in enumerate(value):
        if type(number) not in {int, float} or not math.isfinite(number) or number < 0:
            _fail(f"{path}/{index}", "expected a finite nonnegative coordinate")
    if value[0] >= value[2] or value[1] >= value[3]:
        _fail(path, "xyxy coordinates must be ordered and nonempty")


def _regions(value, path):
    _list(value, path)
    allowed = {"physical_page", "printed_page", "bbox_pdf_points_xyxy",
               "bbox_220dpi_px_xyxy", "page_asset"}
    for index, region in enumerate(value):
        at = f"{path}/{index}"
        _keys(region, allowed, allowed, at)
        _integer(region["physical_page"], at + "/physical_page", 1)
        _integer(region["printed_page"], at + "/printed_page", 1)
        for key in ("bbox_pdf_points_xyxy", "bbox_220dpi_px_xyxy"):
            _bbox(region[key], at + "/" + key)
        _string(region["page_asset"], at + "/page_asset")
        if Path(region["page_asset"]).is_absolute():
            _fail(at + "/page_asset", "expected original relative page metadata")


def _geometry(value, path, *, context=False):
    allowed = GEOMETRY_KEYS | ({"related_context_ids"} if context else set())
    _keys(value, allowed, GEOMETRY_KEYS, path)
    _string(value["layout_type"], path + "/layout_type")
    _page_list(value["actual_viewed_physical_pages"], path + "/actual_viewed_physical_pages")
    for key in ("table_cells_or_merges", "diagram_arrows"):
        _list(value[key], path + "/" + key)
        if value[key]:
            _fail(path + "/" + key, "nonempty geometry requires an explicit interface amendment")
    group_keys = {"parent_resource_id", "operator_printed", "operator", "shared_scope",
                  "numbered_members", "renewal_period_text", "member3_submembers", "geometry_note"}
    common = {"parent_resource_id", "operator_printed", "operator", "shared_scope", "numbered_members"}
    for key in ("rule1_condition_group", "rule2_due_condition_group", "rule2_not_due_adjustment_group"):
        at = path + "/" + key
        group = value[key]
        _keys(group, group_keys, common, at)
        for name, child in group.items():
            if name in {"numbered_members", "member3_submembers"}:
                _string_list(child, at + "/" + name)
            else:
                _string(child, at + "/" + name)
    _list(value["cross_page_joins"], path + "/cross_page_joins")
    for index, join in enumerate(value["cross_page_joins"]):
        at = f"{path}/cross_page_joins/{index}"
        allowed_join = ({"resource_id", "pages"} if isinstance(join, dict) and "resource_id" in join
                        else {"rule3_heading_page", "rule3_common_predicate_page", "note"})
        _keys(join, allowed_join, allowed_join, at)
        for key, child in join.items():
            if key == "pages":
                _page_list(child, at + "/" + key)
            elif key.endswith("_page"):
                _integer(child, at + "/" + key, 1)
            else:
                _string(child, at + "/" + key)
    for key in ("rule2_other_shared_definitions", "global_scope_resources", "related_context_ids"):
        if key in value:
            _string_list(value[key], path + "/" + key)


def _structure(value, path, *, locator=False):
    _keys(value, LOCATOR_KEYS if locator else STRUCTURE_KEYS, set(), path)
    if set(value) & GEOMETRY_KEYS:
        _geometry({k: v for k, v in value.items() if k in GEOMETRY_KEYS | {"related_context_ids"}},
                  path, context=True)
    for key, child in value.items():
        current = path + "/" + key
        if key in STRUCTURE_STRING_KEYS | EXTERNAL_LOCATOR_STRING_KEYS:
            _string(child, current)
        elif key in STRUCTURE_SHA_KEYS:
            _sha(child, current)
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
                if isinstance(item, dict) and "header_index" in item:
                    allowed = {"column_index", "cell_index", "header_index"}
                else:
                    allowed = {"column_index", "cell_index", "header_context_id", "cell_context_id"}
                _keys(item, allowed, allowed, at)
                _integer(item["column_index"], at + "/column_index")
                _integer(item["cell_index"], at + "/cell_index")
                if "header_index" in item:
                    _integer(item["header_index"], at + "/header_index")
                else:
                    _string(item["header_context_id"], at + "/header_context_id")
                    _string(item["cell_context_id"], at + "/cell_context_id")
        elif key == "physical_merged_cells":
            _list(child, current)
            allowed = {
                "column_index", "physical_grid_column_span", "physical_grid_row_span",
                "physical_grid_row_start_zero_based", "text",
            }
            for index, item in enumerate(child):
                at = f"{current}/{index}"
                _keys(item, allowed, allowed, at)
                for field in ("column_index", "physical_grid_row_start_zero_based"):
                    _integer(item[field], at + "/" + field)
                for field in ("physical_grid_column_span", "physical_grid_row_span"):
                    _integer(item[field], at + "/" + field, 1)
                _string(item["text"], at + "/text", nonempty=False)
        elif key in EXTERNAL_LOCATOR_RANGE_KEYS:
            _range(child, current)
        elif key == "character_ranges_0based_halfopen":
            _list(child, current)
            for index, item in enumerate(child):
                _range(item, f"{current}/{index}")
        elif key == "regions":
            _regions(child, current)
        elif key in GEOMETRY_KEYS:
            pass  # The original geometry object was validated without projecting roles.


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
    _keys(value, {"sha256", "locator", "metadata", "source_resource_id"}, {"sha256", "locator"}, path)
    _sha(value["sha256"], path + "/sha256")
    _structure(value["locator"], path + "/locator", locator=True)
    if "source_resource_id" in value:
        _string(value["source_resource_id"], path + "/source_resource_id")
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
    if "source_ref" in row:
        _source_ref(row["source_ref"], path + "/source_ref")
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
    for location, cid in _ctx_refs(row.get("source_ref", {}), path + "/source_ref"):
        if cid not in ids:
            _fail(location, "dangling CTX reference")
    attachments = row.get("source_page_attachments", [])
    _list(attachments, path + "/source_page_attachments")
    attachment_ids = set()
    source_shas = {c["source_ref"]["sha256"] for c in row["contexts"]}
    if "source_ref" in row:
        source_shas.add(row["source_ref"]["sha256"])
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
    raw_attachments = row.get("source_attachments", [])
    _list(raw_attachments, path + "/source_attachments")
    for index, attachment in enumerate(raw_attachments):
        at = f"{path}/source_attachments/{index}"
        _keys(attachment, RAW_ATTACHMENT_KEYS, RAW_ATTACHMENT_KEYS, at)
        _string(attachment["attachment_id"], at + "/attachment_id")
        if attachment["attachment_id"] in attachment_ids:
            _fail(at, "duplicate source attachment identity")
        attachment_ids.add(attachment["attachment_id"])
        _integer(attachment["physical_page"], at + "/physical_page", 1)
        _integer(attachment["render_dpi"], at + "/render_dpi", 1)
        _string(attachment["relative_path"], at + "/relative_path")
        _string(attachment["kind"], at + "/kind")
        _sha(attachment["sha256"], at + "/sha256")
        _sha(attachment["source_pdf_sha256"], at + "/source_pdf_sha256")
        if attachment["source_pdf_sha256"] not in source_shas:
            _fail(at, "page source document is absent from this context graph")
    references = row.get("source_references", [])
    _list(references, path + "/source_references")
    for index, reference in enumerate(references):
        at = f"{path}/source_references/{index}"
        _keys(reference, SOURCE_REFERENCE_KEYS, SOURCE_REFERENCE_KEYS, at)
        for key, child in reference.items():
            if key == "context_id" and child is None:
                continue
            _string(child, at + "/" + key)
        if reference["context_id"] is not None and reference["context_id"] not in ids:
            _fail(at + "/context_id", "dangling supplied context reference")
    images = row.get("source_image_attachments", [])
    _list(images, path + "/source_image_attachments")
    for index, attachment in enumerate(images):
        at = f"{path}/source_image_attachments/{index}"
        _keys(attachment, IMAGE_ATTACHMENT_KEYS, IMAGE_ATTACHMENT_KEYS, at)
        _string(attachment["attachment_id"], at + "/attachment_id")
        if attachment["attachment_id"] in attachment_ids:
            _fail(at, "duplicate source attachment identity")
        attachment_ids.add(attachment["attachment_id"])
        _string(attachment["mime_type"], at + "/mime_type")
        if not _IMAGE_MIME.fullmatch(attachment["mime_type"]):
            _fail(at + "/mime_type", "expected an image MIME type")
        _string(attachment["relative_path"], at + "/relative_path")
        _sha(attachment["sha256"], at + "/sha256")
        _string(attachment["source_url"], at + "/source_url")
    image_shas = {attachment["sha256"] for attachment in images}
    for index, context in enumerate(row["contexts"]):
        for field, location in (("structure", context.get("structure", {})),
                                ("source_ref/locator", context["source_ref"]["locator"])):
            if ("source_image_sha256" in location
                    and location["source_image_sha256"] not in image_shas):
                _fail(f"{path}/contexts/{index}/{field}/source_image_sha256",
                      "source geometry image is absent from original image attachments")


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


def _load_legacy_fixture(source_path, manifest_path):
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
            if (set(row) & {"source_ref", "source_attachments", "source_references"}
                    or any(c["kind"] not in FROZEN_CONTEXT_KINDS
                           or "source_resource_id" in c["source_ref"] for c in row["contexts"])):
                _fail(f"source:{line_number}", "source resource extensions require an explicit design binding")
            for field in ("source_page_attachments", "source_image_attachments"):
                for index, attachment in enumerate(row.get(field, [])):
                    at = f"source:{line_number}/{field}/{index}"
                    relative = Path(attachment["relative_path"])
                    if relative.is_absolute():
                        _fail(at, "expected a fixture-relative path")
                    asset = _inside(root / relative, root, at)
                    if page_bindings.get(asset) != attachment["sha256"]:
                        _fail(at, "attachment is not bound by sealed asset SHA")
            rows.append(row)
    _integer(manifest.get("n"), "manifest/n", 1)
    if len(rows) != manifest["n"] or len({r["id"] for r in rows}) != len(rows):
        _fail("source", "record count or unique source identity differs from seal")
    if any(_digest(path) != sha for path, sha in verified_outputs.items()):
        _fail("fixture", "sealed source/manual changed during loading")
    return rows


def _absolute_path(value, location):
    _string(value, location)
    if not Path(value).is_absolute():
        _fail(location, "expected an explicitly configured absolute path")
    return Path(value).resolve()


def _configured_file(binding, location):
    _keys(binding, {"path", "sha256"}, {"path", "sha256"}, location)
    path = _absolute_path(binding["path"], location + "/path")
    _sha(binding["sha256"], location + "/sha256")
    if not path.is_file():
        _fail(location, "configured material is missing")
    if _digest(path) != binding["sha256"]:
        _fail(location, "configured material SHA mismatch")
    return path


def _bound_relative_asset(relative, base, pages, location):
    _string(relative, location + "/relative_path")
    if Path(relative).is_absolute():
        _fail(location, "expected the original relative asset path")
    asset = (base / relative).resolve()
    if asset not in pages:
        _fail(location, "asset path is not in the exact configured allowlist")
    return pages[asset]


def _check_asset(attachment, base, pages, location):
    binding = _bound_relative_asset(attachment["relative_path"], base, pages, location)
    for key in ("sha256", "physical_page", "source_pdf_sha256"):
        if key in attachment and attachment[key] != binding[key]:
            _fail(location + "/" + key, "asset differs from exact configured page binding")


def _check_regions(ref, pages, location):
    locator = ref["locator"]
    for index, region in enumerate(locator.get("regions", [])):
        at = f"{location}/locator/regions/{index}"
        matched = [asset for asset, binding in pages.items()
                   if binding["physical_page"] == region["physical_page"]
                   and binding["source_pdf_sha256"] == ref["sha256"]
                   and region["page_asset"] == "pages/" + asset.name]
        if len(matched) != 1:
            _fail(at, "region page metadata is not bound to one exact configured asset")
        if "physical_pages" in locator and region["physical_page"] not in locator["physical_pages"]:
            _fail(at, "region page is absent from original locator pages")


def _resource_ids(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from _resource_ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from _resource_ids(child)
    elif isinstance(value, str) and value.startswith("SOURCEPARAGRAPH-"):
        yield value


def _resource(value, base, pages, path):
    _result_guard(value, path)
    _keys(value, RESOURCE_KEYS, RESOURCE_KEYS, path)
    for key in ("source_resource_id", "snapshot", "document_title", "metadata_status", "scope"):
        _string(value[key], path + "/" + key)
    snapshot = _absolute_path(value["snapshot"], path + "/snapshot")  # Metadata only; never open.
    for key in ("source_sha256", "snapshot_sha256"):
        _sha(value[key], path + "/" + key)
    if value["source_sha256"] != value["snapshot_sha256"]:
        _fail(path, "resource source and snapshot SHA bindings differ")
    _integer(value["document_year"], path + "/document_year", 1)
    for key in ("official_url", "official_publication_date"):
        if value[key] is not None:
            _string(value[key], path + "/" + key)
    _list(value["source_texts"], path + "/source_texts")
    texts = {}
    for index, text in enumerate(value["source_texts"]):
        at = f"{path}/source_texts/{index}"
        _keys(text, RESOURCE_TEXT_KEYS, RESOURCE_TEXT_KEYS, at)
        for key in ("source_resource_id", "source_path", "kind", "text"):
            _string(text[key], at + "/" + key)
        for key in ("source_sha256", "text_sha256"):
            _sha(text[key], at + "/" + key)
        _string_list(text["heading_path"], at + "/heading_path")
        _range(text["source_char_interval_footerless_whitespace_normalized"],
               at + "/source_char_interval_footerless_whitespace_normalized")
        _source_ref(text["source_ref"], at + "/source_ref")
        if (text["source_sha256"] != value["source_sha256"]
                or text["source_ref"]["sha256"] != value["source_sha256"]
                or text["source_ref"].get("source_resource_id") != value["source_resource_id"]
                or _absolute_path(text["source_path"], at + "/source_path") != snapshot):
            _fail(at, "source paragraph identity differs from its original resource")
        if hashlib.sha256(text["text"].encode("utf-8")).hexdigest() != text["text_sha256"]:
            _fail(at, "source paragraph text SHA mismatch")
        if text["heading_path"] != text["source_ref"]["locator"].get("heading_path"):
            _fail(at, "source paragraph heading metadata differs from its locator")
        paragraph_id = text["source_resource_id"]
        if paragraph_id in texts:
            _fail(at, "duplicate resource paragraph identity")
        _check_regions(text["source_ref"], pages, at + "/source_ref")
        texts[paragraph_id] = text
    _geometry(value["source_geometry"], path + "/source_geometry")
    for paragraph_id in _resource_ids(value["source_geometry"]):
        if paragraph_id not in texts:
            _fail(path + "/source_geometry", "dangling resource paragraph identity")
    _list(value["source_page_assets"], path + "/source_page_assets")
    asset_keys = (ATTACHMENT_KEYS - {"attachment_id"}) | {"render_dpi"}
    seen_assets = set()
    for index, asset in enumerate(value["source_page_assets"]):
        at = f"{path}/source_page_assets/{index}"
        _keys(asset, asset_keys, asset_keys, at)
        _integer(asset["physical_page"], at + "/physical_page", 1)
        _integer(asset["render_dpi"], at + "/render_dpi", 1)
        _sha(asset["sha256"], at + "/sha256")
        _sha(asset["source_pdf_sha256"], at + "/source_pdf_sha256")
        _check_asset(asset, base, pages, at)
        resolved = (base / asset["relative_path"]).resolve()
        if resolved in seen_assets:
            _fail(at, "duplicate resource page asset")
        seen_assets.add(resolved)
        if asset["source_pdf_sha256"] != value["source_sha256"]:
            _fail(at, "resource page belongs to a different source SHA")
    if seen_assets != set(pages):
        _fail(path + "/source_page_assets", "resource assets differ from exact configured asset set")
    return texts


def _check_resource_row(row, resource, texts, base, pages, path):
    paragraph_contexts = {}
    for context in row["contexts"]:
        if context["kind"] == "same_snapshot_referenced_source_paragraph":
            paragraph_id = context.get("structure", {}).get("source_paragraph_id")
            if paragraph_id not in texts:
                _fail(path + "/contexts", "supplied source paragraph is absent from bound resource")
            if paragraph_id in paragraph_contexts.values():
                _fail(path + "/contexts", "duplicate supplied resource paragraph copy")
            paragraph_contexts[context["context_id"]] = paragraph_id
            original = texts[paragraph_id]
            locator = copy.deepcopy(context["source_ref"]["locator"])
            if locator.pop("source_paragraph_id", None) != paragraph_id:
                _fail(path + "/contexts", "source paragraph locator identity differs from structure")
            if (context.get("text") != original["text"]
                    or context["structure"].get("heading_path") != original["heading_path"]
                    or locator != original["source_ref"]["locator"]):
                _fail(path + "/contexts", "supplied paragraph text or locator differs from original resource")

    def restore_ids(value):
        if isinstance(value, dict):
            return {k: restore_ids(v) for k, v in value.items()}
        if isinstance(value, list):
            return [restore_ids(v) for v in value]
        if isinstance(value, str) and value in paragraph_contexts:
            return paragraph_contexts[value]
        return value

    for index, context in enumerate(row["contexts"]):
        at = f"{path}/contexts/{index}"
        ref = context["source_ref"]
        if (context["kind"] not in FROZEN_CONTEXT_KINDS
                and "source_resource_id" not in ref):
            _fail(at + "/source_ref", "resource context requires explicit original resource identity")
        if ref.get("source_resource_id") is not None:
            if (ref["source_resource_id"] != resource["source_resource_id"]
                    or ref["sha256"] != resource["source_sha256"]):
                _fail(at + "/source_ref", "supplied source reference differs from bound resource")
        _check_regions(ref, pages, at + "/source_ref")
        if context["kind"] == "same_snapshot_source_numbered_group_geometry":
            geometry = {k: v for k, v in context["structure"].items() if k != "related_context_ids"}
            if restore_ids(geometry) != resource["source_geometry"]:
                _fail(at + "/structure", "supplied geometry differs from original resource geometry")
    if "source_ref" in row:
        ref = row["source_ref"]
        if (ref.get("source_resource_id") != resource["source_resource_id"]
                or ref["sha256"] != resource["source_sha256"]):
            _fail(path + "/source_ref", "current source reference differs from bound resource")
        _check_regions(ref, pages, path + "/source_ref")
    for index, reference in enumerate(row.get("source_references", [])):
        if reference["source_resource_id"] != resource["source_resource_id"]:
            _fail(f"{path}/source_references/{index}", "supplied reference names an unbound source resource")
    for field in ("source_page_attachments", "source_image_attachments", "source_attachments"):
        for index, asset in enumerate(row.get(field, [])):
            _check_asset(asset, base, pages, f"{path}/{field}/{index}")


def _load_design_fixture(source_path, design_path):
    # Only source-material configuration is consumed; other design metadata is not input.
    design_bytes = design_path.read_bytes()
    design = _json_loads(design_bytes.decode("utf-8"), "design")
    if not isinstance(design, dict):
        _fail("design", "expected an object")
    source_binding = design.get("source")
    _keys(source_binding, {"path", "sha256"}, {"path", "sha256"}, "design/source")
    configured_source = _absolute_path(source_binding["path"], "design/source/path")
    if Path(source_path).resolve() != configured_source:
        _fail("source_path", "source path differs from exact configured material")
    verified = {}
    for key in ("source", "manual", "resource"):
        selected = _configured_file(design.get(key), "design/" + key)
        if selected in verified:
            _fail("design/" + key, "duplicate configured material path")
        verified[selected] = design[key]["sha256"]
    base = _absolute_path(design.get("asset_path_base"), "design/asset_path_base")
    assets = design.get("source_page_assets")
    _list(assets, "design/source_page_assets")
    pages = {}
    page_identities = set()
    for index, asset in enumerate(assets):
        at = f"design/source_page_assets/{index}"
        allowed = {"path", "sha256", "physical_page", "source_pdf_sha256"}
        _keys(asset, allowed, allowed, at)
        _integer(asset["physical_page"], at + "/physical_page", 1)
        _sha(asset["source_pdf_sha256"], at + "/source_pdf_sha256")
        page = _configured_file({k: asset[k] for k in ("path", "sha256")}, at)
        identity = (asset["source_pdf_sha256"], asset["physical_page"])
        if page in pages or page in verified or identity in page_identities:
            _fail(at, "duplicate configured asset path or physical page")
        pages[page] = asset
        page_identities.add(identity)
        verified[page] = asset["sha256"]
    resource_path = Path(design["resource"]["path"]).resolve()
    resource = _json_loads(resource_path.read_text(encoding="utf-8"), "resource")
    texts = _resource(resource, base, pages, "resource")
    rows = []
    with configured_source.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            at = f"source:{line_number}"
            row = _json_loads(line, at)
            _row(row, at)
            _check_resource_row(row, resource, texts, base, pages, at)
            rows.append(row)
    _integer(design.get("n"), "design/n", 1)
    if len(rows) != design["n"] or len({row["id"] for row in rows}) != len(rows):
        _fail("source", "record count or unique source identity differs from design")
    if design_path.read_bytes() != design_bytes or any(_digest(p) != sha for p, sha in verified.items()):
        _fail("design", "configured source materials changed during loading")
    return rows


def load_fixture(source_path, manifest_path):
    """Load bound source rows unchanged through legacy manifest or source design.

    The caller binds the manifest/design SHA. A design's original source resource
    is checked against supplied copies only; no resource text or geometry is
    appended to the input graph. Reference/output paths are never opened.
    """
    manifest_path = Path(manifest_path).resolve()
    if manifest_path.name == "design.json":
        return _load_design_fixture(source_path, manifest_path)
    return _load_legacy_fixture(source_path, manifest_path)


def semantic_unit(row):
    """Expose supported original source content; exclude the selection ID.

    Raw acceptance does not authorize an unsupported graph as semantic input.
    This is the preadaptation reader's type contract, without role conversion.
    """
    _row(row, "semantic_unit/source_row")
    unsupported = sorted({c["kind"] for c in row["contexts"]} - FROZEN_CONTEXT_KINDS)
    if unsupported:
        raise UnsupportedSourceGraph("semantic_unit/contexts: kinds outside frozen input contract: "
                                     + ", ".join(unsupported))
    if row.get("source_references"):
        raise UnsupportedSourceGraph("semantic_unit/source_references: supplied reference graph "
                                     "is outside frozen input contract")
    unit = {
        "text": row["text"],
        "pages": copy.deepcopy(row["pages"]),
        "contexts": copy.deepcopy(row["contexts"]),
        "attachments": copy.deepcopy(row.get("source_page_attachments", [])),
        "source_image_attachments": copy.deepcopy(row.get("source_image_attachments", [])),
    }
    for key in ("source_ref", "source_attachments", "source_references"):
        if key in row:
            unit[key] = copy.deepcopy(row[key])
    return unit
