import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

here = Path(__file__).resolve().parent
target = here / "completion.json"
if target.exists():
    raise SystemExit("refusing to overwrite completion.json")
records = []
for n in range(1, 43):
    inp = here / f"input-{n:03d}.json"
    out = here / f"output-{n:03d}.json"
    proc = subprocess.run(
        ["/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3", str(here / "validate_output.py"), str(inp), str(out)],
        capture_output=True, text=True,
    )
    verdict = json.loads(proc.stdout)
    records.append({
        "packet": f"{n:03d}",
        "input_file": inp.name,
        "input_sha256": hashlib.sha256(inp.read_bytes()).hexdigest(),
        "output_file": out.name,
        "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "first_output_validation_valid": proc.returncode == 0 and verdict.get("valid") is True,
    })
completion = {
    "shard": 1,
    "model_request_name": "gpt-5.6-sol",
    "underlying_model_revision": "未知",
    "temperature": "未知",
    "random_seed": "未知",
    "completed_at": datetime.now(timezone.utc).isoformat(),
    "packet_count": 42,
    "total_rows": 420,
    "files": records,
}
target.write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n")
print(hashlib.sha256(target.read_bytes()).hexdigest())
