"""Exclusive v17 whole-batch merge identity preparation. No actual response read/merge."""
from pathlib import Path
import ast,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=ROOT/'06-coding/native-full4481-v16-three-member-merge-preparation-sol'
NATIVE=ROOT/'06-coding/native-v17-two-whole-batch-material-delta-preparation-root'
PARENT=ROOT/'06-coding/native-full4481-v16-three-member-compatible-root'
V17=ROOT/'01-review/source-interface-v17-finite-source-addendum-root'
def load(p):return json.loads(p.read_bytes())
def bind(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 with (HERE/p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def put(p,s):
 with (HERE/p).open('x',encoding='utf8') as f:f.write(s)
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
s=(OLD/'merge.py').read_text()
s=once(s,"NATIVE=BASE/'06-coding/native-v16-batch0216-material-delta-preparation-sol'","NATIVE=BASE/'06-coding/native-v17-two-whole-batch-material-delta-preparation-root'")
s=once(s,"IDS=['RECODE25-01402','RECODE25-01403','RECODE25-01404']","BATCH_IDS=('batch-0325','batch-0485')\nCHANGED=('RECODE25-02588','RECODE25-04598')")
s=once(s,"parent=Path(parent).resolve();coverage=c.load(parent/'coverage.json')","parent=Path(parent).resolve();assert parent==Path(doc['parent_collection_seal']['path']).parent,'Current v16 full parent required';c.exact(doc['parent_collection_seal']);coverage=c.load(parent/'coverage.json')")
s=once(s,"for name in ('coverage.json','selected-records.jsonl','selected-whole-batch-bindings.json'):","for name in ('coverage.json','selected-records.jsonl','selected-whole-batch-bindings.json','status.json'):")
s=once(s,"original=c.load(doc['original_manifest']['path']);c.exact(original['ordered_source_ids'])","parent_status=c.load(parent/'status.json');assert parent_status['status']=='complete_native_full4481_v16_three_member_compatible_composite_with_explicit_execution_origins' and parent_status['actual_merge_performed'] is True\n    assert parent_status['source_common_v16']==doc['source_common_v16'],'Current parent material identity differs'\n    original=c.load(doc['original_manifest']['path']);c.exact(original['ordered_source_ids'])")
s=once(s,"def new_whole(selection_path,c,doc):\n    assert Path(selection_path).resolve()==NATIVE/'batch-0216/root-selection.json','Only the actual assigned new-material whole selection is allowed'\n    selection=c.load(selection_path);m=c.load(doc['native_manifest']['path']);a=c.load(m['batches'][0]['assignment']['path'])",'''def new_whole(selection_path,batch_id,c,doc):
    assert batch_id in BATCH_IDS and Path(selection_path).resolve()==NATIVE/batch_id/'root-selection.json','Only the actual assigned new-material whole selection is allowed'
    selection=c.load(selection_path);m=c.load(doc['native_manifest']['path'])
    batch=next(b for b in m['batches'] if b['batch_id']==batch_id);a=c.load(batch['assignment']['path']);ids=a['source_ids']
    material=c.load(doc['material_delta_bindings']['manifest']['path'])
    closure=next(b for b in material['native_whole_batch_closures'] if b['batch_id']==batch_id)
    assert ids==closure['source_ids'] and a['expected_N']==closure['expected_N']==len(ids)==12''')
s=s.replace("m['batches'][0]['assignment']","batch['assignment']")
s=once(s,"'earliest_valid_new_v16_material_whole_batch'","'earliest_valid_new_v17_material_whole_batch'")
s=once(s,"selection['batch_id']==a['batch_id']=='batch-0216'","selection['batch_id']==a['batch_id']==batch_id")
s=once(s,"selection['source_ids']==a['source_ids']==IDS","selection['source_ids']==a['source_ids']==ids")
s=once(s,"selection['original_v15_results_never_overwritten']","selection['original_results_never_overwritten']")
s=once(s,"receipt['batch_id']=='batch-0216'","receipt['batch_id']==batch_id")
s=once(s,"[r['source_id'] for r in first['records']]==IDS","[r['source_id'] for r in first['records']]==ids")
start=s.index("    correspondence=c.load(");end=s.index("    packets={p['source_id']",start)
s=s[:start]+'''    assert a['packets']==closure['new_packets'],'Packet list differs from original-batch v17 closure'
    assert sum(p['bytes'] for p in a['packets'])==closure['new_packet_sum_bytes']<=closure['original_packet_byte_limit']
    prior_packets={p['source_id']:p for p in closure['actual_current_v16_packets']}
    for packet in a['packets']:
        c.exact(packet)
        if packet['source_id'] not in CHANGED:assert packet==prior_packets[packet['source_id']],'Unchanged packet binding differs'
''' +s[end:]
s=once(s,"'original_batch_id':'batch-0216'","'original_batch_id':batch_id")
s=s.replace("'new_actual_v16_material_whole_batch0216'","'new_actual_v17_material_whole_'+batch_id")
s=once(s,"'same_whole_first_for_all_five_dimensions_and_three_rows':True","'same_whole_first_for_all_five_dimensions_and_twelve_rows':True")
s=once(s,"'changed_source_material':sid=='RECODE25-01402'","'changed_source_material':sid in CHANGED")
start=s.index('def merge(')
s=s[:start]+'''def merge(parent_path,selection_paths,output):
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
    output_lines=[(json.dumps(replacements[r['id']],ensure_ascii=False,allow_nan=False)+'\\n').encode() if r['id'] in replacements else line for line,r in zip(lines,data)]
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
'''
ast.parse(s);put('merge.py',s)
old=load(OLD/'manifest.json');material=load(V17/'source-extension-manifest-v17.json')
inputs=[bind(NATIVE/'preparation-seal.json'),bind(NATIVE/'manifest.json'),bind(NATIVE/'strict-readback-receiver.py'),bind(NATIVE/'base-validator.py'),bind(PARENT/'seal.json'),bind(V17/'output-seal.json'),bind(V17/'source-extension-manifest-v17.json'),bind(V17/'packet-bindings-v17.json'),bind(V17/'common-frame-bundles-v17.jsonl')]
for k in ['original_collector','original_manifest','recovery_manifest']:inputs.append(old[k])
inputs.append(load(NATIVE/'manifest.json')['base_guard'])
manifest={'status':'prepared_not_merged','original_collector':old['original_collector'],'original_manifest':old['original_manifest'],'recovery_manifest':old['recovery_manifest'],'native_manifest':bind(NATIVE/'manifest.json'),'native_preparation_seal':bind(NATIVE/'preparation-seal.json'),'parent_collection_seal':bind(PARENT/'seal.json'),'source_common_v16':material['base_common'],'source_common_v17':material['new_common'],'material_delta_bindings':{'seal':bind(V17/'output-seal.json'),'manifest':bind(V17/'source-extension-manifest-v17.json'),'packet_bindings':bind(V17/'packet-bindings-v17.json')},'immutable_input_bindings':inputs,'batch_ids':['batch-0325','batch-0485'],'source_ids':[sid for b in material['native_whole_batch_closures'] for sid in b['source_ids']],'model_calls':0,'classifier_calls':0,'actual_merge_performed':False}
save('manifest.json',manifest)
print(json.dumps({'prepared':str(HERE),'model_calls':0,'actual_merge_performed':False},ensure_ascii=False))
