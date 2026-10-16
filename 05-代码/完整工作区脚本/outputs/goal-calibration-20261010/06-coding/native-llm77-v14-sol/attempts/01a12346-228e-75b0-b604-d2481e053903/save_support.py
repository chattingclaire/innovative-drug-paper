import pathlib,json,os,hashlib,uuid
A=pathlib.Path(__file__).parent;RUN=os.environ['CODEX_THREAD_ID'];DIMS=['S','E','Ec','I','F']
def save(path,obj):
 raw=(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 with pathlib.Path(path).open('xb') as f:f.write(raw)
 return hashlib.sha256(raw).hexdigest()
def context_quote(packet,i,purpose):
 c=packet['source_bundle']['source_record']['contexts'][i];t=c['text'];return {'context_id':c['context_id'],'field_path':'text','quote':t,'span':{'start':0,'end':len(t)},'purpose':purpose}
def anchor(t,kind='current',cid=None,field='text'):
 return {'source_kind':kind,'context_id':cid,'field_path':field,'quote':t,'span':{'start':0,'end':len(t)}}
def evidence(packet,paths,reason,contexts=[],innovation=None,fairness=None,structural=[]):
 t=packet['source_bundle']['source_record']['text'];return {'paths':paths,'current_quote':t,'current_span':{'start':0,'end':len(t)},'contexts_used':contexts,'structural_context_ids_used':structural,'image_sources_used':[],'reason':reason,'innovation_support':innovation,'fairness_specific':fairness}
def base_scope(sid,used):
 sc=json.loads((A/'prepared-scopes'/(sid+'.json')).read_text());q=json.loads((A/'base-view-queue.json').read_text())
 for i,x in enumerate(q):
  bs=[b for b in x['bindings'] if b['source_id']==sid]
  if not bs:continue
  es=[A/'RECODE25-00902-v000-000000-emission.json'] if i==0 else sorted(A.glob('base-q'+str(i).zfill(3)+'-*-emission.json'))
  ms=[json.loads(e.read_text()) for e in es];ds=[e.with_name(e.stem.replace('-emission','')+'-delivery.json') for e in es]
  assert ms and ms[0]['start_byte']==0 and ms[-1]['view_EOF_after_this_chunk'] and all(d.exists() for d in ds)
  assert all(a['end_byte']==b['start_byte'] for a,b in zip(ms,ms[1:]))
  for b in bs:
   rid='READ-'+str(uuid.uuid4());last=json.loads(ds[-1].read_text())
   rr={'receipt_id':rid,'run_id':RUN,'reader':RUN,'source_id':sid,'resource_id':b['resource_id'],'source_sha256':x['source_sha256'],'view':x['view'],'view_sha256':x['view_sha256'],'scope_pointer':b['scope_pointer'],'locator_read':b['locator'],'delivery_status':'complete','read_attestation':'recorded','tool_name':'functions.exec/exec_command/source_view_chunk.py','event_id':None,'local_event_id':last['local_delivery_event_id'],'visible_return_bytes':sum(m['program_stdout_bytes_written'] for m in ms),'actual_range_or_page':{'view_utf8_byte_range':[0,ms[-1]['end_byte']],'delivery_files':[str(d) for d in ds],'emission_files':[str(e) for e in es],'original_bundle_pointer':b['original_bundle_pointer']}}
   sc['read_receipts'].append(rr)
   if (b['resource_id'],x['view']) in used:sc['use_receipts'].append({'resource_id':b['resource_id'],'source_sha256':x['source_sha256'],'view':x['view'],'view_sha256':x['view_sha256'],'scope_pointer':b['scope_pointer'],'use_status':'used','read_receipt_id':rid,'use_scope':used[(b['resource_id'],x['view'])]})
 return sc
