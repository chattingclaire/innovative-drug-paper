"""Transparent synthetic arithmetic, probability-design, boundary and gate QA.
No project labels, unsealed pilots, source text, sample selection or inference.
"""
from pathlib import Path
from fractions import Fraction
from itertools import combinations,product
from copy import deepcopy
import json,math,sys,hashlib
import numpy as np
import scipy
from scipy.stats import hypergeom
from sklearn.metrics import cohen_kappa_score,precision_score,recall_score,f1_score,confusion_matrix
import sklearn
import metrics_engine as e

HERE=Path(__file__).resolve().parent
CHECKS=[]
def check(name,condition,details=None):
    if not condition:raise AssertionError(name+' '+str(details))
    CHECKS.append({'name':name,'status':'passed','details':details})
def completed(values,dimstatus=None):
    x={'status':'completed','labels':dict(zip(e.DIMS,values))}
    if dimstatus:x['dimension_status']=dimstatus
    return x
def toy():
    # Each named reference here is a SYNTHETIC test variable, not human truth.
    ab=[([1,0,1,0,1],[1,0,1,0,1]),([0,1,0,None,0],[0,1,0,1,0]),
        ([1,0,0,0,None],[0,0,0,0,None]),([0,0,0,0,0],[0,0,0,0,0]),
        ([0,1,1,1,0],[1,1,1,0,0]),([None,0,1,0,1],[1,0,0,0,1]),
        ([1,0,None,0,0],[None,0,None,0,0]),([0,1,0,0,1],[0,1,0,0,1])]
    rows=[]
    for i,(a,b) in enumerate(ab):
        hid,dept=('h1','NMPA') if i<4 else ('h2','NHSA') if i<7 else ('h3','NHC')
        out={'A':completed(a),'B':completed(b),'reference':completed(b),
             'rule':completed(a),'LLM':completed(b)}
        if i==1:out['rule']=completed(a,{'I':'execution_failure'})
        if i==2:out['LLM']={'status':'execution_failure','labels':None,'failure_code':'TOY_TECHNICAL_FAILURE'}
        if i==4:del out['LLM'] # No return is explicit process failure, not null.
        if i==5:out['B']=completed(b,{'F':'execution_failure'});out['B']['labels']['F']=None
        rows.append({'unit_id':f'SYNTHETIC-{i+1:02d}','stratum_id':hid,'department':dept,'outputs':out})
    return {'data_role':'synthetic','metadata':{'analysis_stage':'combined',
            'scope':{'kind':'synthetic_toy','population_N':18,'note':'Only synthetic test populations'},
            'design':{'kind':'stratified_srswor','sampling_unit':'source_unit',
                      'strata':[{'id':'h1','N':12,'n':4,'department':'NMPA'},
                                {'id':'h2','N':5,'n':3,'department':'NHSA'},
                                {'id':'h3','N':1,'n':1,'department':'NHC'}]}},'records':rows}
def perfect_numeric_toy(kind='stratified_srswor'):
    rows=[]
    for i,(a,b) in enumerate([(1,1)]*45+[(1,0)]*5+[(0,1)]*5+[(0,0)]*45):
        rows.append({'unit_id':f'SYNTHETIC-NUMERIC-{i:03d}','stratum_id':'census','department':'TOY',
                     'outputs':{'A':completed([a]*5),'B':completed([b]*5),
                                'reference':completed([b]*5),'rule':completed([a]*5),'LLM':completed([a]*5)}})
    return {'data_role':'synthetic','metadata':{'scope':{'kind':'synthetic_toy','population_N':100},
            'design':{'kind':kind,'strata':[{'id':'census','N':100,'n':100,'department':'TOY'}]}},'records':rows}
def expect_error(name,payload):
    try:e.prepare(payload)
    except e.DataError as exc:check(name,True,str(exc));return
    raise AssertionError(name+' did not reject')

def main():
    p=toy();prepared=e.prepare(p)
    result=e.analyze(p,replicates=2000,seed=20261010,guard_mode='joint_table')
    s=result['comparisons']['A_vs_B']['domains']['ALL']['S']
    check('human_S_hand_raw_cells',s['raw']['binary_four_order_a_b_c_d']==[1,1,1,3])
    check('human_S_hand_weighted_exact_cells',s['weighted_four_exact_fractions']==['3','3','5/3','7'])
    check('human_S_hand_kappa_raw_quarter',s['raw_metrics']['kappa']==.25)
    check('human_S_hand_kappa_weighted_36_over113',s['design_weighted_metrics']['kappa']==float(Fraction(36,113)))
    check('nine_grid_keeps_unknowns_and_pair_n',sum(map(sum,s['raw']['completed_0_1_null_3x3']))==8 and s['raw']['comparable_binary_total']==6 and s['raw']['one_or_both_semantic_null_no_failure']==2)
    check('marginal_positive_n_differs_from_paired_positive_n',s['raw']['left_all_assigned_state_totals']['1']==3 and s['raw']['left_comparable_positive_negative'][0]==2)
    check('dimension_unknown_does_not_drop_other_dimensions',result['comparisons']['A_vs_B']['domains']['ALL']['I']['raw']['comparable_binary_total']==7 and s['raw']['comparable_binary_total']==6)
    llm=result['attention']['LLM']['ALL']['S']
    check('nonreturn_and_execution_failure_distinct',llm['failure_process_subtypes']['missing_return']['raw_n']==1 and llm['failure_process_subtypes']['method_execution_failure']['raw_n']==1)
    ri=result['attention']['rule']['ALL']['I']
    check('dimension_failure_separate_from_semantic_null',ri['failure_process_subtypes']['dimension_execution_failure']['raw_n']==1 and ri['raw']['semantic_null']==0)
    check('failure_not_inside_nine_grid',result['comparisons']['LLM_vs_reference']['domains']['ALL']['S']['raw']['any_execution_failure']==2)
    json.dumps(result,allow_nan=False)
    check('output_JSON_has_no_NaN_or_infinite_numbers',True)

    # A frozen department can be fully observed within a noncensus overall design.
    dp=deepcopy(p);dp['metadata']['design']['strata'][2].update({'N':2,'n':2})
    dp['metadata']['scope']['population_N']=19
    extra=deepcopy(dp['records'][-1]);extra['unit_id']='SYNTHETIC-DEPARTMENT-CENSUS'
    extra['outputs']={m:completed([1]*5) for m in e.METHODS};dp['records'].append(extra)
    dr=e.analyze(dp,replicates=100,guard_mode='none')
    ds=dr['comparisons']['A_vs_B']['domains']['department:NHC']['S']
    check('frozen_department_census_keeps_defined_kappa_point_CI_inside_non_census_overall',
          not dr['design']['full_census_no_sampling_error'] and ds['domain_full_census_no_sampling_error']
          and ds['intervals']['kappa']['CI95']==[1.,1.])
    check('frozen_department_census_attention_no_sampling_error',
          dr['attention']['A']['department:NHC']['S']['known_coverage_CI']['CI95']==[.5,.5])
    for h in dp['metadata']['design']['strata']:h.pop('department')
    generic=e.analyze(dp,replicates=100,guard_mode='none')
    gs=generic['comparisons']['A_vs_B']['domains']['department:NHC']['S']
    check('observed_department_membership_alone_cannot_prove_population_census',
          not gs['domain_full_census_no_sampling_error'] and gs['intervals']['kappa']['CI95'] is None)
    for name,call in (
        ('guard_fractional_category_rejected_before_integer_conversion',
         lambda:e.finite_category_guard(prepared,[.5]+[0]*7)),
        ('guard_invalid_joint_state_rejected_before_integer_conversion',
         lambda:e.joint_table_guard(prepared,[16.5]+[0]*7)),
        ('guard_wrong_indicator_length_rejected',
         lambda:e.finite_category_guard(prepared,[0]))):
        try:call()
        except e.DataError:check(name,True)
        else:raise AssertionError(name+' did not reject')

    # Independent sklearn orientation: sklearn rows=true/reference, columns=prediction.
    cells=[21,4,7,68];pred=[1]*25+[0]*75;ref=[1]*21+[0]*4+[1]*7+[0]*68
    got=e.exact_metrics(cells)
    independent={'kappa':cohen_kappa_score(ref,pred),
                 'Precision':precision_score(ref,pred),'Recall':recall_score(ref,pred),
                 'F1':f1_score(ref,pred),'Specificity':recall_score(ref,pred,pos_label=0),
                 'NPV':precision_score(ref,pred,pos_label=0)}
    errors={k:abs(float(got[k])-v) for k,v in independent.items()}
    check('independent_sklearn_unequal_FP_FN_orientation',max(errors.values())<1e-14,errors)
    check('sklearn_confusion_transpose_direction',confusion_matrix(ref,pred,labels=[1,0]).T.tolist()==[[21,4],[7,68]])
    check('Specificity_and_NPV_named_correctly',got['Specificity']==Fraction(17,18) and got['NPV']==Fraction(68,75))
    allneg=e.exact_metrics([0,0,0,9]);one=e.exact_metrics([0,2,0,7])
    check('no_NA_to_one',allneg['kappa'] is None and allneg['Precision'] is None and allneg['Recall'] is None and allneg['F1'] is None and allneg['Po']==1 and allneg['Pneg']==1)
    check('F1_zero_can_exist_when_Recall_NA',one['Recall'] is None and one['F1']==0)
    check('Ppos_equals_F1_algebra_not_role',got['Ppos']==got['F1'])

    # Every metric gradient checked by a separate numerical derivative.
    c=np.array(cells,dtype=float);g=e.metric_gradients(c);gerr={}
    for metric,gradient in g.items():
        numerical=[]
        for j in range(4):
            step=np.zeros(4);step[j]=1e-4
            numerical.append((e.vector_metrics(c+step)[metric][0]-e.vector_metrics(c-step)[metric][0])/2e-4)
        gerr[metric]=float(np.max(np.abs(gradient-numerical)))
    check('all10_analytic_gradients',max(gerr.values())<1e-9,gerr)

    # Exact finite SRS variance, not a mirrored implementation test.
    pop=np.array([[0.,1.],[1.,0.],[2.,1.],[3.,3.],[5.,2.]])
    N,n=5,3;totals=[];estimated=[]
    for ix in combinations(range(N),n):
        x=pop[list(ix)];totals.append(N*x.mean(axis=0))
        centered=x-x.mean(axis=0);estimated.append(N*N*(1-n/N)*(centered.T@centered/(n-1))/n)
    between=np.cov(np.array(totals).T,bias=True)
    centered=pop-pop.mean(axis=0);analytic=N*N*(1-n/N)*(centered.T@centered/(N-1))/n
    check('all10_original_samples_exact_SRS_covariance',np.max(np.abs(between-analytic))<1e-12)
    check('average_sample_variance_unbiased',np.max(np.abs(np.mean(estimated,axis=0)-between))<1e-12)
    # Enumerate all3^2 conditional Rao-Wu draws for one known sample.
    sample=pop[[0,2,4]];rep=[]
    for draws in product(range(n),repeat=n-1):
        k=np.bincount(draws,minlength=n)
        factor=1+math.sqrt(1-n/N)*(n*k/(n-1)-1)
        rep.append(N/n*(factor@sample))
    rep=np.array(rep);point=N*sample.mean(axis=0)
    conditional=(rep-point).T@(rep-point)/len(rep)
    centered=sample-sample.mean(axis=0);expected=N*N*(1-n/N)*(centered.T@centered/(n-1))/n
    check('all9_conditional_rescaled_draws_exact_FPC_covariance',np.max(abs(conditional-expected))<1e-12)
    # Test actual engine generator, common weights and census unit against analytic covariance.
    W=e.rao_wu_weights(prepared,replicates=60000,seed=17)
    X=np.array([[0.,1.],[1.,0.],[3.,1.],[2.,2.],[4.,0.],[0.,3.],[2.,1.],[1.,0.]])
    point=prepared['weights']@X;deviation=W@X-point;mc=deviation.T@deviation/len(W)
    V=e.analytic_covariance(prepared,X)
    rel=float(np.max(abs(mc-V))/np.max(abs(V)))
    check('actual60000_RW_replicates_match_analytic_FPC',rel<.03,{'max_scaled_difference':rel,'analytic':V.tolist(),'MC':mc.tolist()})
    check('every_stratum_total_weight_fixed',all(np.allclose(W[:,prepared['stratum_ids']==hid].sum(axis=1),h['N']) for hid,h in prepared['strata'].items()))
    check('singleton_census_weight_fixed',np.all(W[:,-1]==1))
    check('shared_weights_cross_covariance_preserved',np.max(abs(e.analytic_covariance(prepared,np.column_stack([X[:,0],X[:,0]]))-np.full((2,2),V[0,0])))<1e-12)
    calls=[];original=e.rao_wu_weights
    def spy(*a,**kw):calls.append(1);return original(*a,**kw)
    e.rao_wu_weights=spy
    try:e.analyze(p,replicates=20,seed=9,guard_mode='none')
    finally:e.rao_wu_weights=original
    check('one_unit_weight_draw_shared_all_methods_dimensions',len(calls)==1)

    # Hypergeometric parameter intervals: coverage across every finite count.
    worst=1.;cases=0
    for N in range(2,13):
        for n in range(1,N+1):
            intervals=[e.finite_count_interval(N,n,x) for x in range(n+1)]
            for T in range(N+1):
                cover=sum(hypergeom.pmf(x,N,T,n) for x,(lo,hi) in enumerate(intervals) if lo<=T<=hi)
                worst=min(worst,float(cover));cases+=1
    check('finite_parameter_CI_exact_coverage_not_outcome_quantiles',worst>=.95-1e-12,{'finite_N_n_T_cases':cases,'minimum_coverage':worst})
    check('zero_error_guard_not_zero',e.finite_count_interval(16,8,0)==[0,4])
    joint=s['finite_guard'];check('joint16_guard_explicit_family_and_no_metric_projection',len(joint['strata'][0]['cells'])==16 and joint['metric_projection_implemented'] is False and joint['not45_metric_joint_coverage'])
    check('undefined_replicates_not_silently_deleted',e._interval(.8,[.7,np.nan,.9],True,False)['CI95'] is None)
    check('degenerate_non_census_not_sufficient95',e._interval(1.,[1.,1.,1.],True,False)['CI95'] is None)
    check('census_zero_sampling_error_allowed',e._interval(1.,[1.,1.],True,True)['CI95']==[1.,1.])

    cases=json.loads((HERE/'independent-unknown/toy-boundary-cases.json').read_text())
    # Explicitly hand-check attention edge cases; independent full sweep separately hashed.
    h0=e.attention_bounds([0]*5,[2,0,0,0,0],2)
    check('H0_share_undefined_and_only_dimension_positive',h0['S']['known_hit_attention_share'] is None and h0['S']['unknown_share_bounds_conditional_on_positive_total_not_CI']==[1,1] and h0['E']['unknown_share_bounds_conditional_on_positive_total_not_CI']==[0,0] and h0['S']['zero_total_share_undefined_possible'])
    hnone=e.attention_bounds([0]*5,[0]*5,2)
    check('no_hits_or_unresolved_share_never_defined',hnone['S']['positive_total_share_possible'] is False and hnone['S']['unknown_share_bounds_conditional_on_positive_total_not_CI'] is None)
    hb=e.attention_bounds([2,1,0,0,0],[1,2,0,0,0],5)
    check('attention_marginal_bounds_hand',hb['S']['unknown_coverage_bounds_not_CI']==[.4,.6] and hb['S']['unknown_share_bounds_conditional_on_positive_total_not_CI']==[.4,.75])
    check('failure_in_unknown_mass',llm['design_weighted']['unresolved_total']==llm['design_weighted']['semantic_null']+llm['design_weighted']['execution_failure'])

    numeric=e.analyze(perfect_numeric_toy(),replicates=20,seed=1,guard_mode='none')
    check('exact80_point_target_no_rounding_gate',numeric['project_review']['all_numerical_point_targets_met'] and numeric['comparisons']['A_vs_B']['domains']['ALL']['S']['design_weighted_metrics']['kappa']==.8)
    check('numeric_pass_never_automatic_project_acceptance',numeric['project_review']['formal_acceptance'] is False and not numeric['project_review']['metadata_attestations_complete_for_project_review'])
    dev=e.analyze(perfect_numeric_toy('nonprobability'),replicates=20,seed=1,guard_mode='joint_table')
    check('development_no_population_CI',dev['design']['bootstrap_replicates']==0 and dev['comparisons']['A_vs_B']['domains']['ALL']['S']['intervals']['kappa']['CI95'] is None)
    check('development_numeric_pass_stays_descriptive',dev['project_review']['all_numerical_point_targets_met'] and not dev['project_review']['metadata_attestations_complete_for_project_review'])
    # Noncensus singleton, labels, actual project unsealed, ID/projection tampering.
    singleton=deepcopy(p);singleton['metadata']['design']['strata'][2]['N']=2
    expect_error('noncensus_singleton_rejected',singleton)
    boolean=deepcopy(p);boolean['records'][0]['outputs']['A']['labels']['S']=True
    expect_error('boolean_not_binary_integer_label',boolean)
    unsealed=deepcopy(p);unsealed['data_role']='sealed_project';unsealed['metadata']['input_seals']={m:{'sealed':'false','sha256':'a'*64} for m in e.METHODS}
    expect_error('string_false_seal_rejected_before_labels',unsealed)
    idbad=deepcopy(p);idbad['records'][0]['unit_id']=''
    expect_error('empty_unit_id_rejected',idbad)
    fake=deepcopy(p);fake['metadata']['identities']={'A':{'kind':'human','verified':'false','independent_initial':'false','identity_code':'a'},'B':{'kind':'human','verified':True,'independent_initial':True,'identity_code':'b'},'reference':{'kind':'human_adjudication','credible':'false','blinded_to_machines':'false'}}
    eligibility=e.review_eligibility(e.prepare(fake),True)
    check('identity_truthiness_and_missing_reference_code_not_accepted',any('A is not' in x for x in eligibility['prerequisite_gaps']) and any('Reference adjudicator identity' in x for x in eligibility['prerequisite_gaps']))
    # Only a transparent synthetic projection can exercise the sealed-input gate.
    sealed=deepcopy(p);sealed['data_role']='sealed_project'
    sealed['metadata']['scope']['kind']='synthetic_toy'
    sealed['metadata']['design']['assigned_ids_sha256']=e.canonical_hash(sorted(r['unit_id'] for r in sealed['records']))
    sealed['metadata']['input_seals']={m:{'sealed':True,'sha256':'b'*64,'joined_projection_sha256':e.projection_hash(sealed['records'],m)} for m in e.METHODS}
    check('synthetic_only_exercise_joined_seal_validation',e.prepare(sealed)['role']=='sealed_project')
    sealed['records'][0]['outputs']['A']['labels']['S']=0
    expect_error('sealed_projection_tamper_rejected',sealed)

    # Save only explicitly named SYNTHETIC artifacts, never a new gold standard.
    (HERE/'synthetic-toy-input.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
    (HERE/'synthetic-toy-output.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (HERE/'synthetic-numeric-target-example.json').write_text(json.dumps({'synthetic_only':True,'project_review':numeric['project_review'],'numeric_targets':numeric['numeric_targets']},ensure_ascii=False,indent=2)+'\n')
    env={'Python':sys.version,'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__}
    out={'status':'passed','date':'2026-10-10','model':'GPT-6.1 Sol','reasoning_effort':'ultra',
         'checks':CHECKS,'check_count':len(CHECKS),'environment':env,
         'engine_sha256':e.sha256(HERE/'metrics_engine.py'),'checks_script_sha256':e.sha256(__file__),
         'actual_project_or_unsealed_labels_read':False,'source_text_or_context_read':False,
         'actual_ID_sampling_done':False,'new_machine_execution_done':False,
         'synthetic_reference_is_not_human_gold':True,
         'independent_artifacts':{f:e.sha256(HERE/f) for f in ['independent-math/independent_math_results.json','independent-unknown/toy-enumeration-result.json']}}
    (HERE/'engine-QA.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','check_count':len(CHECKS),'worst_hypergeometric_coverage':worst,'environment':env},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
