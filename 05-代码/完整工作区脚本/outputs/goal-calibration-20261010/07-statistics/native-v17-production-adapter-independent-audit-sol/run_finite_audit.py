#!/usr/bin/env python3
"""Finite audit: reuse the author's two invented records; no real actor calls."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent / "native-v17-production-adapter-sol"
sys.path.insert(0, str(CANDIDATE))
import v17_adapter as adapter
import build_controls as author_controls


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else adapter.canonical(value) + b"\n"
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": str(path), "bytes": len(raw), "sha256": adapter.digest(raw)}


def reseal_ledger(ledger):
    for stream in ledger["runs"].values():
        stream["seal"]["content_sha256"] = adapter.object_sha({"batches": stream["batches"]})


def run_cli(name, inputs, compare):
    directory = HERE / "actual-runs" / name
    directory.mkdir(parents=True, exist_ok=False)
    out = directory / "result.json"
    command = [sys.executable, "-B", str(CANDIDATE / "v17_adapter.py"),
               "--plan", str(inputs / "plan.json"), "--ledger", str(inputs / "ledger.json"),
               "--out", str(out)] + (["--compare"] if compare else [])
    process = subprocess.run(command, capture_output=True, text=True)
    record = {"case": name, "command": command, "exit_code": process.returncode,
              "stdout": process.stdout, "stderr": process.stderr,
              "result_exists": out.exists(), "actual_model_actor_calls": 0}
    save(directory / "cli-record.json", record)
    result = json.loads(out.read_bytes()) if out.exists() else None
    return record, result


def check_whole_failure(result, exhausted=False):
    rows = result["per_record_states"]["R1"]
    assert len(rows) == 2
    assert all(row["state"] == "technical_failure" and row["labels"] is None and row["first"] is None for row in rows.values())
    assert all(check["record_checks"] == [] for check in result["audit"]["R1"][0]["attempts"])
    assert all(row["failure_exhausted_three_attempts"] is exhausted for row in rows.values())


def check_origins(result, attempt):
    origins = list(result["origins"]["R1"].values())
    assert [row["extraction_pointer"] for row in origins] == ["/records/0", "/records/1"]
    assert origins[0]["raw_response"] == origins[1]["raw_response"]
    assert all(row["attempt_number"] == attempt and row["derived_record_is_original_response"] is False for row in origins)
    assert result["per_record_states"]["R1"]["INVENTED-2"]["state"] == "valid_semantic_null"


def main():
    save(HERE / "expectations-before-execution.json", {
        "scope": "14 author cases rerun plus 3 independent boundaries, always the same two wholly invented materials",
        "author_cases": author_controls.CASES,
        "independent_boundaries": {
            "equivalent_original_bytes": "same parsed object, different full raw bytes; exact new bytes retained with fixed pointers",
            "ctx_binding_mismatch": "reject frozen CTX relationship hash mismatch before member extraction",
            "zero_call_precheck_terminal": "explicit H precheck block can close zero-call terminal; H members stay uncalled and excluded"
        },
        "real_inputs_or_actors": False})
    results = []
    rejected = {"legal_null_retry", "four_attempts", "later_first_claim", "production_without_adoption", "unclosed_source_profile"}
    invalid = {"whole_batch_invalid", "illegal_bool", "illegal_float", "supplemental_bad_quote", "unqualified_pointer"}
    for case in author_controls.CASES:
        inputs = CANDIDATE / "constructed-controls-r04-final" / case / "inputs"
        compare = case not in invalid and case != "early_compare"
        record, result = run_cli("author-" + case, inputs, compare)
        assert record["exit_code"] == (2 if case in rejected else 0), record
        if case in rejected:
            assert result is None
        elif case in invalid:
            check_whole_failure(result)
            assert result["comparison_gate"]["unlocked"] is False
            assert result["paired_comparisons"] == {} and result["three_main_runs"] is None
            assert all(r["remaining_retry_slots_if_unresolved"] == 2 for r in result["per_record_states"]["R1"].values())
        elif case == "three_failed":
            check_whole_failure(result, exhausted=True)
            assert result["comparison_gate"]["unlocked"] is True
        elif case in {"normal", "earliest_valid_second"}:
            check_origins(result, 2 if case == "earliest_valid_second" else 1)
            assert result["comparison_gate"]["unlocked"] and len(result["paired_comparisons"]) == 5
            if case == "normal":
                math = result["paired_comparisons"]["R1/R2"]["dimensions"]["S"]["raw"]
                assert math["cells"] == {"n00": 1, "n01": 0, "n10": 1, "n11": 0}
                assert math["Po"] == .5 and math["Pe"] == .5 and math["kappa"] == 0
        elif case == "early_compare":
            assert result["comparison_gate"]["unlocked"] is False
            assert result["paired_comparisons"] == {} and result["three_main_runs"] is None
            extra, forbidden = run_cli("author-early-compare-rejection", inputs, True)
            assert extra["exit_code"] == 2 and forbidden is None
        results.append({"case": case, "kind": "rerun_author_case", "passed": True, "cli_exit_code": record["exit_code"]})

    base = HERE / "independent-boundaries"
    base.mkdir(exist_ok=False)
    for case in ("equivalent_original_bytes", "ctx_binding_mismatch", "zero_call_precheck_terminal"):
        fixture = author_controls.build_case(base, case)
        inputs = fixture / "inputs"
        ledger = json.loads((inputs / "ledger.json").read_bytes())
        save(fixture / "ledger-before-mutation.json", ledger)
        if case == "equivalent_original_bytes":
            attempt = ledger["runs"]["R1"]["batches"][0]["attempts"][0]
            path = Path(attempt["original"]["path"])
            previous = path.read_bytes()
            save(fixture / "original-before-reencoding.utf8", previous)
            obj = json.loads(previous)
            changed = json.dumps(obj, ensure_ascii=False, indent=2).encode() + b"\n"
            assert changed != previous
            path.write_bytes(changed)
            attempt["original"] = author_controls.ref(path)
            first = ledger["runs"]["R1"]["batches"][0]["first"]
            first["original"] = attempt["original"]
            assert first["parsed_batch_sha256"] == adapter.object_sha(obj)
        elif case == "ctx_binding_mismatch":
            source_path = inputs / "common-source-contract.json"
            save(fixture / "source-contract-before-mutation.json", source_path.read_bytes())
            source = json.loads(source_path.read_bytes())
            source["records"][1]["ctx_binding_sha256"] = "0" * 64
            source_path.write_bytes(adapter.canonical(source) + b"\n")
            plan_path = inputs / "plan.json"
            plan = json.loads(plan_path.read_bytes())
            save(fixture / "plan-before-mutation.json", plan)
            plan["source_contract"] = author_controls.ref(source_path)
            plan.pop("plan_content_sha256")
            plan["plan_content_sha256"] = adapter.object_sha(plan)
            plan_path.write_bytes(adapter.canonical(plan) + b"\n")
            ledger["plan_file_sha256"] = adapter.digest(plan_path.read_bytes())
        else:
            stream = ledger["runs"]["H"]
            row = stream["batches"][0]
            row["attempts"], row["first"] = [], None
            row["not_called"] = {"state": "precheck_blocked", "reason": "self-invented prerequisite block, no actual actor call", "terminal_without_attempt": True}
            stream["seal"]["status"] = "condition_terminal_sealed"
        reseal_ledger(ledger)
        (inputs / "ledger.json").write_bytes(adapter.canonical(ledger) + b"\n")
        record, result = run_cli("independent-" + case, inputs, True)
        if case == "ctx_binding_mismatch":
            assert record["exit_code"] == 2 and result is None
            assert "CTX relationship binding" in record["stderr"]
        else:
            assert record["exit_code"] == 0
            if case == "equivalent_original_bytes":
                check_origins(result, 1)
                assert result["origins"]["R1"]["INVENTED-1"]["raw_response"] == author_controls.ref(path)
                assert result["origins"]["R1"]["INVENTED-1"]["parsed_batch_sha256"] == adapter.object_sha(obj)
            else:
                assert result["comparison_gate"]["unlocked"]
                assert result["audit"]["H"][0]["recorded_whole_batch_attempt_n"] == 0
                assert all(r["state"] == "not_called" and r["labels"] is None and r["first"] is None for r in result["per_record_states"]["H"].values())
                assert result["paired_comparisons"]["H/R1"]["dimensions"]["S"]["domain"]["joint_comparable_n"] == 0
        results.append({"case": case, "kind": "independent_boundary_using_author_materials", "passed": True, "cli_exit_code": record["exit_code"]})

    class TraceReader(adapter.BoundReader):
        latest = None
        def __init__(self):
            super().__init__()
            TraceReader.latest = self
    old = adapter.BoundReader
    adapter.BoundReader = TraceReader
    try:
        inputs = CANDIDATE / "constructed-controls-r04-final/production_without_adoption/inputs"
        try:
            adapter.analyze(inputs / "plan.json", inputs / "ledger.json", True)
        except adapter.ContractError as exc:
            assert "production adoption" in str(exc)
            assert TraceReader.latest.seen == {}
            save(HERE / "production-pre-source-read-check.json", {"rejected": True, "reason": str(exc), "bound_source_or_output_files_read": [], "actual_model_actor_calls": 0})
        else:
            raise AssertionError("missing production adoption accepted")
    finally:
        adapter.BoundReader = old
    save(HERE / "actual-finite-results.json", {"case_N": len(results), "passed_case_N": sum(r["passed"] for r in results),
        "author_rerun_case_N": 14, "independent_boundary_case_N": 3, "CLI_invocation_N": 18,
        "results": results, "production_missing_adoption_rejected_before_bound_source_or_output_read": True,
        "actual_model_actor_calls": 0, "real_policy_or_results_read": False})
    print(json.dumps({"passed_case_N": len(results), "case_N": len(results), "CLI_invocation_N": 18, "real_model_actor_calls": 0}))


if __name__ == "__main__":
    main()
