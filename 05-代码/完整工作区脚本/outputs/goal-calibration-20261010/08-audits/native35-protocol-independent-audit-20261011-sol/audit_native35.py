#!/usr/bin/env python3
"""Read-only audit; this script writes only new artifacts in its own audit directory.

It does not import or execute the recovery dispatcher, original receiver, or model.
It never edits or normalizes coding submissions and never adjudicates their labels.
"""
from __future__ import annotations
import collections
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
RECOVERY = ROOT / '06-coding/native-reference77-coverage-recovery-v1-sol'
ORIGINAL = ROOT / '06-coding/native-full4481-v1-sol'
RUNNER = ROOT / '08-audits/run-missing77-native-coverage-recovery-root.py'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
INPUTS: dict[str, set[str]] = {}


def register(p: Path, role: str) -> Path:
    p = p.resolve()
    if p.is_file():
        INPUTS.setdefault(str(p), set()).add(role)
    return p


def strict_load(p: Path):
    def pairs(v):
        result = {}
        for k, value in v:
            if k in result:
                raise ValueError('duplicate JSON key: ' + k)
            result[k] = value
        return result
    def nonfinite(v):
        raise ValueError('nonfinite JSON: ' + v)
    return json.loads(p.read_text(encoding='utf8'), object_pairs_hook=pairs, parse_constant=nonfinite)


def bind(p: Path):
    raw = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, obj):
    p = OUT / name
    assert p.parent == OUT
    with p.open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def string_fields(obj, pointer=''):
    if isinstance(obj, str):
        yield pointer, obj
    elif isinstance(obj, dict):
        for k, value in obj.items():
            yield from string_fields(value, pointer + '/' + str(k).replace('~', '~0').replace('/', '~1'))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from string_fields(value, pointer + '/' + str(i))


def quote_fields(obj, pointer=''):
    if isinstance(obj, dict):
        for k, value in obj.items():
            if k in ('quote', 'current_quote') and isinstance(value, str):
                yield pointer + '/' + k, value
            else:
                yield from quote_fields(value, pointer + '/' + k)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from quote_fields(value, pointer + '/' + str(i))


def lookup(obj, locator):
    if not isinstance(locator, str):
        return None
    if '#/' in locator:
        locator = locator.split('#', 1)[1]
    if locator.startswith('/'):
        parts = [x.replace('~1', '/').replace('~0', '~') for x in locator[1:].split('/')]
    else:
        locator = re.sub(r'^(?:packet\.|\$\.)', '', locator)
        if not locator.startswith('source_bundle.') and locator != 'source_bundle':
            return None
        parts = re.sub(r'\[(\d+)\]', r'.\1', locator).split('.')
    try:
        cur = obj
        for part in parts:
            cur = cur[int(part)] if isinstance(cur, list) else cur[part]
        return cur
    except (KeyError, ValueError, TypeError, IndexError):
        return None


def nested_asset_claims(obj, pointer=''):
    if isinstance(obj, dict):
        for k, value in obj.items():
            nxt = pointer + '/' + k
            if k in ('source_image_read', 'source_page_checked', 'source_page_verified', 'source_figure'):
                yield nxt, value
            else:
                yield from nested_asset_claims(value, nxt)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from nested_asset_claims(value, pointer + '/' + str(i))


def citation(p, line):
    return {'path': str(p.resolve()), 'line': line}


manifest = strict_load(register(RECOVERY / 'manifest.json', 'recovery manifest'))
reception = strict_load(register(RECOVERY / 'technical-reception.json', 'recovery technical receipt'))
register(RUNNER, 'recovery dispatcher and receiver source; never executed')
for p in RECOVERY.iterdir():
    if p.is_file():
        register(p, 'recovery top-level execution provenance')
target_ids = manifest['source_ids']
assert len(target_ids) == len(set(target_ids)) == 35
original_index = {}
for p in sorted(ORIGINAL.glob('batch-*/assignment.json')):
    a = strict_load(register(p, 'original frozen batch map; identity only'))
    for sid in a['source_ids']:
        if sid in target_ids:
            assert sid not in original_index
            original_index[sid] = (p, a)
assert set(original_index) == set(target_ids)
for p in ORIGINAL.iterdir():
    if p.is_file():
        register(p, 'original execution and retention contract')
for p in (ORIGINAL / 'templates').glob('*'):
    if p.is_file():
        register(p, 'original frozen templates')
for shared in manifest['shared'].values():
    register(Path(shared['path']), 'recovery declared shared input')
for sid in target_ids:
    cdir = RECOVERY / 'cases' / sid
    for p in cdir.rglob('*'):
        if p.is_file():
            register(p, 'actual recovery case input/output/trace')
    case = strict_load(cdir / 'case-assignment.json')
    register(Path(case['packet']['path']), 'target packet to audit; labels not changed')
    a = original_index[sid][1]
    for key in ('manual', 'execution_prompt', 'actor_instructions', 'packet_schema', 'output_schema',
                'output_validation_contract', 'strict_technical_validator', 'read_manifest_template',
                'response_retention_policy', 'output_seal_template', 'technical_failure_template',
                'run_scope_binding', 'legacy_locator_alias_table_binding', 'delivery_manifest_order_metadata_only',
                'attempt_output_routing', 'campaign_scope_metadata_binding'):
        if isinstance(a.get(key), dict) and 'path' in a[key]:
            register(Path(a[key]['path']), 'original bound execution input identity')
    for item in a['packets']:
        register(Path(item['path']), 'original whole-batch packet identity only')
    for item in a['source_asset_bindings']:
        register(Path(item['path']), 'original whole-batch asset identity only')

before = [dict(bind(Path(p)), roles=sorted(roles)) for p, roles in sorted(INPUTS.items())]
save('input-seal.json', {'created_at_utc': datetime.now(timezone.utc).isoformat(),
                         'meaning': 'Current input bytes sealed before computation; historical bindings are checked separately.',
                         'input_N': len(before), 'files': before})
receipt_by_id = {x['source_id']: x for x in reception['results']}
facts = []
all_quotes = []
all_concurrency = []
bound_checks = []
event_types = collections.Counter()
all_image_claims = []
all_paths = []

for sid in target_ids:
    cdir = RECOVERY / 'cases' / sid
    slot = cdir / 'attempt-0001'
    case = strict_load(cdir / 'case-assignment.json')
    first = strict_load(slot / 'first.json')
    packet_path = Path(case['packet']['path'])
    packet_text = packet_path.read_text(encoding='utf8')
    packet = strict_load(packet_path)
    original_path, original = original_index[sid]
    original_packet = next(x for x in original['packets'] if x['source_id'] == sid)
    packet_same = all(case['packet'][k] == original_packet[k] for k in ('path', 'bytes', 'sha256'))
    events_path = slot / 'events.jsonl'
    events = [json.loads(line) for line in events_path.read_text(encoding='utf8').splitlines()]
    for e in events:
        event_types[e['type']] += 1
    commands = [(i + 1, e['item']) for i, e in enumerate(events)
                if e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'command_execution']
    outputs = [(line, item.get('aggregated_output', '')) for line, item in commands]
    material_outputs = {}
    for key, path in [('case_assignment', cdir / 'case-assignment.json'),
                      ('manual', Path(case['shared']['manual']['path'])),
                      ('execution_prompt', Path(case['shared']['execution_prompt']['path'])),
                      ('common_execution_protocol', Path(case['shared']['common_execution_protocol']['path'])),
                      ('packet', packet_path)]:
        text = path.read_text(encoding='utf8')
        full = [{'event_line': line, 'logged_output_characters': len(out),
                 'substring_start_0based': out.index(text), 'substring_end_0based': out.index(text) + len(text)}
                for line, out in outputs if text in out]
        material_outputs[key] = {'input': bind(path), 'file_unicode_code_points': len(text),
                                 'file_lines': len(text.splitlines()), 'complete_text_in_logged_stdout': bool(full),
                                 'matching_events': full}
    trunc_events = [{'event_line': line, 'item_id': item['id']} for line, item in commands
                    if re.search(r'(?:truncated|tokens omitted|lines omitted)', item.get('aggregated_output', ''), re.I)]
    packet_strings = list(string_fields(packet))
    quotes = []
    for location, quote in quote_fields(first['dimensions'], '/dimensions'):
        matches = [{'packet_pointer': pointer, 'unicode_start_0based': value.index(quote),
                    'unicode_end_0based': value.index(quote) + len(quote)}
                   for pointer, value in packet_strings if quote and quote in value]
        source_output_matches = [{'event_line': line} for line, out in outputs if quote and quote in out]
        status = 'exact_frozen_packet_substring' if matches else ('exact_logged_source_output_substring' if source_output_matches else 'not_found_in_allowed_observable_text')
        item = {'source_id': sid, 'output_pointer': location, 'quote': quote,
                'status': status, 'packet_matches': matches, 'event_output_matches': source_output_matches}
        quotes.append(item)
        all_quotes.append(item)
    declared_locations = []
    for dim, decision in first['dimensions'].items():
        for j, evidence in enumerate(decision['evidence']):
            quote = evidence.get('quote', evidence.get('current_quote'))
            for key in ('pointer', 'json_pointer', 'packet_pointer', 'json_path', 'evidence_path', 'packet_field', 'packet_location', 'location'):
                if key not in evidence:
                    continue
                location = evidence[key]
                value = lookup(packet, location)
                if isinstance(value, str):
                    status = 'declared_string_contains_exact_quote' if quote and quote in value else 'declared_string_quote_mismatch'
                elif value is not None:
                    status = 'declared_location_is_container_not_string'
                else:
                    status = 'not_a_resolvable_packet_field_locator'
                declared_locations.append({'dimension': dim, 'evidence_index': j,
                                           'locator_key': key, 'locator': location, 'status': status})
    claims = [{'source_id': sid, 'output_pointer': pointer, 'claim': claim}
              for pointer, claim in nested_asset_claims(first['dimensions'], '/dimensions')]
    all_image_claims.extend(claims)
    command_inventory = []
    for line, item in commands:
        command = item['command']
        paths = sorted(set(x.rstrip('\\') for x in re.findall(r'/Users/[^\n\"\' ]+', command)))
        all_paths.extend(paths)
        command_inventory.append({'event_line': line, 'item_id': item['id'], 'command': command,
                                  'exit_code': item.get('exit_code'),
                                  'logged_output_unicode_code_points': len(item.get('aggregated_output', '')),
                                  'logged_output_sha256_utf8': hashlib.sha256(item.get('aggregated_output', '').encode()).hexdigest(),
                                  'literal_absolute_paths': paths})
    start = strict_load(slot / 'dispatch-start.json')
    terminal = strict_load(slot / 'terminal.json')
    stderr_text = (slot / 'stderr.txt').read_text(encoding='utf8')
    times = re.findall(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+Z', stderr_text)
    all_concurrency.append({'source_id': sid, 'start_utc': start['at_utc'],
                            'last_dated_stderr_utc': max(times) if times else None,
                            'meaning': 'Start-to-last-log interval is a conservative known-live interval, not an inferred end time.'})
    all_bindings = [('manifest case', next(x['case'] for x in manifest['cases'] if x['source_id'] == sid)),
                    ('case packet', case['packet']),
                    ('technical reception first', receipt_by_id[sid]['first']),
                    ('terminal events', terminal['events']), ('terminal stderr', terminal['stderr']),
                    ('dispatch prompt', start['prompt'])]
    all_bindings += [('case shared ' + k, v) for k, v in case['shared'].items()]
    checks = [{'role': role, 'binding': b, 'matches_current_bytes': bind(Path(b['path'])) == b}
              for role, b in all_bindings]
    bound_checks.extend(dict(x, source_id=sid) for x in checks)
    missing_top = sorted(set(strict_load(Path(original['output_schema']['path']))['required']) - set(first))
    empty_evidence_dims = [d for d in DIMS if first['dimensions'][d]['value'] in (0, 1) and not first['dimensions'][d]['evidence']]
    strict_packet_evidence_missing = [d for d in DIMS if first['dimensions'][d]['value'] in (0, 1)
        and not any(isinstance(e, dict) and {'pointer', 'quote', 'role'} <= set(e)
                    and e['role'] in ('current', 'context') for e in first['dimensions'][d]['evidence'])]
    artifact_files = sorted(p.name for p in slot.iterdir() if p.is_file())
    facts.append({'source_id': sid, 'original_batch_id': original['batch_id'],
                  'original_assignment': bind(original_path), 'original_batch_expected_N': original['expected_N'],
                  'original_batch_source_ids': original['source_ids'], 'same_packet_as_original_assignment': packet_same,
                  'case': bind(cdir / 'case-assignment.json'), 'first': bind(slot / 'first.json'),
                  'technical_receipt_state': receipt_by_id[sid]['state'], 'terminal_returncode': terminal['returncode'],
                  'thread_id': next(e['thread_id'] for e in events if e['type'] == 'thread.started'),
                  'turn_completed_N': sum(e['type'] == 'turn.completed' for e in events),
                  'requested_model': start['requested_model'], 'requested_reasoning_effort': start['requested_reasoning_effort'],
                  'dispatch_argv': start['argv'], 'material_logged_stdout': material_outputs,
                  'logged_truncation_marker_events': trunc_events,
                  'actual_model_tool_message_budget_and_presented_ranges': 'not recorded in available CLI JSON events',
                  'first_read_manifest_present': 'read_manifest' in first,
                  'original_schema_missing_required_top_keys': missing_top,
                  'empty_packet_evidence_dimensions': empty_evidence_dims,
                  'original_pointer_quote_role_missing_dimensions': strict_packet_evidence_missing,
                  'all_values_exact_integer_zero_one_or_null': all(z['value'] is None or type(z['value']) is int and z['value'] in (0, 1) for z in first['dimensions'].values()),
                  'all_reasons_nonempty': all(isinstance(z['reason'], str) and z['reason'].strip() for z in first['dimensions'].values()),
                  'quote_audit': quotes, 'declared_evidence_locations': declared_locations,
                  'image_read_claims': claims, 'available_event_item_types': sorted({e.get('item', {}).get('type') for e in events if 'item' in e}),
                  'commands': command_inventory, 'attempt_files': artifact_files,
                  'original_report_and_seal_missing': [name for name in ('report.txt', 'seal.json') if name not in artifact_files],
                  'binding_checks': checks})

intervals = []
for entry in all_concurrency:
    if entry['last_dated_stderr_utc']:
        start = datetime.fromisoformat(entry['start_utc']).timestamp()
        last = datetime.fromisoformat(entry['last_dated_stderr_utc'].replace('Z', '+00:00')).timestamp()
        intervals += [(start, 1, entry['source_id']), (last, -1, entry['source_id'])]
running = set()
max_running = 0
proof = None
for stamp, delta, sid in sorted(intervals, key=lambda x: (x[0], x[1])):
    if delta > 0:
        running.add(sid)
    else:
        running.discard(sid)
    if len(running) > max_running:
        max_running = len(running)
        proof = {'at_utc': datetime.fromtimestamp(stamp, timezone.utc).isoformat(), 'source_ids': sorted(running)}
save('case-evidence-audit.json', {'source_N': 35, 'records': facts})
save('quote-exactness-audit.json', {'quote_N': len(all_quotes), 'quotes': all_quotes,
                                  'meaning': 'Literal byte/text provenance check only. It does not adjudicate dimension labels or permitted semantic scope.'})
save('concurrency-evidence.json', {'known_live_intervals': all_concurrency, 'maximum_proven_concurrent_processes': max_running,
                                    'maximum_example': proof, 'dispatcher_max_workers': 4,
                                    'frozen_common_protocol_max_concurrency': 3})
save('binding-readback.json', {'binding_check_N': len(bound_checks), 'mismatch_N': sum(not x['matches_current_bytes'] for x in bound_checks),
                              'checks': bound_checks, 'target_packets_match_original_assignments_N': sum(x['same_packet_as_original_assignment'] for x in facts)})

summary = {
    'source_N': len(facts), 'technical_valid_N_in_new_receiver': reception['technical_valid_N'],
    'terminal_zero_returncode_N': sum(x['terminal_returncode'] == 0 for x in facts),
    'strict_json_parse_ok_N': len(facts),
    'same_target_packet_as_original_assignment_N': sum(x['same_packet_as_original_assignment'] for x in facts),
    'current_binding_mismatch_N': sum(not x['matches_current_bytes'] for x in bound_checks),
    'all_complete_manual_prompt_protocol_packet_logged_stdout_N': sum(all(x['material_logged_stdout'][k]['complete_text_in_logged_stdout'] for k in ('manual', 'execution_prompt', 'common_execution_protocol', 'packet')) for x in facts),
    'logged_truncation_marker_case_N': sum(bool(x['logged_truncation_marker_events']) for x in facts),
    'original_schema_incompatible_N': sum(bool(x['original_schema_missing_required_top_keys']) for x in facts),
    'read_manifest_absent_N': sum(not x['first_read_manifest_present'] for x in facts),
    'report_and_seal_absent_N': sum(bool(x['original_report_and_seal_missing']) for x in facts),
    'records_with_empty_evidence_for_non_null_dimension_N': sum(bool(x['empty_packet_evidence_dimensions']) for x in facts),
    'non_null_dimensions_with_empty_evidence_N': sum(len(x['empty_packet_evidence_dimensions']) for x in facts),
    'original_pointer_quote_role_missing_dimension_N': sum(len(x['original_pointer_quote_role_missing_dimensions']) for x in facts),
    'quote_N': len(all_quotes), 'exact_packet_quote_N': sum(x['status'] == 'exact_frozen_packet_substring' for x in all_quotes),
    'exact_logged_asset_output_quote_N': sum(x['status'] == 'exact_logged_source_output_substring' for x in all_quotes),
    'not_found_quote_N': sum(x['status'] == 'not_found_in_allowed_observable_text' for x in all_quotes),
    'image_read_claim_case_N': len({x['source_id'] for x in all_image_claims}),
    'maximum_proven_concurrent_processes': max_running,
    'unique_original_batch_N': len({x['original_batch_id'] for x in facts}),
    'service_model_identity_independently_verified': False,
    'actual_model_message_untruncated_full_read_independently_verified': False,
    'semantic_labels_audited_or_modified': False,
    'model_rerun_performed': False,
}
manual = ROOT / '03-manual/full4481-common-release-20261010-root/manual.txt'
prompt = manual.parent / 'execution-prompt.txt'
protocol = manual.parent / 'common-execution-protocol.txt'
actor = ORIGINAL / 'actor-instructions.txt'
validator = ORIGINAL / 'validate-structured-batch.py'
receiver = ORIGINAL / 'receive_full4481_batch.py'
comparisons = [
 {'item': 'Frozen rule and target packet bytes', 'result': 'matches_observable_bindings',
  'original_requirement': 'Use bound same-version manual, prompt and packet; do not change input bytes.',
  'observed': 'All 35 case packets equal their original batch bindings; all current checked recovery bindings match bytes.',
  'evidence': [citation(actor, 1), citation(actor, 5), citation(RUNNER, 63), {'audit_artifact': 'binding-readback.json'}]},
 {'item': 'Batch/context/selection identity', 'result': 'changed_not_original_protocol',
  'original_requirement': 'Existing frozen batch order and context_unit=batch; each fresh actor submits one full assigned batch; no first-unit assembly.',
  'observed': '35 individually selected records from original batches were run source-at-a-time with fresh CLI threads and targeted artifact type.',
  'evidence': [citation(protocol, 11), citation(actor, 1), citation(actor, 15), citation(RUNNER, 48), citation(RUNNER, 57)]},
 {'item': 'Concurrency', 'result': 'observed_exceeds_frozen_maximum',
  'original_requirement': 'At most 3 concurrent batches.', 'observed': f'New dispatcher permits 4, and dated trace proves at least {max_running} concurrent processes.',
  'evidence': [citation(protocol, 11), citation(RUNNER, 100), {'audit_artifact': 'concurrency-evidence.json'}]},
 {'item': 'Complete material presentation and truncation', 'result': 'complete_logged_stdout_but_missing_required_read_receipt',
  'original_requirement': 'Actual complete untruncated bounded model presentation, range/event/method/source_id read_manifest; loading/hash is not reading.',
  'observed': 'Each trace contains complete manual, prompt, protocol and packet strings; no stdout truncation markers found. All first files lack read_manifest. Available CLI events omit actual model tool-message budgets and cannot rule out feedback/context truncation.',
  'evidence': [citation(protocol, 7), citation(actor, 7), citation(actor, 9), citation(validator, 109), citation(validator, 139), {'audit_artifact': 'case-evidence-audit.json'}]},
 {'item': 'Evidence for zero and one decisions', 'result': 'changed_and_actual_noncompliance',
  'original_requirement': 'Every 0/1 has at least one exact packet string quote with pointer and current/context role.',
  'observed': 'New prompt explicitly permits empty evidence for zero. Six records contain 22 such non-null dimensions. All 175 dimensions lack the original pointer/quote/role schema combination.',
  'evidence': [citation(actor, 13), citation(RUNNER, 57), {'audit_artifact': 'case-evidence-audit.json'}]},
 {'item': 'Source quote exactness', 'result': 'no_observed_literal_quote_fabrication_but_not_original_schema',
  'original_requirement': 'Packet exact field substring; additional asset evidence explicitly bound and genuinely read.',
  'observed': '232 of 234 quote occurrences are exact frozen packet substrings. Two additional RECODE25-03047 quotes are exact stdout substrings from pdftotext pages 14–15 of the packet-bound original PDF, not packet-string substrings. This checks literal provenance only, not semantic sufficiency.',
  'evidence': [citation(actor, 13), citation(validator, 98), {'audit_artifact': 'quote-exactness-audit.json'}]},
 {'item': 'Image/source asset read claims', 'result': 'unverified_in_available_event_capture',
  'original_requirement': 'Actually open necessary image/source asset before reporting read; actual image/page event and range recorded.',
  'observed': 'Five records claim image read/check/verification in first.json; available JSON events contain only command and agent-message items and no image presentation receipt. RECODE25-03876 additionally hashes image bytes but hashing is not visual reading. Absence in this capture is not proof that no image tool call occurred.',
  'evidence': [citation(actor, 7), citation(actor, 9), {'audit_artifact': 'case-evidence-audit.json'}]},
 {'item': 'Output structure and original technical receiver', 'result': 'not_compatible_with_original_reception',
  'original_requirement': 'Frozen run/batch/scope/context identifiers, ordered records, read_manifest, report.txt, seal.json; strict whole-batch reception.',
  'observed': 'All 35 use targeted single-source top structure and lack original required fields, read_manifest, report and seal. They were accepted by a new thin receiver, not the frozen whole-batch receiver.',
  'evidence': [citation(actor, 13), citation(actor, 15), citation(actor, 19), citation(receiver, 81), citation(RUNNER, 78), citation(RUNNER, 88)]},
 {'item': 'Receiver assurance strength', 'result': 'new_receiver_does_not_establish_original_validity',
  'original_requirement': 'Reject duplicate keys/nonfinite values, exact integer labels, schema identity/order/coverage, quote fields and declared reading.',
  'observed': 'New receiver checks input binding equality and shallow dimension types only; it does not validate exact quote/pointer/read coverage/report/seal/thread/terminal integrity. Membership check also admits bool/float values in principle; actual audited files are strict JSON with integer 0/1/null and nonempty reasons.',
  'evidence': [citation(validator, 10), citation(validator, 64), citation(validator, 96), citation(RUNNER, 82), citation(RUNNER, 88)]},
 {'item': 'Independent inputs and raw output preservation', 'result': 'supported_within_observable_scope',
  'original_requirement': 'No reference/metric/other predictions; inputs read-only; preserve actual originals.',
  'observed': 'Dispatch disables user config/memory/web/delegation and uses ephemeral contexts. Logged commands show supplied inputs and packet-declared assets; no observed reference/metric/other-output reads. Each case has one attempt and exclusive first creation recorded. This does not independently inspect hidden transport behavior.',
  'evidence': [citation(actor, 5), citation(RUNNER, 50), citation(RUNNER, 70), {'audit_artifact': 'case-evidence-audit.json'}]},
 {'item': 'Model request versus service identity', 'result': 'request_verified_service_identity_unverified',
  'original_requirement': 'Request gpt-6.1-sol/ultra and retain request evidence; do not claim service identity proven by file hashes.',
  'observed': 'All 35 dispatch argv/start records request gpt-6.1-sol and ultra. CLI thread/usage events and self-reported first metadata do not attest serving model identity; no provider wire response or authoritative server model identity is in these files.',
  'evidence': [citation(protocol, 7), citation(actor, 3), citation(RUNNER, 70), citation(RUNNER, 71)]},
]
save('protocol-comparison.json', {'comparisons': comparisons})
empty = [{'source_id': x['source_id'], 'dimensions': x['empty_packet_evidence_dimensions']} for x in facts if x['empty_packet_evidence_dimensions']]
report = {'artifact_type': 'native35_independent_protocol_audit', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'Read-only protocol and trace audit of existing 35-record coverage recovery. No label adjudication, model rerun or input modification.',
          'conclusion': '35/35 new thin technical receipts do not establish compliance with the frozen full4481 batch protocol. All 35 are a separate, changed-protocol development recovery.',
          'summary': summary, 'empty_evidence_cases': empty, 'findings': comparisons,
          'usable_for': ['Archival record of the separate source-at-a-time diagnostic recovery and its returned labels.',
                         'Development diagnostics explicitly naming original-partial plus changed-protocol recovery, and reporting unresolved reading/asset/identity assurance.',
                         'Trace, material binding and literal quote provenance review; identifying items requiring further documented verification.'],
          'not_usable_for': ['Frozen original full4481 canonical batch first submission or filling original batch first files.',
                             'Claiming a single original first-pass full-corpus run or identical batch-context procedure.',
                             'Independent repeat/stability estimate, formal holdout validity, human reliability, or proof of semantic correctness.',
                             'Claiming actual serving model identity, provider raw network response, or independently proven full untruncated model/image reading.'],
          'necessary_next_steps': ['Keep these 35 originals and the new technical receipt unchanged and separately identified.',
                                   'For existing diagnostic use, present this protocol deviation/read-assurance audit beside the metrics and separate the 42 original predictions from the 35 recovery predictions.',
                                   'If frozen-protocol-compatible production evidence is required, authorize a new separately frozen execution with the original complete batch assignments/prompt/schema/assets, max 3 concurrency, genuine bounded reading receipts and original strict reception. Do not patch these first answers or reopen exhausted original retries as if nothing changed.',
                                   'If claiming image/source verification or complete actual model presentation, obtain attributable actual presentation records; otherwise keep those claims unverified.'],
          'audit_output_directory': str(OUT), 'input_seal': 'input-seal.json',
          'no_original_or_label_write': True, 'no_model_execution': True}
save('report.json', report)

lines = [
 '# 35条补跑：独立流程审查', '',
 '结论：**35/35仅通过新补跑接收器的薄技术检查，不能据此认定符合原冻结全量4481整批流程。35条均应保留为另一次、已改变流程的开发覆盖补跑。**', '',
 '本审查只读冻结合同、补跑脚本与35条既有记录；没有改标签、改原件、运行模型、调用原接收器或写其他目录。范围是流程与可观察证据，未裁定五维标签的语义正确性。', '',
 '## 逐项结论', '',
 '| 项目 | 实际证据 | 判断 |', '|---|---|---|',
 '| 冻结材料字节 | 35个目标packet均与原batch assignment路径/字节/SHA相同；'+str(summary['current_binding_mismatch_N'])+'项当前绑定不一致 | 目标材料版本保持 |',
 '| batch及上下文 | 原为既定整批、每批新上下文；补跑把'+str(summary['unique_original_batch_N'])+'个原batch中的35条改为逐条独立CLI线程 | 原batch与选择单位已改变 |',
 '| 并发 | 原最多3；脚本允许4；时间日志保守证明最多至少'+str(max_running)+'进程重叠 | 超出冻结上限 |',
 '| 完整文字呈现 | 35条events的aggregated_output均含完整手册/提示/协议/packet；未发现stdout截断标记 | 完整日志输出可核；模型所见未截断仍未独立核实 |',
 '| 读取收据 | 35条均无read_manifest，未记录原要求的实际范围/事件/方法/source_id | 未满足原交付合同 |',
 '| 每维证据 | 6条共22个非null维度证据为空；175维均未采用原pointer/quote/current-context role组合 | 原证据要求被改变 |',
 '| 引文精确性 | 234处引文：232处逐字对应绑定packet，2处对应同次PDF提取stdout | 未发现直接可证的引文改写；不等于语义有效 |',
 '| 图页已读声明 | 5条包含image read/check/verified声明；可用JSON事件未保存图像实际呈现回执，03876另有图像SHA读取 | 无法独立确认；SHA不是视觉阅读 |',
 '| 输出与接收 | 35条均不兼容原schema；缺整批身份、records、read_manifest、report、seal；仅经新receiver接收 | 不能回填原canonical batch |',
 '| 请求模型 | 35条argv请求gpt-6.1-sol/ultra | 请求已核；实际服务模型身份未核 |', '',
 '## 核心证据', '',
 f'- [共同协议第11行]({protocol}:11)冻结既定静态batch、最多12条、260000 packet字节、最多3并发，保留首个完整整批技术有效提交；[actor说明第15行]({actor}:15)禁止拆成first-unit再汇总。补跑脚本[第48–57行]({RUNNER}:48)改为one source only，采用targeted_native_coverage_recovery_first；manifest也明确它不能与原主运行合称一次首次全量运行。',
 f'- [actor说明第7、9行]({actor}:7)要求完整且未截断的实际呈现及read_manifest；[共同协议第7行]({protocol}:7)明确程序加载和SHA不是模型阅读。35条事件确有完整原文stdout，但记录不含实际工具反馈预算/模型呈现区间，也无first内读取收据。不能从完整stdout推断服务模型一定看全；同样不能反向把没有截断标记说成已发生截断。',
 f'- [actor说明第13行]({actor}:13)及原schema要求每个0/1至少一条packet逐字证据；补跑[第57行]({RUNNER}:57)明确允许0的evidence为空。新接收器[第82–88行]({RUNNER}:82)只验绑定、维度集合、值成员及reason/evidence类型，不验来源引文、实际读取、report/seal、严格整数或duplicate keys；本审查另核当前35文件均为严格可解析JSON、175个值均为整数0/1/null，理由非空。',
 f'- [原validator第98–105行]({validator}:98)校验packet quote为指定字符串子串及资产绑定，原validator自身也在[第139行]({validator}:139)承认未独立核实真实模型/工具呈现。新接收器的35/35不应升级为更强的流程或语义证明。', '',
 '无证据的22维如下：', '', '| source_id | 空证据维度 |', '|---|---|',
]
lines += ['| ' + x['source_id'] + ' | ' + ', '.join(x['dimensions']) + ' |' for x in empty]
lines += ['',
 '两个非packet引文都属于RECODE25-03047的S/E补充资产证据。事件第20行对packet声明的同一原PDF执行pdftotext物理第14–15页；引文逐字存在于该stdout，原PDF在对应原assignment资产绑定中。它们不是packet字段引文，因此不能以替换字段名的方式假装已经符合原schema。完整字段、实际引用位置、事件行号及哈希见quote-exactness-audit.json与case-evidence-audit.json。', '',
 '图页声明涉及RECODE25-02355、03271、03818、03876、04155。 available JSON日志仅有command_execution及agent_message项目；这类日志可能不完整记录图像工具呈现，故结论是未核实，而非断言未读或伪造。03876有asset.read_bytes/SHA动作及actual_read=true声明，字节校验本身不能证明视觉阅读。', '',
 '## 具体可用用途与必要下一步', '',
 '可用于单独归档此次逐条覆盖补跑、对这35条做开发诊断、核对材料字节与逐字引文；诊断指标必须清楚披露由42条原预测与35条改变流程的补跑组成，并保留未核实的读取/图页/服务身份边界。', '',
 '不可作为原冻结4481主运行的完整整批首答、原canonical batch回填、同一首次全量运行、独立重复/稳定性样本、正式holdout效度或真人信度证据；也不能据它证明语义正确、实际服务模型身份或模型完整未截断阅读。', '',
 '保留35条及薄技术回执原字节，不补写它们的首答或标签。若需要满足冻结生产流程的证据，下一步应另行授权并冻结新执行：使用原完整batch assignment/提示/schema/绑定资产、最多3并发、真实有界读取收据和原严格整批接收；原已终结attempt不能被覆盖或追写成原流程成功。当前审查不执行重跑。', '',
 '## 审查文件与哈希', '',
 '- report.json：机器可读结论、用途及限制。',
 '- protocol-comparison.json：逐项冻结要求与实际证据。',
 '- case-evidence-audit.json：35条逐条材料stdout区间、命令、缺失字段、证据定位与图页声明。',
 '- quote-exactness-audit.json、concurrency-evidence.json、binding-readback.json：可复核事实。',
 '- input-seal.json、input-integrity-readback.json、output-seal.json：输入前后SHA核对及审查输出哈希；output-seal不自包含。', '',
 '服务模型身份：只验证请求为gpt-6.1-sol/ultra。没有provider wire/权威服务器模型标识；first.json及SHA均不能提升为该身份的独立证明。', '',
]
with (OUT / 'report.md').open('x', encoding='utf8') as f:
    f.write('\n'.join(lines))
after = [bind(Path(x['path'])) for x in before]
changes = [{'before': old, 'after': new} for old, new in zip(before, after)
           if any(old[k] != new[k] for k in ('path', 'bytes', 'sha256'))]
save('input-integrity-readback.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'input_N': len(before),
                                      'changed_input_N': len(changes), 'changes': changes,
                                      'all_input_bytes_unchanged_during_audit_computation': not changes})
outputs = [bind(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'output-seal.json']
save('output-seal.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
                          'meaning': 'SHA seal of every audit output except this seal itself; input originals are unchanged.',
                          'output_N': len(outputs), 'files': outputs})
print(json.dumps(summary, ensure_ascii=False, indent=2))
