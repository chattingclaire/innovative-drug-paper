"""Metadata-only finite-population planning; constructs counts, never sample IDs.

Run: ../.venv/bin/python precision_plan.py
Frozen auxiliary labels are not human answers. Synthetic scenario counts are not
unit-level pseudo-reference labels and are never assigned to actual IDs.
"""
from pathlib import Path
import json, hashlib, math
from collections import Counter, defaultdict
import numpy as np
from scipy.stats import hypergeom, beta

HERE=Path(__file__).resolve().parent
DIMS=['S','E','Ec','I','F']; METHODS=['rules39','LLM03']
ORDER=['NMPA','NHSA','NHC']; Z=1.959963984540054
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def signature(r):
    vals=[r[m][d] for d in ['I','F'] for m in METHODS]
    if any(v is None for v in vals):return 'NA'
    return ''.join(map(str,vals))
def stratum(r,full=False):
    sig=signature(r)
    if any(r[m][d] is None for m in METHODS for d in DIMS):tag='NA'
    elif sig!='0000':tag='IF'
    elif any(r[m][d]==1 for m in METHODS for d in ['S','E','Ec']):tag='OTHER_POS'
    else:tag='ALL_NEG'
    return '|'.join(([r['exposure']] if full else [])+[r['department'],sig,tag])
def strata(rows,full=False):
    c=Counter(stratum(r,full) for r in rows)
    return [{'key':k,'N':N,'department':k.split('|')[-3],
             'IF_signature':k.split('|')[-2],'tag':k.split('|')[-1]} for k,N in sorted(c.items())]
def allocation(st,fraction):
    return {h['key']:h['N'] if h['tag']!='ALL_NEG' or h['department']=='NHC'
            else min(h['N'],max(2,math.ceil(fraction*h['N']))) for h in st}
def metric_grad(c):
    a,b,c1,d=map(float,c);N=a+b+c1+d
    out={}
    if N<=0:return {k:(None,None) for k in ['kappa','precision','recall','F1']}
    den=a+b
    out['precision']=(a/den,np.array([b,-a,0.,0.])/den**2) if den else (None,None)
    den=a+c1
    out['recall']=(a/den,np.array([c1,0.,-a,0.])/den**2) if den else (None,None)
    den=2*a+b+c1
    out['F1']=(2*a/den,np.array([2*(b+c1),-2*a,-2*a,0.])/den**2) if den else (None,None)
    po=(a+d)/N;u=(a+b)/N;v=(a+c1)/N;pe=u*v+(1-u)*(1-v)
    if 1-pe>1e-14:
        k=(po-pe)/(1-pe)
        dpo=(np.array([1.,0.,0.,1.])-po)/N
        du=(np.array([1.,1.,0.,0.])-u)/N;dv=(np.array([1.,0.,1.,0.])-v)/N
        dpe=(2*v-1)*du+(2*u-1)*dv
        out['kappa']=(k,(dpo+(k-1)*dpe)/(1-pe))
    else:out['kappa']=(None,None)
    return out
def covariance(cells,n):
    cells=np.asarray(cells,dtype=float);N=float(sum(cells))
    if n==N or N<=1:return np.zeros((4,4))
    p=cells/N
    S=N/(N-1)*(np.diag(p)-np.outer(p,p))
    return N*N*(1-n/N)*S/n
def bounded_counts(capacity,weights,total):
    """Integer largest remainder, sum fixed, no cell exceeds its population."""
    capacity=np.asarray(capacity,dtype=int);weights=np.asarray(weights,dtype=float)
    if total==0:return np.zeros_like(capacity)
    if total==sum(capacity):return capacity.copy()
    lo=-60.;hi=60.
    logw=np.log(np.maximum(weights,1e-30))
    for _ in range(100):
        mid=(lo+hi)/2;v=capacity/(1+np.exp(np.clip(-(mid+logw),-700,700)))
        if v.sum()<total:lo=mid
        else:hi=mid
    count=np.floor(v).astype(int);remaining=total-int(count.sum())
    rank=sorted(range(len(count)),key=lambda i:(-(v[i]-count[i]),i))
    for i in rank:
        if remaining==0:break
        if count[i]<capacity[i]:count[i]+=1;remaining-=1
    assert remaining==0 and sum(count)==total and np.all(count<=capacity)
    return count
def machine_scenario(rows,dim,T,signal):
    # Joint OLD-machine 2x2 margins are fixed. One reference allocation gives BOTH
    # machines' 2x2 tables, so impossible independent P/R choices cannot arise.
    micro=Counter((stratum(r),r['rules39'][dim],r['LLM03'][dim]) for r in rows)
    keys=sorted(micro);caps=[micro[k] for k in keys]
    weights=[signal**(k[1]+k[2]) for k in keys]
    reference=bounded_counts(caps,weights,T)
    by_method={m:defaultdict(lambda:[0,0,0,0]) for m in METHODS}
    joint=[]
    for (h,x,y),N,t in zip(keys,caps,reference):
        joint.append({'stratum':h,'rules39':x,'LLM03':y,'N':N,'reference_positive':int(t)})
        for m,pred in [('rules39',x),('LLM03',y)]:
            cells=by_method[m][h]
            if pred==1:cells[0]+=int(t);cells[1]+=int(N-t)
            else:cells[2]+=int(t);cells[3]+=int(N-t)
    for m in METHODS:
        assert sum(c[0]+c[2] for c in by_method[m].values())==T
        assert sum(c[0]+c[1] for c in by_method[m].values())==sum(r[m][dim] for r in rows)
    return joint,by_method
def summarize(cells_by_h,ns):
    total=np.sum(list(cells_by_h.values()),axis=0)
    V=sum((covariance(c,ns[h]) for h,c in cells_by_h.items()),np.zeros((4,4)))
    metrics={}
    for key,(value,g) in metric_grad(total).items():
        metrics[key]={'point':value,'linearized_95_halfwidth':None if g is None else Z*math.sqrt(max(0.,float(g@V@g)))}
    return {'TP_FP_FN_TN':list(map(int,total)),
            'predicted_positive_denominator':int(total[0]+total[1]),
            'reference_positive_denominator':int(total[0]+total[2]),'metrics':metrics}
def zero_error_upper(Nn,alpha=.025):
    """Conservative pooled bound for unseen positives after zero in sampled cells.
    Maximizes P(all zero) over all allocations with total K in the specified
    strata. Discrete inversion tests the zero event only; does not estimate all
    metric CIs or include error in any other strata.
    """
    cap=sum(N-n for N,n in Nn)
    # Only few K can survive; computing all cap is cheap for this frame.
    best=np.array([0.])
    for N,n in Nn:
        logp=hypergeom.logpmf(0,N,np.arange(N-n+1),n)
        nxt=np.full(len(best)+len(logp)-1,-np.inf)
        for k,v in enumerate(best):nxt[k:k+len(logp)]=np.maximum(nxt[k:k+len(logp)],v+logp)
        best=nxt
    allowed=np.flatnonzero(best>=math.log(alpha)-1e-12)
    upper=int(allowed[-1]) if len(allowed) else 0
    return {'alpha_one_tail':alpha,'N_n':Nn,'maximum_unseen_count':upper,
            'sup_zero_event_probability_at_upper':float(math.exp(best[upper])),
            'sup_zero_event_probability_at_next':None if upper==cap else float(math.exp(best[upper+1]))}
def positive_count_tail(N_T_n,minimum):
    dist=np.array([1.])
    for N,T,n in N_T_n:
        low=max(0,n-(N-T));high=min(n,T)
        term=np.zeros(high+1);term[low:]=hypergeom.pmf(np.arange(low,high+1),N,T,n)
        dist=np.convolve(dist,term)
    return float(dist[:minimum].sum())
def denominator_examples():
    out=[]
    for m in [10,22,40,55,62,78,97,150]:
        k=round(.8*m);p=k/m
        low=0 if k==0 else float(beta.ppf(.025,k,m-k+1))
        high=1 if k==m else float(beta.ppf(.975,k+1,m-k))
        out.append({'equal_weight_denominator':m,'successes':k,'observed_ratio':p,
                    'Wald_halfwidth_at_point80':Z*math.sqrt(.8*.2/m),
                    'binomial_exact_95':[low,high],
                    'exact_max_radius_about_observed':max(p-low,high-p),
                    'role':'illustration only; not the primary stratified finite-population CI'})
    return out
def human_scenarios(st,allocations):
    N=sum(h['N'] for h in st);out=[]
    for T in [14,43,72,144,289,722]:
        for unequal_factor in [1.,1.25]:
          for nominal in [.8,.85,.9]:
            A=T;B=min(N,round(T*unequal_factor))
            pe=(A*B+(N-A)*(N-B))/N**2
            requested_a_continuous=(N*(nominal*(1-pe)+pe)-N+A+B)/2
            requested_a=round(requested_a_continuous)
            a=min(min(A,B),max(0,A+B-N,requested_a))
            total=[a,A-a,B-a,N-A-B+a]
            # Deterministic transportation of four finite cells to strata.
            rest=np.array([h['N'] for h in st]);hcell=np.zeros((len(st),4),dtype=int)
            for j,c in enumerate(total[:-1]):
                part=bounded_counts(rest,np.ones(len(st)),c);hcell[:,j]=part;rest-=part
            hcell[:,3]=rest
            by_h={h['key']:list(map(int,row)) for h,row in zip(st,hcell)}
            out.append({'reference':'synthetic A/B initial independent decisions, not adjudicated truth',
                        'A_positive':A,'B_positive':B,'nominal_kappa':nominal,
                        'nominal_kappa_feasible_at_these_margins':max(0,A+B-N)-1e-12<=requested_a_continuous<=min(A,B)+1e-12,
                        'finite_A1B1_A1B0_A0B1_A0B0':total,
                        'actual_kappa':metric_grad(total)['kappa'][0],
                        'allocations':{key:summarize(by_h,ns)['metrics']['kappa'] for key,ns in allocations.items()}})
    return out
def joint_PR_feasibility(N,M1,M2,J,threshold=.8):
    q=[J,M1-J,M2-J,N-M1-M2+J]
    lo=max(math.ceil(threshold*M1-1e-12),math.ceil(threshold*M2-1e-12))
    hi=min(math.floor(M1/threshold+1e-12),math.floor(M2/threshold+1e-12))
    feasible=[];witness=None
    for T in range(lo,hi+1):
        for a1 in range(max(math.ceil(threshold*M1-1e-12),math.ceil(threshold*T-1e-12)),min(M1,T)+1):
            for a2 in range(max(math.ceil(threshold*M2-1e-12),math.ceil(threshold*T-1e-12)),min(M2,T)+1):
                xmin=max(0,a1-q[1],a2-q[2],a1+a2-T)
                xmax=min(J,a1,a2,q[3]+a1+a2-T)
                if xmin<=xmax:
                    feasible.append(T)
                    if witness is None:
                        witness={'T':T,'rules39_TP':a1,'LLM03_TP':a2,
                                 'reference_positive_by_machine11_10_01_00':[xmin,a1-xmin,a2-xmin,T-a1-a2+xmin]}
                    break
            if feasible and feasible[-1]==T:break
    return {'fixed_old_machine_joint11_10_01_00':q,
            'both_methods_P_and_R_ge80_possible':bool(feasible),
            'feasible_T_values':sorted(set(feasible)),'one_count_only_witness':witness,
            'certifies_kappa_or_reference_validity':False}
def main():
    binding=json.loads((HERE/'source-bindings.json').read_text())
    p=HERE/'inputs/metadata-and-fixed-labels.jsonl'
    assert sha(p)==binding['projection']['sha256']
    rows=[json.loads(l) for l in p.open()]
    # Projected schema guard: impossible to inject body or human labels silently.
    for r in rows:
        assert set(r)=={'id','department','family','exposure','rules39','LLM03'}
        assert all(set(r[m])==set(DIMS) and all(type(v) is int and v in (0,1) for v in r[m].values()) for m in METHODS)
    eligible=[r for r in rows if r['exposure']=='remaining'];assert len(eligible)==1444
    st=strata(eligible)
    allocs={'negative50pct':allocation(st,.5),'negative85pct':allocation(st,.85),
            'negative95pct':allocation(st,.95),'census':allocation(st,1.)}
    # Exactly one selected proposal; cheaper allocations remain comparisons only.
    selected='census'
    scenario=[]
    for dim in DIMS:
        for prevalence in [.01,.03,.05,.10,.20,.50]:
            T=round(len(eligible)*prevalence)
            for signal in [.25,1.,20.]:
                joint,method_cells=machine_scenario(eligible,dim,T,signal)
                entry={'dimension':dim,'T':T,'prevalence':T/len(eligible),
                       'reference_odds_multiplier_per_auxiliary_positive':signal,
                       'joint_synthetic_counts':joint,
                       'allocation_results':{}}
                for key,ns in allocs.items():
                    entry['allocation_results'][key]={m:summarize(method_cells[m],ns) for m in METHODS}
                # Count-tail: same reference stratum totals for both methods.
                Ts={h:sum(c[i] for i in [0,2]) for h,c in method_cells['rules39'].items()}
                entry['reference_count_shortfall_probabilities']={
                    key:{str(minimum):positive_count_tail([(h['N'],Ts[h['key']],ns[h['key']]) for h in st],minimum)
                         for minimum in [1,10,22,40,62,97]} for key,ns in allocs.items()}
                scenario.append(entry)
    selected_rows=[]
    for h in st:
        n=allocs[selected][h['key']]
        selected_rows.append({**h,'n':n,'pi':n/h['N'],'weight':h['N']/n,'census':n==h['N']})
    selected_plan={
        'status':'one_fixed_proposal__not_final_human_or_sampling_execution_freeze',
        'selected_allocation':selected,'N':1444,'n':sum(allocs[selected].values()),
        'inference_scope':'Only the frozen remaining1444 finite population; 3037 exposed/developed IDs have pi=0 in this plan.',
        'stratum_rule':'department × (rules39_I,LLM03_I,rules39_F,LLM03_F); 0000 split into other S/E/Ec auxiliary-positive vs both-method all-five-negative. NA would be separate positive-probability layer; actual frozen labels have no NA.',
        'IF_signature_order':['rules39_I','LLM03_I','rules39_F','LLM03_F'],
        'strata':selected_rows,
        'department_n':{g:sum(h['n'] for h in selected_rows if h['department']==g) for g in ORDER},
        'future_machine_outputs':'Historical auxiliaries do not bind final label margins. Selected census also covers all future prediction changes and disagreements.',
        'human_workload':{'two_people_unit_readings':2*sum(allocs[selected].values()),
                          'first_decision_dimension_entries':10*sum(allocs[selected].values()),
                          'adjudication_unit_max':sum(allocs[selected].values())},
        'remaining_unselected_units':1444-sum(allocs[selected].values()),
        'design_notes':['No actual sample IDs drawn, no seed chosen, no text distributed.',
                        'All batches fixed before answers; no result-dependent expansion or stopping.',
                        'Census has no sampling randomization. Human presentation order can later be randomized; that is not probability sampling.',
                        'Reference missingness or unknown is reported separately, not filled as zero or silently dropped.',
                        'The selected finite-population census consumes the current remaining pool for this version; there is no unused holdout reserve.']}
    full_st=strata(rows,True)
    full_plan={
        'purpose':'Independent current-human audit of ALL4481 finite-corpus labels and content/attention totals; developed material remains developed.',
        'N':4481,'n':4481,'selection':'census; every nonempty department×exposure×auxiliary layer has pi=1',
        'strata':[{**h,'n':h['N'],'pi':1,'weight':1} for h in full_st],
        'department_n':{g:sum(h['N'] for h in full_st if h['department']==g) for g in ORDER},
        'exposure_n':dict(Counter(r['exposure'] for r in rows)),
        'two_person_unit_readings':8962,'first_decision_dimension_entries':44810,
        'reuse_condition':'Same manual/material versions, same genuine independent submissions/adjudication can serve both purposes; retain separate remaining and exposed domain results. Remaining census adds no duplicate readings.',
        'incremental_two_person_readings_after_remaining_census':6074,
        'scope_limit':'Full finite-corpus audit is not an unseen/generalization claim. Any other fixed positive-probability design must be separately locked before answers.'}
    candidate_summary=[]
    for key,ns in allocs.items():
        tails=zero_error_upper([(h['N'],ns[h['key']]) for h in st if h['tag']=='ALL_NEG'])
        widths={metric:0. for metric in ['kappa','precision','recall','F1']}
        worst={}
        for s in scenario:
            for m,res in s['allocation_results'][key].items():
                for metric,x in res['metrics'].items():
                    v=x['linearized_95_halfwidth']
                    if v is not None and v>=widths[metric]:
                        widths[metric]=v;worst[metric]={'dimension':s['dimension'],'T':s['T'],'signal':s['reference_odds_multiplier_per_auxiliary_positive'],'method':m,'point':x['point']}
        candidate_summary.append({'key':key,'N':1444,'n':sum(ns.values()),
                                  'department_n':{g:sum(ns[h['key']] for h in st if h['department']==g) for g in ORDER},
                                  'worst_linearized_95_halfwidth_on_prespecified_grid':widths,
                                  'worst_scenario':worst,'zero_hidden_positive_guard':tails,
                                  'role':'Selected fixed proposal' if key==selected else 'Planning comparison only, never an adaptive fallback'})
    feasibility={}
    for d in DIMS:
        Ms=[sum(r[m][d] for r in eligible) for m in METHODS]
        intervals={m:[math.ceil(.8*M-1e-12),math.floor(M/.8+1e-12)] for m,M in zip(METHODS,Ms)}
        lo=max(v[0] for v in intervals.values());hi=min(v[1] for v in intervals.values())
        J=sum(r['rules39'][d]==1 and r['LLM03'][d]==1 for r in eligible)
        feasibility[d]={'old_prediction_positive_margins':dict(zip(METHODS,Ms)),
                        'necessary_T_ranges_for_each_P_and_R_point_ge80':intervals,
                        'common_T_necessary_range':None if lo>hi else [lo,hi],
                        'fixed_joint_table_feasibility':joint_PR_feasibility(len(eligible),Ms[0],Ms[1],J),
                        'sufficient':False,'applies_to':'frozen OLD prediction tables only; not future revised methods'}
    results={'date':'2026-10-10','selected_remaining_plan':selected_plan,'separate_full_corpus_plan':full_plan,
             'planning_comparisons':candidate_summary,'old_prediction_point_target_feasibility':feasibility,
             'sources_binding_sha256':sha(HERE/'source-bindings.json'),
             'auxiliary_projection_sha256':sha(p),
             'script_sha256':sha(Path(__file__)),
             'project_targets':{'human_per_dimension_Cohen_kappa_point':.80,
                                'each_machine_per_dimension_kappa_precision_recall_F1_point':.80,
                                'CI_lower_bound_gate_added':False},
             'precision_choices':{'reference_scope':'fixed finite population conditional on reference decisions',
                                  'planning_desired_marginal95_halfwidth':.10,
                                  'selected_census_sampling_halfwidth':0,
                                  'semantic_reference_or_superpopulation_uncertainty_covered':False},
             'equal_weight_denominator_illustrations':denominator_examples(),
             'scenario_count':len(scenario),
             'scenario_limits':['Scenarios are integer joint counts, not actual human labels or estimated performance.',
                                'Finite actual machine joint margins are retained in every scene; reference total common to two methods.',
                                'No independent choosing of prevalence, P and R that violates M_positive=TP+FP.',
                                'Linearization is a planning approximation, especially weak at rare/zero cells; not a coverage guarantee.',
                                'Reference positivity from .01 to .50 and both informative, neutral and reversed auxiliary signal are sensitivity choices, not claimed priors.'],
             'human_kappa_scenarios':human_scenarios(st,allocs)}
    save(HERE/'strata-planning.json',results)
    save(HERE/'scenario-error-tables.json',{'synthetic_not_observed':True,'scenarios':scenario})
    print(json.dumps({'selected_remaining_n':selected_plan['n'],'stratum_count':len(st),
                      'candidate_summary':candidate_summary,'old_prediction_feasibility':feasibility,
                      'outputs':['strata-planning.json','scenario-error-tables.json']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
