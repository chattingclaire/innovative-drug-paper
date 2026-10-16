"""Immutable byte bindings and ROOT-only routing; importing never dispatches."""
import contextlib
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

if not __debug__:
    raise RuntimeError("Do not run this interface with python -O")
HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
PYTHON = "/opt/homebrew/opt/python@3.14/bin/python3.14"
CONDITIONS = ("R1", "R2", "R3", "W", "H")
REQUIRED_KEYS = ("manual", "execution_prompt", "actor_instructions", "packet_schema", "output_schema", "output_validation_contract", "strict_technical_validator", "read_manifest_template", "response_retention_policy", "output_seal_template", "technical_failure_template", "run_scope_binding", "legacy_locator_alias_table_binding", "delivery_manifest_order_metadata_only", "attempt_output_routing", "campaign_scope_metadata_binding", "transport_helper_binding", "transport_common_binding")

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def strict(raw):
    def pairs(rows):
        d = {}
        for k, v in rows:
            if k in d:
                raise ValueError("Duplicate JSON key: " + k)
            d[k] = v
        return d
    def bad(x):
        raise ValueError("Nonfinite JSON number: " + x)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

def load(p):
    return strict(Path(p).read_bytes().decode("utf-8"))

def binding(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return {"path": str(p), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def check(b):
    if type(b.get("bytes")) is not int or not Path(b["path"]).is_absolute():
        raise ValueError("Invalid byte binding")
    actual = binding(b["path"])
    if any(actual[k] != b[k] for k in ("path", "bytes", "sha256")):
        raise ValueError("Changed bound input: " + b["path"])
    return actual

def put(p, raw):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    return binding(p)

def save(p, d):
    return put(p, (json.dumps(d, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())

def save_same(p, d):
    raw = (json.dumps(d, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    if Path(p).exists():
        if Path(p).read_bytes() != raw:
            raise ValueError("Existing ROOT metadata differs; retain it and stop: " + str(p))
        return binding(p)
    return put(p, raw)

def artifact_validate(name, data):
    import jsonschema
    schemas = load(HERE / "artifact-schemas.json")
    schema = {"$defs": schemas["$defs"], **schemas["$defs"][name]}
    jsonschema.Draft202012Validator(schema).validate(data)

def module(b, name):
    check(b)
    spec = importlib.util.spec_from_file_location(name, b["path"])
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def campaign(run):
    run = Path(run).resolve()
    d = load(run / "run-manifest.json")
    if d["run_id"] != run.name or d["status"] != "prepared_no_actual_dispatch":
        raise ValueError("Wrong campaign identity/state")
    if d["conditions"] != list(CONDITIONS) or d["batch_N"] != 87 or d["record_N"] != 800 or d["max_concurrent_CLI"] != 3:
        raise ValueError("Changed frozen diagnostic scope/capacity")
    for b in d["implementation_bindings"]:
        check(b)
    check(d["transport_contract"])
    return run, d

def route(d, condition, batch, attempt):
    if condition not in CONDITIONS or type(batch) is not int or not 1 <= batch <= d["batch_N"] or type(attempt) is not int or attempt not in (1, 2, 3):
        raise ValueError("Invalid external route")
    return next(r for r in d["routes"] if (r["condition"], r["batch_number"], r["attempt_number"]) == (condition, batch, attempt))

def selected_dir(d, condition, batch):
    return Path(route(d, condition, batch, 1)["selection_directory"])

def allowed_inputs(assignment_path):
    p = Path(assignment_path).resolve()
    a = load(p)
    rows = [a[k] for k in REQUIRED_KEYS] + a["packets"] + a["source_asset_bindings"] + [binding(p)]
    allowed = {}
    for b in rows:
        core = {k: b[k] for k in ("path", "bytes", "sha256")}
        if b["path"] in allowed and allowed[b["path"]] != core:
            raise ValueError("Conflicting allowed binding")
        allowed[b["path"]] = core
    return a, allowed

def check_prior(selection, attempt, slot):
    selection = Path(selection)
    if (selection / "root-selection.json").exists() or (selection / "root-zero-call-block.json").exists():
        raise ValueError("Whole batch already terminal; no duplicate dispatch/retry")
    for n in range(1, attempt):
        prior = load(selection / f"root-attempt-reception-{n:04d}.json")
        if prior["state"] != "technical_invalid_whole_batch":
            raise ValueError("Earlier actual attempt was not a technical failure")
        check(prior["completion"])
        c = load(prior["completion"]["path"])
        if c.get("actual_process_terminal") is not True:
            raise ValueError("Earlier process is live/uncertain")
    if (selection / f"root-attempt-reception-{attempt:04d}.json").exists() or any(Path(slot).iterdir()):
        raise ValueError("Attempt slot already used; preserve partial records")

@contextlib.contextmanager
def exclusive(path, blocking=False):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    f = p.open("a+b")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        yield f
    finally:
        f.close()

@contextlib.contextmanager
def capacity(directory, timeout=60):
    """Three shared OS lock tokens, held until the actual child is reaped."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    held = None
    while held is None:
        for n in (1, 2, 3):
            if (directory / f"capacity-{n}.blocked.json").exists():
                continue  # An uncertain live group cannot release usable capacity.
            f = (directory / f"capacity-{n}.lock").open("a+b")
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                if (directory / f"capacity-{n}.blocked.json").exists():
                    f.close()
                    continue
                held = (f, n)
                break
            except BlockingIOError:
                f.close()
        if held is None:
            if time.monotonic() >= deadline:
                raise TimeoutError("No actual CLI capacity token; no model dispatch")
            time.sleep(.05)
    try:
        yield held[1]
    finally:
        held[0].close()

def pid_dead(pid):
    if type(pid) is not int or pid <= 0:
        raise ValueError("Invalid production PID")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False

def validate_GO(run, d, go_path):
    """The ROOT must issue this only after genuine production terminal evidence."""
    go = load(go_path)  # Missing GO raises before any process/dispatch record.
    artifact_validate("ROOT_GO", go)
    if go.get("template_only") is not False or go.get("status") != "ROOT_authorized_actual_diagnostic_execution" or go.get("issuer") != "ROOT":
        raise ValueError("No actual ROOT execution authorization")
    if go.get("campaign_manifest") != binding(Path(run) / "run-manifest.json") or go.get("max_concurrent_CLI") != 3:
        raise ValueError("GO campaign/capacity mismatch")
    check(go["preflight_reception"])
    preflight = load(go["preflight_reception"]["path"])
    if preflight.get("ready_for_ROOT_review") is not True or preflight.get("model_calls") != 0 or preflight.get("campaign_manifest") != go["campaign_manifest"]:
        raise ValueError("GO does not bind this campaign's accepted no-call preflight")
    check(go["production_terminal_certificate"])
    terminal = load(go["production_terminal_certificate"]["path"])
    artifact_validate("ROOT_production_terminal_certificate", terminal)
    if terminal.get("template_only") is not False or terminal.get("status") != "actual_primary_and_recovery_all_terminal" or terminal.get("issuer") != "ROOT" or terminal.get("all_child_processes_terminal") is not True or terminal.get("active_model_process_N") != 0:
        raise ValueError("Production/recovery terminal prerequisite absent")
    if not terminal.get("terminal_evidence_bindings") or not terminal.get("closed_controller_and_child_pids"):
        raise ValueError("Empty production terminal evidence")
    for b in terminal["terminal_evidence_bindings"]:
        check(b)
        evidence = load(b["path"])
        if not any(evidence.get(k) is True for k in ("all_terminal", "actual_process_terminal", "all_primary_and_recovery_terminal", "actual_native_context_terminal")):
            raise ValueError("Terminal evidence has no genuine terminal flag")
    if not all(pid_dead(pid) for pid in terminal["closed_controller_and_child_pids"]):
        raise ValueError("A production/controller/child PID is still present; no overlap")
    if go.get("production_and_recovery_dispatch_closed") is not True or go.get("previous_results_or_history_injected") is not False:
        raise ValueError("GO must close previous dispatch and forbid inherited answers")
    for b in d["cli_executable_bindings"]:
        check(b)
    return binding(go_path)

def presentation_token(b, start, end):
    raw = f"{b['path']}\n{b['sha256']}\n{start}\n{end}".encode()
    return "PRESENT-" + hashlib.sha256(raw).hexdigest()

def presentation_payload(b, text, start, end):
    token = presentation_token(b, start, end)
    meta = {**b, "range_kind": "unicode_code_points", "start": start, "end": end, "presentation_event": token}
    return "PRESENTATION_BEGIN " + json.dumps(meta, ensure_ascii=False, sort_keys=True) + "\n" + text[start:end] + "\nPRESENTATION_END " + token + "\n"
