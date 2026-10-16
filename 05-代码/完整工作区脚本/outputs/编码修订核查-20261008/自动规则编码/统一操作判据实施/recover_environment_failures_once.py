"""Recover only the four recorded environment failures, without code changes."""
from pathlib import Path
import sys,json,hashlib,copy,time,traceback
sys.dont_write_bytecode=True
base=Path(__file__).resolve().parent
sys.path.insert(0,str(base/'runtime'))
from policy_coding_v27 import code_unit
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
code_before={p.name:sha(p) for p in (base/'runtime').iterdir() if p.is_file()}
input_before=sha(base/'development_inputs15.jsonl');first_before=sha(base/'development_outputs15.jsonl')
first=[json.loads(l) for l in (base/'development_outputs15.jsonl').read_text().splitlines()]
failed={r['case_id'] for r in first if r['status']=='failed'}
assert len(failed)==4 and all(r.get('error_type')=='ModuleNotFoundError' and r.get('error')=="No module named 'pypdf'" for r in first if r['case_id'] in failed)
inputs=[json.loads(l) for l in (base/'development_inputs15.jsonl').read_text().splitlines()]
start=time.time();recovered=[]
with (base/'environment_recovery_outputs4.jsonl').open('x') as out:
 for r in inputs:
  if r['case_id'] not in failed:continue
  try:result=code_unit(copy.deepcopy(r['input']));p={'case_id':r['case_id'],'id':r['id'],'status':'completed','result':result}
  except Exception as e:p={'case_id':r['case_id'],'id':r['id'],'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()}
  recovered.append(p);out.write(json.dumps(p,ensure_ascii=False)+'\n');out.flush()
lookup={r['case_id']:r for r in recovered}
combined=[lookup.get(r['case_id'],r) for r in first]
(base/'development_outputs15_with_environment_recovery.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in combined)+'\n')
code_after={p.name:sha(p) for p in (base/'runtime').iterdir() if p.is_file()}
report={'purpose':'same finite development check: one environment recovery for four failures only','python_executable':sys.executable,'python_version':sys.version,'recovery_invocations':4,'recovery_pass_count':1,'semantic_code_unchanged':code_before==code_after,'runtime_files_sha256_before':code_before,'runtime_files_sha256_after':code_after,'input_sha256_before':input_before,'input_sha256_after':sha(base/'development_inputs15.jsonl'),'first_output_sha256_before':first_before,'first_output_sha256_after':sha(base/'development_outputs15.jsonl'),'first_11_successful_outputs_unchanged':all(lookup.get(r['case_id']) is None for r in first if r['status']=='completed'),'recovery_completed':sum(r['status']=='completed' for r in recovered),'recovery_failed':sum(r['status']=='failed' for r in recovered),'combined_completed':sum(r['status']=='completed' for r in combined),'elapsed_seconds':time.time()-start,'model_calls':0,'full_run':False,'semantic_validation_pass_claimed':False}
assert report['semantic_code_unchanged'] and report['input_sha256_before']==report['input_sha256_after'] and report['first_output_sha256_before']==report['first_output_sha256_after']
(base/'environment_recovery_execution_record.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print({k:v for k,v in report.items() if 'sha256' not in k})
for r in recovered:print(r['case_id'],r['id'],r['status'],r.get('result',{}).get('labels'),r.get('error',''))
