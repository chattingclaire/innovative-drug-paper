"""Analyze sealed full reruns against current references; never old author labels.

H427 judgments cannot be loaded until all 4924 LLM predictions are sealed.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
from comparison_statistics import DIMS, label, evaluate_units

HERE=Path(__file__).resolve().parent
LLM=HERE/'llm_runs/gpt56-sol-v13-native-1'
RULE=HERE/'rule_runs/v25-candidate-3'
METHODS=('rules_baseline','rules_v25','llm_gpt56_sol')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(line) for line in p.read_text().splitlines()]
def unique(rows):
    result={r['id']:r for r in rows}
    assert len(result)==len(rows),'duplicate IDs'
    return result

def subtype_set(record,name):
    value=record.get(name)
    if value is None:return set()
    if not isinstance(value,list) or not all(isinstance(item,str) for item in value):
        raise ValueError('Subtype metadata must be an array of strings or null: '+name)
    return set(value)

def scenario_labels(record, scenario):
    values={d:label(record['labels'][d]) for d in DIMS}
    fairness=subtype_set(record,'fairness_subtypes');innovation=subtype_set(record,'innovation_subtypes')
    quality=record.get('safety_quality_basis')
    if quality is None:
        kinds=subtype_set(record,'safety_subtypes')
        quality='quality_only' if kinds=={'quality_safety'} else 'quality_and_other' if 'quality_safety' in kinds else 'no_quality_basis' if kinds else 'unknown'
    if scenario=='exclude_quality_only' and values['S']==1 and quality=='quality_only':values['S']=0
    if scenario=='exclude_quality_only' and values['S']==1 and quality not in {'quality_only','quality_and_other','no_quality_basis'}:values['S']='待定'
    if scenario.startswith(('exclude_F_','F_access_')) and values['F']==1 and not fairness:values['F']='待定'
    if scenario=='exclude_F_clinical_management_only' and values['F']==1 and fairness=={'clinical_management'}:values['F']=0
    if scenario=='F_access_affordability_only' and values['F']==1 and not fairness & {'access','affordability'}:values['F']=0
    if scenario=='exclude_F_dimension_information_only' and values['F']==1 and fairness=={'dimension_information'}:values['F']=0
    if scenario=='exclude_I_qualification_advantage_only' and values['I']==1 and innovation=={'qualification_advantage'}:values['I']=0
    if scenario=='exclude_I_qualification_advantage_only' and values['I']==1 and not innovation:values['I']='待定'
    return values

def summarize(raw_units, scenario):
    units=[]
    for u in raw_units:
        units.append({'id':u['id'],'weight':u['weight'],
            'predictions':{m:scenario_labels(u['predictions'][m],scenario) for m in METHODS},
            'references':{c:scenario_labels(u['references'][c],scenario) for c in ('A','C')}})
    return evaluate_units(units,METHODS)

def load_sealed_predictions():
    seal=json.loads((LLM/'prediction_seal.json').read_text())
    assert seal['n']==4924 and seal['first_outputs_primary'] is True
    assert sha(LLM/'all_predictions.jsonl')==seal['predictions_sha256']
    assert sha(LLM/'run_plan.json')==seal['run_plan_sha256']
    for relative,digest in seal['output_bindings'].items():assert sha(LLM/relative)==digest
    rule_report=json.loads((RULE/'current_1268_comparison.json').read_text())
    assert sha(RULE/'all_predictions.jsonl')==rule_report['output_sha256']
    rules=unique(lines(RULE/'all_predictions.jsonl'));llm=unique(lines(LLM/'all_predictions.jsonl'))
    inputs=unique(lines(HERE/'current_llm_inputs.jsonl'))
    assert set(rules)==set(llm)==set(inputs) and len(rules)==4924
    return rules,llm,inputs,seal

def load_reference_units(scope,rules,llm,inputs):
    result=[];bindings={}
    def append(rid,refs,weight):
        assert rid in rules and rid in llm
        for c in ('A','C'):
            assert set(refs[c]['labels'])==set(DIMS)
            for d in DIMS:label(refs[c]['labels'][d])
        result.append({'id':rid,'weight':weight,'references':refs,
            'predictions':{'rules_baseline':rules[rid]['baseline'],'rules_v25':rules[rid]['candidate'],'llm_gpt56_sol':llm[rid]}})
    if scope=='current1268':
        path=HERE/'current_1268_references.jsonl'
        for r in lines(path):
            h=r['historical_sampling'];append(r['id'],r['original_references'],h['N_h']/h['n_h'])
        bindings[str(path)]=sha(path)
        assert len(result)==1268
    else:
        # This function is called ONLY after load_sealed_predictions succeeded.
        root=HERE/'H427';mapping=json.loads((root/'admin_mapping.json').read_text())
        mapping={r['id']:r for r in mapping};assert len(mapping)==427
        refs={}
        for c in ('A','C'):
            folder=root/f'agent-{c}';completion=folder/'完成清单.json'
            assert completion.exists(),'Independent reference execution is unfinished'
            bindings[str(completion)]=sha(completion)
            rows=[]
            for n in range(1,44):
                f=folder/f'结果-{n:02d}.json';packet=folder/f'材料-{n:02d}.json'
                value=json.loads(f.read_text())
                assert value['coder']==c and value['protocol_version']=='CAL-5D-20260926-v1.3'
                assert value['protocol_acknowledged'] is True
                assert value['input_packet_sha256']==sha(packet)
                rows.extend(value['rows']);bindings[str(f)]=sha(f)
            refs[c]=unique(rows);assert set(refs[c])==set(mapping)
        for blind_id,m in mapping.items():
            rid=m['rerun_id']
            assert hashlib.sha256(inputs[rid]['text'].encode()).hexdigest()==m['text_sha256']
            append(rid,{c:refs[c][blind_id] for c in ('A','C')},1)
        bindings[str(root/'admin_mapping.json')]=sha(root/'admin_mapping.json')
    assert len({u['id'] for u in result})==len(result)
    return result,bindings

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--scope',choices=['current1268','H427'],required=True);args=parser.parse_args()
    rules,llm,inputs,seal=load_sealed_predictions()
    raw_units,bindings=load_reference_units(args.scope,rules,llm,inputs)
    scenarios=['primary','exclude_quality_only','exclude_F_clinical_management_only',
               'F_access_affordability_only','exclude_F_dimension_information_only','exclude_I_qualification_advantage_only']
    out=HERE/'rerun_comparisons'/args.scope;out.mkdir(parents=True,exist_ok=False)
    report={'scope':args.scope,'n':len(raw_units),'old_author_labels_used':False,
        'current_reference_identity':'AI A/C independent first submissions under CAL-5D-20260926-v1.3; not human gold standard',
        'design':'observed/development materials; historical stratified weights descriptive only' if args.scope=='current1268' else 'census of the registered remaining 427 units; weights 1; not representative of all 4924',
        'confidence_intervals':'not reported as sampling intervals for this finite remaining-frame census or post-development comparison',
        'limits':['Completion bounds express logical uncertainty from pending labels, not confidence intervals.',
                  'Shared AI errors and construct validity are not established by high agreement.',
                  'The fixed standard and inputs do not imply either implementation conforms perfectly.',
                  'F information-only and innovation qualification sensitivities use explicit recorded subtypes; unrecorded all-dimension information-only status is not inferred.'],
        'scenarios':{s:summarize(raw_units,s) for s in scenarios}}
    (out/'metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    md=['# 两条方法重跑：'+args.scope,'',f'共{len(raw_units)}条；参照为当前同版A/C首次AI编码，未使用旧作者标签。',
        report['design'],'','下表用每维、每位参考下三种机器版本都可判定的同一子集；A/C分别列出。',
        '1268表使用历史设计权重作描述，H427表所有权重均为1。覆盖、完整计数和待定完成界限见JSON。','',
        '|维度|方法|精确率A/C|召回率A/C|F1 A/C|共同可判条数A/C|','|---|---|---:|---:|---:|---:|']
    primary=report['scenarios']['primary']
    for d in DIMS:
        for method in METHODS:
            def vals(k):
                values=[primary['methods'][c][d]['by_method'][method]['common_units_weighted']['conditional_scores'][k] for c in ('A','C')]
                return '/'.join('NA' if v is None else f'{v:.1%}' for v in values)
            ns='/'.join(str(primary['methods'][c][d]['common_unit_n']) for c in ('A','C'))
            md.append(f'|{d}|{method}|{vals("precision")}|{vals("recall")}|{vals("f1")}|{ns}|')
    md+=['','“待定”不填0，也不无声删除；指标是相对AI参考的符合程度。没有据此自动形成真人金标准或宣布信效度通过。']
    (out/'summary.md').write_text('\n'.join(md)+'\n')
    freeze={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_bindings':bindings,
        'LLM_seal_sha256':sha(LLM/'prediction_seal.json'),'rule_prediction_sha256':sha(RULE/'all_predictions.jsonl'),
        'analysis_script_sha256':sha(Path(__file__)),'statistics_script_sha256':sha(HERE/'comparison_statistics.py'),
        'output_sha256':sha(out/'metrics.json')}
    (out/'analysis_binding.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'scope':args.scope,'n':len(raw_units),'output':str(out),'metrics_sha256':freeze['output_sha256']},ensure_ascii=False))

if __name__=='__main__':main()
