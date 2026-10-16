#!/usr/bin/env python3
"""Two fully invented records; writes only a new constructed-controls directory."""
import copy
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import v17_adapter as a

ROOT = Path(__file__).resolve().parent
CASES = ["normal", "whole_batch_invalid", "earliest_valid_second", "legal_null_retry",
         "illegal_bool", "illegal_float", "early_compare", "three_failed", "four_attempts",
         "later_first_claim", "supplemental_bad_quote", "unqualified_pointer", "production_without_adoption", "unclosed_source_profile"]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else a.canonical(value) + b"\n"
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": str(path), "bytes": len(raw), "sha256": a.digest(raw)}


def ref(path, **extra):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": a.digest(raw), **extra}


def schema_of(value):
    if isinstance(value, dict):
        return {"type": "object", "properties": {k: schema_of(v) for k, v in value.items()}, "required": list(value), "additionalProperties": False}
    if isinstance(value, list):
        assert value
        return {"type": "array", "items": schema_of(value[0])}
    return {"type": "boolean" if type(value) is bool else "integer" if type(value) is int else "string" if isinstance(value, str) else "null"}


def quote_field(packet, pointer, role, location_pointer, context_pointer=None):
    value = a.validate_v17.pointer_value(packet, pointer)
    return {"pointer": pointer, "role": role, "text_sha256": a.digest(value.encode()), "location_pointer": location_pointer,
            "location_sha256": a.object_sha(a.validate_v17.pointer_value(packet, location_pointer)), "context_pointer": context_pointer,
            "context_sha256": a.object_sha(a.validate_v17.pointer_value(packet, context_pointer)) if context_pointer else None}


def build_case(base, case):
    directory = base / case; inputs = directory / "inputs"; inputs.mkdir(parents=True)
    manual = write(inputs / "manual.txt", "自造测试手册：五维值只检查格式；这不是政策材料。\n".encode())
    prompt = write(inputs / "main-prompt.txt", "判读要求\n这是自造设施控制；没有真实模型执行。\n".encode())
    h_prompt = write(inputs / "H-prompt.txt", "判读说明\n这是自造设施控制；没有真实模型执行。\n".encode())
    dispatch = write(inputs / "dispatch.txt", "读取本构造控制固定routing中的自身预留元数据并一次提交整批。\n".encode())
    dummy = write(inputs / "synthetic-contract-placeholder.json", {"synthetic_control_only": True, "no_production_adoption": True})
    asset = write(inputs / "invented-asset.txt", "自造图页文本；只有自造绑定，不是实际图像或工具阅读。\n".encode())
    packets, baseline_packets, source_records, sample_records = [], [], [], []
    for n in (1, 2):
        sid, oid, aid = f"RECODE25-{99000+n:05}", f"B-{99000+n:05}", f"INVENTED-{n}"
        bundle = {"source_record": {"unit_text": f"自造当前句{n}：甲乙连续文字。", "location": f"invented-document-{n}:line-1"},
                  "context": [{"id": f"CTX-INVENTED-{n}", "text": f"自造语境{n}：上下文连续文字。", "location": f"invented-document-{n}:line-2"}],
                  "asset_text": {"text": "自造图页：连续补充文字。", "link": {"asset_path": asset["path"], "asset_sha256": asset["sha256"], "page": 1, "text_pointer": "/source_bundle/asset_text/text"}}}
        packet = {"source_id": sid, "output_id": oid, "source_bundle_sha256": a.object_sha(bundle), "source_bundle": bundle}
        packets.append(packet)
        bound = write(inputs / f"packet-{n}.json", packet)
        baseline_packets.append({**bound, "source_id": sid, "output_id": oid})
        ctx = ["/source_bundle/context/0", "/source_bundle/asset_text/link"]
        fields = [quote_field(packet, "/source_bundle/source_record/unit_text", "current", "/source_bundle/source_record/location"),
                  quote_field(packet, "/source_bundle/context/0/text", "context", "/source_bundle/context/0/location", ctx[0]),
                  quote_field(packet, "/source_bundle/asset_text/text", "context", "/source_bundle/asset_text/link", ctx[1])]
        source_records.append({"assignedID": aid, "source_id": sid, "output_id": oid, "packet": bound,
            "source_content_sha256": a.object_sha(bundle), "ctx_pointers": ctx,
            "ctx_binding_sha256": a.object_sha([{"pointer": p, "value": a.validate_v17.pointer_value(packet, p)} for p in ctx]),
            "quote_fields": fields, "asset_quote_views": [{"asset": asset, "page": 1, "pointer": "/source_bundle/asset_text/text", "link_pointer": ctx[1], "link_sha256": a.object_sha(bundle["asset_text"]["link"])}]})
        sample_records.append({"assignedID": aid, "source_id": sid, "output_id": oid, "weight": 1, "inclusion_probability": None, "material_state": "complete", "material_pending_reason": None})
    source_schema = schema_of(packets[0])
    if case == "unclosed_source_profile":
        source_schema["properties"]["source_bundle"]["additionalProperties"] = True
    schema_ref = write(inputs / "common-closed-source.schema.json", source_schema)
    source_contract = write(inputs / "common-source-contract.json", {"contract_version": a.VERSION, "status": "common_source_only_profile_frozen_declared", "packet_schema": schema_ref, "records": source_records})
    bid = "batch-0001"
    routes, run_routes = [], {}
    for run in a.RUNS:
        batchdir = inputs / ("main" if run in {"R1", "R2", "R3"} else run) / bid
        run_routes[run] = []
        for n in range(1, 4):
            slot = batchdir / f"{run}-attempt-{n}"
            route = {"condition_id": run, "batch_id": bid, "attempt_number": n, "runtime_task_name": f"invented_{case}_{run}_{n}",
                     "expected_canonical_runtime_task_name": f"/root/invented_{case}_{run}_{n}", "output_directory": str(slot),
                     "structured_first_path": str(slot / "structured-first.utf8"), "report_path": str(slot / "report.txt"),
                     "seal_path": str(slot / "seal.json"), "reservation_only_not_actual_attempt": True}
            routes.append(route); run_routes[run].append(route)
    routing = write(inputs / "routing.json", {"artifact_type": "synthetic_native_route_control", "max_total_technical_attempts": 3, "max_technical_retries": 2, "routes": routes, "actual_actor_attempt_N": 0})
    assignments, assignment_refs = {}, {}
    for key in ("main", "W", "H"):
        batchdir = inputs / key / bid
        packet_refs = baseline_packets
        if key == "W":
            packet_refs = []
            for n, packet in enumerate(packets, 1):
                raw = json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2).encode() + b"\n"
                packet_refs.append({**write(inputs / f"W-packet-{n}.json", raw), "source_id": packet["source_id"], "output_id": packet["output_id"]})
        assignment = {k: dummy for k in a.INPUT_KEYS}
        assignment.update({"run_id": f"invented-prospective-{case}", "batch_id": bid, "expected_N": 2, "context_unit": "batch",
            "source_ids": [p["source_id"] for p in packets], "output_directory": str(batchdir), "manual": manual,
            "execution_prompt": h_prompt if key == "H" else prompt, "packet_schema": schema_ref,
            "strict_technical_validator": ref(ROOT / "vendor/validate_v17.py"), "packets": packet_refs,
            "source_asset_bindings": [{**asset, "source_ids": [p["source_id"] for p in packets]}],
            "attempt_output_routing": routing, "requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra",
            "scope": "two invented records; no real coding or tool reading", "max_total_technical_attempts": 3, "max_technical_retries": 2})
        assignment["output_schema"] = write(inputs / key / "output.schema.json", a.schema_for_assignment(assignment))
        assignment_refs[key] = write(batchdir / "assignment.json", assignment)
        assignments[key] = assignment
    plan = {"contract_version": a.VERSION, "data_mode": "prospective_registered_inputs" if case == "production_without_adoption" else "synthetic_control",
        "campaign_id": f"invented-prospective-{case}", "frozen_at": "2026-10-10T00:00:00Z", "production_adoption": None,
        "configuration": {"requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "provider_parameters": None,
                          "provider_session_state": "unknown", "actual_serving_model_independently_verified": False, "native_batch_context_contract": a.CONTEXT},
        "sample": {"selection_mode": "non_probability", "weight_kind": "equal", "target_domain": "invented fixtures only",
                   "selection_rule": "two records invented without real data", "scope_limit": "technical controls only", "frame_seal_sha256": None,
                   "all_target_units_positive_pi_declared": False, "records": sample_records, "batches": [{"batch_id": bid, "members": [r["assignedID"] for r in sample_records]}]},
        "source_contract": source_contract, "conditions": {}}
    for run in a.RUNS:
        key = "main" if run in {"R1", "R2", "R3"} else run
        plan["conditions"][run] = {"role": a.math_engine.ROLES[run], "allowed_change": a.math_engine.CHANGES[run], "batches": {bid: {"assignment": assignment_refs[key], "exact_request": dispatch, "routes": run_routes[run]}}}
    plan["plan_content_sha256"] = a.object_sha(plan)
    plan_ref = write(inputs / "plan.json", plan)
    ledger = {"contract_version": a.VERSION, "plan_file_sha256": plan_ref["sha256"], "runs": {}}
    for run in a.RUNS:
        key = "main" if run in {"R1", "R2", "R3"} else run
        assignment = assignments[key]; attempts = []; first = None
        counts = 0 if case == "early_compare" and run == "H" else 1
        if run == "R1" and case in {"earliest_valid_second", "legal_null_retry"}: counts = 2
        if run == "R1" and case == "three_failed": counts = 3
        if run == "R1" and case == "four_attempts": counts = 4
        for n in range(1, counts + 1):
            route = run_routes[run][n - 1] if n <= 3 else {"runtime_task_name": f"invented_{case}_{run}_{n}", "structured_first_path": str(inputs / key / bid / f"{run}-attempt-{n}" / "structured-first.utf8")}
            records = []
            for index, packetref in enumerate(assignment["packets"]):
                labels = [1, 0, 1, 0, 0] if index == 0 else [0, 1, 0, 1, None]
                if run == "R2" and index == 0: labels[0] = 0
                dimensions = {}
                for d, value in zip(a.DIMS, labels):
                    evidence = [] if value is None else [{"pointer": "/source_bundle/source_record/unit_text", "quote": "甲乙连续文字", "role": "current"}]
                    dimensions[d] = {"value": value, "reason": "自造格式控制；待定维度缺少自造前提。" if value is None else "自造格式控制，没有真实语义判断。", "evidence": evidence}
                if index == 0:
                    dimensions["S"]["evidence"].append({"asset_path": asset["path"], "asset_sha256": asset["sha256"], "page": 1, "quote": "连续补充文字", "role": "context"})
                records.append({"source_id": packetref["source_id"], "output_id": packetref["output_id"], "packet_sha256": packetref["sha256"], "dimensions": dimensions})
            files = []
            for bound in [assignment["manual"], assignment["execution_prompt"], *assignment["packets"]]:
                files.append({k: bound[k] for k in ("path", "bytes", "sha256")})
                files[-1].update({"actual_presented_ranges": [{"range_kind": "unicode_code_points", "range_basis": "0-based half-open constructed range", "start": 0, "end": len(Path(bound["path"]).read_text()), "presentation_event": "constructed-not-actual-tool-reading"}],
                                  "read_method": "synthetic declaration; no actual reading asserted", "source_ids": assignment["source_ids"], "not_truncated": True})
            files.append({**asset, "source_ids": assignment["source_ids"], "not_truncated": True, "read_method": "constructed fixture",
                          "actual_presented_ranges": [{"range_kind": "physical_pages", "range_basis": "invented page", "start": 1, "end": 1, "presentation_event": "constructed-not-actual-tool-reading"}]})
            submission = {"artifact_type": "invented native structured submission", "run_id": assignment["run_id"], "batch_id": bid,
                "requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "manual_binding": manual,
                "execution_prompt_binding": assignment["execution_prompt"], "read_manifest": {"context_unit": "batch", "files": files},
                "records": records, "scope": assignment["scope"], "context_unit": "batch"}
            invalid = run == "R1" and n == 1 and case in {"whole_batch_invalid", "earliest_valid_second", "illegal_bool", "illegal_float", "supplemental_bad_quote", "unqualified_pointer"}
            if invalid:
                if case in {"whole_batch_invalid", "earliest_valid_second"}: records[-1]["dimensions"]["S"]["evidence"][0]["quote"] = "不存在的自造引文"
                elif case == "illegal_bool": records[0]["dimensions"]["S"]["value"] = True
                elif case == "illegal_float": records[0]["dimensions"]["S"]["value"] = 1.0
                elif case == "supplemental_bad_quote": records[0]["dimensions"]["S"]["evidence"][-1]["quote"] = "不存在的图页引文"
                else:
                    records[-1]["dimensions"]["S"]["evidence"][0] = {"pointer": "/source_bundle/source_record/location", "quote": "invented-document", "role": "current"}
            raw = b'{"records": [' if run == "R1" and case in {"three_failed", "four_attempts"} else a.canonical(submission) + b"\n"
            original = write(Path(route["structured_first_path"]), raw)
            attempt = {"attempt_number": n, "started_at": f"2026-10-10T00:00:{n*2:02}Z", "ended_at": f"2026-10-10T00:00:{n*2+1:02}Z",
                "assignment_sha256": assignment_refs[key]["sha256"], "exact_request_sha256": dispatch["sha256"],
                "dispatch": {"runtime_task_name": route["runtime_task_name"], "context_id": route["runtime_task_name"], "requested_model": "gpt-6.1-sol",
                    "requested_reasoning_effort": "ultra", "fork_turns": "none", "previous_output_exposure_declared": False,
                    "actual_tool_request": None, "actual_tool_creation_receipt": None, "evidence_kind": "constructed_declaration"},
                "transport_status": "ok", "failure_reason": None, "original": original, "failure_files": []}
            attempts.append(attempt)
            if not invalid and not (run == "R1" and case in {"three_failed", "four_attempts"}) and first is None:
                first = {"attempt_number": n, "original": original, "parsed_batch_sha256": a.object_sha(submission)}
        if case == "later_first_claim" and run == "R1": first = {**first, "attempt_number": 2}
        terminal = bool(first) or counts == 3
        row = {"batch_id": bid, "attempts": attempts, "not_called": None if counts else {"state": "not_called", "reason": "H remains scheduled", "terminal_without_attempt": False}, "first": first}
        stream = {"batches": [row]}
        stream["seal"] = {"status": "condition_terminal_sealed" if terminal else "snapshot_not_terminal", "content_sha256": a.object_sha(stream),
                           "sealed_at": "2026-10-10T00:01:00Z", "verification": "declaration_not_independently_verified"}
        ledger["runs"][run] = stream
    write(inputs / "ledger.json", ledger)
    return directory


def file_hashes(directory):
    return {str(p.relative_to(directory)): a.digest(p.read_bytes()) for p in sorted(directory.rglob("*")) if p.is_file()}


def main():
    base = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "constructed-controls"); base.mkdir()
    expectations = {"normal": "valid, fixed records pointers, all5 sealed; compare succeeds", "whole_batch_invalid": "both R1 records technical failure; no extracted labels; snapshot locked",
        "earliest_valid_second": "R1 selects attempt2; attempt1 retained", "legal_null_retry": "reject attempt after legal-null valid batch",
        "illegal_bool": "whole R1 invalid", "illegal_float": "whole R1 invalid", "early_compare": "snapshot allowed; requested comparison rejected",
        "three_failed": "terminal after3 actual whole-batch constructed attempts, both records failure", "four_attempts": "reject max3",
        "later_first_claim": "reject non-earliest claimed first", "supplemental_bad_quote": "whole R1 invalid", "unqualified_pointer": "whole R1 invalid although v17 core exact substring passes",
        "production_without_adoption": "reject before source/output read", "unclosed_source_profile": "reject permissive source profile"}
    write(base / "expected-before-execution.json", {"data_origin": "two wholly invented records; not independent real data", "expectations": expectations})
    directories = {case: build_case(base, case) for case in CASES}
    results = []
    reject_cases = {"legal_null_retry", "four_attempts", "later_first_claim", "production_without_adoption", "unclosed_source_profile"}
    invalid_cases = {"whole_batch_invalid", "illegal_bool", "illegal_float", "supplemental_bad_quote", "unqualified_pointer"}
    for case, directory in directories.items():
        inputs = directory / "inputs"; before = file_hashes(inputs); out = directory / "actual-result.json"
        compare = case not in invalid_cases and case != "early_compare"
        cmd = [sys.executable, "-B", str(ROOT / "v17_adapter.py"), "--plan", str(inputs / "plan.json"), "--ledger", str(inputs / "ledger.json"), "--out", str(out)] + (["--compare"] if compare else [])
        done = subprocess.run(cmd, capture_output=True, text=True)
        write(directory / "actual-cli-record.json", {"command": cmd, "exit_code": done.returncode, "stdout": done.stdout, "stderr": done.stderr})
        assert done.returncode == (2 if case in reject_cases else 0), (case, done.stderr)
        if case not in reject_cases:
            result = json.loads(out.read_text()); states = result["per_record_states"]["R1"]
            if case in invalid_cases or case == "three_failed":
                assert all(r["state"] == "technical_failure" and r["labels"] is None and r["first"] is None for r in states.values())
                assert all(c["record_checks"] == [] for c in result["audit"]["R1"][0]["attempts"])
            if case in invalid_cases:
                assert result["paired_comparisons"] == {} and result["three_main_runs"] is None
                assert all(r["remaining_retry_slots_if_unresolved"] == 2 for r in states.values())
            if case == "normal" or case == "earliest_valid_second":
                origins = list(result["origins"]["R1"].values())
                assert [r["extraction_pointer"] for r in origins] == ["/records/0", "/records/1"]
                assert len({r["raw_response"]["path"] for r in origins}) == 1 and all(r["derived_record_is_original_response"] is False for r in origins)
                assert all(r["attempt_number"] == (2 if case == "earliest_valid_second" else 1) for r in origins)
                assert states["INVENTED-2"]["state"] == "valid_semantic_null"
                assert result["comparison_gate"]["unlocked"] and len(result["paired_comparisons"]) == 5
                if case == "normal":
                    math = result["paired_comparisons"]["R1/R2"]["dimensions"]["S"]["raw"]
                    assert math["Po"] == .5 and math["kappa"] == 0
            if case == "early_compare":
                assert result["paired_comparisons"] == {} and result["three_main_runs"] is None
                early = subprocess.run(cmd + ["--compare", "--out", str(directory / "forbidden-early-comparison.json")], capture_output=True, text=True)
                write(directory / "actual-early-compare-rejection.json", {"exit_code": early.returncode, "stdout": early.stdout, "stderr": early.stderr})
                assert early.returncode == 2 and not (directory / "forbidden-early-comparison.json").exists()
        if case == "production_without_adoption":
            reader = a.BoundReader()
            try: a.validate_plan(json.loads((inputs / "plan.json").read_text()), reader)
            except a.ContractError: pass
            else: raise AssertionError("missing adoption accepted")
            assert reader.seen == {}, "must refuse before opening source or original submissions"
        after = file_hashes(inputs)
        assert before == after, "adapter changed original inputs"
        results.append({"case": case, "passed": True, "exit_code": done.returncode, "all_input_files_original_bytes_unchanged": True,
                        "input_file_N": len(before), "before_sha256": a.object_sha(before), "after_sha256": a.object_sha(after), "actual_record": str(directory / "actual-cli-record.json")})
    write(base / "actual-controls-report.json", {"constructed_only": True, "real_model_actor_calls": 0, "real_source_text_read": False,
          "passed_case_N": len(results), "case_N": len(CASES), "controls": results, "predeclared_expectations": ref(base / "expected-before-execution.json"),
          "executed_code_bindings": [ref(ROOT / p) for p in ["v17_adapter.py", "build_controls.py", "statistics_bridge.py", "vendor/stability_engine.py", "vendor/validate_v17.py", "vendor/native-v17-output.schema.json"]]})
    print(json.dumps({"passed_case_N": len(results), "case_N": len(CASES), "real_actor_calls": 0}))


if __name__ == "__main__": main()
