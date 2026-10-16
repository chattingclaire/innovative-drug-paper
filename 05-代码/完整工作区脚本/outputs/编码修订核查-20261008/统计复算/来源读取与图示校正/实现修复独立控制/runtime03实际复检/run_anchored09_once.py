#!/usr/bin/env python3
"""Run the approved synthetic control-09 TXT-line-anchor input once on runtime03."""

import hashlib
import json
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
INPUT = PARENT / "09实际TXT源行锚补齐准备" / "09实际TXT源行锚输入.jsonl"
CONTROLS = PARENT / "构造控制.jsonl"
RUNTIME = HERE.parents[3] / "自动规则编码" / "实质评价与支持关系修复" / "runtime03"
OUTDIR = HERE / "09实际源行锚完整入口"
OUTPUT = OUTDIR / "09实际入口输出.jsonl"
REPORT = OUTDIR / "09实际入口报告.json"
INPUT_SHA = "81aee23ba27ae6720b55f35ea100eaad76f5144f6609438275f2bd7b60014ab1"
CONTROLS_SHA = "05c360a4f3e7c9d5656d4b2d61d24c228a514e8564214e95856ccecf54ef4fdd"
TREE_SHA = "d7d8b8fe77a5a420ec089d52ae28974d50963a0ef2acd47dc009f25591f1bb1d"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(root):
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"}


def tree_sha(files):
    return hashlib.sha256(json.dumps(files, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def main():
    assert sha(INPUT) == INPUT_SHA
    assert not OUTDIR.exists()
    row = json.loads(INPUT.read_text())
    assert row["id"] == "SYNCTRL-09" and "expected_labels" not in json.dumps(row, ensure_ascii=False)
    before = manifest(RUNTIME)
    assert tree_sha(before) == TREE_SHA
    sys.path.insert(0, str(RUNTIME.resolve()))
    import policy_coding_v27 as coder
    assert coder.VERSION == "substantive-evaluation-support-repair-03"
    started = time.monotonic()
    result = coder.code_unit(row["input"], source_adapter=True, substantive_rules=True)
    elapsed = round(time.monotonic() - started, 3)
    OUTDIR.mkdir()
    out = {"id": row["id"], "status": "completed", "result": result}
    OUTPUT.write_text(json.dumps(out, ensure_ascii=False) + "\n")
    assert sha(CONTROLS) == CONTROLS_SHA
    expected = next(json.loads(line)["expected_labels"] for line in CONTROLS.read_text().splitlines()
                    if json.loads(line)["id"] == "SYNCTRL-09")
    evidence = [item for item in result.get("evidence", []) if item.get("dimension") == "I"]
    unit = row["input"]["unit_text"]
    after = manifest(RUNTIME)
    report = {
        "kind": "approved_synthetic_09_actual_txt_anchor_runtime03_full_entry",
        "runtime_version": coder.VERSION,
        "runtime_tree_sha256": TREE_SHA,
        "runtime_unchanged_during_run": before == after,
        "elapsed_seconds": elapsed,
        "input_sha256": sha(INPUT),
        "output_sha256": sha(OUTPUT),
        "expected_labels": expected,
        "actual_labels": result.get("labels"),
        "labels_match": result.get("labels") == expected,
        "I_evidence": evidence,
        "full_I_quote_retains_stop_and_no_longer": bool(evidence) and all(
            item.get("display_quote") == unit and "停止" in item.get("display_quote", "")
            and "不再" in item.get("display_quote", "") for item in evidence),
        "review_flags": result.get("review_flags", []),
        "synthetic_not_policy": True,
        "not_human_validation": True,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
