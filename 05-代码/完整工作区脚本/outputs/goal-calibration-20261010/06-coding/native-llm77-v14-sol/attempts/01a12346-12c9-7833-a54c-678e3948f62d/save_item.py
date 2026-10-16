import os,pathlib,json,sys,uuid
A=pathlib.Path(__file__).resolve().parent
B=A.parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(B/'protocol-necessary-read-v4'))
import necessary_read_gate as g
import packet_builder as pb
config=json.loads(pathlib.Path(sys.argv[1]).read_text())
uid=config['source_id']
idx=json.loads((B/'development77-native-inputs-v14/batch-0001/source-index-compact.json').read_text())
frozen=next(x for x in idx if x['source_id']==uid)
p=json.loads(pathlib.Path(frozen['complete_packet_file']['path']).read_text())
s=json.loads((A/'prepared-scopes'/f'{uid}.json').read_text())
plan=next(x for x in json.loads((A/'view-plan.json').read_text()) if x['source_id']==uid)
reg=json.loads((A/config.get('registry_file','read-registry-v5.json')).read_text())
row=p['source_bundle']['source_record']
text=row['text']
def receipt(v,n):
 ds=[]
 for f in A.glob('*-delivery.json'):
  d=json.loads(f.read_text());m=d['metadata']
  if m['input_file']==reg[n]['path'] and m['json_pointer']==reg[n].get('pointer') and m['view_sha256']==v['view_sha256']: ds.append((f,d))
 ds.sort(key=lambda x:x[1]['metadata']['start_byte']);assert ds and ds[0][1]['metadata']['start_byte']==0
 end=0
 for f,d in ds:
  assert d['actor_read'] and d['body_complete_visible'] and not d['truncated'] and d['metadata']['start_byte']==end
  end=d['metadata']['end_byte']
 assert ds[-1][1]['metadata']['view_EOF_after_this_chunk'] and end==ds[-1][1]['metadata']['view_total_UTF8_bytes']
 event=str(uuid.uuid4())
 pb.save_exclusive(A/'event-attachments'/(event+'.json'),pb.canonical({'local_event_id':event,'source_id':uid,'original_view':v,'delivery_files':[str(f) for f,d in ds],'actual_ranges':[{'start_byte':d['metadata']['start_byte'],'end_byte':d['metadata']['end_byte']} for f,d in ds],'actual_complete_view_read':True}))
 r={'receipt_id':'READ-'+str(uuid.uuid4()),'run_id':A.name,'reader':A.name,'source_id':uid,**{k:v[k] for k in ['resource_id','source_sha256','view','view_sha256','scope_pointer']},'locator_read':v['locator'],'delivery_status':'complete','read_attestation':'recorded','tool_name':'functions.exec > exec_command > source_view_chunk.py','event_id':None,'local_event_id':event,'visible_return_bytes':end,'actual_range_or_page':{'start_byte':0,'end_byte':end,'delivery_files':[str(f) for f,d in ds]}}
 s['read_receipts'].append(r)
 return r
for v in plan['carrier_entries']:receipt(v,v['registry_id'])
extra_receipts={}
for e in config.get('additional',[]):
 v=plan['additional_leaves'][e['leaf_index']]['additional_view'];g.validate_added_view(p['source_bundle'],v);s['additional_views'].append(v)
 rid=f"REQ-{uid}-leaf-{e['leaf_index']}"
 s['requirements'].append({'requirement_id':rid,'resource_id':v['resource_id'],'view':v['view'],'scope_pointer':v['scope_pointer'],'source_relation_kind':e['relation'],'source_evidence_locator':v['locator'],'source_basis':{'note':e['basis'],'bundle_pointers':['/source_record/text',v['scope_pointer']]},'dependency_dimensions':e['dimensions']})
 r=receipt(v,e['registry_id']);extra_receipts[v['scope_pointer']]=r['receipt_id']
 if e.get('citation'):
  s['reference_resolution'].append({'reference_id':f"REF-{uid}-{e['leaf_index']}",'citation_literal':e['citation'],'source_basis':{'note':e['basis'],'bundle_pointers':['/source_record/text',v['scope_pointer']]},'necessary_dependency':True,'dependency_dimensions':e['dimensions'],'resolution_status':'exact_snapshot','target_requirement_id':rid,'target_source_sha256':v['source_sha256'],'identity_basis_pointers':['/source_record/source_ref',v['scope_pointer'].rsplit('/',1)[0]]})
s['necessary_source_scope_review_status']='complete'
s['scope_source_basis']={'note':config['scope_note'],'bundle_pointers':config['scope_pointers']}
s['required_read_complete_claim']=True
used=set(config.get('used_registry_ids',[v['registry_id'] for v in plan['carrier_entries']]))
for r,v in zip(s['read_receipts'][:len(plan['carrier_entries'])],plan['carrier_entries']):
 if v['registry_id'] in used:s['use_receipts'].append({**{k:r[k] for k in ['resource_id','source_sha256','view','view_sha256','scope_pointer']},'use_status':'used','read_receipt_id':r['receipt_id'],'use_scope':config['scope_note']})
for r in s['read_receipts'][len(plan['carrier_entries']):]:s['use_receipts'].append({**{k:r[k] for k in ['resource_id','source_sha256','view','view_sha256','scope_pointer']},'use_status':'used','read_receipt_id':r['receipt_id'],'use_scope':config['scope_note']})
def anchor(spec):
 if 'context_index' in spec:
  c=row['contexts'][spec['context_index']];value=c[spec.get('field_path','text')];kind='context';cid=c['context_id']
 else:value=text;kind='current';cid=None
 q=spec.get('quote',value);start=value.index(q)
 return {'source_kind':kind,'context_id':cid,'field_path':spec.get('field_path','text'),'quote':q,'span':{'start':start,'end':start+len(q)}}
ev={}
for d in g.DIMENSIONS:
 cs=[]
 for n in config.get('contexts_by_dimension',{}).get(d,config.get('contexts_used',[])):
  c=row['contexts'][n];value=c['text'];cs.append({'context_id':c['context_id'],'field_path':'text','quote':value,'span':{'start':0,'end':len(value)},'purpose':config['context_purpose']})
 ev[d]={'paths':config['paths'][d],'current_quote':text,'current_span':{'start':0,'end':len(text)},'contexts_used':cs,'structural_context_ids_used':[row['contexts'][n]['context_id'] for n in config.get('structural_context_indices',[])],'image_sources_used':config.get('image_sources_used',[]),'reason':config['reasons'][d],'innovation_support':None,'fairness_specific':None}
if config.get('innovation_support'):
 z=config['innovation_support'];ev['I']['innovation_support']={'rd_object':anchor(z['rd_object']),'available_support':anchor(z['available_support']),'direct_relation':z['direct_relation']}
if config.get('fairness_specific'):
 z=config['fairness_specific'];ev['F']['fairness_specific']={k:anchor(z[k]) for k in ['patient_drug_object','fairness_relation','arrangement_or_evaluation']};ev['F']['fairness_specific']['relation_type']=z['relation_type']
item={'blind_id':p['output_id'],'content_sha256':p['source_bundle_sha256'],'manual_sha256':'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f','labels':config['labels'],'evidence':ev,'material_requests':config.get('material_requests',[])}
pb.save_exclusive(A/'first-output'/f'{uid}.json',pb.canonical(item));pb.save_exclusive(A/'scopes'/f'{uid}.json',pb.canonical(s))
quotes=[]
for i,z in enumerate(config.get('public_quotes',[])):
 value=g.pointer_value(p['source_bundle'],z['pointer']);q=z['quote'];start=value.index(q);obj={'source_id':uid,'source_bundle_sha256':p['source_bundle_sha256'],'bundle_pointer':z['pointer'],'quote':q,'span':{'start':start,'end':start+len(q)}}
 f=A/'source-quotes'/f'{uid}-{i}.json';pb.save_exclusive(f,pb.canonical(obj));quotes.append({'source_id':uid,'dimensions':z['dimensions'],'purpose':z['purpose'],'quote_file':str(f),'read_receipt_id':extra_receipts.get(z['pointer'])})
pb.save_exclusive(A/'source-quotes'/f'{uid}-index.json',pb.canonical(quotes));print('first_complete_item_and_scope_saved',uid)
