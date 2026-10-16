"""ROOT mechanical reception of an unchanged captured whole-batch JSON."""
import argparse
import json
from pathlib import Path
import uuid
from transport_common import campaign, route, allowed_inputs, binding, check, load, strict, save, save_same, put, module, now, presentation_payload, exclusive, artifact_validate

def events_from(path):
    rows = []
    for line in Path(path).read_bytes().splitlines():
        if line.strip():
            obj = strict(line.decode("utf-8"))
            if not isinstance(obj, dict):
                raise ValueError("Nonobject raw CLI event")
            rows.append(obj)
    return rows

def capture_event(rows, raw):
    threads = [x.get("thread_id") for x in rows if x.get("type") == "thread.started"]
    if len(threads) != 1 or not threads[0] or str(uuid.UUID(threads[0])) != threads[0]:
        raise ValueError("Exactly one genuine-format fresh CLI thread required")
    if sum(x.get("type") == "turn.started" for x in rows) != 1 or sum(x.get("type") == "turn.completed" for x in rows) != 1:
        raise ValueError("Exactly one complete CLI turn required")
    if any(x.get("type") in ("error", "turn.failed") for x in rows):
        raise ValueError("CLI failed event retained; not a complete response")
    candidates, matches = [], []
    for n, row in enumerate(rows):
        item = row.get("item", {})
        if row.get("type") != "item.completed" or item.get("type") != "agent_message":
            continue
        text = item.get("text", "")
        if raw in (text.encode("utf-8"), text.encode("utf-8") + b"\n"):
            matches.append(n)
        try:
            parsed = strict(text)
        except (ValueError, TypeError):
            continue
        if isinstance(parsed, dict) and ("records" in parsed or "read_manifest" in parsed):
            candidates.append(n)
    if len(candidates) != 1 or matches != candidates:
        raise ValueError("Capture is not the sole original structured first message; no later answer selection")
    first_n = candidates[0]
    if not any(r.get("type") == "turn.completed" for r in rows[first_n + 1:]):
        raise ValueError("First message not followed by real terminal turn")
    return threads[0], first_n

def verify_capture(assignment_path, first_path, events_path, completion, start, item, validator_binding, fixture=False):
    a, allowed = allowed_inputs(assignment_path)
    if completion.get("actual_process_terminal") is not True or completion.get("returncode") != 0 or completion.get("timed_out") is not False:
        raise ValueError("Actual CLI process not cleanly terminal")
    if completion.get("provenance") != "ROOT_subprocess_Popen_wait_real_events_capture":
        raise ValueError("Unrecognized completion provenance")
    if completion.get("fixture_only") is True and not fixture:
        raise ValueError("Constructed fixture cannot enter an actual diagnostic reception")
    if (completion.get("condition"), completion.get("batch_number"), completion.get("attempt_number")) != (item["condition"], item["batch_number"], item["attempt_number"]):
        raise ValueError("External process route mismatch")
    if start["assignment"] != item["assignment"] or start["stdin"] != item["fixed_request"] or start["working_directory"] != item["working_directory"]:
        raise ValueError("Actual stdin/input/CWD differs from frozen external route")
    if start.get("resumed_or_inherited_conversation") is not False or start.get("route_appended_to_model_prompt") is not False:
        raise ValueError("History/routing injected into actual request")
    for b in allowed.values():
        check(b)
    check(start["stdin"])
    rows = events_from(events_path)
    raw = Path(first_path).read_bytes()
    thread, first_n = capture_event(rows, raw)
    if completion.get("actual_cli_thread_ids") != [thread]:
        raise ValueError("Process/event thread binding mismatch")
    validator = module(validator_binding, "unchanged_production_validator_capture")
    result = validator.verify(assignment_path, first_path)
    first = load(first_path)
    declarations = first["read_manifest"]["files"]
    if not declarations:
        raise ValueError("Real input/read declaration must be nonempty")
    actual_inputs = {}
    event_proofs = []
    required = {a["manual"]["path"], a["execution_prompt"]["path"], *(b["path"] for b in a["packets"])}
    source_by_packet = {b["path"]: b["source_id"] for b in a["packets"]}
    ids_by_read = {}
    for entry in declarations:
        path = entry["path"]
        b = allowed.get(path)
        if not b or any(entry[k] != b[k] for k in ("path", "bytes", "sha256")):
            raise ValueError("Input declaration outside exact assignment allowlist")
        actual_inputs[path] = b
        ids_by_read.setdefault(path, set()).update(entry["source_ids"])
        text = None
        for interval in entry["actual_presented_ranges"]:
            kind = interval["range_kind"]
            matches = []
            if kind == "unicode_code_points":
                if text is None:
                    text = Path(path).read_bytes().decode("utf-8")
                left, right = interval["start"], interval["end"]
                if not 0 <= left < right <= len(text) or right - left > 2500:
                    raise ValueError("Oversized/outside actual helper text interval")
                payload = presentation_payload(b, text, left, right)
                if interval["presentation_event"] not in payload.split("\n", 1)[0]:
                    raise ValueError("Declared presentation token does not bind this input range")
                for n, row in enumerate(rows[:first_n]):
                    tool = row.get("item", {})
                    if row.get("type") == "item.completed" and tool.get("type") == "command_execution" and tool.get("exit_code") == 0 and payload in tool.get("aggregated_output", ""):
                        matches.append({"raw_event_index": n, "actual_item_id": tool.get("id"), "payload_exact": True})
                if not matches:
                    raise ValueError("Complete declared input slice absent from pre-first real command event")
            else:
                if path in required:
                    raise ValueError("Mandatory UTF8 text must use actual bounded helper codepoint presentation")
                # Physical-page/image declarations retain original contract:
                # only event identity is observable here, not pixel/transcript truth.
                for n, row in enumerate(rows[:first_n]):
                    tool = row.get("item", {})
                    if row.get("type") == "item.completed" and interval["presentation_event"] == tool.get("id"):
                        matches.append({"raw_event_index": n, "actual_item_id": tool.get("id"), "pixel_or_transcript_verified": False})
                if not matches:
                    raise ValueError("Supplemental nontext presentation lacks a real pre-first event identity")
            event_proofs.append({"input": b, "declared_range": interval, "actual_raw_event_matches": matches})
    for path in (a["manual"]["path"], a["execution_prompt"]["path"]):
        if ids_by_read.get(path) != set(a["source_ids"]):
            raise ValueError("Common actual read not bound to every applicable batch member")
    for path, source_id in source_by_packet.items():
        if source_id not in ids_by_read.get(path, set()):
            raise ValueError("Actual packet read not bound to its own record")
    return {"production_validation": result, "actual_input_bindings": list(actual_inputs.values()), "raw_event_presentation_proofs": event_proofs, "actual_thread_id": thread, "single_structured_first_event_index": first_n, "actual_model_context_delivery_or_semantic_read_verified": False, "provider_wire_verified": False, "serving_model_verified": False}

def finish_selection(d, item, receipt, receipt_binding):
    first = Path(receipt["first"]["path"])
    directory = Path(item["selection_directory"])
    check(receipt["first"])
    mirror_path = directory / "first.json"
    if mirror_path.exists():
        if mirror_path.read_bytes() != first.read_bytes():
            raise ValueError("Existing mirror differs from original capture; no replacement")
        mirror = binding(mirror_path)
    else:
        mirror = put(mirror_path, first.read_bytes())
    selection = save_same(directory / "root-selection.json", {"state": "selected", "issuer": "ROOT_transport", "run_id": d["run_id"], "condition": item["condition"], "batch_number": item["batch_number"], "selected_attempt_number": item["attempt_number"], "original_whole_batch_first": binding(first), "canonical_whole_byte_mirror": mirror, "technical_reception": receipt_binding, "ROOT_transport_seal": receipt["transport_seal"], "first_origin": "ROOT_exact_CLI_final_message_capture", "actor_created_seal_claimed": False, "cross_attempt_record_combination": False, "label_based_selection": False, "legal_null_is_terminal_valid": True})
    return {"state": "selected", "selection": selection, "record_N": receipt["validation"]["record_N"]}

def validate_selection(d, condition, batch, selection):
    item = route(d, condition, batch, selection["selected_attempt_number"])
    if any(selection.get(k) != v for k, v in {"state": "selected", "issuer": "ROOT_transport", "run_id": d["run_id"], "condition": condition, "batch_number": batch, "actor_created_seal_claimed": False, "cross_attempt_record_combination": False, "label_based_selection": False, "legal_null_is_terminal_valid": True}.items()):
        raise ValueError("Selection identity/policy mismatch")
    for k in ("original_whole_batch_first", "canonical_whole_byte_mirror", "technical_reception", "ROOT_transport_seal"):
        check(selection[k])
    receipt = load(selection["technical_reception"]["path"])
    if receipt["state"] != "technical_valid_whole_batch" or receipt["attempt_number"] != item["attempt_number"] or receipt["first"] != selection["original_whole_batch_first"]:
        raise ValueError("Selection lacks its original valid reception")
    seal = load(selection["ROOT_transport_seal"]["path"])
    artifact_validate("ROOT_transport_seal", seal)
    if seal["run_id"] != d["run_id"] or seal["batch_id"] != item["batch_id"] or seal["first_binding"] != receipt["first"]:
        raise ValueError("ROOT seal identity/first mismatch")
    for k in ("first_binding", "captured_message_binding", "report_binding", "completion"):
        check(seal[k])
    _, allowed = allowed_inputs(item["assignment"]["path"])
    for b in seal["actual_input_bindings"]:
        if allowed.get(b["path"]) != b:
            raise ValueError("ROOT seal actual inputs outside assignment")
        check(b)
    if selection["original_whole_batch_first"]["sha256"] != selection["canonical_whole_byte_mirror"]["sha256"]:
        raise ValueError("Selected mirror differs from original bytes")
    for n in range(1, item["attempt_number"]):
        earlier = load(Path(item["selection_directory"]) / f"root-attempt-reception-{n:04d}.json")
        if earlier["state"] != "technical_invalid_whole_batch":
            raise ValueError("Bypassed earlier valid/uncertain first")
        check(earlier["completion"])
    return item

def receive_locked(run, d, item):
    slot = Path(item["output_directory"])
    directory = Path(item["selection_directory"])
    receipt_path = directory / f"root-attempt-reception-{item['attempt_number']:04d}.json"
    if (directory / "root-selection.json").exists():
        validate_selection(d, item["condition"], item["batch_number"], load(directory / "root-selection.json"))
        raise ValueError("Immutable valid selection already exists; no repeat")
    if receipt_path.exists():
        existing = load(receipt_path)
        if existing["state"] != "technical_valid_whole_batch":
            raise ValueError("Immutable invalid reception already exists")
        check(existing["completion"])
        check(existing["transport_report"])
        check(existing["transport_seal"])
        return finish_selection(d, item, existing, binding(receipt_path))
    for n in range(1, item["attempt_number"]):
        earlier = load(directory / f"root-attempt-reception-{n:04d}.json")
        if earlier["state"] != "technical_invalid_whole_batch":
            raise ValueError("Earlier valid/uncertain attempt cannot be bypassed")
        check(earlier["completion"])
    cp = slot / "ROOT-process-completion.json"
    completion = load(cp)
    artifact_validate("ROOT_completion", completion)
    if completion.get("actual_process_terminal") is not True:
        raise ValueError("Live/uncertain actual process cannot be technically retried")
    for k in ("start", "raw_cli_events", "stderr"):
        check(completion[k])
    start = load(completion["start"]["path"])
    check(start["GO"])
    receipt = {"artifact_type": "ROOT_external_capture_whole_batch_reception", "issuer": "ROOT_transport", "at_utc": now(), "run_id": d["run_id"], "condition": item["condition"], "batch_id": item["batch_id"], "batch_number": item["batch_number"], "attempt_number": item["attempt_number"], "completion": binding(cp), "assignment": item["assignment"], "first_origin": "ROOT_exact_CLI_final_message_capture", "actor_created_seal_claimed": False, "semantic_correctness_checked": False, "reference_or_accuracy_checked": False}
    first = slot / "first.json"
    try:
        capture = slot / "ROOT-cli-final-message.txt"
        check(completion["captured_final_message"])
        if completion["captured_final_message"] != binding(capture):
            raise ValueError("Wrong original capture path")
        if first.exists():
            if first.read_bytes() != capture.read_bytes():
                raise ValueError("Existing first differs from original capture")
        else:
            put(first, capture.read_bytes())
        proof = verify_capture(item["assignment"]["path"], first, completion["raw_cli_events"]["path"], completion, start, item, d["validator"])
    except Exception as error:
        receipt.update(state="technical_invalid_whole_batch", error={"type": type(error).__name__, "message": str(error)}, retained_actual_files=[binding(p) for p in sorted(slot.iterdir()) if p.is_file()])
        save(receipt_path, receipt)
        return {"state": receipt["state"], "attempt_number": item["attempt_number"], "exhausted": item["attempt_number"] == 3}
    # ROOT artifact-write/runtime failures are outside candidate validation:
    # they must not convert a valid first into a new model attempt.
    report = save_same(slot / "ROOT-transport-report.json", {"issuer": "ROOT_transport", "run_id": d["run_id"], "batch_id": item["batch_id"], "first_origin": receipt["first_origin"], "actor_created_files_claimed": False, "technical_proof": proof, "completion": binding(cp)})
    seal = save_same(slot / "ROOT-transport-seal.json", {"artifact_type": "ROOT_capture_transport_seal", "issuer": "ROOT_transport", "run_id": d["run_id"], "batch_id": item["batch_id"], "template_only": False, "actual_completion_claimed": True, "actual_completion_meaning": "actual clean CLI turn/process and one complete captured structured first, not actor-created-file completion", "first_binding": binding(first), "captured_message_binding": binding(capture), "report_binding": report, "actual_input_bindings": proof["actual_input_bindings"], "completion": binding(cp), "actor_created_seal_claimed": False, "serving_model_verified": False})
    receipt.update(state="technical_valid_whole_batch", validation=proof["production_validation"], technical_proof=proof, first=binding(first), transport_report=report, transport_seal=seal)
    rb = save(receipt_path, receipt)
    return finish_selection(d, item, receipt, rb)

def receive(run, condition, batch, attempt):
    run, d = campaign(run)
    item = route(d, condition, batch, attempt)
    with exclusive(Path(item["selection_directory"]) / "ROOT-reception.lock"):
        return receive_locked(run, d, item)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    p.add_argument("--condition", required=True)
    p.add_argument("--batch", type=int, required=True)
    p.add_argument("--attempt", type=int, required=True, choices=(1, 2, 3))
    a = p.parse_args()
    print(json.dumps(receive(a.run, a.condition, a.batch, a.attempt), ensure_ascii=False))
