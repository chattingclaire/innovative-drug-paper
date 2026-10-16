"""Transparent, nonblind AI adjudication; preserves every first judgement."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / "04-calibration/source-impact4-v12/admin"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source_path = ROOT / "00-baseline/source-files/09d813b3014db413-NMPA-数据保护2026-完整结构化正文.json"
source = json.loads(source_path.read_text())
assert sha(source_path) == "09d813b3014db4137d2bceab8bc280c396a5916fafa7bb4c216c5798ae824d06"
structure = ROOT / "06-coding/root-machine-review/01423-source-branches-sol"
seal = json.loads((structure / "delivery-seal.json").read_text())
for item in seal["files"]:
    path = Path(item["path"])
    assert sha(path) == item["sha256"] and path.stat().st_size == item["bytes"]
manual = ROOT / "03-manual/common-manual-v1.1-development.md"
assert sha(manual) == "6ffc7b35a5cbe1c1f90c81d24d1508dba7adefe5e7bbd058c284d76e14b8a70f"
inputs = []
old = {}
for n in (41, 36):
    p = ROOT / f"06-coding/development-reference{n}-v11/reference.jsonl"
    inputs.append({"path": str(p), "sha256": sha(p)})
    for line in p.read_text().splitlines():
        x = json.loads(line)
        assert x["id"] not in old
        old[x["id"]] = x
ids = ("RECODE25-00887", "RECODE25-00891", "RECODE25-00859", "RECODE25-01423")
decisions = [{"id": rid, "labels": old[rid]["labels"], "reference_labels_changed": False,
              "status": "historical_development_reference_retained_after_source_review"}
             for rid in ids]
current = "5.1 | 境外上市的原研药品申请在境内上市 | 6年 | 符合第七条第二款情形的，数据保护期为4年。"
reason = (
    "固定单元是完整原研表行，包含6年基础安排及4年条件例外，不能缩为备注。"
    "同版第三条明确连接附表；第五条第二款定义相同原研对象的6年待遇，第三款定义其保护的安全、有效和质量试验数据范围。"
    "按共同手册第44行同一安排有限定义补全及完整命题规则，基础分支提供S/E依据。"
    "4年例外另经七条第二款至六条的相应临床优势数据范围，不须把七条第一款首次申请全部安全要求移入例外。"
    "I依据保护范围与实质改良/临床优势资格的直接权利关系；没有明确价格支付或公平关系，Ec/F仍为0。"
)
decisions[-1].update({
    "current_full_unit": current,
    "root_rationale": reason,
    "S_decision": 1,
    "new_A_B_native_S0_review": "shared_omission_of_base_six_year_branch",
    "old_root_reason_corrected": "S不再依该药品回指而继承首次全部义务；用基础6年及第五条条内保护范围直接关系支持",
    "literal_source_evidence": [
        {"locator": f"/normative_paragraphs/{i}", "quote": source["normative_paragraphs"][i]}
        for i in (3, 9, 10, 17, 18)
    ],
    "fifth_article_in_original_25_CTX": False,
    "fifth_article_available_in_bound_original_snapshot": True,
    "neutral_shared_addendum_required_for_next_common_execution": True,
})
report = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "status": "root_nonblind_AI_development_adjudication_complete",
    "actor": "root_AI", "human": False, "fresh_holdout": False,
    "source_sha256": sha(source_path), "manual_sha256": sha(manual),
    "source_structure_seal_sha256": sha(structure / "delivery-seal.json"),
    "historical_reference_files": inputs, "decisions": decisions,
    "new_A_B_first_judgements_unchanged": True,
    "native_first_judgements_unchanged": True,
    "dimensions_redefined": False, "thresholds_changed": False,
    "adjudication_before_new_metric_computation": True,
    "caveat": "AI同判可用于信度诊断，不能自动作为正确性或真人编码证明。"
}
out = ADMIN / "root-adjudication.json"
with out.open("x") as stream:
    stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
dest = ROOT / "06-coding/development-reference36-v12-root-adjudicated"
dest.mkdir()
rows = [old[x["id"]] for x in map(json.loads, (ROOT / "06-coding/development-reference36-v11/reference.jsonl").read_text().splitlines())]
for row in rows:
    row["reference_actor_type"] = "AI_development_adjudication_not_human"
    row["source_version"] = "v12_with_bound_original_snapshot_review"
    if row["id"] == "RECODE25-01423":
        row["root_current_rationale"] = reason
        row["root_adjudication_sha256"] = sha(out)
(dest / "reference.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
binding = {"reference_sha256": sha(dest / "reference.jsonl"), "adjudication_sha256": sha(out),
           "historical_source": inputs[1], "n": 36, "labels_changed_n": 0,
           "old_first_judgements_overwritten": False, "human_reference": False,
           "full_common_execution_with_addendum_done": False}
(dest / "manifest.json").write_text(json.dumps(binding, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(binding, ensure_ascii=False))
