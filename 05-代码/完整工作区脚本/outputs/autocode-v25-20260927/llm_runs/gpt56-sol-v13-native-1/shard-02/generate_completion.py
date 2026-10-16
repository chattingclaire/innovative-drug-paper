import hashlib,json,subprocess
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent
PY='/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
batches=[]
for i in range(1,43):
 n=f'{i:03d}'; inp=HERE/f'input-{n}.json'; first=HERE/f'output-{n}.json'
 check=subprocess.run([PY,str(HERE/'validate_output.py'),str(inp),str(first)],capture_output=True,text=True)
 effective=HERE/'correction-032-01.json' if n=='032' else first
 echeck=subprocess.run([PY,str(HERE/'validate_output.py'),str(inp),str(effective)],capture_output=True,text=True)
 assert echeck.returncode==0,(n,echeck.stdout,echeck.stderr)
 item={'batch':n,'input_file':inp.name,'input_sha256':sha(inp),'first_output_file':first.name,'first_output_sha256':sha(first),'first_output_valid':check.returncode==0,'effective_output_file':effective.name,'effective_output_sha256':sha(effective)}
 batches.append(item)
doc={'shard':2,'model_request_name':'gpt-5.6-sol','completed_at':datetime.now().astimezone().isoformat(timespec='seconds'),'batch_count':42,'total_rows':420,'batches':batches}
(HERE/'completion.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
