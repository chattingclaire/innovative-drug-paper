"""Mechanical whole-batch material composite; no inference, selection edits or old writes."""
import argparse, collections, datetime, json, sys, types
from pathlib import Path
sys.dont_write_bytecode=True
if not __debug__: raise RuntimeError('Required binding assertions disabled')
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
NATIVE=BASE/'06-coding/native-v16-batch0216-material-delta-preparation-sol'
DIMS=('S','E','Ec','I','F')
IDS=['RECODE25-01402','RECODE25-01403','RECODE25-01404']

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
    parent=Path(parent).resolve();coverage=c.load(parent/'coverage.json')
    # First gate: partial collections never become a compatible full composite.
    assert coverage['full_corpus_complete'] is True and coverage['selected_record_N']==4481 and coverage['selected_batch_N']==504,'Actual full original504/4481 parent required; partial snapshot refused'
    assert coverage['missing_record_N']==0 and coverage['pointer_quote_issue_N']==0 and coverage['thin35_included'] is False
    assert coverage['first_values_changed'] is False and coverage['selection_by_semantic_metric'] is False and coverage['formal_validation_complete'] is False
    assert coverage['original_manifest']==doc['original_manifest'] and coverage['recovery_manifest']==doc['recovery_manifest']
    seal=c.load(parent/'seal.json');sealed={x['path']:x for x in seal['files']}
    for b in seal['files']:c.exact(b)
    for name in ('coverage.json','selected-records.jsonl','selected-whole-batch-bindings.json'):
        assert sealed[str(parent/name)]==c.binding(parent/name),'Required parent file outside actual seal'
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
def new_whole(selection_path,c,doc):
    assert Path(selection_path).resolve()==NATIVE/'batch-0216/root-selection.json','Only the actual assigned new-material whole selection is allowed'
    selection=c.load(selection_path);m=c.load(doc['native_manifest']['path']);a=c.load(m['batches'][0]['assignment']['path'])
    assert selection['artifact_type']=='earliest_valid_new_v16_material_whole_batch'
    assert selection['run_id']==a['run_id']==m['run_id'] and selection['batch_id']==a['batch_id']=='batch-0216'
    assert selection['source_ids']==a['source_ids']==IDS and selection['assignment']==m['batches'][0]['assignment']
    assert selection['semantic_scores_not_selection_criteria'] is True and selection['original_v15_results_never_overwritten'] is True and selection['independent_stability_repeat'] is False
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
        try:receiver.verify(doc['native_manifest']['path'],m['batches'][0]['assignment']['path'],prior['first_path'])
        except Exception as e:earlier.append({'attempt':prior['attempt_number'],'process_completion':c.binding(slot/'process-completion.json'),'receipt':c.binding(slot/'root-reception.json'),'read_only_recheck_rejected':{'type':type(e).__name__,'message':str(e)}})
        else:raise AssertionError('Earlier technically valid whole batch exists; no semantic replacement allowed')
    receipt=c.load(selection['reception']['path']);assert receipt['state']=='technical_valid_whole_batch'
    assert receipt['batch_id']=='batch-0216' and receipt['run_id']==m['run_id'] and receipt['attempt']==attempt
    assert receipt['semantic_correctness_checked'] is False and receipt['reference_compared'] is False and receipt['first_or_labels_modified'] is False
    process=c.load(Path(selection['first']['path']).parent/'process-completion.json')
    assert process['actual_process_terminal'] is True and type(process['pid']) is int and process['returncode']==0 and process['timed_out'] is False
    assert datetime.datetime.fromisoformat(selection['at_utc'])>=datetime.datetime.fromisoformat(receipt['at_utc'])>=datetime.datetime.fromisoformat(process['at_utc'])
    verified=receiver.verify(doc['native_manifest']['path'],m['batches'][0]['assignment']['path'],selection['first']['path'])
    assert receipt['validation']==verified and receipt['first']==selection['first']==verified['first'] and receipt['actor_seal']==selection['actor_seal']==verified['actor_seal']
    first=c.load(selection['first']['path']);assert [r['source_id'] for r in first['records']]==IDS
    assert first['requested_model']=='gpt-6.1-sol' and first['requested_reasoning_effort']=='ultra'
    original=c.load(doc['original_manifest']['path']);assert first['manual_binding']['sha256']==original['manual']['sha256'] and first['execution_prompt_binding']['sha256']==original['execution_prompt']['sha256']
    correspondence=c.load(doc['material_delta_bindings']['correspondence']['path']);metadata={x['source_id']:x for x in correspondence['records']}
    assert correspondence['changed_source_ids']==['RECODE25-01402']
    for packet in a['packets']:
        c.exact(packet);assert packet==metadata[packet['source_id']]['new_packet_binding']
        if packet['source_id']!='RECODE25-01402':assert metadata[packet['source_id']]['packet_binding_same'] is True and packet==metadata[packet['source_id']]['old_packet_binding']
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
        new.append({'id':sid,'labels':{d:r['dimensions'][d]['value'] for d in DIMS},'dimensions':r['dimensions'],'packet':flat(packets[sid]),'original_batch_id':'batch-0216','selected_mode':'new_actual_v16_material_whole_batch0216','selected_attempt_number':attempt,'first':selection['first'],'selection':c.binding(selection_path),'technical_receipt':selection['reception'],'actor_seal':selection['actor_seal'],'formal_validation_complete':False,'material_origin':{'kind':'new_actual_v16_material_whole_batch0216','run_id':m['run_id'],'same_whole_first_for_all_five_dimensions_and_three_rows':True,'source_bundle_sha256':packets[sid]['source_bundle_sha256'],'source_bundle_utf8_bytes':packets[sid]['source_bundle_utf8_bytes'],'changed_source_material':sid=='RECODE25-01402','independent_stability_repeat':False}})
    return selection,first,new,{'selected_strict_readback':verified,'earlier_actual_technical_slots':earlier,'process_completion':c.binding(Path(selection['first']['path']).parent/'process-completion.json')}
def merge(parent_path,selection_path,output):
    doc,c=profile();started=now();parent,cov,lines,data,batches=parent_full(parent_path,c,doc)
    selection,first,new,readback=new_whole(selection_path,c,doc)
    replacements={r['id']:r for r in new};old_by_id={r['id']:(line,r) for line,r in zip(lines,data)}
    assert [r['id'] for r in data if r['original_batch_id']=='batch-0216']==IDS
    for sid in IDS:
        line,prior=old_by_id[sid];r=replacements[sid]
        import hashlib
        r['material_origin']['parent_record_origin']={'parent_collector_seal':c.binding(parent/'seal.json'),'parent_selected_records':c.binding(parent/'selected-records.jsonl'),'parent_line_sha256':hashlib.sha256(line).hexdigest(),'packet':prior['packet'],'first':prior['first'],'selection':prior['selection'],'technical_receipt':prior['technical_receipt'],'actor_seal':prior['actor_seal']}
        if sid!='RECODE25-01402':assert r['packet']==prior['packet'],'Unchanged two packet bytes must retain exact old bindings'
    output_lines=[(json.dumps(replacements[r['id']],ensure_ascii=False,allow_nan=False)+'\n').encode() if r['id'] in replacements else line for line,r in zip(lines,data)]
    assert sum(a==b for a,b,r in zip(lines,output_lines,data) if r['id'] not in replacements)==4478
    _,merged=rows(b''.join(output_lines));assert [r['id'] for r in merged]==[r['id'] for r in data]
    for sid in IDS:assert next(r for r in merged if r['id']==sid)['dimensions']==next(r for r in first['records'] if r['source_id']==sid)['dimensions']
    new_batch={'batch_id':'batch-0216','selected_mode':'new_actual_v16_material_whole_batch0216','source_ids':IDS,'selection':c.binding(selection_path),'first':selection['first'],'receipt':selection['reception'],'actor_seal':selection['actor_seal'],'material_origin':{'new_material_run_id':selection['run_id'],'parent_collector_seal':c.binding(parent/'seal.json'),'parent_original_batch_origin':next(b for b in batches if b['batch_id']=='batch-0216'),'not_original_v15_technical_retry_or_stability':True}}
    selected_batches=[new_batch if b['batch_id']=='batch-0216' else b for b in batches];assert len(selected_batches)==504
    mode=collections.Counter();by_dim={d:collections.Counter(r['labels'][d] for r in merged) for d in DIMS}
    for batch in selected_batches:mode[batch['selected_mode']+'_batch_N']+=1;mode[batch['selected_mode']+'_record_N']+=len(batch['source_ids'])
    null=sum(x[None] for x in by_dim.values());coverage=dict(cov)
    coverage.update(at_utc=now(),identity='actual original504/4481 parent plus new actual v16-material whole batch0216;4478 original deliveries retained',binary_label_N=22405-null,lawful_null_label_N=null,missing_record_N=0,missing_label_N=0,record_output_coverage=1.0,complete_binary_record_N=sum(all(r['labels'][d] is not None for d in DIMS) for r in merged),per_dimension={d:{'positive_N':by_dim[d][1],'negative_N':by_dim[d][0],'lawful_null_N':by_dim[d][None],'missing_N':0} for d in DIMS},actual_selected_modes=dict(mode),missing_batch_states={},pointer_quote_issue_N=0,full_corpus_complete=True,provider_serving_model_independently_verified=False,formal_validation_complete=False,thin35_included=False,selection_by_semantic_metric=False,first_values_changed=False,parent_collector_seal=c.binding(parent/'seal.json'),new_whole_selection=c.binding(selection_path),not_all4481_reencoded_in_v16=True,material_changed_record_ids=['RECODE25-01402'],actual_new_whole_batch_record_ids=IDS,merger=c.binding(__file__))
    out=Path(output).resolve();assert not out.exists() and out.parent in (BASE/'06-coding',BASE/'07-statistics') and out!=parent and out!=NATIVE;out.mkdir(parents=True)
    with (out/'selected-records.jsonl').open('xb') as f:f.write(b''.join(output_lines))
    c.save(out/'coverage.json',coverage);c.save(out/'selected-whole-batch-bindings.json',selected_batches);c.save(out/'strict-merge-readback.json',readback)
    proof=c.load(doc['material_delta_bindings']['byteproof']['path'])
    status={'status':'complete_native_full4481_v16_three_member_compatible_composite_with_explicit_execution_origins','started_at_utc':started,'at_utc':now(),'actual_merge_performed':True,'single_actual_merge_pass':True,'actual_record_N':4481,'actual_dimension_N':22405,'parent_raw_line_preserved_N':4478,'actual_new_inference_record_N':3,'actual_new_whole_batch_record_ids':IDS,'material_changed_record_ids':['RECODE25-01402'],'not_all4481_reencoded_in_v16':True,'unresolved_technical_dimension_N':0,'original_failed_attempt_history_not_erased':True,'parent_collector_seal':c.binding(parent/'seal.json'),'parent_selected_records':c.binding(parent/'selected-records.jsonl'),'new_whole_selection':c.binding(selection_path),'new_whole_first':selection['first'],'new_whole_receipt':selection['reception'],'new_whole_actor_seal':selection['actor_seal'],'new_whole_process_completion':readback['process_completion'],'strict_merge_readback':c.binding(out/'strict-merge-readback.json'),'source_common_v15':proof['old_common'],'source_common_v16':proof['new_common'],'material_delta_bindings':doc['material_delta_bindings'],'selected_records':c.binding(out/'selected-records.jsonl'),'selected_whole_batches':c.binding(out/'selected-whole-batch-bindings.json'),'coverage':c.binding(out/'coverage.json'),'merger':c.binding(__file__),'merger_preparation_seal':c.binding(HERE/'seal.json'),'model_calls':0,'classifier_calls':0,'labels_or_first_files_modified':False,'semantic_validation_performed':False,'formal_validation_complete':False,'independent_stability_repeat':False}
    c.save(out/'status.json',status);c.save(out/'seal.json',{'files':[c.binding(p) for p in sorted(out.iterdir()) if p.is_file()],'self_excluded':True});return c.binding(out/'seal.json')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preflight','merge'],required=True);p.add_argument('--parent');p.add_argument('--selection');p.add_argument('--output');x=p.parse_args()
    if x.mode=='preflight':
        doc,c=profile()
        if x.parent:parent_full(x.parent,c,doc)
        print(json.dumps({'status':'prepared_not_merged','model_calls':0,'classifier_calls':0,'requires_actual_full_parent_and_new_whole_selection':True}));
    else:
        assert x.parent and x.selection and x.output,'Actual full parent, new selection and unique output required'
        print(json.dumps(merge(x.parent,x.selection,x.output),ensure_ascii=False))
