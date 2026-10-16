"""Audit completed requests and prepare complete semantic review, never edit labels.

Reuses the already reviewed candidate05-v2 technical audit function against
candidate06's own frozen run snapshots. No model/CLI invocation or A/C label read.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate05-preparation'
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
        assert path.read_text() == content, f'Existing audit differs: {path}'
    else:
        path.write_text(content)


def main():
    frozen = read(HERE / 'design_freeze.json')
    for binding in frozen['files'] + frozen['source_bindings']:
        assert sha(binding['path']) == binding['sha256'], binding['path']
    spec = importlib.util.spec_from_file_location('original05_v2_technical_audit', OLD / 'audit_candidate05_v2.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    plan = read(HERE / 'candidate06_execution_plan_PROPOSED.json')
    runtime = HERE / 'runtime-unchanged-v2'
    # The helper's old key name is an adapter only; it receives the06 prompt SHA.
    adapter = {'candidate05_prompt': {'sha256': sha(HERE / 'candidate06_prompt_PROPOSED.txt')},
               'runtime': {name: {'sha256': sha(runtime / name)} for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']}}
    outputs, technical = {}, []
    for declared in plan['runs']:
        command = declared['future_execution_command_after_separate_root_authorization_only']
        name = command[command.index('--run-name') + 1]
        source = command[command.index('--input') + 1]
        actual, audit = helper.audit_run(runtime / name, {'n': declared['n'], 'batch_size': 25, 'logical_batches': declared['logical_requests'], 'input': source}, adapter)
        outputs[declared['n']] = {row['id']: row for row in actual}
        technical.append(audit)
    assert sum(run['logical_batches'] for run in technical) == 14
    assert sum(run['actual_attempts'] for run in technical) <= 42
    source240 = {row['id']: row for row in lines(HERE / 'exposed240_inputs_UNCHANGED.jsonl')}
    exclusion = read(ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json')
    assert not set(source240) & set(exclusion['all_registered_members_of_reserved_families_unit_ids'])
    history_freeze = read(OLD / 'historical_comparison_freeze.json')
    histories = {}
    for name, binding in history_freeze['frozen_files'].items():
        assert sha(binding['path']) == binding['sha256']
        if name.endswith('_rows'):
            histories[name] = {row['id']: row for row in lines(binding['path'])}
    histories['candidate05_intact_actual_rows'] = {row['id']: row for row in lines(OLD / 'runtime-v2/exposed240-candidate05-first-run/all_predictions.jsonl')}
    assert all(set(rows) == set(source240) for rows in histories.values())
    changes, all240 = [], []
    for ident, source in source240.items():
        new = outputs[240][ident]
        prior = {name: rows[ident] for name, rows in histories.items()}
        changed = {name: [d for d in DIMS if old['labels'][d] != new['labels'][d]] for name, old in prior.items()}
        entry = {'id': ident, 'input': source, 'candidate06_intact_actual_row': new,
                 'historical_intact_rows': prior, 'changed_dimensions_vs_each_history': changed,
                 'semantic_truth_not_inferred_from_agreement': True}
        all240.append(entry)
        if any(changed.values()):
            changes.append(entry)
    expectations = read(HERE / 'synthetic86_expected_PRIVATE_PROPOSED.json')['tests']
    actual_controls = {**outputs[62], **outputs[24]}
    assert len(actual_controls) == len(expectations) == 86
    controls = [{**test, 'candidate06_intact_actual_row': actual_controls[test['input']['id']],
                 'mechanical_different_dimensions': [d for d in DIMS if actual_controls[test['input']['id']]['labels'][d] != test['labels'][d]],
                 'semantic_review_required_even_if_mechanically_matching': True}
                for test in expectations]
    out = HERE / 'execution-audit'
    out.mkdir(exist_ok=True)
    dump_new(out / 'candidate06_technical_QA.json', {'status': 'PASS_TECHNICAL_ONLY_SEMANTIC_REVIEW_PENDING',
             'model_requested': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'actual_logical_requests': 14,
             'actual_attempts': sum(run['actual_attempts'] for run in technical), 'runs': technical,
             'all_selected_raw_bound_to_unique_completed_agent_message': True,
             'first_technically_valid_selection_verified': True, 'semantic_or_metric_selection': False,
             'independent_validation': False, 'labels_or_manuscript_modified': False})
    dump_new(out / 'candidate06_all240_comparison_PRIVATE.json', {'status': 'COMPLETE_DEVELOPMENT_REVIEW_NOT_GOLD_EVALUATION', 'rows': all240})
    dump_new(out / 'candidate06_all_changes_PRIVATE.json', {'status': 'ALL_FIVE_DIMENSION_CHANGE_REVIEW_REQUIRED', 'rows': changes})
    dump_new(out / 'candidate06_all86_controls_PRIVATE.json', {'status': 'ALL_CONTROL_SEMANTICS_REVIEW_REQUIRED', 'tests': controls})
    print(json.dumps({'status': 'PASS_TECHNICAL_ONLY_SEMANTIC_REVIEW_PENDING', 'actual_attempts': sum(run['actual_attempts'] for run in technical),
                      'original_rows': len(all240), 'changed_rows_against_any_intact_history': len(changes), 'controls': len(controls)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
