"""Bind the final filled manuscript to completed numeric, source and visual reviews.

Does not edit DOCX, labels, predictions or any underlying result.
"""
from pathlib import Path
import hashlib
import json

N = Path(__file__).resolve().parent
ROOT = N.parent.parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def binding(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": sha(path)}

def read(path):
    return json.loads(Path(path).read_text())

main = N / "论文修订稿-编码实算结果版.docx"
memo = N / "编码复核说明与真人检验事项.docx"
assert sha(main) == "2145e9d960fe428003181bbe48eb616fb006b05cd1f9b89d4adfeacba8c86585"
assert sha(memo) == "5005be3ccd106f7f89385538fd400a487714eed41e6544091a6c5fdc221ff27e"

checks_path = N / "actual_filled_document_checks.json"
checks = read(checks_path)
assert checks["main_sha256"] == sha(main)
assert checks["memo_sha256"] == sha(memo)
assert checks["checks_count"] == 233
assert checks["status"].startswith("PASS_")

content_path = N / "policy-source-audit/编码实算稿独立内容核查-20261008-v6.json"
content = read(content_path)
assert content["status"] == "PASS_CONTENT_ONLY"
assert not content["blocking_findings"]
assert content["checked_counts"] == {"checks": 16, "table2_scalars": 80, "AB_kappa": 5, "actual_case_rows": 3, "references": 66}
for item in content["input_files"]:
    assert sha(item["path"]) == item["sha256"], item["path"]

numeric_path = ROOT / "outputs/coding-revision-20261007-r3/manuscript-update-20261008/proxy-180-table2-binding-20261008/表2与五维κ_代理180权威绑定.json"
numeric = read(numeric_path)
assert numeric["checks_summary"]["all_pass"]
assert numeric["checks_summary"]["checks_n"] == 439
for item in numeric["input_bindings"]:
    assert sha(item["path"]) == item["sha256"], item["path"]

denominator_path = N / "method-difference-audit/分母与占比核查.json"
denominator = read(denominator_path)
assert denominator["status"] == "PASS_EXACT_AGGREGATE_DENOMINATOR_AUDIT"
assert denominator["check_count"] == 79

part1_paths = sorted((N / "visual-main-v6-part1").glob("*.json"))
assert len(part1_paths) == 1, "Need exactly one final v6 part1 report"
part1_path = part1_paths[0]
part2_path = N / "visual-main-v6-part2/视觉核查-第11至20页.json"
part1, part2 = read(part1_path), read(part2_path)

# Reports use their reviewer's own schema; both must name all assigned pages.
assert part1["document"]["sha256"] == sha(main)
assert part1["reviewed_pages"] == list(range(1, 11))
assert part1["actual_view_count"] == 10
assert part1["all_assigned_pages_actually_opened"]
assert not part1["prior_version_images_reused"]
assert part1["status"] == "PASS_VISUAL_SCOPE_PAGES_1_TO_10_ONLY"
assert part2["DOCX"]["sha256"] == sha(main)
assert part2["pages_actually_opened"] == list(range(11, 21))
assert not part2["blocking_findings"]

main_pngs = [N / f"render-main-v6/page-{i}.png" for i in range(1, 21)]
memo_pngs = [N / f"render-memo-v3/page-{i}.png" for i in range(1, 4)]
assert len(list((N / "render-main-v6").glob("page-*.png"))) == 20
assert len(list((N / "render-memo-v3").glob("page-*.png"))) == 3
root_visual = {
    "status": "PASS_ROOT_REVIEW_MEMO_ALL3_AND_MAIN9_TO11",
    "main": binding(main),
    "memo": binding(memo),
    "tool": "tools.view_image(detail=original)",
    "main_pages_actually_reviewed": [9, 10, 11],
    "memo_pages_actually_reviewed": [1, 2, 3],
    "memo_page_bindings": [binding(p) for p in memo_pngs],
    "main_page_bindings": [binding(main_pngs[i-1]) for i in [9, 10, 11]],
    "blocking_findings": [],
    "observations": ["Table3 now follows text on page9 after the legacy forced break was removed.", "Table4 spans pages11–12 with an intact repeated header; the part2 reviewer confirmed the fairness row and note on page12."],
    "scope": "Root inspection only; all other main pages are covered by the separately bound independent part1 and part2 reports.",
}
root_visual_path = N / "visual-final-root.json"
root_visual_path.write_text(json.dumps(root_visual, ensure_ascii=False, indent=2) + "\n")

freeze = {
    "status": "DELIVERY_QA_PASS_EXISTING_PROXY_RESULTS_FILLED_HUMAN_VALIDATION_PENDING",
    "date": "2026-10-08",
    "deliverables": [binding(main), binding(memo)],
    "counts": checks["counts"],
    "content_checks": binding(checks_path),
    "independent_content_review": binding(content_path),
    "numeric_binding_439_checks": binding(numeric_path),
    "denominator_audit_79_checks": binding(denominator_path),
    "actual_case_audit": binding(N / "method-difference-audit/当前两方法具体差异审计.json"),
    "official_policy_source_pack": binding(N / "policy-source-audit/政策建议官方证据包-20261008.json"),
    "visual_reports": [binding(part1_path), binding(part2_path), binding(root_visual_path)],
    "rendered_main": {"pages": [binding(p) for p in main_pngs], "pdf": binding(N / "render-main-v6/论文修订稿-编码实算结果版.pdf")},
    "rendered_memo": {"pages": [binding(p) for p in memo_pngs], "pdf": binding(N / "render-memo-v3/编码复核说明与真人检验事项.pdf")},
    "review_coverage": {"main": list(range(1, 21)), "memo": [1, 2, 3], "all_pages_actually_viewed_at_original_resolution": True},
    "result_identity": "Table2 has80 actual comparison values plus5 A/B kappa values from180 probability units reviewed by AI proxies. B aliases original C. These are development diagnostics, not the separate prospective240 real-human result.",
    "source_and_algorithm_mutation": {"reference_labels_changed": False, "machine_predictions_changed": False, "source_corpus_changed": False, "new_model_calls": 0, "new_bootstrap_run": False},
    "method_reference": {"reference_number": 44, "source": "Card et al.2015 The Media Frames Corpus Annotations of Frames Across Issues", "url": "https://aclanthology.org/P15-2072/", "supported_claim": "Overlapping frames motivate the adapted multi-label annotation design.", "not_attributed_to_source": "The five drug-policy dimensions, the attention share denominator, or Cohen kappa formulas."},
    "remaining": ["Receive genuine independent A/B first submissions and adjudication records, then recompute under the reserved240 sample design.", "Actual low agreement values and model errors remain; no universal0.80 publication guarantee or human validity certification is made.", "Author details, interview permissions and submission materials require the author's completion."],
    "previous_pending_templates": "Retained as historical versions; not the deliverables in this freeze.",
}
target = N / "final_freeze_actual.json"
target.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": freeze["status"], "freeze": str(target), "freeze_sha256": sha(target), "main_pages": 20, "memo_pages": 3}, ensure_ascii=False))
