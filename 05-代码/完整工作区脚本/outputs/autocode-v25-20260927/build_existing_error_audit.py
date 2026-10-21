"""Read only already published V600/D668 packets and first receipts; write an audit.

No corpus.jsonl is opened. No sampling or relabeling is performed.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path('/PROJECT_ROOT')
OLD = ROOT / 'outputs/validation-expansion-20260926'
OUT = ROOT / 'outputs/autocode-v25-20260927'
FROZEN = OLD / 'V600-frozen-inputs'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

groups = [
    ('M01', '创新属性、激励的术语和句法覆盖不足',
     '把“药物对象—创新属性/研发目标—支持动作或保护权益”分开识别并建立关系。不要以固定相邻字数替代关系，也不能将任意“创新药”对象直接赋I。',
     'I定义；v1.2“新品种、剂型、规格与属性”；共同澄清第3项“相关知识产权与纯专利事务”。'),
    ('M02', '实质内容的明确指代未进入规则',
     '只为当前单元中的相应要求、该药品、评价需要等建立有证据的指代边；记录同段先行词、关系、源ID和文字哈希。未经核验的邻段不是自动父条款。',
     '应提供的材料、判断顺序与留痕；v1.2“当前创新资格与跨程序引用”；共同澄清第4项。'),
    ('M03', '供应、配备状态被狭窄动作词漏掉',
     '对具体药品是否供应、供应持续性以及配备状态的信息要求识别access；登记、维护不自动排除实质信息。',
     'F保障获取；v1.2“保障/经济内容与实现”；共同澄清第2项。'),
    ('M04', '治疗缺口的否定和同义表达未覆盖',
     '识别“缺乏有效治疗措施”“仍未能得到有效治疗”等未满足需求的命题；否定或不足不应把关注维度变为0。',
     '研究对象与编码含义；F“未满足治疗需求”；试验参与、代表性与治疗获取。'),
    ('M05', '具体改良或管理困难不能只靠维度名称',
     '在具体产品特征改良和药物使用复杂性中保留实际特征、困难、改进关系。适龄性、一般便利和临床管理标题仍非充分条件。',
     'I“原创或改良”；v1.2新品种边界；F“临床管理难度”及共用执行说明第3项。'),
    ('M06', '对象门控、术语和输入适用范围是不同故障',
     '把“存在词义证据但对象未核验”与“无维度内容”分开。已绑定的适用范围可消解对象，不能产生不存在的维度证据；缺少适用范围时不从文件名补标签。',
     '上下文只用于对象、条件、指代；不按文件名推定；input_assessment.not_assessed不证明材料充分。'),
    ('M07', '药物研究场景不能替代谓词的真实对象',
     '风险、有效性、费用必须绑定到损害、疗效、药品治疗支付对象；局部处理行政费用、文献标题等，不整句删除其他真实依据。',
     'S/E/Ec排除项；评价内容要求与事务性提及；文本应逐维判断。'),
    ('M08', '缺少关键列表或图示时不能强制二元化',
     '先审查当前单元是否有待补的关键条件或所指材料，再决定可判范围；整条理解受影响时五维待定，单维概念疑问另记。',
     '文本缺陷优先处理；共用执行说明1、2；v1.2冒号边界；共同澄清第1项。'),
    ('M09', 'AI一致与分歧均须接受构念边界审查',
     '这些病例只作为争议和负例挑战候选，不按多数票定规则。区分更优疗效、程序便利、政策目的与保障获取；不为了复现A/C而扩大构念。',
     'I创新对象名称排除；F适宜性和研究参与排除；一般程序与宏观保障；共同澄清第1、3项。'),
    ('M10', '五维命中与来源子类型需分别核验',
     '二元I/F命中不意味着子类型充分。属性、研发支持、创新资格优势分别要有锚点；dimension_information不能伪装成access。',
     '创新资格双锚点；输出记录约定；明确维度信息要求；v1.3研究支持子类型说明。'),
]

# status = supported_gap / input_or_scope_gap / supported_false_positive /
#          input_unresolved / boundary_dispute / positive_control / subtype_gap.
specs = [
 ('V600-0388','M01',['I'],'supported_gap',
  '当前条文明确给予原研药新适应症研发数据6年保护；支持I=1、research_support，依据是保护激励而非“原研”名称。I09把对象至给予的距离限制为35字符，真实条件链超出；本句已有drug_object，不是对象缺失。',
  '将对象、保护范围、给予保护期建立同一条款关系，保留未获批新适应症及证据提交条件。',
  '“登记保护期截止日期”之类纯事务，或无药物创新关系的数据保密，不自动I。'),
 ('V600-0338','M01',['I'],'supported_gap',
  '对创新药等自行取得且未披露数据给予一定保护期是实质成果保护。旧I09仅接受原研/改良型及具体数年，漏掉多对象并列和“一定”保护期。',
  '保护激励可为定量或非定量期限；识别并列对象中确有药物创新对象。',
  '不能从罕见病或儿童名称本身推I，也不能给同句未有依据的E/F。'),
 ('V600-0423','M01',['I'],'supported_gap',
  '“根据…产品特性、创新程度…制定细化分类”实质以创新属性确定注册分类，不仅是标题。词表有创新性、注册分类，未覆盖“创新程度”与“细化分类”这一句法。',
  '将创新程度、创新价值等纳入属性评价词族，但要求药品属性或创新评价的语义关系。',
  '“提高工作创新程度”“管理创新”及引用含创新词的标题不构成I。'),
 ('D668-0357','M01',['I'],'supported_gap',
  '“鼓励新药和创新医疗器械研发”并给予优先审评，明确药物研发支持。词典只认紧邻的新药研发，药械并列打断了目标短语。',
  '支持动词、并列药物研发对象与实际审评支持措施解析后绑定；I来源为research_support。',
  '纯优先审评身份或时限无研发支持/属性锚点不自动I；不得继承前句疗效风险。'),
 ('D668-0349','M01',['I'],'supported_gap',
  '药品原创性成果专利布局和转化为创新成果保护支持，超出“专利”单词或权属事实。旧I01只收自主知识产权、原始创新等特定表达。',
  '对原创药物成果+专利布局/保护/转化建立属性及研发支持证据，可多子型但每项独立留痕。',
  '专利费用、专利机构名称、诉讼日程和纯纠纷事实不能按专利二字自动I。'),
 ('V600-0097','M02',['F'],'supported_gap',
  '“相应要求”明确承接同段的保障市场供应、定点配备和报送配备，将这些要求写入协议属于当前实际约束；候选17虽已识别药品对象，但没有F关系证据。',
  '只解析同段当前句之前的相应要求，保存faq25_p065先行词证据及协议化关系。',
  '不复制同段之后的调出目录制裁或邻段支付标准；无确定先行词时保留语境问题。'),
 ('V600-0242','M02',['F'],'supported_gap',
  '当前明确取得药品生产供应信息，段内已定义其为可获得性评价支持信息。不是一般上传格式。候选F11需要收集/报告/监测+配备+信息，漏掉“获得相关支持信息”及目的关系。',
  '药品供应状况的信息要求与同段可获得性评价目的建立关系，F子型access。',
  '不把该段其他价格、可负担性定义整个复制给当前信息句；居民意见本身不自动F。'),
 ('V600-0378','M02',['I'],'input_or_scope_gap',
  'A/C把“该药品”解析为前款原研药，当前又明确新增适应症数据保护，支持I的解释有实质基础；但包中前款仅标为immediately_preceding_paragraph，尚不是机器可自动信任的父级锚点。',
  '在已提供材料内独立核验第七条连续指代关系并登记对象链，核验后按保护激励识别；不可仅放宽任意相邻段继承。',
  '指代可指向不同对象、邻段非同条或缺少上文时保留语境不足；不得猜测被引第六条其他内容。'),
 ('V600-0073','M03',['F'],'supported_gap',
  '“近3年未向…供应”是具体药品持续供应状态，负面状态同样关注保障获取。旧F规则未覆盖此供应否定表达。',
  '将已供应/未供应/停止供应等实际药品供应状态与保障信息联系，保留时间和对象。',
  '企业是否提交运单、单纯签收流程或办公用品供应不能因此F。'),
 ('V600-0370','M03',['F'],'supported_gap',
  '“维护药品配备情况”明确要求实际配备状态信息，共同澄清不允许因为“维护”而排除。旧规则只涵盖监测、分析、收集、报告等。',
  '把实质名词内容“药品配备情况”与状态信息行为分开建模；同文V600-0515重复条款只作重复机制提示。',
  '维护网站、维护药品名称字段、文件格式或上传时限不含状态内容时不纳入。'),
 ('V600-0193','M04',['F'],'supported_gap',
  '“缺乏有效治疗措施”明确治疗空白，不是罕见病名称推断。旧F04等覆盖“尚无有效治疗药物/手段”，漏掉缺乏+措施表达。',
  '对未满足治疗需要建立缺乏/没有/尚无等否定词与有效治疗手段/措施/药物关系。',
  '罕见病名称、单臂试验或外部对照本身不F；不把真实世界数据可获得性当用药可及。'),
 ('V600-0496','M04',['F'],'supported_gap',
  '“仍有部分患者未能得到有效治疗…治疗需求更高”是明确未满足需求，即使同句其他患者缓解率很高也不能冲掉该依据。',
  '把人群分支和否定治疗获取/获益保持在同一命题内，支持access；留存“未能得到有效治疗”。',
  '不能把任何低缓解率都推成F；需要文本实述未获满足需求，不能用模型自行评估临床缺口。'),
 ('V600-0063','M05',['I'],'supported_gap',
  '本句并非只列剂型规格；“参考数据改善片剂易碎性”明确具体产品特征改变，按手册可支持attribute。旧I07仅枚举剂型互改，未识别此种具体改良。',
  '要求“改良/改善”作用于可定位的药品结构或制剂特征，而非仅开发新规格；具体改良是否纳入应写入开发规则。',
  '同句“开发不同强度片剂及其他规格”本身不是充分I证据；一般适老化、便利性和适龄性不能I。'),
 ('V600-0513','M05',['I','F'],'supported_gap',
  'I依据为针对多病多药问题“改善制剂特征”；F依据为“此类用药行为”承接同段不同服药时间和给药途径的复杂性，不能只把多重用药二字当F。',
  'I留具体改良关系；F留同段p0044的用药复杂性指代，子型clinical_management。',
  '不继承该段末句电解质/辅料过量为本句S，也不把所有多病共存/合理用药自动F。'),
 ('V600-0465','M05',['F'],'supported_gap',
  '当前不仅描述老年身份，而是明确打开药品包装、量取和使用药物困难，可按宽保障构念中的具体用药管理障碍支持F。应保留其临床管理子型及敏感性，而非解释为狭义分配公平。',
  '具体任务+能力障碍+药品使用关系，F=clinical_management；若实施仍无法稳定区分便利与障碍，可先列语义复核。',
  '一般老年变化、建议易开包装不自动F；不能从前句误吸误服风险继承S。'),
 ('V600-0036','M06',['S'],'supported_gap',
  'AE/ADR总体及严重分级发生率明确药物安全证据。已提供抗肿瘤药安全总结的verified_object_scope，但旧scope当前命题白名单不含AE/ADR/人群，范围未激活；S词表也缺缩写，形成两层漏判。',
  '先消费已绑定范围；用词边界、大小写及定义表识别AE/ADR/SAE等，记录术语依据与范围依赖。',
  '未知缩写不能单独推安全；不得从安全资料适用范围把纯数据归档行全赋S。'),
 ('V600-0075','M06',['S','E'],'input_or_scope_gap',
  'S的安全性风险文字直接存在，但本单元/段落只有总结句、未含药物对象，包内无已核验对象范围；机器drug_object_evidence=null。A/C的药物语义解释合理，但不能把文件名当修复证据。E“获益”是否为临床获益也依赖对象。',
  '标记对象核验缺口；在授权且已核验的适用范围提供前，不简单用安全性一词放开所有场景。',
  '医疗机构、质量管理或网络系统的安全/获益-风险不自动S/E；此次不新增源文查证。'),
 ('V600-0051','M06',['Ec'],'input_or_scope_gap',
  '旧Ec08本能识别基金实际支出，但drug_object门控失败；包中仅有“规则二简易续约”分支，未见完整药品适用范围。A/C视其为药品续约支出，不应仅凭标题替代对象核验。',
  '将待核验药品支出对象与非命中区分；未来若补入已核验药品续约对象，仍须区分不同年份支出统计口径。',
  '医保基金泛支出、医疗服务基金支出不自动药品Ec；2025药品费用不能自动改名基金支出。'),
 ('V600-0158','M07',['S','E'],'supported_false_positive',
  'E01命中“质量管理活动的有效性”，E明确对象错置。S02命中风险控制，但当前只陈述试验质量管理风险，未明确用药损害；按主手册不因GCP场景自动S。',
  '按谓词补足语/所有关系识别“谁的有效性/风险”，局部抑制管理活动有效性；S需要药物损害或质量安全风险锚点。',
  '不得整句一律排除：同句若另有不良反应控制或疗效证据，保留对应S/E。'),
 ('V600-0092','M07',['Ec'],'supported_false_positive',
  '“申请人未…缴纳费用，终止药品注册审评审批”是行政申报收费，旧掩码仅收行政申报收费原词或不收任何费用，未覆盖实际表达。',
  '费用-缴纳主体-注册行政程序建立关系，抑制行政收费；保留同句独立药价或药费依据。',
  '不能看到申请人或审批就抑制所有费用；药品经济性研究要求仍可Ec。'),
 ('V600-0222','M07',['Ec'],'supported_false_positive',
  '机器Ec01的“价格”只在《健全药品价格形成机制…意见》标题内；当前实质目的为提高用药保障，并未提出价格评价或支付要求。F16命中则有当前实质依据。',
  '识别书名号引文的语义角色：仅列法律依据的标题不作维度证据；标题外独立要求继续编码。',
  '不得全局删除所有书名号内容：当前实质援引评价条件或明确要求执行价格规则须另判。'),
 ('V600-0167','M08',['S','E','Ec','I','F'],'input_unresolved',
  '句中虽出现1类创新药，但“并需满足以下条件之一”后项缺失，A/C均明确整条待定。开发新增注册创新类别词不应在缺条件输入上直接输出I=1。',
  '将关键未解析后项登记为input context_insufficient；候选二元规则仅在独立完整性审查后运行。',
  '不能把任何冒号都当缺失；自足组织职责引导句的现有单元边界经核验后可判。'),
 ('V600-0181','M08',['S','E','Ec','I','F'],'input_unresolved',
  '流程“如下图2和图3”但包内无对应图，两位均待定；机器F=1仅凭药品申报纳入目录。既是输入未完成，也暴露申报程序与获取结果混淆。',
  '缺少指向的关键图示先待定；不能拿其他样本同名图补进当前记录而不绑定版本。',
  '纯图题不等于纳入保障的具体实体决定；完整流程本身是否F仍应按实质内容判。'),
 ('V600-0223','M09',['I'],'boundary_dispute',
  'A=0、C=1。与已上市中药处方对比是明确比较资料，但未给新颖性、改良或创新分类标准；不能把任何产品对比等同创新。旧0并非已经证明的漏判。',
  '作为需界定的“比较资料与创新属性”边界，暂不把“与已上市…对比”泛化为I。',
  '若明确对比的是作用新颖性或具体改良，可I；这里只引用注册分类文件不能替代当前属性锚点。'),
 ('V600-0355','M09',['I'],'boundary_dispute',
  'A=0、C=1。“中医药创新工作”可以涵盖制度、服务、产业或药物；本句未说明具体研发支持或药品属性。不因同段其他部门科研任务而复制I。',
  '继续保留宏观职责与药物研发支持边界，避免为追C标签新增“中医药创新”无条件规则。',
  '同句若明确中药研发、创新成果保护或转化支持，可按独立证据I。'),
 ('V600-0204','M09',['F'],'boundary_dispute',
  'A=C=1仍不足以排除共同宽化。当前是患者诊治现状与治疗选择资料，前段是PED/临床需求；未明确获取不足、可得性状态或常规药物获得渠道。它可能支持获取评价，也可能仅支持研究设计，需明确构念边界。',
  '不要直接把“就诊路径/治疗选择/PED”泛化为F；列入真实领域复核或保留有理由的单维争议。',
  '若资料明确要求药物是否可获得、渠道障碍或无法得到标准治疗，才有更强F依据。'),
 ('V600-0486','M09',['F'],'boundary_dispute',
  'A=0、C=1。2:1是已入组者获得更优实验治疗的概率，不必然是原本无法治疗人群的获取安排。按现手册偏向保留A的边界，但此处不裁改首次标签。',
  '以“原本无治疗/无法获得药物+具体获取安排”约束研究获取F，不能仅以更多患者潜在更优治疗触发。',
  '对照V600-0592：同段明确末线无标准治疗并使其获得试验治疗，证据链更完整。'),
 ('V600-0396','M09',['I','F'],'boundary_dispute',
  'I的“支持参与创新药物早期临床研发”为明确漏判依据；F却A=1、C=0。同步研发申报审评上市本身不说明患者获取障碍，不能因为扩I规则连带扩F。',
  'I可按明确研发支持改进；F保留争议或0的谨慎解释，要求患者获取或保障锚点。',
  '国际同步、境内上市不自动F；若明确缩短患者等待或保障无药人群治疗，再评F。'),
 ('V600-0567','M09',['I'],'boundary_dispute',
  'A=C=1但本句是印发通知与“全链条支持创新药发展”总目标。它可能表达研发创新支持，也可能主要指上市支付推广；手册要求明确针对药物研发创新，不能机械覆盖“支持创新药发展”。',
  '保留总目标与具体研发支持的判别争议；优先开发实际研发、技术、保护权益等明确动作，不用通知标题充当依据。',
  '明确“支持创新药研发”可I；创新药支付对象或全链条政策标题不能自动I。'),
 ('V600-0574','M09',['F','Ec'],'boundary_dispute',
  'A/C均F=Ec=0，机器两项1。Ec价格协商仅为流程节点，较支持程序性误判；F则流程明确有协商成功纳入/失败不纳入，是否已构成保障准入实质条件存在可辩解释。旧F14还跨图示行拼接匹配，不能据一致0就制作排除所有流程的规则。',
  '先保留图示行/节点边界，避免跨行把目录名与另一分支纳入拼起来；F条件是否实质保障应另外审议。',
  '程序节点名非经济内容；完整具体纳入保障条件又不能仅因以流程图表达而一律F=0。'),
 ('D668-0158','M10',['I','F'],'subtype_gap',
  '二元I机器1，但只以I01改良型新药记attribute；当前本句已同时包含创新/改良对象+尚无防治手段/明显临床优势的资格双锚点，应审查qualification_advantage遗漏。F=0也漏“尚无有效防治手段”，虽E04已命中该词。',
  '允许当前单元内完成资格双锚点，而非必须verified_parent才可能I04；F的治疗空白词族保持“防治”与“治疗”一致。',
  '普通优先审评援引临床优势不能传递突破性创新范围；一般治疗优势没有创新锚点仍不能加资格子型。'),
 ('D668-0040','M10',['S','E','I','F'],'positive_control',
  '明确申报内容涉及安全性、有效性、创新性、公平性信息，旧机器与两AI均命中。此为内容资料要求，不是纯幻灯片格式；保留F的dimension_information，不能把F四子型混合。',
  '作为扩规则时保持的阳性控制：内容要求可以命中；同时保留独立实质与事务性信息的区别。',
  '只有文件命名/上传格式/公开保密而无新增内容要求时不自动赋相应维度。'),
]

phases = {}
source_files = {FROZEN/'candidate_predictions.json', FROZEN/'candidate_dictionary.py', FROZEN/'protocol.md', FROZEN/'protocol_clarifications.md', OLD/'V600-结果解读与正文处理.md'}
for phase in ('V600', 'D668'):
    manifest_path = OLD/phase/'抽样清单-研究者.json'
    manifest = {r['id']: r for r in json.loads(manifest_path.read_text())['rows']}
    source_files.add(manifest_path)
    phases[phase] = {'manifest': manifest}
    for kind, folder, pattern in (
        ('material', OLD/phase/'agent-A', '材料-*.json'),
        ('A', OLD/(phase+'-原始提交接收')/'agent-A', '结果-*.json'),
        ('C', OLD/(phase+'-原始提交接收')/'agent-C', '结果-*.json'),
    ):
        records = {}
        for path in sorted(folder.glob(pattern)):
            payload = json.loads(path.read_text())
            for i, row in enumerate(payload['rows']):
                records[row['id']] = {'value': row, 'file': str(path), 'json_pointer': '/rows/'+str(i), 'file_sha256': digest(path)}
        phases[phase][kind] = records

selected_review_ids = {phases[i.split('-')[0]]['manifest'][i]['review_id'] for i,*_ in specs}
predictions = {r['id']: r for r in json.loads((FROZEN/'candidate_predictions.json').read_text())['rows'] if r['id'] in selected_review_ids}
cases=[]
for display_id, mechanism_id, dimensions, status, assessment, suggestion, negative in specs:
    phase = display_id.split('-')[0]
    data = phases[phase]
    material = data['material'][display_id]
    m = material['value']
    origin = data['manifest'][display_id]
    prediction = predictions[origin['review_id']]
    assert prediction['unit_text_sha256'] == hashlib.sha256(m['text'].encode()).hexdigest(), display_id
    if 'record_sha256' in origin:
        assert prediction['record_sha256'] == origin['record_sha256'], display_id
    for kind in ('material','A','C'):
        source_files.add(Path(data[kind][display_id]['file']))
    cases.append({
      'case_id': display_id, 'original_id': origin['review_id'], 'phase': phase,
      'mechanism_id': mechanism_id, 'focus_dimensions': dimensions, 'audit_status': status,
      'source_title': m['source_title'], 'pages': m['pages'], 'unit_text': m['text'],
      'unit_text_sha256': prediction['unit_text_sha256'], 'original_input': material,
      'first_AI_A': data['A'][display_id], 'first_AI_C': data['C'][display_id],
      'old_machine_output': prediction, 'old_machine_source': str(FROZEN/'candidate_predictions.json'),
      'manual_basis': next(g[3] for g in groups if g[0]==mechanism_id),
      'independent_domain_AI_assessment': assessment,
      'proposed_general_rule': suggestion, 'negative_boundary': negative,
      'not_a_replacement_label': True,
    })

report = {
 'title':'既有样本错误机制审查', 'date':'2026-09-27',
 'identity':'领域审查AI；不是现实中的人工专家、金标准或新独立验证',
 'purpose':'为新开发版本提供可复核错误机制与边界，不回写旧标签、样本或正文',
 'baseline':'v4-development-24-candidate-17',
 'scope':{'selected_cases':len(cases),'phases_used':['V600','D668'],
          'selection':'先按已发布首次标签与旧机器差异检索，再按机制有目的选取；不是概率抽样或全1268条逐条复审',
          'excluded':'未读剩余池正文、未开corpus.jsonl、未重新抽样、未从源文增补上下文、未重跑改标签；H600/R200未另行复审',
          'known_exposure':'这些旧正式材料已用于本开发诊断；后续在其上结果只可称开发回看，不能称新的独立验证。'},
 'priority_findings':[
   'I的属性/激励词族、并列句法与固定字距造成可证实漏判；数据保护与原创成果是强证据例。',
   'F的具体供应/配备状态及未满足治疗需求具有多种真实表达，不能局限少数动词或固定否定短语。',
   '对象、明确指代、输入完整性和子类型需要分别建模；A=C=1不是跨过这些审查的许可。'],
 'mechanisms':[{'id':i,'title':t,'principle':p,'manual_basis':b} for i,t,p,b in groups],
 'cases':cases,
 'implementation_constraints':[
   '所有规则以当前文本证据和已核验关系为依据；不得按样本ID、AI标签或来源部门硬编码。',
   '对象核验只证明适用领域，不能提供本句不存在的价值维度内容。',
   '需保留0/1/待定和待核验状态；不把not_assessed当sufficient。',
   'I属性/研发支持/资格优势，F获取/可负担/临床管理/未细分资料要独立留痕并可做敏感性。',
   '相同原文、源文定位、实际机器证据、A与C首次理由必须可追溯；本文审查意见另存，不覆盖历史。',
   '不把旧样本开发分数、构造反例或AI一致性包装为真实人工有效性。'],
 'read_source_bindings':[{'file':str(f),'sha256':digest(f)} for f in sorted(source_files)],
 'verification':{'case_ids_unique':len({c['case_id'] for c in cases})==len(cases),
                 'all_case_text_hashes_match_frozen_predictions':True,
                 'all_D668_case_record_hashes_match_frozen_predictions':True,
                 'first_receipt_sources_used':True,
                 'old_files_modified':False},
}
(OUT/'既有样本错误机制审查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

def link(path,label): return f'[{label}]({path})'
def focus_labels(c,source):
    val=c[source]['value'] if source in ('first_AI_A','first_AI_C') else c[source]
    return '、'.join(d+'='+str(val['labels'][d]) for d in c['focus_dimensions'])

lines=[
 '# 既有样本错误机制审查', '',
 '日期：2026-09-27。执行者：领域审查 AI。本文不是现实人工专家裁定、人工金标准或新一轮独立验证。', '',
 '**关键判断：创新性和公平性存在可依据原文与现行手册支持的漏判，但不能将所有 A/C 阳性都追认为机器错误。最优先的修复方向是属性/激励的语义关系、实际药品供应状态，以及有证据的句间指代；输入缺口和构念争议必须另外保存。**', '',
 f'本次有目的审查 {len(cases)} 个已发表 V600/D668 病例，覆盖10类机制及阳性控制。为寻找机制使用了旧样本差异检索，未逐条复审全部1268条，不能以本病例数估计错误频率。H600/R200没有另行复审。未打开剩余池正文或任何 corpus.jsonl，未抽新样本、未修改旧标签、旧样本、源文或论文。对应旧机器输出来自候选17的既有冻结预测；每条文本哈希均与该预测匹配。', '',
 'A/C 均保留首次封存标签和理由。下列“支持漏判”是另一名领域 AI 在手册约束下的诊断意见；不替换 A/C，也不生成所谓最终真值。“输入/对象缺口”不能直接修成1，“边界争议”不能用一致票数自动消除。此后使用这些材料调算法，结果只能作为开发回看。', '',
 '## 规范与复核位置', '',
 '- '+link(FROZEN/'protocol.md','冻版五维协议 v1.3')+'；'+link(FROZEN/'protocol_clarifications.md','V600共同执行澄清')+'。',
 '- '+link(FROZEN/'candidate_dictionary.py','候选17源码')+'；'+link(OLD/'V600-结果解读与正文处理.md','原轮结果与低召回边界')+'。',
 '- '+link(OUT/'既有样本错误机制审查.json','逐病例证据JSON')+'保存完整原始输入、可用上下文、A/C首次提交、旧机器证据/抑制、文件SHA256及JSON指针。下文短引文为定位摘录，未修正文句。', '',
 '## 机制与病例', '',
]
status_names={'supported_gap':'支持存在规则漏判','input_or_scope_gap':'对象/关系核验缺口，不能直接改1','supported_false_positive':'支持存在对象或事务性误判','input_unresolved':'应保留材料不足','boundary_dispute':'保留构念边界争议','positive_control':'已有正确命中的阳性控制','subtype_gap':'二元标签与子型分开诊断'}
for gid,title,principle,manual in groups:
    lines += [f'### {gid} {title}', '', principle, '', '手册依据：'+manual, '']
    for c in cases:
        if c['mechanism_id']!=gid: continue
        m=c['original_input']['value']
        page='页码未附' if not c['pages'] else '页'+','.join(map(str,c['pages']))
        pars=', '.join(p['paragraph_id'] for p in m['contexts'].get('paragraph_context',[]))
        lines += [f'**{c["case_id"]} / `{c["original_id"]}` — {status_names[c["audit_status"]]}**', '',
                  f'定位：{c["source_title"]}；{page}；段落 {pars}。'+link(c['original_input']['file'],'材料')+' `'+c['original_input']['json_pointer']+'`。', '',
                  '> '+c['unit_text'].replace('\n','\n> '), '',
                  '旧机器：'+focus_labels(c,'old_machine_output')+'。',
                 ]
        ev=c['old_machine_output']['evidence']
        lines += ['机器证据：'+('；'.join(f'{e["rule"]}/{e["dimension"]}「{e["text"]}」' for e in ev) if ev else '无命中证据')+'。'+('对象证据为空。' if not c['old_machine_output'].get('drug_object_evidence') else ''),'']
        for who,key in [('A','first_AI_A'),('C','first_AI_C')]:
            r=c[key]['value']
            reasons='；'.join(d+'：'+r['dimension_reasons'][d] for d in c['focus_dimensions'])
            lines += [f'{who} 首次：'+focus_labels(c,key)+'。'+reasons+' '+link(c[key]['file'],who+'封存提交')+' `'+c[key]['json_pointer']+'`。','']
        lines += ['独立审查：'+c['independent_domain_AI_assessment'],'',
                  '建议：'+c['proposed_general_rule'],'',
                  '负例边界：'+c['negative_boundary'],'']
        if c['mechanism_id'] in {'M02','M05','M06','M08','M09','M10'}:
            relevant=[]
            # Include exact supplied contexts only; headings are not promoted to parents.
            for x in m['contexts'].get('paragraph_context',[]):
                if x['text']!=m['text']:
                    relevant.append('同段 '+x['paragraph_id']+'：'+x['text'])
            if c['case_id']=='V600-0378':
                relevant.append('仅位置相邻的前段（未自动视为已核验父级）：'+m['contexts']['immediately_preceding_paragraph']['text'])
            if c['case_id']=='V600-0036':
                relevant.append('已绑定对象范围：'+m['contexts']['verified_object_scope'][0]['text'])
            if c['case_id']=='V600-0204':
                relevant.append('提供的前段：'+m['contexts']['immediately_preceding_paragraph']['text'])
            if relevant:
                lines += ['必要上下文（原材料内）：','']
                lines += ['> '+t.replace('\n','\n> ') for t in relevant]
                lines += ['']
lines += ['## 开发使用边界', '',
          '这些病例足以提出可证伪的规则假设，但不支持宣称新方法已经有效。推荐按“对象与输入状态—当前内容—关系依赖—来源子型”顺序实现，并为每类规则准备独立负例边界。负例边界中的泛化句型只是研发约束，不冒充新的政策样本或验证结果。', '',
          '不得用源ID或A/C标签直接决定输出。保留每条原文、上下文来源和机器证据跨度；对补充或实质修复后的输入另存版本，不把旧标签直接迁移为新真值。本审查未建立新的概率检验集、未做新抽样，也不改变旧报告的统计结论。', '',
          '仍需保留的关键争议：比较资料是否足以表示创新属性；宏观支持目标是否明确指向药物研发创新；患者治疗路径资料是否自带保障获取含义；试验分配概率、同步上市与目录流程图是否构成获取安排。特别是 V600-0204、V600-0567 即使 A=C=1，也没有在此审查中被照单纳入修复目标。', '',
          '核验：病例ID无重复；全部病例原文哈希匹配冻结预测；A/C来源为首次原始提交接收目录；仅新目录生成审查文件。']
(OUT/'既有样本错误机制审查.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'cases':len(cases),'mechanisms':len(groups),'statuses':{s:sum(c['audit_status']==s for c in cases) for s in status_names},'outputs':[str(OUT/'既有样本错误机制审查.md'),str(OUT/'既有样本错误机制审查.json')]},ensure_ascii=False))
