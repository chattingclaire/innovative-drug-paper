"""Finite, source-only equivalent of the approved v13 default complete bundle.

Only approved record rows are JSON-decoded. All original bundle fields remain
available; neutral evidence handles never assert applicability or pixel reading.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import re
from html.parser import HTMLParser
from pathlib import Path

CANON_SHA = 'c417474ecbd801f1ea0f784f96dad23bf88b7ac00b12780e3ce67c3cbb8f2764'
MANIFEST_SHA = '0fa14322edbd614496b014be77144701d052ebde6d41383b788b9e6712b63797'
SEAL_SHA = '68b62081c523f3e22ae5830887b073f50ef79a02c0143a4608630355a4b7f426'
V13_SEAL_SHA = 'c34f1365ed771c7e36ef1d941591e3b715844e34cdc9eb8fd20e05880a3b6620'
V13_MANIFEST_SHA = 'd3d1e365e9756ed8334ed3cce4941a28c18d0735f7b856aeec7fe139e40fd0d3'
_SHA = re.compile(r'[a-f0-9]{64}\Z')
_ID_PREFIX = re.compile(rb'^\s*\{\s*"id"\s*:\s*"(RECODE25-[0-9]{5})"\s*[,}]')
BUNDLE_KEYS = {'common_source_bundle_version', 'source_record', 'source_documents',
               'explicit_or_primary_source_resources', 'preserved_historical_neutral_source_supplements',
               'source_full_text_resources', 'source_asset_locations', 'source_locator_bases',
               'source_reference_index', 'source_provenance_addenda'}

class PacketInterfaceError(ValueError):
    """A source shape, finite scope or exact byte binding is unsupported."""


def _fail(path, reason):
    raise PacketInterfaceError(f'{path}: {reason}')


def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def h(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _json(data, path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out: _fail(path, 'duplicate JSON field: ' + key)
            out[key] = value
        return out
    def nonfinite(value): _fail(path, 'nonfinite JSON constant: ' + value)
    return json.loads(data, object_pairs_hook=unique, parse_constant=nonfinite)


def _top_strings(line):
    """Byte envelope identities only; no JSON decode of unselected records."""
    depth, i, out = 0, 0, {}
    while i < len(line):
        byte = line[i]
        if byte == 34:
            j = i + 1
            while j < len(line):
                if line[j] == 92: j += 2; continue
                if line[j] == 34: break
                j += 1
            key = line[i+1:j]
            k = j + 1
            while k < len(line) and line[k] in b' \t\r\n': k += 1
            if depth == 1 and k < len(line) and line[k] == 58:
                k += 1
                while k < len(line) and line[k] in b' \t\r\n': k += 1
                if k < len(line) and line[k] == 34:
                    z = k + 1
                    while z < len(line):
                        if line[z] == 92: z += 2; continue
                        if line[z] == 34: break
                        z += 1
                    out[key] = line[k+1:z]
            i = j + 1
            continue
        if byte in (123, 91): depth += 1
        elif byte in (125, 93): depth -= 1
        i += 1
    return out


def _select_records(data, approved_ids):
    approved = {rid.encode('ascii') for rid in approved_ids}
    if len(approved) != len(approved_ids): _fail('scope', 'duplicate approved record ID')
    selected = {}
    for number, line in enumerate(data.splitlines(), 1):
        if not line.strip(): continue
        match = _ID_PREFIX.match(line)
        if match is None: _fail(f'canonical:{number}', 'unrecognized ID byte envelope; no row decoded')
        if match.group(1) not in approved: continue
        row = _json(line, f'canonical:{number}')
        rid = row.get('id')
        if rid.encode('ascii') != match.group(1): _fail('canonical', 'identity changed during decode')
        if rid in selected: _fail('canonical', 'duplicate selected record ID')
        selected[rid] = row
    if set(selected) != set(approved_ids): _fail('canonical', 'approved record is absent')
    return [selected[rid] for rid in approved_ids]


def _select_rows(data, identities, path):
    wanted = {key.encode(): {str(value).encode() for value in values} for key, values in identities.items()}
    return [_json(line, path) for line in data.splitlines() if line.strip()
            and any(_top_strings(line).get(key) in values for key, values in wanted.items())]


def _guard(value, forbidden, path='$'):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden or key.startswith('machine_') or key.startswith('original_coder_'):
                _fail(path + '/' + key, 'coding/result field forbidden in source input')
            _guard(child, forbidden, path + '/' + key)
    elif isinstance(value, list):
        for i, child in enumerate(value): _guard(child, forbidden, f'{path}/{i}')
    elif isinstance(value, float) and not math.isfinite(value): _fail(path, 'nonfinite source value')


def _validate_schema(value, rule, schema, path='$'):
    if '$ref' in rule:
        target = schema
        for part in rule['$ref'].removeprefix('#/').split('/'): target = target[part]
        return _validate_schema(value, target, schema, path)
    if 'type' in rule:
        types = rule['type'] if isinstance(rule['type'], list) else [rule['type']]
        valid = {'object': isinstance(value, dict), 'array': isinstance(value, list),
                 'string': isinstance(value, str), 'integer': type(value) is int,
                 'number': type(value) in (int, float), 'boolean': type(value) is bool, 'null': value is None}
        if not any(valid.get(kind, False) for kind in types): _fail(path, 'wrong approved schema type')
    if 'enum' in rule and value not in rule['enum']: _fail(path, 'value outside approved enum')
    if 'const' in rule and value != rule['const']: _fail(path, 'value differs from approved constant')
    if isinstance(value, str) and 'pattern' in rule and not re.search(rule['pattern'], value):
        _fail(path, 'value differs from approved pattern')
    if type(value) in (int, float) and 'minimum' in rule and value < rule['minimum']:
        _fail(path, 'value below approved minimum')
    if isinstance(value, dict):
        if set(rule.get('required', [])) - set(value): _fail(path, 'required source fields absent')
        properties = rule.get('properties', {})
        if rule.get('additionalProperties') is False and set(value) - set(properties):
            _fail(path, 'unknown source fields require schema review')
        for key, child in value.items():
            if key in properties: _validate_schema(child, properties[key], schema, path + '/' + key)
    if isinstance(value, list) and 'items' in rule:
        for i, child in enumerate(value): _validate_schema(child, rule['items'], schema, f'{path}/{i}')


def _checked(path, sha, cache):
    path = Path(path).resolve()
    if not _SHA.fullmatch(sha): _fail(str(path), 'invalid source SHA binding')
    if path in cache:
        data = cache[path]
    else:
        data = path.read_bytes()
        cache[path] = data
    if hashlib.sha256(data).hexdigest() != sha: _fail(str(path), 'source SHA mismatch')
    return data


def _assemble(base, approved_ids, expected, cache, audit):
    base = Path(base).resolve()
    def read(path, sha=None):
        path = Path(path).resolve()
        binding = expected.get(str(path))
        if binding is None: _fail(str(path), 'dependency outside exact finite binding list')
        if sha is not None and sha != binding: _fail(str(path), 'conflicting source binding')
        return _checked(path, binding, cache)
    def load(name): return _json(read(base / name), name)
    manifest = load('source-material-manifest-v12.json')
    if expected[str(base / 'source-material-manifest-v12.json')] != MANIFEST_SHA:
        _fail('manifest', 'unapproved v12 material manifest')
    for entry in manifest['files']:
        if entry['path'] in expected and expected[entry['path']] != entry['sha256']:
            _fail('manifest', 'scope binding differs from approved source manifest')
    canonical = read(base / 'canonical_source_context-v12.jsonl', CANON_SHA)
    records = _select_records(canonical, approved_ids)
    audit['canonical_json_decoded_record_N'] = len(records)
    audit['canonical_unapproved_record_json_decode_N'] = 0
    needed = {r['source_ref']['sha256'] for r in records} | {c['source_ref']['sha256'] for r in records for c in r['contexts']}
    refs = {x['source_resource_id'] for r in records for x in r.get('source_references', [])}
    histories = _select_rows(read(base.parent / 'prospective-common-supplements-source-only-v3.jsonl'),
                             {'record_id': set(approved_ids)}, 'historical')
    historical_sha = {x['source_sha256'] for x in histories}
    docs = _select_rows(read(base / 'source-document-identities-v12.jsonl'), {'source_sha256': needed}, 'documents')
    lib = _select_rows(read(base / 'source-library/library-v12.jsonl'),
                       {'source_resource_id': refs, 'source_sha256': needed, 'snapshot_sha256': needed | historical_sha}, 'library')
    asset_ids = {x['sha256'] for r in records for x in r.get('source_attachments', [])}
    asset_ids |= {x['sha256'] for d in lib for x in d.get('source_page_assets', [])}
    assets = _select_rows(read(base / 'source-assets-manifest-v12.jsonl'), {'sha256': asset_ids}, 'assets')
    for asset in assets: read(asset['absolute_path'], asset['sha256'])
    reference_index = _select_rows(read(base / 'source-library/reference-index-v12.jsonl'),
                                   {'record_id': set(approved_ids)}, 'source-reference-index')
    locator_bases = load('source-asset-locator-bases-v12.json')
    fulltexts = {}
    for doc in docs:
        item = doc.get('source_text_resource')
        if item:
            path = base / item['relative_path']
            fulltexts[doc['source_sha256']] = _json(read(path, item['sha256']), 'full-source-text')
    provenance = (load('renewal-official-provenance-addendum-v11.json')
                  if any(d.get('source_sha256') == 'd76f3d33e1ea70990992a99ae76371fcc1f99da93078e72b4376265679167a73' for d in lib) else None)
    schema = load('current-source-schema-v12.json')
    visual_schema = load('source-visual-resource-schema-v12.json')
    forbidden = set(schema['x-source-protocol']['recursive_forbidden_exact_keys'])
    result = []
    for row in records:
        _validate_schema(row, schema, schema)
        _guard(row, forbidden)
        need = {row['source_ref']['sha256']} | {c['source_ref']['sha256'] for c in row['contexts']}
        rowdocs = [d for d in docs if d['source_sha256'] in need]
        historical = [x for x in histories if x['record_id'] == row['id']]
        rowrefs = {x['source_resource_id'] for x in row.get('source_references', [])}
        old_sha = {x['source_sha256'] for x in historical}
        rowlib = [d for d in lib if d['source_resource_id'] in rowrefs or d.get('source_sha256') in need
                  or d.get('snapshot_sha256') in need or d.get('snapshot_sha256') in old_sha]
        used_ids = {x['sha256'] for x in row.get('source_attachments', [])}
        used_ids |= {x['sha256'] for d in rowlib for x in d.get('source_page_assets', [])}
        bundle = {'common_source_bundle_version': {'version': 'v12', 'canonical_sha256': CANON_SHA,
                  'material_manifest_sha256': MANIFEST_SHA, 'actual_consumer_read_and_use_status': 'not_recorded'},
                  'source_record': row, 'source_documents': rowdocs, 'explicit_or_primary_source_resources': rowlib,
                  'preserved_historical_neutral_source_supplements': historical,
                  'source_full_text_resources': [fulltexts[d['source_sha256']] for d in rowdocs if d.get('source_text_resource')],
                  'source_asset_locations': [a for a in assets if a['sha256'] in used_ids],
                  'source_locator_bases': locator_bases,
                  'source_reference_index': [x for x in reference_index if x['record_id'] == row['id']],
                  'source_provenance_addenda': [provenance] if any(d.get('source_sha256') ==
                    'd76f3d33e1ea70990992a99ae76371fcc1f99da93078e72b4376265679167a73' for d in rowlib) else []}
        _guard(bundle, forbidden)
        for document in rowlib:
            for visual in document.get('source_visual_text_resources', []):
                _validate_schema(visual, visual_schema, visual_schema, 'source-visual-resource')
        result.append(copy.deepcopy(bundle))
    return result


def _pointer(value, pointer):
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        _fail('source-pointer', 'expected original absolute JSON pointer')
    for part in pointer[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        try:
            value = value[int(part)] if isinstance(value, list) else value[part]
        except (KeyError, IndexError, ValueError, TypeError):
            _fail(pointer, 'original source pointer is absent')
    return value


class _LiteralParagraphs(HTMLParser):
    """Original HTML code-point coordinates and literal visible paragraph text."""
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.text, self.paragraphs, self.active = text, [], None
        self.starts = [0] + [m.end() for m in re.finditer('\n', text)]
        self.feed(text)
        self.close()

    def _offset(self):
        line, column = self.getpos()
        return self.starts[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            if self.active is not None: _fail('raw-HTML', 'ambiguous nested paragraph')
            line, column = self.getpos()
            self.active = {'tag': tag, 'p_element_index_zero_based_document_wide': len(self.paragraphs),
                           'start_line_one_based': line, 'start_column_zero_based': column,
                           'unicode_character_start_zero_based': self._offset(), 'text': []}

    def handle_data(self, data):
        if self.active is not None: self.active['text'].append(data)

    def handle_endtag(self, tag):
        if tag == 'p' and self.active is not None:
            line, column = self.getpos()
            end = self.text.find('>', self._offset())
            if end < 0: _fail('raw-HTML', 'unclosed original paragraph tag')
            self.active.update({'end_tag_line_one_based': line, 'end_tag_column_zero_based': column,
                                'unicode_character_end_exclusive': end + 1})
            outer = self.text[self.active['unicode_character_start_zero_based']:end + 1]
            self.active['outer_html_sha256_utf8'] = h(outer)
            self.active['text'] = ''.join(self.active['text'])
            self.paragraphs.append(self.active)
            self.active = None


def _v13_registry(scope, expected, cache):
    """Verify the sealed extension and its actual JSON/HTML source proof."""
    base = Path(scope['v13_source_base']).resolve()
    if (scope.get('v13_delivery_seal_sha256') != V13_SEAL_SHA
            or scope.get('v13_extension_manifest_sha256') != V13_MANIFEST_SHA):
        _fail('v13', 'unapproved extension seal or manifest')
    def read(path, sha):
        path = Path(path).resolve()
        if expected.get(str(path)) != sha: _fail(str(path), 'extension proof is outside exact binding list')
        return _checked(path, sha, cache)
    seal = _json(read(base / 'delivery-seal.json', V13_SEAL_SHA), 'v13-seal')
    sealed = {Path(z['absolute_path']).name: z for z in seal['output_files']}
    for name in ('source-extension-manifest.json', 'source-resource-registry.json', 'source-resource-index.json',
                 'source_only_interface_v13.py', 'HTML-locator-view-clarification.json'):
        entry = sealed[name]
        if Path(entry['absolute_path']).resolve() != base / name:
            _fail('v13', 'extension path differs from official seal')
        data = read(entry['absolute_path'], entry['sha256'])
        if len(data) != entry['bytes']: _fail(name, 'sealed extension byte count differs')
    manifest = _json(read(base / 'source-extension-manifest.json', V13_MANIFEST_SHA), 'v13-manifest')
    for entry in ([manifest['base_interface'], manifest['base_material_manifest'], manifest['base_canonical']]
                  + manifest['extension_files'] + manifest['new_source_originals'] + [manifest['source_addendum']]):
        data = read(entry['absolute_path'], entry['sha256'])
        if len(data) != entry['bytes']: _fail(entry['absolute_path'], 'extension source byte count differs')
    registry_entry = next(z for z in manifest['extension_files']
                          if Path(z['absolute_path']).name == 'source-resource-registry.json')
    registry = _json(read(registry_entry['absolute_path'], registry_entry['sha256']), 'v13-registry')
    source_sha = registry['binding_source_sha256']
    document = registry['document_resource']
    paragraphs = registry['paragraph_resources']
    if (not _SHA.fullmatch(source_sha) or registry['source_document_resource_id'] != 'SOURCE-' + source_sha
            or document['source_document_resource_id'] != 'SOURCE-' + source_sha
            or document['source_sha256'] != source_sha or document['source_texts'] != paragraphs):
        _fail('v13-registry', 'conflicting paragraph/document identity')
    originals = registry['original_source_assets']
    verified = {}
    for kind, entry in originals.items():
        data = read(entry['absolute_path'], entry['sha256'])
        if len(data) != entry['bytes']: _fail(kind, 'original source byte count differs')
        verified[kind] = data
    structured = _json(verified['structured_snapshot'], 'v13-original-JSON')
    try:
        raw_html = verified['raw_html'].decode('utf-8')
    except UnicodeError:
        _fail('v13-original-HTML', 'original HTML is not UTF-8')
    html = _LiteralParagraphs(raw_html)
    addendum_entry = registry['original_addendum_binding']
    addendum = _json(read(addendum_entry['absolute_path'], addendum_entry['sha256']), 'v13-original-addendum')
    ids = set()
    for paragraph in paragraphs:
        rid, locator = paragraph['source_resource_id'], paragraph['source_locator']
        if rid in ids: _fail('v13-registry', 'duplicate paragraph resource identity')
        ids.add(rid)
        if (paragraph['source_sha256'] != source_sha
                or paragraph['source_document_resource_id'] != 'SOURCE-' + source_sha
                or paragraph['text_sha256'] != h(paragraph['text'])
                or locator['kind'] != 'structured_JSON_and_original_HTML'):
            _fail(rid, 'paragraph literal text or source identity differs')
        snapshot, raw = locator['structured_snapshot'], locator['raw_html']
        for entry, original in ((snapshot, originals['structured_snapshot']), (raw, originals['raw_html'])):
            if entry['absolute_path'] != original['absolute_path'] or entry['sha256'] != original['sha256']:
                _fail(rid, 'paragraph locator differs from actual original source binding')
        if _pointer(structured, snapshot['json_pointer']) != paragraph['text']:
            _fail(rid, 'literal paragraph differs from original JSON pointer')
        if snapshot['json_pointer'] != '/normative_paragraphs/' + str(snapshot['normative_paragraphs_index_zero_based']):
            _fail(rid, 'original paragraph index and pointer conflict')
        location = raw['locator']
        index = location['p_element_index_zero_based_document_wide']
        if type(index) is not int or not 0 <= index < len(html.paragraphs):
            _fail(rid, 'original HTML paragraph index is absent')
        actual = html.paragraphs[index]
        if {key: actual[key] for key in location} != location or actual['text'] != paragraph['text']:
            _fail(rid, 'literal paragraph or raw-byte UTF-8 HTML locator differs')
        provenance = paragraph['neutral_extraction_provenance']
        if (provenance['addendum_absolute_path'] != addendum_entry['absolute_path']
                or provenance['addendum_sha256'] != addendum_entry['sha256']
                or _pointer(addendum, provenance['addendum_json_pointer'])['text'] != paragraph['text']
                or paragraph['bound_original_table_image_sha256'] != originals['shared_original_table_jpg']['sha256']):
            _fail(rid, 'paragraph original provenance binding differs')
    groups = document['ordered_article_groups']
    ordered = [rid for group in groups for rid in group['ordered_source_resource_ids']]
    if ordered != [paragraph['source_resource_id'] for paragraph in paragraphs]:
        _fail('v13-registry', 'original ordered article group membership differs')
    return registry


def _extend_bundle(old_bundle, registry):
    """Exact official v13 source-SHA availability extension, without lookup."""
    record = old_bundle['source_record']
    source_shas = {record['source_ref']['sha256']} | {z['source_ref']['sha256'] for z in record['contexts']}
    if registry['binding_source_sha256'] not in source_shas: return old_bundle
    result = copy.deepcopy(old_bundle)
    result['explicit_or_primary_source_resources'].append(copy.deepcopy(registry['document_resource']))
    result['source_full_text_resources'].extend(copy.deepcopy(registry['paragraph_resources']))
    result['source_bundle_extension'] = {
        'version': 'v13-source-addendum', 'base_bundle_version': 'v12', 'old_bundle_sha256': h(cj(old_bundle)),
        'extension_manifest_sha256': V13_MANIFEST_SHA, 'binding_source_sha256': registry['binding_source_sha256'],
        'available_added_paragraph_resource_N': len(registry['paragraph_resources']),
        'availability_scope': 'document-SHA inventory; applicability requires current-source reading',
        'actual_consumer_read_status': 'not_recorded', 'actual_consumer_use_status': 'not_recorded',
    }
    return result


def load_scope(scope_manifest_path):
    """Return complete raw bundles for exact finite IDs, never the full frame."""
    scope_path = Path(scope_manifest_path).resolve()
    scope_bytes = scope_path.read_bytes()
    scope = _json(scope_bytes, 'scope-manifest')
    expected = {}
    cache = {}
    for entry in scope['bindings']:
        path = Path(entry['path']).resolve()
        if not Path(entry['path']).is_absolute() or str(path) in expected:
            _fail('scope/bindings', 'nonabsolute or duplicate dependency path')
        expected[str(path)] = entry['sha256']
        data = _checked(path, entry['sha256'], cache)
        if len(data) != entry['bytes']: _fail(str(path), 'dependency byte count mismatch')
    ids = scope['approved_record_ids']
    authorization = scope['finite_scope_authorization']
    authorization_path = str(Path(authorization['path']).resolve())
    if expected.get(authorization_path) != authorization['sha256']:
        _fail('scope', 'parent finite scope authorization is not bound')
    parent_scope = _json(cache[Path(authorization_path)], 'parent-finite-scope')
    if scope['scopes'] != parent_scope['scopes']:
        _fail('scope', 'named scopes differ from parent source authorization')
    group_union = list(dict.fromkeys(rid for group in scope['scopes'].values() for rid in group))
    if ids != group_union: _fail('scope', 'approved IDs differ from named source scopes')
    base = Path(scope['v12_source_base']).resolve()
    if expected.get(str(base / 'delivery-seal-v12.json')) != SEAL_SHA: _fail('scope', 'unapproved v12 seal')
    audit = {}
    bundles = _assemble(base, ids, expected, cache, audit)
    if 'v13_source_base' in scope:
        if h(cj(bundles) + '\n') != scope['base_complete_bundles_canonical_sha256']:
            _fail('scope', 'base v12 complete bundle content differs')
        registry = _v13_registry(scope, expected, cache)
        bundles = [_extend_bundle(bundle, registry) for bundle in bundles]
    if hashlib.sha256((cj(bundles) + '\n').encode()).hexdigest() != scope['complete_bundles_canonical_sha256']:
        _fail('scope', 'complete bundle content differs from finite preparation')
    if scope_path.read_bytes() != scope_bytes: _fail('scope', 'scope manifest changed during loading')
    return bundles


def _derived_contexts(bundle):
    """Exact source text handles; candidate availability conveys no applicability."""
    raw = bundle['source_record']['contexts']
    contexts, origins = [], {}
    candidates = []
    for di, doc in enumerate(bundle['explicit_or_primary_source_resources']):
        for ti, text in enumerate(doc.get('source_texts', [])):
            candidates.append((text, doc, f'/explicit_or_primary_source_resources/{di}/source_texts/{ti}', 'source_resource_text'))
        for ti, text in enumerate(doc.get('source_visual_text_resources', [])):
            candidates.append((text, doc, f'/explicit_or_primary_source_resources/{di}/source_visual_text_resources/{ti}', 'visual_source_text'))
    for hi, text in enumerate(bundle['preserved_historical_neutral_source_supplements']):
        candidates.append((text, text, f'/preserved_historical_neutral_source_supplements/{hi}', 'historical_source_fragment'))
    for fi, doc in enumerate(bundle['source_full_text_resources']):
        if doc.get('source_locator', {}).get('kind') == 'structured_JSON_and_original_HTML':
            candidates.append((doc, doc, f'/source_full_text_resources/{fi}', 'source_resource_text'))
        for pi, text in enumerate(doc.get('paragraphs', doc.get('source_texts', []))):
            candidates.append((text, doc, f'/source_full_text_resources/{fi}/' + ('paragraphs' if 'paragraphs' in doc else 'source_texts') + f'/{pi}', 'source_resource_text'))
    for text, doc, pointer, kind in candidates:
        if not isinstance(text, dict) or not isinstance(text.get('text'), str):
            _fail(pointer, 'source text candidate has unsupported raw shape')
        sha = text.get('source_sha256', doc.get('source_sha256', doc.get('source_pdf_sha256', doc.get('snapshot_sha256'))))
        ref = copy.deepcopy(text.get('source_ref'))
        if ref is None:
            ref = {'sha256': sha, 'source_resource_id': text.get('source_document_resource_id', 'SOURCE-' + str(sha)),
                   'locator': copy.deepcopy(text.get('source_locator', text.get('locator',
                                {'physical_pages': text.get('physical_pages', [])})))}
        if not isinstance(ref.get('sha256'), str) or not _SHA.fullmatch(ref['sha256']):
            _fail(pointer, 'source text candidate has no bound document SHA')
        resource_id = text.get('source_resource_id', text.get('source_paragraph_id', text.get('supplement_id', doc.get('source_resource_id'))))
        original = [c for c in raw if c.get('text') == text['text'] and c['source_ref']['sha256'] == ref['sha256']
                    and resource_id is not None and resource_id in
                    (c.get('structure', {}).get('source_paragraph_id'), c['source_ref']['locator'].get('source_paragraph_id'))]
        origin = {'source_resource_id': resource_id, 'source_bundle_pointer': pointer,
                  'role': text.get('role'), 'representation': text.get('representation', text.get('kind')),
                  'source_sha256': ref['sha256'], 'document_resource_id': doc.get('source_resource_id')}
        if kind == 'visual_source_text' or text.get('source_locator', {}).get('kind') == 'structured_JSON_and_original_HTML':
            inventory_id, view, view_sha = resource_id, 'text', text['text_sha256']
            origin['origin_inventory_consumption_scope'] = 'complete_literal_text_view'
        elif kind == 'historical_source_fragment':
            inventory_id, view, view_sha = 'HISTORICALSOURCE-' + h(cj(text))[:20], 'text', h(cj(text))
            origin['origin_inventory_consumption_scope'] = 'partial_exact_text_field_of_payload'
        elif pointer.startswith('/source_full_text_resources/'):
            inventory_id, view, view_sha = 'FULLSOURCE-' + h(cj(doc))[:20], 'text', h(cj(doc))
            origin['origin_inventory_consumption_scope'] = 'partial_exact_text_field_of_payload'
        else:
            inventory_id, view, view_sha = doc['source_resource_id'], 'document_bundle', h(cj(doc))
            origin['origin_inventory_consumption_scope'] = 'partial_exact_text_field_of_document_bundle'
        origin.update({'origin_inventory_resource_id': inventory_id,
                       'origin_inventory_view': view, 'origin_inventory_view_sha256': view_sha})
        if original:
            for context in original:
                origins.setdefault(context['context_id'], origin)
            continue
        identity = {'source_resource_id': resource_id, 'source_ref': ref, 'text': text['text'],
                    'role': text.get('role'), 'representation': text.get('representation', text.get('kind'))}
        cid = 'CTX-DERIVED-' + h(cj(identity))[:24]
        if cid in origins: continue
        structure = {'source_resource_id': resource_id, 'source_bundle_pointer': pointer}
        for key in ('heading_path', 'source_paragraph_id', 'role', 'representation', 'article', 'clause_index_one_based'):
            if key in text: structure[key] = copy.deepcopy(text[key])
        if text.get('role') is not None: structure['source_role'] = text['role']
        if resource_id is not None: structure.setdefault('source_paragraph_id', resource_id)
        contexts.append({'context_id': cid, 'kind': kind, 'text': text['text'],
                         'source_document': ref['source_resource_id'], 'source_ref': ref, 'structure': structure})
        origins[cid] = origin
    return contexts, origins


def semantic_unit(bundle):
    """Preserve raw current fields and expose neutral resources without record IDs."""
    if not isinstance(bundle, dict) or set(bundle) not in (BUNDLE_KEYS, BUNDLE_KEYS | {'source_bundle_extension'}):
        _fail('bundle', 'expected complete source bundle')
    row = bundle['source_record']
    unit = {key: copy.deepcopy(value) for key, value in row.items() if key != 'id'}
    unit['attachments'] = copy.deepcopy(row.get('source_attachments', []))
    semantic_bundle = copy.deepcopy(bundle)
    semantic_bundle['source_record'].pop('id', None)
    for field in ('preserved_historical_neutral_source_supplements', 'source_reference_index'):
        for item in semantic_bundle[field]: item.pop('record_id', None)
    unit['source_bundle'] = semantic_bundle
    derived, origins = _derived_contexts(bundle)
    unit['contexts'].extend(derived)
    unit['derived_context_origins'] = origins
    return unit


def _v12_source_inventory(b):
 """Describe available views, never claim the consumer read or used them."""
 inv=[];r=b['source_record'];s=r['source_ref']['sha256']
 inv.append({'resource_id':'BODY-'+r['id'],'source_document_id':'SOURCE-'+s,'source_sha256':s,'locator':r['source_ref']['locator'],'available_views':{'text':h(r['text'])},'availability_status':'available','representation':r.get('body_source_representation',{'kind':'current_source_body'}),'consumer_read_status':'not_recorded'})
 for n in r['contexts']:
  views={'geometry':h(cj(n['structure']))};fields={k:n[k] for k in ['text','title','caption','headers','row_cells'] if k in n}
  if fields:views['text']=h(cj(fields))
  inv.append({'resource_id':n['context_id'],'source_document_id':n['source_ref']['source_resource_id'],'source_sha256':n['source_ref']['sha256'],'locator':n['source_ref']['locator'],'available_views':views,'availability_status':'available','representation':n['kind'],'consumer_read_status':'not_recorded'})
 for d in b['explicit_or_primary_source_resources']:
  ds=d.get('source_sha256',d.get('snapshot_sha256'));inv.append({'resource_id':d['source_resource_id'],'source_document_id':d['source_resource_id'],'source_sha256':ds,'locator':{'document_resource_id':d['source_resource_id']},'available_views':{'document_bundle':h(cj(d))},'availability_status':'available','representation':'source_document_resource; applicability_scope_requires_source_read','consumer_read_status':'not_recorded'})
  for z in d.get('source_visual_text_resources',[]):
   inv.append({'resource_id':z['source_resource_id'],'source_document_id':z['source_document_resource_id'],'source_sha256':z['source_sha256'],'locator':z['source_locator'],'available_views':{'text':z['text_sha256']},'availability_status':'available','representation':z['representation'],'role':z['role'],'production_read_provenance':z['source_review_provenance'],'consumer_read_status':'not_recorded'})
  for z in d.get('source_display_regions',[]):
   inv.append({'resource_id':z['region_id'],'source_document_id':'SOURCE-'+z['source_sha256'],'source_sha256':z['source_sha256'],'locator':{'physical_page':z['physical_page'],'coordinate_system':z['coordinate_system'],'bbox_points_xyxy':z['bbox_points_xyxy']},'available_views':{'geometry':h(cj(z))},'availability_status':'available','representation':'pure_display_region_manual_padded','consumer_read_status':'not_recorded'})
 for z in b['preserved_historical_neutral_source_supplements']:
  inv.append({'resource_id':'HISTORICALSOURCE-'+h(cj(z))[:20],'source_document_id':'SOURCE-'+z['source_sha256'],'source_sha256':z['source_sha256'],'locator':z.get('source_locator',{}),'available_views':{'text':h(cj(z))},'availability_status':'available','representation':'previously_shared_neutral_source_fragment','consumer_read_status':'not_recorded'})
 for z in b['source_full_text_resources']:
  inv.append({'resource_id':'FULLSOURCE-'+h(cj(z))[:20],'source_document_id':z.get('source_resource_id'),'source_sha256':z.get('source_sha256'),'locator':{'representation':'source_full_text_resource_payload'},'available_views':{'text':h(cj(z))},'availability_status':'available','representation':'source_full_text_resource; scope_requires_source_read','consumer_read_status':'not_recorded'})
 for a in b['source_asset_locations']:
  inv.append({'resource_id':a['attachment_id'],'source_document_id':'SOURCE-'+a.get('source_pdf_sha256',s),'source_sha256':a.get('source_pdf_sha256',s),'locator':{'absolute_path':a['absolute_path'],'physical_page':a.get('physical_page')},'available_views':{'image':a['sha256']},'availability_status':'available_SHA_matched','representation':a.get('kind','original_source_asset'),'consumer_read_status':'not_recorded'})
 seen={};out=[]
 for z in inv:
  if z['resource_id'] in seen:
   if cj(z)!=cj(seen[z['resource_id']]):
    old=seen[z['resource_id']]
    if old['available_views']!=z['available_views'] or old['source_sha256']!=z['source_sha256'] or old['locator'].get('physical_page')!=z['locator'].get('physical_page'):raise ValueError('conflicting resource ID')
    old['locator'].setdefault('alternate_absolute_paths',[]).append(z['locator']['absolute_path'])
  else:seen[z['resource_id']]=z;out.append(z)
 return out


def source_inventory(bundle):
    """Keep old inventories; describe literal JSON/HTML paragraphs without invented page geometry."""
    paragraphs = [z for z in bundle['source_full_text_resources']
                  if isinstance(z, dict) and isinstance(z.get('source_locator'), dict)
                  and z['source_locator'].get('kind') == 'structured_JSON_and_original_HTML']
    base_view = dict(bundle)
    base_view['source_full_text_resources'] = [z for z in bundle['source_full_text_resources']
                                              if z not in paragraphs]
    inventory = _v12_source_inventory(base_view)
    for z in paragraphs:
        inventory.append({
            'resource_id': z['source_resource_id'],
            'source_document_id': z['source_document_resource_id'],
            'source_sha256': z['source_sha256'],
            'locator': copy.deepcopy(z['source_locator']),
            'available_views': {'text': z['text_sha256']},
            'availability_status': 'available',
            'representation': z['representation'],
            'role': z['role'],
            'consumer_read_status': 'not_recorded',
            'consumer_use_status': 'not_recorded',
        })
    if len({z['resource_id'] for z in inventory}) != len(inventory):
        raise ValueError('conflicting source resource inventory ID')
    return inventory
