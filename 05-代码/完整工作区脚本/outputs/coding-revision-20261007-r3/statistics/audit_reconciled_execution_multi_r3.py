"""Independent read-only QA of explicitly ordered actual source-repair runs.

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
    assert 0 < len(selection['attempts']) <= plan['max_attempts']
    actual_attempt_dirs=sorted(path.resolve() for path in (directory/'attempts').iterdir() if path.is_dir())
    declared_attempt_dirs=sorted((run/entry['relative_path']).resolve() for entry in selection['attempts'])
    assert actual_attempt_dirs==declared_attempt_dirs, 'All actual attempt directories must be retained in selection history'
    for expected_index,entry in enumerate(selection['attempts'],1):
        assert first_valid is None, 'Frozen runner stops after chronological first valid attempt'
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
            'actual_attempt_directory':str(path.resolve()),
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


FROZEN_PROMPT_SHA='682770e2fb6f1a6b8b7ba1703f6900d7ee0d586179282b94c14e0b23feec300e'
COMPLETE_STATUS='complete_actual_five_dimension_calls_with_source_only_batch_repair'


def same_source_identity(original,current):
    assert len(original)==len(current)==4924
    assert len({row['id'] for row in current})==4924
    assert all(a['id']==z['id'] and a['text']==z['text'] and a['source_title']==z['source_title']
               and a['pages']==z['pages'] for a,z in zip(original,current))


def selection_inventory(run):
    batches=run/'batches'
    assert batches.is_dir()
    indices=[]
    for directory in sorted(path for path in batches.iterdir() if path.is_dir()):
        assert directory.name.startswith('batch-')
        index=int(directory.name.removeprefix('batch-'))
        assert directory.name==f'batch-{index:04d}'
        assert (directory/'selection.json').exists(), 'Unfinished actual batch cannot be silently omitted'
        indices.append(index)
    return indices


def frozen_files(run,original_plan):
    for filename,key in [('frozen_prompt.txt','prompt_sha256'),('frozen_validator.py','validator_sha256'),
                         ('frozen_schema.json','schema_sha256'),('frozen_runner.py','runner_sha256')]:
        assert c.sha(run/filename)==original_plan[key]


def load_repair_contract(run,plan,original,original_plan,old):
    assert Path(plan['original_run']).resolve()==original
    assert plan['original_plan_sha256']==c.sha(original/'run_plan.json')
    assert plan['prompt_sha256']==original_plan['prompt_sha256']==FROZEN_PROMPT_SHA
    assert plan['model']==original_plan['model'] and plan['reasoning_effort']==original_plan['reasoning_effort']
    assert plan['batch_size']==25 and plan['batch_count']==197 and plan['n']==4924
    assert plan['max_attempts']==original_plan['max_attempts']
    assert plan['selection_rule']==original_plan['selection_rule']
    assert plan['labels_or_metrics_read'] is False and plan['source_order_and_unit_text_unchanged'] is True
    frozen_files(run,original_plan)
    assert c.sha(run/'frozen_input.jsonl')==plan['new_input_sha256']
    source=jl(run/'frozen_input.jsonl');same_source_identity(old,source)
    indices=plan['rerun_batches']
    assert indices==sorted(set(indices)) and all(1<=index<=197 for index in indices)
    assert selection_inventory(run)==indices, 'Own actual batches only; inherited batches must not be counted as new calls'
    return source,indices


def earliest_exact(origins,histories,index,packet,prompt):
    for origin in origins:
        record=histories[str(origin)].get(index)
        if record is None or record['selected_raw'] is None:continue
        selected=Path(record['selected_raw_path']).parent
        if read(selected/'input.json')!=packet:continue
        assert (selected/'request.txt').read_text()==request(prompt,packet)
        return origin,record
    return None,None


def assert_lineage(line,selected,index,action,origin):
    assert line['batch']==index and line['action']==action
    assert line['actual_origin_run']==str(origin)
    assert line['selected_raw_path']==selected['selected_raw_path']
    assert line['selected_raw_sha256']==selected['selected_raw_sha256']
    assert line['selection_path']==selected['selection_path'] and line['selection_sha256']==selected['selection_sha256']
    assert line['all_five_dimensions_from_one_actual_raw_row'] is True
    selected_dir=Path(selected['selected_raw_path']).parent
    assert line['metadata_sha256']==c.sha(selected_dir/'run_metadata.json')
    assert line['input_sha256']==c.sha(selected_dir/'input.json')


def validate_repair_assembly(run,plan,summary,source,origins,histories,prompt,old,original):
    """Independently replay source-only decisions, including earlier sealed repairs."""
    assert summary['status']==COMPLETE_STATUS
    assert summary['old_three_dimension_outputs_used'] is False and summary['reference_label_or_metric_selection'] is False
    assert summary['prompt_sha256']==FROZEN_PROMPT_SHA and summary['new_input_sha256']==plan['new_input_sha256']
    assert summary['n']==4924 and summary['batch_count']==197
    lines=read(run/'batch_lineage.json')
    assert c.sha(run/'batch_lineage.json')==summary['lineage_sha256'] and len(lines)==197
    records={record['batch']:record for record in plan['batch_records']}
    assert len(plan['batch_records'])==197 and set(records)==set(range(1,198))
    own_records=histories[str(run)];old_records=histories[str(original)]
    aggregate=[];issues=[];selected_records=[];expected_reruns=[];changed_ids=[];origin_counts=Counter()
    is_multi='ordered_origin_runs' in plan
    if is_multi:
        assert plan['ordered_origin_runs']==[str(origin) for origin in origins]
    else:
        assert origins==[original], 'Single-source historical reconciler can only reuse original actual runs'
    for index in range(1,198):
        offset=(index-1)*25;packet={'rows':source[offset:offset+25]}
        old_packet={'rows':old[offset:offset+25]};record=records[index]
        changed=old_packet!=packet;failed=old_records[index]['selected_raw'] is None
        changed_ids.extend(z['id'] for a,z in zip(old_packet['rows'],packet['rows']) if a!=z)
        assert record['changed_input']==changed and record['old_execution_failed']==failed
        assert record['old_selection_sha256']==old_records[index]['selection_sha256']
        assert record['old_selection_path']==old_records[index]['selection_path']
        origin,selected=earliest_exact(origins,histories,index,packet,prompt)
        action='reuse_exact_batch' if origin is not None else 'rerun_complete_batch'
        assert record['action']==action
        if origin is None:
            expected_reruns.append(index);origin=run;selected=own_records[index]
            if is_multi:
                assert record['origin_run'] is None and record['origin_selection_path'] is None
                assert record['origin_selection_sha256'] is None
        elif is_multi:
            assert record['origin_run']==str(origin)
            assert record['origin_selection_path']==selected['selection_path']
            assert record['origin_selection_sha256']==selected['selection_sha256']
        assert selected['selected_raw'] is not None
        selected_dir=Path(selected['selected_raw_path']).parent
        assert read(selected_dir/'input.json')==packet
        assert (selected_dir/'request.txt').read_text()==request(prompt,packet)
        if is_multi:
            assert_lineage(lines[index-1],selected,index,action,origin)
        else:
            # Earlier source-only sealer predated the explicit actual_origin_run field.
            line=dict(lines[index-1]);line['actual_origin_run']=str(origin)
            assert_lineage(line,selected,index,action,origin)
        aggregate.extend(selected['selected_raw']['rows']);issues.extend(selected['selected_raw']['issue_records'])
        selected_records.append(selected);origin_counts[str(origin)]+=1
    assert expected_reruns==plan['rerun_batches'] and changed_ids==plan['changed_ids']
    assert summary['new_whole_batches']==len(expected_reruns) and summary['reused_exact_input_batches']==197-len(expected_reruns)
    assert summary['selected_branch_actual_attempt_count']==sum(len(record['attempts']) for record in selected_records)
    assert summary['selected_branch_all_attempt_tool_events']==sum(a['tool_events'] for record in selected_records for a in record['attempts'])
    if is_multi:assert summary['exact_batch_origin_counts']==dict(origin_counts)
    actual=read(run/'all_predictions.json')
    assert actual['execution_version']=='LLM-binary-v32' and actual['rows']==aggregate and actual['issue_records']==issues
    assert jl(run/'all_predictions.jsonl')==aggregate
    assert c.sha(run/'all_predictions.jsonl')==summary['output_sha256']
    return {'selected_records':selected_records,'aggregate':actual,'changed_ids':changed_ids,
            'expected_reruns':expected_reruns,'origin_counts':dict(origin_counts)}


def stripped(record):
    return {key:value for key,value in record.items() if key!='selected_raw'}


def audit_execution(manifest,bindings_sha256,script_path):
    assert manifest['root_final_source_bindings_confirmed'] is True
    assert bound(manifest['source_qa'])['all_checks_pass'] is True
    original_plan=bound(manifest['original_plan'])
    assert original_plan['method_version']=='LLM-binary-v32' and original_plan['prompt_sha256']==FROZEN_PROMPT_SHA
    assert original_plan['batch_size']==25 and original_plan['batch_count']==197 and original_plan['n']==4924
    original=Path(manifest['original_plan']['path']).resolve().parent
    assert Path(manifest['original_plan']['path']).name=='run_plan.json'
    frozen_files(original,original_plan)
    original_input=original/original_plan['frozen_input_relative_path']
    assert c.sha(original_input)==original_plan['input_sha256']
    old=jl(original_input);same_source_identity(old,old)
    assert selection_inventory(original)==list(range(1,198))
    prompt=(original/'frozen_prompt.txt').read_text();assert digest(prompt)==FROZEN_PROMPT_SHA
    validator=validator_module(original/'frozen_validator.py');schema=read(original/'frozen_schema.json')
    origins=[original];histories={};run_descriptors=[]
    histories[str(original)]={index:audit_batch(original,index,{'rows':old[(index-1)*25:index*25]},prompt,
                                               original_plan,validator,schema) for index in range(1,198)}
    run_descriptors.append({'run':str(original),'role':'original_actual_run','actual_batches':list(range(1,198)),
                            'plan':manifest['original_plan']})
    additional=manifest['additional_actual_runs']
    assert isinstance(additional,list)
    declared_extras=[]
    for descriptor in additional:
        run=Path(descriptor['run_directory']).resolve()
        assert run not in origins, 'One actual run must not be repeated under multiple aliases'
        assert Path(descriptor['plan']['path']).resolve()==run/'source_reconciliation_plan.json'
        assert Path(descriptor['execution_summary']['path']).resolve()==run/'execution_summary.json'
        plan=bound(descriptor['plan']);summary=bound(descriptor['execution_summary'])
        source,indices=load_repair_contract(run,plan,original,original_plan,old)
        assert descriptor['actual_batches']==indices
        histories[str(run)]={index:audit_batch(run,index,{'rows':source[(index-1)*25:index*25]},prompt,
                                              original_plan,validator,schema) for index in indices}
        if 'ordered_origin_runs' in plan:
            declared=plan['additional_actual_runs_in_frozen_precedence_order']
            assert declared==declared_extras
        validate_repair_assembly(run,plan,summary,source,origins,histories,prompt,old,original)
        declared_extras.append({'path':str(run),'plan_sha256':descriptor['plan']['sha256'],
                                'summary_sha256':descriptor['execution_summary']['sha256']})
        origins.append(run)
        run_descriptors.append({'run':str(run),'role':'additional_actual_run','actual_batches':indices,
                                'plan':descriptor['plan'],'execution_summary':descriptor['execution_summary']})
    final_plan=bound(manifest['reconciliation_plan']);final_summary=bound(manifest['reconciled_summary'])
    final=Path(manifest['reconciliation_plan']['path']).resolve().parent
    assert final not in origins
    assert Path(manifest['reconciliation_plan']['path']).name=='source_reconciliation_plan.json'
    assert final_plan['ordered_origin_runs']==[str(origin) for origin in origins]
    assert final_plan['additional_actual_runs_in_frozen_precedence_order']==declared_extras
    source,indices=load_repair_contract(final,final_plan,original,original_plan,old)
    final_input=Path(manifest['final_input']['path'])
    assert c.sha(final_input)==manifest['final_input']['sha256']==final_plan['new_input_sha256']
    assert jl(final_input)==source
    assert Path(manifest['reconciled_summary']['path']).resolve()==final/'execution_summary.json'
    assert Path(manifest['batch_lineage']['path']).resolve()==final/'batch_lineage.json'
    assert Path(manifest['aggregate_json']['path']).resolve()==final/'all_predictions.json'
    assert Path(manifest['output_jsonl']['path']).resolve()==final/'all_predictions.jsonl'
    bound(manifest['batch_lineage']);bound(manifest['aggregate_json'])
    assert c.sha(final/'all_predictions.jsonl')==manifest['output_jsonl']['sha256']
    histories[str(final)]={index:audit_batch(final,index,{'rows':source[(index-1)*25:index*25]},prompt,
                                            original_plan,validator,schema) for index in indices}
    replay=validate_repair_assembly(final,final_plan,final_summary,source,origins,histories,prompt,old,original)
    assert not validator.validate({'rows':source},replay['aggregate'])
    jsonschema.Draft202012Validator(schema).validate(replay['aggregate'])
    run_descriptors.append({'run':str(final),'role':'final_actual_repair','actual_batches':indices,
                            'plan':manifest['reconciliation_plan'],'execution_summary':manifest['reconciled_summary']})
    unique_attempts={};history_counts=[]
    for descriptor in run_descriptors:
        records=histories[descriptor['run']];attempts=[a for record in records.values() for a in record['attempts']]
        for attempt in attempts:
            key=attempt['actual_attempt_directory']
            if key in unique_attempts:assert unique_attempts[key]==attempt
            else:unique_attempts[key]=attempt
        history_counts.append({**descriptor,'actual_batch_count':len(records),'actual_attempt_count':len(attempts),
            'accepted_actual_batch_count':sum(record['selected_raw'] is not None for record in records.values()),
            'failed_actual_batches':[index for index,record in records.items() if record['selected_raw'] is None],
            'all_attempt_tool_events':sum(a['tool_events'] for a in attempts),
            'actual_batch_audit':[stripped(record) for record in records.values()]})
    selected=replay['selected_records']
    return {'status':'pass_independent_execution_QA','all_checks_pass':True,
        'created_at':datetime.datetime.now().astimezone().isoformat(),'final_material_version':manifest['final_material_version'],
        'final_output_sha256':manifest['output_jsonl']['sha256'],'n':4924,'batch_count':197,
        'ordered_origin_runs':[str(origin) for origin in origins],
        'exact_batch_origin_counts':replay['origin_counts'],
        'historical_actual_runs':history_counts,
        'all_actual_attempts_including_superseded_count':len(unique_attempts),
        'all_historical_attempt_tool_events':sum(a['tool_events'] for a in unique_attempts.values()),
        'selected_branch_actual_attempt_count':sum(len(record['attempts']) for record in selected),
        'selected_branch_all_attempt_tool_events':sum(a['tool_events'] for record in selected for a in record['attempts']),
        'new_whole_batches':len(indices),'reused_exact_input_batches':197-len(indices),
        'changed_source_input_rows_from_original':len(replay['changed_ids']),
        'all4924_exact_raw_objects_reconstructed':True,'all_five_dimensions_from_actual_v32_row':True,
        'old_three_dimension_outputs_used':False,'v34_used_in_frozen_confirmation':False,
        'reference_labels_or_metrics_read':False,'source_precedence_checked_independently':True,
        'first_valid_selection_checked_independently':True,'actual_attempts_deduplicated_by_resolved_directory':True,
        'source_unchanged_while_QA_ran':c.sha(final_input)==manifest['final_input']['sha256'],
        'final_selected_branch_audit':[stripped(record) for record in selected],
        'bindings':manifest,'binding_manifest_sha256':bindings_sha256,'script_sha256':c.sha(script_path),
        'limits':['Actual input/request/raw/events/first-valid and frozen source precedence verified; semantic correctness not established.',
                  'Requested model and exposed events preserved; provider internal revision not fabricated.',
                  'Complete history counts deduplicate actual attempt directories, separately from final selected provenance branch.']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bindings',type=Path,required=True);parser.add_argument('--bindings-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    assert not args.out.exists() and c.sha(args.bindings)==args.bindings_sha256
    manifest=read(args.bindings)
    qa=audit_execution(manifest,args.bindings_sha256,Path(__file__))
    assert qa['source_unchanged_while_QA_ran']
    c.write_json(args.out,qa)
    print(json.dumps({'status':qa['status'],'n':4924,'new_batches':qa['new_whole_batches'],
        'actual_attempts_all_history':qa['all_actual_attempts_including_superseded_count'],'out':str(args.out)},ensure_ascii=False))


if __name__=='__main__':main()

