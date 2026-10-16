"""Local finite replay. Frozen inputs/expectations remain unchanged."""
import copy, hashlib, importlib.util, json, runpy, subprocess, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
ROOT=P.parents[5]
AUD=ROOT/'outputs/goal-calibration-20261010/08-audits/SE-Ec-v2-independent-controls-sol'
MODULES=['evidence','source_packet','source_receipts','relations','dimensions']
SCRIPTS=['v2_fixed_controls.py','structural_controls.py','dependency_controls.py','replay_bridge_controls.py','semantic_selfcheck.py','interface_controls.py','closure_binding_controls.py','middle_scope_control.py']
def bind(p):
    p=Path(p).resolve();r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
def write(p,v):
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def imports():
    for name in MODULES:
        sp=importlib.util.spec_from_file_location(name,P/(name+'.py'));m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m)
if sys.argv[1]=='script':
    script,out,capture=sys.argv[2:];imports();captured=[];RV=sys.modules['relations'].RelationView;old=RV.__init__
    def recording(self,unit):
        captured.append(copy.deepcopy(unit));old(self,unit)
    RV.__init__=recording
    sys.argv=[script,out];runpy.run_path(str(P/script),run_name='__main__');write(capture,captured)
    sys.exit()
RUN=P/'runs'/sys.argv[1];RUN.mkdir(parents=True,exist_ok=False)
(RUN/'code-snapshot').mkdir()
for name in MODULES:(RUN/'code-snapshot'/(name+'.py')).write_bytes((P/(name+'.py')).read_bytes())
write(RUN/'code-binding.json',[bind(P/(n+'.py')) for n in MODULES])
original=[]
for script in SCRIPTS:
    out=RUN/(script[:-3]+'.json');cap=RUN/(script[:-3]+'-received-units.json')
    result=subprocess.run([sys.executable,str(P/'run_finite.py'),'script',script,str(out),str(cap)],capture_output=True,text=True)
    (RUN/(script[:-3]+'.stdout.txt')).write_text(result.stdout+'\nSTDERR\n'+result.stderr)
    if result.returncode:
        original.append({'script':script,'error_exit':result.returncode});continue
    x=json.loads(out.read_text());cs=x.get('tests',x.get('cases',[x]))
    original.append({'script':script,'case_N':len(cs),'passed_N':sum(c.get('passed',False) for c in cs),'failures':[{'name':c['name'],'expected':c.get('expected_fixed_before_v2_edit',c.get('expected_fixed_before_execution',c.get('expected'))),'actual':c['actual']} for c in cs if not c.get('passed',False)],'input_capture':bind(cap)})
imports();adapter=sys.modules['source_packet'];rels=sys.modules['relations'];dims=sys.modules['dimensions'];ev=sys.modules['evidence']
cases=[]
for suite,name in [('independent_legacy20','legacy20-controls.json'),('independent_new20','new20-fixed-before-execution.json'),('independent_owner3','owner-closure3-fixed-before-execution.json')]:
    cases.extend((suite,c) for c in json.loads((AUD/name).read_text())['cases'])
cases.extend(('geometry_new12',c) for c in json.loads((P/'geometry-controls-fixed-before-edit.json').read_text())['cases'])
if (P/'refinement-controls-fixed.json').exists():
    source=P/'refinement-controls-interface-complete.json'
    if not source.exists():source=P/'refinement-controls-fixed.json'
    cases.extend(('refinement_new6',c) for c in json.loads(source.read_text())['cases'])
if (P/'consistency-controls-fixed.json').exists():
    cases.extend(('consistency_new3',c) for c in json.loads((P/'consistency-controls-fixed.json').read_text())['cases'])
if (P/'root-position-controls-fixed.json').exists():
    cases.extend(('root_position_new5',c) for c in json.loads((P/'root-position-controls-fixed.json').read_text())['cases'])
rows=[]
for suite,c in cases:
    row={'suite':suite,'name':c['name'],'expected':c['expected'],'manual_reason':c['manual_reason'],'passed':False}
    try:
        if 'synthetic_input' in c:u=copy.deepcopy(c['synthetic_input'])
        else:u=adapter.semantic_unit(copy.deepcopy(c.get('synthetic_bundle',c.get('bound_source_bundle'))))
        row['received_unit']=copy.deepcopy(u);v=rels.RelationView(u);d=dims.judge(v);ev.validate_decisions(u,d)
        row.update(observed={k:d[k]['value'] for k in c['expected']},observed_all5={k:d[k]['value'] for k in d},decisions=d,relations=v.traces(),material_requests=v.material_requests,source_requests=v.source_requests,evidence_valid=True)
        row['mismatches']=[{'dim':k,'expected':value,'actual':d[k]['value']} for k,value in c['expected'].items() if d[k]['value']!=value]
        row['passed']=not row['mismatches'];assert u==row['received_unit']
    except Exception as ex:row['error']={'type':type(ex).__name__,'message':str(ex),'traceback':traceback.format_exc()}
    rows.append(row)
write(RUN/'independent43-and-new12.json',rows)
summary={'not_human_or_independent_formal_accuracy':True,'original156':original,'suite_summaries':{s:{'case_N':sum(r['suite']==s for r in rows),'passed_N':sum(r['passed'] for r in rows if r['suite']==s),'failures':[{'name':r['name'],'expected':r['expected'],'observed':r.get('observed'),'error':r.get('error')} for r in rows if r['suite']==s and not r['passed']]} for s in sorted(set(r['suite'] for r in rows))},'original_case_N':sum(x.get('case_N',0) for x in original),'full77_800_4481_N':0,'neutral_projection_used':False,'original_expected_unchanged':True}
write(RUN/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
