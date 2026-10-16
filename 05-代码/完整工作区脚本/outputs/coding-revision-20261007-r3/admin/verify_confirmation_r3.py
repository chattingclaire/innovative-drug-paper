"""Independent reconstruction QA for r3 sampling and answer-free v9 packets."""
import ast
import collections
import datetime
import hashlib
import json
import math
import random
import re
import unicodedata
from pathlib import Path

R3 = Path(__file__).resolve().parents[1]
R2 = R3.parent / "agent-validation-20261007-r2"
OLD = R3.parent / "recall-revision-20261007"
ADMIN = R3 / "admin"


def read(path):
    return json.loads(Path(path).read_text())


def jl(path):
    return {r["id"]: r for r in [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(text):
    return "".join(c for c in unicodedata.normalize("NFKC", text) if not c.isspace() and unicodedata.category(c)[0] != "P")


def all_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from all_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_keys(item)


def main():
    design = read(ADMIN / "confirmation_sampling_PRIVATE.json")
    exclusion = read(ADMIN / "confirmation_exclusion_evidence_PRIVATE.json")
    frame_record = read(ADMIN / "confirmation_canonical_frame_PRIVATE.json")
    mapping_rows = read(ADMIN / "PRIVATE_mapping.json")
    sampling_freeze = read(ADMIN / "confirmation_sampling_freeze.json")
    packet_freeze = read(ADMIN / "confirmation_packet_freeze.json")
    assert sampling_freeze["design_sha256"] == packet_freeze["sampling_design_sha256"] == sha(ADMIN / "confirmation_sampling_PRIVATE.json")
    assert sampling_freeze["mapping_sha256"] == packet_freeze["mapping_sha256"] == sha(ADMIN / "PRIVATE_mapping.json")
    assert sha(ADMIN / "confirmation_canonical_frame_PRIVATE.json") == sampling_freeze["frame_sha256"]
    assert sha(ADMIN / "confirmation_exclusion_evidence_PRIVATE.json") == sampling_freeze["exclusion_evidence_sha256"]
    assert all(sha(path) == digest for path, digest in sampling_freeze["source_sha256"].items())
    assert all(sha(path) == digest for path, digest in packet_freeze["source_sha256"].items())
    assert sha(ADMIN / "prepare_confirmation_r3.py") == sampling_freeze["prepared_script_sha256"]
    units8 = jl(R2 / "effective_blind_inputs_v8.jsonl")
    units = jl(R3 / "effective_blind_inputs_v9.jsonl")
    rules = jl(R3 / "rule_inputs_shared_v9.jsonl")
    assert set(units8) == set(units) == set(rules)
    assert all(units8[rid]["text"] == units[rid]["text"] for rid in units)
    assert all(rules[rid]["input"]["unit_text"] == row["text"] and rules[rid]["input"]["llm_v29_shared_context"] == row["contexts"] for rid, row in units.items())
    metadata_path = Path(read(OLD / "三部门注意力分布与敏感性.json")["method_bindings"]["metadata"])
    metadata = {Path(r["original_file"]).stem: r["analysis_group"] for r in read(metadata_path)["rows"]}
    groups = {rid: metadata[r["input"]["original_file_stem"]] for rid, r in rules.items()}
    prior = read(R2 / "admin/sampling_design.json")
    future = read(R2 / "admin/future_human_v2_sampling_PRIVATE.json")
    assert set(exclusion["categories"]["historical_known_development"]) == set(prior["excluded_ids"])
    assert set(exclusion["categories"]["r2_all_300_now_development"]) == {r["original_id"] for r in prior["sample"]}
    assert set(exclusion["categories"]["reserved_future_real_human_v2"]) == {r["original_id"] for r in future["sample"]}
    reconstructed_controls = set()
    for entry in exclusion["source_file_manifest"]:
        path = Path(entry["path"])
        assert sha(path) == entry["sha256"]
        assert path.suffix in {".py", ".patch"} or path.name == "test_following_list_certificates.json"
        source = path.read_text()
        reconstructed_controls.update(re.findall(r"RECODE25-\d{5}\b", source))
        if path.suffix == ".py":
            tree = ast.parse(source)
            constants = [n for n in ast.walk(tree) if isinstance(n, ast.Constant)]
            if any(n.value == "RECODE25-" for n in constants):
                reconstructed_controls.update("RECODE25-" + n.value for n in constants if isinstance(n.value, str) and re.fullmatch(r"\d{5}", n.value))
    reconstructed_controls &= set(units)
    assert reconstructed_controls == set(exclusion["categories"]["explicit_legacy_rule_regression_control_IDs"])
    excluded = set.union(*(set(ids) for ids in exclusion["categories"].values()))
    assert excluded == set(exclusion["excluded_original_ID_union"])
    blocked = {norm(units[rid]["text"]) for rid in excluded if rid in units}
    remaining_families = collections.defaultdict(list)
    for rid in units:
        if groups[rid] in {"NMPA", "NHSA", "NHC"} and rid not in excluded and norm(units[rid]["text"]) not in blocked:
            remaining_families[norm(units[rid]["text"])].append(rid)
    cross = {key for key, ids in remaining_families.items() if len({groups[rid] for rid in ids}) > 1}
    frame = {g: {} for g in ("NMPA", "NHSA", "NHC")}
    for fingerprint, members in remaining_families.items():
        if fingerprint not in cross:
            representative = min(members)
            frame[groups[representative]][representative] = sorted(members)
    assert {g: len(rows) for g, rows in frame.items()} == design["frame_N_by_group"] == {"NMPA": 947, "NHSA": 760, "NHC": 60}
    for group, records in frame_record["frame_by_group"].items():
        assert {r["canonical_id"]: r["all_remaining_family_members"] for r in records} == frame[group]
        assert all(hashlib.sha256(units[r["canonical_id"]]["text"].encode()).hexdigest() == r["unit_text_sha256"] for r in records)
    probability = [r for r in design["sample"] if r["component"] == "probability_canonical"]
    challenge = [r for r in design["sample"] if r["component"] == "enriched_challenge"]
    assert len(probability) == 180 and len(challenge) == 60
    assert collections.Counter(r["group"] for r in probability) == {"NMPA": 60, "NHSA": 60, "NHC": 60}
    assert collections.Counter(r["group"] for r in challenge) == {"NMPA": 30, "NHSA": 30}
    rng = random.Random(2026100761)
    replay = []
    for group in ("NMPA", "NHSA", "NHC"):
        F = len(frame[group])
        replay.extend(rng.sample(sorted(frame[group]), min(60, F)))
    assert replay == [r["original_id"] for r in probability]
    for row in probability:
        F, n = len(frame[row["group"]]), min(60, len(frame[row["group"]]))
        assert row["canonical_frame_N"] == F and row["sample_n"] == n
        assert math.isclose(row["inclusion_probability"], n / F, rel_tol=1e-13)
        assert math.isclose(row["analysis_weight"], F / n, rel_tol=1e-13)
    old_rule = jl(R2 / "rules-v32/material-adapter-v32.1/all_predictions_material_v8.jsonl")
    old_llm = jl(R2 / "llm-v31/sealed-final-material-v8/all_predictions_composite.jsonl")
    probability_ids = {r["original_id"] for r in probability}
    replay_challenge = []
    for group in ("NMPA", "NHSA"):
        remaining = sorted(set(frame[group]) - probability_ids)
        primary = [rid for rid in remaining if any(old_rule[rid]["prediction"]["labels"][d] == 1 or old_llm[rid]["labels"][d] == 1 for d in ("I", "F"))]
        broad = [rid for rid in remaining if any(old_rule[rid]["prediction"]["labels"][d] == 1 or old_llm[rid]["labels"][d] == 1 for d in ("S", "E", "Ec", "I", "F"))]
        recorded = design["challenge_pool_details_PRIVATE"][group]
        assert recorded["primary_old_rule_or_LLM_I_F_positive_pool"] == primary
        assert recorded["fallback_any_five_positive_pool"] == broad
        first = rng.sample(primary, min(30, len(primary)))
        fallback = rng.sample([rid for rid in broad if rid not in first], min(30 - len(first), len([rid for rid in broad if rid not in first])))
        replay_challenge.extend(first + fallback)
    assert replay_challenge == [r["original_id"] for r in challenge]
    assert all(r["analysis_weight"] is None and r["inclusion_probability"] is None for r in challenge)
    selected = {r["original_id"] for r in design["sample"]}
    assert len(selected) == len({norm(units[rid]["text"]) for rid in selected}) == 240
    assert not selected & excluded and not {norm(units[rid]["text"]) for rid in selected} & blocked
    assert all(rid in frame[row["group"]] for row in design["sample"] for rid in [row["original_id"]])
    mapping = {(r["coder"], r["blind_id"]): r for r in mapping_rows}
    assert len(mapping) == 480
    orders, counts, banned_keys = {}, {}, []
    for coder in "AC":
        paths = sorted((R3 / f"confirmation/agent-{coder}").glob("材料-*.json"))
        assert len(paths) == 8
        rows = []
        for path in paths:
            assert sha(path) == packet_freeze["packets"][str(path.relative_to(R3))]
            packet = read(path)
            assert packet["material_version"] == "v9" and len(packet["rows"]) == 30
            # A source certificate legitimately uses component for a policy
            # attachment/program; row-level keys below rule out sampling-arm
            # metadata without confusing it with source-structure metadata.
            banned_keys += [{"packet": str(path), "key": key} for key in all_keys(packet) if re.search(r"label|prediction|gold|judgment|reason|answer|adjudicat|expected|subtype|quality_basis|analysis_weight|inclusion_probability", key, re.I)]
            rows.extend(packet["rows"])
        assert len(rows) == len({r["id"] for r in rows}) == 240
        order = []
        for row in rows:
            item = mapping[coder, row["id"]]
            rid = item["original_id"]
            order.append(rid)
            assert set(row) == {"id", "text", "source_title", "pages", "contexts", "context_usage"}
            assert all(row[key] == units[rid][key] for key in ("text", "source_title", "pages", "contexts", "context_usage"))
            assert hashlib.sha256(row["text"].encode()).hexdigest() == item["unit_text_sha256"]
        expected_order = [r["original_id"] for r in design["sample"]]
        random.Random(design["coder_order_seeds"][coder]).shuffle(expected_order)
        assert order == expected_order and set(order) == selected
        orders[coder] = order
        counts[coder] = {"packets": 8, "rows_per_packet": 30, "rows": 240}
    assert not banned_keys and orders["A"] != orders["C"]
    assert sha(R3 / "protocol/完整五维手册-v1.3.md") == sha(R2 / "protocol/完整五维手册-v1.3.md")
    assert sha(R3 / "protocol/共用操作说明-v1.4.md") == sha(R2 / "共用操作说明-v1.4.md")
    instruction = (R3 / "confirmation/任务说明.md").read_text()
    schema_text = (R3 / "confirmation/结果schema.json").read_text()
    assert not any(term in instruction + schema_text for term in ("0.80", "0.8", "κ", "F1", "精确率", "召回率", "预期部门排序"))
    assert not list((R3 / "confirmation").rglob("结果-*.json"))
    reserved_freeze = read(R2 / "admin/future_human_v2_freeze.json")
    assert all(sha(R2 / name) == digest for name, digest in reserved_freeze["package_sha256"].items())
    report = {"status": "pass_canonical_frame_sampling_and_answer_free_v9_packet_QA", "created_at": datetime.datetime.now().astimezone().isoformat(), "auditor": "AI preparation/integrity agent; no labels authored", "material_version": "v9", "entire_v8_v9_ID_and_text_frame_unchanged": True, "all_rule_LLM_texts_contexts_identical": True, "all_canonical_IDs_are_lexicographic_minimum": True, "frame_N_by_group": design["frame_N_by_group"], "probability_n_by_group": design["probability_sample_n_by_group"], "challenge_n_by_group": design["challenge_sample_n_by_group"], "explicit_control_IDs_excluded": len(reconstructed_controls), "control_source_file_hashes_valid": True, "control_sources_not_machine_full_outputs": True, "additional_same_text_IDs_excluded": len(exclusion["additional_same_normalized_text_IDs"]), "cross_department_families_excluded": len(cross), "sample_seed_replay_matches": True, "probability_formula_recomputed": "pi=n/F; weight=F/n for canonical representative frame only", "NHC_remaining_canonical_frame_census": True, "challenge_selection_old_labels_only_replay_matches": True, "challenge_pooled_with_probability": False, "selected_ID_or_normalized_current_text_overlap_with_excluded": 0, "internal_normalized_current_text_duplicates": 0, "packages": counts, "A_C_same_v9_materials_different_order_IDs": True, "banned_answer_component_or_weight_keys_found_in_packets": [], "task_schema_no_expected_metrics_or_department_order": True, "handbook_and_operational_hashes_unchanged": True, "future_real_human_v2_package_bytes_unchanged": True, "no_r3_method_or_new_results_inspected": True, "coding_results_exist": False, "source_freeze_sha256": sha(ADMIN / "confirmation_sampling_freeze.json"), "packet_freeze_sha256": sha(ADMIN / "confirmation_packet_freeze.json"), "limits": ["Inference applies only to the remaining canonical unique-clause representative frame, not all4481 units, not other family members and not excluded policies.", "Same-source adjacent/parent/shared context may previously have been seen; current-unit normalized text-family exclusion does not imply fully unseen context or new-document external validation.", "The60 enriched challenge cases use old r2 machine outputs solely for pool selection and must be reported separately; they do not estimate population prevalence or accuracy.", "This package has no completed AI/human judgments. AI procedural blindness is to other coders and machine judgments; source titles or wording can identify departments."]}
    path = ADMIN / "confirmation_independent_QA.json"
    assert not path.exists()
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (ADMIN / "confirmation_sampling_scope.md").write_text("""# r3确认抽样与材料范围

以r2 v8当前原句锁定正文族和代表框，再核对v9全部ID/原句未变，以v9完整语境生成正式包。规范化为NFKC后去空白和Unicode标点；排除历史已知开发、r2全部300、保留未来真人v2的240及其相同正文族，再排除旧规则/测试源中明确RECODE控制ID及相同正文族。源凭据包含文件SHA、行号和明确引用，不将全量机器输出的所有ID视为开发。跨部门共享剩余正文族整体排除，本轮实际0族。

每个剩余正文族预先取字典序最小原ID为canonical代表。药监947、医保760、卫健60个代表中分别简单随机不放回抽60，共180；卫健是剩余代表框全取。逐条概率n/F、权重F/n，只推断该canonical独特条款代表框，不能推断4481总体或正文族其他成员。固定seed2026100761可重放。

从未抽代表中，按封存r2旧规则或LLM的I/F阳性池，药监和医保各随机取30，共60，另列挑战诊断。必要时才由任一五维阳性补足；不为卫健硬凑挑战，不把挑战样本混入概率总体指标。

两位agent各240条、各8包×30条，原文和完整v9语境相同、匿名编号和顺序不同。材料不含参考/机器标签、样本用途、权重或预期指标；任务和schema不含预期指标或部门排序。手册v1.3与说明v1.4复制字节不变。未生成编码结果，未启动盲评，未读取r3新规则或提示结果。

同源相邻、父级或共享语境可能已有接触。严格去重对象是当前单元规范化正文族，不能称全部语境未接触、新政策文件外部验证或真人验证。设计与排除凭据为PRIVATE；编码员只读自己材料、任务/schema及指定手册。
""")
    print(json.dumps({"status": report["status"], "frame_N_by_group": design["frame_N_by_group"], "per_coder_n": 240, "packets": 16, "QA": str(path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
