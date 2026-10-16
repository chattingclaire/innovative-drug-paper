"""Only finite-read gate +/- cases. Synthetic source tokens; no policy labels."""
import copy
import json
from pathlib import Path
from packet_builder import BUNDLE_KEYS, InputFailure, canonical, file_sha, prompt_bytes, sha
from necessary_read_gate import DIMENSIONS, check_scope, inventory_views, prepare_scope, view_key

ROOT = Path(__file__).resolve().parent
SOURCE_SHA = 'a' * 64
bundle = {key: [] for key in BUNDLE_KEYS}
bundle.update({
    'source_record': {'id': 'RECODE25-99999', 'text': 'CONSTRUCTED_BODY_TOKEN', 'pages': [1],
                      'source_ref': {'sha256': SOURCE_SHA, 'source_resource_id': 'SOURCE-CONSTRUCTED', 'locator': {'paragraph_id': 'CONSTRUCTED_BODY'}},
                      'contexts': [{'context_id': 'CTX-CONSTRUCTED', 'text': 'CONSTRUCTED_CONTEXT_TOKEN', 'kind': 'paragraph',
                                    'structure': {'sequence_index': 0}, 'source_ref': {'sha256': SOURCE_SHA, 'source_resource_id': 'SOURCE-CONSTRUCTED', 'locator': {'paragraph_id': 'CONSTRUCTED_CTX'}}}],
                      'source_attachments': [], 'source_references': []},
    'source_documents': [],
    'explicit_or_primary_source_resources': [{'source_resource_id': 'SOURCE-CONSTRUCTED', 'source_sha256': SOURCE_SHA,
                                              'source_texts': [{'source_resource_id': 'SOURCE-CONSTRUCTED-PART', 'source_sha256': SOURCE_SHA, 'text': 'CONSTRUCTED_OPTIONAL_TOKEN'}]}],
    'source_asset_locations': [{'attachment_id': 'ASSET-CONSTRUCTED', 'source_pdf_sha256': SOURCE_SHA,
                                'sha256': 'b' * 64, 'absolute_path': '/CONSTRUCTED/never-opened.png', 'physical_page': 1}],
    'source_locator_bases': {}, 'common_source_bundle_version': {'version': 'v12'},
})
packet = {'packet_version': 'native-full-source-1', 'source_id': 'RECODE25-99999', 'output_id': 'B-99999',
          'source_bundle_sha256': sha(canonical(bundle)), 'source_bundle': bundle, 'verified_asset_files': []}


def complete_read(log, view, suffix):
    return {'receipt_id': 'CONSTRUCTED-READ-' + suffix, 'run_id': log['run_id'], 'reader': log['reader'], 'source_id': log['source_id'],
            'resource_id': view['resource_id'], 'source_sha256': view['source_sha256'], 'view': view['view'],
            'view_sha256': view['view_sha256'], 'scope_pointer': view.get('scope_pointer'), 'locator_read': copy.deepcopy(view['locator']),
            'delivery_status': 'complete', 'read_attestation': 'recorded', 'tool_name': 'constructed_test_harness_no_actual_read',
            'event_id': None, 'local_event_id': 'CONSTRUCTED-EVENT-' + suffix, 'visible_return_bytes': None,
            'actual_range_or_page': {'constructed_bound_view_locator': copy.deepcopy(view['locator']), 'complete_original_view': True}}


def baseline():
    log = prepare_scope(packet, 'CONSTRUCTED-RUN', 'CONSTRUCTED-READER')
    log['necessary_source_scope_review_status'] = 'complete'
    log['scope_source_basis'] = {'note': 'Synthetic source structure only; optional document and image do not govern constructed current/context.', 'bundle_pointers': ['/source_record']}
    views = inventory_views(log['source_inventory'])
    log['read_receipts'] = [complete_read(log, views[view_key(r)], str(i)) for i, r in enumerate(log['requirements'])]
    log['required_read_complete_claim'] = True
    return log


def request_issue(log, issue_id, dimensions):
    log['source_requests'].append({'issue_id': issue_id, 'status': 'unresolved', 'detail': 'Constructed missing necessary dependency; no source interpretation.',
                                   'dependency_dimensions': list(dimensions), 'conclusions_stopped': True})


PROJECTION = {'null_dimensions': list(DIMENSIONS), 'material_request_dimensions': list(DIMENSIONS)}
results = []


def case(name, action, expect_error=False, predicate=None):
    try:
        result = action()
        passed = not expect_error and (predicate is None or predicate(result))
        evidence = result
    except InputFailure as error:
        passed = expect_error; evidence = {'error': str(error)}
    results.append({'case': name, 'passed': bool(passed), 'evidence': evidence})


case('available_document_and_image_unread_unused_is_legal', lambda: check_scope(packet, baseline()),
     predicate=lambda r: r['scope_record_valid'] and r['required_read_complete'] and r['unread_available_view_count'] == 2)


def required_unread(request=False, claim=False, projection=None):
    log = baseline(); missing = log['requirements'][-1]; log['read_receipts'].pop(); log['required_read_complete_claim'] = claim
    if request: request_issue(log, missing['requirement_id'], missing['dependency_dimensions'])
    return check_scope(packet, log, projection)


case('required_unread_cannot_be_claimed_complete', lambda: required_unread(claim=True), expect_error=True)
case('required_unread_without_request_or_stops_is_invalid', required_unread,
     predicate=lambda r: not r['required_read_complete'] and not r['scope_record_valid'])
case('required_unread_with_request_and_actual_null_projection_is_handled_but_not_read_complete',
     lambda: required_unread(True, False, PROJECTION), predicate=lambda r: r['scope_record_valid'] and not r['required_read_complete'] and r['dependency_handling_complete'])
case('request_without_actual_null_output_projection_is_invalid', lambda: required_unread(True), predicate=lambda r: not r['scope_record_valid'])


def used(image=False, add_read=False):
    log = baseline(); view = inventory_views(log['source_inventory'])[('ASSET-CONSTRUCTED', 'image', None)] if image else inventory_views(log['source_inventory'])[view_key(log['requirements'][-1])]
    receipt = log['read_receipts'][-1]
    if add_read:
        receipt = complete_read(log, view, 'IMAGE'); log['read_receipts'].append(receipt)
    log['use_receipts'].append({'resource_id': view['resource_id'], 'source_sha256': view['source_sha256'], 'view': view['view'], 'view_sha256': view['view_sha256'],
                               'scope_pointer': view.get('scope_pointer'), 'use_status': 'used', 'read_receipt_id': receipt['receipt_id'], 'use_scope': 'Constructed exact-view use.'})
    return check_scope(packet, log)


case('used_same_resource_same_view_complete_read_is_legal', used, predicate=lambda r: r['scope_record_valid'])
case('text_receipt_cannot_supply_image_use', lambda: used(True), expect_error=True)
case('optional_image_actual_same_view_read_then_use_is_legal', lambda: used(True, True), predicate=lambda r: r['scope_record_valid'])


def unresolved(handled=False):
    log = baseline(); log['required_read_complete_claim'] = False
    log['reference_resolution'].append({'reference_id': 'CONSTRUCTED-REF', 'citation_literal': 'CONSTRUCTED_REFERENCE_TOKEN',
                                        'source_basis': {'note': 'Constructed explicit unresolved edition dependency.', 'bundle_pointers': ['/source_record/text']},
                                        'necessary_dependency': True, 'dependency_dimensions': ['I'], 'resolution_status': 'unresolved',
                                        'target_requirement_id': None, 'target_source_sha256': None, 'identity_basis_pointers': []})
    if handled: request_issue(log, 'CONSTRUCTED-REF', ['I'])
    return check_scope(packet, log, PROJECTION if handled else None)


case('necessary_unresolved_reference_without_stop_is_invalid', unresolved, predicate=lambda r: not r['scope_record_valid'])
case('necessary_unresolved_reference_with_request_and_stops_is_handled', lambda: unresolved(True), predicate=lambda r: r['scope_record_valid'] and not r['required_read_complete'])


def mutate(field, value):
    log = baseline(); log[field] = value; return check_scope(packet, log)


case('pending_scope_review_cannot_pass', lambda: mutate('necessary_source_scope_review_status', 'pending'), expect_error=True)
case('full_bundle_sha_mismatch_blocks', lambda: mutate('source_bundle_sha256', 'c' * 64), expect_error=True)


def wrong_read_sha():
    log = baseline(); log['read_receipts'][0]['view_sha256'] = 'c' * 64; return check_scope(packet, log)


case('same_resource_wrong_view_sha_blocks', wrong_read_sha, expect_error=True)


def technical_truncation():
    log = baseline(); image = inventory_views(log['source_inventory'])[('ASSET-CONSTRUCTED', 'image', None)]
    receipt = complete_read(log, image, 'TRUNCATED'); receipt['delivery_status'] = 'truncated'; log['read_receipts'].append(receipt)
    return check_scope(packet, log)


case('observed_technical_truncation_remains_failure_even_when_optional', technical_truncation,
     predicate=lambda r: r['required_read_complete'] and not r['scope_record_valid'] and bool(r['observed_technical_read_failures']))


def added_subview(wrong_sha=False):
    log = baseline(); pointer = '/explicit_or_primary_source_resources/0/source_texts/0/text'
    view = {'resource_id': 'SOURCE-CONSTRUCTED-PART', 'source_sha256': SOURCE_SHA, 'view': 'text',
            'view_sha256': 'c' * 64 if wrong_sha else sha('CONSTRUCTED_OPTIONAL_TOKEN'.encode()),
            'scope_pointer': pointer, 'locator': {'source_bundle_pointer': pointer}, 'encoding': 'utf8_text'}
    log['additional_views'].append(view)
    log['requirements'].append({'requirement_id': 'CONSTRUCTED-SUBVIEW-REQ', 'resource_id': view['resource_id'], 'view': view['view'],
                                'scope_pointer': pointer, 'source_relation_kind': 'necessary_explicit_reference', 'source_evidence_locator': view['locator'],
                                'source_basis': {'note': 'Constructed literal necessary subview, entire document remains available and unread.', 'bundle_pointers': [pointer]}, 'dependency_dimensions': ['I']})
    log['read_receipts'].append(complete_read(log, view, 'SUBVIEW'))
    return check_scope(packet, log)


case('necessary_original_pointer_subview_does_not_force_full_document_read', added_subview,
     predicate=lambda r: r['scope_record_valid'] and r['unread_available_view_count'] == 2)
case('subview_original_hash_mismatch_blocks', lambda: added_subview(True), expect_error=True)


def removed_base():
    log = baseline(); log['requirements'].pop(); return check_scope(packet, log)


case('current_body_CTX_base_requirement_cannot_be_dropped', removed_base, expect_error=True)


def packet_dropped():
    changed = copy.deepcopy(packet); changed['source_bundle'].pop('source_full_text_resources'); return check_scope(changed, baseline())


case('original_ten_key_packet_drop_blocks', packet_dropped, expect_error=True)

# Only presentation/hash binding checks. No full source validation or old tests.
manual = (ROOT / 'manual-v1.1.txt').read_bytes(); schema = (ROOT / 'output-item.schema.json').read_bytes()
index = [{'source_id': packet['source_id'], 'output_id': packet['output_id'], 'source_bundle_sha256': packet['source_bundle_sha256'],
          'complete_packet_file': {'path': '/CONSTRUCTED/compact.json', 'sha256': 'd' * 64}}]
pr = prompt_bytes([packet], manual, schema, 'R', index); ph = prompt_bytes([packet], manual, schema, 'H', index)
pw = prompt_bytes([packet], manual, schema, 'W', index)
case('R_repeats_same_bytes_H_only_first_heading_W_same_index_values',
     lambda: {'R_sha256': sha(pr), 'H_sha256': sha(ph), 'W_sha256': sha(pw), 'R_repeat_identical': pr == prompt_bytes([packet], manual, schema, 'R', index),
              'H_only_first_heading': ph == pr.replace('判读要求'.encode(), '判读说明'.encode(), 1),
              'W_contains_semantically_equal_index': json.loads(pw.decode().split('完整有序来源文件索引（完整文件交付/可访问/hash核对；必要视图须实际完整读）：\n', 1)[1]) == index,
              'manual_original_sha256': sha(manual)},
     predicate=lambda r: r['R_repeat_identical'] and r['H_only_first_heading'] and r['W_contains_semantically_equal_index'] and r['manual_original_sha256'] == '6ffc7b35a5cbe1c1f90c81d24d1508dba7adefe5e7bbd058c284d76e14b8a70f')

report = {'scope': 'only necessary-read gate +/- and prompt/full-bundle/view hash binding', 'fixture': 'constructed tokens only; no real record lookup, no policy labels/candidate outputs, no images opened',
          'actual_model_calls': 0, 'new_source_selection': False, 'owner_lookup_called': False, 'old167_tests_rerun': False, 'full_source_checks_rerun': False,
          'cases': results, 'total': len(results), 'passed': sum(r['passed'] for r in results), 'failed': sum(not r['passed'] for r in results),
          'gate_sha256': file_sha(ROOT / 'necessary_read_gate.py'), 'native_records_sha256': file_sha(ROOT / 'native_records.py'),
          'scope_schema_sha256': file_sha(ROOT / 'necessary-source-scope.schema.json'), 'instructions_sha256': file_sha(ROOT / 'native-reader-instructions.txt')}
with (ROOT / 'necessary-gate-results.run02.json').open('x') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
print(json.dumps({'total': report['total'], 'passed': report['passed'], 'failed': report['failed']}))
raise SystemExit(0 if not report['failed'] else 1)
