"""Protocol v1.3 I/F review, applied after v26.2.

Only I/F evidence, suppressions and review_flags are modified.  Matching is
local and title-masked.  No identifier, department, source name or reference
label is consulted.  This is exposed development, not independent validation.
"""
import hashlib
import re
from rule_support import RuleView, baseline, v25

BASIS_I = 'CAL-5D-20260926-v1.3 创新性及v1.2/v1.3创新来源边界'
BASIS_F = 'CAL-5D-20260926-v1.3 公平性及保障获取/临床管理/信息要求边界'
D = r'(?:药品|药物|新药|原研药|仿制药|创新药|中药|西药|中成药|制剂|用药|该药|本药|给药|药费|购药|送药)'
NOVEL = r'(?:创新药(?:物)?|新药|创新性药物|药物创新|药品创新)'
RND = rf'(?:{NOVEL}(?:[、和及与](?:创新)?(?:医疗)?器械)?(?:的)?(?:联合)?(?:研发|研制|开发|创制)|(?:研发|研制|开发|创制)(?:具有自主知识产权的)?{NOVEL})'
INFO = r'(?:信息|资料|证据|数据|情况)'
CONTENT = r'(?:评价|评估|比较|分析|判断|研究|论证|说明|描述|阐明|明确|考察|提交|提供|收集|补充|报送|包括|包含|内容涉及|应填|填写)'
CARRIER = r'(?:归档|文件命名|命名为|文件名|文件格式|按编号|格式转换|改名|仅上传|仅规定上传|排版|编号整理)'
WRONG = r'(?:信息系统|信息平台|管理系统|数据库|资料库|数据平台|办公系统|软件|文献|模型参数|设备|办公用品|打印纸|机关|医院行政|医院管理|行政审批)'
PROP = r'(?:创新性|创新点|创新程度|创新价值|原创性|原始创新|新颖性|传承性)'


def _parts(text):
    # Commas are hard object boundaries. Coordinating conjunctions delimit a
    # new claim too; a true cross-comma relation needs its own explicit grammar.
    for clause in re.finditer(r'[^。；;，,]+', text):
        boundaries=[clause.start()]
        for m in re.finditer(r'(?:并且|同时|并|且|另须|另应)(?=(?:须|应|需)?(?:评价|评估|比较|分析|提交|提供|补充|报送|归档|保密|公示|上传|鼓励|支持|保障))',clause.group()):
            boundaries.append(clause.start()+m.start())
        boundaries.append(clause.end())
        for a,b in zip(boundaries,boundaries[1:]):
            if a<b:yield re.compile(r'[\s\S]+').match(text,a,b)


def _sent_at(text, pos):
    return next(s for s in re.finditer(r'[^。；;]+', text) if s.start() <= pos < s.end())


def _norm(text):
    return v25._without_titles(baseline.matching_view(text)[0])


def _flag(v, rule, reason, start=None, end=None):
    x = {'rule': rule, 'dimensions': ['I'] if '_I_' in rule else ['F'],
         'reason': reason, 'action': 'no_positive_added_without_bound_relation'}
    if start is not None:
        a, b = v.raw_span(start, end)
        x.update(start=a, end=b, text=v.original[a:b])
    if x not in v.result.setdefault('review_flags', []):
        v.result['review_flags'].append(x)


def _context_object(v, part):
    """Resolve only the drug object, never a dimension mentioned in context."""
    # Explicit non-drug objects cannot borrow a drug noun from another clause.
    if re.search(WRONG + r'|医疗服务|试验设计|研究设计|就医流程|医院管理', part):
        return False, None
    if _has_drug_object(part):
        return True, None
    for p in v.record.get('verified_parent_context', []):
        t = _norm(p['text'])
        if _has_drug_object(t):
            return True, v.dependency(p, 'verified_parent_drug_object_only', t)
    for p, prefix in v.paragraph_prefixes():
        previous = list(re.finditer(r'[^。；;]+', _norm(prefix)))
        if previous and _has_drug_object(previous[-1].group()):
            return True, v.dependency(p, 'same_paragraph_drug_object_only', previous[-1].group())
    for dep in v.result.get('object_scope_dependencies', []):
        if re.search(D, _norm(dep.get('text', ''))):
            return True, dict(kind='validated_object_scope_only', object_scope=dep)
    return False, None


def _has_drug_object(text):
    return any(not re.match(r'企业|公司|监管机构|监督管理部门|管理部门|生产企业|资料库|信息平台',text[m.end():]) for m in re.finditer(D,text))


def _scope(v, part, position):
    ok, dep = _context_object(v, part)
    if ok:
        return ok, dep
    # A substantive dossier enumeration has one governing subject/action.
    # The current item must itself name the dimension; this never copies a
    # dimension from the header to another item.
    s = _sent_at(v.text, position)
    prefix = s.group()[:position-s.start()]
    if re.search(WRONG,part):
        return False,None
    if (re.search(r'药品(?:基本信息|评价|信息|资料)|申报药品|药物评价', prefix)
            and re.search(r'包括|包含|内容涉及|提交|提供|资料|材料', prefix)):
        return True, {'kind': 'current_unit_dossier_enumeration_object',
                      'antecedent_text': prefix}
    if _has_drug_object(prefix) and re.search(r'注明|说明|列明',prefix):
        return True,{'kind':'current_unit_property_information_object','antecedent_text':prefix}
    if (_has_drug_object(s.group()) and re.search(r'支付标准|共同支付|纳入医保支付范围|用药需求|治疗需求|尚无有效|缺乏有效|给药时点|吞咽困难|保障[^。；;]*可及',part)):
        return True,{'kind':'current_sentence_explicit_drug_content','antecedent_text':s.group()}
    if re.search(r'包括但不限于[:：][^。]*药品通用名称',v.text) and re.search(r'未(?:被)?满足的?(?:用药|治疗)需求',part):
        return True,{'kind':'current_unit_drug_dossier_list','antecedent_text':v.text}
    return False, None


def _carrier_only(value):
    # An independent content requirement survives a carrier instruction.
    # Each matcher below also checks the local span, not a whole document.
    return bool(re.search(CARRIER, value) and not _content_action(value))


def _content_action(value):
    # In "创新性评价报告", 评价 modifies a document noun, not an action.
    # Actually submitting the named report remains a content requirement.
    target=rf'(?:该|其|申报)?(?:{D}|{PROP}|公平性|明显临床优势|临床比较优势|作用机制|靶点)'
    return bool(re.search(rf'(?:评价|评估|比较|分析|阐明|测算){target}|(?:提交|提供|收集|补充|报送)(?:新的|新增)?{target}|(?:开展|进行|完成)(?:{target})?(?:评价|评估|分析|比较)|{D}(?:的)?(?:具有|具备|缺乏|不具有)[^。；;，,]*{PROP}',value))


def _disclosure_only(value):
    return bool(re.search(r'公示|公开|保密|披露|上传时间|提交时间|文件格式|专家(?:身份|名单)', value)
                and not _content_action(value))


def _emit(v, rule, dim, part, pattern, subtype, needs_scope=True):
    value = part.group()
    if _carrier_only(value):
        return
    for m in re.finditer(pattern, value):
        if _disclosure_only(_sent_at(v.text,part.start()+m.start()).group()) and not _content_action(value):
            continue
        ok, dep = _scope(v, value, part.start()+m.start()) if needs_scope else (True, None)
        if rule in {'V27_F_coverage_membership','V27_F_drug_directory_membership'}:
            if re.search(WRONG,value) or re.match(r'(?:后|之后|以后|流程|程序)',value[m.end():]):
                continue
            if not ok and re.search(r'纳入|调入|调出|列入',m.group()) and re.search(r'医保目录|药品目录|基本目录|常规目录',m.group()):
                ok,dep=True,{'kind':'explicit_drug_coverage_directory_object','antecedent_text':m.group()}
        if ok:
            v.add(rule, dim, part.start()+m.start(), part.start()+m.end(), subtype,
                  BASIS_I if dim=='I' else BASIS_F, dependency=dep)
        else:
            _flag(v, rule, 'local_drug_object_not_established', part.start()+m.start(), part.start()+m.end())


def _innovation(v, p):
    x=p.group()
    if _carrier_only(x):
        return
    # The property has an explicit drug possessor, or the current clause is
    # a property/content statement with a lawful contextual drug object.
    prop = PROP
    if not _disclosure_only(x):
        direct = rf'{D}(?:的)?(?:产品特性[、,，])?(?:具有|具备|缺乏|不具备|没有|有无|体现|是否具有|的)?(?:明显|充分|一定|较高|较低)?(?:{prop})'
        _emit(v,'V27_I_attribute','I',p,direct,'attribute',False)
        if not re.search(WRONG, x) and not re.search(rf'(?:是|属于|作为)(?:一项|一种)?[^。；;，,]*{PROP}[^。；;，,]*(?:工作|流程|制度|管理|机制|项目)',x):
            _emit(v,'V27_I_attribute_information','I',p,
                  rf'(?:{CONTENT})[^。；;，,]*?(?:{prop})(?:{INFO})?|(?:创新性|创新点|创新程度)(?:信息|资料|证据)', 'attribute')
            _emit(v,'V27_I_novel_mechanism','I',p,
                  r'(?:新(?:的)?(?:靶点|作用机制|化合物|分子实体)|(?:靶点|作用机制|化合物|分子实体)(?:的)?(?:新颖性|原创性)|(?:靶点|作用机制)(?:是|为|具有|不具有)(?:新颖|全新|创新)(?:性)?)','attribute')
            _emit(v,'V27_I_contextual_attribute','I',p,
                  rf'(?:具有|具备|缺乏|不具备)(?:较强|较高|明显|充分|一定)?{PROP}|{PROP}(?:的)?(?:评价|评估|比较|分析|判断)|创新价值(?:很高|较高|较低|不足)', 'attribute')
    # A product category alone (including 改良型新药) is not an attribute
    # evaluation. Explicit registration innovation classification is content.
    _emit(v,'V27_I_registration_innovation','I',p,
          rf'(?:注册分类|注册类别)(?:为|是|属于|判定为|包括|中的|中)?(?:第?[123一二三]类)?(?:创新药|改良型新药)|(?:按|根据|明确|说明|填报|填写|提供|评价|判定)[^。；;，,]*?{D}(?:的)?注册分类|(?:化学药|治疗用生物制品|中药)(?:的)?注册(?:分类|类别)(?:为|是|属于)?[12一二]类|(?:化学药|生物制品|治疗用生物制品|中药)注册按照[^。；;，,]*?创新药[^。；;，,]*?分类|(?:注明|标注|登记|记载)[^。；;，,]*?(?:创新药|改良型新药)[^。；;，,]*?属性|(?:应当为|应为)[^。；;，,]*[1一]类创新药(?:临床试验|注册|申请)', 'attribute')
    # Specific product alterations, not a list of new forms or suitability.
    target = r'(?:给药(?:途径|方式)|(?:药物|药品|制剂)(?:的)?(?:结构|特征|释放特征|释放行为)|片剂(?:的)?易碎性)'
    action = r'(?:改良|改善|优化|改进)'
    _emit(v,'V27_I_specific_modification','I',p,
          rf'{action}(?:了|其|该|相应|有关|具体|有针对性地|的)*{target}|{target}(?:得到|进行|予以|实施|作|做)?(?:了)?{action}|(?:口服|肌肉注射|静脉注射)制剂改(?:为)?(?:口服|肌肉注射|静脉注射)制剂|(?:大容量注射剂|小容量注射剂|注射用无菌粉针)[^。；;，,]*互改剂型', 'attribute',False)
    _emit(v,'V27_I_relative_product_change','I',p,
          rf'(?:相对|相比|相较|与)(?:于)?(?:既有|现有|原有|原)(?:的)?(?:药品|药物|制剂)[^。；;，,]*?(?:改变|改良|改进|优化|增加|减少|采用)[^。；;，,]*(?:结构|剂型|给药途径|释放|配方|工艺)|(?:新颖|原创|创新)(?:的)?(?:制剂设计|制剂技术|药物结构|药物设计)', 'attribute')
    # Patent status can itself be innovation-attribute information. Protection
    # offered as an incentive is separately classified research_support.
    if not re.search(WRONG + r'|专利(?:诉讼|争议|纠纷)会议', x) and not _disclosure_only(x):
        _emit(v,'V27_I_intellectual_property','I',p,
              r'自主知识产权|(?:药品|药物|新药|制剂)(?:的)?(?:专利|知识产权)|(?:专利|知识产权)(?:情况|信息|状态|保护|布局)|(?:取得|获得)(?:的)?专利权|(?:具有|拥有|取得|获得|申请|无|没有|缺乏)[^。；;，,]*?(?:化合物|药物|制剂|药品)专利', 'attribute')
    support = r'(?:支持|鼓励|促进|推动|激励|加快|资助|扶持)'
    _emit(v,'V27_I_research_support','I',p,
          rf'(?:不再|不予|取消对|停止|不)?{support}(?:对|为)?{RND}|(?:不再|不予)?{support}(?:研究和)?(?:创制|研发|研制|开发){NOVEL}|取消(?:了)?对{RND}(?:的)?(?:政策|资金|资源|平台)?支持|对{RND}(?:的)?(?:予以|给予|提供|加大|加强|不予|取消)?(?:政策|资金|资源|平台)?支持|{RND}(?:获得|得到|接受|享有|不再享有)(?:了)?(?:政策|资金|资源|平台|数据服务)?支持|为{RND}(?:提供|配置|投入)[^。；;，,]*(?:资金|投资|数据服务|平台|资源|支持)|{support}(?:医药企业|药企|科研院所|医疗机构|研发机构|企业)(?:[、及和与]*(?:医药企业|药企|科研院所|医疗机构|研发机构|企业))*(?:等)?(?:开展|实施|进行)(?:以)?{RND}(?:为导向的)?(?:科研攻关|研究|项目)?|(?:审评审批|审评|审批)资源[^。；;，,]*向[^。；;，,]*创新药临床试验申请[^。；;，,]*倾斜','research_support',False)
    _emit(v,'V27_I_research_program','I',p,
          rf'(?:设立|扩大|建立|取消|停止){RND}(?:支持|鼓励|资助)?专项|{RND}(?:支持|鼓励|资助)专项(?:设立|扩大|建立|取消|停止)|{RND}(?:支持|鼓励|资助)试点(?:计划)?', 'research_support',False)
    _emit(v,'V27_I_qualified_research_support','I',p,
          rf'{support}(?:了)?(?:以[^。；;，,]*?为导向的|(?:抗|治疗|防治)[^。；;，,]*?|国内|本土)?{RND}|{support}{NOVEL}在[^。；;，,]*?(?:进行|开展)(?:研发|研制|开发|创制)', 'research_support',False)
    _emit(v,'V27_I_restructured_product','I',p,
          r'(?:试验药|药品|药物|该药)(?:为|是)(?:明确)?已上市(?:产品|药品)(?:的)?改构产品','attribute')
    _emit(v,'V27_I_protection_duration','I',p,
          rf'{D}(?:品)?(?:试验)?数据保护期(?:为|是)[0-9一二三四五六七八九十]+年','research_support')
    # Historical support identity in a dossier describes attribute; it does
    # not assert a new support measure. Also block a new support regex inside
    # that question, locally, without affecting another substantive clause.
    history = re.search(r'(?:是否|有无|曾经|既往)[^。；;，,]*(?:重大新药创制|科技重大专项|科技专项)[^。；;，,]*(?:支持|立项|项目|专项)',x)
    if history:
        v.drop_within('I',p.start(),p.end(),'V27_I_support_identity_not_measure','本句仅询问既往专项支持身份；来源记属性，不推定新的研发支持措施。')
        _emit(v,'V27_I_historical_support_attribute','I',p,history.re.pattern,'attribute')
    # Direct drug beneficiaries and actual incentive instruments are needed.
    _emit(v,'V27_I_ip_incentive','I',p,
          rf'(?:对|为){D}[^。；;，,]*?(?:原创性成果|创新成果)[^。；;，,]*?(?:支持|加快|加强|促进)[^。；;，,]*专利(?:布局|保护|转化)|(?:支持|加快|加强|促进)[^。；;，,]*?{D}[^。；;，,]*?(?:原创性成果|创新成果)[^。；;，,]*专利(?:布局|保护|转化)|(?:{D}|儿童用药品|罕见病用药品)(?:[、和及与或]*(?:首个化学仿制药|独家中药品种|儿童用药品|罕见病用药品))*[^。；;，,]*?(?:给予|享有|延长|取消|不再给予)[^。；;，,]*?(?:数据保护期|市场独占期)','research_support')


def _fairness(v,p):
    x=p.group()
    if _carrier_only(x):
        return
    # Each object-based expression is local. A drug mention elsewhere cannot
    # turn software/data access or office shortages into treatment access.
    bad = bool(re.search(WRONG + r'|数据(?:的)?可|证据(?:的)?可|研究(?:代表性|参与)|试验参与|访视',x))
    if not bad:
        _emit(v,'V27_F_patient_drug_access','F',p,
              r'(?:患者|参保人|参保人员|病人)(?:仍|尚|将)?(?:难以|无法|不能|未能)(?:及时|持续)?(?:获得|获取|买到|取得)(?:所需|必要|治疗所需)?(?:药物|药品)|(?:保障|保证|确保|帮助|允许)(?:患者|参保人|参保人员|病人)(?:能够|可以|及时|持续)?(?:获得|获取|取得)(?:所需|必要)?(?:药物|药品)','access')
        _emit(v,'V27_F_access_property','F',p,
              rf'{D}(?:的)?(?:可及性?|可获得性)|(?:可获得|可及)(?:的)?(?:药品|药物|治疗药物)|(?:评价|评估|改善|提高|保障|保证|促进)[^。；;，,]*?(?:药物|药品|用药)可及|用药保障(?:需求|机制|水平|能力)|药品保障机制|药品目录(?:保障)?短板|用药需求短板|(?:弥补|填补|存在|仍有|消除)(?:用药|药品|治疗)?保障空白|(?:用药|药品)?保障尚不充分|(?:创新药|药品|药物)[^。；;，,]{{0,8}}患者可及|药品(?:和|及|与)?医疗器械[^。；;，,]*?可及(?:得到|性|水平|保障)', 'access')
        # Short generic access predicates require a local/verified drug
        # subject. Other objects, especially data and procedures, are blocked.
        _emit(v,'V27_F_access_predicate','F',p,
              r'(?:改善|提高|降低|评价|评估|分析|比较|保障|影响|阻碍)(?:其|该药的)?可及性|供应保障|供药中断|药品断供|(?:药品|药物|用药)(?:供应)?短缺|短缺药品|市场短缺[^。；;，,]*用药品','access')
    # Concrete coverage eligibility/membership/conditions, including negative
    # membership, differs from the bare name 支付范围 or a filing procedure.
    coverage = r'(?:医保(?:基金)?支付范围|基本医疗保险基金支付范围|医保保障范围|用药保障范围|药品保障范围|医保目录|药品目录|基本目录|常规目录|保障范围)'
    # Membership must predicate a drug's coverage.  "新增适应症", a
    # historical listing date, and a forecast of covered sales do not change
    # a patient's coverage merely because the same clause names a directory.
    membership = r'(?:自动属于|属于|纳入|列入|调入|调出|不属于|不纳入|不予纳入|不再纳入|排除|移出)'
    _emit(v,'V27_F_coverage_membership','F',p,
          rf'{D}[^。；;，,]*?{membership}[^。；;，,]*?{coverage}|(?:扩大|扩展|拓展|拓宽|缩小){D}(?:的)?(?:支付|保障|报销)范围|(?:将|把)[^。；;，,]*?药[^。；;，,]*?纳入保障范围','access')
    _emit(v,'V27_F_drug_directory_membership','F',p,
          rf'{D}(?:予以|应予|不再|不予|不得)?(?:纳入|调入|调出)目录(?!文件|清单编号)|(?:纳入|列入)(?:目录乙类|[“\"“]?乙类药品[”\"]?管理)', 'access')
    if not bad:
        _emit(v,'V27_F_drug_need_assessment','F',p,
              r'(?:开展|进行|组织|实施)(?:基层医疗卫生机构|医疗卫生机构|临床|患者)?用药需求评估|(?:填补|弥补)(?:药品)?目录空白','access')
    _emit(v,'V27_F_coverage_condition','F',p,
          rf'(?:仅限|限定|限于|符合|满足|不符合|不满足)[^。；;，,]*?(?:{D})[^。；;，,]*?(?:由|予以|可以|方可|不得|不予)[^。；;，,]*?(?:医保|基本医疗保险|基金)(?:基金)?支付|{D}(?:费用)?[^。；;，,]*?(?:按照|按|依照|符合)[^。；;，,]*?(?:由|纳入)[^。；;，,]*?(?:基本医疗保险|医保)(?:基金)?(?:支付|报销)|(?:基本医疗保险|医保)(?:基金)?(?:不予|予以|仅|可|应)?支付(?:的)?(?:药品|药物|用药)(?:费用)?|(?:医保|基金)支付(?:条件|范围)(?:为|是|限定为|仅限于|限于)[^。；;，,]*(?:患者|用药|药品|药物|治疗|适应症)','access')
    # Titles are still masked; 《药品目录》 may occur between a substantive
    # stocking verb and a real drug noun without becoming the trigger itself.
    _emit(v,'V27_F_stocking_and_supply','F',p,
          rf'(?:优先|必须|应|须|促进|提高|增加|保障|确保|保证|合理|按需)(?:配备|供应|配置|配备和使用|配备使用)[^。；;，,]*?{D}|(?:促进|提高|提升|增加|保证|保障)[^。；;，,]*?{D}(?:优先)?配备(?:使用)?|(?:药品|药物|基本药物)(?:优先)?配备(?:使用)?(?:情况|状况|信息|数据)|(?:未|没有|停止|中断|暂停)[^。；;，,]*?(?:向(?:(?:医保)?定点)?(?:医疗机构|医药机构|零售药店|患者))[^。；;，,]*?供应[^。；;，,]*?{D}|(?:未|不|没有)?按(?:协议|约定)[^。；;，,]*?保障市场供应[^。；;，,]*?{D}|保障(?:市场|持续|稳定)?(?:的)?(?:药品|药物|用药)(?:持续|稳定)?供应|(?:药品|药物|用药)(?:的)?(?:持续|稳定)?供应(?:保障|中断|停止|不足|不充分)|(?:药品|药物|用药)(?:的)?(?:断供|缺货)','access')
    _emit(v,'V27_F_supply_obligation','F',p,
          rf'{D}[^。；;，,]*?(?:应当|应|须|必须|负责|未能|没有|停止|不再)(?:持续|稳定|及时|保障|确保|保证|向医疗机构)?供应|(?:药品|药物|用药)(?:的)?(?:持续|稳定)?供应(?:应当|应|须|必须|需要)(?:得到)?(?:保障|保证|持续|稳定)','access')
    _emit(v,'V27_F_supply_information','F',p,
          r'(?:收集|报告|监测|提供|更新|分析)药品配备(?:及|和|与|、)(?:供应|配送)(?:情况|状况|信息|数据)|(?:收集|报告|监测)药品配备[^。；;，,]*(?:供应|配送)[^。；;，,]*信息','access')
    # Operational delivery alone is not a coverage channel. Patient-facing
    # dispensing, home delivery, outpatient/retail access and dual-channel
    # arrangements are included, with ordinary trial logistics excluded.
    if not re.search(r'临床试验|研究项目|受试者|访视|办公|样本',x):
        _emit(v,'V27_F_treatment_channel','F',p,
              r'(?:医疗机构|医药机构|零售药店|药店)[^。；;，,]*送药上门|(?:患者|参保人|参保人员)[^。；;，,]*?(?:可在|可以在|允许在|能够在|通过|从)[^。；;，,]*?(?:药店|药房|医疗机构)[^。；;，,]*?(?:购药|取药|获得药物|获得药品)|(?:药品|用药)(?:的)?(?:获取渠道|购药渠道)|(?:双通道)[^。；;，,]*(?:供药|供应|配备|购药|取药|药品范围)|(?:不得|不应)[^。；;，,]*?(?:限制|影响|阻碍)[^。；;，,]*(?:配备|用药|获得药品)|(?:用药|药品配备使用|药品配备|药品使用|药品)[^。；;，,]*(?:不受|不再受)[^。；;，,]*(?:一品两规|药占比)[^。；;，,]*(?:限定|限制|约束)|装置[^。；;，,]*附在药品包装中[^。；;，,]*避免难以获得装置','access')
    gap = (r'(?:已无|尚无|并无|没有|缺乏|缺少|不存在)(?:现有的?|标准的?|有效的?|可用的?|其他的?)*'
           r'(?:治疗|防治)(?:措施|手段|选择|方案|药物)|(?:晚期)?无药可治|'
           r'未(?:被)?满足的?(?:用药|治疗)需求|(?:用药|治疗)需求(?:尚未|仍未|不能|无法)满足|'
           r'(?:患者|人群)(?:仍)?(?:未能|无法|不能)(?:得到|获得)(?:充分[、,，]?)?有效治疗|'
           r'(?:治疗|用药)需求(?:迫切|急迫)|满足[^。；;，,]*(?:急迫|迫切)[^。；;，,]*(?:用药|治疗)需求')
    if not re.search(r'数据需求|研究需求|入组需求',x):
        _emit(v,'V27_F_unmet_treatment','F',p,gap,'access')
    # Affordability always contains patient-payment or drug-burden semantics;
    # a price phrase or an unqualified burden is not enough.
    if not re.search(r'企业|医院成本|机构成本|科研经费|项目经费|差旅费',x):
        _emit(v,'V27_F_patient_affordability','F',p,
              r'(?:患者|参保人员|参保人|病人)(?:的)?(?:经济负担|费用负担|支付负担|支付能力|药费负担|用药负担)|(?:患者|参保人员|参保人|病人)[^。；;，,]*(?:难以承担|无法承担|负担不起|可负担|无力支付)[^。；;，,]*(?:药费|药品费用|治疗费用|用药费用)|(?:减轻|降低|加重|增加|缓解)(?:患者|参保人|参保人员)?(?:的)?(?:用药负担|药费负担)|(?:药品|药物|用药)(?:的)?可负担性|(?:药费|药品费用|支付标准)[^。；;，,]*(?:患者|参保人|参保人员)(?:自付|自费)|(?:基金和|基金与)(?:参保人员|参保人|患者)共同支付(?:的)?(?:全部)?(?:药品)?费用|(?:慈善捐赠|医疗救助)[^。；;，,]*困难群众[^。；;，,]*(?:用药|药品|药费)','affordability')
        _emit(v,'V27_F_patient_price_share','F',p,
              r'药品(?:挂网)?价格[^。；;，,]*(?:患者|参保人员|参保人)(?:自付|自费)','affordability')
        _emit(v,'V27_F_patient_share_proportion','F',p,
              r'(?:参保人|参保人员|患者)自付(?:一定)?比例','affordability')
    # No unconstrained task-to-obstacle wildcard. Commas and an explicit
    # different subject break the relation, including within one clause.
    task = r'(?:打开(?:药品|药物)?包装|(?:准确)?量取(?:及使用|和使用|并使用)?药物|(?:吞咽|服用|使用|管理)药物|给药(?:时点|频次|途径|方式)|(?:药物|用药)(?:监测|管理))'
    obstacle = r'(?:困难|障碍|复杂性|复杂|难以完成|无法完成|负担)'
    _emit(v,'V27_F_drug_use_obstacle','F',p,
          rf'{task}(?:的|时|方面|过程)?(?:可能|容易|易|仍|会)?(?:存在|遇到|面临|出现|有|较为)?(?:一定|较大|较高|明显)?{obstacle}|(?:难以|无法|不能)(?:准确|正确|独立|顺利|自行)?{task}|吞咽困难(?:作为|纳入)(?:评价|评估)内容','clinical_management')
    if not re.search(r'医院管理|行政管理|机构管理|信息系统|试验管理|研究管理|数据管理',x):
        _emit(v,'V27_F_management_assessment','F',p,
              r'临床管理难度|(?:评价|评估|分析|说明)[^。；;，,]*?(?:药物使用|药品使用|用药|给药|药物监测)(?:的)?(?:管理)?(?:难度|复杂性|障碍|负担)|(?:评价|评估)[^。；;，,]*?(?:该药|药物|用药)(?:的)?监测频率|(?:基层|患者)(?:能否|是否能够|无法|难以)完成(?:药物|用药|必要)?监测','clinical_management')
    if not _disclosure_only(x) and not re.search(r'公平竞争|企业公平|所有制|招标公平|就业公平',x):
        _emit(v,'V27_F_dimension_information','F',p,
              rf'(?:{CONTENT})[^。；;，,]*公平性(?:{INFO})?|公平性(?:信息|资料|证据)|公平性(?:的)?(?:比较优势|综合研判|评价|评估)','dimension_information')


def _verified_innovation_scope(v):
    """Validate a source excerpt bound to this exact unit and component.

    The excerpt resolves only the innovation-qualified drug object. It cannot
    supply a current eligibility or comparative-advantage statement.
    """
    scope=v.record.get('verified_innovation_scope_v27')
    if scope is None:
        return None
    assert isinstance(scope,dict), 'innovation scope must be an object'
    assert scope.get('verified') is True, 'innovation scope is not verified'
    quote=scope.get('text')
    assert isinstance(quote,str) and quote.strip(), 'innovation scope text missing'
    digest=lambda value:hashlib.sha256(value.encode()).hexdigest()
    assert scope.get('text_sha256')==digest(quote), 'innovation scope text hash mismatch'
    assert scope.get('original_unit_sha256')==digest(v.original), 'innovation scope unit hash mismatch'
    source=v.record.get('unit_source_sha256') or v.record.get('source_sha256')
    assert source and scope.get('source_sha256')==source, 'innovation scope source mismatch'
    assert scope.get('component')=='突破性治疗程序', 'innovation scope component mismatch'
    binding=scope.get('component_binding')
    assert isinstance(binding,dict), 'innovation scope component binding missing'
    assert binding.get('unit_id') and binding['unit_id']==v.record.get('unit_id'), 'innovation scope component unit mismatch'
    assert binding.get('candidate_sha256') and binding['candidate_sha256']==v.record.get('candidate_sha256'), 'innovation scope component candidate mismatch'
    loc=scope.get('locator')
    assert isinstance(loc,dict) and isinstance(loc.get('paragraph_id'),str) and loc['paragraph_id'].strip(), 'innovation scope paragraph locator missing'
    lines=loc.get('source_lines')
    assert isinstance(lines,list) and lines and all(type(n) is int and n>0 for n in lines), 'innovation scope source lines missing'
    quote=_norm(quote)
    assert re.search(r'创新药|改良型新药',quote) and re.search(r'申请适用突破性治疗药物程序',quote), 'innovation scope does not establish the program object'
    return {k:scope[k] for k in ('text','text_sha256','source_sha256','original_unit_sha256','component','verified','locator','component_binding')}


def _linked_relations(v, innovation_scope):
    # Only these declared grammars may bridge a comma. The bridge has a
    # purpose/beneficiary relation, not co-occurrence of two unrelated topics.
    for s in v.sentences():
        x=s.group()
        # A supply failure may precede a coordinated data criterion and name
        # the affected drug only at the end of the sentence.  Keep the supply
        # relation itself; the intervening information platform is not the
        # object whose access is being coded.
        for m in re.finditer(r'(?:未|没有|停止|中断|暂停)[^。；;，,]{0,20}?向(?:医保)?定点(?:医药|医疗)机构供应[^。；;，,]{0,80}?(?:目录)?药品',x):
            if not _carrier_only(m.group()):
                v.add('V27_F_drug_supply_failure_with_postposed_object','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
        # Dimension lists can precede their governing evaluation verb. The
        # list must be attached by 从/围绕/在 to an actual drug evaluation,
        # not merely occur in a disclosed list of dossier names.
        dimension=r'(?:安全性|有效性|经济性|创新性|公平性|适宜性|可及性)'
        if _has_drug_object(x) and not _carrier_only(x) and not _disclosure_only(x):
            for listing in re.finditer(rf'{dimension}(?:[、及和与]{dimension})+',x):
                head=x[:listing.start()]
                tail=x[listing.end():]
                if not re.search(r'(?:从|围绕|在)(?:(?:药品|药物)(?:的)?)?$',head):
                    continue
                if not re.search(r'评价|评估|比较优势|整合分析|综合研判',tail):
                    continue
                for token in re.finditer(r'创新性|公平性|可及性',listing.group()):
                    dim='I' if token.group()=='创新性' else 'F'
                    subtype='attribute' if dim=='I' else 'access' if token.group()=='可及性' else 'dimension_information'
                    v.add('V27_'+dim+'_dimension_evaluation_list',dim,s.start()+listing.start()+token.start(),s.start()+listing.start()+token.end(),subtype,BASIS_I if dim=='I' else BASIS_F,dependency={'kind':'current_unit_explicit_dimension_evaluation','governing_text':x})
        if re.search(r'注册分类标准|药品注册(?:分类|类别)',x):
            for m in re.finditer(r'[1一]\s*类\s*(?:化学药品?|治疗用生物制品|中药)',x):
                v.add('V27_I_standard_based_class_one','I',s.start()+m.start(),s.start()+m.end(),'attribute',BASIS_I)
        # A single drug-evaluation sentence can distribute its object and its
        # named evaluation dimensions over comma-separated phrases.
        for m in re.finditer(r'(?:评价[^。；;，,]{0,35}药品|药品[^。；;，,]{0,35}评价)[^。；;]{0,110}?从[^。；;]{0,45}?创新性[^。；;]{0,30}?维度[^。；;]{0,35}?(?:分析|研判|评价|评估)',x):
            if not re.search(WRONG,m.group()) and not _carrier_only(m.group()):
                v.add('V27_I_drug_evaluation_dimension','I',s.start()+m.start(),s.start()+m.end(),'attribute',BASIS_I)
        goal=re.search(r'(?:为|为了)?(?:促进|支持|鼓励|推动|激励)(?:药品|药物|新药)(?:的)?创新(?:发展|研发)?',x)
        mechanism=re.search(r'(?:完善|建立|健全|实施|制定|强化|扩大|取消)(?:药品)?(?:试验)?数据保护(?:制度|机制|办法|政策)',x)
        if goal and mechanism and not re.search(r'归档|文件命名|编号整理|格式转换',x):
            between=x[min(goal.end(),mechanism.end()):max(goal.start(),mechanism.start())]
            if not re.search(r'另行|另一个|与此同时|办公|软件|数据库',between):
                v.add('V27_I_data_protection_purpose','I',s.start()+min(goal.start(),mechanism.start()),s.start()+max(goal.end(),mechanism.end()),'research_support',BASIS_I)
        # Research data services must explicitly support innovative-drug R&D.
        m=re.search(r'(?:开发|提供|建设)[^。；;，,]*创新药研发[^。；;，,]*数据(?:产品|服务)[^。；;，,]*支持',x)
        if m and not _carrier_only(m.group()):
            v.add('V27_I_rnd_data_service','I',s.start()+m.start(),s.start()+m.end(),'research_support',BASIS_I)
        for m in re.finditer(r'(?:开发|提供|建设)(?:适配|面向|供|用于)?创新药(?:物)?研发(?:需求)?(?:的)?数据(?:产品|服务)',x):
            local=next((p.group() for p in _parts(x) if p.start()<=m.start()<p.end()),x)
            if not _carrier_only(local):
                v.add('V27_I_rnd_data_service','I',s.start()+m.start(),s.start()+m.end(),'research_support',BASIS_I)
        # A drug-beneficiary conditional remains one relation across its
        # comma, provided the protection instrument concerns its trial data.
        pattern=rf'{D}(?:在|如|若)[^。；;，,]*(?:条件|要求|程序)[^。；;，,]*[,，](?:对(?:其|全部|相关)?(?:试验数据)|给予该(?:药品|药物))[^。；;，,]*?(?:给予|享有|延长|取消|不再给予)?[^。；;，,]*?(?:数据保护期|市场独占期)'
        for m in re.finditer(pattern,x):
            if not re.search(WRONG,m.group()) and not _carrier_only(m.group()):
                v.add('V27_I_conditional_ip_incentive','I',s.start()+m.start(),s.start()+m.end(),'research_support',BASIS_I)
        # Protection clauses are often expressed as a drug beneficiary,
        # registration/launch conditions, then the grant or duration. Every
        # intervening clause must continue that same legal-condition chain.
        protection=r'(?:给予|享有|延长|取消|不再给予)(?:一定的|[0-9一二三四五六七八九十]+年)?(?:试验)?数据保护期|(?:试验)?数据保护期(?:为|是)[0-9一二三四五六七八九十]+年'
        for m in re.finditer(protection,x):
            prefix=x[:m.end()]
            drug=next((d for d in re.finditer(D,prefix) if _has_drug_object(d.group()+prefix[d.end():d.end()+8])),None)
            if drug is None:continue
            relation_start=max(prefix.rfind(',',0,drug.start()),prefix.rfind('，',0,drug.start()))+1
            relation=prefix[relation_start:]
            chunks=re.split('[,，]',relation)
            condition=r'上市|注册|试验数据|受保护|许可|适应症|自首次|符合.*(?:款|条)|按照.*(?:款|条)|保护期|给予|享有|延长|取消|不再给予'
            if (re.search(r'上市|注册|试验数据',relation) and all(re.search(condition,c) for c in chunks)
                    and not re.search(WRONG+r'|另行|另一个|其他事项|与此同时',relation)
                    and not _carrier_only(x) and not _disclosure_only(x)):
                v.add('V27_I_registration_bound_data_protection','I',s.start()+relation_start,s.start()+m.end(),'research_support',BASIS_I)
        # A possessive property list keeps its drug subject across list
        # punctuation. A platform's properties cannot borrow that subject.
        for m in re.finditer(r'(?:药品|药物|制剂)(?:的)?产品特性[、,，](?:创新程度|创新性|原创性)',x):
            if not _carrier_only(x):
                v.add('V27_I_drug_property_enumeration','I',s.start()+m.start(),s.start()+m.end(),'attribute',BASIS_I)
        # Explicit patient sharing is a sentence-level payment relation;
        # intervening commas may separate the price and the payer.
        if _has_drug_object(x) and not _carrier_only(x):
            for m in re.finditer(r'(?:医保)?基金(?:和|与)(?:参保人员|参保人|患者)共同支付(?:的)?全部费用|(?:超出部分|超出支付标准部分)(?:需|应)?(?:由)?患者自付|可负担性[^。；;]*用药治疗费用[^。；;]*家庭[^。；;]*收入',x):
                v.add('V27_F_explicit_patient_payment_relation','F',s.start()+m.start(),s.start()+m.end(),'affordability',BASIS_F,dependency={'kind':'current_sentence_drug_payment','antecedent_text':x})
            for m in re.finditer(r'保障(?:更加)?(?:公平|充分)?可及|(?:推进|加强)药品供应[^。；;，,]*下沉',x):
                v.add('V27_F_explicit_access_goal','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F,dependency={'kind':'current_sentence_drug_access','antecedent_text':x})
            # The channel name alone is only an existing identity. A stated
            # coverage decision or uniform payment arrangement supplies F.
            if re.search(r'双通道',x):
                for m in re.finditer(r'施行统一的支付政策|(?:单独支付的)?药品范围[^。；;]*(?:确定|扩大|调整)|纳入异地就医直接结算范围',x):
                    v.add('V27_F_channel_coverage_arrangement','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F,dependency={'kind':'current_sentence_explicit_channel_coverage','antecedent_text':x})
        # Packaging devices can provide access across explanatory commas.
        m=re.search(r'装置[^。；;]*附在药品包装中[,，](?:以)?避免难以获得装置',x)
        if m and not _carrier_only(x):
            v.add('V27_F_required_device_access','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
    # A quoted directory is a valid *object* of a substantive inclusion or
    # removal decision. Its name never triggers a label by itself.
    directory=r'《(?:药品目录|医保目录|基本目录|常规目录|商保创新药目录)》'
    for s in re.finditer(r'[^。；;]+',v.normalized):
        x=s.group()
        for m in re.finditer(rf'(?:纳入|调入|调出|列入){directory}|{directory}(?:不再|不予|不得)?新增\s*(?:OTC\s*)?药品',x):
            local=next((p.group() for p in _parts(x) if p.start()<=m.start()<p.end()),x)
            if (_carrier_only(local) or _disclosure_only(local) or re.match(r'(?:后|之后|以后|流程|程序)',x[m.end():])
                    or re.search(r'(?:申报|申请|拟|建议(?:新增)?)$',x[:m.start()])):
                continue
            # Do not use action words that occur inside another document title.
            if x[:m.start()].count('《')!=x[:m.start()].count('》'):
                continue
            v.add('V27_F_quoted_directory_decision','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F,dependency={'kind':'quoted_directory_as_decision_object','matching_object':m.group()})
        # The protected drug or applicant, trial data, and incentive may be
        # separated by eligibility or temporal clauses. Keep all three anchors.
        incentive = (r'(?:原研药品|改良型药品|创新药|创新治疗用生物制品)[^。；;]{0,180}?'
                     r'(?:首次[^。；;]{0,35}?上市许可|注册申请[^。；;]{0,65}?试验数据|申请人提交[^。；;]{0,65}?试验数据)'
                     r'[^。；;]{0,100}?(?:给予|享有|延长|取消|不再给予)(?:\d+年|一定的?)?数据保护期')
        for m in re.finditer(incentive,x):
            if not re.search(WRONG,m.group()) and not _carrier_only(m.group()):
                v.add('V27_I_drug_data_incentive','I',s.start()+m.start(),s.start()+m.end(),'research_support',BASIS_I)
        for m in re.finditer(r'在数据保护期内[^。；;]{0,90}?其他申请人[^。；;]{0,90}?依赖[^。；;]{0,35}?受保护的数据[^。；;]{0,90}?(?:新药|仿制药|生物类似药)[^。；;]{0,70}?上市申请[^。；;]{0,35}?不予许可',x):
            if not re.search(WRONG,m.group()) and not _carrier_only(m.group()):
                v.add('V27_I_data_exclusivity_rule','I',s.start()+m.start(),s.start()+m.end(),'research_support',BASIS_I)
        for pattern in (r'药品的数据保护范围包括[^。；;]{0,100}?新的临床试验数据',
                        r'药品上市(?:申请|许可)[^。；;]{0,100}?依赖[^。；;]{0,35}?其他申请人受保护数据[^。；;]{0,35}?不予许可'):
            for m in re.finditer(pattern,x):
                if not re.search(WRONG,m.group()) and not _carrier_only(m.group()):
                    v.add('V27_I_drug_data_protection_terms','I',s.start()+m.start(),s.start()+m.end(),'research_support',BASIS_I)
        for pattern in (r'全链条强化政策保障[^。；;]{0,80}?助推创新药突破发展',
                        r'重点创新药品种[^。；;]{0,35}?纳入\d+日通道',
                        r'支持中药传承和创新[^。；;]{0,95}?鼓励[^。；;]{0,40}?研制中药'):
            for m in re.finditer(pattern,x):
                if not re.search(WRONG,m.group()) and not _carrier_only(m.group()):
                    v.add('V27_I_explicit_development_support','I',s.start()+m.start(),s.start()+m.end(),'research_support',BASIS_I)
        for m in re.finditer(r'(?:已知|现有|既有)(?:非处方)?药[^。；;]{0,40}?活性成份[^。；;]{0,35}?组成的新的复方制剂|(?:非处方药的活性成份)[^。；;]{0,30}?组成的新的复方制剂',x):
            v.add('V27_I_new_combination_from_existing_ingredients','I',s.start()+m.start(),s.start()+m.end(),'attribute',BASIS_I)
        # Membership survives an intervening eligibility clause. Quoted
        # directory names are read only as the object of an explicit verb.
        for m in re.finditer(r'(?:(?:竞价|谈判|续约)?药品)[^。；;]{0,80}?(?:支付标准|专家评审)[^。；;]{0,80}?纳入(?:常规|基本|医保|药品)目录(?:乙类)?',x):
            if not _carrier_only(m.group()):
                v.add('V27_F_cross_clause_directory_membership','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
        for m in re.finditer(r'药品(?:和|及|与)?医疗器械[^。；;]{0,35}?(?:安全|有效)[、,，][^。；;]{0,20}?可及(?:得到|性|保障)',x):
            if not re.search(WRONG,m.group()):
                v.add('V27_F_coordinated_drug_access','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
        for m in re.finditer(r'装置[^。；;]{0,70}?附在药品包装中[^。；;]{0,15}?(?:以)?避免难以获得装置',x):
            if not _carrier_only(m.group()):
                v.add('V27_F_dosing_device_access','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
        for m in re.finditer(r'根据(?:药品临床综合)?评价需要[^。；;]{0,75}?药品生产[、,，]供应相关(?:情况|状况|信息|数据)',x):
            if not _carrier_only(m.group()):
                for p,prefix in v.paragraph_prefixes():
                    antecedent=_norm(prefix)
                    if re.search(r'可获得性[^。；;]{0,65}?(?:药品配备|药品供应|短缺)',antecedent):
                        v.add('V27_F_drug_supply_evaluation_information','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F,
                              dependency=v.dependency(p,'same_paragraph_access_evaluation',antecedent))
                        break
        for m in re.finditer(r'治疗手段的可及性[^。；;]{0,100}?药物的效果',x):
            v.add('V27_F_treatment_access_factor','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
        for pattern in (r'药品目录[^。；;]{0,130}?保障更加公平可及',
                        r'医保药品保障水平[^。；;]{0,45}?缓解用药难',
                        r'商保创新药目录内药品享受[^。；;]{0,65}?不计入基本医保自费率指标',
                        r'复杂给药方式[^。；;]{0,70}?指导患者用药',
                        r'培训教育[^。；;]{0,75}?不能完全满足合理用药及正确操作',
                        r'复杂给药方式[^。；;]{0,70}?照护者辅助方式[^。；;]{0,60}?自我给药'):
            for m in re.finditer(pattern,x):
                if re.search(r'复杂给药|培训教育',m.group()):
                    subtype='clinical_management'
                else:
                    subtype='access'
                v.add('V27_F_drug_access_or_use_relation','F',s.start()+m.start(),s.start()+m.end(),subtype,BASIS_F)
        for m in re.finditer(r'药品费用[，,][^。；;]{0,35}?由基本医疗保险基金支付',x):
            v.add('V27_F_drug_fund_payment','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
    for s in re.finditer(r'[^。；;]+',v.normalized):
        for m in re.finditer(r'(?:该|竞价|谈判|续约)?药品(?:通用名)?[^。；;，,]{0,35}?不被纳入《(?:国家)?药品目录》',s.group()):
            v.add('V27_F_quoted_directory_membership','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
        for m in re.finditer(r'定点医疗机构根据《药品目录》调整结果[^。；;]{0,30}?对本医疗机构用药目录进行调整',s.group()):
            v.add('V27_F_facility_drug_stocking_link','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
    # Explicit treatment opportunity for a pre-existing access gap. This
    # grammar binds the gap's patient group to the following drug arrangement;
    # receiving trial drugs in ordinary participation is not sufficient.
    for s in v.sentences():
        for m in re.finditer(r'(?:患者|人群)(?:仍)?(?:未能|无法|不能)(?:得到|获得)有效治疗[,，](?:因此|为此)?(?:该药|本药|研究药物|试验药物)(?:为其|可|能够)?(?:提供|带来)(?:治疗机会|治疗选择)|(?:对|为)(?:原本)?(?:无法|不能|未能)获得治疗的患者[,，]?(?:提供|给予)(?:研究药物|试验药物|药物治疗)',s.group()):
            v.add('V27_F_gap_linked_treatment_opportunity','F',s.start()+m.start(),s.start()+m.end(),'access',BASIS_F)
    # Innovation qualification: current comparative content plus explicit
    # current eligibility anchors. A named existing status is not eligibility.
    parents=v.record.get('verified_parent_context',[])
    governing=[]
    for p in parents:
        x=_norm(p['text'])
        if (re.search(r'突破性治疗药物程序',x)
                and (re.search(r'(?:申请适用|申请纳入)[^。；;]*(?:条件|要求|适用范围)',x)
                     or re.search(r'(?:不再符合|不符合|满足|符合)[^。；;]*纳入条件',x)
                     or re.search(r'(?:以下|下列)(?:任一)?情形[^。；;]*终止突破性治疗药物程序',x))
                and not re.search(r'优先审评|参照.*突破性治疗',x)):
            governing.append(p)
    if any(re.search(r'优先审评|参照.*突破性治疗',_norm(p['text'])) for p in parents):
        governing=[]
    explicit_parent_object=any(re.search(r'创新药|改良型新药|创新(?:性)?药物',_norm(p['text'])) for p in governing)
    if governing and not (explicit_parent_object or innovation_scope):
        _flag(v,'V27_I_qualification_two_anchors','verified_parent_has_program_but_innovation_object_anchor_missing')
        governing=[]
    for s in v.sentences():
        x=s.group()
        current_anchor=bool(re.search(r'创新药|改良型新药',x) and re.search(r'申请(?:适用|纳入)突破性治疗药物程序',x))
        cross=bool(re.search(r'优先审评|参照[^。；;]*突破性治疗',x))
        if not (governing or current_anchor) or cross:
            continue
        pattern=r'(?:与现有治疗手段相比[^。；;]*?)?明显临床优势|尚无有效(?:防治|治疗)手段|(?:较|比|相比|对比)[^。；;，,]*(?:显著|更|改善)[^。；;，,]*(?:疗效|治疗效果|临床获益|临床结局|应答|生存)|(?:显著|更显著|更重要的)(?:或者更重要的|的|临床意义的)?(?:疗效|治疗效果|临床获益|安全性优势|临床结局)|(?:终点上|临床结局上)(?:有|具有)?显著改善'
        # Explicit current content reference to the comparative standard also
        # counts; pure status/timing/revocation without reason does not.
        pattern+=r'|(?:符合|满足|达到|不符合|不再满足|未达到)[^。；;，,]*(?:明显临床优势|临床比较优势)(?:要求|标准|条件)?'
        for m in re.finditer(pattern,x):
            local=next((p.group() for p in _parts(x) if p.start()<=m.end()-1<p.end()),x)
            if _carrier_only(local) or _disclosure_only(local) or (_disclosure_only(x) and not _content_action(local)):
                continue
            dep=None
            if governing:
                dep=v.dependency(governing[0],'verified_current_innovation_qualification',_norm(governing[0]['text']))
                dep['governing_paragraph_ids']=[p.get('paragraph_id') for p in parents]
                if innovation_scope and not explicit_parent_object:
                    dep['innovation_object_scope']=innovation_scope
            v.add('V27_I_qualification_two_anchors','I',s.start()+m.start(),s.start()+m.end(),'qualification_advantage',BASIS_I,dependency=dep)
    # Anaphors must bind the nearest same-paragraph predecessor. Parent scope
    # alone cannot turn '上述义务' into all the parent's dimension claims.
    for p,prefix in v.paragraph_prefixes():
        pred=[m.group().strip() for m in re.finditer(r'[^。]+',_norm(prefix)) if m.group().strip()]
        if not pred: continue
        antecedent=pred[-1]
        if len(pred)>1 and re.match(r'包括|其中|具体包括|并',antecedent) and not re.search(r'财务审计|另行|其他事项',antecedent):
            antecedent='。'.join(pred[-2:])
        if re.search(r'保障[^。]*药品供应|药品[^。]*保障供应',antecedent):
            for m in re.finditer(r'(?:相应|上述)(?:要求|义务)[^。；;]*(?:协议|约定)[^。；;]*(?:明确|落实|约定)',v.text):
                if not re.search(r'另行|其他事项|财务审计',m.group()):
                    v.add('V27_F_obligation_reference','F',m.start(),m.end(),'access',BASIS_F,dependency=v.dependency(p,'same_paragraph_explicit_supply_obligation',antecedent))
        if re.search(r'可获得性[^。]*药品配备|药物可及性[^。]*可获得性',antecedent):
            for m in re.finditer(r'(?:根据|为满足)评价需要[^。；;]*药品生产[、,，]?供应(?:相关)?信息',v.text):
                v.add('V27_F_access_information_reference','F',m.start(),m.end(),'access',BASIS_F,dependency=v.dependency(p,'same_paragraph_access_evaluation',antecedent))
        if re.search(r'不同药物[^。]*不同时间服用|不同(?:的)?给药途径|多种药物同时使用',antecedent):
            for m in re.finditer(r'此类用药行为[^。；;]*(?:多病共存|多重用药)[^。；;]*问题',v.text):
                v.add('V27_F_management_anaphor','F',m.start(),m.end(),'clinical_management',BASIS_F,dependency=v.dependency(p,'same_paragraph_specific_drug_use_complexity',antecedent))


def revise(record,result):
    """Replace audited I/F evidence; caller alone rebuilds label fields."""
    if result.get('judgement_status')=='undetermined':
        return result
    v=RuleView(record,result)
    innovation_scope=_verified_innovation_scope(v)
    # Recompute the complete dimensions so a broad inherited match cannot
    # bypass new object/title/carrier constraints. Preserve an audit trail.
    v.drop(lambda e:e['dimension'] in {'I','F'},'V27_IF_local_reassessment',
           '以v1.3全部I/F语义组重新核对对象、当前内容和局部排除；旧证据不直接继承。')
    for p in _parts(v.text):
        _innovation(v,p)
        _fairness(v,p)
    _linked_relations(v,innovation_scope)
    return result
