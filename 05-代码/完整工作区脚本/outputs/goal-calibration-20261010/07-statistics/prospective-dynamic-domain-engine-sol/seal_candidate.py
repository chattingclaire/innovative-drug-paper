"""Seal current development artifacts without executing statistical code."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def binding(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    with (HERE / name).open('x') as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write('\n')


def main():
    final = json.loads((HERE / 'control-results-final.json').read_text())
    stage = json.loads((HERE / 'stage-helper-control-results.json').read_text())
    wrapper = json.loads((HERE / 'wrapper-control-result.json').read_text())
    inputs = json.loads((HERE / 'input-bindings.json').read_text())
    preservation = json.loads((HERE / 'structural-preservation-and-input-readback.json').read_text())
    assert final['passed_N'] == 29 and final['failed_N'] == 0
    assert stage['passed_N'] == 2 and stage['failed_N'] == 0 and wrapper['passed'] is True
    for report, key in ((final, 'admission_binding'), (stage, 'admission_code_binding'), (wrapper, 'candidate_admission_binding')):
        assert report[key] == binding(HERE / 'scope_admission.py')
    assert final['engine_binding'] == binding(HERE / 'metrics_engine.py')
    assert all(binding(x['path']) == x for x in inputs['frozen_inputs'].values())
    summary = {
        'status': 'sealed_unadopted_dynamic_domain_candidate', 'actor': 'nonhuman_AI_preparation',
        'candidate_files': {name: binding(HERE / name) for name in (
            'metrics_engine.py', 'scope_admission.py', 'frozen_year_core.py',
            'ROOT-scope-registry.UNADOPTED.json', 'input-contract.json', 'future-freeze-dependencies.json')},
        'original_range_controls_N': 30, 'original_range_controls_passed_N': 30,
        'ROOT_added_pure_stage_helper_controls_N': 2, 'ROOT_added_helper_passed_N': 2,
        'fixed_original29_execution_rounds_N': 4,
        'first_original29_passed_N': 28, 'first_original29_failed_N': 1,
        'first_failure': 'Preserved test reader KeyError: A_vs_B has no classification Precision output',
        'all_original_case_expectations_unchanged': True,
        'CLI_repeat_of_two_fixed_refusal_cases_N': 2, 'CLI_metric_output_files_created_N': 0,
        'pure_helper_acceptance_is_not_ROOT_scope_human_or_statistics_admission': True,
        'unchanged_original_math_year_functions_N': len(preservation['unchanged_original_functions']),
        'unchanged_statistical_constants_AST': True, 'unchanged_legacy1444_3037_guards': True,
        'preserved_old200_sealed_members_N': preservation['sealed_old200_member_N'],
        'frozen_upstream_input_files_N': len(inputs['frozen_inputs']),
        'synthetic_max_answer_rows_per_analysis': 8, 'complete4481_TOY_metadata_is_not_label_simulation': True,
        'actual_ROOT_adopted_scope_N': 0, 'actual_new_draw_N': 0, 'actual_human_first_N': 0,
        'actual_human_reference_N': 0, 'main_LLM_partial_labels_read_N': 0,
        'actual_machine_labels_read_N': 0, 'actual_statistics_or_annual_findings_N': 0,
        'formal_acceptance_claimed': False,
        'actual_registered_scope_positive_path_executed': False,
        'current1261_3220_intermediate_snapshot_adopted': False,
        'legacy200_formal_validation_of_updated_rule_permitted': False,
        'remaining_dependencies': 'future-freeze-dependencies.json; no new ROOT-approved scope/design/draw or actual human/reference/full-machine receipts yet',
    }
    write('delivery-summary.json', summary)
    members = [binding(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name not in ('output-seal.json', 'seal-readback.json')]
    seal = {'status': summary['status'], 'actor': summary['actor'],
            'code_binding': binding(__file__), 'candidate_files': summary['candidate_files'],
            'summary_binding': binding(HERE / 'delivery-summary.json'),
            'input_bindings_binding': binding(HERE / 'input-bindings.json'),
            'original_range_final_execution_binding': binding(HERE / 'control-results-final.json'),
            'wrapper_control_execution_binding': binding(HERE / 'wrapper-control-result.json'),
            'ROOT_additional_stage_helper_execution_binding': binding(HERE / 'stage-helper-control-results.json'),
            'all_failures_preserved': True, 'actual_ROOT_scope_draw_human_reference_or_statistics_N': 0,
            'main_LLM_partial_labels_read_N': 0, 'formal_acceptance_claimed': False,
            'self_and_readback_report_excluded_to_avoid_self_reference': True, 'output_members': members}
    write('output-seal.json', seal)
    readback = [{'path': m['path'], 'equal': binding(m['path']) == m} for m in members]
    assert all(x['equal'] for x in readback)
    write('seal-readback.json', {'delivery_seal_binding': binding(HERE / 'output-seal.json'),
                               'member_N': len(readback), 'all_members_bytes_equal': True,
                               'members': readback, 'self_excluded': True,
                               'actual_statistics_executed_N': 0, 'main_LLM_label_files_accessed_N': 0})
    print(json.dumps({'seal': binding(HERE / 'output-seal.json'), 'members_readback': len(readback),
                      'all_equal': True, 'candidate_engine': binding(HERE / 'metrics_engine.py'),
                      'candidate_admission': binding(HERE / 'scope_admission.py'), 'actual_statistics': 0}))


if __name__ == '__main__':
    main()
