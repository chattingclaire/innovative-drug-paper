import copy
import hashlib
import unittest

import rule_support
import rules_ec


def make_record(text, **extra):
    record = {
        "unit_text": text,
        "input_assessment": {"status": "sufficient", "basis": "Complete synthetic development sentence."},
        "source_sha256": "source-test",
        "paragraph_context": [],
    }
    record.update(extra)
    return record


def revised(record):
    result = rule_support.v25.code_unit(record)
    before = copy.deepcopy(result)
    returned = rules_ec.revise(record, result)
    assert returned is result
    assert result["labels"] == before["labels"], "revise must leave labels for root rebuild"
    assert ([e for e in result["evidence"] if e["dimension"] != "Ec"] ==
            [e for e in before["evidence"] if e["dimension"] != "Ec"])
    rule_support.rebuild(result)
    return result


def ec_evidence(result):
    return [e for e in result["evidence"] if e["dimension"] == "Ec"]


class EconomicRulesTest(unittest.TestCase):
    def assert_ec(self, text, **extra):
        result = revised(make_record(text, **extra))
        self.assertEqual(result["labels"]["Ec"], 1, text)
        for evidence in ec_evidence(result):
            self.assertEqual(text[evidence["start"]:evidence["end"]], evidence["text"])
        return result

    def assert_no_ec(self, text, **extra):
        result = revised(make_record(text, **extra))
        self.assertEqual(result["labels"]["Ec"], 0, text)
        self.assertEqual(ec_evidence(result), [])
        return result

    def test_price_and_payment_standard_synonym_order(self):
        result = self.assert_ec("同通用名药品挂网价格高于支付标准1.8倍。")
        rules = {e["rule"] for e in ec_evidence(result)}
        self.assertIn("V27_Ec_drug_price", rules)
        self.assertIn("V27_Ec_payment_standard", rules)

    def test_drug_fee_and_fee_responsibility(self):
        result = self.assert_ec("该药品费用由医保基金和患者共同支付。")
        self.assertTrue(any(e["rule"] == "V27_Ec_medicine_cost" for e in ec_evidence(result)))

    def test_cost_effectiveness_and_budget_impact(self):
        result = self.assert_ec("申报人应提交该药品的成本效果分析和预算影响评估。")
        rules = {e["rule"] for e in ec_evidence(result)}
        self.assertIn("V27_Ec_economic_evaluation_information", rules)
        self.assertIn("V27_Ec_budget_impact", rules)

    def test_pharmacoeconomic_report_and_hyphenated_methods(self):
        for text in (
            "能够提供完整的药物经济学报告以认识该药品价值。",
            "提交该药品的成本-效用分析、成本—效果分析和最小成本分析法。",
            "根据药品决策需求开展成本—效果分析 (CEA)、成本—效用分析 (CUA)、成本—效益分析 (CBA)及最小成本分析 (CMA)。",
        ):
            with self.subTest(text=text):
                self.assert_ec(text)
        self.assert_no_ec("药物经济学专家参加评审，报告按编号归档。")
        self.assert_no_ec("药品成本—效用分析文件按编号归档。")

    def test_comparison_keeps_drug_object_across_comma(self):
        for text in (
            "与同治疗领域的其他药品相比，价格/费用明显偏高。",
            "与同治疗领域的其他药品相比，价格或费用明显偏高，且占用基金量较多。",
        ):
            with self.subTest(text=text):
                result = self.assert_ec(text)
                self.assertTrue(any(e["rule"] == "V27_Ec_comparative_drug_price_or_cost"
                                    for e in ec_evidence(result)))
        self.assert_no_ec("与同类医疗设备相比，价格/费用明显偏高，药品另行采购。")

    def test_drug_economic_dimension_and_study_evidence(self):
        for text in (
            "围绕药品临床使用问题，从安全性、有效性、经济性、创新性等维度开展评价。",
            "形成药品临床应用安全性、有效性、经济性等相关证据。",
            "比较该药品经济性方面的优势和不足。",
        ):
            with self.subTest(text=text):
                self.assert_ec(text)
        text = "重视基于我国人群循证结果的经济性研究，选择数据作为模型参数。"
        paragraph = {"paragraph_id": "p4", "pages": [4],
                     "text": "分析测算药品的成本，判断药品临床应用的经济价值。" + text}
        result = self.assert_ec(text, paragraph_context=[paragraph])
        self.assertTrue(any(e["rule"] == "V27_Ec_contextual_economic_study"
                            and e.get("context_dependency") for e in ec_evidence(result)))
        self.assert_no_ec(text)
        self.assert_no_ec("评估医院运营成本，经济性研究结果另行归档。")
        self.assert_no_ec("药品临床应用数据另存，医院运营成本的经济性相关证据由财务处提供。")

    def test_drug_expense_information_requirement(self):
        self.assert_ec("申报内容包括申报药品基本信息、费用信息、支持性材料。")
        self.assert_ec("企业须提交药品费用信息和价格信息。")
        self.assert_no_ec("药品注册申报费用信息由行政处归档。")
        self.assert_no_ec("申报药品基本信息、注册费用信息及支持性材料。")
        self.assert_no_ec("药品申报系统的使用费用信息按编号归档。")

    def test_data_source_and_medical_claims_definition_are_not_drug_economics(self):
        self.assert_no_ec("药品临床应用真实世界数据来源包括患者病历、费用结算等卫生信息系统数据。")
        self.assert_no_ec("医保数据是医疗保健提供者向保险公司提交的用以获得治疗赔付的医疗费用及相关信息汇编。")

    def test_mixed_administrative_fee_and_drug_economic_evaluation(self):
        result = self.assert_ec("分别核算注册费用和该药品的成本—效用分析结果。")
        self.assertTrue(any("成本—效用" in e["text"] for e in ec_evidence(result)))

    def test_sales_amount_and_use_volume(self):
        self.assert_ec("定期监测该药品销售金额和使用量。")

    def test_insurance_bears_drug_cost(self):
        self.assert_ec("商业健康保险承担该创新药的药费。")

    def test_patient_drug_cost_burden_is_economic(self):
        self.assert_ec("通过降价减轻患者药费负担。")

    def test_verified_ratio_reference(self):
        text = "根据比值A、比值B的计算结果调整支付标准。"
        supplement = {
            "kind": "same_source_ratio_definition",
            "original_unit_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "contexts": [{
                "paragraph_id": "p1",
                "source_sha256": "source-test",
                "pages": [1],
                "verification": "synthetic verified definition",
                "text": "比值A=实际药品费用/药品费用预算；比值B=药品费用预算增加值/基金实际支出预算。",
            }],
        }
        result = self.assert_ec(text, verified_supplemental_context=[supplement])
        ratio = [e for e in ec_evidence(result) if e["rule"] in {"Ec05", "V27_Ec_ratio_reference"}]
        self.assertTrue(ratio)
        self.assertTrue(any(e.get("context_dependency") for e in ratio))

    def test_explicit_same_paragraph_data_anaphora(self):
        text = "相关数据是续约测算的重要基础。"
        paragraph = {"paragraph_id": "p2", "pages": [2],
                     "text": "医保部门反馈谈判药品费用和基金支出。相关数据是续约测算的重要基础。"}
        result = self.assert_ec(text, paragraph_context=[paragraph])
        self.assertTrue(any(e["rule"] == "V27_Ec_explicit_data_anaphora" for e in ec_evidence(result)))

    def test_administrative_registration_fee_excluded(self):
        self.assert_no_ec("药品注册申请人应缴纳申报费用。")

    def test_research_funds_excluded(self):
        self.assert_no_ec("创新药研究项目经费由研究机构承担。")

    def test_general_medical_service_price_excluded_despite_other_drug_clause(self):
        self.assert_no_ec("医院应降低医疗服务价格；同时加强药品供应。")

    def test_negotiation_procedure_only_excluded(self):
        self.assert_no_ec("组织开展价格协商。")

    def test_expert_background_only_excluded(self):
        self.assert_no_ec("药物经济学专家参加评审。")

    def test_file_disclosure_only_excluded(self):
        self.assert_no_ec("摘要幻灯片PPT2不含经济性/价格费用信息。")

    def test_payment_scope_name_alone_excluded(self):
        self.assert_no_ec("反馈企业该药品的医保支付范围。")

    def test_fund_security_alone_excluded(self):
        self.assert_no_ec("加强医保基金监管，确保基金安全。")

    def test_mixed_confidentiality_does_not_delete_substantive_claim(self):
        result = self.assert_ec("提交药品成本效果分析，并对价格资料保密。")
        self.assertTrue(any("成本效果" in e["text"] for e in ec_evidence(result)))
        self.assertFalse(any(e["text"] == "价格" for e in ec_evidence(result)))

    def test_normalization_preserves_original_offsets(self):
        text = "应核算该药 品费用及支付标准。"
        result = self.assert_ec(text)
        self.assertTrue(any("药 品费用" in e["text"] for e in ec_evidence(result)))

    def test_ambiguous_burden_is_flagged_not_forced_positive(self):
        result = self.assert_no_ec("评估疾病负担及患者体验。")
        self.assertTrue(any(f.get("rule") == "V27_Ec_ambiguous_burden"
                            for f in result["review_flags"]))

    def test_migrated_price_payment_and_amount_groups(self):
        for text in (
            "评估该药品的医保支付意愿。",
            "该药物的报价为80元。",
            "推动短缺药品稳价。",
            "该药品可申请DRG除外支付。",
            "统计药品业务收入。",
            "监测药品交易平台交易量。",
            "测算该药品对基金年均实际支出的影响。",
            "评价药品支付对基金可持续性的影响。",
            "明确该药品仅限符合适应症条件方可报销。",
            "慈善捐赠支持困难群众用药。",
            "遵循安全、有效、经济、适宜的合理用药原则。",
        ):
            with self.subTest(text=text):
                self.assert_ec(text)

    def test_mixed_non_drug_expenses_preserve_independent_drug_cost(self):
        for text in (
            "分别核算注册费用和药品费用。",
            "分别核算研究成本和药物治疗成本。",
            "设备采购成本与药费分别由机构和患者承担。",
            "办公设备成本及药品费用分别列支。",
            "降低医疗服务价格和药品价格。",
        ):
            with self.subTest(text=text):
                self.assert_ec(text)

    def test_non_drug_economic_object_does_not_inherit_drug_scope(self):
        for text in (
            "药品研究机构应核算研究成本。",
            "药品企业应控制办公成本。",
            "统计药品研究机构的设备采购使用金额。",
            "药品企业评估办公设备的成本效果。",
            "商业保险支付医疗服务费用。",
            "慈善项目支付机构运行经费。",
            "患者自行承担门诊费用。",
            "评估城市交通建设的成本效果。",
        ):
            with self.subTest(text=text):
                self.assert_no_ec(text)

    def test_payment_standard_and_evaluation_documents_archive_only(self):
        for text in (
            "药品支付标准资料按日期归档。",
            "药品成本效果分析文件按编号归档。",
            "对药品成本效果资料保密。",
        ):
            with self.subTest(text=text):
                self.assert_no_ec(text)

    def test_same_paragraph_context_does_not_silently_propagate(self):
        text = "相关数据按续约日期归档。"
        paragraph = {"paragraph_id": "p3", "pages": [3],
                     "text": "核算药品费用和基金支出。" + text}
        self.assert_no_ec(text, paragraph_context=[paragraph])
        self.assert_no_ec("比值A超过约定数值。")

    def test_treatment_cost_and_reimbursement_rate(self):
        self.assert_ec("该药物的治疗费用由患者自行承担。")
        self.assert_ec("该药品报销比例为70%。")
        self.assert_ec("应评价该药品的经济性。")

    def test_ratio_requires_same_source_and_substantive_use(self):
        for text, context_source in (
            ("比值A资料按日期归档。", "source-test"),
            ("按照比值B确定降幅。", "different-source"),
        ):
            supplement = {
                "kind": "same_source_ratio_definition",
                "original_unit_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "contexts": [{"paragraph_id": "p1", "source_sha256": context_source,
                              "pages": [1], "verification": "synthetic development definition",
                              "text": "比值A为药品费用与预算的比值；比值B为基金实际支出与预算的比值。"}],
            }
            with self.subTest(text=text):
                self.assert_no_ec(text, verified_supplemental_context=[supplement])

    def test_revision_idempotence_and_field_isolation(self):
        record = make_record("该药品价格下调；办公设备成本另行核算。")
        result = rule_support.v25.code_unit(record)
        before = copy.deepcopy(result)
        rules_ec.revise(record, result)
        for key in before.keys() - {"evidence", "suppressions", "review_flags"}:
            self.assertEqual(result[key], before[key], key)
        once = copy.deepcopy(result)
        rules_ec.revise(record, result)
        self.assertEqual(result, once)

    def test_source_audit_economic_evaluation_enumerations(self):
        for text in (
            "对药品临床使用的安全性、有效性、经济性等开展综合评价。",
            "申报药品应说明公平性（含经济性）方面的比较优势。",
            "综合考虑药物经济性等因素。",
            "该药品按规定提交药物经济学等资料。",
            "对同类药品按照药物经济学原则进行比较。",
            "其他不符合安全性、有效性、经济性等条件的药品。",
        ):
            with self.subTest(text=text): self.assert_ec(text)

    def test_source_audit_price_results_and_local_object(self):
        for text in (
            "符合价格合理等条件的药品可纳入目录。",
            "该品种为药品，不会因为价格高而被纳入目录。",
            "专家对药品提出协商价格的评估意见。",
            "对拟价格协商的药品开展测算并提出评估意见。",
            "建立药品、医用耗材价格形成机制。",
            "治理药品、高值医用耗材价格虚高。",
        ):
            with self.subTest(text=text): self.assert_ec(text)
        self.assert_no_ec("完善医疗服务价格项目，建立价格科学确定、动态调整机制。",
                          paragraph_context=[{"paragraph_id":"p", "text":"药品价格应当合理。完善医疗服务价格项目，建立价格科学确定、动态调整机制。"}])

    def test_source_audit_substantive_payment_versus_scope_name_and_expiry(self):
        for text in (
            "对符合条件的药品，由药物经济学专家按规则确定支付标准。",
            "监测谈判药品临床使用情况，及时掌握医保基金支付情况。",
            "每月按流程反馈谈判药品的药品费用和医保基金支出情况。",
            "申办者应免费向患者提供临床试验用药品。",
            "药品使用后发生的费用由基金支付。",
        ):
            with self.subTest(text=text): self.assert_ec(text)
        for text in (
            "竞价药品支付标准有效期到期后纳入常规目录。",
            "对拟谈判药品的主规格、参照药品和限定支付范围提出意见。",
            "原目录内药品建议调整限定支付范围。",
            "商保专家确认是否参与该药品价格协商程序。",
        ):
            with self.subTest(text=text): self.assert_no_ec(text)

    def test_source_audit_drug_amount_and_settlement_anaphora(self):
        for text in (
            "对于调出目录的药品，继续监控一年，掌握其处方点评、使用量、使用金额等情况。",
            "审核医保用药行为，按规定结算和支付医保费用。",
            "核对药品目录落实情况，强化用药合理性和费用审核。",
        ):
            with self.subTest(text=text): self.assert_ec(text)
        self.assert_no_ec("审核一般医疗服务行为，按规定结算和支付医保费用。")

    def test_economic_relation_helpers_respect_carrier_and_repeat_calls(self):
        for text in (
            "药品临床使用经济性相关证据按编号归档。",
            "与同类药品相比价格偏高的报告按编号归档。",
        ):
            with self.subTest(text=text): self.assert_no_ec(text)
        record = make_record("商保专家对拟价格协商的药品开展测算并提出评估意见。")
        result = rule_support.v25.code_unit(record)
        rules_ec.revise(record, result)
        before = copy.deepcopy(result)
        rules_ec.revise(record, result)
        self.assertEqual(result, before)

    def test_pending_result_is_bitwise_unchanged(self):
        record = {"unit_text": None, "input_assessment": {"status": "text_problem", "reason": "missing"}}
        result = rule_support.v25.code_unit(record)
        before = copy.deepcopy(result)
        self.assertIs(rules_ec.revise(record, result), result)
        self.assertEqual(result, before)

    def test_v28_quotation_content_not_plain_negotiation_procedure(self):
        self.assert_ec("该药品按最低报价挂网。")
        text = "企业按程序提交报价。"
        self.assert_ec(text, paragraph_context=[{"paragraph_id":"p", "pages":[1],
            "text":text+"报价用于确定药品支付标准。"}])
        self.assert_no_ec("专家主要负责与药品企业进行现场价格协商。")
        self.assert_no_ec("企业按程序提交报价。")
        self.assert_no_ec("药品企业应提交办公设备报价。")

    def test_v28_price_volume_and_economic_principle(self):
        self.assert_ec("坚持量价挂钩，全面实行药品、医用耗材集中带量采购。")
        self.assert_ec("依据安全、有效、经济的用药原则优化药品目录。")
        self.assert_ec("评估该药物在真实医疗实践中的经济学效益。")
        self.assert_no_ec("办公设备采购坚持量价挂钩。")
        self.assert_no_ec("评估交通项目的经济学效益。")

    def test_v28_data_cutoff_and_program_name_are_not_economic_content(self):
        self.assert_no_ec("独家药品的认定、药品说明书、价格费用数据以截至2025年6月30日最新数据为准。")
        self.assert_no_ec("汇率、药品说明书、价格费用数据等信息均以2025年6月30日为准。")
        self.assert_no_ec("对抗癌药降价专项工作药品开展一般使用监测。")
        self.assert_ec("推动抗癌药降价并核算患者药费。")
        self.assert_ec("价格资料以2025年数据为准；同时评价该药品成本效果。")

    def test_v28_current_payment_relation_scope_and_macro_exclusion(self):
        self.assert_ec("谈判专家根据评估意见与企业开展谈判，确定全国统一的医保支付标准。")
        self.assert_ec("根据适应症变化确定新的医保支付标准。")
        self.assert_ec("市场环境变化的通过重新谈判确定支付标准后纳入常规目录管理。")
        text="开展DRG付费改革，合理确定支付标准。"
        self.assert_no_ec(text, paragraph_context=[{"paragraph_id":"p", "pages":[1],
            "text":text+"另行研究创新药除外支付。"}])
        self.assert_no_ec("谈判专家与企业确定医疗服务的全国统一医保支付标准。")

    def test_v28_actual_payment_responsibility_and_condition(self):
        for text in (
            "探索医疗服务与药品分开支付。",
            "推动商业健康保险产品扩大创新药支付范围。",
            "同通用名药品自动属于基本医疗保险基金支付范围。",
            "申报药品的支付范围与说明书的适应症或功能主治一致。",
            "发生公共卫生事件时可临时调整医保药品支付范围。",
            "建立药品质量风险防范和经济补偿机制。",
            "创新药应用病例可不纳入按病种付费范围，经审核后支付。",
            "合理使用创新药的病例，不适合按病种标准支付的可申报特例单议。",
        ):
            with self.subTest(text=text):self.assert_ec(text)
        for text in (
            "向商业保险推荐创新药目录供参考。",
            "主动申请调整支付范围的谈判药品。",
            "请反馈药品主规格、参照药品和支付范围。",
            "同通用名药品自动属于基本医疗保险基金支付范围的文件按编号归档。",
            "建立办公设备风险防范和经济补偿机制。",
        ):
            with self.subTest(text=text):self.assert_no_ec(text)

    def test_v28_verified_payment_parent_attaches_only_actual_child_condition(self):
        parent={"paragraph_id":"parent","pages":[1],
                "text":"参保人使用药品发生的费用，符合以下条件的可由医保基金支付："}
        text="（一）以疾病诊断或治疗为目的。"
        result=self.assert_ec(text,verified_parent_context=[parent])
        self.assertTrue(any(e.get('context_dependency') for e in ec_evidence(result)))
        self.assert_no_ec(text)
        self.assert_no_ec("请按时提交材料。",verified_parent_context=[parent])
        self.assert_no_ec(text,verified_parent_context=[{"paragraph_id":"p","pages":[1],
            "text":"药品研究应说明以下内容："}])

    def test_v28_verified_renewal_fund_scope_and_same_paragraph_reference(self):
        branch={"paragraph_id":"branch","pages":[1],"text":"规则二简易续约"}
        text="基金实际支出由医保部门统计。"
        self.assert_ec(text,verified_rule_branch_context=branch)
        self.assert_no_ec(text)
        self.assert_no_ec(text,verified_rule_branch_context=dict(branch,source_sha256='other'))
        self.assert_no_ec("药品材料按日期归档。",verified_rule_branch_context=branch)
        current="如协商不能达成一致，以医保方数据为准。"
        paragraph={"paragraph_id":"p","pages":[1],
            "text":"企业和医保方对基金实际支出存在分歧，允许补充提交资料并协商。"+current}
        self.assert_ec(current,verified_rule_branch_context=branch,paragraph_context=[paragraph])
        self.assert_no_ec(current,verified_rule_branch_context=branch)
        self.assert_no_ec(current,verified_rule_branch_context=branch,paragraph_context=[dict(paragraph,
            text="企业和医保方对基金实际支出存在分歧。另行讨论办公设备。"+current)])

    def test_v28_new_relations_are_idempotent_and_do_not_touch_other_dimensions(self):
        for text in ("推动商业保险扩大创新药支付范围。", "依据安全、有效、经济的用药原则。",
                     "专家负责与药品企业进行现场价格协商。", "药品说明书、价格费用以2025年6月30日为准。"):
            record=make_record(text);result=rule_support.v25.code_unit(record);before=copy.deepcopy(result)
            rules_ec.revise(record,result)
            for key in before.keys()-{'evidence','suppressions','review_flags'}:
                self.assertEqual(before[key],result[key])
            self.assertEqual([e for e in before['evidence'] if e['dimension']!='Ec'],
                             [e for e in result['evidence'] if e['dimension']!='Ec'])
            once=copy.deepcopy(result);rules_ec.revise(record,result);self.assertEqual(once,result)


if __name__ == "__main__":
    unittest.main()
