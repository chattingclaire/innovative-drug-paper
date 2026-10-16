"""Prepare three new actual calls, execute only when explicitly invoked with --execute."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args();sample=HERE/'stability-v30/same_batch_36.jsonl';plan=json.loads((HERE/'stability-v30/sample_and_execution_plan.json').read_text());assert sha(sample)==plan['sample_sha256'];configs=[('same-01',HERE/'完整系统提示词-v30-候选03.txt'),('same-02',HERE/'完整系统提示词-v30-候选03.txt'),('dimension-order-01',HERE/'stability-v30/完整提示词-仅维度执行顺序扰动.txt')]
 cmds=[]
 for name,prompt in configs:cmds.append((name,[sys.executable,str(HERE/'run_production_v30.py'),'--input',str(sample),'--expected-input-sha256',sha(sample),'--prompt',str(prompt),'--expected-n','36','--batch-size','36','--workers','1','--max-attempts','3','--run-name',f'stability-v30-{name}']))
 if not a.execute:print(json.dumps({'status':'prepared_no_model_calls','calls':3,'same_36_single_batch':True,'configs':[name for name,_ in cmds]},ensure_ascii=False));return
 def one(config):
  name,cmd=config;p=subprocess.run(cmd,capture_output=True,text=True);(HERE/'stability-v30'/f'{name}-launcher.log').write_text(p.stdout);(HERE/'stability-v30'/f'{name}-launcher.stderr.txt').write_text(p.stderr)
  if p.returncode:raise RuntimeError(f'stability call {name} failed; all raw artifacts preserved')
  v=subprocess.run([sys.executable,str(HERE/'verify_actual_execution_v30.py'),'--run',str(HERE/f'stability-v30-{name}')],capture_output=True,text=True);(HERE/'stability-v30'/f'{name}-verification.log').write_text(v.stdout+v.stderr);assert v.returncode==0,v.stdout+v.stderr;print(json.dumps({'stability_call':name,'status':'actual_execution_verified'}),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for f in concurrent.futures.as_completed([pool.submit(one,c) for c in cmds]):f.result()
 p=subprocess.run([sys.executable,str(HERE/'compare_stability_v30.py')]);raise SystemExit(p.returncode)
if __name__=='__main__':main()
