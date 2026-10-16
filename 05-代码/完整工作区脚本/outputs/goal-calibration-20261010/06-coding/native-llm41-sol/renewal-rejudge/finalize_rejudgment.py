"""Mechanical validation, byte copying, integrity ledgers, and one-time seal.

No external search/API, semantic classification, old-label loading, or scores.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from jsonschema import Draft202012Validator

OUT = Path(__file__).resolve().parent
DIMS = ("S", "E", "Ec", "I", "F")
ORDER = ("RECODE25-00900", "RECODE25-00902")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(name, obj):
    with (OUT/name).open("x") as h:
        json.dump(obj, h, ensure_ascii=False, indent=2)
        h.write("\n")
    (OUT/name).chmod(0o444)

assert not (OUT/"seal.json").exists()
assert not (OUT/"predictions.jsonl").exists()
freeze_bytes = (OUT/"freeze.json").read_bytes()
assert sha(freeze_bytes) == "2f027f53991cbd92a9208bf4470f1a4b837ebbda999bf4a10dbf4794244f0f42"
freeze = json.loads(freeze_bytes)
paths = {x["role"]: x["path"] for x in freeze["allowed_inputs"] if x["role"] != "original_page"}
asset_checks = []
for a in freeze["allowed_inputs"]:
    data = Path(a["path"]).read_bytes()
    assert sha(data) == a["sha256"] and len(data) == a["bytes"]
    asset_checks.append({"role":a["role"], "path":a["path"], "sha256":sha(data), "matches_freeze":True})
source = {x["id"]:x for x in map(json.loads, Path(paths["source"]).read_text().splitlines())}
resources = json.loads(Path(paths["resource"]).read_text())
assert len(resources["source_texts"]) == 37
assert all(sha(x["text"].encode()) == x["text_sha256"] for x in resources["source_texts"])
manual = Path(paths["manual"]).read_text().splitlines()
journal_bytes = (OUT/"first-judgments.jsonl").read_bytes()
assert journal_bytes.endswith(b"\n")
line_bytes = journal_bytes.splitlines(keepends=True)
records = list(map(json.loads, line_bytes))
assert len(records) == 2 and [r["id"] for r in records] == list(ORDER)
schema = json.loads((OUT/"prediction.schema.json").read_text())
validator = Draft202012Validator(schema)
record_checks = []
for i, r in enumerate(records, 1):
    validator.validate(r)
    assert set(r["labels"]) == set(DIMS) == set(r["evidence"])
    assert r["rejudgment"]["order"] == i
    assert r["rejudgment"]["input_manifest_sha256"] == sha(freeze_bytes)
    cxs = {c["context_id"]:c for c in source[r["id"]]["contexts"]}
    for d in DIMS:
        e = r["evidence"][d]
        assert e["value"] is None or type(e["value"]) is int and e["value"] in (0,1)
        assert e["value"] == r["labels"][d]
        assert e["current_quote"] == source[r["id"]]["text"]
        assert e["current_source_ref"] == source[r["id"]]["source_ref"]
        assert e["path"].strip() and e["reason"].strip()
        for q in e["contexts_used"]:
            c = cxs[q["context_id"]]
            assert q["source_ref"] == c["source_ref"] and q["structure"] == c["structure"]
            if "text" in c:
                assert isinstance(q["quote"],str) and q["quote"] and q["quote"] in c["text"]
            else:
                assert q["quote"] is None and q["text_status"] == "no_text_relationship_node"
        for q in e["manual_references"]:
            assert q["quote"] == manual[q["line"]-1]
            assert q["manual_sha256"] == next(x["sha256"] for x in freeze["allowed_inputs"] if x["role"] == "manual")
        if e["value"] is None:
            assert any(d in m["dimensions"] and m["required_material"] and m["reason"] for m in r["material_requests"])
        if e["path"].startswith("I3") and e["value"] == 1:
            assert all(k in e["relation"] for k in ("research_object", "support_arrangement", "direct_link"))
        if e["path"].startswith("F_specific") and e["value"] == 1:
            assert all(k in e["relation"] for k in ("patient_drug_object", "fairness_link", "arrangement"))
    receipt = json.loads((OUT/("receipt-"+r["id"]+".json")).read_text())
    assert receipt["saved_at"] == r["rejudgment"]["saved_at"]
    assert receipt["record_bytes_sha256"] == sha(line_bytes[i-1])
    assert receipt["journal_prefix_sha256"] == sha(b"".join(line_bytes[:i]))
    assert receipt["authored_sha256"] == sha((OUT/receipt["authored_file"]).read_bytes())
    assert receipt["semantic_revision_count"] == 0
    record_checks.append({"id":r["id"], "order":i, "saved_at":r["rejudgment"]["saved_at"], "first_record_bytes_sha256":receipt["record_bytes_sha256"], "schema_and_source_quote_checks_passed":True, "all_five_dimensions_explicit":True, "semantic_revisions_after_save":0})
assert records[0]["rejudgment"]["saved_at"] <= records[1]["rejudgment"]["saved_at"]
readlog = json.loads((OUT/"read-log.json").read_text())
assert readlog["total_context_nodes"] == 106 and readlog["unique_context_ids"] == 106
assert readlog["resource_count"] == 37 and len(readlog["actual_original_pages_viewed"]) == 9
assert all(a["actual_view_success"] for a in readlog["actual_original_pages_viewed"])
assert readlog["recorded_after_completion_at"] < records[0]["rejudgment"]["saved_at"]
technical = json.loads((OUT/"technical-failures.json").read_text())
assert not technical["unresolved"] and technical["semantic_retries"] == 0
old = OUT.parent/"first-run"
old_seal_bytes = (old/"seal.json").read_bytes()
assert sha(old_seal_bytes) == freeze["first_run_seal_before_rejudge_sha256"]
old_seal = json.loads(old_seal_bytes)
old_checks = []
for f in old_seal["files"]:
    b = (old/f["name"]).read_bytes()
    assert sha(b) == f["sha256"] and len(b) == f["bytes"]
    old_checks.append({"name":f["name"], "sha256":sha(b), "bytes":len(b), "unchanged":True})
assert sha((old/"predictions.jsonl").read_bytes()) == freeze["first_run_prediction_before_rejudge_sha256"]
with (OUT/"predictions.jsonl").open("xb") as h:
    h.write(journal_bytes)
assert (OUT/"predictions.jsonl").read_bytes() == journal_bytes
(OUT/"predictions.jsonl").chmod(0o444)
(OUT/"first-judgments.jsonl").chmod(0o444)
now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
save("validation.json", {"validation_type":"mechanical only; no semantic accuracy assessment", "validated_at":now, "passed":True, "units":2, "dimensions":10, "source_order_preserved":True, "strict_values_and_schema_passed":True, "current_quotes_exact_full_text":True, "all_used_context_quotes_contiguous_and_source_bound":True, "manual_quotes_exact":True, "no_text_relationship_nodes_preserved":True, "null_request_consistency_passed":True, "all_13_inputs_unchanged":True, "37_resource_text_hashes_match":True, "read_coverage_verified":True, "first_judgments_predictions_byte_identical":True, "first_run_14_sealed_files_and_seal_unchanged":True, "record_receipts":record_checks, "scores_or_result_comparisons_computed":False})
execution = {"record_type":"completed_execution_ledger", "completed_at":now, "identity":freeze["identity"], "execution":freeze["execution"], "unit_save_ledger":record_checks, "source_read_coverage":{"current_units":2,"contexts":106,"resources":37,"original_images_actually_viewed":9}, "freeze_sha256":sha(freeze_bytes), "plan_sha256":freeze["plan_sha256"], "manual_rule_changes_this_round":False, "I2_disclosure_file":"freeze-addendum.json", "agent_invoked_external_model_api_calls":0, "per_unit_http_sessions":0, "provider_internal_native_conversation_transport":None, "parameter_observability":{"seed":None,"temperature":None,"provider_reported_actual_model":None,"provider_reported_actual_effort":None}, "history_exposure":{"same_conversation":True,"own_first_run_two_unit_judgments_seen":True,"fresh_context":False,"other_coder_or_reference_answers_accessed":False}, "technical_assistance":{"compliance_only_subagent":True,"source_image_or_label_access":False,"semantic_decision_makers":1}, "program_use":"hashing, exact-text projection pointers, ledgers, explicit-value serialization, mechanical validation and raw byte copy only", "technical_event_count":len(technical["events"]), "technical_events_resolved_before_first_save":True, "unresolved_technical_events":0, "semantic_retry_count":0, "semantic_post_save_revisions":0, "legacy_preservation":{"seal_sha256":sha(old_seal_bytes),"sealed_files":old_checks,"unchanged":True,"semantic_labels_not_loaded_or_compared_by_validator":True}, "outside_results_or_metrics_accessed":False,"result_comparisons_computed":False,"human_coder":False,"formal_acceptance":False,"final_heldout":False}
save("execution-ledger.json", execution)
save("submission.json", {"submission_type":"AI same-context source-supplement development rejudgment", "submitted_at":now,"status":"complete; one-time seal follows", "ids":list(ORDER),"record_count":2,"dimension_count":10,"all_five_dimensions_rejudged":True,"configured_model":"gpt-6.1-sol","configured_reasoning_effort":"ultra","configuration_evidence":freeze["execution"]["configuration_evidence"],"provider_reported_model":None,"provider_reported_reasoning_effort":None,"seed":None,"temperature":None,"external_model_API_called":False,"per_unit_new_HTTP_API_sessions":False,"native_Codex_conversation":True,"same_context":True,"own_prior_judgments_seen":True,"new_fresh_context":False,"human_coder":False,"formal_acceptance":False,"final_heldout":False,"first_run_overwritten":False,"original_metadata_status":resources["metadata_status"],"official_url":None,"official_publication_date":None,"plan_path":paths["plan"],"plan_sha256":freeze["plan_sha256"],"freeze_sha256":sha(freeze_bytes),"prediction_file":"predictions.jsonl","prediction_sha256":sha(journal_bytes),"first_judgments_file":"first-judgments.jsonl","first_judgments_sha256":sha(journal_bytes),"byte_identical":True,"input_ledger":"input-ledger.json","read_log":"read-log.json","execution_ledger":"execution-ledger.json","technical_failures":"technical-failures.json","mechanical_validation":"validation.json","metrics_computed":False,"result_comparisons_computed":False,"other_coders_or_reference_accessed":False})
files = []
for p in sorted(OUT.iterdir()):
    assert p.is_file()
    p.chmod(0o444)
    b = p.read_bytes()
    files.append({"name":p.name,"bytes":len(b),"sha256":sha(b)})
save("seal.json", {"sealed_at":datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),"status":"sealed","scope":"all renewal-rejudge files including preparation and schema, except this self-referential seal","files":files,"plan_sha256":freeze["plan_sha256"],"input_checks":asset_checks,"predictions_first_judgments_identical":True,"unit_count":2,"dimension_count":10,"semantic_changes_after_first_save":False,"first_run_unchanged":True,"same_context":True,"own_prior_judgments_seen":True,"fresh_context":False,"human_coder":False,"formal_acceptance":False,"final_heldout":False,"reference_or_other_coder_answers_read":False,"metrics_or_result_comparisons_computed":False})
print(json.dumps({"status":"sealed","unit_count":2,"dimension_count":10,"prediction_sha256":sha(journal_bytes),"submission_sha256":sha((OUT/"submission.json").read_bytes()),"seal_sha256":sha((OUT/"seal.json").read_bytes()),"legacy_unchanged":True,"byte_identical":True,"output_directory":str(OUT)}, ensure_ascii=False))
