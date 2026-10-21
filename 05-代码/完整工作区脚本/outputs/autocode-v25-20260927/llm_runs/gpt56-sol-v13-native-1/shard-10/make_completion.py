#!/usr/bin/env python3
import hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

here=Path(__file__).resolve().parent
manifest=json.loads((here/"manifest.json").read_text())
items=[]
total=0
for n in range(1,43):
    b=f"{n:03d}"
    ip=here/f"input-{b}.json"; op=here/f"output-{b}.json"
    proc=subprocess.run(["/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",str(here/"validate_output.py"),str(ip),str(op)],capture_output=True,text=True)
    audit=json.loads(proc.stdout)
    if proc.returncode or not audit.get("valid"):
        raise SystemExit(f"batch {b} validation failed: {audit}")
    payload=json.loads(ip.read_text()); total+=len(payload["rows"])
    items.append({
        "batch":b,
        "input":ip.name,
        "input_sha256":hashlib.sha256(ip.read_bytes()).hexdigest(),
        "output":op.name,
        "output_sha256":hashlib.sha256(op.read_bytes()).hexdigest(),
        "first_output_validation":{"valid":True,"n":audit["n"],"errors":[]}
    })
expected={x["name"]:x["sha256"] for x in manifest["packets"]}
for item in items:
    if expected[item["input"]]!=item["input_sha256"]:
        raise SystemExit(f"manifest hash mismatch: {item['input']}")
completion={
    "shard":"shard-10",
    "model_request_name":"gpt-5.6-sol",
    "underlying_model_revision":"未知",
    "temperature":"未知",
    "random_seed":"未知",
    "completed_at":datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    "batch_count":len(items),
    "total_rows":total,
    "batches":items
}
target=here/"completion.json"
if target.exists(): raise SystemExit("refusing to overwrite completion.json")
target.write_text(json.dumps(completion,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"batch_count":len(items),"total_rows":total,"completion_sha256":hashlib.sha256(target.read_bytes()).hexdigest()},ensure_ascii=False))
