"""After both v17 machines are complete, reuse the frozen native attention formulas.

No inference, source mutation, label repair or production adoption. The native
facade retains 24 actual new inferences plus 4457 inherited v16 records.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
if not __debug__:
    raise RuntimeError('Frozen statistical checks require assertions enabled')
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ADAPTER = ROOT / '07-statistics/full4481-native-attention-compatible-adapter-preparation-v2-sol/native_attention_adapter.py'
MERGER = ROOT / '06-coding/native-full4481-v17-two-whole-batch-merge-preparation-root/merge.py'
NATIVE_PREP = ROOT / '06-coding/native-v17-two-whole-batch-material-delta-preparation-root'
NATIVE = ROOT / '06-coding/native-full4481-v17-two-whole-batch-compatible-root'
PARENT = ROOT / '06-coding/native-full4481-v16-three-member-compatible-root'
SOURCE = ROOT / '01-review/source-interface-v17-finite-source-addendum-root'
RECEIVED = ROOT / '06-coding/rule-full4481-v15-v17-received-root'
RULE_IMPACT = HERE / 'full-rule-impact'
RULE_ATTENTION = RULE_IMPACT / 'frozen-core-evaluation'
DEFAULT_OUTPUT = HERE / 'full-machine-attention'
BATCH_IDS = ('batch-0325', 'batch-0485')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def frozen_module(path, sha, name):
    require(hashlib.sha256(path.read_bytes()).hexdigest() == sha, 'Changed frozen entry: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_and_metadata(a, m, frozen):
    seal = m.load(SOURCE / 'output-seal.json')
    common = m.bind(SOURCE / 'common-frame-bundles-v17.jsonl')
    packets = m.bind(SOURCE / 'packet-bindings-v17.json')
    for item in seal['files']:
        a.exact(m, item)
    require(common in seal['files'] and packets in seal['files'], 'Unsealed v17 source or packet map')
    units = list(m.iter_jsonl(a.BASE / 'unit-metadata.jsonl'))
    bundles = list(m.iter_jsonl(common['path']))
    bindings = m.load(packets['path'])
    require(len(units) == len(bundles) == len(bindings) == 4481, 'Incomplete metadata/material')
    require(len({u['unit_id'] for u in units}) == 4481, 'Duplicate source ID')
    for u, bundle, packet in zip(units, bundles, bindings):
        current = bundle['source_record']
        require(u['unit_id'] == current['id'] == packet['source_id'], 'v17 metadata/material order mismatch')
        require(hashlib.sha256(current['text'].encode()).hexdigest() == u['exact_current_text_sha256']
                and len(current['text']) == u['current_text_unicode_N'], 'Frozen statistical metadata no longer applies')
    return common, packets, units, bindings


def admit_rule(a, m, frozen, common):
    received_seal = a.sealed(m, RECEIVED, ('predictions.jsonl', 'composite-status.json', 'all-dimension-slots.jsonl', 'execution-origin-lineage.jsonl'))
    status = m.load(RECEIVED / 'composite-status.json')
    require(status['status'] == m.load(RECEIVED / 'seal.json')['status'] == 'validated_complete_full4481_v17_not_adopted', 'Rule is not fully received')
    require(status['actual_record_N'] == 4481 and status['actual_dimension_N'] == 22405
            and status['technical_failure_dimension_N'] == 0 and status['actual_new_inference_record_N'] == 4481
            and status['inherited_N'] == 0 and status['all4481_actually_inferred_under_candidate'] is True
            and status['candidate_algorithm_version'] == 'joint-v15b-complete-repair-root', 'Incomplete or wrong current rule execution')
    require(status['source_common_v17'] == common, 'Rule source is not current v17')
    impact_seal = a.sealed(m, RULE_IMPACT, ('impact.json', 'frozen-core-evaluation/conditional-robustness.json'))
    attention_seal = a.sealed(m, RULE_ATTENTION, ('conditional-robustness.json',))
    impact = m.load(RULE_IMPACT / 'impact.json')
    rule = m.load(RULE_ATTENTION / 'conditional-robustness.json')
    inputs = rule['inputs']['inputs']
    require(impact['received_seal'] == received_seal and impact['new_complete_robustness'] == m.bind(RULE_ATTENTION / 'conditional-robustness.json'), 'Rule attention is not linked to the accepted result')
    require(rule['unit_N'] == 4481 and rule['technical_failure_N'] == 0
            and rule['lawful_null_assignment_N'] == status['lawful_null_N'] and rule['entry'] == frozen['entry']
            and rule['inputs']['prepared'] == frozen['prepared'], 'Rule formula/metadata identity differs')
    require(inputs['bundles'] == common and inputs['material_seal'] == m.bind(SOURCE / 'output-seal.json')
            and inputs['predictions'] == m.bind(RECEIVED / 'predictions.jsonl')
            and inputs['rule_status'] == m.bind(RECEIVED / 'composite-status.json')
            and inputs['rule_seal'] == received_seal, 'Rule attention uses stale v11/v16 inputs')
    for item in [rule['inputs']['entry'], *inputs.values(), *rule['inputs']['prepared'].values()]:
        a.exact(m, item)
    return rule, {'rule_received_seal': received_seal, 'rule_impact_seal': impact_seal, 'rule_attention_seal': attention_seal}


def admit_native(a, m, merger, common, packet_binding, units, packets):
    native_seal = a.sealed(m, NATIVE, ('status.json', 'coverage.json', 'selected-records.jsonl', 'selected-whole-batch-bindings.json', 'strict-merge-readback.json'))
    coverage = a.full_coverage(m, NATIVE / 'coverage.json')
    status = m.load(NATIVE / 'status.json')
    expected = {'status': 'complete_native_full4481_v17_two_whole_batch_compatible_composite_with_explicit_execution_origins',
                'actual_record_N': 4481, 'actual_dimension_N': 22405, 'parent_raw_line_preserved_N': 4457,
                'actual_new_inference_record_N': 24, 'unresolved_technical_dimension_N': 0}
    require(all(status.get(k) == v for k, v in expected.items()) and status['actual_merge_performed'] is True
            and status['not_all4481_reencoded_in_v17'] is True and status['source_common_v17'] == common,
            'Incomplete or wrong native-v17 composite')
    # Reuse the sealed successful whole-batch admission logic; never call merge().
    doc, collector = merger.profile()
    parent, _, old_lines, _, old_batches = merger.parent_full(PARENT, collector, doc)
    require(status['parent_collector_seal'] == m.bind(parent / 'seal.json')
            and status['merger'] == m.bind(MERGER) and status['merger_preparation_seal'] == m.bind(MERGER.parent / 'seal.json'),
            'Unexpected actual native merge chain')
    selections = [NATIVE_PREP / bid / 'root-selection.json' for bid in BATCH_IDS]
    require(status['new_whole_selections'] == [m.bind(p) for p in selections], 'Two exact selections required')
    deliveries = [merger.new_whole(path, bid, collector, doc) for path, bid in zip(selections, BATCH_IDS)]
    require(m.load(NATIVE / 'strict-merge-readback.json') == {'batches': [dict(batch_id=bid, **d[3]) for bid, d in zip(BATCH_IDS, deliveries)]}, 'Saved readback differs from strict reception')
    expected_rows = {r['id']: r for _, _, new, _ in deliveries for r in new}
    require(len(expected_rows) == 24 and status['actual_new_whole_batch_record_ids'] == list(expected_rows)
            and status['material_changed_record_ids'] == list(merger.CHANGED), 'Whole inference/material scope differs')
    lines, selected = merger.rows((NATIVE / 'selected-records.jsonl').read_bytes())
    require(len(lines) == len(old_lines) == len(units) == 4481, 'Incomplete native delivery')
    normalized, preserved, null_n = [], 0, 0
    for old_line, line, r, u, pb in zip(old_lines, lines, selected, units, packets):
        require(r['id'] == u['unit_id'] == pb['source_id'] and r['packet'] == merger.flat(pb), 'Native source/packet/order mismatch')
        if r['id'] not in expected_rows:
            require(line == old_line, 'Inherited native delivery changed')
            preserved += 1
        else:
            # The merger only adds the explicit parent lineage after new_whole().
            expected_row = expected_rows[r['id']]
            for key in expected_row:
                if key != 'material_origin':
                    require(r[key] == expected_row[key], 'Spliced native whole first: ' + key)
            for key, value in expected_row['material_origin'].items():
                require(r['material_origin'][key] == value, 'Changed new material origin')
            origin = r['material_origin']['parent_record_origin']
            old = json.loads(old_line)
            require(origin['parent_collector_seal'] == m.bind(parent / 'seal.json')
                    and origin['parent_line_sha256'] == hashlib.sha256(old_line).hexdigest()
                    and all(origin[key] == old[key] for key in ('packet', 'first', 'selection', 'technical_receipt', 'actor_seal')), 'Broken inherited origin')
        labels = r['labels']
        require(set(labels) == set(r['dimensions']) == set(m.DIMS)
                and all(v is None or type(v) is int and v in (0, 1) for v in labels.values())
                and all(labels[d] == r['dimensions'][d]['value'] for d in m.DIMS), 'Invalid native labels')
        null_n += sum(v is None for v in labels.values())
        normalized.append({'id': r['id'], 'labels': labels, 'implementation_errors': []})
    require(preserved == 4457 and null_n == coverage['lawful_null_label_N'], 'Native preserved/null counts differ')
    batches = m.load(NATIVE / 'selected-whole-batch-bindings.json')
    require(len(batches) == 504 and [b['batch_id'] for b in batches] == [b['batch_id'] for b in old_batches], '504 original batches required')
    for old, current in zip(old_batches, batches):
        bid = current['batch_id']
        if bid not in BATCH_IDS:
            require(current == old, 'Inherited batch origin changed, including v16/0216')
        else:
            selection = deliveries[BATCH_IDS.index(bid)][0]
            require(current['source_ids'] == selection['source_ids']
                    and current['selection'] == m.bind(selections[BATCH_IDS.index(bid)])
                    and all(current[k] == selection[v] for k, v in [('first', 'first'), ('receipt', 'reception'), ('actor_seal', 'actor_seal')]), 'Incomplete replacement whole batch')
    return normalized, {'compatible_merge_seal': native_seal, 'parent_v16_seal': m.bind(parent / 'seal.json'),
        'selections': [m.bind(p) for p in selections], 'packet_bindings_v17': packet_binding, 'source_common_v17': common,
        'compatible_record_N': 4481, 'original_batch_N': 504, 'parent_line_bytes_preserved_N': preserved,
        'new_whole_batch_N': 2, 'new_whole_batch_record_N': 24, 'material_changed_record_N': 2,
        'lawful_null_N': null_n, 'all4481_new_native_inference': False, 'labels_or_reasons_modified': False,
        'null_imputed': False, 'formal_validation_complete': False}


def run(output):
    output = Path(output).resolve()
    require(not output.exists(), 'Output must be a new directory')
    # Neither absent/partial side can cause a facade or statistical output to be created.
    require((NATIVE / 'seal.json').is_file() and (RULE_IMPACT / 'seal.json').is_file()
            and (RULE_ATTENTION / 'conditional-robustness.json').is_file(), 'Both completed v17 machine inputs are required')
    a = frozen_module(ADAPTER, 'e5232ed10bd5b468aaf1ea5a0e204d3fbb641010393b9d8520c9ff4c4fa4bc6a', 'unchanged_native_attention_adapter')
    m = a.core()
    a.sealed(m, ADAPTER.parent, ('native_attention_adapter.py',))
    frozen = a.base_bindings(m)
    merger = frozen_module(MERGER, 'c04a60d43523bd12d872aa133257ac8957a480217d1b3f9bb9d6b43c069036eb', 'unchanged_v17_native_merger')
    common, packet_binding, units, packets = source_and_metadata(a, m, frozen)
    rule, rule_proof = admit_rule(a, m, frozen, common)
    normalized, proof = admit_native(a, m, merger, common, packet_binding, units, packets)
    require(len(rule['scenarios']) == 792 and len(rule['leave_one_source_entry_out']) == 408, 'Rule scenario definitions differ')
    output.mkdir()
    facade = output / 'native-input-facade'
    facade.mkdir()
    for name in ('unit-metadata.jsonl', 'source-entry-metadata.json', 'metadata-coverage.json'):
        (facade / name).symlink_to(a.BASE / name)
    m.jsonl(facade / 'predictions.jsonl', normalized)
    m.save(facade / 'status.json', {'actual_record_N': 4481, 'actual_dimension_N': 22405,
        'technical_failure_dimension_N': 0, 'lawful_null_N': proof['lawful_null_N'],
        'role': 'strict received native v17 composite used through rule-named statistical API; not rule execution or all4481 new native inference',
        'native_new_inference_record_N': 24, 'native_inherited_record_N': 4457})
    inputs = dict(frozen['inputs'])
    inputs['historical_rule_bounds_reference'] = inputs.pop('existing_bounds')
    inputs.update(bundles=common, material_seal=m.bind(SOURCE / 'output-seal.json'),
        predictions=m.bind(facade / 'predictions.jsonl'), rule_status=m.bind(facade / 'status.json'),
        rule_seal=proof['compatible_merge_seal'], actual_native_selected_records=m.bind(NATIVE / 'selected-records.jsonl'))
    m.save(facade / 'input-bindings.json', dict(frozen, inputs=inputs))
    m.save(facade / 'seal.json', {'files': [m.bind(facade / n) for n in ('predictions.jsonl', 'status.json', 'input-bindings.json')], 'self_excluded': True})
    m.HERE = facade
    raw_dir = output / 'frozen-core-evaluation'
    m.analyze(raw_dir)
    raw = m.load(raw_dir / 'conditional-robustness.json')
    require(len(raw['scenarios']) == 792 and len(raw['leave_one_source_entry_out']) == 408, 'Native scenario definitions differ')
    comparison = a.compare(m, rule, raw)
    comparison.update(**rule_proof, native_proof=proof, core_entry=frozen['entry'], unchanged_native_adapter=m.bind(ADAPTER))
    m.save(output / 'machine-attention-comparison.json', comparison)
    m.save(output / 'native-attention-source-role.json', {'machine': 'actual whole-batch LLM v17 compatible composite',
        'native_proof': proof, 'rule_proof': rule_proof, 'frozen_core_output': m.bind(raw_dir / 'conditional-robustness.json'),
        'current_text_metadata_identity_checked_N': 4481, 'legacy_rule_named_keys_are_statistical_facade_only': True,
        'core_formulas_scenarios_and_comparison_reused_without_edit': True, 'models_called': 0, 'classifiers_called': 0,
        'formal_validation_complete': False, 'production_adopted': False, 'paper_writing_gate_open': False})
    # Seal only actual output files after all inputs and comparisons have passed.
    m.save(output / 'seal.json', {'files': [m.bind(p) for p in sorted(output.rglob('*')) if p.is_file()],
        'self_excluded': True, 'formal_validation_complete': False, 'paper_writing_gate_open': False})
    print(json.dumps({'output': str(output), 'native_actual_new_record_N': 24, 'native_inherited_record_N': 4457,
                      'scenario_group_N': 792, 'leave_one_entry_group_N': 408, 'models_called': 0, 'classifiers_called': 0}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(DEFAULT_OUTPUT))
    run(parser.parse_args().output)
