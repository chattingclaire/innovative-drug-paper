#!/usr/bin/env python3
"""未来冻结材料的盲包/格式核验/首判封存工具。仅 stdlib；不抽样，不编码，不算分。"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import random
import re
import shutil
import sys
import tempfile

VERSION = "human-workflow-draft-1"
DIMS = ("S", "E", "Ec", "I", "F")
HEX = re.compile(r"^[0-9a-f]{64}$")
SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
CTX = re.compile(r"^CTX-[A-Za-z0-9_-]+$")
KINDS = set("paragraph preceding_paragraph source_paragraph structural_relation heading ordered_list ordered_members boundary_container boundary parent_paragraph source_fragment table_header_cell table_header supplemental_group cited_reference_group cited_reference cited_article document_context table_row_cell table_row source_list list_parent component cited_section application_scope source_chapter_heading following_heading table_group_row preceding_flattened_table_data_row".split())
STRUCT_KEYS = set("sequence_index paragraph_id pages source_lines relation_id related_context_ids unit_id child_groups parent_context_id candidate_line_ids first_paragraph last_paragraph line_ids position next_paragraph_id text_child_context_ids first_paragraph_id last_paragraph_id physical_pages source_role component_id candidate_paragraph_id candidate_paragraph_start candidate_paragraph_end column_index table_text_context_ids source_unit_id current_unit_id reference_address next_candidate_paragraph_id article component_first_paragraph component_last_paragraph row_index_zero_based column_indices row_cell_column_pairs image_evidence_ref target_paragraph_id paragraph_ids related_unit_ids section line source_pages scope_context_ids follows_context_id physical_grid_row_index_zero_based physical_merged_cells source_group_context_id geometry".split())
# 这些是本草案明确声明的结构接口扩展，不声称已冻结为研究标准。
NESTED_KEYS = set("ordered_context_ids position cell_index column_index header_index row_index row_span column_span start_row end_row start_column end_column attachment_id physical_page bbox x y width height text context_id source_ref".split())
CONTEXT_REFS = {"related_context_ids", "parent_context_id", "text_child_context_ids", "table_text_context_ids", "scope_context_ids", "follows_context_id", "ordered_context_ids", "source_group_context_id", "context_id"}
LOC_KEYS = set("physical_pages printed_pages paragraph_ids line_ids article table_cell source_url snapshot_attachment_id".split())
RESULT_KEYS = set("labels label predictions prediction expected gold reference_label rule_hit score scores confidence dimension_reasons innovation_subtypes fairness_subtypes original_coder_answer sampling_stratum weight pi development_rationale verified_context_certificates".split())
MIME_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif", "application/pdf": ".pdf"}
CODER_GUIDE = """本包只有未填表，无预置答案。先读同版完整 manual.md，再逐条当前命题及必要 CTX/原图。
填写 S/E/Ec/I/F：材料完整未达判据为0，实质涉及为1；关键原文/指代/结构缺失或真实规则冲突为null并具体请求。
逐维保存当前连续引文、实际语境引文/图位置与关系理由；I3与具体F另列必要路径证据。
空白行unfilled的null只是占位；完成行改complete，完成的null必须有具体原因。
凡有附件均实际打开，记录attachment_id、SHA和真实查看时间；不从整篇目的继承标签。
只看自己的本包与共同手册，不看机器、旧标签、对方答案或管理员映射，不请AI生成标签，不外查。
向管理员提中性补材请求；双方同步同版补材，首判不覆盖，重判另轮。
实际身份、独立声明、AI参与和开发接触如实填报；AI草稿经真人复核不能称真人独立首判。
全部五维填完后提交labels.jsonl及submission.json，原字节先封存，再进行讨论与另存裁定。
脚本格式通过不证明真人身份、独立执行或语义正确。完整执行规则另见管理员共同交付的真人操作说明。
"""


class ContractError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ContractError(message)


def exact(obj, required, optional=(), where="object"):
    require(isinstance(obj, dict), f"{where}: 应为对象")
    require(set(required) <= obj.keys(), f"{where}: 缺字段 {sorted(set(required)-obj.keys())}")
    require(obj.keys() <= set(required) | set(optional), f"{where}: 未许可字段 {sorted(obj.keys()-set(required)-set(optional))}")


def string(value, where, nonempty=True):
    require(isinstance(value, str) and (not nonempty or bool(value.strip())), f"{where}: 应为{'非空' if nonempty else ''}字符串")


def sha(value, where):
    require(isinstance(value, str) and HEX.fullmatch(value), f"{where}: SHA256格式错误")


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def load_json(path):
    # 重复键与非有限JSON数字拒收，避免一个解析器看见另一答案。
    def pairs(items):
        d = {}
        for k, v in items:
            require(k not in d, f"重复JSON键 {k}")
            d[k] = v
        return d
    def bad_constant(x):
        raise ContractError(f"非标准JSON数字 {x}")
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=bad_constant)


def load_lines(path):
    rows = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        require(bool(line.strip()), f"{path}:{n}: 空行不作为记录")
        # 单行也使用相同严格解析器，且不写临时研究材料。
        def pairs(items):
            d = {}
            for k, v in items:
                require(k not in d, f"{path}:{n}: 重复键 {k}")
                d[k] = v
            return d
        rows.append(json.loads(line, object_pairs_hook=pairs,
                               parse_constant=lambda x: (_ for _ in ()).throw(ContractError(f"非法数字 {x}"))))
    return rows


def put(path, data, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def put_json(path, obj, mode=0o600):
    put(path, json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8") + b"\n", mode)


def put_lines(path, rows):
    put(path, b"".join(canonical(r) + b"\n" for r in rows))


def local_file(root, rel):
    require(isinstance(rel, str) and "\\" not in rel, "资产路径只能是相对POSIX路径")
    q = PurePosixPath(rel)
    require(not q.is_absolute() and q.parts and all(x not in (".", "..") for x in q.parts), "资产路径越界")
    root = Path(root).resolve()
    path = root.joinpath(*q.parts)
    cursor = root
    for part in q.parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), "拒绝符号链接资产")
    require(path.is_file() and path.resolve().is_relative_to(root), "资产缺失或越界")
    return path


def reject_results(value, where="source"):
    # 只检查字段名；原文中的“标签”“分数”等政策用语不删除、不改写。
    if isinstance(value, dict):
        for key, v in value.items():
            k = key.lower()
            require(k not in RESULT_KEYS and not k.startswith(("machine_", "prediction_", "old_label", "expected_", "gold_")), f"{where}: 禁止结果字段 {key}")
            reject_results(v, f"{where}.{key}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            reject_results(v, f"{where}[{i}]")


def source_ref(value, originals):
    exact(value, ("source_sha256", "source_locator", "provenance_status"), where="source_ref")
    status = value["provenance_status"]
    require(status in ("binary_source_verified", "derived_mapping_verified", "unresolved"), "来源状态无效")
    digest = value["source_sha256"]
    if digest is not None:
        sha(digest, "source_ref.source_sha256")
        require(digest in originals, "来源SHA未绑定本冻结包原始二进制")
    if status != "unresolved":
        require(digest is not None, "已核来源须绑定实际原始二进制SHA")
    locator = value["source_locator"]
    exact(locator, (), LOC_KEYS, "source_locator")
    require(bool(locator), "来源位置不可为空")
    for key, v in locator.items():
        if key in ("physical_pages", "printed_pages", "paragraph_ids", "line_ids"):
            require(isinstance(v, list) and bool(v), f"{key}: 位置清单应非空")
            if key == "physical_pages":
                require(all(type(x) is int and x >= 1 for x in v), "物理页码须为1起整数")
            else:
                require(all(isinstance(x, (str, int)) and not isinstance(x, bool) for x in v), "位置元素类型错误")
        else:
            require(v is None or isinstance(v, (str, int)) and not isinstance(v, bool), f"{key}: 类型错误")


def nested_structure(value, ids, attachment_ids, originals, top=True):
    if isinstance(value, dict):
        permitted = STRUCT_KEYS if top else NESTED_KEYS
        require(value.keys() <= permitted, f"未冻结结构字段 {sorted(value.keys()-permitted)}；须显式修订接口，不丢弃")
        for k, v in value.items():
            if k == "source_ref":
                source_ref(v, originals)
                continue
            if k in CONTEXT_REFS and v is not None:
                refs = v if isinstance(v, list) else [v]
                require(all(isinstance(x, str) and x in ids for x in refs), f"结构语境引用断链: {k}")
            if k in ("image_evidence_ref", "attachment_id") and v is not None:
                require(isinstance(v, str) and v in attachment_ids, "结构图片引用断链")
            if k in ("unit_id", "source_unit_id", "current_unit_id", "related_unit_ids"):
                refs = v if isinstance(v, list) else [v]
                require(all(isinstance(x, str) and (x == "CURRENT_UNIT" or re.fullmatch(r"NU-[A-Za-z0-9_-]+", x)) for x in refs), "可见结构unit引用应为中性编号，不得带旧记录ID")
            nested_structure(v, ids, attachment_ids, originals, top=False)
    elif isinstance(value, list):
        for item in value:
            nested_structure(item, ids, attachment_ids, originals, top=False)
    else:
        require(value is None or isinstance(value, (str, int, float, bool)), "结构含不可序列化对象")


def validate_record(row, originals, assets):
    reject_results(row)
    exact(row, ("record_id", "unit_text", "unit_source_ref", "source_title", "contexts", "attachments", "material_status", "neutral_material_note"), where="source_record")
    string(row["record_id"], "record_id")
    string(row["unit_text"], "unit_text")
    require(row["source_title"] is None or isinstance(row["source_title"], str), "source_title类型错误")
    require(row["neutral_material_note"] is None or isinstance(row["neutral_material_note"], str), "neutral_material_note类型错误")
    require(row["material_status"] in ("ready", "source_reference_pending", "context_provenance_pending", "parse_failure"), "材料状态错误")
    if row["material_status"] != "ready":
        require(bool(row["neutral_material_note"]), "待补材料必须有中性问题说明")
    require(isinstance(row["contexts"], list) and isinstance(row["attachments"], list), "语境/附件应为数组")
    source_ref(row["unit_source_ref"], originals)
    ids = {c.get("context_id") for c in row["contexts"]}
    require(len(ids) == len(row["contexts"]) and all(isinstance(x, str) and CTX.fullmatch(x) for x in ids), "语境中性ID重复或格式错误")
    aids = {a.get("attachment_id") for a in row["attachments"]}
    require(len(aids) == len(row["attachments"]) and all(isinstance(x, str) and re.fullmatch(r"ASSET-[A-Za-z0-9_-]+", x) for x in aids), "附件ID重复或格式错误")
    for a in row["attachments"]:
        exact(a, ("attachment_id", "sha256", "kind", "source_ref"), where="attachment")
        sha(a["sha256"], "attachment.sha256")
        require(a["kind"] in ("original_source_page", "table_crop", "diagram_crop"), "附件类型错误")
        require(a["sha256"] in assets and assets[a["sha256"]]["mime_type"].startswith("image/"), "原页图片资产未完整绑定")
        source_ref(a["source_ref"], originals)
    for c in row["contexts"]:
        exact(c, ("context_id", "kind", "structure", "source_ref"), ("text", "headers", "title", "row_cells", "caption"), "context")
        require(c["kind"] in KINDS, "未许可context.kind；须显式修订接口")
        for k in ("text", "title", "caption"):
            require(c.get(k) is None or isinstance(c.get(k), str), f"context.{k}类型错误")
        source_ref(c["source_ref"], originals)
        require(isinstance(c["structure"], dict), "structure应为对象；无text节点不得删除")
        nested_structure(c["structure"], ids, aids, originals)
        for key in ("headers", "row_cells"):
            if key in c:
                nested_structure(c[key], ids, aids, originals, top=False)
    unresolved = row["unit_source_ref"]["provenance_status"] == "unresolved"
    unresolved |= any(c["source_ref"]["provenance_status"] == "unresolved" for c in row["contexts"])
    unresolved |= any(a["source_ref"]["provenance_status"] == "unresolved" for a in row["attachments"])
    require(not unresolved or row["material_status"] != "ready", "未核来源不可伪装ready")


def neutral(row):
    # 不挑选语境，不排除无text结构，不从标题推导维度。
    return copy.deepcopy({k: row[k] for k in ("unit_text", "unit_source_ref", "source_title", "contexts", "attachments")})


def content_sha(row):
    return sha_bytes(canonical(neutral(row)))


def read_source(root):
    root = Path(root)
    manifest_path = root / "source-manifest.json"
    m = load_json(manifest_path)
    reject_results(m)
    exact(m, ("schema_version", "status", "purpose", "records_file", "records_sha256", "record_count", "assets", "original_sources", "context_selection_version"), where="source_manifest")
    require(m["schema_version"] == "neutral-source-draft-1" and m["status"] == "frozen", "只接受此接口的冻结来源包")
    require(m["purpose"] in ("independent_validation", "toy"), "来源用途错误")
    string(m["context_selection_version"], "context_selection_version")
    records_file = local_file(root, m["records_file"])
    sha(m["records_sha256"], "records_sha256")
    require(sha_file(records_file) == m["records_sha256"], "来源JSONL字节SHA不符")
    originals, assets = {}, {}
    for kind, dest in (("assets", assets), ("original_sources", originals)):
        require(isinstance(m[kind], list), f"{kind}应为清单")
        for a in m[kind]:
            exact(a, ("sha256", "relative_path", "mime_type"), where=kind)
            sha(a["sha256"], "asset.sha256")
            require(a["sha256"] not in dest, "同类资产SHA重复")
            require(a["mime_type"] in MIME_EXT, "未许可资产mime")
            f = local_file(root, a["relative_path"])
            require(sha_file(f) == a["sha256"], "原始来源/图片实际字节SHA不符")
            dest[a["sha256"]] = dict(a, path=f)
    rows = load_lines(records_file)
    require(type(m["record_count"]) is int and len(rows) == m["record_count"], "来源记录数不符")
    byid = {}
    for r in rows:
        validate_record(r, originals, assets)
        require(r["record_id"] not in byid, "来源record_id重复")
        byid[r["record_id"]] = r
    return m, byid, assets, originals, sha_file(manifest_path)


def check_draw(d, source_sha, source_ids, manual_sha, purpose, codes):
    exact(d, ("schema_version", "status", "purpose", "sampling_execution", "draw_id", "round_id", "parent_round_id", "source_manifest_sha256", "manual_sha256", "manual_version", "manual_status", "statistical_plan_sha256", "selected_record_ids", "presentation_seeds", "executors", "design_rows"), where="draw_manifest")
    require(d["schema_version"] == "frozen-draw-draft-1" and d["status"] == "frozen", "抽样清单须事前冻结")
    require(d["sampling_execution"] == "completed", "工具不执行抽样；须输入已经完成的抽样/全核名单")
    require(d["purpose"] == purpose, "来源/抽样用途不一致")
    require(d["source_manifest_sha256"] == source_sha and d["manual_sha256"] == manual_sha, "抽样绑定来源/手册SHA不符")
    require(d["manual_status"] == "frozen", "开发手册不能冒称最终冻结手册")
    sha(d["statistical_plan_sha256"], "statistical_plan_sha256")
    for k in ("draw_id", "round_id", "manual_version"):
        string(d[k], k)
    require(SAFE.fullmatch(d["round_id"]), "round_id需安全目录名")
    require(d["parent_round_id"] is None or isinstance(d["parent_round_id"], str), "parent_round_id错误")
    ids = d["selected_record_ids"]
    require(isinstance(ids, list) and len(ids) >= 2 and len(set(ids)) == len(ids), "本异序接口至少需2个互异入选ID；不是研究样本量门槛")
    require(set(ids) <= set(source_ids), "入选ID缺来源记录")
    exact(d["presentation_seeds"], ("A", "B"), where="presentation_seeds")
    require(all(isinstance(v, str) and v for v in d["presentation_seeds"].values()), "呈现seed应为非空字符串")
    require(d["presentation_seeds"]["A"] != d["presentation_seeds"]["B"], "呈现seed应分别固定")
    exact(d["executors"], ("A", "B"), where="executors")
    require(codes[0] != codes[1] and all(SAFE.fullmatch(x) for x in codes), "执行者匿名代号应安全且互异")
    for side, code in zip(("A", "B"), codes):
        e = d["executors"][side]
        exact(e, ("anonymous_code", "assignment_status", "identity_registry_sha256"), where="executor_assignment")
        require(e["anonymous_code"] == code, "匿名代号不符合冻结执行者分配")
        sha(e["identity_registry_sha256"], "identity_registry_sha256")
        require(e["assignment_status"] == ("confirmed_real_human" if purpose == "independent_validation" else "synthetic_toy"), "真实人未落实不得发独立真人包")
    require(isinstance(d["design_rows"], list), "design_rows应为管理员清单")
    require({r.get("record_id") for r in d["design_rows"]} == set(ids) and len(d["design_rows"]) == len(ids), "设计信息与名单不一一对应")
    for r in d["design_rows"]:
        exact(r, ("record_id", "department", "family_id", "stratum", "N_h", "n_h", "pi", "weight"), where="design_row")
        for key in ("record_id", "department", "family_id", "stratum"):
            string(r[key], "design_row." + key)
        for k in ("N_h", "n_h"):
            require(type(r[k]) is int and r[k] >= 1, "N_h/n_h应为正整数")
        require(r["n_h"] <= r["N_h"], "n_h大于N_h")
        require(type(r["pi"]) in (int, float) and abs(r["pi"] - r["n_h"] / r["N_h"]) < 1e-12, "pi须绑定既定设计")
        require(type(r["weight"]) in (int, float) and abs(r["weight"] - 1 / r["pi"]) < 1e-10, "weight须为1/pi")
    strata = {}
    for r in d["design_rows"]:
        key = (r["department"], r["stratum"])
        group = strata.setdefault(key, [])
        group.append(r)
    for group in strata.values():
        require(len({(r["N_h"], r["n_h"]) for r in group}) == 1, "同层N_h/n_h不一致")
        require(len(group) == group[0]["n_h"], "锁定名单的实际层样本数不等于n_h")
    return ids


def blank_row(p):
    return {"blind_id": p["blind_id"], "content_sha256": p["content_sha256"], "completion_status": "unfilled",
            "dimensions": {dim: {"value": None, "evidence_path": None, "current_quote": None,
                                  "context_quotes": [], "image_evidence": [], "reason": None,
                                  "path_evidence": {}, "material_requests": []} for dim in DIMS},
            "viewed_attachments": []}


def orders(ids, seeds):
    out = {}
    for side in ("A", "B"):
        order = sorted(ids)
        seed = int.from_bytes(hashlib.sha256(seeds[side].encode()).digest(), "big")
        random.Random(seed).shuffle(order)
        out[side] = order
    collision = out["A"] == out["B"]
    if collision:
        out["B"] = out["B"][1:] + out["B"][:1]
    return out, collision


def build(source_root, draw_path, manual_path, codes, output):
    output = Path(output)
    require(not output.exists(), "输出轮次已存在；禁止覆盖，补材重判另建round")
    require(not output.parent.is_symlink(), "输出父路径不得为符号链接")
    m, records, assets, originals, source_sha = read_source(source_root)
    d = load_json(draw_path)
    manual_sha = sha_file(manual_path)
    ids = check_draw(d, source_sha, records, manual_sha, m["purpose"], codes)
    ordered, collision = orders(ids, d["presentation_seeds"])
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    build_lock = output.parent / ("." + output.name + ".build.lock")
    lock_fd = os.open(build_lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    os.close(lock_fd)
    staging = Path(tempfile.mkdtemp(prefix=".build-", dir=output.parent))
    try:
        admin_rows = {r["record_id"]: dict(r) for r in d["design_rows"]}
        packets = {}
        for side, code in zip(("A", "B"), codes):
            folder = staging / ("coder-" + side)
            folder.mkdir(mode=0o700)
            packet = []
            for i, rid in enumerate(ordered[side], 1):
                r = records[rid]
                p = dict(neutral(r), packet_version=VERSION, manual_version=d["manual_version"],
                         blind_id=f"{side}-{i:06d}", material_status=r["material_status"],
                         neutral_material_note=r["neutral_material_note"], content_sha256=content_sha(r))
                packet.append(p)
                admin_rows[rid][side + "_blind_id"] = p["blind_id"]
                admin_rows[rid]["content_sha256"] = p["content_sha256"]
            put_lines(folder / "packet.jsonl", packet)
            put(folder / "manual.md", Path(manual_path).read_bytes())
            put(folder / "操作提示.txt", CODER_GUIDE.encode("utf-8"))
            needed = {a["sha256"] for p in packet for a in p["attachments"]}
            visible_assets = []
            for digest in sorted(needed):
                a = assets[digest]
                rel = "source-assets/" + digest + MIME_EXT[a["mime_type"]]
                put(folder / rel, a["path"].read_bytes())
                visible_assets.append({"sha256": digest, "relative_path": rel, "mime_type": a["mime_type"]})
            packet_manifest = {"schema_version": VERSION, "purpose": m["purpose"], "round_id": d["round_id"],
                               "parent_round_id": d["parent_round_id"], "side": side, "executor_code": code,
                               "identity_registry_sha256": d["executors"][side]["identity_registry_sha256"],
                               "manual_version": d["manual_version"], "manual_sha256": manual_sha,
                               "packet_sha256": sha_file(folder / "packet.jsonl"), "record_count": len(packet),
                               "dimension_count": len(packet) * 5, "assets": visible_assets,
                               "content_set_sha256": sha_bytes(canonical(sorted(p["content_sha256"] for p in packet)))}
            put_json(folder / "packet-manifest.json", packet_manifest)
            put_lines(folder / "labels.blank.jsonl", [blank_row(p) for p in packet])
            put_json(folder / "submission.blank.json", {"schema_version": VERSION, "state": "unfilled",
                     "purpose": m["purpose"], "round_id": d["round_id"], "executor_code": code,
                     "actual_actor_type": "pending", "identity_registry_sha256": None,
                     "manual_sha256": manual_sha, "packet_sha256": packet_manifest["packet_sha256"],
                     "labels_sha256": None, "record_count": len(packet), "dimension_count": len(packet)*5,
                     "started_at": None, "submitted_at": None, "independence_declaration": None,
                     "AI_assistance": None, "prior_development_exposure": None,
                     "material_request_count": None, "image_view_attestation": None})
            packets[side] = packet_manifest
        require(packets["A"]["content_set_sha256"] == packets["B"]["content_set_sha256"], "A/B来源内容不一致")
        admin = staging / "admin-private"
        admin.mkdir(mode=0o700)
        put_json(admin / "mapping.json", {"purpose": m["purpose"], "round_id": d["round_id"],
                 "tool_version": VERSION, "tool_sha256": sha_file(__file__), "python_version": sys.version,
                 "source_manifest_sha256": source_sha, "draw_manifest_sha256": sha_file(draw_path),
                 "manual_sha256": manual_sha, "source_records_sha256": m["records_sha256"],
                 "context_selection_version": m["context_selection_version"],
                 "executors": d["executors"], "presentation_seeds": d["presentation_seeds"],
                 "order_collision_rotation_applied": collision, "records": list(admin_rows.values()),
                 "packets": packets, "generated_at": utc(),
                 "distribution_status": "pending_separate_accounts_or_access_control; same_uid_mode_bits_do_not_isolate"})
        require(not output.exists(), "生成竞争：输出轮次已经存在")
        os.rename(staging, output)
    except BaseException:
        shutil.rmtree(staging)
        build_lock.unlink(missing_ok=True)
        raise
    return {"status": "generated_unfilled_packets", "purpose": m["purpose"], "N": len(ids),
            "same_content": True, "different_order": True, "human_execution_completed": False,
            "output": str(output)}


def text_fragments(context):
    out = []
    for k in ("text", "title", "caption", "headers", "row_cells"):
        def walk(v):
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
            elif isinstance(v, dict):
                # 不把来源URL、位置编号、结构ID当原文证据。
                if isinstance(v.get("text"), str):
                    out.append(v["text"])
        walk(context.get(k))
    return out


def quote_in(quote, texts, where):
    string(quote, where)
    require(any(quote in s for s in texts), f"{where}: 非本次来源的连续引文；不自动去空格/NFKC或拼接")


def read_packet(folder):
    folder = Path(folder)
    m = load_json(folder / "packet-manifest.json")
    exact(m, ("schema_version", "purpose", "round_id", "parent_round_id", "side", "executor_code", "identity_registry_sha256", "manual_version", "manual_sha256", "packet_sha256", "record_count", "dimension_count", "assets", "content_set_sha256"), where="packet_manifest")
    require(m.get("schema_version") == VERSION, "packet接口版本错误")
    require(sha_file(folder / "manual.md") == m["manual_sha256"], "手册SHA改变")
    require(sha_file(folder / "packet.jsonl") == m["packet_sha256"], "packet SHA改变")
    rows = load_lines(folder / "packet.jsonl")
    require(len(rows) == m["record_count"] and m["dimension_count"] == len(rows)*5, "packet数量不符")
    ids = set()
    for r in rows:
        exact(r, ("unit_text", "unit_source_ref", "source_title", "contexts", "attachments", "packet_version", "manual_version", "blind_id", "material_status", "neutral_material_note", "content_sha256"), where="packet_record")
        reject_results(r)
        require(r["packet_version"] == VERSION and r["manual_version"] == m["manual_version"], "packet记录版本错误")
        require(isinstance(r["blind_id"],str) and re.fullmatch(m["side"]+r"-[0-9]{6}",r["blind_id"]), "匿名记录ID错误")
        require(r["blind_id"] not in ids, "packet blind_id重复")
        ids.add(r["blind_id"])
        require(content_sha(r) == r["content_sha256"], "packet同内容SHA不符")
    require(sha_bytes(canonical(sorted(r["content_sha256"] for r in rows))) == m["content_set_sha256"], "content_set SHA不符")
    for a in m["assets"]:
        require(sha_file(local_file(folder, a["relative_path"])) == a["sha256"], "实际原图缺失/损坏")
    required_assets = {a["sha256"] for r in rows for a in r["attachments"]}
    require(required_assets == {a["sha256"] for a in m["assets"]}, "原图清单不完整")
    return m, {r["blind_id"]: r for r in rows}


def check_evidence(dimension, dim, packet):
    exact(dimension, ("value", "evidence_path", "current_quote", "context_quotes", "image_evidence", "reason", "path_evidence", "material_requests"), where=f"dimension.{dim}")
    v = dimension["value"]
    require(v is None or type(v) is int and v in (0, 1), f"{dim}: 标签只能是整数0/1/null，布尔/浮点不收")
    quote_in(dimension["current_quote"], [packet["unit_text"]], dim + ".current_quote")
    string(dimension["evidence_path"], dim + ".evidence_path")
    string(dimension["reason"], dim + ".reason")
    require(isinstance(dimension["context_quotes"], list), "context_quotes类型错误")
    contexts = {c["context_id"]: c for c in packet["contexts"]}
    for q in dimension["context_quotes"]:
        exact(q, ("context_id", "quote"), where="context_quote")
        require(q["context_id"] in contexts, "证据context_id不在本单元")
        quote_in(q["quote"], text_fragments(contexts[q["context_id"]]), "context_quote")
    require(isinstance(dimension["image_evidence"], list), "image_evidence类型错误")
    images = {a["attachment_id"]: a for a in packet["attachments"]}
    for q in dimension["image_evidence"]:
        exact(q, ("attachment_id", "sha256", "location", "quote_or_geometry", "use"), where="image_evidence")
        require(q["attachment_id"] in images and q["sha256"] == images[q["attachment_id"]]["sha256"], "图片证据引用不符")
        for k in ("location", "quote_or_geometry", "use"):
            string(q[k], "image_evidence." + k)
    require(isinstance(dimension["path_evidence"], dict), "path_evidence类型错误")
    paths = dimension["path_evidence"]
    permitted = {"support_object", "support_arrangement", "direct_relation", "patient_drug_object", "fairness_relation", "current_arrangement_or_evaluation"}
    require(paths.keys() <= permitted, "path_evidence有未知字段")
    needed = ()
    paths_used = dimension["evidence_path"].split("+")
    permitted_paths = {"S": {"S_content", "S_information"}, "E": {"E_content", "E_information"},
                       "Ec": {"Ec_content", "Ec_information"}, "I": {"I1", "I2", "I3", "I4"},
                       "F": {"F_general", "F_specific"}}
    require(len(set(paths_used)) == len(paths_used), "证据路径重复")
    require(set(paths_used) <= (permitted_paths[dim] if v == 1 else {"not_met"} if v == 0 else {"unknown"}), "标签/维度与证据路径不符")
    if v == 1 and "I3" in paths_used:
        require(dim == "I", "I3只能用于I")
        needed = ("support_object", "support_arrangement", "direct_relation")
    if v == 1 and "F_specific" in paths_used:
        require(dim == "F", "F_specific只能用于F")
        needed = ("patient_drug_object", "fairness_relation", "current_arrangement_or_evaluation")
    require(set(needed) <= paths.keys(), "I3/具体F必要关系证据不完整")
    for key, e in paths.items():
        exact(e, ("source", "quote", "explanation"), where="path_evidence."+key)
        string(e["explanation"], "path explanation")
        if e["source"] == "current":
            quote_in(e["quote"], [packet["unit_text"]], "path quote")
        elif e["source"] in contexts:
            quote_in(e["quote"], text_fragments(contexts[e["source"]]), "path quote")
            require(any(q["context_id"] == e["source"] and e["quote"] in q["quote"] for q in dimension["context_quotes"]), "path语境须列入实际使用引文")
        elif e["source"] in images:
            require(any(q["attachment_id"] == e["source"] and q["quote_or_geometry"] == e["quote"] for q in dimension["image_evidence"]), "path图证据須列入实际使用图证据")
        else:
            raise ContractError("path来源不是当前/本单元语境/本单元图")
    requests = dimension["material_requests"]
    require(isinstance(requests, list), "material_requests类型错误")
    require(v is not None or bool(requests), "null须有具体缺材/真实规则冲突说明，不当0")
    for q in requests:
        exact(q, ("type", "current_reference_quote", "needed_material", "why_decisive"), where="material_request")
        require(q["type"] in ("missing_source", "unresolved_reference", "unresolved_structure", "rule_conflict"), "缺材问题类型错误")
        quote_in(q["current_reference_quote"], [packet["unit_text"]], "material_request.current_reference_quote")
        string(q["needed_material"], "needed_material")
        string(q["why_decisive"], "why_decisive")
    return len(requests)


def time_value(value, where):
    string(value, where)
    try:
        t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(t.tzinfo is not None, f"{where}: 时间须有时区")
        return t
    except ValueError:
        raise ContractError(f"{where}: 时间格式无效")


def verify(folder, labels_path, submission_path):
    m, packets = read_packet(folder)
    sub = load_json(submission_path)
    required = ("schema_version", "state", "purpose", "round_id", "executor_code", "actual_actor_type", "identity_registry_sha256", "manual_sha256", "packet_sha256", "labels_sha256", "record_count", "dimension_count", "started_at", "submitted_at", "independence_declaration", "AI_assistance", "prior_development_exposure", "material_request_count", "image_view_attestation")
    exact(sub, required, where="submission")
    require(sub["state"] == "complete", "空白/未完成提交不可封存为完成真人首判")
    require(sub["schema_version"] == VERSION and sub["purpose"] == m["purpose"], "提交接口/用途错误")
    for k in ("round_id", "executor_code", "manual_sha256", "packet_sha256", "record_count", "dimension_count"):
        require(sub[k] == m[k], "提交绑定不符: " + k)
    require(sub["labels_sha256"] == sha_file(labels_path), "标签字节SHA不符")
    # 工具仅核对声明结构，真人身份/实际独立操作由管理员另核，不能据声明自动证明。
    require(sub["actual_actor_type"] in ("real_human_independent", "real_human_posthoc_review", "AI_draft", "synthetic_toy"), "实际身份不得pending或伪称")
    if m["purpose"] == "independent_validation":
        require(sub["actual_actor_type"] == "real_human_independent", "AI草稿/事后复核不能作协商前真人首判")
    else:
        require(sub["actual_actor_type"] == "synthetic_toy", "toy不能声明真人执行")
    sha(sub["identity_registry_sha256"], "identity_registry_sha256")
    require(sub["identity_registry_sha256"] == m["identity_registry_sha256"], "执行者真实身份登记SHA不符合冻结分配")
    exact(sub["independence_declaration"], ("own_first_judgment", "machine_answers_unseen", "peer_answers_unseen", "no_discussion_before_seal"), where="independence_declaration")
    require(all(x is True for x in sub["independence_declaration"].values()), "独立声明不完整；保留实际身份，不能用于真人信度")
    exact(sub["AI_assistance"], ("label_drafting_used", "description"), where="AI_assistance")
    require(sub["AI_assistance"]["label_drafting_used"] is False, "AI标签草稿后人工检查不是独立真人首判")
    string(sub["AI_assistance"]["description"], "AI_assistance.description")
    string(sub["prior_development_exposure"], "prior_development_exposure")
    require(time_value(sub["started_at"], "started_at") <= time_value(sub["submitted_at"], "submitted_at"), "提交早于开始")
    require(sub["image_view_attestation"] is True, "须真实声明附件阅读；脚本不能证明实际观看")
    rows = load_lines(labels_path)
    require(len(rows) == len(packets), "提交记录数错误")
    seen, request_n = set(), 0
    for r in rows:
        exact(r, ("blind_id", "content_sha256", "completion_status", "dimensions", "viewed_attachments"), where="labels_row")
        bid = r["blind_id"]
        require(bid in packets and bid not in seen, "提交blind_id重复/额外/未分配")
        seen.add(bid)
        p = packets[bid]
        require(r["completion_status"] == "complete", "未填写行不可把占位null当语义null")
        require(r["content_sha256"] == p["content_sha256"], "提交同内容SHA不符")
        exact(r["dimensions"], DIMS, where="dimensions")
        require(isinstance(r["viewed_attachments"], list), "实际查看清单类型错误")
        viewed = {}
        for a in r["viewed_attachments"]:
            exact(a, ("attachment_id", "sha256", "viewed_at"), where="viewed_attachment")
            require(a["attachment_id"] not in viewed, "实际查看ID重复")
            viewed[a["attachment_id"]] = a["sha256"]
            viewed_at = time_value(a["viewed_at"], "viewed_at")
            require(time_value(sub["started_at"], "started_at") <= viewed_at <= time_value(sub["submitted_at"], "submitted_at"), "查看时间须在实际执行区间内")
        require(viewed == {a["attachment_id"]: a["sha256"] for a in p["attachments"]}, "有附件的单元须逐张记录真实查看；缺/多/哈希错")
        for dim in DIMS:
            request_n += check_evidence(r["dimensions"][dim], dim, p)
    require(seen == packets.keys(), "存在漏交ID")
    require(type(sub["material_request_count"]) is int and sub["material_request_count"] == request_n, "请求计数不符（按逐维请求条目计，不去重）")
    return {"format_status": "passed", "record_count": len(rows), "dimension_count": len(rows)*5,
            "material_request_count": request_n, "actual_actor_type_declared": sub["actual_actor_type"],
            "labels_sha256": sha_file(labels_path), "submission_sha256": sha_file(submission_path),
            "identity_and_independence_external_audit": "pending; software does not establish human authorship",
            "semantic_accuracy": "not_evaluated", "human_validation_complete": False}


def seal(folder, labels_path, submission_path, destination):
    result = verify(folder, labels_path, submission_path)
    destination = Path(destination)
    require(not destination.exists(), "初判封存目录已存在；不覆盖。补材或讨论另轮另文件")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    stage = Path(tempfile.mkdtemp(prefix=".seal-", dir=destination.parent))
    try:
        label_bytes, submission_bytes = Path(labels_path).read_bytes(), Path(submission_path).read_bytes()
        require(sha_bytes(label_bytes) == result["labels_sha256"] and sha_bytes(submission_bytes) == result["submission_sha256"], "核验后提交文件发生变化；重新核验，不封存")
        put(stage / "labels.jsonl", label_bytes, 0o400)
        put(stage / "submission.json", submission_bytes, 0o400)
        put_json(stage / "seal.json", dict(result, sealed_at=utc(), tool_version=VERSION,
                 tool_sha256=sha_file(__file__), python_version=sys.version,
                 packet_manifest_sha256=sha_file(Path(folder) / "packet-manifest.json")), 0o400)
        # rename 的存在检查非并发互斥；用专属锁文件确保同工具并发首判不会相互覆盖。
        lock = destination.parent / ("." + destination.name + ".first-seal.lock")
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
        os.close(fd)
        try:
            require(not destination.exists(), "封存竞争：目的目录已存在")
            os.rename(stage, destination)
        except BaseException:
            lock.unlink(missing_ok=True)
            raise
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return dict(result, sealed_at_directory=str(destination), overwrite_allowed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    b = commands.add_parser("build")
    b.add_argument("--source-package", required=True)
    b.add_argument("--draw-manifest", required=True)
    b.add_argument("--manual", required=True)
    b.add_argument("--executor-a", required=True)
    b.add_argument("--executor-b", required=True)
    b.add_argument("--output", required=True)
    for name in ("verify", "seal"):
        v = commands.add_parser(name)
        v.add_argument("--packet-dir", required=True)
        v.add_argument("--labels", required=True)
        v.add_argument("--submission", required=True)
        if name == "seal":
            v.add_argument("--destination", required=True)
    args = parser.parse_args()
    try:
        if args.command == "build":
            result = build(args.source_package, args.draw_manifest, args.manual,
                           (args.executor_a, args.executor_b), args.output)
        elif args.command == "verify":
            result = verify(args.packet_dir, args.labels, args.submission)
        else:
            result = seal(args.packet_dir, args.labels, args.submission, args.destination)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ContractError, OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({"status": "rejected", "error": str(e), "human_validation_complete": False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
