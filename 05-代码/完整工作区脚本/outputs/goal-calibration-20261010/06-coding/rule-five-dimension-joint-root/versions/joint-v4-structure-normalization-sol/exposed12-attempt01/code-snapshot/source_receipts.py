"""Resolve omitted receipt source identity from explicit, frozen source proof.

The original producer inventory and source bundle are retained unchanged.
This adapter grants neither source applicability nor a reading/use receipt.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import re

_SHA = re.compile(r'[a-f0-9]{64}\Z')


class SourceReceiptIdentityError(ValueError):
    """The exact source identity proof is missing, conflicting or ambiguous."""


def _fail(reason):
    raise SourceReceiptIdentityError(reason)


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _valid_sha(value):
    return isinstance(value, str) and _SHA.fullmatch(value) is not None


def _json(data):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out: _fail('Duplicate field in bound source payload: ' + key)
            out[key] = value
        return out
    def nonfinite(value): _fail('Nonfinite value in bound source payload: ' + value)
    try:
        return json.loads(data, object_pairs_hook=unique, parse_constant=nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        _fail('Bound source payload is not valid UTF-8 JSON: ' + str(exc))


def _bindings(entries):
    if not isinstance(entries, list): _fail('Expected exact material binding list')
    bindings = {}
    for entry in entries:
        if not isinstance(entry, dict): _fail('Malformed material binding')
        path, sha, size = entry.get('path'), entry.get('sha256'), entry.get('bytes')
        if not isinstance(path, str) or not Path(path).is_absolute() or not _valid_sha(sha):
            _fail('Material binding has no absolute path or valid SHA')
        if type(size) is not int or size < 0: _fail('Material binding has no exact byte count')
        resolved = Path(path).resolve()
        if resolved in bindings: _fail('Duplicate material binding path')
        bindings[resolved] = entry
    return bindings


def _verified_file(path, expected_sha, bindings, cache):
    path = Path(path).resolve()
    entry = bindings.get(path)
    if entry is None or entry['sha256'] != expected_sha:
        _fail('Source identity file is outside its exact frozen binding: ' + str(path))
    if path not in cache:
        try:
            data = path.read_bytes()
        except OSError as exc:
            _fail('Bound source identity file cannot be read: ' + str(exc))
        if len(data) != entry['bytes'] or _digest(data) != expected_sha:
            _fail('Bound source identity file byte count or SHA differs: ' + str(path))
        cache[path] = data
    return cache[path], copy.deepcopy(entry)


def resolve_inventory(bundle, producer_inventory, material_bindings, source_base):
    """Return a receipt inventory copy plus explicit identity-only deltas.

    Every FULLSOURCE entry is checked against its original fulltext payload.
    A missing source SHA is filled only from explicit payload/document identity,
    a verified original snapshot and an exact verified source payload file.
    Conflicting existing identities fail; unrelated inventory entries stay exact.
    No event's claimed SHA is used to create its own expected identity.
    """
    if not isinstance(bundle, dict) or not isinstance(producer_inventory, list):
        _fail('Expected original source bundle and producer inventory')
    if not isinstance(source_base, (str, Path)) or not Path(source_base).is_absolute():
        _fail('Expected configured absolute source base')
    base = Path(source_base).resolve()
    payloads = bundle.get('source_full_text_resources')
    documents = bundle.get('source_documents')
    if not isinstance(payloads, list) or not isinstance(documents, list):
        _fail('Original fulltext resources or document identities are absent')
    bindings = _bindings(material_bindings)
    cache, deltas, seen = {}, [], set()
    resolved = copy.deepcopy(producer_inventory)
    for index, original in enumerate(producer_inventory):
        if not isinstance(original, dict): _fail('Malformed producer inventory entry')
        resource_id = original.get('resource_id')
        if not isinstance(resource_id, str) or not resource_id.startswith('FULLSOURCE-'):
            continue
        if resource_id in seen: _fail('Ambiguous duplicate FULLSOURCE inventory identity')
        seen.add(resource_id)
        matches = []
        for payload_index, payload in enumerate(payloads):
            if not isinstance(payload, dict): _fail('Malformed original fulltext payload')
            payload_view_sha = _digest(_canonical(payload).encode('utf-8'))
            if resource_id == 'FULLSOURCE-' + payload_view_sha[:20]:
                matches.append((payload_index, payload, payload_view_sha))
        if len(matches) != 1: _fail('FULLSOURCE inventory does not match one exact original payload')
        payload_index, payload, view_sha = matches[0]
        if original.get('available_views') != {'text': view_sha}:
            _fail('FULLSOURCE view SHA differs from original payload canonical view')
        direct_sha, pdf_sha = payload.get('source_sha256'), payload.get('source_pdf_sha256')
        for value in (direct_sha, pdf_sha):
            if value is not None and not _valid_sha(value): _fail('Explicit source identity SHA is malformed')
        if direct_sha is not None and pdf_sha is not None and direct_sha != pdf_sha:
            _fail('Explicit source SHA and PDF SHA conflict')
        source_sha = direct_sha if direct_sha is not None else pdf_sha
        if source_sha is None: _fail('Original payload has no explicit source identity SHA')
        document_id = 'SOURCE-' + source_sha
        if (payload.get('source_resource_id') != document_id
                or original.get('source_document_id') != document_id):
            _fail('Payload and producer document identities disagree with explicit source SHA')
        if original.get('source_sha256') is not None and original['source_sha256'] != source_sha:
            _fail('Existing producer source SHA conflicts with explicit raw source identity')
        docs = [doc for doc in documents if isinstance(doc, dict)
                and (doc.get('source_resource_id') == document_id or doc.get('source_sha256') == source_sha)]
        if (len(docs) != 1 or docs[0].get('source_resource_id') != document_id
                or docs[0].get('source_sha256') != source_sha):
            _fail('No unique matching original source document identity')
        doc = docs[0]
        snapshot = doc.get('snapshot')
        if not isinstance(snapshot, str) or not Path(snapshot).is_absolute():
            _fail('Original document snapshot path is absent or nonabsolute')
        _, snapshot_binding = _verified_file(snapshot, source_sha, bindings, cache)
        text_resource = doc.get('source_text_resource')
        if not isinstance(text_resource, dict): _fail('Original document has no bound source text resource')
        relative_path, payload_file_sha = text_resource.get('relative_path'), text_resource.get('sha256')
        if (not isinstance(relative_path, str) or not relative_path or Path(relative_path).is_absolute()
                or not _valid_sha(payload_file_sha)):
            _fail('Original source text resource has no relative path and valid SHA')
        if text_resource.get('source_pdf_sha256') is not None and text_resource['source_pdf_sha256'] != source_sha:
            _fail('Source text resource PDF identity conflicts with document identity')
        payload_bytes, payload_binding = _verified_file(base / relative_path, payload_file_sha, bindings, cache)
        file_payload = _json(payload_bytes)
        if file_payload != payload or _canonical(file_payload) != _canonical(payload):
            _fail('Original payload file JSON differs from original source bundle payload')
        if _digest(_canonical(file_payload).encode('utf-8')) != view_sha:
            _fail('Original payload file canonical view differs from producer inventory')
        if original.get('source_sha256') is None:
            resolved[index]['source_sha256'] = source_sha
            deltas.append({'resource_id': resource_id, 'field': 'source_sha256',
                           'producer_value': original.get('source_sha256'), 'resolved_value': source_sha,
                           'resolution_kind': 'explicit_raw_source_identity_with_verified_snapshot_and_payload',
                           'source_document_id': document_id,
                           'source_bundle_pointer': f'/source_full_text_resources/{payload_index}',
                           'payload_canonical_view_sha256': view_sha,
                           'source_snapshot_binding': snapshot_binding,
                           'source_payload_file_binding': payload_binding,
                           'raw_source_text_resource_metadata': copy.deepcopy(text_resource),
                           'producer_inventory_retained_unchanged': True,
                           'read_use_status_changed': False, 'pixel_reading_claimed': False})
    return resolved, deltas
