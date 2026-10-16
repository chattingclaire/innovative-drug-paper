"""Technical audit and complete development comparisons; never edits labels.

Run only after both fixed runs complete. Semantic review remains a separate task.
No A/B/C or other candidate-reference labels are read or used here.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def dump_new(path, obj):
    content = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    if path.exists():
        assert path.read_text() == content, f'Previous audit differs: {path}'
    else:
        path.write_text(content)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def audit_run(run, declared, freeze):
    plan = read(run / 'run_plan.json')
    summary = read(run / 'execution_summary.json')
    assert plan['n'] == declared['n'] and plan['batch_size'] == declared['batch_size']
    assert plan['batch_count'] == declared['logical_batches'] and plan['max_attempts'] == 3
    assert plan['model'] == 'gpt-5.6-sol' and plan['reasoning_effort'] == 'medium'
    assert plan['workers_not_part_of_semantic_batch_plan'] is True
    source = lines(run / 'frozen_input.jsonl')
    assert sha(run / 'frozen_input.jsonl') == plan['input_sha256'] == sha(declared['input'])
    assert sha(run / 'frozen_prompt.txt') == plan['prompt_sha256'] == freeze['candidate05_prompt']['sha256']
    for key, filename in [('schema', 'frozen_schema.json'), ('validator', 'frozen_validator.py'), ('runner', 'frozen_runner.py')]:
        assert sha(run / filename) == plan[key + '_sha256']
    assert plan['schema_sha256'] == freeze['runtime']['output_schema_codex_compatible.json']['sha256']
    assert plan['validator_sha256'] == freeze['runtime']['validate_binary_output.py']['sha256']
    assert plan['runner_sha256'] == freeze['runtime']['run_production_v32.py']['sha256']
    validator = load_module('c05_validator_' + str(declared['n']), run / 'frozen_validator.py')
    runner = load_module('c05_runner_' + str(declared['n']), HERE / 'runtime-v2/run_production_v32.py')
    prompt = (run / 'frozen_prompt.txt').read_text()
    all_rows, all_issues, attempts = [], [], []
    for index in range(1, declared['logical_batches'] + 1):
        batch = run / 'batches' / f'batch-{index:04d}'
        packet = read(batch / 'input.json')
        assert packet == {'rows': source[(index - 1) * 25:index * 25]}
        expected_request = prompt + '\n\n--- 本批冻结盲法输入 ---\n' + json.dumps(packet, ensure_ascii=False) + '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
        assert (batch / 'request.txt').read_text() == expected_request
        selection = read(batch / 'selection.json')
        actual_attempts = sorted((batch / 'attempts').glob('attempt-*'))
        assert 1 <= len(actual_attempts) <= 3
        assert [p.name for p in actual_attempts] == [f'attempt-{i:02d}' for i in range(1, len(actual_attempts) + 1)]
        valid = []
        for attempt in actual_attempts:
            meta = read(attempt / 'run_metadata.json')
            assert read(attempt / 'input.json') == packet
            assert (attempt / 'request.txt').read_text() == expected_request
            assert meta['requested_model'] == 'gpt-5.6-sol' and meta['reasoning_effort'] == 'medium'
            assert meta['prompt_sha256'] == plan['prompt_sha256']
            assert meta['cli_binary_sha256'] == plan['cli_binary_sha256'] and meta['cli_version'] == plan['cli_version']
            cmd = meta['command']
            assert cmd[cmd.index('--model') + 1] == 'gpt-5.6-sol'
            assert 'model_reasoning_effort="medium"' in cmd and 'web_search="disabled"' in cmd
            assert all(flag in cmd for flag in ['--ephemeral', '--ignore-user-config', '--ignore-rules'])
            assert cmd[cmd.index('--sandbox') + 1] == 'read-only'
            for key, filename in [('input', 'input.json'), ('request', 'request.txt'), ('events', 'events.jsonl'), ('stderr', 'raw_stderr.txt'), ('tool_event_audit', 'tool_event_audit.json'), ('validation', 'validation.json')]:
                assert meta[key + '_sha256'] == sha(attempt / filename)
            event_audit = runner.event_audit((attempt / 'events.jsonl').read_text())
            raw_path = attempt / 'raw_output.json'
            if raw_path.exists():
                assert sha(raw_path) == meta['raw_output_sha256']
            raw_output = None
            raw_json_available = False
            errors = ['missing_output']
            if raw_path.exists():
                try:
                    raw_output = read(raw_path)
                    raw_json_available = True
                    errors = validator.validate(packet, raw_output)
                except (ValueError, TypeError, KeyError) as exc:
                    errors = [type(exc).__name__ + ':invalid_raw_or_schema']
            binding_audit = runner.event_output_binding_audit((attempt / 'events.jsonl').read_text(), raw_output, raw_json_available)
            assert read(attempt / 'event_output_binding_audit.json') == binding_audit
            assert sha(attempt / 'event_output_binding_audit.json') == meta['event_output_binding_audit_sha256']
            assert meta['completed_agent_message_count'] == binding_audit['completed_agent_message_count']
            assert meta['raw_output_matches_unique_completed_agent_message'] == binding_audit['event_raw_full_object_equal']
            good = meta['exit_code'] == 0 and not errors and event_audit['completed_turns'] == 1 and not event_audit['violations'] and not event_audit['turn_errors'] and all(m == 'gpt-5.6-sol' for m in event_audit['observed_model_fields']) and not binding_audit['errors']
            assert good == read(attempt / 'validation.json')['valid']
            final_messages = []
            for text in (attempt / 'events.jsonl').read_text().splitlines():
                try:
                    event = json.loads(text)
                except ValueError:
                    continue
                if not isinstance(event, dict):
                    continue
                item = event.get('item', {})
                if event.get('type') == 'item.completed' and isinstance(item, dict) and item.get('type') == 'agent_message':
                    final_messages.append(item.get('text'))
            if good:
                assert raw_path.exists() and sha(raw_path) == meta['raw_output_sha256']
                assert len(final_messages) == 1 and json.loads(final_messages[0]) == read(raw_path)
                valid.append(attempt)
            attempts.append({'batch': index, 'attempt': attempt.name, 'technically_valid': good,
                             'path': str(attempt), 'request_sha256': meta['request_sha256'],
                             'raw_output_sha256': meta['raw_output_sha256'], 'events_sha256': meta['events_sha256']})
        assert valid and valid[0] == actual_attempts[-1]
        chosen = valid[0]
        assert selection['selected_relative_path'] == str(chosen.relative_to(run))
        assert selection['selected_output_sha256'] == sha(chosen / 'raw_output.json')
        assert selection['selection_uses_metric_or_label_values'] is False
        selected = read(chosen / 'raw_output.json')
        all_rows.extend(selected['rows'])
        all_issues.extend(selected['issue_records'])
    aggregate = read(run / 'all_predictions.json')
    assert aggregate['rows'] == all_rows == lines(run / 'all_predictions.jsonl')
    assert aggregate['issue_records'] == all_issues
    assert not validator.validate({'rows': source}, aggregate)
    assert summary['status'] == 'complete_actual_calls_structurally_valid'
    assert summary['accepted_batch_count'] == declared['logical_batches']
    assert summary['actual_attempt_count'] == len(attempts)
    assert summary['output_sha256'] == sha(run / 'all_predictions.jsonl')
    assert summary['source_unchanged_during_run'] is True
    assert summary['source_input_current_sha256'] == plan['input_sha256']
    assert summary['plan_sha256'] == sha(run / 'run_plan.json')
    return all_rows, {'run': str(run), 'n': len(all_rows), 'logical_batches': declared['logical_batches'],
                      'actual_attempts': len(attempts), 'all_labels_from_intact_actual_rows': True,
                      'all_selected_raw_equal_actual_final_event_JSON': True, 'attempts': attempts}


def main():
    package = read(HERE / 'candidate05_package_manifest_v2.json')
    for bound in package['files']:
        assert sha(bound['path']) == bound['sha256']
    freeze = read(HERE / 'candidate05_development_freeze_v2.json')
    historical = read(HERE / 'historical_comparison_freeze.json')
    for bound in historical['frozen_files'].values():
        assert sha(bound['path']) == bound['sha256']
    outputs, technical = {}, []
    for declared in freeze['planned_runs']:
        result, audit = audit_run(HERE / 'runtime-v2' / declared['name'], declared, freeze)
        outputs[declared['n']] = {r['id']: r for r in result}
        technical.append(audit)
    assert sum(a['actual_attempts'] for a in technical) <= 39
    old_outputs = {name: {r['id']: r for r in lines(bound['path'])}
                   for name, bound in historical['frozen_files'].items() if name.endswith('_rows')}
    source240 = {r['id']: r for r in lines(freeze['exposed240_input']['path'])}
    excluded = set(read(freeze['human_reserved_exclusion_metadata']['path'])['all_registered_members_of_reserved_families_unit_ids'])
    assert not excluded.intersection(source240)
    changes, complete = [], []
    for rid, inp in source240.items():
        new = outputs[240][rid]
        prior = {name: rows[rid] for name, rows in old_outputs.items()}
        changed = {name: [d for d in DIMS if row['labels'][d] != new['labels'][d]] for name, row in prior.items()}
        entry = {'id': rid, 'input': inp, 'candidate05_intact_actual_row': new,
                 'historical_intact_rows': prior, 'changed_dimensions_vs_each_history': changed,
                 'semantic_truth_not_inferred_from_agreement': True}
        complete.append(entry)
        if any(changed.values()):
            changes.append(entry)
    tests = read(freeze['synthetic_expected_private']['path'])['tests']
    control_results = []
    for test in tests:
        observed = outputs[62][test['input']['id']]
        control_results.append({**test, 'actual_row': observed,
                                'different_dimensions': [d for d in DIMS if observed['labels'][d] != test['labels'][d]],
                                'requires_semantic_review_even_if_labels_match': True})
    preservation = {name: sha(bound['path']) == bound['sha256']
                    for name, bound in freeze['prior_artifacts_preserved'].items()}
    assert all(preservation.values())
    dump_new(HERE / 'candidate05_technical_QA.json', {'status': 'TECHNICAL_AUDIT_ONLY_SEMANTIC_REVIEW_PENDING',
             'actual_model_attempts': sum(a['actual_attempts'] for a in technical), 'technical_runs': technical,
             'independent_validation': False, 'historical_sources_preserved': preservation})
    dump_new(HERE / 'candidate05_all240_comparison_PRIVATE.json', {'status': 'DEVELOPMENT_ONLY_NOT_GOLD_LABEL_EVALUATION', 'rows': complete})
    dump_new(HERE / 'candidate05_all_changes_PRIVATE.json', {'status': 'ALL_FIVE_DIMENSION_CHANGES_FOR_SEMANTIC_REVIEW', 'rows': changes})
    dump_new(HERE / 'candidate05_all62_controls_PRIVATE.json', {'status': 'DEVELOPMENT_CONTROLS_ONLY_NOT_INDEPENDENT_VALIDATION', 'tests': control_results})
    print(json.dumps({'status': 'TECHNICAL_AUDIT_ONLY_SEMANTIC_REVIEW_PENDING', 'original_rows': 240,
                      'changed_original_rows': len(changes), 'controls': 62, 'production_labels_edited': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
