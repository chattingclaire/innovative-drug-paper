"""Exact, independent label-change sensitivity; never alters any observed row.

No statistical/adapter metric functions are imported. Unit cost is total variation
between four-cell counts: a unit may change both Ec and F at cost one.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import hashlib, json

OUT = Path(__file__).resolve().parent
R3 = OUT.parents[1]
ADOPTION = R3 / 'manuscript-update-20261008/measurement-adapter-v3/采用方法_ROOT_CONFIRMED-v6.json'
ADOPTION_SHA = '0eb45f79319fa56c4da7369b6cb70291360813292899de0ea09c407a98529d65'
CELLS = ('Ec1_F1', 'Ec1_F0', 'Ec0_F1', 'Ec0_F0')
LABELS = ((1, 1), (1, 0), (0, 1), (0, 0))
BOUND = {}

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verified(b):
    p = Path(b['path'])
    assert p.is_absolute() and p.is_file() and digest(p) == b['sha256']
    BOUND[str(p)] = {'path':str(p), 'sha256':b['sha256']}
    return p

def obj(b):
    return json.loads(verified(b).read_text())

def rows(b):
    values = [json.loads(s) for s in verified(b).read_text().splitlines() if s.strip()]
    assert len(values) == 4924 and len({x['id'] for x in values}) == 4924
    return {x['id']:x for x in values}

def frac(x):
    return {'exact':str(x), 'decimal':float(x)}

def rate(state):
    return Fraction(state[0], state[0] + state[1])

def cost(original, new):
    assert sum(original) == sum(new)
    return sum(max(0, n - a) for a, n in zip(original, new))

def witness(original, new):
    donors = [[i, max(0, a-n)] for i, (a,n) in enumerate(zip(original,new))]
    receivers = [[i, max(0, n-a)] for i, (a,n) in enumerate(zip(original,new))]
    moves = []
    for i, supply in donors:
        for target in receivers:
            j, demand = target
            amount = min(supply, demand)
            if amount:
                moves.append({'from':CELLS[i], 'to':CELLS[j], 'units':amount,
                              'labels_changed_per_unit':sum(a != b for a,b in zip(LABELS[i],LABELS[j]))})
                supply -= amount
                target[1] -= amount
    assert sum(x['units'] for x in moves) == cost(original,new)
    return {'four_cells':dict(zip(CELLS,new)), 'Ec_denominator':new[0]+new[1],
            'F_given_Ec':frac(rate(new)), 'changed_units':cost(original,new), 'moves':moves}

def pair_example(h, c, nh, nc):
    d = rate(nc)-rate(nh)
    return {'NHSA':witness(h,nh), 'NHC':witness(c,nc),
            'total_changed_units':cost(h,nh)+cost(c,nc),
            'NHC_minus_NHSA':frac(d), 'relation':'equal' if d==0 else 'strict_reversal' if d<0 else 'original_direction'}

def fixed_ec(h,c):
    eh,ec = sum(h[:2]),sum(c[:2])
    results = {k:{'minimum_units':None, 'examples':[]} for k in ('NHC_le_NHSA','NHC_lt_NHSA','NHC_eq_NHSA')}
    for ah in range(eh+1):
        for ac in range(ec+1):
            difference = Fraction(ac,ec)-Fraction(ah,eh)
            n = abs(ah-h[0])+abs(ac-c[0])
            for key,eligible in (('NHC_le_NHSA',difference<=0),('NHC_lt_NHSA',difference<0),('NHC_eq_NHSA',difference==0)):
                if not eligible: continue
                old = results[key]['minimum_units']
                if old is None or n<old:
                    results[key]={'minimum_units':n,'examples':[]}
                if n==results[key]['minimum_units']:
                    nh=(ah,eh-ah,h[2],h[3]);nc=(ac,ec-ac,c[2],c[3])
                    results[key]['examples'].append(pair_example(h,c,nh,nc))
    results['enumerated_numerator_pairs']=(eh+1)*(ec+1)
    results['proof']='With Ec fixed, changing an F label outside Ec has no effect. Reaching each numerator requires exactly its absolute change in F flips among Ec units. All feasible numerator pairs were enumerated.'
    return results

def reachable(original,budget):
    """Every feasible four-cell target within total-variation radius budget."""
    found=[]
    for d0 in range(-budget,budget+1):
        for d1 in range(-budget,budget+1):
            for d2 in range(-budget,budget+1):
                delta=(d0,d1,d2,-d0-d1-d2)
                n=sum(max(0,x) for x in delta)
                if n>budget: continue
                new=tuple(a+d for a,d in zip(original,delta))
                if min(new)<0 or new[0]+new[1]==0: continue
                assert cost(original,new)==n
                found.append((n,rate(new),new))
    return found

def both_dimensions(h,c,budget=20):
    hs,cs=reachable(h,budget),reachable(c,budget)
    hmax={};cmin={};hbyq={};cbyq={}
    for states,extreme,byq,wantmax in ((hs,hmax,hbyq,True),(cs,cmin,cbyq,False)):
        for n,q,state in states:
            if n not in extreme or (q>extreme[n][0] if wantmax else q<extreme[n][0]):extreme[n]=(q,state)
            if q not in byq or n<byq[q][0]:byq[q]=(n,state)
    levels=[]
    for total in range(budget+1):
        possibilities=[]
        for kh in range(total+1):
            for kc in range(total-kh+1):
                if kh in hmax and kc in cmin:
                    possibilities.append((cmin[kc][0]-hmax[kh][0],kh,kc,hmax[kh][1],cmin[kc][1]))
        delta,kh,kc,nh,nc=min(possibilities)
        levels.append({'budget_at_most':total,'minimum_possible_NHC_minus_NHSA':frac(delta),
                       'best_allocation':{'NHSA':kh,'NHC':kc},'example':pair_example(h,c,nh,nc)})
    result={}
    for name,test in (('NHC_le_NHSA',lambda q:q<=0),('NHC_lt_NHSA',lambda q:q<0)):
        first=next(x for x in levels if test(Fraction(x['minimum_possible_NHC_minus_NHSA']['exact'])))
        result[name]={'minimum_units':first['budget_at_most'],'example':first['example']}
    equality=[]
    for q in hbyq.keys() & cbyq.keys():
        kh,nh=hbyq[q];kc,nc=cbyq[q]
        if kh+kc<=budget:equality.append((kh+kc,q,nh,nc))
    assert equality, 'Increase predeclared enumeration bound if exact equality is not yet certified.'
    minimum=min(x[0] for x in equality)
    result['NHC_eq_NHSA']={'minimum_units':minimum,'examples':[pair_example(h,c,nh,nc) for k,q,nh,nc in sorted(equality) if k==minimum]}
    result['lower_bound_certificate']=levels[:result['NHC_le_NHSA']['minimum_units']+1]
    result['enumeration']={'per_department_budget_bound':budget,'NHSA_feasible_states':len(hs),'NHC_feasible_states':len(cs),
       'all_minima_within_bound':all(result[k]['minimum_units']<=budget for k in ('NHC_le_NHSA','NHC_lt_NHSA','NHC_eq_NHSA'))}
    result['proof']=[
       'For fixed original and target four-cell counts, minimum changed-unit cost is sum positive cell-count differences = half the L1 distance. Every excess unit can move directly to a deficit cell, with either or both labels changed once. This proves necessity and attainability.',
       'The three explicit deltas and the fourth minus their sum enumerate every target table with cost <=20, nonnegative cells, constant department N and a strictly positive Ec denominator.',
       'For any allocation of an at-most-k budget, the smallest possible difference is min(NHC rate at its cost) minus max(NHSA rate at its cost). Every allocation is enumerated. Positive exact gaps for all budgets below the reported threshold prove the global lower bound; the explicit target tables attain it.',
       'Equality is checked separately by intersecting exact rational rates and adding their minimum attainable department costs. Because the resulting minimum is <=20, every potentially cheaper table was included; the equality minimum is global too.'
    ]
    return result

def main():
    assert not (OUT/'independent-reversal-threshold-results.json').exists(), 'No overwrite of prior results'
    cfg=obj({'path':str(ADOPTION),'sha256':ADOPTION_SHA})
    assert cfg['status']=='root_confirmed_complete_method_adoption' and cfg['root_adopted_methods_confirmed'] is True
    reference=obj(cfg['reference_manifest']);source=rows(reference['material']['rule_inputs'])
    metadata=obj(reference['metadata']);byfile={Path(x['original_file']).stem:x['analysis_group'] for x in metadata['rows']}
    assert len(byfile)==len(metadata['rows'])
    group={rid:byfile[x['input']['original_file_stem']] for rid,x in source.items()}
    assert Counter(group.values())==Counter(NMPA=1848,NHSA=2100,NHC=533,GOV=443)
    results={}
    for role in ('rules','LLM'):
        predictions=rows(cfg['methods'][role]['output']);assert set(predictions)==set(source)
        counters={g:Counter() for g in ('NHSA','NHC')}
        for rid,x in predictions.items():
            if role=='rules':assert x['original_id']==source[rid]['original_id']
            else:assert x.get('original_id',rid)==rid
            lab=x.get('prediction',x)['labels'];assert set(lab)=={'S','E','Ec','I','F'}
            assert all(type(v) is int and v in (0,1) for v in lab.values())
            if group[rid] in counters:counters[group[rid]][(lab['Ec'],lab['F'])]+=1
        h=tuple(counters['NHSA'][key] for key in LABELS);c=tuple(counters['NHC'][key] for key in LABELS)
        assert sum(h)==2100 and sum(c)==533
        results[role]={'adopted_method_id':cfg['methods'][role]['method_id'],
          'observed':{'NHSA':dict(zip(CELLS,h)),'NHC':dict(zip(CELLS,c)),
                      'P_F_given_Ec':{'NHSA':frac(rate(h)),'NHC':frac(rate(c))},'unit_N':{'NHSA':2100,'NHC':533}},
          'fixed_Ec_F_flips':fixed_ec(h,c),'Ec_and_F_unit_cost':both_dimensions(h,c)}
    for b in BOUND.values():assert digest(b['path'])==b['sha256']
    report={'status':'EXACT_ENUMERATION_AND_ATTAINABLE_WITNESS_PASS', 'independent_implementation':True,
      'scope':'Two actual adopted methods, NHSA vs NHC full-corpus descriptive P(F|Ec); no future-human data, relabeling, model calls, bootstrap or significance screening.',
      'cost_definition':'Number of changed text units, pooled across the two departments. In the second case a unit may change Ec and F simultaneously at cost one.',
      'interpretation_limit':'Worst-case adversarial label-change robustness only. These minima are not observed error rates, confidence intervals, validation, causal effects, or probabilities that the finding is wrong. Directional choices do not identify which real units are misclassified.',
      'input_bindings':list(BOUND.values()),'script':{'path':str(Path(__file__).resolve()),'sha256':digest(__file__)},'methods':results}
    result=OUT/'independent-reversal-threshold-results.json';result.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    lines=['# 条件比例结论的最小改标反转阈值（独立精确计算）','','目标为使卫健 P(F|Ec) ≤ 医保。分母要求非零；所有改变仅为假设，不修改任何原标签。','',
      '|采用方法|医保原比例|卫健原比例|固定Ec：最少F翻转|Ec/F均可变：最少改变单元|阈值处结果|','|---|---:|---:|---:|---:|---|']
    for role,z in results.items():
        a=z['fixed_Ec_F_flips']['NHC_le_NHSA'];b=z['Ec_and_F_unit_cost']['NHC_le_NHSA'];example=b['example']
        lines.append(f"|{z['adopted_method_id']}|{z['observed']['P_F_given_Ec']['NHSA']['exact']}|{z['observed']['P_F_given_Ec']['NHC']['exact']}|{a['minimum_units']}|{b['minimum_units']}|卫健 {example['NHC']['F_given_Ec']['exact']} < 医保 {example['NHSA']['F_given_Ec']['exact']}|")
    lines+=['','四格顺序：Ec=1,F=1；Ec=1,F=0；Ec=0,F=1；Ec=0,F=0。']
    for role,z in results.items():
        lines += ['',f"## {z['adopted_method_id']}",'',f"原始四格：医保 {list(z['observed']['NHSA'].values())}，卫健 {list(z['observed']['NHC'].values())}。"]
        b=z['Ec_and_F_unit_cost'];cert=b['lower_bound_certificate'][-2]
        lines += [f"在最多 {cert['budget_at_most']} 个单元改变时，遍历所有合法四格后的最小差（卫健−医保）仍为 {cert['minimum_possible_NHC_minus_NHSA']['exact']} > 0。因此更少改变无法消除原方向。",
          f"严格反转最小数：固定Ec为 {z['fixed_Ec_F_flips']['NHC_lt_NHSA']['minimum_units']}，两标签可变为 {b['NHC_lt_NHSA']['minimum_units']}。精确等号另行计算：固定Ec为 {z['fixed_Ec_F_flips']['NHC_eq_NHSA']['minimum_units']}，两标签可变为 {b['NHC_eq_NHSA']['minimum_units']}；不把严格反转与等号混写。",
          '完整可达改标搬移例、等号例和逐预算下界证书均在同名 JSON。']
    lines+=['','最小性依据：任一四格改变的最低单元成本为四格差值正部之和，即半 L1 距离；从盈余格向不足格逐个搬移即可达到。每部门完整枚举成本≤20的合法目标四格，再遍历部门间预算分配与精确有理数比较。Ec/F均可变情形所报最小值均位于20单元枚举范围内；固定Ec情形另已遍历两个部门全部可能分子，不受20单元界限约束。因此各自更低成本均已全部排除。','','这是对假设最不利改标的描述性敏感性分析，不是实际错误率、置信区间、效度证明或错误发生概率，也不意味着这些具体真实单元应被重编码。']
    (OUT/'independent-reversal-threshold-results.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({role:{'fixed':z['fixed_Ec_F_flips']['NHC_le_NHSA']['minimum_units'],'both':z['Ec_and_F_unit_cost']['NHC_le_NHSA']['minimum_units'],'tie_fixed':z['fixed_Ec_F_flips']['NHC_eq_NHSA']['minimum_units'],'tie_both':z['Ec_and_F_unit_cost']['NHC_eq_NHSA']['minimum_units']} for role,z in results.items()}))

if __name__=='__main__':main()
