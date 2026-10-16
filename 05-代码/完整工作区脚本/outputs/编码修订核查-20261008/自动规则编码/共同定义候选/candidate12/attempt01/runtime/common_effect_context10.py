"""Object-only relation for an explicit example of a drug-effect study method.

This matcher does not assign labels, read sources, or authenticate metadata.
Its caller must first reproduce the exact immediate same-paragraph context.
"""
from __future__ import annotations

import re

from common_scope09 import select_active_frame

_METHOD_EFFECT_FRAME = re.compile(
    r"(?P<method>(?:单臂|单组|开放性|随机对照)?临床(?:试验|研究))"
    r"(?P<purpose>(?:也)?(?:是|用于|可用于|可以用于|旨在))"
    r"(?P<action>验证|评价|评估|检验)"
    r"(?P<drug>(?:研究|试验)?(?:药物|药品))(?:的)?"
    r"(?P<effect>有效性|疗效|治疗效果)"
)
_EXAMPLE = re.compile(r"\s*(?P<bridge>例如|比如|譬如)(?:[，,：:]|\s)")
_TRIAL = re.compile(r"(?:临床|随机对照)(?:试验|研究)")
_BRANCH_OTHER = re.compile(
    r"非药物(?:治疗|干预)|非药品(?:治疗|干预)|外科手术|放射治疗|"
    r"物理治疗|心理治疗|康复训练|设备|器械|软件|信息系统"
)
_BRANCH_DISENGAGED = re.compile(r"另行规定|另行处理|转入|转向|改为|仅供存档|仅存档|不涉及")
_BOUNDARIES = "。！？!?；;\n"


def _anchor(text, role, start, end):
    return {"role": role, "start": start, "end": end, "text": text[start:end]}


def method_example_relation(text, previous, option_span):
    """Return exact relation spans; no inheritance of prior evaluation content.

    The explicit example bridge is a boundary of this implementation, not a
    universal requirement of the manual for all possible context relations.
    """
    if not (isinstance(option_span, tuple) and len(option_span) == 2
            and all(type(n) is int for n in option_span)
            and 0 <= option_span[0] < option_span[1] <= len(text)):
        return None
    example = _EXAMPLE.match(text)
    if example is None:
        return None
    start, end = option_span
    left = max(text.rfind(c, 0, start) for c in _BOUNDARIES) + 1
    right = min((p for c in _BOUNDARIES if (p := text.find(c, end)) >= 0), default=len(text))
    branch = text[left:right]
    if _BRANCH_OTHER.search(branch) or _BRANCH_DISENGAGED.search(branch):
        return None
    trial = _TRIAL.search(branch)
    if trial is None:
        return None
    method = select_active_frame(previous, _METHOD_EFFECT_FRAME)
    if method is None:
        return None
    return {
        "antecedent_start": method.start(), "antecedent_end": method.end(),
        "antecedent_anchors": [_anchor(previous, role, *method.span(group)) for role, group in (
            ("preceding_clinical_method", "method"),
            ("preceding_actual_method_purpose", "purpose"),
            ("preceding_drug_effect_validation_action", "action"),
            ("preceding_actual_study_drug_object", "drug"),
            ("preceding_effect_endpoint_identifying_drug_scope", "effect"),
        )],
        "current_relation_anchors": [
            _anchor(text, "current_explicit_method_example", *example.span("bridge")),
            _anchor(text, "current_example_trial_reference", left + trial.start(), left + trial.end()),
        ],
    }
