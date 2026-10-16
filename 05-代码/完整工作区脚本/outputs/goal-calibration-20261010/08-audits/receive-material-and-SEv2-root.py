"""Receive sealed material and S/E/Ec candidates without rerunning a classifier."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '08-audits/material-and-SEv2-reception-root'

def load(path):
    return json.loads(Path(path).read_text())

def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def exact(item):
    assert bind(item['path']) == {k: item[k] for k in ('path', 'bytes', 'sha256')}, item['path']

def save(name, obj):
    with (OUT / name).open('x', encoding='utf8') as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2)
        handle.write('\n')

assert not OUT.exists(), 'Do not replace a prior reception'
common = ROOT / '08-audits/common-material-candidate-reception-sol'
cs = bind(common / 'output-seal.json')
assert cs['sha256'] == '9e671f12dfb521136891e68a540d4c1f099cceb9a537c0d26bfbcd1c30aeb198'
cseal = load(cs['path'])
for item in cseal['output_members']:
    exact(item)
for key in ('candidate_input_seal', 'shared_inventory', 'manual_binding'):
    exact(cseal[key])
parent_seal = load(cseal['candidate_input_seal']['path'])
for item in parent_seal['output_members']:
    exact(item)
inputs = load(common / 'audited-input-bindings.json')['files']
for item in inputs:
    exact(item)
report = load(common / 'report.json')
budget = report['budget_result']
assert report['mechanical_result']['counts'] == dict(records=4481, changed=1227, added_ranges=1227)
assert budget['unchanged_old504_assignments_candidate_over_budget_N'] == 106
assert budget['current_candidate_compact_full_preparation_envelope']['group_N_simulated'] == 659
assert not budget['current_candidate_compact_full_preparation_envelope']['oversize_single_packet_source_ids']
assert not report['scope_limits']['main_LLM_or_rule_judge_called']

v = ROOT / '06-coding/rule-v20-SEEconomic-repair-sol/versions/v2'
delivery = bind(v / 'delivery-seal.json')
candidate = bind(v / 'candidate-seal.json')
assert delivery['sha256'] == '39a87613fc07027fe97a7e739535d6101da0d248c8b84a1c573a6f699cba1d47'
assert candidate['sha256'] == 'a630f5b6c3da8a2a91bd9fd0375caf890d5dfaef83ef2a81df3d8ab062cfc0dd'
ds = load(delivery['path'])
assert ds['candidate_seal_sha256'] == candidate['sha256']
for item in ds['files']:
    exact(item)
seal = load(candidate['path'])
for key in ('code', 'regression_artifacts'):
    for item in seal[key]:
        exact(item)
exact(seal['manual'])
algorithm = load(v / 'algorithm-bindings.json')
assert algorithm['algorithm_sha256'] == seal['algorithm_sha256'] == '88eead7588d2e8353a4de6768cedd42a95ba4cb75c3dc819f6dd05aec9f5ac32'
for item in algorithm['five_modules']:
    exact(item)
exact(algorithm['manual'])
receipt = load(v / 'regression-reception.json')
recomputed = []
total = total_failed = 0
for run in receipt['runs']:
    exact(run['artifact'])
    record = load(run['artifact']['path'])
    tests = record.get('tests', [record])
    assert len(tests) == run['test_N']
    failures = []
    for case in tests:
        expected = next(case[k] for k in ('expected_fixed_before_v2_edit', 'expected_fixed_before_execution', 'expected') if k in case)
        observed = {dim: case['decisions'][dim]['value'] for dim in expected}
        assert observed == case['actual'], case['name']
        passed = expected == observed
        assert passed == case['passed'], case['name']
        if not passed:
            failures.append(dict(case=case['name'], original_fixed_expected=expected, actual=observed, status='preserved_material_scope_difference_not_label_fit'))
    assert failures == run['failures']
    total += len(tests)
    total_failed += len(failures)
    recomputed.append(dict(artifact=run['artifact'], cases=len(tests), matched=len(tests)-len(failures), retained_differences=failures))
assert total == 156 and total_failed == 4
assert sum(r['cases'] for r in recomputed if Path(r['artifact']['path']).name in ('structural-final-scope.json', 'dependency-final-scope.json', 'interface-final-scope.json', 'closure-bindings-final-scope.json', 'missing-middle-final.json')) == 54
reading = load(v / 'actual-read-and-quote-validation.json')
materials = {}
for item in reading['materials']:
    exact(item)
    materials[item['path']] = load(item['path'])
assert len(materials) == 34
real_quote_N = synthetic_quote_N = 0
for q in reading['quotes']:
    if q['material_path'] is not None:
        material = materials[q['material_path']]
        cur = material
        parts = q['json_pointer'].split('/')[1:]
        for part in parts:
            cur = cur[int(part)] if isinstance(cur, list) else cur[part]
        parent = material
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        real_quote_N += 1
    else:
        run = load(v / q['run'])
        case = next(c for c in run.get('tests', [run]) if c['name'] == q['case'])
        contexts = case['synthetic_input']['contexts']
        matches = [c for c in contexts if c.get('context_id') == q['context_id']]
        assert len(matches) == 1
        parent = matches[0]
        cur = parent['text']
        synthetic_quote_N += 1
    assert cur[q['start']:q['end']] == q['quote']
    assert parent.get('context_id') == q['context_id']
    assert parent.get('source_ref') == q['source_ref']
assert len(reading['quotes']) == 84 and (real_quote_N, synthetic_quote_N) == (46, 38)
OUT.mkdir()
result = dict(status='ROOT_received_sealed_developer_candidates_not_formal_release', at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    common_material=dict(seal=cs, exact_audit_output_members=len(cseal['output_members']), exact_audit_input_files=len(inputs), inventory=cseal['shared_inventory'], independent_report=bind(common/'report.json'), records=4481, literal_extended_records=1227, compact_max_bytes=budget['current_candidate_compact_full_preparation_envelope']['packet_bytes']['max'], old_groups_over_budget=106, new_group_count_simulation_only=659, adoption_or_dispatch=False),
    SE_Ec_v2=dict(delivery_seal=delivery, candidate_seal=candidate, sealed_delivery_members=len(ds['files']), algorithm=bind(v/'algorithm-bindings.json'), actual_material_bindings_checked=34, exact_positive_context_quotes_checked=84, actual_material_quotes_checked=real_quote_N, synthetic_control_quotes_checked=synthetic_quote_N, owner_developer_cases_recomputed=total, owner_matched_cases=total-total_failed, preserved_scope_differences=total_failed, new_controls_matched=54, runs=recomputed, new_independent_audit_delegated=True, joint_five_dimension_merge_or_formal_acceptance=False),
    actual_scope=dict(ROOT_classifier_reruns=0, complete_original_documents_semantically_read=False, human_initial_or_reference_results_created=0, main_LLM_partial_labels_read=False, historical_inputs_or_predictions_modified=False))
save('actual-reception.json', result)
save('output-seal.json', dict(output_members=[bind(OUT/'actual-reception.json')], receiver=bind(__file__), self_excluded=True))
print(json.dumps(dict(status=result['status'], destination=str(OUT), material_records=4481, owner_cases=156, retained_scope_differences=4, independent_acceptance=False), ensure_ascii=False))
