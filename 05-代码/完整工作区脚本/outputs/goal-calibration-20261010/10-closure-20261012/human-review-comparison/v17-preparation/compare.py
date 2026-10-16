"""Same fixed-200 descriptive method after development; never independent validation.

Only completed strict rule-v17 and whole-batch LLM-v17 composites are accepted.
The accepted original human projection and all old results remain untouched.
"""
import argparse,ast,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent
ROOT=OLD.parent.parent
V17=ROOT/'01-review/source-interface-v17-finite-source-addendum-root'
DIMS=('S','E','Ec','I','F')
OLD_SCRIPT_SHA='4765ce0307d5fe0c53866cb4569a4731b2dad75825a78d11123e15ef28839f37'
OLD_SUMMARY_SHA='563ce209ed57701e4ec155f9d53cc30aa5b2f2f9cda98b1c948efab3e4a4c654'
OLD_JOIN_SHA='ea4a813abde9158bb7aa9afb1d99d32685ac3073fc2c14153d882c4286930889'
V17_SHA='0f248d9a5a8755e20875b88cecb521821b26b56a270beb2b866f0f4f4796a039'
PACKET_SHA='1ebca062a3b3e28b130bc747d770b832945b479ffba2f923f34fe0d7b93740ab'
RULE_DEFAULT=ROOT/'06-coding/rule-full4481-v15-v17-received-root'
LLM_DEFAULT=ROOT/'06-coding/native-full4481-v17-two-whole-batch-compatible-root'
CHANGED={'RECODE25-02588','RECODE25-04598'}

def require(ok,why):
    if not ok:raise ValueError(why)

def read(path):return json.loads(Path(path).read_text())

def binding(path):
    p=Path(path).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def exact(b):
    require(binding(b['path'])=={k:b[k] for k in ['path','bytes','sha256']},'Changed bound input: '+b['path'])

def expected(path,sha):
    b=binding(path);require(b['sha256']==sha,'Changed frozen input: '+str(path));return b

def seal(directory,status_name):
    directory=Path(directory).resolve();s=read(directory/'seal.json')
    files={b['path']:b for b in s['files']}
    require(str(directory/status_name) in files,'Status not in completed output seal')
    for b in files.values():exact(b)
    return read(directory/status_name),files,binding(directory/'seal.json')

def paired_inputs(rule_dir,llm_dir):
    # Refuse before reading labels or human data when either complete pair is
    # missing. Never substitute the old LLM for the running new rule result.
    require(all((Path(p)/n).is_file() for p,n in [(rule_dir,'seal.json'),(rule_dir,'composite-status.json'),(llm_dir,'seal.json'),(llm_dir,'status.json')]),
            '两份完整 v17 严格接收结果尚未齐备；不得混用新版规则与旧版 LLM。')
    r,rf,rs=seal(rule_dir,'composite-status.json');l,lf,ls=seal(llm_dir,'status.json')
    common=expected(V17/'common-frame-bundles-v17.jsonl',V17_SHA)
    packets_binding=expected(V17/'packet-bindings-v17.json',PACKET_SHA)
    require(r['status']=='validated_complete_full4481_v17_not_adopted' and r['all4481_actually_inferred_under_candidate'] is True and r['inherited_compatible_parent_record_N']==0,'Rule result is not the strict complete new execution')
    require(r['candidate_algorithm_version']=='joint-v15b-complete-repair-root','Rule algorithm is not the reviewed v15b candidate')
    require(l['status']=='complete_native_full4481_v17_two_whole_batch_compatible_composite_with_explicit_execution_origins' and l['actual_merge_performed'] is True and l['single_actual_merge_pass'] is True,'LLM result is not the completed v17 two-whole-batch composite')
    require(l['actual_new_inference_record_N']==24 and l['parent_raw_line_preserved_N']==4457,'LLM whole-batch lineage count differs')
    for status in [r,l]:
        require(status['actual_record_N']==4481 and status['actual_dimension_N']==22405 and status['unresolved_technical_dimension_N']==0,'Incomplete/failed machine frame')
        require(status['source_common_v17']==common and set(status['material_changed_record_ids'])==CHANGED,'Machines are not bound to the same actual v17 material')
    exact(r['actual_run_seal']);exact(r['current_scope']);exact(l['strict_merge_readback'])
    require([x['batch_id'] for x in read(l['strict_merge_readback']['path'])['batches']]==['batch-0325','batch-0485'],'LLM two whole receptions differ')
    for key in ['new_whole_selections','new_whole_firsts','new_whole_receipts','new_whole_actor_seals','new_whole_process_completions']:
        require(len(l[key])==2,'LLM whole reception incomplete: '+key)
        for b in l[key]:exact(b)
    packet_rows=read(packets_binding['path']);ids=[x['source_id'] for x in packet_rows]
    require(len(ids)==len(set(ids))==4481,'V17 frame is not complete/unique')
    machines={};machine_bindings={}
    for name,directory,filename,files in [('rule',rule_dir,'predictions.jsonl',rf),('LLM',llm_dir,'selected-records.jsonl',lf)]:
        path=Path(directory).resolve()/filename;require(str(path) in files,'Machine labels not bound by complete seal')
        rows=[json.loads(x) for x in path.read_text().splitlines()]
        require([x['id'] for x in rows]==ids,'Machine full-frame order differs')
        for row in rows:
            require(set(row['labels'])==set(DIMS),'Five dimensions incomplete')
            for d in DIMS:
                value=row['labels'][d]
                require(value is None or type(value) is int and value in (0,1),'Invalid machine value')
                require(value==row['decisions' if name=='rule' else 'dimensions'][d]['value'],'Label/decision mismatch')
        machines[name]={x['id']:x for x in rows};machine_bindings[name]=files[str(path)]
    for row,packet in zip(machines['LLM'].values(),packet_rows):
        require(row['packet']=={k:packet[k] for k in ['path','bytes','sha256']},'LLM record material differs from actual v17 packet')
    return machines,{'rule_seal':rs,'LLM_seal':ls,'rule_status':binding(Path(rule_dir)/'composite-status.json'),
       'LLM_status':binding(Path(llm_dir)/'status.json'),'common_v17':common,'packets_v17':packets_binding,**machine_bindings}

def summaries(records,exact_metrics):
    result=[]
    groups=[('all200',records),('historical_remaining120',[r for r in records if r['historical_domain']=='remaining']),
      ('historical_exposed80',[r for r in records if r['historical_domain']=='exposed']),
      ('unchanged_material198',[r for r in records if not r['material_supplemented_in_v17']])]
    for group,group_rows in groups:
        for method in ('rule','LLM'):
            for dim in DIMS:
                rows=[r for r in group_rows if r['dimension']==dim]
                states,raw_cells=Counter(),[0,0,0,0];weighted=[Fraction(0) for _ in range(4)]
                for r in rows:
                    h,m=r['human_reviewed_value'],r[method]
                    states[f'{"pending" if h is None else h}|{"null" if m is None else m}']+=1
                    if h is None or m is None:continue
                    index={(1,1):0,(1,0):1,(0,1):2,(0,0):3}[(m,h)]
                    raw_cells[index]+=1;weighted[index]+=Fraction(r['original_weight_exact'])
                def metric(cells):return {k:None if v is None else float(v) for k,v in exact_metrics(cells).items()}
                result.append({'group':group,'method':method,'dimension':dim,'planned_N':len(rows),
                  'common_binary_N':sum(raw_cells),'excluded_N':len(rows)-sum(raw_cells),
                  'human_pending_N':sum(r['human_reviewed_value'] is None for r in rows),
                  'machine_lawful_null_N':sum(r[method] is None for r in rows),'machine_technical_failure_N':0,
                  'joint_states_human_machine':dict(states),'cell_order':['TP','FP','FN','TN'],'raw_cells':raw_cells,
                  'original_weighted_cells_exact':[str(x) for x in weighted],
                  'raw_metrics':metric(raw_cells),'original_weighted_metrics':metric(weighted),
                  'formal_acceptance':False,'independent_accuracy_CI':None})
    return result

def main(rule_dir,llm_dir,out,readiness=False):
    machines,inputs=paired_inputs(rule_dir,llm_dir)
    if readiness:return {'status':'both_strict_same_v17_composites_available','statistics_executed':False}
    out=Path(out).resolve();require(not out.exists(),'Never overwrite a comparison')
    inputs['old_script']=expected(OLD/'analyze.py',OLD_SCRIPT_SHA)
    inputs['accepted_original_comparison']=expected(OLD/'results/comparison.json',OLD_SUMMARY_SHA)
    inputs['accepted_original_join']=expected(OLD/'results/joined-dimension-records.jsonl',OLD_JOIN_SHA)
    prior=read(inputs['accepted_original_comparison']['path'])
    for key in ['human_original','math_core','draw','issued_template']:
        inputs[key]=prior['source_bindings'][key];exact(inputs[key])
    # Exactly the same frozen Fraction functions; no interval engine is added.
    tree=ast.parse(Path(inputs['math_core']['path']).read_text())
    fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_ratio','exact_metrics')]
    require([n.name for n in fns]==['_ratio','exact_metrics'],'Frozen math function identity differs')
    ns={'Fraction':Fraction};exec(compile(ast.Module(body=fns,type_ignores=[]),inputs['math_core']['path'],'exec'),ns)
    records=[json.loads(x) for x in Path(inputs['accepted_original_join']['path']).read_text().splitlines()]
    require(len(records)==1000 and len({(r['source_id'],r['dimension']) for r in records})==1000 and len({r['source_id'] for r in records})==200,'Accepted fixed200 projection changed')
    require(CHANGED<={r['source_id'] for r in records},'Known material changes absent from fixed200')
    for r in records:
        rid=r['source_id'];r['v11_frozen_domain_for_history_only']=r.pop('current_domain')
        r['material_supplemented_in_v17']=rid in CHANGED
        r['v17_supplement_human_reread_verified']=False if rid in CHANGED else None
        r['reference_set_used_for_development']=True
        for method in ['rule','LLM']:r[method]=machines[method][rid]['labels'][r['dimension']]
    numeric=summaries(records,ns['exact_metrics'])
    result={'analysis_type':'fixed200_post_development_AI_initial_human_reviewed_descriptive_comparison',
      'created_at_utc':datetime.now(timezone.utc).isoformat(),'records_N':200,'dimension_slots_N':1000,
      'recording_source_counts':prior['recording_source_counts'],'numeric_comparisons':numeric,
      'material_supplemented_record_ids':sorted(CHANGED),'unchanged_material_sensitivity_record_N':198,
      'supplemented_material_rows':[r for r in records if r['material_supplemented_in_v17']],
      'pending':[r for r in records if r['human_reviewed_value'] is None],'source_bindings':inputs,
      'scope':{'feedback_used_for_model_revision':True,'two_independent_human_firsts':False,
        'formal_independent_validation_executed':False,'formal_acceptance':False,
        'v17_supplement_human_reread_verified':False,'historical_weights_role':'descriptive_reweighting_only_not_current_population_accuracy',
        'material_comparability':'All200 retained; 02588/04598 supplemented machine material compared with the original reviewed reference separately, with unchanged198 sensitivity. No human reread inferred.',
        'CI_reason':prior['scope']['CI_reason']}}
    out.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        with (out/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    save('comparison.json',result)
    with (out/'joined-dimension-records.jsonl').open('x') as f:
        for r in records:f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')
    lines=['# 新版机器与原真人复核的开发对照','',
      '原200条AI初评后经真人复核的反馈已用于模型修订。本次是开发复核对照，不是独立A/B或准确性验收。两机均为完整、严格接收的同v17材料结果。',
      '全部200条保留。02588、04598新增来源材料后，模型结果与原复核参照的可比性另列；未推断真人重读v17。198条未变材料结果仅为敏感性对照。',
      '沿用原共同二元分母、四格表、κ/Precision/Recall/F1与原权重诊断。待定和机器NULL按并集排除；无适用的独立总体95%区间，继续不计算该区间。','']
    fmt=lambda x:'NA' if x is None else f'{x:.3f}'
    for group,title in [('all200','全部200条'),('unchanged_material198','198条未变材料敏感性对照')]:
        lines += ['## '+title,'','| 方法 | 维度 | 共同可比/计划 | 待定 | NULL | TP/FP/FN/TN | κ | P | R | F1 |','|---|---|---:|---:|---:|---|---:|---:|---:|---:|']
        for x in numeric:
            if x['group']!=group:continue
            m=x['raw_metrics'];lines.append('| '+ ' | '.join([x['method'],x['dimension'],f"{x['common_binary_N']}/{x['planned_N']}",str(x['human_pending_N']),str(x['machine_lawful_null_N']),'/'.join(map(str,x['raw_cells'])),*[fmt(m[k]) for k in ['kappa','Precision','Recall','F1']]])+' |')
        lines.append('')
    lines += ['## 两条材料补充记录','', '| 记录 | 维度 | 原复核参照 | 新规则 | 新LLM |','|---|---|---:|---:|---:|']
    for r in result['supplemented_material_rows']:lines.append(f"| {r['source_id']} | {r['dimension']} | {r['human_reviewed_value']} | {r['rule']} | {r['LLM']} |")
    lines += ['', '原120/80历史分组、原抽样概率与权重完整保留在JSON；这些分组不代表新机器下的独立身份。原人审表和旧结果未改。[完整指标](comparison.json) · [逐项记录](joined-dimension-records.jsonl)','']
    with (out/'开发复核对照.md').open('x') as f:f.write('\n'.join(lines))
    return {'status':'descriptive_development_comparison_complete','records_N':200,'formal_acceptance':False,'output':str(out)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rule-received',default=str(RULE_DEFAULT));p.add_argument('--llm-received',default=str(LLM_DEFAULT));p.add_argument('--output-dir',default=str(OLD/'results-v17-development'));p.add_argument('--check-readiness',action='store_true');a=p.parse_args()
    try:print(json.dumps(main(a.rule_received,a.llm_received,a.output_dir,a.check_readiness),ensure_ascii=False))
    except (ValueError,FileNotFoundError) as e:print(json.dumps({'status':'not_ready_or_rejected','reason':str(e)},ensure_ascii=False));raise SystemExit(2)
