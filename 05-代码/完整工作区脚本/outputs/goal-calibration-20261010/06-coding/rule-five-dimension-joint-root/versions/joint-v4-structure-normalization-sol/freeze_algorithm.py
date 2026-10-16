from pathlib import Path
import json, hashlib, datetime
ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
P=ROOT/'06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol'
BASE=P.parent/'joint-v3-interface-sol'
A=ROOT/'08-audits/five-dimension-joint-v3-independent-sol'
E=A/'execution-joint-v3-interface-sol'
def bind(p):
 p=Path(p); b=p.read_bytes(); return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def verify(b):
 assert bind(b['path'])==b, b['path']
def dump(name,x):
 q=P/name; assert not q.exists(),str(q); q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n'); return bind(q)
at=datetime.datetime.now(datetime.timezone.utc).isoformat()
baseline=json.loads((P/'baseline-input-bindings.json').read_text())
for b in [baseline['baseline_delivery_seal'],baseline['baseline_preseal'],baseline['baseline_algorithm'],baseline['manual']]+baseline['baseline_modules']+baseline['common_frozen_input_bindings']:verify(b)
s=bind(E/'output-seal.json');assert s['sha256']=='2e5c1426b344b52d5bac000462b776729a7b471b15a03c304d094f88eb132cc3'
audit=json.loads(Path(s['path']).read_text()); members=audit['output_members']
for b in members: verify(b)
control=bind(A/'controls12-fixed-before-execution.json');assert control['sha256']=='c1f92442c436404922b792f25286911dbe9456962fa362f814402b2925eeadce'
prepare=bind(A/'preparation-seal.json');assert prepare['sha256']=='c2f2033647918ae48c2dbea6bd960c1830b9b4588a5f5272787487eae260cec9'
failures=bind(E/'failure-full-inputs-and-paths.json');assert failures['sha256']=='50a79e9ddef205fe7a0ef78dc473a432677f9529ca43174271e39605a1878405'
reception=dump('exposed12-reception-bindings.json',{'identity':'nonhuman developer reception of already exposed original 12','at_utc':at,'output_seal':s,'verified_output_member_N':len(members),'all_member_bindings':members,'controls':control,'preparation_seal':prepare,'failure_full_inputs':failures,'first_failed_process_storage_loss_preserved':True,'authorized_attempt02_only_runner_capture_repair':True,'original_v3_construction_exceptions':3,'original_v3_numeric_mismatches':3,'original_v3_matched':6,'attempt02_is_not_original_first_execution':True,'expected_unchanged':True,'new_v4_hidden_controls_read':False,'historical_actual_S3_plan_read':False})
modules=[bind(P/f'{n}.py') for n in ['source_packet','source_receipts','evidence','relations','dimensions']]
final75=json.loads((P/'final-original75/summary.json').read_text())
assert modules==final75['code_bindings'][:5]
for n in ['source_packet','source_receipts','evidence']:
 assert (P/f'{n}.py').read_bytes()==(BASE/f'{n}.py').read_bytes()
controls=[bind(P/x) for x in ['controls6-fixed-before-edit.json','control-pre-edit-seal.json','controls2-numbering-positive-fixed.json','controls6-semantic-fixed-before-edit.json','additional-control-pre-edit-seal.json']]
alg=dump('algorithm-bindings.json',{'status':'sealed_joint_v4_developer_candidate_not_formal_release_or_deployment','identity':'nonhuman AI development candidate GPT-6.1 Sol ultra','at_utc':at,'five_modules':modules,'manual':baseline['manual'],'definition_changes':False,'common_frozen_input_bindings':baseline['common_frozen_input_bindings'],'baseline_delivery_seal':baseline['baseline_delivery_seal'],'baseline_preseal':baseline['baseline_preseal'],'baseline_algorithm':baseline['baseline_algorithm'],'exposed12_reception':reception,'exposed12_controls':control,'regression_tests_original75':bind(P/'regression_tests.py'),'pre_fixed_development_controls':controls,'typed_subset_and_only_IF_intersection_preserved':True,'shared_add_units_generic_judge_unchanged':True,'source_packet_evidence_receipts_unchanged':True,'new_neutral_material_projection':False,'new_cohort_77_800_4481_run':False,'main_full_LLM_partial_results_read':False,'new_v4_hidden_controls_read':False,'historical_actual_S3_plan_read':False,'new_actual_source_ids':[],'code_frozen_before_independent_new_hidden6_and_historical_actual3':True,'code_will_not_be_overwritten_after_independent_execution':True})
pre=dump('pre-execution-seal.json',{'status':'final_algorithm_frozen_before_new_independent_execution','identity':'nonhuman developer algorithm seal; development regressions already executed','at_utc':at,'algorithm_bindings':alg,'five_modules':modules,'manual':baseline['manual'],'common_frozen_input_bindings':baseline['common_frozen_input_bindings'],'baseline_delivery_seal':baseline['baseline_delivery_seal'],'fixed_development_controls':controls,'exposed12_reception':reception,'new_v4_hidden_controls_read':False,'historical_actual_S3_plan_read':False,'independent_new_hidden6_and_actual3_execution_performed_by_owner':False,'post_independent_result_mutation_allowed':False,'remaining_delivery_documentation_may_be_added_without_module_edits':True})
for b in [alg,pre]+modules:verify(b)
print(json.dumps({'algorithm':alg,'preseal':pre,'modules':modules,'exposed12_verified_members':len(members)},ensure_ascii=False,indent=2))
