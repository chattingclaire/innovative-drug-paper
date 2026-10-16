"""Apply root-approved source-only explicit-reference repairs, preserving v11.

No classifier, prompt, standard, labels or predictions are changed or read.
Equal available reference material does not imply the frozen rule code consumes
this new field. Actual coding must be rerun on changed payloads by the runner.
"""
from pathlib import Path
import copy,hashlib,json
B=Path(__file__).resolve().parent
P=B/'audit/explicit_qualification_source_proposal_v12.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def jl(p):return [json.loads(s)for s in Path(p).read_text().splitlines()if s.strip()]
for fn in['effective_blind_inputs_v12.jsonl','rule_inputs_shared_v12.jsonl','material_v12_manifest.json']:assert not(B/fn).exists(),'Never overwrite v12'
oldhash={fn:sha(B/fn)for fn in['effective_blind_inputs_v11.jsonl','rule_inputs_shared_v11.jsonl','material_v11_manifest.json']}
ll=jl(B/'effective_blind_inputs_v11.jsonl');rr=jl(B/'rule_inputs_shared_v11.jsonl');original_ll=copy.deepcopy(ll);original_rr=copy.deepcopy(rr);lb={x['id']:x for x in ll};rb={x['id']:x['input']for x in rr};p=json.loads(P.read_text());assert p['affected_unit_n']==48 and len(p['proposals'])==48
refs=0
for x in p['proposals']:
 rid=x['id'];r=rb[rid];assert x['current_unit']==lb[rid]['text']==r['unit_text'];assert digest(r['unit_text'])==x['current_unit_sha256'];assert all(c['verification']['verified']for ref in x['references']for c in ref['contexts'])
 for ref in x['references']:
  for c in ref['contexts']:
   assert sha(c['source_path'])==c['source_sha256'];assert sha(c['candidate_path'])==c['candidate_sha256'];cp=json.loads(Path(c['candidate_path']).read_text());cand=next(z for z in cp['paragraphs']if z['id']==c['paragraph_id']);assert cand['text']==c['text']and cand.get('pages',[])==c['pages'];assert Path(cand.get('source_file')or cp['source']).resolve()==Path(c['source_path']).resolve()
 cert={'repair_version':'v12-source-explicit-qualification-reference','current_unit_sha256':digest(r['unit_text']),'current_unit_id':r['unit_id'],'current_unit_source_path':r.get('unit_source')or r['source'],'current_unit_source_sha256':r.get('unit_source_sha256')or r['source_sha256'],'current_unit_candidate_path':r['candidate_file'],'current_unit_candidate_sha256':r['candidate_sha256'],'references':copy.deepcopy(x['references']),'references_sha256':digest(json.dumps(x['references'],ensure_ascii=False,sort_keys=True)),'usage':'只提供当前原句明确援引的实际源条件，消解资格、对象与范围。不新增当前分析单元，不自动复制所引段落的任何维度标签。'}
 lb[rid]['contexts']['explicitly_cited_qualifications_v12']=copy.deepcopy(cert);r['explicitly_cited_qualifications_v12']=copy.deepcopy(cert);r['llm_v29_shared_context']=copy.deepcopy(lb[rid]['contexts']);refs+=len(x['references'])
assert refs==62
assert len(ll)==len(rr)==4924
assert all(a['id']==b['id']and a['text']==b['text']for a,b in zip(ll,original_ll))
assert all(a['id']==b['id']and a['input']['unit_id']==b['input']['unit_id']and a['input']['unit_text']==b['input']['unit_text']for a,b in zip(rr,original_rr))
assert all(a['contexts']==b['input']['llm_v29_shared_context']for a,b in zip(ll,rr))
freeze=json.loads((B/'rules-v33/candidate_freeze.json').read_text());assert all(sha(k)==v for k,v in freeze['production_code_sha256'].items());assert all(sha(k)==v for k,v in freeze['all_runtime_py_sha256'].items())
for name,rows in [('effective_blind_inputs_v12.jsonl',ll),('rule_inputs_shared_v12.jsonl',rr)]:
 (B/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows))
changed=[a['id']for a,b in zip(ll,original_ll)if a!=b];assert changed==sorted(p['affected_ids'])
manifest={'material_version':'v12','status':'prepared_root_approved_source_repair_pending_final_seal','source_only':True,'reason':'Root-approved full structural-family supply of explicitly incorporated qualification/condition/section text, after actual execution reported missing named source conditions.','n':4924,'unit_text_changes':0,'unit_id_changes':0,'new_analysis_units':0,'incremental_context_changed_n':48,'explicit_reference_interval_n':62,'affected_ids':changed,'two_methods_same_text_and_context':True,'classification_code_unchanged':True,'manual_unchanged':True,'coding_standard_unchanged':'CAL-5D-v1.3 + operational-v1.4','new_field':'explicitly_cited_qualifications_v12','new_field_is_available_to_both_methods':True,'frozen_rule_consumption_of_new_field_not_claimed':True,'references_or_predictions_read_by_preparation_script':False,'prior_v11_files_preserved_sha256':oldhash,'proposal_path':str(P),'proposal_sha256':sha(P),'new_llm_sha256':sha(B/'effective_blind_inputs_v12.jsonl'),'new_rule_sha256':sha(B/'rule_inputs_shared_v12.jsonl'),'01043_boundary_note':'p0006..p0015 is the complete cited 2020 outside-directory subsection: heading,p0007 qualification head,p0008..p0014 seven enumerated criteria,p0015 direct application-scope and exclusive-drug cutoff clarification. The next p0016 is the inside-directory sibling and is excluded.','no_labels_transferred':True,'first_v11_actual_outputs_preserved':True,'actual_model_rerun_required_on_changed_context_payloads':True}
(B/'material_v12_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
assert all(sha(B/fn)==h for fn,h in oldhash.items())
print(json.dumps({k:manifest[k]for k in['n','incremental_context_changed_n','explicit_reference_interval_n','new_llm_sha256','new_rule_sha256']},ensure_ascii=False))
