#!/usr/bin/env python3
"""One independently invented record through the untouched typing-fixed old CLI.

External true flags are deliberately only a legacy mathematical fixture, never
the new batch/source qualification path or a production verifier.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode = True
from vendor import stability_engine as old

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "constructed-controls/inputs/legacy-one-record"


def write(name, value):
    path = INPUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8") + b"\n"
    with path.open("xb") as stream:
        stream.write(data)
    return {"path": name, "sha256": old.digest(data)}


def main():
    INPUT.mkdir(parents=True, exist_ok=False)
    packet = {"unit_text": "旧单条数学回归的独立构造文字", "contexts": []}
    source = write("source.json", packet)
    manual = b"Independent synthetic single-record legacy math regression only."
    prompt = {"system_prefix": "", "system_suffix": "", "user_prefix": "判读要求\n", "user_suffix": "", "payload_template": {"system": "{{SYSTEM_CONTENT}}", "user": "{{USER_CONTENT}}", "settings": "{{REQUEST_SETTINGS}}"}}
    assets = {"manual": write("manual.txt", manual), "prompt": write("prompt.json", prompt)}
    for name in ("output_schema", "adapter", "technical_validator", "protocol"):
        assets[name] = write(name + ".txt", ("Legacy mathematical fixture only: " + name + "; no source or production qualification.").encode("utf-8"))
    common = {name: {"version": "legacy-regression-fixture-only", "artifact": ref} for name, ref in assets.items()}
    i = "INDEPENDENT-ONE"
    material = {"version": "synthetic-math-only", "source_packet": source, "source_semantic_sha256": old.object_sha(packet), "ctx_binding": {}, "ctx_binding_sha256": old.object_sha({})}
    sample = {"selection_mode": "non_probability", "weight_kind": "equal", "target_domain": "one invented regression record", "selection_rule": "invented before responses", "scope_limit": "old single-record mathematics only", "frame_seal_sha256": None, "all_target_units_positive_pi_declared": False, "assigned_records": [{"assignedID": i, "weight": 1, "inclusion_probability": None, "material_state": "complete", "material_pending_reason": None, "material": material}], "ordered_assignedIDs": [i], "batches": [{"batch_id": "SINGLE", "members": [i]}]}
    config = {"intended_model": "gpt-6.1-sol", "intended_reasoning_effort": "ultra", "provider_requested": None, "request_settings": {}, "provider_session_state": "unknown", "actual_model_identity_status": "not_proven_by_requested_identity_or_hash"}
    reg = {"contract_version": old.VERSION, "data_mode": "synthetic_control", "dimensions": list(old.DIMS), "registration": {"registry_id": "legacy-single-record-regression-only", "status": "frozen_before_response_read", "frozen_at": "2026-10-10T00:00:00+00:00", "verification": "declaration_not_independently_verified"}, "sample": sample, "common_artifacts": common, "common_configuration": config, "context_unit": "record", "context_independence_declaration": {"declared_independent": True, "verification": "not_independently_verified", "basis": "constructed metadata only"}, "allow_pending_material_for_valid_response": False, "retry_policy": {"max_actual_attempts": 3, "selection": "first_technically_valid_complete_response", "semantic_null_stops_retry": True, "same_exact_request_only": True}, "comparison_plan": {"pairs": [list(x) for x in old.PAIRS], "three_way": ["R1", "R2", "R3"], "perturbation_baseline": "R1"}, "stability_pass_threshold": None, "confidence_interval_gate": None, "conditions": {}}
    for run in old.RUNS:
        request = write(f"requests/{run}.json", old.request_bytes(reg, prompt, manual, packet, run))
        reg["conditions"][run] = {"run_id": run, "role": old.ROLES[run], "allowed_change": old.CHANGES[run], "common_configuration_sha256": old.object_sha(config), "common_artifacts_sha256": old.object_sha(common), "sample_plan_sha256": old.object_sha(sample), "context_unit": "record", "planned_contexts": {i: "legacy-" + run}, "requests": {i: {"exact_request": request, "source_semantic_sha256": material["source_semantic_sha256"], "ctx_binding_sha256": material["ctx_binding_sha256"]}}}
    reg["registry_content_sha256"] = old.object_sha(reg)
    registry = write("registry.json", reg)
    ledger = {"contract_version": old.VERSION, "data_mode": "synthetic_control", "registry_file_sha256": registry["sha256"], "firsts_selection_rule": "first_technically_valid_complete_response", "runs": {}}
    for run in old.RUNS:
        labels = dict(zip(old.DIMS, (0,0,0,0,0) if run in ("P", "R1", "W") else (1,0,0,0,0)))
        response = {"assignedID": i, "labels": labels, "reasons": {d: "synthetic mechanical regression" for d in old.DIMS}, "null_reasons": {}, "material_requests": {}, "evidence": {d: {} for d in old.DIMS}}
        raw = write(f"original-single-record/{run}.json", response)
        binding = reg["conditions"][run]["requests"][i]
        validator = write(f"checks/{run}.json", {"validator_artifact_sha256": common["technical_validator"]["artifact"]["sha256"], "exact_request_sha256": binding["exact_request"]["sha256"], "raw_response_sha256": raw["sha256"], "checks": dict.fromkeys(old.CHECKS, True), "failure_reasons": []})
        attempt = {"attempt_number": 1, "started_at": "2026-10-10T00:00:01+00:00", "ended_at": "2026-10-10T00:00:02+00:00", "executed_configuration": config, "request_binding": binding, "context": {"context_unit": "record", "planned_context_id": "legacy-" + run, "previous_output_exposure_declared": False, "verification": "not_independently_verified"}, "provider_receipt": {"status": "unavailable", "request_id": None, "returned_model": None, "configuration_evidence": None}, "transport_status": "ok", "transport_reason": None, "raw_response": raw, "validator_report": validator}
        first = {"run_id": run, "assignedID": i, "attempt_number": 1, "raw_response": raw, "parsed_response_sha256": old.object_sha(response)}
        ledger["runs"][run] = {"registered_condition_sha256": old.object_sha(reg["conditions"][run]), "records": [{"assignedID": i, "order_index": 1, "batch_id": "SINGLE", "attempts": [attempt], "not_called": None, "first": first}]}
    write("ledger.json", ledger)
    output = ROOT / "constructed-controls/results/legacy-one-record"
    command = [sys.executable, "-B", str(ROOT / "vendor/stability_engine.py"), "analyze", "--registry", str(INPUT / "registry.json"), "--ledger", str(INPUT / "ledger.json"), "--out-dir", str(output)]
    run = subprocess.run(command, capture_output=True, text=True)
    log = {"argv": command, "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr, "scope": "one invented old-format record; no production source assertion"}
    with (ROOT / "verification/legacy-single-record-cli.json").open("x", encoding="utf-8") as stream:
        json.dump(log, stream, ensure_ascii=False, indent=2)
    if run.returncode:
        print(run.stderr)
        return 1
    report = old.read_json_bytes((output / "report.json").read_bytes(), "old report")
    s = report["paired_comparisons"]["R1/R2"]["dimensions"]["S"]
    e = report["paired_comparisons"]["R1/R2"]["dimensions"]["E"]
    q = report["three_main_runs"]["q"]
    assertions = {"S_raw_n01_one": s["raw"]["cells"] == {"n00":0,"n01":1,"n10":0,"n11":0}, "S_Po_Pe_kappa_zero": all(s["raw"][k] == 0 for k in ("Po","Pe","kappa")), "E_degenerate_kappa_NA": e["raw"]["Pe"] == 1 and e["raw"]["kappa"] is None, "three_vector_agreement_zero_of_one": report["three_main_runs"]["five_dimension_vector"]["agreement_n"] == 0 and report["three_main_runs"]["five_dimension_vector"]["denominator_n"] == 1, "R1_q_zero_denom_NA": q["by_run"]["R1"]["unweighted_sum5T"] == 0 and all(x is None for x in q["by_run"]["R1"]["unweighted_q"].values()), "q_ranges_retain_NA_run": all(x["range"] is None and x["na_runs"] == ["R1"] for x in q["q_ranges"]["unweighted_q"].values())}
    with (ROOT / "verification/legacy-single-record-controls.json").open("x", encoding="utf-8") as stream:
        json.dump({"total": len(assertions), "passed": sum(assertions.values()), "checks": assertions, "no_source_qualification_claim": True}, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"legacy_math_checks": len(assertions), "passed": sum(assertions.values())}))
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
