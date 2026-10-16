"""Prepare metadata, readonly inputs and future slots; never invoke Codex."""
import argparse
import copy
from pathlib import Path
import jsonschema
from transport_common import HERE, BASE, PYTHON, CONDITIONS, REQUIRED_KEYS, now, binding, check, load, put, save

OLD = BASE / "06-coding/current-freeze-stability800-v1-root"

def prepare(run):
    run = Path(run).resolve()
    if run.exists():
        raise ValueError("Use a new campaign path; preserve partial preparations")
    old = load(OLD / "run-manifest.json")
    check(load(OLD / "preparation-seal.json")["run_manifest"])
    ids = load(old["ordered_source_ids"]["path"])
    if old["conditions"] != list(CONDITIONS) or len(ids) != len(set(ids)) or len(ids) != 800 or len(old["batches"]) != 87:
        raise ValueError("Old fixed scope changed")
    run.mkdir()
    scope = save(run / "input-scope.json", {"run_id": run.name, "scope": "fixed800 machine diagnostic with independent R1/R2/R3 and W/H sensitivity; no human assignment or truth claim", "context_unit": "batch", "record_N": 800, "batch_N": 87, "old_manifest": binding(OLD / "run-manifest.json"), "manual": old["manual"], "execution_prompt": old["execution_prompt"], "protocol": old["protocol"], "P_is_any_R": False, "full_source_order_identity_only": old["ordered_source_ids"], "reading_or_completion_receipt": False})
    contract = save(run / "transport-delivery-contract.json", {"artifact_type": "prospective_ROOT_external_capture_transport_contract", "run_id": run.name, "template_only": False, "actual_model_calls_at_freeze": 0, "context_unit": "batch", "model_visible_condition_attempt_route": False, "first_origin": "exact_original_CLI_output_last_message_UTF8_bytes", "first_is_actor_created_file": False, "report_seal_issuer": "ROOT_transport", "provider_wire_claimed": False, "actual_serving_model_verified": False, "first_JSON_schema_unchanged_except_campaign_identity": True, "earliest_valid_whole_batch": True, "no_cross_attempt_splicing": True, "legal_null_is_valid_and_terminal": True, "max_total_technical_attempts": 3, "max_concurrent_CLI": 3, "all_five_terminal_before_statistics": True, "delivery_rule": "Actor final message is exactly one whole-batch JSON object; ROOT preserves capture raw bytes, writes separate transport report/seal/receipt. Conditions and attempts exist only in external ledger.", "actual_text_read_rule": "Bounded helper PRESENTATION payload must occur in completed real command event before the single first candidate; declared manual/prompt/all-packet ranges cover the entire bound UTF8 input. Hash/load is not semantic reading; raw event does not authenticate provider delivery/context."})
    actor = binding(HERE / "actor-capture-instructions.txt")
    helper = binding(HERE / "read_allowed.py")
    validator = binding(HERE / "capture-validator.py")
    templates = {}
    for key, name in [("read_manifest_template", "read-manifest"), ("output_seal_template", "ROOT-output-seal"), ("technical_failure_template", "ROOT-technical-failure")]:
        templates[key] = save(run / "templates" / (name + ".template.json"), {"artifact_type": name + "_empty_template", "run_id": run.name, "template_only": True, "actual_completion_claimed": False, "issuer": "ROOT_transport" if key != "read_manifest_template" else "actor_actual_read_declaration_only", "not_a_receipt": True})
    rows, routes = [], []
    input_files = [scope, contract, actor, helper, *templates.values()]
    for oldrow in old["batches"]:
        n = int(oldrow["batch_id"].rsplit("-", 1)[1])
        rawdir = run / "batches" / oldrow["batch_id"]
        forms = {}
        for form in ("raw", "W"):
            check(oldrow["assignments"][form])
            a = copy.deepcopy(load(oldrow["assignments"][form]["path"]))
            directory = rawdir if form == "raw" else rawdir / "W-material"
            schema = copy.deepcopy(load(a["output_schema"]["path"]))
            schema["properties"]["run_id"] = {"const": run.name}
            schema["title"] = "ROOT captured frozen diagnostic whole-batch first JSON"
            jsonschema.Draft202012Validator.check_schema(schema)
            sb = save(directory / "output.schema.json", schema)
            validation = copy.deepcopy(load(a["output_validation_contract"]["path"]))
            validation.update(run_id=run.name, output_schema_binding=sb, attempt_output_routing=contract, strict_technical_validator=validator, first_origin="ROOT_capture_of_original_final_message_not_actor_file", actor_created_report_or_seal_required=False)
            vb = save(directory / "output-validation-contract.json", validation)
            retention = save(directory / "response-retention-policy.json", {"run_id": run.name, "first_capture_original_bytes": True, "capture_requires_one_complete_JSON_final_message": True, "first_is_not_provider_wire": True, "report_seal_issuer": "ROOT_transport", "no_actor_output_files_expected": True, "no_reserialization_or_repair": True, "max_actual_attempts": 3, "null_or_disagreement_retry": False, "whole_batch_first_valid_selection": True, "no_member_splicing": True})
            a.update(run_id=run.name, state="prepared_no_actual_dispatch", output_directory=str(directory), actor_instructions=actor, output_schema=sb, output_validation_contract=vb, strict_technical_validator=validator, response_retention_policy=retention, attempt_output_routing=contract, campaign_scope_metadata_binding=scope, transport_helper_binding=helper, transport_common_binding=binding(HERE / "transport_common.py"), **templates)
            for key in ("original_assignment_binding", "recovery_round"):
                a.pop(key, None)
            forms[form] = save(directory / "assignment.json", a)
            input_files.extend([sb, vb, retention, forms[form]])
            # No route/condition/attempt/outputslot path is present in the assignment.
            for condition in (("R1", "R2", "R3", "H") if form == "raw" else ("W",)):
                selection = directory / "ROOT-output" / condition
                for attempt in (1, 2, 3):
                    slot = selection / f"attempt-{attempt:04d}"
                    slot.mkdir(parents=True)
                    routes.append({"condition": condition, "batch_number": n, "batch_id": a["batch_id"], "attempt_number": attempt, "selection_directory": str(selection), "output_directory": str(slot), "working_directory": str(directory), "assignment": forms[form], "reservation_only": True})
        # Relative assignment path is identical for R/W/H. W differs only in
        # bound packet display and the nonsemantic file identities of that form.
        core = ("你是本批fresh政策文本编码执行者。先实际完整读 ./assignment.json 及其绑定的运输说明、manual、execution_prompt、共同protocol、output_schema，再按assignment顺序完整读每个packet及必要受限语境。\n"
                "本批唯一有效assignment是当前只读工作目录内的 ./assignment.json。只处理该完整批次，context_unit=batch，不读取其他材料或既有结果。\n"
                "本运输层使用外部final-message捕获：最终消息仅一个严格完整JSON首答对象，不写first/report/seal文件，不加围栏或说明，不自行修正或再答。ROOT另机械封存，条件/attempt/路由不向你提供。合法null保留。\n"
                "UTF8文本实际读取使用绑定helper：" + PYTHON + " " + helper["path"] + " --assignment ./assignment.json --path '<实际绑定文件绝对路径>' --start <Unicode起点> --end <Unicode终点>。每段至多2500字符，工具max_output_tokens至少12000；必须见完整BEGIN/正文/END且未截断，才能把打印PRESENT标识写入read_manifest。hash/解析不是模型阅读。必要图页按实际可用工具和同版受限语境处理。\n").encode()
        requests = {"base": put(rawdir / "request-base.txt", "判读要求\n".encode() + core), "H": put(rawdir / "request-H.txt", "判读说明\n".encode() + core)}
        input_files.extend(requests.values())
        rows.append({"batch_id": oldrow["batch_id"], "members": oldrow["members"], "expected_N": oldrow["expected_N"], "original_packet_bytes": oldrow["original_packet_bytes"], "assignments": forms, "requests": requests, "original_frozen_batch": oldrow})
        for r in routes:
            if r["batch_number"] == n:
                r["fixed_request"] = requests["H" if r["condition"] == "H" else "base"]
    if [i for row in rows for i in row["members"]] != ids:
        raise ValueError("Fixed batch order changed")
    implementation = [binding(HERE / name) for name in ("transport_common.py", "prepare.py", "read_allowed.py", "capture-validator.py", "receiver.py", "runner.py", "controller.py", "preflight.py", "terminal_projection.py", "statistics_after_terminal.py", "actor-capture-instructions.txt", "artifact-schemas.json")]
    external = save(run / "ROOT-only-route-ledger.json", {"issuer": "ROOT", "model_read_forbidden": True, "actual_dispatch_N": 0, "routes": routes, "conditions": list(CONDITIONS), "max_concurrent_CLI": 3})
    d = {"run_id": run.name, "status": "prepared_no_actual_dispatch", "at_utc": now(), "record_N": 800, "batch_N": 87, "conditions": list(CONDITIONS), "batches": rows, "routes": routes, "external_routing": external, "transport_contract": contract, "old_manifest": binding(OLD / "run-manifest.json"), "old_plan": old["plan"], "manual": old["manual"], "execution_prompt": old["execution_prompt"], "protocol": old["protocol"], "validator": validator, "original_validator": old["validator"], "ordered_source_ids": old["ordered_source_ids"], "sample_metadata_coordinator_only": old["sample_metadata_coordinator_only"], "source_locator_findings_metadata_only": old["source_locator_findings_metadata_only"], "statistics_bridge": old["statistics_bridge"], "statistics_engine": old["statistics_engine"], "cli_launcher": old["cli_launcher"], "cli_executable_bindings": old["cli_executable_bindings"], "python_executable": PYTHON, "python_binding": binding(PYTHON), "implementation_bindings": implementation, "input_file_bindings": input_files, "max_concurrent_CLI": 3, "actual_model_calls_at_freeze": 0, "actual_GO_issued": False, "human_assignment_N": 0, "provider_parameters": {"temperature": None, "top_p": None, "seed": None}, "actual_serving_model_verified": False, "first_origin": "ROOT_exact_CLI_final_message_capture", "ROOT_report_seal_issuer": "ROOT_transport", "context_unit": "batch", "P_is_any_R": False}
    mb = save(run / "run-manifest.json", d)
    save(run / "preparation-seal.json", {"run_manifest": mb, "implementation_bindings": implementation, "input_file_bindings": input_files, "external_routing": external, "model_calls": 0, "GO_issued": False})
    # Read-only filesystem modes complement, rather than replace, the actual
    # read-only CLI sandbox. ROOT-output is excluded and never an actor input.
    for b in input_files:
        if run in Path(b["path"]).parents:
            Path(b["path"]).chmod(0o444)
    return {"campaign_manifest": mb, "actual_model_calls": 0, "reserved_slots": len(routes)}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    print(prepare(p.parse_args().run))
