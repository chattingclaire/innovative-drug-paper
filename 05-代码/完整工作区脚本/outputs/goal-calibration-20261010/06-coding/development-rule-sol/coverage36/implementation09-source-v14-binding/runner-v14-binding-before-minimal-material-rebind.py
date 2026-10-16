"""Finite v14 source-only binding update for exactly ten changed records.

Keep v09 inference semantics and manual1.3. Freeze before coder import;
retain the sole first output and every technical slot. No reference is read.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import types

VERSION = 'development-rule-sol-implementation09-source-v14-binding'
DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')
INFERENCE_FILES = ('runner.py', 'source_packet.py', 'source_receipts.py', 'evidence.py', 'relations.py', 'dimensions.py')
CODER_MODULES = ('source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions')
FINITE_DECLARATION_SHA = '25064fe5175cbfe9bc258689a12ab86e1244840f295ea4194a7ff2a459430af3'
V12_SEAL_SHA = '68b62081c523f3e22ae5830887b073f50ef79a02c0143a4608630355a4b7f426'
V12_CANON_SHA = 'c417474ecbd801f1ea0f784f96dad23bf88b7ac00b12780e3ce67c3cbb8f2764'
MANUAL_SHA = 'a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f'
V09_DIM_SHA = '0467b4b4c9c7615830e018dbe75061981fafe2d981b3a58d49ae2e4b8a3f50eb'
V13_SEAL_SHA = 'c34f1365ed771c7e36ef1d941591e3b715844e34cdc9eb8fd20e05880a3b6620'
V13_INTERFACE_SHA = '4f0c291a1a275ad4b47f7ce0a4a8d897832953b924792ac02a8f9b0fefe815bf'
V09_RELATIONS_SHA = '6325208ea748e250f615eed8d860371d3414963b2cf1f3e61e1f94948200f11a'
V09_RECEIPTS_SHA = 'e9ac5bf9a810f1a482f06d76a8706e6bd81427d7f19c45741ee680dce2b20209'
V14_SEAL_SHA = '628bbec47f94546cf228ebd1f8fefbd8b8f1673164c0fef127f65abfe3f5f4aa'
V14_77_SEAL_SHA = 'cb7607d35a1ffa17c5dfdfda6e734144e45716021470b4279fcf180f68cf7458'
V14_INTERFACE_SHA = 'd3662ffda2de485fccfc07864fb60c97f1c301c9fadabacbb49f0ed3e38c5715'
V14_EXTENSION_SHA = '563cfcaf87c41e33de6b958b78a1d11d98f89dac8a373087d7121b8a6352608d'
AUTHORIZED_IDS = ['RECODE25-' + x for x in ('00005','00036','00038','00045','00086','00099','00110','00118','00131','00138')]
V05_EVIDENCE_SHA = '5ce0fc8c39862edbcab837c0b1fdc7f5c605758f34fbf0ab34487a0b4531cdb3'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def write_jsonl(path, rows):
    with Path(path).open('x', encoding='utf-8') as stream:
        for value in rows:
            stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')


def binding(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': digest(p), 'bytes': p.stat().st_size}


def load_frozen_coders(implementation, code):
    expected = {Path(b['path']).stem: b for b in code}
    if any(name in sys.modules for name in CODER_MODULES):
        raise ValueError('coder imported before freeze')
    modules = {}
    for name in CODER_MODULES:
        p = implementation / (name + '.py')
        b = p.read_bytes()
        if hashlib.sha256(b).hexdigest() != expected[name]['sha256']:
            raise ValueError('coder changed after freeze: ' + name)
        module = types.ModuleType(name)
        module.__file__, module.__package__ = str(p), ''
        sys.modules[name] = module
        exec(compile(b, str(p), 'exec'), module.__dict__)
        modules[name] = module
    return modules


def dimension_slots(bundles, predictions, global_errors, diagnostic_only=False):
    source = {b['source_record']['id']: b for b in bundles}
    slots = []
    for p in predictions:
        decisions = p.get('decisions') or p.get('candidate_decisions_diagnostic_only')
        for d in DIMENSIONS:
            decision = decisions.get(d) if isinstance(decisions, dict) else None
            failed = bool(global_errors or p['implementation_errors'] or decision is None)
            slots.append({'id': p['id'], 'dimension': d,
                'source_record': source[p['id']]['source_record'] if p['id'] in source else None,
                'raw_source_delivery_status': ('diagnostic_verified_snapshot_only' if diagnostic_only else 'delivered') if p['id'] in source else 'not_delivered_due_to_loader_failure',
                'rule_executed': bool(p.get('decisions') or p.get('candidate_decisions_diagnostic_only')),
                'source_bundle_sha256': hashlib.sha256(cj(source[p['id']]).encode()).hexdigest() if p['id'] in source else None,
                'status': 'technical_failure' if failed else ('source_dependency_unresolved' if decision['value'] is None else 'retained_rule_decision'),
                'technical_failure': failed, 'rules_null': not failed and decision['value'] is None,
                'rule_value': None if failed else decision['value'], 'retained_rule_decision': decision,
                'record_implementation_errors': p['implementation_errors'], 'global_implementation_errors': global_errors,
                'comparison_eligible': not failed, 'new2_new4_reference_comparison_authorized': False})
    return slots


def finite_protocol(source, bundles, materials, scope):
    """Execute the frozen producer's protocol with finite equivalent lookup.

    The original mechanical prepare/check bytes are retained. A frozen finite
    v14 facade supplies exact verified complete bundles and pure inventories.
    Material identities are the new finite ten-bundle hash plus v14 manifest; the
    old v12 identities remain explicit provenance. No full-frame lookup is run.
    """
    paths = {Path(i['path']).name: i for i in materials}
    item = paths['source_reading_protocol_v12.py']
    payload = Path(item['path']).read_bytes()
    if hashlib.sha256(payload).hexdigest() != item['sha256']:
        raise ValueError('source-reading protocol code changed after freeze')
    by_id = {b['source_record']['id']: b for b in bundles}
    facade = types.ModuleType('source_only_interface_v12')
    def lookup(rid, selector='rule', bundle=True):
        if selector != 'rule' or not bundle or rid not in by_id:
            raise ValueError('protocol lookup outside finite default complete rule scope')
        return copy.deepcopy(by_id[rid])
    facade.lookup = lookup
    from source_receipts import resolve_inventory
    source_base = next(Path(i['path']).parent for i in materials if Path(i['path']).name == 'canonical_source_context-v12.jsonl')
    def receipt_inventory(bundle):
        original = source.source_inventory(bundle)
        resolved, delta = resolve_inventory(bundle, original, materials, source_base)
        return resolved
    facade.source_inventory = receipt_inventory
    facade.cj = cj
    facade.CANON_SHA = scope['complete_bundles_canonical_sha256']
    facade.MANIFEST_SHA = scope['v14_extension_manifest_sha256']
    sys.modules['source_only_interface_v12'] = facade
    protocol = types.ModuleType('finite_source_reading_protocol_v12')
    protocol.__file__ = item['path']
    exec(compile(payload, item['path'], 'exec'), protocol.__dict__)
    protocol.bound_source_identity = {'consumer_interface_version': 'v14-finite-primary-source-literal-textleaf',
        'base_v12_canonical_sha256': V12_CANON_SHA,
        'base_v12_manifest_sha256': '0fa14322edbd614496b014be77144701d052ebde6d41383b788b9e6712b63797',
        'v13_extension_manifest_sha256': scope['v13_extension_manifest_sha256'],
        'v13_delivery_seal_sha256': V13_SEAL_SHA,
        'v14_extension_manifest_sha256': scope['v14_extension_manifest_sha256'],
        'v14_delivery_seal_sha256': V14_SEAL_SHA,
        'v14_development77_source_seal_sha256': V14_77_SEAL_SHA,
        'authorized_finite_record_N': 10,
        'finite_complete_bundles_canonical_sha256': scope['complete_bundles_canonical_sha256'],
        'frozen_input_binding_is_new_material_not_pure_path_adapter': True,
        'original_protocol_code_unchanged_finite_facade_rebound_for_v14': True}
    protocol.producer_source_inventory = source.source_inventory
    protocol.source_identity_resolver = lambda b: resolve_inventory(b, source.source_inventory(b), materials, source_base)
    return protocol


def actual_reading_log(protocol, bundle, view, run_id):
    """Record executed matching/geometry events separately from available assets."""
    rid = bundle['source_record']['id']
    log = protocol.prepare(rid, run_id, 'rule')
    log['actual_source_material_identity'] = copy.deepcopy(protocol.bound_source_identity)
    log['actual_full_source_bundle_sha256'] = hashlib.sha256(cj(bundle).encode()).hexdigest()
    log['source_bundle_extension'] = copy.deepcopy(bundle.get('source_bundle_extension'))
    log['v13_available_paragraphs_not_automatically_read_or_used'] = True
    log['v14_available_textleaf_resources_not_automatically_read_or_used'] = True
    log['producer_source_inventory'] = protocol.producer_source_inventory(bundle)
    resolved, delta = protocol.source_identity_resolver(bundle)
    if cj(resolved) != cj(log['source_inventory']):
        raise ValueError('consumer receipt identity resolution not stable')
    log['source_identity_resolution_delta'] = delta
    log['producer_inventory_original_fields_preserved'] = True
    log['receipt_identity_bridge_is_not_source_content_or_dimension_change'] = True
    inventory = {i['resource_id']: i for i in log['source_inventory']}
    body = inventory['BODY-' + rid]
    if view.text != bundle['source_record']['text']:
        raise ValueError('actual current matching text differs from delivered body')
    events = [{'resource_id': body['resource_id'], 'view': 'text',
        'source_sha256': body['source_sha256'], 'view_sha256': body['available_views']['text'],
        'locator_read': body['locator'], 'event_kind': 'current_text_matching_view',
        'consumption_scope': 'complete fixed current proposition, normalized matching and original offsets'}]
    events += copy.deepcopy(view.source_view_events)
    reads, seen = [], set()
    for index, event in enumerate(events):
        key = event['resource_id'], event['view']
        if key in seen:
            continue
        seen.add(key)
        resource = inventory.get(event['resource_id'])
        if not resource or event['source_sha256'] != resource['source_sha256'] or event['view_sha256'] != resource['available_views'].get(event['view']):
            raise ValueError('actual consumption event source/view binding does not match inventory')
        if event['view'] not in ('text', 'geometry', 'document_bundle'):
            raise ValueError('text rule cannot claim a pixel read')
        reads.append({'receipt_id': 'READ-' + str(index), 'run_id': run_id, 'record_id': rid,
            'resource_id': event['resource_id'], 'source_sha256': event['source_sha256'],
            'view': event['view'], 'view_sha256': event['view_sha256'],
            'locator_read': event['locator_read'], 'delivery_status': event.get('delivery_status', 'complete'),
            'read_attestation': 'recorded', 'reader': 'AI_rule_runtime',
            'event_id': run_id + ':source-event:' + str(index),
            'event_kind': event['event_kind'], 'consumption_scope': event['consumption_scope'],
            'content_modalities': ['text', 'structure', 'source_identity'] if event['view'] == 'document_bundle' else [event['view']],
            'pixel_interpretation': False})
    log['read_receipts'] = reads
    by_key = {(r['resource_id'], r['view']): r for r in reads}
    uses = []
    for trace in view.source_relation_traces:
        for use in trace.get('used_source_views', []):
            key = use['resource_id'], use['view']
            if key not in by_key:
                raise ValueError('source relation used a view without a recorded consumption event')
            uses.append({'resource_id': key[0], 'view': key[1], 'use_status': 'used',
                'read_receipt_id': by_key[key]['receipt_id'], 'use_scope': use['use_scope'],
                'source_relation_kind': trace.get('relation_kind')})
    log['use_receipts'] = uses
    log['source_requests'] = copy.deepcopy(view.source_requests)
    review = view.source_scope_review
    log['necessary_source_scope_review_status'] = review['status']
    log['necessary_source_scope_review_note'] = review['source_evidence_note']
    log['reference_resolution'] += copy.deepcopy(getattr(view, 'source_reference_resolution', []))
    log['actual_text_geometry_events'] = events
    log['image_read_N'] = 0
    log['image_file_integrity_read_is_not_pixel_interpretation'] = True
    return log, protocol.check(log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope-manifest', required=True)
    parser.add_argument('--scope-manifest-sha256', required=True)
    parser.add_argument('--finite-declaration', required=True)
    parser.add_argument('--scope', choices=['changed10'], required=True)
    parser.add_argument('--approved-output-root', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    implementation = Path(__file__).resolve().parent
    root, out = Path(args.approved_output_root).resolve(), Path(args.out).resolve()
    if root != implementation or root not in out.parents or out.exists():
        raise ValueError('run output must be a new child of this authorized implementation')
    scope_path, declaration_path = Path(args.scope_manifest).resolve(), Path(args.finite_declaration).resolve()
    if scope_path.parent != implementation or declaration_path.parent != implementation:
        raise ValueError('scope declarations must be this version files')
    if digest(scope_path) != args.scope_manifest_sha256:
        raise ValueError('source scope manifest differs from pre-run binding')
    if digest(declaration_path) != FINITE_DECLARATION_SHA:
        raise ValueError('finite ID declaration differs from exact predeclared changed10 binding')
    manifest = json.loads(scope_path.read_text())
    declaration = json.loads(declaration_path.read_text())
    groups = declaration['scopes']
    selected_ids = groups[args.scope]
    approved = declaration['approved_record_ids']
    if approved != AUTHORIZED_IDS or groups != {'changed10': AUTHORIZED_IDS} or selected_ids != approved:
        raise ValueError('only the exact ten changed source records are authorized')
    if manifest['approved_record_ids'] != approved or manifest.get('scopes', groups) != groups:
        raise ValueError('source manifest finite ID order or groups differ')
    if (digest(implementation / 'evidence.py') != V05_EVIDENCE_SHA or digest(implementation / 'dimensions.py') != V09_DIM_SHA
            or digest(implementation / 'relations.py') != V09_RELATIONS_SHA or digest(implementation / 'source_receipts.py') != V09_RECEIPTS_SHA):
        raise ValueError('v09 inference semantics or receipt identity bridge changed')
    materials = [dict(item) for item in manifest['bindings']]
    if len({item['path'] for item in materials}) != len(materials):
        raise ValueError('duplicate material dependency binding')
    for item in materials:
        if digest(item['path']) != item['sha256'] or Path(item['path']).stat().st_size != item['bytes']:
            raise ValueError('material changed before freeze: ' + item['path'])
    hashes = {Path(item['path']).name: item['sha256'] for item in materials}
    if hashes.get('delivery-seal-v12.json') != V12_SEAL_SHA or hashes.get('canonical_source_context-v12.jsonl') != V12_CANON_SHA:
        raise ValueError('formal v12 delivery/canonical binding absent')
    if not any(Path(i['path']).name == 'delivery-seal.json' and i['sha256'] == V13_SEAL_SHA for i in materials) or hashes.get('source_only_interface_v13.py') != V13_INTERFACE_SHA:
        raise ValueError('formal v13 extension seal/interface provenance absent')
    required_v14 = [('seal.json', V14_SEAL_SHA), ('delivery-seal.json', V14_77_SEAL_SHA), ('source_only_interface_v14.py', V14_INTERFACE_SHA), ('source-text-extension-manifest.json', V14_EXTENSION_SHA)]
    if any(not any(Path(i['path']).name == name and i['sha256'] == sha for i in materials) for name, sha in required_v14):
        raise ValueError('formal v14 source seal/interface/extension bindings absent')
    if hashes.get('common-manual-v1.3-development.md') != MANUAL_SHA:
        raise ValueError('ROOT clarified manual v1.3 exact binding absent')
    code = [binding(implementation / name) for name in INFERENCE_FILES]
    control_inputs = [binding(scope_path), binding(declaration_path)]
    out.mkdir()
    freeze = {'status': 'frozen_before_coder_import_and_inference', 'runtime_version': VERSION,
        'created_at_utc': now(), 'scope_name': args.scope, 'expected_n': len(selected_ids),
        'authorized_record_ids': selected_ids, 'approved_unique_ID_N': 10,
        'unchanged67_old_v09_first_outputs_retained_without_rerun': True,
        'new77_first_run_claim': False,
        'implementation_files': code, 'material_bindings': materials, 'control_inputs': control_inputs,
        'source_relation_semantics_identical_v09': True, 'not_pure_path_adapter': True,
        'v14_change_scope': ['actual source binding and complete literal TXT leaf adapter only'],
        'source_v12_and_v13_original_fields_preserved': True, 'v14_consumed': True,
        'v14_effective_ten_bundle_material_sha256': manifest['complete_bundles_canonical_sha256'],
        'v13_extension_manifest_sha256': manifest['v13_extension_manifest_sha256'],
        'v14_extension_manifest_sha256': manifest['v14_extension_manifest_sha256'],
        'new_material_input_version_declared': True,
        'dimension_evidence_relations_and_receipt_semantics_unchanged_v09': True,
        'manual_clarification_version': 'v1.3-development; definitions unchanged from v1.1', 'reference_input': None,
        'new2_new4_labels_AB_native_forbidden': True, 'pixels_not_interpreted': True,
        'full4481_remaining1444_not_decoded_or_inferred': True,
        'interpretation': '指定10条v14来源更新首次执行；67条保留旧v09首判，不是新77首轮；本线程不读开发参照或评估指标'}
    write_json(out / 'freeze.json', freeze)
    allowed = {Path(i['path']).resolve() for i in code + materials + control_inputs}
    stdlib = Path(os.__file__).resolve().parent
    reads = []
    def audit(event, params):
        if event != 'open' or not params or isinstance(params[0], int):
            return
        target = Path(os.fsdecode(params[0])).resolve()
        mode = params[1] if len(params) > 1 else None
        flags = params[2] if len(params) > 2 else 0
        writing = isinstance(mode, str) and any(c in mode for c in 'wax+')
        writing |= bool(flags and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        if writing:
            if out not in target.parents:
                raise PermissionError('inference write outside new run directory')
        else:
            if target.name == 'reference.jsonl' or '/04-calibration/' in str(target):
                raise PermissionError('reference/calibration output forbidden during inference')
            if target not in allowed and out not in target.parents and stdlib not in target.parents:
                raise PermissionError('unapproved inference read: ' + str(target))
            reads.append(str(target))
    sys.addaudithook(audit)
    started = now()
    delivered, predictions, errors, units, consumption_logs = [], [], [], [], []
    loader_completed = False
    try:
        modules = load_frozen_coders(implementation, code)
        source = modules['source_packet']
        all_bundles = source.load_scope(scope_path)
        by_id = {b['source_record']['id']: b for b in all_bundles}
        if list(by_id) != approved or len(all_bundles) != 10:
            raise ValueError('reader did not return exact finite complete bundle order')
        protocol = finite_protocol(source, all_bundles, materials, manifest)
        delivered = [by_id[i] for i in selected_ids]
        loader_completed = True
        write_jsonl(out / 'delivered-complete-source-bundles.jsonl', delivered)
        for bundle in delivered:
            row = bundle['source_record']
            view = None
            prediction = {'id': row['id'], 'labels': None, 'decisions': None, 'relation_traces': [],
                'source_relation_traces': [], 'implementation_errors': [], 'source_requests': [], 'pixels_interpreted': False}
            try:
                unit = source.semantic_unit(bundle)
                if 'id' in unit:
                    raise ValueError('semantic unit exposes administrative ID')
                view = modules['relations'].RelationView(unit)
                for name in ('source_view_events', 'source_relation_traces', 'source_requests', 'source_scope_review'):
                    if not hasattr(view, name):
                        raise ValueError('required source-consumer API missing: ' + name)
                if not view.source_view_events:
                    raise ValueError('source consumer did not record actual source view events')
                decisions = modules['dimensions'].judge(view)
                modules['evidence'].validate_decisions(view.unit, decisions)
                prediction['candidate_decisions_diagnostic_only'] = copy.deepcopy(decisions)
                source_log, source_check = actual_reading_log(protocol, bundle, view, out.name)
                if source_check['errors']:
                    raise ValueError('source protocol receipt errors: ' + cj(source_check['errors']))
                stops = source_check['dependency_stop_reasons']
                if any(reason in stops for reason in ('required_view_not_read', 'scope_boundary_unknown', 'read_delivery_incomplete')):
                    raise ValueError('required source consumption incomplete: ' + cj(stops))
                if stops:
                    unresolved = [r for r in view.source_requests
                        if r.get('status', 'unresolved') != 'resolved' and r.get('necessary_dependency', True)]
                    if not unresolved or not view.material_requests:
                        raise ValueError('source dependency stop has no concrete stopped rule dependency')
                    for request in view.material_requests:
                        stopped = any(request in decision['needed_material'] or request in
                            decision.get('details', {}).get('unresolved_material_requests', [])
                            for decision in decisions.values())
                        if not stopped:
                            raise ValueError('source dependency request was not retained in a decision stop or independent-positive audit')
                prediction.update(labels={d: decisions[d]['value'] for d in DIMENSIONS}, decisions=decisions,
                    relation_traces=view.traces(), material_requests=copy.deepcopy(view.material_requests),
                    source_requests=copy.deepcopy(view.source_requests),
                    source_relation_traces=copy.deepcopy(view.source_relation_traces),
                    source_protocol_requirements_recorded=source_check['source_read_requirements_recorded'],
                    source_dependency_stop_reasons=source_check['dependency_stop_reasons'])
                units.append({'id': row['id'], 'semantic_unit': copy.deepcopy(view.unit)})
                consumption_logs.append({'id': row['id'], 'inventory': source.source_inventory(bundle),
                    'actual_text_geometry_events': copy.deepcopy(view.source_view_events),
                    'source_relation_traces': prediction['source_relation_traces'],
                    'uniform_source_reading_log': source_log, 'uniform_source_protocol_check': source_check,
                    'material_requests': prediction['material_requests'], 'source_requests': prediction['source_requests'],
                    'reader': 'AI_rule_runtime', 'image_read_N': 0, 'source_producer_pixel_read_not_inherited': True})
            except Exception as error:
                detail = {'id': row['id'], 'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
                errors.append(detail)
                prediction['implementation_errors'].append(detail)
                if view is not None:
                    for attr in ('source_requests', 'source_view_events', 'source_relation_traces'):
                        if hasattr(view, attr):
                            prediction[attr] = copy.deepcopy(getattr(view, attr))
                for attr in ('source_requests', 'source_view_events', 'source_relation_traces'):
                    if hasattr(error, attr):
                        prediction[attr] = copy.deepcopy(getattr(error, attr))
                consumption_logs.append({'id': row['id'], 'source_reading_status': 'technical_failure', 'implementation_error': detail, 'image_read_N': 0,
                    'retained_error_source_requests': copy.deepcopy(getattr(error, 'source_requests', [])),
                    'retained_error_source_view_events': copy.deepcopy(getattr(error, 'source_view_events', [])),
                    'retained_error_source_relation_traces': copy.deepcopy(getattr(error, 'source_relation_traces', []))})
            predictions.append(prediction)
    except Exception as error:
        errors.append({'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()})
    if not predictions and errors:
        snapshot = manifest.get('complete_bundle_snapshot')
        if snapshot:
            try:
                payload = Path(snapshot['path']).read_bytes()
                expected = next(i for i in materials if i['path'] == snapshot['path'])
                if hashlib.sha256(payload).hexdigest() != expected['sha256'] or len(payload) != expected['bytes']:
                    raise ValueError('diagnostic snapshot does not match frozen binding')
                raw = [json.loads(line) for line in payload.splitlines()]
                if [b['source_record']['id'] for b in raw] != approved:
                    raise ValueError('diagnostic snapshot ID order differs from exact authorized10')
                raw_by_id = {b['source_record']['id']: b for b in raw}
                delivered = [raw_by_id[i] for i in selected_ids]
                write_jsonl(out / 'diagnostic-source-bundles-loader-failure.jsonl', delivered)
            except Exception as fallback_error:
                errors.append({'type': 'DiagnosticSourceUnavailable', 'message': str(fallback_error)})
        # These are expected-ID failure ledger rows, never delivered source rows
        # or classifier judgments. All five technical slots remain explicit.
        predictions = [{'id': rid, 'labels': None, 'decisions': None,
            'relation_traces': [], 'source_relation_traces': [], 'source_requests': [],
            'raw_source_delivery_status': 'not_delivered_due_to_loader_failure',
            'implementation_errors': copy.deepcopy(errors), 'pixels_interpreted': False}
            for rid in selected_ids]
    write_jsonl(out / 'predictions.jsonl', predictions)
    write_jsonl(out / 'effective-semantic-units.jsonl', units)
    write_jsonl(out / 'actual-source-consumption.jsonl', consumption_logs)
    changed = [i['path'] for i in code + materials + control_inputs if digest(i['path']) != i['sha256']]
    if changed:
        errors.append({'type': 'ChangedDependency', 'paths': changed})
    global_errors = [e for e in errors if 'id' not in e]
    slots = dimension_slots(delivered, predictions, global_errors, diagnostic_only=not loader_completed)
    write_jsonl(out / 'all-dimension-slots.jsonl', slots)
    complete = not errors and len(predictions) == len(selected_ids)
    execution = {'status': 'completed' if complete else 'failed_development_attempt',
        'started_at_utc': started, 'finished_at_utc': now(), 'runtime_version': VERSION,
        'scope_name': args.scope, 'expected_record_n': len(selected_ids), 'attempted_record_n': len(delivered) if loader_completed else 0,
        'diagnostic_snapshot_record_n': 0 if loader_completed else len(delivered),
        'output_record_n': len(predictions), 'raw_source_delivered_record_n': len(delivered), 'decision_n': sum(len(p['labels']) for p in predictions if isinstance(p['labels'], dict)),
        'all_dimension_slot_n': len(slots), 'implementation_errors': errors,
        'technical_failure_dimension_n': sum(s['technical_failure'] for s in slots), 'rules_null_n': sum(s['rules_null'] for s in slots),
        'read_paths': sorted(set(reads)), 'no_reference_read': True, 'reference_evaluation_performed': False,
        'source_bundle_is_default_complete_equivalent': loader_completed and len(delivered) == len(selected_ids) and not changed, 'actual_image_pixel_read_N': 0,
        'image_bytes_integrity_check_is_not_pixel_interpretation': True,
        'new2_new4_reference_evaluation': False, 'not_formal_accuracy_or_human_validation': True}
    write_json(out / 'execution.json', execution)
    files = [binding(out / name) for name in ['freeze.json', 'delivered-complete-source-bundles.jsonl', 'predictions.jsonl',
        'effective-semantic-units.jsonl', 'actual-source-consumption.jsonl', 'all-dimension-slots.jsonl', 'diagnostic-source-bundles-loader-failure.jsonl', 'execution.json'] if (out / name).exists()]
    seal = {'status': 'sealed_development_predictions' if complete else 'sealed_failed_development_attempt',
        'sealed_at_utc': now(), 'runtime_version': VERSION, 'scope_name': args.scope, 'record_ids': selected_ids,
        'prediction_path': str(out / 'predictions.jsonl'), 'prediction_sha256': digest(out / 'predictions.jsonl'),
        'prediction_n': len(predictions), 'decision_n': execution['decision_n'], 'all_dimension_slot_n': len(slots),
        'implementation_error_n': len(errors), 'rules_null_n': execution['rules_null_n'],
        'technical_failure_dimension_n': execution['technical_failure_dimension_n'], 'complete': complete,
        'no_reference_read': True, 'implementation_files': code, 'material_bindings': materials,
        'control_inputs': control_inputs, 'output_files': files,
        'new2_new4_reference_evaluation_authorized': False, 'actual_pixel_read_N': 0}
    write_json(out / 'seal.json', seal)
    print(json.dumps({k: seal[k] for k in ['status', 'scope_name', 'prediction_n', 'decision_n', 'prediction_sha256',
        'implementation_error_n', 'rules_null_n', 'technical_failure_dimension_n']}, ensure_ascii=False))
    return 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
