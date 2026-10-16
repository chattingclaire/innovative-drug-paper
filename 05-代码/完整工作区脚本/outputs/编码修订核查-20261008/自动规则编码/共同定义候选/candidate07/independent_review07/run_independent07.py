"""New predeclared invented checks; actual temporary TXT/JSON, full pipeline."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
RUNTIME = BASE / "runtime"
sys.dont_write_bytecode = True
sys.path.insert(0, str(RUNTIME))
import policy_coding_v27 as coder


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prose(folder, current, prefix):
    folder.mkdir()
    source, candidate = folder / "source.txt", folder / "candidate.json"
    body = prefix + current
    source.write_text(body, encoding="utf-8")
    para = {"id": "independent-invented-paragraph", "text": body,
            "pages": [1], "line_ids": ["invented:1"]}
    document = {"source": str(source), "source_sha256": sha(source),
                "unit_candidates": [{"id": "independent-invented-unit", "text": current,
                                     "paragraph_id": para["id"]}], "paragraphs": [para]}
    candidate.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    context = {"paragraph_id": para["id"], "text": body, "pages": [1]}
    return {"unit_id": "independent-invented-unit", "unit_text": current,
            "source": str(source), "unit_source": str(source),
            "source_sha256": sha(source), "unit_source_sha256": sha(source),
            "candidate_file": str(candidate), "candidate_sha256": sha(candidate),
            "paragraph_context": [context],
            "llm_v29_shared_context": {"paragraph_context": [copy.deepcopy(context)]}}


def verify_offsets(record, prediction):
    current = record["unit_text"]
    counts = {"current_evidence": 0, "relationship_anchor": 0,
              "format_anchor": 0, "suppression": 0, "context_dependency": 0}
    errors = []

    def slice_check(item, field):
        a, b, text = item.get("start"), item.get("end"), item.get("text")
        okay = type(a) is int and type(b) is int and 0 <= a < b <= len(current) and current[a:b] == text
        counts[field] += 1
        if not okay:
            errors.append({"kind": field, "item": item})

    for evidence in prediction.get("evidence", []):
        slice_check(evidence, "current_evidence")
        for anchor in evidence.get("current_relation_anchors", []):
            slice_check(anchor, "relationship_anchor")
        dep = evidence.get("context_dependency") or {}
        if dep.get("kind") == "COMMON06_authenticated_current_relation_scope":
            counts["context_dependency"] += 1
            paragraph = next(p for p in record["paragraph_context"] if p["paragraph_id"] == dep["paragraph_id"])
            a, b = dep["antecedent_start_in_paragraph"], dep["antecedent_end_in_paragraph"]
            auth = dep.get("source_authentication", {})
            okay = (paragraph["text"][a:b] == dep["antecedent_text"]
                    and dep["current_unit_sha256"] == hashlib.sha256(current.encode()).hexdigest()
                    and dep["source_sha256"] == sha(record["source"])
                    and dep["candidate_sha256"] == sha(record["candidate_file"])
                    and (auth.get("literal_reproduced_in_current_runtime") is True
                         or auth.get("layout_reconstructed_literal_reproduced") is True))
            if not okay:
                errors.append({"kind": "necessary_context_binding", "dependency": dep})
    for operation in prediction.get("quoted_format_operations07", []):
        for anchor in operation.get("anchors", []):
            slice_check(anchor, "format_anchor")
    for suppression in prediction.get("suppressions", []):
        if all(k in suppression for k in ("start", "end", "text")):
            slice_check(suppression, "suppression")
        for operation in suppression.get("format_operations", []):
            for anchor in operation.get("anchors", []):
                slice_check(anchor, "format_anchor")
    return {"passed": not errors, "counts": counts, "errors": errors}


def main():
    design_path = HERE / "design_independent07.json"
    design = json.loads(design_path.read_text(encoding="utf-8"))
    delivery_path = BASE / "implementation_delivery07.json"
    assert sha(delivery_path) == design["implementation_delivery_expected_sha256"]
    delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
    code_before = {p: sha(p) for p in delivery["code_sha256"]}
    assert code_before == delivery["code_sha256"]
    assert sha(design["fixed_manual"]["path"]) == design["fixed_manual"]["sha256"]
    checks = []
    with tempfile.TemporaryDirectory(prefix="independent07-new-invented-") as tmp:
        for index, case in enumerate(design["cases"]):
            record = prose(Path(tmp) / f"case-{index:02d}", case["text"], case["prefix"])
            if case["expected_source_error"]:
                Path(record["source"]).write_text(case["text"], encoding="utf-8")
                record["source_sha256"] = record["unit_source_sha256"] = sha(record["source"])
            original = copy.deepcopy(record)
            prediction, error = None, None
            try:
                prediction = coder.code_unit(record)
            except Exception as exc:
                error = {"type": type(exc).__name__, "message": str(exc)}
            unchanged = record == original
            technical = verify_offsets(record, prediction) if prediction else None
            if case["expected_source_error"]:
                passed = bool(error and error["type"] == "ValueError" and prediction is None and unchanged)
            else:
                passed = (error is None and unchanged and technical["passed"]
                          and all(prediction["labels"][d] == value for d, value in case["expected"].items()))
            checks.append({"name": case["name"], "expected": case["expected"],
                           "expected_source_error": case["expected_source_error"],
                           "actual_labels": prediction["labels"] if prediction else None,
                           "passed": bool(passed), "error": error, "input_unchanged": unchanged,
                           "source_sha256": sha(record["source"]), "candidate_sha256": sha(record["candidate_file"]),
                           "technical": technical, "prediction": prediction})
    # Reproduce the author's own artificial suite once, without changing or
    # opening prior output records. The stdout is artificial construction data.
    author = subprocess.run([sys.executable, "-B", str(RUNTIME / "selftest_common_scope07.py")],
                            cwd=BASE, capture_output=True, text=True)
    author_stdout = json.loads(author.stdout) if author.returncode == 0 else None
    author_record = {"command": [sys.executable, "-B", str(RUNTIME / "selftest_common_scope07.py")],
                     "exit_code": author.returncode, "stderr": author.stderr,
                     "stdout": author_stdout, "stdout_sha256": hashlib.sha256(author.stdout.encode()).hexdigest(),
                     "purpose": "Mechanical reproduction of author constructions only; not independent semantic validity."}
    with (HERE / "author_scope_suite_reproduction07.json").open("x", encoding="utf-8") as f:
        json.dump(author_record, f, ensure_ascii=False, indent=2)
        f.write("\n")
    code_after = {p: sha(p) for p in delivery["code_sha256"]}
    semantic = [x for x in checks if not x["expected_source_error"]]
    source = [x for x in checks if x["expected_source_error"]]
    return {"schema_version": "independent-candidate07-actual-v1", "at_utc": datetime.now(timezone.utc).isoformat(),
            "design_sha256": sha(design_path), "runner_sha256": sha(__file__), "delivery_sha256": sha(delivery_path),
            "manual_sha256": sha(design["fixed_manual"]["path"]), "runtime_version": coder.VERSION,
            "semantic_n": len(semantic), "semantic_pass_n": sum(x["passed"] for x in semantic),
            "source_error_n": len(source), "source_error_pass_n": sum(x["passed"] for x in source),
            "failures": [x["name"] for x in checks if not x["passed"]], "checks": checks,
            "author_scope_suite_reproduction": {"path": str(HERE/"author_scope_suite_reproduction07.json"),
                "sha256": sha(HERE/"author_scope_suite_reproduction07.json"), "exit_code": author.returncode,
                "passed": author_stdout.get("passed") if author_stdout else False,
                "case_n": author_stdout.get("case_n") if author_stdout else None},
            "code_sha256_before": code_before, "code_sha256_after": code_after,
            "code_unchanged": code_before == code_after == delivery["code_sha256"],
            "read_and_execution_scope": {"real_policy_text_or_answers_semantically_read": False,
                "real21_33_full_executed": False, "model_called": False, "source_authenticator_mocked": False,
                "real_temp_txt_json_used": True, "candidate_runtime_or_author_records_modified": False,
                "root_actual_outputs_read_or_reexecuted": False}}


if __name__ == "__main__":
    result = main()
    path = HERE / "actual_independent07.json"
    with path.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: result[k] for k in ("semantic_n", "semantic_pass_n", "source_error_n",
          "source_error_pass_n", "failures", "code_unchanged")}, ensure_ascii=False))
    print(json.dumps({"actual_path": str(path), "actual_sha256": sha(path)}, ensure_ascii=False))
