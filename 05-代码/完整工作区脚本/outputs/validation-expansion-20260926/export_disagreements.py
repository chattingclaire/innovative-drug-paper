"""Trace completed H600 or R200 comparisons to original reasons and source packets.

This is a descriptive post-submission export, not an adjudication or metric engine.
It refuses incomplete results. No reference labels or replacement labels are made.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

DIMS = ('S', 'E', 'Ec', 'I', 'F')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def pattern(a, c, machine):
    assert all((type(x) is int and x in (0, 1)) or (type(x) is str and x == '待定') for x in (a, c, machine))
    if any(x == '待定' for x in (a, c, machine)):
        return 'has_pending'
    assert all(type(x) is int and x in (0, 1) for x in (a, c, machine))
    if a == c == machine:
        return 'all_equal'
    if a == c:
        return 'A_C_equal_machine_differs'
    if a == machine:
        return 'A_machine_equal_C_differs'
    return 'C_machine_equal_A_differs'

def build(data, packet_bytes, statistics_sha256):
    assert data['status'] in ('completed_frozen_ID_join_not_validation_pass',
                              'completed_challenge_descriptive_ID_join_not_validation_pass')
    challenge = data['status'].startswith('completed_challenge_')
    archive = data['archive']
    rows = archive['normalized_rows_without_generated_reference']
    if challenge:
        assert not data['population_inference'] and not data['population_weights_used']
        assert not data['confidence_intervals_computed']
        assert data['sample_n'] == len(rows)
    else:
        meta = data['design_and_interval_metadata']
        assert meta['sample_size_matches_H600_plan'] is True
        assert meta['sample_n'] == len(rows)
    mapping_rows = archive['sampling_manifest_original']['rows']
    mapping = {r['id']: r for r in mapping_rows}
    assert len(mapping) == len(mapping_rows) == len(rows) == len({r['id'] for r in rows})
    assert set(mapping) == {r['id'] for r in rows}
    original = {'A': {}, 'C': {}}
    for name, submission in archive['raw_coder_submissions'].items():
        coder = submission['coder']
        for row in submission['rows']:
            assert row['id'] not in original[coder]
            original[coder][row['id']] = row
    materials = {}
    expected = {name for name in archive['packet_manifest'] if name.startswith('agent-A/')}
    assert set(packet_bytes) == expected
    for name, raw in packet_bytes.items():
        assert sha(raw) == archive['packet_manifest'][name]['sha256']
        for row in json.loads(raw)['rows']:
            assert row['id'] not in materials
            assert sha(row['text'].encode()) == mapping[row['id']]['unit_text_sha256']
            materials[row['id']] = row
    assert set(materials) == set(original['A']) == set(original['C']) == set(mapping)
    counts = {dim: Counter() for dim in DIMS}
    cases = []
    for normalized in rows:
        key = normalized['id']
        assert all(normalized[coder] == original[coder][key]['labels'] for coder in ('A', 'C'))
        patterns = {d: pattern(normalized['A'][d], normalized['C'][d], normalized['dictionary'][d]) for d in DIMS}
        for d, value in patterns.items():
            counts[d][value] += 1
        if any(value != 'all_equal' for value in patterns.values()):
            cases.append({'id': key, 'source_mapping': mapping[key],
                          'material_original': materials[key],
                          'dimension_patterns': patterns,
                          'original_A': original['A'][key], 'original_C': original['C'][key],
                          'frozen_dictionary_original': archive['selected_machine_records_by_blind_id'][key]})
    return {'status': 'post_submission_descriptive_trace_no_adjudication',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'statistics_sha256': statistics_sha256, 'sample_kind': 'R200' if challenge else 'H600',
            'sample_n': len(rows), 'case_count': len(cases),
            'raw_pattern_counts': {d: dict(v) for d, v in counts.items()},
            'interpretation': [
                'Counts are unweighted descriptions of these sampled units, not population estimates.',
                'A/C agreement does not create truth; machine disagreement is not automatically an error.',
                'Any pending label is retained as pending, including simultaneous pending labels.',
                'case_count counts units with at least one disagreement OR pending label; it is not an error count or an error rate. Each dimension pattern count uses all sample_n units as its raw denominator.',
                'Original reasons and source records are copied without alteration.',
                'This export does not revise the manual, machine, submissions or first reliability estimates.'
            ], 'cases': cases}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--holdout', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve existing issued export'
    raw = args.input.read_bytes()
    data = json.loads(raw)
    packets = {name: (args.holdout / name).read_bytes()
               for name in data['archive']['packet_manifest'] if name.startswith('agent-A/')}
    result = build(data, packets, sha(raw))
    with args.output.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({key: result[key] for key in ('status', 'sample_n', 'case_count', 'raw_pattern_counts')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
