#!/usr/bin/env python3
"""Read-only historical A/C audit. Writes only beside this script.

Run --freeze once to copy inputs; then run without arguments. Calculations use
only hash-verified snapshots, never import historical calculation modules.
Python stdlib Fraction computes exact point estimates. NumPy reproduces the
historical conditional resampling scheme; sklearn independently checks points.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import argparse, hashlib, json, math, platform, sys, warnings

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
R3 = ROOT / 'outputs/coding-revision-20261007-r3'
BASE = OUT.parent / '00-baseline'
DIMS = ['S', 'E', 'Ec', 'I', 'F']
GROUPS = ['NMPA', 'NHSA', 'NHC']
STAGES = ['first_v9', 'final_v11', 'final_v12', 'final_v14']
N = {'NMPA':947, 'NHSA':760, 'NHC':60}
DESIGN = R3/'admin/confirmation_sampling_PRIVATE.json'
OLD_STATS = R3/'statistics/A_C协商前信度-first-v9与final-v11.json'
FINAL_STATS = R3/'statistics/final-v14/A_C_final_before_third_agreement.json'
ADOPTED_STATS = ROOT/'outputs/编码修订核查-20261008/统计复算/完整39与LLM03-同步复算01/A_C_before_third_agreement.json'
DOCS = [
 'outputs/goal-calibration-20261010/完整Goal指令.md',
 'outputs/final-three-department-20261007/指标依据与理论对齐.md',
 'outputs/coding-revision-20261007-r3/statistics/旧指标清单与r3绑定要求.md',
 'outputs/coding-revision-20261007-r3/methods-20261008/低值解释与方法处理依据.md',
 'outputs/indicator-alignment-20261007/指标与变量一致性审查.md',
 'outputs/final-three-department-20261008-human-validation-template/human-design-audit/真人复核统计方法预设冻结.json',
 'outputs/coding-revision-20261007-r3/statistics/statistical_core_r3.py',
 'outputs/coding-revision-20261007-r3/statistics/calculate_A_C_reliability_r3.py',
 'outputs/coding-revision-20261007-r3/statistics/final_bindings_v14_CONFIRMED_r3.json',
 'outputs/编码修订核查-20261008/指标复算准备/采用结果基线精确复算.json',
 'outputs/编码修订核查-20261008/统计复算/同样本注意力解释/同180四组注意力比较.md',
 'outputs/编码修订核查-20261008/统计复算/同样本注意力解释/低Cohenκ方法依据_独立原文核查.md',
 'outputs/编码修订核查-20261008/整套编码采用记录.json',
 'outputs/编码修订核查-20261008/定义溯源核查/方法依据/Hsieh_Shannon2005_relevant_pages.txt',
 '参考文献/中国政府推进基本公共服务的注意力测量——基于中央政府工作报告(1954—2013)的文本分析_文宏.md',
]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,obj):
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def jl(p): return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def original(p): return json.loads(Path(p).read_text())

def freeze():
 target=OUT/'input_manifest.json'
 if target.exists(): raise RuntimeError('Frozen manifest exists; never overwrite input snapshot.')
 paths={DESIGN, OLD_STATS, FINAL_STATS, ADOPTED_STATS}
 paths.update(ROOT/p for p in DOCS)
 paths.update(p for p in BASE.iterdir() if p.is_file())
 for stage in STAGES:
  for coder in ['A','C']:
   p=R3/f'reference/agent_{coder}_{stage}.jsonl'; paths.add(p)
   for r in jl(p):
    for event in ['first','effective']:
     v=r.get('annotation_provenance',{}).get(event,{})
     for k in ['result_path','packet_path']:
      if k in v: paths.add(Path(v[k]))
 (OUT/'snapshots').mkdir(exist_ok=True)
 records=[]
 for p in sorted(paths):
  b=p.read_bytes(); h=hashlib.sha256(b).hexdigest()
  dst=OUT/'snapshots'/f'{h[:16]}-{p.name}'
  if dst.exists(): assert dst.read_bytes()==b
  else: dst.write_bytes(b)
  records.append({'original':str(p),'snapshot':str(dst.relative_to(OUT)), 'sha256':h,'bytes':len(b)})
 write('input_manifest.json',{'scope':'historical diagnostic only; no model execution or label changes','files':records})
 print(json.dumps({'frozen_files':len(records),'bytes':sum(r['bytes'] for r in records)}))

def safe(x):
 return None if x is None else {'exact':str(x),'estimate':float(x)}
def metrics(c):
 a,b,c,d=map(F,c); n=a+b+c+d
 ratio=lambda x,y: x/y if y else None
 return {k:safe(v) for k,v in {
  'kappa':ratio(2*(a*d-b*c),(a+b)*(b+d)+(a+c)*(c+d)),
  'agreement':ratio(a+d,n),'left_positive_rate':ratio(a+b,n),
  'right_positive_rate':ratio(a+c,n),'positive_agreement':ratio(2*a,2*a+b+c),
  'negative_agreement':ratio(2*d,2*d+b+c),
 }.items()}
def binary(x): return type(x) is int and x in [0,1]
def close(a,b): return a is None and b is None or a is not None and b is not None and abs(float(a)-float(b))<1e-10

def main():
 import numpy as np
 import sklearn
 from sklearn.metrics import cohen_kappa_score, confusion_matrix, precision_recall_fscore_support
 manifest=original(OUT/'input_manifest.json'); files={r['original']:r for r in manifest['files']}
 def path(p):
  r=files[str(p)]; q=OUT/r['snapshot']; assert sha(q)==r['sha256']; return q
 def read(p): return original(path(p))
 def rows(p):
  r=jl(path(p)); idx={x['id']:x for x in r}; assert len(idx)==len(r); return idx
 design=read(DESIGN); sample={r['original_id']:r for r in design['sample']}
 assert len(sample)==240 and design['frame_N_by_group']==N
 assert Counter((r['component'],r['group']) for r in sample.values())==Counter({('probability_canonical',g):60 for g in GROUPS}|{('enriched_challenge',g):30 for g in GROUPS[:2]})
 for r in sample.values():
  if r['component']=='probability_canonical':
   assert close(r['analysis_weight'],F(N[r['group']],60))
   assert close(r['inclusion_probability'],F(60,N[r['group']]))
  else: assert r['analysis_weight'] is None
 flows={(s,k):rows(R3/f'reference/agent_{k}_{s}.jsonl') for s in STAGES for k in ['A','C']}
 # Verify every effective label against ORIGINAL submitted JSON, using sealed blind IDs.
 provenance_checks=[]
 for (stage,coder),flow in flows.items():
  assert set(flow)==set(sample)
  for rid,row in flow.items():
   event='first' if stage=='first_v9' else 'effective'
   prov=(flows[('final_v11',coder)][rid]['annotation_provenance']['first'] if event=='first' else row['annotation_provenance']['effective'])
   rp=Path(prov['result_path']); pp=Path(prov['packet_path'])
   assert sha(path(rp))==prov['result_sha256'] and sha(path(pp))==prov['packet_sha256']
   raw=read(rp); pkt=read(pp); bid=prov['blind_id']
   rr=next(x for x in raw['rows'] if x['id']==bid)
   pr=next(x for x in pkt['rows'] if x['id']==bid)
   assert row['labels']==rr['labels'], (stage,coder,rid)
   assert hashlib.sha256(pr['text'].encode()).hexdigest()==sample[rid]['unit_text_sha256']
   provenance_checks.append((stage,coder,rid))
 comparisons=[]; official_checks=[]; factors={}
 metric_names=['kappa','agreement','left_positive_rate','right_positive_rate','positive_agreement','negative_agreement']
 def vec_metrics(cell):
  a,b,c,d=cell.T; total=a+b+c+d
  def div(x,y): return np.divide(x,y,out=np.full_like(x,np.nan,dtype=float),where=y!=0)
  return np.stack([div(2*(a*d-b*c),(a+b)*(b+d)+(a+c)*(c+d)),div(a+d,total),div(a+b,total),div(a+c,total),div(2*a,2*a+b+c),div(2*d,2*d+b+c)],axis=1)
 def boot(ids,component,group):
  key=(tuple(ids),component,group)
  if key in factors:return factors[key]
  mechanism='department_unit_rescaled_SRSWOR' if component=='probability_canonical' else 'department_unit_conditional_WR'
  parts='/'.join([component,mechanism,'/'.join(ids)])
  seed=(2026100731+int(hashlib.sha256(parts.encode()).hexdigest()[:8],16))%2**32
  rng=np.random.default_rng(seed); f=np.zeros((5000,len(ids)))
  for g in GROUPS:
   ix=[i for i,rid in enumerate(ids) if sample[rid]['group']==g]; n=len(ix)
   if not n:continue
   m=n-1 if component=='probability_canonical' else n
   M=rng.multinomial(m,np.repeat(1/n,n),size=5000)
   v=1+math.sqrt(1-n/N[g])*(n/m*M-1) if component=='probability_canonical' else M
   f[:,ix]=v
  factors[key]=f;return f
 for stage in STAGES:
  A=flows[(stage,'A')]; C=flows[(stage,'C')]
  for component in ['probability_canonical','enriched_challenge']:
   groups=[('ALL','unweighted')]+[(g,'unweighted') for g in GROUPS if component=='probability_canonical' or g!='NHC']
   if component=='probability_canonical': groups += [(g,'eligible_design_weighted') for g in ['ALL']+GROUPS]
   for group,weighting in groups:
    ids=sorted(rid for rid,r in sample.items() if r['component']==component and (group=='ALL' or r['group']==group))
    weights={rid:F(N[sample[rid]['group']],60) if weighting=='eligible_design_weighted' else F(1) for rid in ids}
    for dim in DIMS:
     paired=[rid for rid in ids if binary(A[rid]['labels'][dim]) and binary(C[rid]['labels'][dim])]
     cell_pairs=[(1,1),(1,0),(0,1),(0,0)]
     cids=[[rid for rid in paired if (A[rid]['labels'][dim],C[rid]['labels'][dim])==pair] for pair in cell_pairs]
     raw=[len(x) for x in cids]; weighted=[sum((weights[rid] for rid in x),F(0)) for x in cids]
     point=metrics(weighted)
     yA=[A[rid]['labels'][dim] for rid in paired]; yC=[C[rid]['labels'][dim] for rid in paired]; sw=[float(weights[rid]) for rid in paired]
     with warnings.catch_warnings():
      warnings.simplefilter('ignore')
      kap=cohen_kappa_score(yA,yC,labels=[0,1],weights=None,sample_weight=sw)
      cm=confusion_matrix(yA,yC,labels=[0,1],sample_weight=sw)
      # Symmetric positive agreement equals binary F1; neither coder is truth here.
      _,_,f1,_=precision_recall_fscore_support(yC,yA,average='binary',pos_label=1,sample_weight=sw,zero_division=np.nan)
     assert close(point['kappa']['estimate'] if point['kappa'] else None, float(kap) if np.isfinite(kap) else None)
     assert np.allclose(cm,[[float(weighted[3]),float(weighted[2])],[float(weighted[1]),float(weighted[0])]])
     assert close(point['positive_agreement']['estimate'] if point['positive_agreement'] else None,float(f1) if np.isfinite(f1) else None)
     official_checks.append([stage,component,group,weighting,dim])
     mat=np.zeros((len(ids),4))
     for j,cc in enumerate(cids):
      for rid in cc:mat[ids.index(rid),j]=1
     vals=vec_metrics((boot(ids,component,group)*np.array([float(weights[r]) for r in ids]))@mat)
     cis={}
     for j,name in enumerate(metric_names):
      good=vals[:,j][np.isfinite(vals[:,j])]
      cis[name]={'low':float(np.quantile(good,.025)) if len(good) else None,'high':float(np.quantile(good,.975)) if len(good) else None,'defined_repetitions':len(good),'undefined_repetitions':5000-len(good),'conditional_on_defined':len(good)<5000,'degenerate':bool(len(good) and np.min(good)==np.max(good))}
     comparisons.append({'stage':stage,'component':component,'group':group,'weighting':weighting,'dimension':dim,'frame_n':len(ids),'paired_n':len(paired),'excluded_ids':[r for r in ids if r not in paired],'cell_order':['A1_C1','A1_C0','A0_C1','A0_C0'],'raw_cells':raw,'weighted_cells_exact':list(map(str,weighted)),'weighted_cells':list(map(float,weighted)),'cell_ids':cids,'A_positive_n':raw[0]+raw[1],'C_positive_n':raw[0]+raw[2],'A_negative_n':raw[2]+raw[3],'C_negative_n':raw[1]+raw[3],'weighted_A_positive':str(weighted[0]+weighted[1]),'weighted_C_positive':str(weighted[0]+weighted[2]),'weighted_A_negative':str(weighted[2]+weighted[3]),'weighted_C_negative':str(weighted[1]+weighted[3]),'paired_weight_sum':str(sum(weighted)),'metrics':point,'ci95':cis})
 # Compare all present estimates/cells/primary CI against actual adopted result files.
 comparison_lookup={(r['stage'],r['component'],r['group'],r['weighting'],r['dimension']):r for r in comparisons}
 adopted=[]; mismatch=[]
 for p,default_stage in [(OLD_STATS,None),(FINAL_STATS,'final_v14'),(ADOPTED_STATS,'final_v14')]:
  for r in read(p)['comparisons']:
   key=(default_stage or r['stage'],r['component'],r['group'],r['weighting'],r['dimension'])
   if key not in comparison_lookup:
    assert key[1:4]==('enriched_challenge','NHC','unweighted')
    checks={'empty_placeholder_not_sampled':r['paired_n']==0 and r['unit_frame_n']==0,
      'zero_cells':not any(r['symmetric_raw_cells'].values()),
      'all_points_NA':all(v['estimate'] is None for v in r['metrics'].values())}
    rec={'source':str(p),'comparison':list(key),'checks':checks,'pass':all(checks.values())}
    adopted.append(rec)
    if not rec['pass']:mismatch.append(rec)
    continue
   got=comparison_lookup[key]
   checks={'raw_cells':got['raw_cells']==list(r['symmetric_raw_cells'].values()),'weighted_cells':all(close(x,y) for x,y in zip(got['weighted_cells'],r['symmetric_weighted_cells'].values())),'paired_n':got['paired_n']==r['paired_n'],'excluded_ids':got['excluded_ids']==r['excluded_ids']}
   for name,value in r['metrics'].items():
    checks[name]=close(got['metrics'][name]['estimate'] if got['metrics'][name] else None,value['estimate'])
    if 'ci95_primary' in value:
     old=value['ci95_primary']; new=got['ci95'][name]
     for k in ['low','high','defined_repetitions','undefined_repetitions']:checks[name+'_ci_'+k]=close(new[k],old[k])
   rec={'source':str(p),'comparison':list(key),'checks':checks,'pass':all(checks.values())};adopted.append(rec)
   if not rec['pass']:mismatch.append(rec)
 # Source/reread changes are kept separate from disagreement on same version.
 transitions=[]
 for prev,nxt in zip(STAGES,STAGES[1:]):
  for coder in ['A','C']:
   for rid in sorted(sample):
    x=flows[(prev,coder)][rid]; y=flows[(nxt,coder)][rid]
    changes={d:{'before':x['labels'][d],'after':y['labels'][d]} for d in DIMS if x['labels'][d]!=y['labels'][d]}
    if changes:transitions.append({'from':prev,'to':nxt,'coder':coder,'id':rid,'component':sample[rid]['component'],'changes':changes,'effective_provenance':y['annotation_provenance']['effective']})
 disagreements=[]
 for rid in sorted(sample):
  a=flows[('final_v14','A')][rid]; c=flows[('final_v14','C')][rid]
  for dim in DIMS:
   if a['labels'][dim]!=c['labels'][dim]:
    pp=a['annotation_provenance']['effective']; packet=read(pp['packet_path']); pr=next(r for r in packet['rows'] if r['id']==pp['blind_id'])
    disagreements.append({'id':rid,'dimension':dim,'component':sample[rid]['component'],'department':sample[rid]['group'],'design_weight':str(F(N[sample[rid]['group']],60)) if sample[rid]['component']=='probability_canonical' else None,'A':a['labels'][dim],'C':c['labels'][dim],'A_reason':a['dimension_reasons'][dim],'C_reason':c['dimension_reasons'][dim],'text':pr['text'],'A_provenance':pp,'C_provenance':c['annotation_provenance']['effective']})
 baseline=read(BASE/'snapshot_manifest.json')
 baseline_checks=[{'path':r['snapshot'],'recorded_sha':r['sha256'],'actual_sha':sha(path(r['snapshot'])),'pass':r['sha256']==sha(path(r['snapshot']))} for r in baseline['files']]
 changes=read(BASE/'legacy-calibration-changes.json'); candidate_sha=sha(path(BASE/'legacy-calibration-manual.md'))
 stale={'recorded_candidate_sha':changes['candidate']['sha256'],'actual_frozen_candidate_sha':candidate_sha,'match':changes['candidate']['sha256']==candidate_sha,'meaning':'metadata/version mismatch, not statistical formula error; do not change original files'}
 frame=jl(path(BASE/'source-only-frame.jsonl'))
 summary={'historical_scope':'AI initial judgments, with documented user-confirmed retrospective human review; not independent human first coding; C displayed as B later','design':{k:design[k] for k in ['frame_N_by_group','probability_n','challenge_n','probability_scope','challenge_scope','NHC_challenge_n']},'total_comparisons':len(comparisons),'original_submission_label_checks':len(provenance_checks),'official_sklearn_comparisons':len(official_checks),'adopted_comparisons':len(adopted),'adopted_mismatches':mismatch,'baseline_snapshot_checks':baseline_checks,'calibration_change_log_stale_binding':stale,'full_frame_rows':len(frame),'label_transition_count':len(transitions),'final_disagreement_dimensions':len(disagreements),'final_disagreement_units':len({r['id'] for r in disagreements}),'runtime':{'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'numpy':np.__version__,'sklearn':sklearn.__version__},'bootstrap':{'B':5000,'base_seed':2026100731,'rng':'numpy.default_rng PCG64','quantile':'numpy.quantile linear','scope':'reproduce fixed historical labels and design; not semantic uncertainty','undefined':'conditional finite-replicate percentile only; explicit counts; not imputed'},'script_sha256':sha(__file__),'input_manifest_sha256':sha(OUT/'input_manifest.json')}
 write('recomputed_AC.json',{'metadata':summary,'comparisons':comparisons})
 write('adopted_result_crosscheck.json',{'summary':summary,'comparisons':adopted})
 write('label_changes_and_disagreements.json',{'transitions':transitions,'final_disagreements':disagreements})
 print(json.dumps({k:v for k,v in summary.items() if k not in ['baseline_snapshot_checks','design','runtime']},ensure_ascii=False,indent=2))
 for r in comparisons:
  if r['stage']=='final_v14' and r['group']=='ALL':
   print(r['component'],r['weighting'],r['dimension'],r['raw_cells'],{k:v['estimate'] if v else None for k,v in r['metrics'].items()})

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
 freeze() if args.freeze else main()
