#!/usr/bin/env python3
"""Construct independent invented two/three-record batches; never import answers."""
import copy
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import batch_adapter as adapter

ROOT = Path(__file__).resolve().parent


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else adapter.canonical(value) + b"\n"
    with path.open("xb") as stream:
        stream.write(data)
    try:
        relative = path.relative_to(INPUT)
    except ValueError:
        relative = path.relative_to(ROOT)
    return {"path": str(relative), "sha256": adapter.digest(data)}


def item(record, packet, labels):
    evidence, requests = {}, []
    for dim, label in zip(adapter.DIMS, labels):
        positive_path = {"S": "S_drug_risk", "E": "E_drug_effect", "Ec": "Ec_treatment_payment_resource", "I": "I1", "F": "F_general_evaluation"}[dim]
        evidence[dim] = {"paths": ["material_missing" if label is None else positive_path if label == 1 else "excluded"], "current_quote": packet["unit_text"],
                         "current_span": {"start": 0, "end": len(packet["unit_text"])},
                         "contexts_used": [{"context_id": packet["contexts"][0]["context_id"], "field_path": "text", "quote": "构造上下文", "span": {"start": 0, "end": 5}, "purpose": "mechanical constructed quotation"}],
                         "structural_context_ids_used": [], "image_sources_used": [], "reason": "构造说明，不评判标签正确性",
                         "innovation_support": None, "fairness_specific": None}
        if label is None:
            requests.append({"dimension": dim, "kind": "material_missing", "detail": "构造合法语义待定，要求补充材料", "context_ids": []})
    return {"blind_id": record["output_id"], "content_sha256": packet["content_sha256"], "manual_sha256": REG["artifacts"]["manual"]["sha256"],
            "labels": dict(zip(adapter.DIMS, labels)), "evidence": evidence, "material_requests": requests}


def response(run, bid, binding, labels):
    members = next(b["members"] for b in REG["sample"]["batches"] if b["batch_id"] == bid)
    return {"contract_version": "native-codex-batch-v1-proposal", "run_id": run, "condition": "production" if run == "P" else run,
            "batch_id": bid, **{k: binding[k] for k in ("manual_sha256", "source_manifest_sha256", "unit_order_sha256", "prompt_sha256")},
            "items": [item(RECORDS[i], PACKETS[i], labels[i]) for i in members]}


def attempt(run, bid, binding, number, raw, transport=False):
    seconds = 10 + number * 3
    start, capture, end = (f"2026-10-10T00:00:{seconds+x:02d}+00:00" for x in (0, 1, 2))
    rawref = save(INPUT / "original-submissions" / f"{run}-{bid}-attempt-{number}.raw", raw)
    return {"attempt_number": number, "started_at": start, "ended_at": end,
            "assignment_sha256": binding["assignment"]["sha256"], "exact_request_sha256": binding["exact_request"]["sha256"],
            "configuration_sha256": adapter.object_sha(REG["configuration"]),
            "native_tool_assignment": {"requested_create_thread": {"model": "gpt-6.1-sol", "thinking": "ultra"}, "actual_tool_request": None, "actual_tool_creation_receipt": None, "evidence_kind": "synthetic_constructed_declaration"},
            "dispatch": {"context_unit": "batch", "planned_context_id": binding["planned_context_id"], "logical_context_id": f"constructed-{run}-{bid}-{number}", "fresh_context_created_declared": True, "history_mode": "complete_batch_single_initial_prompt", "additional_user_messages": [], "previous_output_exposure_declared": False, "verification": "declared_not_independently_verified", "evidence_kind": "synthetic_constructed_declaration"},
            "delivery": {"ordered_output_ids": [RECORDS[i]["output_id"] for i in next(b["members"] for b in REG["sample"]["batches"] if b["batch_id"] == bid)], "source_manifest_sha256": binding["source_manifest_sha256"], "source_read_status": "complete_declared", "known_context_compaction": False, "known_input_truncation": False, "known_output_truncation": False, "asset_delivery": [], "verification": "declared_not_independently_verified"},
            "provider_receipt": {"status": "unavailable", "request_id": None, "returned_model": None, "configuration_evidence": None},
            "transport_status": "failure" if transport else "ok", "transport_reason": "constructed output transport interruption" if transport else None,
            "original_batch_response": rawref,
            "capture": {"raw_kind": "whole_original_native_structured_submission_file_bytes", "sealed_before_technical_check_declared": True, "captured_at": capture, "verification": "declared_not_independently_verified", "provider_wire_authenticated": False}}


def build():
    global INPUT, REG, RECORDS, PACKETS
    INPUT = ROOT / "constructed-controls/inputs/mixed"
    if INPUT.exists():
        raise RuntimeError("constructed input already exists; no overwrite")
    INPUT.mkdir(parents=True)
    assets = {}
    for name, file in (("statistical_engine", "vendor/stability_engine.py"), ("batch_adapter", "batch_adapter.py"),
                       ("output_schema", "vendor/native-output.schema.json"), ("protocol", "method-native-protocol.md")):
        assets[name] = save(INPUT / "assets" / Path(file).name, (ROOT / file).read_bytes())
    assets["manual"] = save(INPUT / "assets/toy-manual.txt", "完整构造手册；只作接口检查，无真实政策或答案。".encode("utf-8"))
    prompt = {"system_prefix": "fixture instruction text: ", "system_suffix": "", "user_prefix": "判读要求\n", "user_suffix": "\n一次提交完整批次；不得摘出部分记录。",
              "payload_template": {"fixture_system_instruction_content_not_actual_product_system_role": "{{SYSTEM_CONTENT}}", "native_initial_user_content": "{{USER_CONTENT}}", "configuration_disclosure": "{{REQUEST_SETTINGS}}"}}
    assets["prompt"] = save(INPUT / "assets/toy-prompt.json", prompt)
    qref = save(INPUT / "assets/toy_qualification.py", (ROOT / "toy_qualification.py").read_bytes())
    sref = save(INPUT / "assets/toy-source.schema.json", (ROOT / "toy-source.schema.json").read_bytes())
    PACKETS, RECORDS = {}, {}
    for j, weight in enumerate((1, 2, 3, 4, 5), 1):
        assigned = f"CONSTRUCTED-{j}"
        packet = {"contract_version": "synthetic-opaque-source-v1", "source_id": f"SYNTHETIC-SOURCE-{j}", "blind_id": f"A-{900000+j}", "unit_text": f"独立构造当前文字{j}",
                  "contexts": [{"context_id": f"CTX-{j}", "parent_id": None, "text": "构造上下文", "title": "构造标题", "caption": "构造图注"}], "attachments": []}
        packet["content_sha256"] = adapter.object_sha(packet)
        source = save(INPUT / "sources" / f"packet-{j}.json", packet)
        record = {"assignedID": assigned, "output_id": packet["blind_id"], "source_id": packet["source_id"], "weight": weight, "inclusion_probability": None,
                  "material_state": "complete", "material_pending_reason": None, "source_packet": source, "packet_sha256": source["sha256"], "source_content_sha256": packet["content_sha256"], "ctx_binding_sha256": adapter.object_sha(packet["contexts"])}
        PACKETS[assigned], RECORDS[assigned] = packet, record
    ids = list(RECORDS)
    sample = {"selection_mode": "non_probability", "weight_kind": "preassigned_analytic", "target_domain": "five independently invented controls only", "selection_rule": "constructed ex ante; no real label selection", "scope_limit": "synthetic batch fixture, no real source or population inference", "frame_seal_sha256": None, "all_target_units_positive_pi_declared": False,
              "assigned_records": list(RECORDS.values()), "ordered_assignedIDs": ids, "batches": [{"batch_id": "TWO", "members": ids[:2]}, {"batch_id": "THREE", "members": ids[2:]}]}
    REG = {"contract_version": adapter.VERSION, "data_mode": "synthetic_control", "dimensions": list(adapter.DIMS), "registration": {"registry_id": "independent-batch-fixture-v1", "status": "frozen_before_response_read", "frozen_at": "2026-10-10T00:00:00+00:00", "verification": "declaration_not_independently_verified"},
           "sample": sample, "artifacts": assets, "configuration": {"intended_model": "gpt-6.1-sol", "intended_reasoning_effort": "ultra", "provider_requested": None, "request_settings": {"native_tool_requested_create_thread": {"model": "gpt-6.1-sol", "thinking": "ultra"}, "provider_parameters": None, "application_system_instruction": None}, "provider_session_state": "unknown", "actual_model_identity_status": "not_proven_by_requested_identity_or_hash"},
           "source_qualification": {"interface": "opaque-source-and-quotes-v1", "mode": "synthetic_toy_executable_only", "source_schema": sref, "opaque_adapter": qref, "quote_validator": qref, "production_freeze": None}, "context_contract": adapter.CONTEXT,
           "retry_policy": adapter.RETRY, "comparison_plan": {"pairs": [list(x) for x in adapter.PAIRS], "three_way": ["R1", "R2", "R3"], "perturbation_baseline": "R1"}, "limits": {"stability_pass_threshold": None, "confidence_interval_gate": None}, "conditions": {}}
    for run in adapter.RUNS:
        c = {"run_id": run, "role": adapter.math_engine.ROLES[run], "allowed_change": adapter.math_engine.CHANGES[run], "configuration_sha256": adapter.object_sha(REG["configuration"]), "artifacts_sha256": adapter.object_sha(assets), "sample_sha256": adapter.object_sha(sample), "batches": {}}
        for batch in sample["batches"]:
            bid, members = batch["batch_id"], batch["members"]
            request = adapter.request_bytes(REG, prompt, (INPUT / assets["manual"]["path"]).read_bytes(), [PACKETS[i] for i in members], bid, run)
            request_ref = save(INPUT / "requests" / f"{run}-{bid}.utf8", request)
            manifest = [{k: RECORDS[i][k] for k in ("assignedID", "output_id", "source_id", "packet_sha256", "source_content_sha256", "ctx_binding_sha256")} for i in members]
            binding = {"exact_request": request_ref, "planned_context_id": f"planned-{run}-{bid}", "manual_sha256": assets["manual"]["sha256"], "source_manifest_sha256": adapter.object_sha(manifest), "unit_order_sha256": adapter.object_sha([RECORDS[i]["output_id"] for i in members]), "prompt_sha256": adapter.digest(request)}
            assignment = {"contract_version": adapter.VERSION, "run_id": run, "condition": "production" if run == "P" else run, "batch_id": bid, "context_unit": "batch", "members": manifest, "exact_request": request_ref, "configuration_sha256": adapter.object_sha(REG["configuration"]), "artifacts_sha256": adapter.object_sha(assets), "planned_context_id": binding["planned_context_id"], **{k: binding[k] for k in ("manual_sha256", "source_manifest_sha256", "unit_order_sha256", "prompt_sha256")}}
            binding["assignment"] = save(INPUT / "assignments" / f"{run}-{bid}.json", assignment)
            c["batches"][bid] = binding
        REG["conditions"][run] = c
    REG["registry_content_sha256"] = adapter.object_sha(REG)
    registry_ref = save(INPUT / "registry.json", REG)
    # Prior expectations are authored/saved before candidate responses and CLI.
    save(ROOT / "constructed-controls/prior-expectations.json", {"authored_before_response_fixture_and_analysis": True,
        "R1_R2_S_raw_cells": {"n00": 1, "n01": 1, "n10": 1, "n11": 2}, "R1_R2_S_Po": 0.6, "R1_R2_S_Pe": 0.52, "R1_R2_S_kappa": "1/6",
        "R1_R2_S_weighted_cells": {"n00": 1, "n01": 2, "n10": 3, "n11": 9}, "R1_R2_S_weighted_Po": "2/3", "R1_R2_S_weighted_Pe": "16/25", "R1_R2_S_weighted_kappa": "2/27",
        "R1_R2_R3_C5_n": 4, "R1_R2_R3_C5_weight": 13, "P_two_selected_attempt": 2,
        "P_three_state": "all three records technical failure, original malformed bytes preserved", "H_two_selected_attempt": 2,
        "all_failure_members_no_partial_salvage": True, "source_quote_qualification_is_executable_not_asserted": True})
    rows = {
        "R1": [(0,1,0,0,0), (0,0,1,0,0), (1,1,0,0,0), (1,0,0,1,0), (1,0,0,0,1)],
        "R2": [(0,1,0,0,0), (1,0,None,0,0), (0,1,0,0,0), (1,0,0,1,0), (1,0,0,0,1)],
        "R3": [(0,1,0,0,0), (0,0,1,0,0), (1,0,1,0,0), (1,0,0,1,0), (1,0,0,0,1)]}
    rows["W"], rows["H"] = rows["R1"], rows["R3"]
    rows["P"] = [(0,None,0,0,0), (1,0,0,0,0), (0,0,0,0,0), (0,0,0,0,0), (0,0,0,0,0)]
    ledger = {"contract_version": adapter.VERSION, "data_mode": "synthetic_control", "registry_file_sha256": registry_ref["sha256"], "runs": {}}
    for run in adapter.RUNS:
        stream = {"registered_condition_sha256": adapter.object_sha(REG["conditions"][run]), "batches": []}
        labels = dict(zip(ids, rows[run]))
        for position, batch in enumerate(sample["batches"], 1):
            bid = batch["batch_id"]
            binding = REG["conditions"][run]["batches"][bid]
            valid = response(run, bid, binding, labels)
            raw = adapter.canonical(valid) + b"\n"
            attempts, first = [], None
            if run == "P" and bid == "TWO":
                attempts.append(attempt(run, bid, binding, 1, b'{"items":[', True))
            if run == "H" and bid == "TWO":
                broken = copy.deepcopy(valid)
                broken["items"][1]["evidence"]["S"]["current_quote"] = "不存在的构造引文"
                attempts.append(attempt(run, bid, binding, 1, adapter.canonical(broken)))
            if run == "P" and bid == "THREE":
                for n in (1, 2, 3):
                    attempts.append(attempt(run, bid, binding, n, b'{"malformed":'))
            else:
                n = len(attempts) + 1
                a = attempt(run, bid, binding, n, raw)
                attempts.append(a)
                first = {"run_id": run, "batch_id": bid, "attempt_number": n, "original_batch_response": a["original_batch_response"], "parsed_batch_sha256": adapter.object_sha(valid)}
            stream["batches"].append({"batch_id": bid, "batch_order_index": position, "attempts": attempts, "not_called": None, "first": first})
        stream["seal"] = {"status": "condition_terminal_sealed", "content_sha256": adapter.object_sha(stream), "sealed_at": "2026-10-10T00:01:00+00:00", "verification": "declaration_not_independently_verified"}
        ledger["runs"][run] = stream
    save(INPUT / "ledger.json", ledger)
    return INPUT


if __name__ == "__main__":
    print(build())
