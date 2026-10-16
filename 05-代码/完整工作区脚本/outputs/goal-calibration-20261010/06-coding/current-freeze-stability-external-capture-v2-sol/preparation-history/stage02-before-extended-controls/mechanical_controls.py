"""Purely constructed transport failures and local lock controls; no model."""
import argparse
import copy
import json
import multiprocessing
import os
from pathlib import Path
import time
from unittest.mock import patch
import jsonschema
from transport_common import HERE, BASE, REQUIRED_KEYS, PYTHON, binding, put, save, load, now, capacity, presentation_payload, check_prior, artifact_validate, pid_dead
from receiver import verify_capture
from read_allowed import present
import runner

THREAD = "11111111-1111-4111-8111-111111111111"

def fixture(directory, mutate=None, event_mutate=None, completion_mutate=None):
    directory.mkdir(parents=True)
    toy = put(directory / "packet.json", '{"unit_text":"构造条款：仅作运输格式演练。"}\n'.encode())
    packet = {**toy, "source_id": "TOY-ONLY-001", "output_id": "TOY-OUTPUT-001"}
    inputs = {}
    for key in REQUIRED_KEYS:
        inputs[key] = put(directory / (key + ".txt"), ("构造输入：" + key + "。\n").encode())
    inputs["strict_technical_validator"] = binding(HERE / "capture-validator.py")
    inputs["transport_helper_binding"] = binding(HERE / "read_allowed.py")
    inputs["transport_common_binding"] = binding(HERE / "transport_common.py")
    rawschema = load(BASE / "06-coding/current-freeze-stability800-v1-root/diagnostic-batch-0001/output.schema.json")
    schema = copy.deepcopy(rawschema)
    scope = "CONSTRUCTED_CONTROL_NOT_REAL_POLICY_CODING"
    for k, v in {"run_id": "TOY-NO-MODEL", "batch_id": "TOY-BATCH", "manual_binding": inputs["manual"], "execution_prompt_binding": inputs["execution_prompt"], "scope": scope}.items():
        schema["properties"][k] = {"const": v}
    record_schema = copy.deepcopy(schema["properties"]["records"]["prefixItems"][0])
    for k, v in {"source_id": packet["source_id"], "output_id": packet["output_id"], "packet_sha256": packet["sha256"]}.items():
        record_schema["properties"][k] = {"const": v}
    schema["properties"]["records"] = {"type": "array", "minItems": 1, "maxItems": 1, "prefixItems": [record_schema], "items": False}
    inputs["output_schema"] = save(directory / "output.schema.json", schema)
    assignment = {**inputs, "run_id": "TOY-NO-MODEL", "batch_id": "TOY-BATCH", "scope": scope, "context_unit": "batch", "requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "output_directory": str(directory.resolve()), "expected_N": 1, "source_ids": [packet["source_id"]], "packets": [packet], "source_asset_bindings": []}
    ab = save(directory / "assignment.json", assignment)
    declaration = []
    events = [{"type": "thread.started", "thread_id": THREAD}, {"type": "turn.started"}]
    for n, b in enumerate([inputs["manual"], inputs["execution_prompt"], packet]):
        text = Path(b["path"]).read_bytes().decode()
        payload = presentation_payload({k: b[k] for k in ("path", "bytes", "sha256")}, text, 0, len(text))
        token = json.loads(payload.split("\n", 1)[0].removeprefix("PRESENTATION_BEGIN "))["presentation_event"]
        declaration.append({**{k: b[k] for k in ("path", "bytes", "sha256")}, "read_method": "constructed_helper_payload_in_synthetic_event", "not_truncated": True, "source_ids": [packet["source_id"]], "actual_presented_ranges": [{"range_kind": "unicode_code_points", "range_basis": "Unicode code points half-open", "start": 0, "end": len(text), "presentation_event": token}]})
        events.append({"type": "item.completed", "item": {"id": f"synthetic-toy-command-{n}", "type": "command_execution", "exit_code": 0, "status": "completed", "aggregated_output": payload}, "fixture_only": True})
    first = {"artifact_type": "CONSTRUCTED_WHOLE_BATCH_CONTROL", "run_id": assignment["run_id"], "batch_id": assignment["batch_id"], "scope": scope, "context_unit": "batch", "requested_model": assignment["requested_model"], "requested_reasoning_effort": "ultra", "manual_binding": inputs["manual"], "execution_prompt_binding": inputs["execution_prompt"], "read_manifest": {"context_unit": "batch", "files": declaration}, "records": [{"source_id": packet["source_id"], "output_id": packet["output_id"], "packet_sha256": packet["sha256"], "dimensions": {k: {"value": 0, "reason": "构造格式控制，未执行语义判读。", "evidence": [{"pointer": "/unit_text", "quote": "构造条款", "role": "current"}]} for k in ("S", "E", "Ec", "I", "F")}}]}
    if mutate:
        mutate(first)
    raw = (json.dumps(first, ensure_ascii=False, indent=2) + "\n").encode()
    fp = directory / "first.json"
    put(fp, raw)
    events.append({"type": "item.completed", "item": {"id": "synthetic-toy-message", "type": "agent_message", "text": raw.decode().removesuffix("\n")}, "fixture_only": True})
    events.append({"type": "turn.completed", "usage": {}, "fixture_only": True})
    if event_mutate:
        event_mutate(events)
    ep = directory / "synthetic-events.jsonl"
    put(ep, b"".join((json.dumps(e, ensure_ascii=False) + "\n").encode() for e in events))
    stdin = put(directory / "stdin.txt", "判读要求\n构造控制，不调用模型。\n".encode())
    item = {"condition": "R1", "batch_number": 1, "attempt_number": 1, "assignment": ab, "fixed_request": stdin, "working_directory": str(directory.resolve())}
    start = {"assignment": ab, "stdin": stdin, "working_directory": item["working_directory"], "route_appended_to_model_prompt": False, "resumed_or_inherited_conversation": False, "fixture_only": True}
    completion = {"actual_process_terminal": True, "returncode": 0, "timed_out": False, "provenance": "ROOT_subprocess_Popen_wait_real_events_capture", "condition": "R1", "batch_number": 1, "attempt_number": 1, "actual_cli_thread_ids": [THREAD], "fixture_only": True, "actual_model_calls": 0, "synthetic_event_claim": True}
    if completion_mutate:
        completion_mutate(completion)
    return ab, fp, ep, completion, start, item, binding(HERE / "capture-validator.py")

def local_worker(directory, gate, active, peak):
    gate.wait()
    with capacity(directory, timeout=5):
        with active.get_lock():
            active.value += 1
            peak.value = max(peak.value, active.value)
        time.sleep(.2)
        with active.get_lock():
            active.value -= 1

def run_controls(out):
    out = Path(out).resolve()
    out.mkdir(exist_ok=False)
    results = []
    def case(name, fn, reject=False):
        try:
            value = fn()
        except Exception as e:
            results.append({"name": name, "pass": reject and not isinstance(e, (TypeError, KeyError, FileNotFoundError)), "expected_rejection": reject, "error": {"type": type(e).__name__, "message": str(e)}})
        else:
            results.append({"name": name, "pass": not reject, "expected_rejection": reject, "result": value})
    def verify(name, **kwargs):
        args = fixture(out / name, **kwargs)
        return verify_capture(args[0]["path"], *args[1:], fixture=True)
    case("valid_binary_exact_capture", lambda: verify("valid_binary"))
    def null(f):
        f["records"][0]["dimensions"]["F"] = {"value": None, "reason": "构造必要材料缺失，合法待定；不触发重试。", "evidence": []}
    case("legal_null_is_technically_valid", lambda: verify("legal_null", mutate=null))
    case("fake_text_presentation_event", lambda: verify("fake_event", mutate=lambda f: f["read_manifest"]["files"][0]["actual_presented_ranges"][0].update(presentation_event="FAKE")), True)
    case("truncated_payload_cannot_prove_read", lambda: verify("truncated", event_mutate=lambda e: e[2]["item"].update(aggregated_output=e[2]["item"]["aggregated_output"].split("PRESENTATION_END")[0])), True)
    case("missing_manual_coverage", lambda: verify("missing_read", mutate=lambda f: f["read_manifest"]["files"].pop(0)), True)
    case("empty_actual_input_declarations", lambda: verify("empty_reads", mutate=lambda f: f["read_manifest"].update(files=[])), True)
    case("quote_not_exact", lambda: verify("wrong_quote", mutate=lambda f: f["records"][0]["dimensions"]["I"]["evidence"][0].update(quote="并不存在的词句")), True)
    case("bool_not_binary_integer", lambda: verify("bool_value", mutate=lambda f: f["records"][0]["dimensions"]["S"].update(value=True)), True)
    case("float_not_binary_integer", lambda: verify("float_value", mutate=lambda f: f["records"][0]["dimensions"]["S"].update(value=0.0)), True)
    case("wrong_whole_batch_member", lambda: verify("wrong_member", mutate=lambda f: f["records"][0].update(source_id="OTHER-TOY")), True)
    case("extra_record_no_splicing", lambda: verify("extra_record", mutate=lambda f: f["records"].append(copy.deepcopy(f["records"][0]))), True)
    case("multiple_structured_firsts_no_best_pick", lambda: verify("double_first", event_mutate=lambda e: e.insert(-1, copy.deepcopy(e[-2]))), True)
    case("thread_missing", lambda: verify("thread_missing", event_mutate=lambda e: e.pop(0)), True)
    case("turn_not_complete", lambda: verify("no_turn_end", event_mutate=lambda e: e.pop()), True)
    case("nonzero_transport_returncode", lambda: verify("nonzero", completion_mutate=lambda c: c.update(returncode=400)), True)
    case("uncertain_process_cannot_retry", lambda: verify("uncertain", completion_mutate=lambda c: c.update(actual_process_terminal=False)), True)
    case("timeout_not_clean_terminal", lambda: verify("timeout", completion_mutate=lambda c: c.update(timed_out=True)), True)
    args = fixture(out / "fixture_guard")
    case("synthetic_fixture_not_accepted_as_actual", lambda: verify_capture(args[0]["path"], *args[1:]), True)
    case("helper_arbitrary_path_rejected", lambda: present(args[0]["path"], __file__, 0, 1), True)
    case("helper_oversized_segment_rejected", lambda: present(args[0]["path"], args[0]["path"], 0, 2501), True)
    selection = out / "already_selected"
    selection.mkdir()
    save(selection / "root-selection.json", {"state": "selected", "legal_null_is_terminal_valid": True, "fixture_only": True})
    slot = selection / "attempt-0002"
    slot.mkdir()
    case("selected_null_prevents_second_dispatch", lambda: check_prior(selection, 2, slot), True)
    case("own_live_pid_is_not_terminal", lambda: pid_dead(os.getpid()) is False)
    def noGO():
        with patch.object(runner, "campaign", return_value=(out, {})), patch.object(runner.subprocess, "Popen") as call:
            try:
                runner.run_attempt(out, "R1", 1, 1, out / "ABSENT-GO.json")
            except FileNotFoundError:
                return {"Popen_calls": call.call_count, "blocked_before_dispatch": call.call_count == 0}
            raise ValueError("Absent GO did not block")
    case("missing_GO_no_process", noGO)
    def locks():
        ctx = multiprocessing.get_context("spawn")
        gate, active, peak = ctx.Event(), ctx.Value("i", 0), ctx.Value("i", 0)
        workers = [ctx.Process(target=local_worker, args=(str(out / "local-capacity"), gate, active, peak)) for _ in range(4)]
        for p in workers:
            p.start()
        gate.set()
        for p in workers:
            p.join(10)
        if any(p.exitcode != 0 for p in workers) or peak.value != 3 or active.value != 0:
            raise ValueError("Actual local capacity protection failed")
        return {"local_nonmodel_worker_N": 4, "actual_max_active_protected_children": peak.value, "model_process_N": 0, "all_children_terminal": True}
    case("four_local_workers_at_most_three_active", locks)
    badseal = {"artifact_type": "ROOT_capture_transport_seal", "issuer": "ROOT_transport", "run_id": "TOY", "batch_id": "TOY", "template_only": False, "actual_completion_claimed": True, "first_binding": args[0], "captured_message_binding": args[0], "report_binding": args[0], "completion": args[0], "actual_input_bindings": [], "actor_created_seal_claimed": False}
    case("empty_ROOT_seal_actual_binding_rejected", lambda: artifact_validate("ROOT_transport_seal", badseal), True)
    save(out / "results.json", {"at_utc": now(), "fixture_only": True, "model_calls": 0, "classifier_calls": 0, "policy_semantics_classified": False, "all_pass": all(r["pass"] for r in results), "control_N": len(results), "results": results})
    return {"output": binding(out / "results.json"), "all_pass": all(r["pass"] for r in results), "control_N": len(results), "model_calls": 0}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    print(json.dumps(run_controls(p.parse_args().output), ensure_ascii=False))
