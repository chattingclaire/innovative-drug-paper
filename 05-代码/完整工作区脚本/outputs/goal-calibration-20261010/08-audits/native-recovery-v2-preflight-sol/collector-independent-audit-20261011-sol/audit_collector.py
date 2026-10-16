#!/usr/bin/env python3
"""Independent read-only snapshot reconciliation; no collector rerun or coding."""
import collections
import datetime
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent.parent
OLD = BASE / '06-coding/native-full4481-v1-sol'
NEW = BASE / '06-coding/native-full4481-transport-recovery-v2-sol'
SNAPSHOT = BASE / '07-statistics/original-whole-batch-native-snapshot-20261011T1515-root'
INPUTS = {}

def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def reg(path):
    value = binding(path)
    INPUTS.setdefault(value['path'], value)
    return value

def unique(pairs):
    obj = {}
    for k, v in pairs:
        assert k not in obj, 'duplicate JSON key'
        obj[k] = v
    return obj

def loads(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))

def load(path):
    reg(path)
    return loads(Path(path).read_bytes())

def exact(value):
    observed = reg(value['path'])
    assert observed == {k: value[k] for k in ('path', 'bytes', 'sha256')}, 'binding mismatch'
    return observed

def save(name, obj):
    with (HERE / name).open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')

def pointer(obj, path):
    assert path.startswith('/')
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj

snapshot_seal = load(SNAPSHOT / 'seal.json')
for value in snapshot_seal['files']:
    assert Path(value['path']).resolve().parent == SNAPSHOT
    exact(value)
assert {Path(x['path']).name for x in snapshot_seal['files']} == {
    'coverage.json', 'selected-whole-batch-bindings.json', 'missing-original-batches.json',
    'packet-quote-issues.json', 'selected-records.jsonl'}
coverage = load(SNAPSHOT / 'coverage.json')
selections = load(SNAPSHOT / 'selected-whole-batch-bindings.json')
missing = load(SNAPSHOT / 'missing-original-batches.json')
issues = load(SNAPSHOT / 'packet-quote-issues.json')
assert issues == []
original_manifest = load(OLD / 'run-manifest.json')
recovery_manifest = load(NEW / 'manifest.json')
exact(coverage['original_manifest'])
exact(coverage['recovery_manifest'])
exact(coverage['collector'])
exact(original_manifest['ordered_source_ids'])
expected = load(original_manifest['ordered_source_ids']['path'])['approved_record_ids']
assert len(expected) == len(set(expected)) == 4481
snapshot_rows = [loads(line) for line in (SNAPSHOT / 'selected-records.jsonl').read_bytes().splitlines()]
reg(SNAPSHOT / 'selected-records.jsonl')
rows = {x['id']: x for x in snapshot_rows}
assert len(rows) == len(snapshot_rows) == 2168
assert [x['id'] for x in snapshot_rows] == [sid for sid in expected if sid in rows]
original_batches = {x['batch_id']: x for x in original_manifest['batches']}
recovery_batches = {x['batch_id']: x for x in recovery_manifest['batches']}
assert len(original_batches) == 504 and len(recovery_batches) == 207
assert len(selections) == len({x['batch_id'] for x in selections}) == 300
assert len(missing) == len({x['batch_id'] for x in missing}) == 204
assert set(original_batches) == {x['batch_id'] for x in selections} | {x['batch_id'] for x in missing}
assert not {x['batch_id'] for x in selections} & {x['batch_id'] for x in missing}

modes = collections.Counter()
by_dim = {d: collections.Counter() for d in ('S', 'E', 'Ec', 'I', 'F')}
optional_attempt_absent = []
bindings_audit = []
packet_quote_N = 0
decision_N = 0
pointer_role_anomalies = []
for item in selections:
    bid = item['batch_id']
    old_batch = original_batches[bid]
    old_assignment = load(exact(old_batch['assignment'])['path'])
    selection_binding = exact(item['selection'])
    selected = load(selection_binding['path'])
    first_binding = exact(item['first'])
    receipt_binding = exact(item['receipt'])
    first = load(first_binding['path'])
    receipt = load(receipt_binding['path'])
    assert receipt['state'] == 'technical_valid_whole_batch'
    if item['selected_mode'] == 'original':
        assert Path(selection_binding['path']) == OLD / bid / 'root-selection.json'
        assert selected['original_whole_batch_first'] == first_binding
        assert selected['technical_reception'] == receipt_binding
        selected_attempt = selected['selected_attempt_number']
        seal_binding = exact(selected['original_actor_seal'])
        report_binding = exact(selected['original_report'])
        mirror = exact(selected['canonical_whole_byte_mirror'])
        assert (mirror['bytes'], mirror['sha256']) == (first_binding['bytes'], first_binding['sha256'])
        assert selected['cross_attempt_record_combination'] is False
        assert selected['label_based_selection'] is False
        assert receipt['semantic_correctness_checked'] is False
        assert receipt['reference_or_accuracy_comparison_performed'] is False
        assignment = old_assignment
    else:
        assert item['selected_mode'] == 'transport_recovery'
        assert Path(selection_binding['path']) == NEW / bid / 'root-selection-v3.json'
        assert selected['first'] == first_binding and selected['reception'] == receipt_binding
        selected_attempt = selected['attempt']
        assert selected_attempt == 1
        assignment = load(exact(recovery_batches[bid]['assignment'])['path'])
        for key in ('source_ids', 'packets', 'manual', 'execution_prompt', 'source_asset_bindings', 'context_unit'):
            assert assignment[key] == old_assignment[key]
        assert assignment['original_assignment_binding'] == old_batch['assignment']
        seal_binding = exact(receipt['actor_seal'])
        seal_data = load(seal_binding['path'])
        report_binding = exact(seal_data['report_binding'])
        assert selected['semantic_scores_not_selection_criteria'] is True
        assert receipt['reference_compared'] is False
        assert receipt['first_or_labels_modified'] is False
    assert Path(first_binding['path']).parent.name == f'attempt-{selected_attempt:04d}'
    assert receipt.get('attempt_number', receipt.get('attempt')) == selected_attempt
    if 'attempt_number' in first:
        assert first['attempt_number'] == selected_attempt
    else:
        optional_attempt_absent.append({'batch_id': bid, 'mode': item['selected_mode'],
                                       'selected_attempt': selected_attempt})
    assert first['run_id'] == assignment['run_id']
    assert first['batch_id'] == receipt['batch_id'] == bid
    assert first['context_unit'] == assignment['context_unit'] == 'batch'
    assert first['requested_model'] == 'gpt-6.1-sol' and first['requested_reasoning_effort'] == 'ultra'
    assert first['manual_binding'] == assignment['manual']
    assert first['execution_prompt_binding'] == assignment['execution_prompt']
    assert assignment['manual'] == original_manifest['manual']
    assert assignment['execution_prompt'] == original_manifest['execution_prompt']
    assert item['source_ids'] == old_batch['source_ids'] == assignment['source_ids']
    assert [x['source_id'] for x in first['records']] == item['source_ids']
    seal = load(seal_binding['path'])
    assert exact(seal['first_binding']) == first_binding
    assert exact(seal['report_binding']) == report_binding
    assert seal['run_id'] == first['run_id'] and seal['batch_id'] == bid
    assert seal.get('template_only', False) is False
    assert seal['actual_completion_claimed'] is True
    assert isinstance(seal['actual_input_bindings'], list) and seal['actual_input_bindings']
    for bound in seal['actual_input_bindings']:
        exact(bound)
    packets = {p['source_id']: p for p in assignment['packets']}
    for record in first['records']:
        sid = record['source_id']
        row = rows[sid]
        assert row['original_batch_id'] == bid and row['selected_mode'] == item['selected_mode']
        assert row['selected_attempt_number'] == selected_attempt
        assert row['first'] == first_binding and row['selection'] == selection_binding
        assert row['technical_receipt'] == receipt_binding and row['actor_seal'] == seal_binding
        assert row['dimensions'] == record['dimensions']
        assert row['formal_validation_complete'] is False
        packet_binding = exact(packets[sid])
        packet = load(packet_binding['path'])
        assert row['packet'] == packet_binding
        assert record['output_id'] == packets[sid]['output_id']
        assert record['packet_sha256'] == packet_binding['sha256']
        assert set(record['dimensions']) == {'S', 'E', 'Ec', 'I', 'F'}
        for dimension, decision in record['dimensions'].items():
            value = decision['value']
            assert value is None or type(value) is int and value in (0, 1)
            assert row['labels'][dimension] == value
            by_dim[dimension][str(value)] += 1
            decision_N += 1
            if value is None:
                continue
            valid_quote_N = 0
            for evidence in decision['evidence']:
                if 'pointer' not in evidence:
                    continue
                field = pointer(packet, evidence['pointer'])
                assert isinstance(field, str) and evidence['quote'] and evidence['quote'] in field
                assert evidence['role'] in ('current', 'context')
                valid_quote_N += 1
                packet_quote_N += 1
                if (evidence['role'] == 'current') != (evidence['pointer'] == '/source_bundle/source_record/text'):
                    pointer_role_anomalies.append({'batch_id': bid, 'id': sid, 'dimension': dimension,
                                                  'role': evidence['role'], 'pointer': evidence['pointer']})
            assert valid_quote_N >= 1
    modes[item['selected_mode'] + '_batch_N'] += 1
    modes[item['selected_mode'] + '_record_N'] += len(first['records'])
    bindings_audit.append({'batch_id': bid, 'mode': item['selected_mode'], 'record_N': len(first['records']),
        'selected_attempt': selected_attempt, 'first': first_binding, 'receipt': receipt_binding,
        'actor_seal': seal_binding, 'report': report_binding, 'selection': selection_binding,
        'complete_original_batch_order': True, 'snapshot_values_equal_immutable_first': True,
        'all_actual_input_bindings_exact': True})

assert modes == {'original_batch_N': 297, 'original_record_N': 2132,
                 'transport_recovery_batch_N': 3, 'transport_recovery_record_N': 36}
assert collections.Counter(x['mode'] for x in optional_attempt_absent) == {'original': 5, 'transport_recovery': 2}
assert len(optional_attempt_absent) == 7
assert decision_N == 10840
null_N = sum(c['None'] for c in by_dim.values())
assert null_N == 39
missing_ids = [sid for x in missing for sid in x['source_ids']]
assert len(missing_ids) == len(set(missing_ids)) == 2313
assert set(missing_ids) == set(expected) - set(rows)
for item in missing:
    assert item['source_ids'] == original_batches[item['batch_id']]['source_ids']
missing_states = dict(collections.Counter(x['state'] for x in missing))
assert missing_states == {'inflight': 3, 'not_dispatched': 201}
derived = {'selected_record_N': len(rows), 'selected_batch_N': len(selections),
    'missing_record_N': len(missing_ids), 'binary_label_N': decision_N - null_N,
    'lawful_null_label_N': null_N, 'missing_label_N': len(missing_ids) * 5,
    'record_output_coverage': len(rows) / 4481,
    'complete_binary_record_N': sum(all(x['labels'][d] is not None for d in by_dim) for x in snapshot_rows),
    'per_dimension': {d: {'positive_N': c['1'], 'negative_N': c['0'],
                         'lawful_null_N': c['None'], 'missing_N': len(missing_ids)} for d, c in by_dim.items()}}
for k, v in derived.items():
    assert coverage[k] == v, k
assert coverage['missing_batch_states'] == missing_states
assert coverage['pointer_quote_issue_N'] == 0
assert coverage['formal_validation_complete'] is False and coverage['full_corpus_complete'] is False
assert coverage['thin35_included'] is False
assert coverage['first_values_changed'] is False and coverage['selection_by_semantic_metric'] is False
assert coverage['provider_serving_model_independently_verified'] is False
save('selected-batch-bindings-audit.json', {'batches': bindings_audit})
save('input-seal.json', {'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      'files': list(INPUTS.values()), 'input_N': len(INPUTS)})
changed = [item for item in INPUTS.values() if binding(item['path']) != item]
assert not changed
report = {'audited_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'snapshot_at_utc': coverage['at_utc'], 'snapshot_directory': str(SNAPSHOT),
    'state': 'independent_full_snapshot_reconciliation_passed', 'derived_counts': derived,
    'selected_modes': dict(modes), 'missing_batch_states_at_snapshot': missing_states,
    'packet_quotes_of_binary_decisions_checked_N': packet_quote_N,
    'pointer_quote_issue_N': 0, 'role_pointer_anomaly_N': len(pointer_role_anomalies),
    'role_pointer_anomalies': pointer_role_anomalies,
    'optional_first_attempt_field_absent': optional_attempt_absent,
    'optional_missing_attempt_fields_do_not_trigger_retry': True,
    'input_N': len(INPUTS), 'input_mismatch_N': len(changed),
    'all_300_batch_source_bindings_and_values_checked': True,
    'null_not_zero_and_missing_not_null': True,
    'snapshot_not_current_live_state': True,
    'no_original_first_or_labels_or_selection_changed': True,
    'thin35_or_manual77_included': False,
    'model_calls': 0, 'collector_not_rerun': True,
    'model_actual_serving_identity_verified': False,
    'original_297_all_actual_model_reading_independently_audited': False,
    'formal_validation_complete': False, 'full_corpus_complete': False}
save('report.json', report)
save('input-integrity-readback.json', {'input_N': len(INPUTS), 'mismatch_N': len(changed),
                                   'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({'record_N': len(rows), 'selected_batch_N': len(selections), 'input_N': len(INPUTS),
                  'quotes_checked_N': packet_quote_N, 'role_pointer_anomaly_N': len(pointer_role_anomalies),
                  'input_mismatch_N': len(changed), 'optional_missing_attempt_fields_N': 7}, ensure_ascii=False))
