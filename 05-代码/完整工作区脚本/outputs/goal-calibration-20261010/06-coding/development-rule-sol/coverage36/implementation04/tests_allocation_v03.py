"""Constructed permission/grant grammar contrasts, declared before v03 run."""
import unittest
from tests_behavior import record, judge_raw


class AllocationGrammarTests(unittest.TestCase):
    def f(self, text, expected):
        decisions, _ = judge_raw(record(text))
        self.assertEqual(decisions['F']['value'], expected, decisions['F'])

    def test_time_adjunct_between_permission_and_application(self):
        self.f('本药目标疾病尚无有效防治手段，申请人可以在早期临床研究阶段，且通常不晚于关键研究开始前申请适用研发支持程序。', 1)

    def test_stage_adjunct_with_negative_permission_keeps_topic(self):
        self.f('本药目标疾病尚无有效治疗药物，申请人不得在完成关键临床研究以后申请适用优先审评程序。', 1)

    def test_current_direct_grant_to_domestic_option_gap(self):
        self.f('对于临床急需境外已上市境内未上市的罕见病药品，受理后直接纳入优先审评程序。', 1)

    def test_restriction_of_current_priority_grant(self):
        self.f('临床急需境外已上市境内未上市药品不予纳入优先审评程序。', 1)

    def test_existing_priority_identity_is_not_current_grant(self):
        self.f('本药为临床急需境外已上市境内未上市药品，已纳入优先审评程序。', 0)

    def test_other_subject_inside_adjunct_cannot_take_need(self):
        self.f('本药目标疾病尚无有效防治手段，允许在资料核对以后，另一药品申请适用优先审评程序。', 0)

    def test_deadline_and_submission_do_not_grant_opportunity(self):
        self.f('本药目标疾病尚无有效防治手段，申请人可以在5日以内提交申请材料。', 0)

    def test_publication_purpose_keeps_its_own_gate(self):
        self.f('为规范临床急需短缺药品优先审评，制定本程序。', 0)


if __name__ == '__main__':
    unittest.main()
