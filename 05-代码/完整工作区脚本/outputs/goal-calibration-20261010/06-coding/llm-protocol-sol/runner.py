"""Offline preparation and an injected, provider-neutral execution contract. No API exists here."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from adapter import ROOT, ContractError, adapt, canonical, sha, schema_check, verify_assets, validate_response

class ProtocolViolation(ContractError):
    pass

def now():
    return datetime.now(timezone.utc).isoformat()

def implementation_sha256():
    files = list(ROOT.glob('*.py')) + list((ROOT / 'schemas').glob('*.json')) + list((ROOT / 'prompts').glob('*.txt'))
    files += [ROOT / '执行协议.md', ROOT / '稳定性与运行封存预设.md']
    return sha(canonical({str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(files)}))

def valid_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)

def exclusive_json(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def request_bytes(packet, manual_bytes, assets, condition='primary'):
    if condition not in {'primary', 'W', 'H'}:
        raise ContractError('condition is not preregistered')
    system = (ROOT / 'prompts/main-system.txt').read_text(encoding='utf-8')
    user = (ROOT / 'prompts/main-user-template.txt').read_text(encoding='utf-8')
    if condition == 'H':
        if not user.startswith('判读要求\n'):
            raise ContractError('frozen neutral heading changed')
        user = '判读说明\n' + user[len('判读要求\n'):]
    schema = json.loads((ROOT / 'schemas/output.schema.json').read_text(encoding='utf-8'))
    values = {'{{MANUAL_SHA256}}': sha(manual_bytes), '{{MANUAL}}': manual_bytes.decode('utf-8'),
              '{{OUTPUT_SCHEMA}}': canonical(schema).decode('utf-8'),
              '{{SOURCE_PACKET}}': json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) if condition == 'W' else canonical(packet).decode('utf-8')}
    # Single-pass insertion prevents a literal {{MANUAL}} in source text becoming an instruction/template.
    import re
    user = re.sub(r'\{\{(?:MANUAL_SHA256|MANUAL|OUTPUT_SCHEMA|SOURCE_PACKET)\}\}', lambda m: values[m.group()], user)
    envelope = {'system_text': system, 'user_text': user,
                'assets': [{k: a[k] for k in ('attachment_id', 'sha256', 'mime_type')} for a in assets]}
    return canonical(envelope)

def offline_prepare(packet, manifest, asset_root, manual_bytes, *, toy_amendment=False, condition='primary'):
    source = adapt(packet, toy_amendment=toy_amendment)
    if source['material_status'] != 'ready':
        raise ContractError('source preflight pending: no call and no semantic answer generated')
    assets = verify_assets(source, manifest, asset_root)
    raw = request_bytes(source, manual_bytes, assets, condition)
    return {'state': 'not_executed', 'actual_attempts': 0, 'condition': condition,
            'source_profile': 'toy_amendment_only' if toy_amendment else 'conservative_pending_common_freeze',
            'assigned_model': 'GPT-6.1 Sol', 'assigned_reasoning': 'ultra',
            'actual_model_identity': None, 'model_evidence_source': None,
            'source': source, 'assets': assets, 'manual_sha256': sha(manual_bytes),
            'packet_binding_sha256': sha(canonical(source)), 'request_bytes': raw}

def execute(prepared, destination, *, transport=None, freeze=None, purpose='production', simulation=False, expected_wire_request_bytes=None):
    """transport(bytes, assets) returns raw response, exact wire-body bytes, and observed receipt.

    Actual network code and provider parameter names are intentionally absent. Every call must
    create a fresh independent context; a verified facility must guarantee identity and isolation.
    """
    if purpose not in {'production', 'R1', 'R2', 'R3', 'W', 'H'}:
        raise ContractError('unregistered run purpose')
    expected_condition = purpose if purpose in {'W', 'H'} else 'primary'
    if prepared['condition'] != expected_condition:
        raise ContractError('purpose/request condition mismatch')
    dest = Path(destination).resolve()
    if not dest.is_relative_to(ROOT):
        raise ContractError('execution artifacts must stay inside protocol output directory')
    dest.mkdir(parents=True, exist_ok=False)
    state = {k: v for k, v in prepared.items() if k not in {'source', 'assets', 'request_bytes'}}
    state.update({'purpose': purpose, 'simulation': simulation, 'selected_attempt': None,
                  'semantic_result': None, 'attempts': [], 'simulated_attempts': 0})
    request = prepared['request_bytes']
    (dest / 'neutral-request.bin').write_bytes(request)
    state['neutral_request_sha256'] = sha(request)
    state['started_at'] = now()
    exclusive_json(dest / 'prepared-bindings.json', {'source': prepared['source'], 'verified_assets': prepared['assets']})
    if freeze is not None:
        exclusive_json(dest / 'freeze-evidence.json', freeze)
        state['freeze_evidence_sha256'] = sha(canonical(freeze))
    if transport is None:
        state.update({'state': 'not_executed', 'blocker': 'no registered actual model transport', 'ended_at': now()})
        exclusive_json(dest / 'run.json', state)
        return state
    if not simulation:
        if prepared['source_profile'] == 'toy_amendment_only':
            state.update({'state': 'not_executed', 'blocker': 'toy-only source amendment cannot enter real transport', 'ended_at': now()})
            exclusive_json(dest / 'run.json', state)
            return state
        required = ('common_manual_frozen', 'common_source_interface_frozen', 'source_reader_profile_frozen',
                    'source_manifest_frozen', 'prompt_schema_code_frozen', 'diagnostic_design_frozen',
                    'facility_identity_and_isolation_verified')
        if not freeze or any(freeze.get(k) is not True for k in required):
            state.update({'state': 'not_executed', 'blocker': 'required common/facility freeze pending', 'ended_at': now()})
            exclusive_json(dest / 'run.json', state)
            return state
        if not isinstance(freeze.get('actual_model_identity'), str) or not isinstance(freeze.get('actual_reasoning_configuration'), str):
            raise ContractError('actual identity must come from the verified facility mapping')
        expected = {'assigned_model': 'GPT-6.1 Sol', 'assigned_reasoning': 'ultra',
                    'blind_id': prepared['source']['blind_id'], 'packet_binding_sha256': prepared['packet_binding_sha256'],
                    'manual_sha256': prepared['manual_sha256'], 'neutral_request_sha256': sha(request),
                    'code_bundle_sha256': implementation_sha256()}
        if any(freeze.get(k) != v for k, v in expected.items()) or not freeze.get('facility_evidence_ref') or not freeze.get('source_manifest_evidence_ref'):
            state.update({'state': 'not_executed', 'blocker': 'freeze lacks assigned identity/source/request evidence binding', 'ended_at': now()})
            exclusive_json(dest / 'run.json', state)
            return state
        scheduling = freeze.get('scheduling', {})
        if not isinstance(scheduling, dict) or any(k not in scheduling for k in ('run_id', 'unit_sequence', 'batch_id', 'planned_order_sha256', 'batch_manifest_sha256')):
            state.update({'state': 'not_executed', 'blocker': 'freeze lacks preregistered order/batch binding', 'ended_at': now()})
            exclusive_json(dest / 'run.json', state)
            return state
        if not scheduling['run_id'] or not scheduling['batch_id'] or type(scheduling['unit_sequence']) is not int or scheduling['unit_sequence'] < 0 or any(not valid_sha(scheduling[k]) for k in ('planned_order_sha256', 'batch_manifest_sha256')):
            state.update({'state': 'not_executed', 'blocker': 'invalid/null preregistered order/batch binding', 'ended_at': now()})
            exclusive_json(dest / 'run.json', state)
            return state
        state['scheduling'] = scheduling
        if not isinstance(expected_wire_request_bytes, bytes) or freeze.get('wire_request_sha256') != sha(expected_wire_request_bytes):
            state.update({'state': 'not_executed', 'blocker': 'exact provider wire body must be sealed before any call', 'ended_at': now()})
            exclusive_json(dest / 'run.json', state)
            return state
    context_ids = set()
    wire = expected_wire_request_bytes if expected_wire_request_bytes is not None else request
    wire_hash = sha(wire)
    (dest / 'expected-wire-request.bin').write_bytes(wire)
    state['expected_wire_request_sha256'] = wire_hash
    for number in range(1, 4):
        attempt = {'attempt': number, 'started_at': now(), 'neutral_request_sha256': sha(request), 'selected': False}
        state['simulated_attempts' if simulation else 'actual_attempts'] += 1
        folder = dest / f'attempt-{number:02d}'
        folder.mkdir()
        try:
            result = transport(request, prepared['assets'])
        except Exception as exc:
            attempt.update({'outcome': 'transport_failure', 'error_type': type(exc).__name__, 'detail': str(exc)})
        else:
            # Seal all raw returned bytes before parsing or technical checking.
            if not isinstance(result, dict):
                attempt.update({'outcome': 'technical_invalid', 'detail': 'transport returned no structured byte/receipt envelope', 'returned_type': type(result).__name__})
                attempt['ended_at'] = now()
                exclusive_json(folder / 'attempt.json', attempt)
                state['attempts'].append(attempt)
                continue
            raw = result.get('raw_response')
            wire = result.get('wire_request_bytes')
            receipt = result.get('receipt')
            if isinstance(raw, bytes):
                (folder / 'raw-response.bin').write_bytes(raw)
                attempt['raw_response_sha256'] = sha(raw)
            if isinstance(wire, bytes):
                (folder / 'wire-request.bin').write_bytes(wire)
                attempt['wire_request_sha256'] = sha(wire)
            wire_changed = isinstance(wire, bytes) and wire_hash is not None and wire_hash != sha(wire)
            if isinstance(receipt, dict):
                exclusive_json(folder / 'receipt.json', receipt)
            try:
                if not isinstance(raw, bytes) or not isinstance(wire, bytes):
                    raise ContractError('transport must return exact response and credential-free wire body bytes')
                if wire_changed:
                    raise ProtocolViolation('technical retry changed exact wire body')
                schema_check(receipt, 'transport-receipt.schema.json')
                attempt['independent_context_id'] = receipt['context_id']
                attempt['receipt_sha256'] = sha(canonical(receipt))
                attempt['model_evidence_source'] = receipt['model_evidence_source']
                attempt['observed_model_identity'] = receipt['actual_model_identity']
                if not simulation and (receipt['actual_model_identity'] != freeze['actual_model_identity'] or receipt['actual_reasoning_configuration'] != freeze['actual_reasoning_configuration']):
                    raise ProtocolViolation('actual provider identity/configuration differs from frozen verified mapping')
                if receipt['context_id'] in context_ids:
                    raise ProtocolViolation('independent context identity reused')
                context_ids.add(receipt['context_id'])
                delivered = receipt['delivered_attachments']
                expected = [{'attachment_id': a['attachment_id'], 'sha256': a['sha256']} for a in prepared['assets']]
                if sorted(delivered, key=lambda a: a['attachment_id']) != sorted(expected, key=lambda a: a['attachment_id']):
                    raise ContractError('actual asset-delivery receipt differs from complete verified common material')
                response = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
                response = validate_response(response, prepared['source'], prepared['manual_sha256'], [a['attachment_id'] for a in delivered])
                exclusive_json(folder / 'validated-response.json', response)
                attempt.update({'outcome': 'technical_valid', 'selected': True})
                state.update({'selected_attempt': number, 'semantic_result': response,
                              'state': 'simulated_first_valid' if simulation else 'first_valid',
                              'actual_model_identity': None if simulation else receipt['actual_model_identity'],
                              'model_evidence_source': 'constructed_toy_transport' if simulation else receipt['model_evidence_source']})
            except ProtocolViolation as exc:
                attempt.update({'outcome': 'protocol_violation', 'detail': str(exc)})
                state['state'] = 'simulated_protocol_violation' if simulation else 'protocol_violation'
            except (ContractError, ValueError, TypeError, KeyError, UnicodeError) as exc:
                attempt.update({'outcome': 'technical_invalid', 'detail': str(exc)})
        attempt['ended_at'] = now()
        exclusive_json(folder / 'attempt.json', attempt)
        state['attempts'].append(attempt)
        if attempt['selected'] or attempt['outcome'] == 'protocol_violation':
            break
    if state['selected_attempt'] is None and state['state'] not in {'protocol_violation', 'simulated_protocol_violation'}:
        state['state'] = 'simulated_technical_failure' if simulation else 'technical_failure'
    state['ended_at'] = now()
    exclusive_json(dest / 'run.json', state)
    return state

def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ContractError('duplicate JSON response key')
        obj[key] = value
    return obj

def main():
    parser = argparse.ArgumentParser(description='Offline only; no model transport installed')
    parser.add_argument('--packet', required=True)
    parser.add_argument('--assets', required=True)
    parser.add_argument('--asset-root', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--condition', choices=['primary', 'W', 'H'], default='primary')
    parser.add_argument('--toy-amendment', action='store_true')
    args = parser.parse_args()
    packet = json.loads(Path(args.packet).read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    manifest = json.loads(Path(args.assets).read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    manual = (ROOT / 'snapshots/common-manual-v1.1-development.md').read_bytes()
    prepared = offline_prepare(packet, manifest, args.asset_root, manual, toy_amendment=args.toy_amendment, condition=args.condition)
    run = execute(prepared, args.destination, purpose=args.condition if args.condition != 'primary' else 'production')
    print(json.dumps({'state': run['state'], 'actual_attempts': run['actual_attempts'], 'model_calls': 0}, ensure_ascii=False))

if __name__ == '__main__':
    main()
