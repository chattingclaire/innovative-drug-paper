from pathlib import Path
from collections import Counter
import json,hashlib,datetime,re,difflib

OUT=Path(__file__).resolve().parent
def read(name):return json.loads((OUT/name).read_text())
manifest=read('source_manifest.json')
S={x['source_id']:x for x in manifest['sources']}
D={sid:read(f'extracts/{sid}.json') for sid in S if S[sid]['source_path'].endswith('.docx')}
P=lambda sid,n:D[sid]['paragraphs'][n-1]['text']
def ev(sid,n,fragment=None,role='primary_record'):
 t=P(sid,n)
 if fragment is None:fragment=t
 assert fragment in t,(sid,n,fragment)
 return {'source_id':sid,'source_sha256':S[sid]['sha256'],'paragraph_1based':n,'locator':f'{sid}:P{n:03d}','fragment':fragment,'fragment_exact_match':True,'evidence_role':role}
claims=[]
def row(cid,paragraphs,claim,status,evidence,judgement,boundary,action,**kw):
 claims.append({'claim_id':cid,'manuscript_paragraphs_1based':paragraphs,'manuscript_paragraph_texts':[{ 'paragraph_1based':n,'text':P('M00',n)} for n in paragraphs],'audited_claim':claim,'support_status':status,'source_evidence':evidence,'judgement':judgement,'not_supported_by_these_records':boundary,'handoff_action':action,'manuscript_edited':False,**kw})
row('C01',[11],'一类新药注册认定不自动满足医保临床价值评审要求','supported_as_recorded_expert_view',[
 ev('I02',6,'药监局可能认定某个药品为一类新药，代表其在创新性上达到了很高的标准，但这并不意味着该药品能够达到医保所要求的临床价值。'),
 ev('I01',7,'如果专家认为产品的临床价值不高，缺乏创新性，未能满足健康需求，与已有药物差异不大，就不会给予高分。'),ev('R01',896,role='duplicate_appendix_not_independent')],
 '两份纪要均记录注册与医保比较价值的区别；当前转述有原段支持。','不据此证明具体药品被拒绝、总体拒绝率或药监只看新颖性。','可保留访谈观点归属；正式评价要求仍以对应政策原文为准。')
row('C02',[11],'纳入医保后，医疗机构实际使用仍可能遇到障碍','supported_as_recorded_expert_view',[
 ev('I01',15,'现在的问题是药监批了，医保不一定进，医保进了，医院不一定用。'),ev('I01',17,'即使创新药进了医保，在医院端使用时，医生的态度是：第一，我不了解这个新药；'),ev('W03M',13),ev('W02S',75),ev('R01',861,role='duplicate_appendix_not_independent')],
 '专家纪要和企业会议材料均提出支付准入与院端使用衔接问题。','没有测量医院配备率、用药障碍发生比例，也未证明所有药品或医院均如此。','采用可能性和具体问题表述；不升级为普遍效果或因果估计。')
row('C03',[63],'当前稿所称3场研讨会材料具有实际来源','supported_with_event_binding',[
 ev('W01',2),ev('W01',4),ev('W02T',2),ev('W02T',5),ev('W03A',5),ev('W03A',11),ev('W03M',1),ev('W03M',4),ev('W03M',13)],
 '旧版A06明确绑定2月12日、3月19日、5月14日三场；本次原件核查与之吻合。2月为企业会议纪要，3月为专家咨询会转录及整理稿，5月为议程及纪要。3场是所采用会议事件数，非全部资料数量。','议程不能单独证明实际出席或发言；不能把同场转录、整理稿、议程和纪要各算一场，亦不能把开题名单算访谈样本。','交接时按三个事件分别列材料类型；5月议程只证计划，内容采用W03M纪要。',event_ids=['EV01','EV02','EV03'])
row('C04',[63],'当前稿使用史录文访谈纪要和医保调研纪要','supported_as_two_records',[
 ev('I01',1),ev('I01',2),ev('I02',1),ev('R01',32,'并在专家会研讨会、专家一对一访谈的基础上'),ev('R01',847),ev('R01',848),ev('R01',891)],
 '两份独立保存的主题纪要及研究报告附件均存在；实际访谈资料已接收，不能继续归为没有访谈资料。','两份记录数量不等于已核实两人、两人次或全部研究访谈样本；报告附件重复收录不增加独立来源数。','以两份专家纪要描述采用范围，实际参与者总数不补造。')
row('C05',[64],'围绕判断对象、证据要求、结果用途和跨环节问题整理材料','supported_for_explanatory_organization',[
 ev('I01',6),ev('I01',8),ev('I01',15),ev('I02',3),ev('I02',6),ev('W03M',4),ev('W03M',13)],
 '原段包含比较对象、证据与参照、经济测算用途、进院问题，足以进入当前四类解释框架；A07也保存旧版论证定位。','原件不记录按当前框架开展访谈的统一提纲，也不证明正式定性编码、主题饱和、两人独立编码或交叉核对程序。','把该框架作为作者对既有资料的解释整理；不得写成受访时统一提纲或已完成正式定性验证。')
row('C06',[83],'医保调研纪要列安全性、有效性和经济性为综合评审核心内容','supported_as_minutes_wording',[
 ev('I02',4,'评分体系有具体的分值标准，主要围绕安全性、有效性和经济性三个核心维度。'),ev('R01',894,role='duplicate_appendix_not_independent'),ev('I01',5,'综合组要去判定相关产品在临床方向的相关维度，包括安全性、有效性、创新性、公平性、适宜性（包括好不好储存、运输有没有问题、使用方便性等）、经济性这六个维度。')],
 'I02原字支持三个核心维度的纪要表述；I01另记六维，W03M还记企业理解的四象限。当前句已注明医保调研纪要，归属清楚。','三种记录不能拼成同一正式维度体系或精确权重，也不能用来替代本文政策文本五维定义；访谈不是条件比例数值的来源。','保留纪要归属及各自语境；原政策维度和权重另核正式文件。')
row('C07',[86],'注册创新分类不保证企业预期谈判价格','supported_as_recorded_expert_view',[
 ev('I02',6,'为什么自己的一类新药在医保谈判中却无法获得理想的价格。'),ev('I02',25,'不能仅仅因为获得了1.1类新药的认定，就理所当然地要求获得创新药的价格待遇。'),ev('R01',915,role='duplicate_appendix_not_independent')],
 '当前采用转述而非伪直接引文，符合纪要表达的价格预期区别。','不证明注册分类与谈判价格的定量关系或具体价格规则；纪要中的1.1类称谓不能自动移作现行正式分类定义。','可以保留转述；原记录中的分类称谓作为专家表述处理。')
row('C08',[88],'受访专家强调医保评审从健康需求出发','supported_as_recorded_expert_view',[
 ev('I01',6,'是否真正满足了未被满足的健康需求'),ev('I01',7,'各个维度之间的权重比例系数没有明确的绝对标准，但倾向是从健康需求的角度。'),ev('R01',853,role='duplicate_appendix_not_independent')],
 '健康需求导向有连续原段支持。','不据此给本文注意力占比赋予评审权重意义，也不把专家对药监的概括替代正式注册文件。','保留观点转述，权重与政策文本关注比例分开。')
row('C09',[88],'医保调研纪要讨论临床价值分层与经济评价衔接','supported_as_minutes_wording',[
 ev('I02',3,'将药品分为四个层次：创新、提升、改进和同质。这种分层是评审的第一步，随后进行经济性评价。'),ev('I02',3,'首先是与目录内药品进行成本-疗效的比较分析'),ev('I02',3,'其次是预算影响分析（BIA）'),ev('R01',893,role='duplicate_appendix_not_independent')],
 '分层、成本疗效比较和预算影响分析的顺序明确记载。','不证明四层的正式现行名称、统一分值、具体赋权或谈判价格计算公式。','保留当前纪要讨论的层级，不增写正式制度规则。')
row('C10',[91],'史录文纪要日期为2025年6月9日','supported_as_recorded_date',[
 ev('I01',2,'会议时间：2025年6月9日星期一')],
 '正文会议时间确记6月9日，文件名0605与正文不一致；当前稿按纪要正文日期使用，有依据。','未取得独立日程或录音元数据确认实际举办日期；不能据文件名断言应改为6月5日。','台账标记正文记录日期2025-06-09并保留文件名差异。')
row('C11',[91],'纪要记录的直接话语“医保进了，医院不一定用”','exact_quote_verified_in_minutes',[
 ev('I01',15,'医保进了，医院不一定用'),ev('R01',861,'医保进了，医院不一定用',role='duplicate_appendix_not_independent')],
 '短句是I01:P015完整句中的连续原字；当前用“访谈纪要所记录的”限定引文来源，可以核实。','没有相应音频、该访谈逐字稿或逐句确认记录，不能宣称证明了受访时逐字原话。','若保留引号，维持纪要记载的限定；若写成专家直接说则建议转述或改为纪要记载。',quote_audit={'quote':'医保进了，医院不一定用','minutes_literal_match':True,'spoken_verbatim_verified':False,'current_attribution':'访谈纪要所记录的','current_quote_can_be_retained_as_recorded_text':True,'paraphrase_required_if_attributed_as_spoken_verbatim':True})
row('C12',[63],'药监环节主要依据公开技术文件，会议材料补充跨环节问题','supported_as_declared_evidence_scope',[
 ev('W01',17),ev('W02S',58),ev('W02S',75),ev('W03M',4),ev('W03M',13)],
 '采用会议材料确有价格、支付、医院准入及不同评价关系的内容；当前句没有虚构药监专门访谈。','这些文件不构成对药监官员的系统访谈，也不保证所有会议参与者都代表所在机构正式意见；本轮不重审公开技术文件。','沿用公开技术文件与跨环节解释材料的既有分工。')
row('C13',[2,85,106],'条文与访谈使差异具体对应目录准入、费用负担、供应及临床使用','supported_as_author_synthesis',[
 ev('I02',6),ev('I02',9),ev('I02',10),ev('I01',15),ev('I01',17),ev('W01',23),ev('W03M',13)],
 '原段分别涉及准入比较价值、患者费用保障与医院使用；综合联结属于作者结合政策的解释，当前概括有主题依据。','访谈没有独立估计安全性或经济性比例，也未验证部门逻辑导致这些数量差异；三条具体政策方案及实施效果不是这些原段的直接结论。','保留综合解释身份；数量仍绑定编码，正式安排仍绑定政策，效果不由纪要推导。')
row('C14',[12,13,23,28,40,57],'以条文及访谈解释判断对象、参照、用途和注意力配置','supported_for_explanatory_use',[
 ev('I02',6,'特别是与目录内已有的同一治疗领域、同一适应症药品相比的优势。'),ev('I01',6,'也就是确定参照药。'),ev('I01',8,'去测算这个药跟参照药之间的经济关系。'),ev('W03M',13)],
 '上述段落是在说明访谈的解释用途，具体材料能说明参照选择、比较价值、后续测算和临床使用。','不能由此推断访谈是自动规则或LLM的人工金标准、独立内容效度评分或真实评审赋权。','保持解释材料用途；不与标签信度、效度验收合并。')
row('C15',[88],'史录文受访者被称为高校药事管理领域专家','not_established_from_primary_record_identity_fields',[
 ev('I01',1),ev('I01',2,'访谈对象：史录文教授'),ev('R01',848)],
 '原件确认姓名和教授称谓；高校任职及药事管理领域表述在旧审查A06中出现，但本次原始纪要没有独立身份或任职字段。未据此判为身份错误。','原始两份纪要本身不证明具体高校、当前任职或政府职务；医保纪要未列专家姓名。','内部源台账保留已知姓名；公开匿名稿可用受访专家I01。若需要保留高校领域身份，连接已确认作者记录或官方身份来源。')
row('C16',[64],'引文、日期和来源位置列入配套证据索引，保留不同意见的条件','partially_supported_index_presence',[
 ev('I01',2),ev('I02',1),ev('I02',4),ev('I01',5),ev('W03M',5)],
 'A06与A07有旧版日期、段落及主张绑定；本次以当前稿段号建立新映射。不同维度表述和企业评审体验可原位保留。','旧索引不是当前稿完整程序日志；医保纪要的完整日期不可补造，本次也不验证全部政策回查过程已按当前框架完成。','使用本索引补充当前稿定位，医保日期记未载；保留三核心、六维、四象限各自出处，不宣称完成正式定性编码。')

mention_rows=[]
for x in D['M00']['paragraphs']:
 n=x['paragraph_1based'];t=x['text']
 if n>=114 or not re.search(r'访谈|纪要|研讨|受访',t):continue
 role='external_literature_not_project_interview' if n==20 else ('section_heading' if n==62 else 'project_evidence_mention')
 ids=[r['claim_id'] for r in claims if n in r['manuscript_paragraphs_1based']]
 mention_rows.append({'paragraph_1based':n,'role':role,'text':t,'mapped_claim_ids':ids})
assert all(x['mapped_claim_ids'] for x in mention_rows if x['role']=='project_evidence_mention')

duplicate=[]
for sid in ('I01','I02'):
 pairs=[]
 for x in D[sid]['paragraphs']:
  t=x['text']
  if len(t)<30:continue
  normalized=t.replace('史录文教授','XXX教授').replace('史教授','XXX').replace('史录文','XXX')
  y=max(D['R01']['paragraphs'][846:923],key=lambda y:difflib.SequenceMatcher(None,normalized,y['text'],autojunk=False).ratio())
  similarity=difflib.SequenceMatcher(None,normalized,y['text'],autojunk=False).ratio()
  if similarity>=.95:pairs.append({'source_paragraph_1based':x['paragraph_1based'],'report_paragraph_1based':y['paragraph_1based'],'similarity_after_name_normalization':round(similarity,6),'exact_after_name_normalization':normalized==y['text']})
 duplicate.append({'source_id':sid,'report_source_id':'R01','matching_long_paragraphs':len(pairs),'pairs':pairs,'interpretation':'报告匿名收录同一纪要，不能算另一份独立访谈','method':'正文段落至少30字符，受访者姓名规范为XXX，SequenceMatcher autojunk=False，范围R01:P847—P923，阈值0.95；段落相似度仅辅助重复来源判断，不是研究信度指标'})

catalog=[]
details={
 'I01':('真实访谈的主题纪要记录','P001—P002载访谈对象、记录日期和地点；P004—P040为主题整理及专家观点，P042—P043为纪要总结，不宜全部当作直接讲话。','2025-06-09','正文记载；与文件名0605不一致'),
 'I02':('专家调研的主题纪要记录','P003—P032为整理陈述，完整日期、地点、专家姓名未载；不能把0616单独解读为已验证2025-06-16。',None,'文件名和标题仅有0616'),
 'W01':('企业会议纪要','P002—P004载日期、时长与主题，主体为企业需求与建议；非个人专家访谈逐字稿。','2025-02-12','P002正文记载'),
 'W02T':('专家咨询会的带时间戳转录文本','P002载日期与时长，P005为文字记录，P006—P009为说话人和时间戳；可见转录误识及混杂文字，未核原始音频。','2025-03-19','P002正文记载'),
 'W02S':('同场专家会整理纪要','按发言者归纳建议，与W02T构成同场材料组；其机构标签不自动证明发言代表机构正式立场。','2025-03-19','文件名与A06同场绑定；非独立事件'),
 'W03A':('研讨会计划议程','P005计划时间、P010—P013议程、P015以后计划名单；不能单独认定实际出席、时长或提纲修改已执行。','2025-05-14','P005为计划时间'),
 'W03M':('同场企业研讨会议纪要','P004、P008、P013等有评审、参照及进院内容；日期借助W03A与A06对应，标题0514。','2025-05-14','标题月日、议程及旧绑定共同定位；正文无完整日期字段'),
 'R01':('研究报告作者分析及附件','P032作者说明使用专家会与一对一访谈，P847以后重复收录I01/I02及其他商业保险调研记录；正文分析不等于新增原始访谈。',None,'报告文件名日期不替代访谈日期')}
for sid,(kind,reading,date,datebasis) in details.items():
 catalog.append({'source_id':sid,'filename':Path(S[sid]['source_path']).name,'source_kind_chinese':kind,'date':date,'date_basis':datebasis,'interpretation':reading,'sha256':S[sid]['sha256'],'source_path':S[sid]['source_path'],'snapshot_path':S[sid]['snapshot_path']})
author= json.loads(Path(S['A04']['snapshot_path']).read_text())
authorization={'status':'recorded_author_confirmation_received','source_id':'A04','recorded_at':author['recorded_at'],'user_statement':author['user_statement'],'scope':author['scope'],'basis_type':author['basis_type'],'previous_responsible_author_anonymous_use_question_closed':True,'not_established':author['not_established'],'public_manuscript_note':'现采用稿P063/P091具名；公开稿按已确认的匿名引用范围处理身份与源文件链接。内部审核源台账保留真实文件名，不等于公开传播原报告。','requires_new_confirmation_for_this_read_only_audit':False}
limits=[
 {'item':'访谈总人数、总人次和13名受访者','status':'not_established','reason':'议程为拟参会名单；两份专家纪要为采用记录数，未提供跨会议去重、实际出席和研究总体抽样表。'},
 {'item':'约6.2万字、会议次数按文件数相加','status':'not_established','reason':'三月转录与整理稿、五月议程与纪要及报告附件存在同源重复；当前稿没有该字数断言，不应自行增加。'},
 {'item':'受访者逐一签署同意书及本研究伦理审批','status':'not_established','reason':'负责人同意匿名公开使用已确认；这与逐人签署同意、伦理批件为不同事实。R01:P951讨论患者医疗数据使用伦理要求，不能充作本研究伦理审批完成的凭证。'},
 {'item':'正式定性编码、统一访谈提纲执行、饱和及双人交叉核对','status':'not_established','reason':'有主题纪要、会议转录与旧论证索引，未提供正式定性编码工程或执行程序记录；这不否定真实访谈资料存在。'},
 {'item':'逐字原话与纪要原字','status':'distinguished','reason':'I01/I02为主题纪要；P091短句可核纪要原字。W02T是另一场会议的带时间戳转录，不能为I01受访者逐字讲话作证。'},
 {'item':'医保纪要完整日期、地点、专家姓名','status':'not_established_from_primary_record','reason':'I02仅有标题0616；R01重复收录同样未载完整信息。'},
 {'item':'三部门正式规则、实际权重及执行效果','status':'outside_interview_support','reason':'不同纪要的三核心、六维、四象限保留为不同陈述；正式要求须回到政策原文，数量结果须回到编码数据。'},
 {'item':'研究报告中的其他商保访谈','status':'received_but_not_current_adopted_scope','reason':'R01:P924—P943与P945以后有其他调研纪要，但当前P063及旧会议绑定未将其列作采用材料，不增算专家访谈数或三场会议数。'},
]
audit={'created_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'task':'当前采用稿访谈与研讨证据接收核查','audit_identity':'GPT-6.1 Sol，ultra；原始文档读取和哈希检查，本轮独立子审查核对两份纪要的日期与直接引文；并非真人定性编码','authoritative_manuscript':S['M00'],'source_manifest_path':str(OUT/'source_manifest.json'),'main_document_changed':False,'previous_sealed_outputs_changed':False,'prior_source_script_executed':False,'locator_convention':manifest['source_locator_convention'],'summary':{'primary_expert_records_adopted':2,'adopted_meeting_events':3,'adopted_meeting_record_files':5,'manuscript_project_evidence_mention_paragraphs':sum(x['role']=='project_evidence_mention' for x in mention_rows),'claim_mapping_count':len(claims),'support_status_counts':dict(Counter(x['support_status'] for x in claims)),'interpretation':'数量表示本次采用范围或审查条目，不表示受访者总人数、总人次或定性编码样本量。'},'source_catalog':catalog,'manuscript_mention_coverage':mention_rows,'claim_evidence_mapping':claims,'direct_quote_audit':[claims[10]['quote_audit']|{'claim_id':'C11','manuscript_paragraph_1based':91,'primary_source_id':'I01','source_paragraph_1based':15}],'duplicate_record_analysis':duplicate,'responsible_author_anonymous_use':authorization,'unsupported_or_separate_scope':limits,'reading_extent':{'M00':'当前采用稿全部直接正文段落抽取，访谈相关18段逐条定位；P020为外部文献、P062为标题，其余16段映射','I01_I02':'两份完整主题纪要直接正文读取；独立子审查复核日期、引文和核心主张','W01_W02S_W03A_W03M':'短篇纪要及议程正文读取，关联本稿实际使用主题','W02T':'日期、关键词、文字记录头及跨环节相关时间戳片段定向阅读；不宣称逐字校对全部长转录或音频','R01':'报告用途段、保密标识、附件5两份重复纪要与后续商保调研范围定向读取；不验收报告所有事实','other_04_docx':'7份其他文件只作目录及文本抽取上下文清单，不纳入当前采用会议与专家记录计数'},'handoff_required_before_public_submission':['将公开稿P063/P091具名识别按既有匿名使用范围处理。','医保纪要日期字段保留未载；不得单凭0616补完整日期。','P091若保持引号，限定为纪要记录，不能标为经录音核对的逐字讲话。','正式政策、编码指标验收与访谈解释职责分别绑定；本接收核查不等于方法合规验收。']}
(OUT/'interview-evidence.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))

link=lambda sid:f"[{sid} {Path(S[sid]['source_path']).name}](<{S[sid]['source_path']}>)"
md=['# 当前采用稿访谈与研讨证据核查','',
 '当前稿使用的两份专家纪要和三场会议材料均可连接到原文件。关于注册创新与医保临床价值、谈判价格预期、健康需求及院端使用的核心转述有原段支持。唯一带引号的访谈短句“医保进了，医院不一定用”可在纪要原字中核到；它证明纪要记录，尚不能证明受访时的逐字讲话。本次完成证据接收和映射，未改正文。','',
 f"采用稿：{link('M00')}。SHA256：`{S['M00']['sha256']}`。",'',
 'P为python-docx直接正文段落的一基编号，包含空段；不是页码。当前正文18段含访谈、纪要、研讨或受访词，其中P020是外部文献，P062是标题，其余16段均纳入映射。完整主张、底稿原段、证据片段及哈希见同目录JSON。','',
 '## 实际采用范围','',
 '|记录|性质与时间|原始段落及用途|','|---|---|---|']
for s in catalog:
 sid=s['source_id'];date=s['date'] or '完整访谈日期未载'
 md.append(f"|{link(sid)}|{s['source_kind_chinese']}；{date}|{s['interpretation']}|")
md.extend(['','三场会议按事件计数：2月12日企业会议、3月19日专家咨询会、5月14日企业研讨会。3月转录与整理稿、5月议程与纪要分别属于同场材料。两份专家纪要是当前采用的记录数，不是已核实的总人数或总人次。报告附件重复收录同一纪要，不能充作另一位受访者或另一轮验证。','',
 '研究报告P032明确说明使用专家会研讨会及一对一访谈；P847起为专家访谈记录附件。以受访者姓名规范为XXX后，I01有31个、I02有24个不少于30字符的段落与附件对应段落达到0.95以上文本相似度，其中本稿使用的关键段落原字或匿名替换后完全一致。这是重复存档的辅助核查，不是研究信度指标。','',
 '## 底稿主张与原始支持','',
 '|主张|当前稿位置|原段|判断与交接动作|','|---|---|---|'])
for r in claims:
 loc='、'.join(dict.fromkeys(x['locator'] for x in r['source_evidence']))
 mp='、'.join(f'P{n:03d}' for n in r['manuscript_paragraphs_1based'])
 md.append(f"|{r['claim_id']} {r['audited_claim']}|{mp}|{loc}|{r['judgement']} {r['handoff_action']}|")
md.extend(['','上述核心内容支持的是纪要所记录的观点与作者的综合解释。没有把它们当成部门注意力比例、真实评审权重、标签金标准或执行效果的直接证据。','',
 '## 引文日期与身份边界','',
 'I01:P015原句为“现在的问题是药监批了，医保不一定进，医保进了，医院不一定用。”当前P091摘出的短句是连续原字，且已有“访谈纪要所记录的”限定，可以作为纪要引文保留。若后续改成“受访专家原话”，应转述或补受访逐字证据。3月19日的会议转录属于另一事件，不能补证史录文访谈的逐字讲话。','',
 'I01:P002记载2025年6月9日，文件名0605与之不一致；当前稿按正文记录日期使用有依据，不应仅因文件名改成6月5日。I02正文没有完整日期、地点和专家姓名，0616不能单独证明2025年6月16日。I01确认姓名和教授称谓，原纪要没有高校任职字段；“高校药事管理领域”是旧审查采用的身份概括，原件本身未独立证实任职。','',
 '## 匿名使用与未建立的程序事实','',
 f"{link('A04')}已保存2026年9月27日作者事实确认：“{author['user_statement']}”。负责人同意匿名公开使用这一事项已经关闭，不能再列作未确认。该确认不等于受访者逐一签署同意书、伦理审批完成或期刊保密审查证明已出具。当前内部采用稿P063和P091具名，公开稿应与已确认的匿名范围一致；内部原件台账保留真实姓名不构成对外公开原报告的授权。",'',
 '目前材料可以证明存在专家纪要、会议纪要及一场带时间戳的会议转录；不能补写13名受访者、总人次、约6.2万字材料、统一提纲已实施、主题饱和、双人交叉核对或正式定性编码。报告中关于患者数据使用应有伦理审批的讨论，也不是本研究已经获得伦理审批的凭证。','',
 '不同记录保留各自条件：I02:P004称三个核心维度，I01:P005列六维，W03M:P005记企业理解的四象限和评分。三者不得拼接成统一正式制度或权重；本稿五维文本编码仍由政策原文和代码本支持。','',
 '报告附件还含其他商业保险调研材料，但未在当前P063及既有三场会议绑定中作为新增采用资料列入。本次不扩大研究访谈样本或会议数。','',
 '## 交付文件','',
 f"- [完整证据映射](<{OUT/'interview-evidence.json'}>)：16项主张、当前段落覆盖、精确证据片段、引文判断、重复存档分析。",
 f"- [来源清单](<{OUT/'source_manifest.json'}>)：16份来源快照和SHA256、7份其他资料上下文清单、事件分组。",
 f"- [验证结果](<{OUT/'audit_validation.json'}>)：原件及快照哈希、引文原字、覆盖和旧封存完整性检查。",
 '',
 '源文件、旧审核脚本和先前封存均保持原状。指定的核实访谈来源.py只读取其证据定位逻辑，未执行其修改旧工作区文件的操作。本接收核查不替代编码方法合规验收，也未启动正文改写。',''])
(OUT/'interview-evidence.md').write_text('\n'.join(md))

# Verification checks are confined to the requested evidence acceptance outcome.
checks=[]
def check(name,passed,details=None):checks.append({'check':name,'passed':bool(passed),'details':details})
check('current_manuscript_sha256_matches_adopted_binding',hashlib.sha256(Path(S['M00']['source_path']).read_bytes()).hexdigest()==manifest['manuscript_sha256_expected'])
for sid,s in S.items():
 check(f'{sid}_source_unchanged',hashlib.sha256(Path(s['source_path']).read_bytes()).hexdigest()==s['sha256'])
 check(f'{sid}_snapshot_hash_matches_source',hashlib.sha256(Path(s['snapshot_path']).read_bytes()).hexdigest()==s['sha256'])
 check(f'{sid}_snapshot_read_only',Path(s['snapshot_path']).stat().st_mode & 0o222 ==0)
for s in manifest['context_inventory']:
 check(f"{s['source_id']}_context_source_unchanged",hashlib.sha256(Path(s['source_path']).read_bytes()).hexdigest()==s['sha256'])
check('all_current_project_mentions_mapped',all(x['mapped_claim_ids'] for x in mention_rows if x['role']=='project_evidence_mention'))
check('direct_quote_exact_in_current_and_original','医保进了，医院不一定用' in P('M00',91) and '医保进了，医院不一定用' in P('I01',15))
check('quote_attributed_as_minutes_not_verified_spoken_verbatim','访谈纪要所记录的' in P('M00',91) and not audit['direct_quote_audit'][0]['spoken_verbatim_verified'])
check('report_same_as_received_hash',S['R01']['sha256']==json.loads(Path(S['A02']['snapshot_path']).read_text())['sha256'])
check('anonymous_use_existing_confirmation_received',authorization['previous_responsible_author_anonymous_use_question_closed'])
check('three_events_not_five_meeting_records',len(manifest['adopted_event_groups']['meeting_events'])==3)
seal=OUT.parent/'交付封存.json'
old=json.loads(seal.read_text())
for k,v in old.items():
 if isinstance(v,list):
  for z in v:
   if isinstance(z,dict):
    path=z.get('path') or z.get('file') or z.get('absolute_path')
    expected=z.get('sha256')
    if path and expected:
     file=Path(path) if Path(path).is_absolute() else OUT.parent/path
     check('prior_sealed_'+file.name,file.exists() and hashlib.sha256(file.read_bytes()).hexdigest()==expected)
check('all_quote_fragments_match_original_paragraphs',all(x['fragment'] in P(x['source_id'],x['paragraph_1based']) for c in claims for x in c['source_evidence']))
validation={'checked_at':audit['created_at'],'status':'PASS' if all(x['passed'] for x in checks) else 'FAIL','check_count':len(checks),'checks':checks,'scope':'证据原字、来源哈希与交付完整性，不是研究方法信度效度验收'}
(OUT/'audit_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2))
assert validation['status']=='PASS',validation
print(json.dumps({'status':validation['status'],'checks':len(checks),'claims':len(claims),'project_mention_paragraphs':audit['summary']['manuscript_project_evidence_mention_paragraphs'],'quote_verified_in_minutes':True,'spoken_verbatim_verified':False},ensure_ascii=False))
