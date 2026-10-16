"""Run exactly the presealed synthetic I/F controls once."""
from pathlib import Path
import hashlib
import json
import sys
import traceback

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
V2=ROOT/'06-coding/rule-v20-semantic-audit-repair-sol/versions/v2'


def binding(path):
    data=Path(path).read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}


def write_new(name,data):
    with (HERE/name).open('x',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def main():
    pre=json.loads((HERE/'pre-execution-seal.json').read_text())
    for expected in [pre['controls'],pre['authority_and_manual_basis'],pre['algorithm_bindings'],*pre['verified_modules_and_manual']]:
        actual=binding(expected['path'])
        if actual['sha256']!=expected['sha256'] or actual['bytes']!=expected['bytes']:
            raise ValueError('presealed input changed '+expected['path'])
    controls=json.loads(Path(pre['controls']['path']).read_text())
    if len(controls['cases'])!=20:raise ValueError('expected twenty presealed controls')
    sys.path.insert(0,str(V2))
    import relations
    import dimensions
    import evidence
    results=[]
    for c in controls['cases']:
        r={'name':c['name'],'synthetic_only':True,'expected':c['expected'],
           'manual_reason':c['manual_reason'],'current_text':c['synthetic_input']['text'],
           'engine_called':False,'evidence_validation_passed':False}
        try:
            view=relations.RelationView(c['synthetic_input'])
            r['relation_traces']=view.traces();r['material_requests']=view.material_requests
            r['source_requests']=view.source_requests
            r['engine_called']=True
            decisions=dimensions.judge(view);r['decisions']=decisions
            r['observed']={d:decisions[d]['value'] for d in ('I','F')}
            r['mismatches']=[{'dimension':d,'expected':c['expected'][d],'observed':r['observed'][d]}
                             for d in ('I','F') if c['expected'][d]!=r['observed'][d]]
            evidence.validate_decisions(c['synthetic_input'],decisions)
            r['evidence_validation_passed']=True;r['passed']=not r['mismatches']
        except Exception as exc:
            r['passed']=False;r['error']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
        results.append(r)
    summary={'status':'independent_presealed_synthetic_execution_complete','case_N':20,
             'pass_N':sum(c['passed'] for c in results),'fail_N':sum(not c['passed'] for c in results),
             'mismatch_N':sum(len(c.get('mismatches',[])) for c in results),
             'exception_N':sum('error' in c for c in results),
             'evidence_validation_pass_N':sum(c['evidence_validation_passed'] for c in results),
             'failed_names':[c['name'] for c in results if not c['passed']],
             'algorithm_bindings':binding(V2/'algorithm-bindings.json'),
             'controls_binding':binding(HERE/'controls-fixed-before-execution.json'),
             'imported_modules':{'relations':relations.__file__,'dimensions':dimensions.__file__,'evidence':evidence.__file__},
             'execution_attempt_N':1,'formal_records_used':0,'is_human_reference':False,
             'owner_replay_or_regression_result_files_read':False,'neutral_projection_called':False,
             'owner_code_modified':False,'expected_changed':False}
    write_new('execution-results.json',{'summary':summary,'cases':results})
    with (HERE/'execution-results.jsonl').open('x',encoding='utf-8') as f:
        for c in results:f.write(json.dumps(c,ensure_ascii=False,allow_nan=False)+'\n')
    write_new('execution-summary.json',summary)
    print(json.dumps({k:summary[k] for k in ['case_N','pass_N','fail_N','mismatch_N','exception_N','evidence_validation_pass_N','failed_names']},ensure_ascii=False))


if __name__=='__main__':main()
