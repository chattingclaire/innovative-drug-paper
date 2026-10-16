"""Descriptive metrics and document-cluster bootstrap on fixed exposed frames.

Intervals condition on these selected labels and fixed algorithms. They do not
account for code selection or convert these development frames to test data.
"""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
from sklearn.metrics import cohen_kappa_score, precision_recall_fscore_support, accuracy_score

ROOT=Path(__file__).resolve().parent
DIMS=('S','E','Ec','I','F')
METRICS=('kappa','agreement','precision','recall','f1')
B=5000
SEED=20261004

def read(name): return json.loads((ROOT/name).read_text())
def ratio(x,y):
    out=np.full(np.broadcast_shapes(np.shape(x),np.shape(y)),np.nan)
    return np.divide(x,y,out=out,where=np.asarray(y)!=0)

def measures(counts):
    tp,fp,fn,tn=np.moveaxis(np.asarray(counts,dtype=float),-1,0)
    n=tp+fp+fn+tn
    agreement=ratio(tp+tn,n)
    expected=ratio((tp+fp)*(tp+fn)+(fn+tn)*(fp+tn),n*n)
    return np.stack([ratio(agreement-expected,1-expected),agreement,
                     ratio(tp,tp+fp),ratio(tp,tp+fn),ratio(2*tp,2*tp+fp+fn)],axis=-1)

def interval(values):
    finite=values[np.isfinite(values)]
    return {'low':float(np.quantile(finite,.025)) if len(finite) else None,
            'high':float(np.quantile(finite,.975)) if len(finite) else None,
            'defined_repetitions':len(finite),'undefined_repetitions':B-len(finite)}

def main():
    data=read('workbook_data.json'); byid={r['id']:r for r in data['rows']}
    masks=read('comparison_masks.json')
    import sys
    sys.path.insert(0,str(ROOT.parent/'autocode-v25-20260927'))
    from analyze_current_reruns import load_sealed_predictions
    _,llm,_,_=load_sealed_predictions()
    output=[];boot={};pair_records=[]
    for scope in ('H427','current1268'):
        for dim in DIMS:
            for ref in ('A','C','C_for_AC'):
                if ref=='C_for_AC':
                    ids=[r['id'] for r in data['rows'] if r['scope']==scope
                         and type(r['references']['A'][dim]) is int
                         and type(r['references']['C'][dim]) is int]
                    methods=('A_C',)
                else:
                    ids=masks[f'{scope}/{ref}/{dim}'];methods=('rules_v27','rules_v28','llm_unchanged')
                sources=sorted({byid[rid]['source'] for rid in ids}); index={s:i for i,s in enumerate(sources)}
                seed=SEED+int(hashlib.sha256(f'{scope}/{dim}/{ref}'.encode()).hexdigest()[:8],16)
                rng=np.random.default_rng(seed)
                weights=rng.multinomial(len(sources),np.full(len(sources),1/len(sources)),size=B)
                for method in methods:
                    counts=np.zeros((len(sources),4),dtype=int);pairs=[]
                    for rid in ids:
                        row=byid[rid];reference=row['references']['C' if ref=='C_for_AC' else ref][dim]
                        prediction=(row['before'][dim] if method=='rules_v27' else row['after'][dim] if method=='rules_v28'
                                    else llm[rid]['labels'][dim] if method=='llm_unchanged' else row['references']['A'][dim])
                        assert prediction in (0,1) and reference in (0,1)
                        position={(1,1):0,(1,0):1,(0,1):2,(0,0):3}[prediction,reference]
                        counts[index[row['source']],position]+=1;pairs.append((prediction,reference))
                    total=counts.sum(axis=0); point=measures(total);bs=measures(weights@counts)
                    ypred,yref=map(np.array,zip(*pairs))
                    assert abs(float(point[0])-cohen_kappa_score(yref,ypred))<1e-12
                    assert abs(float(point[1])-accuracy_score(yref,ypred))<1e-12
                    prf=precision_recall_fscore_support(yref,ypred,average='binary',zero_division=0)[:3]
                    for got,expected in zip(point[2:],prf):
                        if np.isfinite(got): assert abs(float(got)-expected)<1e-12
                    n=int(total.sum())
                    rec={'scope':scope,'dimension':dim,'method':method,'reference':'A_C' if method=='A_C' else ref,
                         'n':n,'frame_n':427 if scope=='H427' else 1268,
                         'excluded_n':(427 if scope=='H427' else 1268)-n,'source_clusters':len(sources),
                         'reference_positive_n':int(total[0]+total[2]),'prediction_positive_n':int(total[0]+total[1]),
                         'reference_positive_rate':float((total[0]+total[2])/n),
                         'prediction_positive_rate':float((total[0]+total[1])/n),
                         'confusion':dict(zip(('TP','FP','FN','TN'),map(int,total))),
                         'metrics':{name:{'estimate':float(point[j]) if np.isfinite(point[j]) else None,
                                         'ci95':interval(bs[:,j])} for j,name in enumerate(METRICS)
                                    if method!='A_C' or name in ('kappa','agreement')}}
                    if method!='A_C':
                        expected=next(m for m in data['metrics'] if all(m[k]==rec[k] for k in ('scope','dimension','method','reference')))
                        assert rec['confusion']==expected['confusion']
                        for name in ('kappa','precision','recall','f1'): assert abs(rec['metrics'][name]['estimate']-expected[name])<1e-12
                    output.append(rec);boot[scope,dim,ref,method]=(point,bs)
                if ref!='C_for_AC':
                    old,oldb=boot[scope,dim,ref,'rules_v27'];new,newb=boot[scope,dim,ref,'rules_v28']
                    pair_records.append({'scope':scope,'dimension':dim,'reference':ref,
                        'change':'rules_v28 minus rules_v27, paired source-cluster bootstrap',
                        'metrics':{name:{'estimate':float(new[j]-old[j]),'ci95':interval((newb-oldb)[:,j])}
                                   for j,name in enumerate(METRICS)}})
    report={'method':'Nonparametric document-cluster percentile bootstrap; sample all observed source clusters with replacement; retain all sampled units within each selected cluster.',
            'repetitions':B,'base_seed':SEED,'confidence_level':.95,
            'limitations':['Unweighted descriptive estimates conditional on fixed exposed development frames, not population estimates.',
                          'Intervals do not include rule/prompt selection uncertainty or coder systematic error.',
                          'Source document, not broader policy series, is the cluster; dependence across related documents may remain.',
                          'Undefined replicates omitted separately for each metric and counted; sparse positive clusters may give unstable intervals.',
                          'Machine classification scores are relative to unchanged AI A/C, not adjudicated human truth.'],
            'records':output,'paired_changes':pair_records,'independent_sklearn_point_checks':True}
    (ROOT/'extended_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    flat=[]
    for r in output:
        for name,v in r['metrics'].items():
            flat.append({**{k:r[k] for k in ('scope','dimension','method','reference','n','excluded_n','source_clusters','reference_positive_n','prediction_positive_n')},
                         'metric':name,'estimate':v['estimate'],**v['ci95']})
    with (ROOT/'完整指标与95区间.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    print(json.dumps({'comparisons':len(output),'metric_intervals':len(flat),'paired_changes':len(pair_records),
                      'bootstrap_repetitions':B,'sklearn_cross_checks':True}))

if __name__=='__main__':main()
