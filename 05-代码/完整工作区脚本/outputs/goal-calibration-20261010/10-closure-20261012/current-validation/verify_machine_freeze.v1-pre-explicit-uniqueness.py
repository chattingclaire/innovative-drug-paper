"""Read-only integrity checks for the adopted current4481 machine snapshot.

No classifiers, model calls, reception/selection, reference joins, or statistics.
Only aggregate integrity/coverage metadata is emitted, never source text/labels.
"""
import argparse
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
from pathlib import Path

DIMS = ("S", "E", "Ec", "I", "F")
RULE = "06-coding/rule-full4481-v11-v16-receipt-delta-merged-root"
NATIVE = "06-coding/native-full4481-v16-three-member-compatible-root"
DIAG = "07-statistics/current-full4481-v11-v16-source-aligned-diagnostics-root"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            size += len(block)
            digest.update(block)
    return {"path": str(path), "bytes": size, "sha256": digest.hexdigest()}


def core(spec):
    return {key: spec[key] for key in ("path", "bytes", "sha256")}


def lines(path):
    with Path(path).open("rb") as handle:
        for raw in handle:
            if raw.strip():
                yield json.loads(raw), raw


class Inventory:
    def __init__(self):
        self.files = {}

    def add(self, spec, role):
        expected = core(spec)
        path = expected["path"]
        if path in self.files:
            require(core(self.files[path]) == expected, "Conflicting binding: " + path)
        else:
            require(binding(path) == expected, "Frozen file changed: " + path)
            self.files[path] = {**expected, "roles": []}
        if role not in self.files[path]["roles"]:
            self.files[path]["roles"].append(role)
        return expected

    def path(self, path, role):
        path = str(Path(path).resolve())
        return self.add(core(self.files[path]) if path in self.files else binding(path), role)

    def tree(self, value, role):
        if isinstance(value, dict):
            if {"path", "bytes", "sha256"} <= set(value):
                self.add(value, role)
            for child in value.values():
                self.tree(child, role)
        elif isinstance(value, list):
            for child in value:
                self.tree(child, role)

    def document(self, path, role, children=True):
        self.path(path, role)
        value = load(path)
        if children:
            self.tree(value, role)
        return value


def inspect(root):
    root = Path(root).resolve()
    inv = Inventory()
    rp, np, dp = (root / name for name in (RULE, NATIVE, DIAG))
    rs = inv.document(rp / "composite-status.json", "rule_current_status_and_bound_sources")
    ns = inv.document(np / "status.json", "LLM_current_status_and_bound_sources")
    coverage = inv.document(np / "coverage.json", "LLM_coverage_and_original_failure_history")
    for path in (rp / "seal.json", np / "seal.json"):
        inv.document(path, "adopted_current_output_seal")
    # Bind existing diagnostics, without reusing its development-reference scores.
    inv.path(dp / "metrics.json", "existing_diagnostics_not_formal_validation")
    alignment = inv.document(dp / "material-alignment.json", "source_alignment_report", False)
    inv.path(dp / "seal.json", "existing_diagnostics_seal")
    manifest = inv.document(coverage["original_manifest"]["path"], "original_LLM_manifest_and_common_protocol")
    inv.document(coverage["recovery_manifest"]["path"], "LLM_recovery_transport_manifest")
    delta_manifest = root / "06-coding/native-v16-batch0216-material-delta-preparation-sol/manifest.json"
    inv.document(delta_manifest, "LLM_v16_whole_batch_transport_manifest")
    frame_doc = inv.document(manifest["ordered_source_ids"]["path"], "approved_ordered_frame")
    ids = frame_doc["approved_record_ids"]
    require(len(ids) == len(set(ids)) == 4481, "Full frame4481 identity mismatch")
    require(sha(("\n".join(ids) + "\n").encode()) == frame_doc["frame_order_UTF8_LF_sha256"], "Frame LF order mismatch")
    require([sid for batch in manifest["batches"] for sid in batch["source_ids"]] == ids, "Original504 batch order mismatch")
    inv.document(manifest["source_material_inventory"]["path"], "original_common_source_asset_inventory")
    specs = rs["material_delta_bindings"]
    for item in specs.values():
        inv.add(item, "current_v16_material_contract")
    inv.document(specs["seal"]["path"], "current_v16_material_seal")
    packets = inv.document(specs["packet_bindings"]["path"], "current_v16_packet_bindings")
    correspondence = inv.document(specs["correspondence"]["path"], "v15_v16_byte_correspondence")
    proof = inv.document(specs["byteproof"]["path"], "adopted_material_byte_equivalence")
    require([p["source_id"] for p in packets] == ids, "Current packet order differs")
    pby = {p["source_id"]: p for p in packets}
    require(rs["source_common_v16"] == ns["source_common_v16"] == proof["new_common"], "Current source versions differ")
    require(rs["source_common_v15"] == ns["source_common_v15"] == proof["old_common"], "Parent source versions differ")
    require(correspondence["changed_source_ids"] == rs["material_changed_record_ids"] == ["RECODE25-01402"], "Material delta IDs differ")
    require([row["source_id"] for row in correspondence["records"]] == ids, "Correspondence order differs")
    current_bundle_sha = {}
    for ordinal, ((bundle, raw), packet, row) in enumerate(zip(lines(proof["new_common"]["path"]), packets, correspondence["records"]), 1):
        sid = packet["source_id"]
        require(bundle["source_record"]["id"] == sid and row["frame_ordinal_1based"] == ordinal, "Common bundle order differs")
        digest = sha(canonical(bundle))
        require(digest == packet["source_bundle_sha256"], "Canonical bundle SHA differs")
        require(sha(raw) == row["new_common_line_sha256"], "Common line SHA differs")
        require(row["new_packet_binding"] == packet, "Correspondence packet differs")
        actual_packet = load(packet["path"])
        require(actual_packet["source_id"] == sid and actual_packet["source_bundle_sha256"] == digest and sha(canonical(actual_packet["source_bundle"])) == digest, "Physical packet/current bundle mismatch")
        current_bundle_sha[sid] = digest
    require(len(current_bundle_sha) == 4481, "Current common source incomplete")
    require(proof["other_4480_lines_including_terminators_byte_equal"] is True and proof["other_4480_packet_bindings_exact_reused"] is True, "Material equivalence proof absent")

    predictions = dict((record["id"], (record, raw)) for record, raw in lines(rp / "predictions.jsonl"))
    origins = dict((record["id"], record) for record, raw in lines(rp / "execution-origin-lineage.jsonl"))
    require(list(predictions) == list(origins) == ids, "Rule IDs/order incomplete or duplicated")
    rule_counts = {d: Counter() for d in DIMS}
    for sid, (record, raw) in predictions.items():
        require(set(record["labels"]) == set(record["decisions"]) == set(DIMS), "Rule dimension coverage mismatch")
        require(sha(raw) == origins[sid]["actual_prediction_line_sha256"] and len(raw) == origins[sid]["prediction_line_bytes"], "Rule actual line provenance mismatch")
        for dim in DIMS:
            value = record["labels"][dim]
            require(value is None or type(value) is int and value in (0, 1), "Illegal rule value")
            require(record["decisions"][dim]["value"] == value, "Rule decision/value differs")
            rule_counts[dim]["lawful_null_N" if value is None else "positive_N" if value else "negative_N"] += 1
    seen_slots = set()
    for slot, raw in lines(rp / "all-dimension-slots.jsonl"):
        key = (slot["id"], slot["dimension"])
        require(key not in seen_slots, "Duplicate rule slot")
        seen_slots.add(key)
        sid, dim = key
        require(slot["technical_failure"] is False and slot["rule_executed"] is True, "Unresolved rule technical slot")
        require(slot["rule_value"] == predictions[sid][0]["labels"][dim] and slot["rules_null"] == (slot["rule_value"] is None), "Rule slot state mismatch")
        require(slot["retained_rule_decision"] == predictions[sid][0]["decisions"][dim], "Rule retained decision mismatch")
        require(slot["source_bundle_sha256"] == current_bundle_sha[sid], "Rule/current material SHA mismatch")
    require(len(seen_slots) == 22405 and {d: dict(c) for d, c in rule_counts.items()} == rs["counts"], "Rule slot counts differ")
    algorithms = Counter(o["actual_inference_algorithm"] for o in origins.values())
    require(dict(algorithms) == rs["actual_execution_algorithm_record_N"], "Rule mixed execution origins differ")
    run_dirs = sorted({o["actual_run_directory"] for o in origins.values()})
    original_rows = {}
    for directory in run_dirs:
        directory = Path(directory)
        freeze = inv.document(directory / "freeze.json", "actual_rule_run_freeze_and_implementation")
        inv.document(directory / "seal.json", "actual_rule_run_original_seal_including_failures")
        inv.document(directory / "execution.json", "actual_rule_run_execution_evidence")
        release = inv.document(freeze["common_release_binding"]["path"], "actual_rule_production_release")
        require(release["manual"] == manifest["manual"] and release["prompt"] == manifest["execution_prompt"], "Rule/LLM common manual or prompt differs")
        inv.document(freeze["final_candidate_algorithm"]["path"], "actual_rule_algorithm_bindings")
        original_rows[str(directory)] = {r["id"]: raw for r, raw in lines(directory / "predictions.jsonl")}
    for sid, origin in origins.items():
        inv.path(origin["source_consumption_log"], "actual_rule_source_consumption_provenance")
        if origin["unchanged_actual_record_bytes_retained"]:
            require(predictions[sid][1] == original_rows[origin["actual_run_directory"]][sid], "Rule original selected row changed")
        else:
            require(sid == "RECODE25-01402" and origin["new_semantic_execution"] is False and origin["original_first_failure_preserved"] is True, "Unexpected recovered row")
            original = json.loads(original_rows[origin["actual_run_directory"]][sid])
            require(predictions[sid][0]["decisions"] == original["candidate_decisions_diagnostic_only"], "Recovered decisions changed from original diagnostic")
    # Bind each adopted inheritance/equivalence step, never replace its outputs.
    parent_status = rs
    for _ in range(10):
        for key in ("impact_closure_plan", "adoption", "original_input_lineage", "ROOT_receipt_recovery_adoption"):
            if key in parent_status:
                inv.document(parent_status[key]["path"], "adopted_rule_compatibility_and_recovery_evidence")
        parent = parent_status.get("parent_seal")
        if not parent:
            break
        inv.document(parent["path"], "inherited_rule_parent_seal")
        candidate = Path(parent["path"]).parent / "composite-status.json"
        if not candidate.exists():
            break
        parent_status = inv.document(candidate, "inherited_rule_compatible_status")
    inv.document(rs["delta_seal"]["path"], "receipt_recovered_rule_delta_seal")
    inv.document(Path(rs["delta_seal"]["path"]).parent / "execution.json", "receipt_only_recovery_not_new_judgment")

    native = dict((record["id"], (record, raw)) for record, raw in lines(np / "selected-records.jsonl"))
    require(list(native) == ids, "LLM IDs/order incomplete or duplicated")
    batches = inv.document(np / "selected-whole-batch-bindings.json", "adopted_LLM_whole_batch_sources")
    require(len(batches) == 504 and [sid for b in batches for sid in b["source_ids"]] == ids, "LLM whole-batch coverage differs")
    ncounts = {d: Counter() for d in DIMS}
    modes = Counter()
    batch_modes = Counter()
    for batch in batches:
        batch_modes[batch["selected_mode"]] += 1
        selection = inv.document(batch["selection"]["path"], "actual_LLM_selection_retained_not_reselected")
        inv.document(batch["receipt"]["path"], "actual_LLM_technical_receipt")
        original = load(batch["first"]["path"])
        require(original["manual_binding"] == manifest["manual"] and original["execution_prompt_binding"] == manifest["execution_prompt"], "LLM first common manual/prompt mismatch")
        require([r["source_id"] for r in original["records"]] == batch["source_ids"], "LLM selected whole-first membership differs")
        for actual in original["records"]:
            sid = actual["source_id"]
            rec = native[sid][0]
            require(rec["first"] == batch["first"] and rec["selection"] == batch["selection"], "LLM record source differs from whole batch")
            require(rec["dimensions"] == actual["dimensions"], "LLM original complete decisions changed")
            inv.tree({k: rec[k] for k in ("packet", "first", "selection", "technical_receipt", "actor_seal")}, "LLM_original_record_provenance")
            require((rec["packet"]["bytes"], rec["packet"]["sha256"]) == (pby[sid]["bytes"], pby[sid]["sha256"]), "LLM/current packet bytes differ")
            require(actual["packet_sha256"] == rec["packet"]["sha256"], "LLM original packet SHA differs")
            modes[rec["selected_mode"]] += 1
            require(set(rec["labels"]) == set(rec["dimensions"]) == set(DIMS), "LLM dimension coverage mismatch")
            for dim in DIMS:
                value = rec["labels"][dim]
                require(value is None or type(value) is int and value in (0, 1), "Illegal LLM value")
                require(rec["dimensions"][dim]["value"] == value, "LLM value/decision mismatch")
                ncounts[dim]["lawful_null_N" if value is None else "positive_N" if value else "negative_N"] += 1
    for dim in DIMS:
        require(dict(ncounts[dim]) == {k: v for k, v in coverage["per_dimension"][dim].items() if k != "missing_N"}, "LLM coverage counts differ")
    parent_native = {r["id"]: raw for r, raw in lines(ns["parent_selected_records"]["path"])}
    replaced = set(ns["actual_new_whole_batch_record_ids"])
    kept = sum(raw == parent_native[sid] for sid, (row, raw) in native.items() if sid not in replaced)
    require(kept == ns["parent_raw_line_preserved_N"] == 4478 and len(replaced) == 3, "LLM preserved parent provenance differs")
    require(alignment["native_material_aligned_record_N"] == 4481 and alignment["native_material_mismatch_N"] == 0, "Stored material alignment differs")
    require(rs["technical_failure_dimension_N"] == ns["unresolved_technical_dimension_N"] == coverage["missing_label_N"] == 0, "Snapshot has unresolved outputs")
    return inv, {
        "frame_N": 4481, "dimensions": list(DIMS), "slots_per_method_N": 22405,
        "rule_record_N": len(predictions), "rule_lawful_null_N": sum(c["lawful_null_N"] for c in rule_counts.values()),
        "rule_unresolved_technical_slot_N": 0, "rule_actual_algorithm_record_N": dict(algorithms),
        "rule_original_row_byte_retained_N": 4480, "rule_receipt_recovered_original_diagnostic_N": 1,
        "rule_original_v11_failed_slots_retained_N": rs["original_v11_first_technical_failure_dimension_N"],
        "LLM_record_N": len(native), "LLM_whole_batch_N": len(batches),
        "LLM_lawful_null_N": sum(c["lawful_null_N"] for c in ncounts.values()),
        "LLM_missing_slot_N": 0, "LLM_actual_record_modes": dict(modes), "LLM_actual_batch_modes": dict(batch_modes),
        "LLM_parent_rows_exactly_preserved_N": kept, "LLM_new_v16_whole_batch_record_N": 3,
        "current_material_verified_packet_N": len(current_bundle_sha), "rule_material_mismatch_N": 0,
        "LLM_material_mismatch_N": 0, "material_changed_record_N": 1,
        "adopted_source_alignment_reproduced": True,
        "semantics_or_accuracy_checked": False, "formal_validation_complete": False,
    }, {
        "common_manual": manifest["manual"], "common_execution_prompt": manifest["execution_prompt"],
        "common_protocol": manifest["protocol"], "frame_ids": manifest["ordered_source_ids"],
        "current_common_source": rs["source_common_v16"], "current_packet_metadata": specs["packet_bindings"],
        "material_equivalence": specs,
        "rule_predictions": binding(rp / "predictions.jsonl"), "rule_dimension_slots": binding(rp / "all-dimension-slots.jsonl"),
        "rule_execution_lineage": binding(rp / "execution-origin-lineage.jsonl"), "rule_status": binding(rp / "composite-status.json"),
        "LLM_records": binding(np / "selected-records.jsonl"), "LLM_batches": binding(np / "selected-whole-batch-bindings.json"),
        "LLM_coverage": binding(np / "coverage.json"), "source_alignment": binding(dp / "material-alignment.json"),
    }


def create(root, output):
    output = Path(output).resolve()
    require(not output.exists(), "Never overwrite an existing freeze")
    inv, checks, inputs = inspect(root)
    payload = {
        "schema": "current4481-adopted-machine-evidence-freeze-v1",
        "created_at_local": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "project_root": str(Path(root).resolve()), "verifier": binding(__file__),
        "scope": "当前已采用规则兼容组合与LLM全量快照，仅为后续现版验证注册提供真实冻结输入",
        "inputs": inputs, "structural_check_results": checks,
        "file_bindings": sorted(inv.files.values(), key=lambda x: x["path"]),
        "provenance_limits": {
            "all4481_rule_reexecuted_under_v11": False,
            "all4481_LLM_reexecuted_under_v16": False,
            "technical_recovery_or_delta_is_independent_repeat": False,
            "provider_serving_model_independently_verified": False,
            "actual_human_feedback_received_in_this_thread_as_of_creation": False,
            "human_start_time_verified": False, "machine_freeze_before_human_start_claimed": False,
            "human_adjudication_created": False, "formal_acceptance_claimed": False,
            "old200_current_version_validity_granted": False,
            "study_statistics_computed": False,
        },
        "future_registration_requirements": [
            "结合现版开发曝光域及真实人工开始/提交证据另行注册适用范围，不能由文件时间戳推定先后关系。",
            "保留NULL与历史技术失败，不以0填补，不改选既有首答。",
            "机器指标必须另接可信真人裁定；本清单不提供真人标签或裁定。",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, default=Path(__file__).with_name("machine-freeze.json"))
    args = parser.parse_args()
    frozen = load(args.freeze)
    require(binding(__file__) == frozen["verifier"], "Verifier bytes changed")
    for spec in frozen["file_bindings"]:
        require(binding(spec["path"]) == core(spec), "Frozen evidence changed: " + spec["path"])
    inv, checks, inputs = inspect(frozen["project_root"])
    require(checks == frozen["structural_check_results"] and inputs == frozen["inputs"], "Current machine snapshot differs")
    require(sorted(inv.files.values(), key=lambda x: x["path"]) == frozen["file_bindings"], "Evidence inventory differs")
    print(json.dumps({"verified": True, "file_binding_N": len(inv.files),
                      "checks": checks, "formal_acceptance": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
