"""Synthetic manual-behavior checks; never load the 41-case source/reference.

Expected values below come from the shared manual's relations, not a runtime's
rule hits. A failing case must be retained and reviewed; do not weaken its
expectation just to obtain a passing score. No model calls or legacy imports.
"""
from __future__ import annotations

from collections import Counter
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import dimensions
from evidence import DIMENSIONS, validate_decisions
from relations import RelationView
from source_packet import semantic_unit, PacketInterfaceError
from evaluate_development import EvaluationError, binary_metrics, evaluate, verify_seal


SOURCE_SHA = "a" * 64


def context(cid, kind, text, *, sequence=1, structure=None, metadata=None, column=None):
    location = {"paragraph_id": f"P-{sequence}", "sequence_index": sequence, "pages": []}
    if column is not None:
        location["column_index"] = column
    st = {**location, **(structure or {})}
    item = {"context_id": cid, "kind": kind, "text": text,
            "source_document": "/synthetic/source-policy.txt", "structure": st,
            "source_ref": {"sha256": SOURCE_SHA, "locator": copy.deepcopy(location)}}
    if metadata:
        item["source_ref"]["metadata"] = copy.deepcopy(metadata)
    return item


def record(text, contexts=(), identifier="synthetic-case"):
    return {"id": identifier, "text": text, "pages": [], "contexts": copy.deepcopy(list(contexts))}


def member(text, parent):
    contexts = [context("CTX-parent", "parent_paragraph", parent),
                context("CTX-current", "paragraph", text, sequence=2,
                        structure={"parent_context_id": "CTX-parent"})]
    return record(text, contexts)


def complete_list(text, members):
    ids = ["CTX-current", *[f"CTX-member-{index}" for index in range(len(members))]]
    contexts = [context("CTX-list", "ordered_list", "", structure={
        "child_groups": [{"position": "ordered_members", "ordered_context_ids": ids}]}),
        context("CTX-current", "ordered_members", text, sequence=1,
                structure={"parent_context_id": "CTX-list"})]
    contexts += [context(cid, "ordered_members", value, sequence=index + 2,
                         structure={"parent_context_id": "CTX-list"})
                 for index, (cid, value) in enumerate(zip(ids[1:], members))]
    return record(text, contexts)


def table_cell(text, header, *, column=1, unrelated_header="公平性"):
    contexts = [context("CTX-header", "table_header_cell", header, column=column),
                context("CTX-other-header", "table_header_cell", unrelated_header, column=column + 1),
                context("CTX-cell", "table_row_cell", text, sequence=2, column=column,
                        structure={"row_index_zero_based": 0})]
    return record(text, contexts)


def judge_raw(raw):
    before = copy.deepcopy(raw)
    unit = semantic_unit(raw)
    unit_before = copy.deepcopy(unit)
    view = RelationView(unit)
    decisions = dimensions.judge(view)
    validate_decisions(unit, decisions)
    if raw != before or unit != unit_before:
        raise AssertionError("Source input was mutated")
    return decisions, view


def values(decisions):
    return {dimension: decisions[dimension]["value"] for dimension in DIMENSIONS}


def semantic_signature(decisions):
    # Source citation IDs/paths may change as provenance; semantic outcome cannot.
    return {dimension: (decisions[dimension]["value"], decisions[dimension]["basis_path"])
            for dimension in DIMENSIONS}


def rename_context_ids(raw):
    out = copy.deepcopy(raw)
    mapping = {item["context_id"]: f"CTX-renamed-{number}"
               for number, item in enumerate(reversed(out["contexts"]))}
    def transform(value):
        if isinstance(value, dict):
            return {key: transform(child) for key, child in value.items()}
        if isinstance(value, list):
            return [transform(child) for child in value]
        if isinstance(value, str):
            return mapping.get(value, value)
        return value
    return transform(out)


class ManualBehaviorTests(unittest.TestCase):
    def assert_values(self, raw, **expected):
        decisions, view = judge_raw(raw)
        actual = values(decisions)
        for dimension, value in expected.items():
            self.assertEqual(actual[dimension], value, (raw["text"], dimension, decisions[dimension]))
        return decisions, view

    def test_id_context_order_and_source_path_are_not_classification_features(self):
        raw = member("（一）药品适应症发生重大变化。", "下列药品必须申报，方可申请调整支付范围：")
        raw["contexts"].append(context("CTX-unrelated", "source_fragment", "办公文件仅按编号归档。", sequence=9))
        baseline, _ = judge_raw(raw)
        changed = rename_context_ids(raw)
        changed["id"] = "not-a-development-fixture-identifier"
        changed["contexts"].reverse()
        for item in changed["contexts"]:
            item["source_document"] = "/elsewhere/renamed-policy-with-no-dimension-hint.md"
            item["source_ref"]["sha256"] = "b" * 64
        after, _ = judge_raw(changed)
        self.assertEqual(semantic_signature(baseline), semantic_signature(after))

    def test_record_order_does_not_leak_prior_case_state(self):
        rows = [record("本药出现不良反应。", identifier="A"),
                record("本药价格为126元。", identifier="B"),
                record("本药支付范围字段不能为空。", identifier="C")]
        first = {raw["id"]: semantic_signature(judge_raw(raw)[0]) for raw in rows}
        second = {raw["id"]: semantic_signature(judge_raw(raw)[0]) for raw in reversed(rows)}
        self.assertEqual(first, second)

    def test_result_fields_are_rejected_as_source_input(self):
        raw = record("本药出现不良反应。")
        raw["labels"] = {dimension: 1 for dimension in DIMENSIONS}
        with self.assertRaises(PacketInterfaceError):
            semantic_unit(raw)

    def test_missing_named_source_is_dimension_local(self):
        decisions, _ = self.assert_values(record("2024年实施创新药临床试验支持试点。本药出现不良反应。"),
                                        S=1, I=None, E=0, Ec=0, F=0)
        self.assertTrue(decisions["I"]["needed_material"])
        self.assertFalse(decisions["S"]["needed_material"])

    def test_same_version_named_mechanism_completes_support_only(self):
        title = "创新药临床试验支持试点工作方案"
        source = context("CTX-plan", "external_source",
                         "适用范围为1类创新药研发。申请人可获得研究方案反馈。审评在30个工作日内完成。",
                         metadata={"document_date": "2024-07-31", "source_title": title})
        self.assert_values(record("2024年实施创新药临床试验支持试点。本药出现不良反应。", [source]),
                           S=1, I=1, E=0, Ec=0, F=0)

    def test_newer_plan_cannot_resolve_historical_action(self):
        source = context("CTX-plan", "external_source",
                         "适用范围为1类创新药研发。申请人可获得研究方案反馈。",
                         metadata={"document_date": "2025-07-31", "source_title": "创新药临床试验支持试点工作方案"})
        self.assert_values(record("2024年实施创新药临床试验支持试点。本药出现不良反应。", [source]), S=1, I=None)

    def test_negation_is_preserved_without_erasing_risk_topic(self):
        raw = record("本药并未降低药物不良反应风险。")
        decisions, _ = self.assert_values(raw, S=1, E=0)
        proposition = decisions["S"]["current_proposition"]
        quote = proposition["text"] if isinstance(proposition, dict) else proposition
        self.assertEqual(quote, raw["text"])
        self.assertIn("并未", quote)

    def test_conditional_payment_does_not_infer_actual_change_or_fairness(self):
        self.assert_values(record("符合条件者可申请调整药品支付范围；未申报者不得调整。"),
                           Ec=1, F=0, E=0, I=0)

    def test_or_branch_with_need_gap_and_opportunity(self):
        self.assert_values(record("本药目标适应症尚无有效治疗药物，或者申报材料格式符合要求者，可申请优先审评。"),
                           E=1, F=1, I=0)

    def test_procedural_member_does_not_inherit_sibling_gap(self):
        raw = member("（二）申报材料格式符合要求。", "符合以下任一条件的药品，可申请优先审评：")
        raw["contexts"].append(context("CTX-sibling", "ordered_members", "（一）本药目标适应症尚无有效治疗药物。", sequence=3,
                                       structure={"parent_context_id": "CTX-parent"}))
        self.assert_values(raw, S=0, E=0, Ec=0, I=0, F=0)

    def test_parent_payment_condition_and_plain_indication_change(self):
        self.assert_values(member("（一）药品适应症发生重大变化。", "下列药品必须申报，方可申请调整支付范围："),
                           Ec=1, S=0, E=0, I=0, F=0)

    def test_pure_structure_does_not_collect_member_dimensions(self):
        self.assert_values(complete_list("包括下列内容：", ["（一）本药安全性证据。", "（二）本药价格信息。"]),
                           S=0, E=0, Ec=0, I=0, F=0)

    def test_substantive_information_head_uses_complete_members(self):
        self.assert_values(complete_list("应提供本药以下内容：", ["（一）本药安全性证据。", "（二）本药价格信息。"]),
                           S=1, Ec=1, E=0, I=0, F=0)

    def test_independent_substantive_clause_survives_structure_text(self):
        self.assert_values(complete_list("应评价本药安全性。包括下列内容：", ["（一）本药价格信息。"]), S=1)

    def test_table_number_binds_only_its_actual_column(self):
        self.assert_values(table_cell("126", "药品价格（元）"), Ec=1, S=0, E=0, I=0, F=0)

    def test_table_name_does_not_borrow_price_or_fairness_column(self):
        self.assert_values(table_cell("甲药", "药品名称", unrelated_header="药品价格和公平性"),
                           Ec=0, F=0, S=0, E=0, I=0)

    def test_existing_price_and_payment_content_verification(self):
        self.assert_values(record("申请人须核验本药已有支付标准和支付范围是否准确。"), Ec=1, F=0)

    def test_payment_field_presence_and_format_are_only_formal(self):
        self.assert_values(record("本药支付范围字段不能为空，字符格式应正确。"), Ec=0, F=0)

    def test_patient_affordability_contains_payment_ability_without_income_number(self):
        self.assert_values(record("应评价患者能否负担本药治疗费用。"), F=1, Ec=1)

    def test_cost_sharing_alone_is_not_patient_affordability(self):
        self.assert_values(record("本药费用的20%由患者自付。"), Ec=1, F=0)

    def test_general_equity_information_request(self):
        self.assert_values(record("请提供本药公平性证据。"), F=1)

    def test_equity_field_nonempty_is_not_information_request(self):
        self.assert_values(record("本药公平性字段不能为空。"), F=0)

    def test_routine_channel_has_no_automatic_equity(self):
        self.assert_values(record("医院与药店连通电子处方，保障患者凭处方取药。"), F=0)

    def test_shortage_object_and_receipt_deadline_do_not_create_priority(self):
        self.assert_values(record("临床急需短缺药品申报材料应在5日内签章并递交。"), F=0, I=0, E=0)

    def test_existing_program_identity_is_not_current_standard_or_opportunity(self):
        self.assert_values(record("本药已纳入优先审评程序。"), F=0, I=0, E=0, S=0, Ec=0)


class EvaluationIntegrityTests(unittest.TestCase):
    def test_reference_cannot_be_opened_without_seal(self):
        with patch.object(Path, "is_file", return_value=False), \
                patch.object(Path, "read_bytes", side_effect=AssertionError("No file bytes may be read before seal")), \
                patch.object(Path, "read_text", side_effect=AssertionError("No fixture may be read before seal")):
            with self.assertRaises(EvaluationError):
                evaluate(Path("/synthetic/fixture"), Path("/synthetic/predictions.jsonl"),
                         Path("/synthetic/seal.json"), Path("/synthetic/evaluation"))

    def test_changed_prediction_fails_before_fixture_or_reference_read(self):
        seal = {"status": "sealed_development_predictions", "prediction_path": "/synthetic/predictions.jsonl",
                "prediction_sha256": "0" * 64, "no_reference_read": True}
        reads = []
        def read_bytes(path):
            reads.append(str(path))
            if str(path) != "/synthetic/predictions.jsonl":
                raise AssertionError("Fixture/reference accessed before SHA verification")
            return b"changed predictions\n"
        with patch.object(Path, "is_file", return_value=True), \
                patch.object(Path, "read_text", return_value=json.dumps(seal)), \
                patch.object(Path, "read_bytes", autospec=True, side_effect=read_bytes):
            with self.assertRaises(EvaluationError):
                evaluate(Path("/synthetic/fixture"), Path("/synthetic/predictions.jsonl"),
                         Path("/synthetic/seal.json"), Path("/synthetic/evaluation"))
        self.assertEqual(reads, ["/synthetic/predictions.jsonl"])

    def test_all_null_denominators_and_kappa_are_explicit(self):
        metrics = binary_metrics(Counter(prediction_null=41, null_positive=20, null_negative=21), 41)
        self.assertEqual(metrics["all_source_denominator"], 41)
        self.assertEqual(metrics["all_source_unresolved_or_error_n"], 41)
        self.assertEqual(metrics["determined_denominator"], 0)
        self.assertEqual(metrics["coverage"], 0)
        for key in ("precision", "recall", "specificity", "F1", "balanced_accuracy", "cohens_kappa"):
            self.assertIsNone(metrics[key])

    def test_abstention_does_not_disappear_from_all_source_errors(self):
        metrics = binary_metrics(Counter(TP=1, TN=1, prediction_null=1, null_positive=1), 3)
        self.assertEqual(metrics["determined_accuracy"], 1)
        self.assertEqual(metrics["all_source_correct_rate"], 2 / 3)
        self.assertEqual(metrics["all_source_unresolved_or_error_n"], 1)
        self.assertEqual(metrics["recall_all_reference_positives_with_null_unresolved"], 1 / 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
