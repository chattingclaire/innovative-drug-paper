"""Only serialize explicitly AI-authored decisions and check source quotations.

This program has no semantic classifier, label defaults, old-label input, or API.
"""
import json
import hashlib
import sys
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

OUT = Path(__file__).resolve().parent
DIMS = ("S", "E", "Ec", "I", "F")
ORDER = ("RECODE25-00900", "RECODE25-00902")

def digest(data):
    return hashlib.sha256(data).hexdigest()

freeze_bytes = (OUT / "freeze.json").read_bytes()
freeze = json.loads(freeze_bytes)
for asset in freeze["allowed_inputs"]:
    assert digest(Path(asset["path"]).read_bytes()) == asset["sha256"]
paths = {x["role"]: x["path"] for x in freeze["allowed_inputs"] if x["role"] != "original_page"}
source = {x["id"]: x for x in map(json.loads, Path(paths["source"]).read_text().splitlines())}
manual_lines = Path(paths["manual"]).read_text().splitlines()
assert not (OUT / "seal.json").exists(), "Sealed output cannot be modified"
authored_path = Path(sys.argv[1]).resolve()
assert authored_path.parent == OUT
authored = json.loads(authored_path.read_text())
journal = OUT / "first-judgments.jsonl"
previous = [] if not journal.exists() else list(map(json.loads, journal.read_text().splitlines()))
assert len(previous) < len(ORDER)
assert [x["id"] for x in previous] == list(ORDER[:len(previous)])
assert authored["id"] == ORDER[len(previous)]
row = source[authored["id"]]
contexts = {x["context_id"]: x for x in row["contexts"]}
assert set(authored["dimensions"]) == set(DIMS)
assert "material_requests" in authored
evidence = {}
labels = {}
for dim in DIMS:
    a = authored["dimensions"][dim]
    assert "value" in a and (a["value"] is None or type(a["value"]) is int and a["value"] in (0, 1))
    used = []
    for key in a["context_refs"]:
        q = authored["quotation_bank"][key]
        c = contexts[q["context_id"]]
        if "text" in c:
            assert isinstance(q["quote"], str) and q["quote"] and q["quote"] in c["text"]
            status = "source_contiguous_quote"
        else:
            assert q["quote"] is None
            status = "no_text_relationship_node"
        used.append({"context_id":c["context_id"], "quote":q["quote"], "source_ref":c["source_ref"], "structure":c["structure"], "text_status":status})
    mrefs = []
    for n in a["manual_line_refs"]:
        assert type(n) is int and 1 <= n <= len(manual_lines)
        mrefs.append({"manual_path":paths["manual"], "manual_sha256":next(x["sha256"] for x in freeze["allowed_inputs"] if x["role"]=="manual"), "line":n, "quote":manual_lines[n-1]})
    labels[dim] = a["value"]
    evidence[dim] = {"value":a["value"], "path":a["path"], "current_quote":row["text"], "current_source_ref":row["source_ref"], "contexts_used":used, "manual_references":mrefs, "reason":a["reason"]}
    if "relation" in a:
        evidence[dim]["relation"] = a["relation"]
    if a["value"] is None:
        assert any(dim in r["dimensions"] for r in authored["material_requests"])
saved_at = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
result = {"id":row["id"], "labels":labels, "evidence":evidence, "material_requests":authored["material_requests"], "rejudgment":{"order":len(previous)+1, "saved_at":saved_at, "input_manifest_sha256":digest(freeze_bytes), "plan_sha256":freeze["plan_sha256"], "same_context":True, "previous_self_judgments_seen":True, "all_five_dimensions_rejudged":True, "first_run_overwritten":False, "formal_heldout":False, "api_called":False, "api_call_scope":"agent-invoked external model API; native provider internals unavailable", "human_coder":False, "semantic_author":"single native AI conversation", "serialization_only_program":True}}
record_bytes = (json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
with journal.open("ab" if journal.exists() else "xb") as handle:
    handle.write(record_bytes)
    handle.flush()
    os.fsync(handle.fileno())
receipt = {"id":row["id"], "order":len(previous)+1, "saved_at":saved_at, "authored_file":authored_path.name, "authored_sha256":digest(authored_path.read_bytes()), "record_bytes_sha256":digest(record_bytes), "journal_prefix_sha256":digest(journal.read_bytes()), "semantic_revision_count":0}
with (OUT / ("receipt-" + row["id"] + ".json")).open("x") as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
authored_path.chmod(0o444)
(OUT / ("receipt-" + row["id"] + ".json")).chmod(0o444)
print(json.dumps({"saved_id":row["id"], "order":receipt["order"], "record_bytes_sha256":receipt["record_bytes_sha256"]}, ensure_ascii=False))
