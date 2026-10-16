"""Independent read-only QA of original plus source-only whole-batch repair.

Checks actual input/request/raw/selection/events/hash and reconstruction only.
Does not read A/C/T, assign labels, edit quotes or select by accuracy.
Run only after final source freeze and reconciler seal, using explicit SHA bindings.
"""
from pathlib import Path
from collections import Counter
import argparse
import datetime
import hashlib
import importlib.util
import json
import jsonschema
import statistical_core_r3 as c
import reference_bindings_r3 as b


def bound(value):return b.bound_json(value)
def read(path):return json.loads(Path(path).read_text())
def jl(path):return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
def request(prompt,packet):
    return prompt+'\n\n--- 本批冻结盲法输入 ---\n'+json.dumps(packet,ensure_ascii=False)+'\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
def digest(text):return hashlib.sha256(text.encode()).hexdigest()


def event_audit(text):
    """Independent reconstruction of frozen runner's event acceptance contract."""
    violations=[];counts=Counter();models=[];complete=0;turn_errors=[]
    for index,line in enumerate(text.splitlines()):
        if not line.strip():continue
        try:event=json.loads(line)
        except ValueError:
            violations.append({'line':index+1,'reason':'non_json_event'});continue
        kind=event.get('type');item=event.get('item',{});item_kind=item.get('type') if isinstance(item,dict) else None
        counts[f'{kind}/{item_kind}']+=1
        for field in ('model','model_name'):
            if isinstance(event.get(field),str) and event[field] not in models:models.append(event[field])
        if item_kind is not None and item_kind not in {'agent_message','reasoning'}:
            violations.append({'line':index+1,'reason':'non_message_item_potential_tool','event':event})
        if isinstance(kind,str) and any(token in kind.lower() for token in ('tool_call','function_call','web_search','web_fetch','command_execution')):
            violations.append({'line':index+1,'reason':'tool_event_type','event':event})
        if kind=='turn.completed':complete+=1
        if kind in {'turn.failed','error'}:turn_errors.append(event)
    return {'tool_or_unknown_item_event_count':len(violations),'violations':violations,
            'event_type_counts':dict(counts),'observed_model_fields':models,'completed_turns':complete,'turn_errors':turn_errors}


def validator_module(path):
    spec=importlib.util.spec_from_file_location('frozen_literal_validator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def audit_batch(run,index,packet,prompt,plan,validator,schema):
    directory=run/'batches'/f'batch-{index:04d}';selection_path=directory/'selection.json'
    selection=read(selection_path);expected_request=request(prompt,packet)
    assert read(directory/'input.json')==packet
    assert (directory/'request.txt').read_text()==expected_request
    assert selection['batch']==index and selection['input_n']==len(packet['rows'])
    assert selection['ids']==[row['id'] for row in packet['rows']]
    assert selection['selection_uses_metric_or_label_values'] is False
    first_valid=None;attempt_records=[]
    for expected_index,entry in enumerate(selection['attempts'],1):
        assert entry['attempt']==expected_index
        path=run/entry['relative_path'];meta=read(path/'run_metadata.json')
        assert c.sha(path/'run_metadata.json')==entry['metadata_sha256']
        assert read(path/'input.json')==packet and (path/'request.txt').read_text()==expected_request
        assert meta['input_sha256']==c.sha(path/'input.json') and meta['request_sha256']==digest(expected_request)
        assert meta['prompt_sha256']==plan['prompt_sha256']
        assert meta['requested_model']==plan['model'] and meta['reasoning_effort']==plan['reasoning_effort']
        assert meta['cli_binary_sha256']==plan['cli_binary_sha256'] and meta['cli_version']==plan['cli_version']
        assert meta['label_or_metric_selection'] is False
        for file,key in [('events.jsonl','events_sha256'),('raw_stderr.txt','stderr_sha256'),
                         ('tool_event_audit.json','tool_event_audit_sha256'),('validation.json','validation_sha256')]:
            assert c.sha(path/file)==meta[key]
        audit=event_audit((path/'events.jsonl').read_text());assert audit==read(path/'tool_event_audit.json')
        assert audit['tool_or_unknown_item_event_count']==meta['tool_event_count']==entry['tool_event_count']
        assert entry['events_sha256']==meta['events_sha256']
        errors=[]
        if meta['exit_code']!=0:errors.append('cli_execution_failure')
        raw_path=path/'raw_output.json';raw=None
        if not raw_path.exists():errors.append('missing_raw_output');assert meta['raw_output_sha256'] is None
        else:
            assert c.sha(raw_path)==meta['raw_output_sha256']==entry['raw_output_sha256']
            try:raw=read(raw_path);errors.extend(validator.validate(packet,raw))
            except Exception as error:errors.append(f'json_or_validator_error:{type(error).__name__}:{error}')
        if audit['tool_or_unknown_item_event_count']:errors.append('nonzero_tool_or_unknown_item_events')
        if audit['completed_turns']!=1:errors.append('completed_turn_count_not_one')
        if audit['turn_errors']:errors.append('turn_error_event')
        if audit['observed_model_fields'] and any(model!=plan['model'] for model in audit['observed_model_fields']):errors.append('observed_model_mismatch')
        assert errors==meta['errors']==entry['errors']
        validation=read(path/'validation.json')
        assert validation['valid']==(not errors) and validation['errors']==errors
        expected_status='accepted_structural_literal_zero_tools' if not errors else 'failed_attempt_preserved'
        assert meta['status']==entry['status']==expected_status
        if not errors:
            jsonschema.Draft202012Validator(schema).validate(raw)
            if first_valid is None:first_valid=path
        attempt_records.append({'attempt':expected_index,'status':expected_status,'errors':errors,
            'metadata_sha256':entry['metadata_sha256'],'request_sha256':meta['request_sha256'],
            'tool_events':meta['tool_event_count'],'raw_sha256':meta['raw_output_sha256']})
    if first_valid is None:
        assert selection['status']=='all_attempts_failed_preserved' and selection['selected_relative_path'] is None
        selected_raw=None;selected_path=None
    else:
        assert selection['status']=='accepted_first_valid_actual_attempt'
        assert (run/selection['selected_relative_path']).resolve()==first_valid.resolve()
        assert c.sha(first_valid/'raw_output.json')==selection['selected_output_sha256']
        selected_raw=read(first_valid/'raw_output.json');selected_path=first_valid/'raw_output.json'
    return {'batch':index,'run':str(run),'selection_path':str(selection_path),
            'selection_sha256':c.sha(selection_path),'selected_raw_path':str(selected_path) if selected_path else None,
            'selected_raw_sha256':c.sha(selected_path) if selected_path else None,
            'attempts':attempt_records,'selected_raw':selected_raw}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bindings',type=Path,required=True);parser.add_argument('--bindings-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    assert not args.out.exists() and c.sha(args.bindings)==args.bindings_sha256
    manifest=read(args.bindings);assert manifest['root_final_source_bindings_confirmed'] is True
    assert bound(manifest['source_qa'])['all_checks_pass'] is True
    original_plan=bound(manifest['original_plan']);repair_plan=bound(manifest['reconciliation_plan'])
    assert original_plan['method_version']=='LLM-binary-v32'
    assert original_plan['prompt_sha256']=='682770e2fb6f1a6b8b7ba1703f6900d7ee0d586179282b94c14e0b23feec300e'
    summary=bound(manifest['reconciled_summary']);lineage=bound(manifest['batch_lineage'])
    assert summary['status']=='complete_actual_five_dimension_calls_with_source_only_batch_repair'
    assert summary['old_three_dimension_outputs_used'] is False and summary['reference_label_or_metric_selection'] is False
    original=Path(manifest['original_plan']['path']).parent;repair=Path(manifest['reconciliation_plan']['path']).parent
    assert repair_plan['original_plan_sha256']==manifest['original_plan']['sha256']
    assert Path(repair_plan['original_run']).resolve()==original.resolve()
    final_input=Path(manifest['final_input']['path']);assert c.sha(final_input)==manifest['final_input']['sha256']==repair_plan['new_input_sha256']
    new=jl(final_input);old=jl(original/original_plan['frozen_input_relative_path'])
    assert c.sha(original/original_plan['frozen_input_relative_path'])==original_plan['input_sha256']
    assert c.sha(repair/'frozen_input.jsonl')==repair_plan['new_input_sha256']
    assert len(new)==len(old)==4924 and len({row['id'] for row in new})==4924
    assert all(a['id']==b['id'] and a['text']==b['text'] and a['source_title']==b['source_title']
               and a['pages']==b['pages'] for a,b in zip(old,new))
    prompt=(repair/'frozen_prompt.txt').read_text()
    assert digest(prompt)==original_plan['prompt_sha256']==repair_plan['prompt_sha256']==summary['prompt_sha256']
    for file,key in [('frozen_prompt.txt','prompt_sha256'),('frozen_validator.py','validator_sha256'),
                     ('frozen_schema.json','schema_sha256'),('frozen_runner.py','runner_sha256')]:
        assert c.sha(original/file)==c.sha(repair/file)==original_plan[key]
    validator=validator_module(repair/'frozen_validator.py');schema=read(repair/'frozen_schema.json')
    assert c.sha(repair/'batch_lineage.json')==summary['lineage_sha256']==manifest['batch_lineage']['sha256']
    size=original_plan['batch_size'];assert size==25
    assert original_plan['batch_count']==repair_plan['batch_count']==summary['batch_count']==len(lineage)==197
    records={row['batch']:row for row in repair_plan['batch_records']};assert set(records)==set(range(1,198))
    original_audits=[];final_audits=[];aggregate=[];issues=[];expected_reruns=[];changed_ids=[]
    for index in range(1,198):
        offset=(index-1)*size;old_packet={'rows':old[offset:offset+size]};new_packet={'rows':new[offset:offset+size]}
        original_audit=audit_batch(original,index,old_packet,prompt,original_plan,validator,schema)
        original_audits.append(original_audit);record=records[index]
        changed=old_packet!=new_packet;failed=original_audit['selected_raw'] is None
        changed_ids.extend(b['id'] for a,b in zip(old_packet['rows'],new_packet['rows']) if a!=b)
        action='rerun_complete_batch' if changed or failed else 'reuse_exact_batch'
        assert record['action']==action and record['changed_input']==changed and record['old_execution_failed']==failed
        assert record['old_selection_sha256']==original_audit['selection_sha256']
        if changed or failed:
            expected_reruns.append(index);selected=audit_batch(repair,index,new_packet,prompt,original_plan,validator,schema)
        else:
            selected=original_audit
            selected_dir=Path(selected['selected_raw_path']).parent
            assert (selected_dir/'request.txt').read_text()==request(prompt,new_packet),'Reused request must remain byte-identical to final whole-batch request'
            assert read(selected_dir/'input.json')==new_packet
        assert selected['selected_raw'] is not None
        line=lineage[index-1];assert line['batch']==index and line['action']==action
        assert line['selected_raw_path']==selected['selected_raw_path'] and line['selected_raw_sha256']==selected['selected_raw_sha256']
        assert line['selection_sha256']==selected['selection_sha256'] and line['all_five_dimensions_from_one_actual_raw_row'] is True
        assert line['selection_path']==selected['selection_path']
        selected_dir=Path(selected['selected_raw_path']).parent
        assert line['metadata_sha256']==c.sha(selected_dir/'run_metadata.json')
        assert line['input_sha256']==c.sha(selected_dir/'input.json')
        aggregate.extend(selected['selected_raw']['rows']);issues.extend(selected['selected_raw']['issue_records'])
        final_audits.append(selected)
    assert expected_reruns==repair_plan['rerun_batches'] and changed_ids==repair_plan['changed_ids']
    full_json=bound(manifest['aggregate_json']);output=Path(manifest['output_jsonl']['path'])
    assert c.sha(output)==manifest['output_jsonl']['sha256']==summary['output_sha256']
    assert full_json['rows']==jl(output)==aggregate and full_json['issue_records']==issues
    assert not validator.validate({'rows':new},full_json)
    old_attempts=sum(len(row['attempts']) for row in original_audits)
    repair_attempts=sum(len(row['attempts']) for row in final_audits if Path(row['run']).resolve()==repair.resolve())
    final_attempts=sum(len(row['attempts']) for row in final_audits)
    final_tools=sum(a['tool_events'] for row in final_audits for a in row['attempts'])
    original_tools=sum(a['tool_events'] for row in original_audits for a in row['attempts'])
    repair_tools=sum(a['tool_events'] for row in final_audits if Path(row['run']).resolve()==repair.resolve() for a in row['attempts'])
    assert summary['selected_branch_actual_attempt_count']==final_attempts
    assert summary['selected_branch_all_attempt_tool_events']==final_tools
    assert summary['new_whole_batches']==len(expected_reruns) and summary['reused_exact_input_batches']==197-len(expected_reruns)
    for row in original_audits+final_audits:row.pop('selected_raw',None)
    qa={'status':'pass_independent_execution_QA','all_checks_pass':True,
        'created_at':datetime.datetime.now().astimezone().isoformat(),'final_material_version':manifest['final_material_version'],
        'final_output_sha256':manifest['output_jsonl']['sha256'],'n':4924,'batch_count':197,
        'original_actual_attempt_count':old_attempts,'new_repair_actual_attempt_count':repair_attempts,
        'all_actual_attempts_including_superseded_original_count':old_attempts+repair_attempts,
        'original_all_attempt_tool_events':original_tools,'new_repair_all_attempt_tool_events':repair_tools,
        'all_historical_attempt_tool_events':original_tools+repair_tools,
        'selected_branch_actual_attempt_count':final_attempts,'selected_branch_all_attempt_tool_events':final_tools,
        'new_whole_batches':len(expected_reruns),'reused_exact_input_batches':197-len(expected_reruns),
        'changed_source_input_rows':len(changed_ids),'original_failed_batches':[row['batch'] for row in original_audits if row['selected_raw_path'] is None],
        'all4924_exact_raw_objects_reconstructed':True,'all_five_dimensions_from_actual_v32_row':True,
        'old_three_dimension_outputs_used':False,'reference_labels_or_metrics_read':False,
        'first_valid_selection_checked_independently':True,'source_unchanged_while_QA_ran':c.sha(final_input)==manifest['final_input']['sha256'],
        'original_branch_audit':original_audits,'final_selected_branch_audit':final_audits,
        'bindings':manifest,'binding_manifest_sha256':args.bindings_sha256,'script_sha256':c.sha(Path(__file__)),
        'limits':['Actual requests/raw/events/firstvalid and source reconstruction verified; semantic correctness not established.',
                  'Requested model and exposed events preserved; provider internal revision not fabricated.',
                  'Complete historical original attempts counted separately from final selected provenance branch.']}
    assert qa['source_unchanged_while_QA_ran']
    c.write_json(args.out,qa)
    print(json.dumps({'status':qa['status'],'n':4924,'new_batches':len(expected_reruns),
                     'actual_attempts_all_history':old_attempts+repair_attempts,'out':str(args.out)},ensure_ascii=False))


if __name__=='__main__':main()
