#!/usr/bin/env python3
"""Mechanical census sensitivity preparation / conditional rule aggregation.

No classifier, model, reference answers, source interpretation, or inferred
component/issuer attribution. Run prepare and selftest before sealing; run
analyze only against that sealed preparation, into a new output directory.
"""
from pathlib import Path
import argparse
import collections
import datetime
import hashlib
import json
import math

DIMS = ('S', 'E', 'Ec', 'I', 'F')
DEPARTMENTS = ('NMPA', 'NHSA', 'NHC')
YEARS = tuple(range(2017, 2027))
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
INPUTS = {
    'bundles': ROOT / '01-review/source-interface-v16-article6-addendum-sol/common-frame-bundles-v16.jsonl',
    'year_map': ROOT / '07-statistics/annual-year-input-binding-sol/full4481-year-map.jsonl',
    'entry_metadata': ROOT / '01-review/annual-metadata-integrated-sol/source-entry-metadata.jsonl',
    'date_evidence': ROOT / '07-statistics/annual-year-input-binding-sol/source-entry-date-evidence.jsonl',
    'year_seal': ROOT / '07-statistics/annual-year-input-binding-sol/seal.json',
    'metadata_seal': ROOT / '01-review/annual-metadata-integrated-sol/seal.json',
    'material_seal': ROOT / '01-review/source-interface-v16-article6-addendum-sol/output-seal.json',
    'predictions': ROOT / '06-coding/rule-full4481-v11-v16-receipt-delta-merged-root/predictions.jsonl',
    'rule_status': ROOT / '06-coding/rule-full4481-v11-v16-receipt-delta-merged-root/composite-status.json',
    'rule_seal': ROOT / '06-coding/rule-full4481-v11-v16-receipt-delta-merged-root/seal.json',
    'plan': ROOT / '02-methods/department-year-analysis-plan-sol/report.json',
    'existing_engine': ROOT / '07-statistics/prospective-engine-year-independent-audit-sol/metrics_engine_repaired.py',
    'existing_bounds': ROOT / '07-statistics/rule-v11-v16-attention-null-bounds-diagnostic-root/conditional-bounds.json',
}


def bind(path):
    path = Path(path).resolve()
    b = path.read_bytes()
    return {'path': str(path), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def exact(binding):
    if bind(binding['path']) != binding:
        raise ValueError('Frozen input binding changed: ' + binding['path'])


def load(path):
    return json.loads(Path(path).read_bytes())


def iter_jsonl(path):
    with Path(path).open(encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)


def save(path, obj):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def jsonl(path, rows):
    with Path(path).open('x', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')


def div(a, b):
    return None if b == 0 else a / b


def prepare():
    # Hash all inputs, but do not inspect prediction evidence or any label here.
    bindings = {k: bind(p) for k, p in INPUTS.items()}
    years = list(iter_jsonl(INPUTS['year_map']))
    entries = list(iter_jsonl(INPUTS['entry_metadata']))
    em = {e['source_entry_id']: e for e in entries}
    assert len(years) == 4481 and len(em) == len(entries) == 51
    assert len({m['unit_id'] for m in years}) == 4481
    assert sum(e['listed_component_n'] for e in entries) == 56
    fields = ('source_entry_id', 'source_entry_identity_sha256', 'department',
              'policy_year', 'publication_year', 'issue_date', 'publication_date',
              'year_basis', 'policy_series', 'annual_series', 'series_basis',
              'joint_publication', 'publishers', 'department_assignment_basis',
              'listed_component_n', 'component_mapping_status', 'component_clock_status')
    projection = []
    for e in entries:
        assert type(e['annual_series']) is bool and type(e['joint_publication']) is bool
        assert isinstance(e['policy_series'], str) and e['policy_series']
        assert isinstance(e['publishers'], list) and e['publishers']
        projection.append({k: e[k] for k in fields})
    units = []
    counts = collections.Counter()
    lengths = collections.Counter()
    bundles = iter_jsonl(INPUTS['bundles'])
    for m in years:
        b = next(bundles)
        source = b['source_record']
        assert source['id'] == m['unit_id'] == m['source_id']
        assert m['component_id'] is None
        e = em[m['source_entry_id']]
        for k in ('department', 'policy_year', 'publication_year', 'year_basis',
                  'source_entry_identity_sha256', 'issue_date', 'publication_date'):
            assert m[k] == e[k], (m['unit_id'], k)
        assert m['department'] in DEPARTMENTS
        assert type(m['policy_year']) is int and type(m['publication_year']) is int
        text = source['text']  # mechanical hash/length only, never emitted
        assert isinstance(text, str)
        record = {k: m[k] for k in ('unit_id', 'source_entry_id', 'department',
                  'policy_year', 'publication_year', 'year_basis', 'component_id')}
        record.update(exact_current_text_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
                      current_text_unicode_N=len(text))
        units.append(record)
        counts[m['source_entry_id']] += 1
        lengths[m['source_entry_id']] += len(text)
    assert next(bundles, None) is None
    for e in projection:
        assert counts[e['source_entry_id']] == em[e['source_entry_id']]['clause_n']
        e['clause_N'] = counts[e['source_entry_id']]
        e['parsed_current_clause_unicode_N'] = lengths[e['source_entry_id']]
    date_counts = collections.Counter(e['year_basis'] for e in entries)
    assert date_counts == {'issue_date': 48, 'original_publication_date_fallback_no_issue_date': 3}
    annual = [e for e in entries if e['annual_series']]
    joint = [e for e in entries if e['joint_publication']]
    multi = [e for e in entries if e['listed_component_n'] > 1]
    duplicates = {}
    for clock in ('policy_year', 'publication_year'):
        for scope in ('same_source', 'same_department_year'):
            groups = duplicate_groups(units, scope, clock)
            dup = [g for g in groups.values() if len(g) > 1]
            cross = [g for g in dup if len({r['source_entry_id'] for r in g}) > 1]
            duplicates[clock + '/' + scope] = {
                'group_N': len(groups), 'repeated_group_N': len(dup),
                'member_N_in_repeated_groups': sum(map(len, dup)),
                'cross_source_repeated_group_N': len(cross),
                'member_N_in_cross_source_repeated_groups': sum(map(len, cross))}
    report = {
        'schema': 'full4481-attention-mechanical-preparation-v1',
        'unit_N': len(units), 'source_entry_N': len(entries), 'listed_component_N': 56,
        'component_id_missing_unit_N': 4481,
        'year_clock': 'source-entry issue-date-first, original-publication-date fallback; not component years',
        'source_entry_year_basis_N': dict(date_counts),
        'clause_year_basis_N': dict(collections.Counter(r['year_basis'] for r in units)),
        'main_and_publication_year_membership_identical': all(r['policy_year'] == r['publication_year'] for r in units),
        'annual_series_entry_N': len(annual), 'annual_series_clause_N': sum(e['clause_n'] for e in annual),
        'confirmed_annual_series_N': len({e['policy_series'] for e in annual}),
        'joint_entry_N': len(joint), 'joint_clause_N': sum(e['clause_n'] for e in joint),
        'multi_component_entries': [{k: e[k] for k in ('source_entry_id', 'policy_year', 'department', 'listed_component_n', 'clause_n')} for e in multi],
        'duplicate_metadata': duplicates,
        'text_used_only_for_hash_and_length': True, 'source_text_emitted': False,
        'labels_aggregated_in_preparation': False, 'models_called': 0, 'classifiers_called': 0,
        'formal_validation_complete': False, 'paper_writing_gate_open': False,
        'not_supported': {
            'independent_component_equal_weight_and_component_years': 'All 4481 component_id are null; 51 entries include bundles with 56 listed components. No unit-component assignment is invented.',
            'joint_issuer_department_reallocation': 'Actual publisher names are preserved, but no accepted unit-level multi-department attribution is provided. Frozen single department is retained.',
            'semantic_or_template_deduplication': 'Exact UTF-8 current-text equality only; contexts and decisions remain distinct.',
            'same_month_day_windows_or_in_force_stock': 'Not implemented by this source-entry-year census entry; no duration/carry-forward/annualization inference.',
        },
    }
    jsonl(HERE / 'unit-metadata.jsonl', units)
    save(HERE / 'source-entry-metadata.json', projection)
    save(HERE / 'metadata-coverage.json', report)
    save(HERE / 'input-bindings.json', {
        'schema': 'attention-input-bindings-v1', 'inputs': bindings, 'entry': bind(__file__),
        'prepared': {p.name: bind(p) for p in (HERE / 'unit-metadata.jsonl', HERE / 'source-entry-metadata.json', HERE / 'metadata-coverage.json')},
        'formal_validation_complete': False, 'paper_writing_gate_open': False})
    print(json.dumps({k: report[k] for k in ('unit_N', 'source_entry_N', 'listed_component_N', 'annual_series_entry_N', 'joint_entry_N', 'main_and_publication_year_membership_identical')}))


def duplicate_groups(rows, scope, clock):
    groups = collections.defaultdict(list)
    for r in rows:
        owner = (r['source_entry_id'], r[clock]) if scope == 'same_source' else (r['department'], r[clock])
        groups[owner + (r['exact_current_text_sha256'],)].append(r)
    return groups


def weights(rows, mode, clock):
    if mode == 'clause_equal':
        return {r['unit_id']: 1.0 for r in rows}
    scope = {'text_repeat_same_source': 'same_source', 'text_repeat_department_year': 'same_department_year'}[mode]
    return {r['unit_id']: 1.0 / len(g) for g in duplicate_groups(rows, scope, clock).values() for r in g}


def mean_bounds(required, optional):
    """Each tuple is (lower, upper, weight); optional members may be absent."""
    base_w = sum(v[2] for v in required)
    lower_values, upper_values = [], []
    for index, descending, values in ((0, False, lower_values), (1, True, upper_values)):
        a = sum(v[index] * v[2] for v in required)
        w = base_w
        if w:
            values.append(a / w)
        for item in sorted(optional, key=lambda x: x[index], reverse=descending):
            a += item[index] * item[2]
            w += item[2]
            values.append(a / w)
    return {'lower': min(lower_values) if lower_values else None,
            'upper': max(upper_values) if upper_values else None,
            'undefined_possible': base_w == 0}


def fractional_hit_share(rows, w):
    # r: every hit clause contributes total weight 1, divided among its labels.
    complete = [r for r in rows if all(r['labels'][d] is not None for d in DIMS)]
    hit_complete = [r for r in complete if any(r['labels'][d] == 1 for d in DIMS)]
    complete_den = sum(w[r['unit_id']] for r in hit_complete)
    all_complete = len(complete) == len(rows)
    dims = {}
    for d in DIMS:
        req, opt = [], []
        for r in rows:
            ls = r['labels']
            pos = sum(ls[x] == 1 for x in DIMS)
            unknown = sum(ls[x] is None for x in DIMS)
            wd = w[r['unit_id']]
            if pos:
                lo = 1 / (pos + unknown) if ls[d] == 1 else 0.0
                hi = 1 / pos if ls[d] == 1 else (1 / (pos + 1) if ls[d] is None else 0.0)
                req.append((lo, hi, wd))
            elif unknown:
                lo = 0.0 if unknown - (ls[d] is None) > 0 else 1.0
                hi = 1.0 if ls[d] is None else 0.0
                opt.append((lo, hi, wd))
        num = sum(w[r['unit_id']] * r['labels'][d] / sum(r['labels'][x] for x in DIMS) for r in hit_complete)
        dims[d] = {'full_observed_point': div(num, complete_den) if all_complete else None,
                   'complete_record_subset_auxiliary_point': div(num, complete_den),
                   'conditional_bounds': mean_bounds(req, opt)}
    return {'formula': 'sum(weight * Y_d/K for hit clauses) / sum(weight for hit clauses)',
            'all_five_binary_record_N': len(complete), 'all_five_binary_record_weight': sum(w[r['unit_id']] for r in complete),
            'complete_subset_hit_weight': complete_den,
            'full_point_status': 'complete' if all_complete else 'unresolved_labels_no_full_point',
            'dimensions': dims}


def aggregate(rows, w):
    total_w = sum(w[r['unit_id']] for r in rows)
    positive = {d: sum(w[r['unit_id']] for r in rows if r['labels'][d] == 1) for d in DIMS}
    unknown = {d: sum(w[r['unit_id']] for r in rows if r['labels'][d] is None) for d in DIMS}
    bp, bu = sum(positive.values()), sum(unknown.values())
    dimensions = {d: {
        'positive_weight': positive[d], 'negative_weight': total_w - positive[d] - unknown[d],
        'unresolved_weight': unknown[d],
        'q_observed': div(positive[d], bp),
        'q_conditional_lower': div(positive[d], bp + bu - unknown[d]),
        'q_conditional_upper': div(positive[d] + unknown[d], bp + unknown[d]),
        'p_conditional_lower': div(positive[d], total_w),
        'p_conditional_upper': div(positive[d] + unknown[d], total_w)} for d in DIMS}
    # 0/0 means no q at all; bounds endpoints requiring a positive denominator
    # are handled separately for a group with no observed positive labels.
    if bp == 0 and bu:
        for d in DIMS:
            dimensions[d]['q_conditional_lower'] = 0.0 if bu - unknown[d] > 0 else 1.0
            dimensions[d]['q_conditional_upper'] = 1.0 if unknown[d] > 0 else 0.0
    return {'clause_N': len(rows), 'source_entry_N': len({r['source_entry_id'] for r in rows}),
            'clause_weight': total_w, 'positive_assignment_weight': bp, 'unresolved_assignment_weight': bu,
            'q_undefined_possible': bp == 0,
            'known_all_zero_record_N': sum(all(r['labels'][d] == 0 for d in DIMS) for r in rows),
            'unresolved_record_N': sum(any(r['labels'][d] is None for d in DIMS) for r in rows),
            'known_all_zero_weight': sum(w[r['unit_id']] for r in rows if all(r['labels'][d] == 0 for d in DIMS)),
            'observed_labels_per_clause_N': dict(collections.Counter(sum(r['labels'][d] == 1 for d in DIMS) for r in rows)),
            'observed_B_per_clause_weight': div(bp, total_w), 'dimensions': dimensions,
            'fractional_hit_share_r': fractional_hit_share(rows, w)}


def means(rows, key):
    parts = collections.defaultdict(list)
    for r in rows:
        parts[key(r)].append(r)
    summaries = [aggregate(g, weights(g, 'clause_equal', 'policy_year')) for g in parts.values()]
    mandatory = [s for s in summaries if s['positive_assignment_weight'] > 0]
    optional = [s for s in summaries if s['positive_assignment_weight'] == 0 and s['unresolved_assignment_weight'] > 0]
    result = {}
    for d in DIMS:
        req = [(s['dimensions'][d]['q_conditional_lower'], s['dimensions'][d]['q_conditional_upper'], 1.0) for s in mandatory]
        opt = [(s['dimensions'][d]['q_conditional_lower'], s['dimensions'][d]['q_conditional_upper'], 1.0) for s in optional]
        result[d] = {
            'q_mean_among_observed_positive_members': div(sum(s['dimensions'][d]['q_observed'] for s in mandatory), len(mandatory)),
            'q_mean_conditional_bounds': mean_bounds(req, opt),
            'p_mean_conditional_lower': div(sum(s['dimensions'][d]['p_conditional_lower'] for s in summaries), len(summaries)),
            'p_mean_conditional_upper': div(sum(s['dimensions'][d]['p_conditional_upper'] for s in summaries), len(summaries))}
    return {'member_N': len(summaries), 'q_observed_defined_member_N': len(mandatory),
            'q_observed_undefined_member_N': len(summaries) - len(mandatory),
            'q_may_become_defined_member_N': len(optional),
            'q_always_undefined_member_N': len(summaries) - len(mandatory) - len(optional),
            'q_zero_denominator_member_keys': [list(k) if isinstance(k, tuple) else k for k, g in parts.items() if not any(r['labels'][d] == 1 for r in g for d in DIMS)],
            'p_mean_includes_known_zero_members': True, 'dimensions': result}


def group_specs():
    return ([('entire_corpus',)] + [('department', d) for d in DEPARTMENTS]
            + [('corpus_year', y) for y in YEARS]
            + [('department_year', d, y) for d in DEPARTMENTS for y in YEARS])


def subset(rows, spec, clock):
    if spec[0] == 'entire_corpus':
        return rows
    if spec[0] == 'department':
        return [r for r in rows if r['department'] == spec[1]]
    if spec[0] == 'corpus_year':
        return [r for r in rows if r[clock] == spec[1]]
    return [r for r in rows if (r['department'], r[clock]) == spec[1:]]


def duplicate_label_audit(rows, clock):
    results = {}
    for scope in ('same_source', 'same_department_year'):
        repeated = [g for g in duplicate_groups(rows, scope, clock).values() if len(g) > 1]
        results[scope] = {
            'repeated_group_N': len(repeated),
            'member_N': sum(map(len, repeated)),
            'binary_conflict_group_N_by_dimension': {d: sum({r['labels'][d] for r in g if r['labels'][d] is not None} == {0, 1} for g in repeated) for d in DIMS},
            'unresolved_group_N_by_dimension': {d: sum(any(r['labels'][d] is None for r in g) for g in repeated) for d in DIMS},
            'full_vector_difference_group_N': sum(len({tuple(r['labels'][d] for d in DIMS) for r in g}) > 1 for g in repeated),
            'cross_source_repeated_group_N': sum(len({r['source_entry_id'] for r in g}) > 1 for g in repeated)}
    return results


def analyze(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Output must be a new directory')
    preparation = load(HERE / 'seal.json')
    for b in preparation['files']:
        exact(b)
    bindings = load(HERE / 'input-bindings.json')
    exact(bindings['entry'])
    for b in list(bindings['inputs'].values()) + list(bindings['prepared'].values()):
        exact(b)
    status = load(bindings['inputs']['rule_status']['path'])
    assert status['actual_record_N'] == 4481 and status['actual_dimension_N'] == 22405
    assert status['technical_failure_dimension_N'] == 0
    rows = list(iter_jsonl(HERE / 'unit-metadata.jsonl'))
    entries = load(HERE / 'source-entry-metadata.json')
    em = {e['source_entry_id']: e for e in entries}
    prediction_iter = iter_jsonl(bindings['inputs']['predictions']['path'])
    null_n = 0
    for r in rows:
        p = next(prediction_iter)
        assert p['id'] == r['unit_id']
        assert not p.get('implementation_errors')
        ls = p['labels']
        assert set(ls) == set(DIMS)
        assert all(v is None or type(v) is int and v in (0, 1) for v in ls.values())
        r['labels'] = {d: ls[d] for d in DIMS}
        null_n += sum(v is None for v in ls.values())
    assert next(prediction_iter, None) is None
    assert null_n == status['lawful_null_N']
    scenarios = {
        'clause_equal': (rows, 'clause_equal'),
        'text_repeat_same_source': (rows, 'text_repeat_same_source'),
        'text_repeat_department_year': (rows, 'text_repeat_department_year'),
        'exclude_joint_entries': ([r for r in rows if not em[r['source_entry_id']]['joint_publication']], 'clause_equal'),
        'exclude_annual_series_entries': ([r for r in rows if not em[r['source_entry_id']]['annual_series']], 'clause_equal'),
        'exclude_multicomponent_entries': ([r for r in rows if em[r['source_entry_id']]['listed_component_n'] == 1], 'clause_equal'),
        'calendar_year_bounds_2018_2025_only': (rows, 'clause_equal')}
    results = []
    for clock in ('policy_year', 'publication_year'):
        for name, (selected, mode) in scenarios.items():
            if name == 'calendar_year_bounds_2018_2025_only':
                selected = [r for r in selected if 2018 <= r[clock] <= 2025]
            w = weights(selected, mode, clock)
            for spec in group_specs():
                g = subset(selected, spec, clock)
                results.append({'clock': clock, 'scenario': name, 'group': list(spec), 'statistics': aggregate(g, w)})
        for spec in group_specs():
            g = subset(rows, spec, clock)
            results.append({'clock': clock, 'scenario': 'source_entry_q_p_mean', 'group': list(spec),
                            'statistics': means(g, lambda r: r['source_entry_id'])})
            # No component allocation: series is the accepted entry-level field.
            results.append({'clock': clock, 'scenario': 'series_within_year_q_p_mean', 'group': list(spec),
                            'statistics': means(g, lambda r: (r['department'], r[clock], em[r['source_entry_id']]['policy_series']))})
    series = []
    for (dep, year, family), g in sorted(_series_groups(rows, em).items()):
        series.append({'department': dep, 'source_entry_year': year, 'accepted_entry_policy_series': family,
                       'statistics': aggregate(g, weights(g, 'clause_equal', 'policy_year'))})
    leave_one = []
    for e in entries:
        selected = [r for r in rows if r['source_entry_id'] != e['source_entry_id']]
        for clock in ('policy_year', 'publication_year'):
            for spec in (('entire_corpus',), ('department', e['department']), ('corpus_year', e[clock]), ('department_year', e['department'], e[clock])):
                g = subset(selected, spec, clock)
                leave_one.append({'removed_source_entry_id': e['source_entry_id'], 'clock': clock,
                                  'group': list(spec), 'statistics': aggregate(g, weights(g, 'clause_equal', clock))})
    coverage = load(HERE / 'metadata-coverage.json')
    report = {
        'schema': 'full4481-conditional-attention-robustness-v1', 'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'identity': 'conditional diagnostic on frozen observed rule labels, not final findings',
        'unit_N': 4481, 'technical_failure_N': 0, 'lawful_null_assignment_N': null_n,
        'q': 'positive assignment weight / sum of positive assignment weights across five dimensions',
        'p': 'positive assignment weight / clause weight, includes known all-zero clauses',
        'null_contract': 'Observed 0/1 fixed; each lawful null may independently be 0/1. Each dimension interval optimized separately, not a joint rectangle or CI.',
        'mean_contract': 'q first per member then mean only over positive-assignment members; B=0 is NA, optional null-only members enumerated. p mean uses every nonempty member, including known zero.',
        'repeat_contract': 'Exact UTF-8 current text, no whitespace normalization. Weight 1/multiplicity in fixed same-source/year or same-department/year groups; retain every context and label. Cross-year repetitions are preserved.',
        'file_length_contract': 'Source entry clause_N and summed parsed-current-clause Unicode length, not physical page count or independent-component length.',
        'series_contract': 'Accepted source-entry policy_series only; series-year-member mean. Bundled component series are not reassigned; absent series-years are omitted, not zero-filled.',
        'year_contract': coverage['year_clock'], 'metadata_coverage': coverage,
        'duplicate_conflicts_and_nulls': {clock: duplicate_label_audit(rows, clock) for clock in ('policy_year', 'publication_year')},
        'scenarios': results, 'annual_series_flows': series, 'leave_one_source_entry_out': leave_one,
        'confidence_intervals_computed': False, 'human_or_stability_answers_read': False,
        'models_called': 0, 'classifiers_called': 0, 'formal_validation_complete': False, 'paper_writing_gate_open': False,
        'inputs': bindings, 'preparation_seal': bind(HERE / 'seal.json'), 'entry': bind(__file__)}
    output.mkdir()
    save(output / 'conditional-robustness.json', report)
    save(output / 'seal.json', {'files': [bind(output / 'conditional-robustness.json')], 'self_excluded': True,
                              'formal_validation_complete': False, 'paper_writing_gate_open': False})
    print(json.dumps({'unit_N': 4481, 'scenario_group_N': len(results), 'annual_series_flow_N': len(series),
                      'leave_one_entry_group_N': len(leave_one), 'lawful_null_assignment_N': null_n,
                      'formal_validation_complete': False, 'paper_writing_gate_open': False}))


def _series_groups(rows, em):
    groups = collections.defaultdict(list)
    for r in rows:
        e = em[r['source_entry_id']]
        if e['annual_series']:
            groups[(r['department'], r['policy_year'], e['policy_series'])].append(r)
    return groups


def selftest():
    def row(i, s, values, text='x', year=2020):
        return {'unit_id': i, 'source_entry_id': s, 'department': 'NMPA', 'policy_year': year,
                'publication_year': year, 'exact_current_text_sha256': text, 'labels': dict(zip(DIMS, values))}
    a = row('a', 'A', [1, 1, 0, 0, 0])
    b = row('b', 'A', [0, 0, 0, 0, 0])
    c = row('c', 'B', [0, 0, 0, 1, 0])
    g = [a, b, c]
    s = aggregate(g, weights(g, 'clause_equal', 'policy_year'))
    assert s['positive_assignment_weight'] == 3 and s['clause_weight'] == 3
    assert s['dimensions']['S']['q_observed'] == 1/3 and s['dimensions']['S']['p_conditional_lower'] == 1/3
    assert s['known_all_zero_record_N'] == 1
    same = weights(g, 'text_repeat_same_source', 'policy_year')
    cross = weights(g, 'text_repeat_department_year', 'policy_year')
    assert same == {'a': .5, 'b': .5, 'c': 1.0}
    assert all(math.isclose(v, 1/3) for v in cross.values())
    # Conflicting duplicate labels are retained, neither OR nor a representative.
    assert aggregate(g, same)['dimensions']['S']['positive_weight'] == .5
    later = row('d', 'B', [0, 0, 0, 1, 0], year=2021)
    assert weights([a, later], 'text_repeat_department_year', 'policy_year') == {'a': 1., 'd': 1.}
    equal = means(g, lambda r: r['source_entry_id'])
    assert equal['dimensions']['S']['q_mean_among_observed_positive_members'] == .25
    assert equal['dimensions']['S']['p_mean_conditional_lower'] == .25
    zero = means([b], lambda r: r['source_entry_id'])
    assert zero['dimensions']['S']['q_mean_among_observed_positive_members'] is None
    assert zero['dimensions']['S']['p_mean_conditional_lower'] == 0
    empty = aggregate([], {})
    assert empty['dimensions']['S']['q_observed'] is None and empty['dimensions']['S']['p_conditional_lower'] is None
    pending = row('n', 'C', [None, 0, 0, 0, 0])
    uncertain = means([c, pending], lambda r: r['source_entry_id'])
    assert uncertain['dimensions']['S']['q_mean_conditional_bounds'] == {'lower': 0., 'upper': .5, 'undefined_possible': False}
    only_pending = aggregate([pending], {'n': 1.})
    assert only_pending['dimensions']['S']['q_conditional_lower'] == 1.
    assert only_pending['q_undefined_possible'] is True
    # Optional mean bounds validated by exhaustive independent null assignments.
    tiny = [a, pending, row('u', 'D', [0, None, 0, None, 0])]
    unresolved = [(i, d) for i, r in enumerate(tiny) for d in DIMS if r['labels'][d] is None]
    by_d = {d: [] for d in DIMS}
    for mask in range(1 << len(unresolved)):
        assignment = [dict(r, labels=dict(r['labels'])) for r in tiny]
        for bit, (i, d) in enumerate(unresolved):
            assignment[i]['labels'][d] = (mask >> bit) & 1
        z = means(assignment, lambda r: r['source_entry_id'])
        for d in DIMS:
            by_d[d].append(z['dimensions'][d]['q_mean_among_observed_positive_members'])
    bounds = means(tiny, lambda r: r['source_entry_id'])
    for d in DIMS:
        v = bounds['dimensions'][d]['q_mean_conditional_bounds']
        assert math.isclose(v['lower'], min(by_d[d])) and math.isclose(v['upper'], max(by_d[d]))
    rstat = s['fractional_hit_share_r']['dimensions']
    assert rstat['S']['full_observed_point'] == .25 and rstat['I']['full_observed_point'] == .5
    # Missing component/issuer/series fields are not fabricated in synthetic rows.
    assert 'component_id' not in a and 'publishers' not in a and 'policy_series' not in a
    save(HERE / 'synthetic-check.json', {'scope': 'small synthetic denominator, repeat weight, zero/empty denominator, optional null membership, fractional multi-label, missing-field preservation',
         'passed': True, 'real_label_aggregation_executed': False, 'models_called': 0, 'classifiers_called': 0,
         'formal_validation_complete': False, 'paper_writing_gate_open': False, 'entry': bind(__file__)})
    print(json.dumps({'synthetic_check_passed': True, 'real_label_aggregation_executed': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('prepare')
    commands.add_parser('selftest')
    run = commands.add_parser('analyze')
    run.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    elif args.command == 'selftest':
        selftest()
    else:
        analyze(args.output)


if __name__ == '__main__':
    main()
