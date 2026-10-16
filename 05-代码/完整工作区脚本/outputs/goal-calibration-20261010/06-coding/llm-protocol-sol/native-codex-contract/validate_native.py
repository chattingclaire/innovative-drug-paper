"""Offline mechanical validation for the native batch variant, not a native executor."""
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from adapter import ContractError, canonical, sha, content_hash, validate_response

CONDITIONS = ('R1', 'R2', 'R3', 'W', 'H')
SHA_FIELDS = ('manual_sha256', 'source_manifest_sha256', 'unit_order_sha256', 'prompt_sha256')

def unique_object(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ContractError('duplicate JSON key')
        result[k] = v
    return result

def valid_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(x in '0123456789abcdef' for x in value)

def validate_batch(raw, sources, plan, visible_assets):
    if not isinstance(raw, bytes):
        raise ContractError('candidate must preserve original UTF-8 bytes')
    candidate = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    schema = json.loads((ROOT / 'native-output.schema.json').read_text(encoding='utf-8'))
    errors = list(Draft202012Validator(schema).iter_errors(candidate))
    if errors:
        raise ContractError(str(errors[0].message))
    ids = plan['ordered_ids']
    if not ids or plan['expected_n'] != len(ids) or len(ids) > 41 or len(set(ids)) != len(ids):
        raise ContractError('invalid frozen native batch plan')
    if sha(canonical(ids)) != plan['unit_order_sha256']:
        raise ContractError('frozen order hash mismatch')
    if any(not valid_sha(plan.get(k)) for k in SHA_FIELDS):
        raise ContractError('missing frozen input binding')
    for key in ('run_id', 'condition', 'batch_id') + SHA_FIELDS:
        if candidate[key] != plan[key]:
            raise ContractError('candidate identity/input binding mismatch')
    if [r['blind_id'] for r in candidate['items']] != ids:
        raise ContractError('batch rows missing/duplicated/extra/reordered')
    if set(sources) != set(ids) or set(visible_assets) != set(ids):
        raise ContractError('source/read evidence ID set differs from batch')
    expected_manifest = [{'blind_id': i, 'packet_binding_sha256': sha(canonical(sources[i]))} for i in ids]
    if sha(canonical(expected_manifest)) != plan['source_manifest_sha256']:
        raise ContractError('common source packet/CTX/structure binding changed')
    for row in candidate['items']:
        uid = row['blind_id']
        if sources[uid]['content_sha256'] != content_hash(sources[uid]):
            raise ContractError('common source content SHA does not match its declared version')
        expected_assets = {a['attachment_id'] for a in sources[uid].get('attachments', [])}
        if set(visible_assets[uid]) != expected_assets:
            raise ContractError('complete common asset visibility is unconfirmed')
        validate_response(row, sources[uid], plan['manual_sha256'], visible_assets[uid])
    return candidate

def select_first_valid(attempts, sources, plan, visible_assets):
    """Constructed/offline selector; does not create a thread or inspect real answers."""
    if len(attempts) > 3:
        raise ContractError('more than three preregistered technical attempts')
    seen_threads, checks = set(), []
    for number, attempt in enumerate(attempts, 1):
        check = {'attempt': number, 'selected': False, 'candidate_sha256': sha(attempt['raw']) if isinstance(attempt.get('raw'), bytes) else None}
        try:
            thread = attempt.get('thread_id')
            if not thread or thread in seen_threads or attempt.get('created_fresh') is not True:
                raise ContractError('native attempt must use a new logical thread with creation evidence')
            seen_threads.add(thread)
            if attempt.get('additional_user_messages') != [] or attempt.get('history_mode') != 'complete_batch_single_initial_prompt':
                raise ContractError('feedback/continuation or changed input history')
            if attempt.get('initial_prompt_sha256') != plan['prompt_sha256']:
                raise ContractError('technical retry prompt bytes changed')
            if any(attempt.get(k) is not False for k in ('known_context_compaction', 'known_input_truncation', 'known_output_truncation')) or attempt.get('visible_read_status') != 'complete':
                raise ContractError('visible read/output completeness not established; hidden telemetry remains unavailable')
            if attempt.get('candidate_sealed_before_check') is not True:
                raise ContractError('candidate must be sealed before technical checking')
            candidate = validate_batch(attempt.get('raw'), sources, plan, visible_assets)
            check.update({'state': 'format_valid', 'selected': True})
            checks.append(check)
            return {'state': 'first_format_valid', 'selected_attempt': number, 'candidate': candidate, 'checks': checks}
        except (ContractError, ValueError, TypeError, KeyError, UnicodeError) as exc:
            check.update({'state': 'technical_invalid', 'reason': str(exc)})
            checks.append(check)
    return {'state': 'not_executed' if not attempts else 'no_format_valid_batch', 'selected_attempt': None, 'candidate': None, 'checks': checks}

def validate_unavailable_telemetry(ledger):
    # Current facility has only native tool assignment. Non-null values require a new facility version.
    if any(v is not None for v in ledger['telemetry'].values()):
        raise ContractError('provider/parameter telemetry unavailable in this native variant')
    request = ledger['assignment']['requested_create_thread']
    if request != {'model': 'gpt-6.1-sol', 'thinking': 'ultra'}:
        raise ContractError('native assigned configuration differs')
    return True

def comparison_gate(sealed_conditions):
    if set(sealed_conditions) != set(CONDITIONS):
        raise ContractError('all preregistered conditions must complete selection/failure and seal before comparison')
    threads = set()
    for condition in CONDITIONS:
        record = sealed_conditions[condition]
        if record.get('state') not in {'first_format_valid_sealed', 'exhausted_technical_failure_sealed'} or any(not valid_sha(record.get(k)) for k in ('seal_sha256',) + SHA_FIELDS):
            raise ContractError('unsealed condition cannot unlock comparison')
        if record['state'] == 'first_format_valid_sealed' and (not record.get('attempt_thread_ids') or not valid_sha(record.get('selected_candidate_sha256'))):
            raise ContractError('selected native result lacks sealed candidate/thread evidence')
        for thread in record.get('attempt_thread_ids', []):
            if not thread or thread in threads:
                raise ContractError('diagnostic conditions reused a native thread')
            threads.add(thread)
    for key in ('manual_sha256', 'source_manifest_sha256', 'unit_order_sha256'):
        if len({sealed_conditions[c][key] for c in CONDITIONS}) != 1:
            raise ContractError('diagnostic common material/order binding differs')
    if len({sealed_conditions[c]['prompt_sha256'] for c in ('R1', 'R2', 'R3')}) != 1:
        raise ContractError('primary native prompt repeats are not byte-identical')
    return True
