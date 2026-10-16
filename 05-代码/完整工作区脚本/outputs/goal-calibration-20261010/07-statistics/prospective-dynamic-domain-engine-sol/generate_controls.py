"""Fixed synthetic identity frame and eight TOY answer rows, no actual draw."""
import sys
sys.dont_write_bytecode=True
import copy
import hashlib
import json
from pathlib import Path
from fractions import Fraction
import scope_admission as a
HERE=Path(__file__).resolve().parent;DIMS=('S','E','Ec','I','F')

def write(p,x):
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    return a.binding(p)
def jl(p,x):
    with p.open('x') as f:
        for r in x:f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
    return a.binding(p)

def fixture(directory,remaining=False):
    directory.mkdir(parents=True,exist_ok=False)
    frame=[];part=[];membership=[];strata=[]
    index=0
    for hid,N,domain,department in [('r-a',600,'remaining','TOY-A'),('r-b',661,'remaining','TOY-B'),('e-a',1600,'exposed','TOY-A'),('e-b',1620,'exposed','TOY-B')]:
        strata.append({'id':hid,'N':N,'n':2,'department':department,'domain':domain})
        for _ in range(N):
            index+=1;uid=f'TOY-{index:05d}';sha=hashlib.sha256(uid.encode()).hexdigest()
            frame.append({'unit_id':uid,'department':department,'source_identity_sha256':sha})
            part.append({'unit_id':uid,'department':department,'domain':domain,'family_id':'TOY-FAM-'+uid,'exposure_status':'unexposed_at_final_freeze' if domain=='remaining' else 'direct'})
            if not remaining or domain=='remaining':membership.append({'unit_id':uid,'stratum_id':hid})
    if remaining:strata=strata[:2]
    fb=jl(directory/'full-frame.jsonl',frame);pb=jl(directory/'domain-partition.jsonl',part);mb=jl(directory/'stratum-membership.jsonl',membership)
    source=write(directory/'synthetic-source-identity-packet.json',{'synthetic_only':True,'no_policy_text_or_actual_labels':True,'source_ids':[r['unit_id'] for r in frame]})
    material=write(directory/'common-materials.json',{'status':'synthetic_common_materials_identity_fixture','source_packet_binding':source,'records':[{'unit_id':r['unit_id'],'source_bundle_sha256':r['source_identity_sha256']} for r in frame]})
    manual=write(directory/'manual.json',{'synthetic_only':True,'meaning':'TOY metadata fixture, no real coding manual'})
    estimand='remaining_pool' if remaining else 'full_4481_audit';target=[r['unit_id'] for r in membership]
    design=write(directory/'design-before-draw.json',{'status':'synthetic_design_frozen_before_draw','kind':'stratified_srswor','sampling_unit':'source_unit','estimand':estimand,'planned_allocation_before_answers':True,'frame_binding':fb,'partition_binding':pb,'stratum_membership_binding':mb,'seed':2026101002,'strata':strata,'target_ids_sha256':a.canonical(sorted(target))})
    assigned=[]
    for st in strata:
        for r in [r for r in membership if r['stratum_id']==st['id']][:2]:assigned.append({'unit_id':r['unit_id'],'stratum_id':st['id'],'department':st['department'],'domain':st['domain'],'pi_exact':str(Fraction(st['n'],st['N'])),'weight_exact':str(Fraction(st['N'],st['n']))})
    db=write(directory/'original-demo-draw.json',{'status':'synthetic_demonstration_draw_only','design_binding':design,'seed':2026101002,'answers_read_for_draw':False,'redraw_or_outcome_adaptive':False,'records':assigned,'assigned_ids_sha256':a.canonical(sorted(r['unit_id'] for r in assigned)),'assigned_order_sha256':a.canonical([r['unit_id'] for r in assigned])})
    exposure=write(directory/'exposure-final-demo.json',{'status':'synthetic_final_exposure_fixture','domain_partition_binding':pb,'family_closure_complete':True,'no_validation_results_used':True})
    versions={}
    for method in ('rule','LLM'):versions[method]=write(directory/(method+'-version.json'),{'status':'synthetic_fixed_machine_version','method':method,'manual_binding':manual,'common_materials_binding':material,'first_answer_selection_fixed_before_feedback':True})
    yrows=[{'unit_id':r['unit_id'],'policy_year':2020 if i<1261 else 2021} for i,r in enumerate(frame)]
    if not remaining:yrows[next(i for i,r in enumerate(yrows) if r['unit_id']==assigned[-1]['unit_id'])]['policy_year']=None
    yb=jl(directory/'complete4481-year-map.jsonl',yrows)
    ymeta=write(directory/'year-metadata.json',{'status':'synthetic_source_year_metadata_fixture','source_year_map_binding':yb,'assignment_basis':'synthetic_constructed','frozen_before_labels':True,'requested_years':[2020,2021,2022],'no_source_views':[]})
    desc={'registration_id':'TOY-REG-'+('remaining' if remaining else 'full'),'synthetic_only':True,'status':'synthetic_fixture_not_ROOT_approved','estimand':estimand,'statistical_core_sha256':a.FROZEN_STATISTICAL_CORE_SHA256,'statistics_contract_sha256':a.STATISTICS_CONTRACT_SHA256,'statistical_execution':{'replicates':5000,'seed':20261010,'guard_mode':'single_category','numeric_gate':'unchanged_45_ALL_point_targets','new_CI_threshold':False},'full_frame':fb,'domain_partition':pb,'stratum_membership':mb,'design_contract':design,'original_draw':db,'common_manual':manual,'common_materials':material,'rule_version':versions['rule'],'LLM_version':versions['LLM'],'exposure_freeze':exposure,'year_source_map':yb,'year_metadata':ymeta}
    descb=write(directory/'registration-fixture.json',desc)
    def output(v):return {'status':'completed','labels':dict.fromkeys(DIMS,v)}
    records=[]
    rvals=[1,1,0,0,0,0,0,0];refs=[1,0,1,0,None,0,0,0]
    for i,r in enumerate(assigned):records.append({'unit_id':r['unit_id'],'stratum_id':r['stratum_id'],'department':r['department'],'outputs':{'A':output(i%2),'B':output(i%2),'reference':output(refs[i]),'rule':output(rvals[i]),'LLM':output((i+1)%2)}})
    if not remaining:
        records[5]['outputs']['rule']={'status':'execution_failure','labels':None,'failure_code':'SYNTHETIC whole method failure'}
        records[6]['outputs']['rule']=None
        records[7]['outputs']['rule']['labels']['S']=None;records[7]['outputs']['rule']['dimension_status']={'S':'execution_failure'}
    nd={'kind':'stratified_srswor','sampling_unit':'source_unit','strata':strata,'assigned_ids_sha256':a.canonical(sorted(r['unit_id'] for r in assigned)),'domain_population_N':{'remaining':1261} if remaining else {'remaining':1261,'exposed':3220}}
    if not remaining:nd['domain_partition']='remaining_exposed'
    payload={'data_role':'synthetic','metadata':{'analysis_stage':'combined','scope':{'kind':'registered_remaining_pool' if remaining else 'registered_full_4481_audit','registration_id':desc['registration_id'],'population_N':1261 if remaining else 4481,'frame_ids_sha256':a.canonical(sorted(target))},'design':nd,'synthetic_registration_fixture':descb},'records':records}
    return payload,desc

def main():
    root=HERE/'cases';root.mkdir(exist_ok=False)
    full,desc=fixture(root/'base-full');remaining,rd=fixture(root/'base-remaining',True)
    cases=[]
    def case(name,p,expected,mode='prepare'):
        b=write(root/(name+'.input.json'),p);cases.append({'case_id':name,'input_binding':b,'expected':expected,'mode':mode})
    case('valid_full_registered_synthetic',full,'accept_synthetic_only')
    case('valid_remaining_registered_synthetic',remaining,'accept1261_only_not_full4481')
    case('numeric_direction_and_failure_states',full,'raw1_1_1_1_weighted300_300_330.5_330.5_failure2_1_3',mode='analyze')
    case('zero_error_sparse_guard_unchanged',full,'compare_unchanged_core_and_NA_not_one',mode='zero_error')
    case('year_same_design_same5000W',full,'sameW_unknown_year_kept_no_new_gate',mode='annual')
    # Every negative is fixed here before engine execution; changed resource bytes
    # are saved separately and bound, not overwritten in the base fixture.
    def resource_case(name,key,mutate,expected='reject'):
        d=copy.deepcopy(desc);b=d[key];obj=a.rows(b) if Path(b['path']).suffix=='.jsonl' else a.load(b);mutate(obj)
        changed=root/(name+'.changed'+Path(b['path']).suffix);d[key]=jl(changed,obj) if changed.suffix=='.jsonl' else write(changed,obj)
        p=copy.deepcopy(full);p['metadata']['synthetic_registration_fixture']=write(root/(name+'.descriptor.json'),d);case(name,p,expected)
    resource_case('incomplete4481_frame','full_frame',lambda x:x.pop())
    resource_case('duplicate_partition_ID','domain_partition',lambda x:x.__setitem__(-1,x[0]))
    resource_case('family_exposure_closure_leak','domain_partition',lambda x:x[-1].update(family_id=x[0]['family_id']))
    resource_case('population_layer_N_not_actual_members','design_contract',lambda x:x['strata'][0].update(N=599))
    resource_case('missing_target_stratum','stratum_membership',lambda x:x.pop())
    resource_case('zero_pi_n0_layer','design_contract',lambda x:x['strata'][0].update(n=0))
    resource_case('noncensus_singleton','design_contract',lambda x:x['strata'][0].update(n=1))
    resource_case('draw_out_of_frame','original_draw',lambda x:x['records'][0].update(unit_id='TOY-NOT-IN-FRAME'))
    resource_case('old_sample_weight_reused','original_draw',lambda x:x['records'][0].update(weight_exact='1444/120'))
    resource_case('changed_machine_manual','LLM_version',lambda x:x['manual_binding'].update(sha256='0'*64))
    resource_case('intermediate_exposure_not_final','exposure_freeze',lambda x:x.update(status='ROOT_preparatory_candidate_not_final'))
    resource_case('old800_year_map_incomplete','year_source_map',lambda x:x.__delitem__(slice(800,None)))
    resource_case('no_original_draw_adaptive_sample','original_draw',lambda x:x.update(redraw_or_outcome_adaptive=True))
    resource_case('missing_common_material_row','common_materials',lambda x:x['records'].pop())
    p=copy.deepcopy(full);p['metadata']['design']['strata'][0]['N']=599;case('caller_free_N_override',p,'reject')
    p=copy.deepcopy(full);p['records'].pop(6);case('delete_unreturned_assigned_row',p,'reject')
    p=copy.deepcopy(full);p['records'].reverse();case('change_original_draw_order',p,'reject')
    p=copy.deepcopy(full);p['data_role']='sealed_project';p['metadata'].pop('synthetic_registration_fixture');case('empty_ROOT_registry_actual_scope',p,'reject_before_labels')
    p=copy.deepcopy(full);p['data_role']='sealed_project';case('synthetic_fixture_to_real_project',p,'reject_before_labels')
    p=copy.deepcopy(full);p['data_role']='sealed_project';p['metadata']['scope']['kind']='user_free_scope';p['metadata'].pop('synthetic_registration_fixture');case('free_scope_alias_bypass',p,'reject_before_labels')
    case('new_bootstrap_parameter_changed',full,'reject_not5000',mode='bad_replicates')
    # Legacy scope guards and complete return values are tested on only8 TOY rows.
    for kind in ('full_4481_audit','remaining_1444'):
        p=copy.deepcopy(full);p['metadata'].pop('synthetic_registration_fixture');p['metadata']['scope']={'kind':kind,'population_N':4481 if kind=='full_4481_audit' else 1444,'frame_ids_sha256':'e'*64}
        if kind=='remaining_1444':p['records']=p['records'][:4]
        st=[{'id':'legacy-r','N':1444,'n':4,'domain':'remaining','department':'TOY'}]
        if kind=='full_4481_audit':st.append({'id':'legacy-e','N':3037,'n':4,'domain':'exposed','department':'TOY'})
        for i,r in enumerate(p['records']):r['stratum_id']='legacy-r' if i<4 else 'legacy-e';r['department']='TOY'
        p['metadata']['design']={'kind':'stratified_srswor','sampling_unit':'source_unit','strata':st,'domain_population_N':{'remaining':1444,'exposed':3037} if kind=='full_4481_audit' else {'remaining':1444}}
        if kind=='full_4481_audit':p['metadata']['design']['domain_partition']='remaining_exposed'
        case('legacy_'+kind+'_whole_return',p,'entire_analyze_return_exact',mode='legacy_compare')
    p=copy.deepcopy(full);p['metadata'].pop('synthetic_registration_fixture');p['metadata']['scope']['kind']='full_4481_audit';p['metadata']['scope'].pop('registration_id');case('legacy1444_3037_guard_unchanged',p,'reject_existing_guard')
    h={'status':'fixed_before_execution_all_synthetic_or_blank','cases':cases,'case_N':len(cases),'synthetic_answer_rows_max_per_case':8,'real_frame_or_draw_or_human_answers_created_N':0,'actual_1261_3220_adoption':False,'prototype_counts_are_hypothetical_fixture_only':True}
    write(HERE/'controls-fixed-before-execution.json',h)
    print(json.dumps({'cases':len(cases),'max_TOY_answer_rows':8,'actual_scopes_adopted':0}))

if __name__=='__main__':main()
