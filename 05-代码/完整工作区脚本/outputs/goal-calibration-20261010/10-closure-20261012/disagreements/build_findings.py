#!/usr/bin/env python3
"""Reconcile existing semantic audit evidence; never classify new records or alter labels."""
import collections
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CURRENT = ROOT / '07-statistics/current-full4481-v11-v16-source-aligned-diagnostics-root'
RARE = ROOT / '08-audits/current-machine-rare-disagreement-semantic-20261011-sol'
AUX = ROOT / '08-audits/ai800-disagreement-semantic-root'
MANUAL = ROOT / '03-manual/full4481-common-release-20261010-root/manual.txt'
OLD_MATERIALS = ROOT.parent / 'ai-audit800-20261010/source-A/coder-A/materials'
DIMENSIONS = {'S': '安全性', 'E': '有效性', 'Ec': '经济性', 'I': '创新性', 'F': '公平性'}

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def binding(path):
    path = Path(path)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def key(row):
    return row.get('source_id', row.get('id')), row.get('dimension', row.get('dim'))

def dereference(obj, pointer):
    for p in pointer.strip('/').split('/'):
        p = p.replace('~1', '/').replace('~0', '~')
        obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    return obj

def status_counts(rows):
    return dict(collections.Counter(x['status'] for x in rows))

def summarise(rows):
    return {
        'slots': len(rows),
        'unique_records': len({r['id'] for r in rows}),
        'by_dimension': dict(collections.Counter(r['dimension'] for r in rows)),
        'position_counts': dict(collections.Counter(r['retained_position'] for r in rows)),
        'binary_disagreements': sum(r['current_rule'] in (0, 1) and r['current_native'] in (0, 1) for r in rows),
    }

current_rows = [json.loads(s) for s in (CURRENT / 'machine-pair-disagreements.jsonl').read_text().splitlines()]
current = {key(r): r for r in current_rows}
assert len(current) == len(current_rows)
metrics = read(CURRENT / 'metrics.json')
manual_sha = sha(MANUAL)
source_bindings = [binding(CURRENT / 'machine-pair-disagreements.jsonl'), binding(CURRENT / 'metrics.json'), binding(MANUAL)]
packet_cache = {}

def current_packet(row):
    path = row['packet']['path']
    if path not in packet_cache:
        assert sha(path) == row['packet']['sha256'], path
        packet_cache[path] = read(path)
    return packet_cache[path]

rare_file = RARE / 'final130/semantic-reviews130.json'
rare_rows = read(rare_file)
old_disagreement_file = ROOT / '07-statistics/current-v7-machine-diagnostics-20261011T1543-root/machine-pair-disagreements.jsonl'
old_disagreement = {key(r): r for r in map(json.loads, old_disagreement_file.read_text().splitlines())}
second_file = RARE / 'semantic-second-check/selected-mechanism-reviews.json'
second = {key(r): r for r in read(second_file)}
supplement_file = RARE / 'supplement-restricted-mother-object-20261012-sol/report.json'
supplement = {key(r): r for r in read(supplement_file)['positions']}
v9_file = ROOT / '08-audits/v9-repair-adoption-independent-20261012-sol/semantic-and-design-phase01/focused-semantic-positions.json'
v9 = {f'RECODE25-{k}': r for r in read(v9_file) for k in r['ids']}
source_bindings += [binding(p) for p in (rare_file, old_disagreement_file, second_file, supplement_file, v9_file)]
rare_match, rare_reconciliation = [], []
for row in rare_rows:
    k = key(row)
    now = current.get(k)
    old_values = row['machine_values']
    old_pair = (old_values['rules_v7'], old_values['native_original_whole_batch'])
    record = {'id': k[0], 'dimension': k[1], 'old_pair': list(old_pair), 'original_position': row['review_class']}
    if k in supplement:
        record['supplement_position'] = supplement[k]
    if not now:
        record['status'] = 'no_longer_current_disagreement'
    elif row['current_direct_material']['packet']['sha256'] != now['packet']['sha256']:
        record['status'] = 'source_packet_changed'
    elif old_pair != (now['rule'], now['native']):
        record['status'] = 'machine_label_pair_changed'
        record['current_pair'] = [now['rule'], now['native']]
    else:
        packet = current_packet(now)
        material = row['current_direct_material']
        assert material['quote'] == dereference(packet, material['pointer'])
        previous = old_disagreement[k]
        assert previous['packet']['sha256'] == now['packet']['sha256']
        same_native_output = previous['native_first']['sha256'] == now['native_first']['sha256']
        assert same_native_output
        assert all(e['sha256'] == manual_sha for e in row['frozen_manual_evidence'])
        position = supplement.get(k, {}).get('position', row['review_class'])
        record['status'] = 'same_material_and_same_machine_pair'
        item = {
            'id': k[0], 'dimension': k[1], 'evidence_tier': 'A_original_native_pair_audit',
            'current_rule': now['rule'], 'current_native': now['native'],
            'retained_position': position,
            'original_position': row['review_class'],
            'pattern': row['error_or_boundary_pattern'],
            'reason': supplement.get(k, {}).get('reason', row['reason']),
            'current_quote': material['quote'], 'current_packet': now['packet'],
            'current_native_output': now['native_first'],
            'same_original_native_output_sha256': same_native_output,
            'old_review_file': binding(rare_file),
            'old_review_index_0based': rare_rows.index(row),
            'source_packet_sha_match': True, 'manual_sha_match': True,
            'second_check': second.get(k),
            'subsequent_v9_opinion': v9.get(f'{k[0]}/{k[1]}'),
            'not_human_gold': True,
        }
        rare_match.append(item)
    rare_reconciliation.append(record)

# The older comparison used an auxiliary AI, not the production LLM.  Its source
# bundle must equal the current bundle in full; equal label values do not turn it
# into an audit of the production LLM's reasoning or into an independent reference.
aux_sources = [
    'safety89-sol/reviews.json', 'effectiveness49-sol/reviews-scoped.json',
    'economic87-sol/reviews.json', 'innovation-first22-sol/reviews.json',
    'innovation-last22-sol/reviews.json', 'fairness-root-review.json',
]
e_bindings_file = AUX / 'effectiveness49-sol/input-bindings.json'
e_bindings = {x['path']: x['sha256'] for x in read(e_bindings_file)['files']}
joined_file = AUX / 'joined-review.json'
joined = {key(r): r for r in read(joined_file)['rows']}
source_bindings += [binding(e_bindings_file), binding(joined_file)]
aux_match, aux_reconciliation = [], []
for relative in aux_sources:
    path = AUX / relative
    source_bindings.append(binding(path))
    data = read(path)
    rows = data if isinstance(data, list) else data['rows']
    for index, row in enumerate(rows):
        k = key(row)
        now = current.get(k)
        old_pair = (row.get('rule'), row.get('ai', row.get('AI')))
        record = {'id': k[0], 'dimension': k[1], 'old_auxiliary_pair': list(old_pair), 'review_file': str(path)}
        if not now:
            record['status'] = 'not_a_current_disagreement'
        elif old_pair != (now['rule'], now['native']):
            record['status'] = 'old_auxiliary_pair_differs_from_current_native_pair'
            record['current_pair'] = [now['rule'], now['native']]
        else:
            old_path = row.get('current_location', {}).get('file') or row.get('current_source', {}).get('file') or str(OLD_MATERIALS / (row['blind_id'] + '.json'))
            old_expected_sha = row.get('read_material_sha256') or row.get('current_source', {}).get('sha256') or row.get('packet_sha256') or e_bindings.get(old_path)
            assert old_expected_sha is not None, (relative, k, 'no old material hash')
            assert sha(old_path) == old_expected_sha, (relative, k, 'old material modified')
            old_bundle = read(old_path)
            packet = current_packet(now)
            if old_bundle != packet['source_bundle']:
                record['status'] = 'source_bundle_changed'
            else:
                recorded_text = next((row[name] for name in ('current_original', 'current_text', 'current_quote') if row.get(name)), None)
                assert recorded_text == old_bundle['source_record']['text'], (relative, k, 'current text mismatch')
                explicit_manual_sha = row.get('manual_sha256') or data.get('manual_sha256') if isinstance(data, dict) else row.get('manual_sha256')
                if explicit_manual_sha:
                    assert explicit_manual_sha == manual_sha
                # Use the integrated older review where present; retain its detailed
                # source and all boundary flags. No replacement labels are produced.
                opinion = joined.get(k, row)
                review_value = opinion.get('review_value')
                needs_review = bool(row.get('needs_human_review') or opinion.get('needs_human_review'))
                if needs_review or review_value not in (0, 1):
                    position = '边界待定'
                elif review_value == now['rule']:
                    position = '既有审核更支持当前规则标签'
                elif review_value == now['native']:
                    position = '既有审核更支持当前LLM标签'
                else:
                    position = '无法映射'
                record['status'] = 'same_source_bundle_and_matching_label_values_only'
                item = {
                    'id': k[0], 'dimension': k[1],
                    'evidence_tier': 'B_older_auxiliary_AI_semantic_evidence',
                    'current_rule': now['rule'], 'current_native': now['native'],
                    'retained_position': position,
                    'old_review_value_preserved': review_value,
                    'original_assessment': opinion.get('assessment', row.get('assessment')),
                    'needs_human_review_preserved': needs_review,
                    'reason': opinion.get('reason') or row.get('reason') or row.get('explanation'),
                    'current_quote': old_bundle['source_record']['text'],
                    'current_packet': now['packet'],
                    'old_material': binding(old_path),
                    'old_review_file': binding(path), 'old_review_index_0based': index,
                    'integrated_opinion_file': binding(joined_file) if k in joined else None,
                    'source_bundle_full_object_equal': True,
                    'same_label_values_do_not_establish_same_model_or_reasoning': True,
                    'not_human_gold': True,
                }
                aux_match.append(item)
        aux_reconciliation.append(record)

all_evidence = rare_match + aux_match
assert len({key(r) for r in all_evidence}) == len(all_evidence)
covered = {key(r) for r in all_evidence}
binary = [r for r in current_rows if r['rule'] in (0, 1) and r['native'] in (0, 1)]
null_disagreement = [r for r in current_rows if r['rule'] is None or r['native'] is None]
assert len(binary) + len(null_disagreement) == len(current_rows)
directions = collections.Counter(f"{r['rule']}→{r['native']}" for r in binary)
uncovered = [r for r in current_rows if key(r) not in covered]
dim_counts = []
for d, title in DIMENSIONS.items():
    rows = [r for r in current_rows if r['dimension'] == d]
    pair = metrics['machine_pair_agreement_not_accuracy'][d]
    dim_counts.append({'dimension': d, 'name': title, 'all_disagreement_slots': len(rows),
                       'binary_disagreement_slots': sum(r['rule'] in (0,1) and r['native'] in (0,1) for r in rows),
                       'one_side_null_disagreement_slots': sum(r['rule'] is None or r['native'] is None for r in rows),
                       'covered_slots': sum(key(r) in covered for r in rows), **pair})
null_direction = collections.Counter(f"{r['rule']}→{r['native']}" for r in null_disagreement)
findings = {
    'created_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
    'task': 'Version-aligned synthesis of existing semantic disagreement evidence only',
    'unit': 'record × dimension; not unique policy clauses unless explicitly labelled',
    'source_bindings': source_bindings,
    'current_counts': {'all_disagreement_slots': len(current_rows), 'unique_records': len({r['id'] for r in current_rows}),
                       'binary_disagreement_slots': len(binary), 'binary_direction_rule_to_native': dict(directions),
                       'one_side_null_disagreement_slots': len(null_disagreement), 'null_direction_rule_to_native': dict(null_direction),
                       'per_dimension': dim_counts},
    'final130_reconciliation': {'all_old_review_slots': len(rare_rows), 'status_counts': status_counts(rare_reconciliation),
                                'matched_summary': summarise(rare_match), 'entries': rare_reconciliation},
    'older_auxiliary_review_reconciliation': {'old_review_slots_including_common_positive_checks': len(aux_reconciliation),
                                            'status_counts': status_counts(aux_reconciliation),
                                            'matched_summary': summarise(aux_match), 'entries': aux_reconciliation},
    'current_evidence_coverage': {'all_matched_existing_semantic_slots': len(all_evidence),
                                'unique_records': len({r['id'] for r in all_evidence}),
                                'covered_binary_slots': len(all_evidence), 'covered_null_slots': 0,
                                'binary_slots_without_matched_evidence_in_this_synthesis': len(binary) - len(all_evidence),
                                'null_slots_without_matched_evidence_in_this_synthesis': len(null_disagreement),
                                'all_slots_without_matched_evidence_in_this_synthesis': len(uncovered),
                                'does_not_mean_other_evidence_cannot_exist': True},
    'matched_evidence': all_evidence,
    'uncovered_current_slots': [{'id':r['id'],'dimension':r['dimension'],'rule':r['rule'],'native':r['native']} for r in uncovered],
    'limitations': [
        'Non-random, previously exposed AI-assisted semantic review; no population error-rate or accuracy estimate.',
        'Tier A reuses an old production-native comparison on unchanged source and unchanged label values; it is not a new blind review.',
        'Tier B is older auxiliary-AI evidence. Identical current labels and source bundles do not establish the same model, output, or reasoning.',
        'A retained semantic preference is a diagnostic opinion, not a new human adjudication or a replacement label.',
        'Material hash equality proves material identity, not correctness or that a reviewer actually read it.',
        'A slot absent from current disagreement is not automatically correct or semantically repaired.',
        '270 one-side-null disagreements are lawful semantic pending labels in these output files, not 270 execution failures or binary classification errors.',
        'The coverage ledger does not certify exhaustive discovery of every historical review; it specifies the full finite source collections reconciled here.',
        'No human200 material or answers opened; no source/label/manual/prompt modified; no classification calls issued.',
    ],
    'formal_validation_complete': False,
    'labels_modified': False,
}
(OUT / 'findings.json').write_text(json.dumps(findings, ensure_ascii=False, indent=2) + '\n')

lines = [
    '# 当前分歧与既有语义证据的版本核对', '',
    '本文件只归并已有审核，不新增分类、不改机器标签，也不裁定真人参照。计数单位为“记录×维度”；同一条记录可出现多个维度分歧。', '',
    f'当前共有 **{len(current_rows)}项分歧**：**{len(binary)}项二元分歧**和**{len(null_disagreement)}项一方待定的分歧**。二元分歧中规则0/LLM1为{directions["0→1"]}项（{directions["0→1"]/len(binary):.2%}），规则1/LLM0为{directions["1→0"]}项。', '',
    '待定项单独保留。这里的NULL来自合法语义待定，不是运行技术失败；不将其塞入0/1四格表，也不把待定分歧与二元分歧混作错误率。', '',
    '| 维度 | 二元分歧 | 一方待定分歧 | 同为二元的比较数 | 实际一致率 | κ | 正类一致性 | 本次匹配已有语义记录 |',
    '|---|---:|---:|---:|---:|---:|---:|---:|',
]
for d in dim_counts:
    lines.append(f'| {d["name"]} | {d["binary_disagreement_slots"]} | {d["one_side_null_disagreement_slots"]} | {d["binary_pair_N"]} | {d["Po"]:.2%} | {d["kappa"]:.3f} | {d["positive_agreement"]:.2%} | {d["covered_slots"]} |')
lines += [
    '', '## 旧审核能够保留到当前版本的范围', '',
    '**原final130不能整体沿用。** 逐条核对ID、维度、材料包哈希、规则/LLM标签和原LLM输出哈希后：117项已不在当前分歧表，4项标签对已变化，只有9项完全匹配。9项中8项原判断为边界待定、1项为更支持规则。当前不再分歧只说明两法同值，不能由此证明已经正确修复。', '',
    '00068/I、00071/I、00071/F的后补意见已经纳入核对：旧“支持LLM”说法已被补充为边界待定，且这3项当前标签对也已变化，不能作为同标签保留样例。02209/I的原集成补充也不被外推：它已不在当前分歧表。', '',
    f'另核对早期辅助AI审核的S、E、Ec、I、F六组完整记录，共{len(aux_reconciliation)}项（含原有共同阳性抽查）。其中{len(aux_match)}项满足**旧材料哈希未变、整个source_bundle与当前相等、标签数值与当前一致**。这{len(aux_match)}项只能作为可迁移的旧语义证据：当时比较对象是辅助AI，不是当前生产LLM，不能叫“当前LLM已完成独立审核”。', '',
    f'两层证据合计覆盖当前{len(all_evidence)}项二元分歧；仍有 **{len(binary)-len(all_evidence)}项二元分歧和{len(null_disagreement)}项待定分歧**未被本次有限归并覆盖。它们的ID和维度完整保存在findings.json中。旧审核采用非随机选择、已曝光材料和AI辅助判断；这些计数不能估计全体错误率，也不能替代独立人工gold。', '',
    '## 直接匹配原生产LLM审核的9项', '',
    '| 记录/维度 | 当前规则/LLM | 保留的语义判断 | 分歧机制 |',
    '|---|---|---|---|',
]
for r in rare_match:
    lines.append(f'| {r["id"]}/{r["dimension"]} | {r["current_rule"]}/{r["current_native"]} | {r["retained_position"]} | {r["pattern"]} |')
lines += ['', '可以直接追溯的典型样例：', '']
for sample in ('RECODE25-00105/F', 'RECODE25-01386/I', 'RECODE25-01482/F'):
    r = next(x for x in rare_match if f'{x["id"]}/{x["dimension"]}' == sample)
    lines += [f'- **{sample}**：{r["reason"]}', f'  原文：“{r["current_quote"]}”']
lines += [
    '', '## 旧辅助审核提供的机制样例', '',
    '以下例子均完成材料与当前标签核对，保留原审核倾向而不将其改写成已确证的错误。', '',
]
samples = {
    'RECODE25-01353/S': '规则遗漏候选：具体风险控制',
    'RECODE25-01705/Ec': '规则遗漏候选：实质经济信息核验',
    'RECODE25-02826/S': 'LLM过度推断候选：从指南主题扩展到一般沟通',
    'RECODE25-03455/I': 'LLM过度推断候选：把一般设计建议解释为实质改良',
    'RECODE25-00241/E': '概念边界：药效方法与效果证据',
    'RECODE25-00069/I': '上下文承接争点：需保留受限对象链的审查',
}
for sample, title in samples.items():
    r = next(x for x in aux_match if f'{x["id"]}/{x["dimension"]}' == sample)
    lines += [f'- **{title}（{sample}；规则{r["current_rule"]}/LLM{r["current_native"]}）**：{r["reason"]}']
lines += [
    '', '00069/I的旧意见引入了突破性程序对象来解释附条件批准阶段的机会，保留原文供核定；数值及材料相等不等于本轮重新确认这条对象链。已知00068/00071补充意见对受限母对象的提醒不能省略，也不能把未明确覆盖00069的补充擅自改写为其裁定。', '',
    '材料不足作为单独状态保留在当前NULL及其理由中。本次匹配的60项均为二元分歧，不声称已经完成270项待定材料的逐条核定。', '',
    '## 可以据此写出的结论与后续用途', '',
    '现有证据支持“分歧有明显方向且存在可解释机制”：LLM判阳性更广，争点包括具体内容与一般形式的区分、有限语境承接、制度适用对象及概念边界；部分既有审核倾向规则，部分倾向LLM，还有边界待定。不能把所有分歧解释为规则漏判或LLM误判。', '',
    '公平性二元比较的一致率98.25%而κ为0.692，同时正类一致性为70.04%。这三个量应同时报告；大量共同阴性和类别分布会影响κ，但不能以高总体一致率掩盖相关条款识别上的分歧。此处是当前四格表的代数描述，不另立κ≥0.80的机间验收门槛。', '',
    '独立人工材料回收后，应依据其独立结果计算准确性并裁定，而不是用这些已曝光的诊断样例代填。部门与年度结论是否受影响，要连接既有稳健性输出另行核对；本文件没有据总体方向替代该检验。', '',
    '## 可复核文件', '',
    f'- 当前分歧表：`{CURRENT / "machine-pair-disagreements.jsonl"}`',
    f'- 当前四格表及指标：`{CURRENT / "metrics.json"}`',
    f'- 原130项逐条审核：`{rare_file}`',
    f'- 受限母对象补充意见：`{supplement_file}`',
    '- findings.json记录输入哈希、逐条纳入/排除原因、当前样例材料绑定和全部未覆盖分歧。',
    '- build_findings.py可重复运行以上机械核对；不会发起分类调用。',
    '', '本轮没有打开人工200材料包或答案，没有修改任何生产标签、手册、提示或论文正文。',
]
(OUT / 'findings.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'final130': status_counts(rare_reconciliation), 'auxiliary': status_counts(aux_reconciliation), 'coverage': findings['current_evidence_coverage'], 'per_dimension': dim_counts}, ensure_ascii=False, indent=2))
