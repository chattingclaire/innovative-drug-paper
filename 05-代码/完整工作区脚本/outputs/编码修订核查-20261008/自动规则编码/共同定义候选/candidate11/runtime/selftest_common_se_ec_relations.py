"""Exactly 14 self-constructed concept pairs; no corpus or model outputs.

These are implementation checks, not a validation sample or accuracy estimate.
Each pair changes a conceptually material condition under the common definition.
"""

import unittest

from common_se_ec_relations import (
    inspect_economics,
    inspect_quality_content,
    inspect_safety,
    mask_document_titles,
)


# text, verified drug-object scope, expected S, expected Ec
PAIRS = [
    ("ordinary quality / explicit harm", ("该药纯度检验方法需要补充说明。", False, False, False),
     ("应监测该药杂质引起的严重不良反应。", False, True, False)),
    ("quality safety / use safety", ("应强化药品质量安全管理。", False, False, False),
     ("应评价药品质量问题危及患者生命的风险。", False, True, False)),
    ("document title / actual safety evidence", ("参照《药品安全性评价与不良反应监测指南》办理申报。", False, False, False),
     ("参照《申报指南》补充该药的长期安全性评价数据。", False, True, False)),
    ("adverse-effect column / negative assertion", ("不良反应栏目。", False, False, False),
     ("长期随访尚未发现严重不良反应。", False, True, False)),
    ("general production safety / pharmacovigilance", ("药品生产车间应加强生产安全管理。", False, False, False),
     ("上市许可持有人应实施药物警戒计划。", False, True, False)),
    ("fund risk / drug safety risk", ("该药申报材料需要说明基金风险监测流程。", False, False, False),
     ("应对该药开展安全风险监测。", False, True, False)),
    ("evaluation heading / evidence requirement with verified object", ("安全性评价。", True, False, False),
     ("应补充安全性评价资料。", True, True, False)),
    ("report template / substantive evaluation", ("申请人应提供药品安全性评价报告模板。", False, False, False),
     ("申请人应提供药品安全性评价报告及长期毒性研究数据。", False, True, False)),
    ("negotiation result / qualitative price requirement", ("药品价格谈判成功后纳入常规目录。", False, False, False),
     ("要求说明该药价格合理性。", False, False, True)),
    ("directory outcome / actual payment standard", ("协商失败的药品本次不纳入医保目录。", False, False, False),
     ("该药的医保支付标准调整为统一定额。", False, False, True)),
    ("eligibility to apply / actual payment range", ("符合条件的药品可申请调整医保支付范围。", False, False, False),
     ("该药医保支付范围仅限住院治疗。", False, False, True)),
    ("existing standard as process object / cost responsibility", ("既有医保支付标准作为续约申请的名称字段。", False, False, False),
     ("该药治疗费用由患者承担。", False, False, True)),
    ("fundability column / fundability evaluation", ("基金可负担性栏目。", True, False, False),
     ("要求评估该药的基金可负担性。", False, False, True)),
    ("administrative service fee / cost-health relationship", ("应降低药品申报系统服务费。", False, False, False),
     ("应比较该药治疗成本与健康收益。", False, False, True)),
]


class ConceptPairTests(unittest.TestCase):
    def test_fourteen_concept_pairs(self):
        self.assertEqual(len(PAIRS), 14)
        for name, negative, positive in PAIRS:
            for text, scope, safety, economics in (negative, positive):
                with self.subTest(concept=name, text=text):
                    s = inspect_safety(text, drug_scope=scope)
                    ec = inspect_economics(text, drug_scope=scope)
                    self.assertEqual(bool(s), safety)
                    self.assertEqual(bool(ec), economics)
                    # All emitted spans must reproduce the raw Unicode text.
                    for record in s + ec + inspect_quality_content(text):
                        self.assertEqual(set(record), {"start", "end", "quote", "kind", "subtype", "basis"})
                        self.assertEqual(text[record["start"]:record["end"]], record["quote"])
                        self.assertGreater(record["end"], record["start"])
                    masked = mask_document_titles(text)
                    self.assertEqual(len(text), len(masked))
                    if "《" in text:
                        begin, end = text.index("《"), text.index("》") + 1
                        self.assertEqual(masked[begin:end], " " * (end - begin))
                    if name == "ordinary quality / explicit harm":
                        marks = inspect_quality_content(text)
                        self.assertTrue(marks)
                        expected = "quality_with_safety_relation" if safety else "quality_without_safety_relation"
                        self.assertEqual(marks[0]["subtype"], expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
