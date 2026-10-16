"""Empty prospective records and mechanical retry gates; no coding/comparison."""
from packet_builder import CONDITIONS, InputFailure, require, valid_sha

TELEMETRY_KEYS = ('actual_provider_model_identity', 'actual_reasoning_configuration',
                  'provider', 'provider_request_id', 'wire_request_sha256', 'temperature',
                  'seed', 'context_window_tokens', 'max_input_tokens', 'max_output_tokens',
                  'token_usage', 'provider_api_call_count')

def blank_ledger():
    return {'protocol_version': 'native-full-source-prospective-1', 'state': 'planned_not_executed',
            'assignment': {'requested': {'model': 'gpt-6.1-sol', 'thinking': 'ultra'},
                           'actual_tool_request': None, 'actual_tool_return': None},
            'telemetry': {k: None for k in TELEMETRY_KEYS},
            'plan': {'owner_binding_sha256': None, 'manual_sha256': None,
                     'batching_manifest_sha256': None, 'global_order_sha256': None,
                     'conditions': list(CONDITIONS), 'max_technical_attempts_per_condition_batch': 3,
                     'ordered_batches': [], 'within_batch_history_shared': True,
                     'fresh_thread_per_condition_batch_attempt': True,
                     'source_sample_selection': None, 'actual_capacity_evidence': None},
            'actual_read_events': [], 'actual_role_message_events': [], 'attempts': [],
            'selections': [], 'model_calls_made_by_preparation': 0,
            'comparison_unlocked': False, 'all_conditions_and_batches_sealed_at': None}

def check_telemetry(ledger):
    require(set(ledger['telemetry']) == set(TELEMETRY_KEYS), 'missing/extra unavailable telemetry field')
    require(all(v is None for v in ledger['telemetry'].values()), 'native provider telemetry must remain unavailable/null')
    require(ledger['assignment']['requested'] == {'model': 'gpt-6.1-sol', 'thinking': 'ultra'}, 'requested allocation differs')

def select_technical_receipts(receipts, expected_prompt_sha):
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
            require(all(valid_sha(r.get(k)) for k in ['candidate_sha256', 'candidate_seal_sha256', 'format_check_artifact_sha256', 'read_log_sha256', 'history_log_sha256']), 'sealed candidate/read/check binding missing')
            require(r.get('known_input_truncation') is False and r.get('known_output_truncation') is False and
                    r.get('known_compaction') is False and r.get('visible_read_complete') is True, 'visible complete delivery unconfirmed')
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
