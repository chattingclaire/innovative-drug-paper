"""Adjudicate actual disagreements against the existing manual, without overwrites."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
REVIEW = ROOT / "06-coding/root-machine-review/native36-v12-three-semantic-sol"
seal = json.loads((REVIEW / "delivery-seal.json").read_text())
for item in seal["output_files"]:
    path = Path(item["absolute_path"])
    assert sha(path) == item["sha256"] and path.stat().st_size == item["bytes"]
assert sha(REVIEW / "semantic-review.json") == "381c9c69d145243f41da8ad158c0cf16598d5f6a41cb25c76f5297e20ccb05a6"
previous = ROOT / "04-calibration/source-impact4-v12/admin/root-adjudication.json"
old36 = ROOT / "06-coding/development-reference36-v12-root-adjudicated/reference.jsonl"
rows = [json.loads(l) for l in old36.read_text().splitlines()]
byid = {x["id"]: x for x in rows}
reasons = {
    "RECODE25-04333": (
        "完整第一条仅列规范处方审核、促进合理用药及保障用药安全作为制定文件的宗旨。"
        "按既有手册9/44/56/66，明确用药对象及安全目的仍须实质问题、内容要求或风险管理安排；"
        "制定本规范不能从后文倒借具体审核措施。S=0并非因总则位置，也不要求具体不良反应才可有S。"
        "旧A/B及旧root把一般安全宗旨当实质措施，原S=1和旧理由保留，现予以纠正。"
    ),
    "RECODE25-00720": (
        "当前完整条件后果是申报时选择条件3。确指清单的共同父句为可以按程序申报（单选），"
        "主动申请调整医保支付范围描述申报类别，不在当前授予/限制调整权利或核验支付信息。"
        "后续调整范围及签补充协议是其他记录安排，不倒补。Ec=0不以金额、调整细节、充分批准或成功为前提。"
    ),
    "RECODE25-03818": (
        "到期、用途未重大变化、支付范围与说明书不一致及主动申请调整均完整保留，"
        "当前行为仍是选择目录内申报条件2，完整共同父谓词为可以按程序申报（单选）。"
        "分支前提没有成为当前支付信息核验/评价任务或条件到调整权利的直接后果。"
        "不继承前后兄弟项的续约/补充协议；不要求具体金额、调整方式细节或最终成功才纳入Ec。"
    )
}
assert byid["RECODE25-04333"]["labels"]["S"] == 1
byid["RECODE25-04333"]["labels"]["S"] = 0
decisions = []
for rid, dim in (("RECODE25-04333", "S"), ("RECODE25-00720", "Ec"), ("RECODE25-03818", "Ec")):
    row = byid[rid]
    assert row["labels"][dim] == 0
    row.setdefault("root_current_rationales", {})[dim] = reasons[rid]
    row["reference_actor_type"] = "AI_development_adjudication_not_human"
    decisions.append({"id": rid, "dimension": dim, "adjudicated_value": 0,
                      "historical_reference_value": 1 if dim == "S" else 0,
                      "reference_value_changed": dim == "S", "rationale": reasons[rid]})
report = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "status": "root_nonblind_AI_development_adjudication_complete",
    "actor": "root_AI", "human": False, "fresh_holdout": False,
    "review_seal_sha256": sha(REVIEW / "delivery-seal.json"),
    "review_report_sha256": sha(REVIEW / "semantic-review.json"),
    "previous_01423_adjudication_sha256": sha(previous),
    "previous_01423_S1_retained": True,
    "manual_semantic_sha256": "6ffc7b35a5cbe1c1f90c81d24d1508dba7adefe5e7bbd058c284d76e14b8a70f",
    "criteria_redefined": False, "thresholds_changed": False,
    "reviewer_no_performance_summary_read": True,
    "root_previously_saw_first_performance_summary": True,
    "adjudication_before_recomputed_v2_metrics": True,
    "decisions": decisions,
    "raw_AI_A_B_native_first_judgements_changed": False,
    "old_reference_and_old_root_reason_retained": True,
}
out = ROOT / "04-calibration/source-impact4-v12/admin/root-adjudication-native36-v2.json"
with out.open("x") as f:
    f.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
dest = ROOT / "06-coding/development-reference36-v12-root-adjudicated-v2"
dest.mkdir()
for row in rows:
    row["root_adjudication_v2_sha256"] = sha(out)
(dest / "reference.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
manifest = {"reference_sha256": sha(dest / "reference.jsonl"), "n": 36,
            "parent_reference_sha256": sha(old36), "adjudication_sha256": sha(out),
            "label_changes": [{"id": "RECODE25-04333", "dimension": "S", "from": 1, "to": 0}],
            "AI_development_reference": True, "human_reference": False,
            "raw_first_outputs_unchanged": True}
(dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
master = ROOT / "06-coding/development-reference77-v12-root-adjudicated-v2"
master.mkdir()
old41 = ROOT / "06-coding/development-reference41-v11/reference.jsonl"
allrows = [json.loads(l) for l in old41.read_text().splitlines()] + rows
assert len({x["id"] for x in allrows}) == len(allrows) == 77
(master / "reference.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in allrows))
(master / "manifest.json").write_text(json.dumps({"n": 77, "reference_sha256": sha(master / "reference.jsonl"),
    "parents": [{"path": str(old41), "sha256": sha(old41)}, {"path": str(dest / "reference.jsonl"), "sha256": sha(dest / "reference.jsonl")}],
    "source_01423_rationale_adjudication": sha(previous), "three_case_adjudication": sha(out),
    "AI_development_reference": True, "human_reference": False, "new_holdout": False}, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(manifest, ensure_ascii=False))
