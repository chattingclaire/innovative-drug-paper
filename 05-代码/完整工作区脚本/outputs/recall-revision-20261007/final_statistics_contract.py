"""Final-statistics inputs are frozen and require an explicit completed v30 run.

The caller supplies the actual completed prediction hash, execution manifest,
and actual prompt. No previous LLM output is inferred or substituted.
"""
from pathlib import Path
import hashlib
import json

OUT = Path(__file__).resolve().parent
FINAL_MATERIAL_VERSION = 'v3'
FINAL_MATERIAL_READY = True  # Frozen v3 hashes below; actual complete composite manifest is still required.
INPUT_SHA256 = 'ef21e0bd5d07007bc7494ce922987bf55527d64934464406c1b2ef300f86f792'
LLM_INPUT_SHA256 = '7592b73780f2f660c2285b83fe2952921cc4ae1972e31e67a5ecb3fa1e57b5f6'
PROMPT_SHA256 = 'bc2d1ef42d90b369f1949ee954bd37f7e3e5838286e248222c455beb16187753'
MANUAL_SHA256 = '75ff8ebda018a15e008bc1075892000fb9c9c053943d05f04bbe193176c605a6'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    data = [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    result = {r['id']:r for r in data}
    assert len(result) == len(data) == 4924
    return result


def add_arguments(parser):
    parser.add_argument('--rule-execution-manifest', type=Path, required=True,
                        help='Actual final material-v3 full rule execution manifest')
    parser.add_argument('--llm-sha256', required=True, help='Hash of the actual completed full v30 output')
    parser.add_argument('--llm-execution-manifest', type=Path, required=True,
                        help='Actual sealed material-v3 candidate03 composite final_manifest.json')
    parser.add_argument('--llm-prompt', type=Path, required=True, help='Actual frozen prompt used by that run')
    parser.add_argument('--llm-inputs', type=Path, default=OUT/'effective_blind_inputs_v30_v3.jsonl')


def validate_llm_manifest(args):
    """Bind the real v3 composite and independently reconstruct actual material/rows."""
    run=(OUT/'llm-v30/sealed-final-material-v3').resolve()
    assert args.llm.resolve()==run/'all_predictions.jsonl'
    assert args.llm_execution_manifest.resolve()==run/'final_manifest.json'
    manifest=json.loads(args.llm_execution_manifest.read_text())
    assert manifest['status']=='complete_validated_full_corpus' and manifest['n']==4924
    assert manifest['candidate']=='03' and manifest['source_material_version']=='v3'
    design='composite_actual_v2_unchanged_batches_and_unconditional_v3_whole_affected_batch_replacement'
    assert manifest['execution_design']==design
    assert manifest['requested_model']=='gpt-5.6-sol' and manifest['reasoning_effort']=='medium'
    assert Path(manifest['predictions_path']).resolve()==args.llm.resolve()
    assert manifest['predictions_sha256']==args.llm_sha256==sha(args.llm)
    assert manifest['effective_input_sha256']==LLM_INPUT_SHA256==sha(args.llm_inputs)
    assert manifest['shared_rule_input_sha256']==INPUT_SHA256==sha(args.inputs)
    assert manifest['system_prompt_sha256']==PROMPT_SHA256==sha(args.llm_prompt)
    manual=OUT/'llm-v30/protocol-v1.3.md'
    assert manifest['manual_sha256']==sha(manual)==MANUAL_SHA256
    for field in ('mechanically_edited_output_selected','reference_or_metric_based_output_selection'):
        assert manifest[field] is False
    for field in ('not_all_actual_calls_read_v3_full_file','source_rules_and_llm_materials_identical',
                  'all_4924_rows_actual_selected_request_material_equal_final_v3',
                  'all_affected_batches_unconditionally_replaced','not_independent_human_validation'):
        assert manifest[field] is True
    assert manifest['selected_tool_event_count']==0
    assert manifest['affected_original_batch_indices']==[71,72]
    files={'run_plan_sha256':run/'run_plan.json',
           'issue_records_sha256':run/'all_issue_records.json',
           'execution_artifact_hashes_sha256':run/'execution_artifact_hashes.json',
           'selected_execution_lineage_sha256':run/'selected_execution_lineage.json',
           'source_material_QA_sha256':Path(manifest['source_material_QA_path']),
           'independent_source_material_QA_sha256':Path(manifest['independent_source_material_QA_path']),
           'actual_execution_QA_sha256':run/'actual_execution_reconstruction_QA.json',
           'root_execution_QA_sha256':OUT/'最终LLM执行独立核验.json',
           'stability_comparison_v30_sha256':Path(manifest['stability_comparison_v30_path']),
           'stability_sample_material_identity_QA_sha256':run/'stability_sample_material_v3_identity_QA.json'}
    for field,path in files.items():assert sha(path)==manifest[field], (field,path)
    independent=files['independent_source_material_QA_sha256']
    assert independent.resolve()==(OUT/'source_safety_population_v3_independent_QA.json').resolve()
    assert sha(independent)=='90a8e621d7fd7fa37b9d24da35fc2ea3a0856322981dcb0bb3145c47521745ad'
    sourceqa=json.loads(independent.read_text())
    assert sourceqa['status']=='passed' and sourceqa['rule_and_llm_contexts_identical']==4924
    assert sourceqa['original_ids_and_unit_texts_unchanged']==4924
    assert sourceqa['certificates_added_and_bound']==16 and sourceqa['entire_other_records_unchanged']==4919
    assert sha(run/'frozen_independent_source_material_QA.json')==sha(independent)
    plan=json.loads(files['run_plan_sha256'].read_text())
    assert sha(files['run_plan_sha256'])=='a891c2fda090be27cb8f73624221be1b6adfad7622ecf6583088365bfaea778a'
    assert plan['method_version']=='LLM-binary-v30' and plan['candidate']=='03'
    assert plan['source_material_version']=='v3' and plan['execution_design']==design
    assert plan['model']=='gpt-5.6-sol' and plan['reasoning_effort']=='medium'
    assert plan['n']==4924 and plan['batch_count']==197 and plan['batch_size']==25
    assert plan['input_sha256']==LLM_INPUT_SHA256 and plan['shared_rule_input_sha256']==INPUT_SHA256
    assert plan['prompt_sha256']==PROMPT_SHA256 and plan['manual_sha256']==MANUAL_SHA256
    assert Path(plan['source_input_path']).resolve()==args.llm_inputs.resolve()
    assert Path(plan['shared_rule_input_path']).resolve()==args.inputs.resolve()
    for name,value in [('frozen_input.jsonl',LLM_INPUT_SHA256),('frozen_rule_input.jsonl',INPUT_SHA256),
                       ('frozen_prompt.txt',PROMPT_SHA256),('frozen_manual.md',MANUAL_SHA256),
                       ('frozen_schema.json',plan['schema_sha256']),('frozen_validator.py',plan['validator_sha256']),
                       ('frozen_source_material_QA.json',plan['source_material_QA_sha256'])]:
        assert sha(run/name)==value
    assert plan['affected_selection_is_unconditional_not_label_or_metric_based'] is True
    assert plan['all_4924_rows_must_equal_actual_selected_request_material'] is True
    assert plan['reference_labels_read'] is False
    assert plan['affected_original_batch_indices']==[71,72] and plan['affected_actual_n']==50
    original=Path(manifest['original_v2_run_path']).resolve()
    replacement=Path(manifest['affected_actual_run_path']).resolve()
    assert original==(OUT/'llm-v30/production-25-v30-v2').resolve()
    assert replacement==(OUT/'llm-v30/material-v3-affected-full-batches-candidate03').resolve()
    assert Path(plan['original_v2_run_path']).resolve()==original
    assert Path(plan['affected_actual_run_path']).resolve()==replacement
    assert sha(original/'run_plan.json')==plan['original_v2_run_plan_sha256']==manifest['original_v2_run_plan_sha256']
    input_rows=list(rows(args.llm_inputs).values());actual_output=list(rows(args.llm).values())
    old_input=list(rows(original/'frozen_input.jsonl').values())
    changed=[i for i,(a,b) in enumerate(zip(old_input,input_rows)) if a!=b]
    assert changed==[1773,1774,1775,1776,1777]
    assert [r['row_index0'] for r in plan['changed_rows']]==changed
    affected_rows=[r for bi in [71,72] for r in input_rows[(bi-1)*25:bi*25]]
    affected_path=Path(plan['affected_actual_input_path'])
    assert sha(affected_path)==plan['affected_actual_input_sha256']
    assert [json.loads(s) for s in affected_path.read_text().splitlines() if s.strip()]==affected_rows
    assert len(plan['batch_sources'])==197
    lineage=json.loads(files['selected_execution_lineage_sha256'].read_text())
    assert lineage['status']=='all_4924_rows_bound_to_unchanged_selected_actual_responses_and_final_v3_material'
    assert len(lineage['rows'])==4924 and len(lineage['batches'])==197
    reconstructed=[];reconstructed_issues=[];changed_batch_count=0
    for bi,entry in enumerate(plan['batch_sources'],1):
        start,end=(bi-1)*25,min(bi*25,4924)
        assert entry['original_batch_index']==bi and entry['final_row_start0']==start and entry['final_row_end_exclusive']==end
        changed_batch=bi in [71,72]
        assert entry['material_changed'] is changed_batch
        actual_run=replacement if changed_batch else original
        assert Path(entry['actual_run_path']).resolve()==actual_run
        actual_bi=bi-70 if changed_batch else bi
        assert entry['actual_batch_index']==actual_bi
        batch=actual_run/f'batches/batch-{actual_bi:04d}'
        assert Path(entry['actual_batch_path']).resolve()==batch
        packet=json.loads((batch/'input.json').read_text())
        assert packet=={'rows':input_rows[start:end]}, ('Actual batch material differs from final v3',bi)
        assert entry['ids']==[r['id'] for r in packet['rows']]
        request=args.llm_prompt.read_text()+'\n\n--- 本批冻结盲法输入 ---\n'+json.dumps(packet,ensure_ascii=False)+'\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
        assert (batch/'request.txt').read_text()==request
        selection=json.loads((batch/'selection.json').read_text())
        assert selection['status']=='accepted_first_valid_actual_attempt' and selection['selection_uses_metric_or_label_values'] is False
        selected=(actual_run/selection['selected_relative_path']).resolve()
        assert selected.is_relative_to(batch)
        assert json.loads((selected/'input.json').read_text())==packet
        assert (selected/'request.txt').read_text()==request
        raw=selected/'raw_output.json'
        assert sha(raw)==selection['selected_output_sha256']
        response=json.loads(raw.read_text())
        assert [r['id'] for r in response['rows']]==entry['ids']
        reconstructed.extend(response['rows']);reconstructed_issues.extend(response['issue_records'])
        for row in response['rows']:
            binding=lineage['rows'][row['id']]
            assert Path(binding['selected_raw_output_path']).resolve()==raw
            assert binding['selected_raw_output_sha256']==sha(raw) and binding['actual_row_material_equals_final_v3'] is True
            assert Path(binding['actual_input_path']).resolve()==selected/'input.json'
            assert Path(binding['actual_request_path']).resolve()==selected/'request.txt'
        changed_batch_count+=changed_batch
    assert reconstructed==actual_output and changed_batch_count==2
    assert reconstructed_issues==json.loads((run/'all_issue_records.json').read_text())
    summary_path=run/'execution_summary.json';summary=json.loads(summary_path.read_text())
    assert summary['status']=='complete_actual_composite_calls_structurally_valid' and summary['n']==4924
    assert summary['selected_batch_count']==summary['accepted_batch_count']==summary['expected_batch_count']==197
    assert summary['selected_tool_event_count']==0 and summary['source_unchanged_during_seal'] is True
    assert summary['input_sha256']==LLM_INPUT_SHA256 and summary['shared_rule_input_sha256']==INPUT_SHA256
    assert summary['prompt_sha256']==PROMPT_SHA256 and summary['output_sha256']==args.llm_sha256
    assert summary['plan_sha256']==manifest['run_plan_sha256']
    assert summary['all_4924_rows_actual_selected_request_material_equal_final_v3'] is True
    actual=json.loads(files['actual_execution_QA_sha256'].read_text())
    assert actual['status']=='passed_composite_actual_execution_reconstruction' and actual['n']==4924 and actual['binary_label_count']==24620
    assert actual['selected_batches']==197 and actual['selected_tool_events']==0
    assert actual['input_sha256']==LLM_INPUT_SHA256 and actual['shared_rule_input_sha256']==INPUT_SHA256
    assert actual['prompt_sha256']==PROMPT_SHA256 and actual['output_sha256']==args.llm_sha256
    for field in ('all_4924_rows_actual_selected_request_material_equal_final_v3','all_selected_rows_equal_unchanged_actual_raw_outputs',
                  'all_attempts_preserved_and_metadata_hashes_match','all_actual_commands_bound_to_gpt_56_sol_medium',
                  'all_selected_attempts_first_valid_actual_attempts','all_affected_batches_unconditionally_replaced'):
        assert actual[field] is True
    assert actual['reference_or_metric_based_output_selection'] is False
    assert actual['mechanically_edited_output_selected'] is False
    qa=json.loads(files['root_execution_QA_sha256'].read_text())
    assert qa['status']=='passed' and qa['n']==4924 and qa['dimension_labels_checked']==24620
    assert qa['whole_output_literal_and_structure_errors']==[] and qa['predictions_sha256']==args.llm_sha256
    assert qa['effective_input_sha256']==LLM_INPUT_SHA256 and qa['shared_rule_input_sha256']==INPUT_SHA256
    assert qa['input_context_equality_n']==qa['unit_texts_unchanged_n']==4924
    assert qa['selected_tool_event_count']==0 and qa['mechanically_edited_output_selected'] is False
    assert qa['all_4924_rows_actual_selected_request_material_equal_final_v3'] is True
    assert qa['independent_source_material_QA_sha256']==sha(independent)
    stability=json.loads(files['stability_comparison_v30_sha256'].read_text())
    assert stability['status']=='computed_from_new_actual_model_calls' and stability['candidate']=='03'
    assert stability['production_predictions_sha256']==args.llm_sha256 and len(stability['comparisons'])==3
    assert stability['final_full_input_material_version']=='v3' and stability['final_full_input_sha256']==LLM_INPUT_SHA256
    sample=json.loads(files['stability_sample_material_identity_QA_sha256'].read_text())
    assert sample['status']=='passed' and sample['n']==36 and sample['final_v3_input_sha256']==LLM_INPUT_SHA256
    assert sample['all_36_original_sample_rows_equal_final_v3'] is True and sample['sample_bytes_identical_to_v3_subset'] is True
    inventory=json.loads(files['execution_artifact_hashes_sha256'].read_text())
    assert inventory['status']=='actual_original_and_replacement_artifacts_inventory'
    for value_path,value in inventory['artifacts'].items():
        path=Path(value_path).resolve()
        assert any(path.is_relative_to(root) for root in (run,original,replacement))
        assert sha(path)==value, ('Actual execution artifact changed',value_path)
    bindings={str(path.resolve()):sha(path) for path in (*files.values(),summary_path,manual,affected_path,
        original/'run_plan.json',run/'frozen_input.jsonl',run/'frozen_rule_input.jsonl',run/'frozen_prompt.txt',
        run/'frozen_manual.md',run/'frozen_schema.json',run/'frozen_validator.py',run/'frozen_source_material_QA.json',
        run/'frozen_independent_source_material_QA.json',run/'independent_source_QA_binding.json')}
    return {'status':manifest['status'],'candidate':'03','n':4924,'source_material_version':'v3',
            'execution_design':design,'selected_actual_batch_count':197,'unconditional_replacement_batch_count':2,
            'actual_attempt_count':actual['actual_attempt_count'],'actual_material_rows_independently_reconstructed':4924,
            'actual_predictions_rows_independently_reconstructed':4924,
            'requested_model':manifest['requested_model'],'reasoning_effort':manifest['reasoning_effort'],
            'manifest_bound_files':bindings,'actual_execution_artifacts_verified':len(inventory['artifacts'])}


def validate(args):
    assert FINAL_MATERIAL_READY, 'Final statistics await frozen material-v3 and actual composite execution; v2 is diagnostic only.'
    assert args.rule_method == 'rules_v31'
    assert args.rule_version == 'v31-coverage-object-synonyms-20261007'
    assert args.llm_method == 'llm_gpt56_sol_v30'
    assert args.llm and args.llm.resolve().is_relative_to((OUT/'llm-v30').resolve()), 'Final statistics only accepts the explicit new v30 run'
    assert not any('probe' in p.lower() or 'diagnostic' in p.lower() for p in args.llm.parts), 'A development probe cannot enter final statistics'
    assert sha(args.inputs) == INPUT_SHA256
    assert sha(args.rules)=='641e36baefb32e40ec9b1607dc991a3b9196f618865660cd74b119fb519de242'
    assert sha(args.rule_execution_manifest)=='af349b13af73139851319fa0d5a47de82a36e5bafb738ce2c6d5b2f005dac3ea'
    assert sha(args.llm_inputs) == LLM_INPUT_SHA256
    assert sha(args.llm) == args.llm_sha256
    rule_execution=json.loads(args.rule_execution_manifest.read_text())
    assert rule_execution['n']==4924 and rule_execution['pending_n']==0
    assert rule_execution['input_sha256']==INPUT_SHA256
    assert Path(rule_execution['input_path']).resolve()==args.inputs.resolve()
    assert Path(rule_execution['prediction_path']).resolve()==args.rules.resolve()
    assert rule_execution['prediction_sha256']==sha(args.rules)
    assert rule_execution['reference_labels_loaded'] is False
    for path,value in rule_execution['runtime_code_sha256'].items():
        assert sha(path)==value
    assert args.llm_execution_manifest.is_file() and args.llm_prompt.is_file()
    manifest_binding=validate_llm_manifest(args)
    rule_input, llm_input = rows(args.inputs), rows(args.llm_inputs)
    assert set(rule_input) == set(llm_input)
    for rid, r in rule_input.items():
        assert r['input']['unit_text'] == llm_input[rid]['text']
        assert r['input']['llm_v29_shared_context'] == llm_input[rid]['contexts']
    prediction = rows(args.llm)
    assert set(prediction) == set(rule_input)
    for rid,r in prediction.items():
        lab = r.get('prediction',r)['labels']
        assert set(lab) == {'S','E','Ec','I','F'}
        assert all(type(v) is int and v in (0,1) for v in lab.values()), ('Nonbinary actual LLM row',rid)
    return {'rule':{'execution_manifest':str(args.rule_execution_manifest.resolve()),
                    'execution_manifest_sha256':sha(args.rule_execution_manifest),
                    'runtime_code_sha256':rule_execution['runtime_code_sha256']},
            'llm':{'llm_inputs':str(args.llm_inputs.resolve()),'llm_inputs_sha256':LLM_INPUT_SHA256,
            'actual_predictions_sha256':args.llm_sha256,
            'execution_manifest':str(args.llm_execution_manifest.resolve()),
            'execution_manifest_sha256':sha(args.llm_execution_manifest),
            'actual_prompt':str(args.llm_prompt.resolve()),'actual_prompt_sha256':sha(args.llm_prompt),
            **manifest_binding,
            'same_materials_checked':4924,'historical_shared_context_field':'llm_v29_shared_context retains its original key name; its content is the frozen v30 completed v3 input context.'}}
