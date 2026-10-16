from pathlib import Path
import json,hashlib,copy
HERE=Path(__file__).resolve().parent
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
ll=jl(HERE/'effective_blind_inputs_v4.jsonl');rr=jl(HERE/'rule_inputs_shared_v4.jsonl');lb={r['id']:r for r in ll};rb={r['id']:r for r in rr}
ids=[f'RECODE25-{i:05d}' for i in range(1696,1700)]
source=Path(rb[ids[0]]['input']['source']);assert sha(source)==rb[ids[0]]['input']['source_sha256']
# Exact child units already exist in the frozen corpus; source PDF page 6 was reread.
children=[]
for rid in ids[1:]:
 r=rb[rid];assert r['input']['original_file_stem']=='NHSA-谈判药品续约规则-2023'
 children.append({'id':rid,'text':lb[rid]['text'],'pages':r['input']['pages'],'source_path':str(source),'source_sha256':sha(source),'verification':'Exact existing unit plus source PDF page 6 reread; follows the current simultaneously-required condition head.'})
assert children[0]['text'].find('独家药品')>=0
for rid in ids:
 c=lb[rid]['contexts'];c['structured_following_units_v5']=copy.deepcopy(children)
 c['following_condition_head_v5']={'text':lb[ids[0]]['text'],'source_path':str(source),'source_sha256':sha(source),'pages':[6],'usage':'Complete the simultaneous list conditions; do not copy every child dimension to the head or siblings.'}
 rb[rid]['input']['llm_v29_shared_context']=copy.deepcopy(c)
 rb[rid]['input']['structured_following_units_v5']=copy.deepcopy(children)
for name,rows in [('effective_blind_inputs_v5.jsonl',ll),('rule_inputs_shared_v5.jsonl',rr)]:
 (HERE/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
mapping=json.loads((HERE/'admin/PRIVATE_mapping.json').read_text())
for coder in ['A','C']:
 rows=[{**lb[m['original_id']],'id':m['blind_id']} for m in mapping if m['coder']==coder and m['original_id'] in ids]
 dump(HERE/'confirmation'/f'agent-{coder}'/'补充材料-v5.json',{'purpose':'Complete exact following conditions for existing simultaneously-required coverage-adjustment clause; source-only, no labels. Preserve first submission and separately reread supplied entries.','rows':rows})
batch=68;affected=ll[(batch-1)*25:batch*25]
(HERE/'llm-v31/affected_complete_batch_v5.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in affected))
dump(HERE/'material_v5_manifest.json',{'source_pdf':str(source),'source_sha256':sha(source),'source_pages':[6],'affected_ids_incremental':ids,'changed_n_incremental':4,'total_changed_from_v3':22,'unit_text_changes':0,'unaffected_v3_n':4902,'exact_following_units':children,'source_v4_manifest_sha256':sha(HERE/'material_v4_manifest.json'),'new_llm_input_sha256':sha(HERE/'effective_blind_inputs_v5.jsonl'),'new_rule_input_sha256':sha(HERE/'rule_inputs_shared_v5.jsonl'),'new_original_batch_index':68,'new_whole_batch_rerun_n':25,'material_v4_batches_57_58_remain_exactly_v5':all(x==y for x,y in zip(jl(HERE/'llm-v31/affected_complete_batches_v4.jsonl'),ll[1400:1450])),'selection_not_based_on_labels':True})
print(json.dumps({'v5_changed':4,'total_changed':22,'agent_supplement_n':len(rows),'following_children':[r['text'] for r in children]},ensure_ascii=False))
