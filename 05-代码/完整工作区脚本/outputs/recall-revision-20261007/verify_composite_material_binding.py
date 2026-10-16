"""Read-only verification of actual selected requests against final v3 rows."""
from pathlib import Path
from hashlib import sha256
import json,math

ROOT=Path(__file__).resolve().parent
DESIGN='composite_actual_v2_unchanged_batches_and_unconditional_v3_whole_affected_batch_replacement'
def digest(path):return sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
def bound(path,value):assert digest(path)==value,('Material/execution hash mismatch',str(path))

def verify(llm_path,rule_input_path):
    """Verify composition, exact request rows, raw response identity and scope.

    Original v2 plans retain their original full-input hashes.  The condition is
    equality of each selected batch request with the corresponding final v3
    rows; no claim is made that all historical calls read a new full file.
    """
    llm_path=Path(llm_path).resolve();rule_input_path=Path(rule_input_path).resolve()
    assert llm_path.is_relative_to(ROOT)
    run=llm_path.parent;manifest=read(run/'final_manifest.json');plan=read(run/'run_plan.json')
    summary=read(run/'execution_summary.json');lineage=read(run/'selected_execution_lineage.json')
    assert manifest['status']=='complete_validated_full_corpus' and manifest['candidate']=='03'
    assert manifest['source_material_version']==plan['source_material_version']=='v3'
    assert manifest['execution_design']==plan['execution_design']==summary['execution_design']==DESIGN
    assert manifest['not_all_actual_calls_read_v3_full_file'] is True
    assert manifest['all_4924_rows_actual_selected_request_material_equal_final_v3'] is True
    assert manifest['mechanically_edited_output_selected'] is False
    assert manifest['reference_or_metric_based_output_selection'] is False
    assert manifest['selected_tool_event_count']==0 and manifest['all_affected_batches_unconditionally_replaced'] is True
    assert manifest['n']==plan['n']==summary['n']==4924
    current_llm=ROOT/'effective_blind_inputs_v30_v3.jsonl'
    current_rule=ROOT/'rule_inputs_v31_shared_v3.jsonl'
    bound(current_llm,manifest['effective_input_sha256']);bound(current_rule,manifest['shared_rule_input_sha256'])
    assert rule_input_path==current_rule.resolve()
    assert manifest['effective_input_sha256']==plan['input_sha256']==summary['input_sha256']
    assert manifest['shared_rule_input_sha256']==plan['shared_rule_input_sha256']==summary['shared_rule_input_sha256']
    bound(llm_path,manifest['predictions_sha256']);bound(run/'run_plan.json',manifest['run_plan_sha256'])
    bound(run/'selected_execution_lineage.json',manifest['selected_execution_lineage_sha256'])
    bound(ROOT/'llm-v30/完整系统提示词-v30-候选03.txt',manifest['system_prompt_sha256'])
    assert manifest['system_prompt_sha256']==plan['prompt_sha256']==summary['prompt_sha256']
    bound(run/'frozen_prompt.txt',plan['prompt_sha256'])
    bound(run/'frozen_manual.md',manifest['manual_sha256'])
    bound(run/'frozen_input.jsonl',plan['input_sha256'])
    bound(run/'frozen_rule_input.jsonl',plan['shared_rule_input_sha256'])
    source_qa=read(manifest['source_material_QA_path'])
    bound(manifest['source_material_QA_path'],manifest['source_material_QA_sha256'])
    assert source_qa['status'] in {'passed','passed_source_material_and_frozen_certificate_QA'}
    independent=Path(manifest['independent_source_material_QA_path'])
    bound(independent,manifest['independent_source_material_QA_sha256'])
    assert read(independent)['status']=='passed'
    material=rows(current_llm);rules=rows(current_rule);output=rows(llm_path)
    assert len(material)==len(rules)==len(output)==4924
    assert all(a['id']==b['id'] and a['text']==b['input']['unit_text'] and a['contexts']==b['input']['llm_v29_shared_context'] for a,b in zip(material,rules))
    assert [x['id'] for x in material]==[x['id'] for x in output]
    assert len(lineage['rows'])==4924 and set(lineage['rows'])=={r['id'] for r in material}
    assert plan['batch_size']==25
    batch_count=math.ceil(len(material)/plan['batch_size'])
    assert len(plan['batch_sources'])==len(lineage['batches'])==batch_count
    assert summary['selected_batch_count']==summary['accepted_batch_count']==summary['expected_batch_count']==batch_count
    assert manifest['affected_original_batch_indices']==plan['affected_original_batch_indices']
    original=Path(plan['original_v2_run_path'])
    bound(original/'run_plan.json',plan['original_v2_run_plan_sha256'])
    original_plan=read(original/'run_plan.json')
    assert original_plan['input_sha256']==plan['original_v2_input_sha256']
    checked_raw={};rebuilt=[];covered=[];changed_batches=[]
    for expected_bi,(entry,trace) in enumerate(zip(plan['batch_sources'],lineage['batches']),1):
        assert entry['original_batch_index']==trace['original_batch_index']==expected_bi
        start=entry['final_row_start0'];end=entry['final_row_end_exclusive']
        assert start==(expected_bi-1)*25 and end==min(expected_bi*25,4924)
        actual=Path(entry['actual_run_path']);batch=Path(entry['actual_batch_path'])
        localplan=read(actual/'run_plan.json')
        assert localplan['model']=='gpt-5.6-sol' and localplan['reasoning_effort']=='medium'
        assert localplan['prompt_sha256']==plan['prompt_sha256']
        changed=expected_bi in plan['affected_original_batch_indices']
        assert changed==entry['material_changed']==trace['material_changed']
        assert actual.resolve()==Path(plan['affected_actual_run_path'] if changed else plan['original_v2_run_path']).resolve()
        if changed:changed_batches.append(expected_bi)
        packet=read(batch/'input.json')
        assert packet=={'rows':material[start:end]}
        assert entry['ids']==[r['id'] for r in packet['rows']]
        selection=read(batch/'selection.json')
        assert selection['status']=='accepted_first_valid_actual_attempt'
        assert selection['selection_uses_metric_or_label_values'] is False
        attempt=actual/selection['selected_relative_path'];raw=attempt/'raw_output.json'
        bound(raw,selection['selected_output_sha256']);bound(raw,trace['selected_output_sha256'])
        assert trace['selected_output']==str(raw.resolve())
        assert read(attempt/'input.json')==packet
        assert (attempt/'request.txt').read_bytes()==(batch/'request.txt').read_bytes()
        meta=read(attempt/'run_metadata.json')
        assert meta['requested_model']=='gpt-5.6-sol' and meta['reasoning_effort']=='medium'
        assert meta['tool_event_count']==0 and meta['label_or_metric_selection'] is False
        assert meta['status']=='accepted_structural_literal_zero_tools'
        bound(attempt/'input.json',meta['input_sha256']);bound(attempt/'request.txt',meta['request_sha256'])
        data=read(raw);assert [r['id'] for r in data['rows']]==entry['ids']
        for r in data['rows']:
            binding=lineage['rows'][r['id']]
            assert binding['actual_row_material_equals_final_v3'] is True
            assert binding['selected_raw_output_path']==str(raw.resolve())
            assert binding['selected_raw_output_sha256']==digest(raw)
            assert binding['actual_input_path']==str((attempt/'input.json').resolve())
            assert binding['actual_request_path']==str((attempt/'request.txt').resolve())
        checked_raw[str(raw.resolve())]=digest(raw);rebuilt.extend(data['rows']);covered.extend(entry['ids'])
    assert rebuilt==output and len(covered)==len(set(covered))==4924
    assert changed_batches==plan['affected_original_batch_indices']
    reconstruction=read(run/'actual_execution_reconstruction_QA.json')
    bound(run/'actual_execution_reconstruction_QA.json',manifest['actual_execution_QA_sha256'])
    assert reconstruction['status']=='passed_composite_actual_execution_reconstruction'
    assert reconstruction['all_selected_rows_equal_unchanged_actual_raw_outputs'] is True
    return {'status':'passed_current_v3_selected_actual_request_and_raw_output_binding',
        'n':4924,'selected_batch_count':batch_count,'batch_size':plan['batch_size'],
        'affected_original_batch_indices':changed_batches,'actual_historical_attempt_count':summary['actual_attempt_count'],
        'rule_input_sha256':digest(current_rule),'llm_input_sha256':digest(current_llm),
        'prediction_sha256':digest(llm_path),'prompt_sha256':plan['prompt_sha256'],
        'final_manifest_sha256':digest(run/'final_manifest.json'),
        'all_selected_request_rows_equal_final_v3':True,'output_rebuilt_from_unchanged_actual_raw_rows':True,
        'not_all_historical_calls_read_v3_full_file':True,'selected_raw_response_sha256':checked_raw}
