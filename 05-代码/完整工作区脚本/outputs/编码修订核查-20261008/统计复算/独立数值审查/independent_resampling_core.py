"""Independent fixed-resampling reproduction, not an interval coverage proof."""
import hashlib
import numpy as np

GROUPS=('NMPA','NHSA','NHC')
B=5000
BASE_SEED=2026100731
FRAME={'NMPA':947,'NHSA':760,'NHC':60}
METRICS=('kappa','agreement','precision','recall','f1','left_positive_rate','right_positive_rate')
def fixed_seed(*parts):
    return (BASE_SEED+int(hashlib.sha256('/'.join(map(str,parts)).encode()).hexdigest()[:8],16))%2**32

def resampling_factors(ids,design,material,component,mechanism):
    rng=np.random.default_rng(fixed_seed(component,mechanism,'/'.join(ids)))
    result=np.zeros((B,len(ids)))
    group_records=[]
    for group in GROUPS:
        positions=[i for i,rid in enumerate(ids) if design[rid]['group']==group]
        if not positions:continue
        n=len(positions)
        if mechanism=='department_unit_rescaled_SRSWOR':
            assert component=='probability_canonical' and n==60
            multinomial=rng.multinomial(n-1,np.full(n,1/n),size=B)
            f=1+np.sqrt(1-n/FRAME[group])*(n/(n-1)*multinomial-1)
            assert np.allclose(f.sum(axis=1),n,atol=1e-11) and f.min()>=0
            if group=='NHC':assert np.array_equal(f,np.ones_like(f))
            k=n
        elif mechanism=='department_unit_conditional_WR':
            f=rng.multinomial(n,np.full(n,1/n),size=B);k=n
        elif mechanism=='department_source_file_conditional_WR':
            clusters=sorted({material[ids[i]]['source'] for i in positions});k=len(clusters)
            draws=rng.multinomial(k,np.full(k,1/k),size=B)
            lookup={name:j for j,name in enumerate(clusters)}
            f=np.stack([draws[:,lookup[material[ids[i]]['source']]] for i in positions],axis=1)
        else:raise ValueError(mechanism)
        result[:,positions]=f
        group_records.append({'group':group,'sample_n':n,'resampling_cluster_or_unit_n':k,
         'NHC_primary_factors_fixed_one':group=='NHC' and mechanism=='department_unit_rescaled_SRSWOR'})
    assert np.isfinite(result).all() and (not result.size or result.min()>=0)
    return result,{'replicates':B,'seed':fixed_seed(component,mechanism,'/'.join(ids)),
     'mechanism':mechanism,'department_records':group_records,'pairing_shared_across_labels_and_methods':True}

def vector_metrics(cells):
    z=np.asarray(cells,dtype=float);tp,fp,fn,tn=z.T;n=z.sum(axis=1)
    def div(a,b):return np.divide(a,b,out=np.full_like(a,np.nan,dtype=float),where=b>1e-12)
    pe_num=(tp+fp)*(tp+fn)+(fn+tn)*(fp+tn)
    # Algebraically independent multiplied-through Cohen formula. Relative
    # denominator guard matches the declared NA policy for expected agreement1.
    den=n*n-pe_num
    kappa=np.divide(n*(tp+tn)-pe_num,den,out=np.full_like(n,np.nan),where=(n>1e-12)&(den>1e-12*n*n))
    return dict(zip(METRICS,[kappa,div(tp+tn,n),div(tp,tp+fp),div(tp,tp+fn),
     div(2*tp,2*tp+fp+fn),div(tp+fp,n),div(tp+fn,n)]))

def percentile_interval(vals):
    finite=np.asarray(vals)[np.isfinite(vals)]
    limits=np.quantile(finite,[.025,.975]) if len(finite) else [None,None]
    return {'low':float(limits[0]) if limits[0] is not None else None,
     'high':float(limits[1]) if limits[1] is not None else None,
     'defined_repetitions':len(finite),'undefined_repetitions':len(vals)-len(finite)}

def fixed_comparison_intervals(left,right,dim,ids,weights,factors):
    cells=np.zeros((len(ids),4))
    for i,rid in enumerate(ids):
        x,y=left[rid][dim],right[rid][dim]
        if type(x) is int and type(y) is int and x in (0,1) and y in (0,1):
            cells[i,2*(1-x)+(1-y)]=1
    values=vector_metrics((factors*np.asarray(weights))@cells)
    return {k:percentile_interval(v) for k,v in values.items()}
