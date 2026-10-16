"""Freeze unused, answer-free packets for future real human validation."""
from pathlib import Path
import json,random,hashlib,csv
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'recall-revision-20261007'
design=json.loads((HERE/'admin/sampling_design.json').read_text())
excluded=set(design['excluded_ids'])|{r['original_id'] for r in design['sample']}
rows={r['id']:r for r in (json.loads(x) for x in (OLD/'effective_blind_inputs_v30_v3.jsonl').read_text().splitlines())}
root=HERE.parents[1]
meta=json.loads((root/'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json').read_text())['rows']
cls={Path(x['original_file']).stem:x['analysis_group'] for x in meta}
raw=[json.loads(x) for x in (OLD/'rule_inputs_v31_shared_v3.jsonl').read_text().splitlines()]
group={r['id']:cls[r['input']['original_file_stem']] for r in raw}
rng=random.Random(2026100741);chosen=[];sample=[]
for g in ('NMPA','NHSA','NHC'):
 pool=sorted(x for x in rows if group[x]==g and x not in excluded)
 picked=rng.sample(pool,80);chosen+=picked
 sample.extend({'original_id':x,'group':g,'N':len(pool),'n':80,'probability':80/len(pool)} for x in picked)
assert len(set(chosen))==240 and not set(chosen)&excluded
mapping=[];out=HERE/'future-human-validation';out.mkdir(exist_ok=True)
for coder,seed in [('A',2026100743),('C',2026100747)]:
 order=list(chosen);random.Random(seed).shuffle(order)
 data=[]
 for i,rid in enumerate(order,1):
  bid=f'HV2-{coder}-{i:04d}';r=rows[rid]
  data.append({**r,'id':bid});mapping.append({'coder':coder,'blind_id':bid,'original_id':rid})
 (out/f'真人{coder}-无答案材料.json').write_text(json.dumps({'status':'blank_for_future_real_human_execution','coder_name':'','professional_background':'','execution_date':'','manual_version':'v1.3 + operational v1.4','rows':data},ensure_ascii=False,indent=2)+'\n')
 with (out/f'真人{coder}-空白编码表.csv').open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.writer(f);writer.writerow(['匿名编号','政策原文','来源标题','页码','完整语境JSON','S','E','Ec','I','F','S理由','E理由','Ec理由','I理由','F理由','逐字证据','I来源类型','F来源类型','问题说明'])
  for r in data:writer.writerow([r['id'],r['text'],r['source_title'],json.dumps(r['pages'],ensure_ascii=False),json.dumps(r['contexts'],ensure_ascii=False)]+['']*14)
admin={'seed':2026100741,'sample':sample,'mapping':mapping,'execution_status':'not_started_no_real_human_labels','never_use_agent_training_cases_as_formal_human_test':True,'sampling_scope':'Unused residual units after known development and current agent training/confirmation units; no inference to excluded units without additional design.'}
(HERE/'admin/future_human_sampling_PRIVATE.json').write_text(json.dumps(admin,ensure_ascii=False,indent=2)+'\n')
hashes={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
(out/'无答案核验.json').write_text(json.dumps({'n_per_coder':240,'no_agent_training_overlap':True,'all_labels_and_reasons_blank':True,'same_raw_material_different_order':True,'human_execution_completed':False,'sha256':hashes},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'future_human_n_per_coder':240,'completed':False,'training_overlap_n':0},ensure_ascii=False))
