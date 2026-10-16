"""Exhaustive small finite-population QA, entirely synthetic counts."""
import json, math, itertools, hashlib, sys
from pathlib import Path
import numpy as np
import scipy
import precision_plan as p

out={}
c=np.array([21.,4.,7.,68.]);errors={}
for key,(val,g) in p.metric_grad(c).items():
    numerical=[]
    for j in range(4):
        step=np.zeros(4);step[j]=1e-4
        numerical.append((p.metric_grad(c+step)[key][0]-p.metric_grad(c-step)[key][0])/(2e-4))
    errors[key]=float(max(abs(g-numerical)))
    assert errors[key]<1e-9
out['analytic_gradient_max_abs_error']=errors

labels=[0,0,1,2,3,3,3];n=3;N=len(labels)
totals=[]
for subset in itertools.combinations(range(N),n):
    count=np.bincount([labels[i] for i in subset],minlength=4)
    totals.append(count*N/n)
exact=np.cov(np.array(totals).T,bias=True)
derived=p.covariance([2,1,1,3],n)
out['enumerated_SRSWOR_total_covariance_max_abs_error']=float(abs(exact-derived).max())
assert out['enumerated_SRSWOR_total_covariance_max_abs_error']<1e-12

Nn=[(9,4),(7,3)];alpha=.025
best={}
for K1 in range(Nn[0][0]-Nn[0][1]+1):
    for K2 in range(Nn[1][0]-Nn[1][1]+1):
        prob=math.comb(9-K1,4)/math.comb(9,4)*math.comb(7-K2,3)/math.comb(7,3)
        best[K1+K2]=max(best.get(K1+K2,0),prob)
brute=max(K for K,pr in best.items() if pr>=alpha)
derived=p.zero_error_upper(Nn,alpha)
assert brute==derived['maximum_unseen_count']
out['zero_count_guard_bruteforce']=derived
out['NA_guards']={key:p.metric_grad([0,0,0,10])[key][0] for key in ['kappa','precision','recall','F1']}
assert all(v is None for v in out['NA_guards'].values())

plan=json.loads((p.HERE/'strata-planning.json').read_text())
tables=json.loads((p.HERE/'scenario-error-tables.json').read_text())['scenarios']
assert len(tables)==90
checks=0
for s in tables:
    j=s['joint_synthetic_counts']
    assert sum(x['N'] for x in j)==1444 and sum(x['reference_positive'] for x in j)==s['T']
    assert all(0<=x['reference_positive']<=x['N'] for x in j)
    for method,res in s['allocation_results']['census'].items():
        assert res['reference_positive_denominator']==s['T']
        assert all(v['linearized_95_halfwidth'] in (None,0) for v in res['metrics'].values())
        checks+=1
out['integer_joint_scenario_checks']=checks
selected=plan['selected_remaining_plan']
assert sum(h['n'] for h in selected['strata'])==sum(h['N'] for h in selected['strata'])==1444
assert all(h['pi']==1 and h['n']==h['N'] for h in selected['strata'])
assert selected['department_n']=={'NMPA':778,'NHSA':562,'NHC':104}
assert not plan['project_targets']['CI_lower_bound_gate_added']
assert len(plan['human_kappa_scenarios'])==36
for s in plan['human_kappa_scenarios']:
    A=s['A_positive'];B=s['B_positive'];N=1444
    amin=max(0,A+B-N);amax=min(A,B)
    kmin=p.metric_grad([amin,A-amin,B-amin,N-A-B+amin])['kappa'][0]
    kmax=p.metric_grad([amax,A-amax,B-amax,N-A-B+amax])['kappa'][0]
    expected=kmin-1e-12<=s['nominal_kappa']<=kmax+1e-12
    assert expected==s['nominal_kappa_feasible_at_these_margins']
out['human_unequal_margin_and_nominal_feasibility_checks']=36
assert sum(h['n'] for h in plan['separate_full_corpus_plan']['strata'])==4481
assert all(plan['old_prediction_point_target_feasibility'][d]['fixed_joint_table_feasibility']['both_methods_P_and_R_ge80_possible'] is False for d in ['I','F'])
out['fixed_selected_allocation_valid']=True
out['source_hashes_current']={key:hashlib.sha256(Path(info['path']).read_bytes()).hexdigest()==info['sha256']
                             for key,info in json.loads((p.HERE/'source-bindings.json').read_text())['sources'].items()}
core={'adoption_record','frame','exposure','rules39','LLM03'}
assert all(out['source_hashes_current'][k] for k in core)
out['parallel_review_document_updates_recorded_separately']=[k for k,v in out['source_hashes_current'].items() if not v]
assert set(out['parallel_review_document_updates_recorded_separately']) <= {'exposure_audit','design_json','design_md'}
assert (p.HERE/'supplemental-source-bindings.json').exists()
out['runtime']={'Python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__}
out['status']='all_checks_passed_no_text_no_actual_sample'
(p.HERE/'planning-QA.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
