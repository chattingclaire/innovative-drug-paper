"""Receive existing sealed v5 executions; never run a coder or change predictions."""
import ast
import datetime
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
D = R / '06-coding/rule-five-dimension-joint-root/versions/joint-v5-primary-standard-bridge-sol'
B = D.parent / 'joint-v4-structure-normalization-sol'
O = R / '08-audits/joint-v5-and-first-fullrun-reception-root'
assert not O.exists()

def load(p):
    return json.loads(Path(p).read_bytes())

def bind(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def exact(b):
    assert bind(b['path']) == {k: b[k] for k in ('path', 'bytes', 'sha256')}, b['path']

def receive(p, sha, members, inputs=None):
    b = bind(p)
    assert b['sha256'] == sha
    j = load(p)
    rows = j.get('output_members', j.get('members', []))
    assert len(rows) == members
    if inputs is not None:
        assert len(j['inputs']) == inputs
    for m in rows + j.get('inputs', []):
        assert Path(m['path']).resolve() != Path(p).resolve()
        exact(m)
    return b

delivery = receive(D / 'delivery-seal.json',
    '029a125a217ecd61d745da1ea4b9a88614a6d4bc6a3f6fe759eb431d323fc9ad', 121)
pre = bind(D / 'pre-execution-seal.json')
algorithm = bind(D / 'algorithm-bindings.json')
assert pre['sha256'] == '4f8ae9d0a3eb116dd3cd6b44bd8355683b08a54921ee1a6739aff0b609dc3cae'
assert algorithm['sha256'] == '5f9d780b4a72779f69e91082881109f65aa8adc6395ebf94b061bd207e0d14bf'
p, a = load(pre['path']), load(algorithm['path'])
exact(p['algorithm_bindings'])
assert p['five_modules'] == a['five_modules']
for m in p['five_modules'] + p['common_frozen_input_bindings']:
    exact(m)
exact(p['manual'])
assert not p['post_independent_algorithm_edit_allowed']
assert not p['owner_executed_actual_S3_candidate'] and not p['independent_hidden4_read']

def functions(path):
    tree = ast.parse(path.read_text())
    out = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[n.name] = ast.dump(n, include_attributes=False)
        elif isinstance(n, ast.ClassDef):
            for f in n.body:
                if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[n.name + '.' + f.name] = ast.dump(f, include_attributes=False)
    return out

changes = {}
for m in p['five_modules']:
    current = Path(m['path'])
    old = B / current.name
    before, after = functions(old), functions(current)
    assert not set(before) - set(after)
    changes[current.name] = [n for n in after if after[n] != before.get(n)]
    if current.name in ('source_packet.py', 'source_receipts.py', 'evidence.py'):
        assert current.read_bytes() == old.read_bytes()
assert sum(map(len, changes.values())) == 5
assert len(changes['relations.py']) == 3 and len(changes['dimensions.py']) == 2
for file, name in [('relations.py', 'RelationView._add'), ('dimensions.py', '_generic'),
                   ('dimensions.py', 'judge'), ('dimensions.py', '_se_allowed')]:
    assert functions(B / file)[name] == functions(D / file)[name]
finite = load(D / 'finite-runs-reception.json')
assert (finite['runs_N'], finite['case_execution_N']) == (9, 650)
assert (finite['final6_matches'], finite['final75_matches'], finite['final235_matches']) == (6, 75, 227)
assert finite['final235_all_five_outputs_identical_to_v4']

hidden = R / '08-audits/finite-closure-v5-independent4-sol/execution-v5-first'
hidden_seal = receive(hidden / 'output-seal.json',
    'b7c251a65b029c33c413ad5abc880d4fd4b419128ddb0c0e188cb46e25f0f6dc', 22, 21)
h = load(hidden_seal['path'])
assert h['actual_S'] == h['fixed_S_expectations'] == [1, None, 1, 0]
assert (h['case_count'], h['unique_current_source_text_combinations'], h['matches']) == (4, 3, 4)
assert h['calls'] == dict(semantic_unit=4, RelationView=4, judge=4)
assert (h['execution_errors'], h['mechanical_errors'], h['retries']) == (0, 0, 0)

actual = R / '08-audits/common-candidate-actual-interface-v5-execution-sol'
actual_seal = receive(actual / 'output-seal.json',
    '9f5a59ffec0553861904f6eb359d217e56efd77197a6832418df438cf5d22666', 34, 38)
s = load(actual / 'execution-summary.json')
assert s['actual_S'] == [1, 1, 1]
assert s['calls'] == dict(semantic_unit=3, RelationView=3, judge=3)
assert (s['execution_errors_N'], s['validator_errors_N'], s['retry_N']) == (0, 0, 0)
assert s['expectation_dimensions'] == ['S'] and s['other_dimensions_observation_only']

reuse = R / '08-audits/common-material-input-reuse-plan-independent-sol'
reuse_seal = receive(reuse / 'output-seal.json',
    '73a6e577ee330c02ae4e468b811b15b596befb7e4ebebe292d470049ce323bb2', 10)
run = R / '06-coding/rule-full4481-final-v5-sol'
run_pre = bind(run / 'pre-execution-run-seal.json')
assert run_pre['sha256'] == '2bf1a02ec6a92fc96bdf698b3d80ff8e28a6a7c980c924d76a53008b291a3dfc'
r = load(run_pre['path'])
for m in r['entry_files']:
    exact(m)
assert r['candidate_semantic_modules_unchanged']
assert r['max_actual_cohort_inference_runs'] == 1 and not r['neutral_projection_GO']
assert not r['formal_validation_complete'] and not r['human_validation_complete']

receipt = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='ROOT_received_frozen_v5_development_and_first_fullrun_entry',
    delivery=delivery, verified_delivery_members_N=121,
    pre_execution_seal=pre, algorithm_bindings=algorithm,
    effective_function_changes=changes, effective_function_changes_N=5,
    manual_and_common_protocol_unchanged=True,
    source_adapter_receipts_evidence_bytes_unchanged=True,
    shared_add_generic_judge_and_se_allowed_unchanged=True,
    finite_development_runs_N=9, recorded_case_executions_N=650,
    actual_judge_count_not_inferred_from_case_count=True,
    accidental_unchanged_baseline_repeat_after_editor_error_preserved=True,
    parent235_all_values_equal_v4=True, retained_parent235_expected_discrepancy_rows_N=8,
    independent_hidden4=dict(seal=hidden_seal, actual_S=[1, None, 1, 0],
        matched_N=4, unique_current_source_bodies_N=3, errors=0, retries=0,
        nonhuman_synthetic_development_check_not_formal_accuracy=True,
        version_conflict_case_not_included=True),
    historical_actual_S3=dict(seal=actual_seal, actual_S=[1, 1, 1],
        previous_v4_S=[0, 0, 0], historical_fixed_S=[1, 1, 1],
        calls_each=3, errors=0, retries=0, expected_dimensions=['S'],
        other_dimensions_observed_only=True,
        preliminary_runner_preflight_field_error_preserved_zero_candidate_calls=True,
        validation_is_finite_interface_not_full_driver_strict_ledger=True,
        nonhuman_development_regression_not_new_human_accuracy=True),
    material_reuse_planning=dict(seal=reuse_seal, inner_bundle_equal_N=3254,
        inner_bundle_changed_N=1227, same_whole_ordered_batch_and_inner_material_records_N=420,
        original_results_reused_or_new_material_adopted_N=0,
        equivalence_of_inner_bytes_not_automatic_whole_run_equivalence=True),
    first_fullrun_entry=dict(preseal=run_pre, verified_entry_files_N=len(r['entry_files']),
        original_common_material=True, one_first_semantic_pass=True, neutral_GO=False,
        strict_source_request_field_consumer_problem_observed=True,
        original_technical_failures_must_remain_preserved=True,
        diagnostic_labels_not_automatically_retained=True),
    new_ROOT_classifier_or_adapter_executions_N=0,
    partial_main_LLM_labels_read=False, formal_acceptance=False,
    receiver=bind(__file__))
O.mkdir()
def save(path, value):
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
save(O / 'actual-reception.json', receipt)
save(O / 'output-seal.json', {'output_members': [bind(O / 'actual-reception.json')], 'self_excluded': True})
print(json.dumps(dict(status=receipt['status'], members_N=121,
    effective_function_changes_N=5, independent4_matched=4, historical_S=[1, 1, 1],
    full_driver_receipt_issue_preserved=True, formal_acceptance=False), ensure_ascii=False))
