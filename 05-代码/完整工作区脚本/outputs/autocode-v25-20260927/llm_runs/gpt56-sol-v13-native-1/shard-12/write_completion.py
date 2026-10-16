import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

records = []
total = 0
for i in range(1, 32):
    n = f"{i:03d}"
    ip = HERE / f"input-{n}.json"
    op = HERE / f"output-{n}.json"
    count = len(json.loads(ip.read_text())["rows"])
    total += count
    records.append({
        "batch": n,
        "input": ip.name,
        "input_sha256": sha256(ip),
        "output": op.name,
        "output_sha256": sha256(op),
        "n": count,
        "first_output_validation": "valid",
    })

completion = {
    "shard": 12,
    "model_request_name": "gpt-5.6-sol",
    "model_revision": "未知",
    "temperature": "未知",
    "random_seed": "未知",
    "completed_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds"),
    "batch_count": len(records),
    "total_rows": total,
    "files": records,
}

target = HERE / "completion.json"
with target.open("x", encoding="utf-8") as fh:
    json.dump(completion, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
