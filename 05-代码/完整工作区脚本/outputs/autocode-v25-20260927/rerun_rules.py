"""Freeze and rerun both rule versions on all 4924 current full inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import baseline_candidate17 as old
import policy_coding_v25 as new
from evaluate_development import metrics

HERE=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-name',required=True);args=parser.parse_args()
    assert Path(args.run_name).name==args.run_name
    root=HERE/'rule_runs'/args.run_name;root.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((HERE/'current_input_manifest.json').read_text())
    for name,sha in manifest['output_hashes'].items():assert digest(HERE/name)==sha
    files=[HERE/n for n in ['policy_coding_v25.py','baseline_candidate17.py','protocol-v1.3.md','rerun_rules.py','evaluate_development.py','current_input_manifest.json']]
    freeze={'candidate_version':new.VERSION,'baseline_version':old.VERSION,'analysis_N':4924,
        'reference':'current_v13_1268_AI_A_C_first_submissions_not_old_author_labels',
        'code_and_input_bindings':{str(p):digest(p) for p in files},'inputs':manifest['output_hashes'],
        'validation_status':'current_reference_development_comparison; independent_remaining_frame_separate'}
    f=root/'freeze.json'
    if f.exists():assert json.loads(f.read_text())==freeze,'Frozen run differs: preserve and use a new version.'
    else:f.write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
    if (root/'all_predictions.jsonl').exists():raise RuntimeError('Existing predictions preserved; do not overwrite frozen run.')
    inputs=[json.loads(s) for s in (HERE/'current_rule_inputs.jsonl').read_text().splitlines()]
    outputs={};records=[]
    for row in inputs:
        old_output=old.code_unit(row['input']);new_output=new.code_unit(row['input'])
        for method in [old_output,new_output]:
            for e in method['evidence']:
                assert row['input']['unit_text'][e['start']:e['end']]==e['text'],row['id']
        out={'id':row['id'],'original_id':row['original_id'],'baseline':old_output,'candidate':new_output}
        outputs[row['id']]=out;records.append(out)
    assert len(outputs)==4924
    (root/'all_predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    references=[json.loads(s) for s in (HERE/'current_1268_references.jsonl').read_text().splitlines()]
    for r in references:
        r['baseline_frozen']=outputs[r['id']]['baseline'];r['v25']=outputs[r['id']]['candidate']
    result={'status':'rerun_complete_current_reference_descriptive_development_comparison',
        'full_analysis_N':4924,'current_reference_n':1268,'old_author_labels_used':False,
        'candidate_version':new.VERSION,
        'reference_identity':'AI A/C under protocol v1.3; original first labels retained',
        'metrics':{c:{v:metrics(references,c,v) for v in ['baseline_frozen','v25']}for c in ['A','C']},
        'paired_common_determinate_metrics':{c:{v:metrics(references,c,v,True) for v in ['baseline_frozen','v25']}for c in ['A','C']},
        'limits':['1268 includes development examples and cannot certify v25 generalization.',
                  'Weights describe the historical sampling design; post-tuning performance is not unbiased.',
                  'Original LLM results are not current-protocol results and are not substituted here.',
                  'AI reference agreement does not establish human or construct validity.'],
        'output_sha256':digest(root/'all_predictions.jsonl')}
    (root/'current_1268_comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    md=['# 自动编码重跑：与本轮1268条A/C对照','',
        '4,924条完整输入已重跑。参照是本轮v1.3的1,268条A/C首次AI编码，不是旧作者编码。',
        '这是改进后的开发描述；独立剩余框验证须另报，不据此宣布达到效度标准。','',
        '|维度|旧词典召回A/C|本版召回A/C|本版精确率A/C|本版F1 A/C|','|---|---:|---:|---:|---:|']
    for d in old.DIMENSIONS:
        def val(v,k):
            values=[result['paired_common_determinate_metrics'][c][v][d]['historical_design_weighted_descriptive'][k] for c in ['A','C']]
            return '/'.join('NA' if x is None else f'{x:.1%}' for x in values)
        md.append(f'|{d}|{val("baseline_frozen","recall")}|{val("v25","recall")}|{val("v25","precision")}|{val("v25","f1")}|')
    md+=['','完整分子、分母、待定、共同可判覆盖见同名JSON。LLM重跑结果未产生前不填写该方法分数。']
    (root/'current_1268_comparison.md').write_text('\n'.join(md)+'\n')
    print(json.dumps({'full_units':4924,'reference_units':1268,'old_author_labels_used':False,'run':args.run_name},ensure_ascii=False))

if __name__=='__main__':main()
