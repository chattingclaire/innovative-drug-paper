"""Check compatibility of asking one binary method to match both fixed coders.

Exhaustively enumerate counts within the four A/C joint cells, never generate
or change any unit predictions. This is a bound on a metric requirement, not
an algorithm, an evaluation score, or a way to optimize annotations.
"""
import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

DIMS = ('S', 'E', 'Ec', 'I', 'F')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return {row['id']: row for row in map(json.loads, Path(path).read_text().splitlines())}


def kappa(tp, fp, fn, tn):
    n = tp + fp + fn + tn
    if not n:
        return None
    chance_numerator = (tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)
    denominator = n * n - chance_numerator
    if not denominator:
        return None
    return Fraction(n * (tp + tn) - chance_numerator, denominator)


def attainable_bound(cells):
    both, a_only, c_only, neither = cells
    n = sum(cells)
    if both + a_only in (0, n) and both + c_only in (0, n):
        return {'status': 'both_references_constant_numeric_kappa_target_not_identifiable',
                'best_minimum_kappa': None}
    best = None
    assignments = None
    evaluated = 0
    for p_both, p_a, p_c, p_neither in itertools.product(*(range(count + 1) for count in cells)):
        ka = kappa(p_both + p_a, p_c + p_neither,
                   both + a_only - p_both - p_a, c_only + neither - p_c - p_neither)
        kc = kappa(p_both + p_c, p_a + p_neither,
                   both + c_only - p_both - p_c, a_only + neither - p_a - p_neither)
        evaluated += 1
        if ka is None or kc is None:
            continue
        objective = min(ka, kc)
        if best is None or objective > best:
            best = objective
            assignments = {'positive_counts_in_AC_joint_cells': [p_both, p_a, p_c, p_neither],
                           'kappa_with_A': float(ka), 'kappa_with_C': float(kc)}
    return {'status': 'exhaustive_count_bound', 'enumerated_joint_cell_count_assignments': evaluated,
            'best_minimum_kappa': float(best) if best is not None else None,
            'exact_fraction': str(best) if best is not None else None,
            'both_can_reach_0_80': best >= Fraction(4, 5) if best is not None else None,
            'one_bound_witness_in_counts_only': assignments}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--a', type=Path, required=True)
    parser.add_argument('--c', type=Path, required=True)
    parser.add_argument('--design', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    a, c = load(args.a), load(args.c)
    design = json.loads(args.design.read_text())
    sample = {item['original_id']: item for item in design['sample']}
    records = []
    for group in ('ALL', 'NMPA', 'NHSA', 'NHC'):
        ids = [rid for rid, item in sample.items() if item['component'] == 'probability_canonical'
               and (group == 'ALL' or item['group'] == group)]
        for dim in DIMS:
            cells = [sum((a[rid]['labels'][dim], c[rid]['labels'][dim]) == values for rid in ids)
                     for values in ((1, 1), (1, 0), (0, 1), (0, 0))]
            assert sum(cells) == len(ids)
            observed = kappa(cells[0], cells[1], cells[2], cells[3])
            records.append({'group': group, 'dimension': dim, 'n': len(ids),
                            'AC_joint_cells_A1C1_A1C0_A0C1_A0C0': cells,
                            'A_C_kappa': float(observed) if observed is not None else None,
                            **attainable_bound(cells)})
    args.output.write_text(json.dumps({
        'purpose': 'Compatibility check of a numeric requirement with the fixed independent A/C judgments',
        'scope': 'unweighted probability sample only; not an optimization algorithm or a validation score',
        'annotations_changed': False, 'unit_predictions_authored': False,
        'interpretation': 'If the maximum attainable minimum kappa is below0.80, changing a classifier alone cannot reach0.80 with both coders on these fixed labels. Preserve first judgments; calibrate standards and evaluate a final reference separately.',
        'bindings': {str(p.resolve()): sha(p) for p in (args.a, args.c, args.design)},
        'records': records, 'script_sha256': sha(Path(__file__))}, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps([row for row in records if row['group'] == 'ALL'], ensure_ascii=False))


if __name__ == '__main__':
    main()
