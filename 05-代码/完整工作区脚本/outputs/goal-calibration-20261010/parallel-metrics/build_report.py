#!/usr/bin/env python3
"""Build the Chinese audit, complete method matrix and handoff from frozen inputs."""
from pathlib import Path
from fractions import Fraction
import json, hashlib, difflib, shutil

P=Path(__file__).resolve().parent
ROOT=P.parents[2]
def load(p):return json.loads(Path(p).read_text())
def save(name,data):(P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def link(p,label=None):return f'[{label or Path(p).name}](<{p}>)'
def fmt(v):return 'NA' if v is None else f'{v:.6f}'
M=load(P/'input_manifest.json'); frozen={r['original']:P/r['snapshot'] for r in M['files']}

if (P/'supplemental_input_manifest.json').exists():
 for record in load(P/'supplemental_input_manifest.json')['files']:
  frozen[record['original']]=P/record['snapshot']

J=load(P/'recomputed_AC.json'); meta=J['metadata']; rows=J['comparisons']
S={}
def source(key,title,url,read_scope,method,limit,local=None):
 S[key]={'title':title,'url':url,'actual_read_scope_this_audit':read_scope,'supported_method':method,'not_supported':limit,'local_evidence':local}
source('HS2005','Hsieh & Shannon (2005). Three Approaches to Qualitative Content Analysis. Qualitative Health Research 15(9):1277–1288.','https://doi.org/10.1177/1049732305276687','本地原刊提取的印刷1281–1282页；本轮另核出版社及PubMed摘要。','由理论/既有研究起始类别，再给操作定义和例证；检视框架未覆盖内容。','不是本研究五维定义的原发布者；不能据其概念流程宣称完成内容效度。','outputs/编码修订核查-20261008/定义溯源核查/方法依据/Hsieh_Shannon2005_relevant_pages.txt')
source('W2014','文宏 (2014). 中国政府推进基本公共服务的注意力测量. 吉林大学社会科学学报54(2):20–26,171.','https://doi.org/10.15939/j.jujsse.2014.02.012','本地原文转写，关键词、语境判定及句数分母段；旧过程文件另记录原PDF页核查。','文本语境计句、专家审查关键词适配。','原文全部句子分母不等于本文五维句次总和；不能把原文专家实施移写为本文已完成。','参考文献/中国政府推进基本公共服务的注意力测量——基于中央政府工作报告(1954—2013)的文本分析_文宏.md')
source('C2018','陈星平、毕利娜、吴道友 (2018). 中国政府推进科技人才创新创业的注意力测量. 科技进步与对策35(23):155–160.','https://www.kjjb.org/fileup/1001-7348/HTML/2018-23-155.htm','本轮核官网书目；全文入口返回502。方法细节依据已实际阅读的20261007指标过程文件，本轮未重新获取全文。','同句同维一次、跨维计数作为已有项目方法来源。','其信度0.623/0.815不能改称Cohen κ；未将本轮访问失败写成全文重读。')
source('GS2013','Grimmer & Stewart (2013). Text as Data. Political Analysis21(3):267–297.','https://web.stanford.edu/~jgrimmer/tad2.pdf','作者全文§2.3、§5.1、§5.2.1及§5.2.3，作者稿第4、9–10、13页。','根据目标量验证；代码本开发后用新材料评价；保存机器对人工的混淆矩阵。','不规定本研究0.80、180/240/500样本量或未来模型有效性。')
source('CO1960','Cohen (1960). A Coefficient of Agreement for Nominal Scales. Educational and Psychological Measurement20(1):37–46.','https://doi.org/10.1177/001316446002000104','书目由官方scikit-learn参考文献及既有核验核对；本轮未取得原刊全文。','名义二分类κ公式；本轮用独立有理数公式与官方实现交叉核对。','κ不是效度、注意力或通用发表证明；无统一0.80线。')
source('AP2008','Artstein & Poesio (2008). Inter-Coder Agreement for Computational Linguistics. Computational Linguistics34(4):555–596.','https://aclanthology.org/J08-4004.pdf','正式全文§5.3、印刷590–591页及书目信息；相关原文另由旧核验定位。','报告编码设计、四格及罕见类分歧；一致性与基于语料的结果评估分别说明。','不支持更换指标以豁免项目阈值；可靠性不能推出语义真值。')
source('CF1990','Cicchetti & Feinstein (1990). High agreement but low kappa: II. Resolving the paradoxes. Journal of Clinical Epidemiology43(6):551–558.','https://pubmed.ncbi.nlm.nih.gov/2189948/','NLM原文摘要与书目，非全文。','κ附报正类、负类一致率。','Ppos/Pneg不是敏感度/特异度；Ppos与相同二元四格F1数值相同。')
source('BY1993','Byrt, Bishop & Carlin (1993). Bias, prevalence and kappa. Journal of Clinical Epidemiology46(5):423–429.','https://pubmed.ncbi.nlm.nih.gov/8501467/','NLM摘要、书目及项目既有原文核验。','用两方类别边际解释κ对类别分布和判读差异的敏感性。','不能把实际漏判都解释为稀有率，不能跨抽样组成直接比较κ。')
source('HT1952','Horvitz & Thompson (1952). A Generalization of Sampling Without Replacement From a Finite Universe. JASA47(260):663–685.','https://doi.org/10.1080/01621459.1952.10483446','实际查看本地原刊印刷669页图像式(6)，并核出版书目。','已知纳入概率的逆概率总量估计；四格总量与维度总量先加权再形成比率。','总量无偏不意味着κ、P/R/F1或结构比无偏。','outputs/final-three-department-20261007/source-checks/HT1952-p8-policy-review.png')
source('RWY1992','Rao, Wu & Yue (1992). Some recent work on resampling methods for complex surveys. Survey Methodology18(2):209–217.','https://www150.statcan.gc.ca/n1/pub/12-001-x/1992002/article/14486-eng.pdf','官方书目及原刊PDF入口核对；本轮公式实现主要核查官方svrep源代码，未声称重读全篇。','分层复杂抽样重抽样方法来源。','5000次百分位法的稀有类覆盖并非自动充分；原文不为新设计提供通用区间。')
source('SK18','scikit-learn 1.8.0 官方文档与实际软件实现','https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.cohen_kappa_score.html','读取官方API；实际运行1.8.0的cohen_kappa_score、confusion_matrix和precision_recall_fscore_support，核对220组。','sample_weight承载入样设计权重；weights=None保持名义类别。','weights=linear/quadratic为类别距离权重，不能用于把五维排成有序类别；点估计函数不生成设计一致CI。')
source('SVREP','svrep 作者官方源码与CRAN Bootstrap Methods for Surveys vignette','https://cran.r-project.org/web/packages/svrep/vignettes/bootstrap-replicates.html','读取方法选择、有限总体/多阶段条件，及make_bootstrap_weights.R第298–318行，保存源码SHA。','SRSWOR因子1+sqrt(1−pi)[n/(n−1)M−1]可与官方公式逐项对应；复杂设计需完整层次与概率。','本轮没有执行R/survey/svrep；不能把源码核查说成R实算；不把旧180公式移植到新家族两阶段或基础加补样联合设计。')
source('G2023','Gilardi, Alizadeh & Kubli (2023). ChatGPT outperforms crowd workers for text-annotation tasks. PNAS120(30):e2305016120.','https://doi.org/10.1073/pnas.2305016120','读取作者公开稿v2 HTML；正式PMC入口本轮遇验证页，论文身份由既有正式核验及DOI核对。','相同任务说明下区分对人工参照的表现和同提示重复一致性。','不照搬只保留两人一致文本的评价掩码；论文他域结果不验证本项目。')
source('T2024','Törnberg (2024). Best Practices for Text Annotation with Large Language Models. Sociologica18(2):67–85.','https://sociologica.unibo.it/article/download/19461/18662?inline=1','出版社全文，重点§9同提示重复及小幅提示变化。','保存提示/模型/参数，对同请求重复和等义微扰分别评价。','本项目将重复性与分类效度分别验收；小样本稳定不替代人工判断。')
source('HK2026','Halterman & Keith (2026卷期，2025在线). Codebook LLMs. Political Analysis34(2):188–204.','https://doi.org/10.1017/pan.2025.10017','出版社全文§4.1、§8.5–8.6/Table5；70/15/15拆分但文章只用train/dev。','代码本行为测试、纳排条件检查、逐条误差分类。','其0.7是作者F1目标，不是本研究κ阈值；其单标签多类任务不能替代逐维二元评价。')

matrix=[]
def row(id,step,category,refs,method,actual,metrics,conditions,acceptance,evidence,status,next_action,tools):
 matrix.append({'id':id,'步骤':step,'证据类别':category,'参考来源':refs,'参考的具体方法':method,'当前实际实施':actual,'指标或记录':metrics,'适用条件':conditions,'验收要求':acceptance,'现有证据':evidence,'本轮状态':status,'下一步':next_action,'可复用工具与核验':tools})
row('M01','研究范围、来源与语料框','语料可追溯',['GS2013','W2014'],'先明确政策文本的研究范围和目标量，再建立完整可复查语料框。','00-baseline保存4481条三部门源框及136份源文件清单；本支线验证12份基线快照哈希。',['文件/单元纳入排除流量','部门N','时期/效力/附件/联合来源映射','原件/正文/语境SHA'],'文档时期、部门与纳排条件预先确定；4481与GOV443分开。','所有目标ID可追踪；来源不明登记unknown，不能因标签或占比分布删除。不是κ阈值项目。',['00-baseline/source-only-frame.jsonl','00-baseline/source_files_manifest.json','00-baseline/legacy-frame-manifest.json'],'框已冻结；来源问题00064在基线仍待处置','先补核或锁定明确unknown策略再进入正式检验。','hashlib、唯一ID/部门计数、输入清单')
row('M02','分析单元、必要语境与计数','测量操作化',['W2014','C2018','HS2005'],'以固定句段为记录；语境解释该记录，同维布尔计一次、跨维可并存。','共同手册已区分纯引导、实质总领、成员及确指援引；旧语料有重复与语境补全史。',['单位—来源位置映射','正例锚点及必要语境','同维去重','全0/多标签数','纯引导与缺材料数量'],'全部方法共享当前单元和同一语境；同一命题解释范围不等于新增观测。','无静默漏行、无语境副本重复计数；模糊单元须有处置。',['00-baseline/legacy-common-manual.md','00-baseline/source-only-frame.jsonl'],'手册已具规则；新共同判据仍需校准','冻结逐单元材料和清单承接规则；检查计数归属。','ID集合、哈希、布尔矩阵；不以分词软件替代语义判断')
row('M03','五维构念及内容效度','内容效度',['HS2005','W2014','C2018'],'政策/理论概念→维度定义→纳排→正反例→领域审查。','已有政策映射和I/F边界建议；旧宽F与当前公平联系F不同，旧质量S与当前风险S不同。',['五维来源对照','纳排和必要语境覆盖','专家独立意见、异议及采纳理由','未被框架覆盖的实质内容清单'],'真实领域评议与AI开发审查身份分开；若无量化评分则不生成CVI。','五维及实质变更均有直接理论/政策与实例依据；保留有异议边界；不能按预期占比选择定义。',['00-baseline/legacy-common-manual.md','00-baseline/legacy-calibration-manual.md','00-baseline/legacy-I-boundaries.json','00-baseline/legacy-F-boundaries.json'],'有内容依据；没有据本包完成真实独立专家内容审查','完成领域校准记录后冻结统一口径。','概念映射表；不机械加Cronbach α/KMO/因子分析')
row('M04','开发校准与暴露登记','开发/检验独立性',['GS2013','HK2026'],'在开发材料上澄清共同判据，冻结后用独立判断评价。','旧180和挑战60均有开发暴露；历史人工事后审定不等于新人工独立初判。',['开发ID/正文族/语境暴露记录','各次手册实质变更','校准原判和讨论','新旧材料角色'],'分类答案或分歧已用于修改时，不能仍把该材料作新版本独立检验。','暴露与模型/手册版本成对冻结；历史统计保留诊断身份。',['00-baseline/legacy-plan.md','00-baseline/legacy-IF-disagreements.json','01-review/exposure-ids.json'],'旧样本用途明确；新检验未完成','校准结束后锁定方法及独立判读流程。','暴露台账、版本SHA')
row('M05','同手册同材料和实施冻结','版本与复现',['T2024','HK2026'],'封存手册、代码/提示、模型可得参数、输入和执行策略。','旧A/C v9→v11→v12→v14有补材/替代agent复读；本轮变更JSON候选SHA与快照不匹配。',['code/manual/prompt/material hash','实际调用日志/失败/重试','first-valid选取策略','版本间标签变化'],'不得按结果好坏挑响应；只按预置技术有效性重试；本项目后续实际LLM执行按用户指定GPT-6.1 Sol/ultra记录。','各次评价绑定同一实质定义和有效材料；候选变更清单和真实SHA一致。',['input_manifest.json','label_changes_and_disagreements.json','unlogged_calibration_diff.patch'],'历史绑定通过；候选校准元数据需补记','由主对话在新冻结记录中修正绑定并登记未记录的I2等变化，不覆盖旧文件。','hashlib、schema检查、实际执行记录；本支线不新跑模型')
row('M06','抽样与稀有类精度规划','抽样设计',['HT1952','SVREP','GS2013'],'概率样本估计明确总体；已知纳入概率加权；另列富集挑战。','旧180为每部门60个canonical代表，N=947/760/60；挑战60仅药监/医保各30。当前新草案目标是全部4481。',['N_h/n_h/pi/w','参考阳性与预测阳性分母','权重范围/有效信息量','预设区间精度及稀有类达到概率'],'预测阴性需正纳入概率；新样本量按分维度/部门精度，不能机械认定240足够。','设计可复现、总体明确、所有目标单位有正概率；挑战不混入总体κ/P/R/F1。',['00-baseline/legacy-sampling-design.json','snapshotted confirmation_sampling_PRIVATE.json','human-design-audit/真人复核统计方法预设冻结.json'],'旧设计已验证；新n/种子/分层仍未冻结','先选择单层分层SRS或有完整联合概率的补样设计，再封存样本量。','R survey/svrep适用性核定；本轮Fraction核w与pi')
row('M07','人工独立初判信度','人工独立信度',['CO1960','AP2008','CF1990','BY1993'],'两位真人按共同手册独立盲评，封存首次提交后计算逐维一致性。','当前A/C底层为AI初判及复读；另有用户确认的真人事后审定，未形成新手册下的两位真人独立首次标签。',['逐维κ','po','原始/设计加权四格','双方正负边际','Ppos/Pneg','可判n与排除ID','95%CI'],'两位不同真人；机器答案/对方答案不可见；独立初判在讨论前锁定；缺失不能填0。','保留逐维κ≥0.80项目目标；NA不是达标；区间跨0.80不等于通过。部门结果分别披露，阈值主估计口径在检验前锁定。',['recomputed_AC.json','label_changes_and_disagreements.json','00-baseline/legacy-validation-design.md'],'历史值已复核；本轮真人信度验收未执行','完成真实盲评后先算协商前信度，再进入裁定。','sklearn cohen_kappa_score(weights=None,sample_weight=w)＋独立Fraction')
row('M08','分歧裁定与可信参照','参照形成',['GS2013','AP2008','HK2026'],'信度计算后另行裁定，保留A/B原判及理由，裁定者不看机器预测。','旧T为选择性AI裁定流，不能改称真人金标准；后续真人事后审定记录须与独立原判区分。',['分歧数/率','裁定原因与原文','裁定前后标签差','一致控制项审查','未决数量'],'有预先规定的裁定政策和人员身份；不以机器得分选裁定结果。','所有正式参照标签可追溯；独立信度仍使用原始A/B，不用裁定后的一致标签重算。',['snapshotted final_bindings_v14_CONFIRMED_r3.json','00-baseline/legacy-validation-design.md'],'新可信裁定参照待生成','另存reference标签、身份、日期、政策及原判映射。','不可覆盖的三条标签流＋审定记录')
row('M09','规则与LLM逐维分类评价','机器分类效度',['GS2013','HK2026','SK18'],'分别将冻结规则与冻结LLM和可信裁定参照比较。','既有规则/LLM多版只可按同版参照作历史诊断；新定义下尚无独立可信参照。',['κ、Precision、Recall、F1','TP/FP/FN/TN原始及设计加权','po','正负例数量、可判n','95%CI','低值/NA清单'],'参照为纵轴真值侧，预测为机器侧；P=TP/(TP+FP)，R=TP/(TP+FN)，F1=2TP/(2TP+FP+FN)。','两机器分别、五维分别κ/P/R/F1≥0.80；所有必要项均可定义；不挑A或B较高者，不用宏平均替代逐维目标。',['统计复算/采用结果基线精确复算.json','00-baseline/legacy-plan.md'],'本支线不宣布新机器合格','参照与手册核定后按冻结计划计算并逐项验收。','sklearn precision_recall_fscore_support(average=binary,pos_label=1,zero_division=NaN,sample_weight=w)；掩码须外部明示')
row('M10','分类分歧、边际与误判原因','分类诊断',['CF1990','BY1993','HK2026'],'按四格连接原文，分清误检、漏检、参照争议和来源/定义问题。','本轮列出v14全部35个维度分歧、28个单元；I/F高阴性一致掩盖阳性分歧。',['FP/FN清单','部门/维度边际','正负一致率','具体错误类别数量和例证'],'人工A/C无单一真值时四格命名A1C0/A0C1；不得把一方叫FP/FN真错。','每个改动有语义或实施依据；不由提高κ推定标签正确。Ppos与F1同值只算一份阳性重合信息。',['label_changes_and_disagreements.json','recomputed_AC.json'],'已复算并记录；语义裁定非本支线授权工作','I/F原文分歧带入开发校准，随后更新暴露状态。','精确四格＋原始理由/材料包映射')
row('M11','全量输出、待定和执行失败','运行质量',['HK2026','T2024'],'输出完整性、引用准确性与分类正确性分别检查。','基线目标4481；历史后期可判输出4480，00064为材料问题，不能静默减总体。',['目标/返回/有效/待定/失败数','共同可判覆盖','重复/漏ID','schema与引文逐字QA','每维未知权重比例'],'机器失败、资料待定、语义0三种状态分开；可判集合按维保存。','目标ID全部有状态，失败保留；对不完整集合的评价只能作条件评价，不能冒称全框。',['00-baseline/legacy-plan.md','00-baseline/legacy-frame-manifest.json'],'有明确未决材料记录','统一00064及其他新失败处理后绑定全量结果。','集合断言、schema、SHA；正确引文不替代分类效度')
row('M12','同请求重复稳定性','输出稳定性',['G2023','T2024'],'预选同材样本，对完全相同prompt/payload重复，保留全部原输出。','旧v29有36条重复；旧v32有三批三次重复；新prompt/model不能继承旧稳定性值。',['两两逐维κ、po、四格、正负边际','三次标签变化数/整组完全一致率','q范围','无效返回数量'],'模型、实际请求、batch、上下文、参数可得信息相同；重复调用不替换生产首次有效结果。','预先记录抽取范围与重复次数并完整报告；无通用0.80线，不机械套机器效度验收。若主张稳定，须证据支持该具体版本。',['指标依据与理论对齐.md','旧指标清单与r3绑定要求.md'],'旧版本证据存在；新版本需实测','冻结后安排同请求复跑并报告小样本覆盖限制。','同一配对ID的sklearn κ；请求字节比较')
row('M13','提示微扰及行为测试','执行敏感性',['T2024','HK2026'],'等义提示/顺序变化与有预定答案的机制测试分别设计。','旧顺序扰动仅适用旧prompt；当前已有I/F有目的开发控制。',['微扰逐维变化/κ/po','机制正反例通过数','改变前后原文和期望关系'],'微扰不改变实质定义；行为测试覆盖否定、条件、对象、语境承接与排除；构造例标明非政府原文。','预设全部情景均报告；不选最好提示重复，不把控制例通过写成总体分类效度。',['旧指标清单与r3绑定要求.md','00-baseline/legacy-common-manual.md'],'方法可采用，最新正式结果未形成','冻结微扰和行为测试清单；按定义变化同步全部方法。','实际调用日志、配对变化表；有标签/无标签测试分开')
row('M14','抽样区间与设计一致重抽样','抽样不确定性',['HT1952','RWY1992','SVREP'],'按实际抽样单位/层/概率生成配对重抽权重，每次重算四格和非线性指标。','本轮复现旧180 SRSWOR因子与挑战条件WR，5000次；所有历史主区间核对一致。',['逐维95%区间','有效/无定义重抽数','抽样率/FPC','RNG/seed/分位法','区间退化标记'],'旧NHC为60/60普查，重抽因子=1；旧真人家族方案NHC80/140非普查；新4481草案另作设计。','完整披露近似性质与条件对象；不能把零宽区间当语义确定，不能把valid-only分位数称无条件5000次区间。',['recomputed_AC.json','adopted_result_crosscheck.json','human-design-audit/真人复核统计方法预设冻结.json'],'历史复算通过；新设计区间尚待冻结','按新实际设计选survey/svrep或经核验的专用实现，不能沿用旧脚本默认。','NumPy独立重抽已执行；svrep官方源码核查，R未执行')
row('M15','未知值与部分识别','缺失和非抽样不确定性',['HT1952','GS2013'],'未知不填0；条件点值、未知补全范围与抽样CI分开。','v9有179/59配对；补材后为180/60。全量新材料仍有00064未决。',['未知ID/n/设计加权比例','条件κ/P/R/F1','可兼容补全范围','分母为0的NA原因'],'非随机未知不得自动完整案例再权重来代表全框；必要时以上下界说明。','保留NA；报告全部原样本分母；结构比界同时改变本维与其他维，不用全未知0/全未知1代替。',['recomputed_AC.json','指标与变量一致性审查.md'],'历史排除已核对；新方案须锁定规则','每维同步unknown掩码和结果发布规则。','Fraction、结构比单调端点界；没有假定零错误')
row('M16','五维注意力结构与部门比较','主要研究结果',['W2014','C2018','HT1952'],'先计算维度句次总量，再按五维总量归一。','20261007已纠正T/N覆盖率误称结构；后续版本多变，本轮不生成新论文主数值。',['q_gd=T_gd/Σ_dT_gd','部门差100(q_gd−q_hd)','部门内排序','总句次/全0/多标签','覆盖T_gd/N_g仅作不同诊断'],'同维去重、多标签跨维计数；总体先合并总量再归一；零总句次NA。','五维有定义时合计100%；所有表图绑定同一最终输出和分母；占比不是实际行政赋权或效果。',['指标与变量一致性审查.md','00-baseline/legacy-common-manual.md'],'公式口径明确；最终标签尚未验收','合格编码形成后重算全部主表，不移植旧点值。','布尔矩阵求和、HT加权总量；本轮不另装quanteda')
row('M17','同样本机器—参照结构误差','下游测量误差',['GS2013','AP2008'],'在同样本同权重计算方法各自结构及配对差，独立检查主发现。','同180历史比较已记录药监I/E及卫健S/F排序变化；本轮只读该证据。',['机器减参照q百分点差及95%CI','核心方向/排序改变','部门系统误差'],'每方法用自己的五维分母；重抽复用同一权重向量；全量4481与canonical1767估计对象不能相减冒称偏差。','相近比例/区间含0不证明等效；不以聚合结果抵销单元漏判。若设等效界须事前有实质依据。',['统计复算/同样本注意力解释/同180四组注意力比较.md'],'已有历史反例；新版本待检','明确预定主比较及允许解释范围后，随正式参照重算。','paired HT ratio；同一复制权重用于各方法')
row('M18','篇幅、年度系列、重复和归属','注意力结构稳健性',['GS2013','AP2008'],'在事先解释的语料组成情景下重算完整五维结构和全部主比较。','旧指标清单已冻结文件等权/系列等权/最新成员/剔除联合文本/逐一删文；新全框保留重复。',['各情景q及Δ百分点','主导维度与方向反转清单','零命中文件数','重复抓取与跨年度制度延续区分'],'文件等权先算文件q；系列须注明先合并再归一或均值；重复正文不同语境不当然同一测量。','全部预定情景完整报告，不为稳定结论删情景；没有机械0.80阈值。',['旧指标清单与r3绑定要求.md','00-baseline/legacy-family-map.json'],'历史方案齐全，须绑定新全量输出','在冻结情景上报告具体哪些主张稳定、哪些需收缩。','文件/系列元数据，leave-one-document-out；文件bootstrap仅构成敏感性')
row('M19','构念边界情景','定义稳健性',['HS2005','GS2013'],'将有理论依据的备选边界作为明确情景，重算全部分子和共同分母。','旧质量安全、I属性/支持/资格、F获取/可负担/临床管理子类可作旧版敏感性；新版F已排除临床管理难度本身。',['每情景标签数、q及差','受影响维度/ID','主发现变化'],'需同版本真实子类字段；不能由一级标签猜子类；核心定义改变必须新参照，不是只换情景名。','不按更高κ或更均匀部门分布选定义；所有保留主张应明确依赖哪一口径。',['指标依据与理论对齐.md','00-baseline/legacy-common-manual.md','00-baseline/legacy-calibration-changes.json'],'已确认实质定义变化；旧统计不能迁移验收','先冻结主定义，再预先列必要替代边界情景。','显式子类与原文依据；所有五维重新归一')
row('M20','多标签共现与条件比例','可选的联合事件验证',['GS2013','SK18'],'若论文主张F/Ec共同呈现，直接以联合事件Z=F×Ec验证并汇总。','历史稿有共同表达表；本轮不把逐维通过自动视为共现正确。',['共同正例数','F且Ec的四格/P/R/F1（若使用）','条件比例及明确分母','联合事件未知数'],'只有联合事件承担论文核心论证时才纳入必需检验；由现有五维标签派生，不新增构念。','不得用五个边际指标自动证明联合标签；阈值/精度按实际用途预设，不机械增设新0.80门槛。',['旧指标清单与r3绑定要求.md','指标与变量一致性审查.md'],'适用性待主论文主张确认','若保留共现核心结论，先锁联合事件检验；否则保留描述并限缩解释。','布尔联合事件；共同可判掩码')
row('M21','结论证据链与交付核验','结论有效范围',['GS2013','AP2008'],'政策原文/访谈支持含义解释，统计支持文本呈现，二者对应具体主张。','完整Goal要求指标合规后修订整篇论文；本包是方法和历史诊断交接。',['发现—原文—解释—建议映射','数字/图表/引用版本一致','原件/统计/代码/运行记录清单'],'文本频率不识别政策效果或制度逻辑因果；访谈只能使用实际核实材料。','最终论文完成前不得把本报告或部分指标验收标记为完整Goal完成。',['完整Goal指令.md','交接说明.md'],'本支线完成；主Goal仍需独立检验及完整稿交付','主对话按矩阵顺序验收并整合。','总清单、hash manifest、最终文档QA')

# Resolve human-readable evidence names to actual files and frozen inputs.
by_name={Path(k).name:k for k in frozen}
alias={
 'human-design-audit/真人复核统计方法预设冻结.json':ROOT/'outputs/final-three-department-20261008-human-validation-template/human-design-audit/真人复核统计方法预设冻结.json',
 '统计复算/采用结果基线精确复算.json':ROOT/'outputs/编码修订核查-20261008/指标复算准备/采用结果基线精确复算.json',
 '统计复算/同样本注意力解释/同180四组注意力比较.md':ROOT/'outputs/编码修订核查-20261008/统计复算/同样本注意力解释/同180四组注意力比较.md',
}
for entry in matrix:
 resolved=[]
 for label in entry['现有证据']:
  if label in alias:q=alias[label]
  elif label.startswith(('00-baseline/','01-review/')):q=P.parent/label
  elif label.startswith('snapshotted '):q=Path(by_name[label.removeprefix('snapshotted ')])
  elif (P/label).exists():q=P/label
  elif label in by_name:q=Path(by_name[label])
  elif label=='交接说明.md':q=P/label
  else:raise ValueError('Unresolved evidence: '+label)
  assert q.exists() or q.name=='交接说明.md',q
  resolved.append({'label':label,'original':str(q),'frozen_snapshot':str(frozen[str(q)]) if str(q) in frozen else None,'scope':'historical snapshot' if str(q) in frozen else 'current task evidence or generated result'})
 entry['证据文件定位']=resolved

thresholds={'human_independent_reliability':{'metric':'Cohen kappa','by_dimension':['S','E','Ec','I','F'],'minimum':0.8,'data':'frozen manual; two real humans independent first submissions before adjudication'},'machine_classification':{'methods':['rules','LLM'],'metrics':['kappa','precision','recall','f1'],'by_dimension':['S','E','Ec','I','F'],'minimum':0.8,'reference':'credible adjudicated reference under the same frozen definition'},'scope':'Predeclare the primary design-weighted finite-population estimate; preserve raw and department diagnostics. Do not secretly extend or reduce the original target.','NA':'never pass or fill with 1','confidence_intervals':'report 95% and undefined/degenerate diagnostics; crossing .80 is not passing; no new lower-bound>=.80 requirement imposed here','other_metrics':'no mechanical .80 target','forbidden_substitutions':['macro-average for failed dimension','AC1 for failed kappa','post-adjudication agreement for independent reliability','stability or similar attention shares for validity']}
save('完整方法指标矩阵.json',{'scope':'proposed complete method framework with actual historical evidence; not a new data collection or acceptance result','read_inputs_manifest':'input_manifest.json','project_acceptance':thresholds,'sources':S,'matrix':matrix,'not_default_metrics':{'Cronbach_alpha_KMO_factor_analysis':'five co-occurring binary content categories are not reflective items of one latent scale','CVI_Delphi':'do not report without actual expert rating design and original ratings','Krippendorff_alpha':'optional for justified multiple-rater/missing-data design; no substitution for project Cohen kappa','AC1':'optional prevalence-model sensitivity, never passing replacement','AUC_ROC_PR_AUC':'requires meaningful score/threshold continuum; frozen binary labels alone do not justify','JSD_entropy':'only if distributional distance/diversity is a predeclared research question; not reliability or validity proof','significance_tests_580':'old simultaneous region is historical; do not move its conclusion to a new population or denominator'}})

changes=load(frozen[str(ROOT/'outputs/goal-calibration-20261010/00-baseline/legacy-calibration-changes.json')])
old=frozen[str(ROOT/'outputs/goal-calibration-20261010/00-baseline/legacy-common-manual.md')].read_text()
new=frozen[str(ROOT/'outputs/goal-calibration-20261010/00-baseline/legacy-calibration-manual.md')].read_text()
reconstructed=old
for c in changes['changes']:
 assert reconstructed.count(c['before'])==1
 reconstructed=reconstructed.replace(c['before'],c['after'])
diff=''.join(difflib.unified_diff(reconstructed.splitlines(True),new.splitlines(True),fromfile='reconstructed_from_change_log',tofile='actual_frozen_candidate'))
(P/'unlogged_calibration_diff.patch').write_text(diff)

text=['# 完整方法、指标体系与历史统计独立复核\n',
'日期：2026年10月10日。范围：主对话完整八步Goal的“方法恢复与历史诊断”支线；只在parallel-metrics写文件，未修改旧标签、主手册、论文或共享环境，未新跑编码模型。\n',
'## 核心结论\n',
f'已从原始A/C提交及抽样设计独立复算四个阶段（v9、v11、v12、v14）共{meta["total_comparisons"]}组比较；{meta["original_submission_label_checks"]}条“阶段×判读流×单元”的标签逐一追溯到原始提交。精确分数公式与scikit-learn 1.8.0的220组点估计/四格/Ppos交叉核对通过。对三份历史统计共{meta["adopted_comparisons"]}行核查，四格、配对掩码、点估计及适用主95%区间全部一致；其中空NHC挑战占位行只核零样本和NA，未当作真实样本。\n',
'旧概率180的I/F设计加权κ=0.519640/0.641355，与既有采用值0.520/0.641一致。未加权κ=0.495798/0.732143；该差异由设计权重与两方边际改变造成，不是公式错误。概率样本和挑战样本不能合并为总体表现。\n',
'发现一项可证实的版本绑定问题：基线校准变更记录所列candidate SHA不是基线实际候选手册SHA。按变更JSON逐项重建后，仍缺“实质改良I2”的改写、范围句一个措辞及末尾补充依据。应在新冻结记录中补齐，保留旧文件。\n',
'现有原始A/C是AI初判与后续复读；项目记录又明确用户确认了真人事后审定，C后来显示为B。两层身份均保留：可称“AI初判、经真人事后审定的历史参照”，不能写成“新手册下两位真人独立初判”，也不能把AI T候选称真人金标准。\n',
'用户验收要求完整保留：真人协商前逐维κ≥0.80；规则和LLM分别相对同定义可信裁定参照逐维κ/P/R/F1≥0.80。该目标是本项目约束；没有用文献中的别的阈值、AC1、总体一致率或注意力分布相近替代。新手册尚未完成这套验收，不能因本次历史算术通过而开始宣称完整论文已达投稿目标。\n',
'## 完整方法结构\n',
'指标分属内容效度、人工独立信度、机器分类效度、输出稳定性、抽样不确定性与注意力结构稳健性。另设来源/执行完整性作为这些检验共同的数据条件。它们回答不同问题，不能互相替代。以下为可扫描矩阵，完整字段、公式/条件、来源阅读层级、验收与待办见'+link(P/'完整方法指标矩阵.json')+'。\n',
'|步骤|参考做法|必要指标或记录|验收与现状|\n|---|---|---|---|']
for r in matrix:
 text.append('|'+r['id']+' '+r['步骤']+'|'+r['参考的具体方法']+'（'+','.join(r['参考来源'])+'）|'+'；'.join(r['指标或记录'])+'|'+r['验收要求']+' 当前：'+r['本轮状态']+'|')
text += ['\n## 历史抽样与复算口径\n',
'旧概率样本在剩余canonical正文代表框内分部门简单随机不放回抽样：药监947抽60，医保760抽60，卫健60全查。其设计权重依次为947/60、760/60、1，总体1767。每个正文族只取代表不等于覆盖全部家族成员；它不推断全量4481，也不构成新文档外部验证。未加权ALL是各部门均60条的样本混合。挑战60由旧机器I/F阳性富集、必要时回退任一维阳性，药监/医保各30，卫健未抽；没有总体设计权重。\n',
'本次所有“加权κ”都是先按入样概率估计四格，再代入普通名义κ。五维是五个可共存二元标签，没有从安全到公平的有序等级。scikit-learn的sample_weight传入设计权重，weights=None；ordinal weighted κ的linear/quadratic给类别差距赋权，是另一概念。\n',
'四格固定顺序为a=A1C1、b=A1C0、c=A0C1、d=A0C0；N=a+b+c+d。po=(a+d)/N，pA=(a+b)/N，pC=(a+c)/N，pe=pA·pC+(1−pA)(1−pC)，κ=(po−pe)/(1−pe)。独立精确实现另用等价式κ=2(ad−bc)/[(a+b)(b+d)+(a+c)(c+d)]。Ppos=2a/(2a+b+c)，Pneg=2d/(2d+b+c)。分母为0保留NA。\n',
'### v14概率180：未加权原始四格与边际\n',
'|维度|a/b/c/d|A+/C+|A−/C−|κ|po|Ppos|Pneg|\n|---|---|---|---|---:|---:|---:|---:|']
for r in rows:
 if (r['stage'],r['component'],r['group'],r['weighting'])==('final_v14','probability_canonical','ALL','unweighted'):
  vals=[fmt(r['metrics'][k]['estimate']) if r['metrics'][k] else 'NA' for k in ['kappa','agreement','positive_agreement','negative_agreement']]
  text.append(f"|{r['dimension']}|{'/'.join(map(str,r['raw_cells']))}|{r['A_positive_n']}/{r['C_positive_n']}|{r['A_negative_n']}/{r['C_negative_n']}|"+'|'.join(vals)+'|')
text += ['\n### v14概率180：设计加权四格与指标\n','加权四格是估计总量，和为1767，不是受检人数。加权正边际分别是a+b、a+c；负边际是c+d、b+d；JSON同时保存精确分数和边际比例。\n','|维度|a/b/c/d（精确）|κ [主95%区间]|po|Ppos|Pneg|\n|---|---|---|---:|---:|---:|']
for r in rows:
 if (r['stage'],r['component'],r['group'],r['weighting'])==('final_v14','probability_canonical','ALL','eligible_design_weighted'):
  ci=r['ci95']['kappa']; vals=[fmt(r['metrics'][k]['estimate']) for k in ['agreement','positive_agreement','negative_agreement']]
  text.append(f"|{r['dimension']}|{' ; '.join(r['weighted_cells_exact'])}|{fmt(r['metrics']['kappa']['estimate'])} [{fmt(ci['low'])}, {fmt(ci['high'])}]|"+'|'.join(vals)+'|')
text += ['\n### v14挑战60：条件诊断，未与概率样本合并\n','|维度|a/b/c/d|A+/C+|A−/C−|κ|po|Ppos|Pneg|\n|---|---|---|---|---:|---:|---:|---:|']
for r in rows:
 if (r['stage'],r['component'],r['group'],r['weighting'])==('final_v14','enriched_challenge','ALL','unweighted'):
  vals=[fmt(r['metrics'][k]['estimate']) if r['metrics'][k] else 'NA' for k in ['kappa','agreement','positive_agreement','negative_agreement']]
  text.append(f"|{r['dimension']}|{'/'.join(map(str,r['raw_cells']))}|{r['A_positive_n']}/{r['C_positive_n']}|{r['A_negative_n']}/{r['C_negative_n']}|"+'|'.join(vals)+'|')
text += ['\n所有部门、阶段的四格、原始正负边际、设计权重、κ/po/Ppos/Pneg、配对ID/排除ID及95%区间都在'+link(P/'recomputed_AC.json')+'。这里的A/C比较是对称一致性，不把A或C指定为语义真值来报方向性precision/recall。Ppos与相同四格的F1代数相等，并不是第二份独立效度证明。\n',
'## 差异属于哪一种问题\n',
'|类型|证据|处理判断|\n|---|---|---|',
'|统计公式错误|220组独立精确/官方软件一致；180条既有记录核对无不匹配|在所检查A/C四格、点估计及主区间范围内没有发现公式错误；不能扩写为全部历史代码均无错。|',
'|权重/总体口径变化|概率I κ未加权0.495798、设计加权0.519640；F为0.732143/0.641355|分别对应均衡样本混合与1767代表框，不以更高点值选择口径。|',
'|材料/可判分母变化|v9概率00919、挑战02086双方五维待定，逐维配对179/59；v11补料转为180/60|原值不回写；报告材料补全和掩码改变，不能把它叫同一材料上的信度提升。|',
'|实际复读标签变化|v11→v12仅A在01432的S/E由0变1；v12→v14没有五维标签变化，但有替代AI来源复读身份|保存版本差和实际执行者；不是计算修复，也不是完整新独立验证。|',
'|真实同版判读分歧|概率I：01955、02220均A0/C1；概率F有6处，挑战I/F有5/6处|这些导致低κ；本报告只定位分歧，不凭统计决定谁对。|',
'|定义变化|旧F纳保障获取、可负担和临床管理难度；基线F要求公平联系并排除仅临床管理难度。旧S纳明确质量安全，基线S要求药物风险关系|旧标签对新定义属于参照迁移诊断，不能通过重新算κ称新定义验证。|',
'|聚合分母变化|历史指标审查发现T/N覆盖被称为注意力；正确主结构为T/Σ五维T|不能只改表头；占比、百分点差、区间和情景均须按共同分母重算。|',
'|版本元数据错误|candidate记录SHA=3e7ff8…92503；真实候选快照SHA=dc26bf…acd50f|基线快照本身与snapshot_manifest相符；过时的是内部变更记录。新冻结前补记I2及附加依据。|',
'|身份/用途命名变化|AI原始提交与替代agent复读；后续文件记“user-confirmed retrospective human review”，C显示B|保留AI初判和真人事后审定两个事实；不能重命名为真人独立初判。|',
'\n全部实际标签变化及分歧理由见'+link(P/'label_changes_and_disagreements.json')+'；未记录的校准差异见'+link(P/'unlogged_calibration_diff.patch')+'。I与F全部分歧ID如下，按概率与挑战分别列，不增加或替换任何标签。\n',
'|样本|维度|分歧ID|\n|---|---|---|']
D=load(P/'label_changes_and_disagreements.json')
for c in ['probability_canonical','enriched_challenge']:
 for d in ['I','F']:
  ids=[r['id'].removeprefix('RECODE25-') for r in D['final_disagreements'] if r['component']==c and r['dimension']==d]
  text.append('|'+c+'|'+d+'|'+', '.join(ids)+'|')
text += ['\n## 区间和新检验设计的边界\n',
'旧180主重抽为每部门M~Multinomial(59;1/60,…,1/60)，因子a_i=1+sqrt(1−60/N_h)[(60/59)M_i−1]；NHC的因子恒1。本轮用新的实现从冻结标签生成同样5000组复制权重和指标，再与历史文件逐项核对。挑战60采用固定挑战集内部的条件WR，只描述该富集集合的重抽变异。来源文件重抽是另一个构成敏感性，本轮没有冒称已复算其历史全部区间。\n',
'三套抽样设计必须分开：①旧180推断1767个canonical代表，NHC普查；②20261008“真人方法预设”是部门内80个正文族、每族再抽1单元，族框1031/841/140，w=F_g·k_family/80，NHC不是普查；该文件明确真人结果未收到、实际重抽0次；③本轮00-baseline草案目标是完整4481个单元，尚未定n/种子，可用部门分层SRS或预定补样。不能把①的n−1/FPC直接复制到②，更不能把②的79次ultimate-cluster WR近似直接称为③的正式方案。\n',
'家族方案预设的无FPC WR近似对线性总量方差的期望保守性，不保证非线性κ/F1百分位区间覆盖。新设计的区间必须由实际抽样方案重新核定。若采用基础样本加独立分层补样，联合概率为1−(1−n_g/N_g)(1−m_gh/N_gh)，去重后不能任意重抽凑人数；方差还需联合纳入概率或经过核定的复制方案。\n',
'报告95%区间、无定义复制数和实际正例分母。区间跨0.80不是达标；零宽区间不是语义确定；2个正例得到召回1不能证明罕见类识别充分。本支线没有擅自追加“所有区间下界≥0.80”门槛，也没有放松既定点值目标。\n',
'## 方法来源与阅读层级\n',
'下列每条只承担具体方法职责。保留原论文、官方实现和项目操作化的区别；本研究的0.80及实际取样数量来自项目要求，不冒称文献通则。\n']
for k,s in S.items():text.append(f'- **{k}** [{s["title"]}]({s["url"]})。实际阅读：{s["actual_read_scope_this_audit"]} 用途：{s["supported_method"]} 边界：{s["not_supported"]}\n')
text += ['\n## 交付与复现\n',
'输入已按SHA复制到本目录snapshots，主输入共85份，约25.2 MB，另有4份补充方法/暴露记录/官方实现源码/更新后Goal快照；包括本轮00-baseline、指定指标过程文件、原始A/C材料及提交、各阶段标签、旧抽样设计与既有采用统计。主对话工作期间更新了完整Goal，初始快照及更新后快照并存，统计输入未变。原刊/官方工具网页的获取状态另在primary-sources/download_manifest.json，失败获取按失败保留，不冒称取得全文。统计只从快照读取，不导入旧统计模块。\n',
'执行环境为本支线独立.venv；Python3.14.4，具体依赖见requirements-lock.txt。该环境通过system-site-packages使用已有NumPy/SciPy，同时锁定了所用版本；如异地复现可用锁文件建立干净环境。没有修改主对话共享.venv。\n',
'```bash\ncd "'+str(P)+'"\n.venv/bin/python recompute.py\n.venv/bin/python build_report.py\n```\n',
'已有input_manifest.json时不得再次--freeze覆盖。复算前验证全部输入SHA；结果JSON保存脚本SHA、环境和设计。首次两次执行分别因未枚举部门加权行、未单独处理空NHC挑战占位行终止，记录于execution_attempt01/02；修复只补齐核对范围，未改变标签或统计公式。成功记录为execution_attempt03.log；补齐显式加权负边际后的最终成功记录为execution_attempt04.log。\n',
'主对话接下来应先补齐校准手册变更绑定并冻结共同判据；方法—手册—盲评—指标可以按证据循环，但用过的检验材料随修订转为开发，不能降阈值或更名AI身份。正文每张表下应注明对象、样本量、分母、编码/计算口径、来源及必要权重、区间和NA。之后落实实际真人独立初判与裁定，再按新方案实施逐维验收；全部必要指标合规后才启动完整正文整合。这个报告完成的是支线任务，不能作为整篇论文Goal完成证明。\n']
(P/'完整方法与历史统计复核报告.md').write_text('\n'.join(text))

handoff=f'''# 给主对话的简明交接

本支线已完成指定过程文件恢复、完整21步指标矩阵、旧180/挑战60的独立A/C复算与采用结果核对。只写入本目录，未修改旧标签、手册、正文或共享环境；没有新模型调用。

1. **先读** {link(P/'完整方法与历史统计复核报告.md')}；机器可读完整矩阵为 {link(P/'完整方法指标矩阵.json')}。
2. **数值可采用为历史诊断**：220组精确公式/官方sklearn比较通过；1920条阶段标签逐项回原提交核对；三份既有统计180行核对无数值差异。概率180设计加权κ（S/E/Ec/I/F）=0.943860/0.819957/0.878617/0.519640/0.641355。挑战60单列，不能混入。详见 {link(P/'recomputed_AC.json')} 与 {link(P/'adopted_result_crosscheck.json')}。
3. **确需处理的版本问题**：legacy-calibration-changes.json内部candidate SHA过时；逐项重建仍缺I2“实质改良”修订、范围措辞及补充依据。实际基线候选SHA为dc26bf77c62c2f60f6d3e71a1fe1d7aca0d63f12a516b72160519eef06acd50f。见 {link(P/'unlogged_calibration_diff.patch')}。请在新冻结记录补记，别改历史证据。
4. **分清真实身份/用途**：旧A/C为AI初判/复读，后续记录有用户确认的真人事后审定（C显示为B）；这不等于新共同手册下真人独立首次判断。AI T不称真人金标准。旧样本已有开发暴露；保留诊断身份。
5. **定义/设计不能混版**：旧宽F/质量S与本轮定义有实质差别。旧180总体1767，NHC全查；历史真人240为家族两阶段，NHC非全查；新草案4481尚待n和种子。三者权重/CI分别适用。
6. **验收不变**：真人逐维κ≥.80，两机器对同定义可信裁定参照逐维κ/P/R/F1≥.80；内容效度、稳定性、未知/运行质量、抽样区间和注意力稳健性另按矩阵核定，不机械加无关量表指标。历史算术通过不能表示这些新检验已经完成。

复现：本目录`.venv/bin/python recompute.py`，再运行`build_report.py`。原始快照及SHA在input_manifest.json及supplemental_input_manifest.json。成功执行、依赖锁和两次中止修复记录均保留。后续GPT-6.1 Sol/ultra仅按实际执行记录标识；本支线未伪称旧A/C或旧模型执行由新模型完成。
'''
(P/'交接说明.md').write_text(handoff)
required={'参考来源','参考的具体方法','当前实际实施','指标或记录','适用条件','验收要求','现有证据','本轮状态','下一步','可复用工具与核验'}
assert len(matrix)==21 and all(required<=r.keys() for r in matrix)
assert all(x in S for r in matrix for x in r['参考来源'])
assert not meta['adopted_mismatches'] and all(r['pass'] for r in meta['baseline_snapshot_checks'])
save('delivery_QA.json',{'matrix_steps':len(matrix),'sources':len(S),'required_matrix_fields_complete':True,'source_ids_resolve':True,'adopted_crosscheck_pass':True,'all_12_baseline_hashes_pass':True,'historical_diagnostic_only':True,'new_models_run':0,'original_labels_changed':False,'shared_environment_changed':False})
outputs=[p for p in P.iterdir() if p.is_file() and p.name!='delivery_manifest.json']
save('delivery_manifest.json',{'files':[{'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(outputs)],'snapshots_manifest_sha256':sha(P/'input_manifest.json')})
print(json.dumps({'report':str(P/'完整方法与历史统计复核报告.md'),'matrix_rows':len(matrix),'sources':len(S),'QA':'pass'},ensure_ascii=False))
