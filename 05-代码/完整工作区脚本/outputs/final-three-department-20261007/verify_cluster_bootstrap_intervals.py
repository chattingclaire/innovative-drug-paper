"""Independent CI recalculation from raw labels, without production formulas.

Reconstructs all frame/group/metric cluster tables, reproduces the declared
multinomial cluster resampling and checks every percentile interval and every
undefined-replicate count. Does not change any coding or statistical choice.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
DIMS = ('S', 'E', 'Ec', 'I', 'F')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    result = {r['id']: r for r in rows}
    assert len(result) == len(rows)
    return result


def binary(v):
    return type(v) is int and v in (0, 1)


def divide(x, y):
    result = np.full(np.broadcast_shapes(np.shape(x), np.shape(y)), np.nan)
    np.divide(x, y, out=result, where=np.asarray(y) != 0)
    return result


def intervals_from_counts(counts):
    tp, fp, fn, tn = counts.T
    n = counts.sum(axis=1)
    expected_numerator = (tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)
    # Integer cross-products avoid using the production chance-rate formula.
    values = {
        'kappa': divide((tp + tn) * n - expected_numerator, n * n - expected_numerator),
        'agreement': divide(tp + tn, n),
        'precision': divide(tp, tp + fp),
        'recall': divide(tp, tp + fn),
        'f1': divide(2 * tp, 2 * tp + fp + fn),
        'left_positive_rate': divide(tp + fp, n),
        'right_positive_rate': divide(tp + fn, n),
    }
    result = {}
    for metric, array in values.items():
        valid = array[np.isfinite(array)]
        result[metric] = {
            'low': float(np.quantile(valid, .025)) if len(valid) else None,
            'high': float(np.quantile(valid, .975)) if len(valid) else None,
            'defined_repetitions': len(valid),
            'undefined_repetitions': len(array) - len(valid),
        }
    return result


def main():
    target = OUT / '三部门编码指标.json'
    binding = sha(target)
    result = json.loads(target.read_text())
    assert result['bootstrap']['repetitions'] == 5000
    assert result['bootstrap']['base_seed'] == 20261007
    inputs = read_rows(result['method_bindings']['rule']['inputs'])
    metadata = {Path(r['original_file']).stem: r['analysis_group']
                for r in json.loads(Path(result['method_bindings']['metadata']).read_text())['rows']}
    predictions = {
        result['method_bindings']['rule']['method']: {
            rid: row['prediction']['labels']
            for rid, row in read_rows(result['method_bindings']['rule']['rules']).items()}
    }
    if result['method_bindings']['llm']['path']:
        predictions[result['method_bindings']['llm']['method']] = {
            rid: row.get('prediction', row)['labels']
            for rid, row in read_rows(result['method_bindings']['llm']['path']).items()}
    main_refs = read_rows(result['method_bindings']['references'])
    frames = {'main1057': {
        rid: {c: r['original_references'][c]['labels'] for c in ('A', 'C')}
        for rid, r in main_refs.items()}}
    h = ROOT / 'outputs/autocode-v25-20260927/H427'
    mapping = json.loads((h / 'admin_mapping.json').read_text())
    coder = {c: {} for c in ('A', 'C')}
    for c in coder:
        for file in sorted((h / f'agent-{c}').glob('结果-*.json')):
            for row in json.loads(file.read_text())['rows']:
                assert row['id'] not in coder[c]
                coder[c][row['id']] = row['labels']
    frames['supplement_H411'] = {
        m['rerun_id']: {c: coder[c][m['id']] for c in coder} for m in mapping}
    selected = {}
    for frame, refs in frames.items():
        for group in ('ALL', 'NMPA', 'NHSA', 'NHC'):
            ids = [rid for rid in refs
                   if metadata[inputs[rid]['input']['original_file_stem']] in result['scope']
                   and (group == 'ALL' or metadata[inputs[rid]['input']['original_file_stem']] == group)]
            selected[frame, group] = ids
    interval_checks = 0
    field_checks = 0
    counts_by_frame = Counter()
    for record in result['records']:
        frame, group = record['frame'], record['group']
        cluster = defaultdict(lambda: [0, 0, 0, 0])
        for rid in selected[frame, group]:
            unit = inputs[rid]['input']
            source = unit.get('unit_source') or unit['source']
            cell = cluster[source]  # Include zero-pair files in the sampling frame.
            left = frames[frame][rid]['A'][record['dimension']] if record['method'] == 'A_C' else predictions[record['method']][rid][record['dimension']]
            right = frames[frame][rid][record['reference']][record['dimension']]
            if binary(left) and binary(right):
                cell[{(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[left, right]] += 1
        matrix = np.array([cluster[key] for key in sorted(cluster)], dtype=np.int64)
        assert len(matrix) == record['source_clusters']
        assert matrix.sum() == record['n']
        expected_seed = 20261007 + int(hashlib.sha256(f'{frame}/{group}'.encode()).hexdigest()[:8], 16)
        assert expected_seed == record['bootstrap_seed']
        weights = np.random.default_rng(expected_seed).multinomial(
            len(matrix), np.full(len(matrix), 1 / len(matrix)), size=5000)
        actual = intervals_from_counts(weights @ matrix)
        for metric, values in record['metrics'].items():
            expected = values['ci95']
            for name, wanted in expected.items():
                got = actual[metric][name]
                if wanted is None:
                    assert got is None
                elif name.endswith('repetitions'):
                    assert got == wanted
                else:
                    assert got is not None and abs(got - wanted) < 1e-12, (frame, group, record['dimension'], record['method'], metric, name, got, wanted)
                field_checks += 1
            interval_checks += 1
        counts_by_frame[frame] += 1
    assert sha(target) == binding
    report = {
        'status': 'passed', 'target': str(target.resolve()), 'target_sha256': binding,
        'comparison_records': len(result['records']),
        'intervals_independently_recomputed': interval_checks,
        'interval_fields_checked': field_checks,
        'records_by_frame': dict(counts_by_frame),
        'checks': ['Raw original label reconstruction', 'All observed source files retained, including zero-pair clusters',
                   'Declared frame/group seed', '5000 cluster resamples',
                   'Independent integer cross-product kappa formula',
                   'Each lower/upper percentile and defined/undefined-replicate count'],
        'new_statistical_choices': False,
    }
    (OUT / '聚类区间独立重算核验.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
