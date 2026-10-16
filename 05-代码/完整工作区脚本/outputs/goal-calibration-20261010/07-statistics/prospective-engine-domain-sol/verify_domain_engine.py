"""Necessary domain-interface regression; every ledger and ID is synthetic.

Only the adjacent N/n/domain/department schema projection is used for large toys.
The previous source is imported from a local copy, never its sealed directory.
"""
from pathlib import Path
from fractions import Fraction
from unittest.mock import patch
import copy, hashlib, importlib.util, inspect, json, sys
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
import metrics_engine as e
spec=importlib.util.spec_from_file_location('local_frozen_engine',ROOT/'old_engine_source_frozen.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
checks=[]

def check(name,condition,evidence=None):
    if not bool(condition):raise AssertionError(name)
    checks.append({'name':name,'pass':True,'evidence':evidence})

def out(state):
    if state=='execution_failure':return {'status':'execution_failure','labels':{}}
    return {'status':'completed','labels':{d:None if state=='null' else int(state) for d in e.DIMS}}

fixture=json.loads((ROOT/'independent-interface/domain-toy-cases.json').read_text())
base={'data_role':'synthetic','metadata':{'analysis_stage':'combined','design':{
      'kind':'stratified_srswor','sampling_unit':'source_unit',
      'strata':copy.deepcopy(fixture['base']['design']['strata']),
      'domain_population_N':fixture['base']['design']['domain_N'],
      'domain_partition':'remaining_exposed'},'scope':{'kind':'synthetic_small_partition','population_N':14}},'records':[]}
for r in fixture['base']['records']:
    base['records'].append({'unit_id':r['id'],'stratum_id':r['stratum_id'],'department':r['department'],
          'outputs':{m:out(r['left'] if m in ('A','rule','LLM') else r['right']) for m in e.METHODS}})

def run_capture(payload,B=128,guard='none'):
    generated=[];original=e.rao_wu_weights
    def capture(*args,**kwargs):
        W=original(*args,**kwargs);generated.append(W);return W
    with patch.object(e,'rao_wu_weights',side_effect=capture):result=e.analyze(payload,B,20261010,guard)
    check('one complete replicate matrix per analyze call',len(generated)==1,{'B':B,'assigned_n':len(payload['records'])})
    return result,generated[0]

prep=e.prepare(base);res,W=run_capture(base,guard='joint_table')
(ROOT/'toy-small.input.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n')
(ROOT/'toy-small.output.json').write_text(json.dumps(res,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
views=e.analysis_scopes(prep)
check('nine nonempty whole-stratum views',len(views)==9)
check('v2 default B5000 seed20261010 unchanged',inspect.signature(e.analyze).parameters['replicates'].default==5000 and
      inspect.signature(e.analyze).parameters['seed'].default==20261010)
for name in ('rao_wu_weights','analytic_covariance','_interval','attention_bounds','exact_metrics','vector_metrics','finite_count_interval','finite_category_guard','joint_table_guard'):
    check('unchanged previous numerical primitive '+name,inspect.getsource(getattr(e,name))==inspect.getsource(getattr(old,name)))
for key,expected in fixture['expected_base'].items():
    item=res['comparisons']['rule_vs_reference']['domains'][key]['S']
    check('independent exact weighted four / census '+key,item['weighted_four_exact_fractions']==expected['weighted_four'] and
          item['domain_full_census_no_sampling_error']==expected['census'])
    check('assigned and comparable totals retained '+key,item['design_weighted']['assigned_total']==float(Fraction(expected['assigned_weight'])) and
          item['design_weighted']['comparable_binary_total']==float(Fraction(expected['pair_weight'])))
    for metric in ('kappa','Precision','Recall','F1'):
        if metric in expected:
            val=None if expected[metric] is None else float(Fraction(expected[metric]))
            check('independent metric '+key+' '+metric,item['design_weighted_metrics'][metric]==val)
    mask=views[key]['mask']
    check('same global W for mask '+key,np.allclose(W@mask.astype(float),res['analysis_scopes'][key]['population_N']) and
          res['analysis_scopes'][key]['shared_replicate_weights_sha256']==res['design']['shared_replicate_weights_sha256'])
    check('joint16 guard uses scope layers only '+key,{h['stratum'] for h in item['finite_guard']['strata']}==set(views[key]['stratum_ids']) and
          item['finite_guard']['metric_projection_implemented'] is False)
check('all assigned failure/null remain in full table',res['comparisons']['rule_vs_reference']['domains']['ALL']['S']['design_weighted']['assigned_total']==14 and
      res['comparisons']['rule_vs_reference']['domains']['ALL']['S']['design_weighted']['comparable_binary_total']==11)
check('department contrast pairs keep only the previous department views',all(len(v)==1 for v in res['department_attention_difference_bounds'].values()))
check('all numeric scopes independently report formal false',all(v['formal_acceptance'] is False for v in res['numeric_targets_by_analysis_scope'].values()) and
      res['project_review']['formal_acceptance'] is False)
check('joint16 nonlinear projection explicitly unimplemented',res['finite_joint16_nonlinear_metric_projection_implemented'] is False)

def verify_conservation(payload,result,repW):
    p=e.prepare(payload);vs=e.analysis_scopes(p)
    pair=p['states']['rule'][:,0]*4+p['states']['reference'][:,0]
    mats={k:np.stack([((pair==cat)&v['mask']).astype(float) for cat in (5,4,1,0)],axis=1) for k,v in vs.items()}
    R,E='domain:remaining','domain:exposed'
    check('disjoint exhaustive domain unit masks',not np.any(vs[R]['mask']&vs[E]['mask']) and np.all(vs[R]['mask']|vs[E]['mask']))
    check('replicate four cells ALL = R + E',np.allclose(repW@mats['ALL'],repW@mats[R]+repW@mats[E]))
    check('analytic four-cell covariance ALL = R + E',np.allclose(e.analytic_covariance(p,mats['ALL']),e.analytic_covariance(p,mats[R])+e.analytic_covariance(p,mats[E])))
    joint=e.analytic_covariance(p,np.column_stack([mats[R],mats[E]]))
    check('independent-stratum domain cross covariance zero',np.allclose(joint[:4,4:],0))
    for comp in result['comparisons'].values():
        for dim in e.DIMS:
            tables={k:np.array(x[dim]['design_weighted']['full4x4_including_failure']) for k,x in comp['domains'].items()}
            check('full16 table additive by domain',np.allclose(tables['ALL'],tables[R]+tables[E]))
            for dept in sorted(set(p['departments'])):
                keys=[k for k in tables if k.startswith('domain:') and k.endswith('|department:'+dept)]
                check('full16 department table additive over domain intersections',np.allclose(tables['department:'+dept],sum((tables[k] for k in keys),np.zeros((4,4)))))
    check('nonlinear full kappa not average of domain kappas',
          result['comparisons']['rule_vs_reference']['domains']['ALL']['S']['design_weighted_metrics']['kappa'] !=
          sum(result['comparisons']['rule_vs_reference']['domains'][k]['S']['design_weighted_metrics']['kappa'] for k in (R,E))/2)

verify_conservation(base,res,W)

# Domain metadata rejection/compatibility checks, adapting the independent schema.
spec2=importlib.util.spec_from_file_location('independent_oracle',ROOT/'independent-interface/domain_toy_oracle.py')
oracle=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(oracle)
for case in fixture['validation_cases']:
    abstract=oracle.mutated(fixture['base'],case['mutation'])
    candidate=copy.deepcopy(base);design=candidate['metadata']['design'];design['strata']=abstract['design']['strata'];design.pop('domain_partition',None)
    if 'domain_N' in abstract['design']:design['domain_population_N']=abstract['design']['domain_N']
    else:design.pop('domain_population_N',None)
    candidate['metadata']['scope'].pop('population_N',None)
    candidate['records']=[{'unit_id':r['id'],'stratum_id':r['stratum_id'],
                          **({'department':r['department']} if 'department' in r else {}),
                          'outputs':{m:out(r['left'] if m in ('A','rule','LLM') else r['right']) for m in e.METHODS}}
                         for r in abstract['records']]
    try:e.prepare(candidate);accepted=True
    except e.DataError:accepted=False
    check('metadata contract '+case['id'],accepted==case['accepted'])

def rejected(name,mutation):
    x=copy.deepcopy(base);mutation(x)
    try:e.prepare(x);ok=False
    except e.DataError:ok=True
    check(name,ok)

rejected('partition marker with domain fields removed rejects',lambda x:[h.pop('domain') for h in x['metadata']['design']['strata']])
rejected('unknown partition marker rejects',lambda x:x['metadata']['design'].__setitem__('domain_partition','by_labels'))
rejected('record-level domain injection rejects',lambda x:x['records'][0].__setitem__('domain','exposed'))
rejected('separate domain input override rejects',lambda x:x['metadata'].__setitem__('domain_inputs',{}))
rejected('separate domain artifact override rejects',lambda x:x['metadata']['design'].__setitem__('domain_artifact_seals',{}))
rejected('bad full4481 split rejects',lambda x:x['metadata']['scope'].__setitem__('kind','full_4481_audit'))

# A census domain inside a noncensus full population; noncensus singleton illegal.
census_payload=copy.deepcopy(base)
for h in census_payload['metadata']['design']['strata']:
    if h['domain']=='remaining':h['N']=h['n']
census_payload['metadata']['design']['domain_population_N']['remaining']=4
census_payload['metadata']['scope']['population_N']=12
census_result,CW=run_capture(census_payload)
check('remaining census although full population noncensus',census_result['analysis_scopes']['domain:remaining']['full_census_no_sampling_error'] is True and
      census_result['analysis_scopes']['ALL']['full_census_no_sampling_error'] is False)
ci=census_result['comparisons']['rule_vs_reference']['domains']['domain:remaining']['S']['intervals']['kappa']
check('census defined kappa has zero sampling interval',ci['CI95'] is not None and ci['CI95'][0]==ci['CI95'][1])
ci=res['comparisons']['rule_vs_reference']['domains']['domain:exposed|department:Beta']['S']['intervals']['kappa']
check('census no comparable pairs keeps kappa NA',ci['CI95'] is None and ci['status']=='undefined_point_denominator')

# Preserve legacy calculations including mixed-department membership in one layer.
legacy=copy.deepcopy(base);ld=legacy['metadata']['design'];ld.pop('domain_population_N');ld.pop('domain_partition')
for h in ld['strata']:h.pop('domain')
def without_guard_note(v):
    if isinstance(v,dict):return {k:without_guard_note(x) for k,x in v.items() if k!='guard_scope_note'}
    if isinstance(v,list):return [without_guard_note(x) for x in v]
    return v
legacy_new=e.analyze(legacy,128,20261010,'single_category');legacy_old=old.analyze(legacy,128,20261010,'single_category')
for key in ('comparisons','numeric_targets','project_review','attention','department_attention_difference_bounds'):
    check('old version semantic regression '+key,without_guard_note(legacy_new[key])==legacy_old[key])
check('legacy W checksum identical',legacy_new['design']['shared_replicate_weights_sha256']==legacy_old['design']['shared_replicate_weights_sha256'])
check('legacy no added remaining/exposed views',set(legacy_new['analysis_scopes'])=={'ALL','department:Alpha','department:Beta'})
mixed=copy.deepcopy(legacy);mixed['metadata']['design']['strata']=[{'id':'mixed','N':8,'n':4}]
mixed['metadata']['scope']['population_N']=8;mixed['records']=mixed['records'][:4]
for i,r in enumerate(mixed['records']):r['stratum_id']='mixed';r['department']='Alpha' if i<2 else 'Beta'
mp=e.prepare(mixed);mx=np.column_stack([mp['departments']=='Alpha',mp['departments']=='Beta']).astype(float)
mv=e.analytic_covariance(mp,mx)
check('legacy within-layer department covariance nonzero',mv[0,1]<0 and np.isclose(mv.sum(),0))
check('legacy observed departments cannot prove fixed membership census',e.domain_is_census(mp,'department:Alpha') is False and
      e.analysis_scopes(mp)['department:Alpha']['population_N'] is None)

# The original low-information/unknown/failure behavior is unchanged by masks.
allzero=copy.deepcopy(base)
for r in allzero['records']:r['outputs']={m:out('0') for m in e.METHODS}
az=e.analyze(allzero,128,20261010,'none')
check('all-zero defined denominator NA rules retained',all(az['comparisons']['rule_vs_reference']['domains'][k]['S']['design_weighted_metrics']['kappa'] is None and
      az['comparisons']['rule_vs_reference']['domains'][k]['S']['design_weighted_metrics']['F1'] is None for k in az['analysis_scopes']))
check('noncensus constant coverage refuses unguarded95CI',az['attention']['rule']['domain:remaining']['S']['known_coverage_CI']['status']=='degenerate_non_census_requires_finite_guard_not_adequacy_evidence' and
      az['attention']['rule']['domain:remaining']['S']['known_coverage_CI']['CI95'] is None)
fail=copy.deepcopy(base);fail['records'][0]['outputs'].pop('LLM')
fail['records'][1]['outputs']['LLM']=out('0');fail['records'][1]['outputs']['LLM']['labels']['Ec']=None
fail['records'][1]['outputs']['LLM']['dimension_status']={'Ec':'execution_failure'}
fr=e.analyze(fail,128,20261010,'none')
check('missing return and dimension failure retained with domain mass',fr['attention']['LLM']['domain:remaining']['Ec']['failure_process_subtypes']['missing_return']['raw_n']==1 and
      fr['attention']['LLM']['domain:remaining']['Ec']['failure_process_subtypes']['dimension_execution_failure']['raw_n']==1)

# Toy-only sealed projection contract: hashes bind exactly one complete ledger.
sealed=copy.deepcopy(base);sealed['data_role']='sealed_project'
sealed['metadata']['design']['assigned_ids_sha256']=e.canonical_hash(sorted(r['unit_id'] for r in sealed['records']))
sealed['metadata']['input_seals']={m:{'sealed':True,'sha256':e.canonical_hash({'synthetic_only_method':m}),
      'joined_projection_sha256':e.projection_hash(sealed['records'],m)} for m in e.METHODS}
sr=e.analyze(sealed,128,20261010,'none')
check('sealed toy metadata cannot yield formal acceptance',sr['project_review']['formal_acceptance'] is False and
      sr['project_review']['metadata_cannot_authenticate_human_identity_on_its_own'] is True)
tampered=copy.deepcopy(sealed);tampered['records'][0]['outputs']['A']=out('0')
try:e.prepare(tampered);accepted=True
except e.DataError:accepted=False
check('one whole-ledger sealed projection rejects tamper',not accepted)

# Numeric full gate and domain flags may differ, no domain-average gate.
numeric=copy.deepcopy(base);numeric['metadata']['design']['strata']=[
      {'id':'numeric-r','domain':'remaining','department':'Alpha','N':4,'n':4},
      {'id':'numeric-e','domain':'exposed','department':'Alpha','N':198,'n':198}]
numeric['metadata']['design']['domain_population_N']={'remaining':4,'exposed':198};numeric['metadata']['scope']['population_N']=202
numeric['records']=[]
for hid,cells in [('numeric-r',[1,1,1,1]),('numeric-e',[99,0,0,99])]:
    for (a,b),count in zip(((1,1),(1,0),(0,1),(0,0)),cells):
        for _ in range(count):
            numeric['records'].append({'unit_id':'SYNTHETIC-NUMERIC-'+str(len(numeric['records'])),'stratum_id':hid,'department':'Alpha',
              'outputs':{m:out(str(a if m in ('A','rule','LLM') else b)) for m in e.METHODS}})
nr=e.analyze(numeric,128,20261010,'none')
flags=nr['numeric_targets_by_analysis_scope']
check('full passes, remaining fails, exposed passes independently',flags['ALL']['all_numerical_point_targets_met'] is True and
      flags['domain:remaining']['all_numerical_point_targets_met'] is False and flags['domain:exposed']['all_numerical_point_targets_met'] is True and
      nr['project_review']['all_numerical_point_targets_met'] is True and nr['project_review']['formal_acceptance'] is False)
(ROOT/'toy-numeric-gates.output.json').write_text(json.dumps(nr,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

# Full41 schema comes solely from the frozen whitelist projection, never labels.
schemas=json.loads((ROOT/'independent-interface/full-plan-schema-projection.json').read_text())
full_summaries={}
for plan_name,plan in schemas['plans'].items():
    if plan_name not in ('full800','full1000'):continue
    strata=plan['strata']
    check('41-stratum input whitelist '+plan_name,len(strata)==41 and all(set(h)=={'id','domain','department','N','n'} for h in strata))
    payload={'data_role':'synthetic','metadata':{'analysis_stage':'combined','scope':{'kind':'full_4481_audit','population_N':4481},
       'design':{'kind':'stratified_srswor','sampling_unit':'source_unit','domain_partition':'remaining_exposed',
                 'domain_population_N':{'remaining':1444,'exposed':3037},'strata':copy.deepcopy(strata)}},'records':[]}
    for hi,h in enumerate(strata):
        for i in range(h['n']):
            outputs={}
            for mi,m in enumerate(e.METHODS):
                if (i+hi)%29==mi:continue
                if (i+hi)%31==mi:outputs[m]={'status':'execution_failure','labels':{}};continue
                labels={d:None if (i+j*3+mi*2+hi)%11 in (0,1) else (i+j+mi+hi)%2 for j,d in enumerate(e.DIMS)}
                ds={d:'execution_failure' for j,d in enumerate(e.DIMS) if (i+j*3+mi*2+hi)%11==1}
                outputs[m]={'status':'completed','labels':labels,'dimension_status':ds}
            payload['records'].append({'unit_id':f'SYNTHETIC-SCHEMA-{plan_name}-{hi:02d}-{i:04d}',
               'stratum_id':h['id'],'department':h['department'],'outputs':outputs})
    result,FW=run_capture(payload,5000)
    check('full4481 and both domain constant replicate totals '+plan_name,
          all(np.allclose(FW@e.analysis_scopes(e.prepare(payload))[k]['mask'].astype(float),N,rtol=0,atol=1e-8)
              for k,N in (('ALL',4481),('domain:remaining',1444),('domain:exposed',3037))))
    check('full schema assigned n and 12 views '+plan_name,len(payload['records'])==plan['assigned_n'] and len(result['analysis_scopes'])==12)
    # Full16 table additivity across all methods/dimensions, including unknown/failure.
    for comp in result['comparisons'].values():
        for dim in e.DIMS:
            tables={k:np.array(x[dim]['design_weighted']['full4x4_including_failure']) for k,x in comp['domains'].items()}
            check('full41 full16 weighted partition '+plan_name,np.allclose(tables['ALL'],tables['domain:remaining']+tables['domain:exposed']))
            for dept in ('NMPA','NHSA','NHC'):
                check('full41 department/intersection weighted partition '+plan_name,
                      np.allclose(tables['department:'+dept],tables['domain:remaining|department:'+dept]+tables['domain:exposed|department:'+dept]))
    check('full41 cannot claim formal acceptance '+plan_name,result['project_review']['formal_acceptance'] is False and
          result['design']['domain_partition_checks']['full4481_equals_remaining1444_plus_exposed3037'] is True)
    input_path=ROOT/(plan_name+'-synthetic-schema.input.json');output_path=ROOT/(plan_name+'-synthetic-schema.output.json')
    input_path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    output_path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    full_summaries[plan_name]={'assigned_n':len(payload['records']),'B':5000,'seed':20261010,
       'shared_W_sha256':result['design']['shared_replicate_weights_sha256'],
       'scope_totals':{k:{a:v[a] for a in ('assigned_n','population_N','weighted_assigned_total','replicate_assigned_total_range')}
                      for k,v in result['analysis_scopes'].items()},'formal_acceptance':False}

result={'status':'passed_necessary_domain_interface_and_legacy_regression','checks':checks,'check_count':len(checks),
 'full_schema_toys':full_summaries,'engine_sha256':e.sha256(ROOT/'metrics_engine.py'),
 'previous_source_sha256':e.sha256(ROOT/'old_engine_source_frozen.py'),
 'real_project_executions':0,'real_human_or_AI_new_labels_read':0,'real_ID_draws':0,'source_bodies_read':0,
 'formal_acceptance':False,'not_joint16_metric_projection':True}
(ROOT/'domain-regression-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:result[k] for k in ('status','check_count','engine_sha256','real_project_executions')},ensure_ascii=False))
