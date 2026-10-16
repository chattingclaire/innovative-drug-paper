"""Save completed independent semantic reading; no model, label edits or gate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode=True
ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=ROOT/'outputs/编码修订核查-20261008/LLM编码'
PRIVATE=BASE/'候选08-独立检查'
AUTHOR=BASE/'候选08-命题与证据判定'
RUN=AUTHOR/'runtime-unchanged-v2/independent16-candidate08-first-run'
OUT=PRIVATE/'actual-new-controls'
DIMS=['S','E','Ec','I','F']


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def binding(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}


expected_path=PRIVATE/'independent_synthetic16_FULL5_PRIVATE_PREDECLARED.json'
assert sha(expected_path)=='bcc05eb627667ef8180c64fa2e93114d46bf0299267d1a4651ce45965204412c'
expected=read(expected_path)
inputs=read(PRIVATE/'independent_synthetic16_inputs_ONLY_PRIVATE_RUNNER_CONTAINER_V2.json')['rows']
assert inputs==read(PRIVATE/'independent_synthetic16_inputs_ONLY_PRIVATE_PREDECLARED.json')
raw_path=RUN/'all_predictions.json'
assert sha(raw_path)=='7f953d0f999942605f9130946d7829dd3493f7d83acca1d49adf1c8e3b085c45'
assert sha(RUN/'all_predictions.jsonl')=='1380866fc4147d4d90a23e02e1b9429074f894668aa8956efa6f3aa33594128e'
raw=read(raw_path)
assert raw['rows']==[json.loads(x) for x in (RUN/'all_predictions.jsonl').read_text().splitlines() if x.strip()]
assert [r['id'] for r in raw['rows']]==[r['id'] for r in inputs]
assert not raw['issue_records']
assert read(RUN/'frozen_input.json')['rows']==inputs
assert sha(AUTHOR/'design_freeze.json')=='443b958c7821f53dd8feeddaeca6199e76c290ccd94627f4b4b2ce85e66accfc'
assert sha(AUTHOR/'candidate08_prompt_PROPOSED.txt')=='d79c097443fa249051c5264da1ff532ddf7d984225ac3e776807de95f7f21803'
selection=read(RUN/'batches/batch-0001/selection.json')
assert selection['selected_relative_path']=='batches/batch-0001/attempts/attempt-01'
assert len(selection['attempts'])==1 and selection['selection_uses_metric_or_label_values'] is False
selected=RUN/selection['selected_relative_path']/'raw_output.json'
assert read(selected)==raw and sha(selected)==selection['selected_output_sha256']

# These are this agent's completed semantic readings of all five actual reasons,
# not auto-generated judgments from agreement with expected labels.
notes={
 'C08-U001':[
  '对象人群的批准变化没有药物损害或风险内容，S0理由成立。',
  '当前是适应症属性范围变化，没有实际效果、获益、治疗推荐或效果证据要求；E0未把适应症词自动当疗效。',
  '未讨论药价、药费或支付资源，Ec0成立。',
  '成人到儿童是相对既有批准属性的明确变化，I1及attribute有独立依据，不要求已证优效。',
  '人群属性变化不是实际给付/配备范围或未满足治疗获取需要，F0理由成立。'],
 'C08-U002':[
  '信息原文录入和日期记录不涉及药物风险，S0成立。',
  '沿用适应症文字的文书操作没有增加效果评价要求，E0成立。',
  '无经济内容，Ec0成立。',
  '仅原样录入既有属性，未开展创新属性评价或陈述变化；I0没有把新申报误作创新。',
  '没有实际保障或获取内容，F0成立。'],
 'C08-U003':[
  '申请人收集不良反应并更新风险控制记录，S1依据直接且实际。',
  '安全监测义务未涉及药物治疗效果，E0成立。',
  '无药价、治疗成本、支付或预算内容，Ec0成立。',
  '当前是申请人安全义务；创新药背景对象不是机构给予支持或产品变化，I0恰当。',
  '安全记录义务不等于获取或药品临床管理难度，F0成立。'],
 'C08-U004':[
  '指导不良反应识别和风险控制确为安全内容，S1与I可同时成立。',
  '无效果评价或效果证据，E0成立。',
  '专家资源本身不是药费或治疗支付资源经济评价，Ec0成立。',
  '机构向明确创新研发对象配置专家并提供指导，I1/research_support有独立实质支持依据。',
  '研发指导未讨论药物保障、患者负担或管理难度，F0成立。'],
 'C08-U005':[
  '基金预算条件没有药物损害内容，S0成立。',
  '未陈述效果内容，E0成立。',
  '药品支付范围调整造成基金支出预算增幅约束，Ec1不是泛行政经费。',
  '没有创新属性或创新支持命题，I0成立。',
  '给定父谓词明确决定两年续约并持续原范围保障，子条件属于实际保障连续性实质条件；F1/access正确使用关系而非全维背景传播。'],
 'C08-U006':[
  '没有风险内容，S0成立。',
  '没有效果内容，E0成立。',
  '即便父谓词仅程序资格，当前预算增幅仍为实质药物经济内容，Ec1保留恰当。',
  '无创新属性或支持命题，I0成立。',
  '该父谓词仅准许提交材料并安排谈判，没有实际续约延续或给付范围规定，F0恰当地与另一父谓词区分。'],
 'C08-U007':[
  '无处方记录不是药物安全损害，S0成立。',
  '使用记录缺乏不是药物疗效不足判断，E0成立。',
  '未述销售金额、价格或预算，Ec0成立。',
  '未讨论创新属性或支持，I0成立。',
  '给定父句明确拟调出机构常规配备目录，子项是其条件；F1/access不增加已实施或扩大方向门槛。'],
 'C08-U008':[
  '无药物风险，S0成立。',
  '无使用记录不自动等于效果判断，E0成立。',
  '没有经济含义，Ec0成立。',
  '没有创新内容，I0成立。',
  '控制谓词仅分派资料核对组，不决定药品配备/供应，也未要求实际供应缺口信息；F0成立。'],
 'C08-U009':[
  '预约登记不讨论安全，S0成立。',
  '预约登记不讨论治疗效果，E0成立。',
  '价格只限定咨询主题，实际要求为姓名和时间登记；无实质价格、经济评价或费用资料要求，Ec0成立。',
  '无创新支持或属性，I0成立。',
  '咨询入口不是取药渠道或保障范围，F0成立。'],
 'C08-U010':[
  '价格及发票核对不涉及药物损害，S0成立。',
  '无药物效果，E0成立。',
  '具体供货价格上限和发票价格核对均为药价内容，Ec1成立。',
  '无创新内容，I0成立。',
  '向机构供应限定价格适用对象，不能省略价格中心词变成持续供货或患者可负担，F0成立。'],
 'C08-U011':[
  '文书安排未述安全内容，S0成立。',
  '文书安排未述效果内容，E0成立。',
  '无经济内容，Ec0成立。',
  '拟编制有创新研发字样的文件及登记元数据没有规定实体支持，I0理由成立；并非因未来状态排除。',
  '文件目录不是药物配备目录或保障安排，F0成立。'],
 'C08-U012':[
  '统计顾问和一般试验设计未独立陈述安全用途，S0成立。',
  '一般试验设计指导未明确连接药物效果判断，E0成立。',
  '免费的是研发指导服务，不是药品治疗/支付费用，Ec0成立。',
  '明确创新研发对象、顾问人数、时间及指导资源，I1/research_support成立；拟议状态不抹去支持内容。',
  '研发资源安排没有保障获取或患者负担内容，F0成立。'],
 'C08-U013':[
  '仅文件名称版本份数记录，无新增安全资料内容要求，S0成立。',
  '同理无效果资料实质要求，E0成立。',
  '同理无经济内容要求，Ec0成立。',
  '不将背景未来五类文件中的创新性传入秘书文书任务，I0成立。',
  '不将背景公平性文件名传入秘书文书任务，F0成立；句子自足不需要material_issue。'],
 'C08-U014':[
  '当前汇总药物导致严重不良反应是独立安全证据内容，S1成立。',
  '降低患者住院率的药物试验结果直接体现临床获益，E1成立。',
  '住院率本身未讨论住院费、治疗成本或基金资源影响，Ec0成立。',
  '安全/效果资料不因背景文件清单含创新性而复制I，I0成立。',
  '没有实际获取或负担内容，不复制背景F，F0成立。'],
 'C08-U015':[
  '基金支出并非药物安全内容，S0成立。',
  '无效果内容，E0成立。',
  '明确该药医保基金支出预测为药物经济内容，Ec1成立。',
  '无创新内容，I0成立。',
  '基金支出总额没有确定覆盖范围或患者承担与支付能力，F0成立；不虚增affordability。'],
 'C08-U016':[
  '自付药费上限不涉及药物损害，S0成立。',
  '无效果内容，E0成立。',
  '患者自付药费及上限直接属于经济内容，Ec1成立。',
  '无创新内容，I0成立。',
  '明确药费与家庭收入的比例联系直接讨论可负担程度，F1/affordability有独立依据；并未另确定药物覆盖范围，不加access。']}

expect={c['id']:c for c in expected['controls']}
source={x['id']:x for x in inputs}
assert len(notes)==16 and all(len(v)==5 for v in notes.values())

def context_strings(x):
    if isinstance(x,str):return [x]
    if isinstance(x,list):return sum((context_strings(v) for v in x),[])
    if isinstance(x,dict):return sum((context_strings(v) for v in x.values()),[])
    return []

cases=[];mismatches=[];evidence_count=0
for row in raw['rows']:
    ident=row['id']; expected_row=expect[ident]['expected']; inp=source[ident]
    dim_review={}
    for index,d in enumerate(DIMS):
        actual=row['labels'][d];target=expected_row['labels'][d]
        if actual!=target:mismatches.append({'id':ident,'dimension':d,'actual':actual,'frozen_expected':target})
        assert isinstance(row['dimension_reasons'][d],str) and row['dimension_reasons'][d]
        dim_review[d]={'actual_label':actual,'unchanged_frozen_expected_label':target,
            'label_matches_frozen_expectation':actual==target,'actual_reason_actually_read':True,
            'actual_reason_supported_in_this_input':True,'independent_semantic_basis':notes[ident][index],
            'status':'SUPPORTED_CURRENT_VISIBLE_CONTENT'}
    ev_checks=[]
    for ev in row['evidence']:
        strings=[inp['text']] if ev['source']=='unit' else context_strings(inp['contexts'])
        literal=any(ev['quote'] in x for x in strings)
        assert literal and row['labels'][ev['dimension']]==1
        ev_checks.append({'dimension':ev['dimension'],'source':ev['source'],'quote_sha256':hashlib.sha256(ev['quote'].encode()).hexdigest(),
            'continuous_literal_in_correct_unit_or_given_context':True,'meaning_actually_reviewed':True,
            'supports_current_dimension_or_controlling_relation':True})
        evidence_count+=1
    for d in DIMS:
        if row['labels'][d]:assert any(e['dimension']==d and e['source']=='unit' for e in row['evidence'])
    if not any(row['labels'].values()):assert not row['evidence']
    assert set(row['fairness_subtypes'])==set(expected_row['fairness_subtypes'])
    assert set(row['innovation_subtypes'])==set(expected_row['innovation_subtypes'])
    assert row['safety_quality_basis']==expected_row['safety_quality_basis']=='no_quality_basis'
    cases.append({'id':ident,'five_dimensions':dim_review,'evidence_review':ev_checks,
        'innovation_subtypes':{'actual':row['innovation_subtypes'],'matches_frozen':True,'independently_supported':True},
        'fairness_subtypes':{'actual':row['fairness_subtypes'],'matches_frozen':True,'independently_supported':True},
        'safety_quality_basis':{'actual':row['safety_quality_basis'],'matches_frozen':True,
            'review':'无一条包含独立药品质量安全依据；S正类均是临床风险/不良反应，其他条没有S正类。'},
        'actual_issue_records':[],'issue_review':'顶层issue_records已完整读取为空；该句和必要父语境足以判定，没有需要补出的材料缺口。',
        'confirmed_semantic_errors':[],'unresolved_boundary_in_this_constructed_item':False})
assert not mismatches

files=[PRIVATE/'actual-new-controls/actual_review_plan_PREOUTPUT.json',expected_path,
    PRIVATE/'independent_design_manifest_v1.json',PRIVATE/'independent_synthetic16_inputs_ONLY_PRIVATE_PREDECLARED.json',
    PRIVATE/'independent_synthetic16_inputs_ONLY_PRIVATE_RUNNER_CONTAINER_V2.json',PRIVATE/'independent16_runner_container_adapter_v2.json',
    PRIVATE/'semantic_acceptance_PRIVATE_PREDECLARED.json',PRIVATE/'boundary_register_PRIVATE_NOT_SCORED.json',
    AUTHOR/'design_freeze.json',AUTHOR/'candidate08_prompt_PROPOSED.txt',raw_path,RUN/'all_predictions.jsonl',
    RUN/'frozen_input.json',RUN/'run_plan.json',RUN/'execution_summary.json',RUN/'batches/batch-0001/selection.json',selected,
    RUN/'batches/batch-0001/attempts/attempt-01/validation.json',RUN/'batches/batch-0001/attempts/attempt-01/event_output_binding_audit.json']
files += [ROOT/'outputs/coding-revision-20261007-r3/protocol'/x for x in ['完整五维手册-v1.3.md','共用操作说明-v1.4.md']]
projection=AUTHOR/'execution-audit/new-controls/candidate08_independent16_FOR_INDEPENDENT_REVIEW_ONLY_PRIVATE.json'
technical=AUTHOR/'execution-audit/new-controls/candidate08_technical_QA.json'
optional=[]
if projection.exists():
    obj=read(projection)
    assert [r['candidate08_intact_actual_row'] for r in obj['rows']]==raw['rows']
    assert [r['input'] for r in obj['rows']]==inputs
    files.append(projection);optional.append('Independent16 technical projection matched raw and frozen inputs mechanically.')
if technical.exists():
    files.append(technical);optional.append('Phase technical QA bound; no author24 semantic output was read by this reviewer.')
before={str(f):sha(f) for f in files}

report={'status':'COMPLETED_INDEPENDENT16_SEMANTIC_REVIEW_NO_CONFIRMED_ERROR_NOT_A_CONTINUATION_GATE',
 'created_at_UTC':datetime.now(timezone.utc).isoformat(),'reviewer':'/root/validation_state_oct8',
 'source_bindings':[binding(f) for f in files],
 'source_SHA_correction':{'original_root_message_file_name':'all_predictions.json','original_root_message_SHA':'1380866fc4147d4d90a23e02e1b9429074f894668aa8956efa6f3aa33594128e',
   'actual_SHA_belongs_to':'all_predictions.jsonl','actual_JSON_with_issues_SHA':sha(raw_path),
   'JSON_rows_equal_JSONL_rows':True,'initial_filename_SHA_assertion_failed_then_resolved_by_actual_summary_and_files':True},
 'scope':{'independent_synthetic_units':16,'dimension_labels_actually_reviewed':80,'dimension_reasons_actually_reviewed':80,
          'actual_evidence_quotes_actually_reviewed':evidence_count,'all_I_F_subtype_arrays_and16_quality_fields_read':True,
          'all_top_level_issue_records_actually_read':True,'actual_issue_records_count':0,
          'author24_or_real240_semantically_read':False,'protected267_originals_semantically_read':False,
          'private_expectations_rewritten':False,'original_independent_input_semantics_changed':False},
 'mechanical_expectation_comparison':{'label_matches':80,'label_mismatches':mismatches,
     'I_F_subtype_mismatches':[],'S_quality_mismatches':[],'expectation_agreement_is_not_used_as_sole_semantic_review':True},
 'independent_semantic_result':{'confirmed_error_count':0,'confirmed_errors':[],'unresolved_item_count':0,'unresolved_items':[],
     'all_actual_reasons_and_evidence_supported_in_visible_constructed_material':True,
     'original_three_unscored_boundaries_not_run_and_not_forced':True},
 'actual_execution_provenance':{'actual_independent16_logical_requests':1,'actual_attempts':1,'selected_attempt':'attempt-01',
    'selected_intact_raw_object_equals_aggregate_JSON':True,'selection_used_reference_or_label_values':False,
    'run_plan_requested_model':read(RUN/'run_plan.json')['model'],'run_plan_reasoning_effort':read(RUN/'run_plan.json')['reasoning_effort'],'prompt_SHA_fixed':sha(AUTHOR/'candidate08_prompt_PROPOSED.txt'),
    'reviewer_model_calls':0,'reviewer_CLI_invocations':0},
 'cases':cases,'optional_audit_artifact_checks':optional,
 'release_limits':{'continuation_gate_written':False,'next_phase_authorized_by_this_report':False,
    'full_corpus_or_adoption_authorized':False,'any_confirmed_failure_requires_later_phases_NOT_RUN':True,
    'root_must_review_author24_and_phase_technical_QA_before_any_separate_continuation_decision':True},
 'limitations':['This is a complete review of sixteen constructed development controls; it does not estimate corpus accuracy or establish independent human validity.',
   'No candidate08 real240 or inherited106 output has been semantically evaluated here. Current adoption remains Rule39+completeLLM03.',
   'Technical first-attempt success and agreement on these controls do not prove future semantic correctness, causal uniqueness or any kappa threshold.',
   'This reviewer designed and knows the private expectations. The original design preceded reading08 prompt, and no prompt changes were proposed; this is not a blinded human scoring session.'],
 'manual_AB_predictions_outputs_manuscript_modified':False}
target=OUT/'candidate08_independent16_actual_semantic_review_PRIVATE.json'
assert not target.exists()
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for f in files:assert sha(f)==before[str(f)]
print(json.dumps({'status':report['status'],'path':str(target),'sha256':sha(target),'dimension_cells':80,
 'reasons_read':80,'evidence_quotes_read':evidence_count,'confirmed_errors':0,'continuation_gate_written':False},ensure_ascii=False))
