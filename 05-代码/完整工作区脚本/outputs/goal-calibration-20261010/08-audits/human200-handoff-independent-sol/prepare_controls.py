#!/usr/bin/env python3
"""Independent finite handoff expectations, before any handoff call.

Only seal/binding/administrative metadata and real UNFILLED templates are
parsed. Prediction and synthetic-statistics output files are SHA-read only.
"""
import copy
import datetime
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
OWNER=ROOT/'07-statistics/human200-machine-reference-handoff-sol'
EXPECTED_SEAL='d83514d4001afc0ace717c025659458f02f2ed966343b6f564ccf1f0ebe01be6'
EXPECTED_CODE='65ec6edce057d8504846f9a368027e81e2f246292399e1fdbc3457d8767cfa30'


def bind(path):
    p=Path(path).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def load(path):
    return json.loads(Path(path).read_bytes())


def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def canonical(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


verified={}


def exact(b):
    a=bind(b['path']);assert a==b,b['path'];verified[a['path']]=a;return a


assert bind(OWNER/'output-seal.json')['sha256']==EXPECTED_SEAL
seal=load(OWNER/'output-seal.json')
for b in seal['output_members']:exact(b)
exact(seal['code_binding']);exact(seal['bindings'])
assert seal['code_binding']['sha256']==EXPECTED_CODE
contract=load(OWNER/'bindings.json')
for b in contract['frozen_inputs'].values():exact(b)
exact(contract['year200_binding']);exact(contract['common_material_identity_receipt_binding'])
proof=load(contract['common_material_identity_receipt_binding']['path'])
for b in proof['assignment_bindings']:exact(b)
for row in proof['native_members']:exact(row['packet_binding'])
assert proof['old200_common_material_rows']==200
assert proof['human_material_bytes_and_object_equality_N']==400
assert proof['native_packet_bytes_and_object_equality_N']==200
assert proof['rule_delivered_selected_object_equality_N']==200
assert contract['actual_human_reference_N_at_preparation']==0
assert contract['actual_machine_results_admitted_at_preparation']==0
assert contract['real_statistics_runs_at_preparation']==0

manifest=load(contract['frozen_inputs']['LLM_manifest']['path'])
wrapper=load(contract['frozen_inputs']['LLM_frame_ids']['path'])
frame=wrapper['approved_record_ids']
assert manifest['ordered_source_ids']==contract['frozen_inputs']['LLM_frame_ids']
assert set(wrapper)=={'approved_record_ids','frame_order_UTF8_LF_sha256','preserves_original_FRAME4481_order'}
assert len(frame)==4481 and len(set(frame))==4481
lf_sha=hashlib.sha256(('\n'.join(frame)+'\n').encode()).hexdigest()
assert lf_sha==wrapper['frame_order_UTF8_LF_sha256']
assert [r for b in manifest['batches'] for r in b['source_ids']]==frame
assert len(manifest['batches'])==504
assert canonical(frame)==contract['frame_order_sha256']

snapshot=OUT/'code-snapshot';snapshot.mkdir(exist_ok=False)
with (snapshot/'handoff.py').open('xb') as stream:stream.write((OWNER/'handoff.py').read_bytes())
assert bind(snapshot/'handoff.py')['sha256']==EXPECTED_CODE
fixtures=OUT/'fixtures';fixtures.mkdir(exist_ok=False)


def fixture(name,value):
    p=fixtures/name
    with p.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    return bind(p)


cases=[]


def add(name,function,payload,expectation,reason,scope):
    b=fixture(f'{len(cases)+1:02d}-{name}.json',payload)
    cases.append({'name':name,'function':function,'input_binding':b,
                  'expected_before_execution':expectation,'independent_reason':reason,
                  'scope':scope,'no_statistics_expected':True})


add('actual_bound_wrapper_admin_only','frozen_frame',manifest,
    {'outcome':'accept','approved_order_exact':True,'record_N':4481},
    '实际冻结manifest三键文件绑定解析到原approved_record_ids wrapper，再验证4481唯一、UTF8/LF原序及504批展开同序；只接管理名单不接标签。',
    'actual_frozen_administrative_metadata_positive')
raw_list_binding=fixture('raw-list-instead-of-wrapper.json',frame)
wrong=copy.deepcopy(manifest);wrong['ordered_source_ids']=raw_list_binding
add('raw_list_is_not_frozen_wrapper','frozen_frame',wrong,
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Exact frozen frame wrapper required'},
    '直接4481列表没有wrapper与顺序证据，不能冒充批准名单。',
    'synthetic_helper_input_rejection_not_actual_campaign')
foreign=copy.deepcopy(wrapper);foreign['approved_record_ids'][-1]='SYNTHETIC-UNAPPROVED-FOREIGN-FRAME-MEMBER'
foreign['frame_order_UTF8_LF_sha256']=hashlib.sha256(('\n'.join(foreign['approved_record_ids'])+'\n').encode()).hexdigest()
foreign_binding=fixture('foreign-self-consistent-wrapper.json',foreign)
wrong=copy.deepcopy(manifest);wrong['ordered_source_ids']=foreign_binding
wrong['batches'][-1]['source_ids'][-1]=foreign['approved_record_ids'][-1]
add('self_consistent_foreign_wrapper_not_approved','frozen_frame',wrong,
    {'outcome':'reject','exception_class':'ValueError'},
    'helper如对外接任意manifest，单有自洽文件SHA、4481唯一、顺序声明和批展开仍不能确认是既定approved名单；应拒绝替换。另独立核真实CLI是否固定manifest以界定可达范围。',
    'standalone_helper_contract_probe_not_a_claimed_CLI_bypass')
wrong_wrapper=copy.deepcopy(wrapper);wrong_wrapper['frame_order_UTF8_LF_sha256']='0'*64
b=fixture('wrong-LF-order-digest-wrapper.json',wrong_wrapper)
wrong=copy.deepcopy(manifest);wrong['ordered_source_ids']=b
add('wrapper_wrong_original_LF_digest','frozen_frame',wrong,
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Original frame UTF8 LF order differs'},
    '原ID列表未变而UTF8/LF顺序SHA不实，不能用JSON正则化SHA替代原序证据。',
    'synthetic_wrapper_digest_rejection')

blank_review=load(OWNER/'review.UNFILLED.template.json')
assert blank_review['status']=='UNFILLED_NOT_AN_ACTUAL_EXECUTION_REVIEW'
assert blank_review['actual_user_confirmation']=={'source_kind':None,'statement':None}
wrong=copy.deepcopy(blank_review);wrong['old_rule_prediction_binding']['sha256']='0'*64
add('changed_rule_prediction_before_any_label_IO','build',{'review':wrong,'stage':'machine_reference','annual':False},
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Updated rule predictions rejected'},
    '旧200只能使用原规则首答，拒绝改SHA或另版规则；空白真实性字段不补齐，版本闸门先拒绝。',
    'historical_machine_reference_gate_negative')
wrong=copy.deepcopy(blank_review);wrong['domain_population_N']={'remaining':1261,'exposed':3220}
add('dynamic_domain_cannot_enter_annual_old200','build',{'review':wrong,'stage':'combined','annual':True},
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Historical domain contract is immutable'},
    '新未来域不能只用annual开关倒灌旧200设计；必须先于year_join和任何标签/引擎调用拒绝。',
    'annual_version_and_domain_gate_negative_no_year_metric')
add('real_UNFILLED_review_not_actual_execution','build',{'review':blank_review,'stage':'combined','annual':False},
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Actual review is unfilled'},
    '真实未填模板没有实际用户执行、真人身份/裁定/遮盲/独立原件证据，不能由格式或SHA变成接收。',
    'actual_blank_template_negative')

blank_inventory=load(OWNER/'LLM-complete-terminal-inventory.UNFILLED.template.json')
add('real_UNFILLED_machine_inventory','terminal_inventory_gate',blank_inventory,
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Partial or running LLM labels prohibited'},
    '模板504行仍未终止，不能称完整机器回收，也不得读取部分first标签。',
    'actual_blank_terminal_template_negative')


def purported_inventory():
    # An adversarial *synthetic* metadata claim for refusal controls only.
    # No receipts/first.json/human declaration exist or are fabricated.
    obj=copy.deepcopy(blank_inventory)
    obj.update(status='ROOT_received_complete_terminal_native4481_campaign',
               all_batches_terminal=True,reference_or_accuracy_used_in_selection=False)
    for e in obj['batches']:e['terminal_state']='terminal_not_returned'
    return obj


wrong=purported_inventory();wrong['batches']=wrong['batches'][:-1]
add('purported_full_campaign_missing_one_terminal_batch','terminal_inventory_gate',wrong,
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Every frozen batch must have exactly one terminal entry'},
    '声称全终止但只有503条终止记录，与原504批名单不符；全true声明不能替代精确库存。',
    'synthetic_false_completion_claim_negative_no_label_receipts')
wrong=purported_inventory();wrong['batches'][-1]['terminal_state']='running'
add('purported_full_campaign_has_running_batch','terminal_inventory_gate',wrong,
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Running/unfilled batch is forbidden'},
    '即使504行与总布尔为true，只要一批仍运行就不能开任何有效批标签；不能先读已返回部分。',
    'synthetic_running_batch_negative_no_label_receipts')

first_blank=json.loads((OWNER/'reference-original.UNFILLED.template.jsonl').read_text().splitlines()[0])
assert set(first_blank['dimensions'])=={'S','E','Ec','I','F'}
assert all(cell['value'] is None for cell in first_blank['dimensions'].values())
identity={'unit_id':'SYNTHETIC-FINITE-REFERENCE-HELPER',
          'source_bundle_sha256':first_blank['source_bundle_sha256']}
add('real_UNFILLED_reference_row_not_semantic_NULL','reference_output',
    {'row':first_blank,'identity':identity,'codes':[]},
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Unfilled reference template is not an execution'},
    '真实空白裁定模板保留五槽，但unfilled/null既非合法语义NULL，也非真实未返或失败，不能接成参照。',
    'actual_blank_reference_template_negative_no_human_identity')
partial=copy.deepcopy(first_blank);partial['method_status']='completed'
partial['dimensions']['S'].update(completion_status='filled',value=0,human_identity_code='SYNTHETIC-CONTROL-ACTOR')
partial['dimensions']['E'].update(completion_status='not_returned',value=None)
add('returned_reference_row_partial_dimension_nonreturn','reference_output',
    {'row':partial,'identity':identity,'codes':['SYNTHETIC-CONTROL-ACTOR']},
    {'outcome':'reject','exception_class':'ValueError','message_contains':'Per-dimension unreturned is unsupported by registered engine'},
    '只造一个0作为私有函数负控制的前置槽，不造200参照；已返行中某维未返必须留原状态并拒绝，不能改成0、语义NULL或执行失败。所用身份为显式synthetic字符串，未认证真人。',
    'minimal_synthetic_helper_status_negative_not_actual_adjudication')
assert len(cases)==12

write('controls12-fixed-before-execution.json',{
    'status':'independent_expectations_fixed_before_any_handoff_call',
    'case_N':12,'administrative_positive_N':1,'expected_rejection_N':11,
    'owner_seal_binding':bind(OWNER/'output-seal.json'),
    'code_binding':bind(OWNER/'handoff.py'),'cases':cases,
    'actual_human_reference_or_statistics_N':0,
    'candidate_handoff_calls_before_this_seal_N':0,
    'expectations_may_not_change_after_execution':True,
})
write('sealed-input-verification.json',{
    'owner_output_members_N':len(seal['output_members']),
    'all_owner_members_and_direct_frozen_inputs_SHA_bytes_matched':True,
    'all_verified_bindings':[verified[p] for p in sorted(verified)],
    'owner_seal_binding':bind(OWNER/'output-seal.json'),
    'frozen_approved_record_file_exactly_manifest_ordered_source_ids':True,
    'approved_unique_record_N':4481,'frozen_batch_N':504,
    'approved_UTF8_LF_order_sha256':lf_sha,
    'campaign_JSON_canonical_coverage_order_sha256':canonical(frame),
    'the_two_order_digest_encodings_are_distinct_and_each_matches_its_own_contract':True,
    'common_material_identity_receipt_scalar_and_member_bindings_matched':True,
    'hashing_a_label_file_is_not_semantic_label_reading':True,
    'rule_prediction_or_main_LLM_labels_semantically_read':False,
    'owner_synthetic_statistics_or_expected_table_read':False,
})
write('read-scope-before-execution.json',{
    'actual_semantic_reads':['handoff.py entire27412 bytes','README.md','bindings.json',
      'output-seal.json binding inventory','review.UNFILLED.template.json',
      'LLM-complete-terminal-inventory.UNFILLED.template.json administration',
      'reference-original.UNFILLED.template.jsonl first blank row only',
      'common-material-identity-receipt.json administration and bound member pointers',
      'frozen human_first.reviewed_receive and project_records code',
      'prepare_handoff.py frame_order digest preparation source excerpt',
      'bound run-manifest and approved_record_ids administrative wrapper'],
    'no_policy_body_semantic_review':True,'no_actual_A_B_label_reception':True,
    'no_reference_identity_authenticated':True,'no_rule_prediction_semantic_read':True,
    'no_main_LLM_partial_label_read':True,'no_year_join_or_year_metrics':True,
    'no_engine_import_or_statistics_run':True,'no_changed_owner_or_historical_file':True,
    'synthetic_guard_inputs_are_not_actual_reviews_receipts_or_releases':True,
})
pre_members=[bind(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
write('pre-execution-seal.json',{
    'status':'sealed12_independent_handoff_controls_before_execution',
    'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'case_N':12,'owner_seal_sha256':EXPECTED_SEAL,'owner_code_sha256':EXPECTED_CODE,
    'output_members':pre_members,'candidate_handoff_calls_N':0,
})
print(json.dumps({'case_N':12,'preseal':bind(OUT/'pre-execution-seal.json'),'handoff_calls_N':0},ensure_ascii=False))
