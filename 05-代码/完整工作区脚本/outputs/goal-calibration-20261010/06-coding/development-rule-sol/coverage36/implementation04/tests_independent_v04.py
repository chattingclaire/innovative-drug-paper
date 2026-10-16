"""Predeclared synthetic contrast checks; never actual fixture prediction.

Expectations and source constructions are fixed in audit/predeclared-contrasts.json.
Every attempt writes new diagnostics and retains failures. No reference is opened.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import io
import json
import unittest

import source_packet
import evidence
import relations
import dimensions

BASE = Path(__file__).resolve().parent
AUDIT = BASE / "audit"
DECLARATION = AUDIT / "predeclared-contrasts.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True)
    args = parser.parse_args()
    if not args.attempt.isdigit():
        raise ValueError("attempt must be a new numeric identifier")
    stem = "independent-run" + args.attempt
    paths = [AUDIT / (stem + suffix) for suffix in (".json", ".txt")]
    if any(path.exists() for path in paths):
        raise ValueError("refuse to overwrite any independent test attempt")
    declaration = json.loads(DECLARATION.read_text())
    code = [{"path": str(BASE / name), "sha256": digest(BASE / name)}
            for name in ("source_packet.py", "evidence.py", "relations.py", "dimensions.py")]
    attempts = []
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()

    class IndependentContrast(unittest.TestCase):
        pass

    def make_test(case):
        def test(self):
            out = {"name": case["name"], "area": case["area"],
                   "expected": case["expected"], "manual_reason": case["manual_reason"]}
            attempts.append(out)
            unit = source_packet.semantic_unit(case["source"])
            view = relations.RelationView(unit)
            decisions = dimensions.judge(view)
            evidence.validate_decisions(unit, decisions)
            values = {d: decisions[d]["value"] for d in evidence.DIMENSIONS}
            out.update(actual=values, decisions=decisions, relation_traces=view.traces(),
                       material_requests=view.material_requests)
            for dim, value in case["expected"].items():
                with self.subTest(dimension=dim):
                    self.assertEqual(values[dim], value, case["manual_reason"])
            for dim in case.get("forbid_positive_dimensions", []):
                with self.subTest(forbid_positive_dimension=dim):
                    self.assertNotEqual(values[dim], 1, case["manual_reason"])
            used = set()
            for rel in view.traces():
                used.update(e["context_id"] for e in rel["context_evidence"])
            for decision in decisions.values():
                if decision["value"] == 1:
                    used.update(e["context_id"] for e in decision["context_evidence"])
                    for extra in (decision.get("details") or {}).get("additional_evidence", []):
                        used.update(e["context_id"] for e in extra.get("context_evidence", []))
            for cid in case.get("forbidden_evidence_context_ids", []):
                with self.subTest(forbidden_evidence_context_id=cid):
                    self.assertNotIn(cid, used, case["manual_reason"])
            if case.get("requires_material_request"):
                self.assertTrue(view.material_requests or any(d["needed_material"] for d in decisions.values()),
                                "A missing operative reference must retain a concrete request.")
        return test

    for index, case in enumerate(declaration["cases"], 1):
        setattr(IndependentContrast, f"test_{index:02d}_{case['name']}", make_test(case))
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(IndependentContrast)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    finished = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report = {"role": "AI_development_predeclared_synthetic_contrast_execution",
              "started_at_utc": started, "finished_at_utc": finished,
              "declaration_path": str(DECLARATION), "declaration_sha256": digest(DECLARATION),
              "inference_modules": code,
              "inference_code_unchanged_during_execution": all(digest(Path(c["path"])) == c["sha256"] for c in code),
              "case_n": declaration["n_cases"], "tests_run": result.testsRun,
              "failure_entries_n": len(result.failures), "error_entries_n": len(result.errors),
              "successful": result.wasSuccessful(),
              "failures": [{"test": str(test), "traceback": trace} for test, trace in result.failures],
              "errors": [{"test": str(test), "traceback": trace} for test, trace in result.errors],
              "all_case_outputs": attempts,
              "expectations_not_changed_from_execution": True,
              "actual_fixture_prediction_executed": False,
              "raw_reference_file_read": False,
              "not_human_reference_or_acceptance": True}
    with paths[0].open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    with paths[1].open("x", encoding="utf-8") as handle:
        handle.write(stream.getvalue())
    print(json.dumps({k: report[k] for k in ("tests_run", "failure_entries_n", "error_entries_n", "successful", "declaration_sha256")}, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
