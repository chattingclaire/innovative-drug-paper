"""Rerun one invalid row; retain the full first batch response unchanged."""
import argparse, hashlib, json, subprocess, tempfile, time
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
CLI=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')
PROMPT=ROOT/'outputs/llm-v29-method-audit-20261005/完整系统提示词-v29.txt'
SCHEMA=HERE/'output_schema_codex_compatible.json'
VALIDATOR=ROOT/'outputs/llm-v29-method-audit-20261005/validate_binary_output.py'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--batch',type=int,required=True);ap.add_argument('--id',required=True);a=ap.parse_args()
 batch=HERE/'production-25-v29/batches'/f'batch-{a.batch:04d}'
 original_packet=json.loads((batch/'input.json').read_text()); target=[r for r in original_packet['rows'] if r['id']==a.id];assert len(target)==1
 repair=batch/'repairs'/a.id;repair.mkdir(parents=True,exist_ok=False)
 packet={'rows':target}; inp=repair/'input.json';inp.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
 request=PROMPT.read_text()+'\n\n--- 单条格式失败隔离重跑；不提供旧答案 ---\n'+json.dumps(packet,ensure_ascii=False)
 out=repair/'raw_output.json';start=time.time()
 with tempfile.TemporaryDirectory(prefix='llm-v29-repair-') as cwd:
  proc=subprocess.run([str(CLI),'exec','-','--model','gpt-5.6-sol','--cd',cwd,'-c','model_reasoning_effort="medium"','--skip-git-repo-check','--ephemeral','--ignore-user-config','--sandbox','read-only','--output-schema',str(SCHEMA),'--output-last-message',str(out),'--json'],input=request,text=True,capture_output=True,timeout=1800)
 (repair/'events.jsonl').write_text(proc.stdout);(repair/'raw_stderr.txt').write_text(proc.stderr)
 check=subprocess.run(['python3',str(VALIDATOR),str(inp),str(out)],capture_output=True,text=True) if out.exists() else None
 if check:(repair/'validation.json').write_text(check.stdout)
 ok=proc.returncode==0 and check and check.returncode==0
 meta={'status':'accepted_repair_output' if ok else 'failed_repair_preserved','id':a.id,'batch':a.batch,'elapsed_seconds':round(time.time()-start,3),'requested_model':'gpt-5.6-sol','reasoning_effort':'medium','input_sha256':sha(inp),'output_sha256':sha(out) if out.exists() else None,'old_answer_not_in_prompt':True}
 (repair/'run_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(json.dumps(meta,ensure_ascii=False))
 if not ok:raise SystemExit(2)
 base=batch/'repaired_output.json' if (batch/'repaired_output.json').exists() else batch/'raw_output.json'
 original=json.loads(base.read_text()); replacement=json.loads(out.read_text())['rows'][0]
 original['rows']=[replacement if r['id']==a.id else r for r in original['rows']]
 repaired=batch/'repaired_output.json';repaired.write_text(json.dumps(original,ensure_ascii=False,indent=2)+'\n')
 final_check=subprocess.run(['python3',str(VALIDATOR),str(batch/'input.json'),str(repaired)],capture_output=True,text=True)
 (batch/'repaired_validation.json').write_text(final_check.stdout)
 if final_check.returncode:raise SystemExit(3)
 (batch/'repair_manifest.json').write_text(json.dumps({'status':'accepted_after_isolated_model_rerun','original_raw_preserved':True,'repaired_id':a.id,'repaired_output_sha256':sha(repaired)},ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
