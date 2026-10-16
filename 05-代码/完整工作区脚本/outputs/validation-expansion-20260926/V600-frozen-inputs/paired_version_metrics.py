"""Planning-stage paired version statistics; no real labels are read on import.

Payload: strata/population_N and rows as in survey_metrics.prepare, with A/C
and explicit baseline/candidate five-dimensional label maps on every row.
coders[A/C] must explicitly describe the AI identity. baseline_info and
candidate_info contain version and prediction_sha256. No consensus reference
is constructed. The caller must establish the frozen probability sample and
complete, hash-bound original submissions; this pure engine cannot prove them.

All comparisons share 2000 stratified SRSWOR FPC-rescaled replicates, seed
2026092606. Ordinary PRF is conditional on each model/reference pair being
definite. Version differences instead condition on BOTH models AND the same
reference being definite, and disclose that joint coverage. This prevents a
change in the assessed subset being reported as a paired improvement.

Primary differences are candidate-minus-baseline Recall and F1, separately
against A and C. Precision is fully reported for every version but is not a
post hoc substituted primary endpoint. Intervals are marginal approximate
percentile intervals; they do not prove accuracy against a human gold standard.
"""
from __future__ import annotations

import copy
import json
import re

import numpy as np

import survey_metrics as base

DIMS = base.DIMS
REPLICATES = 2000
SEED = 2026092606
PRIMARY_DELTAS = ('recall_definite', 'f1_definite')


def label_map(value, name):
    if not isinstance(value, dict) or set(value) != set(DIMS):
        raise ValueError(name + ': exact five-dimensional map required')
    return [base._label(value[d]) for d in DIMS]


def prepare(payload):
    if not isinstance(payload, dict):
        raise ValueError('Payload must be an object')
    if not isinstance(payload.get('coders'), dict):
        raise ValueError('Explicit coder metadata required')
    for coder in ('A', 'C'):
        info = payload.get('coders', {}).get(coder, {})
        if not isinstance(info, dict) or info.get('kind') != 'AI' or not isinstance(info.get('description'), str) or not info['description'].strip():
            raise ValueError('Explicit AI identity required: ' + coder)
    for version in ('baseline', 'candidate'):
        info = payload.get(version + '_info', {})
        if not isinstance(info, dict) or not isinstance(info.get('version'), str) or not info['version'].strip():
            raise ValueError('Explicit version required: ' + version)
        if not isinstance(info.get('prediction_sha256'), str) or not re.fullmatch('[0-9a-f]{64}', info['prediction_sha256']):
            raise ValueError('Explicit prediction hash required: ' + version)
    rows = payload.get('rows')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Nonempty rows required')
    cleaned = []
    version_maps = {'baseline': {}, 'candidate': {}}
    seen_ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Row must be an object')
        key = row.get('id')
        if not isinstance(key, str) or not key or key in seen_ids:
            raise ValueError('Row IDs must be unique nonempty strings')
        seen_ids.add(key)
        item = {key: row.get(key) for key in ('id', 'stratum', 'N_h', 'n_h', 'A', 'C')}
        for coder in ('A', 'C'):
            label_map(item[coder], coder)
        cleaned.append(item)
        for version in version_maps:
            version_maps[version][key] = label_map(row.get(version), version)
    p = base.prepare({'strata': payload.get('strata'), 'population_N': payload.get('population_N'), 'rows': cleaned})
    # prepare() validates unique IDs and canonically sorts whole rows. Use its
    # row ordering for every model; never align labels by original position.
    for version, values in version_maps.items():
        p['labels'][version] = np.asarray([values[row['id']] for row in p['rows']], dtype=int)
    return p


def replicate_weights(p):
    rng = np.random.Generator(np.random.PCG64(SEED))
    weights = np.tile(p['weights'], (REPLICATES, 1))
    for _, N, n, indices in p['groups']:
        if n == N:
            continue
        counts = rng.multinomial(n - 1, np.full(n, 1 / n), size=REPLICATES)
        factors = 1 + np.sqrt(1 - n / N) * (n * counts / (n - 1) - 1)
        weights[:, indices] *= factors
        if not np.allclose(weights[:, indices].sum(axis=1), N, rtol=1e-12, atol=1e-10):
            raise AssertionError('Replicate stratum weight total changed')
    if not np.allclose(weights.sum(axis=1), p['N']):
        raise AssertionError('Replicate population totals changed')
    if not np.all(np.isfinite(weights)) or np.any(weights <= 0):
        raise AssertionError('Unexpected nonpositive/nonfinite replicate weight')
    return weights


def comparison(p, rw, left, right, classification):
    one_hot = np.eye(9)[3 * left + right]
    table = (p['weights'] @ one_hot).reshape(3, 3)
    tables = (rw @ one_hot).reshape(REPLICATES, 3, 3)
    point, flags = base.metrics_from_table(table, classification)
    replicates = [base.metrics_from_table(t, classification)[0] for t in tables]
    intervals = {key: base.interval_summary(value, [r[key] for r in replicates], p['all_census'])
                 for key, value in point.items()}
    result = {'table_axis_order': [0, 1, base.PENDING],
              'raw_3x3_counts': one_hot.sum(axis=0).reshape(3, 3).astype(int).tolist(),
              'weighted_3x3_estimated_totals': table.tolist(),
              'estimates': point, 'completion_and_undefined_flags': flags,
              'marginal_95_intervals': intervals}
    return result, replicates


def common_subset_view(result):
    # The temporary masking used by comparison is computational only. Never
    # expose its synthetic pending cells as original model abstentions/bounds.
    keys = ('TP', 'FP', 'FN', 'TN', 'precision_definite', 'recall_definite',
            'f1_definite', 'specificity_definite', 'accuracy_definite')
    return {
        'scope': 'jointly definite baseline, candidate and specified reference only',
        'table_axis_order': [0, 1],
        'raw_2x2_counts': [row[:2] for row in result['raw_3x3_counts'][:2]],
        'weighted_2x2_estimated_totals': [row[:2] for row in result['weighted_3x3_estimated_totals'][:2]],
        'estimates': {k: result['estimates'][k] for k in keys},
        'marginal_95_intervals': {k: result['marginal_95_intervals'][k] for k in keys},
        'note': 'Original model abstentions and full-sample completion bounds are in comparisons, not in this restricted table.',
    }


def analyze(payload):
    p = prepare(payload)
    rw = replicate_weights(p)
    result = {
        'status': 'paired_statistical_output_not_validation_pass',
        'sample_n': p['n'], 'population_N': p['N'], 'all_census': p['all_census'],
        'reference_generated': False, 'coders': copy.deepcopy(payload['coders']),
        'versions': {v: copy.deepcopy(payload[v + '_info']) for v in ('baseline', 'candidate')},
        'bootstrap': {'replicates': REPLICATES, 'seed': SEED,
                      'generator': 'numpy.random.PCG64', 'numpy_version': np.__version__,
                      'shared_weights_across_all_versions_dimensions_and_references': True,
                      'intervals': 'approximate marginal 95% percentile, not simultaneous',
                      'undefined_fraction_suppression_threshold': '>0.10'},
        'primary_differences': list(PRIMARY_DELTAS),
        'difference_sign': 'candidate minus baseline',
        'difference_scope': 'jointly definite baseline, candidate and specified reference only',
        'strata': [{'stratum': h, 'N_h': N, 'n_h': n, 'weight': N / n}
                   for h, N, n, _ in p['groups']],
        'comparisons': {}, 'paired_differences': {},
        'limitations': [
            'Caller must verify frozen sampling frame, true stratified SRSWOR and complete original submissions.',
            'Only the final finite candidate frame is covered, not the original full corpus or future policies.',
            'Both references are AI; sampling intervals omit shared model bias, coding error and unknown text exposure.',
            'Per-model PRF uses its own definite subset; paired deltas use the jointly definite subset and must retain joint coverage.',
            'No full-sample completion bounds for paired differences or kappa are claimed.',
            'Rare denominators can make approximate intervals unreliable even when few replicates are undefined.',
            'No passing threshold, consensus truth, imputation, selective metric substitution or corrected labels are generated.',
        ],
    }
    specifications = [('A_vs_C', 'A', 'C', False)]
    specifications += [(v + '_vs_' + c, v, c, True) for v in ('baseline', 'candidate') for c in ('A', 'C')]
    for name, left_key, right_key, classification in specifications:
        output = {'left': left_key, 'right': right_key, 'dimensions': {}}
        for j, dim in enumerate(DIMS):
            output['dimensions'][dim], _ = comparison(p, rw, p['labels'][left_key][:, j], p['labels'][right_key][:, j], classification)
        result['comparisons'][name] = output
    for coder in ('A', 'C'):
        output = {'reference': coder, 'dimensions': {}}
        for j, dim in enumerate(DIMS):
            left = p['labels']['baseline'][:, j]
            right = p['labels']['candidate'][:, j]
            ref = p['labels'][coder][:, j]
            joint = (left < 2) & (right < 2) & (ref < 2)
            # Keep excluded records in the 3x3 coverage table as pending on the
            # prediction side, retaining their actual reference status.
            old, old_replicates = comparison(p, rw, np.where(joint, left, 2), ref, True)
            new, new_replicates = comparison(p, rw, np.where(joint, right, 2), ref, True)
            deltas = {}
            for key in PRIMARY_DELTAS:
                a, b = old['estimates'][key], new['estimates'][key]
                point = None if a is None or b is None else b - a
                draws = [None if x[key] is None or y[key] is None else y[key] - x[key]
                         for x, y in zip(old_replicates, new_replicates)]
                deltas[key] = base.interval_summary(point, draws, p['all_census'])
            output['dimensions'][dim] = {
                'raw_jointly_definite_n': int(joint.sum()),
                'weighted_joint_coverage': float(p['weights'] @ joint / p['N']),
                'raw_baseline_only_assessable_n': int(((left < 2) & (ref < 2) & (right == 2)).sum()),
                'raw_candidate_only_assessable_n': int(((right < 2) & (ref < 2) & (left == 2)).sum()),
                'baseline_common_subset': common_subset_view(old),
                'candidate_common_subset': common_subset_view(new),
                'candidate_minus_baseline': deltas,
            }
        result['paired_differences'][coder] = output
    return result


def synthetic_payload():
    # Hand-computable example: baseline TP=1,FP=1,FN=1; candidate TP=2,FP=0,FN=0.
    triples = [(1, 1, 1), (0, 1, 1), (1, 0, 0), (0, 0, 0)]
    rows = []
    for i, (old, new, ref) in enumerate(triples):
        rows.append({'id': f'fiction-{i}', 'stratum': 'fiction', 'N_h': 8, 'n_h': 4,
                     'A': {d: ref for d in DIMS}, 'C': {d: ref for d in DIMS},
                     'baseline': {d: old for d in DIMS}, 'candidate': {d: new for d in DIMS}})
    return {'strata': [{'stratum': 'fiction', 'N_h': 8, 'n_h': 4}], 'population_N': 8,
            'rows': rows, 'coders': {c: {'kind': 'AI', 'description': 'synthetic QA only'} for c in ('A', 'C')},
            'baseline_info': {'version': 'synthetic-old', 'prediction_sha256': 'a' * 64},
            'candidate_info': {'version': 'synthetic-new', 'prediction_sha256': 'b' * 64}}


def self_test():
    fixture = synthetic_payload()
    out = analyze(fixture)
    d = out['paired_differences']['A']['dimensions']['I']
    assert d['candidate_minus_baseline']['recall_definite']['estimate'] == .5
    assert d['candidate_minus_baseline']['f1_definite']['estimate'] == .5
    shuffled = copy.deepcopy(fixture)
    shuffled['rows'].reverse()
    assert analyze(shuffled) == out, 'ID ordering must not change paired replicates'
    identical = copy.deepcopy(fixture)
    for row in identical['rows']:
        row['candidate'] = row['baseline'].copy()
    same = analyze(identical)['paired_differences']['A']['dimensions']['I']['candidate_minus_baseline']
    assert all(v['estimate'] == v['lower'] == v['upper'] == 0 for v in same.values())
    pending = copy.deepcopy(fixture)
    pending['rows'][1]['candidate']['I'] = base.PENDING
    delta = analyze(pending)['paired_differences']['A']['dimensions']['I']
    assert delta['raw_jointly_definite_n'] == 3 and delta['weighted_joint_coverage'] == .75
    assert delta['raw_baseline_only_assessable_n'] == 1
    assert delta['candidate_minus_baseline']['recall_definite']['estimate'] == 0
    assert abs(delta['candidate_minus_baseline']['f1_definite']['estimate'] - 1 / 3) < 1e-12
    for row in fixture['rows']:
        row['baseline']['I'] = row['candidate']['I'] = row['A']['I'] = row['C']['I'] = 0
    undefined = analyze(fixture)['paired_differences']['A']['dimensions']['I']['candidate_minus_baseline']
    assert all(v['estimate'] is None and v['lower'] is None and v['undefined_replicates'] == REPLICATES for v in undefined.values())
    bad = synthetic_payload()
    bad['rows'][0]['candidate']['I'] = True
    try:
        prepare(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('Boolean label accepted')
    print(json.dumps({'status': 'synthetic_only_checks_passed', 'real_labels_read': False,
                      'tests': ['hand_calculated_paired_gain', 'row_order_invariance', 'identical_version_zero_interval',
                                'changed_abstention_common_subset', 'undefined_kept_NA', 'boolean_rejection']}))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not args.self_test:
        parser.error('Planning stage: only synthetic self-test CLI enabled; no real-data evaluation')
    self_test()
