"""A/C agreement before third-agent review; no machine prediction file read."""
from pathlib import Path
from collections import Counter
import csv
import datetime
import json
import numpy as np
import statistical_core_r3 as c

OUT=Path(__file__).resolve().parent
RUN=OUT.parent


def independent_point(counts):
    a11,a10,a01,a00=map(float,counts)
    n=a11+a10+a01+a00
    if not n:return {k:None for k in ('kappa','agreement','left_positive_rate','right_positive_rate')}
    po=(a11+a00)/n;pA=(a11+a10)/n;pC=(a11+a01)/n
    pe=pA*pC+(1-pA)*(1-pC)
    return {'kappa':(po-pe)/(1-pe) if 1-pe>1e-12 else None,
            'agreement':po,'left_positive_rate':pA,'right_positive_rate':pC}


def main():
    final_qa=RUN/'reference/A_C合并与逐字证据QA-v11.json'
    qa=c.read(final_qa)
    assert qa['status']=='pass' and qa['all_final_labels_binary'] is True
    for path,digest in qa['output_sha256'].items():assert c.sha(RUN/path)==digest
    records=[];bindings={};audit_n=0
    for stage,material in [('first_v9','v9'),('final_v11','v11')]:
        ctx=c.load_context(material)
        a_path=RUN/f'reference/agent_A_{stage}.jsonl'
        cc_path=RUN/f'reference/agent_C_{stage}.jsonl'
        a=c.jsonl(a_path);cc=c.jsonl(cc_path)
        assert set(a)==set(cc)==set(ctx['sample'])
        bindings[stage]={'A':{'path':str(a_path),'sha256':c.sha(a_path)},
                         'C':{'path':str(cc_path),'sha256':c.sha(cc_path)},
                         'material':material,
                         'context_sha256':{str(p):c.sha(p) for p in ctx['source_paths']}}
        cache={}
        for component in ('probability_canonical','enriched_challenge'):
            eligible=[rid for rid in ctx['sample'] if ctx['sample'][rid]['component']==component]
            for group,kind in c.groups_and_weights(component):
                ids=sorted(rid for rid in eligible if group=='ALL' or ctx['sample'][rid]['group']==group)
                if not ids:continue
                for dim in c.DIMS:
                    row=c.comparison(ctx,a,cc,dim,ids,component,group,kind,'A_C','C',cache)
                    row['stage']=stage;row['material_version']=material
                    row['reference']='symmetric independent A/C comparison; neither coder is semantic truth'
                    row['symmetric_raw_cells']=dict(zip(('A1_C1','A1_C0','A0_C1','A0_C0'),row.pop('raw_confusion').values()))
                    row['symmetric_weighted_cells']=dict(zip(('A1_C1','A1_C0','A0_C1','A0_C0'),row.pop('weighted_confusion').values()))
                    row['A_positive_n']=row.pop('left_positive_n')
                    row['C_positive_n']=row.pop('reference_positive_n')
                    row['first_submissions_rewritten']=False
                    # Independently enumerate cells without the core helper.
                    cells=Counter((a[rid]['labels'][dim],cc[rid]['labels'][dim]) for rid in ids
                                  if c.binary(a[rid]['labels'][dim]) and c.binary(cc[rid]['labels'][dim]))
                    manual=[cells[p] for p in ((1,1),(1,0),(0,1),(0,0))]
                    assert manual==list(row['symmetric_raw_cells'].values())
                    weights=c.weighting(ctx,ids,kind)
                    manual_weighted=[sum(float(w) for rid,w in zip(ids,weights)
                                         if c.binary(a[rid]['labels'][dim]) and c.binary(cc[rid]['labels'][dim])
                                         and (a[rid]['labels'][dim],cc[rid]['labels'][dim])==p)
                                     for p in ((1,1),(1,0),(0,1),(0,0))]
                    assert np.allclose(manual_weighted,list(row['symmetric_weighted_cells'].values()))
                    for name,value in independent_point(manual_weighted).items():
                        actual=row['metrics'][name]['estimate']
                        assert (value is None and actual is None) or np.isclose(value,actual)
                    audit_n+=1;records.append(row)
    notes=c.analysis_notes()
    notes.update({'first_v9':'Original independent first submissions retained verbatim, including unresolved labels. Source/context is v9.',
        'final_v11':'Independent same-source material reread applied only to four changed-material units; all other contexts byte-identical to v11. C reason-column correction separately effective, without label changes.',
        'paired_pending_scope':'Metrics condition on actual paired binary labels; pending labels are excluded by dimension, with IDs/n retained. No imputation.',
        'A_C_reference_role':'Symmetric κ/agreement and marginal positive rates only. No P/R/F1 treating either independent coder as truth.',
        'challenge_NHC':'No NHC challenge was sampled; no artificial zero-positive NHC stratum reported.',
        'machine_predictions_read':False})
    result={'created_at':datetime.datetime.now().astimezone().isoformat(),'analysis_notes':notes,
            'bindings':bindings,'merge_qa':{'path':str(final_qa),'sha256':c.sha(final_qa)},
            'script_sha256':c.sha(Path(__file__)),'comparisons':records}
    target=OUT/'A_C协商前信度-first-v9与final-v11.json'
    assert not target.exists();c.write_json(target,result)
    csv_path=OUT/'A_C协商前信度-first-v9与final-v11.csv'
    assert not csv_path.exists()
    columns=['stage','material_version','component','group','weighting','dimension','unit_frame_n','paired_n',
             'excluded_pending_n','A_positive_n','C_positive_n','A1_C1','A1_C0','A0_C1','A0_C0',
             'kappa','kappa_ci95_low','kappa_ci95_high','kappa_undefined_repetitions',
             'agreement','agreement_ci95_low','agreement_ci95_high','diagnostic_0_80']
    with csv_path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=columns);writer.writeheader()
        for row in records:
            flat={k:row[k] for k in columns if k in row};flat.update(row['symmetric_raw_cells'])
            for name in ('kappa','agreement'):
                metric=row['metrics'][name];flat[name]=metric['estimate']
                flat[name+'_ci95_low']=metric['ci95_primary']['low']
                flat[name+'_ci95_high']=metric['ci95_primary']['high']
            flat['kappa_undefined_repetitions']=row['metrics']['kappa']['ci95_primary']['undefined_repetitions']
            flat['diagnostic_0_80']=row['point_0_80_diagnostics']['kappa'];writer.writerow(flat)
    low=[{k:row[k] for k in ('stage','component','group','weighting','dimension','paired_n','excluded_pending_n')}
         | {'kappa':row['metrics']['kappa']['estimate'],'diagnostic':row['point_0_80_diagnostics']['kappa']}
         for row in records if row['point_0_80_diagnostics']['kappa']!='at_least_0_80']
    qa_path=OUT/'A_C信度统计独立数值QA.json'
    assert not qa_path.exists();c.write_json(qa_path,{'status':'pass','comparisons_checked':audit_n,
        'manual_cell_enumeration_and_weighted_point_formulas_match':True,
        'original_first_results_still_match_merge_qa':all(c.sha(p)==digest for p,digest in qa['first_result_hashes_after'].items()),
        'all_NA_and_below_0_80_records':low,'source_sha256':c.sha(target),'csv_sha256':c.sha(csv_path),
        'machine_predictions_read':False})
    summary={stage:{row['dimension']:{'kappa':row['metrics']['kappa']['estimate'],
                    'agreement':row['metrics']['agreement']['estimate'],'n':row['paired_n']}
                   for row in records if row['stage']==stage and row['component']=='probability_canonical'
                   and row['group']=='ALL' and row['weighting']=='unweighted'}
             for stage in ('first_v9','final_v11')}
    print(json.dumps({'status':'complete','comparisons':len(records),'probability_unweighted_ALL':summary,
                      'NA_or_below_0_80_record_n':len(low),'json':str(target)},ensure_ascii=False))


if __name__=='__main__':main()
