"""Current frozen machine projection; no classifier, reception, selection or statistics.

The caller must first pass its independently reviewed real registration gate.
This module proves only machine/source projection integrity, never human truth.
No project data is opened on import. TOY fixtures use the same projection checks.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

DIMS = ('S', 'E', 'Ec', 'I', 'F')
REAL_FREEZE_SHA = 'f6e2e2d08a4f4c448ea1bd8b1b07c51cc95b5f7d2eb35dd0c371fd6d1a961b80'
REAL_VERIFIER_SHA = '5242cf6f634f1cdcf6ad4973a2f99847e3d271c4d809e8768c13836d4536058a'
REAL_SCHEMA = 'current4481-adopted-machine-evidence-freeze-v1'
TOY_SCHEMA = 'TOY-current-machine-projection-freeze-v1'


class ProjectionError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ProjectionError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    path = Path(path).resolve()
    sha = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            sha.update(block)
            size += len(block)
    return {'path': str(path), 'bytes': size, 'sha256': sha.hexdigest()}


def core_binding(value):
    require(isinstance(value, dict) and {'path', 'bytes', 'sha256'} <= set(value),
            'Missing exact byte binding')
    return {k: value[k] for k in ('path', 'bytes', 'sha256')}


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ProjectionError('Nonfinite JSON')))


def unique(rows, key, expected_ids=None):
    result = {}
    for row in rows:
        rid = row.get(key)
        require(isinstance(rid, str) and rid and rid not in result, 'Missing/duplicate record ID')
        result[rid] = row
    if expected_ids is not None:
        require(list(result) == expected_ids, 'Actual full-frame count/order/IDs differ')
    return result


def checked_labels(row, decision_key):
    labels = row.get('labels')
    require(isinstance(labels, dict) and set(labels) == set(DIMS), 'Five explicit machine values required')
    require(set(row.get(decision_key, {})) == set(DIMS), 'Five original decisions required')
    for dim in DIMS:
        val = labels[dim]
        require(val is None or type(val) is int and val in (0, 1), 'Machine value must be int0/int1/NULL')
        decision = row[decision_key][dim]
        require(isinstance(decision, dict) and 'value' in decision and
                type(decision['value']) is type(val) and decision['value'] == val,
                'Machine value differs from original decision')
    return {'status': 'completed', 'labels': {d: labels[d] for d in DIMS}}


def project_machines(machine_freeze_binding, full_frame_ids, *, synthetic=False, synthetic_sources=None):
    """Return full-frame rule/LLM core outputs and immutable-source provenance.

    Real input is pinned to the already adopted freeze. All its evidence bytes
    must still match; this reuses its original-first and material equality proof
    without rerunning semantic validators or parsing policy materials.

    TOY: synthetic_sources={'directory': <fixture root>}; every bound path must
    stay inside that root and every frame ID must begin TOY-. make_synthetic_fixture
    returns exactly the three keyword arguments for a synthetic call.
    """
    require(type(synthetic) is bool, 'Explicit boolean synthetic mode required')
    require(isinstance(full_frame_ids, list) and full_frame_ids and
            all(isinstance(i, str) and i for i in full_frame_ids) and
            len(full_frame_ids) == len(set(full_frame_ids)), 'Unique complete ordered frame required')
    require(all(i.startswith('TOY-') == synthetic for i in full_frame_ids), 'TOY/project IDs cannot mix')
    toy_root = None
    if synthetic:
        require(isinstance(synthetic_sources, dict) and set(synthetic_sources) == {'directory'}, 'TOY root required')
        toy_root = Path(synthetic_sources['directory']).resolve()
    else:
        require(synthetic_sources is None and len(full_frame_ids) == 4481, 'Real projection requires complete4481')
        require(machine_freeze_binding.get('sha256') == REAL_FREEZE_SHA, 'Unadopted current machine freeze')

    def exact(spec):
        b = core_binding(spec)
        path = Path(b['path'])
        require(path.is_absolute(), 'Absolute evidence path required')
        if toy_root is not None:
            require(path.resolve().is_relative_to(toy_root), 'TOY input escapes fixture directory')
        require(binding(path) == b, 'Bound machine evidence changed')
        return path

    freeze = strict(exact(machine_freeze_binding).read_bytes())
    require(freeze.get('schema') == (TOY_SCHEMA if synthetic else REAL_SCHEMA), 'Wrong machine freeze schema')
    if not synthetic:
        require(freeze['verifier']['sha256'] == REAL_VERIFIER_SHA, 'Original machine verifier changed')
        exact(freeze['verifier'])
    inventory = {}
    for item in freeze['file_bindings']:
        b = core_binding(item)
        require(b['path'] not in inventory, 'Duplicate evidence inventory path')
        exact(b)
        inventory[b['path']] = b
    require(inventory and (synthetic or len(inventory) == 11689), 'Incomplete frozen provenance inventory')

    def retained(spec):
        b = core_binding(spec)
        require(inventory.get(b['path']) == b, 'Source absent from adopted complete evidence inventory')
        return Path(b['path'])

    def document(spec):
        return strict(retained(spec).read_bytes())

    def stream(spec):
        with retained(spec).open('rb') as handle:
            for raw in handle:
                require(bool(raw.strip()), 'Blank machine record line')
                yield strict(raw), raw

    inputs, checks = freeze['inputs'], freeze['structural_check_results']
    N = len(full_frame_ids)
    frame = document(inputs['frame_ids'])
    require(frame['approved_record_ids'] == full_frame_ids and
            frame['frame_order_UTF8_LF_sha256'] == digest(('\n'.join(full_frame_ids) + '\n').encode()),
            'Approved full frame/order changed')
    require(checks['frame_N'] == N and checks['slots_per_method_N'] == 5*N and
            checks['rule_record_N'] == checks['LLM_record_N'] == N and
            checks['rule_unresolved_technical_slot_N'] == checks['LLM_missing_slot_N'] == 0 and
            checks['current_material_verified_packet_N'] == N and
            checks['rule_material_mismatch_N'] == checks['LLM_material_mismatch_N'] == 0 and
            checks['adopted_source_alignment_reproduced'] is True, 'Current terminal/material proof absent')
    rs, coverage = document(inputs['rule_status']), document(inputs['LLM_coverage'])
    require(rs['actual_record_N'] == N and rs['actual_dimension_N'] == N*5 and
            rs['technical_failure_dimension_N'] == rs['unresolved_technical_dimension_N'] == 0,
            'Current rule run is incomplete/failed')
    require(rs['prediction_binding'] == inputs['rule_predictions'] and
            rs['label_slots_binding'] == inputs['rule_dimension_slots'] and
            rs['source_common_v16'] == inputs['current_common_source'], 'Current rule source/version differs')
    require(coverage['full_corpus_complete'] is True and
            coverage['allocated_record_N'] == coverage['selected_record_N'] == N and
            coverage['missing_record_N'] == coverage['missing_label_N'] == 0 and
            coverage['selection_by_semantic_metric'] is False and coverage['first_values_changed'] is False,
            'Current LLM complete unselected-by-score terminal proof absent')
    alignment = document(inputs['source_alignment'])
    require(alignment['native_material_aligned_record_N'] == N and
            alignment['native_material_mismatch_N'] == 0, 'Current material alignment absent')
    packets = unique(document(inputs['current_packet_metadata']), 'source_id', full_frame_ids)
    for packet in packets.values():
        retained(packet)
    batches = document(inputs['LLM_batches'])
    batchby = unique(batches, 'batch_id')
    require(len(batches) == checks['LLM_whole_batch_N'] == coverage['allocated_batch_N'] ==
            coverage['selected_batch_N'] and [i for b in batches for i in b['source_ids']] == full_frame_ids,
            'Every original whole batch must be present exactly once')
    owner, attempts = {}, {}
    for b in batches:
        sid = b['batch_id']
        selection, receipt = document(b['selection']), document(b['receipt'])
        require(receipt.get('state') == 'technical_valid_whole_batch' and
                receipt['batch_id'] == selection['batch_id'] == sid and
                receipt['run_id'] == selection['run_id'], 'Nonterminal or mismatched whole-batch receipt')
        if b['selected_mode'] == 'original':
            require(selection['cross_attempt_record_combination'] is False and
                    selection['label_based_selection'] is False and
                    selection['all_actual_attempts_retained'] is True and
                    selection['legal_null_is_terminal_valid'] is True,
                    'Original whole-first selection policy changed')
            first, rec = selection['original_whole_batch_first'], selection['technical_reception']
            attempt = selection['selected_attempt_number']
            require(receipt['attempt_number'] == attempt, 'Original attempt mismatch')
        else:
            require(b['selected_mode'] in ('transport_recovery', 'new_actual_v16_material_whole_batch0216'),
                    'Unknown actual LLM selection mode')
            require(selection['semantic_scores_not_selection_criteria'] is True and
                    receipt['reference_compared'] is False and receipt['first_or_labels_modified'] is False,
                    'Recovery/delta source or selection policy changed')
            first, rec = selection['first'], selection['reception']
            attempt = selection['attempt']
            require(receipt['attempt'] == attempt and receipt['first'] == first, 'Recovery/delta attempt mismatch')
        require(type(attempt) is int and 1 <= attempt <= 3 and first == b['first'] and rec == b['receipt'],
                'Whole-first receipt/source binding mismatch')
        retained(first)
        attempts[sid] = attempt
        for rid in b['source_ids']:
            require(rid not in owner, 'Duplicate whole-batch member')
            owner[rid] = b
    # Only after all full-frame terminal metadata and immutable evidence checks.
    original_native = {}
    for b in batches:
        first = document(b['first'])
        require(first['manual_binding'] == inputs['common_manual'] and
                first['execution_prompt_binding'] == inputs['common_execution_prompt'],
                'Actual whole first uses another manual or prompt')
        originals = unique(first['records'], 'source_id', b['source_ids'])
        for rid, original in originals.items():
            require(rid not in original_native, 'Duplicate original whole-first member')
            original_native[rid] = original
    rule_rows, linehash = [], {}
    for row, raw in stream(inputs['rule_predictions']):
        rule_rows.append(row)
        require(row.get('id') not in linehash, 'Duplicate rule prediction ID')
        linehash[row['id']] = (digest(raw), len(raw))
    ruleby = unique(rule_rows, 'id', full_frame_ids)
    rule = {rid: checked_labels(row, 'decisions') for rid, row in ruleby.items()}
    lineage = unique((r for r, raw in stream(inputs['rule_execution_lineage'])), 'id', full_frame_ids)
    for rid, origin in lineage.items():
        require((origin['actual_prediction_line_sha256'], origin['prediction_line_bytes']) == linehash[rid],
                'Rule current row differs from sealed origin')
        if not origin['unchanged_actual_record_bytes_retained']:
            require((synthetic or rid == 'RECODE25-01402') and
                    origin['new_semantic_execution'] is False and origin['original_first_failure_preserved'] is True,
                    'Unexpected unpreserved rule original')
    seen = set()
    for row, raw in stream(inputs['rule_dimension_slots']):
        key = (row.get('id'), row.get('dimension'))
        require(key not in seen and key[0] in rule and key[1] in DIMS, 'Duplicate/unknown rule dimension slot')
        seen.add(key)
        rid, dim = key
        val = rule[rid]['labels'][dim]
        require(row['rule_executed'] is True and row['technical_failure'] is False and
                type(row['rule_value']) is type(val) and row['rule_value'] == val and
                row['rules_null'] is (val is None) and
                row['source_bundle_sha256'] == packets[rid]['source_bundle_sha256'],
                'Current slot failure/NULL/value/material differs')
    require(len(seen) == N*5, 'Incomplete rule dimension slots')
    native = unique((r for r, raw in stream(inputs['LLM_records'])), 'id', full_frame_ids)
    llm = {}
    modes = Counter()
    for rid, row in native.items():
        b = owner[rid]
        require(row['original_batch_id'] == b['batch_id'] and row['selected_mode'] == b['selected_mode'] and
                row['selected_attempt_number'] == attempts[b['batch_id']] and
                row['first'] == b['first'] and row['selection'] == b['selection'] and
                row['technical_receipt'] == b['receipt'], 'LLM record does not retain its whole-first provenance')
        for key in ('packet', 'first', 'selection', 'technical_receipt', 'actor_seal'):
            retained(row[key])
        require((row['packet']['bytes'], row['packet']['sha256']) ==
                (packets[rid]['bytes'], packets[rid]['sha256']), 'LLM/current material bytes differ')
        llm[rid] = checked_labels(row, 'dimensions')
        original = original_native[rid]
        require(original['packet_sha256'] == row['packet']['sha256'] and
                set(original['dimensions']) == set(DIMS), 'Original first packet/dimensions differ')
        for dim in DIMS:
            require('value' in original['dimensions'][dim] and
                    type(original['dimensions'][dim]['value']) is type(row['labels'][dim]) and
                    original['dimensions'][dim]['value'] == row['labels'][dim],
                    'LLM projection differs from actual whole-first value')
        modes[row['selected_mode']] += 1
    counts = {}
    for name, outputs in [('rule', rule), ('LLM', llm)]:
        dims = {}
        for dim in DIMS:
            c = Counter(outputs[i]['labels'][dim] for i in full_frame_ids)
            dims[dim] = {'positive_N': c[1], 'negative_N': c[0], 'lawful_null_N': c[None]}
        expected = rs['counts'] if name == 'rule' else {
            d: {k: v for k, v in coverage['per_dimension'][d].items() if k != 'missing_N'} for d in DIMS}
        require(dims == expected, 'Actual projected label counts differ from frozen complete coverage')
        nulls = sum(c['lawful_null_N'] for c in dims.values())
        require(nulls == checks['rule_lawful_null_N' if name == 'rule' else 'LLM_lawful_null_N'],
                'Actual lawful NULL count changed')
        counts[name] = {'completed_record_N': N, 'lawful_null_slot_N': nulls, 'execution_failure_slot_N': 0}
    require(dict(modes) == checks['LLM_actual_record_modes'], 'Actual mixed LLM provenance count differs')
    return {'rule': rule, 'LLM': llm, 'provenance': {
        'synthetic_only': synthetic, 'machine_freeze': core_binding(machine_freeze_binding),
        'frozen_evidence_binding_N': len(inventory), 'full_frame_N': N, 'whole_batch_N': len(batches),
        'counts': counts, 'rule_lineage': inputs['rule_execution_lineage'],
        'LLM_whole_batch_inventory': inputs['LLM_batches'], 'current_materials': inputs['current_packet_metadata'],
        'rule_original_historical_failed_slots_retained_N': checks['rule_original_v11_failed_slots_retained_N'],
        'historical_failures_not_relabelled_as_current_failure': True,
        'source_proof_policy': 'Exact reuse of adopted original-first/material proof plus all its unchanged evidence bytes; no new semantic adjudication',
        'actual_selection_or_reception_performed': False, 'human_or_accuracy_verified': False,
        'statistical_execution_authorized': False,
        'original_output_bindings': {'rule': core_binding(inputs['rule_predictions']),
                                     'LLM': core_binding(inputs['LLM_records'])},
        'projection_sha256': {m: digest(canonical([{'unit_id': i, 'output': o[i]} for i in sorted(o)]))
                              for m, o in [('rule', rule), ('LLM', llm)]}}}


def make_synthetic_fixture(directory, full_frame_ids):
    """Write finite TOY-only files; return project_machines keyword arguments.

    No project file is opened. One TOY whole batch, alternating0/1 and one lawful
    NULL per method, with a retained historical failure distinct from current state.
    Intended only for the handoff author's end-to-end synthetic controls.
    """
    require(isinstance(full_frame_ids, list) and len(full_frame_ids) >= 2 and
            len(full_frame_ids) == len(set(full_frame_ids)) and
            all(isinstance(i, str) and i.startswith('TOY-') for i in full_frame_ids), 'TOY-only full frame required')
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    files = []
    def save(name, value, lines=False):
        raw = (b''.join(canonical(v)+b'\n' for v in value) if lines else canonical(value)+b'\n')
        path = root/name
        with path.open('xb') as stream:
            stream.write(raw)
        b = binding(path)
        files.append(b)
        return b
    N = len(full_frame_ids)
    manual = save('TOY-manual.json', {'synthetic_only': True})
    prompt = save('TOY-prompt.json', {'synthetic_only': True})
    common = save('TOY-common.json', {'synthetic_only': True})
    frame = save('TOY-frame.json', {'approved_record_ids': full_frame_ids,
                 'frame_order_UTF8_LF_sha256': digest(('\n'.join(full_frame_ids)+'\n').encode())})
    packets = []
    rules, native_labels, slots, lineage = [], {}, [], []
    for n, rid in enumerate(full_frame_ids):
        packet = save(f'TOY-packet-{n}.json', {'source_id': rid, 'synthetic_only': True})
        packet = {**packet, 'source_id': rid, 'source_bundle_sha256': digest(canonical({'TOY': rid}))}
        packets.append(packet)
        labels = {d: (n+j) % 2 for j, d in enumerate(DIMS)}
        if n == 0:
            labels['F'] = None
        row = {'id': rid, 'labels': labels, 'decisions': {d: {'value': v} for d, v in labels.items()}}
        rules.append(row)
        native_labels[rid] = {**labels, 'S': 1-labels['S']}
        raw = canonical(row)+b'\n'
        origin = {'id': rid, 'actual_prediction_line_sha256': digest(raw), 'prediction_line_bytes': len(raw),
                  'unchanged_actual_record_bytes_retained': n != 0}
        if n == 0:
            origin.update(new_semantic_execution=False, original_first_failure_preserved=True)
        lineage.append(origin)
        for d, v in labels.items():
            slots.append({'id': rid, 'dimension': d, 'rule_executed': True, 'technical_failure': False,
                          'rule_value': v, 'rules_null': v is None, 'source_bundle_sha256': packet['source_bundle_sha256']})
    rp = save('TOY-rule.jsonl', rules, True)
    sp = save('TOY-slots.jsonl', slots, True)
    lp = save('TOY-lineage.jsonl', lineage, True)
    first = save('TOY-first.json', {'synthetic_only': True, 'manual_binding': manual,
        'execution_prompt_binding': prompt,
        'records': [{'source_id': rid, 'packet_sha256': packet['sha256'],
                     'dimensions': {d: {'value': v} for d, v in native_labels[rid].items()}}
                    for rid, packet in zip(full_frame_ids, packets)]})
    actor = save('TOY-actor.json', {'synthetic_only': True})
    receipt = save('TOY-receipt.json', {'state': 'technical_valid_whole_batch', 'batch_id': 'TOY-batch',
                                      'run_id': 'TOY-run', 'attempt_number': 1})
    selection = save('TOY-selection.json', {'batch_id': 'TOY-batch', 'run_id': 'TOY-run',
        'selected_attempt_number': 1, 'original_whole_batch_first': first, 'technical_reception': receipt,
        'cross_attempt_record_combination': False, 'label_based_selection': False,
        'all_actual_attempts_retained': True, 'legal_null_is_terminal_valid': True})
    batch = {'batch_id': 'TOY-batch', 'selected_mode': 'original', 'source_ids': full_frame_ids,
             'selection': selection, 'first': first, 'receipt': receipt}
    nb = save('TOY-batches.json', [batch])
    native = [{'id': rid, 'labels': native_labels[rid],
               'dimensions': {d: {'value': v} for d, v in native_labels[rid].items()},
               'packet': {k: packet[k] for k in ('path', 'bytes', 'sha256')}, 'original_batch_id': 'TOY-batch',
               'selected_mode': 'original', 'selected_attempt_number': 1, 'first': first,
               'selection': selection, 'technical_receipt': receipt, 'actor_seal': actor}
              for rid, packet in zip(full_frame_ids, packets)]
    nr = save('TOY-LLM.jsonl', native, True)
    def tally(rows):
        result = {}
        for d in DIMS:
            c = Counter(r['labels'][d] for r in rows)
            result[d] = {'positive_N': c[1], 'negative_N': c[0], 'lawful_null_N': c[None]}
        return result
    status = save('TOY-rule-status.json', {'actual_record_N': N, 'actual_dimension_N': N*5,
        'technical_failure_dimension_N': 0, 'unresolved_technical_dimension_N': 0,
        'prediction_binding': rp, 'label_slots_binding': sp, 'source_common_v16': common, 'counts': tally(rules)})
    coverage = save('TOY-coverage.json', {'full_corpus_complete': True, 'allocated_record_N': N,
        'selected_record_N': N, 'missing_record_N': 0, 'missing_label_N': 0,
        'allocated_batch_N': 1, 'selected_batch_N': 1, 'selection_by_semantic_metric': False,
        'first_values_changed': False, 'per_dimension': {d: {**c, 'missing_N': 0} for d, c in tally(native).items()}})
    alignment = save('TOY-alignment.json', {'native_material_aligned_record_N': N, 'native_material_mismatch_N': 0})
    packet_list = save('TOY-packets.json', packets)
    doc = {'schema': TOY_SCHEMA, 'inputs': {'frame_ids': frame, 'rule_predictions': rp,
        'rule_dimension_slots': sp, 'rule_execution_lineage': lp, 'rule_status': status,
        'LLM_records': nr, 'LLM_batches': nb, 'LLM_coverage': coverage, 'source_alignment': alignment,
        'current_packet_metadata': packet_list, 'current_common_source': common,
        'common_manual': manual, 'common_execution_prompt': prompt}, 'structural_check_results': {'frame_N': N, 'slots_per_method_N': N*5,
        'rule_record_N': N, 'LLM_record_N': N, 'rule_unresolved_technical_slot_N': 0,
        'LLM_missing_slot_N': 0, 'current_material_verified_packet_N': N,
        'rule_material_mismatch_N': 0, 'LLM_material_mismatch_N': 0,
        'adopted_source_alignment_reproduced': True, 'LLM_whole_batch_N': 1,
        'rule_lawful_null_N': 1, 'LLM_lawful_null_N': 1,
        'LLM_actual_record_modes': {'original': N}, 'rule_original_v11_failed_slots_retained_N': 5},
        'file_bindings': list(files)}
    fb = save('TOY-machine-freeze.json', doc)
    return {'machine_freeze_binding': fb, 'full_frame_ids': list(full_frame_ids),
            'synthetic': True, 'synthetic_sources': {'directory': str(root)}}
