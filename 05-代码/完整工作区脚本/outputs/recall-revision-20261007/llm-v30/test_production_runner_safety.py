"""Synthetic subprocess tests only; never sends policy text or calls a model."""
import json,hashlib,subprocess,tempfile,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 with tempfile.TemporaryDirectory(prefix='synthetic-runner-test-') as td:
  d=Path(td);fake=d/'fake-codex'
  fake.write_text('''#!/usr/bin/env python3
import sys,json,time,pathlib
if '--version' in sys.argv:print('synthetic-cli-no-model');raise SystemExit(0)
args=sys.argv;out=pathlib.Path(args[args.index('--output-last-message')+1]);out.parent.mkdir(parents=True,exist_ok=True)
request=sys.stdin.read();raw=request.split('--- 本批冻结盲法输入 ---',1)[1].split('只根据上述给定材料直接返回规定JSON。',1)[0].strip();packet=json.loads(raw)
index=int(out.parents[2].name.split('-')[-1]);attempt=int(out.parent.name.split('-')[-1]);start=time.time();time.sleep(0.15)
rows=[{'id':r['id'],'labels':{'S':0,'E':0,'Ec':0,'I':0,'F':0},'dimension_reasons':{k:'Synthetic transport test only' for k in ['S','E','Ec','I','F']},'evidence':[],'fairness_subtypes':[],'innovation_subtypes':[],'safety_quality_basis':'no_quality_basis'} for r in packet['rows']]
if index==1 and attempt==1:
 out.write_text('{preserved partial failure');print(json.dumps({'type':'turn.failed','error':{'message':'synthetic transient error'}}));raise SystemExit(75)
if index==2 and attempt==1:print(json.dumps({'type':'item.completed','item':{'type':'command_execution','command':'SYNTHETIC-NO-COMMAND-WAS-EXECUTED'}}))
if index==3 and attempt==1:
 rows[0]['labels']['S']=1;rows[0]['evidence']=[{'dimension':'S','source':'unit','quote':'synthetic nonliteral quote'}]
output={'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v30','release_stage':'final_binary_labels','rows':rows,'issue_records':[]};out.write_text(json.dumps(output))
print(json.dumps({'type':'thread.started'}));print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Synthetic result'}}));print(json.dumps({'type':'turn.completed'}))
(out.parent/'synthetic_invocation_interval.json').write_text(json.dumps({'start':start,'end':time.time(),'model_argument':args[args.index('--model')+1]}))
''');fake.chmod(0o700)
  source=(HERE/'run_production_v30.py').read_text().replace("CLI=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')",f'CLI=Path({str(fake)!r})')
  script=d/'run_production_v30.py';script.write_text(source)
  for name in ['output_schema_codex_compatible.json','validate_binary_output.py']:(d/name).write_bytes((HERE/name).read_bytes())
  prompt=d/'synthetic-prompt.txt';prompt.write_text('Synthetic transport test. No real policy text. No actual model request.')
  inputs=d/'synthetic-input.json';inputs.write_text(json.dumps({'rows':[{'id':f'TEST-{i:04d}','text':'SYNTHETIC ONLY','contexts':{}} for i in range(600)]}))
  cmd=[sys.executable,str(script),'--input',str(inputs),'--prompt',str(prompt),'--expected-n','600','--run-name','synthetic-12-workers','--workers','12']
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr+p.stdout
  run=d/'synthetic-12-workers';summary=json.loads((run/'execution_summary.json').read_text());assert summary['actual_attempt_count']==27 and summary['accepted_batch_count']==24 and summary['all_attempt_tool_event_count']==1 and summary['selected_tool_event_count']==0,summary
  attempts=sorted(run.glob('batches/batch-*/attempts/attempt-*'));assert len(attempts)==27
  assert (run/'batches/batch-0001/attempts/attempt-01/raw_output.json').read_text()=='{preserved partial failure'
  assert json.loads((run/'batches/batch-0002/attempts/attempt-01/tool_event_audit.json').read_text())['tool_or_unknown_item_event_count']==1
  assert 'nonliteral_quote' in (run/'batches/batch-0003/attempts/attempt-01/validation.json').read_text()
  assert all(json.loads((run/f'batches/batch-{i:04d}/selection.json').read_text())['selected_relative_path'].endswith('attempt-02') for i in [1,2,3])
  assert len(json.loads((run/'all_predictions.json').read_text())['rows'])==600
  intervals=[json.loads(q.read_text()) for q in run.glob('batches/batch-*/attempts/attempt-*/synthetic_invocation_interval.json')]
  points=sorted([(r['start'],1) for r in intervals]+[(r['end'],-1) for r in intervals]);active=0;peak=0
  for _,delta in points:active+=delta;peak=max(peak,active)
  assert peak>=8 and peak<=12,peak
  assert all(r['model_argument']=='gpt-5.6-sol' for r in intervals)
  before={str(q.relative_to(run)):hashlib.sha256(q.read_bytes()).hexdigest() for q in run.rglob('*') if q.is_file()}
  p2=subprocess.run(cmd,capture_output=True,text=True,timeout=120);assert p2.returncode==0,p2.stderr
  after={str(q.relative_to(run)):hashlib.sha256(q.read_bytes()).hexdigest() for q in run.rglob('*') if q.is_file()};assert before==after,'resume altered immutable artifacts'
  prompt.write_text('Changed synthetic prompt')
  p3=subprocess.run(cmd+['--plan-only'],capture_output=True,text=True,timeout=120);assert p3.returncode!=0 and 'resume plan changed' in p3.stderr
  after_mismatch={str(q.relative_to(run)):hashlib.sha256(q.read_bytes()).hexdigest() for q in run.rglob('*') if q.is_file()};assert after==after_mismatch
  result={'status':'passed','test_kind':'synthetic subprocess only; no model called and no real policy data','workers_requested':12,'peak_simulated_subprocess_overlap':peak,'batches':24,'attempts':27,'transient_cli_failure_retried_preserving_first_output':True,'tool_event_rejected_and_preserved_then_same_request_retried':True,'nonliteral_quote_rejected_without_mechanical_correction':True,'first_passing_attempt_selected_without_label_or_metric_selection':True,'resume_identical_and_no_new_calls':True,'changed_prompt_rejected_before_calls':True,'gpt_56_sol_cli_argument_binding_checked':True,'production_script_sha256':hashlib.sha256((HERE/'run_production_v30.py').read_bytes()).hexdigest()}
  (HERE/'production_runner_synthetic_safety_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
