"""Independent read-only integrity audit; outputs stay in audit-training only.

This audit verifies provenance and disclosure. It does not recode any item or
claim that lexical evidence checks establish a human semantic gold standard.
"""
from __future__ import annotations

import ast
import collections
import csv
import datetime
import hashlib
import json
import re
import unicodedata
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DIMS = ("S", "E", "Ec", "I", "F")
DIM_NAMES = dict(zip(DIMS, ("安全性", "有效性", "经济性", "创新性", "公平性")))
MATERIAL_VERSION = "v7"
USED: dict[str, str] = {}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(path: Path) -> Path:
    USED[str(path)] = sha(path)
    return path


def read(name: str):
    return json.loads(capture(RUN / name).read_text())


def jsonl(name: str):
    rows = [json.loads(line) for line in capture(RUN / name).read_text().splitlines() if line.strip()]
    assert len({r["id"] for r in rows}) == len(rows), name
    return {r["id"]: r for r in rows}


def csv_rows(name: str):
    with capture(RUN / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def source_texts(value):
    if isinstance(value, dict):
        return [v for k, v in value.items() if k == "text" and isinstance(v, str)] + [s for k, v in value.items() if k != "text" for s in source_texts(v)]
    if isinstance(value, list):
        return [s for v in value for s in source_texts(v)]
    return []


def normalize(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text) if not c.isspace() and not unicodedata.category(c).startswith("P"))


def walk(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield path + "." + key, key, item
            yield from walk(item, path + "." + key)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from walk(item, f"{path}[{i}]")


def main():
    units = jsonl(f"effective_blind_inputs_{MATERIAL_VERSION}.jsonl")
    rules = jsonl(f"rule_inputs_shared_{MATERIAL_VERSION}.jsonl")
    refs = jsonl("reference/adjudicated_candidate_reference.jsonl")
    agents = {coder: jsonl(f"reference/agent_{coder}_final_v6.jsonl") for coder in "AC"}
    design = read("admin/sampling_design.json")
    training = {r["original_id"]: r for r in design["sample"]}
    excluded = set(design["excluded_ids"])
    training_csv = csv_rows("真人培训候选判例-300条.csv")
    guide = capture(RUN / "真人五维编码培训依据.md").read_text()
    manual = capture(RUN / "protocol/完整五维手册-v1.3.md").read_text()
    operational = capture(RUN / "共用操作说明-v1.4.md").read_text()
    freeze = read("protocol/freeze.json")
    baseline = read("admin/baseline_hashes.json")
    binding = read("reference/training_guide_binding.json")
    checks = {}
    integrity_errors = []

    baseline_checks = [{"path": name, "expected_sha256": expected, "actual_sha256": sha(Path(name)), "matches": sha(Path(name)) == expected} for name, expected in baseline.items()]
    freeze_checks = [
        {"path": "protocol/完整五维手册-v1.3.md", "matches": sha(RUN / "protocol/完整五维手册-v1.3.md") == freeze["protocol_sha256"]},
        {"path": "共用操作说明-v1.4.md", "matches": sha(RUN / "共用操作说明-v1.4.md") == freeze["clarification_sha256"]},
        {"path": "admin/sampling_design.json", "matches": sha(RUN / "admin/sampling_design.json") == freeze["sampling_design_sha256"]},
    ] + [{"path": name, "matches": sha(RUN / name) == expected} for name, expected in freeze["packets"].items()]
    checks["immutable_hashes"] = {"baseline": baseline_checks, "freeze": freeze_checks, "all_match": all(x["matches"] for x in baseline_checks + freeze_checks)}
    assert checks["immutable_hashes"]["all_match"]

    checks["construct_continuity"] = {
        "status": "pass_by_document_review",
        "dimensions": DIM_NAMES,
        "manual_contains_all_dimensions": all(f"## {name} {d}" in manual for d, name in DIM_NAMES.items()),
        "operational_keeps_same_five_constructs": "保留安全性S、有效性E、经济性Ec、创新性I、公平性F五个构念" in operational,
        "guide_keeps_binary_multilabel_and_all_zero": "可多维同时为1，也可全部为0" in guide,
        "no_sixth_dimension": "不存在第六个" in guide,
        "semantic_review": "v1.4 continues the v1.3 constructs and clarifies current propositions, substantive innovation support, actual drug access and context inheritance; subtype labels remain provenance, not additional dimensions.",
    }
    assert set(refs) == set(training) == set(agents["A"]) == set(agents["C"])
    assert len(refs) == 300
    material_errors = []
    for rid in refs:
        if rules[rid]["input"]["unit_text"] != units[rid]["text"] or rules[rid]["input"]["llm_v29_shared_context"] != units[rid]["contexts"]:
            material_errors.append(rid)
    checks["material_consistency"] = {"latest_full_material": MATERIAL_VERSION, "A_C_last_supplemented_reference_material": "v6", "reference_units": 300, "rule_LLM_mismatches": material_errors}

    evidence = {}
    for source, rows in {**agents, "candidate_reference": refs}.items():
        errors = []
        total = context_count = positive_count = 0
        for rid, row in rows.items():
            if set(row["labels"]) != set(DIMS) or any(type(v) is not int or v not in (0, 1) for v in row["labels"].values()):
                errors.append({"id": rid, "type": "nonbinary_or_missing_dimension"})
            positive_count += sum(row["labels"].values())
            for item in row["evidence"]:
                total += 1
                context_count += item["source"] == "context"
                corpus = [units[rid]["text"]] if item["source"] == "unit" else source_texts(units[rid]["contexts"]) if item["source"] == "context" else []
                if item["dimension"] not in DIMS or row["labels"][item["dimension"]] != 1 or not item["quote"] or not any(item["quote"] in s for s in corpus):
                    errors.append({"id": rid, "type": "evidence_not_supported", "evidence": item})
            for dim, label in row["labels"].items():
                if not row["dimension_reasons"].get(dim):
                    errors.append({"id": rid, "type": "missing_reason", "dimension": dim})
                if label and not any(e["dimension"] == dim and e["source"] == "unit" for e in row["evidence"]):
                    errors.append({"id": rid, "type": "missing_current_unit_evidence", "dimension": dim})
            for dim, key, allowed in [("I", "innovation_subtypes", {"attribute", "research_support", "qualification_advantage"}), ("F", "fairness_subtypes", {"access", "affordability", "clinical_management", "dimension_information"})]:
                if bool(row[key]) != bool(row["labels"][dim]) or not set(row[key]) <= allowed:
                    errors.append({"id": rid, "type": "subtype_mismatch", "dimension": dim})
        evidence[source] = {"n": len(rows), "positive_labels": positive_count, "evidence_quotes": total, "context_quotes": context_count, "errors": errors}
        integrity_errors += errors
    checks["evidence"] = evidence

    mapping = {r["blind_id"]: r for r in read("admin/adjudication_mapping_PRIVATE.json")}
    adjudications = {}
    adjudication_errors = []
    for packet_n in range(1, 4):
        packet_path = RUN / f"adjudication/材料-{packet_n:02d}.json"
        packet = read(str(packet_path.relative_to(RUN)))
        result = read(f"adjudication/结果-{packet_n:02d}.json")
        if result["input_packet_sha256"] != sha(packet_path) or result["reviewer"] != "independent_AI_adjudicator":
            adjudication_errors.append({"packet": packet_n, "type": "binding"})
        for row in packet["rows"]:
            rid = mapping[row["id"]]["original_id"]
            for key in ("text", "source_title", "pages", "contexts"):
                if row[key] != units[rid][key]:
                    adjudication_errors.append({"id": rid, "type": "packet_material", "field": key})
            for coder in "AC":
                for key in ("labels", "dimension_reasons", "evidence", "innovation_subtypes", "fairness_subtypes"):
                    if row["first_judgments"][coder][key] != agents[coder][rid][key]:
                        adjudication_errors.append({"id": rid, "coder": coder, "type": "provided_A_C", "field": key})
        for row in result["rows"]:
            adjudications[mapping[row["id"]]["original_id"]] = row
    disagreements = {rid for rid in refs if agents["A"][rid]["labels"] != agents["C"][rid]["labels"]}
    assert disagreements == {r["original_id"] for r in mapping.values() if r["selection"] == "disagreement"}
    for rid, row in refs.items():
        expected_origin = "third_agent_disagreement_adjudication" if rid in disagreements else "third_agent_agreement_audit" if rid in adjudications else "A_C_agreement_not_third_audited"
        if row["reference_origin"] != expected_origin:
            adjudication_errors.append({"id": rid, "type": "origin"})
        source_row = adjudications.get(rid, agents["A"][rid])
        for key in ("labels", "dimension_reasons", "evidence", "innovation_subtypes", "fairness_subtypes", "safety_quality_basis", "issues"):
            if row[key] != source_row[key]:
                adjudication_errors.append({"id": rid, "type": "candidate_source", "field": key})
        if row["human_gold_standard"] is not False:
            adjudication_errors.append({"id": rid, "type": "human_gold_claim"})
    checks["adjudication_provenance"] = {"disagreements": len(disagreements), "random_agreement_audits": 24, "third_agent_reviewed": len(adjudications), "remaining_A_C_agreements": 257, "origins": dict(collections.Counter(r["reference_origin"] for r in refs.values())), "errors": adjudication_errors}
    integrity_errors += adjudication_errors

    csv_errors = []
    for row in training_csv:
        rid = row["原单元编号"]
        reference, unit = refs[rid], units[rid]
        values = {"样本用途": training[rid]["component"], "部门": training[rid]["group"], "政策原文": unit["text"], "来源标题": unit["source_title"], "页码": json.dumps(unit["pages"], ensure_ascii=False), "逐字证据JSON": json.dumps(reference["evidence"], ensure_ascii=False), "I子类": "|".join(reference["innovation_subtypes"]), "F子类": "|".join(reference["fairness_subtypes"]), "A首次同材五维": json.dumps(agents["A"][rid]["labels"], ensure_ascii=False), "C首次同材五维": json.dumps(agents["C"][rid]["labels"], ensure_ascii=False), "裁决来源": reference["reference_origin"], "裁决理由": reference["adjudication_reason"], "待真人复审问题": json.dumps(reference["issues"], ensure_ascii=False)}
        for dim, name in DIM_NAMES.items():
            values[dim + name] = str(reference["labels"][dim])
            values[dim + "理由"] = reference["dimension_reasons"][dim]
        csv_errors += [{"id": rid, "field": key} for key, value in values.items() if row[key] != value]
    guide_errors = []
    cases = re.split(r"### 判例(\d+)：(RECODE25-\d+)", guide)
    for index in range(1, len(cases), 3):
        _, rid, body = cases[index:index + 3]
        if re.search(r"^> (.*)$", body, re.M).group(1) != units[rid]["text"]:
            guide_errors.append({"id": rid, "type": "guide_quote"})
        labels = re.search(r"候选五维：(.*)", body).group(1)
        for dim, name in DIM_NAMES.items():
            if int(re.search(name + r"=(\d)", labels).group(1)) != refs[rid]["labels"][dim]:
                guide_errors.append({"id": rid, "type": "guide_label", "dimension": dim})
            if refs[rid]["dimension_reasons"][dim] not in body:
                guide_errors.append({"id": rid, "type": "guide_reason", "dimension": dim})
        left, right = re.search(r"A：(\{.*?\})；C：(\{.*?\})。", body).groups()
        if ast.literal_eval(left) != agents["A"][rid]["labels"] or ast.literal_eval(right) != agents["C"][rid]["labels"]:
            guide_errors.append({"id": rid, "type": "guide_A_C"})
        if re.search(r"裁决或共识依据：(.*)", body).group(1) != refs[rid]["adjudication_reason"]:
            guide_errors.append({"id": rid, "type": "guide_adjudication"})
    checks["training_exports"] = {"CSV_rows": len(training_csv), "CSV_errors": csv_errors, "guide_cases": (len(cases) - 1) // 3, "guide_errors": guide_errors, "binding_hashes_match": all(sha(RUN / fn) == binding[field] for fn, field in [("reference/adjudicated_candidate_reference.jsonl", "reference_sha256"), ("真人培训候选判例-300条.csv", "training_csv_sha256"), ("真人五维编码培训依据.md", "guide_sha256")])}
    integrity_errors += csv_errors + guide_errors
    flags = [{"id": rid, **issue} for rid, row in refs.items() for issue in row["issues"] if isinstance(issue, dict) and issue.get("type") == "needs_human_review"]
    checks["human_review_disclosure"] = {"flags": flags, "expected_three_ids": ["RECODE25-00105", "RECODE25-01059", "RECODE25-03523"], "all_in_guide_verbatim": all(flag["detail"] in guide and flag["id"] in guide for flag in flags), "count": len(flags)}
    assert {flag["id"] for flag in flags} == set(checks["human_review_disclosure"]["expected_three_ids"])
    checks["claims"] = {"status": "pass_by_document_review", "guide_explicit_agent_identity": "所有执行者均为agent" in guide, "guide_not_completed_human_validation": "这不是已完成的真人验证" in guide, "guide_not_immutable_gold": "也不是不可修订的人工金标准" in guide, "freeze_human_validation_completed": freeze["human_validation_completed"], "freeze_publication_threshold_claim": freeze["targets_are_universal_publication_thresholds"], "training_can_be_revised_by_humans": "真人可以修正agent候选标准" in guide, "learning_cases_excluded_from_future_formal_test_instruction": "学习后不得再把这批材料作为本人的未接触正式验证样本" in guide}

    future = read("admin/future_human_sampling_PRIVATE.json")
    future_ids = {r["original_id"] for r in future["sample"]}
    future_map = {(r["coder"], r["blind_id"]): r["original_id"] for r in future["mapping"]}
    future_errors = []
    future_rows = {}
    blank_fields = [*DIMS, *(d + "理由" for d in DIMS), "逐字证据", "I来源类型", "F来源类型", "问题说明"]
    suspicious_keys = []
    for coder in "AC":
        packet = read(f"future-human-validation/真人{coder}-无答案材料.json")
        table = csv_rows(f"future-human-validation/真人{coder}-空白编码表.csv")
        future_rows[coder] = [future_map[coder, row["id"]] for row in packet["rows"]]
        if any(packet[k] != "" for k in ("coder_name", "professional_background", "execution_date")):
            future_errors.append({"coder": coder, "type": "prefilled_identity"})
        if len(packet["rows"]) != 240 or len(table) != 240:
            future_errors.append({"coder": coder, "type": "row_count"})
        for row, cells in zip(packet["rows"], table):
            rid = future_map[coder, row["id"]]
            if any(row[k] != units[rid][k] for k in ("text", "source_title", "pages", "contexts")):
                future_errors.append({"coder": coder, "id": rid, "type": "latest_material_mismatch"})
            if any(cells[k] != "" for k in blank_fields):
                future_errors.append({"coder": coder, "id": rid, "type": "prefilled_answers"})
            if cells["匿名编号"] != row["id"] or cells["政策原文"] != row["text"] or cells["来源标题"] != row["source_title"] or json.loads(cells["页码"]) != row["pages"] or json.loads(cells["完整语境JSON"]) != row["contexts"]:
                future_errors.append({"coder": coder, "id": rid, "type": "JSON_CSV_mismatch"})
        for path, key, value in walk(packet):
            if re.search(r"label|prediction|gold|judgment|reason|answer|adjudicat|expected|subtype|quality_basis", key, re.I):
                suspicious_keys.append({"coder": coder, "path": path})
    checks["future_original_blank_package"] = {"rows_per_coder": {c: len(v) for c, v in future_rows.items()}, "original_id_overlap_with_training": sorted(future_ids & set(refs)), "original_id_overlap_with_known_development": sorted(future_ids & excluded), "A_C_same_material_ids": set(future_rows["A"]) == set(future_rows["C"]) == future_ids, "A_C_different_order": future_rows["A"] != future_rows["C"], "all_answer_and_identity_fields_blank": not future_errors, "suspicious_answer_keys": suspicious_keys, "errors": future_errors, "generic_context_usage_instructions": "Supplied context retains generic source/object and non-inheritance instructions; no item-level answer labels, reasons, predictions, subtype answers or expected judgments were found.", "status": "do_not_use_as_strict_text_unseen_human_holdout_due_to_overlap_below"}
    integrity_errors += future_errors + suspicious_keys

    def overlap(left_ids, right_ids, mode):
        transform = (lambda s: s) if mode == "exact" else normalize
        right = collections.defaultdict(list)
        for rid in sorted(right_ids):
            if rid in units:
                right[transform(units[rid]["text"])].append(rid)
        return [{"training_id" if left_ids == set(training) else "future_id": rid, "component": training[rid]["component"] if rid in training else "future_human_validation_original", "group": training[rid]["group"] if rid in training else next(r["group"] for r in future["sample"] if r["original_id"] == rid), "development_ids" if right_ids == excluded else "training_ids": right[transform(units[rid]["text"])], "text": units[rid]["text"]} for rid in sorted(left_ids) if transform(units[rid]["text"]) in right]

    current_dev = overlap(set(training), excluded, "normalized")
    future_train_exact = overlap(future_ids, set(training), "exact")
    future_train = overlap(future_ids, set(training), "normalized")
    future_dev = overlap(future_ids, excluded, "normalized")
    future_families = collections.defaultdict(list)
    for rid in sorted(future_ids):
        future_families[normalize(units[rid]["text"])].append(rid)
    checks["text_overlap"] = {
        "normalization": "unicodedata.normalize('NFKC', text), remove all Unicode whitespace and all Unicode category P* punctuation; no semantic paraphrase or fuzzy matching",
        "current_training_vs_known_development": {"original_id_overlap": sorted(set(training) & excluded), "normalized_overlap_n": len(current_dev), "by_component": dict(collections.Counter(r["component"] for r in current_dev)), "by_department": dict(collections.Counter(r["group"] for r in current_dev)), "normalized_matches": current_dev},
        "future_original_vs_current_training": {"exact_overlap_n": len(future_train_exact), "normalized_overlap_n": len(future_train), "exact_matches": future_train_exact, "normalized_matches": future_train},
        "future_original_vs_known_development": {"normalized_overlap_n": len(future_dev), "normalized_matches": future_dev},
        "future_original_union_known_or_training_overlap_n": len({r["future_id"] for r in future_train + future_dev}),
        "future_original_internal_duplicate_families": [ids for ids in future_families.values() if len(ids) > 1],
    }
    checks["source_snapshot_unchanged_during_audit"] = all(sha(Path(name)) == expected for name, expected in USED.items())
    result = {
        "audit": "Independent training/reference/holdout integrity QA",
        "auditor": "independent_AI_agent_training_integrity_audit",
        "created_at": datetime.datetime.now().astimezone().isoformat(),
        "status": "integrity_checks_pass_with_material_human_holdout_overlap_issue_and_scope_limitations",
        "reference_material_version": "A/C v6 final supplemented submissions; original first outputs remain separately preserved",
        "full_machine_material_version_at_audit": MATERIAL_VERSION,
        "scope": "No labels, originals, protocol, training exports, future original packages or paper files were altered. Only audit-training outputs are written. No LLM inference is launched.",
        "checks": checks,
        "integrity_errors": integrity_errors,
        "material_findings": [
            {"severity": "material", "code": "FUTURE_ORIGINAL_PACKAGE_TEXT_OVERLAP", "detail": "The old 240-case package is disjoint by unit ID, but 6 future texts exactly repeat current training text; 9 do so after normalization. 17 future texts normalize to known-development text, with 23 cases in the union. It cannot support an unqualified claim of text-unseen formal human validation."},
            {"severity": "scope", "code": "CURRENT_CONFIRMATION_ID_HOLDOUT_NOT_TEXT_HOLDOUT", "detail": "20 current training/confirmation cases normalize to known-development text (18 probability, 2 challenge; all NHSA). This is disclosure and sensitivity information, not grounds to change any code or silently discard cases."},
            {"severity": "pending_source_update", "code": "V8_SOURCE_COMPLETION_PENDING", "detail": "The root source review reports planned v8 scope/parent additions affecting 4155/4156/4165/4167 within the 300. This v7 snapshot verifies provenance and verbatim evidence in supplied material; re-audit updated material and any new independent submissions before final delivery."},
        ],
        "limits": [
            "The audit checks all 300 records and all supplied evidence quotes against current-unit text or actual context text fields, excluding explanatory metadata as source evidence. It does not replace human semantic adjudication or independently reread every original PDF.",
            "The three needs_human_review boundaries remain candidate judgments, with their exact scope and reasoning disclosed in the guide and CSV.",
            "Training CSV contains context evidence excerpts rather than every complete context object. Teaching with that CSV should also allow same-version full material/source lookup when the excerpt cannot resolve a question.",
            "Literal and normalized duplication is a lower bound on textual contact; near-duplicate annual clauses and shared surrounding paragraphs were not semantically deduplicated.",
        ],
        "source_sha256": USED,
    }
    assert not integrity_errors, integrity_errors
    assert checks["source_snapshot_unchanged_during_audit"]
    OUT.mkdir(exist_ok=True)
    (OUT / "独立培训材料QA.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    note = """# 培训材料独立审计（v7材料快照）

300条候选判例的CSV、A/C v6最终补料提交、43条第三agent裁决/抽查来源和24个指南展示判例相互一致。A的241条证据、C的259条证据、候选参照的240条证据全部逐字出现在当前单元或已给原文语境中；每个1均有当前单元证据。五维名称、二元多标签含义和来源子类型连续，未将agent预验证虚称为真人金标准或发表达标。

三条待真人复核边界完整保留：00105儿童规格适用与获取缺口（F）、01059政府定价制度适用关系（Ec）、03523试验风险监测与临床管理难度（F）。旧产物5项SHA、手册/说明/抽样与20份初始封存材料SHA均匹配。

原未来240条的两份CSV均全空，姓名/专业经历/日期均空，两位材料内容及语境一致且顺序不同，正文与v7同材一致。但“无相同ID”不等于“未接触相同正文”：其中6条正文逐字重复培训判例，规范化后9条重复培训、17条重复历史开发，合计23条；包内另有一对相同正文。因此原未来包不能作为严格正文未接触的真人留出包，应保留归档并用另行冻结的v2替代。未改动该包或任何标签。

当前300本身也有20条正文与已登记开发单元规范化重复，其中概率部分18条、挑战部分2条，均属医保。原概率样本和评分应保留，正文接触限制须披露，并可另报排除重复的诊断敏感性；不得据此回改编码。

本次以v7全量机器材料为快照，A/C最后补料参照仍为v6。源审计正在追加v8适用范围/父条件，其中培训集4条受影响；本报告尚未核验v8或新独立复核结果。逐字与来源核验不等于完成每条政策PDF的独立语义重判，也不构成真人效度结论。完整逐项计数、重复对应ID和源SHA见同目录JSON。
"""
    (OUT / "独立培训材料QA.md").write_text(note)
    print(json.dumps({"status": result["status"], "integrity_errors": len(integrity_errors), "current_development_text_overlaps": len(current_dev), "future_original_training_text_overlaps": len(future_train), "future_original_known_text_overlaps": len(future_dev), "output": str(OUT / "独立培训材料QA.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
