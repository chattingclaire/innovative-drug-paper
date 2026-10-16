"""Offline, label-free full-bundle builder. No model, sampling or comparison API."""
import argparse
import copy
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
BUNDLE_KEYS = ('source_record', 'source_documents', 'explicit_or_primary_source_resources',
               'preserved_historical_neutral_source_supplements', 'source_full_text_resources',
               'source_asset_locations', 'source_locator_bases', 'common_source_bundle_version',
               'source_reference_index', 'source_provenance_addenda')
CONDITIONS = ('R1', 'R2', 'R3', 'W', 'H')
EXTRA_FORBIDDEN = {'evidence_certificates', 'dimension_certificate', 'reference_labels',
                   'coder_answer', 'expected', 'rule_hit', 'validated_semantics'}
GRAPH_KEYS = {'related_context_ids', 'text_child_context_ids', 'table_text_context_ids',
              'scope_context_ids', 'ordered_context_ids', 'parent_context_id', 'follows_context_id'}
BUDGET_KEYS = ('max_prompt_and_output_bytes', 'reserve_output_bytes', 'max_context_nodes',
               'max_asset_count', 'max_asset_total_bytes', 'max_asset_individual_bytes',
               'max_asset_total_pixels')

class InputFailure(ValueError):
    """Unsupported or incomplete input is a technical failure, never a label/null."""

def require(condition, message):
    if not condition:
        raise InputFailure(message)

def unique_object(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, 'duplicate JSON key: ' + k)
        result[k] = v
    return result

def parse(raw):
    try:
        return json.loads(raw, object_pairs_hook=unique_object,
                          parse_constant=lambda x: (_ for _ in ()).throw(InputFailure('nonfinite JSON number')))
    except (ValueError, UnicodeError) as exc:
        raise InputFailure(str(exc)) from exc

def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError) as exc:
        raise InputFailure('unsupported non-JSON source: ' + str(exc)) from exc

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def valid_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)

def schema_check(value, schema):
    errors = list(Draft202012Validator(schema).iter_errors(value))
    require(not errors, 'schema failure: ' + (str(list(errors[0].path)) + ' ' + errors[0].message if errors else ''))

def walk(value, pointer=''):
    yield pointer, value
    if isinstance(value, dict):
        for key, child in value.items():
            escaped = key.replace('~', '~0').replace('/', '~1')
            yield from walk(child, pointer + '/' + escaped)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, pointer + '/' + str(index))

def type_name(value):
    if value is None: return 'null'
    if type(value) is bool: return 'boolean'
    if type(value) in (int, float): return 'number'
    if isinstance(value, str): return 'string'
    if isinstance(value, dict): return 'object'
    if isinstance(value, list): return 'array'
    raise InputFailure('unsupported Python type')

def profile_from_sealed_shapes(shapes, literal_values, documents):
    """All4481 sealed shape counters; never learn a profile from selected rows."""
    require(shapes['frame_N'] == 4481 and shapes['field_path_N'] == 1298, 'full-frame v13 shape coverage required')
    paths = {}
    fields = shapes['field_paths']
    for path, entry in fields.items():
        prefix = path + '/' if path else '/'
        children = {key[len(prefix):]: value for key, value in fields.items()
                    if key.startswith(prefix) and '/' not in key[len(prefix):] and key[len(prefix):] != '*'}
        object_N = entry['types'].get('object', 0)
        paths['$' + path] = {'types': sorted({'number' if t == 'integer' else t for t in entry['types']}),
                            'keys': sorted(children) if object_N else [],
                            'required_keys': sorted(key for key, child in children.items() if object_N and child['occurrence_N'] == object_N),
                            'literal_values': literal_values.get('$' + path, [])}
    require(set(paths['$']['required_keys']) == set(BUNDLE_KEYS), 'old ten roots must remain required; extension optional')
    return {'profile_version': 'closed-source-shape-1', 'expected_public_documents': documents, 'paths': paths}

def check_profile(value, profile, forbidden):
    lower_forbidden = {k.casefold() for k in forbidden} | EXTRA_FORBIDDEN
    def check(v, path='$'):
        require(path in profile['paths'], 'unsupported source path: ' + path)
        e = profile['paths'][path]
        require(type_name(v) in e['types'], 'unsupported source type at ' + path)
        if e['literal_values']: require(v in e['literal_values'], 'source role/unknown status value changed at ' + path)
        if isinstance(v, dict):
            require(set(v) <= set(e['keys']), 'unsupported source field at ' + path + ': ' + ','.join(sorted(set(v) - set(e['keys']))))
            require(set(e['required_keys']) <= set(v), 'required original source field missing at ' + path)
            for k, child in v.items():
                require(k.casefold() not in lower_forbidden and not k.casefold().startswith('machine_'), 'forbidden source certificate/result key: ' + path + '/' + k)
                check(child, path + '/' + k.replace('~', '~0').replace('/', '~1'))
        elif isinstance(v, list):
            for child in v: check(child, path + '/*')
    canonical(value)
    check(value)

def bounded_path(path, roots):
    p = Path(path)
    require(p.is_absolute(), 'asset/snapshot requires explicit absolute locator')
    resolved = p.resolve(strict=True)
    require(any(resolved.is_relative_to(Path(r).resolve()) for r in roots), 'path outside frozen allowed roots: ' + str(p))
    require(resolved.is_file(), 'not a source file: ' + str(p))
    return resolved

def image_dimensions(raw):
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):
        require(len(raw) >= 24 and raw[12:16] == b'IHDR', 'bad PNG header')
        return 'image/png', *struct.unpack('>II', raw[16:24])
    if raw.startswith(b'\xff\xd8'):
        i = 2
        while i < len(raw):
            if raw[i] != 255: i += 1; continue
            while i < len(raw) and raw[i] == 255: i += 1
            require(i < len(raw), 'bad JPEG marker')
            marker = raw[i]; i += 1
            if marker in [1, 216, 217] or 208 <= marker <= 215: continue
            require(i + 2 <= len(raw), 'bad JPEG length')
            length = int.from_bytes(raw[i:i+2], 'big')
            require(length >= 2 and i + length <= len(raw), 'truncated JPEG segment')
            if marker in [192, 193, 194, 195, 197, 198, 199, 201, 202, 203, 205, 206, 207]:
                require(length >= 7, 'bad JPEG SOF')
                return 'image/jpeg', int.from_bytes(raw[i+5:i+7], 'big'), int.from_bytes(raw[i+3:i+5], 'big')
            i += length
        raise InputFailure('JPEG dimensions unavailable')
    if raw[:4] == b'RIFF' and raw[8:12] == b'WEBP' and raw[12:16] == b'VP8X' and len(raw) >= 30:
        return 'image/webp', 1 + int.from_bytes(raw[24:27], 'little'), 1 + int.from_bytes(raw[27:30], 'little')
    raise InputFailure('unsupported asset encoding; no silent dimension default')

def verified_assets(bundle, roots):
    assets = []; known = {}; locations = set()
    for source_entry in bundle['source_asset_locations']:
        require(valid_sha(source_entry.get('sha256')), 'asset SHA missing')
        p = bounded_path(source_entry.get('absolute_path', ''), roots)
        raw = p.read_bytes(); require(sha(raw) == source_entry['sha256'], 'asset SHA mismatch: ' + str(p))
        mime, width, height = image_dimensions(raw)
        require(width > 0 and height > 0, 'invalid image dimensions')
        entry = {'sha256': sha(raw), 'absolute_path': str(p), 'bytes': len(raw),
                 'mime_type': mime, 'width': width, 'height': height}
        require(entry['sha256'] not in known or all(known[entry['sha256']][k] == entry[k] for k in ['bytes', 'mime_type', 'width', 'height']), 'inconsistent duplicate asset content')
        if (entry['sha256'], entry['absolute_path']) not in locations: assets.append(entry)
        locations.add((entry['sha256'], entry['absolute_path']))
        known[entry['sha256']] = entry
    # Older public-document paragraphs explicitly retain page images outside the
    # accessor asset-list projection. Resolve only their declared original path
    # and SHA against the declared canonical base; never invent a locator.
    for pointer, obj in walk(bundle['explicit_or_primary_source_resources']):
        if not isinstance(obj, dict) or '/source_page_images/' not in pointer: continue
        require(valid_sha(obj.get('sha256')), 'public paragraph image SHA missing')
        if 'absolute_path' in obj:
            locator = obj['absolute_path']
        else:
            base = bundle['source_locator_bases'].get('canonical_row_attachment_relative_path_base')
            require(isinstance(base, str) and Path(base).is_absolute() and isinstance(obj.get('relative_path'), str), 'public paragraph image explicit locator missing')
            locator = str(Path(base) / obj['relative_path'])
        p = bounded_path(locator, roots); raw = p.read_bytes()
        require(sha(raw) == obj['sha256'], 'public paragraph image SHA mismatch')
        mime, width, height = image_dimensions(raw)
        require(width > 0 and height > 0, 'invalid public paragraph image dimensions')
        entry = {'sha256': sha(raw), 'absolute_path': str(p), 'bytes': len(raw), 'mime_type': mime, 'width': width, 'height': height}
        require(entry['sha256'] not in known or all(known[entry['sha256']][k] == entry[k] for k in ['bytes', 'mime_type', 'width', 'height']), 'inconsistent public paragraph image content')
        if (entry['sha256'], entry['absolute_path']) not in locations: assets.append(entry)
        locations.add((entry['sha256'], entry['absolute_path'])); known[entry['sha256']] = entry
    path_to_asset = {a['absolute_path']: a for a in assets}
    source_objects = dict(walk(bundle))
    for pointer, obj in walk(bundle):
        if not isinstance(obj, dict): continue
        image_hash_keys = ('original_page_asset_sha256', 'new_300dpi_asset_sha256', 'source_image_sha256', 'image_sha256')
        for key in image_hash_keys:
            if key in obj: require(obj[key] in known, 'referenced image asset missing at ' + pointer + '/' + key)
        if ('attachment_id' in obj or 'physical_page' in obj and ('relative_path' in obj or 'absolute_path' in obj)) and 'sha256' in obj:
            require(obj['sha256'] in known, 'source attachment/page asset missing at ' + pointer)
        if 'original_page_asset_absolute_path' in obj:
            p = bounded_path(obj['original_page_asset_absolute_path'], roots)
            require(file_sha(p) == obj.get('original_page_asset_sha256'), 'original page absolute locator mismatch')
        if 'new_300dpi_asset_absolute_path' in obj:
            p = bounded_path(obj['new_300dpi_asset_absolute_path'], roots)
            require(file_sha(p) == obj.get('new_300dpi_asset_sha256') and obj.get('new_300dpi_asset_sha256') in known, '300dpi page absolute locator mismatch')
        for key in ('page_asset', 'new_300dpi_asset_relative_path'):
            if key in obj:
                bases = [v for k, v in bundle['source_locator_bases'].items() if (k.endswith('_base') or k.endswith('_base_absolute_path')) and isinstance(v, str)]
                possible = {str((Path(base) / obj[key]).resolve()) for base in bases}
                matches = possible & set(path_to_asset)
                require(matches, 'page region relative locator has no declared absolute asset binding at ' + pointer + '/' + key)
                if key == 'new_300dpi_asset_relative_path':
                    require(any(path_to_asset[p]['sha256'] == obj.get('new_300dpi_asset_sha256') for p in matches), 'relative page path and declared SHA disagree')
                else:
                    page = obj.get('physical_page')
                    ancestor = pointer; document_sha = None
                    while document_sha is None:
                        parent = source_objects.get(ancestor)
                        if isinstance(parent, dict):
                            document_sha = parent.get('source_sha256', parent.get('source_pdf_sha256'))
                            if document_sha is None and 'sha256' in parent and parent.get('source_resource_id', '').startswith('SOURCE-'): document_sha = parent['sha256']
                        if not ancestor: break
                        ancestor = ancestor.rsplit('/', 1)[0]
                    require(valid_sha(document_sha), 'relative region asset lacks document SHA scope')
                    require(any(any(z.get('physical_page') == page and z.get('source_pdf_sha256') == document_sha and z.get('absolute_path') == p for z in bundle['source_asset_locations']) for p in matches), 'region page locator points to wrong document/page')
    return assets

def resource_integrity(bundle, roots):
    row = bundle['source_record']; contexts = row['contexts']
    ids = [c['context_id'] for c in contexts]
    require(len(ids) == len(set(ids)), 'duplicate CTX ID')
    known_contexts = set(ids)
    for pointer, obj in walk(contexts):
        if isinstance(obj, dict):
            for key in GRAPH_KEYS & set(obj):
                targets = obj[key] if isinstance(obj[key], list) else [obj[key]]
                require(all(t is None or t in known_contexts for t in targets), 'dangling CTX relationship at ' + pointer + '/' + key)
    docs = bundle['source_documents']
    require(docs, 'current source document registry missing')
    needed = {row['source_ref']['sha256']} | {c['source_ref']['sha256'] for c in contexts}
    require(needed <= {d.get('source_sha256') for d in docs}, 'source_ref SHA document closure incomplete')
    for d in docs:
        p = bounded_path(d.get('snapshot', ''), roots)
        require(file_sha(p) == d.get('source_sha256'), 'document snapshot SHA mismatch')
        text_resource = d.get('source_text_resource')
        if text_resource:
            base = bundle['source_locator_bases'].get('canonical_row_attachment_relative_path_base')
            require(isinstance(base, str) and Path(base).is_absolute(), 'full text resource locator base missing')
            p = bounded_path(str((Path(base) / text_resource['relative_path']).resolve()), roots)
            require(file_sha(p) == text_resource['sha256'], 'full text resource file SHA mismatch')
            require(parse(p.read_bytes()) in bundle['source_full_text_resources'], 'exact document full text resource absent from bundle')
    definitions = {}
    def define(obj):
        rid = obj.get('source_resource_id')
        if not rid: return
        source_sha = obj.get('source_sha256', obj.get('snapshot_sha256', obj.get('source_pdf_sha256')))
        if source_sha is None and isinstance(obj.get('source_ref'), dict): source_sha = obj['source_ref']['sha256']
        require(valid_sha(source_sha), 'resource definition lacks source SHA: ' + str(rid))
        if rid in definitions:
            old = definitions[rid]
            require(old[0] == source_sha, 'resource ID has conflicting document SHA')
            if old[1] is not None and obj.get('text_sha256') is not None: require(old[1] == obj['text_sha256'], 'resource ID has conflicting text SHA')
        definitions[rid] = (source_sha, obj.get('text_sha256'))
    for d in docs: define(d)
    for field in BUNDLE_KEYS[2:5]:
        for obj in bundle[field]:
            if 'source_resource_id' in obj: define(obj)
            for key in ('source_texts', 'source_visual_text_resources'):
                for child in obj.get(key, []): define(child)
    for ref in row.get('source_references', []):
        require(ref.get('source_resource_id') in definitions, 'explicit source resource closure incomplete')
    for document in bundle['explicit_or_primary_source_resources']:
        visual = document.get('source_visual_text_resources', [])
        regions = document.get('source_display_regions', [])
        visual_ids = {v['source_resource_id'] for v in visual}
        region_ids = {r['region_id'] for r in regions}
        require(len(visual_ids) == len(visual) and len(region_ids) == len(regions), 'duplicate visual resource/region ID')
        for v in visual:
            schema_check(v, parse((ROOT / 'source-visual-v12.schema.json').read_bytes()))
            require(v['source_document_resource_id'] == document['source_resource_id'] and v['source_sha256'] == document.get('source_sha256', document.get('snapshot_sha256')), 'visual resource parent document binding differs')
            require(v['slide_region_id'] is None or v['slide_region_id'] in region_ids, 'visual resource display region missing')
        for r in regions:
            require(r['source_sha256'] == document.get('source_sha256', document.get('snapshot_sha256')), 'display region document SHA differs')
            require(set(r.get('children_resource_ids', [])) <= visual_ids, 'display region child resource missing')
            for child in r.get('children_resource_ids', []): require(next(v for v in visual if v['source_resource_id'] == child)['slide_region_id'] == r['region_id'], 'visual child belongs to another region')
    for pointer, obj in walk(bundle):
        if isinstance(obj, dict) and 'text_sha256' in obj:
            require(isinstance(obj.get('text'), str) and sha(obj['text'].encode('utf-8')) == obj['text_sha256'], 'source text SHA mismatch at ' + pointer)
        if isinstance(obj, dict) and 'snapshot_sha256' in obj and 'snapshot' in obj:
            p = bounded_path(obj['snapshot'], roots)
            require(file_sha(p) == obj['snapshot_sha256'], 'public resource snapshot SHA mismatch')
        if isinstance(obj, dict):
            for key in ('bbox_points_xyxy', 'bbox_pdf_points_xyxy', 'bbox_220dpi_px_xyxy', 'bbox_300dpi_px_xyxy'):
                if key in obj:
                    box = obj[key]
                    require(isinstance(box, list) and len(box) == 4 and all(type(z) in (int, float) for z in box) and box[0] < box[2] and box[1] < box[3], 'invalid source geometry bbox at ' + pointer)
    return set(definitions)

def validate_bundle(bundle, row_schema, profile, roots):
    require(isinstance(bundle, dict) and set(BUNDLE_KEYS) <= set(bundle) and set(bundle) <= set(BUNDLE_KEYS) | {'source_bundle_extension'}, 'missing/unsupported complete v13 bundle root fields')
    binding = parse((ROOT / 'parent-binding.json').read_bytes())
    frozen = load_frame_bindings(binding).get(bundle['source_record']['id'])
    require(frozen and sha(canonical(bundle)) == frozen['new_bundle_sha256'], 'source differs from sealed all4481 full-material binding')
    require(('source_bundle_extension' in bundle) is frozen['extension_available'], 'v13 extension presence differs from sealed source identity')
    schema_check(bundle, parse((ROOT / 'bundle.schema.json').read_bytes()))
    schema_check(bundle['source_record'], row_schema)
    schema_check(profile, parse((ROOT / 'field-profile.schema.json').read_bytes()))
    version = bundle['common_source_bundle_version']
    require(version.get('version') == 'v12' and version.get('actual_consumer_read_and_use_status') == 'not_recorded', 'wrong owner bundle version or fabricated consumer read receipt')
    forbidden = row_schema.get('x-source-protocol', {}).get('recursive_forbidden_exact_keys')
    require(isinstance(forbidden, list) and forbidden, 'owner forbidden-key protocol unavailable')
    check_profile(bundle, profile, forbidden)
    for field, documents in profile['expected_public_documents'].items():
        for obj in bundle[field]:
            rid = obj.get('source_resource_id')
            require(rid in documents and sha(canonical(obj)) == documents[rid], 'public document resource missing/changed/unsupported: ' + str(rid))
    resource_integrity(bundle, roots)
    return verified_assets(bundle, roots)

def make_packet(bundle, row_schema, profile, roots):
    assets = validate_bundle(bundle, row_schema, profile, roots)
    source_id = bundle['source_record']['id']
    require(source_id.startswith('RECODE25-'), 'unsupported source ID')
    packet = {'packet_version': 'native-full-source-3', 'source_id': source_id,
              'output_id': 'B-' + source_id.split('-')[1],
              'source_bundle_sha256': sha(canonical(bundle)), 'source_bundle': copy.deepcopy(bundle),
              'verified_asset_files': assets}
    require(canonical(packet['source_bundle']) == canonical(bundle), 'lossless bundle copy failed')
    schema_check(packet, parse((ROOT / 'packet.schema.json').read_bytes()))
    return packet

def verify_source_quote(packet, anchor):
    """Continuous Unicode span in an original bundle leaf; no dimension decision."""
    require(set(anchor) == {'source_id', 'source_bundle_sha256', 'bundle_pointer', 'quote', 'span'}, 'source quote fields missing/unsupported')
    require(sha(canonical(packet['source_bundle'])) == packet['source_bundle_sha256'], 'source bundle changed before quote validation')
    require(anchor['source_id'] == packet['source_id'] and anchor['source_bundle_sha256'] == packet['source_bundle_sha256'], 'source quote version binding differs')
    pointer = anchor['bundle_pointer']; require(isinstance(pointer, str) and pointer.startswith('/'), 'source quote needs original JSON Pointer')
    value = packet['source_bundle']
    for part in pointer[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            require(part.isdigit() and (part == '0' or not part.startswith('0')) and int(part) < len(value), 'source quote array location invalid')
            value = value[int(part)]
        elif isinstance(value, dict):
            require(part in value, 'source quote field absent'); value = value[part]
        else: raise InputFailure('source quote descends through a scalar')
    require(isinstance(value, str), 'source quote leaf is not original text')
    span = anchor['span']; require(set(span) == {'start', 'end'} and all(type(span[k]) is int for k in span), 'source quote span requires code-point integers')
    start, end = span['start'], span['end']
    require(0 <= start < end <= len(value) and value[start:end] == anchor['quote'], 'source quote is not exact continuous Unicode span')
    return True

def seal_members(seal):
    if 'files' in seal:
        return {str(Path(e['path']).resolve()): e['sha256'] for e in seal['files']}
    entries = seal['output_files'] + [seal[k] for k in ['base_v12_interface', 'base_v12_canonical', 'base_v12_material_manifest', 'source_addendum_original']] + seal['source_original_files']
    return {str(Path(e['absolute_path']).resolve()): e['sha256'] for e in entries}

def load_frame_bindings(binding):
    entry = binding['frame_bundle_bindings']
    require(file_sha(entry['path']) == entry['sha256'], 'sealed all4481 full-material bindings changed')
    rows = [parse(line) for line in Path(entry['path']).read_bytes().splitlines() if line.strip()]
    require(len(rows) == 4481 and len({r['id'] for r in rows}) == 4481, 'complete frame identity inventory required')
    return {r['id']: r for r in rows}

def load_owner(binding):
    require(binding.get('source_interface_version') == 'v13-source-addendum' and binding.get('source_base_version') == 'v12' and binding.get('binding_state') == 'owner_sealed', 'sealed v13 addendum over unchanged v12 base required')
    owner = binding['owner_seal']; base = binding['base_owner_seal']
    require(file_sha(owner['path']) == owner['sha256'] and file_sha(base['path']) == base['sha256'], 'sealed source/base binding changed')
    members = seal_members(parse(Path(owner['path']).read_bytes()))
    base_members = seal_members(parse(Path(base['path']).read_bytes()))
    for key in ['owner_accessor', 'owner_inventory_module', 'field_shape_counts', 'frame_bundle_bindings', 'extension_manifest', 'extension_registry']:
        e = binding[key]; path = str(Path(e['path']).resolve())
        require(members.get(path) == e['sha256'] and file_sha(path) == e['sha256'], 'v13 sealed component differs: ' + key)
    for key in ['owner_schema', 'owner_visual_schema']:
        e = binding[key]; path = str(Path(e['path']).resolve())
        require(base_members.get(path) == e['sha256'] and file_sha(path) == e['sha256'], 'unchanged base schema binding differs')
    require(file_sha(ROOT / 'source-visual-v12.schema.json') == binding['owner_visual_schema']['sha256'], 'base visual schema differs')
    for key in ['field_profile', 'operational_budget', 'manual']:
        e = binding[key]; require(valid_sha(e['sha256']) and file_sha(e['path']) == e['sha256'], 'v3 final runtime binding incomplete/changed: ' + key)
    profile = parse(Path(binding['field_profile']['path']).read_bytes()); shapes = parse(Path(binding['field_shape_counts']['path']).read_bytes())
    require(set(profile['paths']) == {'$' + x for x in shapes['field_paths']} and shapes['frame_N'] == 4481, 'profile not based on full sealed frame')
    accessor_path = Path(binding['owner_accessor']['path'])
    spec = importlib.util.spec_from_file_location('sealed_v13_source_owner', accessor_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    require(callable(getattr(module, 'lookup', None)) and callable(getattr(module, 'source_inventory', None)), 'sealed source interfaces unavailable')
    return parse(Path(binding['owner_schema']['path']).read_bytes()), module.lookup

def prompt_bytes(packets, manual, output_schema, variant='R', display_override=None):
    require(variant in ['R', 'W', 'H'], 'unsupported condition presentation')
    heading = '判读说明' if variant == 'H' else '判读要求'
    rules = (ROOT / 'native-reader-instructions.txt').read_text(encoding='utf-8')
    displayed = json.dumps(packets if display_override is None else display_override, ensure_ascii=False, sort_keys=True,
                           indent=2 if variant == 'W' else None,
                           separators=None if variant == 'W' else (',', ':'), allow_nan=False)
    uniform = (ROOT / 'source-reading-protocol-v12.md').read_bytes()
    scope_schema = (ROOT / 'necessary-source-scope.schema.json').read_bytes()
    return (heading + '\n' + rules + '\n完整共同手册（逐字，SHA256：' + sha(manual) + '）：\n' + manual.decode('utf-8') +
            '\n统一来源读取协议（逐字，SHA256：' + sha(uniform) + '）：\n' + uniform.decode('utf-8') +
            '\n必要范围与阅读收据技术schema（SHA256：' + sha(scope_schema) + '）：\n' + scope_schema.decode('utf-8') +
            '\n每条输出技术schema：\n' + output_schema.decode('utf-8') +
            '\n完整有序来源文件索引（完整文件交付/可访问/hash核对；必要视图须实际完整读）：\n' + displayed + '\n').encode('utf-8')

def batch_metrics(packets, manual, output_schema):
    files = {}
    for packet in packets:
        for asset in packet['verified_asset_files']:
            require(asset['sha256'] not in files or all(files[asset['sha256']][k] == asset[k] for k in ['bytes', 'mime_type', 'width', 'height']), 'asset identity differs across source bundles')
            files[asset['sha256']] = asset
    return {'units': len(packets), 'source_bundle_bytes': sum(len(canonical(p['source_bundle'])) for p in packets),
            'worst_prompt_bytes': max(len(prompt_bytes(packets, manual, output_schema, v)) for v in ['R', 'W', 'H']),
            'minimum_output_reserve_bytes': 5 * sum(len(json.dumps(p['source_bundle']['source_record']['text'], ensure_ascii=False).encode('utf-8')) for p in packets) + 8192 * len(packets),
            'context_nodes': sum(len(p['source_bundle']['source_record']['contexts']) for p in packets),
            'asset_count': len(files), 'asset_total_bytes': sum(a['bytes'] for a in files.values()),
            'asset_individual_bytes': max([a['bytes'] for a in files.values()] or [0]),
            'asset_total_pixels': sum(a['width'] * a['height'] for a in files.values())}

def check_budget(budget):
    require(set(budget) == {'budget_kind', 'basis', 'limits', 'actual_backend_limits'}, 'unsupported/missing budget fields')
    require(budget['budget_kind'] == 'frozen_operational_budget', 'capacity guarantee is not accepted')
    require(isinstance(budget['basis'], str) and bool(budget['basis'].strip()), 'budget basis missing')
    limits = budget['limits']; require(set(limits) == set(BUDGET_KEYS) | {'max_units'}, 'budget limits missing/unsupported')
    require(type(limits['max_units']) is int and 1 <= limits['max_units'] <= 41, 'max41 is a record ceiling only')
    for key in BUDGET_KEYS: require(type(limits[key]) is int and limits[key] > 0, 'unconfigured operational budget: ' + key)
    require(set(budget['actual_backend_limits']) == {'context_tokens', 'input_tokens', 'output_tokens', 'asset_limits'} and
            all(v is None for v in budget['actual_backend_limits'].values()), 'unavailable native backend limits must remain null')

def within_budget(metrics, budget):
    l = budget['limits']
    return (metrics['units'] <= l['max_units'] and metrics['minimum_output_reserve_bytes'] <= l['reserve_output_bytes'] and
            metrics['worst_prompt_bytes'] + l['reserve_output_bytes'] <= l['max_prompt_and_output_bytes'] and
            all(metrics[k] <= l['max_' + k] for k in ['context_nodes', 'asset_count', 'asset_total_bytes', 'asset_individual_bytes', 'asset_total_pixels']))

def group_batches(packets, budget, manual, output_schema):
    """Contiguous longest-fitting prefixes; no label/difficulty/result input."""
    check_budget(budget)
    ids = [p['source_id'] for p in packets]
    require(ids and len(ids) == len(set(ids)), 'frozen global order missing/duplicated')
    groups = []; current = []
    for packet in packets:
        require(within_budget(batch_metrics([packet], manual, output_schema), budget), 'single complete bundle exceeds operational budget: ' + packet['source_id'])
        trial = current + [packet]
        if current and not within_budget(batch_metrics(trial, manual, output_schema), budget):
            groups.append(current); current = [packet]
        else: current = trial
    if current: groups.append(current)
    return groups

def save_exclusive(path, raw):
    with Path(path).open('xb') as f: f.write(raw)
    return {'path': str(Path(path).resolve()), 'sha256': sha(raw), 'bytes': len(raw)}

def freeze_inputs(packets, binding, budget, manual, output_schema, destination):
    for p in packets:
        require(sha(canonical(p['source_bundle'])) == p['source_bundle_sha256'], 'source bundle changed before freeze')
        require(p['source_bundle']['source_record']['id'] == p['source_id'] and p['output_id'] == 'B-' + p['source_id'].split('-')[1], 'source/output ID map changed')
        for asset in p['verified_asset_files']:
            require(file_sha(asset['absolute_path']) == asset['sha256'], 'asset bytes changed before freeze')
    groups = group_batches(packets, budget, manual, output_schema)
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)
    manifest = {'version': 'native-necessary-read-final-input-3', 'source_version': 'v12', 'source_interface_version': 'v13-source-addendum',
                'necessary_read_protocol_version': 'native-necessary-read-v3',
                'reader_instructions_sha256': file_sha(ROOT / 'native-reader-instructions.txt'),
                'uniform_reading_protocol_sha256': file_sha(ROOT / 'source-reading-protocol-v12.json'),
                'necessary_scope_schema_sha256': file_sha(ROOT / 'necessary-source-scope.schema.json'),
                'parent_binding_sha256': file_sha(ROOT / 'parent-binding.json'),
                'owner_binding_sha256': sha(canonical(binding)), 'operational_budget_sha256': sha(canonical(budget)),
                'manual_sha256': sha(manual), 'output_item_schema_sha256': sha(output_schema),
                'global_order': [p['source_id'] for p in packets],
                'global_order_sha256': sha(canonical([p['source_id'] for p in packets])),
                'conditions': list(CONDITIONS), 'provider_api_call_count': None,
                'model_calls_made_by_builder': 0, 'batches': []}
    save_exclusive(destination / 'owner-binding.json', canonical(binding))
    save_exclusive(destination / 'operational-budget.json', canonical(budget))
    packet_directory = destination / 'packets'; packet_directory.mkdir()
    packet_files = {}
    for p in packets:
        packet_files[p['source_id']] = {
            'R': save_exclusive(packet_directory / (p['source_id'] + '.compact.json'), canonical(p)),
            'W': save_exclusive(packet_directory / (p['source_id'] + '.indented.json'), json.dumps(p, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode())}
    for number, group in enumerate(groups, 1):
        batch_id = f'batch-{number:04d}'; directory = destination / batch_id; directory.mkdir()
        indexes = {v: [{'source_id': p['source_id'], 'output_id': p['output_id'], 'source_bundle_sha256': p['source_bundle_sha256'],
                        'complete_packet_file': packet_files[p['source_id']][v],
                        'context_nodes': len(p['source_bundle']['source_record']['contexts']),
                        'asset_files': p['verified_asset_files']} for p in group] for v in ['R', 'W']}
        displays = {'R': save_exclusive(directory / 'source-index-compact.json', canonical(indexes['R'])),
                    'W': save_exclusive(directory / 'source-index-indented.json', json.dumps(indexes['W'], ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode())}
        prompts = {v: save_exclusive(directory / ('prompt-' + v + '.txt'), prompt_bytes(group, manual, output_schema, v, indexes['W' if v == 'W' else 'R'])) for v in ['R', 'W', 'H']}
        metrics = batch_metrics(group, manual, output_schema)
        metrics['conservative_full_material_presentation_bytes'] = metrics.pop('worst_prompt_bytes')
        metrics['actual_initial_prompt_max_bytes'] = max(e['bytes'] for e in prompts.values())
        manifest['batches'].append({'batch_id': batch_id, 'expected_n': len(group),
                                    'source_ids': [p['source_id'] for p in group], 'output_ids': [p['output_id'] for p in group],
                                    'bundle_bindings': [{'source_id': p['source_id'], 'source_bundle_sha256': p['source_bundle_sha256']} for p in group],
                                    'metrics': metrics, 'display_files': displays, 'prompts': prompts,
                                    'condition_prompt_key': {'R1': 'R', 'R2': 'R', 'R3': 'R', 'W': 'W', 'H': 'H'}})
    save_exclusive(destination / 'batching-manifest.json', canonical(manifest))
    return manifest

def bind_owner(binding_path, binding_sha, destination):
    """Freeze an already whole-frame/profile/budget bound v13 contract, no sample lookup."""
    require(file_sha(binding_path) == binding_sha, 'explicit final v3 binding SHA mismatch')
    binding = parse(Path(binding_path).read_bytes()); load_owner(binding)
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)
    save_exclusive(destination / 'owner-binding.json', canonical(binding))
    return binding

def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('bind-owner'); p.add_argument('--binding', required=True); p.add_argument('--binding-sha', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('build'); p.add_argument('--binding', required=True); p.add_argument('--binding-sha', required=True)
    p.add_argument('--authorized-order', required=True); p.add_argument('--order-file-sha', required=True)
    p.add_argument('--manual', required=True); p.add_argument('--manual-sha', required=True)
    p.add_argument('--budget', required=True); p.add_argument('--budget-sha', required=True); p.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'bind-owner':
            bind_owner(args.binding, args.binding_sha, args.out)
            print(json.dumps({'state': 'whole_frame_binding_frozen_no_sample_selected', 'binding_sha256': file_sha(Path(args.out) / 'owner-binding.json')}))
        else:
            for path, expected in [(args.binding, args.binding_sha), (args.authorized_order, args.order_file_sha), (args.budget, args.budget_sha), (args.manual, args.manual_sha)]:
                require(file_sha(path) == expected, 'explicit frozen input SHA mismatch')
            binding = parse(Path(args.binding).read_bytes()); schema, lookup = load_owner(binding)
            require(file_sha(args.manual) == binding['manual']['sha256'] and file_sha(args.budget) == binding['operational_budget']['sha256'], 'manual/budget differ from final v3 binding')
            profile = parse(Path(binding['field_profile']['path']).read_bytes()); budget = parse(Path(args.budget).read_bytes()); check_budget(budget)
            order = parse(Path(args.authorized_order).read_bytes())
            require(set(order) == {'ordered_source_ids', 'source_selection_manifest'}, 'authorized frozen order interface required')
            selection = order['source_selection_manifest']; require(file_sha(selection['path']) == selection['sha256'], 'source selection authorization changed')
            ids = order['ordered_source_ids']; require(isinstance(ids, list) and ids and len(ids) == len(set(ids)), 'invalid authorized source order')
            packets = [make_packet(lookup(uid, 'model', bundle=True), schema, profile, binding['allowed_source_file_roots']) for uid in ids]
            result = freeze_inputs(packets, binding, budget, Path(args.manual).read_bytes(), (ROOT / 'output-item.schema.json').read_bytes(), args.out)
            print(json.dumps({'state': 'inputs_frozen_no_model_called', 'batches': len(result['batches'])}))
    except (InputFailure, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'state': 'technical_input_failure', 'error': str(exc), 'labels_created': False}), file=sys.stderr); return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
