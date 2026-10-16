"""Reuse the sealed full800 draw and presentation mapping; refresh source bytes only."""
from pathlib import Path
from collections import Counter
import copy, datetime, hashlib, json, sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
OLD = ROOT / '05-validation/full800-real-blindpack-sol'
SOURCE = ROOT / '01-review/source-interface-v15-price-context-sol'
MANUAL = ROOT / '03-manual/human4-alignment-candidate-sol/manual.txt'
COORD = OUT / 'coordinator-private'
SHARED = OUT / 'shared-source'
EXT_KEY = 'v15_same_pdf_physical_page_text'
VERSION = 'full800-common-v15-prerelease-1'
DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')

def H(raw): return hashlib.sha256(raw).hexdigest()
def cj(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def parse(path): return json.loads(Path(path).read_bytes())
def bind(path):
    path = Path(path).resolve(); raw = path.read_bytes()
    return {'absolute_path': str(path), 'bytes': len(raw), 'sha256': H(raw)}
def put(path, raw):
    path = Path(path); path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open('xb') as handle: handle.write(raw)
    path.chmod(0o600)
def savejson(path, value): put(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
def savelines(path, rows): put(path, b''.join(cj(row) + b'\n' for row in rows))

# No draw code, PRNG, outcome file, or coding model is used in this refresh.
assert not (OUT / 'seal.json').exists(), 'Sealed preparation cannot be overwritten'
assert not COORD.exists() and not SHARED.exists(), 'Do not rerun over any output'
OUT.chmod(0o700)
old_before = [dict(path=str(p.relative_to(OLD)), **bind(p)) for p in sorted(OLD.rglob('*')) if p.is_file()]
input_paths = [OLD / 'prepare_blindpack.py', OLD / 'README.md', OLD / 'seal.json',
               OLD / 'coordinator-private/draw-contract.json', OLD / 'coordinator-private/mapping.json',
               OLD / 'shared-source/source-resource-index.json', OLD / 'shared-source/common-source-bundles.jsonl',
               SOURCE / 'common-frame-bundles-v15.jsonl', SOURCE / 'frame-bundle-bindings-v15.jsonl',
               SOURCE / 'source_only_interface_v15.py', SOURCE / 'source-extension-manifest-v15.json',
               SOURCE / 'pdf-extract-chain-v15.json', SOURCE / 'seal.json', MANUAL]
for side in ('A', 'B'):
    input_paths.extend(OLD / ('coder-' + side) / name for name in ('packet.jsonl', 'packet-index.json', 'packet-manifest.json', 'source-assets-index.json'))
inputs = [bind(p) for p in input_paths]
manual_binding = bind(MANUAL)
draw = parse(OLD / 'coordinator-private/draw-contract.json')
mapping = parse(OLD / 'coordinator-private/mapping.json')
selected_ids = draw['selected_record_ids_in_frame_order']
chosen = set(selected_ids)
assert len(selected_ids) == len(chosen) == draw['sample_n'] == 800
assert H(('\n'.join(selected_ids) + '\n').encode()) == draw['selected_ID_UTF8_LF_sha256']
assert len(mapping['records']) == 800 and {r['source_id'] for r in mapping['records']} == chosen
assert Counter(r['domain'] for r in mapping['records']) == {'remaining': 600, 'exposed': 200}
assert draw['domain_sample_n'] == {'remaining': 600, 'exposed': 200}
admin = {r['source_id']: r for r in mapping['records']}
orders = {}
for side in ('A', 'B'):
    key = side + '_blind_id'
    ordered = sorted(mapping['records'], key=lambda r: r[key])
    assert [r[key] for r in ordered] == [f'{side}-{i:06d}' for i in range(1, 801)]
    old_index = parse(OLD / ('coder-' + side) / 'packet-index.json')
    assert [r['blind_id'] for r in old_index['entries']] == [r[key] for r in ordered]
    with (OLD / ('coder-' + side) / 'packet.jsonl').open('rb') as handle:
        for n, line in enumerate(handle):
            outer = json.loads(line)
            assert outer['blind_id'] == ordered[n][key]
            assert outer['source_bundle']['source_record']['id'] == ordered[n]['source_id']
            assert H(line) == old_index['entries'][n]['packet_line_sha256']
    assert n + 1 == 800
    orders[side] = [r['source_id'] for r in ordered]

old_raw = {}
with (OLD / 'shared-source/common-source-bundles.jsonl').open('rb') as handle:
    for line in handle:
        raw = line.removesuffix(b'\n'); b = json.loads(raw); rid = b['source_record']['id']
        assert rid not in old_raw and cj(b) == raw
        old_raw[rid] = raw
assert list(old_raw) == selected_ids
frame_bindings = [json.loads(line) for line in (SOURCE / 'frame-bundle-bindings-v15.jsonl').open('rb')]
assert len(frame_bindings) == 4481 and len({r['id'] for r in frame_bindings}) == 4481
assert [r['frame_ordinal_1based'] for r in frame_bindings] == list(range(1, 4482))
fb = {r['id']: r for r in frame_bindings}
assert chosen <= set(fb)
FORBIDDEN = set('labels label predictions prediction expected gold reference_label rule_hit score scores confidence dimension_reasons innovation_subtypes fairness_subtypes original_coder_answer sampling_stratum stratum domain exposure weight pi development_rationale verified_context_certificates registered_exposure_status already_in_development77 family_id'.split())
def source_only(value):
    if isinstance(value, dict):
        for key, child in value.items():
            low = key.lower()
            assert low not in FORBIDDEN and not low.startswith(('machine_', 'prediction_', 'old_label', 'expected_', 'gold_')), 'Forbidden private/result key: ' + key
            source_only(child)
    elif isinstance(value, list):
        for child in value: source_only(child)

raw_by_id = {}; bundles = {}; changed = []
with (SOURCE / 'common-frame-bundles-v15.jsonl').open('rb') as handle:
    for ordinal, line in enumerate(handle, 1):
        rid = frame_bindings[ordinal - 1]['id']
        if rid not in chosen: continue
        raw = line.removesuffix(b'\n'); b = json.loads(raw); expected = fb[rid]
        assert b['source_record']['id'] == rid and cj(b) == raw
        assert H(raw) == expected['new_v15_bundle_sha256'] and len(raw) == expected['new_v15_bundle_utf8_bytes']
        assert H(old_raw[rid]) == expected['old_v14_bundle_sha256'] and len(old_raw[rid]) == expected['old_v14_bundle_utf8_bytes']
        assert H(cj(b['source_record'])) == expected['source_record_object_sha256']
        source_only(b)
        old_bundle = json.loads(old_raw[rid])
        has_extension = EXT_KEY in b.get('source_bundle_extension', {})
        if has_extension:
            assert expected['added_FULLSOURCE_payload_N'] == 1 and expected['added_physical_page_N'] == 4
            restored = copy.deepcopy(b)
            del restored['source_bundle_extension'][EXT_KEY]
            if not restored['source_bundle_extension']: del restored['source_bundle_extension']
            removed = restored['source_full_text_resources'].pop()
            assert removed['physical_pages'] == [8, 9, 20, 21]
            sha = b['source_bundle_extension'][EXT_KEY]['source_pdf_sha256']
            matching_docs = [d for d in restored['source_documents'] if d['source_sha256'] == sha]
            assert len(matching_docs) == 1
            del matching_docs[0]['source_text_resource']
            assert cj(restored) == old_raw[rid], 'v15 changes exceed sealed extension'
            changed.append(rid)
        else:
            assert raw == old_raw[rid] and expected['added_FULLSOURCE_payload_N'] == 0 and expected['added_physical_page_N'] == 0
        assert b['source_record'] == old_bundle['source_record']
        assert b['source_locator_bases'] == old_bundle['source_locator_bases']
        assert b['source_asset_locations'] == old_bundle['source_asset_locations']
        bundles[rid] = b; raw_by_id[rid] = raw
assert list(raw_by_id) == selected_ids and len(changed) == 55

COORD.mkdir(mode=0o700); SHARED.mkdir(mode=0o700)
put(COORD / 'draw-contract.json', (OLD / 'coordinator-private/draw-contract.json').read_bytes())
put(COORD / 'mapping.json', (OLD / 'coordinator-private/mapping.json').read_bytes())
old_source_index = parse(OLD / 'shared-source/source-resource-index.json')
old_per = {r['source_id']: r for r in old_source_index['per_record']}
files = {}
def register(path, sha, kind, source_ids, locator=None, expected_bytes=None):
    path = Path(path).resolve(); raw = path.read_bytes()
    assert H(raw) == sha and (expected_bytes is None or len(raw) == expected_bytes), 'Missing or mismatched actual source asset: ' + str(path)
    if sha not in files:
        dest = SHARED / 'source-files' / (sha + (path.suffix.lower() or '.bin'))
        put(dest, raw)
        files[sha] = {'sha256': sha, 'bytes': len(raw), 'prepared_absolute_path': str(dest),
                      'prepared_relative_path': str(dest.relative_to(OUT)), 'original_absolute_paths': [],
                      'resource_kinds': [], 'source_ids': [], 'source_locators': [], 'image_pixels': None}
    entry = files[sha]
    assert entry['bytes'] == len(raw)
    if str(path) not in entry['original_absolute_paths']: entry['original_absolute_paths'].append(str(path))
    if kind not in entry['resource_kinds']: entry['resource_kinds'].append(kind)
    for rid in source_ids:
        assert rid in chosen
        if rid not in entry['source_ids']: entry['source_ids'].append(rid)
    if locator is not None and locator not in entry['source_locators']: entry['source_locators'].append(locator)
    return sha

# The original prepared assets are byte-verified and copied, with all original identities retained.
for original in old_source_index['deduplicated_files']:
    sha = register(original['prepared_absolute_path'], original['sha256'], original['resource_kinds'][0], original['source_ids'], expected_bytes=original['bytes'])
    entry = files[sha]
    entry['original_absolute_paths'] = copy.deepcopy(original['original_absolute_paths'])
    entry['resource_kinds'] = copy.deepcopy(original['resource_kinds'])
    entry['source_locators'] = copy.deepcopy(original['source_locators'])
    entry['image_pixels'] = copy.deepcopy(original.get('image_pixels'))
assert len(files) == 133

extension_manifest = parse(SOURCE / 'source-extension-manifest-v15.json')
assert extension_manifest['binding_source_pdf_sha256'] == '64ac48e58753780279df45a96c595f6415e84fef087a316b66f26def2cd5658c'
payload_binding = extension_manifest['payload_file']
payload = parse(payload_binding['path'])
assert H(cj(payload)) == extension_manifest['payload_canonical_view_sha256']
assert len(payload['paragraphs']) == 4 and payload['physical_pages'] == [8, 9, 20, 21]
new_shas = set()
new_shas.add(register(payload_binding['path'], payload_binding['sha256'], 'v15_same_PDF_full_physical_page_JSON_payload', changed, {'source_pdf_sha256': extension_manifest['binding_source_pdf_sha256'], 'physical_pages': [8, 9, 20, 21]}, payload_binding['bytes']))
new_shas.add(register(SOURCE / 'source-extension-manifest-v15.json', H((SOURCE / 'source-extension-manifest-v15.json').read_bytes()), 'v15_source_extension_manifest', changed))
chain = extension_manifest['extract_chain_file']
new_shas.add(register(chain['path'], chain['sha256'], 'v15_original_PDF_extract_chain', changed, expected_bytes=chain['bytes']))
for paragraph, extraction in zip(payload['paragraphs'], extension_manifest['page_extractions']):
    bound = extraction['output_file']; locator = paragraph['source_locator']
    raw = Path(bound['path']).read_bytes()
    assert paragraph['text'].encode() == raw and locator['physical_page'] == extraction['physical_page']
    assert locator['fullpage_text_utf8_sha256'] == H(raw) and locator['fullpage_text_utf8_bytes'] == len(raw)
    new_shas.add(register(bound['path'], bound['sha256'], 'v15_same_PDF_full_physical_page_UTF8_text', changed, locator, bound['bytes']))

def explicit_files(value, rid, found):
    if isinstance(value, dict):
        path = value.get('absolute_path', value.get('path'))
        if isinstance(path, str) and isinstance(value.get('sha256'), str):
            found.add(register(path, value['sha256'], 'explicit_bound_file_view', [rid], expected_bytes=value.get('bytes')))
        for child in value.values(): explicit_files(child, rid, found)
    elif isinstance(value, list):
        for child in value: explicit_files(child, rid, found)

per_record = []
for rid in selected_ids:
    b = bundles[rid]; rec = b['source_record']; found = set(old_per[rid]['source_file_SHAs'])
    locator_base = Path(b['source_locator_bases']['canonical_row_attachment_relative_path_base'])
    for doc in b['source_documents']:
        found.add(register(doc['snapshot'], doc['source_sha256'], 'document_snapshot', [rid], expected_bytes=doc.get('bytes')))
        for name in ('source_text_resource', 'source_visual_text_resource', 'source_display_geometry_resource'):
            view = doc.get(name)
            if view:
                base = Path(view.get('relative_path_base', locator_base))
                found.add(register(base / view['relative_path'], view['sha256'], name, [rid], {'source_document_sha256': doc['source_sha256']}, view.get('bytes')))
    for resource in b['explicit_or_primary_source_resources']:
        snapshot = resource.get('snapshot')
        if not snapshot and resource.get('snapshot_relative_path'):
            snapshot = locator_base / 'source-library' / resource['snapshot_relative_path']
        if snapshot:
            found.add(register(snapshot, resource.get('snapshot_sha256', resource.get('source_sha256')), 'explicit_document_snapshot', [rid]))
    for image in b['source_asset_locations']:
        found.add(register(image['absolute_path'], image['sha256'], 'image_asset', [rid], {'source_document_sha256': image.get('source_pdf_sha256'), 'physical_page': image.get('physical_page')}))
    explicit_files(b, rid, found)
    entry = copy.deepcopy(old_per[rid])
    entry.update(bundle_canonical_sha256=H(raw_by_id[rid]), bundle_UTF8_bytes=len(raw_by_id[rid]),
                 source_record_canonical_sha256=H(cj(rec)), body_UTF8_sha256=H(rec['text'].encode()),
                 CTX_object_canonical_sha256=H(cj(rec['contexts'])), CTX_N=len(rec['contexts']),
                 all_original_root_fields_preserved=list(b))
    if rid in changed:
        found |= new_shas
        for paragraph in payload['paragraphs']:
            entry['available_source_inventory'].append({'resource_id': paragraph['source_paragraph_id'],
                'source_document_id': payload['source_resource_id'], 'source_sha256': payload['source_sha256'],
                'locator': copy.deepcopy(paragraph['source_locator']), 'available_views': {'text': H(paragraph['text'].encode())},
                'availability_status': 'available', 'representation': paragraph['representation'],
                'consumer_read_status': 'not_recorded', 'consumer_use_status': 'not_recorded'})
    assert len({z['resource_id'] for z in entry['available_source_inventory']}) == len(entry['available_source_inventory'])
    entry['source_file_SHAs'] = sorted(found)
    entry['v15_added_FULLSOURCE_payload_N'] = fb[rid]['added_FULLSOURCE_payload_N']
    entry['v15_added_physical_page_N'] = fb[rid]['added_physical_page_N']
    per_record.append(entry)
put(SHARED / 'common-source-bundles.jsonl', b''.join(raw_by_id[rid] + b'\n' for rid in selected_ids))
source_index = {'version': VERSION, 'source_accessor': bind(SOURCE / 'source_only_interface_v15.py'),
    'common_source_file': bind(SHARED / 'common-source-bundles.jsonl'), 'record_N': 800, 'per_record': per_record,
    'deduplicated_files': list(files.values()),
    'locator_policy': 'Original bundle locator identities remain byte-exact. Resolve each original absolute path or explicit relative_path_base plus relative_path through this index to the prepared same-SHA actual file.',
    'available_not_actual_read_or_use': True, 'image_pixels_from_file_headers_not_visual_certification': True}
savejson(SHARED / 'source-resource-index.json', source_index)

GUIDE = '''本包为共同v15来源材料预发布版（pre-release），目前不授权开始正式判读。最终开发比较和手册/来源/方法/统计联合freeze完成后，由管理员确认正式发布。
发布后按本方packet.jsonl顺序独立判读，每条依原样手册对S、E、Ec、I、F五维分别给出0或1。证据不足保留null，并记录具体待定原因和所需材料，不能把缺材或空白占位填0。
先读完整当前正文，再按手册阅读必要语境和确指同版资源及原图。原bundle的来源ID、locator与路径保留；source-assets-index.json把原路径/来源SHA定位到shared-source/source-files中的实际同SHA文件。新增四页文本位于共同v15 JSON资源，并有原PDF物理页及UTF8字节SHA定位。资源可访问不表示已经读过或用过。
不得查看另一方的标签或判读，不得查看机器/Gold/参照答案，不得请求AI代填。A/B分别分发各自目录和共同shared-source；coordinator-private只交管理员。
labels.blank.jsonl全部是unfilled/null空入口，submission.blank.json的身份、时间与读用记录也为空。本包没有创建任何真实判读或复核记录。
保存并封存原始独立初判后，再由管理员组织补材、重判和争议裁定；这些记录另存版本，保留初判，不覆盖原始结果。缺材统一报告管理员，不自行推定。
'''
packet_manifests = {}; side_indexes = {}
for side in ('A', 'B'):
    folder = OUT / ('coder-' + side); folder.mkdir(mode=0o700)
    lines = []; index = []; blanks = []; cursor = 0
    for rid in orders[side]:
        blind = admin[rid][side + '_blind_id']; raw = raw_by_id[rid]
        outer = {'packet_version': VERSION, 'blind_id': blind, 'source_bundle_canonical_sha256': H(raw),
                 'source_bundle_canonical_UTF8_bytes': len(raw), 'source_bundle': bundles[rid]}
        line = cj(outer) + b'\n'; lines.append(line)
        index.append({'blind_id': blind, 'packet_line_start_UTF8_byte': cursor,
                      'packet_line_end_UTF8_byte_exclusive': cursor + len(line), 'packet_line_sha256': H(line),
                      'source_bundle_canonical_sha256': H(raw), 'source_bundle_canonical_UTF8_bytes': len(raw)})
        cursor += len(line)
        blanks.append({'blind_id': blind, 'source_bundle_canonical_sha256': H(raw), 'completion_status': 'unfilled',
                       'dimensions': {d: {'value': None, 'evidence_path': None, 'current_quote': None, 'context_quotes': [],
                                          'source_quotes': [], 'reason': None, 'material_request': None} for d in DIMENSIONS}})
    put(folder / 'packet.jsonl', b''.join(lines)); savejson(folder / 'packet-index.json', {'version': VERSION, 'side': side, 'record_N': 800, 'entries': index})
    put(folder / 'manual.txt', MANUAL.read_bytes()); put(folder / '操作说明.txt', GUIDE.encode())
    savelines(folder / 'labels.blank.jsonl', blanks)
    savejson(folder / 'source-assets-index.json', {'version': VERSION, 'files': list(files.values()), 'availability_not_reading_or_use': True})
    manifest = {'packet_version': VERSION, 'status': 'pre_release_no_formal_coding_authorized', 'side': side,
        'record_N': 800, 'dimension_blank_N': 4000, 'packet_file': bind(folder / 'packet.jsonl'),
        'packet_index': bind(folder / 'packet-index.json'), 'manual': dict(bind(folder / 'manual.txt'), declared_status='exact candidate bytes; final release freeze pending'),
        'blank_labels_file': bind(folder / 'labels.blank.jsonl'), 'source_asset_index': bind(folder / 'source-assets-index.json'),
        'common_bundle_multiset_SHA256': H(cj(sorted(H(raw_by_id[rid]) for rid in selected_ids))),
        'real_executor_assigned': False, 'real_executor_code': None, 'identity_registry_SHA256': None,
        'final_release_freeze_completed': False, 'source_bytes_equal_to_common_v15': True,
        'original_current_body_context_and_locators_unchanged': True}
    savejson(folder / 'packet-manifest.json', manifest); packet_manifests[side] = manifest; side_indexes[side] = index
    savejson(folder / 'submission.blank.json', {'version': VERSION, 'completion_status': 'unfilled',
        'packet_file_sha256': manifest['packet_file']['sha256'], 'manual_sha256': manual_binding['sha256'],
        'record_N': 800, 'dimensions_N': 4000, 'actual_actor_type': None, 'executor_code': None,
        'identity_registry_sha256': None, 'actual_started_at': None, 'actual_submitted_at': None,
        'labels_sha256': None, 'independence_declaration': None, 'AI_assistance': None,
        'image_view_records': None, 'source_read_or_use_attestation': None, 'human_coding_completed': False})

# One finite read-back verifies the actual generated files, without semantic coding.
seen = {}; blank_N = 0
for side in ('A', 'B'):
    folder = OUT / ('coder-' + side); material = {}
    for n, line in enumerate((folder / 'packet.jsonl').open('rb')):
        outer = json.loads(line); rid = outer['source_bundle']['source_record']['id']; raw = cj(outer['source_bundle'])
        assert rid == orders[side][n] and outer['blind_id'] == admin[rid][side + '_blind_id']
        assert raw == raw_by_id[rid] and H(line) == side_indexes[side][n]['packet_line_sha256']
        assert outer['source_bundle_canonical_sha256'] == H(raw) and outer['source_bundle_canonical_UTF8_bytes'] == len(raw)
        source_only(outer['source_bundle']); material[rid] = H(raw)
    assert len(material) == 800 and set(material) == chosen
    seen[side] = material
    for n, line in enumerate((folder / 'labels.blank.jsonl').open('rb')):
        value = json.loads(line); assert value['completion_status'] == 'unfilled' and set(value['dimensions']) == set(DIMENSIONS)
        assert value['blind_id'] == side_indexes[side][n]['blind_id']
        assert value['source_bundle_canonical_sha256'] == side_indexes[side][n]['source_bundle_canonical_sha256']
        for dim in value['dimensions'].values():
            assert all(dim[k] is None for k in ('value', 'evidence_path', 'current_quote', 'reason', 'material_request'))
            assert dim['context_quotes'] == [] and dim['source_quotes'] == []
            blank_N += 1
    assert bind(folder / 'manual.txt')['sha256'] == manual_binding['sha256']
    submission = parse(folder / 'submission.blank.json')
    assert submission['completion_status'] == 'unfilled' and submission['human_coding_completed'] is False
    assert all(value is None for key, value in submission.items() if key in ('actual_actor_type', 'executor_code', 'identity_registry_sha256', 'actual_started_at', 'actual_submitted_at', 'labels_sha256', 'independence_declaration', 'AI_assistance', 'image_view_records', 'source_read_or_use_attestation'))
assert seen['A'] == seen['B'] and blank_N == 8000
for asset in files.values():
    actual = bind(asset['prepared_absolute_path'])
    assert actual['sha256'] == asset['sha256'] and actual['bytes'] == asset['bytes']
for original in old_before: assert bind(original['absolute_path']) == {k: original[k] for k in ('absolute_path', 'bytes', 'sha256')}
assert [str(p.relative_to(OLD)) for p in sorted(OLD.rglob('*')) if p.is_file()] == [b['path'] for b in old_before]
for original in inputs: assert bind(original['absolute_path']) == original
assert (COORD / 'mapping.json').read_bytes() == (OLD / 'coordinator-private/mapping.json').read_bytes()
assert (COORD / 'draw-contract.json').read_bytes() == (OLD / 'coordinator-private/draw-contract.json').read_bytes()
assert not list(OUT.rglob('*.xlsx'))

checks = {'version': VERSION, 'selected_N': 800, 'unique_N': 800, 'no_new_draw': True,
    'remaining_selected_N': 600, 'exposed_selected_N': 200, 'all800_is_new_holdout': False,
    'selected_ID_UTF8_LF_sha256': draw['selected_ID_UTF8_LF_sha256'],
    'original_draw_contract_and_mapping_byte_exact': True, 'A_B_original_order_and_blind_IDs_preserved': True,
    'A_B_all800_source_bundle_bytes_equal_to_selected_common_v15': True,
    'v15_changed_bundle_N': len(changed), 'unchanged_v14_bundle_N': 800 - len(changed),
    'v15_added_material_distinct_JSON_payload_N': 1, 'v15_added_physical_page_text_file_N': 4,
    'original_current_body_context_and_locator_values_exact': True,
    'candidate_manual_bytes_and_SHA_preserved_both_sides': True, 'manual_sha256': manual_binding['sha256'],
    'blank_dimension_slots_N': blank_N, 'all_blank_values_null_unfilled': True, 'new_human_or_AI_judgment_N': 0,
    'prepared_actual_file_distinct_SHA_N': len(files), 'prepared_actual_file_total_bytes_deduplicated': sum(x['bytes'] for x in files.values()),
    'added_v15_distinct_material_and_provenance_asset_SHA_N': len(new_shas),
    'all_prepared_assets_accessible_with_same_SHA': True, 'original_old_files_hash_unchanged_N': len(old_before),
    'original_old_file_set_unchanged': True, 'bound_input_files_unchanged_N': len(inputs),
    'private_sampling_or_exposure_or_prediction_keys_in_source_bundles_N': 0,
    'XLSX_created_N': 0, 'unresolved_mechanical_missing_assets_N': 0,
    'final_release_freeze_completed': False, 'independent_delivery_permissions_tested': False,
    'resource_availability_is_not_read_or_use_attestation': True}
savejson(OUT / 'mechanical-checks.json', checks)
savejson(COORD / 'refresh-contract.json', {'version': VERSION, 'created_at_utc': now(),
    'status': 'pre_release', 'sampling_execution': 'reuse_only; no draw performed',
    'original_draw_contract': bind(OLD / 'coordinator-private/draw-contract.json'),
    'copied_original_draw_contract': bind(COORD / 'draw-contract.json'),
    'original_mapping': bind(OLD / 'coordinator-private/mapping.json'), 'copied_original_mapping': bind(COORD / 'mapping.json'),
    'domain_sample_n_preserved': draw['domain_sample_n'], 'selected_source_IDs_in_frame_order': selected_ids,
    'v15_material_added_source_IDs_in_frame_order': changed,
    'old_files_before_and_after_equal': old_before, 'input_bindings': inputs,
    'manual_candidate_binding': manual_binding, 'final_release_freeze_completed': False})
savejson(OUT / 'preparation-status.json', {'version': VERSION, 'status': 'source_refresh_complete_pre_release',
    'new_draw_N': 0, 'record_N': 800, 'actual_formal_human_coding_started': False,
    'new_human_labels_N': 0, 'new_AI_labels_N': 0, 'human_review_columns_added_N': 0,
    'XLSX_created_N': 0, 'candidate_manual_exact_copy': True, 'final_release_freeze_completed': False,
    'release_pending': ['ROOT final development comparison', 'joint manual/source/methods/statistics freeze', 'formal independent distribution and access confirmation'],
    'missing_asset_condition': 'No mechanical missing file/hash condition found. Any substantive insufficiency during actual reading must remain null with reason and material request, then be resolved through common supplement and separately retained judgments.'})
put(OUT / 'README.md', '''共同v15正式800来源包的pre-release准备版。沿用既有一次800条抽样、A/B盲号与顺序，未重抽；coordinator-private中draw-contract.json与mapping.json为旧契约原始字节副本。原曝光域仍为remaining600与exposed200，800全体不能称为新的holdout。

coder-A/B各800条完整共同v15 bundle，源材料canonical字节逐条与v15原框架一致。55条新增同一原PDF的四页文本payload，其余745条bundle字节与原v14一致。原body、CTX、locator身份保留；共享文件实际同SHA副本在shared-source/source-files，双方source-assets-index.json给出相同绝对/相对路径及原路径绑定。完整来源可访问不代表实际已阅读或使用。

手册为03-manual/human4-alignment-candidate-sol/manual.txt原始字节副本，未修改正文、未追认为已release。JSON入口先行，8000个五维槽仍为unfilled/null，未生成XLSX、真人复核栏、判读、身份或时间记录。A/B仅分别接收本方目录及共同shared-source；coordinator-private只供管理员。

等待ROOT最后开发比较、手册/来源/方法/统计联合freeze和正式独立分发确认后才能启动正式判读。操作说明要求五维独立0/1，证据不足留null及具体待定原因，不能查看另一方或机器；保留原始独立初判后再裁定。
'''.encode('utf-8'))
put(OUT / 'report.md', f'''本次完成同800条纯来源v15刷新，状态pre-release，release尚未完成。

有限机械核对：A/B各800条，原来源范围、顺序与盲号不变；remaining600/exposed200契约与mapping原字节保留；55条有v15同原PDF四页新增资源，745条bundle原v14字节未变；所有A/B bundle逐条等于共同v15框架字节；正文、CTX及原locator身份保留；候选手册两侧原SHA一致；8000维空槽均unfilled/null。

完整共享资产实际复制并核对{len(files)}个不同SHA文件（{sum(x['bytes'] for x in files.values())}字节）；新增v15为一个JSON payload、4个UTF8物理页文件及2个来源链元数据，共{len(new_shas)}个新SHA。索引明确使用资源自身relative_path_base解析新增JSON原定位，A/B共享同SHA路径。未发现机械缺材；实际判读中的证据不足须保留null、原因及统一补材条件，不能0填。

旧目录{len(old_before)}个文件和{len(inputs)}个绑定输入的字节SHA均未变。未读取A/B77标签、机器预测、Gold或指标；未做语义编码、未重抽、未创建XLSX或真人复核栏。未发明参与者或执行时间。文件可读核对不代替独立分发权限测试或真实阅读/使用记录。

后续条件：ROOT完成最后开发比较，联合freeze候选手册、共同来源与方法统计契约，再确认正式独立分发；在此之前不授权正式判读。member输入输出见seal.json，机械结果见mechanical-checks.json，旧抽样/曝光契约见coordinator-private。
'''.encode('utf-8'))

members = [dict(path=str(p.relative_to(OUT)), **bind(p)) for p in sorted(OUT.rglob('*')) if p.is_file()]
savejson(OUT / 'seal.json', {'version': VERSION, 'created_at_utc': now(), 'status': 'pre_release',
    'new_draw_N': 0, 'coding_released': False, 'final_release_freeze_completed': False,
    'new_human_labels_N': 0, 'new_AI_labels_N': 0, 'input_N': len(inputs), 'input_bindings': inputs,
    'members_N': len(members), 'members': members, 'member_table_sha256': H(cj(members)),
    'self_hash_policy': 'seal.json excluded from own member table; all other input/output bindings are byte SHA256',
    'no_existing_file_overwritten': True})
print(json.dumps({'status': 'pre_release_source_refresh_sealed', 'record_N': 800, 'changed_bundle_N': len(changed),
    'assets_N': len(files), 'asset_bytes': checks['prepared_actual_file_total_bytes_deduplicated'],
    'blank_slots_N': blank_N, 'old_files_unchanged_N': len(old_before), 'members_N': len(members),
    'manual_sha256': manual_binding['sha256'], 'final_release_freeze_completed': False}, ensure_ascii=False))
