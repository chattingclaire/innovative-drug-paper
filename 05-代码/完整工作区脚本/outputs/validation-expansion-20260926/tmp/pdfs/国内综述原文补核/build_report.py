from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, os, re, unicodedata
OUT=Path('/PROJECT_ROOT/outputs/validation-expansion-20260926')
TMP=OUT/'tmp/pdfs/国内综述原文补核'
INV=OUT/'参考文献实质证据覆盖-缺口清点.json'
inventory=json.loads(INV.read_text())
refs={x['reference_number']:x for x in inventory['references'] if x['reference_number'] in [1,2,3,4,5,6,7,8,10,11]}
manifest={x['reference_number']:x for x in json.loads((TMP/'source-manifest.json').read_text())}
def ev(physical,printed,section,explanation,quote=None):
 d={'pdf_physical_page':physical,'printed_page':printed,'section_or_table':section,'evidence_paraphrase':explanation}
 if quote: d['short_original_quote']=quote
 return d
records=[
{
 'reference_number':1,
 'current_claim':'对比英、德、法、加四国的创新药价值评估体系，提出中国应构建附加临床收益评估体系并完善医保准入谈判规则。',
 'study_design':'四国创新药价值评估制度与流程的文献比较；原文称采用系统文献综述方法。本次未独立评价其检索完整性。',
 'sample_or_materials':'对象为英国、德国、法国、加拿大的相关价值评估制度；不是四国患者结局或药品临床试验样本。',
 'model_participants':None,
 'findings':'作者建议参考德、法、加经验构建附加临床收益评估及分级，以分级筛选拟谈判药品，并结合药物经济学评价完善准入决策依据。',
 'evidence':[
  ev(1,'17','摘要','摘要明确列出英、德、法、加四国及制度、评估流程的比较对象。'),
  ev(6,'22','3.1—3.3','3.1提出建立附加临床收益评估及具体分级；3.2提出用分级筛选拟谈判药品；3.3提出结合附加临床价值与药物经济学评价。','构建明确的创新药附加临床收益评估体系')],
 'assessment':'基本支持；保持为作者建议，不能写成我国已经建立该制度。',
 'recommended_revision':'孔繁翠[1]比较英、德、法、加四国的创新药价值评估制度，建议建立附加临床收益评估及分级体系，并据此完善拟谈判药品筛选规则。',
 'unresolved_items':['本次未追溯文中各国制度的全部底层政策，也不确认其截至2026年的现行状态。'],
 'pages_actually_read':[1,6], 'visual_check':{'status':'not_needed_for_current_claim','pages':[]},
 'doi':'10.3969/j.issn.1674-2982.2022.06.003'
},
{
 'reference_number':2,
 'current_claim':'建议建立与医保目录动态调整相衔接的临床获益分级机制。',
 'study_design':'法国临床效益评价制度介绍、一个药品案例及对中国的政策建议。',
 'sample_or_materials':'介绍SMR、ASMR评价及其与报销、价格的关系，以维莫非尼Zelboraf治疗特定黑色素瘤的评估作为说明案例；不是大样本效果评估。',
 'model_participants':None,
 'findings':'建议按治疗领域及疗效改善程度建立临床价值等级，将其作为医保准入依据之一，并结合持续证据每5年再评价以服务目录、价格和支付比例动态调整。',
 'evidence':[
  ev(1,'94','1—2','介绍法国评价制度与维莫非尼案例，说明研究范围。'),
  ev(2,'95','3.1','提出按治疗领域和疗效改善程度建立药品临床价值等级。','作为药品医保准入决策的重要依据之一'),
  ev(3,'96','3.2','建议结合新药监测、再注册周期及更新证据，每5年再评价临床价值等级，并据此调整目录、支付价格和比例等。')],
 'assessment':'基本支持；准确术语可用“临床价值分级及再评价”，属于制度建议而非已实施效果。',
 'recommended_revision':'赵华婷等[2]借鉴法国临床效益评价，建议建立临床价值分级及再评价机制，为医保准入与目录动态调整提供依据。',
 'unresolved_items':['本次未核验法国底层制度文件或维莫非尼原始临床试验；当前综述句不需要据此延伸临床效果结论。'],
 'pages_actually_read':[1,2,3], 'visual_check':{'status':'not_needed_for_current_claim','pages':[]},
 'doi':'10.7664/CHE20190524'
},
{
 'reference_number':3,
 'current_claim':'创新药进入医保目录存在遴选依据客观性不足、等待时间过长和谈判机制不健全等障碍。',
 'study_design':'对当时国内外创新药医保准入管理政策的规范性分析与对策讨论。',
 'sample_or_materials':'未报告可用于统计推断的政策或患者样本；文中讨论2009年版目录后长期未调整等历史情境，稿件收稿于2016年、刊发于2017年。',
 'model_participants':None,
 'findings':'摘要列出五类问题：遴选依据、专家遴选机制、目录调出机制、准入等待及谈判机制。当前正文选择其中三类并使用“等”，与原文相符。',
 'evidence':[
  ev(1,'455','摘要','原文问题清单直接列出当前引用的三类障碍，同时还包括专家遴选机制及目录调出机制。','医保目录遴选依据不够客观'),
  ev(2,'456','2.1续、2.4、2.5','客观依据问题涉及药物经济学、循证证据；等待问题基于当时目录调整停滞；谈判问题涉及统一规范、程序和信息。'),
  ev(3,'457','文末收稿、修回日期','稿件收稿日期为2016-03-29、修回日期为2016-06-03，用于标明历史语境。')],
 'assessment':'支持所引三类问题，但需增加历史限定，避免被读成对当前制度的直接判断。',
 'recommended_revision':'段晓托等[3]在2017年的政策分析中指出，当时创新药医保准入存在遴选依据不够客观、等待时间较长和谈判机制不健全等障碍。',
 'unresolved_items':['不据该历史政策分析判断当前制度仍存在相同障碍；本次未另行核验后续改革。'],
 'pages_actually_read':[1,2,3], 'visual_check':{'status':'some_heading_encoding_noise','pages':[],'note':'部分标题抽取乱码；所引摘要正文及相关段落可读，引用不依赖乱码标题。'},
 'doi':'10.6039/j.issn.1001-0408.2017.04.06'
},
{
 'reference_number':4,
 'current_claim':'基于价值的定价需以多维评价体系为前提。',
 'study_design':'基于价值的创新药定价与支付模式综述。',
 'sample_or_materials':'介绍价值定价、按适应症定价及相关支付、风险分担模式；没有报告用于检验“多维体系是必要前提”的经验样本或必要性检验。',
 'model_participants':None,
 'findings':'文中一处讨论价值评估的多维属性逐渐受重视，另一处强调价值评估是定价和支付基础；同时明确具体采用ICER还是价值框架仍需利益相关方探讨。',
 'evidence':[
  ev(1,'77','2.1.1','介绍多维价值评估趋势及DrugAbacus的八个要素。这是方法发展介绍，不等于提出所有价值定价必须先建多维体系。'),
  ev(3,'79','4.2','建议建立公开透明的价值评价标准，且保留ICER与价值框架等具体选择的讨论空间。','价值评估是基于价值的定价和支付模式的基础')],
 'assessment':'当前“需以多维评价体系为前提”合并了两个不同层级论述，必要条件语气偏强，应收窄。',
 'recommended_revision':'艾丹丹等[4]讨论了价值评估的多维属性，并强调以公开透明的价值评价标准支持基于价值的定价和支付。',
 'unresolved_items':['不能据本文证明某一特定多维框架、维度数目或加权方法的必要性与有效性。'],
 'pages_actually_read':[1,2,3], 'visual_check':{'status':'not_needed_for_current_claim','pages':[]},
 'doi':'10.7664/CHE20200318'
},
{
 'reference_number':5,
 'current_claim':'以博弈模型分析药品上市决策中的多方策略互动，揭示利益根源；与[6]—[8]合称多停留在两方或三方博弈层面。',
 'study_design':'药品上市与经营选择的理论博弈框架及均衡分析。',
 'sample_or_materials':'没有报告实证样本。设传统基础药、传统镀金药、创新药三种类型；创新药的临床优势及合理定价等是模型假设，不能当作观测结论。',
 'model_participants':{
  'framework':['药品生产企业','药品经营者（限定为医疗机构）','患者'],
  'government_role':'作为监管与政策建议对象，不直接参与该博弈。',
  'strategic_simplification':'求解时将患者购买概率γ固定为1，重点求解企业改造/销售与医疗机构经营选择。',
  'stages':'四阶段：药品类型、销售方式、医疗机构经营、患者购买。阶段数不等于主体数。'},
 'findings':'在设定条件下分析产业创新程度、医疗机构盈利及其他收益、镀金与额外销售成本如何影响企业及经营者的选择，提出监管建议。',
 'evidence':[
  ev(1,'1921','1及1.1—1.2','明确三类主要参与方、政府不直接参与，并把药品经营者限定为医疗机构。'),
  ev(2,'1922','1.3及2','虽列出四阶段和患者购买策略，但为计算而固定其购买概率。','本文中假定γ＝1'),
  ev(3,'1923','2.1—2.2','分析企业、医疗机构的策略均衡及参数影响；不是三个对称、均独立变化的策略主体。'),
  ev(4,'1924','3','根据模型分析提出创新、医疗机构收益结构和用药监管方面的建议。')],
 'assessment':'“三方框架”成立，但必须保留患者策略固定的简化；不能仅按题名或讨论涉及政府就计成四方，也不能把模型假设当成证据结论。',
 'recommended_revision':'康姗姗等[5]设置生产企业、医疗机构和患者三方框架，并在求解中固定患者购买概率，分析收益与成本因素对药品上市和经营选择的影响。',
 'unresolved_items':['本次未复算均衡推导，亦未验证2010年模型的制度假设对当前市场的适用性。'],
 'pages_actually_read':[1,2,3,4,5], 'page_scope_note':'物理第5页与另一篇文章共享页面，仅本篇续文/参考文献属于本核验来源。',
 'visual_check':{'status':'not_needed_for_current_claim','pages':[]}, 'doi':None
},
{
 'reference_number':6,
 'current_claim':'以博弈模型分析价格管制下多方策略互动及利益根源，并与[5][7][8]合称两方或三方博弈。',
 'study_design':'含政府战略性创新激励、企业创新和定价的多阶段动态博弈，比较价格竞争与价格管制，并作参数化数值分析。',
 'sample_or_materials':'Hotelling横向差异化市场中的两家代表性企业A、B；潜在消费者定义为患者和医生组合并按医保覆盖区分。数值分析采用设定参数，没有报告估计用的真实企业或患者数据样本。',
 'model_participants':{
  'formal_decision_makers':['政府','制药企业A','制药企业B'],
  'counting_boundary':'按独立决策者计为政府加两家企业；按机构类型计为政府与企业两类，不能混用两种计数。',
  'stages':'政府以社会福利最大化选择创新激励；两企业同时选择创新投入；两企业同时选择价格。',
  'other_roles':'患者/医生组合用于消费者效用和需求，医保覆盖及支付作为政策参数；不能因福利讨论提到患者、医保机构就都计作独立博弈方。'},
 'findings':'价格管制、创新激励与医保支付的作用具有参数和制度情景条件；合理配合可能改善创新配置，不等于价格管制或创新补贴无条件使所有主体受益。',
 'evidence':[
  ev(2,'69','2.1','假设两家代表性制药企业及横向差异化竞争。'),
  ev(3,'70','2.1末及2.2','明确三个阶段及政府、A、B的决策分工。','政府作为Stackelberg博弈领导者'),
  ev(5,'72','2.2.3及2.3','对价格管制与医保政策匹配给出有条件命题，并比较企业、患者、社会福利。'),
  ev(6,'73','2.3','数值分析直接给定参数，以展示政策交互作用；不是统计显著性检验。'),
  ev(7,'74','3','总结有条件政策作用并说明完全信息、横向差异化等研究限制。')],
 'assessment':'支持研究主题及条件性机制分析；“三阶段”不能替代“三方”的主体核验，且模型主体计数不构成文献创新性高低的证据。',
 'recommended_revision':'张新鑫等[6]构建政府与两家制药企业的三阶段博弈，讨论价格管制、创新激励和医保支付条件对创新投入及福利的共同影响。',
 'unresolved_items':['本次未复算模型和数值结果，不把条件性理论命题视为现实政策效果的因果证明。'],
 'pages_actually_read':[1,2,3,4,5,6,7,8], 'visual_check':{'status':'not_needed_for_current_claim','pages':[]},
 'doi':'10.19571/j.cnki.1000-2995.2017.10.008'
},
{
 'reference_number':7,
 'current_claim':'以博弈模型分析创新药医保谈判的多方策略互动，揭示利益根源；与[5][6][8]合称两方或三方博弈。',
 'study_design':'医保部门与药企的不完全信息非合作模型及谈判过程中的动态讨价还价模型，并结合2022年医保谈判资料讨论。',
 'sample_or_materials':'使用公开谈判结果和部分药品例子作为现实讨论；不是患者样本或计量因果评估，也未对全部谈判记录估计行为参数。',
 'model_participants':{
  'formal_decision_makers':['医保部门','医药企业'],
  'patient_role':'前文将患者列为利益相关方，但模型以医保部门代表参保者利益，患者不是独立博弈方。',
  'stages':'讨价还价模型列两轮报价、三个阶段；中间阶段涉及药企代表与总部协商，未另建总部为第三类利益主体的独立模型。',
  'policy_discussion_boundary':'建议中涉及医疗机构、监管者及第三方机构，不改变已构建模型的两方结构。'},
 'findings':'作者在设定的收益、风险、奖励惩罚和报价条件下分析策略均衡及谈判收益分配，并提出医保和企业行为改进建议。',
 'evidence':[
  ev(2,'6','1.2、1.3及图1','明确医保代表参保者利益；参与者列医保部门和医药企业（完全理性）。','医保部门、医药企业'),
  ev(3,'7','2及3.1','混合策略矩阵两方；后续动态模型仍针对医保与药企。'),
  ev(4,'8','3.1—3.3及图2','讨价还价的两轮三阶段属于谈判时序；同页公开谈判成功数据作为讨论材料。'),
  ev(5,'9','4.1—4.2','结论围绕两方策略及报价模型；政策建议扩展利益相关者角色。'),
  ev(6,'15','上接第9页，4.2续','讨论医生、监管部门、患者和第三方机构的反馈与支持作用，属于建议部分。')],
 'assessment':'正式模型两方可以确认；不能将利益相关方清单、谈判阶段数或政策建议参与者数当作模型主体数。',
 'recommended_revision':'谭清立等[7]以医保部门与药企为博弈双方，分析非合作策略及医保谈判中的动态报价过程。',
 'unresolved_items':['本次核验的是模型主体和引用范围，未检验该文收益函数、求导或报价推导的正确性。'],
 'pages_actually_read':[1,2,3,4,5,6], 'page_scope_note':'物理第6页即印刷第15页，与另一篇文章共享页面；只使用标明“上接第9页”的本篇续文。',
 'visual_check':{'status':'confirmed','pages':[2,4],'note':'已逐页查看渲染图，核对参与者、图1和两轮三阶段图2。'},
 'doi':'10.14055/j.cnki.33-1056/f.2024.06.004'
},
{
 'reference_number':8,
 'current_claim':'以演化博弈分析专利药医保价格谈判中的多方策略互动及利益根源；与[5]—[7]合称两方或三方博弈。',
 'study_design':'有限理性、非完全知识下的政府—药企两方演化博弈，配合情景仿真及三个药品销售数据的前后比较。',
 'sample_or_materials':'理论模型限定一家企业的一种专利药。实证部分选2016年谈判成功的吉非替尼、埃克替尼、富马酸替诺福韦，米内网2013—2021年20个城市公立医疗机构原研厂商销售资料；本次不推算未报告的有效观测总数。',
 'model_participants':{
  'formal_decision_makers':['政府机构','医药企业'],
  'strategies':'企业同意/拒绝降价；政府纳入/拒绝纳入目录。',
  'boundary':'单企单药，不含企业多品种联动；患者健康效益和社会声誉进入收益概念，并非独立第三方策略。'},
 'findings':'模型与仿真讨论谈判前后销售额、初始意愿和社会声誉对稳定状态或稳定时间的作用。实证部分报告部分销售指标的统计差异，不能改述为所有药品所有指标均显著，也不能直接证明谈判的净因果效应。',
 'evidence':[
  ev(2,'45','2.1.1','明确两方局中人、有限理性、非完全知识及单企单药假设。','政府机构、医药企业'),
  ev(4,'47','3','按设定收益、声誉及初始策略参数进行情景仿真。'),
  ev(7,'50','4、表5—6','明确三药、20城市、2013—2021年数据，按2017年前后分组；作者称采用单样本T检验。报告三药销量差异及埃克替尼、替诺福韦销售额差异有统计意义，而吉非替尼销售额差异不显著。'),
  ev(8,'51','5及末段限制','总结销售额、初始意愿、社会声誉作用，并明确尚未考虑同企业多药联动。')],
 'assessment':'两方演化博弈成立，同时应保留它具有实证比较部分这一事实；不能一概称四篇“仅停留理论模型”，或把前后差异当成已识别的因果效应。',
 'recommended_revision':'王恩楠和朱铭来[8]建立政府与药企的单企单药演化博弈，结合仿真及三种谈判药品的销售数据，讨论销售预期、初始意愿和社会声誉对谈判策略的影响。',
 'unresolved_items':['原文“单样本T检验”与组间比较表述、有效观测数及统计实现未独立复核；不替作者修正其检验方法名称。','Poppler渲染第7页时中文缺字，未能视觉确认中文表头；正文与表格中文依据pypdf可读文本，数字及显著性星号在渲染中可见。'],
 'pages_actually_read':[1,2,3,4,5,6,7,8],
 'visual_check':{'status':'partial_font_rendering_failure','pages':[7],'note':'中文缺字；不得称已完整视觉复核该表。'},
 'doi':'10.3969/j.issn.1674-2982.2023.02.007'
},
{
 'reference_number':10,
 'current_claim':'分析了2015年以来审评审批制度改革的变迁特征。',
 'study_design':'以制度创新理论解释药品研发外部激励和内部治理的制度失衡，并提出强制性、诱致性制度变迁设计。',
 'sample_or_materials':'使用研发投入产出及上市情况的二手描述资料：例如2008—2018年医药制造业R&D投入、2008—2019年国产创新药上市数量，并列2019年全球销量前十药品的国内外上市时间。研究期和主题并不统一限定为2015年后的审评审批政策。',
 'model_participants':None,
 'findings':'融资、审批、知识产权、地方保护属于外部激励；企业研发投入保障和产业自治属于内部治理。审批制度只占其讨论的一部分，文章主要提出制度变迁设计建议。',
 'evidence':[
  ev(1,'38','摘要、引言及1','目的与框架是研发制度失衡及制度设计。','提出强制性制度变迁和诱致性制度变迁的设计建议'),
  ev(3,'40','2.2','2015年文件用于解释新药概念改变，并非把2015年设成整篇制度变迁研究的统一起点。'),
  ev(4,'41','3.1—3.2','按外部激励、内部治理分析供给不足和过剩；审批制度是多个具体问题之一。'),
  ev(5,'42','4.1—4.2、表1','提出融资、审评审批、知识产权、地方保护及企业和产业层面的变迁建议；表1是十个药品的上市时间比较。')],
 'assessment':'当前综述将广义药品研发制度设计误缩写成特定时期的审评审批改革变迁研究，缺少原文支持，建议替换主题概括。',
 'recommended_revision':'毛心仪和姚峥嵘[10]从制度创新理论出发分析药品研发外部激励与内部治理的制度失衡，并提出强制性与诱致性制度变迁建议。',
 'unresolved_items':['若坚持保留“2015年以来审评审批制度改革的变迁特征”这一具体主张，需要另找直接研究该主题的原始文献；本次未扩展寻找替代引文。','未复核其二手统计、上市时间或历史政策批评的外部准确性；不可据此直接描述2026年现状。'],
 'pages_actually_read':[1,2,3,4,5,6], 'page_scope_note':'物理第6页印刷第43页含别篇参考文献，本篇只采用其自己的续列参考文献和文末信息。',
 'visual_check':{'status':'not_needed_for_current_claim','pages':[]},
 'doi':'10.14055/j.cnki.33-1056/f.2021.07.009'
},
{
 'reference_number':11,
 'current_claim':'各地落实创新药准入政策存在显著制度差异。',
 'study_design':'省级国谈药品单独支付政策的内容分类比较，结合专家访谈和模拟测算。',
 'sample_or_materials':'检索国家及省级医保局、卫健委官网；政策纳入期为2021-05-10至2023-09-22，限定省级、含落实28号文表述或单独支付关键词、已公开发布，并纳入所引相关政策。正文未给出最终政策文件总数和访谈专家人数，不据表中省份列名推造统一样本N。情景测算为陕西、辽宁的同一假设A药，单价3000元、城镇职工。',
 'model_participants':None,
 'findings':'对目录发布、遴选、药品管理、保障待遇和政策衔接作描述性比较，发现设计差异。讨论区分支持国谈非创新药落地与激励国谈创新药发展两种功能；并未把全部创新药准入政策作为研究总体。',
 'evidence':[
  ev(1,'24','摘要','对象明确是国家医保谈判药品单独支付的省级政策。'),
  ev(2,'25','1.1—1.2、表1—2及图1','交代政策纳排标准、内容分析、访谈和模拟测算；图1展示目录数量差异，属于描述比较。','通过内容分析法'),
  ev(3,'26','2.2—2.3、表3—5','比较遴选条件、三定/五定等管理办法和保障待遇，不是患者实际可及性效果的统计检验。'),
  ev(4,'27','2.4—2.5、表7—8、3.1','表8按设定条件算出陕西和辽宁报销额分别增加420元、240元，未提供随机样本或显著性检验。3.1区分非创新国谈药落地与国谈创新药支持。'),
  ev(5,'28','3.2—3.4、4.1','讨论制度设计差异与协同问题，并建议区分支持落地与支持创新的单独支付目录。')],
 'assessment':'同时存在对象扩张和强度扩张：应限定为国谈药品单独支付的省际政策设计差异，删除“显著”。本地原文未报告这类差异的P值、置信区间或假设检验。',
 'recommended_revision':'杨钰婷等[11]比较省级国谈药品单独支付政策，发现目录管理、药品管理、保障待遇及政策衔接等方面存在差异。',
 'unresolved_items':['文中未明确报告最终纳入政策文件总数、访谈专家人数及完整访谈资料；未另查补充材料。','该文不能单独支持“所有创新药准入政策存在统计显著差异”或“各省实施效果已经得到经验检验”的表述。'],
 'pages_actually_read':[1,2,3,4,5,6],
 'visual_check':{'status':'confirmed','pages':[2,4],'note':'已查看印刷第25、27页，核对方法、目录比较图表及A药情景测算表8。'},
 'doi':'10.3969/j.issn.1674-2982.2024.01.004'
}
]
for x in records:
 n=x['reference_number']; original=refs[n]; m=manifest[n]
 x['bibliography']=original['bibliography']
 x['manuscript_paragraph_index_zero_based']=original['citing_paragraphs'][0]['paragraph_index_zero_based']
 x['source']={'kind':'local_primary_published_pdf','path':m['path'],'sha256':m['sha256'],'pdf_page_count':m['pages'],'doi':x.pop('doi')}
 x['source']['url']=('https://doi.org/'+x['source']['doi']) if x['source']['doi'] else None
 x['source']['url_visit_status']='not_visited; DOI transcribed from local PDF' if x['source']['url'] else 'not_applicable; local primary PDF used'
 x['verification_scope']='targeted claim-to-source verification; not full-paper acceptance'
 x['evidence_status']='primary_pdf_targeted_verification_completed'

collective={
 'current_claim':'揭示了多主体差异的利益根源，但多停留在两方或三方博弈层面。',
 'finding':'四篇确实通过不同博弈框架讨论利益、政策及信息条件，但“方”的计数口径不同：[5]三方框架中固定患者购买概率；[6]政府加两家企业为三个决策者，政策与消费者角色不能按同一口径累加；[7][8]正式模型为两方。[8]还包含三药销售资料比较。',
 'support_boundary':'可报告这些指定文献的模型配置；不能据四篇有意选列的文献推断整个领域“大多停留”于某种水平，或凭主体数判定理论贡献高低。“揭示利益根源”宜改成在模型假设下分析收益、成本、信息及政策条件与策略选择的关系。',
 'recommended_replacement':'在主体策略互动方面，康姗姗等[5]设置生产企业、医疗机构和患者三方框架，并在求解中固定患者购买概率；张新鑫等[6]构建政府与两家制药企业的三阶段博弈，讨论价格管制、创新激励和医保支付的共同作用；谭清立等[7]以医保部门与药企为双方分析非合作策略及动态报价；王恩楠和朱铭来[8]建立政府与药企的单企单药演化博弈，并结合仿真与三种谈判药品的销售资料展开讨论。这些研究在各自假设下分析利益、政策和信息条件对策略选择的影响。',
 'unresolved_items':['若要保留针对整个领域的“多数”“停留”或研究缺口判断，需要明确检索总体、纳排规则和文献比较依据；本次10条引文核验不能证明该概括，也不能证明本研究创新性。']
}
p15='在评价标准与准入机制方面，孔繁翠[1]比较英、德、法、加四国的创新药价值评估制度，建议建立附加临床收益评估及分级体系，并据此完善拟谈判药品筛选规则；赵华婷等[2]借鉴法国临床效益评价，建议建立临床价值分级及再评价机制，为医保准入与目录动态调整提供依据；段晓托等[3]在2017年的政策分析中指出，当时创新药医保准入存在遴选依据不够客观、等待时间较长和谈判机制不健全等障碍；艾丹丹等[4]讨论了价值评估的多维属性，并强调以公开透明的价值评价标准支持基于价值的定价和支付。上述研究涉及创新药价值评估、临床价值分级及医保准入机制。'
report={
 'status':'bounded_primary_source_claim_verification_completed',
 'created_at':datetime.now(timezone.utc).isoformat(),
 'identity':{'kind':'AI','name':'V600独立评审A（本次仅承担文献原文核验）'},
 'scope':{'reference_numbers':[1,2,3,4,5,6,7,8,10,11],'purpose':'核对清点文件记录的正文具体主张，定位原始PDF中的研究材料、模型主体和结论，提出准确修订建议。','exclusions':['未核验[9]及其他编号','未修改主Word','未读取或修改编码标签与研究统计','未改冻结文件','不作全文验收、投稿就绪或创新性证明']},
 'inventory':{'path':str(INV),'sha256':hashlib.sha256(INV.read_bytes()).hexdigest()},
 'manuscript_binding':{'path':inventory['manuscript']['path'],'sha256_as_recorded_in_inventory':inventory['manuscript']['sha256'],'paragraph_locator':inventory['manuscript']['paragraph_locator'],'current_word_reopened':False,'limit':'本报告绑定清点文件保存的P15、P16文本快照；未重新打开Word，因此不宣称其后未发生变化。'},
 'methods':{'python':'/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3','text_extraction':'pypdf，按物理页抽取；长输出截断后分组补读。少量引文去除PDF断行与字间空格并统一全半角，不改变文字含义。','visual':'pdftoppm渲染并查看[7]物理页2、4，[8]物理页7，[11]物理页2、4。结果及字体问题逐条记录。','reading_scope':'按当前引文定位研究对象、方法、主体和结论；[1]仅定点读物理页1、6，其余实际页记录见各条。本次不声称逐篇方法学全面验收。','context_recovery':'本轮曾经历上下文压缩，沿用本轮已完成阅读记录；恢复后重新定点核对关键引句，并继续完成尚未核对的材料。','web_visits':0,'downloads':0,'source_artifacts':'仅使用匹配题名、作者与刊期的本地已出版原文PDF；提取文本与渲染图是本次自建辅助材料，不替代原件。'},
 'findings_summary':['[1][2]基本支持当前建议性概括；[3]支持但应明确2017年历史语境。','[4]“多维评价体系为前提”强于原文，应改为多维属性讨论及公开透明评价标准。','[5]—[8]逐篇模型主体可确认，但计数层级、阶段数及患者角色各异，不宜用笼统“多停留”作领域或创新性判断。','[10]当前概括的研究主题和时间范围与原文不符，应改为药品研发制度失衡及变迁设计。','[11]对象限于国谈药品单独支付；政策差异为描述性比较，删除“显著”，不外推全部创新药准入。'],
 'references':records,
 'collective_model_claim':collective,
 'suggested_text':{'paragraph_15_full_suggestion':p15,'paragraph_16_model_segment':collective['recommended_replacement'],'paragraph_16_ref10_segment':records[-2]['recommended_revision'],'paragraph_16_ref11_segment':records[-1]['recommended_revision'],'ref9_handling':'[9]原句不在本次任务范围，未作来源验收；此处不给整段P16替换以免将未核验内容一并背书。'},
 'significance_boundary':{'ref8':'原文存在T检验和统计意义报告，但仅对限定三药、时期、城市及特定指标，吉非替尼销售额不显著；未复算其检验，也未认定其因果识别。','ref11':'内容分类比较、专家访谈和设定条件的报销情景测算；未报告所述省际制度差异的统计显著性，不宜写“显著制度差异”。'},
 'global_unresolved_items':['如要维持[10]的原主张，需要另找直接讨论2015年以来审评审批改革变迁的来源。','如要维持领域多数模型或创新性缺口主张，需要超出本次有界清单的系统文献比较。','[11]未明确给出纳入政策总数和访谈人数；[8]检验实施与观测数未复核且中文视觉渲染受限。','未外部复核作者所引底层数据、政策、临床证据，也未评价全部推导是否正确；这些限制不应被“已定位原文”掩盖。'],
 'original_files_modified':False,'coding_or_statistics_accessed_in_this_task':False,'full_manuscript_acceptance':False,'research_originality_proven':False,'submission_ready_claim':False
}

def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s))
for x in records:
 s=x['source']; assert hashlib.sha256(Path(s['path']).read_bytes()).hexdigest()==s['sha256'],s['path']
 texts=json.loads((TMP/f"ref-{x['reference_number']:02d}-pages.json").read_text())
 for e in x['evidence']:
  assert 1<=e['pdf_physical_page']<=s['pdf_page_count']
  if 'short_original_quote' in e: assert norm(e['short_original_quote']) in norm(texts[e['pdf_physical_page']-1]),(x['reference_number'],e)
assert report['inventory']['sha256']=='5c7e52ff8eb1c20a36bcdc97d98864e37af6b3b33f2a18ad16e527845bc00f0a'
report['validation']={'target_reference_set_exact':True,'source_pdf_count':len(records),'all_primary_pdf_hashes_unchanged':True,'inventory_hash_unchanged':True,'all_short_quotes_located_in_stated_pages_after_whitespace_width_normalization':True,'all_required_evidence_fields_present':True}

lines=[
 '# 参考文献缺口：国内综述原文补核',
 '',
 '本次核对[1]—[8]、[10]、[11]共10条，针对清点文件保存的正文P15、P16主张逐篇定位原始PDF。主要需要修正[4]的必要条件表述、[10]的研究主题概括和[11]的对象及“显著”措辞；[5]—[8]需区分模型参与者、决策阶段和政策讨论中的相关方。',
 '',
 '执行者为AI（V600独立评审A，本次仅承担文献原文核验）。原件只读；未改主Word、标签、统计或冻结文件。此报告不是全文验收、投稿就绪判断或研究创新性证明。',
 '',
 f"主张来源：[清点JSON](<{INV}>)；SHA256 `{report['inventory']['sha256']}`。绑定的Word快照为 `{report['manuscript_binding']['path']}`，其清点时SHA256为 `{report['manuscript_binding']['sha256_as_recorded_in_inventory']}`。P15/P16是从0开始的直接段落索引，不是页码；本次没有重新打开Word。",
 '',
 '方法：bundled Python的pypdf按页抽取原文；对模型图及政策比较表作必要视觉检查。引号内只保留必要的短语，去除PDF断行、字间空格并统一全半角。各条分别列物理页和期刊印刷页。[1]为物理页1、6的定点阅读；其他阅读范围见逐条记录。上下文压缩后依据本轮阅读记录恢复，并重新核对关键短引文。没有网络访问或下载。',
 '',
 '## 当前主张与原文对应',
 '',
 '| 引文 | 核验结果 | 修改重点 |',
 '|---|---|---|',
 '| [1] | 基本支持 | 保持四国比较与建议性语气 |',
 '| [2] | 基本支持 | 宜用“临床价值分级及再评价” |',
 '| [3] | 支持历史问题概括 | 加2017年及“当时” |',
 '| [4] | 应收窄 | 多维属性受到重视不等于必要前提 |',
 '| [5] | 三方框架但有固定策略 | 患者购买概率固定为1，政府不直接入局 |',
 '| [6] | 政府与两企业三阶段 | 机构类型、独立决策者、阶段数分别表述 |',
 '| [7] | 正式模型两方 | 患者由医保代表；两轮三阶段不等于三方 |',
 '| [8] | 两方演化博弈并含实证比较 | 单企单药；三药销售比较不等于因果证明 |',
 '| [10] | 当前主题概括失准 | 改为研发制度失衡及变迁设计 |',
 '| [11] | 对象及强度扩大 | 限国谈药单独支付，删“显著” |',
 ''
]
for x in records:
 n=x['reference_number']; s=x['source']
 lines += [f"### [{n}] {x['bibliography']}", '', f"**正文原主张（P{x['manuscript_paragraph_index_zero_based']}）**：{x['current_claim']}", '',f"**来源**：[原始PDF](<{s['path']}>). SHA256 `{s['sha256']}`；共{s['pdf_page_count']}个物理页。"]
 if s['url']:lines += [f"DOI链接：[{s['doi']}]({s['url']})（由本地PDF抄录，未访问网页）。"]
 else:lines += ['本次未在原文识别出DOI；使用上述本地原始PDF，不编造URL。']
 lines += ['',f"**研究设计和材料**：{x['study_design']} {x['sample_or_materials']}"]
 if x['model_participants']:
  lines += ['', '**模型主体与边界**：']
  for k,v in x['model_participants'].items():
   v='、'.join(v) if isinstance(v,list) else v
   lines.append('- '+v)
 lines += ['', '**原文定位与对应**：']
 for e in x['evidence']:
  q=f" 短引：“{e['short_original_quote']}”。" if 'short_original_quote' in e else ''
  lines += [f"- PDF物理第{e['pdf_physical_page']}页／印刷第{e['printed_page']}页，{e['section_or_table']}：{e['evidence_paraphrase']}{q}"]
 lines += ['',f"**结论范围**：{x['findings']}",'',f"**本次判断**：{x['assessment']}",'',f"**建议准确修订**：{x['recommended_revision']}",'','**未解决项及限度**：']
 for u in x['unresolved_items']:lines += ['- '+u]
 lines += ['', '实际阅读物理页：'+ '、'.join(map(str,x['pages_actually_read']))+'。']
 if x.get('page_scope_note'):lines += [x['page_scope_note']]
 if x['visual_check'].get('note'):lines += ['抽取／视觉记录：'+x['visual_check']['note']]
 lines += ['']
lines += ['## 两方、三方及“显著”的合并核对','','原合并句：'+collective['current_claim'],'',collective['finding'],'',collective['support_boundary'],'', '**[8]与[11]不能互借证据强度**：'+report['significance_boundary']['ref8']+' '+report['significance_boundary']['ref11'],'','## 可直接供正文修订的文字','','以下是建议文本，尚未写回主Word。','','**P15建议整段**：','','> '+p15,'','**P16中[5]—[8]片段建议**：','','> '+collective['recommended_replacement'],'','**P16中[10]片段建议**：','','> '+records[-2]['recommended_revision'],'','**P16中[11]片段建议**：','','> '+records[-1]['recommended_revision'],'',report['suggested_text']['ref9_handling'],'','## 尚未解决的证据缺口','']
for u in report['global_unresolved_items']:lines+=['- '+u]
lines += ['','10份原始PDF和清点文件在输出前重新计算哈希，均与本次读取记录一致；10条短引均在所标物理页通过去空白及全半角规范化后定位。该检查验证来源绑定与引文位置，不代替方法学验收。','']

json_text=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
md_text='\n'.join(lines)
assert [x['reference_number'] for x in records]==[1,2,3,4,5,6,7,8,10,11]
for x in records:
 for field in ['source','sample_or_materials','findings','evidence','assessment','recommended_revision','unresolved_items']:
  assert x.get(field)
outputs=[(OUT/'参考文献缺口-国内综述原文补核.json',json_text),(OUT/'参考文献缺口-国内综述原文补核.md',md_text)]
for dest,_ in outputs: assert not dest.exists(),f'拒绝覆盖已有文件: {dest}'
for dest,content in outputs:
 tmp=TMP/(dest.name+'.pending')
 with tmp.open('x',encoding='utf-8') as f: f.write(content); f.flush(); os.fsync(f.fileno())
 os.link(tmp,dest)
 tmp.unlink()
 print(json.dumps({'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size},ensure_ascii=False))
