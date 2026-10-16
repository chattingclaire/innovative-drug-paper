"""Finite source-SHA extension of the sealed v12 accessor. No coding or read inference."""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
MANIFEST_SHA = 'd3d1e365e9756ed8334ed3cce4941a28c18d0735f7b856aeec7fe139e40fd0d3'

def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def h(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def _checked_json(path, expected):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('source byte SHA mismatch: ' + str(path))
    return json.loads(raw)

_manifest = _checked_json(OUT / 'source-extension-manifest.json', MANIFEST_SHA)
_interface = _manifest['base_interface']
if hashlib.sha256(Path(_interface['absolute_path']).read_bytes()).hexdigest() != _interface['sha256']:
    raise ValueError('sealed base interface SHA mismatch')
_spec = importlib.util.spec_from_file_location('sealed_v12_source_accessor', _interface['absolute_path'])
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

def extension_registry():
    for entry in _manifest['new_source_originals'] + [_manifest['source_addendum']]:
        raw = Path(entry['absolute_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('extension original source SHA mismatch: ' + entry['absolute_path'])
    entry = next(z for z in _manifest['extension_files']
                 if Path(z['absolute_path']).name == 'source-resource-registry.json')
    return _checked_json(entry['absolute_path'], entry['sha256'])

def extend_bundle(old_bundle):
    """Availability binding is source identity only, never a unit ID or semantic decision."""
    registry = extension_registry()
    record = old_bundle['source_record']
    source_shas = {record['source_ref']['sha256']} | {
        z['source_ref']['sha256'] for z in record['contexts']}
    if registry['binding_source_sha256'] not in source_shas:
        return old_bundle
    result = copy.deepcopy(old_bundle)
    result['explicit_or_primary_source_resources'].append(copy.deepcopy(registry['document_resource']))
    result['source_full_text_resources'].extend(copy.deepcopy(registry['paragraph_resources']))
    result['source_bundle_extension'] = {
        'version': 'v13-source-addendum',
        'base_bundle_version': 'v12',
        'old_bundle_sha256': h(cj(old_bundle)),
        'extension_manifest_sha256': MANIFEST_SHA,
        'binding_source_sha256': registry['binding_source_sha256'],
        'available_added_paragraph_resource_N': len(registry['paragraph_resources']),
        'availability_scope': 'document-SHA inventory; applicability requires current-source reading',
        'actual_consumer_read_status': 'not_recorded',
        'actual_consumer_use_status': 'not_recorded',
    }
    return result

def lookup(record_id, selector='model', bundle=True):
    old = _base.lookup(record_id, selector, bundle=bundle)
    if selector == 'unit' or not bundle:
        return old
    return extend_bundle(old)

def source_inventory(bundle):
    """Keep old inventories; describe literal JSON/HTML paragraphs without invented page geometry."""
    paragraphs = [z for z in bundle['source_full_text_resources']
                  if isinstance(z, dict) and isinstance(z.get('source_locator'), dict)
                  and z['source_locator'].get('kind') == 'structured_JSON_and_original_HTML']
    base_view = dict(bundle)
    base_view['source_full_text_resources'] = [z for z in bundle['source_full_text_resources']
                                              if z not in paragraphs]
    inventory = _base.source_inventory(base_view)
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('interface', choices=['rule', 'model', 'human', 'unit'])
    parser.add_argument('id')
    parser.add_argument('--record-only', action='store_true')
    parser.add_argument('--inventory', action='store_true')
    args = parser.parse_args()
    try:
        result = lookup(args.id, args.interface, bundle=not args.record_only)
        if args.inventory:
            if args.record_only or args.interface == 'unit':
                raise ValueError('inventory needs complete bundle')
            result = source_inventory(result)
    except (ValueError, KeyError) as error:
        parser.error(str(error))
    print(cj(result))
