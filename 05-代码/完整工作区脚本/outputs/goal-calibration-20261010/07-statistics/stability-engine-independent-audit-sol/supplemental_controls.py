#!/usr/bin/env python3
"""Small repair regressions for intended accepted inputs and pending audit concerns."""
import copy
import json
from fractions import Fraction as F
from pathlib import Path
import audit_controls as a
from independent_fixture import DIMS, RUNS, encoded, write_ref, objsha, seal_inputs

engine=a.load_engine(a.BASE/'repair-candidate/stability_engine.py')
base_report=a.report(engine,a.BASE/'inputs/independent-eleven')

def valid_census(value,name):
    folder,reg,led=a.clone('supplemental-'+name)
    reg['sample'].update(selection_mode='census',weight_kind='equal')
    for row in reg['sample']['assigned_records']:row['weight']=1;row['inclusion_probability']=value
    a.complete_rebind(reg,led);seal_inputs(folder,reg,led)
    r=a.report(engine,folder);assert r['sampling']['selection_mode']=='census'
    assert r['three_main_runs']['five_dimension_vector']['weighted_denominator']==4
    return {'valid_census_numeric_pi':value,'joint_C5_weight':4}
a.check('repair_preserves_numeric_census_pi_1',lambda:valid_census(1,'census-integer-one'))
a.check('repair_preserves_exact_rational_census_pi_1',lambda:valid_census('1/1','census-rational-one'))

def count_three_point_zero():
    folder,reg,led=a.clone('supplemental-legal-numeric-three-point-zero')
    reg['retry_policy']['max_actual_attempts']=3.0
    seal_inputs(folder,reg,led);r=a.report(engine,folder)
    assert r['production_firsts']['AUDIT-003']['attempt_number']==2
    return {'accepted_numeric_count':3.0,'flags_are_JSON_booleans':True,'maximum_actual_attempts_unchanged':3}
a.check('repair_preserves_numeric_const_3_semantics_without_unrelated_scope_change',count_three_point_zero)

def weight_scaling():
    folder,reg,led=a.clone('supplemental-weight-scale-seven')
    for row in reg['sample']['assigned_records']:row['weight']=str(F(row['weight'])*7)
    a.complete_rebind(reg,led);seal_inputs(folder,reg,led);r=a.report(engine,folder)
    for name,p in base_report['paired_comparisons'].items():
        x=r['paired_comparisons'][name]
        for d in DIMS:
            for key in ['Po','Pe','kappa']:
                old=p['dimensions'][d]['weighted'][key];new=x['dimensions'][d]['weighted'][key]
                assert old==new,(name,d,key,old,new)
    old=base_report['three_main_runs'];new=r['three_main_runs']
    assert new['five_dimension_vector']['weighted_denominator']==73.5
    assert old['five_dimension_vector']['weighted_complete_agreement_rate']==new['five_dimension_vector']['weighted_complete_agreement_rate']
    for run in ['R1','R2','R3']:
        assert old['q']['by_run'][run]['weighted_q']==new['q']['by_run'][run]['weighted_q']
    return {'weight_multiplier':7,'C5_weight_after_scaling':73.5,'weighted_ratios_invariant':True}
a.check('common_weight_scaling_keeps_kappa_q_and_vector_rates',weight_scaling)

def extreme_tables():
    x=engine.table_metrics({'n00':0,'n01':2,'n10':2,'n11':0})
    assert x['Po']==0 and x['Pe']==0.5 and x['kappa']==-1
    y=engine.table_metrics({'n00':99,'n01':1,'n10':0,'n11':0})
    assert y['Po']==0.99 and y['Pe']==0.99 and y['kappa']==0
    return {'balanced_disagreement_kappa':-1,'high_Po_rare_positive_change':{'Po':0.99,'kappa':0}}
a.check('hand_negative_kappa_and_high_Po_without_positive_stability',extreme_tables)

def stacked_variant(g,l,b):
    binding=g['conditions']['W']['requests']['AUDIT-001'];p=binding['exact_request']['path']
    payload=json.loads((b/p).read_text());payload['messages'][1]['content']=payload['messages'][1]['content'].replace('判读要求\n','判读说明\n',1)
    binding['exact_request']=write_ref(b,p,encoded(payload,True))
a.check('rehashed_combined_W_H_request_is_rejected',lambda:a.mutate_case(engine,'supplemental-WH-stacked',stacked_variant,'permitted assembly'))

def receipt_drift(g,l,b):
    for run,name in [('R1','constructed-model-one'),('R2','constructed-model-two')]:
        l['runs'][run]['records'][0]['attempts'][0]['provider_receipt']={'status':'observed_unverified','request_id':'invented-'+run,'returned_model':name,'configuration_evidence':None}
a.check('model_receipt_string_drift_rejected',lambda:a.mutate_case(engine,'supplemental-provider-drift',receipt_drift,'provider-returned model identity drift'))

def native_shape():
    folder,reg,led=a.clone('supplemental-complete-batch-in-single-record-slot')
    row=led['runs']['R1']['records'][0];attempt=row['attempts'][0]
    obj1=json.loads((folder/attempt['raw_response']['path']).read_text());r2=led['runs']['R1']['records'][1]
    obj2=json.loads((folder/r2['attempts'][0]['raw_response']['path']).read_text())
    combined={'batch_records':[obj1,obj2]}
    attempt['raw_response']=write_ref(folder,'constructed-native-full-batch.json',encoded(combined,True))
    v=json.loads((folder/attempt['validator_report']['path']).read_text());v['raw_response_sha256']=attempt['raw_response']['sha256']
    v['checks'].update(id_match=False,five_dimensions=False,response_schema=False);v['failure_reasons']=['Constructed batch output does not satisfy the frozen single-record response contract']
    attempt['validator_report']=write_ref(folder,attempt['validator_report']['path'],encoded(v));row['first']=None
    seal_inputs(folder,reg,led);r=a.report(engine,folder)
    assert r['per_record_diagnostic_states']['AUDIT-001']['R1']['state']=='technical_failure'
    assert r['production_firsts']['AUDIT-001'] is not None
    return {'complete_batch_native_shape':'invalid_for_single_record_contract','derived_splits_provenance_authentication':'not implemented','no_project_completion_claim':True}
a.check('complete_batch_native_bytes_not_misparsed_as_valid_single_record_response',native_shape)

summary={'stage':'supplemental_repair_controls','controls_run':len(a.RESULTS),'passed':sum(x['status']=='passed' for x in a.RESULTS),
         'failed':sum(x['status']=='failed' for x in a.RESULTS),'controls':a.RESULTS,'scope':'finite invented data only','real_model_dispatches':0}
(a.BASE/'supplemental-controls.json').write_bytes(encoded(summary))
print(json.dumps({k:v for k,v in summary.items() if k!='controls'}))
raise SystemExit(bool(summary['failed']))
