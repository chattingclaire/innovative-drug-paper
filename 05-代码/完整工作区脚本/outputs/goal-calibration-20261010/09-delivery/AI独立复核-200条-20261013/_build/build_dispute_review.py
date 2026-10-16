import hashlib
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / '分歧复核-20261013'
HUMAN = BASE.parent / '独立真人判读-200条-20261013' / '发给编码者A'
MANUAL = HUMAN / '共同编码手册.txt'
comparison = json.loads((BASE / '_build/comparison.json').read_text())
materials = {r['blind_id']: r for r in json.loads((BASE / 'AI复核者A/read_materials.json').read_text())}

# Decision, provisional preference, classification, concise rationale, frozen rule lines.
decisions = {
 ('A-016', 'E'): (0, None, '语境越界', '当前要求检验一般因果推断方法的假设；后句的疗效分析是应用例证，不能替换当前方法要求的对象。', [15,22,98,100]),
 ('A-023', 'Ec'): (0, None, '规则制定预告误作实质内容', '“另行制定”保留规则制定事项，未设置本句的支付内容或形成机制；0并非因为未来语气。', [9,22,31,110,114]),
 ('A-036', 'I'): (None, 1, '研发支持与支付准入边界', '为确证性研究保留目录申报机会；是否已构成I3研发支持，须与A-120、A-178统一解释。', [124,127,137]),
 ('A-084', 'S'): (0, None, '相容性与药物风险混同', '一般相容性评估未明确药物损害关系；后句针对窄治疗窗药物的混用限制是独立子群命题。', [22,42,84,86,88,90]),
 ('A-088', 'S'): (1, None, '漏用操作性标准援引', '综合审评通过决定批准上市；同一审评的明确内容含安全性，可补全这一标准—待遇关系。', [41,50,84,86]),
 ('A-088', 'E'): (1, None, '漏用操作性标准援引', '综合审评通过决定批准上市；同一审评的明确内容含有效性，可补全这一标准—待遇关系。', [41,50,94,96]),
 ('A-105', 'I'): (1, None, '将支持通道适用误作形式操作', '按研发需求选择实际30日或60日审评路径；同段明确30日通道向创新药临床试验倾斜审评资源。', [35,44,124,127,137]),
 ('A-119', 'S'): (0, None, '一般质量/伦理保护误作药物风险', '全过程质量管理与参与者权益、安全是概括质量伦理要求，当前未建立药物造成损害或风险的联系。', [84,86,88,90]),
 ('A-120', 'I'): (None, 1, '研发支持与支付准入边界', '“5年＋3年”是具体目录申报机会；是否因其服务确证性研究而成为研发支持，手册边界仍需统一。', [124,127,137]),
 ('A-122', 'I'): (None, 1, '目录政策服务与研发支持边界', '存在面向创新药的前置点对点目录指导；服务内容是主规格、参照药、支付范围，是否属于研发支持尚有边界。', [22,124,127,137,139]),
 ('A-126', 'S'): (1, None, '漏用确指资格条件', '满足《实施办法》条件才能申请数据保护；同版第七条分支要求证明安全性的数据，不能只读取15日期限。', [41,50,60,86]),
 ('A-126', 'E'): (1, None, '漏用确指资格条件', '满足《实施办法》条件才能申请数据保护；同版第七条分支要求证明有效性的数据，不能只读取15日期限。', [41,50,60,96]),
 ('A-149', 'S'): (0, None, '一般质量/伦理保护误作药物风险', '当前定义质量管理并保护参与者权益、安全；邻近另一术语的药物风险内容不能移入本条。', [22,42,84,86,88,90]),
 ('A-160', 'Ec'): (1, None, '标签可保留但证据须纠正', '包内2025年《若干措施》第（七）条直接规定商保目录药品结算价协商；应据此判1。', [44,46,112]),
 ('A-160', 'F'): (None, 1, '覆盖范围缺口与公平关系边界', '2025年条款将患者显著获益、超出基本医保范围与重点推荐补充保障相连；是否达到所需治疗保障缺口门槛尚须统一。', [44,46,147,151,154,158,160,164,166]),
 ('A-178', 'I'): (None, 1, '研发支持与支付准入边界', '“这一安排”确指同段5＋3申报机会，不能只当孤立口号；与A-036、A-120共用一个边界问题。', [22,44,124,127,137]),
 ('A-117', 'I'): (0, None, '未达到补全门槛而误列缺材', '当前仅记载2024年启动计划，没有直接连接创新研发对象或可用支持内容，不能倒用后续延伸计划。', [44,46,124,127,214,218]),
 ('A-117', 'F'): (0, None, '未达到补全门槛而误列缺材', '当前仅有年份、计划名和启动沿革，未表达患者治疗缺口与针对性安排的关系，无须继续追索旧计划全文。', [44,46,151,154,214,218]),
}
original_cases = comparison['differences'] + comparison['pending']
assert set(decisions) == {(r['A_id'],r['dimension']) for r in original_cases}

def link(label, path, line=None):
    target = str(path) + (f':{line}' if line else '')
    return f'[{label}](<{target}>)'

def context(rid, index=0):
    fields = materials[rid]['fields']
    prefix = f'/source_record/contexts/{index}'
    return {'context_id': fields.get(prefix+'/context_id'), 'text': fields.get(prefix+'/text'),
            'source_paragraph': fields.get(prefix+'/source_ref/locator/paragraph_id')}

records = []
for r in original_cases:
    value, preference, category, reason, lines = decisions[r['A_id'],r['dimension']]
    rec = dict(r)
    rec.update({
        'review_type': 'AI首判后的证据复核建议',
        'status': '可据现有手册判定' if value is not None else '规则边界待统一',
        'recommended_value': value,
        'provisional_preference': preference,
        'classification': category,
        'reason': reason,
        'current_text': materials[r['A_id']]['current'],
        'source_material': str(HUMAN / '材料' / (r['A_id']+'.html')),
        'context_for_review': context(r['A_id']),
        'manual_lines': lines,
        'critical_material_missing': False,
        'original_submission_modified': False,
    })
    if r['A_id'] in {'A-016','A-084','A-088','A-119','A-126','A-149'}:
        detail_file = 'se-review.json'
    elif r['A_id'] in {'A-023','A-160'}:
        detail_file = 'economy-fairness-review.md'
    else:
        detail_file = 'innovation-review.json'
    rec['full_evidence_review'] = str(OUT / detail_file)
    if r['A_id'] == 'A-160':
        attachment = HUMAN / '附件/fe38c53150311f8eb8ba96f0b690cbcbc1e12a3a63e4ab12cbed407aa68bcc82.txt'
        rec['same_version_mechanism_evidence'] = {'path': str(attachment), 'line': 17, 'version': '2025年6月30日，第（七）条', 'verbatim': attachment.read_text().splitlines()[16]}
    records.append(rec)

protect = json.loads((OUT / '首判保护记录.json').read_text())
checks = [{'path': entry['path'], 'unchanged': hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest() == entry['sha256']} for entry in protect['files']]
assert all(r['unchanged'] for r in checks)
counts = Counter(r['status'] for r in records)
assert counts == {'可据现有手册判定':13, '规则边界待统一':5}
settled_disputes = [r for r in records if r['A']['value'] is not None and r['recommended_value'] is not None]
resolved_pending = [r for r in records if r['A']['value'] is None and r['recommended_value'] is not None]
assert len(settled_disputes)==11 and len(resolved_pending)==2

data = {
 'identity':'AI复核分歧的事后证据审查；不是真人首判或已批准的新金标准',
 'date':'2026-10-13',
 'scope':{'source_records':len({r['unit_id'] for r in records}), 'dimension_cases':18, 'initial_disagreements':16, 'initial_pending':2},
 'summary':dict(counts),
 'critical_missing_material_cases':0,
 'value_convention':'recommended_value为本次可判建议；规则边界为null，provisional_preference仅保留技术倾向，不能当已裁决标签。',
 'manual':{'path':str(MANUAL),'sha256':hashlib.sha256(MANUAL.read_bytes()).hexdigest()},
 'records':records,
 'first_submission_preservation_checks':checks,
 'recomputed_initial_agreement':False,
}
(OUT / '分歧复核建议.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

lines = [
 '# 200条AI独立复核：分歧再识别',
 '',
 '日期：2026年10月13日。范围：14条原文中的16项首判分歧及2项待定，共18项维度判断。',
 '',
 '**按冻结手册，本次建议13项可判定；5项保留为规则边界，集中于3个口径问题。没有需要继续补材料的关键缺材项。** 13项中，11项是原分歧的判定建议，2项是将A-117的I、F由待定改为0的建议。',
 '',
 '这是AI首判后的证据复核。A/B首次Excel、首次JSON、原对照报告和共同手册均保留原样；本报告与正在进行的真人盲评分别保存。表中“待统一”项的倾向意见不计作最终裁决，也不据此重算首轮一致率。',
 '',
 '## 逐项结论',
 '',
 'S＝安全性；E＝有效性；Ec＝经济性；I＝创新性；F＝公平性。编号链接打开原始材料，首判列按A/B顺序列示。',
 '',
 '| A编号／B编号 | 维度 | 首判A/B | 本次建议 | 分歧实质 |',
 '|---|---|---|---|---|',
]
for r in records:
    a = '待定' if r['A']['value'] is None else str(r['A']['value'])
    b = '待定' if r['B']['value'] is None else str(r['B']['value'])
    suggestion = str(r['recommended_value']) if r['recommended_value'] is not None else '待统一（倾向1）'
    lines.append(f"| {link(r['A_id'],r['source_material'])}／{r['B_id']} | {r['dimension']} | {a}/{b} | **{suggestion}** | {r['reason']} |")

lines += [
 '', '## 可判项：证据如何改变结论', '',
 '### 1. A-016/E：建议0；A-084/S：建议0', '',
 '**A-016**当前要求对“上述各种因果推断方法”的假设作敏感性分析，评价推断稳健性。回查原PDF，第29页总领一般因果推断方法；第30页包括药物暴露效应，第31—32页讨论一般处理—结局的因果效应。其所指范围没有限定为药物疗效。第34页同段后续以“例如”引入疗效估计偏倚的应用例证。A把该例证中的效果对象移入当前通用方法要求，超过必要语境的补全范围。依手册第15、98、100行，建议E=0；这不影响后续疗效例证自身可以表达E。',
 '',
 '**A-084**当前鼓励评估药物与食品、饮品的相容性，列的是物质类别、接触时间、面积和操作注意事项。原PDF第13页（印刷第10页）的前句侧重吞咽、口感；后句另以“对于治疗窗窄的药物”规定混用限制。后句不是当前一般相容性评估的定义或明确回指解释。依手册第84—90行，不能从相容性或另一子群命题推成当前已有药物损害关系，建议S=0。',
 '',
 '### 2. A-088、A-126的S/E：四项均建议1', '',
 '**A-088**规定“综合审评结论通过”才批准上市；紧前第三十八条明确同一综合审评评价安全性、有效性及质量可控性。这里是一般性的标准—上市待遇关系，可按手册第41、50行补入确指标准。',
 '',
 '**A-126**不仅规定15日申请期限，还以符合《实施办法》的数据保护条件作为申请资格。同版《实施办法》第七条这一实际资格分支，明确要求提交用于证明安全性、有效性和质量可控性的全部试验数据。S/E来自被援引分支的实质证据条件，不来自“数据保护”的名称；该分支条件不据此推广到全部药类。',
 '',
 '### 3. A-119/S、A-149/S：均建议0', '',
 '两条分别规定或定义临床试验质量管理，使用“保护试验参与者的权益和安全”等概括表达。当前没有明确药物造成的损害、风险或对应控制关系。A-149附近另一术语包含药物获益/风险，也不能赋给本条。按手册第90行，一般质量和伦理保护不能仅凭“安全”字样纳入S。该判定不评价这些管理活动在现实中是否有安全作用。',
 '',
 '### 4. A-105/I：建议1；A-023/Ec：建议0', '',
 '**A-105**要求按研发实际需求选择30日通道或60日默示许可；同段明确30日通道向符合条件的创新药临床试验倾斜审评资源。当前是在适用两种实质审评路径，达到I3的对象—可用安排—直接联系要求。B要求当前重新授予支持，抬高了手册第127、137行的门槛；并列的试验信息登记动作不消除前半句的支持内容。',
 '',
 '**A-023**“支付标准的制定和调整规则另行制定”是规则制定保留条款。其上下文说明支付标准是药费基准，但不能把前句的实际付款命题移给末句。本句未设置形成方式、支付责任、适用条件或调整后果，故Ec=0。未来、尚未实施或没有金额均不是本次判0的理由。',
 '',
 '### 5. A-117/I、F：两项待定均建议0', '',
 '当前完整句只有“2024年药审中心启动了‘关爱计划’试点工作”。依手册第46行，历史机制补全须由当前直接连接支持对象或内容；仅年份、名称和启动沿革尚未达到这一门槛。后句记录实践经验，进一步的罕见病创新研发与治疗需求安排属于后续“关爱计划-延伸”，不能倒灌原句。',
 '',
 '因此，现有固定记录足以判I=0、F=0，不需要为这两项继续请求2024旧计划全文。这一判断只说明当前记录未表达对应关系，不断言旧计划在事实上没有研发或公平功能。',
 '',
 '### 6. A-160/Ec：建议1，但A的原证据链必须修正', '',
 '当前明确陈述2025年提出增设商保创新药目录。原共同材料已包含其确指的2025年《支持创新药高质量发展的若干措施》，第（七）条直接写明：', '',
 '> 通过协商合理确定商保创新药目录内药品结算价，探索更严格的价格保密机制。', '',
 '这属于同一具名安排的直接价格形成机制，按手册第44、46、112行足以支持Ec=1。A原来采用的2026问答中“三除外”等内容跨了版本或平行措施范围；其中按病种付费内容对应2025年第（十四）条，不能直接搬给第（七）条的目录设立。B正确指出推荐目录不等于实际承保，但漏掉了独立成立的结算价协商依据。',
 '',
 '此项应同时记录“标签1可保留”和“原理由不成立、换用同版正确证据”，不能仅凭最终标签相同就认为首判证据无误。',
 '',
 '## 五项边界：收敛为三个明确问题', '',
 '以下材料已完整；问题在于现有定义的适用范围。技术倾向均为1，但在口径正式统一前，本次机器可读建议保留null，并另存倾向。',
 '',
 '### 边界一：A-036、A-120、A-178的I，共用一个“5＋3”证据链', '',
 '三条来自同段：因附条件上市药品完成确证性研究、积累验证数据需要时间，保留更宽裕的目录申请机会；具体安排最多“5年＋3年”；末句称其体现医保对创新和证据的支持。A-178的“这一安排”有明确所指，应读回具体机制，不能只当孤立口号。',
 '',
 '**倾向1的依据：** 有具体可用的申请机会，也有与确证性研究时间相连的支持目标。I3允许创新研发是支持目标，不能额外要求所有对象都先具有某个法定创新注册分类。',
 '',
 '**仍需统一的范围：** 机会发生在支付目录准入端；手册又明确创新药支付待遇不自动构成研发支持。需明确：为完成确证性研究而保留的目录申报机会，是否已满足I3“研发支持机会”。接受这条关系，三条均为1；不接受，三条均为0。三条保留各自记录，不合并计数。',
 '',
 '### 边界二：A-122/I，前置目录政策指导是否属于研发支持', '',
 '当前安排有针对性的目录准入政策指导；同一（三）条允许创新药上市申请受理后同步申请点对点指导，交流主规格、参照药、支付范围。该项置于“加大创新药研发支持力度”之下。',
 '',
 '**倾向1的依据：** 有实际服务、明确对象和前置申请机会，强于单列交流形式；I3也未限于研究设计的技术答复。',
 '',
 '**仍需统一的范围：** 具体内容是支付准入政策，原文没有明确反馈到研究设计或进一步研发。栏目标题与前置阶段能否和当前实际服务共同构成研发支持目标，应作统一解释；不能只靠标题赋I，也不能只因服务谈支付便一律排除。',
 '',
 '### 边界三：A-160/F，目录外覆盖缺口是否达到所需治疗保障缺口', '',
 '2025年第（七）条将“患者获益显著且超出基本医保保障范围”的创新药重点纳入商保推荐目录。',
 '',
 '**倾向1的依据：** 原文有“覆盖范围缺口—重点推荐补充保障”的定性关系，多于一般支付口号或普通名单。',
 '',
 '**仍需统一的范围：** 药品未被基本医保覆盖，是否在这一联合条件下已经表达“所需治疗保障缺口”？手册第154、160行要求这层关系，第158、164行又排除单独患者获益和普通名单。原文没有直接说患者缺乏足够的已保障治疗选项，但也不能临时加上“必须无替代药或已失治”的一般门槛。',
 '',
 'A采用的2026年“基本目录已有同类保障较为充分的品种不纳入”确能加强公平关系，但不能反推为2025年设立时已适用的同版条件。因此，本次仅根据2025年原条款保留倾向1和明确边界。',
 '',
 '## 核验与留存', '',
 '- 18项建议与原对照JSON逐项匹配，覆盖全部16项分歧和2项待定，无新增、无遗漏；涉及14条原文。',
 '- 当前引文、同段语境和手册依据单独留存；原PDF、同版附件回查用于确定证据的实际范围。未以网络外查内容补入判据。',
 '- 已校验保护清单内6个文件的SHA-256，A/B首判Excel、JSON、原对照报告及冻结手册均未改动。',
 '- 保留首轮998项可配对判断中982项一致的原记录；本次事后复核不替换该首轮结果，也不形成真人一致性数据。',
 '',
 '## 来源与复核记录', '',
 '- '+link('冻结共同编码手册', MANUAL)+ '：必要语境第22、41、44—50行；S第84—90行；E第94—100行；I第124—139行；F第147—166行；缺材第214—218行。',
 '- '+link('2025年《若干措施》原附件，第（七）条', HUMAN/'附件/fe38c53150311f8eb8ba96f0b690cbcbc1e12a3a63e4ab12cbed407aa68bcc82.txt',17)+'。',
 '- '+link('A-126确指的《实施办法》同版附件', HUMAN/'附件/e0e9f205f2ba8bdd245da3ebeee78fe68f86b3c7d791b23585ff59acab9ba88b.html')+'。',
 '- '+link('经济性／公平性详细复核', OUT/'economy-fairness-review.md')+'；'+link('创新性及A-117详细复核',OUT/'innovation-review.json')+'；'+link('安全性／有效性详细复核',OUT/'se-review.json')+'。',
 '- '+link('18项机器可读建议及首判保护校验',OUT/'分歧复核建议.json')+'。',
 '',
]
(OUT/'分歧复核结论.md').write_text('\n'.join(lines))
print(json.dumps({'report':str(OUT/'分歧复核结论.md'),'counts':dict(counts),'unique_records':len({r['unit_id'] for r in records}),'protected_files_unchanged':len(checks)},ensure_ascii=False,indent=2))
