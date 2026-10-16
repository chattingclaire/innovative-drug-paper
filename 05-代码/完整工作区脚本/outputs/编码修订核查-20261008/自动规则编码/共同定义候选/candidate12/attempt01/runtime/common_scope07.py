"""Bounded scope checks for necessary E frames and quoted format operations.

These checks do not negate drug-effect or substantive-improvement statements.
Quoted wording is excluded only when an explicit text role and a local format
operation make it the operation's literal object. Original offsets are kept.
"""
from __future__ import annotations

import re


_QUOTED = re.compile(r'“[^“”\n]+”|‘[^‘’\n]+’|"[^"\n]+"|\'[^\'\n]+\'')
_TEXT_ROLE = r"(?:这(?:一|段|句|个)?|该|此)?(?:短语|词语|文字|句话|字样|字符串)"
_OPERATION = r"(?:复制|粘贴|移动|插入|排印|排版|加粗|加下划线|删除)"
_AFTER = re.compile(rf"\s*(?P<role>{_TEXT_ROLE})\s*(?:予以|进行)?(?P<operation>{_OPERATION})")
_ROLE_AFTER = re.compile(rf"\s*(?P<role>{_TEXT_ROLE})")
_BEFORE = re.compile(rf"(?P<operation>{_OPERATION})\s*$")
_MODIFIER = r"(?:实际|直接|真正|正在|继续|明确)?"
_DENIED_FRAME = re.compile(
    rf"(?:并非|并不|不是|不再|未曾|尚未|未|没有|无需|不应|不宜|不){_MODIFIER}$"
)
_UNESTABLISHED_FRAME = re.compile(rf"(?:是否|能否){_MODIFIER}$")
_DOUBLE_NEGATIVE_FRAME = re.compile(rf"(?:并非|不是)不{_MODIFIER}$")


def _anchor(text, role, start, end):
    return {"role": role, "start": start, "end": end, "text": text[start:end]}


def quoted_format_operations(text):
    """Return local literal-text operations, without testing destination words.

    The wording role is required: an ordinary quotation or an instruction to
    evaluate a quoted claim is not a format operation. No full-sentence mask.
    """
    found = []
    for quote in _QUOTED.finditer(text):
        tail = text[quote.end():]
        right = _AFTER.match(tail)
        if right:
            role_a, role_b = (quote.end() + n for n in right.span("role"))
            op_a, op_b = (quote.end() + n for n in right.span("operation"))
        else:
            role = _ROLE_AFTER.match(tail)
            before = _BEFORE.search(text[:quote.start()])
            if not (role and before):
                continue
            role_a, role_b = (quote.end() + n for n in role.span("role"))
            op_a, op_b = before.span("operation")
        found.append({
            "kind": "quoted_wording_is_format_operation_object",
            "payload_start": quote.start() + 1, "payload_end": quote.end() - 1,
            "anchors": [
                _anchor(text, "literal_quoted_wording", quote.start() + 1, quote.end() - 1),
                _anchor(text, "explicit_wording_role", role_a, role_b),
                _anchor(text, "local_format_operation", op_a, op_b),
            ],
        })
    return found


def _overlaps(start, end, operation):
    return start < operation["payload_end"] and operation["payload_start"] < end


def is_format_payload(text, start, end):
    return any(_overlaps(start, end, op) for op in quoted_format_operations(text))


def select_active_frame(text, pattern):
    """Select an asserted treatment/research frame, not a denied activity.

    This is used only to supply the missing drug object of a generic treatment
    option statement. It is never a polarity filter on an effect statement.
    """
    operations = quoted_format_operations(text)
    for match in pattern.finditer(text):
        if any(_overlaps(*match.span(), operation) for operation in operations):
            continue
        prefix = text[:match.start()].rstrip()
        if _DOUBLE_NEGATIVE_FRAME.search(prefix):
            return match
        if _DENIED_FRAME.search(prefix) or _UNESTABLISHED_FRAME.search(prefix):
            continue
        return match
    return None


def revise(record, result):
    """Filter active E/I evidence only, across both inherited and new paths."""
    if result.get("judgement_status") == "undetermined":
        return result
    operations = quoted_format_operations(record["unit_text"])
    result["quoted_format_operations07"] = operations
    retained = []
    for evidence in result.get("evidence", []):
        implicated = []
        if evidence["dimension"] in ("E", "I"):
            # New paths record role-specific anchors; inherited rules still
            # expose their original current-evidence interval. Both are kept
            # auditable rather than silently reassigning a quoted proposition.
            spans = [(evidence["start"], evidence["end"])]
            spans.extend((a["start"], a["end"]) for a in evidence.get("current_relation_anchors", []))
            implicated = [op for op in operations if any(_overlaps(a, b, op) for a, b in spans)]
        if not implicated:
            retained.append(evidence)
            continue
        result.setdefault("suppressions", []).append({
            "rule": "COMMON07_quoted_wording_format_use",
            "dimensions": [evidence["dimension"]],
            "start": evidence["start"], "end": evidence["end"], "text": evidence["text"],
            "suppressed_rule": evidence["rule"], "format_operations": implicated,
            "reason": "当前引用文字是明确格式操作的对象；仅撤销依赖该文字的E/I证据，保留外部独立实质命题。",
        })
    result["evidence"] = retained
    # Final counts describe retained evidence, not the pre-filter candidates.
    if "final_manual_delta06" in result:
        result["final_manual_delta06"]["E_no_effective_option_evidence_n"] = sum(
            e.get("effect_statement_kind") == "no_effective_drug_option" for e in retained)
        result["final_manual_delta06"]["I_baseline_improvement_evidence_n"] = sum(
            e.get("rule") == "COMMON06_I_baseline_attribute_improvement_relation" for e in retained)
    result["implementation_scope_note"] = (
        "candidate07保留06新定稿手册的有界关系实现；仅补必要E活动对象的否定／未确立范围，"
        "及明确格式操作中引用文字的局部E/I证据用途。复杂范围和自然语言未穷尽，未作真实效度验证。")
    return result
