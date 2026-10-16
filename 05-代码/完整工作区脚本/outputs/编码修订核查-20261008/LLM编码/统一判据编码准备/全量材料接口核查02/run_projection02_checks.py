"""Invented projector02 regressions; no corpus, source policy, labels or models."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "全量材料接口核查01"
PROJECTOR = HERE / "project_source_only_inputs.py"
VALIDATOR = HERE.parent / "runtime/validate_binary_output.py"
INDEPENDENT = OLD / "independent_projection_review01/run_independent_projection01.py"
MANIFEST = "9" * 64


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run():
    p = load("projector02_under_test", PROJECTOR)
    validator = load("projection02_frozen_validator", VALIDATOR)
    code_sha = sha(PROJECTOR)
    old_sha = "168617fe56eb050b4c5607f856715515a282e5c2a4643faf0ae7d5af26ab5e42"
    assert sha(OLD / PROJECTOR.name) == old_sha

    # Preserve all six independent fixture bodies; change only the fixed SHA
    # expectation and inject the new module/path after source-only module load.
    class ExpectedHashOnly(ast.NodeTransformer):
        replacement_n = 0

        def visit_Constant(self, node):
            if node.value == old_sha:
                self.replacement_n += 1
                return ast.copy_location(ast.Constant(code_sha), node)
            return node

    tree = ast.parse(INDEPENDENT.read_text(encoding="utf-8"))
    transform = ExpectedHashOnly()
    tree = ast.fix_missing_locations(transform.visit(tree))
    assert transform.replacement_n == 1
    ns = {"__file__": str(INDEPENDENT), "__name__": "independent_fixture_reuse02"}
    exec(compile(tree, str(INDEPENDENT), "exec"), ns)
    ns["p"], ns["PROJECTOR"] = p, PROJECTOR
    independent = ns["main"]()
    base, external_bind = ns["base"], ns["external_bind"]
    added = []

    def status(result):
        s = result["provenance_sidecar"]
        return {key: s[key] for key in (
            "candidate_view_complete", "source_identity_metadata_complete",
            "external_manifest_binding_complete", "binding_complete_for_review",
            "actual_source_authentication_verified", "formal_model_input_ready")}

    def check(name, passed, details):
        added.append({"name": name, "passed": bool(passed), "details": details})

    partial_results = []
    for declaration in (
        {"source_path": "invented-other.txt"}, {"source_sha256": "4" * 64},
        {"unit_source": "invented-other.txt"}, {"unit_source_sha256": "4" * 64},
        {"candidate_path": "invented-other.json"}, {"candidate_sha256": "4" * 64},
        {"source_image": "invented-other.bin"}, {"source_image_sha256": "4" * 64},
    ):
        row, rule = base({"paragraph_context": [{"paragraph_id": "synthetic-p", "text": "全新构造段。", **declaration}]})
        result = external_bind(row, rule)
        partial_results.append({"declared_fields": list(declaration), "status": status(result),
                                "issues": result["provenance_sidecar"]["issues"]})
    check("path_only_and_hash_only_source_candidate_image_pairs_block", all(
        not item["status"]["source_identity_metadata_complete"]
        and not item["status"]["binding_complete_for_review"] for item in partial_results), partial_results)

    row, rule = base({"paragraph_context": [{"paragraph_id": "synthetic-p", "text": "构造完整子来源。",
                    "source_path": "invented-complete-child.txt", "source_sha256": "4" * 64,
                    "candidate_path": "invented-complete-child.json", "candidate_sha256": "5" * 64,
                    "source_image": "invented-complete-child.bin", "source_image_sha256": "6" * 64}]})
    result = external_bind(row, rule)
    origin = result["provenance_sidecar"]["policy_leaves"][-1]["source_binding"]
    check("complete_child_pairs_preserve_identity", origin["source_path"] == "invented-complete-child.txt"
          and origin["source_sha256"] == "4" * 64 and origin["source_image_sha256"] == "6" * 64
          and result["provenance_sidecar"]["binding_complete_for_review"], {"status": status(result), "origin": origin})

    bad_rows = []
    for index in ({"opinion": "DROP_INDEX_OPINION", "labels": {"F": 1}}, -1, True, "3", 1.0):
        row, rule = base({"verified_table_context_v4": [{"table_title": "构造表题", "column_names": ["构造列"],
                        "raw_row_cells": ["构造格"], "row_index_zero_based": index}]})
        result = external_bind(row, rule)
        nodes = result["model_visible_candidate"]["contexts"]
        valid = not result["provenance_sidecar"]["candidate_view_complete"] and all(
            "row_index_zero_based" not in n["structure"] for n in nodes)
        valid = valid and "DROP_INDEX_OPINION" not in json.dumps(result["model_visible_candidate"])
        bad_rows.append({"input_type": type(index).__name__, "passed": valid, "status": status(result)})
    check("only_nonnegative_integer_row_index_reaches_parent_and_cells", all(x["passed"] for x in bad_rows), bad_rows)

    empty_results = []
    for text in ("", " \t\n"):
        row, rule = base(text=text)
        result = external_bind(row, rule)
        empty_results.append(status(result))
    check("empty_and_whitespace_current_cannot_complete", all(not x["candidate_view_complete"]
          and not x["binding_complete_for_review"] for x in empty_results), empty_results)

    leaves = {"title": "构造实际标题。", "unit_text": "构造实际单元文字。", "definition": "构造实际定义。"}
    row, rule = base({"verified_scope_qualifications_v28": [{"paragraph_id": "synthetic-def", **leaves}]})
    result = external_bind(row, rule)
    found = list(validator.iter_context_text(result["model_visible_candidate"]["contexts"]))
    pointers = [x["raw_pointer"] for x in result["provenance_sidecar"]["policy_leaves"]]
    check("declared_title_unit_text_definition_are_quotable_distinct_leaves", all(x in found for x in leaves.values())
          and all(any(k.endswith('/' + key) for k in pointers) for key in leaves)
          and result["provenance_sidecar"]["candidate_view_complete"], {"status": status(result), "raw_pointers": pointers})

    malformed = []
    for field in ("title", "unit_text", "definition"):
        row, rule = base({"paragraph_context": [{"paragraph_id": "synthetic-bad", field: {"opinion": "DROP_FIELD_OPINION"}}]})
        result = external_bind(row, rule)
        malformed.append({"field": field, "status": status(result), "issues": result["provenance_sidecar"]["issues"]})
    check("malformed_declared_policy_leaf_cannot_silently_complete", all(not x["status"]["candidate_view_complete"]
          for x in malformed), malformed)

    unmapped = []
    for contexts in ({"title": "构造根字段。"}, {"paragraph_context": [{"unknown_container": {"definition": "构造未知容器。"}}]},
                     {"complete_following_list_v11": {"structure_boundary": {"definition": "构造未声明边界定义。"}}},
                     {"paragraph_context": "构造无对象家族。"}, {"paragraph_context": [{"contexts": "构造错误成员类型。"}]}):
        row, rule = base(contexts)
        result = external_bind(row, rule)
        unmapped.append({"status": status(result), "issues": result["provenance_sidecar"]["issues"]})
    check("undeclared_root_nested_boundary_or_structural_policy_fields_issue", all(
        not x["status"]["candidate_view_complete"] for x in unmapped), unmapped)

    row, rule = base({"verified_table_context_v4": [{"table_title": "构造原表名", "column_names": ["构造甲列", "构造乙列"],
                    "raw_row_cells": ["构造甲格", "构造乙格"], "row_index_zero_based": 0,
                    "text": "DROP_ASSEMBLED_CERTIFICATE", "unit_text": "DROP_AMBIGUOUS_JOINED_ROW"}]})
    result = external_bind(row, rule)
    payload = json.dumps(result["model_visible_candidate"])
    check("assembled_certificate_excluded_and_context_row_representation_unresolved", "DROP_" not in payload
          and not result["provenance_sidecar"]["candidate_view_complete"],
          {"status": status(result), "excluded_fields": result["provenance_sidecar"]["excluded_assembled_table_certificate_fields"],
           "issues": result["provenance_sidecar"]["issues"]})

    row, rule = base({"verified_table_context_v4": [{"table_title": "构造表名", "column_names": ["甲列", "乙列"],
                    "raw_row_cells": ["甲格", "乙格"], "row_index_zero_based": 0}]}, text="甲格 | 乙格")
    result = external_bind(row, rule)
    check("current_table_row_structure_representation_is_preserved", result["model_visible_candidate"]["text"] == "甲格 | 乙格"
          and result["provenance_sidecar"]["candidate_view_complete"]
          and not result["provenance_sidecar"]["actual_source_authentication_verified"], status(result))

    try:
        p.require_formal_model_input(result)
    except ValueError:
        guard_refused = True
    else:
        guard_refused = False
    check("external_registry_never_authenticates_or_authorizes_formal_input", result["provenance_sidecar"]["binding_complete_for_review"]
          and not result["provenance_sidecar"]["actual_source_authentication_verified"]
          and not result["provenance_sidecar"]["formal_model_input_ready"] and guard_refused, status(result))

    with tempfile.TemporaryDirectory(prefix="projection02-invented-") as tmp:
        sp, cp = Path(tmp)/"actual-invented-source.txt", Path(tmp)/"actual-invented-candidate.json"
        text = "全新临时构造文件句。"
        sp.write_text(text, encoding="utf-8")
        cp.write_text(json.dumps({"source": str(sp), "source_sha256": sha(sp),
                      "unit_candidates": [{"id": "invented-u1", "text": text}]}), encoding="utf-8")
        row, rule = base(text=text)
        rule["input"] = {"unit_text": text, "unit_source": str(sp), "unit_source_sha256": sha(sp),
                         "candidate_file": str(cp), "candidate_sha256": sha(cp)}
        result = external_bind(row, rule)
        checks = p.verify_manifest_files([{"path": str(sp), "sha256": sha(sp)}, {"path": str(cp), "sha256": sha(cp)},
                                         {"path": str(sp), "sha256": "0" * 64}])
        check("real_temporary_source_candidate_sha_checks_do_not_authenticate_leaf", [x["hash_equal"] for x in checks] == [True, True, False]
              and not result["provenance_sidecar"]["actual_source_authentication_verified"],
              {"hash_equal_results": [x["hash_equal"] for x in checks], "status": status(result)})

    malformed_arrays = []
    for fields in ({"headers": {"opinion": "DROP_ARRAY"}}, {"headers": ["a"], "column_names": ["b"]},
                   {"raw_row_cells": ["x"], "row_cells": ["y"]}):
        row, rule = base({"verified_table_context_v4": [{"row_index_zero_based": 0, **fields}]})
        result = external_bind(row, rule)
        malformed_arrays.append(status(result))
    check("malformed_or_conflicting_table_arrays_cannot_complete", all(not x["candidate_view_complete"] for x in malformed_arrays), malformed_arrays)

    assert sha(PROJECTOR) == code_sha and sha(OLD / PROJECTOR.name) == old_sha
    return {"schema_version": "projection02-invented-regressions-v1", "at_utc": datetime.now(timezone.utc).isoformat(),
            "projector_sha256": code_sha, "validator_sha256": sha(VALIDATOR), "runner_sha256": sha(__file__),
            "design_sha256": sha(HERE/"projection02_repair_design.json"),
            "source01_sha256_unchanged": old_sha,
            "independent_fixture_origin": {"path": str(INDEPENDENT), "sha256": sha(INDEPENDENT),
                "adaptation": "Only fixed expected code SHA AST literal replaced, target module/path injected; original fixture bodies and files unchanged."},
            "author13_reproduced": independent["author13_reproduced"],
            "independent6_reproduced": {"check_n": independent["executed_new_check_n"], "passed_n": independent["passed_new_check_n"],
                                        "results": independent["results"]},
            "additional_check_n": len(added), "additional_passed_n": sum(x["passed"] for x in added), "additional_results": added,
            "all_passed": independent["passed_new_check_n"] == 6 and all(x["passed"] for x in added),
            "scope": {"real_corpus_read_or_exported": False, "real_policy_source_or_protected_labels_read": False,
                      "model_or_rule_called": False, "formal_model_input_generated": False,
                      "source01_or_original_independent_files_modified": False},
            "authentication_note": "All external registries are invented interface fixtures. Real temporary file SHA checks establish bytes only, never actual leaf authenticity."}


if __name__ == "__main__":
    target = HERE / "projection02_constructed_results.json"
    result = run()
    with target.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"all_passed": result["all_passed"], "author_n": result["author13_reproduced"]["check_n"],
                      "independent_n": result["independent6_reproduced"]["check_n"],
                      "independent_passed_n": result["independent6_reproduced"]["passed_n"],
                      "additional_n": result["additional_check_n"], "additional_passed_n": result["additional_passed_n"],
                      "result_sha256": sha(target)}, ensure_ascii=False))
    if not result["all_passed"]:
        raise SystemExit(1)
