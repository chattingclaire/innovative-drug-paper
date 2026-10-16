#!/usr/bin/env python3
"""Mechanical source preparation only; never dispatches or performs coding."""
import argparse
import copy
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import jsonschema


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def strict(data):
    return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def binding(path, data=None):
    path = Path(path).resolve()
    data = path.read_bytes() if data is None else data
    return {"path": str(path), "bytes": len(data), "sha256": sha(data)}


def put(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(obj) + b"\n"
    with path.open("xb") as f:
        f.write(data)
    return binding(path, data)


def expect(condition, message):
    if not condition:
        raise ValueError(message)


def type_name(value):
    if value is None:
        return "null"
    return {str: "string", bool: "boolean", int: "integer", float: "number", list: "array", dict: "object"}[type(value)]


def walk(value, pointer=""):
    yield pointer, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, pointer + "/" + key.replace("~", "~0").replace("/", "~1"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, pointer + "/" + str(index))


def resource_references(bundle, source_id):
    """Only declared paths and declared identities; no filename search or inference."""
    bases = bundle.get("source_locator_bases", {})
    root_base = bases.get("canonical_row_attachment_relative_path_base")
    path_keys = {"path", "absolute_path", "snapshot", "source_snapshot", "asset_path", "page_asset", "relative_path", "snapshot_relative_to_projection"}
    for pointer, node in walk(bundle):
        if not isinstance(node, dict):
            continue
        for key in path_keys & node.keys():
            locator = node[key]
            if not isinstance(locator, str) or not locator:
                continue
            declared_sha = node.get("sha256")
            declared_bytes = node.get("bytes")
            if key in {"snapshot", "source_snapshot", "snapshot_relative_to_projection"}:
                declared_sha = node.get("source_sha256", declared_sha)
                declared_bytes = node.get("source_bytes", declared_bytes)
            if key == "page_asset":
                declared_sha = node.get("image_sha256", node.get("asset_sha256", node.get("sha256")))
                declared_bytes = node.get("image_bytes", node.get("asset_bytes", node.get("bytes")))
            base = node.get("relative_path_base")
            base_basis = "node.relative_path_base" if isinstance(base, str) else None
            # Existing canonical attachments explicitly retain this base. Full source
            # resource relative_path uses the same frozen source locator base.
            if not Path(locator).is_absolute() and base is None and key in {"relative_path", "snapshot_relative_to_projection", "page_asset"}:
                base = root_base
                base_basis = "source_locator_bases.canonical_row_attachment_relative_path_base"
            actual_path = None
            if Path(locator).is_absolute():
                actual_path = str(Path(locator).resolve())
            elif isinstance(base, str) and Path(base).is_absolute():
                actual_path = str((Path(base) / locator).resolve())
            yield {"source_id": source_id, "pointer": pointer + "/" + key,
                   "declared_locator": locator, "declared_sha256": declared_sha,
                   "declared_bytes": declared_bytes, "resolved_path": actual_path,
                   "explicit_relative_base": base, "relative_base_basis": base_basis,
                   "identity_is_declared": isinstance(declared_sha, str) and len(declared_sha) == 64,
                   "semantic_applicability_inferred": False, "consumer_read_status": "not_recorded"}


def prepare(args):
    out = Path(args.output).resolve()
    source = Path(args.source_dir).resolve()
    expect(not (out / "preflight.json").exists(), "Existing preflight: do not reread or overwrite")
    source_file = source / "common-frame-bundles-v15.jsonl"
    frame_file = source / "frame-bundle-bindings-v15.jsonl"
    chosen = {"source_jsonl": source_file, "frame_bindings": frame_file,
              "extension_manifest": source / "source-extension-manifest-v15.json",
              "common_material_bindings": source / "common-material-bindings-v15.json",
              "source_seal": source / "seal.json", "packet_schema": Path(args.packet_schema),
              "reused_output_schema": Path(args.output_schema),
              "reused_validator": Path(args.validator), "native_run_manifest": Path(args.native_manifest)}
    # Each full-source file is read once, below. Small contracts are read here.
    small_data = {key: path.read_bytes() for key, path in chosen.items() if key not in {"source_jsonl", "frame_bindings"}}
    objects = {key: strict(data) for key, data in small_data.items() if key != "reused_validator"}
    seal = objects["source_seal"]
    seal_members = {v["path"]: v for v in seal["members"]}
    for key in ("extension_manifest", "common_material_bindings", "packet_schema"):
        actual = binding(chosen[key], small_data[key])
        frozen = seal_members.get(actual["path"])
        expect(frozen and all(actual[k] == frozen[k] for k in ("bytes", "sha256")), f"Source seal mismatch: {key}")
    native = objects["native_run_manifest"]
    budget_path = Path(native["byte_budget"]["path"])
    budget_data = budget_path.read_bytes()
    budget_binding = binding(budget_path, budget_data)
    expect(all(budget_binding[k] == native["byte_budget"][k] for k in ("path", "bytes", "sha256")), "Frozen budget binding mismatch")
    budget = strict(budget_data)
    expect("260000" in budget["budget_basis"], "Native packet-byte heuristic absent")
    expect(args.packet_byte_limit == 260000 and args.max_records == 12, "Frozen budget must stay 260000 packet bytes / at most 12 records")
    packet_validator = jsonschema.Draft202012Validator(objects["packet_schema"])
    frame_raw = frame_file.read_bytes()
    frame_binding = binding(frame_file, frame_raw)
    expect(all(frame_binding[k] == seal_members[str(frame_file)][k] for k in ("bytes", "sha256")), "Frame binding file identity mismatch")
    frame_rows = [strict(line) for line in frame_raw.splitlines()]
    expect(len(frame_rows) == args.expected_n, "Frame binding N mismatch")
    expect([x["frame_ordinal_1based"] for x in frame_rows] == list(range(1, args.expected_n + 1)), "Frozen frame ordinal mismatch")
    order = [x["id"] for x in frame_rows]
    expect(len(set(order)) == args.expected_n, "Nonunique source_id")
    source_hasher = hashlib.sha256()
    source_bytes = 0
    source_profile = defaultdict(Counter)
    records = []
    references = []
    unique = {}
    unresolved = []
    asset_files = {}
    packets_dir = out / "packets"
    packets_dir.mkdir(parents=True, exist_ok=True)
    # This is the only full source-field pass. Source body/array order is never edited.
    with source_file.open("rb") as f:
        for ordinal, (line, row_binding) in enumerate(zip(f, frame_rows, strict=True), 1):
            source_hasher.update(line)
            source_bytes += len(line)
            bundle = strict(line)
            source_id = bundle["source_record"]["id"]
            expect(source_id == row_binding["id"], f"Source order mismatch at {ordinal}")
            body = canonical(bundle)
            expect(sha(body) == row_binding["new_v15_bundle_sha256"] and len(body) == row_binding["new_v15_bundle_utf8_bytes"], f"Bundle identity mismatch: {source_id}")
            expect(sha(canonical(bundle["source_record"])) == row_binding["source_record_object_sha256"], f"Source record identity mismatch: {source_id}")
            expect(bundle["source_record"]["source_ref"]["sha256"] == row_binding["primary_source_sha256"], f"Primary source identity mismatch: {source_id}")
            for pointer, value in walk(bundle):
                normalized = "/".join("*" if part.isdigit() else part for part in pointer.split("/"))
                source_profile[normalized][type_name(value)] += 1
            packet = {"packet_version": "native-full-source-3", "source_id": source_id,
                      "output_id": f"B-{ordinal:05d}", "source_bundle_sha256": sha(body),
                      "source_bundle": bundle, "verified_asset_files": []}
            packet_validator.validate(packet)
            packet_binding = put(packets_dir / f"{source_id}.json", packet)
            packet_binding.update(source_id=source_id, output_id=packet["output_id"], frame_ordinal_1based=ordinal,
                                  source_bundle_sha256=sha(body), source_bundle_utf8_bytes=len(body))
            records.append(packet_binding)
            for ref in resource_references(bundle, source_id):
                path = ref["resolved_path"]
                if path is None:
                    ref["status"] = "unresolved_explicit_locator"
                    unresolved.append(ref)
                elif not Path(path).is_file():
                    ref["status"] = "missing_declared_locator"
                    unresolved.append(ref)
                else:
                    if path not in asset_files:
                        asset_files[path] = binding(path)
                    actual = asset_files[path]
                    ref["actual_file_binding"] = actual
                    mismatches = []
                    if ref["identity_is_declared"] and actual["sha256"] != ref["declared_sha256"]:
                        mismatches.append("sha256")
                    if type(ref["declared_bytes"]) is int and actual["bytes"] != ref["declared_bytes"]:
                        mismatches.append("bytes")
                    ref["status"] = "declared_identity_mismatch" if mismatches else ("verified_declared_identity" if ref["identity_is_declared"] else "available_locator_without_declared_file_sha")
                    ref["identity_mismatches"] = mismatches
                    if mismatches:
                        unresolved.append(ref)
                    entry = unique.setdefault(path, {**actual, "source_ids": [], "source_pointers": [], "consumer_read_status": "not_recorded", "consumer_use_status": "not_recorded"})
                    if source_id not in entry["source_ids"]:
                        entry["source_ids"].append(source_id)
                    entry["source_pointers"].append({"source_id": source_id, "pointer": ref["pointer"], "status": ref["status"]})
                references.append(ref)
    source_binding = {"path": str(source_file), "bytes": source_bytes, "sha256": source_hasher.hexdigest()}
    expect(all(source_binding[k] == seal_members[str(source_file)][k] for k in ("bytes", "sha256")), "Common source JSONL identity mismatch")
    core_candidates = {}
    for key, path in (("manual_candidate", args.manual_candidate), ("execution_prompt_candidate", args.prompt_candidate), ("actor_instruction_interface_candidate", args.actor_instructions)):
        if path:
            core_candidates[key] = binding(path)
    batches = []
    current = []
    total = 0
    for record in records:
        if current and (len(current) == args.max_records or total + record["bytes"] > args.packet_byte_limit):
            batches.append(current)
            current, total = [], 0
        current.append(record)
        total += record["bytes"]
    if current:
        batches.append(current)
    plan = []
    for index, items in enumerate(batches, 1):
        ids = [x["source_id"] for x in items]
        byte_n = sum(x["bytes"] for x in items)
        paths = {ref["resolved_path"] for ref in references if ref["source_id"] in ids and ref.get("actual_file_binding")}
        plan.append({"batch_id": f"batch-{index:04d}", "expected_N": len(items), "source_ids": ids,
                     "frame_ordinals_1based": [x["frame_ordinal_1based"] for x in items],
                     "packets": items, "packet_bytes": byte_n, "input_bytes": byte_n,
                     "input_bytes_meaning": "sum assigned packet file bytes only",
                     "candidate_core_text_input_bytes": byte_n + sum(x["bytes"] for x in core_candidates.values()),
                     "available_source_resource_unique_bytes": sum(asset_files[p]["bytes"] for p in paths),
                     "source_asset_bindings": [{k: v for k, v in unique[p].items() if k != "source_pointers"} for p in sorted(paths)],
                     "oversize_single_packet": len(items) == 1 and byte_n > args.packet_byte_limit,
                     "state": "prepared_not_dispatched"})
    flattened = [source_id for batch in plan for source_id in batch["source_ids"]]
    expect(flattened == order, "Batch plan changed frozen order")
    input_bindings = {key: binding(path, small_data[key]) for key, path in chosen.items() if key in small_data}
    input_bindings.update(source_jsonl=source_binding, frame_bindings=frame_binding, frozen_native_byte_budget=budget_binding)
    put(out / "input-bindings.json", input_bindings)
    put(out / "candidate-core-bindings.json", {"state": "candidate_only_not_final_release", "bindings": core_candidates})
    put(out / "frame-order.json", {"source_ids": order, "UTF8_LF_sha256": sha(("\n".join(order) + "\n").encode()), "canonical_json_sha256": sha(canonical(order))})
    put(out / "packet-bindings.json", records)
    put(out / "source-field-type-profile.json", {key: dict(value) for key, value in sorted(source_profile.items())})
    with (out / "resource-references.jsonl").open("xb") as f:
        for ref in references:
            f.write(canonical(ref) + b"\n")
    put(out / "source-resource-bindings.json", list(unique.values()))
    put(out / "resource-locator-findings.json", {"mechanical_only": True, "semantic_necessity_assessed": False, "findings": unresolved})
    put(out / "batch-plan.json", {"state": "prepared_waiting_final_release_and_ROOT_GO", "context_unit": "batch", "record_N": len(records), "batch_N": len(plan), "max_records": args.max_records, "packet_byte_limit": args.packet_byte_limit, "batching": "greedy contiguous frozen FRAME4481 order; count and actual serialized packet bytes only", "batches": plan})
    packet_sizes = [r["bytes"] for r in records]
    batch_sizes = [x["packet_bytes"] for x in plan]
    report = {"state": "prepared_waiting_final_release_and_ROOT_GO", "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "record_N": len(records), "unique_source_id_N": len(set(order)), "batch_N": len(plan),
              "actual_inference_N": 0, "coding_actors_dispatched_N": 0, "coding_judgments_created_N": 0,
              "actual_consumer_read_or_use_receipt_N": 0, "source_body_semantic_rewrite_N": 0,
              "source_field_full_pass_N": 1, "original_array_and_frame_order_preserved": True,
              "packet_schema_valid_N": len(records), "five_dimensions": ["S", "E", "Ec", "I", "F"],
              "five_dimension_values": [0, 1, None], "input_bindings": input_bindings,
              "frame_order_UTF8_LF_sha256": sha(("\n".join(order) + "\n").encode()),
              "frame_order_canonical_json_sha256": sha(canonical(order)),
              "packet_bytes_distribution": {"min": min(packet_sizes), "max": max(packet_sizes), "sum": sum(packet_sizes)},
              "batch_packet_bytes_distribution": {"min": min(batch_sizes), "max": max(batch_sizes), "sum": sum(batch_sizes)},
              "batch_record_N_distribution": dict(Counter(str(len(x)) for x in batches)),
              "oversize_single_packet_source_ids": [x["source_ids"][0] for x in plan if x["oversize_single_packet"]],
              "resource_unique_file_N": len(asset_files), "resource_unique_available_bytes": sum(x["bytes"] for x in asset_files.values()),
              "resource_reference_status_N": dict(Counter(x["status"] for x in references)),
              "resource_locator_finding_N": len(unresolved),
              "actual_source_resource_hashing_is_not_consumer_reading": True,
              "subset77_800_material_body_comparison_performed": False,
              "subset77_800_common_identity_basis": "same exact sealed full v15 source accessor; no additional material injected; subset bodies were not read",
              "required_before_dispatch": ["ROOT final manual/prompt/procedural release bindings", "per-batch output schema instantiation", "ROOT decision on reported material locator findings", "ROOT GO"],
              "new_scientific_threshold_added": False, "semantic_or_correctness_validation_performed": False,
              "candidate_core_bytes_are_provisional": True,
              "byte_budget_caveat": "260000 is the inherited packet-file-byte heuristic; available file bytes do not certify provider token/context capacity or actual reads",
              "max_total_technical_attempts": native["max_total_technical_attempts"], "max_technical_retries": native["max_technical_retries"],
              "canonical_first_authority": "ROOT; earliest technically valid complete original batch bytes; legal null does not trigger retries"}
    put(out / "preflight.json", report)
    print(json.dumps({k: report[k] for k in ("state", "record_N", "batch_N", "actual_inference_N", "packet_bytes_distribution", "batch_packet_bytes_distribution", "batch_record_N_distribution", "resource_unique_file_N", "resource_reference_status_N", "resource_locator_finding_N", "oversize_single_packet_source_ids")}, ensure_ascii=False, indent=2))


def instantiate(args):
    """Parameterize schema after ROOT freezes the release; no source-field reread."""
    out = Path(args.output).resolve()
    plan = strict((out / "batch-plan.json").read_bytes())
    release = strict(Path(args.release_bindings).read_bytes())
    # Full official path/byte/SHA triplets are required; no candidate default.
    for key in ("manual", "execution_prompt", "actor_instructions", "output_validation_contract", "read_manifest_template", "response_retention_policy", "output_seal_template", "technical_failure_template", "run_scope_binding", "strict_technical_validator"):
        expect(key in release, f"Missing official procedural binding: {key}")
        actual = binding(release[key]["path"])
        expect(actual == release[key], f"Official release identity mismatch: {key}")
    schema = strict(Path(args.output_schema).read_bytes())
    expect(release["context_unit"] == "batch", "Context unit must remain batch")
    schemas = []
    for batch in plan["batches"]:
        current = copy.deepcopy(schema)
        current["title"] = "Native whole-batch original structured submission"
        for key in ("run_id", "requested_model", "requested_reasoning_effort", "context_unit", "scope"):
            current["properties"][key] = {"const": release[key]}
        current["properties"]["batch_id"] = {"const": batch["batch_id"]}
        current["properties"]["manual_binding"] = {"const": release["manual"]}
        current["properties"]["execution_prompt_binding"] = {"const": release["execution_prompt"]}
        item = current["properties"]["records"]["items"]
        prefix = []
        for packet in batch["packets"]:
            own = copy.deepcopy(item)
            for key, value in (("source_id", packet["source_id"]), ("output_id", packet["output_id"]), ("packet_sha256", packet["sha256"])):
                own["properties"][key] = {"const": value}
            prefix.append(own)
        current["properties"]["records"] = {"type": "array", "minItems": batch["expected_N"], "maxItems": batch["expected_N"], "prefixItems": prefix, "items": False}
        jsonschema.Draft202012Validator.check_schema(current)
        schema_binding = put(out / "formal-schemas" / batch["batch_id"] / "output.schema.json", current)
        schemas.append({"batch_id": batch["batch_id"], "source_ids": batch["source_ids"], "output_schema": schema_binding, "state": "prepared_not_dispatched"})
    put(out / "formal-schema-bindings.json", {"state": "formal_bindings_instantiated_waiting_ROOT_GO", "release_bindings": binding(args.release_bindings), "batch_N": len(schemas), "batches": schemas, "actual_inference_N": 0})
    print(json.dumps({"state": "formal_bindings_instantiated_waiting_ROOT_GO", "batch_N": len(schemas), "actual_inference_N": 0}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "instantiate"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-dir")
    parser.add_argument("--packet-schema")
    parser.add_argument("--output-schema", required=True)
    parser.add_argument("--validator")
    parser.add_argument("--native-manifest")
    parser.add_argument("--manual-candidate")
    parser.add_argument("--prompt-candidate")
    parser.add_argument("--actor-instructions")
    parser.add_argument("--expected-n", type=int, default=4481)
    parser.add_argument("--max-records", type=int, default=12)
    parser.add_argument("--packet-byte-limit", type=int, default=260000)
    parser.add_argument("--release-bindings")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args)
    else:
        instantiate(args)


if __name__ == "__main__":
    main()
