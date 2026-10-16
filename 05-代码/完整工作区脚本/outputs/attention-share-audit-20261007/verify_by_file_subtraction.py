"""Independent arithmetic verification using per-file totals and subtraction.

This script does not import the recalculation script. It derives primary and
leave-one-file estimates directly from original labels and exact design weights.
"""
from collections import defaultdict, Counter
from fractions import Fraction
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CURRENT = ROOT / 'outputs/autocode-v28-review-20261004-111306'
BASE = ROOT / 'outputs/autocode-v25-20260927'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC', 'GOV', 'ALL')
METHODS = ('rules_v28_2', 'llm_gpt56_sol_v13_original', 'A_AI_reference', 'C_AI_reference')

def read(path):
    return {r['id']: r for r in [json.loads(line) for line in path.read_text().splitlines() if line.strip()]}

def value(x):
    if x is None:
        return None
    if isinstance(x, dict) and 'exact_fraction' in x:
        return Fraction(x['exact_fraction'])
    return Fraction(x)

def main():
    target = OUT / '注意力占比-原定义重算.json'
    report = json.loads(target.read_text())
    inp = read(CURRENT / 'rule_inputs_v27.jsonl')
    rules = read(CURRENT / 'all_predictions.jsonl')
    llm = read(BASE / 'llm_runs/gpt56-sol-v13-native-1/all_predictions.jsonl')
    ac = read(BASE / 'current_1268_references.jsonl')
    meta = {Path(r['original_file']).stem: r for r in json.loads((ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json').read_text())['rows']}
    totals = defaultdict(Fraction)
    per_file = defaultdict(Fraction)
    rawtotals = Counter()
    overlaps = defaultdict(Fraction)
    rawoverlaps = Counter()
    for rid, source in inp.items():
        file = source['input']['original_file_stem']
        group = meta[file]['analysis_group']
        preds = {'rules_v28_2': (rules[rid]['prediction']['labels'], Fraction(1)),
            'llm_gpt56_sol_v13_original': (llm[rid]['labels'], Fraction(1))}
        if rid in ac:
            h = ac[rid]['historical_sampling']
            for c in ('A', 'C'):
                preds[c + '_AI_reference'] = (ac[rid]['original_references'][c]['labels'], Fraction(h['N_h'], h['n_h']))
        for method, (labels, w) in preds.items():
            hits = sum(v == 1 for v in labels.values())
            pending = sum(v == '待定' for v in labels.values())
            events = {'at_least_one_known_dimension': hits > 0,
                'all_five_confirmed_zero': hits == pending == 0,
                'at_least_two_known_dimensions': hits > 1,
                'exactly_one_known_dimension': hits == 1,
                'any_pending_dimension': pending > 0,
                'no_known_dimension_but_pending': hits == 0 and pending > 0,
                'possibly_at_least_one_dimension': hits + pending > 0,
                'possibly_at_least_two_dimensions': hits + pending > 1}
            for g in (group, 'ALL'):
                totals[method,g,'N'] += w
                for d, status in labels.items():
                    totals[method,g,d,status] += w
                    per_file[method,file,g,d,status] += w
                    rawtotals[method,g,d,status] += 1
                for event, yes in events.items():
                    if yes:
                        overlaps[method,g,event] += w
                        rawoverlaps[method,g,event] += 1
    checked = 0
    for method in METHODS:
        for group in GROUPS:
            row = report['primary'][method][group]
            denom = sum(totals[method,group,d,1] for d in DIMS)
            assert value(row['weighted_five_dimension_known_hit_sum']) == denom
            assert value(row['weighted_unit_count']) == totals[method,group,'N']
            checked += 2
            for d in DIMS:
                x = row['dimensions'][d]
                for status, weightedkey, rawkey in [(1,'weighted_known_hit_count','raw_known_hit_count'),(0,'weighted_confirmed_zero_count','raw_confirmed_zero_count'),('待定','weighted_pending_count','raw_pending_count')]:
                    assert value(x[weightedkey]) == totals[method,group,d,status]
                    assert x[rawkey] == rawtotals[method,group,d,status]
                    checked += 2
                assert value(x['attention_share']) == totals[method,group,d,1] / denom
                checked += 1
            for event, counts in row['overlap'].items():
                assert counts['raw_unit_count'] == rawoverlaps[method,group,event]
                assert value(counts['weighted_unit_count']) == overlaps[method,group,event]
                checked += 2
        for loo in report['sensitivities'][method]['leave_one_policy_file_out']:
            file = loo['discarded_file']
            for group in GROUPS:
                counts = {d: totals[method,group,d,1] - per_file[method,file,group,d,1] for d in DIMS}
                denom = sum(counts.values())
                assert value(loo['distribution'][group]['weighted_five_dimension_known_hit_sum']) == denom
                checked += 1
                for d in DIMS:
                    x = loo['distribution'][group]['dimensions'][d]
                    assert value(x['weighted_known_hit_count']) == counts[d]
                    assert value(x['attention_share']) == counts[d] / denom
                    checked += 2
    result = {'status': 'PASS', 'checks': checked,
        'method': 'Independent direct source scan, per-file Fraction totals, then subtraction (not importing main script)',
        'scope': '20 group-method primary estimates: raw/HT 0/1/pending, denominators, shares, overlap; all 4 methods × 55 leave-one-file × 5 groups × 5 dimension ratios',
        'target_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'source_labels_modified': False, 'confidence_intervals_verified': False,
        'note': 'No confidence intervals are present in this ratio audit; parent-agent new simultaneous-region math requires its separate review.'}
    (OUT / '独立逐文件减法核验.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
