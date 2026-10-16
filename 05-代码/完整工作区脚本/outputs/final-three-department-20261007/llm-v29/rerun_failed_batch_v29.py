"""Rerun a gated batch with one source-verified context supplement."""
import argparse,hashlib,json,subprocess,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CLI=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex');PROMPT=ROOT/'outputs/llm-v29-method-audit-20261005/完整系统提示词-v29.txt';SCHEMA=HERE/'output_schema_codex_compatible.json';VAL=ROOT/'outputs/llm-v29-method-audit-20261005/validate_binary_output.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--batch',type=int,required=True);ap.add_argument('--supplement',required=True);a=ap.parse_args();batch=HERE/'production-25-v29/batches'/f'batch-{a.batch:04d}';sup_path=Path(a.supplement);sup=json.loads(sup_path.read_text());src=Path(sup['source_path']);sup['source_sha256']=sha(src)
 packet=json.loads((batch/'input.json').read_text());found=False
 for row in packet['rows']:
  if row['id']==sup['id']:row['contexts']['resolved_material_supplement']=sup;found=True
 assert found
 dest=batch/'repairs'/'full-batch-context-repair';dest.mkdir(parents=True,exist_ok=False);inp=dest/'input.json';inp.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n');request=PROMPT.read_text()+'\n\n--- 补料后整批独立重读；不提供旧答案 ---\n'+json.dumps(packet,ensure_ascii=False);out=dest/'raw_output.json';start=time.time()
 with tempfile.TemporaryDirectory(prefix='llm-v29-context-repair-') as cwd:proc=subprocess.run([str(CLI),'exec','-','--model','gpt-5.6-sol','--cd',cwd,'-c','model_reasoning_effort="medium"','--skip-git-repo-check','--ephemeral','--ignore-user-config','--sandbox','read-only','--output-schema',str(SCHEMA),'--output-last-message',str(out),'--json'],input=request,text=True,capture_output=True,timeout=1800)
 (dest/'events.jsonl').write_text(proc.stdout);(dest/'raw_stderr.txt').write_text(proc.stderr);check=subprocess.run(['python3',str(VAL),str(inp),str(out)],capture_output=True,text=True) if out.exists() else None
 if check:(dest/'validation.json').write_text(check.stdout)
 ok=proc.returncode==0 and check and check.returncode==0;meta={'status':'accepted_context_repair_rerun' if ok else 'failed_context_repair_preserved','batch':a.batch,'elapsed_seconds':round(time.time()-start,3),'requested_model':'gpt-5.6-sol','reasoning_effort':'medium','supplement_sha256':hashlib.sha256(json.dumps(sup,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'old_answer_not_in_prompt':True,'output_sha256':sha(out) if out.exists() else None};(dest/'run_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(json.dumps(meta,ensure_ascii=False))
 if not ok:raise SystemExit(2)
 (batch/'repaired_output.json').write_bytes(out.read_bytes());(batch/'repaired_validation.json').write_text(check.stdout);(batch/'repair_manifest.json').write_text(json.dumps({'status':'accepted_after_context_repair_model_rerun','original_raw_preserved':True,'supplement_id':sup['id'],'supplement_source_sha256':sup['source_sha256'],'repaired_output_sha256':sha(out)},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
