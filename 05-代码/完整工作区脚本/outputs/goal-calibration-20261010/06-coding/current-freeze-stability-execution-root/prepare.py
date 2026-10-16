"""Prepare the prospectively fixed 87-batch diagnostic; never launch a model."""
import argparse
import copy
import json
from pathlib import Path

import jsonschema
from common import ROOT, CONDITIONS, binding, check, load, save, put, now

HERE = Path(__file__).resolve().parent
PLAN = ROOT / "06-coding/current-freeze-stability-binding-plan-sol"
PRIMARY = ROOT / "06-coding/native-full4481-v1-sol"
PREP = ROOT / "06-coding/full4481-common-v15-production-preparation-sol"
VALIDATOR = ROOT / "06-coding/full4481-native-execution-adapter-sol/root-validator-amendment-01/validate-structured-batch-production-binding-v2.py"
PROFILE = ROOT / "06-coding/full4481-fresh-cli-dispatch-root/CLI-execution-profile-amendment.json"


def prepare(run):
    run = Path(run).resolve()
    assert not run.exists(), "New campaign directory required; preserve any partial preparation"
    for item in load(PLAN / "seal.json")["files"]:
        check(item)
    plan = load(PLAN / "plan.json")
    for item in load(PLAN / "input-bindings.json")["bindings"]:
        check(item)
    addendum = load(PLAN / "ROOT-W-preset-binding-addendum.json")
    assert addendum["planned_no_sort_display_equivalent_actual_packet_N"] == 800
    primary = load(PRIMARY / "run-manifest.json")
    prep_inputs = load(PREP / "input-bindings.json")
    source_plan = load(PREP / "batch-plan.json")
    cli_profile = load(PROFILE)
    packets = {p["source_id"]: p for b in source_plan["batches"] for p in b["packets"]}
    original_assets = {}
    for batch in source_plan["batches"]:
        for item in batch["source_asset_bindings"]:
            if item["path"] not in original_assets:
                original_assets[item["path"]] = copy.deepcopy(item)
            else:
                original_assets[item["path"]]["source_ids"] = sorted(set(original_assets[item["path"]]["source_ids"]) | set(item["source_ids"]))
    ordered = [x for b in plan["batching"]["fixed_batches_metadata_only"] for x in b["members"]]
    assert len(ordered) == len(set(ordered)) == 800
    assert ordered == sorted(ordered, key=lambda x: packets[x]["frame_ordinal_1based"])
    metadata = plan["sample"]["records_metadata_only"]
    assert set(ordered) == {x["source_id"] for x in metadata}
    run.mkdir()
    actor_binding = put(run / "actor-instructions.txt", (HERE / "actor-instructions.txt").read_bytes())
    overlay_binding = put(run / "CLI-procedural-context-overlay.txt", (ROOT / "06-coding/full4481-fresh-cli-dispatch-root/CLI-procedural-context-overlay.txt").read_bytes())
    order_binding = save(run / "ordered-source-ids.json", ordered)
    sample_binding = save(run / "coordinator-private/sample-metadata.json", metadata)
    variants = {}
    for i in ordered:
        original = packets[i]
        check(original)
        parsed = load(original["path"])
        displayed = (json.dumps(parsed, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n").encode()
        assert displayed == (json.dumps(parsed, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode(), "W sorted-key preset would alter original key order"
        variant = put(run / "W-packets" / (i + ".json"), displayed)
        assert load(variant["path"]) == parsed
        variants[i] = {**original, **variant}
    validator_binding = binding(VALIDATOR)
    assert validator_binding["sha256"] == "34a7ebf62a67f7f80929c3375296093db74c76b96709adf5bed7131bcaa5f533"
    scope = "fixed800 machine diagnostic with independent R1/R2/R3 and W/H sensitivity; no human assignment or truth claim"
    scope_binding = save(run / "run-scope.json", {"run_id": run.name, "scope": scope, "context_unit": "batch", "record_N": 800, "batch_N": 87, "actual_inference_N_at_freeze": 0, "primary_P_is_R1": False, "source_jsonl": primary["source_jsonl"], "manual": primary["manual"], "execution_prompt": primary["execution_prompt"], "protocol": primary["protocol"], "missing_source_locators_changed": False, "human_assignment_N": 0})
    templates = {}
    for name in ("read-manifest", "output-seal", "technical-failure"):
        obj = load(PRIMARY / "templates" / (name + ".template.json"))
        obj["run_id"] = run.name
        templates[name.replace("-", "_") + "_template"] = save(run / "templates" / (name + ".template.json"), obj)
    alias_binding = load(PRIMARY / "batch-0001/assignment.json")["legacy_locator_alias_table_binding"]
    check(alias_binding)
    base_schema = load(prep_inputs["reused_output_schema"]["path"])
    routes, batches = [], []
    for number, fixed in enumerate(plan["batching"]["fixed_batches_metadata_only"], 1):
        ids = fixed["members"]
        directory = run / fixed["batch_id"]
        this_routes = []
        for condition in CONDITIONS:
            selection_dir = directory / ("W-material" if condition == "W" else "") / condition
            for attempt in (1, 2, 3):
                slot = selection_dir / f"attempt-{attempt:04d}"
                slot.mkdir(parents=True)
                this_routes.append({"condition": condition, "batch_number": number, "batch_id": fixed["batch_id"], "attempt_number": attempt, "logical_dispatch_label": f"stability800_{condition}_b{number:04d}_a{attempt:02d}", "output_directory": str(slot), "selection_directory": str(selection_dir), "reservation_only_not_actual_attempt": True})
        routing_binding = save(directory / "attempt-output-routing.json", {"run_id": run.name, "routes": this_routes, "actual_actor_attempt_N": 0, "logical_label_is_not_collaboration_identity": True})
        retention = load(PRIMARY / "response-retention-policy.json")
        retention.update(run_id=run.name, runtime_output_routing=routing_binding)
        retention["first_file_definition"] = "fresh CLI actor first structured whole-batch file bytes; not provider wire"
        retention["first_file_rule"] = retention["first_file_rule"].replace("task-name-reserved", "logical-label-reserved")
        retention_binding = save(directory / "response-retention-policy.json", retention)
        bound_assets = [{**a, "source_ids": sorted(set(a["source_ids"]) & set(ids))} for a in original_assets.values() if set(a["source_ids"]) & set(ids)]
        for item in bound_assets:
            check(item)
        assignments = {}
        for form in ("raw", "W"):
            target = directory if form == "raw" else directory / "W-material"
            batch_packets = [packets[i] if form == "raw" else variants[i] for i in ids]
            schema = copy.deepcopy(base_schema)
            schema["title"] = "Frozen diagnostic whole-batch first structured submission"
            for key, value in (("run_id", run.name), ("batch_id", fixed["batch_id"]), ("requested_model", "gpt-6.1-sol"), ("requested_reasoning_effort", "ultra"), ("manual_binding", primary["manual"]), ("execution_prompt_binding", primary["execution_prompt"]), ("context_unit", "batch"), ("scope", scope)):
                schema["properties"][key] = {"const": value}
            prefixes = []
            for item in batch_packets:
                entry = copy.deepcopy(base_schema["properties"]["records"]["items"])
                for key, value in (("source_id", item["source_id"]), ("output_id", item["output_id"]), ("packet_sha256", item["sha256"])):
                    entry["properties"][key] = {"const": value}
                prefixes.append(entry)
            schema["properties"]["records"] = {"type": "array", "minItems": len(ids), "maxItems": len(ids), "prefixItems": prefixes, "items": False}
            jsonschema.Draft202012Validator.check_schema(schema)
            schema_binding = save(target / "output.schema.json", schema)
            contract = load(PRIMARY / "batch-0001/output-validation-contract.json")
            contract.update(run_id=run.name, output_schema_binding=schema_binding, strict_technical_validator=validator_binding, attempt_output_routing=routing_binding)
            contract_binding = save(target / "output-validation-contract.json", contract)
            assignment = {"run_id": run.name, "batch_id": fixed["batch_id"], "requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "context_unit": "batch", "scope": scope, "output_directory": str(target), "expected_N": len(ids), "source_ids": ids, "manual": primary["manual"], "execution_prompt": primary["execution_prompt"], "actor_instructions": actor_binding, "packet_schema": prep_inputs["packet_schema"], "output_schema": schema_binding, "output_validation_contract": contract_binding, "strict_technical_validator": validator_binding, **templates, "response_retention_policy": retention_binding, "run_scope_binding": primary["protocol"], "campaign_scope_metadata_binding": scope_binding, "legacy_locator_alias_table_binding": alias_binding, "delivery_manifest_order_metadata_only": order_binding, "attempt_output_routing": routing_binding, "packets": batch_packets, "source_asset_bindings": bound_assets, "common_source_jsonl_identity_only": primary["source_jsonl"], "packet_bytes": sum(p["bytes"] for p in batch_packets), "max_total_technical_attempts": 3, "max_technical_retries": 2, "state": "prepared_not_dispatched"}
            assignments[form] = save(target / "assignment.json", assignment)
        # All repeated conditions have exactly the same core request. The W path
        # is an explicit input-binding overlay, never a substantive prompt edit.
        core = ("你是本批fresh政策文本编码执行者。先实际完整读绑定的actor-instructions、manual、execution_prompt、共同protocol；按assignment顺序完整读所有packet及必要受限语境。\n"
                "本批共同assignment的确切路径：" + assignments["raw"]["path"] + "\n"
                "若请求外操作元数据提供assignment_override，使用该格式化材料assignment替代共同assignment；只读取一个有效assignment。\n"
                "context_unit=batch；只作一次完整整批first，使用xb写自己的逻辑标签对应slot/first.json、report.txt、seal.json。不读参照、指标、其他批或attempt，不自行派agent或重试。合法null保留。\n").encode()
        core_binding = put(directory / "dispatch-core.txt", core)
        requests = {"base": put(directory / "request-base.txt", "判读要求\n".encode() + (Path(overlay_binding["path"]).read_bytes()) + b"\n" + core), "H": put(directory / "request-H.txt", "判读说明\n".encode() + Path(overlay_binding["path"]).read_bytes() + b"\n" + core)}
        assert Path(requests["base"]["path"]).read_bytes().split(b"\n", 1)[1] == Path(requests["H"]["path"]).read_bytes().split(b"\n", 1)[1]
        for item in this_routes:
            item["assignment"] = assignments["W" if item["condition"] == "W" else "raw"]
            item["fixed_request"] = requests["H" if item["condition"] == "H" else "base"]
            item["fixed_core"] = core_binding
        routes.extend(this_routes)
        batches.append({**fixed, "assignments": assignments, "requests": requests, "routing": routing_binding, "fixed_core": core_binding})
    implementation = [binding(HERE / p) for p in ("common.py", "prepare.py", "run_one.py", "receive_one.py", "terminal_projection.py", "statistics_after_terminal.py", "actor-instructions.txt")]
    manifest = {"run_id": run.name, "status": "prepared_before_any_diagnostic_dispatch", "at_utc": now(), "record_N": 800, "batch_N": len(batches), "conditions": list(CONDITIONS), "batches": batches, "routes": routes, "plan": binding(PLAN / "plan.json"), "W_preset_addendum": binding(PLAN / "ROOT-W-preset-binding-addendum.json"), "primary_manifest_identity_only": binding(PRIMARY / "run-manifest.json"), "common_freeze": primary["common_input_freeze"], "manual": primary["manual"], "execution_prompt": primary["execution_prompt"], "protocol": primary["protocol"], "validator": validator_binding, "ordered_source_ids": order_binding, "sample_metadata_coordinator_only": sample_binding, "cli_launcher": cli_profile["cli_launcher"], "cli_executable_bindings": cli_profile["executable_bindings"], "implementation_bindings": implementation, "statistics_bridge": binding(ROOT / "07-statistics/native-v17-production-adapter-sol/statistics_bridge.py"), "statistics_engine": binding(ROOT / "07-statistics/native-v17-production-adapter-sol/vendor/stability_engine.py"), "overall_execution_slots_including_ROOT": 4, "max_concurrent_CLI": 3, "actual_model_calls_at_freeze": 0, "human_assignment_N": 0, "actual_GO_or_execution_claimed": False, "provider_parameters": {"temperature": None, "top_p": None, "seed": None}, "shared_primary_scheduler_lock": str(ROOT / "06-coding/full4481-cli-fixed-batch-scheduler-sol/scheduler.lock")}
    manifest["source_locator_findings_metadata_only"] = binding(PREP / "resource-locator-findings.json")
    manifest["input_availability_flags_are_not_semantic_completeness_certificates"] = True
    assert manifest["batch_N"] == 87 and len(routes) == 1305
    result = save(run / "run-manifest.json", manifest)
    save(run / "preparation-seal.json", {"run_manifest": result, "bindings": implementation, "status": "preparation_only_no_execution_GO", "actual_model_calls": 0})
    return {"run_manifest": result, "record_N": 800, "batch_N": 87, "actual_model_calls": 0}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    print(json.dumps(prepare(p.parse_args().run), ensure_ascii=False, indent=2))
