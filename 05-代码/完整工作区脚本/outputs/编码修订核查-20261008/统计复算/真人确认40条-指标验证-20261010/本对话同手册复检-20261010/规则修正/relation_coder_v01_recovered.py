"""Five-dimension relation coder for the frozen dc26 calibration manual.

This candidate consumes only ``current_text`` and the supplied ``contexts``.
It does not read source files, old evidence, machine predictions, human labels,
material identifiers, departments, or filenames.  A positive decision always
stores the complete current proposition so conditions and negation remain in
scope, plus literal current/context anchors used by the relation.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable


VERSION = "dc26-relation-candidate-01"
MANUAL_SHA256 = "dc26bf77c62c2f60f6d3e71a1fe1d7aca0d63f12a516b72160519eef06acd50f"
DIMENSIONS = ("S", "E", "Ec", "I", "F")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _search(pattern: str, text: str, flags: int = 0):
    return re.search(pattern, text, flags)


def _all(pattern: str, text: str, flags: int = 0):
    return list(re.finditer(pattern, text, flags))


def _anchor(match: re.Match, role: str) -> dict:
    return {
        "start": match.start(),
        "end": match.end(),
        "text": match.group(),
        "role": role,
    }


def _context_anchors(pattern: str, contexts: list[str], role: str) -> list[dict]:
    out = []
    for index, value in enumerate(contexts):
        match = _search(pattern, value, re.I)
        if match:
            out.append({
                "context_index": index,
                "start": match.start(),
                "end": match.end(),
                "text": match.group(),
                "role": role,
                "context_sha256": digest(value),
            })
    return out


def _scope_signals(text: str) -> dict:
    patterns = {
        "negation": r"不再|不予|未|无|不得|不能|并非|除外|失败|不纳入",
        "condition": r"如果|若|符合|在.+情况下|且|同时满足|申请时|自.+之日起",
        "alternative": r"或者|或是|任一|相比",
        "future_or_purpose": r"未来|拟|计划|旨在|推动|鼓励",
    }
    return {key: [m.group() for m in _all(pattern, text)] for key, pattern in patterns.items()}


@dataclass
class Builder:
    text: str
    contexts: list[str]

    def __post_init__(self):
        self.evidence: list[dict] = []
        self.exclusions: list[dict] = []

    def add(
        self,
        dimension: str,
        rule: str,
        basis: str,
        current_anchors: Iterable[tuple[re.Match, str]],
        context_anchors: Iterable[dict] = (),
    ) -> None:
        anchors = [_anchor(match, role) for match, role in current_anchors]
        if not anchors:
            raise ValueError(f"{rule} requires a literal current anchor")
        key = (dimension, rule, tuple((a["start"], a["end"], a["role"]) for a in anchors))
        for item in self.evidence:
            old = (item["dimension"], item["rule"], tuple(
                (a["start"], a["end"], a["role"]) for a in item["current_relation_anchors"]
            ))
            if old == key:
                return
        context_items = list(context_anchors)
        self.evidence.append({
            "dimension": dimension,
            "rule": rule,
            "basis": basis,
            "current_statement": {
                "start": 0,
                "end": len(self.text),
                "text": self.text,
                "sha256": digest(self.text),
            },
            "current_relation_anchors": anchors,
            "consumed_context_anchors": context_items,
            "consumed_context_indices": sorted({x["context_index"] for x in context_items}),
            "scope_signals": _scope_signals(self.text),
        })

    def exclude(self, rule: str, reason: str, match: re.Match) -> None:
        self.exclusions.append({
            "rule": rule,
            "reason": reason,
            "anchor": _anchor(match, "excluded_candidate"),
            "current_statement": self.text,
        })


def _common_evaluation_and_information(builder: Builder) -> None:
    text = builder.text
    dimension_terms = {
        "S": r"安全性",
        "E": r"有效性",
        "Ec": r"经济性",
        "I": r"创新性|创新价值|创新程度",
        "F": r"公平性",
    }
    drug_value = _search(r"药品价值|药物价值|患者治疗", text)
    evaluation = _search(r"研判|评价|评估|比较|量化|分级", text)
    material_content = _search(r"(?:内容涉及|包括|提供|补充|核对|核验|验证)[^。；;]*(?:信息|证据)", text)
    for dimension, pattern in dimension_terms.items():
        term = _search(pattern, text)
        if not term:
            continue
        if drug_value and evaluation:
            builder.add(
                dimension,
                "COMMON_dimension_evaluation_of_drug_value",
                "当前以药品价值或患者治疗为对象，实质评价或研判该维；不据此补写具体机制。",
                [(term, "dimension_content"), (drug_value, "drug_value_object"), (evaluation, "evaluation_predicate")],
            )
        elif material_content and _search(r"药品|药物|申报材料", text):
            builder.add(
                dimension,
                "COMMON_substantive_dimension_information_requirement",
                "当前明确要求材料包含该维实质信息；不是仅有栏目名称、格式或递交动作。",
                [(term, "dimension_information"), (material_content, "information_content_requirement")],
            )


def _safety(builder: Builder) -> None:
    text = builder.text
    risk = _search(r"药物研发期间风险管理计划|药物风险|用药风险|不良反应|药物警戒|用药差错|试验风险", text)
    action = _search(r"确认|开展风险管理|风险控制|减少用药差错|风险评估|提供指导|技术指导", text)
    if risk and action:
        builder.add(
            "S", "S_drug_risk_evidence_or_control",
            "明确药物或用药风险及其证据、识别或控制安排。",
            [(risk, "drug_risk_content"), (action, "risk_evidence_or_control")],
        )
    fund = _search(r"基金安全", text)
    if fund and not risk:
        builder.exclude("S_fund_safety_not_drug_harm", "基金安全不是药物造成的损害或用药风险。", fund)


def _effectiveness(builder: Builder) -> None:
    text, contexts = builder.text, builder.contexts
    direct_patterns = [
        (r"合理有效的治疗", "effective_treatment"),
        (r"临床获益|患者获益显著|健康收益", "clinical_or_health_benefit"),
        (r"提升[^。；;]{0,20}整体健康水平", "health_level_improvement"),
        (r"尚无有效防治手段|无有效治疗药物|无有效治疗选项", "absence_of_effective_option"),
        (r"与现有治疗手段相比[^。；;]{0,24}明显临床优势", "comparative_clinical_advantage"),
        (r"药理效应[^。；;]{0,20}临床获益", "pharmacologic_effect_to_clinical_benefit"),
    ]
    for pattern, role in direct_patterns:
        match = _search(pattern, text)
        if match and _search(r"药|治疗|患者|临床", text):
            builder.add(
                "E", f"E_{role}",
                "当前明确表达药物防治效果、健康收益、临床获益或相应效果不足。",
                [(match, role)],
            )
    unable = _search(r"无法治愈|不能治愈|未能治愈", text)
    if unable:
        context = _context_anchors(
            r"新药研发[^。；;]{0,40}(?:核心目标|满足患者.{0,8}治疗需求|确定研发立题)|以患者需求确定研发立题",
            contexts,
            "direct_drug_development_goal_context",
        )
        if context:
            builder.add(
                "E", "E_unmet_cure_result_bound_to_drug_development_goal",
                "具体治疗结果未达由当前明确承接的药物研发目标补足对象；不等同于无有效药物。",
                [(unable, "unmet_treatment_result")], context,
            )
        else:
            builder.exclude(
                "E_unable_to_cure_without_drug_effect_object",
                "疾病无法治愈但没有药物研发或药物效果的直接承接。",
                unable,
            )


def _economics(builder: Builder) -> None:
    text = builder.text
    substantive = [
        (r"(?:申请|主动申请)?调整医保支付范围|医保支付范围[^。；;]{0,12}(?:调整|变化|不做任何调整)", "payment_scope_arrangement"),
        (r"医保支付标准[^。；;]{0,16}(?:调整|变化|到期)|支付标准", "payment_standard"),
        (r"基金支出预算|药品费用预算|预算增幅", "budget_impact"),
        (r"纳入支付范围的药品费用|价格费用数据|汇率、?价格(?:和|及)?费用", "price_or_cost_information"),
        (r"商业健康保险保障范围[^。；;]{0,40}(?:支付|费用)|经审核评议程序后支付", "insurance_payment_responsibility"),
        (r"医保基金安全[^。；;]{0,24}(?:目录|药品)|目录[^。；;]{0,24}医保基金安全", "payment_resource_constraint"),
        (r"降价机制|降幅|重新谈判", "price_adjustment_arrangement"),
    ]
    for pattern, role in substantive:
        match = _search(pattern, text)
        if not match:
            continue
        if role == "price_adjustment_arrangement" and not _search(r"降幅|降价机制|支付标准|支付范围|预算", text):
            continue
        builder.add(
            "Ec", f"Ec_{role}",
            "当前明确规定、改变、核验或限定药品价格、费用、支付责任/范围或预算内容。",
            [(match, role)],
        )
    latest = _search(r"(?:汇率、?|价格(?:和|及)?费用|价格费用数据)[^。；;]{0,40}(?:最新数据|以截至[^。；;]{0,18}为准)", text)
    if latest:
        builder.add(
            "Ec", "Ec_economic_evidence_observation_date",
            "以特定时点的最新价格费用数据为准，规定了经济证据的内容版本，不是递交期限。",
            [(latest, "economic_information_and_observation_date")],
        )
    procedure = _search(r"价格谈判|价格协商", text)
    if procedure and not any(e["dimension"] == "Ec" for e in builder.evidence):
        builder.exclude(
            "Ec_negotiation_procedure_without_substantive_economic_content",
            "只有价格协商阶段或成败，没有金额、标准、范围、费用或预算内容。",
            procedure,
        )
    deadline = _search(r"价格材料[^。；;]{0,20}(?:前|截止)[^。；;]{0,10}(?:递交|提交)", text)
    if deadline:
        builder.exclusions.append({
            "rule": "Ec_material_submission_deadline_only",
            "reason": "价格材料的递交期限不等于经济信息的观察时点或实质核验。",
            "anchor": _anchor(deadline, "submission_deadline"),
            "current_statement": text,
        })
        builder.evidence = [e for e in builder.evidence if e["dimension"] != "Ec"]


def _innovation(builder: Builder) -> None:
    text, contexts = builder.text, builder.contexts
    classification = _search(r"(?:1\s*类|一类)[^。；;]{0,50}(?:创新药|新药)|(?:创新药|改良型新药)[^。；;]{0,50}(?:1\s*类|一类)", text)
    definition = _search(r"是指|包括|以下简称", text)
    differentiated_right = _search(r"数据保护(?:期)?|保护期|可申请重新谈判|差异化准入|续约|权利|待遇", text)
    explicit_innovation = _search(r"创新药|改良型新药", text)
    if classification and (definition or differentiated_right):
        anchors = [(classification, "actual_innovation_registration_class")]
        if definition:
            anchors.append((definition, "classification_definition"))
        if differentiated_right:
            anchors.append((differentiated_right, "differentiated_right_or_obligation"))
        builder.add(
            "I", "I_actual_classification_definition_or_institutional_use",
            "明确创新/改良分类的含义，或该分类决定差异化权利义务；不把孤立序号当创新。",
            anchors,
        )
    innovation_degree = _search(r"创新程度(?:较高|较低|高|低)|创新价值(?:进行)?(?:量化|分级|评价|评估)", text)
    if innovation_degree and _search(r"药品|药物|目录", text):
        builder.add(
            "I", "I_innovation_value_or_degree_as_current_criterion",
            "当前把药品创新程度或创新价值作为实质评价、量化或遴选内容。",
            [(innovation_degree, "innovation_value_or_degree")],
        )
    current_support = _search(r"(?:专门)?(?:起草|制定|编制|提供)[^。；;]{0,80}(?:技术指导原则|技术指导|研发指导)", text)
    target = _search(r"创新药研发|药物研发", text)
    support_use = _search(r"为[^。；;]{0,80}(?:药物研发全过程|研发全过程)[^。；;]{0,30}提供指导|为[^。；;]{0,80}提供(?:技术)?指导", text)
    if current_support and target and support_use:
        builder.add(
            "I", "I_actual_targeted_innovation_research_guidance",
            "创新研发对象、当前专门技术资源和研发指导用途直接相连。",
            [(current_support, "current_guidance_resource"), (target, "innovation_research_target"), (support_use, "research_guidance_function")],
        )
    named_action = _search(r"(?:组织开展|决定开展|批准实施|启动|终止)[^。；;]{0,50}(?:创新药[^。；;]{0,25})?(?:试点工作|计划|项目)", text)
    if named_action:
        object_context = _context_anchors(r"试点项目范围[^。；;]{0,30}(?:1\s*类)?创新药", contexts, "named_program_innovation_object")
        mechanism_context = _context_anchors(r"受理后[^。；;]{0,20}\d+\s*个工作日内完成审评审批|缩短[^。；;]{0,20}(?:审评|试验启动)", contexts, "named_program_concrete_convenience")
        if object_context and mechanism_context:
            builder.add(
                "I", "I_named_program_actual_implementation_with_supplied_mechanism",
                "当前实施确指计划，共同材料提供同一计划的创新对象和具体研发便利。",
                [(named_action, "current_named_program_action")],
                object_context + mechanism_context,
            )
        else:
            builder.exclude(
                "I_named_program_without_complete_supplied_mechanism",
                "具名计划缺少共同输入中的创新对象或具体支持机制。",
                named_action,
            )
    change = _search(r"改善[^。；;]{0,12}(?:片剂|制剂|药品)[^。；;]{0,12}(?:易碎性|使用便利性|给药便利性)|开发[^。；;]{0,25}(?:适宜规格|适宜剂型|不同强度的片剂|其他规格或剂型)", text)
    current_obstacle = _search(r"掰断操作便利性|吞咽困难|操作障碍|使用障碍", text)
    context_obstacle = _context_anchors(r"手指灵活性[^。；;]{0,20}(?:影响|不足)|操作(?:困难|障碍)|吞咽困难", contexts, "specific_use_obstacle_context")
    if change and (current_obstacle or context_obstacle):
        anchors = [(change, "product_change_for_use_improvement")]
        if current_obstacle:
            anchors.append((current_obstacle, "current_use_obstacle"))
        builder.add(
            "I", "I_use_obstacle_to_product_improvement_relation",
            "明确操作/使用障碍、拟用产品改变和使用表现改善关系；不表示改良效果已经实现。",
            anchors,
            context_obstacle,
        )
    qualification = _search(r"(?:创新药|改良型新药)[^。；;]{0,60}(?:申请|适用)[^。；;]{0,24}(?:程序|支持)|(?:申请|适用)[^。；;]{0,24}(?:突破性治疗药物程序)[^。；;]{0,30}(?:创新药|改良型新药)", text)
    substantive_condition = _search(r"尚无有效防治手段|与现有治疗手段相比[^。；;]{0,24}明显临床优势", text)
    if qualification and substantive_condition:
        builder.add(
            "I", "I_substantive_innovation_qualification_condition",
            "创新/改良对象与具体比较或缺口条件共同决定支持程序资格。",
            [(qualification, "innovation_qualification_use"), (substantive_condition, "substantive_qualification_condition")],
        )
    if explicit_innovation and _search(r"为鼓励|鼓励研究和创制", text) and _search(r"制定本工作程序|发布|印发", text):
        builder.exclude(
            "I_promulgation_purpose_not_actual_support",
            "制定或发布程序的创新宗旨不是当前实体支持安排。",
            explicit_innovation,
        )


def _fairness(builder: Builder) -> None:
    text = builder.text
    gap_patterns = [
        (r"境内无获批对应治疗选项", "no_domestically_approved_corresponding_option"),
        (r"尚无有效防治手段|无有效治疗药物|无有效治疗选项", "no_effective_treatment_option"),
        (r"市场短缺|现实供应不足|临床急需的短缺药品|短缺药品", "actual_supply_shortage"),
    ]
    action = _search(r"优先审评审批|申请适用突破性治疗药物程序|纳入优先审评审批程序|优先保障|优先供应", text)
    for pattern, role in gap_patterns:
        gap = _search(pattern, text)
        if gap and action:
            builder.add(
                "F", "F_explicit_guarantee_gap_with_targeted_opportunity",
                "明确治疗选项或现实供应缺口与同一药品的针对性申请、优先或保障安排相连；限制/撤回也保留完整范围。",
                [(gap, role), (action, "targeted_opportunity_or_allocation")],
            )
    unlisted = _search(r"境外已上市境内未上市", text)
    if unlisted and action and not any(e["dimension"] == "F" for e in builder.evidence):
        builder.exclude(
            "F_target_product_unlisted_is_not_option_gap",
            "单个目标产品未在境内上市，不证明境内没有对应治疗选项或现实供应不足。",
            unlisted,
        )
    demand = _search(r"用药需求评估|基层需求评估", text)
    if demand and not any(e["dimension"] == "F" for e in builder.evidence):
        builder.exclude(
            "F_general_needs_assessment_without_equity_relation",
            "一般需求评估和药品遴选没有指出患者获取差异、保障缺口或按需待遇。",
            demand,
        )
    insurance = _search(r"商业健康保险保障范围[^。；;]{0,40}(?:支付|药品应用病例)|经审核评议程序后支付", text)
    if insurance:
        builder.add(
            "F", "F_explicit_insurance_coverage_and_payment_opportunity",
            "明确保险保障范围和支付待遇，直接涉及患者获得所需药品治疗的保障机会。",
            [(insurance, "coverage_and_payment_opportunity")],
        )
    affordability = _search(r"患者(?:能否)?负担|患者可负担性|因收入[^。；;]{0,30}(?:无法|难以)(?:获得|持续接受)", text)
    if affordability:
        builder.add(
            "F", "F_patient_affordability_or_access_barrier",
            "明确患者支付能力或不合理获取障碍。",
            [(affordability, "patient_affordability_or_access_barrier")],
        )


def code_unit(unit: dict) -> dict:
    text = unit["current_text"]
    contexts = unit.get("contexts") or []
    if not isinstance(text, str) or not isinstance(contexts, list) or not all(isinstance(x, str) for x in contexts):
        raise TypeError("unit must provide string current_text and list[str] contexts")
    builder = Builder(text, contexts)
    _common_evaluation_and_information(builder)
    _safety(builder)
    _effectiveness(builder)
    _economics(builder)
    _innovation(builder)
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
    }
