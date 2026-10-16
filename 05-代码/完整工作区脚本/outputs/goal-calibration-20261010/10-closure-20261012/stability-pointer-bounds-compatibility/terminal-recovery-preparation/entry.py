"""Candidate recovery entry: extra terminal gates, then the unchanged outer main."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    def unique(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate metadata key")
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique)


def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def exact(value):
    require(bind(value["path"]) == value, "Changed binding: " + value["path"])


def module(value, name):
    exact(value)
    spec = importlib.util.spec_from_file_location(name, value["path"])
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def utc(value):
    result = dt.datetime.fromisoformat(value)
    require(result.tzinfo is not None, "Evidence time lacks timezone")
    return result.astimezone(dt.timezone.utc)


def frozen(check_own_seal=True):
    require(__debug__, "Original assertions must remain enabled")
    cfg = load(HERE / "manifest.json")
    require(cfg["candidate_only"] is True and cfg["execution_authorized"] is False,
            "Candidate manifest must not grant execution authority")
    for value in cfg["bindings"].values():
        exact(value)
    for value in load(cfg["bindings"]["pointer_adapter_seal"]["path"])["files"]:
        exact(value)
    if check_own_seal:
        for value in load(HERE / "seal.json")["files"]:
            exact(value)
    require(Path(sys.executable).resolve() == Path(cfg["python"]).resolve(), "Frozen Python required")
    start = load(cfg["bindings"]["controller_start"]["path"])
    identity = load(cfg["bindings"]["controller_identity"]["path"])
    require(start["actual_Popen_started"] is True
            and start["controller_pid"] == identity["pid"] == 1130
            and identity["birth_observation_status"] == "observed"
            and start["argv"] == cfg["original_outer_argv"], "Original controller identity/argv differs")
    require(cfg["original_outer_argv"][2] == cfg["bindings"]["outer_entry"]["path"], "Wrong outer argv")
    queue = load(cfg["bindings"]["queue_configuration"]["path"])
    require(queue["bindings"]["controller_identity"] == cfg["bindings"]["controller_identity"]
            and queue["bindings"]["campaign_manifest"] == cfg["bindings"]["campaign_manifest"]
            and queue["actual_GO"] == cfg["native_GO_path"], "Wrong fixed dependency queue")
    return cfg


def require_adoption(path, cfg):
    require(path is not None, "Separate actual ROOT recovery adoption required; no receiving/dispatch")
    adopted = load(path)
    flags = {"artifact_type": "ROOT_terminal_pointer_bounds_recovery_adoption", "issuer": "ROOT",
             "template_only": False, "fixture_only": False, "execution_authorized": True,
             "same_campaign_continuation": True, "original_max3_preserved": True,
             "no_changed_labels_or_first_bytes": True}
    require(all(adopted.get(k) == v for k, v in flags.items()), "Actual ROOT recovery adoption absent")
    expected = {"entrypoint": bind(__file__), "candidate_seal": bind(HERE / "seal.json"),
                "configuration": bind(HERE / "manifest.json"),
                "pointer_adapter_seal": cfg["bindings"]["pointer_adapter_seal"],
                "original_outer_entry": cfg["bindings"]["outer_entry"],
                "original_GO": cfg["bindings"]["original_GO"],
                "original_controller_start": cfg["bindings"]["controller_start"],
                "queue_configuration": cfg["bindings"]["queue_configuration"]}
    require(all(adopted.get(k) == v for k, v in expected.items()), "Adoption does not bind exact candidate/original chain")
    for key, expected_path in cfg["terminal_evidence_paths"].items():
        value = adopted.get(key)
        require(isinstance(value, dict) and value.get("path") == expected_path, "Missing/wrong terminal evidence: " + key)
        exact(value)
    output = Path(adopted.get("fresh_gate_output", "")).resolve()
    require(output.parent == HERE / "runtime-evidence" and output.suffix == ".json"
            and not output.exists(), "Require a fresh separately adopted gate evidence file")
    return adopted


def terminal_evidence(cfg, adopted):
    bindings = cfg["bindings"]
    start = load(bindings["controller_start"]["path"])
    terminal = load(adopted["parent_wait"]["path"])
    require(terminal.get("provenance") == "durable_supervisor_actual_Popen_wait"
            and terminal.get("actual_Popen_started") is True
            and terminal.get("actual_wait_returned") is True
            and terminal.get("actual_controller_terminal") is True
            and terminal.get("controller_pid") == 1130
            and type(terminal.get("returncode")) is int
            and terminal.get("returncode_status") == "observed_by_parent_wait"
            and terminal.get("launch_or_supervision_error") is None
            and utc(terminal["at_utc"]) >= utc(start["at_utc"]), "Original 1130 actual parent wait absent")
    for key in ("stdout", "stderr"):
        exact(terminal[key])
        require(Path(terminal[key]["path"]) == Path(adopted["parent_wait"]["path"]).parent / ("controller-" + key + ".txt"), "Parent wait output path differs")
    stdout = load(terminal["stdout"]["path"])
    epoch = Path(cfg["terminal_evidence_paths"]["H_result"]).parent
    require(stdout.get("all_terminal") is False and stdout.get("need_ROOT_attention") is True
            and stdout.get("controller_epoch") == str(epoch), "Parent stdout does not identify this failed epoch")
    result = load(adopted["controller_result"]["path"])
    h = load(adopted["H_result"]["path"])
    epoch_start = load(bindings["epoch_start"]["path"])
    require(epoch_start["GO"] == bindings["original_GO"]
            and epoch_start["campaign_manifest"] == bindings["campaign_manifest"]
            and utc(start["at_utc"]) <= utc(epoch_start["at_utc"]) <= utc(h["at_utc"]) <= utc(terminal["at_utc"]), "Epoch/time/GO chain differs")
    require(result.get("all_terminal") is False and result.get("need_ROOT_attention") is True
            and result.get("no_later_condition_started") is True
            and set(result.get("results", {})) == {"R1", "R2", "R3", "W", "H"}
            and h.get("all_terminal") is False and h["results"] == result["results"]["H"], "Expected original H failure result absent")
    allowed = {"selected", "already_selected", "technical_exhausted"}
    for condition, rows in result["results"].items():
        require(len(rows) == 87 and {r["batch_number"] for r in rows} == set(range(1, 88)), "Incomplete original batch grid")
        for row in rows:
            if condition == "H" and row["batch_number"] == 41:
                require(row.get("state") == "ROOT_execution_or_reception_error_no_retry"
                        and row.get("error") == {"type": "IndexError", "message": "list index out of range"}, "H0041 is not the exact diagnosed IndexError")
            else:
                require(row.get("state") in allowed, "Other original batch is not terminal")
    stopped = load(adopted["watcher_stopped"]["path"])
    watcher_start = load(bindings["watcher_start"]["path"])
    require(watcher_start["pid"] == 18140 and stopped.get("partial_outputs_preserved") is True
            and stopped.get("automatic_restart") is False and stopped.get("ROOT_attention_required") is True
            and isinstance(stopped.get("error"), dict)
            and utc(stopped["at_utc"]) >= utc(watcher_start["at_utc"]), "Original watcher stopping evidence absent")
    require(not Path(cfg["native_GO_path"]).exists(), "Native GO already exists; dependency ordering changed")
    return {"parent_wait": adopted["parent_wait"], "H_result": adopted["H_result"],
            "controller_result": adopted["controller_result"], "watcher_stopped": adopted["watcher_stopped"]}


def process_blockers(cfg, rows, self_pid=None):
    require(rows and len({r["pid"] for r in rows}) == len(rows), "Empty/ambiguous process observation")
    identity = load(cfg["bindings"]["controller_identity"]["path"])
    blockers = {}
    for row in rows:
        command = row["command"]
        old_controller = row["pid"] == identity["pid"] and row["lstart"] == identity["lstart"]
        old_watcher = row["pid"] == 18140 and row["lstart"] == cfg["watcher_birth"]
        scoped = ((cfg["isolated_cli_directory"] in command and (" exec " in command or "codex-code-mode-host" in command))
                  or (cfg["campaign_directory"] in command and (" exec " in command or "controller.py" in command or "receiver.py" in command))
                  or (cfg["bindings"]["outer_entry"]["path"] in command and "--original-entry" in command)
                  or (cfg["bindings"]["queue_supervisor"]["path"] in command and "--mode watch" in command)
                  or (str(HERE / "entry.py") in command and row["pid"] != self_pid))
        if old_controller or old_watcher or scoped:
            blockers[row["pid"]] = row
    while True:
        children = {r["pid"]: r for r in rows if r["ppid"] in blockers}
        if children.keys() <= blockers.keys():
            return list(blockers.values())
        blockers.update(children)


def fresh_quiet_gate(cfg):
    ps = module(cfg["bindings"]["process_helper"], "original_readonly_process_observer")
    observations = []
    first_completed = None
    for index in range(2):
        if index:
            time.sleep(max(0.0, 5.0 - (time.monotonic() - first_completed)))
        rows = ps.ps_rows()
        blockers = process_blockers(cfg, rows, os.getpid())
        require(not blockers, "Original controller/watcher or campaign isolated CLI/host still live")
        require(not Path(cfg["native_GO_path"]).exists(), "Native GO appeared before recovery")
        observations.append({"at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "rows": rows,
                             "blockers": [], "native_GO_exists": False})
        if index == 0:
            first_completed = time.monotonic()
    require(time.monotonic() - first_completed >= 5.0
            and (utc(observations[1]["at_utc"]) - utc(observations[0]["at_utc"])).total_seconds() >= 5.0,
            "Two fresh process observations must be at least five seconds apart")
    return observations


def install_runtime_hook(bootstrap, adapter):
    original_runtime = bootstrap.runtime
    def runtime():
        controller, runner, receiver = original_runtime()
        receiver.module = adapter.wrap_receiver_module_loader(receiver.module)
        return controller, runner, receiver
    bootstrap.runtime = runtime


def call_original_outer(cfg):
    sys.path.insert(0, cfg["capacity13_directory"])
    import bootstrap
    require(bind(bootstrap.__file__) == cfg["bindings"]["bootstrap"], "Unexpected bootstrap import")
    adapter = module(cfg["bindings"]["pointer_adapter"], "adopted_pointer_bounds_adapter")
    install_runtime_hook(bootstrap, adapter)
    outer = module(cfg["bindings"]["outer_entry"], "unchanged_outer_with_pointer_runtime_hook")
    sys.argv = cfg["original_outer_argv"][2:]
    outer.main()  # All original GO, PID, certificate, campaign, schema and max3 guards remain.


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("check", "run"), required=True)
    parser.add_argument("--adoption")
    args = parser.parse_args(argv)
    require(args.adoption is not None, "Separate actual ROOT recovery adoption required; no receiving/dispatch")
    cfg = frozen()
    adoption_binding = bind(args.adoption)
    adopted = require_adoption(args.adoption, cfg)
    evidence = terminal_evidence(cfg, adopted)
    observations = fresh_quiet_gate(cfg)
    exact(adoption_binding)
    if args.mode == "check":
        print(json.dumps({"candidate_only": True, "terminal_gates_passed": True,
                          "evidence": evidence, "observations": observations,
                          "receiving_calls": 0, "model_calls": 0}, ensure_ascii=False))
        return
    # Fresh evidence is written only after separate adoption and every terminal gate.
    target = Path(adopted["fresh_gate_output"])
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x") as stream:
        json.dump({"at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "adoption": bind(args.adoption), "evidence": evidence,
                   "observations": observations, "original_max3_preserved": True}, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    call_original_outer(cfg)


if __name__ == "__main__":
    main()
