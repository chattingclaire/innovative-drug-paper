"""Conservative current-unit metadata for evidence expressions.

Regex spans remain locators used by downstream suppression logic.  This
module never changes labels, evidence membership, or locator ``start/end``.
External quotation always preserves the complete current unit so it cannot
drop cross-clause/sentence negation, conditions, exceptions, or requirements.

Revision note: an earlier draft treated several lexical patterns as resolved
polarity. Counterexamples with conditional negatives, mixed propositions and
cross-sentence scope showed that pattern detection is only a review signal.
This module therefore records signals but never claims polarity resolution.
"""
from __future__ import annotations

import hashlib
import re


VERSION = "proposition-negation-02-presence-only"

_MAJOR_BOUNDARY = "。！？!?\n"
_NEGATION_SIGNAL = re.compile(
    r"不再|不予|并未|并不|并非|不是|不得|不应|不宜|不能|无法|未能|尚未|"
    r"没有|不存在|尚无|仍无|并无|未|无|不"
)
_CONDITION = re.compile(
    r"如果|若(?:是)?|如(?=有|需|未|不|符合|达到|发生|出现)|只要|只有|除非|"
    r"当.{0,24}时|在.{0,24}(?:条件|情况下)|"
    r"符合.{0,30}(?:可以|可|方可|才能|才)|(?:可以|可|方可|才能|才).{0,30}条件"
)
_EXCEPTION = re.compile(r"除外|例外|但.{0,24}除外|不适用|除非|除[^，,。；;]{1,30}(?:外|之外|以外)")
_REQUIREMENT = re.compile(
    r"应当|必须|须|需要|要求|不得|不应|不宜|建议|"
    r"(?<!反)(?<!响)应(?=予|进行|提供|提交|评价|评估|考虑|说明|报告|制定|采取|符合|保证|确保|包括|包含|为|在|由|对|将|根据)"
)
_UNCERTAIN = re.compile(r"不确定|尚不明确|尚不能确定|不能确定|有待(?:证实|验证|明确)|仍需(?:证实|验证)")
_INSUFFICIENT_EVIDENCE = re.compile(
    r"(?:尚)?不能证明|无法证明|未能证明|尚未证实|未被证实|"
    r"证据(?:尚|仍)?(?:不足|不充分)|不足以(?:证明|说明|表明|支持)"
)
_NEGATED_INFERENCE = re.compile(
    r"(?:并不|并非|不|未必)(?:能|足以)?(?:代表|意味着|等于|说明|表明|支持|提示)"
    r"|(?:不能|无法|不足以)(?:据此)?(?:认为|推断|认定)"
)
_CONTRAST_OR_MULTIPLE = re.compile(r"但|然而|另一方面|与此同时|同时|而(?=该|本|另一|其|后者)|[；;]|[。！？!?]\s*[^\s]")


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _bounded_proposition(text, start, end):
    """Return a sentence-level proposition; semicolons remain in scope.

    Commas and semicolons often separate a Chinese condition/qualification
    from its consequence.  Splitting on them is exactly how outer negation was
    lost, so only major sentence boundaries are used here.
    """
    left = max((text.rfind(c, 0, start) for c in _MAJOR_BOUNDARY), default=-1) + 1
    candidates = [text.find(c, end) for c in _MAJOR_BOUNDARY]
    candidates = [p for p in candidates if p >= 0]
    right = min(candidates) + 1 if candidates else len(text)
    while left < right and text[left].isspace():
        left += 1
    while right > left and text[right - 1].isspace():
        right -= 1
    return left, right


def analyze_statement_scope(value):
    """Record lexical review signals; do not infer the proposition's truth."""
    signal_matches = {
        "negation": [m.group() for m in _NEGATION_SIGNAL.finditer(value)],
        "evidence_insufficiency": [m.group() for m in _INSUFFICIENT_EVIDENCE.finditer(value)],
        "negated_inference": [m.group() for m in _NEGATED_INFERENCE.finditer(value)],
        "uncertainty": [m.group() for m in _UNCERTAIN.finditer(value)],
        "condition": [m.group() for m in _CONDITION.finditer(value)],
        "exception": [m.group() for m in _EXCEPTION.finditer(value)],
        "requirement": [m.group() for m in _REQUIREMENT.finditer(value)],
        "contrast_or_multiple_propositions": [m.group() for m in _CONTRAST_OR_MULTIPLE.finditer(value)],
    }
    needs_review = any(signal_matches.values())
    return {
        "scope_status": "needs_scope_review" if needs_review else "presence_only_no_scope_signal",
        "polarity": "not_classified",
        "polarity_scope_reliable": False,
        "semantic_use": "dimension_presence_only_not_fact_direction",
        "heuristic_signals": signal_matches,
        "contains_negation_signal": bool(signal_matches["negation"]),
        "contains_condition_signal": bool(signal_matches["condition"]),
        "contains_exception_signal": bool(signal_matches["exception"]),
        "contains_requirement_signal": bool(signal_matches["requirement"]),
        "review_reason": ("启发式检测到可能改变命题范围或事实状态的表达；保留完整当前单元并人工核定作用域。"
                          if needs_review else
                          "未检测到有限信号也不等于已经证明肯定或否定方向；本层只记录维度议题在场。"),
    }


def proposition_expression(text, start, end):
    """Keep a bounded candidate but expose the whole unit as the quotation."""
    valid = (isinstance(text, str) and isinstance(start, int) and isinstance(end, int)
             and 0 <= start < end <= len(text))
    if not valid:
        value = text if isinstance(text, str) else ""
        return {
            "start": 0,
            "end": len(value),
            "text": value,
            "source": "full_current_unit_fallback_invalid_locator",
            "current_unit_sha256": _sha(value),
            "scope": analyze_statement_scope(value),
            "candidate_proposition": None,
        }

    left, right = _bounded_proposition(text, start, end)
    return {
        "start": 0,
        "end": len(text),
        "text": text,
        "source": "full_current_unit_for_external_quote",
        "current_unit_sha256": _sha(text),
        "scope": analyze_statement_scope(text),
        "candidate_proposition": {
            "start": left, "end": right, "text": text[left:right],
            "use": "review_locator_only_not_resolved_scope",
        },
    }


def normalize_evidence_expressions(record, result, dimensions=None):
    """Attach expression metadata only; never add/drop evidence or labels.

    ``dimensions`` may bound an early-stage caller.  The final pipeline should
    call this once without ``dimensions`` after every dimension has emitted its
    evidence and before serialization/rebuild.  External reports must render
    ``display_quote``/``current_statement``.  Legacy ``text`` and ``start/end``
    are internal locators retained only for matching and suppression.
    """
    text = record.get("unit_text")
    if not isinstance(text, str) or result.get("judgement_status") == "undetermined":
        return result
    allowed = set(dimensions) if dimensions is not None else None
    for evidence in result.get("evidence", []):
        if allowed is not None and evidence.get("dimension") not in allowed:
            continue
        start, end = evidence.get("start"), evidence.get("end")
        expression = proposition_expression(text, start, end)
        evidence["locator"] = {"start": start, "end": end, "text": evidence.get("text")}
        evidence["locator_use"] = "internal_match_and_suppression_only_not_external_quote"
        evidence["evidence_expression"] = expression
        evidence["current_statement"] = {
            "start": expression["start"],
            "end": expression["end"],
            "text": expression["text"],
            "source": expression["source"],
        }
        evidence["display_quote"] = expression["text"]
        evidence["external_quote_field"] = "display_quote"
        evidence["evidence_expression_version"] = VERSION
    return result


def effect_nature_from_expression(expression):
    """Return a presence-only status; patterns never resolve fact direction."""
    scope = expression["scope"]
    return ("scope_review_required" if scope["scope_status"] == "needs_scope_review"
            else "dimension_presence_only_direction_not_classified")
