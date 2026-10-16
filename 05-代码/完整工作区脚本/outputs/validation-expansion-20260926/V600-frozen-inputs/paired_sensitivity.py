"""Five predeclared secondary operationalizations for paired V600 labels.

No study I/O or local statistical imports occur on import or in analyze().
API: analyze(payload, archive, *, paired_metrics=verified_frozen_module).
The caller must first complete paired_holdout_results.assemble and must inject
the hash-verified paired_version_metrics module with its verified survey_metrics
dependency. This pure module checks original ID/label alignment; it does not
replace the bridge's freeze, submission, blinding or frame verification.

The five transformations mirror the inspected policy_statistics.sensitivity_input
branches (lines 201-241): retain all units/weights/other dimensions, alter only
the relevant positive label when its OWN subtypes meet the declared criterion.
Pending remains pending. Missing, unknown, duplicate or inconsistent metadata
makes that scenario explicitly not_calculable, without partial recoding or deletion.

Every complete scenario calls the injected actual paired engine. Only the affected
dimension's five comparisons and A/C paired differences are returned. These are
alternative_operationalization_secondary results for the supplied final finite
candidate frame. They cannot replace primary results or establish full-4924 rankings.

This component has NOT been run on the new research sample. CLI only supports
--synthetic-qa --output NEW.json; there is no real-data CLI or implicit input path.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

DIMS = ("S", "E", "Ec", "I", "F")
COLUMNS = ("A", "C", "baseline", "candidate")
PENDING = "待定"
SEED = 2026092606
COMPARISONS = ("A_vs_C", "baseline_vs_A", "baseline_vs_C", "candidate_vs_A", "candidate_vs_C")
ALLOWED = {"S": {"quality_safety", "other_safety"},
           "I": {"attribute", "research_support", "qualification_advantage"},
           "F": {"access", "affordability", "clinical_management", "dimension_information"}}
SCENARIOS = (
    {"id": "safety_without_quality_only", "dimension": "S", "remove_if_subtypes_within": ["quality_safety"],
     "definition": "S仅有药品质量安全依据时1→0；同时有其他安全依据保留1。AI quality_only移除，quality_and_other或no_quality_basis保留。"},
    {"id": "innovation_without_qualification_only", "dimension": "I", "remove_if_subtypes_within": ["qualification_advantage"],
     "definition": "I仅有qualification_advantage时1→0；同时有attribute或research_support保留1。"},
    {"id": "fairness_without_management_only", "dimension": "F", "remove_if_subtypes_within": ["clinical_management"],
     "definition": "F仅有clinical_management时1→0；存在其他F子型保留1。"},
    {"id": "fairness_without_information_only", "dimension": "F", "remove_if_subtypes_within": ["dimension_information"],
     "definition": "F仅有dimension_information时1→0；存在其他F子型保留1。"},
    {"id": "fairness_access_affordability_only", "dimension": "F", "remove_if_subtypes_within": ["clinical_management", "dimension_information"],
     "definition": "F=1且子型全属clinical_management和/或dimension_information时1→0；只要含access或affordability即保留1。"},
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def serialized(value):
    """Preserve dict/list order when checking that callers' inputs were untouched."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def label_map(value, name):
    require(isinstance(value, dict) and set(value) == set(DIMS), name + ": exact five dimensions required")
    require(all((type(v) is int and v in (0, 1)) or (type(v) is str and v == PENDING) for v in value.values()),
            name + ": literal 0/1/待定 required")
    return dict(value)


def indexed(rows, key, name):
    require(isinstance(rows, list), name + ": list required")
    out = {}
    for row in rows:
        require(isinstance(row, dict), name + ": row object required")
        value = row.get(key)
        require(isinstance(value, str) and value and value not in out, name + ": missing/duplicate ID")
        out[value] = row
    return out


def machine_original_labels(record, name):
    require(all(isinstance(record.get(k), str) and record[k].strip()
                for k in ("judgement_status", "input_assessment_status")),
            name + ": nonempty machine status fields required")
    codes = record.get("labels")
    require(isinstance(codes, dict) and set(codes) == set(DIMS), name + ": exact five machine labels required")
    if any(codes[d] is None for d in DIMS):
        require(all(codes[d] is None for d in DIMS) and record.get("judgement_status") == "undetermined"
                and record.get("input_assessment_status") in {"context_insufficient", "text_problem"},
                name + ": unauthorized partial/null machine labels")
        return {d: PENDING for d in DIMS}
    require(all(type(codes[d]) is int and codes[d] in (0, 1) for d in DIMS)
            and record.get("judgement_status") != "undetermined"
            and record.get("input_assessment_status") not in {"context_insufficient", "text_problem"},
            name + ": inconsistent machine binary labels")
    return dict(codes)


def align_originals(payload, archive):
    """Join by blind ID and review_id, validating original labels in all columns."""
    require(isinstance(payload, dict) and isinstance(archive, dict), "Payload/archive objects required")
    rows = indexed(payload.get("rows"), "id", "payload")
    require(rows, "Empty payload")
    originals = {c: {} for c in COLUMNS}
    submissions = archive.get("raw_coder_submissions")
    require(isinstance(submissions, dict) and submissions, "Original coder submissions required")
    for path, document in submissions.items():
        require(isinstance(document, dict) and document.get("coder") in {"A", "C"}, "Archived coder missing/unknown")
        coder = document["coder"]
        require(isinstance(path, str) and path.startswith("agent-" + coder + "/"), "Archived coder/path mismatch")
        for key, record in indexed(document.get("rows"), "id", "archived coder batch").items():
            require(key not in originals[coder], "Duplicate archived coder ID across batches")
            originals[coder][key] = record
    mapping_doc = archive.get("sampling_manifest_original")
    require(isinstance(mapping_doc, dict), "Original sampling manifest required")
    mapping = indexed(mapping_doc.get("rows"), "id", "archive mapping")
    indexed(mapping_doc["rows"], "review_id", "archive original IDs")
    require(set(mapping) == set(rows), "Archive mapping/payload ID mismatch")
    versions = archive.get("selected_machine_records_by_version_and_blind_id")
    require(isinstance(versions, dict) and set(versions) == {"baseline", "candidate"}, "Both original machine versions required")
    for column in ("baseline", "candidate"):
        require(isinstance(versions[column], dict) and set(versions[column]) == set(rows), "Machine/payload ID mismatch: " + column)
        originals[column] = versions[column]
        for key, record in originals[column].items():
            require(isinstance(record, dict) and record.get("id") == mapping[key]["review_id"], "Machine review_id/blind ID mismatch")
    normalized = indexed(archive.get("normalized_rows_without_generated_reference"), "id", "archived normalized rows")
    require(set(normalized) == set(rows), "Archived normalized/payload ID mismatch")
    # Bind statistical design as well as labels to the assembled archive.
    # A coherent but accidentally changed N_h would otherwise pass the metric
    # engine's internal design checks and silently alter weights and FPC.
    plan = mapping_doc.get("plan")
    require(isinstance(plan, dict) and isinstance(plan.get("strata"), dict), "Archived sampling plan required")
    design = indexed(payload.get("strata"), "stratum", "payload strata")
    require(set(design) == set(plan["strata"]), "Payload/archive stratum set mismatch")
    require(payload.get("population_N") == plan.get("N_star") and len(rows) == plan.get("n"),
            "Payload/archive population or sample size mismatch")
    for h, spec in design.items():
        require(all(spec.get(k) == plan["strata"][h].get(k) for k in ("N_h", "n_h")),
                "Payload/archive stratum design mismatch: " + h)
    for key, row in rows.items():
        require(row == normalized[key], "Payload/archive normalized row mismatch: " + key)
        require(row.get("stratum") in design and all(row.get(k) == mapping[key].get(k)
                for k in ("stratum", "N_h", "n_h")), "Payload/archive sampling row design mismatch: " + key)
    for column in COLUMNS:
        require(set(originals[column]) == set(rows), "Original/payload ID mismatch: " + column)
        for key in sorted(rows):
            actual = label_map(rows[key].get(column), "payload " + column + "/" + key)
            original = (label_map(originals[column][key].get("labels"), "archived AI labels") if column in {"A", "C"}
                        else machine_original_labels(originals[column][key], "archived " + column + "/" + key))
            require(actual == original, "Original archive labels differ from payload: " + column + "/" + key)
            require(label_map(normalized[key].get(column), "archived normalized labels") == actual,
                    "Archived normalized labels differ from payload: " + column + "/" + key)
    return rows, originals


def subtype_metadata(record, column, dimension, code):
    """Return normalized source types or a precise scenario-specific problem."""
    if dimension == "S" and column in {"A", "C"}:
        field = "safety_quality_basis"
        if field not in record:
            return None, field, "missing safety_quality_basis"
        value = record[field]
        allowed = {"no_quality_basis"} if code == 0 else {"undetermined"} if code == PENDING else {"quality_only", "quality_and_other", "no_quality_basis"}
        if not isinstance(value, str) or value not in allowed:
            return None, field, "unknown or label-inconsistent safety_quality_basis"
        if code != 1:
            return set(), field, None
        return {"quality_only": {"quality_safety"}, "quality_and_other": {"quality_safety", "other_safety"},
                "no_quality_basis": {"other_safety"}}[value], field, None
    field = {"S": "safety_subtypes", "I": "innovation_subtypes", "F": "fairness_subtypes"}[dimension]
    if field not in record:
        return None, field, "missing subtype metadata"
    value = record[field]
    if not isinstance(value, list) or any(not isinstance(x, str) or x not in ALLOWED[dimension] for x in value):
        return None, field, "subtypes must be a list of known values"
    if len(value) != len(set(value)):
        return None, field, "duplicate subtype metadata"
    if bool(value) != (code == 1):
        return None, field, "nonempty subtypes required exactly for a positive label"
    if dimension == "I" and column in {"baseline", "candidate"}:
        expected = "complete" if code == 1 else "undetermined" if code == PENDING else "not_applicable"
        if record.get("innovation_subtype_status") != expected:
            return None, "innovation_subtype_status", "missing, unresolved or label-inconsistent innovation attribution status"
        if "innovation_unclassified_evidence" not in record or record["innovation_unclassified_evidence"] != []:
            return None, "innovation_unclassified_evidence", "missing or unresolved innovation attribution evidence"
    return set(value), field, None


def summaries(rows, dimension):
    """Recompute positive counts and reference-positive denominators after recoding."""
    result = {"columns": {}, "comparison_reference_positive_denominators": {}, "paired_joint_reference_positive_denominators": {}}
    def weighted(ids):
        return sum(rows[k]["N_h"] / rows[k]["n_h"] for k in ids)
    for column in COLUMNS:
        positive = [k for k in sorted(rows) if rows[k][column][dimension] == 1]
        pending = [k for k in sorted(rows) if rows[k][column][dimension] == PENDING]
        result["columns"][column] = {"raw_positive_n": len(positive), "weighted_positive_total": weighted(positive),
                                     "raw_pending_n": len(pending), "weighted_pending_total": weighted(pending)}
    for left, right in (("A", "C"), ("baseline", "A"), ("baseline", "C"), ("candidate", "A"), ("candidate", "C")):
        positive = [k for k in sorted(rows) if rows[k][right][dimension] == 1 and rows[k][left][dimension] != PENDING]
        result["comparison_reference_positive_denominators"][left + "_vs_" + right] = {
            "right_column": right, "raw_n": len(positive), "weighted_total": weighted(positive),
            "scope": "positive right-side label among this comparison's jointly definite rows"}
    for reference in ("A", "C"):
        positive = [k for k in sorted(rows) if rows[k][reference][dimension] == 1
                    and rows[k]["baseline"][dimension] != PENDING and rows[k]["candidate"][dimension] != PENDING]
        result["paired_joint_reference_positive_denominators"][reference] = {"raw_n": len(positive), "weighted_total": weighted(positive),
            "scope": "positive reference among baseline, candidate and this reference jointly definite rows"}
    return result


def analyze(payload, archive, *, paired_metrics):
    """Use an explicitly supplied, caller-verified frozen engine; never import one."""
    before_payload, before_archive = serialized(payload), serialized(archive)
    require(tuple(paired_metrics.DIMS) == DIMS and type(paired_metrics.SEED) is int and paired_metrics.SEED == SEED
            and paired_metrics.REPLICATES == 2000, "Expected frozen paired metric contract/seed required")
    rows, originals = align_originals(payload, archive)
    # Statistical payload validation is complementary to, not a substitute for, the bridge.
    paired_metrics.prepare(copy.deepcopy(payload))
    scenarios = {}
    for definition in SCENARIOS:
        dimension = definition["dimension"]
        issues, metadata = [], {}
        for column in COLUMNS:
            for key in sorted(rows):
                value, field, problem = subtype_metadata(originals[column][key], column, dimension, rows[key][column][dimension])
                if problem:
                    issues.append({"id": key, "column": column, "dimension": dimension, "field": field,
                                   "reason": problem, "original_label": rows[key][column][dimension]})
                else:
                    metadata[column, key] = (value, field)
        item = {"analysis_kind": "alternative_operationalization_secondary", "definition": copy.deepcopy(definition),
                "affected_dimension": dimension, "changes_by_column": {c: [] for c in COLUMNS},
                "actual_changed_ids_by_column": {c: [] for c in COLUMNS}, "issues": issues,
                "pending_preserved": True, "all_units_and_weights_retained": True}
        if issues:
            item.update(status="not_calculable", transformation_applied=False, statistics=None,
                        reason="Required subtype metadata is missing, unknown, unresolved or inconsistent; no partial scenario is analyzed.")
            scenarios[definition["id"]] = item
            continue
        transformed = copy.deepcopy(payload)
        changed_rows = indexed(transformed["rows"], "id", "transformed rows")
        removed = set(definition["remove_if_subtypes_within"])
        for column in COLUMNS:
            for key in sorted(rows):
                types_, field = metadata[column, key]
                if rows[key][column][dimension] == 1 and types_ <= removed:
                    changed_rows[key][column][dimension] = 0
                    item["changes_by_column"][column].append({"id": key, "dimension": dimension, "before": 1, "after": 0,
                        "metadata_field": field, "original_metadata": copy.deepcopy(originals[column][key][field]),
                        "normalized_subtypes": sorted(types_)})
                    item["actual_changed_ids_by_column"][column].append(key)
        # Prove the transformation changed only the declared label cells.
        allowed_cells = {(c, x["id"]) for c in COLUMNS for x in item["changes_by_column"][c]}
        for key in rows:
            restored = copy.deepcopy(changed_rows[key])
            for column in COLUMNS:
                if (column, key) in allowed_cells:
                    restored[column][dimension] = rows[key][column][dimension]
            require(restored == rows[key], "Transformation changed an undeclared field, other dimension or weight")
        require(transformed["strata"] == payload["strata"] and transformed["population_N"] == payload["population_N"], "Transformation changed design")
        transformed_before = serialized(transformed)
        full = paired_metrics.analyze(transformed)
        require(serialized(transformed) == transformed_before, "Injected statistics mutated scenario input")
        require(full.get("bootstrap", {}).get("seed") == SEED and full.get("reference_generated") is False,
                "Statistics seed/reference contract changed")
        require(full.get("sample_n") == len(rows) and full.get("population_N") == payload["population_N"], "Statistics changed row count/design")
        require(set(full.get("comparisons", {})) == set(COMPARISONS) and set(full.get("paired_differences", {})) == {"A", "C"},
                "Statistics comparison inventory changed")
        selected = {k: copy.deepcopy(full[k]) for k in ("sample_n", "population_N", "all_census", "bootstrap", "difference_sign", "difference_scope")}
        selected["comparisons"] = {name: {"left": full["comparisons"][name]["left"], "right": full["comparisons"][name]["right"],
            "dimensions": {dimension: copy.deepcopy(full["comparisons"][name]["dimensions"][dimension])}} for name in COMPARISONS}
        selected["paired_differences"] = {c: {"reference": c, "dimensions": {dimension: copy.deepcopy(full["paired_differences"][c]["dimensions"][dimension])}} for c in ("A", "C")}
        item.update(status="completed", transformation_applied=True, statistics=selected,
                    positive_and_denominator_counts=summaries(changed_rows, dimension), other_dimensions_unchanged=True)
        scenarios[definition["id"]] = item
    require(serialized(payload) == before_payload and serialized(archive) == before_archive, "Original input bytes changed")
    return {"status": "alternative_operationalization_secondary", "scenarios": scenarios,
            "scope": "Only the supplied final finite validation frame; not full-4924 departmental rankings or future policies.",
            "primary_statistics_computed_or_overwritten": False, "original_payload_and_archive_serialization_unchanged": True,
            "dependency_contract": "Caller supplies hash-verified frozen paired metrics and survey dependency; this function does not certify those hashes.",
            "bootstrap_seed": SEED, "sample_n": len(rows), "population_N": payload["population_N"],
            "interpretation": ["Each column uses its own original subtype metadata; no shared subtype or consensus reference is inferred.",
                "All original units, design weights and pending labels remain; only predeclared positive dimension labels may change to zero.",
                "Affected positive counts and comparison-specific/reference-joint positive denominators are recomputed.",
                "Secondary operationalizations cannot replace the main analysis or establish that the original full-corpus ranking is robust."]}


def _synthetic_modules(raw_survey, raw_paired):
    """Code-only synthetic runner with an explicitly intercepted survey dependency."""
    import builtins
    import types
    allowed = {"__future__", "copy", "json", "re", "itertools", "hashlib", "math", "pathlib", "numpy"}
    def load(raw, name, dependencies):
        def importer(module_name, globals=None, locals=None, fromlist=(), level=0):
            require(level == 0, "Relative synthetic import forbidden")
            if module_name in dependencies: return dependencies[module_name]
            require(module_name.split(".")[0] in allowed, "Unfrozen local synthetic dependency: " + module_name)
            return builtins.__import__(module_name, globals, locals, fromlist, level)
        module = types.ModuleType("_synthetic_frozen_" + name)
        module.__file__ = "<synthetic frozen " + name + ".py>"
        module.__dict__["__builtins__"] = {**vars(builtins), "__import__": importer}
        exec(compile(raw, module.__file__, "exec"), module.__dict__)
        return module
    survey = load(raw_survey, "survey_metrics", {})
    paired = load(raw_paired, "paired_version_metrics", {"survey_metrics": survey})
    require(paired.base is survey, "Synthetic survey dependency was not intercepted")
    return paired


def synthetic_inputs():
    """Invented eight-row noncensus design; no study file or real judgement."""
    s = ["quality_only", "quality_and_other", "no_quality_basis", "quality_only", "no_quality_basis", "quality_only"]
    i = [["qualification_advantage"], ["qualification_advantage", "attribute"], ["research_support"], ["attribute"],
         ["qualification_advantage", "research_support"], ["qualification_advantage"]]
    f = [["clinical_management"], ["dimension_information"], ["clinical_management", "dimension_information"],
         ["access", "clinical_management"], ["affordability", "dimension_information"], ["access", "affordability"]]
    rows, mapping = [], []
    submissions = {f"agent-{c}/结果-01.json": {"coder": c, "rows": []} for c in ("A", "C")}
    machines = {c: {} for c in ("baseline", "candidate")}
    for n in range(8):
        key, original = f"V600-{n + 1:04d}", "fiction-" + str(n)
        codes = {d: (PENDING if n == 6 else 0 if n == 7 else 1 if d in {"S", "I", "F"} else n % 2) for d in DIMS}
        row = {"id": key, "stratum": "fiction", "N_h": 16, "n_h": 8, **{c: dict(codes) for c in COLUMNS}}
        rows.append(row); mapping.append({"id": key, "review_id": original, "stratum": "fiction", "N_h": 16, "n_h": 8})
        for column in COLUMNS:
            quality = "undetermined" if n == 6 else "no_quality_basis" if n == 7 else s[n]
            innovation, fairness = ([] if n >= 6 else list(i[n])), ([] if n >= 6 else list(f[n]))
            if n == 3 and column in {"C", "candidate"}: quality = "quality_and_other"
            if n == 0 and column == "candidate": innovation.append("attribute")
            if n == 2 and column == "C": fairness = ["clinical_management"]
            record = {"id": key if column in {"A", "C"} else original, "labels": dict(codes),
                      "innovation_subtypes": innovation, "fairness_subtypes": fairness}
            if column in {"A", "C"}:
                record["safety_quality_basis"] = quality
                submissions[f"agent-{column}/结果-01.json"]["rows"].append(record)
            else:
                record.update(safety_subtypes=[] if n >= 6 else ["quality_safety"] if quality == "quality_only" else
                              ["quality_safety", "other_safety"] if quality == "quality_and_other" else ["other_safety"],
                              innovation_subtype_status="undetermined" if n == 6 else "not_applicable" if n == 7 else "complete",
                              innovation_unclassified_evidence=[], judgement_status="undetermined" if n == 6 else "rule_prediction",
                              input_assessment_status="context_insufficient" if n == 6 else "sufficient")
                if n == 6: record["labels"] = {d: None for d in DIMS}
                machines[column][key] = record
    payload = {"strata": [{"stratum": "fiction", "N_h": 16, "n_h": 8}], "population_N": 16, "rows": rows,
               "coders": {c: {"kind": "AI", "description": "Synthetic AI fixture only"} for c in ("A", "C")},
               "baseline_info": {"version": "synthetic-old", "prediction_sha256": "a" * 64},
               "candidate_info": {"version": "synthetic-new", "prediction_sha256": "b" * 64}}
    archive = {"raw_coder_submissions": submissions, "selected_machine_records_by_version_and_blind_id": machines,
               "sampling_manifest_original": {"rows": mapping, "plan": {"N_star": 16, "n": 8,
                   "strata": {"fiction": {"N_h": 16, "n_h": 8}}}},
               "normalized_rows_without_generated_reference": copy.deepcopy(rows)}
    return payload, archive


def self_test():
    here = Path(__file__).resolve()
    code_paths = {"paired_sensitivity": here, "survey_metrics": here.with_name("survey_metrics.py"),
                  "paired_version_metrics": here.with_name("paired_version_metrics.py")}
    sources = {k: path.read_bytes() for k, path in code_paths.items()}
    metrics = _synthetic_modules(sources["survey_metrics"], sources["paired_version_metrics"])
    payload, archive = synthetic_inputs()
    original_p, original_a = serialized(payload), serialized(archive)
    primary = metrics.analyze(copy.deepcopy(payload)); primary_bytes = serialized(primary)
    output = analyze(payload, archive, paired_metrics=metrics)
    require(all(s["status"] == "completed" for s in output["scenarios"].values()), "Complete synthetic scenarios rejected")
    require(serialized(payload) == original_p and serialized(archive) == original_a and serialized(primary) == primary_bytes, "Original or primary metrics changed")
    expected = {
        "safety_without_quality_only": {"A": [1, 4, 6], "C": [1, 6], "baseline": [1, 4, 6], "candidate": [1, 6]},
        "innovation_without_qualification_only": {c: ([6] if c == "candidate" else [1, 6]) for c in COLUMNS},
        "fairness_without_management_only": {c: ([1, 3] if c == "C" else [1]) for c in COLUMNS},
        "fairness_without_information_only": {c: [2] for c in COLUMNS},
        "fairness_access_affordability_only": {c: [1, 2, 3] for c in COLUMNS}}
    for scenario, bycolumn in expected.items():
        item = output["scenarios"][scenario]
        for column, numbers in bycolumn.items():
            require(item["actual_changed_ids_by_column"][column] == [f"V600-{n:04d}" for n in numbers], "Wrong single/multiple subtype transformation")
            require(item["positive_and_denominator_counts"]["columns"][column]["raw_pending_n"] == 1, "Pending label changed")
        require(set(item["statistics"]["comparisons"]) == set(COMPARISONS), "Five comparisons missing")
        require(all(set(x["dimensions"]) == {item["affected_dimension"]} for x in item["statistics"]["comparisons"].values()), "Unrelated primary dimension retained")
        require(item["statistics"]["bootstrap"] == primary["bootstrap"], "Bootstrap seed/design changed")
    s_counts = output["scenarios"]["safety_without_quality_only"]["positive_and_denominator_counts"]
    require(s_counts["columns"]["A"]["raw_positive_n"] == 3 and s_counts["columns"]["A"]["weighted_positive_total"] == 6, "Positive counts not recalculated")
    require(s_counts["paired_joint_reference_positive_denominators"]["A"]["weighted_total"] == 6, "Reference positive denominator not recalculated")
    # Row order must not affect shared-bootstrap secondary outputs or ID joins.
    reversed_p, reversed_a = copy.deepcopy(payload), copy.deepcopy(archive)
    reversed_p["rows"].reverse()
    reversed_a["sampling_manifest_original"]["rows"].reverse()
    reversed_a["normalized_rows_without_generated_reference"].reverse()
    for doc in reversed_a["raw_coder_submissions"].values(): doc["rows"].reverse()
    require(analyze(reversed_p, reversed_a, paired_metrics=metrics) == output, "Row-order-dependent sensitivity result")
    # All affected dimensions invalid: the real engine must not be called for any scenario.
    invalid = copy.deepcopy(archive)
    ai = invalid["raw_coder_submissions"]["agent-A/结果-01.json"]["rows"]
    ai[0].pop("safety_quality_basis")
    ai[1]["innovation_subtypes"] = ["unknown"]
    ai[2]["fairness_subtypes"] = []
    failed = analyze(payload, invalid, paired_metrics=metrics)
    require(all(s["status"] == "not_calculable" and s["statistics"] is None and not s["transformation_applied"]
                and all(not ids for ids in s["actual_changed_ids_by_column"].values()) for s in failed["scenarios"].values()), "Invalid subtypes partially calculated")
    require(all(s["issues"] and all({"id", "column", "reason", "field"} <= set(i) for i in s["issues"]) for s in failed["scenarios"].values()), "Problem IDs/reasons missing")
    # Scenario metadata checks, including zero and pending contradictions.
    subtype_bad = [
        ({}, "A", "S", 1), ({"safety_quality_basis": "quality_only"}, "A", "S", 0),
        ({"safety_quality_basis": "no_quality_basis"}, "A", "S", PENDING),
        ({"safety_subtypes": ["quality_safety", "quality_safety"]}, "baseline", "S", 1),
        ({"safety_subtypes": ["unknown"]}, "baseline", "S", 1),
        ({"fairness_subtypes": ["access"]}, "A", "F", PENDING),
        ({"innovation_subtypes": ["qualification_advantage"], "innovation_subtype_status": "needs_review", "innovation_unclassified_evidence": []}, "baseline", "I", 1),
        ({"innovation_subtypes": ["attribute"], "innovation_subtype_status": "complete", "innovation_unclassified_evidence": [{"unknown": True}]}, "candidate", "I", 1),
    ]
    require(all(subtype_metadata(*args)[2] for args in subtype_bad), "Unknown/missing/inconsistent metadata accepted")
    rejected = {}
    for name, mutate in (
        ("missing_AI_ID", lambda a: a["raw_coder_submissions"]["agent-A/结果-01.json"]["rows"].pop()),
        ("duplicate_AI_ID", lambda a: a["raw_coder_submissions"]["agent-C/结果-01.json"]["rows"].append(copy.deepcopy(a["raw_coder_submissions"]["agent-C/结果-01.json"]["rows"][0]))),
        ("wrong_review_ID", lambda a: a["selected_machine_records_by_version_and_blind_id"]["baseline"]["V600-0001"].update(id="wrong")),
        ("label_mismatch", lambda a: a["raw_coder_submissions"]["agent-A/结果-01.json"]["rows"][0]["labels"].update(S=0)),
        ("boolean_label", lambda a: a["raw_coder_submissions"]["agent-A/结果-01.json"]["rows"][0]["labels"].update(S=True)),
        ("partial_null_machine", lambda a: a["selected_machine_records_by_version_and_blind_id"]["candidate"]["V600-0001"]["labels"].update(S=None)),
        ("missing_judgement_status", lambda a: a["selected_machine_records_by_version_and_blind_id"]["candidate"]["V600-0001"].pop("judgement_status")),
        ("empty_input_status", lambda a: a["selected_machine_records_by_version_and_blind_id"]["candidate"]["V600-0001"].update(input_assessment_status="")),
        ("archive_normalized_design_changed", lambda a: a["normalized_rows_without_generated_reference"][0].update(N_h=32)),
        ("archive_sampling_row_design_changed", lambda a: a["sampling_manifest_original"]["rows"][0].update(stratum="other")),
        ("archive_plan_size_changed", lambda a: a["sampling_manifest_original"]["plan"].update(n=7)),
    ):
        changed = copy.deepcopy(archive); mutate(changed)
        try: analyze(payload, changed, paired_metrics=metrics)
        except ValueError as exc: rejected[name] = str(exc)
        else: raise AssertionError("Archive mismatch accepted: " + name)
    for name in ("coherent_payload_population_drift", "coherent_payload_and_normalized_drift"):
        changed_p, changed_a = copy.deepcopy(payload), copy.deepcopy(archive)
        changed_p["population_N"] = 32; changed_p["strata"][0]["N_h"] = 32
        for row in changed_p["rows"]: row["N_h"] = 32
        if name == "coherent_payload_and_normalized_drift":
            changed_a["normalized_rows_without_generated_reference"] = copy.deepcopy(changed_p["rows"])
        try: analyze(changed_p, changed_a, paired_metrics=metrics)
        except ValueError as exc: rejected[name] = str(exc)
        else: raise AssertionError("Design drift accepted: " + name)
    require(sources == {k: path.read_bytes() for k, path in code_paths.items()}, "QA code dependency changed during run")
    return {"status": "passed_synthetic_QA_only", "real_sample_read_or_analyzed": False, "actual_new_sample_sensitivity_run": False,
            "synthetic_n": 8, "synthetic_population_N": 16, "code_sha256": {k: sha(v) for k, v in sources.items()},
            "checks": {"all_five_secondary_scenarios": True, "single_and_multiple_subtypes": True, "column_specific_own_subtypes": True,
                       "pending_preserved": True, "missing_unknown_inconsistent_metadata_not_calculable": True,
                       "ID_label_mismatch_rejected": rejected, "extra_bad_subtype_contracts": len(subtype_bad),
                       "byte_equivalent_inputs_unchanged": True, "row_order_invariant": True, "primary_metrics_not_overwritten": True,
                       "positive_reference_denominators_recomputed": True, "fixed_shared_seed_and_affected_dimension_only": True},
            "limits": ["Only fictional rows and labels; no real predictions, candidate text or new reference labels were read.",
                       "No actual new-sample sensitivity analysis has run. Frozen dependency hashes must be verified at future execution.",
                       "Secondary operationalizations apply to the supplied new finite frame and do not prove full-corpus rankings."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-qa", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(args.synthetic_qa, "Only synthetic QA CLI is enabled; no research-data execution")
    partial = args.output.with_name("." + args.output.name + ".partial")
    require(not os.path.lexists(args.output) and not os.path.lexists(partial), "Refusing existing QA output/partial")
    output = self_test()
    with partial.open("xb") as handle:
        handle.write((json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())
        handle.flush(); os.fsync(handle.fileno())
    os.link(partial, args.output); partial.unlink()
    print(json.dumps({"status": output["status"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
