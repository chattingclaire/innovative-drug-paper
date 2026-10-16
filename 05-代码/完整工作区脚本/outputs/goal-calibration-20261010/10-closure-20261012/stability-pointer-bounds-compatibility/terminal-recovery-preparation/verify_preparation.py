"""Pure candidate mechanics; no adopted run, receiver, model, signal or lock."""
import datetime as dt
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
import entry


def main():
    cfg = entry.frozen(check_own_seal=False)
    before = {k: entry.bind(v["path"]) for k, v in cfg["bindings"].items()}
    checks = []
    try:
        entry.main(["--mode", "run"])
    except ValueError as error:
        assert "ROOT recovery adoption required" in str(error)
        checks.append({"case": "missing_adoption_refused_before_execution", "passed": True, "error": str(error)})
    else:
        raise AssertionError("Missing adoption was admitted")
    observer = entry.module(cfg["bindings"]["process_helper"], "readonly_mechanical_process_check")
    rows = observer.ps_rows()
    blockers = entry.process_blockers(cfg, rows, None)
    assert any(r["pid"] == 1130 and r["lstart"] == "Mon Oct 12 16:24:46 2026" for r in blockers)
    try:
        entry.fresh_quiet_gate(cfg)
    except ValueError as error:
        assert "still live" in str(error)
        checks.append({"case": "actual_live_1130_and_campaign_children_refused", "passed": True,
                       "error": str(error), "blocker_identities": [{k: r[k] for k in ("pid", "ppid", "lstart")} for r in blockers]})
    else:
        raise AssertionError("Live original controller was admitted")
    order = []
    original_loader = object()
    wrapped_loader = object()
    receiver = types.SimpleNamespace(module=original_loader)
    controller, runner = object(), object()
    def old_runtime():
        order.append("original_bootstrap_runtime")
        return controller, runner, receiver
    def wrap(loader):
        assert loader is original_loader
        order.append("only_receiver_module_loader_wrapped")
        return wrapped_loader
    bootstrap = types.SimpleNamespace(runtime=old_runtime)
    entry.install_runtime_hook(bootstrap, types.SimpleNamespace(wrap_receiver_module_loader=wrap))
    result = bootstrap.runtime()
    assert result == (controller, runner, receiver) and receiver.module is wrapped_loader
    assert order == ["original_bootstrap_runtime", "only_receiver_module_loader_wrapped"]
    checks.append({"case": "runtime_hook_order_and_identity", "passed": True, "order": order,
                   "original_controller_and_runner_returned": True})
    # The real bootstrap only loads/compiles modules; no execute/run/receive call.
    sys.path.insert(0, cfg["capacity13_directory"])
    real_bootstrap = entry.module(cfg["bindings"]["bootstrap"], "readonly_bootstrap_compile_control")
    real_adapter = entry.module(cfg["bindings"]["pointer_adapter"], "readonly_pointer_adapter_control")
    entry.install_runtime_hook(real_bootstrap, real_adapter)
    real_controller, real_runner, real_receiver = real_bootstrap.runtime()
    assert real_controller.receive is real_receiver.receive
    assert real_runner.receive_locked is real_receiver.receive_locked
    validator = real_receiver.module(cfg["bindings"]["original_validator"], "unchanged_production_validator_capture")
    try:
        validator.verify(cfg["bindings"]["real_assignment"]["path"], cfg["bindings"]["real_first"]["path"])
    except ValueError as error:
        assert "contexts/11/title" in str(error)
    else:
        raise AssertionError("Actual runtime loader did not apply the narrow adapter")
    checks.append({"case": "real_frozen_bootstrap_readonly_module_loading", "passed": True,
                   "original_receive_function_identities_preserved": True,
                   "H0041_pure_validator_ValueError": True, "receiving_called": False})
    argv = cfg["original_outer_argv"][2:]
    assert argv[0] == cfg["bindings"]["outer_entry"]["path"] and argv[1] == "--original-entry" and "-B" not in argv
    checks.append({"case": "outer_argv_excludes_python_and_B", "passed": True})
    after = {k: entry.bind(v["path"]) for k, v in cfg["bindings"].items()}
    assert before == after
    print(json.dumps({"at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                      "candidate_only": True, "all_checks_passed": True, "checks": checks,
                      "bindings_before": before, "bindings_after": after,
                      "all_bound_files_unchanged": True, "actual_receiving_calls": 0,
                      "model_calls": 0, "process_signals": 0, "lock_acquisitions": 0,
                      "campaign_or_queue_file_writes": 0, "actual_adoption_generated": False,
                      "outer_main_called": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
