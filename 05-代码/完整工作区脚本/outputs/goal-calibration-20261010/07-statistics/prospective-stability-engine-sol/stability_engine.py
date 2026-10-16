#!/usr/bin/env python3
"""Prospective, offline stability statistics. No model invocation and no truth labels.

All file references are relative to the frozen registry's directory. Only the
registered assets, exact requests, raw responses and technical-check reports are
read. Binary metrics never interpret a missing result as zero. SHA bindings are
integrity checks, not proof of an actual model identity or independent context.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime
from fractions import Fraction
from pathlib import Path

VERSION = "prospective-stability-engine-sol-v1"
DIMS = ("S", "E", "Ec", "I", "F")
RUNS = ("P", "R1", "R2", "R3", "W", "H")
PAIRS = (("R1", "R2"), ("R1", "R3"), ("R2", "R3"), ("W", "R1"), ("H", "R1"))
CHECKS = ("parseable", "id_match", "five_dimensions", "response_schema",
          "source_binding", "context_evidence", "contiguous_quote", "assets_reference")
ROLES = {"P": "production", "R1": "diagnostic_main", "R2": "diagnostic_main",
         "R3": "diagnostic_main", "W": "diagnostic_whitespace", "H": "diagnostic_heading"}
CHANGES = {"P": "none", "R1": "none", "R2": "none", "R3": "none",
           "W": "source_json_compact_to_indent2", "H": "user_first_line_synonym"}
NOT_CALLED = {"not_called", "precheck_blocked", "material_blocked", "creation_empty"}


class ContractError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ContractError(message)


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_sha(obj):
    return digest(canonical(obj))


def read_json_bytes(data, label):
    def reject_duplicates(pairs):
        obj = {}
        for key, value in pairs:
            require(key not in obj, f"{label}: duplicate JSON key {key}")
            obj[key] = value
        return obj
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates,
                          parse_constant=lambda x: (_ for _ in ()).throw(ContractError(f"{label}: {x}")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label}: invalid UTF-8 JSON: {exc}") from exc


def number(value, label):
    require(not isinstance(value, bool), f"{label}: boolean is not a weight")
    try:
        out = Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ContractError(f"{label}: finite decimal/rational number required") from exc
    require(out > 0, f"{label}: must be positive")
    return out


def export_number(value):
    if value is None:
        return None
    if isinstance(value, Fraction):
        return int(value) if value.denominator == 1 else float(value)
    return value


def timestamp(value, label):
    require(isinstance(value, str), f"{label}: ISO timestamp required")
    try:
        out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{label}: invalid ISO timestamp") from exc
    require(out.tzinfo is not None, f"{label}: timezone required")
    return out


class AssetReader:
    def __init__(self, base):
        self.base = Path(base).resolve()
        self.seen = {}

    def read(self, ref, label):
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, f"{label}: path/sha256 ref required")
        rel = Path(ref["path"])
        require(not rel.is_absolute() and ".." not in rel.parts, f"{label}: safe relative path required")
        p = (self.base / rel).resolve()
        require(p.is_relative_to(self.base), f"{label}: path escaped input directory")
        require(p.is_file(), f"{label}: file absent: {rel}")
        data = p.read_bytes()
        require(digest(data) == ref["sha256"], f"{label}: SHA mismatch: {rel}")
        self.seen[str(rel)] = {"path": str(rel), "sha256": digest(data), "bytes": len(data)}
        return data

    def json(self, ref, label):
        return read_json_bytes(self.read(ref, label), label)


def replace_slots(obj, replacements):
    if isinstance(obj, str):
        if obj in replacements:
            return copy.deepcopy(replacements[obj])
        require("{{" not in obj and "}}" not in obj, "payload template: slots must occupy the entire string value")
        return obj
    if isinstance(obj, list):
        return [replace_slots(v, replacements) for v in obj]
    if isinstance(obj, dict):
        return {k: replace_slots(v, replacements) for k, v in obj.items()}
    return obj


def request_bytes(registry, prompt, manual_bytes, source_obj, run):
    """The registered request assembly is explicit; no provider API is guessed."""
    prefix = prompt["user_prefix"]
    require(prefix.startswith("判读要求\n"), "main user_prefix must begin with exact first line 判读要求")
    if run == "H":
        prefix = "判读说明\n" + prefix[len("判读要求\n"):]
    source_json = json.dumps(source_obj, ensure_ascii=False, allow_nan=False,
                             separators=(",", ":")) if run != "W" else json.dumps(
                                 source_obj, ensure_ascii=False, allow_nan=False, indent=2)
    user = prefix + source_json + prompt["user_suffix"]
    system = prompt["system_prefix"] + manual_bytes.decode("utf-8") + prompt["system_suffix"]
    slots = {"{{SYSTEM_CONTENT}}": system, "{{USER_CONTENT}}": user,
             "{{REQUEST_SETTINGS}}": registry["common_configuration"]["request_settings"]}
    serialized = canonical(prompt["payload_template"]).decode("utf-8")
    for slot in slots:
        require(serialized.count(slot) == 1, f"payload template must contain {slot} exactly once")
    return canonical(replace_slots(prompt["payload_template"], slots))


def validate_registry(reg, assets):
    require(set(reg) == {"contract_version", "data_mode", "dimensions", "registration", "sample", "common_artifacts",
                         "common_configuration", "context_unit", "context_independence_declaration", "allow_pending_material_for_valid_response",
                         "retry_policy", "comparison_plan", "stability_pass_threshold", "confidence_interval_gate", "conditions", "registry_content_sha256"},
            "registry top-level fields must be exactly the registered contract")
    require(reg.get("contract_version") == VERSION, "unsupported registry contract_version")
    require(reg.get("data_mode") in {"synthetic_control", "prospective_registered_inputs"}, "explicit data_mode required")
    require(tuple(reg.get("dimensions", [])) == DIMS, "dimensions must be S,E,Ec,I,F in this order")
    freeze = reg["registration"]
    require(set(freeze) == {"registry_id", "status", "frozen_at", "verification"} and bool(freeze["registry_id"]), "freeze registry identity fields required")
    require(freeze["status"] == "frozen_before_response_read", "registry must declare pre-response freeze")
    frozen_at = timestamp(freeze["frozen_at"], "registration.frozen_at")
    require(freeze["verification"] == "declaration_not_independently_verified", "freeze claim must not be relabelled as verified")
    require(reg.get("stability_pass_threshold") is None and reg.get("confidence_interval_gate") is None,
            "no stability pass threshold or CI gate is registered")
    sealed = copy.deepcopy(reg)
    recorded_seal = sealed.pop("registry_content_sha256", None)
    require(recorded_seal == object_sha(sealed), "registry content seal mismatch")
    sample = reg["sample"]
    require(set(sample) == {"selection_mode", "weight_kind", "target_domain", "selection_rule", "scope_limit", "frame_seal_sha256",
                            "all_target_units_positive_pi_declared", "assigned_records", "ordered_assignedIDs", "batches"}, "sample plan fields must be exact")
    require(sample["selection_mode"] in {"probability", "non_probability", "census"}, "sample selection_mode required")
    require(sample["weight_kind"] in {"equal", "preassigned_analytic", "inverse_probability"}, "weight_kind required")
    require(bool(sample["target_domain"]) and bool(sample["selection_rule"]) and bool(sample["scope_limit"]), "sample scope and selection rule required")
    records = sample["assigned_records"]
    require(isinstance(records, list) and len(records) > 0, "nonempty assigned_records required")
    ids = [r["assignedID"] for r in records]
    require(all(isinstance(i, str) and i for i in ids) and len(set(ids)) == len(ids), "assignedID must be nonempty and unique")
    require(sample["ordered_assignedIDs"] == ids, "assigned_records order must equal frozen order")
    batches = sample["batches"]
    require(batches and len({b["batch_id"] for b in batches}) == len(batches), "unique nonempty batch ids required")
    require(all(b["members"] for b in batches) and [i for b in batches for i in b["members"]] == ids,
            "batch flattening must exactly equal order; partitions are not repeats")
    weights, recordmap, sources, batchmap = {}, {}, {}, {}
    for b in batches:
        require(set(b) == {"batch_id", "members"} and isinstance(b["batch_id"], str) and b["batch_id"], "batch fields/id must be exact")
        for i in b["members"]:
            batchmap[i] = b["batch_id"]
    for r in records:
        require(set(r) == {"assignedID", "weight", "inclusion_probability", "material_state", "material_pending_reason", "material"}, "assigned record fields must be exact")
        i = r["assignedID"]
        weights[i] = number(r["weight"], f"{i}.weight")
        require(r["material_state"] in {"complete", "pending"}, f"{i}: material_state required")
        require(r["material_state"] != "pending" or bool(r["material_pending_reason"]), f"{i}: pending reason required")
        material = r["material"]
        require(set(material) == {"version", "source_packet", "source_semantic_sha256", "ctx_binding", "ctx_binding_sha256"}, "material binding fields must be exact")
        require(bool(material["version"]) and bool(material["ctx_binding_sha256"]), f"{i}: material/CTX version binding required")
        packet_bytes = assets.read(material["source_packet"], f"{i}.source_packet")
        packet = read_json_bytes(packet_bytes, f"{i}.source_packet")
        require(material["source_semantic_sha256"] == object_sha(packet), f"{i}: semantic source SHA mismatch")
        require(material["ctx_binding_sha256"] == object_sha(material["ctx_binding"]), f"{i}: CTX binding SHA mismatch")
        sources[i], recordmap[i] = packet, r
        if sample["selection_mode"] == "probability":
            pi = number(r["inclusion_probability"], f"{i}.inclusion_probability")
            require(pi <= 1 and weights[i] == 1 / pi, f"{i}: probability weight must be exactly 1/pi")
        elif sample["selection_mode"] == "census":
            require(weights[i] == 1 and r.get("inclusion_probability") == 1, f"{i}: census requires weight=pi=1")
        else:
            require(r.get("inclusion_probability") is None, f"{i}: non-probability sample must not fabricate pi")
        if sample["weight_kind"] == "equal":
            require(weights[i] == 1, f"{i}: equal weights must equal one")
    if sample["selection_mode"] == "probability":
        require(sample["weight_kind"] == "inverse_probability", "probability sample requires inverse_probability weight_kind")
        require(bool(sample["frame_seal_sha256"]) and sample["all_target_units_positive_pi_declared"] is True,
                "probability frame seal and coverage declaration required")
    if sample["selection_mode"] == "non_probability":
        require(sample["weight_kind"] != "inverse_probability", "non-probability weights cannot be labelled design weights")
    common = reg["common_artifacts"]
    require(set(common) == {"manual", "prompt", "output_schema", "adapter", "technical_validator", "protocol"}, "six common artifact bindings must be exact")
    for name in ("manual", "prompt", "output_schema", "adapter", "technical_validator", "protocol"):
        require(set(common[name]) == {"version", "artifact"}, f"{name}: artifact binding fields must be exact")
        require(bool(common[name]["version"]), f"{name}: version required")
        assets.read(common[name]["artifact"], f"common.{name}")
    manual = assets.read(common["manual"]["artifact"], "manual")
    prompt = assets.json(common["prompt"]["artifact"], "prompt")
    require(set(prompt) == {"system_prefix", "system_suffix", "user_prefix", "user_suffix", "payload_template"}, "prompt assembly keys must be exact")
    config = reg["common_configuration"]
    require(set(config) == {"intended_model", "intended_reasoning_effort", "provider_requested", "request_settings",
                            "provider_session_state", "actual_model_identity_status"}, "common_configuration keys must be exact")
    require(bool(config["intended_model"]) and bool(config["intended_reasoning_effort"]), "intended model and reasoning must be explicit")
    require(config["actual_model_identity_status"] == "not_proven_by_requested_identity_or_hash", "requested identity must not certify actual model")
    require(config["provider_session_state"] in {"stateless_declared_unverified", "stateful_declared_unverified", "unknown"}, "provider state disclosure required")
    require(isinstance(config["request_settings"], dict), "actual controllable request settings must be an explicit object")
    require(type(reg["allow_pending_material_for_valid_response"]) is bool, "allow_pending_material_for_valid_response must be an explicit boolean")
    context_unit = reg["context_unit"]
    require(context_unit in {"record", "batch"}, "context_unit must be record or batch; no implicit native77 assumption")
    declaration = reg["context_independence_declaration"]
    require(set(declaration) == {"declared_independent", "verification", "basis"}, "explicit context independence declaration required")
    require(isinstance(declaration["declared_independent"], bool) and declaration["verification"] == "not_independently_verified"
            and bool(declaration["basis"]), "independence declaration must remain unverified")
    require(reg["retry_policy"] == {"max_actual_attempts": 3, "selection": "first_technically_valid_complete_response",
                                    "semantic_null_stops_retry": True, "same_exact_request_only": True}, "fixed first-valid retry policy required")
    require(reg["comparison_plan"] == {"pairs": [list(p) for p in PAIRS], "three_way": ["R1", "R2", "R3"],
                                       "perturbation_baseline": "R1"}, "comparison plan must retain fixed W/R1,H/R1 and three main runs")
    conditions = reg["conditions"]
    require(list(conditions) == list(RUNS), "conditions must be registered once in P,R1,R2,R3,W,H order")
    identities = set()
    for run in RUNS:
        c = conditions[run]
        require(set(c) == {"run_id", "role", "allowed_change", "common_configuration_sha256", "common_artifacts_sha256",
                            "sample_plan_sha256", "context_unit", "planned_contexts", "requests"}, f"{run}: unregistered condition field/override")
        require(c["run_id"] == run and c["role"] == ROLES[run] and c["allowed_change"] == CHANGES[run], f"{run}: condition role/perturbation drift")
        require(c["common_configuration_sha256"] == object_sha(config), f"{run}: requested configuration drift")
        require(c["common_artifacts_sha256"] == object_sha(common), f"{run}: shared version/manual/prompt drift")
        require(c["sample_plan_sha256"] == object_sha(sample), f"{run}: assignedID/weight/order/batch drift")
        require(c["context_unit"] == context_unit, f"{run}: context unit drift")
        units = ids if context_unit == "record" else [b["batch_id"] for b in batches]
        require(set(c["planned_contexts"]) == set(units), f"{run}: complete frozen context map required")
        for unit in units:
            identity = c["planned_contexts"][unit]
            require(isinstance(identity, str) and identity and identity not in identities, f"{run}: planned contexts reused across registered units/runs")
            identities.add(identity)
        require(list(c["requests"]) == ids, f"{run}: full per-record exact request bindings required in frozen order")
        for i in ids:
            binding = c["requests"][i]
            require(set(binding) == {"exact_request", "source_semantic_sha256", "ctx_binding_sha256"}, f"{run}/{i}: request binding fields required")
            require(binding["source_semantic_sha256"] == recordmap[i]["material"]["source_semantic_sha256"]
                    and binding["ctx_binding_sha256"] == recordmap[i]["material"]["ctx_binding_sha256"], f"{run}/{i}: material identity drift")
            raw = assets.read(binding["exact_request"], f"{run}/{i}.exact_request")
            require(raw == request_bytes(reg, prompt, manual, sources[i], run), f"{run}/{i}: exact request differs from registered permitted assembly")
    return {"ids": ids, "weights": weights, "records": recordmap, "batches": batchmap, "frozen_at": frozen_at}


def response_structure(raw, assigned_id):
    try:
        response = read_json_bytes(raw, "raw_response")
    except ContractError:
        return None, {"parseable": False, "id_match": False, "five_dimensions": False, "response_schema": False}
    if not isinstance(response, dict):
        return None, {"parseable": True, "id_match": False, "five_dimensions": False, "response_schema": False}
    labels = response.get("labels")
    complete = isinstance(labels, dict) and set(labels) == set(DIMS) and all(v is None or type(v) is int and v in (0, 1) for v in labels.values())
    required_keys = {"assignedID", "labels", "reasons", "null_reasons", "material_requests", "evidence"}
    schema = set(response) == required_keys and complete
    if schema:
        schema = isinstance(response["reasons"], dict) and set(response["reasons"]) == set(DIMS) and all(
            isinstance(v, str) and v for v in response["reasons"].values())
        schema = schema and isinstance(response["null_reasons"], dict) and isinstance(response["material_requests"], dict)
        schema = schema and isinstance(response["evidence"], dict) and set(response["evidence"]) == set(DIMS)
        if schema:
            null_dims = {d for d in DIMS if labels[d] is None}
            schema = set(response["null_reasons"]) == null_dims and set(response["material_requests"]) == null_dims
            schema = schema and all(isinstance(response["null_reasons"][d], str) and response["null_reasons"][d]
                                    and isinstance(response["material_requests"][d], str) and response["material_requests"][d]
                                    for d in null_dims)
    return response, {"parseable": True, "id_match": response.get("assignedID") == assigned_id,
                      "five_dimensions": complete, "response_schema": bool(schema)}


def validate_ledger(reg, ledger, meta, assets, registry_bytes):
    require(set(ledger) == {"contract_version", "data_mode", "registry_file_sha256", "firsts_selection_rule", "runs"}, "ledger top-level fields must be exact")
    require(ledger.get("contract_version") == VERSION and ledger.get("data_mode") == reg["data_mode"], "ledger contract/data_mode mismatch")
    require(ledger.get("registry_file_sha256") == digest(registry_bytes), "ledger must bind exact registry bytes")
    require(ledger.get("firsts_selection_rule") == reg["retry_policy"]["selection"], "ledger firsts selection rule drift")
    require(list(ledger["runs"]) == list(RUNS), "ledger needs all six registered conditions, including not-called rows")
    selected, audit, firsts = {}, {}, {}
    observed_models, all_context_receipts = set(), []
    for run in RUNS:
        c, stream = reg["conditions"][run], ledger["runs"][run]
        require(set(stream) == {"registered_condition_sha256", "records"}, f"{run}: ledger stream fields must be exact")
        require(stream["registered_condition_sha256"] == object_sha(c), f"{run}: condition ledger drift")
        require([r["assignedID"] for r in stream["records"]] == meta["ids"], f"{run}: complete ordered record ledger required")
        selected[run], audit[run], firsts[run] = {}, [], {}
        for pos, row in enumerate(stream["records"]):
            i = row["assignedID"]
            require(set(row) == {"assignedID", "order_index", "batch_id", "attempts", "not_called", "first"}, f"{run}/{i}: record ledger fields must be exact")
            require(type(row["order_index"]) is int and row["order_index"] == pos + 1 and row["batch_id"] == meta["batches"][i], f"{run}/{i}: order or batch drift")
            attempts = row["attempts"]
            require(isinstance(attempts, list) and len(attempts) <= 3, f"{run}/{i}: max 3 actual attempts")
            expected_context = c["planned_contexts"][i if reg["context_unit"] == "record" else row["batch_id"]]
            first = None
            attempt_audit = []
            previous_end = None
            for n, a in enumerate(attempts, 1):
                require(first is None, f"{run}/{i}: request after first technical valid response; semantic null cannot trigger retry")
                require(set(a) == {"attempt_number", "started_at", "ended_at", "executed_configuration", "request_binding",
                                  "context", "provider_receipt", "transport_status", "transport_reason", "raw_response", "validator_report"},
                        f"{run}/{i}/{n}: attempt fields must be exact")
                require(type(a["attempt_number"]) is int and a["attempt_number"] == n, f"{run}/{i}: consecutive integer actual attempt numbers required")
                start, end = timestamp(a["started_at"], "started_at"), timestamp(a["ended_at"], "ended_at")
                require(start >= meta["frozen_at"] and end >= start and (previous_end is None or start >= previous_end),
                        f"{run}/{i}/{n}: freeze/time/attempt chronology mismatch")
                previous_end = end
                require(object_sha(a["executed_configuration"]) == object_sha(reg["common_configuration"]), f"{run}/{i}/{n}: requested model/settings drift")
                require(object_sha(a["request_binding"]) == object_sha(c["requests"][i]), f"{run}/{i}/{n}: retry exact request/material drift")
                context = a["context"]
                require(set(context) == {"context_unit", "planned_context_id", "previous_output_exposure_declared", "verification"}, "context receipt fields must be exact")
                require(context["context_unit"] == reg["context_unit"] and context["planned_context_id"] == expected_context,
                        f"{run}/{i}/{n}: context plan drift")
                require(context["previous_output_exposure_declared"] is False and context["verification"] == "not_independently_verified",
                        "context metadata must declare no prior-output exposure and retain unverified status")
                all_context_receipts.append(context)
                receipt = a["provider_receipt"]
                require(set(receipt) == {"status", "request_id", "returned_model", "configuration_evidence"}, "provider receipt fields must be exact")
                require(receipt["status"] in {"unavailable", "observed_unverified"}, "provider receipt is unavailable or observed, never authenticated by SHA")
                if receipt["status"] == "unavailable":
                    require(receipt["request_id"] is None and receipt["returned_model"] is None and receipt["configuration_evidence"] is None,
                            "unavailable provider receipt must not invent identity/parameters")
                elif receipt["returned_model"] is not None:
                    require(isinstance(receipt["returned_model"], str) and receipt["returned_model"], "returned_model must be literal nonempty receipt string")
                    observed_models.add(receipt["returned_model"])
                require(a["transport_status"] in {"ok", "failure"}, "transport_status must be ok/failure")
                item = copy.deepcopy(a)
                if a["transport_status"] == "failure":
                    require(bool(a["transport_reason"]) and a["validator_report"] is None, "transport failure reason required; no fake validation")
                    if a["raw_response"] is not None:
                        assets.read(a["raw_response"], "partial transport response")
                    item["technical_valid"] = False
                    item["failure_type"] = "transport_failure"
                else:
                    require(a["transport_reason"] is None and a["raw_response"] is not None and a["validator_report"] is not None,
                            "transport ok requires bound raw response and validator report")
                    raw = assets.read(a["raw_response"], f"{run}/{i}/{n}.raw_response")
                    response, calculated = response_structure(raw, i)
                    v = assets.json(a["validator_report"], f"{run}/{i}/{n}.validator_report")
                    require(set(v) == {"validator_artifact_sha256", "exact_request_sha256", "raw_response_sha256", "checks", "failure_reasons"}, "validator report keys must be exact")
                    require(v["validator_artifact_sha256"] == reg["common_artifacts"]["technical_validator"]["artifact"]["sha256"]
                            and v["exact_request_sha256"] == c["requests"][i]["exact_request"]["sha256"]
                            and v["raw_response_sha256"] == digest(raw), "validator report binding mismatch")
                    require(set(v["checks"]) == set(CHECKS) and all(type(x) is bool for x in v["checks"].values()), "all preregistered technical checks required")
                    require(all(v["checks"][k] == value for k, value in calculated.items()), "validator report contradicts locally checked raw response schema/ID")
                    valid = all(v["checks"].values())
                    require(isinstance(v["failure_reasons"], list) and (valid or bool(v["failure_reasons"])), "technical invalid result needs failure reasons")
                    item["technical_valid"] = valid
                    item["failure_type"] = None if valid else "technical_invalid_response"
                    if valid:
                        pending = meta["records"][i]["material_state"] == "pending"
                        require(not pending or reg["allow_pending_material_for_valid_response"] is True,
                                f"{i}: pending material valid response not preregistered")
                        first = {"run_id": run, "assignedID": i, "attempt_number": n,
                                 "raw_response": copy.deepcopy(a["raw_response"]), "validator_report": copy.deepcopy(a["validator_report"]),
                                 "exact_request": copy.deepcopy(c["requests"][i]["exact_request"]),
                                 "source_semantic_sha256": c["requests"][i]["source_semantic_sha256"],
                                 "ctx_binding_sha256": c["requests"][i]["ctx_binding_sha256"],
                                 "parsed_response_sha256": object_sha(response), "labels": copy.deepcopy(response["labels"]),
                                 "selection": "first_technically_valid_complete_response", "context": copy.deepcopy(context),
                                 "provider_receipt": copy.deepcopy(receipt)}
                attempt_audit.append(item)
            if not attempts:
                nc = row["not_called"]
                require(isinstance(nc, dict) and set(nc) == {"state", "reason"} and nc["state"] in NOT_CALLED and bool(nc["reason"]),
                        f"{run}/{i}: zero actual attempts needs explicit not_called/precheck/material/empty state")
                state = "not_called"
            else:
                require(row["not_called"] is None, f"{run}/{i}: called row cannot be marked not_called")
                state = "technical_failure" if first is None else ("valid_semantic_null" if any(first["labels"][d] is None for d in DIMS) else "valid_binary")
            expected_first = None if first is None else {k: copy.deepcopy(first[k]) for k in ("run_id", "assignedID", "attempt_number", "raw_response", "parsed_response_sha256")}
            require(object_sha(row["first"]) == object_sha(expected_first), f"{run}/{i}: first binding must equal earliest valid raw response in its own condition; no diagnostic substitution")
            selected[run][i] = {"state": state, "labels": None if first is None else first["labels"], "first": first,
                                "not_called": copy.deepcopy(row["not_called"]), "material_state": meta["records"][i]["material_state"],
                                "failure_exhausted_three_attempts": state == "technical_failure" and len(attempts) == 3,
                                "remaining_retry_slots_if_unresolved": 3 - len(attempts) if state == "technical_failure" else 0}
            audit[run].append({"assignedID": i, "state": state, "actual_attempt_count": len(attempts),
                               "not_called": copy.deepcopy(row["not_called"]), "attempts": attempt_audit,
                               "first": first, "material_state": meta["records"][i]["material_state"],
                               "failure_exhausted_three_attempts": state == "technical_failure" and len(attempts) == 3,
                               "remaining_retry_slots_if_unresolved": 3 - len(attempts) if state == "technical_failure" else 0})
            firsts[run][i] = first
    require(len(observed_models) <= 1, "observed provider-returned model identity drift across frozen conditions; cannot establish same condition")
    return selected, audit, firsts, sorted(observed_models)


def dim_state(row, dim):
    if row["labels"] is None:
        return row["state"]
    return "semantic_null" if row["labels"][dim] is None else f"binary_{row['labels'][dim]}"


def binary(row, dim=None):
    return row["labels"] is not None and (row["labels"][dim] in (0, 1) if dim else all(row["labels"][d] in (0, 1) for d in DIMS))


def vector(row):
    return tuple(row["labels"][d] for d in DIMS)


def mass(ids, weights):
    return sum((weights[i] for i in ids), Fraction(0))


def table_metrics(cells):
    n00, n01, n10, n11 = (Fraction(cells[k]) for k in ("n00", "n01", "n10", "n11"))
    n = n00 + n01 + n10 + n11
    margins = {"first_0": n00 + n01, "first_1": n10 + n11, "second_0": n00 + n10, "second_1": n01 + n11}
    po = None if n == 0 else (n00 + n11) / n
    pe = None if n == 0 else (margins["first_0"] * margins["second_0"] + margins["first_1"] * margins["second_1"]) / (n * n)
    kappa = None if n == 0 or pe == 1 else (po - pe) / (1 - pe)
    return {"cells": {k: export_number(v) for k, v in cells.items()}, "denominator": export_number(n),
            "marginals": {k: export_number(v) for k, v in margins.items()}, "Po": export_number(po), "Pe": export_number(pe),
            "kappa": export_number(kappa), "kappa_na_reason": "no_joint_binary_records" if n == 0 else "Pe_equals_one_degenerate_marginals" if pe == 1 else None,
            "positive_counts": {"first": export_number(margins["first_1"]), "second": export_number(margins["second_1"]),
                                "change_second_minus_first": export_number(margins["second_1"] - margins["first_1"])},
            "label_change_mass": export_number(n01 + n10)}


def domain_accounting(runs, selected, meta, dim=None):
    eligible, excluded, patterns = [], [], {}
    for i in meta["ids"]:
        rows = [selected[r][i] for r in runs]
        ok = all(binary(row, dim) for row in rows)
        (eligible if ok else excluded).append(i)
        if not ok:
            states = [dim_state(row, dim) if dim else row["state"] for row in rows]
            key = tuple(states)
            if key not in patterns:
                patterns[key] = {"states_in_run_order": dict(zip(runs, states)), "assignedIDs": []}
            patterns[key]["assignedIDs"].append(i)
    for pattern in patterns.values():
        pattern["n"] = len(pattern["assignedIDs"])
        pattern["weight_sum"] = export_number(mass(pattern["assignedIDs"], meta["weights"]))
    pending = [i for i in meta["ids"] if meta["records"][i]["material_state"] == "pending"]
    return {"scheduled_n": len(meta["ids"]), "scheduled_weight_sum": export_number(mass(meta["ids"], meta["weights"])),
            "joint_comparable_n": len(eligible), "joint_comparable_weight_sum": export_number(mass(eligible, meta["weights"])),
            "joint_comparable_assignedIDs": eligible, "excluded_n": len(excluded), "excluded_assignedIDs": excluded,
            "exclusion_overlap_patterns": list(patterns.values()),
            "marginal_states": {run: dict(Counter(dim_state(selected[run][i], dim) if dim else selected[run][i]["state"] for i in meta["ids"])) for run in runs},
            "material_pending_n": len(pending), "material_pending_assignedIDs": pending,
            "material_pending_among_joint_comparable_n": len(set(pending) & set(eligible)),
            "scope": "shared_binary_dimension_subset" if dim else "shared_all_five_binary_subset"}


def null_patterns(runs, selected, meta):
    both_valid = [i for i in meta["ids"] if all(selected[r][i]["labels"] is not None for r in runs)]
    involved = [i for i in both_valid if any(any(selected[r][i]["labels"][d] is None for d in DIMS) for r in runs)]
    same = [i for i in involved if len({tuple(selected[r][i]["labels"][d] is None for d in DIMS) for r in runs}) == 1]
    return {"both_or_all_technically_valid_n": len(both_valid), "at_least_one_semantic_null_n": len(involved),
            "same_null_mask_n": len(same), "same_null_mask_denominator": len(involved),
            "same_null_mask_rate": len(same) / len(involved) if involved else None,
            "same_null_mask_assignedIDs": same, "is_binary_stability": False,
            "null_mask_records": [{"assignedID": i, "null_dimensions": {r: [d for d in DIMS if selected[r][i]["labels"][d] is None] for r in runs}} for i in involved]}


def agreement_summary(runs, selected, meta, dim=None):
    domain = domain_accounting(runs, selected, meta, dim)
    ids = domain["joint_comparable_assignedIDs"]
    agree = [i for i in ids if len({selected[r][i]["labels"][dim] if dim else vector(selected[r][i]) for r in runs}) == 1]
    weight_den = mass(ids, meta["weights"])
    return {"domain": domain, "agreement_n": len(agree), "denominator_n": len(ids),
            "complete_agreement_rate": len(agree) / len(ids) if ids else None,
            "weighted_agreement_mass": export_number(mass(agree, meta["weights"])), "weighted_denominator": export_number(weight_den),
            "weighted_complete_agreement_rate": export_number(mass(agree, meta["weights"]) / weight_den) if weight_den else None,
            "agreement_assignedIDs": agree, "disagreement_assignedIDs": [i for i in ids if i not in set(agree)],
            "na_reason": None if ids else "no_shared_binary_records"}


def q_group(runs, selected, meta, weight_kind):
    domain = domain_accounting(runs, selected, meta)
    ids = domain["joint_comparable_assignedIDs"]
    by_run = {}
    for run in runs:
        counts = {d: sum(selected[run][i]["labels"][d] for i in ids) for d in DIMS}
        totals = {d: sum((meta["weights"][i] * selected[run][i]["labels"][d] for i in ids), Fraction(0)) for d in DIMS}
        den, wden = sum(counts.values()), sum(totals.values(), Fraction(0))
        by_run[run] = {"common_record_n": len(ids), "common_weight_sum": export_number(mass(ids, meta["weights"])),
                       "unweighted_T": counts, "unweighted_sum5T": den,
                       "unweighted_q": {d: counts[d] / den if den else None for d in DIMS},
                       "weighted_T": {d: export_number(totals[d]) for d in DIMS}, "weighted_sum5T": export_number(wden),
                       "weighted_q": {d: export_number(totals[d] / wden) if wden else None for d in DIMS},
                       "q_na_reason": None if den else "sum5T_is_zero"}
    ranges = {}
    for mode in ("unweighted_q", "weighted_q"):
        ranges[mode] = {}
        for d in DIMS:
            values = {run: by_run[run][mode][d] for run in runs}
            missing = [run for run in runs if values[run] is None]
            ranges[mode][d] = {"min": None if missing else min(values.values()), "max": None if missing else max(values.values()),
                               "range": None if missing else max(values.values()) - min(values.values()), "values": values,
                               "na_runs": missing, "na_reason": "one_or_more_run_sum5T_zero" if missing else None}
    return {"runs": list(runs), "domain": domain, "weight_kind": weight_kind,
            "same_preregistered_weights_used_for_every_run": True, "by_run": by_run, "q_ranges": ranges,
            "scope": "common_all_five_binary_subset_only; each run has its own sum5T denominator; no full-sample or population structure claim"}


def analyze_registry(registry_path, ledger_path):
    registry_path, ledger_path = Path(registry_path).resolve(), Path(ledger_path).resolve()
    raw_registry, raw_ledger = registry_path.read_bytes(), ledger_path.read_bytes()
    reg, ledger = read_json_bytes(raw_registry, "registry"), read_json_bytes(raw_ledger, "ledger")
    assets = AssetReader(registry_path.parent)
    meta = validate_registry(reg, assets)
    selected, audit, firsts, observed = validate_ledger(reg, ledger, meta, assets, raw_registry)
    pair_reports = {}
    for a, b in PAIRS:
        name = f"{a}/{b}"
        report = {"runs": [a, b], "orientation": "first run rows, second run columns; neither side is truth", "dimensions": {}}
        for d in DIMS:
            domain = domain_accounting((a, b), selected, meta, d)
            counts = {key: 0 for key in ("n00", "n01", "n10", "n11")}
            weighted = {key: Fraction(0) for key in counts}
            changes = []
            for i in domain["joint_comparable_assignedIDs"]:
                x, y = selected[a][i]["labels"][d], selected[b][i]["labels"][d]
                cell = f"n{x}{y}"
                counts[cell] += 1
                weighted[cell] += meta["weights"][i]
                if x != y:
                    changes.append({"assignedID": i, "first_label": x, "second_label": y,
                                    "first_raw_response": firsts[a][i]["raw_response"], "second_raw_response": firsts[b][i]["raw_response"]})
            report["dimensions"][d] = {"domain": domain, "raw": table_metrics(counts), "weighted": table_metrics(weighted),
                                        "label_changes": changes, "weight_kind": reg["sample"]["weight_kind"]}
        report["five_dimension_vector"] = agreement_summary((a, b), selected, meta)
        report["semantic_null_patterns"] = null_patterns((a, b), selected, meta)
        report["q"] = q_group((a, b), selected, meta, reg["sample"]["weight_kind"])
        pair_reports[name] = report
    main = ("R1", "R2", "R3")
    triple = {"runs": list(main), "five_dimension_vector": agreement_summary(main, selected, meta),
              "by_dimension": {d: agreement_summary(main, selected, meta, d) for d in DIMS},
              "semantic_null_patterns": null_patterns(main, selected, meta),
              "q": q_group(main, selected, meta, reg["sample"]["weight_kind"])}
    complete_binary = all(selected[r][i]["state"] == "valid_binary" for r in RUNS for i in meta["ids"])
    summaries = {run: {"scheduled_n": len(meta["ids"]), "record_states": dict(Counter(selected[run][i]["state"] for i in meta["ids"])),
                       "actual_attempt_n": sum(r["actual_attempt_count"] for r in audit[run]),
                       "technical_invalid_attempt_n": sum(a["failure_type"] == "technical_invalid_response" for row in audit[run] for a in row["attempts"]),
                       "transport_failure_attempt_n": sum(a["failure_type"] == "transport_failure" for row in audit[run] for a in row["attempts"]),
                       "semantic_null_by_dimension": {d: sum(dim_state(selected[run][i], d) == "semantic_null" for i in meta["ids"]) for d in DIMS},
                       "technical_failure_exhausted_n": sum(selected[run][i]["failure_exhausted_three_attempts"] for i in meta["ids"]),
                       "technical_failure_with_retry_slots_remaining_n": sum(selected[run][i]["remaining_retry_slots_if_unresolved"] > 0 for i in meta["ids"]),
                       "material_pending_n": sum(meta["records"][i]["material_state"] == "pending" for i in meta["ids"])} for run in RUNS}
    report = {"engine_version": VERSION, "data_mode": reg["data_mode"],
              "execution_status": "synthetic_tool_controls_only" if reg["data_mode"] == "synthetic_control" else "offline_registered_input_analysis",
              "not_a_project_completion_or_validation_decision": True,
              "dimensions": list(DIMS), "sampling": copy.deepcopy(reg["sample"]),
              "identity_and_independence": {"requested_configuration": copy.deepcopy(reg["common_configuration"]),
                 "observed_returned_model_strings": observed, "actual_model_identity_proven": False,
                 "context_unit": reg["context_unit"], "independence_declaration": copy.deepcopy(reg["context_independence_declaration"]),
                 "independent_contexts_verified": False, "planned_context_ids_are_integrity_metadata_only": True,
                 "execution_order_and_batch_verification": "declared_indices_and_memberships_checked; actual_dispatch_order_not_independently_verified",
                 "per_record_context_protocol_shape": reg["context_unit"] == "record",
                 "batch_context_warning": None if reg["context_unit"] == "record" else "batch context differs from protocol's per-record independent context; batch membership is not an independent repeat"},
              "limits": {"stability_pass_threshold": None, "confidence_interval_gate": None, "confidence_intervals_computed": False,
                         "binary_input_complete_for_all_registered_runs": complete_binary, "population_claim_made": False,
                         "all_registered_records_have_technical_firsts": all(firsts[r][i] is not None for r in RUNS for i in meta["ids"]),
                         "population_scope_verification": "not_performed; registry coverage/selection declarations are not proof",
                         "classification_correctness_measured": False, "human_reliability_measured": False,
                         "first_production_selection": "P only, earliest technical valid complete response; diagnostics never replace or fill P",
                         "production_scope": "only registered assignedIDs in this diagnostic registry; no claim about full production corpus",
                         "technical_validity_basis": "schema and ID rechecked locally; source/context/contiguous quote/assets checks supplied by the frozen external validator report and not independently revalidated here",
                         "registration_verification": reg["registration"]["verification"]},
              "run_summaries": summaries, "paired_comparisons": pair_reports, "three_main_runs": triple,
              "production_firsts": firsts["P"], "per_record_diagnostic_states": {i: {r: selected[r][i] for r in RUNS} for i in meta["ids"]},
              "input_bindings": {"registry_file_sha256": digest(raw_registry), "ledger_file_sha256": digest(raw_ledger),
                                 "registry_content_sha256": reg["registry_content_sha256"]}}
    inputs = [{"path": str(registry_path), "sha256": digest(raw_registry), "bytes": len(raw_registry)},
              {"path": str(ledger_path), "sha256": digest(raw_ledger), "bytes": len(raw_ledger)}]
    inputs += [{**item, "path": str(assets.base / item["path"])} for item in sorted(assets.seen.values(), key=lambda x: x["path"])]
    return report, {"contract_version": VERSION, "data_mode": reg["data_mode"], "selection_rule": reg["retry_policy"]["selection"], "runs": firsts}, {"runs": audit}, inputs


def markdown_report(report):
    lines = ["# 前瞻稳定性工具输出", "", f"数据模式：`{report['data_mode']}`。当前输出状态：`{report['execution_status']}`。", "",
             "本输出不改变项目执行计划或完成状态，不测分类正确性或真人信度，不设稳定性通过线或CI门槛。",
             f"上下文单位：`{report['identity_and_independence']['context_unit']}`；独立上下文未核验，身份哈希不证明实际模型。",
             "生产结果仅选 P 条件首次技术有效完整响应；语义 null 停止重试；诊断结果不能补齐或替换生产。", "",
             "| 配对 | 维度 | 共同二元n | n00/n01/n10/n11 | 第一/第二阳性数 | Po | Pe | κ | 排除n |", "|---|---|---:|---|---|---:|---:|---:|---:|"]
    fmt = lambda v: "NA" if v is None else f"{v:.6g}" if isinstance(v, float) else str(v)
    for name, pair in report["paired_comparisons"].items():
        for d in DIMS:
            x = pair["dimensions"][d]
            raw = x["raw"]
            cells = "/".join(str(raw["cells"][k]) for k in ("n00", "n01", "n10", "n11"))
            positives = f"{raw['positive_counts']['first']}/{raw['positive_counts']['second']}"
            lines.append(f"| {name} | {d} | {x['domain']['joint_comparable_n']} | {cells} | {positives} | {fmt(raw['Po'])} | {fmt(raw['Pe'])} | {fmt(raw['kappa'])} | {x['domain']['excluded_n']} |")
    triple = report["three_main_runs"]["five_dimension_vector"]
    lines += ["", f"R1/R2/R3 整组五维二元向量完全一致：{triple['agreement_n']}/{triple['denominator_n']}，率={fmt(triple['complete_agreement_rate'])}。",
              f"排除：{triple['domain']['excluded_n']}；共同权重和={fmt(triple['weighted_denominator'])}。null 模式另列于 JSON，不计作二元稳定。", "",
              "| q组 | 运行 | 共同5维记录n | 原始Σ5T | 加权Σ5T |", "|---|---|---:|---:|---:|"]
    for name, q in [("R1/R2/R3", report["three_main_runs"]["q"])] + [(k, v["q"]) for k, v in report["paired_comparisons"].items()]:
        for run, value in q["by_run"].items():
            lines.append(f"| {name} | {run} | {value['common_record_n']} | {value['unweighted_sum5T']} | {fmt(value['weighted_sum5T'])} |")
    lines += ["", "逐维加权四格、双方边际、阳性变化清单、重叠排除状态、各次T与q及范围见 report.json。q使用同组五维均可判共同子集和同一预定权重，各次分母是本次Σ5T；不是完整诊断样本或总体结构。", "",
              "完整 firsts 原响应绑定见 firsts.json；所有真实尝试、失败和未调用账见 audit-ledger.json；输入/输出SHA见 seal.json。SHA仅验证文件绑定。", ""]
    return "\n".join(lines)


def save_analysis(registry_path, ledger_path, output):
    out = Path(output)
    require(not out.exists() or not any(out.iterdir()), "output directory is nonempty; sealed outputs will not be overwritten")
    report, firsts, audit, inputs = analyze_registry(registry_path, ledger_path)
    out.mkdir(parents=True, exist_ok=True)
    outputs = {"report.json": canonical(report) + b"\n", "firsts.json": canonical(firsts) + b"\n",
               "audit-ledger.json": canonical(audit) + b"\n", "report.md": markdown_report(report).encode("utf-8")}
    for name, data in outputs.items():
        (out / name).write_bytes(data)
    script = Path(__file__).resolve()
    seal = {"engine_version": VERSION, "data_mode": report["data_mode"],
            "identity_or_independence_authenticated_by_hash": False,
            "engine": {"path": str(script), "sha256": digest(script.read_bytes())}, "inputs": inputs,
            "outputs": [{"path": name, "sha256": digest(data), "bytes": len(data)} for name, data in sorted(outputs.items())],
            "reproduce": {"command": "python3 stability_engine.py analyze --registry REGISTRY --ledger LEDGER --out-dir NEW_EMPTY_DIRECTORY",
                          "outputs_deterministic_given_input_bytes": True}, "seal_self_included": False}
    (out / "seal.json").write_bytes(canonical(seal) + b"\n")
    return seal


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="validate sealed registry/ledger and write offline stability statistics")
    analyze.add_argument("--registry", type=Path, required=True)
    analyze.add_argument("--ledger", type=Path, required=True)
    analyze.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        seal = save_analysis(args.registry, args.ledger, args.out_dir)
    except (ContractError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"status": "rejected", "engine_version": VERSION, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": "offline_report_written", "data_mode": seal["data_mode"], "output": str(args.out_dir.resolve()),
                      "project_execution_or_completion_changed": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
