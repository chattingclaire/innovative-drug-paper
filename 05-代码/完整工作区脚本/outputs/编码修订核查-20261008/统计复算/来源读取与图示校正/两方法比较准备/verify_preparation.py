"""Static/synthetic checks; no actual prediction or new-run metadata reads."""
import ast
import hashlib
import json
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[2]


def main():
    script = HERE / 'compare_source_corrected.py'
    source = script.read_bytes()
    ast.parse(source)
    module = types.ModuleType('preparation_only')
    module.__file__ = str(script)
    exec(compile(source, str(script), 'exec'), module.__dict__)
    core = module.load_core()
    checks = []
    def check(name, value):
        assert value, name
        checks.append({'name': name, 'pass': True})
    def refuses(fn):
        try:
            fn()
        except (ValueError, TypeError, KeyError):
            return True
        return False
    check('syntax_import_no_main', module.HERE == HERE)
    original = W / '统计复算/测量与语义统一全量/两方法比较/compare_full_methods.py'
    original_bytes = original.read_bytes()
    check('original_kernel_lock', hashlib.sha256(original_bytes).hexdigest() == '1ede8a8ab978f65c6be56afcc267ab6073f8a0e301526bd2576c80fa968f32d9')
    old_functions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(original_bytes).body if isinstance(n, ast.FunctionDef)}
    new_functions = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse((HERE / 'comparison_core.py').read_bytes()).body if isinstance(n, ast.FunctionDef)}
    for name in ['paired_binary', 'ranking', 'compare_group']:
        check('unchanged_statistical_AST_' + name, old_functions[name] == new_functions[name])
    complete = {'status': 'complete_actual_calls_structurally_valid', 'n': 1,
                'expected_batch_count': 1, 'accepted_batch_count': 1, 'recorded_batch_count': 1,
                'selected_tool_event_count': 0, 'all_attempt_tool_event_count': 0,
                'source_unchanged_during_run': True, 'source_input_current_sha256': 'a' * 64,
                'input_sha256': 'a' * 64, 'output_sha256': 'b' * 64, 'prompt_sha256': 'c' * 64,
                'plan_sha256': 'd' * 64, 'metric_or_reference_label_based_selection': False}
    core.validate_complete_summary(complete, 1)
    check('parameterized_single_unit_metadata_accepts', True)
    check('single_unit_rejects_wrong_population', refuses(lambda: core.validate_complete_summary(complete, 4480)))
    check('partial_single_unit_metadata_refused', refuses(lambda: core.validate_complete_summary({**complete, 'status': 'partial_or_failed_preserved'}, 1)))
    core.validate_complete_summary({**complete, 'n': 4480}, 4480)
    check('parameterized_full_metadata_accepts', True)
    calls = []
    old_read_json, old_read_bound, old_read_jsonl = core.read_json, core.read_bound, core.read_jsonl
    def fake_summary(path, *args):
        calls.append(str(path))
        return {**complete, 'status': 'partial_or_failed_preserved'}
    def forbidden_read(*args, **kwargs):
        raise AssertionError('real prediction read before metadata completion gate')
    core.read_json, core.read_bound, core.read_jsonl = fake_summary, forbidden_read, forbidden_read
    try:
        args = types.SimpleNamespace(llm_run=HERE / 'synthetic_nonexistent_run', llm_summary=None, llm_output=None,
                                     expected_llm_summary_sha256=None, expected_llm_output_sha256=None)
        check('correction_completion_gate_before_predictions', refuses(lambda: core.load_complete_llm(args, {}, 1)) and len(calls) == 1)
    finally:
        core.read_json, core.read_bound, core.read_jsonl = old_read_json, old_read_bound, old_read_jsonl
    roles = ['rule_input', 'rule_output', 'llm_input', 'llm_output', 'frame', 'first_full_qa',
             'rule_execution_qa', 'rule_freeze_record', 'llm_lineage', 'visual_qa', 'source_correction_record', 'root_bundle']
    manifest = {'status': 'frozen_complete_inputs_outputs_for_comparison', 'target_n': 4481, 'executed_n': 4480,
                'manual_sha256': core.MANUAL_SHA, 'lineage_kind': module.LINEAGE_KIND,
                'source_change_ids': [module.CHANGED_ID], 'source_changes_selected_by_labels_or_metrics': False,
                'rule_execution_complete': True, 'rule_lineage_kind': module.RULE_FULL,
                'files': {r: {'path': 'synthetic', 'sha256': 'a' * 64} for r in roles},
                'correction_llm_run': {'path': 'synthetic', 'summary_sha256': 'b' * 64, 'output_sha256': 'c' * 64}}
    module.validate_manifest_contract(manifest, core)
    check('synthetic_final_manifest_contract_accepts', True)
    recovered = {**manifest, 'rule_lineage_kind': module.RULE_RECOVERED, 'rule_recovery_ids': ['synthetic-parser-1'],
                 'files': {**manifest['files'], **{r: {'path': 'synthetic', 'sha256': 'a' * 64} for r in ['rule_base_output', 'rule_base_qa', 'rule_recovery_scope', 'rule_lineage']}},
                 'rule_recovery_runs': [{r: {'path': 'synthetic', 'sha256': 'a' * 64} for r in ['input', 'output', 'execution_qa', 'runtime_freeze']}]}
    module.validate_manifest_contract(recovered, core)
    check('fixed_scope_rule_recovery_manifest_contract_accepts', True)
    check('fixed_scope_recovery_manifest_rejects_missing_runs', refuses(lambda: module.validate_manifest_contract({**recovered, 'rule_recovery_runs': []}, core)))
    for name, patch in [('unfinished', {'status': 'pending'}), ('incorrect_lineage', {'lineage_kind': 'single_run'}),
                        ('extra_source_change', {'source_change_ids': [module.CHANGED_ID, 'synthetic-extra']}),
                        ('selection_by_label', {'source_changes_selected_by_labels_or_metrics': True}),
                        ('incomplete_rule', {'rule_execution_complete': False}), ('missing_file_locks', {'files': {}})]:
        check('manifest_refuses_' + name, refuses(lambda patch=patch: module.validate_manifest_contract({**manifest, **patch}, core)))
    rows = [{'id': 'synthetic-row-' + str(i), 'text': 'source'} for i in range(4480)]
    rows[100] = {'id': module.CHANGED_ID, 'text': 'old-source'}
    def bytes_for(values):
        return ''.join(json.dumps(r) + '\n' for r in values).encode()
    old = bytes_for(rows)
    final = [dict(r) for r in rows]
    final[100]['text'] = 'new-source'
    result = module.exact_one_replacement(old, bytes_for(final), 'synthetic', core)
    check('exact4479_original_lines_preserved', result['ledger']['other_rows_byte_identical_n'] == 4479 and result['changed_position_0_based'] == 100)
    extra = [dict(r) for r in final];extra[101]['text'] = 'extra-change'
    check('second_row_change_refused', refuses(lambda: module.exact_one_replacement(old, bytes_for(extra), 'synthetic', core)))
    reordered = [dict(r) for r in final];reordered[0], reordered[1] = reordered[1], reordered[0]
    check('row_reordering_refused', refuses(lambda: module.exact_one_replacement(old, bytes_for(reordered), 'synthetic', core)))
    elsewhere = [dict(r) for r in rows];elsewhere[101]['text'] = 'wrong-change'
    check('change_to_other_id_refused', refuses(lambda: module.exact_one_replacement(old, bytes_for(elsewhere), 'synthetic', core)))
    check('no_fixed_unknown22_gate', '== 22' not in source.decode() and '== 22' not in (HERE / 'comparison_core.py').read_text())
    pairs = [{'id': str(i), 'group': 'synthetic', 'rule': dict.fromkeys(core.DIMS, r), 'llm': dict.fromkeys(core.DIMS, l)}
             for i, (r, l) in enumerate([(0, 0), (0, 0), (0, 1), (1, 0), (1, 1), (1, 1), (None, 1)])]
    binary = core.paired_binary(pairs, 'S')
    check('unknown_preserved_math_kappa_one_third', binary['paired_determined_n'] == 6 and binary['excluded_unknown_n'] == 1 and binary['kappa_exact_fraction'] == '1/3')
    # In-memory actual-lineage fixture; no policy labels or real file reads.
    scope_ids = [rows[100]['id'], rows[200]['id']]
    base_rows = [{'id': r['id'], 'record': 'synthetic-base-execution'} for r in rows]
    replacement_rows = [{'id': rid, 'record': 'synthetic-scoped-execution'} for rid in scope_ids]
    final_rows = [dict(r) for r in base_rows]
    final_rows[100], final_rows[200] = replacement_rows
    h = lambda b: hashlib.sha256(b).hexdigest()
    base_bytes, final_bytes, recovery_input, recovery_output = bytes_for(base_rows), bytes_for(final_rows), bytes_for([rows[100], rows[200]]), bytes_for(replacement_rows)
    memory = {'synthetic-base': base_bytes, 'synthetic-recovery-input': recovery_input, 'synthetic-recovery-output': recovery_output,
              '/synthetic-runtime/fixture.py': b'synthetic parser source never executed'}
    fake_input_sha = h(bytes_for(rows))
    run_refs = {name: {'path': path, 'sha256': h(memory[path])} for name, path in [('input', 'synthetic-recovery-input'), ('output', 'synthetic-recovery-output')]}
    fake_objects = {
        'rule_recovery_scope': {'scope_ids': scope_ids, 'whole_population_n': 4480, 'derived_from_source_parse_scan': True,
                                'selected_by_labels_or_metrics': False, 'frozen_before_recovery': True, 'input_sha256': fake_input_sha},
        'rule_base_qa': {'all_checks_pass': True, 'actual_execution_complete': True, 'n': 4480, 'manual_sha256': core.MANUAL_SHA,
                         'input_sha256': fake_input_sha, 'output_sha256': h(base_bytes)},
        'rule_lineage': {'lineage_kind': module.RULE_RECOVERED, 'replacement_ids': scope_ids, 'selection_by_label_or_metric': False,
                         'base_output_sha256': h(base_bytes), 'final_output_sha256': h(final_bytes), 'unchanged_other_row_n': 4478}}
    qa_obj = {'all_checks_pass': True, 'actual_execution_complete': True, 'n': 2, 'ids': scope_ids, 'manual_sha256': core.MANUAL_SHA,
              'input_sha256': h(recovery_input), 'output_sha256': h(recovery_output)}
    runtime_obj = {'manual_sha256': core.MANUAL_SHA, 'input_sha256': h(recovery_input), 'ids': scope_ids,
                   'runtime_path': '/synthetic-runtime', 'runtime_files_sha256': {'fixture.py': h(memory['/synthetic-runtime/fixture.py'])}}
    for name, path, value in [('execution_qa', 'synthetic-recovery-qa', qa_obj), ('runtime_freeze', 'synthetic-recovery-runtime', runtime_obj)]:
        memory[path] = json.dumps(value).encode();run_refs[name] = {'path': path, 'sha256': h(memory[path])}
    fixture = {'rule_lineage_kind': module.RULE_RECOVERED, 'rule_recovery_ids': scope_ids, 'rule_recovery_runs': [run_refs],
               'files': {'rule_input': {'sha256': fake_input_sha}, 'rule_base_output': {'sha256': h(base_bytes)},
                         'rule_output': {'sha256': h(final_bytes)}, 'rule_recovery_scope': {'path': 'synthetic-scope', 'sha256': 'a' * 64}}}
    def memory_read(path, bindings, expected=None):
        value = memory[str(path)]
        assert expected == h(value)
        return value
    original_reader = core.read_bound
    core.read_bound = memory_read
    try:
        ledger = module.audit_rule_scoped_recovery(fixture, rows, final_bytes, core, {}, lambda role: base_bytes, lambda role: fake_objects[role])
        check('two_id_scoped_rule_recovery_exact4478_other_bytes', ledger['outside_scope_original_row_bytes_unchanged_n'] == 4478 and ledger['fixed_scope_ids'] == scope_ids)
        extra_final = [dict(r) for r in final_rows];extra_final[0]['record'] = 'unexpected-change'
        check('scoped_rule_recovery_refuses_changed_outside_scope', refuses(lambda: module.audit_rule_scoped_recovery(fixture, rows, bytes_for(extra_final), core, {}, lambda role: base_bytes, lambda role: fake_objects[role])))
        original_scope = dict(fake_objects['rule_recovery_scope']);fake_objects['rule_recovery_scope']['selected_by_labels_or_metrics'] = True
        check('rule_recovery_scope_cannot_be_label_selected', refuses(lambda: module.audit_rule_scoped_recovery(fixture, rows, final_bytes, core, {}, lambda role: base_bytes, lambda role: fake_objects[role])))
        fake_objects['rule_recovery_scope'] = original_scope
    finally:
        core.read_bound = original_reader
    report = {'status': 'parameterized_comparison_preparation_only', 'all_preparation_checks_pass': True,
              'n_checks': len(checks), 'checks': checks, 'script_sha256': hashlib.sha256(source).hexdigest(),
              'core_sha256': module.CORE_SHA, 'actual_comparison_executed': False,
              'new_rule_or_llm_prediction_files_read': 0, 'new_correction_execution_summary_read': 0,
              'coder_or_model_invocations': 0, 'not_semantic_or_actual_execution_validation': True}
    (HERE / '准备静态核查.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'n_checks': len(checks), 'script_sha256': report['script_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
