from pathlib import Path
import sys, hashlib, json, datetime
p=Path("/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-llm77-v13-sol/scheduling/initial-prompts/batch-0001.txt")
root=Path(__file__).parent
b=p.read_bytes()
assert len(b)==159060 and hashlib.sha256(b).hexdigest()=="7a4e8c7507f1f045f7ac30cfa0f0787c5ed67dd7cf032e240c5dc9fbb3e0a44b"
n=int(sys.argv[1]); start=0
for i in range(1,n+1):
 end=min(start+6000,len(b))
 while end<len(b) and b[end]&192==128: end-=1
 if i<n: start=end
assert start<len(b)
body=b[start:end].decode("utf-8")
meta={"file":str(p),"file_bytes":len(b),"file_sha256":hashlib.sha256(b).hexdigest(),"chunk":n,"start":start,"end":end,"body_bytes":end-start,"chunk_sha256":hashlib.sha256(b[start:end]).hexdigest(),"eof":end==len(b),"emitted_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"delivery_status":"emitted_tool_result_requires_agent_verification"}
output=json.dumps(meta,ensure_ascii=False)+"\n---BEGIN RAW BODY---\n"+body+"\n---END RAW BODY chunk="+str(n)+" range=["+str(start)+","+str(end)+") eof="+str(end==len(b)).lower()+"---\n"
(root/("chunk-%04d.txt"%n)).write_text(output,encoding="utf-8",newline="")
with (root/"instruction-read-events.jsonl").open("a",encoding="utf-8") as f: f.write(json.dumps(meta,ensure_ascii=False)+"\n")
print(output,end="")
