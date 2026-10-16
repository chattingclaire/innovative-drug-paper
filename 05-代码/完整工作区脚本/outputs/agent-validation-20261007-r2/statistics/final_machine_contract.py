"""Reject partial/fallback predictions and bind completed material-v8 execution."""
from statistical_core import *

def bound_hashes(mapping):
    for path,value in mapping.items():assert sha(path)==value,(path,'SHA mismatch')

def rule_binding():
    folder=RUN/'rules-v32/material-adapter-v32.1';release=folder/'release_material_v8_manifest.json'
    assert sha(release)=='504073ba1a41c69981c1d54dc9593f2816e33e9c2bd8c790424c386ca1b0676f'
    r=read(release);assert r['n']==4924 and r['source_material_version']=='v8'
    expected={'input_sha256':'e43300eed535cc1e0bb055830a9f2a0123ec17db7536333d6f1ca518283fdd11',
        'llm_material_sha256':'820d4cc554975e59e8e839a2bf12b381e76c1b32175cd97524104f340351e4e4',
        'prediction_sha256':'3c5f65354e67955b27b6483c2f564d16e2a6b91193362fdf236618ae71340896',
        'run_manifest_sha256':'0df6a460ff808630352ccca9ee9ad995d3c095c970af3b027603ebd0761505fc'}
    for key,value in expected.items():assert r[key]==value
    pairs=[('input_path','input_sha256'),('llm_material_path','llm_material_sha256'),('prediction_path','prediction_sha256'),('run_manifest_path','run_manifest_sha256'),('freeze_path','freeze_sha256'),('QA_path','QA_sha256'),('change_path','change_sha256')]
    paths=[release,Path(__file__)]
    for path_key,hash_key in pairs:
        path=Path(r[path_key]);assert sha(path)==r[hash_key];paths.append(path)
    bound_hashes(r['production_runtime_sha256']);bound_hashes(r['material_manifests_sha256'])
    paths.extend(map(Path,r['production_runtime_sha256']));paths.extend(map(Path,r['material_manifests_sha256']))
    run=read(r['run_manifest_path']);qa=read(r['QA_path'])
    assert run['n']==4924 and run['pending_n']==0 and run['reference_labels_loaded'] is False
    assert qa['status']=='passed_actual_4924_same_code_material_v8' and qa['n']==4924 and qa['candidate_code_unchanged'] is True and qa['reference_labels_or_agent_metrics_read'] is False
    prediction=jsonl(r['prediction_path']);assert len(prediction)==4924
    assert all(binary(label(row,d)) for row in prediction.values() for d in DIMS)
    return prediction,{'method':'rules_v32_1_material_v8','reference_exposure_note':'Source-table material adapter after disclosed material defect; no claim of untouched confirmatory development.',
        'path':r['prediction_path'],'prediction_sha256':r['prediction_sha256'],'release_path':str(release),'release_sha256':sha(release),'source_material_version':'v8'},paths

def llm_binding():
    folder=RUN/'llm-v31/sealed-final-material-v8';manifest_path=folder/'final_manifest.json'
    assert manifest_path.exists(),'Complete v6 LLM manifest not yet present; partial output is never substituted.'
    assert sha(manifest_path)=='101932ac72e8a13ab9c7ea3adf3c8ec05104aabd351d6a2a333fc6f2938715f1'
    m=read(manifest_path)
    assert m['status']=='complete_actual_execution_dimension_explicit' and m['n']==4924 and m['material_version']=='v8'
    assert m['requested_model']=='gpt-5.6-sol' and m['I_F_actual_reread_n']==4924
    assert m['S_E_Ec_original_actual_retained_n']==4699 and m['S_E_Ec_same_prompt_material_batch_rerun_n']==225
    assert m['all_methods_final_material_same'] is True and m['all_I_F_selected_batches_input_exactly_final'] is True
    assert m['changed_batches_unconditional']==[57,58,68,90,133,166,167,168,185] and m['selected_I_F_batch_n']==197 and m['selected_S_E_Ec_refresh_batch_n']==9
    assert m['references_or_metrics_used_to_select_outputs'] is False and m['human_validation_completed'] is False
    bound_hashes(m['source_sha256']);bound_hashes(m['outputs_sha256']);bound_hashes(m['material_manifests_sha256'])
    assert m['all_original_197_batches_attempt_audited'] is True
    assert m['technical_repair_original_batches']==[]
    independent=RUN/'最终LLM执行独立核验-v31-v8.json'
    assert sha(independent)=='3844d9c32d07dbb42812d31c586e2c9acfc2185c12527546105e6acd8ef68c15' and read(independent)['status']=='passed'
    assert m['source_sha256'][str(RUN/'effective_blind_inputs_v8.jsonl')]=='820d4cc554975e59e8e839a2bf12b381e76c1b32175cd97524104f340351e4e4'
    assert m['source_sha256'][str(RUN/'rule_inputs_shared_v8.jsonl')]=='e43300eed535cc1e0bb055830a9f2a0123ec17db7536333d6f1ca518283fdd11'
    final_inputs=list(jsonl(RUN/'effective_blind_inputs_v8.jsonl').values());lookup={r['id']:r for r in final_inputs}
    lineages=read(folder/'selected_actual_execution_lineage.json');assert len(lineages['if'])==m['selected_I_F_actual_call_n']==197 and len(lineages['se_ec_material_refresh'])==9
    paths=[manifest_path,Path(__file__),independent]+list(map(Path,m['source_sha256']))+list(map(Path,m['outputs_sha256']))
    def selected(record):
        run=Path(record['run']);selection_path=run/'batches'/f'batch-{record["batch_index"]:04d}'/'selection.json'
        selection=read(selection_path);assert sha(selection_path)==record['selection_sha256']
        assert selection['status']=='accepted_first_valid_actual_attempt'
        accepted=[a for a in selection['attempts'] if a['status']=='accepted_structural_literal_zero_tools']
        assert accepted and accepted[0]['relative_path']==selection['selected_relative_path']==record['selected_relative_path']
        dest=run/record['selected_relative_path'];meta=read(dest/'run_metadata.json');audit=read(dest/'tool_event_audit.json')
        assert meta['requested_model']=='gpt-5.6-sol' and meta['tool_event_count']==0 and meta['label_or_metric_selection'] is False
        assert audit['tool_or_unknown_item_event_count']==0 and audit['completed_turns']==1
        for filename,key in [('raw_output.json','raw_output_sha256'),('input.json','input_sha256'),('run_metadata.json','metadata_sha256'),('events.jsonl','events_sha256')]:
            assert sha(dest/filename)==record[key];paths.append(dest/filename)
        assert sha(dest/'raw_output.json')==meta['raw_output_sha256']==selection['selected_output_sha256']
        assert sha(dest/'events.jsonl')==meta['events_sha256']
        paths.extend([selection_path,dest/'tool_event_audit.json',run/'run_plan.json'])
        inp=read(dest/'input.json')['rows'];out=read(dest/'raw_output.json')['rows']
        assert [r['id'] for r in inp]==[r['id'] for r in out]
        assert all(r==lookup[r['id']] for r in inp)
        return inp,out,read(run/'run_plan.json')
    if_rows=[];new_prompt_sha=sha(RUN/'llm-v31/I-F复核提示词-v31-候选02.txt')
    for index,record in enumerate(lineages['if'],1):
        assert record['original_batch_index']==index
        inp,out,plan=selected(record);assert inp==final_inputs[(index-1)*25:index*25]
        assert plan['prompt_sha256']==new_prompt_sha
        if index in (57,58,68,90,133,166,167,168,185):assert record['reason']=='changed_input_complete_batch_unconditional'
        if_rows.extend(out)
    assert len(if_rows)==4924
    assert jsonl(folder/'all_predictions_if_actual.jsonl')=={r['id']:r for r in if_rows}
    old=jsonl(OLD/'llm-v30/sealed-final-material-v3/all_predictions.jsonl');seec=dict(old);patched=set()
    old_inputs=jsonl(OLD/'effective_blind_inputs_v30_v3.jsonl');old_prompt_sha=sha(OLD/'llm-v30/完整系统提示词-v30-候选03.txt')
    for record in lineages['se_ec_material_refresh']:
        inp,out,plan=selected(record);assert plan['prompt_sha256']==old_prompt_sha
        for row in out:assert row['id'] not in patched;patched.add(row['id']);seec[row['id']]=row
    assert len(patched)==225
    composite_path=folder/'all_predictions_composite.jsonl';assert sha(composite_path)=='5383bf837699ff1209c70b979d7876c5150c62cf9d213860d727b43cbca98ab8';composite=jsonl(composite_path);assert len(composite)==4924
    for if_row in if_rows:
        rid=if_row['id'];r=composite[rid]
        if rid not in patched:assert lookup[rid]==old_inputs[rid]
        assert r['material_version']=='v8'
        for dim in ('S','E','Ec'):
            assert label(r,dim)==label(seec[rid],dim) and r['dimension_reasons'][dim]==seec[rid]['dimension_reasons'][dim]
        for dim in ('I','F'):
            assert label(r,dim)==label(if_row,dim) and r['dimension_reasons'][dim]==if_row['dimension_reasons'][dim]
        assert r['innovation_subtypes']==if_row['innovation_subtypes'] and r['fairness_subtypes']==if_row['fairness_subtypes']
        assert r['evidence']==[e for e in seec[rid]['evidence'] if e['dimension'] in ('S','E','Ec')]+if_row['evidence']
        assert all(binary(label(r,d)) for d in DIMS)
    assert len(lineages['se_ec_retained_4699_row_sources'])==4699
    old_raw={}
    for rid,b in lineages['se_ec_retained_4699_row_sources'].items():
        assert sha(b['raw_path'])==b['raw_sha256']
        if b['raw_path'] not in old_raw:
            raw=read(b['raw_path'])['rows'];inp=read(b['actual_input_path'])['rows']
            old_raw[b['raw_path']]={row['id']:(source,row) for source,row in zip(inp,raw)}
            paths.extend([Path(b['raw_path']),Path(b['actual_input_path'])])
        inp,out=old_raw[b['raw_path']][rid];assert inp==lookup[rid] and out==old[rid]
    return composite,{'method':'llm_v31_IF_v30_SEEc_material_v8','path':str(composite_path),'prediction_sha256':sha(composite_path),'manifest_path':str(manifest_path),'manifest_sha256':sha(manifest_path),
        'source_material_version':'v8','I_F_actual_rows':4924,'S_E_Ec_old_actual_rows_material_identical':4699,'S_E_Ec_same_prompt_material_refresh_rows':225,
        'paired_execution_identity_independently_reconstructed':True},list(dict.fromkeys(paths))

def old_bindings():
    paths={'old_rules_v31_v3':OLD/'rules-v31/all_predictions_completed_material_v3.jsonl',
           'old_llm_v30_v3':OLD/'llm-v30/sealed-final-material-v3/all_predictions.jsonl'}
    expected={'old_rules_v31_v3':'641e36baefb32e40ec9b1607dc991a3b9196f618865660cd74b119fb519de242',
              'old_llm_v30_v3':'dd57127cbb5217a78a4d458dacaef702e9ca3101b7a8ab7a5fd4b9f3d8f453f7'}
    for key,path in paths.items():assert sha(path)==expected[key]
    return {key:jsonl(path) for key,path in paths.items()}, {key:{'path':str(path),'prediction_sha256':expected[key],'material_version':'v3','comparison_note':'Historical method+v3-material baseline; NOT a pure code-only or prompt-only causal contrast.'} for key,path in paths.items()},list(paths.values())
