#!/usr/bin/env python3
"""Read-only R1 first-artifact receiver. No dispatch, labels, or metrics."""
import argparse
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
FLAG_KEYS = ('known_input_truncation', 'known_output_truncation', 'known_compaction')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identify(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}


def parse(raw):
    def pairs(values):
        out = {}
        for key, value in values:
            if key in out:
                raise ValueError('duplicate JSON key: ' + key)
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))


def get(path):
    return parse(Path(path).read_bytes())


def need(value, reason):
    if not value:
        raise ValueError(reason)


def check(entry):
    actual = identify(entry.get('path', entry.get('absolute_path')))
    need(actual['sha256'] == entry['sha256'], 'SHA differs: ' + actual['path'])
    need(actual['bytes'] == entry['bytes'], 'bytes differ: ' + actual['path'])
    return actual


def at(value, pointer):
    if not pointer:
        return value
    need(pointer.startswith('/'), 'JSON Pointer must start with /')
    for token in pointer[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def field(value, path):
    # Relative RFC6901 or the original ordinary dot/index field notation.
    for prefix in ('source_bundle.source_record.', 'source_record.'):
        if path.startswith(prefix):
            path = path[len(prefix):]
    if path.startswith('/'):
        return at(value, path)
    tokens = re.findall(r'[^.\[\]]+', path)
    for token in tokens:
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def exact(value, quote, span):
    need(isinstance(value, str), 'anchor is not an original text leaf')
    start, end = span['start'], span['end']
    need(type(start) is int and type(end) is int and 0 <= start < end <= len(value)
         and value[start:end] == quote, 'non-continuous/original Unicode quote')


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def technical_facts(path, scheduling_root):
    """No default false. External observed facts must point to actual artifacts."""
    values = {key: None for key in (*FLAG_KEYS, 'additional_user_messages',
                                   'hidden_background_history', 'complete_platform_history')}
    bindings = []
    if not path:
        return values, bindings
    supplied = get(path)
    for key, proof in supplied.get('facts', {}).items():
        need(key in values, 'unsupported technical fact')
        if proof is None:
            continue
        artifact = check(proof['artifact'])
        p = Path(artifact['path'])
        need(p.is_relative_to(scheduling_root),
             'technical evidence must be ROOT external scheduling evidence, not actor self-attestation')
        observed = at(get(p), proof['json_pointer'])
        need(observed == proof['value'], 'technical fact differs from actual artifact')
        need(observed is None or type(observed) is bool or
             key == 'additional_user_messages' and isinstance(observed, list), 'technical fact type')
        values[key] = observed
        bindings.append({'fact': key, 'artifact': artifact, 'json_pointer': proof['json_pointer'],
                         'observed_value': observed})
    return values, bindings


def receive(args):
    PLAN=Path(args.plan).resolve(); PLAN_SHA=args.plan_sha
    NATIVE=Path(args.native_root).resolve(); HOME=Path(args.report_root).resolve()
    report = {'receiver_version': 'formal-frozen-native-R1-receiver-interface-1', 'condition': 'R1',
              'batch_id': args.batch, 'attempt': args.attempt, 'state': 'pending_actor_seal',
              'errors': [], 'pending': [], 'receipt': None, 'selection': None,
              'provider_wire_capacity_parameters': None, 'complete_platform_history': None,
              'all_batches_sealed_gate_called': False, 'RWH_five_conditions_complete': False,
              'semantic_or_performance_review': False}
    actor_seal = Path(args.actor_seal).resolve()
    if not actor_seal.is_file():
        report['pending'].append('actor seal absent; no partial actor member read')
        return report
    try:
        need(identify(PLAN)['sha256'] == PLAN_SHA, 'sealed plan-v2 changed')
        plan = get(PLAN)
        batch = next(b for b in plan['batches'] if b['batch_id'] == args.batch)
        need(1 <= args.attempt <= 3, 'at most three fresh same-byte technical attempts')
        report['input_plan'] = identify(PLAN)
        need(Path(plan['actor_attempt_root']).resolve() == NATIVE/'attempts','native root differs from sealed plan')
        if 'receiver_report_root' in plan:
            need(Path(plan['receiver_report_root']).resolve() == HOME,'receiver root differs from sealed plan')
        else:
            need(HOME == ROOT/'06-coding/root-machine-review/native77-v13-R1-receiver-sol','legacy receiver namespace differs')
        check(plan['common_actor_wrapper'])
        check(plan['v4_overlay_seal'])
        for binding in plan['v4_runtime_bindings'].values():
            check(binding)
        attempt_dir = actor_seal.parent
        need(attempt_dir.parent == NATIVE / 'attempts', 'actor attempt root differs')
        seal = get(actor_seal)
        entries = seal.get('files', seal.get('output_files'))
        need(isinstance(entries, list) and entries, 'actor seal has no complete member manifest')
        members = {}
        for entry in entries:
            path = Path(entry.get('path', entry.get('absolute_path'))).resolve()
            need(path.is_relative_to(attempt_dir) and path != actor_seal and path not in members,
                 'actor member escaped/repeated or seal self-included')
            members[path] = check(entry)
        actual = {p.resolve() for p in attempt_dir.rglob('*') if p.is_file() and p.resolve() != actor_seal}
        need(actual == set(members), 'actor directory has unsealed/missing members; no partial read')
        report['actor_seal'] = identify(actor_seal)
        report['actor_member_count'] = len(members)

        def saved(name):
            path = attempt_dir / name
            need(path in members, 'required member not sealed: ' + name)
            return path

        request_path, return_path = Path(args.creation_request).resolve(), Path(args.creation_return).resolve()
        scheduling_root = Path(args.scheduling_root).resolve()
        need(scheduling_root in tuple(Path(p).resolve() for p in plan.get('authorized_scheduling_roots', [str(NATIVE / 'scheduling'), str(NATIVE / 'bootstrap-scheduling-v1')])),
             'unsupported actual scheduling root')
        need(request_path.is_relative_to(scheduling_root) and return_path.is_relative_to(scheduling_root),
             'creation artifacts must be actual scheduling records')
        request = at(get(request_path), args.request_pointer)
        returned = at(get(return_path), args.return_pointer)
        thread = at(returned, args.thread_pointer)
        need(str(uuid.UUID(thread)) == thread and attempt_dir.name == thread, 'create return/attempt UUID differs')
        need(request['model'] == 'gpt-6.1-sol' and request['thinking'] == 'ultra', 'actual create allocation differs')
        actual_prompt_sha = digest(request['prompt'].encode())
        if args.initial_prompt_file:
            launcher = identify(args.initial_prompt_file)
            need(args.initial_prompt_sha and launcher['sha256'] == args.initial_prompt_sha == actual_prompt_sha,
                 'actual create request differs from frozen bootstrap launcher')
            need(launcher['bytes'] <= 4000 and launcher['bytes'] == len(request['prompt'].encode()),
                 'bootstrap actual initial prompt exceeds4000 bytes or differs')
            need(scheduling_root in tuple(Path(p).resolve() for p in plan.get('authorized_short_scheduling_roots', [str(NATIVE / 'bootstrap-scheduling-v1')])), 'short dispatch namespace differs')
            need(args.original_instruction_file, 'bootstrap must bind original long R+wrapper material separately')
            original_instruction = identify(args.original_instruction_file)
            need(original_instruction['sha256'] == batch['actual_initial_prompt']['sha256'],
                 'bootstrap original R+wrapper material changed')
            report['dispatch_variant'] = 'shortbootstrap-v1'
            report['actual_initial_prompt'] = launcher
            report['original_instructions'] = original_instruction
            report['original_instructions_actual_read_status'] = None
        else:
            need(actual_prompt_sha == batch['actual_initial_prompt']['sha256'], 'actual create prompt differs')
            report['dispatch_variant'] = 'legacy-long-v2-administratively-stopped'
            report['actual_initial_prompt'] = {'sha256': actual_prompt_sha, 'bytes': len(request['prompt'].encode()),
                                               'path': str(request_path), 'field': args.request_pointer + '/prompt'}
            report['pending'].append('legacy seven first attempts administratively stopped; do not select complete_valid')
        identity_path = saved('identity.json')
        runtime = at(get(identity_path), args.runtime_pointer)
        need(runtime == thread and str(uuid.UUID(runtime)) == runtime, 'threadId does not match recorded runtime UUID')
        if args.runtime_evidence_member:
            evidence_path = saved(args.runtime_evidence_member)
            observed_runtime = at(get(evidence_path), args.runtime_evidence_pointer)
            if isinstance(observed_runtime, str):
                observed_runtime = observed_runtime.rstrip('\r\n')
            need(observed_runtime == runtime, 'actual sealed runtime-tool return differs')
            report['runtime_tool_evidence'] = members[evidence_path]
        else:
            report['pending'].append('actual runtime-tool return evidence unconfirmed; identity string alone is not authentication')
        report['creation_evidence'] = {'request': identify(request_path), 'return': identify(return_path),
                                       'thread_id': thread, 'identity': members[identity_path],
                                       'runtime_pointer': args.runtime_pointer, 'runtime_matches_actual_create_return': True}
        report['history'] = members[saved('history.json')]
        report['actor_status'] = members[saved('actor-status.json')]

        # Import sealed v4 in this new process, never an existing module cache.
        v4 = Path(plan['v4_runtime_bindings']['native_records.py']['path']).parent
        sys.path.insert(0, str(v4))
        import necessary_read_gate as gate
        bound = check(plan['v4_runtime_bindings']['native-binding.json'])
        need(Path(args.runtime_binding).resolve() == Path(bound['path']).resolve() and args.runtime_binding_sha == bound['sha256'], 'runtime binding must equal actual sealed plan binding')
        if hasattr(gate,'configure'):
            gate.configure(args.runtime_binding,args.runtime_binding_sha)
            if 'source_interface_version' in gate.BINDING:
                for plan_key,runtime_key in [('manual_v1_3','manual'),('output_item_schema','output_item_schema'),
                                             ('public_source_quote_schema','public_source_quote_schema'),
                                             ('necessary_scope_schema','necessary_scope_schema')]:
                    actual=check(plan[plan_key]); expected=check(gate.BINDING[runtime_key])
                    need(actual==expected,'plan/runtime actual binding differs: '+plan_key)
        else:
            need(gate.BINDING_PATH.resolve() == Path(args.runtime_binding).resolve() and gate._pb.file_sha(gate.BINDING_PATH) == args.runtime_binding_sha,'legacy fixed binding differs')
        import native_records as records
        need(Path(records.__file__).resolve() == Path(plan['v4_runtime_bindings']['native_records.py']['path']).resolve(), 'loaded native_records path differs')
        need(Path(gate.__file__).resolve() == Path(plan['v4_runtime_bindings']['necessary_read_gate.py']['path']).resolve(), 'loaded gate path differs')
        pb = gate._pb
        schema = get(check(plan['output_item_schema'])['path'])
        public_schema = get(check(plan['public_source_quote_schema'])['path'])
        packets = []
        for binding in batch['externally_frozen_packet_file_bindings']:
            check(binding)
            packet = get(binding['path'])
            need(packet['source_id'] == binding['source_id'] and packet['source_bundle_sha256'] == binding['source_bundle_sha256'],
                 'frozen packet source binding differs')
            packets.append(packet)
        whole_path = saved('whole-output.json')
        whole = get(whole_path)
        need(set(whole) == {'items'} and len(whole['items']) == len(packets), 'whole ordered candidate incomplete')
        format_errors = []
        for packet, item in zip(packets, whole['items']):
            first_path = saved('first-output/' + packet['source_id'] + '.json')
            need(get(first_path) == item, 'first item differs from whole.items or order')
            need(item['blind_id'] == packet['output_id'] and item['content_sha256'] == packet['source_bundle_sha256'], 'ordered item binding differs')
            need(item['manual_sha256'] == plan['manual_v1_3']['sha256'], 'manual differs')
            try:
                pb.schema_check(item, schema)
                row = packet['source_bundle']['source_record']
                context = {c['context_id']: c for c in row['contexts']}
                for evidence in item['evidence'].values():
                    need(evidence['current_quote'] == row['text'] and evidence['current_span'] == {'start': 0, 'end': len(row['text'])}, 'full current quote/span differs')
                    for anchor in walk(evidence):
                        if {'quote', 'span', 'field_path', 'context_id'} <= set(anchor):
                            current = anchor.get('source_kind') == 'current'
                            if current:
                                need(anchor['context_id'] is None, 'current anchor has a context id')
                            else:
                                need(anchor['context_id'] in context, 'invented/non-original CTX')
                            exact(field(row if current else context[anchor['context_id']], anchor['field_path']), anchor['quote'], anchor['span'])
                    need(set(evidence['structural_context_ids_used']) <= set(context), 'unknown structural CTX')
            except Exception as exc:
                format_errors.append({'source_id': packet['source_id'], 'error': str(exc)})
        packet_map = {p['source_id']: p for p in packets}
        public_quote_N = 0
        for path in members:
            if path.suffix != '.json' or path.name in ('whole-output.json',):
                continue
            for anchor in walk(get(path)):
                if {'bundle_pointer', 'quote', 'span'} <= set(anchor):
                    try:
                        pb.schema_check(anchor, public_schema)
                        pb.verify_source_quote(packet_map[anchor['source_id']], anchor)
                        public_quote_N += 1
                    except Exception as exc:
                        format_errors.append({'file': str(path), 'error': str(exc)})
        report['format'] = {'errors': format_errors, 'public_quote_count': public_quote_N,
                             'saved_actor_format_check': members[saved('format-check.json')],
                             'first_whole_objects_and_order_equal': True}
        actor_status = get(attempt_dir / 'actor-status.json')
        representation = actor_status.get('state', actor_status.get('status')) == 'technical_representation_failed'
        representation = representation or any('innovation_support' in e['error'] and
                                                ('source_kind' in e['error'] or 'public' in e['error']) for e in format_errors)
        report['terminal_schema_representation_failure'] = representation
        scope_path = saved('scope-manifest.json')
        saved_check = saved('scope-check.json')
        check_values = get(saved_check)
        need(isinstance(check_values, list), 'scope-check must preserve actual gate list')
        if hasattr(gate,'configure') and 'attempt_record_blank' in gate.BINDING:
            receipt = get(check(gate.BINDING['attempt_record_blank'])['path'])
        else:
            receipt = get(Path(plan['v4_runtime_bindings']['native-binding.json']['path']).parent.parent /
                          'protocol-necessary-read-v3/attempt-record.blank.json')
        receipt.update(condition='R1', batch_id=args.batch, attempt=args.attempt,
                       initial_prompt_sha256=actual_prompt_sha,
                       creation_request_artifact_sha256=identify(request_path)['sha256'],
                       creation_return_artifact_sha256=identify(return_path)['sha256'],
                       thread_id=thread, host_id=returned.get('hostId'), fresh_thread=True,
                       candidate_sha256=members[whole_path]['sha256'], candidate_seal_sha256=identify(actor_seal)['sha256'],
                       format_check_artifact_sha256=report['format']['saved_actor_format_check']['sha256'],
                       read_log_file=str(scope_path), read_log_sha256=members[scope_path]['sha256'],
                       history_log_sha256=report['history']['sha256'], candidate_file=str(whole_path),
                       scope_check_file=str(saved_check), scope_check_sha256=members[saved_check]['sha256'],
                       required_read_complete=all(r['required_read_complete'] for r in check_values), scope_run_id=thread)
        receipt['candidate_is_assembled_from_multiple_attempts'] = False
        receipt['candidate_piece_attempts'] = []
        receipt['additional_user_messages'] = None  # blank [] is not execution evidence
        results = records.check_saved_scopes(receipt, batch['externally_frozen_packet_file_bindings'])
        report['scope_recomputed_matches_actual_saved_list'] = True
        report['scope_results'] = results
        facts, proof = technical_facts(args.technical_evidence, scheduling_root)
        receipt.update({k: facts[k] for k in (*FLAG_KEYS, 'additional_user_messages', 'hidden_background_history')})
        report['complete_platform_history'] = facts['complete_platform_history']
        report['external_technical_evidence'] = proof
        receipt['state'] = 'format_failed' if format_errors or representation else 'complete_format_valid'
        report['terminal_schema_representation_failure'] = representation
        if facts['known_input_truncation'] is True:
            receipt['state'] = 'input_truncated'
        elif facts['known_output_truncation'] is True:
            receipt['state'] = 'output_interrupted'
        elif facts['known_compaction'] is True:
            receipt['state'] = 'known_compaction'
        prior = []
        for path in args.prior_report:
            path = Path(path).resolve()
            need(path.is_relative_to(HOME), 'prior report must be receiver-owned')
            for entry in get(str(path) + '.seal.json')['files']:
                check(entry)
            old = get(path)
            need(old['batch_id'] == args.batch and old['receipt'] is not None, 'different/pending prior attempt')
            prior.append(old['receipt'])
        need(args.attempt == len(prior) + 1, 'retain all previous technical attempts in order')
        need(all(r['thread_id'] != thread for r in prior), 'technical retry must be fresh')
        report['receipt'] = receipt
        if receipt['additional_user_messages'] != []:
            report['pending'].append('actual frozen user-message history unconfirmed')
        if receipt['state'] == 'complete_format_valid' and not all(facts[k] is False for k in FLAG_KEYS):
            report['pending'].append('known truncation/compaction false lacks actual technical evidence')
        if report['pending']:
            report['state'] = 'selection_pending_technical_evidence'
        else:
            report['selection'] = records.select_technical_receipts(prior + [receipt], actual_prompt_sha, batch['externally_frozen_packet_file_bindings'])
            report['state'] = report['selection']['state']
        report['retry_policy'] = {'max_attempts': 3, 'automatic_retry': False,
                                  'lawful_null_retry': False, 'pending_evidence_retry': False,
                                  'same_prompt_fresh_thread_only': True,
                                  'terminal_no_retry': representation,
                                  'confirmed_technical_failure_only': True}
    except Exception as exc:
        report['state'] = 'format_failed' if report.get('terminal_schema_representation_failure') else 'mechanical_check_failed'
        report['errors'].append({'type': type(exc).__name__, 'reason': str(exc)})
        report['automatic_retry'] = False
        if report.get('terminal_schema_representation_failure'):
            report['retry_policy'] = {'terminal_no_retry': True, 'automatic_retry': False}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('actor-seal', 'batch', 'creation-request', 'creation-return', 'report'):
        parser.add_argument('--' + option, required=True)
    parser.add_argument('--attempt', type=int, required=True)
    parser.add_argument('--request-pointer', default='')
    parser.add_argument('--return-pointer', default='')
    parser.add_argument('--thread-pointer', default='/threadId')
    parser.add_argument('--runtime-pointer', default='/runtime_uuid')
    parser.add_argument('--technical-evidence')
    parser.add_argument('--scheduling-root',required=True)
    for key in ('plan','plan-sha','native-root','report-root','runtime-binding','runtime-binding-sha'):
        parser.add_argument('--'+key,required=True)
    parser.add_argument('--initial-prompt-file')
    parser.add_argument('--initial-prompt-sha')
    parser.add_argument('--original-instruction-file')
    parser.add_argument('--runtime-evidence-member')
    parser.add_argument('--runtime-evidence-pointer', default='')
    parser.add_argument('--prior-report', action='append', default=[])
    args = parser.parse_args()
    destination = Path(args.report).resolve()
    need(destination.is_relative_to(Path(args.report_root).resolve()), 'report must remain receiver-owned')
    need(not destination.exists() and not Path(str(destination) + '.seal.json').exists(), 'receiver report is immutable')
    result = receive(args)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
    output_seal = {'files': [identify(destination)], 'actor_outputs_changed': False,
                   'R1_only': True, 'performance_calculated': False}
    with Path(str(destination) + '.seal.json').open('xb') as stream:
        stream.write((json.dumps(output_seal, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps({'report': identify(destination), 'state': result['state']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
