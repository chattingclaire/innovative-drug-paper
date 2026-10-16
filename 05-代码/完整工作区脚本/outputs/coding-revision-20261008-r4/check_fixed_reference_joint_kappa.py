"""Exact finite diagnostic: can one binary coding agree >=.80 with both A/B?

No new indicator in the paper, no gold-label selection, no label changes.
Enumerates disagreement-cell prediction counts per equal-weight stratum.
For any t>0, setting a consensus11 unit to1 improves BOTH inequalities
po-(1-t)pe>=t; setting a consensus00 unit to0 also improves BOTH.
Thus consensus flips cannot make a positive joint threshold feasible.
"""
from pathlib import Path
from fractions import Fraction as Q
from itertools import product
import json, hashlib, math

BASE=Path(__file__).resolve().parents[2]
SOURCE=BASE/'outputs/coding-revision-20261007-r3/methods-20261008/rules-v36.2-plus-LLM03-reconciled-development-complete-statistics-v3/A_C_before_third_agreement.json'
OUT=Path(__file__).with_name('固定AB参照共同κ目标可行性核查.json')
NFRAME={'NMPA':947,'NHSA':760,'NHC':60}
DIMS=('S','E','Ec','I','F')

def kap(N, pos, p, tp):
    po=(N-pos-p+2*tp)/N
    pe=(pos*p+(N-pos)*(N-p))/(N*N)
    return (po-pe)/(1-pe) if pe!=1 else None

def main():
    assert not OUT.exists()
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(SOURCE)=='724745a210e9ca5ed667e7a61fe55a8abce4ef2b7d89adc42f51159f447204e3'
    source=json.loads(SOURCE.read_text())
    result=[]
    for dim in DIMS:
        groups=[]
        for g,Nh in NFRAME.items():
            row=next(x for x in source['comparisons'] if x['component']=='probability_canonical' and x['group']==g and x['weighting']=='unweighted' and x['dimension']==dim)
            groups.append({'group':g,'weight':Q(Nh,60),'cells':row['symmetric_raw_cells']})
        N=sum(Q(NFRAME[g]) for g in NFRAME)
        joint=sum(x['weight']*x['cells']['A1_C1'] for x in groups)
        a=joint+sum(x['weight']*x['cells']['A1_C0'] for x in groups)
        b=joint+sum(x['weight']*x['cells']['A0_C1'] for x in groups)
        varying=[(x['group'],cell,x['weight'],x['cells'][cell]) for x in groups for cell in ('A1_C0','A0_C1') if x['cells'][cell]]
        best=None; winners=[]; tested=0
        for choices in product(*(range(count+1) for _,_,_,count in varying)):
            tested+=1
            p=joint+sum(w*n for (_,_,w,_),n in zip(varying,choices))
            tpa=joint+sum(w*n for (_,cell,w,_),n in zip(varying,choices) if cell=='A1_C0')
            tpb=joint+sum(w*n for (_,cell,w,_),n in zip(varying,choices) if cell=='A0_C1')
            ka,kb=kap(N,a,p,tpa),kap(N,b,p,tpb)
            if ka is None or kb is None:continue
            score=min(ka,kb)
            if best is None or score>best:best=score;winners=[]
            if score==best:winners.append({'kappa_to_A':str(ka),'kappa_to_B':str(kb),'prediction1_counts_in_disagreement_cells':[{'group':g,'cell':cell,'selected1':n,'available':count} for (g,cell,w,count),n in zip(varying,choices)]})
        result.append({'dimension':dim,'weighted_population_mass':str(N),'A_positive_mass':str(a),'B_positive_mass':str(b),'raw_disagreement_n':sum(x['cells']['A1_C0']+x['cells']['A0_C1'] for x in groups),'distinct_count_patterns_enumerated':tested,'maximum_of_smaller_two_kappas_exact':str(best),'maximum_of_smaller_two_kappas':float(best),'joint_kappa_ge_0_80_feasible':best>=Q(4,5),'maximizers':winners})
    OUT.write_text(json.dumps({'status':'EXACT_ENUMERATION_COMPLETE','scope':'Fixed existing180 probability sample and A/B labels, design weights N_h/60. This is a feasibility diagnostic, not independent validation or a new manuscript metric.','source':{'path':str(SOURCE),'sha256':sha(SOURCE)},'script_sha256':sha(Path(__file__)),'label_changes':False,'proof_of_reduction':'For kappa>=t with fixed reference prevalence a, coefficient of predicted1 is 2*y-1-(1-t)*(2*a-1). For 0<t<=1 it is positive when y=1 and negative when y=0. Hence preserving all common11/common00 labels weakly improves both threshold constraints; only disagreement assignments matter. Stratum-constant weights permit complete enumeration of integer prediction1 counts in each disagreement cell.','results':result},ensure_ascii=False,indent=2))
    print(json.dumps({'path':str(OUT),'results':[{k:x[k] for k in ['dimension','raw_disagreement_n','distinct_count_patterns_enumerated','maximum_of_smaller_two_kappas','joint_kappa_ge_0_80_feasible']} for x in result]},ensure_ascii=False))

if __name__=='__main__':main()
