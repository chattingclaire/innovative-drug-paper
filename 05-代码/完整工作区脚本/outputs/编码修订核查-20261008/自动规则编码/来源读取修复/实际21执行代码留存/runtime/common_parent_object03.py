"""Authenticate a first enumerated item's immediately preceding drug object.

This is a source/object resolver, not a dimension classifier. Structural IDs
and paths are only exact source locators; no document identity is a rule.
Only the current paragraph and its actual immediate predecessor are eligible.
"""

from __future__ import annotations

import copy
import re
import subprocess

from source_context_adapter_v34 import (
    authenticate_context,
    authenticate_target,
    candidate,
    digest,
    norm,
)


VERSION = "common-parent-object03"
_TITLES = re.compile(r"《[^》\r\n]*》|〈[^〉\r\n]*〉")
_FIRST_ITEM = re.compile(
    r"^\s*(?P<marker>一是|第一(?:项|条|点)[、，,.．：:]?|"
    r"[（(]一[）)]|一[、.．]|[（(]1[）)]|1[、.．](?!\d))"
)
_ENUMERATION_LEAD = re.compile(
    r"(?P<lead>(?:(?:具体|主要|分别)?(?:包括|包含)|分为|有)"
    r"(?:以下|下列)(?:(?:几|各|[一二三四五六七八九十\d]+)?"
    r"(?:点|项|事项|要求|内容|方面|条件|情形|措施|要点))?|"
    r"(?:具体(?:内容|要求|条件|事项|安排|措施)?|主要内容|有关要求|要求|条件|事项|安排|措施)如下)"
    r"\s*[：:。]?\s*$"
)
_DRUG_OBJECT = re.compile(r"药品(?!企业|公司|生产企业|经营企业)|药物(?!企业|公司)|用药|制剂|疫苗")
_SENTENCE_BOUNDARY = re.compile(r"[。！？!?；;\r\n]")


def _masked_titles(text: str) -> str:
    return _TITLES.sub(lambda match: " " * len(match.group()), text)


def _same_supplied_paragraph(supplied: object, actual: dict) -> bool:
    if not isinstance(supplied, dict) or supplied.get("text") != actual.get("text"):
        return False
    if supplied.get("paragraph_id") is not None and supplied["paragraph_id"] != actual.get("id"):
        return False
    if supplied.get("pages") is not None and supplied["pages"] != actual.get("pages"):
        return False
    return True


def _context(record: dict, paragraph: dict) -> dict:
    return {
        "paragraph_id": paragraph["id"],
        "text": paragraph["text"],
        "pages": copy.deepcopy(paragraph.get("pages", [])),
        "source_lines": copy.deepcopy(paragraph.get("line_ids", [])),
        "source_path": record.get("unit_source") or record.get("source"),
        "source_sha256": record.get("unit_source_sha256") or record.get("source_sha256"),
        "candidate_path": record["candidate_file"],
        "candidate_sha256": record.get("candidate_sha256"),
    }


def resolve_enumerated_drug_object(record: dict) -> dict | None:
    """Return an authenticated certificate, or None when no eligible relation exists.

Requirements: exact authenticated target; exact unit/current-paragraph binding;
    current first-item marker; actual immediate predecessor equal to the supplied
    predecessor; an explicit enumeration lead at that predecessor's end; and a
    drug object in its same final sentence within 120 characters of the lead.
    Titles cannot supply that object. The target uses authenticate_target plus
    exact candidate-unit/paragraph membership; parent uses authenticate_context.
    No dimension, criterion, or substantive requirement is inherited from parent.
    Source/candidate authentication and dependency errors propagate explicitly;
    they are material/technical failures, never an ordinary no-object result.
    """
    if not isinstance(record, dict):
        return None
    try:
        text = record.get("unit_text")
        if not isinstance(text, str) or not _FIRST_ITEM.match(text):
            return None
        authenticate_target(record)
        doc = candidate(record["candidate_file"])
        units = [unit for unit in doc.get("unit_candidates", [])
                 if unit.get("id") == record.get("unit_id")]
        if len(units) != 1 or units[0].get("text") != text:
            return None
        target = units[0]
        paragraphs = doc.get("paragraphs", [])
        indexes = [index for index, paragraph in enumerate(paragraphs)
                   if paragraph.get("id") == target.get("paragraph_id")]
        if len(indexes) != 1 or indexes[0] == 0:
            return None
        index = indexes[0]
        current, parent = paragraphs[index], paragraphs[index - 1]
        if not isinstance(current.get("text"), str) or not isinstance(parent.get("text"), str):
            return None
        if len([p for p in paragraphs if p.get("id") == parent.get("id")]) != 1:
            return None
        current_marker = _FIRST_ITEM.match(current["text"])
        unit_marker = _FIRST_ITEM.match(text)
        if not current_marker or current_marker.group("marker") != unit_marker.group("marker"):
            return None
        # A later sub-unit cannot claim the paragraph's initial list relation.
        if not norm(current["text"]).startswith(norm(text)):
            return None
        if target.get("pages") is not None and record.get("pages") is not None and target["pages"] != record["pages"]:
            return None
        contexts = record.get("paragraph_context", [])
        bound = [context for context in contexts if isinstance(context, dict)
                 and context.get("paragraph_id") == current.get("id")]
        if len(bound) != 1 or not _same_supplied_paragraph(bound[0], current):
            return None
        if not _same_supplied_paragraph(record.get("immediately_preceding_paragraph"), parent):
            return None
        shared = record.get("llm_v29_shared_context", {})
        if isinstance(shared, dict) and "immediately_preceding_paragraph" in shared:
            if not _same_supplied_paragraph(shared["immediately_preceding_paragraph"], parent):
                return None
        masked_parent = _masked_titles(parent["text"])
        lead = _ENUMERATION_LEAD.search(masked_parent)
        if not lead:
            return None
        boundaries = list(_SENTENCE_BOUNDARY.finditer(masked_parent, 0, lead.start("lead")))
        sentence_start = boundaries[-1].end() if boundaries else 0
        object_start = max(sentence_start, lead.start("lead") - 120)
        objects = list(_DRUG_OBJECT.finditer(masked_parent, object_start, lead.start("lead")))
        if not objects:
            return None
        drug_object = objects[0]
        current_context = _context(record, current)
        parent_context = authenticate_context(_context(record, parent))
        source_path = record.get("unit_source") or record.get("source")
        source_sha = record.get("unit_source_sha256") or record.get("source_sha256")
        return {
            "version": VERSION,
            "role": "authenticated_enumerated_drug_object_only",
            "drug_scope": True,
            "dimension_assignment": False,
            "labels_may_be_copied": False,
            "current_unit_id": record["unit_id"],
            "current_unit_sha256": digest(text),
            "current_paragraph_id": current["id"],
            "parent_paragraph_id": parent["id"],
            "parent_text": parent["text"],
            "parent_text_sha256": digest(parent["text"]),
            "source_path": source_path,
            "source_sha256": source_sha,
            "candidate_path": record["candidate_file"],
            "candidate_sha256": record.get("candidate_sha256"),
            "target_authentication": {
                "authenticated": True,
                "method": "source_context_adapter_v34.authenticate_target",
            },
            "current_paragraph_context": current_context,
            "current_paragraph_binding": {
                "authenticated": True,
                "method": "authenticate_target_and_exact_candidate_unit_paragraph_membership",
                "paragraph_starts_with_current_unit": True,
                "independent_current_paragraph_literal_reproduction_performed": False,
            },
            "parent_context": parent_context,
            "relation": {
                "kind": "immediate_preceding_explicit_enumeration_first_item",
                "actual_parent_index": index - 1,
                "actual_current_index": index,
                "no_intervening_candidate_paragraph": True,
                "current_first_item_marker": unit_marker.group("marker"),
                "parent_enumeration_lead": parent["text"][lead.start("lead"):lead.end("lead")],
                "parent_enumeration_lead_start": lead.start("lead"),
                "parent_enumeration_lead_end": lead.end("lead"),
                "drug_object_quote": parent["text"][drug_object.start():drug_object.end()],
                "drug_object_start": drug_object.start(),
                "drug_object_end": drug_object.end(),
                "usage": "drug_object_only_no_parent_dimensions_or_requirements",
            },
        }
    except (AssertionError, ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError):
        raise


__all__ = ["resolve_enumerated_drug_object"]
