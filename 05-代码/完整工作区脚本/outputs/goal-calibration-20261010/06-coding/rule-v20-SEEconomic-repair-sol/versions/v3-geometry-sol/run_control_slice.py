"""Meaningful local slice, preserving full inputs and code at each execution."""
import copy,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
OUT=P/'runs'/sys.argv[1];OUT.mkdir(exist_ok=False)
mods=['evidence','source_packet','source_receipts','relations','dimensions']
(OUT/'code-snapshot').mkdir()
bindings=[]
for n in mods:
    p=P/(n+'.py');raw=p.read_bytes();(OUT/'code-snapshot'/(n+'.py')).write_bytes(raw);bindings.append({'file':n+'.py','sha256':hashlib.sha256(raw).hexdigest()})
    sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m)
cs=json.loads((P/sys.argv[2]).read_text())['cases'];results=[]
for c in cs:
    r={'name':c['name'],'expected':c['expected']}
    try:
        u=sys.modules['source_packet'].semantic_unit(copy.deepcopy(c['synthetic_bundle']));r['received_unit']=copy.deepcopy(u)
        v=sys.modules['relations'].RelationView(u);d=sys.modules['dimensions'].judge(v);sys.modules['evidence'].validate_decisions(u,d)
        r.update(observed={k:d[k]['value'] for k in c['expected']},decisions=d,relations=v.traces(),material_requests=v.material_requests,evidence_valid=True);r['passed']=r['expected']==r['observed']
    except Exception as ex:r.update(error={'type':type(ex).__name__,'message':str(ex),'traceback':traceback.format_exc()},passed=False)
    results.append(r)
with (OUT/'slice-results.json').open('x',encoding='utf8') as f:json.dump({'code_binding':bindings,'input_file':sys.argv[2],'results':results},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps([{'name':r['name'],'expected':r['expected'],'observed':r.get('observed'),'passed':r['passed']} for r in results],ensure_ascii=False))
