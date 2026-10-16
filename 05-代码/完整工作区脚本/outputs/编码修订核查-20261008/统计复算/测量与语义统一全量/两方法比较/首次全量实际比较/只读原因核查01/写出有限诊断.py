from pathlib import Path
import json,hashlib,datetime
B=Path(__file__).resolve().parent
summary=json.loads((B/'全体计数与代表选择.json').read_text());materials=json.loads((B/'固定12条来源与双方证据.json').read_text())
manual=Path(summary['manual_path']).read_text()
clauses={
 'gate':'仅有程序名称、对象身份、文件背景、沟通形式、资料流转或格式，不据此赋维度。',
 'I1':'当前实质讨论或要求评价原创/新颖技术、机制/靶点新颖性、实际创新注册分类，以及有明确创新联系的临床优势、国产原研/自主研发价值。',
 'I3':'当前实质设置创新/改良研发的资源、专门技术服务、研究方案反馈、研发便利或支持机会。',
 'I3_binding':'创新/改良研发须是该安排的对象选择条件、支持目标或实际适用依据；须保存对象、当前支持安排及二者关系。',
 'I_object_exclusion':'仅新获批/上市/申报、创新药作为管理或支付对象、一般管理创新；',
 'context':'父句援引法规、指南面向创新药、全文以患者保障为宗旨，都不能使每个子项继承其全部维度。',
 'F_relation':'患者按治疗需要获得或持续接受所需药品治疗的合理机会与负担，以及可避免、不合理的获取差异或保障缺口的关注。',
 'F_specific':'例如，针对当前明确的临床急需短缺药物安排优先审评，须同时有已表达的保障缺口与针对性优先安排；',
 'F_exclusion':'只有人群名称、普通供药/渠道/物流信息、普通保障名单、申报资格、一般提前上市或提速；',
 'F_trial':'一般试验参与、随机分组、疾病进展后的治疗调整或交叉治疗。上述内容本身均不是F充分条件。',
 'F_natural_need':'“有治疗需要”不能作为所有药品政策的天然背景。',
 'F_column':'医保“公平性”、卫健“可及性”、药监加快程序名称均不能替代上述联系。',
 'withdrawal':'对具体支持安排的设立、适用、限制或撤回，都可能表达该制度议题；须说明当前是哪一种。',
 'programme_state':'仅“已纳入／不符合某程序条件”这种状态，不能据名称猜出全部实质标准；当前具体讨论的标准仍据实际内容判断。'
}
assert all(v in manual for v in clauses.values())
judgments={
 ('I','RECODE25-01112'):{'diagnostic_category':'可定位规则漏判','confidence':'较明确','manual_clauses':['gate','I1'],'mechanism':'实际输出先用 V27_IF_local_reassessment 撤回旧 I01 的“创新性”词证据；最终没有建立“从创新性维度开展药品评价”的当前要求关系。这里并非孤立栏目名，当前确实提出开展评价的管理要求。','llm_interpretation_assessment':'LLM 理由对应当前实际创新评价要求，与 I1 相合。','decision_limit':'仅对此当前命题判断，不据此认定所有含维度列举的句子均应赋 I。'},
 ('I','RECODE25-02502'):{'diagnostic_category':'定义边界需裁定','confidence':'保留','manual_clauses':['gate','I3','I3_binding'],'mechanism':'规则未生成 I 证据；LLM 把“为进一步完善…支持举措…现提出以下措施”的宗旨和清单引导，视作当前实质支持安排。当前共同包只有这个段落，未含完整后续措施；不能用全文实际存在支持措施代替当前关系。','llm_interpretation_assessment':'“提出措施”是否自身已构成独立支持总领，还是仍须具体资源、便利或机会，是实质总领边界，不能仅凭支持词决定。','decision_limit':'不以整份创新药政策目标补当前具体措施，也不自动把未知或未展开清单判成缺材。'},
 ('I','RECODE25-00004'):{'diagnostic_category':'LLM 泛化候选','confidence':'较明确但保留程序设立边界','manual_clauses':['gate','I3','context'],'mechanism':'规则实际 V32_I_promulgation_purpose_not_substantive_support 删除宗旨范围内旧支持推断。LLM 把“为鼓励研究创制…制定本程序”直接解释为支持设立；虽同名程序适用范围包含创新/改良对象，当前没有具体资源、技术反馈或研发机会内容。','llm_interpretation_assessment':'由程序宗旨和制定行为推定实际研发支持，超出当前具体安排。若研究者将支持程序的制定本身作为实质总领，需先明示并统一适用该边界。','decision_limit':'不能据此否定程序内实际提前介入、反馈或退出支持的独立条款。'},
 ('I','RECODE25-01427'):{'diagnostic_category':'定义边界需裁定','confidence':'保留','manual_clauses':['I1','I_object_exclusion'],'mechanism':'规则 COMMON03_I_authenticated_actual_registration_class 凭已认证表头“注册分类和数据保护期”与“2类／改良型疫苗”列关系赋 I；LLM 认为这是保护期限表中的管理对象，未表达改良条件或研发支持。','llm_interpretation_assessment':'争议是这类映射表在当前是否实质呈现实际创新注册分类，还是只以类别作数据保护对象；两种解释都有当前表结构依据。','decision_limit':'4年保护期不能单独变成创新性；也不能遗漏已提供的真实“注册分类”表头。旧 SHA 出现在规则依据沿革字段，不自动证明采用旧口径。'},
 ('I','RECODE25-04149'):{'diagnostic_category':'定义边界需裁定，含规则漏判候选','confidence':'保留','manual_clauses':['gate','I3','I3_binding'],'mechanism':'旧“鼓励研究和创制新药”证据被 V27_IF_local_reassessment 撤回，最终无 I。LLM 将当前“早期介入、研审联动、滚动提交”经验与“以制度形式转化”及明确创新对象联系为支持设立。它比单纯制定宗旨更具体，但工具究竟在本句实际制度化，还是仅作为制定规范的背景，须判定。','llm_interpretation_assessment':'不能把所有宗旨一律当支持，也不能把含实质制度化工具的混合句全按宗旨排除。','decision_limit':'适用范围可识别对象，后文具体时限不能在没有当前承接时替本句建立行动。'},
 ('I','RECODE25-02205'):{'diagnostic_category':'LLM 过判候选','confidence':'较明确','manual_clauses':['gate','I1','I3'],'mechanism':'规则无 I 证据。LLM 把行业“创新能力持续加强、创新成果涌现”的背景陈述解释为药物创新成果及价值；当前并未呈现具体药物技术新颖性、创新资格或实际研发支持。','llm_interpretation_assessment':'从行业发展背景拓展到本研究药物创新评价／支持范围。后续同段支持研发的另一句不能反向赋当前自足背景句。','decision_limit':'只针对当前背景句，不否定同一解读文件后续真实研发支持条款。'},
 ('F','RECODE25-04903'):{'diagnostic_category':'定义边界需裁定，含 LLM 泛化风险','confidence':'保留','manual_clauses':['F_relation','F_exclusion','F_natural_need'],'mechanism':'规则无 F 证据。LLM 将扩大基层慢性病、常见病药种并满足用药需求，视为按需保障。当前确有特定服务场景和扩种目标，但未直接说明原有保障缺口、获取差异或支付能力障碍；同文后续缺药登记不得自动继承。','llm_interpretation_assessment':'须裁定“扩大基层药种以满足需要”是否已充分表达可指认缺口，不能因为基层人群或满足需求字样就必然 F。','decision_limit':'全文其他明确短缺、下沉限制、延伸处方条款可能有 F；这里没有重判它们。'},
 ('F','RECODE25-01090'):{'diagnostic_category':'可定位规则过宽','confidence':'较明确','manual_clauses':['F_relation','F_exclusion','F_natural_need'],'mechanism':'规则 COMMON11_F_basic_clinical_drug_supply_guarantee 由“保障临床基本用药的供应”直接赋 F；其依据把“临床基本/必需”与供应保障相连就视作公平。当前实际全文是一般供应与合理使用目标，没有具体缺口、按需补偿、机会限制或患者负担联系。','llm_interpretation_assessment':'LLM 将一般供应保障与可指认公平联系分开，更符合当前 F 门槛。','decision_limit':'没有否定一切基本药物保障的 F；其他句若明确所缺药品和按需资源安排可另判。'},
 ('F','RECODE25-03710'):{'diagnostic_category':'定义边界需裁定','confidence':'保留','manual_clauses':['gate','F_relation','F_column'],'mechanism':'V27_IF_local_reassessment 撤回“公平性等多个维度综合研判”的旧证据，最终无 F。LLM 把“从公平性综合研判药品价值”视为实际公平评价要求；这确实比栏目标题多了评价行动，但当前及所给同段没有展开需要、负担或获取差异。','llm_interpretation_assessment':'须明示“明确要求从公平性评价药物”是否已属于实质议题在场，还是必须在同一必要材料中出现具体公平联系。不能把此争议混成普通价格支付与 F 自动联动。','decision_limit':'不得自行借读其他申报指南的公平栏目内容填入这条材料；此边界也应与 I 的明确维度评价句同尺度解释。'},
 ('F','RECODE25-00005'):{'diagnostic_category':'定义边界需裁定，含 LLM 程序门槛泛化风险','confidence':'保留','manual_clauses':['F_relation','F_specific','F_exclusion','programme_state'],'mechanism':'V27_IF_local_reassessment 撤回“尚无有效防治手段”的旧 F 证据，最终无 F。LLM 将无有效治疗选项与申请突破性程序，解释为按治疗需要配置审评支持。当前确有资格机会，尚无有效选项是 E；但从申请程序门槛到患者获取／针对性审评资源补偿的公平关系仍需说明。','llm_interpretation_assessment':'不是因为没有现有有效选项就自动 F，也不能仅程序名称继承全部优先支持内容；需与明确临床急需短缺→优先审评条款区别。','decision_limit':'若认定该当前资格机会本身已足以补偿治疗保障缺口，须由研究者统一说明；OR 中另一“临床优势”分支不能一并解释为无选项缺口。'},
 ('F','RECODE25-02512'):{'diagnostic_category':'LLM 过判候选','confidence':'较明确','manual_clauses':['F_relation','F_exclusion','F_natural_need'],'mechanism':'规则无 F 证据。LLM 以群众基本医疗需求作为目录调整依据，就解释为所需药物按需保障；当前是普通目录定期调整的依据，基金承受能力并非患者能力，未表达具体缺口或针对性补偿。','llm_interpretation_assessment':'把所有药品政策固有治疗需要扩成公平关系。所给父段另有公共卫生特殊必需药临时支付的独立句，不能替当前泛化。','decision_limit':'不否定另句明确缺口及临时支付安排；没有重判该另句。'},
 ('F','RECODE25-00225'):{'diagnostic_category':'定义边界需裁定，含 LLM 治疗范围泛化风险','confidence':'保留','manual_clauses':['F_relation','F_trial','F_natural_need'],'mechanism':'规则无 F 证据；LLM 把兼顾未富集人群治疗需要、研究成功后科学扩大治疗人群，称为“补充保障安排”。当前实质安排进一步临床开发，生物学筛选差异并不自动是不合理获取差异；原文也未直接提供支付、供药或治疗获取补偿。','llm_interpretation_assessment':'是否将有明确未覆盖治疗需要的进一步研发安排纳入按需机会，而非一般试验人群扩展，须裁定；不能把“合理扩大”本身当公平证明。','decision_limit':'完整保留“并不代表该治疗药物绝对无效”的否定推断；本核查只讨论 F，不因 E presence 或该否定决定 F。'}
}
records=[]
for m in materials:
 j=judgments[(m['dimension'],m['id'])];records.append({**m,'diagnosis':j,'exact_manual_clauses':{k:clauses[k] for k in j['manual_clauses']}})
report={'scope':'source/evidence-informed AI development diagnosis, not independent human validation or adjudicated truth','manual_sha256':summary['manual_sha256'],'first_comparison_input_sha256':summary['comparison_input_sha256'],'counts':summary['counts'],'fixed_selection_rule':summary['fixed_selection_rule'],'representatives':records,'limits':['All difference rows are counted, but semantic inspection is limited to fixed 6+6 representatives; document concentration is not error concentration.','Cases marked boundary require researcher/expert decisions; no expected labels or semantic edits are applied.','No old A/B labels, κ, human labels or model calls are read/run. Current machine-to-machine differences do not identify old A/B validity.','Later source-reader corrections and 01446 syntax repair are separate executions; these 173/86 are the specified first comparison, not a newly claimed final comparison.','This fixed sample does not include an exit/withdrawal difference; its success or failure cannot be inferred here. Actual withdrawal can express presence if object and support action are bound, whereas programme status alone is insufficient.'],'source_read_checks_all_selected':all(m['source_sha_matches_recorded'] and m['candidate_sha_matches_recorded'] and m['actual_current_literal_found_in_source_read'] for m in materials),'protected_files_unchanged':summary['protected_files_unchanged_at_end'],'no_code_input_or_label_modifications':True,'not_performance_estimate':True}
(B/'I_F有限原因核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
lines=['# 首次 I/F 分歧的有限只读原因核查','', '当前差异同时含实现缺口、范围泛化与尚待统一的边界，不能据此认定 LLM 或规则整体更好。这里是已知机器输出后的开发诊断，不是独立人工效度。未读旧 A/B 标签或 κ，未改原代码、材料或输出。','', '全体计数按实际 unit source 组件归档，完整文档明细及可复现选择脚本另存：','', '|维度|部门|规则0/LLM1|规则1/LLM0|合计|','|---|---|---:|---:|---:|']
for d in ('I','F'):
 for g in ('NMPA','NHC','NHSA'):
  rs=summary['counts'][d]['department_direction_counts'];a=sum(r['n'] for r in rs if r['department']==g and r['rule']==0 and r['llm']==1);b=sum(r['n'] for r in rs if r['department']==g and r['rule']==1 and r['llm']==0);lines.append(f'|{d}|{g}|{a}|{b}|{a+b}|')
lines+=['','I 共 173 条、36 个源组件；最大集中为三程序附件正文21、2023加快审评规范21、数据保护结构化正文20、2025临床试验政策解读14。F 共86条、22个源组件；最大集中为三程序附件正文11、2026医保问答10、基层药品联动公报9、2025医保支持创新药8。这些是差异计数，不是错误数量。','', '固定选择：每个部门×分歧方向取差异最多的源组件及最小ID；再由尚未代表的最大文档补满每维6条。并列按源路径、ID排序，不按语义判断重选。12条当前全文、双方实际证据、源SHA与手册逐条引文在 JSON 中。所有代表的源文件与候选 SHA 均匹配，当前文字经实际文本／DOC／PDF页面读取核见；两例 PDF 用 pypdf 有界页去除数字页码作只读核对，未新增运行证书。','']
for d in ('I','F'):
 lines.append(f'## {d}：6条固定代表');lines.append('')
 for r in records:
  if r['dimension']!=d:continue
  x=r['diagnosis'];a=r['direction'];lines += [f"**{r['id'].split('-')[-1]}（{r['department']}，规则{a['rule']}/LLM{a['llm']}）：{x['diagnostic_category']}。**",f"当前原句：{r['current_text']}",f"机制：{x['mechanism']}",f"手册：{'；'.join(r['exact_manual_clauses'].values())}",f"边界：{x['decision_limit']}",'']
lines+=['需先统一的研究判断是：支持程序宗旨与实际设立的界限；注册分类在数据保护映射表中的角色；一般治疗需要与可指认保障缺口；明确目录评审维度要求是否本身构成实质议题。对程序退出，要保留撤回关系及对象绑定，不把“不再”读成仍在支持；本固定12条未含退出分歧，不能冒称该机制已由本检查验证。','', '旧 A/B 与新操作定义的迁移另属一项研究问题；本表只解释当前两种机器输出的差异。以上候选与边界不回填标签，不触发按例句调参，也不产生真实性能比例。']
(B/'I_F有限原因核查.md').write_text('\n'.join(lines)+'\n')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze={'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manual_sha256':summary['manual_sha256'],'source_input_sha256':summary['comparison_input_sha256'],'diagnostic_artifacts_sha256':{p.name:sha(p) for p in B.iterdir() if p.is_file() and p.name!='只读封存记录.json'},'runtime_or_labels_changed':False,'human_or_model_validation':False}
(B/'只读封存记录.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
print(str(B/'I_F有限原因核查.md'))
