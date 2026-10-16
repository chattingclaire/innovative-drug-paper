"""Candidate 04: bounded fairness relations over preserved candidate 03.

This candidate was developed after reviewing the candidate-03 evaluation and
two independent semantic audits.  It remains a same-material development
candidate, not an independent validation.  The prediction contract is still
current_text plus the supplied contexts only.
"""

from __future__ import annotations

import relation_coder_v02 as primitives
import relation_coder_v03 as base


VERSION = "dc26-relation-candidate-04"
MANUAL_SHA256 = base.MANUAL_SHA256
DIMENSIONS = base.DIMENSIONS
digest = base.digest


def _need_priority_for_drug_coverage(builder: primitives.Builder) -> None:
    """Recognize a complete qualitative need-priority allocation relation."""
    text, contexts = builder.text, builder.contexts
    directory_object = primitives._search(
        r"(?:进入|纳入)[^。；;]{0,16}(?:药品)?目录[^。；;]{0,12}(?:的)?药品"
        r"|(?:药品|用药)[^。；;]{0,12}(?:目录|保障待遇)",
        text,
    )
    need_order = primitives._search(
        r"(?:更关注|优先|重点保障)[^。；;]{0,18}雪中送炭[^。；;]{0,18}"
        r"(?:控制|减少|审慎安排|限制)[^。；;]{0,18}锦上添花",
        text,
    )
    current_basic = primitives._search(r"保基本|基本保障(?:需要|原则)|基本治疗需要", text)
    current_clinical = primitives._search(r"聚焦临床需求|按(?:临床|治疗|用药)需要|临床需要优先", text)
    context_basic = primitives._context_anchors(
        r"保基本|基本保障(?:需要|原则)|基本治疗需要",
        contexts,
        "basic_coverage_principle",
    )
    context_clinical = primitives._context_anchors(
        r"聚焦临床需求|按(?:临床|治疗|用药)需要|临床需要优先",
        contexts,
        "clinical_need_priority_principle",
    )
    has_basic = bool(current_basic or context_basic)
    has_clinical_need = bool(current_clinical or context_clinical)
    if directory_object and need_order and has_basic and has_clinical_need:
        current_anchors = [
            (directory_object, "drug_coverage_resource_object"),
            (need_order, "qualitative_need_priority_order"),
        ]
        if current_basic:
            current_anchors.append((current_basic, "basic_coverage_principle"))
        if current_clinical:
            current_anchors.append((current_clinical, "clinical_need_priority_principle"))
        builder.add(
            "F",
            "F_drug_coverage_resource_allocated_by_basic_clinical_need",
            "药品保障或目录资源对象明确，并以保基本和临床需要为原则优先雪中送炭、控制锦上添花，属于按不同保障需要配置机会。该关系不推出贫困、基本药物身份，也不推出所有创新药不优先。",
            current_anchors,
            context_basic + context_clinical,
        )
    elif need_order:
        builder.exclude(
            "F_need_priority_metaphor_without_complete_coverage_relation",
            "雪中送炭/锦上添花的排序表述缺少药品保障资源对象、保基本或临床需要关系中的至少一项，不能单独推出按需保障。",
            need_order,
        )


def _targeted_supplementary_coverage_directory(builder: primitives.Builder) -> None:
    """Recognize a targeted directory opportunity that answers a stated gap."""
    text, contexts = builder.text, builder.contexts
    supplementary_directory = primitives._search(
        r"(?:商保|商业健康保险|补充保障|多层次保障)[^。；;]{0,18}(?:创新药|药品)?目录"
        r"[^。；;]{0,32}(?:主要聚焦|重点纳入|定向遴选|承接)",
        text,
    )
    basic_gap = primitives._search(
        r"(?:因)?(?:超出|不属于)[^。；;]{0,12}保基本[^。；;]{0,18}(?:暂时)?无法纳入基本目录"
        r"|基本医保(?:暂时)?不予支付|无法获得基本保障|未纳入基本保障范围",
        text,
    )
    current_need = primitives._search(
        r"患者获益(?:显著|明确)|按(?:临床|治疗|用药)需要|满足[^。；;]{0,16}用药需求",
        text,
    )
    context_need = primitives._context_anchors(
        r"满足[^。；;]{0,24}(?:用药需求|治疗需要)|按(?:临床|治疗|用药)需要",
        contexts,
        "patient_benefit_or_medication_need",
    )
    coverage_channel = primitives._context_anchors(
        r"(?:商保|商业健康保险|补充保障|多层次保障)[^。；;]{0,24}(?:创新药|药品)?目录"
        r"[^。；;]{0,80}(?:商业健康保险|多层次医疗保障体系)[^。；;]{0,32}(?:参考使用|保障)",
        contexts,
        "supplementary_coverage_channel",
    )
    if supplementary_directory and basic_gap and (current_need or context_need) and coverage_channel:
        current_anchors = [
            (supplementary_directory, "targeted_supplementary_directory_opportunity"),
            (basic_gap, "explicit_basic_coverage_gap_or_limit"),
        ]
        if current_need:
            current_anchors.append((current_need, "patient_benefit_or_medication_need"))
        builder.add(
            "F",
            "F_basic_coverage_gap_with_targeted_supplementary_directory_opportunity",
            "当前明确基本保障范围限制、按患者获益或用药需要界定的对象，并由补充保障目录定向承接；必要语境只确认该目录的保障渠道。目录遴选机会不等于已经支付。",
            current_anchors,
            context_need + coverage_channel,
        )
    elif supplementary_directory:
        builder.exclude(
            "F_supplementary_directory_without_complete_gap_need_channel_relation",
            "补充或商保目录只有名称、定位或普通遴选，未同时形成基本保障限制、患者获益/用药需要和补充保障渠道的定向关系。",
            supplementary_directory,
        )


def _needs_based_local_medicine_supply_configuration(builder: primitives.Builder) -> None:
    """Use supplied context only when it explicitly carries the current rule forward."""
    text, contexts = builder.text, builder.contexts
    current_criteria = primitives._search(
        r"根据[^。；;]{0,36}(?:疾病谱|诊疗能力|治疗需要)[^。；;]{0,48}(?:药品供应|药品供给)情况",
        text,
    )
    current_assessment = primitives._search(r"(?:基层)?(?:医疗卫生机构)?用药需求评估", text)
    current_rule = primitives._search(
        r"(?:制定|调整)[^。；;]{0,30}(?:县域)?用药(?:遴选|配置)(?:和调整)?规则",
        text,
    )
    context_rule_link = primitives._context_anchors(
        r"根据(?:该|上述)?(?:用药)?遴选和调整规则",
        contexts,
        "explicit_carry_forward_of_current_selection_rule",
    )
    context_different_needs = primitives._context_anchors(
        r"(?:上下转诊|不同层级|跨层级)[^。；;]{0,16}用药需求",
        contexts,
        "different_referral_or_care_level_medication_needs",
    )
    context_supply_allocation = primitives._context_anchors(
        r"(?:县[^。；;]{0,12}乡[^。；;]{0,12}村|县乡村|不同层级)[^。；;]{0,24}用药种类(?:衔接|配置|供应)",
        contexts,
        "medicine_supply_allocation_across_care_levels",
    )
    if (
        current_criteria
        and current_assessment
        and current_rule
        and context_rule_link
        and context_different_needs
        and context_supply_allocation
    ):
        builder.add(
            "F",
            "F_needs_assessment_rule_carried_into_cross_level_medicine_supply_allocation",
            "当前按疾病、诊疗和供应情况评估用药需要并制定配置规则；同段语境明确根据该规则，按不同转诊/层级需要衔接药品供给。纳入依据是完整承接链，不是基层身份或一般需求评估。",
            [
                (current_criteria, "current_need_and_supply_criteria"),
                (current_assessment, "current_medication_needs_assessment"),
                (current_rule, "current_medicine_selection_or_configuration_rule"),
            ],
            context_rule_link + context_different_needs + context_supply_allocation,
        )
        builder.exclusions = [
            item for item in builder.exclusions
            if item["rule"] != "F_general_needs_assessment_without_equity_relation"
        ]
    elif current_assessment:
        builder.exclude(
            "F_needs_assessment_without_explicit_rule_to_supply_allocation_chain",
            "基层身份或一般用药需求评估没有同时形成当前需求/供应判据、配置规则，以及语境中明确承接该规则的不同需要和药品供给衔接。",
            current_assessment,
        )


def _fairness(builder: primitives.Builder) -> None:
    base._fairness(builder)
    _need_priority_for_drug_coverage(builder)
    _targeted_supplementary_coverage_directory(builder)
    _needs_based_local_medicine_supply_configuration(builder)


def code_unit(unit: dict) -> dict:
    text = unit["current_text"]
    contexts = unit.get("contexts") or []
    if not isinstance(text, str) or not isinstance(contexts, list) or not all(isinstance(value, str) for value in contexts):
        raise TypeError("unit must provide string current_text and list[str] contexts")
    builder = primitives.Builder(text, contexts)
    primitives._common_evaluation_and_information(builder)
    primitives._safety(builder)
    primitives._effectiveness(builder)
    primitives._economics(builder)
    primitives._innovation(builder)
    _fairness(builder)
    labels = {dimension: int(any(item["dimension"] == dimension for item in builder.evidence)) for dimension in DIMENSIONS}
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
        "context_sha256": [digest(value) for value in contexts],
        "labels": labels,
        "evidence": builder.evidence,
        "exclusions": builder.exclusions,
        "judgement_status": "completed",
        "input_policy": "current_text_and_supplied_contexts_only",
        "development_history": "candidate04_after_candidate03_evaluation_and_independent_semantic_audits",
    }
