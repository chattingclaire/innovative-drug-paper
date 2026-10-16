"""Create a new answer-free text-family holdout; never edit old packages or labels."""
import collections
import copy
import datetime
import hashlib
import json
import random
import unicodedata
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "future-human-validation-v2"
SEED = 2026100751
GROUPS = ("NMPA", "NHSA", "NHC")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def jl(path):
    return {r["id"]: r for r in [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]}


def norm(text):
    return "".join(c for c in unicodedata.normalize("NFKC", text) if not c.isspace() and not unicodedata.category(c).startswith("P"))


def write(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def main():
    assert not OUT.exists(), "Do not overwrite a previously generated holdout."
    old_hashes = {str(p.relative_to(RUN)): sha(p) for p in sorted((RUN / "future-human-validation").iterdir()) if p.is_file()}
    units = jl(RUN / "effective_blind_inputs_v8.jsonl")
    rules = jl(RUN / "rule_inputs_shared_v8.jsonl")
    metadata_path = Path(read(RUN.parent / "recall-revision-20261007/三部门注意力分布与敏感性.json")["method_bindings"]["metadata"])
    metadata = {Path(r["original_file"]).stem: r for r in read(metadata_path)["rows"]}
    groups = {rid: metadata[r["input"]["original_file_stem"]]["analysis_group"] for rid, r in rules.items()}
    assert set(units) == set(rules)
    assert all(r["input"]["unit_text"] == units[rid]["text"] and r["input"]["llm_v29_shared_context"] == units[rid]["contexts"] for rid, r in rules.items())
    previous = read(RUN / "admin/sampling_design.json")
    training_ids = {r["original_id"] for r in previous["sample"]}
    known_ids = set(previous["excluded_ids"])
    excluded_ids = training_ids | known_ids
    blocked_texts = {norm(units[rid]["text"]) for rid in excluded_ids if rid in units}
    families = collections.defaultdict(list)
    removed_text_matches = []
    for rid in sorted(units):
        if groups[rid] not in GROUPS or rid in excluded_ids:
            continue
        text = norm(units[rid]["text"])
        if text in blocked_texts:
            removed_text_matches.append(rid)
        else:
            families[text].append(rid)
    cross = {text: ids for text, ids in families.items() if len({groups[rid] for rid in ids}) > 1}
    frame = {g: {} for g in GROUPS}
    for text, ids in families.items():
        if text in cross:
            continue
        fid = "TEXTFAM-" + hashlib.sha256(text.encode()).hexdigest()
        frame[groups[ids[0]]][fid] = {"family_id": fid, "normalized_text_sha256": hashlib.sha256(text.encode()).hexdigest(), "group": groups[ids[0]], "members": sorted(ids), "k_family": len(ids)}
    assert {g: len(v) for g, v in frame.items()} == {"NMPA": 1031, "NHSA": 841, "NHC": 140}
    rng = random.Random(SEED)
    sample = []
    for g in GROUPS:
        F = len(frame[g])
        for fid in rng.sample(sorted(frame[g]), 80):
            family = frame[g][fid]
            rid = rng.choice(family["members"])
            k = family["k_family"]
            sample.append({"original_id": rid, "group": g, "family_id": fid, "eligible_family_count": F, "sampled_family_count": 80, "k_family": k, "eligible_family_members": family["members"], "family_inclusion_probability": 80 / F, "within_family_selection_probability": 1 / k, "unit_inclusion_probability": 80 / F / k, "unit_analysis_weight": F * k / 80})
    assert len(sample) == len({r["original_id"] for r in sample}) == len({norm(units[r["original_id"]]["text"]) for r in sample}) == 240
    OUT.mkdir()
    headers = ["匿名编号", "政策原文", "来源标题", "页码", "完整语境JSON", "S", "E", "Ec", "I", "F", "S理由", "E理由", "Ec理由", "I理由", "F理由", "逐字证据", "I来源类型", "F来源类型", "问题说明"]
    mapping = []
    matrices = {}
    for coder, order_seed in (("A", SEED + 101), ("C", SEED + 202)):
        ordered = [r["original_id"] for r in sample]
        random.Random(order_seed).shuffle(ordered)
        rows = []
        table = [headers]
        for i, rid in enumerate(ordered, 1):
            blind_id = f"HV2V2-{coder}-{i:04d}"
            row = {"id": blind_id, **{k: copy.deepcopy(units[rid][k]) for k in ("text", "source_title", "pages", "contexts", "context_usage")}}
            rows.append(row)
            mapping.append({"coder": coder, "blind_id": blind_id, "original_id": rid})
            table.append([blind_id, row["text"], row["source_title"], json.dumps(row["pages"], ensure_ascii=False), json.dumps(row["contexts"], ensure_ascii=False)] + [""] * 14)
        write(OUT / f"真人{coder}-无答案材料.json", {"status": "blank_for_future_real_human_execution", "package_version": "v2", "material_version": "v8", "coder_name": "", "professional_background": "", "execution_date": "", "manual_version": "v1.3 + operational v1.4", "rows": rows})
        matrices[coder] = table
    write(RUN / "audit-training/future_human_v2_csv_matrices.json", matrices)
    design = {"created_at": datetime.datetime.now().astimezone().isoformat(), "execution_status": "not_started_no_real_human_labels", "package_version": "v2", "material_version": "v8", "seed": SEED, "random_generator": "Python standard-library random.Random; sorted family SHA IDs; sample 80 families without replacement per department, then uniform random one available unit within each selected family", "coder_order_seeds": {"A": SEED + 101, "C": SEED + 202}, "normalization": "NFKC; remove Unicode whitespace and all Unicode punctuation category P*; keep remaining symbols and letter case", "sampling_design": "department-stratified equal-probability family SRSWOR, followed by uniform one-unit selection within sampled family; not ordinary unit SRS", "unit_probability_formula": "pi_unit = (80 / F_group) * (1 / k_family)", "unit_weight_formula": "w_unit = F_group * k_family / 80", "scope": "Only the v8 three-department units remaining after removal of known-development IDs, current 300 IDs and all their normalized-text families, plus all cross-department families. Not a new-document external validation or inference to excluded text families.", "known_development_excluded_ids": sorted(known_ids), "current_training_excluded_ids": sorted(training_ids), "additional_units_excluded_by_normalized_text": removed_text_matches, "cross_department_families_excluded": [{"normalized_text_sha256": hashlib.sha256(text.encode()).hexdigest(), "members": ids, "groups": sorted({groups[rid] for rid in ids})} for text, ids in sorted(cross.items())], "eligible_family_counts": {g: len(frame[g]) for g in GROUPS}, "eligible_unit_counts": {g: sum(f["k_family"] for f in frame[g].values()) for g in GROUPS}, "all_eligible_families": [frame[g][fid] for g in GROUPS for fid in sorted(frame[g])], "sample": sample, "mapping": mapping, "old_package_sha256_preserved": old_hashes}
    write(RUN / "admin/future_human_v2_sampling_PRIVATE.json", design)
    (OUT / "使用说明.md").write_text("""# 未来真人验证材料 v2（尚未执行）

本目录供未来两名真人独立编码。每人240条，原文与完整语境相同，匿名编号和顺序不同。编码员姓名、专业经历、实施日期和全部五维、理由、证据及来源类型均为空，须由实际执行者填写。采用完整五维手册v1.3及共用操作说明v1.4，全文与语境取自本轮v8同材输入；尚无真人编码或真人信度结论。

先完成培训，正式编码时两人不得共享答案或查看机器结果；先封存双方原始提交，计算协商前信度，再人工裁决。遇到缺字、对象或父条件不足，应标明材料问题，不能猜0。原300条agent候选判例供学习和讨论，不能将其答案视为不可修订的人类金标准。

本包按规范化正文族排除全部已知历史开发和当前300条培训材料，再在每部门的可用独特正文族中随机抽80族、族内随机抽1条，共240条。规范化为NFKC后删除全部空白与Unicode标点；本包正文族内不重复。跨部门共享正文族事先整体排除（本轮实际0族）。剩余可用正文族为药监1031、医保841、卫健140族。该设计是先抽正文族、再抽单位，不能称普通单位简单随机抽样，也不代表被排除正文或新政策文件。抽样概率、权重和私有映射封存在admin目录；正式编码时不提供私有映射和任何机器答案。

原future-human-validation目录仅保留历史归档，不再作为正式真人验证包。其编号虽未重合，但存在与培训或开发相同的正文。本v2保留原包字节，以独立新样本替代，未改任何旧标签。
""")
    (RUN / "future-human-validation-旧包停用说明.md").write_text("""# 原未来真人包停用说明

原future-human-validation目录保留原始字节，仅用于归档。该包240条虽与当前培训300和已知开发没有相同原单元编号，但6条正文逐字重复培训，规范化后9条重复培训、17条重复已知开发，合计23条；包内另有一对正文重复。因此不再用于正式真人验证。

未来正式执行使用future-human-validation-v2中的新封存包。v2从v8完整材料按规范化正文族排除当前300与全部已知开发再重新抽样，且两个编码员的五维、理由、证据和身份/实施信息全部为空。原包、既有agent结果和任何旧标签未覆盖。详细重叠对应见audit-training/独立培训材料QA.json；v2独立核验另见该目录的未来真人v2独立QA.json。
""")
    assert old_hashes == {str(p.relative_to(RUN)): sha(p) for p in sorted((RUN / "future-human-validation").iterdir()) if p.is_file()}
    print(json.dumps({"created": str(OUT), "family_counts": design["eligible_family_counts"], "units": 240, "labels_filled": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
