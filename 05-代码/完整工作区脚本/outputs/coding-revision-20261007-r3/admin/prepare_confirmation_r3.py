"""Prepare a distinct canonical-clause confirmation; do not code or inspect r3 methods."""
import argparse
import ast
import collections
import copy
import datetime
import hashlib
import json
import random
import re
import shutil
import unicodedata
from pathlib import Path

R3 = Path(__file__).resolve().parents[1]
R2 = R3.parent / "agent-validation-20261007-r2"
OLD = R3.parent / "recall-revision-20261007"
ADMIN = R3 / "admin"
SEED = 2026100761
GROUPS = ("NMPA", "NHSA", "NHC")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def jl(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    assert len(rows) == len({r["id"] for r in rows})
    return {r["id"]: r for r in rows}


def write(path, value):
    path = Path(path)
    assert not path.exists(), f"Do not overwrite frozen artifact: {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def norm(text):
    return "".join(char for char in unicodedata.normalize("NFKC", text) if not char.isspace() and not unicodedata.category(char).startswith("P"))


def groups_for(rules):
    meta_path = Path(read(OLD / "三部门注意力分布与敏感性.json")["method_bindings"]["metadata"])
    meta = {Path(r["original_file"]).stem: r["analysis_group"] for r in read(meta_path)["rows"]}
    return {rid: meta[row["input"]["original_file_stem"]] for rid, row in rules.items()}, meta_path


def scan_control_ids(corpus_ids):
    roots = [R2 / "rules-v32", OLD / "rules-v31"]
    paths = sorted({p for root in roots for p in root.rglob("*") if p.is_file() and (p.suffix in {".py", ".patch"} or p.name == "test_following_list_certificates.json")})
    manifest, occurrences = [], []
    for path in paths:
        source = path.read_text()
        found = []
        for m in re.finditer(r"RECODE25-\d{5}\b", source):
            found.append({"id": m.group(), "line": source.count("\n", 0, m.start()) + 1, "evidence_type": "explicit_full_RECODE_ID_literal"})
        if path.suffix == ".py" and "RECODE25-" in source:
            tree = ast.parse(source)
            # Existing controls explicitly assemble records['RECODE25-'+short].
            # Recover their five-digit string constants without executing tests.
            if any(isinstance(node, ast.Constant) and node.value == "RECODE25-" for node in ast.walk(tree)):
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str) and re.fullmatch(r"\d{5}", node.value):
                        found.append({"id": "RECODE25-" + node.value, "line": node.lineno, "evidence_type": "five_digit_literal_used_with_explicit_RECODE_prefix_in_control_source"})
        digest = sha(path)
        manifest.append({"path": str(path), "sha256": digest, "explicit_ID_occurrences": len(found)})
        for row in found:
            row.update(source_path=str(path), source_sha256=digest, source_line=source.splitlines()[row["line"] - 1].strip(), exists_in_v8_corpus=row["id"] in corpus_ids)
            occurrences.append(row)
    return {r["id"] for r in occurrences if r["exists_in_v8_corpus"]}, {"scan_roots": [str(p) for p in roots], "source_selection": "All Python and patch source files beneath the two frozen legacy rule trees, plus named curated test_following_list_certificates.json fixtures. No machine full-corpus output, metrics, logs or generated result JSON is used as exposure evidence.", "source_file_manifest": manifest, "ID_occurrences": occurrences, "unique_existing_control_IDs": sorted({r["id"] for r in occurrences if r["exists_in_v8_corpus"]}), "noncorpus_ID_literals": sorted({r["id"] for r in occurrences if not r["exists_in_v8_corpus"]})}


def design():
    design_path = ADMIN / "confirmation_sampling_PRIVATE.json"
    assert not design_path.exists()
    inputs_path, rules_path = R2 / "effective_blind_inputs_v8.jsonl", R2 / "rule_inputs_shared_v8.jsonl"
    units, rules = jl(inputs_path), jl(rules_path)
    groups, metadata_path = groups_for(rules)
    assert set(units) == set(rules)
    previous = read(R2 / "admin/sampling_design.json")
    future = read(R2 / "admin/future_human_v2_sampling_PRIVATE.json")
    categories = {"historical_known_development": set(previous["excluded_ids"]), "r2_all_300_now_development": {r["original_id"] for r in previous["sample"]}, "reserved_future_real_human_v2": {r["original_id"] for r in future["sample"]}}
    controls, evidence = scan_control_ids(set(units))
    categories["explicit_legacy_rule_regression_control_IDs"] = controls
    excluded_ids = set.union(*categories.values())
    blocked = {norm(units[rid]["text"]) for rid in excluded_ids if rid in units}
    families = collections.defaultdict(list)
    same_text_exclusions = []
    for rid in sorted(units):
        if groups[rid] not in GROUPS or rid in excluded_ids:
            continue
        fingerprint = norm(units[rid]["text"])
        if fingerprint in blocked:
            same_text_exclusions.append(rid)
        else:
            families[fingerprint].append(rid)
    cross = {key: ids for key, ids in families.items() if len({groups[rid] for rid in ids}) > 1}
    frame = {g: {} for g in GROUPS}
    for text, ids in families.items():
        if text in cross:
            continue
        representative = min(ids)
        frame[groups[representative]][representative] = {"canonical_id": representative, "group": groups[representative], "family_id": "TEXTFAM-" + text_sha(text), "normalized_text_sha256": text_sha(text), "all_remaining_family_members": sorted(ids), "family_size": len(ids), "unit_text_sha256": text_sha(units[representative]["text"])}
    rng = random.Random(SEED)
    probability = []
    for group in GROUPS:
        F = len(frame[group])
        n = min(60, F)
        for rid in rng.sample(sorted(frame[group]), n):
            probability.append({"original_id": rid, "group": group, "component": "probability_canonical", "canonical_frame_N": F, "sample_n": n, "inclusion_probability": n / F, "analysis_weight": F / n, "unit_text_sha256": frame[group][rid]["unit_text_sha256"], "family_id": frame[group][rid]["family_id"]})
    # Old labels are first read here, after construction of the probability frame
    # and probability selection. They are used only for a separate challenge arm.
    old_rule_path = R2 / "rules-v32/material-adapter-v32.1/all_predictions_material_v8.jsonl"
    old_llm_path = R2 / "llm-v31/sealed-final-material-v8/all_predictions_composite.jsonl"
    old_rule, old_llm = jl(old_rule_path), jl(old_llm_path)
    probability_ids = {r["original_id"] for r in probability}
    challenge, challenge_pools = [], {}
    for group in ("NMPA", "NHSA"):
        remaining = sorted(set(frame[group]) - probability_ids)
        primary = [rid for rid in remaining if any(old_rule[rid]["prediction"]["labels"][d] == 1 or old_llm[rid]["labels"][d] == 1 for d in ("I", "F"))]
        broad = [rid for rid in remaining if any(old_rule[rid]["prediction"]["labels"][d] == 1 or old_llm[rid]["labels"][d] == 1 for d in ("S", "E", "Ec", "I", "F"))]
        chosen_primary = rng.sample(primary, min(30, len(primary)))
        fallback = [rid for rid in broad if rid not in chosen_primary]
        chosen_fallback = rng.sample(fallback, min(30 - len(chosen_primary), len(fallback)))
        chosen = chosen_primary + chosen_fallback
        assert len(chosen) == 30, (group, len(primary), len(broad))
        challenge_pools[group] = {"primary_old_rule_or_LLM_I_F_positive_pool": primary, "fallback_any_five_positive_pool": broad, "primary_selected_n": len(chosen_primary), "fallback_selected_n": len(chosen_fallback)}
        for rid in chosen:
            challenge.append({"original_id": rid, "group": group, "component": "enriched_challenge", "selection_pool": "old_rule_or_LLM_I_F_positive" if rid in chosen_primary else "fallback_any_five_positive", "inclusion_probability": None, "analysis_weight": None, "unit_text_sha256": frame[group][rid]["unit_text_sha256"], "family_id": frame[group][rid]["family_id"]})
    sample = probability + challenge
    assert len({r["original_id"] for r in sample}) == len(sample)
    assert len({norm(units[r["original_id"]]["text"]) for r in sample}) == len(sample)
    mapping = []
    for coder, order_seed in (("A", SEED + 101), ("C", SEED + 202)):
        ordered = [r["original_id"] for r in sample]
        random.Random(order_seed).shuffle(ordered)
        mapping.extend({"coder": coder, "blind_id": f"AV3-{coder}-{i:04d}", "original_id": rid, "unit_text_sha256": text_sha(units[rid]["text"])} for i, rid in enumerate(ordered, 1))
    evidence.update(categories={name: sorted(ids) for name, ids in categories.items()}, category_counts={name: len(ids) for name, ids in categories.items()}, excluded_original_ID_union=sorted(excluded_ids), additional_same_normalized_text_IDs=same_text_exclusions, cross_department_families_excluded=[{"normalized_text_sha256": text_sha(text), "members": ids, "groups": sorted({groups[rid] for rid in ids})} for text, ids in sorted(cross.items())])
    write(ADMIN / "confirmation_exclusion_evidence_PRIVATE.json", evidence)
    write(ADMIN / "confirmation_canonical_frame_PRIVATE.json", {"normalization": "NFKC; remove whitespace and Unicode category P* punctuation; retain other symbols and case", "canonical_rule": "Lexicographically smallest original ID in each eligible normalized-text family", "frame_by_group": {g: [frame[g][rid] for rid in sorted(frame[g])] for g in GROUPS}, "frame_counts": {g: len(frame[g]) for g in GROUPS}})
    write(ADMIN / "PRIVATE_mapping.json", mapping)
    design_data = {"created_at": datetime.datetime.now().astimezone().isoformat(), "status": "selected_ID_and_text_frame_locked_before_v9_packet_generation", "frame_material_version": "v8", "seed": SEED, "random_generator": "Python random.Random; sort canonical IDs; sequential department probability samples then NMPA/NHSA challenge samples", "coder_order_seeds": {"A": SEED + 101, "C": SEED + 202}, "frame_N_by_group": {g: len(frame[g]) for g in GROUPS}, "probability_sample_n_by_group": dict(collections.Counter(r["group"] for r in probability)), "challenge_sample_n_by_group": dict(collections.Counter(r["group"] for r in challenge)), "probability_n": len(probability), "challenge_n": len(challenge), "total_n_per_coder": len(sample), "sample": sample, "challenge_pool_details_PRIVATE": challenge_pools, "probability_scope": "SRSWOR over remaining canonical unique-clause representative units within each department, not all 4481 units and not every member of a text family. For F<=60 the remaining canonical frame is a census.", "probability_formula": "pi = min(60,F_group)/F_group; weight = F_group/min(60,F_group)", "challenge_scope": "30 NMPA and 30 NHSA unselected canonical representatives enriched by frozen r2 old machine I/F positives, with any-five-positive fallback only if needed. Separate conditional diagnostics; never pooled with probability prevalence or population accuracy.", "NHC_challenge_n": 0, "context_contact_limit": "Same-policy adjacent, parent and shared context may have been encountered previously. Exclusion guarantees current-unit normalized-text-family nonrepeat only; this is not new-document external validation or real-human validation.", "no_r3_new_method_or_result_read": True, "no_labels_authored": True, "source_sha256": {str(p): sha(p) for p in [inputs_path, rules_path, metadata_path, R2 / "admin/sampling_design.json", R2 / "admin/future_human_v2_sampling_PRIVATE.json", old_rule_path, old_llm_path]}, "exclusion_evidence_sha256": sha(ADMIN / "confirmation_exclusion_evidence_PRIVATE.json"), "frame_sha256": sha(ADMIN / "confirmation_canonical_frame_PRIVATE.json"), "mapping_sha256": sha(ADMIN / "PRIVATE_mapping.json")}
    write(design_path, design_data)
    write(ADMIN / "confirmation_sampling_freeze.json", {"status": "canonical_frame_and_selected_IDs_frozen_awaiting_same_text_v9_packets", "created_at": design_data["created_at"], "seed": SEED, "design_sha256": sha(design_path), "frame_sha256": design_data["frame_sha256"], "mapping_sha256": design_data["mapping_sha256"], "exclusion_evidence_sha256": design_data["exclusion_evidence_sha256"], "source_sha256": design_data["source_sha256"], "prepared_script_sha256": sha(Path(__file__)), "human_validation_completed": False})
    print(json.dumps({k: design_data[k] for k in ["frame_N_by_group", "probability_sample_n_by_group", "challenge_sample_n_by_group", "probability_n", "challenge_n", "total_n_per_coder"]} | {"explicit_control_IDs": len(controls), "additional_text_exclusions": len(same_text_exclusions), "cross_department_families": len(cross)}, ensure_ascii=False))


def packets():
    design_data = read(ADMIN / "confirmation_sampling_PRIVATE.json")
    sampling_freeze = read(ADMIN / "confirmation_sampling_freeze.json")
    assert sha(ADMIN / "confirmation_sampling_PRIVATE.json") == sampling_freeze["design_sha256"]
    assert all(sha(path) == digest for path, digest in sampling_freeze["source_sha256"].items())
    v8, v9, rules = jl(R2 / "effective_blind_inputs_v8.jsonl"), jl(R3 / "effective_blind_inputs_v9.jsonl"), jl(R3 / "rule_inputs_shared_v9.jsonl")
    manifest = read(R3 / "material_v9_manifest.json")
    assert sha(R3 / "effective_blind_inputs_v9.jsonl") == manifest["new_llm_input_sha256"]
    assert sha(R3 / "rule_inputs_shared_v9.jsonl") == manifest["new_rule_input_sha256"]
    assert set(v8) == set(v9) == set(rules)
    assert all(v8[rid]["text"] == v9[rid]["text"] for rid in v8)
    assert all(rules[rid]["input"]["unit_text"] == v9[rid]["text"] and rules[rid]["input"]["llm_v29_shared_context"] == v9[rid]["contexts"] for rid in v9)
    for certificate in manifest["actual_source_certificates"]:
        for key in ("actual_source", "container_source"):
            assert sha(certificate[key + "_path"]) == certificate[key + "_sha256"]
        assert sha(certificate["candidate_path"]) == certificate["candidate_sha256"]
    frame = read(ADMIN / "confirmation_canonical_frame_PRIVATE.json")
    assert all(text_sha(v9[r["canonical_id"]]["text"]) == r["unit_text_sha256"] for rows in frame["frame_by_group"].values() for r in rows)
    protocol_dir = R3 / "protocol"
    protocol_dir.mkdir(exist_ok=True)
    for origin, target in [(R2 / "protocol/完整五维手册-v1.3.md", protocol_dir / "完整五维手册-v1.3.md"), (R2 / "共用操作说明-v1.4.md", protocol_dir / "共用操作说明-v1.4.md")]:
        if target.exists():
            assert sha(target) == sha(origin)
        else:
            shutil.copyfile(origin, target)
        assert sha(target) == sha(origin)
    mapping = read(ADMIN / "PRIVATE_mapping.json")
    confirmation = R3 / "confirmation"
    assert not confirmation.exists(), "Do not overwrite a previously created confirmation package."
    confirmation.mkdir()
    common = """# 五维独立编码任务

执行者是AI agent，本任务不是已完成的真人验证。仅读同目录指定本方材料及protocol中的完整五维手册v1.3、共用操作说明v1.4。不得读取admin、另一位编码员文件、机器规则/提示及其输出、reference、statistics或培训答案。

亲自逐条读完整分析单元与全部已给语境，分别判断安全性S、有效性E、经济性Ec、创新性I、公平性F。五项可以同时为1，也可以全0。对每维写理由；每个1必须有当前单元连续逐字证据，依赖语境时再引实际对象、父谓词、列头或条件。上下文仅用于消解明确关系，不能将其中所有标签复制到当前单元。保留I/F来源子类、S质量依据及问题说明。

遇到实质缺字、缺对象、父条件或表列不足，五维均显式待定并说明需补的材料；完整材料下存在边界争议则保留本人0/1判断及理由。不能为完整或一致而猜测，也不能读取另一位或机器答案后调整。

按每包原顺序独立提交结果-01.json等；逐包写coder、手册/说明版本、material_version=v9和对应输入包SHA256，使用结果schema。程序可展示材料、序列化本人判断及核对覆盖、逐字引文、JSON与SHA；不得用关键词或自动规则代替逐条语义判读。保留首次提交，后续若有补料另存复核。完成清单写实际时间、模型修订可得性及读取范围，不虚称真人或来源身份完全盲法。

同源文件的相邻、父级或共享语境可能曾被接触；当前包不重复已登记开发/保留样本的当前单元正文族。它不是新政策文件的外部验证。
"""
    (confirmation / "任务说明.md").write_text(common)
    label_schema = {"oneOf": [{"type": "integer", "enum": [0, 1]}, {"type": "string", "enum": ["待定"]}]}
    dims = ("S", "E", "Ec", "I", "F")
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Five-dimension independent coder result v9", "type": "object", "additionalProperties": False, "required": ["coder", "protocol_version", "operational_version", "material_version", "input_packet_sha256", "rows"], "properties": {"coder": {"enum": ["A", "C"]}, "protocol_version": {"const": "CAL-5D-20260926-v1.3"}, "operational_version": {"const": "v1.4"}, "material_version": {"const": "v9"}, "input_packet_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "rows": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["id", "labels", "dimension_reasons", "evidence", "innovation_subtypes", "fairness_subtypes", "safety_quality_basis", "issues"], "properties": {"id": {"type": "string", "pattern": "^AV3-[AC]-[0-9]{4}$"}, "labels": {"type": "object", "additionalProperties": False, "required": list(dims), "properties": {d: label_schema for d in dims}}, "dimension_reasons": {"type": "object", "additionalProperties": False, "required": list(dims), "properties": {d: {"type": "string", "minLength": 1} for d in dims}}, "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["dimension", "source", "quote"], "properties": {"dimension": {"enum": list(dims)}, "source": {"enum": ["unit", "context"]}, "quote": {"type": "string", "minLength": 1}}}}, "innovation_subtypes": {"type": "array", "uniqueItems": True, "items": {"enum": ["attribute", "research_support", "qualification_advantage"]}}, "fairness_subtypes": {"type": "array", "uniqueItems": True, "items": {"enum": ["access", "affordability", "clinical_management", "dimension_information"]}}, "safety_quality_basis": {"enum": ["quality_only", "quality_and_other", "no_quality_basis", "undetermined"]}, "issues": {"type": "array", "items": {"oneOf": [{"type": "string"}, {"type": "object"}]}}}}}}}
    write(confirmation / "结果schema.json", schema)
    packet_hashes = {}
    for coder in "AC":
        own = [r for r in mapping if r["coder"] == coder]
        own.sort(key=lambda r: r["blind_id"])
        folder = confirmation / f"agent-{coder}"
        folder.mkdir()
        for start in range(0, len(own), 30):
            rows = []
            for item in own[start:start + 30]:
                rid = item["original_id"]
                assert text_sha(v9[rid]["text"]) == item["unit_text_sha256"]
                rows.append({"id": item["blind_id"], **{key: copy.deepcopy(v9[rid][key]) for key in ["text", "source_title", "pages", "contexts", "context_usage"]}})
            path = folder / f"材料-{start // 30 + 1:02d}.json"
            write(path, {"material_version": "v9", "rows": rows})
            packet_hashes[str(path.relative_to(R3))] = sha(path)
        (folder / "任务说明.md").write_text(f"# 编码员{coder}\n\n只读本目录材料-*.json、上一级任务说明.md及结果schema.json，以及protocol内同版手册和说明。你的coder字段填{coder}，不要访问另一方目录或admin。按包编号分别提交结果，逐包保留首次记录。\n")
    write(ADMIN / "confirmation_packet_freeze.json", {"status": "v9_answer_free_materials_frozen_ready_for_independent_AI_coding", "created_at": datetime.datetime.now().astimezone().isoformat(), "material_version": "v9", "per_coder_n": design_data["total_n_per_coder"], "sampling_design_sha256": sha(ADMIN / "confirmation_sampling_PRIVATE.json"), "sampling_freeze_sha256": sha(ADMIN / "confirmation_sampling_freeze.json"), "mapping_sha256": sha(ADMIN / "PRIVATE_mapping.json"), "v8_v9_ID_and_current_text_unchanged": True, "entire_canonical_frame_unit_text_SHA_unchanged": True, "rule_LLM_same_v9_unit_and_context": True, "source_sha256": {str(p): sha(p) for p in [R3 / "effective_blind_inputs_v9.jsonl", R3 / "rule_inputs_shared_v9.jsonl", R3 / "material_v9_manifest.json", protocol_dir / "完整五维手册-v1.3.md", protocol_dir / "共用操作说明-v1.4.md", confirmation / "任务说明.md", confirmation / "结果schema.json"]}, "packets": packet_hashes, "no_reference_or_machine_labels_in_packets": True, "human_validation_completed": False, "coding_results_created": False})
    print(json.dumps({"material_version": "v9", "per_coder_n": design_data["total_n_per_coder"], "packet_count": len(packet_hashes), "freeze": str(ADMIN / "confirmation_packet_freeze.json")}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["design", "packets"])
    args = parser.parse_args()
    design() if args.phase == "design" else packets()
