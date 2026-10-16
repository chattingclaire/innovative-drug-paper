"""Bind the delivered files to their completed numerical and visual checks."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime
import json

ROOT = Path(__file__).resolve().parent


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((ROOT / name).read_text())


expected = {
    "论文修订稿-三部门版.docx": "4ca9e0b4340f045a4f8dd6c2bbb83bd4c8ff88bf1f01426be2f7e397d4923fae",
    "校核与待确认事项.docx": "fcd88872388a4f12c21dc7fe93a18eeeb1935c50519cd61c3efdb23190696f47",
    "三部门编码与注意力指标.xlsx": "1c7ecf2be59acb5405a1aaef9b147ff234bc4eb6fa0bdd3a7a4b98536c69507a",
    "三部门编码指标.json": "5f9eebb9f1942202380163849b9dc593e13e33d9added596820d8c69adaa734e",
    "三部门注意力分布与敏感性.json": "a166f0c4f2cc66b1b0155973639d7614ebabef2c6708de1c264847d2386e0f72",
    "llm-v29/production-25-v29/all_predictions.jsonl": "111ddb35068d5adba9ef7607dfad41a8835339a71371a73b7a71b9e84e527915",
    "rules-v30/all_predictions.jsonl": "6dddd213cbb661f1621a5fcfdbbc003455afd2be4146b24ae455f7efab66f9ee",
}
for name, value in expected.items():
    assert digest(ROOT / name) == value, name

manuscript = read("最终文稿数据与引用核验.json")
assert manuscript["status"] == "passed"
assert manuscript["main_sha256"] == expected["论文修订稿-三部门版.docx"]
assert manuscript["memo_sha256"] == expected["校核与待确认事项.docx"]
assert manuscript["statistics_sha256"] == expected["三部门编码指标.json"]
assert manuscript["attention_sha256"] == expected["三部门注意力分布与敏感性.json"]

for name, target in [
    ("三部门编码指标核验.json", "三部门编码指标.json"),
    ("聚类区间独立重算核验.json", "三部门编码指标.json"),
    ("三部门数据独立QA.json", "三部门注意力分布与敏感性.json"),
]:
    qa = read(name)
    assert qa["status"] == "passed" and qa["target_sha256"] == expected[target]

for name in ["workbook-qa.json", "workbook-visual-qa.json"]:
    qa = read(name)
    assert qa["status"] == "passed"
    assert qa["workbook_sha256"] == expected["三部门编码与注意力指标.xlsx"]
for view in read("workbook-visual-qa.json")["views"]:
    assert digest(ROOT / view["filename"]) == view["sha256"], view["filename"]

layout = read("最终篇幅与模板核验.json")
visual = read("final_evidence_visual_QA.json")
assert layout["main_docx_sha256"] == expected["论文修订稿-三部门版.docx"]
assert digest(layout["render_pdf_path"]) == layout["render_pdf_sha256"]
for record in visual["document_bindings"].values():
    assert digest(record["path"]) == record["sha256"]
pages = set(layout["actually_reviewed_pages"])
pages.update(row["page"] for row in visual["actual_viewed_main_pages"])
assert pages == set(range(1, 20))
assert {row["page"] for row in visual["actual_viewed_memo_pages"]} == {1, 2, 3}
for row in layout["page_reviews"]:
    assert digest(row["path"]) == row["sha256"]
for kind, folder in [("main", "render-final-main-v2"), ("memo", "render-final-memo-v2")]:
    for row in visual[f"actual_viewed_{kind}_pages"]:
        assert digest(ROOT / folder / f'page-{row["page"]}.png') == row["png_sha256"]

execution = read("最终LLM执行独立核验.json")
assert execution["status"] == "passed" and execution["n"] == 4924
assert execution["predictions_sha256"] == expected["llm-v29/production-25-v29/all_predictions.jsonl"]
assert execution["selected_tool_event_count"] == 0
assert execution["mechanically_edited_output_selected"] is False
policy = read("最终政策证据独立QA.json")
assert policy["source_hash_pass"] and policy["quote_pass"] and policy["matrix_complete"]
for name, value in policy["files_sha256"].items():
    assert digest(ROOT.parents[1] / name) == value, name
index = read("论证证据索引.json")
assert index["status"] == "final_bound" and len(index["reference_catalog"]) == 62

qa_names = [
    "最终文稿数据与引用核验.json", "最终LLM执行独立核验.json",
    "三部门编码指标核验.json", "聚类区间独立重算核验.json",
    "三部门数据独立QA.json", "最终政策证据独立QA.json",
    "创新性公平性差错审读独立核验.json", "final_evidence_visual_QA.json",
    "最终篇幅与模板核验.json", "workbook-qa.json", "workbook-visual-qa.json",
    "论证证据索引.json", "指标依据与理论对齐.md",
]
result = {
    "status": "passed_final_delivery_bindings",
    "checked_at": datetime.now().astimezone().isoformat(),
    "files": {name: {"path": str(ROOT / name), "sha256": value} for name, value in expected.items()},
    "evidence_and_qa": {name: {"path": str(ROOT / name), "sha256": digest(ROOT / name)} for name in qa_names},
    "actual_visual_review": {"main_pages": sorted(pages), "memo_pages": [1, 2, 3]},
    "libreoffice_word_counts": layout["word_counts"],
    "main_corpus_units": 4481,
    "all_model_execution_units": 4924,
    "human_validation_completed": False,
    "AC_actual_provenance": "AI agents; preserved independent original submissions used as development references",
    "remaining": ["Actual independent human coding and adjudication", "Author, affiliation, funding and submission details"],
    "scope": "Confirms delivery/source/QA version bindings. Does not certify publication acceptance, independent human validity, or a universal kappa threshold.",
}
(ROOT / "最终交付核验.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": result["status"], "delivered_files": 3, "main_pages": 19, "memo_pages": 3, "human_validation_completed": False}, ensure_ascii=False))
