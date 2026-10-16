"""Literal source and source geometry integration only; no coding data is read."""
from pathlib import Path
import json,hashlib,re,copy,subprocess,os,importlib.util
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sp=importlib.util.spec_from_file_location('preflight',OUT/'build_full_frame_preflight_v2.py');pr=importlib.util.module_from_spec(sp);sp.loader.exec_module(pr)
rows=pr.readrows;jl=pr.jsonl;dump=pr.dump;sha=pr.sha;sf=pr.shafile
BASE=OUT/'canonical_source_context-v9.jsonl';data=rows(BASE);D={r['id']:r for r in data}
BS={x['sha256']:x for x in json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text())['files']}
body=rows(OUT/'body-source-QA-v9.jsonl');BQ={x['record_id']:x for x in body};ctx=rows(OUT/'context-source-QA-v9.jsonl');CQ={(x['record_id'],x['context_id']):x for x in ctx}
pending=rows(OUT/'source-exceptions-v9.jsonl');resolved=[];changes=[];newnodes=[];patchlog=[]
def texts(r,c,f):return r['text'] if c is None else dict(pr.pr.text_values(c))[f]
def attach(r,p,s,page,kind='original_binary_rendered_source_page',extra=None):
 assert p.is_file();h=sf(p);a={'attachment_id':'SOURCEASSET-'+h[:20],'sha256':h,'relative_path':os.path.relpath(p,OUT),'source_pdf_sha256':s,'physical_page':page,'kind':kind}
 if extra:a.update(extra)
 ats={x['attachment_id']:x for x in r.get('source_attachments',[])};ats[a['attachment_id']]=a;r['source_attachments']=list(ats.values());return h
def addnode(r,n,status):
 assert not any(x['context_id']==n['context_id'] for x in r['contexts']);r['contexts'].append(n)
 q={'record_id':r['id'],'context_id':n['context_id'],'kind':n['kind'],'primary_source_sha256':n['source_ref']['sha256'],'source_identity_methods':['actual_binary_source_or_actual_source_page_geometry'],'policy_text_fields':[{'field':k,'projected_text_sha256':sha(v.encode()),'literal_status':status} for k,v in pr.pr.text_values(n)],'textless_structure':not any(True for _ in pr.pr.text_values(n))};ctx.append(q);CQ[(r['id'],n['context_id'])]=q;newnodes.append({'record_id':r['id'],'context_id':n['context_id'],'kind':n['kind']})
def setqa(e,status,evidence):
 if e['context_id'] is None:BQ[e['record_id']]['literal_status']=status;BQ[e['record_id']]['source_review_v10']=evidence
 else:
  q=CQ[(e['record_id'],e['context_id'])]
  for f in q['policy_text_fields']:
   if f['field']==e['field']:f['literal_status']=status;f['source_review_v10']=evidence
 resolved.append({**e,'source_literal_status':status,'source_review_v10':evidence})

# Source-specific running header/page-footer cleaning is audit-only. Internal
# spaces in fullwidth printed page digits are retained in the archived raw text.
SG=next(s for s in BS if s.startswith('41fd5850064ce8c3'))
raw=subprocess.run(['pdftotext','-raw',BS[SG]['snapshot'],'-'],capture_output=True,text=True,timeout=30);assert raw.returncode==0 and sf(BS[SG]['snapshot'])==SG
clean=[];removed=[]
for page,t in enumerate(raw.stdout.split('\f'),1):
 ls=t.splitlines()
 if len(ls)>=2 and '国务院公报' in ls[-1] and '部门文件' in ls[-1] and re.fullmatch(r'\s*[—－\-]+\s*[０-９0-9\s]+\s*[—－\-]+\s*',ls[-2]):
  removed.append({'physical_page':page,'original_raw_last_two_lines':ls[-2:],'source_role':'printed page footer and running header, observed on actual pages44–47'});ls=ls[:-2]
 clean.append('\n'.join(ls))
clean='\f'.join(clean)
govkeys=set()
for e in pending:
 if e['source_sha256']!=SG:continue
 r=D[e['record_id']];n=next((x for x in r['contexts'] if x['context_id']==e['context_id']),None);t=texts(r,n,e['field']);assert pr.norm(t.replace('。','.')) in pr.norm(clean)
 ps=e.get('pages',e.get('locator',{}).get('pages',[]));assert ps and set(ps)<=set([44,45,46,47]);imsha=[attach(r,OUT/'source-visual-v9/pages'/f'{SG[:16]}-{p}.png',SG,p) for p in ps]
 ev={'actual_primary_source_sha256':SG,'physical_pages':ps,'rendered_source_page_sha256':imsha,'public_text_unchanged':True,'raw_text_sha256':sha(raw.stdout.encode()),'audit_join_sha256':sha(clean.encode()),'glyph_correspondence':'target。maps to same-source extracted ASCII.; actual Chinese punctuation observed on original pages','source_specific_footer_digit_spacing_handled':True,'AI_source_fact_review':True}
 setqa(e,'actual_primary_PDF_source_specific_running_header_footer_and_spaced_fullwidth_page_number_exclusion_literal_join',ev);govkeys.add((e['record_id'],e['context_id'],e['field']))

# The independent source graph/table reviewer sealed the exact current field
# hashes and actual binary source hashes. Only neutral source geometry is copied.
AP=ROOT/'01-review/source-graph-table-sol';seal=json.loads((AP/'delivery-sha256.json').read_text())
def manifest_entries(x):
 if isinstance(x,list):return x
 for k in ['files','outputs']:
  if k in x:return x[k]
 raise ValueError('unknown source delivery manifest')
entries=manifest_entries(seal);input_sha_checks=[]
for x in entries:
 p=Path(x.get('path',x.get('absolute_path','')))
 if not p.is_absolute():p=AP/p
 assert sf(p)==x['sha256'];input_sha_checks.append({'path':str(p),'sha256':x['sha256']})
assert sf(AP/'neutral-patches.jsonl')=='73f3e34b7fffde5475c3151770091341117b70ba1a0ad14d320dc5c1826a8b42'
patches=rows(AP/'neutral-patches.jsonl');am=json.loads((AP/'source-page-assets-manifest.json').read_text());assets={x['asset_path']:x for x in am['assets']}
def neutral(x):
 if isinstance(x,dict):return {('printed_edge_text' if k=='label' else k):neutral(v) for k,v in x.items()}
 if isinstance(x,list):return [neutral(v) for v in x]
 return x
graphkeys=set()
for p in patches:
 s=p['source_sha256'];assert sf(BS[s]['snapshot'])==s;byrecord={}
 for t in p['targets']:
  r=D[t['record_id']];n=next((x for x in r['contexts'] if x['context_id']==t['context_id']),None);old=texts(r,n,t['field']);assert sha(old.encode())==t['text_sha256']==p['expected_old_text_sha256'];assert (r['source_ref'] if n is None else n['source_ref'])['sha256']==s
  key=(r['id'],t['context_id'],t['field']);graphkeys.add(key);byrecord.setdefault(r['id'],[]).append(t)
  meta={'source_representation':p['additions']['source_representation'],'is_original_continuous_prose_quote':False,'physical_pages':t['verified_physical_pages'],'printed_pages':t['verified_printed_pages'],'field_text_sha256':t['text_sha256']}
  if n is None:r['body_source_representation']=meta
  else:n.setdefault('structure',{})['source_text_representation']=meta
  e=next(x for x in pending if (x['record_id'],x['context_id'],x['field'])==key)
  ev={'actual_primary_source_sha256':s,'source_patch_id':p['patch_id'],'source_patch_job_id':p['job_id'],'expected_source_field_sha256':t['text_sha256'],'actual_physical_pages':t['verified_physical_pages'],'actual_printed_pages':t['verified_printed_pages'],'representation':meta,'public_text_unchanged':True,'AI_source_geometry_review':True}
  setqa(e,'actual_source_nodes_cells_and_geometry_representation_not_continuous_prose_quote',ev)
 for rid,ts in byrecord.items():
  r=D[rid];used=[]
  for path in p['additions']['evidence_assets']:
   a=assets[path];assert sf(Path(a['absolute_path']))==a['sha256'];assert a['source_sha256']==s;used.append(attach(r,Path(a['absolute_path']),s,a['physical_page'],'original_binary_rendered_source_crop' if a.get('crop_xywh_at_render_dpi') else 'original_binary_rendered_source_page',{'render_dpi':a['render_dpi'],'crop_xywh_at_render_dpi':a.get('crop_xywh_at_render_dpi')}))
  gid='CTX-SRCGEOMETRY-'+sha((rid+s+p['job_id']).encode())[:20];st=neutral(copy.deepcopy(p['additions']['source_structure']));st['related_context_ids']=[t['context_id'] for t in ts if t['context_id']];st['represented_body_field']=any(t['context_id'] is None for t in ts);st['source_representation']=p['additions']['source_representation'];st['is_original_continuous_prose_quote']=False
  n={'context_id':gid,'kind':'source_graph_or_table_geometry','source_document':'D-'+s[:16],'structure':st,'source_ref':{'sha256':s,'source_resource_id':'SOURCE-'+s,'locator':{'physical_pages':p['additions']['physical_pages'],'printed_pages':p['additions']['printed_pages'],'source_image_sha256':used}}}
  if st.get('caption'):n['caption']=st['caption']
  elif st.get('section_heading'):n['title']=st['section_heading']['text'] if isinstance(st['section_heading'],dict) else st['section_heading']
  addnode(r,n,'actual_source_geometry_caption_or_section_heading');patchlog.append({'patch_id':p['patch_id'],'record_id':rid,'new_context_id':gid,'old_field_SHA_guards_passed':len(ts),'source_pdf_sha256':s,'source_image_sha256':used,'public_text_replacement':False})

# A separately printed same-edition paragraph, not a word inserted into the graph.
SW=next(s for s in BS if s.startswith('0b5214578c2fd174'));SF=next(s for s in BS if s.startswith('7f5b1829d0030b34'));assert sf(BS[SW]['snapshot'])==SW
layout=subprocess.run(['pdftotext','-layout',BS[SW]['snapshot'],'-'],capture_output=True,text=True,timeout=30);assert layout.returncode==0
blocks=[{'local_paragraph_id':'W25-OUT-1','physical_pages':[2],'section':'二、调整范围；（一）基本目录；1.目录外西药和中成药','text':'（1）2020年1月1日（含，下同）至2025年6月30日（含，下同）期间，经国家药监部门批准上市的新通用名药品。'}, {'local_paragraph_id':'W25-OUT-5','physical_pages':[2],'section':'二、调整范围；（一）基本目录；1.目录外西药和中成药','text':'（5）2025年6月30日前，经国家药监部门批准上市的罕见病治疗药品。'}, {'local_paragraph_id':'W25-COMMERCIAL','physical_pages':[4],'heading_physical_pages':[3],'section':'二、调整范围；（二）商保创新药目录','text':'符合前述基本目录外药品申报条件（1）或条件（5）的独家药品，可以单独申报商保创新药目录或同时申报商保创新药目录、基本目录。'}]
for b in blocks:
 assert pr.norm(b['text']) in pr.norm(layout.stdout);b['text_sha256']=sha(b['text'].encode());b['source_resource_id']='SOURCE-'+SW;b['source_sha256']=SW;b['source_page_images']=[{'relative_path':f'source-visual-v10/pages/workscheme2025-{p}.png','sha256':sf(OUT/f'source-visual-v10/pages/workscheme2025-{p}.png'),'physical_page':p} for p in b['physical_pages']+b.get('heading_physical_pages',[])]
work={'source_resource_id':'SOURCE-'+SW,'source_sha256':SW,'document_title':'2025年国家基本医疗保险、生育保险和工伤保险药品目录及商业健康保险创新药品目录调整工作方案','document_year':2025,'snapshot':BS[SW]['snapshot'],'snapshot_sha256':SW,'document_number_established':False,'source_texts':[{'source_locator':{'physical_page':i},'text':t,'text_sha256':sha(t.encode()),'representation':'literal_pdftotext_layout_of_actual_PDF'} for i,t in enumerate(layout.stdout.split('\f'),1) if t.strip()],'visually_reviewed_selected_paragraphs':blocks,'original_source_title_and_year_viewed_on_physical1':True,'source_literal_word_or_printed_in_paragraph_on_physical4':True,'not_a_word_printed_in_FAQ_figure3':True}
dump(OUT/'source-library/workplan2025-full-source-v10.json',work)
extra=next(p for p in patches if p['job_id']=='SOURCEJOB-c9ecdc96c974ab6b6920')
for rid in sorted({x['record_id'] for x in extra['targets']}):
 r=D[rid];related=[x['context_id'] for x in extra['targets'] if x['record_id']==rid and x['context_id']]
 for b in blocks:
  for p in b['physical_pages']+b.get('heading_physical_pages',[]):attach(r,OUT/f'source-visual-v10/pages/workscheme2025-{p}.png',SW,p)
  gid='CTX-SRCPARAGRAPH-'+sha((rid+SW+b['local_paragraph_id']).encode())[:20];n={'context_id':gid,'kind':'same_edition_explicitly_cited_source_paragraph','source_document':'D-'+SW[:16],'text':b['text'],'structure':{'related_context_ids':related,'source_paragraph_id':b['local_paragraph_id'],'section_heading':b['section'],'heading_physical_pages':b.get('heading_physical_pages',[]),'citation_printed_in_figure':'详见《工作方案》'},'source_ref':{'sha256':SW,'source_resource_id':'SOURCE-'+SW,'locator':{'physical_pages':b['physical_pages'],'local_paragraph_id':b['local_paragraph_id']}}};addnode(r,n,'actual_same_edition_primary_source_paragraph_NFKC_whitespace_literal_and_actual_page_read')

# Preserve the successful July original-document provenance separately from the
# unresolved version of its expressly cited technical guideline. No coding rule
# or dimension-dependent decision is projected here.
TP=ROOT/'parallel-manuscript/source-00064-temporal';timeline=json.loads((TP/'source-timeline.json').read_text());tseal=json.loads((TP/'交付封存.json').read_text())
for x in tseal['outputs']:assert sf(Path(x['path']))==x['sha256']
literal=timeline['verified_literal_provenance'];assert sf(Path(literal['source_doc']))==literal['source_doc_sha256'];assert sf(Path(literal['text']))==literal['text_sha256']
neutral_timeline=[]
for x in timeline['timeline']:
 keep=['id','full_title','issuer','composition_date','publication_date','effective_date','draft_status','source_role','urls','carriers','locator','consultation_deadline','printing_date','official_republication_date']
 neutral_timeline.append({k:x[k] for k in keep if k in x})
tr={'source_resource_id':'SOURCE-REFERENCE-VERSION-CONDITIONAL-202007','document_title':'药品附条件批准上市申请审评审批工作程序（试行）中的技术指导原则引用版本记录','original_program_source_doc_sha256':literal['source_doc_sha256'],'original_program_source_doc':literal['source_doc'],'original_program_text_sha256':literal['text_sha256'],'original_program_text':literal['text'],'original_program_literal_provenance_status':'original_July2020_attachment2_sentence_confirmed','cited_title_verbatim':'药品附条件批准上市技术指导原则','cited_year_or_version_printed':False,'cited_technical_guideline_version_status':'not_uniquely_established','uniquely_bound_guideline_resource_id':None,'timeline':neutral_timeline,'source_version_limitations':timeline['remaining_unresolved'],'version_source_review_manifest_sha256':sf(TP/'交付封存.json'),'source_snapshot_doc_and_text_retained':True}
dump(OUT/'source-library/conditional-guideline-reference-version-v10.json',tr)

library=rows(OUT/'source-library/library.jsonl');library.extend([work,tr]);jl(OUT/'source-library/library-v10.jsonl',library)
idx=rows(OUT/'source-library/reference-index.jsonl');extraidx=[];ST=timeline['original_source_file_sha256'];needle=tr['cited_title_verbatim']
for r in data:
 for cid,f,t,s in [(None,'text',r['text'],r['source_ref']['sha256'])]+[(n['context_id'],k,v,n['source_ref']['sha256']) for n in r['contexts'] for k,v in pr.pr.text_values(n)]:
  if s==SF and '《工作方案》' in t:
   extraidx.append({'record_id':r['id'],'context_id':cid,'source_field':f,'source_field_text_sha256':sha(t.encode()),'resource_id':'SOURCE-'+SW,'literal_reference':'《工作方案》','literal_relation_type':'explicit_title_abbreviation_in_actual_2025_FAQ_source','unit_primary_source_sha256':r['source_ref']['sha256'],'reference_source_sha256':s,'target_title_and_year':'2025年国家基本医疗保险、生育保险和工伤保险药品目录及商业健康保险创新药品目录调整工作方案','target_source_sha256':SW,'binding_scope':'same_edition_document_reference; specific clauses remain separate source paragraphs','automatic_whole_document_applicability_binding':False})
  if s==ST and needle in t:
   extraidx.append({'record_id':r['id'],'context_id':cid,'source_field':f,'source_field_text_sha256':sha(t.encode()),'resource_id':tr['source_resource_id'],'literal_reference':needle,'literal_relation_type':'explicit_citation_with_unresolved_target_version','unit_primary_source_sha256':r['source_ref']['sha256'],'reference_source_sha256':s,'original_program_source_doc_sha256':literal['source_doc_sha256'],'target_source_sha256':None,'target_version_status':'not_uniquely_established','automatic_whole_document_applicability_binding':False})
idx.extend(extraidx);jl(OUT/'source-library/reference-index-v10.jsonl',idx)
for r in data:
 refs=[x for x in idx if x['record_id']==r['id']];r['source_references']=[{'source_resource_id':x['resource_id'],'context_id':x['context_id'],'source_field':x['source_field'],'literal_reference':x['literal_reference'],'literal_relation_type':x['literal_relation_type']} for x in refs]
 if not r['source_references']:r.pop('source_references')

remaining=[e for e in pending if (e['record_id'],e['context_id'],e['field']) not in govkeys|graphkeys];assert not remaining
jl(OUT/'canonical_source_context-v10.jsonl',data);jl(OUT/'body-source-QA-v10.jsonl',body);jl(OUT/'context-source-QA-v10.jsonl',ctx);jl(OUT/'source-exceptions-v10.jsonl',remaining);jl(OUT/'grouped-source-review-jobs-v10.jsonl',[])
dump(OUT/'source-integration-review-v10.json',{'status':'source_fact_review_and_geometry_integration; not_final_material_freeze','base_canonical_sha256':sf(BASE),'independent_graph_review_manifest_sha256':sf(AP/'delivery-sha256.json'),'graph_review_file_byte_checks':input_sha_checks,'resolved_source_occurrences':resolved,'source_graph_patch_integrations':patchlog,'new_source_contexts':newnodes,'public_body_text_changes_N':0,'public_existing_context_text_changes_N':0,'actual_Gov_running_header_pagefooter_raw_lines_excluded_for_audit':removed,'same_edition_workplan_source_paragraphs':blocks,'reference_version_resource_path':'source-library/conditional-guideline-reference-version-v10.json','remaining_literal_jobs_N':len(remaining),'external_reference_and_image_text_completeness_not_inferred_from_literal_match':True})
rm=rows(OUT/'material-record-bindings-v9.jsonl')
for x in rm:r=D[x['id']];assert x['projected_body_sha256']==sha(r['text'].encode());x['projected_context_sha256']=sha(pr.canonical(r['contexts']).encode());x['projected_record_sha256']=sha(pr.canonical(r).encode())
jl(OUT/'material-record-bindings-v10.jsonl',rm);fam=json.loads((OUT/'family-exposure-impact-v9.json').read_text());fam['source_projection_v10_sha256']=sf(OUT/'canonical_source_context-v10.jsonl');fam['all_body_bytes_identical_between_v9_and_v10']=True;dump(OUT/'family-exposure-impact-v10.json',fam)
counts=Counter('body_literal_'+x['literal_status'] for x in body);counts['contexts']=len(ctx);counts['textless_contexts']=sum(x['textless_structure'] for x in ctx)
for x in ctx:
 for f in x['policy_text_fields']:counts['context_literal_'+f['literal_status']]+=1
qa=json.loads((OUT/'source-QA-summary-v9.json').read_text());qa.update({'status':'full_frame_source_preflight_v10_primary_literal_jobs_closed_but_reference_and_image_text_coverage_gaps_retained; not_final_material_freeze','counts':dict(counts),'output':{'path':str(OUT/'canonical_source_context-v10.jsonl'),'sha256':sf(OUT/'canonical_source_context-v10.jsonl')},'pending_issue_N':0,'pending_issue_types':{},'pending_unique_source_text_N':0,'pending_unique_job_fragment_types':{},'v10_resolved_source_occurrences_N':len(resolved),'v10_primary_body_or_existing_context_text_changes_N':0,'v10_new_source_context_nodes_N':len(newnodes),'v10_graph_review_unique_jobs_N':len(patches),'v10_graph_review_target_occurrences_N':len(graphkeys),'v10_Gov_cross_page_occurrences_N':len(govkeys),'all_original_body_bytes_unchanged_claim':False,'body_changes_N':2,'final_material_freeze_completed':False,'external_reference_content_and_machine_text_completeness_certified':False,'old_v4_outputs_kept_as_history_not_current_QA':True});qa['outputs']=[];dump(OUT/'source-QA-summary-v10.json',qa)
print(json.dumps({'canonical_sha256':sf(OUT/'canonical_source_context-v10.jsonl'),'resolved_occurrence_N':len(resolved),'new_context_N':len(newnodes),'pending_literal_N':0,'extra_reference_occurrence_N':len(extraidx),'new_body_text_changes_N':0,'cumulative_body_changes_N':2,'final_freeze':False},ensure_ascii=False,indent=2))
