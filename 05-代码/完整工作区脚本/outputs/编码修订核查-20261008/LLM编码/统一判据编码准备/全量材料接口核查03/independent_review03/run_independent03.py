"""Independent, finite synthetic boundary review; never read a corpus."""
import copy
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key != "paragraph_id":
                yield from strings(item)


def run():
    design_path = HERE / "design_independent03.json"
    design = json.loads(design_path.read_text())
    code = Path(design["code_path"])
    assert sha(code) == design["code_sha256"]
    projector = load("independent_projector03", code)
    validator_path = BASE / "runtime/validate_binary_output.py"
    validator = load("independent_validator03", validator_path)
    results = []
    with tempfile.TemporaryDirectory(prefix="independent-boundary03-") as tmp:
        for number, case in enumerate(design["cases"], 1):
            work = Path(tmp) / str(number)
            work.mkdir()
            current = "这是仅供独立接口复核的当前单元。"
            row = {
                "id": f"INDEPENDENT-BOUNDARY03-{number}", "text": current,
                "pages": [2], "source_title": "DO_NOT_COPY_FILENAME_OR_OPINION",
                "contexts": {"complete_following_list_v11": {
                    "paragraph_id": "list-p70", "text": "构造列表外层原文。",
                    "labels": {"S": 1}, "verification": {"opinion": "DO_NOT_COPY_OPINION"},
                    case["key"]: copy.deepcopy(case["value"]),
                }},
            }
            candidate = work / "candidate.json"
            candidate.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
            source = work / "source.txt"
            source.write_text("\n".join([current, "构造列表外层原文。", *strings(case["value"])]), encoding="utf-8")
            rule = {"id": row["id"], "input": {
                "unit_text": current, "source": str(source), "source_sha256": sha(source),
                "candidate_path": str(candidate), "candidate_sha256": sha(candidate),
            }}
            unchanged = copy.deepcopy((row, rule))
            initial = projector.project_record(row, rule)
            manifest = "a" * 64
            registry = {
                leaf["raw_pointer"]: {
                    "text_sha256": leaf["text_sha256"],
                    "source_sha256": sha(source), "manifest_sha256": manifest,
                    "proof_kind": "source_literal_span", "locator": {"synthetic_pointer": leaf["raw_pointer"]},
                } for leaf in initial["provenance_sidecar"]["policy_leaves"]
            }
            pointer = "/contexts/complete_following_list_v11/" + case["key"]
            if isinstance(case["value"], str) and case["value"].strip():
                proof = {
                    "text_sha256": projector.sha_text(case["value"]),
                    "source_sha256": sha(source), "manifest_sha256": manifest,
                    "proof_kind": "source_literal_span", "locator": {"synthetic_pointer": pointer},
                }
                mode = case["proof"]
                if mode == "wrong_text":
                    proof["text_sha256"] = "b" * 64
                elif mode == "wrong_source":
                    proof["source_sha256"] = "b" * 64
                elif mode == "wrong_manifest":
                    proof["manifest_sha256"] = "b" * 64
                elif mode == "wrong_kind":
                    proof["proof_kind"] = "synthetic_unsupported_kind"
                elif mode == "empty_locator":
                    proof["locator"] = {}
                elif mode == "non_object":
                    proof = "not a proof object"
                if mode != "no_registry":
                    registry[pointer] = proof
            result = projector.project_record(row, rule, literal_bindings=registry, manifest_sha256=manifest)
            side = result["provenance_sidecar"]
            visible = result["model_visible_candidate"]
            nodes = visible["contexts"]
            by_id = {node["context_id"]: node for node in nodes}
            texts = list(validator.iter_context_text(nodes))
            assertions = {
                "view_matches_predeclared_contract": side["candidate_view_complete"] is case["expected_view_complete"],
                "current_exact": visible["text"] == current,
                "inputs_unchanged": (row, rule) == unchanged,
                "no_opinions_or_filename": "DO_NOT_COPY" not in json.dumps(visible, ensure_ascii=False),
                "actual_authentication_false": side["actual_source_authentication_verified"] is False,
                "formal_ready_false": side["formal_model_input_ready"] is False,
            }
            try:
                projector.require_formal_model_input(result)
            except ValueError:
                assertions["formal_accessor_refused"] = True
            else:
                assertions["formal_accessor_refused"] = False
            if case["expected_view_complete"]:
                assertions["metadata_review_complete"] = side["binding_complete_for_review"] is True
                assertions["all_declared_boundary_words_quotable"] = all(s in texts for s in strings(case["value"]))
                if case["structural_check"] == "all_literal_fields":
                    object_node = next((n for n in nodes if n["structure"].get("paragraph_id") == "fresh-p71"), None)
                    assertions["object_paragraph_location_preserved"] = object_node is not None
                    assertions["all_fields_have_distinct_leaf_occurrences"] = len([
                        leaf for leaf in side["policy_leaves"] if leaf["raw_pointer"].startswith(pointer + "/")
                    ]) == 5
                elif case["structural_check"] == "ordered_duplicate_occurrences":
                    parent = next(n for n in nodes if n["structure"].get("paragraph_id") == "list-p70")
                    groups = [g for g in parent["structure"].get("child_groups", []) if g["position"] == case["key"]]
                    ordered = groups[0]["ordered_context_ids"] if groups else []
                    assertions["distinct_ordered_occurrences"] = len(ordered) == len(set(ordered)) == 2
                    assertions["literal_duplicate_count"] = sum(n.get("text") == "重复但独立的界定句。" for n in nodes) == 2
                    assertions["member_location_order_parent"] = (
                        [by_id[c]["structure"].get("paragraph_id") for c in ordered] == ["fresh-p72", "fresh-p73"]
                        and [by_id[c]["structure"].get("sequence_index") for c in ordered] == [0, 1]
                        and all(by_id[c]["structure"].get("parent_context_id") == parent["context_id"] for c in ordered)
                    )
                elif case["structural_check"] == "nested_parent_links":
                    outer = next(n for n in nodes if n["structure"].get("paragraph_id") == "fresh-p74")
                    inner = next(n for n in nodes if n["structure"].get("paragraph_id") == "fresh-p75")
                    assertions["nested_parent_preserved"] = inner["structure"].get("parent_context_id") == outer["context_id"]
                    assertions["nested_group_preserved"] = any(
                        g["position"] == "next_boundary" and g["ordered_context_ids"] == [inner["context_id"]]
                        for g in outer["structure"].get("child_groups", [])
                    )
            else:
                assertions["candidate_view_issue_exists"] = any(i["category"] == "candidate_view" for i in side["issues"])
                assertions["metadata_review_blocked"] = side["binding_complete_for_review"] is False
            results.append({"name": case["name"], "passed": all(assertions.values()), "assertions": assertions, "actual": result})
    preserved = json.loads((HERE / "preservation_before.json").read_text())
    preservation = {path: {"before": expected, "after": sha(path), "unchanged": sha(path) == expected} for path, expected in preserved.items()}
    (HERE / "preservation_after.json").write_text(json.dumps(preservation, ensure_ascii=False, indent=2) + "\n")
    return {
        "schema": "independent-projector03-actual-v1", "at_utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "/root/independent06_static", "code_sha256": sha(code),
        "runner_sha256": sha(__file__), "design_sha256": sha(design_path), "validator_sha256": sha(validator_path),
        "case_n": len(results), "passed_n": sum(r["passed"] for r in results),
        "fail_n": sum(not r["passed"] for r in results), "results": results,
        "original_file_n": len(preservation), "all_original_files_unchanged": all(r["unchanged"] for r in preservation.values()),
        "scope": {"true_policy_leaves_read": 0, "gold_labels_read": 0, "real_corpus_exported": False,
                  "model_called": False, "rule_predictions_run": False, "synthetic_registry_is_source_authentication": False},
    }


if __name__ == "__main__":
    target = HERE / "actual_independent03.json"
    if target.exists():
        raise SystemExit("First execution is immutable; use a separately named attempt if requested.")
    report = run()
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("case_n", "passed_n", "fail_n", "all_original_files_unchanged")}, ensure_ascii=False))
