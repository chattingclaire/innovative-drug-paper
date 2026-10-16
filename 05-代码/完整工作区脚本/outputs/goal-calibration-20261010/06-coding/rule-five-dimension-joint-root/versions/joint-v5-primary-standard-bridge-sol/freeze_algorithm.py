from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).resolve().parent
def load(p):return json.loads(Path(p).read_text())
def bind(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def dump(name,x):
 p=P/name;assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return bind(p)
def verify(b):assert bind(b['path'])==b,b['path']
b=load(P/'input-bindings.json');c=load(P/'control-pre-edit-seal.json')
for z in [b['manual'],b['baseline_delivery_seal'],b['baseline_algorithm'],b['baseline_preseal'],b['actual_S3_baseline_seal'],c['controls']]+b['baseline_five_modules']+b['common_frozen_input_bindings']:verify(z)
modules=[bind(P/(n+'.py')) for n in ['source_packet','source_receipts','evidence','relations','dimensions']]
for z in modules:
 n=Path(z['path']).name;assert (P/n).read_bytes()==(P/'final02-parent235/code-snapshot'/n).read_bytes()==(P/'final02-original75/code-snapshot'/n).read_bytes()==(P/'attempt04-controls6/code-snapshot'/n).read_bytes()
for n in ['source_packet','source_receipts','evidence']:assert (P/(n+'.py')).read_bytes()==(P/'baseline-code-snapshot'/(n+'.py')).read_bytes()
case=load(P/'attempt04-controls6/results.json');fixed=load(P/'controls6-fixed-before-edit.json')['cases'];assert all(x['expected']==y['expected'] and x['semantic_input']==y['synthetic_input'] for x,y in zip(case,fixed));assert all(x['passed'] for x in case)
at=datetime.datetime.now(datetime.timezone.utc).isoformat()
alg=dump('algorithm-bindings.json',dict(status='sealed_joint_v5_development_candidate_not_deployed',identity='nonhuman GPT-6.1 Sol ultra developer candidate',at_utc=at,five_modules=modules,baseline_delivery_seal=b['baseline_delivery_seal'],baseline_algorithm=b['baseline_algorithm'],baseline_preseal=b['baseline_preseal'],manual=b['manual'],definition_changes=False,common_frozen_input_bindings=b['common_frozen_input_bindings'],pre_fixed_controls=bind(P/'controls6-fixed-before-edit.json'),control_pre_edit_seal=bind(P/'control-pre-edit-seal.json'),actual_S3_baseline_seal=b['actual_S3_baseline_seal'],actual_S3_development_inputs=[x['source_packet'] for x in b['actual_S3_development_baseline']],actual_S3_candidate_execution_performed_by_owner=False,development_S3_material_candidate_not_adopted_as_formal_release=True,new_source_reader_or_neutral_projection=False,source_packet_receipts_evidence_unchanged=True,shared_add_generic_judge_consumer_intersection_unchanged=True,shared_units_only_original_quote_range_boundary_filter_changed=True,new_SE_bridge_is_typed_S_E_Ec_only=True,old_cited_standard_not_unconditionally_allowed=True,EOF_not_closure=True,independent_hidden4_read=False,main_LLM_partial_labels_read=False,cohort77_800_4481_run=False,actual_sources_read_only_authorized_S3=['RECODE25-00036','RECODE25-00038','RECODE25-00045'],actual_sources_new_outside_authorized_S3=[],code_frozen_before_independent_hidden4_and_actual_S3_execution=True,code_will_not_change_after_new_results=True))
pre=dump('pre-execution-seal.json',dict(status='final_algorithm_frozen_before_independent_hidden4_and_actual_S3',identity='nonhuman developer algorithm freeze after finite exposed regressions',at_utc=at,algorithm_bindings=alg,five_modules=modules,manual=b['manual'],baseline_delivery_seal=b['baseline_delivery_seal'],common_frozen_input_bindings=b['common_frozen_input_bindings'],fixed_control_pre_edit_seal=bind(P/'control-pre-edit-seal.json'),actual_S3_baseline_seal=b['actual_S3_baseline_seal'],actual_S3_inputs=[x['source_packet'] for x in b['actual_S3_development_baseline']],owner_executed_actual_S3_candidate=False,independent_hidden4_read=False,post_independent_algorithm_edit_allowed=False,delivery_documentation_may_be_added_without_algorithm_change=True))
for z in [alg,pre]+modules:verify(z)
print(json.dumps(dict(algorithm=alg,preseal=pre,modules=modules),ensure_ascii=False,indent=2))
