from pathlib import Path
from fractions import Fraction
from itertools import product
import hashlib
import json
import random

BASE = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
OUT = BASE / 'outputs/indicator-alignment-20261007'
read = json.loads((OUT/'只读提取.json').read_text())
manual = BASE/'outputs/autocode-v25-20260927/protocol-v1.3.md'
paragraphs = {p['index']:p['text'] for p in read['current']['paragraphs']}

contracts=[]
def contract(key, variable, definition, denominator, name, permitted, prohibited, positions, manual_lines=None):
    contracts.append(dict(key=key,theoretical_variable=variable,exact_definition=definition,denominator=denominator,preferred_name=name,permitted_conclusions=permitted,prohibited_conclusions=prohibited,current_paragraph_indices=positions,manual_lines=manual_lines or []))

contract('coding_label','五维评价内容是否在政策单元中被实质讨论','Y_igd∈{0,1,?}。1=实质涉及维度d；0=具备完整判读条件且不涉及；?=实质文本/语境缺失等导致不能判定。每单元每维至多一次，可多标签或全0。','单元级分类，不适用占比分母','维度d相关内容标签（编码1/0/待定）',['描述政策要求、证据需求和讨论内容是否出现'],['药品已经安全/有效/经济/创新/公平；政策已实现预期效果'],[44,45,46,47,55,108],[7,9,11,17,19,27,33,41,49,119])
contract('attention_structure','五维可测内容中的相对注意力配置（稿6原操作化）','对来源组g，T_gd=Σ_i Y_igd（仅完整二元标签时）；A_gd=T_gd/Σ_jT_gj。抽样时以各层N_h/n_h估计各维总量，再对五维总量归一。Σ_jT_gj>0时Σ_dA_gd=1。多标签一句对两个维度计两次，是标签句次构成。','该来源组五个维度相关标签句次之和，绝不是全部单元N_g，也不是至少命中一维的独立单元数','五维注意力结构占比（%）',['描述所纳入文本、所选五维框架内部的相对内容结构；按同一维度比较部门结构占比'],['实际评审赋权、个体认知、部门固有偏好、制度逻辑因果效应或政策效果'],[1,11,12,22,25,28,29,39,47,56,64,65,68,70,72,73,74,76,80,88,104,105,106],[9,11,111])
contract('content_coverage','某维内容在全部纳入政策文本中的覆盖程度','P_gd=T_gd/N_g；三态时分别报告P_gd^1=T_gd^1/N_g与P_gd^?=T_gd^?/N_g，0比例为1−P_gd^1−P_gd^?。五维可重叠，Σ_dP_gd通常不为1。','来源组所有纳入分析的意义单元N_g；不删全0，不把待定填0','维度d内容覆盖比例（编码1）／待定比例',['描述该组全部单元中相应内容的出现程度及可判情况；可作框架覆盖诊断'],['直接称为稿6的注意力结构占比；低覆盖=部门忽视该维；与别组比较后直接断定结构份额更低'],[1,25,29,47,56,57,58,59,65,70,71,72,74,76,77,78,79,80,104,105,106],[9,11,111])
contract('union_coverage','五维框架至少覆盖一维的文本比例','C_g=Σ_i 1{Σ_dY_igd>0}/N_g。须有单元级联合标签；不能把五维边际比例相加代替。待定可另构造已知覆盖/可能覆盖上下界。','来源组全部分析单元N_g','五维框架单元覆盖率（至少一维）',['判断五维框架能测到多少独立单元'],['把Σ_dP_gd叫至少一维覆盖率；把未覆盖解释为政策无价值'],[47,55,59,106],[11,95,111])
contract('overall_structure','跨来源组的总体五维结构','先合并估计总量：A_all,d=Σ_g T_hat,gd / Σ_gΣ_jT_hat,gj。等价于按各组五维总命中量加权组内结构比。','全部来源组五维估计总命中句次；权重为总命中量而非N_g','总体五维注意力结构占比',['合并语料范围内的总体内容构成'],['按N_g加权各组结构比后称句次加总总体结构；把A/C两份相同样本当样本翻倍'],[47,56,59],[111])
contract('overall_coverage','全部语料内某维覆盖比例','P_all,d=Σ_gT_hat,gd/Σ_gN_g=Σ_g(N_g/N_all)P_hat,gd。该N加权对覆盖比例正确，对结构比不正确。','全语料全部分析单元N_all=4924','总体维度内容覆盖比例',['总体语料内容覆盖诊断'],['把按N加权覆盖比例误称注意力内部结构'],[47,56,59,76,79],[111])
contract('file_equal','来源文件或年度系列等权的结构比较','结构口径：先对每文件f计算A_fd=T_fd/Σ_jT_fj，再对有定义的文件作等权平均；零命中文件结构未定义，须单列并说明排除。系列等权须定义先合并系列总量再算比，还是成员份额均值，两者不同。覆盖口径：P_fd=T_fd/N_f，再等权，含全0文件。','文件内五维命中总句次（结构）或文件全部单元N_f（覆盖）；两者不得混用','文件／年度系列等权注意力结构占比；文件／系列等权内容覆盖比例',['检查长文件、年度重复和归属处理对相应指标的描述影响'],['把当前基于P的等权稳定性直接当A结构稳定性；把零命中文件当结构全0且不说明'],[39,43,76,80,122],[111])
contract('pending_structure','待定完成后尚未完全识别的五维内容构成','每维完整总量t_gd在已判1总量与1或待定总量之间。结构比t_gd/Σ_jt_gj的最不利界须同时改变本维与其他维。全部待定置0或全部置1两个归一化结果一般不是逐维结构比上下界。','未知完成后全组五维总命中句次，随机/未知分母','兼容待定任意补全的注意力结构范围／同时置信包络',['在Σ_jt_gj>0域上给出兼容待定与抽样误差的保守范围'],['直接复用固定N差值CI；把两位AI范围称置信区间；把所有待定0/所有待定1归一结果当可靠极值'],[47,56,59,65,68,72,74,79,80],[17,119,168])
contract('ac_agreement','两位独立参照的标注一致性','在双方可判的固定配对集合M_d上，κ_d=(p_o−p_e)/(1−p_e)，p_o为相同标签比例，p_e由二者边际类别比例计算；待定排除情况和M_d另报。','该维双方可判的实际配对n；不是N_g，也不是五维标签句次之和','A—C协商前一致性（目前为agent参照间一致性）',['相同规范下两个判读者在该固定集合的一致程度'],['真人验证已完成；两者共误判被排除；政策部门排序获得验证'],[49,50,53,54,108,112],[99,103,109,168])
contract('machine_kappa','机器方法相对某参照的分类一致性','同一维度、同一版本、同一固定共同可判集合上的机会校正κ；分别作规则—A、规则—C、LLM—A、LLM—C。当前属于开发复核。','每维每对的共同可判n；报告掩码、覆盖和排除待定数','方法—参照一致性κ（开发材料）',['相对固定参照的机会校正一致性；经固定口径可比较开发改善'],['κ是内容占比、临床疗效或可发表证书；agent参照是真人金标准；后设0.8是通用期刊门槛'],[49,50,51,53,54,118],[99,103,109,168])
contract('classification_prf','相对明确参考标签的阳性识别表现','P=TP/(TP+FP)；R=TP/(TP+FN)；F1=2TP/(2TP+FP+FN)。TP等以参考1为相关内容，预测1为识别相关内容。两位参考分别计算，不能挑更接近机器者。','P的分母为预测1数；R为参考1数；F1为2TP+FP+FN；均不是语料N或五维命中总量','精确率P、召回率R、F1（相对A/C的开发复核表现）',['判别误报与漏报的方向及其规模'],['R叫一致率；P叫总体准确率；高F1证明政策结论；把参考的偏差当真实标签消除'],[49,50,51,53,54],[99,103,109])
contract('observed_agreement','固定配对集合上的观察一致率／分类准确率','p_o=(TP+TN)/n。若一方被指定参考可称相对参考准确率，但当前A/C是agent不是真值，优先观察一致率。类别失衡时不能仅报此值。','实际共同可判配对数n','观察一致率（%）；相对参考准确率须限定参考性质',['该集合上标签相同的频率'],['多数阴性下高一致率证明阳性识别好；κ与一致率同义'],[49,50,53],[103,109])
contract('evaluable_coverage','比较指标可判覆盖','|M_d|/|F|，M_d为固定共同可判掩码，F为H427或1268相应框；A/C自身掩码与机器对照掩码不同，不能混用。','相应验证/开发框条数（H427=427等）','共同可判覆盖率（%）',['交代条件κ/P/R/F1适用于多少材料'],['把可判覆盖率叫维度内容覆盖率；把394/391两个掩码当同一391配对全集'],[50,53],[17,103,119])
contract('uncertainty','估计不确定性及待定部分识别范围','κ/P/R/F1的文件聚类bootstrap只针对相应固定开发材料；主分析的有限总体超几何反演针对分层抽样总量。新结构区间由同一联合总量覆盖事件单调映射。','严格绑定各自统计对象与设计；没有统一通用分母','边际置信区间／同时置信包络／待定补全范围，三者分别注明',['在条件、抽样框和参照函数明确的范围内量化不确定性'],['跨统计对象搬用CI；把补全范围当抽样CI；把A/C点差当95%CI；让CI覆盖AI系统性误判或选择规则偏差'],[53,56,59,65,68,72,106],[99,103])
contract('definition_sensitivity','操作定义边界变动的影响','对每情景v重新生成T^(v)，结构A^(v)=T^(v)/Σ_jT_j^(v)，覆盖P^(v)=T^(v)/N；ΔA_d或ΔP_d以百分点分别报告。只删某维标签也会改变其余四维结构占比。','结构情景的五维新总命中量；覆盖情景继续固定N','结构占比变化（百分点）；内容覆盖比例变化（百分点）',['检验定义边界下对应指标及预定方向是否稳定'],['旧P变化直接当ΔA；只重算被删除维度的结构；覆盖15方向稳定直接推出结构15方向稳定'],[39,55,74,76,80],[25,51,111,137])
contract('scoring_weight','实际行政评审的维度赋权','需正式评分表、适用程序规则或决策记录中的权重。文本频率及结构比均不是赋权测量。','实际评分/决策模型定义；当前未获取并估计该变量','实际评审权重（本研究未测量）',['仅依正式规则描述某程序规定的权重；访谈个人表述限定来源'],['由A或P推断部门实际权重；创新性结构高=实际评分更高'],[22,29,73,86,88,90,94,105,106,116],[9,111])
contract('policy_effect','政策实施效果／部门协调效果','需真实实施结果变量及合适研究设计；目前是政策文本要求、条文解释与有限访谈，没有临床结局、药物可及改善或因果政策效果估计。','无可由现有文本编码推导的效果分母','政策安排／评价要求／解释线索；效果未在本研究估计',['比较政策要求、评价对象、证据要求和决策用途；提出有依据的建议'],['编码1=政策有效；经济性内容多=基金绩效改善；公平内容多=实际公平改善；权重差异=协调失灵'],[39,55,62,84,85,86,88,90,94,97,98,99,102,104,106],[9,111])

dimensions = [
 {'dimension':'S','theoretical_name':'安全性','label_name':'安全性相关内容','definition':'药物损害、风险识别控制、不良反应/毒性等及明确药品质量安全；风险不足或要求补证同样可能为1。','boundary':'数据/基金/一般生产安全排除；仅质量安全来源单列敏感性。','manual_lines':[19,21,23,25],'current_paragraphs':[44,45,108]},
 {'dimension':'E','theoretical_name':'有效性','label_name':'有效性相关内容','definition':'药物防治效果、临床获益、疗效终点和与效果判断有明确联系的证据；不是临床有效已经实现。','boundary':'单纯临床试验程序、行政有效期、无效果联系的证据质量不自动纳入。','manual_lines':[27,29,31],'current_paragraphs':[44,45,108]},
 {'dimension':'Ec','theoretical_name':'经济性','label_name':'经济性相关内容','definition':'药品价格费用、治疗成本、支付责任、成本效果、预算/基金影响等；并非仅限医保支付程序。','boundary':'行政收费/一般项目经费排除；患者药费负担可与F并列，标签不互斥。','manual_lines':[33,35,37,39],'current_paragraphs':[44,45,86,108]},
 {'dimension':'I','theoretical_name':'创新性','label_name':'创新性相关内容','definition':'药物创新属性、明确研发创新支持、创新资格比较优势，按v1.3来源子类型留痕。','boundary':'创新药名称或加快程序名称本身不够；不得把注册创新身份等同支付比较价值。','manual_lines':[41,43,45,47,132,134,164,166],'current_paragraphs':[44,45,73,84,108]},
 {'dimension':'F','theoretical_name':'公平性（医保名称）','label_name':'公平性相关内容（保障获取等研究操作口径）','definition':'保障获取、患者可负担、药品临床管理难度及未细分公平性信息要求；这是较宽的保障获取构念。','boundary':'不把全部内容解释成狭义分配公平；一般管理/人群名称/企业公平竞争排除；不与卫健可及性视为同义。','manual_lines':[49,51,53,55,57,123,156],'current_paragraphs':[44,45,55,74,80,94,108]},
]

issues = [
 {'severity':'必须修正','issue':'主要变量分母从五维标签句次总和漂移为来源组全部单元N','original_location':{'paragraph':46,'quote':'以某维度命中句次占该部门五维度命中句次合计的比重作为注意力占比'},'current_locations':[25,47,56,59,65,72,76,79,105], 'action':'保留原研究问题时，恢复结构占比为主变量；现覆盖比例保留为辅助指标，并分别标明分母。不能只给旧值改表头。'},
 {'severity':'必须修正','issue':'现有同时差值区间和零共同方向结论针对覆盖比例，不是结构占比','current_locations':[56,65,66,68,70,72,104], 'action':'由旧580个总量联合覆盖事件推导结构比保守界，再重做结构差值与A/C共同方向。旧0共同方向不得直接搬用。'},
 {'severity':'必须修正','issue':'总体归一和聚合次序','current_locations':[47,56,59,76], 'action':'结构先合并各层/组总量后除五维总量；勿用按N加权组结构。文件/年度系列等权要按结构比重算，并报告零总命中文件。'},
 {'severity':'必须修正','issue':'五项定义敏感性目前是固定N覆盖变化，不能转称结构变化','current_locations':[39,74,76,80], 'action':'每个情景重算全部五维分子、共同结构分母、全部预定方向；其他维度因归一化也变化。'},
 {'severity':'必须修正','issue':'摘要、理论、框架图、结语对关注结构的称谓需与新主指标同步','current_locations':[1,11,12,22,25,28,29,39,64,88,104,105,106], 'action':'引言和理论明确结构/覆盖两层指标；图1左框改为分别测量结构与覆盖，图2结构图须重画。当前“前者描述文本关注结构”不能只由固定N比例支撑。'},
 {'severity':'应明确而非重算','issue':'五维标签1/阳性不是药物被评价为好，也不是政策实施效果','current_locations':[44,45,47,49,55,65,73,76,86,94,104,108], 'action':'首次明确“编码1表示实质相关内容”；表头优先“相关内容/编码1”，正文提及阳性时绑定编码语义。'},
 {'severity':'应保留限定','issue':'A/C与机器κ/P/R/F1不是内容结构统计量或真人效度证明','current_locations':[49,50,53,54,106,112,118], 'action':'当前开发复核限定正确，应保留；不因恢复结构而重算不相关的分类指标，但所有n、配对掩码、参考身份必须不变。'},
 {'severity':'手册增补','issue':'v1.3冻结的是单元语义，缺少聚合分母和指标命名契约','manual_lines':[7,9,11,107,109,111], 'action':'新增独立统计说明而不修改既有标签判据：结构T/ΣT、覆盖T/N、未定处理、总体/文件等权、分类指标与政策效果分开。'},
]

location_groups = [
 ('摘要与研究问题',[1,11,12,22,25,28,29],'明确主变量是五维内容内部结构占比，另将覆盖比例作为辅助诊断。'),
 ('定义与估计方法',[39,47,56,59],'并列定义分子、分母、加权方式、待定策略和结构区间；删除把两类指标混为一项的语句。'),
 ('主结果表图与推断',[57,58,59,64,65,66,67,68,70,71,72,73],'表3/图2若成为主结构表图，须重算并补全部结构比；旧覆盖表可转附表；表4按结构差值重算。'),
 ('平行方法与敏感性',[74,75,76,77,78,79,80],'机器全量数据可直接由未舍入总量重算结构；五项定义、文件/系列等权、最新成员、联合文本、留一来源均按结构指标重算。'),
 ('理论解释与结语',[88,90,104,105,106],'政策条文含义和决策用途结论可以保留；涉及较高、排序、零共同方向、结构与覆盖的结论须使用相应新结果。'),
 ('附录与编码规范',[108,112,116,118,122],'标签规范、分类性能与实际赋权分开；增加统计指标契约，现A/C身份及开发材料限定保留。'),
]
locations=[]
for group,indices,action in location_groups:
    for i in indices:
        locations.append({'group':group,'paragraph_index_zero_based':i,'quote':paragraphs[i],'action':action})

def ratio_bounds(lower,upper,d):
    if not (len(lower)==len(upper) and all(0<=a<=b for a,b in zip(lower,upper))):
        raise ValueError('invalid rectangle')
    if sum(upper)==0:
        return None
    ld=lower[d]+sum(upper[j] for j in range(len(lower)) if j!=d)
    ud=upper[d]+sum(lower[j] for j in range(len(lower)) if j!=d)
    # Restrict to vectors with a strictly positive total. Zero-only boxes have no ratio.
    low=Fraction(lower[d],ld) if ld else Fraction(1)
    high=Fraction(upper[d],ud) if ud else Fraction(0)
    return low,high

intervals=[(l,u) for l in range(4) for u in range(l,4)]
checks=0
boxes=0
undefined_boxes=0
for selected in product(intervals,repeat=3):
    L=[v[0] for v in selected]; U=[v[1] for v in selected]; boxes+=1
    if sum(U)==0:undefined_boxes+=1;continue
    b=[ratio_bounds(L,U,d) for d in range(3)]
    for point in product(*(range(l,u+1) for l,u in zip(L,U))):
        if not sum(point):continue
        for d in range(3):
            q=Fraction(point[d],sum(point));assert b[d][0]<=q<=b[d][1]
            checks+=1
rng=random.Random(20261007)
five_checks=0
for _ in range(500):
    L=[];U=[]
    for d in range(5):
        l=rng.randrange(11);u=rng.randrange(l,11);L.append(l);U.append(u)
    for point in product(*[(l,u) if l!=u else (l,) for l,u in zip(L,U)]):
        if not sum(point):continue
        for d in range(5):
            lo,hi=ratio_bounds(L,U,d);q=Fraction(point[d],sum(point));assert lo<=q<=hi;five_checks+=1

math_audit = {
 'answer':'可以。须在同一至少95%的联合覆盖事件上，针对非负总量与正总分母作单调变换；不是沿用旧固定N的差值区间。',
 'parameter':'完整标签总量t_gd；每维固定已判1总量a_gd≤t_gd≤b_gd=已判1或待定总量。',
 'joint_event':'旧580项家族同时覆盖所有层×两位参考×五维×两端点。按层求和得每组每维L_gd≤a_gd≤t_gd≤b_gd≤U_gd。此事件成立时所有派生结构界同时成立，不需因派生更多结构比/差值再做一次Bonferroni。',
 'lower_formula':'A_gd_lower=L_gd/(L_gd+Σ_{j≠d}U_gj)',
 'upper_formula':'A_gd_upper=U_gd/(U_gd+Σ_{j≠d}L_gj)',
 'domain':'每组Σ_jt_gj>0；L和U必须是同组同参考同单位的非负总量，且0≤L≤U。若使用比例端点，所有维度须同N，同一比例单位，使共同N抵消。',
 'derivatives':'对r=x_d/(x_d+s)，∂r/∂x_d=s/(x_d+s)^2≥0；对每个其他x_j，∂r/∂x_j=−x_d/(x_d+s)^2≤0。由此本维取L、其他维取U得到下界；反向得到上界。',
 'not_sharp':'联合矩形可能包含不兼容的总量组合，所以界保守且一般不锐利；不要求维度或A/C相互独立。',
 'pair_difference':'Δ_gh,d=A_gd−A_hd的同时界为[A_gd_lower−A_hd_upper,A_gd_upper−A_hd_lower]。两组的结构比须均有定义。A/C共同方向须在新差值界上分别同向严格排除0。',
 'within_group':'若要比较同一组d与k，可由矩形构造[A_gd_lower−A_gk_upper,A_gd_upper−A_gk_lower]，仍保守；若原计划仅检验组间同维，则勿事后把探索内部排序说成预先规定推断。',
 'zero_denominator_cases':[
   {'case':'Σ_jU_gj=0','result':'所有候选总量均0，结构未定义，记NA/无五维相关内容；不能填0或均分20%。'},
   {'case':'L_d+Σ其他U_j=0，但ΣU>0','result':'其他维U全0、本维可能正；正总量域上本维结构必为1，下界可设1。若只要安全但不锐利界，设0仍保守，必须显式标记退化，不能直接算0/0。'},
   {'case':'U_d+Σ其他L_j=0，但ΣU>0','result':'本维U=0而其他维可能正；正总量域本维结构恒0，上界应设0，不能直接算0/0。'},
   {'case':'ΣL=0<ΣU','result':'矩形包含全0向量。公式包络只对正总量完成有效；另标记“零总量完成仍可能”，或用样本中固定保留的至少一个已知正标签排除零总量。不能默认为所有未知完成的结构均有定义。'},
 ],
 'zero_point_estimate':'Σ_j T_hat_gj^1=0时已判1构成点估计未定义，即使未知完成的结构可能有定义。图表点记NA，并单独列可识别范围。',
 'counterexample_fixed_N':'N_A=N_B=100，五维计数A=(10,90,0,0,0)，B=(5,5,0,0,0)。第一维覆盖A=10%>B=5%，结构A=10%<B=50%；连方向都可反转，旧覆盖差值CI不能作结构CI。',
 'counterexample_pending':'两维已判1=(10,90)，待定=(10,90)。全待定0及全待定1都给第一维10%，但只将第一维待定补1可达20/110=18.18%，只将第二维补1可低至10/190=5.26%。因此不能把两种统一补全归一结果当极值。',
 'precision':'使用未舍入的分层总量和端点；正文四舍五入值仅展示，不能决定是否严格排除0。',
 'validation':{'three_dimensional_integer_boxes':boxes,'zero_only_boxes':undefined_boxes,'exhaustive_positive_vectors_dimension_checks':checks,'five_dimensional_boxes':500,'five_dimensional_corner_dimension_checks':five_checks,'random_seed':20261007,'all_passed':True},
 'implementation_source':str(OUT/'build_alignment_audit.py'),
}

rounded_illustrations=[]
for row in read['current']['tables'][2]['rows'][1:]:
    vals=[float(c.split('\n')[0]) for c in row[3:]]
    rounded_illustrations.append({'group':row[0],'reference':row[1],'coverage_percent_from_display':vals,'sum_coverage_percent':round(sum(vals),2),'structure_percent_illustration_only':[round(v/sum(vals)*100,2) for v in vals],'not_final_numbers':True})

report = {
 'audit_date':'2026-10-07',
 'read_only':True,
 'input_documents':{k:{a:v[a] for a in ['path','sha256']} for k,v in read.items()},
 'manual':{'path':str(manual),'sha256':hashlib.sha256(manual.read_bytes()).hexdigest(),'same_hash_confirmed_paths':[str(BASE/'outputs/validation-expansion-20260926/V600/agent-A/五维共用编码协议.md'),str(BASE/'outputs/autocode-v28-review-20261004-111306/protocol-v1.3.md')],'aggregation_denominator_defined':False},
 'main_finding':'原稿6注意力占比是T/Σ五维T；现稿表3/表5/图2是T/N内容覆盖比例。理论名称与统计对象存在漂移，需要主辅指标分离及相关推断/敏感性重算，不能只更名。',
 'contracts':contracts,
 'dimension_contracts':dimensions,
 'issues':issues,
 'locations':locations,
 'table_contracts':[{'table_index':0,'printed_table':'表1','status':'制度逻辑分析性概括，非效应估计；原则可保留'}, {'table_index':1,'printed_table':'表2','status':'分类一致性/识别指标；不因结构分母调整自动变化'}, {'table_index':2,'printed_table':'表3','status':'现值是内容覆盖比例，可保留为辅表；若改主结构表必须重算'}, {'table_index':3,'printed_table':'表4','status':'现值是覆盖比例差值区间汇总；结构主比较须重算'}, {'table_index':4,'printed_table':'表5','status':'现值是机器全量内容覆盖比例，可保留辅表并另算结构'}, {'table_index':5,'printed_table':'表A1','status':'固定配对κ；保持参考/版本/n和开发限定'}],
 'figures':[{'figure':'图1','paragraph_index':35,'used_media':'image3.png','status':'当前左框“分布与覆盖”未分名，建议明确为“分别测量五维内容结构与覆盖”；因果限定正确保留'}, {'figure':'图2','paragraph_index':69,'used_media':'image4.png','status':'当前横轴明确T/N覆盖，与原主变量不同；若作为主结构图必须重画及重算包络，范围改0–100%或适合结构比统一尺度'}, {'unused_media':['image1.png','image2.png'],'status':'DOCX包内残留旧图，不在当前正文引用；不把旧图内容当当前图问题'}],
 'mathematical_audit':math_audit,
 'rounded_illustrations_not_for_manuscript':rounded_illustrations,
 'files_modified':['指标与变量一致性审查.md','指标与变量一致性审查.json','build_alignment_audit.py','只读提取.json','current-只读提取.txt','original_v6-只读提取.txt','image1.png','image2.png','image3.png','image4.png'],
}
(OUT/'指标与变量一致性审查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))

md=['# 指标与理论变量一致性审查（2026-10-07）','',
    '**核心问题已确认：原稿6的注意力占比是某维标签句次÷五维标签句次总和；现稿主要表图用某维标签句次÷全部分析单元N，测量对象已从内部结构转为内容覆盖。两者可分别报告，不能共用名称、数值、差值区间或稳定性结论。** 本审查未修改DOCX。','',
    f'读取[现稿](<{read["current"]["path"]}>)、[原稿6](<{read["original_v6"]["path"]}>)、[CAL-5D-v1.3协议](<{manual}>)。具体定位使用python-docx零基段落序号P，正文节名与原句同时保存在JSON。标签手册固定单元语义，未规定汇总分母，宜新增统计术语说明而非改动已冻结标签判据。','',
    '## 术语契约表','',
    '| 理论变量 | 精确定义与分母 | 规范名称 | 允许结论／限制 | 现稿位置 |','|---|---|---|---|---|']
for c in contracts:
    md.append(f"| {c['theoretical_variable']} | {c['exact_definition']} 分母：{c['denominator']} | {c['preferred_name']} | 可：{'；'.join(c['permitted_conclusions'])}。不可：{'；'.join(c['prohibited_conclusions'])}。 | P{',P'.join(map(str,c['current_paragraph_indices']))} |")
md += ['', '## 五维名称与操作定义','', '| 维度 | 规范标签含义 | 边界与理论解释 |','|---|---|---|']
for d in dimensions:
    md.append(f"| {d['theoretical_name']}（{d['dimension']}） | {d['label_name']}：{d['definition']} | {d['boundary']} |")
md += ['', '## 必须同步修改的位置','']
for i in issues:
    ps=i.get('current_locations',[])
    where='P'+',P'.join(map(str,ps)) if ps else '手册统计说明'
    md.append(f"- **{i['issue']}**（{where}）：{i['action']}")
md += ['', '现表3、表5的名称和分母作为“内容覆盖比例”基本自洽，可以保留为辅助材料。问题是摘要、理论、5.1节、图1及结语仍用这些数值概括“关注结构”。表2和表A1属于固定配对分类指标，恢复结构分母本身不要求重算κ/P/R/F1，但需要保留agent身份、开发材料、共同可判掩码和置信区间局限。','',
    '示意（仅用现表四舍五入数字，不能入正文）：AI A药监安全性覆盖为21.67%，五维覆盖合计47.41%，已判1的内部结构约45.71%；医保经济性覆盖31.60%，内部结构约69.40%。正式结果必须从未舍入加权总量重算。这些只是不同统计对象的演示，不是新的验证结果。','',
    '## 结构比保守界的数学核查','',
    '设同一联合覆盖事件给出每组每维非负总量端点L_d、U_d，且每一待定完成总量t_d满足L_d≤t_d≤U_d。对Σ_jt_j>0的结构比A_d=t_d/Σ_jt_j，可构造：','',
    r'\[ A_d^{L}=\frac{L_d}{L_d+\sum_{j\ne d}U_j},\qquad A_d^{U}=\frac{U_d}{U_d+\sum_{j\ne d}L_j}. \]','',
    '证明：结构比对本维总量单调不减，对其他维总量单调不增。因此本维取下界、其他维取上界得到下界，反向得到上界。原580参数家族若确实同时覆盖各层两参考五维两端点，则按层求和及此确定性映射保持至少95%的同时覆盖；无需为派生全部结构比再加一次Bonferroni。矩形可能包含互不兼容组合，所得包络保守且一般不锐利，也不要求维度相互独立。','',
    '组间结构差值的界应重算为[A_gd^L−A_hd^U，A_gd^U−A_hd^L]。只有新界在A、C下都同向严格排除0才记共同方向；不能套用旧固定N覆盖差值区间，也不能搬用旧“零共同方向”结论。','',
    '退化分母必须显式处理：','',
    '- ΣU=0：没有正总量候选，结构未定义，记NA；不能填0或均分。',
    '- 下界分母为0但ΣU>0：其他维只能为0，本维正时结构恒1；在正总量域上可取下界1。',
    '- 上界分母为0但ΣU>0：本维只能为0，只要其他维总量正，结构恒0，上界取0。',
    '- ΣL=0<ΣU：矩形含全0候选，另标记零总量完成仍可能；公式只覆盖结构有定义的正总量完成。若样本中至少一个固定已判1标签已能保证总体总量正，说明此依据。',
    '- 已判1点估计的五维总量为0时，点估计同样记NA，即使未知完成的结构可能有定义。','',
    '反例一：两组N均100，五维计数A=(10,90,0,0,0)、B=(5,5,0,0,0)。第一维覆盖A=10%高于B=5%，结构A=10%却低于B=50%。固定N比较与结构比较连方向都可反转。','',
    '反例二：已判1=(10,90)，待定=(10,90)。所有待定均0或均1都使第一维结构为10%，但只补本维可升至18.18%，只补另一维可降至5.26%。因此“已判1归一”与“1加待定归一”不能当逐维结构上下界。','',
    f'数值边界验证：穷举{boxes}个三维整数矩形、检查{checks}次正总量维度比；另对500个五维矩形检查{five_checks}次角点维度比（种子20261007），全部通过。验证代码与具体输出在[结构化审查](<{OUT/"指标与变量一致性审查.json"}>)。这些检验验证数学界，不是对论文分类标签有效性的验证。','',
    '## 聚合与敏感性容易遗漏的三点','',
    '1. 总体结构先合并各来源组估计命中总量，再归一；按组N加权组内结构并不等价。文件等权结构应先在文件内归一，零总命中文件须单列，不能当五维全0组成。年度系列也须写清先合并总量还是先平均成员份额。','',
    '2. 删除仅质量安全等某维标签后，五维共同分母变小，其余维度的结构份额会增加；每个定义情景必须全部五维重算。原覆盖变化百分点和“15个方向不变”不自动成立于结构占比。','',
    '3. 待定既影响本维分子，也影响五维共同分母。可以展示“已判1标签内部结构”的点估计，但它不是未知完整结构的无争议真值；待定范围及同时包络应另列，不能悄悄把待定置0。','',
    '政策要求、决策用途和协调建议可继续用已核政策条文和有来源的访谈阐释。内容结构、覆盖、分类一致性和政策效果是不同证据层级；恢复原统计对象后，应由新结果决定部门比较表述。','']
(OUT/'指标与变量一致性审查.md').write_text('\n'.join(md))
print(json.dumps({'contracts':len(contracts),'dimensions':len(dimensions),'issues':len(issues),'locations':len(locations),'math_validation':math_audit['validation'],'docx_unchanged':all(hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'] for v in read.values())},ensure_ascii=False,indent=2))
