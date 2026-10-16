"""Single-runner read-only review using self-authored toys and fake subprocess.

No main(), CLI, model, private input or expectation file is invoked/read. All run
artifacts below are temporary mock files. Reviewer authored the StageA helpers.
"""
import sys
sys.dont_write_bytecode = True
import copy
import datetime
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parent
RUNNER = CANDIDATE / 'run_candidate09.py'
REPORT = HERE / 'runner_code_review.json'
if REPORT.exists():
    raise SystemExit('Refusing to overwrite runner review')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = load('review_only_candidate09_runner', RUNNER)
inventory = load('review_only_stageA_inventory', CANDIDATE / 'runtime/stageA_context_inventory.py')
validator = load('review_only_stageA_validator', CANDIDATE / 'runtime/validate_stageA.py')
sources = [RUNNER, CANDIDATE / 'prompt_lock.json', CANDIDATE / 'stageA_prompt.txt', CANDIDATE / 'stageB_prompt.txt']
before = {str(path): sha(path) for path in sources}
checks = []


def check(name, passed):
    checks.append({'check': name, 'pass': bool(passed)})


def event_binding(events, raw):
    messages = [json.loads(line)['item']['text'] for line in events.splitlines()
                if json.loads(line).get('type') == 'item.completed'
                and json.loads(line).get('item', {}).get('type') == 'agent_message']
    valid = len(messages) == 1 and runner.canonical(json.loads(messages[0])) == runner.canonical(raw)
    return {'errors': [] if valid else ['mock_event_binding_failure']}


def fixture(folder, statuses=('accepted_structural_literal_zero_tools',), material=False,
            mutate_source=False, startup_failure=False):
    """Run only the real wrapper flow; actual provider transport is replaced."""
    runner.HERE = folder
    runner.RUN_NAMES = {'A': 'toy-stageA', 'B': 'toy-stageB'}
    runner.PROMPTS = {'A': folder / 'toy-A.txt', 'B': folder / 'toy-B.txt'}
    runner.SCHEMAS = {'A': folder / 'toy-A-schema.json', 'B': folder / 'toy-B-schema.json'}
    runner.VALIDATORS = {'A': folder / 'toy-A-validator.py', 'B': folder / 'toy-B-validator.py'}
    runner.DESIGN_FREEZE = folder / 'toy-design.json'
    runner.INPUT_BINDING = folder / 'toy-binding.json'
    for path in list(runner.PROMPTS.values()) + list(runner.SCHEMAS.values()) + list(runner.VALIDATORS.values()) + [runner.DESIGN_FREEZE, runner.INPUT_BINDING]:
        path.write_text('Self-authored mock technical file.\n')
    cli = folder / 'fake-provider-binary-never-executed'
    cli.write_text('Not executable; subprocess is monkeypatched.\n')
    rows = [{'id': 'toy-' + str(i), 'text': 'Alpha does beta.', 'contexts': {}} for i in range(11)]
    source = folder / 'toy-source.json'
    source.write_text(json.dumps({'rows': rows}))
    input_bytes = source.read_bytes()
    ib = {'input_sha256': sha(source)}
    packet = runner.assemble_stageA_packet(rows, inventory)
    request = runner.make_request('A', packet, runner.PROMPTS['A'].read_text())
    output = {'stage': 'current_proposition_context_record', 'rows': [
        {'id': row['id'], 'current_propositions': [{
            'proposition_id': 'p1', 'subject_or_object': 'Alpha',
            'actions_attributes_and_qualifiers': 'does beta',
            'conditional_outcome': 'No conditional outcome is asserted.',
            'unit_quotes': ['Alpha does beta.']}], 'context_records': [],
         'material_status': 'material_issue' if material and index == 0 else 'sufficient',
         'material_note': 'Toy technical material note.'}
        for index, row in enumerate(rows)]}
    calls = []

    def fake_attempt(dest, actual_packet, actual_request, prompt_sha, cli_version, cli_sha, timeout):
        calls.append((copy.deepcopy(actual_packet), actual_request))
        dest.mkdir(parents=True, exist_ok=False)
        (dest / 'input.json').write_text(json.dumps(actual_packet, ensure_ascii=False, indent=2) + '\n')
        (dest / 'request.txt').write_text(actual_request)
        raw = json.dumps(output, ensure_ascii=False)
        (dest / 'raw_output.json').write_text(raw)
        (dest / 'events.jsonl').write_text(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': raw}}) + '\n')
        status = statuses[min(len(calls) - 1, len(statuses) - 1)]
        meta = {'status': status, 'errors': [] if status.startswith('accepted') else ['toy_technical_failure'],
                'tool_event_count': 0, 'prompt_sha256': prompt_sha}
        (dest / 'run_metadata.json').write_text(json.dumps(meta))
        if mutate_source:
            source.write_text('changed mock source after request')
        return meta

    base = SimpleNamespace(CLI=cli, MODEL=runner.MODEL, EFFORT=runner.EFFORT,
                           run_attempt=fake_attempt, event_output_binding_audit=event_binding,
                           event_audit=lambda events: {'tool_or_unknown_item_event_count': 0,
                               'completed_turns': 1, 'turn_errors': []})
    runner.load_runtime = lambda: (base, inventory, validator)
    original_subprocess = runner.subprocess.run

    def fake_version(*args, **kwargs):
        if startup_failure:
            raise RuntimeError('Self-authored mock version-query failure')
        return SimpleNamespace(returncode=0, stdout='mock-version\n', stderr='')

    runner.subprocess.run = fake_version
    exception = None
    try:
        result = runner.execute_stage('A', packet, request, ib, source, input_bytes,
                                      {'path': 'toy-authority', 'sha256': 'toy'})
    except RuntimeError as exc:
        exception = type(exc).__name__
        result = None
    finally:
        runner.subprocess.run = original_subprocess
    run = folder / 'runs' / 'toy-stageA'
    receipt = json.loads((run / 'final_stage_scope_receipt.json').read_text())
    return SimpleNamespace(rows=rows, packet=packet, request=request, output=output, source=source,
                           ib=ib, result=result, exception=exception, calls=calls, run=run,
                           receipt=receipt, base=base)


with tempfile.TemporaryDirectory(prefix='candidate09-readonly-runner-review-') as temp:
    root = Path(temp)
    def case(name, **kwargs):
        folder = root / name
        folder.mkdir()
        return fixture(folder, **kwargs)

    good = case('good')
    check('first_technical_valid_one_attempt', good.result == 0 and len(good.calls) == 1)
    check('A_sealed_and_B_explicit_NOT_RUN', (good.run / 'stageA_seal.json').exists() and good.receipt['stage_states']['B']['state'] == 'NOT_RUN')
    check('A_original_raw_byte_copy', (good.run / 'all_stageA_records.json').read_bytes() == (good.run / 'attempts/attempt-01/raw_output.json').read_bytes())
    gate = {'status': 'PASS_ROOT_STAGEA_SEMANTIC_REVIEW', 'candidate': runner.CANDIDATE,
            'approved_for_stageB': True, 'reviewed_rows': 11, 'confirmed_semantic_errors': 0,
            'original_stageA_not_edited': True, 'stageA_seal_sha256': sha(good.run / 'stageA_seal.json'),
            'stageA_output_sha256': sha(good.run / 'all_stageA_records.json'),
            'input_sha256': good.ib['input_sha256'],
            'opinion': 'SELF_AUTHORED_GATE_OPINION_MUST_NOT_LEAK',
            'expected_labels': 'SELF_AUTHORED_EXPECTATION_MUST_NOT_LEAK'}
    gate_path = root / 'toy-gate.json'; gate_path.write_text(json.dumps(gate))
    auth = {'stageA_seal': runner.binding(good.run / 'stageA_seal.json'),
            'stageA_semantic_gate': runner.binding(gate_path)}
    raw, gate_bindings = runner.check_stageA_source(good.rows, good.ib, auth)
    bpacket = runner.assemble_stageB_packet(good.rows, raw)
    brequest = runner.make_request('B', bpacket, 'Toy B prompt only.')
    check('gate_opinion_and_expectation_not_in_B_packet_or_request', all(token not in brequest for token in ['SELF_AUTHORED_GATE_OPINION_MUST_NOT_LEAK', 'SELF_AUTHORED_EXPECTATION_MUST_NOT_LEAK', 'stageA_semantic_gate']) and set(bpacket) == {'rows', 'stageA_records'})
    check('B_original_rows_and_same_ID_record_SHA_bound', bpacket['rows'] == good.rows and all(record['id'] == record['record']['id'] == good.rows[i]['id'] and record['record_sha256'] == runner.row_sha(record['record']) for i, record in enumerate(bpacket['stageA_records'])))
    check('gate_bindings_returned_only_as_execution_metadata', set(gate_bindings) == {'stageA_seal', 'stageA_semantic_gate'})
    copied = good.run / 'all_stageA_records.json'
    changed = json.loads(copied.read_text()); changed['rows'][0]['material_note'] = 'Toy post-seal hand edit.'
    copied.write_text(json.dumps(changed))
    rejected = False
    try:
        runner.check_stageA_source(good.rows, good.ib, auth)
    except AssertionError:
        rejected = True
    check('postseal_A_hand_edit_blocks_B_source_check', rejected)
    try:
        runner.execute_stage('A', good.packet, good.request, good.ib, good.source, good.source.read_bytes(), {})
    except AssertionError:
        check('fresh_run_existing_A_restart_rejected', True)
    else:
        check('fresh_run_existing_A_restart_rejected', False)

    retry = case('retry', statuses=('failed_attempt_preserved', 'accepted_structural_literal_zero_tools'))
    check('only_technical_failure_allows_identical_retry', retry.result == 0 and len(retry.calls) == 2 and retry.calls[0] == retry.calls[1])
    check('first_valid_stops_before_attempt03', not (retry.run / 'attempts/attempt-03').exists())
    exhausted = case('exhausted', statuses=('failed_attempt_preserved',))
    check('max3_failed_attempts_preserved', exhausted.result == 2 and len(exhausted.calls) == 3 and all((exhausted.run / ('attempts/attempt-%02d' % i)).exists() for i in range(1, 4)))
    check('exhaustion_B_explicit_NOT_RUN', exhausted.receipt['stage_states']['B']['state'] == 'NOT_RUN')
    material = case('material', material=True)
    check('material_issue_valid_A_not_retried', material.result == 0 and len(material.calls) == 1 and validator.validate({'rows': material.rows}, material.output) == [])
    check('material_issue_seal_count_and_B_NOT_RUN', json.loads((material.run / 'stageA_seal.json').read_text())['stageA_material_issue_count'] == 1 and material.receipt['stage_states']['B']['state'] == 'NOT_RUN')
    try:
        runner.assemble_stageB_packet(material.rows, material.output)
    except AssertionError:
        check('material_issue_B_assembler_rejected', True)
    else:
        check('material_issue_B_assembler_rejected', False)
    failed_material = case('failed-material', material=True, statuses=('failed_attempt_preserved',))
    check('material_flag_on_failed_technical_output_stops_without_retry', failed_material.result == 2 and len(failed_material.calls) == 1)
    startup = case('startup', startup_failure=True)
    check('startup_version_failure_0_attempts_exception_preserved', startup.exception == 'RuntimeError' and not startup.calls and (startup.run / 'execution_exception.json').exists())
    check('startup_failure_B_explicit_NOT_RUN', startup.receipt['stage_states']['B']['state'] == 'NOT_RUN')
    mutation = case('source-mutation', mutate_source=True)
    check('source_mutation_is_recorded_not_hard_stopped_observation', mutation.result == 0 and mutation.receipt['source_input_unchanged'] is False and (mutation.run / 'stageA_seal.json').exists())

check('runner_and_locked_prompts_unchanged', all(sha(path) == digest for path, digest in before.items()))
failures = [item['check'] for item in checks if not item['pass']]
report = {'status': 'PASS_NORMAL_FLOW_WITH_TWO_HARDENING_FINDINGS' if not failures else 'FAIL_REVIEW_MOCK_CHECK',
          'created_at_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'reviewer_role': 'StageA inventory/validator author; independent read-only reviewer of runner authored by parent, not external validation',
          'runner_path': str(RUNNER), 'runner_sha256': sha(RUNNER),
          'locked_source_bindings': [{'path': path, 'sha256': digest, 'unchanged': sha(path) == digest} for path, digest in before.items()],
          'checks_passed': len(checks) - len(failures), 'checks_total': len(checks), 'failures': failures, 'checks': checks,
          'positive_static_paths': [
              {'lines': [81, 95], 'support': 'A packet adds only inventory; B packet includes original rows and same-ID original A records/recordSHA, no gate argument.'},
              {'lines': [97, 143], 'support': 'A sealed files, copied/raw objects, original packet/request, unique completed message and record SHA are bound; root gate is consumed but not returned as packet data.'},
              {'lines': [145, 155], 'support': 'Separate stage authorization, scope/model/size/freeze locks and false semantic-retry/automatic-next-stage permissions.'},
              {'lines': [194, 234], 'support': 'First technical valid attempt only; material flags stop further retries; original raw bytes copied; A sealed but no B call.'},
              {'lines': [250, 269], 'support': 'Fresh immutable stage run; executor/startup exception and both A/B state receipts preserved.'},
              {'lines': [280, 298], 'support': 'B assembly, even plan-only, requires B authorization and original A semantic gate. No automatic second stage.'}],
          'findings': [
              {'id': 'SOURCE_IMMUTABILITY_NOT_HARD_STOP', 'severity': 'bounded_hardening_finding', 'lines': [215, 248],
               'observed': 'Source mutation toy still returns0 and seals TECHNICAL_COMPLETE; receipt records source_input_unchanged=false. Later main read_input hash lock would reject B, but A completion is not itself a hard immutability gate.',
               'minimal_fix': 'Before successful summary/seal, assert current source SHA equals ib input_sha256, retaining raw attempts and exception/receipt. Do not repair source or output.'},
              {'id': 'PRE_EXECUTION_REJECTION_WITHOUT_PERSISTENT_NOT_RUN', 'severity': 'audit_scope_precision', 'lines': [277, 286],
               'observed': 'Design/input/authorization/StageA-gate rejection occurs before execute_stage and its receipt finally. No actual model call starts, but persistent explicit B NOT_RUN is not created for these pre-execution failures.',
               'minimal_fix': 'Either scope the explicit failure-receipt guarantee to started executions, or add a separate fresh immutable pre-execution-rejection receipt containing only stage/status/error type and A/B NOT_RUN metadata.'}],
          'mock_transport': 'All provider calls and the version query replaced by self-authored in-process functions; real main not called.',
          'real_CLI_invocations': 0, 'real_model_calls': 0, 'private_input_expectation_or_real_policy_reads': 0,
          'source_files_modified': False, 'semantic_correctness_verified': False,
          'limits': ['Mocks test wrapper control flow, not provider behavior, schema transport acceptance or model semantics.', 'Frozen design/input binding manifests and actual11 inputs were not read for this runner review.', 'A trusted root authorization and semantic-gate binding remains required; no claim against adversarial rewriting of all authorization and audit files.']}
with REPORT.open('x', encoding='utf-8') as handle:
    handle.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'checks_passed': report['checks_passed'], 'checks_total': report['checks_total'], 'failures': failures, 'report_path': str(REPORT), 'report_sha256': sha(REPORT), 'script_sha256': sha(__file__)}, ensure_ascii=False))
