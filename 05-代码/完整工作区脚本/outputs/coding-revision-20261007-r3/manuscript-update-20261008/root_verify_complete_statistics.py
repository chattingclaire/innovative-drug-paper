"""Read-only root audit of the closed v36.2 statistical bundle."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATS = HERE.parent / 'methods-20261008/rules-v36.2-development-complete-statistics'


def load(name):
    return json.loads((STATS / name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    frozen = load('output_freeze.json')
    hashes = {n: digest(STATS / n) == h for n, h in frozen['files'].items()}
    assert all(hashes.values())
    qa = load('complete_statistics_QA.json')
    assert qa['all_checks_pass']
    assert qa['exact_point_crosschecks']['pass']
    assert qa['machine_comparisons'] == 180 and qa['A_C_comparisons'] == 60
    assert qa['interval_audit']['checked_interval_n'] == 3540
    machine = load('machine_reference_classification.json')['comparisons']
    ac = load('A_C_before_third_agreement.json')['comparisons']
    attn = load('probability_attention_and_paired_department_differences.json')
    assert len(machine) == 180 and len(ac) == 60
    assert (len(attn['profiles']), len(attn['paired_method_differences']),
            len(attn['department_differences'])) == (32, 32, 12)

    intervals = []

    def walk(obj, path=''):
        if isinstance(obj, dict):
            if {'low', 'high', 'defined_repetitions', 'undefined_repetitions'} <= set(obj):
                a, b = obj['low'], obj['high']
                n, u = obj['defined_repetitions'], obj['undefined_repetitions']
                assert n + u in (0, 5000), path
                assert (a is None) == (b is None), path
                assert a is None or a <= b, path
                assert (a is None) == (n == 0), path
                intervals.append((path, a, b, n, u))
            else:
                for k, v in obj.items():
                    walk(v, path + '/' + k)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                walk(value, path + '/' + str(i))

    walk(machine, '/machine')
    walk(ac, '/AC')
    walk(attn['profiles'], '/attention_profiles')
    walk(attn['paired_method_differences'], '/paired_attention')
    walk(attn['department_differences'], '/department_attention')
    assert len(intervals) == 3540, len(intervals)
    primary = [r for r in machine if r['component'] == 'probability_canonical'
               and r['group'] == 'ALL' and r['weighting'] == 'eligible_design_weighted']
    assert len(primary) == 15
    selected = [{
        'reference': r['reference'], 'dimension': r['dimension'],
        'raw_confusion': r['raw_confusion'],
        'metrics': {key: {'estimate': r['metrics'][key]['estimate'],
                         'ci95_primary': r['metrics'][key]['ci95_primary']}
                    for key in ('kappa', 'precision', 'recall', 'f1')}
    } for r in primary]
    result = {
        'status': 'passed_read_only_root_bundle_audit',
        'date': '2026-10-08',
        'statistical_bundle': str(STATS),
        'output_freeze_sha256': digest(STATS / 'output_freeze.json'),
        'sealed_file_checks': hashes,
        'comparison_counts': {'machine': 180, 'A_C': 60, 'attention_profiles': 32,
                              'paired_attention': 32, 'department_attention': 12},
        'independent_exact_point_crosschecks': qa['exact_point_crosschecks'],
        'interval_checks': {
            'n': len(intervals),
            'wholly_undefined': sum(n == 0 and u == 5000 for _, a, b, n, u in intervals),
            'not_attempted_absent_stratum': sum(n + u == 0 for _, a, b, n, u in intervals),
            'partly_undefined': sum(n > 0 and u > 0 for _, a, b, n, u in intervals),
            'defined_degenerate': sum(n > 0 and a == b for _, a, b, n, u in intervals),
            'interpretation': 'Intervals condition on fixed labels and algorithms. '
                              'Perfect or census intervals do not establish semantic validity.'},
        'primary180_design_weighted': selected,
        'scope': 'v36.2 post-exposure development only; no new human validation, '
                 'no claim all point metrics or interval bounds exceed .80',
        'inputs_or_labels_modified': False,
    }
    (HERE / '规则v36.2完整统计根复核.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'comparison_counts',
                                          'interval_checks')}, ensure_ascii=False))


if __name__ == '__main__':
    audit()
