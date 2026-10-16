"""Independent QA for partial-history reuse and explicit technical prompt suffix.

No reference labels or semantic metrics are opened. Every actual attempt is
validated by the existing independent event/literal auditor. Prompt and CLI
differences are bound explicitly, never represented as byte-identical runs.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import argparse
import datetime
import json
import jsonschema
import statistical_core_r3 as c
import audit_reconciled_execution_multi_r3 as a

BASE=a.FROZEN_PROMPT_SHA
TECH='citation-isolation-tech01'


def bound(x):return a.bound(x)
def bd(path):return {'path':str(Path(path).resolve()),'sha256':c.sha(path)}


def inspect_contract(run,plan,original,original_plan,old):
    assert Path(plan['original_run']).resolve()==original
    assert plan['original_plan_sha256']==c.sha(original/'run_plan.json')
    assert plan['prompt_sha256']==BASE
    assert plan['model']==original_plan['model'] and plan['reasoning_effort']==original_plan['reasoning_effort']
    assert (plan['n'],plan['batch_size'],plan['batch_count'])==(4924,25,197)
    assert plan['selection_rule']==original_plan['selection_rule']
    assert plan['max_attempts']==original_plan['max_attempts']
    assert plan['labels_or_metrics_read'] is False and plan['source_order_and_unit_text_unchanged'] is True
    a.frozen_files(run,original_plan)
    assert c.sha(run/'frozen_input.jsonl')==plan['new_input_sha256']
    if 'reconciler_sha256' in plan:
        # Earlier v13 run did not copy the reconciler into its run directory;
        # its exact plan-bound source still exists at the historical path.
        reconciler=run/'frozen_reconciler.py'
        if not reconciler.exists():
            assert not plan.get('technical_batches') and 'ordered_origin_runs' not in plan
            reconciler=run.parent/'reconcile_source_only_batches.py'
        assert c.sha(reconciler)==plan['reconciler_sha256']
    source=a.jl(run/'frozen_input.jsonl');a.same_source_identity(old,source)
    indices=a.selection_inventory(run)
    assert indices==plan['rerun_batches']==sorted(set(indices))
    assert all(1<=index<=197 for index in indices)
    records={r['batch']:r for r in plan['batch_records']}
    assert len(records)==len(plan['batch_records'])==197 and set(records)==set(range(1,198))
    technical=plan.get('technical_batches',[])
    assert technical==sorted(set(technical)) and all(1<=index<=197 for index in technical)
    base_prompt=(run/'frozen_prompt.txt').read_text()
    if technical:
        assert plan['technical_version']==TECH and plan['technical_retry_limit']==3
        appendix=(run/'technical_format_clarification.txt').read_text()
        assert c.sha(run/'technical_format_clarification.txt')==plan['technical_appendix_sha256']
        assert (run/'frozen_technical_prompt.txt').read_text()==base_prompt+appendix
        assert c.sha(run/'frozen_technical_prompt.txt')==plan['technical_prompt_sha256']
    else:appendix=''
    runtime=plan.get('execution_runtime')
    if runtime:
        assert a.read(run/'execution_runtime_binding.json')==runtime
        assert runtime['reported_cli_version'] and len(runtime['actual_executable_sha256'])==64
        assert plan['original_cli_reported_version']==original_plan['cli_version']
        assert plan['cli_reported_version_changed']==(runtime['reported_cli_version']!=original_plan['cli_version'])
        assert plan['original_inner_executable_sha256'] is None
    requests={};batch_prompts={}
    for index,record in records.items():
        prompt=base_prompt+appendix if index in technical else base_prompt
        packet={'rows':source[(index-1)*25:index*25]}
        request=a.request(prompt,packet)
        if 'effective_prompt_sha256' in record:
            assert record['effective_prompt_sha256']==a.digest(prompt)
            assert record['expected_request_sha256']==a.digest(request)
            assert record['technical_version']==(TECH if index in technical else None)
            assert record['max_attempts']==(3 if index in technical else original_plan['max_attempts'])
        requests[index]=request;batch_prompts[index]=prompt
    return source,indices,records,batch_prompts,requests,runtime


def audit_actual_batches(run,plan,original_plan,contract,validator,schema):
    source,indices,records,prompts,requests,runtime=contract
    audited={}
    for index in indices:
        selection=a.read(run/'batches'/f'batch-{index:04d}'/'selection.json')
        for attempt in selection['attempts']:
            assert (run/attempt['relative_path']).resolve().is_relative_to(run.resolve())
        expected=deepcopy(original_plan)
        expected['prompt_sha256']=a.digest(prompts[index])
        expected['max_attempts']=records[index].get('max_attempts',original_plan['max_attempts'])
        if runtime:
            expected['cli_version']=runtime['reported_cli_version']
            expected['cli_binary_sha256']=runtime['launcher_sha256']
        audited[index]=a.audit_batch(run,index,{'rows':source[(index-1)*25:index*25]},prompts[index],expected,validator,schema)
    return audited


def earliest_exact(origins,histories,index,packet,request,prompt_sha):
    for origin in origins:
        record=histories[str(origin)].get(index)
        if record is None or record['selected_raw'] is None:continue
        actual=Path(record['selected_raw_path']).parent
        if a.read(actual/'input.json')!=packet:continue
        if (actual/'request.txt').read_text()!=request:continue
        if a.read(actual/'run_metadata.json')['prompt_sha256']!=prompt_sha:continue
        return origin,record
    return None,None


def assembly(run,plan,summary,contract,origins,histories,old,original):
    source,indices,records,prompts,requests,runtime=contract
    assert plan.get('ordered_origin_runs',[str(original)])==[str(p) for p in origins]
    assert summary['status']==a.COMPLETE_STATUS
    assert summary['old_three_dimension_outputs_used'] is False and summary['reference_label_or_metric_selection'] is False
    assert summary['new_input_sha256']==plan['new_input_sha256']
    assert summary['prompt_sha256']==BASE and summary['n']==4924 and summary['batch_count']==197
    lines=a.read(run/'batch_lineage.json');assert len(lines)==197
    assert c.sha(run/'batch_lineage.json')==summary['lineage_sha256']
    has_rows=(run/'row_provenance.jsonl').exists()
    if has_rows:assert c.sha(run/'row_provenance.jsonl')==summary['row_provenance_sha256']
    aggregate=[];issues=[];provenance=[];selected=[];reruns=[];changed=[];origins_count=Counter()
    for index in range(1,198):
        packet={'rows':source[(index-1)*25:index*25]};old_packet={'rows':old[(index-1)*25:index*25]}
        rec=records[index];line=lines[index-1]
        assert rec['changed_input']==(packet!=old_packet)
        assert rec['old_execution_failed']==(histories[str(original)][index]['selected_raw'] is None)
        assert rec['old_selection_sha256']==histories[str(original)][index]['selection_sha256']
        assert rec['old_selection_path']==histories[str(original)][index]['selection_path']
        changed.extend(z['id'] for x,z in zip(old_packet['rows'],packet['rows']) if x!=z)
        origin,actual=earliest_exact(origins,histories,index,packet,requests[index],a.digest(prompts[index]))
        action='reuse_exact_batch' if origin else 'rerun_complete_batch'
        assert rec['action']==action
        if origin is None:
            reruns.append(index);origin=run;actual=histories[str(run)][index]
            if 'origin_run' in rec:assert rec['origin_run'] is None and rec['origin_selection_path'] is None and rec['origin_selection_sha256'] is None
        elif 'origin_run' in rec:
            assert rec['origin_run']==str(origin)
            assert rec['origin_selection_path']==actual['selection_path'] and rec['origin_selection_sha256']==actual['selection_sha256']
        assert actual['selected_raw'] is not None
        a.assert_lineage(line,actual,index,action,origin)
        selected_dir=Path(actual['selected_raw_path']).parent;meta=a.read(selected_dir/'run_metadata.json')
        assert a.read(selected_dir/'input.json')==packet
        assert (selected_dir/'request.txt').read_text()==requests[index]
        if has_rows:
            assert line['base_semantic_prompt_sha256']==BASE
            assert line['actual_prompt_sha256']==a.digest(prompts[index])==meta['prompt_sha256']
            assert line['actual_request_sha256']==a.digest(requests[index])==meta['request_sha256']
            assert line['technical_version']==rec.get('technical_version')
            runtime_path=origin/'execution_runtime_binding.json'
            actual_runtime=a.read(runtime_path) if runtime_path.exists() else {
                'reported_cli_version':meta['cli_version'],'launcher_sha256':meta['cli_binary_sha256'],
                'actual_executable_sha256':None,'unavailable_reason':'historical run hashed launcher only'}
            assert line['execution_runtime']==actual_runtime
            assert actual_runtime['reported_cli_version']==meta['cli_version']
            assert actual_runtime['launcher_sha256']==meta['cli_binary_sha256']
            provenance.extend({'id':row['id'],**line} for row in actual['selected_raw']['rows'])
        aggregate.extend(actual['selected_raw']['rows']);issues.extend(actual['selected_raw']['issue_records'])
        selected.append(actual);origins_count[str(origin)]+=1
    assert reruns==indices and changed==plan['changed_ids']
    assert summary['new_whole_batches']==len(indices) and summary['reused_exact_input_batches']==197-len(indices)
    assert summary['exact_batch_origin_counts']==dict(origins_count)
    assert summary['selected_branch_actual_attempt_count']==sum(len(x['attempts']) for x in selected)
    assert summary['selected_branch_all_attempt_tool_events']==sum(z['tool_events'] for x in selected for z in x['attempts'])
    output=a.read(run/'all_predictions.json')
    assert output['rows']==aggregate and output['issue_records']==issues and output['execution_version']=='LLM-binary-v32'
    assert a.jl(run/'all_predictions.jsonl')==aggregate
    assert c.sha(run/'all_predictions.jsonl')==summary['output_sha256']
    if has_rows:
        assert a.jl(run/'row_provenance.jsonl')==provenance
        prompt_counts=dict(Counter(x['actual_prompt_sha256'] for x in provenance))
        cli_counts=dict(Counter(x['execution_runtime']['reported_cli_version'] for x in provenance))
        assert summary['actual_prompt_sha256_counts']==prompt_counts
        assert summary['actual_cli_version_counts']==cli_counts
        assert summary['all_actual_prompts_byte_identical']==(len(prompt_counts)==1)
    return {'aggregate':output,'selected':selected,'provenance':provenance,'origin_counts':dict(origins_count),'changed':changed}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bindings',type=Path,required=True)
    parser.add_argument('--bindings-sha256',required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();assert not args.out.exists()
    assert c.sha(args.bindings)==args.bindings_sha256
    m=c.read(args.bindings);assert m['root_final_source_bindings_confirmed'] is True
    assert bound(m['source_qa'])['all_checks_pass'] is True
    op=bound(m['original_plan']);original=Path(m['original_plan']['path']).resolve().parent
    assert op['method_version']=='LLM-binary-v32' and op['prompt_sha256']==BASE
    a.frozen_files(original,op);old=a.jl(original/op['frozen_input_relative_path'])
    assert c.sha(original/op['frozen_input_relative_path'])==op['input_sha256']
    assert a.selection_inventory(original)==list(range(1,198))
    validator=a.validator_module(original/'frozen_validator.py');schema=a.read(original/'frozen_schema.json')
    prompt=(original/'frozen_prompt.txt').read_text()
    histories={str(original):{i:a.audit_batch(original,i,{'rows':old[(i-1)*25:i*25]},prompt,op,validator,schema) for i in range(1,198)}}
    origins=[original];inventory=[{'run':str(original),'role':'original_actual_run','sealed':False,'binding':m['original_plan']}]
    descriptors=m['additional_actual_runs']+[{'run_directory':str(Path(m['reconciliation_plan']['path']).resolve().parent),
        'plan':m['reconciliation_plan'],'execution_summary':m['reconciled_summary'],'final':True}]
    for desc in descriptors:
        run=Path(desc['run_directory']).resolve();assert run not in origins
        plan=bound(desc['plan']);assert Path(desc['plan']['path']).resolve()==run/'source_reconciliation_plan.json'
        contract=inspect_contract(run,plan,original,op,old)
        histories[str(run)]=audit_actual_batches(run,plan,op,contract,validator,schema)
        declared=plan.get('additional_actual_runs_in_frozen_precedence_order',[])
        assert [x['path'] for x in declared]==[str(p) for p in origins[1:]]
        for frozen,past in zip(declared,descriptors):
            assert frozen['plan_sha256']==past['plan']['sha256']
            if 'actual_selection_records' in frozen:
                for spec in frozen['actual_selection_records']:
                    row=histories[frozen['path']][spec['batch']]
                    assert c.sha(spec['path'])==spec['sha256']==row['selection_sha256']
                    assert a.read(spec['path'])['status']==spec['status']
                assert sorted(x['batch'] for x in frozen['actual_selection_records'])==sorted(histories[frozen['path']])
        sealed=bool(desc.get('execution_summary'))
        if sealed:
            summary=bound(desc['execution_summary'])
            replay=assembly(run,plan,summary,contract,origins,histories,old,original)
        else:
            assert not (run/'execution_summary.json').exists(), 'Partial run cannot conceal a present summary'
            assert desc.get('status')=='partial_actual_attempts_only_not_sealed'
        inventory.append({'run':str(run),'role':'final_actual_repair' if desc.get('final') else 'additional_actual_run',
            'sealed':sealed,'binding':desc['plan'],'summary_binding':desc.get('execution_summary'),
            'runtime_binding':bd(run/'execution_runtime_binding.json') if (run/'execution_runtime_binding.json').exists() else None})
        origins.append(run)
    final=origins[-1]
    assert c.sha(m['final_input']['path'])==m['final_input']['sha256']==plan['new_input_sha256']
    assert a.jl(m['final_input']['path'])==contract[0]
    for key,name in [('batch_lineage','batch_lineage.json'),('aggregate_json','all_predictions.json'),
                     ('output_jsonl','all_predictions.jsonl'),('row_provenance','row_provenance.jsonl')]:
        assert Path(m[key]['path']).resolve()==final/name and c.sha(final/name)==m[key]['sha256']
    assert not validator.validate({'rows':contract[0]},replay['aggregate'])
    jsonschema.Draft202012Validator(schema).validate(replay['aggregate'])
    attempts={};history=[]
    for entry in inventory:
        rows=histories[entry['run']]
        run_attempts=[x for r in rows.values() for x in r['attempts']]
        for x in run_attempts:
            key=x['actual_attempt_directory'];assert key not in attempts;attempts[key]=x
        history.append({**entry,'actual_batch_count':len(rows),'actual_attempt_count':len(run_attempts),
            'failed_actual_batches':[i for i,r in rows.items() if r['selected_raw'] is None],
            'accepted_actual_batch_count':sum(r['selected_raw'] is not None for r in rows.values()),
            'actual_batch_audit':[a.stripped(r) for r in rows.values()]})
    result={'status':'pass_independent_execution_QA','all_checks_pass':True,
        'created_at':datetime.datetime.now().astimezone().isoformat(),'final_material_version':m['final_material_version'],
        'final_output_sha256':m['output_jsonl']['sha256'],'n':4924,'batch_count':197,
        'all4924_exact_raw_objects_reconstructed':True,'all_five_dimensions_from_actual_v32_row':True,
        'all_actual_attempts_including_superseded_count':len(attempts),
        'all_historical_attempt_tool_events':sum(x['tool_events'] for x in attempts.values()),
        'selected_branch_actual_attempt_count':sum(len(r['attempts']) for r in replay['selected']),
        'selected_branch_all_attempt_tool_events':sum(x['tool_events'] for r in replay['selected'] for x in r['attempts']),
        'new_whole_batches':len(contract[1]),'reused_exact_input_batches':197-len(contract[1]),
        'exact_batch_origin_counts':replay['origin_counts'],'historical_actual_runs':history,
        'base_semantic_prompt_sha256':BASE,'actual_prompt_sha256_counts':summary['actual_prompt_sha256_counts'],
        'actual_cli_version_counts':summary['actual_cli_version_counts'],
        'all_actual_prompts_byte_identical':summary['all_actual_prompts_byte_identical'],
        'technical_version':summary['technical_version'],'technical_batches':summary['technical_batches'],
        'row_provenance_bound_and_reconstructed':True,'original_inner_executable_sha256_available':False,
        'old_three_dimension_outputs_used':False,'reference_labels_or_metrics_read':False,
        'first_valid_selection_checked_independently':True,'source_precedence_checked_independently':True,
        'partial_historical_runs_not_misrepresented_as_complete':True,
        'bindings':m,'binding_manifest_sha256':args.bindings_sha256,'script_sha256':c.sha(Path(__file__)),
        'independent_attempt_auditor_sha256':c.sha(Path(a.__file__)),
        'limits':['Actual literal/event/first-valid provenance is not semantic correctness.',
            'Technical suffix creates a different actual prompt; provider internal model revision is unknown.',
            'CLI version changed; original historical SHA bound only its launcher, not the inner executable.',
            'Statistics agent had reference access elsewhere; this audit script reads no reference labels or metrics.']}
    assert c.sha(m['final_input']['path'])==m['final_input']['sha256']
    c.write_json(args.out,result)
    print(json.dumps({k:result[k] for k in ('status','n','all_actual_attempts_including_superseded_count',
        'new_whole_batches','actual_prompt_sha256_counts','actual_cli_version_counts')},ensure_ascii=False))


if __name__=='__main__':main()
