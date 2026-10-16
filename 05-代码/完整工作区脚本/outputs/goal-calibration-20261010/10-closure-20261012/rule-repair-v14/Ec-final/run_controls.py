"""Only the fixed Ec affected index; ROOT loads common353 once after merge."""
from pathlib import Path
import copy, datetime, hashlib, importlib.util, json, sys, traceback
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VERS = ROOT / '06-coding/rule-five-dimension-joint-root/versions'
BASE = VERS / 'joint-v14ecb-economic-action-root'
CANDIDATE = VERS / 'joint-v14ecc-economic-object-root'
NAMES = ('evidence','source_packet','source_receipts','relations','dimensions')
def read(p): return json.loads(p.read_text())
def binding(p):
    b=p.read_bytes(); return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,v):
    with p.open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def modules(p):
    result={}
    for n in NAMES:
        spec=importlib.util.spec_from_file_location(n,p/(n+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);result[n]=m
    return result

def main():
    run=sys.argv[1];assert run and Path(run).name==run and run not in ('.','..')
    out=HERE/run;out.mkdir(exist_ok=False);snap=out/'code-snapshot';snap.mkdir()
    origin=read(HERE/'fixed-input-index.json')
    for b in origin['baseline_modules']:assert binding(Path(b['path']))==b
    for e in origin['entries']:assert binding(Path(e['file']['path']))==e['file']
    cases=read(HERE/'controls-index.json')['cases'];assert len(cases)==61
    assert len({(c['control_file'],c['name']) for c in cases})==len(cases)
    assert {(c['control_file'],c['name']) for c in cases}=={(e['file']['path'],e['case_name']) for e in origin['entries']}
    for c,e in zip(cases,origin['entries']):assert c['name']==e['case_name'] and c['expected']==e['expected'] and c['hard_assertion']==e['hard_assertion']
    for n in NAMES:(snap/(n+'.py')).write_bytes((CANDIDATE/(n+'.py')).read_bytes())
    for n in NAMES[:-1]:assert (BASE/(n+'.py')).read_bytes()==(snap/(n+'.py')).read_bytes()
    prepared=[]
    for c in cases:
        if 'packet_binding' in c:
            b=c['packet_binding'];assert binding(Path(b['path']))=={k:b[k] for k in ('path','bytes','sha256')};bundle=read(Path(b['path']))['source_bundle']
        else:bundle=c.get('synthetic_bundle')
        prepared.append((c,bundle))
    save(out/'pre-execution-seal.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver':binding(Path(__file__)),'index':binding(HERE/'controls-index.json'),'origin_index':binding(HERE/'fixed-input-index.json'),'baseline':[binding(BASE/(n+'.py')) for n in NAMES],'candidate':[binding(snap/(n+'.py')) for n in NAMES],'case_N':61,'common353_executed':False})
    old=modules(BASE);new=modules(snap);active=[False];denied=[]
    def audit(event,args):
        if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('Classifier filesystem I/O denied')
    sys.addaudithook(audit)
    def classify(m,unit):
        original=copy.deepcopy(unit);active[0]=True
        try:
            view=m['relations'].RelationView(copy.deepcopy(unit));d=m['dimensions'].judge(view);m['evidence'].validate_decisions(unit,d);assert view.unit==original
            return {'decisions':d,'values':{k:x['value'] for k,x in d.items()},'relations':view.traces(),'material_requests':view.material_requests,'source_requests':view.source_requests,'source_events':view.source_view_events,'private_I_requests':getattr(view,'v11_protected_data_requests',[])}
        finally:active[0]=False
    rows=[]
    for c,bundle in prepared:
        row={k:v for k,v in c.items() if k not in ('semantic_input','synthetic_bundle')}
        try:
            unit=new['source_packet'].semantic_unit(bundle) if bundle is not None else c['semantic_input'];a=classify(old,unit);b=classify(new,unit)
            row.update(baseline=a,candidate=b,expected_match=all(b['values'][d]==v for d,v in c['expected'].items()),baseline_expected_match=all(a['values'][d]==v for d,v in c['expected'].items()),protected_equal=all(a['decisions'][d]==b['decisions'][d] for d in ('S','E','I','F')),source_equal=all(a[k]==b[k] for k in ('material_requests','source_requests','source_events','private_I_requests')),changed_dimensions=[d for d in a['decisions'] if a['decisions'][d]!=b['decisions'][d]])
            row['reserved_Ec_equal']=not c.get('must_preserve_Ec_complete_decision') or a['decisions']['Ec']==b['decisions']['Ec']
            def contexts(x):
                ids=set()
                if isinstance(x,dict):
                    for k,v in x.items():
                        if k=='context_evidence' and isinstance(v,list):ids.update(q['context_id'] for q in v if isinstance(q,dict) and q.get('context_id'))
                        ids.update(contexts(v))
                elif isinstance(x,list):
                    for v in x:ids.update(contexts(v))
                return ids
            sa=c.get('source_consumption_assertions');row['source_assertions_pass']=True
            if sa:
                consumed=contexts(b['decisions'][sa['dimension']]);row['source_assertions_pass']=not (consumed & set(sa.get('forbidden_final_context_ids',[]))) and set(sa.get('required_final_context_ids',[]))<=consumed
            row['pass']=all(row[k] for k in ('expected_match','protected_equal','source_equal','reserved_Ec_equal','source_assertions_pass'))
        except Exception as e:row.update({'pass':False,'error':{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}})
        rows.append(row)
    hard=[x for x in rows if x.get('hard_assertion',True)]
    summary={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_N':len(rows),'prior_Ec_N':56,'new_object_boundary_N':5,'hard_N':len(hard),'hard_pass_N':sum(x['pass'] for x in hard),'hard_failed':[{k:x.get(k) for k in ('name','expected','baseline_expected_match','expected_match','error')} for x in hard if not x['pass']],'protected_changes':[x['name'] for x in rows if x.get('protected_equal') is False],'source_changes':[x['name'] for x in rows if x.get('source_equal') is False],'changed_cases':[{'name':x['name'],'dimensions':x.get('changed_dimensions'),'before':x.get('baseline',{}).get('values'),'after':x.get('candidate',{}).get('values')} for x in rows if x.get('changed_dimensions')],'filesystem_access_attempts':denied,'common353_executed':False,'model_calls':0,'population_calls':0,'formal_accuracy':False}
    save(out/'results.json',rows);save(out/'summary.json',summary);save(out/'output-seal.json',{'files':[binding(p) for p in sorted(out.rglob('*')) if p.is_file()]});print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
