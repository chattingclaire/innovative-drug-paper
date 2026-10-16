"""Meaningful finite-design/synthetic-table and old-delivery preservation QA.
Reads only permitted metadata/method files; never runs a sample or model.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from itertools import combinations
from datetime import datetime,timezone
import hashlib,json,sys,platform
import numpy as np
import scipy
import full_domain_plan as p
HERE=Path(__file__).resolve().parent
CHECKS=[]
def check(name,ok,detail=None):
    if not ok:raise AssertionError(name+' '+str(detail))
    CHECKS.append({'name':name,'status':'passed','details':detail})
def exact(cells):
    a,b,c,d=map(Fraction,cells);N=a+b+c+d
    if not N:return dict.fromkeys(('kappa','precision','recall','F1'))
    po=(a+d)/N;pe=((a+b)*(a+c)+(c+d)*(b+d))/N**2
    return {'kappa':None if pe==1 else (po-pe)/(1-pe),'precision':None if a+b==0 else a/(a+b),
            'recall':None if a+c==0 else a/(a+c),'F1':None if 2*a+b+c==0 else 2*a/(2*a+b+c)}
def reconstruct(scene,method):
    out=defaultdict(lambda:[0,0,0,0]);predkey={'rules39':'old_rules39','LLM03':'old_LLM03'}[method]
    for x in scene['joint_micro_counts']:
        z=out[x['stratum']];t=x['synthetic_reference_positive'];N=x['capacity']
        if x[predkey]==1:z[0]+=t;z[1]+=N-t
        else:z[2]+=t;z[3]+=N-t
    return out
def main():
    allocation=json.loads((HERE/'full-domain-allocation.json').read_text())
    comparison=json.loads((HERE/'full-domain-comparison.json').read_text())
    binding=json.loads((HERE/'source-bindings.json').read_text())
    rows,prior,_=p.read_inputs()
    check('original_inputs_and_600_deliveries_preserved',all(p.sha(Path(f))==v['sha256'] for f,v in binding['inputs'].items()))
    check('allocation_SHA_bound_by_comparison',comparison['allocation_sha256']==p.sha(HERE/'full-domain-allocation.json'))
    check('final_main_script_SHA_bound',comparison['script_sha256']==binding['script_sha256']==p.sha(HERE/'full_domain_plan.py'))
    check('expected90_machine_and36_human_scenes',len(comparison['machine_synthetic_scenarios'])==90 and len(comparison['human_synthetic_scenarios'])==36)
    check('full_scope_positive_pi_and_valid_non_census_n',all(h['pi']>0 and (h['n']>=2 or h['n']==h['N']) for plan in allocation['plans'].values() for h in plan['strata']))
    check('remaining23_layers_unchanged',all({h['prior_remaining_key']:(h['N'],h['n']) for h in plan['strata'] if h['domain']=='remaining'}=={h['key']:(h['N'],h['n']) for h in prior['strata']} for plan in allocation['plans'].values()))
    # An independent exact finite-population covariance oracle via ALL56 samples.
    N,n=8,3;pop=[0,0,0,1,1,2,3,3];totals=[]
    for ix in combinations(range(N),n):
        raw=np.bincount([pop[i] for i in ix],minlength=4);totals.append(raw*N/n)
    centered=np.asarray(totals)-np.mean(totals,axis=0)
    V=centered.T@centered/len(totals)
    check('exhaustive56_SRS_samples_anticipated_FPC_covariance',np.max(np.abs(V-p.anticipated_covariance([3,2,1,2],3)))<1e-12)
    # Independent Fraction central derivatives at a non-symmetric legal table.
    cells=[8,2,4,6];err={}
    for met,(_,g) in p.metric_grad(cells).items():
        approx=[]
        for j in range(4):
            left=[Fraction(x) for x in cells];right=left[:];step=Fraction(1,100000)
            left[j]-=step;right[j]+=step
            approx.append(float((exact(right)[met]-exact(left)[met])/(2*step)))
        err[met]=float(np.max(np.abs(g-approx)))
    check('four_metric_gradients_independent_fraction_difference',max(err.values())<1e-10,err)
    scene_table_count=0;worst_point_error=0.;worst_remaining_difference=0.;worst_cov_additivity=0.;worst_variance_increase=0.
    for s in comparison['machine_synthetic_scenarios']:
        dim=s['dimension'];micro=Counter((p.unit_stratum(r),r['rules39'][dim],r['LLM03'][dim]) for r in rows)
        check('joint_capacity_and_shared_reference_'+s['id'],all(type(x['synthetic_reference_positive']) is int and 0<=x['synthetic_reference_positive']<=x['capacity'] and micro[(x['stratum'],x['old_rules39'],x['old_LLM03'])]==x['capacity'] for x in s['joint_micro_counts']) and sum(x['synthetic_reference_positive'] for x in s['joint_micro_counts'])==s['synthetic_reference_positive_total'])
        for m in p.METHODS:
            by_h=reconstruct(s,m)
            for name,plan in allocation['plans'].items():
                for dom in ('ALL','remaining','exposed'):
                    result=s['allocation_results'][name][dom]['methods'][m]
                    hs=[h for h in plan['strata'] if dom=='ALL' or h['domain']==dom]
                    total=[sum(by_h[h['key']][j] for h in hs) for j in range(4)]
                    check('legal_cells_'+s['id']+'_'+m+'_'+name+'_'+dom,result['synthetic_four_a_b_c_d']==total and sum(total)==sum(h['N'] for h in hs) and total[0]+total[1]==sum(r[m][dim] for r in rows if dom=='ALL' or ('remaining' if r['exposure']=='remaining' else 'exposed')==dom))
                    for met,x in exact(total).items():
                        y=result['metrics'][met]['synthetic_population_point']
                        if x is None:check('NA_point_'+s['id']+'_'+m+'_'+name+'_'+dom+'_'+met,y is None)
                        else:worst_point_error=max(worst_point_error,abs(float(x)-y))
                    scene_table_count+=1
                allv=np.asarray(s['allocation_results'][name]['ALL']['methods'][m]['anticipated_four_cell_total_covariance'])
                part=sum((np.asarray(s['allocation_results'][name][dom]['methods'][m]['anticipated_four_cell_total_covariance']) for dom in ('remaining','exposed')),np.zeros((4,4)))
                worst_cov_additivity=max(worst_cov_additivity,float(np.max(np.abs(allv-part))))
            check('same_remaining_synthetic_results_'+s['id']+'_'+m,s['allocation_results']['full800']['remaining']['methods'][m]==s['allocation_results']['full1000']['remaining']['methods'][m])
            for dom in ('ALL','remaining','exposed'):
                vv=[np.asarray(s['allocation_results'][name][dom]['methods'][m]['anticipated_four_cell_total_covariance']) for name in ('full800','full1000')]
                worst_variance_increase=max(worst_variance_increase,max(0.,-float(np.linalg.eigvalsh(vv[0]-vv[1]).min())))
    check('all_synthetic_points_match_fraction_oracle',worst_point_error<1e-12,{'maximum_difference':worst_point_error})
    check('full_covariance_equals_sum_of_disjoint_domains',worst_cov_additivity<1e-8,{'maximum_difference':worst_cov_additivity})
    check('fixed_scene_larger_exposed_n_covariance_not_increased',worst_variance_increase<1e-8,{'negative_eigenvalue_numerical_error':worst_variance_increase})
    for s in comparison['human_synthetic_scenarios']:
        tables=s['synthetic_stratum_four_cells'];total=s['synthetic_total_four_a_b_c_d']
        st=allocation['plans']['full800']['strata']
        check('human_finite_legal_'+s['id'],all(len(tables[h['key']])==4 and all(type(x) is int and x>=0 for x in tables[h['key']]) and sum(tables[h['key']])==h['N'] for h in st) and [sum(tables[h['key']][j] for h in st) for j in range(4)]==total and total[0]+total[1]==s['A_positive'] and total[0]+total[2]==s['B_positive'])
        check('human_kappa_fraction_'+s['id'],abs(float(exact(total)['kappa'])-s['actual_finite_kappa'])<1e-12)
        check('human_remaining_unchanged_'+s['id'],s['allocation_results']['full800']['remaining']==s['allocation_results']['full1000']['remaining'])
    shift=comparison['future_prediction_auxiliary_shift_synthetic_example']
    check('shift_legal_population_and_positive_count_risk',shift['stratum_population_cells_TP_FP_FN_TN']==[41,9,9,761] and shift['allocation_results']['full800']['stratum_n']==30 and shift['allocation_results']['full1000']['stratum_n']==59 and shift['allocation_results']['full800']['full']['metrics']['precision']['synthetic_population_point']==.82)
    check('no_fake_reference_or_sample_selected',all(plan['final_selected_plan'] is False and plan['actual_sample_drawn'] is False and plan['actual_sampling_seed_selected'] is False for plan in allocation['plans'].values()) and allocation['sample_ID_drawn'] is False and allocation['new_machine_inference'] is False and allocation['new_human_reference_labels_created'] is False)
    out={'status':'passed','date':'2026-10-10','recorded_at_UTC':datetime.now(timezone.utc).isoformat(),'model':'GPT-6.1 Sol','reasoning_effort':'ultra',
        'check_count':len(CHECKS),'checks':CHECKS,'machine_domain_method_plan_tables_checked':scene_table_count,
        'main_script_sha256':p.sha(HERE/'full_domain_plan.py'),'allocation_sha256':p.sha(HERE/'full-domain-allocation.json'),
        'comparison_sha256':p.sha(HERE/'full-domain-comparison.json'),'QA_script_sha256':p.sha(__file__),
        'actual_ref_or_unseen_text_read':False,'actual_sample_drawn':False,'new_machine_run':False,
        'environment':{'Python':sys.version,'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform(),'new_dependencies_installed':False}}
    p.save('full-domain-QA.json',out)
    print(json.dumps({'status':'passed','check_count':len(CHECKS),'synthetic_machine_tables_checked':scene_table_count,'maximum_point_error':worst_point_error,'maximum_cov_additivity_difference':worst_cov_additivity,'maximum_covariance_monotonicity_numerical_error':worst_variance_increase},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
