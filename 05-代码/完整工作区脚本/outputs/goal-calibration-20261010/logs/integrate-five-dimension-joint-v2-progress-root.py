"""Record actual sealed joint development work and status-only LLM coverage."""
import argparse
import datetime
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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


def save(p, value):
    with p.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


folder = ROOT / 'logs/root-five-dimension-joint-v2-progress-20261011'
assert not folder.exists(), 'Do not replace an actual progress receipt'
coding = ROOT / '06-coding'
joint = coding / 'rule-five-dimension-joint-root/versions/joint-v2-geometry01'
baseline = coding / 'rule-five-dimension-joint-root/versions/merge-baseline01'
IF = coding / 'rule-v20-semantic-audit-repair-sol/versions/v3'
SE = coding / 'rule-v20-SEEconomic-repair-sol/versions/v3-geometry-sol'
independent = ROOT / '08-audits/SEv2-independent43-reception-root'
handoff = ROOT / '07-statistics/human200-machine-reference-handoff-sol'
hidden = ROOT / '08-audits/five-dimension-joint-independent-controls-sol'
for p, key in ((IF / 'delivery-seal.json', 'members'), (SE / 'delivery-seal.json', 'files'),
               (joint / 'pre-execution-seal.json', 'output_members'),
               (joint / 'joint-parent235-root-replay01/output-seal.json', 'output_members'),
               (independent / 'output-seal.json', 'output_members'),
               (handoff / 'output-seal.json', 'output_members')):
    for b in load(p)[key]:
        exact(b)
assert bind(IF / 'delivery-seal.json')['sha256'] == '0c884db46c85466aba46c962128c4967fe58ba3d77801e5771dda3796387fc7c'
assert bind(SE / 'delivery-seal.json')['sha256'] == '018d99cb3412a281bc3d172ba83a2316822acf3567de3bedcba4ec812324a102'
assert bind(hidden / 'preparation-seal.json')['sha256'] == '1a73c900c977bbca792152c06a594982fcaa5bbbd8f63cb0acd4e99274fc88a4'
# ROOT has not opened the hidden cases/expectations. Only bind the preparation seal.
old_log = ROOT / 'logs/root-material-exposure-and-SEv2-reception-20261011.json'
old = load(old_log)
exact(old['current_common_material_and_SEv2_ROOT_reception']['receipt'])
exact(old['future_exposure_registry_prepared']['overlay'])
regression = load(joint / 'IF-original75-root-replay01/summary.json')
parent = load(joint / 'joint-parent235-root-replay01/summary.json')
assert (regression['test_N'], regression['pass_N']) == (75, 75)
assert (parent['case_N'], parent['matched'], parent['exceptions']) == (235, 228, 0)
for b in regression['code_bindings']:
    exact(b)
initial = load(baseline / 'joint-parent235-root-replay01/summary.json')
restored = load(baseline / 'explicit-interface5-root-replay02/summary.json')
assert (initial['case_N'], initial['matched']) == (235, 223)
assert (restored['case_N'], restored['matched']) == (5, 5)

started = datetime.datetime.now(datetime.timezone.utc).isoformat()
campaign = coding / 'native-full4481-v1-sol'
selected = sorted(campaign.glob('batch-*/root-selection.json'))
N = 0
for p in selected:
    selection = load(p)
    exact(selection['technical_reception'])
    reception = load(selection['technical_reception']['path'])
    assert reception['state'] == 'technical_valid_whole_batch'
    N += reception['validation']['record_N']
run = coding / 'full4481-cli-fixed-batch-scheduler-v3-capacity13-root/runs/20261010T155504Z-3e8e5f91'
raw = (run / 'events.jsonl').read_text()
lines = raw.splitlines(keepends=True)
complete_lines = [line for line in lines if line.endswith('\n')]
events = [json.loads(line) for line in complete_lines]
observation = dict(observation_started_at=started,
    observation_ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    selected_batch_N=len(selected), technically_receipted_records=N,
    not_yet_receipted_records=4481-N, controller_run_directory=str(run),
    event_counts=dict(Counter(e['event'] for e in events)),
    final_incomplete_event_line_ignored=len(complete_lines)!=len(lines),
    capacity=13, exec_session_id=58820, last_session_poll_was_running=args.controller_session_running,
    source_manual_prompt_model_request_and_selection_unchanged=True,
    live_snapshot_not_claim_of_atomic_scheduler_state=True,
    partial_machine_labels_read_for_semantic_repair=False, complete_or_accepted=False)
progress = ROOT / 'progress.json'
previous_raw = progress.read_bytes()
previous = json.loads(previous_raw)
folder.mkdir()
with (folder / 'previous-progress.json').open('xb') as stream:
    stream.write(previous_raw)
result = dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    current_goal_turn_classification='progress', previous_goal_turn_classification='progress_verified',
    verified_previous_progress_log=bind(old_log), previous_progress_snapshot=bind(folder / 'previous-progress.json'),
    source_semantic_review_answer_basis=bind(ROOT / '08-audits/ai800-disagreement-semantic-root/complete-review-reception-root/summary.json'),
    sealed_IF_v3=dict(delivery_seal=bind(IF / 'delivery-seal.json'), members_N=173,
                      actual_source_exposure='37 source IDs already in prospective excluded pool; no new eligible IDs exposed'),
    sealed_SE_v3_geometry=dict(delivery_seal=bind(SE / 'delivery-seal.json'), members_N=250,
        algorithm=bind(SE / 'algorithm-bindings.json'), function_diff=bind(SE / 'function-diff.json'),
        retained_differences=bind(SE / 'remaining-boundaries-and-null.json'),
        ROOT_detected_fixture_conflict='same-SHA parent/current byte order contradicts supplied paragraph order; final general guard rejects rather than ignores spans',
        owner_quote_check_N=165, owner_quote_checks_not_independently_received_by_this_log=True,
        real_new_source_IDs_N=0),
    SEv2_independent43_ROOT_reception=bind(independent / 'actual-reception.json'),
    original_joint_baseline=dict(pre_execution_seal=bind(baseline / 'pre-execution-seal.json'),
        original235_summary=bind(baseline / 'joint-parent235-root-replay01/summary.json'),
        original_matched=223, first_loader_omitted_exact5_post_view_operations=True,
        restored5_summary=bind(baseline / 'explicit-interface5-root-replay02/summary.json'),
        only_5_restored_inputs_reexecuted=True, remaining230_not_repeated=True,
        normalized_matched_after_protocol_repair=224, initial_outputs_preserved=True),
    actual_joint_v2=dict(pre_execution_seal=bind(joint / 'pre-execution-seal.json'),
        algorithm=bind(joint / 'algorithm-bindings.json'), function_selection=bind(joint / 'function-selection.json'),
        effective_function_N=116, IF75_summary=bind(joint / 'IF-original75-root-replay01/summary.json'),
        IF_original_developer_controls_N=75, IF_original_developer_matches_N=75,
        parent235_summary=bind(joint / 'joint-parent235-root-replay01/summary.json'),
        parent_cases_N=235, parent_matches_N=228, input_executions_N=211,
        retained_differences_N=7, exceptions_N=0, evidence_validated_N=235,
        remaining_differences='four old closure fixtures, duplicated old closure fixture, foreign unlisted F boundary, inconsistent synthetic payment parent coordinates',
        old_actual_five_geometry_error_types_fixed_on_developer_controls=True,
        fixed_runner=bind(coding / 'replay-joint-parent-controls-v2-root.py'),
        whole77_800_4481_runs=0, new_common_material_projection_used=False, release_or_formal_acceptance=False),
    hidden_independent_joint20=dict(preparation_seal=bind(hidden / 'preparation-seal.json'), controls_N=20,
        ROOT_expected_labels_read=False, actor_execution='delegated after final joint algorithm seal; result not yet received'),
    historical200_handoff=dict(seal=bind(handoff / 'output-seal.json'), members_N=40,
        corrected_wrapper_source='approved_record_ids list obtained only after frozen ordered_source_ids binding is verified',
        actual_human_or_reference_results=0, actual_complete_LLM_campaigns_received=0,
        owner_synthetic_blank_controls_N=30, independent_review_pending=True,
        updated_rule_or_new_domain_formal_acceptance=False),
    prospective_dynamic_domain_engine='preparing ROOT-anchored empty registry; new scopes denied until future ROOT design and release freeze',
    future_common_material_batch_plan='source-only actual plan preparation delegated; no adoption or dispatch',
    primary_full4481_technical_observation=observation,
    actual_new_human_results_created=0, formal_acceptance=False,
    full_manuscript_revision_started=False, goal_status_remains_active=True,
    remaining_work=['receive independent joint20 and historical200 handoff review without changing frozen inputs',
        'finish historical main4481 receipt and retain all original attempts; no stability execution yet',
        'receive source-only new batch plan and dynamic-domain preparation, then freeze justified common material/versions and new sampling design',
        'receive actual targeted human decisions and independent human labels/adjudication, compute all prescribed metrics with eligible weights and intervals',
        'only after method and metric acceptance revise and render the complete manuscript'])
save(folder / 'actual-progress.json', result)
previous['five_dimension_joint_v2_actual']=result
previous['current_fixed_full4481_execution_observation']=observation
previous['current_goal_turn_classification']=dict(classification='progress', receipt=str(folder / 'actual-progress.json'),
    authoritative_new_outputs='sealed IFv3 + SEv3, actual root joint v2 and preserved finite test results; independent checks and formal human/results pending')
previous['last_integration_at']=result['at_utc']
previous['updated_at_utc']=result['at_utc']
tmp=progress.with_name('progress-joint-v2.tmp.json')
save(tmp,previous)
tmp.replace(progress)
save(folder / 'output-seal.json', {'output_members': [bind(p) for p in sorted(folder.iterdir()) if p.is_file()], 'self_excluded':True})
print(json.dumps(dict(log=str(folder / 'actual-progress.json'), joint_developer_case_N=235,
    joint_matches_N=228, selected_batches=len(selected), technically_receipted_records=N,
    formal_acceptance=False),ensure_ascii=False))
