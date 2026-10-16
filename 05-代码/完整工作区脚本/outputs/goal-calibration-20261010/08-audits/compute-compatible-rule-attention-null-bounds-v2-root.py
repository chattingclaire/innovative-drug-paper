"""Diagnose unresolved rule labels' possible effect on department/year attention.

Conditional bounds on a coded corpus, not confidence intervals or validation.
No source text is opened and no missing label is imputed.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, json

R = Path(__file__).resolve().parents[1]
YEAR = R / '07-statistics/annual-year-input-binding-sol'
DIMS = ('S', 'E', 'Ec', 'I', 'F')


def bind(p):
    p = Path(p).resolve(); b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def load(p):
    return json.loads(Path(p).read_bytes())


def exact(b):
    a = bind(b['path'])
    assert all(a[k] == b[k] for k in ('path', 'bytes', 'sha256'))


def save(p, x):
    with Path(p).open('x', encoding='utf8') as f:
        json.dump(x, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')


def div(a, b):
    return None if b == 0 else a / b


def derive(rows, group_key):
    n = len(rows)
    p = {d: sum(x['labels'][d] == 1 for x in rows) for d in DIMS}
    u = {d: sum(x['labels'][d] is None for x in rows) for d in DIMS}
    z = {d: n - p[d] - u[d] for d in DIMS}
    total_p = sum(p.values()); total_u = sum(u.values())
    # Lower share: own unknowns=0, all other dimensions' unknowns=1.
    # Upper share: own unknowns=1, all other dimensions' unknowns=0.
    dimensions = {d: {'positive_N': p[d], 'negative_N': z[d], 'unresolved_N': u[d],
        'positive_assignment_share_among_observed': div(p[d], total_p),
        'positive_assignment_share_lower_bound': div(p[d], total_p + total_u - u[d]),
        'positive_assignment_share_upper_bound': div(p[d] + u[d], total_p + u[d]),
        'clause_prevalence_lower_bound': div(p[d], n),
        'clause_prevalence_upper_bound': div(p[d] + u[d], n)} for d in DIMS}
    stable = []
    for a in DIMS:
        for b in DIMS:
            if a != b and p[a] > p[b] + u[b]:
                stable.append({'higher_dimension': a, 'lower_dimension': b,
                               'minimum_higher_positive_N': p[a],
                               'maximum_lower_positive_N': p[b] + u[b]})
    return {'group': group_key, 'clause_N': n, 'observed_positive_assignment_N': total_p,
            'unresolved_assignment_N': total_u, 'dimensions': dimensions,
            'strict_within_group_rankings_immune_to_unresolved_labels': stable,
            'conditional_on_correct_observed_machine_labels': True}


def verify_composite_seal(path, seen=None):
    seen = set() if seen is None else seen
    path = Path(path).resolve()
    if path in seen: return
    seen.add(path)
    seal = load(path)
    for key in ('files', 'output_files', 'implementation_files', 'material_bindings', 'control_inputs'):
        for item in seal.get(key, []): exact(item)
    for ancestor in seal.get('ancestor_seals', []):
        exact(ancestor); verify_composite_seal(ancestor['path'], seen)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rule-composite', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    RULE = Path(args.rule_composite).resolve()
    OUT = Path(args.output).resolve()
    assert not OUT.exists()
    verify_composite_seal(RULE / 'seal.json')
    year_seal = load(YEAR / 'seal.json')
    assert Path(year_seal['root']).resolve() == YEAR.resolve()
    for name, b in year_seal['outputs'].items():
        exact(dict(b, path=str((YEAR / name).resolve())))
    status = load(RULE / 'composite-status.json')
    assert (status['status'].startswith('complete_') and status['status'].endswith('_compatible_composite_with_explicit_execution_origins')) or status['status']=='complete_compatible_rule_composite_with_explicit_execution_origins'
    assert status['actual_record_N'] == 4481 and status['actual_dimension_N'] == 22405
    assert status['technical_failure_dimension_N'] == 0
    predictions = {}
    for line in (RULE / 'predictions.jsonl').read_bytes().splitlines():
        x = json.loads(line); assert x['id'] not in predictions
        predictions[x['id']] = x
    metadata = [json.loads(line) for line in (YEAR / 'full4481-year-map.jsonl').read_bytes().splitlines()]
    assert len(metadata) == len(predictions) == 4481
    assert [x['unit_id'] for x in metadata] == list(predictions)
    groups = collections.defaultdict(list)
    entries = set()
    for m in metadata:
        assert m['unit_id'] == m['source_id'] and m['department'] in ('NMPA', 'NHSA', 'NHC')
        assert type(m['policy_year']) is int and type(m['publication_year']) is int
        assert m['component_id'] is None
        entries.add(m['source_entry_id'])
        x = predictions[m['unit_id']]
        groups[('department', m['department'])].append(x)
        groups[('department_year', m['department'], m['policy_year'])].append(x)
        groups[('corpus_year', m['policy_year'])].append(x)
    assert len(entries) == 51
    results = [derive(rows, list(k)) for k, rows in sorted(groups.items())]
    overall = derive(list(predictions.values()), ['entire_corpus'])
    assert overall['unresolved_assignment_N'] == status['lawful_null_N']
    assert sum(overall['dimensions'][d]['positive_N'] + overall['dimensions'][d]['negative_N'] + overall['dimensions'][d]['unresolved_N'] for d in DIMS) == 22405
    report = {'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'identity': 'conditional diagnostic bounds for unresolved rule slots; not final empirical findings',
        'metadata_source_entry_N': len(entries), 'source_entries_NOT_claimed_independent_components': True,
        'year_basis': 'previously sealed issue-date-first then original-publication-date fallback',
        'component_date_analysis_executed': False, 'confidence_intervals_computed': False,
        'no_source_text_or_new_human_answers_read': True,
        'nulls_imputed_as_zero_or_one': False,
        'bound_assumption': 'Observed binary rule decisions held fixed; unresolved slots may independently be 0 or 1.',
        'share_formula': 'positive_d / sum(all dimensions positive); multi-label assignments are the denominator.',
        'prevalence_formula': 'positive_d / all clauses in the group; dimension prevalences need not sum to 1.',
        'not_a_bound_on_errors_in_observed_binary_labels': True,
        'formal_validation_complete': False, 'paper_writing_gate_open': False,
        'overall': overall, 'groups': results,
        'inputs': [bind(RULE / 'seal.json'), bind(RULE / 'composite-status.json'),
                   bind(RULE / 'predictions.jsonl'), bind(YEAR / 'seal.json'),
                   bind(YEAR / 'full4481-year-map.jsonl')], 'calculator': bind(__file__)}
    OUT.mkdir()
    save(OUT / 'conditional-bounds.json', report)
    lines = ['待定项对部门和年度注意力排序的影响诊断', '',
        f"本表只检查{overall['unresolved_assignment_N']}个规则待定维度项的潜在影响，尚未验证规则所有0/1的语义正确性，因此不能当作最终论文结论或置信区间。未将待定项补成0。", '',
        '占比的分母是同组五维阳性标签数，多标签可重复计入；范围分别令本维与其他维的待定项取最不利组合。年份沿用已封存的成文日期优先、公开日期回退方案，未使用组件或月日分析。', '',
        '|部门|条款数|维度|已判1|待定|观察标签占比|待定项条件范围|',
        '|---|---:|---|---:|---:|---:|---:|']
    for group in results:
        if group['group'][0] != 'department': continue
        for d, v in group['dimensions'].items():
            def fmt(x): return 'NA' if x is None else f'{x:.1%}'
            lines.append(f"|{group['group'][1]}|{group['clause_N']}|{d}|{v['positive_N']}|{v['unresolved_N']}|{fmt(v['positive_assignment_share_among_observed'])}|{fmt(v['positive_assignment_share_lower_bound'])}–{fmt(v['positive_assignment_share_upper_bound'])}|")
    lines += ['', '完整部门×年度及全语料年度分组、分母、待定项与不受这些待定项影响的严格组内排序见conditional-bounds.json。该范围不覆盖机器已判0/1的误判，也不替代独立人工验证、抽样区间或其他口径稳健性。', '']
    (OUT / '部门年度待定项影响.md').write_text('\n'.join(lines))
    save(OUT / 'seal.json', {'files': [bind(p) for p in sorted(OUT.iterdir()) if p.is_file()],
                            'self_excluded': True, 'formal_validation_complete': False})
    print(json.dumps({'group_N': len(results), 'clause_N': 4481, 'positive_assignment_N': overall['observed_positive_assignment_N'],
                      'unresolved_N': overall['unresolved_assignment_N'], 'annual_results_are_conditional_diagnostics': True}))


if __name__ == '__main__':
    main()
