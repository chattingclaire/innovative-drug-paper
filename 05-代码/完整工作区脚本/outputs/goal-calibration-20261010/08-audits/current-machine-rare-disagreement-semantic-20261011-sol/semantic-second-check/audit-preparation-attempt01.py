#!/usr/bin/env python3
"""Read only the exposed 40-review file and 19 packet paths declared inside it.

No classifier, prediction, reference, external asset, manual or unseen packet is read.
Semantic positions are diagnostic arguments, not replacement labels.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

G = Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
BASE = G / '08-audits/current-machine-rare-disagreement-semantic-20261011-sol'
OUT = BASE / 'semantic-second-check'
REVIEW = BASE / 'phase01-first40/semantic-reviews40.json'
SHORT = ['00009','00013','00014','00020','00028','00034','00039','00040','00041','00052','00068','00071','00089','00091','00093','00103','00105','00106','00114']
SELECTED = {'RECODE25-' + x for x in SHORT}
SOURCE_SHA = '980acf76a2fb9b9537e89e6c223462549e984b39e6b1d9a54443e2dadce37036'

def binding(p):
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

def read_allowed(p):
    p = Path(p)
    assert p == REVIEW or p in allowed_packets, str(p)
    return json.loads(p.read_text(encoding='utf-8'))

def pointer(obj, path):
    for k in path.strip('/').split('/'):
        k = k.replace('~1','/').replace('~0','~')
        obj = obj[int(k)] if isinstance(obj, list) else obj[k]
    return obj

def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

allowed_packets = set()
before = [binding(REVIEW)]
reviews = read_allowed(REVIEW)
assert len(reviews) == 40 and len({(x['id'],x['dimension']) for x in reviews}) == 40
assert all(x['machine_values'] == {'rules_v7':0,'native_original_whole_batch':1} for x in reviews)
selected_reviews = [x for x in reviews if x['id'] in SELECTED]
assert len(selected_reviews) == 28
for x in selected_reviews:
    p = Path(x['current_direct_material']['packet']['path'])
    assert p.parent == G / '06-coding/full4481-common-v15-production-preparation-sol/packets'
    assert p.name == x['id'] + '.json'
    allowed_packets.add(p)
assert len(allowed_packets) == 19
before += [binding(p) for p in sorted(allowed_packets)]
packets = {str(p):read_allowed(p) for p in sorted(allowed_packets)}
quote_checks = []
resource_checks = []
for x in selected_reviews:
    declared = x['current_direct_material']['packet']
    actual = next(b for b in before if b['path'] == declared['path'])
    assert actual == declared
    p = packets[declared['path']]
    assert p['output_id'] == x['id']
    assert p['source_bundle']['source_record']['source_ref']['sha256'] == SOURCE_SHA
    for n, e in enumerate([x['current_direct_material']] + x['native_material_evidence']):
        q = e['quote']
        if e.get('pointer'):
            t = pointer(p, e['pointer'])
            start = t.find(q)
            assert start >= 0, (x['id'],x['dimension'],e['pointer'])
            locations = [{'pointer':e['pointer'],'unicode_interval_half_open':[start,start+len(q)]}]
            provenance = 'exact quote at declared packet pointer'
        else:
            # Do not open the external asset. Only test its supplied quote in
            # independently hashed text already embedded in this selected packet.
            assert e['asset_sha256'] == SOURCE_SHA
            locations = []
            for j,r in enumerate(p['source_bundle']['source_full_text_resources']):
                start = r['text'].find(q)
                if start >= 0:
                    locations.append({'pointer':f'/source_bundle/source_full_text_resources/{j}/text','unicode_interval_half_open':[start,start+len(q)]})
            assert locations, (x['id'],x['dimension'],'external quote absent from embedded packet')
            provenance = 'external asset not opened; supplied quote matched exactly in selected packet embedded text'
        quote_checks.append({'id':x['id'],'dimension':x['dimension'],'review_evidence_index':n,'quote':q,'locations':locations,'check':provenance})
for path,p in packets.items():
    for j,r in enumerate(p['source_bundle']['source_full_text_resources']):
        raw = r['text'].encode('utf-8')
        assert r['source_sha256'] == SOURCE_SHA
        assert len(r['text']) == r['text_unicode_code_points']
        assert len(raw) == r['text_utf8_bytes']
        assert hashlib.sha256(raw).hexdigest() == r['text_utf8_sha256']
        resource_checks.append({'packet_path':path,'resource_index':j,'locator':r['locator'],'source_version_id':r['source_version_id'],'source_sha256':r['source_sha256'],'text_bytes':len(raw),'text_sha256':hashlib.sha256(raw).hexdigest()})

# Values here are reasoned second-check positions; they are deliberately not
# target machine labels, are never passed to a classifier, and imply no accuracy.
notes = {
 '00009': {'I':('supports_guarded_generic_mechanism','直接临床优势定义与同一资格父句','当前自身建立无有效手段→可提供手段，或现有治疗→显著临床改善关系；同版直接适用范围明确创新药/改良型新药。可修复明确创新联系的临床优势资格漏判。疾病严重程度、程序名或“新药”单词各自不能替代该链。','p0008/u00006；同一适用条件与 p0004 对象范围')},
 '00013': {'I':('supports_guarded_generic_mechanism','现有局限—具体改良—临床改善','仅治症状→治疗病因、逆转/抑制发展与持续获益是原句明示的实质关系，可支撑 I2；不要求文本已证明所有比较疗效。一般优化建议、未指明局限的新设计不得照搬。','当前 p0012 所在临床优势资格子项及其直接父句')},
 '00014': {'I':('supports_guarded_generic_mechanism','同疗效下安全性实质改良','无法替代的现有手段是比较基准；疗效相当、显著安全性优势、替换/重要补充是具体改善。可识别同疗效下的安全性改良，不能把一般安全义务升级为创新支持。','p0013/u00012；同一临床优势条件')},
 '00020': {
   'I':('supports_guarded_generic_mechanism','资格评估与实际申请开放','当前要求充分评估适用范围/条件并说明纳入理由，是实质申请资格；完整同一突破性程序有创新/改良对象。可支持资格/申请机制，不能称其已实施纳入后 I3 服务。','突破性程序提出申请阶段；p0017/u00019'),
   'F':('supports_guarded_generic_mechanism','按缺口分支提出同一优先支持申请','同一突破性程序的无有效防治手段分支明确药物可提供手段，并承接优先沟通资源。当前实际开放该程序申请且要求按条件说明理由，可按缺口分支识别；有比较优势的另一分支并不全部成为保障缺口。','突破性程序提出申请阶段，范围/条件与优先沟通机制分别保留')},
 '00028': {
   'I':('supports_guarded_generic_mechanism','已纳入品种的具体优先研发服务','原句直接配置沟通资源、指导并促进研发，纳入后阶段和对象明确；同版同一程序完整创新/改良范围可补足对象。可修复具体服务承接，不能只凭整个文件含创新词。','p0023/u00030；突破性程序（四）临床试验研制指导'),
   'F':('supports_guarded_generic_mechanism','同一缺口对象与同阶段优先资源','当前优先资源服务覆盖同一突破性程序的无有效防治手段分支，可在该分支建立缺口—优先沟通资源关系。需要同程序、纳入后同阶段、具体优先动作；不得从程序名向任意行政句扩散。','同一突破性程序范围与纳入后指导阶段')},
 '00034': {
   'I':('supports_guarded_generic_mechanism','保留同阶段研究问题反馈机会','当前允许错过首次窗口后在关键阶段会议提交首次拟讨论问题，直接父语境限定已纳入品种；同版该会议安排审评人员反馈下一步研究方案。保留的是可核明的具体研发机会，不是由“6个月”推导更快。','p0026/u00037；首次沟通与同一关键阶段会议'),
   'F':('supports_guarded_generic_mechanism','保留缺口分支的同一优先会议机会','同一已纳入突破性程序的无有效防治手段分支可使用当前保留的优先会议安排；不把所有晚申请、一般日期宽限或比较优势分支都记成缺口。','已纳入突破性程序的研发沟通阶段')},
 '00039': {
   'I':('supports_guarded_generic_mechanism','具名资格及优先技术服务的实质终止','当前“药审中心将终止”是具有主体、动作、对象的规范，非仅冒号；同版工作要求明确终止后不再优先沟通。可识别真实支持机会撤回，不能把所有冒号标题当规则。','p0029/u00044；同一程序终止与工作要求（三）'),
   'F':('supports_guarded_generic_mechanism','对同一缺口分支的优先机会限制','当前一般终止规范适用整个已纳入集合，其中有直接无有效防治手段分支，后果是撤回同一优先安排。可以诊断需要导向安排的限制，不能宣称患者治疗事实上被撤回。','一般终止规范，不是仅比较优势的特定终止成员')},
 '00040': {
   'I':('supports_guarded_generic_mechanism','明确临床优势资格的终止成员','原句特定比较优势条件失败，经直接终止父句撤回同一创新相关资格与优先技术支持，I 链有当前临床内容。不能从此反向补入其他终止成员的内容。','p0030/u00045；直接终止父句'),
   'F':('retain_original_boundary_no_unconditional_fix','特定比较优势成员不继承无有效手段兄弟分支','当前只说不再显示比现有治疗具有明显临床优势；这不等于所需治疗保障缺口。它与无有效手段分支可能在个别实际药品上重叠，但本文没有确定这种重叠。拒绝“突破性程序含缺口→每个终止成员 F”通用规则，不给机器替换值。','p0030/u00045；限定比较优势成员')},
 '00041': {
   'I':('supports_guarded_generic_mechanism','安全终止触发同一支持资格后果','重大安全问题并非创新依据；其直接终止父句及明确不再优先沟通后果构成资格限制。只能在当前确实承接该后果时使用，不能升级一般安全报告/监测义务。','安全触发子项→明确终止父句→同一工作要求（三）'),
   'F':('supports_guarded_generic_mechanism','一般安全触发条件可作用于原缺口分支','此触发未限定为比较优势成员，适用已纳入范围并限制同一优先技术资源，其中明确存在缺口分支。仅据该分支诊断优先安排限制；不推断所有重大安全问题都有公平含义，也不推断所有对象治疗被撤回。','一般终止触发条件，必须保留原对象分支与服务阶段')},
 '00052': {
   'I':('supports_guarded_generic_mechanism','申请资料中实质资格证据要求','原句要求按符合的突破性情形阐述无有效手段/比较优势临床证据及设计、终点、结果，与创新/改良申请资格直接相接。可识别 I1/I4 内容要求；申请人提交义务本身不等于已提供 I3 服务。','突破性程序申请表的具体申请理由内容'),
   'F':('supports_guarded_generic_mechanism','缺口条件证据与优先申请资格','当前直接要求无有效防治手段的临床证据，并用于同一支持资格；不是仅列一个表格空字段。另一比较优势分支不能承接缺口；纯一般材料提交不自动 F。','同一突破性程序申请表与适用条件')},
 '00068': {'I':('additional_chain_unproven_do_not_auto_fix','申报前技术机制已证，但当前对象交集不足','同版优先程序申报前机制确有数据讨论及检验/核查技术协商，当前也确实开放一并沟通，没有借用纳入后服务。但当前母对象是拟附条件批准品种；“整个优先程序有创新/改良分支”不能单独证明该受限对象交集有明确创新支持内容。已引用手册 I3 句专指对已纳入品种，不能原样套用申报前。需更具体对象/资格承接或手册已有申报前依据；本次允许材料不证明，故暂拒绝据此自动扩展 I。','p0064/u00076；附条件批准申报前母对象→优先程序申报前机制')},
 '00071': {
   'I':('additional_chain_unproven_do_not_auto_fix','并行申请真实，但不能把全程序对象当当前对象','当前确实开放优先申请，不能只当历史身份；但母句限定初步符合附条件批准要求的品种，而优先范围（五）本身未明示创新/改良。仅借全程序（ 一 ）的创新兄弟分支或总目的，未证明当前受限对象中的创新支持链。手册“实际开放同一安排”与“成员不得继承并列范围”存在需明确的边界，不能以这条分歧决定规则。','p0065/u00080；优先范围（五）与（ 一 ）不可直接混并'),
   'F':('additional_chain_unproven_do_not_auto_fix','附条件批准子集的保障缺口未由全范围证明','优先范围中的短缺/无有效治疗分支确有 F 关系，但当前附条件批准母对象并未给出该缺口；同版附条件批准部分指向外部技术指导原则，只明示公共卫生急需及应急疫苗，没有把急需明确为治疗保障缺口。拒绝单凭“整个优先程序含 F 分支”无条件给当前并行申请补 F；本次未打开外部指导原则。','当前附条件批准申请子集；缺少该子集与特定需要分支的可证连接')},
 '00089': {
   'I':('supports_guarded_generic_mechanism','同一儿童成员的实质剂型/规格定义','当前准确指定儿童新品种、剂型、规格成员；同版同一成员条件明确既有剂型/规格均不适用而新形式适用，建立局限—改变—使用改善，可补 I2；不凭“新品种”名称或前一创新药成员。','p0081/u00100；儿童成员→适用条件第3项'),
   'F':('supports_guarded_generic_mechanism','儿童新品种成员的无有效治疗子分支','准确匹配的第3项新品种第一 OR 分支明确儿童严重疾病且无有效药物/手段，直接决定当前优先资格。只有该分支可供 F；新剂型/规格便利不随之获得 F，“此外市场短缺”不能覆盖所有儿童成员。','儿童成员第3项（1）第一分支，不借优先范围其他成员')},
 '00091': {'F':('supports_guarded_generic_mechanism','特定既有资格被当前设为另一优先机会条件','当前“纳入突破性程序”是直接优先申请父句的资格成员，非只报告历史状态；同版该具名资格含明确无有效手段分支，可以保留缺口对象→当前优先待遇关系。不能把任意已纳入清单或资格名称都扩为 F。','优先范围（四）→同版突破性资格定义')},
 '00093': {'F':('supports_guarded_generic_mechanism','编号明确反向指认的其他优先情形','同版适用条件第5项明确说境外已上市境内未上市、临床急需的罕见病药按范围（六）申请，构成确指补全。可识别所需产品境内取得缺口与实际优先机会；不是仅名单身份、不是所有替代治疗无效，也不能借前一附条件批准成员。','p0085/u00104；适用条件第5项明确指向（六）')},
 '00103': {'F':('supports_guarded_generic_mechanism','当前直接 OR 缺口分支与资格父条件','当前第一分支直接写严重儿童疾病且无有效药物/手段，法定父句要求满足相关优先范围条件。它自身足以保留缺口—机会链；第二分支仅比较治疗优势，不因同一 OR 结构获得缺口含义。','儿童新品种（1）第一分支→应同时满足的优先条件')},
 '00105': {'F':('retain_original_boundary_no_unconditional_fix','既有规格不适用与仅给药便利边界','现有全部规格不适用而新规格适用，可能是实质可用治疗障碍，也可能只在给药便利范围；现有引文未进一步明确不可获得/使用所需治疗的保障后果。手册排除仅给药便利等，且不得借新品种无有效治疗或随后市场短缺分支。保留原待定；不把它当确定 rule0 错误或确定 native1 错误。','当前新规格子成员，排除新品种/市场短缺兄弟分支')},
 '00106': {'F':('supports_guarded_generic_mechanism','原句明确市场短缺与优先审评','当前自身明示市场短缺且鼓励研发申报的儿童用药品实行优先审评，缺口和机会在同一句，适合通用关系修复。不应强求“短缺药品”固定连续词序，不把所有儿童药/鼓励清单默认短缺。','p0097/u00117；“此外”独立限定的市场短缺安排')},
 '00114': {'F':('supports_guarded_generic_mechanism','同一申请表明确要求资格情形与证据','当前明确提出优先审评申请并提交附件1；选定包内同版“药品上市许可优先审评审批申请表”要求具体条款、适用条件和证据，且同一范围有短缺分支。可补有实质资格内容的申请，不是普通收件。三个程序均有附1，必须锁定优先程序表名/所在段落；仅同源 SHA 或“附件1”词匹配不足。','p0102/u00127；优先程序的附1申请表，绝不采用突破性程序的附1')}
}

positions=[]
for x in selected_reviews:
    status,family,reason,edge=notes[x['id'].split('-')[-1]][x['dimension']]
    p=packets[x['current_direct_material']['packet']['path']]
    positions.append({'id':x['id'],'dimension':x['dimension'],'diagnostic_position':status,'mechanism_family':family,'reason':reason,'required_legal_edge':edge,'current_text':p['source_bundle']['source_record']['text'],'current_pointer':x['current_direct_material']['pointer'],'source_ref':p['source_bundle']['source_record']['source_ref'],'phase01_review_class':x['review_class'],'phase01_reason':x['reason'],'replacement_label':None,'human_judgment':False})

families=[
 {'mechanism':'直接资格或成员的实质临床/属性关系','representatives':['00009/I','00013/I','00014/I','00052/I','00103/F'],'allow':'当前条件或确指同成员内容建立关系，并由法定资格父句连到待遇。','reject':'疾病严重、名称“新”、相邻创新成员、孤立表格字段。'},
 {'mechanism':'同版同程序同阶段的具体服务及保留机会','representatives':['00028/I,F','00034/I,F'],'allow':'纳入对象、当前技术服务动作、具体资源/反馈机制和对象分支各有证据。','reject':'把程序的一般收件/通知/日期都当服务；跨申报前/纳入后阶段。'},
 {'mechanism':'具名资格的实质终止及机会撤回','representatives':['00039/I,F','00040/I','00041/I,F'],'allow':'实际主体—终止动作—制度对象，加同程序明示停止优先安排后果；分支受限的条件只在自身对象内解释。','reject':'任意安全义务、纯冒号、00040/F 从无有效手段兄弟分支扩散。'},
 {'mechanism':'确指有限定义/成员/表单补全','representatives':['00089/I,F','00091/F','00093/F','00114/F'],'allow':'编号、成员名、程序所属申请表及所在阶段可准确对齐，且引用确含实质条件。','reject':'同源 SHA、任意附1/附件、相同标题、整文件语境；重复附1名称未消歧。'},
 {'mechanism':'直接需要缺口—优先机会','representatives':['00106/F','00093/F','00103/F'],'allow':'市场短缺、无有效治疗或临床急需所需产品境内取得缺口与实际机会相连。','reject':'仅急需、罕见病、儿童人群、便利或清单身份；把产品缺口改写为全体替代治疗无效。'},
 {'mechanism':'受限母对象的一并申请/沟通','representatives':['00068/I','00071/I,F'],'allow':'可证当前母对象与匹配的创新/缺口分支交集，且使用本阶段实际机制。','reject':'目前链不足时直接复制全优先程序的创新/短缺兄弟成员；不能靠分歧值选择解释。'}
]

after=[binding(Path(x['path'])) for x in before]
assert before==after
save('input-bindings.json',{'read_allowlist':before,'same_before_and_after':True,'only_exposed_review_and_19_declared_packets':True,'external_assets_manual_predictions_references_remaining_200_opened':False})
save('quote-pointer-checks.json',{'exact_quote_checks':quote_checks,'resource_text_metadata_checks':resource_checks,'no_normalization_or_fuzzy_match_needed':True,'external_asset_quotes_verified_only_inside_selected_embedded_packet_text':True,'manual_excerpts_status':'仅作为 phase01 提供的冻结引文使用，本次未打开或重新验证外部 manual.txt；不将引文转为独立手册文件核验。'})
save('selected-mechanism-reviews.json',positions)
count={s:sum(p['diagnostic_position']==s for p in positions) for s in sorted({p['diagnostic_position'] for p in positions})}
report={
 'created_utc':datetime.now(timezone.utc).isoformat(),
 'task':'Independent second semantic check of exposed first40 disagreement diagnostics',
 'source_review_count':40,'selected_packet_count':19,'selected_dimension_pair_count':28,
 'selection':'按关系模式与原2个待定选择代表；并额外挑战受限对象的一并申请/沟通。未检查另12项原packet，不将代表机制计数外推为40项审定结果。',
 'diagnostic_position_counts':count,
 'quote_checks':len(quote_checks),'all_quote_checks_exact':True,'resource_text_metadata_checks':len(resource_checks),'input_bindings_unchanged':20,
 'original_boundaries_retained':['RECODE25-00040/F','RECODE25-00105/F'],
 'additional_unproven_chains':['RECODE25-00068/I','RECODE25-00071/I','RECODE25-00071/F'],
 'main_result':'存在可复用的直接条件、同成员定义、同阶段服务、实质资格限制和明确短缺机会漏判机制；不能整体确认38项更支持LLM，也不能把当前代表解释转为金标签。',
 'mechanism_families':families,
 'guarded_fix_requirements':['不以 ID、真人/LLM 标签或指标作为判定条件。','同时验证源/版本、程序归属、阶段、当前实际动作、法定父句、目标成员与对象分支；同源 SHA 不替代关系边。','OR/成员树逐支处理；父级一般服务可对实际合格对象分支判定，特定成员不得反向继承全部兄弟内容。','具名申请/限制/终止可补直接机制；普通网站、收件、签章、报告义务、窗口数字自身不足。','重复表单编号必须按程序所属标题/段落消歧，不能全文搜索第一个附1。','先锁定正反例，特别保留00040/F、00105/F及00068/00071受限对象反例；本次没有实施或运行任何候选修复。'],
 'claim_limits':{'new_human_judgment':False,'new_gold_labels':False,'prediction_modification':False,'classification_rerun':False,'unseen_200_access':False,'remaining90_access':False,'population_accuracy_estimate':False,'formal_validation':False,'paper_final_ready':False},
 'manual_citation_limit':'本次只使用40项报告内已有冻结手册引文；外部手册未重新打开，因此不宣称再次独立核对其物理行号/全文。',
 'semantic_caution':'具体机器值是否应改变仍需通用候选规则、预先固定正反例及适用范围证明；当前诊断不是人类判断。'
}
save('report.json',report)
lines=['# 已暴露40项分歧的独立第二语义复核','',
 '直接条件与确指同成员定义、同阶段技术服务、实质终止及明确短缺优先关系有可复用漏判证据。不能把 phase01 的“38项更支持LLM”整体认证为正确标签。',
 '',f'仅从已暴露40项中选19个原包、28个维度项作模式代表；156条引用全部在所声明原包指针或包内正文精确匹配，95个嵌入正文片段的文本字节/长度/SHA一致，20个输入文件复核前后未变。其余12项原包未读，未打开 remaining、未暴露200材料、外部原资产或外部手册。',
 '', '原 00040/F、00105/F 的边界保留。此外，00068/I 与00071/I、F 的母对象限于附条件批准品种；当前引文虽证明实际沟通/申请机会，但未证明其受限对象与整个优先程序的创新/短缺兄弟分支交集。暂拒绝自动套用全程序维度，不将该判断改写成机器替换值。',
 '', '## 可支持的通用机制与排除条件','']
for f in families:
    lines += ['- **'+f['mechanism']+'**（'+','.join(f['representatives'])+'）：'+f['allow']+' 排除：'+f['reject']]
lines += ['','## 代表逐项意见','','| 原项 | 只读诊断立场 | 核心关系与限制 |','|---|---|---|']
labels={'supports_guarded_generic_mechanism':'支持有关系约束的通用修复机制','retain_original_boundary_no_unconditional_fix':'原边界保留，拒绝无条件修复','additional_chain_unproven_do_not_auto_fix':'当前链不足，暂拒自动扩展'}
for p in positions:
    lines.append('|'+p['id']+'/'+p['dimension']+'|'+labels[p['diagnostic_position']]+'|'+p['reason'].replace('|','/').replace('\n',' ')+'|')
lines += ['','## 修复进入条件','']
for r in report['guarded_fix_requirements']:lines+=['- '+r]
lines += ['','本次没有实施候选、分类重跑、改机器/参照/手册、新增金标签或人类判断。代表模式支持度不是40项正确率，更不是总体准确率或正式验证。手册只沿用40项报告内已有冻结引文，未再次核对外部全文与物理行号。','']
(OUT/'report.md').write_text('\n'.join(lines),encoding='utf-8')
members=[binding(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='output-seal.json']
save('output-seal.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'members':members,'member_count':len(members),'input_files_unchanged':True,'classification_rerun':False,'machine_labels_modified':False,'formal_validation':False})
for x in members:assert binding(Path(x['path']))==x
print(json.dumps({'output':str(OUT),'position_counts_are_not_label_counts':count,'selected_pairs':28,'selected_packets':19,'quote_checks':len(quote_checks),'resource_checks':len(resource_checks),'seal':binding(OUT/'output-seal.json'),'report':binding(OUT/'report.json')},ensure_ascii=False,indent=2))
