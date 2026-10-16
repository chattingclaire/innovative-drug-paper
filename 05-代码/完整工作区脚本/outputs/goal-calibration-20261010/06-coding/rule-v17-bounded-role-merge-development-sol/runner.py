"""One fixed development77 inference; frozen source-v14 and manual1.3.
Reuse sealed semantic/dimension/evidence/receipt code. Only inline heading recognition extends the previously bounded
primary operative-standard relation completion. No reference is read here.
"""
import argparse, copy, datetime, hashlib, json, os, sys, traceback, types
from pathlib import Path
VERSION='rule-v17-bounded-role-merge-development-sol'
DIMENSIONS=('S','E','Ec','I','F')
INFERENCE_FILES=('runner.py','source_packet.py','source_receipts.py','evidence.py','relations.py','dimensions.py')
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
    item=next(b for b in materials if Path(b['path']).name=='source_reading_protocol_v12.py')
    payload=Path(item['path']).read_bytes()
    if hashlib.sha256(payload).hexdigest()!=item['sha256']:raise ValueError('protocol changed')
    by_id={b['source_record']['id']:b for b in bundles}
    facade=types.ModuleType('source_only_interface_v12')
    def lookup(rid,selector='rule',bundle=True):
        if selector!='rule' or not bundle or rid not in by_id:raise ValueError('outside frozen77 scope')
        return copy.deepcopy(by_id[rid])
    facade.lookup=lookup
    from source_receipts import resolve_inventory
    source_base=Path(scope['v12_source_base'])
    facade.source_inventory=lambda b:resolve_inventory(b,source.source_inventory(b),materials,source_base)[0]
    facade.cj=cj;facade.CANON_SHA=scope['complete_bundles_canonical_sha256'];facade.MANIFEST_SHA=scope['source_manifest_sha256']
    sys.modules['source_only_interface_v12']=facade
    protocol=types.ModuleType('finite_source_reading_protocol_v12');protocol.__file__=item['path']
    exec(compile(payload,item['path'],'exec'),protocol.__dict__)
    protocol.bound_source_identity={'consumer_interface_version':'v17-finite77-bounded-role-merge','authorized_finite_record_N':len(bundles),'source_packet_binding':scope['source_packet'],'source_package_seal':scope['source_package_seal'],'manual_binding':scope['manual'],'original_protocol_code_unchanged_finite_facade':True}
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--scope',required=True);parser.add_argument('--scope-sha256',required=True);parser.add_argument('--out',required=True);args=parser.parse_args()
    implementation=Path(__file__).resolve().parent;scope_path=Path(args.scope).resolve();out=Path(args.out).resolve()
    if scope_path.parent!=implementation or out.parent!=implementation or out.name!='run77-first' or out.exists():raise ValueError('one first new authorized run only')
    if digest(scope_path)!=args.scope_sha256:raise ValueError('predeclared scope changed')
    scope=json.loads(scope_path.read_text());materials=scope['material_bindings'];control_inputs=[binding(scope_path)]
    for b in materials:
        if digest(b['path'])!=b['sha256'] or Path(b['path']).stat().st_size!=b['bytes']:raise ValueError('material changed '+b['path'])
    code=[binding(implementation/n) for n in INFERENCE_FILES];out.mkdir()
    freeze={'status':'frozen_before_coder_import_and_inference','runtime_version':VERSION,'created_at_utc':now(),'implementation_files':code,'material_bindings':materials,'control_inputs':control_inputs,'source_scope':scope,'max_actual_cohort_inference_runs':1,'reference_input':None,'semantic_change':'bounded primary standards and object/priority/withdrawal role preservation; I3 priority form limited to proven role relation','all77_real_execution':True,'not_formal_accuracy_or_human_validation':True}
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
    raw=Path(scope['source_packet']['path']).read_bytes();delivered=[json.loads(line) for line in raw.splitlines() if line.strip()]
    if [b['source_record']['id'] for b in delivered]!=scope['approved_record_ids'] or len(delivered)!=scope['expected_record_N']:raise ValueError('fixed77 order mismatch')
    leaf_checks=literal_leaf_integrity(delivered,materials)
    protocol=finite_protocol(source,delivered,materials,scope)
    write_jsonl(out/'delivered-complete-source-bundles.jsonl',delivered)
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
    write_jsonl(out/'predictions.jsonl',predictions);write_jsonl(out/'effective-semantic-units.jsonl',units);write_jsonl(out/'actual-source-consumption.jsonl',consumption_logs)
    changed=[b['path'] for b in code+materials+control_inputs if digest(b['path'])!=b['sha256']]
    if changed:errors.append({'type':'ChangedDependency','paths':changed})
    slots=dimension_slots(delivered,predictions,[e for e in errors if 'id' not in e]);write_jsonl(out/'all-dimension-slots.jsonl',slots)
    execution={'status':'completed' if not errors else 'failed_development_attempt','started_at_utc':started,'finished_at_utc':now(),'runtime_version':VERSION,'expected_record_N':scope['expected_record_N'],'actual_record_N':len(predictions),'actual_dimension_N':len(slots),'retained_decision_N':sum(isinstance(p.get('labels'),dict) for p in predictions)*5,'technical_failure_dimension_N':sum(s['technical_failure'] for s in slots),'lawful_null_N':sum(s['rules_null'] for s in slots),'implementation_errors':errors,'literal_primary_leaf_integrity_checks':leaf_checks,'read_paths':sorted(set(reads)),'no_reference_read':True,'actual_cohort_inference_runs':1,'image_read_N':0,'not_formal_or_human_validation':True}
    write_json(out/'execution.json',execution)
    outputs=[binding(p) for p in sorted(out.iterdir()) if p.is_file()]
    seal={'status':'sealed_complete_development_run' if not errors else 'sealed_failed_development_attempt','sealed_at_utc':now(),'runtime_version':VERSION,'implementation_files':code,'material_bindings':materials,'control_inputs':control_inputs,'output_files':outputs,'prediction_binding':binding(out/'predictions.jsonl'),'record_N':len(predictions),'dimension_N':len(slots),'technical_failure_dimension_N':execution['technical_failure_dimension_N'],'lawful_null_N':execution['lawful_null_N'],'max_actual_cohort_inference_runs':1,'source_packet_unchanged':not changed,'no_reference_read':True,'image_read_N':0}
    write_json(out/'seal.json',seal)
    print(json.dumps({k:execution[k] for k in ['status','actual_record_N','actual_dimension_N','technical_failure_dimension_N','lawful_null_N']},ensure_ascii=False));return 0 if not errors else 2

if __name__=='__main__':raise SystemExit(main())
