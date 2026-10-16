"""Source extraction repair and grouped physical-source work queue; no labels."""
from pathlib import Path
import json,re,subprocess,importlib.util,copy
from collections import Counter,defaultdict
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sp=importlib.util.spec_from_file_location('preflight',OUT/'build_full_frame_preflight_v2.py');pr=importlib.util.module_from_spec(sp);sp.loader.exec_module(pr)
rows=pr.readrows;sha=pr.sha;sf=pr.shafile;jl=pr.jsonl;dump=pr.dump
mf=json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text());BS={r['sha256']:r for r in mf['files']};data=rows(OUT/'canonical_source_context-v5.jsonl');D={r['id']:r for r in data};pending=rows(OUT/'source-exceptions-v5.jsonl');body=rows(OUT/'body-source-QA-v5.jsonl');BQ={r['record_id']:r for r in body};ctx=rows(OUT/'context-source-QA-v5.jsonl');CQ={(r['record_id'],r['context_id']):r for r in ctx};extract={};resolved=[];remaining=[]
glyph_source=next(s for s in BS if s.startswith('41fd5850'));glyph_proof=OUT.parent/'coverage01/source-review-child/source-review.json';g=json.loads(glyph_proof.read_text());assert all(x.get('raw_extraction_match_after_audit_only_fullstop_map') for x in g['checked_context_occurrences'] if x['source_sha256']==glyph_source)
def clean_footer(t):
 ps=t.split('\f');out=[];removed=[]
 for i,p in enumerate(ps,1):
  ls=p.splitlines();last=next((j for j in range(len(ls)-1,-1,-1) if ls[j].strip()),None)
  if last is not None and re.fullmatch(r'\s*[—－\-]*\s*\d{1,3}\s*[—－\-]*\s*',ls[last]):removed.append({'physical_page':i,'literal_bottom_marker':ls.pop(last).strip()})
  out.append('\n'.join(ls))
 return '\f'.join(out),removed
for e in pending:
 s=e['source_sha256'];src=BS[s]
 if Path(src['snapshot']).suffix!='.pdf':remaining.append(e);continue
 if s not in extract:
  raw=subprocess.run(['pdftotext','-raw',src['snapshot'],'-'],capture_output=True,text=True,timeout=30);layout=subprocess.run(['pdftotext','-layout',src['snapshot'],'-'],capture_output=True,text=True,timeout=30);assert raw.returncode==layout.returncode==0
  cr,rf=clean_footer(raw.stdout);cl,lf=clean_footer(layout.stdout);extract[s]={'raw':raw.stdout,'layout':layout.stdout,'clean_raw':cr,'clean_layout':cl,'raw_bottom_markers':rf,'layout_bottom_markers':lf,'raw_NFKC':pr.norm(raw.stdout),'clean_raw_NFKC':pr.norm(cr),'clean_layout_NFKC':pr.norm(cl),'contains_CJK_text':any('\u4e00'<=c<='\u9fff' for c in layout.stdout),'extractable_nonwhitespace_N':len(pr.norm(layout.stdout))}
 r=D[e['record_id']];n=next((n for n in r['contexts'] if n['context_id']==e['context_id']),None);text=r['text'] if n is None else dict(pr.pr.text_values(n))[e['field']];x=extract[s];nt=pr.norm(text);status=None
 if nt in x['raw_NFKC']:status='actual_primary_PDF_raw_order_NFKC_whitespace_literal'
 elif nt in x['clean_raw_NFKC'] or nt in x['clean_layout_NFKC']:status='actual_primary_literal_join_bottom_printed_page_markers_including_multiple_dashes'
 elif s==glyph_source and pr.norm(text.replace('。','.')) in x['raw_NFKC']:status='actual_primary_raw_text_under_source_specific_visually_reviewed_fullstop_glyph_alias'
 if status:
  v={**e,'resolved_source_literal_status':status,'source_snapshot_sha256_verified':sf(src['snapshot'])==s,'unit_or_context_source_text_changed':False}
  if status.endswith('glyph_alias'):v['glyph_correspondence_evidence']={'path':str(glyph_proof),'sha256':sf(glyph_proof),'map':'projected Chinese fullstop。 corresponds to source extraction .; only target。→. is used for audit; decimal ASCII dots and output text remain unchanged','limits':'Alias was visually checked on physical44 and47; mechanistic byte/text correspondence across the same PDF is reported separately from an AI visual reading of every paragraph.'}
  resolved.append(v)
  if n is None:BQ[e['record_id']]['literal_status']=status;BQ[e['record_id']]['source_layout_review_v6']=v
  else:
   q=CQ[(e['record_id'],e['context_id'])]
   for ft in q['policy_text_fields']:
    if ft['field']==e['field']:ft['literal_status']=status;ft['source_layout_review_v6']=v
 else:
  e=copy.deepcopy(e)
  if not x['extractable_nonwhitespace_N']:e['fragment_type']='raster_PDF_no_text_layer'
  elif n and n['kind']=='boundary' and n.get('text')=='EOF':e['fragment_type']='structural_EOF_marker_not_policy_text'
  elif any(z in text for z in ['→','├','└']) and '图' in text[:20]:e['fragment_type']='diagram_branch_and_geometry_transcription'
  elif ' | ' in text:e['fragment_type']='flattened_table_row_requires_original_cell_geometry'
  elif e['issue_type']=='primary_locator_pending_alternate_bundle_fallback_rejected':e['fragment_type']='candidate_aggregate_primary_identity_not_per_leaf'
  elif not x['contains_CJK_text']:e['fragment_type']='PDF_font_character_mapping_or_raster_content'
  else:e['fragment_type']='source_literal_or_column_or_unicode_difference_requires_page_check'
  remaining.append(e)
jl(OUT/'body-source-QA-v6.jsonl',body);jl(OUT/'context-source-QA-v6.jsonl',ctx);jl(OUT/'source-exceptions-v6.jsonl',remaining);jl(OUT/'source-layout-resolved-v6.jsonl',resolved)
dump(OUT/'source-layout-extractors-v6.json',{'sources':[{'source_sha256':s,'actual_primary_snapshot':BS[s]['snapshot'],'raw_bottom_markers':x['raw_bottom_markers'],'layout_bottom_markers':x['layout_bottom_markers'],'extractable_nonwhitespace_N':x['extractable_nonwhitespace_N'],'contains_CJK_text':x['contains_CJK_text']} for s,x in extract.items()],'text_changes_performed':False,'only_last_nonempty_bottom_page_number_lines_removed_in_audit':True})
groups=defaultdict(list)
for e in remaining:groups[(e['source_sha256'],e['text_sha256'])].append(e)
jobs=[]
for (s,ts),es in groups.items():
 first=es[0];r=D[first['record_id']];n=next((n for n in r['contexts'] if n['context_id']==first['context_id']),None);t=r['text'] if n is None else dict(pr.pr.text_values(n))[first['field']];pages=set();roles=set()
 for e in es:
  rr=D[e['record_id']];nn=next((n for n in rr['contexts'] if n['context_id']==e['context_id']),None)
  if nn is None:roles.add('mandatory_primary_unit_body');pages.update(rr['pages'])
  else:
   pages.update(nn['structure'].get('physical_pages',nn['structure'].get('pages',[])))
   parent={z['context_id']:z for z in rr['contexts']}.get(nn['structure'].get('parent_context_id'));roles.add('explicitly_cited_substantive_source_context' if parent and parent['kind']=='cited_reference' else 'retained_source_context_necessity_according_to_frozen_material_protocol_not_dimension_decision')
 jobs.append({'job_id':'SOURCEJOB-'+sha((s+ts).encode())[:20],'actual_primary_source_sha256':s,'actual_primary_snapshot':BS[s]['snapshot'],'text_sha256':ts,'full_source_field_text':t,'physical_pages':sorted(pages),'fragment_types':sorted({e.get('fragment_type','source_review_pending') for e in es}),'roles':sorted(roles),'occurrence_N':len(es),'mandatory_body_occurrence_N':sum(e['context_id'] is None for e in es),'occurrences':es,'source_only_review_task':'Check the same source bytes once for this exact textSHA; retain paragraph/line/page differences per occurrence. Record original typography, actual table/graph geometry and version. Repair only source-supported transcription, never dimension labels.'})
jobs.sort(key=lambda j:(-j['mandatory_body_occurrence_N'],-j['occurrence_N'],j['actual_primary_source_sha256'],j['text_sha256']));jl(OUT/'grouped-source-review-jobs-v6.jsonl',jobs)
by=defaultdict(list)
for j in jobs:by[j['actual_primary_source_sha256']].append(j)
dump(OUT/'grouped-source-review-plan-v6.json',{'groups':[{'actual_primary_source_sha256':s,'actual_primary_snapshot':BS[s]['snapshot'],'unique_text_jobs_N':len(js),'occurrence_N':sum(j['occurrence_N'] for j in js),'mandatory_body_occurrence_N':sum(j['mandatory_body_occurrence_N'] for j in js),'physical_pages':sorted({p for j in js for p in j['physical_pages']}),'fragment_type_counts':dict(Counter(t for j in js for t in j['fragment_types'])),'job_ids':[j['job_id'] for j in js]} for s,js in sorted(by.items(),key=lambda x:-sum(j['occurrence_N'] for j in x[1]))],'structural_EOF_markers_already_separated_N':118,'structural_EOF_is_not_literal_policy_text':True,'contemporaneous_version_exception':{'record_id':'RECODE25-00064','status':'unresolved_contemporaneous_reference_version','source_investigation_file':str(ROOT/'02-methods/source-supplements/MATERIAL-00064-source-investigation.json'),'requires_separate_version_binding_not_a_zero_dimension_label':True},'review_order':'Mandatory bodies, explicitly cited substantive context, table/graph geometry, and remaining source layout; deduplicate by actual primary SHA+textSHA. Necessity here is source-material protocol, not a construct judgment.'})
qa=json.loads((OUT/'source-QA-summary-v5.json').read_text());count=Counter()
for b in body:count['body_literal_'+b['literal_status']]+=1
for q in ctx:
 count['contexts']+=1;count['textless_contexts']+=q['textless_structure'];count['source_identity_resolved_contexts']+=bool(q['primary_source_sha256'])
 for f in q['policy_text_fields']:count['context_literal_'+f['literal_status']]+=1
qa.update({'status':'full_frame_source_preflight_v6_complete_with_grouped_remaining_visual_and_version_work; not_final_material_freeze','source_only_canonical_projection':qa['output'],'counts':dict(count),'source_layout_resolution_occurrence_N':len(resolved),'source_layout_resolution_types':dict(Counter(r['resolved_source_literal_status'] for r in resolved)),'pending_issue_N':len(remaining),'pending_issue_types':dict(Counter(e['issue_type'] for e in remaining)),'pending_unique_source_text_N':len(jobs),'pending_fragment_types':dict(Counter(e.get('fragment_type') for e in remaining)),'canonical_v5_bytes_unchanged':True,'final_material_freeze_completed':False,'machine_human_source_content_equivalence_complete':False,'review_job_queue':{'path':str(OUT/'grouped-source-review-jobs-v6.jsonl'),'sha256':sf(OUT/'grouped-source-review-jobs-v6.jsonl')},'review_group_plan':{'path':str(OUT/'grouped-source-review-plan-v6.json'),'sha256':sf(OUT/'grouped-source-review-plan-v6.json')}});dump(OUT/'source-QA-summary-v6.json',qa)
print(json.dumps({'resolved_N':len(resolved),'resolved_types':qa['source_layout_resolution_types'],'pending_N':len(remaining),'unique_jobs_N':len(jobs),'pending_types':qa['pending_fragment_types'],'canonical_sha256':qa['source_only_canonical_projection']['sha256']},ensure_ascii=False,indent=2))
