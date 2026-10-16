"""Record real rule-repair progress and technical LLM coverage, not acceptance."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--controller-session-running', action='store_true')
args = parser.parse_args()

def load(p):
    return json.loads(Path(p).read_bytes())

def bind(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def exact(b):
    assert bind(b['path']) == {k: b[k] for k in ('path', 'bytes', 'sha256')}, b['path']

def receive(p, sha=None, members=None, inputs=None):
    b = bind(p)
    if sha is not None:
        assert b['sha256'] == sha
    j = load(p)
    rows = j.get('output_members', j.get('members', []))
    if members is not None:
        assert len(rows) == members
    if inputs is not None:
        assert len(j['inputs']) == inputs
    for m in rows + j.get('inputs', []):
        assert Path(m['path']).resolve() != Path(p).resolve()
        exact(m)
    return b

old = R / 'logs/root-joint20-and-batch659-progress-20261011'
receive(old / 'output-seal.json')
previous = load(old / 'actual-progress.json')
assert previous['current_goal_turn_classification'] == 'progress'
for folder in ('dynamic-domain-engine-reception-root', 'historical-S3-interface-reception-root',
               'joint-v4-reception-root'):
    receive(R / '08-audits' / folder / 'output-seal.json')
v3_audit = R / '08-audits/five-dimension-joint-v3-independent-sol/execution-joint-v3-interface-sol'
receive(v3_audit / 'output-seal.json',
    '2e5c1426b344b52d5bac000462b776729a7b471b15a03c304d094f88eb132cc3', 53)
v3_report = load(v3_audit / 'report.json')
assert (v3_report['readable_numeric_discrepancy_dimensions_N'],
        v3_report['constructor_exception_cases_N']) == (3, 3)
hidden = R / '08-audits/joint-v4-independent-sol/execution-joint-v4-structure-normalization-sol'
hidden_seal = receive(hidden / 'output-seal.json',
    '5524b7cfea4744b4b958665be075c833178bd9c8056c58a860906f6b989cb2cb', 29)
hidden_report = load(hidden / 'report.json')
h = hidden_report['first_execution_summary']
assert (h['case_N'], h['matched_N'], h['execution_exceptions_N']) == (6, 6, 0)
actual = R / '08-audits/common-candidate-actual-interface-v4-execution-sol'
actual_seal = receive(actual / 'output-seal.json',
    '3440b911dd4eb92773a2edda27ea33e87b71e90da40165203a6af2300c4af8ca', 21, 16)
results = load(actual / 'execution-results.json')
assert [x['actual_S'] for x in results] == [0, 0, 0]
assert [x['expected_S'] for x in results] == [1, 1, 1]
for x in results:
    assert x['calls'] == dict(semantic_unit=1, RelationView=1, judge=1)
    assert x['execution_error'] is None and x['mechanical_validation_error'] is None
    assert not x['formal_accuracy_claim'] and not x['new_real_human_result']
campaign = R / '06-coding/native-full4481-v1-sol'
selected = sorted(campaign.glob('batch-*/root-selection.json'))
records = 0
for p in selected:
    selection = load(p)
    exact(selection['technical_reception'])
    reception = load(selection['technical_reception']['path'])
    assert reception['state'] == 'technical_valid_whole_batch'
    records += reception['validation']['record_N']
assert 1044 <= records <= 4481
observation = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    selected_batch_N=len(selected), technically_receipted_records=records,
    not_yet_receipted_records=4481-records, exec_session_id=58820,
    last_session_poll_was_running=args.controller_session_running, capacity=13,
    live_snapshot_not_claim_of_atomic_scheduler_state=True,
    partial_machine_labels_read_for_semantic_repair=False,
    full_output_complete_or_accepted=False)
result = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    current_goal_turn_classification='progress', previous_goal_turn_classification='progress_verified',
    previous_log=bind(old / 'actual-progress.json'),
    dynamic_engine_reception=bind(R / '08-audits/dynamic-domain-engine-reception-root/actual-reception.json'),
    dynamic_engine_math_functions_unchanged_N=27,
    current_new_scope_registrations_or_draws_or_human_reference_statistics_N=0,
    historical_source_interface_reception=bind(R / '08-audits/historical-S3-interface-reception-root/actual-reception.json'),
    v3_independent_first_capture_loss_preserved=True,
    v3_attempt02_recorded_constructions_N=12, v3_attempt02_recorded_judges_N=9,
    v3_actual_semantic_discrepancies_N=3, v3_construction_failures_N=3,
    construction_failures_not_NULL_or_15_semantic_errors=True,
    v3_total_judge_count_not_reconstructed=True,
    frozen_v4_reception=bind(R / '08-audits/joint-v4-reception-root/actual-reception.json'),
    new_hidden6=dict(seal=hidden_seal, actual_adapter_and_judge_calls_each=6,
        matched_N=6, technical_or_numeric_failures_N=0,
        current_and_context_quote_checks_passed=True,
        only_IF_units_N=4, only_IF_positive_consumers_N=0,
        only_IF_positive_intersection_not_dynamically_exercised=True,
        typed_subset_units_N=8, typed_subset_positive_consumers_N=4,
        positive_consumer_route_violations_N=0,
        synthetic_nonhuman_code_audit_not_formal_accuracy=True),
    historical_actual_S3=dict(seal=actual_seal,
        record_ids=[x['record_id'] for x in results], actual_S=[0, 0, 0],
        fixed_historical_user_confirmed_S=[1, 1, 1],
        adapter_RelationView_judge_calls_each=3, retries=0, errors=0,
        cited_standard_found_but_rejected_by_SE_closure_consumer_gate=True,
        negative_results_preserved_not_claimed_NULL=True,
        identity='Historical development adjudication, not new independent human validation'),
    separate_v5_repair=dict(status='in_progress_not_frozen_or_adopted',
        scope='Finite same-version standard closure receipt and precise quote boundary consumption',
        source_text_already_available=True,
        original_v4_and_first_results_not_overwritten=True,
        no_unconditional_cited_standard_or_ID_based_labels=True,
        developer_controls_authorized_max_N=6,
        independent_source_only_controls_preparation_authorized_max_N=4,
        final_algorithm_required_before_further_actual_S3_execution=True),
    native_full4481_observation=observation,
    actual_new_human_results_N=0, formal_metric_acceptance=False,
    new_actual_statistics_annual_metrics_or_stability_runs_N=0,
    complete_manuscript_started=False,
    remaining=['v5 limited closure proof repair and checks',
        'complete current fixed full4481 campaign without semantic output selection',
        'freeze appropriate common materials and versions before new validation',
        'actual independent human/reference validation and all metric acceptance',
        'stability, attention robustness and full manuscript after acceptance'],
    integrator=bind(__file__))
progress = R / 'progress.json'
raw = progress.read_bytes()
state = json.loads(raw)
folder = R / 'logs/root-joint-v4-rule-repair-progress-20261011'
assert not folder.exists()
folder.mkdir()
(folder / 'previous-progress.json').write_bytes(raw)
def save(p, value):
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
save(folder / 'actual-progress.json', result)
save(folder / 'output-seal.json', {'output_members': [bind(folder / 'previous-progress.json'),
    bind(folder / 'actual-progress.json')], 'self_excluded': True})
state['joint_v4_rule_repair_actual_reception'] = result
state['current_fixed_full4481_execution_observation'] = observation
state['current_goal_turn_classification'] = 'progress'
state['updated_at_utc'] = result['at_utc']
temp = R / 'progress.joint-v4.tmp.json'
assert not temp.exists()
save(temp, state)
temp.replace(progress)
print(json.dumps(dict(classification='progress', hidden6_matched=6,
    historical_S3_actual=[0, 0, 0], historical_S3_expected=[1, 1, 1],
    v5_status='in_progress', selected_batch_N=len(selected), technical_records=records,
    formal_metric_acceptance=False), ensure_ascii=False))
