"""Independent conservative primary-source audit; preserve all earlier versions."""
from pathlib import Path
import copy,hashlib,json,importlib.util
from collections import Counter,defaultdict
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sp=importlib.util.spec_from_file_location('preflight',OUT/'build_full_frame_preflight_v2.py');pr=importlib.util.module_from_spec(sp);sp.loader.exec_module(pr)
sha=pr.sha;sf=pr.shafile;dump=pr.dump;jl=pr.jsonl;rows=pr.readrows
F={r['id']:r for r in rows(ROOT/'00-baseline/source-only-frame.jsonl')};mf=json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text());BS={r['sha256']:r for r in mf['files']};BP={r['original']:r for r in mf['files']};M={r['id']:r for r in rows(ROOT/'00-baseline/source-files/f4da9adad83e91ba-source_only_with_scope04.jsonl') if r['id'] in F}
oldpath=OUT/'canonical_source_context-v3.jsonl';oldsha=sf(oldpath);data=rows(oldpath);D={r['id']:r for r in data};q=rows(OUT/'context-source-QA-v3.jsonl');QD={(r['record_id'],r['context_id']):r for r in q};pending=rows(OUT/'source-exceptions-v3.jsonl');changes2=json.loads((OUT/'source-changes-v2.json').read_text())['changes'];rollback=[];objects={}
# A candidate file's root source is only a bundle fallback; it is not a per-leaf
# primary identity. Its alternate TXT literal must not displace original PDF.
for change in changes2:
 if change['operation']!='repair_declared_or_unique_literal_paragraph_primary_source_identity':continue
 rid,cid=change['record_id'],change['context_id'];node=next(n for n in D[rid]['contexts'] if n['context_id']==cid);loc=change['candidate_locator'];cs=loc['candidate_sha256']
 if cs not in objects:objects[cs]=json.loads(Path(BS[cs]['snapshot']).read_text())
 original_para=next((p for p in objects[cs].get('paragraphs',[]) if p.get('id',p.get('paragraph_id'))==loc['paragraph_id']),{})
 old=next(n for n in M[rid]['contexts'] if n['context_id']==cid)
 explicit='source_file' in original_para
 declared=old['structure'].get('paragraph_id',old['structure'].get('candidate_paragraph_id'))
 uniquely_declared=declared==loc['paragraph_id'] and explicit
 verified_attachment_parent_source=Path(BS[change['before_source_sha256']]['snapshot']).suffix=='.doc' and node['kind'] in {'heading','preceding_paragraph'} and change['after_source_sha256']==F[rid]['source_position']['source_sha256_recorded']
 if uniquely_declared or verified_attachment_parent_source:continue
 before=change['before_source_sha256'];alternative=change['after_source_sha256'];node['source_document']=old.get('source_document','D-'+before[:16]);node['source_ref']['sha256']=before;node['source_ref']['source_resource_id']='SOURCE-'+before
 item={'record_id':rid,'context_id':cid,'operation':'retain_original_primary_binding_and_reject_candidate_bundle_fallback_as_correction','original_primary_source_sha256':before,'alternate_literal_source_sha256':alternative,'candidate_locator':loc,'reason':'No unique explicit original per-paragraph source_file identity for this selected source node; alternate literal text is a locator candidate, not proof of erroneous original PDF binding.','source_text_unchanged':True};rollback.append(item)
 # Keep alternate identity exclusively in source-QA administration, not as a
 # semantic relevance certificate inside the public source packet.
 qa=QD[(rid,cid)];qa['primary_source_sha256']=before;qa['rejected_primary_rebinding']=item
 for ft in qa['policy_text_fields']:
  ft['literal_status']='original_primary_literal_location_pending_alternate_bundle_not_primary_proof'
  pending.append({'record_id':rid,'context_id':cid,'field':ft['field'],'issue_type':'primary_locator_pending_alternate_bundle_fallback_rejected','source_sha256':before,'text_sha256':ft['projected_text_sha256'],'kind':node['kind'],'alternate_literal_source_sha256':alternative,'candidate_locators':[loc]})
# Correct audit metadata to actual original exported IDs (not mutable objects).
for qa in q:
 old=next(n for n in M[qa['record_id']]['contexts'] if n['context_id']==qa['context_id']);qa['original_source_document']=old.get('source_document')
# All added source-geometry nodes get audit entries as well as the public node.
for r in data:
 for n in r['contexts']:
  if (r['id'],n['context_id']) in QD:continue
  qa={'record_id':r['id'],'context_id':n['context_id'],'kind':n['kind'],'original_source_document':None,'primary_source_sha256':n['source_ref']['sha256'],'source_identity_methods':['new_original_binary_table_geometry_resource'],'candidate_locators':[],'textless_structure':not bool(list(pr.pr.text_values(n))),'policy_text_fields':[{'field':f,'original_text_sha256':None,'projected_text_sha256':sha(t.encode()),'literal_status':'source_table_cells_and_geometry_checked_against_original_binary_or_original_image'} for f,t in pr.pr.text_values(n)]};q.append(qa);QD[(r['id'],n['context_id'])]=qa
assert len(q)==sum(len(r['contexts']) for r in data)
assert not list(pr.forbidden(data))
for r in data:
 cids={n['context_id'] for n in r['contexts']};rids={n['relation_id'] for n in r.get('source_relations',[])}
 assert {n['context_id'] for n in M[r['id']]['contexts']}<=cids
 for n in r['contexts']:
  assert all(cid in cids for _,cid in pr.pr.context_references(n))
  for k in ['image_evidence_ref','relation_id']:
   s=n['structure'].get(k)
   if isinstance(s,str) and s.startswith('NR-'):assert s in rids
 for a in r.get('source_attachments',[]):assert sf(OUT/a['relative_path'])==a['sha256']
 assert sha(F[r['id']]['unit_text'].encode())==F[r['id']]['unit_text_sha256']
for r in F.values():
 for pk,sk in [('source_file','source_sha256_recorded'),('unit_source_file','unit_source_sha256_recorded'),('candidate_file','candidate_sha256_recorded')]:assert BP[r['source_position'][pk]]['sha256']==r['source_position'][sk]
path=OUT/'canonical_source_context-v4.jsonl';jl(path,data);jl(OUT/'context-source-QA-v4.jsonl',q);bodyqa=rows(OUT/'body-source-QA-v3.jsonl');jl(OUT/'body-source-QA-v4.jsonl',bodyqa)
pending=list({(p['record_id'],p['context_id'],p['field'],p['source_sha256'],p['text_sha256'],p['issue_type']):p for p in pending}.values());jl(OUT/'source-exceptions-v4.jsonl',pending)
dump(OUT/'primary-binding-conservative-review-v4.json',{'rejected_unsupported_primary_correction_N':len(rollback),'rollback_policy':'Candidate root-source fallback and full-text-only cross-file duplicate match are not sufficient proof of an original node primary identity error.','changes':rollback,'all_body_texts_unchanged_from_v3':True})
rm=rows(OUT/'material-record-bindings-v3.jsonl')
for b in rm:
 r=D[b['id']];b['projected_context_sha256']=sha(pr.canonical(r['contexts']).encode());b['projected_record_sha256']=sha(pr.canonical(r).encode());assert b['projected_body_sha256']==sha(r['text'].encode());assert b['original_frame_body_sha256']==F[b['id']]['unit_text_sha256']
jl(OUT/'material-record-bindings-v4.jsonl',rm);fa=json.loads((OUT/'family-exposure-impact-v3.json').read_text());fa['source_projection_v4_sha256']=sf(path);fa['v2_v3_v4_bodies_byte_identical']=True;dump(OUT/'family-exposure-impact-v4.json',fa)
# Classify candidate identity discrepancies instead of labelling them all errors.
disc=[]
for qa in q:
 for loc in qa['candidate_locators']:
  if not loc['candidate_text_correspondence'] or not loc['primary_source_sha256'] or loc['primary_source_sha256']==qa['primary_source_sha256']:continue
  cs=loc['candidate_sha256']
  if cs not in objects:objects[cs]=json.loads(Path(BS[cs]['snapshot']).read_text())
  pp=next((p for p in objects[cs].get('paragraphs',[]) if p.get('id',p.get('paragraph_id'))==loc['paragraph_id']),{})
  basis='explicit_per_paragraph_source_file' if pp.get('source_file') else 'candidate_bundle_root_source_fallback_not_per_leaf_identity'
  disc.append({'record_id':qa['record_id'],'context_id':qa['context_id'],'projected_primary_source_sha256':qa['primary_source_sha256'],'candidate_locator':loc,'candidate_identity_basis':basis,'source_identity_error_established':False,'requires_source_version_or_aggregation_review':True})
jl(OUT/'source-identity-disagreements-v4.jsonl',disc)
# Identity registry includes original source SHA restored by conservative review.
oldids=rows(OUT/'source-document-identities-v3.jsonl');ids={x['source_sha256']:x for x in oldids};used={r['source_ref']['sha256'] for r in data}|{n['source_ref']['sha256'] for r in data for n in r['contexts']};assert used<=set(ids)
jl(OUT/'source-document-identities-v4.jsonl',[ids[s] for s in sorted(used)])
refs=[]
for r in data:
 by={n['context_id']:n for n in r['contexts']}
 for n in r['contexts']:
  if n['kind']!='cited_reference':continue
  members=[by[c] for g in n['structure'].get('child_groups',[]) if g['position']=='contexts' for c in g['ordered_context_ids']];sources=sorted({x['source_ref']['sha256'] for x in members});cur=r['source_ref']['sha256'];cy=ids[cur]['document_year_literals_in_recorded_original_path'];ys=[ids[s]['document_year_literals_in_recorded_original_path'] for s in sources]
  refs.append({'record_id':r['id'],'reference_context_id':n['context_id'],'reference_address_locator':n['structure'].get('reference_address'),'current_primary_source_sha256':cur,'cited_primary_source_sha256s':sources,'current_document_year_literals':cy,'cited_document_year_literals':ys,'cited_original_context_ids':[x['context_id'] for x in members],'cited_source_refs':[x['source_ref'] for x in members],'single_calendar_year_identity_matches':len(cy)==1 and all(y==cy for y in ys) if ys else None,'same_edition_not_established_by_year_match_alone':True,'locator_not_dimension_or_semantic_support_certificate':True})
jl(OUT/'explicit-source-reference-index-v4.jsonl',refs)
qa=json.loads((OUT/'source-QA-summary-v3.json').read_text());counts=Counter()
for x in bodyqa:counts['body_literal_'+x['literal_status']]+=1
for x in q:
 counts['contexts']+=1;counts['textless_contexts']+=x['textless_structure'];counts['source_identity_resolved_contexts']+=bool(x['primary_source_sha256'])
 for ft in x['policy_text_fields']:counts['context_literal_'+ft['literal_status']]+=1
containers=[x for x in changes2 if x['operation']=='repair_boundary_container_from_explicit_child_source'];primary_changes=[x for x in changes2 if x['operation']=='repair_declared_or_unique_literal_paragraph_primary_source_identity'];retainedN=len(primary_changes)-len(rollback)
qa.update({'status':'full_frame_source_only_v4_preflight_complete_with_unresolved_source_content_and_locator_items; not_final_material_freeze','output':{'path':str(path),'sha256':sf(path)},'counts':dict(counts),'source_identity_N':len(used),'actual_output_context_N':len(q),'all_original_CTX_retained_and_all_new_source_nodes_audited':True,'source_identity_corrections':{'explicit_or_verified_attachment_primary_corrections_retained_N':retainedN,'unsupported_candidate_fallback_corrections_rejected_N':len(rollback),'already_exported_wrong_boundary_container_identity_corrected_N':sum(x['before_source_sha256'] is not None for x in containers),'previously_UNBOUND_textless_container_identity_completed_N':sum(x['before_source_sha256'] is None for x in containers)},'pending_issue_N':len(pending),'pending_issue_types':dict(Counter(p['issue_type'] for p in pending)),'pending_unique_source_text_N':len({(p['source_sha256'],p['text_sha256']) for p in pending}),'candidate_identity_discrepancy_occurrences_N':len(disc),'candidate_identity_discrepancy_basis':dict(Counter(d['candidate_identity_basis'] for d in disc)),'explicit_frame_complete_source_pair_checks_N':13443,'explicit_frame_complete_source_pair_check_failures_N':0,'v2_v3_v4_bodies_byte_identical':True,'unit_texts_byte_unchanged_from_baseline_N':4480,'unit_texts_changed_from_baseline_N':1,'unit_text_change_reason':'Source FAQ2026 diagram3 rare-disease branch numeral condition2->condition7, actual source physical page11; full original graph reviewed and old body SHA retained.','preserved_v3_sha256':oldsha,'all_CTX_and_NR_recursive_references_resolve':True,'all_source_attachment_byte_SHA_checks_pass':True,'full_original_source_content_transcription_authenticated':False,'machine_human_source_content_equivalence_complete':False,'final_material_freeze_completed':False,'outputs':[{'path':str(p),'sha256':sf(p)} for p in sorted(OUT.glob('*-v4.json*'))]});dump(OUT/'source-QA-summary-v4.json',qa)
assert sf(oldpath)==oldsha
print(json.dumps({'output_sha256':sf(path),'frame_N':4481,'contexts':len(q),'primary_repairs_retained':retainedN,'unsupported_primary_repairs_rejected':len(rollback),'pending_issue_N':len(pending),'pending_unique_source_text_N':qa['pending_unique_source_text_N'],'discrepancy_bases':qa['candidate_identity_discrepancy_basis']},ensure_ascii=False,indent=2))
