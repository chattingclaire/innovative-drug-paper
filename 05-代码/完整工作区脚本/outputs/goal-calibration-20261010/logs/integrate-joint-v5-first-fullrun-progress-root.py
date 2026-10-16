"""Save actual v5 progress, live execution coverage, and unresolved receipt issues."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--native-controller-observed-running', action='store_true')
parser.add_argument('--rule-pid-observed-running', type=int, required=True)
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

previous_dir = R / 'logs/root-joint-v4-rule-repair-progress-20261011'
receive(previous_dir / 'output-seal.json')
previous = load(previous_dir / 'actual-progress.json')
assert previous['current_goal_turn_classification'] == 'progress'
v5_dir = R / '08-audits/joint-v5-and-first-fullrun-reception-root'
receive(v5_dir / 'output-seal.json')
v5 = load(v5_dir / 'actual-reception.json')
assert v5['effective_function_changes_N'] == 5
assert v5['independent_hidden4']['matched_N'] == 4
assert v5['historical_actual_S3']['actual_S'] == [1, 1, 1]
assert not v5['formal_acceptance']
e_dir = R / '08-audits/historical-S3-E-reference-readback-sol'
e_seal = receive(e_dir / 'output-seal.json',
    '1809dce77abac6c65ac7fe2de1558e3e35b23b052a0cd6faca32695b3b750a83', 4, 2)
e_summary = load(e_dir / 'readback.json')['summary']
assert e_summary['A_values'] == e_summary['B_values'] == [1, 1, 1]
assert e_summary['classifier_calls_N'] == e_summary['reference_edits_N'] == 0

campaign = R / '06-coding/native-full4481-v1-sol'
selections = sorted(campaign.glob('batch-*/root-selection.json'))
records = 0
for p in selections:
    selection = load(p)
    exact(selection['technical_reception'])
    reception = load(selection['technical_reception']['path'])
    assert reception['state'] == 'technical_valid_whole_batch'
    records += reception['validation']['record_N']
assert previous['native_full4481_observation']['technically_receipted_records'] <= records <= 4481
native = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    selected_batch_N=len(selections), technically_receipted_records=records,
    not_yet_receipted_records=4481-records, exec_session_id=58820,
    last_session_poll_was_running=args.native_controller_observed_running,
    effective_capacity=13, frozen_original_protocol_capacity=3,
    original_capacity_amended_by_existing_ROOT_transport_controller=True,
    partial_labels_read_for_semantic_repair=False,
    full_output_complete_or_accepted=False,
    live_snapshot_not_atomic_controller_state=True)

run = R / '06-coding/rule-full4481-final-v5-sol'
ledger_path = run / 'run4481-first/execution-ledger.jsonl'
ledger_raw = ledger_path.read_bytes()
rows = []
trailing_partial_line = False
for line in ledger_raw.splitlines():
    try:
        j = json.loads(line)
    except json.JSONDecodeError:
        trailing_partial_line = True
        break
    # Read only execution identity/status; never use labels for further semantic repair.
    rows.append({k: j[k] for k in ('index_1based', 'id', 'at_utc', 'technical_failure')})
assert [j['index_1based'] for j in rows] == list(range(1, len(rows)+1))
assert len({j['id'] for j in rows}) == len(rows)
assert 3 <= len(rows) <= 4481
rule = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    original_scope_record_N=4481, completed_record_prefix_N=len(rows),
    not_yet_recorded_N=4481-len(rows),
    first_prefix_technical_failure_record_N=sum(j['technical_failure'] for j in rows),
    ledger_prefix_bytes=len(ledger_raw), ledger_prefix_sha256=hashlib.sha256(ledger_raw).hexdigest(),
    trailing_partial_line_ignored=trailing_partial_line,
    owner_tool_session_id=32746, observed_OS_pid=args.rule_pid_observed_running,
    ROOT_session_lookup_unavailable_scope_reason='Unknown process id; owner same session and OS pid remain live',
    ROOT_did_not_restart=True, original_v5_and_driver_not_modified=True,
    known_original_strict_ledger_problem='legacy consumer status defaults unresolved when v5 supplies dependency_status resolved',
    known_historical_failure_record_ids=['RECODE25-00036', 'RECODE25-00038', 'RECODE25-00045'],
    diagnostic_outputs_not_retained_labels=True,
    mechanical_receipt_revalidation_candidate_preparation_only=True,
    semantic_reexecution_or_failure_label_backfill_N=0,
    full_first_run_terminal_or_accepted=False,
    neutral_material_GO=False)
result = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    current_goal_turn_classification='progress',
    previous_goal_turn_classification='progress_verified',
    previous_log=bind(previous_dir / 'actual-progress.json'),
    frozen_v5_reception=bind(v5_dir / 'actual-reception.json'),
    independent_hidden4_actual_matches=4,
    independent_hidden4_unique_source_current_bodies_N=3,
    independent_hidden4_nonhuman_not_formal_accuracy=True,
    historical_S3_finite_interface_actual_S=[1, 1, 1],
    historical_S3_first_fullrun_strict_failure_preserved=True,
    finite_interface_validation_not_full_driver_receipt_acceptance=True,
    historical_E_saved_value_readback=dict(seal=e_seal, A_values=[1, 1, 1], B_values=[1, 1, 1],
        matches_observed_v5_E=True, original_values_and_reasons_unchanged=True,
        AI_reason_authorship_note_preserved=True, new_human_E_confirmation_claimed=False),
    common_material_reuse_planning=dict(inner_same_N=3254, inner_changed_N=1227,
        same_ordered_whole_batch_and_inner_material_records_N=420,
        original_run_reused_or_neutral_GO_N=0),
    original_common_fullrule_v5_observation=rule,
    native_full4481_observation=native,
    actual_new_human_results_N=0, formal_metric_acceptance=False,
    new_actual_formal_statistics_stability_or_annual_metrics_N=0,
    complete_manuscript_started=False,
    remaining=['finish the original-material first v5 full rule pass and retain actual failures',
        'independently verify the request-status bridge and possible receipt-only recovery',
        'finish the unchanged primary native full4481 campaign',
        'freeze the final common versions and validate suitable independent human/reference data',
        'complete all required metrics, stability and attention robustness',
        'write and verify the full manuscript after acceptance'],
    integrator=bind(__file__))

progress = R / 'progress.json'
old_progress = progress.read_bytes()
state = json.loads(old_progress)
folder = R / 'logs/root-joint-v5-first-fullrun-progress-20261011'
assert not folder.exists()
folder.mkdir()
def save(p, value):
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
(folder / 'previous-progress.json').write_bytes(old_progress)
save(folder / 'actual-progress.json', result)
save(folder / 'output-seal.json', {'output_members': [bind(folder / 'previous-progress.json'),
    bind(folder / 'actual-progress.json')], 'self_excluded': True})
state['joint_v5_and_first_fullrun_actual_reception'] = result
state['current_fixed_full4481_execution_observation'] = native
state['current_original_common_fullrule_v5_observation'] = rule
state['current_goal_turn_classification'] = 'progress'
state['updated_at_utc'] = result['at_utc']
temp = R / 'progress.joint-v5.tmp.json'
assert not temp.exists()
save(temp, state)
temp.replace(progress)
print(json.dumps(dict(classification='progress', hidden4_matched=4,
    historical_S3_finite_S=[1, 1, 1],
    fullrule_record_prefix_N=len(rows), technical_failures=rule['first_prefix_technical_failure_record_N'],
    native_technical_records=records, native_unreceived=4481-records,
    formal_metric_acceptance=False), ensure_ascii=False))
