"""Retain coverage source projection v1; add verified source geometry and repair IDs only in v2."""
from pathlib import Path
import copy,hashlib,json,os
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
def shafile(p):return sha(Path(p).read_bytes())
def dumps(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def save(p,o):
 b=(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode();p=Path(p)
 if p.exists():assert p.read_bytes()==b,'Existing version differs: '+str(p)
 else:p.write_bytes(b)
def refs(x):
 if isinstance(x,dict):
  for v in x.values():yield from refs(v)
 elif isinstance(x,list):
  for v in x:yield from refs(v)
 elif isinstance(x,str) and x.startswith('CTX-'):yield x
oldpath=OUT/'canonical_source_context.jsonl';oldhash=shafile(oldpath);assert oldhash=='87cbeabb11895584eb5cdb3be0b51e04beb8f14d76da6c9c1401eb92d423ac1f'
old=[json.loads(x) for x in oldpath.read_text().splitlines()];new=copy.deepcopy(old);byid={r['id']:r for r in new}
a=json.loads((OUT/'projection-audit.json').read_text());parent_path=OUT/'source-review-parent/source-review.json';child_path=OUT/'source-review-child/source-review.json'
assert shafile(parent_path)=='932f7eda34ab68c2ff957b94423aab710cee5abe350d61bade3ca66fd53602d5';assert shafile(child_path)=='21206612578d5f227c1262917477d70c5964cea1e37db8ff2a3bcba113f50b80'
parent=json.loads(parent_path.read_text());child=json.loads(child_path.read_text());reviews=parent['checked_context_occurrences']+child['checked_context_occurrences'];rm={(r['record_id'],r['context_id'],r['field']):r for r in reviews};assert len(rm)==19
assert set(rm)=={(r['record_id'],r['context_id'],r['field']) for r in a['unresolved']}
manifest=json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text());bs={r['sha256']:r for r in manifest['files']}
selection_path=ROOT/'04-calibration/coverage01/admin/selection.json';selection=json.loads(selection_path.read_text());ids={r['frame_id'] for r in selection['records']};exposure=json.loads((ROOT/'01-review/exposure-ids.json').read_text());assert len(ids)==36 and ids<=set(exposure['direct_exposure_ids']) and ids==set(byid)
changes=[];attachments={}
def page_attachment(rid,p):
 assert shafile(p['path'])==p['sha256']
 return {'attachment_id':'SOURCEPAGE-'+p['sha256'][:20],'sha256':p['sha256'],'relative_path':os.path.relpath(p['path'],OUT),'source_pdf_sha256':p['source_pdf_sha256'],'physical_page':p['physical_page']}
for rv in parent['checked_context_occurrences']:
 rid,cid=rv['record_id'],rv['context_id'];node=next(n for n in byid[rid]['contexts'] if n['context_id']==cid)
 assert sha(node['text'].encode())==rv['projected_text_sha256'];assert shafile(rv['source_snapshot'])==rv['source_sha256']
 for pg in rv['source_page_evidence']:
  at=page_attachment(rid,pg);attachments[(rid,at['attachment_id'])]=at
 if rv['source_identity_correction_required']:
  container=node['structure']['parent_context_id'];correctsha=rv['source_sha256']
  for target in [node,next(n for n in byid[rid]['contexts'] if n['context_id']==container)]:
   before=copy.deepcopy(target);target['source_document']='D-'+correctsha[:16];target['source_ref']['sha256']=correctsha
   target['source_ref']['locator']['physical_pages']=rv['physical_pages']
   changes.append({'record_id':rid,'context_id':target['context_id'],'operation':'repair_inherited_source_document_binding','before_source_document':before['source_document'],'after_source_document':target['source_document'],'before_source_sha256':before['source_ref']['sha256'],'after_source_sha256':correctsha,'source_snapshot':rv['source_snapshot'],'source_anchor':rv['source_anchor'],'physical_pages':rv['physical_pages'],'policy_text_unchanged':True,'original_context_ID_and_structure_preserved':True})
for rv in child['checked_context_occurrences']:
 rid,cid=rv['record_id'],rv['context_id'];node=next(n for n in byid[rid]['contexts'] if n['context_id']==cid);assert sha(node['text'].encode())==rv['projected_text_sha256']
 if 'page_evidence_file' in rv['locator']:
  pg=next(p for p in child['page_evidence'] if p['path']==rv['locator']['page_evidence_file']);at=page_attachment(rid,pg);attachments[(rid,at['attachment_id'])]=at
for row in new:
 newats=[v for (rid,_),v in attachments.items() if rid==row['id']]
 if newats:row['source_page_attachments']=newats
# Full original table image is a source attachment, with verified local bytes; no new download is claimed.
table_review=child['table_structure_review'];table_image=table_review['source_table_image'];table_html=table_review['source_HTML'];assert shafile(table_image['path'])==table_image['actual_sha256'];assert shafile(table_html['path'])==table_html['actual_sha256']
assets=OUT/'source-assets';assets.mkdir(exist_ok=True);asset_entries=[]
for src,tag in [(table_image,'data-protection-2026-table1.jpg'),(table_html,'data-protection-2026-host-page.html')]:
 dest=assets/(src['actual_sha256'][:16]+'-'+tag);b=Path(src['path']).read_bytes()
 if dest.exists():assert dest.read_bytes()==b
 else:dest.write_bytes(b)
 asset_entries.append({'original_path':src['path'],'snapshot':str(dest),'sha256':src['actual_sha256'],'bytes':len(b),'matches_recorded_source_identity':True,'online_binary_authenticated':False})
image_dest=Path(asset_entries[0]['snapshot']);jsonsha='09d813b3014db4137d2bceab8bc280c396a5916fafa7bb4c216c5798ae824d06';structured=json.loads(Path(bs[jsonsha]['snapshot']).read_text());t=structured['tables'][0]
assert t['group_context']['5类']=='境外上市的药品申请在境内上市' and t['source_sha256']==table_image['actual_sha256']
rid='RECODE25-01423';row=byid[rid];table=next(n for n in row['contexts'] if n['context_id']=='CTX-f769d2ca1a95e0a2bf81');prior=next(n for n in row['contexts'] if n['context_id']=='CTX-782289e75422f0bf09a4')
old_kind=prior['kind'];prior['kind']='preceding_flattened_table_data_row';prior['source_ref']['locator'].update({'json_pointer':'/tables/0/rows/3','physical_grid_row_index_zero_based':4})
changes.append({'record_id':rid,'context_id':prior['context_id'],'operation':'make_source_relation_kind_explicit','before_kind':old_kind,'after_kind':prior['kind'],'source_fact':'4类 is the previous flattened data row. A physical 5类 group row lies between it and the current5.1 subrow.','text_unchanged':True})
gcid='CTX-SRCV2-'+sha((table_image['actual_sha256']+'/grid_row5').encode())[:20]
gnode={'context_id':gcid,'kind':'table_group_row','source_document':'D-'+jsonsha[:16],'structure':{'parent_context_id':table['context_id'],'physical_grid_row_index_zero_based':5,'column_indices':[0,1,2,3]},'text':'5类 | 境外上市的药品申请在境内上市','row_cells':['5类','境外上市的药品申请在境内上市','',''],'source_ref':{'sha256':jsonsha,'locator':{'json_pointer':'/tables/0/group_context/5类','source_image_sha256':table_image['actual_sha256'],'physical_grid_row_index_zero_based':5}}}
row['contexts'].append(gnode)
geometry={'physical_grid_row_index_zero_based':6,'grid_row_index_convention':'0 denotes the header row; physical rows retain merged-cell geometry','physical_merged_cells':[{'text':'5.1','column_index':0,'physical_grid_row_start_zero_based':6,'physical_grid_row_span':2,'physical_grid_column_span':1},{'text':'境外上市的药品申请在境内上市','column_index':1,'physical_grid_row_start_zero_based':5,'physical_grid_row_span':1,'physical_grid_column_span':2}],'source_group_context_id':gcid,'source_image_sha256':table_image['actual_sha256']}
table['structure'].update(geometry);table['source_ref']['locator'].update(copy.deepcopy(geometry));row['source_image_attachments']=[{'attachment_id':'SOURCEIMAGE-'+table_image['actual_sha256'][:20],'sha256':table_image['actual_sha256'],'relative_path':str(image_dest.relative_to(OUT)),'source_url':table_image['URL'],'mime_type':'image/jpeg'}]
changes.append({'record_id':rid,'context_id':table['context_id'],'operation':'add_verified_original_table_geometry','additive_structure':geometry,'all_original_source_fields_retained':True,'column_header_and_selected_row_pairing_unchanged':True,'new_context_node':gnode,'source_image_snapshot':str(image_dest),'source_image_sha256':table_image['actual_sha256']})
# Recursive original/new CTX closure; source refs are checked too.
dangling=[]
for row in new:
 cids={n['context_id'] for n in row['contexts']};assert len(cids)==len(row['contexts'])
 for node in row['contexts']:
  for ref in refs(node):
   if ref not in cids:dangling.append([row['id'],node['context_id'],ref])
assert not dangling
forbidden=set(a['recursive_forbidden_result_key_check']['forbidden_keys']);bad=[]
def check(x,p=''):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in forbidden:bad.append(p+'/'+k)
   check(v,p+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):check(v,p+'/'+str(i))
check(new);assert not bad
assert all(before['text']==after['text'] for before,after in zip(old,new))
oldc={(r['id'],n['context_id']):n for r in old for n in r['contexts']};newc={(r['id'],n['context_id']):n for r in new for n in r['contexts']};assert set(oldc)<set(newc)
for key,n in oldc.items():
 for k in ['text','headers','title','row_cells','caption']:
  if k in n:assert n[k]==newc[key][k]
assert shafile(oldpath)==oldhash
newpath=OUT/'canonical_source_context-v2.jsonl';b=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in new).encode()
if newpath.exists():assert newpath.read_bytes()==b
else:newpath.write_bytes(b)
log={'v1_preserved':{'path':str(oldpath),'sha256':oldhash},'v2':{'path':str(newpath),'sha256':shafile(newpath)},'existing_unit_and_source_text_fields_unchanged':True,'old_context_N':171,'new_context_N':172,'original_context_IDs_and_nodes_retained':True,'old_textless_context_N':13,'new_textless_context_N':13,'source_binding_correction_node_N':4,'source_relation_kind_correction_N':1,'new_table_group_row_N':1,'source_table_geometry_addition_N':1,'changes':changes,'initial_pilot_inputs_modified':False,'labels_read':False,'human_coding':False}
save(OUT/'source-context-changes-v2.json',log);save(OUT/'additional-source-assets-manifest-v2.json',{'reason':'Archived structured table source records original image+HTML; snapshot and verify those exact existing source bytes for full neutral source geometry.','files':asset_entries})
# Audit original context provenance and all 19 issue-specific evidence without discarding failures.
rev=copy.deepcopy(a);rev.update({'status':'coverage01_v2_source_projection_source_specific_review_complete','output':log['v2'],'v1_preserved':log['v1_preserved'],'unresolved':[],'context_ID_strategy':'Original CTX IDs retained; one deterministic new source group-row node; all recursive CTX links checked','all_original_context_nodes_retained':True,'all_original_policy_text_fields_byte_equivalent':True,'all_original_source_structure_and_context_IDs_unchanged':False,'source_only_revision_log':{'path':str(OUT/'source-context-changes-v2.json'),'sha256':shafile(OUT/'source-context-changes-v2.json')},'source_specific_review_inputs':[{'path':str(parent_path),'sha256':shafile(parent_path)},{'path':str(child_path),'sha256':shafile(child_path)}],'additional_source_assets_manifest':{'path':str(OUT/'additional-source-assets-manifest-v2.json'),'sha256':shafile(OUT/'additional-source-assets-manifest-v2.json')},'reviewed_pending_text_field_N':19,'policy_dimension_judgment_performed':False,'manual_hints_visible':False,'recursive_forbidden_result_key_check':{'forbidden_keys':sorted(forbidden),'violations':bad,'count':0},'dangling_context_references':dangling,'selection_before_reading_source_text':{'path':str(selection_path),'sha256':shafile(selection_path),'same_36_IDs':True,'all_prior_direct_exposed':True,'final_holdout_consumed_N':0}})
rev['counts']['contexts']=172;rev['counts']['policy_leaves']=171;rev['counts']['source_identity_resolved']=172;rev['counts']['unresolved_literal_or_source_issues']=0;rev['counts']['source_specific_review_resolved_policy_fields']=19
for record in rev['context_provenance']:
 key=(record['record_id'],record['context_id'],'text')
 if key in rm:record['source_specific_review_v2']=rm[key]
 if (record['record_id'],record['context_id']) in newc:
  node=newc[(record['record_id'],record['context_id'])]
  if node['source_ref']['sha256']!=record.get('source_sha256'):
   source=bs[node['source_ref']['sha256']];record['v2_source_sha256']=source['sha256'];record['v2_source_snapshot']=source['snapshot'];record['v2_source_binding_correction_verified']=True
rev['context_provenance'].append({'record_id':rid,'context_id':gcid,'source_sha256':jsonsha,'source_snapshot':bs[jsonsha]['snapshot'],'text_fields':[{'field':'text','text_sha256':sha(gnode['text'].encode()),'literal_check':'serialized_two_source_group_cells_verified_against_JSON_and_original_image'},{'field':'row_cells/0','text_sha256':sha('5类'.encode()),'literal_check':'source_table_group_class_cell'},{'field':'row_cells/1','text_sha256':sha('境外上市的药品申请在境内上市'.encode()),'literal_check':'source_table_group_content_merged_cell'},{'field':'row_cells/2','text_sha256':sha(b''),'literal_check':'original_group_row_no_separate_period_cell; blank serialization retained'},{'field':'row_cells/3','text_sha256':sha(b''),'literal_check':'original_group_row_blank_note_cell_retained'}],'textless_structural_node':False})
for row in new:rev['record_content_bindings'][row['id']]['v2_canonical_source_content_sha256']=sha(dumps(row).encode())
rev['limits']=['This36 selection is development only; all IDs are already historically directly exposed.','AI source review is not human coding. No construct or dimension adjudication is included.','The archived CDE mirror and archived table image byte hashes are verified; this does not certify new official-origin online binary identity.','Source table group/merged-cell geometry is represented in v2 and complete image attached. All original textual fields and original CTX IDs remain.','Original source-derived structural metadata (such as reference_address) describes location/citation relationships and is not literal policy evidence.']
save(OUT/'projection-audit-v2.json',rev)
print(json.dumps({'record_N':len(new),'original_contexts_retained':171,'context_N':172,'textless_N':13,'source_binding_correction_node_N':4,'reviewed_pending_text_fields':19,'dangling_N':0,'forbidden_result_keys_N':0,'unresolved_N':0,'output_sha256':shafile(newpath),'v1_unchanged':shafile(oldpath)==oldhash},ensure_ascii=False,indent=2))
