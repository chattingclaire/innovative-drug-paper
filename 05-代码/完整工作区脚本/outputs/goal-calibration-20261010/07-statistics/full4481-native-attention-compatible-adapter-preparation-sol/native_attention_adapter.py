#!/usr/bin/env python3
"""Complete native-v16 admission and reuse of the immutable attention entry."""
from pathlib import Path
import argparse
import importlib.util
import hashlib
import json
import math
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / '07-statistics/full4481-attention-robustness-preparation-sol'
DELTA = ('RECODE25-01402', 'RECODE25-01403', 'RECODE25-01404')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def core():
    # Import performs no aggregation: the original __main__ entry is not called.
    path = BASE / 'full4481_attention_robustness.py'
    require(hashlib.sha256(path.read_bytes()).hexdigest() == '9d7c3d98454faa41a40157aafb966d110dda40784e122651c0c8ac708b02d8dc',
            'Frozen attention code changed; refuse import')
    spec = importlib.util.spec_from_file_location('sealed_attention_core', path)
    module = importlib.util.module_from_spec(spec)
    prior = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = prior
    return module


def exact(m, b):
    actual = m.bind(b['path'])
    require(all(actual[k] == b[k] for k in actual), 'Changed binding: ' + b['path'])
    return actual


def sealed(m, directory, required=()):
    directory = Path(directory).resolve()
    seal = m.load(directory / 'seal.json')
    bound = {}
    for item in seal['files']:
        b = exact(m, item)
        bound[b['path']] = b
    for name in required:
        require(str(directory / name) in bound, 'Unsealed required file: ' + name)
    return m.bind(directory / 'seal.json')


def full_coverage(m, path):
    c = m.load(path)
    expected = {'full_corpus_complete': True, 'selected_record_N': 4481,
                'selected_batch_N': 504, 'missing_record_N': 0,
                'missing_label_N': 0, 'pointer_quote_issue_N': 0}
    require(c.get('full_corpus_complete') is True and all(c.get(k) == v for k, v in expected.items()),
            'Incomplete native corpus refused; selected_record_N=' + str(c.get('selected_record_N')))
    require(c.get('thin35_included') is False and c.get('selection_by_semantic_metric') is False,
            'Unsupported selected corpus origin')
    return c


def base_bindings(m):
    sealed(m, BASE)
    b = m.load(BASE / 'input-bindings.json')
    for item in [b['entry'], *b['inputs'].values(), *b['prepared'].values()]:
        exact(m, item)
    return b


def admission(m, parent, compatible, selection):
    parent, compatible = Path(parent).resolve(), Path(compatible).resolve()
    ps = sealed(m, parent, ('coverage.json', 'selected-records.jsonl', 'selected-whole-batch-bindings.json'))
    pc = full_coverage(m, parent / 'coverage.json')  # reject partial before looking at labels
    ms = sealed(m, compatible, ('coverage.json', 'selected-records.jsonl', 'selected-whole-batch-bindings.json', 'status.json'))
    mc = full_coverage(m, compatible / 'coverage.json')
    status = m.load(compatible / 'status.json')
    required_status = {'status': 'complete_native_full4481_v16_three_member_compatible_composite_with_explicit_execution_origins',
        'actual_record_N': 4481, 'actual_dimension_N': 22405, 'parent_raw_line_preserved_N': 4478,
        'actual_new_inference_record_N': 3, 'unresolved_technical_dimension_N': 0}
    require(status.get('actual_merge_performed') is True and status.get('not_all4481_reencoded_in_v16') is True
            and all(status.get(k) == v for k, v in required_status.items()), 'Incomplete actual material merge refused')
    require(exact(m, status['parent_collector_seal']) == ps and exact(m, status['new_whole_selection']) == m.bind(selection),
            'Actual merge parent/selection mismatch')
    sel = m.load(selection)
    require(sel['artifact_type'] == 'earliest_valid_new_v16_material_whole_batch'
            and sel['batch_id'] == 'batch-0216' and tuple(sel['source_ids']) == DELTA
            and sel['semantic_scores_not_selection_criteria'] is True, 'Invalid actual v16 selection')
    for k in ('assignment', 'first', 'reception', 'actor_seal'):
        exact(m, sel[k])
    receipt = m.load(sel['reception']['path'])
    require(receipt['state'] == 'technical_valid_whole_batch'
            and receipt['first'] == sel['first'] and receipt['actor_seal'] == sel['actor_seal'], 'Invalid v16 reception')
    validation = receipt['validation']
    require(validation['new_v16_material_delta'] is True
            and validation['observable_readback']['observable_complete_text_presentations'] is True,
            'Missing actual material reading certification')
    actor = m.load(sel['actor_seal']['path'])
    require(actor['template_only'] is False and actor['actual_completion_claimed'] is True
            and actor['first_binding'] == sel['first'] and actor['actual_input_bindings'], 'Incomplete actor seal')
    process_path = Path(sel['first']['path']).parent / 'process-completion.json'
    process = m.load(process_path)
    require(process['actual_process_terminal'] is True and process['returncode'] == 0
            and process['timed_out'] is False, 'Nonterminal actual material attempt')
    for k in ('events', 'stderr'):
        exact(m, process[k])  # hash only; no event/prompt/source semantics opened
    first = m.load(sel['first']['path'])
    require(first['batch_id'] == 'batch-0216' and tuple(r['source_id'] for r in first['records']) == DELTA,
            'New result is not the complete original batch')
    new = {r['source_id']: r for r in first['records']}
    units = list(m.iter_jsonl(BASE / 'unit-metadata.jsonl'))
    manifest = m.load(ROOT / '01-review/source-interface-v16-article6-addendum-sol/packet-bindings-v16.json')
    require([r['source_id'] for r in manifest] == [r['unit_id'] for r in units], 'v16 manifest/frame identity mismatch')
    parents = (parent / 'selected-records.jsonl').read_bytes().splitlines(keepends=True)
    merged = (compatible / 'selected-records.jsonl').read_bytes().splitlines(keepends=True)
    require(len(parents) == len(merged) == len(units) == 4481, '4481 full lines required')
    normalized, null_n, preserved = [], 0, 0
    for old_line, line, u, pb in zip(parents, merged, units, manifest):
        old, r = json.loads(old_line), json.loads(line)
        require(old['id'] == r['id'] == u['unit_id'] == pb['source_id'] == pb['output_id'], 'Record ID/order mismatch')
        require(r['packet']['bytes'] == pb['bytes'] and r['packet']['sha256'] == pb['sha256']
                and Path(r['packet']['path']).resolve() == Path(pb['path']).resolve(), 'v16 packet mismatch: ' + r['id'])
        # Expected source_bundle binding is the frozen manifest's ID -> packet bridge.
        require(pb['source_bundle_sha256'] and type(pb['source_bundle_utf8_bytes']) is int, 'Missing source bundle bridge')
        if r['id'] not in DELTA:
            require(line == old_line, 'A non-delta parent row changed: ' + r['id'])
            preserved += 1
        else:
            n = new[r['id']]
            require(r['original_batch_id'] == 'batch-0216' and r['first'] == sel['first']
                    and r['technical_receipt'] == sel['reception'] and r['actor_seal'] == sel['actor_seal']
                    and r['selected_attempt_number'] == sel['attempt'] and r['dimensions'] == n['dimensions']
                    and n['packet_sha256'] == pb['sha256'], 'Spliced or unbound new batch row')
        labels = r['labels']
        require(set(labels) == set(m.DIMS) and set(r['dimensions']) == set(m.DIMS), 'Five dimensions required')
        require(all(v is None or type(v) is int and v in (0, 1) for v in labels.values()), 'Invalid labels')
        require(all(labels[d] == r['dimensions'][d]['value'] for d in m.DIMS), 'Label/dimension mismatch')
        null_n += sum(v is None for v in labels.values())
        normalized.append({'id': r['id'], 'labels': labels, 'implementation_errors': []})
    require(preserved == 4478 and null_n == mc['lawful_null_label_N'], 'Whole merge count mismatch')
    batches = m.load(compatible / 'selected-whole-batch-bindings.json')
    require(len(batches) == 504 and len({b['batch_id'] for b in batches}) == 504, 'Whole batch coverage missing')
    chosen = [b for b in batches if b['batch_id'] == 'batch-0216']
    require(len(chosen) == 1 and tuple(chosen[0]['source_ids']) == DELTA
            and chosen[0]['first'] == sel['first'] and chosen[0]['receipt'] == sel['reception'], '0216 whole batch binding mismatch')
    return normalized, {'full_parent_seal': ps, 'compatible_merge_seal': ms, 'selection': m.bind(selection),
        'process_completion': m.bind(process_path), 'packet_bindings_v16': m.bind(ROOT / '01-review/source-interface-v16-article6-addendum-sol/packet-bindings-v16.json'),
        'parent_record_N': 4481, 'parent_batch_N': 504, 'compatible_record_N': 4481,
        'parent_line_bytes_preserved_N': preserved, 'new_whole_batch_N': 1, 'new_whole_batch_record_N': 3, 'lawful_null_N': null_n,
        'labels_or_reasons_modified': False, 'null_imputed': False, 'formal_validation_complete': False, 'paper_writing_gate_open': False}


def metrics(s, d):
    v = s['dimensions'][d]
    if 'q_observed' in v:
        q = (v['q_observed'], v['q_conditional_lower'], v['q_conditional_upper'])
        p = (v['p_conditional_lower'], v['p_conditional_lower'], v['p_conditional_upper'])
    else:
        b = v['q_mean_conditional_bounds']
        q = (v['q_mean_among_observed_positive_members'], b['lower'], b['upper'])
        p = (v['p_mean_conditional_lower'], v['p_mean_conditional_lower'], v['p_mean_conditional_upper'])
    r = s.get('fractional_hit_share_r', {}).get('dimensions', {}).get(d)
    return {'q': q, 'p': p, 'r': (r['full_observed_point'], r['conditional_bounds']['lower'], r['conditional_bounds']['upper']) if r else (None, None, None)}


def rank(points):
    ordered = sorted(((k, v) for k, v in points.items() if v is not None), key=lambda x: (-x[1], str(x[0])))
    ties = []
    for key, value in ordered:
        if ties and math.isclose(value, ties[-1]['value'], rel_tol=0, abs_tol=1e-12):
            ties[-1]['members'].append(key)
        else:
            ties.append({'value': value, 'members': [key]})
    return {'descending_tie_groups': ties, 'undefined_members': [k for k, v in points.items() if v is None]}


def compare(m, rule, native):
    comparisons = []
    def records(items, part):
        for x in items:
            yield (part, x.get('removed_source_entry_id'), x.get('clock'), x.get('scenario'), tuple(x.get('group', ())),
                   x.get('department'), x.get('source_entry_year'), x.get('accepted_entry_policy_series')), x
    rr = dict(records(rule['scenarios'], 'scenario')) | dict(records(rule['leave_one_source_entry_out'], 'leave_one')) | dict(records(rule['annual_series_flows'], 'annual_series'))
    nn = dict(records(native['scenarios'], 'scenario')) | dict(records(native['leave_one_source_entry_out'], 'leave_one')) | dict(records(native['annual_series_flows'], 'annual_series'))
    require(rr.keys() == nn.keys(), 'Machines do not use the identical scenario/group definitions')
    for key, r in rr.items():
        n = nn[key]
        values, orders = {}, {}
        for d in m.DIMS:
            rm, nm = metrics(r['statistics'], d), metrics(n['statistics'], d)
            values[d] = {k: {'rule': rm[k], 'native': nm[k],
                'native_minus_rule_observed': None if rm[k][0] is None or nm[k][0] is None else nm[k][0] - rm[k][0],
                'native_minus_rule_conditional_bounds': [None, None] if any(v is None for v in (*rm[k][1:], *nm[k][1:])) else [nm[k][1] - rm[k][2], nm[k][2] - rm[k][1]]} for k in ('q', 'p', 'r')}
        for metric in ('q', 'p', 'r'):
            orders[metric] = {who: rank({d: values[d][metric][who][0] for d in m.DIMS}) for who in ('rule', 'native')}
        comparisons.append({'identity': list(key[:-4]) + [list(key[4]), *key[5:]], 'differences': values, 'within_group_dimension_orders': orders})
    axes = []
    for clock in ('policy_year', 'publication_year'):
        scenarios = {x['scenario'] for x in rule['scenarios'] if x['clock'] == clock}
        for scenario in sorted(scenarios):
            scopes = [('departments', 'all_years', 'department', 1, None), ('years', 'all_departments', 'corpus_year', 1, None)]
            scopes += [('departments', y, 'department_year', 1, (2, y)) for y in m.YEARS]
            scopes += [('years', d, 'department_year', 2, (1, d)) for d in m.DEPARTMENTS]
            for axis, scope, selector, key_index, restriction in scopes:
                for d in m.DIMS:
                    for metric in ('q', 'p', 'r'):
                        orders = {}
                        for who, corpus in (('rule', rule), ('native', native)):
                            pts = {str(x['group'][key_index]): metrics(x['statistics'], d)[metric][0] for x in corpus['scenarios'] if x['clock'] == clock and x['scenario'] == scenario and x['group'][0] == selector
                                   and (restriction is None or x['group'][restriction[0]] == restriction[1])}
                            orders[who] = rank(pts)
                        axes.append({'clock': clock, 'scenario': scenario, 'axis': axis, 'scope': scope, 'dimension': d, 'metric': metric, 'observed_orders': orders})
    return {'group_differences': comparisons, 'department_and_corpus_year_orders': axes,
            'comparison_identity': 'two machine outputs on identical 4481 materials; neither is gold',
            'point_contract': 'q uses observed positives; p point is observed-positive lower endpoint; r full point is undefined with any lawful null. Mean-q eligible source members may differ by machine; do not call this formal accuracy.',
            'bound_contract': 'Dimension-wise conditional null intervals, not confidence intervals or a bound on observed 0/1 errors.',
            'formal_validation_complete': False, 'paper_writing_gate_open': False}


def run(args):
    m = core()
    frozen = base_bindings(m)
    sealed(m, HERE)
    for b in m.load(HERE / 'input-contract.json')['immutable_bindings']:
        exact(m, b)
    output = Path(args.output).resolve()
    require(not output.exists(), 'Output must be a new directory')
    rows, proof = admission(m, args.parent, args.compatible, args.selection)
    rule_dir = Path(args.rule_attention).resolve()
    rule_seal = sealed(m, rule_dir, ('conditional-robustness.json',))
    rule = m.load(rule_dir / 'conditional-robustness.json')
    require(rule['unit_N'] == 4481 and rule['entry'] == frozen['entry'] and rule['inputs'] == frozen,
            'Rule attention is not this exact same-material frozen algorithm release')
    output.mkdir()
    facade = output / 'native-input-facade'
    facade.mkdir()
    for name in ('unit-metadata.jsonl', 'source-entry-metadata.json', 'metadata-coverage.json'):
        (facade / name).symlink_to(BASE / name)
    m.jsonl(facade / 'predictions.jsonl', rows)
    m.save(facade / 'status.json', {'actual_record_N': 4481, 'actual_dimension_N': 22405,
        'technical_failure_dimension_N': 0, 'lawful_null_N': proof['lawful_null_N'],
        'role': 'verified native adapter for legacy rule-named API; not a rule execution'})
    facade_bindings = dict(frozen, inputs=dict(frozen['inputs']))
    facade_bindings['inputs'].update(predictions=m.bind(facade / 'predictions.jsonl'),
        rule_status=m.bind(facade / 'status.json'), rule_seal=proof['compatible_merge_seal'])
    m.save(facade / 'input-bindings.json', facade_bindings)
    m.save(facade / 'seal.json', {'files': [m.bind(facade / n) for n in ('predictions.jsonl', 'status.json', 'input-bindings.json')], 'self_excluded': True})
    m.HERE = facade  # isolated imported module only; original code/material stays unchanged
    raw_dir = output / 'frozen-core-evaluation'
    m.analyze(raw_dir)
    raw = m.load(raw_dir / 'conditional-robustness.json')
    m.save(output / 'native-attention-source-role.json', {'machine': 'actual whole-batch LLM',
        'native_proof': proof, 'frozen_core_output': m.bind(raw_dir / 'conditional-robustness.json'),
        'legacy_rule_named_keys_are_statistical_facade_only': True,
        'core_formulas_and_scenarios_reused_without_copy_or_edit': True,
        'formal_validation_complete': False, 'paper_writing_gate_open': False})
    comparison = compare(m, rule, raw)
    comparison.update(rule_attention_seal=rule_seal, native_proof=proof, core_entry=frozen['entry'])
    m.save(output / 'machine-attention-comparison.json', comparison)
    m.save(output / 'seal.json', {'files': [m.bind(p) for p in sorted(output.rglob('*')) if p.is_file()],
        'self_excluded': True, 'formal_validation_complete': False, 'paper_writing_gate_open': False})


def selfcheck(args):
    m = core()
    base_bindings(m)
    manifest = m.load(ROOT / '01-review/source-interface-v16-article6-addendum-sol/packet-bindings-v16.json')
    units = list(m.iter_jsonl(BASE / 'unit-metadata.jsonl'))
    require([r['source_id'] for r in manifest] == [u['unit_id'] for u in units] and len(manifest) == 4481, 'Static v16 identity mismatch')
    parent = Path(args.partial_parent).resolve()
    sealed(m, parent, ('coverage.json',))
    try:
        full_coverage(m, parent / 'coverage.json')
    except ValueError as error:
        c = m.load(parent / 'coverage.json')
        m.save(HERE / 'mechanical-check.json', {'partial_rejected': True, 'actual_selected_record_N': c['selected_record_N'],
            'rejection': str(error), 'coverage': m.bind(parent / 'coverage.json'), 'partial_seal': m.bind(parent / 'seal.json'),
            'v16_ID_binding_N': len(manifest), 'core_unchanged': True, 'actual_full_analysis_executed': False,
            'models_called': 0, 'classifiers_called': 0, 'formal_validation_complete': False, 'paper_writing_gate_open': False})
    else:
        raise ValueError('selfcheck requires an actual incomplete snapshot; it must refuse it')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    check = sub.add_parser('selfcheck')
    check.add_argument('--partial-parent', required=True)
    execute = sub.add_parser('run')
    for argument in ('parent', 'compatible', 'selection', 'rule-attention', 'output'):
        execute.add_argument('--' + argument, required=True)
    args = p.parse_args()
    selfcheck(args) if args.command == 'selfcheck' else run(args)
