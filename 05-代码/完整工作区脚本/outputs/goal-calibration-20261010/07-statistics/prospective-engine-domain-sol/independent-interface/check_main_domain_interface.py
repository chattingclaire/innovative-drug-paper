#!/usr/bin/env python3
"""Run new/old engine APIs on constructed toys only, never real input files.

The imported engine files are source-only. Bytecode writes are disabled. The
only data read is the adjacent independent toy fixture. All output stays here.
"""
import sys
sys.dont_write_bytecode = True
import copy
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load_source(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def output(state, dimensions):
    if state == "execution_failure":
        return {"status": "execution_failure", "labels": None}
    label = None if state == "null" else int(state)
    return {"status": "completed", "labels": {d: label for d in dimensions}}


def payload(base, dimensions):
    design = copy.deepcopy(base["design"])
    if "domain_N" in design:
        design["domain_population_N"] = design.pop("domain_N")
    design["kind"] = "stratified_srswor"
    design["sampling_unit"] = "source_unit"
    records = []
    for row in base["records"]:
        left, right = output(row["left"], dimensions), output(row["right"], dimensions)
        item = {"unit_id": row["id"], "stratum_id": row["stratum_id"],
                "outputs": {"A": left, "B": right, "rule": left, "LLM": left, "reference": right}}
        if "department" in row:
            item["department"] = row["department"]
        records.append(item)
    return {"data_role": "synthetic", "metadata": {"analysis_stage": "combined", "design": design,
            "scope": {"kind": "synthetic_toy", "population_N": sum(h["N"] for h in design["strata"])}}, "records": records}


def close(a, b, tolerance=1e-10):
    assert (a is None) == (b is None), (a, b)
    if a is not None:
        assert abs(float(a) - float(b)) <= tolerance, (a, b)


def strip_added_guard_note(value):
    if isinstance(value, dict):
        return {k: strip_added_guard_note(v) for k, v in value.items() if k != "guard_scope_note"}
    if isinstance(value, list):
        return [strip_added_guard_note(v) for v in value]
    return value


def run():
    new_source_hash = hashlib.sha256((ROOT / "metrics_engine.py").read_bytes()).hexdigest()
    old_source_hash = hashlib.sha256((ROOT / "old_engine_source_frozen.py").read_bytes()).hexdigest()
    oracle = load_source("independent_domain_oracle", HERE / "domain_toy_oracle.py")
    new = load_source("new_domain_engine_source_only", ROOT / "metrics_engine.py")
    old = load_source("old_engine_source_only", ROOT / "old_engine_source_frozen.py")
    fixture = json.loads((HERE / "domain-toy-cases.json").read_text())
    interface_checks = []
    for case in fixture["validation_cases"]:
        toy = payload(oracle.mutated(fixture["base"], case["mutation"]), new.DIMS)
        try:
            new.prepare(toy)
            accepted, error = True, None
        except new.DataError as e:
            accepted, error = False, str(e)
        assert accepted == case["accepted"], (case["id"], accepted)
        interface_checks.append({"id": case["id"], "accepted": accepted, "pass": True, "error": error})
    base = payload(fixture["base"], new.DIMS)
    extra = []
    def variant(identifier, fn, accepted):
        toy = copy.deepcopy(base)
        fn(toy)
        try:
            new.prepare(toy)
            actual, error = True, None
        except new.DataError as e:
            actual, error = False, str(e)
        assert actual == accepted, (identifier, actual)
        extra.append({"id": identifier, "accepted": actual, "pass": True, "error": error})
    variant("legal_two_domain_marker", lambda p: p["metadata"]["design"].update(domain_partition="remaining_exposed"), True)
    variant("illegal_partition_marker", lambda p: p["metadata"]["design"].update(domain_partition="other"), False)
    variant("nonstring_domain", lambda p: p["metadata"]["design"]["strata"][0].update(domain=["remaining"]), False)
    variant("null_declared_domain_N", lambda p: p["metadata"]["design"].update(domain_population_N=None), False)
    variant("named_population_N_float", lambda p: p["metadata"]["scope"].update(population_N=14.0), False)
    variant("wrong_full4481_named_capacity", lambda p: p["metadata"]["scope"].update(kind="full_4481_audit"), False)
    variant("wrong_remaining1444_named_capacity", lambda p: p["metadata"]["scope"].update(kind="remaining_1444"), False)
    variant("per_domain_protocol_override", lambda p: p["metadata"].update(domain_protocols={}), False)
    for location in ("payload", "metadata", "design"):
        for field in ("domain_inputs", "domain_input_seals", "domain_artifact_seals", "domain_protocols"):
            if location == "metadata" and field == "domain_protocols":
                continue
            def override(p, location=location, field=field):
                target = p if location == "payload" else p["metadata"] if location == "metadata" else p["metadata"]["design"]
                target[field] = {}
            variant(location + "_" + field + "_override", override, False)
    def ambiguous_missing_department(p):
        p["metadata"]["design"]["strata"][0]["department"] = "UNSPECIFIED"
        p["records"][0].pop("department")
        p["records"][1]["department"] = "UNSPECIFIED"
    variant("named_missing_row_department_even_if_default_matches_frozen_value", ambiguous_missing_department, False)
    variant("row_domain_override_prohibited", lambda p: p["records"][0].update(domain="exposed"), False)
    one_domain = payload(oracle.mutated(fixture["base"], "only_remaining"), new.DIMS)
    one_domain["metadata"]["design"]["domain_partition"] = "remaining_exposed"
    try:
        new.prepare(one_domain)
    except new.DataError:
        extra.append({"id": "two_domain_marker_with_single_domain", "accepted": False, "pass": True})
    else:
        raise AssertionError("A remaining_exposed marker cannot describe only remaining")
    count = [0]
    generate = new.rao_wu_weights
    def counting_weights(*args, **kwargs):
        count[0] += 1
        return generate(*args, **kwargs)
    new.rao_wu_weights = counting_weights
    try:
        actual = new.analyze(base, replicates=128, seed=12345, guard_mode="joint_table")
    finally:
        new.rao_wu_weights = generate
    assert count[0] == 1 == actual["design"]["replicate_weight_generation_count"]
    independent = oracle.summaries(oracle.prepare_contract(fixture["base"]))
    assert set(actual["analysis_scopes"]) == set(independent)
    shared_hash = actual["design"]["shared_replicate_weights_sha256"]
    checked_masks = []
    for name, expected in independent.items():
        scope = actual["analysis_scopes"][name]
        assert scope["assigned_n"] == expected["assigned_n"]
        close(scope["weighted_assigned_total"], expected["assigned_weight"])
        assert scope["full_census_no_sampling_error"] == expected["census"]
        assert scope["shared_replicate_weights_sha256"] == shared_hash
        for endpoint in scope["replicate_assigned_total_range"]:
            close(endpoint, expected["assigned_weight"])
        comp = actual["comparisons"]["rule_vs_reference"]["domains"][name]["S"]
        assert comp["raw"]["comparable_binary_total"] == expected["pair_n"]
        close(comp["design_weighted"]["comparable_binary_total"], expected["pair_weight"])
        assert [Fraction(x) for x in comp["weighted_four_exact_fractions"]] == expected["weighted_four"]
        for metric in ("kappa", "Precision", "Recall", "F1"):
            close(comp["design_weighted_metrics"][metric], expected[metric])
        # All assigned weight is retained even when the comparable domain is empty.
        close(comp["design_weighted"]["assigned_total"], expected["assigned_weight"])
        attention = actual["attention"]["rule"][name]["S"]
        assert attention["raw"]["assigned_n"] == expected["assigned_n"]
        close(attention["design_weighted"]["assigned_weight_total"], expected["assigned_weight"])
        guard = comp["finite_guard"]
        assert sum(h["N"] for h in guard["strata"]) == scope["population_N"]
        assert sum(h["n"] for h in guard["strata"]) == scope["assigned_n"]
        assert guard["metric_projection_implemented"] is False
        assert actual["numeric_targets_by_analysis_scope"][name]["formal_acceptance"] is False
        checked_masks.append({"scope": name, "assigned_n": scope["assigned_n"], "assigned_weight": scope["weighted_assigned_total"],
                              "pair_n": expected["pair_n"], "pair_weight": str(expected["pair_weight"]), "census": expected["census"], "pass": True})
    assert actual["project_review"]["formal_acceptance"] is False
    assert actual["project_review"]["metadata_cannot_authenticate_human_identity_on_its_own"] is True
    # Explicit empty cross-products must be omitted rather than supplied as zero rates.
    empty_cross = copy.deepcopy(base)
    for h in empty_cross["metadata"]["design"]["strata"]:
        if h["domain"] == "exposed": h["department"] = "Gamma"
    for row in empty_cross["records"]:
        if row["stratum_id"].startswith("toy-e-"): row["department"] = "Gamma"
    scoped = new.analysis_scopes(new.prepare(empty_cross))
    assert "domain:remaining|department:Gamma" not in scoped
    assert "domain:exposed|department:Alpha" not in scoped
    assert "domain:exposed|department:Beta" not in scoped
    # Legacy compatibility: identical old keys/tables/metrics/intervals on the same toys.
    legacy_checks = []
    for mode in ("normal", "ambiguous_frozen_department", "global_census", "nonprobability"):
        legacy = payload(oracle.mutated(fixture["base"], "legacy"), new.DIMS)
        if mode == "ambiguous_frozen_department": legacy["metadata"]["design"]["strata"][0].pop("department")
        if mode == "global_census":
            for h in legacy["metadata"]["design"]["strata"]: h["N"] = h["n"]
            legacy["metadata"]["scope"]["population_N"] = 8
            legacy["metadata"]["design"]["strata"][0].pop("department")
        if mode == "nonprobability":
            legacy["metadata"]["design"]["kind"] = "nonprobability"
        before = old.analyze(legacy, replicates=128, seed=12345, guard_mode="single_category")
        after = new.analyze(legacy, replicates=128, seed=12345, guard_mode="single_category")
        for key in ("comparisons", "numeric_targets", "project_review", "attention", "department_attention_difference_bounds", "scope_metadata", "identity_and_freeze_metadata"):
            assert strip_added_guard_note(before[key]) == strip_added_guard_note(after[key]), (mode, key)
        for key, value in before["design"].items(): assert after["design"][key] == value, (mode, key)
        assert after["design"]["named_domain_partition"] is False
        assert all(not key.startswith("domain:") for key in after["analysis_scopes"])
        legacy_checks.append({"case": mode, "old_existing_numerical_and_status_fields_identical": True})
    # Full flag passes while one separate scope flag fails: no implicit averaging/AND.
    numeric = fixture["independent_numeric_flag_case"]
    strata, rows = [], []
    for domain in ("remaining", "exposed"):
        cells = numeric[domain + "_four"]
        number = sum(cells)
        strata.append({"id": "toy-flag-" + domain, "domain": domain, "department": "Flags", "N": number, "n": number})
        for (left, right), n in zip((("1", "1"), ("1", "0"), ("0", "1"), ("0", "0")), cells):
            for _ in range(n):
                rows.append({"id": "toy-flag-only-" + str(len(rows)), "stratum_id": "toy-flag-" + domain,
                             "department": "Flags", "left": left, "right": right})
    flag_payload = payload({"design": {"strata": strata}, "records": rows}, new.DIMS)
    flag_result = new.analyze(flag_payload, replicates=32, seed=12345, guard_mode="none")
    flags = flag_result["numeric_targets_by_analysis_scope"]
    assert flags["ALL"]["all_numerical_point_targets_met"] is True
    assert flags["domain:remaining"]["all_numerical_point_targets_met"] is False
    assert flags["domain:exposed"]["all_numerical_point_targets_met"] is True
    assert flag_result["project_review"]["all_numerical_point_targets_met"] is True
    assert flag_result["project_review"]["formal_acceptance"] is False
    # A labels-free metadata UNIT TEST demonstrates self-asserted identity/seals cannot grant acceptance.
    asserted = {"role": "sealed_project", "kind": "stratified_srswor", "population_N": 4481,
                "meta": {"scope": {"kind": "full_4481_audit", "frame_ids_sha256": "0" * 64},
                         "identities": {"A": {"kind": "human", "verified": True, "independent_initial": True, "identity_code": "TOY-A"},
                                        "B": {"kind": "human", "verified": True, "independent_initial": True, "identity_code": "TOY-B"},
                                        "reference": {"kind": "human_adjudication", "credible": True, "blinded_to_machines": True, "identity_code": "TOY-REF"}},
                         "input_seals": {m: {"sealed": True, "sha256": "0" * 64} for m in new.METHODS},
                         "artifact_seals": {m: {"sealed": True, "sha256": "0" * 64} for m in ("common_manual", "common_materials", "design", "rule_protocol", "LLM_protocol")},
                         "freeze_attestations": {m: True for m in ("common_manual", "common_materials", "design_before_answers", "initial_submissions_before_discussion", "reference_before_machine_comparison", "final_rule_and_LLM_before_test_feedback")},
                         "identity_and_source_evidence_reviewed": True}}
    review = new.review_eligibility(asserted, True)
    assert review["metadata_attestations_complete_for_project_review"] is True
    assert review["formal_acceptance"] is False and review["metadata_cannot_authenticate_human_identity_on_its_own"] is True
    assert new_source_hash == hashlib.sha256((ROOT / "metrics_engine.py").read_bytes()).hexdigest(), "New source changed during execution; repeat against final snapshot"
    assert old_source_hash == hashlib.sha256((ROOT / "old_engine_source_frozen.py").read_bytes()).hexdigest(), "Old source changed during execution"
    return {"status": "passed_main_domain_engine_on_independent_synthetic_interface_cases",
            "engine_sha256": new_source_hash,
            "old_engine_sha256": old_source_hash,
            "source_hash_stable_during_dynamic_checks": True,
            "input_files_read": ["domain-toy-cases.json"], "real_ID_draws": 0, "real_predictions_read": 0,
            "real_reference_labels_created": 0, "source_bodies_read": 0,
            "interface_validation_cases": interface_checks, "extra_named_metadata_cases": extra,
            "mask_and_weight_checks": checked_masks, "replicate_weight_generation_call_count": count[0],
            "all_scope_replicate_weights_sha256_equal": True,
            "empty_intersections_omitted": True, "legacy_compatibility_checks": legacy_checks,
            "separate_numeric_flags": {"ALL": True, "remaining": False, "exposed": True, "formal_acceptance": False},
            "labels_free_metadata_assertion_unit_test": review, "formal_acceptance": False}


if __name__ == "__main__":
    results = run()
    target = HERE / "main-domain-interface-results.json"
    target.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": results["status"], "metadata_cases": len(results["interface_validation_cases"]) + len(results["extra_named_metadata_cases"]), "mask_checks": len(results["mask_and_weight_checks"]), "legacy_cases": len(results["legacy_compatibility_checks"]), "output": str(target)}, ensure_ascii=False))
