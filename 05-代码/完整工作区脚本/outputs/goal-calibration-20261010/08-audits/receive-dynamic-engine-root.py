"""Receive sealed implementation and its independent review; no statistics."""
import ast
import datetime
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
D = R / '07-statistics/prospective-dynamic-domain-engine-sol'
A = R / '08-audits/dynamic-domain-engine-independent-sol'
O = R / '08-audits/dynamic-domain-engine-reception-root'
assert not O.exists()

def load(p):
    return json.loads(Path(p).read_bytes())

def bind(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def exact(b):
    assert bind(b['path']) == {k: b[k] for k in ('path', 'bytes', 'sha256')}

def receive(p, sha, count):
    b = bind(p)
    assert b['sha256'] == sha
    members = load(p)['output_members']
    assert len(members) == count
    for m in members:
        exact(m)
    return b

candidate = receive(D / 'output-seal.json',
    '612e3948e0c48c551a4feb7479e2fc813540124bbbbca70933813c0f52642e7b', 140)
independent = receive(A / 'output-seal.json',
    'af8b7bd42417dfc3591c9399c82276c0e4c661cc1bda9c27aeb3d3ca0992d605', 14)
original = R / '07-statistics/prospective-engine-year-independent-audit-sol/metrics_engine_repaired.py'
assert bind(original)['sha256'] == 'f6b33491bb27d7325cdc18c25fb7d54fef45909e1ef38c3f27606edcb61c2262'
trees = [ast.parse(p.read_text()) for p in (original, D / 'metrics_engine.py')]
functions = [{n.name: ast.dump(n, include_attributes=False) for n in tree.body
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))} for tree in trees]
old, new = functions
unchanged = [name for name in old if old[name] == new.get(name)]
changed = [name for name in old if old[name] != new.get(name)]
assert len(unchanged) == 27 and set(changed) == {'prepare', 'review_eligibility', 'analyze'}
assert set(new) - set(old) == {'_admit_registered_scope'}
report = load(A / 'report.json')
assert report['sealed_candidate_members_N'] == 140
assert report['new_actual_scope_or_draw_or_human_reference_statistics_N'] == 0
assert not report['actual_registered_positive_path_checked']
for f in ('stage-dependency-review.json', 'projection-binding-full-chain.json'):
    for value in load(A / f).values():
        if isinstance(value, dict) and {'binding', 'line_1based', 'quote'} <= value.keys():
            exact(value['binding'])
            text = Path(value['binding']['path']).read_text()
            line = value['line_1based']
            assert ''.join(text.splitlines(keepends=True)[line-1:]).startswith(value['quote'])
results = load(D / 'control-results-final.json')
assert (results['cases_N'], results['passed_N'], results['failed_N']) == (29, 29, 0)
assert load(D / 'wrapper-control-result.json')['passed']
stage = load(D / 'stage-helper-control-results.json')
assert (stage['passed_N'], stage['failed_N']) == (2, 0)
registry = load(D / 'ROOT-scope-registry.UNADOPTED.json')
assert registry['registrations'] == {}
receipt = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='ROOT_received_sealed_unadopted_dynamic_statistics_candidate',
    candidate_seal=candidate, candidate_members_checked_N=140,
    independent_seal=independent, independent_members_checked_N=14,
    unchanged_function_names=unchanged, changed_admission_functions=changed,
    actual_quote_and_line_checks=True, existing_control_results_received_N=32,
    new_control_or_statistical_executions_N=0,
    shared_scope_requires_pre_frozen_machine_protocols=True,
    human_first_requires_only_actual_A_B_method_submissions=True,
    machine_reference_requires_only_actual_reference_rule_LLM_submissions=True,
    current_ledger_projection_is_recomputed_by_unchanged_prepare=True,
    current_ROOT_registered_scopes_N=0, actual_registered_positive_path_verified=False,
    actual_new_draw_human_reference_statistics_N=0, formal_acceptance=False,
    main_partial_predictions_read=False, receiver=bind(__file__))
O.mkdir()
def save(p, value):
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
save(O / 'actual-reception.json', receipt)
save(O / 'output-seal.json', {'output_members': [bind(O / 'actual-reception.json')], 'self_excluded': True})
print(json.dumps({k: receipt[k] for k in ('status', 'candidate_members_checked_N',
    'independent_members_checked_N', 'current_ROOT_registered_scopes_N', 'formal_acceptance')}, ensure_ascii=False))
