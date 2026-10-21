import pathlib,json,os,sys,hashlib
ROOT=pathlib.Path('/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding')
sys.path.insert(0,str(ROOT/'protocol-necessary-read-v4'))
import necessary_read_gate as g, native_records,packet_builder as pb
U=os.environ['CODEX_THREAD_ID']; A=ROOT/'native-llm77-v13-sol/attempts'/U
IDX=json.loads((ROOT/'development77-native-inputs-v3/batch-0007/source-index-compact.json').read_bytes())
DIMS=list(g.DIMENSIONS)
def write(path,obj):
 raw=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode();p=A/path
 with p.open('xb') as f:f.write(raw)
 return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def packet(n):return json.loads(pathlib.Path(IDX[n]['complete_packet_file']['path']).read_bytes())
def anchor(p,ctx=None,quote=None):
 row=p['source_bundle']['source_record']; t=row['text'] if ctx is None else row['contexts'][ctx]['text'];q=t if quote is None else quote;st=t.index(q)
 return {'source_kind':'current' if ctx is None else 'context','context_id':None if ctx is None else row['contexts'][ctx]['context_id'],'field_path':'text','quote':q,'span':{'start':st,'end':st+len(q)}}
def context(p,i,purpose):
 a=anchor(p,i);a.pop('source_kind');a['purpose']=purpose;return a
def read_receipt(p,sc,v,event,actual,tool='exec_command',event_id=None):
 rid=f"READ-{p['source_id']}-{len(sc['read_receipts'])+1}"
 sc['read_receipts'].append({'receipt_id':rid,'run_id':U,'reader':U,'source_id':p['source_id'],'resource_id':v['resource_id'],'source_sha256':v['source_sha256'],'view':v['view'],'view_sha256':v['view_sha256'],'scope_pointer':v['scope_pointer'],'locator_read':v['locator'],'delivery_status':'complete','read_attestation':'recorded','tool_name':tool,'event_id':event_id,'local_event_id':event,'visible_return_bytes':None,'actual_range_or_page':actual})
 return rid
def save(n,values,reasons,scope_note,event_id,paths=None,ctxs=None,images=None,support=None,fairness=None,extra=None,material=None):
 p=packet(n);row=p['source_bundle']['source_record'];sc=json.loads((A/'events'/('prepared-'+p['source_id']+'.json')).read_bytes());sc['necessary_source_scope_review_status']='complete';sc['scope_source_basis']={'note':scope_note,'bundle_pointers':['/source_record/text','/source_record/contexts']};views=g.inventory_views(sc['source_inventory'])
 for req in list(sc['requirements']):
  v=views[g.view_key(req)];actual={'entire_bound_view':True,'bundle_pointers':req['source_basis']['bundle_pointers']}
  if req['view']=='text':
   t=row['text'] if req['resource_id'].startswith('BODY-') else next(c['text'] for c in row['contexts'] if c['context_id']==req['resource_id']);actual['unicode_span']=[0,len(t)]
  receipt=read_receipt(p,sc,v,'source-read-'+event_id,actual,event_id=event_id)
  sc['use_receipts'].append({k:v[k] for k in ['resource_id','source_sha256','view','view_sha256','scope_pointer']}|{'use_status':'used','read_receipt_id':receipt,'use_scope':'确认完整当前、原CTX适用边界及共同谓词；不向当前复制兄弟记录维度。'})
 if extra:extra(p,sc,views)
 sc['required_read_complete_claim']=not sc['source_requests']
 item={'blind_id':p['output_id'],'content_sha256':p['source_bundle_sha256'],'manual_sha256':'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f','labels':dict(zip(DIMS,values)),'evidence':{},'material_requests':material or []}
 for d,val,reason in zip(DIMS,values,reasons):
  item['evidence'][d]={'paths':(paths or {}).get(d,['excluded'] if val==0 else ['material_missing'] if val is None else []),'current_quote':row['text'],'current_span':{'start':0,'end':len(row['text'])},'contexts_used':[context(p,i,'确认父条款、对象或限定；仅用于解释当前命题。') for i in (ctxs or {}).get(d,[])],'structural_context_ids_used':[],'image_sources_used':images or [],'reason':reason,'innovation_support':support if d=='I' else None,'fairness_specific':fairness if d=='F' else None}
 write(pathlib.Path('first-output')/(p['source_id']+'.json'),item);write(pathlib.Path('scopes')/(p['source_id']+'.json'),sc)
 write(pathlib.Path('events')/('read-binding-'+p['source_id']+'.json'),{'source_id':p['source_id'],'actual_tool_chunk_id':event_id,'local_event_id':'source-read-'+event_id,'tool':'exec_command','actual_return_source_ranges':{'current':'complete','CTX':'complete text and structure'},'scope_review':scope_note})
 print('SAVED',p['source_id'])
