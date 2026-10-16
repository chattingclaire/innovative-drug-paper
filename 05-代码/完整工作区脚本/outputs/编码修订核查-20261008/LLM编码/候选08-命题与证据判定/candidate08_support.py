"""Local binding/phase helpers. No CLI/model or semantic selection."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD07 = HERE.parent / '候选方案'
OLD05 = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate05-preparation'
OLD06 = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate06-design/revision-v2'
PLAN = HERE / 'candidate08_execution_plan_PROPOSED.json'
FREEZE = HERE / 'design_freeze.json'
RUNTIME = HERE / 'runtime-unchanged-v2'
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def binding(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def dump_new(path, obj):
    path = Path(path)
    value = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    if path.exists():
        assert path.read_text() == value, f'Never overwrite a different existing record: {path}'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)


def check_binding(x):
    assert sha(x['path']) == x['sha256'], f'Frozen source changed: {x["path"]}'
    if 'bytes' in x:
        assert Path(x['path']).stat().st_size == x['bytes']


def check_plan(plan):
    keys = ['new24', 'independent16', 'inherited62', 'inherited24', 'inherited20', 'exposed240']
    assert plan['scope_run_keys'] == keys
    assert plan['scope_sizes'] == [24, 16, 62, 24, 20, 240]
    assert [r['run_key'] for r in plan['runs']] == keys
    assert sum(r['logical_requests'] for r in plan['runs']) == plan['nominal_logical_requests'] == 17
    assert plan['maximum_identical_technical_attempts'] == 51
    assert plan['model'] == 'gpt-5.6-sol' and plan['reasoning_effort'] == 'medium'
    assert [p['run_keys'] for p in plan['phases']] == [keys[:2], keys[2:5], keys[5:]]
    for run in plan['runs']:
        check_binding(run['input_binding'])
        cmd = run['future_execution_command_after_separate_root_authorization_only']
        assert cmd[cmd.index('--input') + 1] == run['input_binding']['path']
        assert cmd[cmd.index('--expected-input-sha256') + 1] == run['input_binding']['sha256']
        assert cmd[cmd.index('--expected-n') + 1] == str(run['n'])
        assert cmd[cmd.index('--run-name') + 1] == run['run_name']
        assert cmd[cmd.index('--max-attempts') + 1] == '3'
        assert cmd[cmd.index('--batch-size') + 1] == '25'
        assert cmd[cmd.index('--prompt') + 1] == str(HERE/'candidate08_prompt_PROPOSED.txt')


def verify_freeze():
    freeze = read(FREEZE)
    assert freeze['nominal_logical_requests'] == 17 and freeze['max_identical_technical_attempts'] == 51
    assert freeze['independent_preflight_no_blocking_findings'] is True
    for x in freeze['files'] + freeze['source_bindings']:
        check_binding(x)
    plan = read(PLAN)
    check_plan(plan)
    assert sha(HERE/'candidate08_prompt_PROPOSED.txt') == read(HERE/'prompt_lock_before_independent_inputs.json')['prompt']['sha256']
    return freeze, plan


def check_authorization(authorization, freeze_sha, plan, phase=None):
    assert authorization['authorized'] is True
    assert authorization['design_freeze_sha256'] == freeze_sha
    allowed_runs = plan['runs']
    if phase is not None:
        if authorization.get('authorized_phase') is not None:
            assert authorization['authorized_phase'] == phase
            keys = next(p['run_keys'] for p in plan['phases'] if p['phase'] == phase)
            allowed_runs = [r for r in plan['runs'] if r['run_key'] in keys]
        else:
            assert phase in authorization.get('authorized_phases', []), 'Phase authorization must be explicit.'
    assert authorization['scope_run_keys'] == [r['run_key'] for r in allowed_runs]
    assert authorization['scope_sizes'] == [r['n'] for r in allowed_runs]
    assert authorization['model'] == 'gpt-5.6-sol' and authorization['reasoning_effort'] == 'medium'
    logical = sum(r['logical_requests'] for r in allowed_runs)
    assert authorization['max_logical_requests'] == logical and authorization['max_technical_attempts'] == logical * 3
    assert authorization['first_technically_valid_only'] is True
    assert authorization['semantic_retry_allowed'] is False
    assert authorization['full_corpus_or_adoption_allowed'] is False
    assert authorization['phase_semantic_gate_required'] is True


def check_phase_gate(gate, phase, freeze_sha, plan):
    """A later phase needs a root-reviewed complete semantic record, not a score."""
    assert gate['status'] == 'PASS_NO_CONFIRMED_SEMANTIC_ERROR'
    assert gate['phase'] == phase and gate['design_freeze_sha256'] == freeze_sha
    assert gate['root_reviewed_and_approved_to_continue'] is True
    assert gate['confirmed_semantic_error_count'] == 0
    assert gate['all_rows_all_five_dimensions_and_fields_reviewed'] is True
    assert gate['boundary_disputes_separately_retained_not_forced'] is True
    declared = next(p for p in plan['phases'] if p['phase'] == phase)
    runs = [r for r in plan['runs'] if r['run_key'] in declared['run_keys']]
    assert gate['run_keys'] == declared['run_keys']
    assert gate['reviewed_rows'] == sum(r['n'] for r in runs)
    assert gate['reviewed_dimension_cells'] == 5 * gate['reviewed_rows']
    expected = [binding(RUNTIME/r['run_name']/'all_predictions.json') for r in runs]
    assert gate['actual_output_bindings'] == expected
    assert gate['semantic_review_report_bindings'], 'Actual semantic reports required.'
    for x in gate['semantic_review_report_bindings']:
        check_binding(x)
    qa_path = HERE/'execution-audit'/phase/'candidate08_technical_QA.json'
    assert gate['technical_QA_binding'] == binding(qa_path)
    qa = read(qa_path)
    assert qa['status'] == 'PASS_TECHNICAL_ONLY_SEMANTIC_REVIEW_PENDING'
    assert set(declared['run_keys']) <= set(qa['completed_run_keys'])


def source_paths():
    """Whole files hashed mechanically; no protected text/labels displayed."""
    paths = [OLD05/'audit_candidate05_v2.py', OLD05/'historical_comparison_freeze.json',
        OLD05/'runtime-v2/run_production_v32.py',
        OLD05/'runtime-v2/exposed240-candidate05-first-run/all_predictions.jsonl',
        OLD05/'runtime-v2/exposed240-candidate05-first-run/all_predictions.json',
        OLD06/'runtime-unchanged-v2/exposed240-candidate06-first-run/all_predictions.jsonl',
        OLD06/'runtime-unchanged-v2/exposed240-candidate06-first-run/all_predictions.json',
        OLD07/'runtime-unchanged-v2/exposed240-candidate07-first-run/all_predictions.jsonl',
        OLD07/'runtime-unchanged-v2/exposed240-candidate07-first-run/all_predictions.json',
        OLD07/'candidate07_prompt_PROPOSED.txt', OLD07/'design_freeze.json',
        OLD07/'predeclared_acceptance_PROPOSED.json',
        OLD07/'semantic-review/candidate07_final_semantic_gate_report_PRIVATE.json',
        OLD07/'semantic-review/independent-controls/candidate07_actual106_independent_semantic_review.json',
        OLD07/'execution-audit/candidate07_all240_comparison_REDACTED_PRIVATE.json',
        ROOT/'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md',
        ROOT/'outputs/coding-revision-20261007-r3/protocol/共用操作说明-v1.4.md',
        ROOT/'outputs/coding-revision-20261007-r3/llm-candidate03-development/candidate03_prompt.txt',
        ROOT/'outputs/coding-revision-20261007-r3/llm-candidate03-development/full-corpus-candidate03-material-v14-development/frozen_prompt.txt',
        ROOT/'outputs/coding-revision-20261007-r3/effective_blind_inputs_v14.jsonl',
        ROOT/'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py',
        ROOT/'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json',
        Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')]
    paths += [Path(x['path']) for x in read(OLD05/'historical_comparison_freeze.json')['frozen_files'].values()]
    paths += [OLD07/x for x in ['exposed240_inputs_UNCHANGED.jsonl','synthetic62_inputs_UNCHANGED.jsonl',
        'synthetic24_inputs_UNCHANGED.jsonl','synthetic20_inputs_PROPOSED.jsonl','synthetic106_expected_PRIVATE_PROPOSED.json']]
    paths += [OLD07/'runtime-unchanged-v2'/x for x in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']]
    paths += [Path(r['input_binding']['path']) for r in read(PLAN)['runs'] if r['run_key']=='independent16']
    return sorted(set(p.resolve() for p in paths))
