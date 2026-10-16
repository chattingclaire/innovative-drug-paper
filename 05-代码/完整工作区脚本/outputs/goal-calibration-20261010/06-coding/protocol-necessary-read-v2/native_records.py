"""Empty prospective records and mechanical retry gates; no coding/comparison."""
from pathlib import Path
from packet_builder import CONDITIONS, InputFailure, canonical, file_sha, parse, require, valid_sha
from necessary_read_gate import check_scope, dependency_output_projection

TELEMETRY_KEYS = ('actual_provider_model_identity', 'actual_reasoning_configuration',
                  'provider', 'provider_request_id', 'wire_request_sha256', 'temperature',
                  'seed', 'context_window_tokens', 'max_input_tokens', 'max_output_tokens',
                  'token_usage', 'provider_api_call_count')

def blank_ledger():
    return {'protocol_version': 'native-necessary-read-prospective-2', 'state': 'planned_not_executed',
            'assignment': {'requested': {'model': 'gpt-6.1-sol', 'thinking': 'ultra'},
                           'actual_tool_request': None, 'actual_tool_return': None},
            'telemetry': {k: None for k in TELEMETRY_KEYS},
            'plan': {'owner_binding_sha256': None, 'manual_sha256': None,
                     'batching_manifest_sha256': None, 'global_order_sha256': None,
                     'conditions': list(CONDITIONS), 'max_technical_attempts_per_condition_batch': 3,
                     'ordered_batches': [], 'within_batch_history_shared': True,
                     'fresh_thread_per_condition_batch_attempt': True,
                     'necessary_scope_schema_sha256': None, 'uniform_reading_protocol_sha256': None,
                     'externally_frozen_packet_file_bindings': [],
                     'source_sample_selection': None, 'actual_capacity_evidence': None},
            'actual_read_events': [], 'actual_role_message_events': [], 'attempts': [],
            'selections': [], 'model_calls_made_by_preparation': 0,
            'comparison_unlocked': False, 'all_conditions_and_batches_sealed_at': None}

def check_telemetry(ledger):
    require(set(ledger['telemetry']) == set(TELEMETRY_KEYS), 'missing/extra unavailable telemetry field')
    require(all(v is None for v in ledger['telemetry'].values()), 'native provider telemetry must remain unavailable/null')
    require(ledger['assignment']['requested'] == {'model': 'gpt-6.1-sol', 'thinking': 'ultra'}, 'requested allocation differs')

def check_saved_scopes(receipt, expected_packet_files):
    """Recompute finite gate from externally frozen packets and saved first output.

    Complete available inventory does not impose universal actual reading.
    Missing necessary views may stop dependent dimensions with null/requests;
    technical truncation and delivery failures cannot be hidden by those requests.
    """
    require(expected_packet_files, 'externally frozen full-packet file bindings required')
    require(file_sha(receipt['candidate_file']) == receipt['candidate_sha256'], 'saved candidate bytes differ')
    require(file_sha(receipt['read_log_file']) == receipt['read_log_sha256'], 'saved scope manifest bytes differ')
    manifest = parse(Path(receipt['read_log_file']).read_bytes())
    require(set(manifest) == {'scope_log_files'}, 'scope manifest fields differ')
    logs = manifest['scope_log_files']
    require([e['source_id'] for e in logs] == [e['source_id'] for e in expected_packet_files], 'ordered batch scope logs incomplete/different')
    candidate = parse(Path(receipt['candidate_file']).read_bytes())
    require(isinstance(candidate, dict) and isinstance(candidate.get('items'), list) and len(candidate['items']) == len(expected_packet_files), 'first full candidate batch incomplete')
    results = []
    for frozen, entry, item in zip(expected_packet_files, logs, candidate['items']):
        require(file_sha(frozen['path']) == frozen['sha256'], 'externally frozen packet bytes changed')
        packet = parse(Path(frozen['path']).read_bytes())
        require(packet['source_id'] == frozen['source_id'] and packet['source_bundle_sha256'] == frozen['source_bundle_sha256'], 'frozen source/full-bundle binding differs')
        require(item['blind_id'] == packet['output_id'] and item['content_sha256'] == packet['source_bundle_sha256'], 'candidate ordered ID/full-bundle binding differs')
        require(file_sha(entry['path']) == entry['sha256'], 'scope log bytes changed')
        log = parse(Path(entry['path']).read_bytes())
        require(log['reader'] == receipt['thread_id'] and log['run_id'] == receipt['scope_run_id'], 'scope/read events belong to a different native attempt thread/run')
        result = check_scope(packet, log, dependency_output_projection(item))
        require(result['scope_record_valid'], 'necessary read/reference/use/dependency handling unconfirmed')
        results.append(result)
    require(file_sha(receipt['scope_check_file']) == receipt['scope_check_sha256'], 'scope check artifact bytes differ')
    require(canonical(parse(Path(receipt['scope_check_file']).read_bytes())) == canonical(results), 'saved scope check differs from recomputed gate')
    require(receipt['required_read_complete'] is all(r['required_read_complete'] for r in results), 'necessary complete claim differs')
    return results


def select_technical_receipts(receipts, expected_prompt_sha, expected_packet_files):
    """Receipts must come from separately sealed mechanical output checks.

    This does not validate source semantics or candidate labels. All attempts,
    including prohibited attempts after success, are checked and retained.
    """
    require(len(receipts) <= 3, 'too many technical attempts')
    first = None; seen = set(); events = []
    for number, r in enumerate(receipts, 1):
        require(r.get('candidate_is_assembled_from_multiple_attempts', False) is False and not r.get('candidate_piece_attempts'), 'candidate records/dimensions assembled across attempts')
        require(r['attempt'] == number, 'attempt order mismatch')
        require(r['initial_prompt_sha256'] == expected_prompt_sha, 'retry prompt changed')
        require(valid_sha(r['creation_request_artifact_sha256']), 'creation attempt evidence missing')
        if r['state'] == 'creation_failed':
            require(r.get('thread_id') is None, 'creation failure cannot invent thread ID')
        else:
            require(r.get('thread_id') and r['thread_id'] not in seen and r.get('fresh_thread') is True, 'thread reused/unconfirmed')
            seen.add(r['thread_id'])
        require(r.get('additional_user_messages') == [], 'feedback/continuation violates frozen history')
        if first is not None:
            events.append({'attempt': number, 'state': 'protocol_deviation_after_first_valid', 'selected': False})
            continue
        if r['state'] == 'complete_format_valid':
            require(all(valid_sha(r.get(k)) for k in ['candidate_sha256', 'candidate_seal_sha256', 'format_check_artifact_sha256', 'read_log_sha256', 'history_log_sha256', 'scope_check_sha256']), 'sealed candidate/read/check binding missing')
            require(r.get('known_input_truncation') is False and r.get('known_output_truncation') is False and
                    r.get('known_compaction') is False, 'technical truncation/compaction observed or unconfirmed')
            check_saved_scopes(r, expected_packet_files)
            first = number
        else:
            require(r['state'] in ['creation_failed', 'read_failed', 'input_truncated', 'output_interrupted',
                                   'format_failed', 'completeness_unconfirmed', 'known_compaction'], 'unsupported technical state')
        events.append({'attempt': number, 'state': r['state'], 'selected': first == number})
    return {'selected_attempt': first, 'events': events,
            'state': 'not_executed' if not receipts else 'first_complete_valid' if first else 'no_complete_valid'}

def all_batches_sealed_gate(records, batch_ids, common_binding_sha):
    """Boolean integrity gate only. No actual machine comparison is implemented."""
    expected = {(c, b) for c in CONDITIONS for b in batch_ids}
    require(batch_ids and len(batch_ids) == len(set(batch_ids)), 'batch schedule missing/duplicate')
    require(len(records) == len(expected) and {(r['condition'], r['batch_id']) for r in records} == expected, 'all five conditions and every frozen batch required')
    threads = set()
    for r in records:
        require(r['batching_manifest_sha256'] == common_binding_sha and valid_sha(r['seal_sha256']), 'batching/seal binding differs')
        require(r['state'] in ['first_complete_valid_sealed', 'technical_failure_sealed'], 'selection/failure not sealed')
        if r['state'] == 'first_complete_valid_sealed':
            require(valid_sha(r['selected_candidate_sha256']) and r['attempt_thread_ids'], 'selected candidate/thread evidence missing')
        for t in r['attempt_thread_ids']:
            require(t and t not in threads, 'cross-condition/batch thread reuse')
            threads.add(t)
    return True
