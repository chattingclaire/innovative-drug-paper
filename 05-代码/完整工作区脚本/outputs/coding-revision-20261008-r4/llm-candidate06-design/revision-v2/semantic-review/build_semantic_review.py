"""Persist the reviewer's explicit 39-unit judgments; no model or label mutation."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
DIMS=['S','E','Ec','I','F']
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
NOTES='''
00008|疾病严重及死亡风险不是药物损害。|原句用于界定疾病严重性，未治疗的疾病后果能否视作药物效果内容存在解释边界；当前理由把预防残疾的药物作用补入了原句，审查者倾向E0。|没有药价、药费或药物支付资源内容。|创新程序范围不能把疾病严重程度定义变为创新属性或比较资格。|得不到有效治疗是严重程度反事实，不等于不能获取治疗。
00090|疫苗分类没有药物风险内容。|防控急需和未细化临床价值没有具体效果或治疗推荐内容。|未涉及药物经济内容。|创新疫苗名称与父级优先审评资源是否构成实际支持资格仍是原有边界；保留个人I0，不以历史趋同裁真。|急需本身没有说明短缺或未满足获取需要。
00099|优先审评申请限制不含药物风险内容。|未评价仿制药治疗效果。|没有价格、费用或支付内容。|相同活性成分、途径和新申报不证明创新。|本单元自身明示临床急需的短缺药品；短缺事实可计获取内容，不要求另承诺供药。
00110|申请路线未说明安全风险。|临床急需身份不证明效果。|没有药品价格或费用责任。|新药名单和境内未上市不是创新属性。|临床急需的境外已上市境内未上市药品明确指向境内常规治疗获取缺口，可保留F，不由罕见病名称单独推出。
00118|免公示及受理程序无安全内容。|未涉及药物效果或治疗推荐。|没有经济内容。|新药名单和程序待遇不自行构成创新。|本句仍明示临床急需且境内未上市的实际药品获取缺口，不因当前还有公示程序而删去。
00180|不良反应和无法耐受直接涉及药物损害。|明确最终疗效受影响，可计E。|治疗负担未写明经济含义。|没有创新属性或创新研发支持。|不耐受导致失去治疗机会与常规保障获取的边界保留；个人倾向F0，不能以任何旧输出定真。
00637|确认与签约不涉及药物安全。|没有药物效果内容。|支付标准只是协议信息确认字段，没有实质经济评价、标准取值或费用责任。|没有创新内容。|支付范围只是手续字段，没有实质确定给付范围。
00663|没有安全内容。|患者获益显著与临床价值实质涉及治疗获益。|没有价格、费用或费用承担。|创新程度高是明示属性要求，不仅是目录名称。|暂时无法纳入基本目录直接陈述保障排除，不要求另一个商业保险给付承诺。
00771|相关数据明确是费用和基金支出，不是安全资料。|没有效果数据要求。|费用数据获取质量与事务性沟通的边界保留；个人Ec1可由真实指代及数据质量要求支持，不算确定修复或回归。|数据沟通不是创新支持。|费用数据质量没有独立保障获取命题。
00891|预算比例条件不含安全内容。|没有效果评价。|药品费用与费用预算200%的阈值明确经济内容。|独家身份和预算不证明创新。|真实父谓词将预算条件用于确定新的支付范围及补充协议，涉及实际保障条件，不能用泛化简易续约标题替换父谓词。
00964|协商组织与签约没有安全内容。|没有治疗效果内容。|当前仅组织现场价格协商，没有价格取值、调整或经济评价；不能继承上一句测算。|商保创新药目录名称不是创新属性。|协商成功纳入目录是当前明示纳入结果；尚未实施不排除条件性保障内容。
01135|抽象多维证据定义没有具体安全评价要求。|抽象定义不回传后一句效果维度清单。|没有具体经济评价要求。|没有创新评价或支持要求。|没有保障或公平性资料要求。
01264|规格、参照和支付范围没有风险内容。|参照药品没有指定效果比较用途。|当前限定支付范围是保障适用范围；无药价、支付标准、药费责任，不能直接补成经济内容。|无创新内容。|论证确定限定支付范围直接讨论具体保障边界，不因拟谈判或评审阶段排除。
01432|明示必须符合第七条第一款，其实际内容要求提交安全性与质量可控性全部试验数据；S1有直接条件依据。|同一控制性援引要求有效性全部试验数据；不要求本行重新独立写一遍。|保护期限不是药品经济内容。|改良型生物制品是给定的实际创新分类，并直接规定数据专有保护期；attribute成立。|数据保护权利不是患者保障获取。
01446|没有安全内容。|迫切需求不是效果内容。|无药物经济内容。|创新试点宗旨、当前条件引导句及同段较强创新性条件的适用范围仍是原有边界；个人I1有给定条件支持，不称确定改进。|罕见病与需求迫切没有明示获取缺口。
01562|预算条件无安全内容。|没有效果内容。|基金预算增幅100%是药物支付经济内容。|无创新内容。|经核验父句明示满足当前条件可简易续约且有效两年，既有医保药品保障继续；F0仍错误地把实质延续结果降成办理资格。
01616|诊疗方案身份不是安全风险内容。|已纳入诊疗方案只限定不降价例外对象，当前没有治疗推荐或效果评价。|基金超预算与可不降价直接计Ec。|无创新内容。|本句仅价格例外，没有独立保障范围或患者负担内容。
01765|当前明确系统全面安全评价及安全资料质量。|确能带来更好治疗获益是临床获益内容。|没有价格、费用或支付内容。|制定指南以帮助有序高效准备申报资料主要是一般制定宗旨和材料办理便利；未陈述本条实体研发资源或资格，不能由创新对象及指南存在推出I。|迫切需求和尽早上市没有明示保障缺口。
01768|给定语境可消解个性化问题源于安全资料准备，但本句只有沟通形式及未来维护指南，没有实际安全评价或证据要求，S1仍是主题传播。|没有效果内容。|没有经济内容。|沟通方式与未来完善指南不是当前实体研发支持。|没有药物保障或管理难度。
02072|图中没有药物损害评价。|同治疗领域及管理分支没有效果评价。|基金预算及比值A/B、标准变化明示经济内容。|独家身份不等于创新。|整图混合管理转类、简易续约、补充协议及重新谈判，F仍是预识别边界；个人F1可由实际续约与范围连续关系支持，不能只把历史状态条件当新给付结果。
02086|没有安全条件内容。|同治疗领域只是经济市场条件比较范围，不表示效果比较。|原句明示同时满足后项，后项实际包括基金、预算及价格；不能仅因已有结果和期限而认定后项无关。Ec0保留为原有边界，个人倾向Ec1，当前理由及未记boundary_note不足。|独家及续约条件无创新内容。|当前明确既有药物保障协议续约两年，是实际连续期限。
02144|没有药物损害或风险内容。|没有药物效果内容。|总体医保支付机制目的未说明药品费用、费用责任或具体经济评价。|没有创新属性或实体支持。|提高参保人员用药保障水平有明确药品保障联系，制度目标也可计F。
02223|临床试验支持未说明安全评价内容。|试验和同步研发不自行计效果。|无药物经济内容。|支持机构参与创新早期研发与多中心试验是实体便利还是笼统宗旨仍是原有边界；个人I1可辩护，不称确定修复。|同步上市未明示获取缺口或保障安排。
02364|采购验收没有明示药品质量安全或药物风险。|无效果内容。|统一采购职责没有价格、费用或支付。|无创新内容。|内部药学部门采购、检查、验收分工不是患者常规获取渠道，也没有具体配备范围，F0修复成立。
02830|药物警戒、风险最小化及受试者安全明确计S。|试验结果可靠性未指定效果判断，不自动E。|无经济内容。|申请人承担安全义务不是监管机构给予创新研发支持。|受试者权益安全保护不自动是保障获取。
02845|申请人依据安全性风险开展药物警戒保护受试者，S1成立。|未讨论治疗效果。|未讨论经济内容。|申请人自身药物警戒义务不因创新药适用对象成为研发支持。|试验受试者保护不自行计F。
03157|该方法例句没有安全性用途锚点。|同段明确该敏感性分析检测疗效估计偏倚并确定疗效上下限，可消解当前未观测协变量问题的实际效果用途，E1可支持。|无经济内容。|研究方法不是药物创新或实体支持。|接受治疗概率是因果分配问题，不是获取缺口。
03229|不良反应及风险大于收益明示药物风险。|风险收益与临床价值是否足以形成独立临床获益内容存在解释边界；旧审查E1的确定性偏强，本轮保留边界并倾向E1，不因任一旧输出裁真。|药物经济性是明示评价因素。|无创新内容。|真实父谓词以本项条件直接调出医保目录，是实际覆盖退出。
03261|协议期限没有安全内容。|没有效果内容。|期限不继承后句支付标准调整。|无创新内容。|当前规定谈判药品保障协议两年有效期，同段承载医保支付和续签关系；不要求另写患者权益承诺。
03415|减少用药差错是明确风险预防。|整体健康目标没有具体药物效果内容。|无经济内容。|适老化设计总体指导宗旨是否构成实体创新研发指导仍是原有边界，个人I1可辩护，不算确定改善。|体验偏好及一般适宜性不是获取或管理难度。
03471|剂量减半需要未说明损害或用药错误。|剂量调整需要未指定效果结果。|无经济内容。|调整需求本身不是创新或支持。|一般剂量减半或调整没有管理障碍、复杂性或监测负担，不能仅凭临床管理要求泛化计F。
03704|基金安全不是药物安全。|雪中送炭比喻没有效果内容。|当前把进入目录的药品选择直接与医保基金安全底线联系，实际讨论药品支付资源；无具体金额或具体费用列举不是删除理由。|无创新内容。|比喻性取向没有明确获取缺口或覆盖范围。
03712|没有安全内容。|没有效果内容。|重新谈判的降幅与续约比例明确药价调整。|1类序号、新药简称及通用创新宗旨没有给定实际分类含义，不能自行补创新身份或研发支持。|再次谈判机会不是实际保障连续结果。
03735|无安全内容。|新增适应症为协议背景，不是效果判断。|管理转类时点没有药价或费用责任。|无创新内容。|已有保障及完整期限是转类前提，本句主要规定转类时点，不新增保障命题。
03866|书面申请不含药物风险。|未指定效果内容。|保障范围不是支付标准或药费责任。|同通用名规格与申请手续不证明创新。|若未载明规格需纳入时须提出书面申请，是申请动作；未载明不等于当前明示不保障，也没有实质确定纳入结果或给付适用条件，F1仍是把申请机会当覆盖。
03950|未成年人知情同意审查及一般权益安全父题没有具体药物风险或损害内容。|知情同意年龄认知因素不是药物效果。|无经济内容。|无创新内容。|未成年人身份及伦理参与保护不是药物获取或管理难度。
04164|临床试验方案主题没有明确安全证据要求。|方案主题没有指定效果判断用途。|无经济内容。|申请单/多专业沟通形式与议题范围没有监管机构提供实际技术指导或资源，不能由创新药范围继承支持。|无获取或保障内容。
04368|一般处方相符审核未明示药物损害。|处方诊断匹配与药物治疗推荐的操作边界仍保留，个人E0可辩护，不称确定修复。|无经济内容。|无创新内容。|一般处方适宜性不是具体药品管理难度或保障获取。
04894|处方流转流程没有药物损害内容。|没有效果内容。|不继承后句基金费用监测。|信息平台管理不是药物创新。|当前连通医保、医疗机构和定点零售药店并保证电子处方流转，结合双通道语境构成常规取药渠道；不能因基础设施形式或未列具体药名删除F。
'''
ERRORS={('01264','Ec'):0,('01562','F'):1,('01765','I'):0,('01768','S'):0,('03471','F'):0,('03704','Ec'):1,('03866','F'):0,('04894','F'):1}
BOUNDARIES={('00008','E'):0,('00090','I'):0,('00180','F'):0,('00771','Ec'):1,('01446','I'):1,('02072','F'):1,('02086','Ec'):1,('02223','I'):1,('03229','E'):1,('03415','I'):1,('04368','E'):0}
BASIS={'S':['v1.3:21','v1.3:65','v1.3:67'],'E':['v1.3:29','v1.3:31','v1.3:65','v1.4:7','v1.4:9'],'Ec':['v1.3:35','v1.3:37','v1.3:67'],'I':['v1.3:43','v1.3:136','v1.3:142','v1.3:166','v1.4:13','v1.4:16','v1.4:17'],'F':['v1.3:53','v1.3:123','v1.3:152','v1.4:21','v1.4:22','v1.4:24','v1.4:25']}

def main():
 source=read(BASE/'execution-audit/candidate06_all_changes_PRIVATE.json')['rows']
 notes={}
 for line in NOTES.strip().splitlines():
  parts=line.split('|');assert len(parts)==6
  notes['RECODE25-'+parts[0]]=dict(zip(DIMS,parts[1:]))
 assert set(notes)==set(x['id'] for x in source)
 rows=[]
 for x in source:
  ident=x['id'];short=ident.split('-')[-1];actual=x['candidate06_intact_actual_row']; reviews={}
  for dim in DIMS:
   key=(short,dim);a=actual['labels'][dim]
   status='confirmed_error_under_unchanged_manual' if key in ERRORS else 'definition_boundary_not_scored_as_confirmed_error' if key in BOUNDARIES else 'supported'
   judgment=ERRORS.get(key,BOUNDARIES.get(key,a))
   reviews[dim]={'actual':a,'review_status':status,'reviewer_manual_judgment_not_gold':judgment,'reason':notes[ident][dim],'manual_basis':BASIS[dim]}
  rows.append({'id':ident,'complete_input_canonical_sha256':hashlib.sha256(json.dumps(x['input'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'actual_row_canonical_sha256':hashlib.sha256(json.dumps(actual,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'changed_dimensions_vs_each_history':x['changed_dimensions_vs_each_history'],'five_dimension_review':reviews,'reason_evidence_subtypes_reviewed':True,'quote_literal_check_delegated_to_complete_technical_QA':True,'review_read_scope':'完整text、全部给定语境正文及结构关系、当前五维理由/证据/子类型及发生变化历史维度的理由；未读取真人参考标签或保留样本。'})
 old=read(BASE/'candidate05_regression_mechanism_review_PRIVATE.json')['items']
 by={x['id']:x for x in rows};working=[]
 for x in old:
  r=by[x['id']]['five_dimension_review'][x['dimension']]
  working.append({'id':x['id'],'dimension':x['dimension'],'old05_actual':x['actual05'],'candidate06_actual':r['actual'],'reviewer_manual_judgment_not_gold':x['prior_semantic_reviewer_judgment_not_gold'],'status':'fixed_in_this_single_development_run' if r['actual']==x['prior_semantic_reviewer_judgment_not_gold'] else 'persistent_confirmed_error','reason':r['reason']})
 confirmed=[{'id':x['id'],'dimension':d,**r} for x in rows for d,r in x['five_dimension_review'].items() if r['review_status']=='confirmed_error_under_unchanged_manual']
 boundary=[{'id':x['id'],'dimension':d,**r} for x in rows for d,r in x['five_dimension_review'].items() if r['review_status'].startswith('definition_boundary')]
 report={'status':'FAIL_PREDECLARED_REAL_DEVELOPMENT_SEMANTIC_GATE','reviewer_identity':'AI semantic reviewer; no human gold claim','independent_of_A_C_scores':True,'real_units_reviewed':len(rows),'dimensions_reviewed':len(rows)*5,'all_prior05_changed_unit_reviews_included':True,'working_error_cells':working,'working_error_fixed_cells':sum(x['status'].startswith('fixed') for x in working),'working_error_persistent_cells':sum(x['status'].startswith('persistent') for x in working),'confirmed_errors_in_complete_change_review':confirmed,'confirmed_new_regressions_vs05':[x for x in confirmed if x['id'] not in ['RECODE25-01562','RECODE25-01768']],'definition_boundary_cells':boundary,'new_boundary_cells_not_counted_as_confirmed_errors':[x for x in boundary if x['id'] in ['RECODE25-00008','RECODE25-03229']],'Ec02086_reconsideration_preserved':True,'prior03229_E_certainty_reconsidered':'The earlier05 reviewer called E1 supported; full clause can mean clinical benefit or broader net value. Current review records this interpretive boundary, leans E1, and never changes old05 files or uses score preference.','gate_reason':'At least two preidentified errors persist and six new confirmed regressions appear; requiring all11 fixed and no new confirmed regression is not met irrespective of any performance metric or synthetic result.','rows':rows,'limitations':['39 changed units are reviewed over all five dimensions; this is not a semantic census of all240 unchanged units.','Comparators are intact machine histories, not truth. Reviewer judgments and new boundary classifications are transparent and are not backfilled into predictions.','One run cannot identify causal prompt effects or repeat stability. All findings are development reuse, not independent validation.','No full run, adoption, production-label or manuscript changes, metric-based selection, output splicing, or automatic07 design.'],'source_bindings':[{'path':str(p),'sha256':sha(p)} for p in [BASE/'design_freeze.json',BASE/'manual_rule_basis.json',BASE/'execution-audit/candidate06_all_changes_PRIVATE.json',BASE/'candidate05_regression_mechanism_review_PRIVATE.json']]}
 dump(HERE/'candidate06_real_change_semantic_review_PRIVATE.json',report)
 print(json.dumps({k:report[k] for k in ['status','real_units_reviewed','dimensions_reviewed','working_error_fixed_cells','working_error_persistent_cells']},ensure_ascii=False))
if __name__=='__main__':main()
