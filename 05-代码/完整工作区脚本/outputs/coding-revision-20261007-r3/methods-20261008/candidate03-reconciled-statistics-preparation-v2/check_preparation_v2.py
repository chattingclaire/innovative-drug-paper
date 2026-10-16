"""Preparation-only AST/help/PENDING checks. Never fabricate complete execution or read labels."""
from pathlib import Path
import ast,hashlib,json,subprocess,sys,tempfile
P=Path(__file__).resolve().parent;R=P.parents[1];S=R/'statistics';M=R/'manuscript-update-20261008';V=M/'measurement-adapter-v2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bind=lambda p:{'path':str(Path(p).resolve()),'sha256':sha(p)}
def funcs(p):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef)}
def main():
 files=[S/'candidate03_reconciled_execution_profile_v2.py',S/'prepare_candidate03_reconciled_development_bindings_v2.py',S/'run_candidate03_reconciled_complete_statistics_v2.py',S/'run_candidate03_reconciled_full_findings_v2.py',V/'assemble_manuscript_payload_r3.py',V/'independent_verify_adopted_payload.py']
 for f in files:ast.parse(f.read_text())
 runs=[]
 for f in files[1:]:
  cmd=[sys.executable,str(f),'--help'];q=subprocess.run(cmd,capture_output=True,text=True);assert q.returncode==0,(cmd,q.stderr);runs.append({'command':cmd,'exit_code':0})
 with tempfile.TemporaryDirectory(prefix='reconciled-preparation-') as td:
  t=Path(td);outputs=[t/'bindings',t/'statistics',t/'findings']
  commands=[
   [sys.executable,str(files[1]),'--full-binding',str(P/'完整reconciled03执行_PENDING.json'),'--full-binding-sha256',sha(P/'完整reconciled03执行_PENDING.json'),'--preparation-freeze-sha256','PENDING','--root-confirmed-development','--out',str(outputs[0])],
   *[[sys.executable,str(f),'--bindings',str(P/'完整reconciled03开发统计_PENDING.json'),'--bindings-sha256',sha(P/'完整reconciled03开发统计_PENDING.json'),'--out',str(o)] for f,o in zip(files[2:4],outputs[1:])],
   [sys.executable,str(files[4]),'--adoption',str(V/'采用方法_PENDING-v2.json'),'--out',str(t/'adapter-gate'),'--check-only'],
   [sys.executable,str(files[5]),'--adoption',str(V/'采用方法_PENDING-v2.json'),'--payload',str(t/'nonexistent_payload.json'),'--adapter',str(files[4]),'--check-only']]
  for cmd in commands:
   q=subprocess.run(cmd,capture_output=True,text=True);assert q.returncode==2,(cmd,q.stdout,q.stderr);runs.append({'command':cmd,'exit_code':2,'stdout':q.stdout.strip(),'stderr':q.stderr.strip()})
  assert not any(o.exists() for o in outputs)
  gate=json.loads((t/'adapter-gate/gate_report.json').read_text());assert gate['prediction_or_statistical_files_opened'] is False
 preserved={}
 specs=[('statistics_functions',S/'run_candidate03_development_complete_statistics_r3.py',files[2],{'load_methods','main','readable'}),('findings_functions',S/'run_candidate03_full_findings_r3.py',files[3],{'main'}),('adapter_functions',M/'measurement-adapter/assemble_manuscript_payload_r3.py',files[4],{'execution','assemble'}),('independent_checker_functions',M/'measurement-adapter/independent_verify_adopted_payload.py',files[5],{'full_execution_gate','main'})]
 for name,old,new,excepted in specs:
  a,b=funcs(old),funcs(new);keys=[k for k in a if k not in excepted];assert all(a[k]==b[k] for k in keys);preserved[name]=keys
 old_freeze=json.loads((R/'methods-20261008/candidate03-complete-statistics-preparation/preparation_freeze.json').read_text())
 for b in old_freeze['required_code_bindings']:assert sha(b['path'])==b['sha256']
 # Root-authored copies must contain only the disclosed version-path substitutions.
 author=(M/'emit_manuscript_after_adoption.py').read_text();expected=author.replace('measurement-adapter/assemble_manuscript_payload_r3.py','measurement-adapter-v2/assemble_manuscript_payload_r3.py').replace('完整论文局部替换稿.json','完整论文局部替换稿-v4.json').replace('snapshot-20261008-v3','snapshot-20261008-v4').replace('reviewed v3 preflight','reviewed v4 preflight')
 assert (M/'emit_manuscript_after_adoption_v2.py').read_text()==expected
 verifier=(M/'verify_authored_manuscript_r3.py').read_text();assert (M/'verify_authored_manuscript_r3_v2.py').read_text()==verifier.replace("HERE/'emit_manuscript_after_adoption.py'","HERE/'emit_manuscript_after_adoption_v2.py'")
 for name in ('emit_manuscript_after_adoption_v2.py','verify_authored_manuscript_r3_v2.py'):
  f=M/name;ast.parse(f.read_text());cmd=[sys.executable,str(f),'--help'];q=subprocess.run(cmd,capture_output=True,text=True);assert q.returncode==0;runs.append({'command':cmd,'exit_code':0})
 report={'status':'PASS_PREPARATION_ONLY_SYNTAX_HELP_PENDING_GATES','all_preparation_checks_pass':True,'script':bind(__file__),'new_code_bindings':[bind(f) for f in files],'executed_commands':runs,'all_pending_commands_exit2':True,'no_pending_statistics_or_binding_directories_created':True,'unchanged_function_AST':preserved,'old_strict197_preparation_all14_code_SHA_unchanged':True,'root_author_v2_only_expected_path_changes':True,'root_verifier_v2_only_expected_path_change':True,'root_copy_bindings':[bind(M/n) for n in ('emit_manuscript_after_adoption_v2.py','verify_authored_manuscript_r3_v2.py')],'actual_complete03_data_read':False,'original03_partial_labels_read':False,'statistics_or_models_run':False,'complete_binding_selftest_fabricated':False,'DOCX_created_or_modified':False,'actual_complete_execution_or_numerical_QA_PASS_claimed':False}
 out=P/'preparation_QA.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'QA':bind(out)},ensure_ascii=False))
if __name__=='__main__':main()
