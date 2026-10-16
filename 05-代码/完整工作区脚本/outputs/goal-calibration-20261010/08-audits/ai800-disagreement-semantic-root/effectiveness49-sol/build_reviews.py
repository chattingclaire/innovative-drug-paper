#!/usr/bin/env python3
"""Serialize authored E49 semantic reviews and mechanically verify their bindings.

The judgments below were authored after reading the complete current units and
their finite same-version context. They are AI reviews, not human adjudications.
This script does not infer semantic labels from keywords or calculate accuracy.
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
AIROOT = ROOT.parent / 'ai-audit800-20261010'
MANUAL = ROOT / '03-manual/full4481-common-release-20261010-root/manual.txt'
RULE = ROOT / '06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl'
AI = AIROOT / 'AI原始判读-800条.jsonl'
CSV = AIROOT / '与规则法分歧清单.csv'
RAW = AIROOT / 'source-A/shared-source/source-files/d959108cdaaa3b46c8334c217619a42f14c4d83f17af0934502a08c5d62864be.txt'

# ordinal: (review value, actually used packaged context indices, authored reason)
AUTHORED = {
 1: (1, [], '当前要求上市后研究证明药品获益大于风险，并以不能证明决定审评不通过及注销。获益证据及其否定在当前命题中直接在场；不能证明不等于已经证明无效，亦不把证书有效期当E。'),
 2: (1, [0,3], '当前定义患者报告结局，明确包括症状和健康相关生活质量；同版范围将其置于抗肿瘤药物临床研发。由当前的健康结局内容记录E，不把治疗满意度或所有PRO资料处理一律当疗效。'),
 3: (1, [0], '当前把老年人的药物处置、敏感性差异与安全、有效且便利的用药特点的重要性相连，直接提出药物有效性的评价关注。不是仅借文件适老化宗旨或整体健康水平赋E。'),
 4: (1, [0], '当前分析不同人群/亚组的治疗获益和风险，借此确定更精准的目标人群，直接讨论药物治疗获益及证据用途。目标人群精准化本身不代替这个获益关系。'),
 5: (1, [0], '当前在药物开发所用的自然史研究中具体纳入不同阶段患者对治疗的反应，属于治疗效果相关信息。只按该反应内容纳入，不把疾病自然史的所有数据项目赋E。'),
 6: (1, [0], '当前明确富集策略并不意味着其他患者不能获益，并要求成功后继续探索其他人群。保留“并不意味着不能”的否定关系：是在讨论潜在药物获益范围，未宣称其他人群已有获益证据。'),
 7: (1, [0], '当前要求药品疗效、安全性优先采用RCT或指南推荐等较高等级证据；完整段落明确同类药疗效比较。属于药物效果证据要求，不是单凭RCT方法名称赋E。'),
 8: (1, [3,*range(6,16)], '当前以符合第九、十条作为目录调整范围的实质资格条件。完整同版条款含风险大于收益和不符合有效性条件等分支，构成操作性标准援引。其余行政、价格等分支不因此都成E，也未断言某药所有条件失败。'),
 9: (1, [], '当前规定审评发现不满足优先条件即终止该待遇、回到正常审评，属于标准—待遇后果规范。新增核读同包同版第六十八条的完整范围及其确指突破性/附条件批准分支的第五十九、六十三条：含无有效防治手段、比较临床优势及疗效数据要求，故E在被核验标准中在场。不把整体不满足改写为药品无效，也不展开一般另行公布分支。'),
10: (0, [0], '当前只规定已批准、通过一致性评价的化学药品目录集收载哪些身份信息及如何更新公开，没有本记录的效果比较、证据核验或有效性条件要求。“通过一致性评价”在此是收载对象的既有状态，不能据名称展开评价标准。'),
11: (1, [0], '当前说明商保创新药目录的主要准入对象须对患者获益有显著提升，药物/患者对象和健康获益提升直接相连。E依据是这个获益条件，不能只以高度创新或笼统临床价值赋E。'),
12: (1, [0], '当前对老年与一般成人相同观察指标的结果差异，要求说明快速起效或主观体验改善的临床意义并评估剂量调整；完整段落明确这些是客观/主观疗效指标。是疗效差异分析，条件句不证明差异实际存在。'),
13: (1, list(range(5,10)), '当前是经评审直接调出目录的实质条件总领，不是纯清单标题。读完整五个成员后，风险大于收益分支实质涉及治疗收益评价，故E=1；保留“有下列情况之一”，不把另四支或整个目录都视为疗效评价。'),
14: (1, list(range(5,25)), '当前要求符合确指的第二部分目录外条件。读完整该部分及其中直接援引的第七、八条后，第七条“临床必需、安全有效、价格合理”是适用资格的实质条件，故E=1。日期、适应症改变、目录身份及第八条排除对象不自动证明疗效，儿童等例外保持原范围。'),
15: (1, [*range(5,12),*range(21,31)], '当前直接要求第七、八条且满足所列情形之一方可申报；完整条件中的第七条要求药品安全有效，构成概括药物有效性要求。核读完整七个申报分支及第八条排除/例外，不由新通用名、适应症变更或已入其他目录推断效果。'),
16: (1, [0], '当前明确根据中期临床数据分析疗效、安全性；完整段落含达主要终点及终止无效/低效组等效果判断。是疗效证据分析，不能因中期分析是一种方法而删除已表达的E内容。'),
17: (1, [0], '当前列RCT在罕见病或危及生命且没有有效治疗手段疾病中的局限，明确有效治疗选项缺失。即使处于研究方法讨论，缺失的效果要求仍在场；一般小样本或急需本身不用于赋E。'),
18: (1, [], '当前将真实世界证据界定为关于药物使用及潜在获益—风险的临床证据，效果/患者获益对象明确。记录的是潜在获益证据议题，不认定所有真实世界数据已证实疗效。'),
19: (0, [0], '当前因抗肿瘤药物毒性担忧选取充分治疗后无标准治疗可选的末线患者，未明确“标准治疗”不可选是因无效，也未核验效果标准。完整段落后续另行推荐在已见治疗应答的瘤种开展FIH；不能把该独立推荐反向移入当前受试者选择命题。按现手册，一般未满足需要和治疗用途不足以成立E。'),
20: (1, [0], '当前收集患者对治疗风险及不确定性的接受程度，明确不确定的对象为“是否能从治疗中获益”。否定/不确定不是E排除理由；这里只记录治疗获益的不确定评价，不推断患者确能获益。'),
21: (1, [0], '当前把富集策略用于选择最可能从药物治疗获益的患者，完整段落核明研究药物这一对象。是获益概率/适用人群的药物效果判断，不以“富集”方法名称自动赋E。'),
22: (1, [0], '当前将建模模拟的具体应用与为老年患者提供更安全有效的药物治疗方案相连，提出治疗方案有效性内容。E来自该明确药物治疗效果关系，研发效率提升本身不是药物有效性。'),
23: (1, [*range(5,13),*range(23,33)], '当前对目录外申报直接设第七、八条条件；第七条明示安全有效，故为概括药物有效性资格要求。完整核读八个申报情形、日期/排除和第八条例外；不将附条件转常规、目录名称或创新身份自行转为疗效已达标。'),
24: (1, [0], '当前明确商保准入药须对患者获益有显著提升，属于临床获益条件。不是单凭高创新、高临床价值或商业保险定位推定E，也不把后续注册年限等技术条件一律视为效果内容。'),
25: (1, [*range(5,12),*range(22,32)], '当前直接要求第九、十条并满足调整情形；完整同版标准含风险大于收益及不符合有效性条件，且本方案调出分支也直接包含收益评估，故E=1。保留调出与支付调整各自分支，不把行政注销、价格或支付形式都写成疗效失败。'),
26: (1, [6,7], '当前实质要求提供相关说明及依据，完整两项要求含无有效防治手段或相对现有治疗的明显临床优势及其临床证据。不是仅“如下”结构引导；保留替代适用情形、比较对象及证据要求，不把临床优势已经成立作为结论。'),
27: (1, [0], '当前确指抗肿瘤药物研究中的患者报告结局评估终点，并要求开发、验证和讨论该终点。另用同一来源SHA、同版第26页PRO定义核明其症状/健康相关生活质量的效果对象，故属于效果终点验证要求；未因所有方法或治疗满意度都自动赋E。'),
28: (1, [0], '当前明确借工具使患者在无效或剂量不足的治疗上耗时最少，完整段落核明剂量—暴露—效应包含疗效。无效治疗是被限定的药物效果内容，不因这是剂量研究方法而排除E。'),
29: (1, [], '当前真实世界证据定义明确涉及药物潜在获益—风险的临床证据，符合效果/健康获益证据内容。“潜在”保留为未证实性质，不称已获益。'),
30: (1, [0], '当前风险管理措施须考虑适应症和不良反应严重程度，即药物获益—风险比；完整段落以疫苗/抗肿瘤药对不同毒性容忍为例核明治疗获益关系。E依据是获益比较，不是把控制措施“合理有效”误当药物疗效。'),
31: (1, [0], '当前要求终点选择匹配患者需求并证明药物满足需求；完整同段明确收集反映患者获益的终点，举疼痛较现有治疗改善等效果例。由确指终点的效果对象补足E，不把一切患者需求或试验目标都当疗效。'),
32: (1, [0], '当前否定非最优对照研究能体现真正患者需求和药物价值；同段直接承接已被替代、疗效/安全性不确切的对照药问题。当前是在限制比较试验能够证明的治疗价值，不是把已达试验目标断言为达到患者获益。'),
33: (0, [0], '当前说明细胞免疫治疗的增殖、分布及细胞因子释放等PK/PD特点，并分析其与AESI的相关性；完整同段对象是关注的不良事件/安全性。没有治疗效果、健康获益或对应效果终点。不能仅因出现PD及药物机制赋E，亦不否认该句可能涉及其他维。'),
34: (1, [*range(5,10),*range(17,27)], '当前以第七、八条及所列情形决定2021评审范围，第七条“安全有效”为实质资格要求。核读全部四个情形和第八条排除/例外后纳入概括有效性关注；不把注册日期、治疗用途和目录身份本身认定疗效。'),
35: (1, [0], '当前说明老年生理变化可能影响药物药代、药效和安全性，完整段落具体把器官生理病理变化与药物作用反应变化相连。是人群对药物作用反应变化的评价关注，符合E药效边界；“可能”不表示已证临床获益，整体健康宗旨不作依据。'),
36: (1, [0,3], '当前以临床试验没有预期获益作为同意主体安排的条件，同版范围核明为药物临床试验。治疗获益缺失作为实质伦理条件直接在场，故E=1；不由法定代理人形式本身赋E，也不将无预期获益推成药物已证明无效。'),
37: (1, list(range(7,17)), '当前要求所列优先范围满足相关条件，是实质条件总领。完整范围的儿童新品种分支含无有效治疗选项或比现有上市药品有明显治疗优势，故E=1；药品短缺、剂型适宜等其他分支不因此自动涉及疗效。'),
38: (1, [], '当前以综合临床价值、不良反应和药物经济性后的风险大于收益评价作为调出条件，明确治疗收益与风险比较。记录负面收益评价议题，不把临床价值一词直接等同疗效，也不宣称风险大于收益已经对所有药品成立。'),
39: (1, [0], '当前只有在观察研究结果一致且继续显现药品对患者有明显获益时，才可平行开展RCT。药品临床获益作为明确推进条件直接在场；保留“如果”“且”“可”，不把研究许可或条件句当既成疗效。'),
40: (1, [0], '当前特殊指标包括生活质量改善及死亡率等，完整段落明确其用于全面评估老年人药物有效性与安全性。由“这些指标”确指的疗效观察对象补足E，不把全部认知/合并症指标都宣称为已发生药物获益。'),
41: (1, [], '当前直接指出新治疗手段延长肿瘤患者生存期，并据此提出更高生存质量期望，已有具体生存/生命质量内容。虽在背景章节，仍具有实质效果命题；不依后句研发最高目标或笼统宗旨赋E。'),
42: (1, list(range(5,22)), '当前要求符合确指的2021目录外条件。读完整该部分及其中第七、八条后，第七条安全有效是准入资格的实际要求，故E=1。保留日期、四项情形及第八条儿童等例外，不由目录名称或治疗用途反推有效。'),
43: (0, [0,2], '当前泛列人群特征及药物PK/PD、剂型、途径供综合评估与决策，并未说明需要考虑何种人群药物作用反应变化或效果证据。同段落点为适老化适宜设计；前段提升整体健康是指导原则宗旨，不能移入当前补成疗效。仅药效学术语不足以成立E。'),
44: (1, [3], '当前申请药品有效性存在较大缺陷，直接评价药物效果/证据的不足；父谓词将此设为注册不予批准条件。缺陷否定不消除E，也不能改写为药品已确定完全无效。'),
45: (None, [0,2], '当前实际使用成人PK/PD资料建立PK-PD关系以支持儿童设计和用法用量，强于孤立术语，但未明示所建模的PD指标、效果估计或儿童作用反应变化。现手册允许对应药效证据，亦排除无效果联系的一般方法；这里跨年龄建模是否足以完成直接效果关系尚不能确定。前句另一类共患肿瘤的“有效性信号”不能倒借，留null供人工核清边界，不判无效或补0。'),
46: (1, list(range(5,17)), '当前明确优先申请须同时满足(一)(二)，可用完整两项及各范围补足实质资格。儿童新品种分支明确无有效治疗药物/手段或相对现有药物有明显治疗优势，E条件成立；保留同时满足及成员或条件，不以泛称临床价值或程序名称代替效果内容。'),
47: (1, [3,*range(6,16)], '当前以符合第九、十条进入目录调整范围，是实际援引条件而非既有状态。完整条款有风险大于收益、不符合有效性等分支，故E=1；目录内身份、价格过高及其他程序分支不一律继承E。'),
48: (1, [], '当前要求就附条件批准上市的条件及上市后研究内容沟通并确认后申请，不是只列沟通形式。新增核读同包同版第六十三条完整三支：无有效治疗且有疗效数据、公共卫生药的疗效数据、疫苗获益大于风险，补足此次被确认条件的效果内容。故为概括效果条件/信息要求，不称已经符合或所有上市后研究都涉及E。'),
49: (1, [*range(5,9),*range(15,25)], '当前以第七、八条及四项情形设置目录外申报资格，完整第七条安全有效是实质有效性要求。保留日期和第八条排除/儿童等例外；不因新通用名、适应症变更或被列诊疗方案就推成有疗效。'),
}

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def projection(p, ids, kind):
    rows = {}
    with p.open() as f:
        for line in f:
            x = json.loads(line)
            sid = x.get('source_id', x.get('id'))
            if sid not in ids:
                continue
            assert sid not in rows
            if kind == 'ai':
                rows[sid] = {'blind_id': x['blind_id'], 'value': x['judgments']['E']['value'], 'source_text_sha256': x['source_text_sha256']}
            else:
                rows[sid] = {'value': x['labels']['E'], 'decision': x['decisions']['E']}
    return rows

def context_quote(t, index, relation='用于解释当前命题的明确对象、指代或被要求的完整条件；不继承其他独立命题'):
    c = materials[t['ordinal']]['source_record']['contexts'][index]
    assert c.get('text')
    return {'text': c['text'], 'material_path': t['material_path'], 'context_id': c['context_id'], 'context_index': index, 'source_ref': c['source_ref'], 'relation_to_current': relation, 'consumption': 'actually_semantically_read_packaged_context_text'}

def raw_quote(start, end, relation):
    text = '\n'.join(raw_lines[start-1:end])
    return {'text': text, 'path': str(RAW), 'source_ref': {'source_resource_id': 'SOURCE-' + sha(RAW), 'sha256': sha(RAW), 'locator': {'lines': [start,end], 'unit': 'one_based_inclusive_UTF8_splitlines'}}, 'relation_to_current': relation, 'consumption': 'newly_read_finite_same_version_original_excerpt_not_whole_document'}

scope = json.loads((OUT / 'scope49.json').read_text())['targets']
assert len(scope) == 49 and set(AUTHORED) == set(range(1,50))
ids = {t['source_id'] for t in scope}
with CSV.open(encoding='utf-8-sig', newline='') as f:
    csvrows = [r for r in csv.DictReader(f) if r['维度'] == 'E']
assert len(csvrows) == 49 and {r['原记录号'] for r in csvrows} == ids
csvmap = {r['原记录号']: r for r in csvrows}
airows = projection(AI, ids, 'ai')
rulerows = projection(RULE, ids, 'rule')
assert set(airows) == set(rulerows) == ids
materials = {t['ordinal']: json.loads(Path(t['material_path']).read_text()) for t in scope}
raw_lines = RAW.read_text().splitlines()
reviews = []
readlog = []
validations = []
for t in scope:
    i, sid = t['ordinal'], t['source_id']
    m = materials[i]
    s = m['source_record']
    v, indices, reason = AUTHORED[i]
    c = csvmap[sid]
    assert s['id'] == sid and s['text'] == c['当前完整命题']
    assert airows[sid]['blind_id'] == t['blind_id'] == c['A盲号']
    assert airows[sid]['value'] == t['ai'] == int(c['本轮AI值'])
    assert rulerows[sid]['value'] == t['rule'] == int(c['规则法值'])
    textsha = hashlib.sha256(s['text'].encode()).hexdigest()
    assert textsha == airows[sid]['source_text_sha256']
    if v is None:
        assessment = '手册边界待核'
    elif v == 1 and t['rule'] == 0:
        assessment = '规则遗漏依据'
    elif v == 0 and t['rule'] == 1:
        assessment = '规则过度纳入'
    else:
        assessment = 'AI不符合现手册'
    quotes = [context_quote(t, k) for k in indices]
    if i == 9:
        quotes += [raw_quote(225,232,'当前终止优先待遇以优先条件为准；第六十八条给出完整同版对象范围，不由标题或一般临床价值赋E'), raw_quote(198,199,'第六十八条第四支明确指向突破性治疗资格；本条定义该同一安排的无有效手段/比较优势条件'), raw_quote(209,213,'第六十八条第五支要求符合附条件批准；本条完整三支核明该同一资格的效果证据条件')]
    if i == 48:
        quotes += [raw_quote(209,213,'当前要求沟通确认附条件批准条件；本条完整三支是被确认的同版条件内容'), raw_quote(214,216,'核明当前沟通条款及同条第二款的确认—申请/附带研究安排；不把证书有效期作为E')]
    if i == 27:
        donor = next(x for x in scope if x['ordinal'] == 2)
        q = context_quote(donor,0,'当前“患者报告结局评估终点”对象的同源同版定义；不同记录的效果判断不传递，只借确指PRO的定义')
        assert q['source_ref']['sha256'] == s['source_ref']['sha256']
        q['consumption'] = 'already_read_same_version_definition_now_used_for_this_explicit_endpoint'
        quotes.append(q)
    seen = {}
    for k, ctx in enumerate(s['contexts']):
        if not ctx.get('text'):
            continue
        h = hashlib.sha256(ctx['text'].encode()).hexdigest()
        if h not in seen:
            seen[h] = {'canonical_context_index':k, 'canonical_context_id':ctx['context_id'], 'text_sha256':h, 'equivalent_context_ids':[ctx['context_id']], 'semantic_read_status':'actual_full_context_text_read_in_this_review'}
        else:
            seen[h]['equivalent_context_ids'].append(ctx['context_id'])
    readlog.append({'ordinal':i,'blind_id':t['blind_id'],'source_id':sid,'material_path':t['material_path'],'current_text_status':'actual_full_current_unit_read','unique_supplied_context_texts_read':list(seen.values()),'deduplication':'Identical context text is consumed once; equivalent IDs are mechanically bound, not additional independent reading.','source_document_inventory_is_not_reading':True,'whole_original_document_semantically_read':False,'new_finite_original_excerpts_used':i in [9,48]})
    r = {'ordinal':i, 'blind_id':t['blind_id'], 'source_id':sid, 'dimension':'E','ai':t['ai'],'rule':t['rule'],'review_value':v,'assessment':assessment,'reason':reason,'current_text':s['text'],'current_quote':s['text'],'current_source_ref':s['source_ref'],'context_quotes':quotes,'needs_human_review':True,'human_review_note':'AI复审为逐条候选；未替代真人独立编码或裁定。' if v is not None else '此项门槛解释未定，须人工裁定后方可给二元值。','reviewer':'GPT-6.1 Sol / inherited ultra; AI semantic audit','review_role':'auxiliary_AI_disagreement_review_not_human_reference','current_text_sha256':textsha,'manual_binding':{'path':str(MANUAL),'sha256':sha(MANUAL),'used_rules':['§一同一实质门槛/概括性评价','§二否定、条件及有限确指语境','§四E定义、纳入、排除及药效边界']},'original_rule_E':rulerows[sid]['decision']}
    reviews.append(r)
    qc = []
    for q in quotes:
        if 'material_path' in q:
            mm = json.loads(Path(q['material_path']).read_text())
            cc = mm['source_record']['contexts'][q['context_index']]
            ok = cc['text'] == q['text'] and cc['context_id'] == q['context_id'] and cc['source_ref'] == q['source_ref']
        else:
            a,b = q['source_ref']['locator']['lines']
            ok = q['text'] == '\n'.join(raw_lines[a-1:b]) and sha(RAW) == q['source_ref']['sha256']
        assert ok
        qc.append({'source_ref':q['source_ref'],'exact_continuous_quote_match':ok,'quote_text_sha256':hashlib.sha256(q['text'].encode()).hexdigest()})
    validations.append({'ordinal':i,'blind_id':t['blind_id'],'source_id':sid,'csv_AI_rule_identity_and_E_values_match':True,'current_text_CSV_material_AI_SHA_match':True,'current_quote_is_entire_current_unit':True,'context_quote_matches':qc,'all_matches':True})

assert len(reviews) == len({(r['blind_id'],r['source_id'],r['dimension']) for r in reviews}) == 49
save('reviews.json',reviews)
with (OUT / 'reviews.jsonl').open('x',encoding='utf-8') as f:
    for r in reviews:
        f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
save('actual-read-and-use-log.json',{'scope':'49 full current units and each distinct nonblank supplied context text actually read; only listed finite original excerpts were additionally consumed','whole_original_documents_read':0,'newly_read_original_excerpt_file':str(RAW),'newly_read_original_excerpt_lines':[[191,223],[225,243]],'reading_scope_note':'Lines 191–208 include finite adjacent registration/breakthrough passages actually read, not all used as E grounds. Lines 209–223 and 225–243 were read completely. Resource indexes and original-path inventories only show availability. Original AI read_sources is not adopted as this reviewer consumption.','entries':readlog})
save('quote-match-validation.json',{'N':49,'coverage_exact':True,'all_current_text_and_label_bindings_match':True,'all_quotes_exact_continuous_matches':True,'context_quotes':sum(len(r['context_quotes']) for r in reviews),'notes':['Current full quotes keep original negation/condition/exception wording.','Packaged quotations are checked against the exact material object; supplementary original quotations against the sealed same-version TXT bytes.','Same-origin PRO definition is bounded by source SHA and page locator; no new PDF body was read.'], 'entries':validations})
inputs = [AI,CSV,MANUAL,RULE,RAW,AIROOT/'source-A/shared-source/delivery-source-assets-index.json',AIROOT/'source-A/coder-A/source-assets-index.json']+[Path(t['material_path']) for t in scope]
save('input-bindings.json',{'files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in inputs],'rule_semantic_scope':'Only the 49 target E first decisions were used; no formal full/partial LLM results were read.','originals_modified':False})
summary = {'N':49,'AI1_rule0':46,'AI0_rule1':3,'review_value_counts':{('null' if k is None else str(k)):v for k,v in Counter(r['review_value'] for r in reviews).items()},'assessment_counts':dict(Counter(r['assessment'] for r in reviews)),'null_items':[{'blind_id':r['blind_id'],'source_id':r['source_id'],'reason':r['reason']} for r in reviews if r['review_value'] is None],'AI1_not_confirmed':[{'blind_id':r['blind_id'],'source_id':r['source_id'],'review_value':r['review_value']} for r in reviews if r['ai']==1 and r['review_value'] != 1],'human_reference_created':False,'accuracy_computed':False,'formal_labels_modified':False,'previous_statistics_interfaces_modified':False,'status':'49_auxiliary_AI_semantic_reviews_complete_with_one_unresolved_boundary'}
save('summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
