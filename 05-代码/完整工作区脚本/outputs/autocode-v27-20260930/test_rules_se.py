"""Synthetic v1.3 S/E development controls; not independent validation data."""
import copy
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


if __name__ == "__main__":
    unittest.main()
