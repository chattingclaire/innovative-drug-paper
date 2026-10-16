"""Candidate 03: two bounded fairness corrections over preserved candidate 02.

The prediction contract remains current_text + supplied contexts only.  This
module was created after candidate-02 evaluation, so its output is a continued
development result and is not described as independent validation.
"""

from __future__ import annotations

import relation_coder_v02 as base


VERSION = "dc26-relation-candidate-03"
MANUAL_SHA256 = base.MANUAL_SHA256
DIMENSIONS = base.DIMENSIONS
digest = base.digest


def _fairness(builder: base.Builder) -> None:
    # Retain candidate-02 gap/opportunity, affordability, and general-demand
    # boundaries, but remove its over-broad insurance shortcut.
    base._fairness(builder)
    builder.evidence = [
        item for item in builder.evidence
        if item["rule"] != "F_explicit_insurance_coverage_and_payment_opportunity"
    ]

    text, contexts = builder.text, builder.contexts
    insurance = base._search(
        r"商业健康保险保障范围[^。；;]{0,60}(?:支付|药品应用病例)|经审核评议程序后支付",
        text,
    )
    patient_relation = base._search(
        r"患者(?:能否)?负担|患者可负担性|因(?:收入|支付能力)[^。；;]{0,30}(?:无法|难以)(?:获得|持续接受)"
        r"|患者[^。；;]{0,20}(?:获得|持续接受)[^。；;]{0,20}(?:所需药品|药品治疗)"
        r"|按(?:治疗)?需要[^。；;]{0,24}(?:保障|支付|补偿)",
        text,
    )
    context_relation = base._context_anchors(
        r"患者(?:能否)?负担|患者可负担性|因(?:收入|支付能力)[^。；;]{0,30}(?:无法|难以)(?:获得|持续接受)"
        r"|患者[^。；;]{0,20}(?:获得|持续接受)[^。；;]{0,20}(?:所需药品|药品治疗)"
        r"|按(?:治疗)?需要[^。；;]{0,24}(?:保障|支付|补偿)",
        contexts,
        "patient_need_affordability_or_access_relation",
    )
    if insurance and (patient_relation or context_relation):
        anchors = [(insurance, "insurance_coverage_or_payment_arrangement")]
        if patient_relation:
            anchors.append((patient_relation, "patient_need_affordability_or_access_relation"))
        builder.add(
            "F",
            "F_insurance_arrangement_with_explicit_patient_equity_relation",
            "商保支付安排另有患者需要、支付能力、获取/持续治疗障碍的直接联系；普通支付管理本身不足。",
            anchors,
            context_relation,
        )
    elif insurance:
        builder.exclude(
            "F_insurance_payment_without_patient_equity_relation",
            "普通商保保障范围或支付管理没有明确患者需要、支付能力、获取机会差异或保障缺口联系。",
            insurance,
        )

    # A programme-formulation sentence may itself enact a bounded measure when
    # it names the actual shortage/no-option object and the specific priority
    # procedure.  General access/innovation purpose plus programme naming does
    # not satisfy this three-part relation.
    gap = base._search(
        r"临床急需短缺药品|市场短缺(?:的)?药品|短缺药品|境内无获批对应治疗选项|尚无有效防治手段",
        text,
    )
    priority = base._search(r"优先审评审批", text)
    enactment = base._search(r"(?:规范|制定|建立|发布|印发)[^。；;]{0,80}(?:工作程序|程序|办法|规定)", text)
    if gap and priority and enactment:
        builder.add(
            "F",
            "F_explicit_gap_priority_programme_enactment",
            "当前同时明确实际供应/治疗选项缺口对象、具体优先程序和制度制定动作，属于直接对应公平议题的制度安排。",
            [(gap, "explicit_guarantee_gap_object"),
             (priority, "specific_targeted_priority_measure"),
             (enactment, "current_programme_enactment")],
        )
    else:
        generic_programme = base._search(
            r"(?:促进|支持|鼓励)[^。；;]{0,50}(?:可及|创新药|新药)[^。；;]{0,80}(?:制定|发布|印发)[^。；;]{0,30}(?:程序|办法|规定)",
            text,
        )
        if generic_programme:
            builder.exclude(
                "F_generic_access_or_innovation_purpose_not_equity_arrangement",
                "泛称可及或创新目的并制定程序，没有明确缺口对象与针对性措施关系。",
                generic_programme,
            )


def code_unit(unit: dict) -> dict:
    text = unit["current_text"]
    contexts = unit.get("contexts") or []
    if not isinstance(text, str) or not isinstance(contexts, list) or not all(isinstance(x, str) for x in contexts):
        raise TypeError("unit must provide string current_text and list[str] contexts")
    builder = base.Builder(text, contexts)
    base._common_evaluation_and_information(builder)
    base._safety(builder)
    base._effectiveness(builder)
    base._economics(builder)
    base._innovation(builder)
    _fairness(builder)
    labels = {dimension: int(any(e["dimension"] == dimension for e in builder.evidence)) for dimension in DIMENSIONS}
    for item in builder.evidence:
        assert item["current_statement"]["text"] == text
        for anchor in item["current_relation_anchors"]:
            assert text[anchor["start"]:anchor["end"]] == anchor["text"]
        for anchor in item["consumed_context_anchors"]:
            value = contexts[anchor["context_index"]]
            assert value[anchor["start"]:anchor["end"]] == anchor["text"]
    return {
        "version": VERSION,
        "manual_sha256": MANUAL_SHA256,
        "unit_text_sha256": digest(text),
        "context_sha256": [digest(x) for x in contexts],
        "labels": labels,
        "evidence": builder.evidence,
        "exclusions": builder.exclusions,
        "judgement_status": "completed",
        "input_policy": "current_text_and_supplied_contexts_only",
        "development_history": "candidate03_after_candidate02_frozen_evaluation",
    }
