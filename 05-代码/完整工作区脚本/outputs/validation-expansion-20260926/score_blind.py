"""Score independent AI development review. Pending is never coerced to zero."""
import json, math, hashlib
from pathlib import Path
from collections import Counter
DIMS=('S','E','Ec','I','F')
PENDING='待定'

def validate(path, ids):
    doc=json.loads(Path(path).read_text())
    if doc.get('protocol_version')!='CAL-5D-20260926-v1.1' or doc.get('protocol_acknowledged') is not True:
        raise ValueError(f'Unacknowledged protocol: {path}')
    idx={}
    for r in doc['rows']:
        k=r['id']
        if k in idx: raise ValueError(f'Duplicate ID: {k}')
        if set(r['labels'])!=set(DIMS): raise ValueError(f'Missing labels: {k}')
        for d in DIMS:
            x=r['labels'][d]
            if isinstance(x,bool) or not ((type(x) is int and x in (0,1)) or x==PENDING):
                raise ValueError(f'Invalid label: {k}/{d}: {x!r}')
            if not r['dimension_reasons'].get(d,'').strip(): raise ValueError(f'Missing reason: {k}/{d}')
        idx[k]=r
    if set(idx)!=set(ids): raise ValueError(f'ID coverage mismatch {path}')
    return doc,idx

def binary_metrics(a,b,weights=None):
    if len(a)!=len(b) or not a: raise ValueError('Nonempty equal-length arrays required')
    if any(type(x) is not int or x not in (0,1) for x in a+b): raise ValueError('Explicit binary arrays required')
    w=[1]*len(a) if weights is None else weights
    if len(w)!=len(a) or any(not math.isfinite(x) or x<=0 for x in w): raise ValueError('Positive finite weights required')
    c={str(i)+str(j):sum(z for x,y,z in zip(a,b,w) if x==i and y==j) for i in (0,1) for j in (0,1)}
    n=sum(w); po=(c['00']+c['11'])/n; pa=(c['10']+c['11'])/n; pb=(c['01']+c['11'])/n
    pe=pa*pb+(1-pa)*(1-pb)
    pos=2*c['11']+c['01']+c['10']; neg=2*c['00']+c['01']+c['10']
    return {'n':len(a),'weight_sum':n,'contingency_A_then_C':c,'agreement':po,
            'kappa':(po-pe)/(1-pe) if pe<1-1e-14 else None,
            'kappa_undefined_reason':'边际退化，期望一致率为1' if pe>=1-1e-14 else None,
            'positive_agreement':2*c['11']/pos if pos else None,
            'negative_agreement':2*c['00']/neg if neg else None,
            'positive_rate_A':pa,'positive_rate_C':pb}

def pair_summary(a,b):
    ids=list(a)
    result={'n':len(ids),'dimensions':{},'disagreements':[], 'binary_conflicts':[], 'one_side_pending':[], 'both_pending':[], 'incomplete_rows':[]}
    full_def=[]
    for k in ids:
        if all(a[k]['labels'][d] in (0,1) and b[k]['labels'][d] in (0,1) for d in DIMS): full_def.append(k)
        else: result['incomplete_rows'].append(k)
        for d in DIMS:
            x,y=a[k]['labels'][d],b[k]['labels'][d]
            if x!=y:
                item={'id':k,'dimension':d,'A':x,'C':y,'A_reason':a[k]['dimension_reasons'][d],'C_reason':b[k]['dimension_reasons'][d]}
                result['disagreements'].append(item)
                result['one_side_pending' if PENDING in (x,y) else 'binary_conflicts'].append(item)
            if x==y==PENDING: result['both_pending'].append({'id':k,'dimension':d})
    for d in DIMS:
        keep=[k for k in ids if a[k]['labels'][d] in (0,1) and b[k]['labels'][d] in (0,1)]
        m=binary_metrics([a[k]['labels'][d] for k in keep],[b[k]['labels'][d] for k in keep]) if keep else None
        result['dimensions'][d]={'metrics_on_both_definite':m,'both_definite_n':len(keep),'definite_coverage':len(keep)/len(ids),
           'pending_A':sum(a[k]['labels'][d]==PENDING for k in ids),'pending_C':sum(b[k]['labels'][d]==PENDING for k in ids),
           'both_pending':sum(a[k]['labels'][d]==b[k]['labels'][d]==PENDING for k in ids)}
    result['full_vector']={'both_definite_n':len(full_def),'same_n':sum(a[k]['labels']==b[k]['labels'] for k in full_def),
        'agreement':sum(a[k]['labels']==b[k]['labels'] for k in full_def)/len(full_def) if full_def else None}
    result['interpretation']='开发样本描述性诊断；不是随机总体推断或正式信效度通过证明。待定另报，不当0；两者皆待定不计实质一致。无裁定不生成参考真值，AI一致不等于正确。'
    result['confidence_intervals']=None
    result['confidence_intervals_reason']='开发例句目的性池及固定配额样本不提供总体概率推断。'
    return result

def self_test():
    x=binary_metrics([0,0,1,1],[0,1,0,1]); assert x['kappa']==0 and x['agreement']==.5
    x=binary_metrics([0,1],[0,1]); assert x['kappa']==1 and x['positive_agreement']==1
    x=binary_metrics([0,0],[0,0]); assert x['kappa'] is None and x['positive_agreement'] is None and x['agreement']==1
    x=binary_metrics([0,1],[1,0]); assert x['kappa']==-1 and x['agreement']==0
    x=binary_metrics([0,1],[0,0],[1,3]); assert x['agreement']==.25 and x['positive_rate_A']==.75
    a={'x':{'labels':{d:PENDING for d in DIMS},'dimension_reasons':{d:'缺信息' for d in DIMS}}}
    s=pair_summary(a,a); assert s['full_vector']['both_definite_n']==0 and s['dimensions']['S']['both_pending']==1
    for aa,bb in [([True],[1]),([None],[0]),([PENDING],[0]),([] ,[])]:
        try: binary_metrics(aa,bb)
        except ValueError: pass
        else: raise AssertionError('Invalid inputs accepted')
    return {'known_tables':'passed','weighted_case':'passed','degenerate_margins':'passed','pending_and_missing':'passed'}

if __name__=='__main__':
    import sys
    out=Path(__file__).parent
    if '--self-test' in sys.argv:
        tests=self_test(); (out/'评分边界验证.json').write_text(json.dumps(tests,ensure_ascii=False,indent=2)); print(tests)
    else:
        packet=json.loads((out/'开发60-共同无答案材料.json').read_text()); ids=[r['id'] for r in packet['rows']]
        da,a=validate(out/'agent-A/result-A.json',ids); dc,c=validate(out/'agent-C/result-C.json',ids)
        result=pair_summary(a,c)
        result['protocol']='CAL-5D-20260926-v1.1'
        result['input_sha256']={f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in ['agent-A/result-A.json','agent-C/result-C.json','开发60-共同无答案材料.json']}
        target=out/'开发60-独立盲评统计.json'
        if target.exists(): raise RuntimeError('Preserve independent submissions and previous analysis; use versioned output')
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
        print(json.dumps({'n':result['n'],'full_vector':result['full_vector'],'disagreements':len(result['disagreements']),'incomplete_rows':result['incomplete_rows']},ensure_ascii=False))
