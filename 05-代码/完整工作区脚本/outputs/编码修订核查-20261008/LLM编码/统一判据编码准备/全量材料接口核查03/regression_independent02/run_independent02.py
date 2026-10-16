"""Independent artificial projector-interface checks; no corpus or model I/O."""
import copy
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PF = HERE.parent
MANIFEST = "a" * 64


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace(value, mapping):
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [replace(v, mapping) for v in value]
    if isinstance(value, dict):
        return {k: replace(v, mapping) for k, v in value.items()}
    return value


def run():
    design_path = HERE / "design_independent02.json"
    design = json.loads(design_path.read_text())
    source_path = PF / "project_source_only_inputs.py"
    before_sha = sha(source_path)
    assert before_sha == design["projector_sha256"]
    p = load("independently_reviewed_projector02", source_path)
    validator = load("independent02_validator", PF.parent / "runtime/validate_binary_output.py")
    results = []
    with tempfile.TemporaryDirectory(prefix="independent-projector02-invented-") as tmp:
        folder = Path(tmp)
        source_a, source_b = folder / "sourceA.txt", folder / "sourceB.txt"
        source_a.write_text("独立构造当前句。独立原段。", encoding="utf-8")
        source_b.write_text("独立构造段落乙。", encoding="utf-8")
        ca, cb = folder / "candidateA.json", folder / "candidateB.json"
        ca.write_text(json.dumps({"source": str(source_a), "text": "独立构造当前句。"}), encoding="utf-8")
        cb.write_text(json.dumps({"source": str(source_b), "text": "独立构造段落乙。"}), encoding="utf-8")
        ia, ib = folder / "imageA.bin", folder / "imageB.bin"
        ia.write_bytes(b"artificial image identity A; not a decoded policy image")
        ib.write_bytes(b"artificial image identity B; not a decoded policy image")
        mapping = {"$sourceB": str(source_b), "$shaB": sha(source_b),
                   "$candidateB": str(cb), "$candidateShaB": sha(cb),
                   "$imageB": str(ib), "$imageShaB": sha(ib)}
        for number, case in enumerate(design["cases"], 1):
            current = case.get("current", "独立构造当前句。")
            row = {"id": f"NEW-INDEPENDENT-02-{number:02d}", "text": current, "pages": [1],
                   "contexts": replace(case["context"], mapping)}
            if case.get("filename_marker"):
                row["source_title"] = "MARKER_FILENAME_TITLE"
            rule = {"id": row["id"], "input": {
                "unit_text": "独立错配当前句。" if case.get("mismatch") else current,
                "source": str(source_b), "source_sha256": sha(source_b),
                "unit_source": str(source_a), "unit_source_sha256": sha(source_a),
                "candidate_file": str(ca), "candidate_sha256": sha(ca),
                "source_image": str(ia), "source_image_sha256": sha(ia)}}
            original = copy.deepcopy((row, rule))
            result, error, registry = None, None, {}
            try:
                first = p.project_record(row, rule)
                if case["bindings"] == "matching":
                    for leaf in first["provenance_sidecar"]["policy_leaves"]:
                        registry[leaf["raw_pointer"]] = {
                            "text_sha256": leaf["text_sha256"],
                            "source_sha256": leaf["source_binding"].get("source_sha256"),
                            "manifest_sha256": MANIFEST, "proof_kind": "source_literal_span",
                            "locator": {"artificial_occurrence": leaf["raw_pointer"]}}
                    if case.get("registry_mutation"):
                        field = case["registry_mutation"]
                        registry["/text"][field] = {} if field == "locator" else "b" * 64
                    if case.get("boundary_invalid"):
                        pointer = "/contexts/complete_following_list_v11/boundary"
                        registry[pointer] = {"text_sha256": "b" * 64,
                            "source_sha256": sha(source_a), "manifest_sha256": MANIFEST,
                            "proof_kind": "source_literal_span", "locator": {"artificial_occurrence": pointer}}
                    result = p.project_record(row, rule, literal_bindings=registry, manifest_sha256=MANIFEST)
                else:
                    result = first
            except Exception as exc:
                error = {"type": type(exc).__name__, "message": str(exc)}
            checks = {"input_unchanged": (row, rule) == original}
            if case.get("mismatch"):
                checks["binding_mismatch_rejected"] = bool(error and error["type"] == "ValueError")
            elif error:
                checks["unexpected_exception"] = False
            else:
                s = result["provenance_sidecar"]
                visible = result["model_visible_candidate"]
                nodes = visible["contexts"]
                texts = list(validator.iter_context_text(nodes))
                payload = json.dumps(visible, ensure_ascii=False)
                checks["no_actual_or_formal_authentication"] = (s["actual_source_authentication_verified"] is False
                                                               and s["formal_model_input_ready"] is False)
                try:
                    p.require_formal_model_input(result)
                except ValueError:
                    checks["formal_accessor_refused"] = True
                else:
                    checks["formal_accessor_refused"] = False
                contract = case["expected_contract"]
                if contract == "identity_incomplete_no_mixed_inherited_pair":
                    checks["identity_incomplete"] = not s["source_identity_metadata_complete"]
                    checks["review_blocked"] = not s["binding_complete_for_review"]
                    leaf = next(l for l in s["policy_leaves"] if l["raw_pointer"] != "/text")
                    origin = leaf["source_binding"]
                    if case["name"].startswith(("source_", "unit_source")):
                        checks["no_parent_source_substitution"] = "source_path" not in origin and "source_sha256" not in origin
                    elif case["name"].startswith("candidate_"):
                        checks["no_parent_candidate_substitution"] = "candidate_path" not in origin and "candidate_sha256" not in origin
                    else:
                        checks["no_mixed_image_pair"] = "source_image" not in origin and "source_image_sha256" not in origin
                elif contract == "exact_child_identity_review_only":
                    origin = s["policy_leaves"][-1]["source_binding"]
                    checks["child_three_pairs_exact"] = all(origin[k] == v for k, v in {
                        "source_path": str(source_b), "source_sha256": sha(source_b),
                        "candidate_path": str(cb), "candidate_sha256": sha(cb),
                        "source_image": str(ib), "source_image_sha256": sha(ib)}.items())
                    checks["review_metadata_complete"] = s["binding_complete_for_review"]
                elif contract == "invalid_row_absent_from_parent_and_cells":
                    checks["row_never_copied"] = all("row_index_zero_based" not in n["structure"] for n in nodes)
                    checks["view_issue"] = not s["candidate_view_complete"]
                    checks["opinion_absent"] = "MARKER_ROW_OPINION" not in payload
                elif contract == "ordered_cells_and_validated_row_preserved":
                    table = next(n for n in nodes if n["kind"] == "table_row")
                    cells = [n for n in nodes if n["kind"] == "table_row_cell"]
                    checks["all_row_positions_match"] = all(n["structure"].get("row_index_zero_based") == 2 for n in nodes)
                    checks["blank_and_order_preserved"] = table["row_cells"] == ["相同格", "", "相同格"]
                    checks["duplicate_occurrences_separate"] = (len({n["context_id"] for n in cells}) == 2
                        and [n["structure"]["column_index"] for n in cells] == [0, 2])
                    checks["validator_can_quote_cells"] = all(n["text"] in texts for n in cells)
                    checks["review_complete"] = s["binding_complete_for_review"]
                elif contract == "all_distinct_literals_readable":
                    expected = [v for k, v in case["context"]["paragraph_context"][0].items() if k != "paragraph_id"]
                    checks["all_exact_fields_quotable"] = all(t in texts for t in expected)
                    checks["distinct_occurrences"] = len(s["policy_leaves"]) == len(expected) + 1
                    checks["view_complete"] = s["candidate_view_complete"]
                elif contract in {"view_incomplete_no_opinion_leak", "view_incomplete_even_with_bound_context",
                                  "declared_unresolved_boundary_not_view_complete", "omitted_declared_boundary_not_view_complete",
                                  "context_serialization_unresolved_blocks_view"}:
                    checks["view_incomplete"] = not s["candidate_view_complete"]
                    checks["review_blocked"] = not s["binding_complete_for_review"]
                    checks["markers_absent"] = "MARKER_" not in payload
                elif contract == "boundary_preserved_or_material_issue":
                    checks["not_silently_omitted_as_complete"] = ("独立构造边界原文。" in texts or not s["candidate_view_complete"])
                elif contract == "view_and_identity_only_complete":
                    checks["axes_separate"] = (s["candidate_view_complete"] and s["source_identity_metadata_complete"]
                        and not s["external_manifest_binding_complete"] and not s["binding_complete_for_review"])
                elif contract == "review_only_no_actual_or_formal_auth":
                    checks["review_metadata_complete"] = s["binding_complete_for_review"]
                elif contract == "external_binding_incomplete":
                    checks["bad_external_registry_rejected"] = not s["external_manifest_binding_complete"] and not s["binding_complete_for_review"]
                elif contract == "file_sha_does_not_authenticate_literal":
                    checks["literal_actually_absent"] = current not in source_a.read_text()
                    checks["file_bytes_check_only"] = [x["hash_equal"] for x in p.verify_manifest_files([
                        {"path": str(source_a), "sha256": sha(source_a)}, {"path": str(source_a), "sha256": "b"*64}])] == [True, False]
                    checks["metadata_can_be_complete_without_authentication"] = s["binding_complete_for_review"]
                elif contract == "current_exact_table_not_natural_sentence_claim":
                    checks["current_exact"] = visible["text"] == current
                    checks["candidate_view_complete_only"] = s["candidate_view_complete"]
                elif contract == "no_opinions_filename_in_view":
                    checks["markers_absent"] = "MARKER_" not in payload
                else:
                    raise RuntimeError("unhandled predeclared contract: " + contract)
            results.append({"name": case["name"], "contract": case["expected_contract"],
                            "passed": all(checks.values()), "checks": checks, "error": error,
                            "actual": result})
    after_sha = sha(source_path)
    assert before_sha == after_sha
    return {"at_utc": datetime.now(timezone.utc).isoformat(), "design_sha256": sha(design_path),
            "runner_sha256": sha(__file__), "projector_before_sha256": before_sha,
            "projector_after_sha256": after_sha, "check_n": len(results),
            "pass_n": sum(c["passed"] for c in results), "results": results,
            "scope": "33 independently designed artificial interface fixtures; no actual corpus/labels/model. External registry is deliberately invented, not certification."}


if __name__ == "__main__":
    target = HERE / "actual_independent02.json"
    result = run()
    with target.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"check_n": result["check_n"], "pass_n": result["pass_n"],
        "failures": [{"name": c["name"], "failed_checks": [k for k, v in c["checks"].items() if not v], "error": c["error"]}
                     for c in result["results"] if not c["passed"]],
        "path": str(target), "sha256": sha(target)}, ensure_ascii=False))
