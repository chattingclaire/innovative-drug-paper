"""Diagnostic only: current actual machines against the adopted existing A/C streams.

No historical context/method loader, model call, new human review, or label edit.
"""
from pathlib import Path
from collections import Counter
import argparse
import csv
import hashlib
import importlib
import json
import sys

HERE = Path(__file__).resolve().parent
NOTE = '新机器编码—既有真人事后复核参照的诊断比较，本轮共同手册兼容尚待确认'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def bound(binding):
    p = Path(binding['path'])
    require(p.is_absolute() and sha(p) == binding['sha256'], 'Binding mismatch: ' + str(p))
    return p


def read(binding):
    return json.loads(bound(binding).read_text())


def rows(binding):
    rr = [json.loads(x) for x in bound(binding).read_text().splitlines() if x.strip()]
    byid = {r['id']: r for r in rr}
    require(len(rr) == len(byid), 'Duplicate IDs')
    return byid


def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def output_tables(records, suffix):
    fields = ['component', 'group', 'weighting', 'comparison', 'dimension', 'unit_n', 'paired_n',
              'pending_n', 'n11', 'n10', 'n01', 'n00', 'weighted11', 'weighted10', 'weighted01',
              'weighted00', 'kappa', 'precision', 'recall', 'f1', 'agreement',
              'left_positive_rate', 'right_positive_rate']
    for component, filename in [('probability_canonical', '概率180'), ('enriched_challenge', '挑战60')]:
        selected = [r for r in records if r['component'] == component]
        with (HERE / (filename + '-指标长表' + suffix + '.csv')).open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
            for r in selected:
                row = {k: r[k] for k in fields if k in r}
                row.update(dict(zip(('n11', 'n10', 'n01', 'n00'), r['raw_cells'])))
                row.update(dict(zip(('weighted11', 'weighted10', 'weighted01', 'weighted00'), r['weighted_cells'])))
                row.update(r['point']); writer.writerow({k: 'NA' if row.get(k) is None else row.get(k) for k in fields})
        wide = {}
        for r in selected:
            key = (r['group'], r['comparison'], r['weighting'])
            wide.setdefault(key, {})[r['dimension']] = r['point']['kappa']
        with (HERE / (filename + '-五维κ表' + suffix + '.csv')).open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f); writer.writerow(['部门', '比较', '权重', 'S', 'E', 'Ec', 'I', 'F'])
            for key, vals in wide.items():
                writer.writerow([*key, *[vals[d] if vals[d] is not None else 'NA' for d in ('S', 'E', 'Ec', 'I', 'F')]])


def markdown(records, source_report):
    lines = ['# 最新机器与既有 A/C 参照比较', '', NOTE + '。', '',
             'A/C 为原最终采用的两条参照流；保留 AI 生成沿革和用户确认的真人事后复核事实，不称本轮新独立真人盲评。', '',
             '概率 180 每部门 60。总体主表按原剩余规范代表框架权重 N_h/60（947、760、60）计算，部门内该权重为常数。挑战 60 独立呈现，不并入概率总体。κ/P/R/F1 是相对既有 A 或 C 标签的诊断值，不能据此宣布共同手册下最终效度。', '',
             '零分母为 NA；A/C 仅列对称 κ、一致率和标签比例。当前句文本与旧样本核验结果见材料差异说明。', '']
    for component, title in [('probability_canonical', '概率180五维κ'), ('enriched_challenge', '挑战60五维κ')]:
        lines += ['## ' + title, '', '| 部门 | 比较 | S | E | Ec | I | F |', '|---|---|---:|---:|---:|---:|---:|']
        buckets = {}
        for r in records:
            if r['component'] == component:
                buckets.setdefault((r['group'], r['comparison']), {})[r['dimension']] = r['point']['kappa']
        for key, vals in buckets.items():
            lines.append('| ' + ' | '.join([*key, *['NA' if vals[d] is None else f'{vals[d]:.4f}' for d in ('S','E','Ec','I','F')]]) + ' |')
        lines.append('')
    lines += ['## 材料边界', '',
              f"00064 与概率180交集：{source_report['source_gap_probability180_intersection']}；与挑战60交集：{source_report['source_gap_challenge60_intersection']}。",
              f"240条当前句文本全部与原v14和抽样text SHA相等：{source_report['all_sample_text_equal']}。文本相等不意味着材料、语境或手册相同。", '',
              '已记录的新增共享语境六条（正文不变）：' + '、'.join(r['id'] for r in source_report['documented_six_shared_context_additions']) + '。完整当前语境和旧v14语境、各自SHA另存材料差异说明；旧字典与当前纯来源列表的表示差异独立披露，不据文本相等宣布同材料。', '',
              '点估计详表含四格、P/R/F1与A/C对称指标。5000次区间如有输出，仅按原抽样机制且条件于固定标签及既有参照；不涵盖共同手册兼容未确认、语义真值或来源补全的不确定性。']
    (HERE / '诊断比较结果01.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bindings-sha256', required=True)
    parser.add_argument('--bootstrap', action='store_true')
    args = parser.parse_args()
    binding = {'path': str(HERE / 'actual_bindings01.json'), 'sha256': args.bindings_sha256}
    cfg = read(binding)
    require(sha(Path(__file__)) == cfg['calculation_code']['sha256'], 'Calculation code changed')
    old = read(cfg['adopted_final_manifest'])
    require(old['root_final_bindings_confirmed'] is True and cfg['references'] == old['references'] and
            cfg['sampling_design'] == old['sampling_design'], 'A/C or design is not the adopted binding')
    for b in cfg['mathematical_sources'].values():
        bound(b)
    sys.path.insert(0, str(bound(cfg['mathematical_sources']['statistical_core_r3']).parent))
    c = importlib.import_module('statistical_core_r3')
    e = importlib.import_module('statistical_extensions_r3')
    for name, module in [('statistical_core_r3', c), ('statistical_extensions_r3', e)]:
        require(Path(module.__file__).resolve() == bound(cfg['mathematical_sources'][name]).resolve(), 'Unexpected mathematical import')
    design = read(cfg['sampling_design']); sample = {r['original_id']: r for r in design['sample']}
    require(len(sample) == 240 and design['frame_N_by_group'] == c.EXPECTED_ELIGIBLE, 'Design changed')
    require(Counter((r['component'], r['group']) for r in sample.values()) == Counter(
        {('probability_canonical', g): 60 for g in c.GROUPS} | {('enriched_challenge', g): 30 for g in ('NMPA', 'NHSA')}), 'Sample changed')
    current = rows(cfg['current_material']); legacy = rows(cfg['legacy_material'])
    rule_input = rows(cfg['current_rule_material'])
    metadata = read(cfg['department_metadata']); meta = {Path(r['original_file']).stem: r for r in metadata['rows']}
    groups = {rid: meta[r['input']['original_file_stem']]['analysis_group'] for rid, r in rule_input.items()}
    refs = {name: rows(b) for name, b in cfg['references'].items()}
    require(all(set(rr) == set(sample) for rr in refs.values()), 'A/C sample differs')
    methods = {}
    for name, entry in cfg['methods'].items():
        qa = read(entry['execution_qa']); summary = read(entry['execution_summary'])
        require(qa['all_checks_pass'] is True and qa['output_sha256'] == entry['output']['sha256'] and
                qa['input_sha256'] == entry['input_sha256'], 'Actual method QA binding differs')
        require(summary['output_sha256'] == entry['output']['sha256'] and summary['n'] == 4924, 'Actual method summary differs')
        methods[name] = rows(entry['output'])
        require(len(methods[name]) == 4924 and set(methods[name]) == set(current), 'Actual output corpus differs')
    policy = read(cfg['analysis_source_missing_policy']); gap = {r['id'] for r in policy['rows']}
    probability = {rid for rid, r in sample.items() if r['component'] == 'probability_canonical'}
    challenge = set(sample) - probability
    require(gap == {'RECODE25-00064'} and not gap & set(sample), 'Source gap unexpectedly enters A/C sample')
    for rid, s in sample.items():
        require(s['group'] == groups[rid] and current[rid]['text'] == legacy[rid]['text'] == rule_input[rid]['input']['unit_text'] and
                hashlib.sha256(current[rid]['text'].encode()).hexdigest() == s['unit_text_sha256'], 'Sample text/group changed: ' + rid)
        if s['component'] == 'probability_canonical':
            require(s['sample_n'] == 60 and s['canonical_frame_N'] == c.EXPECTED_ELIGIBLE[s['group']] and
                    abs(s['analysis_weight'] - s['canonical_frame_N'] / 60) < 1e-12 and
                    abs(s['inclusion_probability'] - 60 / s['canonical_frame_N']) < 1e-12, 'Original weight changed')
        else:
            require(s['analysis_weight'] is None, 'Challenge incorrectly population weighted')
    for name, rr in {**refs, **methods}.items():
        for rid in sample:
            require(set(rr[rid].get('prediction', rr[rid])['labels']) == set(c.DIMS) and
                    all(c.binary(c.label(rr[rid], d)) or c.label(rr[rid], d) is None for d in c.DIMS), 'Label shape invalid')
    delivery = read(cfg['documented_six_context_changes'])
    changes = []
    for item in delivery['material_changes']:
        rid = item['original_id']; require(rid in probability, 'Documented context addition not in probability180')
        changes.append({'id': rid, 'current_text_changed': False, 'documented_change': item,
                        'legacy_v14_contexts': legacy[rid]['contexts'], 'current_source04_contexts': current[rid]['contexts'],
                        'legacy_context_sha256': canonical_sha(legacy[rid]['contexts']),
                        'current_context_sha256': canonical_sha(current[rid]['contexts'])})
    source_report = {'all_sample_text_equal': True, 'sample_n': 240, 'probability_n': 180, 'challenge_n': 60,
                     'source_gap_probability180_intersection': sorted(gap & probability),
                     'source_gap_challenge60_intersection': sorted(gap & challenge),
                     'text_equal_is_not_same_material': True, 'documented_six_shared_context_additions': changes,
                     'legacy_context_representation': 'v14 context dictionary', 'current_context_representation': 'source04 pure-source list',
                     'legacy_current_context_serialization_different_n': sum(legacy[r]['contexts'] != current[r]['contexts'] for r in sample),
                     'source_claim': 'Six documented additions are not a claim that all other old/current source scopes are identical',
                     'new_common_manual_human_compatibility': '尚待确认', 'new_independent_human_review_claimed': False}
    write('材料差异说明01.json', source_report)
    ctx = {'sample': sample}; records = []; matrices = []; factor_cache = {}
    comparisons = [('rules_A', methods['rules'], refs['A'], 'A'), ('rules_C', methods['rules'], refs['C'], 'C'),
                   ('LLM_A', methods['LLM'], refs['A'], 'A'), ('LLM_C', methods['LLM'], refs['C'], 'C'),
                   ('A_C', refs['A'], refs['C'], 'C')]
    for component in ('probability_canonical', 'enriched_challenge'):
        eligible = sorted(r for r, s in sample.items() if s['component'] == component)
        for group in ('ALL', *c.GROUPS):
            ids = [r for r in eligible if group == 'ALL' or sample[r]['group'] == group]
            if not ids:
                continue
            kind = 'eligible_design_weighted' if component == 'probability_canonical' else 'unweighted'
            w = c.weighting(ctx, ids, kind)
            for name, left, right, reference in comparisons:
                for dim in c.DIMS:
                    matrix, valid = c.cells(left, right, dim, ids); counts = w @ matrix; point = c.metrics(counts)[0]
                    names = c.METRIC_NAMES if name != 'A_C' else ('kappa', 'agreement', 'left_positive_rate', 'right_positive_rate')
                    record = {'component': component, 'group': group, 'weighting': kind, 'comparison': name,
                              'reference': reference, 'dimension': dim, 'unit_n': len(ids), 'paired_n': int(valid.sum()),
                              'pending_n': int((~valid).sum()), 'pending_ids': [r for r, ok in zip(ids, valid) if not ok],
                              'raw_cells': matrix.sum(axis=0).astype(int).tolist(), 'weighted_cells': counts.tolist(),
                              'cell_order': ['11', '10', '01', '00'], 'point': {n: c.safe(point[c.METRIC_NAMES.index(n)]) for n in names},
                              'interpretation': 'A/C symmetric agreement' if name == 'A_C' else 'diagnostic relative to existing post-reviewed reference',
                              'zero_denominator': 'NA', 'not_new_common_manual_validation': True}
                    records.append(record); matrices.append((ids, w, matrix, names))
    result = {'status': 'actual_diagnostic_points_completed', 'interpretation': NOTE, 'records': records,
              'source_gap_analysis_mask_not_needed_on_sample': True, 'labels_modified': False}
    write('实际点估计结果01.json', result); output_tables(records, '01'); markdown(records, source_report)
    summary = {r['comparison']: {} for r in records if r['component'] == 'probability_canonical' and r['group'] == 'ALL'}
    for r in records:
        if r['component'] == 'probability_canonical' and r['group'] == 'ALL':
            summary[r['comparison']][r['dimension']] = r['point']['kappa']
    print(json.dumps({'status': 'points_saved', 'probability180_weighted_ALL_kappa': summary}, ensure_ascii=False), flush=True)
    if args.bootstrap:
        for r, (ids, w, matrix, names) in zip(records, matrices):
            mechanism = 'department_unit_rescaled_SRSWOR' if r['component'] == 'probability_canonical' else 'department_unit_conditional_WR'
            key = (r['component'], r['group'], mechanism, tuple(ids))
            if key not in factor_cache:
                factor_cache[key] = c.replicate_factors(ctx, ids, r['component'], mechanism)
            boot = c.metrics((factor_cache[key] * w[None, :]) @ matrix)
            r['ci95_primary'] = {n: c.interval(boot[:, c.METRIC_NAMES.index(n)]) for n in names}
            r['bootstrap'] = {'repetitions': c.B, 'mechanism': mechanism, 'conditional_on_fixed_labels': True}
        write('实际点估计及5000次区间01.json', {**result, 'status': 'actual_diagnostic_points_and_intervals_completed',
              'records': records, 'bootstrap_factor_sets_n': len(factor_cache),
              'CI_scope': 'original probability design or conditional challenge resampling; not manual-compatibility or semantic-truth uncertainty'})
    tracked = [cfg['references'][n] for n in ('A', 'C')] + [entry['output'] for entry in cfg['methods'].values()]
    require(all(sha(Path(b['path'])) == b['sha256'] for b in tracked), 'Labels changed during comparison')
    files = {p.name: sha(p) for p in HERE.iterdir() if p.is_file() and p.name != 'completion01.json'}
    write('completion01.json', {'status': 'actual_diagnostic_comparison_completed', 'files_sha256': files,
          'labels_unchanged_sha_verified': True, 'bootstrap_executed': args.bootstrap, 'model_calls': 0,
          'new_human_review_claimed': False, 'interpretation': NOTE})
    print(json.dumps({'status': 'completed', 'bootstrap_executed': args.bootstrap, 'record_n': len(records)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
