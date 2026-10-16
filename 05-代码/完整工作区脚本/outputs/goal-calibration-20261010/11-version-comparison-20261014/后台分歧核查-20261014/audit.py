import json, pathlib, hashlib, re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent
BASE = ROOT / '11-version-comparison-20261014'
def read(p):
    return json.loads(pathlib.Path(p).read_text())
def binding(p):
    p = pathlib.Path(p)
    return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2))

llm_path = ROOT/'07-statistics/original-whole-batch-native-full4481-cap13-root/selected-records.jsonl'
manual_path = ROOT/'03-manual/full4481-common-release-20261010-root/manual.txt'
rows = [json.loads(x) for x in llm_path.read_text().splitlines()]
by_id = {r['id']:r for r in rows}
packets = {r['id']: read(r['packet']['path']) for r in rows}
diffs = [r for r in read(BASE/'旧版现有证据核查/逐项分歧.json') if r['method']=='LLM']
counts = [r for r in read(BASE/'旧版现有证据核查/核查结果.json')['full_descriptive_counts'] if r['method']=='LLM']

# This is an openly AI-authored diagnostic review, never a human adjudication.
# Tuple: recommendation, proposed value (None = unresolved), manual basis, rationale.
decisions = {
'03938': ('支持人工',0,'§一共同实质门槛；§三排除数据/网络安全和纯伦理手续', '当前对象是数据系统和流程，既有语境为资料可靠性、隐私和个人信息保护；药物临床试验身份不能单独证明这里的风险是药物损害。现有原文不足以支持S=1，应保留人工0。'),
'02375': ('规则边界待协作',None,'§三质量内容须明确关联药物损害、用药风险或控制；§二成员不继承总领全部标签', '近效期先出、避免库存过期是一项具体措施，但当前句未明示患者使用过期药的损害关系；人工依据同段药品安全管理与全流程监测将其认作安全控制，机器依据质量—风险边界排除。材料已齐，不是缺原文；需研究者确认原手册中“明确联系”是否允许这一层关系。不能为了分数选1或0。'),
'03064': ('支持人工',0,'§一一般方法步骤不继承整个研究目的；§二固定记录和语境计数', '当前仅要求先明确临床问题，没有确指必须覆盖后面所有例子的内容要求。紧接的安全性例子可以解释一个可能选题，不能使一般选题方法变成安全证据要求。'),
'03291': ('支持人工',1,'§一当前实际安排直接对应某维内容的措施；§三用药服务中的风险控制', '本记录在同一完整句中设置药品进销存全流程记录和管理制度，明确直接用于确保用药安全，不是只解释为何制定文件的宗旨句。可按概括的用药安全控制记录S，不声称已降低损害。'),
'03840': ('支持人工',0,'§一一般方法步骤不得继承整个研究目的；§五实质经济内容门槛', '当前陈述已开展参照药预沟通；同段虽说明为后续药物经济学研究打基础，但没有本记录实际经济比较、价格费用核验或经济证据要求。研发服务可以在I单独成立，不能自动生成Ec。'),
'03289': ('支持人工',0,'§五当前制定/改变/比较/评价支付内容或明确核验；§一形式与实质区分', '“另行制定”是规则事项的保留，当前没有规定支付标准形成、调整的具体条件或机制。支持0的理由是没有本条实质内容，而非将一切未来时态排除。'),
'01416': ('支持人工',1,'§二设立与撤回同门槛；§六具名支持计划实施与撤回', '当前明确数据保护终止后允许其他申请人依赖该数据注册，正是同一创新药数据排他权益的终止后果；同版第三、第五条已核明保护安排和创新药分支。不把后续申请人当作创新药，也不妨碍记录原创新保护权益的撤回。'),
'01744': ('支持机器，供研究者复核',1,'§二同版实际机制有限补全；§六纳入若实质授予支持机会可补足', '原包同段明确“5个工作日内未收到项目确认书的临床试验项目不纳入试点”；同版又明确“经确认的试点项目”可适用30个工作日审评。当前发送确认书具有取得试点待遇的操作效力，不仅是无后果的普通通知。支持I=1的机器侧建议须单列，不能改写既有人工答案或回填检验分数。'),
'02503': ('支持人工',0,'§二子项不继承栏目全部内容；§六I3须具体可使用的安排', '当前建设三方互通和公共数据管理，没有直接提供创新研发可使用的数据产品或服务。后句才明确探索提供医保数据服务，不能把后句独立安排倒借给当前；标题能限定对象但不能代替当前支持措施。'),
'04197': ('支持人工',1,'§六I3：专门审评团队、项目反馈、加快通道可成立；不按语法主语判断', '同版范围为明确创新药研发，专门机制规定单独序列和审评时限；当前要求该审评团队解决技术问题以兑现该时限，属于直接实施已核明的专门审评资源。不能仅因是内部协同而要求一定出现面向申请人的服务措辞。'),
'02535': ('支持人工',0,'§七具体F须患者获取/持续治疗/可负担对象和可指认公平联系；不从基金管理推定', '特例单议及按项目付费/调整支付标准实质属于Ec；“不适合按病种标准支付”说明基金与医疗机构的支付适配，原包没有进一步说明患者获取受限、支付能力或保障缺口。机器从支付适配推为患者按需公平保障，多走了一步。'),
'00132': ('支持人工',1,'§七上游按需机会口径；§二同版同安排直接机制的有限补全', '同段限定临床急需、境外已上市境内未上市罕见病药；前段一般优先程序要求审评时限届满25日前完成核查，当前特殊分支允许上市审批后核查，直接提供按缺口条件适用的核查后置便利。不是把前句检验时限移植给本句，而是本句自身设定另一项便利。'),
'00084': ('支持人工',0,'§二一般指引不无限递归；§十不存在关键确指缺失时不无限请求材料', '当前泛指整部技术指南，未确指条款、实质条件或以其决定待遇后果；应按一般技术指引处理，五维0。指南历史版本未唯一核明是真实来源状态，但当前无须展开整部指南，不能因此五维全部待定。'),
}
reviews = []
for d in diffs:
    k = d['id'][-5:]
    rec, value, basis, rationale = decisions[k]
    packet = packets[d['id']]
    reviews.append({
        'id':d['id'], 'A_id':d['A_id'], 'dimension':d['dimension'],
        'original_machine_value':d['machine_value'], 'unchanged_human_value':d['reference_value'],
        'recommendation':rec, 'machine_review_proposed_value':value,
        'manual_basis':basis, 'review_rationale':rationale,
        'current_text':packet['source_bundle']['source_record']['text'],
        'source_record_with_context':packet['source_bundle']['source_record'],
        'original_machine_reason':d['machine_decision']['reason'],
        'human_reason':d['reference_judgment']['reason'],
        'packet_binding':binding(by_id[d['id']]['packet']['path']),
        'review_identity':'AI机器侧事后核查建议，非真人裁定；未用于回填验证得分',
    })
save('17项分歧与待定核查.json',reviews)

negative_scan=[];positive_scan=[];exact_scan=[]
for r in rows:
    sr=packets[r['id']]['source_bundle']['source_record'];t=sr['text']
    near=t+'\n'+'\n'.join(c.get('text','') for c in sr.get('contexts',[]) if c.get('kind')=='paragraph')
    item={'id':r['id'],'current_text':t,'F':r['labels']['F'],'original_reason':r['dimensions']['F']['reason'],'packet_path':r['packet']['path']}
    if r['labels']['F']==0 and re.search('临床急需|短缺|境内未上市|尚无有效|无有效治疗',near) and re.search('可以|应当|支持|优先|加快|允许|减免|豁免|后|前|按需',t):negative_scan.append(item)
    if r['labels']['F']==1 and re.search('特例|病种|机构|支付标准',t):positive_scan.append(item)
    if ('核查' in t and re.search('上市审批后|批准上市后|审评时限|后置|免|豁免',t)) or '特例单议' in t:exact_scan.append(item)
save('公平性同类条款定向检索.json',{'coverage':'全部4481条已保存文本上执行有限检索；是定向诊断而非全库人工复核或错误率估计','query_negative':'F=0；当前及同段包含临床急需/短缺/境内未上市/尚无有效/无有效治疗；当前含措施/时序词','query_positive':'F=1；当前包含特例/病种/机构/支付标准','negative_candidates':negative_scan,'positive_candidates':positive_scan,'inspection_or_case_payment_candidates':exact_scan,'additional_suspected_error':{'id':'RECODE25-02534','machine_F':1,'review_suggested_F':0,'rationale':'与02535同段、同一机构支付适配机制；没有额外患者获取或负担关系。机器侧建议，未经真人新裁定。'},'finding':'漏判定向候选14条中除已知00132，未在所读当前和同段材料识别出另一项明确同类漏判；不能推为样本外没有漏判。另发现02534与02535同类可能误判，说明至少该支付适配边界存在局部重复过度赋F。'})

null_records=[]
for r in rows:
    nd=[d for d,v in r['labels'].items() if v is None]
    if nd:
        null_records.append({'id':r['id'],'null_dimensions':nd,'current_text':packets[r['id']]['source_bundle']['source_record']['text'],'reasons':{d:r['dimensions'][d]['reason'] for d in nd},'packet_path':r['packet']['path']})
bounds=[]
for r in counts:
    pos=r['positive_counts'];nul=r['null_counts'];leader=max(pos,key=pos.get)
    possible_ties=[]
    dims=list(pos)
    for i,a in enumerate(dims):
        for b in dims[i+1:]:
            if max(pos[a],pos[b])<=min(pos[a]+nul[a],pos[b]+nul[b]):possible_ties.append([a,b])
    bounds.append({'department':r['department'],'N':r['N'],'positive_counts':pos,'null_counts':nul,'range':{d:[pos[d],pos[d]+nul[d]] for d in dims},'leader':leader,'leader_guaranteed_under_any_null_assignment':pos[leader]>max(pos[d]+nul[d] for d in dims if d!=leader),'pairs_with_overlapping_count_ranges':possible_ties})
save('60项待定及排序范围.json',{'record_N':len(null_records),'dimension_slot_N':sum(len(r['null_dimensions']) for r in null_records),'records':null_records,'bounds':bounds,'interpretation':'仅给出60项NULL任意补0或1的确定性范围，不能反映其他已判0/1的误判。三个部门首位维度均不变，医保局S/E原为80/80并列，待定补判可改变二者次序。'})
save('核查绑定.json',{'date':'2026-10-14','source_bindings':[binding(llm_path),binding(manual_path),binding(BASE/'人工独立检验记录更正-20261014.json')],'source_label_changes':0,'model_batch_calls':0,'human_independent_validation':True,'scope':'17维判断、13记录；公平性定向诊断；60项待定计数范围','reviewer':'AI机器侧核查，不能代替真人裁定'})
print(json.dumps({'reviewed_slots':len(reviews),'negative_F_candidates':len(negative_scan),'positive_F_candidates':len(positive_scan),'null_records':len(null_records),'null_slots':sum(len(r['null_dimensions']) for r in null_records)},ensure_ascii=False))
