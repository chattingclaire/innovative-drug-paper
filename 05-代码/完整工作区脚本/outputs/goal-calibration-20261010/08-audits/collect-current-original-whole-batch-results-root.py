"""Read-only collection of selected whole batches; diagnostic scoring is later.

No coding actor or selection file is changed. A fresh directory is used each time.
"""
import argparse, collections, datetime, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / '06-coding/native-full4481-v1-sol'
NEW = ROOT / '06-coding/native-full4481-transport-recovery-v2-sol'
DIMS = ('S', 'E', 'Ec', 'I', 'F')

def load(path):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result: raise ValueError('duplicate key: ' + k)
            result[k] = v
        return result
    def finite(value): raise ValueError('nonfinite constant: ' + value)
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique, parse_constant=finite)

def binding(path):
    p = Path(path).resolve(); b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def exact(b):
    current = binding(b['path'])
    assert all(current[k] == b[k] for k in ('path', 'bytes', 'sha256')), 'Changed binding: ' + b['path']
    return current

def save(path, value):
    with Path(path).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')

def pointer(obj, path):
    assert path.startswith('/')
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', required=True)
    parser.add_argument('--require-full', action='store_true'); args = parser.parse_args()
    out = Path(args.output).resolve(); out.mkdir(parents=True, exist_ok=False)
    original = load(OLD / 'run-manifest.json'); recovery = load(NEW / 'manifest.json')
    exact(original['ordered_source_ids'])
    expected = load(original['ordered_source_ids']['path'])['approved_record_ids']
    assert len(expected) == len(set(expected)) == 4481
    for name in ('source_jsonl', 'manual', 'execution_prompt', 'protocol'): exact(original[name])
    assert len(original['batches']) == 504
    new_batches = {b['batch_id']: b for b in recovery['batches']}
    assert len(new_batches) == 207
    records = {}; selections = []; missing = []; quote_issues = []; first_bindings = []
    states = collections.Counter(); by_dim = {d: collections.Counter() for d in DIMS}
    for batch in original['batches']:
        old_dir = Path(batch['assignment']['path']).parent
        assignment_binding = exact(batch['assignment']); oa = load(assignment_binding['path'])
        assert oa['source_ids'] == batch['source_ids']
        old_selection = old_dir / 'root-selection.json'
        new_selection = NEW / batch['batch_id'] / 'root-selection-v3.json'
        if old_selection.exists():
            assert not new_selection.exists(), 'Two selected results for same original batch'
            selection = load(old_selection); mode = 'original'
            assert selection['cross_attempt_record_combination'] is False and selection['label_based_selection'] is False
            first_binding = exact(selection['original_whole_batch_first'])
            receipt_binding = exact(selection['technical_reception'])
            seal_binding = exact(selection['original_actor_seal']); exact(selection['original_report'])
            mirror = exact(selection['canonical_whole_byte_mirror'])
            assert (mirror['bytes'], mirror['sha256']) == (first_binding['bytes'], first_binding['sha256'])
            selected_attempt = selection['selected_attempt_number']
            selected_binding = binding(old_selection)
            receipt = load(receipt_binding['path'])
            assert receipt['semantic_correctness_checked'] is False
            assert receipt['reference_or_accuracy_comparison_performed'] is False
        elif new_selection.exists():
            item = new_batches[batch['batch_id']]; ra_binding = exact(item['assignment']); ra = load(ra_binding['path'])
            assert ra['source_ids'] == oa['source_ids'] and ra['packets'] == oa['packets']
            exact(ra['original_assignment_binding'])
            selection = load(new_selection); mode = 'transport_recovery'
            first_binding = exact(selection['first']); receipt_binding = exact(selection['reception'])
            receipt = load(receipt_binding['path']); seal_binding = exact(receipt['actor_seal'])
            selected_attempt = selection['attempt']; selected_binding = binding(new_selection)
            assert selection['semantic_scores_not_selection_criteria'] is True
            assert receipt['reference_compared'] is False and receipt['first_or_labels_modified'] is False
        else:
            states['missing_batch_N'] += 1
            rd = NEW / batch['batch_id']
            started = list(rd.glob('attempt-*/dispatch-start.json'))
            terminal = list(rd.glob('attempt-*/process-completion.json'))
            terminal_receipts = list(rd.glob('attempt-*/root-reception-v3.json'))
            missing.append({'batch_id': batch['batch_id'], 'source_ids': batch['source_ids'],
                            'started_attempt_N': len(started), 'terminal_attempt_N': len(terminal),
                            'received_attempt_N': len(terminal_receipts),
                            'state': 'inflight' if len(started) > len(terminal) else
                                     ('unaccepted_or_exhausted' if terminal else 'not_dispatched')})
            continue
        assert receipt['state'] == 'technical_valid_whole_batch'
        assert receipt['batch_id'] == batch['batch_id']
        first = load(first_binding['path']); seal = load(seal_binding['path'])
        exact(seal['first_binding']); exact(seal['report_binding'])
        assert seal['first_binding']['sha256'] == first_binding['sha256']
        for b in seal['actual_input_bindings']: exact(b)
        assert [r['source_id'] for r in first['records']] == batch['source_ids']
        assert first['batch_id'] == batch['batch_id']
        assert Path(first_binding['path']).parent.name == f'attempt-{selected_attempt:04d}'
        assert receipt.get('attempt_number', receipt.get('attempt')) == selected_attempt
        if 'attempt_number' in first: assert first['attempt_number'] == selected_attempt
        else: states['optional_first_attempt_field_absent_batch_N'] += 1
        assert first['requested_model'] == 'gpt-6.1-sol' and first['requested_reasoning_effort'] == 'ultra'
        assert first['manual_binding']['sha256'] == original['manual']['sha256']
        assert first['execution_prompt_binding']['sha256'] == original['execution_prompt']['sha256']
        packets = {b['source_id']: b for b in oa['packets']}
        batch_records = []
        for record in first['records']:
            sid = record['source_id']; assert sid not in records
            packet_binding = exact(packets[sid]); packet = load(packet_binding['path'])
            assert record['packet_sha256'] == packet_binding['sha256']
            assert set(record['dimensions']) == set(DIMS)
            labels = {}
            for d in DIMS:
                decision = record['dimensions'][d]; value = decision['value']
                assert value is None or type(value) is int and value in (0, 1)
                labels[d] = value; by_dim[d][str(value)] += 1
                if value is None: continue
                valid_packet_quote_N = 0; bad = []
                for ev in decision['evidence']:
                    if 'pointer' not in ev: continue
                    try:
                        target = pointer(packet, ev['pointer'])
                        assert isinstance(target, str) and isinstance(ev['quote'], str) and ev['quote']
                        assert ev['quote'] in target
                        assert ev['role'] in ('current', 'context')
                        valid_packet_quote_N += 1
                    except (AssertionError, KeyError, ValueError, IndexError, TypeError) as error:
                        bad.append({'pointer': ev.get('pointer'), 'error': type(error).__name__})
                if not valid_packet_quote_N or bad:
                    quote_issues.append({'id': sid, 'dimension': d, 'selected_mode': mode,
                                         'valid_packet_quote_N': valid_packet_quote_N, 'invalid_pointer_evidence': bad,
                                         'value': value, 'first': first_binding})
            item = {'id': sid, 'labels': labels, 'dimensions': record['dimensions'],
                    'packet': packet_binding, 'original_batch_id': batch['batch_id'],
                    'selected_mode': mode, 'selected_attempt_number': selected_attempt,
                    'first': first_binding, 'selection': selected_binding, 'technical_receipt': receipt_binding,
                    'actor_seal': seal_binding, 'formal_validation_complete': False}
            records[sid] = item; batch_records.append(sid)
        states[mode + '_batch_N'] += 1; states[mode + '_record_N'] += len(batch_records)
        first_bindings.append(first_binding)
        selections.append({'batch_id': batch['batch_id'], 'selected_mode': mode, 'source_ids': batch_records,
                           'selection': selected_binding, 'first': first_binding, 'receipt': receipt_binding})
    ordered = [records[s] for s in expected if s in records]
    covered = len(ordered); null_N = sum(r['labels'][d] is None for r in ordered for d in DIMS)
    full = covered == 4481 and len(selections) == 504 and not missing and not quote_issues
    report = {'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'identity': 'actual selected original whole batches and fixed-batch transport recovery; not formal accuracy validation',
              'allocated_record_N': 4481, 'allocated_batch_N': 504, 'selected_record_N': covered,
              'selected_batch_N': len(selections), 'missing_record_N': 4481 - covered,
              'binary_label_N': covered * 5 - null_N, 'lawful_null_label_N': null_N,
              'missing_label_N': (4481 - covered) * 5, 'record_output_coverage': covered / 4481,
              'complete_binary_record_N': sum(all(r['labels'][d] is not None for d in DIMS) for r in ordered),
              'per_dimension': {d: {'positive_N': by_dim[d]['1'], 'negative_N': by_dim[d]['0'],
                                     'lawful_null_N': by_dim[d]['None'], 'missing_N': 4481-covered} for d in DIMS},
              'actual_selected_modes': dict(states), 'missing_batch_states': dict(collections.Counter(x['state'] for x in missing)),
              'pointer_quote_issue_N': len(quote_issues), 'full_corpus_complete': full,
              'provider_serving_model_independently_verified': False,
              'formal_validation_complete': False, 'thin35_included': False,
              'selection_by_semantic_metric': False, 'first_values_changed': False,
              'original_manifest': binding(OLD/'run-manifest.json'), 'recovery_manifest': binding(NEW/'manifest.json'),
              'collector': binding(__file__)}
    save(out/'coverage.json', report); save(out/'selected-whole-batch-bindings.json', selections)
    save(out/'missing-original-batches.json', missing); save(out/'packet-quote-issues.json', quote_issues)
    with (out/'selected-records.jsonl').open('x', encoding='utf8') as f:
        for row in ordered: f.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
    save(out/'seal.json', {'files': [binding(p) for p in sorted(out.iterdir()) if p.is_file()], 'self_excluded': True})
    print(json.dumps(report, ensure_ascii=False))
    if args.require_full: assert full, 'Full corpus incomplete or evidence receipt issues; snapshot is retained'

if __name__ == '__main__': main()
