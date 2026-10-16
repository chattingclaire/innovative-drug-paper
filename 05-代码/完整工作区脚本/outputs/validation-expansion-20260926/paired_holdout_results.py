"""Strict V600 paired-version submission bridge; import performs no study I/O.

Pure API: assemble(bundle) -> (paired_payload, archive); evaluate(bundle) -> result.
Bundle byte snapshots: freeze, seal, frozen={freeze.files key:bytes},
released={relative sealed path:bytes}, results={relative submission path:bytes}.
All original submissions and both selected machine records are archived unchanged.
There is no consensus reference, pending imputation, redrawing, or best-version
selection. Machine null handling is exactly the frozen legacy helper's contract.

CLI takes an explicit final --freeze, --holdout and new --output. It snapshots
and validates everything, runs only hash-verified metric sources, rechecks file
hashes/inventories, and publishes via an exclusive partial plus no-overwrite link.
--synthetic-qa accepts no study inputs and reads only the named code dependencies.

Frozen helper modules are executed in isolated namespaces. Their imports are
allowlisted, and paired_version_metrics' survey_metrics import is intercepted to
the verified in-memory module; no study-local Python module is imported by name.
Python/NumPy runtime versions are recorded, not falsely described as frozen files.
Hashes cannot establish honest blinding, semantic correctness, or unknown exposure.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import types

DIMS = ("S", "E", "Ec", "I", "F")
PENDING = "待定"
PHASE = "V600"
SAMPLING_SEED = 2026092605
BOOTSTRAP_SEED = 2026092606
BUDGET = 600
REQUIRED_FROZEN = {
    "corpus", "adapter", "classification", "exposure", "protocol",
    "baseline_dictionary", "baseline_predictions", "candidate_dictionary",
    "candidate_predictions", "sampler", "sample_helpers", "survey_metrics",
    "paired_version_metrics", "results_bridge", "legacy_results_helpers",
    "analysis_plan", "reviewer_instructions", "protocol_clarifications",
}
STATIC_DOCS = {"protocol": "五维共用编码协议.md", "reviewer_instructions": "评审任务说明.md",
               "protocol_clarifications": "共同执行澄清.md"}
CONTEXT_USAGE = "只编码text；使用核验语境消解对象、条件、指代，不复制上级全标签。nearest_preceding_heading和immediately_preceding_paragraph仅表示位置相邻，未经核验不可自动当有效父级。材料不足保留待定。"
STANDARD_IMPORTS = {
    "__future__", "argparse", "collections", "copy", "datetime", "hashlib",
    "itertools", "json", "math", "os", "pathlib", "random", "re", "sys",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    require(isinstance(data, bytes), "SHA input must be bytes")
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def adapter_digest_json(value):
    """Exact policy_statistics_adapter.py digest_json contract, inspected 2026-09-26.

    The builder uses this serialization for binding, prepared payload and each
    complete raw corpus record. Do not substitute the pretty-printed encoded().
    """
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode())


def nonempty(value, name):
    require(isinstance(value, str) and bool(value.strip()), name + ": nonempty string required")
    return value


def positive_int(value, name):
    require(type(value) is int and value > 0, name + ": positive integer required")
    return value


def hash_value(value, name):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            name + ": lowercase SHA-256 required")
    return value


def read_json(data, name):
    require(isinstance(data, bytes), name + ": byte snapshot required")
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, name + ": duplicate JSON key " + key)
            out[key] = value
        return out
    def bad(value):
        raise ValueError(name + ": nonfinite JSON constant " + value)
    result = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad)
    require(isinstance(result, dict), name + ": JSON object required")
    def finite(value):
        if isinstance(value, dict):
            for item in value.values(): finite(item)
        elif isinstance(value, list):
            for item in value: finite(item)
        elif isinstance(value, float):
            require(math.isfinite(value), name + ": nonfinite JSON number")
    finite(result)
    return result


def unique_rows(rows, key, name):
    require(isinstance(rows, list), name + ": row list required")
    out = {}
    for row in rows:
        require(isinstance(row, dict), name + ": row object required")
        value = nonempty(row.get(key), name + "." + key)
        require(value not in out, name + ": duplicate " + key + " " + value)
        out[value] = row
    return out


def relative_name(name):
    nonempty(name, "relative path")
    p = PurePosixPath(name)
    require(not p.is_absolute() and ".." not in p.parts and str(p) == name
            and "\\" not in name and name not in {".", ""}, "Unsafe/noncanonical relative path")
    return name


def numeric_equal(value, expected, name):
    require(type(value) in (int, float) and math.isfinite(value)
            and math.isclose(value, expected, rel_tol=1e-12, abs_tol=1e-12), name + ": numeric mismatch")


def source_module(data, name, dependencies=None, numpy_allowed=False):
    """Execute already hash-verified source, with no implicit study-local imports."""
    dependencies = dependencies or {}
    allowed = STANDARD_IMPORTS | ({"numpy"} if numpy_allowed else set())
    def frozen_import(module_name, globals=None, locals=None, fromlist=(), level=0):
        require(level == 0, "Relative imports forbidden in frozen runtime: " + module_name)
        if module_name in dependencies:
            return dependencies[module_name]
        root = module_name.split(".")[0]
        require(root in allowed, "Unfrozen/unsupported runtime import: " + module_name)
        return builtins.__import__(module_name, globals, locals, fromlist, level)
    runtime_builtins = dict(vars(builtins))
    runtime_builtins["__import__"] = frozen_import
    module = types.ModuleType("_frozen_" + name)
    module.__file__ = "<frozen " + name + ".py>"
    module.__dict__["__builtins__"] = runtime_builtins
    exec(compile(data, module.__file__, "exec"), module.__dict__)
    return module


def dictionary_version(data, expected, name):
    """Read the literal top-level VERSION without executing either dictionary."""
    tree = ast.parse(data, filename="<frozen " + name + ">")
    values = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "VERSION" for t in node.targets):
            values.append(ast.literal_eval(node.value))
    require(values == [expected], name + ": dictionary VERSION differs from freeze")


def validate_adapter_binding(adapter, classification, analysis, files):
    """Verify declared binding against this exact corpus, not another hash string.

    This does not reopen source/metadata paths or print adapter units. The
    externally verified physical files remain represented by their frozen
    manifest. Corpus/classification are checked against actual frozen bytes.
    """
    binding = adapter.get("binding")
    require(isinstance(binding, dict), "Adapter binding object required")
    require(hash_value(adapter.get("binding_sha256"), "adapter.binding_sha256") == adapter_digest_json(binding),
            "Adapter binding hash does not match canonical binding serialization")
    inputs = binding.get("input_sha256")
    require(isinstance(inputs, dict), "Adapter input_sha256 required")
    for name in ("corpus", "classification"):
        require(hash_value(inputs.get(name), "adapter.input_sha256." + name) == files[name]["sha256"],
                "Adapter " + name + " input hash differs from frozen bytes")
    if "metadata" in inputs:
        hash_value(inputs["metadata"], "adapter.input_sha256.metadata")
        if "metadata" in files:
            require(inputs["metadata"] == files["metadata"]["sha256"], "Adapter metadata input hash differs from frozen bytes")
    require(binding.get("adapter_version") == nonempty(adapter.get("version"), "adapter.version"), "Adapter version/binding mismatch")
    require(binding.get("classification_version") == nonempty(classification.get("version"), "classification.version"),
            "Adapter classification version mismatch")
    prepared = unique_rows(adapter.get("units"), "id", "adapter prepared units")
    require(set(prepared) == set(analysis), "Adapter prepared/corpus ID set mismatch")
    require(hash_value(binding.get("prepared_payload_sha256"), "adapter.prepared_payload_sha256") ==
            adapter_digest_json({"documents": adapter["documents"], "units": adapter["units"]}), "Adapter prepared payload hash mismatch")
    fingerprints = binding.get("analysis_unit_fingerprints")
    require(isinstance(fingerprints, dict) and set(fingerprints) == set(analysis), "Adapter analysis fingerprints ID set mismatch")
    for key, raw in analysis.items():
        expected = adapter_digest_json(raw)
        require(hash_value(fingerprints[key], "analysis fingerprint") == expected, "Adapter corpus record/context fingerprint mismatch: " + key)
        require(prepared[key].get("record_sha256") == expected, "Adapter prepared record/context fingerprint mismatch: " + key)
        require(prepared[key].get("unit_text_sha256") == sha(raw["unit_text"].encode())
                and prepared[key].get("text") == raw["unit_text"], "Adapter prepared source text mismatch: " + key)
    verified = adapter.get("verified_files")
    require(isinstance(verified, dict), "Adapter verified-files manifest required")
    require(hash_value(binding.get("verified_files_sha256"), "adapter.verified_files_sha256") == adapter_digest_json(verified),
            "Adapter verified-files manifest hash mismatch")
    return fingerprints


def validate_frozen(bundle):
    require(isinstance(bundle, dict) and set(bundle) == {"freeze", "seal", "frozen", "released", "results"},
            "Exact byte bundle fields required")
    freeze = read_json(bundle["freeze"], "freeze")
    require(freeze.get("status") == "frozen_for_paired_reference_label_holdout", "Freeze is not final paired freeze")
    require(freeze.get("phase") == PHASE, "Wrong freeze phase")
    for key, value in (("sampling_seed", SAMPLING_SEED), ("bootstrap_seed", BOOTSTRAP_SEED), ("sample_budget", BUDGET)):
        require(type(freeze.get(key)) is int and freeze[key] == value, "Wrong frozen " + key)
    for key in ("protocol_version", "baseline_version", "candidate_version"):
        nonempty(freeze.get(key), "freeze." + key)
    require(freeze["baseline_version"] != freeze["candidate_version"], "Baseline/candidate version names must be distinct")
    files = freeze.get("files")
    require(isinstance(files, dict) and REQUIRED_FROZEN <= set(files), "Missing required frozen file")
    require(isinstance(bundle["frozen"], dict) and set(bundle["frozen"]) == set(files), "Frozen snapshot inventory mismatch")
    for name, entry in files.items():
        require(isinstance(entry, dict), "Frozen entry must be an object")
        require(Path(nonempty(entry.get("path"), name + ".path")).is_absolute(), "Frozen paths must be absolute")
        require(sha(bundle["frozen"][name]) == hash_value(entry.get("sha256"), name + ".sha256"),
                "Frozen file hash mismatch: " + name)
    return freeze


def assemble(bundle):
    """Pure validation/ID join; seeded reproduction is verification, never a new release."""
    freeze = validate_frozen(bundle)
    files, frozen = freeze["files"], bundle["frozen"]
    helpers = source_module(frozen["sample_helpers"], "sample_helpers")
    legacy = source_module(frozen["legacy_results_helpers"], "legacy_results_helpers")
    require(tuple(legacy.DIMS) == DIMS, "Legacy dimensions changed")
    version = freeze["protocol_version"]
    fields = freeze.get("context_fields")
    require(isinstance(fields, list) and fields and all(isinstance(f, str) for f in fields)
            and len(fields) == len(set(fields)), "Explicit unique context_fields required")
    # Read only the supplied byte snapshot, never source paths inside metadata.
    corpus = [read_json(line, "corpus line " + str(i))
              for i, line in enumerate(frozen["corpus"].splitlines(), 1) if line.strip()]
    allunits = unique_rows(corpus, "review_id", "corpus")
    require(all(type(r.get("count_as_analysis_unit")) is bool for r in corpus), "Corpus analysis flags must be literal booleans")
    analysis = {k: r for k, r in allunits.items() if r["count_as_analysis_unit"]}
    require(analysis, "Empty analysis corpus")
    for row in analysis.values():
        require(isinstance(row.get("unit_text"), str), "Corpus unit text must be a string")
    adapter = read_json(frozen["adapter"], "adapter")
    classification = read_json(frozen["classification"], "classification")
    record_fingerprints = validate_adapter_binding(adapter, classification, analysis, files)
    exposure = read_json(frozen["exposure"], "exposure")
    eligible = exposure.get("provisional_eligible_ids")
    require(isinstance(eligible, list) and all(isinstance(x, str) and x for x in eligible)
            and len(eligible) == len(set(eligible)), "Eligible IDs must be unique strings")
    excluded = exposure.get("exclusions")
    require(isinstance(excluded, list), "Exposure exclusion list required")
    excluded_ids = list(excluded)
    require(all(isinstance(x, str) and x for x in excluded_ids) and len(excluded_ids) == len(set(excluded_ids)),
            "Excluded IDs must be unique strings")
    require(not set(eligible) & set(excluded_ids) and set(eligible) | set(excluded_ids) == set(analysis),
            "Exposure must partition the analysis corpus")
    units, pools, metadata = helpers.frame(corpus, adapter, classification, exposure)
    counts = {h: len(rows) for h, rows in sorted(pools.items())}
    allocation = helpers.allocate(counts, BUDGET)  # deterministic allocation check, never random sampling
    expected_strata = {h: {"N_h": N, "n_h": allocation[h], "pi": allocation[h] / N,
                            "weight": N / allocation[h]} for h, N in counts.items()}
    seal = read_json(bundle["seal"], "seal")
    require(seal.get("status") == "drawn" and seal.get("release_status") == "ready_for_blind_review", "Holdout is not released")
    require(seal.get("freeze_manifest_sha256") == sha(bundle["freeze"]), "Release freeze manifest hash mismatch")
    outputs = seal.get("output_files")
    require(isinstance(outputs, dict) and outputs, "Released output hash manifest required")
    require(isinstance(bundle["released"], dict) and set(bundle["released"]) == set(outputs), "Released inventory differs from seal")
    for name, digest in outputs.items():
        relative_name(name)
        require(sha(bundle["released"][name]) == hash_value(digest, name), "Released file hash mismatch: " + name)
    map_name = "抽样清单-研究者.json"
    require(map_name in outputs, "Researcher mapping is not sealed")
    mapping = read_json(bundle["released"][map_name], map_name)
    plan = mapping.get("plan")
    require(isinstance(plan, dict), "Mapping plan required")
    require(all(key in seal and value == seal[key] for key, value in plan.items()), "Mapping plan differs from release seal")
    require(plan.get("status") == "drawn" and plan.get("phase") == PHASE
            and type(plan.get("seed")) is int and plan["seed"] == SAMPLING_SEED, "Unexpected mapping phase/status/seed")
    require(plan.get("freeze_manifest_sha256") == sha(bundle["freeze"]), "Mapping freeze hash mismatch")
    require(plan.get("input_hashes") == {name: item["sha256"] for name, item in files.items()}, "Plan input hashes differ from freeze")
    N, n = positive_int(plan.get("N_star"), "N_star"), positive_int(plan.get("n"), "sample n")
    require(N == len(eligible) and n == min(BUDGET, N), "Sample/frame size differs from V600 plan")
    manifest = plan.get("strata")
    require(isinstance(manifest, dict) and set(manifest) == set(expected_strata), "Stratum inventory differs from frozen frame")
    strata = []
    for h, expected in expected_strata.items():
        spec = manifest[h]
        require(isinstance(spec, dict), "Stratum specification must be object")
        for key in ("N_h", "n_h"):
            require(type(spec.get(key)) is int and spec[key] == expected[key], "Stratum size/allocation mismatch")
        for key in ("pi", "weight"):
            numeric_equal(spec.get(key), expected[key], "Stratum " + key)
        strata.append({"stratum": h, "N_h": expected["N_h"], "n_h": expected["n_h"]})
    maps = unique_rows(mapping.get("rows"), "id", "mapping")
    original_ids = unique_rows(mapping["rows"], "review_id", "mapping review IDs")
    require(len(maps) == n and list(maps) == [f"V600-{i:04d}" for i in range(1, n + 1)], "Mapping V600 ID/count/order mismatch")
    require(set(original_ids) <= set(eligible), "Selected IDs outside eligible frame")
    for key, row in maps.items():
        original = row["review_id"]
        require(all(row.get(k) == v for k, v in metadata[original].items()), "Mapping source/stratum metadata mismatch")
        h = metadata[original]["stratum"]
        for field in ("N_h", "n_h"):
            require(type(row.get(field)) is int and row[field] == expected_strata[h][field], "Mapping stratum size mismatch")
        for field in ("pi", "weight"):
            numeric_equal(row.get(field), expected_strata[h][field], "Mapping " + field)
        require(hash_value(row.get("unit_text_sha256"), "mapping text hash") == sha(units[original]["unit_text"].encode()), "Mapping/source text hash mismatch")
    for h in manifest:
        require(sum(r["stratum"] == h for r in maps.values()) == manifest[h]["n_h"], "Actual per-stratum n mismatch")
    unselected = mapping.get("not_selected_ids")
    require(isinstance(unselected, list) and all(isinstance(x, str) and x for x in unselected)
            and len(unselected) == len(set(unselected)) and set(unselected) == set(eligible) - set(original_ids),
            "Selected/unselected IDs do not partition frozen eligible frame")
    # Reproduce identities in memory solely to verify the already sealed draw.
    # This cannot publish a sample, change its seed, or replace the release.
    sampler = source_module(frozen["sampler"], "sampler")
    require(sampler.PHASE == PHASE and type(sampler.SEED) is int and sampler.SEED == SAMPLING_SEED
            and type(sampler.BUDGET) is int and sampler.BUDGET == BUDGET, "Frozen sampler design mismatch")
    require(sampler.STATIC_DOCS == STATIC_DOCS, "Frozen sampler shared-document inventory mismatch")
    reconstructed, reconstructed_materials = sampler.construct(corpus, adapter, classification, exposure, fields, helpers.__dict__)
    require(mapping["rows"] == reconstructed["rows"] and unselected == reconstructed["not_selected_ids"],
            "Sealed sample does not reproduce from frozen seed/frame/sampler")
    for field in ("random_generator", "ordering"):
        require(plan.get(field) == reconstructed["plan"][field], "Sampling runtime/design metadata mismatch")
    nonempty(plan.get("python_version"), "plan.python_version")
    # The frozen sampler owns the approved ten-field object-scope contract,
    # including component-bound renewal scopes and their jointly released branch.
    expected_materials_by_id = unique_rows(reconstructed_materials, "id", "reconstructed materials")
    require(list(expected_materials_by_id) == list(maps), "Reconstructed material IDs differ from sample")
    batches = math.ceil(n / 25)
    material_names = {f"agent-{c}/材料-{b:02d}.json" for c in ("A", "C") for b in range(1, batches + 1)}
    result_names = {f"agent-{c}/结果-{b:02d}.json" for c in ("A", "C") for b in range(1, batches + 1)}
    manual_names = {f"agent-{c}/{filename}" for c in ("A", "C") for filename in STATIC_DOCS.values()}
    require(set(outputs) == material_names | manual_names | {map_name}, "Unexpected/incomplete released file set")
    require(isinstance(bundle["results"], dict) and set(bundle["results"]) == result_names, "Missing/extra result batch files")
    submitted, raw_submissions, packets, submissions = {"A": {}, "C": {}}, {}, {}, {}
    for coder in ("A", "C"):
        for key, filename in STATIC_DOCS.items():
            require(bundle["released"][f"agent-{coder}/{filename}"] == frozen[key], "Coder shared document differs from freeze: " + filename)
        for batch in range(1, batches + 1):
            pn, rn = f"agent-{coder}/材料-{batch:02d}.json", f"agent-{coder}/结果-{batch:02d}.json"
            raw = bundle["released"][pn]
            require(raw == bundle["released"][f"agent-A/材料-{batch:02d}.json"], "A/C material packets differ")
            packet = read_json(raw, pn)
            require(packet.get("protocol_version") == version and type(packet.get("batch")) is int and packet["batch"] == batch
                    and type(packet.get("total_batches")) is int and packet["total_batches"] == batches, "Material version/batch mismatch")
            require(packet.get("purpose") == "reference_label_holdout_AI_independent", "Wrong material purpose")
            prows = unique_rows(packet.get("rows"), "id", pn)
            expected_ids = list(maps)[(batch - 1) * 25:batch * 25]
            require(list(prows) == expected_ids, "Material/mapping batch ID mismatch")
            for key, row in prows.items():
                source = units[maps[key]["review_id"]]
                expected = expected_materials_by_id[key]
                require(row == expected, "Material row differs from frozen source/context/assessment: " + key)
                require(row["text"] == source["unit_text"] and row["source_title"] == source["original_file_stem"], "Material source/text mismatch")
                require(sha(row["text"].encode()) == maps[key]["unit_text_sha256"], "Material text hash mismatch")
            document = read_json(bundle["results"][rn], rn)
            identity = document.get("identity")
            require(isinstance(identity, dict) and identity.get("kind") == "AI", rn + ": identity must be an object with kind=AI")
            nonempty(identity.get("name"), rn + ".identity.name")
            rrows = legacy.validate_result(document, coder, version, packet, sha(raw), rn)
            for field in ("batch", "total_batches"):
                if field in document:
                    require(type(document[field]) is int, "Submission batch headers must be literal integers")
            for row in rrows.values():
                nonempty(row.get("material_issue"), rn + ".material_issue")
            require(not set(submitted[coder]) & set(rrows), "Duplicate coder ID across batches")
            submitted[coder].update(rrows)
            raw_submissions[rn] = document
            packets[pn] = {"sha256": sha(raw), "ids": expected_ids, "batch": batch}
            submissions[rn] = {"sha256": sha(bundle["results"][rn]), "coder": coder, "ids": list(rrows), "input_packet_sha256": sha(raw)}
        require(set(submitted[coder]) == set(maps), "Incomplete coder submission set")
    # Both prediction inventories and input bindings are validated, never joined by row order.
    all_predictions, prediction_documents, pending, info = {}, {}, {}, {}
    for tag in ("baseline", "candidate"):
        code_key, pred_key = tag + "_dictionary", tag + "_predictions"
        declared_version = freeze[tag + "_version"]
        dictionary_version(frozen[code_key], declared_version, code_key)
        document = read_json(frozen[pred_key], pred_key)
        predictions = unique_rows(document.get("rows"), "id", pred_key)
        require(set(predictions) == set(analysis), tag + ": Prediction/corpus analysis ID set mismatch")
        require(hash_value(document.get("binding_sha256"), tag + ".binding_sha256") == hash_value(adapter.get("binding_sha256"), "adapter.binding_sha256"), tag + ": binding hash mismatch")
        require(document.get("coder_sha256") == files[code_key]["sha256"], tag + ": coder hash mismatch")
        require(document.get("codebook_sha256") == files["protocol"]["sha256"], tag + ": protocol hash mismatch")
        if "version" in document:
            require(document["version"] == declared_version, tag + ": document version mismatch")
        parsed = {}
        for original, prediction in predictions.items():
            require(prediction.get("version") == declared_version, tag + ": row version mismatch")
            require(prediction.get("unit_text_sha256") == sha(analysis[original]["unit_text"].encode()), tag + ": prediction/source text hash mismatch")
            require(prediction.get("record_sha256") == record_fingerprints[original], tag + ": prediction/source record-context hash mismatch")
            parsed[original] = legacy.machine_labels(prediction)
            if not parsed[original][1]:
                require(prediction.get("input_assessment_status") not in {"context_insufficient", "text_problem"}, tag + ": binary machine labels contradict insufficient input")
        all_predictions[tag] = predictions
        prediction_documents[tag] = {k: copy.deepcopy(v) for k, v in document.items() if k != "rows"}
        pending[tag] = [key for key, row in maps.items() if parsed[row["review_id"]][1]]
        info[tag] = {"version": declared_version, "prediction_sha256": files[pred_key]["sha256"],
                     "implementation": copy.deepcopy(files[code_key]), "predictions": copy.deepcopy(files[pred_key]),
                     "input_binding_sha256": document["binding_sha256"], "protocol_sha256": document["codebook_sha256"],
                     "pending_rule": copy.deepcopy(legacy.PENDING_RULE), "pending_conversion_ids": pending[tag],
                     "description": "Frozen " + tag + " dictionary; no selection after reference submission."}
    normalized, selected = [], {"baseline": {}, "candidate": {}}
    for key, row in maps.items():
        joined = {"id": key, "stratum": row["stratum"], "N_h": row["N_h"], "n_h": row["n_h"],
                  "A": legacy.labels(submitted["A"][key]["labels"], "A"), "C": legacy.labels(submitted["C"][key]["labels"], "C")}
        for tag in ("baseline", "candidate"):
            record = all_predictions[tag][row["review_id"]]
            selected[tag][key] = copy.deepcopy(record)
            joined[tag] = legacy.machine_labels(record)[0]
        normalized.append(joined)
    coders = {}
    for coder in ("A", "C"):
        provenance = {name: {k: copy.deepcopy(obj[k]) for k in ("identity", "completed_at", "protocol_version", "input_packet_sha256")}
                      for name, obj in raw_submissions.items() if name.startswith(f"agent-{coder}/")}
        coders[coder] = {"kind": "AI", "coder": coder, "description": "Original independent AI coder " + coder + "; not human or consensus gold truth.",
                         "original_submission_provenance": provenance,
                         "submission_hashes": {name: item["sha256"] for name, item in submissions.items() if name.startswith(f"agent-{coder}/")}}
    payload = {"strata": strata, "population_N": N, "rows": copy.deepcopy(normalized), "coders": coders,
               "baseline_info": info["baseline"], "candidate_info": info["candidate"]}
    archive = {"freeze_manifest_original": freeze, "release_seal_original": seal, "sampling_manifest_original": mapping,
               "raw_coder_submissions": raw_submissions, "selected_machine_records_by_version_and_blind_id": selected,
               "prediction_document_metadata_original": prediction_documents,
               "normalized_rows_without_generated_reference": normalized, "packet_manifest": packets,
               "original_submission_manifest": submissions, "machine_null_conversion_rule": copy.deepcopy(legacy.PENDING_RULE),
               "pending_machine_ids_by_version": pending, "reference_created_by_consensus_or_imputation": False,
               "input_snapshot_hashes": {"freeze": sha(bundle["freeze"]), "seal": sha(bundle["seal"]),
                   "frozen": {name: sha(data) for name, data in frozen.items()}, "released": dict(outputs),
                   "submissions": {name: sha(data) for name, data in bundle["results"].items()}},
               "frame_validation": {"analysis_units": len(analysis), "eligible_N": N, "excluded_n": len(excluded_ids),
                   "selected_unselected_partition_verified": True, "allocation_verified": True,
                   "adapter_binding_digest_recomputed": True, "adapter_corpus_and_classification_bytes_verified": True,
                   "full_corpus_record_and_prediction_context_fingerprints_verified": True,
                   "fixed_seed_sample_identities_reproduced_in_memory_only": True,
                   "original_sampling_python_version": plan["python_version"],
                   "verification_python_version": sys.version}}
    return payload, archive


def evaluate(bundle):
    payload, archive = assemble(bundle)
    base = source_module(bundle["frozen"]["survey_metrics"], "survey_metrics", numpy_allowed=True)
    metrics = source_module(bundle["frozen"]["paired_version_metrics"], "paired_version_metrics", {"survey_metrics": base}, numpy_allowed=True)
    require(metrics.base is base, "Paired metrics did not use frozen survey dependency")
    require(tuple(metrics.DIMS) == DIMS and metrics.SEED == BOOTSTRAP_SEED, "Paired metrics dimensions/bootstrap seed mismatch")
    original_payload = copy.deepcopy(payload)
    result = metrics.analyze(payload)
    require(payload == original_payload, "Statistics mutated analysis payload")
    require(result.get("sample_n") == len(payload["rows"]) and result.get("population_N") == payload["population_N"], "Statistics changed sample/frame size")
    require(result.get("reference_generated") is False, "Statistics generated a reference")
    expected = {"A_vs_C", "baseline_vs_A", "baseline_vs_C", "candidate_vs_A", "candidate_vs_C"}
    require(set(result.get("comparisons", {})) == expected and set(result.get("paired_differences", {})) == {"A", "C"}, "Paired comparison inventory mismatch")
    require(result.get("bootstrap", {}).get("seed") == BOOTSTRAP_SEED, "Output bootstrap seed mismatch")
    for tag in ("baseline", "candidate"):
        require(result.get("versions", {}).get(tag) == payload[tag + "_info"], "Statistics changed version metadata")
    archive["runtime"] = {"python": sys.version, "numpy": metrics.np.__version__,
                          "frozen_module_hashes": {k: sha(bundle["frozen"][k]) for k in ("sampler", "sample_helpers", "legacy_results_helpers", "survey_metrics", "paired_version_metrics")},
                          "local_survey_import_intercepted": True}
    return {"status": "completed_frozen_paired_ID_join_not_validation_pass", "created_at": datetime.now(timezone.utc).isoformat(),
            "phase": PHASE, "paired_statistics": result, "archive": archive,
            "interpretation": ["Both AI references and both dictionary versions share one sample; n is not doubled.",
                "No consensus reference, missing-label imputation, or best-version/reference selection is generated.",
                "Paired differences apply to each reference's jointly definite subset and require joint-coverage reporting.",
                "Hashes do not establish honest blinding, semantic correctness, correct exposure history, or unseen text.",
                "Machine record_sha256 is retained and verified using the inspected adapter builder's canonical full-record JSON serialization.",
                "Physical source/metadata files outside freeze.files are not reopened; their earlier verification is represented by the frozen adapter manifest."]}


def check_unchanged(before, after):
    require(before == after, "Input file or inventory changed during evaluation; output not released")


def inventories(holdout):
    return {"results": sorted(str(p.relative_to(holdout)) for p in holdout.glob("agent-*/结果-*.json")),
            "materials": sorted(str(p.relative_to(holdout)) for p in holdout.glob("agent-*/材料-*.json"))}


def load_snapshot(freeze_path, holdout):
    require(freeze_path.is_absolute() and holdout.is_absolute(), "Use absolute freeze and holdout paths")
    tracked = {}
    def read(path):
        path = Path(path)
        raw = path.read_bytes()
        if str(path) in tracked:
            require(tracked[str(path)] == sha(raw), "Input changed while snapshot was read")
        tracked[str(path)] = sha(raw)
        return raw
    freeze_raw = read(freeze_path)
    freeze = read_json(freeze_raw, "freeze")
    require(isinstance(freeze.get("files"), dict) and REQUIRED_FROZEN <= set(freeze["files"]), "Missing frozen files")
    frozen = {}
    for name, entry in freeze["files"].items():
        require(isinstance(entry, dict) and Path(nonempty(entry.get("path"), name + ".path")).is_absolute(), "Frozen paths must be absolute")
        frozen[name] = read(Path(entry["path"]))
    running_bridge = read(Path(__file__).resolve())
    require(sha(running_bridge) == freeze["files"]["results_bridge"]["sha256"], "Running bridge is not frozen bridge")
    seal_raw = read(holdout / "封存信息.json")
    seal = read_json(seal_raw, "seal")
    require(isinstance(seal.get("output_files"), dict), "Seal output inventory required")
    def inside(name):
        relative_name(name)
        path = holdout / name
        require(path.resolve().is_relative_to(holdout.resolve()), "Input escapes holdout directory")
        return path
    released = {name: read(inside(name)) for name in seal["output_files"]}
    inventory = inventories(holdout)
    results = {name: read(inside(name)) for name in inventory["results"]}
    expected_materials = sorted(name for name in released if re.fullmatch(r"agent-[AC]/材料-\d{2}\.json", name))
    require(inventory["materials"] == expected_materials, "Unsealed/missing material packet inventory")
    return {"freeze": freeze_raw, "seal": seal_raw, "frozen": frozen, "released": released, "results": results}, tracked, inventory


def publish_json(path, obj):
    path = Path(path)
    partial = path.with_name("." + path.name + ".partial")
    require(not os.path.lexists(path) and not os.path.lexists(partial), "Refusing existing output or partial output")
    with partial.open("xb") as stream:
        stream.write(encoded(obj))
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--holdout", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--synthetic-qa", action="store_true")
    args = parser.parse_args()
    require(not os.path.lexists(args.output) and not os.path.lexists(args.output.with_name("." + args.output.name + ".partial")), "Refusing existing output or partial output")
    if args.synthetic_qa:
        require(args.freeze is None and args.holdout is None, "Synthetic QA accepts no study inputs")
        output = self_test()
    else:
        require(args.freeze is not None and args.holdout is not None, "Explicit --freeze and --holdout required")
        bundle, tracked, inventory = load_snapshot(args.freeze, args.holdout)
        output = evaluate(bundle)
        check_unchanged(tracked, {path: sha(Path(path).read_bytes()) for path in tracked})
        check_unchanged(inventory, inventories(args.holdout))
        output["archive"]["filesystem_snapshot_manifest"] = tracked
        output["archive"]["input_inventory"] = inventory
    publish_json(args.output, output)
    print(json.dumps({"output": str(args.output), "status": output["status"]}, ensure_ascii=False))


def synthetic_adapter(corpus, corpus_bytes, classification, classification_bytes, documents):
    """Invented adapter with the real builder's binding serialization contract."""
    units = [{"id": r["review_id"], "document_id": r["original_file_stem"], "text": r["unit_text"],
              "unit_text_sha256": sha(r["unit_text"].encode()), "record_sha256": adapter_digest_json(r)}
             for r in corpus if r["count_as_analysis_unit"]]
    verified = {"/synthetic-only/fictional-source.txt": "f" * 64}
    binding = {"adapter_version": "synthetic-adapter-v1", "verified_files_sha256": adapter_digest_json(verified),
               "input_sha256": {"corpus": sha(corpus_bytes), "metadata": sha(b"SYNTHETIC METADATA ONLY"),
                                "classification": sha(classification_bytes)},
               "input_paths": {k: "/synthetic-only/" + k for k in ("corpus", "metadata", "classification")},
               "prepared_payload_sha256": adapter_digest_json({"documents": documents, "units": units}),
               "classification_version": classification["version"],
               "analysis_unit_fingerprints": {u["id"]: u["record_sha256"] for u in units}}
    return {"version": "synthetic-adapter-v1", "documents": documents, "units": units,
            "verified_files": verified, "binding": binding, "binding_sha256": adapter_digest_json(binding)}


def synthetic_bundle(code_sources, include_scopes=True):
    """Only invented text/labels: 28 analysis units, 2 excluded, 26 census cases."""
    frozen = {name: ("SYNTHETIC NONPOLICY " + name).encode() for name in REQUIRED_FROZEN}
    frozen.update(code_sources)
    protocol_version = "SYNTHETIC-PROTOCOL-v1"
    frozen["protocol"] = b"SYNTHETIC MANUAL ONLY; NO POLICY CONTENT"
    corpus = []
    for i in range(28):
        corpus.append({"review_id": f"fiction-{i:04d}", "count_as_analysis_unit": True,
                       "original_file_stem": "fiction-a" if i < 14 else "fiction-b",
                       "unit_text": "FICTIONAL NONPOLICY PLACEHOLDER " + str(i), "pages": [1],
                       "paragraph_context": [{"paragraph_id": "fiction-p" + str(i), "text": "FICTIONAL CONTEXT", "pages": [1]}],
                       "input_assessment": {"status": "not_assessed"}})
    if include_scopes:
        for index, kind in enumerate(("drug_clinical_trial", "drug_regulatory_research", "anticancer_drug_development", "anticancer_drug_safety_dossier", "negotiated_drug_renewal")):
            unit = corpus[index]
            quote = "虚构范围引文，非政策原文：" + kind
            text_scope = kind == "drug_clinical_trial"
            unit["source_sha256"] = "f" * 64
            unit["verified_object_scope"] = [{"kind": kind, "source_sha256": "f" * 64,
                "unit_text_sha256": sha(unit["unit_text"].encode()), "text": quote, "text_sha256": sha(quote.encode()),
                "locator": {"article": 2, "line": 5, "source": "/synthetic-only/fictional-source.txt"} if text_scope else
                           {"physical_pages": [1, 2], "source": "/synthetic-only/fictional-source.pdf"},
                "verification": "Synthetic scope verification only; no real source claim",
                "normalization": "none" if text_scope else "remove_extraction_whitespace",
                "source_hash_field": "source_sha256", "required_branch_text": None}]
            if kind == "negotiated_drug_renewal":
                # Deliberately distinct announcement/component hashes catch
                # accidental acceptance of the wrong physical source binding.
                unit["unit_source_sha256"] = "e" * 64
                unit["verified_rule_branch_context"] = {"text": "规则 二\n简易续约", "pages": [1],
                    "source": "/synthetic-only/fictional-component.pdf", "source_sha256": "e" * 64,
                    "verification": "Synthetic branch verification; no real source claim"}
                unit["verified_object_scope"][0].update(source_sha256="e" * 64, source_hash_field="unit_source_sha256",
                    required_branch_text="规则二简易续约", locator={"physical_pages": [1, 2], "source": "/synthetic-only/fictional-component.pdf"})
    documents = [
        {"id": "fiction-a", "group": "NHSA", "publication_date": "2025-01-01", "series": "fiction-series"},
        {"id": "fiction-b", "group": "NMPA", "publication_date": "2025-01-01", "series": "fiction-series"}]
    classification = {"version": "synthetic-classification-v1", "rows": [{"original_file": "fiction-a.pdf", "analysis_group": "NHSA"},
                               {"original_file": "fiction-b.pdf", "analysis_group": "NMPA"}]}
    exposure = {"exclusions": ["fiction-0013", "fiction-0027"],
                "provisional_eligible_ids": [r["review_id"] for r in corpus if r["review_id"] not in {"fiction-0013", "fiction-0027"}]}
    frozen["corpus"] = b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in corpus) + b"\n"
    for key, doc in (("classification", classification), ("exposure", exposure)):
        frozen[key] = encoded(doc)
    adapter = synthetic_adapter(corpus, frozen["corpus"], classification, frozen["classification"], documents)
    frozen["adapter"] = encoded(adapter)
    for tag in ("baseline", "candidate"):
        machine_version = "synthetic-" + tag + "-v1"
        frozen[tag + "_dictionary"] = ("VERSION = '" + machine_version + "'\n").encode()
        machine = []
        for i, r in enumerate(corpus):
            pending = i == (0 if tag == "baseline" else 2)
            value = (i % 2) if tag == "baseline" or i != 3 else 0
            machine.append({"id": r["review_id"], "version": machine_version,
                            "unit_text_sha256": sha(r["unit_text"].encode()), "record_sha256": adapter_digest_json(r),
                            "labels": {d: None if pending else value for d in DIMS},
                            "judgement_status": "undetermined" if pending else "rule_prediction",
                            "input_assessment_status": "context_insufficient" if pending else "sufficient"})
        rows = list(reversed(machine)) if tag == "baseline" else machine[8:] + machine[:8]
        frozen[tag + "_predictions"] = encoded({"version": machine_version,
            "binding_sha256": adapter["binding_sha256"], "coder_sha256": sha(frozen[tag + "_dictionary"]),
            "codebook_sha256": sha(frozen["protocol"]), "rows": rows})
    freeze = {"status": "frozen_for_paired_reference_label_holdout", "phase": PHASE,
              "sampling_seed": SAMPLING_SEED, "bootstrap_seed": BOOTSTRAP_SEED, "sample_budget": BUDGET,
              "protocol_version": protocol_version, "baseline_version": "synthetic-baseline-v1",
              "candidate_version": "synthetic-candidate-v1", "context_fields": ["paragraph_context"] + (["verified_object_scope", "verified_rule_branch_context"] if include_scopes else []),
              "files": {name: {"path": "/synthetic-only/" + name, "sha256": sha(raw)} for name, raw in frozen.items()}}
    helpers = source_module(frozen["sample_helpers"], "synthetic_sample_helpers")
    sampler = source_module(frozen["sampler"], "synthetic_sampler")
    mapping, materials = sampler.construct(corpus, adapter, classification, exposure, freeze["context_fields"], helpers.__dict__)
    freeze_bytes = encoded(freeze)
    mapping["plan"].update(freeze_manifest_sha256=sha(freeze_bytes), input_hashes={name: sha(raw) for name, raw in frozen.items()})
    released = {"抽样清单-研究者.json": encoded(mapping)}
    results = {}
    for coder in ("A", "C"):
        for key, filename in STATIC_DOCS.items():
            released[f"agent-{coder}/{filename}"] = frozen[key]
        for batch in (1, 2):
            rows = materials[(batch - 1) * 25:batch * 25]
            packet = {"protocol_version": protocol_version, "purpose": "reference_label_holdout_AI_independent",
                      "batch": batch, "total_batches": 2, "rows": rows}
            pn, rn = f"agent-{coder}/材料-{batch:02d}.json", f"agent-{coder}/结果-{batch:02d}.json"
            released[pn] = encoded(packet)
            judgments = []
            for r in rows:
                original = next(m["review_id"] for m in mapping["rows"] if m["id"] == r["id"])
                i = int(original.split("-")[1])
                value = PENDING if coder == "C" and i == 1 else i % 2
                judgments.append({"id": r["id"], "labels": {d: value for d in DIMS},
                    "dimension_reasons": {d: "Synthetic reason only; no actual policy interpretation" for d in DIMS},
                    "evidence": "FICTIONAL EVIDENCE", "material_issue": "synthetic pending" if value == PENDING else "none",
                    "rationale": "Synthetic fixture; no real coder or policy claim",
                    "fairness_subtypes": ["access"] if value == 1 else [],
                    "innovation_subtypes": ["attribute"] if value == 1 else [],
                    "safety_quality_basis": "undetermined" if value == PENDING else "no_quality_basis",
                    "input_assessment": {"status": "context_insufficient" if value == PENDING else "sufficient", "basis": "Synthetic assessment only"}})
            results[rn] = encoded({"coder": coder, "identity": {"kind": "AI", "name": "SYNTHETIC AI ONLY " + coder},
                "protocol_version": protocol_version, "protocol_acknowledged": True,
                "completed_at": "2000-01-01T00:00:00+00:00", "input_packet_sha256": sha(released[pn]),
                "batch": batch, "total_batches": 2, "rule_questions": [], "rows": list(reversed(judgments))})
    seal = {**mapping["plan"], "release_status": "ready_for_blind_review",
            "output_files": {name: sha(raw) for name, raw in released.items()}}
    return {"freeze": freeze_bytes, "seal": encoded(seal), "frozen": frozen, "released": released, "results": results}


def self_test():
    """QA reads code only and creates no temporary policy/sample artifacts."""
    here = Path(__file__).resolve()
    code_paths = {"results_bridge": here, "sample_helpers": here.with_name("sample_holdout.py"),
                  "legacy_results_helpers": here.with_name("holdout_results.py"), "sampler": here.with_name("sample_paired_holdout.py"),
                  "survey_metrics": here.with_name("survey_metrics.py"), "paired_version_metrics": here.with_name("paired_version_metrics.py")}
    sources = {name: path.read_bytes() for name, path in code_paths.items()}
    fixture = synthetic_bundle(sources)
    payload, archive = assemble(fixture)
    # The older, scope-free packet shape remains accepted with the same binding checks.
    assemble(synthetic_bundle(sources, include_scopes=False))
    require(len(payload["rows"]) == 26 and set(payload["coders"]) == {"A", "C"}, "Synthetic joined rows/coders lost")
    require(all("reference" not in r for r in payload["rows"]), "Manufactured reference")
    maps = {r["id"]: r["review_id"] for r in archive["sampling_manifest_original"]["rows"]}
    for tag, pending_id in (("baseline", "fiction-0000"), ("candidate", "fiction-0002")):
        row = next(r for r in payload["rows"] if maps[r["id"]] == pending_id)
        require(row[tag] == {d: PENDING for d in DIMS}, "Machine pending lost")
    require(next(r for r in payload["rows"] if maps[r["id"]] == "fiction-0001")["C"] == {d: PENDING for d in DIMS}, "AI pending lost")
    raw_corpus = [read_json(line, "synthetic corpus") for line in fixture["frozen"]["corpus"].splitlines()]
    scope_by_original = {r["review_id"]: r["verified_object_scope"] for r in raw_corpus if r.get("verified_object_scope")}
    require(len(scope_by_original) == 5, "All five scope kinds must be exercised")
    branch_by_original = {r["review_id"]: r["verified_rule_branch_context"] for r in raw_corpus if r.get("verified_rule_branch_context")}
    for coder in ("A", "C"):
        packet_rows = {}
        for batch in (1, 2):
            packet_rows.update(unique_rows(read_json(fixture["released"][f"agent-{coder}/材料-{batch:02d}.json"], "synthetic packet")["rows"], "id", "scope packet"))
        for blind_id, original in maps.items():
            if original in scope_by_original:
                require(encoded(packet_rows[blind_id]["contexts"]["verified_object_scope"]) == encoded(scope_by_original[original]),
                        "Scope field/quote/locator/hash changed between corpus and " + coder + " packet")
            if original in branch_by_original:
                require(encoded(packet_rows[blind_id]["contexts"]["verified_rule_branch_context"]) == encoded(branch_by_original[original]),
                        "Renewal supporting branch changed or was lost between corpus and " + coder + " packet")
    require(adapter_digest_json({"z": 1, "中文": [True, None]}) == sha('{"z":1,"中文":[true,null]}'.encode()),
            "Builder canonical JSON serialization changed")
    rejected = {}
    def refresh(bundle):
        freeze = read_json(bundle["freeze"], "synthetic freeze")
        for name, data in bundle["frozen"].items():
            freeze["files"][name]["sha256"] = sha(data)
        bundle["freeze"] = encoded(freeze)
        mapping = read_json(bundle["released"]["抽样清单-研究者.json"], "synthetic mapping")
        mapping["plan"].update(freeze_manifest_sha256=sha(bundle["freeze"]), input_hashes={name: sha(raw) for name, raw in bundle["frozen"].items()})
        bundle["released"]["抽样清单-研究者.json"] = encoded(mapping)
        seal = read_json(bundle["seal"], "synthetic seal")
        seal.update(mapping["plan"])
        seal["output_files"] = {name: sha(raw) for name, raw in bundle["released"].items()}
        bundle["seal"] = encoded(seal)
    def alter(bundle, container, key, transform, reseal=False):
        obj = read_json(bundle[container][key], "synthetic mutation")
        transform(obj)
        bundle[container][key] = encoded(obj)
        if reseal: refresh(bundle)
    def result(bundle, transform):
        alter(bundle, "results", "agent-A/结果-01.json", transform)
    def pred(bundle, transform, tag="candidate"):
        alter(bundle, "frozen", tag + "_predictions", transform, True)
    def mutate_corpus(bundle, transform, rebind=False, remake_packets=False):
        rows = [read_json(line, "synthetic corpus mutation") for line in bundle["frozen"]["corpus"].splitlines()]
        transform(rows)
        bundle["frozen"]["corpus"] = b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in rows) + b"\n"
        if rebind:
            old = read_json(bundle["frozen"]["adapter"], "synthetic adapter")
            cl = read_json(bundle["frozen"]["classification"], "synthetic classification")
            new = synthetic_adapter(rows, bundle["frozen"]["corpus"], cl, bundle["frozen"]["classification"], old["documents"])
            bundle["frozen"]["adapter"] = encoded(new)
            for tag in ("baseline", "candidate"):
                # Rebind the container but deliberately retain the old row fingerprints.
                alter(bundle, "frozen", tag + "_predictions", lambda x: x.update(binding_sha256=new["binding_sha256"]))
            if remake_packets:
                freeze = read_json(bundle["freeze"], "synthetic freeze")
                helpers = source_module(bundle["frozen"]["sample_helpers"], "synthetic_rebind_helpers")
                sampler = source_module(bundle["frozen"]["sampler"], "synthetic_rebind_sampler")
                _, materials = sampler.construct(rows, new, cl, read_json(bundle["frozen"]["exposure"], "synthetic exposure"), freeze["context_fields"], helpers.__dict__)
                for coder in ("A", "C"):
                    for batch in (1, 2):
                        pn, rn = f"agent-{coder}/材料-{batch:02d}.json", f"agent-{coder}/结果-{batch:02d}.json"
                        alter(bundle, "released", pn, lambda x, batch=batch: x.update(rows=materials[(batch - 1) * 25:batch * 25]))
                        alter(bundle, "results", rn, lambda x, pn=pn: x.update(input_packet_sha256=sha(bundle["released"][pn])))
        refresh(bundle)
    def bad(name, mutate, needle=None, run=evaluate):
        changed = copy.deepcopy(fixture)
        mutate(changed)
        try:
            run(changed)
        except (ValueError, KeyError, TypeError, SyntaxError) as exc:
            if needle:
                require(needle in str(exc), "Wrong rejection for " + name + ": " + str(exc))
            rejected[name] = str(exc)
        else:
            raise AssertionError("Invalid synthetic bundle accepted: " + name)
    bad("missing_batch", lambda b: b["results"].pop("agent-C/结果-02.json"), "batch files")
    bad("duplicate_AI_ID", lambda b: result(b, lambda x: x["rows"].append(copy.deepcopy(x["rows"][0]))), "duplicate")
    bad("missing_AI_row", lambda b: result(b, lambda x: x["rows"].pop()), "ID set")
    bad("boolean_AI_label", lambda b: result(b, lambda x: x["rows"][0]["labels"].update(S=True)), "literal")
    bad("null_AI_label", lambda b: result(b, lambda x: x["rows"][0]["labels"].update(S=None)), "literal")
    bad("missing_dimension", lambda b: result(b, lambda x: x["rows"][0]["labels"].pop("E")), "five dimensions")
    bad("empty_reason", lambda b: result(b, lambda x: x["rows"][0]["dimension_reasons"].update(E="")), "nonempty")
    bad("missing_evidence", lambda b: result(b, lambda x: x["rows"][0].update(evidence="")), "nonempty")
    bad("unknown_subtype", lambda b: result(b, lambda x: x["rows"][0].update(innovation_subtypes=["unknown"])), "allowed subtypes")
    bad("positive_F_missing_subtype", lambda b: result(b, lambda x: next(r for r in x["rows"] if r["labels"]["F"] == 1).update(fairness_subtypes=[])), "exactly when F=1")
    bad("quality_basis_conflict", lambda b: result(b, lambda x: next(r for r in x["rows"] if r["labels"]["S"] == 0).update(safety_quality_basis="quality_only")), "inconsistent with S")
    bad("assessment_pending_conflict", lambda b: result(b, lambda x: x["rows"][0]["input_assessment"].update(status="text_problem")), "all five labels pending")
    bad("wrong_protocol_version", lambda b: result(b, lambda x: x.update(protocol_version="other")), "protocol version")
    bad("human_identity_rejected", lambda b: result(b, lambda x: x.update(identity={"kind": "human", "name": "Synthetic Person"})), "kind=AI")
    bad("string_identity_rejected", lambda b: result(b, lambda x: x.update(identity="SYNTHETIC AI STRING")), "kind=AI")
    bad("empty_AI_identity_name", lambda b: result(b, lambda x: x.update(identity={"kind": "AI", "name": ""})), "identity.name")
    bad("blank_AI_identity_name", lambda b: result(b, lambda x: x.update(identity={"kind": "AI", "name": "  "})), "identity.name")
    bad("boolean_batch_header", lambda b: result(b, lambda x: x.update(batch=True)), "literal integers")
    bad("wrong_packet_hash", lambda b: result(b, lambda x: x.update(input_packet_sha256="0" * 64)), "packet hash")
    bad("unacknowledged_protocol", lambda b: result(b, lambda x: x.update(protocol_acknowledged="true")), "acknowledgement")
    bad("frozen_source_changed", lambda b: b["frozen"].update(candidate_predictions=b"changed"), "Frozen file hash")
    bad("release_material_changed", lambda b: b["released"].update({"agent-A/材料-01.json": b"changed"}), "Released file hash")
    bad("freeze_manifest_changed", lambda b: b.update(freeze=b["freeze"] + b" "), "manifest hash")
    bad("duplicate_prediction_ID", lambda b: pred(b, lambda x: x["rows"].append(copy.deepcopy(x["rows"][0]))), "duplicate")
    bad("missing_prediction_ID", lambda b: pred(b, lambda x: x["rows"].pop()), "analysis ID set")
    bad("prediction_text_hash", lambda b: pred(b, lambda x: x["rows"][0].update(unit_text_sha256="0" * 64)), "text hash")
    bad("prediction_version", lambda b: pred(b, lambda x: x["rows"][0].update(version="other")), "row version")
    bad("prediction_coder_hash", lambda b: pred(b, lambda x: x.update(coder_sha256="0" * 64)), "coder hash")
    bad("prediction_protocol_hash", lambda b: pred(b, lambda x: x.update(codebook_sha256="0" * 64)), "protocol hash")
    bad("prediction_binding_hash", lambda b: pred(b, lambda x: x.update(binding_sha256="0" * 64)), "binding hash")
    bad("prediction_record_context_hash", lambda b: pred(b, lambda x: x["rows"][0].update(record_sha256="0" * 64)), "record-context hash")
    bad("adapter_binding_digest_tampered", lambda b: alter(b, "frozen", "adapter", lambda x: x["binding"]["input_paths"].update(corpus="/synthetic-only/different"), True), "canonical binding serialization")
    bad("adapter_classification_bytes_stale", lambda b: alter(b, "frozen", "classification", lambda x: x.update(version="synthetic-classification-v2"), True), "classification input hash")
    bad("adapter_corpus_bytes_stale", lambda b: mutate_corpus(b, lambda rows: rows[10].update(unit_text="CHANGED SYNTHETIC BODY")), "corpus input hash")
    bad("adapter_context_only_bytes_stale", lambda b: mutate_corpus(b, lambda rows: rows[0]["paragraph_context"][0].update(text="CHANGED SYNTHETIC CONTEXT; SAME BODY")), "corpus input hash")
    bad("adapter_scope_only_bytes_stale", lambda b: mutate_corpus(b, lambda rows: rows[0]["verified_object_scope"][0].update(verification="CHANGED SYNTHETIC SCOPE; SAME BODY")), "corpus input hash")
    bad("old_predictions_after_scope_input_rebound", lambda b: mutate_corpus(b, lambda rows: rows[0]["verified_object_scope"][0].update(verification="NEW SYNTHETIC SCOPE VERIFICATION"), True, True), "record-context hash")
    bad("scope_target_hash_stale", lambda b: mutate_corpus(b, lambda rows: rows[0]["verified_object_scope"][0].update(unit_text_sha256="0" * 64), True), "Stale scope target hash")
    bad("scope_normalization_invalid", lambda b: mutate_corpus(b, lambda rows: rows[1]["verified_object_scope"][0].update(normalization="none"), True), "locator/normalization")
    bad("scope_old_eight_key_shape", lambda b: mutate_corpus(b, lambda rows: [rows[0]["verified_object_scope"][0].pop(k) for k in ("source_hash_field", "required_branch_text")], True), "Unexpected object-scope fields")
    bad("scope_extra_key", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(extra="UNREVIEWED SYNTHETIC FIELD"), True), "Unexpected object-scope fields")
    bad("scope_unknown_kind", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(kind="unsupported_synthetic_kind"), True), "Unreviewed object-scope kind")
    for index, kind in enumerate(("drug_clinical_trial", "drug_regulatory_research", "anticancer_drug_development", "anticancer_drug_safety_dossier")):
        bad(kind + "_wrong_component_field", lambda b, i=index: mutate_corpus(b, lambda rows: rows[i]["verified_object_scope"][0].update(source_hash_field="unit_source_sha256"), True), "kind/source_hash_field")
        bad(kind + "_non_null_required_branch", lambda b, i=index: mutate_corpus(b, lambda rows: rows[i]["verified_object_scope"][0].update(required_branch_text="规则二简易续约"), True), "kind/required_branch_text")
    bad("renewal_main_announcement_hash", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(source_sha256=rows[4]["source_sha256"]), True), "component mismatch")
    bad("renewal_wrong_component_hash", lambda b: mutate_corpus(b, lambda rows: rows[4].update(unit_source_sha256="d" * 64), True), "component mismatch")
    bad("renewal_component_hash_missing", lambda b: mutate_corpus(b, lambda rows: rows[4].pop("unit_source_sha256"), True), "component mismatch")
    bad("renewal_wrong_hash_field", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(source_hash_field="source_sha256"), True), "kind/source_hash_field")
    bad("renewal_missing_branch_restriction", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(required_branch_text=None), True), "kind/required_branch_text")
    bad("renewal_wrong_branch_restriction", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(required_branch_text="规则一常规续约"), True), "kind/required_branch_text")
    bad("renewal_wrong_branch", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_rule_branch_context"].update(text="规则一常规续约"), True), "Renewal branch mismatch")
    bad("renewal_branch_extra_text", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_rule_branch_context"].update(text="规则二简易续约和其他分支"), True), "Renewal branch mismatch")
    bad("renewal_branch_missing", lambda b: mutate_corpus(b, lambda rows: rows[4].pop("verified_rule_branch_context"), True), "single object")
    bad("renewal_branch_list", lambda b: mutate_corpus(b, lambda rows: rows[4].update(verified_rule_branch_context=[rows[4]["verified_rule_branch_context"]]), True), "single object")
    bad("renewal_branch_text_not_string", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_rule_branch_context"].update(text=1), True), "single object")
    bad("renewal_quote_hash_changed", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(text="CHANGED SYNTHETIC QUOTE"), True), "Scope quote hash mismatch")
    bad("renewal_target_hash_changed", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(unit_text_sha256="0" * 64), True), "Stale scope target hash")
    bad("renewal_scope_source_hash_malformed", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(source_sha256="not-a-hash"), True), "Valid scope hashes required")
    bad("renewal_locator_extra_key", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0]["locator"].update(extra="UNREVIEWED"), True), "locator/normalization")
    bad("renewal_locator_relative_source", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0]["locator"].update(source="fiction.pdf"), True), "Absolute scope source locator")
    bad("renewal_normalization_invalid", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_object_scope"][0].update(normalization="none"), True), "locator/normalization")
    bad("adapter_branch_only_bytes_stale", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_rule_branch_context"].update(verification="CHANGED SYNTHETIC BRANCH VERIFICATION")), "corpus input hash")
    bad("old_predictions_after_branch_input_rebound", lambda b: mutate_corpus(b, lambda rows: rows[4]["verified_rule_branch_context"].update(verification="NEW SYNTHETIC BRANCH VERIFICATION"), True, True), "record-context hash")
    bad("boolean_machine_label", lambda b: pred(b, lambda x: x["rows"][0]["labels"].update(S=True)), "literal integer")
    bad("partial_null_machine", lambda b: pred(b, lambda x: x["rows"][0]["labels"].update(S=None)), "partial null")
    bad("null_machine_wrong_status", lambda b: pred(b, lambda x: next(r for r in x["rows"] if r["labels"]["S"] is None).update(judgement_status="rule_prediction")), "authorized pending")
    bad("binary_machine_insufficient", lambda b: pred(b, lambda x: x["rows"][0].update(input_assessment_status="text_problem")), "contradict insufficient")
    def bad_dictionary(b):
        b["frozen"]["candidate_dictionary"] = b"VERSION = 'wrong-literal-version'\n"
        refresh(b)
    bad("dictionary_source_version", bad_dictionary, "VERSION")
    def both_materials(b):
        for coder in ("A", "C"):
            alter(b, "released", f"agent-{coder}/材料-01.json", lambda x: x["rows"][0]["contexts"].update(invented="NOT SOURCE"))
        refresh(b)
    bad("both_resealed_materials_modified", both_materials, "frozen source/context")
    def changed_shared_clarification(b):
        for coder in ("A", "C"):
            b["released"][f"agent-{coder}/共同执行澄清.md"] += b"\nCHANGED SYNTHETIC INSTRUCTION"
        refresh(b)
    bad("both_resealed_clarifications_modified", changed_shared_clarification, "shared document differs")
    def missing_shared_instructions(b):
        b["released"].pop("agent-C/评审任务说明.md")
        refresh(b)
    bad("missing_shared_task_instructions", missing_shared_instructions, "released file set")
    def both_packets_drop_scope(b):
        for coder in ("A", "C"):
            for batch in (1, 2):
                alter(b, "released", f"agent-{coder}/材料-{batch:02d}.json", lambda x: [r["contexts"].pop("verified_object_scope", None) for r in x["rows"]])
        refresh(b)
    bad("scope_lost_from_both_resealed_packets", both_packets_drop_scope, "frozen source/context")
    def both_packets_drop_branch(b):
        for coder in ("A", "C"):
            for batch in (1, 2):
                alter(b, "released", f"agent-{coder}/材料-{batch:02d}.json", lambda x: [r["contexts"].pop("verified_rule_branch_context", None) for r in x["rows"]])
        refresh(b)
    bad("renewal_branch_lost_with_scope_retained_in_both_resealed_packets", both_packets_drop_branch, "frozen source/context")
    def omit_scope_field(b):
        freeze = read_json(b["freeze"], "synthetic freeze")
        freeze["context_fields"].remove("verified_object_scope")
        b["freeze"] = encoded(freeze); refresh(b)
    bad("scope_omitted_from_frozen_fields", omit_scope_field, "omitted from released fields")
    def omit_branch_field(b):
        freeze = read_json(b["freeze"], "synthetic freeze")
        freeze["context_fields"].remove("verified_rule_branch_context")
        b["freeze"] = encoded(freeze); refresh(b)
    bad("renewal_supporting_branch_omitted_from_frozen_fields", omit_branch_field, "supporting branch omitted from released fields")
    bad("mapping_metadata", lambda b: alter(b, "released", "抽样清单-研究者.json", lambda x: x["rows"][0].update(group="GOV"), True), "metadata mismatch")
    bad("mapping_weight", lambda b: alter(b, "released", "抽样清单-研究者.json", lambda x: x["rows"][0].update(weight=2), True), "numeric mismatch")
    bad("duplicate_review_ID", lambda b: alter(b, "released", "抽样清单-研究者.json", lambda x: x["rows"][1].update(review_id=x["rows"][0]["review_id"]), True), "duplicate review_id")
    bad("unselected_partition", lambda b: alter(b, "released", "抽样清单-研究者.json", lambda x: x.update(not_selected_ids=["fiction-0013"]), True), "partition")
    bad("exposure_overlap", lambda b: alter(b, "frozen", "exposure", lambda x: x["exclusions"].append(x["provisional_eligible_ids"][0]), True), "partition")
    def wrong_seed(b):
        obj = read_json(b["freeze"], "freeze"); obj["sampling_seed"] += 1; b["freeze"] = encoded(obj); refresh(b)
    bad("wrong_frozen_seed", wrong_seed, "sampling_seed")
    def import_leak(b):
        b["frozen"]["paired_version_metrics"] += b"\nimport unfrozen_local_study_module\n"
        refresh(b)
    bad("unfrozen_local_import", import_leak, "Unfrozen/unsupported runtime import")
    # Preserve a single-dimension concept-boundary pending value with sufficient materials.
    accepted = copy.deepcopy(fixture)
    def boundary_pending(doc):
        row = next(r for r in doc["rows"] if r["labels"]["I"] == 1)
        row["labels"]["I"] = PENDING; row["innovation_subtypes"] = []
        row["dimension_reasons"]["I"] = "Synthetic concept-boundary uncertainty"
    result(accepted, boundary_pending)
    accepted_payload, accepted_archive = assemble(accepted)
    require(any(r["A"]["I"] == PENDING for r in accepted_payload["rows"]), "Concept pending overwritten")
    require(accepted_archive["raw_coder_submissions"] != archive["raw_coder_submissions"], "Original changed submission was not preserved")
    for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'):
        try: read_json(raw, "synthetic invalid JSON")
        except ValueError: pass
        else: raise AssertionError("Invalid/duplicate/nonfinite JSON accepted")
    # Deliberately poison the ordinary module cache: evaluate must use its frozen dependency.
    from unittest.mock import patch
    poison = types.ModuleType("survey_metrics")
    poison.DIMS = ("WRONG",)
    with patch.dict(sys.modules, {"survey_metrics": poison}):
        actual = evaluate(fixture)
    require(actual["archive"]["raw_coder_submissions"] == archive["raw_coder_submissions"], "Original submissions changed")
    require(actual["archive"]["selected_machine_records_by_version_and_blind_id"] == archive["selected_machine_records_by_version_and_blind_id"], "Original machine records changed")
    require(actual["paired_statistics"]["sample_n"] == 26, "Statistics wrong synthetic n")
    # Mock snapshot reads/inventories and publication, creating no QA temp/sample files.
    fake_root, fake_freeze = Path("/synthetic-only/V600"), Path("/synthetic-only/freeze.json")
    fs = {str(fake_freeze): fixture["freeze"], str(fake_root / "封存信息.json"): fixture["seal"], str(here): sources["results_bridge"]}
    for name, raw in fixture["frozen"].items(): fs["/synthetic-only/" + name] = raw
    for container in ("released", "results"):
        for name, raw in fixture[container].items(): fs[str(fake_root / name)] = raw
    def fake_glob(path, pattern):
        container = fixture["results"] if "结果" in pattern else fixture["released"]
        marker = "结果" if "结果" in pattern else "材料"
        return [path / name for name in container if marker in name]
    with patch.object(Path, "read_bytes", lambda p: fs[str(p)]), patch.object(Path, "glob", fake_glob):
        snap, tracked, inventory = load_snapshot(fake_freeze, fake_root)
        require(snap == fixture, "Snapshot bytes/inventory mismatch")
        check_unchanged(tracked, {path: sha(fs[path]) for path in tracked})
        check_unchanged(inventory, inventories(fake_root))
    try: check_unchanged({"fiction": "before"}, {"fiction": "after"})
    except ValueError: pass
    else: raise AssertionError("Changed input accepted")
    from io import BytesIO
    class MemoryStream(BytesIO):
        def fileno(self): return 12345
        def close(self): pass
    with patch("os.path.lexists", return_value=True):
        try: publish_json(Path("/synthetic-only/existing.json"), {})
        except ValueError: pass
        else: raise AssertionError("Overwrite allowed")
    memory = MemoryStream()
    with patch("os.path.lexists", return_value=False), patch.object(Path, "open", return_value=memory) as opened, patch("os.fsync"), patch("os.link") as linked, patch.object(Path, "unlink") as unlinked:
        publish_json(Path("/synthetic-only/new.json"), {"synthetic": True})
        require(opened.call_args.args == ("xb",) and linked.call_count == unlinked.call_count == 1, "Exclusive atomic publication protocol failed")
    # Dependency files are code-only inputs; refuse to certify a racing code edit.
    require(sources == {name: path.read_bytes() for name, path in code_paths.items()}, "QA code dependency changed during checks")
    return {"status": "passed_synthetic_QA_only", "real_policy_text_read": False, "real_labels_read": False,
            "real_sample_drawn": False, "real_statistics_generated": False, "synthetic_analysis_units": 28,
            "synthetic_sample_n": 26, "batches_per_coder": 2, "code_sha256": {name: sha(raw) for name, raw in sources.items()},
            "checks": {"two_version_review_ID_join_with_reversed_orders": True, "original_submissions_and_machine_records_preserved": True,
                       "AI_identity_object_kind_and_nonempty_name_required": True,
                       "adapter_binding_canonical_digest_and_exact_input_bytes_verified": True,
                       "full_record_context_fingerprints_match_adapter_and_both_predictions": True,
                       "five_ten_field_scope_kinds_and_both_normalizations_preserved_end_to_end": True,
                       "renewal_component_hash_and_single_exact_normalized_branch_required": True,
                       "renewal_scope_and_supporting_branch_preserved_in_both_coder_packets": True,
                       "scope_free_legacy_material_shape_still_accepted": True,
                       "AI_and_machine_pending_preserved_without_consensus": True, "sufficient_material_single_dimension_pending_retained": True,
                       "frozen_survey_import_overrides_poisoned_module_cache": True, "mock_snapshot_and_recheck": True,
                       "mock_exclusive_nooverwrite_publication": True, "duplicate_nonfinite_JSON_rejected": True,
                       "rejected_case_count": len(rejected), "rejected_cases": rejected},
            "limits": ["Only synthetic text and labels were used; code checks do not validate real semantic judgments or blinding.",
                       "Filesystem snapshot/publication operations were mocked; no real sample/output inventory was read.",
                       "Scope quotes, source locators and hashes are invented. Physical source authenticity is not established by this QA.",
                       "Corpus/classification hashes and full record fingerprints are verified; external metadata/source files absent from freeze.files are not reopened."]}


if __name__ == "__main__":
    main()
