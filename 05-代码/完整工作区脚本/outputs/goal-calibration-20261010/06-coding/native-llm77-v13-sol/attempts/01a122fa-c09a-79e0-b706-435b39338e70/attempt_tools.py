import json, pathlib, sys, hashlib, os
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/protocol-necessary-read-v4')
import necessary_read_gate as gate

def write_new(name, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    with (ROOT / name).open('xb') as f:
        f.write(data)

def packet(suffix):
    sid = 'RECODE25-' + suffix
    entry = next(e for e in json.loads((ROOT/'batch-index.json').read_text()) if e['source_id'] == sid)
    return json.loads(pathlib.Path(entry['complete_packet_file']['path']).read_text())

def anchor(p, quote, context_index=None):
    if context_index is None:
        text=p['source_bundle']['source_record']['text']; cid=None; path='text'; kind='current'
    else:
        c=p['source_bundle']['source_record']['contexts'][context_index];text=c['text'];cid=c['context_id'];path='text';kind='context'
    start=text.index(quote)
    return {'source_kind':kind,'context_id':cid,'field_path':path,'quote':quote,'span':{'start':start,'end':start+len(quote)}}

def context_quote(p, index, purpose, quote=None):
    c=p['source_bundle']['source_record']['contexts'][index];t=c['text'];q=t if quote is None else quote;start=t.index(q)
    return {'context_id':c['context_id'],'field_path':'text','quote':q,'span':{'start':start,'end':start+len(q)},'purpose':purpose}

def item(p, labels, paths, reasons, contexts=None, support=None, fairness=None, structural=None, images=None, requests=None):
    t=p['source_bundle']['source_record']['text']; evidence={}
    for dim in gate.DIMENSIONS:
        evidence[dim]={'paths':paths.get(dim,['excluded']),'current_quote':t,'current_span':{'start':0,'end':len(t)},'contexts_used':(contexts or {}).get(dim,[]),'structural_context_ids_used':structural or [],'image_sources_used':images or [],'reason':reasons[dim],'innovation_support':support if dim=='I' else None,'fairness_specific':fairness if dim=='F' else None}
    return {'blind_id':p['output_id'],'content_sha256':p['source_bundle_sha256'],'manual_sha256':'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f','labels':dict(zip(gate.DIMENSIONS,labels)),'evidence':evidence,'material_requests':requests or []}

def base_scope(p, event_id, note, pointers=None):
    s=gate.prepare_scope(p,ROOT.name,ROOT.name);s['necessary_source_scope_review_status']='complete';s['scope_source_basis']={'note':note,'bundle_pointers':pointers or ['/source_record']}
    views=gate.inventory_views(s['source_inventory'])
    for req in s['requirements']:
        v=views[gate.view_key(req)];rid=v['resource_id'];view=v['view']
        if rid.startswith('BODY-'):t=p['source_bundle']['source_record']['text'];ran={'unicode_codepoints':[0,len(t)]}
        else:
            c=next(c for c in p['source_bundle']['source_record']['contexts'] if c['context_id']==rid)
            if view=='text': t=c['text'];ran={'unicode_codepoints':[0,len(t)]}
            else:ran={'complete_json_pointer': '/source_record/contexts/'+str(p['source_bundle']['source_record']['contexts'].index(c))+'/structure'}
        rec={'receipt_id':'READ-'+req['requirement_id'],'run_id':ROOT.name,'reader':ROOT.name,'source_id':p['source_id'],'resource_id':rid,'source_sha256':v['source_sha256'],'view':view,'view_sha256':v['view_sha256'],'scope_pointer':None,'locator_read':v['locator'],'delivery_status':'complete','read_attestation':'recorded','tool_name':'functions.exec/tools.exec_command','event_id':event_id,'local_event_id':None,'visible_return_bytes':None,'actual_range_or_page':ran}
        s['read_receipts'].append(rec)
        s['use_receipts'].append({'resource_id':rid,'source_sha256':v['source_sha256'],'view':view,'view_sha256':v['view_sha256'],'scope_pointer':None,'use_status':'used','read_receipt_id':rec['receipt_id'],'use_scope':'当前完整命题、原 CTX 结构/正文的身份、共同谓词和有限适用范围审阅；不继承无关兄弟内容。'})
    s['required_read_complete_claim']=True
    return s

def save_first(p, it, scope):
    write_new('first-output/'+p['source_id']+'.json',it)
    write_new('scopes/'+p['source_id']+'.json',scope)

def add_original_object(s,p,pointer,event_id,relation,dimensions,note,reference=None):
    obj=gate.pointer_value(p['source_bundle'],pointer);rid=obj['source_resource_id'];sha=obj.get('source_sha256',obj.get('source_pdf_sha256'))
    digest=hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();locator={'source_bundle_pointer':pointer}
    v={'resource_id':rid,'source_sha256':sha,'view':'document_bundle','view_sha256':digest,'scope_pointer':pointer,'locator':locator,'encoding':'canonical_json'};s['additional_views'].append(v)
    reqid='ADDED-'+hashlib.sha256(pointer.encode()).hexdigest()[:20];basis={'note':note,'bundle_pointers':['/source_record',pointer]}
    s['requirements'].append({'requirement_id':reqid,'resource_id':rid,'view':v['view'],'scope_pointer':pointer,'source_relation_kind':relation,'source_evidence_locator':locator,'source_basis':basis,'dependency_dimensions':dimensions})
    receipt='READ-'+reqid
    s['read_receipts'].append({'receipt_id':receipt,'run_id':ROOT.name,'reader':ROOT.name,'source_id':p['source_id'],'resource_id':rid,'source_sha256':sha,'view':v['view'],'view_sha256':digest,'scope_pointer':pointer,'locator_read':locator,'delivery_status':'complete','read_attestation':'recorded','tool_name':'functions.exec/tools.exec_command','event_id':event_id,'local_event_id':None,'visible_return_bytes':None,'actual_range_or_page':{'complete_original_json_object':pointer}})
    s['use_receipts'].append({'resource_id':rid,'source_sha256':sha,'view':v['view'],'view_sha256':digest,'scope_pointer':pointer,'use_status':'used','read_receipt_id':receipt,'use_scope':note})
    if reference:s['reference_resolution'].append({'reference_id':'REF-'+reqid,'citation_literal':reference,'source_basis':basis,'necessary_dependency':True,'dependency_dimensions':dimensions,'resolution_status':'exact_snapshot','target_requirement_id':reqid,'target_source_sha256':sha,'identity_basis_pointers':[pointer+'/source_sha256','/source_record/source_ref/sha256']})
    return receipt

def source_quote(p,pointer,quote=None):
    t=gate.pointer_value(p['source_bundle'],pointer);q=t if quote is None else quote;start=t.index(q)
    return {'source_id':p['source_id'],'source_bundle_sha256':p['source_bundle_sha256'],'bundle_pointer':pointer,'quote':q,'span':{'start':start,'end':start+len(q)}}
