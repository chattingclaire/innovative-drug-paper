from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import json,hashlib,math,datetime
R=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/coding-revision-20261007-r3');D=Path(__file__).parent
DIMS=['S','E','Ec','I','F'];GROUPS=['ALL','NMPA','NHSA','NHC'];CELLS=['TP','FP','FN','TN'];METRICS=['kappa','agreement','precision','recall','f1','left_positive_rate','right_positive_rate']
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p)}
def load(p):
 rows=[json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()];result={x['id']:x for x in rows};assert len(rows)==len(result);return result
def labels(r):return r.get('prediction',r)['labels']
def verify(b):assert sha(b['path'])==b['sha256'],b['path']
def write(name,j):(D/name).write_text(json.dumps(j,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
manifest_path=R/'statistics/final_bindings_v14_CONFIRMED_r3.json';manifest=read(manifest_path)
assert sha(manifest_path)=='46582af989d0473655b71ba38f174c2043794b8da9833bca9940aa0cf62c71cd'
old_path=R/'statistics/v33-v34.1-v35.1-v14-development-diagnostic/comparisons.json';old=read(old_path)
source=R/'rules-v36.2-development/final_candidate_binding.json';selected=read(source)
assert selected['version']=='v36.2-two-bounded-omissions-development'
assert selected['prediction']['sha256']=='105d10d7f441ed2c609911aa1f02bcaa4fc695acea35c6164750930a3021cc2b'
for k in ['prediction','run','freeze','input','QA']:verify(selected[k])
assert read(selected['QA']['path'])['all_checks_pass']
run=read(selected['run']['path'])
for p,s in run['runtime_code_sha256'].items():assert sha(p)==s
assert run['input_sha256']==manifest['material']['rule_inputs']['sha256']
for b in [manifest['sampling_design'],manifest['material']['rule_inputs'],manifest['references']['A'],manifest['references']['C']]:verify(b)
candidate={'path':str(R/'statistics/final-v14/candidate_reference.jsonl'),'sha256':'9f586dbebb774dd4ffd671ac948d0ea22f889462ba6d7047c0832076e02fa20e'};verify(candidate)
refbinds={**manifest['references'],'candidate':candidate};refs={k:load(v['path']) for k,v in refbinds.items()}
methodbinds={m:old['provenance']['methods'][m]['prediction'] for m in ['v33','v35.1']};prior36_path=R/'methods-20261008/v36.1-development-diagnostic/comparisons.json';prior36=read(prior36_path)
methodbinds['v36.1']=prior36['provenance']['methods']['v36.1'];methodbinds['v36.2']=selected['prediction']
for b in methodbinds.values():verify(b)
methods={k:load(v['path']) for k,v in methodbinds.items()};inputs=load(manifest['material']['rule_inputs']['path'])
for method in methods.values():
 assert set(method)==set(inputs) and len(method)==4924
 assert all(type(labels(x)[d]) is int and labels(x)[d] in (0,1) for x in method.values() for d in DIMS)
design=read(manifest['sampling_design']['path']);sample={x['original_id']:x for x in design['sample']}
assert len(sample)==240 and design['frame_N_by_group']=={'NMPA':947,'NHSA':760,'NHC':60}
assert Counter((x['component'],x['group']) for x in sample.values())==Counter({('probability_canonical',g):60 for g in GROUPS[1:]}|{('enriched_challenge',g):30 for g in ['NMPA','NHSA']})
assert all(set(ref)==set(sample) for ref in refs.values())
for x in sample.values():
 if x['component']=='probability_canonical':assert math.isclose(x['analysis_weight'],x['canonical_frame_N']/60)
 else:assert x['analysis_weight'] is None

def metrics(z):
 a,b,c,d=z;n=a+b+c+d
 div=lambda x,y:x/y if y else None
 po=div(a+d,n);p=div(a+b,n);q=div(a+c,n);pe=p*q+(1-p)*(1-q) if n else None
 return dict(zip(METRICS,[div(po-pe,1-pe) if n else None,po,div(a,a+b),div(a,a+c),div(2*a,2*a+b+c),p,q]))
rows=[]
for component in ['probability_canonical','enriched_challenge']:
 for group in GROUPS:
  ids=[rid for rid,x in sample.items() if x['component']==component and (group=='ALL' or x['group']==group)]
  for weighting in (['unweighted','eligible_design_weighted'] if component=='probability_canonical' else ['unweighted']):
   for m,pred in methods.items():
    for ref,truth in refs.items():
     for dim in DIMS:
      raw=[0]*4;weighted=[F(0)]*4;errors={'FP':[],'FN':[]}
      for rid in ids:
       a,b=labels(pred[rid])[dim],labels(truth[rid])[dim];cell={(1,1):0,(1,0):1,(0,1):2,(0,0):3}[a,b]
       raw[cell]+=1;weighted[cell]+=F(sample[rid]['canonical_frame_N'],60) if weighting=='eligible_design_weighted' else F(1)
       if cell in (1,2):errors[CELLS[cell]].append(rid)
      mm=metrics(weighted)
      rows.append({'component':component,'group':group,'weighting':weighting,'method':m,'reference':ref,'dimension':dim,'unit_frame_n':len(ids),'paired_n':len(ids),'excluded_pending_n':0,'paired_ids':ids,'raw_confusion':dict(zip(CELLS,raw)),'weighted_confusion':dict(zip(CELLS,map(float,weighted))),'exact_weighted_confusion':dict(zip(CELLS,map(str,weighted))),'metrics':{k:{'estimate':float(v) if v is not None else None,'exact_fraction':str(v) if v is not None else None} for k,v in mm.items()},'errors':errors,'confidence_intervals':'not_computed_requested_point_only'})
keys=['component','group','weighting','method','reference','dimension'];lookup={tuple(r[k] for k in keys):r for r in rows};checks=0
for previous in [*old['comparisons'],*prior36['comparisons']]:
 if previous['method'] not in ['v33','v35.1','v36.1']:continue
 now=lookup[tuple(previous[k] for k in keys)]
 assert now['raw_confusion']==previous['raw_confusion']
 for cell in CELLS:assert math.isclose(now['weighted_confusion'][cell],previous['weighted_confusion'][cell],rel_tol=1e-11,abs_tol=1e-10)
 for k in METRICS:
  a,b=now['metrics'][k]['estimate'],previous['metrics'][k]['estimate'];assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a,b,abs_tol=1e-10)),(now,k,a,b);checks+=1
comparisons=[]
for row in rows:
 if row['method']!='v36.2':continue
 for base in ['v33','v35.1','v36.1']:
  k=tuple(base if name=='method' else row[name] for name in keys);before=lookup[k];md={}
  for metric in ['kappa','precision','recall','f1']:
   a=before['metrics'][metric]['estimate'];b=row['metrics'][metric]['estimate'];delta=b-a if a is not None and b is not None else None
   md[metric]={'before':a,'after':b,'delta':delta,'status':'NA_transition' if delta is None else 'improved' if delta>1e-12 else 'worsened' if delta< -1e-12 else 'unchanged'}
  comparisons.append({**{k:row[k] for k in keys},'baseline':base,'metrics':md})
changes=[]
for baseline in ['v33','v35.1','v36.1']:
 for rid,x in sample.items():
  for dim in DIMS:
   a,b=labels(methods[baseline][rid])[dim],labels(methods['v36.2'][rid])[dim]
   if a!=b:changes.append({'id':rid,'dimension':dim,'baseline':baseline,'before':a,'after':b,'component':x['component'],'group':x['group'],'reference_comparison':{ref:{'label':labels(v[rid])[dim],'before_matches':a==labels(v[rid])[dim],'after_matches':b==labels(v[rid])[dim]} for ref,v in refs.items()}})
provenance={'stage':'post_exposure_development_diagnostic_only','all240_exposed':True,'independent_validation':False,'human_validation_completed':False,'formal_baseline':'v33 unchanged','material':'v14','scope':'probability180 and enrichedchallenge60 separate; within-department and overall raw and probability design-weighted results. Canonical remaining frames947/760/60; NHC challenge0 explicitly NA. Not full4481inference. No CI/newbootstrap/noLLMcandidate/no56scenario rerun.','reference_manifest':bind(manifest_path),'references':refbinds,'methods':methodbinds,'development_binding':bind(source),'previous_development_comparisons':bind(old_path),'previous_v36_1':bind(prior36_path),'sampling_design':manifest['sampling_design'],'source_qa':selected['QA'],'script_sha256':sha(__file__),'created_at':datetime.datetime.now().astimezone().isoformat()}
write('comparisons.json',{'provenance':provenance,'comparisons':rows});write('differences.json',{'provenance':provenance,'metric_deltas':comparisons,'sample_binary_case_dimension_changes':changes})
fmt=lambda x:'NA' if x is None else f'{x:.3f}'
md=['# v36.2开发点值诊断','', '全部240条已用于开发，不能视为独立验证。v33正式基线保留；A/C/候选参照均为AI标签流，尚未完成人工金标准验证。只复算点值，无新CI、bootstrap或文件敏感性。','', '概率180来自剩余canonical框947/760/60，设计权重分别947/60、760/60、1；不代表全4481。挑战60另列，两部门各30，卫健挑战为0。分部门设计权重恒定，点值与其未加权相同，JSON保留两种四格。0.8不是普遍发表线；NA不补1。','']
for comp,weight,title in [('probability_canonical','eligible_design_weighted','概率180，设计加权'),('probability_canonical','unweighted','概率180，未加权'),('enriched_challenge','unweighted','挑战60，未加权')]:
 md += [f'## {title}','', '|部门|参考|维度|v33 κ|v35.1 κ|v36.1 κ|v36.2 κ/P/R/F1|v36.2原始TP/FP/FN/TN|Δκ对v36.1|','|---|---|---|---:|---:|---:|---|---|---:|']
 for group in GROUPS:
  for ref in refs:
   for dim in DIMS:
    rr={m:lookup[comp,group,weight,m,ref,dim] for m in methods};current=rr['v36.2'];a=rr['v36.1']['metrics']['kappa']['estimate'];b=current['metrics']['kappa']['estimate']
    md.append('|'+ '|'.join([group,ref,dim,fmt(rr['v33']['metrics']['kappa']['estimate']),fmt(rr['v35.1']['metrics']['kappa']['estimate']),fmt(a),' / '.join(fmt(current['metrics'][z]['estimate']) for z in ['kappa','precision','recall','f1']),'/'.join(str(current['raw_confusion'][z]) for z in CELLS),fmt(b-a if a is not None and b is not None else None)])+'|')
 md.append('')
md+=['改善和退步均保留在differences.json；全体逐维原始/加权四格、P/R/F1、错误ID在comparisons.json。稀有阳性或退化边际下的NA均保留。样本中具体变化另列，无原文、标签、裁决或算法改写。']
(D/'开发点值表.md').write_text('\n'.join(md)+'\n')
qa={'pass':True,'exact_Fraction_metrics':True,'previous_v33_v35_1_v36_1_metric_point_crosschecks':checks,'comparison_rows':len(rows),'delta_rows':len(comparisons),'sample_changes_by_baseline':dict(Counter(x['baseline'] for x in changes)),'all_bound_input_hashes_pass':True,'original_changes':False,'CI_computed':False,'sample_n':240,'probability_n':180,'challenge_n':60}
write('point_QA.json',qa);write('output_freeze.json',{'files':{p.name:sha(p) for p in D.iterdir() if p.is_file() and p.name!='output_freeze.json'}})
print(json.dumps(qa,ensure_ascii=False))
for ref in refs:
 print(ref,[(dim,lookup['probability_canonical','ALL','eligible_design_weighted','v36.2',ref,dim]['metrics']['kappa']['estimate']) for dim in DIMS])
