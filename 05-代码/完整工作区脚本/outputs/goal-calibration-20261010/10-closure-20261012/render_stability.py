"""Render the existing final statistics, without running or changing a model.

Use only after the original all-five terminal statistics have been produced.
This is presentation code; it neither selects results nor computes new metrics.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CAMPAIGN = ROOT / '06-coding/current-freeze-stability-external-capture-v2-sol/prepared-fixed800-87-v2'
SOURCE = CAMPAIGN / 'terminal-stability-statistics.json'
CONDITIONS = ('R1', 'R2', 'R3', 'W', 'H')
DIMS = ('S', 'E', 'Ec', 'I', 'F')
DOMAINS = {'fixed800': 800, 'remaining600': 600, 'exposed200': 200}
PAIRS = ('R1/R2', 'R1/R3', 'R2/R3', 'W/R1', 'H/R1')


def checked_json(binding):
    raw = Path(binding['path']).read_bytes()
    if len(raw) != binding['bytes'] or hashlib.sha256(raw).hexdigest() != binding['sha256']:
        raise ValueError('Changed input: ' + binding['path'])
    return json.loads(raw)


def fmt(value):
    return 'NA' if value is None else f'{value:.6g}' if isinstance(value, float) else str(value)


def cells(table):
    return '/'.join(fmt(table['cells'][key]) for key in ('n00', 'n01', 'n10', 'n11'))


def render(result, metadata, source_sha):
    if result.get('all_five_conditions_terminal') is not True:
        raise ValueError('All five conditions must be terminal')
    projection = result['original_record_projection']
    if projection.get('all_five_conditions_all_batches_terminal') is not True:
        raise ValueError('Original record projection is not terminal')
    ids = [row['source_id'] for row in metadata]
    if len(ids) != len(set(ids)) or len(ids) != 800:
        raise ValueError('Expected the original 800 unique assignments')
    members = {'fixed800': set(ids)}
    members.update({name: {r['source_id'] for r in metadata if r['domain'] == domain}
                    for name, domain in (('remaining600', 'remaining'), ('exposed200', 'exposed'))})
    if {k: len(v) for k, v in members.items()} != DOMAINS:
        raise ValueError('Historical sample groups changed')
    if set(result['domains']) != set(DOMAINS) or set(projection['conditions']) != set(CONDITIONS):
        raise ValueError('Incomplete final result')
    for condition in CONDITIONS:
        rows = projection['conditions'][condition]
        row_ids = [r['source_id'] for r in rows]
        if len(row_ids) != 800 or len(set(row_ids)) != 800 or set(row_ids) != set(ids):
            raise ValueError('Original assignments changed or contain duplicates')
        for row in rows:
            labels = row['labels']
            if labels is None:
                if row['status'] not in ('technical_fail', 'not_called'):
                    raise ValueError('Unknown terminal failure state')
            elif row['status'] != 'valid' or set(labels) != set(DIMS) or any(
                v is not None and (type(v) is not int or v not in (0, 1)) for v in labels.values()
            ):
                raise ValueError('Malformed final label projection')
    lines = ['# 重复稳定性与请求敏感性结果', '',
             'R1/R2/R3为同条件重复；W改变JSON展示格式，H改变请求首行的等义表述。下列值直接来自原定统计入口，技术失败与合法待定分开计数。', '',
             '这是机器稳定性诊断，不是分类准确率或真人信度检验。未设统一0.80通过线，也未新增区间下限门槛。共同有效子集的结果不能代表完整800条或全4481条。', '',
             f'统计来源：[原始JSON]({SOURCE})；SHA256 `{source_sha}`。', '',
             '## 覆盖与待定', '',
             '| 历史分组 | 条件 | 计划条数 | 技术有效 | 其中至少一维待定 | 技术失败 | 未调用 |',
             '|---|---|---:|---:|---:|---:|---:|']
    for domain, n in DOMAINS.items():
        for condition in CONDITIONS:
            rows = [r for r in projection['conditions'][condition] if r['source_id'] in members[domain]]
            states = Counter(r['status'] for r in rows)
            null_n = sum(r['labels'] is not None and any(v is None for v in r['labels'].values()) for r in rows)
            if len(rows) != n:
                raise ValueError('Coverage denominator differs')
            lines.append(f"| {domain} | {condition} | {n} | {states['valid']} | {null_n} | {states['technical_fail']} | {states['not_called']} |")
    lines += ['', 'remaining600/exposed200为原抽样分组，继续保留原概率和权重。当前开发曝光交叉身份另见[总进度](../总进度.md)，不能把历史remaining600全部称为当前未参与开发。', '',
              '待定列是技术有效记录的子集，不能与技术有效数相加。失败和未调用不补0；逐维待定数及重叠排除模式保留在原始JSON。']
    for domain, n in DOMAINS.items():
        value = result['domains'][domain]
        if value['scheduled_N'] != n or set(value['pairs']) != set(PAIRS):
            raise ValueError('Final domain or planned comparisons changed')
        lines += ['', f'## {domain}：逐维共同可比结果', '',
                  '四格依次为n00/n01/n10/n11；行对应配对名称的第一条件，列对应第二条件，双方均不是真值。', '',
                  '| 配对 | 维度 | 共同二元n | 排除n | 原始四格 | 原始一致率 | 原始κ | 加权四格 | 加权一致率 | 加权κ | κ为NA的原因 |',
                  '|---|---|---:|---:|---|---:|---:|---|---:|---:|---|']
        for pair in PAIRS:
            for dim in DIMS:
                item = value['pairs'][pair]['dimensions'][dim]
                raw, weighted, accounting = item['raw'], item['weighted'], item['domain']
                if accounting['joint_comparable_n'] + accounting['excluded_n'] != n:
                    raise ValueError('Comparable and excluded counts do not exhaust scheduled sample')
                reason = raw['kappa_na_reason'] or weighted['kappa_na_reason'] or '—'
                lines.append(f"| {pair} | {dim} | {accounting['joint_comparable_n']} | {accounting['excluded_n']} | {cells(raw)} | {fmt(raw['Po'])} | {fmt(raw['kappa'])} | {cells(weighted)} | {fmt(weighted['Po'])} | {fmt(weighted['kappa'])} | {reason} |")
        groups = [('R1/R2/R3', value['triple'])] + [(p, value['pairs'][p]) for p in PAIRS]
        lines += ['', '### 五维向量共同一致性', '',
                  '| 比较组 | 共同五维二元n | 完全一致n | 排除n | 原始完全一致率 | 加权完全一致率 | 技术有效交集n | 交集中至少一维待定n |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|']
        for name, group in groups:
            vector, nulls = group['five_dimension_vector'], group['semantic_null_patterns']
            lines.append(f"| {name} | {vector['denominator_n']} | {vector['agreement_n']} | {vector['domain']['excluded_n']} | {fmt(vector['complete_agreement_rate'])} | {fmt(vector['weighted_complete_agreement_rate'])} | {nulls['both_or_all_technically_valid_n']} | {nulls['at_least_one_semantic_null_n']} |")
        lines += ['', '### 同一共同子集上的注意力份额', '',
                  '每组使用五维均可二元比较的共同记录和同一原抽样权重；每次的份额分母为该次五维阳性赋值总和。下列份额为0—1比例，极差换算为百分点。', '',
                  '| 比较组 | 条件 | 共同记录n | 原始Σ5T | 加权Σ5T | 加权S | 加权E | 加权Ec | 加权I | 加权F |',
                  '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        for name, group in groups:
            for condition, q in group['q']['by_run'].items():
                shares = ' | '.join(fmt(q['weighted_q'][d]) for d in DIMS)
                lines.append(f"| {name} | {condition} | {q['common_record_n']} | {q['unweighted_sum5T']} | {fmt(q['weighted_sum5T'])} | {shares} |")
        lines += ['', '| 比较组 | S极差pp | E极差pp | Ec极差pp | I极差pp | F极差pp |',
                  '|---|---:|---:|---:|---:|---:|']
        for name, group in groups:
            ranges = group['q']['q_ranges']['weighted_q']
            values = ' | '.join(fmt(None if ranges[d]['range'] is None else 100 * ranges[d]['range']) for d in DIMS)
            lines.append(f'| {name} | {values} |')
    lines += ['', '原始JSON保留逐项原答指针、逐维阳性边际、标签变化名单、重叠排除、待定模式及未加权份额。退化分母保持NA。本报告不补写原统计入口没有计算的置信区间，也不据此判定正式准确性验收。', '']
    return '\n'.join(lines)


def main():
    # No campaign outputs are opened unless its final statistics file exists.
    raw = SOURCE.read_bytes()
    result = json.loads(raw)
    metadata = checked_json(result['original_record_projection']['source_metadata'])
    text = render(result, metadata, hashlib.sha256(raw).hexdigest())
    directory = HERE / 'stability-results'
    directory.mkdir(exist_ok=True)
    output = directory / '稳定性与敏感性结果.md'
    with output.open('x', encoding='utf-8') as handle:
        handle.write(text)
    print(json.dumps({'output': str(output), 'new_statistics_computed': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
