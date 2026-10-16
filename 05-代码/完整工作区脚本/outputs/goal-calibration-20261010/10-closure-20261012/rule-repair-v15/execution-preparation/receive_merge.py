"""Receive one full4481 actual execution; zero inherited candidate results.

Compare completed v13b as a traceable research baseline, not adopted gold.
No RelationView/judge, model call, resampling or production adoption occurs.
"""
import argparse,collections,copy,json
from pathlib import Path
from merge_common import bind,cj,exact,load,now,rows,save,seal,sha,spans
from scope_contract import contract,driver_argv,require,validate_full_scope
from receive_boundaries import conditional_s_basis,source_delta,validate_actual_log
import rule_driver

if not __debug__:raise RuntimeError('Run without optimization; exact binding assertions must remain active')
H=Path(__file__).resolve().parent
DIMS=('S','E','Ec','I','F')

def member(raw,key):return raw[slice(*spans(raw)[key])]

def validate_wait(scope_path,scope):
    c=contract();wait=Path(scope['wait_directory'])
    start=load(wait/'supervisor-start.json');child=load(wait/'controller-start.json');terminal=load(wait/'controller-terminal.json')
    argv=driver_argv(scope_path,scope)
    require(start['argv']==child['argv']==argv,'Actual parent waited on a different driver argv')
    require(start['automatic_restart'] is False,'Unexpected supervisor restart')
    p=start['provenance']
    require(p['ROOT_release']==scope['release'] and p['frozen_scope']==bind(scope_path) and p['helper']==c['wait_helper'] and p['supervisor']==bind(H/'actual-first-run-supervisor.py'),'Actual wait provenance differs from current release/scope')
    require(terminal['provenance']=='durable_supervisor_actual_Popen_wait' and terminal['actual_Popen_started'] is True and terminal['actual_wait_returned'] is True and terminal['actual_controller_terminal'] is True,'No true parent wait terminal')
    require(terminal['returncode_status']=='observed_by_parent_wait' and type(terminal['returncode']) is int and terminal['returncode']==0 and terminal['launch_or_supervision_error'] is None,'Actual first process failed or return code unknown')
    require(child['actual_Popen_started'] is True and terminal['controller_pid']==child['controller_pid'],'Actual child identity differs')
    for k in ['stdout','stderr']:exact(terminal[k])
    return {k:bind(wait/k) for k in ['supervisor-start.json','controller-start.json','controller-terminal.json']}

def validate_pair(oldraw,newraw,oldlog,newlog,slots,bundle,modules,protocol,run_id):
    old,new=load_bytes(oldraw),load_bytes(newraw)
    require(old['id']==new['id']==bundle['source_record']['id'],'Prediction/source identity mismatch')
    require(not old['implementation_errors'] and not new['implementation_errors'],'Technical failure is not an accepted decision')
    require(set(new['labels'])==set(new['decisions'])==set(DIMS),'Incomplete five-dimensional record')
    require(new.get('candidate_decisions_diagnostic_only')==new['decisions'],'Actual candidate decision changed after validation')
    for d in DIMS:
        value=new['labels'][d];slot=slots[d]
        require(value is None or type(value) is int and value in (0,1),'Invalid binary/NULL value')
        require(value==new['decisions'][d]['value'],'Label/decision mismatch')
        require(slot['id']==new['id'] and slot['dimension']==d,'Slot identity mismatch')
        require(not slot['technical_failure'] and not slot['record_implementation_errors'] and not slot['global_implementation_errors'],'Failed slot cannot be received')
        require(slot['rule_value']==value and slot['retained_rule_decision']==new['decisions'][d],'Slot/decision mismatch')
        require(slot['rules_null']==(value is None) and slot['status']==('source_dependency_unresolved' if value is None else 'retained_rule_decision'),'Lawful NULL and technical failure were interchanged')
    require(old['decisions']['I']==new['decisions']['I'] and member(member(oldraw,'decisions'),'I')==member(member(newraw,'decisions'),'I'),'Immutable complete I decision/token changed')
    if old['decisions']['S']==new['decisions']['S']:
        require(member(member(oldraw,'decisions'),'S')==member(member(newraw,'decisions'),'S'),'Unchanged S token altered')
        sbasis=None
    else:sbasis=conditional_s_basis(old,new,bundle,modules)
    validate_actual_log(rule_driver,protocol,modules,bundle,new,newlog,run_id)
    delta=source_delta(old,new,oldlog,newlog,modules,new['decisions'])
    return {'label_changes':[d for d in DIMS if old['labels'][d]!=new['labels'][d]],
      'decision_changes':[d for d in DIMS if old['decisions'][d]!=new['decisions'][d]],
      'relation_trace_changed':old.get('relation_traces')!=new.get('relation_traces'),
      'conditional_S_change_basis':sbasis,'source_delta':delta}

def load_bytes(raw):
    from interface_common import parse_json
    return parse_json(raw)

def receive(scope_path,delta_path,output_path,validate_only=False):
    c=contract();scope=load(scope_path);validate_full_scope(scope);release=load(scope['release']['path'])
    run=Path(delta_path).resolve();out=Path(output_path).resolve();parent=Path(c['comparison_baseline_directory'])
    require(str(run)==scope['output_directory'] and str(out)==scope['received_directory'],'Run/received directory outside exact release')
    require(validate_only or not out.exists(),'Never overwrite a prior receipt')
    wait=validate_wait(scope_path,scope)
    ds=seal(run/'seal.json');execution=load(run/'execution.json');freeze=load(run/'freeze.json')
    require(ds['status']=='sealed_complete_production_provisional_rule_full4481_run' and execution['status']=='completed','Not a completed actual first full run')
    require(execution['actual_record_N']==4481 and execution['actual_dimension_N']==22405 and execution['retained_decision_N']==22405,'Actual full coverage differs')
    require(execution['technical_failure_dimension_N']==0 and not execution['implementation_errors'] and execution['actual_cohort_inference_runs']==1 and execution['no_reference_read'] is True,'Failed/repeated/reference-reading run cannot be received')
    require(ds['control_inputs']==freeze['control_inputs']==[bind(scope_path)] and freeze['source_scope']==scope,'Actual first run scope differs')
    require(freeze['fixed_algorithm_version']==scope['candidate_algorithm_version'] and freeze['semantic_change']==scope['semantic_change'],'Actual algorithm/semantic declaration differs')
    require(freeze['implementation_files']==ds['implementation_files']==release['implementation_bindings'],'Actual implementation differs from ROOT release')
    require(ds['material_bindings']==freeze['material_bindings']==scope['material_bindings'],'Actual frozen material bindings differ')
    baseline=load(c['comparison_baseline_bindings']['path']);exact(baseline['parent_seal'])
    ps=seal(baseline['parent_seal']['path']);require(ps['files']==baseline['parent_files'],'Comparison baseline seal differs')
    logbindings={}
    for pair in baseline['actual_origin_source_logs']:
        exact(pair['actual_run_seal']);s=load(pair['actual_run_seal']['path']);exact(pair['log'])
        require(pair['log'] in s.get('output_files',[])+s.get('files',[]),'Historical log is not bound by its actual run seal')
        logbindings[pair['log']['path']]=pair['log']
    old=rows(parent/'predictions.jsonl');new=rows(run/'predictions.jsonl');origins=rows(parent/'execution-origin-lineage.jsonl')
    slots=rows(run/'all-dimension-slots.jsonl',('id','dimension'));logs=rows(run/'actual-source-consumption.jsonl')
    units=rows(run/'effective-semantic-units.jsonl');deliveries=rows(run/'input-deliveries.jsonl','source_id');ledger=rows(run/'execution-ledger.jsonl')
    ids=scope['approved_record_ids']
    require(list(old)==list(new)==list(origins)==list(logs)==list(units)==list(deliveries)==list(ledger)==ids and len(ids)==4481,'Full actual ID coverage/order differs')
    require(set(slots)=={(rid,d) for rid in ids for d in DIMS},'Actual22405 slot coverage differs')
    lines=Path(scope['source_packet']['path']).read_bytes().splitlines(keepends=True)
    bundles=[load_bytes(x) for x in lines]
    actual=[load_bytes(x) for x in (run/'delivered-complete-source-bundles.jsonl').read_bytes().splitlines()]
    require(len(actual)==len(bundles)==4481 and actual==bundles,'Actual delivered v17 frame differs')
    # Frozen modules supply source identity/decision validators only. No view
    # construction, judge, candidate search or new classification is invoked.
    code=release['implementation_bindings'];modules=rule_driver.load_frozen_coders(H,code)
    materials=scope['material_bindings']
    for b in materials:exact(b)
    require(rule_driver.literal_leaf_integrity(bundles,materials)==execution['literal_primary_leaf_integrity_checks'],'Actual literal leaf integrity differs')
    protocol=rule_driver.finite_protocol(modules['source_packet'],bundles,materials,scope)
    packet_plan=load(scope['packet_bindings']['path']);cache={};changes=[];source_changes=[];lineage=[];counts={d:collections.Counter() for d in DIMS};cursor=0
    for ordinal,(rid,bundle,line) in enumerate(zip(ids,bundles,lines),1):
        delivery=deliveries[rid][2];packet=packet_plan['packets'][ordinal-1]
        require(bundle['source_record']['id']==rid and delivery['source_id']==rid,'Actual source ID differs')
        require(delivery['input_line_sha256']==sha(line) and delivery['source_bundle_sha256']==sha(cj(bundle).encode()) and delivery['actual_packet_binding']==packet,'Actual original input/packet identity differs')
        require(delivery['input_line_1based']==ordinal and delivery['input_start_utf8_byte']==cursor and delivery['input_end_utf8_byte_exclusive']==cursor+len(line),'Actual source byte span differs');cursor+=len(line)
        led=ledger[rid][2];require(led['index_1based']==ordinal and led['one_adapter_view_judge_attempt_only'] is True and not led['technical_failure'] and led['labels']==new[rid][2]['labels'],'Actual one-attempt record ledger differs')
        unit=modules['source_packet'].semantic_unit(bundle)
        require(unit==units[rid][2]['semantic_unit'] and 'id' not in unit,'Stored semantic projection differs from actual material')
        modules['evidence'].validate_decisions(unit,new[rid][2]['decisions'])
        prior=origins[rid][2];require(prior['corpus_ordinal_1based']==ordinal and prior['actual_prediction_line_sha256']==sha(old[rid][1]) and prior['prediction_line_bytes']==len(old[rid][1]),'Original baseline lineage differs')
        path=prior['source_consumption_log'];require(path in logbindings,'Original baseline source log lacks actual sealed identity')
        if path not in cache:cache[path]=rows(path)
        check=validate_pair(old[rid][1],new[rid][1],cache[path][rid][2],logs[rid][2],{d:slots[rid,d][2] for d in DIMS},bundle,modules,protocol,run.name)
        if any(check[k] for k in ['label_changes','decision_changes','relation_trace_changed']):changes.append({'id':rid,**{k:v for k,v in check.items() if k!='source_delta'}})
        if any(check['source_delta'].values()):source_changes.append({'id':rid,**check['source_delta']})
        for d in DIMS:counts[d]['positive_N' if new[rid][2]['labels'][d]==1 else 'negative_N' if new[rid][2]['labels'][d]==0 else 'lawful_null_N']+=1
        lineage.append({'id':rid,'corpus_ordinal_1based':ordinal,'actual_inference_algorithm':scope['candidate_algorithm_version'],
          'actual_run_directory':str(run),'source_consumption_log':str(run/'actual-source-consumption.jsonl'),'source_consumption_record_key':rid,
          'actual_prediction_line_sha256':sha(new[rid][1]),'prediction_line_bytes':len(new[rid][1]),
          'unchanged_actual_record_bytes_retained':True,'inherited_from_baseline':False,
          'comparison_baseline_origin':prior,'comparison_baseline_line_sha256':sha(origins[rid][1])})
    null_N=sum(x['lawful_null_N'] for x in counts.values());require(null_N==execution['lawful_null_N']==ds['lawful_null_N'],'Actual NULL counts differ')
    # Recheck original bytes before any received copy is made; a later file
    # change cannot be accepted merely because parsing happened earlier.
    require(seal(run/'seal.json')==ds,'Actual run seal changed during reception')
    for b in release['implementation_bindings']:exact(b)
    for b in baseline['parent_files']:exact(b)
    for b in logbindings.values():exact(b)
    exact(scope['source_packet']);exact(scope['release'])
    result={'status':'validated_complete_full4481_v17_not_adopted','actual_new_inference_record_N':4481,'dimension_N':22405,'inherited_N':0,
      'immutable_I_complete_decision_tokens_equal':True,'conditional_S_boundary_passed':True,
      'old_source_sequences_preserved_new_deltas_protocol_verified':True,'changed_record_N':len(changes),'source_delta_record_N':len(source_changes),
      'new_inference_by_receiver':False,'lawful_null_N':null_N}
    if validate_only:return result
    out.mkdir(parents=True,exist_ok=False)
    for name in ['predictions.jsonl','all-dimension-slots.jsonl']:
        with (out/name).open('xb') as f:f.write((run/name).read_bytes())
    with (out/'execution-origin-lineage.jsonl').open('x') as f:
        for row in lineage:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    save(out/'comparison-baseline-to-candidate-actual-changes.json',{'changes':changes,'globally_immutable_dimensions':['I'],'conditional_S_contract':scope['conditional_S_contract']})
    save(out/'actual-source-deltas.json',{'deltas':source_changes,'old_sequences_preserved':True,'new_events_are_original_protocol_verified_actual_events':True})
    status={**result,'at_utc':now(),'candidate_algorithm_version':scope['candidate_algorithm_version'],
      'actual_record_N':4481,'actual_dimension_N':22405,'technical_failure_dimension_N':0,'unresolved_technical_dimension_N':0,
      'counts':{d:dict(counts[d]) for d in DIMS},'actual_execution_algorithm_record_N':{scope['candidate_algorithm_version']:4481},
      'all4481_actually_inferred_under_candidate':True,'inherited_compatible_parent_record_N':0,
      'source_common_v17':scope['source_packet'],'material_changed_record_ids':scope['material_changed_record_ids'],
      'comparison_baseline_seal':baseline['parent_seal'],'actual_run_seal':bind(run/'seal.json'),'actual_parent_wait':wait,
      'current_scope':bind(scope_path),'release':scope['release'],'receiver':bind(__file__),
      'prediction_binding':bind(out/'predictions.jsonl'),'label_slots_binding':bind(out/'all-dimension-slots.jsonl'),
      'predictions_path':str(out/'predictions.jsonl'),'label_slots_path':str(out/'all-dimension-slots.jsonl'),
      'formal_validation_complete':False,'human_validation_complete':False,'production_adopted':False,'paper_writing_gate_open':False}
    save(out/'composite-status.json',status)
    save(out/'seal.json',{'status':status['status'],'files':[bind(p) for p in sorted(out.iterdir()) if p.is_file()],
       'ancestor_seals':[baseline['parent_seal'],bind(run/'seal.json')],'self_excluded':True,'no_new_inference_executed_by_merge':True,'formal_validation_complete':False})
    return dict(result,output=str(out))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--scope',required=True);p.add_argument('--delta',required=True);p.add_argument('--output',required=True);p.add_argument('--validate-only',action='store_true');a=p.parse_args()
    print(json.dumps(receive(a.scope,a.delta,a.output,a.validate_only),ensure_ascii=False))
