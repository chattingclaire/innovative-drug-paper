"""Literal source evidence and per-dimension output validation.

Normalization is only a matching view. Original text, negation and conditions
remain in the complete current proposition and in literal source anchors.
These helpers neither infer dimension values nor read reference judgments.
"""
from __future__ import annotations

import copy
import json
import re
import unicodedata

DIMENSIONS = ("S", "E", "Ec", "I", "F")
_CJK_WHITESPACE = re.compile(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])")
_DECISION_KEYS = {
    "value", "basis_path", "current_anchor", "current_proposition", "context_evidence",
    "reason", "needed_material", "rule_conflict", "details",
}


def matching_view(raw):
    """Per-character NFKC plus CJK inter-character whitespace removal.

    Offset pairs always refer to the exact original Unicode string. This is
    the old offset algorithm reimplemented with standard-library dependencies;
    no legacy module is imported and no absent character is reconstructed.
    """
    if not isinstance(raw, str):
        raise ValueError("matching_view requires original text")
    chars, offsets = [], []
    for index, char in enumerate(raw):
        for normalized in unicodedata.normalize("NFKC", char):
            chars.append(normalized)
            offsets.append((index, index + 1))
    joined = "".join(chars)
    removed = {i for match in _CJK_WHITESPACE.finditer(joined)
               for i in range(match.start(), match.end())}
    return ("".join(char for i, char in enumerate(chars) if i not in removed),
            [pair for i, pair in enumerate(offsets) if i not in removed])


def raw_span(offsets, a, b):
    """Map a nonempty normalized half-open span to the original range."""
    if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(offsets)):
        raise ValueError("normalized span must be nonempty and in range")
    for index in (a, b - 1):
        pair = offsets[index]
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or any(type(n) is not int for n in pair) or not 0 <= pair[0] < pair[1]):
            raise ValueError("invalid original offset pair")
    start, end = offsets[a][0], offsets[b - 1][1]
    if start >= end:
        raise ValueError("original range is not ordered")
    return start, end


def anchor(raw, a, b):
    """Build a literal original-text anchor using original offsets."""
    if not isinstance(raw, str):
        raise ValueError("anchor requires original text")
    if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(raw):
        raise ValueError("original anchor must be nonempty and in range")
    return {"start": a, "end": b, "text": raw[a:b]}


def _context(unit, cid):
    matches = [c for c in unit.get("contexts", []) if c.get("context_id") == cid]
    if len(matches) != 1:
        raise ValueError("context evidence must locate one supplied source context")
    return matches[0]


def context_anchor(unit, cid, a, b, usage):
    """Cite exact supplied context text and its unchanged source binding."""
    if not isinstance(usage, str) or not usage.strip():
        raise ValueError("context evidence requires a concrete usage")
    context = _context(unit, cid)
    if not isinstance(context.get("text"), str):
        raise ValueError("textless structure cannot be cited as literal context text")
    if not isinstance(context.get("source_ref"), dict):
        raise ValueError("context source_ref is missing")
    return {**anchor(context["text"], a, b), "context_id": cid, "usage": usage,
            "source_ref": copy.deepcopy(context["source_ref"])}


def make_decision(value, basis_path, current_anchor, current_proposition,
                  context_evidence, reason, needed_material=None,
                  rule_conflict=None, details=None):
    """Construct an output object; validate_decisions checks it against source."""
    if value is not None and (type(value) is not int or value not in (0, 1)):
        raise ValueError("decision value must be 0, 1 or null; bool is not a label")
    return {
        "value": value,
        "basis_path": copy.deepcopy(basis_path),
        "current_anchor": copy.deepcopy(current_anchor),
        "current_proposition": copy.deepcopy(current_proposition),
        "context_evidence": copy.deepcopy(context_evidence),
        "reason": reason,
        "needed_material": copy.deepcopy([] if needed_material is None else needed_material),
        "rule_conflict": copy.deepcopy(rule_conflict),
        "details": copy.deepcopy(details),
    }


def _literal_anchor(raw, value, path, *, context=False):
    allowed = {"start", "end", "text"}
    if context:
        allowed |= {"context_id", "usage", "source_ref"}
    if not isinstance(value, dict) or set(value) != allowed:
        raise ValueError(f"{path}: anchor fields differ from the literal interface")
    expected = anchor(raw, value["start"], value["end"])
    if value["text"] != expected["text"]:
        raise ValueError(f"{path}: quote is not the exact original substring")


def _concrete_needed(value, path):
    if not isinstance(value, list):
        raise ValueError(f"{path}: needed_material must be an array")
    generic = {"unknown", "missing", "context", "pending", "未知", "缺材", "待核", "语境"}
    for index, item in enumerate(value):
        if isinstance(item, str):
            if not item.strip() or item.strip().lower() in generic:
                raise ValueError(f"{path}/{index}: name the missing content or relation")
        elif isinstance(item, dict):
            if not item or not any(isinstance(v, str) and v.strip()
                                   and v.strip().lower() not in generic for v in item.values()):
                raise ValueError(f"{path}/{index}: missing material needs a concrete description")
        else:
            raise ValueError(f"{path}/{index}: expected a description or source request object")


def validate_decisions(unit, decisions):
    """Validate five 0/1/null decisions and their source evidence; return None.

    Completeness is preserved mechanically by requiring a positive decision's
    current_proposition to retain the whole fixed record. Narrow current
    relation anchors and finite context quotations remain separate. Semantic
    correctness is a different check performed after output is sealed.
    """
    if not isinstance(unit, dict) or not isinstance(unit.get("text"), str) or not unit["text"]:
        raise ValueError("unit requires original current text")
    if not isinstance(decisions, dict) or set(decisions) != set(DIMENSIONS):
        raise ValueError("decisions must contain exactly S/E/Ec/I/F")
    raw = unit["text"]
    for dimension in DIMENSIONS:
        decision = decisions[dimension]
        path = "decisions/" + dimension
        if not isinstance(decision, dict) or set(decision) != _DECISION_KEYS:
            raise ValueError(f"{path}: missing or unknown decision fields")
        value = decision["value"]
        if value is not None and (type(value) is not int or value not in (0, 1)):
            raise ValueError(f"{path}: value must be 0, 1 or null")
        if not isinstance(decision["reason"], str) or not decision["reason"].strip():
            raise ValueError(f"{path}: every decision requires a reason")
        basis = decision["basis_path"]
        if not (isinstance(basis, str) and basis.strip()
                or isinstance(basis, list) and basis
                and all(isinstance(x, str) and x.strip() for x in basis)):
            raise ValueError(f"{path}: identify the manual basis path")
        current = decision["current_anchor"]
        if current is not None:
            _literal_anchor(raw, current, path + "/current_anchor")
        proposition = decision["current_proposition"]
        if isinstance(proposition, dict):
            _literal_anchor(raw, proposition, path + "/current_proposition")
            complete = proposition == anchor(raw, 0, len(raw))
        elif isinstance(proposition, str):
            if proposition not in raw or not proposition:
                raise ValueError(f"{path}: proposition must be literal supplied current text")
            complete = proposition == raw
        elif proposition is None:
            complete = False
        else:
            raise ValueError(f"{path}: proposition must be original text or an anchor")
        if value == 1 and (current is None or not complete):
            raise ValueError(f"{path}: 1 requires a current anchor and the complete fixed proposition")
        citations = decision["context_evidence"]
        if not isinstance(citations, list):
            raise ValueError(f"{path}: context_evidence must be an array")
        for index, citation in enumerate(citations):
            at = f"{path}/context_evidence/{index}"
            if not isinstance(citation, dict) or not isinstance(citation.get("context_id"), str):
                raise ValueError(f"{at}: context_id is missing")
            context = _context(unit, citation["context_id"])
            if not isinstance(context.get("text"), str):
                raise ValueError(f"{at}: a textless context is not literal evidence")
            _literal_anchor(context["text"], citation, at, context=True)
            if citation["source_ref"] != context.get("source_ref"):
                raise ValueError(f"{at}: citation source binding differs from supplied source")
            if not isinstance(citation["usage"], str) or not citation["usage"].strip():
                raise ValueError(f"{at}: explain the relation completed by this context")
        needed = decision["needed_material"]
        _concrete_needed(needed, path + "/needed_material")
        if value is None and not needed:
            raise ValueError(f"{path}: null requires a specific material or unresolved relation request")
        if value is not None and needed:
            raise ValueError(f"{path}: a decided value cannot retain an unresolved material dependency")
        if decision["rule_conflict"] is not None:
            conflict = decision["rule_conflict"]
            if not isinstance(conflict, (str, dict)) or not conflict:
                raise ValueError(f"{path}: rule_conflict must describe the concrete boundary dispute")
    try:
        json.dumps(decisions, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("decisions contain non-JSON output values") from error
