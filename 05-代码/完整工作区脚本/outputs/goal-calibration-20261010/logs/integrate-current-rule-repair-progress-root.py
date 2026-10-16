"""Append actual progress without rewriting any previous coding or receipt."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
now=datetime.datetime.now(datetime.timezone.utc).isoformat()

def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def load(p):return json.loads(Path(p).read_text())

def exact(item):assert bind(item['path'])=={k:item[k]for k in('path','bytes','sha256')},item['path']

def save(p,v):
    with Path(p).open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

coding=ROOT/'06-coding';scheduler=coding/'full4481-cli-fixed-batch-scheduler-v3-capacity13-root'
recovery=scheduler/'ROOT-runtime-reception-recovery-01';GO=scheduler/'ROOT-runtime-GO-02'
for directory in(recovery,GO):
    for item in load(directory/'output-seal.json')['output_members']:exact(item)
candidate=ROOT/'03-manual/common-material-projection-candidate-root'
for item in load(candidate/'output-seal.json')['output_members']:exact(item)
audits={}
for name in('SE-Ec-repair-independent-controls-sol','IF-v2-independent-controls-sol'):
    directory=ROOT/'08-audits/independent-rule-control-reception-root'/name
    for item in load(directory/'output-seal.json')['output_members']:exact(item)
    actual=load(directory/'actual-reception.json')
    audits[name]={'receipt':bind(directory/'actual-reception.json'),'counts':actual['counts_recomputed_from_all20'],'manual_quote_N':actual['exact_manual_quote_N'],'formal_acceptance_or_human_results_created':False}
IFseal=coding/'rule-v20-semantic-audit-repair-sol/delivery/delivery-seal.json';IFS=load(IFseal)
for key in('v2_code','delivery_artifacts'):
    for item in IFS[key]:exact(item)
for key in('v2_algorithm_manifest','v1_pre_run_seal'):exact(IFS[key])
campaign=coding/'native-full4481-v1-sol'
selections=sorted(campaign.glob('batch-*/root-selection.json'));records=0
for path in selections:
    selection=load(path);exact(selection['technical_reception']);received=load(selection['technical_reception']['path'])
    assert received['state']=='technical_valid_whole_batch';records+=received['validation']['record_N']
latest=max((scheduler/'runs').iterdir(),key=lambda p:p.stat().st_mtime)
events=[json.loads(line)for line in(latest/'events.jsonl').read_text().splitlines()]
started=[e['batch']for e in events if e['event']=='runner_started']
diagnostics=[e for e in events if e['event']=='stop_new_dispatch_root_inspection_required']
assert latest.name!='20261010T153845Z-6ef4c40a' and started[:13]==list(range(67,80))
progress_file=ROOT/'progress.json';previous=load(progress_file)
log=ROOT/'logs/root-rule-independent-controls-and-runtime-recovery-20261010.json'
receipt={'at_utc':now,'current_goal_turn_classification':'progress','user_question_answer_basis':'source-based278 semantic developer audit identifies230 suggested rule omissions21 suggested excess inclusions7 auxiliaryAI errors20pending; not formal accuracy','primary_full4481_actual':{'selected_batch_N':len(selections),'technically_receipted_records':records,'not_yet_receipted_records':4481-records,'previous_exec_session20456_terminal_exit2_observed_by_ROOT':True,'local_failure':'bundled Python could not import jsonschema in receiver before receipt creation','existing13terminal_outputs_recovered_without_model_retry':13,'runtime_recovery':bind(recovery/'summary.json'),'pre_dispatch_GO':bind(GO/'pre-dispatch-runtime-GO.json'),'resumed_exec_session_id':58820,'resumed_capacity':13,'new_controller_run_directory':str(latest),'actual_new_unused_batch_starts':started,'diagnostic_N_so_far':len(diagnostics),'selection_or_gold_labels_read_for_semantic_repair':False,'prompt_model_manual_sources_core_and_selection_unchanged':True,'full_complete_or_accepted':False},'independent_rule_controls_ROOT_received':audits,'IF_v2_delivery_byte_checks':{'seal':bind(IFseal),'actual_v2_whole77_800_runs':0,'v2_targeted_regression_owner75_passed':'owner delivery report; separate independent20 produces7differences10dims','next_repair':'independent versions/v3 authorized for6 executed type groups and real structural boundary controls; foreign NULL handcoded boundary preserved'},'SEEconomic_v2_status':'owner currently implementing frozen independent control errors and closing whole-article/member scope; not sealed or adopted','five_dimension_merge_interface':'owner static comparison137 effectivefunctions42constants, overlapping __init__/_generic/judge; SEv2 changed afterward so snapshot not release binding','common_source_only_candidate_prepared':{'seal':bind(candidate/'output-seal.json'),'summary':bind(candidate/'summary.json'),'records':4481,'records_with_new_literal_resources':1227,'same_version_original_copies':17,'equal_role_packet_inventory':bind(candidate/'equal-visibility-role-bindings.json'),'new_source_record_or_old_resource_prefix_changes':0,'actual_release_coding_or_new_human_results':0,'old_primary_or_old_human_inputs_changed':False,'independent_readback_and_real_budget_check_delegated':True,'pretty_JSON_byte_size_not_assumed_to_be_the_actual_batch_budget_measure':True},'human_targeted35_original_delivery_unchanged':{'slots':35,'records':34,'actual_new_human_calibration_results_received':0},'formal_acceptance':False,'full_manuscript_revision_started':False,'goal_status_remains_active':True,'remaining_work':['complete general v3 I/F and v2 SE/Ec repairs, inspect shared interfaces, seal and actually validate joint5dim version','receive remainder of unchanged current primary4481 whole batches; independent stability not started','inspect common material candidate and future common release/budgets/exposure before any new version execution','receive actual targeted boundary decisions and human independent smaller-sample results, then frozen formal metrics/intervals and annual analysis','only after coding and prescribed metrics are accepted, revise and render the complete paper'],'previous_progress_binding':bind(progress_file)}
save(log,receipt)
previous['rule_independent_controls_and_runtime_recovery_actual']=receipt
previous['current_fixed_full4481_execution_observation']=receipt['primary_full4481_actual']
previous['current_goal_turn_classification']={'classification':'progress','authoritative_new_outputs':'received40 independent controls and all quoted bounds; recovered13 existing primary outputs;595/4481 received and13 fresh batches resumed; prepared equal4481 material candidate without label changes','receipt':str(log)}
previous['last_integration_at']=now;previous['updated_at_utc']=now
temporary=progress_file.with_name('progress-current-integration.tmp.json')
save(temporary,previous);temporary.replace(progress_file)
print(json.dumps({'log':str(log),'primary_selected_batches':len(selections),'primary_received_records':records,'actual_unused_new_batch_starts':started,'diagnostics':len(diagnostics),'formal_acceptance':False},ensure_ascii=False))
