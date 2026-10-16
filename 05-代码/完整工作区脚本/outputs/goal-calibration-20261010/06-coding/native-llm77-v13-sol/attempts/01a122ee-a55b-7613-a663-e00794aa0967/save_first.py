import json,pathlib,os,sys,hashlib
A=pathlib.Path(__file__).parent
BASE=A.parents[2].parent
sys.path.insert(0,str(BASE/'protocol-necessary-read-v4'))
import necessary_read_gate as gate
D=['S','E','Ec','I','F']
INDEX=json.loads((A/'batch-index.json').read_text())
def xb(name,obj):
 p=A/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return p
def pkt(sid):
 x=next(x for x in INDEX if x['source_id']==sid)
 return json.loads(pathlib.Path(x['complete_packet_file']['path']).read_bytes())
def context(row,i,purpose):
 c=row['contexts'][i];v=c['text']
 return dict(context_id=c['context_id'],field_path='text',quote=v,span={'start':0,'end':len(v)},purpose=purpose)
def anchor(row,quote=None,ci=None):
 c=row if ci is None else row['contexts'][ci];v=c['text'];q=quote or v;start=v.index(q)
 return {'source_kind':'current' if ci is None else 'context','context_id':None if ci is None else c['context_id'],'field_path':'text','quote':q,'span':{'start':start,'end':start+len(q)}}
def save(sid,decision):
 pk=pkt(sid);row=pk['source_bundle']['source_record'];text=row['text']
 labels=dict(zip(D,decision['labels']))
 evidence={}
 for d in D:
  e=decision['evidence'][d]
  evidence[d]={'paths':e['paths'],'current_quote':text,'current_span':{'start':0,'end':len(text)},'contexts_used':[context(row,i,p) for i,p in e.get('contexts',[])],'structural_context_ids_used':[row['contexts'][i]['context_id'] for i in e.get('structure',[])],'image_sources_used':e.get('images',[]),'reason':e['reason'],'innovation_support':None,'fairness_specific':None}
  if 'support' in e:
   v=e['support'];evidence[d]['innovation_support']={'rd_object':anchor(row,v.get('object_quote'),v.get('object_context')),'available_support':anchor(row,v.get('support_quote'),v.get('support_context')),'direct_relation':v['relation']}
  if 'fairness' in e:
   v=e['fairness'];evidence[d]['fairness_specific']={k:anchor(row,v[k].get('quote'),v[k].get('context')) for k in ['patient_drug_object','fairness_relation','arrangement_or_evaluation']};evidence[d]['fairness_specific']['relation_type']=v['relation_type']
 item={'blind_id':pk['output_id'],'content_sha256':pk['source_bundle_sha256'],'manual_sha256':'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f','labels':labels,'evidence':evidence,'material_requests':decision.get('material_requests',[])}
 if decision.get('representation_override'):item['evidence'][decision['representation_override']['dimension']].update(decision['representation_override']['fields'])
 # First complete item is saved before mechanical validation, and never rewritten.
 p=xb('first-output/'+sid+'.json',item)
 scope=gate.prepare_scope(pk,os.environ['CODEX_THREAD_ID'],os.environ['CODEX_THREAD_ID'])
 views=gate.inventory_views(scope['source_inventory']);b=pk['source_bundle']
 def read(v,event,pointer,range_detail,use):
  rid='READ-'+sid+'-'+str(len(scope['read_receipts'])+1)
  r={k:v[k] for k in ['resource_id','source_sha256','view','view_sha256','scope_pointer']}
  r.update(receipt_id=rid,run_id=scope['run_id'],reader=scope['reader'],source_id=sid,locator_read=v['locator'],delivery_status='complete',read_attestation='recorded',tool_name='functions.exec/tools.exec_command' if v['view']!='image' else 'functions.exec/tools.view_image',event_id=event,local_event_id=sid+'-'+str(len(scope['read_receipts'])+1),visible_return_bytes=None,actual_range_or_page=range_detail)
  scope['read_receipts'].append(r)
  scope['use_receipts'].append({k:v[k] for k in ['resource_id','source_sha256','view','view_sha256','scope_pointer']}|{'use_status':'used' if use else 'not_used','read_receipt_id':rid if use else None,'use_scope':use or ''})
  return rid
 for req in scope['requirements']:
  v=views[gate.view_key(req)];rid=req['resource_id'];pointer=req['source_basis']['bundle_pointers'][0]
  if rid=='BODY-'+sid:range_detail={'bundle_pointer':'/source_record/text','unicode_span':{'start':0,'end':len(text)}}
  else:
   c=next(c for c in row['contexts'] if c['context_id']==rid)
   range_detail={'bundle_pointer':pointer,'complete_context_object':True,'view':req['view']}
  use='当前命题及原源关系范围审阅' if rid=='BODY-'+sid else '父子、标题、编号、限定及边界范围审阅；不继承兄弟内容'
  read(v,decision['read_event'],pointer,range_detail,use)
 for av in decision.get('additional_views',[]):
  scope['additional_views'].append(av)
 for x in decision.get('additional_requirements',[]):scope['requirements'].append(x)
 for x in decision.get('extra_reads',[]):read(x['view'],x['event'],x.get('pointer'),x['range'],x.get('use'))
 scope['reference_resolution']=decision.get('references',[])
 scope['source_requests']=decision.get('source_requests',[])
 scope['necessary_source_scope_review_status']='complete'
 scope['scope_source_basis']={'note':decision['scope_note'],'bundle_pointers':decision.get('scope_pointers',['/source_record','/source_record/contexts'])}
 scope['required_read_complete_claim']=decision.get('required_read_complete',True)
 xb('scopes/'+sid+'.json',scope)
 xb('decisions/'+sid+'.json',decision)
 print(json.dumps({'source_id':sid,'first_item_path':str(p),'labels':labels,'item_bytes':p.stat().st_size,'item_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},ensure_ascii=False))
 return item,scope
