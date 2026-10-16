"""Independent offline checks only: no CLI, network, or model invocation."""
import ast
import contextlib
import hashlib
import io
import json
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OLD = BASE.parents[1] / '候选08-命题与证据判定'
checks = []
failures = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(name, ok, detail=None):
    checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
    if not ok:
        failures.append(name)


def load(path):
    return json.loads(Path(path).read_text())


def binding(path):
    path = Path(path)
    return {'path': str(path.resolve()), 'sha256': sha(path), 'bytes': path.stat().st_size}


freeze_path = HERE / 'preparation_freeze.json'
plan_path = HERE / 'final_execution_plan.json'
check('preparation_freeze_exact_expected_SHA', sha(freeze_path) == '09a1c615192b2f805c4d2a79b892f6bbbbe11915ab520d286ff7c4956587203b')
check('final_plan_exact_expected_SHA', sha(plan_path) == '8512c40ea7ad13b34ea4e06012694d126fed47a86b71819922b50d54e89a9a6a')
freeze, plan = load(freeze_path), load(plan_path)
frozen_before = {}
for entry in freeze['files']:
    path = Path(entry['path'])
    frozen_before[str(path)] = sha(path)
    check('freeze_SHA_and_bytes:' + str(path.relative_to(BASE)) if path.is_relative_to(BASE) else 'freeze_SHA_and_bytes:' + path.name,
          sha(path) == entry['sha256'] and path.stat().st_size == entry['bytes'])
manifest = load(BASE / 'mechanism_design_manifest_PROPOSED.json')
for entry in [manifest['plan'], manifest['private_expected_controls'], *manifest['input_files'], manifest['builder'], *manifest['source_bindings']]:
    check('original_design_binding:' + Path(entry['path']).name,
          sha(entry['path']) == entry['sha256'] and Path(entry['path']).stat().st_size == entry['bytes'])
for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']:
    check('runtime_copy_byte_identical:' + name,
          (HERE / 'runtime' / name).read_bytes() == (OLD / 'runtime-unchanged-v2' / name).read_bytes())

private = load(BASE / 'five_new_bases_FULL5_EXPECTATIONS_PRIVATE_FROZEN.json')
check('frozen_four_hard_one_boundary', private['hard_scored_bases'] == 4 and private['boundary_bases'] == 1 and len(private['cases']) == 5)
original_cases = private['cases']
ids = [case['id'] for case in original_cases]
prompt_path = OLD / 'candidate08_prompt_PROPOSED.txt'
prompt = prompt_path.read_text()
check('original08_prompt_SHA_unchanged', sha(prompt_path) == 'd79c097443fa249051c5264da1ff532ddf7d984225ac3e776807de95f7f21803')
check('four_requests_maximum_twelve_technical_attempts', plan['logical_requests'] == 4 and plan['maximum_identical_technical_attempts'] == 12 and len(plan['arms']) == 4)
check('model_effort_fixed', plan['model'] == 'gpt-5.6-sol' and plan['reasoning_effort'] == 'medium')
check('no_candidate_adoption_or_original08_continuation', plan['no_adoption_or_original08_continuation_authorized'] is True and plan['original08_status'] == 'FAIL_CONFIRMED_SEMANTIC_ERROR')
check('execution_order_fixed', plan['execution_order'] == [arm['arm'] for arm in plan['arms']])

runner_source = (HERE / 'runtime' / 'run_production_v32.py').read_text()
runner_tree = ast.parse(runner_source)
request_nodes = [node.value for node in ast.walk(runner_tree) if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == 'request' for target in node.targets)]
check('runner_one_explicit_request_expression', len(request_nodes) == 1)
request_expression = compile(ast.Expression(request_nodes[0]), '<frozen-request-expression>', 'eval')
arm_evidence = []
normalized = []
for arm in plan['arms']:
    arm_name = arm['arm']
    packet = load(arm['input']['path'])
    rows = packet['rows']
    check(arm_name + ':input_packet_exact_binding', binding(arm['input']['path']) == arm['input'])
    check(arm_name + ':offline_packet_exact_input_bytes', Path(arm['input']['path']).read_bytes() == Path(arm['offline_packet']['path']).read_bytes())
    check(arm_name + ':packet_rows_only_no_expected_or_reference_fields', set(packet) == {'rows'} and len(rows) == 5)
    check(arm_name + ':same_ID_sequence', [row['id'] for row in rows] == ids)
    expected_keys = ['id', 'contexts', 'text'] if arm['requested_row_serialization'] == 'before_text' else ['id', 'text', 'contexts']
    normalized_rows = []
    for i, (row, original) in enumerate(zip(rows, original_cases)):
        context = row['contexts'][arm['field_key']]
        check(arm_name + f':row_{i+1}_key_order', list(row) == expected_keys)
        check(arm_name + f':row_{i+1}_field_name_only', set(row['contexts']) == {arm['field_key']})
        check(arm_name + f':row_{i+1}_complete_original_current_and_context_text', row['text'] == original['text'] and len(context) == 1 and context[0]['text'] == original['following_text'])
        check(arm_name + f':row_{i+1}_same_true_position_no_invented_typed_status', set(context[0]) == {'source_position', 'text'} and context[0]['source_position'] == original['source_position'] == 'following_adjacent')
        normalized_rows.append({'id': row['id'], 'text': row['text'], 'context': context})
    normalized.append(normalized_rows)
    independently_assembled = (prompt + '\n\n--- 本批冻结盲法输入 ---\n' + json.dumps(packet, ensure_ascii=False)
                               + '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。')
    runner_assembled = eval(request_expression, {'__builtins__': {}, 'prompt': prompt, 'packet': packet, 'json': json})
    stored_request = Path(arm['offline_request']['path']).read_bytes()
    check(arm_name + ':independent_formula_equals_runner_AST_equals_frozen_request_bytes',
          independently_assembled == runner_assembled and independently_assembled.encode() == stored_request)
    arguments = arm['runner_arguments']
    arg_map = dict(zip(arguments[::2], arguments[1::2]))
    check(arm_name + ':arguments_only_frozen_input_prompt_and_technical_limits',
          set(arg_map) == {'--input', '--expected-input-sha256', '--prompt', '--expected-n', '--run-name', '--batch-size', '--workers', '--max-attempts', '--timeout-seconds', '--purpose'}
          and arg_map['--input'] == arm['input']['path'] and arg_map['--expected-input-sha256'] == arm['input']['sha256']
          and arg_map['--prompt'] == str(prompt_path) and arg_map['--expected-n'] == '5' and arg_map['--batch-size'] == '25'
          and arg_map['--workers'] == '1' and arg_map['--max-attempts'] == '3' and arg_map['--run-name'] == arm_name)
    check(arm_name + ':actual_arm_not_started', not (HERE / 'runtime' / arm_name).exists())
    arm_evidence.append({'arm': arm_name, 'field_key': arm['field_key'], 'row_key_order': expected_keys,
                         'input': binding(arm['input']['path']), 'offline_request': binding(arm['offline_request']['path']),
                         'n': len(rows), 'normalized_semantic_content_SHA': hashlib.sha256(json.dumps(normalized_rows, ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
check('all_arm_text_position_and_ID_order_equal_after_only_context_key_normalization', all(rows == normalized[0] for rows in normalized))
by_name = {arm['arm']: arm for arm in plan['arms']}
for side in ['before', 'after']:
    typed = Path(by_name['field_typed_context_' + side]['offline_request']['path']).read_text()
    neutral = Path(by_name['field_neutral_context_' + side]['offline_request']['path']).read_text()
    prefix_length = len(prompt)
    check('exact_field_only_request_contrast:' + side,
          typed[:prefix_length] == neutral[:prefix_length] and typed[prefix_length:].replace('"structured_following_units"', '"provided_context_units"') == neutral[prefix_length:])

wrapper_source = (BASE / 'execute_root_diagnostic.py').read_text()
ast.parse(wrapper_source)
check('wrapper_static_separate_authorization_preflight_freeze_and_bounds', all(fragment in wrapper_source for fragment in [
    "auth['preparation_freeze_sha256']", "auth['independent_preflight']['sha256']", "auth['independent_preflight_pass'] is True",
    "auth['maximum_logical_requests']==4", "auth['maximum_identical_technical_attempts']==12", "marker.open('x')",
    "assert not run.exists()", "actual.read_bytes()==Path(arm['offline_request']['path']).read_bytes()"
]))
check('runner_first_valid_pure_technical_selection_static', all(fragment in runner_source for fragment in [
    'MODEL=\'gpt-5.6-sol\';EFFORT=\'medium\'', "if m['status']=='accepted_structural_literal_zero_tools':selected=attempt;break",
    'for ai in range(1,a.max_attempts+1):', "'selection_uses_metric_or_label_values':False",
    "'--ephemeral'", "'--ignore-user-config'", "'--ignore-rules'", "'--sandbox','read-only'"
]))


def mock_wrapper_case(mode):
    """Execute only the wrapper control flow against fake Popen, never a process."""
    with tempfile.TemporaryDirectory(prefix='independent-diag-wrapper-offline-') as temp:
        folder = Path(temp)
        arms = []
        for index in range(4):
            name = 'test-arm-' + str(index + 1)
            offline = folder / (name + '-offline.txt')
            offline.write_bytes(b'offline synthetic fixture only')
            arms.append({'arm': name, 'offline_request': {'path': str(offline)}, 'runner_arguments': ['--run-name', name]})
        (folder / 'final_execution_plan.json').write_text(json.dumps({'arms': arms}))
        (folder / 'preparation_freeze.json').write_text(json.dumps({'files': []}))
        pf = folder / 'fake-preflight.json'
        pf.write_text('{}')
        (folder / 'root_execution_authorization.json').write_text(json.dumps({
            'preparation_freeze_sha256': sha(folder / 'preparation_freeze.json'),
            'status': 'AUTHORIZED_BOUNDED_FOUR_ARM_DIAGNOSTIC_ONLY',
            'independent_preflight': {'path': str(pf), 'sha256': sha(pf)}, 'independent_preflight_pass': True,
            'maximum_logical_requests': 4, 'maximum_identical_technical_attempts': 12}))
        launched = []

        class FakeProcess:
            stdout = []

            def __init__(self, command, **kwargs):
                name = command[command.index('--run-name') + 1]
                launched.append(name)
                run = folder / 'runtime' / name
                run.mkdir(parents=True)
                self.code = 2 if mode == 'technical_failure_first' and len(launched) == 1 else 0
                (run / 'execution_summary.json').write_text(json.dumps({'status': 'partial_or_failed_preserved' if self.code else 'complete_actual_calls_structurally_valid'}))
                batch = run / 'batches' / 'batch-0001'
                batch.mkdir(parents=True)
                (batch / 'request.txt').write_bytes(b'different fixture' if mode == 'request_mismatch_first' and len(launched) == 1 else b'offline synthetic fixture only')

            def wait(self):
                return self.code

        namespace = {'__file__': str(BASE / 'execute_root_diagnostic.py'), '__name__': 'offline_wrapper_only'}
        exec(compile(wrapper_source, '<exact-wrapper-offline-mock>', 'exec'), namespace)
        namespace['PREP'] = folder
        namespace['subprocess'] = types.SimpleNamespace(Popen=FakeProcess, PIPE=-1, STDOUT=-2)
        namespace['sys'] = types.SimpleNamespace(executable='/OFFLINE_FAKE_PYTHON_NEVER_LAUNCHED')
        exception = None
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                namespace['main']()
            except (SystemExit, AssertionError) as exc:
                exception = type(exc).__name__ + ':' + str(exc)
        terminal = load(folder / 'actual_execution_completion.json') if (folder / 'actual_execution_completion.json').exists() else None
        if mode == 'all_success':
            ok = len(launched) == 4 and terminal['status'] == 'ALL_FOUR_ACTUAL_REQUESTS_COMPLETE_SEMANTIC_REVIEW_PENDING'
        elif mode == 'technical_failure_first':
            ok = len(launched) == 1 and len(terminal['arms']) == 4 and all(row['status'] == 'NOT_RUN_AFTER_TECHNICAL_EXHAUSTION' for row in terminal['arms'][1:]) and exception.startswith('SystemExit:2')
        else:
            ok = len(launched) == 1 and exception is not None and exception.startswith('AssertionError:actual request differs')
        return {'fixture': mode, 'pass': ok, 'fake_Popen_count': len(launched), 'real_subprocess_count': 0,
                'terminal_present': terminal is not None, 'exception': exception,
                'request_mismatch_handling_limit': 'Mismatch raises and prevents all later launches, but does not synthesize a completion record; root must preserve exception transcript.' if mode == 'request_mismatch_first' else None}


mock_results = [mock_wrapper_case(mode) for mode in ['all_success', 'technical_failure_first', 'request_mismatch_first']]
for result in mock_results:
    check('offline_mock_wrapper:' + result['fixture'], result['pass'])
check('no_actual_start_marker_created', not (HERE / 'actual_execution_start.json').exists())
check('no_execution_authorization_claimed_by_this_review', not (HERE / 'root_execution_authorization.json').exists())
check('frozen_sources_unchanged_after_review', all(sha(path) == original_sha for path, original_sha in frozen_before.items()))

evidence_path = HERE / 'independent_execution_preflight_evidence.json'
evidence = {'created_at_UTC': datetime.now(timezone.utc).isoformat(), 'checks': checks, 'arm_request_metadata_no_original_text_or_expectations': arm_evidence,
            'offline_mock_results': mock_results, 'real_model_calls': 0, 'real_CLI_invocations': 0,
            'scope': 'Existing frozen five synthetic bases only; no new reserved texts, human labels, actual model outputs or model calls read/generated.'}
evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
report = {
    'status': 'PASS_OFFLINE_INDEPENDENT_EXECUTION_PREFLIGHT_NOT_EXECUTION_AUTHORIZATION' if not failures else 'FAIL_OFFLINE_INDEPENDENT_EXECUTION_PREFLIGHT',
    'created_at_UTC': datetime.now(timezone.utc).isoformat(), 'blocking_findings': failures, 'failures': failures,
    'checks_passed': sum(row['pass'] for row in checks), 'checks_total': len(checks),
    'real_model_calls': 0, 'real_CLI_invocations': 0, 'source_files_modified': False, 'frozen_files_count': len(freeze['files']),
    'source_bindings': [binding(freeze_path), binding(plan_path), binding(BASE / 'execute_root_diagnostic.py'), binding(BASE / 'prepare_root_execution.py'), binding(Path(__file__)), *freeze['files']],
    'evidence_binding': binding(evidence_path),
    'actual_verified': [
        'Four independent requests, five identical synthetic base IDs in fixed order in each request; four hard bases and one unscored boundary.',
        'All original current text and full following text retained byte-for-byte as string values; same following_adjacent source-position metadata; absent typed status unchanged.',
        'Only contextual field key and JSON row key order vary; unchanged original08 prompt, schema, validator and runner copies.',
        'Request equals independently assembled full prompt plus exact serialized rows and fixed suffix; no expected labels, rationales, scores, manual anchors or private expectation-file material enter input.',
        'Frozen gpt-5.6-sol/medium; four logical requests, one five-row batch per arm, at most three identical purely technical attempts each; first technically valid selected, all attempts preserved.',
        'Wrapper requires separate root authorization bound to exact preparation freeze and preflight; rejects previous start marker/existing arm and preserves original08 FAIL.',
        'Mocked original-wrapper control flow completes four successful fake runs, stops after first exhausted technical run with other three NOT_RUN, and halts after request mismatch without later launches.'
    ],
    'limits_and_nonblocking_observations': [
        'No model execution has been authorized or performed by this reviewer. Actual request equality and output provenance still require postexecution verification on all attempts.',
        'Unexpected request-byte mismatch raises AssertionError before a completion file; it blocks later arms, but the root execution transcript is needed to preserve that failure. This was verified with a fake subprocess and does not loosen byte equality.',
        'This is a small synthetic representation diagnostic, not external human validity, a new adopted candidate, a probability accuracy estimate, or proof of a latent causal mechanism.',
        'The field_typed arm name denotes the original field name only; all five synthetic examples lack typed-status metadata and do not test production typed-status branches.'
    ],
    'original08_status': 'FAIL_CONFIRMED_SEMANTIC_ERROR', 'original08_real240_and_full4924': 'NOT_RUN',
    'new_candidate_or_adoption_authorized': False, 'root_separate_authorization_required': True
}
report_path = HERE / 'independent_execution_preflight.json'
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'passed': report['checks_passed'], 'total': report['checks_total'],
                  'blocking_findings': failures, 'report': binding(report_path), 'evidence': binding(evidence_path)}, ensure_ascii=False))
if failures:
    raise SystemExit(1)
