"""Executable synthetic qualification fixture. Not a production source adapter.

No report boolean can replace these operations. Original packets must satisfy the
externally bound closed schema, their identity/content/CTX hashes, and every
quoted leaf and span is inspected. Only this toy shape is supported here.
"""
from copy import deepcopy
import hashlib
import json
from jsonschema import Draft202012Validator

INTERFACE = "opaque-source-and-quotes-v1"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def adapt_source(packet, assignment, schema):
    """Opaque identity projection: reject unknown metadata, never trim it."""
    errors = list(Draft202012Validator(schema).iter_errors(packet))
    need(not errors, "closed source schema: " + (errors[0].message if errors else ""))
    need(packet["source_id"] == assignment["source_id"], "source_id mismatch")
    need(packet["blind_id"] == assignment["output_id"], "source output_id mismatch")
    unsigned = deepcopy(packet)
    declared = unsigned.pop("content_sha256")
    need(declared == sha(unsigned), "source content SHA mismatch")
    ids = [x["context_id"] for x in packet["contexts"]]
    need(len(ids) == len(set(ids)), "duplicate CTX")
    need(all(x["parent_id"] is None or x["parent_id"] in ids for x in packet["contexts"]), "dangling CTX")
    need(assignment["ctx_binding_sha256"] == sha(packet["contexts"]), "CTX binding drift")
    need(assignment["source_content_sha256"] == declared, "source content identity drift")
    # No geometry/assets are silently converted into this toy representation.
    need(packet["attachments"] == [], "toy adapter has no asset capability")
    return deepcopy(packet)


def check_quotes(item, packet, manual_sha256, delivered_assets):
    """Actually resolve toy text paths and Unicode half-open continuous spans."""
    need(item["blind_id"] == packet["blind_id"], "response output identity drift")
    need(item["content_sha256"] == packet["content_sha256"], "response content SHA mismatch")
    need(item["manual_sha256"] == manual_sha256, "response manual SHA mismatch")
    need(delivered_assets == [], "unexpected asset delivery")
    ctx = {x["context_id"]: x for x in packet["contexts"]}
    traces = []

    def quote(text, value, span, pointer):
        need(type(span["start"]) is int and type(span["end"]) is int, "span integer type")
        start, end = span["start"], span["end"]
        need(0 <= start < end <= len(text) and text[start:end] == value,
             "noncontiguous/mismatched quote at " + pointer)
        traces.append({"response_pointer": pointer, "start": start, "end": end,
                       "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})

    def referenced(ref, pointer):
        if ref["source_kind"] == "current":
            need(ref["context_id"] is None and ref["field_path"] == "unit_text", "current reference path")
            text = packet["unit_text"]
        else:
            need(ref["context_id"] in ctx and ref["field_path"] in {"text", "title", "caption"}, "unknown CTX/path")
            text = ctx[ref["context_id"]][ref["field_path"]]
        quote(text, ref["quote"], ref["span"], pointer)

    nulls = {d for d, value in item["labels"].items() if value is None}
    requests = item["material_requests"]
    need(len(requests) == len(nulls) and {x["dimension"] for x in requests} == nulls,
         "material request must uniquely cover exactly semantic null dimensions")
    for req in requests:
        need(all(i in ctx for i in req["context_ids"]), "material-request CTX absent")
    for dim, ev in item["evidence"].items():
        value = item["labels"][dim]
        need(value is None or type(value) is int and value in (0, 1), "labels require JSON integer or null")
        null_paths = set(ev["paths"]) & {"material_missing", "rule_conflict"}
        need(bool(null_paths) == (value is None), "null technical path inconsistency")
        if value is None:
            req = next(x for x in requests if x["dimension"] == dim)
            need(req["kind"] in null_paths, "null reason/request kind mismatch")
        quote(packet["unit_text"], ev["current_quote"], ev["current_span"], "/evidence/" + dim + "/current_quote")
        for index, ref in enumerate(ev["contexts_used"]):
            need(ref["context_id"] in ctx and ref["field_path"] in {"text", "title", "caption"}, "unknown CTX/path")
            quote(ctx[ref["context_id"]][ref["field_path"]], ref["quote"], ref["span"],
                  f"/evidence/{dim}/contexts_used/{index}")
        need(all(i in ctx for i in ev["structural_context_ids_used"]), "structural CTX absent")
        need(ev["image_sources_used"] == [], "toy has no image evidence")
        for name, fields in (("innovation_support", ("rd_object", "available_support")),
                             ("fairness_specific", ("patient_drug_object", "fairness_relation", "arrangement_or_evaluation"))):
            if ev[name] is not None:
                for field in fields:
                    referenced(ev[name][field], f"/evidence/{dim}/{name}/{field}")
        need((ev["innovation_support"] is not None) == (dim == "I" and value == 1 and "I3" in ev["paths"]), "I3 structured support required only for its path")
        need((ev["fairness_specific"] is not None) == (dim == "F" and value == 1 and "F_specific" in ev["paths"]), "F structured support required only for its path")
    return {"interface": INTERFACE, "quote_trace": traces,
            "source_validation": "executed_closed_toy_schema_and_identity_projection",
            "semantic_classification_validated": False}
