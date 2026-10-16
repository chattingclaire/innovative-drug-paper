"""Pre-fixed synthetic/blank negative controls; no real labels or identities."""
import sys
sys.dont_write_bytecode=True
import copy
import json
from pathlib import Path
import handoff as h
HERE=h.HERE

def main():
    c=h.contract();ex=h.load(HERE/'control-expectations.json')['expected_controls'];results={};details={}
    def ok(name,fn):
        try:info=fn();results[name]={'passed':True,'detail':info}
        except Exception as e:results[name]={'passed':False,'type':type(e).__name__,'message':str(e)}
    def reject(name,fn):
        try:fn();results[name]={'passed':False,'message':'Unexpected acceptance'}
        except ValueError as e:results[name]={'passed':True,'rejection':str(e)}
    manifest=h.load(h.verify(c['frozen_inputs']['LLM_manifest']))
    ok('manifest_binding_wrapper_exact4481_order',lambda:{'rows':len(h.frozen_frame(manifest)),'canonical_order_sha256':h.canonical(h.frozen_frame(manifest))})
    bad=copy.deepcopy(manifest);bad['ordered_source_ids']['sha256']='0'*64
    reject('wrong_manifest_bytes_binding',lambda:h.frozen_frame(bad))
    blank=h.load(HERE/'review.UNFILLED.template.json')
    reject('blank_review',lambda:h.actual_gate(blank,c))
    # Transparent fabricated TOY attestations only exercise gates. They are not saved
    # in any actual review path or fed to build/analyze as project execution.
    toy=copy.deepcopy(blank);toy.update(status='ROOT_reviewed_actual_human200_reference_and_complete_machine_snapshot',control_or_synthetic=False,
       actual_human_adjudication=True,reference_machine_blinded=True,reference_before_machine_comparison=True,whole_LLM_campaign_terminal=True,machine_snapshot_frozen_before_human_feedback=True,
       AI_substitution_used=False,A_B_agreement_used_as_reference=False,label_based_machine_attempt_selection=False,reference_human_identity_codes=['TOY-ID-ONLY'],actual_user_confirmation={'source_kind':'direct_user_confirmation','statement':'SYNTHETIC GATE CONTROL; NOT ACTUAL CONFIRMATION'},AB_execution_review_binding={},reference_original_binding={},LLM_terminal_inventory_binding={})
    for name,key,v in [('updated_rule_snapshot','snapshot_id','rule-v20-UPDATED'),('updated_rule_prediction_bytes','old_rule_prediction_binding',{}),('future1261_3220_domain_relabel','domain_population_N',{'remaining':1261,'exposed':3220}),('AI_reference_substitution','AI_substitution_used',True),('A_B_agreement_auto_reference','A_B_agreement_used_as_reference',True),('reference_not_machine_blinded','reference_machine_blinded',False),('missing_actual_user_confirmation','actual_user_confirmation',{})]:
        bad=copy.deepcopy(toy);bad[key]=v;reject(name,lambda bad=bad:h.actual_gate(bad,c))
    inv=h.load(HERE/'LLM-complete-terminal-inventory.UNFILLED.template.json')
    reject('LLM_running_or_unfilled_inventory',lambda:h.terminal_inventory_gate(inv,toy,c))
    vi=copy.deepcopy(inv);vi.update(status='ROOT_received_complete_terminal_native4481_campaign',all_batches_terminal=True,reference_or_accuracy_used_in_selection=False)
    for b in vi['batches']:b['terminal_state']='technical_valid_whole_batch'
    bad=copy.deepcopy(vi);bad['batches']=bad['batches'][:-1]
    reject('LLM_503_batch_partial_inventory',lambda:h.terminal_inventory_gate(bad,toy,c))
    bad=copy.deepcopy(vi);bad['batches'][-1]['terminal_state']=None
    reject('LLM_one_unfilled_batch_of504',lambda:h.terminal_inventory_gate(bad,toy,c))
    identity={'unit_id':'TOY-ONLY','source_bundle_sha256':'f'*64}
    def rr(ms='completed',status='filled',v=0):return {'blind_id':'TOY-R','method_status':ms,'source_bundle_sha256':'f'*64,'dimensions':{d:{'completion_status':status,'value':v,'human_identity_code':'TOY-ID-ONLY','null_reason':None,'failure_code':None} for d in h.DIMS}}
    reject('blank_reference',lambda:h.reference_output(rr('unfilled','unfilled',None),identity,['TOY-ID-ONLY']))
    r=rr();r['dimensions']['S']['value']=1;r['dimensions']['Ec'].update(completion_status='lawful_null',value=None,null_reason='TOY unresolved wording')
    def exact():
        out=h.reference_output(r,identity,['TOY-ID-ONLY']);h.require(out['labels']=={'S':1,'E':0,'Ec':None,'I':0,'F':0},'Exact values changed');return out
    ok('reference_exact0_1_null',exact)
    reject('reference_unjustified_null',lambda:h.reference_output(rr('completed','lawful_null',None),identity,['TOY-ID-ONLY']))
    reject('reference_bool',lambda:h.reference_output(rr(v=True),identity,['TOY-ID-ONLY']))
    reject('reference_string',lambda:h.reference_output(rr(v='1'),identity,['TOY-ID-ONLY']))
    def nonreturn():h.require(h.reference_output(rr('not_returned','not_returned',None),identity,[]) is None,'Nonreturn changed into semantic null');return 'method=None'
    ok('reference_whole_not_returned',nonreturn)
    rfail=rr('execution_failure','execution_failure',None)
    for x in rfail['dimensions'].values():x['failure_code']='TOY whole failure'
    def wf():
        out=h.reference_output(rfail,identity,[]);h.require(out['status']=='execution_failure' and out['labels'] is None,'Whole failure state changed');return out
    ok('reference_whole_failure',wf)
    d=rr();d['dimensions']['S'].update(completion_status='execution_failure',value=None,failure_code='TOY cell failure')
    def df():
        out=h.reference_output(d,identity,['TOY-ID-ONLY']);h.require(out['dimension_status']=={'S':'execution_failure'} and out['labels']['S'] is None,'Dimension failure erased');return out
    ok('reference_dimension_failure',df)
    d=rr();d['dimensions']['S'].update(completion_status='not_returned',value=None)
    reject('reference_partial_dimension_nonreturn',lambda:h.reference_output(d,identity,['TOY-ID-ONLY']))
    engine=h.module('_control_existing_engine',c['frozen_inputs']['engine']);year=h.module('_control_existing_year_engine',c['frozen_inputs']['year_engine'])
    for stage in ('machine_reference','combined'):
        reject('engine_empty_'+stage+'_template',lambda stage=stage:engine.prepare(h.load(HERE/(stage+'.UNFILLED.template.json'))))
    def output(v):return {'status':'completed','labels':dict.fromkeys(h.DIMS,v)}
    rows=[]
    for i,(rv,ref,lv) in enumerate(zip([1,1,1,0],[1,0,0,1],[0,1,0,1]),1):
        rows.append({'unit_id':f'TOY-{i}','stratum_id':'TOY-first','department':'TOY','outputs':{'A':output(1),'B':output(1),'reference':output(ref),'rule':output(rv),'LLM':output(lv)}})
    for i in range(5,9):rows.append({'unit_id':f'TOY-{i}','stratum_id':'TOY-second','department':'TOY','outputs':{'A':output(0),'B':output(1),'reference':output(0),'rule':output(0),'LLM':output(0)}})
    rows[4]['outputs']['reference']=output(None)
    rows[5]['outputs']['rule']={'status':'execution_failure','labels':None,'failure_code':'TOY-WHOLE'}
    rows[6]['outputs']['rule']=None
    rows[7]['outputs']['rule']['labels']['S']=None;rows[7]['outputs']['rule']['dimension_status']={'S':'execution_failure'}
    payload={'data_role':'synthetic','metadata':{'analysis_stage':'combined','scope':{'kind':'synthetic_toy_only','population_N':22},'design':{'kind':'stratified_srswor','sampling_unit':'source_unit','strata':[{'id':'TOY-first','N':10,'n':4,'department':'TOY'},{'id':'TOY-second','N':12,'n':4,'department':'TOY'}]}},'records':rows}
    bad=copy.deepcopy(payload);bad['metadata']['scope']={'kind':'full_4481_audit','population_N':4481};bad['metadata']['design'].update(domain_partition='remaining_exposed',domain_population_N={'remaining':1261,'exposed':3220})
    for stratum,domain,N in zip(bad['metadata']['design']['strata'],('remaining','exposed'),(1261,3220)):stratum.update(domain=domain,N=N)
    reject('engine_new_population_domain_contract',lambda:engine.prepare(bad))
    plain=engine.analyze(payload,replicates=5000,seed=20261010,guard_mode='single_category')
    def direction():
        cells=plain['comparisons']['rule_vs_reference']['domains']['ALL']['S']
        h.require(cells['raw']['binary_four_order_a_b_c_d']==[1,2,1,0],'Raw machine/reference direction changed')
        h.require(cells['design_weighted']['binary_four_order_a_b_c_d']==[2.5,5.,2.5,0.],'Original unequal weights not used')
        h.require(plain['comparisons']['rule_vs_reference']['orientation']['row']=='rule' and plain['comparisons']['rule_vs_reference']['orientation']['column']=='reference','Direction reversed')
        h.require(plain['project_review']['formal_acceptance'] is False,'Toy promoted to formal');return {'raw':[1,2,1,0],'weighted':[2.5,5,2.5,0],'formal_acceptance':False}
    ok('synthetic_raw_weighted_direction',direction)
    def failures():
        prep=engine.prepare(payload);h.require(list(prep['failure_causes']['rule'][:,0])==[0,0,0,0,0,2,1,3],'Failure/nonreturn causes changed');return list(map(int,prep['failure_causes']['rule'][:,0]))
    ok('synthetic_three_failure_causes',failures)
    ypayload=copy.deepcopy(payload)
    for i,r in enumerate(ypayload['records']):r['policy_year']=2020 if i<4 else (None if i==7 else 2021)
    mapping={'assignment_basis':'synthetic_constructed','sealed':True,'frozen_before_labels':True,'sha256':'a'*64,'requested_years':[2020,2021,2022],'no_source_views':[]}
    mapping['joined_projection_sha256']=year.canonical_hash(year.year_projection(ypayload['records'],mapping));ypayload['metadata']['year_mapping']=mapping
    annual=year.analyze(ypayload,replicates=5000,seed=20261010,guard_mode='single_category')
    stage_results={}
    for stage,active in [('human_first',('A','B')),('machine_reference',('reference','rule','LLM'))]:
        p=copy.deepcopy(ypayload);p['metadata']['analysis_stage']=stage
        for r in p['records']:r['outputs']={m:r['outputs'][m] for m in active}
        stage_results[stage]=year.analyze(p,replicates=5000,seed=20261010,guard_mode='single_category')
    def shared():
        resultsall=[plain,annual,*stage_results.values()];hashes=[r['design']['shared_replicate_weights_sha256'] for r in resultsall]
        h.require(len(set(hashes))==1 and all(r['design']['replicate_weight_generation_count']==1 and r['design']['bootstrap_replicates']==5000 for r in resultsall),'Annual/method stages altered W')
        h.require(annual['comparisons']['rule_vs_reference']['domains']['ALL']==plain['comparisons']['rule_vs_reference']['domains']['ALL'],'Annual enabled changed old ALL result')
        return {'5000_W_sha256':hashes[0],'generation_count_per_analyze':1,'separate_synthetic_calls':4}
    ok('synthetic_all_methods_and_years_common5000W',shared)
    def unknown():
        h.require(annual['year_metadata']['unknown_policy_year_assigned_n']==1,'Unknown year imputed')
        h.require(annual['attention']['rule']['year:2020']['S']['p_status']=='unresolved_source_year_membership','Unknown source-year uncertainty erased')
        return {'unknown_year_N':1,'calendar_p_status':'unresolved_source_year_membership'}
    ok('synthetic_year_unknown',unknown)
    first=h.module('_control_human_original_gate',c['frozen_inputs']['human_first'])
    reject('blank_AB_original_reception',lambda:first.reviewed_receive(h.ROOT/'05-validation/human200-reception-root/checks/blank200-dry-run',h.ROOT/'07-statistics/human200-formal-handoff-root/review.UNFILLED.template.json'))
    h.require(set(results)==set(ex),'Control coverage differs from pre-fixed plan')
    out={'status':'synthetic_and_blank_controls_only','expectations_binding':h.binding(HERE/'control-expectations.json'),'code_binding':h.binding(__file__),'handoff_binding':h.binding(HERE/'handoff.py'),'engine_bindings':{k:c['frozen_inputs'][k] for k in ('engine','year_engine')},'controls':results,'passed_N':sum(r['passed'] for r in results.values()),'failed_N':sum(not r['passed'] for r in results.values()),'actual_human_reference_N':0,'actual_LLM_partial_labels_read':0,'actual_formal_statistics_N':0}
    with (HERE/'control-results-attempt02.json').open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    with (HERE/'synthetic-statistical-inputs-and-results-attempt02.json').open('x') as f:json.dump({'data_role':'synthetic','no_real_human_or_machine_identity':True,'combined_payload':payload,'year_payload':ypayload,'plain':plain,'annual':annual,'stage_results':stage_results},f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'controls_N':len(results),'passed':out['passed_N'],'failed':out['failed_N'],'actual_results':0}))

if __name__=='__main__':main()
