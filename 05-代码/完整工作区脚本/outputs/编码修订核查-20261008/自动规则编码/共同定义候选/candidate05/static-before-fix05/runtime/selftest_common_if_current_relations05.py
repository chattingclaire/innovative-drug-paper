"""Invented current-relation fixtures; real literal authentication, no gold labels."""
import copy
import json
import tempfile
from pathlib import Path

from common_if_relations import inspect_fairness, inspect_innovation
from common_if_current_relations05 import inspect_current_relations
from selftest_common_if_extensions03 import prose


def main():
    checks = []

    def check(group, name, record, dimension, expected):
        if isinstance(record, str):
            record = {"unit_text": record}
        before = copy.deepcopy(record)
        text = record["unit_text"]
        existing = (inspect_innovation if dimension == "I" else inspect_fairness)(text)
        current = [e for e in inspect_current_relations(record) if e["dimension"] == dimension]
        assert bool(existing or current) is expected, (name, existing, current)
        assert record == before
        for e in existing:
            assert text[e["start"]:e["end"]] == e["quote"]
        for e in current:
            assert text[e["start"]:e["end"]] == e["text"]
            for a in e.get("current_relation_anchors", []):
                assert text[a["start"]:a["end"]] == a["text"]
            dep = e.get("context_dependency")
            if dep:
                assert dep["source_authentication"]["literal_reproduced_in_current_runtime"]
                paragraph = next(p for p in record["paragraph_context"] if p["paragraph_id"] == dep["paragraph_id"])
                assert paragraph["text"][dep["antecedent_start_in_paragraph"]:dep["antecedent_end_in_paragraph"]] == dep["antecedent_text"]
        checks.append({"group": group, "name": name, "constructed_text": text,
                       "dimension": dimension, "expected_attention": expected,
                       "actual_relation_present": bool(existing or current),
                       "new_component_rule_names": [e["rule"] for e in current],
                       "source_bound_dependencies": sum(bool(e.get("context_dependency")) for e in current),
                       "source_offsets_valid": True})

    with tempfile.TemporaryDirectory(prefix="common-current05-invented-") as tmp:
        root = Path(tmp)
        check(1, "explicit_review_channel", "重点创新药品种将纳入优先审评通道。", "I", True)
        channel = "重点创新药品种将依申请纳入18日通道。"
        check(1, "numeric_channel_with_bound_scope", prose(root / "channel", channel,
              prefix="主管机构优化药品审评审批机制。"), "I", True)
        check(1, "numeric_channel_without_scope", channel, "I", False)
        check(1, "numeric_channel_wrong_scope", prose(root / "channel-wrong", channel,
              prefix="主管机构优化物流配送机制。"), "I", False)
        check(1, "channel_without_innovative_category", prose(root / "channel-no-category",
              "药品将依申请纳入18日通道。", prefix="主管机构优化药品审评审批机制。"), "I", False)
        check(1, "only_management_object", "重点创新药品种列入管理统计表。", "I", False)
        check(1, "nomination_only", "建议提名重点创新药品种进入优先审评通道。", "I", False)

        check(2, "explicit_drug_innovation_evaluation",
              "通过分析国产原研创新情况，进行药品的创新性评价。", "I", True)
        continuation = "开展创新性评价，应当说明创新价值判断。"
        check(2, "bound_same_evaluation_continuation", prose(root / "evaluation", continuation,
              prefix="通过分析药品原创性，进行药品的创新性评价。"), "I", True)
        check(2, "continuation_without_drug_object", continuation, "I", False)
        check(2, "different_preceding_topic", prose(root / "evaluation-wrong", continuation,
              prefix="对药品开展质量评价。"), "I", False)
        check(2, "intervening_topic_break", prose(root / "evaluation-distant", continuation,
              prefix="进行药品的创新性评价。设备管理工作另行安排。"), "I", False)
        check(2, "column_format_only", "填写药品创新性评价栏目格式。", "I", False)
        check(2, "evaluation_named_in_column_change", "开展药品创新性评价栏目格式调整。", "I", False)
        forged = prose(root / "evaluation-forged", continuation,
                       prefix="进行药品的创新性评价。")
        forged["paragraph_context"][0]["text"] = "伪造的药品创新性评价。" + continuation
        forged["llm_v29_shared_context"]["paragraph_context"] = copy.deepcopy(forged["paragraph_context"])
        try:
            inspect_current_relations(forged)
        except ValueError:
            checks.append({"group": 2, "name": "forged_same_paragraph_scope", "authentication_error": True})
        else:
            raise AssertionError("forged paragraph accepted")

        check(3, "explicit_class_definition", "本规范的儿童专用创新药是指，专为儿童开发的1类创新药。", "I", True)
        check(3, "definition_word_order", "本规范的专用创新药定义为针对特定治疗需要开发的 1 类创新药。", "I", True)
        check(3, "category_identity_only", "儿童专用创新药应按时提交材料。", "I", False)
        check(3, "definition_without_category", "本规范中的创新药是指拟推荐进入评审名单的药品。", "I", False)
        check(3, "ordinary_number_only", "本规范所称药品是指1类药品。", "I", False)
        check(3, "title_definition_only", "文件标题中的创新药是指1类创新药。", "I", False)

        check(4, "need_before_directory", "根据临床用药需求动态调整用药目录。", "F", True)
        check(4, "directory_before_need", "用药目录应当根据临床用药需求变化实行动态调整。", "F", True)
        check(4, "multiple_explicit_bases", "用药目录根据临床用药需求变化、药品供应条件和相关目录调整情况实行动态调整。", "F", True)
        check(4, "ordinary_directory_update", "用药目录根据年度工作安排实行动态调整。", "F", False)
        check(4, "directory_format_only", "用药目录根据临床用药需求变化进行上传格式更新。", "F", False)
        check(4, "embedded_adjustment_is_not_current_action", "用药目录根据临床用药需求变化和相关目录调整情况填报数据。", "F", False)

        check(5, "urgent_drug_guarantee", "保障抢救药品可用，确保急危重患者优先救治。", "F", True)
        check(5, "coordinated_equipment_and_drug", "保障各单元抢救设备和药品可用，确保急危重患者优先救治。", "F", True)
        check(5, "equipment_only", "保障抢救设备可用，确保急危重患者优先救治。", "F", False)
        check(5, "availability_without_need_link", "保障抢救药品可用，确保患者及时登记资料。", "F", False)
        check(5, "ordinary_drug_availability", "保障药品可用。", "F", False)
        check(5, "unmet_need_rd_is_not_F", "创新药研发用于填补临床未满足需求，可以申请优先审评程序。", "F", False)
        check(5, "separate_sentence_does_not_inherit", "保障抢救药品可用。另行确保急危重患者优先救治。", "F", False)

    print(json.dumps({"passed": True, "group_n": 5, "check_n": len(checks), "checks": checks,
                      "real_policy_units_executed": 0, "reference_labels_loaded": False,
                      "authenticators_mocked": False, "full_pipeline_executed": False,
                      "interpretation": "Invented component tests only; not a real-case correction or validity estimate."},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
