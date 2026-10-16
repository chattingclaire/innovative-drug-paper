"""Prepare development-excluded agent reference packets; never reads new labels."""
from pathlib import Path
import hashlib,json,random,re,collections
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'outputs/recall-revision-20261007'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
inputs=jl(OLD/'effective_blind_inputs_v30_v3.jsonl')
rules=jl(OLD/'rule_inputs_v31_shared_v3.jsonl')
meta=json.loads((ROOT/'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json').read_text())['rows']
cls={Path(x['original_file']).stem:x for x in meta}
groups={r['id']:cls[r['input']['original_file_stem']]['analysis_group'] for r in rules}
sources=[ROOT/'outputs/autocode-v25-20260927/current_1268_references.jsonl',ROOT/'outputs/autocode-v25-20260927/H427/admin_mapping.json',OLD/'blind_mapping_PRIVATE.json']
sources+=list((OLD/'llm-v30').glob('*semantic*json'))+list((OLD/'statistics-material-effect').glob('*semantic*json'))
sources+=list((OLD/'llm-v30').glob('stability*/**/*input*.json*'))
sources+=list(OLD.glob('blind*json*'))
excluded=set()
for p in sources:
 if p.exists():excluded.update(re.findall(r'RECODE25-\d{5}',p.read_text()))
rows={r['id']:r for r in inputs if groups[r['id']] in ('NMPA','NHSA','NHC') and r['id'] not in excluded}
prior_rule={r['id']:r['prediction']['labels'] for r in jl(OLD/'rules-v31/all_predictions_completed_material_v3.jsonl')}
prior_llm={r['id']:r.get('prediction',r)['labels'] for r in jl(OLD/'llm-v30/sealed-final-material-v3/all_predictions.jsonl')}
rng=random.Random(2026100719)
sample=[];design=[]
for g in ('NMPA','NHSA','NHC'):
 pool=sorted(rid for rid in rows if groups[rid]==g)
 assert len(pool)>=100,(g,len(pool))
 base=rng.sample(pool,80)
 for rid in base:design.append({'original_id':rid,'group':g,'component':'probability_base','eligible_N':len(pool),'sample_n':80,'inclusion_probability':80/len(pool),'analysis_weight':len(pool)/80})
 # Challenge sample is intentionally enriched and never treated as representative.
 eligible=[rid for rid in pool if rid not in base and (prior_rule[rid]['I'] or prior_llm[rid]['I'] or prior_rule[rid]['F']!=prior_llm[rid]['F'])]
 if len(eligible)<20:eligible=[rid for rid in pool if rid not in base and any(prior_rule[rid][d] or prior_llm[rid][d] for d in ('I','F','E','Ec'))]
 assert len(eligible)>=20,(g,len(eligible))
 challenge=rng.sample(sorted(eligible),20)
 for rid in challenge:design.append({'original_id':rid,'group':g,'component':'enriched_challenge','conditional_pool_N':len(eligible),'sample_n':20,'conditional_selection_probability':20/len(eligible),'analysis_weight':None})
 sample.extend(base+challenge)
assert len(sample)==len(set(sample))==300 and not set(sample)&excluded
mapping=[]
for coder,seed in [('A',2026100721),('C',2026100727)]:
 order=list(sample);random.Random(seed).shuffle(order)
 packet=[]
 for i,rid in enumerate(order,1):
  bid=f'AV2-{coder}-{i:04d}'
  r=rows[rid];packet.append({**r,'id':bid})
  mapping.append({'coder':coder,'blind_id':bid,'original_id':rid,'text_sha256':hashlib.sha256(r['text'].encode()).hexdigest()})
 folder=OUT/'confirmation'/f'agent-{coder}'
 for b in range(10):dump(folder/f'材料-{b+1:02d}.json',{'rows':packet[b*30:(b+1)*30]})
 dump(folder/'任务说明.json',{'coder':coder,'n':300,'batches':10,'per_batch':30,'protocol':str(OUT/'protocol/完整五维手册-v1.3.md'),'operational_clarifications':str(OUT/'共用操作说明-v1.4.md'),'origin':'AI agent预验证，供真人培训使用；不得声称真人编码','blindness':'不读取机器结果、其他编码员标签、指标或预期分布；来源语义可能透露部门，非来源身份双盲'})
dump(OUT/'admin/PRIVATE_mapping.json',mapping)
dump(OUT/'admin/sampling_design.json',{'seed':2026100719,'source_input_sha256':sha(OLD/'effective_blind_inputs_v30_v3.jsonl'),'source_rules_input_sha256':sha(OLD/'rule_inputs_v31_shared_v3.jsonl'),'excluded_development_n':len(excluded),'eligible_by_group':dict(collections.Counter(groups[x] for x in rows)),'excluded_ids':sorted(excluded),'sample':design,'scope':'Probability component represents development-excluded eligible units only, not the complete 4481-unit corpus. Enriched challenge component reported separately; no naive pooled prevalence.'})
protected=[OLD/'effective_blind_inputs_v30_v3.jsonl',OLD/'rule_inputs_v31_shared_v3.jsonl',OLD/'rules-v31/all_predictions_completed_material_v3.jsonl',OLD/'llm-v30/sealed-final-material-v3/all_predictions.jsonl',ROOT/'outputs/autocode-v25-20260927/current_1268_references.jsonl']
dump(OUT/'admin/baseline_hashes.json',{str(p):sha(p) for p in protected})
dump(OUT/'protocol/freeze.json',{'status':'frozen_before_agent_confirmation','protocol_sha256':sha(OUT/'protocol/完整五维手册-v1.3.md'),'clarification_sha256':sha(OUT/'共用操作说明-v1.4.md'),'packets':{str(p.relative_to(OUT)):sha(p) for p in sorted((OUT/'confirmation').glob('agent-*/材料-*.json'))},'sampling_design_sha256':sha(OUT/'admin/sampling_design.json'),'reference_type':'AI-agent procedural-blind prevalidation','human_validation_completed':False,'work_targets':{'kappa':.8,'precision':.8,'recall':.8,'f1':.8},'targets_are_universal_publication_thresholds':False,'no_data_dependent_equivalence_margin':True})
print(json.dumps({'n':300,'probability_n':240,'challenge_n':60,'eligible_by_group':dict(collections.Counter(groups[x] for x in rows)),'excluded_n':len(excluded),'manual_sha256':sha(OUT/'共用操作说明-v1.4.md')},ensure_ascii=False))
