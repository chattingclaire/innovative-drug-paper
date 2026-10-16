#!/usr/bin/env python3
"""Finite mechanical controls, original invalid byte candidates, and real CLI logs."""
import copy
import json
from pathlib import Path
import subprocess
import sys
from fractions import Fraction
sys.dont_write_bytecode = True
import batch_adapter as a

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "constructed-controls/inputs/mixed"
OUT = ROOT / "constructed-controls"


def write(path, value):
    data = value if isinstance(value, bytes) else a.canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def main():
    checks = []
    registry_bytes = (INPUT / "registry.json").read_bytes()
    reg = a.read_json_bytes(registry_bytes, "reg")
    ledger = a.read_json_bytes((INPUT / "ledger.json").read_bytes(), "ledger")
    reader = a.AssetReader(INPUT)
    meta = a.validate_registry(reg, reader)
    report, firsts, audit, _ = a.analyze(INPUT / "registry.json", INPUT / "ledger.json")
    prior = a.read_json_bytes((OUT / "prior-expectations.json").read_bytes(), "prior")

    def check(name, ok, actual):
        checks.append({"name": name, "passed": bool(ok), "actual": actual})

    s = report["paired_comparisons"]["R1/R2"]["dimensions"]["S"]
    for mode, prefix in (("raw", "R1_R2_S_"), ("weighted", "R1_R2_S_weighted_")):
        expected = prior[prefix + "raw_cells"] if mode == "raw" else prior[prefix + "cells"]
        check(mode + " S independent prior four cells", s[mode]["cells"] == expected, s[mode]["cells"])
        for field in ("Po", "Pe", "kappa"):
            key = prefix + field
            if key in prior:
                wanted = float(Fraction(str(prior[key])))
                actual = s[mode][field]
                check(mode + " S hand-checked " + field, abs(actual - wanted) < 1e-12, actual)
    triple = report["three_main_runs"]["five_dimension_vector"]
    check("C5 excludes genuine null only", triple["denominator_n"] == 4 and triple["weighted_denominator"] == 13, triple)
    check("production null stops on whole batch attempt two", firsts["runs"]["P"]["CONSTRUCTED-1"]["attempt_number"] == 2 and firsts["runs"]["P"]["CONSTRUCTED-1"]["labels"]["E"] is None, firsts["runs"]["P"]["CONSTRUCTED-1"])
    check("failed three-record batch has no salvaged first", all(firsts["runs"]["P"][f"CONSTRUCTED-{i}"] is None for i in (3,4,5)), audit["runs"]["P"][1])
    check("bad quote invalidates all first-batch members", audit["runs"]["H"][0]["attempts"][0]["technical_valid"] is False and audit["runs"]["H"][0]["attempts"][0]["record_checks"] == [], audit["runs"]["H"][0]["attempts"][0])
    check("shared batch first original ref and unique pointers", firsts["runs"]["R1"]["CONSTRUCTED-1"]["original_batch_response"] == firsts["runs"]["R1"]["CONSTRUCTED-2"]["original_batch_response"] and firsts["runs"]["R1"]["CONSTRUCTED-1"]["extraction_pointer"] == "/items/0" and firsts["runs"]["R1"]["CONSTRUCTED-2"]["extraction_pointer"] == "/items/1", {i: firsts["runs"]["R1"][i] for i in ("CONSTRUCTED-1", "CONSTRUCTED-2")})
    check("five sealed diagnostics unlock comparison", report["comparison_gate"]["unlocked"], report["comparison_gate"])
    run, bid = "R1", "TWO"
    binding = reg["conditions"][run]["batches"][bid]
    raw = reader.read(ledger["runs"][run]["batches"][0]["attempts"][0]["original_batch_response"], "baseline original")
    candidate = a.read_json_bytes(raw, "candidate")

    def raw_invalid(name, change=None, data=None):
        obj = copy.deepcopy(candidate)
        if change:
            change(obj)
        bad = data if data is not None else a.canonical(obj)
        write(OUT / "invalid-original-submissions" / (name + ".raw"), bad)
        parsed, result = a.qualify_whole_batch(bad, reg, meta, run, bid, binding)
        write(OUT / "invalid-original-submissions" / (name + ".check.json"), result)
        check(name, parsed is None and result["technical_valid"] is False and result["record_checks"] == [], result)

    raw_invalid("duplicate-output-id", lambda x: x["items"].__setitem__(1, copy.deepcopy(x["items"][0])))
    raw_invalid("missing-output-id", lambda x: x["items"].pop())
    raw_invalid("extra-output-id", lambda x: x["items"].append(copy.deepcopy(x["items"][0])))
    raw_invalid("reordered-output-id", lambda x: x["items"].reverse())
    raw_invalid("wrong-batch", lambda x: x.__setitem__("batch_id", "ABSENT"))
    raw_invalid("wrong-condition", lambda x: x.__setitem__("condition", "R2"))
    raw_invalid("wrong-record-content-sha", lambda x: x["items"][1].__setitem__("content_sha256", "0"*64))
    raw_invalid("missing-dimension", lambda x: x["items"][1]["labels"].pop("S"))
    raw_invalid("boolean-label", lambda x: x["items"][1]["labels"].__setitem__("S", True))
    raw_invalid("float-label", lambda x: x["items"][1]["labels"].__setitem__("S", 1.0))
    raw_invalid("unknown-record-field", lambda x: x["items"][0].__setitem__("unknown", 1))
    raw_invalid("bad-current-continuous-span", lambda x: x["items"][1]["evidence"]["S"]["current_span"].__setitem__("end", 1))
    raw_invalid("unknown-context-id", lambda x: x["items"][1]["evidence"]["S"]["contexts_used"][0].__setitem__("context_id", "MISSING"))
    raw_invalid("unknown-context-field", lambda x: x["items"][1]["evidence"]["S"]["contexts_used"][0].__setitem__("field_path", "labels.S"))
    raw_invalid("bad-context-continuous-quote", lambda x: x["items"][0]["evidence"]["S"]["contexts_used"][0].__setitem__("quote", "不存在"))
    raw_invalid("fake-asset-reference", lambda x: x["items"][0]["evidence"]["S"]["image_sources_used"].append("fake-asset"))
    raw_invalid("null-without-material-request", lambda x: x["items"][0]["labels"].__setitem__("S", None))
    raw_invalid("malformed", data=b'{"items":')
    raw_invalid("duplicate-json-key", data=raw.replace(b'"batch_id":"TWO"', b'"batch_id":"TWO","batch_id":"TWO"'))
    raw_invalid("nonfinite-json", data=raw.replace(b'"S":0', b'"S":NaN', 1))
    raw_invalid("non-utf8", data=b'\xff\xfe')

    def reseal(stream, status="condition_terminal_sealed"):
        stream["seal"]["status"] = status
        stream["seal"]["content_sha256"] = a.object_sha({k:v for k,v in stream.items() if k != "seal"})

    def ledger_reject(name, change):
        mutated = copy.deepcopy(ledger)
        change(mutated)
        for stream in mutated["runs"].values():
            if isinstance(stream, dict) and "seal" in stream:
                reseal(stream, stream["seal"]["status"])
        write(OUT / "rejected-ledgers" / (name + ".json"), mutated)
        try:
            a.validate_ledger(reg, mutated, meta, a.AssetReader(INPUT), registry_bytes)
        except (a.ContractError, ValueError, KeyError, TypeError) as exc:
            check(name, True, str(exc))
        else:
            check(name, False, "unexpected acceptance")

    ledger_reject("retry-after-valid-semantic-null", lambda x: x["runs"]["P"]["batches"][0]["attempts"].append(copy.deepcopy(x["runs"]["P"]["batches"][0]["attempts"][-1])))
    ledger_reject("four-attempts", lambda x: x["runs"]["P"]["batches"][1]["attempts"].append(copy.deepcopy(x["runs"]["P"]["batches"][1]["attempts"][-1])))
    ledger_reject("missing-ledger-batch", lambda x: x["runs"]["R2"]["batches"].pop())
    ledger_reject("duplicate-ledger-batch", lambda x: x["runs"]["R2"]["batches"].__setitem__(1, copy.deepcopy(x["runs"]["R2"]["batches"][0])))
    ledger_reject("first-from-diagnostic-into-production", lambda x: x["runs"]["P"]["batches"][0].__setitem__("first", copy.deepcopy(x["runs"]["R1"]["batches"][0]["first"])))
    ledger_reject("first-later-candidate", lambda x: x["runs"]["R1"]["batches"][0]["first"].__setitem__("attempt_number", 2))
    ledger_reject("retry-request-sha-change", lambda x: x["runs"]["H"]["batches"][0]["attempts"][1].__setitem__("exact_request_sha256", "0"*64))
    ledger_reject("record-context-disguised-as-batch", lambda x: x["runs"]["R1"]["batches"][0]["attempts"][0]["dispatch"].__setitem__("context_unit", "record"))
    ledger_reject("reused-logical-context", lambda x: x["runs"]["R2"]["batches"][0]["attempts"][0]["dispatch"].__setitem__("logical_context_id", x["runs"]["R1"]["batches"][0]["attempts"][0]["dispatch"]["logical_context_id"]))
    ledger_reject("feedback-user-message", lambda x: x["runs"]["R1"]["batches"][0]["attempts"][0]["dispatch"]["additional_user_messages"].append("try a different label"))
    ledger_reject("known-input-truncation", lambda x: x["runs"]["R1"]["batches"][0]["attempts"][0]["delivery"].__setitem__("known_input_truncation", True))
    ledger_reject("fake-provider-telemetry", lambda x: x["runs"]["R1"]["batches"][0]["attempts"][0]["provider_receipt"].__setitem__("returned_model", "claimed-from-interface"))
    ledger_reject("incomplete-declared-terminal", lambda x: (x["runs"]["H"]["batches"][0].__setitem__("attempts", x["runs"]["H"]["batches"][0]["attempts"][:1]), x["runs"]["H"]["batches"][0].__setitem__("first", None)))

    # A partial technical snapshot may be audited but cannot unlock comparisons.
    snapshot = copy.deepcopy(ledger)
    stream = snapshot["runs"]["H"]
    stream["batches"][0]["attempts"] = stream["batches"][0]["attempts"][:1]
    stream["batches"][0]["first"] = None
    reseal(stream, "snapshot_not_terminal")
    snapshot_path = INPUT / "snapshot-ledger.json"
    write(snapshot_path, snapshot)
    snapshot_report, _, snapshot_audit, _ = a.analyze(INPUT / "registry.json", snapshot_path)
    check("unsealed snapshot locks all comparisons", snapshot_report["comparison_gate"]["unlocked"] is False and snapshot_report["paired_comparisons"] == {} and snapshot_report["three_main_runs"] is None, snapshot_report["comparison_gate"])
    check("single failure has two retry slots and no salvage", snapshot_audit["runs"]["H"][0]["remaining_retry_slots_if_unresolved"] == 2 and all(snapshot_report["per_record_states"]["H"][i]["labels"] is None for i in ("CONSTRUCTED-1", "CONSTRUCTED-2")), snapshot_audit["runs"]["H"][0])
    schema = reader.json(reg["source_qualification"]["source_schema"], "schema")
    original_packet = meta["packets"]["CONSTRUCTED-1"]
    for name, change in (("source-unknown-old-result-field", lambda x: x.__setitem__("old_result_metadata", 1)), ("nested-unknown-source-field", lambda x: x["contexts"][0].__setitem__("unexpected", {})), ("wrong-source-id", lambda x: x.__setitem__("source_id", "SYNTHETIC-SOURCE-999")), ("wrong-source-output-id", lambda x: x.__setitem__("blind_id", "A-999999")), ("dangling-source-context", lambda x: x["contexts"][0].__setitem__("parent_id", "MISSING"))):
        packet = copy.deepcopy(original_packet)
        change(packet)
        unsigned = copy.deepcopy(packet); unsigned.pop("content_sha256")
        packet["content_sha256"] = a.object_sha(unsigned)
        record = copy.deepcopy(meta["records"]["CONSTRUCTED-1"])
        record["source_content_sha256"] = packet["content_sha256"]
        record["ctx_binding_sha256"] = a.object_sha(packet["contexts"])
        write(OUT / "rejected-sources" / (name + ".json"), packet)
        try:
            a.toy_qualification.adapt_source(packet, record, schema)
        except ValueError as exc:
            check(name, True, str(exc))
        else:
            check(name, False, "unexpected opaque qualification")
    production = copy.deepcopy(reg)
    production["data_mode"] = "prospective_registered_inputs"
    try:
        a.qualification_binding(production, a.AssetReader(INPUT))
    except a.ContractError as exc:
        check("toy-cannot-certify-production", True, str(exc))
    else:
        check("toy-cannot-certify-production", False, "unexpected production acceptance")
    command = [sys.executable, "-B", str(ROOT / "batch_adapter.py"), "analyze", "--registry", str(INPUT / "registry.json"), "--ledger", str(INPUT / "ledger.json"), "--out-dir", str(OUT / "results/cli-replay")]
    completed = subprocess.run(command, capture_output=True, text=True)
    write(ROOT / "verification/actual-cli.json", {"argv": command, "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    check("actual CLI executes successfully", completed.returncode == 0, completed.returncode)
    replay = OUT / "results/cli-replay"
    check("CLI deterministically reproduces report firsts audit", all((replay/name).read_bytes() == (OUT / "results/mixed" / name).read_bytes() for name in ("report.json", "firsts.json", "audit-ledger.json", "report.md")), "four result files")
    overwrite = subprocess.run(command, capture_output=True, text=True)
    write(ROOT / "verification/actual-cli-overwrite-rejection.json", {"argv": command, "exit_code": overwrite.returncode, "stdout": overwrite.stdout, "stderr": overwrite.stderr})
    check("nonempty sealed output rejected", overwrite.returncode == 2 and "cannot be overwritten" in overwrite.stderr, overwrite.stderr)
    for seal_path in (OUT / "results/mixed/seal.json", replay / "seal.json"):
        seal = a.read_json_bytes(seal_path.read_bytes(), "seal")
        ok = all(Path(x["path"]).stat().st_size == x["bytes"] and a.digest(Path(x["path"]).read_bytes()) == x["sha256"] for x in seal["inputs"] + seal["code"])
        ok = ok and all((seal_path.parent / x["path"]).stat().st_size == x["bytes"] and a.digest((seal_path.parent / x["path"]).read_bytes()) == x["sha256"] for x in seal["outputs"])
        check("per-analysis seal exact bytes " + seal_path.parent.name, ok, {"input_n": len(seal["inputs"]), "output_n": len(seal["outputs"])})
    write(OUT / "controls.json", {"scope": "finite synthetic controls, not independent reviewer or real labels", "total": len(checks), "passed": sum(x["passed"] for x in checks), "checks": checks})
    print(json.dumps({"total": len(checks), "passed": sum(x["passed"] for x in checks)}))
    return 0 if all(x["passed"] for x in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
