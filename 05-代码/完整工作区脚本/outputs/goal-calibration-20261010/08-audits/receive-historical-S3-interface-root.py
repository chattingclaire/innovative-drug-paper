"""Receive the source inspection and historical development plan; no classifier."""
import datetime
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
D = R / '08-audits/common-candidate-actual-interface-sol'
O = R / '08-audits/historical-S3-interface-reception-root'
assert not O.exists()

def load(p):
    return json.loads(Path(p).read_bytes())

def bind(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def exact(b):
    assert bind(b['path']) == {k: b[k] for k in ('path', 'bytes', 'sha256')}, b['path']

def receive(p, sha, members, inputs):
    b = bind(p)
    assert b['sha256'] == sha
    value = load(p)
    assert len(value['members']) == members and len(value['inputs']) == inputs
    assert not any(Path(m['path']).resolve() == Path(p).resolve() for m in value['members'])
    for m in value['members'] + value['inputs']:
        exact(m)
    return b, value

source_seal, source = receive(D / 'output-seal.json',
    '0e4d70ac1bc0d78e54b302e87a3123ade68edef888000df6446cf1232ce9f156', 11, 10)
plan_seal, plan = receive(D / 'historical-human-S3-development-plan/output-seal.json',
    'e791c3183117c5d2c427788b818febf6df0faa2c6c99d3d2f73206690f4b185b', 11, 13)
ids = ['RECODE25-00036', 'RECODE25-00038', 'RECODE25-00045']
findings = load(D / 'interface-findings.json')
assert [f['record_id'] for f in findings] == ids
for f in findings:
    assert f['historically_exposed_ID_confirmed']
    assert f['old_new_source_bundle_equal'] and f['prior_semantic_contexts_equal']
    assert f['literal_standard_terminal_boundary_available']
    assert not f['candidate_provenance']['material_interface_changed']
    assert f['dimension_expectations'] is None and f['classification'] is None
fixed = load(D / 'historical-human-S3-development-plan/fixed-S3-before-execution.json')
assert [f['record_id'] for f in fixed] == ids
for f in fixed:
    assert f['dimension'] == 'S' and f['expected_value'] == 1
    q = f['acceptance_document_quote']
    exact(q['source'])
    text = Path(q['source']['path']).read_text()
    low, high = q['line_range_1based_inclusive']
    quote = ''.join(text.splitlines(keepends=True)[low-1:high])
    assert quote == q['quote']
    assert hashlib.sha256(quote.encode()).hexdigest() == q['quote_sha256']
    exact(f['frozen_source_packet_copy'])
    exact(f['exact_upstream_source_packet'])
    assert Path(f['frozen_source_packet_copy']['path']).read_bytes() == Path(f['exact_upstream_source_packet']['path']).read_bytes()
assert source['actual_adapter_calls'] == 7 and source['unique_adapter_identities'] == 6
assert source['judge_calls'] == 0 and source['RelationView_calls'] == 0
assert plan['algorithm_binding'] is None and plan['judge_calls'] == 0
receipt = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='ROOT_received_source_interface_and_historical_S3_development_plan',
    record_ids=ids, source_seal=source_seal, source_members_N=11, source_inputs_N=10,
    plan_seal=plan_seal, plan_members_N=11, plan_inputs_N=13,
    original_current_source_and_same_version_standards_available=True,
    old_new_source_bundles_equal=True,
    semantic_context_equality_previously_observed=True,
    complete_saved_semantic_unit_equality_not_independently_replayed=True,
    structured_reference_and_finite_closure_interface_missing=True,
    actual_upstream_adapter_calls=7, unique_upstream_adapter_identities=6,
    expected_S_values=[1, 1, 1], identity='historical user-confirmed development adjudication',
    frozen_original_and_revised_archives_preserved=True,
    no_claim_of_original_first_submission_chain=True,
    new_ROOT_adapter_or_RelationView_or_judge_calls=0,
    new_human_reference_or_formal_statistics_N=0,
    classifier_execution_pending_final_v4_binding=True,
    original_exposure_status_preserved=True,
    receiver=bind(__file__))
O.mkdir()
def save(p, value):
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
save(O / 'actual-reception.json', receipt)
save(O / 'output-seal.json', {'output_members': [bind(O / 'actual-reception.json')], 'self_excluded': True})
print(json.dumps({k: receipt[k] for k in ('status', 'expected_S_values',
    'structured_reference_and_finite_closure_interface_missing', 'new_ROOT_adapter_or_RelationView_or_judge_calls')}, ensure_ascii=False))
