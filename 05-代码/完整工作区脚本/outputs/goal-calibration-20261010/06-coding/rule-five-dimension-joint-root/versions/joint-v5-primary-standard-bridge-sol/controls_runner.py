"""Six fixed source-only standard-bridge controls. No original-file resolution or corpus."""
import argparse, copy, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
sys.dont_write_bytecode = True
P = Path(__file__).resolve().parent
def bind(p):
    p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--baseline',action='store_true');args=parser.parse_args()
out=P/args.out;out.mkdir(exist_ok=False);snap=out/'code-snapshot';snap.mkdir();modules={}
source=P/'baseline-code-snapshot' if args.baseline else P
for n in ('evidence','source_packet','source_receipts','relations','dimensions'):
    path=snap/(n+'.py');path.write_bytes((source/(n+'.py')).read_bytes())
    spec=importlib.util.spec_from_file_location(n,path);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);modules[n]=m
fixed=P/'controls6-fixed-before-edit.json';cases=json.loads(fixed.read_bytes())['cases'];assert len(cases)==6
write(out/'pre-execution-seal.json',dict(at_utc=datetime.now(timezone.utc).isoformat(),modules=[bind(snap/(n+'.py'))for n in modules],controls=bind(fixed),runner=bind(__file__),expected_not_given_to_classifier=True,case_N=6))
active=False;attempts=[]
def audit(event,a):
    if active and event=='open':attempts.append(str(a[0]));raise RuntimeError('Classifier filesystem access blocked; provenance paths do not supply missing material.')
sys.addaudithook(audit);results=[]
for i,c in enumerate(cases):
    row=dict(index=i,name=c['name'],semantic_input=copy.deepcopy(c['synthetic_input']),expected=copy.deepcopy(c['expected']))
    try:
        active=True;view=modules['relations'].RelationView(copy.deepcopy(c['synthetic_input']));decisions=modules['dimensions'].judge(view);modules['evidence'].validate_decisions(c['synthetic_input'],decisions);active=False
        row.update(observed={d:decisions[d]['value']for d in c['expected']},decisions=decisions,traces=view.traces(),source_requests=view.source_requests,material_requests=view.material_requests,structural_address_issues=getattr(view,'structural_address_issues',[]),evidence_validated=True)
        row['mismatches']=[dict(dimension=d,expected=v,actual=row['observed'][d])for d,v in c['expected'].items()if v!=row['observed'][d]];row['passed']=not row['mismatches']
    except Exception as e:
        active=False;row.update(error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()),evidence_validated=False,passed=False)
    results.append(row)
summary=dict(identity='nonhuman six finite structure development controls, not formal accuracy',case_N=6,matched=sum(r['passed']for r in results),exceptions=sum('error'in r for r in results),evidence_validated=sum(r['evidence_validated']for r in results),failed=[dict(index=r['index'],name=r['name'],mismatches=r.get('mismatches'),error=r.get('error'))for r in results if not r['passed']],filesystem_access_attempts=attempts,new_hidden_v5_controls_read=False,new_actual_source_ids=[],cohort_run=False)
write(out/'results.json',results);write(out/'summary.json',summary);write(out/'output-seal.json',dict(output_members=[bind(x)for x in sorted(out.rglob('*'))if x.is_file()],self_excluded=True));print(json.dumps(summary,ensure_ascii=False))
