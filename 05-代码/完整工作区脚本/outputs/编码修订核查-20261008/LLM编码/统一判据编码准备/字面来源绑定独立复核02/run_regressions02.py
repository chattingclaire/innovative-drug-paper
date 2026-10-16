"""Reproduce existing invented suites against read-only binder02; no actual corpus."""
import hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CODE=BASE/'字面来源绑定02/literal_source_binder.py';before=sha(CODE)
assert before=='c0819f3ebfe39d67c76a7504b66de253e8a04f0712523a19cfc55caa9f875753'
output=HERE/'regression_execution02.json';assert not output.exists()
root_folder=HERE/'root10_reproduction';root_folder.mkdir()
root_original=BASE/'字面来源绑定01/root_independent_review01'
design=json.loads((root_original/'design.json').read_text());design['binder_sha256']=before
(root_folder/'design.json').write_text(json.dumps(design,indent=2)+'\n')
original=(root_original/'run_checks.py').read_text()
old="CODE = HERE.parent / 'literal_source_binder.py'"
assert original.count(old)==1
adapted=original.replace(old,"CODE = Path("+repr(str(CODE))+")")
(root_folder/'run_checks.py').write_text(adapted)
new_folder=HERE/'implementation6_reproduction';new_folder.mkdir()
contract=BASE/'字面来源绑定02/implementation_contract_before02.json'
(new_folder/contract.name).write_bytes(contract.read_bytes())
original6=BASE/'字面来源绑定02/run_declared02_checks.py'
original=original6.read_text();old="CODE = HERE / 'literal_source_binder.py'";assert original.count(old)==1
(new_folder/'run_checks.py').write_text(original.replace(old,"CODE = Path("+repr(str(CODE))+")"))
suites=[('author59',[sys.executable,'-B',str(CODE),'--self-test'],HERE/'author59_reproduction.json'),
        ('root10',[sys.executable,'-B',str(root_folder/'run_checks.py')],root_folder/'actual_execution.json'),
        ('implementation6',[sys.executable,'-B',str(new_folder/'run_checks.py')],new_folder/'constructed_execution02.json')]
results=[]
for name,command,report_path in suites:
    proc=subprocess.run(command,capture_output=True,timeout=180)
    if name=='author59':
        assert not report_path.exists();report_path.write_bytes(proc.stdout)
    assert proc.returncode==0,(name,proc.returncode)
    report=json.loads(report_path.read_text())
    results.append({'suite':name,'command':command,'exit_code':proc.returncode,'stdout_sha256':hashlib.sha256(proc.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(proc.stderr).hexdigest(),'report_path':str(report_path),'report_sha256':sha(report_path),'report_summary_keys':{k:v for k,v in report.items() if k in {'passed','case_n','total','failures','unavailable_fixtures','all_passed','checks_n','unavailable'}}})
assert sha(CODE)==before
preservation=json.loads((HERE/'preservation_before02.json').read_text())['files_sha256']
assert all(sha(p)==h for p,h in preservation.items())
report={'binder_sha256':before,'binder_unchanged':True,'original01_02_unchanged':True,'actual_policy_leaves_bound':0,'model_rule_calls':0,'adaptation':'Original root10 runner only CODE path changed; original10 expected outcomes unchanged, design only binder_sha256 updated. Six runner only CODE path changed, contract bytes unchanged. Author59 executes actual read-only02 self-test CLI.','original_runner_sha256':{'root10':sha(root_original/'run_checks.py'),'implementation6':sha(original6)},'suites':results}
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report_sha256':sha(output),'suites':results},ensure_ascii=False))
