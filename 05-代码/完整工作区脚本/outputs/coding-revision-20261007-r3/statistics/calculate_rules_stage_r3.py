"""Frozen current rule against independent A/C; provisional, no candidate/LLM."""
from pathlib import Path
import csv
import datetime
import json
import numpy as np
import statistical_core_r3 as c

RUN=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent


def main():
    path=RUN/'rules-v33/all_predictions_material_v11.jsonl'
    assert c.sha(path)=='294acd08ec55658bc254e80e0171e2f22ea29cc42be96cb61a0e1b428b1ed481'
    ctx=c.load_context('v11');rule=c.jsonl(path)
    assert len(rule)==4924 and set(rule)==set(ctx['inputs'])
    assert all(c.binary(c.label(row,d)) for row in rule.values() for d in c.DIMS)
    merge_qa=c.read(RUN/'reference/A_C合并与逐字证据QA-v11.json')
    refs={ref:c.jsonl(RUN/f'reference/agent_{ref}_final_v11.jsonl') for ref in 'AC'}
    for ref in 'AC':
        refpath=RUN/f'reference/agent_{ref}_final_v11.jsonl'
        assert c.sha(refpath)==merge_qa['output_sha256'][str(refpath.relative_to(RUN))]
    cache={};records=[];undefined=[];diagnostics=[]
    for component in ('probability_canonical','enriched_challenge'):
        eligible=[rid for rid in ctx['sample'] if ctx['sample'][rid]['component']==component]
        for group,kind in c.groups_and_weights(component):
            ids=sorted(rid for rid in eligible if group=='ALL' or ctx['sample'][rid]['group']==group)
            if not ids:continue
            for reference,labels in refs.items():
                for dim in c.DIMS:
                    row=c.comparison(ctx,rule,labels,dim,ids,component,group,kind,'rules-v33-v11',reference,cache)
                    row['stage']='provisional_rules_vs_independent_A_C'
                    row['material_version']='v11';row['candidate_or_LLM_compared']=False
                    raw=row['raw_confusion'];weighted=row['weighted_confusion']
                    # Independent raw/weighted cells and conventional scalar formulas.
                    manual=[]
                    w=c.weighting(ctx,ids,kind)
                    for p in ((1,1),(1,0),(0,1),(0,0)):
                        chosen=[i for i,rid in enumerate(ids) if c.binary(c.label(rule[rid],dim))
                                and c.binary(c.label(labels[rid],dim))
                                and (c.label(rule[rid],dim),c.label(labels[rid],dim))==p]
                        manual.append((len(chosen),sum(float(w[i]) for i in chosen)))
                    assert [v[0] for v in manual]==list(raw.values())
                    assert np.allclose([v[1] for v in manual],list(weighted.values()))
                    tp,fp,fn,tn=[v[1] for v in manual];n=tp+fp+fn+tn
                    independent={'precision':tp/(tp+fp) if tp+fp else None,
                                 'recall':tp/(tp+fn) if tp+fn else None,
                                 'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
                    if n:
                        po=(tp+tn)/n;pl=(tp+fp)/n;pr=(tp+fn)/n
                        pe=pl*pr+(1-pl)*(1-pr)
                        independent.update({'agreement':po,'kappa':(po-pe)/(1-pe) if 1-pe>1e-12 else None})
                    else:independent.update({'agreement':None,'kappa':None})
                    for name,value in independent.items():
                        actual=row['metrics'][name]['estimate']
                        assert (value is None and actual is None) or np.isclose(value,actual)
                    reasons={}
                    for name,metric in row['metrics'].items():
                        if metric['estimate'] is not None:continue
                        reasons[name]=('no paired binary observations' if not n else
                            'both marginals identical constant; expected agreement equals1' if name=='kappa' else
                            'no predicted positives: TP+FP=0' if name=='precision' else
                            'no reference positives: TP+FN=0' if name=='recall' else
                            'neither side has a positive: 2TP+FP+FN=0' if name=='f1' else 'zero denominator')
                    row['undefined_point_reasons']=reasons
                    identifier={k:row[k] for k in ('component','group','weighting','reference','dimension','paired_n')}
                    if reasons:undefined.append(identifier|{'raw_confusion':raw,'reasons':reasons})
                    if any(v!='at_least_0_80' for v in row['point_0_80_diagnostics'].values()):
                        diagnostics.append(identifier|{'raw_confusion':raw,'diagnostics':row['point_0_80_diagnostics'],
                            'metrics':{k:v['estimate'] for k,v in row['metrics'].items() if k in ('kappa','precision','recall','f1')}})
                    records.append(row)
    notes=c.analysis_notes();notes.update({'references':'Independent AI-agent A/C final v11 only. Third candidate and final LLM not yet bound; these are provisional comparisons.',
        'rule_v9_v11_material_note':'The source material changed; root independently confirmed all rule binary labels unchanged. No accuracy improvement from source completion is asserted.',
        'no_old_LLM_substitution':True})
    result={'stage':'provisional_rules_vs_independent_A_C','created_at':datetime.datetime.now().astimezone().isoformat(),
        'analysis_notes':notes,'rules':{'path':str(path),'sha256':c.sha(path)},
        'references':{ref:{'path':str(RUN/f'reference/agent_{ref}_final_v11.jsonl'),
                           'sha256':c.sha(RUN/f'reference/agent_{ref}_final_v11.jsonl')} for ref in 'AC'},
        'source_sha256':{str(p):c.sha(p) for p in ctx['source_paths']},'comparisons':records,
        'script_sha256':c.sha(Path(__file__))}
    target=OUT/'阶段规则-v33-v11对最终A_C.json';assert not target.exists();c.write_json(target,result)
    c.write_json(OUT/'阶段规则-v33-v11低值与NA.json',{'stage':result['stage'],'undefined':undefined,'diagnostics':diagnostics})
    columns=['component','group','weighting','reference','dimension','unit_frame_n','paired_n','excluded_pending_n',
             'left_positive_n','reference_positive_n','TP','FP','FN','TN']
    columns += [col for name in c.METRIC_NAMES for col in (name,name+'_ci95_low',name+'_ci95_high')]
    csvpath=OUT/'阶段规则-v33-v11对最终A_C.csv';assert not csvpath.exists()
    with csvpath.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=columns);writer.writeheader()
        for row in records:
            flat={k:row[k] for k in columns if k in row};flat.update(row['raw_confusion'])
            for name,metric in row['metrics'].items():
                flat[name]=metric['estimate'];flat[name+'_ci95_low']=metric['ci95_primary']['low']
                flat[name+'_ci95_high']=metric['ci95_primary']['high']
            writer.writerow(flat)
    c.write_json(OUT/'阶段规则统计独立数值QA.json',{'status':'pass','comparisons':len(records),
        'manual_raw_weighted_cells_and_scalar_metrics_match':True,'classification_interval_n':len(records)*len(c.METRIC_NAMES)*2,
        'rule_sha_verified':True,'source_sha256':c.sha(target),'candidate_or_LLM_read':False,
        'undefined_comparison_n':len(undefined),'comparison_with_below_target_or_NA_n':len(diagnostics)})
    summary={ref:{row['dimension']:{k:row['metrics'][k]['estimate'] for k in ('kappa','precision','recall','f1')}
                 for row in records if row['reference']==ref and row['component']=='probability_canonical'
                 and row['group']=='ALL' and row['weighting']=='unweighted'} for ref in 'AC'}
    print(json.dumps({'status':'complete','comparisons':len(records),'probability_unweighted_ALL':summary,
                      'undefined_comparison_n':len(undefined),'json':str(target)},ensure_ascii=False))


if __name__=='__main__':main()
