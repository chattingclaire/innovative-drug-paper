"""Finite, source-only equivalent of the approved v12 default complete bundle.

Only approved record rows are JSON-decoded. All original bundle fields remain
available; neutral evidence handles never assert applicability or pixel reading.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import re
from pathlib import Path

CANON_SHA = 'c417474ecbd801f1ea0f784f96dad23bf88b7ac00b12780e3ce67c3cbb8f2764'
MANIFEST_SHA = '0fa14322edbd614496b014be77144701d052ebde6d41383b788b9e6712b63797'
SEAL_SHA = '68b62081c523f3e22ae5830887b073f50ef79a02c0143a4608630355a4b7f426'
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
        result.append(copy.deepcopy(bundle))
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
    group_union = list(dict.fromkeys(rid for group in scope['scopes'].values() for rid in group))
    if ids != group_union: _fail('scope', 'approved IDs differ from named source scopes')
    base = Path(scope['v12_source_base']).resolve()
    if expected.get(str(base / 'delivery-seal-v12.json')) != SEAL_SHA: _fail('scope', 'unapproved v12 seal')
    audit = {}
    bundles = _assemble(base, ids, expected, cache, audit)
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
        if kind == 'visual_source_text':
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
        for key in ('heading_path', 'source_paragraph_id', 'role', 'representation'):
            if key in text: structure[key] = copy.deepcopy(text[key])
        if text.get('role') is not None: structure['source_role'] = text['role']
        if resource_id is not None: structure.setdefault('source_paragraph_id', resource_id)
        contexts.append({'context_id': cid, 'kind': kind, 'text': text['text'],
                         'source_document': ref['source_resource_id'], 'source_ref': ref, 'structure': structure})
        origins[cid] = origin
    return contexts, origins


def semantic_unit(bundle):
    """Preserve raw current fields and expose neutral resources without record IDs."""
    if not isinstance(bundle, dict) or set(bundle) != BUNDLE_KEYS: _fail('bundle', 'expected complete source bundle')
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


def source_inventory(b):
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
