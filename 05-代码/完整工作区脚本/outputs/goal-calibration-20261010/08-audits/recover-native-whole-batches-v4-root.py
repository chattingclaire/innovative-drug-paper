"""Distinct transport recovery, fixed original batches, earliest valid whole batch.

No reference labels or semantic scores are read. Original attempts are immutable.
Recovery has its own finite three-attempt budget; it is not original attempt four.
"""
import argparse, copy, datetime, hashlib, importlib.util, json, os, shutil, subprocess, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
STOP_NEW_DISPATCH=threading.Event()
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'06-coding/native-full4481-v1-sol'
OUT=ROOT/'06-coding/native-full4481-transport-recovery-v2-sol'
CLI=ROOT/'06-coding/isolated-codex-cli-0.162.1-root/node_modules/.bin/codex'
VALIDATOR=ROOT/'06-coding/full4481-native-execution-adapter-sol/root-validator-amendment-01/validate-structured-batch-production-binding-v2.py'
GUARD=ROOT/'08-audits/native-recovery-v2-preflight-sol/strict_reception_guard.py'
CAPACITY=ROOT/'08-audits/native-recovery-v2-preflight-sol/ROOT-transport-capacity3-sidecar.json'
SCOPE='transport recovery of previously technically failed original full4481 batches; fixed conceptual manual, prompt, packets and original batch membership; not a new independent validation or stability repeat'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_bytes())
def bind(p):
 p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def exact(b):
 assert bind(b['path'])=={k:b[k] for k in ('path','bytes','sha256')},'Frozen input changed: '+b['path']
def setup():
 if OUT.exists():return load(OUT/'manifest.json')
 batches=[b for b in sorted(OLD.glob('batch-*')) if not (b/'root-selection.json').exists()]
 assert len(batches)==207
 OUT.mkdir();shutil.copyfile(VALIDATOR,OUT/'strict-validator.py')
 instructions=(OLD/'actor-instructions.txt').read_text()
 instructions=instructions.replace('全量4481条政策材料生产编码中的','原全量4481条材料中技术失败批次的独立恢复轮')
 instructions+='\n本轮是另存的运输恢复轮，不是旧轮第4次attempt，也不把旧失败或逐条35补跑写成原完整整批结果。本轮手册、执行提示、各packet及每个既定batch成员和顺序原字节不变；run_id、scope、assignment/output/routing路径依本恢复轮绑定。每次是fresh ephemeral CLI上下文；runtime task-name由ROOT外部元数据提供。仅处理自己的完整batch，完整读本轮assignment/手册/prompt/actor instructions/输出schema及各packet，不读任何旧或同伴结果。0/1必须至少一条当前packet逐字证据；null如实保留。每次仅一次first原件，不自行再答或补写first。运行并发先3批运输验证，通过后按ROOT已有容量13授权扩展；它只改变调度容量。不得把程序hash/load写成阅读。保存first后，用独占创建写自身report.txt与seal.json；seal至少包括run_id,batch_id,first_binding,report_binding,actual_input_bindings，并绑定真实读过的文件，不伪造记录。schema/validator仅ROOT核收，禁止自己用反馈改首答。\n'
 (OUT/'actor-instructions.txt').write_text(instructions)
 save(OUT/'transport-amendment.json',{'created_at_utc':now(),'type':'separate_nonsemantic_transport_recovery','old_campaign':str(OLD),'old_failed_batch_N':207,'old_failed_record_N':2349,'new_round_max_attempts_per_batch':3,'original_attempts_unchanged':True,'reuse_earliest_original_valid_batch':True,'fixed_original_batch_membership':True,'conceptual_manual_prompt_packets_unchanged':True,'old_nonexecuted_errors_do_not_count_as_semantic_repeats':True,'initial_concurrency':3,'expanded_concurrency':13,'expanded_basis':str(ROOT/'06-coding/full4481-cli-fixed-batch-scheduler-v3-capacity13-root/CLI-concurrency-amendment-13.json'),'original_actual_CLI_launcher_also_same_version':True,'backend_failure_cause_not_identified':True,'requested_model':'gpt-6.1-sol','requested_reasoning_effort':'ultra','semantic_retries_prohibited':True,'null_not_zero':True,'formal_validation_complete':False})
 routes=[]
 for old in batches:
  for a in range(1,4):
   slot=OUT/old.name/f'attempt-{a:04d}';slot.mkdir(parents=True)
   name=f'native_recoveryv2_{old.name.replace("-", "")}_a{a:02d}'
   routes.append({'attempt_number':a,'batch_id':old.name,'runtime_task_name':name,'expected_canonical_runtime_task_name':'/root/'+name,'output_directory':str(slot),'first_path':str(slot/'first.json'),'report_path':str(slot/'report.txt'),'seal_path':str(slot/'seal.json')})
 routing=load(OLD/'attempt-output-routing.json');routing['routes']=routes;routing['coding_actors_must_be_ROOT_fresh_fork_none']=False;routing['coding_actors_are_fresh_ephemeral_CLI']=True
 save(OUT/'attempt-output-routing.json',routing)
 prepared=[]
 for old in batches:
  directory=OUT/old.name;assignment=load(old/'assignment.json');schema=load(old/'output.schema.json')
  schema['properties']['run_id']['const']=OUT.name;schema['properties']['scope']['const']=SCOPE
  save(directory/'output.schema.json',schema)
  contract=load(old/'output-validation-contract.json');contract['recovery_round']=OUT.name;contract['original_contract_binding']=bind(old/'output-validation-contract.json');save(directory/'output-validation-contract.json',contract)
  assignment.update(run_id=OUT.name,scope=SCOPE,output_directory=str(directory),state='frozen_for_transport_recovery',actor_instructions=bind(OUT/'actor-instructions.txt'),output_schema=bind(directory/'output.schema.json'),output_validation_contract=bind(directory/'output-validation-contract.json'),strict_technical_validator=bind(OUT/'strict-validator.py'),attempt_output_routing=bind(OUT/'attempt-output-routing.json'),campaign_scope_metadata_binding=bind(OUT/'transport-amendment.json'))
  # Do not bind original-run scope text as this new round's identity metadata.
  assignment['original_assignment_binding']=bind(old/'assignment.json')
  save(directory/'assignment.json',assignment)
  prepared.append({'batch_id':old.name,'source_ids':assignment['source_ids'],'assignment':bind(directory/'assignment.json'),'old_assignment':bind(old/'assignment.json'),'packet_bindings_unchanged':assignment['packets']==load(old/'assignment.json')['packets']})
 ids=[s for b in prepared for s in b['source_ids']];assert len(ids)==2349 and len(set(ids))==2349
 manifest={'created_at_utc':now(),'run_id':OUT.name,'source_N':len(ids),'batch_N':len(prepared),'batches':prepared,'runner':bind(__file__),'cli_launcher':bind(CLI),'validator':bind(OUT/'strict-validator.py'),'instructions':bind(OUT/'actor-instructions.txt'),'transport_amendment':bind(OUT/'transport-amendment.json'),'max_total_technical_attempts':3,'technical_states_only':True,'reference_labels_read':False,'full_corpus_complete':False,'formal_validation_complete':False}
 save(OUT/'manifest.json',manifest);return manifest
def prompt(assignment,route):
 return f'''你是独立的原生政策文本编码执行者。本次 fresh ephemeral CLI context 对应 runtime task-name：{route['runtime_task_name']}，只处理本批完整assignment一次。先完整阅读 {assignment}，再按绑定阅读手册、execution prompt、actor instructions、output schema、合同和全部packet。遵守共同手册的有限语境范围和原样五维标准。

实际呈现文件时按不超过6500 Unicode字符的连续范围读取，每次明确文件路径/start/end，并保证工具 max_output_tokens 足够；若出现截断，重读缺失范围，不能声称已读。必须在first.read_manifest记录真实工具呈现范围和事件。程序load/hash不是阅读。先读完手册与提示，再按既定顺序完整读packet；真实所需图页/资产按assignment绑定打开和限定范围读取。不得读参照、预测、指标、旧尝试、其他batch/actor/历史/用户配置，不委派。

只向自己slot提交一次：{route['first_path']}；用独占创建保存完整原字节，records顺序/身份、绑定、五维value/reason/evidence及read_manifest严格符合assignment.output_schema。每个0/1至少一个已读packet字符串内的逐字quote与真实JSON pointer，合法null可空证据并说明真实缺项。不要把概括或未来机会当作已经发生效果。

遵守共同协议与ROOT冻结sidecar，实际并发始终不超过3；v2准备中未执行的13容量计划已经撤回。first保存后只写自己的report和seal：{route['report_path']}、{route['seal_path']}。不写canonical、不运行validator、不根据反馈改首答、不自己重试。seal的run_id/batch_id必须与assignment相同，template_only=false、actual_completion_claimed=true；actual_input_bindings须为非空真实已读且绑定的文件列表，并绑定实际first/report。不得把空模板或未读文件当成收据；不宣称provider wire或已独立核验服务model。结束简短报告完成或真实失败。'''
def attempt(directory,number,manifest):
 slot=directory/f'attempt-{number:04d}';assert not (slot/'dispatch-start.json').exists()
 routes=load(OUT/'attempt-output-routing.json')['routes'];route=next(r for r in routes if r['batch_id']==directory.name and r['attempt_number']==number)
 assignment=directory/'assignment.json';text=prompt(assignment,route);(slot/'dispatch-prompt.txt').write_text(text)
 cmd=[str(CLI),'exec','--ignore-user-config','--skip-git-repo-check','--ephemeral','--json','--color','never','-C',str(slot),'--model','gpt-6.1-sol','-c','model_reasoning_effort="ultra"','-c','approval_policy="never"','--sandbox','workspace-write','-c','features.multi_agent=false','-c','features.memories=false','-c','web_search="disabled"','-c','project_doc_max_bytes=0','--output-last-message',str(slot/'final-message.txt'),'-']
 save(slot/'dispatch-start.json',{'at_utc':now(),'argv':cmd,'requested_model':'gpt-6.1-sol','requested_reasoning_effort':'ultra','prompt':bind(slot/'dispatch-prompt.txt'),'assignment':bind(assignment),'run_id':OUT.name,'batch_id':directory.name,'attempt':number,'old_attempt_budget_not_modified':True})
 with (slot/'cli-events.jsonl').open('xb') as stdout,(slot/'stderr.txt').open('xb') as stderr:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,cwd=slot,start_new_session=True)
  try:proc.communicate(text.encode(),timeout=2400);timedout=False
  except subprocess.TimeoutExpired:
   import signal
   os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=20)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
   timedout=True
 save(slot/'process-completion.json',{'at_utc':now(),'pid':proc.pid,'returncode':proc.returncode,'timed_out':timedout,'events':bind(slot/'cli-events.jsonl'),'stderr':bind(slot/'stderr.txt'),'first_exists':(slot/'first.json').exists(),'actual_process_terminal':True})
 for line in (slot/'cli-events.jsonl').read_text().splitlines():
  try:event=json.loads(line)
  except ValueError:continue
  if event.get('type') in ('error','turn.failed') and 'not supported when using Codex with a ChatGPT account' in str(event):STOP_NEW_DISPATCH.set()
 receipt={'at_utc':now(),'run_id':OUT.name,'batch_id':directory.name,'attempt':number,'assignment':bind(assignment),'validator':manifest['validator'],'semantic_correctness_checked':False,'reference_compared':False}
 try:
  spec=importlib.util.spec_from_file_location('native_strict_validator_'+directory.name.replace('-','_'),OUT/'strict-validator.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
  result=v.verify(assignment,slot/'first.json')
  first=v.load_strict(slot/'first.json')
  for rec in first['records']:
   for d,dec in rec['dimensions'].items():
    assert dec['value'] is None or any('pointer' in e for e in dec['evidence']),'0/1 lacks packet evidence'
  seal=load(slot/'seal.json');assert seal['first_binding']==bind(slot/'first.json') and seal['report_binding']==bind(slot/'report.txt'),'Actor seal binding mismatch'
  for b in seal['actual_input_bindings']:exact(b)
  assert proc.returncode==0 and not timedout,'CLI not cleanly terminal'
  receipt.update(state='technical_valid_whole_batch',validation=result,first=bind(slot/'first.json'),actor_seal=bind(slot/'seal.json'))
 except Exception as e:receipt.update(state='technical_invalid_whole_batch',error={'type':type(e).__name__,'message':str(e)})
 return receive_completed(directory,number,manifest)
def receive_completed(directory,number,manifest):
 slot=directory/f'attempt-{number:04d}';rp=slot/'root-reception-v3.json'
 if rp.exists():return load(rp)
 receipt={'at_utc':now(),'run_id':OUT.name,'batch_id':directory.name,'attempt':number,'assignment':bind(directory/'assignment.json'),'guard':bind(GUARD),'capacity_sidecar':bind(CAPACITY),'reference_compared':False,'first_or_labels_modified':False}
 try:
  spec=importlib.util.spec_from_file_location('strict_supplement_'+directory.name.replace('-','_'),GUARD);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
  result=guard.verify(OUT/'manifest.json',directory/'assignment.json',slot/'first.json')
  receipt.update(state='technical_valid_whole_batch',validation=result,first=result['first'],actor_seal=result['actor_seal'])
 except Exception as e:receipt.update(state='technical_invalid_whole_batch',error={'type':type(e).__name__,'message':str(e)})
 save(rp,receipt);return receipt
def run_batch(item,manifest):
 exact(item['assignment']);directory=Path(item['assignment']['path']).parent
 if (directory/'root-selection-v3.json').exists():return load(directory/'root-selection-v3.json')
 for number in range(1,4):
  if STOP_NEW_DISPATCH.is_set():return {'batch_id':directory.name,'state':'not_dispatched_or_retry_stopped_global_model_account_error'}
  rp=directory/f'attempt-{number:04d}/root-reception-v3.json'
  if rp.exists():r=load(rp)
  elif (directory/f'attempt-{number:04d}/process-completion.json').exists():r=receive_completed(directory,number,manifest)
  else:r=attempt(directory,number,manifest)
  if r['state']=='technical_valid_whole_batch':
   selection={'artifact_type':'earliest_technically_valid_whole_batch_transport_recovery','created_at_utc':now(),'batch_id':directory.name,'run_id':OUT.name,'attempt':number,'assignment':item['assignment'],'first':r['first'],'reception':bind(rp),'scope':SCOPE,'original_valid_results_never_overwritten':True,'semantic_scores_not_selection_criteria':True}
   save(directory/'root-selection-v3.json',selection);print(json.dumps({'batch':directory.name,'state':'accepted','record_N':len(item['source_ids']),'attempt':number}),flush=True);return selection
 print(json.dumps({'batch':directory.name,'state':'exhausted','record_N':len(item['source_ids'])}),flush=True);return {'batch_id':directory.name,'state':'exhausted'}
def main():
 profile=load(OUT/'ROOT-controller-v4-binding.json')
 for name in ('controller','guard','capacity_sidecar','prepared_manifest'):exact(profile[name])
 assert profile['actual_concurrency_cap']==3
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['prepare','pilot','remaining'],required=True);p.add_argument('--concurrency',type=int,default=3);args=p.parse_args();manifest=setup()
 for k in ('runner','cli_launcher','validator','instructions','transport_amendment'):exact(manifest[k])
 if args.mode=='prepare':print(json.dumps({'batch_N':manifest['batch_N'],'source_N':manifest['source_N']}));return
 batches=manifest['batches'][:3] if args.mode=='pilot' else manifest['batches']
 if args.mode=='remaining':
  assert all((Path(b['assignment']['path']).parent/'root-selection-v3.json').exists() for b in manifest['batches'][:3]),'All three intact pilot batches must first pass'
 assert 1<=args.concurrency<=3, 'Frozen ROOT sidecar permanently caps actual capacity at three'
 run=OUT/'execution-runs'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
 save(run/'start.json',{'controller':bind(__file__),'strict_guard':bind(GUARD),'capacity3_sidecar':bind(CAPACITY),'at_utc':now(),'mode':args.mode,'concurrency':args.concurrency,'manifest':bind(OUT/'manifest.json'),'batch_ids':[b['batch_id'] for b in batches]})
 results=[]
 with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
  futures={pool.submit(run_batch,b,manifest):b for b in batches}
  for f in as_completed(futures):
   try:results.append(f.result())
   except Exception as e:results.append({'batch_id':futures[f]['batch_id'],'state':'controller_error','error':repr(e)});print(json.dumps(results[-1]),flush=True)
 save(run/'result.json',{'at_utc':now(),'results':results,'all_terminal':True,'accepted_N':sum('first'in r for r in results),'exhausted_or_error_N':sum('first'not in r for r in results)})
 print(json.dumps({'result':str(run/'result.json'),'accepted_N':sum('first'in r for r in results),'other_N':sum('first'not in r for r in results)}),flush=True)
if __name__=='__main__':main()
