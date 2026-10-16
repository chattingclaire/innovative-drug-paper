#!/usr/bin/env python3
"""Create ONLY invented inputs and finite mathematical counterexamples."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

from stability_engine import (VERSION, DIMS, RUNS, PAIRS, CHECKS, ROLES, CHANGES,
                              canonical, digest, object_sha, request_bytes)


def write_ref(base, relative, data):
    p = base / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return {"path": relative, "sha256": digest(data)}


def json_bytes(value):
    # Registry/ledger registration order is meaningful; preserve insertion order.
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def response(i, labels):
    nulls = [d for d, value in zip(DIMS, labels) if value is None]
    return {"assignedID": i, "labels": dict(zip(DIMS, labels)),
            "reasons": {d: "构造数学控制理由；无真实政策语义" for d in DIMS},
            "null_reasons": {d: "构造的合法语义待定" for d in nulls},
            "material_requests": {d: "构造的待补材料请求" for d in nulls},
            "evidence": {d: [] for d in DIMS}}


def make_fixture(base, mode="mixed", context_unit="record", probability=False):
    base = Path(base)
    if base.exists() and any(base.iterdir()):
        raise ValueError(f"Refusing to overwrite existing controls: {base}")
    base.mkdir(parents=True, exist_ok=True)
    ids = [f"TOY-{n:03d}" for n in range(1, 9)]
    weights = list(range(1, 9))
    prompt = {"system_prefix": "构造请求，共用手册：\n", "system_suffix": "\n",
              "user_prefix": "判读要求\n", "user_suffix": "\n只按构造契约返回五维。",
              "payload_template": {"settings": "{{REQUEST_SETTINGS}}", "messages": [
                  {"role": "system", "content": "{{SYSTEM_CONTENT}}"}, {"role": "user", "content": "{{USER_CONTENT}}"}]}}
    toy_artifacts = {"manual": b"S E Ec I F toy-only manual; no real source or truth labels.\n",
                     "prompt": json_bytes(prompt), "output_schema": json_bytes({"toy_schema": "labels exactly S/E/Ec/I/F 0/1/null; reasons/evidence/null reasons/material requests required"}),
                     "adapter": b"toy opaque source JSON adapter v1\n",
                     "technical_validator": b"constructed validator supplied assertions; not a production quote validator\n",
                     "protocol": b"toy fixture follows read-only prospective stability protocol; no actual execution\n"}
    artifacts = {name: {"version": "toy-v1", "artifact": write_ref(base, f"artifacts/{name}.txt", data)} for name, data in toy_artifacts.items()}
    records, packets = [], {}
    for i, w in zip(ids, weights):
        # Internal double whitespace/newline demonstrates preservation under W.
        packet = {"assignedID": i, "source_text": f"构造来源 {i}：a  b\n第二行。", "contexts": [{"CTXID": f"CTX-{i}", "text": "构造语境"}]}
        packets[i] = packet
        ctx = [{"CTXID": f"CTX-{i}", "source_pointer": "contexts/0"}]
        records.append({"assignedID": i, "weight": str(w), "inclusion_probability": str(1 / w) if probability else None,
                        "material_state": "pending" if i == ids[6] and mode == "mixed" else "complete",
                        "material_pending_reason": "构造的共同材料预检阻断" if i == ids[6] and mode == "mixed" else None,
                        "material": {"version": "toy-source-v1", "source_packet": write_ref(base, f"materials/{i}.json", json_bytes(packet)),
                                     "source_semantic_sha256": object_sha(packet), "ctx_binding": ctx, "ctx_binding_sha256": object_sha(ctx)}})
    # Fractions are precise input strings; reciprocal weights must match exactly.
    if probability:
        for record, w in zip(records, weights):
            record["inclusion_probability"] = f"1/{w}"
    sample = {"selection_mode": "probability" if probability else "non_probability",
              "weight_kind": "inverse_probability" if probability else "preassigned_analytic",
              "target_domain": "eight invented TOY units only", "selection_rule": "all invented mathematical-control rows, fixed before constructed outputs",
              "scope_limit": "toy controls only; no project sample/population inference", "frame_seal_sha256": digest(b"toy-frame-eight") if probability else None,
              "all_target_units_positive_pi_declared": True if probability else False,
              "assigned_records": records, "ordered_assignedIDs": ids,
              "batches": [{"batch_id": "B1", "members": ids[:4]}, {"batch_id": "B2", "members": ids[4:]}]}
    reg = {"contract_version": VERSION, "data_mode": "synthetic_control", "dimensions": list(DIMS),
           "registration": {"registry_id": f"toy-{mode}-{context_unit}", "status": "frozen_before_response_read",
                            "frozen_at": "2026-10-09T00:00:00+00:00", "verification": "declaration_not_independently_verified"},
           "sample": sample, "common_artifacts": artifacts,
           "common_configuration": {"intended_model": "GPT-6.1 Sol (requested toy identity; never invoked)", "intended_reasoning_effort": "ultra",
                                    "provider_requested": "toy-no-provider", "request_settings": {"toy_controllable_parameter": "fixed", "toy_numeric_parameter": 1},
                                    "provider_session_state": "unknown", "actual_model_identity_status": "not_proven_by_requested_identity_or_hash"},
           "context_unit": context_unit,
           "context_independence_declaration": {"declared_independent": True, "verification": "not_independently_verified",
                                                "basis": "invented context identifiers; no provider execution or independent evidence"},
           "allow_pending_material_for_valid_response": False,
           "retry_policy": {"max_actual_attempts": 3, "selection": "first_technically_valid_complete_response", "semantic_null_stops_retry": True, "same_exact_request_only": True},
           "comparison_plan": {"pairs": [list(p) for p in PAIRS], "three_way": ["R1", "R2", "R3"], "perturbation_baseline": "R1"},
           "stability_pass_threshold": None, "confidence_interval_gate": None, "conditions": {}}
    for run in RUNS:
        units = ids if context_unit == "record" else ["B1", "B2"]
        condition = {"run_id": run, "role": ROLES[run], "allowed_change": CHANGES[run],
                     "common_configuration_sha256": object_sha(reg["common_configuration"]), "common_artifacts_sha256": object_sha(artifacts),
                     "sample_plan_sha256": object_sha(sample), "context_unit": context_unit,
                     "planned_contexts": {u: f"TOY-CONTEXT-{run}-{u}" for u in units}, "requests": {}}
        for i in ids:
            condition["requests"][i] = {"exact_request": write_ref(base, f"requests/{run}/{i}.json", request_bytes(reg, prompt, toy_artifacts["manual"], packets[i], run)),
                                        "source_semantic_sha256": records[ids.index(i)]["material"]["source_semantic_sha256"],
                                        "ctx_binding_sha256": records[ids.index(i)]["material"]["ctx_binding_sha256"]}
        reg["conditions"][run] = condition
    reg["registry_content_sha256"] = object_sha(reg)
    registry_bytes = json_bytes(reg)
    (base / "registry.json").write_bytes(registry_bytes)
    z = [0, 0, 0, 0, 0]
    r1 = [z, [1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [1, 1, 1, 1, 1], [1, 0, 0, None, 0], "failure", "not_called", z]
    r2 = [z, [1, 0, 0, 0, 0], [0, 1, 0, 1, 0], [0, 1, 1, 1, 1], [1, 0, 0, 0, 0], z, "not_called", [0, 0, 0, 0, None]]
    r3 = [z, [1, 0, 0, 1, 0], [0, 1, 0, 0, 0], [1, 1, 1, 1, 1], [1, 0, 0, None, 0], z, "not_called", z]
    w = [z, [1, 0, 0, 0, 0], [0, 1, 0, 1, 0], [1, 1, 1, 1, 1], [1, 0, 0, None, 0], z, "not_called", z]
    h = copy.deepcopy(w)
    p = [z, [1, 0, 0, None, 0], "failure", z, z, z, "not_called", z]
    labels = {"P": p, "R1": r1, "R2": r2, "R3": r3, "W": w, "H": h}
    if mode == "all_zero":
        labels = {run: [z] * 8 for run in RUNS}
    elif mode == "rare":
        labels = {run: [z] * 7 + [[0, 0, 0, 0, 1]] for run in RUNS}
    ledger = {"contract_version": VERSION, "data_mode": "synthetic_control", "registry_file_sha256": digest(registry_bytes),
              "firsts_selection_rule": "first_technically_valid_complete_response", "runs": {}}
    for run in RUNS:
        c = reg["conditions"][run]
        stream = {"registered_condition_sha256": object_sha(c), "records": []}
        for index, i in enumerate(ids):
            state = labels[run][index]
            batch = "B1" if index < 4 else "B2"
            row = {"assignedID": i, "order_index": index + 1, "batch_id": batch, "attempts": [], "not_called": None, "first": None}
            if state == "not_called":
                row["not_called"] = {"state": "material_blocked", "reason": "构造预检阻断；实际尝试数为零"}
            else:
                sequence = ["transport_failure", "bad_schema", "transport_failure"] if state == "failure" else (
                    ["bad_schema", state] if mode == "mixed" and run == "P" and index == 0 else [state])
                for n, value in enumerate(sequence, 1):
                    a = {"attempt_number": n, "started_at": f"2026-10-09T01:00:{2*n:02d}+00:00", "ended_at": f"2026-10-09T01:00:{2*n+1:02d}+00:00",
                         "executed_configuration": copy.deepcopy(reg["common_configuration"]), "request_binding": copy.deepcopy(c["requests"][i]),
                         "context": {"context_unit": context_unit, "planned_context_id": c["planned_contexts"][i if context_unit == "record" else batch],
                                     "previous_output_exposure_declared": False, "verification": "not_independently_verified"},
                         "provider_receipt": {"status": "unavailable", "request_id": None, "returned_model": None, "configuration_evidence": None},
                         "transport_status": "failure" if value == "transport_failure" else "ok",
                         "transport_reason": "constructed transport interruption" if value == "transport_failure" else None,
                         "raw_response": None, "validator_report": None}
                    if value != "transport_failure":
                        obj = response(i, z if value == "bad_schema" else value)
                        if value == "bad_schema":
                            del obj["labels"]["F"]
                        raw = canonical(obj)
                        a["raw_response"] = write_ref(base, f"responses/{run}/{i}/attempt-{n}.json", raw)
                        checks = {k: True for k in CHECKS}
                        if value == "bad_schema":
                            checks["five_dimensions"] = checks["response_schema"] = False
                        report = {"validator_artifact_sha256": artifacts["technical_validator"]["artifact"]["sha256"],
                                  "exact_request_sha256": c["requests"][i]["exact_request"]["sha256"], "raw_response_sha256": digest(raw),
                                  "checks": checks, "failure_reasons": ["constructed missing F invalidates entire response"] if value == "bad_schema" else []}
                        a["validator_report"] = write_ref(base, f"responses/{run}/{i}/validation-{n}.json", json_bytes(report))
                        if value != "bad_schema":
                            row["first"] = {"run_id": run, "assignedID": i, "attempt_number": n,
                                            "raw_response": copy.deepcopy(a["raw_response"]), "parsed_response_sha256": object_sha(obj)}
                    row["attempts"].append(a)
            stream["records"].append(row)
        ledger["runs"][run] = stream
    (base / "ledger.json").write_bytes(json_bytes(ledger))
    return base / "registry.json", base / "ledger.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    for name, mode, context in [("mixed", "mixed", "record"), ("all-zero", "all_zero", "record"),
                                 ("rare", "rare", "record"), ("batch-context", "mixed", "batch")]:
        registry, ledger = make_fixture(args.out_dir / name, mode, context)
        print(json.dumps({"fixture": name, "registry": str(registry), "ledger": str(ledger), "synthetic_only": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
