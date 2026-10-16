"""Prospectively registered secondary sensitivity; primary first labels unchanged."""
import copy
import datetime
import importlib.util
import json
from pathlib import Path
import re
from analyze_current_reruns import HERE,LLM,METHODS,load_sealed_predictions,load_reference_units,sha
from comparison_statistics import DIMS,evaluate_units,label

def main():
    rules,first,inputs,seal=load_sealed_predictions()
    out=HERE/'rerun_comparisons/LLM更正影响';out.mkdir(parents=True,exist_ok=False)
    corrected=copy.deepcopy(first);audit=[];bindings={}
    for folder in sorted(LLM.glob('shard-*')):
        if not folder.is_dir():continue
        selected={}
        for f in folder.glob('correction-???-??.json'):
            match=re.fullmatch(r'correction-(\d{3})-(\d{2})\.json',f.name)
            batch,revision=map(int,match.groups())
            if batch not in selected or revision>selected[batch][0]:selected[batch]=(revision,f)
        spec=importlib.util.spec_from_file_location('correction_validator',folder/'validate_output.py')
        validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
        schema=json.loads((folder/'output_schema.json').read_text())
        for batch,(_,f) in sorted(selected.items()):
            raw=json.loads(f.read_text());packet=json.loads((folder/f'input-{batch:03d}.json').read_text())['rows']
            errors=validator.shape(raw,schema)
            if not errors:errors+=validator.validate(raw,packet)
            assert not errors,('Last recorded correction is not valid; do not silently select an earlier favorable output',folder.name,f.name,errors)
            bindings[str(f.relative_to(LLM))]=sha(f)
            for row in raw['rows']:
                old=first[row['id']]
                fields=sorted(k for k in set(old)|set(row) if old.get(k)!=row.get(k))
                dims=[d for d in DIMS if label(old['labels'][d])!=label(row['labels'][d])]
                if fields:audit.append({'id':row['id'],'file':str(f.relative_to(LLM)),
                    'changed_fields':fields,'changed_dimensions':dims,
                    'first_labels':old['labels'],'corrected_labels':row['labels']})
                corrected[row['id']]=row
    changed={d:sum(d in a['changed_dimensions'] for a in audit) for d in DIMS}
    total={'registered_plan_sha256':sha(HERE/'LLM更正影响分析预登记.json'),
        'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'analysis':'secondary sensitivity of independently logged corrections, not a new blind test',
        'primary_predictions_not_modified':True,'correction_selection':'last numbered recorded correction per batch; no score-based selection',
        'correction_files':bindings,'changed_record_n':len(audit),
        'label_changed_record_n':sum(bool(a['changed_dimensions']) for a in audit),
        'changed_labels_per_dimension':changed,'changes':audit,
        'first_prediction_seal_sha256':sha(LLM/'prediction_seal.json')}
    (out/'correction_audit.json').write_text(json.dumps(total,ensure_ascii=False,indent=2)+'\n')
    (out/'corrected_predictions_secondary.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for _,r in sorted(corrected.items())))
    md=['# LLM自检更正影响（次要敏感性）','',
        f'共{len(bindings)}批有更正；{len(audit)}条记录的字段改变，其中{total["label_changed_record_n"]}条标签改变。主结果仍使用首次输出。',
        '按照内部预登记规则统一采用每批最后编号的更正，未根据参考一致率选择。此处不是新的独立验证。',
        '本表首次与更正值均按四方法共同可判配对子集重新计算；本表的首次值可能与三方法共同可判的主表不同。共同可判条数及占本组的比例并列显示。','',
        '|样本组|维度|首次召回A/C|更正后召回A/C|首次F1 A/C|更正后F1 A/C|共同可判n A/C|共同可判比例A/C|','|---|---|---:|---:|---:|---:|---:|---:|']
    for scope in ('current1268','H427'):
        raw_units,_=load_reference_units(scope,rules,first,inputs)
        units=[]
        for u in raw_units:
            pred={m:u['predictions'][m]['labels'] for m in METHODS}
            pred['llm_gpt56_sol_corrected']=corrected[u['id']]['labels']
            units.append({'id':u['id'],'weight':u['weight'],'predictions':pred,
                          'references':{c:u['references'][c]['labels'] for c in ('A','C')}})
        result=evaluate_units(units,(*METHODS,'llm_gpt56_sol_corrected'))
        (out/f'{scope}_correction_sensitivity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        for d in DIMS:
            def fmt(method,key):
                vals=[result['methods'][c][d]['by_method'][method]['common_units_weighted']['conditional_scores'][key] for c in ('A','C')]
                return '/'.join('NA' if v is None else f'{v:.1%}' for v in vals)
            common_n=[result['methods'][c][d]['common_unit_n'] for c in ('A','C')]
            ns='/'.join(map(str,common_n));coverage='/'.join(f'{n/len(units):.1%}' for n in common_n)
            md.append(f'|{scope}|{d}|{fmt("llm_gpt56_sol","recall")}|{fmt("llm_gpt56_sol_corrected","recall")}|{fmt("llm_gpt56_sol","f1")}|{fmt("llm_gpt56_sol_corrected","f1")}|{ns}|{coverage}|')
    (out/'summary.md').write_text('\n'.join(md)+'\n')
    print(json.dumps({'correction_batches':len(bindings),'records_changed':len(audit),'label_changed_records':total['label_changed_record_n'],'output':str(out)},ensure_ascii=False))

if __name__=='__main__':main()
