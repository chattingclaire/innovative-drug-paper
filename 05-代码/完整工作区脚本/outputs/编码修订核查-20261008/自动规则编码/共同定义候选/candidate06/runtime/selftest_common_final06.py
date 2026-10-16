"""Predeclared wholly invented cases, run through candidate06's actual pipeline.

Temporary TXT/JSON sources exercise the real authenticator; no policy material,
reference annotations, external model, or mocked authentication is used.
"""
import copy
import hashlib
import json
import tempfile
from pathlib import Path

import policy_coding_v27 as coder
from selftest_common_if_extensions03 import prose

ROOT = Path(__file__).resolve().parent.parent
FINAL_SHA = "5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    design_path = ROOT / "constructed_design06.json"
    design = json.loads(design_path.read_text())
    addendum_path = ROOT / "constructed_design06_addendum01.json"
    addendum2_path = ROOT / "constructed_design06_addendum02.json"
    addendum3_path = ROOT / "constructed_design06_addendum03.json"
    addendum4_path = ROOT / "constructed_design06_addendum04.json"
    addendum4 = json.loads(addendum4_path.read_text())
    ambiguous = set(addendum4["ambiguous_expectations"])
    cases = (design["checks"] + json.loads(addendum_path.read_text())["checks"]
             + json.loads(addendum2_path.read_text())["checks"] + json.loads(addendum3_path.read_text())["checks"]
             + addendum4["checks"])
    checks = []
    with tempfile.TemporaryDirectory(prefix="candidate06-invented-only-") as temporary:
        folder = Path(temporary)
        for case in cases:
            record = prose(folder / case["name"], case["text"], prefix=case["prefix"])
            if case["expect_source_error"]:
                Path(record["source"]).write_text(case["text"] + "本构造来源不含所提供的前句。", encoding="utf-8")
                record["source_sha256"] = record["unit_source_sha256"] = sha(Path(record["source"]))
                record["paragraph_context"][0]["verification"] = {"verified": True, "method": "insufficient_invented_negative_fixture"}
                record["llm_v29_shared_context"]["paragraph_context"] = copy.deepcopy(record["paragraph_context"])
            before = copy.deepcopy(record)
            prediction, error = None, None
            try:
                prediction = coder.code_unit(record)
            except Exception as exc:
                error = {"type": type(exc).__name__, "message": str(exc)}
            assert record == before
            if case["expect_source_error"]:
                passed = bool(error and error["type"] == "ValueError" and
                              "actual literal or layout source reproduction" in error["message"])
            else:
                passed = error is None and prediction["labels"][case["dimension"]] == case["expected"]
                if case["name"] in ambiguous and error is None:
                    passed = None  # Observation only: the original expected 0 is not unique.
            if prediction:
                assert prediction["common_rules_sha256"] == FINAL_SHA
                assert prediction["unit_text_sha256"] == hashlib.sha256(case["text"].encode()).hexdigest()
                if case["name"] in {"E_no_effective_drug_option", "E_no_effective_treatment_drug", "E_no_effect_criterion_option", "E_authenticated_trial_scope"}:
                    assert any(e.get("effect_statement_kind") == "no_effective_drug_option" for e in prediction["evidence"])
                if case["name"] == "E_negative_drug_effect":
                    assert any(e.get("effect_statement_kind") == "specific_drug_ineffectiveness" for e in prediction["evidence"])
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
                        assert dep["source_sha256"] == sha(Path(record["source"]))
                        assert dep["candidate_sha256"] == sha(Path(record["candidate_file"]))
            checks.append({"name": case["name"], "dimension": case["dimension"],
                           "expected": case["expected"], "actual": prediction["labels"][case["dimension"]] if prediction else None,
                           "passed": passed, "error": error,
                           "expectation_status": "ambiguous_not_scored" if case["name"] in ambiguous else "predeclared_boundary",
                           "evidence": [e for e in prediction["evidence"] if e["dimension"] == case["dimension"]] if prediction else None,
                           "offsets_checked": prediction is not None, "input_unchanged": True})
    print(json.dumps({"passed": all(c["passed"] is not False for c in checks), "check_n": len(checks),
                      "scored_check_n": sum(c["passed"] is not None for c in checks),
                      "ambiguous_observation_n": sum(c["passed"] is None for c in checks),
                      "design_path": str(design_path), "design_sha256": sha(design_path),
                      "addendum_path": str(addendum_path), "addendum_sha256": sha(addendum_path), "checks": checks,
                      "addendum2_path": str(addendum2_path), "addendum2_sha256": sha(addendum2_path),
                      "addendum3_path": str(addendum3_path), "addendum3_sha256": sha(addendum3_path),
                      "addendum4_path": str(addendum4_path), "addendum4_sha256": sha(addendum4_path),
                      "fixture_origin": "all deliberately invented, not empirical samples",
                      "real_policy_units_executed": 0, "labels_loaded": False,
                      "authenticators_mocked": False, "full_pipeline_on_invented_only": True},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
