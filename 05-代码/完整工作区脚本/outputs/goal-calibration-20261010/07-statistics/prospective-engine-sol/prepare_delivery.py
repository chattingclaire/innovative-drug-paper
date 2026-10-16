"""Write only this new engine delivery's template, environment and manifest.
External reads are only the authorized common unknown policy and v2 methods contract.
No real labels, text, frame IDs, model inference or sample selection.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,platform,sys
import numpy,scipy,sklearn

HERE=Path(__file__).resolve().parent
POLICY=HERE.parent.parent/'02-methods'/'unknown-and-denominator-policy.json'
CONTRACT=HERE.parent.parent/'02-methods'/'prospective-statistical-contract-v2'/'validation-design-v2.json'
CONTRACT_NOTE=CONTRACT.parent/'统计契约说明与勘误.md'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(name,value):
    (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--finalize',action='store_true');args=parser.parse_args()
    if not args.finalize:
        (HERE/'inputs').mkdir(exist_ok=True)
        (HERE/'inputs'/'unknown-and-denominator-policy.json').write_bytes(POLICY.read_bytes())
        for source in (CONTRACT,CONTRACT_NOTE):(HERE/'inputs'/source.name).write_bytes(source.read_bytes())
        methods=('A','B','reference','rule','LLM')
        flags=('common_manual','common_materials','design_before_answers','initial_submissions_before_discussion',
               'reference_before_machine_comparison','final_rule_and_LLM_before_test_feedback')
        identities={m:{'kind':'human','identity_code':None,'verified':False,'independent_initial':False} for m in ('A','B')}
        identities['reference']={'kind':'human_adjudication','identity_code':None,'credible':False,'blinded_to_machines':False}
        save('future-input-template.json',{
            'template_status':'NOT_EXECUTABLE_UNTIL_REAL_DESIGN_AND_SEALED_INPUTS_ARE_AVAILABLE',
            'data_role':'sealed_project','metadata':{'analysis_stage':'combined',
                'scope':{'kind':'remaining_1444','population_N':1444,'frame_ids_sha256':None,
                         'note':'Scope example only; final n and assigned IDs not frozen. full_4481_audit is a separate design.'},
                'design':{'kind':'stratified_srswor','sampling_unit':'source_unit','assigned_ids_sha256':None,
                          'strata':[],'note':'Fill fixed positive-pi strata id, department, integer N and n before answers. No final n chosen here.'},
                'identities':identities,
                'statistical_contract_binding':{'version':'v2-preexecution-contract','path':'inputs/validation-design-v2.json',
                    'sha256':sha(CONTRACT),'method_note_sha256':sha(CONTRACT_NOTE),
                    'primary':'common source-unit FPC-rescaled bootstrap percentile95','replicates':5000,'seed':20261010,
                    'secondary':'stratified design covariance and analytic metric gradients/SE diagnostics',
                    'selected_before_real_results':True,'entire_project_final_freeze_completed':False},
                'input_seals':{m:{'sealed':False,'sha256':None,'joined_projection_sha256':None} for m in methods},
                'artifact_seals':{a:{'sealed':False,'sha256':None} for a in ('common_manual','common_materials','design','rule_protocol','LLM_protocol')},
                'freeze_attestations':{f:False for f in flags},'identity_and_source_evidence_reviewed':False},
            'records':[]})
        save('execution-environment.json',{
            'recorded_at_UTC':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
            'Python':sys.version,'python_executable':sys.executable,'Python_binary_sha256':sha(sys.executable),
            'packages':{'numpy':numpy.__version__,'scipy':scipy.__version__,'scikit-learn':sklearn.__version__},
            'engine_runtime_requirements':['Python','numpy','scipy'],'QA_only_requirement':'scikit-learn',
            'existing_environment_reused_read_only':True,'dependencies_installed_or_updated':False,
            'model_instruction':'GPT-6.1 Sol / ultra; no Astra',
            'unknown_policy':{'source_path':str(POLICY),'snapshot':'inputs/unknown-and-denominator-policy.json','sha256':sha(POLICY)},
            'statistical_contract_v2':{'source_path':str(CONTRACT),'snapshot':'inputs/validation-design-v2.json','sha256':sha(CONTRACT),
                'method_note_source_path':str(CONTRACT_NOTE),'method_note_snapshot':'inputs/统计契约说明与勘误.md','method_note_sha256':sha(CONTRACT_NOTE),
                'primary_secondary_chosen_before_real_results':True,'all_project_freezes_completed':False},
            'bootstrap':{'seed':20261010,'synthetic_main_QA_replicates':2000,'synthetic_covariance_check_replicates':60000,
                         'synthetic_CLI_replicates':5000,'quantile_method':'linear'},
            'execution_scope':'synthetic/exhaustive arithmetic and code only; no unsealed project execution'})
    files=[p for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='delivery-manifest.json']
    save('delivery-manifest.json',{
        'created_at_UTC':datetime.now(timezone.utc).isoformat(),'root':str(HERE),
        'status':'ENGINE_PREPARATION_ONLY_NO_REAL_PROJECT_STATISTICS',
        'final_sample_size_frozen':False,'real_sealed_results_executed':False,
        'source_text_or_unsealed_results_read':False,'real_ID_sample_drawn':False,'new_rule_or_LLM_execution':False,
        'file_count':len(files),'excluded':['__pycache__','manifest self hash'],
        'files':[{'path':str(p.relative_to(HERE)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    print(json.dumps({'metadata_status':'written','finalized':args.finalize,'manifest_file_count':len(files)},ensure_ascii=False))
if __name__=='__main__':main()
