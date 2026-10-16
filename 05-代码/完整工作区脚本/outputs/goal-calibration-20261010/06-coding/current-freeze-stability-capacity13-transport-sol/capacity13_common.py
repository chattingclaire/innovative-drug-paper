"""ROOT-only capacity13 overlay of sealed cap3 preparation; never changes research inputs."""
import importlib.util
import json
from pathlib import Path
import sys
import types
sys.dont_write_bytecode = True
HERE13 = Path(__file__).resolve().parent
BASE_COMMON_BINDING = {'path': '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/current-freeze-stability-external-capture-v2-sol/transport_common.py', 'bytes': 10574, 'sha256': '2624060c822cd22e96b8c3b784f8026022c1a6c72c3771af08de0dc011f1d7aa'}
raw_base = Path(BASE_COMMON_BINDING["path"]).read_bytes()
import hashlib
if len(raw_base) != BASE_COMMON_BINDING["bytes"] or hashlib.sha256(raw_base).hexdigest() != BASE_COMMON_BINDING["sha256"]:
    raise ValueError("Sealed base common changed")
_base = types.ModuleType("immutable_cap3_common")
_base.__file__ = BASE_COMMON_BINDING["path"]
exec(compile(raw_base, _base.__file__, "exec"), _base.__dict__)
for _name, _value in _base.__dict__.items():
    if not _name.startswith("__"):
        globals().setdefault(_name, _value)

def profile():
    return load(HERE13 / "run-manifest.json")

def campaign(run):
    d13 = profile()
    check(d13["base_campaign_manifest"])
    check(d13["base_preparation_freeze"])
    check(d13["capacity13_sidecar"])
    for b in d13["capacity13_implementation_bindings"]:
        check(b)
    base_run = Path(d13["base_campaign_manifest"]["path"]).parent
    if Path(run).resolve() != base_run.resolve():
        raise ValueError("Capacity13 entry must use the unchanged original campaign/output slots")
    base_run, base_doc = _base.campaign(base_run)
    keys = ("base_campaign_manifest", "base_preparation_freeze", "capacity13_sidecar", "capacity13_implementation_bindings")
    expected = dict(base_doc)
    expected["max_concurrent_CLI"] = 13
    for key in keys:
        expected[key] = d13[key]
    if d13 != expected:
        raise ValueError("Capacity overlay changed fields beyond capacity/ROOT-only bindings")
    return base_run, d13

def artifact_validate(name, data):
    if name != "ROOT_GO":
        return _base.artifact_validate(name, data)
    import jsonschema
    schemas = load(HERE13 / "artifact-schemas-capacity13.json")
    schema = {"$defs": schemas["$defs"], **schemas["$defs"][name]}
    jsonschema.Draft202012Validator(schema).validate(data)

@contextlib.contextmanager
def capacity(directory, timeout=60):
    """Thirteen shared OS lock tokens, held until the actual child is reaped."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    held = None
    while held is None:
        for n in range(1, 14):
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

def _base_GO_logic_capacity13(run, d, go_path):
    """The ROOT must issue this only after genuine production terminal evidence."""
    go = load(go_path)  # Missing GO raises before any process/dispatch record.
    artifact_validate("ROOT_GO", go)
    if go.get("fixture_only") is True:
        raise ValueError("Constructed GO cannot authorize a model")
    if go.get("template_only") is not False or go.get("status") != "ROOT_authorized_actual_diagnostic_execution" or go.get("issuer") != "ROOT":
        raise ValueError("No actual ROOT execution authorization")
    if go.get("campaign_manifest") != binding(Path(run) / "run-manifest.json") or go.get("max_concurrent_CLI") != 13:
        raise ValueError("GO campaign/capacity mismatch")
    check(go["preflight_reception"])
    preflight = load(go["preflight_reception"]["path"])
    if preflight.get("artifact_type") != "no_model_external_capture_preflight" or preflight.get("ready_for_ROOT_review") is not True or preflight.get("model_calls") != 0 or preflight.get("campaign_manifest") != go["campaign_manifest"]:
        raise ValueError("GO does not bind this campaign's accepted no-call preflight")
    check(go["production_terminal_certificate"])
    terminal = load(go["production_terminal_certificate"]["path"])
    artifact_validate("ROOT_production_terminal_certificate", terminal)
    if terminal.get("fixture_only") is True:
        raise ValueError("Constructed production terminal certificate cannot authorize a model")
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

def validate_GO(run, d, go_path):
    result = _base_GO_logic_capacity13(run, d, go_path)
    go = load(go_path)
    if go["capacity13_profile"] != binding(HERE13 / "run-manifest.json") or go["capacity13_sidecar"] != d["capacity13_sidecar"]:
        raise ValueError("GO does not bind the external capacity13 revision")
    if go["capacity_only_exception_acknowledged"] is not True or go["old_cap3_entrypoint_not_authorized"] is not True:
        raise ValueError("GO must explicitly choose only capacity13 and disclose capacity exception")
    check(go["capacity13_preflight"])
    preflight = load(go["capacity13_preflight"]["path"])
    if preflight.get("artifact_type") != "no_model_capacity13_overlay_preflight" or preflight.get("ready_for_ROOT_review") is not True or preflight.get("model_calls") != 0 or preflight.get("classifier_calls") != 0 or preflight.get("capacity13_profile") != go["capacity13_profile"]:
        raise ValueError("GO does not bind the checked capacity13 preparation")
    return result
