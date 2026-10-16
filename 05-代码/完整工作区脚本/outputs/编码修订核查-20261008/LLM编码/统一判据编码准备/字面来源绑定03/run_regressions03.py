"""Separate mechanical reproduction of prior synthetic suites against binder03."""
import hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;CODE=HERE/'literal_source_binder.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
initial=sha(CODE);output=HERE/'mechanical_regressions03.json';assert not output.exists()
old24=BASE/'字面来源绑定独立复核02';f24=HERE/'independent24_regression';f24.mkdir()
d24=json.loads((old24/'design_independent02.json').read_text());d24['binder']={'path':str(CODE),'sha256':initial}
(f24/'design_independent02.json').write_text(json.dumps(d24,ensure_ascii=False,indent=2)+'\n')
for name in ['run_independent02.py','preservation_before02.json']:(f24/name).write_bytes((old24/name).read_bytes())
old10=BASE/'字面来源绑定01/root_independent_review01';f10=HERE/'root10_regression';f10.mkdir()
d10=json.loads((old10/'design.json').read_text());d10['binder_sha256']=initial
(f10/'design.json').write_text(json.dumps(d10,indent=2)+'\n')
s=(old10/'run_checks.py').read_text();old="CODE = HERE.parent / 'literal_source_binder.py'";assert s.count(old)==1
(f10/'run_checks.py').write_text(s.replace(old,'CODE = Path('+repr(str(CODE))+')'))
f6=HERE/'implementation6_regression';f6.mkdir()
(f6/'implementation_contract_before02.json').write_bytes((BASE/'字面来源绑定02/implementation_contract_before02.json').read_bytes())
s=(BASE/'字面来源绑定02/run_declared02_checks.py').read_text();old="CODE = HERE / 'literal_source_binder.py'";assert s.count(old)==1
(f6/'run_checks.py').write_text(s.replace(old,'CODE = Path('+repr(str(CODE))+')'))
suites=[('independent24',24,[sys.executable,'-B',str(f24/'run_independent02.py')],f24/'actual_independent02.json'),
 ('author59',59,[sys.executable,'-B',str(CODE),'--self-test'],HERE/'author59_regression.json'),
 ('root10',10,[sys.executable,'-B',str(f10/'run_checks.py')],f10/'actual_execution.json'),
 ('implementation6',6,[sys.executable,'-B',str(f6/'run_checks.py')],f6/'constructed_execution02.json')]
results=[]
for name,n,command,report_path in suites:
 proc=subprocess.run(command,capture_output=True,timeout=180)
 if name=='author59':assert not report_path.exists();report_path.write_bytes(proc.stdout)
 assert proc.returncode==0,(name,proc.returncode)
 d=json.loads(report_path.read_text());assert d['passed'],name
 assert len(d['checks'])==n
 results.append({'suite':name,'check_n':n,'all_passed':True,'command':command,'exit_code':proc.returncode,'report_path':str(report_path),'report_sha256':sha(report_path),'stdout_sha256':hashlib.sha256(proc.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(proc.stderr).hexdigest()})
assert sha(CODE)==initial
preservation=json.loads((HERE/'preservation_before03.json').read_text())['files_sha256'];assert all(sha(p)==h for p,h in preservation.items())
report={'scope':'Prior synthetic mechanical regressions only; not independent03 verification or empirical validity.','code_sha256_before':initial,'code_sha256_after':sha(CODE),'code_unchanged':True,'previous_file_n':len(preservation),'previous_files_unchanged':True,'actual_policy_leaf_n':0,'model_rule_calls':0,
 'adaptations':{'independent24':'Original runner and prior38 preservation receipt bytes identical; copied design changes only binder path/SHA. Original expected24 unchanged.','author59':'Original test code bytes identical; actual03 isolated self-test CLI.','root10':'Copied original expected10, binder SHA updated; only runner CODE path changed.','implementation6':'Original contract bytes identical; only runner CODE path changed.'},'suites':results,'passed':True}
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report_sha256':sha(output),'code_sha256':initial,'passed':True,'suites':[{'suite':r['suite'],'check_n':r['check_n'],'report_sha256':r['report_sha256']} for r in results]},ensure_ascii=False))
