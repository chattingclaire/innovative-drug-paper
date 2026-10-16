"""Supplementary descriptive department profiles after completed H600 submissions.

Uses paired sampled units and their already fixed survey weights. No significance
test, new confidence interval, rule revision or imputed reference is produced.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC', 'GOV')
NAMES = {'NMPA': '药监', 'NHSA': '医保', 'NHC': '卫健', 'GOV': '国务院/两办'}

def compute(data):
    assert data['status'] == 'completed_frozen_ID_join_not_validation_pass'
    assert data['design_and_interval_metadata']['sample_size_matches_H600_plan'] is True
    archive = data['archive']
    mapping_rows = archive['sampling_manifest_original']['rows']
    mapping = {row['id']: row for row in mapping_rows}
    rows = archive['normalized_rows_without_generated_reference']
    assert len(rows) == len(mapping) == len(mapping_rows) == 600
    assert len({row['id'] for row in rows}) == len(rows) and {row['id'] for row in rows} == set(mapping)
    grouped = defaultdict(list)
    for row in rows:
        meta = mapping[row['id']]
        assert meta['group'] in GROUPS and row['stratum'].split('|')[0] == meta['group']
        assert row['stratum'] == meta['stratum'] and row['N_h'] == meta['N_h'] and row['n_h'] == meta['n_h']
        grouped[meta['group']].append(row)
    output = {}
    for group in GROUPS:
        members = grouped[group]
        weighted_N = sum(r['N_h'] / r['n_h'] for r in members)
        population = sum(s['N_h'] for s in data['design_and_interval_metadata']['strata'] if s['stratum'].split('|')[0] == group)
        assert math.isclose(weighted_N, population, rel_tol=1e-12)
        result = {'sample_n': len(members), 'eligible_pool_department_N': population, 'weighted_sample_total': weighted_N, 'coders': {}}
        for coder in ('dictionary', 'A', 'C'):
            values = {}
            for dim in DIMS:
                hits = sum(r['N_h'] / r['n_h'] for r in members if r[coder][dim] == 1)
                pending = sum(r['N_h'] / r['n_h'] for r in members if r[coder][dim] == '待定')
                values[dim] = {'raw_positive': sum(r[coder][dim] == 1 for r in members),
                               'raw_pending': sum(r[coder][dim] == '待定' for r in members),
                               'weighted_positive_total': hits, 'weighted_pending_total': pending,
                               'positive_rate_completion_lower': hits / weighted_N if weighted_N else None,
                               'positive_rate_completion_upper': (hits + pending) / weighted_N if weighted_N else None}
            max_known = max(values[d]['weighted_positive_total'] for d in DIMS)
            # A dimension can be a (possibly tied) maximum in some completion iff
            # its all-pending-positive total reaches every other known-positive total.
            # Empty departments have no profile or ranking, including no all-zero tie.
            known_top = [d for d in DIMS if math.isclose(values[d]['weighted_positive_total'], max_known)] if weighted_N else []
            possible_top = [d for d in DIMS if values[d]['weighted_positive_total'] + values[d]['weighted_pending_total'] >= max_known - 1e-10] if weighted_N else []
            result['coders'][coder] = {'dimensions': values, 'largest_observed_positive_total_dimensions': known_top,
                                      'possible_top_dimensions_due_to_pending_only': possible_top}
        output[group] = result
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--json-output', type=Path, required=True)
    parser.add_argument('--report-output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.json_output.exists() and not args.report_output.exists(), 'Preserve existing export'
    raw = args.input.read_bytes()
    profiles = compute(json.loads(raw))
    out = {'status': 'supplementary_descriptive_H600_department_profile_not_confirmatory_test',
           'created_at': datetime.now(timezone.utc).isoformat(),
           'statistics_sha256': hashlib.sha256(raw).hexdigest(), 'profiles': profiles,
           'limitations': ['Same H600 rows and design weights for all three coders; inference scope remains U*, not all 4924 units.',
                           'Denominator is all weighted sampled analysis units in that department, not all dimension hits or equal-weighted source documents.',
                           'Pending completion ranges are deterministic bounds conditional on observed sampled labels, not confidence intervals.',
                           'Largest observed weighted-positive total and possible-top sets do not account for sampling error or shared AI error.',
                           'Possible-top includes ties: each listed dimension can be a maximum in some arbitrary binary completion; this is not a simultaneous rank-confidence set.',
                           'Supplementary descriptive check; it does not replace frozen primary performance estimates or validate causal/institutional explanations.']}
    lines = ['# H600部门维度分布的补充描述核对', '',
             '用同一600条的固定抽样权重，并列显示词典、A、C的逐部门结果。各维分母为该部门全部加权分析单元；不采用多标签命中总次数或来源等权分母。五维可同时命中，逐维命中率不要求加总为100%。推断范围仍限于排除已知开发材料后的U*，不直接对照全4924条作误差归因。', '',
             '这是补充描述检查，不是新增的预设显著性检验。区间仅表示待定标签任意补全的上下界；没有待定时显示一个数。这些范围不包含抽样误差或共享AI误差，首位描述也不证明总体排名稳定。可能首位集合允许并列，表示其中每一维可在某一种二元补全中达到最大，不是同时排名置信集合。没有部门样本时命中率及首位显示NA。', '',
             '| 部门（样本n） | 编码 | S命中率补全界 | E命中率补全界 | Ec命中率补全界 | I命中率补全界 | F命中率补全界 | 已判阳性加权量首位 | 考虑待定后可能首位（可并列） |',
             '|---|---|---:|---:|---:|---:|---:|---|---|']
    for group in GROUPS:
        for coder in ('dictionary', 'A', 'C'):
            profile = profiles[group]['coders'][coder]
            cells = []
            for dim in DIMS:
                v = profile['dimensions'][dim]
                lo, hi = v['positive_rate_completion_lower'], v['positive_rate_completion_upper']
                cells.append('NA' if lo is None else f'{lo:.1%}' if math.isclose(lo, hi) else f'{lo:.1%}—{hi:.1%}')
            title = '冻结词典' if coder == 'dictionary' else f'AI {coder}'
            lines.append('| ' + ' | '.join([f'{NAMES[group]}（{profiles[group]["sample_n"]}）', title, *cells,
                                           '/'.join(profile['largest_observed_positive_total_dimensions']) or 'NA',
                                           '/'.join(profile['possible_top_dimensions_due_to_pending_only']) or 'NA']) + ' |')
    lines += ['', '该表核对编码方式是否给出相近的样本分布。不能由维度命中率推出机构评分权重、人员认知或制度冲突；正文中的政策含义仍须由具体文本和其他实际证据支持。', '',
              f'统计输入：[{args.input.name}]({args.input.resolve()})；SHA-256 `{out["statistics_sha256"]}`。']
    with args.json_output.open('x') as handle:
        json.dump(out, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    with args.report_output.open('x') as handle:
        handle.write('\n'.join(lines) + '\n')
    print(json.dumps({'status': out['status'], 'groups': list(profiles)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
