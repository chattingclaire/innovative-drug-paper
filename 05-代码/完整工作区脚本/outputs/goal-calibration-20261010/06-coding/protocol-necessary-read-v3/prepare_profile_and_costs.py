"""One all-frame mechanical cost/profile pass; no semantic outputs or sampling."""
import copy
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from packet_builder import canonical, file_sha, parse, profile_from_sealed_shapes, prompt_bytes, require, sha, walk

ROOT = Path(__file__).resolve().parent
binding = parse((ROOT / 'parent-binding.pending.json').read_bytes())
for key in ['owner_accessor', 'frame_bundle_bindings', 'field_shape_counts']:
    entry = binding[key]; require(file_sha(entry['path']) == entry['sha256'], 'sealed source metadata changed')
spec = importlib.util.spec_from_file_location('cost_only_sealed_v13_source', binding['owner_accessor']['path'])
src = importlib.util.module_from_spec(spec); spec.loader.exec_module(src)
base = src._base
# Process-local caches preserve exact accessor return values; no file/code edit.
original_checked, original_rows, original_manifest = base.checked, base.rows, base.load_manifest
@lru_cache(maxsize=None)
def checked_cached(path, digest, size, mtime):
    return original_checked(path, digest)
def checked(path, digest):
    p = Path(path); st = p.stat(); return checked_cached(str(p), digest, st.st_size, st.st_mtime_ns)
@lru_cache(maxsize=None)
def rows_cached(path, size, mtime):
    return original_rows(path)
def rows(path):
    p = Path(path); st = p.stat(); return rows_cached(str(p), st.st_size, st.st_mtime_ns)
@lru_cache(maxsize=None)
def manifest_cached(size, mtime):
    return original_manifest()
def manifest():
    st = (base.OUT / 'source-material-manifest-v12.json').stat(); return manifest_cached(st.st_size, st.st_mtime_ns)
base.checked, base.rows, base.load_manifest = checked, rows, manifest
src.extension_registry = lru_cache(maxsize=1)(src.extension_registry)

frozen = [parse(line) for line in Path(binding['frame_bundle_bindings']['path']).read_bytes().splitlines() if line.strip()]
metadata = parse((ROOT / 'budget-source-metadata.json').read_bytes())
records = metadata['ordered_records']; assets = metadata['asset_lookup']
require(len(frozen) == len(records) == 4481, 'all-frame metadata required')
manual = (ROOT / 'manual-v1.3.txt').read_bytes(); output_schema = (ROOT / 'output-item.schema.json').read_bytes()
fixed = {v: len(prompt_bytes([], manual, output_schema, v)) - 2 for v in ['R', 'W', 'H']}
literal_values = {}; documents = {'explicit_or_primary_source_resources': {}, 'source_full_text_resources': {}}
costs = []
for index, (expected, meta) in enumerate(zip(frozen, records), 1):
    require(expected['id'] == meta['source_id'], 'frame metadata order changed')
    bundle = src.lookup(expected['id'], 'model', bundle=True)
    raw = canonical(bundle)
    require(len(raw) == expected['new_bundle_utf8_bytes'] and sha(raw) == expected['new_bundle_sha256'], 'cost source differs from sealed whole-material binding')
    verified = [assets[key]['entry'] for key in meta['verified_asset_keys']]
    packet = {'packet_version': 'native-full-source-3', 'source_id': expected['id'], 'output_id': 'B-' + expected['id'].split('-')[1],
              'source_bundle_sha256': expected['new_bundle_sha256'], 'source_bundle': bundle, 'verified_asset_files': verified}
    compact = canonical(packet); pretty = json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode('utf-8')
    body_quote = len(json.dumps(bundle['source_record']['text'], ensure_ascii=False).encode('utf-8'))
    cost = {'id': expected['id'], 'source_bundle_sha256': expected['new_bundle_sha256'], 'source_bundle_bytes': len(raw),
            'R_array_element_bytes': len(compact), 'W_array_element_bytes': len(pretty) + 2 * (pretty.count(b'\n') + 1),
            'current_quote_json_bytes': body_quote, 'minimum_output_reserve_bytes': 5 * body_quote + 8192,
            'context_nodes': len(bundle['source_record']['contexts']), 'verified_asset_keys': meta['verified_asset_keys'],
            'extension_available': expected['extension_available']}
    costs.append(cost)
    for pointer, value in walk(bundle):
        path = '$' + '/'.join('*' if part.isdigit() else part for part in pointer.split('/'))
        key = pointer.rsplit('/', 1)[-1]
        if key == 'role' or 'status' in key:
            if not isinstance(value, (dict, list)):
                slot = literal_values.setdefault(path, [])
                if value not in slot: slot.append(value)
    for field in documents:
        for obj in bundle[field]:
            rid = obj.get('source_resource_id')
            if rid:
                digest = sha(canonical(obj)); require(rid not in documents[field] or documents[field][rid] == digest, 'conflicting full-frame public resource identity')
                documents[field][rid] = digest
    if index % 1000 == 0:
        print(json.dumps({'mechanical_cost_records_processed': index}), flush=True)

shapes = parse(Path(binding['field_shape_counts']['path']).read_bytes())
profile = profile_from_sealed_shapes(shapes, literal_values, documents)
for name, value in [('source-field-profile.json', profile),
                    ('frame-render-costs.json', {'scope': 'all4481 exact full R/W/H packet-render bytes and original frame order; technical cost inventory, no experiment sample',
                                                  'source_binding_sha256': binding['frame_bundle_bindings']['sha256'], 'source_shape_sha256': binding['field_shape_counts']['sha256'],
                                                  'asset_metadata_sha256': file_sha(ROOT / 'budget-source-metadata.json'), 'fixed_prompt_prefix_bytes': fixed,
                                                  'manual_sha256': sha(manual), 'instructions_sha256': file_sha(ROOT / 'native-reader-instructions.txt'),
                                                  'output_schema_sha256': sha(output_schema), 'scope_schema_sha256': file_sha(ROOT / 'necessary-source-scope.schema.json'),
                                                  'ordered_records': costs, 'semantic_source_text_emitted': False, 'actual_model_calls': 0,
                                                  'source_lookup_used_for_bytes_shape_identity_only': True, 'provider_capacity_inferred': False})]:
    with (ROOT / name).open('x') as handle: json.dump(value, handle, ensure_ascii=False, indent=2); handle.write('\n')
summary = {'records': len(costs), 'field_paths': len(profile['paths']), 'public_resource_fingerprints': {k: len(v) for k, v in documents.items()},
           'fixed_prompt_prefix_bytes': fixed, 'max_single_R_packet_bytes': max(x['R_array_element_bytes'] for x in costs),
           'max_single_W_array_element_bytes': max(x['W_array_element_bytes'] for x in costs),
           'max_single_contexts': max(x['context_nodes'] for x in costs), 'manual_sha256': sha(manual),
           'source_field_profile_sha256': file_sha(ROOT / 'source-field-profile.json'), 'frame_render_costs_sha256': file_sha(ROOT / 'frame-render-costs.json')}
with (ROOT / 'profile-and-cost-preparation-summary.json').open('x') as handle: json.dump(summary, handle, ensure_ascii=False, indent=2); handle.write('\n')
print(json.dumps(summary), flush=True)
