"""Operator disk QA after first pass; never calls binder or coders."""
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def run():
    contract = json.loads((HERE / "implementation_execution_contract01.json").read_text())
    summary = json.loads((HERE / "execution_summary01.json").read_text())
    frozen = json.loads((HERE / "frozen_adapter_identity01.json").read_text())
    target = read(contract["inputs"]["leaf_index"]["path"])
    boundaries = read(contract["inputs"]["omitted_boundary_index"]["path"])
    for b in boundaries:
        b["occurrence_kind"] = "separate_nonemitted_scalar_boundary"
    target += boundaries
    target.sort(key=lambda x: (x["record_index_one_based"], x.get("leaf_index_within_record_one_based", 10**9)))
    results = read(HERE / "per_leaf_results01.jsonl")
    assert len(target) == len(results)
    failures, counts, categories, reasons = [], Counter(), defaultdict(Counter), Counter()
    seen, tool_ids, failed_occurrences = set(), {}, []
    for number, (expected, actual) in enumerate(zip(target, results), 1):
        key = (actual["id"], actual["raw_pointer"])
        checks = {
            "ordered_occurrence": actual["occurrence_index_one_based"] == number and actual["record_index_one_based"] == expected["record_index_one_based"],
            "exact_occurrence_identity": key == (expected["id"], expected["raw_pointer"]),
            "text_metadata_exact": actual["text_sha256"] == expected["text_sha256"] and actual["character_n"] == expected["character_n"],
            "unique_occurrence": key not in seen,
            "formal_ready_false": actual["formal_model_input_ready"] is False,
            "adapter_identity_exact": actual["adapter_sha256"] == frozen["files_sha256"][str(HERE / "source_locator_adapter01.py")],
            "binder_identity_exact": actual["fixed_binder03_sha256"] == contract["references"]["binder03"]["sha256"],
        }
        seen.add(key); counts[actual["status"]] += 1
        cat = "current_unit" if actual["raw_pointer"] == "/text" else "separate_nonemitted_boundary" if actual["occurrence_kind"] == "separate_nonemitted_scalar_boundary" else "registered_context_leaf"
        categories[cat][actual["status"]] += 1
        if actual["binder_called"]:
            b = actual["binding"]
            checks["bound_request_identity"] = b["record_id"] == actual["id"] and b["raw_pointer"] == actual["raw_pointer"] and b["text_sha256"] == actual["text_sha256"] and b["implementation_sha256"] == actual["fixed_binder03_sha256"]
        if actual["status"] in {"bound_literal", "bound_native_grid_image_bytes_only"}:
            b, p = actual["binding"], actual["plan"]
            checks["bound_position_axes"] = b["axes"]["candidate_position_bound"] is True and b["axes"]["source_literal_position_bound"] is True and bool(b["candidate_position"]) and bool(b["source_position"])
            checks["source_pair_exact"] = b["source"]["sha256"] == p["source_identity"]["source_sha256"] and b["source"]["path"] == str(Path(p["source_identity"]["source_path"]).resolve())
            checks["candidate_pair_exact"] = b["candidate_identity"]["sha256"] == p["candidate_identity"]["candidate_sha256"]
            checks["no_whitespace_or_punctuation_normalization"] = b["source_position"].get("literal_position", {}).get("matching", "exact_native_grid") in {"exact", "exact_native_grid"}
            if actual["status"] == "bound_native_grid_image_bytes_only":
                checks["no_false_visual_claim"] = b["axes"]["visual_transcription_revalidated"] is False
            tool = b["source_position"].get("extraction", {}).get("tool")
            if tool:
                tool_ids[tool["executable_sha256"]] = {k: tool[k] for k in ("name", "path", "executable_sha256", "version_probe_output_sha256")}
        else:
            failed_occurrences.append(actual)
            for reason in actual["reasons"]:
                reasons[actual["status"] + "::" + reason] += 1
        for code, passed in checks.items():
            if not passed:
                failures.append({"occurrence_index_one_based": number, "id": actual["id"], "raw_pointer": actual["raw_pointer"], "code": code})
    failed_file = read(HERE / "unsupported_and_failures01.jsonl")
    fail_subset_exact = failed_file == failed_occurrences
    preserve = all(sha(item["path"]) == item["sha256"] for item in contract["inputs"].values())
    frozen_preserved = all(sha(path) == s for path, s in frozen["files_sha256"].items())
    report = {"schema": "first-real-locator-pass-disk-QA01-v1", "at_utc": datetime.now(timezone.utc).isoformat(),
              "identity": "Operator serialization QA only, not new independent binder/source/coding validation.",
              "passed": not failures and fail_subset_exact and preserve and frozen_preserved,
              "declared_occurrence_n": len(target), "result_n": len(results), "counts": dict(counts),
              "by_material_occurrence_kind": {k: dict(v) for k, v in categories.items()}, "reason_counts": dict(reasons),
              "failed_subset_exact": fail_subset_exact, "failures": failures, "input_hashes_preserved": preserve,
              "frozen_implementation_preserved": frozen_preserved, "successful_extractor_tool_identities": list(tool_ids.values()),
              "first_execution_summary_sha256": sha(HERE / "execution_summary01.json"),
              "binder_model_rule_called_in_QA": False, "formal_model_input_ready": False}
    out = HERE / "disk_QA01.json"
    if out.exists():
        raise RuntimeError("Retain first disk QA; do not overwrite.")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "result_n": report["result_n"], "counts": report["counts"], "categories": report["by_material_occurrence_kind"], "qa_sha256": sha(out)}, ensure_ascii=False))


if __name__ == "__main__":
    run()
