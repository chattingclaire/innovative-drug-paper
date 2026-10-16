#!/usr/bin/env python3
"""Run ten synthetic controls once through the frozen full code-unit entry.

Do not invoke until root supplies the final runtime directory, tree SHA and
implementation version. Expected labels are loaded only after all encoder
calls have completed and are never passed to the encoder.
"""

import argparse
import ast
import collections
import hashlib
import json
import re
import sys
import time
import traceback
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE / "完整入口输入10.jsonl"
EXPECTATIONS = HERE / "构造控制.jsonl"
SOURCE = HERE / "fixtures" / "合成机制控制-非政府文件.txt"
CANDIDATE = HERE / "fixtures" / "合成机制控制-非政府文件.candidate.json"
MANUAL = HERE.parents[2] / "定义溯源核查" / "测量与计数统一" / "共用编码手册.md"
OUTPUT = HERE / "实际入口输出10.jsonl"
FREEZE = HERE / "实际入口执行冻结.json"
REPORT = HERE / "实际入口执行报告.json"
INPUT_SHA256 = "eb6650ea3cff400c725b157b807abf6a19ef425acc469b2519649c605ca1b031"
EXPECTATIONS_SHA256 = "05c360a4f3e7c9d5656d4b2d61d24c228a514e8564214e95856ccecf54ef4fdd"
SOURCE_SHA256 = "2515890a161cb741ba8547df19124a838b83f514b5f7791f88bc57f56ff3adae"
CANDIDATE_SHA256 = "e398e7b411c39e2882b0e230d10d4d14f7447ae2266766eabb7f14a5f29d9a26"
MANUAL_SHA256 = "24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9"
DIMS = ("S", "E", "Ec", "I", "F")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(root):
    return {str(path.relative_to(root)): sha(path) for path in sorted(root.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"}


def tree_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-dir", required=True)
    parser.add_argument("--expected-runtime-tree-sha256", required=True)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    runtime = Path(args.runtime_dir).resolve()
    assert runtime.is_dir()
    assert not any(path.exists() for path in (OUTPUT, FREEZE, REPORT)), "One actual run only; no overwrite."
    assert sha(INPUT) == INPUT_SHA256 and sha(SOURCE) == SOURCE_SHA256
    assert sha(CANDIDATE) == CANDIDATE_SHA256 and sha(MANUAL) == MANUAL_SHA256
    rows = [json.loads(line) for line in INPUT.read_text().splitlines() if line.strip()]
    assert len(rows) == len({row["id"] for row in rows}) == 10
    assert all("expected_labels" not in json.dumps(row, ensure_ascii=False) for row in rows)
    candidate = json.loads(CANDIDATE.read_text())
    assert candidate["status"] == "synthetic_not_policy_not_human_validation"
    assert all(row["input"]["content_role"] == "synthetic_development_fixture" for row in rows)
    assert all(row["input"]["verified_parent_context"] == []
               if "verified_parent_context" in row["input"] else True for row in rows)
    assert all(row["input"]["llm_v29_shared_context"]["verified_parent_context"] == []
               for row in rows)

    before = manifest(runtime)
    assert tree_hash(before) == args.expected_runtime_tree_sha256
    for path in runtime.glob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
    # EXPECTATIONS is deliberately excluded here: it is first opened only
    # after all encoder calls. Its fixed SHA is checked at that point.
    protected = {str(path.resolve()): sha(path) for path in
                 (INPUT, SOURCE, CANDIDATE, MANUAL)}
    freeze = {
        "kind": "synthetic_full_entry_mechanism_controls_not_human_validation",
        "n": 10,
        "input_path": str(INPUT.resolve()),
        "input_sha256": sha(INPUT),
        "source_path": str(SOURCE.resolve()),
        "source_sha256": sha(SOURCE),
        "candidate_path": str(CANDIDATE.resolve()),
        "candidate_sha256": sha(CANDIDATE),
        "manual_sha256": sha(MANUAL),
        "runtime_path": str(runtime),
        "runtime_manifest": before,
        "runtime_tree_sha256": tree_hash(before),
        "expected_version": args.expected_version,
        "expected_labels_absent_from_encoder_input": True,
        "expected_labels_not_loaded_before_encoder_calls": True,
        "synthetic_not_policy": True,
        "no_human_validation_claim": True,
        "protected_files_before": protected,
    }
    sys.path.insert(0, str(runtime))
    import policy_coding_v27 as coder
    assert Path(coder.__file__).resolve().parent == runtime
    assert coder.VERSION == args.expected_version
    assert coder.CURRENT_MANUAL_SHA256 == MANUAL_SHA256
    FREEZE.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n")
    started = time.monotonic()
    results = []
    with OUTPUT.open("w") as handle:
        for row in rows:
            try:
                result = coder.code_unit(row["input"], source_adapter=True,
                                         substantive_rules=True)
                original = row["input"]["unit_text"]
                assert result["unit_text_sha256"] == hashlib.sha256(original.encode()).hexdigest()
                assert set(result["labels"]) == set(DIMS)
                for evidence in result.get("evidence", []):
                    assert original[evidence["start"]:evidence["end"]] == evidence["text"]
                out = {"id": row["id"], "status": "completed", "result": result}
            except Exception as error:
                out = {"id": row["id"], "status": "failed",
                       "error_type": type(error).__name__, "error": str(error),
                       "traceback": traceback.format_exc()}
            results.append(out)
            handle.write(json.dumps(out, ensure_ascii=False) + "\n")
            handle.flush()
            print(row["id"], out["status"], flush=True)

    # Expectations enter only after every code_unit call has returned.
    assert sha(EXPECTATIONS) == EXPECTATIONS_SHA256
    controls = {row["id"]: row for row in
                (json.loads(line) for line in EXPECTATIONS.read_text().splitlines() if line.strip())}
    assessments = []
    for row, out in zip(rows, results):
        expected = controls[row["id"]]["expected_labels"]
        result = out.get("result", {})
        labels = result.get("labels")
        unit_text = row["input"]["unit_text"]
        evidence = result.get("evidence", [])
        positive_quote_checks = {}
        for dim, value in expected.items():
            if value != 1:
                continue
            dim_evidence = [item for item in evidence if item.get("dimension") == dim]
            positive_quote_checks[dim] = bool(dim_evidence) and all(
                item.get("display_quote") == unit_text
                and item.get("current_statement", {}).get("text") == unit_text
                for item in dim_evidence)
        case09 = None
        if row["id"] == "SYNCTRL-09":
            i_evidence = [item for item in evidence if item.get("dimension") == "I"]
            explanation = json.dumps(i_evidence, ensure_ascii=False)
            case09 = {
                "I_issue_label_is_one": labels is not None and labels.get("I") == 1,
                "full_quote_retains_stop_and_no_longer": bool(i_evidence) and all(
                    "停止" in item.get("display_quote", "") and "不再" in item.get("display_quote", "")
                    for item in i_evidence),
                "no_explicit_current_support_claim_detected_by_bounded_guard": not bool(re.search(
                    r"(?:当前|仍然|仍|继续|正在|持续|保持)(?:在)?(?:提供|给予|开展|实施)"
                    r"(?:创新研发)?(?:支持|反馈|咨询|帮助)?", explanation)),
                "human_reason_review_required": True,
                "support_status_output_field_required": False,
                "direction_classifier_required": False,
            }
        passed = (out["status"] == "completed" and labels == expected
                  and all(positive_quote_checks.values())
                  and (case09 is None or all(value for key, value in case09.items()
                                             if key not in ("human_reason_review_required",
                                                            "support_status_output_field_required",
                                                            "direction_classifier_required"))))
        assessments.append({
            "id": row["id"], "expected_labels": expected, "actual_labels": labels,
            "labels_match": labels == expected, "positive_quote_checks": positive_quote_checks,
            "case09_negated_support_interpretation": case09, "pass": passed,
            "manual_reason": controls[row["id"]]["reason"],
        })

    after = manifest(runtime)
    protected_after = {path: sha(path) for path in protected}
    report = {
        "kind": "one_actual_synthetic_full_entry_control_run_not_human_validation",
        "n": 10,
        "status_counts": dict(collections.Counter(row["status"] for row in results)),
        "n_undetermined": sum(row.get("result", {}).get("judgement_status") == "undetermined"
                              for row in results),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "input_sha256": sha(INPUT), "output_sha256": sha(OUTPUT),
        "manual_sha256": sha(MANUAL), "runtime_tree_sha256": tree_hash(before),
        "runtime_unchanged_during_run": before == after,
        "protected_files_unchanged": protected == protected_after,
        "expected_labels_loaded_only_after_all_encoder_calls": True,
        "case09_bounded_guard_is_not_semantic_direction_classification": True,
        "case09_output_reason_requires_human_review": True,
        "all_controls_pass": all(item["pass"] for item in assessments),
        "assessments": assessments,
        "synthetic_not_policy": True,
        "no_human_or_model_labels_used_by_encoder": True,
        "no_human_validation_or_performance_claim": True,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "n", "status_counts", "n_undetermined", "runtime_unchanged_during_run",
        "protected_files_unchanged", "all_controls_pass", "output_sha256")},
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
