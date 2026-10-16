"""Reproducible synthetic-only controls. Reads no real label/Gold ledgers.

All writes are confined to this script's directory. Importing the predecessor
reads only its source; bytecode generation is disabled for both implementations.
"""
from pathlib import Path
from fractions import Fraction
import copy, hashlib, importlib.util, json, subprocess, sys
import numpy as np

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'prospective-engine-domain-sol'
PLAN=ROOT.parent.parent/'02-methods/department-year-analysis-plan-sol/report.json'
REPS=5000
SEED=20261010
CHECKS=[]

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(name,obj):
    path=ROOT/name
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    return path
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
engine=module('year_engine_control',ROOT/'metrics_engine.py')
old=module('domain_engine_control',OLD/'metrics_engine.py')

def check(name,condition,evidence):
    if not condition:raise AssertionError(name)
    CHECKS.append({'control':name,'passed':True,'evidence':evidence})

def same_prepared(a,b):
    if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(same_prepared(a[k],b[k]) for k in a)
    return a==b

def completed(labels):return {'status':'completed','labels':dict(zip(engine.DIMS,labels))}
def payload(strata,rows):
    return {'data_role':'synthetic','metadata':{'analysis_stage':'combined',
            'scope':{'kind':'synthetic_closed_toy','population_N':sum(h['N'] for h in strata)},
            'design':{'kind':'stratified_srswor','sampling_unit':'source_unit','strata':strata}},'records':rows}

def bind_years(name,p,requested=(),absent=()):
    p=copy.deepcopy(p)
    mapping={'assignment_basis':'synthetic_constructed','sealed':True,'frozen_before_labels':True,
             'requested_years':list(requested),'no_source_views':list(absent)}
    projection=engine.year_projection(p['records'],mapping)
    source=write(name+'-frozen-source-year-map.json',projection)
    mapping.update(sha256=digest(source),joined_projection_sha256=engine.canonical_hash(projection))
    p['metadata']['year_mapping']=mapping
    return p

def strip_years(p):
    p=copy.deepcopy(p);p['metadata'].pop('year_mapping',None)
    for row in p['records']:row.pop('policy_year',None)
    return p

def execute(name,p,guard='single_category'):
    input_path=write(name+'-input.json',p)
    captured=[];original=engine.rao_wu_weights
    def once(prepared,replicates=5000,seed=20261010):
        W=original(prepared,replicates,seed);captured.append(W);return W
    engine.rao_wu_weights=once
    try:out=engine.analyze(p,REPS,SEED,guard)
    finally:engine.rao_wu_weights=original
    expected=1 if p['metadata']['design']['kind']=='stratified_srswor' else 0
    check(name+': one full-design weight generation',len(captured)==expected,
          {'observed_generation_count':len(captured),'expected':expected,
           'shape':list(captured[0].shape) if captured else None})
    out_path=write(name+'-output.json',out)
    return out,captured[0] if captured else None,input_path,out_path

def states_from_row(row,method,j):
    out=row.get('outputs',{}).get(method)
    if out is None or out['status']=='execution_failure':return 3
    dim=engine.DIMS[j]
    if out.get('dimension_status',{}).get(dim)=='execution_failure':return 3
    value=out['labels'][dim]
    return 2 if value is None else value

def manual_mask(p,key):
    hindex={h['id']:h for h in p['metadata']['design']['strata']}
    def keep(row):
        for segment in key.split('|'):
            field,value=segment.split(':',1)
            if field=='year' and row['policy_year']!=(None if value=='unknown' else int(value)):return False
            if field=='department' and row['department']!=value:return False
            if field=='domain' and hindex[row['stratum_id']]['domain']!=value:return False
        return True
    return np.array([keep(r) for r in p['records']])

def expect_error(name,p,substring):
    try:engine.analyze(p,16,SEED,'none')
    except engine.DataError as error:
        check(name,substring in str(error),{'rejection':str(error)})
    else:raise AssertionError(name+' was accepted')

def main():
    strata=[{'id':'ra','N':30,'n':6,'department':'alpha','domain':'remaining'},
            {'id':'rb','N':60,'n':6,'department':'beta','domain':'remaining'},
            {'id':'ea','N':24,'n':6,'department':'alpha','domain':'exposed'},
            {'id':'eb','N':90,'n':6,'department':'beta','domain':'exposed'}]
    rows=[]
    for block,h in enumerate(strata):
        for i,y in enumerate((2020,2021,2020,None,2022,2021)):
            ordinal=block*6+i
            truth=[int((ordinal+j)%3==0) for j in range(5)]
            outputs={m:completed(truth) for m in engine.METHODS}
            outputs['rule']['labels']['S']=int((ordinal+1)%3==0)
            outputs['LLM']['labels']['E']=int((ordinal+2)%3==0)
            if ordinal==3:outputs['reference']['labels']['E']=None
            if ordinal==7:outputs.pop('rule')
            if ordinal==15:outputs['rule']={'status':'execution_failure','labels':None}
            if ordinal==20:
                outputs['rule']['labels']['F']=None
                outputs['rule']['dimension_status']={'F':'execution_failure'}
            if ordinal==10:outputs['LLM']['labels']['F']=None
            rows.append({'unit_id':f'toy-filename-1999-{h["id"]}-{i}','stratum_id':h['id'],
                         'department':h['department'],'policy_year':y,'outputs':outputs})
    cross=bind_years('cross-strata',payload(strata,rows),(2019,2020,2021,2022,2023),('year:2019',))
    out,W,input_path,output_path=execute('cross-strata',cross)
    year_keys=[k for k,v in out['analysis_scopes'].items() if 'policy_year' in v]
    shared={v['shared_replicate_weights_sha256'] for v in out['analysis_scopes'].values()}
    check('same W hash for all years, departments, domains, methods and dimensions',
          shared=={hashlib.sha256(np.ascontiguousarray(W).tobytes()).hexdigest()},
          {'views':len(out['analysis_scopes']),'annual_views':len(year_keys),'shared_hash_count':len(shared)})
    index={h['id']:h for h in strata}
    expected_cells=0
    for key in year_keys:
        mask=manual_mask(cross,key)
        for name,(left,right,purpose) in engine.COMPARISONS.items():
            for j,dim in enumerate(engine.DIMS):
                raw=np.zeros((4,4),dtype=int);weighted=np.zeros((4,4),dtype=float)
                exact=[Fraction(0) for _ in range(4)]
                for row,keep in zip(rows,mask):
                    if not keep:continue
                    a=states_from_row(row,left,j);b=states_from_row(row,right,j)
                    h=index[row['stratum_id']];weight=Fraction(h['N'],h['n'])
                    raw[a,b]+=1;weighted[a,b]+=float(weight)
                    for cell,(sa,sb) in enumerate(((1,1),(1,0),(0,1),(0,0))):
                        if (a,b)==(sa,sb):exact[cell]+=weight
                got=out['comparisons'][name]['domains'][key][dim]
                assert got['raw']['full4x4_including_failure']==raw.tolist()
                assert got['design_weighted']['full4x4_including_failure']==weighted.tolist()
                assert got['weighted_four_exact_fractions']==[str(x) for x in exact]
                expected_cells+=1
    check('nonuniform original inclusion weights preserved in all annual 16-state tables',True,
          {'comparison_dimension_view_tables_checked':expected_cells,'original_weights':[5,10,4,15],
           'every_original_stratum_split_across_years':True})
    missing=out['year_metadata']
    check('unknown year retained independently of null/failure labels',
          missing['unknown_policy_year_assigned_n']==4 and missing['unknown_policy_year_assigned_weight']==34 and
          out['analysis_scopes']['year:unknown']['is_calendar_year_effect'] is False and
          out['attention']['rule']['year:unknown']['S']['p'] is None,
          {'unknown_assigned_n':4,'unknown_assigned_weight':34,'bucket':'year:unknown','calendar_year_effect':False})
    for name in engine.COMPARISONS:
        for dim in engine.DIMS:
            total=np.zeros((4,4))
            for year in (2020,2021,2022,'unknown'):
                total+=np.array(out['comparisons'][name]['domains']['year:'+str(year)][dim]['design_weighted']['full4x4_including_failure'])
            assert np.array_equal(total,np.array(out['comparisons'][name]['domains']['ALL'][dim]['design_weighted']['full4x4_including_failure']))
    check('calendar-year plus unknown tables reconstruct ALL without dropping units',True,{'all_comparisons_and_dimensions':15})
    absent=out['attention']['reference']['year:2019']['S']
    unobserved=out['attention']['reference']['year:2023']['S']
    check('no source and no sampled year are different NA states, never zero',
          absent['p'] is None and absent['q'] is None and absent['p_status']=='NA(no_observed_source)' and
          out['analysis_scopes']['year:2019']['population_N']==0 and
          unobserved['p'] is None and unobserved['q'] is None and
          out['analysis_scopes']['year:2023']['population_N'] is None and
          unobserved['p_status']=='NA(no_assigned_year_observation_population_presence_unknown)',
          {'year2019':'bound no-source NA; population_N=0','year2023':'no assigned observation; population_N=null',
           'empty_coverage_undefined_replicates':absent['known_coverage_CI']['undefined_replicates']})
    check('date not inferred from unit identifier or file naming',
          'year:1999' not in out['analysis_scopes'] and out['analysis_scopes']['year:2020']['assigned_n']==8,
          {'misleading_identifier_year':1999,'explicit_year2020_assigned_n':8})
    # Independently form the year-domain Bernoulli vectors over ALL sampled units.
    mask=manual_mask(cross,'department:alpha|year:2020')
    X=np.array([[int(keep and states_from_row(r,'reference',j)==1) for j in range(5)]
                for r,keep in zip(rows,mask)],dtype=float)
    base=np.array([index[r['stratum_id']]['N']/index[r['stratum_id']]['n'] for r in rows])
    K=base@X;den=base@mask;Kr=W@X;Dr=W@mask.astype(float)
    for j,dim in enumerate(engine.DIMS):
        expected=engine._interval(float(K[j]/den),Kr[:,j]/Dr,True,False)
        assert out['attention']['reference']['department:alpha|year:2020'][dim]['known_coverage_CI']==expected
        expected=engine._interval(float(K[j]/K.sum()),Kr[:,j]/Kr.sum(axis=1),True,False)
        assert out['attention']['reference']['department:alpha|year:2020'][dim]['known_share_CI']==expected
    check('annual q and p interval calculations reuse masked full W, including varying year totals',True,
          {'replicates':REPS,'year_denominator_range':[float(Dr.min()),float(Dr.max())],
           'full_stratum_replication_not_year_bootstrap':True})
    # The annual analytic covariance must also retain zeros for units outside year.
    pair=np.array([4*states_from_row(r,'rule',0)+states_from_row(r,'reference',0) for r in rows])
    X=np.stack([((pair==cat)&mask).astype(float) for cat in (5,4,1,0)],axis=1)
    manual_V=np.zeros((4,4))
    for h in strata:
        block=X[[r['stratum_id']==h['id'] for r in rows]]
        manual_V+=h['N']**2*(1-h['n']/h['N'])*np.cov(block,rowvar=False,ddof=1)/h['n']
    assert np.allclose(engine.analytic_covariance(engine.prepare(cross),X),manual_V,rtol=0,atol=1e-12)
    check('annual analytic covariance uses original full strata with outside-year zeros',True,{'original_strata':4})
    for key in year_keys:
        guard=out['comparisons']['rule_vs_reference']['domains'][key]['S']['finite_guard']
        assert guard['status']=='unavailable_year_subdomain_not_fixed_stratum_union'
    check('year-local finite-count guard and year restratification are unavailable',True,{'annual_views_checked':len(year_keys)})
    failure=out['attention']['rule']['year:2020']['F']['failure_process_subtypes']['dimension_execution_failure']
    missing_return=out['attention']['rule']['year:2021']['S']['failure_process_subtypes']['missing_return']
    semantic_null=out['attention']['LLM']['year:2022']['F']['design_weighted']['semantic_null']
    check('semantic null, missing return and dimension failure retain original year weights',
          failure=={'raw_n':1,'weighted_total':15.0} and missing_return=={'raw_n':1,'weighted_total':10.0} and semantic_null==10,
          {'dimension_failure_weight':15,'missing_return_weight':10,'semantic_null_weight':10})
    # ALL has positive and negative examples in every dimension; the sparse
    # positive year and all-negative year must not become new acceptance gates.
    rare_rows=[{'unit_id':'rare-'+str(i),'stratum_id':'r','department':'alpha','policy_year':2020 if i==0 else 2021,
                'outputs':{m:completed([int(i==0)]*5) for m in engine.METHODS}} for i in range(4)]
    rare=bind_years('rare-positive',payload([{'id':'r','N':40,'n':4,'department':'alpha','domain':'remaining'}],rare_rows),(2019,2020,2021,2022),('year:2019',))
    rare_out,_,_,_=execute('rare-positive',rare)
    sparse=rare_out['comparisons']['rule_vs_reference']['domains']['year:2020']['S']
    check('one annual positive with zero observed errors is not perfect annual adequacy evidence',
          sparse['raw']['comparable_binary_total']==1 and sparse['raw']['binary_four_order_a_b_c_d']==[1,0,0,0] and
          sparse['design_weighted_metrics']['kappa'] is None and sparse['design_weighted_metrics']['F1']==1 and
          sparse['intervals']['F1']['CI95'] is None and
          sparse['intervals']['F1']['status']=='degenerate_non_census_requires_finite_guard_not_adequacy_evidence',
          {'annual_comparable_n':1,'observed_errors':0,'kappa':None,'F1':1,'F1_CI95':None})
    legacy_rare=old.analyze(strip_years(rare),REPS,SEED)
    check('ALL .80 gate unchanged even when annual targets are false/undefined',
          rare_out['project_review']==legacy_rare['project_review'] and rare_out['numeric_targets']==legacy_rare['numeric_targets'] and
          rare_out['project_review']['all_numerical_point_targets_met'] is True and
          rare_out['numeric_targets_by_analysis_scope']['year:2020']['all_numerical_point_targets_met'] is False and
          rare_out['project_review']['CI_lower_or_halfwidth_gate_added'] is False and
          rare_out['year_metadata']['annual_numeric_or_CI_gate_added'] is False,
          {'ALL_points_met':True,'sparse_year_points_met':False,'formal_acceptance':False,'added_year_or_CI_gate':False})
    census_rows=[{'unit_id':'census-'+str(i),'stratum_id':'c','department':'alpha','policy_year':2020 if i<2 else 2021,
                 'outputs':{m:completed([int(i==0),int(i==1),0,0,0]) for m in engine.METHODS}} for i in range(4)]
    census=bind_years('true-zero',payload([{'id':'c','N':4,'n':4,'department':'alpha','domain':'remaining'}],census_rows),(2019,2020,2021))
    zero_out,_,_,_=execute('true-zero',census)
    zero_dim=zero_out['attention']['reference']['year:2020']['Ec']
    zero_total=zero_out['attention']['reference']['year:2021']['S']
    check('known dimension zero versus no dimension mentions versus no source',
          zero_dim['p']==0 and zero_dim['q']==0 and zero_dim['p_status']=='defined' and zero_dim['q_status']=='defined' and
          zero_total['p']==0 and zero_total['q'] is None and zero_total['q_status']=='NA(no_dimension_mentions)' and
          zero_out['attention']['reference']['year:2019']['S']['p'] is None,
          {'known_dimension_zero':{'p':0,'q':0},'all_five_zero':{'p':0,'q':None},'no_source':{'p':None,'q':None}})
    check('census annual subsets known exactly without creating year strata',
          zero_out['analysis_scopes']['year:2020']['population_N']==2 and
          zero_out['analysis_scopes']['year:2020']['full_census_no_sampling_error'] is True and
          zero_dim['known_coverage_CI']['status']=='finite_census_no_sampling_error_conditional_on_labels',
          {'censused_parent':'ALL','annual_population_N':2,'new_year_strata':0})
    unknown_rows=[{'unit_id':'unknown-label-'+str(i),'stratum_id':'u','department':'alpha','policy_year':2020,
                  'outputs':{m:completed([0]*5) for m in engine.METHODS}} for i in range(4)]
    unknown_rows[0]['outputs']['rule']=completed([None]*5)
    unknown_rows[1]['outputs']['rule']={'status':'execution_failure','labels':None}
    unknown_rows[2]['outputs'].pop('rule')
    unknown_rows[3]['outputs']['rule']['labels']['F']=None
    unknown_rows[3]['outputs']['rule']['dimension_status']={'F':'execution_failure'}
    unresolved=bind_years('unresolved',payload([{'id':'u','N':12,'n':4,'department':'alpha'}],unknown_rows))
    unresolved_out,_,_,_=execute('unresolved',unresolved)
    uu=unresolved_out['attention']['rule']['year:2020']['F']
    check('zero known hits with unresolved mass cannot be reported as true zero',
          uu['design_weighted']['known_positive']==0 and uu['design_weighted']['unresolved_total']==12 and
          uu['p'] is None and uu['q'] is None and uu['p_status']=='unresolved_labels' and uu['q_status']=='unresolved_labels' and
          uu['unknown_coverage_bounds_not_CI']==[0,1] and uu['zero_total_share_undefined_possible'] is True,
          {'known_positive':0,'unresolved_weight':12,'p':None,'q':None,'p_bounds':[0,1],
           'semantic_null_and_three_failure_subtypes_preserved':True})
    nonprob=copy.deepcopy(cross);nonprob['metadata']['design']['kind']='nonprobability'
    nonprob_out,nonprob_W,_,_=execute('nonprobability',nonprob)
    check('nonprobability annual views remain descriptive and have no population W or CI',
          nonprob_W is None and nonprob_out['design']['replicate_weight_generation_count']==0 and
          nonprob_out['attention']['reference']['year:2020']['S']['known_share_CI']['CI95'] is None and
          nonprob_out['project_review']['formal_acceptance'] is False,
          {'replicate_weight_generation_count':0,'population_CI':None,'formal_acceptance':False})
    # Exact entire-return regression, not merely a few selected metric values.
    regression=[]
    noyear=strip_years(cross)
    for named in (True,False):
        for kind in ('stratified_srswor','nonprobability'):
            for stage,methods in (('combined',engine.METHODS),('human_first',('A','B')),('machine_reference',('reference','rule','LLM'))):
                for guard in ('none','single_category','joint_table'):
                    case=copy.deepcopy(noyear);case['metadata']['design']['kind']=kind
                    case['metadata']['analysis_stage']=stage
                    if not named:
                        for h in case['metadata']['design']['strata']:h.pop('domain')
                    for row in case['records']:row['outputs']={m:o for m,o in row['outputs'].items() if m in methods}
                    prior=old.analyze(case,128,SEED,guard);now=engine.analyze(case,128,SEED,guard)
                    assert prior==now,(named,kind,stage,guard)
                    assert same_prepared(old.prepare(case),engine.prepare(case))
                    regression.append({'named_domains':named,'kind':kind,'stage':stage,'guard_mode':guard,'entire_analyze_return_equal':True,
                                       'entire_prepare_return_equal':True,
                                       'return_sha256':engine.canonical_hash(now)})
    write('legacy-regression-results.json',regression)
    check('old interface complete numerical and structural regression',len(regression)==36,
          {'cases':36,'entire_analyze_return_equal':True,'entire_prepare_return_equal':True,'schema_without_year':'1.1',
           'coverage':'named/legacy × probability/nonprobability × 3 stages × 3 finite-guard modes'})
    old_cross=old.analyze(noyear,REPS,SEED)
    for field in ('numeric_targets','project_review','design','department_attention_difference_bounds'):
        assert out[field]==old_cross[field]
    for key in old_cross['analysis_scopes']:
        assert out['analysis_scopes'][key]==old_cross['analysis_scopes'][key]
        assert out['numeric_targets_by_analysis_scope'][key]==old_cross['numeric_targets_by_analysis_scope'][key]
        for method in engine.METHODS:assert out['attention'][method][key]==old_cross['attention'][method][key]
        for comp in engine.COMPARISONS:assert out['comparisons'][comp]['domains'][key]==old_cross['comparisons'][comp]['domains'][key]
    check('enabling year leaves all original scopes, ALL gate, and W exactly unchanged',True,{'original_scopes':len(old_cross['analysis_scopes'])})
    # Source metadata integrity controls; none contain real project submissions.
    wrong=copy.deepcopy(cross);wrong['records'][0]['policy_year']='2020'
    expect_error('reject string year',wrong,'integer or explicit null')
    wrong=copy.deepcopy(cross);wrong['records'][0]['policy_year']=True
    expect_error('reject bool year',wrong,'integer or explicit null')
    wrong=copy.deepcopy(cross);wrong['records'][0].pop('policy_year')
    expect_error('reject partially omitted year rather than silently dropping unit',wrong,'integer or explicit null')
    wrong=copy.deepcopy(cross);wrong['records'][0]['policy_year']=2021
    expect_error('reject altered joined year projection',wrong,'differs from its frozen binding')
    wrong=copy.deepcopy(cross);wrong['metadata']['year_mapping']['assignment_basis']='filename_year'
    expect_error('reject filename-based year assignment',wrong,'source issue/publication')
    wrong=copy.deepcopy(cross);wrong['metadata']['year_mapping']['sealed']=False
    expect_error('reject unfrozen source mapping',wrong,'sealed SHA256')
    wrong=strip_years(cross)
    for r in wrong['records']:r['policy_year']=2020
    expect_error('reject years without a source mapping',wrong,'frozen metadata.year_mapping')
    wrong=copy.deepcopy(cross)
    wrong['metadata']['year_mapping']['no_source_views']=['year:2020']
    wrong['metadata']['year_mapping']['joined_projection_sha256']=engine.canonical_hash(engine.year_projection(wrong['records'],wrong['metadata']['year_mapping']))
    expect_error('reject no-source declaration when assigned units exist',wrong,'contradicts assigned year units')
    wrong=copy.deepcopy(cross);wrong['metadata']['year_mapping']['no_source_views']=['year:unknown']
    wrong['metadata']['year_mapping']['joined_projection_sha256']=engine.canonical_hash(engine.year_projection(wrong['records'],wrong['metadata']['year_mapping']))
    expect_error('reject unknown year as no-source calendar year',wrong,'never year:unknown')
    wrong=strip_years(cross);wrong['data_role']='sealed_project'
    expect_error('preserve refusal of unsealed project labels',wrong,'must be sealed')
    # Exercise the shipped command line and compare it to the inspected API run.
    cli_path=ROOT/'cross-strata-cli-output.json'
    args=[sys.executable,str(ROOT/'metrics_engine.py'),'--input',str(input_path),'--output',str(cli_path),
          '--replicates',str(REPS),'--seed',str(SEED),'--guard-mode','single_category']
    result=subprocess.run(args,capture_output=True,text=True,check=True,env={**__import__('os').environ,'PYTHONDONTWRITEBYTECODE':'1'})
    cli=json.loads(cli_path.read_text());provenance=cli.pop('execution_provenance')
    check('actual CLI invocation matches synthetic API output and binds exact input/engine',
          cli==out and provenance['input_sha256']==digest(input_path) and provenance['engine_sha256']==digest(ROOT/'metrics_engine.py'),
          {'argv':args,'exit_code':result.returncode,'input_sha256':provenance['input_sha256'],
           'engine_sha256':provenance['engine_sha256'],'stdout':result.stdout,'stderr':result.stderr})
    report={'schema':'synthetic-year-extension-controls-v1','status':'all_controls_passed','passed_controls':len(CHECKS),
            'synthetic_only':True,'real_label_or_gold_ledgers_read':0,'real_annual_results_computed':0,
            'source_files_read':[str(OLD/'metrics_engine.py'),str(OLD/'input-contract.json'),str(PLAN)],
            'runtime':{'python':sys.version,'numpy':np.__version__,'scipy':__import__('scipy').__version__},
            'default_probability_replicates':REPS,'default_seed':SEED,'checks':CHECKS,
            'legacy_regression_cases':36,'annual_acceptance_gate_added':False,'CI_acceptance_gate_added':False}
    write('control-report.json',report)
    sources={str(p):digest(p) for p in (OLD/'metrics_engine.py',OLD/'input-contract.json',PLAN)}
    inputs={p.name:digest(p) for p in sorted(ROOT.glob('*-input.json'))}
    maps={p.name:digest(p) for p in sorted(ROOT.glob('*-frozen-source-year-map.json'))}
    write('input-seal.json',{'schema':'file-sha256-seal-v1','role':'synthetic_controls_and_read_only_predecessor_sources',
                            'predecessor_and_plan':sources,'synthetic_inputs':inputs,'synthetic_frozen_source_year_maps':maps,
                            'real_project_label_inputs':0})
    outputs={p.name:digest(p) for p in sorted(ROOT.iterdir()) if p.is_file() and
             p.name not in ('output-seal.json','input-seal.json') and p.name not in inputs and p.name not in maps}
    write('output-seal.json',{'schema':'file-sha256-seal-v1','files':outputs,'input_seal_sha256':digest(ROOT/'input-seal.json'),
                             'self_excluded_to_avoid_recursive_hash':True})
    print(json.dumps({'status':report['status'],'passed_controls':len(CHECKS),'legacy_regression_cases':36,
                      'real_annual_results_computed':0,'output_directory':str(ROOT)},ensure_ascii=False))

if __name__=='__main__':main()
