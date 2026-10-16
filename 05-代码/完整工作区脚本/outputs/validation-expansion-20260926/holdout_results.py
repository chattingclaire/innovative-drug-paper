"""Strict frozen H600 ID bridge; importing this module reads no study data.

CLI (run only after all independent submissions exist):
  python -B holdout_results.py --freeze /absolute/最终冻结清单.json \
      --holdout /absolute/H600 --output /absolute/new-results.json
Synthetic QA, which accepts no study paths:
  python -B holdout_results.py --synthetic-qa --output new-QA.json

Final freeze.files must include the sampler's required files AND holdout_results
(this exact bridge) and survey_metrics (the exact statistical implementation).
All file paths in freeze.files must be absolute. H600/封存信息.json must declare
release_status=ready_for_blind_review and output_files={relative_path:sha256}.
Released files are the researcher mapping, A/C manuals and material packets;
submissions are agent-A/C/结果-NN.json and must cover exactly their material batch.
No missing submission, ID, dimension or reason is imputed.
F/I subtype lists, S quality basis, assessment/label consistency and nonempty
string evidence follow the fixed reviewer output contract; no field is repaired.

Fixed machine-null rule, explicitly supplied by the study coordinator:
all FIVE labels must be None, judgement_status must be 'undetermined', AND
input_assessment_status must be 'context_insufficient' or 'text_problem'. Only
then all five become literal 待定. Mixed None/binary labels, other null statuses,
and binary labels marked undetermined are errors. No fallback parsing is used.

Public pure API: assemble(bundle) -> (payload_by_coder, archive), then
evaluate(bundle) -> JSON-serializable result. bundle contains byte strings:
  freeze, seal; frozen={freeze_file_name:bytes};
  released={H600_relative_path:bytes}; results={H600_relative_path:bytes}.
No filesystem reads occur inside assemble/evaluate. evaluate executes the exact
hash-verified survey_metrics source bytes and calls analyze twice, using each
original AI coder as an explicit separate reference. No consensus/adjudicated
reference is generated. A_vs_C is retained once; both dictionary comparisons are
reported, with no selection of the better result or doubling of sample size.

CLI reads one snapshot, validates it, evaluates, rechecks every input file/hash
and the submission/material inventory, then writes an exclusive partial JSON
and atomically publishes with a no-overwrite hard link in the same directory.
An existing output or partial file blocks publication. Original parsed freeze,
seal, mapping and coder submissions, exact source hashes, selected machine
records and normalized analysis rows are preserved in the output archive.
Hashes preserve provenance; they cannot certify honest timestamps, coder
independence, substantive evidence quality, unseen text or correct frame creation.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re

DIMS = ("S", "E", "Ec", "I", "F")
PENDING = "待定"
REQUIRED_FROZEN = {
    "corpus", "adapter", "classification", "exposure", "protocol", "dictionary",
    "dictionary_predictions", "sampler", "survey_metrics", "llm_prompt", "holdout_results",
}
PENDING_RULE = {
    "version": "explicit_machine_null_rule_v1",
    "all_five_labels_are_null": True,
    "judgement_status_equals": "undetermined",
    "input_assessment_status_in": ["context_insufficient", "text_problem"],
    "partial_null_labels": "reject",
    "otherwise": "literal_integer_0_or_1_only; undetermined_binary_conflict_rejected",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value, name):
    require(isinstance(value, str) and bool(value.strip()), f"{name}: nonempty string required")
    return value


def hash_value(value, name):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            f"{name}: lowercase SHA-256 required")
    return value


def positive_int(value, name):
    require(type(value) is int and value > 0, f"{name}: positive integer required")
    return value


def read_json(data, name):
    require(isinstance(data, bytes), f"{name}: byte snapshot required")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"{name}: duplicate JSON key {key}")
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError(f"{name}: nonfinite JSON constant {value}")
    obj = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad_constant)
    require(isinstance(obj, dict), f"{name}: JSON object required")
    return obj


def unique_rows(rows, key, name):
    require(isinstance(rows, list), f"{name}: rows must be a list")
    result = {}
    for row in rows:
        require(isinstance(row, dict), f"{name}: row object required")
        value = nonempty(row.get(key), f"{name}.{key}")
        require(value not in result, f"{name}: duplicate {key} {value}")
        result[value] = row
    return result


def relative_name(name):
    nonempty(name, "relative output path")
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts and str(path) == name
            and "\\" not in name and name not in {".", ""}, "Unsafe/noncanonical released path")
    return name


def labels(value, name):
    require(isinstance(value, dict) and set(value) == set(DIMS), f"{name}: exact five dimensions required")
    for dim, code in value.items():
        require((type(code) is int and code in (0, 1)) or
                (type(code) is str and code == PENDING), f"{name}.{dim}: literal 0/1/待定 required")
    return dict(value)


def machine_labels(row):
    value = row.get("labels")
    require(isinstance(value, dict) and set(value) == set(DIMS), "Machine: exact five labels required")
    judgement = nonempty(row.get("judgement_status"), "machine.judgement_status")
    assessment = nonempty(row.get("input_assessment_status"), "machine.input_assessment_status")
    any_null = any(value[d] is None for d in DIMS)
    if any_null:
        require(all(value[d] is None for d in DIMS), "Machine: partial null labels forbidden")
        require(judgement == "undetermined" and assessment in {"context_insufficient", "text_problem"},
                "Machine: null labels lack the explicit authorized pending status")
        return {d: PENDING for d in DIMS}, True
    require(judgement != "undetermined", "Machine: binary labels conflict with undetermined status")
    require(all(type(value[d]) is int and value[d] in (0, 1) for d in DIMS),
            "Machine: non-null labels must be literal integer 0/1")
    return dict(value), False


def validate_result(document, coder, version, packet, packet_sha, name):
    require(document.get("coder") == coder, f"{name}: coder mismatch")
    identity = document.get("identity")
    require((isinstance(identity, str) and bool(identity.strip())) or
            (isinstance(identity, dict) and bool(identity)), f"{name}: explicit identity required")
    require(document.get("protocol_version") == version, f"{name}: protocol version mismatch")
    require(document.get("protocol_acknowledged") is True, f"{name}: explicit protocol acknowledgement required")
    completed = nonempty(document.get("completed_at"), f"{name}.completed_at")
    try:
        datetime.fromisoformat(completed.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name}: completed_at must be an ISO timestamp") from exc
    require("T" in completed or " " in completed, f"{name}: completed_at must include time")
    require(document.get("input_packet_sha256") == packet_sha, f"{name}: input packet hash mismatch")
    for key in ("batch", "total_batches"):
        if key in document:
            require(document[key] == packet[key], f"{name}: {key} mismatch")
    require("rule_questions" in document, f"{name}: rule_questions missing")
    rows = unique_rows(document.get("rows"), "id", name)
    require(set(rows) == {r["id"] for r in packet["rows"]}, f"{name}: incomplete or cross-batch ID set")
    for key, row in rows.items():
        codes = labels(row.get("labels"), f"{name}/{key}")
        reasons = row.get("dimension_reasons")
        require(isinstance(reasons, dict) and set(reasons) == set(DIMS), f"{name}/{key}: five reasons required")
        for dim in DIMS:
            nonempty(reasons[dim], f"{name}/{key}.reason.{dim}")
        for field in ("evidence", "material_issue", "rationale", "fairness_subtypes",
                      "innovation_subtypes", "safety_quality_basis", "input_assessment"):
            require(field in row, f"{name}/{key}: missing {field}")
        nonempty(row["rationale"], f"{name}/{key}.rationale")
        nonempty(row["evidence"], f"{name}/{key}.evidence")
        for dim, field, allowed in (
            ("F", "fairness_subtypes", {"access", "affordability", "clinical_management", "dimension_information"}),
            ("I", "innovation_subtypes", {"attribute", "research_support", "qualification_advantage"}),
        ):
            subtypes = row[field]
            require(isinstance(subtypes, list) and all(isinstance(x, str) and x in allowed for x in subtypes),
                    f"{name}/{key}: {field} must be a list of allowed subtypes")
            require(len(subtypes) == len(set(subtypes)), f"{name}/{key}: duplicate {field}")
            require(bool(subtypes) == (codes[dim] == 1),
                    f"{name}/{key}: {field} must be nonempty exactly when {dim}=1")
        quality = row["safety_quality_basis"]
        allowed_quality = ({"no_quality_basis"} if codes["S"] == 0 else
                           {"undetermined"} if codes["S"] == PENDING else
                           {"quality_only", "quality_and_other", "no_quality_basis"})
        require(isinstance(quality, str) and quality in allowed_quality,
                f"{name}/{key}: safety_quality_basis inconsistent with S")
        require(isinstance(row["input_assessment"], dict), f"{name}/{key}: input_assessment object required")
        status = nonempty(row["input_assessment"].get("status"), f"{name}/{key}.input_assessment.status")
        require(status in {"sufficient", "context_insufficient", "text_problem"},
                f"{name}/{key}: unsupported input_assessment.status")
        if status != "sufficient":
            require(all(codes[d] == PENDING for d in DIMS),
                    f"{name}/{key}: material insufficiency requires all five labels pending")
        nonempty(row["input_assessment"].get("basis"), f"{name}/{key}.input_assessment.basis")
    return rows


def assemble(bundle):
    """Validate byte snapshots and return explicit A-reference/C-reference payloads."""
    freeze = read_json(bundle["freeze"], "freeze")
    seal = read_json(bundle["seal"], "seal")
    require(freeze.get("status") == "frozen_for_reference_label_holdout", "Freeze is not final")
    version = nonempty(freeze.get("protocol_version"), "freeze.protocol_version")
    files = freeze.get("files")
    require(isinstance(files, dict) and REQUIRED_FROZEN <= set(files), "Missing required frozen file")
    require(set(bundle["frozen"]) == set(files), "Frozen source snapshot inventory mismatch")
    for name, entry in files.items():
        require(isinstance(entry, dict), "Frozen file entry must be an object")
        require(Path(nonempty(entry.get("path"), f"files.{name}.path")).is_absolute(), "Frozen paths must be absolute")
        require(sha(bundle["frozen"][name]) == hash_value(entry.get("sha256"), f"files.{name}.sha256"),
                f"Frozen file hash mismatch: {name}")
    require(seal.get("status") == "drawn" and seal.get("release_status") == "ready_for_blind_review",
            "Holdout is not released")
    require(seal.get("freeze_manifest_sha256") == sha(bundle["freeze"]), "Freeze manifest hash mismatch")
    outputs = seal.get("output_files")
    require(isinstance(outputs, dict) and outputs, "Released output hash manifest required")
    require(set(bundle["released"]) == set(outputs), "Released inventory differs from seal")
    for name, digest in outputs.items():
        relative_name(name)
        require(sha(bundle["released"][name]) == hash_value(digest, name), f"Released file hash mismatch: {name}")
    map_name = "抽样清单-研究者.json"
    require(map_name in outputs, "Researcher mapping is not sealed")
    mapping = read_json(bundle["released"][map_name], map_name)
    plan = mapping.get("plan")
    require(isinstance(plan, dict), "Mapping plan required")
    require(all(key in seal and value == seal[key] for key, value in plan.items()), "Mapping plan differs from release seal")
    require(plan.get("status") == "drawn" and plan.get("seed") == 2026092602, "Unexpected sampling status/seed")
    require(plan.get("freeze_manifest_sha256") == sha(bundle["freeze"]), "Mapping freeze hash mismatch")
    require(plan.get("input_hashes") == {name: entry["sha256"] for name, entry in files.items()},
            "Sampling plan input hashes differ from freeze")
    N = positive_int(plan.get("N_star"), "N_star")
    n = positive_int(plan.get("n"), "sample n")
    require(n == min(600, N), "Sample size does not match H600 plan")
    manifest = plan.get("strata")
    require(isinstance(manifest, dict) and manifest, "Nonempty stratum manifest required")
    strata = []
    for h, spec in manifest.items():
        nonempty(h, "stratum")
        require(isinstance(spec, dict), "Stratum specification must be an object")
        Nh = positive_int(spec.get("N_h"), "N_h")
        nh = positive_int(spec.get("n_h"), "n_h")
        require(nh <= Nh and (nh == Nh or nh >= 2), "Invalid stratum sample size")
        for key, expected in (("pi", nh / Nh), ("weight", Nh / nh)):
            value = spec.get(key)
            require(type(value) in (int, float) and math.isfinite(value) and
                    math.isclose(value, expected, rel_tol=1e-12, abs_tol=1e-12), f"Invalid stratum {key}")
        strata.append({"stratum": h, "N_h": Nh, "n_h": nh})
    require(sum(x["N_h"] for x in strata) == N and sum(x["n_h"] for x in strata) == n,
            "Stratum totals differ from N_star/sample n")
    maps = unique_rows(mapping.get("rows"), "id", "mapping")
    original_ids = unique_rows(mapping["rows"], "review_id", "mapping original IDs")
    require(len(maps) == n, "Mapping row count differs from sample n")
    for row in maps.values():
        h = row.get("stratum")
        require(h in manifest, "Mapping contains undeclared stratum")
        for key in ("N_h", "n_h"):
            require(type(row.get(key)) is int and row[key] == manifest[h][key], "Mapping stratum size mismatch")
        for key in ("pi", "weight"):
            if key in row:
                require(type(row[key]) in (int, float) and math.isclose(row[key], manifest[h][key],
                        rel_tol=1e-12, abs_tol=1e-12), f"Mapping {key} mismatch")
        hash_value(row.get("unit_text_sha256"), "mapping.unit_text_sha256")
    for h, spec in manifest.items():
        require(sum(r["stratum"] == h for r in maps.values()) == spec["n_h"], "Actual per-stratum n mismatch")
    unselected = mapping.get("not_selected_ids")
    require(isinstance(unselected, list) and all(isinstance(x, str) and x for x in unselected),
            "Unselected ID list required")
    require(len(set(unselected)) == len(unselected) == N - n and not set(unselected) & set(original_ids),
            "Unselected IDs inconsistent with sample/frame size")
    batches = math.ceil(n / 25)
    material_names = {f"agent-{c}/材料-{b:02d}.json" for c in ("A", "C") for b in range(1, batches + 1)}
    result_names = {f"agent-{c}/结果-{b:02d}.json" for c in ("A", "C") for b in range(1, batches + 1)}
    manual_names = {f"agent-{c}/五维共用编码协议.md" for c in ("A", "C")}
    require(set(outputs) == material_names | manual_names | {map_name}, "Unexpected/incomplete released file set")
    require(set(bundle["results"]) == result_names, "Missing/extra result batch files")
    submitted = {"A": {}, "C": {}}
    raw_submissions, packet_manifest, submission_manifest = {}, {}, {}
    for coder in ("A", "C"):
        manual = f"agent-{coder}/五维共用编码协议.md"
        require(bundle["released"][manual] == bundle["frozen"]["protocol"], "Coder manual differs from frozen protocol")
        for batch in range(1, batches + 1):
            pn, rn = f"agent-{coder}/材料-{batch:02d}.json", f"agent-{coder}/结果-{batch:02d}.json"
            packet_bytes = bundle["released"][pn]
            require(packet_bytes == bundle["released"][f"agent-A/材料-{batch:02d}.json"], "A/C material packets differ")
            packet = read_json(packet_bytes, pn)
            require(packet.get("protocol_version") == version and type(packet.get("batch")) is int
                    and packet["batch"] == batch and type(packet.get("total_batches")) is int
                    and packet["total_batches"] == batches, f"{pn}: version/batch header mismatch")
            require(packet.get("purpose") == "reference_label_holdout_AI_independent", "Wrong material purpose")
            prows = unique_rows(packet.get("rows"), "id", pn)
            expected_ids = list(maps)[(batch - 1) * 25:batch * 25]
            require(list(prows) == expected_ids, f"{pn}: mapping/material batch ID mismatch")
            for key, row in prows.items():
                require(isinstance(row.get("text"), str), f"{pn}/{key}: text must be a string (empty allowed)")
                require(sha(row["text"].encode("utf-8")) == maps[key]["unit_text_sha256"], f"{pn}/{key}: unit text hash mismatch")
                require(isinstance(row.get("contexts"), dict) and isinstance(row.get("input_assessment"), dict),
                        f"{pn}/{key}: frozen contexts/assessment object required")
            result = read_json(bundle["results"][rn], rn)
            rrows = validate_result(result, coder, version, packet, sha(packet_bytes), rn)
            require(not set(submitted[coder]) & set(rrows), "Duplicate coder ID across batches")
            submitted[coder].update(rrows)
            raw_submissions[rn] = result
            packet_manifest[pn] = {"sha256": sha(packet_bytes), "ids": expected_ids, "batch": batch}
            submission_manifest[rn] = {"sha256": sha(bundle["results"][rn]), "coder": coder,
                                       "input_packet_sha256": sha(packet_bytes), "ids": list(rrows)}
        require(set(submitted[coder]) == set(maps), f"Coder {coder} differs from complete sampled ID set")
    prediction_doc = read_json(bundle["frozen"]["dictionary_predictions"], "dictionary_predictions")
    predictions = unique_rows(prediction_doc.get("rows"), "id", "dictionary_predictions")
    require(set(original_ids) <= set(predictions), "Missing sampled machine prediction")
    normalized, selected_predictions, pending_ids, machine_versions = [], {}, [], set()
    for key, row in maps.items():
        prediction = predictions[row["review_id"]]
        require(prediction.get("unit_text_sha256") == row["unit_text_sha256"], "Prediction/source unit text hash mismatch")
        machine_versions.add(nonempty(prediction.get("version"), "machine.version"))
        values, converted = machine_labels(prediction)
        if converted:
            pending_ids.append(key)
        selected_predictions[key] = prediction
        normalized.append({"id": key, "stratum": row["stratum"], "N_h": row["N_h"], "n_h": row["n_h"],
                           "A": labels(submitted["A"][key]["labels"], "A"),
                           "C": labels(submitted["C"][key]["labels"], "C"), "dictionary": values})
    require(len(machine_versions) == 1, "Mixed machine versions among sampled records")
    machine_version = next(iter(machine_versions))
    if "version" in prediction_doc:
        require(prediction_doc["version"] == machine_version, "Prediction document/row version mismatch")
    if "dictionary_version" in freeze:
        require(freeze["dictionary_version"] == machine_version, "Frozen/row dictionary version mismatch")
    dictionary_info = {"description": f"Frozen dictionary predictions; row version {machine_version}; no post-reference selection.",
                       "version": machine_version, "implementation": files["dictionary"],
                       "predictions": files["dictionary_predictions"], "pending_rule": PENDING_RULE,
                       "pending_conversion_ids": pending_ids}
    payloads = {}
    for coder in ("A", "C"):
        provenance = {name: {k: obj[k] for k in ("identity", "completed_at", "protocol_version", "input_packet_sha256")}
                      for name, obj in raw_submissions.items() if name.startswith(f"agent-{coder}/")}
        ref_info = {"kind": "AI", "coder": coder,
                    "description": f"Original independent AI coder {coder} only; explicit comparison labels, not adjudicated consensus or error-free truth.",
                    "original_submission_provenance": provenance,
                    "submission_hashes": {name: info["sha256"] for name, info in submission_manifest.items()
                                          if name.startswith(f"agent-{coder}/")}}
        payloads[coder] = {"strata": copy.deepcopy(strata), "population_N": N,
                           "rows": [{**copy.deepcopy(row), "reference": dict(row[coder])} for row in normalized],
                           "reference_info": ref_info, "dictionary_info": copy.deepcopy(dictionary_info)}
    archive = {"freeze_manifest_original": freeze, "release_seal_original": seal,
               "sampling_manifest_original": mapping, "raw_coder_submissions": raw_submissions,
               "selected_machine_records_by_blind_id": selected_predictions,
               "normalized_rows_without_generated_reference": normalized,
               "input_snapshot_hashes": {"freeze": sha(bundle["freeze"]), "seal": sha(bundle["seal"]),
                    "frozen": {name: sha(data) for name, data in bundle["frozen"].items()},
                    "released": dict(outputs), "submissions": {name: sha(data) for name, data in bundle["results"].items()}},
               "packet_manifest": packet_manifest, "original_submission_manifest": submission_manifest,
               "machine_null_conversion_rule": PENDING_RULE,
               "pending_machine_ids": pending_ids,
               "reference_created_by_consensus_or_imputation": False}
    return payloads, archive


def evaluate(bundle):
    """Run both explicit AI-reference comparisons with the hash-verified metric code."""
    payloads, archive = assemble(bundle)
    namespace = {"__name__": "_frozen_survey_metrics_for_holdout", "__file__": "<frozen survey_metrics.py>"}
    exec(compile(bundle["frozen"]["survey_metrics"], "<frozen survey_metrics.py>", "exec"), namespace)
    outputs = {}
    for coder, payload in payloads.items():
        result = namespace["analyze"](payload)
        require(result["sample_size_matches_H600_plan"] is True, "Statistical tool rejected planned sample size")
        require(result["sample_n"] == len(archive["sampling_manifest_original"]["rows"]), "Statistical row count changed")
        require(set(row["id"] for row in payload["rows"]) ==
                {row["id"] for row in archive["sampling_manifest_original"]["rows"]}, "Analysis ID set changed")
        outputs[coder] = result
    require(outputs["A"]["comparisons"]["A_vs_C"] == outputs["C"]["comparisons"]["A_vs_C"],
            "Original A/C comparison changed between explicit reference calls")
    common = {k: v for k, v in outputs["A"].items()
              if k not in {"comparisons", "reference_info", "dictionary_info", "classification_status"}}
    comparisons = {"A_vs_C": outputs["A"]["comparisons"]["A_vs_C"]}
    for coder in ("A", "C"):
        item = copy.deepcopy(outputs[coder]["comparisons"]["dictionary_vs_reference"])
        item["right"] = coder
        item["reference_info"] = outputs[coder]["reference_info"]
        item["dictionary_info"] = outputs[coder]["dictionary_info"]
        comparisons[f"dictionary_vs_{coder}"] = item
    return {"status": "completed_frozen_ID_join_not_validation_pass",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "design_and_interval_metadata": common, "comparisons": comparisons, "archive": archive,
            "interpretation": ["Both single-AI-reference comparisons are reported; neither is human gold truth.",
                "These comparisons share one sample and one dictionary; sample size is not doubled.",
                "Original A/C submissions and first independent agreement are unchanged by later adjudication.",
                "Conditional binary metrics require coverage and pending bounds; no pending value becomes zero.",
                "Hashes and metadata do not prove honest independence, correct evidence, complete development exclusions or unseen text.",
                "Machine record_sha256 is preserved as supplied; its undocumented record serialization is not inferred."]}


def check_unchanged(before, after):
    require(before == after, "Input file or inventory changed during evaluation; output not released")


def load_snapshot(freeze_path, holdout):
    """Read runtime inputs only when explicitly called by the CLI; no import-time I/O."""
    require(freeze_path.is_absolute() and holdout.is_absolute(), "Use absolute freeze and holdout paths")
    tracked = {}
    def read(path):
        path = Path(path)
        raw = path.read_bytes()
        if str(path) in tracked:
            require(tracked[str(path)] == sha(raw), "Input changed while snapshot was read")
        tracked[str(path)] = sha(raw)
        return raw
    freeze_bytes = read(freeze_path)
    freeze = read_json(freeze_bytes, "freeze")
    require(isinstance(freeze.get("files"), dict) and REQUIRED_FROZEN <= set(freeze["files"]), "Missing frozen files")
    frozen = {name: read(Path(entry["path"])) for name, entry in freeze["files"].items()}
    running_bridge = read(Path(__file__).resolve())
    require(sha(running_bridge) == freeze["files"]["holdout_results"]["sha256"], "Running bridge is not frozen bridge")
    seal_bytes = read(holdout / "封存信息.json")
    seal = read_json(seal_bytes, "seal")
    released = {}
    for name in seal.get("output_files", {}):
        relative_name(name)
        path = holdout / name
        require(path.resolve().is_relative_to(holdout.resolve()), "Released file escapes holdout directory")
        released[name] = read(path)
    inventory = sorted(str(p.relative_to(holdout)) for p in holdout.glob("agent-*/结果-*.json"))
    results = {}
    for name in inventory:
        path = holdout / name
        require(path.resolve().is_relative_to(holdout.resolve()), "Submission escapes holdout directory")
        results[name] = read(path)
    materials = sorted(str(p.relative_to(holdout)) for p in holdout.glob("agent-*/材料-*.json"))
    expected_materials = sorted(name for name in released if re.fullmatch(r"agent-[AC]/材料-\d{2}\.json", name))
    require(materials == expected_materials, "Unsealed/missing material packet inventory")
    return {"freeze": freeze_bytes, "seal": seal_bytes, "frozen": frozen,
            "released": released, "results": results}, tracked, {"results": inventory, "materials": materials}


def publish_json(path, obj):
    """Exclusive partial write, then atomic no-overwrite publication on the same filesystem."""
    path = Path(path)
    partial = path.with_name("." + path.name + ".partial")
    require(not os.path.lexists(path) and not os.path.lexists(partial), "Refusing existing output or partial output")
    data = encoded(obj)
    with partial.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)  # Fails atomically if another writer created the destination.
    partial.unlink()


def _synthetic_bundle(metric_bytes, bridge_bytes):
    """Only invented text and labels; N=n=26 gives two batches and a valid plan size."""
    version = "synthetic-protocol-v1"
    frozen = {name: ("SYNTHETIC FROZEN " + name).encode() for name in REQUIRED_FROZEN}
    frozen["survey_metrics"], frozen["holdout_results"] = metric_bytes, bridge_bytes
    frozen["protocol"] = b"SYNTHETIC MANUAL ONLY"
    maps, materials, machine = [], [], []
    for i in range(26):
        key, original, text = f"H600-{i+1:04d}", f"synthetic-original-{i+1}", f"SYNTHETIC POLICY PLACEHOLDER {i+1}"
        h = "GOV|2021" if i < 13 else "NMPA|unknown"
        maps.append({"id": key, "review_id": original, "stratum": h, "N_h": 13, "n_h": 13,
                     "pi": 1.0, "weight": 1.0, "unit_text_sha256": sha(text.encode())})
        materials.append({"id": key, "text": text, "contexts": {}, "input_assessment": {"status": "not_assessed"}})
        pending = i == 0
        machine.append({"id": original, "version": "synthetic-machine-v1", "unit_text_sha256": sha(text.encode()),
                        "labels": {d: None if pending else i % 2 for d in DIMS},
                        "judgement_status": "undetermined" if pending else "determined",
                        "input_assessment_status": "context_insufficient" if pending else "sufficient"})
    frozen["dictionary_predictions"] = encoded({"version": "synthetic-machine-v1", "rows": list(reversed(machine))})
    freeze = {"status": "frozen_for_reference_label_holdout", "protocol_version": version,
              "files": {name: {"path": f"/synthetic-only/{name}", "sha256": sha(data)} for name, data in frozen.items()}}
    fb = encoded(freeze)
    plan = {"status": "drawn", "N_star": 26, "n": 26, "seed": 2026092602,
            "strata": {h: {"N_h": 13, "n_h": 13, "pi": 1.0, "weight": 1.0} for h in ("GOV|2021", "NMPA|unknown")},
            "freeze_manifest_sha256": sha(fb), "input_hashes": {name: sha(data) for name, data in frozen.items()}}
    released = {"抽样清单-研究者.json": encoded({"plan": plan, "rows": maps, "not_selected_ids": []})}
    results = {}
    for coder in ("A", "C"):
        released[f"agent-{coder}/五维共用编码协议.md"] = frozen["protocol"]
        for batch in (1, 2):
            rows = materials[(batch - 1) * 25:batch * 25]
            packet = {"protocol_version": version, "purpose": "reference_label_holdout_AI_independent",
                      "batch": batch, "total_batches": 2, "rows": rows}
            pn, rn = f"agent-{coder}/材料-{batch:02d}.json", f"agent-{coder}/结果-{batch:02d}.json"
            released[pn] = encoded(packet)
            judgments = []
            for row in rows:
                i = int(row["id"].split("-")[1]) - 1
                label = PENDING if coder == "C" and i == 1 else i % 2
                judgments.append({"id": row["id"], "labels": {d: label for d in DIMS},
                    "dimension_reasons": {d: "Synthetic reason only" for d in DIMS}, "evidence": "Synthetic evidence only",
                    "material_issue": label == PENDING, "rationale": "Synthetic rationale only",
                    "fairness_subtypes": ["access"] if label == 1 else [],
                    "innovation_subtypes": ["attribute"] if label == 1 else [],
                    "safety_quality_basis": "undetermined" if label == PENDING else "no_quality_basis",
                    "input_assessment": {"status": "context_insufficient" if label == PENDING else "sufficient",
                                         "basis": "Synthetic basis only"}})
            results[rn] = encoded({"coder": coder, "identity": {"kind": "AI", "name": f"synthetic-{coder}"},
                                  "protocol_version": version, "protocol_acknowledged": True,
                                  "completed_at": "2026-09-26T00:00:00+00:00", "input_packet_sha256": sha(released[pn]),
                                  "rows": list(reversed(judgments)), "rule_questions": []})
    seal = {**plan, "release_status": "ready_for_blind_review",
            "output_files": {name: sha(data) for name, data in released.items()}}
    return {"freeze": fb, "seal": encoded(seal), "frozen": frozen, "released": released, "results": results}


def self_test():
    """Read only this source and survey_metrics.py; all study-shaped data are invented."""
    here = Path(__file__).resolve()
    bridge_bytes = here.read_bytes()
    metric_bytes = here.with_name("survey_metrics.py").read_bytes()
    fixture = _synthetic_bundle(metric_bytes, bridge_bytes)
    payloads, archive = assemble(fixture)
    require(len(payloads["A"]["rows"]) == 26, "Synthetic joined rows lost")
    require(payloads["A"]["rows"][0]["dictionary"] == {d: PENDING for d in DIMS}, "Pending conversion failed")
    require(payloads["A"]["rows"][0]["reference"] == {d: 0 for d in DIMS}, "Reference was manufactured")
    require(payloads["C"]["rows"][1]["reference"] == {d: PENDING for d in DIMS}, "AI pending dropped")
    checks = {"ID_join_two_batches_reversed_submission_and_prediction_order": "passed",
              "all_samples_and_original_pending_retained": "passed"}
    rejected = {}
    def bad(name, mutate, needle=None):
        candidate = copy.deepcopy(fixture)
        mutate(candidate)
        try:
            assemble(candidate)
        except (ValueError, KeyError, TypeError) as exc:
            if needle:
                require(needle in str(exc), f"Wrong rejection for {name}: {exc}")
            rejected[name] = str(exc)
        else:
            raise AssertionError(f"Invalid synthetic bundle accepted: {name}")
    def result_mutate(b, transform, path="agent-A/结果-01.json"):
        obj = read_json(b["results"][path], path); transform(obj); b["results"][path] = encoded(obj)
    def reseal_release(b, path, transform):
        obj = read_json(b["released"][path], path); transform(obj); b["released"][path] = encoded(obj)
        seal = read_json(b["seal"], "seal"); seal["output_files"][path] = sha(b["released"][path]); b["seal"] = encoded(seal)
    def reseal_predictions(b, transform):
        # Keep all container hashes internally consistent to test semantic ID/text checks.
        obj = read_json(b["frozen"]["dictionary_predictions"], "synthetic predictions")
        transform(obj)
        b["frozen"]["dictionary_predictions"] = encoded(obj)
        freeze = read_json(b["freeze"], "synthetic freeze")
        freeze["files"]["dictionary_predictions"]["sha256"] = sha(b["frozen"]["dictionary_predictions"])
        b["freeze"] = encoded(freeze)
        map_name = "抽样清单-研究者.json"
        mapping = read_json(b["released"][map_name], "synthetic mapping")
        mapping["plan"]["freeze_manifest_sha256"] = sha(b["freeze"])
        mapping["plan"]["input_hashes"] = {name: entry["sha256"] for name, entry in freeze["files"].items()}
        b["released"][map_name] = encoded(mapping)
        seal = read_json(b["seal"], "synthetic seal")
        seal.update(mapping["plan"])
        seal["output_files"][map_name] = sha(b["released"][map_name])
        b["seal"] = encoded(seal)
    bad("missing_batch", lambda b: b["results"].pop("agent-C/结果-02.json"), "batch files")
    bad("missing_row", lambda b: result_mutate(b, lambda x: x["rows"].pop()), "ID set")
    bad("duplicate_row_ID", lambda b: result_mutate(b, lambda x: x["rows"].append(copy.deepcopy(x["rows"][0]))), "duplicate")
    bad("cross_batch_ID", lambda b: result_mutate(b, lambda x: x["rows"][0].update(id="H600-0026")), "ID set")
    bad("missing_dimension", lambda b: result_mutate(b, lambda x: x["rows"][0]["labels"].pop("S")), "five dimensions")
    bad("empty_dimension_reason", lambda b: result_mutate(b, lambda x: x["rows"][0]["dimension_reasons"].update(S="")), "nonempty")
    bad("boolean_label", lambda b: result_mutate(b, lambda x: x["rows"][0]["labels"].update(S=True)), "literal")
    bad("missing_material_issue", lambda b: result_mutate(b, lambda x: x["rows"][0].pop("material_issue")), "missing material_issue")
    bad("wrong_coder", lambda b: result_mutate(b, lambda x: x.update(coder="C")), "coder mismatch")
    bad("unacknowledged_protocol", lambda b: result_mutate(b, lambda x: x.update(protocol_acknowledged="true")), "acknowledgement")
    bad("changed_protocol_version", lambda b: result_mutate(b, lambda x: x.update(protocol_version="changed")), "version mismatch")
    bad("wrong_input_packet_hash", lambda b: result_mutate(b, lambda x: x.update(input_packet_sha256="0" * 64)), "packet hash")
    bad("changed_frozen_predictions_bytes", lambda b: b["frozen"].update(dictionary_predictions=b"changed"), "Frozen file hash")
    bad("changed_material_bytes", lambda b: b["released"].update({"agent-A/材料-01.json": b"changed"}), "Released file hash")
    bad("changed_freeze_manifest", lambda b: b.update(freeze=b["freeze"] + b" "), "manifest hash")
    def change_both_text(b):
        for coder in ("A", "C"):
            reseal_release(b, f"agent-{coder}/材料-01.json", lambda x: x["rows"][0].update(text="CHANGED SYNTHETIC TEXT"))
    bad("unit_text_hash_after_resealed_packets", change_both_text, "unit text hash")
    bad("pending_none_in_AI_submission", lambda b: result_mutate(b, lambda x: x["rows"][0]["labels"].update(S=None)), "literal")
    bad("missing_sampled_machine_prediction", lambda b: reseal_predictions(b, lambda x: x["rows"].pop()), "Missing sampled machine")
    bad("duplicate_machine_ID", lambda b: reseal_predictions(b, lambda x: x["rows"].append(copy.deepcopy(x["rows"][0]))), "duplicate")
    bad("prediction_unit_text_hash", lambda b: reseal_predictions(b, lambda x: x["rows"][0].update(unit_text_sha256="0" * 64)), "unit text hash")
    bad("mixed_machine_versions", lambda b: reseal_predictions(b, lambda x: x["rows"][0].update(version="synthetic-other-version")), "Mixed machine versions")
    bad("duplicate_original_mapping_ID", lambda b: reseal_release(b, "抽样清单-研究者.json",
        lambda x: x["rows"][1].update(review_id=x["rows"][0]["review_id"])), "duplicate review_id")
    checks["invalid_ID_schema_version_and_hash_cases"] = {"status": "passed", "rejected_cases": dict(rejected)}
    previous_rejections = set(rejected)
    def semantic_mutate(b, transform, key="H600-0001"):
        result_mutate(b, lambda obj: transform(next(row for row in obj["rows"] if row["id"] == key)))
    bad("unknown_fairness_subtype", lambda b: semantic_mutate(b, lambda r: r.update(fairness_subtypes=["unknown"]), "H600-0002"), "allowed subtypes")
    bad("duplicate_innovation_subtype", lambda b: semantic_mutate(b, lambda r: r.update(innovation_subtypes=["attribute", "attribute"]), "H600-0002"), "duplicate innovation_subtypes")
    bad("positive_F_missing_subtype", lambda b: semantic_mutate(b, lambda r: r.update(fairness_subtypes=[]), "H600-0002"), "exactly when F=1")
    bad("zero_I_has_subtype", lambda b: semantic_mutate(b, lambda r: r.update(innovation_subtypes=["research_support"])), "exactly when I=1")
    def pending_F_with_subtype(row):
        row["labels"]["F"] = PENDING
        row["fairness_subtypes"] = ["access"]
    bad("pending_F_has_subtype", lambda b: semantic_mutate(b, pending_F_with_subtype), "exactly when F=1")
    bad("zero_S_has_quality_basis", lambda b: semantic_mutate(b, lambda r: r.update(safety_quality_basis="quality_only")), "inconsistent with S")
    bad("pending_S_missing_undetermined_basis", lambda b: semantic_mutate(b, lambda r: r["labels"].update(S=PENDING)), "inconsistent with S")
    bad("positive_S_undetermined_basis", lambda b: semantic_mutate(b, lambda r: r.update(safety_quality_basis="undetermined"), "H600-0002"), "inconsistent with S")
    bad("unsupported_assessment_status", lambda b: semantic_mutate(b, lambda r: r["input_assessment"].update(status="not_assessed")), "unsupported input_assessment.status")
    for status in ("context_insufficient", "text_problem"):
        bad(f"{status}_with_binary_labels", lambda b, status=status: semantic_mutate(b, lambda r: r["input_assessment"].update(status=status)), "all five labels pending")
    bad("evidence_list_instead_of_string", lambda b: semantic_mutate(b, lambda r: r.update(evidence=[])), "evidence: nonempty string")
    bad("blank_evidence_string", lambda b: semantic_mutate(b, lambda r: r.update(evidence="  ")), "evidence: nonempty string")
    # Sufficient material can leave a concept boundary pending without changing its reason.
    accepted = copy.deepcopy(fixture)
    def concept_pending(row):
        row["labels"]["I"] = PENDING
        row["innovation_subtypes"] = []
        row["dimension_reasons"]["I"] = "Synthetic concept-boundary uncertainty; no binary imputation"
    semantic_mutate(accepted, concept_pending, "H600-0002")
    accepted_payloads, accepted_archive = assemble(accepted)
    accepted_row = next(r for r in accepted_payloads["A"]["rows"] if r["id"] == "H600-0002")
    require(accepted_row["A"]["I"] == PENDING, "Sufficient-material concept pending was overwritten")
    original_row = next(r for r in accepted_archive["raw_coder_submissions"]["agent-A/结果-01.json"]["rows"] if r["id"] == "H600-0002")
    require(original_row["dimension_reasons"]["I"] == "Synthetic concept-boundary uncertainty; no binary imputation", "Concept pending reason changed")
    for quality in ("quality_only", "quality_and_other", "no_quality_basis"):
        accepted = copy.deepcopy(fixture)
        semantic_mutate(accepted, lambda r, quality=quality: r.update(
            safety_quality_basis=quality,
            fairness_subtypes=["access", "affordability", "clinical_management", "dimension_information"],
            innovation_subtypes=["attribute", "research_support", "qualification_advantage"]), "H600-0002")
        assemble(accepted)
    checks["reviewer_semantic_contract"] = {"status": "passed",
        "rejected_cases": {key: rejected[key] for key in rejected if key not in previous_rejections},
        "sufficient_material_individual_pending_and_reason_preserved": True,
        "all_allowed_F_I_subtypes_and_three_positive_S_bases_accepted": True}
    machine_cases = [
        ({d: None if d == "S" else 0 for d in DIMS}, "undetermined", "context_insufficient"),
        ({d: None for d in DIMS}, "determined", "context_insufficient"),
        ({d: None for d in DIMS}, "undetermined", "sufficient"),
        ({d: 0 for d in DIMS}, "undetermined", "context_insufficient"),
        ({d: PENDING for d in DIMS}, "undetermined", "context_insufficient"),
    ]
    for value, status, assessment in machine_cases:
        try:
            machine_labels({"labels": value, "judgement_status": status, "input_assessment_status": assessment})
        except ValueError:
            pass
        else:
            raise AssertionError("Unauthorized machine-null/label mapping accepted")
    for assessment in ("context_insufficient", "text_problem"):
        parsed, converted = machine_labels({"labels": {d: None for d in DIMS}, "judgement_status": "undetermined", "input_assessment_status": assessment})
        require(converted and set(parsed.values()) == {PENDING}, "Authorized pending not retained")
    checks["explicit_machine_pending_rule"] = {"status": "passed", "rejected_cases": len(machine_cases), "authorized_statuses": 2}
    try:
        check_unchanged({"synthetic": "a"}, {"synthetic": "b"})
    except ValueError:
        checks["post_evaluation_input_change_guard"] = "passed"
    else:
        raise AssertionError("Changed snapshot accepted")
    result = evaluate(fixture)
    require(set(result["comparisons"]) == {"A_vs_C", "dictionary_vs_A", "dictionary_vs_C"}, "Comparison inventory wrong")
    require(result["design_and_interval_metadata"]["sample_size_matches_H600_plan"] is True, "Formal sample size guard failed")
    require(result["comparisons"]["dictionary_vs_A"]["reference_info"]["coder"] == "A" and
            result["comparisons"]["dictionary_vs_C"]["reference_info"]["coder"] == "C", "Reference provenance wrong")
    require(result["archive"]["raw_coder_submissions"] == archive["raw_coder_submissions"], "Original submissions changed")
    checks["two_real_metric_calls_one_original_A_C_no_consensus_reference"] = "passed"
    # Mock publication system calls so QA creates no third file or temporary artifact.
    from unittest.mock import patch
    for exists in (True, False):
        if exists:
            with patch("os.path.lexists", return_value=True):
                try:
                    publish_json(Path("/synthetic-only/existing.json"), {})
                except ValueError:
                    pass
                else:
                    raise AssertionError("Existing output accepted")
        else:
            from io import BytesIO
            class MemoryStream(BytesIO):
                def fileno(self): return 12345
                def close(self): pass
            memory = MemoryStream()
            with patch("os.path.lexists", return_value=False), patch.object(Path, "open", return_value=memory) as opened, \
                 patch("os.fsync"), patch("os.link") as linked, patch.object(Path, "unlink") as unlinked:
                publish_json(Path("/synthetic-only/new.json"), {"synthetic": True})
                require(opened.call_args.args == ("xb",), "Partial file not exclusive")
                require(linked.call_count == 1 and unlinked.call_count == 1, "Atomic publication protocol missing")
                require(json.loads(memory.getvalue())["synthetic"] is True, "Partial content wrong")
    checks["exclusive_partial_atomic_publication_mock_only"] = "passed"
    return {"status": "passed_synthetic_QA_only", "real_policy_text_read": False, "real_labels_read": False,
            "real_results_generated": False, "code_sha256": sha(bridge_bytes), "survey_metrics_sha256": sha(metric_bytes),
            "synthetic_sample_n": 26, "synthetic_batches_per_coder": 2,
            "checks": checks, "machine_pending_rule": PENDING_RULE,
            "limits": ["No actual H600 or freeze manifest was read.",
                "Publication was mocked to avoid writing any temporary study artifact; actual filesystem durability was not benchmarked.",
                "Synthetic checks verify structural/provenance safeguards, not evidence correctness or semantic label validity.",
                "Statistical interval limitations remain those of the frozen survey_metrics implementation."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--holdout", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--synthetic-qa", action="store_true")
    args = parser.parse_args()
    if args.synthetic_qa:
        require(args.freeze is None and args.holdout is None, "Synthetic QA accepts no study inputs")
        output = self_test()
    else:
        require(args.freeze is not None and args.holdout is not None, "Explicit --freeze and --holdout required")
        require(not os.path.lexists(args.output) and not os.path.lexists(args.output.with_name("." + args.output.name + ".partial")),
                "Refusing existing output or partial output")
        bundle, tracked, inventory = load_snapshot(args.freeze, args.holdout)
        output = evaluate(bundle)
        current = {path: sha(Path(path).read_bytes()) for path in tracked}
        check_unchanged(tracked, current)
        current_inventory = {"results": sorted(str(p.relative_to(args.holdout)) for p in args.holdout.glob("agent-*/结果-*.json")),
                             "materials": sorted(str(p.relative_to(args.holdout)) for p in args.holdout.glob("agent-*/材料-*.json"))}
        check_unchanged(inventory, current_inventory)
        output["archive"]["filesystem_snapshot_manifest"] = tracked
        output["archive"]["input_inventory"] = inventory
    publish_json(args.output, output)
    print(json.dumps({"output": str(args.output), "status": output["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
