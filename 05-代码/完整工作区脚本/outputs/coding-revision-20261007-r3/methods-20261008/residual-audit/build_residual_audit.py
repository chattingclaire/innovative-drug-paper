from pathlib import Path
import json,hashlib,datetime,sys
R=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/coding-revision-20261007-r3');D=Path(__file__).parent;S=R/'statistics';C=R/'methods-20261008/rules-v36.2-development-complete-statistics'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def bind(p):return {'path':str(p),'sha256':sha(p)}
def load(p):
 a=[json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()];r={x['id']:x for x in a};assert len(a)==len(r);return r
DIMS=['S','E','Ec','I','F'];manifest_path=S/'final_bindings_v14_CONFIRMED_r3.json';manifest=read(manifest_path)
assert sha(manifest_path)=='46582af989d0473655b71ba38f174c2043794b8da9833bca9940aa0cf62c71cd'
source=read(R/'rules-v36.2-development/final_candidate_binding.json');freeze=read(source['freeze']['path'])
assert source['prediction']['sha256']=='105d10d7f441ed2c609911aa1f02bcaa4fc695acea35c6164750930a3021cc2b'
for b in [source['prediction'],source['run'],source['freeze'],source['QA'],manifest['material']['llm_inputs'],manifest['references']['A'],manifest['references']['C'],manifest['sampling_design']]:assert sha(b['path'])==b['sha256']
for p,h in freeze['manuals'].items():assert sha(p)==h
assert read(source['QA']['path'])['all_checks_pass']
comparison_path=C/'machine_reference_classification.json';stats=read(comparison_path)['comparisons'];prior_path=R/'methods-20261008/v36.2-development-diagnostic/comparisons.json';prior=read(prior_path)['comparisons'];refqa_path=S/'final-v14/reference_binding_QA.json';refqa=read(refqa_path)
inputs=load(manifest['material']['llm_inputs']['path']);rules=load(source['prediction']['path']);refs={x:load(manifest['references'][x]['path']) for x in ['A','C']};candidate_path=S/'final-v14/candidate_reference.jsonl';candidate=load(candidate_path)
design=read(manifest['sampling_design']['path']);sample={x['original_id']:x for x in design['sample']};prob=[rid for rid,x in sample.items() if x['component']=='probability_canonical'];assert len(prob)==180
primary=next(x for x in stats if x['component']=='probability_canonical' and x['group']=='ALL' and x['weighting']=='eligible_design_weighted' and x['reference']=='candidate' and x['dimension']=='E')
errE={k:[rid for rid in prob if rules[rid]['prediction']['labels']['E']==p and candidate[rid]['labels']['E']==q] for k,p,q in [('FN',0,1),('FP',1,0)]}
assert set(errE['FN'])==set(['RECODE25-03157','RECODE25-03065','RECODE25-00919','RECODE25-02158']) and not errE['FP']
Epositive=[rid for rid in prob if rules[rid]['prediction']['labels']['E'] or candidate[rid]['labels']['E']]
othererr=set()
selected=[]
for row in stats:
 if row['component']=='probability_canonical' and row['group']!='ALL' and row['weighting']=='unweighted' and row['dimension'] in ['S','Ec']:
  old=next(x for x in prior if x['method']=='v36.2' and all(x[k]==row[k] for k in ['component','group','weighting','reference','dimension']))
  selected.append({**row,'errors':old['errors']});othererr.update(old['errors']['FN']);othererr.update(old['errors']['FP'])
ids=sorted(set(Epositive)|othererr)
manual_path=R/'protocol/完整五维手册-v1.3.md';operation_path=R/'protocol/共用操作说明-v1.4.md'
clause_specs={'M_context':(manual_path,17),'M_S':(manual_path,21),'M_E':(manual_path,29),'M_E_design':(manual_path,31),'M_Ec':(manual_path,35),'M_Ec_exclusions':(manual_path,37),'M_requirement':(manual_path,65),'M_transaction':(manual_path,67),'M_macro':(manual_path,87),'M_dispute':(manual_path,97),'M_development':(manual_path,105),'O_current':(operation_path,7),'O_no_theme':(operation_path,9),'O_F_scope':(operation_path,21),'O_SEEc':(operation_path,30),'O_target':(operation_path,38)}
clauses={k:{**bind(p),'line':n,'quote':p.read_text().splitlines()[n-1]} for k,(p,n) in clause_specs.items()}
code_specs={'reference_relation':(R/'rules-v36.2-development/runtime/referenced_relations_v34.py',26,48),'reference_application':(R/'rules-v36.2-development/runtime/referenced_relations_v34.py',89,118),'E_direct_and_evidence':(R/'rules-v36.2-development/runtime/rules_se.py',361,442),'E_antecedent':(R/'rules-v36.2-development/runtime/rules_semantic_v36.py',117,141),'S_direct':(R/'rules-v36.2-development/runtime/rules_se.py',35,43),'S_review':(R/'rules-v36.2-development/runtime/rules_se.py',445,492),'Ec_cutoff':(R/'rules-v36.2-development/runtime/rules_ec.py',142,152)}
code={k:{**bind(p),'line_start':a,'line_end':b,'code':'\n'.join(p.read_text().splitlines()[a-1:b])} for k,(p,a,b) in code_specs.items()}
# These are this unblinded AI auditor's reasoned readings, not replacement labels.
assess={
'RECODE25-00919':{'focus':['S','E','Ec'],'category':'有意保守边界与实质条件解释分歧；尚未确证为实现bug','stance':'更支持S/E/Ec纳入；不能因此自动赋F或I。','reason':'“符合第七条、第八条规定”是当前申报资格的必要条件。已核验第七条明确临床必需、安全有效、价格合理；不是仅由文件标题推定，也不是从所有后项搬运标签。操作说明允许条件消解，且不要求已经产生正面效果。规则成功读入真实引用，却把当前关系限制为纳入/退出、支付计算、专有权利或按…评价，没有“符合特定条款条件”的路径，构成可定位的保守关系限制。但历史开发控制正是有意排除此种办理/资格继承，未匹配本身不证明程序bug；关键在这一限制是否比共同手册更窄。','counterargument':'C认为本句只列申报资格，须当前另行明述各维评价；这与手册允许条件性规定和明确承接存在张力；手册却未逐字裁决“符合条款、可以申报”的条件援引是否已达实质关注阈值。本次审读不能替换C，也不能把这一规范争议伪装成已确证的漏词bug。','boundary':'可纳入的是所援引的必要药品价值条件；申报资格不是实际给付，不传播第八条的保障退出后果、后项药品类别或创新身份。泛称依照法规精神也不能按整部法规赋标签。','clauses':['O_current','M_context','M_E','M_S','M_Ec','O_F_scope'],'code':['reference_relation','reference_application']},
'RECODE25-02158':{'focus':['S','E','Ec'],'category':'有意保守边界与实质条件解释分歧；尚未确证为实现bug','stance':'更支持S/E/Ec条件内容纳入；候选F另有明显边界疑点，不能连带继承。','reason':'当前用“符合第九条、第十条规定”识别目录调整药品，其对象正由不良反应/风险收益、临床价值不确切/有效性不符、价格费用偏高/经济性不符等实质条件限定。给定父谓词只恢复调整范围，所引特定条款才提供对象条件。代码current_relation对此没有可应用类型；历史assessment_scope控制有意不传播评审范围引用，故这是保守解释的已知行为，不是输入未读取或偶发执行失败。','counterargument':'C坚持调整对象列举不独立讨论所引条件。A/T接受S/E/Ec，但A与C均F=0，T还从原条款调出后果推F=1；后者并不是修复S/E/Ec所必需。','boundary':'当前纳入调整/评审范围不等于直接决定退出保障；应隔离具体对象条件与最终处置后果，不能将全部引用维度/行为传播。','clauses':['O_current','M_context','M_E','M_S','M_Ec','O_F_scope'],'code':['reference_relation','reference_application']},
'RECODE25-03157':{'focus':['E'],'category':'纳排争议：效果证据与跨句示例承接','stance':'倾向E纳入，但不足以认定所有统计示例都应命中。','reason':'当前“例如”具体说明未观测协变量使接受治疗概率不同；同段紧接句明确敏感性分析检测这种协变量对疗效估计偏倚的影响，并给出疗效上下限。二者有可指认的相同协变量—治疗概率—疗效估计链，强于只凭真实世界研究主题。但当前句自身尚未说药效，A按最窄单元边界判0，C/T按明确承接判1。','counterargument':'跨句关系不是指代该研究终点的现有实现形态；把同段所有统计术语计E会过度传播。两种读取在“明确联系”的操作阈值上有真实分歧，不能当普通关键词漏词。','boundary':'若另设实现，须保留同一变量/同一估计关系和明确疗效目标；不得仅见协变量、接受治疗概率、偏倚就赋E，也不等于实际保障获取。','clauses':['M_E','M_E_design','M_context','O_current','O_no_theme'],'code':['E_direct_and_evidence','E_antecedent']},
'RECODE25-03065':{'focus':['E'],'category':'参照可疑兼纳排争议：研究用途不必然等于效果内容','stance':'在现冻结手册下，规则E=0有充分依据；不建议为贴合T而直接扩张。','reason':'当前明确S来自联合用药安全性；E方面只列“新增适应症研究”和建立历史/外部对照。T把治疗用途研究解释成效果证据，A/C均认为未说明效果判断。当前没有疗效目标/终点/效果评价，邻句“科学方面的有效性”指科学可解释性、假设和I类误差，不能作为药效依据。','counterargument':'新增适应症研究通常可涉及治疗效果，但“通常”不是当前文本已明确的研究目的，也可能涉及安全或其他问题。手册明确试验设计本身不一律赋E。T的宽读有解释性，仍需人工校准而不能冒充确定真值。','boundary':'不能将新增适应症、单臂试验、外部对照或“临床问题”设为无条件E触发；若另有明确药效目标再判。','clauses':['M_E','M_E_design','M_context','O_no_theme'],'code':['E_direct_and_evidence']},
'RECODE25-00771':{'focus':['Ec'],'category':'纳排争议：经济资料获取要求与事务性质量保证','stance':'倾向维持规则Ec=0，先明确数据质量管理与新增内容要求的界线。','reason':'“相关数据”确实可还原为药品费用及基金支出，不是缺少经济对象。争议在当前行为：保持沟通并保证获取科学、及时、准确，是已规定数据的质量/沟通要求，还是新的经济证据收集要求。A/C判前者，T判后者；不能说T没有读懂指代，也不能仅按被指代数据包含费用就决定Ec。','counterargument':'手册也纳入收集内容或证据，T把“保证获取”视为收集要求有文字依据；手册没有给出这类质量保证句的专门例。故其优先级低于已明确的费用测算或数量要求，不宜直接改排除规则。','boundary':'若当前新增费用/基金支出数据的收集范围、测算内容，Ec可纳入；纯及时性/准确性或公开格式不能自动继承数据主题。','clauses':['M_Ec','M_requirement','M_transaction','O_current'],'code':[]},
'RECODE25-02144':{'focus':['Ec'],'category':'可能的真实覆盖缺口，兼药物支付层级纳排分歧','stance':'较倾向Ec纳入，但不能把所有医保宗旨自动赋Ec。','reason':'当前把医保用药管理与建立医保支付机制直接连接，研究对象是药品目录；操作说明明确药物支付归Ec，并不要求必须已有具体价数。A因未说明费用责任或标准而判0，C/T按支付制度关注判1。规则未留下Ec抑制理由，也未产生药物支付机制关系证据，符合偏窄覆盖的表现。','counterargument':'“管用高效”是抽象宗旨，未说明标准、费用承担或基金效果，手册Ec的具体例主要为实质支付内容。需区分明确药物支付机制与一般制度口号，不能根据同句F=1反推Ec。','boundary':'不从“根据…法规精神”引入全文维度；不将一般医保筹资、医院管理和行政效率视为药品经济内容。','clauses':['M_Ec','M_Ec_exclusions','M_macro','O_SEEc'],'code':[]},
'RECODE25-02462':{'focus':['Ec'],'category':'较强参照疑点：纯资料取值时点','stance':'规则Ec=0与事务性排除更一致；不应仅因T=1删除日期排除。','reason':'本句仅规定汇率/价格费用信息截至某日，说明书按批件日，没有新增测算、比较、费用责任或价格条件。A/C均0，新增首次T按价格信息要求判1。规则明确记录economic_data_cutoff_date_only抑制，说明不是没读见价格。手册事务性条款要求“没有新增评价内容要求”的不因维度名称赋值，更支持0。','counterargument':'手册例示申报时点，并没有逐字列出经济数据截止日。此处是将相同的内容/事务区分原则应用于取值日期；需要如实标为审读推论，而不是声称手册已有该例。T也是实际独立提交，不能因其单独不同而直接改标。','boundary':'如果同句另有成本效果分析、价格调整或费用承担要求，不能整句排除。当前观察不足以支持取消所有日期排除。','clauses':['M_requirement','M_transaction','M_Ec_exclusions','O_current'],'code':['Ec_cutoff']},
'RECODE25-04346':{'focus':['S'],'category':'可能的真实关系覆盖不足，兼风险资料边界分歧','stance':'较倾向S纳入，依据当前审方用途及用药史/过敏史，不依据前条。','reason':'当前要求将用药史、过敏史提供给处方审核；这不是单纯系统建设，具体资料与用药风险识别有直接用途关系。A/T如此判S，C认为未明确风险评价。规则输出S0且无相关证据，已读代码虽有过敏试验等内容，未见审方—过敏史资料这一路径。','counterargument':'“病史”或“过敏史”单词本身不总是药物损害证据；当前也列通用检查/检验等信息。手册未逐字列审方史料，故应限制在当前药物审核用途，不能一般病历全赋S。','boundary':'前一条的用药错误拒绝调配不是本句证据；一般处方规范或医院信息化仍可为0。','clauses':['M_S','M_requirement','M_context','O_current'],'code':['S_direct','S_review']},
'RECODE25-03763':{'focus':['Ec'],'category':'参照C纳排分歧；非候选参照下的规则错误','stance':'较支持规则Ec=1，保留C=0理由。','reason':'当前不只是模板或谈判程序名称，而明述材料用于医保底价测算，即药价决定的资料基础。A/T及规则均1，C因未新增具体经济评价内容而0。手册允许讨论药价和评价证据，不要求列明计算数值。','counterargument':'若只有模板、文件名或用途泛称，应排除；本句的关键增量是底价测算。不能把所有谈判材料事务性说明纳入。','boundary':'本条只解释NHSA对C的1个FP，不属于对候选参照的FP；不拿一方较接近机器就选作金标准。','clauses':['M_Ec','M_requirement','M_transaction','M_Ec_exclusions'],'code':[]}
}
history_path=R/'rules-v34-audit/architecture/reference_relation_results.json'
history=read(history_path)
assert history['all_passed'] and history['n']==12
same_cited=[x for x in history['controls'] if x['control'] in ['generic_evaluation','specific_effect','administrative','navigation']]
assert len({x['cited_text'] for x in same_cited})==1
history_bindings={'script':bind(R/'rules-v34-audit/architecture/reference_relation_controls.py'),'results':bind(history_path),'architecture_rationale':bind(R/'rules-v34-audit/architecture/AUDIT.md'),'original_sealed_relation_code':bind(R/'rules-v34-audit/architecture/runtime-sealed-sourceblind-20261007/referenced_relations_v34.py')}
assert history_bindings['original_sealed_relation_code']['sha256']==code['reference_relation']['sha256']
for rid in ['RECODE25-00919','RECODE25-02158']:
 assess[rid]['historical_intent']='v34预先构造行政办理和评审范围反例，预期援引维度为空；当前v36.2引用消费模块与该封存代码SHA逐字相同。不能把故意边界直接称为未匹配bug；开发对照不是人工真值。'
 assess[rid]['unresolved_normative_question']='手册允许用语境消解条件，且S/E/Ec不要求已产生正面结果；同时禁止背景复制。特定实质条件作为必要申报/调整对象限定是否已构成讨论，尚存在A/T与C的真实口径差。F的实际保障门槛不能自动推广到S/E/Ec，但也不能据此断言一切符合条款皆计入。'
 assess[rid]['code'].append('reference_role')
p=R/'rules-v36.2-development/runtime/source_context_adapter_v34.py';code['reference_role']={**bind(p),'line_start':144,'line_end':153,'code':'\n'.join(p.read_text().splitlines()[143:153])}
positive_notes={
'RECODE25-00292':'明确药物试验OS获益、与生存获益相关终点和更有效治疗；不是仅试验设计。',
'RECODE25-00442':'当前明确更好地评价药物长期效果；非仅AI方法名称。',
'RECODE25-00694':'当前明确有效性内容，RCT/指南作为这一内容的高等级证据要求。',
'RECODE25-01145':'明确分析测算药品的成本、效果、效用和效益，E/Ec可同时存在。',
'RECODE25-02215':'直接说明临床试验确定药物安全性和有效性的研究目的。',
'RECODE25-02515':'当前医保支付标准要求符合药品临床价值，并考虑患者获益；不是单纯谈判程序。',
'RECODE25-03101':'“该研究的主要终点…验证”明确承接同段该药减少临床骨质疏松性骨折的效果研究；强于纯代表性字样。',
'RECODE25-03229':'当前临床价值、药物风险大于收益的权衡，含治疗获益判断与否定结果。'}
# Collect current materials plus original actual submissions, and validate all
# packet fields against current v14. No new labels are written to reference files.
origin_files={};case_rows=[]
def submission(prov):
 for k in ['result','packet']:
  p=prov[k+'_path'];h=prov[k+'_sha256'];assert sha(p)==h;origin_files[p]=h
 result=next(x for x in read(prov['result_path'])['rows'] if x['id']==prov['blind_id'])
 packet=next(x for x in read(prov['packet_path'])['rows'] if x['id']==prov['blind_id'])
 return result,packet
for rid in ids:
 coders={}
 for name in ['A','C']:
  prov=refs[name][rid]['annotation_provenance']['effective'];raw,packet=submission(prov)
  assert raw['labels']==refs[name][rid]['labels'] and raw['dimension_reasons']==refs[name][rid]['dimension_reasons']
  for k in ['text','source_title','pages','contexts','context_usage']:assert packet[k]==inputs[rid][k],(rid,name,k)
  coders[name]={'effective_provenance':prov,'original_submission':raw}
 if rid in refqa['T']['provenance']:
  prov=refqa['T']['provenance'][rid]['effective'];raw,packet=submission(prov)
  for k in ['text','source_title','pages','contexts','context_usage']:assert packet[k]==inputs[rid][k],(rid,'T',k)
  coders['T']={'effective_provenance':prov,'original_submission':raw}
 else:coders['T']={'status':'not_reviewed','reason':'candidate uses frozen A/C agreement for this case; no invented T label or reason'}
 if rid in assess:assessment=assess[rid]
 else:
  assert rid in positive_notes
  assessment={'focus':['E'],'category':'E一致阳性内容复核（TP）','stance':'当前材料支持E内容。','reason':positive_notes[rid],'counterargument':'此项是已暴露样本的内容检查，不构成独立确认或一般化准确率。','boundary':'只使用当前内容和真实必要承接，不从整篇研究主题传播标签。','clauses':['M_E','M_E_design','O_current'],'code':[]}
 case_rows.append({'id':rid,'group':sample[rid]['group'],'sampling':sample[rid],'material':inputs[rid],
  'current_unit_text_sha256':hashlib.sha256(inputs[rid]['text'].encode()).hexdigest(),'A_C_T':coders,'candidate':candidate[rid],
  'rules_prediction':rules[rid]['prediction'],'candidate_confusion_membership':{d:('TP' if rules[rid]['prediction']['labels'][d] and candidate[rid]['labels'][d] else 'FP' if rules[rid]['prediction']['labels'][d] else 'FN' if candidate[rid]['labels'][d] else 'TN') for d in DIMS},'unblinded_development_semantic_audit':assessment})
# Exact retrieval of all original reasons, not a newly invented adjudication.
summary={'E_error_ids':errE,'E_positive_union_n':len(Epositive),'E_true_positive_n':8,'E_true_negative_n':168,'E_raw_confusion':{'TP':8,'FP':0,'FN':4,'TN':168},'E_weighted_confusion':primary['weighted_confusion'],
 'E_design_weighted_metrics':primary['metrics'],'E_residual_reading':'No indisputable implementation defect established.2 intentionally excluded conditional-reference cases with plausible overly-strict boundary concern;1 explicit-cross-sentence boundary dispute;1 reference-suspect research-design interpretation. Historical synthetic controls prove intent, not semantic correctness. These are unblinded audit judgments, not replacement gold.',
 'S_Ec_error_union_across_A_C_candidate_n':len(othererr),'distinct_detailed_case_n':len(case_rows),
 'not_just_prevalence':'4 of12 candidate-positive E cases are not retrieved (weighted FN56.9 of positive159.033333). High overall agreement does not erase these errors. All4 have actual AI reference disagreement: A/C differ on3; A=C0,T1 on03065.',
 'reference_policy_note':'All dimensions on all66 T-reviewed cases use T under the pre-frozen policy, including A/C-agreement controls. A=C0,T1 on03065/00771/02462 is not a merge error, but substantive reference uncertainty.',
 'NA_note':'NMPA Ec has60 paired negatives, both marginals0: κ denominator1-pe=0, precisionTP+FP=0, recallTP+FN=0, F1 denominator0. Not missing data or perfect positive-class performance. NHC Ec is1 TP and59 TN; κ1 is based on one positive in the60-case census, not broad evidence of robustness.',
 'action':'No implementation, reference or sampling changes. Any later conditional-reference repair must be bounded by current predicate, exact cited substance and dimension-specific permission; classify safeguards before a new frozen candidate, then independent fresh validation. Never add broad study/indication/data-date triggers just to match T or reach.8.'}
allbinds={'reference_manifest':bind(manifest_path),'candidate_source_binding':bind(R/'rules-v36.2-development/final_candidate_binding.json'),'rule_prediction':source['prediction'],'source_material':manifest['material']['llm_inputs'],'sampling_design':manifest['sampling_design'],'A':manifest['references']['A'],'C':manifest['references']['C'],'candidate':bind(candidate_path),'third_provenance':bind(refqa_path),'complete_statistics':bind(comparison_path),'previous_point_audit':bind(prior_path),'complete_statistics_freeze':bind(C/'output_freeze.json'),'manuals':{p:{'path':p,'sha256':h} for p,h in freeze['manuals'].items()},'original_submission_and_packet_files':[{'path':p,'sha256':h} for p,h in sorted(origin_files.items())],'code':code,'historical_intent_and_control_bindings':history_bindings}
for entry in allbinds['original_submission_and_packet_files']:assert sha(entry['path'])==entry['sha256']
provenance={'stage':'read_only_unblinded_post_exposure_residual_audit','all240_exposed':True,'independent_validation':False,'human_validation_completed':False,'no_rules_labels_reference_or_statistics_modified':True,'no_partial_candidate03_read':True,'scope':'All4 E FNs and0 FPs vs candidate in probability180; all12 candidate/rule E-positive union reviewed; all department S/Ec disagreement cases againstA/C/candidate. Does not claim independent semantic review of168 E shared-negative cases or of all4924.','created_at':datetime.datetime.now().astimezone().isoformat(),'script':bind(Path(__file__))}
data={'provenance':provenance,'bindings':allbinds,'summary':summary,'protocol_clauses':clauses,'department_S_Ec_tables':selected,'cases':case_rows,'historical_same_cited_content_controls':same_cited,'historical_other_controls':history['controls'],'historical_control_scope':'Existing development synthetic controls, not current policy quotations or human gold; read only, not rerun.','diagnostic_revision':'Initial working hypothesis that current_relation lacked a condition form was narrowed after historical negative controls showed intentional exclusion. No confirmed automatic repair proposed.'}
(D/'残余低值逐例审读.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
fmt=lambda v:'NA' if v is None else f'{v:.4f}'
md=['# v36.2残余低值逐例审读','','这是已暴露240条上的只读开发诊断，执行者为已看过规则及A/C/T答案的AI统计审读者；不是新的盲审、真人裁定或独立验证。原始标签、算法和已封存统计均未修改，未读取部分03。','',
'概率180的E对候选参照为TP=8、FP=0、FN=4、TN=168；原始P/R/F1=1.0000/0.6667/0.8000。设计加权四格为'+str(primary['weighted_confusion'])+'，κ/P/R/F1='+ '/'.join(fmt(primary['metrics'][m]['estimate']) for m in ['kappa','precision','recall','f1'])+'。4个漏判占候选12个阳性的三分之一，不能用高总一致率或稀有率把它们消解。','',
'本次未确证无争议的实现缺陷。00919、02158的特定条款条件援引没有进入现有处理路径，但旧构造对照表明这是有意排除申报/评审范围继承，不是源材料缺失或词形漏匹配就能证明的bug；其是否对当前实质条件过于保守，需作为规范解释问题保留。03157是跨句统计示例如何承接疗效证据的边界；03065是T对新增适应症/外部对照作宽读，不能据此把研究类型直接设为E触发。每项审读结论均保留相反理由。','',
'E的4个FN全部存在A/C/T判断差异：00919、02158为A1/C0/T1，03157为A0/C1/T1，03065为A0/C0/T1。全部T评审项按冻结政策替换五维，故即使A/C一致，T也可能改变候选。此机制不是合并错误，但候选仍然不是无误金标准。','',
'## 分部门S/Ec四格与NA','','表中四格顺序TP/FP/FN/TN；每部门n=60、设计权重在部门内恒定，因此点值与未加权相同。','',
'|部门|参考|维度|四格|κ|P|R|F1|NA原因或解释|','|---|---|---|---|---:|---:|---:|---:|---|']
for r in selected:
 note='；'.join(r['undefined_point_reasons'].values()) or ('只有1个共同阳性，不能从κ=1推断普遍准确' if r['group']=='NHC' and r['dimension']=='Ec' else '无FN/FP' if not any(r['errors'].values()) else '错误ID见JSON及下文')
 md.append('|'+ '|'.join([r['group'],r['reference'],r['dimension'],'/'.join(map(str,r['raw_confusion'].values())),*[fmt(r['metrics'][m]['estimate']) for m in ['kappa','precision','recall','f1']],note])+'|')
md+=['','药监Ec的κ/P/R/F1为NA是两方60条全部为0造成的代数退化；不是60条缺失，也不是阳性识别率100%。卫健Ec只有1个共同阳性，虽然该剩余框是普查，语义真值和泛化不确定性仍存在。NHSA安全性只有4个候选阳性，漏掉两条条件援引就使R=0.5；小分母解释数值敏感，不能消除相对候选参照的实际FN；是否为语义真漏判仍须看具体内容。','',
'## 逐例审读：全部E差异与S/Ec差异','','以下原句、必要语境及三方理由来自冻结文件。完整语境、逐字证据、原提交路径/SHA/盲ID、全部五维标签及运行证据均存JSON。']
for row in case_rows:
 rid=row['id'];a=row['unblinded_development_semantic_audit']
 if a['category'].startswith('E一致'):continue
 md+=['',f"### {rid}（{row['group']}；关注{'/'.join(a['focus'])}）",'',f"原句（{row['material']['source_title']}，页码{row['material']['pages'] or '原材料未登记页码'}）：{row['material']['text']}",'',f"判断类别：**{a['category']}**。{a['stance']}",'']
 # Current paragraph and expressly cited clauses are compact enough for this table;
 # complete context dictionaries remain unabridged in JSON.
 ctx=row['material']['contexts'];pars=ctx.get('paragraph_context',[])
 for p in pars:
  if p['text']!=row['material']['text']:md.append('同段必要语境：'+p['text'])
 for p in ctx.get('explicitly_cited_articles_v10',[]):
  if any(s in p['text'] for s in ['安全有效','临床价值','价格或费用','有效性','药物经济性']):md.append('明确被引条件：'+p['text'])
 if rid=='RECODE25-02158':md.append('当前恢复的父谓词：'+ctx['verified_parent_context'][0]['text'])
 md+=['','|标签流|关注维标签|原理由|','|---|---|---|']
 for coder in ['A','C','T']:
  item=row['A_C_T'][coder]
  if 'original_submission' not in item:md.append(f'|{coder}|未评审|没有补造标签或理由|');continue
  raw=item['original_submission'];md.append('|'+ '|'.join([coder,'；'.join(f'{d}={raw["labels"][d]}' for d in a['focus']),'；'.join(d+'：'+raw['dimension_reasons'][d] for d in a['focus'])])+'|')
 md+=['', '审读理由：'+a['reason'],'','反向理由与限制：'+a['counterargument'],'','不能泛化为：'+a['boundary'],'','共用条款：'+ '；'.join(f"[{k}，第{clauses[k]['line']}行]({clauses[k]['path']}:{clauses[k]['line']})" for k in a['clauses'])+'。']
 if a['code']:md+=['','实现定位：'+ '；'.join(f"[{k}]({code[k]['path']}:{code[k]['line_start']})" for k in a['code'])+'。']
md+=['','## 同一被引内容、不同当前关系：已有构造正反对照','','下面是v34已经封存的教学/开发构造例及当时实际结果，不是政策原句、真人金标或本轮新运行；四行引用同一句“第二条 药品须安全有效、价格合理。”。当前v36.2的引用消费模块与该旧封存模块SHA相同。对照说明有意的关系差异，不能证明该边界一定符合研究构念。','','|当前命题（构造）|旧预期引用维度|旧实际引用维度|','|---|---|---|']
for h in same_cited:md.append('|'+ '|'.join([h['current_unit'],'/'.join(h['expected_cited_dimensions']) or '空','/'.join(h['actual_cited_dimensions']) or '空'])+'|')
md+=['','另有最接近02158的旧构造反例：“符合第二条的药品可以纳入目录评审范围。”引用“第二条 疗效不确切的药品应调出药品目录。”，旧预期和实际均无引用维度。说明开发者主动把当前评审对象分类与所引疗效/保障后果分开。00919/02158是否应因“符合”这一具体必要条件而例外，不能由A/T多数或新分数直接裁决。', '', '现手册明确支持“按该条评价药品价值”等当前实质评价及其限定维度；也明确排除只凭程序身份/背景推断。对“特定价值条件被纳入申请/评审对象定义”的中间情形，文本未给出逐字决策例。审读较倾向允许必要S/E/Ec条件内容，但这种偏好不是确证bug，更不授权自动修复。', '', '03157也必须有当前“例如”所指的同一未观测协变量—治疗概率—疗效估计关系才有宽读依据；仅后句出现疗效或整段谈研究，不足以继承E。A的窄读仍需保留。']
md+=['','## E其余8个阳性病例内容复核','','这8条是规则与候选的TP；复核用于确认“直接效果/证据要求”与上述边界病例的区别，不是第二套独立效度。168个共同阴性没有重新逐条语义复审，不能据此声称已找齐所有真实错误。','','|ID|当前内容为何支持E|A/C/T|','|---|---|---|']
for row in case_rows:
 if row['id'] not in positive_notes:continue
 states=[]
 for name in ['A','C','T']:
  item=row['A_C_T'][name];states.append(name+('='+str(item['original_submission']['labels']['E']) if 'original_submission' in item else '=未评审'))
 md.append('|'+ '|'.join([row['id'],positive_notes[row['id']],'/'.join(states)])+'|')
md+=['','## 处理边界','','1. 00919/02158首先是有意关系边界的争议样例，尚不能宣布代码错误或据分数放开。若后续人工校准认为该排除过宽，任何候选都必须先限定“当前具体条件—特定已认证引用内容”的关系，并分别决定S/E/Ec；不能把F中的实际保障限制误施于所有维度，也不能反向把所引退出后果自动赋F。泛称法规依据、研究主题、程序身份及相邻条款内容应保留为反例。',
'2. 03157的同变量跨句承接、04346的审方风险资料、02144的明确药物支付机制有可讨论的内容依据，但存在真实的操作阈值分歧，应记录而非笼统当成稀有率问题。单纯过敏史、医院信息化、医保宗旨不能自动扩张。',
'3. 03065、02462需要优先保留参照疑点；00771属于事务性资料质量与新增证据要求的边界。不能为了接近T而无条件放开新增适应症、外部对照、数据截止日或“相关数据”触发。03763只解释对C的FP，当前规则与候选相合，不能混进候选误判数。',
'4. 0.8不触发自动修改。现统计照报；若后续授权修复，原240条仍只能用于开发，另做预先冻结、未暴露材料验证，并补真人参照。此次不生成替换标签、不重新计算“去掉难例后”的好看指标，也不选择更贴近机器的A/C/T作为金标准。','','## 引用条款原文','']
for k,x in clauses.items():md+=['- '+k+f"（[{Path(x['path']).name}:{x['line']}]({x['path']}:{x['line']})）："+x['quote']]
(D/'残余低值逐例审读.md').write_text('\n'.join(md)+'\n')
# Confirm every frozen input remained unchanged and the sealed statistics file set
# matches the existing output freeze, without rewriting it.
for p,h in origin_files.items():assert sha(p)==h
sealed=read(C/'output_freeze.json');assert all(sha(C/n)==h for n,h in sealed['files'].items())
qa={'all_checks_pass':True,'E_FN_n':4,'E_FP_n':0,'E_positive_union_read_n':len(Epositive),'detailed_case_n':len(case_rows),'department_S_Ec_rows':len(selected),'original_submission_packet_binding_count':len(origin_files),'all_current_v14_material_fields_match_original_effective_packets':True,'all_A_C_labels_and_reasons_match_original_submissions':True,'all_frozen_complete_statistics_hashes_unchanged':True,'no_partial03_read':True,'semantic_audit_is_unblinded_development_not_gold':True}
(D/'audit_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
(D/'output_freeze.json').write_text(json.dumps({'files':{p.name:sha(p) for p in D.iterdir() if p.is_file() and p.name!='output_freeze.json'}},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(qa,ensure_ascii=False))
