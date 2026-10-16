import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from validate_output import shape, validate


HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validation(input_path, output_path):
    inputs = json.loads(input_path.read_text(encoding="utf-8"))["rows"]
    result = json.loads(output_path.read_text(encoding="utf-8"))
    schema = json.loads((HERE / "output_schema.json").read_text(encoding="utf-8"))
    errors = shape(result, schema)
    if not errors:
        errors += validate(result, inputs)
    return {"n": len(inputs), "errors": errors, "valid": not errors}


batches = []
for number in range(1, 43):
    code = f"{number:03d}"
    input_path = HERE / f"input-{code}.json"
    output_path = HERE / f"output-{code}.json"
    corrections = []
    for correction_path in sorted(HERE.glob(f"correction-{code}-*.json")):
        corrections.append(
            {
                "file": correction_path.name,
                "sha256": sha256(correction_path),
                "validation": validation(input_path, correction_path),
            }
        )
    batches.append(
        {
            "batch": code,
            "input_file": input_path.name,
            "input_sha256": sha256(input_path),
            "output_file": output_path.name,
            "output_sha256": sha256(output_path),
            "first_output_validation": validation(input_path, output_path),
            "correction_outputs": corrections,
        }
    )

completion = {
    "shard": 11,
    "model_request_name": "gpt-5.6-sol",
    "completed_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
    "batch_count": 42,
    "total_rows": 420,
    "model_revision": "未知",
    "temperature": "未知",
    "random_seed": "未知",
    "batches": batches,
}

target = HERE / "completion.json"
if target.exists():
    raise SystemExit("completion.json already exists; refusing to overwrite")
target.write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
