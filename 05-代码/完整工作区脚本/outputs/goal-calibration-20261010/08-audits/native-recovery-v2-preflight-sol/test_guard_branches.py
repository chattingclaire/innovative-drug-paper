#!/usr/bin/env python3
"""Synthetic unit checks of supplement branches only, never coding/model checks.

The fixture validator deliberately returns success. Original strict schema/evidence
validation is not simulated or claimed by this test. All fixture writes stay here.
"""
import copy
import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('readonly_guard', HERE / 'strict_reception_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

def save(path, value):
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def fixture(name, change):
    root = HERE / 'guard-synthetic-tests' / name
    root.mkdir(parents=True)
    first_path = root / 'first.json'
    report_path = root / 'report.txt'
    seal_path = root / 'seal.json'
    validator = root / 'fixture-validator.py'
    validator.write_text('def verify(*args): return {"fixture_only": True}\n')
    packet = root / 'fixture-packet.json'
    packet.write_text('{"text":"fixture exact quote"}\n')
    routing_path = root / 'routing.json'
    save(routing_path, {'routes': [{'batch_id': 'fixture-batch', 'first_path': str(first_path),
        'report_path': str(report_path), 'seal_path': str(seal_path),
        'attempt_number': 1, 'output_directory': str(root)}]})
    assignment_path = root / 'assignment.json'
    assignment = {'run_id': 'fixture-run', 'batch_id': 'fixture-batch',
        'source_ids': ['fixture-source'], 'strict_technical_validator': guard.binding(validator),
        'attempt_output_routing': guard.binding(routing_path),
        'packets': [guard.binding(packet)], 'source_asset_bindings': [],
        'original_assignment_binding': {'synthetic_fixture_only': True}}
    save(assignment_path, assignment)
    manifest_path = root / 'manifest.json'
    save(manifest_path, {'run_id': 'fixture-run', 'batches': [{'batch_id': 'fixture-batch',
        'source_ids': assignment['source_ids'], 'assignment': guard.binding(assignment_path)}],
        'validator': guard.binding(validator), 'max_total_technical_attempts': 3})
    first = {'records': [{'source_id': 'fixture-source', 'dimensions': {
        'S': {'value': None, 'evidence': []}}}]}
    if name == 'zero_without_packet_evidence':
        first['records'][0]['dimensions']['S']['value'] = 0
    save(first_path, first)
    report_path.write_text('Synthetic guard branch test; no coding performed.\n')
    events = root / 'events.jsonl'
    event_values = [{'type': 'thread.started', 'thread_id': 'fixture-fresh-thread'},
                    {'type': 'turn.completed'}]
    if name == 'missing_completed_turn':
        event_values.pop()
    events.write_text(''.join(json.dumps(x) + '\n' for x in event_values))
    stderr = root / 'stderr.txt'
    stderr.write_text('')
    process = {'actual_process_terminal': True, 'returncode': 0, 'timed_out': False,
               'events': guard.binding(events), 'stderr': guard.binding(stderr)}
    if name == 'nonterminal_process':
        process['actual_process_terminal'] = False
    save(root / 'process-completion.json', process)
    seal = {'run_id': 'fixture-run', 'batch_id': 'fixture-batch', 'template_only': False,
        'actual_completion_claimed': True, 'first_binding': guard.binding(first_path),
        'report_binding': guard.binding(report_path), 'actual_input_bindings': [guard.binding(packet)]}
    change(seal)
    save(seal_path, seal)
    return manifest_path, assignment_path, first_path

cases = [
    ('legal_null', lambda s: None, False, True),
    ('missing_template_original_v3_default', lambda s: s.pop('template_only'), False, True),
    ('missing_template_explicit_new_mode', lambda s: s.pop('template_only'), True, False),
    ('wrong_run_id', lambda s: s.update(run_id='wrong'), False, False),
    ('wrong_batch_id', lambda s: s.update(batch_id='wrong'), False, False),
    ('template_true', lambda s: s.update(template_only=True), False, False),
    ('completion_false', lambda s: s.update(actual_completion_claimed=False), False, False),
    ('missing_completion_flag', lambda s: s.pop('actual_completion_claimed'), False, False),
    ('empty_real_inputs', lambda s: s.update(actual_input_bindings=[]), False, False),
    ('wrong_first_hash', lambda s: s['first_binding'].update(sha256='0' * 64), False, False),
    ('zero_without_packet_evidence', lambda s: None, False, False),
    ('nonterminal_process', lambda s: None, False, False),
    ('missing_completed_turn', lambda s: None, False, False),
]
results = []
for name, change, explicit, expected in cases:
    paths = fixture(name, change)
    try:
        result = guard.verify(*paths, require_explicit_template_false=explicit)
        observed = True
        detail = result['state']
    except Exception as error:
        observed = False
        detail = type(error).__name__ + ': ' + str(error)
    assert observed == expected, (name, observed, expected, detail)
    results.append({'case': name, 'expected_valid': expected,
                    'observed_valid': observed, 'pass': True, 'detail': detail})
report = {'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'guard': guard.binding(HERE / 'strict_reception_guard.py'),
    'cases': results, 'passed_N': len(results), 'model_calls': 0,
    'original_or_v2_files_written': False,
    'scope': 'Synthetic supplemental branches only. Fixture strict validator is a stub; '
             'this does not test original schema semantics or prove actual pilot reception.'}
save(HERE / 'guard-branch-tests.json', report)
print(json.dumps({'passed_N': len(results), 'scope': report['scope']}, ensure_ascii=False))
