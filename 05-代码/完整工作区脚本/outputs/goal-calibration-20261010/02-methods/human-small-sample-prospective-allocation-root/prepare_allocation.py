"""Compare smaller human workloads from frozen stratum metadata only.

Does not draw members, read predictions or human answers, or issue workbooks.
"""
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / '05-validation/full800-common-v15-prerelease-sol/coordinator-private/draw-contract.json'
CONTRACT = ROOT / '02-methods/prospective-statistical-contract-v2/validation-design-v2.json'


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def compare(strata, total):
    allocated = {s['stratum']: min(2, s['N_h']) for s in strata}
    budgets = {'remaining': total * 3 // 5, 'exposed': total * 2 // 5}
    for domain, budget in budgets.items():
        domain_strata = sorted((s for s in strata if s['domain'] == domain), key=lambda s: s['stratum'])
        if sum(allocated[s['stratum']] for s in domain_strata) > budget:
            raise ValueError('Budget smaller than the pre-answer stratum baseline')
        while sum(allocated[s['stratum']] for s in domain_strata) < budget:
            eligible = [s for s in domain_strata if allocated[s['stratum']] < s['n_h']]
            if not eligible:
                raise ValueError('Budget exceeds existing probability-draw capacity')
            winner = eligible[0]
            for candidate in eligible[1:]:
                if Fraction(candidate['N_h'], allocated[candidate['stratum']] + 1) > Fraction(winner['N_h'], allocated[winner['stratum']] + 1):
                    winner = candidate
            allocated[winner['stratum']] += 1
    rows = []
    by_department = defaultdict(int)
    by_domain = defaultdict(int)
    weight_square_sum = Fraction(0)
    for s in sorted(strata, key=lambda s: s['stratum']):
        n = allocated[s['stratum']]
        N = s['N_h']
        old_n = s['n_h']
        if not (1 <= n <= old_n <= N) or (n < 2 and n != N):
            raise ValueError('Invalid allocation or non-census singleton')
        by_department[s['department']] += n
        by_domain[s['domain']] += n
        weight_square_sum += Fraction(N * N, n)
        rows.append({'stratum': s['stratum'], 'domain': s['domain'], 'department': s['department'],
                     'N_h': N, 'old_n_h': old_n, 'new_n_h': n,
                     'original_pi_exact': str(Fraction(old_n, N)),
                     'conditional_new_pi_exact': str(Fraction(n, old_n)),
                     'overall_pi_exact': str(Fraction(n, N)),
                     'overall_weight_exact': str(Fraction(N, n)),
                     'same_stratum_joint_pi_exact': str(Fraction(n * (n - 1), N * (N - 1))) if N > 1 else None})
    if sum(allocated.values()) != total or dict(by_domain) != budgets:
        raise ValueError('Allocation totals mismatch')
    return {'proposed_records_per_coder': total, 'dimension_decisions_per_coder': total * 5,
            'two_coders_total_dimension_decisions': total * 10,
            'by_domain': dict(by_domain), 'by_department': dict(by_department),
            'stratum_N': len(rows), 'strata': rows,
            'kish_weight_only_effective_N': float(Fraction(4481 ** 2, 1) / weight_square_sum),
            'kish_interpretation': 'Unequal-weight dispersion diagnostic only; not kappa precision, power, observed accuracy, or proof of adequate rare-positive counts.'}


def main():
    d = json.loads(SOURCE.read_text())
    strata = d['selected_strata']
    if len(strata) != 41 or sum(s['N_h'] for s in strata) != 4481 or sum(s['n_h'] for s in strata) != 800:
        raise ValueError('Frozen stratum inventory mismatch')
    # Selected IDs are intentionally not used: there is no new member draw here.
    result = {
        'artifact_type': 'prospective_human_workload_allocation_comparison',
        'at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'metadata_only_preparation_not_an_issued_human_assignment',
        'inputs': [binding(SOURCE), binding(CONTRACT), binding(Path(__file__))],
        'budget_question_answer_received': False,
        'working_budget_assumption': '200 records per coder is a reversible workload candidate, not a user-confirmed upper limit or a methodological minimum.',
        'algorithm': 'Fix remaining/exposed budgets at 60/40. Give each stratum min(2,N_h), then repeatedly maximize exact N_h/(n_h+1); ties use ascending stratum name. Cap n_h at the existing800 draw count. All priority factors are one.',
        'allocation_is_precision_optimal_or_sufficient': False,
        'candidates': [compare(strata, 200), compare(strata, 300)],
        'new_members_drawn': 0,
        'human_workbooks_created': 0,
        'human_assignments_issued': 0,
        'new_human_results_read': 0,
        'machine_predictions_read_for_this_preparation': 0,
        'scientific_boundaries': [
            'Auxiliary strata were frozen before current human answers. Their labels are not human truth and do not guarantee five-dimension positive or negative support.',
            'A subsequent independent uniform subset of each existing random stratum sample, with fixed n_h before answers, has unconditional stratum-SRS inclusion probability n_h/N_h. The overall weight must be recomputed as N_h/n_h; do not reuse the800 weights.',
            'The proposed200 candidate has120 remaining-domain records for independent validation and80 exposed-domain records for a separate fixed-corpus audit. Exposed records cannot be described as unseen generalization material.',
            'This establishes a potential probability design for4481, not a guarantee that actual labels, lawful NULL coverage, or intervals will support all acceptance claims.',
            'Retain the five-dimensional project thresholds and the prespecified design-based interval method. An undefined or sparsely supported metric cannot be declared passed.',
            'No label-dependent sample selection, favorable-output retries, or retrospective confidence interval selection. A future redesign after inspecting answers needs its own inferential justification.',
            'The existing800 blank packs and machine-stability800 plan remain intact;800 is not a mandatory human workload.'
        ],
        'primary_sources': [
            {'title': 'Statistics Canada: Probability sampling', 'url': 'https://www150.statcan.gc.ca/n1/edu/power-pouvoir/ch13/prob/5214899-eng.htm', 'use': 'Known inclusion probabilities, pre-sampling strata, independent within-stratum random samples; sample design balances cost and estimation goals.'},
            {'title': 'Grimmer and Stewart2013: Text as Data', 'url': 'https://web.stanford.edu/~jgrimmer/tad2.pdf', 'use': 'Separate hand-coded validation from iterative coding development; the illustrative300 sample is not a universal minimum.'}
        ]
    }
    with (OUT / 'allocation-comparison.json').open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: result[k] for k in ['status', 'new_members_drawn', 'human_assignments_issued']}, ensure_ascii=False))
    for candidate in result['candidates']:
        print(json.dumps({k: candidate[k] for k in ['proposed_records_per_coder', 'by_domain', 'by_department', 'kish_weight_only_effective_N']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
