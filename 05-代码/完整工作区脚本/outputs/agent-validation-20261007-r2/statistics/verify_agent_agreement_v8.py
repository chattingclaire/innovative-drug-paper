"""Independent raw-count/replicate-interval implementation; imports no builders."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import datetime,hashlib,json
import numpy as np

P=Path(__file__).resolve().parent;RUN=P.parent
DIMS=('S','E','Ec','I','F');GROUPS=('NMPA','NHSA','NHC');B=5000;BASE=2026100721
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def rows(p):return {r['id']:r for r in map(json.loads,Path(p).read_text().splitlines())}
def valid(x):return type(x)is int and x in (0,1)
def estimate(v):
    tp,fp,fn,tn=v;n=sum(v)
    div=lambda a,b:float(a/b) if b else None
    po=div(tp+tn,n);a=div(tp+fp,n);c=div(tp+fn,n)
    pe=(tp+fp)*(tp+fn)+(tn+fn)*(tn+fp)
    return {'kappa':div(n*(tp+tn)-pe,n*n-pe),'agreement':po,'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'f1':div(2*tp,2*tp+fp+fn),'left_positive_rate':a,'right_positive_rate':c}
def vector(v):
    tp,fp,fn,tn=v.T;n=v.sum(axis=1)
    def div(a,b):return np.divide(a,b,out=np.full_like(a,np.nan),where=np.abs(b)>1e-10)
    pe=(tp+fp)*(tp+fn)+(tn+fn)*(tn+fp)
    return {'kappa':div(n*(tp+tn)-pe,n*n-pe),'agreement':div(tp+tn,n),'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'f1':div(2*tp,2*tp+fp+fn),'left_positive_rate':div(tp+fp,n),'right_positive_rate':div(tp+fn,n)}

def main():
    report=read(P/'A_C协商前信度-v8.json');sample={r['original_id']:r for r in read(RUN/'admin/sampling_design.json')['sample']}
    inputs=rows(RUN/'rule_inputs_shared_v6.jsonl');refs={v:{c:rows(RUN/f'reference/agent_{c}_{v}.jsonl') for c in ('A','C')} for v in ('first','final_v6','final_v8')}
    assert report['human_validation_completed'] is False and report['adjudication_used_for_A_C_reliability'] is False
    sources={rid:r['input'].get('unit_source',r['input']['source']) for rid,r in inputs.items()}
    before={k:sha(k) for k in report['source_sha256']};assert before==report['source_sha256']
    records=0;interval_fields=0;degenerate=0;undefined=0;factor_cache={}
    for r in report['records']:
        ids=[rid for rid,s in sample.items() if s['component']==r['component'] and(r['group']=='ALL' or s['group']==r['group'])]
        a,c=refs[r['reference_version']]['A'],refs[r['reference_version']]['C'];d=r['dimension'];raw=[];keep=[]
        for rid in ids:
            av,cv=a[rid]['labels'][d],c[rid]['labels'][d]
            keep.append(valid(av) and valid(cv))
            raw.append([int(valid(av) and valid(cv) and (av,cv)==pair) for pair in ((1,1),(1,0),(0,1),(0,0))])
        raw=np.asarray(raw,dtype=float)
        weights=[Fraction(1) if r['weighting']=='unweighted' else Fraction(sample[rid]['eligible_N'],sample[rid]['sample_n']) for rid in ids]
        exact=[sum((weights[i]*int(raw[i,j]) for i in range(len(ids))),Fraction()) for j in range(4)]
        counts=raw.sum(axis=0).astype(int).tolist();point=estimate(exact)
        assert r['raw_confusion']==dict(zip(('TP','FP','FN','TN'),counts))
        assert r['paired_n']==sum(keep) and r['excluded_pending_n']==len(ids)-sum(keep)
        assert r['paired_ids']==[rid for rid,v in zip(ids,keep) if v]
        for k,v in r['weighted_confusion'].items():assert abs(v-float(exact[('TP','FP','FN','TN').index(k)]))<1e-9
        for name,metric in r['metrics'].items():
            expected=point[name];actual=metric['estimate']
            assert actual is None if expected is None else actual is not None and abs(actual-expected)<1e-12
        for mechanism,ci_field in [(r['primary_bootstrap_mechanism'],'ci95_primary'),('department_source_file_conditional_WR','ci95_source_file_conditional_sensitivity')]:
            key=(r['component'],r['group'],mechanism,tuple(ids))
            if key not in factor_cache:
                material='/'.join((r['component'],mechanism,'/'.join(ids)))
                rng=np.random.default_rng((BASE+int(hashlib.sha256(material.encode()).hexdigest()[:8],16))%2**32)
                factors=np.zeros((B,len(ids)))
                for group in GROUPS:
                    ii=[i for i,rid in enumerate(ids) if sample[rid]['group']==group]
                    if not ii:continue
                    n=len(ii)
                    if mechanism=='department_source_file_conditional_WR':
                        clusters=sorted({sources[ids[i]] for i in ii});m=len(clusters)
                        cnt=rng.multinomial(m,[1/m]*m,size=B)
                        for i in ii:factors[:,i]=cnt[:,clusters.index(sources[ids[i]])]
                    else:
                        m=n-1 if mechanism=='department_unit_rescaled_SRSWOR' else n
                        cnt=rng.multinomial(m,[1/n]*n,size=B)
                        if mechanism=='department_unit_rescaled_SRSWOR':
                            f=n/sample[ids[ii[0]]]['eligible_N']
                            cnt=1-np.sqrt(1-f)+np.sqrt(1-f)*(n/m)*cnt
                        factors[:,ii]=cnt
                        assert np.allclose(cnt.sum(axis=1),n,atol=1e-10)
                assert factors.min()>=0
                factor_cache[key]=factors
            boot=vector((factor_cache[key]*np.array(list(map(float,weights))))@raw)
            for name,metric in r['metrics'].items():
                vals=boot[name];vals=vals[np.isfinite(vals)];ci=metric[ci_field]
                assert ci['defined_repetitions']==len(vals) and ci['undefined_repetitions']==B-len(vals)
                q=np.quantile(vals,[.025,.975]) if len(vals) else [None,None]
                for field,v in zip(('low','high'),q):
                    assert ci[field] is None if v is None else ci[field] is not None and abs(ci[field]-v)<1e-10
                    interval_fields+=1
                if not len(vals):undefined+=1
                elif abs(q[1]-q[0])<1e-12:degenerate+=1
        records+=1
    # Exact covariance check for the linear-total special case, not a nonlinear CI coverage claim.
    variance_checks=[]
    for N in (1147,1575,240):
        n=80;f=n/N;m=n-1;y=np.arange(n,dtype=float)%3;w=N/n
        cov_counts=m*(np.eye(n)/n-np.ones((n,n))/n**2)
        cov_factors=(1-f)*(n/m)**2*cov_counts
        actual=w*w*y@cov_factors@y
        expected=N*N*(1-f)*np.var(y,ddof=1)/n
        assert abs(actual-expected)<1e-8
        variance_checks.append({'N':N,'n':n,'fpc':1-f,'replicate_linear_total_variance':actual,'SRSWOR_linear_total_variance':expected})
    assert before=={k:sha(k) for k in before}
    qa={'status':'passed','checked_at':datetime.datetime.now().astimezone().isoformat(),'independence':'No builder/core imports. Raw four-cell tables and rational-weight point estimates independently derived; all two-mechanism intervals reconstructed using alternative kappa algebra.',
        'records_checked':records,'interval_endpoint_fields_checked':interval_fields,'undefined_intervals':undefined,'degenerate_intervals':degenerate,
        'rescaled_weights_nonnegative_and_department_sums_preserved':True,'exact_linear_total_variance_checks':variance_checks,
        'nonlinear_percentile_intervals_are_approximate_not_exact_coverage':True,'human_validation_completed':False,
        'source_sha256':{**before,str(P/'A_C协商前信度-v8.json'):sha(P/'A_C协商前信度-v8.json'),str(Path(__file__)):sha(__file__)}}
    (P/'A_C协商前信度-v8独立QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items() if k not in ('source_sha256','independence','exact_linear_total_variance_checks')},ensure_ascii=False))

if __name__=='__main__':main()
