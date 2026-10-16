import unittest

from policy_coding_v26 import code_unit, v25


def record(text, paragraph=None, assessment=None):
    value = {"unit_text": text, "input_assessment": assessment or {"status": "not_assessed"}}
    if paragraph is not None:
        value["paragraph_context"] = [{"paragraph_id": "synthetic-p1", "text": paragraph, "pages": []}]
    return value


class CandidateIFTest(unittest.TestCase):
    def test_delivery_route_is_specific_modification(self):
        text = "改良给药途径是重要改良方式之一。"
        paragraph = text + "比如开发皮下制剂、口服制剂，以改善患者治疗便利性。"
        out = code_unit(record(text, paragraph))
        self.assertEqual(out["labels"]["I"], 1)
        self.assertIn("attribute", out["innovation_subtypes"])

    def test_data_protection_has_explicit_innovation_support_relation(self):
        text = "为促进药品创新发展，完善药品试验数据保护制度。"
        out = code_unit(record(text))
        self.assertEqual(out["labels"]["I"], 1)
        self.assertIn("research_support", out["innovation_subtypes"])

    def test_research_support_not_limited_by_character_window(self):
        text = "鼓励通过长期稳定的公共数据平台、专业技术服务和跨区域协作机制，支持创新药研发。"
        out = code_unit(record(text))
        self.assertEqual(out["labels"]["I"], 1)

    def test_research_support_word_order_and_negative_variants(self):
        for text in (
            "支持创新药的研发。",
            "对创新药研发予以支持。",
            "取消对创新药研发的支持。",
            "不再支持创新药研发。",
        ):
            with self.subTest(text=text):
                self.assertEqual(code_unit(record(text))["labels"]["I"], 1)

    def test_unrelated_support_object_does_not_cross_link(self):
        out = code_unit(record("创新药研发工作已经完成，并支持建设办公场所。"))
        self.assertEqual(out["labels"]["I"], 0)

    def test_specific_formulation_feature_improvement(self):
        text = "在药物设计时，应有针对性地改善制剂特征。"
        out = code_unit(record(text))
        self.assertEqual(out["labels"]["I"], 1)

    def test_plain_new_strength_or_dosage_form_is_not_innovation(self):
        out = code_unit(record("开发不同强度片剂及其他规格或剂型。", "药物开发中，开发不同强度片剂及其他规格或剂型。"))
        self.assertEqual(out["labels"]["I"], 0)
        self.assertTrue(any(x["rule"] == "V26_I_product_modification_relation" for x in out["v26_if_suppressions"]))

    def test_data_protection_archive_without_innovation_goal_is_not_I(self):
        out = code_unit(record("将药品试验数据保护文件按编号归档。"))
        self.assertEqual(out["labels"]["I"], 0)
        self.assertTrue(any(x["rule"] == "V26_I_data_protection_support_relation" for x in out["v26_if_suppressions"]))

    def test_non_drug_information_system_innovation_is_suppressed_locally(self):
        negative = code_unit(record("药品申报工作采用创新性的信息管理系统。"))
        self.assertEqual(negative["labels"]["I"], 0)
        self.assertTrue(any(x["rule"] == "V26_I_non_drug_system_object" for x in negative["v26_if_suppressions"]))
        mixed = code_unit(record("药品申报工作采用创新性的信息管理系统，同时评价药物新作用机制。"))
        self.assertEqual(mixed["labels"]["I"], 1)
        self.assertTrue(any(e["dimension"] == "I" and e["text"] == "新作用机制" for e in mixed["evidence"]))

    def test_modified_treatment_gap_order(self):
        text = "该药物用于缺乏有效标准治疗手段的难治疾病。"
        out = code_unit(record(text))
        self.assertEqual(out["labels"]["F"], 1)
        self.assertIn("access", out["fairness_subtypes"])

    def test_data_accessibility_is_suppressed_locally(self):
        negative = code_unit(record("药品申报管理中的数据可及性需要提升。"))
        self.assertEqual(negative["labels"]["F"], 0)
        self.assertTrue(any(x["rule"] == "V26_F_data_access_object" for x in negative["v26_if_suppressions"]))
        mixed = code_unit(record("药品申报管理中的数据可及性需要提升，同时改善药品可及性。"))
        self.assertEqual(mixed["labels"]["F"], 1)
        self.assertTrue(any(e["dimension"] == "F" and e["text"] == "可及性" for e in mixed["evidence"]))

    def test_no_drug_to_treat_is_gap(self):
        out = code_unit(record("晚期无药可治的肿瘤患者存在急迫治疗需求。"))
        self.assertEqual(out["labels"]["F"], 1)

    def test_opportunity_requires_preexisting_gap(self):
        negative = code_unit(record("入组受试者均能接受试验治疗，以观察疗效。", "本药物研究中，入组受试者均能接受试验治疗，以观察疗效。"))
        self.assertEqual(negative["labels"]["F"], 0)
        self.assertTrue(any(x["reason"] == "preexisting_treatment_gap_missing" for x in negative["v26_if_suppressions"]))
        positive = code_unit(record("晚期无药可治的患者均能接受试验药物治疗，得到潜在治疗机会。"))
        self.assertEqual(positive["labels"]["F"], 1)
        rules = {e["rule"] for e in positive["evidence"] if e["dimension"] == "F"}
        self.assertIn("V26_F_treatment_opportunity_from_gap", rules)

    def test_explicit_drug_use_obstacle_allows_modifiers_and_coordination(self):
        text = "老年患者在打开药品包装、准确量取及使用药物时遇到困难。"
        out = code_unit(record(text))
        self.assertEqual(out["labels"]["F"], 1)
        self.assertIn("clinical_management", out["fairness_subtypes"])

    def test_convenience_without_obstacle_is_not_F(self):
        out = code_unit(record("建议改进药品包装以提高老年患者用药便利性。"))
        self.assertEqual(out["labels"]["F"], 0)

    def test_anaphor_requires_same_paragraph_complexity_antecedent(self):
        text = "此类用药行为无法避免，因此需预判多重用药问题并改善制剂特征。"
        paragraph = "多种药物同时使用，包括不同药物需要在不同时间服用，或者采用不同的给药途径。" + text
        positive = code_unit(record(text, paragraph))
        self.assertEqual(positive["labels"]["F"], 1)
        negative = code_unit(record(text))
        self.assertEqual(negative["labels"]["F"], 0)
        self.assertTrue(any(x["reason"] == "same_paragraph_complexity_antecedent_missing" for x in negative["v26_if_suppressions"]))

    def test_context_insufficient_positive_stays_pending(self):
        text = "使患者获得试验药物治疗机会。"
        out = code_unit(record(text, assessment={"status": "context_insufficient", "reason": "缺少说明患者原有治疗缺口的上位条件"}))
        self.assertEqual(set(out["labels"].values()), {None})
        self.assertEqual(out["judgement_status"], "undetermined")

    def test_S_E_Ec_are_byte_for_byte_decision_invariant(self):
        cases = [
            "改良给药途径是重要改良方式之一。",
            "为促进药品创新发展，完善药品试验数据保护制度。",
            "该药物用于缺乏有效标准治疗手段的难治疾病。",
            "老年患者在打开药品包装、准确量取及使用药物时遇到困难。",
        ]
        for text in cases:
            old = v25.code_unit(record(text))
            new = code_unit(record(text))
            self.assertEqual({d: new["labels"][d] for d in ("S", "E", "Ec")},
                             {d: old["labels"][d] for d in ("S", "E", "Ec")})


if __name__ == "__main__":
    unittest.main()
