"""Prospective metadata/labels-only statistics. No sampling or model inference.

Inputs must be transparent synthetic toys, historical arithmetic, or sealed
project submissions. The engine never labels numeric targets formal acceptance.
Fixed one-stage stratified SRSWOR only; source units are the resampling units.
"""
from __future__ import annotations
from pathlib import Path
from fractions import Fraction
from collections import Counter
import argparse, hashlib, json, math
import numpy as np
from scipy.stats import hypergeom

DIMS=('S','E','Ec','I','F')
METHODS=('A','B','reference','rule','LLM')
STATES=('0','1','null','execution_failure')
COMPARISONS={'A_vs_B':('A','B','agreement'),
             'rule_vs_reference':('rule','reference','classification'),
             'LLM_vs_reference':('LLM','reference','classification')}
TARGET=Fraction(4,5)
FROZEN_DOMAINS=('remaining','exposed')
class DataError(ValueError):pass
def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _number(v):return None if v is None else float(v)
def _ratio(a,b):return a/b if b else None

def exact_metrics(cells):
    """Machine rows/prediction, reference columns: TP,FP,FN,TN.
    For humans: A1B1,A1B0,A0B1,A0B0, without a truth assumption.
    Fraction arithmetic is also used for exact point-target comparisons.
    """
    a,b,c,d=(Fraction(x) for x in cells);N=a+b+c+d
    if not N:return {k:None for k in ('Po','Pe','kappa','Ppos','Pneg','Precision','Recall','F1','Specificity','NPV')}
    po=(a+d)/N;pe=((a+b)*(a+c)+(c+d)*(b+d))/N**2
    return {'Po':po,'Pe':pe,'kappa':_ratio(po-pe,1-pe),
            'Ppos':_ratio(2*a,2*a+b+c),'Pneg':_ratio(2*d,2*d+b+c),
            'Precision':_ratio(a,a+b),'Recall':_ratio(a,a+c),
            'F1':_ratio(2*a,2*a+b+c),'Specificity':_ratio(d,b+d),'NPV':_ratio(d,c+d)}

def vector_metrics(cells):
    c=np.asarray(cells,dtype=float)
    if c.ndim==1:c=c[None,:]
    a,b,fn,d=c.T;N=c.sum(axis=1)
    def div(x,y):
        out=np.full(np.broadcast(x,y).shape,np.nan,dtype=float)
        return np.divide(x,y,out=out,where=np.abs(y)>1e-14)
    po=div(a+d,N);pe=div((a+b)*(a+fn)+(fn+d)*(b+d),N*N)
    return {'Po':po,'Pe':pe,'kappa':div(po-pe,1-pe),
            'Ppos':div(2*a,2*a+b+fn),'Pneg':div(2*d,2*d+b+fn),
            'Precision':div(a,a+b),'Recall':div(a,a+fn),'F1':div(2*a,2*a+b+fn),
            'Specificity':div(d,b+d),'NPV':div(d,fn+d)}

def metric_gradients(cells):
    """Gradients of homogeneous total-cell functions; comparable N can vary."""
    a,b,c,d=np.asarray(cells,dtype=float);N=a+b+c+d
    out={k:None for k in ('Po','Pe','kappa','Ppos','Pneg','Precision','Recall','F1','Specificity','NPV')}
    if N<=0:return out
    po=(a+d)/N;u=(a+b)/N;v=(a+c)/N;pe=u*v+(1-u)*(1-v)
    dpo=(np.array([1.,0.,0.,1.])-po)/N
    du=(np.array([1.,1.,0.,0.])-u)/N;dv=(np.array([1.,0.,1.,0.])-v)/N
    dpe=(2*v-1)*du+(2*u-1)*dv
    out['Po']=dpo;out['Pe']=dpe
    if 1-pe>1e-14:
        k=(po-pe)/(1-pe);out['kappa']=(dpo+(k-1)*dpe)/(1-pe)
    if a+b:out['Precision']=np.array([b,-a,0.,0.])/(a+b)**2
    if a+c:out['Recall']=np.array([c,0.,-a,0.])/(a+c)**2
    if 2*a+b+c:
        out['F1']=out['Ppos']=np.array([2*(b+c),-2*a,-2*a,0.])/(2*a+b+c)**2
    if 2*d+b+c:out['Pneg']=np.array([0.,-2*d,-2*d,2*(b+c)])/(2*d+b+c)**2
    if b+d:out['Specificity']=np.array([0.,-d,0.,b])/(b+d)**2
    if c+d:out['NPV']=np.array([0.,0.,-d,c])/(c+d)**2
    return out

def _validate_metadata(payload):
    role=payload.get('data_role')
    if role not in ('synthetic','historical_arithmetic','sealed_project'):
        raise DataError('data_role must be synthetic, historical_arithmetic or sealed_project')
    meta=payload.get('metadata',{})
    stage=meta.get('analysis_stage','combined')
    if stage not in ('human_first','machine_reference','combined'):raise DataError('Unknown analysis_stage')
    active={'human_first':['A','B'],'machine_reference':['reference','rule','LLM'],'combined':list(METHODS)}[stage]
    if role=='sealed_project':
        # Refuse current/unsealed executions before inspecting record outputs.
        seals=meta.get('input_seals',{})
        for method in active:
            seal=seals.get(method,{})
            if seal.get('sealed') is not True or not _valid_hash(seal.get('sha256')):
                raise DataError(f'Project {method} submission must be sealed with a SHA256 binding')
    return role,meta,active
def _valid_hash(x):return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x.lower())
def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def projection_hash(records,method):
    return canonical_hash([{'unit_id':r['unit_id'],'output':r.get('outputs',{}).get(method)} for r in sorted(records,key=lambda r:r['unit_id'])])

def prepare(payload):
    role,meta,active=_validate_metadata(payload)
    records=payload.get('records')
    if not isinstance(records,list) or not records:raise DataError('Nonempty assigned-unit records required')
    design=meta.get('design',{})
    kind=design.get('kind')
    if kind not in ('stratified_srswor','nonprobability'):raise DataError('Only fixed stratified_srswor or nonprobability supported')
    if design.get('sampling_unit','source_unit')!='source_unit':raise DataError('Family/cluster/two-stage designs require another implementation')
    strata=design.get('strata',[])
    if not strata:raise DataError('Every assigned design stratum must be declared')
    if not isinstance(strata,list) or not all(isinstance(h,dict) for h in strata):raise DataError('strata must be a list of mappings')
    # Domain membership is frozen design metadata, never inferred from labels,
    # record IDs, key spelling, observed outcomes or a separately joined ledger.
    named_domains=any('domain' in h for h in strata) or 'domain_population_N' in design or 'domain_partition' in design
    if named_domains:
        if 'domain_partition' in design and design['domain_partition']!='remaining_exposed':
            raise DataError('Only domain_partition=remaining_exposed is supported')
        if any(h.get('domain') not in FROZEN_DOMAINS for h in strata):
            raise DataError('Every stratum must declare domain remaining/exposed; no partial or null partition')
        if any(not isinstance(h.get('department'),str) or not h['department'] for h in strata):
            raise DataError('Named domains require a frozen nonempty department for every stratum')
        if any(k in container for container in (payload,meta,design) for k in ('domain_inputs','domain_input_seals','domain_artifact_seals','domain_protocols')):
            raise DataError('All domains must use one ledger and common input/artifact bindings; domain overrides prohibited')
    index={}
    for h in strata:
        hid=h.get('id')
        if not isinstance(hid,str) or hid in index:raise DataError('Unique string stratum id required')
        N,n=h.get('N'),h.get('n')
        if type(N) is not int or type(n) is not int or not 1<=n<=N:
            raise DataError('Each nonempty stratum requires integer 1<=n<=N; no zero-pi layer')
        if kind=='stratified_srswor' and n==1 and N>1:raise DataError('Noncensus singleton stratum has unidentified variance; cannot bootstrap')
        index[hid]={'N':N,'n':n,'department':h.get('department')}
        if named_domains:index[hid]['domain']=h['domain']
    domain_N={d:sum(h['N'] for h in index.values() if h['domain']==d) for d in FROZEN_DOMAINS
              if any(h['domain']==d for h in index.values())} if named_domains else {}
    if 'domain_population_N' in design:
        declared=design['domain_population_N']
        if not isinstance(declared,dict) or set(declared)!=set(domain_N) or any(type(v) is not int or v<=0 for v in declared.values()) or declared!=domain_N:
            raise DataError('domain_population_N must have exactly the present domain keys and integer stratum-sum populations')
    if 'domain_partition' in design and set(domain_N)!=set(FROZEN_DOMAINS):
        raise DataError('remaining_exposed partition requires both nonempty domains')
    if named_domains and meta.get('scope',{}).get('kind')=='full_4481_audit' and domain_N!={'remaining':1444,'exposed':3037}:
        raise DataError('Named full_4481_audit requires remaining1444 and exposed3037')
    if named_domains and meta.get('scope',{}).get('kind')=='remaining_1444' and domain_N!={'remaining':1444}:
        raise DataError('Named remaining_1444 scope requires only remaining1444')
    seen=set();observed=Counter();departments=[];stratum_ids=[];state={m:np.zeros((len(records),5),dtype=np.int8) for m in active}
    failure_cause={m:np.zeros((len(records),5),dtype=np.int8) for m in active}
    allowed_row={'unit_id','stratum_id','department','outputs'}
    for i,r in enumerate(records):
        if set(r)-allowed_row:raise DataError('Label ledger accepts no body/context/reason fields')
        rid=r.get('unit_id');hid=r.get('stratum_id')
        if not isinstance(rid,str) or not rid or rid in seen:raise DataError('Unique nonempty unit_id required')
        if hid not in index:raise DataError('Unregistered stratum')
        seen.add(rid);observed[hid]+=1;stratum_ids.append(hid)
        if named_domains and 'department' not in r:raise DataError('Named-domain rows must explicitly bind their frozen department')
        dept=r.get('department','UNSPECIFIED')
        if not isinstance(dept,str) or not dept:raise DataError('Nonempty department string required')
        departments.append(dept)
        if index[hid]['department'] is not None and index[hid]['department']!=dept:
            raise DataError('Declared stratum department does not match record')
        outputs=r.get('outputs',{})
        if set(outputs)-set(active):raise DataError('Include only methods active in this sealed analysis stage; no unsealed unused outputs')
        for method in active:
            out=outputs.get(method)
            # No returned output is an execution failure, not semantic null.
            if out is None:state[method][i,:]=3;failure_cause[method][i,:]=1;continue
            if not isinstance(out,dict):raise DataError('Output must be a labels/status mapping or missing return')
            if set(out)-{'status','labels','dimension_status','version_sha256','failure_code'}:
                raise DataError('Unexpected output fields; labels/status only, no coding explanations')
            status=out.get('status')
            if status not in ('completed','execution_failure'):raise DataError('Explicit completed/execution_failure status required')
            labels=out.get('labels',{})
            if status=='execution_failure':
                if labels is None:labels={}
                if not isinstance(labels,dict):raise DataError('Failed labels must be empty mapping or null')
                if any(v is not None for v in labels.values()):raise DataError('Failed output cannot carry valid labels')
                state[method][i,:]=3;failure_cause[method][i,:]=2;continue
            if not isinstance(labels,dict):raise DataError('Completed labels must be a five-dimension mapping')
            if set(labels)!=set(DIMS):raise DataError('Completed output must contain all five labels; unresolved is explicit null')
            statuses=out.get('dimension_status',{})
            if not isinstance(statuses,dict):raise DataError('dimension_status must be a mapping')
            if set(statuses)-set(DIMS):raise DataError('Invalid dimension_status key')
            for j,dim in enumerate(DIMS):
                val=labels[dim];ds=statuses.get(dim,'completed')
                if ds not in ('completed','execution_failure'):raise DataError('Invalid dimension status')
                if ds=='execution_failure':
                    if val is not None:raise DataError('Dimension failure cannot carry a nonnull label')
                    state[method][i,j]=3;failure_cause[method][i,j]=3
                elif val is None:state[method][i,j]=2
                elif type(val) is int and val in (0,1):state[method][i,j]=val
                else:raise DataError('Each label must be integer0/1/null; bool/string/NaN prohibited')
    for hid,h in index.items():
        if observed[hid]!=h['n']:raise DataError(f'Assigned n mismatch in {hid}; keep nonresponse as explicit failure rows')
    assigned_hash=canonical_hash(sorted(seen))
    if role=='sealed_project':
        if design.get('assigned_ids_sha256')!=assigned_hash:
            raise DataError('Project joined ledger IDs differ from the before-answer assigned-ID hash')
        for method in active:
            if meta['input_seals'][method].get('joined_projection_sha256')!=projection_hash(records,method):
                raise DataError(f'Joined {method} label/status projection differs from its sealed binding')
    Ntotal=sum(h['N'] for h in index.values())
    scope=meta.get('scope',{})
    if named_domains and 'population_N' in scope and type(scope['population_N']) is not int:
        raise DataError('Named domain scope population_N must be an integer')
    if kind=='stratified_srswor' and scope.get('population_N',Ntotal)!=Ntotal:raise DataError('Declared domain N must equal sum of positive-pi strata N')
    weights=np.array([index[h]['N']/index[h]['n'] if kind=='stratified_srswor' else 1. for h in stratum_ids])
    return {'role':role,'meta':meta,'active':active,'kind':kind,'strata':index,'stratum_ids':np.array(stratum_ids),
            'departments':np.array(departments),'records':records,'states':state,'failure_causes':failure_cause,'weights':weights,
            'population_N':Ntotal if kind=='stratified_srswor' else len(records),
            'named_domains':named_domains,'domain_population_N':domain_N,
            'unit_domains':np.array([index[h]['domain'] for h in stratum_ids]) if named_domains else None}

def rao_wu_weights(prepared,replicates=5000,seed=20261010):
    """FPC-rescaled single-stage SRSWOR (Beaumont–Émond Eq20, m=n−1).
    Same replicate-weight matrix MUST be reused for every output/dimension.
    """
    if prepared['kind']!='stratified_srswor':raise DataError('No population bootstrap for nonprobability development materials')
    if type(replicates) is not int or replicates<2:raise DataError('At least two bootstrap replicates')
    rng=np.random.default_rng(seed);base=prepared['weights']
    W=np.broadcast_to(base,(replicates,len(base))).copy()
    for hid,h in prepared['strata'].items():
        ix=np.flatnonzero(prepared['stratum_ids']==hid);n=h['n'];N=h['N']
        if n==N:continue
        if n<2:raise DataError('Illegal noncensus singleton')
        counts=rng.multinomial(n-1,np.full(n,1/n),size=replicates)
        factor=1+math.sqrt(1-n/N)*(n*counts/(n-1)-1)
        W[:,ix]=base[ix]*factor
    return W

def analytic_covariance(prepared,X):
    X=np.asarray(X,dtype=float)
    if X.ndim==1:X=X[:,None]
    if prepared['kind']!='stratified_srswor':return None
    V=np.zeros((X.shape[1],X.shape[1]))
    for hid,h in prepared['strata'].items():
        n,N=h['n'],h['N']
        if n==N:continue
        x=X[prepared['stratum_ids']==hid];center=x-x.mean(axis=0)
        S=center.T@center/(n-1)
        V+=N*N*(1-n/N)*S/n
    return V

def finite_count_interval(N,n,x,alpha=.05):
    """Exact equal-tail hypergeometric confidence set for one finite count T.
    Neither hypergeom.interval nor its outcome quantiles are parameter CIs.
    """
    if not (type(N) is int and type(n) is int and type(x) is int and 0<=x<=n<=N and n>0):
        raise DataError('Integer N,n,x with0<=x<=n<=N required')
    if not 0<alpha<1:raise DataError('alpha in(0,1) required')
    if n==N:return [x,x]
    T=np.arange(x,N-n+x+1,dtype=int)
    valid=(hypergeom.sf(x-1,N,T,n)>=alpha/2-1e-14)&(hypergeom.cdf(x,N,T,n)>=alpha/2-1e-14)
    keep=T[valid]
    if not len(keep):raise ArithmeticError('Empty hypergeometric parameter interval')
    return [int(keep[0]),int(keep[-1])]

def finite_category_guard(prepared,indicator,alpha=.05):
    """Bonferroni across strata for ONE predeclared error/category total."""
    if prepared['kind']!='stratified_srswor':return {'status':'unavailable_nonprobability','interval':None}
    raw=np.asarray(indicator)
    if raw.shape!=(len(prepared['records']),) or not np.all(np.isin(raw,[0,1])):
        raise DataError('Category indicator must be0/1 for every assigned unit before integer conversion')
    y=raw.astype(int)
    H=len(prepared['strata']);out=[]
    for hid,h in prepared['strata'].items():
        x=int(y[prepared['stratum_ids']==hid].sum())
        lo,hi=finite_count_interval(h['N'],h['n'],x,alpha/H)
        out.append({'stratum':hid,'N':h['N'],'n':h['n'],'observed':x,'count95':[lo,hi]})
    return {'status':'one_category_stratified_Bonferroni_finite_count_guard',
            'nominal_coverage':1-alpha,'interval':[sum(x['count95'][0] for x in out),sum(x['count95'][1] for x in out)],
            'strata':out,'scope':'ONE category total only. Not a metric CI, full confusion-table CI or45-metric simultaneous interval.'}

def joint_table_guard(prepared,pair_states,alpha=.05):
    """Conservative simultaneous 16-state count-set, including null/failure.
    Produces count constraints, not unimplemented nonlinear metric projections.
    """
    if prepared['kind']!='stratified_srswor':return {'status':'unavailable_nonprobability'}
    raw=np.asarray(pair_states)
    if raw.shape!=(len(prepared['records']),) or not np.all(np.isin(raw,np.arange(16))):
        raise DataError('One integer category0..15 required for every assigned unit before integer conversion')
    pair=raw.astype(int);H=len(prepared['strata']);out=[]
    for hid,h in prepared['strata'].items():
        block=pair[prepared['stratum_ids']==hid]
        cells=[]
        for cat in range(16):
            x=int((block==cat).sum());bounds=finite_count_interval(h['N'],h['n'],x,alpha/(H*16))
            cells.append({'left_state':STATES[cat//4],'right_state':STATES[cat%4],
                          'observed':x,'population_count_bounds':bounds})
        out.append({'stratum':hid,'N':h['N'],'n':h['n'],'cells':cells,
                    'additional_constraint':'integer category counts nonnegative and sum exactly N'})
    return {'status':'joint16_category_count_confidence_set','nominal_coverage':1-alpha,
            'family':'one comparison × one dimension, all strata×16 states simultaneously',
            'alpha_per_count':alpha/(H*16),'strata':out,
            'metric_projection_implemented':False,
            'strict_projection_contract':'To obtain simultaneous metric bounds, optimize each metric over THIS whole constrained integer count set, retaining undefined-denominator possibilities and known population margins if independently bound. Marginal endpoints or a single error guard cannot be passed as metric confidence limits.',
            'not45_metric_joint_coverage':True}

def attention_bounds(known_hits,unresolved,denominator):
    k=np.asarray(known_hits,dtype=float);u=np.asarray(unresolved,dtype=float)
    if k.shape!=(5,) or u.shape!=(5,) or np.any(k<0) or np.any(u<0) or denominator<=0:
        raise DataError('Five nonnegative hit/unresolved totals and positive assigned denominator')
    if np.any(k+u>denominator+1e-8):raise DataError('Hit+unresolved must not exceed assigned weight')
    H=float(k.sum());U=float(u.sum());out={}
    for j,dim in enumerate(DIMS):
        coverage=[float(k[j]/denominator),float((k[j]+u[j])/denominator)]
        if H>0:share=[float(k[j]/(H+U-u[j])),float((k[j]+u[j])/(H+u[j]))]
        elif U==0:share=None
        elif u[j]==0:share=[0.,0.]
        elif U-u[j]==0:share=[1.,1.]
        else:share=[0.,1.]
        out[dim]={'known_hit_coverage':float(k[j]/denominator),
                  'known_hit_attention_share':None if not H else float(k[j]/H),
                  'unknown_coverage_bounds_not_CI':coverage,
                  'unknown_share_bounds_conditional_on_positive_total_not_CI':share,
                  'positive_total_share_possible':H+U>0,
                  'zero_total_share_undefined_possible':H==0}
    return out

def analysis_scopes(prepared):
    """Full-length masks; named domains and intersections are unions of strata.
    Legacy departments without complete frozen membership remain sampled views.
    No weights are regenerated here, and no nonlinear metrics are pooled.
    """
    ids=prepared['stratum_ids'];strata=prepared['strata'];scopes={}
    fixed_depts=all(isinstance(h['department'],str) and h['department'] for h in strata.values())
    probability=prepared['kind']=='stratified_srswor'
    global_census=probability and all(h['n']==h['N'] for h in strata.values())
    def add(key,mask,members,kind,domain=None,department=None):
        if not mask.any():return
        scopes[key]={'mask':mask,'stratum_ids':members,'kind':kind,'domain':domain,'department':department,
                     'population_N':sum(strata[h]['N'] for h in members) if probability and members is not None else
                                    int(mask.sum()) if global_census else None,
                     'full_census':probability and (global_census or
                                   (members is not None and all(strata[h]['n']==strata[h]['N'] for h in members)))}
    add('ALL',np.ones(len(ids),dtype=bool),list(strata),'all')
    if prepared['named_domains']:
        for domain in FROZEN_DOMAINS:
            members=[h for h,x in strata.items() if x['domain']==domain]
            add('domain:'+domain,prepared['unit_domains']==domain,members,'domain',domain=domain)
    for dept in sorted(set(prepared['departments'])):
        members=[h for h,x in strata.items() if x['department']==dept] if fixed_depts else None
        add('department:'+dept,prepared['departments']==dept,members,'department',department=dept)
    if prepared['named_domains']:
        for domain in FROZEN_DOMAINS:
            for dept in sorted(set(prepared['departments'])):
                members=[h for h,x in strata.items() if x['domain']==domain and x['department']==dept]
                add('domain:'+domain+'|department:'+dept,(prepared['unit_domains']==domain)&(prepared['departments']==dept),
                    members,'domain_department',domain,dept)
    return scopes

def domain_is_census(prepared,domain):
    view=analysis_scopes(prepared).get(domain)
    return bool(view and view['full_census'])

def _guard_scope_prepared(prepared,view):
    """Subset only the finite-count guard's fixed stratum universe; never W.
    Guards remain marginal per view/comparison/dimension, not jointly across views.
    """
    members=view['stratum_ids']
    if members is None:return None
    return {**prepared,'strata':{h:prepared['strata'][h] for h in members},
            'stratum_ids':prepared['stratum_ids'][view['mask']],
            'records':[r for r,keep in zip(prepared['records'],view['mask']) if keep]}

def _interval(point,reps,probability,census):
    if not probability:return {'CI95':None,'status':'no_population_CI_for_nonprobability_development'}
    reps=np.asarray(reps,dtype=float);valid=np.isfinite(reps);undefined=int((~valid).sum())
    if point is None:return {'CI95':None,'status':'undefined_point_denominator','undefined_replicates':undefined,'total_replicates':len(reps)}
    conditional=None if not valid.any() else [float(x) for x in np.quantile(reps[valid],[.025,.975],method='linear')]
    if undefined:return {'CI95':None,'conditional_quantiles_among_defined_replicates':conditional,
                         'status':'undefined_bootstrap_replicates_no_unconditional95_claim',
                         'undefined_replicates':undefined,'total_replicates':len(reps)}
    degenerate=bool(np.ptp(reps)<1e-12)
    return {'CI95':None if degenerate and not census else conditional,
            'bootstrap_percentiles95':conditional,'undefined_replicates':0,'total_replicates':len(reps),
            'status':'finite_census_no_sampling_error_conditional_on_labels' if census else
                     'degenerate_non_census_requires_finite_guard_not_adequacy_evidence' if degenerate else 'approximate_FPC_rescaled_bootstrap_percentile95',
            'variance_about_original_point':float(np.mean((reps-point)**2))}

def _exact_weighted_cells(prepared,pair,domain_mask):
    cats=(5,4,1,0);out=[]
    for cat in cats:
        total=Fraction(0)
        for hid,h in prepared['strata'].items():
            count=int(((pair==cat)&domain_mask&(prepared['stratum_ids']==hid)).sum())
            total+=count*(Fraction(h['N'],h['n']) if prepared['kind']=='stratified_srswor' else 1)
        out.append(total)
    return out

def _table_summary(table,raw=False):
    t=np.asarray(table,dtype=int if raw else float);a,b,c,d=t[1,1],t[1,0],t[0,1],t[0,0]
    number=int if raw else float
    row=t.sum(axis=1);col=t.sum(axis=0)
    return {'full4x4_including_failure':t.tolist(),'completed_0_1_null_3x3':t[:3,:3].tolist(),
            'binary_four_order_a_b_c_d':[number(a),number(b),number(c),number(d)],
            'assigned_total':number(t.sum()),'comparable_binary_total':number(t[:2,:2].sum()),
            'left_all_assigned_state_totals':dict(zip(STATES,map(number,row))),
            'right_all_assigned_state_totals':dict(zip(STATES,map(number,col))),
            'left_comparable_positive_negative':[number(a+b),number(c+d)],
            'right_comparable_positive_negative':[number(a+c),number(b+d)],
            'one_or_both_semantic_null_no_failure':number(t[:3,:3].sum()-t[:2,:2].sum()),
            'any_execution_failure':number(t.sum()-t[:3,:3].sum()),'both_execution_failure':number(t[3,3]),
            'both_semantic_null':number(t[2,2])}

def review_eligibility(prepared,numeric):
    meta=prepared['meta'];reasons=[];role=prepared['role'];scope=meta.get('scope',{})
    if role!='sealed_project':reasons.append('Synthetic/historical arithmetic is not prospective project execution')
    if prepared['kind']!='stratified_srswor':reasons.append('Nonprobability development cannot validate a finite population')
    if scope.get('kind') not in ('remaining_1444','full_4481_audit'):reasons.append('No declared prospective finite validation scope')
    expected={'remaining_1444':1444,'full_4481_audit':4481}.get(scope.get('kind'))
    if expected is not None and prepared['population_N']!=expected:reasons.append('Domain size differs from declared4481/1444 scope')
    if not _valid_hash(scope.get('frame_ids_sha256')):reasons.append('No frozen target-ID frame binding')
    identities=meta.get('identities',{})
    for m in ('A','B'):
        identity=identities.get(m,{})
        if identity.get('kind')!='human' or identity.get('verified') is not True or identity.get('independent_initial') is not True:
            reasons.append(f'{m} is not attested genuine verified independent initial human coder')
        if not isinstance(identity.get('identity_code'),str) or not identity['identity_code'].strip():
            reasons.append(f'{m} has no nonempty identity code')
    if identities.get('A',{}).get('identity_code')==identities.get('B',{}).get('identity_code'):
        reasons.append('A/B must be distinct people')
    ref=identities.get('reference',{})
    if ref.get('kind')!='human_adjudication' or ref.get('credible') is not True or ref.get('blinded_to_machines') is not True:
        reasons.append('No attested credible human adjudication blinded to machines')
    if not isinstance(ref.get('identity_code'),str) or not ref['identity_code'].strip():reasons.append('Reference adjudicator identity is missing')
    freezes=meta.get('freeze_attestations',{})
    for flag in ('common_manual','common_materials','design_before_answers','initial_submissions_before_discussion','reference_before_machine_comparison','final_rule_and_LLM_before_test_feedback'):
        if freezes.get(flag) is not True:reasons.append('Missing freeze attestation: '+flag)
    for method in METHODS:
        seal=meta.get('input_seals',{}).get(method,{})
        if seal.get('sealed') is not True or not _valid_hash(seal.get('sha256')):reasons.append('Missing complete sealed binding: '+method)
    for artifact in ('common_manual','common_materials','design','rule_protocol','LLM_protocol'):
        seal=meta.get('artifact_seals',{}).get(artifact,{})
        if seal.get('sealed') is not True or not _valid_hash(seal.get('sha256')):
            reasons.append('Missing frozen artifact binding: '+artifact)
    if meta.get('identity_and_source_evidence_reviewed') is not True:reasons.append('Identity/freeze/scope assertions have not been externally reviewed')
    return {'all_numerical_point_targets_met':numeric,'metadata_attestations_complete_for_project_review':not reasons,
            'prerequisite_gaps':reasons,'formal_acceptance':False,
            'formal_acceptance_status':'requires_explicit_project_review_of_numeric_results_scope_unknowns_real_identity_freezes_and_reference',
            'CI_lower_or_halfwidth_gate_added':False,
            'metadata_cannot_authenticate_human_identity_on_its_own':True,
            'remaining_1444_cannot_validate_all4481':scope.get('kind')=='remaining_1444'}

def analyze(payload,replicates=5000,seed=20261010,guard_mode='single_category'):
    """Calculate only supplied frozen label ledger; never access source corpus."""
    if guard_mode not in ('none','single_category','joint_table'):raise DataError('guard_mode none/single_category/joint_table')
    prep=prepare(payload);prob=prep['kind']=='stratified_srswor';base=prep['weights']
    W=rao_wu_weights(prep,replicates,seed) if prob else None
    census=prob and all(h['n']==h['N'] for h in prep['strata'].values())
    scopes=analysis_scopes(prep)
    domains={key:view['mask'] for key,view in scopes.items()}
    weights_hash=None if W is None else hashlib.sha256(np.ascontiguousarray(W).tobytes()).hexdigest()
    scope_targets={key:{'comparisons':{},'all_numerical_point_targets_met':True,'formal_acceptance':False,
                        'aggregation':'Targets computed from this scope weighted four-cell totals; no average of domain metrics.'}
                   for key in scopes}
    comparisons={};numerical={};all_numeric=True
    for name,(left,right,purpose) in COMPARISONS.items():
        if left not in prep['active'] or right not in prep['active']:continue
        comp={'orientation':{'row':left,'column':right,'four_order':'a=row1col1,b=row1col0,c=row0col1,d=row0col0',
                             'interpretation':'TP,FP,FN,TN' if purpose=='classification' else 'A1B1,A1B0,A0B1,A0B0; neither person is truth'},'domains':{}}
        numerical[name]={}
        for dom,mask in domains.items():
            domain_census=scopes[dom]['full_census']
            dimensions={}
            scope_targets[dom]['comparisons'][name]={}
            for j,dim in enumerate(DIMS):
                pair=prep['states'][left][:,j]*4+prep['states'][right][:,j]
                X=np.stack([((pair==cat)&mask).astype(float) for cat in (5,4,1,0)],axis=1)
                raw=np.bincount(pair[mask],minlength=16).reshape(4,4)
                weighted=np.bincount(pair[mask],weights=base[mask],minlength=16).reshape(4,4)
                exact=_exact_weighted_cells(prep,pair,mask);met=exact_metrics(exact)
                rawmet=exact_metrics([int(raw[1,1]),int(raw[1,0]),int(raw[0,1]),int(raw[0,0])])
                keys=('Po','Pe','kappa','Ppos','Pneg') if purpose=='agreement' else tuple(met)
                values={k:_number(met[k]) for k in keys};rawvalues={k:_number(rawmet[k]) for k in keys}
                V=analytic_covariance(prep,X);grad=metric_gradients([float(x) for x in exact])
                reps=vector_metrics(W@X) if prob else {}
                intervals={k:_interval(values[k],reps.get(k,[]),prob,domain_census) for k in keys}
                se={k:None if V is None or grad[k] is None else math.sqrt(max(0.,float(grad[k]@V@grad[k]))) for k in keys}
                required=('kappa',) if purpose=='agreement' else ('kappa','Precision','Recall','F1')
                targets={k:{'point':_number(met[k]),'target':.8,'met':met[k] is not None and met[k]>=TARGET,
                            'scope':'comparable determinate binary subdomain'} for k in required}
                scope_targets[dom]['comparisons'][name][dim]=targets
                scope_targets[dom]['all_numerical_point_targets_met'] &= all(x['met'] for x in targets.values())
                if dom=='ALL':
                    numerical[name][dim]=targets
                    all_numeric=all_numeric and all(x['met'] for x in targets.values())
                item={'raw':_table_summary(raw,raw=True),'design_weighted':_table_summary(weighted),
                      'weighted_four_exact_fractions':[str(x) for x in exact],
                      'raw_metrics':rawvalues,'design_weighted_metrics':values,
                      'domain_full_census_no_sampling_error':domain_census,
                      'analytic_sampling_SE':se,'intervals':intervals,
                      'numeric_targets':targets,'binary_zero_cells':[lab for lab,x in zip(('a','b','c','d'),raw[np.ix_([1,0],[1,0])].reshape(-1)) if x==0],
                      'metric_scope':'Both completed0/1 pairs only; other assigned units remain in9/16-state tables, unknown/failure and weights.',
                      'Ppos_F1_relation':'Same formula2a/(2a+b+c); human Ppos measures symmetric positive agreement, machine F1 measures positive-class overlap against a credible reference. Same number does not equate reliability and validity.'}
                guard_prep=prep if dom=='ALL' else _guard_scope_prepared(prep,scopes[dom]) if prep['named_domains'] else None
                if guard_prep is not None and guard_mode!='none':
                    guard_pair=pair if dom=='ALL' else pair[mask]
                    if guard_mode=='joint_table':item['finite_guard']=joint_table_guard(guard_prep,guard_pair)
                    else:
                        cats={'A1B0':4,'A0B1':1} if purpose=='agreement' else {'FP':4,'FN':1}
                        item['finite_guard']={k:finite_category_guard(guard_prep,(guard_pair==cat).astype(int)) for k,cat in cats.items()}
                        item['guard_not_metric_CI']='Each category guard is separate marginal95, not a simultaneous four-cell, κ/P/R/F1 or45-metric interval.'
                    item['guard_scope_note']='One fixed stratum-union view only; no simultaneous coverage across views. Full16-state nonlinear metric projection remains unimplemented.'
                dimensions[dim]=item
            comp['domains'][dom]=dimensions
        comparisons[name]=comp
    if set(comparisons)!=set(COMPARISONS):
        all_numeric=False
        for targets in scope_targets.values():targets['all_numerical_point_targets_met']=False
    attention={}
    for method in prep['active']:
        attention[method]={}
        for dom,mask in domains.items():
            domain_census=scopes[dom]['full_census']
            s=prep['states'][method];k=(s==1).astype(float)*mask[:,None]
            null=(s==2).astype(float)*mask[:,None];fail=(s==3).astype(float)*mask[:,None]
            K=base@k;U=base@(null+fail);den=float(base[mask].sum())
            bounds=attention_bounds(K,U,den)
            results={}
            kr=W@k if prob else None;nr=W@null if prob else None;fr=W@fail if prob else None
            dr=W@mask.astype(float) if prob else None
            for j,dim in enumerate(DIMS):
                q=None if not K.sum() else float(K[j]/K.sum())
                qr=np.divide(kr[:,j],kr.sum(axis=1),out=np.full(replicates,np.nan),where=kr.sum(axis=1)>0) if prob else []
                results[dim]={**bounds[dim],
                              'domain_full_census_no_sampling_error':domain_census,
                              'raw':{'known_positive':int(k[:,j].sum()),'semantic_null':int(null[:,j].sum()),'execution_failure':int(fail[:,j].sum()),'assigned_n':int(mask.sum())},
                              'design_weighted':{'known_positive':float(K[j]),'semantic_null':float(base@null[:,j]),'execution_failure':float(base@fail[:,j]),'unresolved_total':float(U[j]),'assigned_weight_total':den},
                              'semantic_null_rate':float(base@null[:,j]/den),'execution_failure_rate':float(base@fail[:,j]/den),
                              'unresolved_rate':float(U[j]/den),
                              'failure_process_subtypes':{
                                  lab:{'raw_n':int(((prep['failure_causes'][method][:,j]==code)&mask).sum()),
                                       'weighted_total':float(base@((prep['failure_causes'][method][:,j]==code)&mask))}
                                  for code,lab in ((1,'missing_return'),(2,'method_execution_failure'),(3,'dimension_execution_failure'))},
                              'semantic_null_rate_CI':_interval(float(base@null[:,j]/den),nr[:,j]/dr if prob else [],prob,domain_census),
                              'execution_failure_rate_CI':_interval(float(base@fail[:,j]/den),fr[:,j]/dr if prob else [],prob,domain_census),
                              'unresolved_rate_CI':_interval(float(U[j]/den),(nr[:,j]+fr[:,j])/dr if prob else [],prob,domain_census),
                              'known_coverage_CI':_interval(float(K[j]/den),kr[:,j]/dr if prob else [],prob,domain_census),
                              'known_share_CI':_interval(q,qr,prob,domain_census),
                              'unknown_bounds_interpretation':'Partial-identification ranges conditional on observed/design-weighted totals; not95CI. Null and failure unresolved masses are both included; sampling uncertainty is separate.'}
            attention[method][dom]=results
    contrast={}
    depts=[dom for dom,view in scopes.items() if view['kind']=='department']
    for method in prep['active']:
        contrast[method]={}
        for i,one in enumerate(depts):
            for two in depts[i+1:]:
                values={}
                for dim in DIMS:
                    aa=attention[method][one][dim];bb=attention[method][two][dim]
                    a=aa['unknown_share_bounds_conditional_on_positive_total_not_CI'];b=bb['unknown_share_bounds_conditional_on_positive_total_not_CI']
                    values[dim]={'q_difference_unknown_bounds_not_CI':None if a is None or b is None else [a[0]-b[1],a[1]-b[0]],
                                 'conditional_on_both_domains_positive_hit_denominators':True,
                                 'undefined_possible':aa['zero_total_share_undefined_possible'] or bb['zero_total_share_undefined_possible']}
                contrast[method][one+' minus '+two]=values
    scope_metadata={key:{'kind':view['kind'],'domain':view['domain'],'department':view['department'],
                         'frozen_stratum_ids':view['stratum_ids'],'population_membership_frozen':view['stratum_ids'] is not None,
                         'assigned_n':int(view['mask'].sum()),'population_N':view['population_N'],
                         'weighted_assigned_total':float(base[view['mask']].sum()),
                         'full_census_no_sampling_error':view['full_census'],
                         'replicate_assigned_total_range':None if W is None else
                              [float(x) for x in (np.min(W@view['mask'].astype(float)),np.max(W@view['mask'].astype(float)))],
                         'unit_mask_sha256':hashlib.sha256(np.ascontiguousarray(view['mask']).tobytes()).hexdigest(),
                         'shared_replicate_weights_sha256':weights_hash,
                         'common_bindings_reference':'identity_and_freeze_metadata; one whole-ledger validation in prepare'}
                    for key,view in scopes.items()}
    return {'engine_schema_version':'1.1','data_role':prep['role'],'analysis_stage':prep['meta'].get('analysis_stage','combined'),
            'scope_metadata':prep['meta'].get('scope',{}),'identity_and_freeze_metadata':{k:prep['meta'].get(k,{}) for k in ('identities','input_seals','artifact_seals','freeze_attestations')},
            'design':{'kind':prep['kind'],'assigned_n':len(base),'population_N':prep['population_N'],
                      'weighted_assigned_total':float(base.sum()),'strata':prep['strata'],
                      'CI_method':'one-stage SRSWOR FPC-rescaled Rao-Wu/RWYB special case, m=n−1; common unit weights all methods/dimensions' if prob else 'no population CI: nonprobability development',
                      'bootstrap_replicates':replicates if prob else 0,'seed':seed if prob else None,
                      'bootstrap_quantile_method':'numpy.quantile method=linear',
                      'resampling_unit_order':'input record order, frozen by execution input SHA256',
                      'shared_replicate_weights_sha256':weights_hash,
                      'replicate_weight_generation_count':1 if prob else 0,
                      'named_domain_partition':prep['named_domains'],'domain_population_N':prep['domain_population_N'],
                      'domain_membership_source':'frozen stratum.domain only' if prep['named_domains'] else 'legacy single-domain design',
                      'domain_partition_checks':None if not prep['named_domains'] else
                          {'every_unit_has_one_frozen_domain':True,'nonempty_present_domains':list(prep['domain_population_N']),
                           'mutually_exclusive_domains':True,'sum_domain_population_N':sum(prep['domain_population_N'].values()),
                           'matches_total_stratum_population_N':sum(prep['domain_population_N'].values())==sum(h['N'] for h in prep['strata'].values()),
                           'full4481_equals_remaining1444_plus_exposed3037':prep['domain_population_N']=={'remaining':1444,'exposed':3037}},
                      'full_census_no_sampling_error':census,
                      'percentile_CI_scope':'Approximate marginal95 per scalar, not finite-sample exact coverage nor45-metric simultaneous95. Zero/undefined replicate conditions are explicit.'},
            'comparisons':comparisons,'numeric_targets':numerical,'project_review':review_eligibility(prep,all_numeric),
            'analysis_scopes':scope_metadata,'numeric_targets_by_analysis_scope':scope_targets,
            'global_numeric_gate_scope':'ALL only; per-scope flags are separate results, never averages or a new acceptance gate',
            'attention':attention,'department_attention_difference_bounds':contrast,
            'finite_joint16_nonlinear_metric_projection_implemented':False,
            'analytic_covariance_role':'diagnostic sampling covariance and gradient SE only; not a CI or numeric gate',
            'unknown_policy':'0/1/null9-state table plus failure4th state; no imputation, no renormalization claiming full-domain performance.',
            'nonprobability_weighting_note':'No design weights or population CI; weighted columns equal raw descriptive totals.' if not prob else None}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--replicates',type=int,default=5000);parser.add_argument('--seed',type=int,default=20261010)
    parser.add_argument('--guard-mode',choices=('none','single_category','joint_table'),default='single_category')
    args=parser.parse_args()
    payload=json.loads(args.input.read_text())
    output=analyze(payload,args.replicates,args.seed,args.guard_mode)
    output['execution_provenance']={'input_path':str(args.input.resolve()),'input_sha256':sha256(args.input),
                                     'engine_path':str(Path(__file__).resolve()),'engine_sha256':sha256(__file__)}
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
