"""Actual future CLI entrypoint, gated by ROOT GO; never executes on import."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from transport_common import campaign, route, check, binding, load, save, put, now, validate_GO, check_prior, capacity, exclusive
from receiver import receive_locked, events_from

def command(d, item):
    capture = Path(item["output_directory"]) / "ROOT-cli-final-message.txt"
    return [d["cli_launcher"], "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral", "--json", "--color", "never", "-C", item["working_directory"], "--model", "gpt-6.1-sol", "-c", 'model_reasoning_effort="ultra"', "-c", 'approval_policy="never"', "--sandbox", "read-only", "-c", "features.multi_agent=false", "-c", "features.memories=false", "-c", 'web_search="disabled"', "-c", "project_doc_max_bytes=0", "--output-last-message", str(capture), "-"]

def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False

def close_group(proc):
    if proc is None:
        return True
    if group_exists(proc.pid):
        os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=10)
    if group_exists(proc.pid):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 3
    while group_exists(proc.pid) and time.monotonic() < deadline:
        time.sleep(.05)
    return not group_exists(proc.pid)

def run_attempt(run, condition, batch, attempt, go_path, timeout=3600):
    run, d = campaign(run)
    go = validate_GO(run, d, go_path)  # This runs before creating any attempt files.
    item = route(d, condition, batch, attempt)
    slot = Path(item["output_directory"])
    selection = Path(item["selection_directory"])
    with exclusive(selection / "ROOT-reception.lock"):
        check_prior(selection, attempt, slot)
        check(item["assignment"])
        check(item["fixed_request"])
        argv = command(d, item)
        raw = Path(item["fixed_request"]["path"]).read_bytes()
        with capacity(run / "ROOT-capacity", timeout=60) as token:
            # Routing is recorded only outside the readonly input directory.
            start = save(slot / "ROOT-dispatch-start.json", {"status": "ROOT_about_to_launch_real_CLI", "at_utc": now(), "GO": go, "assignment": item["assignment"], "stdin": item["fixed_request"], "working_directory": item["working_directory"], "condition": condition, "batch_number": batch, "attempt_number": attempt, "argv": argv, "capacity_token": token, "route_appended_to_model_prompt": False, "resumed_or_inherited_conversation": False, "requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "actual_serving_model_verified": False})
            proc, timed_out, terminal, error = None, False, False, None
            events, stderr = slot / "ROOT-cli-events.jsonl", slot / "ROOT-stderr.txt"
            try:
                with events.open("xb") as out, stderr.open("xb") as err:
                    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=out, stderr=err, cwd=item["working_directory"], start_new_session=True)
                    save(slot / "ROOT-actual-process-start.json", {"at_utc": now(), "pid": proc.pid, "process_group_id": proc.pid, "start": start, "actual_CLI_process_started": True, "provider_API_call_count": None})
                    try:
                        proc.communicate(raw, timeout=timeout)
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        terminal = close_group(proc)
                    else:
                        # Codex's launcher child group must also be gone.
                        terminal = close_group(proc)
            except Exception as exc:
                error = {"type": type(exc).__name__, "message": str(exc)}
                terminal = close_group(proc)
            if not terminal:
                save(run / "ROOT-capacity" / f"capacity-{token}.blocked.json", {"at_utc": now(), "reason": "uncertain_or_live_actual_process_group", "process_group_id": None if proc is None else proc.pid, "attempt_start": start, "no_new_process_may_reuse_token": True})
            thread_ids = []
            try:
                thread_ids = [r["thread_id"] for r in events_from(events) if r.get("type") == "thread.started"]
            except Exception:
                pass  # Strict receiver records the malformed raw-event failure.
            capture = slot / "ROOT-cli-final-message.txt"
            completion = save(slot / "ROOT-process-completion.json", {"at_utc": now(), "provenance": "ROOT_subprocess_Popen_wait_real_events_capture", "fixture_only": False, "actual_process_terminal": terminal, "actual_CLI_process_started": proc is not None, "pid": None if proc is None else proc.pid, "returncode": None if proc is None else proc.returncode, "timed_out": timed_out, "launch_or_transport_error": error, "condition": condition, "batch_number": batch, "attempt_number": attempt, "start": start, "raw_cli_events": binding(events), "stderr": binding(stderr), "captured_final_message": binding(capture) if capture.exists() else None, "actual_cli_thread_ids": thread_ids, "provider_API_call_count": None})
            if not terminal:
                return {"state": "process_uncertain_do_not_retry", "completion": completion}
            return receive_locked(run, d, item)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    p.add_argument("--go", required=True)
    p.add_argument("--condition", required=True)
    p.add_argument("--batch", required=True, type=int)
    p.add_argument("--attempt", required=True, type=int, choices=(1, 2, 3))
    p.add_argument("--timeout", type=int, default=3600)
    a = p.parse_args()
    print(json.dumps(run_attempt(a.run, a.condition, a.batch, a.attempt, a.go, a.timeout), ensure_ascii=False))
