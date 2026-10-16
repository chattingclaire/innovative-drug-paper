"""Finite v13 wrapper: literal text leaves for one verified primary source SHA. No coding."""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
MANIFEST_SHA = '563cfcaf87c41e33de6b958b78a1d11d98f89dac8a373087d7121b8a6352608d'
def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def _checked_json(entry):
    raw = Path(entry['absolute_path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry['sha256'] or len(raw) != entry['bytes']:
        raise ValueError('source byte SHA/size mismatch: ' + entry['absolute_path'])
    return json.loads(raw)
_manifest_raw = (OUT / 'source-text-extension-manifest.json').read_bytes()
if hashlib.sha256(_manifest_raw).hexdigest() != MANIFEST_SHA:
    raise ValueError('text extension manifest SHA mismatch')
_manifest = json.loads(_manifest_raw)
_interface = _manifest['base_interface']
_raw = Path(_interface['absolute_path']).read_bytes()
if hashlib.sha256(_raw).hexdigest() != _interface['sha256'] or len(_raw) != _interface['bytes']:
    raise ValueError('sealed base interface SHA/size mismatch')
_spec = importlib.util.spec_from_file_location('sealed_v13_source_accessor', _interface['absolute_path'])
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
_registry_cache = None
def extension_registry():
    global _registry_cache
    if _registry_cache is None:
        value = _checked_json(_manifest['resource_file'])
        entry = _manifest['original_snapshot']; raw = Path(entry['absolute_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256'] or len(raw) != entry['bytes']:
            raise ValueError('original snapshot SHA/size mismatch')
        original = raw.decode('utf-8', errors='strict')
        resources = value['resources']
        if ''.join(z['text'] for z in resources) != original:
            raise ValueError('literal text leaves do not reconstruct original snapshot')
        for z in resources:
            if z['source_sha256'] != _manifest['binding_primary_source_sha256']:
                raise ValueError('literal text source SHA mismatch')
            text = z['text'].encode('utf-8')
            if hashlib.sha256(text).hexdigest() != z['text_utf8_sha256'] or len(text) != z['text_utf8_bytes']:
                raise ValueError('literal text leaf SHA/bytes mismatch')
        _registry_cache = value
    return _registry_cache

def extend_bundle(old_bundle):
    """Availability follows primary source SHA only; no per-ID or label condition."""
    if old_bundle['source_record']['source_ref']['sha256'] != _manifest['binding_primary_source_sha256']:
        return old_bundle
    result = copy.deepcopy(old_bundle)
    result['source_full_text_resources'].extend(copy.deepcopy(extension_registry()['resources']))
    return result

def lookup(record_id, selector='model', bundle=True):
    old = _base.lookup(record_id, selector, bundle=bundle)
    if selector == 'unit' or not bundle:
        return old
    return extend_bundle(old)

def source_inventory(bundle):
    """Literal text SHA/coordinates only; available does not mean read or used."""
    added = [z for z in bundle['source_full_text_resources']
             if isinstance(z, dict) and z.get('kind') == 'verbatim_UTF8_snapshot_text'
             and z.get('source_sha256') == _manifest['binding_primary_source_sha256']]
    base_view = dict(bundle)
    base_view['source_full_text_resources'] = [z for z in bundle['source_full_text_resources'] if z not in added]
    inventory = _base.source_inventory(base_view)
    for z in added:
        inventory.append({'resource_id': z['source_resource_id'],
                          'source_document_id': 'SOURCE-' + z['source_sha256'],
                          'source_sha256': z['source_sha256'], 'locator': copy.deepcopy(z['locator']),
                          'available_views': {'text': z['text_utf8_sha256']},
                          'availability_status': 'available',
                          'representation': 'literal original UTF8 snapshot text; bounded complete physical lines',
                          'consumer_read_status': 'not_recorded', 'consumer_use_status': 'not_recorded'})
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
