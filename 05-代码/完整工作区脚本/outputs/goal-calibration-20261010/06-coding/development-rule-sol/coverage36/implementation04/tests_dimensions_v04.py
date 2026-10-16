"""Predeclared generic dimensions04 contrasts; never classify actual fixtures.

Expected values and manual reasons were saved before testing in
dimensions-v04-declaration-before-tests.json. Original tests remain untouched.
"""
import copy
import unittest

import dimensions
from evidence import validate_decisions
from relations import RelationView
from source_packet import semantic_unit
from tests_behavior import context, record, member, judge_raw, values


class DimensionsV04Tests(unittest.TestCase):
    def assert_dimensions(self, raw, **expected):
        decisions, view = judge_raw(raw)
        for dim, value in expected.items():
            self.assertEqual(decisions[dim]["value"], value, (raw["text"], dim, decisions[dim]))
        return decisions, view

    def test_ec_route_only(self):
        self.assert_dimensions(record("对于拟申请变更支付范围的药品，申报时选择对应申报条件。"), Ec=0)

    def test_ec_route_plus_content_check(self):
        self.assert_dimensions(record("申报时须先核验本药已有支付范围是否准确，再选择申报条件。"), Ec=1)

    def test_ec_choice_substantive_standard(self):
        self.assert_dimensions(record("申请人应选择与本药实际治疗费用相符的支付标准。"), Ec=1)

    def test_ec_conditional_authorization(self):
        self.assert_dimensions(record("符合条件的药品可申请调整支付范围，申报时选择对应申请类别。"), Ec=1)

    def test_ec_parent_condition(self):
        self.assert_dimensions(member("（一）需先申报。", "下列药品满足条件后方可调整支付标准："), Ec=1)

    def test_ec_routing_no_neighbor_inheritance(self):
        raw = record("对于拟申请调整支付标准的药品，申报时选择申报选项。", [
            context("CTX-previous", "source_paragraph", "药品不申报不能续约。"),
            context("CTX-next", "source_paragraph", "下一类别药品应签订补充协议改变支付标准。", sequence=3)])
        self.assert_dimensions(raw, Ec=0)

    def test_s_current_safety_goal(self):
        decisions, view = self.assert_dimensions(record("第九条为规范药品处方审核，保障患者用药安全，制定本规则。"), S=1, E=0, I=0, F=0)
        self.assertEqual(decisions["S"]["basis_path"], "current_medication_safety_goal")

    def test_s_goal_not_child_inheritance(self):
        raw = record("药品申报资料须在五日内递交。", [context("CTX-purpose", "parent_paragraph", "为保障患者用药安全，制定本规范。")])
        self.assert_dimensions(raw, S=0)

    def test_s_data_safety(self):
        self.assert_dimensions(record("药物研究应保障数据安全。"), S=0)

    def test_s_fund_safety(self):
        self.assert_dimensions(record("药品目录管理应保障基金安全。"), S=0)

    def test_se_current_content_definition(self):
        self.assert_dimensions(record("本规则所称人体药物研究，是指以探明药物安全性和有效性为目的的研究。"), S=1, E=1, I=0, F=0)

    def test_se_trial_name_only(self):
        self.assert_dimensions(record("本药项目名称为临床试验。"), S=0, E=0)

    def test_se_registration_purpose_only(self):
        self.assert_dimensions(record("本药临床试验以申请上市注册为目的。"), S=0, E=0)

    def test_se_general_research_only(self):
        self.assert_dimensions(record("本药将在人体开展药物研究。"), S=0, E=0)

    def test_se_formal_fields(self):
        self.assert_dimensions(record("药物安全性与有效性字段不能为空。"), S=0, E=0)

    def finite_reference_decisions(self, qualification):
        """Consumer-only test of the resolver's declared finite interface.

        Real graph discovery/bounds are independently tested by its owner.
        All text/evidence below is artificial original material, not label data.
        """
        text = "符合第十一条第二款情形的，数据保护期为三年。"
        raw = record(text, [context("CTX-data-scope", "source_paragraph", qualification)])
        unit = semantic_unit(raw)
        view = RelationView(unit)
        quote = view.context_anchor("CTX-data-scope", 0, len(qualification), "人工有限条款条件原文")
        condition = text[:text.index("，")]
        consequence = text[text.index("，") + 1:text.index("。")]
        view.relations.append({"kind": "cited_standard", "current_anchor": view.proposition(), "context_evidence": [quote],
                               "details": {"relation_subtype": "finite_operational_article_reference",
                                           "current_condition_anchor": {"text": condition},
                                           "current_consequence_anchor": {"text": consequence},
                                           "reference_chain": [{"article": 11, "clause": 2}],
                                           "qualification_context_evidence": [quote],
                                           "qualification_text": qualification,
                                           "object_definition": "药品", "standard_text": qualification}})
        decisions = dimensions.judge(view)
        validate_decisions(unit, decisions)
        self.assertEqual(raw, record(text, [context("CTX-data-scope", "source_paragraph", qualification)]))
        return decisions

    def test_i_finite_condition_right(self):
        decisions = self.finite_reference_decisions("本条款中药品的数据保护范围包括证明其与已知活性成分药品相比具有明显临床优势的新的临床试验数据。")
        self.assertEqual(decisions["I"]["value"], 1, decisions["I"])
        self.assertEqual(decisions["I"]["basis_path"], "I4_finite_operative_improvement_data_scope")

    def test_i_plain_data_right(self):
        decisions = self.finite_reference_decisions("本条款中药品的数据保护范围包括该原研药品的申报材料。")
        self.assertEqual(decisions["I"]["value"], 0, decisions["I"])

    def test_i_general_clinical_advantage(self):
        self.assert_dimensions(record("本药数据与已上市药品相比显示明显临床优势。"), E=1, I=0)

    def test_bounded_support_restriction_consumer(self):
        text = "对于拟附条件批准的创新药，不得在探索性临床试验结束前适用本规范。"
        content = "本规范对创新药研发提供研究方案反馈，优先审评按照单独序列管理。"
        unit = semantic_unit(record(text, [context("CTX-support", "source_paragraph", content)]))
        view = RelationView(unit)
        quote = view.context_anchor("CTX-support", 0, len(content), "人工确指可用研发支持")
        view.relations.append({"kind": "named_mechanism", "current_anchor": view.proposition(), "context_evidence": [quote],
                               "details": {"relation_subtype": "bounded_rule_preapplication_authorization",
                                           "current_authorization_anchor": view.proposition(), "object_definition": "创新药研发",
                                           "direct_mechanism": content, "research_stage": "上市前研发", "content": content}})
        decisions = dimensions.judge(view)
        validate_decisions(unit, decisions)
        self.assertEqual({d: decisions[d]["value"] for d in ("I", "S", "E", "F")}, {"I": 1, "S": 0, "E": 0, "F": 0})

    def test_restriction_without_usable_support(self):
        self.assert_dimensions(record("对于拟附条件批准的创新药，不得在探索性临床试验结束前适用本规范。"), I=0)

    def test_negative_priority_field_formality(self):
        self.assert_dimensions(record("创新药研发材料中的优先审评字段不得为空。"), I=0)

    def test_negative_priority_account_formality(self):
        self.assert_dimensions(record("创新药研发项目不得共享优先审评账号密码。"), I=0)

    def test_registration_certificate_validity_not_efficacy(self):
        self.assert_dimensions(record("为确定药品注册证书的有效性，核对证书编号。"), E=0)

    def test_trial_data_validity_only_not_efficacy(self):
        self.assert_dimensions(record("本研究仅确定药物试验数据的有效性与完整性。"), E=0)

    def test_data_validity_with_negated_explicit_drug_effect(self):
        self.assert_dimensions(record("本研究仅确定药物试验数据的有效性与完整性，不评价药物疗效。"), E=1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
