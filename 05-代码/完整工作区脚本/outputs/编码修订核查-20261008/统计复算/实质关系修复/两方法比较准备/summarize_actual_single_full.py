#!/usr/bin/env python3
"""Render the frozen actual comparison; no coding or model calls.

The independently computed comparison exists before the root check is read.
Root's check is only used as a separately bound arithmetic cross-check.
"""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

W = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/编码修订核查-20261008')
P = W / '统计复算/实质关系修复/两方法比较准备'
O = P / '实际比较01'
D = ('S', 'E', 'Ec', 'I', 'F')
G = ('NMPA', 'NHSA', 'NHC', 'TOTAL')
names = {'NMPA': '药监', 'NHSA': '医保', 'NHC': '卫健', 'TOTAL': '总体'}
def read(p):
    return json.loads(p.read_text(encoding='utf-8'))
def ref(p):
    return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
def save(n, obj):
    p = O / n
    assert not p.exists(), f'preserve existing artifact: {p}'
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return p
def close(a, b):
    return a is None and b is None or a is not None and b is not None and abs(a - b) < 1e-10
def rank(groups):
    return ' > '.join(' = '.join(z) for z in groups)

x = read(O / '两方法描述与一致性.json')
qa = read(O / '输入绑定与来源校正核查.json')
assert qa['all_technical_binding_checks_pass'] is True
# A second arithmetic implementation reads the final bound raw outputs.
# It does not call comparison_core/helper/coder/model or copy primary values.
bundle_ref = qa['manifest']['files']['root_bundle']
bundle = read(Path(bundle_ref['path']))
assert ref(Path(bundle_ref['path']))['sha256'] == bundle_ref['sha256']
rawrefs = {k: bundle[k] for k in ('rule_output', 'llm_output', 'frame')}
for z in rawrefs.values():
    assert ref(Path(z['path']))['sha256'] == z['sha256']
def rows(z):
    return [json.loads(l) for l in Path(z['path']).read_text().splitlines()]
rule_raw, llm_raw, frame = rows(rawrefs['rule_output']), rows(rawrefs['llm_output']), rows(rawrefs['frame'])
assert len(rule_raw) == len(llm_raw) == len({z['id'] for z in rule_raw}) == len({z['id'] for z in llm_raw}) == 4480
rr, ll = {z['id']: z['result']['labels'] for z in rule_raw}, {z['id']: z['labels'] for z in llm_raw}
assert set(rr) == set(ll)
records = [{'id': z['id'], 'group': z['analysis_group'], 'rule': rr.get(z['id'], dict.fromkeys(D)), 'llm': ll.get(z['id'], dict.fromkeys(D))} for z in frame]
assert set(z['id'] for z in records) - set(rr) == {'RECODE25-00064'}
def ratio(a, b):
    return float(Fraction(a, b)) if b else None
independent = {'bundle_sha256': bundle_ref['sha256'], 'independent_formula_check': True, 'raw_refs': rawrefs, 'algorithm': 'separate Counter marginals and Fraction arithmetic; no primary count/q/kappa values read for calculation', 'groups': {}}
for g in G:
    chosen = [z for z in records if g == 'TOTAL' or z['group'] == g]
    common = [z for z in chosen if all(z[m][d] is not None for m in ('rule', 'llm') for d in D)]
    qg = {'executed_n': len(common), 'source_unknown_ids': [z['id'] for z in chosen if z['id'] not in rr], 'methods': {}, 'method_agreement': {}}
    for m in ('rule', 'llm'):
        complete = [z for z in chosen if all(z[m][d] is not None for d in D)]
        c = {d: sum(z[m][d] == 1 for z in complete) for d in D}
        a = {d: sum(z[m][d] == 1 for z in chosen) for d in D}
        u = {d: sum(z[m][d] is None for z in chosen) for d in D}
        B, A = sum(c.values()), sum(a.values())
        qg['methods'][m] = {'positive_counts': c, 'total_dimension_mentions': B, 'q_percent': {d: 100 * ratio(c[d], B) for d in D}, 'q_percent_unknown_bounds': {d: [100 * ratio(a[d], A + sum(u[k] for k in D if k != d)), 100 * ratio(a[d] + u[d], A + u[d])] for d in D}}
    for d in D:
        paired = [z for z in chosen if z['rule'][d] is not None and z['llm'][d] is not None]
        C = Counter((z['rule'][d], z['llm'][d]) for z in paired)
        n = len(paired);Po = Fraction(C[0, 0] + C[1, 1], n)
        r0, r1 = C[0, 0] + C[0, 1], C[1, 0] + C[1, 1]
        l0, l1 = C[0, 0] + C[1, 0], C[0, 1] + C[1, 1]
        Pe = Fraction(r0 * l0 + r1 * l1, n * n)
        kappa = None if Pe == 1 else float((Po - Pe) / (1 - Pe))
        qg['method_agreement'][d] = {'four_cells_rule_llm': {str(r) + str(l): C[r, l] for r, l in ((0, 0), (0, 1), (1, 0), (1, 1))}, 'kappa': kappa, 'agreement': float(Po), 'different_n': C[0, 1] + C[1, 0]}
    independent['groups']['ALL' if g == 'TOTAL' else g] = qg
rp = save('独立算术复算.json', independent)
r = read(rp)
assert r['bundle_sha256'] == ref(W / '统计复算/实质关系修复/当前同材料结果/同材料结果绑定.json')['sha256']
execution = read(Path(bundle['rule_execution']['path']))
assert ref(Path(bundle['rule_execution']['path']))['sha256'] == bundle['rule_execution']['sha256']
assert execution['n_undetermined'] == sum(any(z['rule'][d] is None for d in D) for z in records if z['id'] in rr)
checks = []
summary = {
    'status': 'frozen_descriptive_comparison_not_final_results_or_gold_validation',
    'primary_comparison_preceded_independent_raw_output_recalculation': True,
    'actual_rule_execution_ref': bundle['rule_execution'],
    'actual_rule_executed_n_undetermined': execution['n_undetermined'],
    'actual_comparison_refs': [ref(O / '两方法描述与一致性.json'), ref(O / '输入绑定与来源校正核查.json')],
    'adapter_records_are_explicitly_derived_not_new_actual_runs': True,
    'lineage': {'llm': x['llm_lineage_kind'], 'rule': x['rule_lineage_kind']},
    'denominator_notes': x['denominator_notes'],
    'groups': {}, 'unknown_unit_ledger': x['unknown_unit_ledger'],
    'no_coder_or_model_called_in_this_comparison': True,
    'no_semantic_validity_or_human_validation_certified': True,
}
md = [
    '# 同材料实际比较（描述性封存）', '',
    '本比较使用已封存的同材料4481目标框。LLM来源为“全量实际执行＋1条来源校正实际执行”；规则来源为同一次完整4480条实际执行。技术绑定通过，规则全部行来自该完整执行输出；LLM与NF2同材料结果逐字节一致，其历史运行链中的其余4479行原输出字节保持。兼容接口文件明确标为derived，不是新执行证明。', '',
    'S/E/Ec/I/F依次为安全、有效、经济、创新、公平。下表为共同全五维可判定单位上的阳性句次（q%）。q的分母是本方法五维阳性句次之和，允许一条跨维计数，不是正文单元数；单位阳性率p及逐维覆盖另存JSON。', '',
    '| 部门 | 方法 | 判定单位/目标 | 阳性句次总和B | S | E | Ec | I | F | 排序 |',
    '|---|---|---:|---:|---:|---:|---:|---:|---:|---|',
]
agreement_rows = []
bounds_rows = []
diff_rows = []
for g in G:
    v = x['analyses'][g]
    zroot = r['groups']['ALL' if g == 'TOTAL' else g]
    checks.append({'field': f'{g}.n', 'pass': zroot['executed_n'] == v['common_all_five_determined_comparison']['unit_n']})
    sv = {'target_unit_n': v['target_unit_n'], 'common_all_five_determined_n': v['common_all_five_determined_comparison']['unit_n'], 'methods': {}, 'agreement': v['binary_agreement_on_dimensionwise_common_determined'], 'q_differences': v['q_differences']}
    for m in ('rule', 'llm'):
        a = v['method_descriptive'][m]
        dims = a['dimensions']
        sm = {'fully_determined_unit_n': a['fully_determined_unit_n'], 'any_unknown_unit_n': a['any_unknown_unit_n'], 'unknown_label_cell_n': a['unknown_label_cell_n'], 'q_denominator_positive_occurrences': a['conditional_q_denominator_positive_label_occurrences'], 'ranking_tie_groups': v['own_fully_determined_population_ranking_tie_groups'][m], 'dimensions': {}}
        cells = []
        for d in D:
            b = dims[d]
            sm['dimensions'][d] = {'positive_n': b['fully_determined_units_positive_n'], 'dimension_known_n': b['dimension_determined_unit_n'], 'dimension_unknown_n': b['dimension_unknown_unit_n'], 'q_percent': b['q_conditional_on_fully_determined_units']['percent'], 'p_percent_conditional_known': b['unit_positive_rate_conditional_on_this_dimension_determined']['percent'], 'p_full_target_bounds_percent': [b['full_target_unit_positive_rate_bounds'][k]['percent'] for k in ('lower', 'upper')], 'q_full_target_bounds_percent': [b['full_target_relative_attention_q_bounds'][k]['percent'] for k in ('lower', 'upper')]}
            s = sm['dimensions'][d]
            rr = zroot['methods'][m]
            checks += [
                {'field': f'{g}.{m}.{d}.count', 'pass': s['positive_n'] == rr['positive_counts'][d]},
                {'field': f'{g}.{m}.{d}.q', 'pass': close(s['q_percent'], rr['q_percent'][d])},
                {'field': f'{g}.{m}.{d}.q_bounds', 'pass': all(close(t, u) for t, u in zip(s['q_full_target_bounds_percent'], rr['q_percent_unknown_bounds'][d]))},
            ]
            cells.append(f"{s['positive_n']} ({s['q_percent']:.2f})")
        sv['methods'][m] = sm
        md.append(f"| {names[g]} | {'规则' if m == 'rule' else 'LLM'} | {sm['fully_determined_unit_n']}/{v['target_unit_n']} | {sm['q_denominator_positive_occurrences']} | " + ' | '.join(cells) + ' | ' + rank(sm['ranking_tie_groups']) + ' |')
        if sm['any_unknown_unit_n']:
            vals = [f"{sm['dimensions'][d]['q_full_target_bounds_percent'][0]:.3f}–{sm['dimensions'][d]['q_full_target_bounds_percent'][1]:.3f}" for d in D]
            bounds_rows.append('| ' + names[g] + ' | ' + m + ' | ' + ' | '.join(vals) + ' |')
    for d in D:
        a = sv['agreement'][d]
        b = zroot['method_agreement'][d]
        checks += [
            {'field': f'{g}.{d}.four_cells', 'pass': list(a['cells'].values()) == [b['four_cells_rule_llm'][k] for k in ('00', '01', '10', '11')]},
            {'field': f'{g}.{d}.kappa', 'pass': close(a['cohen_kappa'], b['kappa'])},
            {'field': f'{g}.{d}.agreement', 'pass': close(a['agreement'], b['agreement'])},
            {'field': f'{g}.{d}.disagreements', 'pass': a['disagreement_n'] == b['different_n']},
        ]
    kappas = [f"{sv['agreement'][d]['cohen_kappa']:.4f} ({100 * sv['agreement'][d]['agreement']:.2f}%)" for d in D]
    agreement_rows.append('| ' + names[g] + ' | ' + ' | '.join(kappas) + ' |')
    diff_rows.append('| ' + names[g] + ' | ' + ' | '.join(f"{v['q_differences'][d]['common_all_five_determined_population_q_llm_minus_rule_percentage_points']:+.3f}" for d in D) + ' |')
    summary['groups'][g] = sv

assert all(c['pass'] for c in checks), [c for c in checks if not c['pass']]
save('部门结果简表.json', summary)
save('数据汇总独立交叉核对.json', {'all_checks_pass': True, 'checks_n': len(checks), 'checks': checks, 'source_refs': [ref(O / '两方法描述与一致性.json'), ref(rp)], 'tolerance_for_float': 1e-10, 'no_expected_values_hardcoded': True, 'semantic_validity_not_tested': True})
md += ['', '两方法排序在每个部门及总体均一致；占比差异仍需保留。', '', '| 部门 | Δq S | Δq E | Δq Ec | Δq I | Δq F |', '|---|---:|---:|---:|---:|---:|'] + diff_rows
md += ['', 'Δq为LLM减规则的百分点；两方法均在相同单位集合比较。', '', '| 部门 | S κ（一致率） | E κ（一致率） | Ec κ（一致率） | I κ（一致率） | F κ（一致率） |', '|---|---:|---:|---:|---:|---:|'] + agreement_rows
md += ['', '总体分歧句次S/E/Ec/I/F为' + '/'.join(str(x['difference_export_counts'][d]) for d in D) + '。每维分歧文件保留ID、文本、双方完整理由与证据；κ及一致率只衡量两方法一致程度，双方均不是标准答案，没有据此计算准确率或gold P/R。', '', '00064因所援指导原则的当时适用版本未核定保留五维未知，两方法均未将其填0。实际规则执行4480条中的unknown为0；完整目标框按真实null保留00064这1条来源未知。整数输出不代表内容效度已经验证。全框q的逻辑边界如下（不是置信区间）：', '', '| 范围 | 方法 | S q%界 | E q%界 | Ec q%界 | I q%界 | F q%界 |', '|---|---|---:|---:|---:|---:|---:|'] + bounds_rows
md += ['', '医保及卫健无unknown，界等于表中q。全框单位阳性率p使用目标总单位数，q界允许未知维度独立取0/1；部门、总体全量边界和保守Δq界均保留在JSON。这里仅封存当前bundle描述，后续实现修复不覆盖本次结果。', '', f'主比较先完成，随后另用原始已绑定输出和独立Counter/Fraction公式复算，共{len(checks)}项计数、四格、q及边界、一致率、κ检查均一致（浮点容差1e-10）。技术QA只证明文件、来源、运行链和字节绑定，不证明语义有效性或真人效度。', '', '来源绑定和完整SHA见输入核查JSON与交付SHA；本轮没有调用编码器或模型，也没有重编码或修改原运行文件。', '']
mp = O / '部门结果与分母说明.md'
assert not mp.exists()
mp.write_text('\n'.join(md), encoding='utf-8')
targets = [P / 'compare_single_full.py', P / 'comparison_core.py', P / 'build_single_full_adapter.py', Path(__file__), P / 'single_full_adapter_manifest.json'] + sorted(p for p in O.iterdir() if p.is_file())
save('实际比较交付SHA.json', {'all_technical_binding_checks_pass': True, 'arithmetic_cross_check_pass': True, 'not_final_publication_or_human_validation': True, 'files': [ref(p) for p in targets]})
print(json.dumps({'status': 'complete', 'checks_n': len(checks), 'summary': ref(O / '部门结果简表.json'), 'report': ref(mp), 'comparison': ref(O / '两方法描述与一致性.json'), 'qa': ref(O / '输入绑定与来源校正核查.json'), 'freeze': ref(O / '实际比较交付SHA.json')}, ensure_ascii=False))
