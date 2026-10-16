"""Execute root's predeclared, invented cases using real temporary source files."""
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent / "runtime"
sys.path.insert(0, str(RUNTIME))
import policy_coding_v27 as coder
from selftest_common_if_extensions03 import prose


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identities():
    return {str(p): sha(p) for p in sorted(RUNTIME.glob("*.py"))}


def main():
    output = HERE / "actual_execution.json"
    if output.exists():
        raise FileExistsError("Preserve the first execution; use a separate, declared attempt.")
    design = json.loads((HERE / "design.json").read_text())
    before = identities()
    rows = []
    with tempfile.TemporaryDirectory(prefix="root-common07-independent-") as tmp:
        for case in design["cases"]:
            record = prose(Path(tmp) / case["name"], case["text"], prefix=case["prefix"])
            if case.get("expected_source_error"):
                Path(record["source"]).write_text(case["text"], encoding="utf-8")
                record["source_sha256"] = record["unit_source_sha256"] = sha(Path(record["source"]))
            original = copy.deepcopy(record)
            pred, error = None, None
            try:
                pred = coder.code_unit(record)
            except Exception as exc:
                error = {"type": type(exc).__name__, "message": str(exc)}
            assert record == original
            if pred:
                for e in pred["evidence"]:
                    assert case["text"][e["start"]:e["end"]] == e["text"]
                    for anchor in e.get("current_relation_anchors", []):
                        assert case["text"][anchor["start"]:anchor["end"]] == anchor["text"]
                    dep = e.get("context_dependency") or {}
                    if dep.get("kind") == "COMMON06_authenticated_current_relation_scope":
                        paragraph = next(p for p in record["paragraph_context"] if p["paragraph_id"] == dep["paragraph_id"])
                        assert paragraph["text"][dep["antecedent_start_in_paragraph"]:dep["antecedent_end_in_paragraph"]] == dep["antecedent_text"]
                        assert dep["source_sha256"] == sha(Path(record["source"]))
                        assert dep["candidate_sha256"] == sha(Path(record["candidate_file"]))
                        auth = dep["source_authentication"]
                        assert auth.get("literal_reproduced_in_current_runtime") or auth.get("layout_reconstructed_literal_reproduced")
            if case.get("expected_source_error"):
                passed = error is not None and error["type"] == "ValueError"
            else:
                passed = error is None and pred["labels"][case["dimension"]] == case["expected"]
            rows.append({"name": case["name"], "expected": case.get("expected"),
                         "expected_source_error": bool(case.get("expected_source_error")),
                         "actual": pred["labels"][case["dimension"]] if pred else None,
                         "passed": passed, "error": error, "prediction": pred,
                         "input_unchanged": True, "current_offsets_checked": pred is not None})
    after = identities()
    assert before == after
    result = {"scope": "Four independent targeted method/example checks; invented material only, not empirical validity or accuracy.",
              "design_sha256": sha(HERE / "design.json"), "manual_sha256": design["manual_sha256"],
              "code_sha256": before, "code_unchanged": True, "authenticators_mocked": False,
              "real_policy_units_executed": 0, "labels_read": False,
              "checks": rows, "passed": all(row["passed"] for row in rows)}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "checks": [{k: row[k] for k in ("name", "actual", "passed", "error")} for row in rows], "output_sha256": sha(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
