"""Isolated actual-log/protocol/stop-guard checks; no production entry or new READ."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
DRIVER = ROOT / '10-closure-20261012/rule-repair-v13/execution-preparation/rule_driver.py'
BRIDGE = DRIVER.with_name('status_bridge.py')
PROTOCOL = ROOT / '01-review/context-projection-sol/full-frame-preflight/source_reading_protocol_v12.py'


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def check_actual_route(loaded, view, decisions, bundle):
    assert bundle and isinstance(bundle.get('source_record'), dict)
    assert binding(DRIVER)['sha256'] == '979363460d383412a060e4032a3aa010660f12a0aa316fbd6c492713a54085a3'
    assert binding(PROTOCOL)['sha256'] == 'edec7a03cb29b835f106acb55f306ad8fe4767d3964fdf130e2f3f91754ff076'
    bridge = {'__name__': 'NONHUMAN_status_bridge'}
    exec(compile(BRIDGE.read_bytes(), str(BRIDGE), 'exec'), bridge)
    tree = ast.parse(DRIVER.read_text())
    log_function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'actual_reading_log')
    stop_guard = next(n for n in ast.walk(tree) if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == 'stops')
    adapter = {'copy': copy, 'hashlib': hashlib, 'cj': cj, 'canonicalize_request': bridge['canonicalize_request']}
    exec(compile(ast.Module(body=[log_function], type_ignores=[]), str(DRIVER), 'exec'), adapter)
    facade = types.ModuleType('source_only_interface_v12')
    rid = bundle['source_record']['id']
    def lookup(record, selector='rule', **kwargs):
        assert record == rid and selector == 'rule'
        return copy.deepcopy(bundle)
    facade.lookup = lookup
    facade.source_inventory = loaded['source_packet'].source_inventory
    facade.cj = cj
    facade.CANON_SHA = hashlib.sha256(cj(bundle).encode()).hexdigest()
    facade.MANIFEST_SHA = hashlib.sha256(b'NONHUMAN_E_DEPENDENCY_CONTROL').hexdigest()
    old = sys.modules.get('source_only_interface_v12')
    sys.modules['source_only_interface_v12'] = facade
    try:
        protocol = types.ModuleType('NONHUMAN_original_source_protocol')
        protocol.__file__ = str(PROTOCOL)
        exec(compile(PROTOCOL.read_bytes(), str(PROTOCOL), 'exec'), protocol.__dict__)
    finally:
        if old is None:
            sys.modules.pop('source_only_interface_v12', None)
        else:
            sys.modules['source_only_interface_v12'] = old
    protocol.bound_source_identity = {'status': 'ISOLATED_SUPPLIED_BUNDLE_CHECK_NOT_PRODUCTION_ADOPTION'}
    protocol.producer_source_inventory = facade.source_inventory
    protocol.source_identity_resolver = lambda b: (facade.source_inventory(b), [])
    log, checked = adapter['actual_reading_log'](protocol, bundle, view, 'NONHUMAN-E-DEPENDENCY')
    assert not checked['errors'], checked['errors']
    assert log['original_source_requests'] == view.source_requests
    checked_routes = []
    for request in view.material_requests:
        route = loaded['dimensions']._material_request_route(request)
        for dim in ['S', 'E', 'Ec', 'I', 'F']:
            retained = (request in decisions[dim]['needed_material'] or
                        request in decisions[dim]['details'].get('unresolved_material_requests', []))
            assert retained == (dim in route['dimensions']), (request, dim)
        checked_routes.append({'request':request,'dimensions':route['dimensions']})
    for request in view.source_requests:
        canonical, provenance = bridge['canonicalize_request'](request)
        assert canonical in log['source_requests']
        if canonical['status'] == 'stopped':
            # The original driver guard below is authoritative for historical
            # requests; newly typed dependencies additionally bind their stop.
            if request.get('producer') in ('E_closed_content_dependency','F_finite_standard_dependency','S_finite_standard_dependency'):
                assert request['stop_reason'] in checked['dependency_stop_reasons']
                assert request in view.material_requests
    guard_env = {'stops':checked['dependency_stop_reasons'],'view':view,
                 'decisions':decisions,'canonicalize_request':bridge['canonicalize_request']}
    guard_code = compile(ast.Module(body=[stop_guard],type_ignores=[]),str(DRIVER),'exec')
    exec(guard_code,guard_env)
    # Reads still describe only actually delivered current/context views.
    inventory = {q['resource_id'] for q in log['source_inventory']}
    assert all(q['resource_id'] in inventory for q in log['read_receipts'])
    assert not any(q.get('path') == 'E_explicit_content_scope' for q in log['read_receipts'])
    return {'status':'passed_isolated_actual_log_protocol_stop_guard',
            'dimension_values':{d:v['value'] for d,v in decisions.items()},
            'checked_material_routes':checked_routes,'protocol_errors':checked['errors'],
            'dependency_stop_reasons':checked['dependency_stop_reasons'],
            'actual_driver_stop_guard_passed':True,'missing_material_READ_not_created':True,
            'original_source_requests':log['original_source_requests'],
            'canonical_source_requests':log['source_requests'],
            'read_receipt_N':len(log['read_receipts']),'use_receipt_N':len(log['use_receipts']),
            'driver_binding':binding(DRIVER),'bridge_binding':binding(BRIDGE),'protocol_binding':binding(PROTOCOL),
            'production_entry_executed':False,'isolated_facade_not_production_identity':True,
            'input_is_NONHUMAN':str(bundle['common_source_bundle_version'].get('status','')).startswith('NONHUMAN')}
