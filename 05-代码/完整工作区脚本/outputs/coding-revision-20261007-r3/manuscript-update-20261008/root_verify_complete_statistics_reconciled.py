"""Independent standard-library point/count/scope audit; never alters labels.

No imports from statistics, adapters, or execution profiles. Interval checks
validate coverage/undefined bookkeeping, not a fresh bootstrap computation.
"""
from pathlib import Path
from fractions import Fraction as Q
import argparse, hashlib, json, math

DIMS = ('S', 'E', 'Ec', 'I', 'F')
CELLS = ('TP', 'FP', 'FN', 'TN')

def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bound(b):
    assert sha(b['path']) == b['sha256'], b['path']
    return read(b['path'])
def rows(b):
    assert sha(b['path']) == b['sha256'], b['path']
    data = [json.loads(x) for x in Path(b['path']).read_text().splitlines() if x.strip()]
    result = {x['id']: x for x in data}
    assert len(result) == len(data)
    return result
def label(row, d):
    v = row.get('prediction', row)['labels'][d]
    assert type(v) is int and v in (0, 1)
    return v
def eq(a, b):
    assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a, float(b), rel_tol=1e-10, abs_tol=1e-10)), (a, b)
def metrics(z):
    a, b, c, d = z; n = sum(z)
    div = lambda x, y: x / y if y else None
    den = (a+b)*(b+d)+(a+c)*(c+d)
    return {'kappa': div(2*(a*d-b*c), den), 'agreement': div(a+d, n),
            'precision': div(a, a+b), 'recall': div(a, a+c),
            'f1': div(2*a, 2*a+b+c), 'left_positive_rate': div(a+b, n),
            'right_positive_rate': div(a+c, n)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--stats', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True); args=ap.parse_args()
    assert not args.out.exists(), 'Preserve earlier root audits'
    freeze=read(args.stats/'output_freeze.json')
    assert all(sha(args.stats/n)==h for n,h in freeze['files'].items())
    machine_doc=read(args.stats/'machine_reference_classification.json')
    dev=bound(machine_doc['provenance']['bindings']); ref=bound(dev['reference_manifest'])
    design=bound(ref['sampling_design']); sample={x['original_id']:x for x in design['sample']}
    assert len(sample)==240 and design['frame_N_by_group']=={'NMPA':947,'NHSA':760,'NHC':60}
    references={k:rows(ref['references'][k]) for k in ('A','C')}
    references['candidate']=rows(dev['existing_candidate_reference'])
    methods={k:rows(v['output']) for k,v in dev['methods'].items()}
    assert len(methods)==2 and all(len(x)==4924 for x in methods.values())
    allrows={**references,**methods}
    machine=machine_doc['comparisons']; ac=read(args.stats/'A_C_before_third_agreement.json')['comparisons']
    attention=read(args.stats/'probability_attention_and_paired_department_differences.json')
    assert (len(machine),len(ac),len(attention['profiles']),len(attention['paired_method_differences']),len(attention['department_differences']))==(360,60,40,64,15)
    checked=0
    for row in machine+ac:
        ids=sorted(i for i,x in sample.items() if x['component']==row['component'] and (row['group']=='ALL' or x['group']==row['group']))
        left,right=(references['A'],references['C']) if row['method']=='A_C' else (methods[row['method']],references[row['reference']])
        raw=[0]*4; z=[Q(0)]*4
        for i in ids:
            a,b=label(left[i],row['dimension']),label(right[i],row['dimension'])
            j={(1,1):0,(1,0):1,(0,1):2,(0,0):3}[a,b]
            raw[j]+=1; z[j]+=Q(sample[i]['canonical_frame_N'],60) if row['weighting']=='eligible_design_weighted' else Q(1)
        rk,wk=('symmetric_raw_cells','symmetric_weighted_cells') if row['method']=='A_C' else ('raw_confusion','weighted_confusion')
        keys=('A1_C1','A1_C0','A0_C1','A0_C0') if row['method']=='A_C' else CELLS
        assert [row[rk][k] for k in keys]==raw
        for k,v in zip(keys,z): eq(row[wk][k],v)
        mm=metrics(z)
        for name,v in row['metrics'].items(): eq(v['estimate'],mm[name]); checked+=1
        assert row['paired_n']==len(ids) and row['excluded_pending_n']==0
        if not ids: assert row['absent_stratum'] and row['group']=='NHC' and row['component']=='enriched_challenge'
        else: assert row['paired_ids']==ids
    qlookup={}; attention_checks=0
    for row in attention['profiles']:
        ids=sorted(i for i,x in sample.items() if x['component']=='probability_canonical' and (row['group']=='ALL' or x['group']==row['group']))
        assert row['complete_support_ids']==ids
        counts=[sum((Q(sample[i]['canonical_frame_N'],60) if row['weighting']=='eligible_design_weighted' else Q(1))*label(allrows[row['method']][i],d) for i in ids) for d in DIMS]
        den=sum(counts); q=[v/den if den else None for v in counts]
        if den: assert sum(q)==1
        for d,n,v in zip(DIMS,counts,q):
            eq(row['dimensions'][d]['weighted_known_coding_count'],n); eq(row['dimensions'][d]['attention_share'],v); attention_checks+=2
        qlookup[row['group'],row['weighting'],row['method']]=q
    for row in attention['paired_method_differences']:
        one=qlookup[row['group'],row['weighting'],row['method_one']]; two=qlookup[row['group'],row['weighting'],row['method_two']]
        for d,a,b in zip(DIMS,one,two): eq(row['dimensions'][d]['estimate'],a-b if a is not None and b is not None else None); attention_checks+=1
    for row in attention['department_differences']:
        one=qlookup[row['department_one'],'eligible_design_weighted',row['method']]; two=qlookup[row['department_two'],'eligible_design_weighted',row['method']]
        for d,a,b in zip(DIMS,one,two): eq(row['dimensions'][d]['difference_percentage_points'],100*(a-b) if a is not None and b is not None else None); attention_checks+=1
    intervals=[]
    def walk(x,path=''):
        if isinstance(x,dict):
            if {'low','high','defined_repetitions','undefined_repetitions'}<=set(x):
                n,u=x['defined_repetitions'],x['undefined_repetitions']; a,b=x['low'],x['high']
                assert n+u==(0 if 'not_run_reason' in x else 5000),path
                assert (a is None)==(b is None)==(n==0),path
                assert a is None or a<=b,path
                intervals.append({'path':path,**x})
            else:
                for k,v in x.items():walk(v,path+'/'+str(k))
        elif isinstance(x,list):
            for i,v in enumerate(x):walk(v,path+'/'+str(i))
    walk({'machine':machine,'AC':ac,'attention':attention})
    qa=read(args.stats/'complete_statistics_QA.json')
    assert qa['all_checks_pass'] and qa['interval_audit']['checked_interval_n']==len(intervals)
    result={'status':'PASS_ROOT_INDEPENDENT_STANDARD_LIBRARY_POINT_AND_SCOPE_AUDIT','statistics_freeze':{'path':str((args.stats/'output_freeze.json').resolve()),'sha256':sha(args.stats/'output_freeze.json')},'classification_metric_checks':checked,'attention_count_and_difference_checks':attention_checks,'comparison_counts':{'machine':360,'A_C':60,'attention_profiles':40,'paired_attention':64,'department_attention':15},'interval_bookkeeping_checks':len(intervals),'intervals_with_undefined_repetitions':sum(x['undefined_repetitions']>0 for x in intervals),'interval_scope':'Coverage and NA bookkeeping checked; this script does not independently regenerate bootstrap intervals. Driver separate replication QA retained.','labels_or_inputs_edited':False,'human_validation_completed':False}
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
