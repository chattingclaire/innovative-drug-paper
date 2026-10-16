"""Finite integration of two already reviewed same-snapshot source slide documents.
No dimension coding, selection, external source search, or prior file modification.
"""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,copy,unicodedata
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];UP=ROOT/'01-review/source-slide-example-sol'
H=lambda b:hashlib.sha256(b).hexdigest()
def sf(p):return H(Path(p).read_bytes())
def rows(p):return list(map(json.loads,Path(p).read_text().splitlines()))
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def lines(p,x):Path(p).write_text(''.join(json.dumps(z,ensure_ascii=False,separators=(',',':'))+'\n' for z in x))
def cj(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def th(x):return H(x.encode())
def norm(t):return ''.join(c for c in unicodedata.normalize('NFKC',t) if not c.isspace() and not unicodedata.category(c).startswith('P'))
def walk(x):
 if isinstance(x,dict):
  for k,v in x.items():yield k,v;yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for z in x.values():yield from strings(z)
 elif isinstance(x,list):
  for z in x:yield from strings(z)
# Check upstream seals and all old delivered files before any new projection.
up_hashes={'SEALED.json':'6bf1e34dbc3222b2bd70d176228e41f5cc18e25421303e713b85624005626bc9','delivery-manifest.json':'d8003f025a81635fd6f8a31e5be5bcb300d209f184f7e0011f64474d305a7eef','source-only-supplement.json':'d7d162a6dcca477920d4b1476e8a6ad5f1cb6e590fc9a7cd870f748043b90fa7','source-text-resources.jsonl':'a946fa3e637a534f02067ff48db04fa992c8300d9864f8b1bb23b5f570475b9a','source-region-structure.json':'09b4cf9d6c4b27ed13f12338b9cf89322b8343b7acadf2734ff0262c70c4dea3'}
assert all(sf(UP/n)==v for n,v in up_hashes.items())
up_manifest=json.loads((UP/'delivery-manifest.json').read_text());assert len(up_manifest['files'])==19
assert all(sf(UP/z['relative_path'])==z['sha256'] and (UP/z['relative_path']).stat().st_size==z['bytes'] for z in up_manifest['files'])
old_seals=[]
for n in ['delivery-seal-v11.json','delivery-addenda-seal-v11.json']:
 d=json.loads((OUT/n).read_text());assert all(sf(z['path'])==z['sha256'] for z in d['files']);old_seals.append({'path':str(OUT/n),'sha256':sf(OUT/n),'files_rechecked_N':len(d['files'])})
assert sf(OUT/'canonical_source_context-v11.jsonl')=='5eaeddcfda5e0953fd31bea2d7bef20b9304ef40af277d94a586f9579406b8b6'
old=rows(OUT/'canonical_source_context-v11.jsonl');data=copy.deepcopy(old);oldmap={z['id']:z for z in old}
supp=json.loads((UP/'source-only-supplement.json').read_text());res=rows(UP/'source-text-resources.jsonl');reg=json.loads((UP/'source-region-structure.json').read_text());pages=json.loads((UP/'source-page-assets.json').read_text())['assets']
assert res==supp['resources'];assert len(res)==104 and len(reg['regions'])==17 and len(pages)==9
source_docs=supp['source_pdfs'];shas={d['source_sha256'] for d in source_docs};assert len(shas)==2
for d in source_docs:assert sf(d['snapshot'])==d['source_sha256']
assert all(th(z['text'])==z['text_sha256'] and not z['uncertain_characters'] for z in res)
assets=rows(OUT/'source-assets-manifest-v11.jsonl');old_asset_shas={z['sha256'] for z in assets};by_page={(z['source_sha256'],z['physical_page']):z for z in pages}
for p in pages:
 assert sf(p['original_asset_absolute_path'])==p['original_asset_sha256']
 absolute=UP/p['new_asset_relative_path'];assert sf(absolute)==p['new_asset_sha256']
 a={'attachment_id':'SOURCEPAGE-'+p['new_asset_sha256'][:20],'sha256':p['new_asset_sha256'],'kind':'same_snapshot_source_page_300dpi','source_pdf_sha256':p['source_sha256'],'physical_page':p['physical_page'],'absolute_path':str(absolute),'snapshot':str(absolute),'bytes':absolute.stat().st_size,'render_dpi':300,'pixel_dimensions':p['new_asset_pixels'],'source_review_identity_type':'AI','source_review_actual_page_read':'upstream_A_original_and_300dpi_page_read','source_review_provenance_seal_sha256':up_hashes['SEALED.json']}
 if a['sha256'] not in old_asset_shas:assets.append(a)
for z in res:
 p=by_page[z['source_sha256'],z['physical_page']];loc=z['source_locator'];loc['new_300dpi_asset_absolute_path']=str(UP/p['new_asset_relative_path']);loc['new_300dpi_asset_sha256']=p['new_asset_sha256']
 # Producer review provenance is distinct from the current consumer's read receipt.
 del z['actual_visual_read'];z['source_review_provenance']={'identity_type':'AI','model':'GPT-6.1 Sol','reasoning_setting':'ultra','actual_original_and_300dpi_page_read_by_resource_producer':True,'producer_seal_sha256':up_hashes['SEALED.json']}
removed=[]
for z in reg['regions']:
 removed.append({'region_id':z['region_id'],'removed_public_key':'interpretation','reason':'administrative commentary; public source geometry needs no such field'})
 del z['interpretation']
 if z['title_verbatim']=='示例封面':
  z['display_region_name']=z.pop('title_verbatim');z['display_region_name_is_printed_source_text']=False
 p=by_page[z['source_sha256'],z['physical_page']]
 z['source_page_assets']=[{'sha256':p['original_asset_sha256'],'absolute_path':p['original_asset_absolute_path']},{'sha256':p['new_asset_sha256'],'absolute_path':str(UP/p['new_asset_relative_path']),'render_dpi':300}]
projected_geometry={'representation':reg['representation'],'page_coordinate_system':reg['page_coordinate_system'],'bbox_accuracy':reg['bbox_accuracy'],'regions':reg['regions'],'arrows_or_normative_implication_edges_added':reg['arrows_or_normative_implication_edges_added']}
assert not projected_geometry['arrows_or_normative_implication_edges_added']
res_by_sha={s:[z for z in res if z['source_sha256']==s] for s in shas};regs_by_sha={s:[z for z in reg['regions'] if z['source_sha256']==s] for s in shas}
lib=rows(OUT/'source-library/library-v11.jsonl');registry=rows(OUT/'source-document-identities-v11.jsonl');refs=rows(OUT/'source-library/reference-index-v11.jsonl')
for z in lib:
 s=z.get('source_sha256')
 if s in shas:
  z['source_visual_text_resources']=res_by_sha[s];z['source_display_regions']=regs_by_sha[s]
  z['source_visual_text_review_scope']={'source_pdf_sha256':s,'physical_pages':[p['physical_page'] for p in pages if p['source_sha256']==s],'review_identity_type':'AI','bounded_visible_text_transcribed':True,'uncertain_character_N':0,'region_boxes_are_manual_padded_not_word_OCR':True,'upstream_seal_sha256':up_hashes['SEALED.json'],'consumer_actual_read_or_use_status':'not_recorded'}
  z['source_page_assets'].extend({'physical_page':p['physical_page'],'sha256':p['new_asset_sha256'],'absolute_path':str(UP/p['new_asset_relative_path']),'source_pdf_sha256':s,'render_dpi':300} for p in pages if p['source_sha256']==s)
for z in registry:
 if z['source_sha256'] in shas:
  z['source_visual_text_resource']={'relative_path':'source-library/slide-visual-text-v12.jsonl','sha256':None,'source_sha256':z['source_sha256'],'resource_N':len(res_by_sha[z['source_sha256']])}
  z['source_display_geometry_resource']={'relative_path':'source-library/slide-display-geometry-v12.json','sha256':None,'source_sha256':z['source_sha256'],'region_N':len(regs_by_sha[z['source_sha256']])}
lines(OUT/'source-library/slide-visual-text-v12.jsonl',res);dump(OUT/'source-library/slide-display-geometry-v12.json',projected_geometry)
for z in registry:
 if z['source_sha256'] in shas:
  z['source_visual_text_resource']['sha256']=sf(OUT/'source-library/slide-visual-text-v12.jsonl');z['source_display_geometry_resource']['sha256']=sf(OUT/'source-library/slide-display-geometry-v12.json')
changes=[];affected=[]
expected_ids={i for d in source_docs for i in d['affected_existing_record_ids']}
for r in data:
 s=r['source_ref']['sha256']
 if s not in shas:continue
 assert r['id'] in expected_ids
 match=[z for z in res_by_sha[s] if z['role']=='body_instruction' and norm(r['text']) in norm(z['text'])]
 assert len(match)==1;instruction=match[0]
 cid='CTX-'+th('v12-source-display:'+r['id']+':'+s)[:20]
 structure={'representation':'same_snapshot_source_display_geometry','source_document_resource_id':'SOURCE-'+s,'bound_body_instruction_resource_id':instruction['source_resource_id'],'bound_body_instruction_region_id':instruction['slide_region_id'],'document_display_region_ids':[z['region_id'] for z in regs_by_sha[s]],'document_source_visual_text_resource_ids':[z['source_resource_id'] for z in res_by_sha[s]],'physical_pages':[p['physical_page'] for p in pages if p['source_sha256']==s],'coordinate_system':'PDF points, top-left origin','source_geometry_relative_path':'source-library/slide-display-geometry-v12.json','source_geometry_sha256':sf(OUT/'source-library/slide-display-geometry-v12.json')}
 r['contexts'].append({'context_id':cid,'kind':'same_snapshot_source_display_geometry','source_document':'D-'+s[:16],'structure':structure,'source_ref':{'sha256':s,'source_resource_id':'SOURCE-'+s,'locator':{'physical_pages':structure['physical_pages'],'bound_instruction_region_id':instruction['slide_region_id'],'source_geometry_relative_path':structure['source_geometry_relative_path'],'source_geometry_sha256':structure['source_geometry_sha256']}}})
 r.setdefault('source_references',[]).append({'source_resource_id':'SOURCE-'+s,'source_sha256':s,'relation':'same_snapshot_source_display_regions','bound_body_instruction_resource_id':instruction['source_resource_id'],'bound_body_instruction_region_id':instruction['slide_region_id']})
 # New images are neutral alternate-resolution views; all previous attachments remain.
 for p in pages:
  if p['source_sha256']==s:r.setdefault('source_attachments',[]).append({'attachment_id':'SOURCEPAGE-'+p['new_asset_sha256'][:20],'sha256':p['new_asset_sha256'],'absolute_path':str(UP/p['new_asset_relative_path']),'source_pdf_sha256':s,'physical_page':p['physical_page'],'kind':'same_snapshot_source_page_300dpi'})
 refs.append({'record_id':r['id'],'context_id':cid,'source_field':'text','source_field_text_sha256':th(r['text']),'resource_id':'SOURCE-'+s,'literal_relation_type':'same_snapshot_body_instruction_region','source_visual_text_resource_id':instruction['source_resource_id'],'source_region_id':instruction['slide_region_id'],'unit_primary_source_sha256':s,'literal_match_normalization':'NFKC; remove whitespace and Unicode P* punctuation','literal_body_is_contained_in_source_instruction':True,'automatic_whole_document_applicability_binding':False})
 changes.append({'record_id':r['id'],'primary_source_sha256':s,'old_body_sha256':th(oldmap[r['id']]['text']),'new_body_sha256':th(r['text']),'body_changed':False,'old_context_N':len(oldmap[r['id']]['contexts']),'new_context_N':len(r['contexts']),'all_old_contexts_preserved_byte_content':r['contexts'][:-1]==oldmap[r['id']]['contexts'],'new_context_id':cid,'matched_instruction_resource_id':instruction['source_resource_id'],'matched_instruction_region_id':instruction['slide_region_id'],'shared_source_visual_text_resource_N':len(res_by_sha[s]),'shared_source_display_region_N':len(regs_by_sha[s]),'new_actual_300dpi_page_N':sum(p['source_sha256']==s for p in pages)})
 affected.append(r['id'])
assert set(affected)==expected_ids and len(affected)==12
assert all(x['text']==y['text'] and x['id']==y['id'] for x,y in zip(old,data))
assert all(r==oldmap[r['id']] for r in data if r['id'] not in affected)
for rid in ['RECODE25-00900','RECODE25-00902']:assert next(r for r in data if r['id']==rid)==oldmap[rid]
lines(OUT/'canonical_source_context-v12.jsonl',data);lines(OUT/'source-library/library-v12.jsonl',lib);lines(OUT/'source-library/reference-index-v12.jsonl',refs);lines(OUT/'source-document-identities-v12.jsonl',registry);lines(OUT/'source-assets-manifest-v12.jsonl',assets);lines(OUT/'source-changes-v12.jsonl',changes)
# All4481 identity/body/family checks are mechanical; no new text-label review.
frame=rows(ROOT/'00-baseline/source-only-frame.jsonl');base={z['id']:z for z in frame};assert [z['id'] for z in frame]==[z['id'] for z in data]
oldbind={z['id']:z for z in rows(OUT/'material-record-bindings-v11.jsonl')};assert all('TEXTFAM-'+th(norm(z['unit_text']))==oldbind[z['id']]['original_family_id'] for z in frame);binding=[]
for r in data:
 b=copy.deepcopy(oldbind[r['id']]);b['projected_body_sha256']=th(r['text']);b['projected_family_id']='TEXTFAM-'+th(norm(r['text']));b['projected_context_sha256']=th(cj(r['contexts']));b['projected_record_sha256']=th(cj(r));b['source_projection_version']='v12';binding.append(b)
lines(OUT/'material-record-bindings-v12.jsonl',binding)
ex=json.loads((ROOT/'01-review/exposure-ids.json').read_text());seeds=set(ex['excluded_ids']);families={r['id']:'TEXTFAM-'+th(norm(r['text'])) for r in data};exposed_families={families[i] for i in seeds};closed={i for i,f in families.items() if f in exposed_families}|seeds;pool=set(base)-closed;oldpool=set(base)-seeds
assert len(seeds)==len(closed)==3037 and len(pool)==1444 and pool==oldpool
fam={'version':'v12','canonical_sha256':sf(OUT/'canonical_source_context-v12.jsonl'),'normalization':'NFKC; remove Unicode whitespace and P* punctuation; retain all other symbols and case','source_body_bytes_identical_to_v11_all4481':True,'original_family_N':len({z['original_family_id'] for z in oldbind.values()}),'current_family_N':len(set(families.values())),'cumulative_original_body_changes_N':sum(r['text']!=base[r['id']]['unit_text'] for r in data),'body_changes_since_v11_N':0,'historical_direct_exposure_N':len(ex['direct_exposure_ids']),'old_closed_exposure_seed_N':len(seeds),'all_old_closed_stable_IDs_seeded':True,'current_closed_exposure_N':len(closed),'current_remaining_N':len(pool),'exposure_membership_delta_N':len(seeds^closed),'remaining_membership_delta_N':len(pool^oldpool),'remaining_by_department':dict(Counter(base[i]['analysis_group'] for i in pool)),'source_fact_review_not_added_to_label_development_exposure':True,'remaining_pool_is_not_final_frozen_sample':True}
assert fam['original_family_N']==fam['current_family_N']==3754 and fam['cumulative_original_body_changes_N']==2
dump(OUT/'family-exposure-impact-v12.json',fam)
forbid=set(json.loads((OUT/'current-source-schema-v11.json').read_text())['x-source-protocol']['recursive_forbidden_exact_keys']);hits=[]
for name,content in [('canonical',data),('library',lib),('text_resources',res),('display_geometry',projected_geometry)]:
 hits.extend({'object':name,'key':k} for k,v in walk(content) if k in forbid)
assert not hits,hits
visual_ids={z['source_resource_id'] for z in res};region_ids={z['region_id'] for z in reg['regions']};globalctx={n['context_id'] for r in data for n in r['contexts']};dangling=[];dup=0
for r in data:
 cs=[n['context_id'] for n in r['contexts']];dup+=len(cs)-len(set(cs));available=set(cs)
 for v in strings(r):
  if v.startswith('CTX-') and v not in available:dangling.append({'record_id':r['id'],'ref':v})
  if v.startswith('SOURCEVISUAL-') and v not in visual_ids:dangling.append({'record_id':r['id'],'ref':v})
  if v.startswith('SLIDE-') and v not in region_ids:dangling.append({'record_id':r['id'],'ref':v})
for item in res+reg['regions']:
 for v in strings(item):
  if v.startswith('SOURCEVISUAL-') and v not in visual_ids:dangling.append({'resource':'visual','ref':v})
  if v.startswith('SLIDE-') and v not in region_ids:dangling.append({'resource':'display','ref':v})
assert not dangling and dup==0
assert all(n['source_ref']['source_resource_id']=='SOURCE-'+n['source_ref']['sha256'] for r in data for n in [r]+r['contexts'])
source_manifest=json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text());source_checks=[{'source_sha256':z['sha256'],'path':z['snapshot'],'SHA_matched':sf(z['snapshot'])==z['sha256']} for z in source_manifest['files']];assert len(source_checks)==136 and all(z['SHA_matched'] for z in source_checks)
asset_checks=[{'sha256':z['sha256'],'path':z['absolute_path'],'SHA_matched':sf(z['absolute_path'])==z['sha256']} for z in assets];assert all(z['SHA_matched'] for z in asset_checks)
# Preserve previous actual-QA rows and append neutral geometry status for12 new nodes.
(OUT/'body-source-QA-v12.jsonl').write_bytes((OUT/'body-source-QA-v11.jsonl').read_bytes())
ctxqa=rows(OUT/'context-source-QA-v11.jsonl')
for z in changes:ctxqa.append({'record_id':z['record_id'],'context_id':z['new_context_id'],'source_sha256':z['primary_source_sha256'],'status':'same_snapshot_display_geometry_and_bounded_AI_visual_source_resources','textless_structure':True,'source_producer_actual_page_read_seal_sha256':up_hashes['SEALED.json'],'consumer_read_status':'not_recorded'})
lines(OUT/'context-source-QA-v12.jsonl',ctxqa)
for n in ['source-exceptions-v12.jsonl','grouped-source-review-jobs-v12.jsonl']:(OUT/n).write_text('')
bases=json.loads((OUT/'source-asset-locator-bases-v11.json').read_text());bases['v12_absolute_locator_policy']='All新增300dpi图页与视觉文字资源locator写绝对路径+文件SHA；旧相对路径仍按既有明确base解析。';bases['slide_supplement_base_absolute_path']=str(UP);dump(OUT/'source-asset-locator-bases-v12.json',bases)
gaps=json.loads((OUT/'source-material-gaps-v11.json').read_text());gaps['version']='v12';gaps['status']='finite_source_material_freeze_candidate; remaining_limits_explicit; joint_execution_freeze_not_performed';gaps['gaps']=[g for g in gaps['gaps'] if g['issue_id']!='SOURCE-GAP-SLIDE-EXAMPLE-TEXT'];gaps['closed_bounded_source_gaps']=[{'issue_id':'SOURCE-GAP-SLIDE-EXAMPLE-TEXT','source_pdf_N':2,'original_page_N':9,'visual_text_resource_N':104,'display_region_N':17,'affected_record_N':12,'producer_identity_type':'AI','closure_scope':'指定两个同SHA文档九页全部可见文字有界转写与纯展示关系；非通用像素/图像语义完备证书','producer_seal_sha256':up_hashes['SEALED.json']}];gaps['all_methods_actually_read_images_or_all_available_resources']='not_certified';dump(OUT/'source-material-gaps-v12.json',gaps)
impact77=rows(OUT/'development77-material-impact-v11.jsonl');ids77={z.get('record_id',z.get('id')) for z in impact77};assert len(ids77)==77
impact={'version':'v12','compared_to_v11':True,'development_ID_N':77,'new_slide_source_affected_development_ids':sorted(ids77&expected_ids),'development77_body_changes_since_v11_N':sum(oldmap[i]['text']!=next(z['text'] for z in data if z['id']==i) for i in ids77),'development77_canonical_rows_changed_since_v11_N':sum(oldmap[i]!=next(z for z in data if z['id']==i) for i in ids77),'prior_v11_source_impact_report':{'path':str(OUT/'development77-material-impact-v11.jsonl'),'sha256':sf(OUT/'development77-material-impact-v11.jsonl')},'source_content_only_no_label_impact_inferred':True}
assert not impact['new_slide_source_affected_development_ids'];dump(OUT/'development77-material-impact-v12.json',impact)
qa={'version':'v12','old_version_seals':old_seals,'upstream_manifest_files_rechecked_N':19,'upstream_seal':{'path':str(UP/'SEALED.json'),'sha256':up_hashes['SEALED.json']},'public_filter_operations':removed,'source_snapshot_checks':source_checks,'public_asset_checks':asset_checks,'frame_N':len(data),'source_body_changes_since_v11_N':0,'cumulative_original_body_changes_N':2,'current_context_N':sum(len(r['contexts']) for r in data),'new_context_N':12,'current_textless_node_N':sum(not any(n.get(k) for k in ['text','title','caption','headers','row_cells']) for r in data for n in r['contexts']),'all_old_contexts_preserved':all(all(n==r['contexts'][j] for j,n in enumerate(oldmap[r['id']]['contexts'])) for r in data),'forbidden_key_hit_N':0,'dangling_reference_N':0,'duplicate_context_ID_within_record_N':0,'uniform_source_ref_IDs':True,'source_display_resource_N':104,'source_display_region_N':17,'source_display_roles':dict(Counter(z['role'] for z in res)),'source_library_document_resource_N':len(lib),'public_actual_file_path_N':len({z['absolute_path'] for z in assets}),'public_distinct_asset_SHA_N':len({z['sha256'] for z in assets}),'new_actual_file_path_N':len(pages),'new_distinct_asset_SHA_N':len({z['sha256'] for z in assets}-old_asset_shas),'literal_pending_occurrence_N':0,'literal_pending_unique_job_N':0,'future_required_reference_discovery_not_covered_by_this_zero':True,'human_independent_coding_or_machine_coding_not_performed':True,'joint_manual_rule_prompt_sampling_material_freeze_not_performed':True}
dump(OUT/'package-integrity-v12.json',qa)
summary={'schema':'source-preflight-summary/v12','version':'v12','status':'finite_same_snapshot_source_material_freeze_candidate; not_joint_execution_freeze','current_state':{'frame_N':4481,'excluded_GOV_interface_N':443,'canonical_projection':{'path':str(OUT/'canonical_source_context-v12.jsonl'),'sha256':sf(OUT/'canonical_source_context-v12.jsonl')},'cumulative_original_body_changes_N':2,'body_changes_since_v11_N':0,'current_context_N':qa['current_context_N'],'current_textless_node_N':qa['current_textless_node_N'],'all_original_contexts_and_existing_v11_contexts_preserved':True,'new_context_N':12,'new_bounded_visual_text_resource_N':104,'new_display_region_N':17,'shared_visual_instruction_resource_N':sum(z['role']=='body_instruction' for z in res),'affected_record_N':12,'new_300dpi_page_asset_N':qa['new_actual_file_path_N'],'new_distinct_asset_SHA_N':qa['new_distinct_asset_SHA_N'],'current_public_actual_file_path_N':qa['public_actual_file_path_N'],'current_public_distinct_asset_SHA_N':qa['public_distinct_asset_SHA_N'],'original_source_snapshots_SHA_pass_N':136,'current_source_library_document_resource_N':len(lib),'current_literal_pending_occurrence_N':0,'current_literal_pending_unique_job_N':0,'current_literal_pending_fragment_types':{},'current_dangling_references_N':0,'current_forbidden_key_hits_N':0,'current_closed_exposure_N':3037,'current_remaining_N':1444,'pool_membership_delta_N':0,'source_material_gaps':{'path':str(OUT/'source-material-gaps-v12.json'),'sha256':sf(OUT/'source-material-gaps-v12.json'),'remaining_limit_types_N':len(gaps['gaps'])},'new_external_source_acquisitions_N':0,'consumer_actual_read_or_use_status':'not_recorded','human_independent_validation_performed':False,'new_full_frame_machine_coding_launched':False,'joint_freeze_completed':False},'historical_versions':old_seals,'bounded_change_scope':{'affected_ids':affected,'source_sha256s':sorted(shas),'upstream_source_supplement':{'path':str(UP/'source-only-supplement.json'),'sha256':up_hashes['source-only-supplement.json']}},'evidence_reports':{'integrity':str(OUT/'package-integrity-v12.json'),'family_exposure':str(OUT/'family-exposure-impact-v12.json'),'change_log':str(OUT/'source-changes-v12.jsonl'),'development77_impact':str(OUT/'development77-material-impact-v12.json')}}
dump(OUT/'source-QA-summary-v12.json',summary)
print(json.dumps(summary['current_state'],ensure_ascii=False,indent=2))
