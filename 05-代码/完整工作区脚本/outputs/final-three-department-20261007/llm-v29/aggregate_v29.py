"""Publish a JSONL only after every production batch validates and IDs close."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "production-25-v29"
INPUT = HERE / "frozen_blind_inputs_v29.jsonl"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    expected = [json.loads(line)["id"] for line in INPUT.read_text().splitlines() if line.strip()]
    rows, issues, failures = [], [], []
    for index in range(1, 198):
        batch = RUN / "batches" / f"batch-{index:04d}"
        meta_path = batch / "run_metadata.json"
        if not meta_path.exists():
            failures.append({"batch": index, "status": "missing_or_running"})
            continue
        meta = json.loads(meta_path.read_text())
        no_retrieval = batch / "no_retrieval_output.json"
        repaired = batch / "repaired_output.json"
        if meta["status"] != "accepted_first_output" and not repaired.exists() and not no_retrieval.exists():
            failures.append({"batch": index, "status": meta["status"], "errors": meta.get("errors", [])})
            continue
        selected = no_retrieval if no_retrieval.exists() else repaired if repaired.exists() else batch / "raw_output.json"
        output = json.loads(selected.read_text())
        rows.extend(output["rows"])
        issues.extend(output["issue_records"])
    status = {"expected_n": len(expected), "accepted_n": len(rows), "failed_or_missing_batches": failures}
    (RUN / "aggregation_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    if failures or [row["id"] for row in rows] != expected:
        raise SystemExit("full ID closure not reached; final file not written")
    output = RUN / "all_predictions.jsonl"
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    issue_output = RUN / "all_issue_records.json"
    issue_output.write_text(json.dumps(issues, ensure_ascii=False, indent=2) + "\n")
    manifest = {
        "status": "complete_validated_full_corpus", "n": len(rows),
        "input_sha256": sha(INPUT), "predictions_sha256": sha(output),
        "issue_records_sha256": sha(issue_output), "requested_model": "gpt-5.6-sol",
        "reasoning_effort": "medium"
    }
    (RUN / "final_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
