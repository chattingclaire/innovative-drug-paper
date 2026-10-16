"""Predeclared synthetic contrasts for common-manual v1.1 relations.

These expectations are declared before editing the v02 predicates. The texts
are constructed examples, not development records or reference judgements.
Only the parent task executes the suite after the complete implementation freeze.
"""
from __future__ import annotations

import unittest

from tests_behavior import context, record, member, judge_raw, values


def operative_standard(current, content):
    """A supplied, structurally bound complete same-source qualification."""
    source = context("CTX-standard", "source_paragraph", content, sequence=1)
    relation = context("CTX-standard-link", "structural_relation", "", sequence=2,
                       structure={"related_context_ids": ["CTX-standard"]})
    return record(current, [source, relation])


class SemanticV02Tests(unittest.TestCase):
    def assert_values(self, raw, **expected):
        decisions, view = judge_raw(raw)
        actual = values(decisions)
        for dimension, value in expected.items():
            self.assertEqual(actual[dimension], value,
                             (raw["text"], dimension, decisions[dimension]))
        return decisions, view

    # I: technical/clinical qualification is substantive; identities and disease
    # definitions cannot inherit it. An operative standards link may use the
    # supplied complete qualification, without requiring a numeric category.
    def test_comparative_innovative_research_qualification_and_opportunity(self):
        decisions, _ = self.assert_values(record(
            "创新药研发品种与现有治疗药物相比具有明显临床优势的，可以申请研究方案反馈支持机会。"),
            I=1, E=1, F=0)
        paths = {decisions["I"]["basis_path"]}
        paths.update(e["basis_path"] for e in decisions["I"]["details"]["additional_evidence"])
        self.assertIn("I4_substantive_qualification_opportunity", paths)

    def test_modified_research_qualification_can_restrict_opportunity(self):
        self.assert_values(record(
            "改良型新药研发品种不具备相较现有治疗的明显临床优势时，不得申请研究方案反馈支持机会。"),
            I=1, E=1, F=0)

    def test_innovation_identity_and_submission_method_are_insufficient(self):
        self.assert_values(record("本文件适用于创新药，申报材料应在线递交。"),
                           I=0, F=0)

    def test_clinical_advantage_without_innovation_link_is_only_effect_content(self):
        self.assert_values(record("本药与现有治疗相比具有明显临床优势。"),
                           I=0, E=1)

    def test_disease_definition_cannot_take_innovation_from_parent(self):
        self.assert_values(member("（一）用于治疗严重疾病的药品。",
                                  "创新药研发项目同时满足下列条件可以申请研究方案反馈支持机会："),
                           I=0, E=0, F=0)

    def test_complete_nonnumeric_standard_controls_support_termination(self):
        raw = operative_standard(
            "不符合创新研发支持计划资格条件的药品，应终止该计划支持机会。",
            "创新研发支持计划申请条件：创新药研发品种须与现有治疗药物相比具有明显临床优势。")
        decisions, view = self.assert_values(raw, I=1, E=1, F=0)
        self.assertTrue(view.linked("cited_standard"))
        self.assertTrue(decisions["I"]["context_evidence"])

    def test_program_status_does_not_expand_standards(self):
        raw = operative_standard(
            "本药曾进入创新研发支持计划，联系方式现已更新。",
            "创新研发支持计划申请条件：创新药研发品种须与现有治疗药物相比具有明显临床优势。")
        self.assert_values(raw, I=0, E=0, F=0)

    # I2: candidate entry does not require an innovation word, but product change
    # still requires the explicitly stated obstacle and improvement relationship.
    def test_breakability_design_with_explicit_operation_obstacle(self):
        self.assert_values(record(
            "为缓解老年患者掰断片剂的操作困难，拟改善片剂易碎性，降低操作负担。"),
            I=1, F=0)

    def test_strength_and_dosage_design_with_explicit_obstacle(self):
        self.assert_values(record(
            "现有片剂难以掰断，拟开发不同强度的片剂或新的剂型，便于患者操作。"),
            I=1, F=0)

    def test_product_change_alone_is_not_substantive_modification(self):
        self.assert_values(record("拟开发不同强度的片剂和新的剂型。"), I=0, F=0)

    def test_operation_obstacle_without_product_change_is_insufficient(self):
        self.assert_values(record("患者掰断片剂存在操作困难，应说明操作方法。"), I=0, F=0)

    # Ec: treatment payment mode and funded resource decisions are economic
    # content. Fund safety does not become drug risk or patient fairness.
    def test_disease_payment_scope_exception_and_conditional_payment(self):
        self.assert_values(record(
            "符合保障条件的本药病例，可不纳入按病种付费范围，经审核评议后支付。"),
            Ec=1, S=0, I=0, F=0)

    def test_conditional_payment_mode_with_separate_payment_responsibility(self):
        self.assert_values(record(
            "该药不纳入按病种付费范围，经审核符合条件的，基金另行支付其费用。"),
            Ec=1, S=0, F=0)

    def test_payment_mode_parent_condition_is_substantive(self):
        self.assert_values(member("（一）本药用于指定治疗病例。",
                                  "以下病例经审核后，可不纳入按病种付费范围，由基金另行支付："),
                           Ec=1, F=0, I=0)

    def test_payment_mode_field_format_remains_form_only(self):
        self.assert_values(record("本药按病种付费范围字段不能为空，材料应签字递交。"),
                           Ec=0, F=0)

    def test_fund_capacity_linked_to_drug_directory_selection(self):
        self.assert_values(record(
            "医保基金承受能力有限，药品目录选择应考虑支付资源约束。"),
            Ec=1, S=0, F=0)

    def test_fund_capacity_condition_restricts_drug_payment_scope(self):
        self.assert_values(record("基金承受能力不足时限制本药医保支付范围。"),
                           Ec=1, S=0, F=0)

    def test_fund_safety_boundary_restricts_drug_directory_selection(self):
        self.assert_values(record(
            "以医保基金安全为底线，对进入目录的药品更关注雪中送炭。"),
            Ec=1, S=0, F=0)

    def test_fund_safety_without_drug_selection_or_payment_is_insufficient(self):
        self.assert_values(record("应维护医保基金运行安全，并完善办公安全管理。"),
                           Ec=0, S=0, F=0)

    def test_unconnected_fund_resource_statement_is_not_drug_economics(self):
        self.assert_values(record("医保基金承受能力有限，办公设备采购应控制支出。"),
                           Ec=0, S=0, F=0)

    # F: an explicit eligibility-to-application statement supplies the relation
    # even without 对/为/因此. A publication purpose naming a program does not.
    def test_need_condition_to_application_without_specific_connective(self):
        self.assert_values(record(
            "本药目标适应症没有有效治疗选项，满足此条件可申请优先审评。"),
            E=1, F=1, I=0)

    def test_domestic_option_gap_condition_to_application(self):
        self.assert_values(record(
            "境内无对应获批药物时，可申请本品临床急需使用。"),
            E=0, F=1, I=0)

    def test_gap_without_opportunity_is_not_fairness(self):
        self.assert_values(record("本药目标适应症尚无有效治疗药物。"), E=1, F=0)

    def test_shortage_and_priority_publication_purpose_is_not_allocation(self):
        self.assert_values(record("为规范临床急需短缺药品优先审评，制定本程序。"),
                           F=0)

    def test_publication_purpose_without_demonstrative_is_not_allocation(self):
        self.assert_values(record("为缓解药品供应短缺，制定优先审评程序。"),
                           F=0)

    def test_actual_allocation_can_coexist_with_publication_action(self):
        self.assert_values(record(
            "为缓解临床急需短缺药品的供药缺口，安排这些药品优先审评并制定办理规则。"),
            F=1)

    def test_publication_purpose_does_not_erase_effect_content(self):
        self.assert_values(record(
            "为研究尚无有效治疗药物的疾病，制定优先审评程序。"),
            E=1, F=0)

    # Bounded object scope cannot supply resource content. The whole-review
    # service definition and development stage are separate source facts.
    def test_generic_team_with_innovation_scope_has_no_defined_service(self):
        text = "根据具体品种研究任务组建审评团队。"
        raw = record(text, [context("CTX-scope", "source_paragraph",
                                   "（一）适用范围：创新药研发项目。"),
                            context("CTX-current", "paragraph", text, sequence=2)])
        self.assert_values(raw, I=0)

    def test_current_team_has_complete_stable_technical_service_definition(self):
        text = "根据具体品种研究任务组建审评团队。"
        paragraph = text + "该审评团队负责注册申请申报前的沟通交流及技术审评全过程，并保持人员相对稳定。"
        raw = record(text, [context("CTX-scope", "source_paragraph",
                                   "（一）适用范围：创新药研发项目。"),
                            context("CTX-stage", "source_paragraph",
                                   "本文件适用于药品上市前研发阶段。", sequence=2),
                            context("CTX-current", "paragraph", paragraph, sequence=3)])
        decisions, view = self.assert_values(raw, I=1)
        self.assertTrue(view.linked("named_mechanism"))
        self.assertTrue(decisions["I"]["context_evidence"])

    def test_routine_after_marketing_service_does_not_inherit_research_support(self):
        text = "根据具体品种上市后常规临床服务任务组建审评团队。"
        paragraph = text + "该审评团队负责注册申请申报前的沟通交流及技术审评全过程，并保持人员相对稳定。"
        raw = record(text, [context("CTX-scope", "source_paragraph",
                                   "（一）适用范围：创新药研发项目。"),
                            context("CTX-stage", "source_paragraph",
                                   "本文件适用于药品上市前研发阶段。", sequence=2),
                            context("CTX-current", "paragraph", paragraph, sequence=3)])
        self.assert_values(raw, I=0)

    def test_breakability_attribute_alone_is_not_an_operation_obstacle(self):
        self.assert_values(record("拟改善片剂易碎性，并收集相关属性数据。"), I=0)

    def test_same_paragraph_operation_data_reference_uses_actual_limitation(self):
        text = "应收集片剂掰断操作便利性数据，并参考数据改善片剂易碎性。"
        paragraph = "手指灵活性不足可能限制患者的掰断操作。" + text
        raw = record(text, [context("CTX-current", "paragraph", paragraph)])
        decisions, view = self.assert_values(raw, I=1, F=0)
        links = view.linked("parent_predicate")
        self.assertTrue(any(r["details"].get("relation_subtype") == "same_paragraph_operation_reference" for r in links))
        self.assertTrue(decisions["I"]["context_evidence"])

    def test_adjacent_unbound_operation_limitation_cannot_supply_content(self):
        text = "应收集片剂掰断操作便利性数据，并参考数据改善片剂易碎性。"
        raw = record(text, [context("CTX-current", "paragraph", text, sequence=2),
                            context("CTX-unbound", "source_paragraph",
                                    "手指灵活性不足可能限制患者的掰断操作。")])
        self.assert_values(raw, I=0, F=0)


if __name__ == "__main__":
    unittest.main()
