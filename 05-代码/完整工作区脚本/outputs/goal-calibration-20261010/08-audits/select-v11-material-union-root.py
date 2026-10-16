"""Pure current-text code gate plus sealed material delta; no classifier calls."""
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode = True

def bind(path):
    p = Path(path).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def exact(binding):
    assert bind(binding['path']) == {k: binding[k] for k in ('path', 'bytes', 'sha256')}
    return Path(binding['path'])

def load(path):
    return json.loads(Path(path).read_bytes())

def module(binding, name):
    spec = importlib.util.spec_from_file_location(name, exact(binding))
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--contract', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args(); out = Path(args.output); assert not out.exists()
    c = load(args.contract); audit = c['manual_static_audit']
    assert audit['approved'] is True and audit['approval_actor'] == 'ROOT'
    assert c['allowed_mutable_dimensions'] == ['I']
    for key in ('record_local_only', 'new_relation_not_consumed_by_old_units',
                'only_allowed_dimension_decision_or_explicit_request_mutations',
                'same_adapter_evidence_wrapper_and_only_sealed_material_delta',
                'mixed_baseline_equivalence_for_unselected_unchanged_material_verified',
                'pure_current_text_gate_and_material_union_verified'):
        assert audit[key] is True
    for b in audit['proof_artifact_bindings']: exact(b)
    assert c['selector_binding'] == bind(__file__)
    code = module(c['candidate_code_selector_binding'], 'frozen_v11_static_ast')
    assert code.prove_code(c['old_modules'], c['candidate_modules']) is True
    material_api = module(c['material_checker_binding'], 'frozen_material_checker')
    original_scope = load(exact(c['original_scope_binding']))
    original_plan = load(exact(c['original_packet_plan_binding']))
    material = material_api.validate_material(c['material_delta_bindings'], original_scope, original_plan)
    assert c['material_changed_record_ids'] == material['changed_record_ids']
    manifest = load(exact(c['manifest_binding'])); old_manifest = load(exact(c['baseline_manifest_binding']))
    ids = original_scope['approved_record_ids']
    assert manifest['approved_record_ids'] == old_manifest['approved_record_ids'] == ids
    assert [r['id'] for r in manifest['records']] == [r['id'] for r in old_manifest['records']] == ids
    assert manifest['record_N'] == 4481 and manifest['classifier_executed'] is False
    assert manifest['source_input'] == material['new_source']
    assert manifest['material_delta_bindings'] == material['bindings']
    assert [r['packet_binding'] for r in manifest['records']] == [material_api.flat(p) for p in material['packets']]
    assert [r['packet_binding'] for r in old_manifest['records']] == [material_api.flat(p) for p in original_plan['packets']]
    parent = [json.loads(raw) for raw in exact(c['baseline_prediction_binding']).read_bytes().splitlines()]
    assert [r['id'] for r in parent] == ids
    assert all(not r['implementation_errors'] and set(r['decisions']) == {'S', 'E', 'Ec', 'I', 'F'}
               and r['decisions'] == r['candidate_decisions_diagnostic_only'] for r in parent)
    exact(c['baseline_seal_binding'])
    gate = module(c['static_gate_binding'], 'frozen_v11_pure_gate')
    affected, excluded, gate_ids = [], [], []
    changed = set(material['changed_record_ids'])
    for row in manifest['records']:
        packet = load(exact(row['packet_binding']))
        assert packet['source_id'] == row['id'] and packet['output_id'] == row['output_id']
        current = packet['source_bundle']['source_record']
        assert current['id'] == row['id'] and isinstance(current['text'], str)
        matched = bool(gate.gate(current['text']))
        if matched: gate_ids.append(row['id'])
        reasons = []
        if matched: reasons.append('pure_current_protected_data_role_entry')
        if row['id'] in changed: reasons.append('sealed_material_changed_whole_record')
        record = {'id': row['id'], 'packet_binding': row['packet_binding'], 'gate_matched': matched,
                  'material_changed': row['id'] in changed, 'reasons': reasons,
                  'recompute_scope': 'whole record and complete evidence/typed request chains'}
        (affected if reasons else excluded).append(record)
    result = {'status': 'static_selection_only_no_classifier_execution', 'record_N': 4481,
              'selected_N': len(affected), 'reusable_N': len(excluded), 'affected_records': affected,
              'selected_record_ids': [r['id'] for r in affected], 'reusable_record_ids': [r['id'] for r in excluded],
              'code_gate_record_ids': gate_ids, 'material_changed_record_ids': material['changed_record_ids'],
              'material_delta_bindings': material['bindings'], 'full_fallback_reasons': [],
              'contract_binding': bind(args.contract), 'manifest_binding': c['manifest_binding'],
              'baseline_prediction_binding': c['baseline_prediction_binding'], 'selector_binding': bind(__file__),
              'candidate_code_selector_binding': c['candidate_code_selector_binding'],
              'gate_source_binding': c['static_gate_binding'], 'approved_record_ids': ids,
              'selection_never_filters_old_zero_one_or_null': True, 'classifier_executions': 0}
    material_api.validate_union(result, c, material, ids)
    with out.open('x', encoding='utf8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({k: result[k] for k in ('record_N', 'selected_N', 'reusable_N', 'classifier_executions')}))

if __name__ == '__main__': main()
