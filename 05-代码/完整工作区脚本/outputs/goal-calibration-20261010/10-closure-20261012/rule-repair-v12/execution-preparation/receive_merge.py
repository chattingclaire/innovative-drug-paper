"""Receive one completed v12 S/F delta and preserve the compatible parent bytes.

Reuses existing prediction/slot/source-log/lineage/seal formats and byte helpers.
No classifier, model, accuracy scoring, or human reference is invoked.
"""
import argparse
import collections
import json
from pathlib import Path
from merge_common import bind, cj, exact, load, now, rows, save, seal, sha, spans
import rule_driver

if not __debug__:
    raise RuntimeError('Run without Python optimization; existing binding assertions remain active')
H=Path(__file__).resolve().parent
DIMS=('S','E','Ec','I','F')
FIXED=('E','Ec','I')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def member(raw, key):
    return raw[slice(*spans(raw)[key])]


def recorded_events(record):
    if 'actual_text_geometry_events' in record:
        return record['actual_text_geometry_events']
    if record.get('primary_source_audit_origin', {}).get('source_view_events') == 'live_view':
        events = record['source_view_events']
        require(events == record['live_view_source_audit']['source_view_events'], 'Historical live source event snapshot differs')
        return events
    raise ValueError('No actual stored source event group; metadata cannot fill it')


def validate_pair(old_raw, new_raw, old_log, new_log, slots):
    old, new = json.loads(old_raw), json.loads(new_raw)
    require(old['id'] == new['id'], 'Prediction ID mismatch')
    require(not old['implementation_errors'] and not new['implementation_errors'], 'Technical failure is not an accepted decision')
    require(set(new['labels']) == set(new['decisions']) == set(DIMS), 'Incomplete new five-dimensional record')
    require(new.get('candidate_decisions_diagnostic_only') == new['decisions'], 'Validated original candidate and retained decision differ')
    for dim in DIMS:
        value = new['labels'][dim]
        require(value is None or type(value) is int and value in (0,1), 'Invalid label type')
        require(value == new['decisions'][dim]['value'], 'Label/complete decision mismatch')
        slot = slots[dim]
        require(slot['id'] == new['id'] and slot['dimension'] == dim, 'Slot identity mismatch')
        require(not slot['technical_failure'] and not slot['record_implementation_errors'] and not slot['global_implementation_errors'], 'Failed slot cannot be merged')
        require(slot['rule_value'] == value and slot['retained_rule_decision'] == new['decisions'][dim], 'Slot changed decision')
        require(slot['rules_null'] == (value is None), 'NULL and technical failure were interchanged')
        require(slot['status'] == ('source_dependency_unresolved' if value is None else 'retained_rule_decision'), 'Slot status inconsistent')
        if dim in FIXED:
            require(old['decisions'][dim] == new['decisions'][dim], 'Immutable complete decision changed: ' + dim)
            require(member(member(old_raw,'decisions'),dim) == member(member(new_raw,'decisions'),dim), 'Immutable decision JSON token changed: ' + dim)
    for key in ('source_requests','material_requests'):
        require(key in old and key in new and old[key] == new[key], 'Original source request changed: ' + key)
        require(new_log.get(key) == new[key], 'New source log/request mismatch: ' + key)
    require(recorded_events(old_log) == recorded_events(new_log), 'Original source event group changed')
    check = new_log['uniform_source_protocol_check']
    require(not check['errors'], 'Actual new protocol check failed')
    require(not set(check['dependency_stop_reasons']) & {'required_view_not_read','scope_boundary_unknown','read_delivery_incomplete'}, 'Actual necessary source was not consumed')
    # Run IDs, receipt IDs, source identity extensions and historical recovery
    # annotations are provenance, not semantic fields to force byte equality.
    return {'label_changes': [d for d in DIMS if old['labels'][d] != new['labels'][d]],
            'decision_changes': [d for d in DIMS if old['decisions'][d] != new['decisions'][d]],
            'relation_trace_changed': old.get('relation_traces') != new.get('relation_traces')}


def receive(scope_path, delta_path, output_path, validate_only=False):
    contract = load(H/'execution-contract.json')
    for entry in contract['upstream_bindings'].values(): exact(entry)
    exact(contract['selection']);exact(contract['subset_source'])
    selection = load(contract['selection']['path']);scope=load(scope_path)
    rule_driver.validate_sf_scope(scope)
    exact(scope['release']);release=load(scope['release']['path'])
    require(scope['status']=='frozen_for_execution' and release['status']=='released_for_production_provisional', 'No actual existing-format release')
    require(scope['authorization_id'] and scope['authorization_id']==release['authorization_id'], 'Release authorization mismatch')
    delta=Path(delta_path).resolve();out=Path(output_path).resolve();parent=Path(contract['parent_composite'])
    require(str(delta)==scope['output_directory']==release['output_directory'], 'Delta outside released output')
    require(validate_only or not out.exists(), 'Never overwrite a result')
    ds=seal(delta/'seal.json');execution=load(delta/'execution.json');freeze=load(delta/'freeze.json')
    require(ds['status']=='sealed_complete_production_provisional_rule_delta_run' and execution['status']=='completed', 'Delta is not a complete terminal success')
    require(execution['actual_record_N']==2082 and execution['actual_dimension_N']==10410 and execution['retained_decision_N']==10410, 'Delta coverage differs')
    require(execution['technical_failure_dimension_N']==0 and not execution['implementation_errors'] and execution['actual_cohort_inference_runs']==1 and execution['no_reference_read'] is True, 'Failed or repeated delta cannot be merged')
    require(ds['control_inputs']==freeze['control_inputs']==[bind(scope_path)], 'Actual first run did not bind supplied scope')
    require(freeze['fixed_algorithm_version']==contract['candidate_version'] and freeze['source_scope']==scope, 'Actual first freeze differs')
    require(freeze['implementation_files']==ds['implementation_files']==release['implementation_bindings'], 'Actual implementation differs from external release')
    require(release['execution_contract']==scope['execution_contract']==bind(H/'execution-contract.json') and release['static_impact_selection']==contract['selection'], 'Release changed exact current candidate')
    require(release['allowed_mutable_dimensions']==['S','F'] and release['immutable_dimensions']==list(FIXED), 'Release mutable boundary changed')
    for key,rkey in [('manual','manual'),('prompt','prompt'),('protocol','protocol'),('source_packet','source_input')]:
        require(scope[key]==release[rkey], 'Released material differs: '+key)
    old=rows(parent/'predictions.jsonl');new=rows(delta/'predictions.jsonl')
    oldslots=rows(parent/'all-dimension-slots.jsonl',('id','dimension'));newslots=rows(delta/'all-dimension-slots.jsonl',('id','dimension'))
    origins=rows(parent/'execution-origin-lineage.jsonl');newlogs=rows(delta/'actual-source-consumption.jsonl')
    units=rows(delta/'effective-semantic-units.jsonl');deliveries=rows(delta/'input-deliveries.jsonl','source_id')
    require(list(new)==list(newlogs)==list(units)==list(deliveries)==scope['approved_record_ids']==selection['selected_record_ids'], 'Delta ID coverage/order differs')
    require(len(old)==len(origins)==4481 and list(old)==list(origins) and len(oldslots)==22405, 'Current complete parent missing/duplicated')
    require(set(newslots)=={(rid,d) for rid in new for d in DIMS} and set(oldslots)=={(rid,d) for rid in old for d in DIMS}, 'Complete slot coverage differs')
    source=Path(contract['subset_source']['path']).read_bytes().splitlines(keepends=True)
    actual=[json.loads(x) for x in (delta/'delivered-complete-source-bundles.jsonl').read_bytes().splitlines()]
    require(len(actual)==len(source)==2082, 'Actual delivery count differs')
    packet_plan=load(H/'packet-bindings.json');cache={};changes=[]
    frozen_parent=load(contract['upstream_bindings']['current_machine_freeze']['path'])
    parent_file_bindings={x['path']:x for x in frozen_parent['file_bindings']}
    for index,(rid,(_,newraw,newrow)) in enumerate(new.items()):
        bundle=json.loads(source[index]);delivery=deliveries[rid][2]
        require(actual[index]==bundle and bundle['source_record']['id']==rid, 'Actual source delivery differs from current v16')
        require(delivery['input_line_sha256']==sha(source[index]) and delivery['source_bundle_sha256']==sha(cj(bundle).encode()), 'Actual delivery byte identity differs')
        require(delivery['actual_packet_binding']==packet_plan['packets'][index], 'Actual packet mapping differs')
        origin=origins[rid][2];log_path=origin['source_consumption_log']
        if log_path not in cache:
            require(log_path in parent_file_bindings, 'Original source log not in current machine freeze')
            exact(parent_file_bindings[log_path]);cache[log_path]=rows(log_path)
        old_log=cache[log_path][rid][2]
        check=validate_pair(old[rid][1],newraw,old_log,newlogs[rid][2],{d:newslots[rid,d][2] for d in DIMS})
        if check['label_changes'] or check['decision_changes'] or check['relation_trace_changed']:
            changes.append({'id':rid,**check})
    # Validate the exact retained parent line, slot and origin before output.
    counts={d:collections.Counter() for d in DIMS};lineage=[];prediction_bytes=[];slot_bytes=[]
    for ordinal,(rid,(_,parentraw,parentrow)) in enumerate(old.items(),1):
        selected=rid in new;_,raw,row=(new if selected else old)[rid];prior=origins[rid][2]
        require(prior['corpus_ordinal_1based']==ordinal and prior['actual_prediction_line_sha256']==sha(parentraw) and prior['prediction_line_bytes']==len(parentraw), 'Original actual lineage differs')
        prediction_bytes.append(raw)
        for d in DIMS:
            _,sraw,slot=(newslots if selected else oldslots)[rid,d]
            require(slot['retained_rule_decision']==row['decisions'][d] and slot['rule_value']==row['labels'][d] and not slot['technical_failure'], 'Composite slot is incomplete')
            slot_bytes.append(sraw);counts[d]['positive_N' if row['labels'][d]==1 else 'negative_N' if row['labels'][d]==0 else 'lawful_null_N']+=1
        origin=(dict(id=rid,actual_inference_algorithm=contract['candidate_version'],actual_run_directory=str(delta),source_consumption_log=str(delta/'actual-source-consumption.jsonl'),source_consumption_record_key=rid,superseded_parent_origin=prior) if selected else dict(prior))
        origin.update(corpus_ordinal_1based=ordinal,actual_prediction_line_sha256=sha(raw),prediction_line_bytes=len(raw),unchanged_actual_record_bytes_retained=True,candidate_compatibility_basis='actual_v12_affected_first_inference' if selected else 'unchanged_current_packet_and_SF_structural_noop_proof',inherited_parent_origin_binding=None if selected else {'path':str(parent/'execution-origin-lineage.jsonl'),'record_key':rid,'line_sha256':sha(origins[rid][1])})
        lineage.append(origin)
    result={'status':'validated_complete_v12_SF_delta_not_yet_merged','selected_N':2082,'inherited_N':2399,'actual_new_inference_record_N':2082,'complete_immutable_decisions_equal':True,'original_source_requests_and_stored_events_equal':True,'changed_record_N':len(changes),'new_inference_by_receiver':False}
    if validate_only:return result
    out.mkdir(parents=True,exist_ok=False)
    with (out/'predictions.jsonl').open('xb') as f:f.write(b''.join(prediction_bytes))
    with (out/'all-dimension-slots.jsonl').open('xb') as f:f.write(b''.join(slot_bytes))
    with (out/'execution-origin-lineage.jsonl').open('x') as f:
        for x in lineage:f.write(json.dumps(x,ensure_ascii=False,allow_nan=False)+'\n')
    save(out/'parent-compatible-to-candidate-actual-changes.json',{'changes':changes,'allowed_mutable_dimensions':['S','F'],'immutable_dimensions':list(FIXED),'complete_immutable_decision_tokens_equal':True,'source_request_and_stored_event_groups_equal':True,'run_receipt_metadata_not_forced_equal':True})
    ps=load(parent/'composite-status.json')
    status={'at_utc':now(),'status':'complete_v12_SF_v16_compatible_composite_with_explicit_execution_origins','candidate_algorithm_version':contract['candidate_version'],'actual_record_N':4481,'actual_dimension_N':22405,'technical_failure_dimension_N':0,'unresolved_technical_dimension_N':0,'lawful_null_N':sum(c['lawful_null_N'] for c in counts.values()),'counts':{d:{k:c[k] for k in ('positive_N','negative_N','lawful_null_N')} for d,c in counts.items()},'actual_execution_algorithm_record_N':dict(collections.Counter(x['actual_inference_algorithm'] for x in lineage)),'actual_affected_inference_record_N':2082,'inherited_compatible_parent_record_N':2399,'all4481_actually_inferred_under_candidate':False,'new_inference_executed_by_merge':False,'allowed_mutable_dimensions':['S','F'],'immutable_dimensions':list(FIXED),'immutable_complete_decision_bytes_all_identical':True,'parent_seal':bind(parent/'seal.json'),'delta_seal':bind(delta/'seal.json'),'parent_historical_status':bind(parent/'composite-status.json'),'source_common_v15':ps['source_common_v15'],'source_common_v16':ps['source_common_v16'],'material_delta_bindings':ps['material_delta_bindings'],'material_changed_record_ids':ps['material_changed_record_ids'],'new_material_changes_from_current_v16':[],'current_scope':bind(scope_path),'release':scope['release'],'static_impact_selection':contract['selection'],'original_input_lineage':bind(H/'original-input-lineage-sidecar.json'),'merger':bind(__file__),'prediction_binding':bind(out/'predictions.jsonl'),'label_slots_binding':bind(out/'all-dimension-slots.jsonl'),'predictions_path':str(out/'predictions.jsonl'),'label_slots_path':str(out/'all-dimension-slots.jsonl'),'formal_validation_complete':False,'human_validation_complete':False,'paper_writing_gate_open':False}
    save(out/'composite-status.json',status)
    save(out/'seal.json',{'status':status['status'],'files':[bind(p) for p in sorted(out.iterdir()) if p.is_file()],'ancestor_seals':[bind(parent/'seal.json'),bind(delta/'seal.json')],'self_excluded':True,'no_new_inference_executed_by_merge':True,'formal_validation_complete':False})
    return dict(result,status=status['status'],output=str(out))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--scope',required=True);p.add_argument('--delta',required=True);p.add_argument('--output',required=True);p.add_argument('--validate-only',action='store_true');a=p.parse_args()
    print(json.dumps(receive(a.scope,a.delta,a.output,a.validate_only),ensure_ascii=False))
