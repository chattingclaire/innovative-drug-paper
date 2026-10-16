"""Administrative V600 reception; never opens prediction files or computes metrics.

Use explicit absolute --freeze, --holdout and --receipts paths. The final freeze
must contain admin_receiver (this file), results_bridge, legacy_results_helpers,
and all three shared documents. Only these frozen inputs and sealed release files
are opened. Source modules are hash-checked before execution; the frozen bridge's
source_module loads the legacy validate_result implementation.

Every first-seen result-JSON byte stream is saved with exclusive creation BEFORE
JSON/schema checks. Raw copies, receipt records, and append-only validation reports
are separate. Invalid submissions are still immutable receipts, not repair slots.
Subsequent source changes/disappearance or archive changes fail closed. Run one
receiver at a time; concurrent exclusive-create conflicts are errors. This is an
administrative check, not an assessment of evidence, independence, or performance.

--synthetic-qa --output NEW_PATH uses bridge.synthetic_bundle and temporary files;
it accepts no study paths, runs no metric function, and creates no actual holdout.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import types
import uuid

PHASE = "V600"
STATIC_DOCS = {"protocol": "五维共用编码协议.md", "reviewer_instructions": "评审任务说明.md",
               "protocol_clarifications": "共同执行澄清.md"}
ADMIN_INPUTS = {"admin_receiver", "results_bridge", "legacy_results_helpers"} | set(STATIC_DOCS)
RESULT_PATTERN = re.compile(r"结果-(\d{2})\.json\Z")


class AdminError(ValueError):
    def __init__(self, code, field, file=None):
        self.issue = {"code": code, "field": field}
        if file is not None:
            self.issue["file"] = file
        super().__init__(code)


def require(condition, code, field, file=None):
    if not condition:
        raise AdminError(code, field, file)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def read_json(raw, field, file=None):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, "duplicate_json_key", field, file)
            out[key] = value
        return out
    def bad(_):
        raise AdminError("nonfinite_json", field, file)
    try:
        obj = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
        require(isinstance(obj, dict), "json_object_required", field, file)
        def finite(value):
            if isinstance(value, dict):
                for v in value.values(): finite(v)
            elif isinstance(value, list):
                for v in value: finite(v)
            elif isinstance(value, float):
                require(math.isfinite(value), "nonfinite_json", field, file)
        finite(obj)
        return obj
    except AdminError:
        raise
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise AdminError("invalid_json", field, file) from None


def raw_file(path, field, file=None):
    require(path.is_file() and not path.is_symlink(), "regular_file_required", field, file)
    try:
        return path.read_bytes()
    except OSError:
        raise AdminError("file_read_failed", field, file) from None


def exclusive_bytes(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError:
        raise AdminError("exclusive_write_failed", "receipt_storage", path.name) from None


def result_inventory(root):
    result = {}
    for coder in ("A", "C"):
        directory = root / ("agent-" + coder)
        require(not directory.is_symlink(), "symlink_directory_forbidden", "result_directory", "agent-" + coder)
        if directory.exists():
            require(directory.is_dir(), "directory_required", "result_directory", "agent-" + coder)
            for path in sorted(directory.glob("结果-*.json")):
                result[str(path.relative_to(root))] = path
    return result


def prepare(freeze_path, holdout):
    """Validate administrative inputs only; no corpus/prediction/statistic reads."""
    tracked = {}
    def snapshot(path, field, name):
        raw = raw_file(path, field, name)
        tracked[str(path)] = sha(raw)
        return raw
    freeze_raw = snapshot(freeze_path, "freeze", "freeze")
    freeze = read_json(freeze_raw, "freeze")
    require(freeze.get("status") == "frozen_for_paired_reference_label_holdout"
            and freeze.get("phase") == PHASE, "paired_final_freeze_required", "freeze.status")
    for key, value in (("sampling_seed", 2026092605), ("bootstrap_seed", 2026092606), ("sample_budget", 600)):
        require(type(freeze.get(key)) is int and freeze[key] == value, "frozen_design_mismatch", "freeze." + key)
    version = freeze.get("protocol_version")
    require(isinstance(version, str) and bool(version.strip()), "protocol_version_required", "freeze.protocol_version")
    files = freeze.get("files")
    require(isinstance(files, dict) and ADMIN_INPUTS <= set(files), "missing_admin_freeze_entry", "freeze.files")
    require(all(isinstance(entry, dict) and isinstance(entry.get("sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) for entry in files.values()),
            "invalid_frozen_entry_metadata", "freeze.files")
    sources = {}
    for name in sorted(ADMIN_INPUTS):
        entry = files[name]
        require(isinstance(entry, dict) and isinstance(entry.get("path"), str)
                and Path(entry["path"]).is_absolute(), "absolute_frozen_path_required", "freeze.files." + name)
        raw = snapshot(Path(entry["path"]), "frozen_input", name)
        require(sha(raw) == entry.get("sha256"), "frozen_input_hash_mismatch", "freeze.files." + name)
        sources[name] = raw
    current = snapshot(Path(__file__).resolve(), "receiver_code", "admin_receiver")
    require(sha(current) == files["admin_receiver"]["sha256"], "running_receiver_not_frozen", "admin_receiver")
    bridge = types.ModuleType("_verified_administrative_bridge")
    bridge.__file__ = "<verified paired_holdout_results.py>"
    try:
        exec(compile(sources["results_bridge"], bridge.__file__, "exec"), bridge.__dict__)
        legacy = bridge.source_module(sources["legacy_results_helpers"], "legacy_results_helpers")
    except Exception:
        raise AdminError("verified_helper_load_failed", "frozen_helpers") from None
    require(bridge.PHASE == PHASE and bridge.STATIC_DOCS == STATIC_DOCS
            and tuple(legacy.DIMS) == tuple(bridge.DIMS), "helper_contract_mismatch", "frozen_helpers")
    seal_raw = snapshot(holdout / "封存信息.json", "seal", "封存信息.json")
    seal = read_json(seal_raw, "seal")
    require(seal.get("status") == "drawn" and seal.get("release_status") == "ready_for_blind_review"
            and seal.get("phase") == PHASE, "released_paired_holdout_required", "seal.status")
    require(seal.get("freeze_manifest_sha256") == sha(freeze_raw), "seal_freeze_hash_mismatch", "seal.freeze_manifest_sha256")
    require(seal.get("input_hashes") == {k: v.get("sha256") for k, v in files.items()},
            "seal_input_inventory_mismatch", "seal.input_hashes")
    n = seal.get("n")
    require(type(n) is int and 0 < n <= 600, "invalid_sample_count", "seal.n")
    require(type(seal.get("N_star")) is int and n == min(600, seal["N_star"]), "invalid_frame_sample_count", "seal.N_star")
    batches = math.ceil(n / 25)
    packets = {f"agent-{c}/材料-{b:02d}.json" for c in ("A", "C") for b in range(1, batches + 1)}
    manuals = {f"agent-{c}/{name}" for c in ("A", "C") for name in STATIC_DOCS.values()}
    outputs = seal.get("output_files")
    require(isinstance(outputs, dict) and set(outputs) == packets | manuals | {"抽样清单-研究者.json"},
            "sealed_release_inventory_mismatch", "seal.output_files")
    actual_packets = {str(p.relative_to(holdout)) for c in ("A", "C")
                      for p in (holdout / ("agent-" + c)).glob("材料-*.json")}
    require(actual_packets == packets, "packet_file_inventory_mismatch", "released.materials")
    released = {}
    for name, digest in sorted(outputs.items()):
        raw = snapshot(holdout / name, "sealed_release", name)
        require(sha(raw) == digest, "sealed_release_hash_mismatch", "sealed_release", name)
        released[name] = raw
    parsed_packets = {}
    for coder in ("A", "C"):
        for key, name in STATIC_DOCS.items():
            require(released[f"agent-{coder}/{name}"] == sources[key], "shared_document_differs_from_freeze", key, name)
        for batch in range(1, batches + 1):
            name = f"agent-{coder}/材料-{batch:02d}.json"
            raw = released[name]
            require(raw == released[f"agent-A/材料-{batch:02d}.json"], "coder_packet_bytes_differ", "released.materials", name)
            packet = read_json(raw, "packet", name)
            require(packet.get("protocol_version") == version and packet.get("purpose") == "reference_label_holdout_AI_independent",
                    "packet_protocol_mismatch", "packet.protocol_version", name)
            require(type(packet.get("batch")) is int and packet["batch"] == batch
                    and type(packet.get("total_batches")) is int and packet["total_batches"] == batches,
                    "packet_batch_mismatch", "packet.batch", name)
            rows = packet.get("rows")
            require(isinstance(rows, list) and all(isinstance(r, dict) for r in rows), "packet_rows_invalid", "packet.rows", name)
            expected_ids = [f"V600-{i:04d}" for i in range((batch - 1) * 25 + 1, min(batch * 25, n) + 1)]
            require([r.get("id") for r in rows] == expected_ids, "packet_id_count_order_mismatch", "packet.rows.id", name)
            parsed_packets[name] = packet
    binding = {"status": "immutable_administrative_receipts", "phase": PHASE,
               "freeze_sha256": sha(freeze_raw), "seal_sha256": sha(seal_raw),
               "holdout": str(holdout), "receiver_sha256": sha(current)}
    return {"freeze": freeze, "seal": seal, "packets": parsed_packets, "packet_bytes": released,
            "legacy": legacy, "bridge": bridge, "tracked": tracked, "binding": binding, "batches": batches}


def result_error_field(exc):
    """Map helper errors to fixed field names; never echo submitted strings/IDs."""
    text = str(exc)
    fields = ("safety_quality_basis", "fairness_subtypes", "innovation_subtypes", "input_assessment",
              "material_issue", "dimension_reasons", "completed_at", "input_packet_sha256",
              "protocol_version", "protocol_acknowledged", "rule_questions", "rationale", "evidence", "coder")
    for field in fields:
        if field in text:
            return field
    if "five reasons" in text or ".reason." in text: return "dimension_reasons"
    if "protocol acknowledgement" in text: return "protocol_acknowledged"
    if "packet hash" in text: return "input_packet_sha256"
    if "protocol version" in text: return "protocol_version"
    if "ID" in text or " id " in text: return "rows.id"
    if "dimension" in text or "0/1" in text or "labels" in text: return "rows.labels"
    return "result_schema"


def validate_submission(raw, relative, context):
    coder = relative.split("/")[0][-1]
    match = RESULT_PATTERN.fullmatch(Path(relative).name)
    require(match is not None, "invalid_result_filename", "filename", relative)
    batch = int(match.group(1))
    packet_name = f"agent-{coder}/材料-{batch:02d}.json"
    require(packet_name in context["packets"], "unexpected_result_batch", "batch", relative)
    document = read_json(raw, "result_json", relative)
    identity = document.get("identity")
    require(isinstance(identity, dict) and identity.get("kind") == "AI", "invalid_AI_identity", "identity.kind", relative)
    require(isinstance(identity.get("name"), str) and bool(identity["name"].strip()), "identity_name_required", "identity.name", relative)
    for field in ("batch", "total_batches"):
        require(field not in document or type(document[field]) is int, "literal_integer_required", field, relative)
    try:
        rows = context["legacy"].validate_result(document, coder, context["freeze"]["protocol_version"],
                     context["packets"][packet_name], sha(context["packet_bytes"][packet_name]), "submission")
    except Exception as exc:
        raise AdminError("result_schema_invalid", result_error_field(exc), relative) from None
    for row in rows.values():
        require(isinstance(row.get("material_issue"), str) and bool(row["material_issue"].strip()),
                "material_issue_required", "material_issue", relative)
    return batch, len(rows)


def receive(freeze_path, holdout, receipts):
    for path in (freeze_path, holdout, receipts):
        require(path.is_absolute(), "absolute_path_required", "arguments")
    freeze_path, holdout, receipts = (p.resolve() for p in (freeze_path, holdout, receipts))
    require(receipts != holdout and holdout not in receipts.parents and receipts not in holdout.parents,
            "separate_receipts_directory_required", "receipts")
    context = prepare(freeze_path, holdout)
    receipts.mkdir(parents=True, exist_ok=True)
    binding_path = receipts / "接收绑定.json"
    if binding_path.exists():
        require(read_json(raw_file(binding_path, "receipt_binding"), "receipt_binding") == context["binding"],
                "receipt_binding_changed", "receipt_binding")
    else:
        require(not any(receipts.iterdir()), "unbound_receipts_not_empty", "receipt_binding")
        exclusive_bytes(binding_path, encoded(context["binding"]))
    summary = {c: {"expected_batches": context["batches"], "received_files": 0,
                   "validated_batches": [], "validated_rows": 0, "not_received_batches": []} for c in ("A", "C")}
    errors = []
    inventory = result_inventory(holdout)
    original_hashes = {}
    try:
        archived = result_inventory(receipts)
        records_root = receipts / "receipt-records"
        records = result_inventory(records_root)
        require(set(records) <= set(archived), "archived_raw_missing", "receipt_raw")
        # Check immutable prior receipts before accepting anything new.
        for relative, path in archived.items():
            raw = raw_file(path, "receipt_raw", relative)
            if relative in records:
                record = read_json(raw_file(records[relative], "receipt_record", relative), "receipt_record", relative)
                require(record.get("sha256") == sha(raw) and record.get("byte_count") == len(raw)
                        and record.get("file") == relative and record.get("binding") == context["binding"],
                        "archived_raw_or_record_changed", "receipt_raw", relative)
            require(relative in inventory, "previously_received_source_missing", "result_file", relative)
            current = raw_file(inventory[relative], "result_file", relative)
            require(current == raw, "previously_received_source_changed", "result_bytes", relative)
        for relative, path in inventory.items():
            raw = raw_file(path, "result_file", relative)
            original_hashes[relative] = sha(raw)
            archive_path = receipts / relative
            if relative not in archived:
                exclusive_bytes(archive_path, raw)
            else:
                require(raw_file(archive_path, "receipt_raw", relative) == raw,
                        "previously_received_source_changed", "result_bytes", relative)
            record_path = records_root / relative
            if relative not in records:
                exclusive_bytes(record_path, encoded({"file": relative, "sha256": sha(raw), "byte_count": len(raw),
                    "recorded_at": datetime.now(timezone.utc).isoformat(), "binding": context["binding"],
                    "recovered_prior_raw_without_record": relative in archived}))
            coder = relative.split("/")[0][-1]
            try:
                batch, count = validate_submission(raw, relative, context)
                summary[coder]["validated_batches"].append(batch)
                summary[coder]["validated_rows"] += count
            except AdminError as exc:
                errors.append(exc.issue)
        require(set(result_inventory(holdout)) == set(inventory), "result_inventory_changed_during_receive", "result_inventory")
        for relative, digest in original_hashes.items():
            require(sha(raw_file(inventory[relative], "result_file", relative)) == digest,
                    "result_changed_during_receive", "result_bytes", relative)
            require(sha(raw_file(receipts / relative, "receipt_raw", relative)) == digest,
                    "archived_raw_changed_during_receive", "receipt_raw", relative)
        for path, digest in context["tracked"].items():
            require(sha(raw_file(Path(path), "verified_input", Path(path).name)) == digest,
                    "verified_input_changed_during_receive", "verified_input", Path(path).name)
    except AdminError as exc:
        errors.append(exc.issue)
    received_inventory = result_inventory(receipts)
    for coder in ("A", "C"):
        summary[coder]["received_files"] = sum(name.startswith("agent-" + coder + "/") for name in received_inventory)
        summary[coder]["not_received_batches"] = [b for b in range(1, context["batches"] + 1)
            if f"agent-{coder}/结果-{b:02d}.json" not in inventory]
    report = {"status": "structural_errors" if errors else "administrative_checks_passed",
              "checked_at": datetime.now(timezone.utc).isoformat(), "phase": PHASE,
              "summary": summary, "structural_errors": errors, "performance_computed": False}
    report_path = receipts / "validation-reports" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-") + uuid.uuid4().hex + ".json")
    exclusive_bytes(report_path, encoded(report))
    return {**report, "validation_report": str(report_path)}


def synthetic_qa():
    import copy
    import tempfile
    here = Path(__file__).resolve()
    names = {"results_bridge": "paired_holdout_results.py", "sample_helpers": "sample_holdout.py",
             "legacy_results_helpers": "holdout_results.py", "sampler": "sample_paired_holdout.py",
             "survey_metrics": "survey_metrics.py", "paired_version_metrics": "paired_version_metrics.py",
             "admin_receiver": here.name}
    sources = {key: here.with_name(name).read_bytes() for key, name in names.items()}
    bridge = types.ModuleType("_synthetic_fixture_bridge")
    bridge.__file__ = "<synthetic fixture bridge>"
    exec(compile(sources["results_bridge"], bridge.__file__, "exec"), bridge.__dict__)
    bundle = bridge.synthetic_bundle(sources)
    checks = {}
    with tempfile.TemporaryDirectory(prefix="codex-admin-receiver-synthetic-") as temp:
        root = Path(temp).resolve()
        def fixture(name, change=None):
            case = root / name
            holdout, receipts, frozen_dir = case / "holdout", case / "receipts", case / "frozen"
            b = copy.deepcopy(bundle)
            if change: change(b)
            freeze = read_json(b["freeze"], "synthetic.freeze")
            for key, entry in freeze["files"].items():
                entry["path"] = str(frozen_dir / key)
                # Intentionally do NOT create predictions, dictionaries, corpus or
                # metrics. Reception must not need to open any of those inputs.
                if key in ADMIN_INPUTS:
                    exclusive_bytes(Path(entry["path"]), b["frozen"][key])
            freeze_raw = encoded(freeze)
            seal = read_json(b["seal"], "synthetic.seal")
            seal["freeze_manifest_sha256"] = sha(freeze_raw)
            mapping = read_json(b["released"]["抽样清单-研究者.json"], "synthetic.mapping")
            mapping["plan"]["freeze_manifest_sha256"] = sha(freeze_raw)
            b["released"]["抽样清单-研究者.json"] = encoded(mapping)
            seal["output_files"]["抽样清单-研究者.json"] = sha(b["released"]["抽样清单-研究者.json"])
            freeze_path = case / "freeze.json"
            exclusive_bytes(freeze_path, freeze_raw)
            exclusive_bytes(holdout / "封存信息.json", encoded(seal))
            for rel, raw in b["released"].items(): exclusive_bytes(holdout / rel, raw)
            for rel, raw in b["results"].items(): exclusive_bytes(holdout / rel, raw)
            return freeze_path, holdout, receipts, b
        def run(paths):
            return receive(*paths[:3])
        complete = fixture("complete")
        first = run(complete)
        require(not first["structural_errors"] and all(x["validated_rows"] == 26 for x in first["summary"].values()), "QA_failed", "receive_complete")
        raw_paths = result_inventory(complete[2])
        original = {k: (p.read_bytes(), p.stat().st_mtime_ns) for k, p in raw_paths.items()}
        second = run(complete)
        require(not second["structural_errors"] and all((p.read_bytes(), p.stat().st_mtime_ns) == original[k] for k, p in raw_paths.items()), "QA_failed", "repeat_unchanged")
        checks["first_receive_and_repeat_preserve_raw_bytes_and_mtime"] = True
        for name, operation, expected in (
            ("changed", lambda p: p.write_bytes(p.read_bytes() + b" "), "previously_received_source_changed"),
            ("missing", lambda p: p.unlink(), "previously_received_source_missing")):
            paths = fixture(name); run(paths)
            stored = (paths[2] / "agent-A/结果-01.json").read_bytes()
            operation(paths[1] / "agent-A/结果-01.json")
            report = run(paths)
            require(any(e["code"] == expected for e in report["structural_errors"])
                    and (paths[2] / "agent-A/结果-01.json").read_bytes() == stored, "QA_failed", name)
            checks[name + "_source_rejected_original_preserved"] = True
        def invalid_json(b): b["results"]["agent-A/结果-01.json"] = b'{"broken":'
        invalid = fixture("invalid-json", invalid_json)
        report = run(invalid)
        require(any(e["field"] == "result_json" for e in report["structural_errors"])
                and (invalid[2] / "agent-A/结果-01.json").read_bytes() == b'{"broken":', "QA_failed", "invalid_raw_retained")
        (invalid[1] / "agent-A/结果-01.json").write_bytes(bundle["results"]["agent-A/结果-01.json"])
        report = run(invalid)
        require(any(e["code"] == "previously_received_source_changed" for e in report["structural_errors"]), "QA_failed", "invalid_raw_not_replaceable")
        checks["invalid_JSON_received_before_validation_and_cannot_be_replaced"] = True
        paths = fixture("archive-changed"); run(paths)
        (paths[2] / "agent-A/结果-01.json").write_bytes(b"SYNTHETIC ARCHIVE MODIFICATION")
        report = run(paths)
        require(any(e["code"] == "archived_raw_or_record_changed" for e in report["structural_errors"]),
                "QA_failed", "archive_tamper_rejected")
        checks["archived_raw_tampering_rejected"] = True
        paths = fixture("archive-missing"); run(paths)
        (paths[2] / "agent-A/结果-01.json").unlink()
        report = run(paths)
        require(any(e["code"] == "archived_raw_missing" for e in report["structural_errors"]),
                "QA_failed", "archive_disappearance_rejected")
        checks["archived_raw_disappearance_rejected"] = True
        def malformed_name(b):
            b["results"]["agent-A/结果-bad.json"] = b["results"].pop("agent-A/结果-01.json")
        paths = fixture("malformed-name", malformed_name); report = run(paths)
        require(any(e["field"] == "filename" for e in report["structural_errors"])
                and (paths[2] / "agent-A/结果-bad.json").read_bytes() == paths[3]["results"]["agent-A/结果-bad.json"],
                "QA_failed", "malformed_filename_received")
        checks["malformed_result_filename_raw_retained"] = True
        for field, mutate in (("identity.kind", lambda d: d.update(identity={"kind": "human", "name": "synthetic"})),
                              ("identity.name", lambda d: d.update(identity={"kind": "AI", "name": " "})),
                              ("material_issue", lambda d: d["rows"][0].update(material_issue="")),
                              ("batch", lambda d: d.update(batch=True)),
                              ("input_packet_sha256", lambda d: d.update(input_packet_sha256="0" * 64))):
            def change(b, mutate=mutate):
                d = read_json(b["results"]["agent-A/结果-01.json"], "synthetic.result")
                mutate(d); b["results"]["agent-A/结果-01.json"] = encoded(d)
            paths = fixture("bad-" + field.replace(".", "-"), change)
            report = run(paths)
            require(any(e["field"] == field for e in report["structural_errors"])
                    and (paths[2] / "agent-A/结果-01.json").read_bytes() == paths[3]["results"]["agent-A/结果-01.json"], "QA_failed", field)
            checks["supplemental_or_legacy_field_rejected_" + field] = True
        for name, target in (("receiver", "admin_receiver"), ("shared_document", "protocol")):
            paths = fixture("frozen-" + name)
            frozen = read_json(paths[0].read_bytes(), "synthetic.freeze")
            Path(frozen["files"][target]["path"]).write_bytes(b"SYNTHETIC CHANGED INPUT")
            try: run(paths)
            except AdminError as exc: require(exc.issue["code"] == "frozen_input_hash_mismatch", "QA_failed", name)
            else: raise AssertionError("Tampered frozen input accepted")
            checks["frozen_" + name + "_hash_required"] = True
        for name in list(STATIC_DOCS.values()) + ["材料-01.json"]:
            paths = fixture("sealed-" + name)
            (paths[1] / "agent-C" / name).write_bytes(b"SYNTHETIC RELEASE CHANGE")
            try: run(paths)
            except AdminError as exc: require(exc.issue["code"] == "sealed_release_hash_mismatch", "QA_failed", "sealed_release_hash")
            else: raise AssertionError("Changed sealed document/packet accepted")
        checks["all_three_shared_documents_and_packets_seal_bound"] = True
        paths = fixture("partial")
        for rel in paths[3]["results"]:
            if rel != "agent-A/结果-01.json": (paths[1] / rel).unlink()
        partial = run(paths)
        require(not partial["structural_errors"] and partial["summary"]["A"]["validated_rows"] == 25
                and partial["summary"]["C"]["validated_rows"] == 0, "QA_failed", "partial_progress")
        checks["not_yet_submitted_batches_allowed"] = True
        # No raw supplied strings, labels, reasons, or statistical artifacts are
        # included in administrative reports; malicious row IDs are not echoed.
        def malicious(b):
            d = read_json(b["results"]["agent-A/结果-01.json"], "synthetic.result")
            d["rows"][0]["id"] = "SECRET_SYNTHETIC_SUBMISSION_STRING"
            b["results"]["agent-A/结果-01.json"] = encoded(d)
        paths = fixture("nonleak", malicious); report = run(paths)
        require("SECRET_SYNTHETIC_SUBMISSION_STRING" not in json.dumps(report) and '"labels":' not in json.dumps(report), "QA_failed", "report_nonleak")
        for p in root.rglob("*"):
            require("performance" not in p.name and "统计" not in p.name, "QA_failed", "no_performance_artifacts")
        checks["reports_do_not_echo_labels_text_or_ID_values"] = True
        checks["no_metric_function_or_prediction_file_needed"] = True
        checks["no_performance_artifact_created"] = True
    require(sources == {key: here.with_name(name).read_bytes() for key, name in names.items()}, "QA_failed", "code_changed_during_QA")
    return {"status": "passed_synthetic_administrative_QA", "checks": checks,
            "code_sha256": {k: sha(v) for k, v in sources.items()}, "real_sample_created": False,
            "real_materials_or_labels_read": False, "performance_computed": False,
            "limits": ["Uses synthetic_bundle and real temporary filesystem operations only.",
                       "Administrative schema/hash checks do not establish independent or correct substantive judgments."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--holdout", type=Path)
    parser.add_argument("--receipts", type=Path)
    parser.add_argument("--synthetic-qa", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.synthetic_qa:
            require(args.freeze is None and args.holdout is None and args.receipts is None and args.output is not None,
                    "synthetic_QA_accepts_only_output", "arguments")
            result = synthetic_qa()
            exclusive_bytes(args.output, encoded(result))
            print(json.dumps({"status": result["status"], "output": str(args.output)}, ensure_ascii=False))
            return 0
        require(args.freeze is not None and args.holdout is not None and args.receipts is not None and args.output is None,
                "explicit_freeze_holdout_receipts_required", "arguments")
        result = receive(args.freeze, args.holdout, args.receipts)
        print(json.dumps(result, ensure_ascii=False))
        return 2 if result["structural_errors"] else 0
    except AdminError as exc:
        print(json.dumps({"status": "structural_errors", "structural_errors": [exc.issue], "performance_computed": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
