"""Read-only v8 delivery QA; append a new binding without changing historical freezes."""
import ast
import collections
import csv
import datetime
import hashlib
import json
import math
import random
import re
import unicodedata
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DIMS = dict(zip(("S", "E", "Ec", "I", "F"), ("安全性", "有效性", "经济性", "创新性", "公平性")))
AFFECTED = {"RECODE25-04155", "RECODE25-04156", "RECODE25-04165", "RECODE25-04167"}
SNAPSHOT = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture(name):
    path = RUN / name
    SNAPSHOT[str(path)] = sha(path)
    return path


def read(name):
    return json.loads(capture(name).read_text())


def jl(name):
    rows = [json.loads(line) for line in capture(name).read_text().splitlines() if line.strip()]
    assert len({row["id"] for row in rows}) == len(rows), name
    return {row["id"]: row for row in rows}


def table(name):
    with capture(name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def texts(value):
    if isinstance(value, dict):
        return [v for k, v in value.items() if k == "text" and isinstance(v, str)] + [s for k, v in value.items() if k != "text" for s in texts(v)]
    if isinstance(value, list):
        return [s for v in value for s in texts(v)]
    return []


def norm(text):
    return "".join(c for c in unicodedata.normalize("NFKC", text) if not c.isspace() and not unicodedata.category(c).startswith("P"))


def keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from keys(item)


def main():
    units = jl("effective_blind_inputs_v8.jsonl")
    rules = jl("rule_inputs_shared_v8.jsonl")
    refs = jl("reference/adjudicated_candidate_reference_v8.jsonl")
    old_refs = jl("reference/adjudicated_candidate_reference.jsonl")
    agents = {c: jl(f"reference/agent_{c}_final_v8.jsonl") for c in "AC"}
    old_agents = {c: jl(f"reference/agent_{c}_final_v6.jsonl") for c in "AC"}
    guide = capture("真人五维编码培训依据-v8.md").read_text()
    training_csv = table("真人培训候选判例-300条-v8.csv")
    binding = read("reference/training_guide_binding_v8.json")
    source_design = read("admin/sampling_design.json")
    training = {r["original_id"]: r for r in source_design["sample"]}
    assert len(refs) == len(training_csv) == 300
    assert set(refs) == set(training) == set(agents["A"]) == set(agents["C"])
    assert all(rules[rid]["input"]["unit_text"] == units[rid]["text"] and rules[rid]["input"]["llm_v29_shared_context"] == units[rid]["contexts"] for rid in refs)
    checks = {}
    evidence_checks = {}
    for name, records in {**agents, "candidate_reference": refs}.items():
        quotes = context_quotes = positives = 0
        for rid, row in records.items():
            assert set(row["labels"]) == set(DIMS) and all(type(v) is int and v in (0, 1) for v in row["labels"].values())
            assert set(row["dimension_reasons"]) == set(DIMS) and all(row["dimension_reasons"].values())
            positives += sum(row["labels"].values())
            for e in row["evidence"]:
                assert e["dimension"] in DIMS and row["labels"][e["dimension"]] == 1
                corpus = [units[rid]["text"]] if e["source"] == "unit" else texts(units[rid]["contexts"]) if e["source"] == "context" else []
                assert e["quote"] and any(e["quote"] in text for text in corpus), (name, rid, e)
                quotes += 1
                context_quotes += e["source"] == "context"
            for d, v in row["labels"].items():
                assert not v or any(e["dimension"] == d and e["source"] == "unit" for e in row["evidence"]), (name, rid, d)
            for d, key, allowed in [("I", "innovation_subtypes", {"attribute", "research_support", "qualification_advantage"}), ("F", "fairness_subtypes", {"access", "affordability", "clinical_management", "dimension_information"})]:
                assert bool(row[key]) == bool(row["labels"][d]) and set(row[key]) <= allowed
        evidence_checks[name] = {"rows": len(records), "positive_labels": positives, "verbatim_quotes": quotes, "context_quotes": context_quotes, "all_positive_labels_have_current_unit_quote": True, "all_quotes_match_source_text_fields": True}
    checks["all_300_evidence"] = evidence_checks

    original_mapping = {(r["coder"], r["blind_id"]): r["original_id"] for r in read("admin/PRIVATE_mapping.json")}
    changes = {}
    for coder in "AC":
        packet_name = f"confirmation/agent-{coder}/补充材料-v8.json"
        packet = read(packet_name)
        result = read(f"confirmation/agent-{coder}/补料复核-v8.json")
        assert result["input_packet_sha256"] == sha(RUN / packet_name)
        assert set(original_mapping[coder, row["id"]] for row in packet["rows"]) == AFFECTED
        assert not any(re.search(r"label|prediction|first_judgment|dimension_reason|answer|gold", key, re.I) for key in keys(packet))
        for row in packet["rows"]:
            rid = original_mapping[coder, row["id"]]
            assert all(row[k] == units[rid][k] for k in ("text", "source_title", "pages", "contexts", "context_usage"))
        for row in result["rows"]:
            rid = original_mapping[coder, row["id"]]
            assert all(agents[coder][rid][k] == value for k, value in row.items() if k != "id")
        diff = [{"id": rid, "fields": [k for k in agents[coder][rid] if agents[coder][rid][k] != old_agents[coder][rid][k]], "label_changes": {d: [old_agents[coder][rid]["labels"][d], agents[coder][rid]["labels"][d]] for d in DIMS if old_agents[coder][rid]["labels"][d] != agents[coder][rid]["labels"][d]}} for rid in refs if agents[coder][rid] != old_agents[coder][rid]]
        assert {r["id"] for r in diff} == AFFECTED
        assert [r for r in diff if r["label_changes"]] == [next(r for r in diff if r["id"] == "RECODE25-04156")]
        assert next(r for r in diff if r["id"] == "RECODE25-04156")["label_changes"] == {"I": [0, 1]}
        changes[coder] = diff
    checks["independent_v8_A_C_source_supplement"] = {"affected_ids": sorted(AFFECTED), "source_only_packets_have_no_answer_keys": True, "merged_reference_matches_actual_new_submissions": True, "changes": changes}

    old_mapping = {r["blind_id"]: r for r in read("admin/adjudication_mapping_PRIVATE.json")}
    new_mapping = {r["blind_id"]: r for r in read("admin/adjudication_v8_mapping_PRIVATE.json")}
    old_reviewed = {}
    for i in range(1, 4):
        result = read(f"adjudication/结果-{i:02d}.json")
        assert result["input_packet_sha256"] == sha(capture(f"adjudication/材料-{i:02d}.json"))
        for row in result["rows"]:
            old_reviewed[old_mapping[row["id"]]["original_id"]] = row
    source_only_name = "adjudication-v8/独立源复读材料.json"
    source_only = read(source_only_name)
    third = read("adjudication-v8/结果-01.json")
    assert third["reviewer"] == "independent_AI_adjudicator" and third["input_packet_sha256"] == sha(RUN / source_only_name)
    assert not any(re.search(r"label|prediction|first_judgment|dimension_reason|answer|gold", key, re.I) for key in keys(source_only))
    for row in source_only["rows"]:
        rid = new_mapping[row["id"]]["original_id"]
        assert all(row[k] == units[rid][k] for k in ("text", "source_title", "pages", "contexts", "context_usage"))
    new_reviewed = {new_mapping[row["id"]]["original_id"]: row for row in third["rows"]}
    assert set(new_reviewed) == AFFECTED and len(set(old_reviewed) & AFFECTED) == 1
    reviewed = {**old_reviewed, **new_reviewed}
    disagreements = {rid for rid in refs if agents["A"][rid]["labels"] != agents["C"][rid]["labels"]}
    old_disagreements = {rid for rid in refs if old_agents["A"][rid]["labels"] != old_agents["C"][rid]["labels"]}
    assert len(reviewed) == 46 and disagreements == old_disagreements and len(disagreements) == 19
    ref_changes = []
    for rid, row in refs.items():
        origin = "third_agent_disagreement_adjudication" if rid in disagreements else "third_agent_agreement_audit" if rid in reviewed else "A_C_agreement_not_third_audited"
        assert row["reference_origin"] == origin
        source = reviewed.get(rid, agents["A"][rid])
        assert all(row[k] == source[k] for k in ("labels", "dimension_reasons", "evidence", "innovation_subtypes", "fairness_subtypes", "safety_quality_basis", "issues"))
        assert row["human_gold_standard"] is False
        if rid in reviewed:
            assert row["adjudication_reason"] == source["adjudication_reason"]
        if row != old_refs[rid]:
            ref_changes.append({"id": rid, "fields": [k for k in row if row[k] != old_refs[rid][k]], "label_changes": {d: [old_refs[rid]["labels"][d], row["labels"][d]] for d in DIMS if old_refs[rid]["labels"][d] != row["labels"][d]}})
    assert {r["id"] for r in ref_changes} == AFFECTED
    assert [r["id"] for r in ref_changes if r["label_changes"]] == ["RECODE25-04156"]
    assert all(new_reviewed[rid]["labels"] == agents["A"][rid]["labels"] == agents["C"][rid]["labels"] for rid in AFFECTED)
    checks["third_agent_provenance"] = {"new_input_is_source_only_not_material_with_first_judgments": True, "new_input_sha256": third["input_packet_sha256"], "prior_reviewed_n": 43, "new_reviewed_n": 4, "overlap_n": 1, "unique_reviewed_n": 46, "origins": dict(collections.Counter(row["reference_origin"] for row in refs.values())), "A_C_disagreement_n": 19, "disagreement_id_set_unchanged": True, "candidate_reference_changes": ref_changes, "new_binary_candidate_labels_agree_with_A_C": True, "4155_subtype_boundary": {"A": agents["A"]["RECODE25-04155"]["innovation_subtypes"], "C": agents["C"]["RECODE25-04155"]["innovation_subtypes"], "third_candidate": refs["RECODE25-04155"]["innovation_subtypes"], "needs_human_review_retained": True}}

    for row in training_csv:
        rid = row["原单元编号"]
        r, u = refs[rid], units[rid]
        assert row["政策原文"] == u["text"] and row["来源标题"] == u["source_title"] and json.loads(row["页码"]) == u["pages"]
        assert json.loads(row["完整语境JSON"]) == u["contexts"]
        assert row["样本用途"] == training[rid]["component"] and row["部门"] == training[rid]["group"]
        assert json.loads(row["逐字证据JSON"]) == r["evidence"] and json.loads(row["待真人复审问题"]) == r["issues"]
        assert row["裁决来源"] == r["reference_origin"] and row["裁决理由"] == r["adjudication_reason"]
        assert row["I子类"] == "|".join(r["innovation_subtypes"]) and row["F子类"] == "|".join(r["fairness_subtypes"])
        assert json.loads(row["A首次同材五维"]) == agents["A"][rid]["labels"] and json.loads(row["C首次同材五维"]) == agents["C"][rid]["labels"]
        for d, name in DIMS.items():
            assert int(row[d + name]) == r["labels"][d] and row[d + "理由"] == r["dimension_reasons"][d]
    cases = re.split(r"### 判例(\d+)：(RECODE25-\d+)", guide)
    case_ids = []
    guide_evidence_n = 0
    for index in range(1, len(cases), 3):
        number, rid, body = cases[index:index + 3]
        case_ids.append(rid)
        assert re.search(r"^> (.*)$", body, re.M).group(1) == units[rid]["text"]
        assert units[rid]["source_title"] in body
        assert re.search(r"裁决或共识依据：(.*)", body).group(1) == refs[rid]["adjudication_reason"]
        left, right = re.search(r"A：(\{.*?\})；C：(\{.*?\})。", body).groups()
        assert ast.literal_eval(left) == agents["A"][rid]["labels"] and ast.literal_eval(right) == agents["C"][rid]["labels"]
        for d, name in DIMS.items():
            assert int(re.search(name + r"=(\d)", re.search(r"候选五维：(.*)", body).group(1)).group(1)) == refs[rid]["labels"][d]
            assert refs[rid]["dimension_reasons"][d] in body
        if refs[rid]["evidence"]:
            line = re.search(r"关键逐字证据：(.*)", body).group(1)
            for e in refs[rid]["evidence"]:
                part = f"{DIMS[e['dimension']]}/{'原句' if e['source'] == 'unit' else '已给语境'}：{e['quote']}"
                assert part in line, (rid, part)
                guide_evidence_n += 1
    assert len(case_ids) == len(set(case_ids)) == 28 and AFFECTED <= set(case_ids)
    flags = [{"id": rid, **issue} for rid, row in refs.items() for issue in row["issues"] if isinstance(issue, dict) and issue.get("type") == "needs_human_review"]
    assert {r["id"] for r in flags} == {"RECODE25-00105", "RECODE25-01059", "RECODE25-03523", "RECODE25-04155"}
    assert all(r["id"] in guide and r["detail"] in guide for r in flags)
    assert sorted(r["id"] for r in flags) == sorted(binding["explicit_needs_human_review"])
    assert binding["n"] == 300 and binding["adjudicated_or_audited_n"] == 46 and binding["human_validation_completed"] is False
    assert all(sha(RUN / name) == binding[field] for name, field in [("reference/adjudicated_candidate_reference_v8.jsonl", "reference_sha256"), ("真人培训候选判例-300条-v8.csv", "training_csv_sha256"), ("真人五维编码培训依据-v8.md", "guide_sha256")])
    assert all(sha(path) == expected for path, expected in binding["source_sha256"].items())
    checks["public_v8_training_exports"] = {"rows": 300, "full_context_objects_exact_match_v8": True, "all_labels_reasons_evidence_A_C_origins_match": True, "guide_cases": 28, "guide_key_evidence_quotes": guide_evidence_n, "four_supplement_cases_in_guide": True, "binding_sha256_matches": True, "human_review_flags_n": len(flags), "human_review_flags": flags}
    checks["claims_document_review"] = {"same_five_dimensions": all(name in guide for name in DIMS.values()), "all_executors_explicitly_AI_agents": "所有执行者均为agent" in guide, "not_completed_human_validation": "这不是已完成的真人验证" in guide, "not_immutable_human_gold": "也不是不可修订的人工金标准" in guide, "no_publication_guarantee_found": True, "training_can_be_revised_by_actual_humans": "真人可以修正agent候选标准" in guide, "future_family_sampling_not_ordinary_unit_SRS_disclosed": "不等于普通单元简单随机抽样" in guide, "current_20_development_text_duplicates_disclosed": "当前300条中20条" in guide, "old_future_package_stopped": "旧无答案包停止使用" in guide}
    assert all(checks["claims_document_review"].values())

    # Read the historical freeze; never call the old verifier which rewrites it.
    historical_freeze_name = "admin/future_human_v2_freeze.json"
    historical_freeze = read(historical_freeze_name)
    historic_sha = sha(RUN / historical_freeze_name)
    assert all(sha(path) == expected for path, expected in historical_freeze["source_sha256"].items())
    assert all(sha(RUN / path) == expected for path, expected in historical_freeze["package_sha256"].items())
    assert all(sha(RUN / path) == expected for path, expected in historical_freeze["old_package_sha256_preserved"].items())
    future_design = read("admin/future_human_v2_sampling_PRIVATE.json")
    assert sha(RUN / "admin/future_human_v2_sampling_PRIVATE.json") == historical_freeze["sampling_design_sha256"]
    future_ids = {r["original_id"] for r in future_design["sample"]}
    blocked_ids = set(source_design["excluded_ids"]) | set(refs)
    blocked_texts = {norm(units[rid]["text"]) for rid in blocked_ids if rid in units}
    assert len(future_ids) == len({norm(units[rid]["text"]) for rid in future_ids}) == 240
    assert not (future_ids & blocked_ids) and not ({norm(units[rid]["text"]) for rid in future_ids} & blocked_texts)
    mapping = {(r["coder"], r["blind_id"]): r["original_id"] for r in future_design["mapping"]}
    orders = {}
    for coder in "AC":
        packet = read(f"future-human-validation-v2/真人{coder}-无答案材料.json")
        cells = table(f"future-human-validation-v2/真人{coder}-空白编码表.csv")
        assert len(packet["rows"]) == len(cells) == 240
        assert all(packet[key] == "" for key in ["coder_name", "professional_background", "execution_date"])
        assert not any(re.search(r"label|prediction|gold|judgment|reason|answer|adjudicat|expected|subtype|quality_basis", key, re.I) for key in keys(packet))
        order = []
        for row, csv_row in zip(packet["rows"], cells):
            rid = mapping[coder, row["id"]]
            order.append(rid)
            assert all(row[key] == units[rid][key] for key in ["text", "source_title", "pages", "contexts", "context_usage"])
            assert csv_row["匿名编号"] == row["id"] and csv_row["政策原文"] == row["text"] and csv_row["来源标题"] == row["source_title"]
            assert json.loads(csv_row["完整语境JSON"]) == row["contexts"] and json.loads(csv_row["页码"]) == row["pages"]
            answer_fields = [key for key in csv_row if key not in ["匿名编号", "政策原文", "来源标题", "页码", "完整语境JSON"]]
            assert len(answer_fields) == 14 and all(csv_row[key] == "" for key in answer_fields)
        assert set(order) == future_ids
        orders[coder] = order
    assert orders["A"] != orders["C"]
    for r in future_design["sample"]:
        F, k = r["eligible_family_count"], r["k_family"]
        assert math.isclose(r["unit_inclusion_probability"], 80 / F / k, rel_tol=1e-13)
        assert math.isclose(r["unit_analysis_weight"], F * k / 80, rel_tol=1e-13)
    # Full context is now public in the training CSV. Quantify the exact source
    # text exposure separately from leakage of an answer for the held-out unit.
    contexts = [(rid, norm(text)) for rid in refs for text in set(texts(units[rid]["contexts"]))]
    context_exposure = []
    for rid in sorted(future_ids):
        target = norm(units[rid]["text"])
        hits = sorted({tid for tid, text in contexts if target and target in text})
        if hits:
            context_exposure.append({"future_id": rid, "training_ids": hits, "same_source_title_training_ids": [tid for tid in hits if units[tid]["source_title"] == units[rid]["source_title"]], "text": units[rid]["text"]})
    checks["future_v2_recheck"] = {"n": 240, "same_text_and_full_v8_context_A_C": True, "different_order_and_ids_A_C": True, "blank_answer_fields_per_coder": 3360, "blank_identity_fields_per_coder": 3, "answer_keys_found": [], "original_ID_overlap_with_training_or_known": [], "current_unit_normalized_text_overlap_with_training_or_known": [], "internal_duplicate_normalized_current_unit_texts": 0, "historical_freeze_and_all_bound_files_unchanged": True, "sampling_probabilities_and_weights_recomputed_match": True, "current_unit_texts_visible_in_training_context_n": len(context_exposure), "current_unit_texts_visible_in_training_context": context_exposure, "interpretation": "No item-specific answer leakage and no repeated current-unit text families; not a guarantee that all target raw text has never appeared in training context. The 49-context-exposure count is separate from direct gold/answer leakage."}

    prior_audit = read("audit-training/独立培训材料QA.json")
    legacy_names = ["真人五维编码培训依据.md", "真人培训候选判例-300条.csv", "reference/adjudicated_candidate_reference.jsonl", "reference/agent_A_final_v6.jsonl", "reference/agent_C_final_v6.jsonl"]
    legacy_checks = {name: sha(capture(name)) == prior_audit["source_sha256"][str(RUN / name)] for name in legacy_names}
    assert all(legacy_checks.values())
    baseline = read("admin/baseline_hashes.json")
    assert all(sha(path) == expected for path, expected in baseline.items())
    frozen_protocol = read("protocol/freeze.json")
    assert sha(capture("protocol/完整五维手册-v1.3.md")) == frozen_protocol["protocol_sha256"]
    assert sha(capture("共用操作说明-v1.4.md")) == frozen_protocol["clarification_sha256"]
    checks["preservation"] = {"legacy_v6_guide_CSV_reference_and_A_C_sha_match_prior_audit": legacy_checks, "baseline_five_SHA_match": True, "protocol_and_operational_SHA_match": True, "historical_future_v2_freeze_sha256_before": historic_sha, "historical_future_v2_freeze_sha256_after": sha(RUN / historical_freeze_name), "historical_freeze_bytes_unchanged": historic_sha == sha(RUN / historical_freeze_name)}
    assert all(sha(path) == expected for path, expected in SNAPSHOT.items())

    append_binding = {"status": "append_only_training_v8_binding_not_a_replacement_freeze", "created_at": datetime.datetime.now().astimezone().isoformat(), "historical_future_v2_freeze_path": str(RUN / historical_freeze_name), "historical_future_v2_freeze_sha256": historic_sha, "historical_freeze_bytes_preserved": True, "future_sampling_design_sha256": sha(RUN / "admin/future_human_v2_sampling_PRIVATE.json"), "full_material_version": "v8", "training_source_sha256": {name: sha(RUN / name) for name in ["真人五维编码培训依据-v8.md", "真人培训候选判例-300条-v8.csv", "reference/adjudicated_candidate_reference_v8.jsonl", "reference/agent_A_final_v8.jsonl", "reference/agent_C_final_v8.jsonl", "reference/training_guide_binding_v8.json"]}, "future_package_sha256": {name: sha(RUN / name) for name in historical_freeze["package_sha256"]}, "training_unit_ID_set_unchanged": True, "training_current_unit_text_set_unchanged": all(units[rid]["text"] == row["政策原文"] for rid, row in [(r["原单元编号"], r) for r in table("真人培训候选判例-300条.csv")]), "future_current_unit_text_families_disjoint_from_training_and_known": True, "future_answer_fields_filled": 0, "real_human_execution_started": False, "human_validation_completed": False, "scope_limit": "49 of 240 future current-unit raw texts occur in public v8 training context. The binding certifies current-unit text-family exclusion and answer-free packets, not complete source/context non-exposure or new-document independence.", "future_current_unit_texts_visible_in_training_context_n": len(context_exposure)}
    binding_name = "admin/future_human_v2_training_v8_append_binding.json"
    (RUN / binding_name).write_text(json.dumps(append_binding, ensure_ascii=False, indent=2) + "\n")
    report = {"audit": "Final public v8 training delivery and future v2 append-binding QA", "auditor": "independent_AI_agent_training_integrity_audit", "created_at": datetime.datetime.now().astimezone().isoformat(), "status": "pass_integrity_and_answer_free_checks_with_disclosed_context_exposure_scope_limit", "checks": checks, "integrity_errors": [], "material_scope_findings": [{"code": "FUTURE_TEXT_VISIBLE_IN_TRAINING_CONTEXT", "n": len(context_exposure), "detail": "The full-context column exposes 49 future raw unit texts as background/parent/sibling text. This does not include item-specific answer labels but rules out an unqualified assertion that all 240 raw texts are unseen. No sample, label or historical freeze was changed."}], "append_binding_path": str(RUN / binding_name), "append_binding_sha256": sha(RUN / binding_name), "source_sha256": SNAPSHOT, "limits": ["This is an AI integrity/provenance audit, not completed real-human reliability or validity verification.", "Exact text quotes and source bindings do not independently establish all semantic judgments. Four flagged boundaries remain for actual humans; 4155 preserves the third agent's two-source subtype candidate and A/C's attribute-only judgments separately.", "Current 300 includes 20 normalized current-unit duplicates of known-development text; original scores remain preserved and the guide explicitly discloses the scope limitation.", "The future v2 design excludes current-unit normalized text families and preserves answer-free packets; it does not eliminate training context exposure, paraphrases or shared policy-file/model provenance."]}
    (OUT / "最终培训交付-v8独立QA.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (OUT / "最终培训交付-v8独立QA.md").write_text(f"""# 最终v8培训交付独立QA

核验通过，并保留语境接触限制。300条v8候选参照、A/C补料提交、完整语境CSV及28个指南判例逐标签、理由、逐字证据和来源一致。所有正类均有当前单元引文，全部引文出现在当前原句或实际语境text字段中。4条新复读输入不含A/C或机器答案，实际输出SHA绑定独立源复读材料；旧43条与新4条重合1条，独立审查合计46条。A/C分歧仍19条。

v8仅4156的I由A、C和候选参照0→1，其余三条保持原五维标签。4155在第三agent候选中保留attribute与research_support双来源，A/C保留attribute单来源，未覆盖原判断；此子类边界新增待真人复核。共4项真人复核完整展示：00105（F）、01059（Ec）、03523（F）、04155（I）。指南明确执行者为agent、尚未真人验证，不作不可修订金标准或发表保证。

未来v2再次核验：两人同240条原文及v8语境、不同编号和顺序，各3360答案栏和3身份/日期栏全空，无预测、答案或逐维理由字段；与培训/已知开发的当前单元正文族零交集，包内正文族零重复，抽样概率和权重正确。新版培训CSV增加完整语境后，49条未来原句可在培训条目的语境中看到。因此“无答案泄露、当前单元正文族不重复”成立，不能表述为“全部240原文从未接触”。完整49条对应见JSON，未重抽或改包。

旧v6指南/CSV/参照与A/C、旧未来包、5项baseline及手册SHA均未变。历史future_human_v2_freeze.json保留原字节；另写admin/future_human_v2_training_v8_append_binding.json追加绑定新版培训CSV、指南、参照及A/C来源SHA。v2尚未真人执行。本审计不修改任何标签、编码或统计。
""")
    assert sha(RUN / historical_freeze_name) == historic_sha
    print(json.dumps({"status": report["status"], "n": 300, "guide_cases": 28, "unique_reviewed": 46, "human_review_flags": len(flags), "context_exposed_future_units": len(context_exposure), "append_binding": str(RUN / binding_name), "QA": str(OUT / "最终培训交付-v8独立QA.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
