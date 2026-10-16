"""Finite exposed development controls; no corpus run or expected-value feature."""
import argparse,copy,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;G=P.parents[3]
def bind(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def cj(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def load(p):return json.loads(Path(p).read_bytes())
def write(p,v):
 with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
a=argparse.ArgumentParser();a.add_argument('--suite',choices=['235'],required=True);a.add_argument('--out',required=True);a.add_argument('--numbering-stage',action='store_true');args=a.parse_args()
O=P/args.out;O.mkdir(exist_ok=False);snap=O/'code-snapshot';snap.mkdir();modules={}
for n in ['evidence','source_packet','source_receipts','relations','dimensions']:
 q=snap/(n+'.py');q.write_bytes(((P/'numbering-before-semantic-code-snapshot' if args.numbering_stage else P)/(n+'.py')).read_bytes());spec=importlib.util.spec_from_file_location(n,q);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);modules[n]=m
path=P.parent/'joint-v2-geometry01/joint-parent235-root-replay01/controls-fixed-before-joint-execution.json';cs=load(path)['cases'];cases=[dict(name=c['name'],suite=c['suite'],input=c['semantic_input'],expected=c['expected'],operations=c.get('post_view_operations',[]),origin_binding=bind(path),origin_index=i) for i,c in enumerate(cs)]
assert len(cases)==int(args.suite)
write(O/'pre-execution-seal.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'modules':[bind(snap/(n+'.py')) for n in modules],'fixed_controls':bind(path),'runner':bind(__file__),'case_N':len(cases),'expected_not_given_to_classifier':True,'expectations_unchanged':True,'no_reference_original_files_read_by_classifier':True})
read_guard={'active':False};denied=[]
def audit(event,args):
 if read_guard['active'] and event=='open':
  denied.append(str(args[0]));raise RuntimeError('Classifier attempted filesystem access; source_ref paths are provenance only.')
sys.addaudithook(audit)
results=[]
for c in cases:
 unit=copy.deepcopy(c['input']);row={k:copy.deepcopy(v) for k,v in c.items() if k!='input'};row['semantic_input']=copy.deepcopy(unit)
 try:
  read_guard['active']=True
  view=modules['relations'].RelationView(unit)
  for op in c['operations']:view._add(op['kind'],[view._quote(view.by_id[op['context_id']],op['usage'])],op['reason'],**op['details'])
  decisions=modules['dimensions'].judge(view);modules['evidence'].validate_decisions(unit,decisions)
  read_guard['active']=False
  assert cj(unit)==cj(c['input'])
  observed={d:decisions[d]['value'] for d in c['expected']};row.update(observed=observed,decisions=decisions,traces=view.traces(),material_requests=view.material_requests,source_requests=view.source_requests,structural_address_issues=view.structural_address_issues,evidence_validation_passed=True)
  row['mismatches']=[dict(dimension=d,expected=v,actual=observed[d]) for d,v in c['expected'].items() if v!=observed[d]];row['passed']=not row['mismatches']
 except Exception as e:
  read_guard['active']=False;row.update(passed=False,error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()},mismatches=[],evidence_validation_passed=False)
 results.append(row)
summary={'identity':'nonhuman finite development replay; not formal accuracy or a gold standard','case_N':len(cases),'matched':sum(x['passed'] for x in results),'exceptions':sum('error'in x for x in results),'evidence_validated':sum(x['evidence_validation_passed'] for x in results),'failed':[{'name':x['name'],'mismatches':x['mismatches'],'error':x.get('error')} for x in results if not x['passed']],'filesystem_access_attempts_during_classification':denied,'new_cohort_77_800_4481_runs':0,'main_LLM_labels_read':False,'new_actual_source_ids':[],'original_expected_unchanged':True}
write(O/'results.json',results);write(O/'summary.json',summary);write(O/'output-seal.json',{'output_members':[bind(x) for x in sorted(O.rglob('*')) if x.is_file()],'self_excluded':True})
print(json.dumps(summary,ensure_ascii=False,indent=2))
