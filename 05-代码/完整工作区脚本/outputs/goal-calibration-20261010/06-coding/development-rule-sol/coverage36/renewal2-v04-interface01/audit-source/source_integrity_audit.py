"""Independent source-only integrity audit. Does not load any semantic coder."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
NEW = HERE.parent
EXPECTED_DESIGN = 'ff022f5a9d803ed28befedd5a1218011ed06dfab4493c9ac2a04c4ce9f44482b'
EXPECTED_SOURCE = '0abd018875edb2ae41cc4a7aff3c7ba5d4194895d575517fd51ea5261983c799'
EXPECTED_RESOURCE = '6058415bb88be3a6cc61ed1f06092910d94c0148308082b7628ad65adb8707b1'
SEMANTIC = {
    'evidence.py': '5ce0fc8c39862edbcab837c0b1fdc7f5c605758f34fbf0ab34487a0b4531cdb3',
    'relations.py': 'ba63f8b17624138b83d140d05791121a60d11c472a337b0d1abc535cf62b90da',
    'dimensions.py': 'a85fcfc93b1c4b8ccb53b0b55ffb571f175c8fdaa978e2a1c3b10dabad2dc638',
}
READS = []
CHECKS = []


def pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def decode(payload):
    return json.loads(payload, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON: ' + value)))


def checked(path, expected=None, expected_bytes=None, role=None):
    path = Path(path).resolve()
    payload = path.read_bytes()
    sha = hashlib.sha256(payload).hexdigest()
    if expected is not None:
        assert sha == expected, ('digest mismatch', str(path), sha, expected)
    if expected_bytes is not None:
        assert len(payload) == expected_bytes, ('byte mismatch', str(path))
    READS.append({'path': str(path), 'sha256': sha, 'bytes': len(payload), 'role': role,
                  'digest_checked_before_parse': expected is not None})
    return payload


def check(name, condition, detail=None):
    CHECKS.append({'name': name, 'passed': bool(condition), 'detail': detail})


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def inventory(value, prefix='$', result=None):
    result = result if result is not None else collections.defaultdict(collections.Counter)
    result[prefix][type(value).__name__] += 1
    if isinstance(value, dict):
        for key, child in value.items():
            inventory(child, prefix + '.' + key, result)
    elif isinstance(value, list):
        for child in value:
            inventory(child, prefix + '[]', result)
    return result


def transform(value, mapping):
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, dict):
        return {key: transform(child, mapping) for key, child in value.items()}
    if isinstance(value, list):
        return [transform(child, mapping) for child in value]
    return value


def write(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    auth = decode(checked(NEW / 'initial-authorization-and-semantic-binding.json', role='parent_authorization'))
    assert auth['design_sha256'] == EXPECTED_DESIGN and auth['source_sha256'] == EXPECTED_SOURCE
    design = decode(checked(auth['design_path'], EXPECTED_DESIGN, role='authorized_source_design'))
    assert design['source']['sha256'] == EXPECTED_SOURCE and design['resource']['sha256'] == EXPECTED_RESOURCE
    manual = checked(design['manual']['path'], design['manual']['sha256'], design['manual'].get('bytes'), role='common_manual_integrity')
    raw = checked(design['source']['path'], EXPECTED_SOURCE, design['source'].get('bytes'), role='canonical_source_context')
    rows = [decode(line) for line in raw.splitlines() if line.strip()]
    resource = decode(checked(design['resource']['path'], EXPECTED_RESOURCE, design['resource'].get('bytes'), role='source_text_and_geometry_resource'))
    seal_payload = checked(design['source_seal'], role='source_only_delivery_seal_current_hash')
    seal = decode(seal_payload)
    seal_files = {entry['path']: entry for entry in seal['files']}
    check('source_and_resource_match_delivery_seal', all(
        seal_files[design[k]['path']]['sha256'] == design[k]['sha256'] and
        seal_files[design[k]['path']]['bytes'] == len(raw if k == 'source' else Path(design[k]['path']).read_bytes()) for k in ('source', 'resource')))
    check('source_seal_has_source_only_status', 'source_only' in seal['status'])
    # Do not follow source_inputs/projection-audit paths: they are outside the runtime allowlist.
    pdf = checked(resource['snapshot'], resource['snapshot_sha256'], role='original_pdf_integrity_only')
    check('snapshot_primary_sha_consistent', resource['source_sha256'] == resource['snapshot_sha256'])
    primary = resource['snapshot_sha256']
    root_id = resource['source_resource_id']
    assets = {}
    for entry in design['source_page_assets']:
        payload = checked(entry['path'], entry['sha256'], role='original_png_integrity_and_header_only')
        check('png_signature_page_' + str(entry['physical_page']), payload[:8] == b'\x89PNG\r\n\x1a\n')
        check('png_IHDR_page_' + str(entry['physical_page']), payload[12:16] == b'IHDR')
        width, height = struct.unpack('>II', payload[16:24])
        page = entry['physical_page']
        assert page not in assets
        assets[page] = {**entry, 'width': width, 'height': height, 'bytes': len(payload)}
    check('exact_nine_pages', set(assets) == set(range(1, 10)))
    check('all_asset_same_snapshot', all(a['source_pdf_sha256'] == primary for a in assets.values()))
    check('record_scope_and_order', len(rows) == design['n'] == 2 and [row['id'] for row in rows] == design['ids'])
    check('dimension_scope_metadata_10', design['dimension_n'] == 10)
    check('raw_top_closed_keys', all(set(row) == {'id', 'text', 'pages', 'source_ref', 'contexts', 'source_attachments', 'source_references'} for row in rows))
    text_entries = resource['source_texts']
    text_map = {entry['source_resource_id']: entry for entry in text_entries}
    check('37_unique_source_text_entries', len(text_map) == len(text_entries) == 37)
    region_n = 0
    geometry_problems = []
    interval_problems = []
    for entry in text_entries:
        rid = entry['source_resource_id']
        check('text_sha:' + rid, hashlib.sha256(entry['text'].encode()).hexdigest() == entry['text_sha256'])
        check('text_snapshot:' + rid, entry['source_sha256'] == primary and entry['source_path'] == resource['snapshot'] and entry['source_ref']['sha256'] == primary and entry['source_ref']['source_resource_id'] == root_id)
        left, right = entry['source_char_interval_footerless_whitespace_normalized']
        if not (type(left) is int and type(right) is int and 0 <= left <= right and right-left == len(entry['text'])):
            interval_problems.append({'resource_id': rid, 'interval': [left, right], 'text_length': len(entry['text'])})
        loc = entry['source_ref']['locator']
        check('heading_path:' + rid, loc['heading_path'] == entry['heading_path'])
        check('region_pages:' + rid, sorted(set(region['physical_page'] for region in loc['regions'])) == sorted(loc['physical_pages']) and sorted(set(region['printed_page'] for region in loc['regions'])) == sorted(loc['printed_pages']))
        for region in loc['regions']:
            region_n += 1
            page = region['physical_page']
            asset = assets.get(page)
            xy = region['bbox_220dpi_px_xyxy']
            points = region['bbox_pdf_points_xyxy']
            reasons = []
            if asset is None or region['page_asset'] != 'pages/' + Path(asset['path']).name:
                reasons.append('exact_page_asset_binding')
            if len(xy) != 4 or len(points) != 4 or any(type(n) not in (int, float) for n in xy + points):
                reasons.append('coordinate_schema')
            else:
                if not (0 <= xy[0] < xy[2] <= asset['width'] and 0 <= xy[1] < xy[3] <= asset['height']):
                    reasons.append('pixel_bounds')
                if not (0 <= points[0] < points[2] and 0 <= points[1] < points[3]):
                    reasons.append('point_order')
                if max(abs(px - pt * 220 / 72) for px, pt in zip(xy, points)) > .011:
                    reasons.append('220dpi_scaling')
            if reasons:
                geometry_problems.append({'resource_id': rid, 'page': page, 'reasons': reasons})
    check('resource_intervals_shape_and_length', not interval_problems, interval_problems)
    check('all_regions_page_asset_geometry_consistent', not geometry_problems, {'region_n': region_n, 'problems': geometry_problems})
    overlaps = []
    for i, one in enumerate(text_entries):
        a, b = one['source_char_interval_footerless_whitespace_normalized']
        for two in text_entries[i+1:]:
            c, d = two['source_char_interval_footerless_whitespace_normalized']
            start, end = max(a,c), min(b,d)
            if start < end and one['text'][start-a:end-a] != two['text'][start-c:end-c]:
                overlaps.append([one['source_resource_id'], two['source_resource_id'], start, end])
    check('overlapping_text_intervals_consistent', not overlaps, overlaps)
    geometry = resource['source_geometry']
    external_resource_refs = sorted({value for value in strings(geometry) if value.startswith('SOURCEPARAGRAPH-')} - text_map.keys())
    check('original_resource_geometry_closed', not external_resource_refs, external_resource_refs)
    record_reports = []
    for row in rows:
        contexts = row['contexts']
        ids = [ctx['context_id'] for ctx in contexts]
        ctx_set = set(ids)
        references = {v for v in strings(row) if v.startswith('CTX-')}
        absent = sorted(references - ctx_set)
        check('context_graph_closed:' + row['id'], len(ctx_set) == len(ids) and not absent, absent)
        check('all_raw_source_refs_same_snapshot:' + row['id'], row['source_ref']['sha256'] == primary and all(ctx['source_ref']['sha256'] == primary and ctx['source_ref']['source_resource_id'] == root_id for ctx in contexts))
        supplied = [ctx for ctx in contexts if ctx['kind'] == 'same_snapshot_referenced_source_paragraph']
        rid_to_ctx = {ctx['structure']['source_paragraph_id']: ctx['context_id'] for ctx in supplied}
        check('complete37_in_each_record:' + row['id'], set(rid_to_ctx) == set(text_map) and len(supplied) == 37)
        mismatches = []
        for ctx in supplied:
            rid = ctx['structure']['source_paragraph_id']
            entry = text_map[rid]
            loc = dict(ctx['source_ref']['locator'])
            loc.pop('source_paragraph_id')
            if ctx['text'] != entry['text'] or ctx['structure']['heading_path'] != entry['heading_path'] or loc != entry['source_ref']['locator']:
                mismatches.append(rid)
        check('37_raw_text_locator_exact_copy:' + row['id'], not mismatches, mismatches)
        geoms = [ctx for ctx in contexts if ctx['kind'] == 'same_snapshot_source_numbered_group_geometry']
        adapted_geometry = dict(geoms[0]['structure'])
        related = adapted_geometry.pop('related_context_ids')
        check('raw_geometry_only_explicit_id_rebinding:' + row['id'], len(geoms) == 1 and adapted_geometry == transform(geometry, rid_to_ctx) and set(related) == set(rid_to_ctx.values()))
        attach_problems = []
        for attachment in row['source_attachments']:
            asset = assets.get(attachment['physical_page'])
            resolved = (Path(design['asset_path_base']) / attachment['relative_path']).resolve()
            expected = Path(asset['path']).resolve()
            if resolved != expected or attachment['sha256'] != asset['sha256'] or attachment['source_pdf_sha256'] != primary or attachment['render_dpi'] != 220 or attachment['attachment_id'] != 'SOURCEASSET-' + asset['sha256'][:20] or attachment['kind'] != 'original_binary_rendered_source_page':
                attach_problems.append(attachment['attachment_id'])
        check('nine_raw_attachments_exact_bindings:' + row['id'], len(row['source_attachments']) == 9 and not attach_problems, attach_problems)
        check('source_reference_root_closed:' + row['id'], len(row['source_references']) == 1 and row['source_references'][0]['source_resource_id'] == root_id and row['source_references'][0]['context_id'] is None)
        record_reports.append({'id': row['id'], 'top_schema': {k:type(v).__name__ for k,v in row.items()}, 'pages': row['pages'], 'context_n': len(contexts), 'kind_counts': dict(collections.Counter(ctx['kind'] for ctx in contexts)), 'textless_context_n': sum('text' not in ctx for ctx in contexts), 'source_resource_context_n': len(supplied), 'source_attachment_n': len(row['source_attachments']), 'source_reference_n': len(row['source_references']), 'context_ids': ids})
    check('resource_asset_metadata_exact_copies', len(resource['source_page_assets']) == 9 and all((Path(design['asset_path_base']) / entry['relative_path']).resolve() == Path(assets[entry['physical_page']]['path']).resolve() and entry['sha256'] == assets[entry['physical_page']]['sha256'] and entry['source_pdf_sha256'] == primary and entry['render_dpi'] == 220 for entry in resource['source_page_assets']))
    semantic_files = []
    for name, expected in SEMANTIC.items():
        new_bytes = checked(NEW/name, expected, role='frozen_semantic_byte_integrity')
        old = NEW.parent/'implementation04'/name
        old_bytes = checked(old, expected, role='frozen_origin_byte_integrity')
        check('semantic_byte_equal:' + name, new_bytes == old_bytes)
        semantic_files.append({'path': str((NEW/name).resolve()), 'sha256': expected, 'origin_path': str(old.resolve()), 'byte_equal': new_bytes == old_bytes})
    raw_inventory = inventory(rows)
    write('raw-field-type-inventory.json', {k:dict(v) for k,v in sorted(raw_inventory.items())})
    write('source-integrity-report.json', {
        'status': 'source_only_integrity_audit', 'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'reads': READS, 'checks': CHECKS, 'check_n': len(CHECKS), 'passed_n': sum(c['passed'] for c in CHECKS), 'failed_n': sum(not c['passed'] for c in CHECKS),
        'records': record_reports, 'original_resource_text_n': len(text_entries), 'original_resource_region_n': region_n,
        'assets': list(assets.values()), 'semantic_files': semantic_files,
        'scope': resource['scope'],
        'qualifications': [
            'Resource completeness is audited against the explicitly supplied scope; not every word of the PDF is claimed transcribed.',
            'No source text semantics is automatically transferred to a current record.',
            'source_references.source_field is the literal source_context while the raw row key is contexts; preserved descriptive metadata, not rewritten into a JSON pointer.',
            'The source-only delivery seal path has no prior SHA in design; current digest is recorded before parse and its supplied source/resource bindings agree. Runner freezes this current digest and rechecks it after inference.',
            'PNG files were hashed and IHDR geometry read; no pixels were interpreted. PDF read for digest only.',
        ],
        'no_actual_prediction_or_evaluation': True, 'no_reference_or_AB_native_read': True,
    })
    runtime_roles = {'authorized_source_design', 'common_manual_integrity', 'canonical_source_context', 'source_text_and_geometry_resource', 'source_only_delivery_seal_current_hash', 'original_pdf_integrity_only', 'original_png_integrity_and_header_only'}
    materials = [entry for entry in READS if entry['role'] in runtime_roles]
    write('runtime-material-read-allowlist.json', {'status': 'source_only_exact_runtime_material_allowlist', 'material_file_n': len(materials), 'files': materials, 'semantic_files': semantic_files, 'notes': ['No projection-audit/source_inputs file has been read or added to allowlist.', 'Raw relative paths preserved; attachment resolution uses design.asset_path_base; regions bind by exact asset basename + physical page + snapshot SHA.'], 'forbidden': ['new2 reference', 'A/B/native output', 'other material', 'previous decisions or metrics as runtime input']})
    print(json.dumps({'check_n': len(CHECKS), 'passed_n': sum(c['passed'] for c in CHECKS), 'failed_n': sum(not c['passed'] for c in CHECKS), 'material_file_n': len(materials), 'record_n': len(rows), 'context_n': sum(len(row['contexts']) for row in rows), 'region_n': region_n}))


if __name__ == '__main__':
    main()
