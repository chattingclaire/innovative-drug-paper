"""Final sealed v5 full4481 original common source-only execution; one first domain pass; persistent per-record outputs."""
import argparse, copy, datetime, hashlib, json, os, sys, traceback, types
from pathlib import Path
VERSION='v7-full4481-original-common-driver-1'
sys.dont_write_bytecode = True
from interface_common import parse_json, verify_binding, unpack_packet
from status_bridge import canonicalize_request
HERE = Path(__file__).resolve().parent
DIMENSIONS=('S','E','Ec','I','F')
INFERENCE_FILES=('rule_driver.py','interface_common.py','status_bridge.py','algorithm-bindings.json','packet-bindings.json')
ACTIVE_OUT=None
RUNTIME_STAGE='preflight'
CODER_MODULES=('source_packet','source_receipts','evidence','relations','dimensions')

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
        p = Path(expected[name]['path'])
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


def capture_exception_source_audit(view, error, source_log, source_check, source_log_stage):
    """Snapshot available exception-time data; never reconstruct missing old logs."""
    attributes = ('source_requests', 'material_requests', 'source_view_events', 'source_relation_traces')
    exception_attributes = attributes + ('source_log', 'source_check',
        'uniform_source_reading_log', 'uniform_source_protocol_check')
    live = {}
    live_present = {}
    for name in attributes:
        present = view is not None and hasattr(view, name)
        live_present[name] = present
        if present:
            live[name] = copy.deepcopy(getattr(view, name))
    carried = {}
    exception_present = {}
    for name in exception_attributes:
        present = hasattr(error, name)
        exception_present[name] = present
        if present:
            carried[name] = copy.deepcopy(getattr(error, name))
    snapshot = {
        'live_view_available': view is not None,
        'live_view_attribute_presence': live_present,
        'live_view_source_audit': live,
        'exception_attribute_presence': exception_present,
        'exception_source_audit': carried,
        'primary_source_audit_origin': {},
        'uniform_source_reading_log': copy.deepcopy(source_log),
        'uniform_source_protocol_check': copy.deepcopy(source_check),
        'uniform_source_audit_state': {
            'driver_call_stage': source_log_stage,
            'log': 'available_returned_value' if source_log is not None else (
                'not_produced' if source_log_stage == 'not_started' else 'not_returned_to_driver'),
            'check': 'available_returned_value' if source_check is not None else (
                'not_produced' if source_log_stage == 'not_started' else 'not_returned_to_driver'),
            'local_byte_reconstruction_claimed': False}}
    for name in attributes:
        if live_present[name]:
            snapshot[name] = copy.deepcopy(live[name])
            snapshot['primary_source_audit_origin'][name] = 'live_view'
        elif exception_present[name]:
            snapshot[name] = copy.deepcopy(carried[name])
            snapshot['primary_source_audit_origin'][name] = 'exception_attribute'
        else:
            snapshot[name] = []
            snapshot['primary_source_audit_origin'][name] = 'not_available'
    return snapshot


def finite_protocol(source, bundles, materials, scope):
    item=next(b for b in materials if Path(b['path']).name=='source_reading_protocol_v12.py')
    payload=Path(item['path']).read_bytes()
    if hashlib.sha256(payload).hexdigest()!=item['sha256']:raise ValueError('protocol changed')
    by_id={b['source_record']['id']:b for b in bundles}
    facade=types.ModuleType('source_only_interface_v12')
    def lookup(rid,selector='rule',bundle=True):
        if selector!='rule' or not bundle or rid not in by_id:raise ValueError('outside explicit frozen scope')
        return copy.deepcopy(by_id[rid])
    facade.lookup=lookup
    from source_receipts import resolve_inventory
    source_base=Path(scope['v12_source_base'])
    facade.source_inventory=lambda b:resolve_inventory(b,source.source_inventory(b),materials,source_base)[0]
    facade.cj=cj;facade.CANON_SHA=scope['complete_bundles_canonical_sha256'];facade.MANIFEST_SHA=scope['source_manifest_sha256']
    sys.modules['source_only_interface_v12']=facade
    protocol=types.ModuleType('finite_source_reading_protocol_v12');protocol.__file__=item['path']
    exec(compile(payload,item['path'],'exec'),protocol.__dict__)
    protocol.bound_source_identity={'consumer_interface_version':VERSION,'authorized_finite_record_N':len(bundles),'source_packet_binding':scope['source_packet'],'source_package_seal':scope['source_package_seal'],'manual_binding':scope['manual'],'original_protocol_code_unchanged_finite_facade':True}
    protocol.producer_source_inventory=source.source_inventory
    protocol.source_identity_resolver=lambda b:resolve_inventory(b,source.source_inventory(b),materials,source_base)
    return protocol


def literal_leaf_integrity(bundles,materials):
    expected={b['path']:b for b in materials};cache={};checks=[];seen=set()
    for bundle in bundles:
        for leaf in bundle['source_full_text_resources']:
            if leaf.get('kind')!='verbatim_UTF8_snapshot_text':continue
            key=leaf['source_resource_id']
            if key in seen:continue
            seen.add(key);locator=leaf['locator'];p=Path(locator['snapshot_absolute_path']).resolve()
            entry=expected[str(p)]
            if p not in cache:
                raw=p.read_bytes()
                if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('literal snapshot changed')
                cache[p]=(raw,raw.decode('utf8'))
            raw,text=cache[p];a,b=locator['unicode_code_point_interval_half_open'];x,y=locator['utf8_byte_interval_half_open']
            if (entry['sha256']!=leaf['source_sha256'] or text[a:b]!=leaf['text'] or raw[x:y]!=leaf['text'].encode('utf8')
                    or hashlib.sha256(raw[x:y]).hexdigest()!=leaf['text_utf8_sha256']):raise ValueError('literal primary leaf source/byte/span mismatch')
            checks.append({'resource_id':key,'source_sha256':entry['sha256'],'unicode_span':[a,b],'utf8_byte_span':[x,y],'leaf_sha256':leaf['text_utf8_sha256'],'exact_snapshot_span_verified':True,'integrity_read_is_not_pixel_read':True})
    return checks

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
    # Canonical field alias only: preserve each request, its proof and order.
    # Missing/conflicting statuses raise instead of inferring resolution.
    log['original_source_requests'] = copy.deepcopy(view.source_requests)
    normalized=[canonicalize_request(r) for r in view.source_requests]
    log['source_requests'] = [r for r,p in normalized]
    log['source_request_status_alias_provenance'] = [p for r,p in normalized]
    review = view.source_scope_review
    log['necessary_source_scope_review_status'] = review['status']
    log['necessary_source_scope_review_note'] = review['source_evidence_note']
    log['reference_resolution'] += copy.deepcopy(getattr(view, 'source_reference_resolution', []))
    log['actual_text_geometry_events'] = events
    log['image_read_N'] = 0
    log['image_file_integrity_read_is_not_pixel_interpretation'] = True
    return log, protocol.check(log)


def main():
    global ACTIVE_OUT,RUNTIME_STAGE
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('scope', 'scope-sha256', 'input', 'input-sha256', 'out'):
        parser.add_argument('--'+flag,required=True)
    args=parser.parse_args()
    scope_path=Path(args.scope).resolve();out=Path(args.out).resolve()
    if out.exists():raise ValueError('first output exists; use a distinct authorized round, never overwrite')
    if digest(scope_path)!=args.scope_sha256:raise ValueError('predeclared scope changed')
    scope=parse_json(scope_path.read_bytes())
    if scope.get('driver_version')!=VERSION:raise ValueError('explicit driver version required')
    if scope.get('status')!='frozen_for_execution':raise ValueError('scope not released for execution')
    if scope.get('output_directory')!=str(out):raise ValueError('output outside frozen authorization')
    if scope.get('max_actual_cohort_inference_runs')!=1:raise ValueError('scope must authorize exactly one run')
    if scope.get('execution_purpose') != 'production_provisional':
        raise ValueError('adapter permits production_provisional execution only')
    if scope.get('expected_record_N') != 4481 or scope.get('expected_dimension_N') != 22405:
        raise ValueError('adapter requires the complete 4481-record, 22405-dimension scope')
    if scope.get('formal_validation_complete') is not False or scope.get('human_validation_complete') is not False or scope.get('blind_validation') is not False:
        raise ValueError('production_provisional scope must retain unfinished human/formal validation and disclosed calibration provenance')
    for key in ('manual', 'prompt', 'protocol', 'source_reading_protocol_code', 'release'):
        verify_binding(scope[key])
    release = parse_json(Path(scope['release']['path']).read_bytes())
    if release.get('status') != 'released_for_production_provisional' or release.get('execution_purpose') != 'production_provisional':
        raise ValueError('external release does not authorize production_provisional execution')
    if not isinstance(scope.get('authorization_id'), str) or not scope['authorization_id'] or release.get('authorization_id') != scope['authorization_id']:
        raise ValueError('scope authorization differs from exact release')
    if release.get('output_directory') != str(out) or release.get('max_actual_cohort_inference_runs') != 1:
        raise ValueError('release must authorize this first output and exactly one run')
    for key, release_key in (('manual', 'manual'), ('prompt', 'prompt'), ('protocol', 'protocol'), ('source_packet', 'source_input')):
        if release.get(release_key) != scope[key]:
            raise ValueError('released common binding differs: ' + release_key)
    if Path(args.input).resolve()!=Path(scope['source_packet']['path']).resolve() or args.input_sha256!=scope['source_packet']['sha256']:
        raise ValueError('CLI input differs from frozen scope')
    verify_binding(scope['source_packet']);verify_binding(scope['manual'])
    algorithm_path=HERE/'algorithm-bindings.json'
    verify_binding(scope['algorithm_bindings'])
    if Path(scope['algorithm_bindings']['path']).resolve()!=algorithm_path:
        raise ValueError('algorithm manifest must be this immutable driver dependency')
    algorithms=parse_json(algorithm_path.read_bytes())['modules']
    if [x['module'] for x in algorithms]!=list(CODER_MODULES):raise ValueError('fixed candidate module order changed')
    for item in algorithms:verify_binding(item)
    materials=scope['material_bindings'];control_inputs=[binding(scope_path)]
    for required in (scope['source_packet'],scope['manual'],scope['prompt'],scope['protocol'],scope['source_reading_protocol_code'],scope['release']):
        if not any(x==required for x in materials):raise ValueError('released common input absent from exact material bindings')
    if len(scope['approved_record_ids'])!=scope['expected_record_N'] or len(set(scope['approved_record_ids']))!=scope['expected_record_N']:
        raise ValueError('frozen record order missing, duplicate, or wrong count')
    if scope['expected_dimension_N']!=scope['expected_record_N']*5:raise ValueError('frozen dimension count differs')
    for b in materials:
        if digest(b['path'])!=b['sha256'] or Path(b['path']).stat().st_size!=b['bytes']:raise ValueError('material changed '+b['path'])
    protocol_files=[b for b in materials if Path(b['path']).name=='source_reading_protocol_v12.py']
    if protocol_files != [scope['source_reading_protocol_code']]:
        raise ValueError('source protocol code must be the unique unchanged finite-protocol material')
    implementation=HERE
    code=[binding(implementation/n) for n in INFERENCE_FILES]+algorithms
    out.parent.mkdir(parents=True,exist_ok=True);out.mkdir();ACTIVE_OUT=out;RUNTIME_STAGE='frozen_source_delivery'
    freeze={'status':'frozen_before_coder_import_and_inference','runtime_version':VERSION,'created_at_utc':now(),'implementation_files':code,'material_bindings':materials,'control_inputs':control_inputs,'source_scope':scope,'max_actual_cohort_inference_runs':1,'reference_input':None,'semantic_change':'joint-v7 generic direct-content and bounded-relation repair; original common packets/manual/prompt/protocol unchanged','fixed_algorithm_version':'joint-v7-relation-content-sol','execution_purpose':scope['execution_purpose'],'formal_validation_complete':False,'human_validation_complete':False,'calibration_labels_already_disclosed':True,'blind_validation':False,'common_release_binding':scope['release'],'authorization_id':scope['authorization_id'],'algorithm_origin':scope['algorithm_origin'],'final_candidate_algorithm':scope['final_candidate_algorithm'],'final_candidate_pre_execution_seal':scope['final_candidate_pre_execution_seal'],'final_candidate_delivery_seal':scope['final_candidate_delivery_seal'],'source_material_candidate_adopted':False,'neutral_projection_GO':False}
    write_json(out/'freeze.json',freeze)
    allowed={Path(b['path']).resolve() for b in code+materials+control_inputs};stdlib=Path(os.__file__).resolve().parent;reads=[]
    def audit(event,params):
        if event!='open' or not params or isinstance(params[0],int):return
        target=Path(os.fsdecode(params[0])).resolve();mode=params[1] if len(params)>1 else None;flags=params[2] if len(params)>2 else 0
        writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or bool(flags and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
        if writing:
            if out not in target.parents:raise PermissionError('write outside first run')
        else:
            if target.name=='reference.jsonl' or '/04-calibration/' in str(target):raise PermissionError('reference/calibration prohibited')
            if target not in allowed and out not in target.parents and stdlib not in target.parents:raise PermissionError('unapproved read '+str(target))
            reads.append(str(target))
    sys.addaudithook(audit);started=now();predictions=[];errors=[];units=[];consumption_logs=[]
    modules=load_frozen_coders(implementation,code);source=modules['source_packet']
    raw=Path(scope['source_packet']['path']).read_bytes();delivered=[];deliveries=[]
    packet_plan=parse_json(verify_binding(scope['packet_bindings']))
    if packet_plan['ordered_source_ids']!=scope['approved_record_ids'] or packet_plan['packet_N']!=4481:raise ValueError('packet manifest order differs')
    cursor=0
    for line_no,line in enumerate(raw.splitlines(keepends=True),1):
        if not line.strip():raise ValueError('blank input row')
        frozen_bundle,metadata=unpack_packet(parse_json(line))
        packet_entry=packet_plan['packets'][line_no-1]
        packet_raw=verify_binding(packet_entry)
        packet=parse_json(packet_raw)
        if set(packet)!={'output_id','packet_version','source_bundle','source_bundle_sha256','source_id','verified_asset_files'} or packet['packet_version']!='native-full-source-3':
            raise ValueError('original native packet shape/version changed')
        bundle=packet['source_bundle']
        if packet['source_id']!=packet_entry['source_id'] or packet['source_bundle_sha256']!=packet_entry['source_bundle_sha256'] or cj(bundle)!=cj(frozen_bundle):
            raise ValueError('original packet differs from frozen same-order common bundle')
        if hashlib.sha256(cj(bundle).encode()).hexdigest()!=packet['source_bundle_sha256']:
            raise ValueError('original packet canonical SHA differs')
        metadata.update(input_line_1based=line_no,input_line_sha256=hashlib.sha256(line).hexdigest(),
                        input_start_utf8_byte=cursor,input_end_utf8_byte_exclusive=cursor+len(line),
                        actual_input_kind='original_frozen_native_packet',actual_packet_binding=packet_entry,
                        original_packet_output_id=packet['output_id'],same_common_JSONL_identity_verified=True)
        cursor+=len(line);delivered.append(bundle);deliveries.append(metadata)
    if [b['source_record']['id'] for b in delivered]!=scope['approved_record_ids'] or len(delivered)!=scope['expected_record_N']:
        raise ValueError('explicit frozen order/count mismatch')
    write_jsonl(out/'input-deliveries.jsonl',deliveries)
    leaf_checks=literal_leaf_integrity(delivered,materials)
    protocol=finite_protocol(source,delivered,materials,scope)
    write_jsonl(out/'delivered-complete-source-bundles.jsonl',delivered)
    streams={name:(out/name).open('x',encoding='utf-8') for name in ('predictions.jsonl','effective-semantic-units.jsonl','actual-source-consumption.jsonl','execution-ledger.jsonl')}
    RUNTIME_STAGE='inference'
    for bundle in delivered:
        row = bundle['source_record']
        view = None
        source_log = None
        source_check = None
        source_log_stage = 'not_started'
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
            source_log_stage = 'building'
            source_log, source_check = actual_reading_log(protocol, bundle, view, out.name)
            source_log_stage = 'returned'
            if source_check['errors']:
                raise ValueError('source protocol receipt errors: ' + cj(source_check['errors']))
            stops = source_check['dependency_stop_reasons']
            if any(reason in stops for reason in ('required_view_not_read', 'scope_boundary_unknown', 'read_delivery_incomplete')):
                raise ValueError('required source consumption incomplete: ' + cj(stops))
            if stops:
                unresolved = [r for r in view.source_requests
                    if canonicalize_request(r)[0]['status'] != 'resolved' and r.get('necessary_dependency', True)]
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
            exception_audit = capture_exception_source_audit(
                view, error, source_log, source_check, source_log_stage)
            prediction.update(copy.deepcopy(exception_audit))
            consumption_logs.append({'id': row['id'], 'source_reading_status': 'technical_failure', 'implementation_error': detail, 'image_read_N': 0,
                **copy.deepcopy(exception_audit),
                'retained_error_source_requests': copy.deepcopy(exception_audit['exception_source_audit'].get('source_requests', [])),
                'retained_error_material_requests': copy.deepcopy(exception_audit['exception_source_audit'].get('material_requests', [])),
                'retained_error_source_view_events': copy.deepcopy(exception_audit['exception_source_audit'].get('source_view_events', [])),
                'retained_error_source_relation_traces': copy.deepcopy(exception_audit['exception_source_audit'].get('source_relation_traces', []))})
        predictions.append(prediction)
        streams['predictions.jsonl'].write(json.dumps(prediction,ensure_ascii=False,allow_nan=False)+'\n')
        streams['actual-source-consumption.jsonl'].write(json.dumps(consumption_logs[-1],ensure_ascii=False,allow_nan=False)+'\n')
        if units and units[-1]['id']==row['id']:
            streams['effective-semantic-units.jsonl'].write(json.dumps(units[-1],ensure_ascii=False,allow_nan=False)+'\n')
        ledger={'index_1based':len(predictions),'id':row['id'],'at_utc':now(),'stage':'record_completed','technical_failure':bool(prediction['implementation_errors']),'labels':prediction.get('labels'),'source_bundle_sha256':hashlib.sha256(cj(bundle).encode()).hexdigest(),'one_adapter_view_judge_attempt_only':True,'no_null_filled_zero':True}
        streams['execution-ledger.jsonl'].write(json.dumps(ledger,ensure_ascii=False,allow_nan=False)+'\n')
        for stream in streams.values():stream.flush()
        units.clear();consumption_logs.clear()
        if len(predictions)%100==0:
            print(json.dumps({'stage':'inference','completed_record_N':len(predictions),'technical_failure_record_N':len(errors),'at_utc':now()},ensure_ascii=False),flush=True)
    for stream in streams.values():stream.close()
    changed=[b['path'] for b in code+materials+control_inputs if digest(b['path'])!=b['sha256']]
    if changed:errors.append({'type':'ChangedDependency','paths':changed})
    slots=dimension_slots(delivered,predictions,[e for e in errors if 'id' not in e]);write_jsonl(out/'all-dimension-slots.jsonl',slots)
    execution={'status':'completed' if not errors else 'failed_execution_attempt','started_at_utc':started,'finished_at_utc':now(),'runtime_version':VERSION,'expected_record_N':scope['expected_record_N'],'actual_record_N':len(predictions),'actual_dimension_N':len(slots),'retained_decision_N':sum(isinstance(p.get('labels'),dict) for p in predictions)*5,'technical_failure_dimension_N':sum(s['technical_failure'] for s in slots),'lawful_null_N':sum(s['rules_null'] for s in slots),'implementation_errors':errors,'literal_primary_leaf_integrity_checks':leaf_checks,'read_paths':sorted(set(reads)),'no_reference_read':True,'actual_cohort_inference_runs':1,'image_read_N':0,'execution_purpose':scope['execution_purpose'],'formal_validation_complete':False,'human_validation_complete':False}
    write_json(out/'execution.json',execution)
    outputs=[binding(p) for p in sorted(out.iterdir()) if p.is_file()]
    seal={'status':'sealed_complete_production_provisional_rule_run' if not errors else 'sealed_failed_execution_attempt','sealed_at_utc':now(),'runtime_version':VERSION,'implementation_files':code,'material_bindings':materials,'control_inputs':control_inputs,'output_files':outputs,'prediction_binding':binding(out/'predictions.jsonl'),'record_N':len(predictions),'dimension_N':len(slots),'technical_failure_dimension_N':execution['technical_failure_dimension_N'],'lawful_null_N':execution['lawful_null_N'],'max_actual_cohort_inference_runs':1,'source_packet_unchanged':not changed,'no_reference_read':True,'image_read_N':0,'execution_purpose':'production_provisional','formal_validation_complete':False,'human_validation_complete':False,'blind_validation':False,'common_release_binding':scope['release']}
    write_json(out/'seal.json',seal)
    print(json.dumps({k:execution[k] for k in ['status','actual_record_N','actual_dimension_N','technical_failure_dimension_N','lawful_null_N']},ensure_ascii=False));return 0 if not errors else 2

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        if ACTIVE_OUT is not None and not (ACTIVE_OUT/'seal.json').exists():
            failure={'status':'terminal_driver_technical_failure','stage':RUNTIME_STAGE,
                'error_type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc(),
                'no_missing_label_filled_zero':True,'formal_validation_complete':False,
                'actual_cohort_inference_started':RUNTIME_STAGE=='inference'}
            write_json(ACTIVE_OUT/'driver-failure.json',failure)
            outputs=[binding(p) for p in sorted(ACTIVE_OUT.iterdir()) if p.is_file()]
            write_json(ACTIVE_OUT/'seal.json',{'status':'sealed_terminal_driver_failure','output_files':outputs,
                'stage':RUNTIME_STAGE,'existing_first_output_bytes_preserved':True,'no_labels_backfilled':True})
        print(json.dumps({'status':'rejected_or_failed','reason':str(error),'stage':RUNTIME_STAGE},ensure_ascii=False),file=sys.stderr)
        raise SystemExit(2)
