"""Export the specified existing 41+36 development sources, without coding."""
from pathlib import Path
from functools import lru_cache
import datetime, hashlib, importlib.util, json, struct, sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ROOT = BASE.parents[2]
V13 = BASE.parent / 'source-interface-v13-addendum'
OLD41 = ROOT / '06-coding/development-rule-sol/coverage36/implementation07-source-v12-receipts/run-old41-01/delivered-complete-source-bundles.jsonl'
INDEX36 = BASE / 'coverage36-common-v12/source-resource-index.json'
SOURCE36 = BASE / 'coverage36-common-v12/common-source-bundles.jsonl'
H = lambda value: hashlib.sha256(value).hexdigest()
def bind(path):
    path = Path(path); raw = path.read_bytes()
    return {'absolute_path': str(path), 'sha256': H(raw), 'bytes': len(raw)}
def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

assert not (OUT / 'delivery-seal.json').exists(), 'Do not overwrite sealed package'
seal_path = V13 / 'delivery-seal.json'
assert bind(seal_path)['sha256'] == 'c34f1365ed771c7e36ef1d941591e3b715844e34cdc9eb8fd20e05880a3b6620'
parent_seal = json.loads(seal_path.read_text())
for entry in parent_seal['output_files']: assert bind(entry['absolute_path']) == entry
spec = importlib.util.spec_from_file_location('source_v13', V13 / 'source_only_interface_v13.py')
src = importlib.util.module_from_spec(spec); spec.loader.exec_module(src)

# Process-local caching of the checked immutable JSONL files only. No old file
# is written and the original checked() still verifies each file before use.
original_rows = src._base.rows
@lru_cache(maxsize=None)
def cached_rows(path, size, mtime): return original_rows(path)
def rows(path):
    path = Path(path); stat = path.stat()
    return cached_rows(str(path), stat.st_size, stat.st_mtime_ns)
src._base.rows = rows
original_checked = src._base.checked
@lru_cache(maxsize=None)
def checked_once(path, expected, size, mtime): return original_checked(path, expected)
def checked(path, expected):
    path = Path(path); stat = path.stat()
    return checked_once(str(path), expected, stat.st_size, stat.st_mtime_ns)
src._base.checked = checked

old41 = [json.loads(z) for z in OLD41.read_bytes().splitlines()]
ids41 = [z['source_record']['id'] for z in old41]
ids36 = json.loads(INDEX36.read_text())['fixed_record_ids_in_input_order']
assert len(ids41) == 41 and len(ids36) == 36
ids = ids41 + ids36
assert len(ids) == len(set(ids)) == 77
old_source_records = {z['source_record']['id']: z['source_record'] for z in old41}
old_source_records.update({z['source_record']['id']: z['source_record']
                          for z in map(json.loads, SOURCE36.read_text().splitlines())})
bindings = {z['id']: z for z in map(json.loads, (V13 / 'frame-bundle-bindings.jsonl').read_text().splitlines()) if z['id'] in ids}
assert len(bindings) == 77

files, documents, library_resources, per_record, shared_views = {}, {}, {}, [], {}
def pixel_header(raw):
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):
        width, height = struct.unpack('>II', raw[16:24]); return {'format': 'PNG', 'width': width, 'height': height}
    if raw.startswith((b'GIF87a', b'GIF89a')):
        width, height = struct.unpack('<HH', raw[6:10]); return {'format': 'GIF', 'width': width, 'height': height}
    if raw.startswith(b'\xff\xd8'):
        index = 2
        while index + 4 < len(raw):
            if raw[index] != 255: index += 1; continue
            while index + 1 < len(raw) and raw[index + 1] == 255: index += 1
            marker = raw[index + 1]
            if marker in [0xD8, 0xD9, 0x01] or 0xD0 <= marker <= 0xD7: index += 2; continue
            length = int.from_bytes(raw[index + 2:index + 4], 'big')
            if marker in [0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF]:
                height = int.from_bytes(raw[index + 5:index + 7], 'big'); width = int.from_bytes(raw[index + 7:index + 9], 'big')
                return {'format': 'JPEG', 'width': width, 'height': height}
            if length < 2: break
            index += 2 + length
    return None
path_checks = {}
def add_file(path, expected, kind, rid, locator=None):
    path = Path(path).resolve()
    key = str(path)
    if key not in path_checks:
        raw = path.read_bytes(); actual = H(raw)
        path_checks[key] = {'sha256': actual, 'bytes': len(raw), 'pixels': pixel_header(raw)}
    checked_file = path_checks[key]; assert checked_file['sha256'] == expected, key
    entry = files.setdefault(expected, {'sha256': expected, 'bytes': checked_file['bytes'], 'absolute_paths': [],
                                       'resource_kinds': [], 'record_ids': [], 'source_locators': [], 'image_pixels': checked_file['pixels']})
    assert entry['bytes'] == checked_file['bytes'] and entry['image_pixels'] == checked_file['pixels']
    if key not in entry['absolute_paths']: entry['absolute_paths'].append(key)
    if kind not in entry['resource_kinds']: entry['resource_kinds'].append(kind)
    if rid not in entry['record_ids']: entry['record_ids'].append(rid)
    if locator is not None and locator not in entry['source_locators']: entry['source_locators'].append(locator)
    return expected

lines = []
for ordinal, rid in enumerate(ids, 1):
    # This finite export actually checks all three defaults for its 77 inputs;
    # parent all4481 checks are separately bound, not renamed as this execution.
    all_roles = [src.lookup(rid, selector) for selector in ['rule', 'model', 'human']]
    bundle = all_roles[1]; text = src.cj(bundle); raw = text.encode()
    assert text == src.cj(all_roles[0]) == src.cj(all_roles[2])
    expected = bindings[rid]
    assert H(raw) == expected['new_bundle_sha256'] and len(raw) == expected['new_bundle_utf8_bytes']
    record = bundle['source_record']; assert record == old_source_records[rid]
    assert H(record['text'].encode()) == expected['body_utf8_sha256']
    assert H(src.cj(record['contexts']).encode()) == expected['unchanged_context_object_sha256']
    assert set(bundle) == set(old41[0]) | ({'source_bundle_extension'} if expected['extension_available'] else set())
    source_files = set()
    for doc in bundle['source_documents']:
        sha = doc['source_sha256']; source_files.add(add_file(doc['snapshot'], sha, 'document_snapshot', rid))
        documents.setdefault(sha, {'source_sha256': sha, 'source_document_resource_ids': [], 'record_ids': []})
        if doc['source_resource_id'] not in documents[sha]['source_document_resource_ids']: documents[sha]['source_document_resource_ids'].append(doc['source_resource_id'])
        if rid not in documents[sha]['record_ids']: documents[sha]['record_ids'].append(rid)
        for key in ['source_text_resource', 'source_visual_text_resource', 'source_display_geometry_resource']:
            if doc.get(key):
                z = doc[key]; source_files.add(add_file(BASE / z['relative_path'], z['sha256'], key, rid, {'source_document_sha256': sha}))
    for resource in bundle['explicit_or_primary_source_resources']:
        resource_id = resource['source_resource_id']; payload = src.cj(resource).encode()
        shared = library_resources.setdefault(resource_id, {'resource_id': resource_id, 'payload_sha256': H(payload), 'payload_utf8_bytes': len(payload), 'record_ids': []})
        assert shared['payload_sha256'] == H(payload)
        if rid not in shared['record_ids']: shared['record_ids'].append(rid)
        snapshot = resource.get('snapshot')
        if not snapshot and resource.get('snapshot_relative_path'): snapshot = BASE / 'source-library' / resource['snapshot_relative_path']
        if snapshot: source_files.add(add_file(snapshot, resource.get('snapshot_sha256', resource.get('source_sha256')), 'document_snapshot', rid))
    for resource in bundle['source_full_text_resources']:
        locator = resource.get('source_locator', {})
        if locator.get('kind') == 'structured_JSON_and_original_HTML':
            for view in ['structured_snapshot', 'raw_html']:
                z = locator[view]; source_files.add(add_file(z['absolute_path'], z['sha256'], 'original_' + view, rid, z))
    for asset in bundle['source_asset_locations']:
        source_files.add(add_file(asset['absolute_path'], asset['sha256'], 'image_asset', rid,
                                 {'source_document_sha256': asset.get('source_pdf_sha256'), 'physical_page': asset.get('physical_page')}))
    inventory = src.source_inventory(bundle)
    for view in inventory:
        identity = H(src.cj(view).encode())
        shared = shared_views.setdefault(identity, {'view_identity_sha256': identity, 'source_inventory_entry': view, 'record_ids': []})
        if rid not in shared['record_ids']: shared['record_ids'].append(rid)
    lines.append(raw + b'\n')
    per_record.append({'ordinal_1based': ordinal, 'record_id': rid, 'bundle_sha256': H(raw), 'bundle_UTF8_bytes_excluding_LF': len(raw),
                       'bundle_JSONL_line_UTF8_bytes_including_LF': len(raw) + 1, 'source_record_sha256': H(src.cj(record).encode()),
                       'source_record_UTF8_bytes': len(src.cj(record).encode()), 'body_UTF8_bytes': len(record['text'].encode()),
                       'body_sha256': expected['body_utf8_sha256'], 'old_CTX_N': len(record['contexts']),
                       'old_CTX_UTF8_JSON_bytes': len(src.cj(record['contexts']).encode()),
                       'old_CTX_object_sha256': expected['unchanged_context_object_sha256'],
                       'source_file_SHAs': sorted(source_files), 'inventory_view_identity_SHAs': [H(src.cj(z).encode()) for z in inventory],
                       'public_image_asset_path_N': len(bundle['source_asset_locations']), 'v13_extension_available': expected['extension_available'],
                       'old_v12_bundle_sha256': expected['old_bundle_sha256'], 'actual_three_role_default_same_bytes': True})

packet = OUT / 'common-source-bundles.jsonl'; packet.write_bytes(b''.join(lines))
image_files = [z for z in files.values() if 'image_asset' in z['resource_kinds']]
assert all(z['image_pixels'] is not None for z in image_files)
resource_index = {'version': 'existing-development77-common-v13', 'fixed_record_ids_in_input_order': ids,
                  'fixed_ID_order_UTF8_LF_sha256': H(('\n'.join(ids) + '\n').encode()), 'per_record': per_record,
                  'deduplicated_source_document_identities': list(documents.values()), 'deduplicated_library_payloads': list(library_resources.values()),
                  'deduplicated_available_source_views': list(shared_views.values()), 'deduplicated_actual_source_files_by_SHA': list(files.values()),
                  'inventory_is_availability_not_actual_read_or_use': True,
                  'pixel_dimensions_are_actual_PNG_JPEG_GIF_headers_not_visual_inspection': True}
dump('source-resource-index.json', resource_index)
manual = ROOT / '03-manual/common-manual-v1.1-development.md'
assert bind(manual)['sha256'] == '6ffc7b35a5cbe1c1f90c81d24d1508dba7adefe5e7bbd058c284d76e14b8a70f'
counts = {'bundle_JSON_UTF8_total_excluding_LF': sum(z['bundle_UTF8_bytes_excluding_LF'] for z in per_record),
          'common_source_JSONL_UTF8_total_including_LF': packet.stat().st_size,
          'max_single_bundle_UTF8_bytes': max(z['bundle_UTF8_bytes_excluding_LF'] for z in per_record),
          'actual_source_file_distinct_SHA_N': len(files), 'actual_source_file_absolute_path_N': len(path_checks),
          'deduplicated_actual_source_file_bytes': sum(z['bytes'] for z in files.values()),
          'actual_image_asset_distinct_SHA_N': len(image_files),
          'deduplicated_image_asset_bytes': sum(z['bytes'] for z in image_files),
          'deduplicated_image_asset_pixel_N': sum(z['image_pixels']['width'] * z['image_pixels']['height'] for z in image_files),
          'new_v13_extension_record_N': sum(z['v13_extension_available'] for z in per_record)}
manifest = {'status': 'fixed_existing_development77_source_only_v13', 'record_N': 77,
            'fixed_order_sources': [dict(bind(OLD41), fields_consumed='source_record.id order and source_record equality only; pure source file'),
                                    dict(bind(INDEX36), fields_consumed='fixed_record_ids_in_input_order')],
            'source36_for_unchanged_record_comparison': bind(SOURCE36),
            'v13_parent_seal': bind(seal_path), 'v13_accessor': bind(V13 / 'source_only_interface_v13.py'),
            'v13_frame_bundle_bindings': bind(V13 / 'frame-bundle-bindings.jsonl'),
            'fixed_record_ID_order_UTF8_LF_sha256': resource_index['fixed_ID_order_UTF8_LF_sha256'],
            'actual_checks': {'real_default_role_comparisons_N': 77, 'default_role_calls_N': 231,
                              'per_ID_full_bundle_SHA_bytes_matched_v13_frame_bindings_N': 77,
                              'source_record_and_old_CTX_unchanged_vs_old_pure_inputs_N': 77,
                              'v13_parent_full_frame_role_same_bytes_fact_N': parent_seal['role_default_bundle_same_bytes_N'],
                              'parent_full_frame_fact_separate_from_this77_execution': True},
            'common_manual_binding_only': dict(bind(manual), version='v1.1', semantic_content_not_modified=True),
            'actual_bytes_and_assets': counts, 'no_token_capacity_guess': True,
            'no_new_sample_or_labels_or_performance_read': True, 'source_only_not_execution_prompt_or_budget': True,
            'source_availability_not_actual_method_read_or_use': True,
            'joint_freeze_and_native_coding': 'not executed in this source preparation'}
dump('manifest.json', manifest)
(OUT / 'README.md').write_text('77条既有开发共同纯来源包v13。固定顺序为指定v07 run-old41-01的41个source_record.id，然后指定coverage36来源索引的36个ID；不重新抽样。\n\n每条完整default bundle取自已封存v13接口，逐ID核其实际SHA和UTF8 bytes与v13 frame-bundle-bindings一致；source_record及旧CTX与既有纯来源输入逐值相同。原十个根字段完整保留，适用的v13 extension随包保留。本次对77条实际调用rule/model/human共231次，默认对象同字节；v13既有all4481事实另绑定。\n\nsource-resource-index.json列固定ID、每条来源/CTX字节、可用视图及定位，按SHA去重列实际文件绝对路径、bytes和图片header pixels。重复来源仍完整存在每条公共包。资源可用不等于方法实际读入或使用；仅解析图片header元数据，不声称本次视觉检查。\n\n未读取答案、参照、性能文件，未编码、外搜或修改v12/v13旧seal；本包不是执行提示或容量预算。ROOT另行事前冻结后才执行；有限纯来源准备到此停止。\n')
for entry in parent_seal['output_files']: assert bind(entry['absolute_path']) == entry
for entry in src._base.load_manifest()['files']: original_checked(entry['path'], entry['sha256'])
for entry in [manifest['fixed_order_sources'][0], manifest['fixed_order_sources'][1], manifest['source36_for_unchanged_record_comparison']]:
    assert bind(entry['absolute_path'])['sha256'] == entry['sha256']
outputs = [bind(OUT / name) for name in ['common-source-bundles.jsonl', 'source-resource-index.json', 'manifest.json', 'README.md', 'export_package.py']]
delivery = {'seal_type': 'fixed_existing_development77_common_source_v13',
            'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'configured_model': 'gpt-6.1-sol', 'configured_reasoning_effort': 'ultra',
            'output_files': outputs, 'parent_v13_seal': bind(seal_path), 'record_N': 77,
            'fixed_record_ID_order_UTF8_LF_sha256': resource_index['fixed_ID_order_UTF8_LF_sha256'],
            'common_manual_binding_only': manifest['common_manual_binding_only'], 'actual_bytes_and_assets': counts,
            'original_inputs_not_modified': True, 'coding_or_new_independent_validation': False,
            'joint_freeze_status': 'pending_ROOT'}
dump('delivery-seal.json', delivery)
print(json.dumps({'directory': str(OUT), 'seal': bind(OUT / 'delivery-seal.json'), 'packet': bind(packet), 'counts': counts}, ensure_ascii=False, indent=2))
