"""Bind verified government table titles/headers symmetrically, without label access."""
from pathlib import Path
import json,hashlib,copy
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'recall-revision-20261007'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
source=Path('/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区/原文补全/NMPA-数据保护2026-完整结构化正文.json')
doc=json.loads(source.read_text());rr=jl(OLD/'rule_inputs_v31_shared_v3.jsonl');ll=jl(OLD/'effective_blind_inputs_v30_v3.jsonl');byid={x['id']:x for x in ll}
matches=[];certificates={}
for r in rr:
 x=r['input']
 if x['original_file_stem']!='NMPA-药品试验数据保护实施办法-2026' or x.get('unit_type')!='normative_table_row':continue
 cells=[s.strip() for s in x['unit_text'].split('|')]
 hit=[]
 for ti,t in enumerate(doc['tables']):
  for ri,row in enumerate(t['rows']):
   if cells[:4]==[str(v).strip() for v in row]:hit.append((ti,ri,t))
 assert len(hit)==1,(r['id'],cells,[(a,b) for a,b,_ in hit])
 ti,ri,t=hit[0];image=Path(t['source_image']);assert sha(image)==t['source_sha256']
 cert={'kind':'verified_table_title_columns_v4','table_title':t['title'],'column_names':t['columns'],'text':t['title']+'；列名：'+' | '.join(t['columns']),'source_image':str(image),'source_image_sha256':sha(image),'source_url':t['source_url'],'source_document_url':doc['source_url'],'source_structured_sha256':sha(source),'row_index_zero_based':ri,'raw_row_cells':t['rows'][ri],'visual_review':'root viewed the actual three source images in this turn; headers and row alignment confirmed','use':'Resolve table column meaning only; no labels or intended department distribution.'}
 # Independent mapping to exact visible source row prevents header propagation across tables.
 context=byid[r['id']]['contexts']
 context.setdefault('verified_table_context_v4',[]).append(cert)
 x['llm_v29_shared_context']=copy.deepcopy(context)
 x['verified_table_context_v4']=[cert]
 matches.append(r['id']);certificates[r['id']]=cert
assert len(matches)==18,len(matches)
for name,rows in [('effective_blind_inputs_v4.jsonl',ll),('rule_inputs_shared_v4.jsonl',rr)]:
 (HERE/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
oldll={x['id']:x for x in jl(OLD/'effective_blind_inputs_v30_v3.jsonl')}
assert all(byid[rid]['text']==oldll[rid]['text'] for rid in byid)
assert all(byid[rid]==oldll[rid] for rid in byid if rid not in matches)
mapping=json.loads((HERE/'admin/PRIVATE_mapping.json').read_text())
for coder in ['A','C']:
 selected=[]
 for m in mapping:
  if m['coder']==coder and m['original_id'] in matches:selected.append({**byid[m['original_id']],'id':m['blind_id']})
 dump(HERE/'confirmation'/f'agent-{coder}'/'补充材料-v4.json',{'purpose':'Source-only table header completion, same underlying units for both coders. Preserve initial results, independently reread these entries using complete source context. No other coder or machine labels supplied.','rows':selected})
future=HERE/'admin/future_human_sampling_PRIVATE.json'
future_ids={m['original_id'] for m in json.loads(future.read_text())['mapping']}&set(matches)
dump(HERE/'material_v4_manifest.json',{'change':'Restore titles and four actual columns of three normative drug data-protection tables','source_sha256':sha(source),'verified_images':{t['source_image']:sha(Path(t['source_image'])) for t in doc['tables']},'affected_ids':matches,'affected_n':len(matches),'unit_text_changes':0,'unaffected_units_identical':4906,'new_llm_input_sha256':sha(HERE/'effective_blind_inputs_v4.jsonl'),'new_rule_input_sha256':sha(HERE/'rule_inputs_shared_v4.jsonl'),'certificates':certificates,'future_human_affected_ids':sorted(future_ids),'no_label_access_in_script':True})
# Whole production batches are selected by input changes only, never by prediction values.
indices=sorted({int(rid.split('-')[-1])//25+1 if int(rid.split('-')[-1])%25 else int(rid.split('-')[-1])//25 for rid in matches})
affected=[]
for i in indices:affected+=ll[(i-1)*25:i*25]
(HERE/'llm-v31/affected_complete_batches_v4.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in affected))
dump(HERE/'llm-v31/material_v4_batch_plan.json',{'original_batch_indices':indices,'whole_batch_n':len(affected),'changed_unit_n':18,'selection':'Unconditionally replace these complete batches after actual same-prompt re-execution. Retain every other production batch only after exact input equality with v4. No metric or label selection.','inputs_sha256':sha(HERE/'llm-v31/affected_complete_batches_v4.jsonl')})
print(json.dumps({'changed':len(matches),'selected_agent_rows':{c:len(json.loads((HERE/'confirmation'/f'agent-{c}'/'补充材料-v4.json').read_text())['rows']) for c in ['A','C']},'production_batches':indices,'rerun_n':len(affected),'future_human_affected_n':len(future_ids)},ensure_ascii=False))
