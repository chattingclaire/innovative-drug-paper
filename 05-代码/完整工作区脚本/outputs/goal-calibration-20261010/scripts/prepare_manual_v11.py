"""Create a new development manual and preserve both first submissions."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
old = ROOT / '03-manual/common-manual-v1.0-development.md'
target = ROOT / '03-manual/common-manual-v1.1-development.md'
assert not target.exists(), 'Do not overwrite a released development version'
text = old.read_text()
replacements = [
    ('# 五维共同编码手册 v1.0：开发校准版', '# 五维共同编码手册 v1.1：开发校准版'),
    ('- “详见工作方案”“按有关规定”及程序名称属于一般指引，不无限递归展开。仅“已纳入／不符合某程序条件”这种状态，不能据名称猜出全部实质标准；当前具体讨论的标准仍据实际内容判断。',
     '- “详见工作方案”“按有关规定”及程序名称属于一般指引，不无限递归展开。只报告某品种“已纳入／现已不符合某程序条件”等身份或状态，没有本记录的标准核验、条件要求或标准—待遇后果关系时，不从名称展开全部实质标准。当前直接要求核验、满足确指标准，或以该标准是否满足决定授予、维持、限制、终止实质待遇的一般规范，属于操作性标准援引：完整同版本标准核明后，按实际被援引内容逐维判断。一般终止规范无需指出现实中是哪项失败才记录标准议题；但不得把“不符合整体条件”改写为某药无效、不安全或所有条件均失败。并列“或”逐支判断，纯手续分支不继承另一分支的评价内容。'),
    ('设立与撤回、肯定与否定使用同一门槛。创新支持依此规则补足后仍须满足I3，公平支持仍须满足F的对象与公平关系。',
     '设立与撤回、肯定与否定使用同一门槛。创新支持依此规则补足后仍须满足I3，公平支持仍须满足F的对象与公平关系。\n\n“当前”指固定记录的命题，不表示只有现在时才可编码。过去、完成或未来时态及背景位置均不能单独决定标签。若当前记录明确陈述在某时期设立或实施同一具名安排，并直接连接支持对象或内容，可补该时期同版本的必要定义和直接机制；这表示曾实施的支持议题，不证明今天仍可申请。仅年份、名称、沿革、名单身份或笼统宗旨，没有独立实质行动/内容关系时，不展开。具名机制补全只用于解释当前行动与可用安排，不能把该方案中的全部安全义务、效果要求、费用或平行措施一并复制给当前记录；当前另有操作性标准援引时，再按该路径逐维检查。确指的关键机制确实缺失时登记补材；不能因任何句子可能另有背景而无限请求材料。'),
    ('基金可负担不同于患者可负担，药价信息不等于经济效率，也不自动构成F。',
     '基金可负担不同于患者可负担，药价信息不等于经济效率，也不自动构成F。\n\n**支付内容的条件与形式操作：** 当前明确授权、限制、要求或以条件准许改变药品支付标准、支付范围、支付责任时，构成经济内容的制度安排。成员可与直接父谓词组成“条件—支付后果”命题；必要前置条件不必是批准的充分条件，也不要求新金额、范围清单或调整已成功。普通目录申请身份、提交材料、签章、截止日期、字段非空等没有上述内容后果时仍排除；不得从整个目录准入背景推定支付。只核验格式的“支付范围字段不能为空”为0；“符合条件者可申请调整支付范围”或具体规定哪类药须经申报方可调整，是支付变更的适用/限制关系。用途变化本身不因此成为有效性或创新性。I4同样要求创新/改良资格与当前实质权利义务相连，不能对一维使用内容门槛、另一维使用字段门槛。'),
    ('**患者可负担性：**',
     '**定性与比喻：** 公平关系可以定性表达，不要求金额、病种、药名或收入数值，也不因使用比喻而一律排除。具体路径仍须能从当前及有限语境写出可辨认的治疗需要差别、所需药品保障缺口、获取障碍或患者负担关系，并与评价/保障安排直接相连。“保基本”“聚焦临床需求”“补短板”“雪中送炭”等单独或并列的导向，没有明确这层关系时，不由编码员补成患者缺口；一般临床价值优先或基金控费也不能替代F。若同政策确指解释把相应表达定义为优先填补未满足的所需治疗或按不同需要给予适当保障，可在共同材料加入核明片段后判断。此时理由只写原文关系，不补造收入阶层、地域差异、断供或无有效药。\n\n**患者可负担性：**'),
]
for before, after in replacements:
    assert text.count(before) == 1, (before, text.count(before))
    text = text.replace(before, after)
text += '''
## 十一、开发校准版本记录

v1.1依据封存首判后的两份独立开发讨论，澄清操作性标准援引、支付变更条件、定性公平关系和历史实施陈述。首判、讨论、补材后重判各存独立文件。此版本仍用于开发校准，不能称为冻结后的最终检验手册。共同材料修复或新增官方解释属于材料版本变化，不得伪装成原包一直包含的信息。

同版官方解释仅能补足其明确对应的措施、目标对象和问题。解释权威性不允许把全篇目的或一个措施的缺口移植到所有兄弟项。真实性、版本/时期与问题—措施映射须可核；无法核明的片段在来源清单标明状态，不能宣称已经认证。
'''
target.write_text(text)
discussion_paths = [ROOT/f'04-calibration/pilot01/{coder}/discussion01.json' for coder in ['A','B']]
initials = [ROOT/f'04-calibration/pilot01/{coder}/{name}.jsonl' for coder in ['A','B'] for name in ['labels']]
initials += [ROOT/f'04-calibration/pilot01/{coder}/submission.json' for coder in ['A','B']]
changes = {
    'status': 'development_rule_decisions_not_final_validation',
    'date': datetime.now().isoformat(timespec='seconds'),
    'decision_author': {'type':'AI_primary_agent','model_requested':'GPT-6.1 Sol','reasoning_effort_requested':'ultra'},
    'prior_manual': {'path':str(old),'sha256':sha(old)},
    'new_manual': {'path':str(target),'sha256':sha(target)},
    'discussion_sources':[{'path':str(p),'sha256':sha(p)} for p in discussion_paths],
    'initial_submissions_preserved':[{'path':str(p),'sha256':sha(p)} for p in initials],
    'selection_basis':'Current normative content and common construct/limited-context protocol, not score or desired department shares.',
    'decisions':[
        {'id':'DC01','topic':'操作性标准援引与资格状态','records':['RECODE25-00036','RECODE25-00038'],'rule':'仅身份状态不展开；一般规范以同版确指标准决定待遇后果，可读完整标准逐维判，不推定具体失败原因。','development_candidate':{'E':1},'adopted_argument':'A、B讨论均支持一般标准—后果关系；共同门槛适用于五维。','rejected_argument':'以尚未知个别失败项排除规范议题，会混淆文本关注与个别药品属性；纯手续分支仍无E。','sources':['pilot01/A/discussion01.json:B01','pilot01/B/discussion01.json:01','原2020突破性治疗工作程序及同版适用条件']},
        {'id':'DC02','topic':'支付范围变更条件与手续','records':['RECODE25-01955'],'rule':'直接条件—支付变更后果可Ec；材料流转、字段非空和普通目录身份仍0。','development_candidate':{'Ec':1},'adopted_argument':'父谓词方可调整与当前明确支付范围组成直接经济安排，不以已给金额为额外门槛。','rejected_argument':'不能把所有申请环节或所有支付文件名称视为经济安排；此处正例有指定的内容变更后果。','sources':['pilot01/A/discussion01.json:B02','pilot01/B/discussion01.json:02','原2024医保调整工作方案父子条款']},
        {'id':'DC03','topic':'比喻与定性公平关系','records':['RECODE25-03704'],'rule':'定性关系可纳入；保基本/临床需要/比喻仍须可辨认需要差别、保障缺口或负担关系。','development_candidate':{'F':0},'adopted_argument':'现包没有给出比喻所对应的保障缺口或不同需要分配标准，基金安全/一般临床优先不能补成公平。','rejected_argument':'从保基本将比喻翻译为明确患者需要层级，超过现有原文；这不是要求数值或公平字样。','sources':['pilot01/A/discussion01.json:B03','pilot01/B/discussion01.json:03','https://www.who.int/health-topics/health-equity','Oliver与Mossialos(2004)按需要的获取机会原则'],'source_limit':'WHO与原论文支持公平概念；本句比喻的二元门槛是本研究操作化，不冒称原论文直接裁定。'},
        {'id':'DC04','topic':'历史实施与时态','records':['RECODE25-02233','RECODE25-01729','RECODE25-02269'],'rule':'当前记录有独立实施/设立行动和支持联系时，允许补行动时期同版本机制；纯名称沿革不展开。','development_candidate':{'I':None},'candidate_status':'待共同2024机制补材后另行重判','adopted_argument':'文本关注不要求今天仍可申请；完成时与背景位置不能作为独立排除项。','sources':['pilot01/A/discussion01.json:B04','pilot01/B/discussion01.json:04','2024官方试点方案 prospective-common-supplements.jsonl']},
        {'id':'DC05','topic':'同政策解释补足配送措施','records':['RECODE25-04915'],'rule':'统一加入同版官方解释，核明所需药品获取/持续供给问题与当前措施直接映射，再逐维判；不全篇传播。','development_candidate':{'F':None},'candidate_status':'待来源核明与共同补材后另行重判','adopted_argument':'现有初判包不含这段解释；允许下一版有限补材，保留初判0及其真实输入。','sources':['pilot01/A/discussion01.json:B05','pilot01/B/discussion01.json:05','2024NHC同政策官方解释 prospective-common-supplements.jsonl']},
    ],
    'development_candidate_use':'AI开发裁定意见；不是真人参照，不回写首判，也不能充作独立检验或正式金标准。',
    'source_projection_issue':'pilot01省略28无文本结构节点、71引用悬空；新canonical修复另行版本化；不改变首判材料。',
    'pending':['复核canonical余下13处字面定位','补材来源映射审核','新包A/B分别重判','三部门开发覆盖补充','冻结与真实独立执行'],
}
(ROOT/'03-manual/manual-v1.1-change-log.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'manual':str(target),'sha256':sha(target),'rule_decisions':len(changes['decisions'])},ensure_ascii=False))
