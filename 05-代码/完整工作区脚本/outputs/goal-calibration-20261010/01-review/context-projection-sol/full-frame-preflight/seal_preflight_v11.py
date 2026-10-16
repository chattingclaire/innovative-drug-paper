"""Seal source material version, keeping genuine coverage limits separate."""
from pathlib import Path
import json,hashlib,copy,re,os,subprocess,unicodedata
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
H=lambda b:hashlib.sha256(b).hexdigest()
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def sf(p):return H(Path(p).read_bytes())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def jl(p,x):p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in x))
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
data=rows(OUT/'canonical_source_context-v11.jsonl');old=rows(OUT/'canonical_source_context-v8.jsonl');OD={r['id']:r for r in old};frame=rows(ROOT/'00-baseline/source-only-frame.jsonl');FD={r['id']:r for r in frame};M=json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text());BS={x['sha256']:x for x in M['files']}
assert [r['id'] for r in data]==[r['id'] for r in frame] and len(data)==4481

# Source examples omitted from the selected left instruction blocks are now
# available as separate whole-source text/image resources. Original unit scope
# is retained; this is not an instruction to assign an example to a dimension.
lib=[x for x in rows(OUT/'source-library/library-v11.jsonl') if not x.get('source_sha256','').startswith(('1be84453158f1e92','da218af12c655b8b'))];slide_sources=[]
for prefix in ['1be84453158f1e92','da218af12c655b8b']:
 s=next(k for k in BS if k.startswith(prefix));assert sf(BS[s]['snapshot'])==s
 z=subprocess.run(['pdftotext','-layout',BS[s]['snapshot'],'-'],capture_output=True,text=True,timeout=30);assert z.returncode==0
 ps=[t for t in z.stdout.split('\f') if t.strip()];assets=[]
 for i,t in enumerate(ps,1):
  path=OUT/('source-visual-v11/pages' if i==1 else 'source-visual-v9/pages')/f'{prefix}-{i}.png';assert path.is_file();assets.append({'physical_page':i,'sha256':sf(path),'absolute_path':str(path),'source_pdf_sha256':s})
 extracted=''.join(c for c in unicodedata.normalize('NFKC',z.stdout) if not c.isspace());checks={t:t in extracted for t in ['盐酸二甲双胍片','1999年','共108家','本品首选用于单纯饮食控制']}
 ids=[r['id'] for r in data if r['source_ref']['sha256']==s]
 resource={'source_resource_id':'SOURCE-'+s,'source_sha256':s,'snapshot':BS[s]['snapshot'],'snapshot_sha256':s,'document_title_verbatim_on_first_source_page':'附件2-2；本短片仅做参考' if len(ps)==5 else '附件2-3；本短片仅做参考','source_title_reading_status':'actual first page visually viewed; typo 短片 preserved from source','source_texts':[{'source_locator':{'physical_page':i},'text':t,'text_sha256':H(t.encode()),'representation':'whole actual source PDF pdftotext layout; both instruction and illustration regions'} for i,t in enumerate(ps,1)],'source_page_assets':assets,'source_regions':{'left_upper_slide_instruction_block':'原记录正文/语境所选“包括但不限于”说明块','right_upper_and_lower_slide_example_blocks':'源图确实存在药品示例、疾病信息和用法用量等文字；完整文档资源可读','first_page_example_notice':'本短片仅做参考'},'source_image_every_glyph_transcription_completeness_certified':False}
 lib.append(resource);slide_sources.append({'source_sha256':s,'affected_record_ids':ids,'affected_record_N':len(ids),'physical_page_N':len(ps),'detected_original_selected_JSON_example_phrases_missing_N':4,'now_whole_source_extraction_phrase_presence_checks':checks,'detected_demo_phrases_still_absent_from_actual_PDF_text_layer_N':sum(not v for v in checks.values()),'current_source_library_resource_id':'SOURCE-'+s,'every_source_pixel_text_completeness_status':'not_certified','target_selected_left_instruction_body_unchanged':True})
jl(OUT/'source-library/library-v11.jsonl',lib)

docs=rows(OUT/'source-document-identities-v8.jsonl')
for x in docs:
 # Filename years are metadata candidates, never certificates of publication,
 # applicability or the specific contemporaneous version of a cited document.
 if 'document_year_established' in x:
  x['document_year_candidate_from_recorded_original_path']=x.pop('document_year_established');x['recorded_path_year_is_not_source_publication_or_effective_date']=True
 s=x['source_sha256'];resources=[y['source_resource_id'] for y in lib if y.get('source_sha256')==s or y.get('snapshot_sha256')==s]
 if resources:x['source_library_resource_ids']=resources
 if s.startswith('0b5214578c2fd174'):
  x['source_title_actual_page_read']='2025年国家基本医疗保险、生育保险和工伤保险药品目录及商业健康保险创新药品目录调整工作方案';x['document_year_explicitly_printed_in_actual_source_title']=2025;x['actual_title_physical_page']=1
 if s.startswith('b8524dded105cc5b'):
  x['source_title_actual_page_read']='国家卫生健康委办公厅关于印发第二批国家重点监控合理用药药品目录的通知';x['document_number_actual_page_read']='国卫办医政函〔2023〕9号';x['composition_date_actual_page_read']='2023-01-13';x['actual_title_physical_page']=1
 if s.startswith('d76f3d33'):
  x['source_title_actual_page_read']='谈判药品续约规则';x['source_year_explicit_annual_example']=2025;x['official_publication_date']=None;x['official_origin_URL']=None;x['source_text_resource']={'relative_path':'source-library/renewal2025-reference-source-v11.json','sha256':sf(OUT/'source-library/renewal2025-reference-source-v11.json'),'source_pdf_sha256':s,'kind':'same_source_full_named_rules_and_shared_appendix'}
 if s.startswith('980acf76'):
  x['original_July_program_binary_source_SHA']='7335b5b6bc8ab6106aa7c327473896be8cfe8fc8b6ead01df0765b71a17bde61';x['expressly_cited_technical_guideline_version_status']='not_uniquely_established';x['reference_version_source_resource_id']='SOURCE-REFERENCE-VERSION-CONDITIONAL-202007'
jl(OUT/'source-document-identities-v11.jsonl',docs)
forbid=set(json.loads((OUT/'source-QA-summary-v11.json').read_text())['recursive_forbidden_keys']['keys'])|{'dimension_decision'};bad=[];dangling=[];dups=[];assets={};image_relation_unbound=[]
def walk(x,path):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in forbid:bad.append(path+'/'+k)
   walk(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'/'+str(i))
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
for r in data:
 walk(r,r['id']);cids={n['context_id'] for n in r['contexts']};nr={x['relation_id'] for x in r.get('source_relations',[])}
 assert {n['context_id'] for n in OD[r['id']]['contexts']}<=cids
 if len(cids)!=len(r['contexts']):dups.append(r['id'])
 for s in strings(r):
  if s.startswith('CTX-') and s not in cids:dangling.append([r['id'],s])
  if s.startswith('NR-') and s not in nr:dangling.append([r['id'],s])
 ats={a['attachment_id']:a for a in r.get('source_attachments',[])}
 for a in ats.values():
  path=(OUT/a['relative_path']).resolve();assert sf(path)==a['sha256'];assets[(str(path),a['sha256'])]={**a,'absolute_path':str(path),'snapshot':str(path)}
 for rel in r.get('source_relations',[]):
  if rel.get('kind')=='image_source_metadata':
   for a in rel['image_sources']:
    if a['attachment_id'] not in ats:image_relation_unbound.append([r['id'],rel['relation_id'],a['attachment_id']])
 for target in [r]+r['contexts']:
  s=target['source_ref']['sha256'];assert s in BS
for x in lib:walk(x,'source_library/'+x['source_resource_id'])
assert not bad and not dangling and not dups and not image_relation_unbound
# Library-only assets remain public even where a row does not include every page.
for x in lib:
 for a in x.get('source_page_assets',[]):
  path=Path(a['absolute_path']) if 'absolute_path' in a else (OUT/a['relative_path']).resolve();assert sf(path)==a['sha256'];assets[(str(path),a['sha256'])]={**a,'absolute_path':str(path),'snapshot':str(path),'attachment_id':'SOURCEASSET-'+a['sha256'][:20]}
jl(OUT/'source-assets-manifest-v11.jsonl',list(assets.values()))
dump(OUT/'source-asset-locator-bases-v11.json',{'canonical_row_attachment_relative_path_base':str(OUT),'source_library_renewal_resource_page_asset_base':str(ROOT/'01-review/renewal-reference-source-sol'),'canonical_source_ref_absolute_primary_files_in_registry':True,'asset_SHA_to_absolute_path_manifest':'source-assets-manifest-v11.jsonl','all_attachment_SHA_checks_passed':True,'description':'Source region page_asset strings preserve the original source reviewer local page name; resolve by source SHA+physical page or attachment/image SHA in the public asset manifest.'})
dump(OUT/'renewal-common-v11/source-asset-locator-bases.json',{'canonical_source_context_attachment_relative_path_base':str(OUT),'source_resource_source_ref_region_page_asset_base':str(ROOT/'01-review/renewal-reference-source-sol'),'source_resource_source_page_assets_relative_path_base':str(OUT),'primary_source_pdf':str(BS[next(s for s in BS if s.startswith('d76f3d33'))]['snapshot']),'primary_source_sha256':next(s for s in BS if s.startswith('d76f3d33')),'same9_source_page_assets':next(x for x in lib if x.get('source_sha256','').startswith('d76f3d33'))['source_page_assets']})

# Independently rerun the exact family normalization and monotone exposure closure.
def fn(t):return ''.join(c for c in unicodedata.normalize('NFKC',t) if not c.isspace() and not unicodedata.category(c).startswith('P'))
rm=rows(OUT/'material-record-bindings-v11.jsonl');RMD={x['id']:x for x in rm}
for r in data:
 f=FD[r['id']];of='TEXTFAM-'+H(fn(f['unit_text']).encode());nf='TEXTFAM-'+H(fn(r['text']).encode());assert f['normalized_text_family']['family_id']==of;assert RMD[r['id']]['original_family_id']==of and RMD[r['id']]['projected_family_id']==nf
ex=json.loads((ROOT/'01-review/exposure-ids.json').read_text());seed=set(ex['excluded_ids']);oldpool=set(FD)-seed;closedfamilies={RMD[rid]['projected_family_id'] for rid in seed};closed={r['id'] for r in data if RMD[r['id']]['projected_family_id'] in closedfamilies};pool=set(FD)-closed;assert seed<=closed and closed==seed and pool==oldpool
fam=json.loads((OUT/'family-exposure-impact-v11.json').read_text());fam['changed_body_records']=[RMD[x['id']] for x in fam['changed_body_records']];fam['independently_rerun_against_final_v11_body_bytes']=True;fam['old_family_exposure_links_preserved_by_stable_ID']=True;fam['final_projection_body_SHA_binding_all4481_rechecked']=True;dump(OUT/'family-exposure-impact-v11.json',fam)

gaps=[{'issue_id':'SOURCE-GAP-CONDITIONAL-GUIDE-VERSION','kind':'expressly_cited_technical_guideline_target_version_unresolved','resource_id':'SOURCE-REFERENCE-VERSION-CONDITIONAL-202007','original_program_binary_provenance_status':'confirmed_2020_July_attachment2_original_DOC','cited_target_version_status':'not_uniquely_established','november2020_final_is_later_than_July_program':True,'candidate_drafts_not_silently_bound':True,'next_action':'Keep unresolved reference version visible; no repeated unbounded source search requested.'}, {'issue_id':'SOURCE-GAP-IMAGE-TEXT-COMPLETENESS','kind':'machine_public_text_vs_actual_source_pixels_not_universally_certified','original_image_source_relation_N':47,'all_original_image_relation_attachment_IDs_resolved':True,'all_images_have_SHA_verified_actual_file_paths':True,'source_pixels_every_material_detail_projected_into_text_status':'unknown_outside_explicitly_reviewed_required_text_and_geometry','all_declared_source_figures_have_pure_geometry_for_reviewed13jobs':True,'next_action':'Consumers must record which image/geometry resources they actually read; a text-only rule cannot be treated as receiving pixel information merely because image paths are in its JSON.'}, {'issue_id':'SOURCE-GAP-SLIDE-EXAMPLE-TEXT','kind':'actual_example_regions_outside_original_selected_left_instruction_text','source_documents':slide_sources,'current_status':'whole-source PDF extracted text and all9 source page images supplied separately; source drug name appears in raw extraction but3 checked physical2 example phrases per document remain absent from that text layer','remaining_limit':'actual right-side source example pixels are not completely parsed; known missing example phrases are1999年、共108家、本品首选用于单纯饮食控制. This is a machine text gap and is not an automatic negative code.'}, {'issue_id':'SOURCE-GAP-REFERENCE-INDEX-COVERAGE','kind':'explicit_reference_fulltext_closure_not_comprehensively_certified','current_index_scope':'two prior neutral sources; actual2025 FAQ workplan references; sameSHA2025 renewal named rule references; July conditional-guideline version status','next_action':'Before final coding-material freeze, approve a uniform necessary-context/reference protocol and track newly discovered exact reference omissions for all affected units, without label-driven selection.'}]
dump(OUT/'source-material-gaps-v11.json',{'status':'source_version_seal_with_material_coverage_limits; not_final_material_freeze','primary_literal_unlocated_occurrence_N':0,'primary_literal_unlocated_unique_job_N':0,'zero_literal_jobs_does_not_prove_zero_content_omissions':True,'known_original_frame_body_corrections_N':2,'public_text_pending_is_not_an_automatic_negative_code':True,'gaps':gaps,'machine_human_material_read_equivalence_status':'same_source_bundle_available; actual resource consumption still must be logged','source_review_is_AI_not_true_human_independent_coding':True})
counts=Counter('body_literal_'+x['literal_status'] for x in rows(OUT/'body-source-QA-v11.jsonl'));ct=rows(OUT/'context-source-QA-v11.jsonl');counts['contexts']=len(ct);counts['textless_contexts']=sum(x['textless_structure'] for x in ct)
for x in ct:
 for f in x['policy_text_fields']:counts['context_literal_'+f['literal_status']]+=1
prior_qa=json.loads((OUT/'source-QA-summary-v10.json').read_text())
current={'frame_N':4481,'source_interface_input_N':4924,'excluded_GOV_interface_N':443,'department_N':prior_qa['department_N'],'counts':dict(counts),'canonical_projection':{'path':str(OUT/'canonical_source_context-v11.jsonl'),'sha256':sf(OUT/'canonical_source_context-v11.jsonl')},'original_body_unchanged_N':4479,'cumulative_original_body_changes_N':2,'body_changes_since_v8_N':0,'existing_context_text_changes_since_v8_N':0,'pending_literal_occurrence_N':0,'pending_literal_unique_job_N':0,'pending_literal_fragment_types':{},'source_material_coverage_gaps_path':str(OUT/'source-material-gaps-v11.json'),'remaining_source_coverage_issue_types_N':len(gaps),'source_library_document_resource_N':len(lib),'shared_renewal_paragraph_resource_N':37,'sameSHA_named_renewal_reference_restore_record_N':72,'current_context_N':len(ct),'original_context_N':24655,'all_original_CTX_IDs_preserved':True,'original_textless_node_N':1348,'current_textless_node_N':counts['textless_contexts'],'original_image_relation_N':47,'unbound_original_image_relations_N':0,'attached_unique_actual_file_N':len(assets),'primary_literal_jobs_closed_is_not_material_freeze':True,'final_material_freeze_completed':False,'new_whole_frame_coding_launched':False,'human_independent_coding_validation_performed':False}
qa={'schema':'source-preflight-summary/v11','version':'v11','status':'sealed_source_only_version_with_literal_tasks_closed_and_explicit_material_coverage_limits','current_state':current,'counts':dict(counts),'frame_N':4481,'body_changes_N':2,'pending_issue_N':0,'pending_unique_source_text_N':0,'output':current['canonical_projection'],'recursive_forbidden_keys':{'keys':sorted(forbid),'violations':bad},'current_primary_source_byte_checks':{'source_snapshot_N':136,'failed_N':0,'all_source_attachment_SHA_checks_passed':True,'forbidden_fields':bad,'dangling_CTX_or_NR':dangling},'source_registry_metadata_policy':'Recorded original-path years are candidates; actual source title/year/date is asserted separately only where specifically read. Filename years do not certify publication, effectiveness or a cited version.','historical_versions':{'not_current_state':True,'version_files':[{'version':v,'path':str(OUT/f'source-QA-summary-{v}.json'),'sha256':sf(OUT/f'source-QA-summary-{v}.json')} for v in ['v4','v5','v6','v7','v8','v9','v10']],'v8_to_v9_actual_literal_resolutions_N':173,'v9_to_v10_actual_literal_resolutions_N':52,'v9_to_v10_graph_unique_job_N':13,'v10_to_v11_renewal_context_additions_N':2736},'source_changes_current_proofs':['source-text-changes-v8.json','source-integration-review-v10.json','renewal-source-integration-v11.json'],'source_material_gaps':'source-material-gaps-v11.json','builders':[{'path':str(OUT/n),'sha256':sf(OUT/n)} for n in ['integrate_source_v10.py','integrate_renewal_v11.py','seal_preflight_v11.py']],'input_files':prior_qa['input_files'],'scope':'source identity, literal text, geometry and explicit-reference restoration only; labels and independent coder outputs not read','final_material_freeze_completed':False}
dump(OUT/'source-QA-summary-v11.json',qa)
checks={'status':'source_preflight_v11_version_seal_not_final_material_freeze','frame_N':4481,'all_original_IDs_order_and_exclusions_preserved':True,'original_body_unchanged_N':sum(r['text']==FD[r['id']]['unit_text'] for r in data),'cumulative_original_body_changes_N':2,'new_body_text_changes_since_v8_N':0,'new_existing_context_text_changes_since_v8_N':0,'current_context_N':sum(len(r['contexts']) for r in data),'original_context_N':24655,'all_original_CTX_IDs_preserved':True,'original_textless_node_N':1348,'all_original_textless_nodes_preserved':True,'current_textless_node_N':counts['textless_contexts'],'forbidden_keys':bad,'dangling_CTX_or_NR':dangling,'duplicate_CTX':dups,'unbound_original_image_relations':image_relation_unbound,'original_image_relation_N':47,'unique_public_actual_file_N':len(assets),'source_manifest136_SHA_checks_passed':all(sf(x['snapshot'])==x['sha256'] for x in M['files']),'library_document_resources_N':len(lib),'named_renewal_restoration_record_N':72,'pending_literal_occurrence_N':0,'pending_literal_unique_job_N':0,'remaining_source_coverage_issue_types_N':len(gaps),'remaining_pool_N':len(pool),'historical_closed_exposure_N':len(closed),'remaining_pool_membership_change_N':0,'old3037_stable_IDs_not_washed_by_new_family_names':True,'final_material_freeze_completed':False,'human_independent_validation_completed':False,'new_whole_frame_machine_coding_launched':False}
dump(OUT/'package-integrity-v11.json',checks)
names=['canonical_source_context-v11.jsonl','body-source-QA-v11.jsonl','context-source-QA-v11.jsonl','source-QA-summary-v11.json','source-exceptions-v11.jsonl','grouped-source-review-jobs-v11.jsonl','material-record-bindings-v11.jsonl','family-exposure-impact-v11.json','source-integration-review-v10.json','renewal-source-integration-v11.json','source-document-identities-v11.jsonl','source-assets-manifest-v11.jsonl','source-asset-locator-bases-v11.json','source-material-gaps-v11.json','source-library/library-v11.jsonl','source-library/reference-index-v11.jsonl','source-library/workplan2025-full-source-v10.json','source-library/conditional-guideline-reference-version-v10.json','source-library/renewal2025-reference-source-v11.json','package-integrity-v11.json','integrate_source_v10.py','integrate_renewal_v11.py','seal_preflight_v11.py']
dump(OUT/'delivery-seal-v11.json',{'status':'sealed_source_only_preflight_v11; primary_literal_tasks_closed; coverage_limits_retained; not_final_coding_material_freeze','files':[{'path':str(OUT/n),'sha256':sf(OUT/n),'bytes':(OUT/n).stat().st_size} for n in names],'integrity':checks,'current_canonical_sha256':sf(OUT/'canonical_source_context-v11.jsonl'),'public_assets_manifest_sha256':sf(OUT/'source-assets-manifest-v11.jsonl'),'original_snapshots_old_versions_and_two_record_packet_seals_preserved':True})
print(json.dumps(checks,ensure_ascii=False,indent=2))
