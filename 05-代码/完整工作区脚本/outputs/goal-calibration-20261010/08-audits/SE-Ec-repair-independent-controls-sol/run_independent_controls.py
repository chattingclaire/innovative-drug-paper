"""Execute presealed synthetic controls only; never load development labels."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import traceback

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANDIDATE = ROOT / "06-coding/rule-v20-SEEconomic-repair-sol"


def digest(path):
    data = Path(path).read_bytes()
    return {"path": str(Path(path).resolve()), "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data)}


def write_new(name, data):
    with (HERE / name).open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def main():
    preseal = json.loads((HERE / "pre-execution-seal.json").read_text())
    controls_path = HERE / "controls-fixed-before-execution.json"
    controls_binding = digest(controls_path)
    if controls_binding["sha256"] != preseal["controls_sha256"]:
        raise ValueError("presealed synthetic expectations changed")
    candidate_seal = Path(preseal["candidate_seal_path"])
    if digest(candidate_seal)["sha256"] != preseal["candidate_seal_sha256"]:
        raise ValueError("candidate seal changed")
    seal = json.loads(candidate_seal.read_text())
    verified = []
    for expected in [seal["manual"], *seal["code"]]:
        actual = digest(expected["path"])
        if actual["sha256"] != expected["sha256"] or actual["bytes"] != expected["bytes"]:
            raise ValueError("sealed input changed: " + expected["path"])
        verified.append(actual)
    sys.path.insert(0, str(CANDIDATE))
    import relations
    import dimensions
    import evidence

    controls = json.loads(controls_path.read_text())
    if controls["case_N"] != 20 or len(controls["cases"]) != 20:
        raise ValueError("expected exactly 20 independent controls")
    results = []
    for case in controls["cases"]:
        outcome = {"name": case["name"], "synthetic_only": True,
                   "expected": case["expected"], "manual_reason": case["manual_reason"],
                   "current_text": case["synthetic_input"]["text"],
                   "engine_called": False, "evidence_validation_passed": False}
        try:
            unit = case["synthetic_input"]
            view = relations.RelationView(unit)
            outcome["relation_traces"] = view.traces()
            outcome["material_requests"] = view.material_requests
            outcome["source_requests"] = view.source_requests
            outcome["engine_called"] = True
            decisions = dimensions.judge(view)
            outcome["decisions"] = decisions
            observed = {dim: decisions[dim]["value"] for dim in ("S", "E", "Ec")}
            outcome["observed"] = observed
            outcome["mismatches"] = [{"dimension": dim, "expected": case["expected"][dim],
                                      "observed": observed[dim]}
                                     for dim in ("S", "E", "Ec")
                                     if case["expected"][dim] != observed[dim]]
            evidence.validate_decisions(unit, decisions)
            outcome["evidence_validation_passed"] = True
            outcome["passed"] = not outcome["mismatches"]
        except Exception as exc:
            outcome["passed"] = False
            outcome["error"] = {"type": type(exc).__name__, "message": str(exc),
                                "traceback": traceback.format_exc()}
        results.append(outcome)
    summary = {"status": "independent_synthetic_control_execution_complete",
               "synthetic_only": True, "formal_records_used": 0, "human_reference_used": False,
               "candidate_mutated": False, "expected_changed_after_execution": False,
               "case_N": len(results), "passed_N": sum(x["passed"] for x in results),
               "failed_N": sum(not x["passed"] for x in results),
               "exception_N": sum("error" in x for x in results),
               "evidence_validation_passed_N": sum(x["evidence_validation_passed"] for x in results),
               "mismatch_N": sum(len(x.get("mismatches", [])) for x in results),
               "failed_names": [x["name"] for x in results if not x["passed"]],
               "inputs": {"controls": controls_binding, "candidate_seal": digest(candidate_seal),
                          "sealed_manual_and_code": verified},
               "executed_import_paths": {"relations": relations.__file__,
                                         "dimensions": dimensions.__file__, "evidence": evidence.__file__}}
    write_new("execution-results.json", {"summary": summary, "cases": results})
    with (HERE / "execution-results.jsonl").open("x", encoding="utf-8") as f:
        for outcome in results:
            f.write(json.dumps(outcome, ensure_ascii=False, allow_nan=False) + "\n")
    write_new("execution-summary.json", summary)
    print(json.dumps({k: summary[k] for k in
                     ("case_N", "passed_N", "failed_N", "exception_N",
                      "evidence_validation_passed_N", "mismatch_N", "failed_names")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
