"""One authorized real pass over frozen source-only occurrences; no coders."""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from source_locator_adapter01 import Adapter, BINDER_PATH, BINDER_SHA, PROJECTOR_PATH, PROJECTOR_SHA, sha

HERE = Path(__file__).resolve().parent


def dump(stream, item):
    stream.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")


def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def run():
    contract_path = HERE / "implementation_execution_contract01.json"
    contract = json.loads(contract_path.read_text())
    frozen = json.loads((HERE / "frozen_adapter_identity01.json").read_text())
    for path, expected in frozen["files_sha256"].items():
        if sha(path) != expected:
            raise RuntimeError("frozen_implementation_dependency_changed:" + path)
    for item in contract["inputs"].values():
        if sha(item["path"]) != item["sha256"]:
            raise RuntimeError("fixed_input_changed:" + item["path"])
    for name in ("per_leaf_results01.jsonl", "unsupported_and_failures01.jsonl", "progress01.jsonl", "execution_summary01.json"):
        if (HERE / name).exists():
            raise RuntimeError("First real execution retained; no overwrite:" + name)
    data = contract["inputs"]
    rules = load_jsonl(data["rule_inputs"]["path"])
    rows = load_jsonl(data["llm_inputs"]["path"])
    sidecars = load_jsonl(data["projection_sidecars"]["path"])
    occurrences = load_jsonl(data["leaf_index"]["path"])
    boundaries = load_jsonl(data["omitted_boundary_index"]["path"])
    assert len(rows) == len(rules) == len(sidecars) == contract["record_n"]
    assert len(occurrences) == contract["registered_leaf_occurrence_n"]
    assert len(boundaries) == contract["separate_nonemitted_scalar_boundary_n"]
    for index, (row, rule, sidecar) in enumerate(zip(rows, rules, sidecars), 1):
        assert row["id"] == rule["id"] == sidecar["id"]
        assert row["text"] == rule["input"]["unit_text"]
    for boundary in boundaries:
        boundary = dict(boundary)
        boundary["occurrence_kind"] = "separate_nonemitted_scalar_boundary"
        occurrences.append(boundary)
    occurrences.sort(key=lambda x: (x["record_index_one_based"], x.get("leaf_index_within_record_one_based", 10**9)))
    adapter, totals = Adapter(), Counter()
    reasons, by_kind, by_format = Counter(), defaultdict(Counter), defaultdict(Counter)
    seen_records = set()
    started = datetime.now(timezone.utc).isoformat()
    with (HERE / "per_leaf_results01.jsonl").open("x", encoding="utf-8") as output, \
            (HERE / "unsupported_and_failures01.jsonl").open("x", encoding="utf-8") as failures, \
            (HERE / "progress01.jsonl").open("x", encoding="utf-8") as progress:
        for index, occurrence in enumerate(occurrences, 1):
            ri = occurrence["record_index_one_based"] - 1
            row, rule, sidecar = rows[ri], rules[ri], sidecars[ri]
            assert occurrence["id"] == row["id"]
            result = adapter.bind(row, rule, occurrence, sidecar)
            result.update(occurrence_index_one_based=index, record_index_one_based=ri + 1,
                          adapter_sha256=frozen["files_sha256"][str(HERE / "source_locator_adapter01.py")],
                          fixed_binder03_sha256=BINDER_SHA)
            dump(output, result)
            if result["status"] not in {"bound_literal", "bound_native_grid_image_bytes_only"}:
                dump(failures, result)
            seen_records.add(row["id"])
            totals["processed_occurrence_n"] += 1
            totals[result["status"]] += 1
            totals["binder_call_n"] += bool(result["binder_called"])
            for reason in result["reasons"]:
                reasons[result["status"] + "::" + reason] += 1
            by_kind[result["occurrence_kind"]][result["status"]] += 1
            declared = result.get("plan", {}).get("source_identity", result.get("declared_source_binding") or {})
            source_path = declared.get("source_path", declared.get("path", ""))
            by_format[Path(source_path).suffix.lower() or "<unavailable_or_no_suffix>"][result["status"]] += 1
            if index == 100 or index % 500 == 0 or index == len(occurrences):
                item = {"at_utc": datetime.now(timezone.utc).isoformat(), "processed_leaf_n": index,
                        "target_leaf_n": len(occurrences), "processed_record_n": len(seen_records), "counts": dict(totals),
                        "formal_model_input_ready": False}
                dump(progress, item); progress.flush(); output.flush(); failures.flush()
                print(json.dumps(item, ensure_ascii=False), flush=True)
    identities = {name: {"path": item["path"], "expected_sha256": item["sha256"], "after_sha256": sha(item["path"]),
                        "unchanged": sha(item["path"]) == item["sha256"]} for name, item in contract["inputs"].items()}
    frozen_unchanged = all(sha(path) == expected for path, expected in frozen["files_sha256"].items())
    summary = {"schema": "first-real-source-locator-pass-summary01-v1", "started_at_utc": started,
        "ended_at_utc": datetime.now(timezone.utc).isoformat(), "contract_sha256": sha(contract_path),
        "frozen_implementation_manifest_sha256": sha(HERE / "frozen_adapter_identity01.json"),
        "counts": dict(totals), "distinct_records_processed": len(seen_records),
        "all_declared_nonblank_occurrences_processed": totals["processed_occurrence_n"] == contract["registered_leaf_occurrence_n"] + contract["separate_nonemitted_scalar_boundary_n"],
        "reason_counts": dict(reasons), "by_occurrence_kind": {k: dict(v) for k, v in by_kind.items()},
        "by_source_suffix": {k: dict(v) for k, v in by_format.items()}, "input_identity_preservation": identities,
        "frozen_implementation_unchanged": frozen_unchanged,
        "actual_first_support_and_position_binding_pass_performed": True,
        "global_all_material_authenticated_claim": False, "formal_model_input_ready": False,
        "model_or_rule_called": False, "formal_model_packet_generated": False,
        "labels_read_or_modified": False, "original_source_candidate_input_or_manuscript_modified": False,
        "rate_meaning": "Support and actual literal/grid position binding coverage over declared leaf occurrences; not coding validity/reliability/precision/recall.",
        "unsupported_known_projection_issues": "716 empty/invalid text and unknown containers remain in preceding issues01.jsonl; no fabricated leaf strings added.",
        "artifacts": {name: {"path": str(HERE / name), "sha256": sha(HERE / name)} for name in ("per_leaf_results01.jsonl", "unsupported_and_failures01.jsonl", "progress01.jsonl")}}
    (HERE / "execution_summary01.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"complete": True, "counts": dict(totals), "reason_counts": dict(reasons)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    run()
