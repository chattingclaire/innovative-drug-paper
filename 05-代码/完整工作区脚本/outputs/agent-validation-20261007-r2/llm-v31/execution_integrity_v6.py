"""Independently reconstruct actual requests, attempts and first-valid selection.

Only execution/material files are read. No agent references, evaluation
metrics or manuscript conclusions are inputs to this audit.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

SUFFIX = '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


def event_reconstruction(path):
    violations = []; counts = {}; models = []; completed = 0; failures = []; messages = []
    for index, line in enumerate(Path(path).read_text().splitlines()):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            violations.append({'line': index + 1, 'reason': 'non_json_event'}); continue
        kind = event.get('type'); item = event.get('item', {})
        item_kind = item.get('type') if isinstance(item, dict) else None
        key = f'{kind}/{item_kind}'; counts[key] = counts.get(key, 0) + 1
        for field in ['model', 'model_name']:
            if isinstance(event.get(field), str) and event[field] not in models:
                models.append(event[field])
        if item_kind is not None and item_kind not in {'agent_message', 'reasoning'}:
            violations.append({'line': index + 1, 'reason': 'non_message_item_potential_tool', 'event': event})
        if isinstance(kind, str) and any(x in kind.lower() for x in ['tool_call', 'function_call', 'web_search', 'web_fetch', 'command_execution']):
            violations.append({'line': index + 1, 'reason': 'tool_event_type', 'event': event})
        if kind == 'turn.completed': completed += 1
        if kind in {'turn.failed', 'error'}: failures.append(event)
        if kind == 'item.completed' and item_kind == 'agent_message': messages.append(item.get('text'))
    return {'tool_or_unknown_item_event_count': len(violations), 'violations': violations,
            'event_type_counts': counts, 'observed_model_fields': models,
            'completed_turns': completed, 'turn_errors': failures}, messages


def audit_run(run, require_finished=True):
    run = Path(run).resolve(); plan = read(run / 'run_plan.json')
    assert plan['model'] == 'gpt-5.6-sol' and plan['reasoning_effort'] == 'medium'
    for name, key in [('frozen_prompt.txt', 'prompt_sha256'), ('frozen_schema.json', 'schema_sha256'),
                      ('frozen_validator.py', 'validator_sha256'), ('frozen_runner.py', 'runner_sha256')]:
        assert sha(run / name) == plan[key], (run, name)
    frozen = run / plan['frozen_input_relative_path']
    assert sha(frozen) == plan['input_sha256']
    material = lines(frozen) if frozen.suffix == '.jsonl' else read(frozen)['rows']
    assert len(material) == plan['n'] and len({r['id'] for r in material}) == plan['n']
    prompt = (run / 'frozen_prompt.txt').read_text()
    spec = importlib.util.spec_from_file_location('frozen_validator_' + plan['validator_sha256'], run / 'frozen_validator.py')
    validator = importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
    selected = {}; failures = []; attempt_count = 0; all_tool_events = 0; all_unresolved = []
    observed = set(); snapshots = {}; selections = sorted((run / 'batches').glob('batch-*/selection.json'))
    if require_finished:
        assert len(selections) == plan['batch_count'], ('incomplete actual run', run, len(selections), plan['batch_count'])
    for selection_path in selections:
        selection = read(selection_path); index = selection['batch']; batch = selection_path.parent
        assert batch.name == f'batch-{index:04d}'
        expected = material[(index - 1) * plan['batch_size']:index * plan['batch_size']]
        packet = {'rows': expected}; request = prompt + '\n\n--- 本批冻结盲法输入 ---\n' + json.dumps(packet, ensure_ascii=False) + SUFFIX
        assert read(batch / 'input.json') == packet and (batch / 'request.txt').read_text() == request
        assert selection['ids'] == [r['id'] for r in expected] and selection['input_n'] == len(expected)
        assert selection['selection_uses_metric_or_label_values'] is False
        attempts = sorted((batch / 'attempts').glob('attempt-*'))
        assert len(attempts) == len(selection['attempts']) <= plan['max_attempts']
        first_valid = None; accepted_output = None; accepted_meta = None
        for attempt_number, (attempt, declared) in enumerate(zip(attempts, selection['attempts']), 1):
            attempt_count += 1
            assert attempt.name == f'attempt-{attempt_number:02d}' and declared['attempt'] == attempt_number
            assert declared['relative_path'] == str(attempt.relative_to(run))
            assert read(attempt / 'input.json') == packet and (attempt / 'request.txt').read_text() == request
            metadata = read(attempt / 'run_metadata.json'); validation = read(attempt / 'validation.json')
            assert sha(attempt / 'run_metadata.json') == declared['metadata_sha256']
            for filename, key in [('input.json', 'input_sha256'), ('request.txt', 'request_sha256'),
                                  ('events.jsonl', 'events_sha256'), ('raw_stderr.txt', 'stderr_sha256'),
                                  ('tool_event_audit.json', 'tool_event_audit_sha256'), ('validation.json', 'validation_sha256')]:
                assert sha(attempt / filename) == metadata[key], (attempt, filename)
            assert metadata['requested_model'] == plan['model'] and metadata['reasoning_effort'] == plan['reasoning_effort']
            assert metadata['prompt_sha256'] == plan['prompt_sha256'] and metadata['web_search'] == 'disabled'
            assert metadata['cli_binary_sha256'] == plan['cli_binary_sha256'] and metadata['cli_version'] == plan['cli_version']
            assert metadata['label_or_metric_selection'] is False and metadata['ids'] == selection['ids']
            command = metadata['command']
            assert command[command.index('--model') + 1] == plan['model']
            assert 'model_reasoning_effort="medium"' in command and 'web_search="disabled"' in command
            assert all(x in command for x in ['--ignore-user-config', '--ignore-rules', '--ephemeral', '--json'])
            assert command[command.index('--sandbox') + 1] == 'read-only'
            event, messages = event_reconstruction(attempt / 'events.jsonl')
            assert event == read(attempt / 'tool_event_audit.json')
            assert metadata['tool_event_count'] == declared['tool_event_count'] == event['tool_or_unknown_item_event_count']
            assert metadata['events_sha256'] == declared['events_sha256']
            observed.update(event['observed_model_fields']); all_tool_events += event['tool_or_unknown_item_event_count']
            errors = []; raw = attempt / 'raw_output.json'; data = None
            if metadata['exit_code'] != 0: errors.append('cli_execution_failure')
            if not raw.exists(): errors.append('missing_raw_output')
            else:
                assert sha(raw) == metadata['raw_output_sha256'] == declared['raw_output_sha256']
                try:
                    data = read(raw); errors.extend(validator.validate(packet, data))
                    assert messages and json.loads(messages[-1]) == data, ('raw output differs from actual event final message', raw)
                except (ValueError, TypeError, KeyError) as error:
                    errors.append(f'json_or_validator_error:{type(error).__name__}:{error}')
            if event['tool_or_unknown_item_event_count']: errors.append('nonzero_tool_or_unknown_item_events')
            if event['completed_turns'] != 1: errors.append('completed_turn_count_not_one')
            if event['turn_errors']: errors.append('turn_error_event')
            if event['observed_model_fields'] and any(m != plan['model'] for m in event['observed_model_fields']):
                errors.append('observed_model_mismatch')
            assert sorted(errors) == sorted(metadata['errors']) == sorted(validation['errors']) == sorted(declared['errors']), (attempt, errors, metadata['errors'])
            assert validation['valid'] == (not errors)
            expected_status = 'failed_attempt_preserved' if errors else 'accepted_structural_literal_zero_tools'
            assert declared['status'] == metadata['status'] == expected_status
            for issue in (data or {}).get('issue_records', []):
                if issue.get('status') == 'material_issue':
                    all_unresolved.append({'run': str(run), 'batch': index, 'attempt': attempt_number, 'issue': issue})
            if not errors:
                assert first_valid is None, ('a later attempt was run after acceptance', attempt)
                first_valid = attempt; accepted_output = data; accepted_meta = metadata
                assert attempt_number == len(attempts), ('selection did not stop at first valid', batch)
        if first_valid:
            assert selection['status'] == 'accepted_first_valid_actual_attempt'
            assert selection['selected_relative_path'] == str(first_valid.relative_to(run))
            assert selection['selected_output_sha256'] == sha(first_valid / 'raw_output.json')
            selected[index] = {'input': expected, 'output': accepted_output, 'metadata': accepted_meta,
                               'selected_attempt': str(first_valid), 'raw_path': str(first_valid / 'raw_output.json'),
                               'run_path': str(run), 'batch_index': index, 'selection_path': str(selection_path),
                               'selection_sha256': sha(selection_path), 'attempts': selection['attempts']}
        else:
            assert selection['status'] == 'all_attempts_failed_preserved'
            assert selection['selected_relative_path'] is None and selection['selected_output_sha256'] is None
            assert len(attempts) == plan['max_attempts']
            failures.append({'batch': index, 'selection': str(selection_path), 'selection_sha256': sha(selection_path),
                             'attempts': selection['attempts']})
        snapshots[str(selection_path)] = sha(selection_path)
    return {'run': str(run), 'plan': plan, 'plan_sha256': sha(run / 'run_plan.json'),
            'completed_batch_count': len(selections), 'selected': selected, 'failed_batches': failures,
            'all_actual_attempt_count': attempt_count, 'all_attempt_tool_events': all_tool_events,
            'observed_model_fields': sorted(observed), 'all_material_issue_records': all_unresolved,
            'audited_selection_hashes': snapshots}
