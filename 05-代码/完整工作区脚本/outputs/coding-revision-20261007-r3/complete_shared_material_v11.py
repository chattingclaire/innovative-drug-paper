"""Apply locked, source-only following-list repairs to identical shared materials.

This release reads no labels/predictions. It uses an explicitly reviewed proposal,
never a heading-rank heuristic. All v10/earlier files are left untouched.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,unicodedata
HERE=Path(__file__).resolve().parent
PROPOSAL=HERE/'audit/necessary_list_completion_proposal_v11.json'
CLEANUP=HERE/'audit/independent_following_boundary_proposal_v10.json'
def jl(p):return [json.loads(x)for x in Path(p).read_text().splitlines()if x.strip()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s)if c.isalnum())
ll=jl(HERE/'effective_blind_inputs_v10.jsonl');rr=jl(HERE/'rule_inputs_shared_v10.jsonl')
old=copy.deepcopy(ll);oldr=copy.deepcopy(rr)
lb={r['id']:r for r in ll};rb={r['id']:r['input']for r in rr}
p=json.loads(PROPOSAL.read_text());cleanup=json.loads(CLEANUP.read_text())
assert p['n']==121 and not p['failed_source_checks']
assert cleanup['n_definite_boundary_overshoot_units']==32 and cleanup['all_source_checks_pass']
# Remove only the exact reviewed old items; all original units remain fixed.
for x in cleanup['proposals']:
 c=lb[x['id']]['contexts'];assert c[x['field']]==x['keep_exact_context_items']+x['remove_exact_context_items'],x['id']
 c[x['field']]=copy.deepcopy(x['keep_exact_context_items'])
keep_v10=set(json.loads((HERE/'material_v10_manifest.json').read_text())['affected_ids'])
v10_lists={x['id']for x in json.loads((HERE/'material_v10_manifest.json').read_text())['list_source_repairs']}
repairs=[];new_v27=[];not_v27=[];reuse=[]
spec=importlib.util.spec_from_file_location('frozen_cv_v11',HERE/'rules-v33/runtime/context_validation.py');cv=importlib.util.module_from_spec(spec);spec.loader.exec_module(cv)
for x in p['proposals']:
 rid=x['id'];r=rb[rid];c=lb[rid]['contexts'];cp=Path(x['candidate_path']);sp=Path(x['source_path'])
 assert sha(cp)==x['candidate_sha256']==r['candidate_sha256']
 assert sha(sp)==x['source_sha256']==(r.get('unit_source_sha256')or r['source_sha256'])
 ps=json.loads(cp.read_text())['paragraphs'];ix={z['id']:i for i,z in enumerate(ps)};i=ix[x['first_paragraph_id']];j=ix[x['last_paragraph_id']]
 contexts=[]
 for z,y in zip(ps[i:j+1],x['complete_contiguous_interval']):
  assert z['id']==y['paragraph_id']and z['text']==y['text']and z.get('pages',[])==y['pages']
  assert y['verification']['verified']and all(v for v in y['source_checks'].values()if v is not None)
  contexts.append({k:copy.deepcopy(v)for k,v in y.items()if k!='source_checks'})
 assert len(contexts)==j-i+1 and norm(r['unit_text'])in norm(contexts[0]['text'])
 b=x['next_boundary'];assert b is None or(ps[j+1]['id']==b['paragraph_id']and ps[j+1]['text']==b['text'])
 boundary={'first_paragraph':contexts[0]['paragraph_id'],'last_paragraph':contexts[-1]['paragraph_id'],'all_paragraphs_in_interval_included':True,'next_paragraph_id':b['paragraph_id']if b else None,'next_paragraph_text':b['text']if b else None,'review':x['boundary_review']}
 # The 19 v10 complete lists and their already accepted certificates are reused verbatim.
 if rid in v10_lists:
  assert [(z['paragraph_id'],z['text'])for z in c['structured_following_units']]==[(z['paragraph_id'],z['text'])for z in contexts[1:]]
  assert cv.verified_following_list(r);reuse.append(rid);continue
 cert={'original_unit_sha256':digest(r['unit_text']),'source_sha256':x['source_sha256'],'contexts':contexts,'contexts_sha256':digest(json.dumps(contexts,ensure_ascii=False,sort_keys=True)),'repair_status':'supplemented','unresolved_material_gaps':[],'source_files_hash_verified':True,'structure_boundary':boundary,'usage':'本字段提供当前命题明确引出的完整列举及其直接说明，仅用于消解当前命题的条件和回指；不增加分析单元，不把后项维度复制到当前命题。'}
 before=copy.deepcopy(c.get('structured_following_units',[]));c['structured_following_units']=copy.deepcopy(contexts[1:]);c['complete_following_list_v11']=copy.deepcopy(cert)
 c['following_context_status_v11']={'field':'structured_following_units','role':'complete_actual_enumeration','complete':True,'head':r['unit_text'],'first_paragraph_id':contexts[0]['paragraph_id'],'last_paragraph_id':contexts[-1]['paragraph_id'],'next_boundary':copy.deepcopy(b),'usage':cert['usage']}
 r['complete_following_list_v11']=copy.deepcopy(cert)
 # Reuse the frozen v27 certificate schema wherever its existing structural
 # validator accepts the literal list. Bullet/letter/一是 lists are explicitly
 # complete material, without falsely claiming v27 marker compatibility.
 if not r.get('verified_following_list_v27'):
  probe=dict(r,verified_following_list_v27=cert)
  if cv.verified_following_list(probe):
   r['verified_following_list_v27']=copy.deepcopy(cert);c.setdefault('verified_context_certificates',{})['verified_following_list_v27']=copy.deepcopy(cert);new_v27.append(rid)
  else:not_v27.append(rid)
 repairs.append({'id':rid,'old_following_item_n':len(before),'new_following_paragraph_n':len(contexts)-1,'exact_full_following':copy.deepcopy(contexts[1:]),'boundary':boundary,'source_path':x['source_path'],'source_sha256':x['source_sha256'],'candidate_path':x['candidate_path'],'candidate_sha256':x['candidate_sha256']})
preview='00321 00596 00916 00937 00996 01016 01046 01088 01194 01233 01250 01797 01944 01963 02147 02163 02250 02299 02592 02614 02832 02908 03164 03655 04271 04287 03701'.split()
for short in preview:
 rid='RECODE25-'+short;c=lb[rid]['contexts'];c['following_context_status_v11']={'field':'structured_following_units','role':'local_navigation_preview','complete':False,'usage':'这是广义通知、工作程序、阶段或图表的局部导航预览，并非当前引导句的完整后项列表或全文。只用于定位和消解明确回指；不得把它当作完整列举，也不得因预览局部而将整条猜为0。当前命题仍按原句及已核实的实际适用范围独立判定。'}
rid='RECODE25-00054';lb[rid]['contexts']['following_context_status_v11']={'field':'structured_following_units','role':'self_contained_form_field_no_actual_following_enumeration','complete':False,'usage':'当前原句是异议表中的独立填写要求；下一来源组件为另一张表。已移除其后另一表的预览，不能把该组件误认为当前原句的列举。'}
for r in ll:rb[r['id']]['llm_v29_shared_context']=copy.deepcopy(r['contexts'])
assert len(ll)==len(rr)==4924
assert all(a['id']==b['id']and a['text']==b['text']for a,b in zip(ll,old))
assert all(a['id']==b['id']and a['input']['unit_id']==b['input']['unit_id']and a['input']['unit_text']==b['input']['unit_text']for a,b in zip(rr,oldr))
assert all(a['contexts']==b['input']['llm_v29_shared_context']for a,b in zip(ll,rr))
assert all(lb[rid]['contexts']==next(x['contexts']for x in old if x['id']==rid)for rid in v10_lists)
freeze=json.loads((HERE/'rules-v33/candidate_freeze.json').read_text())
assert all(sha(k)==v for k,v in freeze['production_code_sha256'].items())
assert all(sha(k)==v for k,v in freeze['all_runtime_py_sha256'].items())
for name,rows in [('effective_blind_inputs_v11.jsonl',ll),('rule_inputs_shared_v11.jsonl',rr)]:
 (HERE/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows))
changed=[a['id']for a,b in zip(ll,old)if a!=b]
manifest={'material_version':'v11','reason':'Source-only removal of definite next-section overshoots and completion of every real necessary enumeration among existing following fields; broad document/program navigation marked incomplete. No label-based boundary selection.','n':4924,'unit_text_changes':0,'unit_id_changes':0,'two_methods_same_text_and_context':True,'source_only':True,'coding_standard_unchanged':'CAL-5D-v1.3 + operational-v1.4','classification_code_unchanged':True,'references_or_predictions_read_by_release_script':False,'incremental_context_changed_n':len(changed),'affected_ids':changed,'definite_overshoot_cleanup_unit_n':32,'definite_overshoot_removed_context_item_n':50,'overshoot_cleanup_ids':[x['id']for x in cleanup['proposals']],'necessary_complete_list_n':121,'necessary_complete_list_paragraph_n':sum(len(x['complete_contiguous_interval'])for x in p['proposals']),'v10_complete_19_reused_verbatim':reuse,'new_or_updated_complete_list_n':len(repairs),'new_or_updated_complete_lists':repairs,'new_v27_validator_accepted_ids':new_v27,'complete_material_non_v27_marker_ids':not_v27,'local_navigation_preview_ids':['RECODE25-'+s for s in preview],'self_contained_form_field_ids':['RECODE25-00054'],'v5_v6_versioned_fields_reused_unchanged':True,'source_proposal_path':str(PROPOSAL),'source_proposal_sha256':sha(PROPOSAL),'overshoot_proposal_path':str(CLEANUP),'overshoot_proposal_sha256':sha(CLEANUP),'previous_llm_sha256':sha(HERE/'effective_blind_inputs_v10.jsonl'),'previous_rule_sha256':sha(HERE/'rule_inputs_shared_v10.jsonl'),'new_llm_sha256':sha(HERE/'effective_blind_inputs_v11.jsonl'),'new_rule_sha256':sha(HERE/'rule_inputs_shared_v11.jsonl'),'frozen_before_full_v32_model_execution':True,'new_blind_first_outputs_preserved':True,'explicit_cited_articles_v10_reused_unchanged':True}
(HERE/'material_v11_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:manifest[k]for k in ['n','incremental_context_changed_n','new_or_updated_complete_list_n','necessary_complete_list_n','new_llm_sha256','new_rule_sha256']},ensure_ascii=False))
