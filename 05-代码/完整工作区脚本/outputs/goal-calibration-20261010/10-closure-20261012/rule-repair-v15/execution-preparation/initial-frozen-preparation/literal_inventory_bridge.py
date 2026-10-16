"""Neutral missing literal-view projection from frozen JSON/HTML source proof.

Reuse the existing FULLSOURCE identity resolver. Append missing explicit literal
source_texts only; retain old inventory entries, protocol and actual event guard.
This function has no record-ID, decision, event or reference input.
"""
import copy
import hashlib
import json
from pathlib import Path
from interface_common import verify_binding, pointer_value


def _require(ok, message):
    if not ok:
        raise ValueError('literal inventory: ' + message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _source_file(locator, materials, cache):
    path = str(Path(locator['absolute_path']).resolve())
    matches = [b for b in materials if b['path'] == path]
    _require(len(matches) == 1 and matches[0]['sha256'] == locator['sha256'], 'source file outside exact frozen binding')
    if path not in cache:
        cache[path] = verify_binding(matches[0])
    return cache[path]


def _interval(raw, locator, unicode_key, bytes_key):
    pair, byte_pair = locator[unicode_key], locator[bytes_key]
    _require(isinstance(pair, list) and len(pair) == 2 and all(type(v) is int for v in pair), 'invalid Unicode interval')
    _require(isinstance(byte_pair, list) and len(byte_pair) == 2 and all(type(v) is int for v in byte_pair), 'invalid UTF8 interval')
    text = raw.decode('utf8');a, b = pair;x, y = byte_pair
    _require(0 <= a < b <= len(text) and 0 <= x < y <= len(raw), 'interval outside immutable source')
    _require(text[a:b].encode() == raw[x:y], 'Unicode/UTF8 interval disagree')
    return text[a:b], raw[x:y]


def append_literal_entries(bundle, resolved_inventory, materials):
    """Generic form of the adopted five-literal inventory correction; no coding."""
    original = copy.deepcopy(resolved_inventory)
    registry = {item['resource_id']: item for item in original}
    _require(len(registry) == len(original), 'duplicate original inventory ID')
    delta, cache = [], {}
    for di, document in enumerate(bundle['explicit_or_primary_source_resources']):
        for ti, text in enumerate(document.get('source_texts', [])):
            locator = text.get('source_locator', {})
            if locator.get('kind') != 'structured_JSON_and_original_HTML':
                continue
            rid = text['source_resource_id']
            core = {'source_sha256': text['source_sha256'],
                    'available_views': {'text': text['text_sha256']}, 'locator': locator}
            _require(isinstance(text.get('text'), str) and _sha(text['text'].encode()) == text['text_sha256'], 'literal text SHA mismatch')
            if rid in registry:
                _require(all(registry[rid].get(k) == v for k, v in core.items()), 'duplicate literal ID has conflicting source/view/locator')
                continue
            # The existing supported representation gives both exact source
            # coordinate systems. Missing provenance is an error, never a read.
            documents = [d for d in bundle['source_documents'] if
                         d.get('source_resource_id') == text['source_document_resource_id']]
            _require(len(documents) == 1, 'no unique original source document')
            source = documents[0]
            _require(source.get('source_sha256') == document.get('source_sha256') == text['source_sha256'], 'literal/document source identity conflict')
            _require(bool(text.get('source_version_id')) and
                     source.get('source_version_id') == document.get('source_version_id') == text['source_version_id'], 'literal/document version conflict')
            structured, html = locator['structured_snapshot'], locator['raw_html']
            sr = _source_file(structured, materials, cache)
            _require(_sha(sr) == text['source_sha256'], 'structured source SHA differs')
            actual = pointer_value(json.loads(sr), structured['json_pointer'])
            if 'raw_JSON_string_literal_unicode_interval_half_open' in structured:
                part, _ = _interval(sr, structured, 'raw_JSON_string_literal_unicode_interval_half_open', 'raw_JSON_string_literal_utf8_byte_interval_half_open')
                _require(json.loads(part) == actual == text['text'], 'JSON pointer/literal text mismatch')
            else:
                part, _ = _interval(sr, structured, 'raw_JSON_string_literal_header_unicode_interval_half_open', 'raw_JSON_string_literal_header_utf8_byte_interval_half_open')
                a, b = structured['literal_prefix_character_range_0based_halfopen']
                _require(type(a) is int and type(b) is int and a == 0 and 0 < b <= len(actual), 'invalid literal header prefix')
                _require(actual[a:b] == part == text['text'], 'JSON header prefix mismatch')
            hr = _source_file(html, materials, cache)
            part, fragment = _interval(hr, html, 'raw_unicode_interval_half_open', 'raw_utf8_byte_interval_half_open')
            if 'outer_html_sha256_utf8' in html:
                _require(_sha(fragment) == html['outer_html_sha256_utf8'], 'HTML exact finite fragment SHA mismatch')
            else:
                _require(part == text['text'], 'HTML printed header differs')
            pointer = f'/explicit_or_primary_source_resources/{di}/source_texts/{ti}'
            item = {'resource_id': rid, 'source_document_id': text['source_document_resource_id'],
                    **copy.deepcopy(core), 'role': text.get('role'),
                    'representation': text.get('representation'), 'projection_pointer': pointer,
                    'availability_status': 'available', 'consumer_read_status': 'not_recorded',
                    'consumer_use_status': 'not_recorded'}
            registry[rid] = item
            delta.append({'kind': 'independently_bound_missing_explicit_literal_view',
                          'resource_id': rid, 'source_bundle_pointer': pointer,
                          'source_version_id': text['source_version_id'], 'added_entry': copy.deepcopy(item),
                          'expected_identity_from_events': False, 'read_or_use_attested': False})
    extended = list(registry.values())
    _require(extended[:len(original)] == original, 'original inventory changed')
    return extended, delta


def resolve_complete_inventory(bundle, producer_inventory, materials, source_base):
    # Lazy import only after the unchanged driver freezes and loads all coders.
    from source_receipts import resolve_inventory
    resolved, identity_delta = resolve_inventory(bundle, producer_inventory, materials, source_base)
    extended, literal_delta = append_literal_entries(bundle, resolved, materials)
    return extended, identity_delta + literal_delta
