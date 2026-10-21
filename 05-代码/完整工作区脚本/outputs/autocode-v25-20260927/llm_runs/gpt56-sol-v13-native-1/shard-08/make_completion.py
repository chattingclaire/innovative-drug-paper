import hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

here=Path(__file__).resolve().parent
py="/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for n in range(1,43):
    tag=f"{n:03d}"
    inp=here/f"input-{tag}.json"
    first=here/f"output-{tag}.json"
    effective=here/("correction-015-02.json" if n==15 else f"output-{tag}.json")
    first_check=subprocess.run([py,str(here/'validate_output.py'),str(inp),str(first)],capture_output=True,text=True)
    eff_check=subprocess.run([py,str(here/'validate_output.py'),str(inp),str(effective)],capture_output=True,text=True)
    records.append({
      "batch":tag,"input_file":inp.name,"input_sha256":sha(inp),
      "first_output_file":first.name,"first_output_sha256":sha(first),
      "first_output_valid":first_check.returncode==0,
      "effective_output_file":effective.name,"effective_output_sha256":sha(effective),
      "effective_output_valid":eff_check.returncode==0
    })
data={
 "shard":"08","requested_model":"gpt-5.6-sol","underlying_model_revision":"未知",
 "temperature":"未知","random_seed":"未知",
 "completed_at":datetime.now(timezone.utc).astimezone().isoformat(),
 "batch_count":42,"total_rows":420,"protocol_version":"CAL-5D-20260926-v1.3",
 "batches":records,
 "corrections":[
  {"batch":"015","file":"correction-015-01.json","sha256":sha(here/'correction-015-01.json'),"valid":False,"reason":"首次结构校验发现Ec引文不是单元内连续原文；保留原输出，另存更正。"},
  {"batch":"015","file":"correction-015-02.json","sha256":sha(here/'correction-015-02.json'),"valid":True,"reason":"移除非逐字引文，仅保留单元内连续原文；标签与语义判断未改变。"}
 ]
}
(here/'completion.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
assert all(r['effective_output_valid'] for r in records)
