"""Restore the original five-dimension attention-share estimand.

Transforms the pre-existing fixed 580-parameter simultaneous count region.
Never uses the old fixed-denominator difference intervals as share intervals.
Input labels and original inference files are read only.
"""
from pathlib import Path
from itertools import combinations
from fractions import Fraction
import json, hashlib

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'outputs/validation-expansion-20260926/D668-原4924范围主统计.json'
DIMS=('S','E','Ec','I','F')
GROUPS=('NMPA','NHSA','NHC','GOV')

def region_ratio(lower,upper,dim):
    # If total=0 the composition is undefined. On the subset total>0,
    # a zero candidate denominator at the lower/upper corner gives 1/0.
    dl=lower[dim]+sum(upper[d] for d in DIMS if d!=dim)
    du=upper[dim]+sum(lower[d] for d in DIMS if d!=dim)
    if sum(upper.values())==0:
        return {'defined':False,'lower':None,'upper':None}
    lo=Fraction(lower[dim],dl) if dl else Fraction(1)
    hi=Fraction(upper[dim],du) if du else Fraction(0)
    return {'defined':True,'lower':float(lo),'upper':float(hi),
            'exact_lower':[lo.numerator,lo.denominator],
            'exact_upper':[hi.numerator,hi.denominator],
            'total_strictly_positive_certified':sum(lower.values())>0}

def sign_region(low,high):
    return 1 if low>0 else -1 if high<0 else 0

def main():
    data=json.loads(SOURCE.read_text())['statistics']
    assert data['metadata']['family_size']==580
    by_status={(r['coder'],r['department'],r['dimension'],r['measure']):r
        for r in data['department_status_estimates']}
    by_potential={(r['coder'],r['department'],r['dimension']):r
        for r in data['department_potential_positive_estimates']}
    rows=[]
    for coder in ('A','C'):
        for group in GROUPS:
            counts={d:by_status[coder,group,d,'1']['ht_total'] for d in DIMS}
            pending={d:by_status[coder,group,d,'pending']['ht_total'] for d in DIMS}
            lower={d:by_status[coder,group,d,'1']['simultaneous_confidence_interval']['population_total_lower'] for d in DIMS}
            upper_known={d:by_status[coder,group,d,'1']['simultaneous_confidence_interval']['population_total_upper'] for d in DIMS}
            upper_completed={d:by_potential[coder,group,d]['simultaneous_confidence_interval']['population_total_upper'] for d in DIMS}
            total=sum(counts.values())
            for dim in DIMS:
                lo=counts[dim]/(counts[dim]+sum(counts[d]+pending[d] for d in DIMS if d!=dim))
                hi=(counts[dim]+pending[dim])/(total+pending[dim])
                rows.append({'coder':coder,'group':group,'dimension':dim,
                    'weighted_coded_count':counts[dim],'weighted_pending_count':pending[dim],
                    'weighted_five_dimension_count':total,
                    'attention_share':counts[dim]/total,
                    'pending_completion_descriptive_range':[lo,hi],
                    'known_count_simultaneous_share_region':region_ratio(lower,upper_known,dim),
                    'completed_count_simultaneous_share_region':region_ratio(lower,upper_completed,dim)})
    idx={(r['coder'],r['group'],r['dimension']):r for r in rows}
    comparisons=[]
    common=[]
    for g1,g2 in combinations(GROUPS,2):
        for dim in DIMS:
            directions={}
            for coder in ('A','C'):
                a,b=idx[coder,g1,dim],idx[coder,g2,dim]
                result={'coder':coder,'pair':[g1,g2],'dimension':dim,
                    'share_difference_point':a['attention_share']-b['attention_share']}
                for label,key in [('known','known_count_simultaneous_share_region'),('completed','completed_count_simultaneous_share_region')]:
                    al,au=Fraction(*a[key]['exact_lower']),Fraction(*a[key]['exact_upper'])
                    bl,bu=Fraction(*b[key]['exact_lower']),Fraction(*b[key]['exact_upper'])
                    lo,hi=al-bu,au-bl
                    result[label+'_simultaneous_difference_region']={
                        'lower':float(lo),'upper':float(hi),'direction':sign_region(lo,hi),
                        'exact_lower':[lo.numerator,lo.denominator],
                        'exact_upper':[hi.numerator,hi.denominator]}
                directions[coder]=result['completed_simultaneous_difference_region']['direction']
                comparisons.append(result)
            common.append({'pair':[g1,g2],'dimension':dim,'coder_directions':directions,
                'common_direction':directions['A'] if directions['A']==directions['C'] else 0})
    within=[]
    for group in GROUPS:
        for d1,d2 in combinations(DIMS,2):
            ds={}
            for coder in ('A','C'):
                a=by_status[coder,group,d1,'1']['simultaneous_confidence_interval']['population_total_lower']
                b=by_potential[coder,group,d2]['simultaneous_confidence_interval']['population_total_upper']
                c=by_potential[coder,group,d1]['simultaneous_confidence_interval']['population_total_upper']
                d=by_status[coder,group,d2,'1']['simultaneous_confidence_interval']['population_total_lower']
                ds[coder]=sign_region(a-b,c-d)
            within.append({'group':group,'dimension_pair':[d1,d2],'coder_directions':ds,
                'common_direction':ds['A'] if ds['A']==ds['C'] else 0})
    overall=[]
    for coder in ('A','C'):
        counts={d:sum(idx[coder,g,d]['weighted_coded_count'] for g in GROUPS) for d in DIMS}
        for dim in DIMS:overall.append({'coder':coder,'dimension':dim,
            'weighted_coded_count':counts[dim],'weighted_five_dimension_count':sum(counts.values()),
            'attention_share':counts[dim]/sum(counts.values())})
    out={'estimand':'attention_share = dimension coded occurrences / sum of five dimension coded occurrences',
        'definition_provenance':'original manuscript 6 paragraph 46; restored on 2026-10-07',
        'source_path':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'method':'monotone transformations of the original fixed 580-parameter count simultaneous region',
        'source_labels_modified':False,'rows':rows,'overall':overall,
        'department_comparisons':comparisons,'common_department_directions':common,
        'within_department_dimension_comparisons':within,
        'summary':{'known_single_coder_directions':sum(r['known_simultaneous_difference_region']['direction']!=0 for r in comparisons),
                   'completed_single_coder_directions':sum(r['completed_simultaneous_difference_region']['direction']!=0 for r in comparisons),
                   'common_department_directions':sum(r['common_direction']!=0 for r in common),
                   'common_within_department_directions':sum(r['common_direction']!=0 for r in within)},
        'limits':['AI agent reference, not actual human validation','Point shares use recorded coded-as-1 occurrences; pending unresolved counts remain separate',
                  'Pending completion and sampling uncertainty are propagated through the ratio denominator',
                  'Existing fixed-unit denominator difference intervals are not reused for attention-share inference',
                  'Coverage is conditional on the original finite-frame sampling design and fixed reference functions',
                  'Source occurrence counts have no interpretation as actual review weights or causal effects']}
    for coder in ('A','C'):
        for group in GROUPS:
            assert abs(sum(idx[coder,group,d]['attention_share'] for d in DIMS)-1)<1e-12
            for d in DIMS:
                row=idx[coder,group,d]
                for key in ('known_count_simultaneous_share_region','completed_count_simultaneous_share_region'):
                    ci=row[key];assert 0<=ci['lower']<=row['attention_share']<=ci['upper']<=1
    (OUT/'attention_share_bounds.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out['summary'],ensure_ascii=False))
    for coder in ('A','C'):
        for group in GROUPS:print(coder,group,[round(100*idx[coder,group,d]['attention_share'],2) for d in DIMS])

if __name__=='__main__':main()
