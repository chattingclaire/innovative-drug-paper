"""Independent predeclared artificial cases and separately named old regression."""
import copy
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "runtime"))
import policy_coding_v27 as coder


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prose(folder, current, prefix):
    folder.mkdir()
    source, candidate = folder / "invented-source.txt", folder / "invented-candidate.json"
    paragraph = prefix + current
    source.write_text(paragraph, encoding="utf-8")
    candidate.write_text(json.dumps({"paragraphs": [{"id": "invented-p", "text": paragraph,
        "pages": [1], "line_ids": ["invented:1"]}], "unit_candidates": [{"id": "invented-u",
        "text": current, "paragraph_id": "invented-p"}]}, ensure_ascii=False), encoding="utf-8")
    context = {"paragraph_id": "invented-p", "text": paragraph, "pages": [1]}
    return {"unit_id": "invented-u", "unit_text": current, "source": str(source), "unit_source": str(source),
        "source_sha256": sha(source), "unit_source_sha256": sha(source), "candidate_file": str(candidate),
        "candidate_sha256": sha(candidate), "paragraph_context": [context],
        "llm_v29_shared_context": {"paragraph_context": [copy.deepcopy(context)]}}


def verify(record, result):
    original = record["unit_text"]
    errors, counts = [], {"active_evidence": 0, "current_anchors": 0, "context_bindings": 0,
                          "prior_evidence": 0, "format_truth_anchors": 0}

    def check_span(obj, category):
        counts[category] += 1
        a, b = obj.get("start"), obj.get("end")
        if not (type(a) is int and type(b) is int and 0 <= a < b <= len(original)
                and original[a:b] == obj.get("text")):
            errors.append({"category": category, "span": obj})

    for e in result["evidence"]:
        check_span(e, "active_evidence")
        for anchor in e.get("current_relation_anchors", []):
            check_span(anchor, "current_anchors")
        dep = e.get("context_dependency") or {}
        if dep.get("kind") == "COMMON06_authenticated_current_relation_scope":
            counts["context_bindings"] += 1
            paragraph = next(p for p in record["paragraph_context"] if p["paragraph_id"] == dep["paragraph_id"])
            actual = paragraph["text"][dep["antecedent_start_in_paragraph"]:dep["antecedent_end_in_paragraph"]]
            auth = dep["source_authentication"]
            if not (actual == dep["antecedent_text"] and dep["source_sha256"] == sha(record["source"])
                    and dep["candidate_sha256"] == sha(record["candidate_file"])
                    and (auth.get("literal_reproduced_in_current_runtime") is True
                         or auth.get("layout_reconstructed_literal_reproduced") is True)):
                errors.append({"category": "context_binding", "dependency": dep})
    for e in result.get("common_definition_prior_evidence", []):
        check_span(e, "prior_evidence")
    for operation in result.get("quoted_format_operations08", []):
        for anchor in operation["anchors"]:
            check_span(anchor, "format_truth_anchors")
        for use in operation.get("substantive_uses", []):
            for anchor in use["anchors"]:
                check_span(anchor, "format_truth_anchors")
    for dim in ("S", "E", "Ec", "I", "F"):
        if type(result["labels"][dim]) is not int or result["labels"][dim] not in (0, 1):
            errors.append({"category": "binary_type", "dimension": dim})
        if result["labels"][dim] != int(any(e["dimension"] == dim for e in result["evidence"])):
            errors.append({"category": "active_evidence_label_mismatch", "dimension": dim})
    return {"passed": not errors, "counts": counts, "errors": errors}


def run():
    design_path = HERE / "design_independent08.json"
    design = json.loads(design_path.read_text())
    old_design_path = Path(json.loads((ROOT / "constructed_design08.json").read_text())["regressions"][0]["path"])
    old_cases = json.loads(old_design_path.read_text())["cases"]
    code_before = {str(p): sha(p) for p in sorted((ROOT / "runtime").glob("*.py"))}
    checks = []
    with tempfile.TemporaryDirectory(prefix="independent08-actual-invented-") as temporary:
        for group, cases in (("new_independent08", design["cases"]), ("old20_mechanical_regression", old_cases)):
            for index, case in enumerate(cases):
                record = prose(Path(temporary) / f"{group}-{index}", case["text"], case["prefix"])
                if case.get("expected_source_error"):
                    Path(record["source"]).write_text(case["text"], encoding="utf-8")
                    record["source_sha256"] = record["unit_source_sha256"] = sha(record["source"])
                before = copy.deepcopy(record)
                result, error = None, None
                try:
                    result = coder.code_unit(record)
                except Exception as exc:
                    error = {"type": type(exc).__name__, "message": str(exc)}
                technical = verify(record, result) if result is not None else None
                if case.get("expected_source_error"):
                    passed = bool(error and error["type"] == "ValueError" and result is None and record == before)
                else:
                    passed = bool(error is None and result is not None and record == before and technical["passed"]
                                  and all(result["labels"][dim] == expected for dim, expected in case["expected"].items()))
                checks.append({"group": group, "name": case["name"], "expected": case["expected"],
                    "expected_source_error": case.get("expected_source_error", False),
                    "passed": passed, "error": error, "input_unchanged": record == before,
                    "technical": technical, "actual_labels": result["labels"] if result else None,
                    "prediction": result, "source_sha256": sha(record["source"]), "candidate_sha256": sha(record["candidate_file"])})
    after = {str(p): sha(p) for p in sorted((ROOT / "runtime").glob("*.py"))}
    assert code_before == after
    return {"at_utc": datetime.now(timezone.utc).isoformat(), "runtime_version": coder.VERSION,
        "design_path": str(design_path), "design_sha256": sha(design_path), "runner_sha256": sha(__file__),
        "old20_design_path": str(old_design_path), "old20_design_sha256": sha(old_design_path),
        "runtime_sha256_before": code_before, "runtime_sha256_after": after,
        "checks": checks, "new_n": len(design["cases"]),
        "new_pass_n": sum(c["passed"] for c in checks if c["group"] == "new_independent08"),
        "old20_n": len(old_cases), "old20_pass_n": sum(c["passed"] for c in checks if c["group"] == "old20_mechanical_regression"),
        "old20_not_counted_as_new_independent": True,
        "scope": "Artificial actual TXT/JSON; full pipeline, no mocks, no true policy corpus/reference labels/models; all first outputs preserved."}


if __name__ == "__main__":
    result = run()
    path = HERE / "actual_independent08_first.json"
    with path.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"new_n": result["new_n"], "new_pass_n": result["new_pass_n"],
        "old20_n": result["old20_n"], "old20_pass_n": result["old20_pass_n"],
        "failures": [{"group": c["group"], "name": c["name"], "expected": c["expected"],
                      "actual": c["actual_labels"], "error": c["error"]} for c in result["checks"] if not c["passed"]],
        "output_path": str(path), "output_sha256": sha(path)}, ensure_ascii=False))
