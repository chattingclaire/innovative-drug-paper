"""Prepare immutable development inputs and prompt; never relabel policy records."""
import json, pathlib, hashlib, shutil, datetime

HERE = pathlib.Path(__file__).resolve().parent
R3 = HERE.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def lines(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def jsonl(p, rows): p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))

base = R3/'llm-v32/完整系统提示词-v32-候选02.txt'
text = base.read_text()
assert sha(base)=='682770e2fb6f1a6b8b7ba1703f6900d7ee0d586179282b94c14e0b23feec300e'
text=text.replace('全五维LLM语义执行说明 v32 候选02','全五维LLM语义执行说明 v32 候选03-development',1)
old='**支持资格与通用办理事务分别判断。** 已核验对象是药物研发创新，且给定材料明确专门指导、优先资源、加速支持或其他实体支持制度时，当前实质规定该支持的适用资格、研发阶段范围或取得/失去支持的条件，可以涉及research_support。这属于支持内容的资格规定，不要求本句再次列出全部资源。仅安排填表、报送材料、沟通申请形式、截止时间或一般报告节奏，未实质确定支持资格或内容时，仍不自动计I。只有程序名而没有创新对象证据时也不能纳入。'
new='**支持资格与通用办理事务分别判断。** 按v1.4判断当前规定本身是否新增或改变创新研发支持的实际内容、资源或资格。上下文可补足已明确承接的支持对象和措施，但不得仅因为条目位于创新项目中，就把一般阶段描述或程序身份认定为实体支持。资格条款仍可涉及I，须具体说明当前条件如何规定得到或失去何种已明确创新研发支持；仅安排填表、报送材料、沟通申请形式、截止时间或一般报告节奏，不自动计I。若仅能从背景推出支持关系而当前承接有边界争议，按完整手册独立判读并记录boundary_note，不强行趋同。'
assert text.count(old)==1
text=text.replace(old,new)
clarification='''
## 候选03：命题、资格和目标的对称语义核对

以下核对帮助执行完整手册及v1.4，不新增维度或按部门设标准。先对当前文字作语义判断，不搜索词表；教学构造例不是政策原句，也不是本批答案。

1. **F的需求迫切不等于获取不足。** 疾病严重、临床急需、希望及早上市或满足更多需求，单独都不能补出尚无可用治疗、短缺、负担或获取障碍。当前明确治疗空白、需求未获满足、缺少可获得治疗或供应短缺，则按原F范围纳入；不额外要求说明医保支付障碍。不能为减少误报一律排除短缺或未满足治疗需要，也不能把一般改善疗效改叫获取保障。
2. **当前规定的行为和内容分别核对。** 申请沟通的形式、名单公示、文件发布、结果公布及组织落实本身不是实体研发支持或实际药物保障。不要用这些活动通常有助于研发/获取的推论赋I/F。但同句独立陈述专门配置指导资源、明确创新属性、药物供应缺口、实际给付/供应条件时，必须分别保留对应维度，不能把含有程序词的整句排除。
3. **条件性保障与已经实施不同。** 对药物保障范围、患者获取或保障连续性作实质规定/评价，即使使用拟、可以、经程序确定、退出等表达，也可涉及F；不要求列出具体药名、患者姓名或已发生给付结果。当前只是允许重新申请或选择办理路线，未说明实际保障内容时不自动纳入。条件只依其所控制的实际谓词判断；不要把邻句的效果传播过来，也不要忽略真正控制当前条件的父条款。
4. **创新对象、属性和支持不混用。** 创新药名称不等于创新属性；一般指南目的和材料办理便利不等于实体创新研发支持。针对创新研发明确配置人员/指导资源或实质研发便利时仍按I纳入。仅有注册分类序号，即便文本说按现行分类，不从常识补出该序号的创新含义；给定定义明确表明原创/改良或创新分类时可以纳入。明确产品改良不另要求优效，普通适龄便利不自动变成改良。
5. **指代不能把全部条件传下去。** “符合条件后公示/办理”只是处理动作时，不把之前列出的所有维度复制为当前评价内容。当前明确要求满足某项实质条件、评价/提供该内容，或子项由父谓词直接控制时，则使用对应给定内容；说明到底承接了对象、评价内容还是仅处理流程。争议不以参考答案解决。
6. **完整保留S/E/Ec。** 药物安全管理、风险控制或明确安全内容不额外要求列出具体损害结果；效果证据用途须有真实承接，研究同时涉及多个主题不代表每个方法句自动涉及全部主题。一般整体健康宗旨不自动等同药物效果。价格协商的会务流程、协议数据确认与价格/费用实质内容分别判断；经济性不要求必须出现金额。知识产权范围内用安全/疗效名称分类资料，不因此自动成为新增安全/疗效评价要求；若同句独立要求评价或提交相应证据仍纳入。

教学对照（仅标所讨论维度，实际每条仍独立判断全部五维）：
- “推动药物更早上市以回应迫切需求”本身不足以赋F；“该人群没有可获得的治疗药物，安排紧急供药”有F依据。
- 创新研发背景下“可选择线上或书面沟通”本身不足以赋I；“向创新药研发团队配置专门技术顾问”有I支持依据。
- “公布调整后的目录并通知各地”本身不足以赋F；“调整后的药物给付范围涵盖指定的新适应症”有F依据。
- “某注册编号的药品可申请”不能仅凭编号赋I；给定文字定义其为原创新化合物时可依据该定义判断I。
- “符合前述条件的先公示再办理手续”不复制前述每个维度；“申报资料须比较药物相对标准治疗的生存获益”明确关注E。
- “与会人员讨论价格协商时间”不因价格一词赋Ec；“药物治疗费用由保险与患者分别承担”明确关注Ec，有患者可负担内容时另判F。

输出前核对每个I/F的理由是否把当前文字没有表达的未满足、创新身份、支持措施或实际保障关系补了进去，也核对是否因程序/条件/目的形式错删明确实质内容。所有修订均限于判断；禁止改变输入、补写引文或读取外部材料。

'''
marker='--- 冻结的完整手册（原样） ---'
text=text.replace(marker,clarification+'\n'+marker)
technical=(R3/'llm-v32/full-production-candidate02-material-v14-source-citation-reconciled/frozen_technical_prompt.txt').read_text()
suffix=technical[technical.index('【引文格式澄清：citation-isolation-tech01】'):]
text=text.rstrip()+'\n\n'+suffix
prompt=HERE/'candidate03_prompt.txt';prompt.write_text(text)
manual=R3/'protocol/完整五维手册-v1.3.md'
operation=R3/'llm-v32/共用实质操作说明-v1.4-运行摘录.txt'
assert manual.read_text().strip() in text
assert operation.read_text().strip() in text
assert 'RECODE25-' not in text and '0.80' not in text
for name in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']:
    shutil.copyfile(R3/'llm-v32'/name,HERE/name)

source=R3/'effective_blind_inputs_v14.jsonl'
assert sha(source)=='6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763'
refs=lines(R3/'statistics/final-v14/candidate_reference.jsonl')
ids={r['id'] for r in refs};assert len(ids)==240
actual=[r for r in lines(source) if r['id'] in ids]
assert len(actual)==240
jsonl(HERE/'exposed240_inputs.jsonl',actual)

# Synthetic control expectations are fixed before model calls and never put in input packets.
tests=[]
def add(text, positives, rationale, contexts=None):
    rid=f'C03-CONTROL-{len(tests)+1:03d}'
    tests.append({'input':{'id':rid,'text':text,'contexts':contexts or {}},'labels':{d:int(d in positives) for d in ['S','E','Ec','I','F']},'rationale':rationale})
add('该病严重危害健康，临床需要十分迫切。',[], '迫切程度不等于治疗缺口。')
add('该人群尚无可获得的治疗药物，应建立常规用药获取渠道。',['F'],'明确缺少可获得药物和获取渠道。')
add('缩短审批时间，争取药物尽快上市以满足更多患者的需求。',[],'上市效率与一般需求不证明获取缺口。')
add('建立药物短缺储备，保障患者日常治疗所需药品持续供应。',['F'],'明确短缺和持续供药。')
add('已经入组的患者可按随机安排转入另一治疗组。',[],'试验分组机会并非明确治疗获取障碍。')
add('对没有其他可获得治疗选择的患者，安排提供研究药物以满足其治疗需要。',['F'],'明确治疗获取缺口及对应安排。')
add('发布目录调整结果并要求各单位做好通知和落实工作。',[],'公布落实本身不提供实际保障内容。')
add('本药的保险给付范围扩展至规定的新适应症，相关药费由保险承担。',['Ec','F'],'实际药费责任和给付范围。')
add('工作人员应安排药品价格协商会议并通知参会企业。',[],'价格协商会务，未规定药价或经济评价。')
add('该药统一支付标准为每盒二十元。',['Ec'],'药价标准不自行补患者负担或保障内容。')
add('应评价该药在基层使用时必须频繁监测带来的管理难度。',['F'],'明确药物临床管理难度评价。')
add('医疗机构应完善处方管理制度并规范开具处方。',[],'一般合理用药行政规范。')
add('创新药申请人可选用电话或平台方式提交沟通申请。',[],'创新对象名称与申请形式不等于实体支持。')
add('为创新药研发团队配备专职顾问，提供持续的研发技术辅导。',['I'],'针对创新研发的实质人员与指导资源。')
add('第七类注册药品可以提出本次申请。',[],'注册序号未给定创新含义。')
add('本条第七类注册药品是指含有原创化合物的创新药，申报时须说明其原创属性。',['I'],'给定分类含义与原创属性资料要求。')
add('药品外包装应标示适于老年人阅读的清晰文字。',[],'一般适龄设计不自动创新或公平。')
add('通过改良原有制剂的释药设计，将原每日三次给药改为每日一次。',['I'],'明确相对原产品改良，不要求优效。')
add('本药的作用机制是阻断该受体的信号传导。',[],'普通机制未表达新颖性。')
add('说明该药首次采用的新颖作用机制及其原创性。',['I'],'明确要求创新机制属性信息。')
add('申请资料属于商业秘密，未经许可不得公开。',[],'一般保密不等于创新专有权利。')
add('该创新药的专有试验数据受六年保护，期限内不得被其他申请人用于申报。',['I'],'明确专有试验数据权利及期限。')
add('符合条件的品种按程序公示，公示后办理纳入手续。',[],'处理动作不复制所有前置条件。',{'paragraph_context':[{'text':'创新或改良药物如具备显著临床比较优势，可申请支持程序。'}]})
add('申请该创新药资格须证明其相比现有标准治疗具有明显生存获益。',['E','I'],'当前创新资格和实质临床比较优势双锚点。')
add('定期监测本药不良反应，并据此调整风险控制措施。',['S'],'明确药物损害识别与控制。')
add('定期检查申报平台的数据安全设置和账户权限。',[],'网络安全非药物安全。')
add('应补充本药降低复发率的临床证据。',['E'],'效果证据要求不要求正面结果。')
add('研究系统应检查数据字段的有效性。',[],'数据有效性非药物疗效。')
add('患者因药费过高无力继续治疗，拟降低其药费自付比例。',['Ec','F'],'明确患者药费支付负担和药费责任。')
add('科研项目年度经费不足，应增加实验室设备采购资金。',[],'科研设备经费非药物治疗支付。')
assert len(tests)==30
jsonl(HERE/'synthetic30_inputs.jsonl',[t['input'] for t in tests])
dump(HERE/'synthetic30_expected_PRIVATE.json',{'status':'predeclared_before_model_calls','independent_external_validation':False,'synthetic_not_policy_quotes':True,'tests':tests})

ledger=R3/'statistics/final-v14-reference-error-ledger_PRIVATE.json'
records=json.loads(ledger.read_text())['records']
# Assessments are direct semantic review decisions, separate from all machine outputs.
confirmed={('RECODE25-01446','F'):'需求迫切被补成未获满足。',('RECODE25-00292','F'):'及早上市满足需求不独立证明获取缺口。',('RECODE25-00066','F'):'急需疫苗定义未表达获取缺口。',('RECODE25-04164','I'):'沟通申请形式被扩成实体创新支持。',('RECODE25-00967','F'):'发布与组织落实被补成实际给付内容。',('RECODE25-01765','I'):'资料准备效率及指南宗旨被扩成实体创新支持。',('RECODE25-01765','F'):'迫切需求被补成尚无可用治疗。',('RECODE25-04588','I'):'公示纳入动作复制父条件的创新内容。',('RECODE25-04588','F'):'公示纳入程序被补成治疗获取安排。',('RECODE25-00090','F'):'急需疫苗被补成未满足获取。',('RECODE25-03712','I'):'只凭注册序号从常识推定创新分类。',('RECODE25-03865','F'):'要求已作具体个别给付决定，遗漏明确形成新实际支付范围的规定。'}
review=[]
for r in records:
    if r['dimension'] not in ['I','F'] or not any(e['method']=='LLM' for e in r['errors_relative_to_AI_reference']): continue
    key=(r['id'],r['dimension'])
    category='repairable_execution_misuse' if key in confirmed else 'reference_boundary_dispute'
    reason=confirmed.get(key,'对实际支持资格、语境承接、治疗短缺/渠道或保障持续条件存在合理边界分歧；不以任一参考优先或较高一致率定输赢。')
    review.append({'id':r['id'],'dimension':r['dimension'],'category':category,'semantic_diagnosis':reason,'baseline_prediction':r['predictions']['LLM'],'references_preserved':r['references'],'candidate_match_does_not_prove_correct':True,'full_original_ledger_record':r})
dump(HERE/'IF_semantic_diagnosis_PRIVATE.json',{'ledger_sha256':sha(ledger),'manual_sha256':sha(manual),'operation_excerpt_sha256':sha(operation),'confirmed_misuse_n':len(confirmed),'reviewed_case_dimension_n':len(review),'records':review})

counts={d:sum(r['labels'][d]==1 for r in refs) for d in ['S','E','Ec','I','F']}
freeze={'status':'candidate03_development_frozen_before_actual_model_calls','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method_id':'LLM-v32-candidate03-development','schema_execution_version':'LLM-binary-v32 (format family, not prompt identity)','model':'gpt-5.6-sol','reasoning_effort':'medium','base_prompt_sha256':sha(base),'prompt_sha256':sha(prompt),'manual_verbatim_sha256':sha(manual),'operation_substantive_verbatim_sha256':sha(operation),'source_v14_sha256':sha(source),'all_240_now_development_exposed':True,'all_reference_labels_unchanged':True,'new_independent_validation_claimed':False,'synthetic_control_expected_sha256':sha(HERE/'synthetic30_expected_PRIVATE.json'),'development240_input_sha256':sha(HERE/'exposed240_inputs.jsonl'),'synthetic30_input_sha256':sha(HERE/'synthetic30_inputs.jsonl'),'reference_positive_counts_development_only':counts,'rare_class_note':'Counts and errors will be reported explicitly; low prevalence is a sampling property, not a reason to alter labels or require a kappa threshold.','planned_calls':{'exposed240':10,'synthetic30':2,'development_total_nominal':12,'technical_maximum':36,'future_full4924_nominal':197,'future_full4924_technical_maximum':591},'workers':3,'semantic_gate':'Actual complete first-valid execution; synthetic positive and negative controls reviewed separately; confirmed misuse changes and every regression reviewed. No kappa target and no acceptance by matching a reference. No systematic new semantic misuse.','technical_selection':'first valid actual attempt; at most 3 identical request attempts only after execution/schema/literal/tool failure; keep every failure','source_modification':False,'baseline_v14_replaced':False,'scope':'All five dimensions are newly judged together per actual record; never splice prior dimensions.'}
dump(HERE/'candidate03_development_freeze.json',freeze)
print(json.dumps({'prompt_sha256':sha(prompt),'freeze_sha256':sha(HERE/'candidate03_development_freeze.json'),'reference_positive_counts':counts,'confirmed_misuse_n':len(confirmed),'boundary_cases':len(review)-len(confirmed)},ensure_ascii=False))
