"""Resolve boundary source address through same-record source candidates and primary bytes."""
from pathlib import Path
import copy,json,importlib.util
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sp=importlib.util.spec_from_file_location('preflight',OUT/'build_full_frame_preflight_v2.py');pr=importlib.util.module_from_spec(sp);sp.loader.exec_module(pr)
rows=pr.readrows;sha=pr.sha;sf=pr.shafile;jl=pr.jsonl;dump=pr.dump
mf=json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text());BS={r['sha256']:r for r in mf['files']};BP={r['original']:r for r in mf['files']};F={r['id']:r for r in rows(ROOT/'00-baseline/source-only-frame.jsonl')};S={r['id']:r for r in rows(pr.SIDE) if r['id'] in F};data=rows(OUT/'canonical_source_context-v4.jsonl');QA=rows(OUT/'context-source-QA-v4.jsonl');Q={(q['record_id'],q['context_id']):q for q in QA};objects={};texts={};changes=[]
def literal(t,s):
 if s not in texts:
  txt,_=pr.pr.extract_snapshot_text(BS[s]['snapshot']);texts[s]=(txt,pr.remove_pdf_printed_footer(txt)[0] if txt is not None and Path(BS[s]['snapshot']).suffix=='.pdf' else txt)
 raw,clean=texts[s]
 if raw is not None and t in raw:return 'exact_primary_extracted_text'
 if raw is not None and pr.norm(t) in pr.norm(raw):return 'primary_NFKC_whitespace_only'
 if clean is not None and pr.norm(t) in pr.norm(clean):return 'primary_literal_join_across_bottom_printed_page_markers'
 return None
for r in data:
 rid=r['id'];by={n['context_id']:n for n in r['contexts']};candidate_paths={F[rid]['source_position']['candidate_file']}
 candidate_paths.update(l.get('source_binding',{}).get('candidate_path') for l in S[rid].get('policy_leaves',[]));candidate_paths.discard(None)
 for n in r['contexts']:
  if n['kind']!='boundary' or not n.get('text') or n['text']=='EOF':continue
  if literal(n['text'],n['source_ref']['sha256']):continue
  declared=n['structure'].get('paragraph_id');parent=by.get(n['structure'].get('parent_context_id'));ref=by.get(parent['structure'].get('parent_context_id')) if parent else None
  related_sources=set()
  if ref:
   for g in ref['structure'].get('child_groups',[]):
    if g['position']=='contexts':related_sources.update(by[c]['source_ref']['sha256'] for c in g['ordered_context_ids'] if c in by)
  opts={}
  for cp in candidate_paths:
   if cp not in BP:continue
   cs=BP[cp]['sha256']
   if cs not in objects:objects[cs]=json.loads(Path(BS[cs]['snapshot']).read_text())
   d=objects[cs]
   for p in d.get('paragraphs',[]):
    pid=p.get('id',p.get('paragraph_id'))
    if declared and pid!=declared:continue
    if pr.norm(n['text'])!=pr.norm(p.get('text','')):continue
    source=BP.get(p.get('source_file',d.get('source')))
    if not source:continue
    s=source['sha256'];status=literal(n['text'],s)
    if not status:continue
    # Candidate root is accepted only when it is the actual source of an
    # already bound member in the same explicit reference, never a heading.
    if not p.get('source_file') and s not in related_sources:continue
    opts[s]={'candidate_sha256':cs,'candidate_paragraph_id':pid,'actual_primary_source_sha256':s,'source_identity_basis':'explicit_candidate_paragraph_source_file' if p.get('source_file') else 'candidate_root_primary_source_also_bound_to_same_reference_member','physical_pages':p.get('pages',[]),'line_ids':p.get('line_ids',[]),'literal_status':status}
  if len(opts)!=1:continue
  s,proof=next(iter(opts.items()));before=n['source_ref']['sha256']
  if s==before:continue
  cid=n['context_id'];n['source_document']='D-'+s[:16];n['source_ref']['sha256']=s;n['source_ref']['source_resource_id']='SOURCE-'+s;n['source_ref']['locator']['physical_pages']=proof['physical_pages'];q=Q[(rid,cid)];q['primary_source_sha256']=s;q['source_identity_methods'].append('actual_same_record_candidate_address_and_primary_literal');q['boundary_source_review_v5']=proof
  for f in q['policy_text_fields']:f['literal_status']=proof['literal_status']
  changes.append({'record_id':rid,'context_id':cid,'operation':'correct_reference_boundary_source_using_explicit_source_address_and_actual_primary_literal','before_source_sha256':before,'after_source_sha256':s,'proof':proof,'text_unchanged':True})
  if parent and parent['kind']=='boundary_container' and parent['structure'].get('text_child_context_ids')==[cid]:
   old=parent['source_ref']['sha256'];parent['source_document']='D-'+s[:16];parent['source_ref']['sha256']=s;parent['source_ref']['source_resource_id']='SOURCE-'+s;parent['source_ref']['locator']['physical_pages']=proof['physical_pages'];Q[(rid,parent['context_id'])]['primary_source_sha256']=s;changes.append({'record_id':rid,'context_id':parent['context_id'],'operation':'correct_boundary_container_explicit_child_source','before_source_sha256':old,'after_source_sha256':s,'child_context_id':cid})
fixed={(c['record_id'],c['context_id']) for c in changes};pending=[p for p in rows(OUT/'source-exceptions-v4.jsonl') if (p['record_id'],p['context_id']) not in fixed];assert not list(pr.forbidden(data));path=OUT/'canonical_source_context-v5.jsonl';jl(path,data);jl(OUT/'context-source-QA-v5.jsonl',QA);jl(OUT/'body-source-QA-v5.jsonl',rows(OUT/'body-source-QA-v4.jsonl'));jl(OUT/'source-exceptions-v5.jsonl',pending);dump(OUT/'source-boundary-corrections-v5.json',{'strategy':'same-record actual source candidates plus explicit reference-member identity, not inherited heading or unit-ID exception','changes':changes})
rm=rows(OUT/'material-record-bindings-v4.jsonl');D={r['id']:r for r in data}
for b in rm:b['projected_context_sha256']=sha(pr.canonical(D[b['id']]['contexts']).encode());b['projected_record_sha256']=sha(pr.canonical(D[b['id']]).encode());assert b['projected_body_sha256']==sha(D[b['id']]['text'].encode())
jl(OUT/'material-record-bindings-v5.jsonl',rm);fa=json.loads((OUT/'family-exposure-impact-v4.json').read_text());fa['source_projection_v5_sha256']=sf(path);fa['v2_v3_v4_v5_bodies_byte_identical']=True;dump(OUT/'family-exposure-impact-v5.json',fa)
qa=json.loads((OUT/'source-QA-summary-v4.json').read_text());counts=Counter()
for q in QA:
 counts['contexts']+=1;counts['textless_contexts']+=q['textless_structure'];counts['source_identity_resolved_contexts']+=bool(q['primary_source_sha256'])
 for f in q['policy_text_fields']:counts['context_literal_'+f['literal_status']]+=1
for b in rows(OUT/'body-source-QA-v5.jsonl'):counts['body_literal_'+b['literal_status']]+=1
qa.update({'status':'full_frame_source_only_v5_automatic_preflight_and_source_specific_repairs_complete; pending_primary_text_and_geometry_authentication_retained','output':{'path':str(path),'sha256':sf(path)},'counts':dict(counts),'v5_boundary_and_container_correction_operations_N':len(changes),'v5_boundary_correction_N':sum(c['operation'].startswith('correct_reference_boundary') for c in changes),'pending_issue_N':len(pending),'pending_issue_types':dict(Counter(p['issue_type'] for p in pending)),'pending_unique_source_text_N':len({(p['source_sha256'],p['text_sha256']) for p in pending}),'v2_v3_v4_v5_bodies_byte_identical':True});dump(OUT/'source-QA-summary-v5.json',qa)
print(json.dumps({'source_sha256':sf(path),'boundary_and_container_repairs_N':len(changes),'pending_N':len(pending),'pending_unique_text_N':qa['pending_unique_source_text_N']},ensure_ascii=False,indent=2))
