#!/usr/bin/env python3
"""ROOT-only read-only supplement to the v2 transport receiver.

No model call, no first/label repair, no file writes. Returns a receipt to stdout.
This does not replace or overwrite the existing v2 receiver's receipt.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True

def reject_duplicate_keys(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError('Duplicate JSON object key: ' + k)
        result[k] = v
    return result

def load_strict(path):
    def reject_nonfinite(x):
        raise ValueError('Non-finite JSON value: ' + x)
    return json.loads(Path(path).read_bytes().decode('utf8'), object_pairs_hook=reject_duplicate_keys,
                      parse_constant=reject_nonfinite)

def binding(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def exact(item):
    assert type(item.get('bytes')) is int, 'Input byte count must be exact integer'
    assert binding(item['path']) == {k: item[k] for k in ('path', 'bytes', 'sha256')}, 'Bound file changed'

def verify(manifest_path, assignment_path, submission_path, require_explicit_template_false=False):
    manifest_path = Path(manifest_path).resolve()
    assignment_path = Path(assignment_path).resolve()
    first_path = Path(submission_path).resolve()
    manifest = load_strict(manifest_path)
    assignment = load_strict(assignment_path)
    assert manifest['run_id'] == assignment['run_id'], 'Manifest/assignment run identity mismatch'
    batch = next(x for x in manifest['batches'] if x['batch_id'] == assignment['batch_id'])
    assert batch['assignment'] == binding(assignment_path), 'Assignment outside frozen manifest'
    assert batch['source_ids'] == assignment['source_ids'], 'Manifest/assignment membership/order mismatch'
    exact(assignment['attempt_output_routing'])
    routing = load_strict(assignment['attempt_output_routing']['path'])
    route_matches = [x for x in routing['routes'] if x['batch_id'] == assignment['batch_id']
                     and Path(x['first_path']).resolve() == first_path]
    assert len(route_matches) == 1, 'Submission outside unique assigned attempt route'
    route = route_matches[0]
    assert 1 <= route['attempt_number'] <= manifest['max_total_technical_attempts'] == 3, 'Attempt outside finite recovery budget'
    assert first_path.parent == Path(route['output_directory']).resolve(), 'Slot path mismatch'
    validator_binding = manifest['validator']
    exact(validator_binding)
    assert assignment['strict_technical_validator'] == validator_binding, 'Unfrozen validator identity'
    # Executing the frozen read-only verifier via compile avoids writing __pycache__ in v2.
    module = types.ModuleType('frozen_v2_read_only_validator')
    module.__file__ = validator_binding['path']
    exec(compile(Path(module.__file__).read_bytes(), module.__file__, 'exec'), module.__dict__)
    schema_result = module.verify(assignment_path, first_path)
    first = load_strict(first_path)
    for record in first['records']:
        for dim, decision in record['dimensions'].items():
            value = decision['value']
            assert value is None or type(value) is int and value in (0, 1), 'Exact integer/null value required'
            if value is not None:
                assert any({'pointer', 'quote', 'role'} <= set(e) and e['role'] in ('current', 'context')
                           for e in decision['evidence']), f'{record["source_id"]}/{dim}: 0/1 lacks frozen packet evidence'
    report_path = Path(route['report_path']).resolve()
    seal_path = Path(route['seal_path']).resolve()
    assert report_path.parent == first_path.parent == seal_path.parent, 'Seal/report outside own slot'
    seal = load_strict(seal_path)
    assert seal['run_id'] == assignment['run_id'], 'Actor seal run_id mismatch'
    assert seal['batch_id'] == assignment['batch_id'], 'Actor seal batch_id mismatch'
    # Default follows the original v3 receiver exactly: missing template_only is false.
    # Optional explicit-field mode is stronger and must be frozen before new dispatch.
    if require_explicit_template_false:
        assert 'template_only' in seal, 'Actor seal explicit template_only field absent'
    assert seal.get('template_only', False) is False, 'Uninstantiated actor seal template'
    assert seal.get('actual_completion_claimed') is True, 'Actor seal actual completion is not true'
    assert seal['first_binding'] == binding(first_path), 'Actor first-byte seal mismatch'
    assert seal['report_binding'] == binding(report_path), 'Actor report-byte seal mismatch'
    inputs = seal.get('actual_input_bindings')
    assert isinstance(inputs, list) and inputs, 'Actor actual input bindings absent or empty'
    allowed = {str(assignment_path): binding(assignment_path)}
    for value in assignment.values():
        if isinstance(value, dict) and {'path', 'bytes', 'sha256'} <= set(value):
            allowed[value['path']] = {k: value[k] for k in ('path', 'bytes', 'sha256')}
    for value in [*assignment['packets'], *assignment['source_asset_bindings']]:
        allowed[value['path']] = {k: value[k] for k in ('path', 'bytes', 'sha256')}
    for item in inputs:
        assert isinstance(item, dict) and {'path', 'bytes', 'sha256'} <= set(item), 'Malformed actor actual input binding'
        assert allowed.get(item['path']) == {k: item[k] for k in ('path', 'bytes', 'sha256')}, 'Actor seal input outside frozen assignment'
        exact(item)
    process_path = first_path.parent / 'process-completion.json'
    process = load_strict(process_path)
    assert process.get('actual_process_terminal') is True, 'CLI process is not recorded terminal'
    assert process.get('returncode') == 0 and process.get('timed_out') is False, 'CLI process not cleanly terminal'
    exact(process['events'])
    exact(process['stderr'])
    events = [json.loads(x) for x in Path(process['events']['path']).read_text(encoding='utf8').splitlines()]
    thread_ids = [x['thread_id'] for x in events if x['type'] == 'thread.started']
    assert len(thread_ids) == 1, 'Exactly one fresh CLI thread expected'
    assert sum(x['type'] == 'turn.completed' for x in events) == 1, 'Completed CLI turn absent or duplicated'
    return {'artifact_type': 'ROOT_supplemental_strict_v2_whole_batch_reception',
            'state': 'technical_valid_whole_batch_with_v3_seal_guard',
            'run_id': assignment['run_id'], 'batch_id': assignment['batch_id'],
            'recovery_attempt_number': route['attempt_number'], 'actual_cli_thread_id': thread_ids[0],
            'original_assignment_binding': assignment['original_assignment_binding'],
            'manifest': binding(manifest_path), 'assignment': binding(assignment_path),
            'first': binding(first_path), 'report': binding(report_path), 'actor_seal': binding(seal_path),
            'validator': validator_binding, 'schema_validation': schema_result,
            'seal_flags': {k: seal.get(k, False if k == 'template_only' else None) for k in ('run_id', 'batch_id', 'template_only', 'actual_completion_claimed')},
            'explicit_template_only_present': 'template_only' in seal,
            'actual_input_binding_N': len(inputs),
            'zero_one_exact_packet_evidence_checked': True, 'legal_null_is_terminal_valid': True,
            'semantic_correctness_checked': False, 'reference_or_accuracy_compared': False,
            'actual_model_or_tool_presentations_independently_verified': False,
            'provider_wire_or_serving_model_identity_claimed': False,
            'first_or_labels_modified': False, 'files_written': False,
            'scope': 'Supplemental ROOT nonsemantic reception; does not convert a v2 thin receipt into original campaign success.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--assignment', required=True)
    parser.add_argument('--submission', required=True)
    parser.add_argument('--require-explicit-template-false', action='store_true')
    args = parser.parse_args()
    try:
        result = verify(args.manifest, args.assignment, args.submission, args.require_explicit_template_false)
    except Exception as error:
        print(json.dumps({'artifact_type': 'ROOT_supplemental_strict_v2_whole_batch_reception',
                          'state': 'technical_invalid_whole_batch',
                          'error': {'type': type(error).__name__, 'message': str(error)},
                          'first_or_labels_modified': False, 'files_written': False,
                          'semantic_correctness_checked': False,
                          'legal_null_itself_is_never_a_retry_reason': True}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    sys.exit(main())
