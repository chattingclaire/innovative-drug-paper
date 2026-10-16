"""Only capacity13 competition and missing/template GO gates; no real CLI or classifier."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
sys.dont_write_bytecode = True
import capacity13_common as common

def state(root, delta=0):
    with (root / "counter.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        p = root / "counter.json"
        doc = json.loads(p.read_text()) if p.exists() else {"active": 0, "peak": 0, "entered": 0}
        doc["active"] += delta
        if delta > 0:
            doc["entered"] += 1
        doc["peak"] = max(doc["peak"], doc["active"])
        if delta:
            p.write_text(json.dumps(doc))
        return doc

def worker(root):
    root = Path(root)
    with common.capacity(root / "tokens", timeout=20):
        state(root, 1)
        deadline = time.monotonic() + 15
        while not (root / "release").exists():
            if time.monotonic() > deadline:
                raise TimeoutError("Test barrier was not released")
            time.sleep(.01)
        time.sleep(.05)
        state(root, -1)

def run_controls(root):
    root = Path(root)
    root.mkdir(exist_ok=False)
    from bootstrap import runtime
    _, runner, _ = runtime()
    d = common.profile()
    run = Path(d["base_campaign_manifest"]["path"]).parent
    slots = [Path(x["output_directory"]) for x in d["routes"]]
    assert all(not any(p.iterdir()) for p in slots)
    actual = subprocess.Popen
    intercepted = []
    def forbidden(*args, **kwargs):
        intercepted.append({"args": repr(args)})
        raise AssertionError("Model process must never be attempted without GO")
    results = []
    runner.subprocess.Popen = forbidden
    try:
        try:
            runner.run_attempt(run, "R1", 1, 1, root / "absent-actual-GO.json")
        except FileNotFoundError:
            results.append({"name": "missing_GO_rejects_before_Popen_and_slot_files", "pass": not intercepted})
        else:
            raise AssertionError("Missing GO accepted")
        schema = common.load(Path(__file__).parent / "artifact-schemas-capacity13.json")
        template = {"issuer": "ROOT", "status": "ROOT_authorized_actual_diagnostic_execution", "template_only": True, "campaign_manifest": d["base_campaign_manifest"], "preflight_reception": common.binding(Path(d["base_campaign_manifest"]["path"]).parent.parent / "preflight-reception.json"), "production_terminal_certificate": {"path": "/nonexistent/terminal.json", "bytes": 0, "sha256": "0" * 64}, "max_concurrent_CLI": 13, "production_and_recovery_dispatch_closed": True, "previous_results_or_history_injected": False, "capacity13_profile": common.binding(Path(__file__).parent / "run-manifest.json"), "capacity13_preflight": {"path": "/nonexistent/capacity13-preflight.json", "bytes": 0, "sha256": "0" * 64}, "capacity13_sidecar": d["capacity13_sidecar"], "capacity_only_exception_acknowledged": True, "old_cap3_entrypoint_not_authorized": True}
        common.save(root / "invalid-template-GO.json", template)
        import jsonschema
        try:
            runner.run_attempt(run, "R1", 1, 1, root / "invalid-template-GO.json")
        except jsonschema.ValidationError as error:
            assert list(error.path) == ["template_only"], list(error.path)
            results.append({"name": "capacity13_template_GO_rejected_by_exact_template_flag", "pass": not intercepted})
        else:
            raise AssertionError("Template GO accepted")
    finally:
        runner.subprocess.Popen = actual
    assert not intercepted and all(not any(p.iterdir()) for p in slots)
    capacity_root = root / "capacity14-local-worker-test"
    capacity_root.mkdir()
    children = [subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--worker", str(capacity_root)], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(14)]
    deadline = time.monotonic() + 12
    try:
        while state(capacity_root)["active"] != 13 and time.monotonic() < deadline:
            time.sleep(.02)
        reached = state(capacity_root)
    finally:
        (capacity_root / "release").write_text("release local test workers only\n")
    child_rows = []
    for p in children:
        out, err = p.communicate(timeout=20)
        child_rows.append({"pid": p.pid, "returncode": p.returncode, "stdout": out.decode(), "stderr": err.decode()})
    final = state(capacity_root)
    passed = reached["active"] == 13 and final == {"active": 0, "peak": 13, "entered": 14} and all(p["returncode"] == 0 for p in child_rows)
    results.append({"name": "14_real_local_python_workers_exactly13_tokens_no_more13_active", "pass": passed, "at_release": reached, "final": final, "workers": child_rows, "not_CLI_or_model_workers": True})
    doc = {"artifact_type": "bounded_capacity13_mechanical_controls", "at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "control_N": len(results), "all_pass": all(r["pass"] for r in results), "model_calls": 0, "classifier_calls": 0, "actual_CLI_processes_including_help": 0, "intercepted_model_Popen_N": len(intercepted), "local_nonmodel_worker_N": 14, "old_1305_slots_still_empty": all(not any(p.iterdir()) for p in slots), "old37_controls_not_rerun": True, "results": results}
    common.save(root / "results.json", doc)
    print(json.dumps({"all_pass": doc["all_pass"], "control_N": len(results), "local_peak": final["peak"], "model_calls": 0}))
    if not doc["all_pass"]:
        raise SystemExit(1)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--worker")
    p.add_argument("--output")
    a = p.parse_args()
    if a.worker:
        worker(a.worker)
    else:
        run_controls(a.output)
