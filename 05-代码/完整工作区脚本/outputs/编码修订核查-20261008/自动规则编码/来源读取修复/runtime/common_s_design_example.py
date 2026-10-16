"""Authenticated same-paragraph design-duty to medication-risk examples.

This is a bounded S relation, not a general human-factors or innovation rule.
The current unit must itself impose a substantive design duty.  The exact
source paragraph must then immediately continue with an explicit ``例如/如``
elaboration that names medication/use error or injection injury prevention.
"""
from __future__ import annotations

import copy
import hashlib
import re

from source_context_adapter_v34 import authenticate_context, authenticate_target, candidate


VERSION = "common-s-authenticated-design-example-01"

_DESIGN_DUTY = re.compile(
    r"(?=[^。！？!?\n]{0,180}(?:设计|开发))"
    r"(?=[^。！？!?\n]{0,180}(?:应当|应|须|需要|建议))"
    r"(?=[^。！？!?\n]{0,180}(?:考虑|评估|评价|分析|结合))"
    r"[^。！？!?\n]+"
)
_EXAMPLE = re.compile(
    r"^\s*(?P<bridge>例如|如)[,，:：]?\s*(?P<body>.*?)"
    r"(?=(?:此外|另一方面|至于|另行|鼓励|基于)[,，:：]|$)",
    re.S,
)
_RISK_CONTROL = re.compile(
    r"(?:减少|降低|防止|预防|避免)[^。！？!?；;\n]{0,24}"
    r"(?:用药错误|用药差错|给药错误|给药差错|误用|误服|误吸|误选|误刺)"
    r"(?:风险)?|"
    r"(?:减少|降低)(?:记忆|操作|给药)[^。！？!?；;\n]{0,16}负担"
    r"[^。！？!?；;\n]{0,30}(?:减少|降低)(?:用药|给药)(?:错误|差错)(?:风险)?"
)
_MEDICINE_USE_OBJECT = re.compile(
    r"药品|药物|用药|给药|制剂|药液|注射|注射器|针头|自我注射|服药"
)
_TOPIC_SHIFT = re.compile(r"^\s*(?:另一|另一个|其他项目|不同项目|与此无关|关于其他|至于其他)")


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _bound_current_paragraphs(record):
    supplied = record.get("paragraph_context", [])
    if not supplied:
        return []
    shared = record.get("llm_v29_shared_context", {})
    if "paragraph_context" in shared and shared["paragraph_context"] != supplied:
        raise ValueError("S design example: paragraph differs across shared materials")

    authenticate_target(record)
    document = candidate(record["candidate_file"])
    units = [u for u in document.get("unit_candidates", [])
             if u.get("id") == record.get("unit_id")]
    if len(units) != 1:
        raise ValueError("S design example: target candidate is not unique")
    target = units[0]
    paragraphs = document.get("paragraphs", [])
    bound = []
    for context in supplied:
        body = context.get("text", "") if isinstance(context, dict) else ""
        if record["unit_text"] not in body:
            continue
        if body.count(record["unit_text"]) != 1:
            raise ValueError("S design example: current unit is ambiguous in paragraph")
        if target.get("paragraph_id") != context.get("paragraph_id"):
            continue
        actual = [p for p in paragraphs if p.get("id") == context.get("paragraph_id")]
        if (len(actual) != 1 or actual[0].get("text") != body
                or actual[0].get("pages", []) != context.get("pages", [])):
            raise ValueError("S design example: paragraph text/pages do not bind candidate")
        cert = copy.deepcopy(context)
        cert.update({
            "source_path": record.get("unit_source") or record.get("source"),
            "source_sha256": record.get("unit_source_sha256") or record.get("source_sha256"),
            "candidate_path": record["candidate_file"],
            "candidate_sha256": record["candidate_sha256"],
        })
        if not cert.get("source_lines"):
            cert["source_lines"] = actual[0].get("line_ids") or actual[0].get("source_lines") or []
        bound.append(cert)
    return bound


def inspect_safety_design_example(record):
    """Return current-unit S relations with authenticated double anchors."""
    text = record.get("unit_text", "")
    duty = _DESIGN_DUTY.search(text)
    if not duty:
        return []

    found = []
    for paragraph in _bound_current_paragraphs(record):
        body = paragraph["text"]
        current_start = body.index(text)
        current_end = current_start + len(text)
        following = body[current_end:]
        example = _EXAMPLE.match(following)
        if not example or _TOPIC_SHIFT.search(example.group("body")):
            continue
        example_body = example.group("body")
        risk = _RISK_CONTROL.search(example_body)
        if not risk:
            continue
        risk_start = current_end + example.start("body") + risk.start()
        risk_end = current_end + example.start("body") + risk.end()
        bridge_start = current_end + example.start("bridge")
        bridge_end = current_end + example.end("bridge")
        local_relation = body[max(0, current_start - 180):risk_end]
        if not _MEDICINE_USE_OBJECT.search(local_relation):
            continue
        # Authenticate the exact source excerpt that carries both anchors.
        # A whole candidate paragraph can cross a PDF page number/header and
        # fail literal reproduction even though this bounded relation is
        # physically present. Candidate paragraph identity was checked above;
        # this second check binds the actual source bytes and relation text.
        source_excerpt = body[current_start:risk_end]
        source_cert = authenticate_context({**paragraph, "text": source_excerpt})
        auth = source_cert.get("authentication_v34") or {}
        if not (auth.get("literal_reproduced_in_current_runtime") is True or
                auth.get("layout_reconstructed_literal_reproduced") is True):
            raise ValueError("S design example: actual source literal/layout authentication required")
        dependency = {
            "kind": "authenticated_same_paragraph_design_duty_explicit_risk_example",
            "rule_release": VERSION,
            "paragraph_id": paragraph["paragraph_id"],
            "paragraph_text_sha256": _sha(body),
            "current_unit_sha256": _sha(text),
            "source_path": paragraph["source_path"],
            "source_sha256": paragraph["source_sha256"],
            "candidate_path": paragraph["candidate_path"],
            "candidate_sha256": paragraph["candidate_sha256"],
            "pages": paragraph.get("pages", []),
            "source_lines": paragraph.get("source_lines", []),
            "authentication": auth,
            "authenticated_source_excerpt": {
                "text": source_excerpt,
                "sha256": _sha(source_excerpt),
                "start_in_paragraph": current_start,
                "end_in_paragraph": risk_end,
            },
            "current_design_duty_anchor": {
                "start_in_paragraph": current_start,
                "end_in_paragraph": current_end,
                "text": text,
            },
            "explicit_example_bridge_anchor": {
                "start_in_paragraph": bridge_start,
                "end_in_paragraph": bridge_end,
                "text": body[bridge_start:bridge_end],
            },
            "explicit_medication_risk_control_anchor": {
                "start_in_paragraph": risk_start,
                "end_in_paragraph": risk_end,
                "text": body[risk_start:risk_end],
            },
            "usage": ("The authenticated example explains the current design duty as medication/use-risk "
                      "prevention; no other paragraph dimension is inherited."),
        }
        found.append({
            "start": 0,
            "end": len(text),
            "quote": text,
            "kind": "authenticated_design_duty_risk_prevention_example",
            "subtype": "use_harm_prevention",
            "basis": ("当前实质设计义务由同段紧随的明确例示连接到用药错误、误刺等风险预防；"
                      "一般人因、便利或疼痛内容本身不构成S。"),
            "context_dependency": dependency,
        })
        break
    return found
