import json,pathlib,hashlib,collections,datetime
D=pathlib.Path(__file__).resolve().parent; P=D.parent/'llm-candidate05-preparation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes=json.loads((P/'candidate05_all_changes_PRIVATE.json').read_text())['rows']
controls=json.loads((P/'candidate05_all62_controls_PRIVATE.json').read_text())['tests']
ex=json.loads((D.parent/'validation-state-audit/future_human_v5_development_exclusion_metadata.json').read_text())
reserved=set(ex['all_registered_members_of_reserved_families_unit_ids'])
assert not (reserved & {r['id'] for r in changes})
DIM=['S','E','Ec','I','F']
# Manual assessments below were written after reading every complete changed unit, its
# supplied context texts, all five actual reasons/evidence/subtypes and historical changes.
# They are reviewer judgments, never replacement production or human reference labels.
base0={
'S':'当前命题没有明确药物损害、用药风险或相应安全证据要求。',
'E':'当前命题没有明确药物效果、临床获益、药物治疗推荐或效果判断证据。',
'Ec':'当前命题没有实质药价、药费、治疗成本、支付责任或药品支付资源内容。',
'I':'当前命题没有创新属性、创新资格或针对创新研发的实质支持。',
'F':'当前命题没有实际药物保障获取、患者可负担或具体临床管理难度内容。'}
# Cases with current positive dimensions receive independent, case-specific grounds.
positive={
'00099':{'F':'明确“临床急需的短缺药品”本身已陈述供应获取缺口；不要求同句再新增供货义务。v1.4 F4。'},
'00110':{'F':'明确境外已上市、境内未上市的临床急需罕见病药品，讨论境内常规上市可获得状态；不是只有疾病严重或人群名称。v1.4 F4/F6。'},
'00118':{'F':'明确境外已上市而境内未上市的临床急需罕见病药品，陈述地域药品可获得状态。v1.4 F4/F6。'},
'00180':{'S':'明确不良反应、无法耐受、减量/终止治疗等药物损害。','E':'明确影响患者最终疗效及生活质量，属于药物效果。'},
'00663':{'E':'“患者获益显著”明确临床获益；非仅目录名称。','I':'“创新程度高”明确创新属性，非仅创新药类别名称。'},
'00891':{'Ec':'当前费用与预算200%阈值直接讨论药品费用；保留2025统计对象为纳入支付范围的药品费用。','F':'核验父谓词用本阈值决定通过补充协议确定新的支付范围；条件与实际保障范围改变直接组成命题。v1.4 F1。'},
'00964':{'F':'当前明确价格协商成功的药品纳入商保目录，实质确定条件性的目录保障范围；不因商业保险还需另作合同而删除本政策目录覆盖命题。'},
'01264':{'F':'当前实质行为为“论证确定…限定支付范围”；不能仅因仍处评审阶段将当前确定保障范围的要求排除。v1.4 F1允许条件/要求。'},
'01432':{'I':'表列“改良型生物制品”以及4/6年数据保护权利与期限直接讨论改良属性和专有数据权利。v1.4 I2/I3。'},
'01446':{},
'01562':{'Ec':'当前列明调整支付范围导致的未来两年基金支出预算增幅100%门槛，属于药品支付预算影响。'},
'01616':{'Ec':'明确基金实际支出超预算时可不降价，实际经济条件与价格后果齐备。'},
'01765':{'S':'明确系统全面安全评价与安全资料质量要求。','E':'“确能带来更好治疗获益”实质讨论临床获益。'},
'02072':{'Ec':'完整流程图含基金支出预算增幅、比值及支付标准变化；核验补充语境说明降幅与最终支付标准，经济内容明确。'},
'02144':{'F':'直接提出提高参保人员用药保障水平；药品保障联系明确，非一般医疗服务均等化。v1.3宏观保障边界。'},
'02830':{'S':'申请人更新安全报告并持续实施药物警戒和风险最小化措施，明确风险识别控制。'},
'02845':{'S':'申请人依据药物风险开展警戒、识别管理风险以保护受试者，明确药物安全义务。'},
'03157':{'E':'当前例句解释未观测协变量导致治疗分配概率差异；同段明确其敏感性分析用于检测疗效估计偏倚及疗效上下限，形成效果判断方法的直接用途。'},
'03229':{'S':'明确不良反应与风险大于收益的评估。','E':'药品风险收益判断含临床收益；负向结论不删除效果维度。','Ec':'明确将药物经济性列为当前综合评估因素。','F':'核验父谓词“直接调出《药品目录》”由当前风险收益条件控制，实际保障范围退出。'},
'03415':{'S':'“减少用药差错”属于用药风险预防。'},
'03704':{'Ec':'明确把进入目录药品的选择与医保基金安全底线联系，实际讨论药品支付资源；没有数值不等于没有经济内容。'},
'03712':{'Ec':'重新谈判的降幅与简易续约降幅比较，实际价格调整命题明确。'},
'04894':{'F':'医院、医保经办与定点零售药店连通，保证处方流转；给定双通道语境补足常规药物获取渠道，而非单纯机构内部采购职责。v1.4 F4。'},
}
# certainty is kept separate from whether the cell changed against a given history.
# confirmed_error = manual conflict; boundary = reasonable application ambiguity, no forced gold.
override={
'00090':{'I':('boundary',None,'当前子项仅称创新疫苗，但核验父谓词确为可申请优先审评；I0的名称排除与I1的面向创新对象优先资源解释仍有交界。没有新增属性证据，亦不能忽视实际优先资源；暂不作为确证修复。')},
'00180':{'F':('boundary',None,'“失去治疗机会”源于不耐受，未明示缺少可获得的替代药物或保障供给障碍。S/E明确；是否将临床无法耐受造成机会丧失纳入F治疗需求未满足，手册未直接裁断。暂不当作确证改善或错误。')},
'00663':{'F':('confirmed_error',1,'“暂时无法纳入基本目录”直接陈述当前药品基本医保覆盖排除状态；不要求另有商业保险给付安排才算F。模型将实际保障缺口降为对象分类，过度删除。v1.4 F1/F6。')},
'00771':{'Ec':('boundary',None,'相关数据由同段明确解析为谈判药品费用与基金支出；保证其获取质量可能是经济证据要求，也可能是纯沟通事务。v1.3排除单纯格式/保密，未明确裁断本类数据获取质量要求。当前Ec0不作确证修复，需独立裁断。')},
'00964':{'Ec':('confirmed_error',0,'当前只组织现场价格协商并签约，没有价格取值、支付责任或新增经济评价内容；邻句测算评估不复制。v1.3明确单纯谈判程序不自动Ec。与控制C03-009所排除的会务程序同类。')},
'01432':{
'S':('confirmed_error',1,'本行明示“符合本办法第七条第一款”；核验引用第一款要求提交用于证明安全性的全部试验数据，构成当前保护资格的实质安全证据要求。不是无关父背景。v1.3评价内容要求。'),
'E':('confirmed_error',1,'同一明确引用第一款要求提交证明有效性的全部试验数据；明示条件引用不能以“未独立提出新评价”删除。v1.3评价内容要求。')},
'01446':{'I':('boundary',None,'本句同时有鼓励/科学问题宗旨及罕见病申请条件。“源头性创新”可被读为创新属性限定，也可仅为计划目标；实际较强创新条件在后句。模型改记attribute，不能依据后句或项目名直接补属性，暂不算确证修复。')},
'01562':{'F':('confirmed_error',1,'核验父谓词明确满足当前条件可简易续约且有效两年，且对象为既有医保谈判药品协议。费用阈值直接控制保障延续；不是仅获得再申请/重新谈判机会。v1.4 F2。')},
'01616':{'E':('confirmed_error',0,'纳入诊疗方案仅界定不降价例外的适用对象；当前没有实质治疗推荐/疗效内容。既有方案身份不能传播E。v1.4共同边界。')},
'01768':{'S':('confirmed_error',0,'仅规定未阐明问题可沟通、未来完善指南；安全资料主题可用于解析问题，但未使当前沟通形式新增安全评价/证据要求。v1.3事务性提及边界。')},
'02072':{'F':('boundary',None,'完整图包括常规目录转类、简易续约、补充协议与重新谈判分支。模型主要引“非独家药品→纳入常规目录”，可能是既有保障管理转类而非新保障；其他分支又涉及调整支付范围。应对完整图的当前复合命题裁断，不能只凭管理路线整体F0，也不能只凭“纳入”整体F1。')},
'02086':{
'Ec':('confirmed_error',0,'当前引导句主体/对象/行为自足，实质规定续约及期限；后列经济条件另列并非理解期限所必需。模型把全部子项费用条件反向复制为当前Ec，违反单元边界。与必须补足评价对象的C05-016不同。v1.3冒号引导句/共同语境边界。'),
'F':('confirmed_error',1,'当前直接规定到期既有医保谈判药品协议可续约、有效两年，是保障连续期限，不要求再逐字复述患者药费继续支付。v1.4 F2。')},
'02223':{'I':('boundary',None,'本句明确《意见》支持试验机构参与创新药早期研发和开展国际多中心试验；区别于仅“为支持创新现发布文件”的宗旨。模型追加必须有人员/资源/技术指导/优先资格的窄门槛，可能过度删除实质组织便利；但文字未列具体配置措施。保留I0/I1边界，不直接据旧一致判真。')},
'02364':{'F':('confirmed_error',0,'药学部门承担机构统一采购及检查验收是内部采购职责，未确定药物配备供应范围、常规治疗获取渠道或患者保障关系。不能把“统一采购”本身泛化为患者access。v1.3一般行政管理/一般配送边界。')},
'03261':{'F':('confirmed_error',1,'当前“谈判药品协议有效期两年”在医保目录制定调整对象中直接限定药品保障协议时长，语境只补足对象；不是后续再谈判机会或管理转类前提。v1.4 F2。')},
'03415':{'I':('boundary',None,'目的句明确适老化研发设计指导的内容方向，但仍是“旨在提出”的总体目标，未列当前具体支持资源或技术内容。与单纯创新标题不同；当前I1研发指导支持和I0一般宗旨解释需冻结手册边界后裁断。')},
'03712':{'I':('confirmed_error',0,'当前仅列1类注册序号及更优惠再谈判降幅；给定材料没有该类别原创/改良/创新分类的实际含义，也没有将此价格安排实质连接创新研发。段落一般支持创新宗旨不能替代创新对象/研发支持证据。v1.4 I1/I4/I5。')},
'04368':{'E':('boundary',None,'诊断与处方相符是一般处方适宜性审查，未明示药物效果、获益或具体指南治疗推荐。模型把“是否适用于疾病”扩为E治疗推荐，存在回归风险；手册未专门裁断该一般审查内容，先列边界而非当确定错误。')},
}
# Negative cells needing specific non-mechanical context explanations.
negative={
'00090':{'E':'“明显临床价值”为一般父级资格措辞，未给具体效果；不复制E。','F':'“急需”未明确短缺或治疗不可获得。'},
'00637':{'Ec':'确认协议中支付标准字段为既有信息确认/签约事务，未新增经济内容要求。','F':'支付范围是需确认字段，未当前设定或改变覆盖范围。'},
'01135':{d:'抽象定义多维证据综合评判，后句另列六维内容，当前不控制该列举；五维不由相邻句反向传播。' for d in DIM},
'01264':{'Ec':'确定限定支付范围不同于价格、药费、支付标准或费用责任；规格/参照药品本身不补经济内容。'},
'01765':{'I':'当前主要帮助整理准备安全申报材料；创新药对象名称不自动把申报资料要求变成研发支持。'},
'02144':{'Ec':'宏观建立医保支付机制的目的没有具体药费、支付责任或药品支付资源内容；F仍保留用药保障目的。'},
'02830':{'E':'试验结果可靠性未明确用于药物效果判断。','I':'申请人更新风险计划/报告及警戒是义务，非给予创新研发实际资源。','F':'一般受试者权益/安全不等于治疗获取或可负担。'},
'02845':{'I':'当前施事为申请人，行为为承担药物警戒风险管理义务，受益为受试者安全；没有机构向创新研发对象提供支持的命题。'},
'03157':{'F':'接受治疗概率差异是观察研究方法示例，不是常规药物获取缺口。'},
'03471':{d:'本句仅述老年患者可能需常规减量/调量；未述损害、疗效、经济、创新改变或具体管理障碍。后句适龄设计措施不整体传播。' for d in DIM},
'03704':{'S':'基金安全是支付资源安全，非药物安全。','F':'雪中送炭/锦上添花为方向性比喻，未具体陈述获取缺口。'},
'03735':{'F':'已有两年协议只是转常规管理的前提；当前未新增保障关系或延续条件。v1.4 F1。'},
'03866':{'F':'假定企业希望增加未载明规格支付范围，仅要求书面申请；当前未确定纳入结果，后句新标准执行另存。v1.4 F1。'},
'03950':{'S':'审查未成年知情同意与认知心理法规条件属伦理保护；父安全保护词未具体连接药物损害。'},
'04164':{'I':'创新范围只补对象，当前申请人选择单/多专业申请和沟通议题，未当前规定审评人员技术辅导/资源配置。'},
'04894':{'Ec':'医保信息平台/经办机构在本句是处方流转载体，不复制后句药费基金监测内容。'},
}
rows=[]
for c in changes:
 k=c['id'].split('-')[-1]; a=c['candidate05_intact_actual_row']; dims={}
 for dim in DIM:
  status,judgment,note=override.get(k,{}).get(dim,('supported',a['labels'][dim],positive.get(k,{}).get(dim,negative.get(k,{}).get(dim,base0[dim]))))
  dims[dim]={'actual':a['labels'][dim],'review_status':status,'reviewer_manual_judgment_not_gold':judgment,'reason':note}
 flags=[]
 if k=='01432': flags.append('I=1正确；research_support除数据保护权利外没有另列独立研发支持证据，子类型需另审，不能由本轮直接改写。')
 rows.append({'id':c['id'],'full_input_and_actual_row_bound_to_source':True,'changed_dimensions_vs_each_history':c['changed_dimensions_vs_each_history'],'five_dimension_review':dims,'source_type_review_flags':flags,'review_read_scope':'完整单元、全部给定语境文本、当前五维理由和证据/子类型、所有发生变化的历史理由；未读取真人参考标签。'})
assert len(rows)==38 and all(set(r['five_dimension_review'])==set(DIM) for r in rows)
assert all(v['reason'] != base0[d] for r in rows for d,v in r['five_dimension_review'].items() if v['actual']==1 and v['review_status']=='supported')
controlnotes=[
'严重疾病和迫切需求未陈述药物损害/效果/获取缺口；全0。',
'无可获得药物且建立常规渠道；F access，其他0。',
'审批上市效率与一般需求，不补治疗缺口或创新研发对象；全0。',
'药物短缺储备与日常持续供应；F access。',
'已入组后随机转换组，不证明无其他治疗；全0。',
'明确无其他可获得治疗选择，并对应提供研究药；F access。',
'发布结果/通知落实没有具体目录覆盖内容；全0。',
'扩大具体适应证给付、保险承担药费；Ec+F access。',
'只安排价格协商会议通知，不引入经济判断；全0。',
'每盒二十元支付标准明确Ec，无患者负担或覆盖变化；F0。',
'频繁监测被明确作为药物基层使用管理难度；F clinical_management，无毒性证据不补S。',
'一般处方管理规范，没有具体治疗推荐或风险；全0。',
'创新对象中的申请提交形式，不是研发支持；全0。',
'专职顾问与持续技术辅导，是实际创新研发资源；I research_support。',
'只注册序号和申请资格，无类别含义；全0。',
'注册类别定义为原创化合物且要求说明原创属性；I attribute。',
'包装文字适老可读，未说误用风险、改变或获取障碍；全0。',
'明示改良释药设计与原产品频次变化；I attribute，无疗效或管理难度证据。',
'一般受体阻断机制未明示新颖性或药效；全0。',
'首次新颖机制与原创性信息要求；I attribute。',
'一般商业秘密保密，非药物专有数据权利；全0。',
'六年专有试验数据权利及排除他人依赖；I attribute，无S/E数据内容。',
'当前公示与纳入手续，不复制父创新临床优势资格；全0。',
'当前创新资格与相对标准治疗生存获益双锚点；E+I qualification_advantage。',
'不良反应监测与风险控制；S，不自动将监测记F难度。',
'平台数据安全与账户权限非药物安全；全0。',
'补充降低复发率临床证据，效果资料要求即E。',
'数据字段有效性非药物治疗有效性；全0。',
'药费过高造成无法继续治疗，降低自付；Ec+F access/affordability，两个F来源均有独立内容。',
'科研/设备经费非药品支付资源，也未明确创新研发对象；全0。',
'再次提交续约材料机会未承诺保障持续；全0。',
'实际治疗药物供应延续三年；F access，无费用责任。',
'费用预算条件由保险继续承担药费三年父谓词控制；Ec+F access。',
'同一费用条件只控制材料审核顺序；Ec，F0。',
'创新项目中申请人选择沟通形式/议题；无机构实际辅导资源；全0。',
'机构给创新研发专门专家团队与方案辅导；I research_support。',
'已有创新支持项目身份，只季末报告进度；全0。',
'当前确认原创属性并给予专门研发资源；I attribute/research_support，两来源均有独立内容。',
'创新适用背景中申请人的药物不良反应/风险义务；S，I0/F0。',
'监管机构实际配置专家指导风险控制；S+I research_support。',
'创新项目申请人季度报告进度纯事务；全0。',
'达到条件者取得专门研发设备优先使用权；I research_support，受规制申请人仍可作为实际支持接受者。',
'为支持创新发布资料指南，仅宗旨和发布；全0。',
'审评机构安排专业人员依据资料向创新研发提供研究设计技术建议；I research_support，无S/E用途不补。',
'已核验原创对象由父级补足，当前机构专门方案咨询；I research_support。',
'相同咨询针对普通药品；后节原创项目不传播；全0。',
'预算增幅条件被实际保障继续生效两年/继续支付药费父谓词控制；Ec+F access。',
'同预算条件仅安排材料办理顺序；Ec，F0。',
'已履行保障协议仅作当前管理转类前提；全0。',
'当前到期后保障协议继续生效两年且原给付条件适用；F access，未述具体药费责任不补Ec。',
'增加支付范围的希望/书面申请程序未确定实际纳入；全0。',
'新增适应证实质纳入保障且基金承担药费；Ec+F access，适应证名称不补E。',
'抽象评价定义不控制后句五维列举；全0。',
'当前引导句要求包括后列五维评价内容，后项为理解当前评价对象必需；五维1，F affordability/I attribute。',
'常规剂量调整需求没有风险、疗效或明确管理负担；全0。',
'每周采血与基层能力的管理负担评价；F clinical_management，未述毒性不补S。',
'新编号本身不支持I，但同句还明确否定产品组成及剂型变化；I1可受否定命题仍算讨论的总则支持。冻结期待I0的理由只处理前半句，未充分处理后半句。控制预设争议，不能直接算模型错。',
'从小容量注射液到无菌粉末是具体剂型变化；I attribute，不额外强求创新词或优效。',
'一般格式存档/保密，不是专有试验数据权利；全0。',
'六年专有数据权利及排除他人依赖申报；I attribute，无效果或风险内容不补S/E。',
'病情严重、急需、希望早用未明示获取缺口；全0。',
'明确无可获得治疗药物，指定机构提供且持续供应；F access。'
]
assert len(controlnotes)==62
ctrl=[]
for c,note in zip(controls,controlnotes):
 a=c['actual_row']; disputed=a['id']=='C05-NEW-019'
 ctrl.append({'id':a['id'],'actual_row':a,'frozen_expected_labels_unchanged':c['labels'],'mechanical_different_dimensions':c['different_dimensions'],'five_dimension_review':{dim:{'actual':a['labels'][dim],'review_status':'control_expectation_boundary' if disputed and dim=='I' else 'supported'} for dim in DIM},'reviewer_manual_assessment_not_gold':note,'evidence_and_subtypes_read':True,'current_control_judgment':'BOUNDARY_IN_FROZEN_EXPECTATION' if disputed else 'SUPPORTED_ON_GIVEN_MATERIAL'})
counts={}
for hist in changes[0]['historical_intact_rows']:
 tab=collections.Counter();dimtab=collections.Counter();celllist=[]
 for row in rows:
  for dim in row['changed_dimensions_vs_each_history'][hist]:
   status=row['five_dimension_review'][dim]['review_status'];tab[status]+=1;dimtab[dim]+=1;celllist.append({'id':row['id'],'dimension':dim,'review_status':status})
 counts[hist]={'changed_units':sum(bool(r['changed_dimensions_vs_each_history'][hist]) for r in rows),'changed_dimension_counts':dict(dimtab),'total_changed_cells':len(celllist),'review_status_counts':dict(tab),'cells':celllist}
errors=[{'id':r['id'],'dimension':d,'actual':v['actual'],'reviewer_judgment_not_gold':v['reviewer_manual_judgment_not_gold'],'reason':v['reason']} for r in rows for d,v in r['five_dimension_review'].items() if v['review_status']=='confirmed_error']
boundaries=[{'id':r['id'],'dimension':d,'actual':v['actual'],'reason':v['reason']} for r in rows for d,v in r['five_dimension_review'].items() if v['review_status']=='boundary']
# Bound all evidence to real files; no new model/CLI subprocess calls anywhere in this script.
paths=[P/'candidate05_technical_QA.json',P/'candidate05_all_changes_PRIVATE.json',P/'candidate05_all62_controls_PRIVATE.json',P/'candidate05_all240_comparison_PRIVATE.json',P/'candidate05_development_freeze_v2.json',P/'candidate05_package_manifest_v2.json',P/'candidate05_prompt_frozen.txt',P/'exposed240_inputs_frozen.jsonl',P/'synthetic62_inputs_frozen.jsonl',P/'synthetic62_expected_PRIVATE_frozen.json',P/'runtime-v2/exposed240-candidate05-first-run/all_predictions.jsonl',P/'runtime-v2/synthetic62-candidate05-first-run/all_predictions.jsonl',D.parent/'validation-state-audit/future_human_v5_development_exclusion_metadata.json',D.parent.parent/'coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md',D.parent.parent/'coding-revision-20261007-r3/llm-v32/共用实质操作说明-v1.4-运行摘录.txt']
bindings=[{'path':str(p),'sha256':sha(p)} for p in paths]
report={
'status':'TECHNICAL_PASS_SEMANTIC_REGRESSIONS_BLOCK_FULL_CORPUS_ADOPTION',
'created_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
'reviewer_identity':'AI independent implementation reviewer /root/llm_repair05; candidate05 prompt/controls preparation author, not an independent semantic validation coder',
'scope':{'changed_units_against_any_of_three_intact_histories':38,'all_five_dimensions_of_each_changed_unit_read':True,'controls_read_in_all_five_dimensions':62,'unchanged_202_units_individual_semantic_read_claimed':False,'model_calls_by_this_audit':0,'actual_prior_bounded_logical_requests':13,'actual_prior_bounded_attempts':13,'full_corpus_model_call':False,'new_human_labels_read':False,'new_reserved_family_members_individually_read':False,'reviewed_original_unit_ids_reserved_intersection':[],'production_labels_edited':False,'frozen_expected_labels_edited':False},
'limitation':'This is a development semantic audit by an AI who prepared candidate05, not independent validation or human adjudication. All reference labels/κ were unavailable and not used. Root may separately compute frozen old180/60 exact points; no choice by highest κ is authorized here.',
'bindings':bindings,
'real_technical_audit':{'command':'bundlePython '+str(P/'audit_candidate05_v2.py'),'result':'PASS','raw_final_event_binding':'Each of 13 actual attempts has exactly one completed agent_message; its parsed JSON equals selected raw output with type-preserving equality. First valid attempt selected; zero tools; all intact row/instruction/input/runtime hashes checked by existing audit.','details':str(P/'candidate05_technical_QA.json')},
'comparison_change_counts_and_manual_review':counts,
'confirmed_current_errors_in_changed_review':{'units':len({r['id'] for r in errors}),'dimension_cells':len(errors),'items':errors},
'manual_boundary_cells_in_changed_review':boundaries,
'control_review':{'mechanical_units_matching_frozen_expectations':61,'mechanical_cells_matching_frozen_expectations':309,'total_cells':310,'reviewer_confirmed_errors':0,'frozen_expectation_boundary_units':['C05-NEW-019'],'expectation_not_changed':True,'all_actual_reasons_evidence_subtypes_read':True,'interpretation':'Do not silently count disputed control as passed or as proven model error. Preserve 61/62 and 309/310 as only mechanical agreement with the pre-frozen expected file.'},
'decision':'Keep complete candidate05 actual outputs as development evidence. Do not splice dimensions/units, do not adopt as replacement or launch full model call from this audit. Confirmed regression plus persistent F failures preclude a safe general repair claim even though the target pharmacovigilance I false positives were corrected.',
'development_implication':['02830/02845 support the narrow actor/action distinction: applicant safety obligations are not a regulator-to-innovation-development support measure.','Synthetic parent-predicate controls with explicit protection/payment wording succeeded, but actual authenticated negotiated-medicine renewal predicates still failed (01562/02086/03261). This is a generalization gap, not a technical retry justification.','Avoid broadening the repair into requiring an explicit repeated patient/payment sentence for every renewal; object resolution plus actual continuation term can establish F.','S/E must survive explicit incorporated evidence conditions (01432); current-unit boundary cannot be used to erase an expressly cited substantive condition.','Before any new prompt variant, freeze ordinary-language boundary decisions on named issues; a new development run would require separate bounded authorization. Do not use model voting as truth or claim this review is independent validation.'],
'changed_unit_reviews':rows,
'all_62_control_reviews':ctrl,
'prior_02845_cross_request_comparison':'Prior old03 vs full03 had identical unit input/certificates/full prompt/CLI0.160.1/model effort but different peers/position and separate executions. Complete request differed; cannot call an identical-request repeat or attribute reversal to batch alone. Candidate05 also changes prompt and occasion; do not attribute target correction to a uniquely isolated factor.'
}
(D/'candidate05_semantic_review_PRIVATE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
summary='''候选05实际执行后技术与语义审查（开发材料，非独立验证）

结论：真实技术门禁通过，但存在确证回归和持续漏判，不支持据本轮直接替换生产结果或启动全量模型。

已实际运行既有 audit_candidate05_v2.py；13 logical / 13 attempts均为首次技术有效输出，唯一完成agent_message与raw JSON一致；未新增任何模型调用。240完整输出SHA256 947e5be969eaff712cfea95a97ac7a2b1a1608f30062442bf2d9eb3082c312c0；62控制输出SHA256 5ab52a1636fd8d66c0d6dfe57f4728733ac9d85663d2dd21b5f5e6f3b711bee4。

逐条审读范围：相对旧03开发、旧04开发、现行全量03任一历史发生变化的全部38单元，其完整输入/给定语境/五维实际理由证据及子类型；全部62控制同样逐条五维核对。相对现行全量03实际25单元/27维变化；相对旧03为19单元/20维，相对旧04为18单元/24维。没有声称逐条语义审读另外202个不变单元。

按本审查员对v1.3/v1.4的独立解释，现行全量03→05的27维变化中，12维有手册依据、9维为确证回归、6维为手册边界争议。这是开发判读分类，不是真人金标准或准确率。

确证修复包括02830/02845把申请人药物警戒义务恢复为S1I0，04164把沟通申请形式I扩判恢复I0；短缺/境内未上市获取状态00099/00110/00118及直接控制新支付范围的00891恢复F1；03157与疗效估计明确关联的研究方法恢复E1。其他改善/每维证据见JSON。

确证回归：00663删除当前无法纳入基本目录的保障缺口F；00964把现场价格协商程序计Ec；01432删除明示援引安全性和有效性试验数据条件的S/E；01616把既有诊疗方案身份传播E；01768把安全资料主题沟通方式传播S；02086将子项经济条件反向复制Ec且删除当前两年续约F；03712仅注册序号、一般创新宗旨及价格安排未给实际创新分类/研发支持证据却计I。合计7单元9维。

持续错误还包括01562费用阈值直接控制两年续约但F0，03261医保谈判药品协议两年有效期F0，02364机构内部统一采购职责F1。这三项相对现行全量标签不变，不能被变化净额掩盖。全部变化审读中共10单元12维当前确证问题。

边界单列：00090创新疫苗与优先资源、00180不耐受造成失去治疗机会、00771经济数据获取质量、01446源头创新目的与属性、02072完整续约图的复合保障含义、02223支持试验机构参与创新研发、03415目的句中的适老化研发指导、04368诊断与处方相符审查。未强迫裁为真值，不按历史多数推定正确。

62控制机械预设一致61/62（309/310维）。唯一差异C05-NEW-019的模型I1有总则“否定仍可讨论维度”依据：原句不只新编号，还明确组成和剂型未变；冻结预设I0理由只处理新编号。将其登记为控制预设争议，原预设不改，既不事后算全通过，也不直接当模型错。其余61控制的理由、证据与子类型本次均审读并在给定材料上可支持。控制特别明确“保障/继续支付”措辞，不能代表已泛化至真实续约语境。

未触碰生产标签、DOCX、新真人标签或保留267家族新成员原文；无新模型/全量调用。本文审查员参与候选05提示和控制准备，所以这是实施后的开发语义审查，不能称独立验证。规则v37.2独立预检允许shadow的结论另见independent-rule-v37.2-review/independent_preflight_v37_2.json，不因此改变候选05结论。
'''
(D/'候选05执行后语义审查结论.txt').write_text(summary)
# File creation is confined to this independent review directory.
manifest={'status':'SEMANTIC_REVIEW_FROZEN','bindings':[{'path':str(p),'sha256':sha(p)} for p in [D/'candidate05_semantic_review_PRIVATE.json',D/'候选05执行后语义审查结论.txt',D/'read_review_material.py',D/'write_semantic_review.py']],'source_bindings':bindings,'no_new_model_calls':True}
(D/'semantic_review_freeze.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':report['status'],'comparison_counts':{k:{kk:vv for kk,vv in v.items() if kk!='cells'} for k,v in counts.items()},'confirmed_error_units':len({r['id'] for r in errors}),'confirmed_error_cells':len(errors),'boundary_cells_total':len(boundaries),'report_sha256':sha(D/'candidate05_semantic_review_PRIVATE.json'),'freeze_sha256':sha(D/'semantic_review_freeze.json')},ensure_ascii=False,indent=2))
