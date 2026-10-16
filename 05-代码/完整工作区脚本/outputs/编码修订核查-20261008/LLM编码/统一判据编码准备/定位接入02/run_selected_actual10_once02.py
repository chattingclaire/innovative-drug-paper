"""One finite-layout binding pass on exactly ten preselected actual cases."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from source_locator_adapter02 import Adapter

HERE = Path(__file__).resolve().parent
BASE = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def selected_rows(path, indices):
    with Path(path).open(encoding="utf-8") as stream:
        return {i: json.loads(line) for i, line in enumerate(stream, 1) if i in indices}


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write("\n")


def run():
    frozen = json.loads((HERE / "frozen_execution02_corrected01.json").read_text())
    for path, identity in frozen["required_files_sha256"].items():
        assert sha(path) == identity, ("fixed_file_changed", path)
    for name in ("actual10_results02.jsonl", "actual10_first_failures02.jsonl", "actual10_summary02.json"):
        assert not (HERE / name).exists(), "Retain first ten-case execution, no overwrite."
    design = json.loads((BASE / "真实失败原因诊断01/selection_design01.json").read_text())
    items = design["selected"]
    assert len(items) == 10
    wanted = {x["record_index_one_based"] for x in items}
    contract = json.loads((BASE / "真实定位接入01/implementation_execution_contract01.json").read_text())
    rows = selected_rows(contract["inputs"]["llm_inputs"]["path"], wanted)
    rules = selected_rows(contract["inputs"]["rule_inputs"]["path"], wanted)
    sidecars = selected_rows(contract["inputs"]["projection_sidecars"]["path"], wanted)
    keys = {(x["id"], x["raw_pointer"]) for x in items}
    prior = {}
    with (BASE / "真实定位接入01/per_leaf_results01.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            result = json.loads(line)
            if (result["id"], result["raw_pointer"]) in keys:
                prior[(result["id"], result["raw_pointer"])] = result
    assert len(prior) == 10
    adapter = Adapter()
    actual, failures = [], []
    counts = Counter()
    with (HERE / "actual10_results02.jsonl").open("x", encoding="utf-8") as output, (HERE / "actual10_first_failures02.jsonl").open("x", encoding="utf-8") as failed:
        for i, item in enumerate(items, 1):
            ri = item["record_index_one_based"]
            old = prior[(item["id"], item["raw_pointer"])]
            occurrence = {k: old[k] for k in ("id", "raw_pointer", "text_sha256", "character_n", "occurrence_kind")}
            occurrence["source_binding"] = old["declared_source_binding"]
            result = adapter.bind(rows[ri], rules[ri], occurrence, sidecars[ri])
            same_plan = all(result.get("plan", {}).get(k) == old["plan"][k] for k in ("source_identity", "candidate_identity", "source_locator", "candidate_locator"))
            result.update(selected_case_index_one_based=i, original_occurrence_index_one_based=item["occurrence_index_one_based"],
                original_record_index_one_based=ri, first_execution_status=old["status"], first_execution_reasons=old["reasons"],
                original_material_and_positional_plan_unchanged=same_plan,
                adapter02_sha256=sha(HERE / "source_locator_adapter02.py"))
            output.write(json.dumps(result, ensure_ascii=False) + "\n");output.flush()
            if result["status"] not in {"bound_with_finite_layout_mapping", "bound_literal", "bound_native_grid_image_bytes_only"}:
                failed.write(json.dumps(result, ensure_ascii=False) + "\n");failed.flush();failures.append(result)
            actual.append(result);counts[result["status"]] += 1
    unchanged = {path: sha(path) == identity for path, identity in frozen["required_files_sha256"].items()}
    summary = {"at_utc": datetime.now(timezone.utc).isoformat(), "actual_n": len(actual), "counts": dict(counts),
        "all_original_positional_plans_unchanged": all(x["original_material_and_positional_plan_unchanged"] for x in actual),
        "fixed_inputs_and_implementations_and_sources_unchanged": all(unchanged.values()), "preservation_by_path": unchanged,
        "binder_call_n": sum(x["binder_called"] for x in actual),
        "source_and_candidate_actual_SHA_before_and_after": "Binder04 rechecks each actual pair before/after; complete fixed identities also checked here.",
        "expected_nine_was_not_used_as_acceptance_answer": True, "whole_28196_reexecuted": False,
        "formal_model_input_ready": False, "model_or_rule_called": False, "labels_read_or_modified": False,
        "artifacts": {n: {"path": str(HERE / n), "sha256": sha(HERE / n)} for n in ("actual10_results02.jsonl", "actual10_first_failures02.jsonl")}}
    write_new(HERE / "actual10_summary02.json", summary)
    print(json.dumps({"actual_n": len(actual), "counts": dict(counts), "plans_unchanged": summary["all_original_positional_plans_unchanged"],
        "fixed_files_unchanged": summary["fixed_inputs_and_implementations_and_sources_unchanged"],
        "cases": [{"id": x["id"], "pointer": x["raw_pointer"], "status": x["status"], "reasons": x["reasons"]} for x in actual]}, ensure_ascii=False))


if __name__ == "__main__":
    run()
