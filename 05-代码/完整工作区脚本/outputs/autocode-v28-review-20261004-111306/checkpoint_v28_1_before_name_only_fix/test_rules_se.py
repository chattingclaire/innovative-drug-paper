"""Synthetic v1.3 S/E development controls; not independent validation data."""
import copy
import hashlib
import unittest

import rule_support
import rules_se


def record(text, paragraph=None):
    return {"unit_text": text, "source_sha256": "synthetic-source",
            "paragraph_context": [{"paragraph_id": "p1", "pages": [1],
                                   "text": paragraph or text}]}


def revised(rec):
    result = rule_support.v25.code_unit(rec)
    before = copy.deepcopy(result)
    assert rules_se.revise(rec, result) is result
    assert result["labels"] == before["labels"]
    assert ([e for e in result["evidence"] if e["dimension"] not in {"S", "E"}] ==
            [e for e in before["evidence"] if e["dimension"] not in {"S", "E"}])
    for key in set(before) - {"evidence", "suppressions", "review_flags"}:
        assert result[key] == before[key], key
    return rule_support.rebuild(result)


class SafetyEffectivenessTest(unittest.TestCase):
    def check(self, text, dimension, expected, paragraph=None):
        result = revised(record(text, paragraph))
        self.assertEqual(result["labels"][dimension], expected, (text, result))
        for e in result["evidence"]:
            self.assertEqual(text[e["start"]:e["end"]], e["text"])
        return result

    def controls(self, dimension, positive, negative):
        for text in positive:
            with self.subTest(dimension=dimension, text=text):
                self.check(text, dimension, 1)
        for text in negative:
            with self.subTest(dimension=dimension, text=text):
                self.check(text, dimension, 0)

    def test_s_drug_harm_and_negation(self):
        self.controls("S", ["该药物尚无明显不良反应。", "该药物未发现肝毒性。",
                            "评价该药物的禁忌和副作用。", "预防用药错误。",
                            "应加强药物警戒。", "分析药物与食物的相互作用。"],
                      ["药品生产企业开展网络安全检查。", "医疗用毒性药品按类别登记。"])

    def test_s_explicit_content_requirement(self):
        self.controls("S", ["提交药品安全性数据。", "补充该药物安全信号分析。",
                            "该药物的安全性尚不明确。"],
                      ["药品安全性资料仅按日期归档。", "公示药品安全性资料。"])

    def test_s_quality_safety_basis(self):
        result = self.check("控制药品质量风险。", "S", 1)
        self.assertEqual(result["safety_quality_basis"], "quality_only")
        result = self.check("药品质量风险控制应加强。", "S", 1)
        self.assertEqual(result["safety_quality_basis"], "quality_only")
        result = self.check("评价药品质量安全和药物不良反应。", "S", 1)
        self.assertEqual(result["safety_quality_basis"], "quality_and_other")
        self.check("药品生产质量和工艺稳定性应符合规范。", "S", 0)

    def test_s_harm_control_vs_process_risk(self):
        self.controls("S", ["制定药物不良反应风险管理措施。",
                            "药品试验应实施患者安全风险控制。"],
                      ["药品试验风险控制措施确保质量管理活动的有效性。",
                       "药品申报服务器应加强风险控制。"])

    def test_s_abbreviations_local_object_and_archive(self):
        self.controls("S", ["报告药品ADR发生率。", "报告试验药物SAE严重程度。",
                            "评价药品SUSAR与停药的相关性。"],
                      ["药品申报已经完成。报告数据库AE发生率。",
                       "报告数据库SAE发生率。", "药品ADR报告文件仅按编号归档。",
                       "药品申报会议结束。汇总ADR发生率。"])

    def test_s_abbreviation_same_paragraph_definition(self):
        text = "汇总AE发生率。"
        result = self.check(text, "S", 1, "不良事件（AE）需要记录。" + text)
        self.assertTrue(any(e.get("context_dependency") for e in result["evidence"]))
        self.check(text, "S", 0, "严重不良事件（SAE）需要记录。" + text)
        self.check(text, "S", 0, "不良事件（AE）需要记录。" + text + text)

    def test_s_e_personnel_background(self):
        for dim in ("S", "E"):
            self.check("药品申报工作由具有安全性和有效性评价经验的人员承担。", dim, 0)
        self.check("具有药品疗效研究经验的专家出席会议。", "E", 0)
        self.check("专家应评价该药物安全性和疗效数据。", "S", 1)
        self.check("专家应评价该药物安全性和疗效数据。", "E", 1)

    def test_benefit_risk_both_sides_and_negation(self):
        for text in ["评估该药物的获益风险。", "药品获益-风险关系尚不能确定。"]:
            for dim in ("S", "E"):
                self.check(text, dim, 1)
        for dim in ("S", "E"):
            self.check("讨论获益风险。", dim, 0)
            self.check("药品申报信息系统的获益风险需要评估。", dim, 0)

    def test_combined_safe_effective_use_requirements(self):
        for text in ["药品应当安全有效。", "遵循安全、有效、经济的合理用药原则。",
                     "提交该药物的安全有效性证据。"]:
            for dim in ("S", "E"):
                self.check(text, dim, 1)

    def test_e_effects_endpoints_and_negative_result(self):
        self.controls("E", ["该药物疗效证据尚不充分。", "该药物未延长总生存期。",
                            "药品未达到最小有效剂量和最短有效疗程。",
                            "该药物的主要临床终点为客观缓解率。",
                            "药物试验以PFS和OS作为主要终点。"],
                      ["药品审批系统的OS需要更新。", "药品申报资料的有效期为一年。"])

    def test_e_evidence_requirement_and_design_only(self):
        self.controls("E", ["补充该药物有效性信息。", "提交该药物有效性数据。",
                            "评价该药物疗效证据质量。",
                            "补充药物临床获益的研究资料。"],
                      ["药物临床试验设计应采用随机分组。", "提交药物试验数据质量说明。",
                       "提交药代动力学参数。", "检查药品试验数据的有效性。"])

    def test_e_nonclinical_effects_and_toxicity(self):
        self.check("非临床研究显示药物具有抗肿瘤活性。", "E", 1)
        self.check("非临床研究显示药物具有肝毒性。", "S", 1)
        for dim in ("S", "E"):
            self.check("提交药物非临床研究材料目录。", dim, 0)

    def test_e_patient_outcome_and_guideline(self):
        self.controls("E", ["该药物改善患者生活质量。", "指南推荐使用该药物。",
                            "评价药物治疗后的患者报告结局。"],
                      ["药品企业应改善员工生活质量。", "药品生产企业更新文件管理指南。"])

    def test_e_representation_effect_link(self):
        self.check("药物试验人群代表性支持疗效判断。", "E", 1)
        self.check("药物试验应提高人群代表性。", "E", 0)

    def test_e_wrong_effect_objects(self):
        self.controls("E", [], ["药品试验质量管理活动的有效性需要审查。",
                                 "检查药品申报信息系统的有效性。",
                                 "药品管理部门评价培训干预效果。",
                                 "药品监管工作应提高行政效率。"])

    def test_explicit_non_drug_object_overrides_remote_drug_scope(self):
        self.controls("E", [], ["该药物用于治疗疾病；评价员工培训的有效性。",
                                 "评价外科手术对患者的治疗效果。",
                                 "药物资料已提交；评价外科手术对患者的治疗效果。",
                                 "评价患者心理干预的生活质量结果。"])
        self.controls("S", [], ["药品资料已提交；评价外科手术安全性。",
                                 "分析医疗质量（安全）不良事件的发生率。"])
        self.controls("E", ["药物临床研究中，评价患者的生活质量。",
                            "药物试验中，评价受试者的临床获益。",
                            "评价该药物与外科手术的治疗效果。",
                            "评价员工培训的有效性；同时分析该药物的疗效。",
                            "评价员工培训的有效性并分析该药物的疗效。"], [])

    def test_clinical_safety_data_and_dimension_lists_are_not_it_safety(self):
        self.check("药物临床试验期中分析评价临床数据的有效性和安全性。", "S", 1)
        self.check("药物临床试验应基于前期研究数据、风险控制开展评估。", "S", 1)
        self.check("药品申报资料包括经济性信息（含基金支出预算）、有效性信息、安全性信息。", "S", 1)
        self.check("药物试验应确保电子数据的可靠性、可追溯性和安全性。", "S", 0)

    def test_pharmacodynamic_model_and_pro_measurement_require_effect_link(self):
        self.controls("E", [], ["收集药物药代动力学和药效动力学参数支持试验设计。",
                                 "药物研究可用问卷收集患者报告结局数据。",
                                 "患者报告结局是患者自行填报的数据。"])
        self.controls("E", ["药物研究应评价治疗后的患者报告结局。",
                            "药物注册试验应开发患者报告结局评估终点。",
                            "药效动力学研究提示该药物具有临床获益。"], [])

    def test_titles_and_carrier_only(self):
        for dim in ("S", "E"):
            self.check("提交《药品安全性与有效性研究报告》。", dim, 0)
            self.check("归档药品安全性评价报告和有效性评价报告。", dim, 0)
        self.check("药品安全性更新报告应当每年提交一次。", "S", 0)
        self.check("落实仿制药质量和疗效一致性评价的相关鼓励政策。", "E", 0)
        self.check("登记药物非临床安全性评价研究机构。", "S", 0)

    def test_mixed_substantive_content_survives(self):
        self.controls("S", ["药品ADR报告文件仅按编号归档；另须报告药品ADR发生率。",
                            "归档药品安全性评价报告，并评价该药物不良反应。",
                            "提交该药物安全性数据，并对安全性资料保密。"], [])
        self.controls("E", ["审查药品试验质量管理活动的有效性；同时提交药物疗效数据。",
                            "提交药品疗效数据并归档有效性报告。"], [])

    def test_original_spans_after_normalization(self):
        self.check("报告药 品ＡＤＲ发生率及药物疗 效。", "S", 1)
        self.check("报告药 品ＡＤＲ发生率及药物疗 效。", "E", 1)

    def test_pending_is_unchanged(self):
        rec = {"unit_text": None}
        result = rule_support.v25.code_unit(rec)
        before = copy.deepcopy(result)
        rules_se.revise(rec, result)
        self.assertEqual(result, before)

    def test_v28_verified_scope_resolves_object_without_old_activation_words(self):
        cases = [("建议列出3级AE以及确定无关的ADR。", "S"),
                 ("增加安全性信息。", "S"), ("补充实效比较研究结果。", "E")]
        for text, dim in cases:
            rec = record(text)
            quote = "本指南主要用于支持药物监管决策。"
            rec["verified_object_scope"] = [{
                "kind": "drug_regulatory_research", "source_sha256": rec["source_sha256"],
                "source_hash_field": "source_sha256",
                "unit_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "text": quote, "text_sha256": hashlib.sha256(quote.encode()).hexdigest(),
                "locator": {"physical_pages": [1]}, "verification": "synthetic verified object"}]
            out = revised(rec)
            self.assertEqual(out["labels"][dim], 1, (text, out))
            self.assertTrue(any(e.get("context_dependency") for e in out["evidence"] if e["dimension"] == dim))
            self.check(text, dim, 0)
        bad = copy.deepcopy(rec)
        bad["verified_object_scope"][0]["source_sha256"] = "wrong-source"
        with self.assertRaises(AssertionError):
            revised(bad)

    def test_v28_benefit_comparison_and_vaccine_object(self):
        for dim in ("S", "E"):
            self.check("尚不能证明该疫苗获益明显大于潜在风险。", dim, 1)
            self.check("药品申报系统的获益风险需要评估。", dim, 0)
        self.check("药物试验参与者没有预期获益。", "E", 1)

    def test_v28_medication_errors_and_safety_controls(self):
        self.controls("S", ["审核处方剂量、用法是否正确。", "识别用药风险。",
                            "药品使用应进行过敏试验。", "注意电解质和辅料过量问题；本品应谨慎使用。",
                            "将易混淆药品分别存放。", "评估药物误吸或误服风险。",
                            "罕见病药品上市后应制定风险管控计划。"],
                      ["填写处方文件的编号。", "药物警戒工作经验相关说明。"])

    def test_v28_trial_safety_responsibility_and_urgent_protection(self):
        self.controls("S", ["药物试验负责人应保护试验参与者的权益和安全。",
                            "药物试验应消除对试验参与者的紧急危害。",
                            "紧急医学状态需要快速识别临床试验用药品。"],
                      ["药物试验负责人应具有安全性评价经验。"])

    def test_v28_explicit_drug_effect_relations(self):
        self.controls("E", ["评价该药物的治疗应答者。", "肿瘤耐药影响新药治疗。",
                            "利用模型估计药物暴露的效应。", "该药物新增适应症需要RCT支持。",
                            "试验药物显著优于安慰剂。", "用药后疼痛感较现有治疗改善。"],
                      ["药物研究规定统计软件版本。", "药品申报资料包括有效数据。"])

    def test_v28_guideline_inclusion_is_predicate_not_bare_title(self):
        self.check("纳入最新版《某病诊疗方案》的药品。", "E", 1)
        self.check("归档《某病诊疗方案》。", "E", 0)
        self.check("符合《基本医疗保险用药管理暂行办法》的药品。", "E", 0)

    def test_v28_disease_burden_not_drug_outcome(self):
        self.controls("E", [], ["该药拟用于疾病严重影响生活质量的患者。",
                                 "药品研发用于治疗或改善严重影响生活质量的慢性疾病。",
                                 "促进药品回归临床价值，发布管理指南。",
                                 "药学科参与会诊，发挥康复治疗对治疗效果的作用。"])
        self.check("该药物治疗改善患者生活质量。", "E", 1)

    def test_v28_report_management_and_enforcement_are_local_exclusions(self):
        self.check("药品编码管理档案汇集安全性相关报告。", "S", 0)
        self.check("药品检查发现问题应依法依规查处并采取风险控制措施。", "S", 0)
        self.check("药品编码管理档案汇集安全性报告；同时评估该药物不良反应。", "S", 1)
        self.check("本指南不能涵盖药品安全性资料准备的所有情况。", "S", 0)

    def test_v28_explicit_same_paragraph_references(self):
        text = "应修正判定结果。"
        self.check(text, "S", 1, "药物不良反应ADR需要确认判定依据。" + text)
        self.check(text, "S", 0, "药物研究需要核查财务判定依据。" + text)
        text = "该真实世界研究的结果与其他研究相近。"
        paragraph = "某药上市后开展有效性和安全性研究。" + text
        for dim in ("S", "E"):
            self.check(text, dim, 1, paragraph)
            self.check(text, dim, 0, "药品申报系统开展稳定性研究。" + text)

    def test_v28_formulation_effect_and_harm_relation(self):
        for dim in ("S", "E"):
            self.check("胶囊吞咽困难可能影响治疗并带来风险。", dim, 1)
            self.check("胶囊生产进度可能影响报批时间。", dim, 0)

    def test_v28_verified_data_risk_branch_is_not_drug_harm(self):
        text = "风险控制措施应保障受试者权益和安全。"
        rec = record(text)
        rec["verified_parent_context"] = [
            {"paragraph_id": "drug-scope", "text": "本指南包括药物治疗风险及数据可靠性风险。", "pages": [1]},
            {"paragraph_id": "data-subsection", "text": "2.数据可靠性的相关风险控制措施", "pages": [2]}]
        self.assertEqual(revised(rec)["labels"]["S"], 0)
        rec["unit_text"] = "药物毒性引起不良反应，应实施风险控制。"
        rec["paragraph_context"] = [{"paragraph_id": "p1", "text": rec["unit_text"], "pages": [2]}]
        self.assertEqual(revised(rec)["labels"]["S"], 1)

    def test_v28_mixed_treatment_parent_does_not_establish_drug_outcome(self):
        text = "评价治疗获益对患者生活质量的影响。"
        rec = record(text)
        rec["verified_parent_context"] = [{"paragraph_id": "intro", "pages": [1],
            "text": "收集患者观点和体验数据，评价治疗选择。"}]
        rec["verified_scope_qualifications_v28"] = [{"paragraph_id": "mixed", "pages": [1],
            "text": "患者的治疗选择包括超适应症用药、非处方药、替代和支持疗法。"}]
        self.assertEqual(revised(rec)["labels"]["E"], 0)
        rec["unit_text"] = "评价该药物治疗获益对患者生活质量的影响。"
        rec["paragraph_context"] = [{"paragraph_id": "p1", "text": rec["unit_text"], "pages": [1]}]
        self.assertEqual(revised(rec)["labels"]["E"], 1)


if __name__ == "__main__":
    unittest.main()
