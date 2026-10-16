"""Only the Nil-inventory regression and original-view positive/negative cases.

Receipt dictionaries below are synthetic in-memory fixtures. They are never
saved as real reading/use records and never attest actual semantic reading.
No policy text, labels, references, performance data or old suite is emitted.
"""
import copy
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import necessary_read_gate as gate
import native_records as native

pb = gate._pb
ROOT = Path(__file__).resolve().parent
INPUTS = Path(gate.BINDING['inherited_development77_seal']['path']).parent
results = []
packets = {}
prepared = {}

def blocked(operation):
    try:
        operation()
    except pb.InputFailure:
        return
    raise AssertionError('Expected technical rejection')

def check(name, operation):
    try:
        details = operation()
        results.append({'name': name, 'state': 'passed', 'details': details})
    except Exception as exc:
        results.append({'name': name, 'state': 'failed', 'error_type': type(exc).__name__, 'error': str(exc)[:350]})

def receipt(scope, view, index):
    return {'receipt_id': 'SYNTHETIC-FIXTURE-' + str(index), 'run_id': scope['run_id'], 'reader': scope['reader'],
            'source_id': scope['source_id'], 'resource_id': view['resource_id'], 'source_sha256': view['source_sha256'],
            'view': view['view'], 'view_sha256': view['view_sha256'], 'scope_pointer': view['scope_pointer'],
            'locator_read': view['locator'], 'delivery_status': 'complete', 'read_attestation': 'recorded',
            'tool_name': 'synthetic_mechanical_fixture_not_actual_read', 'event_id': None,
            'local_event_id': 'SYNTHETIC-FIXTURE-EVENT-' + str(index), 'visible_return_bytes': None,
            'actual_range_or_page': {'fixture_only': 'No actual semantic reading event; in-memory gate contrast'}}

def baseline_scope(packet):
    scope = gate.prepare_scope(packet, 'SYNTHETIC-MECHANICAL-FIXTURE', 'NOT-AN-ACTUAL-READER')
    scope['necessary_source_scope_review_status'] = 'complete'
    scope['scope_source_basis'] = {'note': 'Synthetic mechanical gate fixture; not a real semantic scope review',
                                   'bundle_pointers': ['/source_record']}
    views = gate.inventory_views(scope['source_inventory'])
    for index, requirement in enumerate(scope['requirements']):
        scope['read_receipts'].append(receipt(scope, views[gate.view_key(requirement)], index))
    scope['required_read_complete_claim'] = True
    return scope

def extra_view(packet):
    pointer = '/source_full_text_resources/0'
    obj = gate.pointer_value(packet['source_bundle'], pointer)
    return {'resource_id': obj['source_resource_id'], 'source_sha256': obj['source_pdf_sha256'],
            'view': 'document_bundle', 'view_sha256': pb.sha(pb.canonical(obj)), 'scope_pointer': pointer,
            'locator': {'source_bundle_pointer': pointer}, 'encoding': 'canonical_json'}

def requirement(view, rid='SYNTHETIC-EXTRA-REQUIREMENT'):
    return {'requirement_id': rid, 'resource_id': view['resource_id'], 'view': view['view'],
            'scope_pointer': view.get('scope_pointer'), 'source_relation_kind': 'necessary_explicit_reference',
            'source_evidence_locator': view['locator'],
            'source_basis': {'note': 'Synthetic mechanical requirement; no semantic necessity certified',
                             'bundle_pointers': ['/source_full_text_resources/0']},
            'dependency_dimensions': ['S']}

def use(scope, view):
    r = receipt(scope, view, len(scope['read_receipts']))
    scope['read_receipts'].append(r)
    scope['use_receipts'].append({'resource_id': view['resource_id'], 'source_sha256': view['source_sha256'],
        'view': view['view'], 'view_sha256': view['view_sha256'], 'scope_pointer': view.get('scope_pointer'),
        'use_status': 'used', 'read_receipt_id': r['receipt_id'],
        'use_scope': 'Synthetic gate contrast only; not actual source use'})

def positive(uid):
    path = INPUTS / 'packets' / (uid + '.compact.json')
    packet = pb.parse(path.read_bytes())
    packet_files = {Path(e['path']): e['sha256'] for e in pb.parse((INPUTS / 'delivery-seal.json').read_bytes())['files']}
    assert pb.file_sha(path) == packet_files[path]
    gate.packet_identity(packet)
    scope = baseline_scope(packet)
    before = pb.canonical(scope['source_inventory'])
    unbound = gate.unbound_inventory_views(scope['source_inventory'])
    assert len(unbound) == 1 and unbound[0]['source_sha256'] is None
    blocked(lambda: gate._inventory_views_v3(scope['source_inventory']))
    result = gate.check_scope(packet, scope)
    assert result['scope_record_valid'] and result['required_read_complete']
    assert result['unbound_available_view_count'] == 1 and not result['source_identity_imputed']
    assert result['unbound_available_view_identities'][0]['source_sha256'] is None
    assert not any(gate.view_key(r) == gate.view_key(unbound[0]) for r in scope['read_receipts'] + scope['use_receipts'])
    prepared[uid] = copy.deepcopy(scope)
    packets[uid] = packet
    view = extra_view(packet)
    gate.validate_added_view(packet['source_bundle'], view)
    assert view['resource_id'] != unbound[0]['resource_id']
    scope['additional_views'].append(view)
    scope['requirements'].append(requirement(view))
    use(scope, view)
    result = gate.check_scope(packet, scope)
    assert result['scope_record_valid'] and result['required_read_complete']
    assert pb.canonical(scope['source_inventory']) == before
    assert not result['source_identity_imputed'] and result['unbound_available_view_count'] == 1
    return {'source_id': uid, 'frozen_packet_sha256': pb.file_sha(path), 'source_bundle_sha256': packet['source_bundle_sha256'],
            'v3_global_Nil_rejection_reproduced': True, 'unbound_unused_inventory_allowed': True,
            'original_SOURCE_PDF_SHA_pointer_extra_view_with_fixture_read_use_allowed': True,
            'original_inventory_hash_unchanged': True, 'unbound_source_sha256_preserved': None}

for uid in ['RECODE25-01459', 'RECODE25-01464', 'RECODE25-01480']:
    check('Nil_unused_and_original_extra_view_' + uid, lambda uid=uid: positive(uid))

uid = 'RECODE25-01459'
def unknown_necessary():
    packet = packets[uid]; scope = copy.deepcopy(prepared[uid])
    entry = next(e for e in scope['source_inventory'] if e['source_sha256'] is None)
    view = {'resource_id': entry['resource_id'], 'view': 'text', 'scope_pointer': None, 'locator': entry['locator']}
    scope['requirements'].append(requirement(view))
    blocked(lambda: gate.check_scope(packet, scope))  # false claim of complete
    scope['required_read_complete_claim'] = False
    result = gate.check_scope(packet, scope)
    assert not result['required_read_complete'] and not result['scope_record_valid']
    assert result['dependency_stops'][-1]['reason'] == 'missing_required_source_view'
    scope['source_requests'] = [{'issue_id': 'SYNTHETIC-EXTRA-REQUIREMENT', 'status': 'unresolved',
        'detail': 'Original available inventory has no complete source identity for this necessary view',
        'dependency_dimensions': ['S'], 'conclusions_stopped': True}]
    result = gate.check_scope(packet, scope, {'null_dimensions': ['S'], 'material_request_dimensions': ['S']})
    assert result['scope_record_valid'] and not result['required_read_complete'] and result['stopped_dimensions'] == ['S']
    return {'complete_claim_rejected': True, 'unhandled_dependency_invalid': True,
            'explicit_request_and_dependent_stop_valid_without_complete_claim': True}
check('unbound_necessary_cannot_complete_and_requires_dependency_stop', unknown_necessary)

def unbound_used():
    packet = packets[uid]; scope = copy.deepcopy(prepared[uid])
    entry = next(e for e in scope['source_inventory'] if e['source_sha256'] is None)
    view = {'resource_id': entry['resource_id'], 'source_sha256': extra_view(packet)['source_sha256'],
            'view': 'text', 'view_sha256': entry['available_views']['text'], 'scope_pointer': None, 'locator': entry['locator']}
    use(scope, view)  # a guessed source SHA cannot create an inventory binding
    blocked(lambda: gate.check_scope(packet, scope))
    return {'guessed_SHA_does_not_bind_FULLSOURCE_read_or_use': True}
check('unbound_used_with_guessed_SHA_rejected', unbound_used)

def forged_original(kind):
    packet = packets[uid]; view = extra_view(packet)
    if kind == 'resource_alias':
        view['resource_id'] = gate.unbound_inventory_views(prepared[uid]['source_inventory'])[0]['resource_id']
    if kind == 'locator':
        view['locator'] = {'source_bundle_pointer': '/source_full_text_resources/1'}
    if kind == 'source_SHA':
        view['source_sha256'] = '0' * 64
    blocked(lambda: gate.validate_added_view(packet['source_bundle'], view))
    return {'invalid_original_binding_rejected': kind}
for kind in ['resource_alias', 'locator', 'source_SHA']:
    check('forged_extra_view_' + kind + '_rejected', lambda kind=kind: forged_original(kind))

assert native._base.check_scope is gate.check_scope
ledger = native.blank_ledger(); native.check_telemetry(ledger)
assert ledger['protocol_version'] == 'native-necessary-read-prospective-4'
assert ledger['receipt_scope_schema_version'] == 'native-necessary-read-v3'
report = {'scope': 'v4 Nil-unused identity threshold and true original extra-view binding only',
          'checks': results, 'passed': sum(r['state'] == 'passed' for r in results), 'failed': sum(r['state'] == 'failed' for r in results),
          'synthetic_read_and_use_receipts': 'in memory only; not saved as production records and not actual semantic reading',
          'actual_read_receipts_created': 0, 'model_calls': 0, 'source_lookup_calls': 0, 'labels_created': False,
          'policy_text_emitted': False, 'old13_19_167_suites_rerun': False, 'full_frame_scan': False,
          'native_records_dispatch_bound_to_v4': True, 'inherited_receipt_schema_and_prompts_unchanged': True,
          'binding_sha256': pb.file_sha(gate.BINDING_PATH)}
run = 1
while (ROOT / f'minimal-check-run-{run:02d}.json').exists(): run += 1
with (ROOT / f'minimal-check-run-{run:02d}.json').open('x') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
print(json.dumps({'run': run, 'passed': report['passed'], 'failed': report['failed'], 'checks': results}))
raise SystemExit(1 if report['failed'] else 0)
