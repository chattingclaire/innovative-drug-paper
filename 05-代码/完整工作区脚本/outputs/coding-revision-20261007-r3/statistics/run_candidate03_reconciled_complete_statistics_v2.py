"""Explicit reconciled196+25 candidate03 copy; preserves both earlier sealed drivers.
SHA-bound, post-exposure development statistics. Does not rewrite final tables.
Future LLM03 requires its own completed execution audit and separately confirmed binding.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from collections import Counter
import argparse,copy,datetime,hashlib,json,math,platform,sys,importlib.util
import candidate03_reconciled_execution_profile_v2 as reconciled_v2
import numpy as np
import statistical_core_r3 as c
import statistical_extensions_r3 as e
import final_binding_io_r3 as io
from run_final_statistics_r3 import classification,binding_leaves,point_undefined_reasons

CELLS=('TP','FP','FN','TN')
KEYS=('component','group','weighting','method','reference','dimension')

def verify_tree(obj):
    leaves=list(binding_leaves(obj))
    for x in leaves:assert c.sha(x['path'])==x['sha256'],x['path']
    return leaves

def same(a,b):
    assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10)),(a,b)

def exact_metrics(z):
    a,b,f,d=z;n=sum(z)
    div=lambda x,y:x/y if y else None
    p=div(a+b,n);q=div(a+f,n);po=div(a+d,n)
    pe=p*q+(1-p)*(1-q) if n else None
    return dict(zip(c.METRIC_NAMES,[div(po-pe,1-pe) if n else None,po,div(a,a+b),div(a,a+f),div(2*a,2*a+b+f),p,q]))

def scopes(component):
    return c.groups_and_weights(component)+([(g,'eligible_design_weighted') for g in c.GROUPS] if component=='probability_canonical' else [])

def empty_record(method,ref,dim,is_ac=False):
    names=('kappa','agreement','left_positive_rate','right_positive_rate') if is_ac else c.METRIC_NAMES
    ci={'low':None,'high':None,'defined_repetitions':0,'undefined_repetitions':0,'not_run_reason':'no NHC challenge sample; no repetitions attempted'}
    r={'component':'enriched_challenge','group':'NHC','weighting':'unweighted','method':method,'reference':ref,'dimension':dim,'unit_frame_n':0,'paired_n':0,'excluded_pending_n':0,'paired_ids':[],'excluded_ids':[],
       'left_positive_n':0,'reference_positive_n':0,'raw_confusion':dict.fromkeys(CELLS,0),'weighted_confusion':dict.fromkeys(CELLS,0.0),
       'metrics':{n:{'estimate':None,'ci95_primary':dict(ci),'ci95_source_file_conditional_sensitivity':dict(ci)} for n in names},
       'undefined_point_reasons':dict.fromkeys(names,'no NHC challenge sample'),
       'primary_bootstrap_mechanism':None,'absent_stratum':True,'material_version':'v14'}
    if is_ac:
        r['symmetric_raw_cells']=dict(zip(('A1_C1','A1_C0','A0_C1','A0_C0'),r.pop('raw_confusion').values()))
        r['symmetric_weighted_cells']=dict(zip(('A1_C1','A1_C0','A0_C1','A0_C0'),r.pop('weighted_confusion').values()))
    return r

def complete_classification(ctx,methods,refs):
    records,ac=classification(ctx,methods,refs);cache={}
    for group in c.GROUPS:
        ids=sorted(rid for rid,x in ctx['sample'].items() if x['component']=='probability_canonical' and x['group']==group)
        for method,rows in methods.items():
            for reference,target in refs.items():
                for dim in c.DIMS:
                    row=c.comparison(ctx,rows,target,dim,ids,'probability_canonical',group,'eligible_design_weighted',method,reference,cache)
                    row['undefined_point_reasons']=point_undefined_reasons(row);row['material_version']=ctx['material_version'];records.append(row)
        for dim in c.DIMS:
            row=c.comparison(ctx,refs['A'],refs['C'],dim,ids,'probability_canonical',group,'eligible_design_weighted','A_C','symmetric A/C',cache)
            row['undefined_point_reasons']=point_undefined_reasons(row)
            row['symmetric_raw_cells']=dict(zip(('A1_C1','A1_C0','A0_C1','A0_C0'),row.pop('raw_confusion').values()))
            row['symmetric_weighted_cells']=dict(zip(('A1_C1','A1_C0','A0_C1','A0_C0'),row.pop('weighted_confusion').values()))
            row['material_version']=ctx['material_version'];ac.append(row)
    records.extend(empty_record(m,r,d) for m in methods for r in refs for d in c.DIMS)
    ac.extend(empty_record('A_C','symmetric A/C',d,True) for d in c.DIMS)
    return records,ac

def probability_attention(ctx,methods,refs):
    all_rows={**refs,**methods};ids=sorted(rid for rid,x in ctx['sample'].items() if x['component']=='probability_canonical')
    assert e.common_complete_mask(list(all_rows.values()),ids).all()
    pairs=[(m,r) for m in methods for r in refs]+list(combinations(methods,2))+[('A','C')]
    cache={};profiles=[];paired=[]
    for group,kind in scopes('probability_canonical'):
        chosen=[rid for rid in ids if group=='ALL' or ctx['sample'][rid]['group']==group]
        for name,rows in all_rows.items():profiles.append(e.attention_profile(ctx,rows,chosen,'probability_canonical',group,kind,name,cache))
        for one,two in pairs:
            paired.append({'group':group,'weighting':kind,'method_one':one,'method_two':two,**e.paired_attention_difference(ctx,all_rows[one],all_rows[two],chosen,'probability_canonical',group,kind,cache)})
    mechanism='department_unit_rescaled_SRSWOR';factors=c.replicate_factors(ctx,ids,'probability_canonical',mechanism)
    w=c.weighting(ctx,ids,'eligible_design_weighted');department=[]
    for name,rows in all_rows.items():
        hits=np.asarray([[c.label(rows[rid],d) for d in c.DIMS] for rid in ids],float);points={};boots={}
        for group in c.GROUPS:
            mask=np.asarray([ctx['sample'][rid]['group']==group for rid in ids]);points[group]=e.attention_share(w[mask]@hits[mask]);boots[group]=e.attention_share((factors[:,mask]*w[mask])@hits[mask])
        for one,two in combinations(c.GROUPS,2):
            delta=points[one]-points[two];rep=boots[one]-boots[two]
            department.append({'method':name,'department_one':one,'department_two':two,'difference_direction':'department_one_minus_department_two','primary_bootstrap_mechanism':mechanism,'unit_frame_n_per_department':60,'dimensions':{d:{'difference_percentage_points':c.safe(100*delta[j]),'ci95_percentage_points':c.interval(100*rep[:,j])} for j,d in enumerate(c.DIMS)}})
    return {'scope':'same180 probability canonical representatives; N_h/60 weights, not all4481 units','profiles':profiles,'paired_method_differences':paired,'department_differences':department,'interpretation':'Post-exposure descriptive development comparison. Intervals condition on fixed labels and algorithms; do not correct development overfit, measure semantic truth, or establish equivalence.'}

def load_methods(dev,manifest,ctx):
    reconciled_v2.development_header(dev)
    result={};audit={}
    for name,item in dev['methods'].items():
        assert item['material_version']=='v14' and item['all240_exposed'] is True
        rows=io.bound_jsonl(item['output'])
        assert set(rows)==set(ctx['inputs']) and len(rows)==4924
        assert all(c.binary(c.label(x,d)) for x in rows.values() for d in c.DIMS)
        if item['kind']=='rules':
            binding=io.bound(item['source_candidate_binding']);verify_tree(binding)
            assert binding['prediction']==item['output'] and binding['not_independent_validation'] and binding['exposed240_used_for_development']
            assert binding['reference_labels_edited'] is False and binding['scope_closed'] is True
            qa=io.bound(binding['QA']);run=io.bound(binding['run'])
            assert qa['all_checks_pass'] and run['n']==4924 and run['pending_n']==0
            assert run['input_sha256']==manifest['material']['rule_inputs']['sha256']
            assert run['prediction_sha256']==item['output']['sha256']
            for path,digest in run['runtime_code_sha256'].items():assert c.sha(path)==digest
            audit[name]={'source_binding':item['source_candidate_binding'],'execution_QA':binding['QA'],'all4924_binary':True,'runtime_code_hash_count':len(run['runtime_code_sha256'])}
        elif item['kind']=='LLM':
            assert name==reconciled_v2.STAT_KEY and item['frozen_method_id']==reconciled_v2.METHOD
            adapter=io.bound(item['execution_adapter']);verify_tree(adapter)
            assert adapter['status']==reconciled_v2.ADAPTER_STATUS and adapter['root_confirmed'] is True
            assert adapter['material_input']==manifest['material']['llm_inputs'] and adapter['output']==item['output']
            module_path=Path(__file__).resolve().parent.parent/'manuscript-update-20261008/measurement-adapter-v2/assemble_manuscript_payload_r3.py'
            spec=importlib.util.spec_from_file_location('reconciled_measurement_v2',module_path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            actual_io=module.BoundIO()
            checked=reconciled_v2.verify_complete(adapter['source_full_binding'],actual_io,rows)
            actual_io.unchanged()
            audit[name]={'execution_adapter':item['execution_adapter'],'actual_profile_audit':checked,'all4924_binary':True,'stability':'not evaluated; no candidate02 reuse'}
        else:raise ValueError(item['kind'])
        result[name]=rows
    return result,audit

def exact_point_audit(ctx,methods,refs,records,ac,dev,attention):
    checked=0;rows_exact=[]
    for row in records+ac:
        ids=[rid for rid,x in ctx['sample'].items() if x['component']==row['component'] and (row['group']=='ALL' or x['group']==row['group'])]
        left,right=(refs['A'],refs['C']) if row['method']=='A_C' else (methods[row['method']],refs[row['reference']])
        raw=[0]*4;z=[F(0)]*4
        for rid in ids:
            a,b=c.label(left[rid],row['dimension']),c.label(right[rid],row['dimension']);j={(1,1):0,(1,0):1,(0,1):2,(0,0):3}[a,b]
            raw[j]+=1;z[j]+=F(ctx['sample'][rid]['canonical_frame_N'],60) if row['weighting']=='eligible_design_weighted' else F(1)
        rawkey='symmetric_raw_cells' if row['method']=='A_C' else 'raw_confusion';wkey='symmetric_weighted_cells' if row['method']=='A_C' else 'weighted_confusion'
        assert list(row[rawkey].values())==raw
        for a,b in zip(row[wkey].values(),z):same(a,float(b))
        mm=exact_metrics(z)
        for metric,v in row['metrics'].items():same(v['estimate'],float(mm[metric]) if mm[metric] is not None else None);checked+=1
        rows_exact.append({**{k:row[k] for k in KEYS},'exact_cells':list(map(str,z)),'exact_metrics':{k:str(v) if v is not None else None for k,v in mm.items()}})
    previous_checks=0
    for audit in dev['previous_point_audits']:
        previous=io.bound(audit['binding'])['comparisons'];lookup={tuple(x[k] for k in KEYS):x for x in previous}
        for row in records:
            if row['method']!=audit['method']:continue
            key=tuple(audit['previous_method'] if k=='method' else row[k] for k in KEYS);old=lookup[key]
            assert old['raw_confusion']==row['raw_confusion']
            for metric in row['metrics']:same(row['metrics'][metric]['estimate'],old['metrics'][metric]['estimate']);previous_checks+=1
    ac_old=io.bound(dev['existing_AC_statistics'])['comparisons'];ac_lookup={tuple(x[k] for k in KEYS):x for x in ac};ac_checks=0
    for old in ac_old:
        now=ac_lookup[tuple(old[k] for k in KEYS)];assert now['symmetric_raw_cells']==old['symmetric_raw_cells']
        for metric in now['metrics']:same(now['metrics'][metric]['estimate'],old['metrics'][metric]['estimate']);ac_checks+=1
    # Independent rational attention totals, ratios, and paired/department deltas.
    all_rows={**refs,**methods};qlookup={};qchecks=0
    for row in attention['profiles']:
        ids=row['complete_support_ids'];w=[F(ctx['sample'][rid]['canonical_frame_N'],60) if row['weighting']=='eligible_design_weighted' else F(1) for rid in ids]
        totals=[sum((ww*c.label(all_rows[row['method']][rid],dim) for rid,ww in zip(ids,w)),F(0)) for dim in c.DIMS];den=sum(totals)
        q=[t/den if den else None for t in totals];qlookup[row['group'],row['weighting'],row['method']]=q
        for dim,t,v in zip(c.DIMS,totals,q):
            same(row['dimensions'][dim]['weighted_known_coding_count'],float(t));same(row['dimensions'][dim]['attention_share'],float(v) if v is not None else None);qchecks+=2
    for row in attention['paired_method_differences']:
        one=qlookup[row['group'],row['weighting'],row['method_one']];two=qlookup[row['group'],row['weighting'],row['method_two']]
        for dim,a,b in zip(c.DIMS,one,two):same(row['dimensions'][dim]['estimate'],float(a-b) if a is not None and b is not None else None);qchecks+=1
    for row in attention['department_differences']:
        one=qlookup[row['department_one'],'eligible_design_weighted',row['method']];two=qlookup[row['department_two'],'eligible_design_weighted',row['method']]
        for dim,a,b in zip(c.DIMS,one,two):same(row['dimensions'][dim]['difference_percentage_points'],float(100*(a-b)) if a is not None and b is not None else None);qchecks+=1
    return {'pass':True,'new_Fraction_classification_metric_checks':checked,'previous_exact_development_metric_checks':previous_checks,'existing_formal_AC_metric_checks':ac_checks,'Fraction_attention_and_difference_checks':qchecks,'exact_rows':rows_exact}

def interval_audit(objects):
    rows=[]
    def walk(x,path):
        if isinstance(x,dict):
            if {'low','high','defined_repetitions','undefined_repetitions'}<=set(x):
                if 'not_run_reason' not in x:assert x['defined_repetitions']+x['undefined_repetitions']==5000,path
                if x['defined_repetitions']:assert x['low'] is not None and x['high'] is not None and x['low']<=x['high']
                else:assert x['low'] is None and x['high'] is None
                rows.append({'path':path,**x})
            else:
                for k,v in x.items():walk(v,path+'/'+str(k))
        elif isinstance(x,list):
            for i,v in enumerate(x):walk(v,path+'/'+str(i))
    walk(objects,'')
    return {'checked_interval_n':len(rows),'partly_or_wholly_undefined': [r for r in rows if r['undefined_repetitions'] or r['defined_repetitions']==0],
        'defined_endpoint_degenerate_n':sum(r['defined_repetitions']>0 and r['low']==r['high'] for r in rows),'absent_stratum_no_bootstrap_n':sum('not_run_reason' in r for r in rows)}

def replication_audit(ctx):
    result=[]
    for comp in ('probability_canonical','enriched_challenge'):
        for group in ('ALL',)+c.GROUPS:
            ids=sorted(rid for rid,x in ctx['sample'].items() if x['component']==comp and (group=='ALL' or x['group']==group))
            if not ids:continue
            mech='department_unit_rescaled_SRSWOR' if comp=='probability_canonical' else 'department_unit_conditional_WR'
            value=(2026100731+int(hashlib.sha256('/'.join((comp,mech,'/'.join(ids))).encode()).hexdigest()[:8],16))%(2**32)
            rng=np.random.default_rng(value);direct=np.zeros((5000,len(ids)))
            for g in c.GROUPS:
                pos=[i for i,rid in enumerate(ids) if ctx['sample'][rid]['group']==g]
                if not pos:continue
                n=len(pos)
                if comp=='probability_canonical':
                    m=n-1;count=rng.multinomial(m,[1/n]*n,size=5000);scale=math.sqrt(1-n/ctx['design']['frame_N_by_group'][g]);z=(1-scale)+(scale*n/m)*count
                else:z=rng.multinomial(n,[1/n]*n,size=5000)
                direct[:,pos]=z
            actual=c.replicate_factors(ctx,ids,comp,mech)
            assert np.allclose(actual,direct,rtol=0,atol=1e-14)
            nhc=[i for i,rid in enumerate(ids) if ctx['sample'][rid]['group']=='NHC']
            if nhc:assert np.array_equal(actual[:,nhc],np.ones((5000,len(nhc))))
            result.append({'component':comp,'group':group,'mechanism':mech,'seed':value,'ids':ids,'replicate_factor_float64_c_order_sha256':hashlib.sha256(actual.tobytes()).hexdigest(),'repetitions':5000,'direct_equivalent_formula_check':True})
    return result

def fmt(v):return 'NA' if v is None else f'{v:.3f}'
def cifmt(m):
    ci=m['ci95_primary'];return f"{fmt(m['estimate'])} [{fmt(ci['low'])}, {fmt(ci['high'])}]"

def readable(records,ac,attention):
    out=['# 规则v36.2与LLM03单元隔离恢复完整开发统计（既有240条已暴露）','','原197批协议保留为技术不完整；新方法由196个原批次与25个独立单元请求组成。原始标签、样本、正式v33表不变。A/C/T均为AI判读，候选参照按冻结政策合成；本表不能作为独立效度验证。概率180与富集挑战60分开。κ是二元Cohen κ，设计加权指四格使用N_h/60，不是ordinal weighted κ。','',
    '概率框947/760/60；主区间为5000次部门分层单位重标SRSWOR的非线性percentile区间，固定原材料、算法与标签。卫健60为该框普查，主区间可退化为点。挑战区间为条件WR描述性重采样，不外推总体。JSON另保留来源文件WR构成敏感性区间，不能混称主CI。零分母为NA；0.8不是普遍发表线。','',
    '每行依次给κ及95%主区间、P/R/F1点值；各自P/R/F1区间、全部原始/设计加权四格和未定义重复次数见JSON。分部门设计权重恒定，另存加权行可直接核对未加权结果。','']
    for comp,weight,title in [('probability_canonical','eligible_design_weighted','概率180：设计加权'),('probability_canonical','unweighted','概率180：未加权'),('enriched_challenge','unweighted','挑战60：条件诊断')]:
        out += ['## '+title,'','|部门|方法|参照|维度|κ [95%区间]|P|R|F1|原始TP/FP/FN/TN|','|---|---|---|---|---|---:|---:|---:|---|']
        for r in records:
            if r['component']!=comp or r['weighting']!=weight:continue
            out.append('|'+ '|'.join([r['group'],r['method'],r['reference'],r['dimension'],cifmt(r['metrics']['kappa']),*[fmt(r['metrics'][x]['estimate']) for x in ('precision','recall','f1')],'/'.join(map(str,r['raw_confusion'].values()))])+'|')
        out+=['','|部门|A/C裁定前维度|κ [95%区间]|A1C1/A1C0/A0C1/A0C0|','|---|---|---|---|']
        for r in ac:
            if r['component']==comp and r['weighting']==weight:out.append('|'+ '|'.join([r['group'],r['dimension'],cifmt(r['metrics']['kappa']),'/'.join(map(str,r['symmetric_raw_cells'].values()))])+'|')
        out.append('')
    out+=['## 同180注意力q：设计加权','','|部门|标签流|S %|E %|Ec %|I %|F %|','|---|---|---:|---:|---:|---:|---:|']
    for r in attention['profiles']:
        if r['weighting']=='eligible_design_weighted':out.append('|'+ '|'.join([r['group'],r['method'],*[fmt(100*r['dimensions'][d]['attention_share']) if r['dimensions'][d]['attention_share'] is not None else 'NA' for d in c.DIMS]])+'|')
    out+=['','注意力q=该维编码句次/五维编码句次总和；单元coverage另列为known_label_hit_rate_diagnostic，不混用。JSON给各q主CI、与各参照的配对q差值、三组部门差值及主CI。聚合一致不能取代单元效度。']
    return '\n'.join(out)+'\n'

def main():
    p=argparse.ArgumentParser();p.add_argument('--bindings',type=Path,required=True);p.add_argument('--bindings-sha256',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert not a.out.exists(),'Preserve prior runs: output must be a new directory'
    assert c.sha(a.bindings)==a.bindings_sha256
    dev=c.read(a.bindings)
    reconciled_v2.development_header(dev)
    assert dev['stage']=='development_only_all240_exposed' and dev['root_development_bindings_confirmed'] is True
    assert dev['independent_validation'] is False and dev['human_validation_completed'] is False
    leaves=verify_tree(dev);manifest=io.bound(dev['reference_manifest']);leaves+=verify_tree(manifest)
    mathqa=io.bound(dev['mathematical_QA']);assert mathqa['status']=='pass_label_free_frame_and_synthetic_mathematical_QA'
    for module in ('statistical_core_r3.py','statistical_extensions_r3.py'):assert c.sha(Path(__file__).with_name(module))==mathqa['code_sha256'][module]
    assert c.B==5000 and c.BASE_SEED==2026100731
    ctx=io.context_from_manifest(manifest);refs,refaudit=io.final_references(manifest,ctx)
    saved_candidate=io.bound_jsonl(dev['existing_candidate_reference'])
    assert set(saved_candidate)==set(refs['candidate'])
    assert all(c.label(saved_candidate[rid],d)==c.label(refs['candidate'][rid],d) for rid in saved_candidate for d in c.DIMS)
    methods,methodaudit=load_methods(dev,manifest,ctx)
    print(json.dumps({'status':'validated_inputs_running_5000_replicates','methods':list(methods)},ensure_ascii=False),flush=True)
    records,ac=complete_classification(ctx,methods,refs);attention=probability_attention(ctx,methods,refs)
    exact=exact_point_audit(ctx,methods,refs,records,ac,dev,attention);reps=replication_audit(ctx);ciqa=interval_audit({'classification':records,'A_C':ac,'attention':attention})
    for x in leaves:assert c.sha(x['path'])==x['sha256'],x['path']
    for name,item in dev['methods'].items():
        if item['kind']=='rules':verify_tree(io.bound(item['source_candidate_binding']))
    prov={'stage':dev['stage'],'all240_exposed':True,'independent_validation':False,'human_validation_completed':False,
          'created_at':datetime.datetime.now().astimezone().isoformat(),'material_version':'v14','bindings':{'path':str(a.bindings.resolve()),'sha256':a.bindings_sha256},
          'script_sha256':c.sha(__file__),'code_bindings':dev['statistical_code'],'math_QA':dev['mathematical_QA'],'analysis_notes':c.analysis_notes(),
          'reference_identity':'A/C/T independent AI sessions, includes explicitly identified replacement/source rereview; not human experts','candidate_policy':'third_for_every_reviewed_dimension;66 T-reviewed all five dimensions,174 A/C-agreed cases',
          'formal_v33_unchanged':True,'no_LLM02_CI_or_stability_reuse':True,'python_version':platform.python_version(),'numpy_version':np.__version__,
          'interval_limit':'Fixed-label/material/algorithm design variability only; does not undo development exposure or quantify semantic-truth/model-run uncertainty.'}
    na=[{**{k:r[k] for k in KEYS},'paired_n':r['paired_n'],'point_NA_reasons':r['undefined_point_reasons'],'metrics':r['metrics']} for r in records+ac if r['undefined_point_reasons']]
    qa={'all_checks_pass':True,'machine_comparisons':len(records),'A_C_comparisons':len(ac),'attention_profiles':len(attention['profiles']),'paired_attention_comparisons':len(attention['paired_method_differences']),'department_attention_comparisons':len(attention['department_differences']),
        'exact_point_crosschecks':{k:v for k,v in exact.items() if k!='exact_rows'},'interval_audit':ciqa,'replication_factor_audits':reps,'all_bound_inputs_unchanged':True,'no_refit_or_threshold_selection':True}
    a.out.mkdir(parents=True,exist_ok=False)
    outputs={'provenance.json':prov,'reference_binding_QA.json':refaudit,'method_execution_binding_QA.json':methodaudit,
             'machine_reference_classification.json':{'provenance':prov,'comparisons':records},'A_C_before_third_agreement.json':{'provenance':prov,'comparisons':ac},
             'probability_attention_and_paired_department_differences.json':{'provenance':prov,**attention},'independent_exact_point_crosscheck.json':exact,
             'NA_and_interval_status.json':{'point_NA':na,'interval_status':ciqa},'complete_statistics_QA.json':qa}
    for name,value in outputs.items():c.write_json(a.out/name,value)
    (a.out/'开发完整统计表.md').write_text(readable(records,ac,attention))
    c.write_json(a.out/'output_freeze.json',{'bindings_sha256':a.bindings_sha256,'files':{p.name:c.sha(p) for p in a.out.iterdir() if p.is_file()}})
    print(json.dumps({'status':'complete_development_statistics_all240_exposed','output':str(a.out),'machine_comparisons':len(records),'A_C_comparisons':len(ac),'point_checks':qa['exact_point_crosschecks'],'interval_n':ciqa['checked_interval_n']},ensure_ascii=False),flush=True)

if __name__=='__main__':
    try: main()
    except (reconciled_v2.ProfileGateError,AssertionError,KeyError,TypeError,ValueError,OSError) as exc:
        print(json.dumps({'status':'BLOCKED_NO_STATISTICS_RELEASED','error':str(exc)},ensure_ascii=False));sys.exit(2)
