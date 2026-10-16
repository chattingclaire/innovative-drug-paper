"""Read-only mechanical freeze preflight; produces no labels/model results."""
import argparse
import json
from pathlib import Path
import sys
import jsonschema
from transport_common import HERE, PYTHON, campaign, CONDITIONS, REQUIRED_KEYS, allowed_inputs, check, binding, load, save, now

def preflight(run, output):
    run, d = campaign(run)
    if Path(sys.executable).resolve() != Path(PYTHON).resolve():
        raise ValueError("Use the verified system Python3.14/jsonschema runtime")
    check(d["python_binding"])
    check(d["old_manifest"])
    old = load(d["old_manifest"]["path"])
    if old["record_N"] != 800 or old["batch_N"] != 87:
        raise ValueError("Old diagnostic scope changed")
    checks, semantic_checks = [], []
    checked = set()
    def once(b):
        if b["path"] not in checked:
            check(b)
            checks.append({k: b[k] for k in ("path", "bytes", "sha256")})
            checked.add(b["path"])
    once(d["mechanical_controls"])
    controls = load(d["mechanical_controls"]["path"])
    if controls["all_pass"] is not True or controls["model_calls"] != 0 or controls["classifier_calls"] != 0:
        raise ValueError("Mechanical controls not accepted")
    for b in controls["implementation_bindings"]:
        once(b)
    for b in [*d["implementation_bindings"], *d["input_file_bindings"], *d["cli_executable_bindings"], d["validator"], d["ordered_source_ids"], d["sample_metadata_coordinator_only"], d["statistics_engine"], d["statistics_bridge"], d["external_routing"]]:
        once(b)
    ids = load(d["ordered_source_ids"]["path"])
    if [i for b in d["batches"] for i in b["members"]] != ids:
        raise ValueError("Changed fixed800 batch order")
    for newrow, oldrow in zip(d["batches"], old["batches"]):
        if any(newrow[k] != oldrow[k] for k in ("batch_id", "members", "expected_N", "original_packet_bytes")):
            raise ValueError("Old87 batch members/order changed")
        assignments = {}
        for form in ("raw", "W"):
            a, allowed = allowed_inputs(newrow["assignments"][form]["path"])
            assignments[form] = a
            oa = load(oldrow["assignments"][form]["path"])
            for k in ("packets", "source_asset_bindings", "manual", "execution_prompt", "run_scope_binding", "packet_schema", "source_ids", "expected_N", "context_unit", "scope", "requested_model", "requested_reasoning_effort"):
                if a[k] != oa[k]:
                    raise ValueError("Changed conceptual/member/source input: " + k)
            for b in allowed.values():
                once(b)
            schema = load(a["output_schema"]["path"])
            jsonschema.Draft202012Validator.check_schema(schema)
            oschema = load(oa["output_schema"]["path"])
            oschema["properties"]["run_id"] = {"const": d["run_id"]}
            oschema["title"] = schema["title"]
            if oschema != schema:
                raise ValueError("Output first schema changed beyond campaign/title metadata")
        for raw, W in zip(assignments["raw"]["packets"], assignments["W"]["packets"]):
            # Programmatic semantic-object equality, not model presentation or
            # a human review; no contents/answers/labels are emitted.
            if load(raw["path"]) != load(W["path"]):
                raise ValueError("W decoded source object changed")
            semantic_checks.append({"source_id": raw["source_id"], "raw": raw, "W": W, "decoded_object_equal": True, "model_read_claimed": False})
        base = Path(newrow["requests"]["base"]["path"]).read_bytes()
        H = Path(newrow["requests"]["H"]["path"]).read_bytes()
        if not base.startswith("判读要求\n".encode()) or H != "判读说明\n".encode() + base.split(b"\n", 1)[1]:
            raise ValueError("H changed more than first-line synonym")
        for r in (r for r in d["routes"] if r["batch_id"] == newrow["batch_id"]):
            wanted = newrow["requests"]["H" if r["condition"] == "H" else "base"]
            if r["fixed_request"] != wanted:
                raise ValueError("R/W/H actual stdin condition identity changed")
            form = "W" if r["condition"] == "W" else "raw"
            if r["assignment"] != newrow["assignments"][form] or r["working_directory"] != str(Path(r["assignment"]["path"]).parent):
                raise ValueError("External route input/CWD mismatch")
            if any(Path(r["output_directory"]).iterdir()):
                raise ValueError("Actual/partial attempt already present; this is not a no-call preflight")
    schemas = load(HERE / "artifact-schemas.json")
    for definition in schemas["$defs"].values():
        jsonschema.Draft202012Validator.check_schema({"$defs": schemas["$defs"], **definition})
    result = {"at_utc": now(), "artifact_type": "no_model_external_capture_preflight", "ready_for_ROOT_review": True, "campaign_manifest": binding(run / "run-manifest.json"), "model_calls": 0, "classifier_calls": 0, "GO_issued": False, "batch_N": 87, "record_N": 800, "conditions": list(CONDITIONS), "max_concurrent_CLI": 3, "all1305_slots_empty": True, "same_R_stdin_and_CWD": True, "route_or_attempt_in_user_stdin": False, "H_only_first_line_delta": True, "W_decoded_object_equality_N": len(semantic_checks), "W_hash_object_load_is_model_reading": False, "old_sources_members_and_conceptual_schema_preserved": True, "exact_unique_input_binding_N": len(checks), "checked_bindings": checks, "W_binding_checks": semantic_checks, "human200_answers_opened": False, "actual_serving_model_verified": False}
    return save(output, result)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    print(json.dumps(preflight(a.run, a.output), ensure_ascii=False))
