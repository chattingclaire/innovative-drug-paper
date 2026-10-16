"""Assemble the agent's individually read, label-aware semantic diagnoses.

No prediction, reference, prompt, or coding metric is modified. The decisions
below are authored diagnoses, not a keyword classifier or a new gold standard.
"""
from pathlib import Path
import collections
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PACKET = OUT / 'final_llm_if_error_review_packet.json'
PROTOCOL = ROOT / 'outputs/llm-v29-method-audit-20261005/protocol-v1.3.md'
PROMPT = ROOT / 'outputs/llm-v29-method-audit-20261005/完整系统提示词-v29.txt'
LLM = OUT / 'llm-v29/production-25-v29/all_predictions.jsonl'
INPUTS = OUT / 'llm-v29/effective_blind_inputs_v29.jsonl'
RULE_INPUTS = OUT / 'llm-v29/rule_inputs_v29_shared.jsonl'
MAIN = ROOT / 'outputs/autocode-v25-20260927/current_1268_references.jsonl'
MAPPING = ROOT / 'outputs/autocode-v25-20260927/H427/admin_mapping.json'
METADATA = ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def text_sha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def jl(p):
    return {r['id']: r for r in (json.loads(s) for s in Path(p).read_text().splitlines() if s.strip())}

def context_texts(obj):
    """Retain every literal human context text; metadata is retained separately."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ('text', 'quote', 'unit_text', 'content', 'title', 'heading', 'context', 'parent_text') and isinstance(v, str):
                yield v
            elif isinstance(v, (dict, list)):
                yield from context_texts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from context_texts(v)

CLAUSES = {
    'context': ('应提供给编码员的材料', '上下文用于确定指代、对象、条件与列含义，不把父段或标题中的所有维度复制到子项。'),
    'attention': ('研究对象与编码含义', '条件、否定、不确定性及证据不足的陈述仍可能讨论相应维度。'),
    'I_definition': ('创新性 I', '讨论药物创新属性、创新点、原创或改良、作用机制或靶点的新颖性、相关知识产权、注册创新分类，以及明确针对药物研发创新的激励。'),
    'I_name': ('创新性 I', '仅把“创新药”作为某类药品的名称、政策标题或支付对象，不自动赋I。'),
    'I_qualification': ('v1.2新增操作边界／当前创新资格与跨程序引用', 'I的“创新资格的比较优势”须有两个证据锚点：当前条款在识别已明确登记的创新/改良资格；本单元实质陈述临床比较优势、治疗突破或该要求的明确内容援引。'),
    'I_change': ('v1.2新增操作边界／新品种、剂型、规格与属性', '须明确讨论原创、改良、新颖设计/技术、注册创新分类、相对既有产品的具体变化，或明确要求评价/提供创新属性信息。'),
    'I_change_limits': ('v1.2新增操作边界／新品种、剂型、规格与属性', '新申报、新上市、普通规格、给药便利与适龄性不自行补成创新；明确注册创新分类不受上述名称排除泛化影响。'),
    'I_support': ('v1.3冻结前子类型说明', 'research_support指本单元明确规定、提供、扩大或讨论针对药物研发创新的支持措施。'),
    'F_definition': ('公平性 F', '保障获取包括弥补用药保障空白、改善药品可及、短缺供应及防止不合理用药获取限制；患者可负担涉及患者支付能力或药费负担。'),
    'F_unmet': ('公平性 F', '儿童、老年、罕见病患者的名称本身不赋F，需有相关治疗需求未获满足、获取或保障含义。'),
    'F_arrangement': ('v1.2新增操作边界／保障/经济内容与实现', '按现有F边界识别具体药品配备和供应状况的信息要求、药物保障安排、明确公平性评价/资料要求及常规治疗获取渠道；不把一般配送、事务性记录、公平竞争、研究访视便利自动纳入。'),
    'F_management': ('公平性中的临床管理难度', '将临床管理要求限定为针对药品使用的具体管理障碍、复杂性、监测负担，或者明确评价该难度的要求。'),
    'F_convenience': ('公平性 F', '适老化包装、给药便利等适宜性内容不自动纳入F；若明确涉及误用风险或获取障碍，分别据其实际内容赋S或F。'),
    'F_trial': ('试验参与、代表性与治疗获取', '若条款明确使原本无法获得治疗的人群获得研究药物或治疗机会，则根据具体获取安排判断F，不能只凭“临床试验”“受试者”“便利性”推断。'),
    'content_not_outcome': ('评价内容要求与事务性提及', '该处理测量政策对评价内容的关注，不是评价已经完成或药物已被证明有效。'),
    'boundary': ('判断顺序与留痕', '文本问题和语境不足不强迫填0/1；边界争议可保留个人判断及理由，不能偷偷调整以迎合另一人或机器。'),
}
PROMPT_CLAUSES = {
    'I_execution': ('三／I 创新性', '以下内容单独出现时 I=0：把“创新药”当作药品类别或支付对象；“罕见病药品”“新药”“新品种”“新剂型”“新规格”等名称；普通作用机制；一般临床价值；突破性治疗、优先审评、附条件批准等程序名称；新的管理流程、数字系统或工作方式；一般产业发展或研发效率背景。'),
    'F_execution': ('三／F 公平性', '以下内容单独出现时 F=0：儿童、老年、罕见病或其他重点人群名称；创新药、基本目录、商保目录或申报资格；试验代表性、一般受试者参与便利；适老化包装、吞咽或给药便利；医院一般管理、处方规范或公平竞争；宏观医保筹资、机构建设或医疗服务均等化而没有明确药品使用/保障联系；一般配送、签收或文件报送事务。'),
    'context_execution': ('二／6 限制上下文用途', '禁止背景传播不等于忽视有明确语法或语义指向的上文；判断关键是当前命题是否通过指代、比较或条件关系实际承接该上文。'),
}

# One hand-authored diagnosis per exact ID x dimension, after reading the full
# text, every distinct context text, and the actual LLM/A/C explanations.
# Category is causal diagnosis, not the direction of disagreement or a score.
DECISIONS = {
('00009','I'): (1,'原文/语境差异','high','资格对象父条补全','当前已核验语境明确对象为“创新药或者改良型新药等”，本句实质规定相对现有治疗的明显临床优势，两个资格锚点齐全。原A/C材料未含该创新/改良对象语境，二者理由也明确指出缺此锚点；不能将当前I=1与历史I=0直接当作LLM错误。',['I_qualification','context'],'qualification_advantage'),
('00028','I'): (1,'原文/语境差异','high','研发支持对象父条补全','本句确实提供优先沟通资源和研发指导，当前新增已核验语境说明被支持的突破性程序面向创新/改良药物，足以消解支持对象。旧A/C发包没有该对象条款，且旧理由据此排除I；这是支持对象材料变化，不是程序名称自动赋I。',['I_support','context'],'research_support'),
('00126','F'): (1,'操作边界争议','medium','未上市急需药加速准入','不只出现罕见病名称，句中同时明确临床急需、境外已上市而境内未上市的获取缺口，并给出70日特殊上市审评路径，倾向按获取支持记F。A/LLM将其限于内部时限、C将其视为可及安排，反映对间接准入支持的边界分歧，尚非无争议错误。',['F_unmet','F_arrangement','boundary'],'access'),
('00174','F'): (1,'操作边界争议','medium','治疗无反应与未满足治疗需求','句子具体指出现有治疗后仍有患者未得到有效治疗，并要求特别关注这一人群更高的治疗需求。按本手册较宽的未满足治疗需求口径倾向F=1；LLM将F严格限于供应/支付渠道而排除疗效未覆盖人群。疗效无反应与获取空白并非同一概念，故应保留边界，不将双方差异直接认定为已裁定漏判。',['F_unmet','F_definition','boundary'],'access'),
('00270','F'): (0,'LLM理解偏差','high','试验分配机会泛化为获取保障','2:1改变已入组者被分配至潜在更优治疗组的概率，本句未明确使原本无法获得治疗的人群取得药物，也未描述常规药品获取缺口。LLM及C把试验内分配概率直接扩为保障获取，超过试验参与例外所要求的明确缺口。',['F_trial','F_convenience'],None),
('00646','F'): (1,'操作边界争议','medium','实际医保纳入与准入流程','本句包含确认支付标准后将药品纳入医保目录的条件结果，不只是目录名称或申报资格。按药物保障安排口径倾向F=1；A/LLM按程序分流处理亦有手册中的程序排除依据。需统一实际保障准入条件与仅申报分流的区别，不能只看“目录”定标签。',['F_arrangement','boundary'],'access'),
('00722','F'): (0,'LLM理解偏差','high','可申报误作已扩展保障','当前仅允许新增适应症申报支付范围调整并签补充协议，未给出审核后实际覆盖规则。LLM称为相应适应症进入保障范围的具体渠道，跳过申报资格与实际保障安排的区别。原A/C=0与明确的申报资格排除一致。',['F_execution','F_arrangement'],None),
('00723','F'): (0,'LLM理解偏差','high','调整程序归属误作保障扩展','句子只区分整体目录调整与企业申报的办理归属，没有规定调整方向、纳入结果或患者保障后果。LLM将“将纳入整体目录调整过程中考虑”解释为具体保障安排，实质是把评议程序当成保障覆盖。',['F_execution','F_arrangement'],None),
('00837','F'): (0,'操作边界争议','medium','已有保障药品的甲乙分类','核验分支对象为已在协议期内谈判保障中的药品，本句仅规定转常规后原则归乙类，没有新增纳入、保障延续条件或患者负担变化。倾向F=0；A/C把目录类别归属看作具体保障安排。该分类与实际覆盖的操作界线仍需事先固定。',['F_execution','F_arrangement','boundary'],None),
('01051','F'): (1,'操作边界争议','medium','价格门槛决定实际医保覆盖','完整命题将明确报价门槛与该通用名药品纳入或不纳入乙类医保目录直接连接，倾向认定为实际保障准入条件，区别于申报材料资格。A只记经济性，C/LLM同时记保障安排，属于Ec与F重叠边界。',['F_arrangement','attention','boundary'],'access'),
('01081','F'): (1,'操作边界争议','medium','负向保障准入规则','这是实际目录排除规则的条件示例：报价条件导致该通用名不获医保目录覆盖。倾向按药品保障范围关注记F，负向或假设例示不要求已经产生效果；LLM把它视作仅目录资格。与01051应采用同一实际覆盖边界，不以正负方向区别。',['F_arrangement','attention','boundary'],'access'),
('01134','F'): (0,'LLM理解偏差','high','基本用药需求泛称扩大为保障缺口','汇总基本用药需求用于综合评价选题，不等于收集配备、供应、获取障碍或未满足保障状态。所附语境同样为评价主题遴选与工作组织。LLM从一般需求信息推为保障获取，缺少对应的实质保障命题。',['F_arrangement','F_execution'],None),
('01149','F'): (1,'操作边界争议','medium','临床需求评价的同段消解','当前要求比较药品与参比药品满足临床需求程度，紧邻同段将这种创新性评价具体解释为填补治疗空白和未满足需求。倾向将后文作为当前评价对象的语义消解记F，非把整段全部维度复制；A强调当前句需求泛称、C/LLM使用同段说明，属于上下文使用边界。',['F_unmet','context','boundary'],'access'),
('01385','I'): (0,'操作边界争议','medium','制度宗旨与具体创新支持','本句明示鼓励药品创新的制定宗旨，但未说明本办法提供何种研发支持、知识产权利益或创新属性评价。依research_support要求具体支持措施，倾向I=0；A/C将制定创新制度这一目的本身作为激励讨论，属于目的条款是否构成实质支持的边界。',['I_support','I_name','boundary'],None),
('01503','F'): (1,'LLM理解偏差','high','常规治疗渠道信息被要求另证障碍','当前明确收集患者就诊路径及现有药物治疗选择，包括超适应症和非处方药。手册v1.2已将常规治疗获取渠道列入保障获取，不要求只有已发现短缺或障碍才记F。LLM以未指出障碍为由一概排除，缩窄该信息要求口径。',['F_arrangement','content_not_outcome'],'access'),
('01723','F'): (0,'操作边界争议','medium','续约办理路径与保障延续承诺','失败后按原支付范围再谈判或简易续约，只规定后续办理路径，并未在本句承诺继续支付或保证续约成功。LLM解释为“明确保留既有保障覆盖”超出文字；倾向F=0，但若将制度化续约后备路径操作化为连续保障，也需另固定该宽口径。',['F_execution','F_arrangement','boundary'],None),
('02226','I'): (1,'操作边界争议','medium','创新药全球同步研发支持条件','本句规定我国研究者牵头/共同牵头国际多中心III期试验，并讨论早期参与如何支持创新药全球同步研发；同段及问答主题说明这是纳入30日通道支持范围的条件。倾向按明确讨论创新研发支持机制记I，不是仅出现创新药名称。LLM把实施条件视为一般试验组织，分歧在支持机制条件的内容层级。',['I_support','context','boundary'],'research_support'),
('02259','F'): (1,'LLM理解偏差','high','只接受有利保障后果而排除负向供应','清除具体问题品种出本机构药品供应目录，实质改变可获得药物的配备供应范围。测量的是关注，不是政策是否改善公平；LLM以其为限制措施而非保障改善为由判0，把正向政策效果误作纳入前提。',['F_arrangement','attention'],'access'),
('02317','F'): (1,'操作边界争议','medium','实际确定药品给付范围','当前对具体续约药品要求确定下一协议期支付标准和支付范围，后者决定实际药品给付覆盖。按药物保障安排及内容评价要求倾向F=1，不需要先证明覆盖扩大；A/C要求另有缺口/障碍，采用了较窄F阈值。',['F_arrangement','content_not_outcome','boundary'],'access'),
('02361','F'): (0,'操作边界争议','medium','药品目录联动的一般管理','当前仅鼓励联动管理、规范机构用药目录，未说明具体药品跨院衔接、配备不足或患者取得药物的安排。倾向F=0，不能复制同段别句的基本药物配备要求。C从整段配备管理功能解读为可及衔接，属于组织机制与具体配备措施边界。',['F_arrangement','context','boundary'],None),
('02391','F'): (0,'参照疑点','high','药学服务组织方式扩大为药物获取','临床药师院际会诊是服务组织形式；本句及相邻语境未规定患者取得某药渠道，也未评价药品使用管理的具体困难。C把跨机构药学服务本身视为治疗药物获取渠道，超出药品保障获取构念；LLM与A的0更符合现有排除。',['F_execution','F_management'],None),
('02393','F'): (0,'参照疑点','high','基层药学服务清单扩大为药物获取','当前列基层咨询、药物治疗管理、科普等一般服务，并未说明取得药物障碍或使用某药管理复杂性。同段后句行动不便人群上门服务不可移入当前句。C仅据新增服务渠道判F=1，混合了药学服务可及与药品获取。',['F_execution','F_management','context'],None),
('02534','F'): (1,'LLM理解偏差','high','具体药物支付障碍被降为一般申报','本句明确合理使用目录创新药病例无法适配按病种支付，并给出特例单议通道；所附同段进一步说明按项目付费或调整支付标准。当前已经有具体药物使用的支付障碍与解决机制，不能按一般目录申报排除。',['F_arrangement','context_execution'],'access'),
('02598','F'): (1,'操作边界争议','medium','未医保覆盖基本药物的优先审议','对象明确为基本药物中仍在医保目录外的药物，优先考虑其进入备选评审，具有回应基本用药保障覆盖空缺的方向，倾向F=1。LLM要求实际承诺纳入才记F过于结果化，但该句仍处评审优先阶段，需保留与一般申报资格的边界。',['F_unmet','F_arrangement','content_not_outcome','boundary'],'access'),
('03220','F'): (1,'LLM理解偏差','high','恢复父谓词后的实际保障排除','该列举项须承接已核验父条“以下药品不纳入《药品目录》”，构成某类药品实际不予医保覆盖的规定，而非只出现药品名称或申报资格。LLM把恢复完整命题后的覆盖排除仍当目录类别，忽视了父谓词，并将负向保障内容排除。',['context','F_arrangement','attention'],'access'),
('03274','F'): (1,'操作边界争议','medium','基金承担药费的条件','父条明确参保人用目录药发生费用在符合条件时可由医保基金支付，本项给出诊治目的条件。倾向将费用保障条件记为药物保障安排；A/C只记经济支付条件、要求额外缺口/负担描述。不得把所有支付字样都记F，但此处有参保人药费与基金承担的明确关系。',['context','F_arrangement','boundary'],'access'),
('03282','F'): (0,'操作边界争议','medium','既有保障药品类别管理','本句将已经协议期内谈判的药品归乙类管理，未新增进入医保的条件或保障范围变化。倾向F=0，区别于首次纳入/调出规则；C视甲乙保障归属本身为F，属于已覆盖药品分类是否纳入的操作边界。',['F_execution','F_arrangement','boundary'],None),
('03308','F'): (1,'LLM理解偏差','high','错误要求保障调整必须正向','本句为紧急公共卫生事件建立医保药品支付范围临时调整授权，已是与具体用药情境相关的保障安排。LLM因未说明一定扩大保障而排除F，混淆“实质关注保障”与“已经改善保障”；方向及幅度不确定不构成0的理由。',['F_arrangement','attention'],'access'),
('03410','I'): (0,'LLM理解偏差','high','文件制定发布元信息扩大为研发支持','本句只是组织制定并列明创新药适老化指导原则的文件名，没有规定具体技术支持或研发激励措施。LLM把任何面向创新药的指导文件制定事实直接视为研究支持，越过标题/文档元信息排除。',['I_name','I_support'],None),
('03425','F'): (1,'参照疑点','high','具体服药管理障碍被当人群特征','当前明确认知减退导致记不清是否/何时/如何服药以及混淆不同药品，已经是具体用药管理障碍，不是仅老年人群名称或一般服用便利。C要求另有评价措辞而排除，忽视手册同时纳入实质描述障碍。',['F_management'],'clinical_management'),
('03474','I'): (1,'LLM理解偏差','high','具体相对产品改良被要求额外创新标签','要求根据掰断操作数据改善既有片剂易碎性，属于相对既有产品某项具体属性的改变；不能把后半普通强度/规格列表作为独立创新依据，但也不能忽视前半具体改良。冻结v1.2允许这种具体变化且不强求新靶点、创新分类或已证明优越。LLM另要求显式创新身份，缩窄了手册。',['I_change','I_change_limits'],'attribute'),
('03474','F'): (0,'LLM理解偏差','high','掰片便利性泛化为临床管理难度','本句收集的是老年患者掰片操作便利性并改善制剂属性，所附语境也是手指灵活性和分割操作。没有额外说明复杂管理、必要监测或治疗获取障碍。LLM将一般给药操作便利直接视作管理难度，违反适老化便利不自动纳入F的明确排除。',['F_convenience','F_management'],None),
('03489','I'): (1,'操作边界争议','medium','制剂特征改良的具体性','当前基于已经描述的多病共存及多药不同时间/途径使用问题要求有针对性地改善制剂特征，倾向依相对既有产品改良记I，非仅文件题名。LLM要求显式原创/改良身份而排除较窄；但当前未指明究竟改变哪项特征，不能复制后文缓释/辅助装置举例，故保留具体性边界。',['I_change','context','boundary'],'attribute'),
('03715','F'): (0,'操作边界争议','medium','放宽跨目录申报资格','当前只取消商保药申请基本目录时的上市年限限制，尚未规定实际医保给付或获取渠道。按申报资格排除倾向F=0；C把跨保障体系申请障碍的移除视为制度可及，同段目标确实支持这一较宽解释，应保留边界而非称其必错。',['F_execution','F_arrangement','boundary'],None),
('03734','F'): (0,'操作边界争议','medium','既有谈判保障转常规分类','对象已在医保谈判目录，本句主要规定到期后转常规乙类管理的条件，未改变可获得药品或给付范围，倾向F=0。LLM称继续纳入保障，可反映分类稳定性，但若无明确保障中断问题，不宜由管理类型转换自动推F。',['F_execution','F_arrangement','boundary'],None),
('03759','F'): (1,'操作边界争议','medium','明确患者减负机制的语境承接','当前挂网价格红黄标正是同段首句所说为减轻参保患者用药负担建立的价格与支付标准联动机制，后句给出阈值。倾向把该明确用途作为当前机制的对象/保障关系消解，记可负担F；A/LLM只按本句价格标识记Ec，属于目的语境与当前措施的承接强度边界。',['context_execution','F_definition','boundary'],'affordability'),
('03803','F'): (0,'参照疑点','high','商保目录计数与资格被当保障实况','当前19种及撤市1种用于限定本条申报资格，药品列入推荐商保目录本身不等于实际被保险计划覆盖或患者取得药品。C以目录状态直接认定保障覆盖，超过目录/申报资格名称排除；A与LLM=0更符合当前功能。',['F_execution','F_arrangement'],None),
('03894','I'): (0,'参照疑点','high','普通处方比较误作创新属性资料','当前只要求与已上市中药处方对比，未限定差异用于原创、改良、新颖性或注册创新分类判定。C把所有属性比较都等同创新属性信息，缺少创新或具体变化锚点；LLM与A=0更符合定义。重复句号是可见版式瑕疵，不使该创新判断缺料。',['I_definition','I_change'],None),
('04444','I'): (1,'LLM理解偏差','high','忽视当前支持措施与同条创新对象承接','同一第十三条先明确加快上市制度支持临床价值导向的药物创新，当前随即具体规定研制注册中的指导、沟通、优先资源和缩短时限。当前措施承接同一制度的创新支持对象，使用该语境属于对象消解而非背景标签复制。LLM机械禁止使用该上文导致漏判。',['I_support','context_execution'],'research_support'),
('04703','F'): (1,'操作边界争议','medium','临床急需境外药上市加速','当前把临床急需的境外已上市罕见病药特别列为70日上市审评对象，倾向认定针对急需治疗的进入支持路径，而不是仅罕见病类别。与00126相比，本句没有直接写境内未上市，获取缺口锚点更弱；A/LLM按一般时限排除与C较宽制度可及均需保留。',['F_unmet','F_arrangement','boundary'],'access'),
('03455','F'): (1,'参照疑点','high','明确使用问题评价未被识别为管理难度','本句明确评估药物使用环节突出问题，并支持老年患者适宜管理和使用；前句将问题具体化为认知、操作、照料环境，前段还有减少方案复杂性。不同于仅吞咽/包装便利，这里存在使用管理障碍的评价。A将其全部视为一般适宜性而排除，较手册临床管理口径偏窄。',['F_management','context'],'clinical_management'),
('01412','I'): (1,'操作边界争议','medium','数据独占实效与办理时限','药品已获数据保护后，依赖他人受保护数据的竞争申请必须等到保护期届满才能获批，实质说明数据独占的保护效果，倾向作为相关知识产权记I。LLM/A将其视为仅办理时限，C视为权利效力；区别于单纯报送/公开手续，应固定数据保护实质规则的层级。',['I_definition','I_support','boundary'],'attribute'),
('01414','I'): (0,'操作边界争议','medium','权利终止状态与创新属性','本句列批准文件撤销、主动放弃等既有数据保护终止事由，没有讨论新颖数据价值、保护范围或创新激励利益，倾向视为权利状态程序I=0。C将一切保护权终止条件纳入相关知识产权，属于实质权利边界和行政身份处理的界线，不据本审读强改。',['I_definition','I_name','boundary'],None),
('00046','I'): (1,'原文/语境差异','medium','创新支持撤回对象父条补全','当前明确撤回优先研发沟通资源，属于支持措施的负向制度安排；新语境提供创新/改良对象锚点。旧H材料仅有突破性程序及沟通时限，A/C据已有程序身份排除。倾向当前I=1，但研发支持撤回与一般程序终止的边界仍需保留，首要差异是可用对象语境。',['I_support','attention','context'],'research_support'),
('02269','I'): (1,'操作边界争议','medium','创新药试点批准与文件名','本句实际批准京沪开展专门优化创新药临床试验审批的试点，而非单纯发布一个标题，倾向视为针对创新研发环节提供制度支持。A将其作为行政批复元信息排除，C/LLM把批准实施本身作为支持，体现政策实施决定与正文细则的内容边界。',['I_support','I_name','boundary'],'research_support'),
('04619','F'): (1,'操作边界争议','medium','应急用药特别准入','本句不仅出现特别审批程序名，还明确对象为突发公共卫生事件应急所需防治药，设立专门准入安排，倾向按用药需求的获取支持记F。LLM要求另写短缺/供应关系，采取较窄口径；特殊审批与实际治疗获取之间的间接联系仍须事先统一。',['F_unmet','F_arrangement','boundary'],'access'),
('04516','I'): (0,'操作边界争议','medium','普通剂型规格变更的具体性','当前只概述非处方药改变剂型/规格而其适应症、剂量、途径不变，没有具体改良属性或新颖配置。倾向按普通剂型规格变化排除I；A据相对既有产品变化记I，也可援引v1.2，说明“相对具体变化”与“普通剂型规格”界线须固定，不以本审读冒充裁定。',['I_change','I_change_limits','boundary'],None),
('01413','I'): (1,'LLM理解偏差','high','受保护数据专有权被一概降为事务合规','对虚称自有而依赖他人受保护数据的申请不予许可，实质保护药品试验数据的独占权与侵用后果，属于相关知识产权规则，而非资料格式、报送或公开事务。LLM将该实质保护一概解释为合规事项，遗漏手册允许的知识产权内容。',['I_definition'],'attribute'),
('02522','F'): (1,'操作边界争议','medium','具体药品保障体系目录衔接','当前要求商保创新药与医保药品目录衔接，所附同段已明确保障对象为超出基本医保范围且有患者获益的药物、多层次保障参考使用。倾向视为药品保障安排，非宏观一般机构建设。LLM认为衔接过于抽象，分歧在具体药品保障制度与可执行获取措施的最低内容要求。',['F_arrangement','context','boundary'],'access'),
('04620','F'): (1,'操作边界争议','medium','当前加速措施承接应急药对象','本句实质组织加快同步注册各环节，前条明确实施特别审批对象为应急所需药品，当前指代“实施特别审批的药品注册申请”承接该对象，倾向作为用药获取支持安排。C/LLM将其限于作业流程，A记可及，反映加速措施与直接获取之间的边界。',['context_execution','F_arrangement','boundary'],'access'),
('04517','I'): (1,'操作边界争议','medium','既有活性成分新组合的改良属性','本句具体说明用已确定非处方药活性成分组成新的复方制剂，区别于无内容的“新药”名称，倾向按相对既有单方/产品的新组合属性记I，不需证明更优疗效。LLM仅视新品种形态；但当前未给组合配方和新颖性范围，故与普通品种名称的界线仍保留争议。',['I_change','I_change_limits','boundary'],'attribute'),
('00763','F'): (1,'操作边界争议','medium','申报后形成实际新给付范围','当前不止允许申请，还规定经程序确定新的医保支付标准、支付范围并签补充协议，倾向作为实际药品保障范围调整的安排记F；不要求其一定扩大或已实施。A要求另写获取/负担问题，C/LLM据具体给付关系记F，与00722只述申请资格应区分。',['F_arrangement','content_not_outcome','boundary'],'access'),
}

def main():
    packet = json.loads(PACKET.read_text())
    protocol_text, prompt_text = PROTOCOL.read_text(), PROMPT.read_text()
    for key, (section, quote) in CLAUSES.items():
        assert quote in protocol_text, (key, section)
    for key, (section, quote) in PROMPT_CLAUSES.items():
        assert quote in prompt_text, (key, section)
    all_llm, inp, rule_inp, refs = jl(LLM), jl(INPUTS), jl(RULE_INPUTS), jl(MAIN)
    metadata = {Path(r['original_file']).stem: r for r in json.loads(METADATA.read_text())['rows']}
    mapping = {r['rerun_id']: r for r in json.loads(MAPPING.read_text())}
    files = [PACKET, PROTOCOL, PROMPT, LLM, INPUTS, RULE_INPUTS, MAIN, MAPPING, METADATA, Path(__file__)]
    packet_index = {}
    result_index = {}
    for frame in ('V600', 'D668'):
        for coder in ('A', 'C'):
            folder = ROOT / f'outputs/validation-expansion-20260926/{frame}/agent-{coder}'
            for p in sorted(folder.glob('材料-*.json')):
                for row in json.loads(p.read_text()).get('rows', []):
                    packet_index[(frame, coder, row['id'])] = (p, row)
            for p in sorted(folder.glob('结果-*.json')):
                for row in json.loads(p.read_text()).get('rows', []):
                    result_index[(frame, coder, row['id'])] = (p, row)
    for coder in ('A', 'C'):
        folder = ROOT / f'outputs/autocode-v25-20260927/H427/agent-{coder}'
        for p in sorted(folder.glob('材料-*.json')):
            for row in json.loads(p.read_text()).get('rows', []):
                packet_index[('H427', coder, row['id'])] = (p, row)
        for p in sorted(folder.glob('结果-*.json')):
            for row in json.loads(p.read_text()).get('rows', []):
                result_index[('H427', coder, row['id'])] = (p, row)
    before = {str(p): sha(p) for p in files}
    assert before[str(LLM)] == '111ddb35068d5adba9ef7607dfad41a8835339a71371a73b7a71b9e84e527915'
    records = []
    for rec in packet:
        rid, dim = rec['id'], rec['dimension']
        key = (rid.split('-')[1], dim)
        judgment, category, confidence, subtype, reason, clauses, basis = DECISIONS[key]
        ref_id = refs[rid]['current_reference_id'] if rec['frame'] == 'main1057' else mapping[rid]['id']
        source_frame = ref_id.split('-')[0]
        literal_current_contexts = list(dict.fromkeys(context_texts(rec['input']['contexts'])))
        old_sources = {}
        for coder in ('A', 'C'):
            p, row = packet_index[(source_frame, coder, ref_id)]
            files.append(p)
            old_texts = list(dict.fromkeys(context_texts(row.get('contexts', {}))))
            added = [t for t in literal_current_contexts if t not in old_texts and t != rec['input']['text']]
            old_sources[coder] = {
                'packet_path': str(p), 'packet_sha256': sha(p), 'reference_id': ref_id,
                'original_unit_text': row.get('text'),
                'same_unit_text_as_current': row.get('text') == rec['input']['text'],
                'original_contexts': row.get('contexts', {}),
                'current_added_literal_contexts': [{'text': t, 'text_sha256': text_sha(t)} for t in added],
                'original_reference_record_used_for_metrics': rec['references'][coder],
            }
            if (source_frame, coder, ref_id) in result_index:
                rp, result = result_index[(source_frame, coder, ref_id)]
                files.append(rp)
                old_sources[coder].update({
                    'original_result_path': str(rp), 'original_result_sha256': sha(rp),
                    'original_result_record': result,
                    'merged_reference_label_equals_original_result': result['labels'][dim] == rec['references'][coder]['labels'][dim],
                })
        citations = []
        for clause in clauses:
            source = PROTOCOL if clause in CLAUSES else PROMPT
            section, quote = (CLAUSES | PROMPT_CLAUSES)[clause]
            citations.append({'key':clause, 'path':str(source), 'sha256':sha(source), 'section':section, 'literal_quote':quote})
        same_review = {c: judgment == rec['references'][c]['labels'][dim]
                       for c in ('A','C') if type(rec['references'][c]['labels'][dim]) is int}
        records.append({
            'frame':rec['frame'], 'id':rid, 'group':rec['group'], 'dimension':dim,
            'current_labels': {'LLM':rec['llm']['labels'][dim], **{c:rec['references'][c]['labels'][dim] for c in ('A','C')}},
            'different_binary_references':rec['different_references'],
            'current_text': rec['input']['text'], 'unit_text_sha256':text_sha(rec['input']['text']),
            'source_title':rec['input'].get('source_title'), 'pages':rec['input'].get('pages'),
            'current_contexts':rec['input']['contexts'],
            'current_contexts_sha256_canonical_json':text_sha(json.dumps(rec['input']['contexts'],ensure_ascii=False,sort_keys=True,separators=(',',':'))),
            'current_llm_reason':rec['llm']['dimension_reasons'][dim],
            'current_llm_dimension_evidence':[e for e in rec['llm']['evidence'] if e['dimension']==dim],
            'reference_source_records':old_sources,
            'diagnosis': {'primary_category':category, 'subtype':subtype,
                          'reviewer_binary_judgment':judgment, 'confidence':confidence,
                          'reviewer_basis_subtype':basis, 'specific_reason':reason,
                          'agrees_with_llm':judgment == rec['llm']['labels'][dim],
                          'agrees_with_reference':same_review,
                          'is_binding_adjudication':False,
                          'requires_prospective_boundary_clarification':category=='操作边界争议',
                          'applicable_manual_clauses':citations},
            'material_gate_review':{
                'current_defect_precluding_binary_review':False,
                'visible_issue': 'duplicate punctuation only; does not alter this judgment' if rid=='RECODE25-03894' else None,
                'historical_context_comparison_recorded':True,
                'note':'新增语境是逐字材料差异；只有在逐项具体理由证明因果时才归类为材料语境差异，不把所有新增相邻段自动视为旧材料缺陷。'},
        })
    assert {(r['id'].split('-')[1],r['dimension']) for r in packet} == set(DECISIONS)
    assert len(records) == 52 and len({r['id'] for r in records}) == 51
    expected = []
    h_refs = {}
    for rid, m in mapping.items():
        h_refs[rid] = {c: result_index[('H427',c,m['id'])][1] for c in ('A','C')}
    for frame, source in [('main1057',refs),('supplement_H411',h_refs)]:
        for rid, r in source.items():
            group = metadata[rule_inp[rid]['input']['original_file_stem']]['analysis_group']
            if group not in ('NMPA','NHSA','NHC'):
                continue
            rs = r['original_references'] if frame=='main1057' else r
            for dim in ('I','F'):
                differing = [c for c in ('A','C') if type(rs[c]['labels'][dim]) is int and rs[c]['labels'][dim] != all_llm[rid]['labels'][dim]]
                if differing:
                    expected.append((frame,rid,dim))
    actual = [(r['frame'],r['id'],r['dimension']) for r in records]
    assert len(expected)==len(set(expected)) and set(expected)==set(actual), 'Missing actual I/F discrepancy'
    summary = {}
    for frame in ('main1057','supplement_H411','combined_separate_frames'):
        chosen = records if frame=='combined_separate_frames' else [r for r in records if r['frame']==frame]
        summary[frame] = {
            'reviewed_id_dimension_n':len(chosen), 'unique_id_n':len({r['id'] for r in chosen}),
            'by_dimension':dict(collections.Counter(r['dimension'] for r in chosen)),
            'by_primary_category':dict(collections.Counter(r['diagnosis']['primary_category'] for r in chosen)),
            'reviewer_differs_from_llm_n':sum(not r['diagnosis']['agrees_with_llm'] for r in chosen),
            'high_confidence_llm_deviations_n':sum(r['diagnosis']['primary_category']=='LLM理解偏差' and r['diagnosis']['confidence']=='high' for r in chosen),
            'differences_not_model_error_by_default':True,
        }
    counts = collections.defaultdict(collections.Counter)
    for rid, ll in all_llm.items():
        group = metadata[rule_inp[rid]['input']['original_file_stem']]['analysis_group']
        if group in ('NMPA','NHSA','NHC'):
            counts[group].update(ll['labels'])
    bounds = {}
    for group in ('NMPA','NHSA','NHC'):
        b = {d:{'observed_llm_count':counts[group][d],'min_if_all_reviewed_disagreements_set_zero':counts[group][d],
                 'max_if_all_reviewed_disagreements_set_one':counts[group][d]} for d in ('S','E','Ec','I','F')}
        for rec in records:
            if rec['group']==group:
                d=rec['dimension'];old=rec['current_labels']['LLM']
                b[d]['min_if_all_reviewed_disagreements_set_zero']-=old
                b[d]['max_if_all_reviewed_disagreements_set_one']+=1-old
        bounds[group]=b
    assert counts['NMPA']['S'] > max(v['max_if_all_reviewed_disagreements_set_one'] for d,v in bounds['NMPA'].items() if d!='S')
    assert counts['NHSA']['Ec'] > max(v['max_if_all_reviewed_disagreements_set_one'] for d,v in bounds['NHSA'].items() if d!='Ec')
    assert bounds['NHC']['F']['min_if_all_reviewed_disagreements_set_zero'] > max(counts['NHC'][d] for d in ('E','Ec','I'))
    assert counts['NHC']['S'] > max(counts['NHC'][d] for d in ('E','Ec','I'))
    sources = {str(p):sha(p) for p in dict.fromkeys(files)}
    assert all(sources[p]==v for p,v in before.items()), 'Read-only source changed'
    result = {
        'created_date':'2026-10-07','review_identity':'AI agent /root/final_semantic_error_review',
        'review_design':'Label-aware diagnostic reading of every actual LLM-v29 vs unchanged AI A/C I/F disagreement; not blind review, human validation, adjudicated gold, or a new reliability sample.',
        'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v29',
        'scope_definition':'Original main 1057 and separate H411 restricted by frozen analysis_group NMPA/NHSA/NHC. An ID×dimension enters if LLM differs from at least one actually binary A/C reference; pending labels are never converted.',
        'pairing_check':{'expected_disagreements':len(expected),'reviewed_disagreements':len(actual),'complete_set_exact':True,
                         'all_104_merged_reference_dimension_labels_equal_actual_original_result':all(
                             x.get('merged_reference_label_equals_original_result') is True
                             for r in records for x in r['reference_source_records'].values())},
        'review_constraints':['No A/C label changed.','No LLM output changed.','No prompt or rule changed.','No metric threshold was used to infer a semantic error.','A reviewer judgment is provisional and does not replace an actual prospective adjudication.'],
        'category_definitions':{
            '原文/语境差异':'旧参照发包与当前已核验语境有影响该维判断的具体差别；不等同当前原文缺字或LLM理解错误。',
            'LLM理解偏差':'本审读认为当前LLM理由与冻结手册明确纳入/排除或当前承接关系发生较清楚冲突。它仍是AI诊断而非真人裁定。',
            '操作边界争议':'手册或执行澄清的层级/具体性/上下文承接仍允许不同解释；保存本人倾向及双方依据，不回改分数。',
            '参照疑点':'至少一个旧A/C理由与当前完整语义边界有较清楚偏离，而LLM并非必然错误；不以另一方法一致作为真值。'},
        'summary':summary,
        'observed_patterns':[
            '公平性存在把所有程序性渠道扩大为保障安排的个别过宽判断，也存在要求已实现、必须扩大或必须额外指出障碍而漏掉信息要求/负向保障/具体支付例外的过窄判断；不能用一个“召回低”或“误报多”概括全部。',
            '创新性分歧中，部分旧参照缺少现在已核验的创新资格对象语境；另有当前LLM对具体片剂改良、相关药品数据专有权和同条创新支持的理解偏窄，以及将文件制定元信息视作研发支持的偏宽判断。',
            '目录类分歧应区分纯名称/申报资格/既有甲乙分类，与实际纳入排除条件、参保人药费承担和应急给付范围安排。此区分需要前瞻冻结，不能把本审读倾向当作已完成统一裁定。'],
        'local_conclusion_impact':{
            'actual_full_corpus_llm_dimension_counts':dict(counts),
            'extreme_bounds_only_over_reviewed_52_items':bounds,
            'observed_order_robust_within_these_items':{'NMPA_S_is_unique_maximum':True,'NHSA_Ec_is_unique_maximum':True,'NHC_S_and_F_remain_top_two':True},
            'interpretation':'即使将本审读52个ID×维度分歧（51个独特ID）的I/F任意置0或1，药监S居首、医保Ec居首、卫健S/F为前两位仍不变。该局部算术界限不证明全语料无同标签共同错误，也不抵消创新性/公平性的具体解释偏差；剩余语料和新真人样本未由本审读覆盖。未把任何反事实标签写回实际结果。'},
        'source_sha256':sources,'records':records,
    }
    dest=OUT/'final_llm_if_error_review.json'
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'output':str(dest),'sha256':sha(dest),'summary':summary,'source_files':len(sources),'local_bounds_checked':True},ensure_ascii=False))

if __name__=='__main__':
    main()
