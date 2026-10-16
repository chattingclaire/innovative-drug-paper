#!/usr/bin/env python3
"""Finite development-only comparison; reads only sealed batches 4/7 and devref."""
import datetime
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
OUT = Path(__file__).resolve().parent
DIMS = ['S', 'E', 'Ec', 'I', 'F']
BATCHES = ['batch-0004', 'batch-0007']


def bind(p):
    b = Path(p).read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def load(p):
    return json.loads(Path(p).read_bytes())


def verify(e):
    actual = bind(Path(e['path']))
    assert actual['bytes'] == e['bytes'] and actual['sha256'] == e['sha256'], e['path']
    return actual


def save(name, obj, lines=False):
    raw = ''.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) + '\n' for x in obj) if lines else json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    with (OUT / name).open('xb') as f:
        f.write(raw.encode())


def fraction(n, d):
    if d == 0:
        return {'value': None, 'exact_fraction': None, 'undefined_reason': 'zero denominator'}
    v = Fraction(n, d)
    return {'value': float(v), 'exact_fraction': f'{v.numerator}/{v.denominator}', 'undefined_reason': None}


def metrics(rows, dim):
    valid = [r for r in rows if r['candidate_labels'][dim] is not None and r['reference_labels'][dim] is not None]
    c = {'TP': 0, 'FP': 0, 'FN': 0, 'TN': 0}
    for r in valid:
        p, t = r['candidate_labels'][dim], r['reference_labels'][dim]
        c['TP' if p == 1 and t == 1 else 'FP' if p == 1 else 'FN' if t == 1 else 'TN'] += 1
    tp, fp, fn, tn = [c[k] for k in ['TP', 'FP', 'FN', 'TN']]
    n = len(valid)
    chance_n = (tp + fn) * (tp + fp) + (tn + fp) * (tn + fn)
    return {
        'assigned_round_records': 77,
        'assigned_diagnostic_subset_records': len(rows),
        'complete_candidate_records': len(rows),
        'candidate_binary_decidable': sum(r['candidate_labels'][dim] is not None for r in rows),
        'candidate_null': sum(r['candidate_labels'][dim] is None for r in rows),
        'reference_binary_decidable_in_subset': sum(r['reference_labels'][dim] is not None for r in rows),
        'reference_null_in_subset': sum(r['reference_labels'][dim] is None for r in rows),
        'paired_binary_denominator': n,
        'either_side_null_excluded': len(rows) - n,
        'subset_technical_failed': 0,
        'round_technical_incomplete_or_failed_excluded': 39,
        **c,
        'kappa': fraction(n * (tp + tn) - chance_n, n * n - chance_n),
        'P': fraction(tp, tp + fp),
        'R': fraction(tp, tp + fn),
        'F1': fraction(2 * tp, 2 * tp + fp + fn),
        'Po': fraction(tp + tn, n),
        'Pe': fraction(chance_n, n * n),
        'Ppos': fraction(2 * tp, 2 * tp + fp + fn),
        'Pneg': fraction(2 * tn, 2 * tn + fp + fn),
        'disagreements': [r['source_id'] for r in valid if r['candidate_labels'][dim] != r['reference_labels'][dim]],
    }


log_path = ROOT / 'logs/root-native77-short-round-reception-20261010.json'
log = load(log_path)
plan_path = ROOT / '06-coding/native-llm77-v13-sol/preparation/plan-v2.json'
plan = load(plan_path)
ref_path = ROOT / '06-coding/development-reference77-v12-root-adjudicated-v2/reference.jsonl'
ref_manifest_path = ref_path.parent / 'manifest.json'
ref_manifest = load(ref_manifest_path)
assert bind(ref_path)['sha256'] == ref_manifest['reference_sha256']
raw_ref_lines = ref_path.read_bytes().splitlines(keepends=True)
ref = {}
for ordinal, raw in enumerate(raw_ref_lines, 1):
    row = json.loads(raw)
    assert row['id'] not in ref
    ref[row['id']] = (row, ordinal, hashlib.sha256(raw).hexdigest())
assert len(ref) == ref_manifest['n'] == 77

provenance = {
    'root_reception_log': bind(log_path), 'plan_metadata': bind(plan_path),
    'reference_file': bind(ref_path), 'reference_manifest': bind(ref_manifest_path),
    'source_candidate_seal_checks': [], 'actual_source_bodies_or_images_read_for_new_adjudication': 0,
}
derived, disagreements = [], []
for batch_id in BATCHES:
    row = next(x for x in log['rows'] if x['batch_id'] == batch_id)
    actor_seal = verify(row['seal'])
    attempt = Path(actor_seal['path']).parent
    s = load(actor_seal['path'])
    checks, firsts = [], {}
    for e in s['files']:
        q = Path(e['path'])
        q = q if q.is_absolute() else attempt / q
        a = verify({**e, 'path': str(q)})
        checks.append(a)
        if q.parent.name == 'first-output':
            item = load(q)
            assert item['blind_id'] not in firsts
            firsts[item['blind_id']] = (q.stem, item, a)
    rp = Path(row['receiver_report']['path'])
    receiver = verify(row['receiver_report'])
    receiver_seal_path = Path(str(rp) + '.seal.json')
    rs = load(receiver_seal_path)
    for e in rs['files']:
        verify(e)
    assert any(e['path'] == str(rp) and e['sha256'] == receiver['sha256'] for e in rs['files'])
    rr = load(rp)
    assert rr['actor_seal'] == actor_seal and not rr['errors']
    assert rr['format']['first_whole_objects_and_order_equal']
    assert rr['scope_recomputed_matches_actual_saved_list']
    assert all(x['scope_record_valid'] for x in rr['scope_results'])
    runtime_event_binding = verify(row['actual_runtime_tool_evidence'])
    event = load(runtime_event_binding['path'])
    actual_runtime = json.loads(event['actual_selected_event']['output']['text'])['CODEX_THREAD_ID']
    creation_return = verify(rr['creation_evidence']['return'])
    # ROOT's actual read_thread extraction proves the runtime ID, not unseen platform history.
    assert actual_runtime == row['threadId'] == rr['creation_evidence']['thread_id']
    assert row['root_actual_runtime_identity_matches_create_return'] is True
    for e in [rr['creation_evidence']['request'], rr['creation_evidence']['identity']]:
        verify(e)
    whole_path = attempt / 'whole-output.json'
    whole = load(whole_path)['items']
    expected = [x['source_id'] for x in next(x for x in plan['batches'] if x['batch_id'] == batch_id)['externally_frozen_packet_file_bindings']]
    actual = []
    for item in whole:
        source_id, first, first_binding = firsts[item['blind_id']]
        assert first == item
        actual.append(source_id)
        reference, ordinal, row_sha = ref[source_id]
        for labels in [item['labels'], reference['labels']]:
            assert set(labels) == set(DIMS)
            assert all(v is None or (type(v) is int and v in [0, 1]) for v in labels.values())
        derived.append({
            'source_id': source_id, 'batch_id': batch_id, 'runtime_thread_id': actual_runtime,
            'blind_id': item['blind_id'], 'candidate_first_file': first_binding,
            'candidate_whole_file': bind(whole_path), 'candidate_whole_item_ordinal_one_based': len(actual),
            'candidate_content_sha256': item['content_sha256'], 'candidate_manual_sha256': item['manual_sha256'],
            'candidate_labels': item['labels'], 'candidate_material_requests': item['material_requests'],
            'reference_labels': reference['labels'], 'reference_manual_sha256': reference['manual_sha256'],
            'reference_role_as_saved': reference['reference_role'],
            'reference_row_ordinal_one_based': ordinal, 'reference_original_line_sha256_including_newline': row_sha,
            'technical_state': 'complete_format_candidate_pending_technical_selection',
            'formally_selected_complete_valid': False,
            'binary_pair_eligibility': {d: item['labels'][d] is not None and reference['labels'][d] is not None for d in DIMS},
        })
        for d in DIMS:
            if item['labels'][d] != reference['labels'][d]:
                disagreements.append({
                    'source_id': source_id, 'batch_id': batch_id, 'dimension': d,
                    'candidate_label': item['labels'][d], 'development_reference_label': reference['labels'][d],
                    'candidate_original_evidence': item['evidence'][d], 'candidate_first_file': first_binding,
                    'reference_original_evidence_A': reference.get('evidence_A', {}).get(d),
                    'reference_original_evidence_B': reference.get('evidence_B', {}).get(d),
                    'reference_file': bind(ref_path), 'reference_row_ordinal_one_based': ordinal,
                    'adjudication_by_this_diagnostic': None,
                    'note': 'Evidence retained for ROOT source-based review; disagreement does not decide which label to change.',
                })
    assert actual == expected and len(firsts) == len(whole) == row['expected_records']
    provenance['source_candidate_seal_checks'].append({
        'batch_id': batch_id, 'actor_seal': actor_seal, 'actor_member_count': len(checks),
        'all_member_SHA_bytes_match': True, 'members': checks,
        'receiver_report': receiver, 'receiver_report_seal': bind(receiver_seal_path),
        'receiver_state_as_saved': rr['state'], 'receiver_pending_as_saved': rr['pending'],
        'later_ROOT_identity_verified': True, 'actual_runtime_event': runtime_event_binding,
        'actual_runtime_UUID': actual_runtime, 'creation_request': rr['creation_evidence']['request'],
        'creation_return': creation_return, 'whole': bind(whole_path),
        'whole_first_objects_and_order_independently_equal': True,
        'original_schema_and_source_quote_checks_basis': 'Previously sealed ROOT receiver: errors=[]; no new semantic validation or changed schema.',
        'scope_saved_results_basis': 'Previously sealed ROOT receiver scope results; all record_valid, no semantic truth claim.',
        'complete_provider_platform_history': None, 'selection_still_pending': True,
    })
assert len(derived) == 38 and len({x['source_id'] for x in derived}) == 38
save('input-bindings.json', provenance)
save('derived-rows.jsonl', derived, lines=True)
save('disagreements.jsonl', disagreements, lines=True)
save('metrics-exact.json', {
    'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'historically exposed, nonprobability, technical-success subset; AI nonblind ROOT-adjudicated development reference',
    'diagnostic_records': 38, 'round_assigned': 77,
    'technical_incomplete_or_failed_records_excluded': 39,
    'excluded_batches': [{k: x[k] for k in ['batch_id', 'expected_records', 'saved_first_items', 'state']} for x in log['rows'] if x['batch_id'] not in BATCHES],
    'nonbinary_policy': 'Either side null retained and excluded from binary denominator; no technical failure filled as 0.',
    'confusion_orientation': 'reference is comparison target; candidate positive=1: TP(candidate1/ref1), FP(1/0), FN(0/1), TN(0/0).',
    'formulas': {'kappa': '(Po-Pe)/(1-Pe)', 'Pe': '[(TP+FN)(TP+FP)+(TN+FP)(TN+FN)]/n^2', 'P': 'TP/(TP+FP)', 'R': 'TP/(TP+FN)', 'F1': '2TP/(2TP+FP+FN)', 'Po': '(TP+TN)/n', 'Ppos': '2TP/(2TP+FP+FN)', 'Pneg': '2TN/(2TN+FP+FN)'},
    'undefined_policy': 'Zero denominator returns null/NA, never 1.',
    'per_dimension': {d: metrics(derived, d) for d in DIMS},
    'disagreement_dimension_count': len(disagreements),
    'disagreement_unique_record_count': len({x['source_id'] for x in disagreements}),
    'candidate_manual_sha256': sorted({x['candidate_manual_sha256'] for x in derived}),
    'reference_manual_sha256': sorted({x['reference_manual_sha256'] for x in derived}),
    'manual_version_note': 'Candidate v1.3 and historical reference v1.1 hashes differ, retained explicitly; neither reference nor definitions changed for this comparison.',
    'population_CI_calculated': False, 'formal_acceptance': False,
    'random_holdout': False, 'human_gold': False, 'full77_result': False,
    'selected_complete_valid': False, 'model_calls_by_analyst': 0,
    'analyst_history': 'AI /root/pilot01_a_sol, GPT-6.1 Sol ultra; prior A development judgments, source restoration, source/technical audits; not blind to historical development material.',
})
print(json.dumps({'records': len(derived), 'disagreement_dimensions': len(disagreements), 'disagreement_records': len({x['source_id'] for x in disagreements}), 'actor_members_verified': sum(x['actor_member_count'] for x in provenance['source_candidate_seal_checks'])}))
