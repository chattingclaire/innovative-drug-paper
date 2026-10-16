"""Evaluator protocol checks on generated artificial data only.

Never opens development-reference36-v11/reference.jsonl or coverage01 outputs.
All artificial files live under this coverage36 directory and remain reviewable.
"""
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("coverage36_evaluator", ROOT / "evaluate_development.py")
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)
DIMS = evaluator.DIMENSIONS


def write(path, obj, *, lines=False):
    path.write_bytes(evaluator.json_bytes(obj, lines=lines))
    return evaluator.sha_file(path)


class ArtificialAttempt:
    def __init__(self, *, modifications=None, missing=(), global_failure=False, record_failures=(), technical=False, source_contexts=()):
        self.root = Path(tempfile.mkdtemp(prefix="evaluator-artificial-", dir=ROOT))
        self.fixture = self.root / "fixture"
        self.run = self.root / "run"
        self.code = self.root / "code"
        for directory in (self.fixture, self.run, self.code):
            directory.mkdir()
        sources = [{"id": f"SYN-{i}", "text": "人工构造测试材料", "contexts": copy.deepcopy(list(source_contexts)),
                    "source_page_attachments": [{"mime_type": "image/png", "page_number": 1, "artificial": True}],
                    "source_image_attachments": [{"mime_type": "image/jpeg", "artificial": True}]}
                   for i in range(36)]
        refs = [{"id": row["id"], "labels": {d: i % 2 for d in DIMS},
                 "reference_role": "artificial_test_only",
                 "evidence_A": {d: {"reason": "synthetic A", "current_quote": row["text"]} for d in DIMS},
                 "evidence_B": {d: {"reason": "synthetic B", "current_quote": row["text"]} for d in DIMS}}
                for i, row in enumerate(sources)]
        predictions = []
        errors = []
        for i, row in enumerate(sources):
            if i in missing:
                if not global_failure:
                    errors.append({"id": row["id"], "type": "ArtificialMissingPrediction"})
                continue
            labels = {d: (modifications or {}).get((i, d), i % 2) for d in DIMS}
            record_errors = [{"id": row["id"], "type": "ArtificialFailure"}] if i in record_failures else []
            errors.extend(record_errors)
            predictions.append({"id": row["id"], "labels": labels if not record_errors else None,
                                "decisions": {d: {"value": labels[d], "reason": "synthetic rule"} for d in DIMS}
                                if not record_errors else None,
                                "implementation_errors": record_errors, "relation_traces": []})
        if global_failure:
            errors.append({"type": "ArtificialGlobalFailure"})
        successful = not errors
        self.inputs = {}
        for name, obj, lines in (("source.jsonl", sources, True), ("reference.jsonl", refs, True)):
            self.inputs[name] = {"path": str(self.fixture / name), "sha256": write(self.fixture / name, obj, lines=lines)}
        (self.fixture / "manual.md").write_text("人工构造手册，仅测试评估协议。\n")
        self.inputs["manual.md"] = {"path": str(self.fixture / "manual.md"), "sha256": evaluator.sha_file(self.fixture / "manual.md")}
        manifest = {"n": 36, "dimension_judgments": 180, "outputs": list(self.inputs.values())}
        manifest_hash = write(self.fixture / "manifest.json", manifest)
        code = []
        for name in sorted(evaluator.INFERENCE_FILES):
            (self.code / name).write_text("# Synthetic protocol fixture; never executed.\n")
            code.append({"path": str(self.code / name), "sha256": evaluator.sha_file(self.code / name)})
        bindings = {"runtime_version": evaluator.RUNTIME_VERSION, "implementation_files": code,
                    "source_path": str(self.fixture / "source.jsonl"), "source_sha256": self.inputs["source.jsonl"]["sha256"],
                    "manual_path": str(self.fixture / "manual.md"), "manual_sha256": self.inputs["manual.md"]["sha256"],
                    "fixture_manifest_path": str(self.fixture / "manifest.json"), "fixture_manifest_sha256": manifest_hash}
        freeze_hash = write(self.run / "freeze.json", {"status": "frozen_before_coder_import_and_inference",
                            "expected_n": 36, "reference_input": None, "no_legacy_runtime_import": True, **bindings})
        self.pred = self.run / "predictions.jsonl"
        pred_hash = write(self.pred, predictions, lines=True)
        technical_binding = {"technical_diagnostics_path": None, "technical_diagnostics_sha256": None,
                             "technical_diagnostics_n": 0, "technical_failure_dimension_n": 0}
        if technical:
            diagnostics = []
            for p in predictions:
                for d in DIMS:
                    failed = bool(global_failure or p["implementation_errors"] or p["decisions"] is None)
                    diagnostics.append({"id": p["id"], "dimension": d, "technical_failure": failed,
                                        "comparison_eligible": False, "status": "technical_failure" if failed else "retained_rule_decision"})
            technical_path = self.run / "technical-diagnostics.jsonl"
            technical_binding = {"technical_diagnostics_path": str(technical_path),
                                 "technical_diagnostics_sha256": write(technical_path, diagnostics, lines=True),
                                 "technical_diagnostics_n": len(diagnostics),
                                 "technical_failure_dimension_n": sum(x["technical_failure"] for x in diagnostics)}
        execution_hash = write(self.run / "execution.json", {"status": "completed" if successful else "failed_development_attempt",
                               "runtime_version": evaluator.RUNTIME_VERSION, "attempted_record_n": 0 if global_failure and not predictions else 36,
                               "output_record_n": len(predictions), "implementation_errors": errors,
                               "reference_was_input": False, "read_paths": [], "comparison_eligible": successful, **technical_binding})
        self.seal = self.run / "seal.json"
        self.seal_object = {"status": "sealed_development_predictions" if successful else "sealed_failed_development_attempt",
                            "sealed_at_utc": "2026-10-10T00:00:00Z", "prediction_path": str(self.pred), "prediction_sha256": pred_hash,
                            "prediction_n": len(predictions), "decision_n": sum(len(p["labels"]) for p in predictions if isinstance(p["labels"], dict)),
                            "freeze_sha256": freeze_hash, "execution_sha256": execution_hash, "no_reference_read": True,
                            "complete": successful, "comparison_eligible": successful, "implementation_error_n": len(errors),
                            **bindings, **technical_binding}
        write(self.seal, self.seal_object)
        self.output = self.root / "evaluation"

    def evaluate(self):
        return evaluator.evaluate(self.fixture, self.pred, self.seal, self.output)

    def comparison(self):
        return [json.loads(line) for line in (self.output / "comparison180.jsonl").read_text().splitlines()]


class CoverageEvaluatorTests(unittest.TestCase):
    def test_complete180_and_AB_evidence_and_source_images_retained(self):
        case = ArtificialAttempt()
        metrics = case.evaluate()
        self.assertEqual(metrics["all36"]["exact_complete_vector_n"], 36)
        self.assertEqual(metrics["all180"]["confusion_determined"], {"TP": 90, "FP": 0, "FN": 0, "TN": 90})
        rows = case.comparison()
        self.assertEqual(len(rows), 180)
        self.assertEqual(rows[0]["reference_decision"]["evidence_A"]["reason"], "synthetic A")
        self.assertEqual(rows[0]["reference_decision"]["evidence_B"]["reason"], "synthetic B")
        self.assertEqual(rows[0]["source_record"]["source_image_attachments"][0]["mime_type"], "image/jpeg")
        self.assertEqual(rows[0]["source_image_attachments"][0]["mime_type"], "image/jpeg")
        self.assertEqual(rows[0]["source_page_attachments"][0]["mime_type"], "image/png")

    def test_null_context_text_does_not_break_error_report(self):
        case = ArtificialAttempt(modifications={(1, "Ec"): 0}, source_contexts=({"text": None}, {"text": "实质语境"}))
        metrics = case.evaluate()
        self.assertEqual(metrics["all180"]["misprediction_n"], 1)
        row = next(r for r in case.comparison() if r["id"] == "SYN-1" and r["dimension"] == "Ec")
        self.assertIsNone(row["source_contexts"][0]["text"])

    def test_FP_FN_count_and_full_denominator(self):
        case = ArtificialAttempt(modifications={(0, "S"): 1, (1, "Ec"): 0})
        metrics = case.evaluate()
        self.assertEqual(metrics["all180"]["confusion_determined"], {"TP": 89, "FP": 1, "FN": 1, "TN": 89})
        self.assertEqual(metrics["all180"]["misprediction_n"], 2)
        self.assertEqual(metrics["all36"]["exact_complete_vector_n"], 34)
        self.assertEqual(len((case.output / "mispredictions.jsonl").read_text().splitlines()), 2)

    def test_rule_null_does_not_become_zero_or_technical_failure(self):
        case = ArtificialAttempt(modifications={(1, "I"): None})
        metrics = case.evaluate()
        self.assertEqual(metrics["all180"]["prediction_null_n"], 1)
        self.assertEqual(metrics["all180"]["prediction_unknown_n"], 1)
        self.assertEqual(metrics["all180"]["technical_failure_n"], 0)
        self.assertEqual(metrics["all180"]["determined_denominator"], 179)
        row = next(r for r in case.comparison() if r["id"] == "SYN-1" and r["dimension"] == "I")
        self.assertEqual(row["comparison"], "null_unresolved")
        self.assertEqual(metrics["per_dimension"]["I"]["recall_all_reference_positives_with_null_unresolved"], 17 / 18)

    def test_NA_is_distinct_from_unknown_and_failure(self):
        case = ArtificialAttempt(modifications={(0, "F"): "NA", (1, "I"): "unknown"})
        metrics = case.evaluate()
        self.assertEqual(metrics["all180"]["prediction_NA_n"], 1)
        self.assertEqual(metrics["all180"]["prediction_unknown_n"], 1)
        self.assertEqual(metrics["all180"]["technical_failure_n"], 0)
        self.assertEqual(metrics["all180"]["determined_denominator"], 178)

    def test_failed_record_has5_technical_slots_no_rule_null(self):
        case = ArtificialAttempt(record_failures=(0,), technical=True)
        metrics = case.evaluate()
        self.assertFalse(metrics["comparison_eligible"])
        self.assertFalse(metrics["metrics_valid_for_complete_rule_run"])
        self.assertEqual(metrics["all180"]["technical_failure_n"], 5)
        self.assertEqual(metrics["all180"]["prediction_null_n"], 0)
        self.assertEqual(metrics["all180"]["determined_denominator"], 175)
        self.assertEqual(metrics["all36"]["technical_failure_record_n"], 1)
        self.assertEqual(len(case.comparison()), 180)

    def test_zero_predictions_global_failure_retains180_material(self):
        case = ArtificialAttempt(missing=tuple(range(36)), global_failure=True)
        metrics = case.evaluate()
        self.assertEqual(metrics["all180"]["technical_failure_n"], 180)
        self.assertEqual(metrics["all180"]["prediction_null_n"], 0)
        self.assertEqual(metrics["all180"]["coverage"], 0)
        self.assertEqual(metrics["all180"]["determined_denominator"], 0)
        self.assertIsNone(metrics["all180"]["F1"])
        self.assertIsNone(metrics["all180"]["cohens_kappa"])
        self.assertEqual(len(case.comparison()), 180)
        self.assertTrue(all(r["prediction"] is None and r["prediction_record"] is None for r in case.comparison()))

    def test_missing_prediction_retains_source_slot(self):
        case = ArtificialAttempt(missing=(35,))
        metrics = case.evaluate()
        self.assertEqual(metrics["all180"]["technical_failure_n"], 5)
        self.assertEqual(metrics["all180"]["determined_denominator"], 175)
        self.assertEqual(metrics["all36"]["unresolved_record_n"], 1)
        self.assertEqual(len(case.comparison()), 180)

    def test_seal_absence_prevents_reference_read(self):
        case = ArtificialAttempt()
        case.seal.unlink()
        with patch.object(Path, "read_bytes", side_effect=AssertionError("no byte read without seal")):
            with self.assertRaises(evaluator.EvaluationError):
                case.evaluate()

    def test_prediction_tampering_prevents_reference_read(self):
        case = ArtificialAttempt()
        case.pred.write_bytes(b"changed\n")
        self.assert_ref_unread(case, "Predictions changed after sealing")

    def test_technical_tampering_prevents_reference_read(self):
        case = ArtificialAttempt(record_failures=(0,), technical=True)
        (case.run / "technical-diagnostics.jsonl").write_bytes(b"changed\n")
        self.assert_ref_unread(case, "Technical diagnostics changed after sealing")

    def test_code_tampering_prevents_reference_read(self):
        case = ArtificialAttempt()
        (case.code / "relations.py").write_bytes(b"changed\n")
        self.assert_ref_unread(case, "Frozen inference code changed")

    def test_source_tampering_prevents_reference_read(self):
        case = ArtificialAttempt()
        (case.fixture / "source.jsonl").write_bytes(b"changed\n")
        self.assert_ref_unread(case, "Independent source SHA mismatch")

    def assert_ref_unread(self, case, pattern):
        original = Path.read_bytes
        actual_reference = (case.fixture / "reference.jsonl").resolve()
        def guarded(path):
            self.assertNotEqual(path.resolve(), actual_reference, "reference read before sealed inputs validated")
            return original(path)
        with patch.object(Path, "read_bytes", autospec=True, side_effect=guarded):
            with self.assertRaisesRegex(evaluator.EvaluationError, pattern):
                case.evaluate()

    def test_overwrite_is_refused(self):
        case = ArtificialAttempt()
        case.evaluate()
        with self.assertRaisesRegex(evaluator.EvaluationError, "never overwrite"):
            case.evaluate()

    def test_output_cannot_change_sealed_or_fixture_inputs(self):
        case = ArtificialAttempt()
        with self.assertRaisesRegex(evaluator.EvaluationError, "outside the fixture"):
            evaluator.evaluate(case.fixture, case.pred, case.seal, case.fixture / "evaluation")

    def test_pe1_kappa_remains_undefined(self):
        self.assertIsNone(evaluator.binary_metrics(Counter(TN=36), 36)["cohens_kappa"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
