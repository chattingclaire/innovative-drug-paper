"""Candidate03: explicit improvement and authenticated registration-class rows.

No result labels, IDs, department or path meaning are used as semantic criteria.
File locators are consumed only by existing source authentication interfaces.
"""

from __future__ import annotations

import copy
import hashlib
import re

from common_if_relations import REGISTRATION_CATEGORY

COMMON_RULES_SHA256 = "6b902fd7518379d5edc8e100c1192b627202a0069e69d6e40fea72cad7880a28"
VERSION = "common-if-extensions03-bounded-01"
COMMON_BASIS = "五维共用编码规则 I 路径1、2；固定SHA256=" + COMMON_RULES_SHA256

_ATTRIBUTE = r"(?:给药频次|给药频率|给药途径|给药方式|释放特征|剂型|制剂|配方|药物结构|治疗属性)"
_MODIFY = re.compile(
    rf"(?:在)?(?:对)?(?:(?:该药|本药|药物|药品)(?:的)?)?{_ATTRIBUTE}"
    r"(?:尚未|并未|未|不再)?(?:进行|作|做|实施)(?:了)?"
    r"(?:实质(?:性)?)?(?:改良|改进)(?:时)?"
)
_QUALIFIED_RD = re.compile(
    r"(?:改良型新药|改良型药品|改良型生物制品)(?:的)?(?:临床)?(?:研发|开发|研究)"
)
_OTHER_OBJECT = re.compile(r"设备|器械|软件|管理系统|文件格式|保密|文件名|栏目|字体")
_CATEGORY = re.compile(REGISTRATION_CATEGORY)
_CLASS_NUMBER = re.compile(r"[0-9一二三四五六七八九十]+(?:\.[0-9]+)?类")
_TITLE = re.compile(r"《[^》\n]*》")


def _mask_titles(text):
    return _TITLE.sub(lambda m: "□" * len(m.group()), text)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _evidence(text, start, end, rule, dependency):
    return {"dimension": "I", "rule": rule, "start": start, "end": end,
            "text": text[start:end], "subtype": "attribute", "basis": COMMON_BASIS,
            "common_basis": COMMON_BASIS, "context_dependency": dependency}


def _current_paragraphs(record):
    """Bind supplied paragraphs to the exact current candidate and source.

    This does not assign I; it certifies same-paragraph membership.  Unlike a
    supplied `verified=True`, the existing authenticators check actual bytes.
    """
    from source_context_adapter_v33 import candidate
    from source_context_adapter_v34 import authenticate_context, authenticate_target

    supplied = record.get("paragraph_context", [])
    if not supplied:
        return []
    shared = record.get("llm_v29_shared_context", {})
    if "paragraph_context" in shared and shared["paragraph_context"] != supplied:
        raise ValueError("I extension: paragraph differs across shared materials")
    authenticate_target(record)
    document = candidate(record["candidate_file"])
    unit = next(u for u in document.get("unit_candidates", [])
                if u.get("id") == record.get("unit_id"))
    paragraphs = document.get("paragraphs", [])
    bound = []
    for context in supplied:
        if not isinstance(context, dict) or record["unit_text"] not in context.get("text", ""):
            continue
        if unit.get("paragraph_id") != context.get("paragraph_id"):
            continue
        actual = [p for p in paragraphs if p.get("id") == context.get("paragraph_id")]
        if (len(actual) != 1 or actual[0].get("text") != context["text"]
                or actual[0].get("pages", []) != context.get("pages", [])):
            raise ValueError("I extension: paragraph text/pages do not bind current unit")
        cert = copy.deepcopy(context)
        cert.update({"source_path": record.get("unit_source") or record.get("source"),
                     "source_sha256": record.get("unit_source_sha256") or record.get("source_sha256"),
                     "candidate_path": record["candidate_file"],
                     "candidate_sha256": record["candidate_sha256"]})
        if not cert.get("source_lines"):
            cert["source_lines"] = actual[0].get("line_ids") or actual[0].get("source_lines") or []
        cert = authenticate_context(cert)
        bound.append(cert)
    return bound


def _improvement_relations(record):
    text = record["unit_text"]
    matches = []
    for match in _MODIFY.finditer(_mask_titles(text)):
        quote = text[match.start():match.end()]
        # Bare `改进` or ordinary change is not an independent improvement claim.
        if "改良" not in quote and not re.search(r"实质(?:性)?改进", quote):
            continue
        if _OTHER_OBJECT.search(quote):
            continue
        matches.append(match)
    if not matches:
        return []
    paragraphs = None
    evidence = []
    for match in matches:
        quote = match.group()
        if (re.search(r"该药|本药|药物|药品", quote)
                and re.search(r"实质(?:性)?(?:改良|改进)", quote)):
            evidence.append(_evidence(text, match.start(), match.end(),
                "COMMON03_I_current_explicit_substantive_improvement",
                {"kind": "self_contained_current_drug_substantive_improvement",
                 "current_unit_sha256": _sha(text),
                 "usage": "Current drug object, product attribute and substantive improvement are explicit; no context labels inherited."}))
            continue
        if paragraphs is None:
            paragraphs = _current_paragraphs(record)
        for paragraph in paragraphs:
            ptext = paragraph["text"]
            if ptext.count(text) != 1:
                raise ValueError("I extension: current-unit membership in paragraph is ambiguous")
            target_start = ptext.index(text)
            # Only the same paragraph's preceding qualified R&D scope is used.
            # Other safety, efficacy or convenience requirements are not copied.
            prefix = _mask_titles(ptext[:target_start])
            scope = list(_QUALIFIED_RD.finditer(prefix))
            if not scope:
                continue
            anchor = scope[-1]
            dependency = {
                "kind": "authenticated_same_paragraph_improved_drug_rd_object",
                "paragraph_id": paragraph["paragraph_id"],
                "paragraph_text_sha256": _sha(ptext),
                "antecedent_text": anchor.group(),
                "antecedent_start_in_paragraph": anchor.start(),
                "antecedent_end_in_paragraph": anchor.end(),
                "current_unit_start_in_paragraph": target_start,
                "current_unit_end_in_paragraph": target_start + len(text),
                "current_unit_sha256": _sha(text),
                "source_path": paragraph["source_path"],
                "source_sha256": paragraph["source_sha256"],
                "candidate_path": paragraph["candidate_path"],
                "candidate_sha256": paragraph["candidate_sha256"],
                "pages": paragraph.get("pages", []),
                "source_lines": paragraph.get("source_lines", []),
                "authentication": paragraph["authentication_v34"],
                "usage": "Only resolve the current explicit improvement's drug-R&D object; no neighboring dimension or benefit inherited.",
            }
            evidence.append(_evidence(text, match.start(), match.end(),
                                      "COMMON03_I_authenticated_explicit_improvement", dependency))
            break
    return evidence


def _registration_relations(record):
    if not record.get("verified_table_context_v4") and not record.get("llm_v29_shared_context", {}).get("verified_table_context_v4"):
        return []
    from table_material_adapter_v321 import verified_rows

    text = record["unit_text"]
    evidence = []
    for row in verified_rows(record):
        cert = row["certificate"]
        title = cert["table_title"]
        if not (re.search(r"药品|化学药|中药|生物制品|疫苗", title)
                and "注册分类" in title):
            continue
        columns = cert["column_names"]
        class_cols = [i for i, c in enumerate(columns) if c in {"分类", "注册分类", "注册类别"}]
        content_cols = [i for i, c in enumerate(columns) if c in {"内容", "分类内容", "类别内容", "类别名称"}]
        if len(class_cols) != 1 or len(content_cols) != 1:
            continue
        ci, di = class_cols[0], content_cols[0]
        cells = cert["raw_row_cells"]
        if not _CLASS_NUMBER.fullmatch(cells[ci].strip()):
            continue
        if not _CATEGORY.fullmatch(cells[di].strip()):
            continue
        offsets = []
        cursor = 0
        for cell in cells:
            offsets.append((cursor, cursor + len(cell)))
            cursor += len(cell) + len(" | ")
        start = min(offsets[ci][0], offsets[di][0])
        end = max(offsets[ci][1], offsets[di][1])
        dependency = {k: copy.deepcopy(v) for k, v in row.items() if k != "certificate"}
        dependency.update({
            "kind": "authenticated_current_registration_classification_cell",
            "antecedent_text": cert["text"], "table_title": title,
            "column_names": columns, "classification_column": columns[ci],
            "classification_cell": cells[ci], "classification_content_column": columns[di],
            "classification_content_cell": cells[di], "raw_row_cells": cells,
            "current_unit_sha256": _sha(text), "source_image": cert["source_image"],
            "source_image_sha256": cert["source_image_sha256"],
            "row_index_zero_based": cert["row_index_zero_based"],
            "usage": "Exact authenticated registration-class row and actual column meaning only; protection term, rights and ordinary object names are not innovation grounds.",
        })
        evidence.append(_evidence(text, start, end,
                                  "COMMON03_I_authenticated_actual_registration_class", dependency))
    return evidence


def inspect_extensions(record, result):
    """Return only new I evidence; do not mutate record/result or read labels.

    Invalid supplied source bindings raise rather than being silently coded zero.
    Unresolved objects/unsupported grammar yield no extension and remain root's
    material-review responsibility.
    """
    if not isinstance(record, dict) or not isinstance(record.get("unit_text"), str):
        raise TypeError("record must contain string unit_text")
    if not isinstance(result, dict):
        raise TypeError("result must be dict")
    if result.get("judgement_status") == "undetermined":
        return []
    evidence = _improvement_relations(record) + _registration_relations(record)
    unique = {(e["rule"], e["start"], e["end"]): e for e in evidence}
    return sorted(unique.values(), key=lambda e: (e["start"], e["end"], e["rule"]))
