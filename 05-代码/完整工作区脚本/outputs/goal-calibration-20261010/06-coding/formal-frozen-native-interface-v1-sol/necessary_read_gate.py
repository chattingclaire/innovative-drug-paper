"""Explicit binding adapter; sealed v3/v4 scope/read/use algorithms are unchanged."""
import hashlib, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
BINDING_PATH = None
BINDING = None
_pb = None
_base = None
_READY = False

def _checked(key):
    entry = BINDING[key]
    path = Path(entry.get('path', entry.get('absolute_path')))
    if not path.is_absolute(): raise ValueError('nonabsolute binding: ' + key)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry['sha256'] or ('bytes' in entry and len(raw) != entry['bytes']):
        raise ValueError('sealed component changed: ' + key)
    return path

def _load(key, name):
    path = _checked(key)
    if name in sys.modules:
        existing = sys.modules[name]
        if Path(existing.__file__).resolve() != path.resolve(): raise ValueError('module file differs: ' + name)
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def configure(binding_path, binding_sha256):
    global BINDING_PATH, BINDING, _pb, _base, _check_scope_v3, _READY
    path = Path(binding_path).resolve()
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding_sha256: raise ValueError('explicit runtime binding SHA differs')
    if BINDING_PATH is not None:
        if not _READY: raise ValueError('failed configuration retained; use a fresh process, no rebinding')
        if BINDING_PATH != path or hashlib.sha256(BINDING_PATH.read_bytes()).hexdigest() != binding_sha256:
            raise ValueError('one frozen runtime binding per process; no rebinding')
        return BINDING
    # Use the original strict parser, not a permissive new JSON dialect.
    probe = json.loads(raw)
    e = probe['packet_builder']; p = Path(e['path']); b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != e['sha256']: raise ValueError('packet builder SHA differs')
    BINDING_PATH, BINDING = path, probe
    _pb = _load('packet_builder', 'packet_builder')
    BINDING = _pb.parse(raw)
    for key in ['necessary_scope_schema','manual','reader_instructions','operational_budget',
                'uniform_protocol','uniform_protocol_text','base_gate','base_native_records']:
        _checked(key)
    if 'source_interface_version' not in BINDING:
        # Existing v4 binding remains valid without rewriting it.
        for key in ['inherited_v3_seal','inherited_development77_seal','parent_binding','batching_manifest']:
            _checked(key)
    else:
        for key in ['manual_component_seal','output_item_schema','public_source_quote_schema',
                    'source_profile','source_index','source_inventory_module','source_component_seal',
                    'full800_component_seal','quote_format_component_seal','owner_schema','bundle_schema','packet_schema','attempt_record_blank',
                    'transport_overlay','source_view_chunk_helper','actor_wrapper_template','adapter_gate','adapter_native_records']:
            _checked(key)
    if 'source_interface_version' in BINDING:
        for seal_key, keys in [
            ('source_component_seal',['source_profile','source_inventory_module']),
            ('full800_component_seal',['source_index','common_source_file']),
            ('manual_component_seal',['manual']),
            ('quote_format_component_seal',['output_item_schema'])]:
            sealed = _pb.parse(_checked(seal_key).read_bytes())
            members = sealed.get('members',sealed.get('files',sealed.get('output_files',[])))
            table = {str(Path(e.get('absolute_path',e.get('path'))).resolve()):e for e in members}
            for key in keys:
                e = BINDING[key]; member=table.get(str(Path(e['path']).resolve()))
                if not member or member['sha256'] != e['sha256'] or member['bytes'] != e['bytes']:
                    raise ValueError('entry not bound by actual component seal: '+key)
    _base = _load('base_gate', '_formal_inherited_v3_necessary_read_gate')
    # check_scope's exact original schema is preserved; only its binding is explicit.
    if _pb.file_sha(_base.ROOT / 'necessary-source-scope.schema.json') != BINDING['necessary_scope_schema']['sha256']:
        raise ValueError('scope schema cannot be relaxed by parameterization')
    if _pb.file_sha(_base.ROOT/'source-reading-protocol-v12.json') != BINDING['uniform_protocol']['sha256']:
        raise ValueError('uniform reading protocol cannot be relaxed by binding')
    if 'public_source_quote_schema' in BINDING and _pb.file_sha(_pb.ROOT/'source-quote.schema.json') != BINDING['public_source_quote_schema']['sha256']:
        raise ValueError('original public quote contract must remain exact')
    if 'source_interface_version' in BINDING:
        if _checked('adapter_gate').resolve() != Path(__file__).resolve(): raise ValueError('loaded gate differs from bound adapter')
        # Inventory is pure and loaded only for an actual scope check, not bind controls.
        def owner_inventory(bundle):
            owner = _load('source_inventory_module', '_formal_bound_source_inventory')
            return owner.source_inventory(bundle)
        def uniform_protocol_sha():
            return _pb.file_sha(_checked('uniform_protocol'))
        _base.owner_inventory = owner_inventory
        _base.uniform_protocol_sha = uniform_protocol_sha
    _base.inventory_views = inventory_views
    _check_scope_v3 = _base.check_scope
    _READY = True
    return BINDING

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

_EXPORTS = ('DIMENSIONS','READ_STATUSES','uniform_protocol_sha','pointer_value','source_basis',
 'owner_inventory','packet_identity','view_key','validate_added_view','base_requirements',
 'prepare_scope','dependency_output_projection')
def __getattr__(name):
    if name in _EXPORTS and _base is not None: return getattr(_base, name)
    raise AttributeError('configure frozen runtime binding before using ' + name)
