"""Append actual candidate reception, exposure accounting and technical coverage."""
import datetime
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads(Path(path).read_text())
def bind(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def exact(item): assert bind(item['path'])=={k:item[k] for k in ('path','bytes','sha256')}, item['path']
def save(path,obj):
    with path.open('x',encoding='utf8') as handle:
        json.dump(obj,handle,ensure_ascii=False,indent=2);handle.write('\n')

material=ROOT/'08-audits/material-and-SEv2-reception-root'
exposure=ROOT/'02-methods/prospective-exposure-refresh-root'
for folder in (material,exposure):
    for item in load(folder/'output-seal.json')['output_members']:exact(item)
inputs=load(exposure/'input-bindings.json')
for item in inputs['inputs']+inputs['real_material_bindings']:exact(item)
actual=load(material/'actual-reception.json')
overlay=load(exposure/'future-development-exposure-overlay.json')
coding=ROOT/'06-coding';campaign=coding/'native-full4481-v1-sol'
started_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
selected=sorted(campaign.glob('batch-*/root-selection.json'));N=0
for path in selected:
    selection=load(path);exact(selection['technical_reception'])
    receipt=load(selection['technical_reception']['path'])
    assert receipt['state']=='technical_valid_whole_batch'
    N+=receipt['validation']['record_N']
scheduler=coding/'full4481-cli-fixed-batch-scheduler-v3-capacity13-root'
run=max((scheduler/'runs').iterdir(),key=lambda p:p.name)
events=[json.loads(line) for line in (run/'events.jsonl').read_text().splitlines()]
event_counts=dict(Counter(e['event'] for e in events))
assert run.name=='20261010T155504Z-3e8e5f91'
progress_path=ROOT/'progress.json'
previous=load(progress_path)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
log=ROOT/'logs/root-material-exposure-and-SEv2-reception-20261011.json'
result=dict(at_utc=now,current_goal_turn_classification='progress',
    source_semantic_review_answer_basis=bind(ROOT/'08-audits/ai800-disagreement-semantic-root/complete-review-reception-root/summary.json'),
    current_common_material_and_SEv2_ROOT_reception=dict(receipt=bind(material/'actual-reception.json'),seal=bind(material/'output-seal.json'),common_candidate=actual['common_material'],SE_Ec_candidate=actual['SE_Ec_v2']),
    reception_receiver_schema_attempts_preserved=dict(attempts_directory=str(ROOT/'08-audits/material-and-SEv2-reception-attempts-root'),technical_failures=2,causes=['context identity field is context_id','84quotes include46real+38synthetic'],candidate_or_original_mutations=False,classifier_reruns=0),
    future_exposure_registry_prepared=dict(seal=bind(exposure/'output-seal.json'),overlay=bind(exposure/'future-development-exposure-overlay.json'),counts=overlay['counts'],historical200_weights_domain_originals_preserved=True,new_human_draws=0,new_contract_or_formal_release=False,subsequent_semantic_reads_need_future_update=True),
    primary_full4481_technical_observation=dict(observation_started_at=started_at,observation_ended_at=now,selected_batch_N=len(selected),technically_receipted_records=N,not_yet_receipted_records=4481-N,controller_run_directory=str(run),event_counts=event_counts,capacity=13,exec_session_id=58820,last_session_poll_was_running=True,source_manual_prompt_model_request_and_selection_unchanged=True,live_snapshot_not_claim_of_atomic_scheduler_state=True,partial_machine_labels_read_for_semantic_repair=False,complete_or_accepted=False),
    parallel_work=dict(IF_v3='owner reports75original controls matched,31/32finite controls with foreign NULL boundary retained; final seal pending',SE_v2_independent='delegated new finite independent audit after owner seal; not yet received',human200_adapter='preparing machine-reference/combined and annual entries; true human/reference/version gates, old snapshot only; actual results0'),
    actual_human_results_created=0,formal_acceptance=False,full_manuscript_revision_started=False,goal_status_remains_active=True,
    adjusted_execution_dependency='Final new-rule independent sampling must freeze updated exposure domains before a new design; do not relabel historical200 and reuse its oldweights. Existing1444/3037 engine and results retain old version bindings.',
    remaining_work=['receive independent SEv2 review and sealed IFv3; merge exact five-dimension interfaces and validate actual joint candidate','finish receiving unchanged historical primary4481 and retain all outputs; no stability runs yet','freeze new common material and classifier versions, correct batch assignment and future independence registry before any new version deployment','receive genuine targeted boundary decisions, independent human initials and blinded adjudication; compute all prescribed metrics and confidence intervals for eligible versions','after methodological and metric acceptance, revise and render the complete paper'],
    previous_progress_binding=bind(progress_path))
save(log,result)
previous['material_exposure_and_SEv2_reception_actual']=result
previous['current_fixed_full4481_execution_observation']=result['primary_full4481_technical_observation']
previous['current_goal_turn_classification']=dict(classification='progress',receipt=str(log),authoritative_new_outputs='ROOT received independent material audit and sealed SEv2; prepared future source-only exposure frame and historical200 impact without newdraw or label changes')
previous['last_integration_at']=now;previous['updated_at_utc']=now
tmp=progress_path.with_name('progress-material-exposure-SEv2.tmp.json')
save(tmp,previous);tmp.replace(progress_path)
print(json.dumps(dict(log=str(log),selected_batches=len(selected),records=N,remaining=4481-N,candidate_domains=overlay['counts']['candidate_domains'],new_independent_validation_accepted=False),ensure_ascii=False))
