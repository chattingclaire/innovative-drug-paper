"""Independent count/metric cross-check and immutable diagnostic checkpoint.

No classification, source mutation, reference mutation or manuscript editing.
"""
from pathlib import Path
import argparse, hashlib, json, math
from collections import Counter

HERE = Path(__file__).resolve().parent
DIMS = ('S', 'E', 'Ec', 'I', 'F')
NAMES = dict(zip(DIMS, ('安全性', '有效性', '经济性', '创新性', '公平性')))

def read(p):
    return json.loads(Path(p).read_text())

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, value):
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--checks', type=Path, required=True)
    args = parser.parse_args()
    r = read(args.run / 'report.json')
    pred = read(args.run / 'candidate-predictions.json')
    prev = read(args.previous / 'candidate-predictions.json')
    human = {x['unit_id']: {d: x['judgments'][d]['value'] for d in DIMS}
             for x in read(r['inputs']['reference200']['path'])['records']}
    checks = read(args.checks)
    assert checks['all_passed'] and r['baseline_reproduction_passed']
    for name, binding in r['code'].items():
        assert digest(binding['path']) == binding['sha256'] == checks['code_sha256'][name + '.py']
    for key in ('semantic_units', 'old_predictions', 'reference200', 'sample_draw', 'guard_cases', 'script'):
        binding = r['inputs'][key]
        assert digest(binding['path']) == binding['sha256']
    if r['input_enrichment']['applied']:
        binding = r['input_enrichment']['overrides_binding']
        assert digest(binding['path']) == binding['sha256']
    if r.get('parent_input_control'):
        binding = r['parent_input_control']['input_binding']
        assert digest(binding['path']) == binding['sha256']
    assert all(x['passed'] for x in r['generalization_guards'])
    changes, remaining, rows = [], [], []
    total = Counter()
    for d in DIMS:
        pairs = Counter()
        pending, errors = [], []
        for rid, h in human.items():
            row = pred[rid]
            a, b, target = prev[rid]['labels'][d], row['labels'][d], h[d]
            if row['implementation_error']:
                errors.append(rid); total['technical_errors'] += 1
            elif b is None:
                pending.append(rid); total['pending'] += 1
            else:
                pairs[(target, b)] += 1
                total['agreed' if target == b else 'disagreed'] += 1
            if a != b:
                status = ('pending_to_binary' if a is None and b is not None else
                          'binary_to_pending' if a is not None and b is None else
                          'corrected' if b == target else 'new_disagreement' if a == target else 'changed_disagreement')
                changes.append({'id': rid, 'dimension': d, 'previous': a, 'candidate': b,
                                'reference': target, 'status': status, 'agrees_now': b == target})
            if b != target or row['implementation_error']:
                remaining.append({'id': rid, 'dimension': d, 'candidate': b, 'human_reference': target,
                                  'status': 'technical_error' if row['implementation_error'] else 'pending' if b is None else 'disagreement',
                                  'decision': row['decisions'][d] if row['decisions'] else None})
        tp, fn, fp, tn = [pairs[k] for k in [(1,1), (1,0), (0,1), (0,0)]]
        n = sum(pairs.values())
        po = (tp + tn) / n
        pe = ((tp + fn) / n) * ((tp + fp) / n) + ((tn + fp) / n) * ((tn + fn) / n)
        computed = {'agreement': po, 'kappa': (po-pe)/(1-pe),
                    'precision': tp/(tp+fp) if tp+fp else None,
                    'recall': tp/(tp+fn) if tp+fn else None,
                    'F1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
        saved = next(x for x in r['candidate_metrics']['200'] if x['dimension'] == d)
        assert saved['TP_FP_FN_TN'] == [tp, fp, fn, tn]
        assert saved['binary_N'] == n and set(saved['NULL_ids']) == set(pending) and not errors
        for key, value in computed.items():
            assert (value is None and saved['raw_metrics'][key] is None) or math.isclose(value, saved['raw_metrics'][key], abs_tol=1e-12)
        rows.append({'dimension': d, 'binary_N': n, 'pending_N': len(pending),
                     'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn, **computed})
    assert sum(total.values()) == 1000
    assert all(x['binary_N'] == 77 and x['raw_metrics']['agreement'] == 1 for x in r['candidate_metrics']['77'])
    assert not any(x['status'] == 'new_reference_disagreement' for x in r['changes'])
    save(HERE / '指标独立复算.json', {'input': str(args.run.resolve()), 'counts': dict(total),
                                  'metrics_verified_from_predictions_and_reference': rows,
                                  'candidate_independent_validation': False})
    save(HERE / '相对上一轮变化.json', {'counts': dict(Counter(x['status'] for x in changes)), 'items': changes})
    save(HERE / '剩余分歧与待定.json', {'purpose': 'development diagnostic; unchanged human reference', 'items': remaining})
    seal = {'status': 'machine_development_checkpoint', 'candidate_independent_validation': False,
            'run': str(args.run.resolve()), 'code': r['code'], 'inputs': r['inputs'],
            'input_enrichment': {k:v for k,v in r['input_enrichment'].items() if k != 'same_code_input_effect_changes'},
            'parent_input_control': {k:v for k,v in (r.get('parent_input_control') or {}).items() if k != 'same_code_incremental_input_changes'},
            'counts': dict(total), 'metrics_independently_recomputed': True,
            'calibration77_all_agree': True, 'checks': {'path':str(args.checks.resolve()), 'sha256':digest(args.checks)},
            'no_full4481_rerun': True, 'no_LLM_calls': True, 'no_human_label_edits': True,
            'no_manuscript_edits': True}
    save(HERE / '完成核验.json', seal)
    print(json.dumps({'counts':dict(total), 'changes':dict(Counter(x['status'] for x in changes)),
                      'metrics_verified': True}, ensure_ascii=False))

if __name__ == '__main__':
    main()
