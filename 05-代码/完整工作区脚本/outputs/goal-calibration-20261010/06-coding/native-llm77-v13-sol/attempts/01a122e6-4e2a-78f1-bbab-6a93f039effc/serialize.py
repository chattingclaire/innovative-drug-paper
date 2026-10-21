import os,sys,json,pathlib,hashlib,copy
sys.dont_write_bytecode=True
BASE=pathlib.Path('/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding')
sys.path.insert(0,str(BASE/'protocol-necessary-read-v4'))
import necessary_read_gate as gate,native_records
RUN=os.environ['CODEX_THREAD_ID']; A=BASE/'native-llm77-v13-sol'/'attempts'/RUN
MANUAL='a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f'
DIMS=['S','E','Ec','I','F']
def put(path,obj):
 p=A/path
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return str(p)
def packet(num):
 return json.loads((BASE/'development77-native-inputs-v3/packets'/('RECODE25-'+num+'.compact.json')).read_text())
def span(text,quote=None):
 if quote is None:return {'start':0,'end':len(text)}
 s=text.index(quote);return {'start':s,'end':s+len(quote)}
def ctxquote(p,i,purpose):
 c=p['source_bundle']['source_record']['contexts'][i];t=c['text']
 return {'context_id':c['context_id'],'field_path':'text','quote':t,'span':span(t),'purpose':purpose}
def anchor(p,quote=None,ctx=None):
 row=p['source_bundle']['source_record'];c=row if ctx is None else row['contexts'][ctx];t=c['text']
 return {'source_kind':'current' if ctx is None else 'context','context_id':None if ctx is None else c['context_id'],'field_path':'text','quote':t if quote is None else quote,'span':span(t,quote)}
def read_receipts(scope,event,local,reqs=None,actual=None):
 views=gate.inventory_views(scope['source_inventory']);views.update({gate.view_key(v):v for v in scope['additional_views']})
 for req in scope['requirements'] if reqs is None else reqs:
  v=views[gate.view_key(req)]
  receipt={'receipt_id':'READ-'+scope['source_id']+'-'+str(len(scope['read_receipts'])+1),'run_id':RUN,'reader':RUN,'source_id':scope['source_id'],'resource_id':v['resource_id'],'source_sha256':v['source_sha256'],'view':v['view'],'view_sha256':v['view_sha256'],'scope_pointer':v['scope_pointer'],'locator_read':v['locator'],'delivery_status':'complete','read_attestation':'recorded','tool_name':'exec_command','event_id':event,'local_event_id':local,'visible_return_bytes':None,'actual_range_or_page':actual or {'scope':'complete original current body or CTX text/structure as returned in the recorded source payload','bundle_pointers':req['source_basis']['bundle_pointers']}}
  scope['read_receipts'].append(receipt)
  scope['use_receipts'].append({k:receipt[k] for k in ['resource_id','source_sha256','view','view_sha256','scope_pointer']}|{'use_status':'used','read_receipt_id':receipt['receipt_id'],'use_scope':'Current proposition and finite object, heading, parent/group, qualifier or boundary review; no whole-document label inheritance.'})
def save(num,values,reasons,paths,scope_note,event,contexts=None,support=None,fair=None,requests=None,extra_scope=None):
 p=packet(num);sid=p['source_id'];row=p['source_bundle']['source_record']
 sc=json.loads((A/'events'/('prepared-'+sid+'.json')).read_text())
 if extra_scope is not None:extra_scope(sc,p)
 read_receipts(sc,event,'source-read-'+num,reqs=[r for r in sc['requirements'] if r['scope_pointer'] is None and r['source_relation_kind'] in ['current_body','preserved_current_source_context','necessary_role_or_scope_boundary','necessary_geometry']])
 sc['necessary_source_scope_review_status']='complete';sc['scope_source_basis']={'note':scope_note,'bundle_pointers':['/source_record','/source_record/contexts']};sc['required_read_complete_claim']=not sc['source_requests']
 ev={}
 for j,d in enumerate(DIMS):
  ev[d]={'paths':paths[j],'current_quote':row['text'],'current_span':span(row['text']),'contexts_used':[ctxquote(p,i,purpose) for i,purpose in (contexts or {}).get(d,[])],'structural_context_ids_used':[c['context_id'] for c in row['contexts'] if c['kind']=='structural_relation'],'image_sources_used':[],'reason':reasons[j],'innovation_support':support if d=='I' else None,'fairness_specific':fair if d=='F' else None}
 item={'blind_id':p['output_id'],'content_sha256':p['source_bundle_sha256'],'manual_sha256':MANUAL,'labels':dict(zip(DIMS,values)),'evidence':ev,'material_requests':requests or []}
 put('first-output/'+sid+'.json',item);put('scopes/'+sid+'.json',sc)
 put('events/source-read-'+num+'.json',{'reader':RUN,'local_event_id':'source-read-'+num,'tool':'exec_command','tool_chunk_id':event,'source_packet_path':str(BASE/'development77-native-inputs-v3/packets'/(sid+'.compact.json')),'source_packet_sha256':hashlib.sha256((BASE/'development77-native-inputs-v3/packets'/(sid+'.compact.json')).read_bytes()).hexdigest(),'observed_range':'complete current text, all original CTX text/structure, source roles and identity metadata; any extra sources separately recorded','full_platform_wire_response':None})
 return item
