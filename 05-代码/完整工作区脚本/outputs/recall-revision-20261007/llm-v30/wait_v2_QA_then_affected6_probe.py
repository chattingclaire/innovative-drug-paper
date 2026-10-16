from pathlib import Path
import json,hashlib,subprocess,sys,time
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
TARGET='0c05b1dbd43a74943bb1deafd26b1dbb1963bef0505dda501d83cdf1bfed9955'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scalars(x):
 if isinstance(x,dict):
  for z in x.values():yield from scalars(z)
 elif isinstance(x,list):
  for z in x:yield from scalars(z)
 else:yield x
def main():
 qa=BASE/'source_object_scope_v2_independent_QA.json';full=BASE/'effective_blind_inputs_v30_v2.jsonl';packet=HERE/'material-v2/affected_blind90_v2.jsonl';prompt=HERE/'完整系统提示词-v30-候选02.txt';assert sha(full)==TARGET and sha(packet)=='1ad41252e8b9356ae389dc1ebc39c505b79a84219353ff40727bb80c7eaef0b8';deadline=time.time()+1800
 print(json.dumps({'status':'waiting_for_v2_source_QA_before_affected6_probe','no_model_calls_yet':True}),flush=True)
 while time.time()<deadline:
  if qa.exists():
   try:d=json.loads(qa.read_text());ss=list(scalars(d))
   except (ValueError,OSError):time.sleep(3);continue
   if TARGET in ss and any(isinstance(x,str) and (x.lower() in {'passed','pass','success'} or x.lower().startswith('passed_')) for x in ss):break
  time.sleep(5)
 else:raise SystemExit('v2 source QA not passed; no affected probe called')
 assert sha(full)==TARGET
 cmd=[sys.executable,str(HERE/'run_production_v30.py'),'--input',str(packet),'--expected-input-sha256',sha(packet),'--prompt',str(prompt),'--expected-n','6','--run-name','completed-material-v2-affected6-candidate02','--workers','1','--max-attempts','3'];p=subprocess.run(cmd)
 if p.returncode:raise SystemExit(p.returncode)
 raise SystemExit(subprocess.run([sys.executable,str(HERE/'verify_actual_execution_v30.py'),'--run',str(HERE/'completed-material-v2-affected6-candidate02')]).returncode)
if __name__=='__main__':main()
