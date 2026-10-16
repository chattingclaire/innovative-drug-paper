"""Finite new binding/locator/render checks, no coding fixtures or legacy suites."""
import ast
import copy
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import packet_builder as pb
import necessary_read_gate as ng
import native_records as nr

ROOT = Path(__file__).resolve().parent
results = []
def check(name, operation):
    try:
        operation()
        results.append({'name': name, 'state': 'passed'})
    except Exception as exc:
        results.append({'name': name, 'state': 'failed', 'error_type': type(exc).__name__, 'error': str(exc)[:400]})
def expect_blocked(operation):
    try:
        operation()
    except pb.InputFailure:
        return
    raise AssertionError('expected technical rejection')
def equals(a, b):
    assert a == b

binding = pb.parse((ROOT / 'parent-binding.json').read_bytes())
schema, lookup = pb.load_owner(binding)
profile = pb.parse(Path(binding['field_profile']['path']).read_bytes())
shapes = pb.parse(Path(binding['field_shape_counts']['path']).read_bytes())
cost = pb.parse((ROOT / 'frame-render-costs.json').read_bytes())
costs = {r['id']: r for r in cost['ordered_records']}
frames = pb.load_frame_bindings(binding)
budget = pb.parse((ROOT / 'operational-budget.json').read_bytes())
registry = pb.parse(Path(binding['extension_registry']['path']).read_bytes())
manual = (ROOT / 'manual-v1.3.txt').read_bytes()
output_schema = (ROOT / 'output-item.schema.json').read_bytes()
packets = {}
for uid in ['RECODE25-01423', 'RECODE25-00859']:
    # Two technical integration fixtures, not experiment sample selection.
    bundle = lookup(uid, 'model', bundle=True)
    check('complete_packet_' + uid, lambda uid=uid, bundle=bundle: packets.setdefault(uid, pb.make_packet(bundle, schema, profile, binding['allowed_source_file_roots'])))

check('all4481_and1298_frozen_shape_coverage', lambda: equals((len(costs), len(profile['paths']), set(profile['paths'])), (4481, 1298, {'$' + p for p in shapes['field_paths']})))
def old_roots_optional_addendum():
    for uid, packet in packets.items():
        bundle = packet['source_bundle']; frame = frames[uid]
        assert set(pb.BUNDLE_KEYS) <= set(bundle)
        assert len(bundle) == (11 if frame['extension_available'] else 10)
        assert bundle['common_source_bundle_version']['version'] == 'v12'
        assert pb.sha(pb.canonical(bundle)) == frame['new_bundle_sha256']
        assert pb.sha(pb.canonical(bundle['source_record'])) == frame['source_record_object_sha256']
        assert pb.sha(pb.canonical(bundle['source_record']['contexts'])) == frame['unchanged_context_object_sha256']
        assert pb.sha(bundle['source_record']['text'].encode()) == frame['body_utf8_sha256']
check('old_roots_version_body_CTX_and_full_binding', old_roots_optional_addendum)
def negative_roots_and_hash():
    b = packets['RECODE25-01423']['source_bundle']
    for mode in ['remove_addendum', 'extra_root', 'base_version', 'tampered_full_hash']:
        changed = copy.deepcopy(b)
        if mode == 'remove_addendum': del changed['source_bundle_extension']
        if mode == 'extra_root': changed['unsupported_twelfth_root'] = True
        if mode == 'base_version': changed['common_source_bundle_version']['version'] = 'v13'
        if mode == 'tampered_full_hash': changed['source_bundle_extension']['version'] = 'changed'
        expect_blocked(lambda: pb.make_packet(changed, schema, profile, binding['allowed_source_file_roots']))
check('missing_addendum_unknown_root_and_identity_rejected', negative_roots_and_hash)
def inventory_and_scope():
    p = packets['RECODE25-01423']; inventory = ng.owner_inventory(p['source_bundle'])
    index = {v['resource_id']: v for v in inventory}
    assert len(index) == len(inventory)
    for paragraph in registry['paragraph_resources']:
        view = index[paragraph['source_resource_id']]
        assert view['source_sha256'] == paragraph['source_sha256']
        assert view['available_views']['text'] == paragraph['text_sha256']
        assert view['locator'] == paragraph['source_locator']
    scope = ng.prepare_scope(p, 'technical-binding-check', 'technical-preparation')
    assert scope['scope_version'] == 'native-necessary-read-v3'
    assert scope['necessary_source_scope_review_status'] == 'pending'
    assert scope['read_receipts'] == scope['use_receipts'] == []
    assert not scope['required_read_complete_claim']
    expect_blocked(lambda: ng.check_scope(p, scope))
check('nine_real_inventory_bindings_available_without_read_claim', inventory_and_scope)
def one_original_locator():
    paragraph = registry['paragraph_resources'][0]
    loc = paragraph['source_locator']; structured = loc['structured_snapshot']; html = loc['raw_html']
    assert pb.file_sha(structured['absolute_path']) == structured['sha256']
    value = ng.pointer_value(pb.parse(Path(structured['absolute_path']).read_bytes()), structured['json_pointer'])
    assert isinstance(value, str) and value == paragraph['text']
    assert pb.sha(value.encode()) == paragraph['text_sha256']
    raw = Path(html['absolute_path']).read_bytes()
    assert pb.sha(raw) == html['sha256']
    raw_text = raw.decode('utf-8'); position = html['locator']
    outer = raw_text[position['unicode_character_start_zero_based']:position['unicode_character_end_exclusive']]
    assert pb.sha(outer.encode()) == position['outer_html_sha256_utf8']
    assert outer.startswith('<p') and outer.endswith('</p>')
    assert 'CR/LF preserved' in html['text_view']
check('representative_real_JSON_pointer_and_raw_CRLF_HTML_span', one_original_locator)
def original_quote_subview():
    packet = packets['RECODE25-01423']; bundle = packet['source_bundle']
    paragraph = registry['paragraph_resources'][0]
    i = next(i for i, value in enumerate(bundle['source_full_text_resources']) if value.get('source_resource_id') == paragraph['source_resource_id'])
    pointer = '/source_full_text_resources/' + str(i) + '/text'
    value = ng.pointer_value(bundle, pointer)
    ng.validate_added_view(bundle, {'resource_id': paragraph['source_resource_id'], 'source_sha256': paragraph['source_sha256'],
        'view': 'text', 'view_sha256': paragraph['text_sha256'], 'scope_pointer': pointer,
        'locator': {'source_bundle_pointer': pointer}, 'encoding': 'utf8_text'})
    pb.verify_source_quote(packet, {'source_id': packet['source_id'], 'source_bundle_sha256': packet['source_bundle_sha256'],
        'bundle_pointer': pointer, 'quote': value[:2], 'span': {'start': 0, 'end': 2}})
check('original_public_text_subview_and_side_quote_without_fake_CTX', original_quote_subview)
def exact_render_formula():
    ps = list(packets.values()); records = [costs[p['source_id']] for p in ps]; n = len(ps)
    for variant in ['R', 'W', 'H']:
        expected = cost['fixed_prompt_prefix_bytes'][variant]
        expected += sum(r['W_array_element_bytes' if variant == 'W' else 'R_array_element_bytes'] for r in records)
        expected += 2 * (n - 1) + 4 if variant == 'W' else (n - 1) + 2
        assert len(pb.prompt_bytes(ps, manual, output_schema, variant)) == expected
    r = pb.prompt_bytes(ps, manual, output_schema, 'R'); h = pb.prompt_bytes(ps, manual, output_schema, 'H')
    assert r.split(b'\n', 1)[1] == h.split(b'\n', 1)[1]
    assert manual in r and pb.sha(manual) == binding['manual']['sha256']
    for packet in ps:
        uid = packet['source_id']
        assert len(pb.canonical(packet)) == costs[uid]['R_array_element_bytes']
    instructions = (ROOT / 'native-reader-instructions.txt').read_text()
    assert 'R1/R2/R3' not in instructions and '(condition,batch)' not in instructions
check('exact_full_R_W_H_byte_formula_and_H_heading_only', exact_render_formula)
check('positive_budget_max41_and_null_backend_capacity', lambda: pb.check_budget(budget))
def all_metadata_groups():
    plan = pb.parse((ROOT / 'all-frame-technical-prebatch-plan.json').read_bytes())
    assert plan['frame_record_count'] == 4481
    assert plan['model_calls'] == 0
    assert plan['original_order_coverage_complete'] is True
    assert not plan['single_record_blockers']
    assert all(pb.within_budget(group['metrics'], budget) for group in plan['batches'])
check('all_frame_prebatch_metadata_coverage', all_metadata_groups)
check('prospective_ledger_null_telemetry_no_execution', lambda: nr.check_telemetry(nr.blank_ledger()))
def syntax_and_schema():
    for name in ['packet_builder.py', 'native_records.py', 'necessary_read_gate.py', 'prepare_profile_and_costs.py', 'budget-and-prebatch.py']:
        ast.parse((ROOT / name).read_text())
    for path in ROOT.glob('*.schema.json'):
        pb.Draft202012Validator.check_schema(pb.parse(path.read_bytes()))
check('new_runtime_syntax_and_schema_definitions', syntax_and_schema)

report = {'scope': 'finite v3 delta integration only; not semantic QA, old167 or old19 suite',
          'checks': results, 'passed': sum(r['state'] == 'passed' for r in results), 'failed': sum(r['state'] == 'failed' for r in results),
          'source_lookup_calls': 2, 'model_calls': 0, 'policy_text_or_labels_emitted': False,
          'actual_read_receipts_created': 0, 'formal_sample_selected': False, 'fixtures': list(packets),
          'preparation_failure_retained': {'collector_first_attempt': 'KeyError id before source loop; corrected source_id and asset wrapper entry; tool chunk 52516d'},
          'parent_binding_sha256': pb.file_sha(ROOT / 'parent-binding.json')}
run = 1
while (ROOT / f'integration-check-run-{run:02d}.json').exists(): run += 1
with (ROOT / f'integration-check-run-{run:02d}.json').open('x') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
print(json.dumps({'run': run, 'passed': report['passed'], 'failed': report['failed'], 'checks': results}))
raise SystemExit(1 if report['failed'] else 0)
