"""Offline provenance checks only; never print private input/output or expectations.

No subprocess, CLI invocation, model call, label scoring, or semantic judgment.
Expectation/design files in the 18-file freeze are opaque SHA/size checks only.
"""
import sys
sys.dont_write_bytecode = True
import collections
import datetime
import hashlib
import importlib.util
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / 'independent_actual_technical_review.json'
if OUT.exists():
    raise SystemExit('Refusing to overwrite independent review')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def canonical_sha(obj):
    return hashlib.sha256(canonical(obj).encode('utf-8')).hexdigest()

checks = []
def check(name, value):
    checks.append({'check': name, 'pass': bool(value)})
    return bool(value)

def bind(obj):
    return Path(obj['path'])

def argument_value(arguments, flag, default=None):
    return arguments[arguments.index(flag) + 1] if flag in arguments else default

def stderr_counts(path):
    # All labels below are fixed audit categories; no stderr content is returned.
    lines = Path(path).read_text(encoding='utf-8', errors='replace').splitlines()
    warn = [line for line in lines if re.search(r'\bWARN(?:ING)?\b', line, re.I)]
    err = [line for line in lines if re.search(r'\bERROR\b|\bFATAL\b', line, re.I)]
    patterns = {
        'experimental_feature': r'under.development|experimental|unstable',
        'schema_or_format': r'schema|format',
        'model_configuration': r'model|reasoning',
        'session_or_state': r'session|rollout|state',
        'shell_or_snapshot': r'snapshot|shell',
        'authentication': r'auth|credential|token',
        'transport': r'network|socket|stream|connection|http',
        'tool_configuration': r'\bmcp\b|\btool',
        'telemetry': r'otlp|telemetry',
    }
    categories = collections.Counter()
    for line in warn:
        matches = [key for key, pattern in patterns.items() if re.search(pattern, line, re.I)]
        for key in matches or ['unclassified_warning']:
            categories[key] += 1
    return {'bytes': Path(path).stat().st_size, 'line_count': len(lines),
            'warning_line_count': len(warn), 'error_or_fatal_line_count': len(err),
            'warning_category_counts_nonexclusive': dict(categories),
            'raw_content_not_disclosed': True}

auth_path = BASE / 'root_execution_authorization.json'
auth = read(auth_path)
freeze_path = BASE / 'preparation_freeze.json'
freeze = read(freeze_path)
plan_path = BASE / 'final_execution_plan.json'
plan = read(plan_path)
preflight_path = Path(auth['independent_preflight']['path'])
preflight = read(preflight_path)
start = read(BASE / 'actual_execution_start.json')
completion = read(BASE / 'actual_execution_completion.json')
check('authorization_status', auth['status'] == 'AUTHORIZED_BOUNDED_FOUR_ARM_DIAGNOSTIC_ONLY')
check('authorization_bounds_4_logical_12_attempts', auth['maximum_logical_requests'] == 4 and auth['maximum_identical_technical_attempts'] == 12)
check('authorization_no_original240_or_full4924_or_adoption', auth['original240_or_full4924_execution_authorized'] is False and auth['new_candidate_or_adoption_authorized'] is False)
check('authorization_freeze_sha', sha(freeze_path) == auth['preparation_freeze_sha256'])
check('authorization_plan_sha', sha(plan_path) == auth['final_execution_plan_sha256'])
check('authorization_preflight_sha', sha(preflight_path) == auth['independent_preflight']['sha256'])
check('start_authorization_sha', start['authorization_sha256'] == sha(auth_path))
check('preflight_pass', auth['independent_preflight_pass'] is True and preflight['status'].startswith('PASS_') and preflight['checks_passed'] == preflight['checks_total'] and not preflight['blocking_findings'] and not preflight['failures'])
check('preflight_offline_0_calls', preflight['real_model_calls'] == 0 and preflight['real_CLI_invocations'] == 0)
evidence_bind = preflight['evidence_binding']
check('preflight_evidence_binding', sha(Path(evidence_bind['path'])) == evidence_bind['sha256'])
check('freeze_has_exactly18_files', len(freeze['files']) == 18)
freeze_results = []
for item in freeze['files']:
    path = Path(item['path'])
    # Opaque bytes only, including private expectation/design files. No decoding.
    actual = sha(path)
    size = path.stat().st_size
    passed = actual == item['sha256'] and size == item['bytes']
    check('freeze_item_' + str(len(freeze_results) + 1), passed)
    freeze_results.append({'path': str(path), 'expected_sha256': item['sha256'],
                           'actual_sha256': actual, 'bytes': size, 'pass': passed,
                           'content_not_decoded': True})
freeze_start = {item['path']: sha(item['path']) for item in freeze['files']}

arms = plan['arms']
arm_names = [arm['arm'] for arm in arms]
check('four_unique_run_names', len(arms) == 4 and len(set(arm_names)) == 4)
check('execution_order_binding', plan['execution_order'] == arm_names)
check('plan_bounds', plan['logical_requests'] == 4 and plan['maximum_identical_technical_attempts'] == 12)
check('fixed_requested_model_effort', plan['model'] == auth['requested_model'] == 'gpt-5.6-sol' and plan['reasoning_effort'] == auth['reasoning_effort'] == 'medium')
runtime_dirs = sorted(path.name for path in (BASE / 'runtime').iterdir() if path.is_dir() and path.name.startswith('field_'))
check('exact_runtime_arm_set', sorted(arm_names) == runtime_dirs)

validator_path = BASE / 'runtime' / 'validate_binary_output.py'
spec = importlib.util.spec_from_file_location('independent_frozen_structural_validator', validator_path)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

arm_results = []
all_cwds = []
all_thread_ids = []
total_attempts = 0
total_tools = 0
allowed_event_types = {'thread.started', 'turn.started', 'item.started', 'item.updated', 'item.completed', 'turn.completed'}
for arm in arms:
    name = arm['arm']
    run = BASE / 'runtime' / name
    run_plan_path = run / 'run_plan.json'
    run_plan = read(run_plan_path)
    summary = read(run / 'execution_summary.json')
    args = arm['runner_arguments']
    check(name + ':run_name_matches_arguments', argument_value(args, '--run-name') == name and Path(name).name == name)
    check(name + ':one_batch_args', int(argument_value(args, '--expected-n')) == 5 and int(argument_value(args, '--batch-size', '25')) >= 5 and int(argument_value(args, '--workers', '8')) == 1 and int(argument_value(args, '--max-attempts', '3')) == 3 and int(argument_value(args, '--start', '1')) == 1)
    check(name + ':runner_not_plan_only', '--plan-only' not in args)
    check(name + ':actual_one_batch_run_plan', run_plan['n'] == 5 and run_plan['batch_count'] == 1 and run_plan['max_attempts'] == 3 and run_plan['model'] == 'gpt-5.6-sol' and run_plan['reasoning_effort'] == 'medium')
    input_path = bind(arm['input'])
    request_path = bind(arm['offline_request'])
    packet_path = bind(arm['offline_packet'])
    for key in ['input', 'offline_request', 'offline_packet']:
        record = arm[key]
        check(name + ':offline_binding_' + key, sha(bind(record)) == record['sha256'] and bind(record).stat().st_size == record['bytes'])
    check(name + ':argument_input_and_hash_lock', Path(argument_value(args, '--input')).resolve() == input_path.resolve() and argument_value(args, '--expected-input-sha256') == arm['input']['sha256'])
    check(name + ':run_source_input_binding', Path(run_plan['source_input_path']).resolve() == input_path.resolve() and run_plan['input_sha256'] == arm['input']['sha256'])
    check(name + ':frozen_input_byte_identity', (run / run_plan['frozen_input_relative_path']).read_bytes() == input_path.read_bytes())
    for frozen_name, source, hash_field in [
        ('frozen_prompt.txt', Path(run_plan['source_prompt_path']), 'prompt_sha256'),
        ('frozen_schema.json', BASE / 'runtime' / 'output_schema_codex_compatible.json', 'schema_sha256'),
        ('frozen_validator.py', validator_path, 'validator_sha256'),
        ('frozen_runner.py', BASE / 'runtime' / 'run_production_v32.py', 'runner_sha256')]:
        check(name + ':source_snapshot_' + frozen_name, (run / frozen_name).read_bytes() == source.read_bytes() and sha(source) == run_plan[hash_field])
    batches = sorted((run / 'batches').glob('batch-*'))
    check(name + ':exact_batch0001_only', len(batches) == 1 and batches[0].name == 'batch-0001')
    batch = run / 'batches' / 'batch-0001'
    check(name + ':batch_request_byte_identity_offline', (batch / 'request.txt').read_bytes() == request_path.read_bytes())
    check(name + ':batch_input_byte_identity_offline', (batch / 'input.json').read_bytes() == packet_path.read_bytes())
    packet = read(packet_path)  # Mechanical only; never serialized into this report.
    source_input = read(input_path)
    check(name + ':packet_full_rows_equals_frozen_source', canonical(packet) == canonical(source_input))
    recomposed = (run / 'frozen_prompt.txt').read_text() + '\n\n--- 本批冻结盲法输入 ---\n' + json.dumps(packet, ensure_ascii=False) + '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
    check(name + ':request_exact_formula', recomposed.encode() == request_path.read_bytes())
    selection = read(batch / 'selection.json')
    attempts = sorted((batch / 'attempts').glob('attempt-*'))
    total_attempts += len(attempts)
    check(name + ':attempts_complete_contiguous_and_bounded', 1 <= len(attempts) <= 3 and [path.name for path in attempts] == ['attempt-%02d' % i for i in range(1, len(attempts) + 1)] and len(selection['attempts']) == len(attempts))
    attempt_results = []
    independent_valid = []
    for index, attempt in enumerate(attempts, 1):
        prefix = name + ':' + attempt.name + ':'
        meta_path = attempt / 'run_metadata.json'
        meta = read(meta_path)
        check(prefix + 'actual_request_byte_identity_offline', (attempt / 'request.txt').read_bytes() == request_path.read_bytes())
        check(prefix + 'actual_input_byte_identity_offline', (attempt / 'input.json').read_bytes() == packet_path.read_bytes())
        for meta_field, filename in [('input_sha256', 'input.json'), ('request_sha256', 'request.txt'), ('raw_output_sha256', 'raw_output.json'), ('events_sha256', 'events.jsonl'), ('stderr_sha256', 'raw_stderr.txt'), ('tool_event_audit_sha256', 'tool_event_audit.json'), ('validation_sha256', 'validation.json'), ('event_output_binding_audit_sha256', 'event_output_binding_audit.json')]:
            check(prefix + 'metadata_binding_' + filename, sha(attempt / filename) == meta[meta_field])
        record = selection['attempts'][index - 1]
        check(prefix + 'selection_metadata_binding', record['attempt'] == index and record['relative_path'] == str(attempt.relative_to(run)) and record['metadata_sha256'] == sha(meta_path))
        command = meta['command']
        configs = [command[i + 1] for i, token in enumerate(command[:-1]) if token == '-c']
        cwd = argument_value(command, '--cd')
        all_cwds.append(cwd)
        check(prefix + 'actual_command_fixed_model_effort', argument_value(command, '--model') == 'gpt-5.6-sol' and 'model_reasoning_effort="medium"' in configs and meta['requested_model'] == 'gpt-5.6-sol' and meta['reasoning_effort'] == 'medium')
        check(prefix + 'actual_command_isolation', all(flag in command for flag in ['--ephemeral', '--ignore-user-config', '--ignore-rules', '--skip-git-repo-check', '--json']) and argument_value(command, '--sandbox') == 'read-only' and 'web_search="disabled"' in configs and Path(cwd).name.startswith('llm-v32-empty-') and not Path(cwd).exists())
        check(prefix + 'actual_cli_binary_binding_without_invocation', command[0] == run_plan['cli_path'] == meta['cli_path'] and sha(command[0]) == run_plan['cli_binary_sha256'] == meta['cli_binary_sha256'])
        check(prefix + 'output_path_is_exact_attempt', Path(argument_value(command, '--output-last-message')).resolve() == (attempt / 'raw_output.json').resolve())
        check(prefix + 'schema_path_exact', Path(argument_value(command, '--output-schema')).resolve() == (BASE / 'runtime' / 'output_schema_codex_compatible.json').resolve())
        raw = read(attempt / 'raw_output.json')
        events = []
        event_parse_failures = 0
        for line in (attempt / 'events.jsonl').read_text().splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise TypeError()
                events.append(event)
            except (ValueError, TypeError):
                event_parse_failures += 1
        final_messages = [event['item'].get('text') for event in events if event.get('type') == 'item.completed' and isinstance(event.get('item'), dict) and event['item'].get('type') == 'agent_message']
        final_obj = None
        final_json_ok = False
        if len(final_messages) == 1 and isinstance(final_messages[0], str):
            try:
                final_obj = json.loads(final_messages[0]); final_json_ok = True
            except ValueError:
                pass
        event_raw_equal = final_json_ok and canonical(final_obj) == canonical(raw)
        tool_or_unknown_items = sum(1 for event in events if (isinstance(event.get('item'), dict) and event['item'].get('type') not in {None, 'reasoning', 'agent_message'}) or any(token in str(event.get('type', '')).lower() for token in ['tool_call', 'function_call', 'web_search', 'web_fetch', 'command_execution']))
        turn_completed = sum(event.get('type') == 'turn.completed' for event in events)
        turn_errors = sum(event.get('type') in {'turn.failed', 'error'} for event in events)
        unknown_types = sum(event.get('type') not in allowed_event_types for event in events)
        threads = [event.get('thread_id') for event in events if event.get('type') == 'thread.started']
        all_thread_ids.extend(threads)
        observed_models = sorted({event[field] for event in events for field in ['model', 'model_name'] if isinstance(event.get(field), str)})
        structural_errors = validator.validate(packet, raw)  # Frozen pure function; not a model/CLI.
        valid = meta['exit_code'] == 0 and meta['execution_error'] is None and event_parse_failures == 0 and len(final_messages) == 1 and event_raw_equal and tool_or_unknown_items == 0 and turn_completed == 1 and turn_errors == 0 and not structural_errors and all(model == 'gpt-5.6-sol' for model in observed_models)
        independent_valid.append(valid)
        total_tools += tool_or_unknown_items
        check(prefix + 'events_unique_completed_agent_full_json_equals_raw', event_raw_equal and len(final_messages) == 1)
        check(prefix + 'zero_tool_and_error_events', tool_or_unknown_items == 0 and turn_errors == 0 and event_parse_failures == 0 and turn_completed == 1 and unknown_types == 0)
        check(prefix + 'one_independent_thread', len(threads) == 1 and isinstance(threads[0], str) and bool(threads[0]))
        check(prefix + 'metadata_technical_validity_reproduced', valid == (meta['status'] == 'accepted_structural_literal_zero_tools') and meta['tool_event_count'] == tool_or_unknown_items and not meta['label_or_metric_selection'])
        check(prefix + 'selection_record_actual_attempt_binding', record['status'] == meta['status'] and record['raw_output_sha256'] == sha(attempt / 'raw_output.json') and record['events_sha256'] == sha(attempt / 'events.jsonl') and record['tool_event_count'] == tool_or_unknown_items)
        binding = read(attempt / 'event_output_binding_audit.json')
        validation = read(attempt / 'validation.json')
        check(prefix + 'stored_validation_reproduced', validation['valid'] == valid and validation['semantic_correctness_verified'] is False and not validation['errors'])
        check(prefix + 'stored_event_binding_reproduced', binding['completed_agent_message_count'] == len(final_messages) and binding['event_raw_full_object_equal'] == event_raw_equal and binding['event_final_json_canonical_sha256'] == canonical_sha(final_obj) and binding['raw_output_json_canonical_sha256'] == canonical_sha(raw))
        attempt_results.append({'attempt': index, 'request_sha256': sha(attempt / 'request.txt'), 'offline_request_sha256': arm['offline_request']['sha256'], 'input_sha256': sha(attempt / 'input.json'), 'offline_packet_sha256': arm['offline_packet']['sha256'], 'events_sha256': sha(attempt / 'events.jsonl'), 'raw_output_sha256': sha(attempt / 'raw_output.json'), 'event_raw_canonical_sha256': canonical_sha(raw), 'event_raw_full_json_equal': event_raw_equal, 'completed_agent_messages': len(final_messages), 'completed_turns': turn_completed, 'tool_or_unknown_item_events': tool_or_unknown_items, 'unknown_event_type_count': unknown_types, 'event_parse_failure_count': event_parse_failures, 'structural_literal_error_count': len(structural_errors), 'technical_valid_recomputed': valid, 'observed_model_fields_present': bool(observed_models), 'provider_internal_revision_verified': False, 'stderr_summary': stderr_counts(attempt / 'raw_stderr.txt')})
    first_valid = next((index for index, valid in enumerate(independent_valid, 1) if valid), None)
    selected_path = run / selection['selected_relative_path'] if selection['selected_relative_path'] else None
    check(name + ':first_valid_selected_no_later_attempt', first_valid is not None and selected_path == attempts[first_valid - 1] and len(attempts) == first_valid and all(not valid for valid in independent_valid[:first_valid - 1]) and not selection['selection_uses_metric_or_label_values'])
    selected_raw = read(selected_path / 'raw_output.json')
    aggregate_path = run / 'all_predictions.json'
    aggregate = read(aggregate_path)
    jsonl_rows = [json.loads(line) for line in (run / 'all_predictions.jsonl').read_text().splitlines() if line.strip()]
    check(name + ':raw_full_object_equals_aggregate', canonical(selected_raw) == canonical(aggregate))
    check(name + ':aggregate_jsonl_rows_exact_unmodified', canonical(aggregate['rows']) == canonical(jsonl_rows))
    check(name + ':selection_raw_hash', selection['selected_output_sha256'] == sha(selected_path / 'raw_output.json'))
    check(name + ':summary_complete_and_bound', summary['status'] == 'complete_actual_calls_structurally_valid' and summary['accepted_batch_count'] == summary['expected_batch_count'] == summary['recorded_batch_count'] == 1 and summary['actual_attempt_count'] == len(attempts) and summary['n'] == 5 and summary['all_attempt_tool_event_count'] == summary['selected_tool_event_count'] == 0)
    check(name + ':summary_full_source_hashes', summary['input_sha256'] == summary['source_input_current_sha256'] == sha(input_path) and summary['source_unchanged_during_run'] is True and summary['plan_sha256'] == sha(run_plan_path) and summary['output_sha256'] == sha(run / 'all_predictions.jsonl') and summary['prompt_sha256'] == sha(run / 'frozen_prompt.txt'))
    check(name + ':summary_no_semantic_validity_or_label_selection', summary['semantic_validity_not_proven_by_structure'] is True and summary['metric_or_reference_label_based_selection'] is False)
    arm_results.append({'arm': name, 'actual_attempt_count': len(attempts), 'n': 5, 'batch_count': 1, 'first_technically_valid_attempt': first_valid, 'earlier_failed_attempts': (first_valid - 1) if first_valid else len(attempts), 'request_offline_and_every_actual_attempt_bytes_equal': all(result['request_sha256'] == result['offline_request_sha256'] for result in attempt_results), 'input_offline_and_every_actual_attempt_bytes_equal': all(result['input_sha256'] == result['offline_packet_sha256'] for result in attempt_results), 'raw_aggregate_full_json_equal': canonical(selected_raw) == canonical(aggregate), 'aggregate_jsonl_sha256': sha(run / 'all_predictions.jsonl'), 'aggregate_json_sha256': sha(aggregate_path), 'attempts': attempt_results})

check('four_distinct_ephemeral_cwds', len(all_cwds) == total_attempts and len(set(all_cwds)) == total_attempts)
check('four_distinct_event_thread_ids', len(all_thread_ids) == total_attempts and len(set(all_thread_ids)) == total_attempts)
check('actual_attempt_count_within_authorized_bound', total_attempts <= 12)
check('all_four_first_attempt_valid_no_failed_or_later_attempts', total_attempts == 4 and all(arm['actual_attempt_count'] == arm['first_technically_valid_attempt'] == 1 for arm in arm_results))
check('completion_all_four', completion['status'] == 'ALL_FOUR_TECHNICALLY_COMPLETE_PENDING_SEMANTIC_REVIEW' and [record['arm'] for record in completion['arms']] == arm_names and completion['new_candidate_or_adoption'] is False)
for record, result in zip(completion['arms'], arm_results):
    check(result['arm'] + ':completion_record_binding', record['exit_code'] == 0 and record['offline_equal_actual'] is True and record['actual_request_sha256'] == result['attempts'][0]['request_sha256'] and record['summary_sha256'] == sha(BASE / 'runtime' / result['arm'] / 'execution_summary.json'))
check('freeze18_unchanged_during_independent_audit', all(sha(path) == original for path, original in freeze_start.items()))
failures = [item['check'] for item in checks if not item['pass']]
report = {'status': 'PASS_ACTUAL_TECHNICAL_ONLY_NOT_SEMANTIC' if not failures else 'FAIL_ACTUAL_TECHNICAL_REVIEW', 'created_at_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reviewer': '/root/llm_repair05/content_analysis_methods', 'scope': 'Independent offline mechanical provenance/attempt/event/raw/aggregate checks only; no expected-label or original-control semantic read', 'authorization_sha256': sha(auth_path), 'preparation_freeze_sha256': sha(freeze_path), 'final_execution_plan_sha256': sha(plan_path), 'independent_preflight_sha256': sha(preflight_path), 'independent_preflight_evidence_sha256': sha(Path(evidence_bind['path'])), 'review_script_sha256': sha(__file__), 'checks_passed': len(checks) - len(failures), 'checks_total': len(checks), 'failures': failures, 'checks': checks, 'frozen_files': freeze_results, 'arms': arm_results, 'total_logical_requests': len(arm_results), 'total_actual_attempts': total_attempts, 'total_tool_or_unknown_item_events': total_tools, 'audit_model_calls': 0, 'audit_CLI_invocations': 0, 'private_input_output_content_disclosed': False, 'expectation_and_design_files_decoded': False, 'source_files_modified': False, 'semantic_accuracy_verified': False, 'limits': ['Opaque SHA checks of private expectation/design freeze members do not read their meaning.', 'The frozen pure structural/literal validator is rerun; it cannot establish label or reason semantics.', 'Command metadata and distinct event thread IDs substantiate isolated requested runs; no provider-internal model revision is exposed or certified.', 'Deleted temporary cwd cannot be forensically inspected after execution; isolation is evidenced by frozen runner code, exact recorded command and distinct temporary paths.', 'All four actual first attempts succeeded; technical-exhaustion stop logic was statically checked, not exercised by this actual execution.', 'No independent heldout accuracy, kappa improvement, full-corpus claim, candidate adoption or continuation of the old08 run follows from this technical PASS.']}
with OUT.open('x', encoding='utf-8') as handle:
    handle.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'checks_passed': report['checks_passed'], 'checks_total': report['checks_total'], 'failure_check_names_only': failures, 'arms': len(arm_results), 'actual_attempts': total_attempts, 'tool_events': total_tools, 'report_path': str(OUT), 'report_sha256': sha(OUT), 'script_sha256': sha(__file__)}, ensure_ascii=False))
