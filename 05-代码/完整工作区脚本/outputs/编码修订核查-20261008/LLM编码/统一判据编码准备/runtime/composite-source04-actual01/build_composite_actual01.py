"""Assemble actual fixed-protocol outputs with explicit batch recovery lineage.

No model calls, score-based selection, quote changes or replacement of raw labels.
The original run stays partial; this is an explicitly composite execution product.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
from collections import Counter

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent
BASE = RUNTIME.parent
MANUAL = BASE.parent.parent / '定义溯源核查/共同判据定稿/共用编码手册.md'
INPUT = BASE / '共用纯来源材料04/source_only_with_scope04.jsonl'
PROMPT = BASE / '统一判据编码提示-执行留痕明确.txt'
ORIGINAL = RUNTIME / 'full-common-source02'
TECHNICAL = RUNTIME / 'recovered-original-batch155-technical01'
SOURCE03 = RUNTIME / 'source-recovery03-batches38-79-92'
NETWORK = RUNTIME / 'network-recovery03-batches174-194'
SOURCE04 = RUNTIME / 'source-recovery04-original-batch156'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def bind(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def jsonl(path, values):
    with Path(path).open('x') as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')


def chosen_batch(run, batch):
    directory = run / 'batches' / f'batch-{batch:04d}'
    selection_path = directory / 'selection.json'
    selection = read(selection_path)
    assert selection['status'] == 'accepted_first_valid_actual_attempt'
    assert selection['selection_uses_metric_or_label_values'] is False
    chosen = run / selection['selected_relative_path']
    assert sha(chosen / 'raw_output.json') == selection['selected_output_sha256']
    metadata = read(chosen / 'run_metadata.json')
    assert metadata['status'] == 'accepted_structural_literal_zero_tools'
    assert metadata['requested_model'] == 'gpt-5.6-sol'
    assert metadata['reasoning_effort'] == 'medium'
    assert metadata['tool_event_count'] == 0 and metadata['label_or_metric_selection'] is False
    assert metadata['prompt_sha256'] == sha(PROMPT)
    assert read(chosen / 'validation.json')['valid'] is True
    return chosen / 'input.json', chosen / 'raw_output.json', selection_path, None


def main():
    assert sha(MANUAL) == '5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c'
    assert sha(INPUT) == 'f4da9adad83e91ba8f46ab79086af8d51404122c9a27055d0fa54a69909437f3'
    assert sha(PROMPT) == '278576419a48c76ea204aeac58398ec31ba456048678c3e3e4b32b81d44953b9'
    inputs = [json.loads(line) for line in INPUT.read_text().splitlines()]
    assert len(inputs) == 4924 and len({r['id'] for r in inputs}) == 4924
    original_summary = read(ORIGINAL / 'execution_summary.json')
    assert original_summary['status'] == 'partial_or_failed_preserved'
    assert original_summary['accepted_batch_count'] == 173
    component_runs = {'base': ORIGINAL, 'source03': SOURCE03, 'network': NETWORK,
                      'source04': SOURCE04, 'technical155': ORIGINAL}
    components = []
    for component, run in component_runs.items():
        plan = read(run / 'run_plan.json')
        assert plan['model'] == 'gpt-5.6-sol' and plan['reasoning_effort'] == 'medium'
        assert plan['prompt_sha256'] == sha(PROMPT)
        if component in ('source03', 'network', 'source04'):
            summary = read(run / 'execution_summary.json')
            assert summary['status'] == 'complete_actual_calls_structurally_valid'
            assert summary['selected_tool_event_count'] == 0
        components.append({'component_id': component, 'run_plan': bind(run / 'run_plan.json'),
                           'summary': bind(run / 'execution_summary.json'),
                           'selection_basis': 'actual technical/source recovery, never label or metric values'})
    recovery = read(TECHNICAL / 'recovery_manifest.json')
    assert recovery['status'] == 'corrected_technical_event_binding'
    assert recovery['output_n'] == 25 and recovery['all_fields_unchanged'] is True
    assert recovery['original_raw_output_sha256'] == recovery['recovered_raw_output_sha256']
    assert recovery['schema_and_literal_checks_pass'] is True
    events = read(TECHNICAL / 'corrected_event_binding.json')
    assert events['actual_tool_event_n'] == 0 and events['unknown_event_n'] == 0
    assert events['unique_different_completed_output_n'] == 1 and events['turn_completed_n'] == 1
    aggregate, lineage, issues = [], [], []
    batch_components = []
    for original_batch in range(1, 198):
        component, run, batch = 'base', ORIGINAL, original_batch
        if original_batch in (38, 79, 92):
            component, run, batch = 'source03', SOURCE03, (38, 79, 92).index(original_batch) + 1
        elif 174 <= original_batch <= 194:
            component, run, batch = 'network', NETWORK, original_batch - 173
        elif original_batch == 156:
            component, run, batch = 'source04', SOURCE04, 1
        if original_batch == 155:
            component = 'technical155'
            input_path, output_path = TECHNICAL / 'same_batch_input.json', TECHNICAL / 'original_raw_output.json'
            selection_path, event_path = TECHNICAL / 'recovery_manifest.json', TECHNICAL / 'corrected_event_binding.json'
        else:
            input_path, output_path, selection_path, event_path = chosen_batch(run, batch)
        packet, output = read(input_path), read(output_path)
        current_batch = inputs[(original_batch - 1) * 25: original_batch * 25]
        assert packet['rows'] == current_batch, ('current material differs', original_batch)
        assert [r['id'] for r in output['rows']] == [r['id'] for r in current_batch]
        spec = importlib.util.spec_from_file_location('validator', RUNTIME / 'validate_binary_output.py')
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        assert validator.validate(packet, output) == [], original_batch
        for index, prediction in enumerate(output['rows']):
            row = {'id': prediction['id'], 'original_batch': original_batch, 'component_id': component,
                   'input_packet': bind(input_path), 'input_row_index0': index,
                   'raw_output': bind(output_path), 'output_row_index0': index,
                   'source_input_row_sha256': canonical(current_batch[index]),
                   'prediction_row_sha256': canonical(prediction), 'selection_record': bind(selection_path),
                   'technical_recovery': component == 'technical155',
                   'prompt_sha256': sha(PROMPT), 'manual_sha256': sha(MANUAL)}
            if event_path:
                row['technical_event_record'] = bind(event_path)
            aggregate.append(prediction)
            lineage.append(row)
        issues.extend(output['issue_records'])
        batch_components.append({'original_batch': original_batch, 'component_id': component,
                                 'component_batch': None if component == 'technical155' else batch,
                                 'ids': [r['id'] for r in current_batch], 'selection_record': bind(selection_path)})
    assert len(aggregate) == 4924 and [r['id'] for r in aggregate] == [r['id'] for r in inputs]
    output_path, lineage_path = HERE / 'all_predictions.jsonl', HERE / 'prediction_lineage.jsonl'
    jsonl(output_path, aggregate)
    jsonl(lineage_path, lineage)
    write(HERE / 'all_predictions.json', {'protocol_version': 'COMMON-5D-20261009',
          'execution_version': 'actual_composite_source04', 'release_stage': 'development_labels',
          'rows': aggregate, 'issue_records': issues})
    plan_path = HERE / 'composite_plan.json'
    write(plan_path, {'status': 'actual_composite_plan_not_single_call', 'n': 4924,
          'original_batch_count': 197, 'components': components, 'batches': batch_components,
          'material_input': bind(INPUT), 'manual': bind(MANUAL), 'prompt': bind(PROMPT),
          'original_partial_run_unchanged': True, 'builder': bind(Path(__file__)),
          'metric_or_reference_label_based_selection': False})
    write(HERE / 'analysis_source_missing_policy.json', {'scope': 'analysis derivative only; raw labels stay intact',
          'rows': [{'id': 'RECODE25-00064', 'dimensions': ['S', 'E', 'Ec', 'I', 'F'],
                    'reason': '历史外部引用指南适用版本未核实', 'no_implicit_zero': True}],
          'manual_changed': False, 'unknown_does_not_mean_all_zero': True})
    summary = {'status': 'complete_actual_composite_lineage', 'n': 4924, 'original_batch_count': 197,
               'component_batch_counts': dict(Counter(r['component_id'] for r in batch_components)),
               'prompt_sha256': sha(PROMPT), 'manual_sha256': sha(MANUAL),
               'input_sha256': sha(INPUT), 'output_sha256': sha(output_path),
               'lineage_sha256': sha(lineage_path), 'plan_sha256': sha(plan_path),
               'selected_tool_event_count': 0, 'metric_or_reference_label_based_selection': False,
               'source_unchanged_during_assembly': True,
               'every_row_full_input_and_raw_prediction_equal': True,
               'semantic_validity_not_proven_by_structure': True,
               'human_validation': False, 'original_partial_status_preserved': True}
    write(HERE / 'execution_summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
