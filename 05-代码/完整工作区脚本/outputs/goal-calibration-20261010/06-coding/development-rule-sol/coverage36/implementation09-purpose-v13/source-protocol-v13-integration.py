"""One necessary source API integration, without judge or reference evaluation."""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import types

BASE = Path(__file__).resolve().parent
CASES = [{'case': 'v13_new_HTML_JSON_inventory_and_branch_source_receipt_integration', 'record_id': 'RECODE25-01423'}]

def main():
    out = Path(sys.argv[1]).resolve()
    if out.exists() or out.parent != BASE:
        raise ValueError('integration output must be a new child of this version')
    out.mkdir()
    runner_path = BASE / 'runner.py'
    runner = types.ModuleType('source_integration_runner')
    runner.__file__ = str(runner_path)
    payload = runner_path.read_bytes()
    # Import definitions only; main/judge are not executed here.
    exec(compile(payload, str(runner_path), 'exec'), runner.__dict__)
    scope = json.loads((BASE / 'source-scope-v13.json').read_text())
    code = [runner.binding(BASE / name) for name in runner.INFERENCE_FILES]
    freeze = {'status': 'source_only_integration_frozen_before_coder_definitions',
        'implementation_files': code, 'source_scope_manifest': runner.binding(BASE / 'source-scope-v13.json'),
        'integration_code': runner.binding(__file__), 'material_bindings': scope['bindings'],
        'cases': CASES, 'judge_call_N': 0, 'reference_read_N': 0,
        'expectations': 'mandatory source APIs present; pure v13 inventories and literal JSON/HTML locators match actual selected source events/use; new material identities bound explicitly; protocol errors and missing mechanical current-source reads are absent; legitimate source requests stay explicit',
        'not_dimension_or_reference_validation': True}
    runner.write_json(out / 'freeze.json', freeze)
    allowed = {Path(i['path']).resolve() for i in code + scope['bindings']}
    allowed.update({Path(__file__).resolve(), BASE / 'source-scope-v13.json'})
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
                raise PermissionError('integration write outside fresh output')
        else:
            if target.name == 'reference.jsonl' or '/04-calibration/' in str(target):
                raise PermissionError('reference/calibration output forbidden in source integration')
            if target not in allowed and out not in target.parents and stdlib not in target.parents:
                raise PermissionError('unapproved source integration read: ' + str(target))
            reads.append(str(target))
    sys.addaudithook(audit)
    results, errors = [], []
    try:
        modules = runner.load_frozen_coders(BASE, code)
        source = modules['source_packet']
        bundles = source.load_scope(BASE / 'source-scope-v13.json')
        protocol = runner.finite_protocol(source, bundles, scope['bindings'], scope)
        by_id = {b['source_record']['id']: b for b in bundles}
        for case in CASES:
            bundle = by_id[case['record_id']]
            view = modules['relations'].RelationView(source.semantic_unit(bundle))
            for attr in ('source_view_events', 'source_relation_traces', 'source_requests', 'source_scope_review'):
                if not hasattr(view, attr):
                    raise ValueError('missing required source API: ' + attr)
            log, check = runner.actual_reading_log(protocol, bundle, view, out.name)
            runner.write_json(out / (case['record_id'] + '-source-log.json'), log)
            identity = log['actual_source_material_identity']
            v13_inventory = [x for x in log['producer_source_inventory']
                if x.get('locator', {}).get('kind') == 'structured_JSON_and_original_HTML']
            uses = [x for x in log['use_receipts'] if x['resource_id'].startswith('SOURCETEXT-')]
            bridge_ok = (identity['consumer_interface_version'] == 'v13-finite-source-extension'
                and identity['finite_complete_bundles_canonical_sha256'] == scope['complete_bundles_canonical_sha256']
                and identity['v13_extension_manifest_sha256'] == scope['v13_extension_manifest_sha256']
                and len(v13_inventory) == 9 and bool(uses)
                and all('structured_snapshot' in x['locator'] and 'raw_html' in x['locator'] for x in v13_inventory)
                and log['source_bundle_extension']['actual_consumer_read_status'] == 'not_recorded')
            bad = (not bridge_ok) or check['errors'] or any(s in check['dependency_stop_reasons'] for s in
                ('required_view_not_read', 'scope_boundary_unknown', 'read_delivery_incomplete'))
            result = {**case, 'contract_pass': not bad, 'check': check,
                'judge_call_N': 0, 'image_read_N': 0, 'source_requests': view.source_requests,
                'v13_protocol_binding_pass': bridge_ok, 'v13_available_literal_inventory_N': len(v13_inventory),
                'actual_v13_source_text_uses': uses, 'actual_source_material_identity': identity}
            results.append(result)
            if bad:
                errors.append(result)
    except Exception as error:
        errors.append({'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()})
    changed = [i['path'] for i in code + scope['bindings'] if runner.digest(i['path']) != i['sha256']]
    if changed:
        errors.append({'type': 'ChangedIntegrationDependency', 'paths': changed})
    runner.write_json(out / 'result.json', {'status': 'PASS' if not errors and len(results) == len(CASES) else 'FAIL',
        'results': results, 'errors': errors, 'judge_call_N': 0, 'reference_read_N': 0,
        'image_pixel_read_N': 0, 'expectations_unchanged': True, 'read_paths': sorted(set(reads))})
    print(json.dumps({'status': 'PASS' if not errors and len(results) == len(CASES) else 'FAIL',
        'case_N': len(results), 'error_N': len(errors), 'judge_call_N': 0}))
    return 0 if not errors and len(results) == len(CASES) else 2


if __name__ == '__main__':
    raise SystemExit(main())
