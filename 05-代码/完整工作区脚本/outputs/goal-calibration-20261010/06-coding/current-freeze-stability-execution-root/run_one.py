"""Launch one genuine fresh CLI attempt only after a separate ROOT execution GO."""
import argparse
import fcntl
import json
from pathlib import Path
import subprocess
from common import campaign, route, selected_dir, check_prior, binding, check, load, save, put, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    p.add_argument("--condition", required=True)
    p.add_argument("--batch", type=int, required=True)
    p.add_argument("--attempt", type=int, choices=(1, 2, 3), required=True)
    p.add_argument("--capacity-slot", type=int, choices=(1, 2, 3), required=True)
    a = p.parse_args()
    run, doc = campaign(a.run)
    go = load(run / "ROOT-execution-GO.json")
    assert go["status"] == "ROOT_authorized_actual_diagnostic_execution"
    assert go["campaign"] == binding(run / "run-manifest.json")
    assert go["max_concurrent_CLI"] == 3
    for item in go["required_terminal_bindings"]:
        check(item)
    # A running primary scheduler holds this same file exclusively. Shared
    # leases allow only this diagnostic's separately locked three CLI slots.
    with Path(doc["shared_primary_scheduler_lock"]).open("a+") as common_lock, (run / f"capacity-{a.capacity_slot}.lock").open("a+") as slot_lock:
        fcntl.flock(common_lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        fcntl.flock(slot_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        item = route(doc, a.condition, a.batch, a.attempt)
        directory = selected_dir(doc, a.condition, a.batch)
        check_prior(directory, a.attempt)
        for bound in [item["assignment"], item["fixed_request"], *doc["cli_executable_bindings"]]:
            check(bound)
        slot = Path(item["output_directory"])
        assert slot.is_dir() and not list(slot.iterdir()), "Actual attempt slot must be empty"
        metadata = {"logical_dispatch_label": item["logical_dispatch_label"], "attempt_number": a.attempt, "own_output_slot": str(slot), "execution_transport": "fresh_codex_cli_exec"}
        if a.condition == "W":
            metadata["assignment_override"] = item["assignment"]["path"]
        prompt = Path(item["fixed_request"]["path"]).read_bytes() + "\n请求外操作元数据（逻辑派发标签不是collaboration代理身份）：\n".encode() + json.dumps(metadata, ensure_ascii=False).encode() + b"\n"
        prompt_binding = put(slot / "ROOT-cli-dispatch-prompt.txt", prompt)
        command = [doc["cli_launcher"], "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral", "--json", "--color", "never", "-C", str(slot), "--model", "gpt-6.1-sol", "-c", 'model_reasoning_effort="ultra"', "-c", 'approval_policy="never"', "--sandbox", "workspace-write", "-c", "features.multi_agent=false", "-c", "features.memories=false", "-c", 'web_search="disabled"', "-c", "project_doc_max_bytes=0", "--output-last-message", str(slot / "ROOT-cli-final-message.txt"), "-"]
        start = save(slot / "ROOT-cli-dispatch-start.json", {"status": "actual_cli_process_about_to_start", "at_utc": now(), "GO": binding(run / "ROOT-execution-GO.json"), "assignment": item["assignment"], "prompt": prompt_binding, "fixed_request": item["fixed_request"], "metadata": metadata, "argv": command, "requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "resumed_or_inherited_conversation": False})
        out, err = slot / "ROOT-cli-events.jsonl", slot / "ROOT-cli-stderr.txt"
        with out.open("xb") as output, err.open("xb") as errors:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=output, stderr=errors, cwd=slot)
            process.communicate(prompt)
        thread_ids, counts = [], {}
        for line in out.read_text(errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = event.get("type", "unknown")
            counts[kind] = counts.get(kind, 0) + 1
            if kind == "thread.started":
                thread_ids.append(event.get("thread_id"))
        receipt = {"status": "actual_cli_process_terminal", "at_utc": now(), "start": start, "returncode": process.returncode, "actual_cli_thread_ids": thread_ids, "event_type_counts": counts, "raw_cli_events": binding(out), "stderr": binding(err), "requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "logical_dispatch_label": item["logical_dispatch_label"], "condition": a.condition, "batch_number": a.batch, "attempt_number": a.attempt, "provider_wire_or_serving_model_authentication_claimed": False, "first_file_exists": (slot / "first.json").exists(), "accuracy_compared": False}
        save(slot / "ROOT-cli-process-completion.json", receipt)
        print(json.dumps({"status": receipt["status"], "returncode": process.returncode, "thread_ids": thread_ids}, ensure_ascii=False))


if __name__ == "__main__":
    main()
