"""Independent AI technical audit; synthetic constructed controls only.

Never invokes the author's run_controls and never writes outside this directory.
"""
from pathlib import Path
from fractions import Fraction
from datetime import datetime, timezone
import copy, hashlib, importlib.util, itertools, json, math, platform, sys
import numpy as np
import scipy

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
NEW=ROOT/'07-statistics/prospective-engine-year-sol'
OLD=ROOT/'07-statistics/prospective-engine-domain-sol'
PLAN=ROOT/'02-methods/department-year-analysis-plan-sol/report.json'
DIMS=('S','E','Ec','I','F')
METHODS=('A','B','reference','rule','LLM')
CHECKS=[]

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canon(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(name,obj):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    return p
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def check(name,condition,evidence):
    if not condition:raise AssertionError(name)
    CHECKS.append({'check':name,'passed':True,'evidence':evidence})
def close(a,b):return np.allclose(a,b,atol=1e-12,rtol=1e-12)
def output(values):return {'status':'completed','labels':dict(zip(DIMS,values))}
def row(uid,h,year,values):
    return {'unit_id':uid,'stratum_id':h['id'],'department':h['department'],
            'policy_year':year,'outputs':{m:output(values) for m in METHODS}}
def payload(strata,rows,prob=True):
    return {'data_role':'synthetic','metadata':{'analysis_stage':'combined',
            'scope':{'kind':'independent_constructed_toy','population_N':sum(h['N'] for h in strata)},
            'design':{'kind':'stratified_srswor' if prob else 'nonprobability','strata':strata}},'records':rows}
def bind(name,p,requested=(),no_source=()):
    p=copy.deepcopy(p)
    y={'assignment_basis':'synthetic_constructed','sealed':True,'frozen_before_labels':True,
       'requested_years':list(requested),'no_source_views':list(no_source)}
    # Independently implement the published canonical projection, excluding labels.
    proj={'assignment_basis':y['assignment_basis'],'requested_years':sorted(requested),
          'no_source_views':sorted(no_source),
          'records':[{'unit_id':r['unit_id'],'policy_year':r['policy_year']}
                     for r in sorted(p['records'],key=lambda r:r['unit_id'])]}
    f=write('cases/'+name+'-source-year-map.json',proj)
    y.update(sha256=digest(f),joined_projection_sha256=canon(proj))
    p['metadata']['year_mapping']=y;write('cases/'+name+'-input.json',p);return p
def execute(mod,name,p,reps=64,guard='none'):
    write('cases/'+name+'-executed-input.json',p)
    captured=[];fn=mod.rao_wu_weights
    def capture(prepared,replicates=5000,seed=20261010):
        w=fn(prepared,replicates,seed);captured.append(w);return w
    mod.rao_wu_weights=capture
    try:o=mod.analyze(copy.deepcopy(p),reps,20261010,guard)
    finally:mod.rao_wu_weights=fn
    write('cases/'+name+'-output.json',o)
    return o,captured
def expect_reject(mod,name,p):
    try:mod.analyze(p,8,20261010,'none')
    except mod.DataError as exc:
        check(name,True,{'rejection':str(exc)});return
    raise AssertionError(name+' accepted')
def strip(p):
    p=copy.deepcopy(p);p['metadata'].pop('year_mapping',None)
    for r in p['records']:r.pop('policy_year',None)
    return p

def main():
    source_paths=sorted([p for p in NEW.iterdir() if p.is_file()])+[OLD/'metrics_engine.py',OLD/'input-contract.json',PLAN]
    source_before={str(p):digest(p) for p in source_paths}
    original=load('original_year_independent_audit',NEW/'metrics_engine.py')
    old=load('old_domain_independent_audit',OLD/'metrics_engine.py')
    repaired=load('repaired_year_independent_audit',HERE/'metrics_engine_repaired.py')
    # Verify original delivery seals for integrity only, never as a mathematical proof.
    inp=json.loads((NEW/'input-seal.json').read_text());outseal=json.loads((NEW/'output-seal.json').read_text())
    seal_checks=[]
    for path,h in inp['predecessor_and_plan'].items():seal_checks.append(digest(Path(path))==h)
    for section in ('synthetic_inputs','synthetic_frozen_source_year_maps'):
        for name,h in inp[section].items():seal_checks.append(digest(NEW/name)==h)
    for name,h in outseal['files'].items():seal_checks.append(digest(NEW/name)==h)
    seal_checks.append(digest(NEW/'input-seal.json')==outseal['input_seal_sha256'])
    check('original input/output seals match actual files',all(seal_checks),{'bindings_checked':len(seal_checks),'meaning':'integrity only'})

    # Six units, original inclusion weights 3, 5, 1. Years split two original strata.
    hs=[{'id':'ra','N':6,'n':2,'department':'alpha','domain':'remaining'},
        {'id':'ea','N':10,'n':2,'department':'alpha','domain':'exposed'},
        {'id':'rb','N':2,'n':2,'department':'beta','domain':'remaining'}]
    rs=[row('audit-a0',hs[0],2020,[1,1,0,0,0]),row('audit-a1',hs[0],2021,[0,0,1,0,0]),
        row('audit-b0',hs[1],2020,[0,1,1,0,0]),row('audit-b1',hs[1],2021,[1,0,0,1,0]),
        row('audit-c0',hs[2],2020,[0,0,0,0,0]),row('audit-c1',hs[2],2020,[1,0,0,0,1])]
    for i,v in ((0,[1,0,0,0,0]),(2,[0,0,1,0,0]),(5,[1,0,0,0,0])):
        rs[i]['outputs']['reference']=output(v)
    mainp=bind('ht-hand',payload(hs,rs),(2020,2021,2022))
    mainout,caps=execute(original,'ht-hand-original',mainp,5000,'single_category')
    fixedout,fixedcaps=execute(repaired,'ht-hand-repaired',mainp,5000,'single_category')
    W=caps[0]
    check('one full Rao-Wu matrix generated and shared',len(caps)==len(fixedcaps)==1 and W.shape==(5000,6) and np.array_equal(W,fixedcaps[0]),{'shape':list(W.shape),'repaired_W_identical':True})
    keys=mainout['analysis_scopes']
    whash=hashlib.sha256(np.ascontiguousarray(W).tobytes()).hexdigest()
    check('every scope uses same complete W hash',all(x['shared_replicate_weights_sha256']==whash for x in keys.values()),{'scope_count':len(keys),'W_sha256':whash})
    weights=[Fraction(3),Fraction(3),Fraction(5),Fraction(5),Fraction(1),Fraction(1)]
    hindex={h['id']:h for h in hs}
    table_checks=0
    for key,view in keys.items():
        keep=[]
        for r in rs:
            valid=True
            for segment in ([] if key=='ALL' else key.split('|')):
                field,value=segment.split(':',1)
                if field=='department':valid &= r['department']==value
                elif field=='domain':valid &= hindex[r['stratum_id']]['domain']==value
                elif field=='year':valid &= r['policy_year']==(None if value=='unknown' else int(value))
            keep.append(bool(valid))
        manual_mask=np.array(keep,dtype=bool)
        assert view['unit_mask_sha256']==hashlib.sha256(np.ascontiguousarray(manual_mask).tobytes()).hexdigest()
        for name,(left,right) in {'A_vs_B':('A','B'),'rule_vs_reference':('rule','reference'),'LLM_vs_reference':('LLM','reference')}.items():
            for d in DIMS:
                raw=np.zeros((4,4),dtype=int);weighted=np.zeros((4,4),dtype=float)
                for i,r in enumerate(rs):
                    if not keep[i]:continue
                    a=r['outputs'][left]['labels'][d];b=r['outputs'][right]['labels'][d]
                    raw[a,b]+=1;weighted[a,b]+=float(weights[i])
                actual=mainout['comparisons'][name]['domains'][key][d]
                assert actual['raw']['full4x4_including_failure']==raw.tolist()
                assert actual['design_weighted']['full4x4_including_failure']==weighted.tolist()
                table_checks+=1
    check('independent full-length mask and original-weight16-state oracle for every view',True,{'tables_checked':table_checks,'all_mask_hashes_match_independent_six_entry_vectors':True})
    mask=[True,False,True,False,True,True]
    K=[sum(weights[i]*rs[i]['outputs']['rule']['labels'][d] for i in range(6) if mask[i]) for d in DIMS]
    den=sum(weights[i] for i in range(6) if mask[i]);B=sum(K)
    got=mainout['attention']['rule']['year:2020']
    check('annual HT denominator and multi-label q/p match hand fractions',den==10 and K==[4,8,5,0,1] and B==18 and all(close(got[d]['p'],float(K[j]/den)) and close(got[d]['q'],float(K[j]/B)) for j,d in enumerate(DIMS)),{'Nhat':str(den),'T':list(map(str,K)),'B':str(B),'q':[str(k/B) for k in K],'p':[str(k/den) for k in K],'raw_n':4,'sum_p':'9/5'})
    check('method-specific q denominators are separate',close(mainout['attention']['reference']['year:2020']['S']['q'],4/9) and close(got['S']['q'],2/9),{'rule_B':18,'reference_B':9})
    # m=n-1=1 gives exactly two FPC-scaled weights per noncensus stratum.
    s1=math.sqrt(Fraction(2,3));s2=math.sqrt(Fraction(4,5))
    four=[]
    for a,b in itertools.product((-1,1),repeat=2):
        four.append(np.array([3*(1+a*s1),3*(1-a*s1),5*(1+b*s2),5*(1-b*s2),1,1]))
    check('observed W rows belong to exhaustive four hand-computable draws',all(any(close(w,z) for z in four) for w in W) and close(W[:,:2].sum(1),6) and close(W[:,2:4].sum(1),10) and close(W[:,4:].sum(1),2),{'FPCs':[2/3,4/5,0],'original_stratum_totals':[6,10,2],'year_not_new_stratum':True})
    dr=np.array([sum(w[i] for i in range(6) if mask[i]) for w in W])
    kr=np.array([[sum(w[i]*rs[i]['outputs']['rule']['labels'][d] for i in range(6) if mask[i]) for d in DIMS] for w in W])
    ci_expected={}
    for j,d in enumerate(DIMS):
        for f,v in (('known_coverage_CI',kr[:,j]/dr),('known_share_CI',kr[:,j]/kr.sum(1))):
            q=np.quantile(v,[.025,.975]).tolist();actual=got[d][f]
            check('masked full W interval '+d+' '+f,close(actual['bootstrap_percentiles95'],q),{'expected':q,'status':actual['status']})
            ci_expected[d+' '+f]=q
    check('year denominator varies rather than year-local fixed n/N',np.ptp(dr)>0 and close(keys['year:2020']['replicate_assigned_total_range'],[dr.min(),dr.max()]),{'actual_range':[float(dr.min()),float(dr.max())],'four_possible_denominators':[float(z[[0,2,4,5]].sum()) for z in four]})
    X=np.array([[1,0,0,0],[0,0,0,0],[0,0,0,1],[0,0,0,0],[0,0,0,1],[1,0,0,0]],dtype=float)
    handV=np.diag([6.,0.,0.,20.])
    totals=np.array([z@X for z in four]);exact_cov=(totals-totals.mean(0)).T@(totals-totals.mean(0))/4
    check('outside-year zero indicators preserve original-design covariance',close(original.analytic_covariance(original.prepare(mainp),X),handV) and close(exact_cov,handV),{'hand_covariance':handV.tolist(),'derivation':'6^2*(1-2/6)/2*(1/2)=6; 10^2*(1-2/10)/2*(1/2)=20'})
    annualkeys=[k for k in keys if 'policy_year' in keys[k]]
    check('year finite guards unavailable without new layer',all(mainout['comparisons']['rule_vs_reference']['domains'][k]['S']['finite_guard']['status']=='unavailable_year_subdomain_not_fixed_stratum_union' for k in annualkeys),{'annual_scopes_checked':len(annualkeys),'original_strata':3})
    check('empty sampled year differs from legitimate complete census empty child',keys['year:2022']['population_N'] is None and keys['year:2022']['source_status']=='NA(no_assigned_year_observation_population_presence_unknown)' and keys['department:beta|year:2022']['population_N']==0 and keys['department:beta|year:2022']['source_status']=='NA(no_observed_source_in_censused_parent_scope)',{'sampled_empty':keys['year:2022']['source_status'],'complete_census_empty':keys['department:beta|year:2022']['source_status']})

    # Counterexample: a full ID census with an unresolved source year.
    c=[{'id':'c','N':2,'n':2,'department':'alpha','domain':'remaining'}]
    cr=[row('unknown-year-unit',c[0],None,[0,1,0,0,0]),row('known-year-unit',c[0],2020,[1,0,0,0,0])]
    cp=bind('census-unknown-year',payload(c,cr),(2020,2021))
    co,_=execute(original,'census-unknown-year-original',cp)
    cf,_=execute(repaired,'census-unknown-year-repaired',cp)
    partition_tables=0
    for comparison in co['comparisons'].values():
        for d in DIMS:
            parent=np.array(comparison['domains']['ALL'][d]['design_weighted']['full4x4_including_failure'])
            children=sum((np.array(comparison['domains'][k][d]['design_weighted']['full4x4_including_failure']) for k in ('year:2020','year:unknown')),start=np.zeros((4,4)))
            assert close(parent,children);partition_tables+=1
    check('calendar plus unknown buckets reconstruct ALL16-state tables',True,{'tables_checked':partition_tables,'unknown_source_row_not_dropped':True})
    check('BUG reproduced: ID census incorrectly implies year-source completeness',co['analysis_scopes']['year:2021']['population_N']==0 and co['analysis_scopes']['year:2021']['source_status']=='NA(no_observed_source_in_censused_parent_scope)' and co['attention']['rule']['year:2020']['S']['q_status']=='defined',{'empty_year_original':co['analysis_scopes']['year:2021'],'nonempty_original_p_q_status':['defined','defined'],'possible_completion_1':'null unit is 2021 => year2021 is nonempty','possible_completion_2':'null unit is 2020 => true annual S q=p=1/2, original reports1'})
    check('candidate repair distinguishes incomplete membership from no source',cf['analysis_scopes']['year:2021']['population_N'] is None and cf['analysis_scopes']['year:2021']['source_status']=='NA(no_assigned_year_observation_unresolved_parent_source_year)' and cf['analysis_scopes']['year:2020']['population_N'] is None and cf['attention']['rule']['year:2020']['S']['p'] is None and cf['attention']['rule']['year:2020']['S']['q_status']=='unresolved_source_year_membership',{'empty_source_status':cf['analysis_scopes']['year:2021']['source_status'],'nonempty_p_q_status':cf['attention']['rule']['year:2020']['S']['q_status']})
    check('repair retains unknown bucket, known diagnostics, original W and ALL gate',cf['year_metadata']['unknown_policy_year_assigned_n']==1 and cf['attention']['rule']['year:unknown']['E']['design_weighted']['known_positive']==1 and cf['attention']['rule']['year:2020']['S']['known_hit_coverage']==1 and cf['design']['shared_replicate_weights_sha256']==co['design']['shared_replicate_weights_sha256'] and cf['numeric_targets']==co['numeric_targets'] and cf['project_review']==co['project_review'],{'unknown_assigned_n':1,'known-year-diagnostic_S':1,'unknown_weight_not_imputed':True})
    evidencep=bind('census-unknown-with-no-source-evidence',payload(c,cr),(2020,2021),('year:2021',))
    evidenceout,_=execute(repaired,'census-unknown-no-source-evidence-repaired',evidencep)
    check('independent frozen no-source evidence retains precedence',evidenceout['analysis_scopes']['year:2021']['population_N']==0 and evidenceout['attention']['rule']['year:2021']['S']['p_status']=='NA(no_observed_source)' and evidenceout['analysis_scopes']['department:alpha|year:2021']['population_N']==0 and evidenceout['attention']['rule']['year:2020']['S']['q'] is None,{'no_source_global_and_child_N':0,'unknown_unit_retained':True,'year2020_still_unresolved':True})
    # Unknown membership in alpha must not contaminate a separately complete beta census.
    localhs=c+[{'id':'d','N':1,'n':1,'department':'beta','domain':'exposed'}]
    localp=bind('local-parent-unknown',payload(localhs,cr+[row('beta-known',localhs[1],2020,[1,0,0,0,0])]),(2020,2021))
    localout,_=execute(repaired,'local-parent-unknown-repaired',localp)
    check('source incompleteness blockers apply to affected parents only',localout['attention']['rule']['department:beta|year:2020']['S']['q']==1 and localout['analysis_scopes']['department:beta|year:2021']['population_N']==0 and localout['attention']['rule']['department:alpha|year:2020']['S']['q'] is None,{'beta_complete_q':1,'alpha_unresolved_q':None})

    zhs=[{'id':'z','N':4,'n':4,'department':'alpha'}]
    zrs=[row('zero0',zhs[0],2020,[0,0,0,0,0]),row('zero1',zhs[0],2020,[0,0,0,0,0]),row('zero2',zhs[0],2021,[1,0,0,0,0]),row('zero3',zhs[0],2021,[0,0,0,0,0])]
    zp=bind('zero-states',payload(zhs,zrs),(2020,2021,2022));zo,_=execute(original,'zero-states-original',zp)
    zf,_=execute(repaired,'zero-states-repaired',zp)
    check('real dimension zero, all-zero labels, no-source remain distinct',zo['attention']['rule']['year:2021']['E']['p']==zo['attention']['rule']['year:2021']['E']['q']==0 and zo['attention']['rule']['year:2020']['S']['p']==0 and zo['attention']['rule']['year:2020']['S']['q'] is None and zo['attention']['rule']['year:2020']['S']['q_status']=='NA(no_dimension_mentions)' and zo['attention']['rule']['year:2022']['S']['p'] is None,{'dimension_zero':[0,0],'all_dimensions_zero':[0,None],'no_source':[None,None]})
    check('repair preserves complete annual numerical results',all(zo['attention'][m][k][d][f]==zf['attention'][m][k][d][f] for m in METHODS for k in zo['attention'][m] for d in DIMS for f in ('known_hit_coverage','known_hit_attention_share','p','q','p_status','q_status') if 'year:' in k),{'complete_case':'zero-states'})
    uhs=[{'id':'u','N':5,'n':5,'department':'alpha'}]
    urs=[row('u'+str(i),uhs[0],2020,[0,0,0,0,0]) for i in range(5)]
    urs[0]['outputs'].pop('rule');urs[1]['outputs']['rule']={'status':'execution_failure','labels':None}
    urs[2]['outputs']['rule']['labels']['S']=None;urs[2]['outputs']['rule']['dimension_status']={'S':'execution_failure'}
    urs[3]['outputs']['rule']['labels']['S']=None;urs[4]['outputs']['rule']['labels']['E']=1
    up=bind('label-unresolved',payload(uhs,urs),(2020,));uo,_=execute(original,'label-unresolved-original',up)
    U=uo['attention']['rule']['year:2020']['S']
    utable=uo['comparisons']['rule_vs_reference']['domains']['year:2020']['S']['design_weighted']['full4x4_including_failure']
    check('unresolved labels retained in annual16-state confusion table',utable==[[1.,0.,0.,0.],[0.,0.,0.,0.],[1.,0.,0.,0.],[3.,0.,0.,0.]],{'matrix':utable,'null_state':2,'failure_state':3,'total_weight':5})
    check('semantic null and three failure processes retain assigned mass',U['p'] is None and U['q'] is None and U['design_weighted']['assigned_weight_total']==5 and U['design_weighted']['unresolved_total']==4 and U['raw']['semantic_null']==1 and all(t['raw_n']==1 for t in U['failure_process_subtypes'].values()) and close(U['unknown_coverage_bounds_not_CI'],[0,.8]) and close(U['unknown_share_bounds_conditional_on_positive_total_not_CI'],[0,.8]),{'assigned':5,'semantic_null':1,'three_failure_subtypes_each':1,'S_p_and_q_bounds':[0,.8]})
    nonp=copy.deepcopy(mainp);nonp['metadata']['design']['kind']='nonprobability'
    no,ncaps=execute(original,'nonprobability-original',nonp);nf,nfcaps=execute(repaired,'nonprobability-repaired',nonp)
    check('nonprobability stays descriptive without W or population CI',ncaps==nfcaps==[] and no['attention']['rule']['year:2020']['S']['known_coverage_CI']['CI95'] is None and no['design']['replicate_weight_generation_count']==0,{'generated_W':0,'population_CI':None})

    # Binding/error controls start with genuinely saved frozen synthetic maps.
    for name,mutate in [('changed-year',lambda p:p['records'][0].update(policy_year=2021)),
                        ('omitted-year',lambda p:p['records'][0].pop('policy_year')),
                        ('bool-year',lambda p:p['records'][0].update(policy_year=True)),
                        ('string-year',lambda p:p['records'][0].update(policy_year='2020')),
                        ('unfrozen-map',lambda p:p['metadata']['year_mapping'].update(frozen_before_labels=False)),
                        ('missing-map',lambda p:p['metadata'].pop('year_mapping'))]:
        bad=copy.deepcopy(mainp);mutate(bad);expect_reject(original,'reject '+name,bad)
    labelchange=copy.deepcopy(mainp);labelchange['records'][0]['outputs']['rule']['labels']['S']=0
    original.prepare(labelchange)
    check('source-year projection independent of label changes',labelchange['metadata']['year_mapping']['joined_projection_sha256']==mainp['metadata']['year_mapping']['joined_projection_sha256'],{'binding_unchanged':True,'synthetic_only':True})
    collision=bind('contradict-no-source',mainp,(2020,2021),('year:2020',))
    expect_reject(original,'reject no-source against known assigned year',collision)
    unknownabs=bind('unknown-not-no-source',cp,(2020,2021),('year:unknown',))
    expect_reject(original,'reject unknown bucket as calendar no-source',unknownabs)
    unsealed=copy.deepcopy(mainp);unsealed['data_role']='sealed_project'
    expect_reject(original,'reject unsealed project before labels',unsealed)

    # Independent complete-return regression, no author controls imported.
    regress=[]
    for named,prob,stage in itertools.product((False,True),(False,True),('human_first','machine_reference','combined')):
        p=strip(mainp)
        if not named:
            for h in p['metadata']['design']['strata']:h.pop('domain')
        if not prob:p['metadata']['design']['kind']='nonprobability'
        p['metadata']['analysis_stage']=stage
        active={'human_first':('A','B'),'machine_reference':('reference','rule','LLM'),'combined':METHODS}[stage]
        for r in p['records']:r['outputs']={m:r['outputs'][m] for m in active}
        a=old.analyze(p,16,20261010,'none');b=original.analyze(p,16,20261010,'none');d=repaired.analyze(p,16,20261010,'none')
        regress.append({'named':named,'probability':prob,'stage':stage,'guard':'none','complete_return_equal':a==b==d})
    for guard in ('single_category','joint_table'):
        p=strip(mainp)
        a=old.analyze(p,16,20261010,guard);b=original.analyze(p,16,20261010,guard);d=repaired.analyze(p,16,20261010,guard)
        regress.append({'named':True,'probability':True,'stage':'combined','guard':guard,'complete_return_equal':a==b==d})
    write('legacy-independent-regression.json',regress)
    check('legacy entire analyze return unchanged across independent cases',all(x['complete_return_equal'] for x in regress),{'cases':len(regress),'old_and_original_and_repaired_equal':True})
    oldo=old.analyze(strip(mainp),5000,20261010,'single_category')
    check('enabling years preserves old scopes, ALL targets, project review and design W',all(mainout['analysis_scopes'][k]==v for k,v in oldo['analysis_scopes'].items()) and mainout['design']==oldo['design'] and mainout['numeric_targets']==oldo['numeric_targets'] and mainout['project_review']==oldo['project_review'] and all(mainout['attention'][m][k]==oldo['attention'][m][k] for m in METHODS for k in oldo['attention'][m]),{'original_scopes':len(oldo['analysis_scopes']),'year_or_CI_gate_added':False})
    check('original sources and delivery outputs preserved',source_before=={str(p):digest(p) for p in source_paths},{'files_unchanged':len(source_paths)})
    finding={'id':'YEAR-001','priority':'P1','type':'incorrect_inference_from_incomplete_source_membership',
      'original_file':str(NEW/'metrics_engine.py'),'original_lines':[389,397,413,423,426],
      'title':'ID census does not make source-year assignments complete',
      'trigger':'A census parent has at least one policy_year=null and requested/observed calendar years.',
      'original_behavior':'Empty known-year mask gets precise population_N=0 and no-source status; observed known-year subset gets exact population_N and final q/p despite unresolved membership.',
      'counterexample':'Two census units: one known2020=S1, one null-year=E1. If null resolves2021, year2021 is nonempty; if resolves2020, full annual S q=p=1/2 instead of original1.',
      'repair':'Track unresolved source-year mass per parent; calendar N unknown, final q/p unresolved, retain known-year diagnostics and unknown buckets. Explicit frozen no-source declaration can separately resolve its target scope.',
      'original_status':'unmodified','repair_status':'candidate_saved_and_constructed_controls_passed_not_promoted'}
    report={'schema':'independent-year-engine-ai-technical-audit-v1','generated_at':datetime.now(timezone.utc).isoformat(),
      'identity':{'role':'AI technical auditor','not_human_expert_or_formal_validation':True,'requested_model_constraint':'gpt-6.1-sol ultra; no Astra'},
      'status':'original_has_confirmed_source_year_membership_bug_candidate_repair_verified',
      'scope':{'synthetic_only':True,'real_labels_or_gold_read':0,'real_800_or_4481_data_read':0,'real_annual_statistics_computed':0,'author_run_controls_executed':False,'writes_confined_to':str(HERE)},
      'evidence_policy':'Author control-report is read as context and integrity evidence only; findings and checks come from independent constructed inputs, hand fractions, exhaustive n=2 FPC draws and actual API execution.',
      'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
      'findings':[finding],'checks':CHECKS,'passed_independent_checks':len(CHECKS),
      'coverage':{'annual_HT_denominator':'verified original N_h/n_h, Nhat10 versus raw n4',
        'q_p_multilabel':'verified separate method B denominators; q sum1, p sum9/5',
        'full_design_Rao_Wu_FPC':'one 5000x6 W, original FPCs, four exhaustive draws, all full-length masks',
        'year_as_layer':'no new layer; year-local finite guards explicitly unavailable',
        'gates':'ALL only; no annual point/CI/halfwidth threshold; legacy project review preserved',
        'unknown_NA_zero':'label failure/null and true-zero cases pass; source-year census inference bug confirmed',
        'bindings':'actual constructed source artifacts and independent projection hash; mutated/year-missing/unsealed rejects',
        'legacy':'14 independent complete-return old/original/repaired comparisons pass'},
      'limits':['No source-date truth, human identity, or real-world label validity authenticated.',
        'Source mapping engine validates submitted projection binding but does not open the external source artifact, as disclosed by its contract.',
        'Only the published views are generated; standalone domain×year views are not implemented (domain×department×year views are).',
        'No source/component/series sensitivity scenarios, year differences, trend or causal conclusions were calculated.',
        'Known diagnostic intervals/bounds exclude unresolved source-year membership; candidate marks this explicitly.'],
      'contract_change':{'file':'input-contract-repaired.json','status':'incomplete source-year membership blocks complete annual p/q; independent no-source declarations remain admissible','new_numeric_gate':False},
      'inputs':source_before,'legacy_regression':'legacy-independent-regression.json'}
    write('audit.json',report)
    write('input-seal.json',{'schema':'file-sha256-seal-v1','role':'independent_synthetic_audit_inputs',
         'read_only_original_files':source_before,'constructed_inputs':{str(p.relative_to(HERE)):digest(p) for p in sorted((HERE/'cases').glob('*input.json'))},
         'constructed_frozen_source_year_maps':{str(p.relative_to(HERE)):digest(p) for p in sorted((HERE/'cases').glob('*source-year-map.json'))},
         'real_data_inputs':0,'self_excluded':True})
    print(json.dumps({'status':report['status'],'checks':len(CHECKS),'findings':1,'audit':str(HERE/'audit.json')},ensure_ascii=False))

if __name__=='__main__':main()
