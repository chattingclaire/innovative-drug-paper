#!/usr/bin/env python3
"""Finite constructed creation controls. All fixture UUIDs/times are synthetic."""
import copy
import json
from pathlib import Path
import creation_bridge as bridge

HOME = Path(__file__).resolve().parent
ROOT_ID = '00000000-0000-4000-8000-000000000001'
ROOT_TURN = '00000000-0000-4000-8000-000000000002'
CHILD_ID = '00000000-0000-4000-8000-000000000003'
CHILD_TURN = '00000000-0000-4000-8000-000000000004'
PATH = '/root/synthetic_control'


def fixture():
    root = {'schemaVersion': 1, 'thread': {'id': ROOT_ID, 'kind': 'codex', 'hostId': 'local', 'createdAt': 10},
            'page': {'order': 'newest_first', 'hasMore': True, 'nextCursor': 'synthetic_old_root_history'},
            'turns': [{'id': ROOT_TURN, 'startedAt': 100, 'status': 'inProgress', 'completedAt': None,
                       'items': [{'type': 'subAgentActivity', 'id': 'synthetic_started_event', 'kind': 'started',
                                  'agentPath': PATH, 'agentThreadId': CHILD_ID}]}]}
    child = {'schemaVersion': 1, 'thread': {'id': CHILD_ID, 'kind': 'codex', 'hostId': 'local',
                                          'createdAt': 200, 'updatedAt': 250},
             'page': {'order': 'newest_first', 'hasMore': False, 'nextCursor': None},
             'turns': [{'id': CHILD_TURN, 'startedAt': 200, 'status': 'inProgress', 'completedAt': None, 'items': []}]}
    def capture(thread, payload):
        return {'request': {'threadId': thread, 'turnLimit': 1, 'includeOutputs': False},
                'observed_start_utc': '1970-01-01T00:05:00Z', 'observed_end_utc': '1970-01-01T00:05:01Z',
                'raw_tool_result': {'isError': False, 'content': [{'type': 'text', 'text': json.dumps(payload)}]}}
    return {'scope': 'constructed_fixture_not_real_dispatch',
            'spawn_request': {'task_name': 'synthetic_control', 'fork_turns': 'none', 'model': 'gpt-6.1-sol',
                              'reasoning_effort': 'ultra', 'message': 'SYNTHETIC NONCODING CONTROL'},
            'spawn_return': {'task_name': PATH}, 'root_read': capture(ROOT_ID, root), 'child_read': capture(CHILD_ID, child)}


def mutate_payload(data, capture_key, callback):
    text = data[capture_key]['raw_tool_result']['content'][0]
    payload = json.loads(text['text'])
    callback(payload)
    text['text'] = json.dumps(payload)


def run():
    cases = []
    def execute(name, mutate, expected_error=None):
        data = fixture()
        mutate(data)
        entry = bridge.save(HOME / 'controls' / 'fixtures' / (name + '.json'), data)
        receipt = {'receipt_version': bridge.VERSION, 'purpose': 'technical_only',
                   'tool': 'collaboration.spawn_agent', 'authority': {'root_thread_id': ROOT_ID,
                       'root_turn_id': ROOT_TURN, 'scheduling_root': str(HOME)},
                   'sources': {key: {'artifact': entry, 'json_pointer': '/' + key}
                               for key in ('spawn_request', 'spawn_return', 'root_read', 'child_read')},
                   'spawn_call_observed_interval': None}
        try:
            request, returned, proof = bridge.verify_receipt(receipt, HOME, ROOT_ID, ROOT_TURN, 'technical_only')
            if expected_error:
                raise AssertionError('control unexpectedly accepted: ' + name)
            assert request == {'model': 'gpt-6.1-sol', 'thinking': 'ultra',
                               'prompt': data['spawn_request']['message'], 'fork_turns': 'none'}
            assert returned['threadId'] == CHILD_ID and proof['actual_provider_wire_telemetry'] is None
            cases.append({'case': name, 'expected': 'accept_creation_only', 'actual': 'accepted', 'pass': True, 'fixture': entry})
        except ValueError as exc:
            assert expected_error and expected_error in str(exc), (name, str(exc))
            cases.append({'case': name, 'expected': 'reject', 'actual': str(exc), 'pass': True, 'fixture': entry})
    execute('01-positive', lambda d: None)
    execute('02-interacted-reuse', lambda d: mutate_payload(d, 'root_read', lambda r: r['turns'][0]['items'][0].update(kind='interacted')), 'interacted/reused')
    execute('03-wrong-model', lambda d: d['spawn_request'].update(model='gpt-6-sol'), 'model/effort differs')
    execute('04-wrong-effort', lambda d: d['spawn_request'].update(reasoning_effort='high'), 'model/effort differs')
    execute('05-fork-all', lambda d: d['spawn_request'].update(fork_turns='all'), 'context fork must be none')
    execute('06-missing-real-return', lambda d: d['spawn_return'].clear(), 'spawn return path differs')
    execute('07-missing-started-event', lambda d: mutate_payload(d, 'root_read', lambda r: r['turns'][0].update(items=[])), 'one unique')
    execute('08-path-uuid-conflict', lambda d: mutate_payload(d, 'root_read', lambda r: r['turns'][0]['items'].append(dict(r['turns'][0]['items'][0], agentThreadId=CHILD_TURN))), 'one unique')
    execute('09-uuid-path-conflict', lambda d: mutate_payload(d, 'root_read', lambda r: r['turns'][0]['items'].append(dict(r['turns'][0]['items'][0], agentPath='/root/another_control'))), 'conflicting agentPaths')
    execute('10-old-created-at', lambda d: mutate_payload(d, 'child_read', lambda c: c['thread'].update(createdAt=99)), 'not created in this observed ROOT turn')
    execute('11-old-turns-hidden', lambda d: mutate_payload(d, 'child_read', lambda c: c['page'].update(hasMore=True, nextCursor='old_turn')), 'earlier turns are hidden')
    execute('12-multiple-child-turns', lambda d: mutate_payload(d, 'child_read', lambda c: c['turns'].append(copy.deepcopy(c['turns'][0]))), 'child is reused')
    execute('13-root-thread-mismatch', lambda d: mutate_payload(d, 'root_read', lambda r: r['thread'].update(id=CHILD_ID)), 'returned a different thread')
    execute('14-root-turn-mismatch', lambda d: mutate_payload(d, 'root_read', lambda r: r['turns'][0].update(id=CHILD_TURN)), 'pinned current ROOT turn')
    execute('15-child-uuid-mismatch', lambda d: mutate_payload(d, 'child_read', lambda c: c['thread'].update(id=ROOT_ID)), 'returned a different thread')
    execute('16-no-actual-message', lambda d: d['spawn_request'].pop('message'), 'full dispatched message absent')
    result = {'scope': '16 finite constructed creation controls; no policy/source/label reads',
              'fixture_identity': 'synthetic, not actual allocation or dispatch', 'cases': cases,
              'all_passed': all(c['pass'] for c in cases), 'original_receiver_called': False,
              'actual_policy_predictions_N': 0, 'provider_wire_telemetry': None}
    bridge.save(HOME / 'controls' / 'constructed-controls.json', result)
    print(json.dumps({'cases': len(cases), 'all_passed': result['all_passed'], 'original_receiver_called': False}))


if __name__ == '__main__':
    run()
