#!/usr/bin/env python3
"""ROOT creation provenance preflight, then the unchanged sealed native receiver.

This module dispatches no actors and reads no source/label files during preflight.
The evidence boundary is actual ROOT-owned logical tool records, not provider wire.
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
VERSION = 'native-collaboration-creation-bridge-1'
PURPOSES = ('technical_only', 'native_coding_creation')


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def identify(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def checked(entry, external_root=None):
    path = Path(entry['path'])
    need(path.is_absolute(), 'artifact path must be absolute')
    actual = identify(path)
    need(actual == entry, 'artifact path/bytes/SHA binding differs: ' + str(path))
    if external_root is not None:
        need(Path(actual['path']).is_relative_to(external_root), 'creation evidence is outside ROOT scheduling namespace')
    return parse(Path(actual['path']).read_bytes())


def at(value, pointer):
    if pointer == '':
        return value
    need(isinstance(pointer, str) and pointer.startswith('/'), 'invalid JSON pointer')
    for part in pointer[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def canonical_uuid(value):
    need(isinstance(value, str) and str(uuid.UUID(value)) == value, 'noncanonical UUID')
    return value


def unix(value):
    need(type(value) is int and value >= 0, 'app lifecycle timestamp must be integer Unix seconds')
    return value


def observed(value):
    need(isinstance(value, str), 'actual app read observation time absent')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(parsed.tzinfo is not None, 'observation time needs timezone')
    return parsed.timestamp()


def load_ref(ref, external_root):
    return at(checked(ref['artifact'], external_root), ref['json_pointer'])


def app_read(ref, external_root, expected_thread):
    capture = load_ref(ref, external_root)
    need(capture['request']['threadId'] == expected_thread, 'actual app read request thread differs')
    need(not capture['raw_tool_result'].get('isError', False), 'actual app read failed')
    payload = at(capture['raw_tool_result'], ref.get('payload_pointer', '/content/0/text'))
    payload = parse(payload) if isinstance(payload, str) else payload
    need(payload['schemaVersion'] == 1 and payload['thread']['kind'] == 'codex', 'unsupported app read payload')
    need(payload['thread']['id'] == expected_thread, 'actual app read returned a different thread')
    start, end = observed(capture['observed_start_utc']), observed(capture['observed_end_utc'])
    need(start <= end, 'app read observation interval reversed')
    need(payload['page']['order'] == 'newest_first', 'app turn order unavailable')
    return payload, start, end


def verify_receipt(receipt, external_root, expected_root_thread, expected_root_turn, purpose):
    """Validate actual current-turn creation. Exact spawn duration may remain null.

    A started event alone, UUID novelty alone, or a readable child alone is insufficient.
    The conjunction binds the dispatch's returned path to the actual ROOT turn and
    new child lifecycle, with a complete child turn page showing no old context.
    """
    external_root = Path(external_root).resolve()
    canonical_uuid(expected_root_thread)
    canonical_uuid(expected_root_turn)
    need(purpose in PURPOSES and receipt['purpose'] == purpose, 'ROOT purpose differs')
    need(receipt['receipt_version'] == VERSION, 'unsupported creation receipt version')
    authority = receipt['authority']
    need(authority == {'root_thread_id': expected_root_thread, 'root_turn_id': expected_root_turn,
                       'scheduling_root': str(external_root)}, 'external ROOT thread/turn/namespace differs')
    need(receipt['tool'] == 'collaboration.spawn_agent', 'not an actual spawn receipt')
    sources = receipt['sources']
    need(set(sources) == {'spawn_request', 'spawn_return', 'root_read', 'child_read'}, 'creation source set differs')
    request = load_ref(sources['spawn_request'], external_root)
    returned = load_ref(sources['spawn_return'], external_root)
    need(request.get('model') == 'gpt-6.1-sol' and request.get('reasoning_effort') == 'ultra',
         'actual requested model/effort differs')
    need(request.get('fork_turns') == 'none', 'actual context fork must be none')
    need(isinstance(request.get('message'), str) and request['message'], 'actual full dispatched message absent')
    name = request.get('task_name')
    need(isinstance(name, str) and name and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in name), 'task name invalid')
    path = '/root/' + name
    need(returned.get('task_name') == path, 'actual spawn return path differs')
    root, root_start, root_end = app_read(sources['root_read'], external_root, expected_root_thread)
    turns = root['turns']
    need(isinstance(turns, list) and turns and turns[0]['id'] == expected_root_turn,
         'creation event is not from the pinned current ROOT turn')
    need(len([t for t in turns if t['id'] == expected_root_turn]) == 1, 'ROOT turn duplicated')
    turn = turns[0]
    root_turn_start = unix(turn['startedAt'])
    need(unix(root['thread']['createdAt']) <= root_turn_start <= math.floor(root_start), 'ROOT lifecycle/observation differs')
    need(turn['status'] in ('inProgress', 'completed'), 'ROOT creation turn failed/interrupted')
    activities = [i for t in turns for i in t['items'] if i.get('type') == 'subAgentActivity']
    targeted = [i for i in turn['items'] if i.get('type') == 'subAgentActivity' and i.get('agentPath') == path]
    need(len(targeted) == 1, 'creation needs one unique current ROOT agentPath event')
    event = targeted[0]
    need(event.get('kind') == 'started' and isinstance(event.get('id'), str) and event['id'],
         'interacted/reused actor or absent actual new started event')
    thread = canonical_uuid(event.get('agentThreadId'))
    need(thread != expected_root_thread, 'child UUID equals ROOT UUID')
    need(all(i.get('agentThreadId') == thread for i in activities if i.get('agentPath') == path), 'agentPath maps to conflicting UUIDs')
    need(all(i.get('agentPath') == path for i in activities if i.get('agentThreadId') == thread), 'UUID maps to conflicting agentPaths')
    need(len([i for i in activities if i.get('agentPath') == path]) == 1, 'agentPath has earlier/repeated interaction')
    child, child_start, child_end = app_read(sources['child_read'], external_root, thread)
    page = child['page']
    need(page['hasMore'] is False and page['nextCursor'] is None, 'child earlier turns are hidden/unconfirmed')
    need(len(child['turns']) == 1, 'child is reused or first turn unavailable')
    first = child['turns'][0]
    canonical_uuid(first['id'])
    created, started = unix(child['thread']['createdAt']), unix(first['startedAt'])
    need(root_turn_start <= created <= math.floor(root_start), 'child was not created in this observed ROOT turn')
    need(created <= started <= math.floor(child_start), 'child first-turn lifecycle/observation differs')
    need(unix(child['thread']['updatedAt']) >= created, 'child update precedes creation')
    need(first['status'] in ('inProgress', 'completed'), 'child initial turn failed/interrupted')
    need(child['thread']['hostId'] == root['thread']['hostId'], 'ROOT and child host differ')
    need(not any(i.get('type') == 'userMessage' for i in first['items']), 'additional child user message observed')
    timing = receipt.get('spawn_call_observed_interval')
    if timing is not None:
        start, end = observed(timing['start_utc']), observed(timing['end_utc'])
        need(root_turn_start <= start <= end <= root_end, 'spawn observation interval differs')
        need(math.floor(start) <= created <= math.floor(end), 'creation outside actual recorded spawn interval')
    normal_request = {'model': request['model'], 'thinking': request['reasoning_effort'],
                      'prompt': request['message'], 'fork_turns': request['fork_turns']}
    normal_return = {'threadId': thread, 'hostId': child['thread']['hostId'],
                     'creation_transport': 'collaboration.spawn_agent', 'agentPath': path}
    proof = {'bridge_version': VERSION, 'purpose': purpose,
             'state': 'creation_only_confirmed', 'fresh_in_observed_current_root_turn': True,
             'root_thread_id': expected_root_thread, 'root_turn_id': expected_root_turn,
             'root_turn_started_at': root_turn_start, 'agent_path': path, 'started_event_id': event['id'],
             'child_thread_id': thread, 'child_created_at': created, 'child_first_turn_id': first['id'],
             'child_first_turn_started_at': started, 'child_turn_page_has_more': False,
             'actual_requested': {'model': request['model'], 'reasoning_effort': request['reasoning_effort'], 'fork_turns': 'none'},
             'actual_message_sha256': hashlib.sha256(request['message'].encode()).hexdigest(),
             'actual_message_bytes': len(request['message'].encode()),
             'spawn_call_observed_interval': timing, 'actual_provider_wire_telemetry': None,
             'root_read_observed_interval_unix': [root_start, root_end],
             'child_read_observed_interval_unix': [child_start, child_end],
             'sources': sources, 'original_receiver_called': False,
             'policy_prediction_or_first_output_certified': False,
             'scope_read_history_compaction_first_attempt_cap_and_Gold_guards_evaluated': False}
    return normal_request, normal_return, proof


def load_binding(path, sha):
    actual = identify(path)
    need(actual['sha256'] == sha, 'bridge binding SHA differs')
    binding = checked(actual)
    need(binding['bridge_version'] == VERSION, 'bridge binding version differs')
    need(Path(binding['bridge_source']['path']).resolve() == Path(__file__).resolve(), 'loaded bridge path differs')
    need(identify(binding['bridge_source']['path']) == binding['bridge_source'], 'bridge source bytes/SHA differ')
    for entry in binding['original_components'].values():
        # Hash only: no loading scope, policy source, manual, or prediction modules.
        need(identify(entry['path']) == entry, 'original component changed: ' + entry['path'])
    return binding


def save(path, value):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
    return identify(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('mode', choices=('preflight', 'receive'))
    for key in ('receipt', 'receipt-sha', 'binding', 'binding-sha', 'scheduling-root',
                'root-thread', 'root-turn', 'purpose'):
        parser.add_argument('--' + key, required=True)
    parser.add_argument('--report')
    parser.add_argument('--normalized-dir')
    parser.add_argument('--native-args-file')
    parser.add_argument('--native-args-sha')
    args = parser.parse_args()
    binding = load_binding(args.binding, args.binding_sha)
    receipt_entry = identify(args.receipt)
    need(receipt_entry['sha256'] == args.receipt_sha, 'creation receipt SHA differs')
    receipt = checked(receipt_entry)
    need(Path(args.receipt).resolve().is_relative_to(Path(args.scheduling_root).resolve()), 'receipt outside ROOT scheduling namespace')
    normal_request, normal_return, proof = verify_receipt(receipt, args.scheduling_root,
                                                        args.root_thread, args.root_turn, args.purpose)
    proof['receipt_artifact'] = receipt_entry
    proof['bridge_binding'] = identify(args.binding)
    if args.mode == 'preflight':
        need(args.report, 'preflight report path required')
        result = save(args.report, proof)
        save(str(args.report) + '.seal.json', {'files': [result], 'creation_only': True,
                                             'original_receiver_called': False, 'provider_telemetry': None})
        print(json.dumps({'state': proof['state'], 'purpose': args.purpose, 'report': result}))
        return
    need(args.purpose == 'native_coding_creation', 'technical_only context cannot be submitted to native receiver')
    need(args.normalized_dir and args.native_args_file and args.native_args_sha, 'receive normalization/native arguments required')
    out = Path(args.normalized_dir).resolve()
    schedule = Path(args.scheduling_root).resolve()
    need(out.is_relative_to(schedule) and not out.exists(), 'normalization requires a new ROOT scheduling directory')
    native_entry = identify(args.native_args_file)
    need(native_entry['sha256'] == args.native_args_sha, 'native argument artifact SHA differs')
    need(Path(native_entry['path']).is_relative_to(schedule), 'native arguments outside ROOT scheduling namespace')
    native = checked(native_entry)
    required = {'actor_seal', 'batch', 'attempt', 'report', 'plan', 'plan_sha', 'native_root',
                'report_root', 'runtime_binding', 'runtime_binding_sha', 'scheduling_root'}
    optional = {'technical_evidence', 'initial_prompt_file', 'initial_prompt_sha', 'original_instruction_file',
                'runtime_pointer', 'runtime_evidence_member', 'runtime_evidence_pointer', 'prior_report'}
    need(isinstance(native, dict) and required <= set(native) <= required | optional, 'native argument set differs; creation pointers cannot be overridden')
    need(Path(native['scheduling_root']).resolve() == schedule, 'native scheduling root differs')
    need(type(native['attempt']) is int and 1 <= native['attempt'] <= 3, 'original native max3 retained')
    receiver = binding['original_components']['receiver.py']
    # Original receiver still checks plan, native bindings, actual prompt, UUID,
    # runtime tool evidence, whole seal, first files, scopes, history and prior caps.
    argv = [sys.executable, '-B', receiver['path']]
    for key, value in native.items():
        values = value if key == 'prior_report' else [value]
        need(isinstance(values, list), 'prior_report must be a list')
        for item in values:
            need(type(item) in (str, int) and not str(item).startswith('--'), 'invalid native argument value')
            argv.extend(['--' + key.replace('_', '-'), str(item)])
    out.mkdir(parents=True, exist_ok=False)
    request_entry = save(out / 'normalized-creation-request.json', normal_request)
    return_entry = save(out / 'normalized-creation-return.json', normal_return)
    provenance_entry = save(out / 'creation-provenance.json', proof)
    save(out / 'normalization.seal.json', {'files': [request_entry, return_entry, provenance_entry],
                                         'original_receiver': receiver, 'native_args': native_entry,
                                         'provider_wire_telemetry': None, 'coding_or_metrics_performed_by_bridge': False})
    argv.extend(['--creation-request', request_entry['path'], '--creation-return', return_entry['path'],
                 '--request-pointer', '', '--return-pointer', '', '--thread-pointer', '/threadId'])
    completed = subprocess.run(argv, check=False)
    raise SystemExit(completed.returncode)


if __name__ == '__main__':
    main()
