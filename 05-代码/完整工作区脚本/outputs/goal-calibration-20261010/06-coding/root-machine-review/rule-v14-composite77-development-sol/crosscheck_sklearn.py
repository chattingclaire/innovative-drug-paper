#!/usr/bin/env python3
"""One existing sklearn1.8.0 cross-calculation of the exact mixed77 rows."""
import hashlib
import json
import math
import sys
from pathlib import Path
import numpy as np
import sklearn
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix, f1_score, precision_score, recall_score

OUT = Path(__file__).resolve().parent
metrics = json.loads((OUT / 'metrics-exact.json').read_bytes())
rows = [json.loads(x) for x in (OUT / 'composite-predictions77.jsonl').read_text().splitlines()]
ref_path = Path(metrics['reference_file']['path'])
reference = {x['id']: x for x in [json.loads(x) for x in ref_path.read_text().splitlines()]}
assert sklearn.__version__ == '1.8.0' and len(rows) == 77


def num(x):
    return float(x) if math.isfinite(float(x)) else None


results = {}
for d in ['S', 'E', 'Ec', 'I', 'F']:
    pairs = [(reference[x['id']]['labels'][d], x['labels'][d]) for x in rows if x['labels'][d] is not None and reference[x['id']]['labels'][d] is not None]
    truth, pred = map(list, zip(*pairs))
    matrix = confusion_matrix(truth, pred, labels=[0, 1])
    tn, fp, fn, tp = map(int, matrix.ravel())
    counts = {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn}
    values = {'kappa': num(cohen_kappa_score(truth, pred, labels=[0, 1])), 'P': num(precision_score(truth, pred, zero_division=np.nan)), 'R': num(recall_score(truth, pred, zero_division=np.nan)), 'F1': num(f1_score(truth, pred, zero_division=np.nan)), 'Po': num(accuracy_score(truth, pred)), 'Ppos': num(f1_score(truth, pred, pos_label=1, zero_division=np.nan)), 'Pneg': num(f1_score(truth, pred, pos_label=0, zero_division=np.nan))}
    expected = metrics['full77_per_dimension'][d]
    checks = {k: v == expected[k] for k, v in counts.items()}
    for k, v in values.items():
        e = expected[k]['value']
        checks[k] = (v is None and e is None) or (v is not None and e is not None and abs(v - e) <= 1e-12)
    results[d] = {'paired_binary_n': len(pairs), 'matrix_row_reference_column_candidate_labels_0_1': matrix.tolist(), **counts, **values, 'matches_exact': checks}
report = {'scope': 'one mixed77 development cross-calculation only; not new inference, formal acceptance or human validation', 'python_executable': sys.executable, 'sklearn_version': sklearn.__version__, 'composite_sha256': hashlib.sha256((OUT / 'composite-predictions77.jsonl').read_bytes()).hexdigest(), 'reference_sha256': hashlib.sha256(ref_path.read_bytes()).hexdigest(), 'exact_metrics_sha256': hashlib.sha256((OUT / 'metrics-exact.json').read_bytes()).hexdigest(), 'per_dimension': results, 'all_match': all(all(x['matches_exact'].values()) for x in results.values()), 'tolerance_for_calculator_roundoff_only_not_acceptance_threshold': 1e-12, 'old_suites_or_fullframe_QA_executed': False}
with (OUT / 'sklearn-crosscheck.json').open('xb') as f:
    f.write((json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode())
print(json.dumps({'sklearn': sklearn.__version__, 'records': 77, 'all_match': report['all_match']}))
