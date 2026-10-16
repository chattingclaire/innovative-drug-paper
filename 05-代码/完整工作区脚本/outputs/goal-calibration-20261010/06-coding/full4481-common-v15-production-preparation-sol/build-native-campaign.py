#!/usr/bin/env python3
"""Instantiate the frozen full-source native campaign. No coding/dispatch occurs."""
import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema


def raw(path):
    return Path(path).read_bytes()


def load(path):
    return json.loads(raw(path))


def binding(path, data=None):
    path = Path(path).resolve()
    data = raw(path) if data is None else data
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with path.open("xb") as f:
        f.write(data)
    return binding(path, data)


def copy_bytes(source, target):
    data = raw(source)
    with Path(target).open("xb") as f:
        f.write(data)
    return binding(target, data)


def ensure_identity(item):
    if binding(item["path"]) != item:
        raise ValueError("Frozen binding mismatch: " + item["path"])


def build_campaign(preparation_dir, campaign_dir, common_freeze, adapter_dir, native_manifest, runtime_task_prefix):
    prep, run, adapter = (Path(p).resolve() for p in (preparation_dir, campaign_dir, adapter_dir))
    if (run / "run-manifest.json").exists():
        raise ValueError("Existing immutable campaign; no overwrite or re-instantiation")
    plan = load(prep / "batch-plan.json")
    inputs = load(prep / "input-bindings.json")
    freeze = load(common_freeze)
    old_manifest = load(native_manifest)
    for key in ("manual", "prompt", "protocol"):
        ensure_identity(freeze[key])
    # Do not reread the full source body: match its already verified binding.
    if freeze["sources"] != inputs["source_jsonl"] or freeze["source_package_seal"] != inputs["source_seal"]:
        raise ValueError("Final release changed the common full-source identity")
    run.mkdir(parents=True, exist_ok=True)
    run_id = run.name
    scope = "one full4481 common-source production run; formal800 validation and stability/repeatability validation remain separate"
    model, effort = old_manifest["requested_model"], old_manifest["requested_reasoning_effort"]
    actor = copy_bytes(adapter / "actor-instructions.txt", run / "actor-instructions.txt")
    validator = copy_bytes(adapter / "validate-structured-batch.py", run / "validate-structured-batch.py")
    if validator["sha256"] != inputs["reused_validator"]["sha256"]:
        raise ValueError("Technical validator was changed")
    receiver = copy_bytes(adapter / "receive_full4481_batch.py", run / "receive_full4481_batch.py")
    routing = load(old_manifest["attempt_output_routing"]["path"])
    routing["run_id"], routing["routes"], routing["actual_actor_attempt_N"] = run_id, [], 0
    for number, batch in enumerate(plan["batches"], 1):
        for attempt in range(1, 4):
            slot = run / batch["batch_id"] / f"attempt-{attempt:04d}"
            slot.mkdir(parents=True, exist_ok=True)
            task = runtime_task_prefix + f"_b{number:04d}_a{attempt:02d}"
            routing["routes"].append({"batch_id": batch["batch_id"], "attempt_number": attempt,
                                      "runtime_task_name": task, "expected_canonical_runtime_task_name": "/root/" + task,
                                      "output_directory": str(slot), "structured_first_path": str(slot / "first.json"),
                                      "report_path": str(slot / "report.txt"), "seal_path": str(slot / "seal.json"),
                                      "reservation_only_not_actual_attempt": True})
    routing_binding = write(run / "attempt-output-routing.json", routing)
    # Existing technical policies retain all criteria; only run/route/schema bindings change.
    retention = load(old_manifest["response_retention_policy"]["path"])
    retention["run_id"], retention["runtime_output_routing"] = run_id, routing_binding
    retention_binding = write(run / "response-retention-policy.json", retention)
    templates = {}
    old_dir = Path(native_manifest).resolve().parent
    for key, relative in (("read_manifest_template", "templates/read-manifest.template.json"),
                          ("output_seal_template", "templates/output-seal.template.json"),
                          ("technical_failure_template", "templates/technical-failure.template.json")):
        obj = load(old_dir / relative)
        obj["run_id"] = run_id
        templates[key] = write(run / relative, obj)
    aliases = load(old_manifest["legacy_locator_aliases"]["path"])
    old_alias_binding = binding(old_manifest["legacy_locator_aliases"]["path"])
    aliases["run_id"] = run_id
    aliases["source_jsonl_binding"] = inputs["source_jsonl"]
    aliases["reused_mechanical_alias_metadata_binding"] = old_alias_binding
    aliases["coverage_note"] = "The existing four exact same-source snapshot mappings are retained. Nine old relative page_asset locators have no image-file SHA in their own nodes and are retained as unresolved, without filename-based guesses. This table does not claim all legacy locators are resolved."
    aliases["unresolved_page_locator_findings_binding"] = binding(prep / "resource-locator-findings.json")
    alias_binding = write(run / "legacy-locator-aliases.json", aliases)
    run_scope = {"run_id": run_id, "status": "frozen_before_dispatch", "record_N": plan["record_N"],
                 "batch_N": plan["batch_N"], "context_unit": "batch", "scope": scope,
                 "manual": freeze["manual"], "execution_prompt": freeze["prompt"], "protocol": freeze["protocol"],
                 "source_jsonl": inputs["source_jsonl"], "source_package_seal": inputs["source_seal"],
                 "one_run_not_independent_repeats": True, "record_independent_context_satisfied": False,
                 "independent_repeats_performed": False, "stability_or_repeatability_conditions_tested": False,
                 "requested_model": model, "requested_reasoning_effort": effort,
                 "actual_serving_model_independently_verified": False, "provider_wire_capture_claimed": False,
                 "actual_inference_N_at_freeze": 0, "actual_consumer_read_or_use_receipt_N_at_freeze": 0}
    run_scope_binding = write(run / "run-scope.json", run_scope)
    order_binding = binding(prep / "approved_record_ids.json")
    base_schema = load(inputs["reused_output_schema"]["path"])
    old_contract = load(old_manifest["output_validation_contract"]["path"])
    campaign_batches = []
    actual_byte_rows = []
    for batch in plan["batches"]:
        directory = run / batch["batch_id"]
        schema = copy.deepcopy(base_schema)
        schema["title"] = "Native full-source whole-batch first structured submission"
        for key, value in (("run_id", run_id), ("batch_id", batch["batch_id"]),
                           ("requested_model", model), ("requested_reasoning_effort", effort),
                           ("manual_binding", freeze["manual"]), ("execution_prompt_binding", freeze["prompt"]),
                           ("context_unit", "batch"), ("scope", scope)):
            schema["properties"][key] = {"const": value}
        item = base_schema["properties"]["records"]["items"]
        prefix = []
        for packet in batch["packets"]:
            own = copy.deepcopy(item)
            for key, value in (("source_id", packet["source_id"]), ("output_id", packet["output_id"]), ("packet_sha256", packet["sha256"])):
                own["properties"][key] = {"const": value}
            prefix.append(own)
        schema["properties"]["records"] = {"type": "array", "minItems": batch["expected_N"], "maxItems": batch["expected_N"], "prefixItems": prefix, "items": False}
        jsonschema.Draft202012Validator.check_schema(schema)
        schema_binding = write(directory / "output.schema.json", schema)
        contract = copy.deepcopy(old_contract)
        contract.update(run_id=run_id, output_schema_binding=schema_binding, strict_technical_validator=validator, attempt_output_routing=routing_binding)
        contract["common_scientific_execution_protocol"] = freeze["protocol"]
        contract_binding = write(directory / "output-validation-contract.json", contract)
        ids = set(batch["source_ids"])
        assets = [{**asset, "source_ids": [x for x in asset["source_ids"] if x in ids]} for asset in batch["source_asset_bindings"]]
        assignment = {"run_id": run_id, "batch_id": batch["batch_id"], "requested_model": model,
                      "requested_reasoning_effort": effort, "context_unit": "batch", "scope": scope,
                      "output_directory": str(directory), "expected_N": batch["expected_N"], "source_ids": batch["source_ids"],
                      "manual": freeze["manual"], "execution_prompt": freeze["prompt"], "actor_instructions": actor,
                      "packet_schema": inputs["packet_schema"], "output_schema": schema_binding,
                      "output_validation_contract": contract_binding, "strict_technical_validator": validator,
                      **templates, "response_retention_policy": retention_binding,
                      # Official common protocol is an allowed procedural input under
                      # the existing validator's run_scope_binding interface slot.
                      "run_scope_binding": freeze["protocol"], "campaign_scope_metadata_binding": run_scope_binding,
                      "legacy_locator_alias_table_binding": alias_binding,
                      "delivery_manifest_order_metadata_only": order_binding, "attempt_output_routing": routing_binding,
                      "packets": batch["packets"], "source_asset_bindings": assets,
                      "common_source_jsonl_identity_only": inputs["source_jsonl"],
                      "packet_bytes": batch["packet_bytes"], "max_total_technical_attempts": 3, "max_technical_retries": 2,
                      "state": "prepared_not_dispatched"}
        assignment_binding = write(directory / "assignment.json", assignment)
        request = ("你是本次全量生产编码的fresh coding actor。先实际完整读取本批assignment指定的actor-instructions、共同冻结manual、execution_prompt和run_scope_binding所绑定的共同执行protocol；然后完整读本批所有packet与必要受限语境。\n"
                   "assignment的确切路径：" + str(directory / "assignment.json") + "\n"
                   "context_unit=batch；依assignment顺序一次整批首答。只写与自己runtime task-name匹配的唯一attempt slot，使用xb保存原始first/report/seal，不写canonical。不要读取参照、指标、其他批或其他attempt输出，不自行派agent或重试。合法null保留。程序解析或hash不等于实际阅读。\n"
                   "本请求在同批所有技术attempt保持同字节；runtime slot是请求外操作元数据。\n").encode()
        with (directory / "dispatch-request.txt").open("xb") as f:
            f.write(request)
        request_binding = binding(directory / "dispatch-request.txt", request)
        common_core = sum(x["bytes"] for x in (freeze["manual"], freeze["prompt"], freeze["protocol"], actor))
        procedural = [assignment[k] for k in ("manual", "execution_prompt", "actor_instructions", "packet_schema", "output_schema", "output_validation_contract", "strict_technical_validator", "read_manifest_template", "response_retention_policy", "output_seal_template", "technical_failure_template", "run_scope_binding", "legacy_locator_alias_table_binding", "delivery_manifest_order_metadata_only", "attempt_output_routing")]
        readable = {x["path"]: x for x in [*procedural, *batch["packets"], *assets, assignment_binding]}
        byte_row = {"batch_id": batch["batch_id"], "expected_N": batch["expected_N"], "packet_bytes": batch["packet_bytes"],
                    "input_bytes": batch["packet_bytes"], "core_text_input_bytes": batch["packet_bytes"] + common_core,
                    "declared_policy_input_files_total_bytes": batch["packet_bytes"] + sum(x["bytes"] for x in assets),
                    "full_declared_readable_input_files_total_bytes": sum(x["bytes"] for x in readable.values())}
        actual_byte_rows.append(byte_row)
        campaign_batches.append({**byte_row, "source_ids": batch["source_ids"], "assignment": assignment_binding,
                                 "output_schema": schema_binding, "dispatch_request": request_binding, "state": "prepared_not_dispatched"})
    byte_budget_binding = write(run / "byte-budget.json", {"run_id": run_id, "context_unit": "batch", "max_records": 12,
                               "packet_byte_limit": 260000, "budget_basis": "Inherited 260000 packet-file-byte heuristic and at most 12 records, statically determined before coding; no provider token/context guarantee; assets/procedures are declared availability, not actual reads.", "batches": actual_byte_rows})
    manifest = {"run_id": run_id, "status": "frozen_before_dispatch", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "record_N": plan["record_N"], "batch_N": plan["batch_N"], "runtime_task_prefix": runtime_task_prefix,
                "context_unit": "batch", "scope": scope, "requested_model": model, "requested_reasoning_effort": effort,
                "manual": freeze["manual"], "execution_prompt": freeze["prompt"], "protocol": freeze["protocol"],
                "common_input_freeze": binding(common_freeze), "source_jsonl": inputs["source_jsonl"],
                "source_package_seal": inputs["source_seal"], "source_material_inventory": binding(prep / "production-source-material-bindings.json"),
                "ordered_source_ids": order_binding, "prepared_batch_plan": binding(prep / "batch-plan.json"),
                "actor_instructions": actor, "strict_technical_validator": validator, "ROOT_receiver": receiver,
                "run_scope": run_scope_binding, "attempt_output_routing": routing_binding, "byte_budget": byte_budget_binding,
                "max_total_technical_attempts": 3, "max_technical_retries": 2, "batches": campaign_batches,
                "actual_inference_N_at_freeze": 0, "coding_actors_dispatched_N_at_freeze": 0,
                "actor_read_use_coding_receipts_N_at_freeze": 0, "GO_or_actual_running_claimed": False,
                "readiness": "mechanically instantiated, awaits ROOT coding dispatch"}
    manifest_binding = write(run / "run-manifest.json", manifest)
    return {"campaign_directory": str(run), "record_N": plan["record_N"], "batch_N": plan["batch_N"], "run_manifest": manifest_binding,
            "actual_inference_N": 0, "coding_dispatch_performed": False}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("preparation-dir", "campaign-dir", "common-freeze", "adapter-dir", "native-manifest", "runtime-task-prefix"):
        p.add_argument("--" + name, required=True)
    a = p.parse_args()
    print(json.dumps(build_campaign(a.preparation_dir, a.campaign_dir, a.common_freeze, a.adapter_dir, a.native_manifest, a.runtime_task_prefix), ensure_ascii=False, indent=2))
