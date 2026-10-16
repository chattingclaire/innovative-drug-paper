"""Candidate thin durable wait around the separately adopted terminal recovery entry."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
RUNTIME_SCOPE = "original_durable_wait_plus_terminal_pointer_bounds_adapter"


def recovery_module():
    path = HERE.parent / "terminal-recovery-preparation/entry.py"
    expected = json.loads((HERE / "manifest.json").read_bytes())["bindings"]["recovery_entry"]
    raw = path.read_bytes()
    if expected != {"path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}:
        raise ValueError("Changed bound recovery entry before import")
    spec = importlib.util.spec_from_file_location("terminal_pointer_recovery_admission", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def frozen(check_own_seal=True):
    recovery = recovery_module()
    cfg = recovery.load(HERE / "manifest.json")
    recovery.require(cfg["candidate_only"] is True and cfg["execution_authorized"] is False,
                     "Candidate manifest does not authorize execution")
    for value in cfg["bindings"].values():
        recovery.exact(value)
    for value in recovery.load(cfg["bindings"]["recovery_seal"]["path"])["files"]:
        recovery.exact(value)
    if check_own_seal:
        for value in recovery.load(HERE / "seal.json")["files"]:
            recovery.exact(value)
    recovery_cfg = recovery.frozen()
    recovery.require(recovery.bind(recovery.__file__) == cfg["bindings"]["recovery_entry"], "Wrong recovery module")
    old = recovery.load(cfg["bindings"]["original_authorization_03"]["path"])
    recovery.require(old.get("issuer") == "ROOT" and old.get("template_only") is False
                     and old.get("same_campaign_continuation") is True
                     and old["unchanged_GO"] == cfg["bindings"]["original_GO"]
                     and old["campaign_manifest"] == cfg["bindings"]["campaign_manifest"], "Wrong original authorization chain")
    rows = old["closed_attempts"]
    keys = [(row["condition"], row["batch_number"], row["attempt_number"]) for row in rows]
    expected = [("R3", 42, 3), ("R3", 47, 2), ("R3", 49, 3),
                *[("R3", n, 1) for n in range(51, 59)], ("R3", 59, 2), ("R3", 60, 1)]
    recovery.require(len(rows) == len(set(keys)) == 13 and set(keys) == set(expected), "Changed original 13-orphan scope")
    for row in rows:
        for key in ("terminal_certificate", "technical_reception"):
            recovery.exact(row[key])
        cert = recovery.load(row["terminal_certificate"]["path"])
        receipt = recovery.load(row["technical_reception"]["path"])
        route = tuple(row[k] for k in ("condition", "batch_number", "attempt_number"))
        recovery.require(tuple(cert[k] for k in ("condition", "batch_number", "attempt_number")) == route
                         and tuple(receipt[k] for k in ("condition", "batch_number", "attempt_number")) == route
                         and cert["returncode"] is None and cert["returncode_status"] == "unknown_parent_wait_unavailable"
                         and receipt["state"] == "technical_invalid_whole_batch"
                         and receipt["completion"] == row["terminal_certificate"]
                         and receipt.get("error", {}).get("type") == "OrphanedControllerWaitReceiptUnavailable",
                         "Original orphan certificate/reception semantics changed")
    return cfg, recovery_cfg, recovery, old


def controller_argv(cfg, authorization):
    return [cfg["python"], "-B", cfg["bindings"]["recovery_entry"]["path"],
            "--mode", "run", "--adoption", authorization["pointer_recovery_adoption"]["path"]]


def authorization_gate(path, context):
    cfg, recovery_cfg, recovery, old = context
    recovery.require(path is not None, "Separate actual ROOT durable recovery authorization required")
    authorization_binding = recovery.bind(path)
    authorization = recovery.load(path)
    flags = {"artifact_type": "ROOT_stability_pointer_bounds_durable_recovery_authorization",
             "issuer": "ROOT", "template_only": False, "fixture_only": False,
             "execution_authorized": True, "same_campaign_continuation": True,
             "original_max3_preserved": True, "orphan_recovery_adopted": True,
             "runtime_scope": RUNTIME_SCOPE}
    recovery.require(all(authorization.get(k) == v for k, v in flags.items()), "Actual ROOT durable recovery authority absent")
    expected = {"supervisor": recovery.bind(__file__), "actual_supervisor_entrypoint": recovery.bind(__file__),
                "configuration": recovery.bind(HERE / "manifest.json"), "candidate_seal": recovery.bind(HERE / "seal.json"),
                "original_authorization_03": cfg["bindings"]["original_authorization_03"],
                "execution_wrapper": cfg["bindings"]["recovery_entry"],
                "recovery_candidate_seal": cfg["bindings"]["recovery_seal"],
                "reused_wait_implementation": cfg["bindings"]["wait_helper"],
                "unchanged_GO": old["unchanged_GO"], "campaign_manifest": old["campaign_manifest"],
                "unchanged_entry": old["unchanged_entry"], "unchanged_adoption": old["unchanged_adoption"],
                "closed_attempts": old["closed_attempts"]}
    recovery.require(all(authorization.get(k) == v for k, v in expected.items()), "Authorization changes a fixed binding/history")
    pointer_adoption = authorization.get("pointer_recovery_adoption")
    recovery.require(isinstance(pointer_adoption, dict), "Separate pointer recovery adoption required")
    recovery.exact(pointer_adoption)
    recovery.require(authorization.get("actual_controller_argv") == controller_argv(cfg, authorization), "Actual controller argv is not explicitly bound")
    out = Path(authorization["output_directory"])
    recovery.require(str(out) == cfg["output_directory"] and out.is_absolute()
                     and str(out.resolve()) == cfg["output_directory"] and not out.exists(), "Unique fixed new output directory required")
    # This is the new terminal admission; old metadata_gate's empty later slots are not replayed.
    recovery.require_adoption(pointer_adoption["path"], recovery_cfg)
    recovery.exact(authorization_binding)
    return authorization, authorization_binding, out


def exact_self_identity(cfg, authorization_path, platform, rows, actual_pid, actual_sid, actual_argv):
    expected = [cfg["python"], "-B", str(HERE / "supervisor.py"), "--authorization", authorization_path]
    if actual_argv != expected[2:]:
        return False
    own = [row for row in rows if row["pid"] == actual_pid]
    return len(own) == 1 and platform.self_identity_ok(own[0], expected, actual_pid, actual_sid, cfg["python"])


def recovery_gates(recovery, recovery_cfg, adoption_path):
    adopted = recovery.require_adoption(adoption_path, recovery_cfg)
    evidence = recovery.terminal_evidence(recovery_cfg, adopted)
    observations = recovery.fresh_quiet_gate(recovery_cfg)
    return evidence, observations


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization")
    args = parser.parse_args(argv)
    if args.authorization is None:
        raise ValueError("Separate actual ROOT durable recovery authorization required")
    context = frozen()
    cfg, recovery_cfg, recovery, old = context
    authorization, authorization_binding, out = authorization_gate(args.authorization, context)
    original = recovery.module(cfg["bindings"]["wait_helper"], "unchanged_durable_recovery_wait")
    platform = recovery.module(cfg["bindings"]["platform_identity_helper"], "unchanged_framework_identity_helper")
    recovery.require(platform.FRAMEWORK_RUNTIME == cfg["bindings"]["python_process_image"]
                     and platform.FROZEN_LAUNCH_PYTHON == cfg["bindings"]["python_launcher"],
                     "Runtime provenance must use the exact original Framework/launcher bindings")
    ps = recovery.module(cfg["bindings"]["process_helper"], "unchanged_durable_process_observer")
    recovery.require(os.getsid(0) == os.getpid(), "Detached supervisor session required")
    stdin = os.fstat(0)
    recovery.require(stat.S_ISCHR(stdin.st_mode) and stdin.st_rdev == os.stat("/dev/null").st_rdev,
                     "Supervisor stdin must be DEVNULL")
    recovery.require(exact_self_identity(cfg, args.authorization, platform, ps.ps_rows(),
                                        os.getpid(), os.getsid(0), sys.argv), "Exact supervisor PID/SID/Framework/argv identity required")
    with original.exclusive():  # The original shared supervisor lock, held across real parent wait.
        recovery.exact(authorization_binding)
        recovery.exact(authorization["pointer_recovery_adoption"])
        evidence, observations = recovery_gates(recovery, recovery_cfg, authorization["pointer_recovery_adoption"]["path"])
        recovery.require(not out.exists(), "Recovery output already exists; no automatic restart")
        recovery.exact(authorization_binding)
        recovery.exact(authorization["pointer_recovery_adoption"])
        actual_argv = controller_argv(cfg, authorization)
        provenance = {"ROOT_authorization": authorization_binding,
                      "actual_supervisor_entrypoint": recovery.bind(__file__),
                      "configuration": recovery.bind(HERE / "manifest.json"),
                      "self_runtime_executable_binding": cfg["bindings"]["python_process_image"],
                      "reused_wait_implementation": cfg["bindings"]["wait_helper"],
                      "execution_wrapper": cfg["bindings"]["recovery_entry"],
                      "pointer_recovery_adoption": authorization["pointer_recovery_adoption"],
                      "runtime_scope": RUNTIME_SCOPE,
                      "fresh_process_gate": {"terminal_evidence": evidence, "observations": observations}}
        result = original.wait_and_seal(actual_argv, out, provenance)
    if not result["actual_wait_returned"] or result["launch_or_supervision_error"] is not None:
        raise SystemExit(1)
    raise SystemExit(result["returncode"] if result["returncode"] >= 0 else 128 - result["returncode"])


if __name__ == "__main__":
    main()
