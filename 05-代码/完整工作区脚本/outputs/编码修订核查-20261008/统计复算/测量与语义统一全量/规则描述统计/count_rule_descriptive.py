"""Describe the specified new rule output; never invokes a coder/model.

Null labels remain unknown. The missing source-gap unit remains in the target
frame. Partial rows retain their available labels only for cell-wise summaries
and bounds; the common-population conditional q uses fully determined rows.
"""
import hashlib
import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[2]
DIMS = ['S', 'E', 'Ec', 'I', 'F']
PATHS = {
    'result': HERE.parent / '规则全量输出4480.jsonl',
    'input': HERE.parent / '规则输入4480.jsonl',
    'frame': W / '人工参照复核/全量目标框验证准备01/source_only_frame_all4481.jsonl'
}
LOCKS = {
    'result': 'a15f974a30cbe3d95ff339c88a63c786cdd84fae43a4e8a530509318d7a0cc8e',
    'input': '0a0704613e29ca81bc35c25bcdab8c36f5b2367250562d2f5f80a73f0e71fe2d',
    'frame': '301f05240c8ada00129ed8f84bc68e5047118cdedef9777937f01d49cad17c29'
}
MANUAL_SHA = '24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(role):
    data = PATHS[role].read_bytes()
    assert sha(data) == LOCKS[role], f'{role} changed from the specified new-file lock'
    rows = [json.loads(line) for line in data.decode('utf-8').splitlines() if line.strip()]
    assert len({r['id'] for r in rows}) == len(rows), f'{role}: duplicate IDs'
    return data, rows

def ratio(n, d):
    return {'numerator': n, 'denominator': d,
            'fraction': str(Fraction(n, d)) if d else None,
            'value': n / d if d else None,
            'percent': 100 * n / d if d else None}

def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def shape(rows):
    return dict(Counter('|'.join(sorted(r.keys())) for r in rows))

def summarize(records):
    n = len(records)
    complete = [r for r in records if all(type(r['labels'][d]) is int for d in DIMS)]
    partial = [r for r in records if 0 < sum(r['labels'][d] is not None for d in DIMS) < 5]
    all_unknown = [r for r in records if all(r['labels'][d] is None for d in DIMS)]
    c = {d: sum(r['labels'][d] for r in complete) for d in DIMS}
    b = sum(c.values())
    a = {d: sum(r['labels'][d] for r in records if r['labels'][d] is not None) for d in DIMS}
    u = {d: sum(r['labels'][d] is None for r in records) for d in DIMS}
    observed_total = sum(a.values())
    unknown_cells = sum(u.values())
    dimensions = {}
    for d in DIMS:
        known_n = n - u[d]
        lower_q = ratio(a[d], observed_total + unknown_cells - u[d])
        upper_q = ratio(a[d] + u[d], observed_total + u[d])
        dimensions[d] = {
            'fully_determined_units_positive_n': c[d],
            'q_conditional_on_fully_determined_units': ratio(c[d], b),
            'unit_positive_rate_conditional_on_fully_determined_units': ratio(c[d], len(complete)),
            'available_cell_positive_n': a[d], 'available_cell_zero_n': known_n - a[d],
            'dimension_determined_unit_n': known_n, 'dimension_unknown_unit_n': u[d],
            'unit_positive_rate_conditional_on_this_dimension_determined': ratio(a[d], known_n),
            'full_target_unit_positive_rate_bounds': {
                'lower': ratio(a[d], n), 'upper': ratio(a[d] + u[d], n)
            },
            'full_target_relative_attention_q_bounds': {'lower': lower_q, 'upper': upper_q}
        }
        assert a[d] <= known_n and c[d] <= a[d]
        if lower_q['value'] is not None:
            assert 0 <= lower_q['value'] <= upper_q['value'] <= 1
    if b:
        assert sum(Fraction(c[d], b) for d in DIMS) == 1
    assert len(complete) + len(partial) + len(all_unknown) == n
    return {
        'target_unit_n': n, 'fully_determined_unit_n': len(complete),
        'partially_determined_unit_n': len(partial), 'all_five_unknown_unit_n': len(all_unknown),
        'any_unknown_unit_n': len(partial) + len(all_unknown),
        'conditional_q_denominator_positive_label_occurrences': b,
        'available_cell_positive_label_occurrences': observed_total,
        'unknown_label_cell_n': unknown_cells,
        'fully_determined_all_zero_unit_n': sum(all(r['labels'][d] == 0 for d in DIMS) for r in complete),
        'dimensions': dimensions
    }

def main():
    result_bytes, results = load('result')
    input_bytes, inputs = load('input')
    frame_bytes, frame = load('frame')
    assert len(results) == len(inputs) == 4480 and len(frame) == 4481
    assert shape(results) == {'id|result|status': 4480}
    result_by_id = {r['id']: r for r in results}
    frame_by_id = {r['id']: r for r in frame}
    assert [r['id'] for r in results] == [r['id'] for r in inputs]
    assert set(result_by_id) <= set(frame_by_id)
    missing = sorted(set(frame_by_id) - set(result_by_id))
    assert missing == ['RECODE25-00064']
    groups = Counter(r['analysis_group'] for r in frame)
    assert set(groups) == {'NMPA', 'NHSA', 'NHC'} and sorted(groups.values()) == [533, 1848, 2100]
    department_names = {}
    for row in frame:
        group = row['analysis_group']
        if group in department_names:
            assert department_names[group] == row['department_name']
        department_names[group] = row['department_name']
    for inp, out in zip(inputs, results):
        rid = inp['id']
        f = frame_by_id[rid]
        current_sha = sha(inp['input']['unit_text'].encode('utf-8'))
        assert current_sha == f['unit_text_sha256'] == out['result']['unit_text_sha256'], f'{rid}: text identity mismatch'
        assert inp['original_id'] == f['original_id']
        assert out['status'] == 'completed'
        prediction = out['result']
        assert prediction['current_manual_sha256'] == MANUAL_SHA
        assert set(prediction['labels']) == set(DIMS)
        assert all(v is None or (type(v) is int and v in (0, 1)) for v in prediction['labels'].values())
        has_unknown = any(v is None for v in prediction['labels'].values())
        assert (prediction['judgement_status'] == 'undetermined') == has_unknown
        assert prediction['judgement_status'] in {'rule_prediction', 'undetermined'}
    undetermined = [r for r in results if r['result']['judgement_status'] == 'undetermined']
    assert len(undetermined) == 21
    label_type_patterns = Counter('|'.join(type(r['result']['labels'][d]).__name__ for d in DIMS) for r in results)
    shape_qa = {
        'status': 'shape_and_identity_checked_before_counting', 'all_checks_pass': True,
        'source_files': {role: {'path': str(PATHS[role]), 'sha256': LOCKS[role], 'bytes': len(data)}
                         for role, data in [('result', result_bytes), ('input', input_bytes), ('frame', frame_bytes)]},
        'result_n': len(results), 'input_n': len(inputs), 'frame_n': len(frame),
        'result_shape_counts': shape(results), 'input_shape_counts': shape(inputs), 'frame_shape_counts': shape(frame),
        'outer_status_counts': dict(Counter(r['status'] for r in results)),
        'judgement_status_counts': dict(Counter(r['result']['judgement_status'] for r in results)),
        'input_assessment_status_counts': dict(Counter(r['result']['input_assessment_status'] for r in results)),
        'label_type_patterns_S_E_Ec_I_F': dict(label_type_patterns),
        'missing_from_output_and_input_but_retained_unknown_in_target': missing,
        'target_department_counts': dict(groups), 'department_names': department_names,
        'result_input_id_order_equal': True, 'all_current_text_sha_match_frame_input_output': True,
        'all_current_manual_sha_match': True, 'manual_sha256': MANUAL_SHA,
        'classification_correctness_verified': False
    }
    write('输出形状与身份核查.json', shape_qa)
    records = []
    unknown_ledger = []
    for f in frame:
        rid = f['id']
        if rid in result_by_id:
            raw = result_by_id[rid]['result']
            labels = dict(raw['labels'])
            reason = raw['input_assessment_status']
        else:
            labels = {d: None for d in DIMS}
            reason = 'explicitly_retained_source_gap_00064_missing_from_execution_input'
        rec = {'id': rid, 'group': f['analysis_group'], 'labels': labels}
        records.append(rec)
        unknown_dims = [d for d in DIMS if labels[d] is None]
        if unknown_dims:
            unknown_ledger.append({'id': rid, 'group': f['analysis_group'],
                                   'unknown_dimensions': unknown_dims, 'known_labels_retained': {d: labels[d] for d in DIMS if labels[d] is not None},
                                   'provenance': reason, 'present_in_rule_output': rid in result_by_id})
    assert len(unknown_ledger) == 22
    report = {
        'status': 'new_rule_output_descriptive_diagnostic_not_final_results',
        'sources': shape_qa['source_files'], 'manual_sha256': MANUAL_SHA,
        'python_executable': sys.executable, 'script_sha256': sha(Path(__file__).read_bytes()),
        'definitions': {
            'counts': 'Each fixed original target-frame record is retained; each known dimension 1 is counted once. Multiple dimensions can be 1. No family collapse or weighting.',
            'fully_determined_conditional_q': 'c_d / B; c_d counts positives only among units with all five binary labels; B=sum_j c_j. It is a conditional composition, not a full-frame estimate under a missing-at-random assumption.',
            'dimension_conditional_rate': 'a_d / (N-u_d); uses all available binary cells for that dimension. Different dimensions can have different observed unit populations; these rates are not a common-denominator q.',
            'full_target_unit_positive_rate_bounds': '[a_d/N, (a_d+u_d)/N]',
            'full_target_q_bounds': '[a_d/(A+sum_{j != d}u_j), (a_d+u_d)/(A+u_d)]; A=sum_j a_j. For the lower endpoint set unknown d cells to0 and all other unknown cells to1; for the upper endpoint do the reverse. This varies hypothetical completions only in the bound calculation, never changes stored labels.',
            'bounds_interpretation': 'Logical bounds allowing independent binary completion of unknown cells; endpoints for different dimensions need not be jointly achievable. Not confidence intervals and not a semantic validation.',
            'unknown_policy': 'Null is never treated as zero.00064 contributes five unknown cells; the21 undetermined output rows retain their remaining known cells. Other review flags are not newly adjudicated here.'
        },
        'departments': {g: {'department_name': department_names[g], **summarize([r for r in records if r['group'] == g])}
                        for g in ['NMPA', 'NHSA', 'NHC']},
        'all_three_departments': summarize(records), 'unknown_unit_ledger': unknown_ledger,
        'actions': {'coder_or_model_invoked': False, 'old_predictions_read': False,
                    'source_inputs_outputs_or_frame_modified': False, 'paper_written': False,
                    'semantic_review_performed': False}
    }
    assert all(sha(PATHS[role].read_bytes()) == LOCKS[role] for role in PATHS)
    write('规则描述统计.json', report)
    print(json.dumps({'status': report['status'], 'target_department_counts': dict(groups),
                      'departments': {g: {'N': v['target_unit_n'], 'fully_determined': v['fully_determined_unit_n'],
                                         'any_unknown': v['any_unknown_unit_n'], 'q_denominator': v['conditional_q_denominator_positive_label_occurrences'],
                                         'count': {d: v['dimensions'][d]['fully_determined_units_positive_n'] for d in DIMS},
                                         'q_percent': {d: v['dimensions'][d]['q_conditional_on_fully_determined_units']['percent'] for d in DIMS},
                                         'unknown_by_dimension': {d: v['dimensions'][d]['dimension_unknown_unit_n'] for d in DIMS},
                                         'q_bounds_percent': {d: [v['dimensions'][d]['full_target_relative_attention_q_bounds'][k]['percent'] for k in ['lower', 'upper']] for d in DIMS}}
                                      for g, v in report['departments'].items()},
                      'all_target_any_unknown': report['all_three_departments']['any_unknown_unit_n'],
                      'report_sha256': sha((HERE/'规则描述统计.json').read_bytes()),
                      'shape_qa_sha256': sha((HERE/'输出形状与身份核查.json').read_bytes())}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
