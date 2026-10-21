"""Compare material-only rule changes; final LLM results are never read."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import argparse
import csv
import hashlib
import json

ROOT=Path('/PROJECT_ROOT')
OUT=Path(__file__).resolve().parent
PARENT=OUT.parent


def read(path):
    data=[json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    result={r['id']:r for r in data}
    assert len(data)==len(result)
    return result


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate-inputs',type=Path,default=PARENT/'rule_inputs_v31_shared.jsonl')
    parser.add_argument('--candidate-predictions',type=Path,default=OUT/'rules-v31-completed-material-frozen.jsonl')
    parser.add_argument('--candidate-metrics',type=Path,default=OUT/'三部门编码指标.json')
    parser.add_argument('--label',default='v1')
    parser.add_argument('--effect-isolation',default='Same rule classification code, changed source context materials only; frozen old code-only predictions compared against completed-material run.')
    args=parser.parse_args()
    old_metrics=PARENT/'statistics-code-only/三部门编码指标.json'
    old_pred=PARENT/'statistics-code-only/rules-v31-code-only-frozen.jsonl'
    old_inp=ROOT/'outputs/final-three-department-20261007/rules-v30/rule_inputs_v30_shared.jsonl'
    sources=[old_metrics,old_pred,old_inp,args.candidate_inputs,args.candidate_predictions,args.candidate_metrics,Path(__file__)]
    hashes={str(p):sha(p) for p in sources}
    before,after=read(old_pred),read(args.candidate_predictions)
    inputs_before,inputs=read(old_inp),read(args.candidate_inputs)
    assert len(before)==len(after)==len(inputs)==4924 and set(before)==set(after)==set(inputs)==set(inputs_before)
    for rid in inputs:
        assert inputs[rid]['input']['unit_text']==inputs_before[rid]['input']['unit_text']
        assert inputs[rid]['original_id']==inputs_before[rid]['original_id']
    old,new=json.loads(old_metrics.read_text()),json.loads(args.candidate_metrics.read_text())
    assert new['latest_llm']['path'] is None
    index={(r['frame'],r['group'],r['dimension'],r['reference']):r for r in old['records'] if r['method']=='rules_v31_code_only'}
    rows=[]
    for b in new['records']:
        if b['method']=='A_C':continue
        a=index[b['frame'],b['group'],b['dimension'],b['reference']]
        assert a['n']==b['n'] and a['exclusions']==b['exclusions'] and a['eligible_ids_sha256']==b['eligible_ids_sha256']
        row={k:b[k] for k in ('frame','group','dimension','reference','n','excluded_n','right_positive_n')}
        row['old_confusion'],row['new_confusion']=a['confusion'],b['confusion']
        for metric in ('precision','recall','f1','kappa','agreement'):
            x,y=a['metrics'][metric]['estimate'],b['metrics'][metric]['estimate']
            row['old_'+metric],row['new_'+metric]=x,y
            row['delta_'+metric]=y-x if x is not None and y is not None else None
        row['changed']=row['old_confusion']!=row['new_confusion']
        rows.append(row)
    changes=[]
    for rid in inputs:
        for d in ('S','E','Ec','I','F'):
            a,b=before[rid]['prediction']['labels'][d],after[rid]['prediction']['labels'][d]
            if a!=b:
                changes.append({'id':rid,'dimension':d,'old':a,'new':b,'unit_text':inputs[rid]['input']['unit_text']})
    metadata_path=ROOT/'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
    meta={Path(r['original_file']).stem:r['analysis_group'] for r in json.loads(metadata_path.read_text())['rows']}
    reference_path=ROOT/'outputs/autocode-v25-20260927/current_1268_references.jsonl'
    refs=read(reference_path)
    for path in (metadata_path,reference_path):hashes[str(path)]=sha(path)
    independent_n=0
    for b in new['records']:
        if b['frame']!='main1057' or b['method']=='A_C':continue
        counts=Counter()
        for rid,r in refs.items():
            group=meta[inputs[rid]['input']['original_file_stem']]
            if group not in ('NMPA','NHSA','NHC') or b['group'] not in ('ALL',group):continue
            x=after[rid]['prediction']['labels'][b['dimension']]
            y=r['original_references'][b['reference']]['labels'][b['dimension']]
            if type(y) is int and y in (0,1):counts[x,y]+=1
        tp,fp,fn,tn=[counts[x] for x in ((1,1),(1,0),(0,1),(0,0))]
        assert list(b['confusion'].values())==[tp,fp,fn,tn]
        n=tp+fp+fn+tn
        po=Fraction(tp+tn,n);pe=Fraction((tp+fp)*(tp+fn)+(fn+tn)*(fp+tn),n*n)
        ratio=lambda a,b:float(Fraction(a,b)) if b else None
        values={'kappa':float((po-pe)/(1-pe)) if pe!=1 else None,'agreement':float(po),
                'precision':ratio(tp,tp+fp),'recall':ratio(tp,tp+fn),'f1':ratio(2*tp,2*tp+fp+fn)}
        for metric,wanted in values.items():
            got=b['metrics'][metric]['estimate']
            assert got is None if wanted is None else got is not None and abs(got-wanted)<1e-12
        independent_n+=1
    assert independent_n==40
    assert hashes=={p:sha(p) for p in hashes}
    result={'status':'DEVELOPMENT_MATERIAL_ONLY_DIAGNOSTIC_NOT_FINAL_STATISTICS',
            'label':args.label,'effect_isolation':args.effect_isolation,
            'reference_identity':'Unchanged first AI A/C submissions, not independent human validation',
            'LLM_loaded':False,'CI_recomputed':False,'independent_main_rule_records_verified':independent_n,
            'rule_id_dimension_changes':changes,'comparisons':rows,'source_sha256':hashes}
    (OUT/f'材料效应-{args.label}-逐项比较.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    flat=[]
    for row in rows:
        item={k:v for k,v in row.items() if k not in ('old_confusion','new_confusion')}
        for phase in ('old','new'):item.update({phase+'_'+k:v for k,v in row[phase+'_confusion'].items()})
        flat.append(item)
    with (OUT/f'材料效应-{args.label}-逐项比较.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    print(json.dumps({'label':args.label,'changes':changes,'changed_metric_rows':[r for r in rows if r['changed']],'independently_verified_main_records':independent_n},ensure_ascii=False))


if __name__=='__main__':main()
