"""Freeze a diagnostic draw before semantic review of common I/F negatives."""
import hashlib
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AI = ROOT.parent / 'ai-audit800-20261010'
OUT = HERE / 'common-negative30-root'


def binding(p):
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b),
            'sha256': hashlib.sha256(b).hexdigest()}


def main():
    OUT.mkdir(exist_ok=True)
    destination = OUT / 'draw-freeze.json'
    assert not destination.exists(), 'Preserve the existing diagnostic draw'
    initial = AI / 'AI原始判读-800条.jsonl'
    rule_path = ROOT / '06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl'
    metadata_path = AI / 'checks/sample-metadata.json'
    ai = [json.loads(s) for s in initial.read_text().splitlines()]
    rule = {r['id']: r for r in map(json.loads, rule_path.read_text().splitlines())}
    metadata = json.loads(metadata_path.read_text())['records']
    groups = defaultdict(list)
    for row in ai:
        if not all(row['judgments'][d]['value'] == 0 and
                   rule[row['source_id']]['labels'][d] == 0 for d in ['I', 'F']):
            continue
        m = metadata[row['blind_id']]
        groups[m['department'], m['domain']].append({
            'blind_id': row['blind_id'], 'source_id': row['source_id'],
            'department': m['department'],
            'historical_domain': m['domain'],
            'material_path': str(AI / 'source-A/coder-A/materials' /
                                 (row['blind_id'] + '.json'))})
    assert len(groups) == 6 and sum(map(len, groups.values())) == 739
    rng = random.Random(2026101002)
    selections, strata = [], []
    for key in sorted(groups):
        rows = sorted(groups[key], key=lambda r: r['blind_id'])
        N, n = len(rows), 5
        assert N >= n
        picked = rng.sample(rows, n)
        for row in sorted(picked, key=lambda r: r['blind_id']):
            row['conditional_diagnostic_inclusion_probability'] = n / N
            row['conditional_diagnostic_weight'] = N / n
            selections.append(row)
        strata.append({'department': key[0], 'historical_domain': key[1],
                       'common_negative_frame_N': N, 'selected_n': n})
    assert len(selections) == 30
    frame = sorted((row for group in groups.values() for row in group),
                   key=lambda r: r['blind_id'])
    result = {
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'diagnose shared I/F omissions after inspecting all positives',
        'population': '739 records in the existing auxiliary800 for which AI and rule both have binary I=0,F=0',
        'sampling': 'SRSWOR5 per department×historical-exposure stratum',
        'seed': 2026101002, 'strata': strata, 'selected_records': selections,
        'frame': frame,
        'inputs': [binding(initial), binding(rule_path), binding(metadata_path)],
        'manual': binding(ROOT / '03-manual/full4481-common-release-20261010-root/manual.txt'),
        'actual_current_text_semantic_reviews_completed_at_freeze': 0,
        'diagnostic_AI_reviews_are_human_reference': False,
        'conditional_weights_are_full4481_or_formal200_weights': False,
        'existing_positive_review_and_this_draw_may_be_pooled_unweighted_for_accuracy': False,
        'historical_remaining_status_proves_future_untuned_independence': False,
        'current_formal_production_inputs_modified': False}
    with destination.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'frozen_draw': str(destination), 'frame_N': 739,
                      'selected_N': 30, 'strata_N': 6,
                      'semantic_review_completed_N': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
