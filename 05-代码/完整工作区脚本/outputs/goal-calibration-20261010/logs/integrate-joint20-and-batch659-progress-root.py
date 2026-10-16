"""Integrate actual receptions and status-only coverage without reading predictions."""
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

def save(p, v):
    with p.open('x', encoding='utf8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')

old = R / 'logs/root-five-dimension-joint-v2-progress-20261011'
for b in load(old / 'output-seal.json')['output_members']:
    exact(b)
previous_log = load(old / 'actual-progress.json')
assert previous_log['current_goal_turn_classification'] == 'progress'
assert previous_log['actual_joint_v2']['parent_matches_N'] == 228
receipt_dir = R / '08-audits/joint20-and-batch659-reception-root'
for b in load(receipt_dir / 'output-seal.json')['output_members']:
    exact(b)
receipt = load(receipt_dir / 'actual-reception.json')
exact(receipt['receiver'])
assert receipt['classifier_calls_N'] == 0 and not receipt['formal_metric_acceptance']
assert receipt['source_only_batch_plan']['actual_batch_N'] == 659
assert receipt['joint20_first_execution']['raw_mismatched_dimensions_N'] == 9
hidden = R / '08-audits/five-dimension-joint-v3-independent-sol/preparation-seal.json'
assert bind(hidden)['sha256'] == 'c2f2033647918ae48c2dbea6bd960c1830b9b4588a5f5272787487eae260cec9'
# Bind only the hidden seal; do not open its members, inputs, or expected labels.
handoff_audit = R / '08-audits/human200-handoff-independent-sol/output-seal.json'
assert bind(handoff_audit)['sha256'] == '9e355480ce53a1f17ff08796faa986055adc20d4e8b4a0d7d8a36de697b24a62'
for b in load(handoff_audit)['output_members']:
    exact(b)
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
campaign = R / '06-coding/native-full4481-v1-sol'
selected = sorted(campaign.glob('batch-*/root-selection.json'))
record_N = 0
for p in selected:
    selection = load(p)
    exact(selection['technical_reception'])
    reception = load(selection['technical_reception']['path'])
    assert reception['state'] == 'technical_valid_whole_batch'
    record_N += reception['validation']['record_N']
assert 0 <= record_N <= 4481
observation = dict(observation_started_at=start,
    observation_ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    selected_batch_N=len(selected), technically_receipted_records=record_N,
    not_yet_receipted_records=4481-record_N, exec_session_id=58820,
    last_session_poll_was_running=args.controller_session_running,
    capacity=13, live_snapshot_not_claim_of_atomic_scheduler_state=True,
    partial_machine_labels_read_for_semantic_repair=False,
    full_output_complete_or_accepted=False)
progress = R / 'progress.json'
raw = progress.read_bytes()
state = json.loads(raw)
folder = R / 'logs/root-joint20-and-batch659-progress-20261011'
assert not folder.exists(), 'Do not replace prior progress'
folder.mkdir()
(folder / 'previous-progress.json').write_bytes(raw)
result = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    current_goal_turn_classification='progress', previous_goal_turn_classification='progress_verified',
    verified_previous_log=bind(old / 'actual-progress.json'),
    actual_joint20_and_source_batch659_reception=bind(receipt_dir / 'actual-reception.json'),
    raw_independent20_result=dict(cases=20, matched=15, failed_cases=5,
        raw_dimension_mismatches=9, execution_errors=0, exact_quote_checks=36,
        substantive_problem_dimension_mismatches=8,
        original_expected_S_NULL_vs_actual_known_S1_interpretation_difference=1,
        original_expected_values_and_first_outputs_preserved=True,
        other_missing_standard_request_still_unresolved=True,
        naturally_observed_only_IF_units_N=0),
    joint_v3_interface_repair='In progress on separately fixed developer controls; final candidate not yet received or adopted',
    new_hidden12_preparation=dict(seal=bind(hidden), cases=12,
        ROOT_inputs_or_expected_read=False, candidate_execution_N=0),
    source_only_new_batch_plan=dict(actual_batch_N=659, record_N=4481,
        compact_full_envelope_bytes=123466714, max_batch_bytes=259626,
        historical504_and_4481_parent_inputs_preserved=True,
        candidate_material_adopted=False, model_or_rule_dispatch_N=0,
        provider_context_capacity_verified=False),
    historical200_independent_handoff_audit=dict(seal=bind(handoff_audit),
        control_N=12, matched_N=11, standalone_frame_helper_unapproved_wrapper_issue=True,
        sealed_CLI_bypass_demonstrated=False, actual_human_or_reference_results_N=0),
    dynamic_domain_engine='Separate candidate still pending final seal and ROOT reception; stage-specific helper repair reported; no scope admitted',
    primary_full4481_technical_observation=observation,
    actual_new_human_results_created=0, formal_metric_acceptance=False,
    full_manuscript_revision_started=False, goal_status_remains_active=True,
    remaining_work=['finish the general joint rule repair, seal the candidate, then execute new hidden12 once',
        'receive final dynamic-domain engine candidate without claiming actual project admission',
        'finish historical primary full4481 technical reception before any new-release execution',
        'freeze justified final common materials/versions and eligible validation design; receive actual human results and compute prescribed metrics',
        'revise and verify the full manuscript after method and metric acceptance'])
save(folder / 'actual-progress.json', result)
state['joint20_and_batch659_actual_reception'] = result
state['current_fixed_full4481_execution_observation'] = observation
state['current_goal_turn_classification'] = dict(classification='progress',
    receipt=str(folder / 'actual-progress.json'),
    authoritative_new_outputs='ROOT receipt of retained original independent20 and actual full source659 batch files; general repair continues')
state['updated_at_utc'] = state['last_integration_at'] = result['at_utc']
temp = progress.with_name('progress-joint20-batch659.tmp.json')
save(temp, state)
temp.replace(progress)
save(folder / 'output-seal.json', {'output_members': [bind(p) for p in sorted(folder.iterdir()) if p.is_file()], 'self_excluded': True})
print(json.dumps(dict(log=str(folder / 'actual-progress.json'), selected_batch_N=len(selected),
    technically_receipted_records=record_N, formal_metric_acceptance=False), ensure_ascii=False))
