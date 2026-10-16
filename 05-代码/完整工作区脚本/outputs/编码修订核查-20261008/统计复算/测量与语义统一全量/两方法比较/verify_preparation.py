"""Preparatory tests only: synthetic metadata/math, never actual predictions."""
import ast
import hashlib
import json
import math
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / 'compare_full_methods.py'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    code = SCRIPT.read_bytes()
    ast.parse(code, filename=str(SCRIPT))
    module = types.ModuleType('comparison_preparation_only')
    module.__file__ = str(SCRIPT)
    exec(compile(code, str(SCRIPT), 'exec'), module.__dict__)
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append({'name': name, 'pass': True})

    check('syntax_and_import_without_main', module.HERE == HERE)
    check('all_declared_locks_are_full_sha256', all(module.is_sha256(x) for x in list(module.SOURCE_LOCKS.values()) + list(module.FROZEN_LOCKS.values())))
    sources = {}
    prep = module.W / 'LLM编码/测量与语义统一'
    names = {'frozen_prompt.txt': '编码提示.txt', 'frozen_schema.json': 'output_schema_codex_compatible.json',
             'frozen_validator.py': 'validate_binary_output.py', 'frozen_runner.py': 'run_coding.py'}
    for frozen, name in names.items():
        path = prep / name
        data = path.read_bytes()
        sources[str(path)] = {'sha256': sha(data), 'bytes': len(data)}
        check('fixed_preparation_lock_' + frozen, sha(data) == module.FROZEN_LOCKS[frozen])
    for key in ['manual', 'rule_summary_helper']:
        path = module.DEFAULT_PATHS[key]
        data = path.read_bytes()
        sources[str(path)] = {'sha256': sha(data), 'bytes': len(data)}
        check('source_lock_' + key, sha(data) == module.SOURCE_LOCKS[key])
    helper = types.ModuleType('preparation_math_helper')
    helper.__file__ = str(module.DEFAULT_PATHS['rule_summary_helper'])
    exec(compile(module.DEFAULT_PATHS['rule_summary_helper'].read_bytes(), helper.__file__, 'exec'), helper.__dict__)

    complete = {'status': 'complete_actual_calls_structurally_valid', 'n': 4480,
                'expected_batch_count': 180, 'accepted_batch_count': 180, 'recorded_batch_count': 180,
                'selected_tool_event_count': 0, 'all_attempt_tool_event_count': 0,
                'source_unchanged_during_run': True, 'source_input_current_sha256': 'a' * 64,
                'input_sha256': 'a' * 64, 'output_sha256': 'b' * 64,
                'prompt_sha256': 'c' * 64, 'plan_sha256': 'd' * 64,
                'metric_or_reference_label_based_selection': False}
    module.validate_complete_summary(complete)
    check('synthetic_complete_metadata_gate_accepts', True)
    mutations = [('partial_status', {'status': 'partial_or_failed_preserved'}),
                 ('wrong_population', {'n': 4479}), ('incomplete_batches', {'accepted_batch_count': 179}),
                 ('missing_output_sha', {'output_sha256': None}), ('tool_event', {'all_attempt_tool_event_count': 1}),
                 ('source_changed', {'source_unchanged_during_run': False}),
                 ('source_hash_changed', {'source_input_current_sha256': 'e' * 64}),
                 ('selection_by_labels', {'metric_or_reference_label_based_selection': True})]
    for name, patch in mutations:
        refused = False
        try:
            module.validate_complete_summary({**complete, **patch})
        except module.BindingError:
            refused = True
        check('synthetic_gate_refuses_' + name, refused)

    # Replace all data-reader functions: this test cannot open a real run file.
    original = {name: getattr(module, name) for name in ['read_json', 'read_jsonl', 'read_bound']}
    reads = []
    def partial_summary(path, bindings, expected=None):
        reads.append(str(path))
        return {**complete, 'status': 'partial_or_failed_preserved'}
    def forbidden_prediction_read(*args, **kwargs):
        raise AssertionError('prediction or later frozen file opened before completion gate')
    module.read_json = partial_summary
    module.read_jsonl = forbidden_prediction_read
    module.read_bound = forbidden_prediction_read
    args = types.SimpleNamespace(llm_run=HERE / '_synthetic_nonexistent_run', llm_summary=None,
                                 llm_output=None, expected_llm_summary_sha256=None,
                                 expected_llm_output_sha256=None)
    try:
        refused = False
        try:
            module.load_complete_llm(args, {})
        except module.BindingError:
            refused = True
        check('partial_gate_precedes_any_prediction_read', refused and len(reads) == 1 and reads[0].endswith('/execution_summary.json'))
    finally:
        for name, fn in original.items():
            setattr(module, name, fn)

    def record(number, rv, lv):
        return {'id': 'synthetic-math-' + str(number), 'group': 'synthetic',
                'rule': {d: (rv if d == 'S' else 0) for d in module.DIMS},
                'llm': {d: (lv if d == 'S' else 0) for d in module.DIMS}}
    records = [record(i, r, l) for i, (r, l) in enumerate([(0, 0), (0, 0), (0, 1), (1, 0), (1, 1), (1, 1)])]
    result = module.paired_binary(records, 'S')
    check('four_cells_2_1_1_2', list(result['cells'].values()) == [2, 1, 1, 2])
    check('agreement_two_thirds_kappa_one_third', math.isclose(result['agreement'], 2 / 3) and result['kappa_exact_fraction'] == '1/3')
    swapped = [{**r, 'rule': r['llm'], 'llm': r['rule']} for r in records]
    check('kappa_symmetric_no_gold_rater', module.paired_binary(swapped, 'S')['cohen_kappa'] == result['cohen_kappa'])
    constant = module.paired_binary([record(1, 0, 0), record(2, 0, 0)], 'S')
    check('constant_marginals_kappa_undefined', constant['cohen_kappa'] is None and constant['kappa_undefined_reason'] == 'expected_agreement_is_one')
    missing = module.paired_binary([record(1, 1, 1), record(2, None, 1)], 'S')
    check('unknown_excluded_not_zero', missing['paired_determined_n'] == 1 and missing['excluded_unknown_n'] == 1 and missing['cells']['rule0_llm1'] == 0)
    empty = module.paired_binary([record(1, None, 1)], 'S')
    check('no_pairs_kappa_undefined', empty['cohen_kappa'] is None and empty['agreement'] is None and empty['kappa_undefined_reason'] == 'no_paired_units')

    def vector_record(number, r, l):
        return {'id': 'synthetic-q-' + str(number), 'group': 'synthetic',
                'rule': dict(zip(module.DIMS, r)), 'llm': dict(zip(module.DIMS, l))}
    qs = [vector_record(1, [1, 0, 0, 0, 0], [0, 0, 0, 1, 0]),
          vector_record(2, [0, 1, 0, 0, 0], [0, 1, 0, 0, 0]),
          vector_record(3, [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]),
          vector_record(4, [1, 0, 0, None, 0], [1, 0, 0, 0, 0])]
    comparison = module.compare_group(qs, helper)
    check('common_all_five_cohort_is_same_three_units', comparison['common_all_five_determined_comparison']['unit_n'] == 3 and comparison['common_all_five_determined_comparison']['excluded_unknown_ids'] == ['synthetic-q-4'])
    check('dimensionwise_cohort_retains_partial_known_cells', comparison['binary_agreement_on_dimensionwise_common_determined']['S']['paired_determined_n'] == 4 and comparison['binary_agreement_on_dimensionwise_common_determined']['I']['paired_determined_n'] == 3)
    check('same_cohort_q_difference_is_percentage_points', comparison['q_differences']['S']['common_all_five_determined_population_q_llm_minus_rule_percentage_points'] == -50 and comparison['q_differences']['I']['common_all_five_determined_population_q_llm_minus_rule_percentage_points'] == 50)
    desc = comparison['method_descriptive']['rule']
    check('partial_known_positive_retained_for_bounds', desc['dimensions']['S']['available_cell_positive_n'] == 2 and desc['dimensions']['I']['dimension_unknown_unit_n'] == 1)
    check('dense_ranking_ties', comparison['common_all_five_determined_comparison']['ranking_tie_groups']['rule'] == [['S', 'E'], ['Ec', 'I', 'F']])
    all_zero = helper.summarize([{'id': 'synthetic-zero', 'group': 'synthetic', 'labels': dict.fromkeys(module.DIMS, 0)}])
    check('zero_attention_denominator_has_no_ranking', module.ranking(all_zero) is None)

    report = {'status': 'preparation_static_and_synthetic_checks_only', 'all_preparation_checks_pass': True,
              'checks': checks, 'n_checks': len(checks), 'script_sha256': sha(code),
              'python_executable': sys.executable, 'bound_preparation_sources': sources,
              'real_llm_prediction_files_read': 0, 'real_llm_execution_summary_files_read': 0,
              'real_full_comparison_executed': False, 'coder_or_model_invocations': 0,
              'semantic_validity_or_completeness_of_real_run_not_verified': True,
              'synthetic_cases_are_arithmetic_and_metadata_tests_not_policy_expected_labels': True}
    (HERE / '脚本准备核查.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'n_checks': len(checks), 'script_sha256': report['script_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
