"""Verify frozen v4 implementation and recorded development runs without reruns."""
import ast
import datetime
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
D = R / '06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol'
B = D.parent / 'joint-v3-interface-sol'
O = R / '08-audits/joint-v4-reception-root'
assert not O.exists()

def load(p):
    return json.loads(Path(p).read_bytes())

def bind(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def exact(b):
    assert bind(b['path']) == {k: b[k] for k in ('path', 'bytes', 'sha256')}, b['path']

delivery = bind(D / 'delivery-seal.json')
assert delivery['sha256'] == '7732efae659ca39b8474a726a915dacd86312e2300f4ed7daf73ee9f832c28ec'
members = load(D / 'delivery-seal.json')['output_members']
assert len(members) == 155
for m in members:
    assert Path(m['path']).resolve() != D / 'delivery-seal.json'
    exact(m)
pre = bind(D / 'pre-execution-seal.json')
algorithm = bind(D / 'algorithm-bindings.json')
assert pre['sha256'] == 'd3eb4a895f1154173488eac32366f86a47687c9935716eb50876f3ba9a5670e0'
assert algorithm['sha256'] == '45c33b4eb89e3a263a36560515617f1884f91c13e988777881675b7119e8a54b'
p = load(pre['path'])
a = load(algorithm['path'])
exact(p['algorithm_bindings'])
assert p['five_modules'] == a['five_modules']
for m in p['five_modules'] + p['common_frozen_input_bindings'] + p['fixed_development_controls']:
    exact(m)
exact(p['manual'])
assert not p['post_independent_result_mutation_allowed']
assert not p['new_v4_hidden_controls_read'] and not p['historical_actual_S3_plan_read']

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
assert sum(map(len, changes.values())) == 19
assert len(changes['relations.py']) == 16 and len(changes['dimensions.py']) == 3
for n in ('_add', '_units', '_generic', 'judge'):
    name = 'RelationView.' + n if n == '_add' else n
    file = 'relations.py' if n == '_add' else 'dimensions.py'
    assert functions(B / file)[name] == functions(D / file)[name]
finite = load(D / 'finite-runs-reception.json')
assert finite['run_N'] == 12 and finite['case_execution_N'] == 382
assert finite['v3_parent235_all_five_outputs_identical']
assert finite['v3_parent235_all_expectations_identical']
assert finite['expectations_not_passed_to_classifiers']
remaining = load(D / 'retained-failures.json')
assert remaining['remaining_final_discrepancy_rows_N'] == 11
receipt = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='ROOT_received_frozen_v4_development_candidate',
    delivery=delivery, verified_delivery_members_N=155,
    pre_execution_seal=pre, algorithm_bindings=algorithm,
    effective_function_changes=changes, effective_function_changes_N=19,
    shared_add_units_generic_judge_unchanged=True,
    adapter_receipts_evidence_original_bytes_unchanged=True,
    manual_and_common_protocol_unchanged=True,
    finite_development_runs_N=12, recorded_case_executions_N=382,
    actual_judge_call_total_not_inferred_from_case_count=True,
    parent235_all_values_and_expectations_equal_v3=True,
    retained_original_expectation_discrepancy_rows_N=11,
    first_ROOT_schema_probe_error='KeyError modules; v4 schema is five_modules; no classifier call',
    source_only_new_hidden6_and_historical_S3_delegated_after_frozen_binding=True,
    new_ROOT_classifier_or_adapter_executions_N=0,
    new_human_reference_statistics_N=0, formal_acceptance=False,
    known_actual_historical_S3_consumer_gap_requires_separate_v5=True,
    partial_main_LLM_labels_read=False,
    receiver=bind(__file__))
O.mkdir()
def save(path, value):
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
save(O / 'actual-reception.json', receipt)
save(O / 'output-seal.json', {'output_members': [bind(O / 'actual-reception.json')], 'self_excluded': True})
print(json.dumps({k: receipt[k] for k in ('status', 'verified_delivery_members_N',
    'effective_function_changes_N', 'formal_acceptance')}, ensure_ascii=False))
