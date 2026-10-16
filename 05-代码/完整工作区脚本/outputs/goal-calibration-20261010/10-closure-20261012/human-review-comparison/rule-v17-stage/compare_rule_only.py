"""Actual fixed-200 rule-only development comparison; no model execution.

Uses the accepted human projection and frozen exact arithmetic. This separate
stage does not change or relax the strict paired-v17 comparison entry.
"""
import ast
import json
import runpy
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent
ROOT = OLD.parent.parent
ENTRY = OLD / 'v17-preparation/compare.py'
ENTRY_SHA = '6f571dc244d2f94293febe7122f5e4679c0b089a2972e5aed33012b4297d48fe'


def main():
    import hashlib
    if hashlib.sha256(ENTRY.read_bytes()).hexdigest() != ENTRY_SHA:
        raise ValueError('Frozen paired entry changed')
    lib = runpy.run_path(str(ENTRY))
    require, binding, exact = lib['require'], lib['binding'], lib['exact']
    expected, read, dims = lib['expected'], lib['read'], lib['DIMS']
    out = HERE / 'results'
    require(not out.exists(), 'Never overwrite a comparison')
    rule_dir = lib['RULE_DEFAULT']
    status, files, rule_seal = lib['seal'](rule_dir, 'composite-status.json')
    common = expected(lib['V17'] / 'common-frame-bundles-v17.jsonl', lib['V17_SHA'])
    packets = expected(lib['V17'] / 'packet-bindings-v17.json', lib['PACKET_SHA'])
    require(status['status'] == 'validated_complete_full4481_v17_not_adopted'
            and status['candidate_algorithm_version'] == 'joint-v15b-complete-repair-root'
            and status['all4481_actually_inferred_under_candidate'] is True
            and status['inherited_compatible_parent_record_N'] == 0,
            'Not the strict complete candidate rule execution')
    require(status['actual_record_N'] == 4481 and status['actual_dimension_N'] == 22405
            and status['unresolved_technical_dimension_N'] == 0,
            'Incomplete machine frame')
    require(status['source_common_v17'] == common
            and set(status['material_changed_record_ids']) == lib['CHANGED'],
            'Rule material binding differs')
    exact(status['actual_run_seal']); exact(status['current_scope'])
    pred_path = rule_dir / 'predictions.jsonl'
    require(str(pred_path) in files, 'Predictions missing from completed seal')
    machine = [json.loads(x) for x in pred_path.read_text().splitlines()]
    ids = [x['source_id'] for x in read(packets['path'])]
    require(len(ids) == len(set(ids)) == 4481
            and [x['id'] for x in machine] == ids, 'Rule frame not complete and unique')
    for row in machine:
        require(set(row['labels']) == set(dims), 'Missing dimension')
        for dim, value in row['labels'].items():
            require(value is None or type(value) is int and value in (0, 1), 'Invalid label')
            require(value == row['decisions'][dim]['value'], 'Decision/label mismatch')
    machine = {x['id']: x for x in machine}
    inputs = {
        'entry': binding(Path(__file__)), 'frozen_paired_entry': binding(ENTRY),
        'rule_seal': rule_seal, 'rule_status': binding(rule_dir / 'composite-status.json'),
        'rule_predictions': files[str(pred_path)], 'common_v17': common, 'packets_v17': packets,
        'accepted_original_comparison': expected(OLD / 'results/comparison.json', lib['OLD_SUMMARY_SHA']),
        'accepted_original_join': expected(OLD / 'results/joined-dimension-records.jsonl', lib['OLD_JOIN_SHA'])}
    prior = read(inputs['accepted_original_comparison']['path'])
    for key in ('human_original', 'math_core', 'draw', 'issued_template'):
        inputs[key] = prior['source_bindings'][key]; exact(inputs[key])
    tree = ast.parse(Path(inputs['math_core']['path']).read_text())
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef)
           and n.name in ('_ratio', 'exact_metrics')]
    require([n.name for n in fns] == ['_ratio', 'exact_metrics'], 'Frozen arithmetic changed')
    ns = {'Fraction': Fraction}
    exec(compile(ast.Module(body=fns, type_ignores=[]), inputs['math_core']['path'], 'exec'), ns)
    records = [json.loads(x) for x in Path(inputs['accepted_original_join']['path']).read_text().splitlines()]
    require(len(records) == 1000 and len({(r['source_id'], r['dimension']) for r in records}) == 1000
            and len({r['source_id'] for r in records}) == 200, 'Accepted fixed200 changed')
    require(lib['CHANGED'] <= {r['source_id'] for r in records}, 'Material-change rows missing')
    for r in records:
        rid = r['source_id']
        r['v11_frozen_domain_for_history_only'] = r.pop('current_domain')
        r['rule_v11'] = r.pop('rule'); r.pop('LLM')
        r['rule_v15b_v17'] = machine[rid]['labels'][r['dimension']]
        r['material_supplemented_in_v17'] = rid in lib['CHANGED']
        r['v17_supplement_human_reread_verified'] = False if rid in lib['CHANGED'] else None
        r['reference_set_used_for_development'] = True
    numeric = []
    groups = [('all200', records),
              ('historical_remaining120', [r for r in records if r['historical_domain'] == 'remaining']),
              ('historical_exposed80', [r for r in records if r['historical_domain'] == 'exposed']),
              ('unchanged_material198', [r for r in records if not r['material_supplemented_in_v17']])]
    for group, group_rows in groups:
        for method in ('rule_v11', 'rule_v15b_v17'):
            for dim in dims:
                rows = [r for r in group_rows if r['dimension'] == dim]
                cells = [0, 0, 0, 0]; weighted = [Fraction(0) for _ in range(4)]; states = Counter()
                for r in rows:
                    h, m = r['human_reviewed_value'], r[method]
                    states[f'{"pending" if h is None else h}|{"null" if m is None else m}'] += 1
                    if h is None or m is None:
                        continue
                    i = {(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[(m, h)]
                    cells[i] += 1; weighted[i] += Fraction(r['original_weight_exact'])
                metric = lambda c: {k: None if v is None else float(v) for k, v in ns['exact_metrics'](c).items()}
                x = {'group': group, 'method': method, 'dimension': dim, 'planned_N': len(rows),
                     'common_binary_N': sum(cells), 'excluded_N': len(rows) - sum(cells),
                     'human_pending_N': sum(r['human_reviewed_value'] is None for r in rows),
                     'machine_lawful_null_N': sum(r[method] is None for r in rows),
                     'machine_technical_failure_N': 0, 'joint_states_human_machine': dict(states),
                     'cell_order': ['TP', 'FP', 'FN', 'TN'], 'raw_cells': cells,
                     'original_weighted_cells_exact': [str(v) for v in weighted],
                     'raw_metrics': metric(cells), 'original_weighted_metrics': metric(weighted),
                     'formal_acceptance': False, 'independent_accuracy_CI': None}
                numeric.append(x)
                if method == 'rule_v11' and group != 'unchanged_material198':
                    previous = next(y for y in prior['numeric_comparisons']
                                    if y['group'] == group and y['method'] == 'rule' and y['dimension'] == dim)
                    require({k: v for k, v in x.items() if k != 'method'}
                            == {k: v for k, v in previous.items() if k != 'method'},
                            'Old accepted arithmetic no longer reproduced')
    result = {'analysis_type': 'rule_only_fixed200_post_development_descriptive_comparison',
              'created_at_utc': datetime.now(timezone.utc).isoformat(), 'records_N': 200,
              'dimension_slots_N': 1000, 'numeric_comparisons': numeric,
              'label_changed_record_N': len({r['source_id'] for r in records if r['rule_v11'] != r['rule_v15b_v17']}),
              'label_changed_dimension_N': sum(r['rule_v11'] != r['rule_v15b_v17'] for r in records),
              'supplemented_material_rows': [r for r in records if r['material_supplemented_in_v17']],
              'pending': [r for r in records if r['human_reviewed_value'] is None],
              'source_bindings': inputs,
              'scope': {**prior['scope'], 'feedback_used_for_model_revision': True,
                        'new_draw_or_model_changes': False, 'LLM_evaluated_in_this_stage': False,
                        'v17_supplement_human_reread_verified': False,
                        'material_comparability': 'All200 retained; two supplemented records separately identified; unchanged198 sensitivity retained.',
                        'paired_v17_comparison_still_pending': True}}
    out.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        with (out / name).open('x') as f:
            json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
    save('comparison.json', result)
    with (out / 'joined-dimension-records.jsonl').open('x') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n')
    lines = ['# 修正版规则与现有真人复核的对照', '',
             '使用严格接收的4481条新规则结果，连接原200条真人复核记录。该复核反馈已用于规则修订，本表是开发后描述性对照；不计为独立准确性验收。此次不计算LLM，新版两机配对统计仍待24条LLM结果。', '',
             '200条全部保留；02588、04598的机器材料后来有补充，未据此推断真人已重读，另列198条未变材料的敏感性结果。人工待定与规则NULL按并集排除，不填0。', '',
             f"相对旧规则，样本中{result['label_changed_record_N']}条、{result['label_changed_dimension_N']}个维度标签改变。旧版15项分组维度结果均与已接收统计完全复现。", '']
    fmt = lambda v: 'NA' if v is None else f'{v:.3f}'
    for group, title in [('all200', '全部200条原始指标'), ('unchanged_material198', '198条未变材料原始指标')]:
        lines += ['## ' + title, '', '| 规则 | 维度 | 可比/计划 | 人工待定 | 规则NULL | TP/FP/FN/TN | κ | P | R | F1 |',
                  '|---|---|---:|---:|---:|---|---:|---:|---:|---:|']
        for x in numeric:
            if x['group'] != group:
                continue
            lines.append('| ' + ' | '.join(['旧版' if x['method'] == 'rule_v11' else '修正版', x['dimension'],
                         f"{x['common_binary_N']}/{x['planned_N']}", str(x['human_pending_N']), str(x['machine_lawful_null_N']),
                         '/'.join(map(str, x['raw_cells'])), *[fmt(x['raw_metrics'][k]) for k in ('kappa', 'Precision', 'Recall', 'F1')]]) + ' |')
        lines.append('')
    lines += ['## 原权重诊断（全部200条）', '',
              '原抽样权重保持不变，仅作描述性重加权，不解释为修正版总体独立准确率。', '',
              '| 规则 | 维度 | κ | P | R | F1 |', '|---|---|---:|---:|---:|---:|']
    for x in numeric:
        if x['group'] == 'all200':
            lines.append('| ' + ' | '.join(['旧版' if x['method'] == 'rule_v11' else '修正版', x['dimension'],
                         *[fmt(x['original_weighted_metrics'][k]) for k in ('kappa', 'Precision', 'Recall', 'F1')]]) + ' |')
    lines += ['', '历史120/80分组、精确加权四格表和全部逐项记录见[完整结果](comparison.json)。原人审表、旧结果及新版两机接收入口均未修改。', '']
    with (out / '规则复核对照.md').open('x') as f:
        f.write('\n'.join(lines))
    save('seal.json', {'analysis_type': result['analysis_type'], 'formal_acceptance': False,
                       'files': [binding(out / name) for name in ('comparison.json', 'joined-dimension-records.jsonl', '规则复核对照.md')],
                       'entry': inputs['entry'], 'self_excluded': True})
    print(json.dumps({'status': 'rule_only_descriptive_comparison_complete', 'output': str(out),
                      'formal_acceptance': False, 'model_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
