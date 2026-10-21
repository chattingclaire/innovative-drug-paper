"""Transparent statistics for the new AI-agent reference exercise; never edit labels."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import numpy as np

ROOT=Path('/PROJECT_ROOT')
RUN=ROOT/'outputs/agent-validation-20261007-r2'
OUT=RUN/'statistics'
OLD=ROOT/'outputs/recall-revision-20261007'
DIMS=('S','E','Ec','I','F')
GROUPS=('NMPA','NHSA','NHC')
B=5000
BASE_SEED=2026100721
EXPECTED_ELIGIBLE={'NMPA':1147,'NHSA':1575,'NHC':240}
METRIC_NAMES=('kappa','agreement','precision','recall','f1','left_positive_rate','right_positive_rate')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def jsonl(path):
    rows=[json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    result={r['id']:r for r in rows}
    assert len(result)==len(rows),path
    return result
def write_json(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def seed(*parts):return (BASE_SEED+int(hashlib.sha256('/'.join(map(str,parts)).encode()).hexdigest()[:8],16))%2**32
def safe(value):return float(value) if np.isfinite(value) else None
def binary(value):return type(value) is int and value in (0,1)
def label(row,dim):return row.get('prediction',row)['labels'][dim]

def load_context():
    design_path=RUN/'admin/sampling_design.json'
    design=read(design_path);sample={r['original_id']:r for r in design['sample']}
    assert len(sample)==300 and design['eligible_by_group']==EXPECTED_ELIGIBLE
    assert not set(sample)&set(design['excluded_ids'])
    assert Counter((r['component'],r['group']) for r in sample.values())==Counter({(c,g):n for c,n in [('probability_base',80),('enriched_challenge',20)] for g in GROUPS})
    rule_inputs=jsonl(RUN/'rule_inputs_shared_v6.jsonl');llm_inputs=jsonl(RUN/'effective_blind_inputs_v6.jsonl')
    assert len(rule_inputs)==len(llm_inputs)==4924 and set(rule_inputs)==set(llm_inputs)
    metadata_path=Path(read(OLD/'三部门注意力分布与敏感性.json')['method_bindings']['metadata'])
    meta={Path(r['original_file']).stem:r for r in read(metadata_path)['rows']}
    groups={rid:meta[r['input']['original_file_stem']]['analysis_group'] for rid,r in rule_inputs.items()}
    sources={rid:r['input'].get('unit_source',r['input']['source']) for rid,r in rule_inputs.items()}
    for rid,r in rule_inputs.items():
        assert r['input']['unit_text']==llm_inputs[rid]['text']
        assert r['input']['llm_v29_shared_context']==llm_inputs[rid]['contexts']
    assert Counter(groups.values())==Counter({'NMPA':1848,'NHSA':2100,'NHC':533,'GOV':443})
    for rid,r in sample.items():
        assert r['group']==groups[rid]
        if r['component']=='probability_base':
            assert r['eligible_N']==EXPECTED_ELIGIBLE[r['group']] and r['sample_n']==80
            assert abs(r['analysis_weight']-r['eligible_N']/80)<1e-12
            assert abs(r['inclusion_probability']-80/r['eligible_N'])<1e-12
        else:assert r['analysis_weight'] is None
    return {'design':design,'sample':sample,'inputs':rule_inputs,'llm_inputs':llm_inputs,'groups':groups,'sources':sources,'metadata':meta,
        'source_paths':[design_path,RUN/'rule_inputs_shared_v6.jsonl',RUN/'effective_blind_inputs_v6.jsonl',metadata_path,Path(__file__)]}

def cells(left,right,dim,ids):
    valid=np.asarray([binary(label(left[rid],dim)) and binary(label(right[rid],dim)) for rid in ids])
    a=np.asarray([label(left[rid],dim) if binary(label(left[rid],dim)) else -1 for rid in ids])
    c=np.asarray([label(right[rid],dim) if binary(label(right[rid],dim)) else -1 for rid in ids])
    # Order TP,A1/C0,A0/C1,TN; symmetric for A/C.
    matrix=np.stack([valid&(a==1)&(c==1),valid&(a==1)&(c==0),valid&(a==0)&(c==1),valid&(a==0)&(c==0)],axis=1).astype(float)
    return matrix,valid

def metrics(counts):
    counts=np.asarray(counts,dtype=float)
    if counts.ndim==1:counts=counts[None,:]
    tp,fp,fn,tn=counts.T;n=counts.sum(axis=1)
    def ratio(a,b):return np.divide(a,b,out=np.full_like(a,np.nan,dtype=float),where=b>1e-12)
    agree=ratio(tp+tn,n);lp=ratio(tp+fp,n);rp=ratio(tp+fn,n)
    pe=lp*rp+(1-lp)*(1-rp)
    kappa=ratio(agree-pe,1-pe)
    return np.stack([kappa,agree,ratio(tp,tp+fp),ratio(tp,tp+fn),ratio(2*tp,2*tp+fp+fn),lp,rp],axis=1)

def interval(values):
    values=np.asarray(values,dtype=float);finite=values[np.isfinite(values)]
    return {'low':safe(np.quantile(finite,.025)) if len(finite) else None,
            'high':safe(np.quantile(finite,.975)) if len(finite) else None,
            'defined_repetitions':len(finite),'undefined_repetitions':len(values)-len(finite)}

def replicate_factors(ctx,ids,component,mechanism):
    """Factors shared by all labels/methods: preserve pairing and sampling strata."""
    rng=np.random.default_rng(seed(component,mechanism,'/'.join(ids)))
    result=np.zeros((B,len(ids)))
    for group in GROUPS:
        positions=[i for i,rid in enumerate(ids) if ctx['sample'][rid]['group']==group]
        if not positions:continue
        n=len(positions)
        if mechanism=='department_unit_rescaled_SRSWOR':
            assert component=='probability_base' and n==80
            f=n/EXPECTED_ELIGIBLE[group];m=n-1
            multiplicities=rng.multinomial(m,np.repeat(1/n,n),size=B)
            factors=1+np.sqrt(1-f)*((n/m)*multiplicities-1)
            assert factors.min()>=0 and np.allclose(factors.sum(axis=1),n,atol=1e-11)
        elif mechanism=='department_unit_conditional_WR':
            factors=rng.multinomial(n,np.repeat(1/n,n),size=B)
        elif mechanism=='department_source_file_conditional_WR':
            clusters=sorted({ctx['sources'][ids[i]] for i in positions});k=len(clusters)
            drawn=rng.multinomial(k,np.repeat(1/k,k),size=B)
            lookup={source:j for j,source in enumerate(clusters)}
            factors=np.stack([drawn[:,lookup[ctx['sources'][ids[i]]]] for i in positions],axis=1)
        else:raise ValueError(mechanism)
        result[:,positions]=factors
    assert np.isfinite(result).all() and result.min()>=0
    return result

def weighting(ctx,ids,kind):
    if kind=='unweighted':return np.ones(len(ids))
    assert kind=='eligible_design_weighted'
    return np.asarray([ctx['sample'][rid]['analysis_weight'] for rid in ids])

def comparison(ctx,left,right,dim,ids,component,group,kind,method,reference,factor_cache):
    matrix,valid=cells(left,right,dim,ids);w=weighting(ctx,ids,kind)
    raw=matrix.sum(axis=0).astype(int);weighted=w@matrix;point=metrics(weighted)[0]
    ids_valid=[rid for rid,v in zip(ids,valid) if v]
    primary='department_unit_rescaled_SRSWOR' if component=='probability_base' else 'department_unit_conditional_WR'
    intervals={}
    for mechanism in (primary,'department_source_file_conditional_WR'):
        cache_key=(component,group,mechanism,tuple(ids))
        if cache_key not in factor_cache:factor_cache[cache_key]=replicate_factors(ctx,ids,component,mechanism)
        factors=factor_cache[cache_key];boot=metrics((factors*w)@matrix)
        intervals[mechanism]={name:interval(boot[:,j]) for j,name in enumerate(METRIC_NAMES)}
    names=('kappa','agreement','left_positive_rate','right_positive_rate') if method=='A_C' else METRIC_NAMES
    return {'component':component,'group':group,'weighting':kind,'method':method,'reference':reference,'dimension':dim,
        'unit_frame_n':len(ids),'paired_n':int(valid.sum()),'excluded_pending_n':int((~valid).sum()),
        'paired_ids':ids_valid,'excluded_ids':[rid for rid,v in zip(ids,valid) if not v],
        'left_positive_n':int(raw[0]+raw[1]),'reference_positive_n':int(raw[0]+raw[2]),
        'raw_confusion':dict(zip(('TP','FP','FN','TN'),map(int,raw))),
        'weighted_confusion':dict(zip(('TP','FP','FN','TN'),map(float,weighted))),
        'source_file_clusters_by_department':{g:len({ctx['sources'][rid] for rid in ids if ctx['sample'][rid]['group']==g}) for g in GROUPS},
        'metrics':{name:{'estimate':safe(point[METRIC_NAMES.index(name)]),
            'ci95_primary':intervals[primary][name],
            'ci95_source_file_conditional_sensitivity':intervals['department_source_file_conditional_WR'][name]} for name in names},
        'primary_bootstrap_mechanism':primary,
        'point_0_80_diagnostics':{name:('undefined' if not np.isfinite(point[METRIC_NAMES.index(name)]) else 'at_least_0_80' if point[METRIC_NAMES.index(name)]>=.8 else 'below_0_80') for name in (('kappa',) if method=='A_C' else ('kappa','precision','recall','f1'))}}

def groups_and_weights(component):
    values=[('ALL','unweighted')]+[(g,'unweighted') for g in GROUPS]
    if component=='probability_base':values.append(('ALL','eligible_design_weighted'))
    return values

def analysis_notes():
    return {'references':'New independent expert AI-agent A/C submissions; no completed real-human coding or human adjudication.',
        'probability_scope':'240 department-stratified unit SRSWOR cases represent only development-excluded eligible frame NMPA1147/NHSA1575/NHC240, not all4481.',
        'challenge_scope':'60 enriched cases are conditional diagnostic challenge performance; never pooled into prevalence or population estimates.',
        'unweighted_ALL':'Equal allocation across departments yields a sample mixture, not eligible-frame population prevalence. Eligible-design-weighted ALL is separately identified.',
        'unit_rescaled_formula':'For each department h: n_h=80, f_h=n_h/N_h, m_h=n_h-1; M_h*~Multinomial(m_h;1/n_h,...,1/n_h); a_hi*=1+sqrt(1-f_h)*[(n_h/m_h)M_hi*-1]. Replicate weight is a_hi* times the relevant base weight (1 or N_h/n_h).',
        'unit_rescaled_properties':'All factors nonnegative and within-department factor sums equal n_h. The replicate variance of a linear total matches the SRSWOR finite-population variance algebraically. Percentile intervals for nonlinear kappa/P/R/F1/ratio statistics are approximations, not exact finite-sample confidence coverage.',
        'source_file_sensitivity':'Independently within department, resample the observed sampled source-file clusters with replacement and retain all sampled units in selected files. This conditions on the sample and is NOT the unit-SRSWOR sampling design, nor a complete design-based measurement-error interval.',
        'uncertainty_scope':'All intervals condition on fixed completed agent labels and fixed model/version/material. They do not measure unobserved semantic truth, annotator-selection uncertainty, development selection, or error outside the eligible frame. Rare classes, perfect sample agreement and few files can give degenerate/unstable intervals.',
        'undefined_policy':'Zero denominator is NA/undefined, never replaced by1. Kappa is undefined when expected agreement=1 even if raw agreement=1.',
        'threshold_role':'0.80 is a work-target diagnostic only, not a universal publication criterion or post-hoc equivalence margin.',
        'replications':B,'base_seed':BASE_SEED,
        'method_references':[{'title':'svrep: Rao-Wu-Yue-Beaumont bootstrap weights, single-stage SRSWOR special case','url':'https://bschneidr.github.io/svrep/reference/make_rwyb_bootstrap_weights.html'},
            {'title':'Official svrep implementation, SRSWOR adjustment factor','url':'https://github.com/bschneidr/svrep/blob/main/R/make_bootstrap_weights.R'},
            {'title':'Beaumont and Emond (2022), original method publication; publisher access rate-limited during this check; formula verified against official implementation','url':'https://doi.org/10.3390/stats5020019'}]}
