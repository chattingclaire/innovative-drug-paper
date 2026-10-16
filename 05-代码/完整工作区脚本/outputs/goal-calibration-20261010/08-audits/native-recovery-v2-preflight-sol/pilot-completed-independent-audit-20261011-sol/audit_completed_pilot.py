#!/usr/bin/env python3
"""Read-only audit of completed pilot artifacts. Writes only this new directory."""
import collections
import datetime
import hashlib
import json
import re
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PREFLIGHT = HERE.parent
BASE = PREFLIGHT.parent.parent
RUN = BASE / '06-coding/native-full4481-transport-recovery-v2-sol'
OLD = BASE / '06-coding/native-full4481-v1-sol'
INPUTS = {}

def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def register(path):
    item = bind(path)
    INPUTS.setdefault(item['path'], item)
    return item

def load(path):
    register(path)
    return json.loads(Path(path).read_bytes())

def walk_bindings(obj):
    if isinstance(obj, dict):
        if {'path', 'bytes', 'sha256'} <= set(obj) and Path(obj['path']).is_file():
            register(obj['path'])
        for value in obj.values():
            walk_bindings(value)
    elif isinstance(obj, list):
        for value in obj:
            walk_bindings(value)

def save(name, obj):
    with (HERE / name).open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')

def coverage(intervals, end):
    cursor = 0
    for left, right in sorted(intervals):
        if left > cursor:
            return False
        cursor = max(cursor, right)
    return cursor >= end

def pointer_value(obj, pointer):
    for token in pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        obj = obj[int(token)] if isinstance(obj, list) else obj[token]
    return obj

previous = load(PREFLIGHT / 'input-seal.json')
historical_binding_mismatches = []
for item in previous['files']:
    current = register(item['path'])
    if current != item:
        historical_binding_mismatches.append({'expected': item, 'observed': current})
assert not historical_binding_mismatches
manifest = load(RUN / 'manifest.json')
guard_binding = register(PREFLIGHT / 'strict_reception_guard.py')
guard = types.ModuleType('read_only_pilot_guard')
guard.__file__ = guard_binding['path']
exec(compile(Path(guard.__file__).read_bytes(), guard.__file__, 'exec'), guard.__dict__)
repair = load(RUN / 'ROOT-receiver-runtime-preflight-repair.json')
stop = load(RUN / 'ROOT-stop-receiver-dependency-error.json')
controller_profile = load(RUN / 'ROOT-controller-v4-binding.json')
walk_bindings(repair)
walk_bindings(controller_profile)
import jsonschema
runtime = {'python': sys.executable, 'version': sys.version,
           'jsonschema_module': register(jsonschema.__file__)}
assert str(Path(sys.executable).resolve()) == str(Path(repair['receiver_runtime']).resolve())
assert runtime['jsonschema_module'] == repair['jsonschema_module']
for name in ('controller', 'guard', 'capacity_sidecar', 'prepared_manifest'):
    assert register(controller_profile[name]['path']) == controller_profile[name]

patterns = [
    re.compile(r'(?m)^PATH=(.+)\nSTART=(\d+)\nEND=(\d+)\nTOTAL_UNICODE_CHARS=(\d+)\n'),
    re.compile(r'(?m)^FILE (.+) start=(\d+) end=(\d+) total_unicode_chars=(\d+)\n'),
    re.compile(r'(?m)^FILE (.+)\nSTART (\d+) END (\d+) TOTAL (\d+)\n'),
]
audits = []
all_decisions = []
all_evidence = []
for bid in ('batch-0296', 'batch-0299', 'batch-0300'):
    batch_dir = RUN / bid
    slot = batch_dir / 'attempt-0001'
    assignment_path = batch_dir / 'assignment.json'
    first_path = slot / 'first.json'
    assignment = load(assignment_path)
    original = load(OLD / bid / 'assignment.json')
    first = load(first_path)
    seal = load(slot / 'seal.json')
    process = load(slot / 'process-completion.json')
    reception = load(slot / 'root-reception-v3.json')
    thin = load(slot / 'root-reception.json')
    selection = load(batch_dir / 'root-selection-v3.json')
    dispatch = load(slot / 'dispatch-start.json')
    register(slot / 'report.txt')
    register(slot / 'dispatch-prompt.txt')
    walk_bindings(assignment)
    walk_bindings(seal)
    walk_bindings(process)
    walk_bindings(reception)
    walk_bindings(selection)
    result = guard.verify(RUN / 'manifest.json', assignment_path, first_path)
    assert result == reception['validation'], 'Independent guard differs from ROOT stored validation'
    assert reception['state'] == 'technical_valid_whole_batch'
    assert reception['attempt'] == selection['attempt'] == 1
    assert selection['first'] == reception['first'] == register(first_path)
    assert selection['reception'] == register(slot / 'root-reception-v3.json')
    assert selection['assignment'] == register(assignment_path)
    assert selection['run_id'] == reception['run_id'] == assignment['run_id']
    assert thin['error'] == {'type': 'ModuleNotFoundError', 'message': "No module named 'jsonschema'"}
    assert original['source_ids'] == assignment['source_ids'] == [r['source_id'] for r in first['records']]
    preserved_keys = ['source_ids', 'expected_N', 'packets', 'manual', 'execution_prompt',
                      'source_asset_bindings', 'context_unit', 'requested_model', 'requested_reasoning_effort',
                      'max_total_technical_attempts']
    preserved = {key: original.get(key) == assignment.get(key) for key in preserved_keys}
    assert all(preserved.values())
    raw = (slot / 'cli-events.jsonl').read_bytes()
    register(slot / 'cli-events.jsonl')
    (HERE / f'{bid}-terminal-events.snapshot.jsonl').open('xb').write(raw)
    events = [json.loads(line) for line in raw.splitlines()]
    outputs = [(line, e['item']) for line, e in enumerate(events, 1)
               if e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'command_execution']
    readable = {str(assignment_path): assignment_path.read_text()}
    for key in ('manual', 'execution_prompt', 'actor_instructions', 'output_schema', 'output_validation_contract'):
        item = assignment[key]
        readable[item['path']] = Path(item['path']).read_text()
    for item in assignment['packets']:
        readable[item['path']] = Path(item['path']).read_text()
    actual_ranges = collections.defaultdict(list)
    segments = []
    literal_stdout_truncation_markers = []
    for line, event in outputs:
        output = event.get('aggregated_output', '')
        if re.search(r'Warning: truncated output|\d+ tokens truncated|\d+ lines omitted|\d+ characters omitted', output, re.I):
            literal_stdout_truncation_markers.append(line)
        for path, text in readable.items():
            if text in output:
                actual_ranges[path].append((0, len(text)))
        headers = sorted([m for pattern in patterns for m in pattern.finditer(output)], key=lambda m: m.start())
        for index, match in enumerate(headers):
            path = match.group(1)
            start, end, total = map(int, match.groups()[1:])
            if path not in readable:
                continue
            body = output[match.end():headers[index + 1].start() if index + 1 < len(headers) else len(output)]
            text = readable[path]
            exact = 0 <= start <= end <= len(text) and total == len(text) and text[start:end] in body
            if exact:
                actual_ranges[path].append((start, end))
            segments.append({'event_line': line, 'item_id': event['id'], 'path': path,
                'start': start, 'end': end, 'total': total, 'exact_stdout_slice': exact,
                'entire_command_stdout_unicode_N': len(output)})
    material_coverage = [{'path': path, 'unicode_N': len(text),
        'exact_stdout_ranges': sorted(set(actual_ranges[path])),
        'complete_exact_stdout_coverage': coverage(actual_ranges[path], len(text))}
        for path, text in readable.items()]
    assert all(x['complete_exact_stdout_coverage'] for x in material_coverage)
    packet_map = {x['source_id']: x for x in assignment['packets']}
    value_counts = collections.Counter()
    evidence_counts = collections.Counter()
    for record in first['records']:
        packet = load(packet_map[record['source_id']]['path'])
        for dim, decision in record['dimensions'].items():
            value_counts[str(decision['value'])] += 1
            packet_evidence_N = 0
            current_evidence_N = 0
            for index, evidence in enumerate(decision['evidence']):
                entry = {'batch_id': bid, 'source_id': record['source_id'], 'dimension': dim,
                         'value': decision['value'], 'evidence_index': index, 'evidence': evidence}
                if 'pointer' in evidence:
                    field = pointer_value(packet, evidence['pointer'])
                    entry['exact_packet_quote'] = isinstance(field, str) and evidence['quote'] in field and bool(evidence['quote'])
                    entry['packet_full_stdout_coverage'] = True
                    assert entry['exact_packet_quote']
                    entry['quote_unicode_N'] = len(evidence['quote'])
                    if evidence['role'] == 'current':
                        entry['role_pointer_compatible'] = evidence['pointer'] == '/source_bundle/source_record/text'
                        current_evidence_N += 1
                    else:
                        entry['role_pointer_compatible'] = evidence['pointer'] != '/source_bundle/source_record/text'
                    assert entry['role_pointer_compatible']
                    if 'context_id' in evidence:
                        parent = pointer_value(packet, evidence['pointer'].rsplit('/', 1)[0])
                        entry['context_id_matches_packet'] = parent.get('context_id') == evidence['context_id']
                        assert entry['context_id_matches_packet']
                    packet_evidence_N += 1
                    evidence_counts['packet'] += 1
                else:
                    entry['supplemental_asset_bound_to_own_record'] = True
                    entry['supplemental_quote_verification_by_event_review'] = 'Separate event/asset review required; frozen validator checks identity only'
                    evidence_counts['asset'] += 1
                all_evidence.append(entry)
            assert decision['value'] is None or packet_evidence_N >= 1
            all_decisions.append({'batch_id': bid, 'source_id': record['source_id'], 'dimension': dim,
                'value': decision['value'], 'packet_evidence_N': packet_evidence_N,
                'current_command_evidence_N': current_evidence_N,
                'total_evidence_N': len(decision['evidence']),
                'all_packet_quotes_exact': True, 'all_packet_role_pointers_compatible': True,
                'whole_packet_stdout_coverage': True, 'reason_nonempty': bool(decision['reason'].strip()),
                'semantic_correctness_checked': False})
    a2 = batch_dir / 'attempt-0002'
    a2_files = sorted(x.name for x in a2.iterdir())
    for file in a2.iterdir():
        if file.is_file():
            register(file)
    audits.append({'batch_id': bid, 'record_N': len(first['records']), 'selected_attempt': 1,
        'independent_strict_guard_passed': True, 'independent_guard_equals_ROOT_reception': True,
        'original_research_assignment_preserved': preserved,
        'source_ids': assignment['source_ids'], 'value_counts': dict(value_counts),
        'evidence_counts': dict(evidence_counts), 'seal_flags': result['seal_flags'],
        'template_only_explicitly_present': 'template_only' in seal,
        'missing_template_only_accepted_by_original_v3_default_only': 'template_only' not in seal,
        'actual_input_binding_N': len(seal['actual_input_bindings']),
        'first': register(first_path), 'report': register(slot / 'report.txt'),
        'seal': register(slot / 'seal.json'), 'process': process,
        'root_reception': register(slot / 'root-reception-v3.json'),
        'root_selection': selection, 'cli_event_type_counts': dict(collections.Counter(e['type'] for e in events)),
        'material_coverage': material_coverage, 'exact_stdout_segments': segments,
        'literal_stdout_truncation_marker_event_lines': literal_stdout_truncation_markers,
        'actor_reported_truncation_events': first['read_manifest'].get('truncation_events', []),
        'actor_reported_other_read_events': first['read_manifest'].get('events', []),
        'thin_receiver_error': thin['error'],
        'redundant_attempt2_files_preserved': a2_files,
        'redundant_attempt2_first_exists': (a2 / 'first.json').exists(),
        'redundant_attempt2_terminal_receipt_present': (a2 / 'process-completion.json').exists(),
        'ROOT_stop_record_does_not_assert_known_exit_codes': all(not x['exit_code_known'] for x in stop['signal_receipts']),
        'requested_model': dispatch['requested_model'], 'requested_reasoning_effort': dispatch['requested_reasoning_effort'],
        'actual_serving_model_independently_verified': False,
        'actual_model_tool_feedback_budget_independently_verified': False,
        'reference77_or_thin35_read_or_merged_by_audit': False})

save('input-seal.json', {'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'files': list(INPUTS.values()), 'input_N': len(INPUTS),
    'historical_preflight_inputs_rechecked_N': len(previous['files']),
    'historical_preflight_input_mismatch_N': len(historical_binding_mismatches)})
save('strict-reception-and-presentation-audit.json', {'runtime': runtime, 'batches': audits,
    'receiver_runtime_repair': repair, 'stop_record': stop, 'controller_profile': controller_profile})
save('decision-evidence-audit.json', {'decision_N': len(all_decisions), 'decisions': all_decisions,
    'evidence_N': len(all_evidence), 'evidence': all_evidence,
    'semantic_correctness_or_reference_agreement_checked': False})
changed = []
for item in INPUTS.values():
    current = bind(item['path'])
    if current != item:
        changed.append({'before': item, 'after': current})
assert not changed, 'Read-only audit input changed concurrently'
save('input-integrity-readback.json', {'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'input_N': len(INPUTS), 'mismatch_N': len(changed), 'mismatches': changed,
    'writes_only_in_this_audit_directory': True, 'model_calls': 0})
print(json.dumps({'batch_N': len(audits), 'record_N': sum(x['record_N'] for x in audits),
    'decision_N': len(all_decisions), 'evidence_N': len(all_evidence), 'input_N': len(INPUTS),
    'input_mismatch_N': len(changed), 'values': dict(collections.Counter(str(x['value']) for x in all_decisions)),
    'evidence_kinds': dict(collections.Counter('packet' if 'pointer' in x['evidence'] else 'asset' for x in all_evidence))}, ensure_ascii=False))
