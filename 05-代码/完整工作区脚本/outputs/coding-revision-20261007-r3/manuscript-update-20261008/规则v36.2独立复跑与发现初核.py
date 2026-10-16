"""Read-only root audit of the sealed rule candidate and full-corpus counts."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.parent.parent
DIMS = ("S", "E", "Ec", "I", "F")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

binding_path = ROOT / "rules-v36.2-development/final_candidate_binding.json"
binding = json.loads(binding_path.read_text())
pred_path = Path(binding["prediction"]["path"])
replay_path = ROOT / "rules-v36.2-development/root_reproduced_material_v14.jsonl"
assert sha(pred_path) == binding["prediction"]["sha256"]
assert sha(Path(binding["input"]["path"])) == binding["input"]["sha256"]
for field in ("freeze", "run", "QA", "changes", "complete_development_comparison", "reproduce_script"):
    item = binding[field]
    assert sha(Path(item["path"])) == item["sha256"], field
original, replay = rows(pred_path), rows(replay_path)
assert len(original) == len(replay) == 4924
assert original == replay, "Replay must reproduce every complete prediction record"
inputs = rows(ROOT / "rule_inputs_shared_v14.jsonl")
by_id = {x["id"]: x for x in inputs}
assert len(by_id) == 4924
metadata_path = WORKSPACE / "outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json"
metadata = json.loads(metadata_path.read_text())
group_by_file = {Path(x["original_file"]).stem: x["analysis_group"] for x in metadata["rows"]}
llm_path = ROOT / "llm-v32/full-production-candidate02-material-v14-source-citation-reconciled/all_predictions.jsonl"
llm = rows(llm_path)
assert {x["id"] for x in original} == {x["id"] for x in llm} == set(by_id)

def count(predictions, nested):
    result = {g: {"n_units": 0, "counts": Counter({d: 0 for d in DIMS}), "F_and_Ec": 0} for g in ("NMPA", "NHSA", "NHC", "GOV")}
    for item in predictions:
        labels = item["prediction"]["labels"] if nested else item["labels"]
        assert set(labels) == set(DIMS) and all(x in (0, 1) for x in labels.values())
        group = group_by_file[by_id[item["id"]]["input"]["original_file_stem"]]
        target = result[group]
        target["n_units"] += 1
        target["counts"].update(labels)
        target["F_and_Ec"] += labels["F"] * labels["Ec"]
    for group, target in result.items():
        c = dict(target["counts"])
        target["counts"] = c
        total = sum(c.values())
        target["five_dimension_count_sum"] = total
        target["attention_share_percent"] = {d: 100 * c[d] / total if total else None for d in DIMS}
        target["content_coverage_percent"] = {d: 100 * c[d] / target["n_units"] for d in DIMS}
        target["economic_units_with_fairness_percent"] = 100 * target["F_and_Ec"] / c["Ec"] if c["Ec"] else None
        target["fairness_units_with_economic_percent"] = 100 * target["F_and_Ec"] / c["F"] if c["F"] else None
        assert group == "GOV" or target["n_units"] == {"NMPA": 1848, "NHSA": 2100, "NHC": 533}[group]
    assert sum(x["n_units"] for g, x in result.items() if g != "GOV") == 4481
    return result

report = {
    "status": "PASS_root_complete_record_replay_and_full_counts",
    "rule_development_not_independent_validation": True,
    "references_or_labels_modified_by_this_audit": False,
    "binding_sha256": sha(binding_path),
    "rule_sha256": sha(pred_path),
    "replay_sha256": sha(replay_path),
    "llm_baseline_sha256": sha(llm_path),
    "classification_sha256": sha(metadata_path),
    "n_reproduced_complete_records": len(original),
    "rules_v36_2": count(original, True),
    "llm_candidate02_v14_frozen": count(llm, False),
    "interpretation_scope": "Full-corpus descriptive comparison; conditional shares are not five-dimension attention shares or independent validity evidence. Candidate03 full development comparison is still running."
}
for method in ("rules_v36_2", "llm_candidate02_v14_frozen"):
    assert report[method]["NHC"]["economic_units_with_fairness_percent"] > report[method]["NHSA"]["economic_units_with_fairness_percent"]
output = Path(__file__).with_name("规则v36.2独立复跑与发现初核.json")
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": report["status"], "sha_equal": report["rule_sha256"] == report["replay_sha256"], "methods": {m: {g: report[m][g] for g in ("NHSA", "NHC")} for m in ("rules_v36_2", "llm_candidate02_v14_frozen")}}, ensure_ascii=False))
