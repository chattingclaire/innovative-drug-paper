"""Seal only real, complete 196+25 reconciled development inputs; never run models/statistics."""
from pathlib import Path
import argparse,copy,datetime,hashlib,importlib.util,json,sys
import candidate03_reconciled_execution_profile_v2 as profile
R=Path(__file__).resolve().parent.parent
BASE=R/'methods-20261008/development-complete-bindings/rules-v36.2-development-bindings.json'
BASE_SHA='a00c3dfd743fd2cd30b6a9e56dd55bc90114d595b2e5e49d93916b2d90d4f8e9'
PREP=R/'methods-20261008/candidate03-reconciled-statistics-preparation-v3'
ADAPTER=R/'manuscript-update-20261008/measurement-adapter-v3/assemble_manuscript_payload_r3.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(Path(p).resolve()),'sha256':sha(p)}
def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def require(ok,why):profile.require(ok,why)

def main():
 p=argparse.ArgumentParser();p.add_argument('--full-binding',type=Path,required=True);p.add_argument('--full-binding-sha256',required=True);p.add_argument('--preparation-freeze-sha256',required=True);p.add_argument('--root-confirmed-development',action='store_true');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 require(a.root_confirmed_development,'Root development authorization required; no adoption implied')
 require(not a.out.exists(),'Refuse to overwrite binding directory')
 full_binding={'path':str(a.full_binding.resolve()),'sha256':a.full_binding_sha256}
 full,*_=profile.closed_header(full_binding)  # Before code closure, input/reference/labels.
 require(sha(PREP/'preparation_freeze.json')==a.preparation_freeze_sha256,'Preparation freeze changed')
 frozen=read(PREP/'preparation_freeze.json')
 for b in frozen['required_code_bindings']:require(sha(b['path'])==b['sha256'],'Prepared dependency changed: '+b['path'])
 require(sha(BASE)==BASE_SHA,'Frozen v36.2 base manifest changed')
 spec=importlib.util.spec_from_file_location('reconciled_payload_adapter_v2',ADAPTER);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 io=mod.BoundIO();audit=profile.verify_complete(full_binding,io)
 base=read(BASE);io.tree(base)
 manifest,inputs,llm_inputs,groups,sample,refs=mod.context({'reference_manifest':base['reference_manifest'],'candidate_reference':base['existing_candidate_reference'],'material_version':'v14'},io)
 require(mod.same_binding(full['source_input'],manifest['material']['llm_inputs']),'Source material binding differs')
 rows=io.rows(full['output']);mod.labels(rows,inputs);io.unchanged()
 adapter={'status':profile.ADAPTER_STATUS,'root_confirmed':True,'execution_profile':profile.PROFILE,'output':full['output'],'material_input':full['source_input'],'n':4924,'accepted_request_n':221,'original_production_batches':197,'original_accepted_requests':196,'original_failed_batches':[115],'original_execution_status':'partial_or_failed_preserved','recovery_single_unit_requests':25,'all_checks_pass':True,'all_accepted_requests_first_valid_actual_attempt':True,'all_attempts_retained':True,'exact_actual_requests_verified':True,'zero_tools':True,'actual_prompt_and_runtime_bound':True,'all_rows_reconstructed_exactly':True,'not_candidate02_stability':True,'source_full_binding':full_binding,'technical_QA':full['technical_QA'],'run_plan':full['run_plan'],'execution_summary':full['execution_summary'],'row_provenance':full['row_provenance'],'original_run_QA':full['original_run_QA'],'recovery_QA':full['recovery_QA'],'source_execution_method_id':profile.METHOD,'statistics_frozen_method_id':profile.METHOD,'formal_adoption':False,'independent_validation':False,'all240_exposed':True,'actual_profile_audit':audit,'execution_note':'Original197 protocol remains incomplete (terminal115). Accepted requests196+25 reconstruct full4924; actual unchanged full-five-dimensional rows only. No02 intervals/sensitivity/stability transferred. Adoption remains undecided.'}
 a.out.mkdir(parents=True,exist_ok=False);ap=a.out/'LLM03_reconciled_actual_execution_adapter_v3.json';save(ap,adapter)
 dev=copy.deepcopy(base);dev['authorization']='Root authorized complete reconciled196+25 candidate03 development statistics after real execution/row QA. All240 exposed; adoption undecided.';dev['formal_method_adoption']=False;dev['created_at']=datetime.datetime.now().astimezone().isoformat()
 dev['methods'][profile.STAT_KEY]={'kind':'LLM','frozen_method_id':profile.METHOD,'execution_source_method_id':profile.METHOD,'execution_profile':profile.PROFILE,'material_version':'v14','all240_exposed':True,'execution_adapter':bind(ap),'output':full['output']}
 for b in frozen['required_code_bindings']:dev['statistical_code'][str(Path(b['path']).relative_to(R))]=b
 dev['preparation_freeze']=bind(PREP/'preparation_freeze.json')
 dp=a.out/'rules-v36.2-plus-LLM03-reconciled-development-bindings-v3.json';save(dp,dev)
 save(a.out/'binding_preparation_QA.json',{'status':'PASS_ACTUAL_RECONCILED_EXECUTION_BOUND_DEVELOPMENT_ONLY','all_checks_pass':True,'actual_profile_audit':audit,'source_full_binding':full_binding,'script':bind(__file__),'complete_statistics_bindings':bind(dp),'no_formal_adoption':True,'all_input_bindings':list(io.bindings.values())})
 save(a.out/'output_freeze.json',{'files':{x.name:sha(x) for x in a.out.iterdir() if x.is_file()}})
 print(json.dumps({'status':'actual_reconciled03_inputs_ready_for_development_statistics','bindings':bind(dp),'execution_adapter':bind(ap),'formal_adoption':False},ensure_ascii=False))

if __name__=='__main__':
 try:main()
 except (profile.ProfileGateError,AssertionError,KeyError,TypeError,ValueError,OSError) as exc:
  print(json.dumps({'status':'BLOCKED_NO_BINDINGS_OR_STATISTICS_RELEASED','error':str(exc)},ensure_ascii=False));sys.exit(2)
