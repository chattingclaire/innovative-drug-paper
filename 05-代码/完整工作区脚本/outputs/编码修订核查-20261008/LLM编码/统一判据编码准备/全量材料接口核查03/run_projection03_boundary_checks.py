"""Predeclared artificial boundary interface checks; no source authentication."""
import copy
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run():
    projector = HERE / "project_source_only_inputs.py"
    before_sha = sha(projector)
    p = load("boundary_projector03", projector)
    v = load("boundary_validator03", HERE.parent / "runtime/validate_binary_output.py")
    design_path = HERE / "projection03_boundary_design.json"
    design = json.loads(design_path.read_text())
    results = []
    with tempfile.TemporaryDirectory(prefix="projector03-artificial-boundary-") as tmp:
        source = Path(tmp) / "source.txt"
        source.write_text("第三版构造当前句。第三版构造清单。第三版构造下一条边界。", encoding="utf-8")
        for number, case in enumerate(design["checks"], 1):
            key, value = case["boundary_key"], case["boundary_value"]
            row = {"id": f"CONSTRUCTED-BOUNDARY03-{number}", "text": "第三版构造当前句。", "pages": [1],
                   "contexts": {"complete_following_list_v11": {"text": "第三版构造清单。", key: copy.deepcopy(value)}}}
            rule = {"id": row["id"], "input": {"unit_text": row["text"], "unit_source": str(source), "unit_source_sha256": sha(source)}}
            original = copy.deepcopy((row, rule))
            first = p.project_record(row, rule)
            manifest = "d" * 64
            registry = {leaf["raw_pointer"]: {"text_sha256": leaf["text_sha256"],
                "source_sha256": leaf["source_binding"].get("source_sha256"),
                "manifest_sha256": manifest, "proof_kind": "source_literal_span",
                "locator": {"artificial_occurrence": leaf["raw_pointer"]}}
                for leaf in first["provenance_sidecar"]["policy_leaves"]}
            pointer = "/contexts/complete_following_list_v11/" + key
            if isinstance(value, str) and value.strip():
                registry[pointer] = {"text_sha256": p.sha_text(value) if case["proof"] == "matching" else "e" * 64,
                    "source_sha256": sha(source), "manifest_sha256": manifest,
                    "proof_kind": "source_literal_span", "locator": {"artificial_occurrence": pointer}}
            result = p.project_record(row, rule, literal_bindings=registry, manifest_sha256=manifest)
            side = result["provenance_sidecar"]
            nodes = result["model_visible_candidate"]["contexts"]
            texts = list(v.iter_context_text(nodes))
            checks = {"input_unchanged": (row, rule) == original,
                      "view_matches_predeclared_contract": side["candidate_view_complete"] == case["expected_view_complete"],
                      "no_actual_or_formal_authentication": side["actual_source_authentication_verified"] is False and side["formal_model_input_ready"] is False}
            try:
                p.require_formal_model_input(result)
            except ValueError:
                checks["formal_accessor_refused"] = True
            else:
                checks["formal_accessor_refused"] = False
            if case["expected_view_complete"]:
                checks["review_metadata_complete"] = side["binding_complete_for_review"]
                if isinstance(value, str):
                    checks["boundary_exact_literal_preserved"] = value in texts
                elif isinstance(value, dict):
                    checks["all_declared_boundary_literals_preserved"] = all(t in texts for k, t in value.items() if k != "paragraph_id")
                    checks["paragraph_position_preserved"] = any(n["structure"].get("paragraph_id") == "bound01" for n in nodes)
                else:
                    parent = next(n for n in nodes if n["kind"] == "ordered_list")
                    groups = [g for g in parent["structure"].get("child_groups", []) if g["position"] == key]
                    ordered = groups[0]["ordered_context_ids"] if groups else []
                    by_id = {n["context_id"]: n for n in nodes}
                    checks["distinct_ordered_boundary_occurrences"] = len(ordered) == 2 and len(set(ordered)) == 2
                    checks["positions_and_parent_preserved"] = (len(ordered) == 2 and [by_id[c]["structure"].get("paragraph_id") for c in ordered] == ["bound02", "bound03"]
                        and all(by_id[c]["structure"].get("parent_context_id") == parent["context_id"] for c in ordered))
            else:
                checks["candidate_view_issue_recorded"] = any(i["category"] == "candidate_view" for i in side["issues"])
                checks["review_blocked"] = not side["binding_complete_for_review"]
            results.append({"name": case["name"], "passed": all(checks.values()), "checks": checks, "actual": result})
    assert sha(projector) == before_sha
    return {"at_utc": datetime.now(timezone.utc).isoformat(), "code_sha256": before_sha,
            "runner_sha256": sha(__file__), "design_sha256": sha(design_path),
            "check_n": len(results), "passed_n": sum(r["passed"] for r in results), "results": results,
            "scope": "New constructed checks, not independent review or source certification; no actual material/model/answers."}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
