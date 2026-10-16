"""Only the fixed Ec affected index; ROOT loads common353 once after merge."""
from pathlib import Path
from routing_checks import check_actual_route
import copy, datetime, hashlib, importlib.util, json, sys, traceback
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VERS = ROOT / '06-coding/rule-five-dimension-joint-root/versions'
BASE = VERS / 'joint-v14ecc-economic-object-root'
CANDIDATE = VERS / 'joint-v14ecd-finite-negotiation-root'
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
    prep=read(HERE/'preparation.json')
    for b in prep['base_modules']:assert binding(Path(b['path']))==b
    for key in ['prior_index','contract','controls','index']:
        b=prep[key];assert binding(Path(b['path']))==b
    for b in prep['source_fixtures']:assert binding(Path(b['path']))==b
    cases=read(HERE/'controls-index.json')['cases'];assert len(cases)==72
    assert len({(c['control_file'],c['name']) for c in cases})==len(cases)
    for n in NAMES:(snap/(n+'.py')).write_bytes((CANDIDATE/(n+'.py')).read_bytes())
    for n in NAMES[:3]:assert (BASE/(n+'.py')).read_bytes()==(snap/(n+'.py')).read_bytes()
    prepared=[]
    for c in cases:
        if 'packet_binding' in c:
            b=c['packet_binding'];assert binding(Path(b['path']))=={k:b[k] for k in ('path','bytes','sha256')};bundle=read(Path(b['path']))['source_bundle']
        else:bundle=c.get('synthetic_bundle')
        prepared.append((c,bundle))
    save(out/'pre-execution-seal.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver':binding(Path(__file__)),'index':binding(HERE/'controls-index.json'),'preparation':binding(HERE/'preparation.json'),'baseline':[binding(BASE/(n+'.py')) for n in NAMES],'candidate':[binding(snap/(n+'.py')) for n in NAMES],'case_N':72,'common353_executed':False})
    old=modules(BASE);new=modules(snap);active=[False];denied=[]
    def audit(event,args):
        if active[0] and event=='open':denied.append(str(args[0]));raise RuntimeError('Classifier filesystem I/O denied')
    sys.addaudithook(audit)
    def classify(m,unit,bundle=None):
        original=copy.deepcopy(unit);active[0]=True
        try:
            view=m['relations'].RelationView(copy.deepcopy(unit));d=m['dimensions'].judge(view);m['evidence'].validate_decisions(unit,d);assert view.unit==original
            result={'decisions':d,'values':{k:x['value'] for k,x in d.items()},'relations':view.traces(),'material_requests':view.material_requests,'source_requests':view.source_requests,'source_events':view.source_view_events,'private_I_requests':getattr(view,'v11_protected_data_requests',[])}
        finally:active[0]=False
        if bundle is not None:result['route_check']=check_actual_route(m,view,d,bundle)
        return result
    rows=[]
    for c,bundle in prepared:
        row={k:v for k,v in c.items() if k not in ('semantic_input','synthetic_bundle')}
        try:
            unit=new['source_packet'].semantic_unit(bundle) if bundle is not None else c['semantic_input'];a=classify(old,unit);b=classify(new,unit,bundle if c['name'].startswith('finite_definition/') else None)
            row.update(baseline=a,candidate=b,expected_match=all(b['values'][d]==v for d,v in c['expected'].items()),baseline_expected_match=all(a['values'][d]==v for d,v in c['expected'].items()),protected_equal=all(a['decisions'][d]==b['decisions'][d] for d in ('S','E','I','F')),source_equal=all(a[k]==b[k] for k in ('material_requests','source_requests','source_events','private_I_requests')),changed_dimensions=[d for d in a['decisions'] if a['decisions'][d]!=b['decisions'][d]])
            row['reserved_Ec_equal']=not c.get('must_preserve_Ec_complete_decision') or a['decisions']['Ec']==b['decisions']['Ec']
            added=[q for q in b['material_requests'] if q not in a['material_requests']]
            row['source_append_contract']=a['source_events']==b['source_events'] and a['private_I_requests']==b['private_I_requests'] and all(q in b['material_requests'] for q in a['material_requests']) and all(q in b['source_requests'] for q in a['source_requests']) and all(q.get('path')=='price_arrangement' and q.get('stop_reason')=='finite_negotiation_definition_unresolved' for q in added) and b['source_requests']==a['source_requests']+[q for q in b['source_requests'] if q not in a['source_requests']] and all(q in added for q in b['source_requests'] if q not in a['source_requests'])
            revision=c.get('preservation_contract_revision')
            row['preservation_supersession_valid']=False
            if revision:
                cb=revision['contract_binding'];assert binding(Path(cb['path']))==cb
                repl=next(q for q in cases if q['name']==revision['replacement_case_name'])
                row['preservation_supersession_valid']=revision['superseded_flags']==['must_preserve_Ec_complete_decision'] and repl['expected']=={'Ec':None} and repl['packet_binding']['sha256']==c['packet_binding']['sha256'] and b['values']['Ec'] is None
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
            row['pass']=all(row[k] for k in ('expected_match','protected_equal','source_append_contract','source_assertions_pass')) and (row['reserved_Ec_equal'] or row['preservation_supersession_valid'])
        except Exception as e:row.update({'pass':False,'error':{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}})
        rows.append(row)
    hard=[x for x in rows if x.get('hard_assertion',True)]
    summary={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_N':len(rows),'prior_Ec_N':61,'new_source_boundary_N':11,'hard_N':len(hard),'hard_pass_N':sum(x['pass'] for x in hard),'hard_failed':[{k:x.get(k) for k in ('name','expected','baseline_expected_match','expected_match','error')} for x in hard if not x['pass']],'protected_changes':[x['name'] for x in rows if x.get('protected_equal') is False],'source_changes':[x['name'] for x in rows if x.get('source_equal') is False],'source_contract_violations':[x['name'] for x in rows if x.get('source_append_contract') is False],'superseded_preservation_checks':[{'name':x['name'],'old_check':x['reserved_Ec_equal'],'new_contract':x['preservation_supersession_valid']} for x in rows if x.get('preservation_contract_revision')],'changed_cases':[{'name':x['name'],'dimensions':x.get('changed_dimensions'),'before':x.get('baseline',{}).get('values'),'after':x.get('candidate',{}).get('values')} for x in rows if x.get('changed_dimensions')],'filesystem_access_attempts':denied,'common353_executed':False,'model_calls':0,'population_calls':0,'formal_accuracy':False}
    save(out/'results.json',rows);save(out/'summary.json',summary);save(out/'output-seal.json',{'files':[binding(p) for p in sorted(out.rglob('*')) if p.is_file()]});print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
