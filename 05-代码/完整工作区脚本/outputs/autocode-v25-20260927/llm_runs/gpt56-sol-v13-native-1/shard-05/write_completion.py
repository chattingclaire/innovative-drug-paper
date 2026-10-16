import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

here = Path(__file__).resolve().parent
target = here / "completion.json"
if target.exists():
    raise SystemExit("refusing to overwrite completion.json")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

files = []
for n in range(1, 43):
    stem = f"{n:03d}"
    inp = here / f"input-{stem}.json"
    out = here / f"output-{stem}.json"
    proc = subprocess.run(
        [sys.executable, str(here / "validate_output.py"), str(inp), str(out)],
        text=True, capture_output=True
    )
    status = json.loads(proc.stdout)
    record = {
        "input": inp.name,
        "input_sha256": sha(inp),
        "first_output": out.name,
        "first_output_sha256": sha(out),
        "first_output_validation": status,
    }
    if n == 34:
        correction = here / "correction-034-01.json"
        cproc = subprocess.run(
            [sys.executable, str(here / "validate_output.py"), str(inp), str(correction)],
            text=True, capture_output=True, check=True
        )
        record["correction"] = {
            "name": correction.name,
            "sha256": sha(correction),
            "validation": json.loads(cproc.stdout),
            "log": "correction-log.txt",
            "log_sha256": sha(here / "correction-log.txt"),
        }
    files.append(record)

completion = {
    "shard": "shard-05",
    "model_request_name": "gpt-5.6-sol",
    "underlying_model_revision": "unknown",
    "temperature": "unknown",
    "random_seed": "unknown",
    "completed_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
    "batch_count": 42,
    "total_rows": 420,
    "protocol_version": "CAL-5D-20260926-v1.3",
    "files": files,
}
target.write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n")
