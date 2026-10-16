"""Synthetic expectations for implementation02; never load the real fixture.

Expectations declared before execution:
* freeze and read guard precede every coder import, using frozen source bytes;
* missing seal fields or changed predictions fail before fixture/reference reads;
* changed freeze/execution/seal bindings cannot complete a comparison;
* evaluation outputs cannot be inside a fixture or sealed run;
* complete failed attempts retain 41 records and 205 technical slots, while
  technical failures and rule-null decisions stay distinct and yield no metrics;
* partial attempts never fabricate 205 slots; successful shapes and A/B evidence
  remain visible without choosing one AI reference provider.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from evaluate_development import EvaluationError, REQUIRED_SEAL_FIELDS, evaluate


HERE = Path(__file__).resolve().parent
WORK = HERE / "boundary-synthetic-work"
DIMS = ("S", "E", "Ec", "I", "F")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        WORK.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="boundary-", dir=WORK)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def make_run(self, mode="success", count=41):
        fixture, code, runs = (self.base / name for name in ("synthetic-fixture", "synthetic-code", "synthetic-runs"))
        for path in (fixture, code, runs):
            path.mkdir()
        source, manual, reference = (fixture / name for name in ("source.jsonl", "manual.md", "reference.jsonl"))
        rows = [{"id": f"synthetic-{n}", "text": f"boundary synthetic {n}", "pages": [], "contexts": []}
                for n in range(count)]
        source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        manual.write_text("Synthetic boundary manual, no real policy text.\n", encoding="utf-8")
        refs = [{"id": row["id"], "labels": {d: 0 for d in DIMS},
                 "reference_role": "AI_consensus_development_only",
                 "evidence_A": {d: {"reason": "AI A synthetic reason", "path": "A path", "current_quote": row["text"],
                                    "contexts_used": [], "image_sources_used": [], "name": "AI A"} for d in DIMS},
                 "evidence_B": {d: {"reason": "AI B synthetic reason", "path": "B path", "current_quote": row["text"],
                                    "contexts_used": [], "image_sources_used": [], "name": "AI B"} for d in DIMS}}
                for row in rows]
        reference.write_text("".join(json.dumps(row) + "\n" for row in refs), encoding="utf-8")
        manifest = fixture / "manifest.json"
        write_json(manifest, {"n": 41, "dimension_judgments": 205,
                             "outputs": [{"path": str(path), "sha256": digest(path)}
                                         for path in (source, manual, reference)]})
        shutil.copyfile(HERE / "runner.py", code / "runner.py")
        packet = (
            "import json\nfrom pathlib import Path\n"
            "def load_fixture(source, manifest):\n"
            "    return [json.loads(line) for line in Path(source).read_text().splitlines() if line]\n"
            "def semantic_unit(row):\n    return dict(row)\n"
        )
        if mode == "blocked_import":
            packet += "Path(" + repr(str(reference)) + ").read_text()\n"
        (code / "source_packet.py").write_text(packet, encoding="utf-8")
        (code / "evidence.py").write_text(
            "DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')\n"
            "def validate_decisions(unit, decisions):\n"
            "    if set(decisions) != set(DIMENSIONS): raise ValueError('synthetic invalid dimensions')\n",
            encoding="utf-8")
        (code / "relations.py").write_text(
            "class RelationView:\n"
            "    def __init__(self, unit):\n        self.unit = unit\n        self.material_requests = []\n"
            "    def traces(self):\n        return []\n", encoding="utf-8")
        (code / "dimensions.py").write_text(
            "from evidence import DIMENSIONS\nfrom dataclasses import dataclass\n"
            "@dataclass\nclass SyntheticMarker:\n    value: int = 0\n"
            "def judge(view):\n"
            "    mode = " + repr(mode) + "\n"
            "    if mode == 'fail_all' or (mode == 'mixed_failure' and view.unit['id'] == 'synthetic-0'):\n"
            "        raise ValueError('synthetic grammar implementation failure')\n"
            "    return {d: {'value': None if d == 'Ec' and view.unit['id'] == 'synthetic-1' else 0,\n"
            "                'reason': 'synthetic rule material null' if d == 'Ec' and view.unit['id'] == 'synthetic-1' else 'synthetic rule'}\n"
            "            for d in DIMENSIONS}\n", encoding="utf-8")
        out = runs / "run01"
        completed = subprocess.run(
            [sys.executable, "-B", str(code / "runner.py"), "--source", str(source), "--manual", str(manual),
             "--manifest", str(manifest), "--source-sha256", digest(source), "--expected-n", "41",
             "--approved-output-root", str(runs), "--out", str(out)],
            cwd=code, capture_output=True, text=True, check=False)
        self.assertIn(completed.returncode, (0, 2), completed.stdout + completed.stderr)
        return {"fixture": fixture, "out": out, "code": code, "process": completed,
                "predictions": out / "predictions.jsonl", "seal": out / "seal.json",
                "reference": reference, "evaluation": self.base / "synthetic-evaluation"}

    def compare(self, run, output=None):
        return evaluate(run["fixture"], run["predictions"], run["seal"], output or run["evaluation"])

    def tracked_reads(self):
        reads = []
        original = Path.read_bytes
        def track(path):
            reads.append(path.resolve())
            return original(path)
        return reads, patch.object(Path, "read_bytes", autospec=True, side_effect=track)

    def test_guard_blocks_reference_at_coder_import_after_freeze(self):
        run = self.make_run("blocked_import")
        self.assertEqual(run["process"].returncode, 2)
        freeze = json.loads((run["out"] / "freeze.json").read_text())
        self.assertEqual(freeze["status"], "frozen_before_coder_import_and_inference")
        execution = json.loads((run["out"] / "execution.json").read_text())
        self.assertIn("development reference is forbidden", execution["implementation_errors"][0]["message"])
        self.assertEqual(execution["implementation_errors"][0]["type"], "PermissionError")
        self.assertNotIn(str(run["reference"]), execution["read_paths"])
        self.assertEqual(read_jsonl(run["predictions"]), [])

    def test_success_shape_preserves_all41_null_and_both_ai_evidence(self):
        run = self.make_run()
        self.assertEqual(run["process"].returncode, 0, run["process"].stderr)
        predictions_before = run["predictions"].read_bytes()
        metrics = self.compare(run)
        self.assertEqual(metrics["source_records"], 41)
        self.assertEqual(metrics["dimension_decisions"], 205)
        self.assertEqual(metrics["all41"]["error_or_unresolved_record_n"], 1)
        self.assertEqual(metrics["per_dimension"]["Ec"]["determined_denominator"], 40)
        self.assertEqual(metrics["per_dimension"]["Ec"]["prediction_null_n"], 1)
        comparison = read_jsonl(run["evaluation"] / "comparison205.jsonl")
        self.assertEqual(len(comparison), 205)
        first = comparison[0]
        self.assertEqual(first["reference_reason"], {"evidence_A": "AI A synthetic reason", "evidence_B": "AI B synthetic reason"})
        self.assertEqual(first["reference_decision"]["evidence_A"]["name"], "AI A")
        self.assertEqual(first["reference_decision"]["evidence_B"]["name"], "AI B")
        self.assertEqual(first["reference_decision"]["reference_role"], "AI_consensus_development_only")
        self.assertEqual(run["predictions"].read_bytes(), predictions_before)

    def test_each_missing_required_seal_field_refuses_before_other_bytes(self):
        run = self.make_run()
        seal = json.loads(run["seal"].read_text())
        for field in sorted(REQUIRED_SEAL_FIELDS):
            with self.subTest(field=field):
                altered = dict(seal)
                del altered[field]
                write_json(run["seal"], altered)
                reads, tracker = self.tracked_reads()
                with tracker, self.assertRaises(EvaluationError):
                    self.compare(run)
                self.assertEqual(reads, [run["seal"]])
        self.assertFalse(run["evaluation"].exists())

    def test_changed_prediction_refuses_before_freeze_fixture_or_reference(self):
        run = self.make_run()
        with run["predictions"].open("ab") as handle:
            handle.write(b" ")
        reads, tracker = self.tracked_reads()
        with tracker, self.assertRaisesRegex(EvaluationError, "Predictions changed after sealing"):
            self.compare(run)
        self.assertEqual(reads, [run["seal"], run["predictions"]])

    def test_changed_freeze_refuses_before_fixture_or_reference(self):
        run = self.make_run()
        (run["out"] / "freeze.json").write_text("{}\n")
        reads, tracker = self.tracked_reads()
        with tracker, self.assertRaisesRegex(EvaluationError, "Sealed freeze changed"):
            self.compare(run)
        self.assertNotIn(run["reference"], reads)
        self.assertNotIn(run["fixture"] / "source.jsonl", reads)

    def test_changed_execution_refuses_before_fixture_or_reference(self):
        run = self.make_run()
        (run["out"] / "execution.json").write_text("{}\n")
        reads, tracker = self.tracked_reads()
        with tracker, self.assertRaisesRegex(EvaluationError, "Sealed execution changed"):
            self.compare(run)
        self.assertNotIn(run["reference"], reads)

    def test_nested_evaluation_directories_refuse_before_any_reads(self):
        run = self.make_run()
        for target in (run["fixture"], run["fixture"] / "nested", run["out"], run["out"] / "nested"):
            with self.subTest(target=target):
                reads, tracker = self.tracked_reads()
                with tracker, self.assertRaisesRegex(EvaluationError, "outside the fixture"):
                    self.compare(run, target)
                self.assertEqual(reads, [])
                if target.name == "nested":
                    self.assertFalse(target.exists())

    def test_seal_mutation_during_evaluation_refuses_completion(self):
        run = self.make_run()
        original = Path.read_bytes
        def mutate_on_reference(path):
            payload = original(path)
            if path == run["reference"]:
                seal = json.loads(original(run["seal"]))
                seal["sealed_at_utc"] = "changed during synthetic evaluation"
                write_json(run["seal"], seal)
            return payload
        with patch.object(Path, "read_bytes", autospec=True, side_effect=mutate_on_reference), \
                self.assertRaisesRegex(EvaluationError, "Run seal changed during evaluation"):
            self.compare(run)
        self.assertFalse(run["evaluation"].exists())

    def test_mixed_failure_retains205_and_rule_null_independently(self):
        run = self.make_run("mixed_failure")
        self.assertEqual(run["process"].returncode, 2)
        predictions = read_jsonl(run["predictions"])
        self.assertEqual(len(predictions), 41)
        self.assertIsNone(predictions[0]["labels"])
        self.assertIsNone(predictions[0]["decisions"])
        technical = read_jsonl(run["out"] / "technical-diagnostics.jsonl")
        self.assertEqual(len(technical), 205)
        self.assertEqual(technical[0]["source_text"], "boundary synthetic 0")
        self.assertEqual(technical[0]["source_contexts"], [])
        self.assertEqual(sum(row["technical_failure"] for row in technical), 5)
        self.assertTrue(all(not row["rules_null"] for row in technical if row["technical_failure"]))
        rule_null = next(row for row in technical if row["id"] == "synthetic-1" and row["dimension"] == "Ec")
        self.assertTrue(rule_null["rules_null"])
        self.assertFalse(rule_null["technical_failure"])
        self.assertEqual(rule_null["status"], "retained_rule_decision")
        seal = json.loads(run["seal"].read_text())
        self.assertEqual(seal["technical_diagnostics_n"], 205)
        self.assertEqual(seal["technical_diagnostics_sha256"], digest(run["out"] / "technical-diagnostics.jsonl"))
        self.assertFalse(seal["comparison_eligible"])
        reads, tracker = self.tracked_reads()
        with tracker, self.assertRaisesRegex(EvaluationError, "diagnostics only"):
            self.compare(run)
        self.assertEqual(reads, [run["seal"]])
        self.assertFalse(run["evaluation"].exists())

    def test_all_failed_records_remain205_technical_without_rule_nulls(self):
        run = self.make_run("fail_all")
        technical = read_jsonl(run["out"] / "technical-diagnostics.jsonl")
        self.assertEqual(len(technical), 205)
        self.assertTrue(all(row["technical_failure"] and not row["rules_null"] for row in technical))
        self.assertEqual(len(read_jsonl(run["predictions"])), 41)

    def test_partial_attempt_does_not_fabricate205_slots(self):
        run = self.make_run(count=40)
        self.assertEqual(run["process"].returncode, 2)
        seal = json.loads(run["seal"].read_text())
        self.assertEqual(seal["prediction_n"], 0)
        self.assertEqual(seal["technical_diagnostics_n"], 0)
        self.assertFalse((run["out"] / "technical-diagnostics.jsonl").exists())
        self.assertFalse(seal["comparison_eligible"])

    def test_no_overwrite_of_existing_evaluation(self):
        run = self.make_run()
        self.compare(run)
        before = (run["evaluation"] / "metrics.json").read_bytes()
        with self.assertRaisesRegex(EvaluationError, "never overwrite"):
            self.compare(run)
        self.assertEqual((run["evaluation"] / "metrics.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
