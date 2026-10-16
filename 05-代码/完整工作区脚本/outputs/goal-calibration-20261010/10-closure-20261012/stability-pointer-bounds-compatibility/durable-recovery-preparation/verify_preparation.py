"""Pure mechanics: no actual authorization, locks, parent wait, signals or models."""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
import supervisor


def main():
    ctx = supervisor.frozen(check_own_seal=False)
    cfg, recovery_cfg, recovery, old = ctx
    before = {k: recovery.bind(v["path"]) for k, v in cfg["bindings"].items()}
    orphan_before = [recovery.bind(row[key]["path"]) for row in old["closed_attempts"] for key in ("terminal_certificate", "technical_reception")]
    checks = []
    try:
        supervisor.main([])
    except ValueError as error:
        assert "ROOT durable recovery authorization required" in str(error)
        checks.append({"case": "missing_authority_refused_before_lock_or_launch", "passed": True})
    else:
        raise AssertionError("Missing authorization admitted")
    platform = recovery.module(cfg["bindings"]["platform_identity_helper"], "pure_platform_identity_control")
    assert platform.FRAMEWORK_RUNTIME == cfg["bindings"]["python_process_image"]
    assert platform.FROZEN_LAUNCH_PYTHON == cfg["bindings"]["python_launcher"]
    fake_auth_path = str(Path(cfg["output_directory"]).parent / "ROOT-FIXTURE-NOT-CREATED.json")
    expected = [cfg["python"], "-B", str(supervisor.HERE / "supervisor.py"), "--authorization", fake_auth_path]
    pid = os.getpid()
    row = {"pid": pid, "command": cfg["bindings"]["python_process_image"]["path"] + " " + " ".join(expected[1:]),
           "ppid": 1, "pgid": pid, "stat": "S", "lstart": "Tue Oct 13 02:00:00 2026"}
    assert supervisor.exact_self_identity(cfg, fake_auth_path, platform, [row], pid, pid, expected[2:])
    assert not supervisor.exact_self_identity(cfg, fake_auth_path, platform, [row], pid, pid + 1, expected[2:])
    assert not supervisor.exact_self_identity(cfg, fake_auth_path, platform, [row], pid + 1, pid + 1, expected[2:])
    assert not supervisor.exact_self_identity(cfg, fake_auth_path, platform, [row], pid, pid, expected[2:] + ["--extra"])
    wrong = dict(row, command="/usr/bin/python3 " + " ".join(expected[1:]))
    assert not supervisor.exact_self_identity(cfg, fake_auth_path, platform, [wrong], pid, pid, expected[2:])
    checks.append({"case": "exact_Framework_PID_SID_full_argv_controls", "passed": True, "fixture_only": True})
    # No recovery entry path in the supervisor's argv; original process matcher is untouched.
    assert recovery_cfg["bindings"]["outer_entry"]["path"] not in row["command"]
    assert str(Path(recovery.__file__).resolve()) not in row["command"]
    assert recovery.process_blockers(recovery_cfg, [row], pid) == []
    old_controller = {"pid": 1130, "ppid": 1122, "pgid": 1130, "stat": "S",
                      "lstart": "Mon Oct 12 16:24:46 2026", "command": "original controller"}
    assert recovery.process_blockers(recovery_cfg, [row, old_controller], pid) == [old_controller]
    checks.append({"case": "exact_new_supervisor_not_self_blocked_old_controller_still_blocked", "passed": True, "fixture_only": True})
    order = []
    stub = types.SimpleNamespace(
        require_adoption=lambda path, cfg: order.append("require_adoption") or {"fixture_only": True},
        terminal_evidence=lambda cfg, adopted: order.append("terminal_evidence") or {},
        fresh_quiet_gate=lambda cfg: order.append("fresh_quiet_gate") or [])
    supervisor.recovery_gates(stub, {}, "fixture-not-created")
    assert order == ["require_adoption", "terminal_evidence", "fresh_quiet_gate"]
    checks.append({"case": "reused_recovery_gate_order", "passed": True, "fixture_only": True, "order": order})
    fake = {"pointer_recovery_adoption": {"path": "fixture-not-created"}}
    actual = supervisor.controller_argv(cfg, fake)
    assert actual == [cfg["python"], "-B", cfg["bindings"]["recovery_entry"]["path"], "--mode", "run", "--adoption", "fixture-not-created"]
    checks.append({"case": "queue_compatible_controller_argv", "passed": True})
    original = recovery.module(cfg["bindings"]["wait_helper"], "readonly_original_wait_identity_control")
    assert Path(original.exclusive.__wrapped__.__code__.co_filename).resolve() == Path(cfg["bindings"]["wait_helper"]["path"])
    assert Path(original.wait_and_seal.__code__.co_filename).resolve() == Path(cfg["bindings"]["wait_helper"]["path"])
    checks.append({"case": "original_exclusive_and_wait_functions_reused_without_invocation", "passed": True})
    after = {k: recovery.bind(v["path"]) for k, v in cfg["bindings"].items()}
    orphan_after = [recovery.bind(row[key]["path"]) for row in old["closed_attempts"] for key in ("terminal_certificate", "technical_reception")]
    assert before == after and orphan_before == orphan_after
    assert not Path(cfg["output_directory"]).exists()
    print(json.dumps({"at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "candidate_only": True,
                      "all_checks_passed": True, "checks": checks, "bindings_before": before,
                      "bindings_after": after, "original_orphan_bindings_before": orphan_before,
                      "original_orphan_bindings_after": orphan_after, "original_13_orphan_receipts_unchanged": True,
                      "output_directory_created": False, "actual_authorization_created": False,
                      "original_metadata_gate_called": False, "lock_acquisitions": 0,
                      "wait_and_seal_calls": 0, "recovery_entry_run_calls": 0,
                      "receiving_calls": 0, "model_calls": 0, "process_signals": 0,
                      "campaign_and_queue_writes": 0}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
