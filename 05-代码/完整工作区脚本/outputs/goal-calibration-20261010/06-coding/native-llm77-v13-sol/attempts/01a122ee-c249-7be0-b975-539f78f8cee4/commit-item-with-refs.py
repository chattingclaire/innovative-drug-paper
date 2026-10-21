from pathlib import Path
import json,sys,hashlib
ROOT=Path('/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding')
A=Path(__file__).resolve().parent
RUN=A.name
sys.path.insert(0,str(ROOT/'protocol-necessary-read-v4'))
import necessary_read_gate as gate
def write(name,value):
    b=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with (A/name).open('xb') as f:f.write(b)
    return {'path':str(A/name),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
decision=json.loads(sys.stdin.read())
sid=decision['source_id']
packet=json.loads((ROOT/'development77-native-inputs-v3/packets'/f'{sid}.compact.json').read_bytes())
row=packet['source_bundle']['source_record']
scope=gate.prepare_scope(packet,RUN,RUN)
scope['necessary_source_scope_review_status']='complete'
scope['scope_source_basis']={'note':decision['scope_note'],'bundle_pointers':decision.get('scope_pointers',['/source_record/text','/source_record/contexts'])}
byid={x['resource_id']:x for x in scope['source_inventory']}
for req in scope['requirements']:
    v=byid[req['resource_id']]
    cid=req['resource_id']
    if req['view']=='text':
        content=row['text'] if cid.startswith('BODY-') else next(c['text'] for c in row['contexts'] if c['context_id']==cid)
        actual={'unit':'Unicode codepoints','start':0,'end':len(content),'full_view':True}
    else:
        ctx=next(c for c in row['contexts'] if c['context_id']==cid)
        actual={'full_original_structure':True,'bundle_pointer':'/source_record/contexts/'+str(row['contexts'].index(ctx))+'/structure'}
    receipt={'receipt_id':'READ-'+cid+'-'+req['view'],'run_id':RUN,'reader':RUN,'source_id':sid,'resource_id':cid,'source_sha256':v['source_sha256'],'view':req['view'],'view_sha256':v['available_views'][req['view']],'scope_pointer':None,'locator_read':v['locator'],'delivery_status':'complete','read_attestation':'recorded','tool_name':'exec_command','event_id':decision['read_event_id'],'local_event_id':'packet-read-'+sid.split('-')[1],'visible_return_bytes':None,'actual_range_or_page':actual}
    scope['read_receipts'].append(receipt)
    scope['use_receipts'].append({'resource_id':cid,'source_sha256':receipt['source_sha256'],'view':receipt['view'],'view_sha256':receipt['view_sha256'],'scope_pointer':None,'use_status':'used','read_receipt_id':receipt['receipt_id'],'use_scope':'当前内容及完整保留CTX的对象、父子关系、共同谓词、限定与边界审阅。'})
for image in decision.get('images',[]):
    v=byid[image['resource_id']]
    req={'requirement_id':'REQ-IMAGE-'+image['resource_id'],'resource_id':image['resource_id'],'view':'image','scope_pointer':None,'source_relation_kind':'necessary_original_image','source_evidence_locator':v['locator'],'source_basis':{'note':image['basis'],'bundle_pointers':image['pointers']},'dependency_dimensions':image.get('dimensions',list(gate.DIMENSIONS))}
    scope['requirements'].append(req)
    receipt={'receipt_id':'READ-'+image['resource_id']+'-image','run_id':RUN,'reader':RUN,'source_id':sid,'resource_id':v['resource_id'],'source_sha256':v['source_sha256'],'view':'image','view_sha256':v['available_views']['image'],'scope_pointer':None,'locator_read':v['locator'],'delivery_status':'complete','read_attestation':'recorded','tool_name':'view_image','event_id':image.get('event_id'),'local_event_id':image['local_event_id'],'visible_return_bytes':None,'actual_range_or_page':{'physical_page':v['locator'].get('physical_page'),'full_original_image':True,'detail':'original'}}
    scope['read_receipts'].append(receipt)
    scope['use_receipts'].append({'resource_id':v['resource_id'],'source_sha256':v['source_sha256'],'view':'image','view_sha256':receipt['view_sha256'],'scope_pointer':None,'use_status':'used','read_receipt_id':receipt['receipt_id'],'use_scope':image['basis']})
for ref in decision.get('references',[]):
    target=next(r for r in scope['requirements'] if r['resource_id']==ref['target_resource_id'] and r['view']==ref.get('target_view','text'))
    scope['reference_resolution'].append({'reference_id':ref['reference_id'],'citation_literal':ref['citation_literal'],'source_basis':{'note':ref['basis'],'bundle_pointers':ref['basis_pointers']},'necessary_dependency':True,'dependency_dimensions':ref.get('dimensions',list(gate.DIMENSIONS)),'resolution_status':ref['resolution_status'],'target_requirement_id':target['requirement_id'],'target_source_sha256':byid[ref['target_resource_id']]['source_sha256'],'identity_basis_pointers':ref['identity_pointers']})
scope['required_read_complete_claim']=True
item={'blind_id':packet['output_id'],'content_sha256':packet['source_bundle_sha256'],'manual_sha256':'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f','labels':decision['labels'],'evidence':{},'material_requests':decision.get('material_requests',[])}
for d in gate.DIMENSIONS:
    spec=decision['evidence'][d]; contexts=[]
    for idx in spec.get('contexts',[]):
        c=row['contexts'][idx]; quote=c['text']
        contexts.append({'context_id':c['context_id'],'field_path':'text','quote':quote,'span':{'start':0,'end':len(quote)},'purpose':spec.get('context_purpose','确认当前对象、共同谓词及有限适用范围；兄弟项不移植。')})
    item['evidence'][d]={'paths':spec['paths'],'current_quote':row['text'],'current_span':{'start':0,'end':len(row['text'])},'contexts_used':contexts,'structural_context_ids_used':[row['contexts'][i]['context_id'] for i in spec.get('structural',[])],'image_sources_used':[x['resource_id'] for x in decision.get('images',[]) if d in x.get('dimensions',list(gate.DIMENSIONS))],'reason':spec['reason'],'innovation_support':spec.get('innovation_support'),'fairness_specific':spec.get('fairness_specific')}
print(json.dumps({'first_output':write('first-output/'+sid+'.json',item),'scope':write('scopes/'+sid+'.json',scope),'decision':write('events/decision-'+sid+'.json',decision)},ensure_ascii=False))

