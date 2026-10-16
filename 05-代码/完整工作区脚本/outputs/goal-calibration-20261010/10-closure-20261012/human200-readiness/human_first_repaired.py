"""Original issued200 A/B initial agreement only; no machine/reference admission.

The historical120/80 allocation is retained, not certified as current unexposed.
Actual user-reviewed independent submissions are required before label I/O.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import posixpath
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LATER = ROOT / "07-statistics/human200-machine-reference-handoff-sol"
RECEIVER = ROOT / "05-validation/human200-reception-root"
HISTORICAL_POPULATION = {"remaining": 1444, "exposed": 3037}
HISTORICAL_SAMPLE = {"remaining": 120, "exposed": 80}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def pinned(path, size, digest):
    expected = {"path": str(path.resolve()), "bytes": size, "sha256": digest}
    require(binding(path) == expected, "Changed sealed metadata/helper: " + str(path))
    return expected


def helpers():
    # Importing the sealed helper has no label I/O. Do not call its full
    # contract(), which also hashes machine predictions and source packets.
    code = pinned(LATER / "handoff.py", 27412,
                  "65ec6edce057d8504846f9a368027e81e2f246292399e1fdbc3457d8767cfa30")
    contract_binding = pinned(LATER / "bindings.json", 14967,
                              "b1247eb5d5a75a8e322dba89ee5fe3268f9691f1d87f4a913a1d5030528488bb")
    spec = importlib.util.spec_from_file_location("_issued200_AB_projection", code["path"])
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    contract = helper.load(Path(contract_binding["path"]))
    first = helper.module("_issued200_actual_review_gate", contract["frozen_inputs"]["human_first"])
    original_module = helper.module
    reader_binding = contract["frozen_inputs"]["receiver_source_reader"]

    def compatible_module(name, item):
        imported = original_module(name, item)  # Preserve exact sealed-byte verification.
        if item == reader_binding:
            # The sealed reader omitted this standard-library import. Injection
            # occurs only when projection imports it, after the actual review.
            require("posixpath" not in imported.__dict__, "Unexpected sealed reader dependency")
            imported.posixpath = posixpath
        return imported

    helper.module = compatible_module
    return helper, contract, first, {
        "projection_helper": code, "projection_contract": contract_binding,
        "runtime_reader_compatibility": {
            "reader": reader_binding, "injected_standard_library": "posixpath",
            "sealed_source_modified": False,
        },
    }


def human_contract(helper, contract):
    """Verify only the frozen A/B, design, frame and original-engine inputs."""
    frozen = contract["frozen_inputs"]
    keys = ("human_first", "human_first_bindings", "receiver_bindings",
            "receiver_code", "receiver_source_reader", "receiver_seal",
            "statistics_template", "assigned_design", "draw", "workbook_manifest",
            "materials", "manual", "engine", "LLM_manifest", "LLM_frame_ids")
    used = {key: frozen[key] for key in keys}
    for item in used.values():
        helper.verify(item)
    original = helper.load(helper.verify(frozen["human_first_bindings"]))
    for old_key, key in (("code", "human_first"), ("engine", "engine"),
                         ("receiver_bindings", "receiver_bindings"),
                         ("statistics_template", "statistics_template"),
                         ("assigned_design_metadata", "assigned_design"),
                         ("manual", "manual"), ("production_manifest", "LLM_manifest")):
        require(original[old_key] == frozen[key], "Original A/B binding differs: " + key)
    manifest = helper.load(helper.verify(frozen["LLM_manifest"]))
    require(manifest["ordered_source_ids"] == frozen["LLM_frame_ids"], "Frame binding differs")
    frame = helper.frozen_frame(manifest)  # ID metadata only, no predictions.
    draw = helper.load(helper.verify(frozen["draw"]))["records"]
    ids = [row["source_id"] for row in draw]
    require(len(ids) == 200 and len(set(ids)) == 200 and set(ids) <= set(frame),
            "Original200 sample/frame mismatch")
    require(dict(Counter(row["domain"] for row in draw)) == HISTORICAL_SAMPLE,
            "Original120/80 allocation differs")
    meta = helper.load(helper.verify(frozen["statistics_template"]))["metadata"]
    require(meta["design"]["domain_population_N"] == HISTORICAL_POPULATION,
            "Original1444/3037 domain design differs")
    return used


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receive-dir", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output_dir.resolve()
    runs = HERE / "runs"
    require(output.is_relative_to(runs) and output != runs and not output.exists(),
            "Use a new output directory below human200-readiness/runs; never overwrite")
    helper, contract, first, dependencies = helpers()
    # The unchanged actual-review gate runs before projection, material reads,
    # engine loading, statistics, and creation of any result directory.
    review, report, receive_seal = first.reviewed_receive(args.receive_dir, args.review)
    used = human_contract(helper, contract)
    payload = helper.initial_projection(args.receive_dir.resolve(), review, contract)
    require(payload["metadata"]["analysis_stage"] == "human_first", "A/B-only stage required")
    require(payload["metadata"]["design"]["domain_population_N"] == HISTORICAL_POPULATION,
            "Projected historical design changed")
    require(all(set(row["outputs"]) == {"A", "B"} for row in payload["records"]),
            "Machine/reference outputs prohibited")
    engine = helper.module("_issued200_original_domain_engine", used["engine"])
    engine.prepare(payload)
    result = engine.analyze(payload, replicates=5000, seed=20261010,
                            guard_mode="single_category")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(exist_ok=False)
    for name, data in (("bound-statistical-input.json", payload),
                       ("human-first-results.json", result)):
        with (output / name).open("x", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
    receipt = {
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "actual_reviewed_original_issued200_AB_initial_agreement",
        "scope": "原发放200条协商前A/B人际一致性；历史120/80不表示现版未开发/曝光域",
        "analysis_stage": "human_first", "sample_N": 200,
        "historical_domain_population_N": HISTORICAL_POPULATION,
        "historical_sample_by_domain": HISTORICAL_SAMPLE,
        "replicates": 5000, "seed": 20261010, "guard_mode": "single_category",
        "review": binding(args.review),
        "receive_seal": binding(args.receive_dir / "seal.json"),
        "code": binding(__file__), "reused_helpers": dependencies,
        "verified_human_only_inputs": used,
        "human_identity_is_actual_user_attestation_not_crypto_authentication": True,
        "current_unexposed_validation_claimed": False,
        "human_reference_created": False, "machine_predictions_admitted": False,
        "machine_accuracy_or_annual_analysis_performed": False,
        "project_overall_acceptance_claimed": False,
        "members": [binding(path) for path in sorted(output.iterdir()) if path.is_file()],
    }
    with (output / "seal.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": receipt["status"], "sample_N": 200,
                      "output": str(output), "formal_acceptance": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
