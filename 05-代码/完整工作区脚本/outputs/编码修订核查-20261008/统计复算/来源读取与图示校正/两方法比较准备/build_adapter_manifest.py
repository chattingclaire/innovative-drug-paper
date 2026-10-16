"""Build an explicitly derived compatibility manifest from actual frozen records.

Never executes a coder/model; no label or score is used to choose a row.
"""
import hashlib
import json
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[2]
ROOT_SHA = 'b001d8df5a304604f0ebe33865369768c7ed92dd1ba576378816810ca20bb9f7'
MANUAL = '24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def main():
    destination = HERE / 'adapter_actual01'
    assert not destination.exists(), 'derived adapter records must be new'
    bindings = {}
    def read(ref):
        p = Path(ref['path']);b = p.read_bytes();assert sha(b) == ref['sha256'], str(p)
        bindings[str(p)] = {'sha256': sha(b), 'bytes': len(b)}
        return b
    def read_json(ref):
        return json.loads(read(ref))
    def reference(p):
        p = Path(p);return {'path': str(p.resolve()), 'sha256': sha(p.read_bytes())}
    root_ref = {'path': str(W / '统计复算/来源读取与图示校正/当前同材料结果/同材料结果绑定.json'), 'sha256': ROOT_SHA}
    root = read_json(root_ref)
    assert root['status'] == 'complete_same_material_current_methods_bound_not_human_validated'
    assert root['target_n'] == 4481 and root['executed_n'] == 4480 and root['manual_sha256'] == MANUAL
    assert root['label_or_metric_based_selection'] is False
    for ref in root['source_bindings'].values():
        read(ref)
    source = read(root['rule_input'])
    full_inputs = [json.loads(x) for x in source.splitlines()]
    full_ids = [r['id'] for r in full_inputs]
    assert len(full_ids) == len(set(full_ids)) == 4480
    base_bytes = read(root['rule_base_output']);base_rows = [json.loads(x) for x in base_bytes.splitlines()]
    final_bytes = read(root['rule_output']);final_rows = [json.loads(x) for x in final_bytes.splitlines()]
    assert [r['id'] for r in base_rows] == [r['id'] for r in final_rows] == full_ids
    assert all(r['status'] == 'completed' and r['result']['current_manual_sha256'] == MANUAL for r in base_rows + final_rows)
    raw_base = read_json(root['rule_base_execution'])
    freeze_ref = reference(W / '统计复算/来源读取与图示校正/执行冻结记录.json')
    raw_freeze = read_json(freeze_ref)
    assert raw_base['n'] == raw_base['completed'] == 4480 and raw_base['failed'] == 0
    assert raw_base['input_sha256'] == root['rule_input']['sha256']
    assert raw_base['output_sha256'] == root['rule_base_output']['sha256']
    assert raw_base['runtime_unchanged_during_execution'] and raw_base['reference_labels_used'] is False
    assert raw_freeze['same_manual_sha256'] == MANUAL
    assert all(h == raw_freeze['runtime_files_sha256'].get(name) for name, h in raw_base['runtime_before_sha256'].items())
    assert set(raw_freeze['runtime_files_sha256']) - set(raw_base['runtime_before_sha256']) == {'cross_carrier_certificates.json','visual_transcriptions.json'}
    for name, h in raw_freeze['runtime_files_sha256'].items():
        read({'path': str(Path(raw_base['runtime']) / name), 'sha256': h})
    scope = read_json(root['rule_patch_scope'])
    raw_patch = read_json(root['rule_patch_report'])
    patch_freeze = read_json(root['rule_patch_freeze'])
    delivery = read_json(root['rule_patch_delivery'])
    ids = scope['conservative_current_paragraph_ids']
    assert ids == root['rule_patch_ids'] == patch_freeze['ids'] == delivery['scope_ids']
    assert scope['scope_type'] == 'static syntax-difference census, no encoder invoked and no label expectation'
    assert scope['input_rows'] == 4480 and scope['input_sha256'] == root['rule_input']['sha256']
    assert len(ids) == len(set(ids)) == raw_patch['n'] == patch_freeze['subset_n'] == 34
    assert [r['id'] for r in scope['current_rows_in_changed_paragraphs']] == ids
    assert patch_freeze['scope_sha256'] == root['rule_patch_scope']['sha256']
    pin_bytes, pout_bytes = read(root['rule_patch_input']), read(root['rule_patch_output'])
    pin, pout = [json.loads(x) for x in pin_bytes.splitlines()], [json.loads(x) for x in pout_bytes.splitlines()]
    assert [r['id'] for r in pin] == [r['id'] for r in pout] == ids
    assert pin_bytes == b''.join(l for l, r in zip(source.splitlines(keepends=True), full_inputs) if r['id'] in set(ids))
    assert all(r['status'] == 'completed' and r['result']['current_manual_sha256'] == MANUAL for r in pout)
    assert raw_patch['status_counts'] == {'completed': 34}
    assert raw_patch['input_sha256'] == patch_freeze['input_sha256'] == root['rule_patch_input']['sha256']
    assert raw_patch['output_sha256'] == root['rule_patch_output']['sha256']
    assert raw_patch['full_input_sha256'] == patch_freeze['full_input_sha256'] == root['rule_input']['sha256']
    assert raw_patch['base_full_output_sha256'] == patch_freeze['base_full_output_sha256'] == root['rule_base_output']['sha256']
    assert raw_patch['manual_sha256'] == patch_freeze['manual_sha256'] == MANUAL
    assert raw_patch['runtime_unchanged_during_run'] and raw_patch['baseline_runtime_unchanged']
    assert raw_patch['protected_source_input_output_manual_unchanged'] and raw_patch['no_human_or_model_labels_used']
    assert patch_freeze['expected_labels_not_used']
    assert raw_patch['runtime_manifest'] == patch_freeze['runtime_manifest'] == delivery['all_runtime_files_sha256']
    patch_runtime = Path(root['rule_patch_input']['path']).parent / 'runtime'
    for name, h in patch_freeze['runtime_manifest'].items():
        read({'path': str(patch_runtime / name), 'sha256': h})
    driver_ref = reference(Path(root['rule_patch_input']['path']).parent / '执行保守34一次.py')
    driver = read(driver_ref).decode()
    assert driver.index("(B/'实际34执行冻结.json').write_text") < driver.index("policy_coding_v27.code_unit(row['input'])")
    assert driver_ref['sha256'] == delivery['development_artifacts_sha256']['执行保守34一次.py']
    replacement_lines = dict(zip(ids, pout_bytes.splitlines(keepends=True)))
    base_lines, final_lines = base_bytes.splitlines(keepends=True), final_bytes.splitlines(keepends=True)
    assert all(new == (replacement_lines[rid] if rid in replacement_lines else old)
               for rid, old, new in zip(full_ids, base_lines, final_lines))
    assert root['unchanged_rule_rows_n'] == 4446
    original_run = W / 'LLM编码/测量与语义统一/full4480'
    one_summary_ref = root['one_row_actual_execution'];one_summary = read_json(one_summary_ref)
    one_run = Path(one_summary_ref['path']).parent
    original_summary_ref = next(ref for ref in root['source_bindings'].values() if ref['path'] == str(original_run / 'execution_summary.json'))
    original_summary = read_json(original_summary_ref)
    original_llm_ref = next(ref for ref in root['source_bindings'].values() if ref['path'] == str(original_run / 'all_predictions.jsonl'))
    one_output_ref = {'path': str(one_run / 'all_predictions.jsonl'), 'sha256': one_summary['output_sha256']}
    old_llm = read(original_llm_ref).splitlines(keepends=True);final_llm = read(root['llm_output']).splitlines(keepends=True)
    one_line = read(one_output_ref)
    assert len(old_llm) == len(final_llm) == 4480
    assert all(new == (one_line if rid == 'RECODE25-03875' else old) for rid, old, new in zip(full_ids, old_llm, final_llm))
    assert root['unchanged_llm_rows_n'] == 4479
    for method, raw_ref, raw_lines in [('rule', root['rule_lineage'], final_lines), ('llm', root['llm_lineage'], final_llm)]:
        lineage_rows = [json.loads(x) for x in read(raw_ref).splitlines()]
        assert [r['id'] for r in lineage_rows] == full_ids
        for rec, line in zip(lineage_rows, raw_lines):
            assert rec['row_sha256'] == sha(canonical(json.loads(line)))
            if method == 'rule':
                expected = root['rule_patch_output'] if rec['id'] in ids else root['rule_base_output']
                assert rec['actual_output'] == expected['path'] and rec['actual_output_sha256'] == expected['sha256']
                assert rec['selection_basis'] == ('fixed_source_parse_scope' if rec['id'] in ids else 'unchanged_full_run_row')
            else:
                corrected = rec['id'] == 'RECODE25-03875'
                assert rec['actual_run'] == str(one_run if corrected else original_run)
                assert rec['actual_output_sha256'] == (one_summary['output_sha256'] if corrected else original_summary['output_sha256'])
                assert rec['actual_input_sha256'] == (one_summary['input_sha256'] if corrected else original_summary['input_sha256'])
                assert rec['selection_basis'] == ('fixed_source_correction_id' if corrected else 'unchanged_full_run_row')
    destination.mkdir()
    refs = {}
    def write(name, value, raw_refs):
        value = {**value, 'derived_compatibility_record': True, 'not_a_new_actual_execution_record': True,
                 'derived_from_actual_record_refs': raw_refs,
                 'validation_scope': 'technical file/ID/current-source/runtime lineage checks only; no semantic or human validity certification'}
        p = destination / name;p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        ref = reference(p);refs[name] = ref;return ref
    base_qa = write('derived_rule_base_QA.json', {'all_checks_pass': True, 'actual_execution_complete': True, 'n': 4480,
                    'manual_sha256': MANUAL, 'input_sha256': root['rule_input']['sha256'], 'output_sha256': root['rule_base_output']['sha256']}, [root['rule_base_execution'], freeze_ref])
    scope_ref = write('derived_rule_scope.json', {'scope_ids': ids, 'whole_population_n': 4480, 'input_sha256': root['rule_input']['sha256'],
                     'derived_from_source_parse_scan': True, 'selected_by_labels_or_metrics': False, 'frozen_before_recovery': True,
                     'freeze_order_basis': 'Real frozen scope hash/IDs plus saved executor writes actual34 freeze before code_unit call; no new execution or timestamp invented'}, [root['rule_patch_scope'], root['rule_patch_freeze'], driver_ref])
    patch_qa = write('derived_rule34_QA.json', {'all_checks_pass': True, 'actual_execution_complete': True, 'n': 34, 'ids': ids,
                    'manual_sha256': MANUAL, 'input_sha256': root['rule_patch_input']['sha256'], 'output_sha256': root['rule_patch_output']['sha256']}, [root['rule_patch_report'], root['rule_patch_freeze'], root['rule_patch_delivery']])
    runtime_ref = write('derived_rule34_runtime_freeze.json', {'manual_sha256': MANUAL, 'input_sha256': root['rule_patch_input']['sha256'],
                       'ids': ids, 'runtime_path': str(patch_runtime), 'runtime_files_sha256': patch_freeze['runtime_manifest']}, [root['rule_patch_freeze'], root['rule_patch_delivery']])
    rule_kind = 'full_actual_execution_plus_fixed_source_parse_scope_actual_recovery'
    llm_kind = 'full_actual_execution_plus_one_source_correction_actual_execution'
    rule_lineage = write('derived_rule_lineage.json', {'lineage_kind': rule_kind, 'replacement_ids': ids, 'selection_by_label_or_metric': False,
                         'base_output_sha256': root['rule_base_output']['sha256'], 'final_output_sha256': root['rule_output']['sha256'], 'unchanged_other_row_n': 4446}, [root['rule_lineage'], root_ref])
    llm_lineage = write('derived_llm_lineage.json', {'lineage_kind': llm_kind, 'replacement_ids': ['RECODE25-03875'], 'selection_by_label_or_metric': False,
                        'original_output_sha256': original_summary['output_sha256'], 'correction_output_sha256': one_summary['output_sha256'],
                        'final_output_sha256': root['llm_output']['sha256'], 'unchanged_other_row_n': 4479}, [root['llm_lineage'], root_ref])
    final_qa = write('derived_final_rule_binding_QA.json', {'all_checks_pass': True, 'actual_execution_complete': True, 'n': 4480,
                    'manual_sha256': MANUAL, 'input_sha256': root['rule_input']['sha256'], 'output_sha256': root['rule_output']['sha256'],
                    'lineage_kind': rule_kind, 'full_single_run_not_claimed': True}, [base_qa, patch_qa, rule_lineage, root_ref])
    visual_ref = reference(W / '来源材料核查/03875图示分支校正/独立视觉校核结论01.json')
    manifest = {'status': 'frozen_complete_inputs_outputs_for_comparison', 'target_n': 4481, 'executed_n': 4480, 'manual_sha256': MANUAL,
                'lineage_kind': llm_kind, 'source_change_ids': ['RECODE25-03875'], 'source_changes_selected_by_labels_or_metrics': False,
                'rule_execution_complete': True, 'rule_lineage_kind': rule_kind, 'rule_recovery_ids': ids,
                'files': {**{k: root[k] for k in ['rule_input','rule_output','llm_input','llm_output','frame','rule_base_output']},
                          'root_bundle': root_ref, 'first_full_qa': root['complete_original_llm_execution_QA'], 'rule_execution_qa': final_qa,
                          'rule_freeze_record': freeze_ref, 'llm_lineage': llm_lineage, 'visual_qa': visual_ref,
                          'source_correction_record': root['source_correction'], 'rule_base_qa': base_qa, 'rule_recovery_scope': scope_ref, 'rule_lineage': rule_lineage},
                'correction_llm_run': {'path': str(one_run), 'summary_sha256': one_summary_ref['sha256'], 'output_sha256': one_summary['output_sha256']},
                'rule_recovery_runs': [{'input': root['rule_patch_input'], 'output': root['rule_patch_output'], 'execution_qa': patch_qa, 'runtime_freeze': runtime_ref}],
                'derived_adapter_manifest': True, 'not_new_experiment_evidence': True, 'underlying_actual_records_are_preserved': True,
                'raw_file_bindings_rechecked_while_deriving': bindings, 'derived_wrappers': refs, 'adapter_builder_sha256': sha(Path(__file__).read_bytes())}
    assert all(sha(Path(path).read_bytes()) == meta['sha256'] for path, meta in bindings.items())
    p = destination / 'adapter_manifest.json';p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'path': str(p), 'sha256': sha(p.read_bytes()), 'derived_compatibility_only': True,
                      'rule_unchanged_other_n': 4446, 'llm_unchanged_other_n': 4479}, ensure_ascii=False))


if __name__ == '__main__':
    main()
