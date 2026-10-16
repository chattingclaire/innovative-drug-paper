"""One SHA-bound rerun of frozen R3 mathematics on intact adopted39/intact03.

No classifier/model calls, reference edits, score-driven choice, or manuscript edits.
Raw inputs may contain reserved-family text; they are read mechanically in memory
by the unchanged material/reference validators and never printed or copied here.
"""
import argparse
import contextlib
import csv
import datetime
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
R3 = PROJECT/'outputs/coding-revision-20261007-r3'
STATS = R3/'statistics'
RULE_KEY = 'rules-v39'
LLM_KEY = 'LLM-candidate03-single-unit-reconciled'
DIMS = ('S','E','Ec','I','F')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def binding(path):
    p=Path(path).resolve()
    return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def read(path): return json.loads(Path(path).read_text())
def verify(item):
    assert Path(item['path']).is_absolute() and sha(item['path'])==item['sha256'],item['path']
def leaves(value):
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):yield value
        for x in value.values():yield from leaves(x)
    elif isinstance(value,list):
        for x in value:yield from leaves(x)
def verify_tree(value):
    out=list(leaves(value))
    for item in out:verify(item)
    return out
def write(path,value):
    assert not path.exists(),path
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def boot_modules(spec):
    for item in spec['code_bindings']+spec['existing_dependency_files']:verify(item)
    sys.path.insert(0,spec['existing_jsonschema_dependency_dir'])
    sys.path.insert(0,str(STATS))
    import numpy as np
    import statistical_core_r3 as c
    import statistical_extensions_r3 as e
    import final_binding_io_r3 as io
    import run_development_complete_statistics_r3 as complete
    import run_candidate03_reconciled_full_findings_v2 as full
    import final_attention_r3 as attention
    import candidate03_reconciled_execution_profile_v2 as profile
    assert c.B==5000 and c.BASE_SEED==2026100731
    return np,c,e,io,complete,full,attention,profile

def inputs(spec,io,c,profile):
    adoption=read(spec['adoption_record']['path'])
    assert adoption['status']=='WHOLE_RULE39_ADOPTED_FOR_SYNCHRONIZED_RECALCULATION_LLM03_RETAINED_COMPLETE'
    assert adoption['candidate07_adopted'] is False and adoption['original_AB_T_labels_modified'] is False
    assert adoption['rules']['sha256']==spec['methods'][RULE_KEY]['output']['sha256']
    assert adoption['LLM']['sha256']==spec['methods'][LLM_KEY]['output']['sha256']
    olddev=read(spec['old_development_binding']['path']); verify_tree(olddev)
    manifest=io.bound(olddev['reference_manifest']); verify_tree(manifest)
    mathqa=io.bound(olddev['mathematical_QA'])
    assert mathqa['status']=='pass_label_free_frame_and_synthetic_mathematical_QA'
    for name in ['statistical_core_r3.py','statistical_extensions_r3.py']:
        assert sha(STATS/name)==mathqa['code_sha256'][name]
    # Re-authenticate the existing closed actual LLM lineage before loading rows.
    adapter=io.bound(olddev['methods'][LLM_KEY]['execution_adapter']);verify_tree(adapter)
    assert adapter['status']==profile.ADAPTER_STATUS and adapter['root_confirmed'] is True
    source_header=profile.closed_header(adapter['source_full_binding'])[0]
    assert source_header['output']['sha256']==spec['methods'][LLM_KEY]['output']['sha256']
    ctx=io.context_from_manifest(manifest);refs,refaudit=io.final_references(manifest,ctx)
    saved=io.bound_jsonl(olddev['existing_candidate_reference'])
    assert set(saved)==set(refs['candidate']) and all(c.label(saved[r],d)==c.label(refs['candidate'][r],d) for r in saved for d in DIMS)
    methods={}
    for name,item in spec['methods'].items():
        rows=io.bound_jsonl(item['output'])
        assert len(rows)==4924 and list(rows)==list(ctx['inputs'])
        assert all(c.binary(c.label(row,d)) for row in rows.values() for d in DIMS)
        methods[name]=rows
    ruleqa=io.bound(spec['rules39_mechanical_QA'])
    assert ruleqa.get('status')=='PASS' or ruleqa.get('all_checks_pass') is True or ruleqa.get('all_passed') is True, list(ruleqa)
    assert ruleqa['source_sha256']==manifest['material']['rule_inputs']['sha256']
    assert ruleqa['raw_output_sha256']==spec['methods'][RULE_KEY]['output']['sha256']
    run=io.bound(spec['rules39_full_run_summary']);execution=io.bound(spec['rules39_actual_execution'])
    assert run['input_n']==run['unique_n']==4924 and run['undetermined_n']==0
    assert run['source_input_sha256']==manifest['material']['rule_inputs']['sha256']
    assert run['raw_output_sha256']==spec['methods'][RULE_KEY]['output']['sha256']
    assert execution['status']=='ACTUAL_ONCE_FULL4924_EXIT0' and execution['exit_code']==0 and execution['attempt_n']==1
    assert execution['dependency_freeze_sha256']==spec['rules39_dependency_freeze']['sha256']
    assert execution['entry_sha256']==spec['rules39_actual_entrypoint']['sha256']
    return olddev,manifest,ctx,refs,methods,refaudit

def full_findings(ctx,manifest,methods,refs,full,c):
    full.ctx=ctx
    full.allids={g:sorted(r for r in ctx['inputs'] if ctx['groups'][r]==g) for g in c.GROUPS}
    pids={g:sorted(r for r,x in ctx['sample'].items() if x['component']=='probability_canonical' and x['group']==g) for g in c.GROUPS}
    assert [len(full.allids[g]) for g in c.GROUPS]==[1848,2100,533]
    assert all(len(x)==60 for x in pids.values())
    stems=sorted({ctx['inputs'][r]['input']['original_file_stem'] for g in c.GROUPS for r in full.allids[g]})
    assert len(stems)==51
    full.latest={}
    for st in stems:
        m=ctx['metadata'][st]
        if m['annual_series']:full.latest[m['policy_series']]=max(full.latest.get(m['policy_series'],m['year_in_filename']),m['year_in_filename'])
    scenarios=[(s,None) for s in manifest['robustness_scenarios'] if s!='leave_one_policy_entry_out']
    if 'leave_one_policy_entry_out' in manifest['robustness_scenarios']:
        scenarios.extend(('leave_one_policy_entry_out',st) for st in stems)
    assert len(scenarios)==len(set(scenarios))==56
    compositions=[]
    for scenario,omit in scenarios:
        gids={g:full.ids_for(g,scenario,omit) for g in c.GROUPS}
        key='policy_file' if scenario=='policy_file_equal' else 'policy_series' if scenario=='policy_series_equal' else None
        obj={'scenario':scenario,'omitted_policy_entry':omit,'scope_ids':gids,'methods':{}}
        for name,rows in methods.items():
            values=full.data(rows,gids,key);obj['methods'][name]={'departments':values,'contrasts':full.contrast(values)}
        compositions.append(obj)
    definitions=[]
    for scenario,explanation in full.SCENARIOS.items():
        obj={'scenario':scenario,'explanation':explanation,'methods':{}}
        for name,rows in methods.items():
            derived,changes=full.derive(rows,scenario)
            values=full.data(derived,full.allids);small=full.data(derived,pids)
            obj['methods'][name]={'full4481':{'departments':values,'contrasts':full.contrast(values)},
                'same180':{'departments':small,'contrasts':full.contrast(small)},'removed_labels':changes,
                'removed_labels_by_group_dimension':{g:{d:sum(ctx['groups'][x['id']]==g and x['dimension']==d for x in changes) for d in DIMS} for g in c.GROUPS}}
        definitions.append(obj)
    assert len(definitions)==6
    primary={name:{'departments':full.data(rows,full.allids),'status':'post_exposure_development'} for name,rows in methods.items()}
    same180={name:{'departments':full.data(rows,pids),'status':'AIreference_not_new_human' if name in refs else 'post_exposure_development'} for name,rows in {**refs,**methods}.items()}
    for obj in [*primary.values(),*same180.values()]:obj['contrasts']=full.contrast(obj['departments'])
    metrics=['P_F_given_Ec','P_Ec_given_F','OR']+[f'{s}_{d}' for s in ['attention_share','coverage'] for d in DIMS]
    summary={}
    for name in methods:
        summary[name]={}
        for kind,records in [('definition6',[x['methods'][name]['full4481'] for x in definitions]),('composition56',[x['methods'][name] for x in compositions])]:
            summary[name][kind]={}
            for metric in metrics:
                values=[x['contrasts'][metric]['NHSA_minus_NHC'] for x in records];valid=[v for v in values if v is not None];scale=1 if metric=='OR' else 100
                summary[name][kind][metric]={'scenario_n':len(values),'NHSA_higher_n':sum(v>1e-12 for v in valid),'NHC_higher_n':sum(v< -1e-12 for v in valid),'equal_n':sum(abs(v)<=1e-12 for v in valid),'NA_n':len(values)-len(valid),'NHSA_minus_NHC_range':[min(valid)*scale,max(valid)*scale] if valid else None,'range_units':'OR units' if metric=='OR' else 'percentage points'}
    pair_n=0
    def check(departments):
        nonlocal pair_n
        for group,value in departments.items():
            assert len(value['all10_pairs'])==10 and {(x['dimension_a'],x['dimension_b']) for x in value['all10_pairs']}==set(full.PAIRS)
            for pair in value['all10_pairs']:
                pair_n+=1
                if pair['cell_type']=='raw_counts':
                    assert all(type(pair[k]) is int and pair[k]>=0 for k in full.CELL)
                    assert sum(pair[k] for k in full.CELL)==pair['unit_n']
                    assert pair['a_positive']==value['profile']['coding_count'][pair['dimension_a']]
                    assert pair['b_positive']==value['profile']['coding_count'][pair['dimension_b']]
                else:
                    assert abs(sum(pair['equal_cluster_cell_mixture'][k] for k in full.CELL)-1)<1e-12
                    assert pair['defined_a_clusters']+len(pair['zero_a_clusters_excluded'])==pair['equal_cluster_n']
                    assert pair['defined_b_clusters']+len(pair['zero_b_clusters_excluded'])==pair['equal_cluster_n']
    for obj in [*primary.values(),*same180.values()]:check(obj['departments'])
    for obj in compositions:
        for value in obj['methods'].values():check(value['departments'])
    for obj in definitions:
        for value in obj['methods'].values():check(value['full4481']['departments']);check(value['same180']['departments'])
    flat=[]
    for scope,values in [('full4481',primary),('same180_probability',same180)]:
        for name,obj in values.items():
            for group,value in obj['departments'].items():flat.extend({'scope':scope,'method':name,'department':group,**p} for p in value['all10_pairs'])
    return {'primary_full4481':primary,'same180_primary':same180,'definition6':definitions,'composition56':compositions,'summary':summary},flat,pair_n

def export_classification_csv(path,records):
    names=['component','group','weighting','method','reference','dimension','unit_frame_n','paired_n','excluded_pending_n']
    cells=['TP','FP','FN','TN']
    metric_names=['kappa','agreement','precision','recall','f1','left_positive_rate','right_positive_rate']
    fields=names+[f'raw_{x}' for x in cells]+[f'weighted_{x}' for x in cells]+[f'{m}_{s}' for m in metric_names for s in ['estimate','ci95_low','ci95_high','undefined_repetitions']]
    with path.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
        for row in records:
            out={k:row[k] for k in names};raw=row.get('raw_confusion',row.get('symmetric_raw_cells'));weighted=row.get('weighted_confusion',row.get('symmetric_weighted_cells'))
            out.update({f'raw_{k}':v for k,v in zip(cells,raw.values())});out.update({f'weighted_{k}':v for k,v in zip(cells,weighted.values())})
            for metric,value in row['metrics'].items():
                out.update({f'{metric}_estimate':value['estimate'],f'{metric}_ci95_low':value['ci95_primary']['low'],f'{metric}_ci95_high':value['ci95_primary']['high'],f'{metric}_undefined_repetitions':value['ci95_primary']['undefined_repetitions']})
            writer.writerow(out)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bindings',type=Path,required=True);parser.add_argument('--bindings-sha256',required=True);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    assert sys.flags.optimize==0 and sha(args.bindings)==args.bindings_sha256
    spec=read(args.bindings);all_bound=verify_tree(spec)
    assert spec['entrypoint']['sha256']==sha(__file__)
    np,c,e,io,complete,full,attention,profile=boot_modules(spec)
    olddev,manifest,ctx,refs,methods,refaudit=inputs(spec,io,c,profile)
    if not args.execute:
        path=HERE/'preflight_metadata.json'
        write(path,{'status':'INPUT_CODE_REFERENCE_PREFLIGHT_PASS_NO_STATISTICS_RUN','bindings':binding(args.bindings),
            'source_binding_count':len(all_bound),'complete_machine_rows_per_method':4924,'fixed_reference_rows':240,
            'probability_n':180,'challenge_n':60,'classification_records_expected':420,'frozen_B':5000,'frozen_seed':2026100731,
            'protected_material_manually_read':False,'model_calls':0,'new_dependency_installs':0})
        print(json.dumps(binding(path),ensure_ascii=False));return
    out=Path(spec['output_directory']);assert not out.exists(),'One run only; never overwrite previous output'
    out.mkdir(parents=True,exist_ok=False)
    print(json.dumps({'status':'RUNNING_ONCE_FROZEN5000_NO_MODEL','output':str(out)},ensure_ascii=False),flush=True)
    prov={'stage':'post_exposure_fixed_reference_synchronized_statistics','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'material_version':'v14','bindings':binding(args.bindings),'script_sha256':sha(__file__),
        'methods':spec['methods'],'reference_manifest':olddev['reference_manifest'],'reference_display_mapping':{'A':'A','C':'B','candidate':'candidate'},
        'bootstrap':olddev['bootstrap'],'analysis_notes':c.analysis_notes(),'python_version':platform.python_version(),'numpy_version':np.__version__,
        'reference_identity':'Existing A/C AI first judgments with recorded verification lineage; T is AI. No new human coding in this run.',
        'candidate_policy':'Frozen third_for_every_reviewed_dimension:66 T-reviewed all five dimensions,174 A/C-agreed cases.',
        'independent_validation':False,'new_human_validation_completed':False,'no_model_calls':True,'no_reference_or_raw_prediction_changes':True,
        'no_metric_driven_method_selection':True,'manuscript_not_modified':True,
        'interval_limit':'Fixed label/material/algorithm design variability; file composition intervals are separate sensitivity. Not truth/model-run uncertainty or interval coverage proof.'}
    records,ac=complete.complete_classification(ctx,methods,refs)
    probability=complete.probability_attention(ctx,methods,refs)
    assert len(records)==360 and len(ac)==60
    old_for_exact={**olddev,'previous_point_audits':[{'method':LLM_KEY,'previous_method':LLM_KEY,'binding':spec['previous_complete_classification']}]}
    exact=complete.exact_point_audit(ctx,methods,refs,records,ac,old_for_exact,probability)
    repqa=complete.replication_audit(ctx)
    intervalqa=complete.interval_audit({'classification':records,'A_C':ac,'attention':probability})
    c.write_json(out/'machine_reference_classification.json',{'provenance':prov,'comparisons':records})
    c.write_json(out/'A_C_before_third_agreement.json',{'provenance':prov,'comparisons':ac})
    c.write_json(out/'probability_attention_and_paired_department_differences.json',{'provenance':prov,**probability})
    c.write_json(out/'reference_binding_QA.json',refaudit)
    c.write_json(out/'independent_exact_point_crosscheck.json',exact)
    c.write_json(out/'NA_and_interval_status.json',{'point_NA':[{**{k:r[k] for k in complete.KEYS},'paired_n':r['paired_n'],'point_NA_reasons':r['undefined_point_reasons'],'metrics':r['metrics']} for r in records+ac if r['undefined_point_reasons']],'interval_status':intervalqa})
    export_classification_csv(out/'machine_reference_classification.csv',records)
    export_classification_csv(out/'A_C_before_third_agreement.csv',ac)
    print(json.dumps({'status':'CLASSIFICATION420_AND_SAME180_COMPLETE_FULL4481_RUNNING'},ensure_ascii=False),flush=True)
    findings,flat,pair_n=full_findings(ctx,manifest,methods,refs,full,c)
    fullout=out/'full4481';fullout.mkdir()
    c.write_json(fullout/'完整定义构成核查.json',{'provenance':prov,**findings})
    c.write_json(fullout/'完整十对主表.json',{'provenance':prov,'rows':flat})
    c.write_json(fullout/'full4481_attention.json',{'provenance':prov,'primary':{name:{g:x['profile'] for g,x in obj['departments'].items()} for name,obj in findings['primary_full4481'].items()}})
    # Frozen function requires generic internal names; retain its original schema.
    file_ci=attention.full_machine_attention(ctx,{'rules':methods[RULE_KEY],'LLM':methods[LLM_KEY]},manifest['robustness_scenarios'])
    assert len(file_ci['paired_file_composition_sensitivity'])==15 and file_ci['robustness_case_n']==56
    c.write_json(fullout/'全量注意力与配对文件构成区间.json',{'provenance':prov,'generic_method_key_identity':{'rules':RULE_KEY,'LLM':LLM_KEY},**file_ci})
    ciqa_full=complete.interval_audit(file_ci)
    detail_path=Path(spec['all60_detail_script']['path'])
    loader=importlib.util.spec_from_file_location('synchronized_all60_fixed_details',detail_path);detail=importlib.util.module_from_spec(loader);loader.loader.exec_module(detail)
    detail.SOURCE=fullout/'完整定义构成核查.json';detail.OUT=fullout/'all-pair-details'
    with (out/'all60_detail_execution.log').open('w') as log,contextlib.redirect_stdout(log):detail.main()
    for item in all_bound:verify(item)
    verify_tree(olddev);verify_tree(manifest)
    qa={'all_checks_pass':True,'no_refit_or_selection':True,'all_bound_sources_unchanged':True,
        'machine_comparisons':360,'A_C_comparisons':60,'all_classification_records':420,
        'attention_profiles':len(probability['profiles']),'paired_attention_comparisons':len(probability['paired_method_differences']),'department_attention_comparisons':len(probability['department_differences']),
        'exact_point_crosschecks':{k:v for k,v in exact.items() if k!='exact_rows'},'replication_factor_audits':repqa,'interval_audit':intervalqa,
        'full4481':{'unit_n':4481,'GOV_excluded':443,'same180_n':180,'definition_n':6,'composition_n':56,'all10_pair_record_n_checked':pair_n,'all60_conditional_department_contrasts':60,'fixed_detail_candidates':8,'paired_source_file_q_interval_n':15,'interval_audit':ciqa_full,'no_new_conditional_CI_or_significance_test':True}}
    c.write_json(out/'complete_statistics_QA.json',qa);c.write_json(out/'provenance.json',prov)
    (out/'统计核验表.md').write_text('# 完整39与完整LLM03同步统计\n\n固定原180概率与60挑战分开；360机器参照记录及60 A/C对称记录共420。内部C对外显示B；T为AI参照。所有原始预测及参照未改。\n\n主区间沿用5000次分层单位SRSWOR重标；挑战区间是条件WR描述，NHC无挑战保留NA。另列源文件构成敏感性区间，不能混称主CI。\n\n同180注意力分母为五维编码句次总和；全4481排除GOV443。6定义、56构成分别计算，保留所有10对及全60双向条件比较，不交叉成336场景。全量15个q差区间是配对源文件构成敏感性，不是条件比例CI、因果证据或新独立效度。\n\n完整数值及未定义次数以同目录JSON/CSV及full4481配套表为准。未改正文，不按分数择法。\n')
    files=[binding(p) for p in sorted(out.rglob('*')) if p.is_file()]
    c.write_json(out/'output_freeze.json',{'status':'COMPLETE_ONE_SYNCHRONIZED_STATISTICS_RUN_NO_MODEL','bindings':binding(args.bindings),'entrypoint':binding(Path(__file__).resolve()),'files':files,'all_bound_inputs_unchanged':True})
    print(json.dumps({'status':'COMPLETE_SYNCHRONIZED_RUN','output':str(out),'freeze':binding(out/'output_freeze.json'),'machine_comparisons':360,'A_C_comparisons':60,'definition_n':6,'composition_n':56,'all10_pair_record_n':pair_n,'full_q_interval_n':15},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
