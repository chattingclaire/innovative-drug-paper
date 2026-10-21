#!/usr/bin/env python3
"""只读核查输入；仅向新建 --out 目录写 JSON、CSV、Markdown。标准库即可运行。"""
import argparse
import collections
import csv
import hashlib
import io
import itertools
import json
import math
import random
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

DIMS = ("S", "E", "Ec", "I", "F")
STATES = ("0", "1", "null", "missing", "invalid", "duplicate")
DEFAULT_PACKAGE = Path("/PROJECT_ROOT/outputs/goal-calibration-20261010/09-delivery/human200-independent-preparation-root")
LOCKS = {
    "coordinator-private/draw-and-mapping.json": "5690672e10612371def277f7d98ed332e22cb281cfb5b636a9cbc93eaba1bd55",
    "coordinator-private/pre-draw-freeze.json": "042ed0065cd66fbb55571f70f7bcc2f51e079e7f5857604360a25fe59f056f95",
    "_build/workbook-input.json": "52c49db879f59745ff880f16c4e58d9f64d6f8f2d1e3f8e2173d4bea4cb3f16b",
}
MANUAL_SHA = "5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b"
PROMPT_SHA = "69c8291200aa960502c240dc24a6671ca9a8c6b0aad95998e0af611b6ea2ffc9"
MATERIAL_SIGNATURE = "9a1a5cfa8719a0e78c3c15570d81f71775e27e83a7221708b430db153df16aca"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_no_duplicate_keys(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError("JSON对象重复键: " + k)
        obj[k] = v
    return obj


def decode(data):
    return json.loads(data, object_pairs_hook=object_no_duplicate_keys)


def ensure(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def locked_mapping(package):
    """所有配对先验证固定映射哈希、唯一性、两侧原始材料及其真实source_id。"""
    for name, sha in LOCKS.items():
        ensure(digest((package / name).read_bytes()) == sha, "冻结输入哈希不符: " + name)
    draw = decode((package / "coordinator-private/draw-and-mapping.json").read_bytes())
    freeze = decode((package / "coordinator-private/pre-draw-freeze.json").read_bytes())
    workbook = decode((package / "_build/workbook-input.json").read_bytes())
    records = draw["records"]
    ensure(len(records) == 200, "抽样映射必须恰好200条")
    for key in ("source_id", "A_blind_id", "B_blind_id"):
        ensure(len({r[key] for r in records}) == 200, "映射非一一对应: " + key)
    ensure(sorted(r["source_id"] for r in records) == draw["source_ids_sorted"], "source_ids_sorted不符")
    ensure(len({r["stratum"] for r in records}) == 41, "抽样层数不符")
    grouped = collections.defaultdict(list)
    material_hashes = []
    for r in records:
        grouped[r["stratum"]].append(r)
        ensure(Fraction(r["pi_exact"]) == Fraction(r["n_h"], r["N_h"]), "pi不符: " + r["source_id"])
        ensure(Fraction(r["weight_exact"]) == 1 / Fraction(r["pi_exact"]), "权重不符: " + r["source_id"])
        a = (package / "coder-A/materials" / (r["A_blind_id"] + ".json")).read_bytes()
        b = (package / "coder-B/materials" / (r["B_blind_id"] + ".json")).read_bytes()
        ensure(a == b, "配对材料原字节不同: " + r["source_id"])
        ensure(decode(a)["source_record"]["id"] == r["source_id"], "材料真实source_id与映射不符")
        material_hashes.append({"source_id": r["source_id"], "A_blind_id": r["A_blind_id"], "B_blind_id": r["B_blind_id"], "material_sha256": digest(a)})
    ensure(digest(json.dumps(material_hashes, sort_keys=True, separators=(',',':')).encode()) == MATERIAL_SIGNATURE, "200条材料指纹相对准备时变化")
    allocations = {r["stratum"]: r for r in freeze["fixed_allocation"]["strata"]}
    for h, rows in grouped.items():
        ensure(len(rows) == rows[0]["n_h"] == allocations[h]["new_n_h"], "层内样本数不符: " + h)
        ensure(all(r["N_h"] == allocations[h]["N_h"] for r in rows), "层总体数不符")
    ensure(sum(Fraction(r["weight_exact"]) for r in records) == 4481, "总权重不等于4481")
    orders = {}
    for side in ("A", "B"):
        ensure(digest((package / f"coder-{side}/manual.txt").read_bytes()) == MANUAL_SHA, "手册哈希不符")
        ensure(digest((package / f"coder-{side}/execution-prompt.txt").read_bytes()) == PROMPT_SHA, "执行说明哈希不符")
        by_id = {r[f"{side}_blind_id"]: r["source_id"] for r in records}
        order = [r["blind_id"] for r in workbook["sides"][side]]
        ensure(len(order) == 200 and set(order) == set(by_id), "编码表顺序清单覆盖不符")
        ensure({f.stem for f in (package / f"coder-{side}/materials").glob("*.json")} == set(by_id), "材料JSON覆盖不符")
        orders[side] = [by_id[v] for v in order]
    summary = {
        "record_N": 200, "dimension_decisions_per_AI": 1000, "stratum_N": 41,
        "same_source_id_set": True, "paired_source_materials_byte_identical_N": 200,
        "A_B_same_order": orders["A"] == orders["B"],
        "same_source_at_same_position_N": sum(a == b for a, b in zip(orders["A"], orders["B"])),
        "pairing_rule": "A_blind_id -> source_id <- B_blind_id；不按顺序或盲号数值配对",
        "by_domain": dict(collections.Counter(r["domain"] for r in records)),
        "by_department": dict(collections.Counter(r["department"] for r in records)),
        "weighted_population_N": 4481, "mapping_sha256": LOCKS["coordinator-private/draw-and-mapping.json"],
        "manual_sha256": MANUAL_SHA, "execution_prompt_sha256": PROMPT_SHA,
        "paired_material_signature_sha256": MATERIAL_SIGNATURE,
        "judgments_opened": False,
    }
    return records, summary, material_hashes


def gate_submissions(side_paths):
    """两侧封存证明全部通过后，才允许解析任一侧判读记录。"""
    submissions, buffers, issues = {}, {}, []
    for side, folder in side_paths.items():
        try:
            manifest_bytes = (folder / "submission.json").read_bytes()
            sub = decode(manifest_bytes)
            checks = {
                "status必须为sealed": sub.get("status") == "sealed",
                "identity必须标明本侧AI": sub.get("identity") == "AI评审" + side,
                "record_count必须为200": type(sub.get("record_count")) is int and sub["record_count"] == 200,
                "judgment_count必须为1000": type(sub.get("judgment_count")) is int and sub["judgment_count"] == 1000,
                "independent必须为true": sub.get("independent") is True,
                "human_judgments必须为false": sub.get("human_judgments") is False,
                "manual_sha256不符": sub.get("manual_sha256") == MANUAL_SHA,
                "execution_prompt_sha256不符": sub.get("execution_prompt_sha256") == PROMPT_SHA,
                "null_count必须为0..1000整数": type(sub.get("null_count")) is int and 0 <= sub["null_count"] <= 1000,
            }
            for message, passed in checks.items():
                if not passed:
                    issues.append({"side": side, "issue": message})
            submissions[side] = {"manifest": sub, "submission_sha256": digest(manifest_bytes)}
        except (OSError, ValueError, TypeError) as exc:
            issues.append({"side": side, "issue": str(exc)})
    if issues:
        return submissions, buffers, issues
    # 上面确认两侧皆宣告封存。读取固定字节只用于校验；不解析未通过哈希的内容。
    for side, folder in side_paths.items():
        try:
            data = (folder / "judgments.jsonl").read_bytes()
            ensure(digest(data) == submissions[side]["manifest"].get("judgments_sha256"), "judgments_sha256不符")
            buffers[side] = data
            # 捕获校验窗口内的封存元数据变动，防止边写边读取。
            ensure(digest((folder / "submission.json").read_bytes()) == submissions[side]["submission_sha256"], "封存清单读取期间变化")
        except (OSError, ValueError, TypeError) as exc:
            issues.append({"side": side, "issue": str(exc)})
    return submissions, buffers, issues


def label_state(value):
    if value is None:
        return "null"
    if type(value) is int and value in (0, 1):
        return str(value)
    return "invalid"


def substantive_reason(reason):
    return isinstance(reason, str) and reason.strip() not in ("", "待定", "待定：", "待定:")


def parse_side(data, expected, side):
    seen, issues = collections.defaultdict(list), []
    nonblank_lines = 0
    for line_no, line in enumerate(data.decode("utf-8-sig").splitlines(), 1):
        if not line.strip():
            issues.append({"side": side, "line": line_no, "issue": "空行"})
            continue
        nonblank_lines += 1
        try:
            row = decode(line)
            ensure(isinstance(row, dict), "每行必须为对象")
            blind_id = row.get("blind_id")
            ensure(isinstance(blind_id, str), "blind_id缺失/非法")
            ensure(blind_id in expected, "不在本侧冻结抽样集的blind_id: " + blind_id)
            seen[blind_id].append((line_no, row))
        except (ValueError, TypeError) as exc:
            issues.append({"side": side, "line": line_no, "issue": str(exc)})
    cells = {}
    for blind_id in sorted(expected):
        rows = seen[blind_id]
        if len(rows) != 1:
            state = "missing" if not rows else "duplicate"
            issues.append({"side": side, "blind_id": blind_id, "issue": state, "occurrences": len(rows)})
            for dim in DIMS:
                cells[blind_id, dim] = {"state": state, "pending": False, "reason": "", "evidence": "", "context": ""}
            continue
        line_no, row = rows[0]
        judgments = row.get("judgments")
        if not isinstance(judgments, dict):
            judgments = {}
            issues.append({"side": side, "blind_id": blind_id, "issue": "judgments必须为五维对象"})
        extra = set(judgments) - set(DIMS)
        if extra:
            issues.append({"side": side, "blind_id": blind_id, "issue": "非法维度", "dimensions": sorted(extra)})
        for dim in DIMS:
            item = judgments.get(dim)
            state = "missing" if item is None else "invalid"
            if isinstance(item, dict):
                state = label_state(item["value"]) if "value" in item else "missing"
            else:
                item = {}
            reason = item.get("reason", "")
            pending = state == "null" and substantive_reason(reason)
            cell = {"state": state, "pending": pending, "reason": reason,
                    "evidence": item.get("evidence", ""), "context": item.get("context", "")}
            cells[blind_id, dim] = cell
            problems = []
            if state not in ("0", "1", "null"):
                problems.append("标签必须为整数0/1或null")
            if not substantive_reason(reason):
                problems.append("理由缺失/仅待定占位；不能机械认定完成")
            if "evidence" not in item or "context" not in item:
                problems.append("缺evidence或context字段")
            if problems:
                issues.append({"side": side, "blind_id": blind_id, "dimension": dim, "line": line_no, "issue": "；".join(problems)})
    summary = {"nonblank_lines": nonblank_lines, "unique_assigned_ids_received": len([k for k, v in seen.items() if v]),
               "expected_records": 200, "expected_cells": 1000,
               "duplicate_ids": sum(len(v) > 1 for v in seen.values()),
               "missing_ids": sum(not seen[k] for k in expected),
               "counted_valid_label_cells": sum(c["state"] in ("0", "1", "null") for c in cells.values()),
               "null_count": sum(c["state"] == "null" for c in cells.values())}
    return cells, issues, summary


def safe_ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def agreement(cells):
    a, b, c, d = [cells.get(k, 0) for k in (("1", "1"), ("1", "0"), ("0", "1"), ("0", "0"))]
    n = a + b + c + d
    po = safe_ratio(a + d, n)
    pe = safe_ratio((a+b)*(a+c)+(c+d)*(b+d), n*n)
    return {"a_A1B1": a, "b_A1B0": b, "c_A0B1": c, "d_A0B0": d,
            "comparable_denominator": n, "observed_agreement": po, "chance_agreement": pe,
            "cohen_kappa": safe_ratio(po-pe, 1-pe) if po is not None and pe is not None else None,
            "positive_agreement": safe_ratio(2*a, 2*a+b+c), "negative_agreement": safe_ratio(2*d, 2*d+b+c),
            "A_positive_denominator": a+b, "B_positive_denominator": a+c,
            "A_negative_denominator": c+d, "B_negative_denominator": b+d,
            "interpretation": "AI–AI一致性诊断；非真人效度；不设通过判定",
            "CI": None, "CI_note": "原始未加权结果仅为样本描述；加权结果另附设计区间"}


def group_records(records):
    result = {"all_200": records}
    for key in ("domain", "department"):
        for value in sorted({r[key] for r in records}):
            result[key + ":" + value] = [r for r in records if r[key] == value]
    return result


def summarize(records, side_cells):
    counts, cross, metrics, discrepancies = [], [], [], []
    for group, rows in group_records(records).items():
        for dim in DIMS:
            for side in ("A", "B"):
                count = collections.Counter(side_cells[side][r[f"{side}_blind_id"], dim]["state"] for r in rows)
                pending = sum(side_cells[side][r[f"{side}_blind_id"], dim]["pending"] for r in rows)
                counts.append({"group": group, "side": side, "dimension": dim, "assigned": len(rows),
                               **{s: count[s] for s in STATES}, "pending_with_reason_subset_of_null": pending,
                               "null_without_reason": count["null"]-pending})
            for weighting in ("raw", "design_weighted"):
                table = collections.defaultdict(float)
                for r in rows:
                    key = tuple(side_cells[s][r[f"{s}_blind_id"], dim]["state"] for s in ("A", "B"))
                    table[key] += 1 if weighting == "raw" else float(Fraction(r["weight_exact"]))
                for a in STATES:
                    for b in STATES:
                        cross.append({"group": group, "dimension": dim, "weighting": weighting, "A": a, "B": b, "value": table[a, b]})
                metric = agreement(table)
                metric.update({"group": group, "dimension": dim, "weighting": weighting,
                               "assigned_denominator": len(rows) if weighting == "raw" else sum(float(Fraction(r["weight_exact"])) for r in rows),
                               "not_comparable_denominator": sum(v for (a,b),v in table.items() if a not in ("0","1") or b not in ("0","1"))})
                metrics.append(metric)
    for r in sorted(records, key=lambda r: r["source_id"]):
        for dim in DIMS:
            a = side_cells["A"][r["A_blind_id"], dim]
            b = side_cells["B"][r["B_blind_id"], dim]
            if a["state"] != b["state"] or a["state"] not in ("0", "1"):
                discrepancies.append({"source_id": r["source_id"], "A_blind_id": r["A_blind_id"], "B_blind_id": r["B_blind_id"],
                                      "dimension": dim, "kind": "binary_disagreement" if {a["state"], b["state"]} == {"0", "1"} else "pending_or_invalid",
                                      "A_state": a["state"], "B_state": b["state"],
                                      "A_evidence": a["evidence"], "B_evidence": b["evidence"],
                                      "A_context": a["context"], "B_context": b["context"],
                                      "A_reason": a["reason"], "B_reason": b["reason"]})
    return counts, cross, metrics, discrepancies


def percentile(values, probability):
    values = sorted(values)
    if not values:
        return None
    at = (len(values)-1)*probability
    lo = int(math.floor(at))
    hi = int(math.ceil(at))
    return values[lo] + (values[hi]-values[lo])*(at-lo)


def interval_summary(values):
    valid = [v for v in values if v is not None and math.isfinite(v)]
    undefined = len(values)-len(valid)
    quantiles = [percentile(valid, .025), percentile(valid, .975)] if valid else None
    degenerate = bool(quantiles is not None and math.isclose(quantiles[0], quantiles[1], rel_tol=0, abs_tol=1e-12))
    return {"replicates_total": len(values), "replicates_defined": len(valid),
            "undefined_replicate_fraction": undefined/len(values),
            "confidence_interval_95": quantiles if not undefined else None,
            "defined_replicates_only_quantile_diagnostic": quantiles if undefined else None,
            "degenerate": degenerate,
            "interval_width": quantiles[1]-quantiles[0] if quantiles is not None and not undefined else None,
            "note": "存在未定义重复；条件分位数不宣称无条件95%覆盖" if undefined else
                    "退化区间不能证明罕见错误或正类不存在；需有限总体边界核查" if degenerate else
                    "按实际分层SRSWOR逐指标95%区间；不是全部指标同时95%"}


def replicate_weights(records, rng):
    strata = collections.defaultdict(list)
    for i, r in enumerate(records):
        strata[r["stratum"]].append(i)
    weights = [0.0] * len(records)
    for h in sorted(strata):
        indices = sorted(strata[h], key=lambda i: records[i]["source_id"])
        n, N = len(indices), records[indices[0]]["N_h"]
        if n == N:
            for i in indices:
                weights[i] = float(Fraction(records[i]["weight_exact"]))
            continue
        ensure(n >= 2, "非全取层n=1，无法按既定Rao-Wu实现")
        k = collections.Counter(rng.randrange(n) for _ in range(n-1))
        scale = math.sqrt(1-n/N)
        for j, i in enumerate(indices):
            multiplier = 1-scale + scale*n/(n-1)*k[j]
            weights[i] = float(Fraction(records[i]["weight_exact"])) * multiplier
    return weights


def zero_event_upper(N, n, alpha):
    """超几何零观察事件的上界：最大T，使P(X=0|N,T,n)>=alpha。"""
    def p0(T):
        if N-T < n:
            return 0.0
        return math.exp(sum(math.log((N-T-j)/(N-j)) for j in range(n)))
    lo, hi = 0, N
    while lo < hi:
        mid = (lo+hi+1)//2
        if p0(mid) >= alpha:
            lo = mid
        else:
            hi = mid-1
    return lo


def zero_error_guard(rows, side_cells, dim):
    pairs = [(side_cells['A'][r['A_blind_id'], dim]['state'], side_cells['B'][r['B_blind_id'], dim]['state']) for r in rows]
    if not all(a in ('0','1') and b in ('0','1') for a,b in pairs):
        return {"status": "not_computed_unknown_or_invalid", "note": "未知不能当作无分歧；全域界需包括未知类别"}
    if any(a != b for a,b in pairs):
        return {"status": "not_applicable_nonzero_disagreements", "note": "这里只实现零分歧的有限总体边界保护，非通用四格联合界"}
    strata = collections.defaultdict(list)
    for r in rows:
        strata[r['stratum']].append(r)
    # 对Po的二元分歧事件，逐层一侧alpha=.05/H，Bonferroni总体覆盖至少95%。
    H = len(strata)
    upper = sum(zero_event_upper(rs[0]['N_h'], len(rs), .05/H) for rs in strata.values())
    N = sum(rs[0]['N_h'] for rs in strata.values())
    return {"status": "zero_disagreement_one_sided_finite_population_guard", "population_N": N,
            "stratum_N": H, "alpha_per_stratum": .05/H, "unobserved_disagreement_total_upper": upper,
            "agreement_lower_bound_95_at_least": 1-upper/N,
            "note": "Po专用的保守一侧超几何/Bonferroni边界；不替代主区间，不是κ界、真人效度界或新增验收线"}


def add_bootstrap(records, side_cells, metrics):
    groups = group_records(records)
    keys = [(group, dim) for group in groups for dim in DIMS]
    indexed = {key: i for i, key in enumerate(keys)}
    values = {key: {"observed_agreement": [], "cohen_kappa": []} for key in keys}
    memberships = []
    for r in records:
        memberships.append(["all_200", "domain:"+r['domain'], "department:"+r['department']])
    contributions = []
    for i,r in enumerate(records):
        for dim in DIMS:
            a,b = (side_cells[s][r[f'{s}_blind_id'],dim]['state'] for s in ('A','B'))
            if a in ('0','1') and b in ('0','1'):
                cell = {('1','1'):0,('1','0'):1,('0','1'):2,('0','0'):3}[a,b]
                contributions.append((i,cell,[indexed[g,dim] for g in memberships[i]]))
    rng = random.Random(20261010)
    weight_hash = hashlib.sha256()
    for _ in range(5000):
        weights = replicate_weights(records, rng)
        weight_hash.update(json.dumps(weights, separators=(',',':')).encode())
        tables = [[0.0]*4 for _ in keys]
        for i,cell,ks in contributions:
            for k in ks:
                tables[k][cell] += weights[i]
        for key, (a,b,c,d) in zip(keys,tables):
            n = a+b+c+d
            po = safe_ratio(a+d,n)
            pe = safe_ratio((a+b)*(a+c)+(c+d)*(b+d),n*n)
            kappa = safe_ratio(po-pe,1-pe) if po is not None and pe is not None else None
            values[key]['observed_agreement'].append(po)
            values[key]['cohen_kappa'].append(kappa)
    for metric in metrics:
        if metric['weighting'] != 'design_weighted':
            continue
        key = metric['group'],metric['dimension']
        metric['CI'] = {name:interval_summary(vals) for name,vals in values[key].items()}
        metric['CI_note'] = "Rao-Wu重缩放bootstrap；同41层设计、FPC、共同重复权重；5000次、seed=20261010"
        metric['zero_disagreement_guard'] = zero_error_guard(groups[key[0]],side_cells,key[1])
    return {"method": "stratified_SRSWOR_Rao_Wu_rescaled_bootstrap", "replicates":5000,"seed":20261010,
            "record_order": "draw-and-mapping.records；层名及层内source_id排序生成抽签",
            "replicate_factor": "1-sqrt(1-n_h/N_h)+sqrt(1-n_h/N_h)*n_h/(n_h-1)*k_hi; k from n_h-1 multinomial draws",
            "census_strata": "固定原权重；非全取n_h=1拒绝计算", "repeated_weights_sha256": weight_hash.hexdigest(),
            "shared_weights": "五维、all_200、remaining、exposed及部门均使用同一套重复权重",
            "percentile": "2.5%与97.5%；排序后线性插值(type7)",
            "identity_warning":"仅AI–AI一致性诊断；不产生真人精确率/召回率/F1或验收结论"}


def self_test():
    assert label_state(True) == "invalid" and label_state(1.0) == "invalid"
    assert label_state("1") == "invalid" and label_state(None) == "null"
    table = {("1", "1"): 8, ("1", "0"): 2, ("0", "1"): 4, ("0", "0"): 6}
    r = agreement(table)
    assert r["observed_agreement"] == .7 and math.isclose(r["cohen_kappa"], .4)
    assert r["comparable_denominator"] == 20 and r["positive_agreement"] == 16/22
    assert agreement({("0", "0"): 200})["cohen_kappa"] is None
    assert agreement({("null", "null"): 200})["observed_agreement"] is None
    expected = {"A-000001"}
    row = {"blind_id": "A-000001", "judgments": {d: {"value": 0, "evidence": "test", "context": "", "reason": "测试理由"} for d in DIMS}}
    line = json.dumps(row)
    c, i, s = parse_side((line+"\n"+line+"\n").encode(), expected, "A")
    assert s["duplicate_ids"] == 1 and c["A-000001", "S"]["state"] == "duplicate"
    row["judgments"]["I"]["value"] = None
    c, i, s = parse_side(json.dumps(row).encode(), expected, "A")
    assert s["null_count"] == 1 and c["A-000001", "I"]["pending"]
    assert c["A-000001", "S"]["state"] == "0"
    assert interval_summary([1.0]*20)['degenerate']
    assert interval_summary([None,1.0])['confidence_interval_95'] is None
    assert zero_event_upper(10,10,.05) == 0
    assert zero_event_upper(10,2,.05) == 7
    # n=2,N=10时枚举仅两种重复，层总权重恒10；方差应等于FPC线性化方差。
    synthetic = [{'stratum':'h','source_id':str(i),'N_h':10,'weight_exact':'5'} for i in range(2)]
    class Choose:
        def __init__(self, value): self.value=value
        def randrange(self, n): return self.value
    estimates=[]
    for chosen in (0,1):
        ws=replicate_weights(synthetic,Choose(chosen))
        assert math.isclose(sum(ws),10)
        estimates.append(ws[1]/10)
    assert math.isclose(sum((v-.5)**2 for v in estimates)/2, (1-2/10)*.5/2)
    # n=3所有9种复抽独立枚举，验证n-1次数、FPC和层总量保持。
    synthetic = [{'stratum':'h','source_id':str(i),'N_h':10,'weight_exact':'10/3'} for i in range(3)]
    class ChooseSequence:
        def __init__(self, values): self.values=iter(values)
        def randrange(self, n): return next(self.values)
    estimates=[]
    for chosen in itertools.product(range(3),repeat=2):
        ws=replicate_weights(synthetic,ChooseSequence(chosen))
        assert math.isclose(sum(ws),10)
        estimates.append(ws[2]/10)
    assert math.isclose(sum((v-1/3)**2 for v in estimates)/9, (1-3/10)*(1/3)/3)
    try:
        decode('{"value":0,"value":1}')
        raise AssertionError("重复JSON键未拒绝")
    except ValueError:
        pass
    print("self-test: passed（仅合成数据；未读取判读提交）")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("mapping", "audit", "self-test"))
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--a", type=Path, help="A侧包含submission.json与judgments.jsonl的目录")
    parser.add_argument("--b", type=Path, help="B侧包含submission.json与judgments.jsonl的目录")
    parser.add_argument("--out", type=Path, help="新建输出目录；已有非空目录会拒绝")
    args = parser.parse_args()
    if args.mode == "self-test":
        self_test()
        return 0
    ensure(args.out is not None, "必须提供--out")
    if args.mode == "audit":
        ensure(args.a is not None and args.b is not None, "audit需同时提供--a/--b")
        ensure(args.a.resolve() != args.b.resolve(), "两侧目录不可相同")
    inputs = [args.package] + ([args.a, args.b] if args.mode == "audit" else [])
    for src in inputs:
        ensure(args.out.resolve() != src.resolve() and src.resolve() not in args.out.resolve().parents, "输出目录不可覆盖或嵌入输入目录")
    ensure(not args.out.exists() or not any(args.out.iterdir()), "输出目录非空；请选新目录")
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        records, mapping_summary, hashes = locked_mapping(args.package)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        write_json(args.out / "gate-errors.json", {"status": "mapping_gate_failed", "judgments_parsed": False, "error": str(exc)})
        return 2
    write_json(args.out / "mapping-check.json", mapping_summary)
    write_csv(args.out / "paired-mapping.csv", hashes, list(hashes[0]))
    if args.mode == "mapping":
        print("mapping: passed；只核对无答案材料与映射。")
        return 0
    submissions, buffers, issues = gate_submissions({"A": args.a, "B": args.b})
    if issues:
        write_json(args.out / "gate-errors.json", {"status": "submission_gate_failed", "judgments_parsed": False, "issues": issues})
        (args.out / "核查说明.md").write_text("封存门槛未通过，未解析任何一侧判读答案。见 gate-errors.json。\n", encoding="utf-8")
        return 2
    side_cells, coverage = {}, {}
    for side in ("A", "B"):
        expected = {r[f"{side}_blind_id"] for r in records}
        cells, side_issues, summary = parse_side(buffers[side], expected, side)
        side_cells[side], coverage[side] = cells, summary
        issues.extend(side_issues)
        for key, observed in (("record_count", summary["nonblank_lines"]), ("judgment_count", summary["counted_valid_label_cells"]), ("null_count", summary["null_count"])):
            if submissions[side]["manifest"][key] != observed:
                issues.append({"side": side, "issue": "封存宣告与实际不符: " + key, "declared": submissions[side]["manifest"][key], "observed": observed})
    counts, cross, metrics, discrepancies = summarize(records, side_cells)
    bootstrap = add_bootstrap(records, side_cells, metrics)
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "mechanical_issues_found" if issues else "mechanical_checks_passed",
              "identity": "two_independent_AI_reviewers", "human_judgments_received_by_this_script": False,
              "acceptance_decision": "not_assessed", "precision_recall_F1_against_human": None,
              "thresholds_applied": False, "mapping": mapping_summary, "sealed_inputs": submissions,
              "coverage": coverage, "issues": issues, "counts": counts, "agreement_metrics": metrics, "bootstrap": bootstrap,
              "binary_disagreement_cell_N": sum(r["kind"] == "binary_disagreement" for r in discrepancies),
              "pending_or_invalid_cell_N": sum(r["kind"] == "pending_or_invalid" for r in discrepancies),
              "limitations": ["机械通过不等于语义、引文或分类正确。", "null与有理由待定为包含关系，不能相加。",
                              "重复ID的所有五维标为duplicate，不挑一行。", "双可判分母仅描述可比较子域，不补齐未知。",
                              "AI–AI一致性不能替代真人信度或真人参照效度；不自动扩样。", "分歧清单在双方封存后供协调员使用，真人独立judge封存前不应提供给真人。"]}
    write_json(args.out / "audit-report.json", report)
    write_json(args.out / "disagreements.json", discrepancies)
    write_csv(args.out / "dimension-counts.csv", counts, list(counts[0]))
    write_csv(args.out / "cross-tables.csv", cross, list(cross[0]))
    metric_fields = [k for k in metrics[0] if k not in ("interpretation", "CI", "CI_note", "zero_disagreement_guard")]
    write_csv(args.out / "agreement-metrics.csv", [{k:r[k] for k in metric_fields} for r in metrics], metric_fields)
    ci_rows=[]
    for m in metrics:
        if m['CI']:
            for name,ci in m['CI'].items():
                interval=ci['confidence_interval_95']
                ci_rows.append({'group':m['group'],'dimension':m['dimension'],'metric':name,'point':m[name],
                                'lower_95':interval[0] if interval else None,'upper_95':interval[1] if interval else None,
                                'width':ci['interval_width'],'undefined_fraction':ci['undefined_replicate_fraction'],
                                'degenerate':ci['degenerate'],'note':ci['note']})
    write_csv(args.out / "agreement-intervals.csv",ci_rows,list(ci_rows[0]))
    discrepancy_fields = ["source_id","A_blind_id","B_blind_id","dimension","kind","A_state","B_state","A_evidence","B_evidence","A_context","B_context","A_reason","B_reason"]
    csv_discrepancies = [{k:json.dumps(v, ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in discrepancies]
    write_csv(args.out / "disagreements.csv", csv_discrepancies, discrepancy_fields)
    lines = ["# AI双盲评机械核查", "", "状态：" + report["status"] + "。本状态仅表示格式、覆盖与封存检查；不表示分类验收通过。", "",
             "两侧均已声明AI身份、独立提交并通过输出及共同手册哈希校验。没有读取真人judge。", "",
             "|维度|A正/负/null|B正/负/null|双可判n|原始一致率|κ|", "|---|---:|---:|---:|---:|---:|"]
    for dim in DIMS:
        cs = {r["side"]:r for r in counts if r["group"]=="all_200" and r["dimension"]==dim}
        m = next(r for r in metrics if r["group"]=="all_200" and r["dimension"]==dim and r["weighting"]=="raw")
        fmt = lambda v: "NA" if v is None else f"{v:.4f}"
        lines.append(f"|{dim}|{cs['A']['1']}/{cs['A']['0']}/{cs['A']['null']}|{cs['B']['1']}/{cs['B']['0']}/{cs['B']['null']}|{m['comparable_denominator']:g}|{fmt(m['observed_agreement'])}|{fmt(m['cohen_kappa'])}|")
    lines += ["", f"机械问题 {len(issues)} 项；二元分歧 {report['binary_disagreement_cell_N']} 个记录×维度；待定或无效配对 {report['pending_or_invalid_cell_N']} 个。", "",
              "AI–AI一致性只作实现诊断。P/R/F1和真人效度未评定；不自动扩样。加权Po/κ的Rao-Wu逐指标95%区间见agreement-intervals.csv，零分歧有限总体边界见JSON；不可用退化区间证明罕见误差不存在。", "",
              "null不填0。‘有理由待定’是null子集，仅核查理由字段是否填写，不自动验证其理由正确性。", "",
              "真人judge须先保存独立原件，再开放本分歧清单。"]
    (args.out / "核查说明.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(report["status"] + "；结果写入 " + str(args.out))
    return 1 if issues else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, UnicodeError) as exc:
        print("核查终止：" + str(exc), file=sys.stderr)
        sys.exit(2)
