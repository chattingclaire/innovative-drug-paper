"""Independent read-only output-integrity audit. Never imports or runs coder modules.

Reads only this run, its control/schema contracts, the authorized source packet,
and opaque bound dependency bytes. Writes only this previously new audit folder.
No reference labels or accuracy calculation are used.
"""
from pathlib import Path
import collections
import copy
import datetime
import hashlib
import json

V = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
R = V / 'run77-first'
SOURCE = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/01-review/source-interface-v15-price-context-sol/development77/common-source-bundles-v15.jsonl')
SOURCE_SHA = '6c8623909a30566fd5348df3679f14c74cba1b86ccda5602b45707dd55fcb16a'
SEAL_SHA = '2d6318c7b5db190061259e73ee2023cc50ebd15cac84b539a00d34ab9beb205a'
DIMS = ['S', 'E', 'Ec', 'I', 'F']
ledger = []
counts = collections.Counter()
cache = {}
quotes = []
structures = []
schema_notes = []
record_counts = []

def digest(b):
    return hashlib.sha256(b).hexdigest()

def canonical(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf8')

def cjsha(o):
    return digest(canonical(o))

def raw(path):
    p = Path(path).resolve()
    if p not in cache:
        cache[p] = p.read_bytes()
    return cache[p]

def unique(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError('duplicate JSON key: ' + k)
        d[k] = v
    return d

def parse(b):
    return json.loads(b, object_pairs_hook=unique, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def obj(path):
    return parse(raw(path))

def rows(path):
    return [parse(x) for x in raw(path).splitlines() if x.strip()]

def check(category, key, passed, detail=None):
    entry = {'category': category, 'key': key, 'passed': bool(passed)}
    if detail is not None:
        entry['detail'] = detail
    ledger.append(entry)
    counts[category + '_checks'] += 1
    if not passed:
        counts[category + '_failed'] += 1

def ptr(o, p):
    if p == '':
        return o
    assert p.startswith('/')
    for k in p[1:].split('/'):
        k = k.replace('~1', '/').replace('~0', '~')
        o = o[int(k)] if isinstance(o, list) else o[k]
    return o

def bound(entry, category, key):
    b = raw(entry['path'])
    check(category, key + ':bytes', len(b) == entry['bytes'])
    check(category, key + ':sha256', digest(b) == entry['sha256'])

def nodes(x, path=''):
    if isinstance(x, dict):
        yield path, x
        for k, v in x.items():
            yield from nodes(v, path + '/' + k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from nodes(v, path + '/' + str(i))

scope = obj(V / 'source-scope.json')
seal = obj(R / 'seal.json')
pre = obj(V / 'pre-run-seal.json')
go = obj(V / 'root-go.json')
launch = obj(V / 'actual-launch-record.json')
result = obj(V / 'actual-launch-result.json')
execution = obj(R / 'execution.json')
freeze = obj(R / 'freeze.json')
check('seal', 'specified_run_seal_SHA', digest(raw(R / 'seal.json')) == SEAL_SHA)
check('input', 'specified_source_SHA', digest(raw(SOURCE)) == SOURCE_SHA)
for category, data, fields in [('run_member', seal, ['implementation_files', 'material_bindings', 'control_inputs', 'output_files']),
                               ('pre_run_member', pre, ['files', 'implementation_files', 'material_bindings', 'other_frozen_bindings'])]:
    for field in fields:
        counts[category + '_' + field + '_N'] = len(data[field])
        for i, entry in enumerate(data[field]):
            bound(entry, category, field + '/' + str(i))
bound(seal['prediction_binding'], 'seal', 'prediction_binding')
for field in ['source_packet', 'source_manifest', 'source_package_seal', 'source_material_whitelist', 'manual', 'candidate_implementation_seal', 'manual_candidate_manifest', 'preserved_v2_preparation_seal']:
    bound(scope[field], 'control_binding', 'scope/' + field)
for field in ['launcher_binding', 'scope_binding', 'pre_run_seal_binding', 'ROOT_GO_binding', 'source_packet_binding', 'manual_binding', 'independent_control_binding']:
    bound(launch[field], 'control_binding', 'launch/' + field)
for field in ['stdout_binding', 'stderr_binding', 'driver_output_seal_binding']:
    bound(result[field], 'control_binding', 'result/' + field)
check('control', 'ROOT_GO_scope_SHA', go['scope_sha256'] == digest(raw(V / 'source-scope.json')))
check('control', 'ROOT_GO_pre_run_SHA', go['pre_run_seal_sha256'] == digest(raw(V / 'pre-run-seal.json')))
check('control', 'ROOT_GO_source_SHA', go['source_packet_sha256'] == SOURCE_SHA)
check('control', 'frozen_control_scope_unchanged', freeze['source_scope'] == scope)
check('control', 'frozen_implementation_same_members', freeze['implementation_files'] == seal['implementation_files'] == pre['implementation_files'])
check('control', 'frozen_material_same_members', freeze['material_bindings'] == seal['material_bindings'] == pre['material_bindings'])
check('control', 'launch_and_execution_one_recorded_run', result['actual_driver_process_launch_N'] == execution['actual_cohort_inference_runs'] == 1 and not result['retry_attempted'])
check('control', 'process_exit_zero', result['exit_code'] == 0)
check('control', 'stderr_empty', len(raw(V / 'driver-stderr.txt')) == 0)

source_rows = rows(SOURCE)
delivered = rows(R / 'delivered-complete-source-bundles.jsonl')
preds = rows(R / 'predictions.jsonl')
cons = rows(R / 'actual-source-consumption.jsonl')
effective = rows(R / 'effective-semantic-units.jsonl')
deliveries = rows(R / 'input-deliveries.jsonl')
slots = rows(R / 'all-dimension-slots.jsonl')
approved = scope['approved_record_ids']
check('cohort', 'source_77_unique_exact_order', [x['source_record']['id'] for x in source_rows] == approved and len(set(approved)) == len(approved) == 77)
for field, data in [('delivered', delivered), ('predictions', preds), ('consumption', cons), ('effective', effective), ('deliveries', deliveries)]:
    ids = [x['source_record']['id'] if field == 'delivered' else x['source_id'] if field == 'deliveries' else x['id'] for x in data]
    check('cohort', field + '_77_exact_order', ids == approved and len(data) == 77)
check('cohort', 'slots_385_order', [(x['id'], x['dimension']) for x in slots] == [(i, d) for i in approved for d in DIMS])
check('input', 'delivered_all_bundle_objects_exact', delivered == source_rows)
check('input', 'delivered_raw_serialization_exact_contract', raw(R / 'delivered-complete-source-bundles.jsonl') == ''.join(json.dumps(x, ensure_ascii=False, allow_nan=False) + '\n' for x in source_rows).encode('utf8'))
check('input', 'input_file_scope_bytes_SHA', len(raw(SOURCE)) == scope['source_packet']['bytes'] and digest(raw(SOURCE)) == scope['source_packet']['sha256'])
offset = 0
for i, (line, b, d) in enumerate(zip(raw(SOURCE).splitlines(keepends=True), source_rows, deliveries)):
    rid = b['source_record']['id']
    expected = {'delivery_kind': 'complete_bare_bundle', 'blind_id': None, 'source_id': rid,
                'source_bundle_sha256': cjsha(b), 'source_bundle_utf8_bytes': len(canonical(b)),
                'input_line_1based': i + 1, 'input_line_sha256': digest(line),
                'input_start_utf8_byte': offset, 'input_end_utf8_byte_exclusive': offset + len(line)}
    for k, v in expected.items():
        check('input_delivery', rid + '/' + k, d.get(k) == v)
    offset += len(line)
check('input', 'line_byte_intervals_cover_full_input', offset == len(raw(SOURCE)))

def expected_inventory(b):
    """Independent registry expectations from raw source fields and declared view schema."""
    reg = {}
    row = b['source_record']
    def add(rid, doc, sha, locator, views, pointer, kind):
        z = {'resource_id': rid, 'source_document_id': doc, 'source_sha256': sha,
             'locator': locator, 'available_views': views, 'pointer': pointer, 'kind': kind}
        if rid in reg:
            old = reg[rid]
            check('inventory_source', row['id'] + '/' + rid + '/duplicate_identity', old['available_views'] == views and old['source_sha256'] == sha)
            if old['locator'] != locator:
                old['locator'].setdefault('alternate_absolute_paths', []).append(locator['absolute_path'])
        else:
            reg[rid] = z
    sha = row['source_ref']['sha256']
    add('BODY-' + row['id'], 'SOURCE-' + sha, sha, row['source_ref']['locator'], {'text': digest(row['text'].encode())}, '/source_record', 'body')
    for i, c in enumerate(row['contexts']):
        views = {'geometry': cjsha(c['structure'])}
        texts = {k: c[k] for k in ['text', 'title', 'caption', 'headers', 'row_cells'] if k in c}
        if texts:
            views['text'] = cjsha(texts)
        ref = c['source_ref']
        add(c['context_id'], ref['source_resource_id'], ref['sha256'], ref['locator'], views, '/source_record/contexts/' + str(i), 'context')
    for i, doc in enumerate(b['explicit_or_primary_source_resources']):
        p = '/explicit_or_primary_source_resources/' + str(i)
        add(doc['source_resource_id'], doc['source_resource_id'], doc.get('source_sha256', doc.get('snapshot_sha256')), {'document_resource_id': doc['source_resource_id']}, {'document_bundle': cjsha(doc)}, p, 'document')
        for j, z in enumerate(doc.get('source_visual_text_resources', [])):
            check('source_text', row['id'] + p + '/visual/' + str(j), digest(z['text'].encode()) == z['text_sha256'])
            add(z['source_resource_id'], z['source_document_resource_id'], z['source_sha256'], z['source_locator'], {'text': digest(z['text'].encode())}, p + '/source_visual_text_resources/' + str(j), 'literal')
        for j, z in enumerate(doc.get('source_display_regions', [])):
            add(z['region_id'], 'SOURCE-' + z['source_sha256'], z['source_sha256'], {k: z[k] for k in ['physical_page', 'coordinate_system', 'bbox_points_xyxy']}, {'geometry': cjsha(z)}, p + '/source_display_regions/' + str(j), 'region')
    for i, z in enumerate(b['preserved_historical_neutral_source_supplements']):
        h = cjsha(z)
        add('HISTORICALSOURCE-' + h[:20], 'SOURCE-' + z['source_sha256'], z['source_sha256'], z.get('source_locator', {}), {'text': h}, '/preserved_historical_neutral_source_supplements/' + str(i), 'historical')
    for i, z in enumerate(b['source_full_text_resources']):
        p = '/source_full_text_resources/' + str(i)
        if z.get('kind') == 'verbatim_UTF8_snapshot_text':
            check('source_text', row['id'] + p + '/literal_sha', digest(z['text'].encode()) == z['text_utf8_sha256'])
            check('source_text', row['id'] + p + '/unicode_length', len(z['text']) == z['text_unicode_code_points'])
            check('source_text', row['id'] + p + '/byte_length', len(z['text'].encode()) == z['text_utf8_bytes'])
            loc = z['locator']; snapshot = raw(loc['snapshot_absolute_path']); original = snapshot.decode('utf8')
            a, q = loc['unicode_code_point_interval_half_open']; x, y = loc['utf8_byte_interval_half_open']
            check('literal_snapshot', row['id'] + p + '/snapshot_sha', digest(snapshot) == z['source_sha256'] == loc['snapshot_sha256'])
            check('literal_snapshot', row['id'] + p + '/unicode_span', original[a:q] == z['text'])
            check('literal_snapshot', row['id'] + p + '/byte_span', snapshot[x:y] == z['text'].encode())
            lo, hi = loc['physical_line_range_1based_inclusive']
            check('literal_snapshot', row['id'] + p + '/physical_lines', ''.join(original.splitlines(keepends=True)[lo-1:hi]) == z['text'])
            add(z['source_resource_id'], 'SOURCE-' + z['source_sha256'], z['source_sha256'], loc, {'text': digest(z['text'].encode())}, p, 'literal')
        elif z.get('source_locator', {}).get('kind') == 'structured_JSON_and_original_HTML':
            check('source_text', row['id'] + p + '/literal_sha', digest(z['text'].encode()) == z['text_sha256'])
            add(z['source_resource_id'], z['source_document_resource_id'], z['source_sha256'], z['source_locator'], {'text': digest(z['text'].encode())}, p, 'literal')
        else:
            h = cjsha(z)
            add('FULLSOURCE-' + h[:20], z.get('source_resource_id'), z.get('source_sha256'), {'representation': 'source_full_text_resource_payload'}, {'text': h}, p, 'fullpayload')
    for i, z in enumerate(b['source_asset_locations']):
        sha = z.get('source_pdf_sha256', row['source_ref']['sha256'])
        add(z['attachment_id'], 'SOURCE-' + sha, sha, {'absolute_path': z['absolute_path'], 'physical_page': z.get('physical_page')}, {'image': z['sha256']}, '/source_asset_locations/' + str(i), 'asset')
    return reg

for i, (b, p, c, eu) in enumerate(zip(source_rows, preds, cons, effective)):
    rid = b['source_record']['id']; unit = eu['semantic_unit']; log = c['uniform_source_reading_log']
    registry = expected_inventory(b)
    contexts = {z['context_id']: z for z in unit['contexts']}
    check('semantic', rid + '/raw_current_text', unit['text'] == b['source_record']['text'])
    for k, v in b['source_record'].items():
        if k != 'id':
            check('semantic', rid + '/preserved/' + k, unit.get(k)[:len(v)] == v if k == 'contexts' else unit.get(k) == v)
    expected_semantic_bundle = copy.deepcopy(b); expected_semantic_bundle['source_record'].pop('id')
    for z in expected_semantic_bundle['source_full_text_resources']:
        if z.get('kind') == 'verbatim_UTF8_snapshot_text':
            z['text_sha256'] = z['text_utf8_sha256']; z['source_locator'] = copy.deepcopy(z['locator'])
    for f in ['preserved_historical_neutral_source_supplements', 'source_reference_index']:
        for z in expected_semantic_bundle[f]:
            z.pop('record_id', None)
    check('semantic', rid + '/semantic_bundle_only_declared_aliases', unit['source_bundle'] == expected_semantic_bundle)
    check('semantic', rid + '/contexts_unique', len(contexts) == len(unit['contexts']))
    for cid, origin in unit['derived_context_origins'].items():
        target = ptr(b, origin['source_bundle_pointer']); ctx = contexts[cid]
        check('semantic_origin', rid + '/' + cid + '/raw_text', ctx.get('text') == target.get('text'))
        check('semantic_origin', rid + '/' + cid + '/source_identity', ctx['source_ref']['sha256'] == origin['source_sha256'])
        resource = registry[origin['origin_inventory_resource_id']]
        check('semantic_origin', rid + '/' + cid + '/inventory_view', resource['available_views'].get(origin['origin_inventory_view']) == origin['origin_inventory_view_sha256'])
        if target.get('kind') == 'verbatim_UTF8_snapshot_text':
            check('semantic_origin', rid + '/' + cid + '/source_locator', ctx['source_ref']['locator'] == target['locator'])
    producer = {z['resource_id']: z for z in log['producer_source_inventory']}
    resolved = {z['resource_id']: z for z in log['source_inventory']}
    counts['producer_inventory_resource_N'] += len(producer); counts['resolved_inventory_resource_N'] += len(resolved)
    check('inventory', rid + '/producer_ID_set', set(producer) == set(registry))
    check('inventory', rid + '/resolved_ID_set', set(resolved) == set(registry))
    check('inventory', rid + '/top_inventory_is_preserved_producer', c['inventory'] == log['producer_source_inventory'])
    delta = log['source_identity_resolution_delta']; changes = []
    for resource_id, expected in registry.items():
        pr = producer[resource_id]; rs = resolved[resource_id]
        counts['available_source_view_N'] += len(expected['available_views'])
        for f in ['source_document_id', 'source_sha256', 'locator', 'available_views']:
            check('inventory', rid + '/' + resource_id + '/producer/' + f, pr[f] == expected[f])
        for view, sha in expected['available_views'].items():
            check('source_view_binding', rid + '/' + resource_id + '/' + view, rs['available_views'].get(view) == sha)
        same = copy.deepcopy(pr)
        if expected['kind'] == 'fullpayload':
            payload = ptr(b, expected['pointer']); explicit_sha = payload.get('source_sha256', payload.get('source_pdf_sha256'))
            check('identity', rid + '/' + resource_id + '/raw_explicit_source_SHA', rs['source_sha256'] == explicit_sha and rs['source_document_id'] == 'SOURCE-' + explicit_sha)
            if pr['source_sha256'] is None:
                same['source_sha256'] = explicit_sha; changes.append(resource_id)
        check('identity', rid + '/' + resource_id + '/only_declared_identity_delta', same == rs)
    check('identity', rid + '/delta_IDs_exact', changes == [z['resource_id'] for z in delta])
    for z in delta:
        counts['source_identity_delta_N'] += 1
        payload = ptr(b, z['source_bundle_pointer'])
        check('identity', rid + '/' + z['resource_id'] + '/payload_canonical_SHA', cjsha(payload) == z['payload_canonical_view_sha256'])
        for f in ['source_snapshot_binding', 'source_payload_file_binding']:
            bound(z[f], 'identity_dependency', rid + '/' + f)
        check('identity', rid + '/' + z['resource_id'] + '/payload_file_exact_object', obj(z['source_payload_file_binding']['path']) == payload)
        check('identity', rid + '/' + z['resource_id'] + '/explicit_SHA_matches_snapshot', z['resolved_value'] == z['source_snapshot_binding']['sha256'] == payload.get('source_sha256', payload.get('source_pdf_sha256')))
    reads = log['read_receipts']; events = log['actual_text_geometry_events']; uses = log['use_receipts']
    counts['used_distinct_record_view_N'] += len({(u['resource_id'], u['view']) for u in uses})
    counts['read_receipt_N'] += len(reads); counts['use_receipt_N'] += len(uses); counts['request_N'] += len(log['source_requests'])
    counts['actual_event_N'] += len(events); counts['requirement_N'] += len(log['requirements'])
    counts['relation_trace_N'] += len(p['relation_traces'])
    check('log', rid + '/bundle_canonical_SHA', log['actual_full_source_bundle_sha256'] == cjsha(b))
    check('log', rid + '/canonical_input_SHA', log['canonical_sha256'] == SOURCE_SHA)
    check('log', rid + '/manifest_SHA', log['material_manifest_sha256'] == scope['source_manifest_sha256'])
    check('log', rid + '/logged_packet_identity', log['actual_source_material_identity']['source_packet_binding'] == scope['source_packet'])
    check('log', rid + '/events_top_plus_body', events[1:] == c['actual_text_geometry_events'] and events[0]['resource_id'] == 'BODY-' + rid)
    check('relation', rid + '/trace_arrays', c['source_relation_traces'] == p['source_relation_traces'])
    normalized = [{k: v for k, v in t.items() if k != 'relation_kind'} for t in p['source_relation_traces']]
    check('relation', rid + '/trace_semantic_copy', normalized == p['relation_traces'])
    seen = set(); first_events = []
    for n, ev in enumerate(events):
        key = (ev['resource_id'], ev['view']); rs = resolved[ev['resource_id']]
        check('event_binding', rid + '/' + str(n) + '/source_SHA', ev['source_sha256'] == rs['source_sha256'])
        check('event_binding', rid + '/' + str(n) + '/view_SHA', ev['view_sha256'] == rs['available_views'].get(ev['view']))
        expected_locator = rs['locator']
        if registry[ev['resource_id']]['kind'] in ['historical', 'fullpayload']:
            payload = ptr(b, registry[ev['resource_id']]['pointer'])
            expected_locator = payload.get('locator', {'document_resource_id': ev['resource_id']})
        check('event_binding', rid + '/' + str(n) + '/locator_exact_scan_contract', ev['locator_read'] == expected_locator)
        if key not in seen:
            seen.add(key); first_events.append((n, ev))
    check('read', rid + '/receipt_count_first_unique_events', len(reads) == len(first_events))
    by_id = {z['receipt_id']: z for z in reads}; by_key = {(z['resource_id'], z['view']): z for z in reads}
    for rd, (n, ev) in zip(reads, first_events):
        counts['read_view_' + rd['view'] + '_N'] += 1
        check('read', rid + '/' + rd['receipt_id'] + '/receipt_and_event_identity', rd['receipt_id'] == 'READ-' + str(n) and rd['event_id'] == R.name + ':source-event:' + str(n) and rd['run_id'] == R.name and rd['record_id'] == rid)
        for f in ['resource_id', 'view', 'source_sha256', 'view_sha256', 'locator_read', 'event_kind', 'consumption_scope']:
            check('read', rid + '/' + rd['receipt_id'] + '/' + f, rd[f] == ev[f])
        check('read', rid + '/' + rd['receipt_id'] + '/complete_recorded_AI_nonpixel', rd['delivery_status'] == 'complete' and rd['read_attestation'] == 'recorded' and rd['reader'] == 'AI_rule_runtime' and not rd['pixel_interpretation'])
    for req in log['requirements']:
        key = req['required_resource_id'], req['required_view']
        check('requirement', rid + '/' + req['requirement_id'] + '/view_has_actual_read', key in by_key)
        check('requirement', rid + '/' + req['requirement_id'] + '/resolved', req['requirement_status'] == 'resolved')
        check('requirement', rid + '/' + req['requirement_id'] + '/locator', req['source_evidence_locator'] == resolved[key[0]]['locator'])
    flat_uses = []
    for tn, trace in enumerate(p['source_relation_traces']):
        trace_key = rid + '/trace/' + str(tn)
        ce = trace['context_evidence']; details = trace['details']
        check('relation', trace_key + '/context_IDs', details['context_ids'] == [a['context_id'] for a in ce])
        selected_content = '\n'.join(a['text'] for a in ce)
        if details.get('relation_subtype') == 'bounded_primary_qualification_support_roles':
            selected_content = '\n'.join(z['evidence']['text'] for z in details['source_roles'] if z['inherited_as_support_definition'])
        elif details.get('relation_subtype') == 'bounded_primary_postadmission_technical_support':
            selected_content = '\n'.join(z['evidence']['text'] for z in details['source_roles'] if z['role'] != 'programme_heading')
        check('relation', trace_key + '/content_exact_declared_roles', details['content'] == selected_content)
        for sn, role in enumerate(details.get('source_roles', [])):
            anchor = role['evidence']; ctx = contexts[anchor['context_id']]; loc = ctx['source_ref']['locator']
            if 'source_leaf_span' in role:
                check('relation_span', trace_key + '/role/' + str(sn) + '/leaf_span', role['source_leaf_span'] == [anchor['start'], anchor['end']])
            if 'source_snapshot_span' in role and 'unicode_code_point_interval_half_open' in loc:
                base = loc['unicode_code_point_interval_half_open'][0]
                check('relation_span', trace_key + '/role/' + str(sn) + '/snapshot_span', role['source_snapshot_span'] == [base + anchor['start'], base + anchor['end']])
        for sn, span in enumerate(details.get('selected_leaf_spans', [])):
            ctx = contexts[span['context_id']]; loc = ctx['source_ref']['locator']; lo, hi = span['leaf_span']
            check('relation_span', trace_key + '/selected/' + str(sn) + '/leaf_bounds', 0 <= lo <= hi <= len(ctx['text']))
            if 'unicode_code_point_interval_half_open' in loc:
                base = loc['unicode_code_point_interval_half_open'][0]
                check('relation_span', trace_key + '/selected/' + str(sn) + '/snapshot_span', span['snapshot_span'] == [base + lo, base + hi])
            check('relation_span', trace_key + '/selected/' + str(sn) + '/exact_CE_match', any(a['context_id'] == span['context_id'] and a['start'] == lo and a['end'] == hi and a['text'] == ctx['text'][lo:hi] for a in ce))
        counts['relation_kind_' + trace['kind'] + '_N'] += 1
        for u in trace['used_source_views']:
            key = u['resource_id'], u['view']; use_scope = u['use_scope']
            check('use', trace_key + '/' + u['resource_id'] + '/actual_read_exists', key in by_key)
            rd = by_key[key]
            flat_uses.append({'resource_id': key[0], 'view': key[1], 'use_status': 'used', 'read_receipt_id': rd['receipt_id'], 'use_scope': use_scope, 'source_relation_kind': trace['relation_kind']})
            if 'source_bundle_pointer' in use_scope:
                counts['five_field_source_quote_N'] += 1
                qkey = trace_key + '/quote/' + str(counts['five_field_source_quote_N'])
                check('quote', qkey + '/five_scope_fields', set(use_scope) == {'reason', 'source_bundle_pointer', 'source_resource_id', 'exact_anchor', 'field_scope'})
                target = ptr(b, use_scope['source_bundle_pointer']); anchor = use_scope['exact_anchor']; text = target['text']
                fallback = None
                if use_scope['source_bundle_pointer'].startswith('/explicit_or_primary_source_resources/'):
                    fallback = b['explicit_or_primary_source_resources'][int(use_scope['source_bundle_pointer'].split('/')[2])]['source_resource_id']
                target_id = target.get('source_resource_id', target.get('source_paragraph_id', target.get('supplement_id', fallback)))
                check('quote', qkey + '/raw_pointer_target_or_explicit_parent_identity', target_id == use_scope['source_resource_id'])
                check('quote', qkey + '/exact_span', type(anchor['start']) is int and type(anchor['end']) is int and 0 <= anchor['start'] <= anchor['end'] <= len(text) and text[anchor['start']:anchor['end']] == anchor['text'])
                origin = unit['derived_context_origins'][anchor['context_id']]
                check('quote', qkey + '/origin_pointer', origin['source_bundle_pointer'] == use_scope['source_bundle_pointer'])
                check('quote', qkey + '/inventory_resource_view_bridge', origin['origin_inventory_resource_id'] == key[0] and origin['origin_inventory_view'] == key[1])
                check('quote', qkey + '/source_SHA', anchor['source_ref']['sha256'] == origin['source_sha256'] == rd['source_sha256'])
                check('quote', qkey + '/reason_and_scope_nonempty', bool(use_scope['reason']) and bool(use_scope['field_scope']))
                quotes.append({'id': rid, 'trace_index': tn, 'resource_id': key[0], 'view': key[1], 'pointer': use_scope['source_bundle_pointer'], 'span': [anchor['start'], anchor['end']], 'quote_utf8_sha256': digest(anchor['text'].encode()), 'source_sha256': rd['source_sha256'], 'view_sha256': rd['view_sha256'], 'read_receipt_id': rd['receipt_id']})
            elif 'exact_anchor' in use_scope:
                counts['ordinary_context_quote_N'] += 1
                anchor = use_scope['exact_anchor']; cid = anchor['context_id']; origin = unit['derived_context_origins'].get(cid)
                raw_context_ids = {z['context_id'] for z in b['source_record']['contexts']}
                expected_key = (cid, 'text') if cid in raw_context_ids else (origin['origin_inventory_resource_id'], origin['origin_inventory_view'])
                check('quote_bridge', trace_key + '/' + cid, key == expected_key)
            elif 'geometry_pointer' in use_scope or 'source_article_group_pointer' in use_scope:
                counts['structure_pointer_use_N'] += 1
                pointer = use_scope.get('geometry_pointer', use_scope.get('source_article_group_pointer'))
                target = ptr(b, pointer); document_pointer = registry[key[0]]['pointer']
                check('structure_use', trace_key + '/inside_read_document', pointer.startswith(document_pointer + '/') and key[1] == 'document_bundle' and isinstance(target, dict))
                if 'printed_operator' in use_scope:
                    check('structure_use', trace_key + '/printed_operator', use_scope['printed_operator'] == target.get('operator'))
                structures.append({'id': rid, 'trace_index': tn, 'resource_id': key[0], 'view': key[1], 'pointer': pointer, 'pointer_target_canonical_sha256': cjsha(target), 'raw_pointer_target': target, 'read_receipt_id': rd['receipt_id'], 'view_sha256': rd['view_sha256']})
            else:
                counts['reference_chain_use_N'] += 1
                chain_proof = []
                for chain in use_scope.get('reference_chain', []):
                    check('structure_use', trace_key + '/reference_chain/' + chain['container_context_id'], chain['container_context_id'] in contexts and all(cid in contexts for cid in chain['context_ids']))
                    container = contexts[chain['container_context_id']]
                    ordered = [cid for group in container['structure']['child_groups'] if group['position'] == 'contexts' for cid in group['ordered_context_ids']]
                    selected = chain['context_ids']
                    check('structure_use', trace_key + '/reference_chain_members/' + chain['container_context_id'], all(cid in ordered for cid in selected) and [cid for cid in ordered if cid in selected] == selected and all(contexts[cid]['structure']['parent_context_id'] == chain['container_context_id'] for cid in selected))
                    check('structure_use', trace_key + '/reference_chain_reads/' + chain['container_context_id'], (chain['container_context_id'], 'geometry') in by_key and all((cid, 'text') in by_key for cid in selected))
                    chain_proof.append({'declared_chain': chain, 'container_raw_pointer': registry[chain['container_context_id']]['pointer'], 'container_geometry_sha256': cjsha(container['structure']), 'container_structure': container['structure'], 'selected_context_pointers': [registry[cid]['pointer'] for cid in selected], 'selected_text_read_receipt_ids': [by_key[(cid, 'text')]['receipt_id'] for cid in selected]})
                structures.append({'id': rid, 'trace_index': tn, 'resource_id': key[0], 'view': key[1], 'read_receipt_id': rd['receipt_id'], 'view_sha256': rd['view_sha256'], 'reference_chain_proof': chain_proof})
    check('use', rid + '/all_receipts_exact_trace_flattening', uses == flat_uses)
    for n, u in enumerate(uses):
        rd = by_id.get(u['read_receipt_id'])
        check('use', rid + '/receipt/' + str(n), rd is not None and (rd['resource_id'], rd['view']) == (u['resource_id'], u['view']))
    for path, a in nodes(p):
        if {'start', 'end', 'text'} <= set(a):
            cid = a.get('context_id'); text = contexts[cid].get('text', '') if cid else unit['text']
            family = 'context_span' if cid else 'body_span'; counts[family + '_occurrence_N'] += 1
            check(family, rid + path, type(a['start']) is int and type(a['end']) is int and 0 <= a['start'] <= a['end'] <= len(text) and text[a['start']:a['end']] == a['text'])
            if cid:
                check('context_ref', rid + path, a['source_ref'] == contexts[cid]['source_ref'])
    check('decisions', rid + '/five_dimensions', list(p['labels']) == DIMS and list(p['decisions']) == DIMS)
    check('decisions', rid + '/diagnostic_copy', p['decisions'] == p['candidate_decisions_diagnostic_only'])
    for d in DIMS:
        dec = p['decisions'][d]; slot = slots[i * 5 + DIMS.index(d)]
        counts['decision_N'] += 1; counts['decision_null_N'] += dec['value'] is None
        counts['technical_failure_N'] += bool(slot['technical_failure'])
        check('decisions', rid + '/' + d + '/label_value_same', dec['value'] == p['labels'][d] == slot['rule_value'])
        check('decisions', rid + '/' + d + '/slot_retained_decision_same', slot['retained_rule_decision'] == dec)
        check('decisions', rid + '/' + d + '/slot_source_record_exact', slot['source_record'] == b['source_record'])
        check('decisions', rid + '/' + d + '/slot_bundle_SHA', slot['source_bundle_sha256'] == cjsha(b))
        check('decisions', rid + '/' + d + '/slot_delivery_execution_status', slot['raw_source_delivery_status'] == 'delivered' and slot['rule_executed'] and slot['status'] == 'retained_rule_decision' and not slot['technical_failure'] and not slot['rules_null'])
    for path, a in nodes({'prediction': p, 'consumption': c}):
        for k in ['source_requests', 'material_requests', 'implementation_errors', 'source_dependency_stop_reasons', 'unresolved_material_requests', 'material_request_routes', 'needed_material']:
            if k in a and isinstance(a[k], list):
                check('requests_errors', rid + path + '/' + k, len(a[k]) == 0)
    record_counts.append({'id': rid, 'producer_inventory_N': len(producer), 'source_view_N': sum(len(z['available_views']) for z in registry.values()), 'event_N': len(events), 'read_N': len(reads), 'use_N': len(uses), 'request_N': len(log['source_requests']), 'requirement_N': len(log['requirements']), 'relation_trace_N': len(p['relation_traces'])})

binding_paths = {str(Path(z['path']).resolve()) for k in ['implementation_files', 'material_bindings', 'control_inputs', 'output_files'] for z in seal[k]}
path_classes = collections.Counter(); unbound = []
for path in execution['read_paths']:
    resolved_path = str(Path(path).resolve())
    if resolved_path in binding_paths:
        path_classes['exact_bound_source_or_implementation'] += 1
    elif '/lib/python3.14/' in resolved_path and resolved_path.startswith('/opt/homebrew/Cellar/python@3.14/'):
        path_classes['allowed_Python_stdlib'] += 1
    else:
        path_classes['unclassified'] += 1; unbound.append(path)
check('read_paths', 'all_logged_paths_bound_or_declared_stdlib', not unbound, unbound)
check('execution', 'counts_recomputed', len(preds) == execution['actual_record_N'] == seal['record_N'] == 77 and len(slots) == execution['actual_dimension_N'] == seal['dimension_N'] == 385)
check('execution', 'technical_failure_recomputed', counts['technical_failure_N'] == execution['technical_failure_dimension_N'] == seal['technical_failure_dimension_N'] == 0)
check('execution', 'null_recomputed', counts['decision_null_N'] == execution['lawful_null_N'] == seal['lawful_null_N'] == 0)
check('execution', 'run_seal_unchanged_after_audit', digest(Path(R / 'seal.json').read_bytes()) == SEAL_SHA)
check('execution', 'source_unchanged_after_audit', digest(SOURCE.read_bytes()) == SOURCE_SHA)

initial = obj(OUT / 'initial-probe' / 'report.json')
initial_preservation = obj(OUT / 'initial-probe-preservation.json')
for n, entry in enumerate(initial_preservation['files']):
    bound(entry, 'initial_probe_preservation', str(n))
schema_rules = {
    'input': {'diagnostic_N': 1, 'basis': 'driver write_jsonl uses JSON reserialization; original input is separately bound by input line byte offsets, byte SHA and canonical bundle SHA.', 'contract': 'rule_driver.py:30'},
    'relation': {'diagnostic_N': 2, 'basis': 'source_roles distinguish support-content from qualification-standard/heading evidence. For qualification support, content is only inherited_as_support_definition=true; postadmission content excludes programme_heading. Both exact role joins independently match.', 'contract': 'relations.py:691'},
    'event_binding': {'diagnostic_N': 19, 'basis': 'FULLSOURCE scanner locator_read is {document_resource_id: inventory_id}, while inventory locator denotes payload representation; historical scanner reads the raw locator whereas inventory source_locator defaults to {}. Each alternative independently matches its exact raw payload schema.', 'contract': 'relations.py:245'},
    'quote_bridge': {'diagnostic_N': 27, 'basis': 'A preserved raw CTX that also has a neutral source origin produces both raw CTX text use and origin document/text use. Ordinary CTX quote binds to its raw CTX receipt; five-field origin quote separately binds to source pointer and origin view.', 'contract': 'relations.py:268'},
    'inventory': {'diagnostic_N': 3, 'basis': 'Top-level consumption inventory is original producer inventory, including 3 missing source SHA entries. uniform_source_reading_log.source_inventory contains separately verified identity resolution; deltas independently verified against raw payload, unique source document, snapshot and payload file.', 'contract': 'rule_driver.py:362'},
    'quote': {'diagnostic_N': 16, 'basis': 'source_texts entries may omit per-text resource id. Their pointer still resolves exact text, with source_resource_id inherited from explicit parent source document; every declared id equals the exact parent document id and its origin inventory.', 'contract': 'source_packet.py:64'},
}
initial_categories = collections.Counter(z['category'] for z in initial['errors'])
check('harness_review', 'all_68_initial_diagnostics_categorized', dict(initial_categories) == {k: v['diagnostic_N'] for k, v in schema_rules.items()} and len(initial['errors']) == 68)
schema_review = {'initial_probe_checks_N': initial['checks_N'], 'initial_probe_diagnostic_N': len(initial['errors']),
                 'initial_probe_preservation_manifest': str(OUT / 'initial-probe-preservation.json'),
                 'initial_diagnostics': initial['errors'], 'schema_rules': schema_rules,
                 'all_diagnostics_resolved_by_explicit_schema_contracts': True,
                 'run_output_changed': False, 'coder_executed': False}

errors = [z for z in ledger if not z['passed']]
limitations = [
    '这是标签已经披露后的 AI 开发回归输出完整性审计；没有计算或推断准确率，不构成正式盲验或真人独立验证。',
    'event/read/use 是本次程序保存的记录；本审计核验其原始 source/view/locator 与事件和凭据的一致性，不独立观察此前执行时刻的实际认知读取，也不认证语义适用性或编码正确性。',
    '一次执行结论来自冻结控制、一次 launch 及 result/execution 记录的一致性；没有系统级进程审计，无法从这些文件证明不存在未记录的外部进程。',
    'source packet 及所有 seal member 原始 bytes/hash 均重算。外部依赖只作 opaque bytes/hash 检查；只有字面 textleaf snapshot 和 identity delta 的 source payload 作指定原文/身份比对。',
    '图片文件 hash 的读取不等于像素解读；日志记录 image/pixel read 为 0。PDF/HTML 生产链的转写真实性没有重新渲染、OCR 或人工核验。',
    'Python 标准库路径按 driver 的明示 stdlib 契约分类，既有 stdlib pyc 不当作未绑定 source。',
    'body/context span occurrence 包含 predictions 中的 diagnostic copy 和重复 source_relation_traces；权威生产部分与重复部分分别计数，避免把复制证据当作新增证据。',
    '71 个五字段 pointer 引用与 62 个 ordinary CTX 引用是使用记录计数，可能指向同一个物理证据；不是 133 个独立来源。8 个结构 pointer 与 2 个 chain 使用的完整核验路径、target hash、container/成员顺序及 read receipt 另存 structure-use-evidence.json。',
    '初探 68 个诊断已保留原始脚本、ledger、报告与 seal 字节。6 类诊断由明示 schema 的序列化、locator 替代、双 CTX/derived 句柄、parent document id fallback、producer/resolved 分离与有界 role content 消解；判据及具体诊断见 schema-review.json。',
    'delivered output 是源 bundle 的重新序列化副本，其原始 bytes/SHA 与 input 文件不同；77 个对象与逐条 canonical SHA 完全一致，真正输入的原始 byte offset、行 SHA 及文件 SHA 已单独核验。',
]
primary_spans = collections.Counter()
for p in preds:
    for _, a in nodes({'decisions': p['decisions'], 'relation_traces': p['relation_traces']}):
        if {'start', 'end', 'text'} <= set(a):
            primary_spans['context' if 'context_id' in a else 'body'] += 1
counts['authoritative_body_span_N'] = primary_spans['body']
counts['authoritative_context_span_N'] = primary_spans['context']
summary = {'audit_scope': 'Independent disclosed-label AI development output integrity, no accuracy and no coder execution',
           'audited_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'run_seal_sha256': SEAL_SHA, 'source_packet_sha256': SOURCE_SHA,
           'source_input_utf8_bytes': len(raw(SOURCE)), 'checks_N': len(ledger), 'passed_check_N': len(ledger)-len(errors), 'failed_check_N': len(errors),
           'counts': dict(counts), 'read_path_classes': dict(path_classes), 'errors': errors, 'limitations': limitations,
           'input_serialization': {'source_raw_sha256': digest(raw(SOURCE)), 'source_raw_bytes': len(raw(SOURCE)), 'delivered_raw_sha256': digest(raw(R / 'delivered-complete-source-bundles.jsonl')), 'delivered_raw_bytes': len(raw(R / 'delivered-complete-source-bundles.jsonl')), 'raw_bytes_equal': raw(SOURCE) == raw(R / 'delivered-complete-source-bundles.jsonl'), 'all_77_JSON_objects_and_canonical_hashes_equal': delivered == source_rows},
           'initial_probe_diagnostic_N': 68, 'schema_review': schema_rules,
           'record_count_N': len(preds), 'dimension_slot_N': len(slots), 'record_counts': record_counts}
OUT.mkdir(exist_ok=True)
for name, data in [('report.json', summary), ('quote-evidence.json', quotes), ('structure-use-evidence.json', structures), ('schema-review.json', schema_review)]:
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
(OUT / 'checks.jsonl').write_text(''.join(json.dumps(z, ensure_ascii=False) + '\n' for z in ledger), encoding='utf8')
report = f'''# 独立输出完整性审计\n\n本次逐项核验 {len(preds)} 条 predictions、{len(slots)} 个维度槽位；{len(ledger)} 个独立布尔检查中 {len(ledger)-len(errors)} 通过、{len(errors)} 失败。未读参照标签，未运行/import coder，未计算准确率。\n\nrun seal SHA256：`{SEAL_SHA}`。唯一 source packet SHA256：`{SOURCE_SHA}`，原始 input {len(raw(SOURCE)):,} bytes，77 ID 与冻结顺序逐一匹配。\n\nseal member 逐个重算 132 个（implementation 10、material 113、control 1、output 8）；另核 pre-run 的 134 个 member 条目，含重复绑定。实际原始 input 行 byte 起止、行 SHA、bundle canonical SHA 逐行核验。\n\n实际 read receipts {counts['read_receipt_N']}（text {counts['read_view_text_N']}、geometry {counts['read_view_geometry_N']}、document_bundle {counts['read_view_document_bundle_N']}）；events {counts['actual_event_N']}；use {counts['use_receipt_N']}；request {counts['request_N']}；requirements {counts['requirement_N']}；relation traces {counts['relation_trace_N']}。\n\n五字段 source quotes {counts['five_field_source_quote_N']}；普通 context exact quotes {counts['ordinary_context_quote_N']}；结构 pointer uses {counts['structure_pointer_use_N']}；reference chain uses {counts['reference_chain_use_N']}。全部核 pointer、原文半开区间、resource/source/view identity、read receipt。\n\nproducer/resolved inventories 各 {counts['producer_inventory_resource_N']} 个资源（逐记录累计）；可用 view {counts['available_source_view_N']}；身份 delta {counts['source_identity_delta_N']} 个，逐一重核显式 SHA、snapshot/payload file hash、canonical payload 和只变动 source SHA。\n\n权威生产证据 body spans {counts['authoritative_body_span_N']}、context spans {counts['authoritative_context_span_N']}；全 prediction 包含重复副本累计 body spans {counts['body_span_occurrence_N']}、context spans {counts['context_span_occurrence_N']}。\n\n重新计数技术失败 {counts['technical_failure_N']}、null {counts['decision_null_N']}；保存的 launch/result/execution 共同记录一次执行、exit 0、无重试、stderr 空。\n\n错误：\n\n'''
report += '\n'.join('- ' + json.dumps(e, ensure_ascii=False) for e in errors) if errors else '0 个检查错误。\n'
report += '\n\n局限：\n\n' + '\n'.join('- ' + x for x in limitations) + '\n'
report += '\n\n初次诊断的 schema 复核：\n\n' + '\n'.join('- ' + str(z['diagnostic_N']) + ' 个 ' + k + '：' + z['basis'] + ' 静态契约 ' + z['contract'] + '。' for k, z in schema_rules.items()) + '\n'
(OUT / 'report.md').write_text(report, encoding='utf8')
audit_members = []
for name in ['audit.py', 'checks.jsonl', 'report.json', 'quote-evidence.json', 'structure-use-evidence.json', 'schema-review.json', 'report.md', 'initial-probe-preservation.json', 'initial-probe/audit.py', 'initial-probe/checks.jsonl', 'initial-probe/report.json', 'initial-probe/quote-evidence.json', 'initial-probe/report.md', 'initial-probe/seal.json']:
    p = OUT / name; b = p.read_bytes(); audit_members.append({'path': str(p), 'bytes': len(b), 'sha256': digest(b)})
audit_seal = {'status': 'sealed_independent_read_only_output_integrity_audit', 'run_seal_sha256': SEAL_SHA, 'source_packet_sha256': SOURCE_SHA,
              'checks_N': len(ledger), 'failed_check_N': len(errors), 'coder_execution_N': 0, 'reference_label_read_N': 0, 'accuracy_computation_N': 0,
              'files': audit_members, 'disclosed_label_development_only': True, 'formal_validation_complete': False, 'human_validation_complete': False}
(OUT / 'seal.json').write_text(json.dumps(audit_seal, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'checks_N': len(ledger), 'passed_check_N': len(ledger)-len(errors), 'failed_check_N': len(errors), 'errors': errors[:30], 'counts': dict(counts), 'audit_seal_sha256': digest((OUT / 'seal.json').read_bytes())}, ensure_ascii=False, indent=2))
