#!/usr/bin/env python3
"""Run controls 03/08/09 once through the frozen pre-repair full entry."""

import hashlib
import json
import sys
import time
import traceback
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
INPUT = PARENT / "完整入口输入10.jsonl"
CONTROLS = PARENT / "构造控制.jsonl"
RUNTIME = (HERE.parents[3] / "自动规则编码" / "测量与语义统一" / "runtime").resolve()
OUTPUT = HERE / "旧基线三条输出.jsonl"
FREEZE = HERE / "旧基线三条执行冻结.json"
REPORT = HERE / "旧基线三条执行报告.json"
TARGETS = ("SYNCTRL-03", "SYNCTRL-08", "SYNCTRL-09")
INPUT_SHA256 = "eb6650ea3cff400c725b157b807abf6a19ef425acc469b2519649c605ca1b031"
CONTROLS_SHA256 = "05c360a4f3e7c9d5656d4b2d61d24c228a514e8564214e95856ccecf54ef4fdd"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(root):
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"}


def tree_sha(files):
    return hashlib.sha256(json.dumps(files, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def main():
    assert sha(INPUT) == INPUT_SHA256
    assert not any(path.exists() for path in (OUTPUT, FREEZE, REPORT)), "one run; no overwrite"
    rows = [json.loads(line) for line in INPUT.read_text().splitlines() if line.strip()]
    rows = [row for row in rows if row["id"] in TARGETS]
    assert tuple(row["id"] for row in rows) == TARGETS
    assert all("expected_labels" not in json.dumps(row, ensure_ascii=False) for row in rows)
    before = manifest(RUNTIME)
    sys.path.insert(0, str(RUNTIME))
    import policy_coding_v27 as coder
    assert Path(coder.__file__).resolve().parent == RUNTIME
    freeze = {
        "kind": "three_synthetic_controls_old_baseline_full_entry_diagnostic",
        "targets": list(TARGETS),
        "input_path": str(INPUT.resolve()),
        "input_sha256": sha(INPUT),
        "runtime_path": str(RUNTIME),
        "runtime_version": coder.VERSION,
        "runtime_manifest_before": before,
        "runtime_tree_sha256_before": tree_sha(before),
        "expected_labels_absent_from_encoder_input": True,
        "synthetic_not_policy": True,
        "not_human_validation": True,
    }
    FREEZE.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n")
    started = time.monotonic()
    results = []
    with OUTPUT.open("w") as handle:
        for row in rows:
            try:
                result = coder.code_unit(row["input"], source_adapter=True, substantive_rules=True)
                out = {"id": row["id"], "status": "completed", "result": result}
            except Exception as error:
                out = {"id": row["id"], "status": "failed",
                       "error_type": type(error).__name__, "error": str(error),
                       "traceback": traceback.format_exc()}
            results.append(out)
            handle.write(json.dumps(out, ensure_ascii=False) + "\n")
            handle.flush()
            print(row["id"], out["status"], flush=True)
    # Expected judgments are first opened after all encoder calls.
    assert sha(CONTROLS) == CONTROLS_SHA256
    expected = {row["id"]: row["expected_labels"] for row in
                (json.loads(line) for line in CONTROLS.read_text().splitlines() if line.strip())}
    comparisons = []
    for out in results:
        labels = out.get("result", {}).get("labels")
        comparisons.append({"id": out["id"], "expected_labels": expected[out["id"]],
                            "actual_labels": labels, "labels_match": labels == expected[out["id"]],
                            "drug_object_in_unit": out.get("result", {}).get("drug_object_in_unit"),
                            "review_flags": out.get("result", {}).get("review_flags", [])})
    after = manifest(RUNTIME)
    report = {
        "kind": "old_baseline_three_case_mechanism_diagnostic_not_validation",
        "n": len(results),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "output_sha256": sha(OUTPUT),
        "runtime_version": coder.VERSION,
        "runtime_tree_sha256_before": tree_sha(before),
        "runtime_unchanged_during_run": before == after,
        "comparisons": comparisons,
        "synthetic_not_policy": True,
        "not_human_validation": True,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
