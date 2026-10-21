from pathlib import Path
from fractions import Fraction as F
from itertools import product
import json,sys,hashlib
R=Path('/PROJECT_ROOT/outputs/coding-revision-20261007-r3');S=R/'statistics';D=R/'methods-20261008';D.mkdir(exist_ok=True);sys.path.insert(0,str(S))
import statistical_core_r3 as c,final_binding_io_r3 as io
m=c.read(S/'final_bindings_v14_CONFIRMED_r3.json');ctx=io.context_from_manifest(m);refs,_=io.final_references(m,ctx)
ids=sorted(r for r,x in ctx['sample'].items() if x['component']=='probability_canonical')
N={'NMPA':947,'NHSA':760,'NHC':60}
def kappa(y,z,w):
 n=sum(w);tp=sum(t for a,b,t in zip(y,z,w) if a and b);p=sum(t for a,t in zip(y,w) if a);r=sum(t for b,t in zip(z,w) if b);den=n*(p+r)-2*p*r
 return 2*(n*tp-p*r)/den if den else None
bounds=[]
for dim in c.DIMS:
 a=[c.label(refs['A'][r],dim) for r in ids];b=[c.label(refs['C'][r],dim) for r in ids];diff=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
 for weighting,w in [('unweighted',[F(1) for r in ids]),('eligible_design_weighted',[F(N[ctx['sample'][r]['group']],60) for r in ids])]:
  scores=[]
  for choices in product([0,1],repeat=len(diff)):
   pred=a.copy()
   for i,z in zip(diff,choices):pred[i]=z
   ka=kappa(pred,a,w);kb=kappa(pred,b,w);scores.append((min(ka,kb),ka,kb))
  best=max(t[0] for t in scores);pairs=sorted(set((str(ka),str(kb)) for mm,ka,kb in scores if mm==best))
  bounds.append({'dimension':dim,'weighting':weighting,'A_positive_n':sum(a),'C_positive_n':sum(b),'disagreement_n':len(diff),'combinations_enumerated':2**len(diff),'best_possible_min_kappa':float(best),'best_possible_min_kappa_exact':str(best),'best_joint_kappa_pairs_exact':pairs,'can_both_reach_point_0_8':best>=F(4,5),'bound_scope':'Any arbitrary binary prediction vector on fixed180 references. Agreed A/C labels held at common value, which dominates flipping them for both kappas. All assignments of discordant units enumerated. This is logical compatibility, not an implementable or validated classifier; no labels/proposed predictions exported.'})
print(json.dumps(bounds,ensure_ascii=False,indent=2))
rows=c.read(S/'final-v14/machine_reference_classification.json')['comparisons'];ac=c.read(S/'final-v14/A_C_final_before_third_agreement.json')['comparisons'];diag=[]
for row in ac:
 for k,orig in [('raw_confusion','symmetric_raw_cells'),('weighted_confusion','symmetric_weighted_cells')]:row[k]=dict(zip(['TP','FP','FN','TN'],[row[orig][q] for q in ['A1_C1','A1_C0','A0_C1','A0_C0']]))
for row in rows+ac:
 if row['group']!='ALL' or row['component']!='probability_canonical':continue
 z=row['weighted_confusion'];a,b,cc,d=[z[k] for k in ['TP','FP','FN','TN']];n=a+b+cc+d;po=(a+d)/n;pbar=(2*a+b+cc)/(2*n);pe=2*pbar*(1-pbar)
 diag.append({k:row[k] for k in ['component','group','weighting','method','reference','dimension','raw_confusion','weighted_confusion','left_positive_n','reference_positive_n','metrics']}|{'positive_specific_agreement':2*a/(2*a+b+cc) if 2*a+b+cc else None,'negative_specific_agreement':2*d/(2*d+b+cc) if 2*d+b+cc else None,'AC1_descriptive_supplement':(po-pe)/(1-pe),'AC1_note':'Posthoc binary AC1 plug-in, no new CI, does not replace kappa or measure detection sensitivity; design-weighted rows apply same normalized survey weights.'})
sourcefiles=[S/'final_bindings_v14_CONFIRMED_r3.json',S/'final-v14/machine_reference_classification.json',S/'final-v14/A_C_final_before_third_agreement.json',S/'v33-v34.1-v35.1-v14-development-diagnostic/comparisons.json',S/'final-v14-reference-error-ledger_PRIVATE.json']
out={'scope':'Read-only audit, fixedv14; no original labels, methods or sample modified.','same180_reference_compatibility_bounds':bounds,'supplemental_agreement_diagnostics':diag,'source_bindings':[{'path':str(p),'sha256':c.sha(p)} for p in sourcefiles],'new_sampling':False,'new_inferential_tests':False}
c.write_json(D/'当前v14低值与参考兼容性审计.json',out)
