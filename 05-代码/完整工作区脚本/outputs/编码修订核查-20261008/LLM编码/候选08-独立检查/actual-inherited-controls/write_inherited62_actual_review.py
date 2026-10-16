"""Seal independently completed 62-control reading. Never executes models/gates."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=ROOT/'outputs/编码修订核查-20261008/LLM编码'
A=BASE/'候选08-命题与证据判定';P=BASE/'候选08-独立检查'
R=A/'runtime-unchanged-v2/inherited62-candidate08-first-run'
O=P/'actual-inherited-controls';D=['S','E','Ec','I','F']
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def strings(x):
 if isinstance(x,str):return [x]
 if isinstance(x,list):return sum((strings(v) for v in x),[])
 if isinstance(x,dict):return sum((strings(v) for v in x.values()),[])
 return []

assert sha(R/'all_predictions.json')=='cdf7098fcccab3ea7e984bf8c021283da0558fcd899360202a56118879c17688'
assert sha(R/'all_predictions.jsonl')=='1b1f919862770c15170d0678083a68cd0fd9d0e89288117fdd2d2ad8e58428c0'
raw=read(R/'all_predictions.json')
assert raw['rows']==[json.loads(x) for x in (R/'all_predictions.jsonl').read_text().splitlines() if x.strip()]
inputs=[json.loads(x) for x in (A/'synthetic62_inputs_UNCHANGED.jsonl').read_text().splitlines() if x.strip()]
frozen_expected=read(A/'synthetic106_expected_INHERITED_PRIVATE.json')['tests']
expected={x['input']['id']:x for x in frozen_expected}
assert len(inputs)==len(raw['rows'])==62
assert [x['id'] for x in inputs]==[x['id'] for x in raw['rows']]
src={x['id']:x for x in inputs}
assert all(expected[x['id']]['input']==x for x in inputs)
assert all(not any(f in expected[x['id']] for f in ['fairness_subtypes','innovation_subtypes','safety_quality_basis']) for x in inputs)
assert sha(A/'design_freeze.json')=='443b958c7821f53dd8feeddaeca6199e76c290ccd94627f4b4b2ce85e66accfc'
assert sha(A/'candidate08_prompt_PROPOSED.txt')=='d79c097443fa249051c5264da1ff532ddf7d984225ac3e776807de95f7f21803'

# Fresh independent semantic observations after actually reading every current
# input/context and all five current actual reasons, quotations and extra fields.
N={
'C03-CONTROL-001':'疾病危害和临床急需不自动成为药物风险、效果或治疗获取缺口；五维0有据。',
'C03-CONTROL-002':'明确尚无可获得治疗并建立常规渠道，F/access成立；未将缺口冒充药效或创新。',
'C03-CONTROL-003':'审批提速明确连接尽快上市及更多患者需要，可按改善获取支持F1；冻结F0强调一般需求并非缺口，也有依据。保留宽窄范围边界，不把期待改为1。',
'C03-CONTROL-004':'短缺储备与持续供药是实质获取安排，F/access有据，其余四维不补造。',
'C03-CONTROL-005':'已入组随机转组不等于治疗获取缺口或效果判断，五维0有据。',
'C03-CONTROL-006':'无其他可获得治疗与提供研究药对应，符合试验获取例外；治疗需要不自动是效果或创新。',
'C03-CONTROL-007':'公布结果、通知落实无具体保障对象内容，五维0与一般发布边界一致。',
'C03-CONTROL-008':'实际药费承担为Ec，给付范围扩展为F/access；当前未加缺乏独立依据的affordability，旧异议当前闭合但历史保留。',
'C03-CONTROL-009':'仅安排价格协商会议和通知企业，不等于实质药价条件，Ec0及其他0成立。',
'C03-CONTROL-010':'给出每盒支付标准，Ec1；不能只因价格或支付词补成可负担/保障，F0成立。',
'C03-CONTROL-011':'频繁监测的基层管理难度直接支持F/clinical_management；未写安全用途、经济成本或治疗效果，其他0正确。',
'C03-CONTROL-012':'一般处方制度未述药物损害、使用管理难度或评价内容，五维0成立。',
'C03-CONTROL-013':'创新对象与电话/平台提交形式不等于实体研发支持，I0及其余0有据；boundary_note合理记录范围。',
'C03-CONTROL-014':'向创新研发团队配备顾问和持续技术辅导支持I/research_support；一般研发方法不补S/E。',
'C03-CONTROL-015':'没有第七类的创新含义，序号与申请资格不构成I；其他0有据，不把完整0视作材料缺失。',
'C03-CONTROL-016':'明确原创化合物含义及原创属性资料要求支持I/attribute，序号不再是唯一依据。',
'C03-CONTROL-017':'普通适老包装文字要求不自行证明改良、安全风险或获取障碍；五维0与v1.4普通设计边界一致。',
'C03-CONTROL-018':'相对原制剂改良释药设计与频次变化支持I/attribute；频次减少不自动等于疗效或临床管理难度。',
'C03-CONTROL-019':'普通受体阻断机制未表达新颖性、药效结果或风险，五维0成立。',
'C03-CONTROL-020':'首次采用、新颖机制及原创性信息要求明确，I/attribute成立，未推定治疗效果。',
'C03-CONTROL-021':'一般商业秘密保密无专有数据排他权利或实质评价内容，五维0成立。',
'C03-CONTROL-022':'专有数据保护期限与排除其他申报权利支持I/attribute；泛试验数据未说明安全或效果内容。',
'C03-CONTROL-023':'冻结与旧独立意见把既合格品种公示纳入视作行政办理，偏好E/I0；当前模型用“符合条件”直接指向临床比较优势与创新资格，存在明确援引的可辩护1解释。保留两维作用域边界，不能只凭期待差异认定确定错误；F0正确区分支持程序与保障。',
'C03-CONTROL-024':'当前须证明明显生存获益以取得创新资格，E与I/qualification_advantage双锚成立；其余0有据。',
'C03-CONTROL-025':'药物不良反应监测及风险控制支持S；未把安全管理泛化成F或I。',
'C03-CONTROL-026':'平台数据安全不是药物安全，五维0有据。',
'C03-CONTROL-027':'降低复发率的临床证据要求支持E；不要求已有正面结果，其余0有据。',
'C03-CONTROL-028':'数据字段有效性不等于药物疗效，五维0有据。',
'C03-CONTROL-029':'药费过高及拟降低自付直接支持Ec/F；无力继续治疗另有获取障碍，access与affordability均有依据。',
'C03-CONTROL-030':'一般科研设备经费非药物治疗支付经济内容，且未明确创新研发对象，五维0有据。',
'C04-CONTROL-031':'再次递交续约申请不确定保障延续，F0及其他0有据；相应boundary_note不掩盖缺口。',
'C04-CONTROL-032':'保障协议期满继续供应三年直接支持F/access，无费用承担所以不补Ec。',
'C04-CONTROL-033':'药物年度治疗费用阈值为Ec，父谓词实际决定保险继续承担三年支持F/access；不自动加患者负担。',
'C04-CONTROL-034':'治疗费用阈值仍属Ec，父谓词仅安排审核顺序所以F0；Ec理由“以预算倍数限制年度治疗费用”略将排序标准写成费用管制，属理由精度提醒，不是确认标签错误。',
'C04-CONTROL-035':'创新项目背景只补对象，专业沟通形式选择没有实际指导资源，五维0有据；与既有真实沟通边界不强合并。',
'C04-CONTROL-036':'专门专家团队与持续研究方案辅导支持I/research_support，一般研究方案不补S/E。',
'C04-CONTROL-037':'既有支持项目身份及季度进度报告是事务义务，当前不传播为I，其余0有据。',
'C04-CONTROL-038':'明确原创属性条件及专门研发资源，I1；attribute与research_support分别有依据，不补经济标签。',
'C05-NEW-001':'创新研发背景下申请人安全义务支持S，不能扩大为机构给研发支持I；保护受试者不是F获取。',
'C05-NEW-002':'机构配置专家并提供试验药物风险辅导，S与I/research_support独立共存，不删实际安全内容。',
'C05-NEW-003':'创新项目仅界定报告者，季度进度事务不成为I，其他0有据。',
'C05-NEW-004':'创新研发对象取得具体研发设备优先权为实质支持，I/research_support成立，不把设备经费/资源自动计Ec。',
'C05-NEW-005':'发布指南的创新支持目的不替代本条实体支持，五维0有据。',
'C05-NEW-006':'创新研发期间实际安排专业人员指导研究设计，I/research_support成立；试验资料没有给出安全/效果用途，S/E0有据。',
'C05-NEW-007':'父语境消解当前真实指代为原创药物，当前机构专门研究咨询为I/research_support；不另传attribute。',
'C05-NEW-008':'当前对象普通药品，下一节原创项目不传入当前咨询；五维0成立，相应resolved_context_issue消解对象合理。',
'C05-NEW-009':'基金预算增幅本身Ec，父条件直接决定保障延续和药费支付，F/access有据。',
'C05-NEW-010':'相同预算指标用于材料办理顺序仍Ec1，父句明确不决定给付供应所以F0；理由把排序阈值说成基金预算约束稍过强，属精度提醒。',
'C05-NEW-011':'已经履行两年保障只是管理转类对象前提，当前未规定继续/退出，F0及其他0有据。',
'C05-NEW-012':'F/access明确；Ec0匹配旧期待且未给具体药费条件内容，可成立。旧07独立报告曾按原给付条件延续支持Ec1，须保留解释差异，不冒称统一真值。',
'C05-NEW-013':'希望增加支付范围者先提交书面申请，仅办事要求不确定药物覆盖或费用责任，五维0有据。',
'C05-NEW-014':'实际新增保障范围与基金承担支持Ec/F access；I0把新增适应证看作保障对象有依据，但“经审定新增适应证”也可读成产品属性变化，保留控制文本作用域歧义，不把I0匹配期待当充分证据。',
'C05-NEW-015':'确定错误：自足综合评价方法定义未引导、援引或依赖后项清单；structured_following_units仅是提供位置，模型把相邻评价项目传播为当前五维要求。原全0期待与本次全五维独立判定0一致；五个1理由、unit证据及错误承接关系均不成立，resolved_context_issue亦误称补足缺口。',
'C05-NEW-016':'当前明确“应包括下列”真实控制后项实质清单，五维1及I/attribute、F/affordability有据；与015不能仅按同主题混同。',
'C05-NEW-017':'一般剂量调整未说明安全、效果、改良或管理难度，五维0有据。',
'C05-NEW-018':'每周采血监测管理负担和基层能力评价直接F/clinical_management；未写药物风险所以不补S，非经济负担所以不补Ec。',
'C05-NEW-019':'新申报编号本身不证明创新；明确组成/剂型未变可看行政未变说明（偏好I0），也可依否定关注原则看属性判断I1。保留既有合理边界，原期待不改，不能以分数强迫。',
'C05-NEW-020':'明确液体到粉末剂型的相对产品改变，I/attribute有据，无须创新字样或优效；剂型名称不自动补S质量。',
'C05-NEW-021':'数据格式存档保密义务不是专有保护权利，也未指定风险/效果内容，五维0有据。',
'C05-NEW-022':'六年专有保护及阻止他人依赖申报是知识产权实质权利，I/attribute有据；未推试验数据S/E。',
'C05-NEW-023':'疾病严重、急需、希望尽早使用没有明确不可获得治疗缺口，五维0有据。',
'C05-NEW-024':'明确无可获得治疗及指定机构持续供应，F/access成立，未推效果或经济内容。'}
assert set(N)==set(src)
boundaries={('C03-CONTROL-003','F'),('C03-CONTROL-023','E'),('C03-CONTROL-023','I'),('C05-NEW-012','Ec'),('C05-NEW-014','I'),('C05-NEW-019','I')}
precision={('C04-CONTROL-034','Ec'),('C05-NEW-010','Ec')}
issues_by_id={ident:[x for x in raw['issue_records'] if x['id']==ident] for ident in src}
rows=[];mismatches=[];quote_count=0;literal_errors=[];semantic_quote_failures=[]
for a in raw['rows']:
 ident=a['id'];i=src[ident];e=expected[ident]
 dims={}
 for d in D:
  if a['labels'][d]!=e['labels'][d]:mismatches.append({'id':ident,'dimension':d,'actual':a['labels'][d],'original_expected':e['labels'][d]})
  assert a['dimension_reasons'][d]
  status='SUPPORTED_CURRENT_CONTENT'
  preferred=a['labels'][d]
  if ident=='C05-NEW-015':status='CONFIRMED_FALSE_POSITIVE_WRONG_CONTEXT_ATTACHMENT';preferred=0
  elif (ident,d) in boundaries:status='RETAINED_INTERPRETIVE_BOUNDARY_NOT_FORCED';preferred=None
  elif (ident,d) in precision:status='LABEL_SUPPORTED_REASON_PRECISION_COMMENT'
  dims[d]={'actual':a['labels'][d],'original_frozen_expected':e['labels'][d],'original_expectation_matches':a['labels'][d]==e['labels'][d],
     'actual_reason_actually_read':True,'reason_and_evidence_semantic_status':status,'independent_unambiguous_preferred':preferred,
     'allowed_boundary_readings':[0,1] if (ident,d) in boundaries else None}
 ev=[]
 for q in a['evidence']:
  literal=any(q['quote'] in s for s in ([i['text']] if q['source']=='unit' else strings(i.get('contexts',{}))))
  if not literal:literal_errors.append({'id':ident,'evidence':q})
  meaningful=ident!='C05-NEW-015'
  if not meaningful:semantic_quote_failures.append({'id':ident,'dimension':q['dimension'],'source':q['source'],'reason':'Abstract unit or neighbouring list does not establish current dimension/attachment.'})
  ev.append({'dimension':q['dimension'],'source':q['source'],'quote_sha256':hashlib.sha256(q['quote'].encode()).hexdigest(),'literal_in_proper_source':literal,
      'semantic_attachment_supported':meaningful,'boundary_in_dimension':(ident,q['dimension']) in boundaries})
  quote_count+=1
 for d in D:
  if a['labels'][d]:assert any(q['dimension']==d and q['source']=='unit' for q in a['evidence'])
 assert a['safety_quality_basis']=='no_quality_basis'
 row_status='CONFIRMED_ERROR' if ident=='C05-NEW-015' else ('RETAINED_BOUNDARY' if any((ident,d) in boundaries for d in D) else ('REASON_PRECISION_COMMENT' if any((ident,d) in precision for d in D) else 'SUPPORTED'))
 aux_status='UNSUPPORTED_DUE_TO_WRONG_CONTEXT_ATTACHMENT' if ident=='C05-NEW-015' else ('BOUNDARY_DEPENDENT' if ident in ['C03-CONTROL-023','C03-CONTROL-003','C05-NEW-019'] else 'INDEPENDENTLY_SUPPORTED')
 rows.append({'id':ident,'full_input_contexts_and_all_five_actual_fields_actually_read':True,'status':row_status,'reviewer_semantic_note':N[ident],
  'five_dimensions':dims,'evidence_review':ev,
  'auxiliary_fields_review':{'predeclared_auxiliary_expectations_available':False,'invented_expected_auxiliary_values':False,
    'actual_I_subtypes':a['innovation_subtypes'],'actual_F_subtypes':a['fairness_subtypes'],'I_F_semantic_status':aux_status,
    'actual_S_quality_basis':a['safety_quality_basis'],'quality_review':'未出现独立药品质量安全内容；临床不良反应/风险依据不等于质量安全；制剂名称也不自行赋质量依据。'},
  'actual_issue_records':issues_by_id[ident],
  'issue_review_status':'INCORRECT_RESOLVED_CONTEXT_ISSUE' if ident=='C05-NEW-015' else ('SCOPE_BOUNDARY_RETAINED' if ident=='C03-CONTROL-023' else 'READ_NO_ADDITIONAL_CONFIRMED_MATERIAL_DEFECT')})
assert not literal_errors
assert len(mismatches)==9
assert len(raw['issue_records'])==15

attempts=[];files=[P/'actual-inherited-controls/inherited62_review_plan_PREOUTPUT.json',A/'design_freeze.json',A/'candidate08_prompt_PROPOSED.txt',A/'synthetic62_inputs_UNCHANGED.jsonl',A/'synthetic106_expected_INHERITED_PRIVATE.json',A/'predeclared_acceptance_PROPOSED.json',R/'all_predictions.json',R/'all_predictions.jsonl',R/'run_plan.json',R/'execution_summary.json',R/'frozen_input.jsonl']
aggregate=[];aggregate_issues=[]
for batch in sorted((R/'batches').glob('batch-*')):
 s=read(batch/'selection.json');files.append(batch/'selection.json')
 ap=sorted((batch/'attempts').glob('attempt-*'))
 assert len(ap)==1 and s['selected_relative_path'].endswith('/attempt-01')
 for attempt in ap:
  val=read(attempt/'validation.json');meta=read(attempt/'run_metadata.json');r=read(attempt/'raw_output.json')
  assert val['valid'] is True and not val['errors'] and not meta['errors']
  aggregate.extend(r['rows']);aggregate_issues.extend(r['issue_records'])
  attempts.append({'batch':batch.name,'attempt':attempt.name,'selected':True,'earlier_attempts_exist':False,
   'material_issue_flags':[x for x in r['issue_records'] if x['status']=='material_issue'],'validation_errors':val['errors'],
   'all_issue_records_actually_read':True})
  files += [attempt/n for n in ['raw_output.json','run_metadata.json','validation.json','event_output_binding_audit.json']]
assert aggregate==raw['rows'] and aggregate_issues==raw['issue_records']
assert len(attempts)==3 and not any(x['material_issue_flags'] for x in attempts)
prior=BASE/'候选方案/semantic-review/independent-controls/candidate07_actual106_independent_semantic_review.json'
files.append(prior)
files += [ROOT/'outputs/coding-revision-20261007-r3/protocol'/x for x in ['完整五维手册-v1.3.md','共用操作说明-v1.4.md']]
before={str(f):sha(f) for f in files}
assert not (A/'runtime-unchanged-v2/exposed240-candidate08-first-run').exists()
report={'status':'FAIL_CONFIRMED_INHERITED62_SEMANTIC_ERROR_COMPLETE_REVIEW_NOT_A_CONTINUATION_GATE',
 'created_at_UTC':datetime.now(timezone.utc).isoformat(),'reviewer':'/root/validation_state_oct8','bindings':[bind(f) for f in files],
 'actual_coverage':{'units':62,'dimension_labels':310,'dimension_reasons_actually_read':310,'evidence_records_actually_read':quote_count,
  'all62_I_F_subtype_arrays_and_quality_fields_read':True,'top_level_issue_records_actually_read':15,'actual_attempts_examined':3,
  'earlier_failed_attempt_count':0,'material_issue_flags_across_all_actual_attempts':0,
  'author_other44_or_real240_outputs_semantically_read':False,'protected267_originals_read':False},
 'mechanical_comparison':{'frozen_label_matches':301,'frozen_label_mismatches':mismatches,'literal_evidence_errors':literal_errors,
  'old62_has_no_predeclared_auxiliary_expectations':True,'original_expectations_or_input_or_output_edited':False,
  'matching_labels_are_not_sufficient_semantic_validation':True},
 'confirmed_errors':[{'id':'C05-NEW-015','dimensions':D,'actual':{d:1 for d in D},'independently_supported':{d:0 for d in D},
   'basis':'Current self-contained abstract definition has no explicit forward reference or controlling content requirement. Mere following-unit placement does not inherit a neighbouring list.',
   'manual_basis':['v1.3 line17:context disambiguates referents/objects/conditions/columns, not all dimensions','v1.3 lines146-148:self-contained introductory content and necessary missing continuation distinguished','v1.4 line7:actual current relation, no background copying'],
   'reason_evidence_issue_effect':'All five reasons falsely assert explicit continuation; ten quotes are literal but current attachment is false. I attribute/F affordability inherit the same false attachment. resolved_context_issue incorrectly claims a missing content relation was resolved.'}],
 'confirmed_error_units':1,'confirmed_error_dimensions':5,
 'retained_boundary_cells':[{'id':i,'dimension':d,'judgment':'No single truth forced; see fresh row note and preserved original expectation.'} for i,d in sorted(boundaries)],
 'reason_precision_comments':[{'id':i,'dimension':d,'note':N[i]} for i,d in sorted(precision)],
 'historical_opinion_precision':{'008_extra_affordability':'Current access only is supported; older error record remains.',
  '034_reason_precision':'Current labels supported, but wording again overstates sorting criterion as treatment-cost restriction; do not claim wording issue closed.',
  '003_F':'Prior independent07 supported1, original expectation0; both readings retained here.',
  '012_Ec':'Prior independent07 supported1; current08 Ec0 agrees original expectation0 and is defensible under narrow current-content reading. No uniform adjudication invented.',
  '019_I':'Existing negative-attribute versus mere unchanged administration boundary retained.',
  '023_EI':'Prior independent07 preferred0; current08 1 uses explicit condition reference. Scope ambiguity retained without rewriting expectation.',
  '014_I':'Additional ambiguity of newly approved indication versus merely newly covered indication recorded even though label matches original expectation.'},
 'attempt_material_flag_review':attempts,'reviews':rows,
 'decision_limits':{'continuation_PASS_gate_written':False,'later_exposed240_directory_absent_at_review':True,
  'confirmed_failure_requires_later240_NOT_RUN':True,'candidate08_adoption_or_full4924_authorized':False,
  'root_owns_stage_decision':True},
 'reviewer_model_calls':0,'reviewer_CLI_invocations':0,'source_files_modified':False,
 'limitations':['These are inherited synthetic development controls, not external human validity or a corpus error-rate estimate.',
  'The complete62 review documents a confirmed failure despite literal/schema success; fixed expectations were not revised to fit outputs.',
  'Boundary judgments are separately retained and cannot rescue the confirmed015 failure.',
  'Current adopted full-corpus methods remain Rule39 and completeLLM03; this report does not alter A/B human-adjudicated references or manuscript.']}
target=O/'candidate08_inherited62_actual_full_semantic_review_PRIVATE.json';assert not target.exists()
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for f in files:assert sha(f)==before[str(f)]
print(json.dumps({'status':report['status'],'path':str(target),'sha256':sha(target),'units':62,'dimension_cells':310,'actual_quotes_read':quote_count,'confirmed_error_dimensions':5,'mechanical_label_mismatches':9,'boundary_cells':len(boundaries),'continuation_gate_written':False},ensure_ascii=False))
