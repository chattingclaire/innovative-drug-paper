"""保存本AI复审者已实际阅读后的语义判断；不改输入或生产标签。"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE = ROOT / 'outputs/ai-audit800-20261010'
OUT = Path(__file__).parent
MAT = BASE / 'source-A/coder-A/materials'
SRC = BASE / 'source-A/shared-source/source-files'
MAN = BASE / 'source-A/coder-A/manual.txt'
RULE = ROOT / 'outputs/goal-calibration-20261010/06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl'
AI = {r['source_id']: r for r in map(json.loads, (BASE / 'AI原始判读-800条.jsonl').open())}
RULES = {r['id']: r for r in map(json.loads, RULE.open())}
DIS = [r for r in csv.DictReader((BASE / '与规则法分歧清单.csv').open(encoding='utf-8-sig')) if r['维度'] == 'I'][:22]
DATASHA = '09d813b3014db4137d2bceab8bc280c396a5916fafa7bb4c216c5798ae824d06'
TRIAL24 = 'ab19a319be3fae7b59a47401225441046720ea363ec2b273618f8f8868f81332'
TRIAL25 = 'ba7393a33c8061d4b5ff4ce0cf9e59c4e12cd81579da431bbc127db0dcad175c'
REG20 = 'd959108cdaaa3b46c8334c217619a42f14c4d83f17af0934502a08c5d62864be'
PROGRAM20 = '980acf76a2fb9b9537e89e6c223462549e984b39e6b1d9a54443e2dadce37036'

# review_value='未定'表示材料已有而操作边界仍需统一，绝不把不确定记作0。
C = {
 'A-000018': ('未定', ['I3', 'I3技术指导边界'], ['CTX-5ad3490febf57a533ee5'],
  '本句确实面向抗肿瘤创新药研发中指南未覆盖的安全评价情况鼓励与技术审评机构沟通，不能按安全内容或指南位置一律排除。但原文未明定服务、反馈内容或办理路径；“鼓励密切沟通”是否已构成可使用的专门技术机会，和一般沟通倡议的界线在现手册仍可有两种一致性解释。AI直接称其“提供”机会超出明文强度，规则直接以形式排除也未解释这一实质目的。需统一I3机会门槛，暂不硬判任一方。'),
 'A-000019': ('未定', ['I2', '必要语境的有限补全'], ['CTX-1338b912f2bd185cc4e5'],
  '当前有装置结构、推注速度、剂量规格等具体改变，并以“基于数据分析结果”承接自动注射装置便利性反馈；完整同段也明示视力、握力、记忆负担、注射时长及疼痛问题。支持I2的读法是反馈驱动改设计直接针对这些已述障碍；严格读法是本句仅适配不同场景的一般需求，未指明某项改变究竟改善哪一障碍，不能复制同段另句已独立成立的改良关系。现手册未明确这类反馈承接能否补足具体改变—障碍对应，保留边界待核。'),
 'A-000076': (1, ['I4', '具名安排撤回及同版有限补全'], [],
  '当前是终止同一数据保护权益的一般规范，而非仅报告某药“已获保护”的身份。核同版第三、五、六条及附表：该安排确实以创新/改良分类决定6年/4年保护，并排除他人依赖受保护数据获准。当前撤回同一实质权益可补其明确分类分支，I成立；不把批准文件被撤销解释成创新技术失败，也不把同一办法仿制药分支统称创新。AI标签有根据，但更稳妥留痕为创新/改良待遇制度的限制/撤回，而非把知识产权存在本身当研发支持。'),
 'A-000106': (1, ['I4', '成员与共同父谓词'], ['CTX-e851a9383ee2e4b32dcc'],
  '当前改良型新药成员承接第五十三条指定检验机构的共同谓词。完整条款随后将其他药品交由所在地省级机构，明确改良类别决定注册检验机构这一监管权利义务。这里不从“改良”身份泛称赋I，而是其法定分类的实际制度使用；保留中药除外，不把该安排声称为研发优惠。'),
 'A-000122': (1, ['I3', '同版同一安排有限补全'], [],
  '本句直接向经确认试点项目实施30工作日临床试验审批，属于实质办理便利。同版2024工作方案二（二）限定为1类创新药临床试验并明确排除细胞/基因治疗及疫苗，故对象与当前同一试点支持直接相连。不是从题名借I，也不借2025新版本倒灌。'),
 'A-000123': (1, ['I3', '具名支持计划实施与撤回'], ['CTX-73b7b312e5c00cbed344'],
  '当前决定维持或退出同一“关爱计划-延伸”资格，是支持机会是否持续的规范，不是名单状态。完整当前段明确研发期跟踪随访/密切沟通；同版计划明确以较强创新性及早期临床研发为申请条件，核心机制为与药审中心讨论开发计划并在整个开发中沟通。当前资格去留因此直接限制或维持这项可用研发服务，I3成立。未把安全事件等退出原因本身解释为创新属性。'),
 'A-000165': ('未定', ['I2', 'I3一般设计建议排除'], ['CTX-fa81d6c1b188043f6944'],
  '同段明确复杂给药时培训不足以保证老年患者正确操作，当前将照护者辅助纳入药物设计作为自我给药补充，有障碍—拟用方式的关系，不能说完全没有障碍。但具体改变是照护者辅助方式，制剂只是“进一步优化”，尚未指定产品/治疗属性怎样改变。是否把这种用药协助设计计入I2的药物产品/治疗属性改良，需统一界线；不能因指南面向创新药改称I3。保留未定而非擅自收窄或放宽I2。'),
 'A-000166': (1, ['I3'], ['CTX-7c68e08d1c1aab7a7854'],
  '当前明确开发适配创新药研发需求的医保数据产品，并支持企业/科研院所/医疗机构决定研发方向和管线。对象、数据资源安排、研发用途三项俱全；未来/探索语气不取消已设的支持议题。规则0遗漏当前自足的资源—研发关系，不需要从章标题推导。'),
 'A-000167': (1, ['I4', '同版保护机制实际实施'], ['CTX-7a4820192833280e2a7f'],
  '当前在数据保护申请审查过渡期实际不受理/不批准依赖受保护数据的申请，承接同段符合实施办法保护条件的申请，不是资料流转或保护名称。核同版第三、五、六条及附表：创新及改良分类实际决定专属保护待遇，其中创新/改良分支的许可屏障在当前得到实施。可有限补该分支的待遇关系，不从“促进创新”的宗旨或孤立数据权利赋I，也不声称所有受保护药品均创新。'),
 'A-000181': (1, ['I4', 'I3', '完整实质总领与并列范围'], ['CTX-273567229abc47f9a0c1','CTX-24f563b8cb62b74ccac2','CTX-78ca9441169499e115a8'],
  '本句将中药/化学药/生物制品1类创新资格作为纳入30日审评通道的必备条件，并有独立的条件—机会关系，非纯结构引导。完整三选一成员和同版第一条30日审评机制均核明。创新分类被实际用于准入；并列成员不被一概推为技术创新事实，不要求这句逐项重写分类定义。'),
 'A-000186': (0, ['I2', '公共指南一般设计建议排除'], ['CTX-f9c383f79876afc8f839','CTX-5468732f7401a3149e3a'],
  '完整语境列吞咽、认知及操作能力等患者特征，当前泛称评估“突出问题”、适当调整药物特征和延伸产品线以满足需求。它未指定具体特征如何改变，也未把某个明确既有局限与该改变相连。“能力”不能补写成已有吞咽/认知障碍，笼统产品调整不能直接升格实质改良。当前亦未设置研发可用资源、反馈或办理机会。AI把这一一般设计建议具体化为已指认障碍—实质改良，超过现I2门槛。'),
 'A-000189': (1, ['I2', 'I4比较条件'], ['CTX-874bd2f312d2eabef58f','CTX-ec9e4e35cbe15d36ab6d'],
  '当前不仅说新剂型，而同时规定现有所有上市剂型均不适用于儿童、新剂型须适宜儿童，并把该比较作为优先审评适用条件。明确既有使用局限与新剂型使用适宜性改善关系，I2成立；不需要推测具体剂型或已证治疗优效。保留两个条件及父条款，避免从“儿童新剂型”几个字泛判。'),
 'A-000202': (1, ['I3', '成员与共同父谓词'], ['CTX-25e0d15b3af7b2464e1c'],
  '当前创新疫苗分支承接“具有明显临床价值的药品可以申请适用优先审评审批程序”，实际开放创新对象的办理机会。疾病急需疫苗与创新疫苗是混合范围，创新分支足以计I一次；并不把所有急需疫苗等同创新。不仅是文件对象身份。'),
 'A-000212': (1, ['I3', '操作性标准援引及支持撤回'], [],
  '本句以是否满足优先审评条件决定终止实质审评待遇，属于一般规范的操作性标准援引。同版注册办法第68条范围完整含创新/改良新药和创新疫苗，第70条明确130日及优先核查等支持。当前实际撤回同一办理便利，对其中明确创新研发分支可补I3关系；不用下一版本，更不推断现实药品哪项失败或各条件均失败。'),
 'A-000227': (1, ['I1', 'I4实质创新价值选择条件'], ['CTX-69b489948e6bd22a139f'],
  '当前实际开展商保创新药目录调整，并以“创新程度高”与临床价值/获益作为主要纳入选择标准；不是仅制定文件的原因或目录名称。创新程度评价直接用于目录准入，I1/I4成立。此依据属于创新价值/资格的制度使用，不把目录推荐称为研发支持或药品已具优越性。'),
 'A-000229': (1, ['I1创新联系的临床优势', 'I4确切改良分类及保护范围'], ['CTX-bda6b629cee3a7283741'],
  '“本条款”在同版第六条明确承接改良型药品4年数据保护。当前要求新临床试验数据证明其较已知活性成分药品/上市生物制品的明显临床优势，并排除BA/BE/疫苗免疫原性。确切改良分类、比较内容与保护范围直接相连，属于有创新/改良联系的价值及资格信息；不是凭新数据或一般疗效优势推创新。保留排除项，且不把未被保护数据说成无效。'),
 'A-000242': ('未定', ['I1创新联系的临床优势', 'I4非每一程序条件均为创新条件'], ['CTX-a089dc6ed0f6834d3168','CTX-81d79f38a208aae58b73','CTX-a93cd3b83f46b25324f1'],
  '当前明确比较联合治疗相对现有治疗的疗效，E依据明确。完整父条款把它列为突破性治疗“明显临床优势”的一支，适用范围为创新药或改良型新药等。可按I1读作有创新联系的临床优势；但也可认为创新/改良仅是上位对象身份，该成员本身只核疗效条件，不涉及技术新颖/改良资格，现I4特别排除把每一程序子项都当创新条件。AI将其直接称I4创新/改良资格过于确定；规则0也需解释为何该明确关联不足。需统一I1创新联系与一般疗效条件的界线，保留未定。'),
 'A-000255': (1, ['I3', '同版具名支持申请机会'], ['CTX-6d114aa01dc5932e4f4c'],
  '当前准许符合要求的申请人自愿申报同一试点，是支持机会的开放，另有组长机构条件。核2024同版方案二（二）创新1类对象及三（四）30工作日审评机制，形成对象—申报机会—研发办理便利关系。不是把递交材料或组长单位身份本身算I，不以2025通道标准替代2024试点。'),
 'A-000285': (1, ['I3', '支持限制与同版有限补全'], ['CTX-56b38e8d30592e2075d5'],
  '当前在疑难复杂情况下把同一30日通道改为60日，是明确加速便利的条件例外/限制，并同时规定通知。核2025同版第一、三条：该通道对1类创新药临床研发提供30工作日审批。I依据是限制当前创新研发办理安排，不能只把整句视为通知形式，也不称60日仍有30日加速。'),
 'A-000297': (1, ['I3', '同版同阶段的滚动资料反馈机会'], ['CTX-b20cd4bf470f790e01d2','CTX-75cb2f2c8d12a6c7eb8d','CTX-9323a1e6a58c526dc910'],
  '当前实际允许与药审中心协商审评过程中继续提交资料的计划，完整同段明确可据双方一致计划滚动提交，属于研究资料计划反馈及审评办理便利。同版规范明确儿童专用/罕见病/突破性程序创新药适用范围及上市前研发阶段，与当前早期介入滚动计划直接对应。不是电话视频形式，也非普通申请人履行证据义务。规则以沟通形式排除遗漏实质安排。'),
 'A-000298': (1, ['I2'], ['CTX-6acc6f9037c3085a6ef3'],
  '当前明确调整药液浓度、黏度、装量和推注速度来避免注射过长不适，并用针头规格/自动隐藏设计降低疼痛、误刺和恐针。这是已明示操作/使用障碍—具体产品设计—改善使用表现的关系，符合手册拟用设计操作化；不需证明已实现创新或优效。依据是当前I2，不是指南全篇创新题名的I3。'),
 'A-000305': (1, ['I3', '同版同一审评机制有限补全'], ['CTX-177ec9e741acdea0e7f7'],
  '当前向优先审评程序实施130日审评时限，并有罕见病进口品种70日例外；同版附件3完整范围含防治重大传染病/罕见病的创新及改良新药和创新疫苗，技术审评条明确优先配置资源。当前基础分支实际施用该机制，可有限补明确创新研发对象的办理便利，I3成立；70日例外对象不因此全部被称创新，亦不从纯名单身份展开。'),
}

POS = {
 'A-000405': (['I1','I4'], ['CTX-3b3331e1e34f0a94ea77','CTX-3eecfda0e07bd082b2ee'], '当前完整或分支直接定义FIC新机制/靶点；父谓词明确“具有较强创新性”的申报资格。创新属性与资格内容自足，I=1；不把每个或分支均解释成机制新颖。'),
 'A-000430': (['I1概括性评价','共同门槛概括性评价要求'], ['CTX-d7eb96813ab88ea5d80f'], '当前以药品临床综合评价为对象，要求围绕包括创新性在内的维度开展数据整合与综合研判，属于明确药品创新价值评价；不是只有标题或字段。'),
 'A-000480': (['I1概括性评价','过去时与背景位置不单独排除'], ['CTX-d31b67eff924d7d39a83'], '虽在主要内容介绍中采用“提出了”，但当前独立陈述从创新性等维度开展药品临床综合评价的管理要求，含明确药品对象和实质评价内容。依过去时/背景统一规则I=1，不凭文体位置清零。'),
 'A-000543': (['I3','过去时期具名安排的实施'], ['CTX-1e951085464dcbc4a4fb'], '当前历史叙述同时明确创新药研发对象、2024已组织开展的同一试点、加速临床试验申请审评行动，三个I3证据项俱全。背景位置及试点现已完成不取消曾实施的支持议题；不声称今天仍能申请。'),
 'A-000685': (['I1概括性创新信息要求','共同门槛资料内容与形式核验'], ['CTX-8591a75ed92a7ee3767a'], '当前申报内容明确包括药品创新性信息，并要求摘要与申报材料一致，属于创新实质信息提供/核验要求。不是空字段格式或递交流转，也不证明申报药品创新。'),
}

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def context(d, bid, cid):
    c = next(c for c in d['source_record']['contexts'] if c.get('context_id') == cid)
    return {'quote': c['text'], 'file': str(MAT / (bid+'.json')), 'json_pointer': f'/source_record/contexts/{d["source_record"]["contexts"].index(c)}', 'resource_id': cid, 'original_source_ref': c.get('source_ref'), 'use': '解释当前明确承接的对象、比较或机制；不新增记录'}

def text_lines(sha, lo, hi, use):
    p = SRC / (sha+'.txt'); ls=p.read_text().splitlines()
    return {'quote':'\n'.join(ls[lo-1:hi]),'file':str(p),'line_range_1based_inclusive':[lo,hi],'source_sha256':sha,'use':use}

def match_lines(sha, texts, use):
    p=SRC/(sha+'.txt'); ls=p.read_text().splitlines(); indexes=[i for i,l in enumerate(ls) if any(t in l for t in texts)]
    assert indexes, (sha,texts)
    return [text_lines(sha,i+1,i+1,use) for i in indexes]

def data_pars(ix, use):
    p=SRC/(DATASHA+'.json'); j=json.loads(p.read_text())
    return [{'quote':j['normative_paragraphs'][i],'file':str(p),'json_pointer':f'/normative_paragraphs/{i}','source_sha256':DATASHA,'use':use} for i in ix]

def external(bid, d):
    if bid in ['A-000076','A-000167']:
        return data_pars([3,4,8,13], '同版数据保护定义、实质许可屏障及创新/改良分类—待遇分支')
    if bid == 'A-000229': return data_pars([13,14,15,16], '核本条款确指的第六条改良药保护完整范围及排除')
    if bid == 'A-000106': return [text_lines(REG20,173,180,'核指定机构与其他药品机构差异；分类—监管义务')]
    if bid in ['A-000122','A-000255']:
        return match_lines(TRIAL24,['试点项目范围为1类创新药','经确认的试点项目，药审中心'], '仅补2024同一试点的对象及30日机制')
    if bid == 'A-000123':
        rs=d['source_full_text_resources'][0]; ps=rs['paragraphs']
        return [{'quote':p['text'],'file':str(MAT/(bid+'.json')),'json_pointer':f'/source_full_text_resources/0/paragraphs/{ps.index(p)}','resource_id':p['source_paragraph_id'],'physical_pages':p['physical_pages'],'source_sha256':rs['source_pdf_sha256'],'use':'核同版关爱延伸创新对象和贯穿开发的实际服务'} for p in ps if p['source_paragraph_id'] in ['CARE-P007','CARE-P008','CARE-P024','CARE-P025']]
    if bid in ['A-000181','A-000285']:
        return match_lines(TRIAL25,['一、为进一步支持','三、纳入30日通道'], '核2025同一30日通道对象与办理机制；不借2024条件')
    if bid == 'A-000212': return [text_lines(REG20,225,242,'同版注册办法第68—71条完整范围、支持及终止关系')]
    if bid == 'A-000305': return [text_lines(PROGRAM20,155,161,'同版附件3完整六项适用范围；混合分支逐支确认'),text_lines(PROGRAM20,184,185,'同一纳入后技术审评与优先资源机制')]
    return []

manual_sha=digest(MAN)
assert manual_sha == '5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
used_bids = [r['A盲号'] for r in DIS]
joint = [r for r in AI.values() if r['judgments']['I']['value']==1 and RULES[r['source_id']]['labels']['I']==1]
assert len(joint)==5 and {r['blind_id'] for r in joint} == set(POS)
results=[]
for n,bid in enumerate(used_bids + [r['blind_id'] for r in joint],1):
    d=json.loads((MAT/(bid+'.json')).read_text()); s=d['source_record']; sid=s['id']; a=AI[sid]; rule=RULES[sid]
    if bid in C:
        val, clauses, cids, reason=C[bid]; assessment='规则遗漏依据' if val==1 else 'AI不符合现手册' if val==0 else '手册边界待核'; group='创新分歧前22项'
    else:
        val=1; clauses,cids,reason=POS[bid]; assessment='共同阳性复核成立'; group='双方I=1的5条共同阳性检查'
    evidence=[context(d,bid,cid) for cid in cids] + external(bid,d)
    obj={
     'blind_id':bid,'source_id':sid,'dimension':'I','ai':a['judgments']['I']['value'],'rule':rule['labels']['I'],
     'review_value':val,'assessment':assessment,'check_group':group,'selection_order':n,
     'reviewer':'AI-Codex-innovation-first22-sol','is_human_review':False,
     'review_identity_note':'AI独立核源语义复审；已见原AI及规则值，非真人、非新盲法效度结果；blind_id只是原材料编号。',
     'current_original':s['text'],'current_location':{'file':str(MAT/(bid+'.json')),'json_pointer':'/source_record/text','source_ref':s['source_ref']},
     'actual_context_evidence':evidence,'manual_clauses':clauses,'manual_file':str(MAN),'manual_sha256':manual_sha,
     'reason':reason,'needs_human_review':val=='未定','material_missing':False,
     'ai_original_judgment':a['judgments']['I'],'rule_original_decision':rule['decisions']['I'],
     'read_material_sha256':digest(MAT/(bid+'.json')),
    }
    results.append(obj)

(OUT/'reviews.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results))
(OUT/'reviews.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
counts=Counter(r['assessment'] for r in results[:22])
manifest={
 'reviewer':'AI-Codex-innovation-first22-sol','is_human_review':False,'scope':'I分歧清单按原CSV顺序前22项，另含双方I=1全部5条',
 'manual_sha256':manual_sha,'input_csv_sha256':digest(BASE/'与规则法分歧清单.csv'),'ai_input_sha256':digest(BASE/'AI原始判读-800条.jsonl'),'rule_input_sha256':digest(RULE),
 'disagreement_count':22,'joint_positive_count':5,'assessment_counts_disagreements_only':dict(counts),
 'undetermined_blind_ids':[r['blind_id'] for r in results if r['review_value']=='未定'],
 'zero_blind_ids':[r['blind_id'] for r in results if r['review_value']==0],
 'actual_read_statement':'本复审实际读完全部27项当前完整命题与所列必要上下文；核2024试点、2025通道、2020注册办法及附件3、2026数据保护同版完整有关条款，直接查看数据保护附表1原图。引用只使用已读关系片段。未对27项以外作推断。',
 'original_table_image_actually_viewed':str(SRC/'fc1c182e94170d6fec92fd653f299a72bdbd2da2bb44d8f3ef54a0cc092b1d3a.jpg'),
 'limitations':'这是后续AI审查，不能替代真人信度/效度或据此直接改生产值；未按部门占比、目标得分修改定义。四项未定是手册操作边界而非缺材。',
 'writes_restricted_to':str(OUT),'source_or_production_files_modified':False,
}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
md=[
 '# 创新维度前22项分歧及共同阳性：AI语义复审',
 '',
 '身份：AI-Codex，非真人结果。已经看到双方原标签，因此本次是核源后的独立语义复审，不是盲法首判。未改原始、生产或抽检结果。',
 '',
 '按现冻结手册（SHA256 5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b），22项分歧中：17项有规则遗漏依据；1项AI超出现手册；4项手册边界待核。5条共同阳性均复核为1。没有因规则输出0而先验认定0正确。',
 '',
 '明确遗漏主要是已核同版的创新研发数据资源、30日试点/通道、优先审评办理、滚动提交反馈，以及改良法定类别的指定检验义务。明确AI放宽是A-000186：患者特征与笼统产品调整未建立具体改变—已知局限关系。A-000018（鼓励沟通是否构成可用技术服务）、A-000019（便利性反馈与具体障碍的承接）、A-000165（照护者辅助是否属于药物/治疗属性改良）、A-000242（突破性疗效条件与I1创新联系）保留未定，建议统一边界后再裁定。',
 '',
 '共同阳性包括FIC资格、两条药品创新性综合评价要求、2024实际创新临床试验加速试点、药品创新性申报信息要求。背景/过去时不单独排除；信息内容要求与形式流转分开。',
 '',
 '逐条完整原文、实际使用的上下文引文/位置、手册路径、理由及需真人复核标志在reviews.json和reviews.jsonl；输入哈希与范围在manifest.json。所有判断仅用于检查，不自动变更生产标签；没有新建真人结果或重跑CLI。',
 '',
 '|盲号|原记录号|AI|规则|本次AI复审|分类|',
 '|---|---|---:|---:|---|---|',
]
for r in results:md.append(f'|{r["blind_id"]}|{r["source_id"]}|{r["ai"]}|{r["rule"]}|{r["review_value"]}|{r["assessment"]}|')
(OUT/'report.md').write_text('\n'.join(md)+'\n')
assert len(results)==27 and len({r['source_id'] for r in results})==27
print(json.dumps(manifest,ensure_ascii=False,indent=2))
