"""Independent rational point estimates and alternative algebra for all intervals."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
from itertools import combinations
import argparse,datetime,hashlib,json
import numpy as np

P=Path(__file__).resolve().parent;RUN=P.parent
DIMS=('S','E','Ec','I','F');GROUPS=('NMPA','NHSA','NHC');B=5000;BASE=2026100721
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def rows(p):return {r['id']:r for r in map(json.loads,Path(p).read_text().splitlines())}
def val(row,d):return row.get('prediction',row)['labels'][d]
def valid(v):return type(v)is int and v in (0,1)
def close(a,b,tol=1e-10):
    assert a is None if b is None else a is not None and abs(a-b)<tol,(a,b)
def point(v):
    tp,fp,fn,tn=v;n=sum(v);div=lambda a,b:float(a/b) if b else None
    pe=(tp+fp)*(tp+fn)+(tn+fn)*(tn+fp)
    return {'kappa':div(n*(tp+tn)-pe,n*n-pe),'agreement':div(tp+tn,n),'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'f1':div(2*tp,2*tp+fp+fn),'left_positive_rate':div(tp+fp,n),'right_positive_rate':div(tp+fn,n)}
def arrays(v):
    tp,fp,fn,tn=v.T;n=v.sum(axis=1)
    def div(a,b):return np.divide(a,b,out=np.full_like(a,np.nan),where=np.abs(b)>1e-10)
    pe=(tp+fp)*(tp+fn)+(tn+fn)*(tn+fp)
    return {'kappa':div(n*(tp+tn)-pe,n*n-pe),'agreement':div(tp+tn,n),'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'f1':div(2*tp,2*tp+fp+fn),'left_positive_rate':div(tp+fp,n),'right_positive_rate':div(tp+fn,n)}
def seed(*parts):return(BASE+int(hashlib.sha256('/'.join(map(str,parts)).encode()).hexdigest()[:8],16))%2**32
def verify_ci(ci,v):
    vv=np.asarray(v);vv=vv[np.isfinite(vv)]
    assert ci['defined_repetitions']==len(vv) and ci['undefined_repetitions']==B-len(vv)
    qs=np.quantile(vv,[.025,.975]) if len(vv) else[None,None]
    close(ci['low'],qs[0]);close(ci['high'],qs[1])

def factors(sample,sources,ids,component,mechanism):
    rng=np.random.default_rng(seed(component,mechanism,'/'.join(ids)));out=np.zeros((B,len(ids)))
    for g in GROUPS:
        ii=[i for i,rid in enumerate(ids) if sample[rid]['group']==g]
        if not ii:continue
        n=len(ii)
        if mechanism=='department_source_file_conditional_WR':
            files=sorted({sources[ids[i]] for i in ii});k=len(files);cnt=rng.multinomial(k,[1/k]*k,size=B)
            for i in ii:out[:,i]=cnt[:,files.index(sources[ids[i]])]
        else:
            m=n-1 if mechanism=='department_unit_rescaled_SRSWOR' else n
            cnt=rng.multinomial(m,[1/n]*n,size=B)
            if mechanism=='department_unit_rescaled_SRSWOR':
                f=n/sample[ids[ii[0]]]['eligible_N'];cnt=1-np.sqrt(1-f)+np.sqrt(1-f)*n/m*cnt
            out[:,ii]=cnt
        assert out[:,ii].min()>=0
    return out

def q_exact(data,ids,weights=None):
    if weights is None:weights=[Fraction(1)]*len(ids)
    counts={d:sum((w*val(data[rid],d) for rid,w in zip(ids,weights)),Fraction()) for d in DIMS}
    total=sum(counts.values());return counts,{d:counts[d]/total if total else None for d in DIMS}
def qvec(v):
    v=np.asarray(v,dtype=float);n=v.sum(axis=1)
    return np.asarray([np.divide(v[:,j],n,out=np.full_like(n,np.nan),where=n>0) for j in range(5)]).T
def rank(q):return None if any(v is None for v in q.values()) else[[d for d in DIMS if q[d]==v] for v in sorted(set(q.values()),reverse=True)]
def verify_q(r,data,ids,weights=None):
    counts,q=q_exact(data,ids,weights)
    assert r['unit_n']==len(ids) and r['rank_tiers']==rank(q)
    for d in DIMS:
        close(r['shares'][d],None if q[d]is None else float(q[d]))
        assert r['exact_share_fractions'][d]==(None if q[d]is None else str(q[d]))
        if 'dimension_hit_counts'in r:close(r['dimension_hit_counts'][d],float(counts[d]))
    if 'five_dimension_hit_denominator'in r:close(r['five_dimension_hit_denominator'],float(sum(counts.values())))
    return q

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['rule_only','final'],required=True);args=p.parse_args()
    stem='最终机器参照比较' if args.stage=='final' else '规则已完成阶段参照比较'
    cpath=P/(stem+'.json');report=read(cpath);sample={r['original_id']:r for r in read(RUN/'admin/sampling_design.json')['sample']}
    inputs=rows(RUN/'rule_inputs_shared_v6.jsonl');sources={rid:r['input'].get('unit_source',r['input']['source']) for rid,r in inputs.items()}
    data={name:rows(binding['path']) for name,binding in report['method_bindings'].items()}
    refs={c:rows(RUN/f'reference/agent_{c}_final_v8.jsonl') for c in('A','C')};refs['third_agent_candidate']=rows(P/'adjudicated_agent_reference_candidate_v8.jsonl')
    source_hashes={**report['source_sha256'],str(cpath):sha(cpath),str(Path(__file__)):sha(__file__)}
    assert all(sha(p)==s for p,s in source_hashes.items())
    cache={};checked=0;ci_checked=0;undefined=0;below=0
    for r in report['records']:
        ids=[rid for rid,s in sample.items() if s['component']==r['component'] and(r['group']=='ALL'or s['group']==r['group'])]
        left,right=data[r['method']],refs[r['reference']];d=r['dimension']
        raw=np.asarray([[int((val(left[rid],d),val(right[rid],d))==pair) for pair in((1,1),(1,0),(0,1),(0,0))] for rid in ids],dtype=float)
        assert all(valid(val(left[rid],d))and valid(val(right[rid],d)) for rid in ids)
        weights=[Fraction(1)if r['weighting']=='unweighted'else Fraction(sample[rid]['eligible_N'],80)for rid in ids]
        exact=[sum((weights[i]*int(raw[i,j]) for i in range(len(ids))),Fraction())for j in range(4)]
        assert r['raw_confusion']==dict(zip(('TP','FP','FN','TN'),map(int,raw.sum(axis=0))))
        assert r['paired_n']==r['unit_frame_n']==len(ids)and r['excluded_pending_n']==0 and r['paired_ids']==ids
        assert r['left_positive_n']==sum(val(left[rid],d)for rid in ids)and r['reference_positive_n']==sum(val(right[rid],d)for rid in ids)
        est=point(exact)
        for name,m in r['metrics'].items():close(m['estimate'],est[name])
        for name,flag in r['point_0_80_diagnostics'].items():
            expected='undefined'if est[name]is None else'at_least_0_80'if est[name]>=.8 else'below_0_80';assert flag==expected
            undefined+=flag=='undefined';below+=flag=='below_0_80'
        for mechanism,field in[(r['primary_bootstrap_mechanism'],'ci95_primary'),('department_source_file_conditional_WR','ci95_source_file_conditional_sensitivity')]:
            key=(r['component'],r['group'],mechanism,tuple(ids))
            if key not in cache:cache[key]=factors(sample,sources,ids,r['component'],mechanism)
            boot=arrays((cache[key]*np.array(list(map(float,weights))))@raw)
            for name,m in r['metrics'].items():verify_ci(m[field],boot[name]);ci_checked+=1
        checked+=1
    attention_checked=0;attention_CIs=0;robust_checked=0
    if args.stage=='final':
        apath=P/'最终五维注意力与配对差值.json';a=read(apath);source_hashes.update(a['source_sha256']);source_hashes[str(apath)]=sha(apath)
        assert all(sha(p)==s for p,s in source_hashes.items())
        meta_path=next(p for p in a['source_sha256']if p.endswith('classification--部门归属与年度系列-冻结v1.json'))
        meta={Path(r['original_file']).stem:r for r in read(meta_path)['rows']}
        groups={rid:meta[r['input']['original_file_stem']]['analysis_group']for rid,r in inputs.items()}
        for r in a['probability_sample_attention']:
            ids=[rid for rid,s in sample.items()if s['component']=='probability_base'and(r['group']=='ALL'or s['group']==r['group'])]
            weights=[Fraction(1)if r['weighting']=='unweighted'else Fraction(sample[rid]['eligible_N'],80)for rid in ids]
            obj=data.get(r['method'],refs.get(r['method']));verify_q(r,obj,ids,weights)
            v=np.asarray([[val(obj[rid],d)for d in DIMS]for rid in ids]);f=factors(sample,sources,ids,'probability_base','department_unit_rescaled_SRSWOR')
            qb=qvec((f*np.array(list(map(float,weights))))@v)
            for j,d in enumerate(DIMS):verify_ci(r['ci95_approximate_unit_design'][d],qb[:,j]);attention_CIs+=1
            attention_checked+=1
        for method,departments in a['full_4481_attention'].items():
            assert sum(r['unit_n']for r in departments.values())==4481
            for g,r in departments.items():verify_q(r,data[method],[rid for rid in inputs if groups[rid]==g]);attention_checked+=1
        current=[name for name in data if not name.startswith('old_')];assert len(current)==2
        rm=next(m for m in current if m.startswith('rules_'));lm=next(m for m in current if m.startswith('llm_'))
        for g in GROUPS:
            ids=[rid for rid in inputs if groups[rid]==g];files=sorted({sources[rid]for rid in ids});k=len(files)
            rng=np.random.default_rng(seed('full_corpus_paired_source_file',g));multiplicity=rng.multinomial(k,[1/k]*k,size=B)
            bs=[];exact=[]
            for method in(rm,lm):
                vv=np.asarray([[sum(val(data[method][rid],d)for rid in ids if sources[rid]==file)for d in DIMS]for file in files])
                bs.append(qvec(multiplicity@vv));exact.append(q_exact(data[method],ids)[1])
            for j,d in enumerate(DIMS):
                r=next(r for r in a['paired_full_corpus_rule_minus_LLM_difference_CIs']if r['group']==g and r['dimension']==d)
                close(r['rule_minus_LLM_percentage_points'],float((exact[0][d]-exact[1][d])*100))
                verify_ci(r['ci95_paired_difference_percentage_points'],100*(bs[0][:,j]-bs[1][:,j]))
                verify_ci(r['rule_share_ci95_conditional_file'],bs[0][:,j]);verify_ci(r['LLM_share_ci95_conditional_file'],bs[1][:,j]);attention_CIs+=3
                assert r['equivalence_test_performed']is False and r['equivalence_margin_prespecified']is False
        for case in a['robustness']:
            dirs={}
            for method,m in case['methods'].items():
                qby={}
                for g,r in m['departments'].items():
                    ids=[rid for rid in inputs if groups[rid]==g and inputs[rid]['input']['original_file_stem']!=case['omitted_policy_entry']]
                    if case['case']in('policy_file_equal','policy_series_equal'):
                        grouped={}
                        for rid in ids:
                            stem=inputs[rid]['input']['original_file_stem'];key=stem if case['case']=='policy_file_equal'else meta[stem]['policy_series'];grouped.setdefault(key,[]).append(rid)
                        active=[q_exact(data[method],v)[1]for v in grouped.values()if sum(q_exact(data[method],v)[0].values())>0]
                        q={d:sum((row[d]for row in active),Fraction())/len(active)if active else None for d in DIMS}
                        assert r['clusters_total']==len(grouped)and r['clusters_active']==len(active)and r['rank_tiers']==rank(q)
                        for d in DIMS:close(r['shares'][d],None if q[d]is None else float(q[d]));assert r['exact_share_fractions'][d]==(None if q[d]is None else str(q[d]))
                    else:q=verify_q(r,data[method],ids)
                    qby[g]=q;robust_checked+=1
                direction=[]
                for l,rr in combinations(GROUPS,2):
                    for d in DIMS:
                        gap=None if qby[l][d]is None or qby[rr][d]is None else qby[l][d]-qby[rr][d]
                        direction.append(None if gap is None else int(gap>0)-int(gap<0))
                assert [r['sign']for r in m['same_dimension_department_directions']]==direction;dirs[method]=direction
            count=sum(x==y for x,y in zip(dirs[rm],dirs[lm]));assert case['consistent_same_dimension_department_directions_n']==count
        assert len(a['robustness'])==a['robustness_case_n']==54
    assert all(sha(p)==s for p,s in source_hashes.items())
    qa={'status':'passed','checked_at':datetime.datetime.now().astimezone().isoformat(),'stage':args.stage,
        'independence':'No statistical_core, classification-builder or attention-builder imports. Rational point values, alternative kappa algebra and independently reconstructed shared bootstrap multiplicities.',
        'classification_comparisons':checked,'classification_intervals_checked':ci_checked,'undefined_point_work_diagnostics':undefined,'below_0_80_point_work_diagnostics':below,
        'attention_vectors_checked':attention_checked,'attention_intervals_checked':attention_CIs,'robustness_department_vectors_checked':robust_checked,
        'human_validation_completed':False,'intervals_approximate_and_conditional_scope_preserved':True,'source_sha256':source_hashes}
    target=P/('最终统计独立数值QA.json'if args.stage=='final'else'规则阶段独立数值QA.json');target.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items()if k not in('source_sha256','independence')},ensure_ascii=False))

if __name__=='__main__':main()
