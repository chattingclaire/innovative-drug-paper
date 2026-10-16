"""Private predeclared diagnostic design. Zero model/CLI calls; no09 edits."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=ROOT/'outputs/编码修订核查-20261008/LLM编码'
A=BASE/'候选08-命题与证据判定';P=BASE/'候选08-独立检查';O=P/'机制对照预设计'
D=['S','E','Ec','I','F'];NOW=datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def new(p,o):
 assert not p.exists(),'Never overwrite prior design or expectations.'
 p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')

# New synthetic language only. Exact examples/expectations stay private.
five='登记的药物项目为：给药后严重过敏的发生情况、该药减少急性发作的试验结果、每月药费、相对既有制剂的释药改良，以及患者自付药费与收入的比例。'
two='研究证据分为：该药引起严重肝损伤的监测记录，以及该药延缓疾病复发的比较试验结果。'
cases=[
 {'id':'M08-M01','kind':'clear_negative','text':'综合分析是把多个材料来源加以整理和比较的一种方法。','following_text':five,
  'labels':dict.fromkeys(D,0),'I_subtypes':[],'F_subtypes':[],
  'basis':'Current self-contained abstract method definition neither refers to nor requires the adjacent substantive list. Following position alone must not import its dimensions.'},
 {'id':'M08-M02','kind':'clear_positive','text':'本次药物综合评价必须逐项检查相邻登记的全部项目。','following_text':five,
  'labels':dict.fromkeys(D,1),'I_subtypes':['attribute'],'F_subtypes':['affordability'],
  'basis':'Current mandatory predicate explicitly incorporates the adjacent list, which independently contains drug risk, effect, drug expense, relative product improvement and patient affordability.'},
 {'id':'M08-M03','kind':'clear_negative','text':'办公室只负责这批研究文件的版本号、页码和纸质副本登记。','following_text':two,
  'labels':dict.fromkeys(D,0),'I_subtypes':[],'F_subtypes':[],
  'basis':'Self-contained clerical metadata work does not require safety/effect contents; no missing continuation exists.'},
 {'id':'M08-M04','kind':'clear_positive','text':'此次补充申报必须提交相邻条目列明的两类药物证据。','following_text':two,
  'labels':{'S':1,'E':1,'Ec':0,'I':0,'F':0},'I_subtypes':[],'F_subtypes':[],
  'basis':'The current evidence requirement explicitly incorporates adjacent drug-caused injury and recurrence-reduction evidence. Generic research evidence is not innovation support or economic/access content.'},
 {'id':'M08-M05','kind':'unscored_boundary','text':'开展综合分析时，可以参照相邻登记项目的安排。','following_text':five,
  'labels':None,'I_subtypes':None,'F_subtypes':None,
  'basis':'Reference to arrangements may import substantive projects or merely organizational arrangements. No hard unique vector is declared. Reasons and quotation scope still require semantic review.'}
]
for c in cases:
 c['safety_quality_basis']='no_quality_basis'
 c['source_position']='following_adjacent'
 c['manual_anchors']=['v1.3 context/current-content principles and introductory-clause boundary','v1.4 shared step7:given context disambiguates real relation, not background copying']
 c['not_a_real_policy_quote']=True
 c['expected_evidence']=[] if c['labels'] is None else [
  {'dimension':d,'source':'unit','quote':c['text']} for d in D if c['labels'][d]] + [
  {'dimension':d,'source':'context','quote':c['following_text']} for d in D if c['labels'][d]]
 if c['kind']=='unscored_boundary':
  c['possible_readings_NOT_FORCED']=[{'reading':'Reference incorporates current substantive projects','labels':dict.fromkeys(D,1)},
    {'reading':'Reference concerns arrangements and does not import project content','labels':dict.fromkeys(D,0)}]

private=O/'five_new_bases_FULL5_EXPECTATIONS_PRIVATE_FROZEN.json'
new(private,{'status':'PRIVATE_SYNTHETIC_BASES_AND_EXPECTATIONS_FROZEN_BEFORE_ANY_MODEL_OUTPUT',
 'created_at_UTC':NOW,'cases':cases,'hard_scored_bases':4,'boundary_bases':1,
 'reviewer_model_calls':0,'reviewer_CLI_invocations':0,'prompt_author_has_not_received_inputs_or_expectations':True,
 'not_external_human_validity':True})

# Same ids, base order, literal text and true source position in separate requests.
# Only field key and row key serialization order are proposed perturbations.
base_order=['M08-M03','M08-M02','M08-M05','M08-M01','M08-M04']
by_id={c['id']:c for c in cases}
arms=[]
for name,key,placement in [
 ('field_typed_context_before','structured_following_units','before_text'),
 ('field_neutral_context_before','provided_context_units','before_text'),
 ('field_typed_context_after','structured_following_units','after_text'),
 ('field_neutral_context_after','provided_context_units','after_text')]:
 rows=[]
 for ident in base_order:
  c=by_id[ident]
  context={key:[{'source_position':'following_adjacent','text':c['following_text']}]}
  if placement=='before_text':r={'id':ident,'contexts':context,'text':c['text']}
  else:r={'id':ident,'text':c['text'],'contexts':context}
  rows.append(r)
 target=O/(name+'_INPUT_ONLY_PRIVATE_PROPOSED.json')
 new(target,{'rows':rows})
 arms.append({'arm':name,'field_key':key,'requested_row_serialization':placement,
  'input_binding':bind(target),'n':5,'logical_requests':1,'maximum_same_request_technical_attempts':3,
  'separate_ephemeral_request_required':True,'actual_request_fidelity_verified':False, 'frozen_runner_json_order_delivery_path_confirmed_from_source':True})

# Check factual identity across variants without rendering any protected source.
for ar in arms:
 packet=json.loads(Path(ar['input_binding']['path']).read_text())
 assert [r['id'] for r in packet['rows']]==base_order
 for r in packet['rows']:
  c=by_id[r['id']];ctx=r['contexts'][ar['field_key']][0]
  assert r['text']==c['text'] and ctx['text']==c['following_text'] and ctx['source_position']=='following_adjacent'
  assert list(r)==(['id','contexts','text'] if ar['requested_row_serialization']=='before_text' else ['id','text','contexts'])

red_path=ROOT/'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py'
sp=importlib.util.spec_from_file_location('mechanism_redactor',red_path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
red=m.ReservedContextRedactor()
protected_checks=[]
for ar in arms:
 packet=json.loads(Path(ar['input_binding']['path']).read_text())
 check=red.audit_object_no_full_match(packet)
 assert check['no_remaining_full_normalized_reserved_unit_match']
 protected_checks.append({'arm':ar['arm'],'no_full_normalized_protected_match':True})

prompt=A/'candidate08_prompt_PROPOSED.txt'
closure=A/'closure/candidate08_actual_execution_semantic_closure.json'
sources=[bind(prompt),bind(A/'design_freeze.json'),bind(A/'phase-gates/inherited-controls.json'),bind(closure),
 bind(P/'actual-inherited-controls/candidate08_inherited62_actual_full_semantic_review_PRIVATE.json'),
 bind(ROOT/'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md'),
 bind(ROOT/'outputs/coding-revision-20261007-r3/protocol/共用操作说明-v1.4.md'),
 bind(A/'runtime-unchanged-v2/run_production_v32.py'),bind(red_path)]
assert sha(prompt)=='d79c097443fa249051c5264da1ff532ddf7d984225ac3e776807de95f7f21803'
assert sha(closure)=='991c1233c6f9a2a4fe8afd3b1c4c78b54c65b224448a3e487ed7cfce0717f36e'
plan={'status':'PROPOSED_DIAGNOSTIC_DESIGN_ONLY_ZERO_CALLS_NO_EXECUTION_AUTHORIZATION',
 'created_at_UTC':NOW,'reviewer':'/root/validation_state_oct8','purpose':'Distinguish sensitivity to following-context field name and request serialization location from persistent current-sentence relation errors. Diagnostic only; not a new coding candidate.',
 'control_freeze':bind(private),'source_bindings':sources,
 'design':{'type':'two_by_two_minimal_separable_factors_in_four_independent_requests',
  'factor1':'structured_following_units versus provided_context_units; same literal content and source-position metadata',
  'factor2':'contexts serialized before versus after text in each row; actual document position remains following_adjacent in all cells',
  'units_per_arm':5,'hard_scored_units_per_arm':4,'unscored_boundary_units_per_arm':1,
  'total_model_rows_if_all_four_arms_authorized':20,'total_hard_dimension_cells':80,'boundary_dimension_cells_unscored':20,
  'same_ids_and_same_base_order_in_every_request':base_order,
  'no_duplicate_representations_together_in_one_request':True,
  'not_changed':['Complete current sentence','Complete given adjacent text','True document source position','All five semantic definitions','Output schema/validator','Frozen08 prompt','Model and effort','Per-request base order and IDs'],
  'no_context_deletion_or_background_answer_tokens':True, 'typed_status_handling':'Every new base has the same absent typed-status, and this absence is preserved in all arms. No production typed-status is removed or relabeled; production typed branches are not tested. Only the verified production fact structured-following nonempty148 is background metadata, not an outcome or sampling claim.'},
 'proposed_arms':arms,
 'runtime_if_later_separately_authorized':{'model':'gpt-5.6-sol','reasoning_effort':'medium','fixed_prompt_binding':bind(prompt),
  'one_predeclared_experiment_with_four_independent_logical_requests':True,'total_logical_requests':4,'maximum_identical_technical_attempts':12,
  'workers_per_arm':1,'batch_size':25,'first_chronologically_technically_valid_only':True,'semantic_retries_allowed':False,
  'different_prompt_or_reference_or_expected_fields_in_request_allowed':False,
  'semantic_wrong_answers_are_diagnostic_outcomes_not_a_reason_to_rerun_or_select_an_arm':True,
  'technical_exhaustion':'Preserve attempts and stop unstarted arms; report incomplete comparison/NOT_RUN, do not replace a request.',
  'not_authorized_by_existing_candidate08_execution_or_failure_gate':True},
 'required_before_final_experimental_plan_or_authorization':[
  'Root first determines whether the causal question is necessary after author input→actualrequest fidelity audit; do not assume hypotheses explain015.',
  'Establish from the frozen runner serialization path that key names, row text, context text and requested ordering survive to the exact model request; input-file order alone is insufficient evidence.',
  'Bind offline serialized request bytes/hashes and verify the only intended differences, without invoking CLI or model. If runner rebuilds/sorts fields, the position factor is not delivered and cannot be called a position experiment.',
  'If position perturbation cannot be delivered or root judges it unnecessary, preserve this proposal and predeclare a new two-arm field-only plan before any actual output: contexts after text in both, two independent requests, maximum6technical attempts. No post-result fallback or selective comparison.',
  'Only after root review freeze the final selected design and obtain separate explicit bounded execution authorization. This PROPOSED artifact supplies none.'
 ],
 'predeclared_analysis':{'hard_labels':'Compare all80 hard cells against unchanged private expectations and review every reason/evidence/subtype/quality and issue; not label match alone.',
  'primary_false_positive_units':'Two self-contained negatives, five zero dimensions each, across each delivered factorial cell.',
  'positive_controls':'Explicit incorporation of the same nearby content must preserve its supported dimensions; a representation that fixes negatives by dropping necessary positive context is under-reading, not a successful mechanism fix.',
  'field_contrast':'For each semantic base and delivered serialization position, display typed-versus-neutral false positives and false negatives, plus reason/evidence attachment differences.',
  'position_contrast':'For each base and field key, display before-versus-after differences only when exact requests confirm the intended key order.',
  'boundary':'Review all four boundary outputs and reasons separately; no accuracy score or forced unique truth; unsupported claims can still be recorded.',
  'no_performance_threshold':'No kappa0.8 tuning, superiority threshold, significance claim or winner selection. Preserve all actual outputs and failures.'},
 'interpretation_limits':[
  'A typed-field failure that vanishes under neutral naming while positive relations remain understood is evidence of representation sensitivity in these constructed requests, not proof of a unique causal mechanism.',
  'A systematic before/after difference with same facts suggests request-order sensitivity only if fidelity is demonstrated; it does not imply the document source order changed.',
  'Errors shared across all representations are consistent with sentence-relation or other common-context failure; they do not prove field naming is irrelevant or isolate one cognitive cause.',
  'One response per arm has stochastic variation and no independent replication. Four separate ephemeral requests reduce within-request counterpart leakage but do not eliminate common training/context effects.',
  'Passing new examples cannot erase original08FAIL, justify09 or adoption, estimate corpus accuracy, or establish external human validity.'
 ],
 'privacy':{'new_originals_and_expectations_not_sent_to_prompt_author':True,'private_input_access_for_execution_must_be_mechanical_only':True,
  'if_prompt_later_modified_by_anyone_who_saw_these_examples':'Record that exposure, new promptSHA and identity transition to development regression; do not present the same examples as an unseen test of the revised prompt.'},
 'protected_check_metadata_only':protected_checks,'reviewer_model_calls':0,'reviewer_CLI_invocations':0,
 'manual_AB_original_outputs_or_manuscript_modified':False,'new_candidate09_written':False,'execution_authorized':False}
plan_path=O/'mechanism_contrast_plan_PROPOSED_PRIVATE.json';new(plan_path,plan)
manifest={'status':'FROZEN_NEW_SYNTHETIC_BASES_WITH_PROPOSED_UNAUTHORIZED_DIAGNOSTIC_PLAN','created_at_UTC':NOW,
 'plan':bind(plan_path),'private_expected_controls':bind(private),'input_files':[a['input_binding'] for a in arms],
 'builder':bind(Path(__file__).resolve()),'source_bindings':sources,
 'n_bases':5,'n_arms_proposed':4,'n_rows_if_authorized':20,'hard_dimension_cells':80,'boundary_dimension_cells':20,
 'actual_request_fidelity_not_yet_confirmed':True, 'frozen_runner_json_order_delivery_path_confirmed_from_source':True,'model_calls':0,'real_CLI_invocations':0,'execution_authorized':False}
mp=O/'mechanism_design_manifest_PROPOSED.json';new(mp,manifest)
print(json.dumps({'path':str(mp),'sha256':sha(mp),'plan_sha256':sha(plan_path),'private_controls_sha256':sha(private),
 'bases':5,'proposed_arms':4,'model_calls':0,'execution_authorized':False},ensure_ascii=False))
