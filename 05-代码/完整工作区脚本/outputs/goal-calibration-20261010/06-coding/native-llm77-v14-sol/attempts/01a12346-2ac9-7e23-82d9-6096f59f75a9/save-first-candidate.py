import pathlib,json,hashlib,uuid
p=pathlib.Path(__file__).parent
sid='RECODE25-04915'
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def save(path,value):
 raw=canonical(value)+b'\n'
 with path.open('xb') as f:f.write(raw)
 return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
rows=json.loads((p/'packet-identities.json').read_bytes())
x=next(x for x in rows if x['source_id']==sid)
packet=json.loads(pathlib.Path(x['packet_file']['path']).read_bytes());bundle=packet['source_bundle'];row=bundle['source_record']
index=json.loads(pathlib.Path(x['view_index_file']['path']).read_bytes());scope=json.loads((p/'prepared'/f'{sid}.json').read_bytes())
for d in ['first-output','scopes','source-quotes','events']: (p/d).mkdir(exist_ok=False)
read_ids={}
def receipt(binding,deliveries,key):
 events=[];end=0
 for d in deliveries:
  e=json.loads(d.read_bytes());m=json.loads(pathlib.Path(e['emission_file']).read_bytes())
  assert e['matching_BEGIN_END'] and not e['truncated'] and e['read_attestation']=='recorded' and m['start_byte']==end
  assert m['view_sha256']==binding['view_sha256']
  end=m['end_byte'];events.append({'delivery_file':str(d),'local_delivery_event_id':e['local_delivery_event_id'],'start_byte':m['start_byte'],'end_byte':end})
 assert m['view_EOF_after_this_chunk'] and end==m['view_total_UTF8_bytes']
 rid='READ-'+str(uuid.uuid4());local='READ-EVENT-'+str(uuid.uuid4())
 event={'local_event_id':local,'reader':p.name,'resource_id':binding['resource_id'],'source_sha256':binding['source_sha256'],'view':binding['view'],'view_sha256':binding['view_sha256'],'scope_pointer':binding.get('scope_pointer'),'original_locator':binding['locator'],'actual_contiguous_ranges':events,'complete_0_to_EOF':True,'image_pixels_read':False}
 save(p/'events'/(local+'.json'),event)
 scope['read_receipts'].append({'receipt_id':rid,'run_id':p.name,'reader':p.name,'source_id':sid,'resource_id':binding['resource_id'],'source_sha256':binding['source_sha256'],'view':binding['view'],'view_sha256':binding['view_sha256'],'scope_pointer':binding.get('scope_pointer'),'locator_read':binding['locator'],'delivery_status':'complete','read_attestation':'recorded','tool_name':'functions.exec / exec_command / source_view_chunk.py','event_id':None,'local_event_id':local,'visible_return_bytes':end,'actual_range_or_page':{'start_byte':0,'end_byte':end,'range_unit':'UTF8_byte','delivery_ranges':events,'original_bundle_pointer':binding.get('original_bundle_pointer')}})
 read_ids[key]=rid
 return rid
views=index['original_body_CTX_view_carriers']
for i,v in enumerate(views):
 actual={5:3,6:4}.get(i,i)
 d=p/(sid+'-view-'+str(actual)+'-000000-delivery.json')
 assert v['source_sha256']==views[actual]['source_sha256'] and v['view_sha256']==views[actual]['view_sha256'] and v['view']==views[actual]['view']
 receipt(v,[d],str(i))
public=bundle['explicit_or_primary_source_resources'][0]
inv=next(z for z in scope['source_inventory'] if z['resource_id']==public['source_resource_id'])
binding={'resource_id':inv['resource_id'],'source_sha256':inv['source_sha256'],'view':'document_bundle','view_sha256':inv['available_views']['document_bundle'],'scope_pointer':None,'locator':inv['locator'],'original_bundle_pointer':'/explicit_or_primary_source_resources/0'}
ptr='/explicit_or_primary_source_resources/0';key=hashlib.sha256(ptr.encode()).hexdigest()[:16]
receipt(binding,[p/(sid+'-leaf-'+key+'-'+str(start).zfill(6)+'-delivery.json') for start in [0,6000,11998]],'public')
public_req={'requirement_id':'REQ-PUBLIC-EXPLAINER-38-F','resource_id':binding['resource_id'],'view':'document_bundle','scope_pointer':None,'source_relation_kind':'necessary_role_or_scope_boundary','source_evidence_locator':binding['locator'],'source_basis':{'note':'当前县域中心药房、上下级用药衔接和偏远地区配送措施的目标问题需按同政策解释的直接问题—措施映射确定；只用EXP004、EXP007和EXP012解释本项，不移植兄弟措施。','bundle_pointers':['/source_record/text','/explicit_or_primary_source_resources/0/source_texts/3/text','/explicit_or_primary_source_resources/0/source_texts/6/text','/explicit_or_primary_source_resources/0/source_texts/11/text']},'dependency_dimensions':['F']}
scope['requirements'].append(public_req)
doc=bundle['source_documents'][0];ptr='/source_documents/0'
added={'resource_id':doc['source_resource_id'],'source_sha256':doc['source_sha256'],'view':'document_bundle','view_sha256':hashlib.sha256(canonical(doc)).hexdigest(),'scope_pointer':ptr,'locator':{'source_bundle_pointer':ptr},'encoding':'canonical_json'}
scope['additional_views'].append(added)
key=hashlib.sha256(ptr.encode()).hexdigest()[:16]
receipt({**added,'original_bundle_pointer':ptr},[p/(sid+'-leaf-'+key+'-000000-delivery.json')],'identity')
scope['requirements'].append({'requirement_id':'REQ-CURRENT-POLICY-38-IDENTITY','resource_id':added['resource_id'],'view':added['view'],'scope_pointer':ptr,'source_relation_kind':'necessary_role_or_scope_boundary','source_evidence_locator':added['locator'],'source_basis':{'note':'以原PDF抽取的实际标题与国卫药政发〔2024〕38号确认公共解释所说明的同一政策；不以文件名年份定版。','bundle_pointers':['/source_documents/0/source_title_lines_verbatim_extraction_candidates','/explicit_or_primary_source_resources/0/explained_policy_document_number','/explicit_or_primary_source_resources/0/explained_policy_title']},'dependency_dimensions':['F']})
scope['necessary_source_scope_review_status']='complete'
scope['scope_source_basis']={'note':'已完整读取当前正文、原段落及重复标题的原text/geometry视图，并绑定页7/p0007。当前为县域药房和偏远地区配送措施，父段其他安全、需求审核和采购清单内容不自动继承。公共解释EXP004的地域供应缺口、EXP007的目标和EXP012的同一措施用于有限补全。其余解释段落虽然随完整document_bundle实际读入，未用于标签。原图无必要依赖；无当前确指的未解法规条件。','bundle_pointers':['/source_record','/source_documents/0','/explicit_or_primary_source_resources/0']}
scope['reference_resolution']=[{'reference_id':'REL-SAME-POLICY-38-EXPLAINER','citation_literal':'关于改革完善基层药品联动管理机制 扩大基层药品种类的意见','source_basis':{'note':'源内原PDF标题/文号国卫药政发〔2024〕38号与解释的explained_policy_title/document_number一致；解释EXP012直接复述当前县域药房和偏远配送措施，EXP004/007说明对应问题。解释为官方转载HTML快照，不声称原在线二进制已认证。','bundle_pointers':['/source_documents/0/source_title_lines_verbatim_extraction_candidates','/explicit_or_primary_source_resources/0/explained_policy_title','/explicit_or_primary_source_resources/0/explained_policy_document_number','/explicit_or_primary_source_resources/0/source_texts/11/text']},'necessary_dependency':True,'dependency_dimensions':['F'],'resolution_status':'same_edition_confirmed','target_requirement_id':public_req['requirement_id'],'target_source_sha256':binding['source_sha256'],'identity_basis_pointers':['/source_documents/0/source_title_lines_verbatim_extraction_candidates','/explicit_or_primary_source_resources/0/document_title','/explicit_or_primary_source_resources/0/explained_policy_document_number','/explicit_or_primary_source_resources/0/explained_policy_title','/explicit_or_primary_source_resources/0/snapshot_sha256']}]
for r in scope['read_receipts']:
 use_scope='当前/CTX边界、原文及原页定位；不继承父段的全部维度。'
 if r['receipt_id']==read_ids['public']:use_scope='F仅使用EXP004、EXP007、EXP012的问题—当前措施关系与来源身份；其他公共全文段落未用于判断。'
 if r['receipt_id']==read_ids['identity']:use_scope='同一政策原文标题及文号身份核对，仅支持F的解释映射。'
 scope['use_receipts'].append({k:r[k] for k in ['resource_id','source_sha256','view','view_sha256','scope_pointer']}|{'use_status':'used','read_receipt_id':r['receipt_id'],'use_scope':use_scope})
scope['required_read_complete_claim']=True
quote_entries=[];quotes={}
for n in [3,6,11]:
 text=public['source_texts'][n]['text']
 q={'source_id':sid,'source_bundle_sha256':packet['source_bundle_sha256'],'bundle_pointer':f'/explicit_or_primary_source_resources/0/source_texts/{n}/text','quote':text,'span':{'start':0,'end':len(text)}}
 file=save(p/'source-quotes'/f'{sid}-EXP{n+1:03d}.json',q);quotes[n]=q
 quote_entries.append({'source_id':sid,'dimension':'F','quote_file':file,'purpose':'有限同政策问题—措施及身份映射','read_receipt_id':read_ids['public']})
save(p/'quote-index.json',{'entries':quote_entries})
text=row['text'];parent=row['contexts'][0]
def ctx(c,purpose):return {'context_id':c['context_id'],'field_path':'text','quote':c['text'],'span':{'start':0,'end':len(c['text'])},'purpose':purpose}
reasons={
'S':'当前建设药房、优化药品配送与用药衔接并降低供应成本，没有规定药物损害、风险识别或控制。父段另有质量安全内容，当前不承接其具体风险命题。',
'E':'当前药品供应和用药衔接属于供给安排，未讨论药物防治效果、临床获益或效果证据；不从治疗用途推定疗效。',
'Ec':'明确要求降低药品供应成本，直接涉及药品治疗供给所需资源和费用，属于实质经济安排。',
'I':'县域中心药房及配送方式优化是供给管理安排，没有药物技术新颖性、实质产品改良或创新研发对象—支持机会的直接关系。',
'F':'当前县域药房、上下级药品供应衔接和偏远地区配送措施，依同政策解释EXP004、EXP007、EXP012直接对应转诊患者在基层获取所需药品受限及中西部、偏远地区供应不稳定、时常断供的问题，属于纠正地域药品获取差异的具体关系。只补本项问题—措施映射，不继承其他措施或推定已经改善公平。'}
paths={'S':'excluded','E':'excluded','Ec':'Ec_treatment_payment_resource','I':'excluded','F':'F_specific'}
evidence={}
for dim in ['S','E','Ec','I','F']:
 evidence[dim]={'paths':[paths[dim]],'current_quote':text,'current_span':{'start':0,'end':len(text)},'contexts_used':[ctx(parent,'确认当前在同一药品集中供应配送段落中的适用对象及边界，其他措施不自动继承。'),ctx(row['contexts'][1],'确认本项属基层药品集中供应配送机制。')],'structural_context_ids_used':[],'image_sources_used':[],'reason':reasons[dim],'innovation_support':None,'fairness_specific':None}
current_anchor={'source_kind':'current','context_id':None,'field_path':'text','quote':text,'span':{'start':0,'end':len(text)}}
# The truthful public-source anchor is preserved in the first candidate even
# though the inherited current/context-only field cannot represent this source.
# No source_kind enum, context ID or original schema is altered or invented.
evidence['F']['fairness_specific']={'patient_drug_object':current_anchor,'fairness_relation':quotes[3],'arrangement_or_evaluation':current_anchor,'relation_type':'unequal_access'}
item={'blind_id':packet['output_id'],'content_sha256':packet['source_bundle_sha256'],'manual_sha256':'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f','labels':{'S':0,'E':0,'Ec':1,'I':0,'F':1},'evidence':evidence,'material_requests':[]}
save(p/'first-output'/f'{sid}.json',item)
save(p/'whole-output.json',{'items':[item]})
manifest=[]
for x in rows:
 s=scope if x['source_id']==sid else json.loads((p/'prepared'/(x['source_id']+'.json')).read_bytes())
 entry=save(p/'scopes'/(x['source_id']+'.json'),s)
 manifest.append({'source_id':x['source_id'],'path':entry['path'],'sha256':entry['sha256']})
save(p/'scope-manifest.json',{'scope_log_files':manifest})
save(p/'technical-representation-failure.json',{'state':'technical_representation_failed','source_id':sid,'dimension':'F','field':'evidence.F.fairness_specific.fairness_relation','actual_source_kind':'public-source document_bundle / original source_texts[3].text','actual_source_quote_file':quote_entries[0]['quote_file'],'schema_boundary':'This inherited anchor permits only source_kind=current/context plus context_id/field_path. The fairness relationship is in the public same-policy explainer, not current text or an original CTX. A truthful source-quote anchor was preserved in the candidate without inventing an enum or relabeling it as CTX; the candidate therefore cannot pass the inherited output schema.','schema_modified':False,'source_missing':False,'labels_changed_to_hide_boundary':False,'batch_stopped_immediately':True,'completed_first_candidate_count':1,'expected_batch_count':10,'unprocessed_source_ids':[x['source_id'] for x in rows[1:]]})
print(json.dumps({'saved_first_candidate':str(p/'first-output'/f'{sid}.json'),'whole_output':str(p/'whole-output.json'),'candidate_items':1,'state':'technical_representation_failed'},ensure_ascii=False))
