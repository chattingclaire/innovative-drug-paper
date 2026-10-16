"""Independently reconstruct and verify v2 holdout, then freeze source/output SHA."""
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
OUT = RUN / "audit-training"
PACK = RUN / "future-human-validation-v2"
GROUPS = ("NMPA", "NHSA", "NHC")


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(value):
    value = unicodedata.normalize("NFKC", value)
    return "".join(char for char in value if not char.isspace() and unicodedata.category(char)[0] != "P")


def strings_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from strings_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from strings_keys(value)


def main():
    design_path = RUN / "admin/future_human_v2_sampling_PRIVATE.json"
    design = read(design_path)
    units = {r["id"]: r for r in [json.loads(line) for line in (RUN / "effective_blind_inputs_v8.jsonl").read_text().splitlines()]}
    rules = {r["id"]: r for r in [json.loads(line) for line in (RUN / "rule_inputs_shared_v8.jsonl").read_text().splitlines()]}
    meta_path = Path(read(RUN.parent / "recall-revision-20261007/三部门注意力分布与敏感性.json")["method_bindings"]["metadata"])
    meta = {Path(r["original_file"]).stem: r["analysis_group"] for r in read(meta_path)["rows"]}
    groups = {rid: meta[row["input"]["original_file_stem"]] for rid, row in rules.items()}
    old_design = read(RUN / "admin/sampling_design.json")
    known = set(old_design["excluded_ids"])
    training = {r["original_id"] for r in old_design["sample"]}
    blocked = {normalize(units[rid]["text"]) for rid in known | training if rid in units}
    eligible = [rid for rid in units if groups[rid] in GROUPS and rid not in known | training and normalize(units[rid]["text"]) not in blocked]
    all_families = collections.defaultdict(list)
    for rid in eligible:
        all_families[normalize(units[rid]["text"])].append(rid)
    cross = {key for key, ids in all_families.items() if len({groups[rid] for rid in ids}) != 1}
    frame = {}
    for text, ids in all_families.items():
        if text not in cross:
            fid = "TEXTFAM-" + hashlib.sha256(text.encode()).hexdigest()
            frame[fid] = (groups[ids[0]], sorted(ids))
    recorded = {r["family_id"]: (r["group"], r["members"]) for r in design["all_eligible_families"]}
    assert recorded == frame
    family_counts = dict(collections.Counter(group for group, _ in frame.values()))
    assert family_counts == design["eligible_family_counts"] == {"NMPA": 1031, "NHSA": 841, "NHC": 140}
    assert len(cross) == len(design["cross_department_families_excluded"]) == 0
    sample = design["sample"]
    ids = [r["original_id"] for r in sample]
    assert len(ids) == len(set(ids)) == len({normalize(units[rid]["text"]) for rid in ids}) == 240
    assert collections.Counter(r["group"] for r in sample) == {g: 80 for g in GROUPS}
    assert not (set(ids) & (known | training))
    assert not ({normalize(units[rid]["text"]) for rid in ids} & blocked)
    rng = random.Random(2026100751)
    replay = []
    for group in GROUPS:
        for fid in rng.sample(sorted(fid for fid, (g, _) in frame.items() if g == group), 80):
            replay.append((fid, rng.choice(frame[fid][1])))
    assert replay == [(r["family_id"], r["original_id"]) for r in sample]
    for r in sample:
        group, members = frame[r["family_id"]]
        F, k = family_counts[group], len(members)
        assert r["eligible_family_members"] == members and r["k_family"] == k and r["original_id"] in members
        assert math.isclose(r["unit_inclusion_probability"], 80 / F / k, rel_tol=1e-13)
        assert math.isclose(r["unit_analysis_weight"], F * k / 80, rel_tol=1e-13)
        assert math.isclose(r["unit_analysis_weight"] * r["unit_inclusion_probability"], 1, rel_tol=1e-13)
    mapping = {(r["coder"], r["blind_id"]): r["original_id"] for r in design["mapping"]}
    assert len(mapping) == 480
    orders = {}
    blank_count = {}
    answer_keys_found = []
    package_checks = {}
    for coder in "AC":
        packet = read(PACK / f"真人{coder}-无答案材料.json")
        with (PACK / f"真人{coder}-空白编码表.csv").open(encoding="utf-8-sig", newline="") as handle:
            table = list(csv.DictReader(handle))
        assert len(packet["rows"]) == len(table) == 240
        assert packet["material_version"] == "v8"
        assert packet["status"] == "blank_for_future_real_human_execution"
        assert all(packet[k] == "" for k in ["coder_name", "professional_background", "execution_date"])
        order = []
        count = 0
        for row, cells in zip(packet["rows"], table):
            rid = mapping[coder, row["id"]]
            order.append(rid)
            assert set(row) == {"id", "text", "source_title", "pages", "contexts", "context_usage"}
            assert all(row[key] == units[rid][key] for key in ["text", "source_title", "pages", "contexts", "context_usage"])
            assert rules[rid]["input"]["unit_text"] == row["text"] and rules[rid]["input"]["llm_v29_shared_context"] == row["contexts"]
            assert cells["匿名编号"] == row["id"] and cells["政策原文"] == row["text"] and cells["来源标题"] == row["source_title"]
            assert json.loads(cells["页码"]) == row["pages"] and json.loads(cells["完整语境JSON"]) == row["contexts"]
            answer_fields = [key for key in cells if key not in ["匿名编号", "政策原文", "来源标题", "页码", "完整语境JSON"]]
            assert len(answer_fields) == 14 and all(cells[key] == "" for key in answer_fields)
            count += len(answer_fields)
        orders[coder] = order
        assert set(order) == set(ids)
        expected_order = ids.copy()
        random.Random(design["coder_order_seeds"][coder]).shuffle(expected_order)
        assert order == expected_order
        blank_count[coder] = count
        answer_keys_found += [{"coder": coder, "key": key} for key in strings_keys(packet) if re.search(r"label|prediction|gold|judgment|reason|answer|adjudicat|expected|subtype|quality_basis", key, re.I)]
        package_checks[coder] = {"rows": 240, "blank_answer_fields": count, "blank_identity_fields": 3, "JSON_CSV_exact_match": True, "latest_v8_text_source_pages_context_match": True}
    assert not answer_keys_found and orders["A"] != orders["C"]
    assert design["old_package_sha256_preserved"] == {str(p.relative_to(RUN)): sha(p) for p in sorted((RUN / "future-human-validation").iterdir()) if p.is_file()}
    baseline = read(RUN / "admin/baseline_hashes.json")
    assert all(sha(path) == expected for path, expected in baseline.items())
    protocol = read(RUN / "protocol/freeze.json")
    assert sha(RUN / "protocol/完整五维手册-v1.3.md") == protocol["protocol_sha256"]
    assert sha(RUN / "共用操作说明-v1.4.md") == protocol["clarification_sha256"]
    source_paths = [RUN / "effective_blind_inputs_v8.jsonl", RUN / "rule_inputs_shared_v8.jsonl", RUN / "admin/sampling_design.json", RUN / "protocol/完整五维手册-v1.3.md", RUN / "共用操作说明-v1.4.md", RUN / "真人培训候选判例-300条.csv", meta_path, OUT / "build_future_human_v2.py", OUT / "build_future_human_v2_csv.mjs", Path(__file__)]
    output_paths = sorted(p for p in PACK.iterdir() if p.is_file()) + [RUN / "future-human-validation-旧包停用说明.md"]
    freeze = {"status": "frozen_before_real_human_execution", "created_at": datetime.datetime.now().astimezone().isoformat(), "package_version": "v2", "full_material_version": "v8", "manual_version": "v1.3 + operational v1.4", "sampling_seed": 2026100751, "sampling_design": "department family SRSWOR followed by uniform one-unit selection within selected family", "sampling_design_private_path": str(design_path), "sampling_design_sha256": sha(design_path), "source_sha256": {str(p): sha(p) for p in source_paths}, "package_sha256": {str(p.relative_to(RUN)): sha(p) for p in output_paths}, "old_package_sha256_preserved": design["old_package_sha256_preserved"], "real_human_execution_started": False, "human_validation_completed": False, "answer_fields_filled": 0, "identity_fields_filled": 0}
    (RUN / "admin/future_human_v2_freeze.json").write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n")
    report = {"status": "pass_answer_free_text_family_holdout_frozen_not_human_executed", "created_at": datetime.datetime.now().astimezone().isoformat(), "auditor": "independent_AI_agent_training_integrity_audit", "full_material_version": "v8", "A_C_training_reference_last_supplement_material": "v6 (v8 source-only supplement review pending separately)", "sample_n": 240, "sample_by_group": {g: 80 for g in GROUPS}, "eligible_family_counts": family_counts, "eligible_unit_counts": design["eligible_unit_counts"], "cross_department_text_family_exclusions": 0, "known_development_original_id_intersection": [], "training_original_id_intersection": [], "known_or_training_normalized_text_intersection": [], "within_package_duplicate_normalized_texts": 0, "seed_replay_matches": True, "all_family_members_match_reconstructed_frame": True, "unit_inclusion_probabilities_and_weights_recomputed_match": True, "probability_formula": "pi_unit = (80/F_group)*(1/k_family)", "weight_formula": "w_unit = F_group*k_family/80", "not_ordinary_unit_SRS": True, "A_C_same_original_units_and_full_context": True, "A_C_different_order_and_identifiers": True, "packages": package_checks, "answer_keys_found": answer_keys_found, "old_package_bytes_unchanged": True, "baseline_hashes_and_protocol_hashes_unchanged": True, "sampling_design_path": str(design_path), "sampling_design_sha256": sha(design_path), "freeze_path": str(RUN / "admin/future_human_v2_freeze.json"), "freeze_sha256": sha(RUN / "admin/future_human_v2_freeze.json"), "limits": ["Exact normalized-text-family exclusion does not establish independence from paraphrases, adjacent context, underlying model training or policy-file provenance.", "The frame excludes known development/training text families; inference is restricted to this residual frame, and no real human has coded the packet.", "Generic source/object verification and non-inheritance guidance remain part of shared contexts; no item-specific labels, predictions, dimension reasons or expected answers are included."]}
    (OUT / "未来真人v2独立QA.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (OUT / "未来真人v2独立QA.md").write_text("""# 未来真人v2无答案包独立核验

通过。v2取自v8原文和完整语境，两人各240条、同材料不同编号和顺序；每人3360个答案栏及3个身份/日期栏全部为空。JSON与CSV一致，未发现标签、机器预测、逐维理由或预期答案字段。旧包全部字节、旧产物SHA和手册SHA均未变化。

从排除已知开发及当前300全部规范化正文族后的剩余框，按部门各随机抽80个正文族，再在族内均匀抽1实际单元。可用正文族为药监1031、医保841、卫健140；可用单元分别1044、1113、140；跨部门共享正文族0。固定seed2026100751可重放。与培训和已知开发的编号及规范化正文均零交集，包内正文族零重复。

私有设计保留全部可用族成员，逐条概率为(80/F部门)×(1/k族)，权重为F部门×k族/80，已独立重算。它不是普通单位简单随机样本，不能推断被排除正文或称新文件外部验证。设计、来源与包文件SHA已冻结到admin/future_human_v2_freeze.json。v2尚未真人执行；近义改写、相邻语境或底层模型既往接触不在本次严格去重证明范围内。
""")
    print(json.dumps({"status": report["status"], "sample_n": 240, "family_counts": family_counts, "freeze": str(RUN / "admin/future_human_v2_freeze.json"), "QA": str(OUT / "未来真人v2独立QA.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
