"""Seal code/toy-only delivery after reviews complete; no project execution."""
from pathlib import Path
import hashlib, json, platform, subprocess, sys
import numpy, scipy

ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/name).read_text())
def write(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

subprocess.run([sys.executable,'-B',str(ROOT/'verify_preservation.py')],check=True,capture_output=True)
main=read('domain-regression-results.json')
mi=read('independent-math/independent_domain_interface_results.json')
mm=read('independent-math/independent_domain_mask_results.json')
it=read('independent-interface/main-domain-interface-results.json')
cli=read('toy-small-defaults.cli.output.json')
schema=read('independent-interface/full-plan-schema-projection.json')
source_sha=digest(ROOT/'metrics_engine.py')
assert main['engine_sha256']==it['engine_sha256']==cli['execution_provenance']['engine_sha256']==source_sha
assert mi['input_bindings_sha256'][str(ROOT/'metrics_engine.py')]==source_sha
assert all(c['pass'] for c in main['checks']) and mi['all_passed'] and mm['all_passed']
assert it['source_hash_stable_during_dynamic_checks'] is True and it['replicate_weight_generation_call_count']==1
assert it['formal_acceptance'] is False and cli['project_review']['formal_acceptance'] is False
assert cli['design']['bootstrap_replicates']==5000 and cli['design']['seed']==20261010
for plan in ('full800','full1000'):
    output=read(plan+'-synthetic-schema.output.json')
    assert output['data_role']=='synthetic' and output['project_review']['formal_acceptance'] is False
    assert output['design']['bootstrap_replicates']==5000 and output['design']['seed']==20261010

environment={'python':sys.version,'python_executable':sys.executable,'numpy':numpy.__version__,'scipy':scipy.__version__,
 'platform':platform.platform(),'engine_sha256':source_sha,'previous_source_sha256':digest(ROOT/'old_engine_source_frozen.py'),
 'full_domain_allocation_metadata_source_sha256':schema['source_sha256'],
 'N_n_schema_projection_sha256':digest(ROOT/'independent-interface/full-plan-schema-projection.json'),
 'real_source_or_prediction_inputs_read':0,'dependency_installations':0}
write('environment-and-provenance.json',environment)
summary={'status':'code_and_synthetic_domain_interface_round_complete','engine_schema_version':'1.1','engine_sha256':source_sha,
 'previous_source_sha256':environment['previous_source_sha256'],
 'old_directory_preservation':read('old-version-preservation-final.json'),
 'shared_complete_unit_W':{'generation_count_per_probability_analyze':1,'default_B':5000,'default_seed':20261010,
    'views':['ALL','remaining','exposed','department','nonempty domain x department']},
 'QA':{'main_regression_checks':main['check_count'],'independent_math_checks':mm['check_count'],
       'independent_engine_math_interface_checks':mi['check_count'],
       'independent_metadata_cases':len(it['interface_validation_cases'])+len(it['extra_named_metadata_cases']),
       'independent_mask_checks':len(it['mask_and_weight_checks']),
       'independent_legacy_compatibility_checks':len(it['legacy_compatibility_checks']),
       'default_CLI_B5000_seed_verified':True,'all_reports_bind_final_source':True},
 'full41_schema_only_toys':main['full_schema_toys'],
 'real_project_executions':0,'real_ID_draws':0,'real_human_or_AI_new_labels_read':0,'real_source_bodies_read':0,
 'people_arranged':False,'formal_acceptance':False,'metadata_authenticates_human_identity':False,
 'finite_joint16_nonlinear_metric_projection_implemented':False,
 'analytic_covariance_role':'diagnostics_only','point_or_CI_acceptance_gates_added':False,
 'old_remaining_n600_allocation_modified':False,
 'limitations':['Toy QA is not real project validation','Identity/source/manual/reference/freezes require external evidence review',
   'Finite guards have no joint coverage across views or45 metrics','Strict joint16 nonlinear metric projection remains unimplemented']}
write('delivery-summary.json',summary)
files=[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size}
       for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='delivery-manifest.json' and '__pycache__' not in p.parts]
manifest={'status':'sealed_code_and_synthetic_toys_only','engine_sha256':source_sha,'file_count':len(files),
          'excluded':['delivery-manifest.json','__pycache__'],'files':files,'formal_acceptance':False,'real_project_executions':0}
write('delivery-manifest.json',manifest)
print(json.dumps({'status':summary['status'],'QA':summary['QA'],'sealed_files':len(files),'source_sha256':source_sha},ensure_ascii=False))
