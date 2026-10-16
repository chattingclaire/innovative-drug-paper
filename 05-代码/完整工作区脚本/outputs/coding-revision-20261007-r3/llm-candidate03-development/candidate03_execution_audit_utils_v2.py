"""Audit fixed CLI runs, including explicitly incomplete original runs."""
import hashlib, importlib.util, json, pathlib, sys
from run_and_audit_candidate03_stability import check_events

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(pathlib.Path(p).read_text())
def lines(p): return [json.loads(s) for s in pathlib.Path(p).read_text().splitlines() if s.strip()]
def bind(p): return {'path': str(pathlib.Path(p).resolve()), 'sha256': sha(p)}
def dump(p, x): pathlib.Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')
def canonical_sha(x): return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def event_output_binding(events_path, raw_path):
    final_messages = []
    for line in pathlib.Path(events_path).read_text().splitlines():
        if not line.strip(): continue
        try: event = json.loads(line)
        except ValueError: continue
        item = event.get('item')
        if event.get('type') == 'item.completed' and isinstance(item, dict) and item.get('type') == 'agent_message':
            final_messages.append(item.get('text'))
    result = {'completed_agent_messages': len(final_messages), 'event_final_json_canonical_sha256': None, 'raw_json_canonical_sha256': None, 'event_raw_full_object_equal': False}
    try:
        final = json.loads(final_messages[-1]); result['event_final_json_canonical_sha256'] = canonical_sha(final)
    except (IndexError, TypeError, ValueError) as exc:
        result['event_final_parse_error'] = type(exc).__name__; final = None
    try:
        raw = read(raw_path); result['raw_json_canonical_sha256'] = canonical_sha(raw)
    except (OSError, ValueError) as exc:
        result['raw_parse_error'] = type(exc).__name__; raw = None
    if result['event_final_json_canonical_sha256'] is not None and result['raw_json_canonical_sha256'] is not None:
        result['event_raw_full_object_equal'] = final == raw
    return result

def audit(run, expected_n, batch_size, expected_input_sha, expected_prompt_sha, allowed_terminal_failures):
    if sys.flags.optimize != 0:
        raise RuntimeError('Audit requires Python optimization=0; assertions must remain active.')
    run = pathlib.Path(run); plan = read(run / 'run_plan.json'); summary = read(run / 'execution_summary.json')
    n_batches = (expected_n + batch_size - 1) // batch_size
    assert plan['n'] == expected_n and plan['batch_size'] == batch_size and plan['batch_count'] == n_batches and plan['max_attempts'] == 3
    assert plan['model'] == 'gpt-5.6-sol' and plan['reasoning_effort'] == 'medium'
    assert plan['input_sha256'] == expected_input_sha == sha(run / 'frozen_input.jsonl')
    assert plan['prompt_sha256'] == expected_prompt_sha == sha(run / 'frozen_prompt.txt')
    for k, f in [('schema', 'frozen_schema.json'), ('validator', 'frozen_validator.py'), ('runner', 'frozen_runner.py')]: assert plan[k + '_sha256'] == sha(run / f)
    assert summary['recorded_batch_count'] == summary['expected_batch_count'] == n_batches
    assert summary['source_unchanged_during_run'] and summary['input_sha256'] == expected_input_sha
    assert summary['prompt_sha256'] == expected_prompt_sha and summary['plan_sha256'] == sha(run / 'run_plan.json')
    source = lines(run / 'frozen_input.jsonl'); assert len(source) == expected_n == len({r['id'] for r in source})
    spec = importlib.util.spec_from_file_location('candidate03_audit_validator', run / 'frozen_validator.py')
    v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
    prompt = (run / 'frozen_prompt.txt').read_text(); accepted = {}; attempt_audits = []; batches = []; failed = []
    for bi in range(1, n_batches + 1):
        b = run / 'batches' / f'batch-{bi:04d}'; packet = read(b / 'input.json'); selection = read(b / 'selection.json')
        assert packet == {'rows': source[(bi - 1) * batch_size:bi * batch_size]}
        assert selection['batch'] == bi and selection['input_n'] == len(packet['rows']) and selection['ids'] == [r['id'] for r in packet['rows']]
        request = prompt + '\n\n--- 本批冻结盲法输入 ---\n' + json.dumps(packet, ensure_ascii=False) + '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
        assert (b / 'request.txt').read_text() == request
        attempts = sorted((b / 'attempts').glob('attempt-*')); assert 1 <= len(attempts) <= 3
        assert [a.name for a in attempts] == [f'attempt-{i:02d}' for i in range(1, len(attempts) + 1)]
        assert len(selection['attempts']) == len(attempts); valid_attempts = []
        for ai, a in enumerate(attempts, 1):
            m = read(a / 'run_metadata.json'); saved = read(a / 'validation.json')
            assert read(a / 'input.json') == packet and (a / 'request.txt').read_text() == request
            assert m['ids'] == selection['ids'] and m['input_n'] == len(packet['rows'])
            for k, f in [('input', 'input.json'), ('request', 'request.txt'), ('events', 'events.jsonl'), ('stderr', 'raw_stderr.txt'), ('tool_event_audit', 'tool_event_audit.json'), ('validation', 'validation.json')]: assert m[k + '_sha256'] == sha(a / f)
            assert m['prompt_sha256'] == expected_prompt_sha and m['requested_model'] == 'gpt-5.6-sol' and m['reasoning_effort'] == 'medium'
            assert m['cli_version'] == plan['cli_version'] and m['cli_binary_sha256'] == plan['cli_binary_sha256']
            cmd = m['command']; assert cmd[0] == plan['cli_path'] and cmd[cmd.index('--model') + 1] == 'gpt-5.6-sol'
            assert 'model_reasoning_effort="medium"' in cmd and 'web_search="disabled"' in cmd
            assert all(x in cmd for x in ['--ignore-user-config', '--ignore-rules', '--ephemeral']) and cmd[cmd.index('--sandbox') + 1] == 'read-only'
            ev = check_events(a / 'events.jsonl'); raw = a / 'raw_output.json'
            if raw.exists():
                assert sha(raw) == m['raw_output_sha256']
                try: errors = v.validate(packet, read(raw))
                except Exception as e: errors = [f'{type(e).__name__}:{e}']
            else: errors = ['missing_raw_output']
            valid = m['exit_code'] == 0 and not errors and ev['completed'] == 1 and not ev['violations'] and not ev['turn_errors'] and all(x == 'gpt-5.6-sol' for x in ev['observed_models'])
            output_event_binding = event_output_binding(a / 'events.jsonl', raw)
            if valid: assert output_event_binding['event_raw_full_object_equal'], ('Selected raw must exactly equal the actual final event JSON', str(a), output_event_binding)
            assert valid == saved['valid'] == (m['status'] == 'accepted_structural_literal_zero_tools')
            assert len(ev['violations']) == m['tool_event_count'] == read(a / 'tool_event_audit.json')['tool_or_unknown_item_event_count']
            selected_attempt_record = selection['attempts'][ai - 1]
            assert selected_attempt_record['relative_path'] == str(a.relative_to(run)) and selected_attempt_record['metadata_sha256'] == sha(a / 'run_metadata.json')
            assert selected_attempt_record['raw_output_sha256'] == m['raw_output_sha256'] and selected_attempt_record['events_sha256'] == m['events_sha256']
            attempt_audits.append({'batch': bi, 'attempt': ai, 'path': str(a), 'valid': valid, 'metadata_sha256': sha(a / 'run_metadata.json'), 'request_sha256': m['request_sha256'], 'raw_output_sha256': m['raw_output_sha256'], 'events_sha256': m['events_sha256'], 'validation_errors': errors, 'event_check': ev, 'actual_output_event_binding': output_event_binding, 'original_execution_errors': m['errors']})
            if valid: valid_attempts.append(a)
        if valid_attempts:
            a = valid_attempts[0]; assert a == attempts[-1]
            assert selection['status'] == 'accepted_first_valid_actual_attempt' and selection['selected_relative_path'] == str(a.relative_to(run))
            assert selection['selected_output_sha256'] == sha(a / 'raw_output.json')
            accepted[bi] = {'packet': packet, 'raw': read(a / 'raw_output.json'), 'metadata': read(a / 'run_metadata.json'), 'attempt_path': a}
        else:
            assert len(attempts) == 3 and selection['status'] == 'all_attempts_failed_preserved'
            assert selection['selected_relative_path'] is None and selection['selected_output_sha256'] is None
            failed.append(bi)
        batches.append({'batch': bi, 'n': len(packet['rows']), 'attempts': len(attempts), 'accepted': bool(valid_attempts), 'selection': bind(b / 'selection.json')})
    assert failed == allowed_terminal_failures, ('Unexpected terminal failures: scope must not expand automatically', failed)
    assert summary['accepted_batch_count'] == len(accepted) and summary['actual_attempt_count'] == len(attempt_audits) <= n_batches * 3
    assert summary['all_attempt_tool_event_count'] == sum(len(x['event_check']['violations']) for x in attempt_audits)
    if failed:
        assert summary['status'] == 'partial_or_failed_preserved' and summary['output_sha256'] is None
        assert not (run / 'all_predictions.jsonl').exists() and not (run / 'all_predictions.json').exists()
    else:
        aggregate = read(run / 'all_predictions.json'); rows = [r for bi in accepted for r in accepted[bi]['raw']['rows']]
        assert aggregate['rows'] == rows == lines(run / 'all_predictions.jsonl')
        assert aggregate['issue_records'] == [r for bi in accepted for r in accepted[bi]['raw']['issue_records']]
        assert not v.validate({'rows': source}, aggregate) and summary['output_sha256'] == sha(run / 'all_predictions.jsonl')
    qa = {'status': 'PASS_AUDIT_OF_TECHNICALLY_INCOMPLETE_RUN' if failed else 'PASS', 'original_execution_status': summary['status'], 'run': str(run), 'n_input_rows': expected_n, 'logical_batches': n_batches, 'accepted_batches': len(accepted), 'accepted_rows': sum(len(x['raw']['rows']) for x in accepted.values()), 'terminal_failed_batches': failed, 'actual_attempts': len(attempt_audits), 'failed_attempts_preserved': sum(not a['valid'] for a in attempt_audits), 'source': bind(run / 'frozen_input.jsonl'), 'prompt': bind(run / 'frozen_prompt.txt'), 'run_plan': bind(run / 'run_plan.json'), 'execution_summary': bind(run / 'execution_summary.json'), 'first_valid_selected_without_post_valid_calls': True, 'all_selected_raw_objects_equal_actual_final_event_JSON': True, 'batch_audits': batches, 'attempt_audits': attempt_audits, 'provider_internal_revision': 'not exposed; requested CLI parameter and any event model fields audited'}
    return accepted, qa, v
