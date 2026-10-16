from pathlib import Path
import json,hashlib,copy
HERE=Path(__file__).resolve().parent
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
ll=jl(HERE/'effective_blind_inputs_v5.jsonl');rr=jl(HERE/'rule_inputs_shared_v5.jsonl');lb={r['id']:r for r in ll};rb={r['id']:r for r in rr};rid='RECODE25-03312'
source=Path(rb[rid]['input']['source']);assert sha(source)==rb[rid]['input']['source_sha256']
children=[{'id':f'RECODE25-{i:05d}','text':lb[f'RECODE25-{i:05d}']['text'],'pages':rb[f'RECODE25-{i:05d}']['input']['pages'],'source_path':str(source),'source_sha256':sha(source),'verification':'Exact existing units; independently reread source PDF pages 1-2 for complete five simultaneous conditions and nested branches.'} for i in range(3313,3322)]
lb[rid]['contexts']['structured_following_units_v6']=children
lb[rid]['contexts']['following_list_use_v6']='Read five actual simultaneous conditions and nested branches for completeness; do not transfer every child dimension to the head.'
rb[rid]['input']['llm_v29_shared_context']=copy.deepcopy(lb[rid]['contexts']);rb[rid]['input']['structured_following_units_v6']=copy.deepcopy(children)
for name,rows in [('effective_blind_inputs_v6.jsonl',ll),('rule_inputs_shared_v6.jsonl',rr)]:
 (HERE/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
mapping=json.loads((HERE/'admin/PRIVATE_mapping.json').read_text())
for coder in ['A','C']:
 rows=[{**lb[m['original_id']],'id':m['blind_id']} for m in mapping if m['coder']==coder and m['original_id']==rid]
 dump(HERE/'confirmation'/f'agent-{coder}'/'补充材料-v6.json',{'purpose':'Complete five exact simultaneous conditions, with nested branches, of an existing renewal clause. Source-only, no labels; preserve first submission and independently reread.','rows':rows})
batch=133;affected=ll[(batch-1)*25:batch*25]
(HERE/'llm-v31/affected_complete_batch_v6.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in affected))
base=jl(HERE.parent/'recall-revision-20261007/effective_blind_inputs_v30_v3.jsonl')
changed=[a['id'] for a,b in zip(ll,base) if a!=b]
assert len(changed)==23 and all(a['text']==b['text'] for a,b in zip(ll,base))
dump(HERE/'material_v6_manifest.json',{'source_pdf':str(source),'source_sha256':sha(source),'source_pages':[1,2],'affected_ids_incremental':[rid],'total_affected_ids_from_v3':changed,'total_changed_from_v3':23,'unit_text_changes':0,'unaffected_v3_n':4901,'new_llm_input_sha256':sha(HERE/'effective_blind_inputs_v6.jsonl'),'new_rule_input_sha256':sha(HERE/'rule_inputs_shared_v6.jsonl'),'final_changed_original_batches':[57,58,68,133],'source_v5_manifest_sha256':sha(HERE/'material_v5_manifest.json'),'selection_not_based_on_labels':True})
print(json.dumps({'incremental_changed':1,'total_changed':23,'source_children_n':len(children),'new_original_batch':133},ensure_ascii=False))
