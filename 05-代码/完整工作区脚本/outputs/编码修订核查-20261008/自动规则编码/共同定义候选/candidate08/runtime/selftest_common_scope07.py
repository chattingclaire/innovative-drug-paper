"""Predeclared artificial scope cases; real TXT/JSON and full candidate pipeline."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path

import policy_coding_v27 as coder
from selftest_common_if_extensions03 import prose

ROOT = Path(__file__).resolve().parent.parent


def main():
    path = ROOT / "constructed_design07.json"
    design = json.loads(path.read_text())
    addendum = ROOT / "constructed_design07_addendum01.json"
    cases = design["checks"] + json.loads(addendum.read_text())["checks"]
    checks = []
    with tempfile.TemporaryDirectory(prefix="candidate07-artificial-scope-") as tmp:
        for case in cases:
            record = prose(Path(tmp) / case["name"], case["text"], prefix=case["prefix"])
            original = copy.deepcopy(record)
            error, prediction = None, None
            try:
                prediction = coder.code_unit(record)
            except Exception as exc:
                error = {"type": type(exc).__name__, "message": str(exc)}
            assert record == original
            if prediction:
                assert prediction["unit_text_sha256"] == hashlib.sha256(case["text"].encode()).hexdigest()
                for evidence in prediction["evidence"]:
                    assert case["text"][evidence["start"]:evidence["end"]] == evidence["text"]
                    for anchor in evidence.get("current_relation_anchors", []):
                        assert case["text"][anchor["start"]:anchor["end"]] == anchor["text"]
                    dep = evidence.get("context_dependency") or {}
                    if dep.get("kind") == "COMMON06_authenticated_current_relation_scope":
                        paragraph = next(p for p in record["paragraph_context"] if p["paragraph_id"] == dep["paragraph_id"])
                        assert paragraph["text"][dep["antecedent_start_in_paragraph"]:dep["antecedent_end_in_paragraph"]] == dep["antecedent_text"]
                        auth = dep["source_authentication"]
                        assert auth.get("literal_reproduced_in_current_runtime") is True or auth.get("layout_reconstructed_literal_reproduced") is True
                        assert dep["source_sha256"] == hashlib.sha256(Path(record["source"]).read_bytes()).hexdigest()
                        assert dep["candidate_sha256"] == hashlib.sha256(Path(record["candidate_file"]).read_bytes()).hexdigest()
                for operation in prediction.get("quoted_format_operations07", []):
                    for anchor in operation["anchors"]:
                        assert case["text"][anchor["start"]:anchor["end"]] == anchor["text"]
            passed = error is None and prediction["labels"][case["dimension"]] == case["expected"]
            if case["observation_only"] and error is None:
                passed = None
            checks.append({"name": case["name"], "expected": case["expected"],
                           "actual": prediction["labels"][case["dimension"]] if prediction else None,
                           "passed": passed, "error": error,
                           "observation_only": case["observation_only"],
                           "evidence": [e for e in prediction["evidence"] if e["dimension"] == case["dimension"]] if prediction else None,
                           "scope_suppressions": [s for s in prediction.get("suppressions", []) if s.get("rule", "").startswith("COMMON07_")] if prediction else None,
                           "input_unchanged": True, "offsets_checked": prediction is not None})
    print(json.dumps({"version": coder.VERSION, "passed": all(c["passed"] is not False for c in checks),
                      "case_n": len(checks), "semantic_check_n": sum(c["passed"] is not None for c in checks),
                      "observation_n": sum(c["passed"] is None for c in checks), "checks": checks,
                      "design_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "addendum_sha256": hashlib.sha256(addendum.read_bytes()).hexdigest(),
                      "real_policy_units_executed": 0, "labels_read": False, "authenticators_mocked": False},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
