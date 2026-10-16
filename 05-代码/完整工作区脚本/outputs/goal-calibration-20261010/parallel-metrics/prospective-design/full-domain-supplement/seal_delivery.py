"""Seal only this new full-domain planning directory, checking prior preservation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):(HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    binding=json.loads((HERE/'source-bindings.json').read_text())
    preservation=[]
    for f,expected in binding['inputs'].items():
        path=Path(f);actual=sha(path)
        if actual!=expected['sha256'] or path.stat().st_size!=expected['bytes']:raise ValueError('Earlier input/delivery changed: '+f)
        preservation.append({'path':f,'sha256':actual,'unchanged':True})
    qa=json.loads((HERE/'full-domain-QA.json').read_text())
    if qa['status']!='passed' or qa['main_script_sha256']!=sha(HERE/'full_domain_plan.py') or qa['comparison_sha256']!=sha(HERE/'full-domain-comparison.json'):
        raise ValueError('QA does not bind the final current implementation/comparison')
    save('old-inputs-and-600-preservation.json',{'status':'all_permitted_old_input_and_600_delivery_hashes_unchanged',
        'files':preservation,'new_writes_only_in':str(HERE),'remaining_plan_N':1444,'remaining_plan_n':600})
    save('execution-environment.json',{'date':'2026-10-10',**qa['environment'],
        'existing_environment_reused':True,'dependencies_installed':False,
        'model':'GPT-6.1 Sol','reasoning_effort':'ultra','actual_sample_or_new_model_execution':False})
    files=[p for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='delivery-manifest.json']
    save('delivery-manifest.json',{'date':'2026-10-10','created_at_UTC':datetime.now(timezone.utc).isoformat(),
        'root':str(HERE),'status':'PREANSWER_DESIGN_COMPARISON_ONLY_NOT_SELECTED_OR_IMPLEMENTED',
        'population_N':4481,'candidate_total_n':[800,1000],'fixed_remaining_N_n':[1444,600],'candidate_exposed_N_n':[[3037,200],[3037,400]],
        'actual_ID_draw_or_sampling_seed_selected':False,'unseen_body_context_real_reference_read':False,
        'new_machine_inference':False,'new_reference_labels':False,'new_CI_goal_or_threshold':False,
        'file_count':len(files),'excluded':['__pycache__','manifest self hash'],
        'files':[{'path':str(p.relative_to(HERE)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    print(json.dumps({'status':'planning_delivery_sealed','files':len(files),'prior_inputs_verified':len(preservation),'QA_checks':qa['check_count']},ensure_ascii=False))
if __name__=='__main__':main()
