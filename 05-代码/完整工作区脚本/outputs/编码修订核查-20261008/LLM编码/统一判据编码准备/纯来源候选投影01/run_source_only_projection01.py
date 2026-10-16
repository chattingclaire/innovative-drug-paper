"""Authorized isolated source-only projection; no binder/coder/model imports."""
import copy
import hashlib
import importlib.util
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(stream, value):
    stream.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def pointer_value(row, pointer):
    value = row
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def raw_nodes(module, row):
    def walk(value, pointer):
        if isinstance(value, list):
            for i, item in enumerate(value):
                yield from walk(item, f"{pointer}/{i}")
        elif isinstance(value, dict):
            yield pointer, value
            for key in module.CHILDREN:
                if key in value:
                    yield from walk(value[key], f"{pointer}/{key}")
    for key, value in row["contexts"].items():
        if key == "verified_context_certificates" and isinstance(value, dict):
            for name, item in value.items():
                if name in module.KINDS:
                    yield from walk(item, f"/contexts/{key}/{name}")
        elif key in module.KINDS:
            yield from walk(value, f"/contexts/{key}")


def all_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from all_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_keys(item)


def mechanical(module, row, rule, result):
    visible, side = result["model_visible_candidate"], result["provenance_sidecar"]
    nodes = visible["contexts"]
    by_id = {n["context_id"]: n for n in nodes}
    failures = []
    def check(condition, code, pointer=None):
        if not condition:
            failures.append({"code": code, "raw_pointer": pointer})
    check(set(visible) == {"id", "text", "pages", "contexts"}, "unexpected_visible_top_keys")
    check(visible["id"] == row["id"], "current_id_changed")
    check(visible["text"] == row["text"] == rule["input"]["unit_text"], "current_text_changed")
    check(visible["pages"] == row.get("pages", []), "current_pages_changed")
    check(len(by_id) == len(nodes), "duplicate_context_id")
    forbidden = set(module.DROP) | {"source_title", "labels", "判定理由", "编码理由", "认证意见"}
    check(not (set(all_keys(visible)) & forbidden), "forbidden_key_visible")
    admitted_node = {"context_id", "kind", "source_document", "structure", "text", "definition", "title", "caption", "headers", "row_cells"}
    admitted_structure = set(module.LOCATORS) | {"parent_context_id", "sequence_index", "position", "text_child_context_ids", "table_text_context_ids", "child_groups", "column_index", "column_indices", "row_cell_column_pairs", "line", "physical_pages"}
    raw_by_context = {"CTX-" + module.sha_text(row["id"] + "\0" + p)[:20]: (p, obj) for p, obj in raw_nodes(module, row)}
    for n in nodes:
        check(set(n) <= admitted_node, "unexpected_context_key", n["context_id"])
        check(set(n["structure"]) <= admitted_structure, "unexpected_structure_key", n["context_id"])
        check(re.fullmatch(r"D-[0-9a-f]{16}|UNBOUND", n["source_document"]) is not None, "source_filename_or_invalid_document_id", n["context_id"])
        structure = n["structure"]
        refs = [structure["parent_context_id"]] if "parent_context_id" in structure else []
        refs += structure.get("text_child_context_ids", []) + structure.get("table_text_context_ids", [])
        for group in structure.get("child_groups", []):
            check(set(group) == {"position", "ordered_context_ids"}, "unexpected_child_group_key")
            refs += group["ordered_context_ids"]
        check(all(c in by_id for c in refs), "dangling_context_relation", n["context_id"])
        for field, keys in (("headers", ("column_names", "header_cells", "headers")), ("row_cells", ("raw_row_cells", "row_cells"))):
            if field in n:
                raw = raw_by_context.get(n["context_id"])
                selected = next((k for k in keys if raw and isinstance(raw[1].get(k), list)), None)
                check(raw is not None and selected is not None and n[field] == raw[1][selected], "table_array_changed", raw[0] if raw else n["context_id"])
    leaf_by_output = defaultdict(list)
    leaf_checks = []
    for leaf in side["policy_leaves"]:
        raw = pointer_value(row, leaf["raw_pointer"])
        check(isinstance(raw, str), "leaf_raw_value_not_string", leaf["raw_pointer"])
        exact_hash = isinstance(raw, str) and module.sha_text(raw) == leaf["text_sha256"] and len(raw) == leaf["character_n"]
        check(exact_hash, "raw_leaf_metadata_changed", leaf["raw_pointer"])
        owner = visible if leaf["context_id"] is None else by_id.get(leaf["context_id"], {})
        exact_emitted = owner.get(leaf["output_field"]) == raw
        check(exact_emitted, "visible_leaf_changed_or_absent", leaf["raw_pointer"])
        leaf_by_output[(leaf["context_id"], leaf["output_field"])].append(leaf)
        if "additional_output_occurrence" in leaf:
            a = leaf["additional_output_occurrence"]
            field, index = a["field"].split("/")
            check(by_id[a["context_id"]][field][int(index)] == raw, "additional_table_occurrence_changed", leaf["raw_pointer"])
        leaf_checks.append((leaf, exact_hash, exact_emitted))
    for n in nodes:
        for field in ("text", "title", "definition", "caption"):
            if field in n:
                check(len(leaf_by_output[(n["context_id"], field)]) == 1, "visible_policy_field_without_unique_raw_lineage", n["context_id"] + "/" + field)
    check(side["actual_source_authentication_verified"] is False and side["formal_model_input_ready"] is False, "authentication_or_formal_ready_promoted")
    check(all(x["binding_status"] == "unbound_policy_leaf_candidate" for x in side["policy_leaves"]), "unexpected_external_binding_without_registry")
    try:
        module.require_formal_model_input(result)
    except ValueError:
        pass
    else:
        check(False, "formal_accessor_did_not_refuse")
    return failures, leaf_checks, list(raw_by_context.values())


def run():
    contract_path = HERE / "execution_contract01.json"
    contract = json.loads(contract_path.read_text())
    identities = contract["inputs"]
    for key, entry in identities.items():
        assert sha(entry["path"]) == entry["sha256"], key
    spec = importlib.util.spec_from_file_location("authorized_source_only_projector04", identities["projector"]["path"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = dict(contract["artifacts"])
    names["omitted_declared_text_index"] = "omitted_declared_text_index01.jsonl"
    for name in names.values():
        if (HERE / name).exists():
            raise RuntimeError("Existing execution retained; no overwrite: " + name)
    totals = Counter()
    issue_occurrences = defaultdict(Counter)
    issue_records = defaultdict(lambda: defaultdict(set))
    seen, ordered_ids = set(), []
    with ExitStack() as stack:
        streams = {key: stack.enter_context((HERE / value).open("x", encoding="utf-8")) for key, value in names.items() if key != "summary"}
        rule_file = stack.enter_context(Path(identities["rule_inputs"]["path"]).open(encoding="utf-8"))
        llm_file = stack.enter_context(Path(identities["llm_inputs"]["path"]).open(encoding="utf-8"))
        for index, (rline, lline) in enumerate(itertools.zip_longest(rule_file, llm_file), 1):
            totals["input_record_n"] += 1
            row = rule = None
            try:
                assert rline is not None and lline is not None, "input length mismatch"
                rule, row = json.loads(rline), json.loads(lline)
                rid = row["id"]
                assert rid == rule["id"] and rid not in seen, "input ID order mismatch or duplicate"
                seen.add(rid); ordered_ids.append(rid)
                assert row["text"] == rule["input"]["unit_text"], "input current mismatch"
                assert row["contexts"] == rule["input"]["llm_v29_shared_context"], "shared context mismatch"
                original = copy.deepcopy((row, rule))
                result = module.project_record(row, rule)
                failures, leaf_checks, declared_nodes = mechanical(module, row, rule, result)
                if (row, rule) != original:
                    failures.append({"code": "input_object_mutated", "raw_pointer": None})
                visible, side = result["model_visible_candidate"], result["provenance_sidecar"]
                write(streams["candidate"], visible)
                write(streams["sidecar"], side)
                totals["projected_record_n"] += 1
                totals["context_node_n"] += len(visible["contexts"])
                for axis in ("candidate_view_complete", "source_identity_metadata_complete", "external_manifest_binding_complete", "binding_complete_for_review"):
                    totals[axis + ":" + str(side[axis]).lower()] += 1
                for leaf_number, (leaf, exact_hash, exact_emitted) in enumerate(leaf_checks, 1):
                    write(streams["leaf_index"], {"record_index_one_based": index, "id": rid, "leaf_index_within_record_one_based": leaf_number, **leaf,
                          "raw_string_metadata_exact": exact_hash, "emitted_string_exact": exact_emitted})
                    totals["policy_leaf_occurrence_n"] += 1
                    totals["unbound_policy_leaf_occurrence_n"] += leaf["binding_status"] == "unbound_policy_leaf_candidate"
                for issue_number, issue in enumerate(side["issues"], 1):
                    write(streams["issues"], {"record_index_one_based": index, "id": rid, "issue_index_within_record_one_based": issue_number, **issue})
                    issue_occurrences[issue["category"]][issue["code"]] += 1
                    issue_records[issue["category"]][issue["code"]].add(rid)
                for pointer, obj in declared_nodes:
                    for key in module.AMBIGUOUS_TEXT:
                        value = obj.get(key)
                        raw_pointer = pointer + "/" + key
                        if isinstance(value, str) and value.strip():
                            write(streams["omitted_declared_text_index"], {"record_index_one_based": index, "id": rid, "raw_pointer": raw_pointer,
                                  "text_sha256": module.sha_text(value), "character_n": len(value),
                                  "registered_policy_leaf": any(x[0]["raw_pointer"] == raw_pointer for x in leaf_checks),
                                  "emitted": any(n.get("text") == value and n["context_id"] == module.Projector(rid).context_id(raw_pointer) for n in visible["contexts"]),
                                  "status": "declared_scalar_boundary_requires_literal_binding_not_authenticated"})
                            totals["declared_nonblank_scalar_boundary_occurrence_n"] += 1
                write(streams["mechanical_checks"], {"record_index_one_based": index, "id": rid, "passed": not failures, "failures": failures,
                      "current_id_text_and_shared_context_exact": True, "policy_leaf_n": len(leaf_checks),
                      "formal_accessor_refused": not any(x["code"] == "formal_accessor_did_not_refuse" for x in failures)})
                totals["mechanical_pass_record_n" if not failures else "mechanical_fail_record_n"] += 1
            except Exception as exc:
                totals["exception_record_n"] += 1
                write(streams["exceptions"], {"record_index_one_based": index, "id": row.get("id") if isinstance(row, dict) else None,
                      "error_type": type(exc).__name__, "message": str(exc), "projected_record_not_claimed_complete": True})
    preserved = {key: {"path": entry["path"], "expected_sha256": entry["sha256"], "actual_sha256": sha(entry["path"]), "unchanged": sha(entry["path"]) == entry["sha256"]} for key, entry in identities.items()}
    summary = {"schema": "source-only-real4924-projection-summary01-v1", "at_utc": datetime.now(timezone.utc).isoformat(),
        "contract_sha256": sha(contract_path), "driver_sha256": sha(__file__), "totals": dict(totals),
        "issue_counts_by_category_code": {cat: {code: {"occurrence_n": n, "distinct_record_n": len(issue_records[cat][code])} for code, n in counts.items()} for cat, counts in issue_occurrences.items()},
        "ordered_input_ids_sha256": module.sha_text(json.dumps(ordered_ids, ensure_ascii=False, separators=(",", ":"))),
        "all4924_ordered_unique_projected": totals["input_record_n"] == totals["projected_record_n"] == len(seen) == contract["expected_record_n"] and not totals["exception_record_n"],
        "all_mechanical_checks_passed": totals["mechanical_pass_record_n"] == contract["expected_record_n"] and not totals["mechanical_fail_record_n"] and not totals["exception_record_n"],
        "input_and_dependency_preservation": preserved, "all_inputs_and_dependencies_unchanged": all(x["unchanged"] for x in preserved.values()),
        "actual_authorized_source_only_candidate_projection_performed": True, "formal_model_packet_generated": False,
        "actual_source_authentication_verified": False, "formal_model_input_ready": False,
        "binder_called": False, "model_called": False, "rule_called": False, "labels_or_manuscript_modified": False,
        "leaf_denominator": "Projector registered leaf occurrences only; omitted scalar boundaries separately indexed, no assumed authentic source coverage.",
        "mechanical_scope": "Exact raw-pointer lineage and forbidden visible schema keys, neutral structure/document-ID schema, input preservation and formal accessor refusal; not semantic review or source authentication.",
        "legacy_full_export_flag": "04 sidecar flag retained false unchanged; actual isolated candidate projection recorded separately here.",
        "artifacts": {key: {"path": str(HERE / value), "sha256": sha(HERE / value)} for key, value in names.items() if key != "summary"}}
    (HERE / names["summary"]).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = run()
    print(json.dumps({"totals": result["totals"], "all_mechanical_checks_passed": result["all_mechanical_checks_passed"],
                      "all4924_ordered_unique_projected": result["all4924_ordered_unique_projected"],
                      "issue_counts_by_category_code": result["issue_counts_by_category_code"]}, ensure_ascii=False))
