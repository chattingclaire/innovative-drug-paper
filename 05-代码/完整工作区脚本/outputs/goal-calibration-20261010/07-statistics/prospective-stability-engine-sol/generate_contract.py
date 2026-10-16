#!/usr/bin/env python3
"""Generate the static JSON Schema companion; Python enforces cross-file semantics."""
import json
from pathlib import Path
from stability_engine import VERSION, DIMS, RUNS, CHECKS, PAIRS


def obj(properties, required=None):
    return {"type": "object", "properties": properties, "required": list(properties) if required is None else required,
            "additionalProperties": False}


def ref(name):
    return {"$ref": f"#/$defs/{name}"}


def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


def string():
    return {"type": "string", "minLength": 1}


def enum(*values):
    return {"enum": list(values)}


def array(item, minimum=0):
    return {"type": "array", "items": item, "minItems": minimum}


def generate():
    sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    date = {"type": "string", "format": "date-time"}
    ids = {"type": "array", "items": string(), "minItems": 1, "uniqueItems": True}
    numeric = {"anyOf": [{"type": "number", "exclusiveMinimum": 0},
                           {"type": "string", "pattern": "^[0-9]+(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+|/[0-9]+)?$"}]}
    defs = {}
    defs["fileRef"] = obj({"path": string(), "sha256": sha})
    defs["artifact"] = obj({"version": string(), "artifact": ref("fileRef")})
    defs["material"] = obj({"version": string(), "source_packet": ref("fileRef"), "source_semantic_sha256": sha,
                             "ctx_binding": {}, "ctx_binding_sha256": sha})
    defs["assignedRecord"] = obj({"assignedID": string(), "weight": numeric, "inclusion_probability": nullable(numeric),
                                   "material_state": enum("complete", "pending"), "material_pending_reason": nullable(string()), "material": ref("material")})
    defs["batch"] = obj({"batch_id": string(), "members": ids})
    defs["sample"] = obj({"selection_mode": enum("probability", "non_probability", "census"),
                          "weight_kind": enum("equal", "preassigned_analytic", "inverse_probability"),
                          "target_domain": string(), "selection_rule": string(), "scope_limit": string(),
                          "frame_seal_sha256": nullable(sha), "all_target_units_positive_pi_declared": {"type": "boolean"},
                          "assigned_records": array(ref("assignedRecord"), 1), "ordered_assignedIDs": ids, "batches": array(ref("batch"), 1)})
    defs["commonArtifacts"] = obj({name: ref("artifact") for name in ("manual", "prompt", "output_schema", "adapter", "technical_validator", "protocol")})
    defs["configuration"] = obj({"intended_model": string(), "intended_reasoning_effort": string(), "provider_requested": string(),
                                 "request_settings": {"type": "object"},
                                 "provider_session_state": enum("stateless_declared_unverified", "stateful_declared_unverified", "unknown"),
                                 "actual_model_identity_status": {"const": "not_proven_by_requested_identity_or_hash"}})
    defs["requestBinding"] = obj({"exact_request": ref("fileRef"), "source_semantic_sha256": sha, "ctx_binding_sha256": sha})
    defs["condition"] = obj({"run_id": enum(*RUNS), "role": enum("production", "diagnostic_main", "diagnostic_whitespace", "diagnostic_heading"),
                              "allowed_change": enum("none", "source_json_compact_to_indent2", "user_first_line_synonym"),
                              "common_configuration_sha256": sha, "common_artifacts_sha256": sha, "sample_plan_sha256": sha,
                              "context_unit": enum("record", "batch"),
                              "planned_contexts": {"type": "object", "additionalProperties": string(), "minProperties": 1},
                              "requests": {"type": "object", "additionalProperties": ref("requestBinding"), "minProperties": 1}})
    defs["registry"] = obj({"contract_version": {"const": VERSION}, "data_mode": enum("synthetic_control", "prospective_registered_inputs"),
                             "dimensions": {"const": list(DIMS)},
                             "registration": obj({"registry_id": string(), "status": {"const": "frozen_before_response_read"},
                                                  "frozen_at": date, "verification": {"const": "declaration_not_independently_verified"}}),
                             "sample": ref("sample"), "common_artifacts": ref("commonArtifacts"), "common_configuration": ref("configuration"),
                             "context_unit": enum("record", "batch"),
                             "context_independence_declaration": obj({"declared_independent": {"type": "boolean"}, "verification": {"const": "not_independently_verified"}, "basis": string()}),
                             "allow_pending_material_for_valid_response": {"type": "boolean"},
                             "retry_policy": {"const": {"max_actual_attempts": 3, "selection": "first_technically_valid_complete_response",
                                                        "semantic_null_stops_retry": True, "same_exact_request_only": True}},
                             "comparison_plan": {"const": {"pairs": [list(p) for p in PAIRS], "three_way": ["R1", "R2", "R3"], "perturbation_baseline": "R1"}},
                             "stability_pass_threshold": {"type": "null"}, "confidence_interval_gate": {"type": "null"},
                             "conditions": obj({run: ref("condition") for run in RUNS}), "registry_content_sha256": sha})
    defs["context"] = obj({"context_unit": enum("record", "batch"), "planned_context_id": string(),
                            "previous_output_exposure_declared": {"const": False}, "verification": {"const": "not_independently_verified"}})
    defs["providerReceipt"] = obj({"status": enum("unavailable", "observed_unverified"), "request_id": nullable(string()),
                                   "returned_model": nullable(string()), "configuration_evidence": {}})
    defs["attempt"] = obj({"attempt_number": {"type": "integer", "minimum": 1, "maximum": 3}, "started_at": date, "ended_at": date,
                            "executed_configuration": ref("configuration"), "request_binding": ref("requestBinding"), "context": ref("context"),
                            "provider_receipt": ref("providerReceipt"), "transport_status": enum("ok", "failure"), "transport_reason": nullable(string()),
                            "raw_response": nullable(ref("fileRef")), "validator_report": nullable(ref("fileRef"))})
    defs["inputFirst"] = obj({"run_id": enum(*RUNS), "assignedID": string(), "attempt_number": {"type": "integer", "minimum": 1, "maximum": 3},
                               "raw_response": ref("fileRef"), "parsed_response_sha256": sha})
    defs["row"] = obj({"assignedID": string(), "order_index": {"type": "integer", "minimum": 1}, "batch_id": string(),
                        "attempts": {"type": "array", "items": ref("attempt"), "maxItems": 3},
                        "not_called": nullable(obj({"state": enum("not_called", "precheck_blocked", "material_blocked", "creation_empty"), "reason": string()})),
                        "first": nullable(ref("inputFirst"))})
    defs["runLedger"] = obj({"registered_condition_sha256": sha, "records": array(ref("row"), 1)})
    defs["ledger"] = obj({"contract_version": {"const": VERSION}, "data_mode": enum("synthetic_control", "prospective_registered_inputs"),
                           "registry_file_sha256": sha, "firsts_selection_rule": {"const": "first_technically_valid_complete_response"},
                           "runs": obj({run: ref("runLedger") for run in RUNS})})
    defs["rawResponse"] = obj({"assignedID": string(), "labels": obj({d: enum(0, 1, None) for d in DIMS}),
                                "reasons": obj({d: string() for d in DIMS}),
                                "null_reasons": obj({d: string() for d in DIMS}, required=[]),
                                "material_requests": obj({d: string() for d in DIMS}, required=[]),
                                "evidence": obj({d: {} for d in DIMS})})
    defs["validatorReport"] = obj({"validator_artifact_sha256": sha, "exact_request_sha256": sha, "raw_response_sha256": sha,
                                    "checks": obj({k: {"type": "boolean"} for k in CHECKS}), "failure_reasons": array(string())})
    defs["promptAssembly"] = obj({"system_prefix": {"type": "string"}, "system_suffix": {"type": "string"},
                                   "user_prefix": {"type": "string", "pattern": "^判读要求\\n"}, "user_suffix": {"type": "string"}, "payload_template": {}})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:prospective-stability-engine-sol:v1:inputs",
            "title": "Frozen registry or complete condition ledger",
            "$comment": "Shape companion only. Cross-file hashes, exact request assembly, first-valid chronology, source semantics, sampling weights, five-dimension null rules and comparison scope are enforced by stability_engine.py. SHA never proves actual model/context identity.",
            "oneOf": [ref("registry"), ref("ledger")], "$defs": defs}


if __name__ == "__main__":
    path = Path(__file__).resolve().parent / "input-contract.json"
    path.write_text(json.dumps(generate(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)
