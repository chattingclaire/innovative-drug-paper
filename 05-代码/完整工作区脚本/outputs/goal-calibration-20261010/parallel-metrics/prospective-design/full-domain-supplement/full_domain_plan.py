"""Pre-answer full4481 probability-audit planning, never actual ID sampling.
Reads only the existing whitelist metadata/fixed old prediction projection and
prior remaining600 method allocations. Outputs only this new supplement folder.
No body/context/gold labels, new inference, source packet, or final sample seed.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from itertools import combinations
import argparse,hashlib,json,math
import numpy as np
from scipy.stats import hypergeom

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent
DIMS=('S','E','Ec','I','F');METHODS=('rules39','LLM03');DEPTS=('NMPA','NHSA','NHC')
FACTORS={'1_I_DISAGREEMENT':6,'2_F_DISAGREEMENT':5,'3_OTHER_DISAGREEMENT':3,
         '4_IF_AGREE_POS':3,'5_OTHER_AGREE_POS':2,'6_ALL_NEG':1}
Z=1.959963984540054
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):
    (HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def canonical_sha(obj):
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def remaining_key(r):
    sig=''.join(str(r[m][d]) for d in ('I','F') for m in METHODS)
    if sig!='0000':tag='IF'
    elif any(r['rules39'][d]!=r['LLM03'][d] for d in ('S','E','Ec')):tag='OTHER_DISAGREEMENT'
    elif any(r[m][d] for m in METHODS for d in ('S','E','Ec')):tag='OTHER_AGREE_POS'
    else:tag='ALL_NEG'
    return '|'.join((r['department'],sig,tag))
def exposed_tag(r):
    a,b=r['rules39'],r['LLM03']
    if a['I']!=b['I']:return '1_I_DISAGREEMENT'
    if a['F']!=b['F']:return '2_F_DISAGREEMENT'
    if any(a[d]!=b[d] for d in ('S','E','Ec')):return '3_OTHER_DISAGREEMENT'
    if any(r[m][d] for m in METHODS for d in ('I','F')):return '4_IF_AGREE_POS'
    if any(r[m][d] for m in METHODS for d in ('S','E','Ec')):return '5_OTHER_AGREE_POS'
    return '6_ALL_NEG'
def unit_stratum(r):
    if r['exposure']=='remaining':return 'remaining|'+remaining_key(r)
    return 'exposed|'+r['department']+'|'+exposed_tag(r)
def read_inputs():
    p=PRIOR/'inputs/metadata-and-fixed-labels.jsonl'
    bindings=json.loads((PRIOR/'source-bindings.json').read_text())
    if sha(p)!=bindings['projection']['sha256']:raise ValueError('Frozen projection hash mismatch')
    rows=[json.loads(x) for x in p.read_text().splitlines()]
    for r in rows:
        if set(r)!={'id','department','family','exposure','rules39','LLM03'}:raise ValueError('Whitelist schema only')
        if r['department'] not in DEPTS or r['exposure'] not in ('remaining','direct','family_only'):raise ValueError('Invalid metadata category')
        for m in METHODS:
            if set(r[m])!=set(DIMS) or any(type(v) is not int or v not in (0,1) for v in r[m].values()):raise ValueError('Invalid fixed auxiliary binary labels')
    if len(rows)!=4481 or len({r['id'] for r in rows})!=4481:raise ValueError('Full frame must be exactly4481 unique units')
    prior=json.loads((PRIOR/'small-plan-comparison.json').read_text())
    if prior['N']!=1444 or prior['n']!=600:raise ValueError('Do not substitute another remaining design')
    if prior.get('projected_inputs_sha256')!=sha(p):raise ValueError('Do not silently substitute a different pool/projection for the prior600 design')
    observed=Counter(remaining_key(r) for r in rows if r['exposure']=='remaining')
    if observed!={h['key']:h['N'] for h in prior['strata']}:raise ValueError('Remaining strata drifted')
    return rows,prior,bindings
def strata_for(rows,prior):
    counts=Counter(unit_stratum(r) for r in rows);out=[]
    for h in prior['strata']:
        out.append({'key':'remaining|'+h['key'],'prior_remaining_key':h['key'],
                    'domain':'remaining','department':h['department'],'tag':h['tag'],
                    'N':h['N'],'fixed_remaining_n':h['n'],'priority_multiplier':None})
    for key,N in sorted(counts.items()):
        if not key.startswith('exposed|'):continue
        _,dept,tag=key.split('|')
        out.append({'key':key,'domain':'exposed','department':dept,'tag':tag,'N':N,
                    'priority_multiplier':FACTORS[tag]})
    out.sort(key=lambda h:h['key'])
    if {h['key']:h['N'] for h in out}!=counts:raise ValueError('Full mutually exclusive stratum partition failed')
    return out
def exposed_allocate(strata,budget):
    """Deterministic capped maximum quotient, exact rational comparisons.
    Start min(2,N); each next slot maximizes N*factor/(current_n+1).
    Lexical key resolves exact ties. No true/reference or new prediction input.
    """
    st=[h for h in strata if h['domain']=='exposed']
    n={h['key']:min(2,h['N']) for h in st}
    if not sum(n.values())<=budget<=sum(h['N'] for h in st):raise ValueError('Budget outside feasible range')
    trace=[]
    while sum(n.values())<budget:
        eligible=[h for h in st if n[h['key']]<h['N']]
        h=min(eligible,key=lambda h:(-Fraction(h['N']*h['priority_multiplier'],n[h['key']]+1),h['key']))
        score=Fraction(h['N']*h['priority_multiplier'],n[h['key']]+1)
        n[h['key']]+=1
        trace.append({'slot':sum(n.values()),'stratum':h['key'],'new_n':n[h['key']],'winning_quotient_exact':str(score)})
    return n,trace
def build_plan(strata,budget):
    ns,trace=exposed_allocate(strata,budget);table=[]
    for h in strata:
        n=h['fixed_remaining_n'] if h['domain']=='remaining' else ns[h['key']]
        N=h['N'];pi=Fraction(n,N);w=Fraction(N,n)
        if not 0<n<=N or (n==1 and n!=N):raise ValueError('Every nonempty stratum needs positive pi and identifiable variance')
        pair=None if N==1 else Fraction(n*(n-1),N*(N-1))
        table.append({**h,'n':n,'pi':float(pi),'pi_exact':str(pi),'weight':float(w),'weight_exact':str(w),
                      'census':n==N,'same_stratum_pi_ij':None if pair is None else float(pair),
                      'same_stratum_pi_ij_exact':None if pair is None else str(pair)})
    cross=[]
    for a,b in combinations(table,2):
        q=Fraction(a['n'],a['N'])*Fraction(b['n'],b['N'])
        cross.append({'first_stratum':a['key'],'second_stratum':b['key'],'pi_ij':float(q),'pi_ij_exact':str(q)})
    n=600+budget
    return {'name':f'full{n}','population_N':4481,'assigned_n':n,'remaining_n':600,'exposed_n':budget,
            'strata':table,'exposed_increment_allocation_trace':trace,
            'cross_stratum_joint_second_order_probabilities':cross,
            'department_population_N':{g:sum(h['N'] for h in table if h['department']==g) for g in DEPTS},
            'department_n':{g:sum(h['n'] for h in table if h['department']==g) for g in DEPTS},
            'domain_department_n':{dom:{g:sum(h['n'] for h in table if h['domain']==dom and h['department']==g) for g in DEPTS} for dom in ('remaining','exposed')},
            'domain_N':{'remaining':1444,'exposed':3037},
            'minimum_unit_inclusion_probability':min(h['pi'] for h in table),'maximum_weight':max(h['weight'] for h in table),
            'weight_total_for_constant_one_exact':str(sum((Fraction(h['N'],h['n'])*h['n'] for h in table),Fraction(0))),
            'workload':{'two_independent_people_unit_readings':2*n,'five_dimension_first_decision_entries_two_people':10*n,
                        'reference_unit_audits':n,'machine_dimension_outputs_two_methods_one_fixed_run':10*n,
                        'additional_exposed_two_people_readings':2*budget,'additional_exposed_first_decision_entries':10*budget},
            'actual_sample_drawn':False,'actual_sampling_seed_selected':False,'final_selected_plan':False}
def allocation_output(rows,prior,bindings):
    st=strata_for(rows,prior);plans={f'full{600+b}':build_plan(st,b) for b in (200,400)}
    all_id_stratum=[{'id':r['id'],'stratum':unit_stratum(r)} for r in sorted(rows,key=lambda r:r['id'])]
    out={'status':'PREANSWER_FULL4481_DISJOINT_DOMAIN_PROBABILITY_AUDIT_COMPARISON_NOT_SELECTED_OR_EXECUTED',
         'date':'2026-10-10','model':'GPT-6.1 Sol','reasoning_effort':'ultra','population_N':4481,
         'population_department_N':dict(Counter(r['department'] for r in rows)),
         'exposure_metadata_counts':dict(Counter(r['exposure'] for r in rows)),
         'fixed_remaining_design_N':1444,'fixed_remaining_design_n':600,
         'exposed_domain_N':3037,'exposed_domain_definition':'direct2770 plus family_only267; all remain developed/exposed',
         'auxiliary_source_versions':{m:bindings['sources'][m] for m in METHODS},
         'permitted_input_projection':{'path':str(PRIOR/'inputs/metadata-and-fixed-labels.jsonl'),'sha256':sha(PRIOR/'inputs/metadata-and-fixed-labels.jsonl')},
         'prior_remaining_plan_sha256':sha(PRIOR/'small-plan-comparison.json'),
         'full_frame_stratum_assignment_hash_only':canonical_sha(all_id_stratum),
         'stratum_assignment_is_not_sample_selection':True,
         'exposed_stratification':'department x first applicable I disagreement / F disagreement / S,E,Ec disagreement / I,F agreed positive / other agreed positive / all-five both-method negative',
         'priority_factors':FACTORS,'allocation_rule':'Baseline min(2,N_h). Repeatedly add one slot to nonfull stratum maximizing exact N_h*priority/(n_h+1); lexical key breaks ties, until fixed budget200 or400. Same sequence; no reference labels or new model outputs used.',
         'allocation_rule_is_budget_heuristic_not_precision_optimality_claim':True,
         'joint_inclusion_contract':{'same_stratum':'n_h*(n_h-1)/(N_h*(N_h-1)) for distinct units when N_h>1',
                                     'different_strata':'(n_h/N_h)*(n_k/N_k) because all strata independent',
                                     'singleton':'n=N=1, pi=1; no distinct within-stratum pair exists'},
         'plans':plans,'no_new_point_or_CI_target':True,'new_human_reference_labels_created':False,
         'unseen_body_context_or_real_reference_read':False,'new_machine_inference':False,'sample_ID_drawn':False}
    return out
def bounded_counts(capacity,weights,total):
    """Only aggregate finite synthetic counts, never labels for real IDs.
    Logistic weighted allocation then deterministic largest-remainder rounding.
    """
    cap=np.asarray(capacity,dtype=int);w=np.asarray(weights,dtype=float)
    if type(total) is not int or not 0<=total<=int(cap.sum()):raise ValueError('Synthetic total outside capacity')
    if total==0:return np.zeros_like(cap)
    if total==int(cap.sum()):return cap.copy()
    lo,hi=-60.,60.;logw=np.log(w)
    for _ in range(100):
        mid=(lo+hi)/2;v=cap/(1+np.exp(np.clip(-(mid+logw),-700,700)))
        if v.sum()<total:lo=mid
        else:hi=mid
    a=np.floor(v).astype(int);left=total-int(a.sum())
    for i in sorted(range(len(cap)),key=lambda i:(-(v[i]-a[i]),i)):
        if left and a[i]<cap[i]:a[i]+=1;left-=1
    if left or int(a.sum())!=total or np.any(a>cap):raise ArithmeticError('Synthetic bounded rounding failed')
    return a
def metric_grad(cells):
    a,b,c,d=map(float,cells);N=a+b+c+d
    out={m:(None,None) for m in ('kappa','precision','recall','F1')}
    if not N:return out
    if a+b:out['precision']=(a/(a+b),np.array([b,-a,0.,0.])/(a+b)**2)
    if a+c:out['recall']=(a/(a+c),np.array([c,0.,-a,0.])/(a+c)**2)
    if 2*a+b+c:out['F1']=(2*a/(2*a+b+c),np.array([2*(b+c),-2*a,-2*a,0.])/(2*a+b+c)**2)
    po=(a+d)/N;u=(a+b)/N;v=(a+c)/N;pe=u*v+(1-u)*(1-v)
    if 1-pe>1e-14:
        k=(po-pe)/(1-pe)
        dpo=(np.array([1.,0.,0.,1.])-po)/N
        du=(np.array([1.,1.,0.,0.])-u)/N;dv=(np.array([1.,0.,1.,0.])-v)/N
        dpe=(2*v-1)*du+(2*u-1)*dv
        out['kappa']=(k,(dpo+(k-1)*dpe)/(1-pe))
    return out
def anticipated_covariance(cells,n):
    """Exact design covariance for a GIVEN synthetic finite population.
    Actual analysis estimates this from observed sample covariance, not these toys.
    """
    c=np.asarray(cells,dtype=float);N=c.sum()
    if N<=1 or n==N:return np.zeros((4,4))
    q=c/N;S=N/(N-1)*(np.diag(q)-np.outer(q,q))
    return N*N*(1-n/N)*S/n
def summarize(by_h,plan,domain='ALL'):
    hs=[h for h in plan['strata'] if domain=='ALL' or h['domain']==domain]
    total=np.sum([by_h[h['key']] for h in hs],axis=0)
    V=sum((anticipated_covariance(by_h[h['key']],h['n']) for h in hs),np.zeros((4,4)))
    metrics={}
    for name,(point,g) in metric_grad(total).items():
        se=None if g is None else math.sqrt(max(0.,float(g@V@g)))
        metrics[name]={'synthetic_population_point':point,'anticipated_linearization_SE':se,
                       'normal95_planning_halfwidth':None if se is None else Z*se}
    return {'synthetic_four_a_b_c_d':[int(x) for x in total],
            'population_N':int(total.sum()),'prediction_or_A_positive':int(total[0]+total[1]),
            'reference_or_B_positive':int(total[0]+total[2]),
            'anticipated_raw_reference_positive_observations':sum(h['n']*(by_h[h['key']][0]+by_h[h['key']][2])/h['N'] for h in hs),
            'anticipated_four_cell_total_covariance':V.tolist(),'metrics':metrics,
            'width_role':'Pre-answer linearization planning diagnostic for a synthetic finite count table; not actual data or the primary bootstrap CI.'}
def count_tail(hcounts,minimum):
    dist=np.array([1.])
    for N,T,n in hcounts:
        low=max(0,n-N+T);high=min(T,n);term=np.zeros(high+1)
        term[low:]=hypergeom.pmf(np.arange(low,high+1),N,T,n)
        dist=np.convolve(dist,term)
    return float(dist[:minimum].sum())
def machine_scene(rows,dim,T,signal):
    micro=Counter((unit_stratum(r),r['rules39'][dim],r['LLM03'][dim]) for r in rows)
    keys=sorted(micro);cap=[micro[k] for k in keys]
    refs=bounded_counts(cap,[signal**(k[1]+k[2]) for k in keys],T)
    by_method={m:defaultdict(lambda:[0,0,0,0]) for m in METHODS};joint=[]
    for (h,a,b),N,t in zip(keys,cap,refs):
        t=int(t);joint.append({'stratum':h,'old_rules39':a,'old_LLM03':b,'capacity':N,'synthetic_reference_positive':t})
        for m,pred in (('rules39',a),('LLM03',b)):
            cells=by_method[m][h]
            if pred:cells[0]+=t;cells[1]+=N-t
            else:cells[2]+=t;cells[3]+=N-t
    return joint,by_method
def make_machine_scenarios(rows,allocation):
    scenarios=[]
    for dim in DIMS:
        for prevalence in (.01,.03,.05,.10,.20,.50):
            T=round(4481*prevalence)
            for signal in (.25,1.,20.):
                joint,cells=machine_scene(rows,dim,T,signal);results={}
                for name,plan in allocation['plans'].items():
                    results[name]={}
                    for domain in ('ALL','remaining','exposed'):
                        hs=[h for h in plan['strata'] if domain=='ALL' or h['domain']==domain]
                        Ts={h['key']:cells['rules39'][h['key']][0]+cells['rules39'][h['key']][2] for h in hs}
                        results[name][domain]={'methods':{m:summarize(cells[m],plan,domain) for m in METHODS},
                            'raw_reference_positive_count_shortfall':{str(k):count_tail([(h['N'],Ts[h['key']],h['n']) for h in hs],k) for k in (1,5,10,20,40)}}
                scenarios.append({'id':f'{dim}|prev{prevalence}|signal{signal}', 'dimension':dim,
                    'reference_role':'one shared purely synthetic finite-count reference, no real-ID labels and no human gold',
                    'synthetic_reference_positive_total':T,'prevalence_grid':prevalence,
                    'aux_positive_reference_odds_factor':signal,'joint_micro_counts':joint,'allocation_results':results})
    return scenarios
def make_human_scenarios(allocation):
    st=allocation['plans']['full800']['strata'];N=4481;out=[]
    for prevalence in (.01,.03,.05,.10,.20,.50):
        A=round(N*prevalence)
        for unequal in (1.,1.25):
            B=round(A*unequal)
            for nominal in (.8,.85,.9):
                pe=(A*B+(N-A)*(N-B))/N**2
                requested_a=(N*(nominal*(1-pe)+pe)-N+A+B)/2
                a=min(A,B,max(0,A+B-N,round(requested_a)))
                total=[a,A-a,B-a,N-A-B+a]
                rest=np.array([h['N'] for h in st]);table=np.zeros((len(st),4),dtype=int)
                for j,amount in enumerate(total[:3]):
                    part=bounded_counts(rest,np.ones(len(st)),amount);table[:,j]=part;rest-=part
                table[:,3]=rest;by_h={h['key']:[int(x) for x in t] for h,t in zip(st,table)}
                out.append({'id':f'A{A}|B{B}|nominal{nominal}','role':'synthetic paired initial A/B decisions, neither is truth',
                    'A_positive':A,'B_positive':B,'requested_kappa':nominal,
                    'requested_kappa_feasible_at_margins':max(0,A+B-N)<=requested_a<=min(A,B),
                    'synthetic_total_four_a_b_c_d':total,'actual_finite_kappa':metric_grad(total)['kappa'][0],
                    'synthetic_stratum_four_cells':by_h,
                    'allocation_results':{name:{dom:summarize(by_h,plan,dom) for dom in ('ALL','remaining','exposed')} for name,plan in allocation['plans'].items()}})
    return out
def shifted_prediction_example(allocation):
    key='exposed|NHSA|6_ALL_NEG';population_cells=[41,9,9,761]
    plan=allocation['plans']['full800']
    by_h={h['key']:population_cells[:] if h['key']==key else [0,0,0,h['N']] for h in plan['strata']}
    out={'role':'Pure synthetic future prediction/reference count example; no labels assigned to actual IDs',
         'auxiliary_change':'Both frozen old machines predict0 in this stratum, but an imagined new frozen machine predicts50 positives, reference has50, overlap41.',
         'stratum':key,'stratum_population_cells_TP_FP_FN_TN':population_cells,'old_auxiliary_positive_in_stratum':0,
         'future_synthetic_prediction_positive':50,'synthetic_reference_positive':50,'allocation_results':{}}
    for name,plan in allocation['plans'].items():
        h=next(h for h in plan['strata'] if h['key']==key)
        out['allocation_results'][name]={'full':summarize(by_h,plan),
            'stratum_n':h['n'],'expected_raw_predicted_positive_observations':h['n']*50/820,
            'no_raw_prediction_positive_observed_probability':float(hypergeom.pmf(0,820,50,h['n'])),
            'no_raw_reference_positive_observed_probability':float(hypergeom.pmf(0,820,50,h['n'])),
            'raw_reference_positives_below5_probability':float(hypergeom.cdf(4,820,50,h['n']))}
    return out
def make_comparison(rows,allocation):
    machine=make_machine_scenarios(rows,allocation);human=make_human_scenarios(allocation)
    maxima={}
    for name in allocation['plans']:
        maxima[name]={}
        for dom in ('ALL','remaining','exposed'):
            maxima[name][dom]={}
            for dim in DIMS:
                maxima[name][dom][dim]={}
                for m in METHODS:
                    maxima[name][dom][dim][m]={}
                    for met in ('kappa','precision','recall','F1'):
                        entries=[(s['allocation_results'][name][dom]['methods'][m]['metrics'][met],s) for s in machine if s['dimension']==dim]
                        valid=[(v,s) for v,s in entries if v['normal95_planning_halfwidth'] is not None]
                        v,s=max(valid,key=lambda x:x[0]['normal95_planning_halfwidth'])
                        maxima[name][dom][dim][m][met]={'max_grid_halfwidth':v['normal95_planning_halfwidth'],
                            'synthetic_point_at_that_max':v['synthetic_population_point'],'scenario':s['id'],
                            'undefined_scenarios':sum(v['normal95_planning_halfwidth'] is None for v,s in entries)}
    rare=[]
    for name,plan in allocation['plans'].items():
        for h in plan['strata']:
            if h['tag'] not in ('6_ALL_NEG','ALL_NEG'):continue
            rare.append({'plan':name,'stratum':h['key'],'domain':h['domain'],'department':h['department'],
                'N':h['N'],'n':h['n'],'miss_all_hidden_positives_probability':{str(T):float(hypergeom.pmf(0,h['N'],T,h['n'])) for T in (1,2,5,10,20,50)}})
    return {'status':allocation['status'],'date':'2026-10-10','model':'GPT-6.1 Sol','reasoning_effort':'ultra',
        'allocation_file':'full-domain-allocation.json','allocation_sha256':sha(HERE/'full-domain-allocation.json'),
        'script_sha256':sha(__file__),'plans':{name:{k:v for k,v in plan.items() if k not in ('strata','cross_stratum_joint_second_order_probabilities','exposed_increment_allocation_trace')} for name,plan in allocation['plans'].items()},
        'population_old_auxiliary_positive_counts':{dom:{m:{dim:sum(r[m][dim] for r in rows if dom=='ALL' or ('remaining' if r['exposure']=='remaining' else 'exposed')==dom) for dim in DIMS} for m in METHODS} for dom in ('ALL','remaining','exposed')},
        'population_old_auxiliary_count_is_not_future_machine_truth':True,
        'scenario_scope':'all examples are aggregate legal finite counts, without actual-ID synthetic reference assignment',
        'actual_primary_CI_contract':'If this candidate design is later chosen and frozen, use common unit FPC-rescaled bootstrap5000 seed20261010 for actual marginal95 CI, linearization diagnostics secondary; zero/undefined safeguards and unknown tables remain required.',
        'planning_widths_are_not_actual_primary_CIs':True,'CI_halfwidth_or_lower_bound_gate_added':False,
        'machine_synthetic_scenarios':machine,'human_synthetic_scenarios':human,
        'machine_planning_grid_maxima':maxima,'both_old_auxiliary_negative_hidden_positive_risks':rare,
        'future_prediction_auxiliary_shift_synthetic_example':shifted_prediction_example(allocation),
        'interpretation':[
            'All4481 units have positive pi under either combined disjoint-domain design; remaining1444 retains its exact prior600 allocation.',
            'Developed3037 are audited current finite-corpus records; they are not unseen generalization or a new holdout.',
            'The full nonlinear metrics must be computed from summed weighted full-domain cells, never from averaging remaining/exposed kappas or ratios.',
            'Changing future machine predictions does not invalidate the frozen positive-probability design, but auxiliary enrichment efficiency can fall sharply.',
            'Synthetic covariance is an anticipated design quantity; zero observed cells, missing real reference and rare denominators need actual safeguards, not this scenario grid.',
            'The total800 or1000 observations are not800 or1000 predicted/ref positives; sparse classes and human positive disagreement may yield wide or undefined metrics.',
            'Budget400 increases each exposed n under the same deterministic count allocation sequence, not a permission for outcome-dependent200-to400 expansion.',
            'No sample IDs or sampling seed selected, no new machine run, no unseen text/context/ref labels read; no final scheme chosen and no numerical pass guarantee.'
        ]}
def render_report(allocation,comparison):
    lines=[]
    def add(s=''):lines.append(s)
    names={'NMPA':'药监','NHSA':'医保','NHC':'卫健'}
    tags={'1_I_DISAGREEMENT':'I两机分歧','2_F_DISAGREEMENT':'余项F分歧',
          '3_OTHER_DISAGREEMENT':'余项S/E/Ec分歧','4_IF_AGREE_POS':'余项I/F一致阳性',
          '5_OTHER_AGREE_POS':'余项其他一致阳性','6_ALL_NEG':'两机五维全阴性'}
    add('# 全4481有限语料审计：剩余600＋开发200/400两档规划')
    add('\n2026-10-10；GPT-6.1 Sol / ultra。仅使用已有白名单元数据、曝光归属和固定rules39/LLM03五维预测作辅助变量；不读未使用正文/语境或真实参照，不抽ID、不选抽样seed、不运行新机器、不新增真实参照。原剩余1444的600档全部23层N/n保持。两档均未被选择或实施。')
    add('\n**full800与full1000均为全4481的正概率审计候选方案。** 开发曝光3037另抽200或400，与剩余1444抽600互斥组合；开发域direct2770与family-only267均保留资格。这使全部4481具有正纳入概率，不能把开发曝光记录称为未见泛化。全域表现与剩余域表现分别报告；不能将剩余域结果重加权成全4481。')
    add('\n## 工作量与覆盖')
    add('\n| 方案 | 剩余域N/n | 开发域N/n | 全域N/n | 药监n | 医保n | 卫健n | 两人单位阅读 | 两人五维首判项 | 参照审计单位 |\n|---|---|---|---|---:|---:|---:|---:|---:|---:|')
    for name,plan in allocation['plans'].items():
        n=plan['department_n'];w=plan['workload']
        add(f"| {name} | 1444/600 | 3037/{plan['exposed_n']} | 4481/{plan['assigned_n']} | {n['NMPA']} | {n['NHSA']} | {n['NHC']} | {w['two_independent_people_unit_readings']} | {w['five_dimension_first_decision_entries_two_people']} | {w['reference_unit_audits']} |")
    add('\n在相同剩余600上，200档新增400次双人单位阅读、2000个首判项；400档新增800次阅读、4000个首判项。两个机器每条均输出五维，一个冻结主运行分别为8000/10000个机器维度输出。真人身份、独立首判、参照审计、执行失败与unknown仍须真实记录，预算条数不是完成证明。')
    add('\n全框部门N为药监1848、医保2100、卫健533；开发域N为1070/1538/429，剩余域N为778/562/104。开发域占3037/4481=67.8%，因此其低抽样率层可能主导全域不确定性；剩余600并不能消除这部分方差。')
    add('\n## 开发域固定层与整数分配')
    add('\n部门内依次判断I分歧、F分歧、S/E/Ec分歧、无分歧I/F阳性、其他共同阳性、双方五维全阴性；只取第一个满足的类，共18个非空层。direct与family-only都进入开发域，不把family-only删去。旧规则及LLM为已核固定版本，不能用新参照答案或未来错误来分层。')
    add('\n预设乘数分别6/5/3/3/2/1。各层先放min(2,N_h)（共35槽）；剩余预算逐槽分给尚未全取且精确商数N_h×乘数/(n_h+1)最大的层，商数平局按层key字典序。200档增加165槽，400档增加365槽。该透明预算启发式富集I/F及五维分歧、保留阴性信息，没有精度最优或过线保证；除单例必须全取外，不预设某类必须全核。完整逐槽轨迹可复算。')
    add('\n| 部门 | 互斥优先类 | N_h | n200 | pi200 | w200 | n400 | pi400 | w400 |\n|---|---|---:|---:|---:|---:|---:|---:|---:|')
    large={h['key']:h for h in allocation['plans']['full1000']['strata']}
    for h in sorted((h for h in allocation['plans']['full800']['strata'] if h['domain']=='exposed'),key=lambda h:(DEPTS.index(h['department']),h['tag'])):
        b=large[h['key']]
        add(f"| {names[h['department']]} | {tags[h['tag']]} | {h['N']} | {h['n']} | {h['pi']:.4f} | {h['weight']:.2f} | {b['n']} | {b['pi']:.4f} | {b['weight']:.2f} |")
    add('| **合计** | | **3037** | **200** | | | **400** | | |')
    add('\nremaining层均为原small-plan-comparison.json的23层，添加domain前缀而不改N/n；新增开发18层后共41层。所有非空层pi>0、所有非全取层n≥2，NHC I分歧单例n=N=1合法。两档开发全阴性层总样本63/125，占1747的3.61%/7.16%；部门各层pi约3.5%或7.0%，并非缺失抽样资格。')
    add('\n## 一阶、二阶概率与同设计估计')
    add('\n各层独立SRSWOR：pi_i=n_h/N_h、w_i=N_h/n_h。同层不同单位pi_ij=n_h(n_h−1)/[N_h(N_h−1)]；异层pi_ij=pi_i×pi_j。单例不存在同层不同单位对，不能计算0/0。JSON列明41层精确有理数及每档全部820对异层二阶概率。每次样本的HT常数总量Σ_h(n_h×w_h)=4481；剩余域为1444、开发域为3037。')
    add('\n每维先保留原始四格及0/1/null九格、执行失败，再按全部分配单位原权重求全域四格Ĉ=Σ_h(N_h/n_h)C_sample,h。剩余域只对其原23层求和；开发域只对18层求和。全域κ/P/R/F1由两域加权四格相加后求函数，不能平均两域κ或P/R/F1。unknown和失败仍带权重，二元指标只描述可比子域；全域未知率和关注度部分识别范围另报。')
    add('\n未来若选择并冻结此候选，应一次生成完整41层单位重复权重矩阵，所有方法、五维以及ALL/remaining/exposed/部门域都使用同一矩阵。主CI遵照v2共同FPC重缩放bootstrap5000、seed20261010；解析协方差与梯度为辅助诊断，逐指标95%不等于45项同时95%。现通用引擎已有全域和部门输出；正式采用两域设计前须将冻结stratum.domain映射接入域输出，或由同一份已生成重复权重作域掩码汇总，不能为每个指标或比较另重抽。该接口工作不构成本次已实施统计。')
    add('\n## 合成场景下的宽区间风险')
    add('\n90个机器场景保持实际旧两机联合容量及边际，以一个共同整数合成参照构造两机合法四格：全域正类比例网格1/3/5/10/20/50%，旧辅助阳性对参照的odds倍率.25/1/20。每个场景同时计算两档的全域、剩余域、开发域诊断；没有将合成参照分配给任何真实ID。36个人A/B场景分别含相同/不等阳性边际及请求κ=.8/.85/.9，实际整数κ另列，边际不能实现请求值时明示。')
    add('\n下面的半宽来自给定合成有限四格的FPC协方差与梯度，属于事前信息风险诊断，**不是实际主bootstrap CI、精确覆盖保证或验收门槛**。未截断超出指标范围的近似半宽；每个最大值可能来自不同场景，不组成一张同时可实现的最坏四格表。')
    add('\n| 全域方案 | 维度 | 旧辅助机器 | κ网格最大规划半宽 | P | R | F1 |\n|---|---|---|---:|---:|---:|---:|')
    for name in allocation['plans']:
        for dim in DIMS:
            for m in METHODS:
                x=comparison['machine_planning_grid_maxima'][name]['ALL'][dim][m]
                add(f"| {name} | {dim} | {m} | "+' | '.join(f"{x[k]['max_grid_halfwidth']:.3f}" for k in ('kappa','precision','recall','F1'))+' |')
    add('\n开发域旧I/F阳性未被全核，全4481的旧I/F P不能继承原剩余域的零抽样方差。S/E/Ec、R与人κ的分母/边际和错误位置也影响信息量。完全相同的合成剩余域四格在两档有相同N/n和协方差；新增开发样本提高全域信息，不增加剩余域独立信息。')
    add('\n| 合成人A/B阳性边际 | 实际有限κ | full800规划半宽 | full1000规划半宽 |\n|---|---:|---:|---:|')
    for A,B in ((45,45),(134,134),(224,280)):
        s=next(s for s in comparison['human_synthetic_scenarios'] if s['A_positive']==A and s['B_positive']==B and s['requested_kappa']==.8)
        widths=[s['allocation_results'][name]['ALL']['metrics']['kappa']['normal95_planning_halfwidth'] for name in allocation['plans']]
        add(f"| {A}/{B} | {s['actual_finite_kappa']:.6f} | {widths[0]:.3f} | {widths[1]:.3f} |")
    add('\n低阳性时总n800/1000仍可能只有少量正类或分歧实观单位，Recall/Precision可能NA，κ的Pe=1边界也会NA。较大权重的1个正类不能当作几十个独立阳性观察。真实缺失参照会进一步缩小可比信息；不能使用机器补成人工答案。')
    add('\n### 新机器与旧辅助失配：设计仍有效，效率可下降')
    x=comparison['future_prediction_auxiliary_shift_synthetic_example']
    add('\n明确的合法计数例：医保开发旧双全阴层N=820，想象新机器与参照各有50阳性、重叠41，层内TP/FP/FN/TN=(41,9,9,761)，其他层全TN。这不是实际标签。全域P=R=F1=.82，κ约'+f"{x['allocation_results']['full800']['full']['metrics']['kappa']['synthetic_population_point']:.4f}"+'；其信息来自200档该层n30或400档n59。')
    add('\n| 方案 | 该层n | 预计实观预测阳性 | 未观到任何预测阳性概率 | 参照阳性实观不足5概率 | P规划半宽 | R规划半宽 |\n|---|---:|---:|---:|---:|---:|---:|')
    for name,v in x['allocation_results'].items():
        met=v['full']['metrics']
        add(f"| {name} | {v['stratum_n']} | {v['expected_raw_predicted_positive_observations']:.2f} | {v['no_raw_prediction_positive_observed_probability']:.1%} | {v['raw_reference_positives_below5_probability']:.1%} | {met['precision']['normal95_planning_halfwidth']:.3f} | {met['recall']['normal95_planning_halfwidth']:.3f} |")
    add('\n新预测落在旧阴性低pi层不损正概率设计的HT总量有效性；比率指标仍是同设计比率估计，有限样本不声称严格无偏。旧辅助富集效果会下降，其实际P/R分母远小于总样本量。不能重分类后按新错误补容易题，也不能假定旧0就是新0。')
    add('\n| 开发域旧双全阴层 | N | n200/n400 | 藏20个未来正类：200档全漏 | 400档全漏 |\n|---|---:|---|---:|---:|')
    for g in DEPTS:
        rr=[r for r in comparison['both_old_auxiliary_negative_hidden_positive_risks'] if r['domain']=='exposed' and r['department']==g]
        a=next(r for r in rr if r['plan']=='full800');b=next(r for r in rr if r['plan']=='full1000')
        add(f"| {names[g]} | {a['N']} | {a['n']}/{b['n']} | {a['miss_all_hidden_positives_probability']['20']:.2%} | {b['miss_all_hidden_positives_probability']['20']:.2%} |")
    add('\n这些是给定合成层内正类数的精确Hypergeom零事件概率，不是实际错误率、CI或新的验收线。独立风险报告另给合法四格/样本例：总n800/1000仍可全负观察而κ/P/R/F1均NA；即使偶然只见1个TP、点值全为1，也不足以宣称总体没有隐藏错误。真实零格应报告完整状态/计数和有限总体guard；单类别guard不冒充联合指标95%区间。')
    add('\n## 选择、冻结和交付')
    add('\nGoal原有逐维点值目标不变：真实独立人κ，以及每个最终机器对可信参照的κ/P/R/F1≥.80。此处无census要求、CI下界线或半宽线，也不保证通过。800/1000是两档可供事前选择的工作量设计，不能在200档分数出现后按过线与否切换400档；新方案采用前还须冻结分配、抽样seed、名单/材料/手册/机器版本、真人安排和参照流程。')
    add('\n全部源输入SHA、41层N/n/pi/w、每档820组二阶概率、全框层归属的hash（不输出样本名单）、合法合成格数与方差诊断均保存在full-domain-allocation.json / full-domain-comparison.json。full_domain_plan.py可复现；用已有parallel-metrics/.venv运行，不安装依赖。新增独立算术、分配与风险报告位于本目录各independent-*子目录。所有新输出仅在full-domain-supplement，不改原剩余600/1444交付。')
    (HERE/'full-domain-comparison.md').write_text('\n'.join(lines)+'\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allocation-only',action='store_true');args=parser.parse_args()
    rows,prior,bindings=read_inputs();out=allocation_output(rows,prior,bindings)
    save('full-domain-allocation.json',out)
    save('source-bindings.json',{'status':'metadata_and_prior_design_only','date':'2026-10-10',
        'inputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in
                  (PRIOR/'inputs/metadata-and-fixed-labels.jsonl',PRIOR/'source-bindings.json',PRIOR/'small-plan-comparison.json',PRIOR/'small-plan-comparison.md',PRIOR/'small_plan.py')},
        'script_sha256':sha(__file__),'old_remaining_design_modified':False,'no_text_gold_sample_or_inference':True})
    if not args.allocation_only:
        comparison=make_comparison(rows,out);save('full-domain-comparison.json',comparison)
        render_report(out,comparison)
    print(json.dumps({'status':'allocation_planning_only' if args.allocation_only else 'full_comparison_planning_only','plans':{k:{'N':v['population_N'],'n':v['assigned_n'],'department_n':v['department_n'],'exposed_department_n':v['domain_department_n']['exposed']} for k,v in out['plans'].items()}},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
