"""Apply only literal, source-SHA-bound scan transcription and neutral table geometry.

Original frame IDs, old packets and old transcripts remain unchanged. The family
closure preserves ALL earlier exposed stable IDs as seeds, including old family
links, so correcting a body or splitting a family cannot wash prior exposure.
"""
from pathlib import Path
import json,copy,importlib.util,os,re,unicodedata
from collections import Counter,defaultdict
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sp=importlib.util.spec_from_file_location('preflight',OUT/'build_full_frame_preflight_v2.py');pr=importlib.util.module_from_spec(sp);sp.loader.exec_module(pr)
rows=pr.readrows;sha=pr.sha;sf=pr.shafile;jl=pr.jsonl;dump=pr.dump
tr=json.loads((OUT/'care-source-transcriptions-v8.json').read_text());s=tr['source_pdf_sha256'];paras=tr['source_transcriptions']
src=next(x for x in json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text())['files'] if x['sha256']==s);assert sf(src['snapshot'])==s
data=rows(OUT/'canonical_source_context-v7.jsonl');D={r['id']:r for r in data};old=copy.deepcopy(D)
body=rows(OUT/'body-source-QA-v7.jsonl');BQ={x['record_id']:x for x in body};ctx=rows(OUT/'context-source-QA-v7.jsonl');CQ={(x['record_id'],x['context_id']):x for x in ctx}
pending=rows(OUT/'source-exceptions-v7.jsonl');resolved=[];remaining=[];changes=[];pages=[];geometry=[]
for i in range(1,19):
 path=OUT/('source-visual-v7' if i<4 else 'source-visual-v8')/'pages'/f'cde-care-{i:02}.png'
 pages.append({'source_pdf_sha256':s,'physical_page':i,'printed_page':i if i<4 else i-3 if i<9 else ['I','II','III','IV'][i-9] if i<13 else i-12,'path':str(path),'sha256':sf(path)})
P={p['physical_page']:p for p in pages}
def get_text(r,n,f):return r['text'] if n is None else dict(pr.pr.text_values(n))[f]
def set_text(r,n,f,t):
 if n is None:r['text']=t
 elif '[' not in f:n[f]=t
 else:
  k,ix=f.rstrip(']').split('[');n[k][int(ix)]=t
def attach(r,ps):
 ats={x['attachment_id']:x for x in r.get('source_attachments',[])}
 for i in ps:
  p=P[i];a={'attachment_id':'SOURCEPAGE-'+p['sha256'][:20],'sha256':p['sha256'],'relative_path':os.path.relpath(p['path'],OUT),'source_pdf_sha256':s,'physical_page':i,'printed_page':p['printed_page'],'kind':'original_binary_rendered_source_page'};ats[a['attachment_id']]=a
 r['source_attachments']=list(ats.values())
for e in pending:
 if e['source_sha256']!=s:remaining.append(e);continue
 r=D[e['record_id']];n=next((x for x in r['contexts'] if x['context_id']==e['context_id']),None);t=get_text(r,n,e['field']);new=t
 # This phrase was actually read on physical p2. It is not a semantic rewrite.
 if '便于在整个研发过程中及时高效地与药审中心开展沟通交流。' in t:new=t.replace('便于在整个研发过程中及时高效地与药审中心开展沟通交流。','便于在整个开发过程中及时高效地与药审中心开展沟通交流。')
 target=pr.norm(new);matches=[p for p in paras if target in pr.norm(p['text'])];method='AI_visual_primary_scanned_page_independent_literal_correspondence'
 if not matches and new.startswith('•'):
  stripped=pr.norm(new[1:]);matches=[p for p in paras if stripped==pr.norm(p['text']) and any(i in [13,14,17] for i in p['physical_pages'])];method='AI_visual_actual_solid_round_list_bullet_and_literal_text_correspondence'
 table=None
 if not matches:
  for tab in tr['actual_tables']:
   for ix,cells in enumerate(tab['rows']):
    if cells and pr.norm(new)==pr.norm(' | '.join(cells)):
     table={**tab,'actual_data_row_index_zero_based':ix};matches=[{'source_paragraph_id':f"CARE-TABLE-P{tab['physical_page']}-R{ix}",'physical_pages':[tab['physical_page']],'text':' | '.join(cells),'text_sha256':sha((' | '.join(cells)).encode())}];method='AI_visual_actual_five_column_source_table_cells_and_geometry_literal_serialization';break
   if matches:break
 if not matches:remaining.append(e);continue
 expected=e.get('pages',e.get('locator',{}).get('pages',[]));m=next((p for p in matches if set(expected)&set(p['physical_pages'])),matches[0]);ps=m['physical_pages']
 if new!=t:
  assert 2 in ps and target in pr.norm(m['text']);set_text(r,n,e['field'],new)
  changes.append({'record_id':r['id'],'context_id':e['context_id'],'field':e['field'],'old_text':t,'new_text':new,'old_text_sha256':sha(t.encode()),'new_text_sha256':sha(new.encode()),'actual_source_pdf_sha256':s,'actual_physical_pages':ps,'actual_printed_pages':[P[i]['printed_page'] for i in ps],'rendered_source_page_sha256':[P[i]['sha256'] for i in ps],'source_paragraph_id':m['source_paragraph_id'],'difference':'旧转写“整个研发过程中”；实际同版原图为“整个开发过程中”。','coding_dimension_judgment':False})
 ev={**e,'source_snapshot_sha256_verified':True,'source_literal_status':method,'actual_source_paragraph_id':m['source_paragraph_id'],'actual_source_paragraph_transcription_sha256':m['text_sha256'],'physical_pages':ps,'rendered_source_page_sha256':[P[i]['sha256'] for i in ps],'projected_field_sha256':sha(new.encode()),'source_text_changed':new!=t,'human_coding':False,'dimension_judgment':False}
 resolved.append(ev);attach(r,ps)
 if n is None:BQ[r['id']]['literal_status']=method;BQ[r['id']]['projected_body_sha256']=sha(new.encode());BQ[r['id']]['source_visual_review_v8']=ev
 else:
  for ft in CQ[(r['id'],n['context_id'])]['policy_text_fields']:
   if ft['field']==e['field']:ft['literal_status']=method;ft['projected_text_sha256']=sha(new.encode());ft['source_visual_review_v8']=ev
 if table:
  gid='CTX-SRCTABLE-'+sha((r['id']+s+str(table['physical_page'])).encode())[:20]
  st={'physical_pages':[table['physical_page']],'printed_pages':[P[table['physical_page']]['printed_page']],'column_indices':list(range(5)),'physical_grid_row_index_zero_based':table['actual_data_row_index_zero_based']+1,'grid_row_index_convention':'0 denotes actual header row','row_cell_column_pairs':[{'column_index':i,'header_index':i,'cell_index':i} for i in range(5)],'physical_merged_cells':[],'source_image_sha256':P[table['physical_page']]['sha256'],'related_context_ids':[n['context_id']] if n else []}
  gn={'context_id':gid,'kind':'source_table_row_geometry','source_document':'D-'+s[:16],'title':table['title'],'headers':table['headers'],'row_cells':table['rows'][table['actual_data_row_index_zero_based']],'structure':st,'source_ref':{'sha256':s,'source_resource_id':'SOURCE-'+s,'locator':copy.deepcopy(st)}}
  if not any(x['context_id']==gid for x in r['contexts']):r['contexts'].append(gn);geometry.append({'record_id':r['id'],'context_id':gid,'actual_source_pdf_sha256':s,'physical_page':table['physical_page'],'five_columns_no_merged_cells':True,'source_page_sha256':P[table['physical_page']]['sha256']})
  if n:n['structure']['source_table_geometry_context_id']=gid;n['source_ref']['locator']=copy.deepcopy(n['structure'])
  ctx.append({'record_id':r['id'],'context_id':gid,'kind':gn['kind'],'primary_source_sha256':s,'source_identity_methods':['actual_original_binary_rendered_source_table'],'policy_text_fields':[{'field':f,'projected_text_sha256':sha(t.encode()),'literal_status':'AI_visual_actual_source_table_cell_geometry'} for f,t in pr.pr.text_values(gn)],'textless_structure':False})
# Check previously v7-resolved literals against the reopened corrected audit transcript.
recheck=[]
for ev in json.loads((OUT/'source-visual-review-v7.json').read_text())['resolved_occurrences']:
 r=D[ev['record_id']];n=next((x for x in r['contexts'] if x['context_id']==ev['context_id']),None);t=get_text(r,n,ev['field']);ok=any(pr.norm(t) in pr.norm(p['text']) for p in paras);recheck.append({'record_id':r['id'],'context_id':ev['context_id'],'field':ev['field'],'source_pdf_sha256':s,'current_text_sha256':sha(t.encode()),'reopened_actual_source_literal_correspondence':ok})
assert all(x['reopened_actual_source_literal_correspondence'] for x in recheck),'Do not retain an unsupported earlier literal assertion.'
jl(OUT/'canonical_source_context-v8.jsonl',data);jl(OUT/'body-source-QA-v8.jsonl',body);jl(OUT/'context-source-QA-v8.jsonl',ctx);jl(OUT/'source-exceptions-v8.jsonl',remaining)
dump(OUT/'source-visual-review-v8.json',{'status':'source_only_AI_visual_review_not_human_coding_or_final_material_freeze','source_pdf':src,'all_18_actual_rendered_pages_opened':pages,'independent_transcription_file':{'path':str(OUT/'care-source-transcriptions-v8.json'),'sha256':sf(OUT/'care-source-transcriptions-v8.json')},'resolved_occurrences':resolved,'prior_v7_literal_assertions_rechecked':recheck,'prior_independent_audit_transcript_corrections':tr['prior_audit_transcription_corrections'],'public_source_text_changes':changes,'neutral_source_table_geometry_additions':geometry,'unmatched_source_fields_retained':len(remaining),'no_label_coding':True})
dump(OUT/'source-text-changes-v8.json',{'source_pdf_sha256':s,'changes':changes,'body_changes_from_v7_N':sum(x['context_id'] is None for x in changes),'context_field_changes_from_v7_N':sum(x['context_id'] is not None for x in changes),'audit_transcript_changes_separate_from_public_text_changes':True})
# Same exact baseline family algorithm, stable-ID monotone exposure closure.
frame=rows(ROOT/'00-baseline/source-only-frame.jsonl');F={r['id']:r for r in frame};exp=json.loads((ROOT/'01-review/exposure-ids.json').read_text());seed=set(exp['excluded_ids']);direct=set(exp['direct_exposure_ids']);assert len(seed)==3037 and len(direct)==2770 and direct<=seed
def family(t):
 n=''.join(c for c in unicodedata.normalize('NFKC',t) if not c.isspace() and not unicodedata.category(c).startswith('P'));return 'TEXTFAM-'+sha(n.encode())
groups=defaultdict(set);bindings=[]
for r in data:
 f=F[r['id']];assert family(f['unit_text'])==f['normalized_text_family']['family_id'];fam=family(r['text']);groups[fam].add(r['id'])
 bindings.append({'id':r['id'],'department':f['analysis_group'],'original_frame_body_sha256':f['unit_text_sha256'],'projected_body_sha256':sha(r['text'].encode()),'body_changed':r['text']!=f['unit_text'],'original_family_id':f['normalized_text_family']['family_id'],'projected_family_id':fam,'primary_source_sha256':r['source_ref']['sha256'],'original_context_sha256':f['shared_context_identity']['model_contexts_sha256'],'projected_context_sha256':sha(pr.canonical(r['contexts']).encode()),'projected_record_sha256':sha(pr.canonical(r).encode())})
closed=seed|set().union(*(ids for ids in groups.values() if ids&seed));oldremaining=set(F)-seed;newremaining=set(F)-closed;newids=sorted(closed-seed);changed=[x for x in bindings if x['body_changed']]
jl(OUT/'material-record-bindings-v8.jsonl',bindings)
dump(OUT/'family-exposure-impact-v8.json',{'normalization':'NFKC; remove Unicode whitespace and P* punctuation; retain all other symbols and case; verified baseline identity for all4481','original_family_N':len({x['normalized_text_family']['family_id'] for x in frame}),'projected_family_N':len(groups),'changed_body_N':len(changed),'changed_body_records':changed,'changed_family_assignment_N':sum(x['original_family_id']!=x['projected_family_id'] for x in bindings),'historical_direct_exposure_N':len(direct),'old_closed_excluded_N':len(seed),'recomputed_closed_excluded_N':len(closed),'prior_all_closed_IDs_seeded_not_only_direct_IDs':True,'old_family_exposure_links_preserved_by_stable_ID':True,'prior_exposure_lost_IDs':sorted(seed-closed),'newly_closed_excluded_ids':newids,'old_remaining_pool_N':len(oldremaining),'recomputed_remaining_pool_N':len(newremaining),'newly_remaining_IDs':sorted(newremaining-oldremaining),'remaining_pool_membership_unchanged':newremaining==oldremaining,'remaining_by_department':dict(Counter(F[i]['analysis_group'] for i in newremaining)),'source_projection_v8_sha256':sf(OUT/'canonical_source_context-v8.jsonl'),'source_fact_review_not_added_to_label_development_direct_exposure':True,'remaining_pool_not_final_frozen_sample':True})
jobs=rows(OUT/'grouped-source-review-jobs-v7.jsonl');remainkeys={(x['source_sha256'],x['text_sha256']) for x in remaining};jobs=[x for x in jobs if (x['actual_primary_source_sha256'],x['text_sha256']) in remainkeys]
for x in jobs:x['occurrences']=[e for e in remaining if (e['source_sha256'],e['text_sha256'])==(x['actual_primary_source_sha256'],x['text_sha256'])];x['occurrence_N']=len(x['occurrences'])
jl(OUT/'grouped-source-review-jobs-v8.jsonl',jobs)
counts=Counter('body_literal_'+q['literal_status'] for q in body)
counts.update({'contexts':len(ctx),'textless_contexts':sum(q.get('textless_structure',False) for q in ctx)})
for q in ctx:
 for f in q['policy_text_fields']:counts['context_literal_'+f['literal_status']]+=1
qa=json.loads((OUT/'source-QA-summary-v7.json').read_text());qa.update({'status':'full_frame_source_preflight_v8_care_scan_all18_pages_literal_review; pending_items_retained; not_material_freeze','counts':dict(counts),'output':{'path':str(OUT/'canonical_source_context-v8.jsonl'),'sha256':sf(OUT/'canonical_source_context-v8.jsonl')},'pending_issue_N':len(remaining),'pending_issue_types':dict(Counter(x['issue_type'] for x in remaining)),'pending_unique_source_text_N':len(jobs),'pending_unique_job_fragment_types':dict(Counter(t for x in jobs for t in x['fragment_types'])),'source_only_new_visual_resolved_occurrence_N':len(resolved),'body_changes_N':len(changed),'v8_body_changes_from_v7_N':sum(x['context_id'] is None for x in changes),'v8_context_field_changes_from_v7_N':sum(x['context_id'] is not None for x in changes),'new_neutral_geometry_node_N':len(geometry),'final_material_freeze_completed':False});dump(OUT/'source-QA-summary-v8.json',qa)
print(json.dumps({'resolved_occurrences_N':len(resolved),'pending_occurrences_N':len(remaining),'pending_unique_N':len(jobs),'canonical_sha256':sf(OUT/'canonical_source_context-v8.jsonl'),'body_changes_from_baseline_N':len(changed),'body_changes_from_v7_N':sum(x['context_id'] is None for x in changes),'neutral_table_node_N':len(geometry),'family_N':len(groups),'remaining_N':len(newremaining),'pool_changed':newremaining!=oldremaining},ensure_ascii=False,indent=2))
