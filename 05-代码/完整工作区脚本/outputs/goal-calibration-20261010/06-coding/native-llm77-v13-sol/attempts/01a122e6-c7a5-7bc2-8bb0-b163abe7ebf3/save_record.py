import os, sys, json, hashlib
from pathlib import Path
BASE = Path('/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding')
ATTEMPT = BASE / 'native-llm77-v13-sol/attempts' / os.environ['CODEX_THREAD_ID']
sys.path.insert(0, str(BASE / 'protocol-necessary-read-v4'))
import necessary_read_gate as gate
import packet_builder as pb
INDEX = json.loads((ATTEMPT / 'batch-source-index.json').read_bytes())
def exclusive(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8')
    with path.open('xb') as f: f.write(raw)
def packet(source_id):
    e = next(e for e in INDEX if e['source_id'] == source_id)
    return json.loads(Path(e['complete_packet_file']['path']).read_bytes())
def context_quote(p, i, purpose):
    c = p['source_bundle']['source_record']['contexts'][i]
    field = next(k for k in ['text','title','caption'] if isinstance(c.get(k), str) and c[k])
    text = c[field]
    return {'context_id':c['context_id'],'field_path':field,'quote':text,'span':{'start':0,'end':len(text)},'purpose':purpose}
def anchor_current(p):
    text = p['source_bundle']['source_record']['text']
    return {'source_kind':'current','context_id':None,'field_path':'text','quote':text,'span':{'start':0,'end':len(text)}}
def anchor_context(p, i, field='text'):
    c = p['source_bundle']['source_record']['contexts'][i]; text = c[field]
    return {'source_kind':'context','context_id':c['context_id'],'field_path':field,'quote':text,'span':{'start':0,'end':len(text)}}
def save_record(source_id, decisions, event_id, scope_note, context_uses=None, structural_uses=None, images=None, support=None, fairness=None, extra=None):
    p = packet(source_id); row=p['source_bundle']['source_record']; u=os.environ['CODEX_THREAD_ID']
    scope=gate.prepare_scope(p,u,u)
    scope['necessary_source_scope_review_status']='complete'
    scope['scope_source_basis']={'note':scope_note,'bundle_pointers':['/source_record'] + (extra or {}).get('basis_pointers',[])}
    views=gate.inventory_views(scope['source_inventory'])
    for req in scope['requirements']:
        v=views[gate.view_key(req)]
        rid='READ-'+pb.sha((source_id+':'+req['requirement_id']).encode())[:20]
        scope['read_receipts'].append({'receipt_id':rid,'run_id':u,'reader':u,'source_id':source_id,'resource_id':v['resource_id'],'source_sha256':v['source_sha256'],'view':v['view'],'view_sha256':v['view_sha256'],'scope_pointer':v.get('scope_pointer'),'locator_read':v['locator'],'delivery_status':'complete','read_attestation':'recorded','tool_name':'functions.exec/exec_command (python3 source_record display)','event_id':event_id,'local_event_id':'source-record-'+source_id+'-'+event_id,'visible_return_bytes':None,'actual_range_or_page':{'scope':'complete current text / complete preserved CTX view','bundle_pointer':req['source_basis']['bundle_pointers'][0]}})
        scope['use_receipts'].append({'resource_id':v['resource_id'],'source_sha256':v['source_sha256'],'view':v['view'],'view_sha256':v['view_sha256'],'scope_pointer':v.get('scope_pointer'),'use_status':'used','read_receipt_id':rid,'use_scope':'当前命题及原CTX父子、编号、限定与边界核对；不继承兄弟项标签。'})
    if extra:
        for k in ['additional_views','requirements','reference_resolution','read_receipts','use_receipts','source_requests']:
            scope[k].extend(extra.get(k,[]))
    scope['required_read_complete_claim']=not scope['source_requests']
    item={'blind_id':p['output_id'],'content_sha256':p['source_bundle_sha256'],'manual_sha256':'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f','labels':{},'evidence':{},'material_requests':(extra or {}).get('material_requests',[])}
    for d,(label,paths,reason) in decisions.items():
        item['labels'][d]=label
        item['evidence'][d]={'paths':paths,'current_quote':row['text'],'current_span':{'start':0,'end':len(row['text'])},'contexts_used':[context_quote(p,i,purpose) for i,purpose in (context_uses or {}).get(d,[])],'structural_context_ids_used':[row['contexts'][i]['context_id'] for i in (structural_uses or {}).get(d,[])],'image_sources_used':(images or {}).get(d,[]),'reason':reason,'innovation_support':support if d=='I' else None,'fairness_specific':fairness if d=='F' else None}
    exclusive(ATTEMPT/'first-output'/f'{source_id}.json',item)
    exclusive(ATTEMPT/'scopes'/f'{source_id}.json',scope)
    exclusive(ATTEMPT/'events'/f'{source_id}-source-record.json',{'event_id':event_id,'local_event_id':'source-record-'+source_id+'-'+event_id,'tool_name':'functions.exec/exec_command','saved_payload_kind':'source_record JSON displayed by the tool; not provider wire response','complete_visible_source_record':row})
    return item
