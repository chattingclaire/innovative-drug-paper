from pathlib import Path
import json,hashlib,datetime,copy
R=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent;V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v10-generic-relationship-sol';OLD=V.parent/'joint-v9-generic-relationship-sol';D=R/'08-audits/v9-generic-relationship-repair-design-sol/revision02-bidirectional-before-implementation'
def bind(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
sha='b'*64
ref={'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'paragraph_ids':['p0002']}}
def ctx(cid,kind,text,**loc):return {'context_id':cid,'kind':kind,'text':text,'source_ref':{'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':loc},'structure':loc.copy()}
def unit(text,contexts):return {'text':text,'source_ref':copy.deepcopy(ref),'contexts':contexts}
cs=[]
def case(name,u,expected,reason,no_new=False):cs.append({'name':name,'semantic_input':u,'expected':expected,'hard_assertion':True,'semantic_reason':reason,'synthetic':True,'must_not_add_v10_positive':no_new})
# Finite programme source has an explicit complete same-member cross-reference.
member='(六)药监机构规定其他优先审评审批的情形。'
parent='药品上市许可申请时,以下具有明显临床价值的药品,可以申请适用优先审评审批程序:'
def priority(reference,beneficiary):
 raw='甲优先审评审批程序\n一、适用范围\n'+parent+'\n'+member+'\n二、工作程序\n对于'+beneficiary+'，申请人可以在药品上市许可申请时按照适用范围“'+reference+'”提出优先审评审批申请。\n三、工作要求\n按规定审评。'
 return unit(member,[ctx('cur','paragraph',member,paragraph_id='p0002'),ctx('parent','parent_paragraph',parent,paragraph_id='p0001',target_paragraph_id='p0002',sequence_index=0),ctx('leaf','source_textleaf',raw,unicode_code_point_interval_half_open=[0,len(raw)])])
case('v10_crossreference_different_member',priority('(五)其他申请情形','临床急需境外已上市境内未上市的罕见病药品'),{'F':0},'需要分支所明确指向的是另一个完整成员；同序号/同程序不能扩散。',True)
case('v10_crossreference_without_drug_gap',priority(member.rstrip('。'),'具有明显临床优势的药品'),{'F':0},'完整成员相同仍须需要对象；单纯优势不能倒补F。',True)
# Complete synthetic plan: actual body and exceptional scope stay in the source.
def plan(text,scope='试点项目范围为1类创新药（疫苗产品除外）临床试验申请。',extra=''):
 raw='乙药临床试验审评审批试点工作方案\n一、工作目标\n开展试点工作。\n二、纳入试点工作的有关要求\n（一）试点区域\n在具备条件的省开展试点。\n（二）试点项目\n'+scope+'\n（三）试点机构\n试点机构已建立在申请人提交新药临床试验申请前提供临床试验项目立项服务的工作制度。\n三、试点工作实施步骤\n（三）试点项目申请\n1.提出申请。符合要求的申请人自愿申报试点项目。'+extra+text+'\n（四）审评审批\n经确认的试点项目，药审中心在受理临床试验申请后30个工作日内完成审评审批。\n四、时间安排及预期成果\n工作为期一年。\n五、保障措施\n（三）加强技术培训\n药审中心为试点区域临床试验机构提供人员培训，以提高临床试验机构方案审核技术能力。\n'
 return unit(text,[ctx('cur','paragraph',text,paragraph_id='p0002'),ctx('plan','source_resource_text',raw,character_range_0based_halfopen=[0,len(raw)],sections='方案标题、引言及一至五全部正文')])
case('v10_wrong_drug_type_pilot',plan('疫苗项目申请人在项目申请前可提出新药临床试验申请前沟通交流。'),{'I':0},'疫苗被实际试点范围排除，不能套用1类创新的对象。',True)
case('v10_pilot_other_beneficiary',plan('仿制药乙申请人在项目申请前可提出新药临床试验申请前沟通交流。'),{'I':0},'当前受益对象是仿制药乙；同方案创新范围不能给错主体。',True)
case('v10_pilot_flow_only',plan('申请人在项目申请前须填写沟通交流申请表。'),{'I':0},'填写申请表未实际开放或提供技术沟通，不继承机会。',True)
case('v10_pilot_purpose_only',plan('为支持创新药研发，现将试点工作方案印发。'),{'I':0},'仅印发宗旨未当前实施试点或提供服务。',True)
case('v10_training_nonpilot_only',plan('药审中心仅为非试点机构提供人员培训，以提高临床试验机构方案审核技术能力。'),{'I':0},'对象只限非试点分支；不能借试点创新项目范围。',True)
# Current mechanism must consume its own actual innovation appraisal.
t='建立了覆盖申报、评审等全流程支持创新的机制。';b=t+'另一常规药管理机制对创新价值进行量化和分级。'
case('v10_innovation_appraisal_other_mechanism',unit(t,[ctx('cur','paragraph',b,paragraph_id='p0002')]),{'I':0},'当前未给实质创新标准；另一机制不能补当前泛支持。',True)
t='建立了覆盖申报、评审等全流程支持创新的机制。';b=t+'借助技术工具综合研判药品价值，并对创新价值进行量化和分级。'
case('v10_innovation_appraisal_actual_mechanism',unit(t,[ctx('cur','paragraph',b,paragraph_id='p0002')]),{'I':1},'当前实质建立机制，同段直接定义其药品创新价值评价内容。')
case('v10_pilot_preapplication_actual_service',plan('申请人在项目申请前可根据需要向药审中心提出新药临床试验申请前沟通交流。'),{'I':1},'同阶段当前可用技术沟通，完整项目范围明确创新对象；不借纳入后30日。')
save(A/'new-controls-fixed-before-edit.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':cs,'original_189_unchanged':True,'expected_outside_classifier_input':True})
inputs=[R/'03-manual/full4481-common-release-20261010-root/manual.txt',D/'real-controls-fixed-before-edit.json',D/'synthetic-controls-fixed-before-edit.json']+[OLD/p for p in ['supplemental-controls-before-attempt02.json','supplemental-controls-b-before-attempt02.json','supplemental-controls-before-attempt04.json','supplemental-controls-before-attempt06.json']]+[OLD/(n+'.py') for n in ['evidence','source_packet','source_receipts','relations','dimensions']]
inputs += [R/f'06-coding/full4481-common-v15-production-preparation-sol/packets/RECODE25-{i}.json' for i in ['00093','00381','00649','01382','01731','01743','01757']]
save(A/'design-freeze-before-edit.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':[bind(p) for p in inputs],'new_controls':bind(A/'new-controls-fixed-before-edit.json'),'max_local_candidate_control_executions':3,'only_IF':True,'excluded_material_change':'01402 supplemental material not read or consumed','no_score_target':True,'new_entry':'pure compound semantic current-text gate; all gated records regardless of old value selected','paths':{'F':'exact complete current member referenced by actual need-selected priority application in same finite programme','I3_tools':'specific tool selection/acceptance regulator communication under physically bounded same attachment innovative clinical scope','I1_appraisal':'actual current established innovation mechanism, same paragraph operational drug innovation valuation definition','I4_rights':'current qualified data-protection execution consumes supplied complete innovative entitlement article within same arrangement, preserving own-data exceptions','I3_pilot':'complete same plan plus current operative rollout/preapplication communication/institution technical training, each bound to actual beneficiary/stage, no purpose/flow/other branch inheritance'},'preserve_failure_and_pending':True})
(A/'design.md').write_text('本轮只新增有限关系证据及显式 I/F 消费者，保留冻结 v9 和原 189 控制。当前动作入口先由纯 current-text compound gate 判定；入口内仍需同对象、同阶段及有限原文治理边，不能由命中词直接判正。新 gate 只提名，所有旧 0/1/null 入 gate 均受影响候选。新增证据保存为 v10_IF_relationship，旧单位及对象消费者不读取此 kind。\n\n00093 仅消费对完整当前成员的明确引用和实际需要药品的优先申请；00381 要求完整附件角色序列、物理页及段落范围闭合，而非同源即适用；00649 限当前所建机制的药品创新价值量化定义；01382 限当前给予资格后的实质执行和包内完整创新保护条款；试点三项分别证明开展、项目申请前沟通、针对试点机构的实质技术培训，不以标题或宗旨代替操作关系。所有否定、例外和未纳入角色在各路径保留。\n\n01402 补材不进入本轮。旧 E 应答率失败已有独立手册审查，保留期待与失败。本轮最多三次完整有限控制执行，每次封存所有失败；开发控制不是正式准确性验收。\n')
for n in ['evidence','source_packet','source_receipts','relations','dimensions']:(V/(n+'.py')).write_bytes((OLD/(n+'.py')).read_bytes())
save(A/'pre-edit-output-seal.json',{'files':[bind(A/p) for p in ['prepare-design-and-controls.py','new-controls-fixed-before-edit.json','design-freeze-before-edit.json','design.md']],'self_excluded':True})
print(V)
