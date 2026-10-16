"""Audit repair: rerun a full batch with web search explicitly disabled."""
import argparse,hashlib,json,shutil,subprocess,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CLI=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex');PROMPT=ROOT/'outputs/llm-v29-method-audit-20261005/完整系统提示词-v29.txt';SCHEMA=HERE/'output_schema_codex_compatible.json';VAL=ROOT/'outputs/llm-v29-method-audit-20261005/validate_binary_output.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tool_events(path):
 found=[]
 for line in path.read_text().splitlines():
  try:event=json.loads(line)
  except ValueError:continue
  text=json.dumps(event,ensure_ascii=False).lower()
  if any(term in text for term in ('web_search','web_fetch','tool_call','function_call')):found.append(event)
 return found
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--batch',type=int,required=True);ap.add_argument('--attempt',default='no-retrieval-rerun-01');ap.add_argument('--supplement');ap.add_argument('--supplement-id');a=ap.parse_args();batch=HERE/'production-25-v29/batches'/f'batch-{a.batch:04d}';history=batch/'history-before-no-retrieval'
 if not history.exists():
  history.mkdir()
  for item in list(batch.iterdir()):
   if item.name in {'history-before-no-retrieval',a.attempt}:continue
   if item.is_dir():shutil.copytree(item,history/item.name)
   else:shutil.copy2(item,history/item.name)
 dest=batch/a.attempt;dest.mkdir();packet=json.loads((batch/'input.json').read_text())
 if a.supplement:
  sup=json.loads(Path(a.supplement).read_text());sup['source_sha256']=sha(Path(sup['source_path']))
  if a.supplement_id: sup['id']=a.supplement_id
  target=next(row for row in packet['rows'] if row['id']==sup['id']);target['contexts']['resolved_material_supplement']=sup
 inp=dest/'input.json';inp.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n');request=PROMPT.read_text()+'\n\n--- 审计后禁止任何外部检索的整批独立重跑 ---\n'+json.dumps(packet,ensure_ascii=False);(dest/'request_sha256.txt').write_text(hashlib.sha256(request.encode()).hexdigest()+'\n');out=dest/'raw_output.json';events=dest/'events.jsonl';start=time.time()
 with tempfile.TemporaryDirectory(prefix='llm-v29-no-retrieval-') as cwd:
  proc=subprocess.run([str(CLI),'exec','-','--model','gpt-5.6-sol','--cd',cwd,'-c','model_reasoning_effort="medium"','-c','web_search="disabled"','--skip-git-repo-check','--ephemeral','--ignore-user-config','--sandbox','read-only','--output-schema',str(SCHEMA),'--output-last-message',str(out),'--json'],input=request,text=True,capture_output=True,timeout=1800)
 events.write_text(proc.stdout);(dest/'raw_stderr.txt').write_text(proc.stderr);check=subprocess.run(['python3',str(VAL),str(inp),str(out)],capture_output=True,text=True) if out.exists() else None
 if check:(dest/'validation.json').write_text(check.stdout)
 calls=tool_events(events);(dest/'tool_event_audit.json').write_text(json.dumps({'count':len(calls),'events':calls},ensure_ascii=False,indent=2)+'\n');ok=proc.returncode==0 and check and check.returncode==0 and not calls
 meta={'status':'accepted_no_retrieval_rerun' if ok else 'failed_no_retrieval_rerun_preserved','batch':a.batch,'elapsed_seconds':round(time.time()-start,3),'requested_model':'gpt-5.6-sol','reasoning_effort':'medium','web_search':'disabled','tool_event_count':len(calls),'input_sha256':sha(inp),'request_sha256':hashlib.sha256(request.encode()).hexdigest(),'output_sha256':sha(out) if out.exists() else None,'events_sha256':sha(events)};(dest/'run_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(json.dumps(meta,ensure_ascii=False))
 if not ok:raise SystemExit(2)
 shutil.copy2(out,batch/'no_retrieval_output.json');(batch/'no_retrieval_selection_manifest.json').write_text(json.dumps({'status':'selected_by_execution_validation_and_zero_tool_calls','label_or_metric_selection':False,'previous_material_preserved_in':str(history),'selected_output_sha256':sha(out),'rerun_metadata_sha256':sha(dest/'run_metadata.json')},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
