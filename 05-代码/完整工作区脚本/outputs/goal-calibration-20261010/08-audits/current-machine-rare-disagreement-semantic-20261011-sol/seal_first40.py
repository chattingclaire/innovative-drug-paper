"""Seal actual first40 semantic audit judgments; no classifier call or label edit."""
from pathlib import Path
import datetime,hashlib,json,collections,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent.parent;OUT=P/'phase01-first40';OUT.mkdir(exist_ok=False)
MANUAL=B/'03-manual/full4481-common-release-20261010-root/manual.txt';manual=MANUAL.read_text()
rows=[json.loads(l) for l in (P/'selected-semantic-inputs.jsonl').open()];byid={r['id']:r for r in rows}
full=''.join(c['text'] for c in rows[0]['source_bundle']['source_full_text_resources']);assert len(full)==9612
def bind(q):
 q=Path(q).resolve();r=q.read_bytes();return dict(path=str(q),bytes=len(r),sha256=hashlib.sha256(r).hexdigest())
def write(n,x):
 with (OUT/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def ptr(raw,path):
 for k in path.lstrip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');raw=raw[int(k)] if isinstance(raw,list) else raw[k]
 return raw
manual_quotes={
 'finite_named_action':'当前明确设立、实施、开放、适用、限制或终止同一制度安排时，可用共同材料中已经核明的该安排定义、适用对象和直接机制补全所指；',
 'member_no_sibling':'当前只是某一成员或该成员的解释时，按该成员的实际内容判断，不反向继承全部并列成员、整个程序或支持计划的维度。',
 'I_clinical_link':'以及有明确创新联系的临床优势、国产原研/自主研发价值。',
 'I_support':'必要语境可以补足明确承接的支持对象或条件，不要求每句重复创新词、以监管机构作主语或出现“提供”。',
 'I_improvement':'仅属性变化、一般设计/优化建议时，须由原文明确既有治疗/使用局限，或明确拟用设计所针对的操作障碍，并建立具体改变与治疗/使用表现改善的关系；',
 'postadmission_scope':'当前实质实施某程序对已纳入品种的技术沟通服务，可用共同材料中同版同一程序的完整对象范围及纳入后技术审评、优先沟通或补充技术资料的具体机会补足I3三项证据。',
 'F_gap_allocation':'明确药物保障缺口与按需要的补偿、优先保障或资源分配相连；不同治疗需要/持续治疗负担与适当保障安排相连；',
 'F_branch':'并列“或”条件逐支判断，同一记录因其中一支符合可记1，其他支不随之获公平含义。',
 'F_admin':'纯收件、通知、签章、一般截止日期不因对象为短缺/罕见病就记F；',
 'F_convenience_excluded':'仅给药便利、储存或监测复杂度、临床管理难度；',
 'F_same_priority':'当前实质实施某程序的服务时，只有同版同一程序、同一阶段明确把可辨认的所需治疗保障缺口与该项优先机会相连，才可据此补足具体F关系。',
 'I_mixed':'混合对象范围可因其中有实际创新/改良支持分支而记I，其他对象分支不因此都具创新含义。',
}
anchors={}
for name,q in manual_quotes.items():
 a=manual.index(q);anchors[name]={'path':str(MANUAL.resolve()),'line_1based':manual.count('\n',0,a)+1,'unicode_interval_half_open':[a,a+len(q)],'quote':q,'sha256':bind(MANUAL)['sha256']}
I={
 '00009':('有明确创新联系的临床优势资格','当前并非仅疾病定义，实质规定提供有效治疗或显著终点改善。相邻同版范围明确创新药/改良型新药，直接条件父句要求满足；符合I1/I4，不能把这份证据条件只因无创新词清成0。'),
 '00010':('有明确创新联系的临床优势资格','当前要求相对安慰剂/历史对照具有显著临床结局改善，同版创新/改良范围及条件父句直接承接。不是从疾病严重程度单独继承I。'),
 '00011':('有明确创新联系的临床优势资格','当前比较完全应答、部分应答或临床意义明确的应答率提高，实际临床优势内容与创新/改良资格直接连接。'),
 '00012':('有明确创新联系的临床优势资格','当前规定联用后的显著或重要疗效提高，并非由联用形式本身认定创新；同版范围及条件父句明确创新/改良对象。'),
 '00013':('实质治疗属性改良','现有仅治症状与该药治病因、抑制病情并带来持续获益形成明确局限—改变—改善关系。I2不要求已经证明优效。'),
 '00014':('相同疗效下的安全性改良','同一临床优势资格中，现有不可替代治疗与候选药显著安全性优势、替换或重要补充直接相连。依据具体比较和创新联系，不是孤立新药一词。'),
 '00020':('实际申请机会及资格评估','当前要求充分评估同一程序范围/条件并提出理由，同时开放申请。范围明确创新/改良研发及纳入后的技术支持；I1/I4内容关系尤其直接，I3只能表述可申请支持而不能称已获全部支持。'),
 '00026':('纳入实质授予研发支持','无异议即纳入是取得同版优先沟通及研究方案反馈机会的实质条件，不只是公示或通知。普通异议手续分支不继承该依据。'),
 '00028':('实际研发技术服务','当前直接优先配置资源沟通、加强研发指导；同版纳入对象含创新/改良研发，同阶段支持关系闭合。规则身份/形式排除未解释这项实际服务。'),
 '00030':('同阶段优先技术服务','当前包含关键阶段会议和一般技术咨询并明确优先处理；与同版纳入对象及研制指导直接相连，不是仅列面对面/电话形式。'),
 '00034':('保留后续研发反馈机会','当前允许错过首次交流窗口后仍在后续关键阶段会议提交研究问题；该会议同版直接有审评人员研究方案反馈。这是实际办理便利，不凭6个月数字推更快。'),
 '00035':('研究方案实际反馈','当前安排审评人员沟通、下一步研究方案意见建议并反馈申请人，同一纳入阶段的创新/改良对象可以使用。I3三项证据均已有。'),
 '00039':('具名支持机会撤回','当前规定触发条件将终止同一程序；同版工作要求明确终止后不再优先沟通。是实质撤回规范，不是纯冒号结构。'),
 '00040':('创新资格的限制及支持撤回','当前临床优势证据不足与直接终止父谓词组合，限定同版创新/改良程序资格并取消沟通优先；不能只当普通效果背景。'),
 '00041':('对同一研发支持的限制','安全原因导致试验结束，经同一终止父句撤回程序及沟通优先。I不是由创新对象把一般安全义务升级，而是当前资格/机会后果。'),
 '00042':('同一支持的兜底撤回','当前兜底与实质终止父句连接，同版终止后取消沟通优先。可记录支持限制，不补造其他原因的具体创新属性。'),
 '00052':('实际临床优势证据要求','当前说明符合程序情形的无有效治疗或比较临床优势证据，连到创新/改良申请资格；I1/I4成立，该申请人义务自身不能改称已实施I3服务。'),
 '00068':('同阶段申报前技术沟通','当前对拟申请优先审评者开放一并进行技术沟通；优先程序同版申报前机制具体协商技术、检验和核查问题，对象范围含创新/改良分支。依据申报前机制，不借纳入后服务。'),
 '00071':('同一实质优先机会并行申请','当前允许一并申请优先审评，是对同版混合对象中创新/改良研发分支可用的实际加快/资源机会。并行申请不证明已纳入或所有对象创新。'),
 '00089':('儿童适宜形式的实质改良资格','当前儿童新品种/剂型/规格在直接父谓词下决定优先申请；同版同一编号范围限定新剂型/规格须现有均不适用且新形式适用。至少该实质改良分支成立I2；新品种词本身不构成创新。'),
}
F={
 '00020':('无有效治疗分支的按需申请','申请机会本身已开放且要求评估同一范围/条件，完整标准含无有效防治手段并由该药提供有效手段的分支，连接同版研发优先资源。不能推广到只有比较优势的分支。'),
 '00026':('纳入授予按需优先资源','无异议即纳入授予同一纳入后的优先沟通资源，完整对象中的无有效治疗分支限定所需治疗缺口。不是因公示5日或通知猜公平。'),
 '00028':('缺口分支与当前优先服务','当前明确优先配置沟通资源，同一对象/阶段存在无有效治疗分支；三项F关系闭合。'),
 '00030':('被按需优先处理的同一服务','当前列出的关键会议/技术咨询就是前项优先资源的研制指导机制，明确优先处理，同一缺口分支可使用。'),
 '00034':('保留缺口分支的同一反馈机会','不是从延期期限猜优先；当前保留的后续关键阶段会议已由同版研制指导明确列为优先处理，缺口对象来自同一程序分支。'),
 '00035':('实施已限定的优先研究反馈','当前实际安排关键阶段研究反馈，与同版该类会议优先处理及无有效治疗分支直接相连。不能以申报前沟通替代此纳入后服务。'),
 '00039':('一般终止规范限制按需机会','同一程序完整范围含无有效治疗分支，当前一般规范终止其优先技术支持；具体终止原因不需要被解释成公平障碍。'),
 '00040':('特定比较优势成员与缺口分支关系待定','支持LLM：直接父句撤回同一程序及优先资源，完整程序确有缺口分支。支持规则：当前只就比现有治疗的优势不足规定终止，不能把另一无有效治疗分支反向赋给本成员；该特定成员与缺口对象的实际重合不能从一般程序名保证。需统一有限消费范围，不能默认所有成员都F1。'),
 '00041':('安全触发撤回同一按需支持','安全问题本身不是获取差异；但对原无有效治疗分支的项目，当前通过终止父句限制同一优先技术资源。条件可适用该分支且不补造所有患者治疗被撤回。'),
 '00042':('兜底限制同一已核明的优先资源','当前与父句撤回同一程序，缺口—优先资源关系可由完整同版机制限定到无有效治疗分支；不推定兜底原因是什么。'),
 '00052':('缺口资格的实质证据要求','当前明确要求阐述尚无有效防治手段及其临床证据，并用于申请同一优先支持机会；不是泛称临床价值或表格字段。比较优势分支不能继承缺口。'),
 '00071':('明确优先机会的并行申请','当前允许申请的是同版实质优先安排，完整范围中有供药不足/无有效治疗等分支；可按该分支记录，不把所有附条件批准药品称为短缺。'),
 '00089':('儿童新品种的无有效治疗分支','同版完全对应本儿童范围的新品种条件有无有效治疗分支，并通过当前父句决定优先申请。市场短缺此外条款不应用来统称所有儿童新品种/规格均短缺；即使不用此外条款，所限定无有效治疗分支已有依据。'),
 '00091':('程序资格到另一优先机会','纳入突破性程序的身份在当前直接父句中被设为优先申请条件，是身份—待遇关系。完整同版突破性范围存在无有效治疗分支，不是只报告已纳入历史状态。'),
 '00093':('明确对应六项的产品取得缺口','同版第5项明文指定该临床急需境外上市/境内未上市产品可按范围(六)申请优先；对应关系可核明。更支持F阳性，但原LLM境内无获批选项表述须缩为该所需产品通常上市取得缺口，不推断全部适应症治疗无获批药。'),
 '00095':('操作性临床优势标准援引','当前以完整具名临床优势标准决定优先申请资格，标准一个分支明确无有效治疗且候选药提供有效手段；与实质优先资源相连。其它比较优势分支不得照搬缺口。'),
 '00103':('儿童无有效治疗的直接资格','当前第一或分支直接表达儿童严重疾病无有效治疗选项，并在同版直接父条件下决定优先机会；第二有优势分支不被记为缺口。'),
 '00105':('适宜规格缺口与便利排除的边界','支持LLM：已有儿童适应症且全部已上市规格不适用，新规格适用，并以此提供优先申请，可能构成该所需规格的合理治疗机会缺口。支持规则：这可能仍只是给药/规格适宜性改良，手册明确仅给药便利不足；没有说明不适用的实际取得/治疗障碍。两种读法不能凭儿童/新规格词解决，保留待定。'),
 '00106':('市场供药缺口与优先审评直接连接','当前明文市场短缺，直接实行优先审评；F具体关系已自足。不能只接受药品短缺的固定词序而漏掉市场短缺这一实际供药缺口。'),
 '00114':('具体申请情形与支持证据','当前要求提交具名附1支持资料，附1实质要求详细说明优先情形/适用条件及依据，含按供药缺口配置机会的分支。依据确指内容要求，不是把所有网站提交或任意附件都展开为F。'),
}
results=[];quote_checks=[]
for d,mapping in [('I',I),('F',F)]:
 for sid,(pattern,reason) in mapping.items():
  r=byid['RECODE25-'+sid];md=next(x for x in r['machine_disagreements'] if x['dimension']==d)
  for i,e in enumerate(md['native_decision']['evidence']):
   if 'pointer' in e:
    text=ptr(r,e['pointer']);exact=isinstance(text,str) and bool(e['quote']) and e['quote'] in text
   else:
    text=full;exact=e.get('asset_sha256')=='980acf76a2fb9b9537e89e6c223462549e984b39e6b1d9a54443e2dadce37036' and e['quote'] in text
   assert exact,(sid,d,i)
   quote_checks.append({'id':r['id'],'dimension':d,'evidence_index':i,'exact':True,'pointer':e.get('pointer'),'asset_checked_against_same_policy_text_already_in_packet':not 'pointer' in e})
  relevant=['finite_named_action','member_no_sibling']+(['I_clinical_link','I_support','I_improvement','postadmission_scope','I_mixed'] if d=='I' else ['F_gap_allocation','F_branch','F_same_priority','F_admin','F_convenience_excluded'])
  results.append({'id':r['id'],'dimension':d,'machine_values':{'rules_v7':md['rule'],'native_original_whole_batch':md['native']},'review_class':'边界待定' if (d=='F' and sid in ['00040','00105']) else '更支持LLM','error_or_boundary_pattern':pattern,'reason':reason,'current_direct_material':{'packet':r['packet'],'pointer':'/source_bundle/source_record/text','quote':r['source_bundle']['source_record']['text']},'native_material_evidence':md['native_decision']['evidence'],'frozen_manual_evidence':[anchors[k] for k in relevant],'scope':'first20 of frozen readable dimension set, not full population or new human judgment','machine_labels_modified':False})
assert len(results)==40
write('semantic-reviews40.json',results);write('native-quote-checks.json',{'evidence_N':len(quote_checks),'exact_N':len(quote_checks),'checks':quote_checks,'exact_quote_not_semantic_truth':True})
write('summary.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'review_N':40,'unique_source_id_N':27,'by_dimension':{'I':20,'F':20},'classification_counts':dict(collections.Counter(r['review_class'] for r in results)),'all_selected_direction':'rule0/native1 due source-ordered one-sided selection; not prevalence or correctness estimate','same_policy_concentration':True,'remaining90_not_reviewed_in_this_phase':True,'classification_runs':0,'model_calls':0,'machine_labels_or_frozen_inputs_changed':False,'manual_binding':bind(MANUAL),'parent_selection_freeze':bind(P/'readable-disagreement-selection-freeze.json'),'selected_input_snapshot':bind(P/'selected-semantic-inputs.jsonl'),'formal_validation_complete':False,'new_human_review':False})
write('seal.json',{'files':[bind(q) for q in sorted(OUT.iterdir()) if q.is_file()],'self_excluded':True,'parent_frozen_selection_unchanged':True})
print(json.dumps({'phase01_N':40,'class_counts':dict(collections.Counter(r['review_class'] for r in results)),'quote_N':len(quote_checks),'seal':bind(OUT/'seal.json')},ensure_ascii=False))
