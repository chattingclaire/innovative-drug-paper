"""Verify delivered files and register evidence without accepting formal research results."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    annual_dir = ROOT / "01-review/annual-publication-date-audit-sol"
    seal = json.loads((annual_dir / "seal.json").read_text())
    for item in seal["files"]:
        p = annual_dir / item["relative_path"]
        assert sha(p) == item["sha256"], str(p)
        assert p.stat().st_size == item["bytes"], str(p)
    metadata = json.loads((annual_dir / "metadata.json").read_text())
    for item in metadata["inputs"]:
        assert sha(item["path"]) == item["sha256"]
    for entry in metadata["entries"]:
        assert sha(entry["metadata_path"]) == entry["metadata_sha256"]
    assert len(metadata["entries"]) == 20
    assert metadata["verified_exact_original_publication_date_n"] == 20
    assert metadata["still_null_n"] == 0

    engine_dir = ROOT / "07-statistics/prospective-engine-year-sol"
    ins = json.loads((engine_dir / "input-seal.json").read_text())
    outs = json.loads((engine_dir / "output-seal.json").read_text())
    engine_inputs_n = 0
    for key in ["predecessor_and_plan", "synthetic_inputs", "synthetic_frozen_source_year_maps"]:
        for filename, expected in ins[key].items():
            p = Path(filename) if Path(filename).is_absolute() else engine_dir / filename
            assert sha(p) == expected, str(p)
            engine_inputs_n += 1
    assert sha(engine_dir / "input-seal.json") == outs["input_seal_sha256"]
    for filename, expected in outs["files"].items():
        assert sha(engine_dir / filename) == expected, filename

    support = ROOT / "logs/remaining4-calibration-delivery"
    calibration = json.loads((support / "saved-workbook-verification.json").read_text())
    assert sha(calibration["output"]) == calibration["sha256"]
    inputs = json.loads((support / "report-inputs.json").read_text())
    for binding in inputs["bindings"]:
        assert sha(binding["path"]) == binding["sha256"]
    receipt = {
        "created_at": now,
        "annual_original_date_audit": {
            "sealed_files_verified_N": len(seal["files"]),
            "input_and_child_metadata_bindings_verified_N": len(metadata["inputs"]) + len(metadata["entries"]),
            "new_original_dates": 20,
            "prior_31_status_preserved_not_reaudited_here": True,
            "metadata_sha256": sha(annual_dir / "metadata.json"),
            "integration_agent": "/root/annual_metadata_integrate_sol",
        },
        "annual_engine": {
            "input_bindings_verified_N": engine_inputs_n,
            "output_bindings_verified_N": len(outs["files"]),
            "engine_sha256": sha(engine_dir / "metrics_engine.py"),
            "sealed_controls_are_author_control_evidence_only": True,
            "independent_audit_agent": "/root/annual_engine_independent_audit_sol",
            "independent_audit_finding": "census-parent source-year null can cause unjustified empty-year N=0 and complete annual membership claims",
            "status": "candidate_with_confirmed_independent_counterexample_not_released",
            "actual_project_year_results_computed": False,
        },
        "remaining4_calibration": {
            **calibration,
            "input_bindings_verified_N": len(inputs["bindings"]),
            "human_response_received": False,
            "workbook_labels_blank_at_reception": True,
            "native_png_renderer_image_visible": False,
            "saved_xlsx_embedded_original_image_bytes_verified": True,
            "authoring_and_saved_workbook_checks_completed": True,
            "known_originals_and_raw_predictions_unchanged": True,
        },
        "previous_goal_turn_classification": "progress",
        "formal_acceptance": False,
        "final_manuscript_started": False,
    }
    target = ROOT / "logs/root-annual-and-remaining4-delivery-reception-20261010.json"
    with target.open("x") as f:
        f.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    progress_path = ROOT / "progress.json"
    with (support / "progress-pre-current-integration.json").open("xb") as f:
        f.write(progress_path.read_bytes())
    progress = json.loads(progress_path.read_text())
    progress["remaining4_calibration_delivery_actual"] = receipt["remaining4_calibration"]
    progress["uniform77_disagreement_audit_actual"]["remaining_targeted_workbook"] = str(Path(calibration["output"]).relative_to(ROOT))
    progress["annual_original_date_audit_reception_actual"] = receipt["annual_original_date_audit"]
    progress["annual_engine_candidate_reception_actual"] = receipt["annual_engine"]
    progress["department_year_conclusion_requirement_actual"]["strict_publication_dates_pending_entries_N"] = 0
    progress["department_year_conclusion_requirement_actual"]["integrated_51_source_year_mapping_status"] = "in_progress_not_yet_received"
    progress["parallel_tasks_current_finite"].update({
        "rule_request_routing_repair_sol": "running: isolated candidate, constructed inputs only, no real-cohort rerun",
        "annual_engine_independent_audit_sol": "running: confirmed source-year-null counterexample, isolated correction candidate",
        "annual_metadata_integrate_sol": "running: source entries and no-label full-frame year mapping",
    })
    progress["current_goal_turn_classification"] = {"classification": "progress", "registered_at": now, "previous_turn": "progress", "evidence": [str(target.relative_to(ROOT)), "logs/remaining4-calibration-delivery/saved-workbook-verification.json"], "formal_acceptance": False, "phase7_full_manuscript_started": False}
    progress["last_integration_at"] = now
    progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"receipt": str(target), "annual_seal_files_verified": len(seal["files"]), "engine_seal_outputs_verified": len(outs["files"]), "human_4_received": False, "formal_acceptance": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
