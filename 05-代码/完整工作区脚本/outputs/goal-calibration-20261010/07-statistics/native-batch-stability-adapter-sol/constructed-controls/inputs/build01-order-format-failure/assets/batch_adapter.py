#!/usr/bin/env python3
"""Whole-original-native-batch qualification to frozen stability mathematics.

No executor, native campaign reader, truth labels or model dispatch is present.
The only executable source adapter in this frozen candidate is a synthetic toy.
Production needs a separately frozen common schema/opaque adapter/quote verifier;
hashes and declarations never certify actual provider identity or independence.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
from jsonschema import Draft202012Validator

sys.dont_write_bytecode = True
from vendor import stability_engine as math_engine
import toy_qualification

VERSION = "native-batch-stability-adapter-sol-v1"
DIMS, RUNS, PAIRS = math_engine.DIMS, math_engine.RUNS, math_engine.PAIRS
canonical, digest, object_sha = math_engine.canonical, math_engine.digest, math_engine.object_sha
require, ContractError, read_json_bytes = math_engine.require, math_engine.ContractError, math_engine.read_json_bytes
AssetReader, timestamp = math_engine.AssetReader, math_engine.timestamp
ROOT = Path(__file__).resolve().parent
RETRY = {"max_actual_attempts": 3, "selection": "first_technically_valid_complete_batch_response",
         "semantic_null_stops_retry": True, "same_exact_request_only": True,
         "invalid_any_record_invalidates_whole_batch": True}
CONTEXT = {"context_unit": "batch", "deviation_from_record_protocol": "explicit_batch_context_variant_not_record_independence",
           "verification": "declared_not_independently_verified", "basis": "one complete batch single initial prompt per fresh logical context"}
CONFIG_FIELDS = {"intended_model", "intended_reasoning_effort", "provider_requested", "request_settings",
                 "provider_session_state", "actual_model_identity_status"}


def exact(obj, keys, label):
    require(isinstance(obj, dict) and set(obj) == set(keys), label + ": exact closed fields required")


def request_bytes(reg, prompt, manual, packets, batch_id, run):
    exact(prompt, {"system_prefix", "system_suffix", "user_prefix", "user_suffix", "payload_template"}, "prompt")
    require(prompt["user_prefix"].startswith("判读要求\n"), "fixed main neutral heading required")
    prefix = prompt["user_prefix"]
    if run == "H":
        prefix = "判读说明\n" + prefix[len("判读要求\n"):]
    source = {"batch_id": batch_id, "items": packets}
    display = json.dumps(source, ensure_ascii=False, allow_nan=False, indent=2) if run == "W" else json.dumps(source, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    slots = {"{{SYSTEM_CONTENT}}": prompt["system_prefix"] + manual.decode("utf-8") + prompt["system_suffix"],
             "{{USER_CONTENT}}": prefix + display + prompt["user_suffix"],
             "{{REQUEST_SETTINGS}}": reg["configuration"]["request_settings"]}
    template = canonical(prompt["payload_template"]).decode("utf-8")
    require(all(template.count(s) == 1 for s in slots), "request slots must occur exactly once")
    return canonical(math_engine.replace_slots(prompt["payload_template"], slots))


def qualification_binding(reg, assets):
    q = reg["source_qualification"]
    exact(q, {"interface", "mode", "source_schema", "opaque_adapter", "quote_validator", "production_freeze"}, "source qualification")
    require(q["interface"] == toy_qualification.INTERFACE, "qualification interface mismatch")
    # The production seam is concrete and fail-closed. This toy implementation is
    # never accepted merely by changing a mode or asserting a report boolean.
    require(reg["data_mode"] == "synthetic_control" and q["mode"] == "synthetic_toy_executable_only",
            "production source/schema/opaque adapter/quote verifier adoption absent in this candidate")
    require(q["production_freeze"] is None, "toy fixture cannot assert a production freeze")
    source_schema = assets.json(q["source_schema"], "externally bound toy source schema")
    expected_schema = read_json_bytes((ROOT / "toy-source.schema.json").read_bytes(), "candidate toy schema")
    require(object_sha(source_schema) == object_sha(expected_schema), "toy schema cannot be replaced by permissive qualification")
    require(assets.read(q["opaque_adapter"], "opaque adapter") == (ROOT / "toy_qualification.py").read_bytes(), "opaque adapter binding is not the executed frozen implementation")
    require(assets.read(q["quote_validator"], "quote validator") == (ROOT / "toy_qualification.py").read_bytes(), "quote validator binding is not the executed frozen implementation")
    return source_schema


def validate_registry(reg, assets):
    exact(reg, {"contract_version", "data_mode", "dimensions", "registration", "sample", "artifacts", "configuration",
                "source_qualification", "context_contract", "retry_policy", "comparison_plan", "limits", "conditions", "registry_content_sha256"}, "registry")
    require(reg["contract_version"] == VERSION and reg["dimensions"] == list(DIMS), "contract/dimensions drift")
    freeze = reg["registration"]
    exact(freeze, {"registry_id", "status", "frozen_at", "verification"}, "registration")
    require(bool(freeze["registry_id"]) and freeze["status"] == "frozen_before_response_read" and freeze["verification"] == "declaration_not_independently_verified", "freeze declaration must remain unverified")
    frozen_at = timestamp(freeze["frozen_at"], "freeze")
    unsigned = copy.deepcopy(reg)
    seal = unsigned.pop("registry_content_sha256")
    require(object_sha(unsigned) == seal, "registry content seal mismatch")
    require(object_sha(reg["context_contract"]) == object_sha(CONTEXT), "explicit batch-context deviation required")
    require(object_sha(reg["retry_policy"]) == object_sha(RETRY), "whole-batch fixed first-valid max-three policy required")
    require(reg["comparison_plan"] == {"pairs": [list(x) for x in PAIRS], "three_way": ["R1", "R2", "R3"], "perturbation_baseline": "R1"}, "fixed comparison drift")
    require(reg["limits"] == {"stability_pass_threshold": None, "confidence_interval_gate": None}, "no new threshold/CI gate")
    config = reg["configuration"]
    exact(config, CONFIG_FIELDS, "configuration")
    require(config["intended_model"] == "gpt-6.1-sol" and config["intended_reasoning_effort"] == "ultra", "requested configuration drift")
    require(config["request_settings"] == {"native_tool_requested_create_thread": {"model": "gpt-6.1-sol", "thinking": "ultra"}, "provider_parameters": None, "application_system_instruction": None}, "native tool request must be separated from unavailable provider/application telemetry")
    require(config["actual_model_identity_status"] == "not_proven_by_requested_identity_or_hash" and config["provider_session_state"] in {"unknown", "stateless_declared_unverified", "stateful_declared_unverified"} and isinstance(config["request_settings"], dict), "identity/session disclosure required")
    artifacts = reg["artifacts"]
    exact(artifacts, {"manual", "prompt", "output_schema", "protocol", "statistical_engine", "batch_adapter"}, "artifacts")
    for name, ref in artifacts.items():
        assets.read(ref, name)
    require(assets.read(artifacts["statistical_engine"], "math engine") == (ROOT / "vendor/stability_engine.py").read_bytes(), "math implementation binding drift")
    require(artifacts["statistical_engine"]["sha256"] == "4e4bc00ef8f2d5e9d69b99841c18642bbb8919fbea83601d52c61816aca98e6d", "typing-fixed math source required")
    require(assets.read(artifacts["batch_adapter"], "adapter") == Path(__file__).read_bytes(), "batch adapter implementation drift")
    native_schema = assets.json(artifacts["output_schema"], "native schema")
    require(object_sha(native_schema) == object_sha(read_json_bytes((ROOT / "vendor/native-output.schema.json").read_bytes(), "native fixed schema")), "native schema drift")
    source_schema = qualification_binding(reg, assets)
    sample = reg["sample"]
    exact(sample, {"selection_mode", "weight_kind", "target_domain", "selection_rule", "scope_limit", "frame_seal_sha256", "all_target_units_positive_pi_declared", "assigned_records", "ordered_assignedIDs", "batches"}, "sample")
    require(sample["selection_mode"] in {"probability", "non_probability", "census"} and sample["weight_kind"] in {"equal", "preassigned_analytic", "inverse_probability"}, "sample selection/weight kind")
    require(all(isinstance(sample[x], str) and sample[x] for x in ("target_domain", "selection_rule", "scope_limit")), "sample scope required")
    records = sample["assigned_records"]
    require(isinstance(records, list) and records, "nonempty fixed assignments required")
    ids = [r["assignedID"] for r in records]
    require(ids == sample["ordered_assignedIDs"] and all(isinstance(i, str) and i for i in ids) and len(ids) == len(set(ids)), "fixed unique assignment order")
    for field in ("output_id", "source_id"):
        require(len({r[field] for r in records}) == len(ids), "one-to-one " + field + " required")
    batches = sample["batches"]
    require(isinstance(batches, list) and batches and len({b["batch_id"] for b in batches}) == len(batches), "unique complete batch plan")
    require([i for b in batches for i in b["members"]] == ids, "batch partition/order must equal assigned IDs")
    for b in batches:
        exact(b, {"batch_id", "members"}, "batch plan")
        require(isinstance(b["batch_id"], str) and b["batch_id"] and 1 <= len(b["members"]) <= 41, "frozen native batch size")
    recordmap, weights, packets, batchmap = {}, {}, {}, {}
    for b in batches:
        batchmap.update({i: b["batch_id"] for i in b["members"]})
    for r in records:
        exact(r, {"assignedID", "output_id", "source_id", "weight", "inclusion_probability", "material_state", "material_pending_reason", "source_packet", "packet_sha256", "source_content_sha256", "ctx_binding_sha256"}, "record assignment")
        i = r["assignedID"]
        require(r["material_state"] == "complete" and r["material_pending_reason"] is None, "toy candidate covers complete synthetic material only")
        raw = assets.read(r["source_packet"], "original frozen source packet")
        require(r["packet_sha256"] == digest(raw), "packet exact-byte binding drift")
        packet = read_json_bytes(raw, "source packet")
        try:
            packets[i] = toy_qualification.adapt_source(packet, r, source_schema)
        except (ValueError, TypeError, KeyError) as exc:
            raise ContractError("source qualification failed: " + str(exc)) from exc
        weights[i] = math_engine.number(r["weight"], i + ".weight")
        if sample["selection_mode"] == "non_probability":
            require(r["inclusion_probability"] is None and sample["weight_kind"] != "inverse_probability", "no fabricated probability weights")
        else:
            pi = math_engine.number(r["inclusion_probability"], i + ".pi")
            require(pi <= 1 and weights[i] == 1 / pi, "weight must exactly equal 1/pi")
            if sample["selection_mode"] == "census":
                require(pi == 1 and weights[i] == 1, "census pi/weight exactly 1")
        if sample["weight_kind"] == "equal":
            require(weights[i] == 1, "equal weight must be 1")
        recordmap[i] = r
    if sample["selection_mode"] == "probability":
        require(sample["weight_kind"] == "inverse_probability" and bool(sample["frame_seal_sha256"]) and sample["all_target_units_positive_pi_declared"] is True, "positive pi/frame declaration required")
    conditions = reg["conditions"]
    require(list(conditions) == list(RUNS), "all six conditions in fixed order required")
    manual = assets.read(artifacts["manual"], "manual")
    prompt = assets.json(artifacts["prompt"], "prompt")
    planned = set()
    for run in RUNS:
        c = conditions[run]
        exact(c, {"run_id", "role", "allowed_change", "configuration_sha256", "artifacts_sha256", "sample_sha256", "batches"}, "condition")
        require(c["run_id"] == run and c["role"] == math_engine.ROLES[run] and c["allowed_change"] == math_engine.CHANGES[run], "condition role/allowed perturbation drift")
        require(c["configuration_sha256"] == object_sha(config) and c["artifacts_sha256"] == object_sha(artifacts) and c["sample_sha256"] == object_sha(sample), "condition common drift")
        require(list(c["batches"]) == [b["batch_id"] for b in batches], "all exact frozen batch assignments required")
        for b in batches:
            bid, members = b["batch_id"], b["members"]
            binding = c["batches"][bid]
            exact(binding, {"assignment", "exact_request", "planned_context_id", "manual_sha256", "source_manifest_sha256", "unit_order_sha256", "prompt_sha256"}, "batch binding")
            require(binding["planned_context_id"] and binding["planned_context_id"] not in planned, "planned batch context reused")
            planned.add(binding["planned_context_id"])
            outids = [recordmap[i]["output_id"] for i in members]
            manifest = [{"assignedID": i, "output_id": recordmap[i]["output_id"], "source_id": recordmap[i]["source_id"], "packet_sha256": recordmap[i]["packet_sha256"], "source_content_sha256": recordmap[i]["source_content_sha256"], "ctx_binding_sha256": recordmap[i]["ctx_binding_sha256"]} for i in members]
            request = request_bytes(reg, prompt, manual, [packets[i] for i in members], bid, run)
            require(assets.read(binding["exact_request"], "whole batch exact request") == request, "whole batch request differs from allowed W/H assembly")
            require(binding["manual_sha256"] == artifacts["manual"]["sha256"] and binding["source_manifest_sha256"] == object_sha(manifest) and binding["unit_order_sha256"] == object_sha(outids) and binding["prompt_sha256"] == digest(request), "batch binding SHA drift")
            assignment = {"contract_version": VERSION, "run_id": run, "condition": "production" if run == "P" else run,
                          "batch_id": bid, "context_unit": "batch", "members": manifest,
                          "exact_request": binding["exact_request"], "configuration_sha256": object_sha(config),
                          "artifacts_sha256": object_sha(artifacts), "planned_context_id": binding["planned_context_id"],
                          **{k: binding[k] for k in ("manual_sha256", "source_manifest_sha256", "unit_order_sha256", "prompt_sha256")}}
            require(object_sha(assets.json(binding["assignment"], "original frozen batch assignment")) == object_sha(assignment), "original assignment drift")
    return {"ids": ids, "records": recordmap, "weights": weights, "packets": packets, "batches": batchmap,
            "batch_plan": batches, "frozen_at": frozen_at, "schema": native_schema}


def qualify_whole_batch(raw, reg, meta, run, bid, binding):
    """All-or-nothing. No per-record values leave this function after failure."""
    try:
        response = read_json_bytes(raw, "whole original batch response")
        errors = list(Draft202012Validator(meta["schema"]).iter_errors(response))
        require(not errors, "native output schema: " + (errors[0].message if errors else ""))
        for field in ("run_id", "condition", "batch_id", "manual_sha256", "source_manifest_sha256", "unit_order_sha256", "prompt_sha256"):
            expected = run if field == "run_id" else ("production" if run == "P" else run) if field == "condition" else bid if field == "batch_id" else binding[field]
            require(response[field] == expected, "batch original response binding mismatch: " + field)
        members = next(b["members"] for b in meta["batch_plan"] if b["batch_id"] == bid)
        require([x["blind_id"] for x in response["items"]] == [meta["records"][i]["output_id"] for i in members], "batch rows missing/duplicated/extra/reordered")
        traces = []
        for index, i in enumerate(members):
            traces.append({"assignedID": i, "extraction_pointer": f"/items/{index}",
                           "executed_qualification": toy_qualification.check_quotes(response["items"][index], meta["packets"][i], binding["manual_sha256"], [])})
        return response, {"technical_valid": True, "failure_reasons": [], "record_checks": traces}
    except (ContractError, ValueError, TypeError, KeyError, IndexError) as exc:
        return None, {"technical_valid": False, "failure_reasons": [str(exc)], "record_checks": [],
                      "no_partially_valid_record_extracted": True}


def validate_ledger(reg, ledger, meta, assets, registry_bytes):
    exact(ledger, {"contract_version", "data_mode", "registry_file_sha256", "runs"}, "ledger")
    require(ledger["contract_version"] == VERSION and ledger["data_mode"] == reg["data_mode"] and ledger["registry_file_sha256"] == digest(registry_bytes), "ledger exact registry binding")
    require(list(ledger["runs"]) == list(RUNS), "full six-condition batch ledger required")
    selected, firsts, audit, contexts, models = {}, {}, {}, set(), set()
    for run in RUNS:
        stream = ledger["runs"][run]
        exact(stream, {"registered_condition_sha256", "batches", "seal"}, "run ledger")
        require(stream["registered_condition_sha256"] == object_sha(reg["conditions"][run]), "registered condition ledger drift")
        require([r["batch_id"] for r in stream["batches"]] == [b["batch_id"] for b in meta["batch_plan"]], "complete ordered batch ledger required")
        selected[run], firsts[run], audit[run] = {}, {}, []
        for position, row in enumerate(stream["batches"]):
            exact(row, {"batch_id", "batch_order_index", "attempts", "not_called", "first"}, "batch ledger row")
            bid = row["batch_id"]
            require(type(row["batch_order_index"]) is int and row["batch_order_index"] == position + 1, "batch ledger order drift")
            binding = reg["conditions"][run]["batches"][bid]
            members = meta["batch_plan"][position]["members"]
            attempts = row["attempts"]
            require(isinstance(attempts, list) and len(attempts) <= 3, "max three actual whole-batch attempts")
            first, first_response, checks, previous_end = None, None, [], None
            for n, a in enumerate(attempts, 1):
                require(first is None, "request after first technically valid batch, including semantic null")
                exact(a, {"attempt_number", "started_at", "ended_at", "assignment_sha256", "exact_request_sha256", "configuration_sha256", "native_tool_assignment", "dispatch", "delivery", "provider_receipt", "transport_status", "transport_reason", "original_batch_response", "capture"}, "whole batch attempt")
                require(type(a["attempt_number"]) is int and a["attempt_number"] == n, "consecutive integer batch attempt")
                start, end = timestamp(a["started_at"], "start"), timestamp(a["ended_at"], "end")
                require(start >= meta["frozen_at"] and end >= start and (previous_end is None or start >= previous_end), "freeze/attempt chronology drift")
                previous_end = end
                require(a["assignment_sha256"] == binding["assignment"]["sha256"] and a["exact_request_sha256"] == binding["exact_request"]["sha256"] and a["configuration_sha256"] == object_sha(reg["configuration"]), "attempt assignment/request/config binding drift")
                tool_assignment = a["native_tool_assignment"]
                require(tool_assignment == {"requested_create_thread": {"model": "gpt-6.1-sol", "thinking": "ultra"}, "actual_tool_request": None, "actual_tool_creation_receipt": None, "evidence_kind": "synthetic_constructed_declaration"}, "toy cannot fabricate native tool accepted/created evidence")
                dispatch = a["dispatch"]
                exact(dispatch, {"context_unit", "planned_context_id", "logical_context_id", "fresh_context_created_declared", "history_mode", "additional_user_messages", "previous_output_exposure_declared", "verification", "evidence_kind"}, "dispatch declaration")
                context_id = dispatch["logical_context_id"]
                require(dispatch["context_unit"] == "batch" and dispatch["planned_context_id"] == binding["planned_context_id"] and isinstance(context_id, str) and context_id and context_id not in contexts, "batch context/unique logical attempt context drift")
                contexts.add(context_id)
                require(dispatch["fresh_context_created_declared"] is True and dispatch["previous_output_exposure_declared"] is False and dispatch["additional_user_messages"] == [] and dispatch["history_mode"] == "complete_batch_single_initial_prompt" and dispatch["verification"] == "declared_not_independently_verified" and dispatch["evidence_kind"] == "synthetic_constructed_declaration", "dispatch must disclose complete fresh batch single prompt without feedback; synthetic declarations are not actual evidence")
                delivery = a["delivery"]
                exact(delivery, {"ordered_output_ids", "source_manifest_sha256", "source_read_status", "known_context_compaction", "known_input_truncation", "known_output_truncation", "asset_delivery", "verification"}, "delivery declaration")
                require(delivery["ordered_output_ids"] == [meta["records"][i]["output_id"] for i in members] and delivery["source_manifest_sha256"] == binding["source_manifest_sha256"] and delivery["source_read_status"] == "complete_declared" and delivery["asset_delivery"] == [] and delivery["verification"] == "declared_not_independently_verified" and all(delivery[k] is False for k in ("known_context_compaction", "known_input_truncation", "known_output_truncation")), "batch delivery/completeness declaration mismatch")
                receipt = a["provider_receipt"]
                exact(receipt, {"status", "request_id", "returned_model", "configuration_evidence"}, "provider receipt")
                require(receipt["status"] in {"unavailable", "observed_unverified"}, "provider receipt never hash-authenticated")
                if receipt["status"] == "unavailable":
                    require(all(receipt[k] is None for k in ("request_id", "returned_model", "configuration_evidence")), "unavailable receipt cannot invent telemetry")
                elif receipt["returned_model"] is not None:
                    require(isinstance(receipt["returned_model"], str) and receipt["returned_model"], "literal model receipt required")
                    models.add(receipt["returned_model"])
                capture = a["capture"]
                exact(capture, {"raw_kind", "sealed_before_technical_check_declared", "captured_at", "verification", "provider_wire_authenticated"}, "response capture")
                require(capture["raw_kind"] == "whole_original_native_structured_submission_file_bytes" and capture["sealed_before_technical_check_declared"] is True and capture["verification"] == "declared_not_independently_verified" and capture["provider_wire_authenticated"] is False, "original native submission file evidence is not authenticated provider wire bytes")
                captured = timestamp(capture["captured_at"], "capture time")
                require(start <= captured <= end, "capture chronology mismatch")
                check = copy.deepcopy(a)
                if a["transport_status"] == "failure":
                    require(isinstance(a["transport_reason"], str) and a["transport_reason"], "transport failure reason required")
                    if a["original_batch_response"] is not None:
                        assets.read(a["original_batch_response"], "original partial batch transport bytes")
                    check.update({"technical_valid": False, "failure_type": "transport_failure", "record_checks": [], "failure_reasons": [a["transport_reason"]]})
                else:
                    require(a["transport_status"] == "ok" and a["transport_reason"] is None and a["original_batch_response"] is not None, "ok transport must preserve complete batch bytes")
                    raw = assets.read(a["original_batch_response"], "whole original native batch bytes")
                    response, qualification = qualify_whole_batch(raw, reg, meta, run, bid, binding)
                    check.update(qualification)
                    check["failure_type"] = None if qualification["technical_valid"] else "technical_invalid_whole_batch"
                    if qualification["technical_valid"]:
                        first = {"run_id": run, "batch_id": bid, "attempt_number": n,
                                 "original_batch_response": a["original_batch_response"], "parsed_batch_sha256": object_sha(response)}
                        first_response = response
                checks.append(check)
            if not attempts:
                nc = row["not_called"]
                exact(nc, {"state", "reason"}, "zero-attempt state")
                require(nc["state"] in math_engine.NOT_CALLED and isinstance(nc["reason"], str) and nc["reason"], "zero-attempt explicit reason")
                batch_state = "not_called"
            else:
                require(row["not_called"] is None, "attempted batch cannot be not-called")
                batch_state = "technical_failure" if first is None else "first_technically_valid_complete_batch"
            require(object_sha(row["first"]) == object_sha(first), "first must equal earliest valid whole batch in its own condition")
            for index, i in enumerate(members):
                item = None if first_response is None else first_response["items"][index]
                labels = None if item is None else copy.deepcopy(item["labels"])
                state = batch_state if item is None else "valid_semantic_null" if any(x is None for x in labels.values()) else "valid_binary"
                origin = None if first is None else {**copy.deepcopy(first), "assignedID": i, "output_id": meta["records"][i]["output_id"], "source_id": meta["records"][i]["source_id"], "packet_sha256": meta["records"][i]["packet_sha256"], "source_content_sha256": meta["records"][i]["source_content_sha256"], "ctx_binding_sha256": meta["records"][i]["ctx_binding_sha256"], "extraction_pointer": f"/items/{index}", "derived_record_sha256": object_sha(item), "derived_record_is_original_response": False, "labels": labels, "raw_response": copy.deepcopy(first["original_batch_response"]), "exact_request": binding["exact_request"], "original_assignment": binding["assignment"], "manual_sha256": binding["manual_sha256"], "prompt_sha256": binding["prompt_sha256"], "configuration_sha256": object_sha(reg["configuration"]), "dispatch": attempts[first["attempt_number"] - 1]["dispatch"], "delivery": attempts[first["attempt_number"] - 1]["delivery"], "provider_receipt": attempts[first["attempt_number"] - 1]["provider_receipt"]}
                firsts[run][i] = origin
                selected[run][i] = {"state": state, "labels": labels, "first": origin, "not_called": copy.deepcopy(row["not_called"]), "material_state": meta["records"][i]["material_state"], "failure_exhausted_three_attempts": state == "technical_failure" and len(attempts) == 3, "remaining_retry_slots_if_unresolved": 3 - len(attempts) if state == "technical_failure" else 0}
            audit[run].append({"batch_id": bid, "members": members, "state": batch_state, "actual_batch_attempt_count": len(attempts), "attempts": checks, "not_called": row["not_called"], "first": first, "failure_exhausted_three_attempts": batch_state == "technical_failure" and len(attempts) == 3, "remaining_retry_slots_if_unresolved": 3 - len(attempts) if batch_state == "technical_failure" else 0})
        seal = stream["seal"]
        exact(seal, {"status", "content_sha256", "sealed_at", "verification"}, "condition seal")
        require(seal["status"] in {"condition_terminal_sealed", "snapshot_not_terminal"} and seal["verification"] == "declaration_not_independently_verified", "explicit condition terminal/snapshot seal required")
        unsigned = {k: v for k, v in stream.items() if k != "seal"}
        require(seal["content_sha256"] == object_sha(unsigned), "condition seal content mismatch")
        sealed_at = timestamp(seal["sealed_at"], "condition seal time")
        require(sealed_at >= meta["frozen_at"] and all(sealed_at >= timestamp(a["ended_at"], "attempt end") for b in stream["batches"] for a in b["attempts"]), "condition seal precedes attempt completion")
        terminal = all(b["state"] != "technical_failure" or b["failure_exhausted_three_attempts"] for b in audit[run])
        require((seal["status"] == "condition_terminal_sealed") == terminal, "unresolved retry slots cannot be labelled terminal/sealed for comparisons")
    require(len(models) <= 1, "observed returned-model string drift")
    return selected, firsts, audit, sorted(models)


def statistics(reg, meta, selected, firsts):
    """Reuse the untouched audited single-record mathematics with origin pointers."""
    pairs = {}
    for a, b in PAIRS:
        pair = {"runs": [a, b], "orientation": "first run rows, second run columns; neither side is truth", "dimensions": {}}
        for dim in DIMS:
            domain = math_engine.domain_accounting((a, b), selected, meta, dim)
            counts = dict.fromkeys(("n00", "n01", "n10", "n11"), 0)
            weighted = {k: Fraction(0) for k in counts}
            changes = []
            for i in domain["joint_comparable_assignedIDs"]:
                x, y = selected[a][i]["labels"][dim], selected[b][i]["labels"][dim]
                counts[f"n{x}{y}"] += 1
                weighted[f"n{x}{y}"] += meta["weights"][i]
                if x != y:
                    changes.append({"assignedID": i, "first_label": x, "second_label": y, "first_origin": firsts[a][i], "second_origin": firsts[b][i]})
            pair["dimensions"][dim] = {"domain": domain, "raw": math_engine.table_metrics(counts), "weighted": math_engine.table_metrics(weighted), "label_changes": changes, "weight_kind": reg["sample"]["weight_kind"]}
        pair["five_dimension_vector"] = math_engine.agreement_summary((a, b), selected, meta)
        pair["semantic_null_patterns"] = math_engine.null_patterns((a, b), selected, meta)
        pair["q"] = math_engine.q_group((a, b), selected, meta, reg["sample"]["weight_kind"])
        pairs[f"{a}/{b}"] = pair
    main = ("R1", "R2", "R3")
    triple = {"runs": list(main), "five_dimension_vector": math_engine.agreement_summary(main, selected, meta), "by_dimension": {d: math_engine.agreement_summary(main, selected, meta, d) for d in DIMS}, "semantic_null_patterns": math_engine.null_patterns(main, selected, meta), "q": math_engine.q_group(main, selected, meta, reg["sample"]["weight_kind"])}
    return pairs, triple


def analyze(registry_path, ledger_path):
    registry_path, ledger_path = Path(registry_path).resolve(), Path(ledger_path).resolve()
    raw_registry, raw_ledger = registry_path.read_bytes(), ledger_path.read_bytes()
    reg, ledger = read_json_bytes(raw_registry, "registry"), read_json_bytes(raw_ledger, "ledger")
    assets = AssetReader(registry_path.parent)
    meta = validate_registry(reg, assets)
    selected, firsts, audit, models = validate_ledger(reg, ledger, meta, assets, raw_registry)
    comparison_unlocked = all(ledger["runs"][r]["seal"]["status"] == "condition_terminal_sealed" for r in ("R1", "R2", "R3", "W", "H"))
    pairs, triple = statistics(reg, meta, selected, firsts) if comparison_unlocked else ({}, None)
    report = {"contract_version": VERSION, "data_mode": reg["data_mode"], "execution_status": "synthetic_constructed_whole_batch_controls_only",
              "sampling": reg["sample"], "comparison_gate": {"unlocked": comparison_unlocked, "rule": "all R1/R2/R3/W/H selected or explicit terminal failure and condition-sealed before comparison", "verification": "file bindings/declarations checked; actual pre-comparison chronology not independently authenticated"}, "paired_comparisons": pairs, "three_main_runs": triple,
              "production_firsts": firsts["P"], "per_record_states": selected,
              "run_summaries": {run: {"scheduled_record_n": len(meta["ids"]), "record_states": dict(Counter(x["state"] for x in selected[run].values())), "actual_batch_attempt_n": sum(x["actual_batch_attempt_count"] for x in audit[run]), "attempt_counts_are_constructed_not_actual_model_calls": True} for run in RUNS},
              "identity_and_independence": {"requested_configuration": reg["configuration"], "observed_returned_model_strings": models, "actual_provider_identity_proven": False, "actual_model_identity_proven": False, "independent_contexts_verified": False, "context_contract": reg["context_contract"], "hash_proves_actual_dispatch_or_delivery": False},
              "limits": {"stability_pass_threshold": None, "confidence_interval_gate": None, "confidence_intervals_computed": False, "classification_correctness_measured": False, "human_reliability_measured": False, "new_true_R_runs_executed": False, "project_completion_decision": False, "production_qualification_supported_by_toy": False, "population_claim": False, "source_and_quote_checks": "executed frozen synthetic schema/opaque adapter/quote code; production interface not adopted", "whole_batch_invalidates_all_members": True, "derived_json_is_original_response": False, "original_byte_evidence_kind": "native structured submission UTF-8 file bytes; never authenticated provider raw network/wire response", "native_batch_attempt_count_is_provider_API_call_count": False, "provider_API_call_count": None},
              "input_bindings": {"registry_file_sha256": digest(raw_registry), "ledger_file_sha256": digest(raw_ledger)}}
    inputs = [{"path": str(registry_path), "sha256": digest(raw_registry), "bytes": len(raw_registry)}, {"path": str(ledger_path), "sha256": digest(raw_ledger), "bytes": len(raw_ledger)}] + [{**x, "path": str(assets.base / x["path"])} for x in sorted(assets.seen.values(), key=lambda x: x["path"])]
    return report, {"contract_version": VERSION, "runs": firsts}, {"contract_version": VERSION, "runs": audit}, inputs


def save_analysis(registry_path, ledger_path, output):
    out = Path(output)
    require(not out.exists() or not any(out.iterdir()), "nonempty output: sealed results cannot be overwritten")
    report, firsts, audit, inputs = analyze(registry_path, ledger_path)
    out.mkdir(parents=True, exist_ok=True)
    outputs = {"report.json": canonical(report) + b"\n", "firsts.json": canonical(firsts) + b"\n", "audit-ledger.json": canonical(audit) + b"\n",
               "report.md": ("# 构造整批稳定性衔接输出\n\n完整原始批次首次技术有效才抽取 `/items/N`。所有失败字节和完整批次台账保留。\n\n上下文为 batch，明确偏离逐record独立上下文；实际身份、派发、交付及独立性未认证。\n\n仅独立构造控制，没有新真实R运行、真实稳定率、CI或标签/项目验证结论。正式来源和引用接口尚未采纳。数值见 report.json。\n").encode("utf-8")}
    for name, data in outputs.items():
        with (out / name).open("xb") as stream:
            stream.write(data)
    code = [Path(__file__).resolve(), ROOT / "toy_qualification.py", ROOT / "toy-source.schema.json", ROOT / "vendor/stability_engine.py", ROOT / "vendor/native-output.schema.json"]
    seal = {"contract_version": VERSION, "identity_or_independence_authenticated_by_hash": False, "inputs": inputs,
            "code": [{"path": str(p), "sha256": digest(p.read_bytes()), "bytes": p.stat().st_size} for p in code],
            "outputs": [{"path": name, "sha256": digest(data), "bytes": len(data)} for name, data in sorted(outputs.items())], "seal_self_included": False}
    with (out / "seal.json").open("xb") as stream:
        stream.write(canonical(seal) + b"\n")
    return seal


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("analyze")
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        save_analysis(args.registry, args.ledger, args.out_dir)
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "rejected", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": "synthetic_batch_report_written", "new_true_R_runs_executed": False, "project_completion_changed": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
