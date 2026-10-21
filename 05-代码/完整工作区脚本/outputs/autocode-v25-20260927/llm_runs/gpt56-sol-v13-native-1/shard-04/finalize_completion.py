import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).resolve().parent
PYTHON = "/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(input_path: Path, output_path: Path) -> bool:
    run = subprocess.run(
        [PYTHON, str(HERE / "validate_output.py"), str(input_path), str(output_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    return bool(json.loads(run.stdout)["valid"])


batches = []
for number in range(1, 43):
    input_path = HERE / f"input-{number:03d}.json"
    first_output = HERE / f"output-{number:03d}.json"
    corrections = sorted(HERE.glob(f"correction-{number:03d}-*.json"))
    entry = {
        "batch": number,
        "input": {
            "name": input_path.name,
            "sha256": sha256(input_path),
        },
        "first_output": {
            "name": first_output.name,
            "sha256": sha256(first_output),
            "validation_status": "valid" if validate(input_path, first_output) else "invalid",
        },
        "correction_outputs": [
            {
                "name": path.name,
                "sha256": sha256(path),
                "validation_status": "valid" if validate(input_path, path) else "invalid",
            }
            for path in corrections
        ],
    }
    batches.append(entry)

completion = {
    "shard": 4,
    "model_request_name": "gpt-5.6-sol",
    "model_revision": "未知",
    "temperature": "未知",
    "random_seed": "未知",
    "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "batch_count": 42,
    "total_rows": 420,
    "batches": batches,
}

(HERE / "completion.json").write_text(
    json.dumps(completion, ensure_ascii=False, indent=2) + "\n"
)
