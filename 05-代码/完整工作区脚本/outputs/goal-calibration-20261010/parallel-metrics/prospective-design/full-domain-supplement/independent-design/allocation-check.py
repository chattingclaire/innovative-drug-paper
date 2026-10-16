"""Deterministic aggregate quota check; no text, gold labels or ID samples.

Only reads the frozen metadata projection and prior small-plan aggregate file.
All outputs, when run, are confined to this independent-design directory.
"""
from collections import Counter
from fractions import Fraction
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent.parent
MULTIPLIERS = {
    'I_disagreement': 6,
    'F_disagreement': 5,
    'other_disagreement': 3,
    'IF_positive_agreement': 3,
    'other_positive_agreement': 2,
    'all_negative_agreement': 1,
}
DEPARTMENTS = ['NMPA', 'NHSA', 'NHC']
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def priority_tag(row):
    a, b = row['rules39'], row['LLM03']
    if a['I'] != b['I']:
        return 'I_disagreement'
    if a['F'] != b['F']:
        return 'F_disagreement'
    if any(a[d] != b[d] for d in ['S', 'E', 'Ec']):
        return 'other_disagreement'
    if any(a[d] or b[d] for d in ['I', 'F']):
        return 'IF_positive_agreement'
    if any(a[d] or b[d] for d in ['S', 'E', 'Ec']):
        return 'other_positive_agreement'
    return 'all_negative_agreement'


def allocate(strata, budget):
    ns = {h['key']: min(2, h['N']) for h in strata}
    if not sum(ns.values()) <= budget <= sum(h['N'] for h in strata):
        raise ValueError('Budget must fit minimum coverage and finite capacity')
    while sum(ns.values()) < budget:
        candidates = [h for h in strata if ns[h['key']] < h['N']]
        quotients = {h['key']: Fraction(h['N'] * h['multiplier'], ns[h['key']] + 1)
                     for h in candidates}
        maximum = max(quotients.values())
        chosen = min(key for key, value in quotients.items() if value == maximum)
        ns[chosen] += 1
    return ns


def main():
    projection = PARENT / 'inputs/metadata-and-fixed-labels.jsonl'
    small = PARENT / 'small-plan-comparison.json'
    projection_hash = hashlib.sha256(projection.read_bytes()).hexdigest()
    small_hash = hashlib.sha256(small.read_bytes()).hexdigest()
    rows = [json.loads(line) for line in projection.open()]
    assert len(rows) == 4481
    assert len({row['id'] for row in rows}) == 4481
    for row in rows:
        assert set(row) == {'id', 'department', 'family', 'exposure', 'rules39', 'LLM03'}
        assert row['exposure'] in {'remaining', 'direct', 'family_only'}
        for method in ['rules39', 'LLM03']:
            assert set(row[method]) == set(DIMS)
            assert all(type(row[method][d]) is int and row[method][d] in (0, 1) for d in DIMS)
    prior = json.loads(small.read_text())
    assert prior['N'] == 1444 and prior['n'] == 600
    developed = [r for r in rows if r['exposure'] != 'remaining']
    assert len(developed) == 3037
    counts = Counter((r['department'], priority_tag(r)) for r in developed)
    strata = [{'key': dept + '|' + tag, 'department': dept, 'tag': tag,
               'N': N, 'multiplier': MULTIPLIERS[tag]}
              for (dept, tag), N in sorted(counts.items())]
    assert len(strata) == 18 and sum(min(2, h['N']) for h in strata) == 35
    plans = {}
    for budget in [200, 400]:
        ns = allocate(strata, budget)
        allocation = [{**h, 'n': ns[h['key']], 'pi': ns[h['key']] / h['N'],
                       'weight': h['N'] / ns[h['key']],
                       'same_stratum_pair_pi': None if h['N'] == 1 else
                       ns[h['key']] * (ns[h['key']] - 1) / (h['N'] * (h['N'] - 1)),
                       'census': ns[h['key']] == h['N']}
                      for h in strata]
        assert sum(h['n'] for h in allocation) == budget
        assert all(0 < h['n'] <= h['N'] and (h['n'] >= 2 or h['n'] == h['N'])
                   for h in allocation)
        dept_n = {g: sum(h['n'] for h in allocation if h['department'] == g)
                  for g in DEPARTMENTS}
        plans[str(budget)] = {
            'developed_n': budget, 'total_n_with_unchanged_remaining600': budget + 600,
            'developed_department_n': dept_n,
            'full_department_n': {g: prior['department_n'][g] + dept_n[g]
                                  for g in DEPARTMENTS},
            'allocation': allocation,
            'unique_hidden_positive_miss_probability_in_developed_all_negative':
                {h['department']: 1 - h['pi'] for h in allocation
                 if h['tag'] == 'all_negative_agreement'},
        }
    assert all(plans['400']['allocation'][i]['n'] >= plans['200']['allocation'][i]['n']
               for i in range(len(strata)))
    assert hashlib.sha256(projection.read_bytes()).hexdigest() == projection_hash
    assert hashlib.sha256(small.read_bytes()).hexdigest() == small_hash
    output = {
        'status': 'independent_metadata_only_integer_allocation_review_not_execution',
        'date': '2026-10-10', 'model': 'GPT-6.1 Sol', 'reasoning_effort': 'ultra',
        'projection_N': 4481,
        'exposure_counts': dict(Counter(r['exposure'] for r in rows)),
        'developed_domain_N': 3037, 'remaining_N': 1444, 'remaining_n_unchanged': 600,
        'priority_multiplier_choice': MULTIPLIERS,
        'allocation_rule': 'Start n_h=min(2,N_h); exclude capped strata; assign each extra slot to maximum exact rational N_h*multiplier_h/(n_h+1); exact ties by lexicographic key; stop at fixed total budget.',
        'key_order_binding': 'department|tag using exact English codes in priority_multiplier_choice; no ID-dependent tie rule',
        'minimum_floor_total': 35, 'developed_nonempty_strata': 18,
        'all_developed_strata_positive_pi': True,
        'only_singleton_census_in_both_current_budgets': True,
        'plans': plans,
        'not_claimed': ['Neyman or globally optimal precision allocation',
                        'Guaranteed narrow confidence intervals or .80 point targets',
                        'Unseen-generalization performance for developed3037',
                        'Actual final sample IDs, random seed or human execution'],
        'bounds': {'no_gold_or_human_results_used': True, 'no_source_text_or_context_read': True,
                   'no_new_machine_runs': True, 'no_actual_ID_sample_drawn': True,
                   'existing_remaining600_files_modified': False},
        'inputs': {'metadata_projection_sha256': projection_hash,
                   'small_plan_comparison_json_sha256_preserved': small_hash},
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (HERE / 'allocation-review.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'minimum_floor_total': 35,
                      '200_developed_department_n': plans['200']['developed_department_n'],
                      '400_developed_department_n': plans['400']['developed_department_n'],
                      'all_positive_pi_and_minimum_counts': True,
                      'prior_small_file_hash_preserved': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
