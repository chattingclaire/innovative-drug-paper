from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path

from relation_coder import DIMENSIONS, MANUAL_SHA256, VERSION, code_unit


HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parent
INPUT_DIR = CAMPAIGN / "无答案输入"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def run_controls() -> int:
    control_path = HERE / "关系控制.json"
    payload = json.loads(control_path.read_text())
    assert payload["manual_sha256"] == MANUAL_SHA256
    rows = []
    failure_n = 0
    for case in payload["controls"]:
        result = code_unit({"current_text": case["current_text"], "contexts": case.get("contexts", [])})
        observed = {dimension: result["labels"][dimension] for dimension in case["expected"]}
        passed = observed == case["expected"]
        failure_n += int(not passed)
        rows.append({
            "id": case["id"],
            "expected": case["expected"],
            "observed": observed,
            "passed": passed,
            "reason": case["reason"],
            "evidence": result["evidence"],
            "exclusions": result["exclusions"],
        })
    report = {
        "kind": "predeclared_general_relation_controls",
        "version": VERSION,
        "manual_sha256": MANUAL_SHA256,
        "control_file": str(control_path),
        "control_file_sha256": sha(control_path),
        "coder_file_sha256": sha(HERE / "relation_coder.py"),
        "n": len(rows),
        "passed_n": len(rows) - failure_n,
        "failed_n": failure_n,
        "rows": rows,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    write_json(HERE / "控制执行结果.json", report)
    print(json.dumps({key: report[key] for key in ("n", "passed_n", "failed_n")}, ensure_ascii=False))
    return 1 if failure_n else 0


def load_units() -> tuple[list[dict], list[dict]]:
    units, bindings = [], []
    for path in sorted(INPUT_DIR.glob("批次*.json")):
        payload = json.loads(path.read_text())
        assert payload["manual_sha256"] == MANUAL_SHA256
        assert payload["manual_file"] == str((INPUT_DIR / "共用编码手册.md").resolve())
        units.extend(payload["units"])
        bindings.append({"path": str(path), "sha256": sha(path), "n": len(payload["units"])})
    assert len(units) == 40
    assert len({unit["material_id"] for unit in units}) == 40
    return units, bindings


def run_predictions() -> int:
    manual_path = INPUT_DIR / "共用编码手册.md"
    assert sha(manual_path) == MANUAL_SHA256
    control_report = json.loads((HERE / "控制执行结果.json").read_text())
    units, bindings = load_units()
    rows = []
    for unit in units:
        # material_id is copied to the output solely as an external join key.
        # code_unit receives no id, department, filename, source locator, label,
        # prior prediction, or human reason.
        prediction_input = {
            "current_text": unit["current_text"],
            "contexts": unit.get("contexts", []),
        }
        rows.append({
            "material_id": unit["material_id"],
            "prediction": code_unit(prediction_input),
        })
    output_path = HERE / "40条规则实际输出.jsonl"
    assert not output_path.exists(), "preserve the first actual 40-row execution"
    output_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    manifest = {
        "kind": "one_actual_40_unit_same_manual_development_candidate_execution",
        "version": VERSION,
        "manual_path": str(manual_path),
        "manual_sha256": sha(manual_path),
        "input_batches": bindings,
        "input_unit_count": len(units),
        "output_path": str(output_path),
        "output_sha256": sha(output_path),
        "coder_path": str(HERE / "relation_coder.py"),
        "coder_sha256": sha(HERE / "relation_coder.py"),
        "runner_sha256": sha(Path(__file__).resolve()),
        "control_result_sha256": sha(HERE / "控制执行结果.json"),
        "control_failures_preserved": control_report["failed_n"],
        "status_counts": {"completed": len(rows)},
        "label_positive_counts": {
            dimension: sum(row["prediction"]["labels"][dimension] for row in rows)
            for dimension in DIMENSIONS
        },
        "evidence_n": sum(len(row["prediction"]["evidence"]) for row in rows),
        "excluded_candidate_n": sum(len(row["prediction"]["exclusions"]) for row in rows),
        "prediction_fields_consumed": ["current_text", "contexts"],
        "reference_or_prior_prediction_loaded": False,
        "source_files_opened_for_prediction": False,
        "full_4480_run": False,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    write_json(HERE / "40条规则实际执行记录.json", manifest)
    print(json.dumps({
        "n": len(rows),
        "positive_counts": manifest["label_positive_counts"],
        "output_sha256": manifest["output_sha256"],
    }, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("controls", "predict"))
    args = parser.parse_args()
    return run_controls() if args.mode == "controls" else run_predictions()


if __name__ == "__main__":
    raise SystemExit(main())
