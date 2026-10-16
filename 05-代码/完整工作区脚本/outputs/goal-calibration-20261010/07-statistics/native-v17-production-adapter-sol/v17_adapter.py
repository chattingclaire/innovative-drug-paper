#!/usr/bin/env python3
"""Offline native-v17 records qualification. No executor or campaign discovery.

Only explicitly bound prospective inputs are read. Qualification proves file
binding and contiguous text matches, never actual model identity/tool reading.
"""
from __future__ import annotations
import argparse
import copy
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError, SchemaError

sys.dont_write_bytecode = True
from vendor import stability_engine as math_engine
from vendor import validate_v17
from statistics_bridge import statistics

ROOT = Path(__file__).resolve().parent
VERSION = "native-v17-records-adapter-sol-v1"
RUNS = ("R1", "R2", "R3", "W", "H")
DIMS = math_engine.DIMS
require, ContractError = math_engine.require, math_engine.ContractError
canonical, digest, object_sha = math_engine.canonical, math_engine.digest, math_engine.object_sha
parse, timestamp = math_engine.read_json_bytes, math_engine.timestamp
MATH_SHA = "4e4bc00ef8f2d5e9d69b99841c18642bbb8919fbea83601d52c61816aca98e6d"
V17_SHA = "456c4b51084ba47f6234cec29452242aa6644336d454e7166dac3eb5ecd78f8f"
BASE_SCHEMA_SHA = "5c09ee7335576642dd1b862942fc97c853a9633e1158b2b6284f443dbd88be41"
CONTEXT = {"context_unit": "batch", "record_independence_claimed": False,
           "W_variant": "frozen_packet_JSON_file_compact_to_indent2",
           "H_variant": "execution_prompt_first_line_判读要求_to_判读说明",
           "request_evidence": "native_initial_dispatch_text_and_bound_file_inputs_not_provider_wire",
           "actual_tool_reading_or_provider_identity_authenticated": False}
INPUT_KEYS = ("manual", "execution_prompt", "actor_instructions", "packet_schema", "output_schema",
              "output_validation_contract", "strict_technical_validator", "read_manifest_template",
              "response_retention_policy", "output_seal_template", "technical_failure_template",
              "run_scope_binding", "legacy_locator_alias_table_binding",
              "delivery_manifest_order_metadata_only", "attempt_output_routing")


def exact(obj, keys, label):
    require(isinstance(obj, dict) and set(obj) == set(keys), label + ": closed fields required")


class BoundReader:
    def __init__(self):
        self.seen = {}

    def read(self, ref, label):
        require(isinstance(ref, dict) and {"path", "bytes", "sha256"} <= set(ref), label + ": file binding required")
        p = Path(ref["path"])
        require(p.is_absolute() and p.is_file(), label + ": absolute bound file absent")
        raw = p.read_bytes()
        require(type(ref["bytes"]) is int and len(raw) == ref["bytes"] and digest(raw) == ref["sha256"], label + ": bytes/SHA mismatch")
        self.seen[str(p)] = {"path": str(p), "bytes": len(raw), "sha256": digest(raw)}
        return raw

    def json(self, ref, label):
        return parse(self.read(ref, label), label)


def schema_for_assignment(assignment):
    """Keep v17 layout; replace only prospective identities and exact batch N."""
    raw = (ROOT / "vendor/native-v17-output.schema.json").read_bytes()
    require(digest(raw) == BASE_SCHEMA_SHA, "v17 schema vendor drift")
    schema = parse(raw, "v17 schema")
    for k in ("run_id", "batch_id", "scope", "manual_binding", "execution_prompt_binding"):
        value = assignment[{"manual_binding": "manual", "execution_prompt_binding": "execution_prompt"}.get(k, k)]
        schema["properties"][k] = {"const": value}
    require(type(assignment["expected_N"]) is int and 1 <= assignment["expected_N"] <= 12, "frozen v17 batch capacity 1..12")
    schema["properties"]["records"]["minItems"] = assignment["expected_N"]
    schema["properties"]["records"]["maxItems"] = assignment["expected_N"]
    return schema


def closed_source_schema(schema):
    """Deliberately small explicit grammar; reject permissive nested profiles."""
    require(isinstance(schema, dict) and "type" in schema, "explicit source-schema type required")
    require(not any(k in schema for k in ("$ref", "oneOf", "anyOf", "allOf", "patternProperties")), "source profile requires explicit recursive shape, without schema shortcuts")
    types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
    require(set(types) <= {"object", "array", "string", "integer", "number", "boolean", "null"} and bool(types), "source profile type")
    if "object" in types:
        require(schema.get("additionalProperties") is False and isinstance(schema.get("properties"), dict), "source nested objects must be recursively closed")
        require(set(schema.get("required", [])) <= set(schema["properties"]), "source profile required fields")
        for child in schema["properties"].values():
            closed_source_schema(child)
    if "array" in types:
        require(isinstance(schema.get("items"), dict), "source array item profile required")
        closed_source_schema(schema["items"])


def adoption_base_sha(plan):
    p = copy.deepcopy(plan)
    p.pop("plan_content_sha256", None)
    p["production_adoption"] = None
    return object_sha(p)


def check_adoption(plan, reader):
    require(plan["data_mode"] in {"synthetic_control", "prospective_registered_inputs"}, "data mode")
    if plan["data_mode"] == "synthetic_control":
        require(plan["production_adoption"] is None, "constructed controls cannot assert production adoption")
        return
    require(plan["production_adoption"] is not None, "production adoption / common closed source qualification freeze absent; fail-closed")
    a = reader.json(plan["production_adoption"], "production adoption")
    exact(a, {"contract_version", "status", "campaign_id", "plan_base_sha256", "shared_source_contract",
              "native_method_addendum", "frozen_at", "verification", "qualification_scope"}, "production adoption")
    require(a["contract_version"] == VERSION and a["status"] == "ROOT_adopted_before_response_read_declared", "prospective ROOT adoption required")
    require(a["campaign_id"] == plan["campaign_id"] and a["plan_base_sha256"] == adoption_base_sha(plan), "adoption binds prospective plan")
    require(a["shared_source_contract"] == plan["source_contract"], "common source qualification binding")
    require(a["qualification_scope"] == "file_binding_and_contiguous_quotes_only" and a["verification"] == "declaration_not_independently_authenticated", "limited production qualification scope")
    require(timestamp(a["frozen_at"], "adoption") <= timestamp(plan["frozen_at"], "plan freeze"), "adoption after freeze")
    addendum = reader.json(a["native_method_addendum"], "native batch method addendum")
    require(object_sha(addendum) == object_sha(CONTEXT), "native context and file-display deviation must be explicitly adopted")


def sources(plan, reader):
    source = reader.json(plan["source_contract"], "source contract")
    exact(source, {"contract_version", "status", "packet_schema", "records"}, "source contract")
    require(source["contract_version"] == VERSION and source["status"] == "common_source_only_profile_frozen_declared", "common source-only profile contract")
    schema = reader.json(source["packet_schema"], "closed source profile")
    closed_source_schema(schema)
    Draft202012Validator.check_schema(schema)
    require([r["assignedID"] for r in source["records"]] == [r["assignedID"] for r in plan["sample"]["records"]], "source contract complete fixed order")
    result = {}
    for r in source["records"]:
        exact(r, {"assignedID", "source_id", "output_id", "packet", "source_content_sha256", "ctx_pointers",
                  "ctx_binding_sha256", "quote_fields", "asset_quote_views"}, "source record contract")
        packet = reader.json(r["packet"], "frozen original source packet")
        Draft202012Validator(schema).validate(packet)
        require(packet["source_id"] == r["source_id"] and packet["output_id"] == r["output_id"], "source identity mapping")
        require(object_sha(packet["source_bundle"]) == r["source_content_sha256"] == packet["source_bundle_sha256"], "canonical source content identity")
        require(isinstance(r["ctx_pointers"], list) and len(set(r["ctx_pointers"])) == len(r["ctx_pointers"]), "fixed CTX pointer list")
        ctx = [{"pointer": p, "value": validate_v17.pointer_value(packet, p)} for p in r["ctx_pointers"]]
        require(object_sha(ctx) == r["ctx_binding_sha256"], "CTX relationship binding")
        fields = {}
        for f in r["quote_fields"]:
            exact(f, {"pointer", "role", "text_sha256", "location_pointer", "location_sha256", "context_pointer", "context_sha256"}, "quote field")
            text = validate_v17.pointer_value(packet, f["pointer"])
            require(isinstance(text, str) and digest(text.encode("utf-8")) == f["text_sha256"], "quote field exact UTF8 text binding")
            require(f["role"] in {"current", "context"} and f["pointer"] not in fields, "unique source text pointer/role")
            loc = validate_v17.pointer_value(packet, f["location_pointer"])
            require(bool(loc) and object_sha(loc) == f["location_sha256"], "bound nonempty source location")
            if f["role"] == "context":
                require(f["context_pointer"] in r["ctx_pointers"] and object_sha(validate_v17.pointer_value(packet, f["context_pointer"])) == f["context_sha256"], "quote uses original frozen CTX")
            else:
                require(f["context_pointer"] is None and f["context_sha256"] is None, "current quote CTX declaration")
            fields[f["pointer"]] = f
        require(any(f["role"] == "current" for f in fields.values()), "current source text qualification absent")
        views = {}
        for v in r["asset_quote_views"]:
            exact(v, {"asset", "page", "pointer", "link_pointer", "link_sha256"}, "asset quote view")
            reader.read(v["asset"], "bound supplemental asset")
            require(v["pointer"] in fields, "supplemental quote must use qualified source text")
            link = validate_v17.pointer_value(packet, v["link_pointer"])
            require(object_sha(link) == object_sha({"asset_path": v["asset"]["path"], "asset_sha256": v["asset"]["sha256"], "page": v["page"], "text_pointer": v["pointer"]}) == v["link_sha256"], "frozen asset/page/text link absent")
            key = (v["asset"]["path"], str(v["page"]))
            require(key not in views, "duplicate asset/page qualification")
            views[key] = v
        result[r["assignedID"]] = {"contract": r, "packet": packet, "fields": fields, "views": views}
    return result


def validate_plan(plan, reader):
    exact(plan, {"contract_version", "data_mode", "campaign_id", "frozen_at", "configuration", "sample", "source_contract",
                 "production_adoption", "conditions", "plan_content_sha256"}, "plan")
    require(plan["contract_version"] == VERSION and plan["campaign_id"] and plan["campaign_id"] != "native-llm77-v17-sol", "new prospective campaign identity required; current v17 cannot be R1")
    unsigned = {k: v for k, v in plan.items() if k != "plan_content_sha256"}
    require(object_sha(unsigned) == plan["plan_content_sha256"], "plan seal mismatch")
    require(__debug__, "assert-based frozen v17 validator cannot run under python -O")
    require(digest((ROOT / "vendor/stability_engine.py").read_bytes()) == MATH_SHA and digest((ROOT / "vendor/validate_v17.py").read_bytes()) == V17_SHA, "frozen executed mathematics/validator drift")
    config = plan["configuration"]
    require(object_sha(config) == object_sha({"requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "provider_parameters": None,
                       "provider_session_state": "unknown", "actual_serving_model_independently_verified": False,
                       "native_batch_context_contract": CONTEXT}), "requested vs actual configuration/deviation disclosure")
    check_adoption(plan, reader)  # Must fail before opening any prospective source/output.
    sample = plan["sample"]
    exact(sample, {"selection_mode", "weight_kind", "target_domain", "selection_rule", "scope_limit", "frame_seal_sha256",
                   "all_target_units_positive_pi_declared", "records", "batches"}, "sample")
    require(sample["selection_mode"] in {"non_probability", "probability", "census"} and sample["weight_kind"] in {"equal", "preassigned_analytic", "inverse_probability"}, "sampling/weight kind")
    require(all(isinstance(sample[k], str) and sample[k] for k in ("target_domain", "selection_rule", "scope_limit")), "sample scope required")
    ids, recordmap, weights = [], {}, {}
    for r in sample["records"]:
        exact(r, {"assignedID", "source_id", "output_id", "weight", "inclusion_probability", "material_state", "material_pending_reason"}, "sample record")
        require(r["material_state"] == "complete" and r["material_pending_reason"] is None, "candidate accepts only explicitly frozen complete source packages; pending-source interface is not adopted")
        require(all(isinstance(r[k], str) and r[k] for k in ("assignedID", "source_id", "output_id")), "sample identities")
        require(r["assignedID"] not in recordmap, "duplicate assignedID")
        ids.append(r["assignedID"]); recordmap[r["assignedID"]] = r
        w = weights[r["assignedID"]] = math_engine.number(r["weight"], "weight")
        if sample["selection_mode"] == "non_probability":
            require(r["inclusion_probability"] is None and sample["weight_kind"] != "inverse_probability", "no fabricated probability weights")
        else:
            pi = math_engine.number(r["inclusion_probability"], "pi")
            require(pi <= 1 and w == 1 / pi, "inverse probability weight mismatch")
            if sample["selection_mode"] == "census":
                require(pi == 1 and w == 1, "census weight/pi")
        if sample["weight_kind"] == "equal":
            require(w == 1, "equal weight must equal one")
    require(ids and all(len({r[k] for r in recordmap.values()}) == len(ids) for k in ("source_id", "output_id")), "one-to-one sample identities")
    if sample["selection_mode"] == "probability":
        require(sample["weight_kind"] == "inverse_probability" and sample["frame_seal_sha256"] and sample["all_target_units_positive_pi_declared"] is True, "probability frame/positive pi declaration")
    batches = sample["batches"]
    require(isinstance(batches, list) and [i for b in batches for i in b["members"]] == ids and len({b["batch_id"] for b in batches}) == len(batches), "fixed complete batch partition/order")
    for b in batches:
        exact(b, {"batch_id", "members"}, "batch")
        require(isinstance(b["batch_id"], str) and b["batch_id"] and 1 <= len(b["members"]) <= 12, "native batch capacity")
    src = sources(plan, reader)
    for i in ids:
        require(all(src[i]["contract"][k] == recordmap[i][k] for k in ("source_id", "output_id")), "sample/source mapping drift")
    require(set(plan["conditions"]) == set(RUNS), "all five prospective diagnostic conditions required")
    assignments, routes, requests, context_names, original_paths = {}, {}, {}, set(), set()
    for run in RUNS:
        condition = plan["conditions"][run]
        exact(condition, {"role", "allowed_change", "batches"}, "condition")
        require(condition["role"] == math_engine.ROLES[run] and condition["allowed_change"] == math_engine.CHANGES[run], "fixed condition role/perturbation")
        require(set(condition["batches"]) == {b["batch_id"] for b in batches}, "condition batch coverage")
        for b in batches:
            bid = b["batch_id"]; binding = condition["batches"][bid]
            exact(binding, {"assignment", "exact_request", "routes"}, "condition batch binding")
            a = reader.json(binding["assignment"], "native frozen assignment")
            require(a["run_id"] == plan["campaign_id"] and a["batch_id"] == bid and a["expected_N"] == len(b["members"]) and a["context_unit"] == "batch", "prospective native assignment identity")
            require(a["requested_model"] == "gpt-6.1-sol" and a["requested_reasoning_effort"] == "ultra", "assignment configuration")
            require(a["source_ids"] == [recordmap[i]["source_id"] for i in b["members"]], "assignment member order")
            require(type(a["max_total_technical_attempts"]) is int and a["max_total_technical_attempts"] == 3 and type(a["max_technical_retries"]) is int and a["max_technical_retries"] == 2, "frozen max3 policy")
            require(isinstance(a["scope"], str) and a["scope"], "native assignment scope")
            require(Path(binding["assignment"]["path"]) == Path(a["output_directory"]) / "assignment.json", "native assignment directory")
            for ref in [*[a[k] for k in INPUT_KEYS], *a["packets"], *a["source_asset_bindings"]]:
                reader.read(ref, "assignment bound input")
            require(a["strict_technical_validator"]["sha256"] == V17_SHA and a["packet_schema"] == reader.json(plan["source_contract"], "source contract")["packet_schema"], "executed validator/common source schema binding")
            require(object_sha(reader.json(a["output_schema"], "prospective output schema")) == object_sha(schema_for_assignment(a)), "prospective schema differs beyond permitted identity/N substitution")
            require([p["source_id"] for p in a["packets"]] == a["source_ids"], "ordered native packet bindings")
            for i, ref in zip(b["members"], a["packets"]):
                packet = reader.json(ref, "condition packet")
                require(object_sha(packet) == object_sha(src[i]["packet"]) and ref["output_id"] == recordmap[i]["output_id"], "condition canonical source/CTX content changed")
                expected_raw = json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n" if run == "W" else reader.read(src[i]["contract"]["packet"], "main packet exact bytes")
                require(reader.read(ref, "condition packet raw") == expected_raw, "only frozen W JSON display may change packet bytes")
            require(len(binding["routes"]) == 3, "exactly three reserved native attempt routes")
            route_file = reader.json(a["attempt_output_routing"], "native output routing")
            require(type(route_file["max_total_technical_attempts"]) is int and route_file["max_total_technical_attempts"] == 3 and type(route_file["max_technical_retries"]) is int and route_file["max_technical_retries"] == 2, "route max3")
            for n, route in enumerate(binding["routes"], 1):
                require(route in route_file["routes"] and route["condition_id"] == run and route["batch_id"] == bid and type(route["attempt_number"]) is int and route["attempt_number"] == n, "frozen native route selection")
                require(route["runtime_task_name"] not in context_names and route["structured_first_path"] not in original_paths, "unique reserved runtime/output slot")
                context_names.add(route["runtime_task_name"]); original_paths.add(route["structured_first_path"])
                require(Path(a["output_directory"]) in Path(route["structured_first_path"]).parents, "original slot outside assigned native directory")
            assignments[run, bid], routes[run, bid] = a, binding["routes"]
            requests[run, bid] = reader.read(binding["exact_request"], "exact native initial dispatch text")
    for b in batches:
        bid = b["batch_id"]; main = assignments["R1", bid]
        for run in RUNS:
            a = assignments[run, bid]
            require(requests[run, bid] == requests["R1", bid], "native initial dispatch text must stay exactly fixed; route is external metadata")
            require(a["manual"] == main["manual"], "manual drift")
            require(a["scope"] == main["scope"] and object_sha(a["source_asset_bindings"]) == object_sha(main["source_asset_bindings"]), "scope/asset delivery binding drift")
            for key in set(INPUT_KEYS) - {"execution_prompt", "output_schema"}:
                require(object_sha(a[key]) == object_sha(main[key]), "unpermitted condition input drift: " + key)
            main_prompt = reader.read(main["execution_prompt"], "main prompt")
            require(main_prompt.startswith("判读要求\n".encode()), "frozen neutral heading must be first line")
            expected_prompt = "判读说明\n".encode() + main_prompt[len("判读要求\n".encode()):] if run == "H" else main_prompt
            require(reader.read(a["execution_prompt"], "condition prompt") == expected_prompt, "only H heading may change execution prompt")
            if run in {"R2", "R3"}:
                require(plan["conditions"][run]["batches"][bid]["assignment"] == plan["conditions"]["R1"]["batches"][bid]["assignment"], "R1/R2/R3 reuse same frozen assignment and substantive request")
    return {"ids": ids, "records": recordmap, "weights": weights, "sources": src, "batch_plan": batches,
            "assignments": assignments, "routes": routes, "frozen_at": timestamp(plan["frozen_at"], "freeze")}


def qualify(assignment_ref, original_ref, meta, run, bid, reader):
    """No labels or record pointers escape a failing whole batch."""
    try:
        raw = reader.read(original_ref, "unaltered complete native structured submission")
        submission = parse(raw, "whole native structured submission UTF8")
        receipt = validate_v17.verify(assignment_ref["path"], original_ref["path"])
        require(receipt["submission_sha256"] == original_ref["sha256"] and receipt["submission_bytes"] == original_ref["bytes"], "original changed while frozen validator was checking")
        reader.read(original_ref, "original integrity after validator")
        members = next(b["members"] for b in meta["batch_plan"] if b["batch_id"] == bid)
        checks = []
        for n, i in enumerate(members):
            record = submission["records"][n]; src = meta["sources"][i]
            for d in DIMS:
                value = record["dimensions"][d]["value"]
                require(value is None or type(value) is int and value in (0, 1), "parsed original value must be exact int 0/1 or null")
                for ev in record["dimensions"][d]["evidence"]:
                    if "pointer" in ev:
                        exact(ev, {"pointer", "quote", "role"}, "packet evidence")
                        f = src["fields"].get(ev["pointer"])
                        require(f and f["role"] == ev["role"], "quote pointer/role outside frozen source qualification")
                        text = validate_v17.pointer_value(src["packet"], ev["pointer"])
                    else:
                        exact(ev, {"asset_path", "asset_sha256", "page", "quote", "role"}, "supplemental evidence")
                        view = src["views"].get((ev["asset_path"], str(ev["page"])))
                        require(view and object_sha(view["page"]) == object_sha(ev["page"]) and view["asset"]["sha256"] == ev["asset_sha256"] and src["fields"][view["pointer"]]["role"] == ev["role"], "no frozen asset/page contiguous-text qualification")
                        presented = [entry for entry in submission["read_manifest"]["files"] if entry["path"] == ev["asset_path"] and record["source_id"] in entry["source_ids"]]
                        require(presented and any(r["range_kind"] == "full_image" or type(ev["page"]) is int and r["range_kind"] == "physical_pages" and r["start"] <= ev["page"] <= r["end"] for entry in presented for r in entry["actual_presented_ranges"]), "supplemental asset page presentation declaration absent")
                        text = validate_v17.pointer_value(src["packet"], view["pointer"])
                    require(isinstance(ev["quote"], str) and ev["quote"] and ev["quote"] in text, "quote is not a contiguous exact string in frozen qualified location")
            checks.append({"assignedID": i, "pointer": f"/records/{n}", "source_binding_and_exact_quotes_checked": True})
        return submission, {"technical_valid": True, "record_checks": checks, "reason": None}
    except (ContractError, AssertionError, ValueError, TypeError, KeyError, IndexError, OSError, ValidationError, SchemaError) as exc:
        return None, {"technical_valid": False, "record_checks": [], "reason": str(exc), "no_partially_valid_record_extracted": True}


def analyze(plan_path, ledger_path, compare_requested=False):
    reader = BoundReader()
    plan_raw, ledger_raw = Path(plan_path).read_bytes(), Path(ledger_path).read_bytes()
    plan, ledger = parse(plan_raw, "plan"), parse(ledger_raw, "ledger")
    meta = validate_plan(plan, reader)
    exact(ledger, {"contract_version", "plan_file_sha256", "runs"}, "ledger")
    require(ledger["contract_version"] == VERSION and ledger["plan_file_sha256"] == digest(plan_raw) and set(ledger["runs"]) == set(RUNS), "ledger binds full five-condition plan")
    selected, firsts, audit, contexts, terminal_conditions = {}, {}, {}, set(), []
    for run in RUNS:
        stream = ledger["runs"][run]
        exact(stream, {"batches", "seal"}, "condition ledger")
        require([b["batch_id"] for b in stream["batches"]] == [b["batch_id"] for b in meta["batch_plan"]], "complete ordered condition batch ledger")
        selected[run], firsts[run], audit[run] = {}, {}, []
        ends, terminal = [], True
        for row, b in zip(stream["batches"], meta["batch_plan"]):
            exact(row, {"batch_id", "attempts", "not_called", "first"}, "batch ledger")
            bid = b["batch_id"]; attempts = row["attempts"]
            require(isinstance(attempts, list) and len(attempts) <= 3, "max3 actual whole-batch technical attempts")
            first, response, checks, previous = None, None, [], None
            binding = plan["conditions"][run]["batches"][bid]
            for n, attempt in enumerate(attempts, 1):
                require(first is None, "attempt after earliest valid complete batch, including legal null")
                exact(attempt, {"attempt_number", "started_at", "ended_at", "assignment_sha256", "exact_request_sha256", "dispatch", "transport_status", "failure_reason", "original", "failure_files"}, "attempt")
                require(type(attempt["attempt_number"]) is int and attempt["attempt_number"] == n, "consecutive exact integer attempts")
                start, end = timestamp(attempt["started_at"], "start"), timestamp(attempt["ended_at"], "end")
                require(start >= meta["frozen_at"] and end >= start and (previous is None or start >= previous), "freeze/attempt chronological declarations")
                previous = end; ends.append(end)
                require(attempt["assignment_sha256"] == binding["assignment"]["sha256"] and attempt["exact_request_sha256"] == binding["exact_request"]["sha256"], "same frozen attempt assignment/request")
                dispatch = attempt["dispatch"]
                exact(dispatch, {"runtime_task_name", "context_id", "requested_model", "requested_reasoning_effort", "fork_turns", "previous_output_exposure_declared", "actual_tool_request", "actual_tool_creation_receipt", "evidence_kind"}, "dispatch")
                route = meta["routes"][run, bid][n - 1]
                require(dispatch["runtime_task_name"] == route["runtime_task_name"] and isinstance(dispatch["context_id"], str) and dispatch["context_id"] and dispatch["context_id"] not in contexts, "unique native context / runtime route")
                contexts.add(dispatch["context_id"])
                require(dispatch["requested_model"] == "gpt-6.1-sol" and dispatch["requested_reasoning_effort"] == "ultra" and dispatch["fork_turns"] == "none" and dispatch["previous_output_exposure_declared"] is False, "fresh requested configuration without previous answer exposure")
                if plan["data_mode"] == "synthetic_control":
                    require(dispatch["evidence_kind"] == "constructed_declaration" and dispatch["actual_tool_request"] is None and dispatch["actual_tool_creation_receipt"] is None, "synthetic cannot fabricate native tool receipts")
                else:
                    require(dispatch["evidence_kind"] == "file_bound_native_tool_evidence" and dispatch["actual_tool_request"] is not None, "real native tool request file missing")
                    reader.read(dispatch["actual_tool_request"], "native tool request evidence; not authenticated by SHA")
                    if dispatch["actual_tool_creation_receipt"] is not None:
                        reader.read(dispatch["actual_tool_creation_receipt"], "native creation receipt; not provider identity")
                    else:
                        require(attempt["transport_status"] == "failed", "successful real attempt requires native creation receipt file")
                for ref in attempt["failure_files"]:
                    reader.read(ref, "preserved actual failure artifact")
                if attempt["original"] is not None:
                    exact(attempt["original"], {"path", "bytes", "sha256"}, "original file binding")
                    require(attempt["original"]["path"] == route["structured_first_path"], "unaltered original file must be reserved native slot")
                    reader.read(attempt["original"], "retained original candidate bytes")
                if attempt["transport_status"] == "failed":
                    require(isinstance(attempt["failure_reason"], str) and attempt["failure_reason"] and (attempt["failure_files"] or attempt["original"] is not None), "transport failure retains real failure bytes")
                    check = {"technical_valid": False, "reason": attempt["failure_reason"], "record_checks": []}
                else:
                    require(attempt["transport_status"] == "ok" and attempt["failure_reason"] is None and attempt["original"] is not None, "ok transport preserves whole original bytes")
                    response_candidate, check = qualify(binding["assignment"], attempt["original"], meta, run, bid, reader)
                    if check["technical_valid"]:
                        response = response_candidate
                        first = {"attempt_number": n, "original": attempt["original"], "parsed_batch_sha256": object_sha(response)}
                checks.append({"attempt_number": n, "original": attempt["original"], "failure_files": attempt["failure_files"], **check})
            if attempts:
                require(row["not_called"] is None, "attempted batch cannot be not-called")
                state = "first_technically_valid_complete_batch" if first else "technical_failure"
                batch_terminal = first is not None or len(attempts) == 3
            else:
                nc = row["not_called"]
                exact(nc, {"state", "reason", "terminal_without_attempt"}, "not-called")
                require(nc["state"] in math_engine.NOT_CALLED and isinstance(nc["reason"], str) and nc["reason"], "zero-attempt explicit state/reason")
                require(type(nc["terminal_without_attempt"]) is bool and (not nc["terminal_without_attempt"] or nc["state"] in {"precheck_blocked", "material_blocked"}), "only explicit precheck/material block may terminate without model attempt")
                state, batch_terminal = "not_called", nc["terminal_without_attempt"]
            require(object_sha(row["first"]) == object_sha(first), "claimed first must equal earliest technically valid whole original batch")
            terminal = terminal and batch_terminal
            for index, i in enumerate(b["members"]):
                record = response["records"][index] if response is not None else None
                labels = {d: record["dimensions"][d]["value"] for d in DIMS} if record else None
                origin = None if first is None else {**first, "condition_id": run, "batch_id": bid, "assignedID": i,
                    "source_id": record["source_id"], "output_id": record["output_id"], "packet_sha256": record["packet_sha256"],
                    "extraction_pointer": f"/records/{index}", "derived_record_sha256": object_sha(record), "derived_record_is_original_response": False,
                    "raw_response": first["original"], "exact_request": binding["exact_request"], "original_assignment": binding["assignment"]}
                firsts[run][i] = origin
                selected[run][i] = {"state": state if record is None else "valid_semantic_null" if any(v is None for v in labels.values()) else "valid_binary",
                    "labels": labels, "first": origin, "not_called": row["not_called"], "material_state": meta["records"][i]["material_state"],
                    "failure_exhausted_three_attempts": state == "technical_failure" and len(attempts) == 3,
                    "remaining_retry_slots_if_unresolved": 3 - len(attempts) if state == "technical_failure" else 0}
            audit[run].append({"batch_id": bid, "state": state, "recorded_whole_batch_attempt_n": len(attempts), "attempts": checks,
                               "first": first, "terminal": batch_terminal, "no_record_splicing": True,
                               "attempt_counts_are_file_bound_ledger_declarations": True})
        seal = stream["seal"]
        exact(seal, {"status", "content_sha256", "sealed_at", "verification"}, "condition seal")
        require(seal["status"] == ("condition_terminal_sealed" if terminal else "snapshot_not_terminal") and seal["content_sha256"] == object_sha({"batches": stream["batches"]}), "terminal status/content seal must match every planned batch")
        require(seal["verification"] == "declaration_not_independently_verified", "seal chronology cannot be authenticated by hash")
        at = timestamp(seal["sealed_at"], "seal time")
        require(at >= meta["frozen_at"] and all(at >= t for t in ends), "seal time precedes declared attempt completion")
        terminal_conditions.append(terminal)
    unlocked = all(terminal_conditions)
    require(not compare_requested or unlocked, "comparison requested before all R1/R2/R3/W/H terminal seals; fail-closed")
    for ref in list(reader.seen.values()):
        reader.read(ref, "input integrity before any comparison")
    pairs, triple = statistics(plan, meta, selected, firsts) if compare_requested else ({}, None)
    return {"contract_version": VERSION, "data_mode": plan["data_mode"], "campaign_id": plan["campaign_id"],
        "comparison_gate": {"unlocked": unlocked, "comparison_requested": compare_requested, "all_five_terminal_seals_required": True},
        "paired_comparisons": pairs, "three_main_runs": triple, "per_record_states": selected, "origins": firsts, "audit": audit,
        "qualifications": {"scope": "frozen_file_binding_and_contiguous_quotes_only", "actual_tool_reading_authenticated": False,
            "source_package_completeness": "declared_in_frozen_plan; semantic_adequacy_not_checked",
            "actual_serving_model_identity_authenticated": False, "actual_context_independence_authenticated": False,
            "provider_wire_capture_claimed": False, "native_batch_attempt_n_is_provider_API_call_n": False,
            "current_v17_retroactively_R1": False, "classification_correctness_checked": False, "human_reliability_measured": False,
            "confidence_intervals_computed": False, "stability_pass_threshold": None, "project_completion_decision": False},
        "input_bindings": {"plan_file_sha256": digest(plan_raw), "ledger_file_sha256": digest(ledger_raw), "files": sorted(reader.seen.values(), key=lambda x: x["path"])}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", required=True); p.add_argument("--ledger", required=True)
    p.add_argument("--out", required=True); p.add_argument("--compare", action="store_true")
    args = p.parse_args()
    try:
        require(not Path(args.out).exists(), "refuse to overwrite prior result")
        result = analyze(args.plan, args.ledger, args.compare)
        with Path(args.out).open("xb") as stream:
            stream.write(canonical(result) + b"\n")
    except (ContractError, OSError, ValueError, KeyError, TypeError, AssertionError, ValidationError, SchemaError) as exc:
        print(json.dumps({"status": "rejected", "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": "qualified_native_records_files", "data_mode": result["data_mode"], "comparison_unlocked": result["comparison_gate"]["unlocked"], "actual_model_calls_made_by_adapter": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
