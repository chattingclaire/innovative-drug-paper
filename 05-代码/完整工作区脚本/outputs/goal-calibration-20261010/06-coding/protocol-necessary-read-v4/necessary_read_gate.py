"""Minimal v4 gate overlay over sealed v3; never impute source identity."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
BINDING_PATH = ROOT / 'native-binding.json'
BINDING = json.loads(BINDING_PATH.read_bytes())

def _checked(key):
    entry = BINDING[key]
    path = Path(entry['path'])
    if not path.is_absolute() or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
        raise ValueError('sealed inherited component changed: ' + key)
    return path

for _key in ['inherited_v3_seal', 'inherited_development77_seal', 'parent_binding',
             'necessary_scope_schema', 'manual', 'reader_instructions', 'operational_budget',
             'uniform_protocol', 'uniform_protocol_text', 'batching_manifest']:
    _checked(_key)

def _load(key, name):
    path = _checked(key)
    if name in sys.modules:
        existing = sys.modules[name]
        if Path(existing.__file__).resolve() != path.resolve():
            raise ValueError('inherited module name bound to a different file: ' + name)
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

_pb = _load('packet_builder', 'packet_builder')
_base = _load('base_gate', '_inherited_v3_necessary_read_gate')

def unbound_inventory_views(inventory):
    """Keep missing identity explicit; do not replace None with a guessed SHA."""
    result = []
    for entry in inventory:
        for view, digest in entry['available_views'].items():
            missing = []
            if not _pb.valid_sha(entry.get('source_sha256')):
                missing.append('source_sha256')
            if not _pb.valid_sha(digest):
                missing.append('view_sha256')
            if missing:
                result.append({'resource_id': entry['resource_id'], 'view': view,
                               'scope_pointer': None, 'source_sha256': entry.get('source_sha256'),
                               'view_sha256': digest, 'missing_or_invalid_identity_fields': missing})
    return result

def inventory_views(inventory):
    """Only fully bound views can satisfy a read/use or necessary requirement.

    The exact complete original inventory stays in the scope log. An unused
    available entry with incomplete identity does not reject the whole record.
    """
    result = {}
    for entry in inventory:
        for view, digest in entry['available_views'].items():
            if not _pb.valid_sha(entry.get('source_sha256')) or not _pb.valid_sha(digest):
                continue
            item = {'resource_id': entry['resource_id'], 'source_sha256': entry['source_sha256'],
                    'view': view, 'view_sha256': digest, 'scope_pointer': None, 'locator': entry['locator']}
            key = _base.view_key(item)
            _pb.require(key not in result or result[key] == item, 'conflicting inventory view identity')
            result[key] = item
    return result

# Process-local dispatch only. Neither sealed v3 code nor source inventory is changed.
_inventory_views_v3 = _base.inventory_views
_base.inventory_views = inventory_views
_check_scope_v3 = _base.check_scope

def check_scope(packet, log, output_projection=None):
    result = _check_scope_v3(packet, log, output_projection)
    unbound = unbound_inventory_views(log['source_inventory'])
    result['gate_version'] = 'native-necessary-read-gate-v4'
    result['identity_bound_view_count'] = result['available_view_count']
    result['unbound_available_view_count'] = len(unbound)
    result['unbound_available_view_identities'] = unbound
    result['available_view_count'] += len(unbound)
    result['unread_available_view_count'] += len(unbound)
    result['source_identity_imputed'] = False
    return result

for _name in ['DIMENSIONS', 'READ_STATUSES', 'uniform_protocol_sha', 'pointer_value', 'source_basis',
              'owner_inventory', 'packet_identity', 'view_key', 'validate_added_view', 'base_requirements',
              'prepare_scope', 'dependency_output_projection']:
    globals()[_name] = getattr(_base, _name)
