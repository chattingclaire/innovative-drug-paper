"""Seal development-only inputs after the actual candidate03 full execution QA.
This script does not run a model, compute statistics, adopt a method, or write DOCX.
"""
from pathlib import Path
import argparse,copy,importlib.util,json,hashlib,datetime

R=Path(__file__).resolve().parent.parent
BASE=R/'methods-20261008/development-complete-bindings/rules-v36.2-development-bindings.json'
BASE_SHA='a00c3dfd743fd2cd30b6a9e56dd55bc90114d595b2e5e49d93916b2d90d4f8e9'
ORIGINAL_DRIVER_SHA='20653602caff956d8fade50071e3ec15c4655e65a0b715f22983abee04290f3b'
PREP=R/'methods-20261008/candidate03-complete-statistics-preparation'
ADAPTER=R/'manuscript-update-20261008/measurement-adapter/assemble_manuscript_payload_r3.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(Path(p).resolve()),'sha256':sha(p)}
def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main():
 p=argparse.ArgumentParser();p.add_argument('--full-binding',type=Path,required=True);p.add_argument('--full-binding-sha256',required=True);p.add_argument('--preparation-freeze-sha256',required=True);p.add_argument('--root-confirmed-development',action='store_true');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert a.root_confirmed_development,'Root development authorization required; no method adoption is implied'
 assert not a.out.exists(),'Do not replace an earlier binding directory'
 assert sha(a.full_binding)==a.full_binding_sha256
 full=read(a.full_binding)
 assert full['status']=='complete_actual_full_corpus_development_comparison_QA_PASS' and full['n']==4924 and full['batches']==197,'Do not read an incomplete run'
 assert full['formal_adoption'] is False and full['independent_validation'] is False and full['all_240_exposed_development'] is True
 assert sha(PREP/'preparation_freeze.json')==a.preparation_freeze_sha256
 frozen=read(PREP/'preparation_freeze.json')
 for b in frozen['required_code_bindings']:assert sha(b['path'])==b['sha256'],b['path']
 assert sha(BASE)==BASE_SHA and sha(R/'statistics/run_development_complete_statistics_r3.py')==ORIGINAL_DRIVER_SHA
 spec=importlib.util.spec_from_file_location('readonly_measurement_adapter',ADAPTER);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 io=mod.BoundIO();io.verify({'path':str(a.full_binding.resolve()),'sha256':a.full_binding_sha256});io.tree(full)
 base=read(BASE);io.tree(base)
 context_cfg={'reference_manifest':base['reference_manifest'],'candidate_reference':base['existing_candidate_reference'],'material_version':'v14'}
 manifest,inputs,llm_inputs,groups,sample,refs=mod.context(context_cfg,io)
 rows=io.rows(full['output']);assert len(rows)==4924;mod.labels(rows,inputs)
 mod.execution({'method_id':full['method_id'],'execution_profile':'LLM03_full_execution','output':full['output'],'execution_binding':{'path':str(a.full_binding.resolve()),'sha256':a.full_binding_sha256}},'LLM',manifest,io,rows)
 qa=io.json(full['technical_QA']);lineage=io.rows(full['row_provenance'])
 assert qa['actual_prompt_sha256']==full['prompt']['sha256']
 assert all(x['actual_prompt_sha256']==full['prompt']['sha256'] for x in lineage.values())
 assert all(x['requested_model']=='gpt-5.6-sol' and x['reasoning_effort']=='medium' for x in lineage.values())
 io.unchanged()
 adapter={'status':'passed_candidate03_full_actual_execution_and_binding_QA','root_confirmed':True,'output':full['output'],'material_input':full['source_input'],'n':4924,'batch_n':197,
  'all_checks_pass':True,'all197_batches_first_valid_actual_attempt':True,'all_attempts_retained':True,'exact_actual_requests_verified':True,'zero_tools':True,'actual_prompt_and_runtime_bound':True,'all_rows_reconstructed_exactly':True,'not_candidate02_stability':True,
  'source_full_binding':{'path':str(a.full_binding.resolve()),'sha256':a.full_binding_sha256},'technical_QA':full['technical_QA'],'run_plan':full['run_plan'],'execution_summary':full['execution_summary'],'row_provenance':full['row_provenance'],
  'source_execution_method_id':full['method_id'],'statistics_frozen_method_id':'LLM-candidate03-development','formal_adoption':False,'independent_validation':False,'all240_exposed':True,
  'execution_note':'Actual full execution/row QA verified before this adapter was written. No candidate02 CI, definition/composition sensitivity or stability evidence is substituted. Stability is a separate actual experiment.'}
 a.out.mkdir(parents=True,exist_ok=False);adapter_path=a.out/'LLM03_actual_execution_adapter.json';save(adapter_path,adapter)
 dev=copy.deepcopy(base);dev['authorization']='Root authorized complete candidate03 development statistics after actual full execution closure and binding QA; adoption remains undecided. All240 exposed.'
 dev['formal_method_adoption']=False;dev['created_at']=datetime.datetime.now().astimezone().isoformat()
 dev['methods']['LLM-candidate03']={'kind':'LLM','frozen_method_id':'LLM-candidate03-development','execution_source_method_id':full['method_id'],'material_version':'v14','all240_exposed':True,'execution_adapter':bind(adapter_path),'output':full['output']}
 for b in frozen['required_code_bindings']:dev['statistical_code'][Path(b['path']).name]=b
 dev['preparation_freeze']=bind(PREP/'preparation_freeze.json')
 devpath=a.out/'rules-v36.2-plus-LLM03-development-bindings.json';save(devpath,dev)
 save(a.out/'binding_preparation_QA.json',{'status':'PASS_ACTUAL_FULL_EXECUTION_BOUND_DEVELOPMENT_ONLY','n':4924,'batch_n':197,'all_checks_pass':True,'source_full_binding':adapter['source_full_binding'],'script':bind(__file__),'complete_statistics_bindings':bind(devpath),'actual_method_outputs':{k:v['output'] for k,v in dev['methods'].items()},'no_formal_adoption':True,'all_input_bindings':list(io.bindings.values())})
 save(a.out/'output_freeze.json',{'files':{x.name:sha(x) for x in a.out.iterdir() if x.is_file()}})
 print(json.dumps({'status':'actual_full03_inputs_ready_for_development_statistics','bindings':bind(devpath),'execution_adapter':bind(adapter_path),'formal_adoption':False},ensure_ascii=False))

if __name__=='__main__':main()
