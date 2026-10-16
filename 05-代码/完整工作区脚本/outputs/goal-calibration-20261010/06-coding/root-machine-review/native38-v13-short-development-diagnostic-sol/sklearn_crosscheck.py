#!/usr/bin/env python3
"""Independent vector/matrix calculation on the same 38 derived rows only."""
import hashlib
import json
import math
import sys
from pathlib import Path
import sklearn
import numpy as np
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix, f1_score, precision_score, recall_score

OUT = Path(__file__).resolve().parent
rows_path = OUT / 'derived-rows.jsonl'
rows = [json.loads(x) for x in rows_path.read_text().splitlines()]
primary = json.loads((OUT / 'metrics-exact.json').read_bytes())
assert sklearn.__version__ == '1.8.0' and len(rows) == 38


def number(v):
    return None if not math.isfinite(float(v)) else float(v)


results = {}
for dim in ['S', 'E', 'Ec', 'I', 'F']:
    pairs = [(r['reference_labels'][dim], r['candidate_labels'][dim]) for r in rows if r['reference_labels'][dim] is not None and r['candidate_labels'][dim] is not None]
    truth, prediction = map(list, zip(*pairs))
    matrix = confusion_matrix(truth, prediction, labels=[0, 1])
    tn, fp, fn, tp = [int(v) for v in matrix.ravel()]
    counts = {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn}
    values = {
        'kappa': number(cohen_kappa_score(truth, prediction, labels=[0, 1])),
        'P': number(precision_score(truth, prediction, pos_label=1, zero_division=np.nan)),
        'R': number(recall_score(truth, prediction, pos_label=1, zero_division=np.nan)),
        'F1': number(f1_score(truth, prediction, pos_label=1, zero_division=np.nan)),
        'Po': number(accuracy_score(truth, prediction)),
        'Ppos': number(f1_score(truth, prediction, pos_label=1, zero_division=np.nan)),
        'Pneg': number(f1_score(truth, prediction, pos_label=0, zero_division=np.nan)),
    }
    expected = primary['per_dimension'][dim]
    checks = {k: counts[k] == expected[k] for k in counts}
    for k, value in values.items():
        e = expected[k]['value']
        checks[k] = (value is None and e is None) or (value is not None and e is not None and abs(value - e) <= 1e-12)
    results[dim] = {'paired_binary_denominator': len(pairs), 'confusion_matrix_row_reference_column_candidate_labels_0_1': matrix.tolist(), **counts, **values, 'matches_exact_primary': checks}

report = {
    'scope': 'same38 historically exposed technical-success AI development diagnostic; no population CI or formal acceptance',
    'python_executable': sys.executable, 'sklearn_version': sklearn.__version__,
    'derived_rows_sha256': hashlib.sha256(rows_path.read_bytes()).hexdigest(),
    'primary_metrics_sha256': hashlib.sha256((OUT / 'metrics-exact.json').read_bytes()).hexdigest(),
    'per_dimension': results,
    'all_crosschecks_equal': all(all(x['matches_exact_primary'].values()) for x in results.values()),
    'comparison_tolerance_is_calculator_roundoff_only_not_acceptance_gate': 1e-12,
    'no_other_data_or_old_test_suite_executed': True,
}
with (OUT / 'sklearn-crosscheck.json').open('xb') as f:
    f.write((json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode())
print(json.dumps({'sklearn': sklearn.__version__, 'records': len(rows), 'all_crosschecks_equal': report['all_crosschecks_equal']}))
