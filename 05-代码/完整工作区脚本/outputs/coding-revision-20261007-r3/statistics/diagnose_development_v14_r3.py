"""v33/v34.1/v35.1 on v14 references; all r3 cases are development-exposed."""
from pathlib import Path
import argparse
import datetime
import json
import numpy as np
import statistical_core_r3 as c
import final_binding_io_r3 as io
from run_final_statistics_r3 import classification
from diagnose_v33_v34_samecontext_v13_r3 import independent_metrics


def bd(path):return {'path':str(path),'sha256':c.sha(path)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();assert not args.out.exists()
    root=c.RUN;binding_path=root/'statistics/T参照66-v14阶段绑定.json'
    binding=c.read(binding_path);ctx=io.context_from_manifest(binding);refs,qa=io.final_references(binding,ctx)
    paths={'v33':root/'rules-v33/all_predictions_material_v14.run.json',
        'v34.1':root/'rules-v34-audit/architecture/candidate_predictions_v14_source_interface.run.json',
        'v35.1':root/'rules-v35.1-development/all_predictions_material_v14.run.json'}
    predictions={};methods={}
    for name,path in paths.items():
        run=c.read(path);assert run['input_sha256']==binding['material']['rule_inputs']['sha256']
        p=Path(run['prediction_path']);assert c.sha(p)==run['prediction_sha256']
        assert c.sha(run['candidate_freeze_path'])==run['candidate_freeze_sha256']
        assert all(c.sha(code)==digest for code,digest in run['runtime_code_sha256'].items())
        predictions[name]=c.jsonl(p);assert set(predictions[name])==set(ctx['inputs'])
        assert all(c.binary(c.label(row,d)) for row in predictions[name].values() for d in c.DIMS)
        methods[name]={'run':bd(path),'prediction':bd(p),'candidate_freeze':bd(Path(run['candidate_freeze_path']))}
    rows,_=classification(ctx,predictions,refs)
    for row in rows:
        for name,value in independent_metrics(row['weighted_confusion']).items():
            actual=row['metrics'][name]['estimate']
            assert (value is None and actual is None) or np.isclose(value,actual)
    keys=('component','group','weighting','reference','dimension')
    lookup={(row['method'],*(row[k] for k in keys)):row for row in rows}
    deltas=[];case_differences=[]
    for name in ('v34.1','v35.1'):
        for before in rows:
            if before['method']!='v33':continue
            after=lookup[name,*(before[k] for k in keys)]
            deltas.append({k:before[k] for k in keys}|{'method':name,'baseline':'v33',
                'metrics':{metric:{'v33':before['metrics'][metric]['estimate'],'development':after['metrics'][metric]['estimate'],
                    'delta':after['metrics'][metric]['estimate']-before['metrics'][metric]['estimate']
                        if all(x['metrics'][metric]['estimate'] is not None for x in (before,after)) else None}
                    for metric in ('kappa','precision','recall','f1')}})
        for rid in ctx['inputs']:
            for d in c.DIMS:
                old=c.label(predictions['v33'][rid],d);new=c.label(predictions[name][rid],d)
                if old==new:continue
                record={'id':rid,'method':name,'dimension':d,'v33':old,'development':new,
                    'in_reference_sample':rid in ctx['sample'],'text':ctx['llm_inputs'][rid]['text'],
                    'source_title':ctx['llm_inputs'][rid]['source_title']}
                if rid in ctx['sample']:
                    record.update({'component':ctx['sample'][rid]['component'],'group':ctx['sample'][rid]['group'],
                        'reference_comparison':{ref:{'label':c.label(target[rid],d),
                            'before_matches':old==c.label(target[rid],d),'after_matches':new==c.label(target[rid],d)}
                            for ref,target in refs.items()}})
                case_differences.append(record)
    errors=[]
    for rid in ctx['sample']:
        for dim in c.DIMS:
            for name,method in predictions.items():
                for ref,target in refs.items():
                    pred=c.label(method[rid],dim);truth=c.label(target[rid],dim)
                    if pred==truth:continue
                    errors.append({'id':rid,'dimension':dim,'method':name,'reference':ref,'type':'FP' if pred else 'FN',
                        'component':ctx['sample'][rid]['component'],'group':ctx['sample'][rid]['group'],
                        'text':ctx['llm_inputs'][rid]['text'],
                        'reference_reason':target[rid].get('dimension_reasons',{}).get(dim),
                        'reference_dimension_source':target[rid].get('dimension_label_source',{}).get(dim)})
    note={'stage':'post_exposure_development_diagnostic_only','created_at':datetime.datetime.now().astimezone().isoformat(),
        'reference_binding':bd(binding_path),'methods':methods,'sample_n':240,
        'v35_1_r3_reference_exposure':'All240 r3 reference cases used in v35/v35.1 development; none count as independent confirmation.',
        'formal_baseline_retained':'v33','human_validation_completed':False,
        'script_sha256':c.sha(Path(__file__)),'analysis_notes':c.analysis_notes()}
    args.out.mkdir();c.write_json(args.out/'comparisons.json',{'provenance':note,'comparisons':rows})
    c.write_json(args.out/'differences.json',{'provenance':note,'metric_deltas':deltas,'binary_case_dimension_changes':case_differences})
    c.write_json(args.out/'FN_FP_PRIVATE.json',{'provenance':note,'errors':errors})
    fmt=lambda v:'NA' if v is None else f'{v:.3f}'
    text=['v14材料上的规则开发诊断','','v35.1已使用全部240条r3参考进行开发；本表不能视为v35.1独立确认。v34.1也是开发候选，旧v35仅保留历史。正式基准保留v33，原标签未改。','',
        'NA保持未定义；概率180和挑战60分开，设计权重只推断canonical剩余抽样框。0.80不是普遍发表门槛。','']
    for comp,weight,title in [('probability_canonical','eligible_design_weighted','概率180，设计加权'),
                             ('probability_canonical','unweighted','概率180，等额样本构成'),
                             ('enriched_challenge','unweighted','挑战60')]:
        text += [title,'','|参考|维度|方法|κ|P|R|F1|Δκ / ΔP / ΔR / ΔF1 对v33|','|---|---|---|---|---|---|---|---|']
        for ref in refs:
            for dim in c.DIMS:
                for name in predictions:
                    row=lookup[name,comp,'ALL',weight,ref,dim]
                    values=[row['metrics'][m]['estimate'] for m in ('kappa','precision','recall','f1')]
                    base=lookup['v33',comp,'ALL',weight,ref,dim]
                    diffs=[v-base['metrics'][m]['estimate'] if v is not None and base['metrics'][m]['estimate'] is not None else None for m,v in zip(('kappa','precision','recall','f1'),values)]
                    text.append(f"|{ref}|{dim}|{name}|{'|'.join(fmt(v) for v in values)}|{' / '.join(fmt(v) for v in diffs)}|")
        text.append('')
    (args.out/'开发差异表.md').write_text('\n'.join(text))
    c.write_json(args.out/'output_freeze.json',{'files':{p.name:c.sha(p) for p in args.out.iterdir() if p.is_file()}})
    print(json.dumps({'status':'complete_development_diagnostic','comparisons':len(rows),
        'changes':len(case_differences),'sample_changes':sum(x['in_reference_sample'] for x in case_differences),
        'output':str(args.out)},ensure_ascii=False))


if __name__=='__main__':main()
