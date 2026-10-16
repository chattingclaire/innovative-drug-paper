"""Machine-versus-A/C/adjudicated-candidate classification; probability != challenge."""
import argparse,csv,datetime
from statistical_core import *
from current_material_context import load_current_context
from final_machine_contract import rule_binding,llm_binding,old_bindings

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['rule_only','final'],required=True);args=parser.parse_args()
    ctx=load_current_context();rule,rb,rpaths=rule_binding();machines={rb['method']:rule};bindings={rb['method']:rb};paths=ctx['source_paths']+rpaths+[Path(__file__)]
    if args.stage=='final':
        llm,lb,lpaths=llm_binding();machines[lb['method']]=llm;bindings[lb['method']]=lb;paths+=lpaths
    old,ob,op=old_bindings();machines.update(old);bindings.update(ob);paths+=op
    refs={c:jsonl(RUN/f'reference/agent_{c}_final_v8.jsonl') for c in ('A','C')};paths+=[RUN/f'reference/agent_{c}_final_v8.jsonl' for c in ('A','C')]
    candidate_path=OUT/'adjudicated_agent_reference_candidate_v8.jsonl';candidate_qa=OUT/'裁决候选参照来源核验-v8.json'
    assert candidate_path.exists() and candidate_qa.exists(),'All43 third-agent candidates required; no vote substitution.'
    qa=read(candidate_qa);assert qa['n']==300 and qa['candidate_sha256']==sha(candidate_path) and qa['human_validation_completed'] is False
    refs['third_agent_candidate']=jsonl(candidate_path);paths+=[candidate_path,candidate_qa]
    for name,data in machines.items():assert set(data)==set(ctx['inputs']),name
    for data in refs.values():assert set(data)==set(ctx['sample'])
    before={str(path):sha(path) for path in set(paths)};records=[];factors={}
    for method,left in machines.items():
        for reference,right in refs.items():
            for component in ('probability_base','enriched_challenge'):
                for group,kind in groups_and_weights(component):
                    ids=[rid for rid,r in ctx['sample'].items() if r['component']==component and(group=='ALL' or r['group']==group)]
                    for dim in DIMS:
                        row=comparison(ctx,left,right,dim,ids,component,group,kind,method,reference,factors)
                        row['comparison_role']='historical_v3_material_baseline' if method.startswith('old_') else 'current_completed_v8_candidate'
                        records.append(row)
    stem='最终机器参照比较' if args.stage=='final' else '规则已完成阶段参照比较'
    report={'status':'completed_all_current_machine_comparisons' if args.stage=='final' else 'completed_rule_only_stage_LLM_not_included',
        'created_at':datetime.datetime.now().astimezone().isoformat(),'human_validation_completed':False,'new_LLM_partial_or_fallback_used':False,
        'analysis_notes':analysis_notes(),'method_bindings':bindings,'reference_identity':'A/C independent final_v8 submissions and derived third-expert-agent candidate; no completed real-human ground truth.',
        'historical_contrast_limit':'Old methods use materialv3. New-vs-old differences combine implementation and actual material changes; no pure prompt/code causal effect is claimed.',
        'records':records,'source_sha256':before}
    write_json(OUT/(stem+'.json'),report)
    fields=['component','group','weighting','method','reference','comparison_role','dimension','unit_frame_n','paired_n','left_positive_n','reference_positive_n','TP','FP','FN','TN']
    for metric in ('kappa','agreement','precision','recall','f1'):fields += [metric,metric+'_low',metric+'_high',metric+'_source_file_low',metric+'_source_file_high']
    fields+=['work_target_0_80_diagnostics']
    with (OUT/(stem+'.csv')).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader()
        for r in records:
            row={k:r[k] for k in fields if k in r};row.update(r['raw_confusion'])
            for name in ('kappa','agreement','precision','recall','f1'):
                metric=r['metrics'][name];row[name]=metric['estimate']
                for field in ('low','high'):
                    row[name+'_'+field]=metric['ci95_primary'][field];row[name+'_source_file_'+field]=metric['ci95_source_file_conditional_sensitivity'][field]
            row['work_target_0_80_diagnostics']=json.dumps(r['point_0_80_diagnostics'],ensure_ascii=False)
            writer.writerow(row)
    lows=[{k:r[k] for k in ('component','group','weighting','method','reference','dimension','paired_n','reference_positive_n','point_0_80_diagnostics')} for r in records if any(v!='at_least_0_80' for v in r['point_0_80_diagnostics'].values())]
    write_json(OUT/(stem+'-低值与未定义.json'),{'threshold_role':'Diagnostic work target; not a publication/equivalence claim.','records':lows})
    assert before=={str(path):sha(path) for path in before}
    print(json.dumps({'status':report['status'],'records':len(records),'current_records':sum(not r['method'].startswith('old_') for r in records),'historical_records':sum(r['method'].startswith('old_') for r in records),'low_or_undefined_comparisons':len(lows)},ensure_ascii=False))

if __name__=='__main__':main()
