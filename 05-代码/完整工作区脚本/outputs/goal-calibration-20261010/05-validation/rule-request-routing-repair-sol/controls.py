"""Constructed routing controls; exact code allowlist, no real cohort inputs."""
import ast
import copy
import difflib
import hashlib
import json
import os
import sys
import traceback
import types
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "06-coding/rule-v18-overall-health-boundary-development-root"
DRIVER_BASE = ROOT / "05-validation/rule-driver-exception-audit-v2-sol"
OUTPUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else "control-results-attempt01.json")
if OUTPUT.parent != HERE or OUTPUT.exists():
    raise ValueError("distinct new control output required")
allowed = {HERE / name for name in (
    "controls.py", "source_packet.py", "source_receipts.py", "evidence.py", "relations.py",
    "dimensions.py", "rule_driver.py", "interface_common.py", "algorithm-bindings.json",
    "formal-manual-binding.json", "input-bindings.json")}
allowed |= {BASE / name for name in (
    "source_packet.py", "source_receipts.py", "evidence.py", "relations.py", "dimensions.py")}
allowed.add(DRIVER_BASE / "rule_driver.py")
stdlib = Path(os.__file__).resolve().parent
reads = []


def audit(event, args):
    if event != "open" or not args or isinstance(args[0], int):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    mode = args[1] if len(args) > 1 else None
    flags = args[2] if len(args) > 2 else 0
    writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(
        flags and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
    if writing:
        if path.parent != HERE:
            raise PermissionError("control write outside isolated candidate directory")
    else:
        if path not in allowed and stdlib not in path.parents:
            raise PermissionError("control read outside exact code allowlist: " + str(path))
        reads.append(str(path))


sys.addaudithook(audit)


def load_module(name, path):
    module = types.ModuleType(name)
    module.__file__, module.__package__ = str(path), ""
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


mods = {name: load_module(name, HERE / (name + ".py")) for name in (
    "source_packet", "source_receipts", "evidence", "relations", "dimensions")}
baseline = load_module("baseline_dimensions", BASE / "dimensions.py")
judge = mods["dimensions"].judge
validate = mods["evidence"].validate_decisions
RelationView = mods["relations"].RelationView
semantic_unit = mods["source_packet"].semantic_unit
DIMS = mods["dimensions"].DIMENSIONS
results = []
cases = []


def check(name, passed, details=None):
    results.append({"name": name, "passed": bool(passed), "details": details})


def funcs(text):
    return {node.name: node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}


def ast_sha(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


old_dim = (BASE / "dimensions.py").read_text()
new_dim = (HERE / "dimensions.py").read_text()
old_funcs, new_funcs = funcs(old_dim), funcs(new_dim)
predicate_names = ["_units", "_object", "_generic", "_safety_effect", "_economics", "_classification",
                   "_finite_reference_qualification", "_innovation_qualification", "_innovation", "_fairness", "judge"]
predicate_bindings = []
for name in predicate_names:
    a, b = ast_sha(old_funcs[name]), ast_sha(new_funcs[name])
    predicate_bindings.append({"function": name, "original_AST_sha256": a, "candidate_AST_sha256": b})
    check("positive_predicate_AST_unchanged:" + name, a == b)
check("all_original_top_level_functions_AST_unchanged", all(
    ast_sha(old_funcs[name]) == ast_sha(new_funcs[name]) for name in old_funcs))
old_classes = {node.name: node for node in ast.parse(old_dim).body if isinstance(node, ast.ClassDef)}
new_classes = {node.name: node for node in ast.parse(new_dim).body if isinstance(node, ast.ClassDef)}
check("semantic_Unit_AST_unchanged", ast_sha(old_classes["Unit"]) == ast_sha(new_classes["Unit"]))
for name in ("add", "exclude", "request", "error"):
    before_method = next(node for node in old_classes["Accumulator"].body if isinstance(node, ast.FunctionDef) and node.name == name)
    after_method = next(node for node in new_classes["Accumulator"].body if isinstance(node, ast.FunctionDef) and node.name == name)
    check("positive_accumulation_method_AST_unchanged:" + name, ast_sha(before_method) == ast_sha(after_method))
old_assigns = [node for node in ast.parse(old_dim).body if isinstance(node, ast.Assign)]
new_assigns = {tuple(ast.dump(target, include_attributes=False) for target in node.targets): node
               for node in ast.parse(new_dim).body if isinstance(node, ast.Assign)}
check("all_original_topic_and_threshold_constants_AST_unchanged", all(
    ast_sha(node) == ast_sha(new_assigns[tuple(ast.dump(target, include_attributes=False) for target in node.targets)]) for node in old_assigns))
for name in ("source_packet.py", "source_receipts.py", "evidence.py", "relations.py"):
    check("unchanged_algorithm_module:" + name, (BASE / name).read_bytes() == (HERE / name).read_bytes())

old_driver = (DRIVER_BASE / "rule_driver.py").read_text()
new_driver = (HERE / "rule_driver.py").read_text()
old_driver_funcs, new_driver_funcs = funcs(old_driver), funcs(new_driver)
for name in old_driver_funcs:
    if name != "main":
        check("driver_function_AST_unchanged:" + name, ast_sha(old_driver_funcs[name]) == ast_sha(new_driver_funcs[name]))


def guard_text(text):
    start = text.index("            if stops:\n")
    end = text.index("            prediction.update(labels=", start)
    return text[start:end]


guard = guard_text(new_driver)
check("dependency_guard_exact_bytes_unchanged", guard == guard_text(old_driver))
guard_code = compile("\n".join(line[12:] for line in guard.splitlines()), str(HERE / "rule_driver.py") + ":constructed_guard", "exec")
required_guards = [
    "raise ValueError('first output exists; use a distinct authorized round, never overwrite')",
    "if scope.get('max_actual_cohort_inference_runs')!=1:",
    "if target.name=='reference.jsonl' or '/04-calibration/' in str(target):raise PermissionError('reference/calibration prohibited')",
    "if target not in allowed and out not in target.parents and stdlib not in target.parents:raise PermissionError('unapproved read '+str(target))",
]
for text in required_guards:
    check("driver_scope_guard_preserved:" + hashlib.sha256(text.encode()).hexdigest()[:12], text in new_driver)
ns = {"copy": copy, "hashlib": hashlib, "DIMENSIONS": DIMS,
      "cj": lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)}
audit_nodes = ast.Module(body=[new_driver_funcs["capture_exception_source_audit"], new_driver_funcs["dimension_slots"]], type_ignores=[])
exec(compile(ast.fix_missing_locations(audit_nodes), str(HERE / "rule_driver.py") + ":constructed_helpers", "exec"), ns)
capture, slots = ns["capture_exception_source_audit"], ns["dimension_slots"]


def bundle(current, contexts=None):
    sha = hashlib.sha256(("constructed-source:" + current).encode()).hexdigest()
    ref = {"sha256": sha, "source_resource_id": "CONSTRUCTED-SOURCE", "locator": {}}
    return {"common_source_bundle_version": "constructed-control-not-study",
            "source_record": {"id": "CONSTRUCTED", "text": current, "source_ref": ref, "contexts": contexts or []},
            "source_documents": [], "explicit_or_primary_source_resources": [],
            "preserved_historical_neutral_source_supplements": [], "source_full_text_resources": [],
            "source_asset_locations": [], "source_locator_bases": {}, "source_reference_index": [], "source_provenance_addenda": []}


def context(cid, kind, text, ref, structure=None):
    return {"context_id": cid, "kind": kind, "text": text,
            "source_document": ref["source_resource_id"], "source_ref": copy.deepcopy(ref), "structure": structure or {}}


def values(decisions):
    return {dim: decisions[dim]["value"] for dim in DIMS}


def run_case(name, b, expected, expected_request_paths=None):
    view = RelationView(semantic_unit(b))
    before = baseline.judge(view)
    after = judge(view)
    validate(view.unit, after)
    if view.material_requests:
        exec(guard_code, {"view": view, "decisions": after, "stops": ["required_reference_unresolved"]})
    passed = values(after) == expected
    if expected_request_paths is not None:
        passed = passed and {r["path"] for r in view.material_requests} == set(expected_request_paths)
    case = {"name": name, "constructed_bundle": b, "baseline_values": values(before), "candidate_values": values(after),
            "expected_from_constructed_contract": expected, "requests": copy.deepcopy(view.material_requests),
            "relation_kinds": [r["kind"] for r in view.relations], "decisions": after,
            "passed": passed, "constructed_only": True, "real_cohort_inference": False}
    cases.append(case)
    check(name, passed)
    dimension_rows = slots([{"source_record": {"id": "CONSTRUCTED"}}], [{
        "id": "CONSTRUCTED", "labels": values(after), "decisions": after, "implementation_errors": []}], [])
    check(name + ":valid_output_masks", all(
        not row["technical_failure"] and row["comparison_eligible"] and
        row["rules_null"] == (after[row["dimension"]]["value"] is None) and
        row["rule_value"] == after[row["dimension"]]["value"] for row in dimension_rows))
    for dim in DIMS:
        if after[dim]["value"] is None:
            check(name + ":lawful_null_reason:" + dim,
                  bool(after[dim]["needed_material"]) and bool(after[dim]["reason"]) and
                  all(r.get("missing", "") in after[dim]["reason"] for r in after[dim]["needed_material"] if isinstance(r, dict)))
    return view, before, after


all_null = {dim: None for dim in DIMS}
current_list = "药品应提供以下内容。"
run_case("missing_list_without_current_topic_words", bundle(current_list), all_null, ["substantive_list"])

full_list = bundle(current_list)
ref = full_list["source_record"]["source_ref"]
member_ids = ["CONSTRUCTED-MEMBER-" + dim for dim in DIMS]
full_list["source_record"]["contexts"] = [
    context("CONSTRUCTED-LIST", "ordered_list", "有序内容组", ref,
            {"child_groups": [{"position": "ordered_members", "ordered_context_ids": ["CONSTRUCTED-HEAD"] + member_ids}]}),
    context("CONSTRUCTED-HEAD", "ordered_members", current_list, ref),
] + [context(cid, "ordered_members", topic + "。", ref)
     for cid, topic in zip(member_ids, ["安全性", "有效性", "经济性", "创新性", "公平性"])]
run_case("closed_list_has_actual_five_consumers", full_list, {dim: 1 for dim in DIMS}, [])

current_standard = "药品符合该标准条件可以申请待遇。"
run_case("missing_standard_without_current_topic_words", bundle(current_standard), all_null, ["cited_standard"])
full_standard = bundle("审核该标准条件，药品可以申请适用支持试点。")
ref = full_standard["source_record"]["source_ref"]
full_standard["source_record"]["contexts"] = [
    context("CONSTRUCTED-RELATION", "structural_relation", "有界关联", ref,
            {"related_context_ids": ["CONSTRUCTED-STANDARD"]}),
    context("CONSTRUCTED-STANDARD", "source_paragraph",
            "药品可以申请适用支持试点，用于审核资格，条件包括安全性、有效性、经济性、创新性及公平性资料。", ref),
]
run_case("closed_standard_has_actual_five_consumers", full_standard, {dim: 1 for dim in DIMS}, [])

article = bundle("符合第八条条件的药品可以获得许可。")
ref = article["source_record"]["source_ref"]
article["source_record"]["contexts"] = [context("CONSTRUCTED-CURRENT", "paragraph", article["source_record"]["text"], ref)]
run_case("missing_finite_article_keeps_unknown_payload", article, all_null, ["cited_standard"])

named_current = "实施创新药研发支持试点。"
named_missing, _, _ = run_case("missing_named_mechanism_routes_I_and_F", bundle(named_current),
                             {"S": 0, "E": 0, "Ec": 0, "I": None, "F": None}, ["named_mechanism"])
named_full = bundle(named_current)
ref = copy.deepcopy(named_full["source_record"]["source_ref"])
ref["metadata"] = {"document_title": "创新药研发支持试点"}
named_full["source_record"]["contexts"] = [context("CONSTRUCTED-MECHANISM", "external_source",
    "本试点适用于创新药研发，针对尚无有效治疗药物的患者需求。可申请研究方案反馈技术服务。加快审评并给予优先审评。", ref)]
nv, nb, na = run_case("closed_named_mechanism_has_actual_I_F_predicates", named_full,
                     {"S": 0, "E": 0, "Ec": 0, "I": 1, "F": 1}, [])
check("named_F_witness_uses_named_mechanism_relation", na["F"]["details"].get("relation_kind") == "named_mechanism")
check("named_S_E_Ec_do_not_consume_quoted_missing_mechanism", all(na[dim]["value"] == 0 for dim in ("S", "E", "Ec")))

partial = "药品应提供以下内容；应评估药品安全性。"
pv, pb, pa = run_case("independent_S_positive_survives_unknown_list", bundle(partial),
                     {"S": 1, "E": None, "Ec": None, "I": None, "F": None}, ["substantive_list"])
check("independent_S_keeps_original_evidence_and_reason", all(pa["S"][key] == pb["S"][key] for key in (
    "value", "basis_path", "current_anchor", "current_proposition", "context_evidence", "reason")))
check("independent_S_audits_exact_request_with_empty_needed_material", pa["S"]["needed_material"] == [] and
      pa["S"]["details"]["unresolved_material_requests"] == pv.material_requests)

all_positive = "药品应提供以下内容；应提供药品安全性、有效性、经济性、创新性及公平性评价资料。"
av, ab, aa = run_case("all_independent_positive_labels_preserved", bundle(all_positive), {dim: 1 for dim in DIMS}, ["substantive_list"])
check("all_positive_original_anchors_propositions_and_reasons_preserved", all(
    aa[dim][key] == ab[dim][key] for dim in DIMS for key in (
        "value", "basis_path", "current_anchor", "current_proposition", "context_evidence", "reason")))

for name, current in (
    ("no_dependency_direct_safety", "应核对用药禁忌，预防用药差错。"),
    ("no_dependency_direct_efficacy", "应评估该药对患者整体健康水平的影响。"),
    ("no_dependency_purpose_boundary", "为保障患者用药安全，制定本规范。"),
    ("no_dependency_administrative_content", "药品资料应完成归档。"),
):
    view = RelationView(semantic_unit(bundle(current)))
    before, after = baseline.judge(view), judge(view)
    validate(view.unit, after)
    check(name + ":unchanged_values", values(before) == values(after) and not view.material_requests)

explicit = copy.deepcopy(named_missing)
explicit.material_requests[0]["dimensions"] = ["I"]
explicit.source_requests = [dict(explicit.material_requests[0], dependency_status="stopped")]
ex = judge(explicit)
validate(explicit.unit, ex)
exec(guard_code, {"view": explicit, "decisions": ex, "stops": ["required_reference_unresolved"]})
check("valid_explicit_consumer_subset_does_not_null_unaffected_dimension", values(ex) == {"S": 0, "E": 0, "Ec": 0, "I": None, "F": 0})


def exception_result(view, error, diagnostic=None):
    prediction = {"id": "CONSTRUCTED", "labels": None, "decisions": None,
                  "implementation_errors": [{"type": type(error).__name__, "message": str(error)}]}
    if diagnostic is not None:
        prediction["candidate_decisions_diagnostic_only"] = diagnostic
    snap = capture(view, error, None, None, "not_started")
    prediction.update(copy.deepcopy(snap))
    dimension_rows = slots([{"source_record": {"id": "CONSTRUCTED"}}], [prediction], [])
    return prediction, snap, dimension_rows


bad_requests = [
    ("unknown_path", {"path": "unmapped_relation", "reference": "构造确指", "missing": "构造来源关系不能闭合"}),
    ("non_object_request", "构造格式错误"),
    ("missing_concrete_content", {"path": "cited_standard", "reference": "构造确指"}),
    ("string_dimensions", {"path": "cited_standard", "reference": "构造确指", "missing": "有界条件原文缺失", "dimensions": "S"}),
    ("empty_explicit_dimensions", {"path": "cited_standard", "reference": "构造确指", "missing": "有界条件原文缺失", "dimensions": []}),
    ("unknown_explicit_dimension", {"path": "cited_standard", "reference": "构造确指", "missing": "有界条件原文缺失", "dimensions": ["Z"]}),
    ("incompatible_consumer_dimension", {"path": "named_mechanism", "reference": "构造确指", "missing": "直接机制原文缺失", "dimensions": ["S"]}),
    ("conflicting_explicit_dimension_fields", {"path": "named_mechanism", "reference": "构造确指", "missing": "直接机制原文缺失", "dimensions": ["I"], "affected_dimensions": ["F"]}),
    ("resolved_request_not_unresolved_dependency", {"path": "cited_standard", "reference": "构造确指", "missing": "有界条件原文缺失", "status": "resolved"}),
    ("nonnecessary_request_cannot_create_null", {"path": "cited_standard", "reference": "构造确指", "missing": "有界条件原文缺失", "necessary_dependency": False}),
]
for name, request in bad_requests:
    view = RelationView(semantic_unit(bundle("药品资料完成归档。")))
    view.material_requests = [copy.deepcopy(request)]
    view.source_requests = [dict(request, dependency_status="stopped")] if isinstance(request, dict) else [request]
    try:
        judge(view)
    except mods["dimensions"].MaterialRequestRoutingError as error:
        pred, snap, dimension_rows = exception_result(view, error)
        check(name + ":technical_failure_retains_exact_request", snap["material_requests"] == [request] and
              pred["labels"] is None and all(row["technical_failure"] and not row["rules_null"] and
              row["rule_value"] is None and not row["comparison_eligible"] for row in dimension_rows), str(error))
    else:
        check(name + ":technical_failure_retains_exact_request", False)

# The original guard still rejects unpropagated diagnostic zeros.
zero_view = types.SimpleNamespace(material_requests=[{"path": "unmapped_relation", "reference": "构造确指", "missing": "构造缺失"}],
                                 source_requests=[{"status": "unresolved", "necessary_dependency": True}])
zeros = {dim: {"value": 0, "needed_material": [], "details": {}} for dim in DIMS}
try:
    exec(guard_code, {"view": zero_view, "decisions": zeros, "stops": ["required_reference_unresolved"]})
except ValueError as error:
    pred, snap, dimension_rows = exception_result(zero_view, error, zeros)
    check("unpropagated_diagnostic_zeros_remain_five_technical_failures", pred["labels"] is None and
          all(row["technical_failure"] and row["rule_value"] is None and not row["rules_null"] for row in dimension_rows))
else:
    check("unpropagated_diagnostic_zeros_remain_five_technical_failures", False)

malformed = bundle("药品资料完成归档。")
malformed["source_full_text_resources"] = [{"paragraphs": [{"text": 7}]}]
try:
    unit = semantic_unit(malformed)
except mods["source_packet"].PacketInterfaceError as error:
    pred, snap, dimension_rows = exception_result(None, error)
    check("source_parser_failure_is_technical_not_absent_predicate", pred["labels"] is None and
          all(row["technical_failure"] and not row["rules_null"] for row in dimension_rows), str(error))
    check("unproduced_source_log_not_reconstructed", snap["uniform_source_reading_log"] is None and
          snap["uniform_source_audit_state"]["log"] == "not_produced")
else:
    check("source_parser_failure_is_technical_not_absent_predicate", False)

parse_error_view = RelationView(semantic_unit(bundle("应评估药品有效性。")))
parse_error_view.implementation_errors = [{"dimensions": ["E"], "error": "constructed_relation_parse_failure"}]
try:
    judge(parse_error_view)
except ValueError as error:
    pred, snap, dimension_rows = exception_result(parse_error_view, error)
    check("relation_parse_error_not_swallowed_by_independent_positive", all(row["technical_failure"] for row in dimension_rows))
else:
    check("relation_parse_error_not_swallowed_by_independent_positive", False)

returned_log = {"constructed": "returned", "source_requests": copy.deepcopy(pv.source_requests)}
returned_check = {"errors": [], "dependency_stop_reasons": ["required_reference_unresolved"]}
snapshot = capture(pv, ValueError("constructed"), returned_log, returned_check, "returned")
before_snapshot = copy.deepcopy(snapshot)
pv.material_requests[0]["missing"] = "后续构造变异"
returned_log["constructed"] = "mutated"
check("exception_snapshot_is_deep_copy_of_live_and_returned_audit", snapshot == before_snapshot and
      snapshot["uniform_source_protocol_check"] == returned_check)
start = new_driver.index("            exception_audit = capture_exception_source_audit(")
end = new_driver.index("\n        predictions.append(prediction)", start)
exception_branch = "\n".join(line[12:] for line in new_driver[start:end].splitlines())
exception_local = {"capture_exception_source_audit": capture, "copy": copy, "view": pv,
                   "error": ValueError("constructed exception branch"), "source_log": returned_log,
                   "source_check": returned_check, "source_log_stage": "returned",
                   "prediction": {"id": "CONSTRUCTED", "labels": None, "decisions": None},
                   "row": {"id": "CONSTRUCTED"}, "detail": {"type": "ValueError"}, "consumption_logs": []}
exec(compile(exception_branch, str(HERE / "rule_driver.py") + ":constructed_exception_branch", "exec"), exception_local)
saved = exception_local["consumption_logs"][0]
check("exact_driver_exception_branch_preserves_requests_events_and_returned_log", all(
    saved[key] == getattr(pv, key) for key in ("source_requests", "material_requests", "source_view_events", "source_relation_traces")) and
    saved["uniform_source_reading_log"] == returned_log and saved["uniform_source_protocol_check"] == returned_check)
building = capture(pv, ValueError("constructed"), None, None, "building")
check("failed_before_return_log_stays_unknown", building["uniform_source_reading_log"] is None and
      building["uniform_source_audit_state"]["log"] == "not_returned_to_driver")

result = {"scope": "finite constructed interface and semantic-consumer witnesses only", "actual_cohort_runs": 0,
          "real_material_or_Gold_or_labels_read": False, "formal_validation_complete": False,
          "positive_predicate_AST_bindings": predicate_bindings,
          "guard_sha256": hashlib.sha256(guard.encode()).hexdigest(),
          "consumer_contract": mods["dimensions"].MATERIAL_REQUEST_CONSUMERS,
          "cases": cases, "controls": results, "controls_N": len(results),
          "passed": all(row["passed"] for row in results), "runtime_read_paths": sorted(set(reads))}
with OUTPUT.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
print(json.dumps({"controls_N": result["controls_N"], "passed": result["passed"],
                  "failed": [row["name"] for row in results if not row["passed"]], "actual_cohort_runs": 0}, ensure_ascii=False))
raise SystemExit(0 if result["passed"] else 2)
