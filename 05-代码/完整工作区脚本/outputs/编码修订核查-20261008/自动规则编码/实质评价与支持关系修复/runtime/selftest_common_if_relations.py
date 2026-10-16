"""Twelve invented constructions; no real policy units, IDs or reference labels.

Run only this bounded grammar check, never a full-corpus coding command.
"""

from common_if_relations import inspect_fairness, inspect_innovation


CASES = (
    {
        "name": "uncertain_novelty_and_new_mechanism",
        "text": "本药尚不能确定是否具有技术新颖性；本药采用全新作用机制。",
        "I": {"novelty_attribute"}, "F": set(),
    },
    {
        "name": "declared_substantive_improvement",
        "text": "拟研发改良剂型以改善本药给药方式。",
        "I": {"substantive_improvement"}, "F": set(),
    },
    {
        "name": "innovative_research_safety_guidance",
        "text": "为创新药物早期研发安排专家并提供安全风险技术指导。",
        "I": {"targeted_rnd_support"}, "F": set(),
    },
    {
        "name": "qualification_comparison",
        "text": "创新药申请专门支持资格须较既有药物具有明确技术创新优势。",
        "I": {"qualification_comparison"}, "F": set(),
    },
    {
        "name": "ordinary_change_rights_and_safety_duties",
        "text": "该药适应症发生重大变化；本药变更剂型；创新药应更新安全报告；药物专利保护期限为十年。",
        "I": set(), "F": set(),
    },
    {
        "name": "title_and_other_object_do_not_leak",
        "text": "对《创新药原创性评价》文件的字体作统一规定；药品管理软件具有新颖性；另需评估该药原创性。",
        "I": {"novelty_attribute"}, "F": set(), "scope": True,
        "forbidden_quotes": ("字体", "软件", "《"),
    },
    {
        "name": "affordability_not_cost_responsibility",
        "text": "评估患者对该药的可负担性；患者由医保按比例分担药费。",
        "I": set(), "F": {"patient_affordability"},
        "forbidden_quotes": ("分担",),
    },
    {
        "name": "need_allocation_and_guarantee_gap",
        "text": "根据基层临床用药需求配置药品并补足库存；另需填补用药保障缺口。",
        "I": set(), "F": {"needs_based_allocation", "guarantee_gap"},
    },
    {
        "name": "region_condition_causes_treatment_barrier",
        "text": "农村缺乏监测条件导致当地患者难以获得该药治疗。",
        "I": set(), "F": {"population_region_access_barrier"},
    },
    {
        "name": "opportunity_difference_and_equity_goal",
        "text": "评价不同收入患者获得药物治疗的机会差异，并改善药品保障公平性。",
        "I": set(), "F": {"population_region_access_barrier", "equity_goal_or_evaluation"},
    },
    {
        "name": "ordinary_access_management_and_consultation",
        "text": "药品由患者自付三成；连通电子处方取药通道；临床管理难度较高；为行动不便者上门提供用药咨询。",
        "I": set(), "F": set(), "scope": True,
    },
    {
        "name": "mixed_metadata_wrong_object_and_actual_relations",
        "text": "患者可负担性报告只须保密；器械创新性需要评估；为创新药研发提供技术指导，器械使用机会按需保障；按治疗需要保障患者持续获得药品。",
        "I": {"targeted_rnd_support"}, "F": {"needs_based_allocation", "needs_based_guarantee"},
        "scope": True, "forbidden_quotes": ("保密", "器械"),
    },
)


def main():
    assert len(CASES) == 12
    relations = 0
    for case in CASES:
        text = case["text"]
        for dimension, inspect in (("I", inspect_innovation), ("F", inspect_fairness)):
            result = inspect(text, drug_scope=case.get("scope", False))
            actual = {r["kind"] for r in result}
            assert actual == case[dimension], (case["name"], dimension, actual, case[dimension], result)
            assert result == inspect(text, drug_scope=case.get("scope", False))
            for relation in result:
                assert set(relation) == {"start", "end", "quote", "kind", "subtype", "basis"}
                assert 0 <= relation["start"] < relation["end"] <= len(text)
                assert text[relation["start"]:relation["end"]] == relation["quote"]
                assert relation["basis"] and relation["subtype"]
                assert not any(word in relation["quote"] for word in case.get("forbidden_quotes", ()))
                relations += 1
        print("PASS", case["name"])
    print("12 invented construction checks passed; exact offsets and deterministic outputs checked; relations", relations)


if __name__ == "__main__":
    main()
