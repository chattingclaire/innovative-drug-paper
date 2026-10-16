"""Mechanical evidence audit; immutable AI first judgements stay untouched."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "04-calibration/source-impact4-v12/B"
ADMIN = B.parent / "admin"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pointer(obj, value):
    for part in value.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


seal = json.loads((B / "delivery-seal.json").read_text())
checks = []
for item in seal["files"]:
    p = Path(item["path"])
    checks.append({"path": str(p), "sha_match": sha(p) == item["sha256"],
                   "bytes_match": p.stat().st_size == item["bytes"]})
assert all(c["sha_match"] and c["bytes_match"] for c in checks)
assert sha(ADMIN / "input-freeze.json") == seal["input_freeze_sha256"]
assert sha(B / "first-complete-submission.json") == seal["first_complete_submission_sha256"]
assert sha(B / "labels.jsonl") == seal["labels_jsonl_sha256"]
rows = [json.loads(l) for l in (B / "labels.jsonl").read_text().splitlines()]
first = json.loads((B / "first-complete-submission.json").read_text())["items"]
assert rows == first
assert [x["id"] for x in rows] == seal["order"]
common_path = ROOT / "01-review/context-projection-sol/full-frame-preflight/4-record-common-v12/common-source-bundles.jsonl"
common = {x["source_record"]["id"]: x for x in map(json.loads, common_path.read_text().splitlines())}
quote_n = 0
record_checks = []
for row in rows:
    rid = row["id"]
    assert json.loads((B / f"{rid}.first-judgment.json").read_text()) == row
    source = json.loads((B / f"{rid}.source-record.json").read_text())
    assert source == common[rid]["source_record"]
    contexts = {c["context_id"]: c for c in source["contexts"]}
    assert set(row["labels"]) == {"S", "E", "Ec", "I", "F"}
    assert all(type(v) is int and v in (0, 1) for v in row["labels"].values())
    assert row["source_requests"] == []
    for evidence in row["evidence"].values():
        q = evidence["current_quote"]
        span = evidence["current_span"]
        assert source["text"][span["start"]:span["end"]] == q
        assert q in source["text"]
        quote_n += 1
        for cq in evidence.get("context_quotes", []):
            text = contexts[cq["context_id"]]["text"]
            span = cq["span"]
            assert text[span["start"]:span["end"]] == cq["quote"]
            assert pointer(common[rid], cq["source_bundle_pointer"]) == text
            quote_n += 1
    record_checks.append({"id": rid, "first_submission_object_equal": True,
                          "raw_source_object_equal": True, "current_and_context_quotes_and_spans_pass": True})
report = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "status": "root_mechanical_binding_and_literal_quote_audit_passed",
    "delivery_seal_sha256": sha(B / "delivery-seal.json"),
    "file_checks": checks, "record_checks": record_checks,
    "record_n": len(rows), "binary_decision_n": len(rows) * 5,
    "literal_quote_n": quote_n,
    "semantic_correctness_certified": False,
    "human_coding": False,
    "note": "File identity and literal quotes do not prove that all substantive branches were interpreted correctly."
}
out = ADMIN / "root-B-seal-and-quote-quality.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"report": str(out), "sha256": sha(out), "files": len(checks), "quotes": quote_n}))
