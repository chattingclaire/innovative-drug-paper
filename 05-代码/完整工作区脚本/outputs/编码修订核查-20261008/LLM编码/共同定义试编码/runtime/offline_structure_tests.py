"""Small constructed contract tests; no CLI/model calls or semantic evaluation."""

import ast
import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "候选09-分步判读" / "runtime"


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


with mock.patch.object(subprocess, "run", side_effect=AssertionError("offline test forbids process/CLI calls")):
    validator = load_module("common_pilot_validator", "validate_binary_output.py")
    runner = load_module("common_pilot_runner", "run_production_v32.py")

SCHEMA = json.loads((HERE / "output_schema_codex_compatible.json").read_text(encoding="utf-8"))


def constructed_fixture():
    text = "报告不良反应，评价疗效、药费和患者可负担性，为创新研发提供技术指导。"
    packet = {"rows": [
        {"id": "constructed-positive", "text": text, "contexts": []},
        {"id": "constructed-quality-content", "text": "说明纯度检验方法。", "contexts": []},
    ]}
    quotes = {"S": "不良反应", "E": "疗效", "Ec": "药费", "I": "创新研发", "F": "患者可负担性"}
    output = {
        "protocol_version": "COMMON-5D-20261009",
        "execution_version": "LLM-common-definition-pilot",
        "release_stage": "development_labels",
        "rows": [
            {
                "id": "constructed-positive",
                "labels": {dim: 1 for dim in validator.DIMS},
                "dimension_reasons": {dim: "构造例仅检查字段与引用契约。" for dim in validator.DIMS},
                "evidence": [{"dimension": dim, "source": "unit", "quote": quote} for dim, quote in quotes.items()],
                "fairness_subtypes": ["patient_affordability"],
                "innovation_subtypes": ["research_support"],
                "safety_quality_basis": "no_quality_basis",
                "quality_content_without_safety": False,
            },
            {
                "id": "constructed-quality-content",
                "labels": {dim: 0 for dim in validator.DIMS},
                "dimension_reasons": {dim: "构造例仅检查字段与引用契约。" for dim in validator.DIMS},
                "evidence": [],
                "fairness_subtypes": [],
                "innovation_subtypes": [],
                "safety_quality_basis": "no_quality_basis",
                "quality_content_without_safety": True,
            },
        ],
        "issue_records": [],
    }
    return packet, output


class OfflineContractTests(unittest.TestCase):
    def setUp(self):
        guard = mock.patch.object(subprocess, "run", side_effect=AssertionError("offline test forbids process/CLI calls"))
        guard.start()
        self.addCleanup(guard.stop)
        self.packet, self.output = constructed_fixture()

    def test_valid_records_and_schema_contract(self):
        self.assertEqual(validator.validate(self.packet, self.output), [])
        self.output["rows"][1]["quality_content_without_safety"] = False
        self.assertEqual(validator.validate(self.packet, self.output), [])
        for field in ("protocol_version", "execution_version", "release_stage"):
            self.assertEqual(SCHEMA["properties"][field]["const"], self.output[field])
        row = SCHEMA["properties"]["rows"]["items"]
        self.assertEqual(set(row["properties"]["fairness_subtypes"]["items"]["enum"]), validator.F_SUBTYPES)
        self.assertEqual(set(row["properties"]["innovation_subtypes"]["items"]["enum"]), validator.I_SUBTYPES)
        self.assertEqual(set(row["properties"]["safety_quality_basis"]["enum"]), validator.S_BASES)
        self.assertEqual(row["properties"]["quality_content_without_safety"]["type"], "boolean")
        self.assertIn("quality_content_without_safety", row["required"])
        self.assertFalse(row["additionalProperties"])

    def test_wrong_versions_rejected(self):
        for field, old in (("protocol_version", "CAL-5D-20260926-v1.3"), ("execution_version", "LLM-binary-v32"), ("release_stage", "final_binary_labels")):
            with self.subTest(field=field):
                output = copy.deepcopy(self.output)
                output[field] = old
                self.assertIn(f"root:{field}", validator.validate(self.packet, output))

    def test_fabricated_quote_rejected(self):
        self.output["rows"][0]["evidence"][0]["quote"] = "本输入不存在的伪造引文"
        errors = validator.validate(self.packet, self.output)
        self.assertTrue(any("nonliteral_quote" in error for error in errors))
        self.assertTrue(any("S:missing_literal_unit_evidence" in error for error in errors))

    def test_F_zero_with_subtype_rejected(self):
        self.output["rows"][1]["fairness_subtypes"] = ["patient_affordability"]
        self.assertIn("constructed-quality-content:fairness_subtypes_label_conflict", validator.validate(self.packet, self.output))

    def test_tool_events_rejected(self):
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
            {"type": "turn.completed"},
        ]
        encode = lambda items: "\n".join(json.dumps(item) for item in items)
        self.assertEqual(runner.event_audit(encode(events))["tool_or_unknown_item_event_count"], 0)
        events.append({"type": "item.started", "item": {"type": "command_execution", "command": "synthetic-only-not-executed"}})
        self.assertGreater(runner.event_audit(encode(events))["tool_or_unknown_item_event_count"], 0)

    def test_quality_content_boolean_constraints(self):
        for value in (True, "false"):
            with self.subTest(invalid_S_one_value=value):
                output = copy.deepcopy(self.output)
                output["rows"][0]["quality_content_without_safety"] = value
                self.assertTrue(any("quality_content_without_safety" in error for error in validator.validate(self.packet, output)))

    def test_transport_and_selection_preserved_except_versions(self):
        source = (SOURCE / "run_production_v32.py").read_text(encoding="utf-8")
        for old, new in (("CAL-5D-20260926-v1.3", "COMMON-5D-20261009"), ("LLM-binary-v32", "LLM-common-definition-pilot"), ("final_binary_labels", "development_labels")):
            source = source.replace(old, new)
        actual = (HERE / "run_production_v32.py").read_text(encoding="utf-8")
        self.assertEqual(ast.dump(ast.parse(source)), ast.dump(ast.parse(actual)))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OfflineContractTests))
    report = {
        "purpose": "constructed offline structure/literal/event contract checks only",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "passed": result.wasSuccessful(),
        "CLI_or_model_calls": 0,
        "external_process_calls_blocked_by_mock": True,
        "semantic_correctness_verified": False,
        "json_schema_engine_validation_run": False,
        "schema_constants_and_new_field_contract_checked": True,
        "historical_labels_metrics_or_protected_pool_read": False,
        "transport_selection_runner_AST_equal_after_only_version_substitution": True,
    }
    (HERE / "offline_test_result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
