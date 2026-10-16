"""Post-execution audit only: no model calls, label edits, score selection or A/B reads.

Raw execution files remain intact. All new human-review projections are redacted
before being saved; protected originals are used only inside the mechanical redactor.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD05 = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate05-preparation'
OLD06 = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate06-design/revision-v2'
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


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    freeze = read(HERE / 'design_freeze.json')
    for binding in freeze['files'] + freeze['source_bindings']:
        assert sha(binding['path']) == binding['sha256'], binding['path']
    helper = module('frozen05_v2_technical_audit', OLD05 / 'audit_candidate05_v2.py')
    redactor_module = module('frozen_reserved_redactor', ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py')
    redactor = redactor_module.ReservedContextRedactor()
    runtime = HERE / 'runtime-unchanged-v2'
    adapter = {'candidate05_prompt': {'sha256': sha(HERE / 'candidate07_prompt_PROPOSED.txt')},
               'runtime': {name: {'sha256': sha(runtime / name)} for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']}}
    outputs, technical = {}, []
    for declared in read(HERE / 'candidate07_execution_plan_PROPOSED.json')['runs']:
        command = declared['future_execution_command_after_separate_root_authorization_only']
        name = command[command.index('--run-name') + 1]
        source = command[command.index('--input') + 1]
        actual, audit = helper.audit_run(runtime / name, {'n': declared['n'], 'batch_size': 25,
            'logical_batches': declared['logical_requests'], 'input': source}, adapter)
        outputs[declared['n']] = {row['id']: row for row in actual}
        technical.append(audit)
    assert sum(run['logical_batches'] for run in technical) == 15
    assert sum(run['actual_attempts'] for run in technical) <= 45
    source240 = {row['id']: row for row in lines(HERE / 'exposed240_inputs_UNCHANGED.jsonl')}
    assert not any(redactor.is_reserved(ident) for ident in source240)
    histories = {}
    for name, binding in read(OLD05 / 'historical_comparison_freeze.json')['frozen_files'].items():
        assert sha(binding['path']) == binding['sha256']
        if name.endswith('_rows'):
            histories[name] = {row['id']: row for row in lines(binding['path'])}
    histories['candidate05_intact_actual_rows'] = {row['id']: row for row in lines(OLD05 / 'runtime-v2/exposed240-candidate05-first-run/all_predictions.jsonl')}
    histories['candidate06_intact_actual_rows'] = {row['id']: row for row in lines(OLD06 / 'runtime-unchanged-v2/exposed240-candidate06-first-run/all_predictions.jsonl')}
    assert all(set(rows) == set(source240) for rows in histories.values())
    all240, changes = [], []
    for ident, source in source240.items():
        new = outputs[240][ident]
        prior = {name: rows[ident] for name, rows in histories.items()}
        changed = {name: [d for d in DIMS if old['labels'][d] != new['labels'][d]] for name, old in prior.items()}
        entry = {'id': ident, 'input': source, 'candidate07_intact_actual_row': new,
                 'historical_intact_rows': prior, 'changed_dimensions_vs_each_history': changed,
                 'semantic_truth_not_inferred_from_agreement': True}
        all240.append(entry)
        if any(changed.values()):
            changes.append(entry)
    expectations = read(HERE / 'synthetic106_expected_PRIVATE_PROPOSED.json')['tests']
    actual_controls = {**outputs[62], **outputs[24], **outputs[20]}
    assert len(actual_controls) == len(expectations) == 106
    controls = [{**test, 'candidate07_intact_actual_row': actual_controls[test['input']['id']],
                 'mechanical_different_dimensions': [d for d in DIMS if actual_controls[test['input']['id']]['labels'][d] != test['labels'][d]],
                 'semantic_review_required_even_if_mechanically_matching': True} for test in expectations]
    out = HERE / 'execution-audit'
    out.mkdir(exist_ok=True)
    dump_new(out / 'candidate07_technical_QA.json', {'status': 'PASS_TECHNICAL_ONLY_SEMANTIC_REVIEW_PENDING',
        'model_requested': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'actual_logical_requests': 15,
        'actual_attempts': sum(run['actual_attempts'] for run in technical), 'runs': technical,
        'all_selected_raw_bound_to_unique_completed_agent_message': True,
        'first_technically_valid_selection_verified': True, 'semantic_or_metric_selection': False,
        'independent_validation': False, 'labels_or_manuscript_modified': False})
    redaction_records = []
    for name, obj in [('candidate07_all240_comparison_REDACTED_PRIVATE.json', {'rows': all240}),
                      ('candidate07_all_changes_REDACTED_PRIVATE.json', {'rows': changes}),
                      ('candidate07_all106_controls_PRIVATE.json', {'tests': controls})]:
        clean, hits = redactor.redact_object(obj)
        assert redactor.audit_object_no_full_match(clean)['no_remaining_full_normalized_reserved_unit_match']
        dump_new(out / name, clean)
        redaction_records.append({'projection': str(out / name), 'sha256': sha(out / name),
            'hits_ID_and_field_path_only': [{'reserved_unit_id': h['reserved_unit_id'], 'field_path': h['locator']} for h in hits],
            'post_projection_no_full_normalized_match': True})
    dump_new(out / 'candidate07_human_review_redaction_metadata.json', {'original_model_inputs_and_outputs_unmodified': True,
        'records': redaction_records, 'limitation': 'Full normalized reserved originals only; partial quotes/paraphrases may escape detection. Protected index not serialized.'})
    print(json.dumps({'status': 'PASS_TECHNICAL_ONLY_SEMANTIC_REVIEW_PENDING', 'actual_attempts': sum(run['actual_attempts'] for run in technical),
        'original_rows': len(all240), 'changed_rows_against_any_intact_history': len(changes), 'controls': len(controls)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
