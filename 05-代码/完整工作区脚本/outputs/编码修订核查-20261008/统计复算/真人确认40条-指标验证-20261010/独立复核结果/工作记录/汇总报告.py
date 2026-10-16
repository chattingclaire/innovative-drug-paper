from pathlib import Path
import json, html, hashlib, datetime

OUT = Path(__file__).resolve().parents[1]
PACK = OUT.parent / '差异项复核包-20261010'
initial = json.loads((OUT/'01-独立初判-对照前.json').read_text())
answers = {(x['material_id'], x['dimension']): x for x in json.loads((PACK/'再核建议与差异定位.json').read_text())}
raw = {(x['material_id'], x['dimension']): x for x in json.loads((PACK/'追溯记录/原始机器记录与语境.json').read_text())}

# 语境编号与对照前保存文件一致；这是使用范围，不是删除未使用语境。
used = {'02/I':[2,3], '03/I':[4], '05/I':[1,2], '06/F':[], '07/Ec':[1,2], '08/F':[], '12/Ec':[], '17/F':[], '20/F':[], '21/F':[4,5], '22/I':[1], '22/F':[1], '23/I':[3,5,6,7], '24/I':[], '25/F':[], '26/I':[], '28/E':[1,2,3], '31/F':[], '32/E':[], '34/Ec':[], '36/I':[], '36/F':[4,5], '38/F':[], '39/I':[]}
causes = {
'02/I':('手册口径细化；LLM关系解释差异','当前手册明确分类决定制度资格可纳入。规则已判1；LLM所需适用范围与沟通审评片段早已存在，不能说缺少关键语境。'),
'03/I':('手册口径变化为主；既有语法过窄','新版I2明确纳入针对操作障碍的拟用设计。旧输入已含手指灵活性、剂量调整及掰片数据的决定性同段，新增标题不是漏判主因。'),
'05/I':('分类制度使用口径变化；表格识别过严','表格完整内容列不满足固定名称fullmatch。旧机器已含表头单元格、同列索引、完整内容及6年；不能把逐字整行未命中解释为缺表头或表格解析失败。'),
'06/F':('明确关系实现缺陷；本复核初判亦需修正','代码将单个产品境内未上市直接标成实际保障缺口；药品对象锚点还抓到机关名称中的“药品”。原句不证明境内无对应治疗选项。'),
'07/Ec':('明确实现排除过宽','申请调整医保支付范围被_APPLICATION_PROCESS拦截；局部最小对照去掉申请语气即可匹配，显示没有按申请内容区分经济安排和手续。'),
'08/F':('手册新增概括公平路径；实现迁移未覆盖','旧具体公平关系门槛不涵盖新版概括评价。旧F证据被重判删除后无新入口；不能把跨手册差异全部算旧定义下的实现错误。'),
'12/Ec':('LLM把程序当内容；规则本项正确','原图只有价格协商阶段、成败及目录去向。最终经济检测为空与手册相符，应保留作价格词出现但Ec0的反例。'),
'17/F':('明确关系实现门槛过宽','无需任何标题或上下文，当前句局部模板即把需求评估指导用药遴选判F。确切归因是本句普通管理被当公平关系，不是已证实的标题继承。'),
'20/F':('手册新增概括公平路径；实现迁移未覆盖','与08采用同一门槛。关键评价关系在当前句，新增章节或导向背景不是成立所需材料。'),
'21/F':('解释边界待裁定','未命中模板不等于漏判。原建议虽标待裁，规则家族仍先称“覆盖不足”“保障排序”，应改为待明确的规范性优先解释。'),
'22/I':('实现漏识别为主；新版作进一步明确','旧手册共同门槛第13行已允许提供某维实质内容及证据；当前创新信息要求不宜与新增公平路径一概归为手册变化。原I属性信息证据被清除，后续语法未补回。'),
'22/F':('手册新增概括公平信息路径；实现迁移未覆盖','新版F明确公平实质信息可纳入，不必另造具体障碍。原F信息证据被删且最终缺对应入口；关键申报内容语境原已存在。'),
'23/I':('手册新增具名计划路径；关键输入实质不同','2024同一试点的1类创新对象、30工作日机制不在旧machine_shared_input中。现有I1正确依赖补材，LLM旧输出虽为1不证明已读取或核实该机制。规则侧源码可访问源库不等于有实际消费证据。'),
'24/I':('明确实现覆盖退步及语法缺陷','上游rules_semantic_v36已识别，后置共同重判清除I证据而更窄检测器未补回。“起草”、标题中的“(试行)”、非紧邻的“提供指导”均可令模板漏匹配。只加起草一词不够；应统一责任模块并检查迁移覆盖。'),
'25/F':('明确关系实现缺陷；本复核初判亦需修正','与06同一产品层次与治疗选项层次混淆；当前确有申请机会，但缺口证据不能由该药未上市推成。'),
'26/I':('手册明确分类制度使用；旧分类排除需迁移','旧V33分类序号须附定义的门槛及旧支付对象排除影响此项。新手册允许当期法定分类决定差异续约权利，须区分药种和时期；不是I3。'),
'28/E':('解释边界待裁定','E基础定义未改变，关键药研语境旧输入已有。无法治愈可能表达治疗结果未达，也可能按严格药物对象规则视为一般治疗背景；不是补一个裸关键词即可认定的实现缺陷。'),
'31/F':('手册明确上游机会口径；关系类别未覆盖','无有效防治手段与突破性申请机会在F缺口、动作词族都缺失；相关组合仅发I。不能只称语序问题；只由无有效手段分支支持F。'),
'32/E':('明确实现覆盖不足','当前已将药物产品开发连接整体健康收益；原档药物对象已识别，但效果、存活和无选项规则都为空。不是缺上下文。'),
'34/Ec':('明确排除过宽且正向入口缺失','旧economic_data_cutoff_date_only排除命中；然而最终Ec重建器在不调用该排除器时仍返回空。须同时修经济证据选取/时效关系，单删排除不保证补回。'),
'36/I':('明确实现覆盖退步及词序、断句限制','上游rules_semantic_v36已识别，后置共同重判删除，替代检测器未补回。当前创新程度高作为遴选条件，属性前置、药品对象后置且跨逗号令窄语法漏判；不能用目录标题代替属性证据。'),
'36/F':('解释边界待裁定','基本目录之外并不直接等于患者保障缺口，商保推荐目录并非保险支付。原语境已有总体定位与完整分点，不应说缺少关键语境，或继承并列第四点的可及措施。'),
'38/F':('明确实现缺口词形、关系模板及额外门槛问题','市场短缺与儿童药品分隔，且现规则额外要求临床急需或固定连续短缺药品词形；当前缺口与优先安排完整。不是一般缺语境，也不止语序。'),
'39/I':('LLM把立规目的当实际支持；规则本项正确','只读当前与共同必要语境，不能展开整份优先程序。单纯鼓励创制目的不构成创新支持机制，与23有统一提供的同一计划机制不同。')}

controls = {
'02/I':'儿童身份或新获批身份单独不足；明确法定创新分类决定差异资格才纳入。',
'03/I':'孤立换剂型/规格、一般优化建议不纳入；必须保留使用障碍与拟用改变的直接关系，不自动增加F。',
'05/I':'仅数字1类、一般保护期或缺列关系不纳入；不能把化学药分类套给中药、生物制品。',
'06/F':'单药未上市+优先机会仍0；无有效选项/无境内获批对应选项/现实短缺+针对性机会可1。F其他路径不强求无替代药。',
'07/Ec':'申请改变医保支付范围为实质内容；普通申报资格、递交材料、目录结果本身为0。',
'08/F':'药品公平性评价为1；公平性栏目、企业公平竞争、上传格式为0，不继承给子项。',
'12/Ec':'仅协商流程为0；明确报价、支付标准核验或费用承担要求才可1。',
'17/F':'基层身份+普通需求调查仍0；明确药品品种限制导致治疗中断并按需纠正可1。不能一律排除基层措施。',
'20/F':'与08同一规则；不同来源位置分别保留，但开发/检验拆分应按文件族避免近重复泄漏。',
'21/F':'单独基金安全/保基本不纳入；如允许定性基本需要优先，须明确需要层次与配置取舍的可识别语义，不能只匹配隐喻。',
'22/I':'申报内容要求创新性实质信息可1；仅创新性字段非空、页码、签章或上传要求为0。',
'22/F':'明确公平信息内容要求可1；仅栏目、空字段或格式要求为0；不据此断言具体公平障碍。',
'23/I':'同计划的启动、实施、限制、撤回均记录议题；仅计划名/宣传目的或无机制时不能猜1。',
'24/I':'专门提供创新研发指导可1；创新药指南内一般安全义务、标题、沟通形式不自动I。不要要求固定主语或提供二字。',
'25/F':'与06一致；允许申请与已经优先应区分，但二者都不能替代缺口条件。',
'26/I':'法定创新分类决定差异续约可1；泛称创新药支付对象或无创新含义的注册序号仍0。保留“可申请”“可不一定高于”的条件性。',
'28/E':'有治愈/疾病控制/生存结果缺口且直接对应药研目标可倾向1；单说严重、急需或未满足需求为0；不能将不能治愈写成无有效药。',
'31/F':'仅临床优势+突破性程序不自动F；尚无有效手段分支才支持本项，保留且/或者结构。',
'32/E':'药物开发—健康收益目标可1；仅体验偏好/给药便利或非药物运动改善健康不自动E。',
'34/Ec':'价格费用采用某日最新数值可1；资料于某日前递交、日期格式正确、批件时间本身为0。',
'36/I':'创新程度高作为药品遴选条件可1；只有商保创新药目录名称、企业管理创新不纳入。',
'36/F':'推荐目录不等于保险待遇；若要纳入补充机会须有明确需要/障碍与措施联系，且与普通保障名单排除一致。',
'38/F':'市场短缺+同对象优先可1；短缺仅在文件名或另一药物上、只有儿童群体或新剂型仍不足。',
'39/I':'立规宗旨不纳入；明确当前创新研发支持安排或同计划机制闭合可纳入，不按制定/开展动词分正负。'}

iaudit=json.loads((OUT/'独立代码核查-I.json').read_text())
eaudit=json.loads((OUT/'独立代码核查-E-Ec.json').read_text())
faudit=json.loads((OUT/'独立代码核查-F.json').read_text())
code_by_key={}
for item in iaudit['per_item']+eaudit['entries']:
    code_by_key[item['material_id']+'/'+item['dimension']]=item
f_groups=[['06','25'],['17'],['08','20','22'],['31','38'],['21','36']]
for group,finding in zip(f_groups,faudit['findings']):
    for num in group:code_by_key['校准'+num+'/F']=finding

rows=[]
for old in initial['rows']:
    row=dict(old); key=(row['material_id'],row['dimension']); short=row['material_id'][-2:]+'/'+row['dimension']; a=answers[key]; m=raw[key]
    final=0 if short in ['06/F','25/F'] else row['independent_initial']
    status='建议保留'
    reason=row['initial_rationale']
    if short in ['06/F','25/F']:
        reason='当前确实将临床急需、该产品境内未上市与优先审评机会相连，但仅有产品上市状态，未说明境内无获批的对应治疗选项、现实短缺或其他患者获取障碍。手册排除仅急需/未上市；因此保留F0。初判1将产品缺位扩大为治疗选项缺口，对照后依据该层次区分修正，不以机器或人工票数决定。'
    if short in ['21/F','36/F']: status='建议由1调为0；待真人裁定'
    if short=='28/E': status='倾向保留1；待真人明确对象边界'
    row.update({'human_reference_unchanged':a['reference'],'legacy_rule':a['rule'],'legacy_llm':a['llm'],'existing_recommendation':a['review']['recommended_label'],'existing_review_status':a['review']['decision'],'after_comparison':final,'review_status':status,'final_rationale':reason,'used_context_indices_1based':used[short], 'used_contexts':[{'text':row['contexts'][i-1],**row['context_descriptors'][i-1]} for i in used[short]],'cause_type':causes[short][0],'cause_review':causes[short][1],'suggestion_and_negative_control':controls[short],'machine_context_comparison':m['context_comparison'],'context_check_limit':'逐字片段比较不等于语义内容有无；另检查结构化表头及决定性片段。','human_new_adjudication':None})
    row['independent_code_audit']=code_by_key.get(row['material_id']+'/'+row['dimension'],{'note':'本项仅LLM与参照不同，规则为1；不将LLM解释差异冒称源代码缺陷。'})
    rows.append(row)

result={'scope':'22条材料的24个指定维度；未重新裁定全40条五维','date':'2026-10-10','procedure':'先只读共用手册与无答案材料并保存24项初判；其后对照答案、原机器输入与实际代码；分工复核者同样先盲读。','initial_file':'01-独立初判-对照前.json','manual_sha256':initial['manual_sha256'],'old_machine_manual_sha256':'24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9','summary':{'stable_keep':21,'recommend_change_pending_human':2,'lean_keep_pending_boundary':1,'self_corrected_blind_labels':['校准06/F:1→0','校准25/F:1→0']},'limitations':'有目的选取的开发校准，且新旧手册与输入不同。本次不改参照、不修代码、不报告修后分数；不能称独立总体效度验证。','rows':rows}
(OUT/'03-逐项对照后结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))

conclusion='''本轮独立复核结论（2026年10月10日）

已完成22条材料、24个指定维度的复核。21项建议保留现结论；校准21/F、36/F建议由1调为0，但须由真人统一边界后裁定；校准28/E倾向保留1，也须明确药物效果对象的承接门槛。原参照、人工填写位置、机器输出和源代码均保留。

三个重点边界

21/F：我倾向0。“保基本＋雪中送炭/锦上添花”表达优先取向，但未明确是哪一种患者需要差别、获取障碍或保障缺口。不能补成贫困救助或无药可用。如果真人认为这种定性基本需要优先原则已足够，应在手册中统一写明它与普通需求口号的区别。

36/F：我倾向0。基本目录未纳入说明制度边界，并不直接证明患者得不到所需药物；商保目录是推荐参考，不等于保险支付或按需补偿。当前是“一是遴选范围”，不能继承并列“四是支持可及”的措施。若拟把这种遴选机会也纳入F，须说明与普通保障名单、一般申报资格及17/F的区别。

28/E：我倾向保留1。当前已陈述“无法治愈”这一具体治疗结果不足，且直接用于患者需求与药物研发立题关系。它不只是“疾病严重”，但也绝不等于“没有有效药物”。真人应明确：这种直接研发目标语境能否补足药物对象；若采用更严格门槛，须在所有相同关系中一致适用。

两个重要的自我修正

06/F、25/F在我的盲读初判中均为1，对照后修为0。初判把“这个药境内未上市”扩大成“境内没有对应治疗选项”。当前材料不足以作后一个判断。这个修正依据原文与手册的层次区分，不能因为LLM与另一种机器同判1就保留1。也不能反过来要求所有F都必须无替代药；患者可负担、现实短缺及人群获取差异另有各自路径。

原文与引文

复核表24项标签与建议JSON一致；22条当前全文及语境内容均能还原，完全重复当前句的语境副本省略不造成缺失；关键摘引均能逐字对应材料。另核看05原图、12流程图及21、28、36原PDF页，未发现会改变本轮判断的漏句或错列。解释上须保留31的“或者”分支、26的条件性、05表名属于结构记录，以及36各并列项的界限。03关键掰片障碍语境和05表头结构原机器已有，不能把呈现变化说成关键材料缺失；23的2024试点机制则确是旧共享输入之外的实质补材。

规则与方法应怎样改

1. 先确定手册版本和共同输入。把概括公平评价/信息要求、针对操作障碍的拟用设计、分类制度使用、具名计划和上游机会配置的口径变化分别登记。21/F、28/E、36/F先裁边界，不先补正例。22/I旧共同门槛已经支持实质信息要求，不能全部归为手册新增。

2. 公平关系分路径实现。评价/实质信息要求单列；具体关系分别记录无有效选项、境内无获批对应选项、现实供应不足、支付能力或人群机会障碍。缺口用于按需配置路径时，绑定同一对象的申请、优先或保障安排；患者能否负担及不合理获取差异的实质讨论或评价本身也可成立，不额外要求另有干预措施。06/25不要用单药未上市充当缺口，且对象锚点不得抓监管机关名中的“药品”。17的需求评估—遴选只作候选。31保留无有效手段分支；38补市场短缺及分隔表达，不硬要求“临床急需”四字。

3. 创新关系按属性、改良、研发支持、资格分别留据。24、36/I上游已经识别，却被后置共同重判删除，须先解决多阶段覆盖退步，不能只补词。05修表格列关系和过严fullmatch；26按药种、时期核实分类条件；24按创新对象、专门指南供给及研发用途判断，标题“(试行)”和词距也会阻断；36/I允许前置属性和后置药品对象。03仍须障碍—改变—使用改善，23须同一计划机制，避免把一般设计建议或立规宗旨算成研发支持。

4. 经济和有效性修具体关系。07区分申请改变支付范围与纯递交手续。34既要收紧日期排除，也要新增经济证据选取/时效的正向关系，单删排除器不能保证恢复。32补药物产品开发—健康收益目标。12价格协商流程继续作0反例；28不新增裸“无法治愈”关键词。

5. 验证按完整流水线和关系反例进行。局部函数复现已证实上述代码行为，但不代表修复后最终标签。修改后检查新增和删除的证据、否定/条件/或分支、表格与正文同义表达、上下文保留和移除对照，再检查全量候选及未参与开发的文件族。不得按材料编号、部门或目标一致率触发，也不得用这40条修后指标宣称独立总体效度。

逐项完整原文、初判、对照后判断、实际使用语境、原因及反例见“逐项复核报告.html”和“03-逐项对照后结果.json”。代码位置、局部复现和合成反例见三份“独立代码核查”记录。真人新裁定未代填。
'''
(OUT/'复核结论.txt').write_text(conclusion)

e=html.escape
blocks=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>创新药政策编码独立复核</title><style>body{margin:0 auto;max-width:1080px;padding:38px 24px;color:#233044;background:#f6f7f9;font:16px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}h1{font-size:28px}h2{font-size:21px;margin-top:0}h3{font-size:17px}section{background:white;padding:24px;margin:24px 0;border:1px solid #dce1e7;border-radius:8px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid #dce1e7;padding:9px;text-align:left;vertical-align:top}th{background:#e9eef5}blockquote{margin:10px 0;padding:12px 18px;background:#f5f7fa;border-left:3px solid #8498ad;white-space:pre-wrap}p{margin:9px 0}a{color:#185d93}details{margin-top:16px}summary{cursor:pointer;color:#185d93}.meta{font-size:13px;color:#596779}.pending{border-left:5px solid #b7751d}.zero{color:#505c6b}@media print{body{max-width:none;background:white;font-size:11pt}section{break-inside:avoid}details{display:block}}</style><h1>创新药政策编码独立复核</h1><p>2026年10月10日 · 22条材料 / 24个指定维度</p><p><strong>21项建议保留，2项建议调整后交真人裁定，1项倾向保留并明确边界。</strong>每项的0/1为本次独立建议；现人工参照单列保留。</p><p class="meta">先盲读并保存初判，再对照现有结论、机器原始输入及实际代码。旧机器使用较早手册，本批为有目的开发校准，不作独立总体效度验证。未修改原表、参照、机器输出或源代码。</p>']
blocks.append('<section><h2>逐项总览</h2><table><thead><tr><th>材料/维度</th><th>原参照</th><th>旧规则</th><th>旧LLM</th><th>独立初判</th><th>对照后</th><th>处理建议</th></tr></thead><tbody>')
for r in rows:
    k=r['material_id']+'/'+r['dimension']; ident=r['material_id']+'-'+r['dimension']
    blocks.append('<tr>'+''.join('<td>'+v+'</td>' for v in [f'<a href="#{ident}">{e(k)}</a>',str(r['human_reference_unchanged']),str(r['legacy_rule']),str(r['legacy_llm']),str(r['independent_initial']),str(r['after_comparison']),e(r['review_status'])])+'</tr>')
blocks.append('</tbody></table></section><section><h2>结论与修改次序</h2>')
for para in conclusion.split('\n\n')[1:-1]:blocks.append('<p>'+e(para).replace('\n','<br>')+'</p>')
blocks.append('</section>')
for r in rows:
    ident=r['material_id']+'-'+r['dimension']; c='pending' if '待真人' in r['review_status'] else ''
    blocks.append(f'<section class="{c}" id="{ident}"><h2>{e(r["material_id"]+" / "+r["dimension"])}　{r["after_comparison"]} · {e(r["review_status"])}</h2>')
    blocks.append('<p class="meta">原参照 '+str(r['human_reference_unchanged'])+'；原再核建议 '+str(r['existing_recommendation'])+'（'+e(r['existing_review_status'])+'）；独立初判 '+str(r['independent_initial'])+'；对照后 '+str(r['after_comparison'])+'。真人新裁定：未填写。</p>')
    blocks.append('<h3>完整当前单元</h3><blockquote>'+e(r['current_text'])+'</blockquote><p class="meta">'+e(r['source_name']+'；'+r['source_locator']+'；PDF页 '+str(r['pages']))+'</p>')
    blocks.append('<h3>独立初判与对照后判断</h3><p><b>初判：</b>'+e(r['initial_rationale'])+'</p><p><b>对照后：</b>'+e(r['final_rationale'])+'</p><p><b>边界：</b>'+e(r['initial_boundary'])+'</p>')
    blocks.append('<h3>实际使用的语境</h3>')
    if r['used_contexts']:
        for cxt in r['used_contexts']:blocks.append('<blockquote>'+e(cxt['text'])+'</blockquote><p class="meta">'+e(cxt.get('source_name','')+'；'+cxt.get('source_locator',''))+'</p>')
    else:blocks.append('<p>当前单元足以支持本维判断。已完整阅读全部共同语境，未将相邻自足命题或栏目标签继承到当前。</p>')
    blocks.append('<h3>归因核查及修改约束</h3><p><b>'+e(r['cause_type'])+'</b>：'+e(r['cause_review'])+'</p><p>'+e(r['suggestion_and_negative_control'])+'</p>')
    audit=r['independent_code_audit']
    locations=audit.get('code_evidence',audit.get('code_locations',[]))
    if locations:
        blocks.append('<details><summary>实际代码位置与核查证据</summary>')
        for loc in locations:
            path=loc.get('path',str(Path(faudit['runtime_path'])/loc.get('file','')))
            start=loc.get('start_line',loc.get('line_start',(loc.get('lines') or [None])[0]))
            end=loc.get('end_line',loc.get('line_end',(loc.get('lines') or [None])[-1]))
            blocks.append('<p class="meta">'+e(Path(path).name)+'：'+str(start)+'—'+str(end)+'行</p>')
            if loc.get('basis'):blocks.append('<p>'+e(loc['basis'])+'</p>')
            if loc.get('code'):blocks.append('<blockquote class="meta">'+e(loc['code'])+'</blockquote>')
        blocks.append('</details>')
    blocks.append('<details><summary>展开全部已读共同语境与来源（包括未用作正向依据的部分）</summary>')
    for i,(txt,desc) in enumerate(zip(r['contexts'],r['context_descriptors']),1):blocks.append('<p class="meta">语境'+str(i)+' · '+e(desc.get('source_name','')+'；'+desc.get('source_locator',''))+'</p><blockquote>'+e(txt)+'</blockquote>')
    blocks.append('</details></section>')
blocks.append('<section><h2>可追溯文件</h2><p>01-独立初判-对照前.json：对照前原判断，未回写。</p><p>02-来源与逐字核查.json：工作簿和JSON核对、关键摘引、原文件摘要。</p><p>03-逐项对照后结果.json：24项完整机器可读结果，真人新裁定均为空。</p><p>独立代码核查-I.json、独立代码核查-F.json、独立代码核查-E-Ec.json：具体文件行号、代码归因及局部复现。合成最小反例只检验机制，不计入真实政策样本。</p></section></html>')
(OUT/'逐项复核报告.html').write_text('\n'.join(blocks))
print('saved',len(rows),'rows; stable',sum(r['review_status']=='建议保留' for r in rows))
