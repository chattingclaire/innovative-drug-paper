"""Record the bounded semantic review. This writes audits, never model labels."""
import json,pathlib,hashlib,collections
H=pathlib.Path(__file__).resolve().parent
D=['S','E','Ec','I','F']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
p=read(H/'candidate03_candidate04_complete_changes_PRIVATE.json');qa=read(H/'candidate04_actual_QA_and_changes_PRIVATE.json')
notes={}
def note(ids,dim,kind,text):
 for rid in ids.split():notes[(f'RECODE25-{rid}',dim)]=(kind,text)
note('00066 00090 00292 01446 01765','F','confirmed_execution_correction','不再从急需、需求迫切、及早上市或一般试验转换机会补出获取缺口；明确的其他维度仍保留。')
note('00967','F','confirmed_execution_correction','结果公布及组织执行本身没有给付或供应条件，排除正确。')
note('01765','I','confirmed_execution_correction','一般资料准备便利及指南宗旨不构成实体创新支持。')
note('04164','I','confirmed_execution_correction','本轮终于区分申请人选择沟通形式/议题与机构实际提供指导资源。')
for d in ['E','I','F']:note('04588',d,'confirmed_execution_correction','公示及程序纳入动作不能复制此前资格条款的各维内容。')
note('03865','F','confirmed_execution_correction','明确形成新支付范围及补充协议，不再额外要求已经对个别患者给付。')
note('00891','F','substantive_condition_correction','按实际控制父条款判断费用门槛与新保障范围的关系，保留Ec与F的独立依据。')
note('01562 02086','F','candidate03_regression_repaired','识别原协议保障持续与两年续约期限；完整原父谓词及费用条件对照另存，不只是匹配参考。')
note('03261','F','agreement_duration_correction','给定内容把该协议确认为医保药物保障协议，其有效期间可构成保障连续性。')
note('00964 03876','Ec','procedural_content_correction','价格协商会务/流程节点不是价格水平、费用责任或经济评价实质内容。')
note('01396','S','evidence_role_correction','安全性数据是专有权利客体分类，当前没有新增安全评价或提交内容要求。')
note('01396','E','evidence_role_correction','有效性数据是专有权利客体分类，当前没有新增疗效评价或提交内容要求。')
note('01768','S','procedural_content_correction','沟通处理问题及完善指南未新增安全内容，不从背景的资料主题赋S。')
note('02861','S','risk_management_correction','给定范围明确药物临床风险，当前执行该风险管理计划是实质风险控制要求。')
note('03101','S','context_anchor_correction','研究总体同时提及安全性，不证明本条主要终点和效果稳健性方法也承担安全性判断用途。')
note('03157','E','context_anchor_correction','给定连续论述明确把协变量例子用于疗效估计偏倚分析，使用的是证据用途而非传播研究主题。')
note('03415','E','general_goal_correction','整体健康宗旨不等于已经讨论药物防治效果或治疗获益。')
note('03927 03941','S','safety_anchor_correction','药物试验中明确参与者安全保护和风险预防，无须另列已经发生的不良事件。')
note('03704','Ec','fund_impact_correction','药品目录支付以基金安全为约束，实际关注药物对基金资源的影响，不要求具体金额。')
note('00180','F','preserved_reference_boundary','临床不能耐受导致失去治疗机会，是否属于宽F的未满足治疗需要仍有边界；按root要求保留F=0首次结果，不强迫改回参考。')
note('01264','F','preserved_reference_boundary','本轮回到0，但与01979近似的论证确定支付范围命题仍给出不同理由/参考；不能把接近参考称为已解决边界。')
note('01446','I','preserved_reference_boundary','本轮回到1且理由改为属性，原命题的创新对象、目的和实体支持关系仍有解释边界；标签相符不证明新的子类型理由正确。')
note('01448','I','preserved_reference_boundary','研发阶段是否实质限定得到具体支持与仅列申请对象之间仍有边界；本轮0不作为手册新增的阶段词排除规则。')
note('00099','F','preserved_reference_boundary','本条直接写明短缺状态，赋F有可解释依据；同时保留其主要行为为程序申请限制的参考分歧。')
for d in ['S','E','Ec','I','F']:note('01135',d,'confirmed_new_execution_error','当前只是综合评价的抽象定义。具体六维仅在后句，模型将后句标签复制为当前句评价要求，违反当前命题与context_usage；五维全1是明确新增误用。')
note('01616','E','reintroduced_execution_error','诊疗方案中的既有身份仅是降价例外条件，未陈述当前药物治疗推荐；candidate03曾纠正，本轮重新继承为E。')
note('02364','F','new_execution_error','药学部门统一采购及检查验收是内部行政职责，不足以推导患者获取渠道、保障范围或供应改善；当前理由补入了取得并供应患者的关系。')
note('03471','F','new_execution_error','普通剂量减半/调整及适老化适宜性不自动等于具体临床管理难度，模型自行补了复杂性。')
note('03735','F','new_execution_error','原有两年协议作为何时转常规管理的前提，当前规定管理转类；不能把既有保障期限本身重新传播为当前保障命题。')
note('03866','F','new_execution_error','当前规定未列规格需要纳入时提交书面申请，没有完成新范围确定；后句的执行结果不能倒灌成本句已经规定的实际给付条件。')
note('02072','F','renewal_route_overextension_concern','本图混列常规转类、续约、重新谈判和补充协议路线；候选04将整体当实质保障持续，未区分哪些节点仅办理机会。A/C/T已有分歧，但本轮宽泛继承构成新误用疑虑，不能因含续约二字一律判F。')
note('04894','F','preserved_reference_boundary_with_new_inference','原句部署处方流转信息设施，模型补成患者通过双通道取得药品；是否已构成实质获取渠道存在参考边界，应保留原理由而非宣布获得确认。')
note('03229','E','new_false_negative_concern','药物风险大于收益的临床取舍可能已有治疗获益内容；将收益全部解释为综合概称有过严排除疑虑，且从原三方一致正类转为0，须显式保留退步。')
note('03415','I','reintroduced_broad_support_inference','本轮又把一般适老化指南宗旨解释为实质创新研发指导。与具体支持资源/指导内容的边界仍未稳定，不能把标题创新或泛称指导自动当支持；保留分歧。')
note('03712','I','unresolved_innovation_basis_changed','本轮不再直接以注册序号判属性，而借背景支持创新机制判研发支持；当前价格政策是否有明确药物研发创新对象/支持联系仍未被充分说明，初始误用的标签纠正没有保住。不能将新理由等同已解决。')
assert set(notes)=={(r['id'],r['dimension']) for r in p['all_changes']},set((r['id'],r['dimension']) for r in p['all_changes'])-set(notes)
review=[]
for r in p['all_changes']:
 kind,n=notes[(r['id'],r['dimension'])]
 review.append({'id':r['id'],'dimension':r['dimension'],'versions':r['versions'],'references':r['references'],'semantic_category':kind,'semantic_assessment':n,'original_candidate04_reason':r['reasons']['candidate04'],'all_original_reasons':r['reasons'],'source_ledger':'candidate03_candidate04_complete_changes_PRIVATE.json','labels_not_changed_by_review':True})
verdict={'status':'bounded_development_complete_mixed_semantic_outcome_not_unqualified_semantic_pass','technical_QA':'PASS','candidate04_controls':{'rows':38,'dimensions':190,'disagreements':0},'actual_model_calls_total':24,'actual_candidate03_calls':12,'actual_candidate04_calls':12,'all_calls_first_attempt_valid':True,'tool_events':0,'all_240_exposed_development':True,'independent_validation':False,'baseline_v14_preserved':True,'no_candidate05_or_full_corpus_calls_started':True,'root_confirmation_required_before_full_corpus':True,'initial12_misuse_label_corrections_candidate03':11,'initial12_misuse_label_corrections_candidate04':11,'important_note':'The corrected set differs: candidate04 fixes 04164 I but restores 03712 I with a different rationale. Counts are not a semantic adoption threshold.','explicit_new_01135_error_dimensions':D,'reviewed_changes_n':len(review),'all_change_semantic_reviews':review,'aggregate_reference_direction_only':p['reference_direction_counts_not_semantic_truth'],'recommendation':'Do not describe candidate04 as uniformly validated or replace v14. Root should decide adoption/full rerun from this complete evidence and forthcoming independent validation. This bounded run is finished; no further tuning or model calls.','source_and_reference_preservation_QA_sha256':sha(H/'original_reference_source_baseline_preservation_QA.json'),'technical_QA_sha256':sha(H/'candidate04_actual_QA_and_changes_PRIVATE.json'),'comparison_ledger_sha256':sha(H/'candidate03_candidate04_complete_changes_PRIVATE.json')}
dump(H/'candidate04_semantic_QA_PRIVATE.json',verdict)

md=['# candidate03 / candidate04 有界开发交付','',
'两轮开发已真实完成，共 24 次 gpt-5.6-sol、medium 调用，全部首次通过执行、结构、逐字引文、ID 顺序及零工具事件校验。候选03完成 240 条政策单元与30条合成控制；候选04完成同240条与38条合成控制。每条五维均来自同次完整判断，没有拼接旧维度。', '',
'**候选04有明确改善，也有明确新增错误，不能记为无条件语义通过。** 两条续约漏判和沟通申请误判已纠正；01135将后句六维继承为当前定义句五维全1，属于新增错误。全部原始请求、返回、理由和变化均保留。没有启动候选05或197批全量，后续采用和全量决定交由root。', '',
'当前240条已经用于开发，30/38条合成控制也只是开发对照，均不能改称独立验证。v14基线、v1.3/v1.4、A/C/T和原始LLM输入保持不变，保存校验通过。', '',
'## 调用与冻结绑定','',
'| 版本 | 实际调用 | 控制结果 | 240条输出 SHA256 |','|---|---:|---|---|',
'| candidate03 | 12 | 30条/150维符合预先期望 | `09d8cc5e5d306acad6e4792a5c75118aa604d5e559a05f46bc41d91d74058e20` |',
'| candidate04 | 12 | 38条/190维符合预先期望 | `4d9dc3708482679ac19d2f6fdeb3f245ce7fa43e203aa7a58d110c09fde44479` |','',
'candidate03 prompt SHA：`8576d9a1be10b0dd7b69b4c12367f4c357f55abf4ca30d979d5b333493089ba4`。candidate04 prompt SHA：`969123c95b6636d0ab33d515ed3c34017ef5d4a6defa2441f0091656e3c3806d`。', '',
'所有运行固定选择首次技术有效结果，未因标签或指标重试。本轮没有技术失败；并发主运行3、控制1。PTY 72419/33100（候选03）与54972/23563（候选04）均正常结束，不存在需要重启或等待的本任务调用。CLI事件未暴露服务端内部模型修订号；请求模型和实际CLI调用参数已留痕。', '',
'## 改善、退步及语义结论','',
'初始12个明确I/F误用，候选03纠正11个标签，候选04也纠正11个，但集合不同：04164 I在第二轮纠正，03712 I重新变为1，理由改成支持创新机制，不能称已解决。01562与02086的候选03新漏判均在第二轮修复，原控制父谓词、完整语境、三版本原始五维行及限定义对照单独保存。', '',
'与AI候选参考的方向变化仅作描述：候选03相对v14转近26维、转离5维；候选04相对v14转近28维、转离13维；候选04相对候选03转近9维、转离15维。这不是把参考当真值的语义结论，也没有以κ或0.8作为采用门槛。概率180与挑战60的四格分别保存在实际QA文件中，未合并成独立准确性报告。', '',
'新增明确错误：01135五维后句继承；03471 F将普通剂量调整推为管理难度；02364 F将内部采购职责推为患者获取安排；03735 F把管理转类前提当新保障命题；03866 F把书面申请当实际范围确定。01616 E重新出现诊疗方案身份继承。02072 F的路线图泛化、03229 E过严排除药物收益以及03415/03712 I支持解释不稳定，另列疑虑和边界。', '',
'00180 F、01264 F、01446 I按原约定保留语义边界，不强迫回到候选参考。01264与01979仍体现近似“论证确定拟谈判药品支付范围”的不一致解释，标签碰巧接近参考不能证明该边界已经解决。', '',
'## 全部变化清单','',
'以下包括三版本间出现过的全部48个变化维度；0/1顺序为v14→候选03→候选04。每项原始五维行、各版理由、证据、完整语境和A/C/候选参考均在JSON台账中。', '',
'| ID | 维度 | v14→03→04 | A/C/候选 | 语义审查 |','|---|---|---|---|---|']
for r in review:
 vs='→'.join(str(r['versions'][v]) for v in ['v14','candidate03','candidate04']);rs='/'.join(str(r['references'][v]) for v in ['A','C','candidate'])
 md.append(f"| {r['id']} | {r['dimension']} | {vs} | {rs} | {r['semantic_assessment']} |")
md+=['','## 可审计文件','',
'- `candidate04_actual_QA_and_changes_PRIVATE.json`：逐次技术核验、初始误用、全部新变化及分组件四格。',
'- `candidate04_semantic_QA_PRIVATE.json`：48个变化维度逐项语义结论与全部原始理由。',
'- `candidate03_candidate04_complete_changes_PRIVATE.json`：完整文本、语境、证据、三版原始理由及所有剩余参考分歧。',
'- `continuity_parent_predicate_contrasts_PRIVATE.json`：01562/02086原父谓词、三版完整结果和预定正反对照。',
'- `development_handoff_bindings.json`：四个真实run、输出、计划、执行摘要及逐条actual prompt/request/attempt provenance。',
'- `original_reference_source_baseline_preservation_QA.json`、`candidate03_preservation_hashes.json`：原参考、v14输入/输出与候选03历史文件保存核验。',
'','本次有界开发已停止。下一步应由root依据完整改善/退步证据决定是否采用候选及启动197个新批次；不存在以零错误或某一κ阈值强迫通过的结论。','']
report=H/'候选03-04开发结果与完整语义交付.md';report.write_text('\n'.join(md))
b=read(H/'development_handoff_bindings.json');b['semantic_QA']={'path':str(H/'candidate04_semantic_QA_PRIVATE.json'),'sha256':sha(H/'candidate04_semantic_QA_PRIVATE.json')};b['readable_report']={'path':str(report),'sha256':sha(report)};dump(H/'development_handoff_bindings.json',b)
print(json.dumps({'semantic_QA_sha256':sha(H/'candidate04_semantic_QA_PRIVATE.json'),'report_sha256':sha(report),'handoff_sha256':sha(H/'development_handoff_bindings.json'),'reviewed_changes':len(review)},ensure_ascii=False))
