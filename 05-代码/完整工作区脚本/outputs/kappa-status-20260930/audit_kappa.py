from pathlib import Path
import sys,json,hashlib
from fractions import Fraction
from collections import Counter
ROOT=Path('/PROJECT_ROOT')
BASE=ROOT/'outputs/autocode-v25-20260927'
OUT=ROOT/'outputs/kappa-status-20260930'
sys.path.insert(0,str(BASE))
from comparison_statistics import agreement,DIMS
from analyze_current_reruns import normalize_rule_record
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def readlines(p):
 rows=[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
 data={r['id']:r for r in rows};assert len(data)==len(rows)
 return data
rp=BASE/'rule_runs/v25-candidate-3/all_predictions.jsonl';lp=BASE/'llm_runs/gpt56-sol-v13-native-1/all_predictions.jsonl'
r=readlines(rp);l=readlines(lp)
assert len(r)==4924 and set(r)==set(l)
assert sha(lp)==json.loads((lp.parent/'prediction_seal.json').read_text())['predictions_sha256']
assert sha(rp)==json.loads((rp.parent/'current_1268_comparison.json').read_text())['output_sha256']
r={k:normalize_rule_record(v['candidate'])['labels'] for k,v in r.items()}
l={k:v['labels'] for k,v in l.items()}
def checked(pairs):
 a=agreement(pairs)
 c=Counter((x,y) for x,y,w in pairs if x in (0,1) and y in (0,1));n=sum(c.values())
 numerator=n*(c[0,0]+c[1,1])-((c[0,0]+c[0,1])*(c[0,0]+c[1,0])+(c[1,0]+c[1,1])*(c[0,1]+c[1,1]))
 denominator=n*n-((c[0,0]+c[0,1])*(c[0,0]+c[1,0])+(c[1,0]+c[1,1])*(c[0,1]+c[1,1]))
 exact=float(Fraction(numerator,denominator)) if denominator else None
 assert exact is None or abs(exact-a['binary_agreement']['kappa'])<1e-12
 # A separate nominal three-state coefficient retains pending as a distinct state.
 full=Counter((x,y) for x,y,w in pairs);N=sum(full.values());levels=(0,1,'待定')
 obs=sum(full[z,z] for z in levels)/N
 exp=sum(sum(full[z,q] for q in levels)*sum(full[q,z] for q in levels) for z in levels)/(N*N)
 a['three_state_kappa_supplement']=(obs-exp)/(1-exp) if exp!=1 else None
 return a
new={d:checked([(r[k][d],l[k][d],1) for k in r]) for d in DIMS}
new['pooled_five_dimensions']=checked([(r[k][d],l[k][d],1) for k in r for d in DIMS])
oldbase=Path('/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/03-编码数据与脚本')
odp=oldbase/'coding_v3_dict.json';olp=oldbase/'coding_v3_llm.json'
odrows=json.loads(odp.read_text());olrows=json.loads(olp.read_text());od={z['id']:z for z in odrows};ol={z['id']:z for z in olrows}
assert len(od)==len(odrows) and len(ol)==len(olrows)==2965 and set(ol)<=set(od)
names=dict(zip(DIMS,['安全性','有效性','经济性','创新性','公平性']))
oldpairs={d:[(int(names[d] in od[k]['dims_v3']),int(names[d] in ol[k]['dims']),1) for k in ol] for d in DIMS}
old={d:checked(pairs) for d,pairs in oldpairs.items()};old['pooled_five_dimensions']=checked([pair for pairs in oldpairs.values() for pair in pairs])
# Descriptive reference-relative kappa on the same H427 common subsets used in existing P/R/F1 tables.
h=json.loads((BASE/'rerun_comparisons/H427/metrics.json').read_text())['scenarios']['primary']['methods'];hr={}
for ref in ('A','C'):
 hr[ref]={}
 for d in DIMS:
  hr[ref][d]={}
  for method in ('rules_v25','llm_gpt56_sol'):
   counts=h[ref][d]['by_method'][method]['common_units_unweighted']['confusion_on_joint_determinate']
   pairs=[]
   for label,x,y in [('TP',1,1),('FP',1,0),('FN',0,1),('TN',0,0)]:pairs.extend([(x,y,1)]*int(counts[label]))
   hr[ref][d][method]=checked(pairs)
result={'purpose':'Post-hoc descriptive clarification of the current rule–LLM Cohen kappa; no predictions or manuscript changed.','bindings':[{ 'path':str(p),'sha256':sha(p)} for p in [rp,lp,odp,olp]],'old_manuscript_reported_kappa':dict(zip(list(DIMS)+['pooled_five_dimensions'],[.702,.645,.693,.481,.606,.654])),'old_recalculated':old,'current_recalculated':new,'current_H427_relative_to_AI_references':hr,'limits':['Old and current standards, unit boundaries, models and corpus sizes differ; this is not a matched-version improvement estimate.','Current binary kappa is conditional on both methods assigning 0/1; pending remains recorded and is not zero-filled.','Pooled kappa combines unit-by-dimension decisions, not independent policy observations or the arithmetic mean of five kappas.','Method agreement and AI-reference agreement do not establish human accuracy or construct validity.','This audit is post-hoc descriptive, not new independent validation.']}
(OUT/'kappa-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('dimension | old reported | old recalculated | current | current common n | current pending rule/LLM | current three-state supplement')
for d in [*DIMS,'pooled_five_dimensions']:
 a=new[d];b=old[d]
 print(d, result['old_manuscript_reported_kappa'][d],round(b['binary_agreement']['kappa'],6),round(a['binary_agreement']['kappa'],6),int(a['joint_determinate_n_or_weight']),int(a['prediction_pending_n_or_weight']),int(a['reference_pending_n_or_weight']),round(a['three_state_kappa_supplement'],6))
print('H427 vs AI references, rule then LLM:')
for d in DIMS:print(d,{ref:{m:round(v['binary_agreement']['kappa'],6) for m,v in hr[ref][d].items()} for ref in hr})
