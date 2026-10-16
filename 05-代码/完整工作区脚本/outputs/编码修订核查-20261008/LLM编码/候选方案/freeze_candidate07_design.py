"""Freeze only after independent preflight; this program never calls a model."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD05 = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate05-preparation'
OLD06 = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate06-design/revision-v2'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def binding(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def main():
    target = HERE / 'design_freeze.json'
    assert not target.exists(), 'Preserve frozen history; never overwrite a freeze.'
    preflight_path = HERE / 'independent-preflight/candidate07_independent_preflight_v2.json'
    preflight = read(preflight_path)
    assert not preflight['blocking_findings']
    assert preflight['real_model_calls'] == 0 and preflight['real_CLI_invocations'] == 0
    assert preflight['source_files_modified'] is False
    for source in preflight['source_bindings']:
        assert sha(source['path']) == source['sha256'], source['path']
    for path in HERE.rglob('*.py'):
        ast.parse(path.read_text())
    marker = '--- 冻结的完整手册（原样） ---'
    prompt = (HERE / 'candidate07_prompt_PROPOSED.txt').read_text()
    assert prompt.split(marker, 1)[1] == (OLD06 / 'candidate06_prompt_PROPOSED.txt').read_text().split(marker, 1)[1]
    assert 'RECODE25-' not in prompt and '0.80' not in prompt
    for old_name, new_name in [('exposed240_inputs_UNCHANGED.jsonl', 'exposed240_inputs_UNCHANGED.jsonl'),
                              ('synthetic62_inputs_UNCHANGED.jsonl', 'synthetic62_inputs_UNCHANGED.jsonl'),
                              ('synthetic24_inputs_PROPOSED.jsonl', 'synthetic24_inputs_UNCHANGED.jsonl'),
                              ('synthetic86_expected_PRIVATE_PROPOSED.json', 'synthetic86_expected_INHERITED_PRIVATE.json')]:
        assert (OLD06 / old_name).read_bytes() == (HERE / new_name).read_bytes()
    for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']:
        assert (HERE / 'runtime-unchanged-v2' / name).read_bytes() == (OLD06 / 'runtime-unchanged-v2' / name).read_bytes()
    prior_delivery = OLD06 / 'candidate06_execution_delivery_freeze.json'
    assert sha(prior_delivery) == '2e5b9e7fc38228fb6b3467efb2380dd12a6bd0fdf34ac70aabfc792658865c32'
    assert all(sha(x['path']) == x['sha256'] for x in read(prior_delivery)['files'])
    plan = read(HERE / 'candidate07_execution_plan_PROPOSED.json')
    assert [x['n'] for x in plan['runs']] == [240, 62, 24, 20]
    for run in plan['runs']:
        cmd = run['future_execution_command_after_separate_root_authorization_only']
        assert sha(cmd[cmd.index('--input') + 1]) == cmd[cmd.index('--expected-input-sha256') + 1]
        assert not (HERE / 'runtime-unchanged-v2' / cmd[cmd.index('--run-name') + 1]).exists()
    source_paths = [
        OLD05 / 'audit_candidate05_v2.py', OLD05 / 'historical_comparison_freeze.json',
        OLD05 / 'runtime-v2/run_production_v32.py', OLD05 / 'runtime-v2/validate_binary_output.py',
        OLD05 / 'runtime-v2/output_schema_codex_compatible.json',
        OLD05 / 'runtime-v2/exposed240-candidate05-first-run/all_predictions.jsonl',
        OLD05 / 'runtime-v2/exposed240-candidate05-first-run/all_predictions.json',
        OLD06 / 'runtime-unchanged-v2/exposed240-candidate06-first-run/all_predictions.jsonl',
        OLD06 / 'runtime-unchanged-v2/exposed240-candidate06-first-run/all_predictions.json',
        OLD06 / 'candidate06_prompt_PROPOSED.txt', OLD06 / 'design_freeze.json', prior_delivery,
        OLD06 / 'exposed240_inputs_UNCHANGED.jsonl', OLD06 / 'synthetic62_inputs_UNCHANGED.jsonl',
        OLD06 / 'synthetic24_inputs_PROPOSED.jsonl', OLD06 / 'synthetic86_expected_PRIVATE_PROPOSED.json',
        OLD06 / 'independent-control-semantic-audit/independent_all86_control_semantic_review_PRIVATE.json',
        ROOT / 'outputs/coding-revision-20261008-r4/old180-IF-disagreement-independent-review/independent_IF_disagreement_review.json',
        ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py',
        ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json',
        ROOT / 'outputs/coding-revision-20261007-r3/effective_blind_inputs_v14.jsonl',
        ROOT / 'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md',
        ROOT / 'outputs/coding-revision-20261007-r3/protocol/共用操作说明-v1.4.md',
        Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')]
    source_paths.extend(Path(x['path']) for x in read(OLD05 / 'historical_comparison_freeze.json')['frozen_files'].values())
    for path in (ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate07-design').iterdir():
        if path.is_file(): source_paths.append(path)
    source_paths = sorted(set(p.resolve() for p in source_paths))
    files = [binding(path) for path in sorted(HERE.rglob('*'))
             if path.is_file() and '__pycache__' not in path.parts and path != target]
    manifest = {'status': 'FROZEN_DESIGN_ONLY_PENDING_SEPARATE_ROOT_EXECUTION_AUTHORIZATION',
        'created_at_UTC': datetime.now(timezone.utc).isoformat(), 'candidate': '07 clean separate design',
        'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'nominal_logical_requests': 15,
        'max_identical_technical_attempts': 45, 'run_sizes': [240, 62, 24, 20],
        'manual_scope': 'Complete v1.3 plus v1.4 substantive operational part, unchanged candidate06 suffix',
        'schema_validator_runner_unchanged': True, 'unique_completed_agent_message_raw_binding_gate_unchanged': True,
        'first_chronological_technically_valid_only': True, 'semantic_or_metric_retries_or_selection': False,
        'full_corpus_or_automatic_adoption': False, 'model_calls_before_freeze': 0,
        'independent_preflight': binding(preflight_path), 'independent_preflight_no_blocking_findings': True,
        'known_checks_8_errors_9_preserved_plus01955_02220_even_if_unchanged': True,
        'all_output_fields_and_issue_changes_reviewed_not_labels_alone': True,
        'reserved_context_exposure_limits_separately_recorded_original_input_not_silently_changed': True,
        'files': files, 'source_bindings': [binding(path) for path in source_paths]}
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'path': str(target), 'sha256': sha(target),
        'files': len(files), 'source_bindings': len(source_paths), 'model_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
