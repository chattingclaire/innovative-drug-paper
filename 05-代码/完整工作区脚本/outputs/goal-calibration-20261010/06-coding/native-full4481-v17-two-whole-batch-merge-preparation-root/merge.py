"""Mechanical whole-batch material composite; no inference, selection edits or old writes."""
import argparse, collections, datetime, json, sys, types
from pathlib import Path
sys.dont_write_bytecode=True
if not __debug__: raise RuntimeError('Required binding assertions disabled')
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
NATIVE=BASE/'06-coding/native-v17-two-whole-batch-material-delta-preparation-root'
DIMS=('S','E','Ec','I','F')
BATCH_IDS=('batch-0325','batch-0485')
CHANGED=('RECODE25-02588','RECODE25-04598')

def module(b):
    import hashlib
    raw=Path(b['path']).read_bytes();assert len(raw)==b['bytes'] and hashlib.sha256(raw).hexdigest()==b['sha256']
    m=types.ModuleType('frozen_read_only_helper');m.__file__=b['path'];exec(compile(raw,b['path'],'exec'),m.__dict__);return m
def profile():
    import hashlib
    def bind(p):
        p=Path(p).resolve();x=p.read_bytes();return {'path':str(p),'bytes':len(x),'sha256':hashlib.sha256(x).hexdigest()}
    doc=json.loads((HERE/'manifest.json').read_bytes())
    for b in json.loads((HERE/'seal.json').read_bytes())['files']+doc['immutable_input_bindings']:
        assert bind(b['path'])=={k:b[k] for k in ('path','bytes','sha256')},'Changed preparation binding'
    return doc,module(doc['original_collector'])
def flat(b):return {k:b[k] for k in ('path','bytes','sha256')}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def rows(raw):
    lines=raw.splitlines(keepends=True);values=[]
    def unique(pairs):
        d={}
        for k,v in pairs:assert k not in d,'Duplicate JSON key';d[k]=v
        return d
    def invalid(v):raise ValueError('Nonfinite JSON: '+v)
    for line in lines:
        assert line.endswith(b'\n'),'Unterminated parent delivery line'
        values.append(json.loads(line,object_pairs_hook=unique,parse_constant=invalid))
    return lines,values
def parent_full(parent,c,doc):
    parent=Path(parent).resolve();assert parent==Path(doc['parent_collection_seal']['path']).parent,'Current v16 full parent required';c.exact(doc['parent_collection_seal']);coverage=c.load(parent/'coverage.json')
    # First gate: partial collections never become a compatible full composite.
    assert coverage['full_corpus_complete'] is True and coverage['selected_record_N']==4481 and coverage['selected_batch_N']==504,'Actual full original504/4481 parent required; partial snapshot refused'
    assert coverage['missing_record_N']==0 and coverage['pointer_quote_issue_N']==0 and coverage['thin35_included'] is False
    assert coverage['first_values_changed'] is False and coverage['selection_by_semantic_metric'] is False and coverage['formal_validation_complete'] is False
    assert coverage['original_manifest']==doc['original_manifest'] and coverage['recovery_manifest']==doc['recovery_manifest']
    seal=c.load(parent/'seal.json');sealed={x['path']:x for x in seal['files']}
    for b in seal['files']:c.exact(b)
    for name in ('coverage.json','selected-records.jsonl','selected-whole-batch-bindings.json','status.json'):
        assert sealed[str(parent/name)]==c.binding(parent/name),'Required parent file outside actual seal'
    parent_status=c.load(parent/'status.json');assert parent_status['status']=='complete_native_full4481_v16_three_member_compatible_composite_with_explicit_execution_origins' and parent_status['actual_merge_performed'] is True
    assert parent_status['source_common_v16']==doc['source_common_v16'],'Current parent material identity differs'
    original=c.load(doc['original_manifest']['path']);c.exact(original['ordered_source_ids'])
    expected=c.load(original['ordered_source_ids']['path'])['approved_record_ids'];assert len(expected)==len(set(expected))==4481
    lines,data=rows((parent/'selected-records.jsonl').read_bytes());assert [r['id'] for r in data]==expected
    batches=c.load(parent/'selected-whole-batch-bindings.json');assert len(batches)==504
    assert [b['batch_id'] for b in batches]==[b['batch_id'] for b in original['batches']]
    for selected,allocated in zip(batches,original['batches']):assert selected['source_ids']==allocated['source_ids']
    for r in data:
        assert set(r['labels'])==set(r['dimensions'])==set(DIMS) and r['formal_validation_complete'] is False
        for d in DIMS:assert r['labels'][d]==r['dimensions'][d]['value'] and (r['labels'][d] is None or type(r['labels'][d]) is int and r['labels'][d] in (0,1))
    return parent,coverage,lines,data,batches
def new_whole(selection_path,batch_id,c,doc):
    assert batch_id in BATCH_IDS and Path(selection_path).resolve()==NATIVE/batch_id/'root-selection.json','Only the actual assigned new-material whole selection is allowed'
    selection=c.load(selection_path);m=c.load(doc['native_manifest']['path'])
    batch=next(b for b in m['batches'] if b['batch_id']==batch_id);a=c.load(batch['assignment']['path']);ids=a['source_ids']
    material=c.load(doc['material_delta_bindings']['manifest']['path'])
    closure=next(b for b in material['native_whole_batch_closures'] if b['batch_id']==batch_id)
    assert ids==closure['source_ids'] and a['expected_N']==closure['expected_N']==len(ids)==12
    assert selection['artifact_type']=='earliest_valid_new_v17_material_whole_batch'
    assert selection['run_id']==a['run_id']==m['run_id'] and selection['batch_id']==a['batch_id']==batch_id
    assert selection['source_ids']==a['source_ids']==ids and selection['assignment']==batch['assignment']
    assert selection['semantic_scores_not_selection_criteria'] is True and selection['original_results_never_overwritten'] is True and selection['independent_stability_repeat'] is False
    attempt=selection['attempt'];assert type(attempt) is int and 1<=attempt<=3
    for k in ('first','reception','actor_seal'):c.exact(selection[k])
    route=c.load(a['attempt_output_routing']['path'])['routes'];assert len(route)==3
    selected_route=route[attempt-1];assert selected_route['attempt_number']==attempt
    assert selection['first']==c.binding(selected_route['first_path']) and selection['reception']==c.binding(Path(selected_route['output_directory'])/'root-reception.json')
    receiver=module(m['receiver']);earlier=[]
    for prior in route[:attempt-1]:
        slot=Path(prior['output_directory']);process=c.load(slot/'process-completion.json');receipt=c.load(slot/'root-reception.json')
        assert process['actual_process_terminal'] is True and type(process['returncode']) is int
        c.exact(process['events']);c.exact(process['stderr']);assert receipt['state']=='technical_invalid_whole_batch'
        try:receiver.verify(doc['native_manifest']['path'],batch['assignment']['path'],prior['first_path'])
        except Exception as e:earlier.append({'attempt':prior['attempt_number'],'process_completion':c.binding(slot/'process-completion.json'),'receipt':c.binding(slot/'root-reception.json'),'read_only_recheck_rejected':{'type':type(e).__name__,'message':str(e)}})
        else:raise AssertionError('Earlier technically valid whole batch exists; no semantic replacement allowed')
    receipt=c.load(selection['reception']['path']);assert receipt['state']=='technical_valid_whole_batch'
    assert receipt['batch_id']==batch_id and receipt['run_id']==m['run_id'] and receipt['attempt']==attempt
    assert receipt['semantic_correctness_checked'] is False and receipt['reference_compared'] is False and receipt['first_or_labels_modified'] is False
    process=c.load(Path(selection['first']['path']).parent/'process-completion.json')
    assert process['actual_process_terminal'] is True and type(process['pid']) is int and process['returncode']==0 and process['timed_out'] is False
    assert datetime.datetime.fromisoformat(selection['at_utc'])>=datetime.datetime.fromisoformat(receipt['at_utc'])>=datetime.datetime.fromisoformat(process['at_utc'])
    verified=receiver.verify(doc['native_manifest']['path'],batch['assignment']['path'],selection['first']['path'])
    assert receipt['validation']==verified and receipt['first']==selection['first']==verified['first'] and receipt['actor_seal']==selection['actor_seal']==verified['actor_seal']
    first=c.load(selection['first']['path']);assert [r['source_id'] for r in first['records']]==ids
    assert first['requested_model']=='gpt-6.1-sol' and first['requested_reasoning_effort']=='ultra'
    original=c.load(doc['original_manifest']['path']);assert first['manual_binding']['sha256']==original['manual']['sha256'] and first['execution_prompt_binding']['sha256']==original['execution_prompt']['sha256']
    assert a['packets']==closure['new_packets'],'Packet list differs from original-batch v17 closure'
    assert sum(p['bytes'] for p in a['packets'])==closure['new_packet_sum_bytes']<=closure['original_packet_byte_limit']
    prior_packets={p['source_id']:p for p in closure['actual_current_v16_packets']}
    for packet in a['packets']:
        c.exact(packet)
        if packet['source_id'] not in CHANGED:assert packet==prior_packets[packet['source_id']],'Unchanged packet binding differs'
    packets={p['source_id']:p for p in a['packets']};new=[]
    for r in first['records']:
        sid=r['source_id'];packet=c.load(packets[sid]['path']);assert r['packet_sha256']==packets[sid]['sha256'] and set(r['dimensions'])==set(DIMS)
        for d in DIMS:
            decision=r['dimensions'][d];assert decision['value'] is None or type(decision['value']) is int and decision['value'] in (0,1)
            good=0
            for e in decision['evidence']:
                if 'pointer' in e:
                    target=c.pointer(packet,e['pointer']);assert isinstance(target,str) and isinstance(e['quote'],str) and e['quote'] and e['quote'] in target and e['role'] in ('current','context');good+=1
            assert decision['value'] is None or good>0,'Binary dimension lacks precise packet quote'
        new.append({'id':sid,'labels':{d:r['dimensions'][d]['value'] for d in DIMS},'dimensions':r['dimensions'],'packet':flat(packets[sid]),'original_batch_id':batch_id,'selected_mode':'new_actual_v17_material_whole_'+batch_id,'selected_attempt_number':attempt,'first':selection['first'],'selection':c.binding(selection_path),'technical_receipt':selection['reception'],'actor_seal':selection['actor_seal'],'formal_validation_complete':False,'material_origin':{'kind':'new_actual_v17_material_whole_'+batch_id,'run_id':m['run_id'],'same_whole_first_for_all_five_dimensions_and_twelve_rows':True,'source_bundle_sha256':packets[sid]['source_bundle_sha256'],'source_bundle_utf8_bytes':packets[sid]['source_bundle_utf8_bytes'],'changed_source_material':sid in CHANGED,'independent_stability_repeat':False}})
    return selection,first,new,{'selected_strict_readback':verified,'earlier_actual_technical_slots':earlier,'process_completion':c.binding(Path(selection['first']['path']).parent/'process-completion.json')}
def merge(parent_path,selection_paths,output):
    doc,c=profile();started=now();parent,cov,lines,data,batches=parent_full(parent_path,c,doc)
    expected_paths=[NATIVE/b/'root-selection.json' for b in BATCH_IDS]
    assert [Path(p).resolve() for p in selection_paths]==expected_paths,'Exactly two original whole selections in fixed batch order required'
    deliveries=[new_whole(path,bid,c,doc) for path,bid in zip(selection_paths,BATCH_IDS)]
    new=[r for _,_,records,_ in deliveries for r in records];ids=[r['id'] for r in new]
    assert len(ids)==len(set(ids))==24
    replacements={r['id']:r for r in new};old_by_id={r['id']:(line,r) for line,r in zip(lines,data)}
    source_first={r['source_id']:r for _,first,_,_ in deliveries for r in first['records']}
    for bid,(selection,first,records,readback) in zip(BATCH_IDS,deliveries):
        assert [r['id'] for r in data if r['original_batch_id']==bid]==selection['source_ids']
    for sid in ids:
        line,prior=old_by_id[sid];r=replacements[sid]
        import hashlib
        r['material_origin']['parent_record_origin']={'parent_collector_seal':c.binding(parent/'seal.json'),'parent_selected_records':c.binding(parent/'selected-records.jsonl'),'parent_line_sha256':hashlib.sha256(line).hexdigest(),'packet':prior['packet'],'first':prior['first'],'selection':prior['selection'],'technical_receipt':prior['technical_receipt'],'actor_seal':prior['actor_seal']}
        if sid not in CHANGED:assert r['packet']==prior['packet'],'Unchanged22 packet bytes must retain exact old bindings'
    output_lines=[(json.dumps(replacements[r['id']],ensure_ascii=False,allow_nan=False)+'\n').encode() if r['id'] in replacements else line for line,r in zip(lines,data)]
    assert sum(a==b for a,b,r in zip(lines,output_lines,data) if r['id'] not in replacements)==4457
    _,merged=rows(b''.join(output_lines));assert [r['id'] for r in merged]==[r['id'] for r in data]
    for sid in ids:assert next(r for r in merged if r['id']==sid)['dimensions']==source_first[sid]['dimensions']
    new_batches={}
    for bid,path,(selection,first,records,readback) in zip(BATCH_IDS,selection_paths,deliveries):
        new_batches[bid]={'batch_id':bid,'selected_mode':'new_actual_v17_material_whole_'+bid,'source_ids':selection['source_ids'],'selection':c.binding(path),'first':selection['first'],'receipt':selection['reception'],'actor_seal':selection['actor_seal'],'material_origin':{'new_material_run_id':selection['run_id'],'parent_collector_seal':c.binding(parent/'seal.json'),'parent_original_batch_origin':next(b for b in batches if b['batch_id']==bid),'not_previous_technical_retry_or_stability':True}}
    selected_batches=[new_batches.get(b['batch_id'],b) for b in batches];assert len(selected_batches)==504
    assert next(b for b in selected_batches if b['batch_id']=='batch-0216')==next(b for b in batches if b['batch_id']=='batch-0216'),'Preserve v16/0216 actual origin'
    mode=collections.Counter();by_dim={d:collections.Counter(r['labels'][d] for r in merged) for d in DIMS}
    for batch in selected_batches:mode[batch['selected_mode']+'_batch_N']+=1;mode[batch['selected_mode']+'_record_N']+=len(batch['source_ids'])
    null=sum(x[None] for x in by_dim.values());coverage=dict(cov)
    # Parent current-round singular fields are now historical, still bound through the full parent seal.
    for key in ('new_whole_selection','not_all4481_reencoded_in_v16'):coverage.pop(key,None)
    selections=[c.binding(p) for p in selection_paths]
    coverage.update(at_utc=now(),identity='actual full v16 parent plus actual v17-material whole batches0325/0485;4457 parent raw deliveries retained',binary_label_N=22405-null,lawful_null_label_N=null,missing_record_N=0,missing_label_N=0,record_output_coverage=1.0,complete_binary_record_N=sum(all(r['labels'][d] is not None for d in DIMS) for r in merged),per_dimension={d:{'positive_N':by_dim[d][1],'negative_N':by_dim[d][0],'lawful_null_N':by_dim[d][None],'missing_N':0} for d in DIMS},actual_selected_modes=dict(mode),missing_batch_states={},pointer_quote_issue_N=0,full_corpus_complete=True,provider_serving_model_independently_verified=False,formal_validation_complete=False,thin35_included=False,selection_by_semantic_metric=False,first_values_changed=False,parent_collector_seal=c.binding(parent/'seal.json'),new_whole_selections=selections,not_all4481_reencoded_in_v17=True,material_changed_record_ids=list(CHANGED),actual_new_whole_batch_record_ids=ids,merger=c.binding(__file__))
    out=Path(output).resolve();assert not out.exists() and out.parent in (BASE/'06-coding',BASE/'07-statistics') and out!=parent and out!=NATIVE;out.mkdir(parents=True)
    with (out/'selected-records.jsonl').open('xb') as f:f.write(b''.join(output_lines))
    c.save(out/'coverage.json',coverage);c.save(out/'selected-whole-batch-bindings.json',selected_batches)
    readbacks=[dict(batch_id=bid,**delivery[3]) for bid,delivery in zip(BATCH_IDS,deliveries)]
    c.save(out/'strict-merge-readback.json',{'batches':readbacks})
    status={'status':'complete_native_full4481_v17_two_whole_batch_compatible_composite_with_explicit_execution_origins','started_at_utc':started,'at_utc':now(),'actual_merge_performed':True,'single_actual_merge_pass':True,'actual_record_N':4481,'actual_dimension_N':22405,'parent_raw_line_preserved_N':4457,'actual_new_inference_record_N':24,'actual_new_whole_batch_record_ids':ids,'material_changed_record_ids':list(CHANGED),'not_all4481_reencoded_in_v17':True,'unresolved_technical_dimension_N':0,'original_failed_attempt_history_not_erased':True,'parent_collector_seal':c.binding(parent/'seal.json'),'parent_selected_records':c.binding(parent/'selected-records.jsonl'),'new_whole_selections':selections,'new_whole_firsts':[d[0]['first'] for d in deliveries],'new_whole_receipts':[d[0]['reception'] for d in deliveries],'new_whole_actor_seals':[d[0]['actor_seal'] for d in deliveries],'new_whole_process_completions':[d[3]['process_completion'] for d in deliveries],'strict_merge_readback':c.binding(out/'strict-merge-readback.json'),'source_common_v16':doc['source_common_v16'],'source_common_v17':doc['source_common_v17'],'material_delta_bindings':doc['material_delta_bindings'],'selected_records':c.binding(out/'selected-records.jsonl'),'selected_whole_batches':c.binding(out/'selected-whole-batch-bindings.json'),'coverage':c.binding(out/'coverage.json'),'merger':c.binding(__file__),'merger_preparation_seal':c.binding(HERE/'seal.json'),'model_calls':0,'classifier_calls':0,'labels_or_first_files_modified':False,'semantic_validation_performed':False,'formal_validation_complete':False,'independent_stability_repeat':False}
    c.save(out/'status.json',status);c.save(out/'seal.json',{'files':[c.binding(p) for p in sorted(out.iterdir()) if p.is_file()],'self_excluded':True});return c.binding(out/'seal.json')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preflight','merge'],required=True);p.add_argument('--parent');p.add_argument('--selection',action='append');p.add_argument('--output');x=p.parse_args()
    if x.mode=='preflight':
        doc,c=profile()
        if x.parent:parent_full(x.parent,c,doc)
        print(json.dumps({'status':'prepared_not_merged','model_calls':0,'classifier_calls':0,'requires_actual_full_v16_parent_and_two_whole_selections':True}));
    else:
        assert x.parent and x.selection and x.output,'Actual full parent, two selections and unique output required'
        print(json.dumps(merge(x.parent,x.selection,x.output),ensure_ascii=False))
