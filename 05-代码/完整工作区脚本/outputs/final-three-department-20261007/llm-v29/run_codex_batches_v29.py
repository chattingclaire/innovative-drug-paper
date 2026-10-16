"""Resumable, immutable v29 calls through the bundled official Codex CLI."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL = "gpt-5.6-sol"
CLI = Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex")
PROMPT = ROOT / "outputs/llm-v29-method-audit-20261005/完整系统提示词-v29.txt"
SCHEMA = HERE / "output_schema_codex_compatible.json"
VALIDATOR = ROOT / "outputs/llm-v29-method-audit-20261005/validate_binary_output.py"
INPUTS = HERE / "frozen_blind_inputs_v29.jsonl"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return digest(path.read_bytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--limit-batches", type=int)
    parser.add_argument("--run-name", required=True)
    args = parser.parse_args()
    assert 1 <= args.batch_size <= 50 and args.start >= 1
    assert Path(args.run_name).name == args.run_name
    rows = [json.loads(line) for line in INPUTS.read_text().splitlines() if line.strip()]
    assert len(rows) == 4924
    batches = [rows[i:i + args.batch_size] for i in range(0, len(rows), args.batch_size)]
    plan = {
        "model": MODEL,
        "n": len(rows),
        "batch_size": args.batch_size,
        "batch_count": len(batches),
        "input_sha256": file_sha(INPUTS),
        "system_prompt_sha256": file_sha(PROMPT),
        "schema_sha256": file_sha(SCHEMA),
        "validation_policy": "Preserve first response; stop on execution or validation failure; never replace labels silently.",
        "reasoning_effort": "medium",
        "reference_labels_or_machine_predictions_available_to_model": False,
    }
    run_root = HERE / args.run_name
    run_root.mkdir(exist_ok=True)
    plan_path = run_root / "run_plan.json"
    if plan_path.exists():
        assert json.loads(plan_path.read_text()) == plan, "resume plan mismatch"
    else:
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    last = len(batches) if args.limit_batches is None else min(len(batches), args.start - 1 + args.limit_batches)
    instruction = PROMPT.read_text()
    for index in range(args.start, last + 1):
        batch = batches[index - 1]
        dest = run_root / "batches" / f"batch-{index:04d}"
        if dest.exists():
            meta_path = dest / "run_metadata.json"
            if not meta_path.exists():
                print(json.dumps({"batch": index, "status": "claimed_or_incomplete_skip"}), flush=True)
                continue
            meta = json.loads(meta_path.read_text())
            if meta["status"] != "accepted_first_output":
                print(json.dumps({"batch": index, "status": "preserved_failure_skip"}), flush=True)
            continue
        try:
            dest.mkdir(parents=True)
        except FileExistsError:
            print(json.dumps({"batch": index, "status": "concurrent_claim_skip"}), flush=True)
            continue
        packet = {"rows": batch}
        packet_path = dest / "input.json"
        packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
        full_prompt = instruction + "\n\n--- 本批冻结盲法输入 ---\n" + json.dumps(packet, ensure_ascii=False)
        (dest / "request_sha256.txt").write_text(digest(full_prompt.encode()) + "\n")
        output_path = dest / "raw_output.json"
        events_path = dest / "events.jsonl"
        started = time.time()
        with tempfile.TemporaryDirectory(prefix="llm-v29-codex-") as empty:
            cmd = [str(CLI), "exec", "-", "--model", MODEL, "--cd", empty,
                   "-c", 'model_reasoning_effort="medium"',
                   "--skip-git-repo-check", "--ephemeral", "--ignore-user-config",
                   "--sandbox", "read-only", "--output-schema", str(SCHEMA),
                   "--output-last-message", str(output_path), "--json"]
            proc = subprocess.run(cmd, input=full_prompt, text=True, capture_output=True, timeout=1800)
        events_path.write_text(proc.stdout)
        (dest / "raw_stderr.txt").write_text(proc.stderr)
        errors = []
        if proc.returncode == 0 and output_path.exists():
            check = subprocess.run(["python3", str(VALIDATOR), str(packet_path), str(output_path)], capture_output=True, text=True)
            (dest / "validation.json").write_text(check.stdout)
            if check.returncode:
                errors.append("schema_or_literal_validation_failure")
        else:
            errors.append("cli_execution_failure")
        observed_models = []
        for line in proc.stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            for key in ("model", "model_name"):
                value = event.get(key)
                if isinstance(value, str) and value not in observed_models:
                    observed_models.append(value)
        meta = {
            "status": "accepted_first_output" if not errors else "execution_or_validation_failure",
            "requested_model": MODEL,
            "observed_model_fields": observed_models,
            "exit_code": proc.returncode,
            "elapsed_seconds": round(time.time() - started, 3),
            "input_n": len(batch),
            "ids": [row["id"] for row in batch],
            "input_sha256": file_sha(packet_path),
            "request_sha256": digest(full_prompt.encode()),
            "raw_output_sha256": file_sha(output_path) if output_path.exists() else None,
            "events_sha256": file_sha(events_path),
            "errors": errors,
            "runtime_parameters_not_exposed": ["temperature", "provider_internal_model_revision"],
            "tool_isolation": "empty temporary cwd; read-only sandbox; prompt contains blind input only",
        }
        (dest / "run_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"batch": index, "status": meta["status"], "elapsed_seconds": meta["elapsed_seconds"]}, ensure_ascii=False), flush=True)
        # Preserve and isolate a failed first response, then continue other
        # independent batches. A later repair uses a new attempt directory.


if __name__ == "__main__":
    main()
