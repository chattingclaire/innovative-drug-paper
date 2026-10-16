import unittest

import policy_coding_v26 as frozen_v26
import policy_coding_v26_2 as fixed_v26


def record(text):
    return {"unit_text": text, "input_assessment": {"status": "not_assessed"}}


class TitleScopeFixTest(unittest.TestCase):
    def assert_title_only_not_triggered(self, text, dimension):
        # The frozen candidate reproduces the regression that motivated this
        # bounded derivative; the title-scoped candidate must remove it.
        self.assertEqual(frozen_v26.code_unit(record(text))["labels"][dimension], 1)
        fixed = fixed_v26.code_unit(record(text))
        self.assertEqual(fixed["labels"][dimension], 0)
        self.assertEqual(fixed["derived_from_candidate_sha256"], fixed_v26.DERIVED_FROM_SHA256)

    def test_research_support_in_title_is_not_I(self):
        self.assert_title_only_not_triggered("现发布《支持创新药的研发办法》。", "I")

    def test_product_modification_in_title_is_not_I(self):
        self.assert_title_only_not_triggered("现发布《改良给药途径指导原则》。", "I")

    def test_treatment_gap_in_title_is_not_F(self):
        self.assert_title_only_not_triggered(
            "现发布《药品用于缺乏有效标准治疗手段的患者的研究指南》。", "F")

    def test_title_does_not_block_independent_outside_relations(self):
        text = ("现发布《支持创新药的研发办法》，并明确对创新药研发予以支持；"
                "该药物用于缺乏有效标准治疗手段的患者。")
        fixed = fixed_v26.code_unit(record(text))
        self.assertEqual(fixed["labels"]["I"], 1)
        self.assertEqual(fixed["labels"]["F"], 1)
        positive = [e for e in fixed["evidence"] if e["rule"].startswith("V26_")]
        self.assertTrue(any(e["dimension"] == "I" and "对创新药研发予以支持" in e["text"] for e in positive))
        self.assertTrue(any(e["dimension"] == "F" and "缺乏有效标准治疗手段" in e["text"] for e in positive))

    def test_real_anchors_across_title_keep_original_offset_span(self):
        text = ("为促进药品创新发展，按照《药品试验数据保护办法》"
                "完善药品试验数据保护制度。")
        fixed = fixed_v26.code_unit(record(text))
        self.assertEqual(fixed["labels"]["I"], 1)
        evidence = [e for e in fixed["evidence"]
                    if e["rule"] == "V26_I_data_protection_support_relation"]
        self.assertEqual(len(evidence), 1)
        item = evidence[0]
        self.assertIn("促进药品创新发展", item["text"])
        self.assertIn("《药品试验数据保护办法》", item["text"])
        self.assertIn("完善药品试验数据保护制度", item["text"])
        self.assertEqual(text[item["start"]:item["end"]], item["text"])


if __name__ == "__main__":
    unittest.main()
