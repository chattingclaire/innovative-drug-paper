from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path

from relation_coder_v03 import DIMENSIONS, MANUAL_SHA256, VERSION, code_unit


HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parent
INPUT_DIR = CAMPAIGN / "无答案输入"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    assert not path.exists(), f"preserve existing actual artifact: {path.name}"
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_control_cases() -> tuple[list[dict], list[dict]]:
    old_path = HERE / "关系控制_v02.json"
    new_path = HERE / "关系控制_v03.json"
    old = json.loads(old_path.read_text())
    new = json.loads(new_path.read_text())
    assert old["manual_sha256"] == new["manual_sha256"] == MANUAL_SHA256
    # F08 encoded the candidate-02 insurance shortcut. F09 encoded the prior
    # view that even an explicit shortage + priority programme enactment was
    # only purpose language. Candidate03 explicitly replaces both boundaries;
    # its F03_01..F03_05 controls supply the new positive and negative pairs.
    superseded = {"F08", "F09"}
    cases = [case for case in old["controls"] if case["id"] not in superseded] + new["controls"]
    assert len({case["id"] for case in cases}) == len(cases)
    bindings = [
        {"path": str(old_path), "sha256": sha(old_path), "excluded_superseded_case_ids": sorted(superseded)},
        {"path": str(new_path), "sha256": sha(new_path)},
    ]
    return cases, bindings


def run_controls() -> int:
    cases, bindings = load_control_cases()
    rows, failed = [], 0
    for case in cases:
        result = code_unit({"current_text": case["current_text"], "contexts": case.get("contexts", [])})
        observed = {dimension: result["labels"][dimension] for dimension in case["expected"]}
        passed = observed == case["expected"]
        failed += int(not passed)
        rows.append({
            "id": case["id"], "expected": case["expected"], "observed": observed,
            "passed": passed, "reason": case["reason"],
            "evidence": result["evidence"], "exclusions": result["exclusions"],
        })
    report = {
        "kind": "candidate03_predeclared_general_relation_controls",
        "version": VERSION,
        "manual_sha256": MANUAL_SHA256,
        "control_bindings": bindings,
        "coder_sha256": sha(HERE / "relation_coder_v03.py"),
        "preserved_base_coder_sha256": sha(HERE / "relation_coder_v02.py"),
        "n": len(rows), "passed_n": len(rows) - failed, "failed_n": failed,
        "rows": rows,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    write_json(HERE / f"控制执行结果-{VERSION}-final.json", report)
    print(json.dumps({"n": len(rows), "passed_n": len(rows) - failed, "failed_n": failed}, ensure_ascii=False))
    return 1 if failed else 0


def load_units() -> tuple[list[dict], list[dict]]:
    units, bindings = [], []
    for path in sorted(INPUT_DIR.glob("批次*.json")):
        payload = json.loads(path.read_text())
        assert payload["manual_sha256"] == MANUAL_SHA256
        units.extend(payload["units"])
        bindings.append({"path": str(path), "sha256": sha(path), "n": len(payload["units"])})
    assert len(units) == len({unit["material_id"] for unit in units}) == 40
    return units, bindings


def run_predictions() -> int:
    manual_path = INPUT_DIR / "共用编码手册.md"
    assert sha(manual_path) == MANUAL_SHA256
    controls_path = HERE / f"控制执行结果-{VERSION}-final.json"
    controls = json.loads(controls_path.read_text())
    units, bindings = load_units()
    rows = []
    for unit in units:
        prediction_input = {"current_text": unit["current_text"], "contexts": unit.get("contexts", [])}
        rows.append({"material_id": unit["material_id"], "prediction": code_unit(prediction_input)})
    output_path = HERE / f"40条规则实际输出-{VERSION}.jsonl"
    output_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    manifest = {
        "kind": "continued_development_execution_after_candidate02_evaluation_not_independent_validation",
        "version": VERSION,
        "manual_path": str(manual_path), "manual_sha256": sha(manual_path),
        "input_batches": bindings, "input_unit_count": len(units),
        "output_path": str(output_path), "output_sha256": sha(output_path),
        "coder_path": str(HERE / "relation_coder_v03.py"), "coder_sha256": sha(HERE / "relation_coder_v03.py"),
        "base_coder_path": str(HERE / "relation_coder_v02.py"), "base_coder_sha256": sha(HERE / "relation_coder_v02.py"),
        "runner_path": str(Path(__file__).resolve()), "runner_sha256": sha(Path(__file__).resolve()),
        "control_result_path": str(controls_path), "control_result_sha256": sha(controls_path),
        "preliminary_control_failure_path": str(HERE / f"控制执行结果-{VERSION}.json"),
        "preliminary_control_failure_sha256": sha(HERE / f"控制执行结果-{VERSION}.json"),
        "preliminary_control_failure_preserved": True,
        "control_failures_preserved": controls["failed_n"],
        "status_counts": {"completed": len(rows)},
        "label_positive_counts": {dimension: sum(row["prediction"]["labels"][dimension] for row in rows) for dimension in DIMENSIONS},
        "evidence_n": sum(len(row["prediction"]["evidence"]) for row in rows),
        "excluded_candidate_n": sum(len(row["prediction"]["exclusions"]) for row in rows),
        "prediction_fields_consumed": ["current_text", "contexts"],
        "reference_or_prior_prediction_loaded_during_prediction": False,
        "developer_had_seen_candidate02_evaluation_before_candidate03": True,
        "source_files_opened_for_prediction": False,
        "full_4480_run": False,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    write_json(HERE / f"40条规则实际执行记录-{VERSION}.json", manifest)
    print(json.dumps({"n": len(rows), "positive_counts": manifest["label_positive_counts"], "output_sha256": manifest["output_sha256"]}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("controls", "predict"))
    args = parser.parse_args()
    return run_controls() if args.mode == "controls" else run_predictions()


if __name__ == "__main__":
    raise SystemExit(main())
