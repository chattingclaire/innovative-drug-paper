"""Candidate only: same campaign/GO, identity-aware historical PID closure."""
import argparse
import contextvars
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
TZ = ZoneInfo("Asia/Shanghai")


def load(path):
    return json.loads(Path(path).read_bytes())


def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def exact(b):
    if bind(b["path"]) != {k: b[k] for k in ("path", "bytes", "sha256")}:
        raise ValueError("Changed frozen binding: " + b["path"])


def utc(value):
    value = dt.datetime.fromisoformat(value)
    if value.tzinfo is None:
        raise ValueError("Timezone absent from actual timestamp")
    return value.astimezone(dt.timezone.utc)


def birth(row):
    return dt.datetime.strptime(row["lstart"], "%a %b %d %H:%M:%S %Y").replace(tzinfo=TZ).astimezone(dt.timezone.utc)


def ps_rows():
    # Read-only observation; no kill(0), signals, process launch or cleanup.
    offset = subprocess.run(["/bin/date", "+%z"], capture_output=True, text=True, check=True).stdout.strip()
    if offset != "+0800":
        raise ValueError("Unexpected local ps timezone; identity unknown")
    raw = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,pgid=,stat=,lstart=,command="], capture_output=True, text=True, check=True).stdout
    rows = []
    for line in raw.splitlines():
        m = re.fullmatch(r"\s*(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(.{24})\s+(.*)", line)
        if not m:
            raise ValueError("Unparsed actual ps line; cannot claim absence")
        pid, ppid, pgid, stat, started, command = m.groups()
        rows.append({"pid": int(pid), "ppid": int(ppid), "pgid": int(pgid), "stat": stat, "lstart": started, "command": command})
    if not rows or len({r["pid"] for r in rows}) != len(rows):
        raise ValueError("Empty/ambiguous process observation")
    return rows


def same_old(row, identity):
    return row["pid"] == identity["pid"] and row["lstart"] == identity["lstart"]


def historical_closed(pid, rows, old_identities, certificate_at, new_owned):
    """True means the certified historical process is closed, not numeric PID dead."""
    if type(pid) is not int or pid <= 0:
        raise ValueError("Invalid historical production PID")
    matches = [r for r in rows if r["pid"] == pid]
    if not matches:
        return True
    if len(matches) != 1:
        return False
    row = matches[0]
    if any(same_old(row, old) for old in old_identities):
        return False  # An original PID/birth identity is still present.
    try:
        if birth(row) <= utc(certificate_at):
            return False
    except (ValueError, KeyError):
        return False
    # A later birth alone is insufficient: genuine same-campaign lineage required.
    return pid in new_owned


def expected_argv(d, item):
    capture = str(Path(item["output_directory"]) / "ROOT-cli-final-message.txt")
    return [d["cli_launcher"], "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral", "--json", "--color", "never", "-C", item["working_directory"], "--model", "gpt-6.1-sol", "-c", 'model_reasoning_effort="ultra"', "-c", 'approval_policy="never"', "--sandbox", "read-only", "-c", "features.multi_agent=false", "-c", "features.memories=false", "-c", 'web_search="disabled"', "-c", "project_doc_max_bytes=0", "--output-last-message", capture, "-"]


def campaign_owned(rows, d, go_binding, certificate_at):
    """Only actual Popen roots and their currently witnessed descendants qualify."""
    indexed = {r["pid"]: r for r in rows}
    roots = set()
    cert_time = utc(certificate_at)
    for item in d["routes"]:
        argv = expected_argv(d, item)
        tail = " " + " ".join(argv[1:])
        if not any(r["command"].endswith(tail) for r in rows):
            continue
        slot = Path(item["output_directory"])
        start_path = slot / "ROOT-actual-process-start.json"
        if not start_path.exists():
            continue  # No retained genuine launch identity, no alias.
        actual = load(start_path)
        exact(actual["start"])
        dispatched = load(actual["start"]["path"])
        if (actual.get("actual_CLI_process_started") is not True
                or dispatched.get("GO") != go_binding or dispatched.get("argv") != argv
                or dispatched.get("assignment") != item["assignment"]
                or dispatched.get("stdin") != item["fixed_request"]
                or dispatched.get("working_directory") != item["working_directory"]
                or tuple(dispatched.get(k) for k in ("condition", "batch_number", "attempt_number")) != tuple(item[k] for k in ("condition", "batch_number", "attempt_number"))
                or utc(actual["at_utc"]) <= cert_time):
            raise ValueError("Unbound actual same-campaign CLI identity")
        root = indexed.get(actual["pid"])
        full_argv = " ".join(argv)
        if root is None:
            continue  # Orphan/vanished ancestry is unknown, never inferred.
        prefix = root["command"].removesuffix(full_argv)
        if (not root["command"].endswith(full_argv)
                or not re.fullmatch(r"(?:[^\s]+/)?node\s+", prefix)
                or birth(root) < utc(actual["at_utc"]).replace(microsecond=0)):
            continue
        roots.add(root["pid"])
    owned = set(roots)
    isolated = str(Path(d["cli_launcher"]).parents[2]) + "/"
    while True:
        more = {r["pid"] for r in rows if r["ppid"] in owned and birth(r) > cert_time
                and (r["command"].startswith(isolated) or r["command"].startswith("node " + isolated))}
        if more <= owned:
            return owned
        owned |= more


def frozen_context():
    manifest = load(HERE / "manifest.json")
    for b in manifest["immutable_input_bindings"]:
        exact(b)
    cert = load(manifest["production_terminal_certificate"]["path"])
    proof = load(cert["terminal_evidence_bindings"][0]["path"])
    old = load(proof["new13_terminal_observation"]["path"])
    if not (cert["all_child_processes_terminal"] is True and cert["active_model_process_N"] == 0
            and proof["all_primary_and_recovery_terminal"] is True and old["owned_processes"] == []
            and old["new_controller_and_all_known_descendants_absent"] is True):
        raise ValueError("Real historical terminal evidence absent")
    return manifest, cert, old["known_owned_process_identity_registry"]


def install(common, go_path, cert, old_identities):
    original_validate = common.validate_GO
    context = contextvars.ContextVar("historical_PID_observation")

    def revised_dead(pid):
        rows, new_owned = context.get()
        return historical_closed(pid, rows, old_identities, cert["at_utc"], new_owned)

    def revised_validate(run, d, path):
        if bind(path) != bind(go_path):
            raise ValueError("Different GO; no same-campaign continuation")
        rows = ps_rows()
        owned = campaign_owned(rows, d, bind(go_path), cert["at_utc"])
        token = context.set((rows, owned))
        try:
            return original_validate(run, d, path)  # All original GO checks remain.
        finally:
            context.reset(token)

    common.pid_dead = revised_dead  # Only capacity13's historical-PID predicate.
    common.validate_GO = revised_validate  # Fresh single observation per thread/call.


def require_adoption(path, go_path, manifest):
    adopted = load(path)
    if not (adopted.get("issuer") == "ROOT" and adopted.get("template_only") is False
            and adopted.get("compatibility_adopted") is True
            and adopted.get("same_campaign_continuation") is True):
        raise ValueError("Actual ROOT compatibility adoption absent; no dispatch")
    if (adopted.get("candidate_seal") != bind(HERE / "seal.json")
            or adopted.get("entrypoint") != bind(__file__)
            or adopted.get("unchanged_actual_GO") != bind(go_path)
            or adopted.get("unchanged_actual_GO") != manifest["actual_GO"]):
        raise ValueError("ROOT adoption does not bind this candidate/same GO")
    b = adopted["prior_controller_terminal_evidence"]
    exact(b)
    terminal = load(b["path"])
    if not (terminal.get("actual_session") == 86083 and terminal.get("actual_controller_terminal") is True
            and terminal.get("all_started_CLI_children_and_hosts_terminal") is True
            and terminal.get("actual_exit_observed") is True
            and type(terminal.get("actual_returncode")) is int
            and terminal.get("live_owned_processes") == []):
        raise ValueError("Real previous controller/child terminal evidence absent")
    identity = terminal["prior_controller_identity"]
    for r in ps_rows():
        if same_old(r, identity):
            raise ValueError("Previous controller identity still present")
        if (manifest["campaign_directory"] in r["command"] and (" exec " in r["command"] or "successor_entry.py" in r["command"])):
            raise ValueError("Old campaign/controller child still active")
        if manifest["isolated_cli_directory"] in r["command"] and (" exec " in r["command"] or "codex-code-mode-host" in r["command"]):
            raise ValueError("Isolated CLI/host still active before continuation")
    return adopted


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("preflight", "run"), required=True)
    p.add_argument("--target", choices=("stability13",), default="stability13")
    p.add_argument("--go")
    p.add_argument("--adoption")
    args = p.parse_args()
    manifest, cert, old = frozen_context()
    if args.mode == "preflight":
        print(json.dumps({"state": "candidate_no_execution_authority", "model_calls": 0, "receiver_calls": 0, "classifier_calls": 0, "requires_real_prior_terminal_and_ROOT_adoption": True}))
        return
    if not args.adoption or not args.go:
        raise ValueError("Actual ROOT adoption + same actual GO required; no dispatch")
    if bind(args.go) != manifest["actual_GO"]:
        raise ValueError("GO changed")
    for b in load(HERE / "seal.json")["outputs"]:
        exact(b)
    require_adoption(args.adoption, args.go, manifest)
    sys.path.insert(0, manifest["capacity13_directory"])
    import capacity13_common as common
    install(common, args.go, cert, old)
    original = manifest["unchanged_successor_entrypoint"]
    sys.path.insert(0, str(Path(original["path"]).parent))
    spec = importlib.util.spec_from_file_location("unchanged_successor_for_PID_continuation", original["path"])
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    entry.c.assert_preparation()
    entry.run_stability(args.go)  # Same original bootstrap/campaign/GO/slots/budget.


if __name__ == "__main__":
    main()
