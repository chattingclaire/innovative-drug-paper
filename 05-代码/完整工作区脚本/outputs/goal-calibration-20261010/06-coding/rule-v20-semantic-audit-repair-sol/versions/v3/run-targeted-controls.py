"""Local pre-fixed development controls; never cohort/gold-standard accuracy."""
from pathlib import Path
import sys,json,hashlib,datetime,types,traceback,copy
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
NAMES=('source_packet','source_receipts','evidence','relations','dimensions')
def bind(p):
 p=Path(p).resolve();x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
def write(p,x):
 with p.open('x',encoding='utf-8')as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def load(code):
 out={}
 for n in NAMES:
  m=types.ModuleType(n);m.__file__=str(code/(n+'.py'));sys.modules[n]=m
  exec(compile((code/(n+'.py')).read_bytes(),m.__file__,'exec'),m.__dict__);out[n]=m
 return out
def main():
 code=Path(sys.argv[1]).resolve();dest=Path(sys.argv[2]).resolve();dest.mkdir(exist_ok=False)
 bindings=[bind(code/(n+'.py'))for n in NAMES]
 controls=[]
 for file,kind in [('independent20-original-controls.json','original independent 20 replay'),('scope-controls-fixed-before-execution.json','new fixed development scope controls')]:
  x=json.loads((HERE/file).read_bytes())
  for c in x['cases']:controls.append(dict(c,control_group=kind))
 write(dest/'pre-execution-bindings.json',{'code':bindings,'controls':[bind(HERE/n)for n in ['independent20-original-controls.json','scope-controls-fixed-before-execution.json']],'runner':bind(__file__),'expected_changed':False,'code_path':str(code),'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 (dest/'code-snapshot').mkdir()
 for n in NAMES:(dest/'code-snapshot'/(n+'.py')).write_bytes((code/(n+'.py')).read_bytes())
 coders=load(code);results=[]
 for c in controls:
  r={'name':c['name'],'control_group':c['control_group'],'expected':c['expected'],'synthetic_input':c['synthetic_input'],'manual_reason':c['manual_reason'],'evidence_validation_passed':False}
  try:
   u=copy.deepcopy(c['synthetic_input']);v=coders['relations'].RelationView(u);d=coders['dimensions'].judge(v)
   r.update(decisions=d,observed={k:d[k]['value']for k in ('I','F')},relation_traces=v.traces(),material_requests=v.material_requests,source_requests=v.source_requests)
   r['mismatches']=[{'dimension':k,'expected':c['expected'][k],'observed':d[k]['value']}for k in ('I','F')if c['expected'][k]!=d[k]['value']]
   coders['evidence'].validate_decisions(u,d);r['evidence_validation_passed']=True;r['passed']=not r['mismatches']
  except Exception as e:r.update(passed=False,error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
  results.append(r)
 summary={'identity':'nonhuman AI local development replay','formal_records_or_cohort_run':False,'expected_changed':False,'case_N':len(results),'pass_N':sum(r['passed']for r in results),'failure_N':sum(not r['passed']for r in results),'mismatch_N':sum(len(r.get('mismatches',[]))for r in results),'exception_N':sum('error'in r for r in results),'evidence_validation_pass_N':sum(r['evidence_validation_passed']for r in results),'failed_names':[r['name']for r in results if not r['passed']]}
 write(dest/'results.json',results);write(dest/'summary.json',summary)
 # Exact original 75 script. Only its code-directory loader changes, documented.
 mod=types.ModuleType('regression75');mod.__file__=str(HERE/'regression_tests.py');exec(compile((HERE/'regression_tests.py').read_bytes(),mod.__file__,'exec'),mod.__dict__);mod.HERE=code
 mod.run(dest/'original75')
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
