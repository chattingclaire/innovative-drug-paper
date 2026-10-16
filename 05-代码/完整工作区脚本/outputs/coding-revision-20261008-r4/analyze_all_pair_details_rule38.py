"""Exhaustive descriptive detail screen; preserve all60 conditional contrasts.

Two directions per pair, three department contrasts, ten pairs. Does not
invent significance, causal effects, thresholds, human truth, or new labels.
"""
from pathlib import Path
from itertools import combinations
import json,hashlib

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'rules38-LLM03-synchronized-findings/完整定义构成核查.json'
OUT=HERE/'all-pair-attention-detail-analysis-rule38'
GROUPS=('NMPA','NHSA','NHC')
NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}

def get(deps,group,a,b,reverse):
    x=next(x for x in deps[group]['all10_pairs'] if (x['dimension_a'],x['dimension_b'])==(a,b))
    return x['p_a_given_b' if reverse else 'p_b_given_a'],x

def main():
    assert not OUT.exists()
    d=json.loads(SOURCE.read_text());methods=list(d['primary_full4481']);rows=[]
    pairs=[(x['dimension_a'],x['dimension_b']) for x in d['primary_full4481'][methods[0]]['departments'][GROUPS[0]]['all10_pairs']]
    for a,b in pairs:
        for reverse in (False,True):
            for one,two in combinations(GROUPS,2):
                row={'condition_dimension':b if reverse else a,'cooccurring_dimension':a if reverse else b,'department_one':one,'department_two':two,'methods':{}}
                for method in methods:
                    deps=d['primary_full4481'][method]['departments']
                    left,lc=get(deps,one,a,b,reverse);right,rc=get(deps,two,a,b,reverse)
                    value={'one':{'both_n':lc['both_n'],'condition_positive_n':lc['b_positive' if reverse else 'a_positive'],'conditional_share':left},'two':{'both_n':rc['both_n'],'condition_positive_n':rc['b_positive' if reverse else 'a_positive'],'conditional_share':right},'difference_percentage_points':100*(left-right) if left is not None and right is not None else None}
                    for key,items in [('definition6',[r['methods'][method]['full4481']['departments'] for r in d['definition6']]),('composition56',[r['methods'][method]['departments'] for r in d['composition56']])]:
                        vals=[]
                        for dep in items:
                            x,_=get(dep,one,a,b,reverse);y,_=get(dep,two,a,b,reverse)
                            vals.append(x-y if x is not None and y is not None else None)
                        defined=[v for v in vals if v is not None]
                        value[key]={'scenario_n':len(vals),'one_higher_n':sum(v>1e-12 for v in defined),'two_higher_n':sum(v< -1e-12 for v in defined),'equal_n':sum(abs(v)<=1e-12 for v in defined),'undefined_n':len(vals)-len(defined),'difference_percentage_point_range':[100*min(defined),100*max(defined)] if defined else None}
                    row['methods'][method]=value
                signs=[1 if r['difference_percentage_points']>1e-10 else -1 if r['difference_percentage_points']< -1e-10 else 0 for r in row['methods'].values()]
                row['two_method_primary_direction_same']=len(set(signs))==1
                row['same_primary_direction_in_all_definition_and_composition_scenarios']=all(v[k]['one_higher_n' if signs[0]==1 else 'two_higher_n']==v[k]['scenario_n'] for v in row['methods'].values() for k in ('definition6','composition56')) if len(set(signs))==1 and signs[0] else False
                row['minimum_primary_condition_positive_n']=min(v[g]['condition_positive_n'] for v in row['methods'].values() for g in ('one','two'))
                rows.append(row)
    assert len(rows)==60
    OUT.mkdir()
    report={'scope':'All10 dimension pairs ×2 conditional directions ×3 department pairs =60 comparisons, each in2 methods,6 definition and56 composition scenarios. Descriptive exhaustive screen, not preregistered hypotheses, significance/equivalence tests or independent human validation. Equal-file/series conditional shares follow existing mean-defined-cluster estimand, not pooled numerator/denominator.','source':{'path':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rows':rows}
    (OUT/'all60_conditional_department_contrasts.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    wanted=[('S','E','NHSA','NHC'),('S','E','NMPA','NHSA'),('Ec','F','NHSA','NHC'),('I','E','NMPA','NHSA'),('F','Ec','NHSA','NHC'),('E','F','NMPA','NHC'),('Ec','S','NHSA','NHC'),('Ec','E','NHSA','NHC')]
    selected=[r for r in rows if (r['condition_dimension'],r['cooccurring_dimension'],r['department_one'],r['department_two']) in wanted]
    (OUT/'重点候选细节_来自全60项.json').write_text(json.dumps({'screening_rule':'Theory-relevant detail candidates selected for qualitative source review; selection does not establish discovery or validity. All60 retained in companion JSON.','rows':selected},ensure_ascii=False,indent=2))
    print(json.dumps({'all_contrasts':len(rows),'both_methods_same_direction_n':sum(r['two_method_primary_direction_same'] for r in rows),'all62_scenarios_same_direction_n':sum(r['same_primary_direction_in_all_definition_and_composition_scenarios'] for r in rows),'selected':[{'condition':r['condition_dimension'],'cooccurring':r['cooccurring_dimension'],'departments':[r['department_one'],r['department_two']],'all62_consistent':r['same_primary_direction_in_all_definition_and_composition_scenarios'],'minimum_condition_n':r['minimum_primary_condition_positive_n'],'methods':{m:{'one':v['one'],'two':v['two'],'definition6':v['definition6'],'composition56':v['composition56']} for m,v in r['methods'].items()}} for r in selected]},ensure_ascii=False))

if __name__=='__main__':main()
