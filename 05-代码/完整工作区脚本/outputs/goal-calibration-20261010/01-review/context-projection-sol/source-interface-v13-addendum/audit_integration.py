"""One finite source/hash/shape scan of the actual 4481 frame, without coding."""
from pathlib import Path
from collections import Counter
from functools import lru_cache
from html.parser import HTMLParser
import datetime, hashlib, json, copy
import source_only_interface_v13 as src

OUT = Path(__file__).resolve().parent
base = src._base
H = lambda value: hashlib.sha256(value).hexdigest()
def bind(path):
    path = Path(path); raw = path.read_bytes()
    return {'absolute_path': str(path), 'sha256': H(raw), 'bytes': len(raw)}
def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

# Audit-local immutable file parsing/hash caches avoid repeatedly parsing the same
# sealed 23MB frame. They do not alter the accessor file or serialized results.
original_checked, original_rows, original_manifest = base.checked, base.rows, base.load_manifest
@lru_cache(maxsize=None)
def checked_cached(path, expected, size, mtime):
    return original_checked(path, expected)
def checked(path, expected):
    path = Path(path); stat = path.stat()
    return checked_cached(str(path), expected, stat.st_size, stat.st_mtime_ns)
@lru_cache(maxsize=None)
def rows_cached(path, size, mtime):
    return original_rows(path)
def rows(path):
    path = Path(path); stat = path.stat()
    return rows_cached(str(path), stat.st_size, stat.st_mtime_ns)
@lru_cache(maxsize=None)
def manifest_cached(size, mtime):
    return original_manifest()
def manifest():
    path = base.OUT / 'source-material-manifest-v12.json'; stat = path.stat()
    return manifest_cached(stat.st_size, stat.st_mtime_ns)
base.checked, base.rows, base.load_manifest = checked, rows, manifest

registry = src.extension_registry()
addition = registry['paragraph_resources']
doc_sha = registry['binding_source_sha256']
addendum = json.loads(Path(registry['original_addendum_binding']['absolute_path']).read_text())
snapshot = json.loads(Path(registry['original_source_assets']['structured_snapshot']['absolute_path']).read_text())
html = Path(registry['original_source_assets']['raw_html']['absolute_path']).read_bytes().decode('utf-8')
class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts = []
    def handle_data(self, value):
        self.parts.append(value)
line_starts = [0] + [i + 1 for i, value in enumerate(html) if value == '\n']
class ParagraphStarts(HTMLParser):
    def __init__(self):
        super().__init__(); self.starts = []
    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            line, column = self.getpos()
            self.starts.append(line_starts[line - 1] + column)
paragraph_starts = ParagraphStarts(); paragraph_starts.feed(html)
paragraph_checks = []
for z in addition:
    loc = z['source_locator']; pointer = loc['structured_snapshot']['json_pointer']
    index = loc['structured_snapshot']['normative_paragraphs_index_zero_based']
    assert pointer == '/normative_paragraphs/' + str(index)
    assert snapshot['normative_paragraphs'][index] == z['text']
    assert H(z['text'].encode()) == z['text_sha256']
    raw_locator = loc['raw_html']['locator']
    start, end = raw_locator['unicode_character_start_zero_based'], raw_locator['unicode_character_end_exclusive']
    outer = html[start:end]
    assert H(outer.encode()) == raw_locator['outer_html_sha256_utf8']
    assert paragraph_starts.starts[raw_locator['p_element_index_zero_based_document_wide']] == start
    assert raw_locator['start_line_one_based'] == html.count('\n', 0, start) + 1
    assert raw_locator['start_column_zero_based'] == start - html.rfind('\n', 0, start) - 1
    end_tag = end - len('</p>'); assert html[end_tag:end] == '</p>'
    assert raw_locator['end_tag_line_one_based'] == html.count('\n', 0, end_tag) + 1
    assert raw_locator['end_tag_column_zero_based'] == end_tag - html.rfind('\n', 0, end_tag) - 1
    visible = Text(); visible.feed(outer)
    assert ''.join(visible.parts) == z['text']
    assert 'physical_page' not in loc and 'normalized_character_interval' not in loc
    paragraph_checks.append({'resource_id': z['source_resource_id'], 'text_utf8_bytes': len(z['text'].encode()),
        'text_sha256': z['text_sha256'], 'structured_JSON_pointer_exact': True,
        'original_HTML_outer_SHA_exact': True, 'original_HTML_visible_text_Unicode_exact': True,
        'original_HTML_raw_UTF8_character_p_index_line_column_exact': True,
        'source_locator': loc, 'no_normalization_or_invented_PDF_page': True})

canonical = base.OUT / 'canonical_source_context-v12.jsonl'
raw_lines = canonical.read_bytes().splitlines()
frame = [json.loads(line) for line in raw_lines]
assert len(frame) == 4481 and len({r['id'] for r in frame}) == 4481
forbidden = set(json.loads((base.OUT / 'current-source-schema-v12.json').read_text())
                ['x-source-protocol']['recursive_forbidden_exact_keys'])
shapes, violations = {}, []
def type_name(value):
    if value is None: return 'null'
    if isinstance(value, bool): return 'boolean'
    if isinstance(value, int): return 'integer'
    if isinstance(value, float): return 'number'
    if isinstance(value, str): return 'string'
    if isinstance(value, list): return 'array'
    if isinstance(value, dict): return 'object'
    raise TypeError(type(value))
def escape(key): return str(key).replace('~', '~0').replace('/', '~1')
def shape(value, path, per_record_paths, record_id):
    slot = shapes.setdefault(path, {'occurrence_N': 0, 'record_N': 0, 'types': Counter()})
    slot['occurrence_N'] += 1; slot['types'][type_name(value)] += 1; per_record_paths.add(path)
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden: violations.append({'id': record_id, 'path': path + '/' + escape(key), 'key': key})
            shape(child, path + '/' + escape(key), per_record_paths, record_id)
    elif isinstance(value, list):
        for child in value: shape(child, path + '/*', per_record_paths, record_id)

bindings, affected = [], []
old_total = new_total = 0
max_bytes, max_id = -1, None
ctx_total = 0
with (OUT / 'affected-common-source-bundles.jsonl').open('w') as affected_stream:
    for position, (record, raw_line) in enumerate(zip(frame, raw_lines), 1):
        rid = record['id']; old = base.lookup(rid, 'model')
        roles = [src.lookup(rid, selector) for selector in ['rule', 'model', 'human']]
        old_json, new_json = src.cj(old), src.cj(roles[0])
        assert new_json == src.cj(roles[1]) == src.cj(roles[2])
        current = roles[0]; assert current['source_record'] == old['source_record'] == record
        old_bytes, new_bytes = len(old_json.encode()), len(new_json.encode())
        source_set = {record['source_ref']['sha256']} | {n['source_ref']['sha256'] for n in record['contexts']}
        changed = doc_sha in source_set
        if changed:
            assert current['explicit_or_primary_source_resources'][:-1] == old['explicit_or_primary_source_resources']
            assert current['explicit_or_primary_source_resources'][-1] == registry['document_resource']
            assert current['source_full_text_resources'][:-len(addition)] == old['source_full_text_resources']
            assert current['source_full_text_resources'][-len(addition):] == addition
            assert set(current) == set(old) | {'source_bundle_extension'}
            for key in set(old) - {'explicit_or_primary_source_resources', 'source_full_text_resources'}:
                assert current[key] == old[key]
            assert current['source_bundle_extension']['old_bundle_sha256'] == H(old_json.encode())
            affected.append(rid); affected_stream.write(new_json + '\n')
        else:
            assert current == old and new_json == old_json
        inventory = src.source_inventory(current)
        assert all(z['consumer_read_status'] == 'not_recorded' for z in inventory)
        if changed:
            indexed = {z['resource_id']: z for z in inventory}
            for paragraph in addition:
                z = indexed[paragraph['source_resource_id']]
                assert z['locator'] == paragraph['source_locator']
                assert z['available_views'] == {'text': paragraph['text_sha256']}
                assert z['consumer_use_status'] == 'not_recorded'
        paths = set(); shape(current, '', paths, rid)
        for path in paths: shapes[path]['record_N'] += 1
        bindings.append({'frame_ordinal_1based': position, 'id': rid,
            'primary_source_sha256': record['source_ref']['sha256'], 'extension_available': changed,
            'old_bundle_sha256': H(old_json.encode()), 'new_bundle_sha256': H(new_json.encode()),
            'old_bundle_utf8_bytes': old_bytes, 'new_bundle_utf8_bytes': new_bytes,
            'added_bundle_utf8_bytes': new_bytes - old_bytes,
            'source_record_object_sha256': H(src.cj(record).encode()),
            'original_canonical_JSONL_record_line_sha256': H(raw_line),
            'body_utf8_sha256': H(record['text'].encode()), 'body_utf8_bytes': len(record['text'].encode()),
            'unchanged_context_object_sha256': H(src.cj(record['contexts']).encode()),
            'unchanged_context_N': len(record['contexts']), 'source_inventory_N': len(inventory),
            'old_source_asset_N_unchanged': len(old['source_asset_locations']),
            'all_rule_model_human_default_bytes_identical': True})
        old_total += old_bytes; new_total += new_bytes; ctx_total += len(record['contexts'])
        if new_bytes > max_bytes: max_bytes, max_id = new_bytes, rid
        if position % 1000 == 0: print('source-only object/bytes scan', position, flush=True)
assert not violations
assert len(affected) == 59
assert canonical.read_bytes() == b'\n'.join(raw_lines) + b'\n'
with (OUT / 'frame-bundle-bindings.jsonl').open('w') as stream:
    for z in bindings: stream.write(src.cj(z) + '\n')
for z in shapes.values(): z['types'] = dict(sorted(z['types'].items()))
order = [r['id'] for r in frame]
dump('field-shape-counts.json', {'scope': 'actual default extended bundle; all4481; no values or text words emitted',
    'path_format': 'JSON Pointer; array elements use *; root is empty string',
    'occurrence_contract': 'Each visited value occurrence, including repeated shared resources in different records; record_N counts distinct bundles containing the path.',
    'frame_N': len(frame), 'frame_ID_order_LF_sha256': H(('\n'.join(order) + '\n').encode()),
    'field_path_N': len(shapes), 'field_paths': dict(sorted(shapes.items()))})
dump('source-interface-QA.json', {'version': 'v13-source-addendum',
    'actual_run_identity': 'gpt-6.1-sol / ultra AI source integration; no coding',
    'base_canonical_binding': bind(canonical), 'base_interface_binding': bind(base.OUT / 'source_only_interface_v12.py'),
    'extension_manifest_binding': bind(OUT / 'source-extension-manifest.json'),
    'source_paragraph_checks': paragraph_checks, 'new_unique_paragraph_resource_N': len(addition),
    'new_unique_paragraph_text_utf8_bytes': sum(z['text_utf8_bytes'] for z in paragraph_checks),
    'affected_source_document_sha256': doc_sha, 'affected_record_N': len(affected), 'affected_ids': affected,
    'frame_N': len(frame), 'unaffected_bundle_byte_identical_N': len(frame) - len(affected),
    'source_record_unchanged_N': len(frame), 'body_changed_N': 0, 'old_context_changed_N': 0,
    'old_context_N': ctx_total, 'all_old_nonextension_root_values_preserved_N': len(frame),
    'rule_model_human_same_default_bundle_N': len(frame), 'forbidden_exact_key_hit_N': len(violations),
    'source_inventory_actual_read_use_not_inferred': True,
    'original_JSON_and_HTML_locators_preserved_no_invented_PDF_locator': True,
    'frame_ID_order_contract': 'UTF8 IDs separated by LF, including final LF',
    'frame_ID_order_LF_sha256': H(('\n'.join(order) + '\n').encode()),
    'frame_ID_array_canonical_JSON_sha256': H(src.cj(order).encode()),
    'default_bundle_byte_contract': 'UTF8 of canonical sorted-key compact JSON with ensure_ascii=False; excludes output trailing LF',
    'old_all_bundle_utf8_bytes': old_total, 'new_all_bundle_utf8_bytes': new_total,
    'added_total_bundle_utf8_bytes': new_total - old_total, 'jsonl_all_bundle_bytes_if_exported': new_total + len(frame),
    'max_single_bundle_utf8_bytes': max_bytes, 'max_single_bundle_record_id': max_id,
    'affected_old_bundle_utf8_bytes_range': [min(z['old_bundle_utf8_bytes'] for z in bindings if z['extension_available']), max(z['old_bundle_utf8_bytes'] for z in bindings if z['extension_available'])],
    'affected_new_bundle_utf8_bytes_range': [min(z['new_bundle_utf8_bytes'] for z in bindings if z['extension_available']), max(z['new_bundle_utf8_bytes'] for z in bindings if z['extension_available'])],
    'per_affected_added_bundle_utf8_bytes_range': [min(z['added_bundle_utf8_bytes'] for z in bindings if z['extension_available']), max(z['added_bundle_utf8_bytes'] for z in bindings if z['extension_available'])],
    'old_v12_manifest_files_after_scan': [bind(z['path']) for z in base.load_manifest()['files']],
    'audit_local_cache': 'Hashes/parsing cached only while this audit process runs, keyed by path+size+mtime. Original accessor source file not modified; originals rebound at audit end.',
    'joint_source_manual_rules_prompt_sampling_freeze': 'not performed',
    'human_validation_or_semantic_certification': 'not performed', 'tokens_or_capacity_guesses': 'none',
    'source_reading_protocol_integration': 'Original v12 protocol remains untouched. Its v12-bound inventory check is not presented as accepting this added v13 inventory until ROOT separately binds the execution contract.'})
for z in base.load_manifest()['files']: original_checked(z['path'], z['sha256'])
for z in src._manifest['extension_files'] + src._manifest['new_source_originals'] + [src._manifest['source_addendum']]:
    assert bind(z['absolute_path'])['sha256'] == z['sha256']
print(json.dumps({'frame': len(frame), 'affected': len(affected), 'new_bundle_total_bytes': new_total,
                  'max_bundle_bytes': max_bytes, 'new_source_text_resources': len(addition)}, ensure_ascii=False), flush=True)
