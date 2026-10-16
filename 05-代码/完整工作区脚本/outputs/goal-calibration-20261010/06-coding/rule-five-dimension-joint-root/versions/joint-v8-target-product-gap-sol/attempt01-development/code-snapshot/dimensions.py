# ROOT five-dimensional joint developer candidate; no cohort release or formal acceptance.
"""Five construct predicates for the common v1.3F frozen manual.

Only current text and legally linked source quotations enter judgement.  IDs,
hashes, paths, departments, earlier labels and performance measures are never
features.  This module performs no I/O and does not load the development fixture.
Words nominate candidates; every positive is justified by a content relation.
"""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any
from evidence import make_decision
DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')
MATERIAL_REQUEST_CONSUMERS = {'substantive_list': DIMENSIONS, 'cited_standard': DIMENSIONS, 'named_mechanism': ('I', 'F'), 'parent_predicate': ('I', 'F'), 'price_arrangement': ('Ec',)}
REQUEST_ROUTING_VERSION = 'relation-consumer-routing-3-local-parent-origin-conflict'

class MaterialRequestRoutingError(ValueError):
    """An unresolved request without an exact consumer route is technical failure."""

def _material_request_route(request):
    if not isinstance(request, dict):
        raise MaterialRequestRoutingError('material request must be a concrete object')
    for key in ('path', 'reference', 'missing'):
        if not isinstance(request.get(key), str) or not request[key].strip():
            raise MaterialRequestRoutingError('material request lacks concrete ' + key)
    path = request['path']
    if path not in MATERIAL_REQUEST_CONSUMERS:
        raise MaterialRequestRoutingError('unallocated material request path: ' + path)
    if request.get('status', 'unresolved') != 'unresolved' or request.get('dependency_status', 'stopped') != 'stopped' or request.get('necessary_dependency', True) is not True:
        raise MaterialRequestRoutingError('material request is not a necessary unresolved dependency')
    consumers = MATERIAL_REQUEST_CONSUMERS[path]
    declared = []
    for key in ('dimensions', 'affected_dimensions'):
        if key not in request:
            continue
        dims = request[key]
        if not isinstance(dims, list) or not dims or any((not isinstance(dim, str) or dim not in consumers for dim in dims)) or (len(set(dims)) != len(dims)):
            raise MaterialRequestRoutingError('invalid material request ' + key)
        declared.append(tuple((dim for dim in DIMENSIONS if dim in dims)))
    if len(declared) == 2 and declared[0] != declared[1]:
        raise MaterialRequestRoutingError('conflicting material request dimension declarations')
    dims = declared[0] if declared else consumers
    return {'version': REQUEST_ROUTING_VERSION, 'request': request, 'relation_kind': path, 'dimensions': list(dims), 'basis': 'validated_explicit_consumer_subset' if declared else 'closed_relation_consumer_contract', 'necessary_dependency_unresolved': True, 'absent_source_topics_inferred': False}
MANUAL = {'S': '共同冻结手册5ea7ab74（未改变定义） §一、§二、§三', 'E': '共同冻结手册5ea7ab74（未改变定义） §一、§二、§四', 'Ec': '共同冻结手册5ea7ab74（未改变定义） §一、§二、§五', 'I': '共同冻结手册5ea7ab74（未改变定义） §一、§二、§六、§九', 'F': '共同冻结手册5ea7ab74（未改变定义） §一、§二、§七'}
DRUG = '药品|药物|用药|给药|制剂|片剂|胶囊|药费|新药|化学药|生物制品|中药|该药|本药|研究药|试验药|治疗药'
CONTENT_ACTION = '评价|评估|比较|分析|研判|量化|分级|考察|测算|说明|描述|提供|提交|补充|报告|收集|核实|核对|确认|验证|证明|关注|讨论|要求|应包括|内容涉及'
FORM = '字段[^。；;，,]{0,18}(?:不能为空|不得为空|非空|已填|填写完整)|(?:字符|文件|材料|字段|数据)(?:的)?格式|(?:签字|签章|盖章|账号|命名|归档|上传时间|递交时间|截止日期|截止时间)'
PURE_STRUCTURE = re.compile('^\\s*(?:[（(]?[一二三四五六七八九十0-9]+[）)、.．]?\\s*)?(?:如下|具体如下|包括以下内容|包括下列内容|包括以下|包括下列|具体包括|下列条件|以下条件|适用范围|申请资格|申请条件|申报流程|安全性|有效性|经济性|创新性|公平性)[:：]?\\s*$')
TOPICS = {'S': '安全性|用药安全|安全用药|药物风险|用药风险|不良反应|不良事件|毒性|毒理|肝损伤|禁忌|相互作用|药物警戒|用药差错|用药错误|风险管理|风险评估|风险识别|过敏史', 'E': '有效性|疗效|治疗效果|防治效果|临床获益|健康收益|健康获益|生存(?:期|率|获益)?|生命质量|生活质量|临床优势|疾病控制|有效(?:防治|治疗)(?:手段|药物|选择|选项)|药效|主要终点|药物作用反应|整体健康水平', 'Ec': '经济性|药价|药品价格|价格|药费|费用|成本|成本效果|成本效用|支付标准|支付范围|支付责任|报销|自付|基金支出|基金预算|预算影响|基金承受能力|基金(?:运行)?安全(?:为|作为)(?:底线|前提|约束)|支付资源|资源约束|按病种付费|DRG|DIP|销售金额|下调比例|降幅|供应成本', 'I': '创新性|创新点|创新程度|创新价值|原创|新颖|新作用机制|新靶点|新化合物|新分子实体|改良|改进|优化|创新药|首创新药|注册分类|[1-5一二三四五]类(?:化学药|治疗用生物制品|预防用生物制品|中药)|研发|研制|数据保护|市场独占', 'F': '公平|可及|可获得|可负担|负担不起|无力支付|买不起|治疗需要|用药需求|短缺|尚无有效|尚无药物获批|未满足|保障缺口|保障空白|断供|供应不稳定|配送|临床管理|吞咽|给药便利|目录|处方流转|雪中送炭|锦上添花'}
NONDIM = {'S': '基金安全|网络安全|信息安全|数据安全|一般生产安全|消防安全|办公安全', 'E': '账号有效期|协议有效期|文件有效期|数据有效性|格式有效|行政效能|审批效能|审评审批效能', 'Ec': '科研(?:项目)?经费|研究经费|设备采购(?:费|成本)?|行政收费|办公(?:费用|成本)', 'I': '管理创新|制度创新|企业创新能力|产业创新发展|新质生产力', 'F': '企业竞争公平|公平竞争|廉政风险|利益冲突|工作纪律|程序公平|程序公正'}
INNOVATION_OBJECT = '创新药(?:物)?|创新型药物|创新(?:型)?(?:疫苗|生物制品)|改良型新药|首创新药|源头性创新[^。；;]{0,12}药物|药物创新|药品创新'
SUPPORT = '资金|经费|研发资源|研究资源|审评资源|数据服务|数据产品|技术服务|技术培训|人员培训|专门审评团队|审评团队|审评人员|研究方案反馈|方案反馈|提出意见|提出建议|技术指导|支持机会|申请机会|研发便利|优先审评|加快通道|单独序列管理|缩短[^。；;]{0,12}(?:启动|审评)|(?:研究|试验|研发)(?:方案|设计)[^。；;]{0,15}(?:反馈|意见|建议)'
SUPPORT_ACTION = '设立|建立|安排|组建|配置|提供|给予|开放|允许|可以|可申请|申请适用|纳入|组织开展|组织实施|实施|开展|开发|终止|停止|取消|撤回|不再|不予|不得|禁止|不可|不能|限制|不适用|同意'
PAYMENT_CONTENT = '支付标准|支付范围|支付责任|药品价格|药价|药费|治疗费用|药品费用|基金支出|基金预算|预算增幅|下调比例|降幅|成本|费用|报销|自付|销售金额'
PAYMENT_ACTION = '制定|确定|调整|下调|上调|计算|测算|评价|分析|说明|确认|核对|核验|验证|提供|承担|支付|补偿|报销|限制|允许|可申请|方可|须申报|不超过|超过|不低于|降价|降低|控制|变化|负担'
OPPORTUNITY = '优先[^。；;，,]{0,15}(?:研究方案反馈|试验方案反馈|技术反馈|技术沟通|技术咨询)|优先审评|优先配置|优先保障|优先支持|针对性支持|可申请|可以申请|申请适用|申请加入|申请[^。；;]{0,15}(?:试点|支持|程序)|治疗机会|保障安排|资源配置|资源分配|补偿|援助|填补|弥补|保证[^。；;]{0,12}所需|保障[^。；;]{0,12}所需'
MODIFICATION_CHANGE = '(?:改善|改良|改进|优化|改变|设计|开发)[^。；;]{0,25}(?:片剂|剂型|强度|给药途径|给药频次|释放|结构|包装|装置|口崩|掰断)|(?:片剂|剂型|给药途径|给药频次|释放|结构|包装|装置)[^。；;]{0,15}(?:改善|改良|改进|优化)'
TECHNICAL_QUALIFICATION = '新作用机制|新靶点|新化合物|新分子实体|原创(?:性)?|新颖(?:性)?|原始创新|实质改良|实质改进|(?:与|相较|较)[^。；;，,]{0,30}(?:现有|已有|既有|对照|原有)[^。；;，,]{0,35}(?:临床优势|临床获益|疗效优势|治疗优势|安全性优势)|(?:现有|已有|既有|对照|原有)[^。；;，,]{0,20}(?:相比|比较)[^。；;，,]{0,30}(?:临床优势|临床获益|疗效优势|治疗优势|安全性优势)'
QUALIFICATION_CONSEQUENCE = '(?:可|可以|允许|不得|不予|不再)[^。；;，,]{0,12}申请[^。；;]{0,30}(?:支持|反馈|优先|试点|程序|计划|机会|通道)|申请(?:适用|加入)[^。；;]{0,30}(?:支持|反馈|试点|程序|计划|通道)|(?:授予|给予|开放|终止|取消|撤回|限制|维持)[^。；;]{0,25}(?:支持机会|支持|待遇|权利|保护|准入|申请资格)|(?:支持|待遇|权利|保护|准入)[^。；;]{0,15}(?:终止|取消|撤回|限制|维持)'
PAYMENT_MODE = '按病种付费|按疾病诊断(?:相关)?分组付费|DRG|DIP'
ACTUAL_ALLOCATION = '(?:提供|不再提供|撤回|终止)[^。；;，,]{0,20}优先[^。；;，,]{0,20}(?:反馈|沟通|咨询)|(?:安排|配置|给予|予以|实行|实施|允许|开放|应当|可以|可)[^。；;，,]{0,25}(?:优先审评|优先保障|优先配置|优先支持|资源|资金|技术服务|反馈|支持机会|申请机会)|(?:可|可以|允许|不得|不予|不再)[^。；;，,]{0,8}申请|(?:直接|应当|可以|可|不得|不予|不再)(?:予以)?纳入[^。；;，,]{0,18}(?:优先审评|优先保障|优先配置|优先支持)|(?:可|可以|允许|不得|不予|不再)(?:在|于)[^。；;]{0,120}申请(?:适用|加入|优先|技术支持|研发支持|研究反馈|临床急需)'
GAPS = {'no_effective_option': '(?:尚无|没有|不存在)有效(?:防治|治疗)(?:手段|药物|选择|选项)|(?:尚无|没有|已无)(?:标准|有效|可用)治疗(?:可供选择|选择|手段|方案|药物)', 'no_domestic_approved_option': '境内[^。；;]{0,12}(?:尚无|没有)药物获批(?:用于|治疗)[^。；;]{0,15}(?:疾病|适应症)|境内[^。；;]{0,12}尚无药物获批[^。；;]{0,20}适应症|境内(?:无|尚无|未有)[^。；;]{0,12}获批[^。；;]{0,15}(?:药物|治疗选项)', 'supply_gap': '临床急需[^。；;]{0,12}短缺药品|药品(?:供应)?短缺|供药不足|药品供应不足|供应不稳定|时常断供|药品断供|药物断供|供药中断'}

@dataclass
class Unit:
    text: str
    a: int
    b: int
    contexts: list[dict] = field(default_factory=list)
    kind: str = 'current'
    details: dict = field(default_factory=dict)
    inherited: str = ''

def _hits(pattern: str, text: str):
    return list(re.finditer(pattern, text))

def _literal(anchor: Any) -> str:
    if isinstance(anchor, str):
        return anchor
    if isinstance(anchor, dict):
        return str(anchor.get('text', anchor.get('quote', '')))
    return ''

def _norm(text: str) -> str:
    return re.sub('\\s+', '', unicodedata.normalize('NFKC', text))

def _context_text(unit: Unit) -> str:
    return '。'.join((_norm(_literal(c)) for c in unit.contexts if _literal(c)))

def _document_name_only(text: str, dimension: str) -> bool:
    """Identify the named-file role, not negation of a drug property.

    An independent substantive clause survives. Denial of inference from a
    filename is not an evaluation request and cannot donate its action verb.
    """
    if not re.search('文件名|附件名|文件名称|附件名称|栏目[^。；;]{0,20}(?:名称|文件名)|标题', text):
        return False
    content = text
    for match in reversed(list(re.finditer('《[^》]+》|“[^”]+”|"[^"]+"', text))):
        before = text[max(0, match.start()-24):match.start()]
        if re.search('(?:文件|附件|材料)?(?:名称|文件名|附件名|标题)(?:为|是|[:：])?$', before):
            content = content[:match.start()] + ' ' + content[match.end():]
    candidates = []
    for part in re.findall('[^，,。；;]+', content):
        if not re.search(TOPICS[dimension], part):
            continue
        nominal = re.search('(?:仅|只)(?:用作|作为|用于)[^。；;]{0,20}(?:文件名|附件名|标题)|(?:文件|附件|材料)?(?:名称|文件名|附件名|标题)(?:为|是|[:：])', part)
        denied_inference = re.search('(?:不据|不从|不得[^。；;]{0,6}从|不能[^。；;]{0,6}从)[^。；;]{0,20}(?:名称|文件名|附件名|标题)[^。；;]{0,12}(?:推定|推断|认定|判断)', part)
        if not (nominal or denied_inference):
            candidates.append(part)
    return bool(re.search(TOPICS[dimension], text)) and not candidates

def _form_only(text: str, dimension: str) -> bool:
    if _document_name_only(text, dimension):
        return True
    if not re.search(FORM, text):
        return False
    candidates = [p for p in re.split('[，,]|或者|或(?=申报|字段|材料|文件|格式)', text) if re.search(TOPICS[dimension], p)]
    if any((not re.search(FORM, part) for part in candidates)):
        return False
    content = f'(?:评价|评估|比较|分析|说明|核对|核验|确认|验证|补充|提供)[^。；;，,]{{0,20}}(?:{TOPICS[dimension]})'
    action = re.search(content, text)
    return action is None or bool(re.search('字段|格式|签章|签字|盖章', action.group()))

def _drug_safety_standard(text: str):
    """An actual criterion-setting action with drug risk and its test content."""
    return re.search('(?:制定|规定|确定|采用|执行|应当|须|必须)[^《》。；;，,]{0,20}(?:' + DRUG + ')[^《》。；;，,]{0,20}(?:风险|安全性|不良反应|毒性|毒理|禁忌|相互作用)[^《》。；;，,]{0,12}(?:评价|评估|监测|检验|检测|审核)[^《》。；;，,]{0,18}(?:标准|要求|指标|阈值|判据)', text)

def _publication_content_spans(text: str):
    """Return independent current content, or None for a non-enactment clause.

    Numbering is only stripped to locate the proposition; it never excludes a
    substantive clause. Purpose words without an actual document enactment are
    outside this boundary. Exact span offsets retain the full original record
    as current_proposition while nominating only its operative content.
    """
    prefix = '(?:第[零〇一二两三四五六七八九十百千0-9]+条(?:第[零〇一二两三四五六七八九十百千0-9]+款)?|[（(]?[一二三四五六七八九十0-9]+[）)、.．])?'
    if not re.match('^\\s*' + prefix + '\\s*(?:为了|为)', text):
        return None
    document_kind = '指导原则|办法|程序|方案|规则|指南|规范|规定|规程|文件|通知|意见|细则|标准'
    document = '《[^《》。；;，,]{0,80}(?:' + document_kind + ')[^《》。；;，,]{0,12}》|(?:本|该)[^《》。；;，,]{0,40}?(?:' + document_kind + ')|[^《》。；;，,]{1,60}?(?:' + document_kind + ')'
    publication = re.search('(?:特)?(?:制定|印发|发布)(?:' + document + ')', text)
    if not publication:
        return None
    spans = []
    for part in re.finditer('[^，,。；;]+', text[:publication.start()]):
        s = part.group()
        requirement = re.search('(?:应当|应|须|必须|不得|禁止|要求|需要|需)[^。；;]{0,35}(?:' + CONTENT_ACTION + '|审核|监测|控制|拒绝|调配|限制|配置|给予|开放)', s)
        problem = re.search('(?:' + DRUG + ')[^。；;]{0,25}(?:导致|造成|存在|发生)[^。；;]{0,25}(?:风险|不良反应|损伤|缺口|障碍|费用|成本|疗效|治疗效果)', s)
        enacted_action = re.search('(?:决定|同意|批准)(?:组织)?(?:开展|实施|设立|建立|开放|组建|配置|提供|给予)[^。；;]+', s)
        if requirement or problem or enacted_action or re.search(ACTUAL_ALLOCATION, s) or _drug_safety_standard(s):
            spans.append((part.start(), part.end()))
    if _drug_safety_standard(publication.group()):
        spans.append(publication.span())
    for part in re.finditer('[^，,。；;]+', text[publication.end():]):
        spans.append((publication.end() + part.start(), publication.end() + part.end()))
    return spans

def _publication_purpose(text: str) -> bool:
    return _publication_content_spans(text) == []

def _substantive(text: str, dimension: str) -> bool:
    if _form_only(text, dimension) or PURE_STRUCTURE.fullmatch(text):
        return False
    if re.search(CONTENT_ACTION, text):
        return True
    if dimension == 'S':
        return bool(re.search('导致|造成|减少|预防|控制|识别|监测|管理|警戒|不良反应|毒性|毒理|禁忌|用药差错|过敏史', text))
    if dimension == 'E':
        return bool(re.search('改善|提高|提升|获益|优势|不足|尚无有效|没有有效|疗效|治疗效果|防治效果|疾病控制', text))
    if dimension == 'Ec':
        return bool(re.search(PAYMENT_ACTION, text))
    if dimension == 'I':
        return bool(re.search('具有|具备|缺乏|不同于|新作用机制|新靶点|新颖|原创|改良|改善|改进|设立|组建|提供|实施|开展|申请|续约|谈判|给予', text))
    return bool(re.search('负担不起|无力支付|买不起|可负担|不能获得|无法获得|难以获得|不平衡|差异|限制|保障|优先|申请|改善|优化', text))

def _payment_route_only(text: str) -> bool:
    """A current option routing action does not change its drug subject's payment.

    This is a proposition boundary, not a ban on selection/application words.
    Substantive payment selection, content checking, or authorization survives.
    A caller may include an actually direct parent payment-consequence predicate.
    """
    route = re.search('(?:选择|勾选|选用|填报|填写|进入)[^。；;，,]{0,20}(?:申报|申请)(?:条件|类别|模块|选项|渠道)|(?:申报|申请)(?:时|应|须)[^。；;，,]{0,15}(?:选择|勾选)[^。；;，,]{0,15}(?:条件|类别|模块|选项)', text)
    if not route:
        return False
    content_action = '核验|核对|确认|说明(?!书)|提供|提交|补充|评价|评估|比较|分析|测算|计算|制定|确定|承担|报销|补偿|控制|降低'
    actual_content = re.search(f'(?:{content_action})[^。；;，,]{{0,20}}(?:{PAYMENT_CONTENT})|(?:{PAYMENT_CONTENT})[^。；;，,]{{0,20}}(?:{content_action})', text) or re.search('明确(?:药品|药物|治疗|用药|该药|本药)?(?:的)?(?:预算|费用)', text)
    authorization = re.search(f'(?:可(?:以)?|允许|准许|不得|不能|方可|才能)[^。；;，,]{{0,18}}(?:调整|变更|制定|确定)[^。；;，,]{{0,18}}(?:{PAYMENT_CONTENT})', text)
    payment_selection = re.search(f'(?:选择|选用|适用)[^。；;，,]{{0,15}}(?:{PAYMENT_CONTENT})', text)
    return not (actual_content or authorization or payment_selection)

def _non_drug_validity_spans(text: str):
    """Local noun→validity binding; a drug mentioned earlier is not its target."""
    nominal_target = '注册证书|证书|文书|文件|资料|材料|数据|记录|字段|账号|账户|协议'
    return list(re.finditer(f'(?:{nominal_target})(?:的|本身的|自身的)?有效性', text))

def _current_overall_health_effect(text: str) -> bool:
    """Require a current drug-effect relation for a broad overall-health phrase.

    General product-design/experience goals and baseline patient descriptions
    are not independent efficacy claims. Uncertain, negative or prospective
    drug-effect claims and explicit effect-evaluation requirements remain in.
    """
    if '整体健康水平' not in text:
        return False
    for part in re.findall('[^，,。；;]+', text):
        if '整体健康水平' not in part:
            continue
        baseline_only = re.search('入组前|治疗前|给药前|基线', part) and (not re.search('治疗前后|给药前后|治疗后|给药后|用药后|服药后', part))
        if baseline_only:
            continue
        direct = re.search('(?:该药|本品|这种药物|该药物|药物治疗|药物|该治疗(?:方案)?)(?P<bridge>[^，,。；;]{0,25}?)(?:改善|提升|提高|降低|减少)[^，,。；;]{0,25}整体健康水平', part)
        if direct and (not re.search('研发|开发|设计|体验|偏好', direct.group('bridge'))):
            return True
        assessment = re.search('(?:评价|评估|比较|验证|确认|核实|测量)[^，,。；;]{0,20}(?:该药|本品|药物|该治疗|治疗前后|给药前后|治疗后|给药后)[^，,。；;]{0,35}整体健康水平', part)
        if assessment and re.search('影响|变化|改善|提高|提升|效果|差异', part) and (not re.search('研发|开发|设计|体验|偏好', assessment.group())):
            return True
        if re.search('治疗前后|给药前后|治疗后|给药后|用药后|服药后', part) and re.search('整体健康水平[^，,。；;]{0,10}(?:变化|改善|提高|提升|差异)|(?:改善|提高|提升)[^，,。；;]{0,25}整体健康水平', part):
            return True
    return False

def _drug_effectiveness_topic(text: str) -> bool:
    administrative = _non_drug_validity_spans(text)
    return any((not any((span.start() <= topic.start() and topic.end() <= span.end() for span in administrative)) for topic in re.finditer('有效性', text)))

def _drug_content_determination(text: str, topic: str):
    pattern = f'(?:确定|探明|查明|判明|判断)[^。；;，,]{{0,12}}(?:{DRUG})(?P<target_gap>[^。；;，,]{{0,12}}){topic}'
    non_drug_target = '注册(?:证书|文件|资料|记录)|证书|文书|文件|资料|材料|数据|记录|字段|账号|账户|协议'
    for match in re.finditer(pattern, text):
        if re.search(non_drug_target, match.group('target_gap')):
            continue
        if topic == '有效性' and any((span.start() < match.end() and span.end() >= match.end() for span in _non_drug_validity_spans(text))):
            continue
        return match
    return None

def _object(view, unit: Unit) -> dict:
    obj = view.object_evidence(unit.a, unit.b)
    if not isinstance(obj, dict):
        raise TypeError('RelationView.object_evidence must return its source evidence')
    if obj.get('established'):
        return obj
    text = unit.text + '。' + unit.inherited + '。' + _context_text(unit)
    if unit.kind != 'current' and re.search(DRUG, text):
        return {'established': True, 'current_anchors': [], 'context_evidence': unit.contexts, 'object_text': text, 'role': 'legally_linked_drug_object', 'reason': '对象由当前关系实际使用的来源引文补足。'}
    return obj

def _unique_contexts(items: list[dict]) -> list[dict]:
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out

def _verified_source_quote_identity(view, quote):
    """Exact original range identity; a shared leaf ID alone is not a boundary."""
    if not isinstance(quote, dict):
        return None
    matches=[c for c in view.contexts if c.get('context_id')==quote.get('context_id')]
    if len(matches)!=1:
        return None
    c=matches[0];a,b=quote.get('start'),quote.get('end')
    if type(a) is not int or type(b) is not int or not 0<=a<b<=len(c.get('text','')):
        return None
    if quote.get('text')!=c['text'][a:b] or quote.get('source_ref')!=c.get('source_ref'):
        return None
    return (quote['context_id'],a,b,quote['text'],quote['source_ref'])

def _units(view) -> list[Unit]:
    if _publication_purpose(view.norm):
        return []
    units = []
    for m in re.finditer('[^。；;]+', view.norm):
        text = _norm(m.group())
        spans = _publication_content_spans(text)
        if spans is None:
            units.append(Unit(text, m.start(), m.end()))
        else:
            units.extend((Unit(text[a:b], m.start() + a, m.start() + b) for a, b in spans))
    for kind in ('parent_predicate', 'substantive_list', 'cited_standard', 'named_mechanism', 'policy_explanation', 'price_arrangement'):
        for rel in view.linked(kind):
            details = dict(rel.get('details') or {})
            anchor = rel.get('current_anchor') or {}
            a = anchor.get('norm_start', details.get('norm_start', 0))
            b = anchor.get('norm_end', details.get('norm_end', len(view.norm)))
            if not isinstance(a, int) or not isinstance(b, int) or (not 0 <= a < b <= len(view.norm)):
                a, b = (0, len(view.norm))
            contexts = rel.get('context_evidence') or []
            current = view.norm[a:b]
            spans = _publication_content_spans(current)
            current_parts = [(0, len(current))] if spans is None else spans
            for start, end in current_parts:
                operative = current[start:end]
                if kind == 'parent_predicate':
                    governing = _norm(details.get('shared_predicate') or details.get('content') or '。'.join((_literal(c) for c in contexts)))
                    units.append(Unit(operative, a + start, a + end, contexts, kind, details, governing))
                elif kind in {'substantive_list', 'cited_standard'}:
                    for ctx in contexts:
                        proof = details.get('closure_proof', {})
                        proof_only = proof.get('boundary_quotes', []) + proof.get('identity_quotes', []) + proof.get('proof_only_quotes', [])
                        same_source_quotes = [q for q in proof_only if q.get('context_id') == ctx.get('context_id')]
                        if same_source_quotes:
                            actual = _verified_source_quote_identity(view, ctx)
                            keys = [_verified_source_quote_identity(view,q) for q in same_source_quotes]
                            if actual is None or any(key is None for key in keys):
                                scope=set(details.get('affected_dimensions',DIMENSIONS))
                                if details.get('only_IF_consumers'):scope &= {'I','F'}
                                if scope:view.material_requests.append({'path':kind,'reference':view.text,'missing':'标准内容/仅作边界的引文缺少一致精确源区间，不能按不同text放行','dimensions':sorted(scope),'request_kind':'quote_scope_conflict'})
                                continue
                            if any(actual == key for key in keys):
                                continue
                            if any(actual[1] < key[2] and key[1] < actual[2] for key in keys):
                                scope=set(details.get('affected_dimensions',DIMENSIONS))
                                if details.get('only_IF_consumers'):scope &= {'I','F'}
                                if scope:view.material_requests.append({'path':kind,'reference':view.text,'missing':'所供实质标准引文与实际仅作边界/身份的原文区间重叠，须核正有限消费范围','dimensions':sorted(scope),'request_kind':'quote_scope_conflict'})
                                continue
                        content = _norm(_literal(ctx))
                        content_spans = _publication_content_spans(content)
                        parts = [(0, len(content))] if content_spans is None else content_spans
                        for left, right in parts:
                            if content[left:right]:
                                units.append(Unit(content[left:right], a + start, a + end, contexts if details.get('SE_scope_verified') else [ctx], kind, details, operative))
                else:
                    units.append(Unit(operative, a + start, a + end, contexts, kind, details, _norm(details.get('content') or '。'.join((_literal(c) for c in contexts)))))
    return units

class Accumulator:

    def __init__(self, view):
        self.view = view
        self.positive = {d: [] for d in DIMENSIONS}
        self.excluded = {d: [] for d in DIMENSIONS}
        self.material = {d: [] for d in DIMENSIONS}
        self.material_routes = {d: [] for d in DIMENSIONS}
        self.errors = {d: [] for d in DIMENSIONS}
        self.boundaries = {d: [] for d in DIMENSIONS}

    def boundary(self, dim, unit, reference, issue):
        request = {'reference': reference, 'missing': issue, 'request_kind': 'unresolved_manual_relation_boundary', 'current_proposition': self.view.proposition(unit.a, unit.b), 'context_evidence': unit.contexts, 'not_missing_source_claim': True}
        if request not in self.boundaries[dim]:
            self.boundaries[dim].append(request)

    def exclude(self, dim, unit, reason):
        if re.search(TOPICS[dim], unit.text) and reason not in self.excluded[dim]:
            self.excluded[dim].append(reason)

    def add(self, dim, unit, path, reason, obj, details=None):
        ce = _unique_contexts(unit.contexts + list(obj.get('context_evidence') or []))
        record = {'basis_path': path, 'current_anchor': self.view.current_anchor(unit.a, unit.b), 'current_proposition': self.view.proposition(unit.a, unit.b), 'context_evidence': ce, 'reason': reason, 'details': {'manual': MANUAL[dim], 'relation_kind': unit.kind, 'object_evidence': obj, **(details or {})}}
        if record not in self.positive[dim]:
            self.positive[dim].append(record)

    def request(self, dim, reason):
        if reason not in self.material[dim]:
            self.material[dim].append(reason)

    def error(self, dim, reason):
        if reason not in self.errors[dim]:
            self.errors[dim].append(reason)

    def finish(self):
        for request in getattr(self.view, 'material_requests', []):
            route = _material_request_route(request)
            for dim in route['dimensions']:
                self.request(dim, request)
                if route not in self.material_routes[dim]:
                    self.material_routes[dim].append(route)
        for error in getattr(self.view, 'implementation_errors', []):
            dims = error.get('dimensions', DIMENSIONS) if isinstance(error, dict) else DIMENSIONS
            for dim in dims:
                if dim in self.errors:
                    self.error(dim, error)
        failures = {d: errors for d, errors in self.errors.items() if errors}
        if failures:
            raise ValueError('implementation_error: ' + repr(failures))
        out = {}
        for dim in DIMENSIONS:
            positives = self.positive[dim]
            if positives:
                first = positives[0]
                details = dict(first['details'])
                details['additional_evidence'] = positives[1:]
                details['near_candidate_exclusions'] = self.excluded[dim]
                details['unresolved_material_requests'] = self.material[dim]
                details['material_request_routes'] = self.material_routes[dim]
                details['implementation_errors'] = self.errors[dim]
                details['unresolved_semantic_boundaries'] = self.boundaries[dim]
                out[dim] = make_decision(1, first['basis_path'], first['current_anchor'], first['current_proposition'], first['context_evidence'], first['reason'], details=details)
            elif self.boundaries[dim]:
                out[dim] = make_decision(None, 'manual_relation_boundary', self.view.current_anchor(0, len(self.view.norm)), self.view.proposition(), _unique_contexts([c for r in self.boundaries[dim] for c in r['context_evidence']]), '材料已有，当前关系的手册边界尚待统一；不把未定改写为0或1。', needed_material=self.boundaries[dim], rule_conflict={'boundary_requests': self.boundaries[dim]}, details={'manual': MANUAL[dim], 'source_missing': False, 'unresolved_material_requests': self.material[dim]})
            elif self.material[dim]:
                specific = '；'.join((f"{item['path']}确指{item['reference']}：{item['missing']}" if isinstance(item, dict) else str(item) for item in self.material[dim]))
                out[dim] = make_decision(None, 'material_insufficient', None, None, [], '当前确指关系所必需的来源内容缺失，不能将未知记为0。' + specific, needed_material=self.material[dim], details={'manual': MANUAL[dim], 'material_request_routes': self.material_routes[dim], 'implementation_errors': self.errors[dim]})
            else:
                reason = '；'.join(self.excluded[dim][:4]) or '当前完整命题未表达本维的实质内容、证据要求或直接制度关系。'
                out[dim] = make_decision(0, 'no_substantive_relation', None, None, [], reason, details={'manual': MANUAL[dim], 'near_candidate_exclusions': self.excluded[dim]})
        return out

def _generic(acc: Accumulator, unit: Unit, obj: dict):
    if unit.kind in {'named_mechanism', 'policy_explanation', 'price_arrangement'}:
        return
    text = unit.text
    for dim in DIMENSIONS:
        if dim in ('S', 'E', 'Ec'):
            continue
        consumers = set(unit.details.get('affected_dimensions', DIMENSIONS))
        if unit.details.get('only_IF_consumers'):
            consumers &= {'I', 'F'}
        if dim not in consumers:
            continue
        if not re.search(TOPICS[dim], text):
            continue
        if dim == 'Ec' and _payment_route_only(text + ('。' + unit.inherited if unit.kind == 'parent_predicate' else '')):
            acc.exclude(dim, unit, '当前只选择申报条件/类别等流程选项；支付调整属于对象身份，没有支付内容核验或授权后果。')
            continue
        if _form_only(text, dim):
            acc.exclude(dim, unit, '仅为字段、格式、签章或材料手续，未提出本维实质内容要求。')
            continue
        if PURE_STRUCTURE.fullmatch(text):
            acc.exclude(dim, unit, '只有栏目或组织性引导，没有本记录独立的实质要求。')
            continue
        if not obj.get('established'):
            acc.exclude(dim, unit, '候选词未建立药物、用药或药品治疗/支付对象。')
            continue
        if dim == 'I' and _administrative_innovation_owner(text):
            acc.exclude('I', unit, '创新性/新颖性修饰办公室组织、值班或管理工作；药品技术属性不是其内容对象。')
            continue
        if dim == 'I' and re.search('创新性[^。；;]{0,15}(?:系统性[^。；;]{0,15})?(?:开展|做好|推进|进行)?[^。；;]{0,12}工作', text) and (not re.search('(?:药品|药物|产品)(?:的)?创新性|创新性(?:信息|评价|评估|证据)|(?:评价|评估|比较)[^。；;]{0,15}(?:药品|药物)[^。；;]{0,8}创新', text)):
            acc.exclude('I', unit, '创新性修饰管理工作的方式，未以药品创新属性或创新研发支持为内容对象。')
            continue
        if re.search(NONDIM[dim], text) and (not re.search(f'(?:药品|药物|用药)[^。；;，,]{{0,15}}(?:{TOPICS[dim]})', text)):
            acc.exclude(dim, unit, '候选词指向行政、信息、基金、一般机构或程序对象。')
            continue
        governed = unit.kind in {'substantive_list', 'cited_standard'}
        content = _substantive(text, dim) or (governed and re.search(CONTENT_ACTION + '|符合|满足|条件|终止', unit.inherited))
        general_word = {'S': '安全性', 'E': '有效性', 'Ec': '经济性', 'I': '创新性|创新程度|创新价值', 'F': '公平性'}[dim]
        topic_content = re.search(general_word, text) and (dim != 'E' or _drug_effectiveness_topic(text))
        if topic_content and content and (re.search(CONTENT_ACTION, text) or governed):
            if dim == 'F' and re.search(NONDIM['F'], text):
                continue
            acc.add(dim, unit, 'general_evaluation_or_information', '当前以药物/治疗为对象要求本维评价、比较或实质信息；具体机制未由概括词补写。', obj)

def _safety_effect(acc, unit, obj):
    if not _se_parent_consumer_scope(acc.view, unit):
        return
    obj = _se_object(acc.view, unit, obj)
    if not obj.get('established'):
        return
    text = unit.text
    for dim in ('S', 'E'):
        if not _se_allowed(unit, dim) or _se_form_or_status(text, dim) or PURE_STRUCTURE.fullmatch(text):
            acc.exclude(dim, unit, '当前仅形式、既有状态、栏目或研究学科名称，没有本维实际内容关系。')
            continue
        governed = unit.kind in {'substantive_list', 'cited_standard'} and bool(re.search('符合|满足|条件|标准|' + SE_ACTION, unit.inherited))
        direct_parent = unit.kind == 'parent_predicate' and unit.details.get('relation_subtype', '').startswith('SE_')
        scope = text + ('。' + unit.inherited if direct_parent else '')
        if re.search('^(?:为了|为)[^。；;]{0,100}(?:现将|予以)[^。；;]{0,80}(?:印发|发布)$', scope) and (not re.search('(?:应|必须|须|要求)[^。；;]{0,30}(?:核验|评价|评估|监测|控制)|(?:药物|药品)[^。；;]{0,15}(?:造成|导致|存在)[^。；;]{0,15}(?:损伤|不良反应|风险)', scope)):
            acc.exclude(dim, unit, '当前仅印发文件的宗旨，未规定实质风险或效果内容。')
            continue
        if dim == 'S':
            if re.search(NONDIM['S'], scope) and (not re.search(SE_RISK + '|' + SE_BENEFIT_RISK, scope)):
                acc.exclude(dim, unit, '当前安全对象为基金、行政、网络或数据，没有药物损害风险。')
                continue
            comparison = re.search(SE_BENEFIT_RISK, scope)
            specific_risk = re.search(SE_RISK, scope)
            generic_risk = re.search('(?:药品|药物|用药)[^。；;，,]{0,15}风险', scope)
            non_drug_owner = re.search('(?:基础疾病|疾病进展|病情进展|数据丢失|数据泄漏|数据库损毁|申报数据|网络|消防|车间)[^。；;]{0,18}(?:风险|安全)', scope)
            linked_risk = re.search('风险控制|风险管理', text) if unit.details.get('relation_subtype') == 'SE_same_drug_risk_control_example' and re.search('给药|用药', unit.inherited) else None
            direct_monitor = re.search('风险(?:发现|识别).{0,12}(?:干预|控制)', scope) if re.search('用药指导|服药后不适', scope) else None
            # Use the operative risk-management relationship outside titles.
            # A document name alone does not establish substantive risk content.
            operative_scope = re.sub('《[^《》]*》', '', scope)
            lifecycle_risk = re.search('(?:全生命周期)?风险管理[^。；;，,《》]{0,24}(?:贯穿|覆盖|用于|应用于)[^。；;，,《》]{0,24}(?:药物|药品)(?:研发|开发)', operative_scope)
            risk = comparison or specific_risk or linked_risk or direct_monitor or lifecycle_risk or (generic_risk if not non_drug_owner else None)
            if non_drug_owner and (not re.search('不良反应|肝损伤|副作用|毒性|过敏|用药错误|用药差错|获益.{0,15}风险', scope)):
                risk = None
            safety_content = re.search('安全性(?:内容|信息|数据|证据|特征|分析|评价|观察|缺陷|风险)|安全(?:耐受性|耐受)[^。；;]{0,8}(?:数据|证据)|用药安全|安全用药|(?:药品|药物)[^。；;，,]{0,15}(?:安全、?有效|更安全)|(?:符合|满足)[^。；;]{0,15}安全[、,]?有效|(?:确保|保证|考虑|关注|影响)[^。；;，,]{0,18}(?:受试者|试验参与者)[^。；;，,]{0,8}安全|(?:耐受性)[^。；;，,]{0,10}(?:较差|不足|降低)|更安全[、,]?有效(?:的)?药物治疗方案|安全性(?!更新报告)', scope)
            substance = bool(re.search(SE_ACTION, scope) or governed or re.search('符合|满足|条件|导致|造成|发生|存在|可能|特征|期望|担忧|变化|减退|混淆', scope))
            if comparison or (risk and (substance or re.search('严重|危害|不鼓励|不得|信号', scope))) or (safety_content and (substance or governed or re.search('重要|更高|较大|缺陷|排除', scope))):
                acc.add(dim, unit, 'S_actual_drug_risk_or_safety_content', '当前识别、评价、形成或核验药物风险/安全性内容，或将其作为条件/控制内容；完整否定、风险获益和例外保留，不认定风险已发生。', obj, {'matched_risk_or_content': (risk or safety_content).group(), 'scope': 'current_or_explicit_bounded_relation'})
                continue
            use_control = re.search('(?:处方|给药|用药医嘱)[^。；;]{0,20}(?:剂量|用法|时间|途径|总量)[^。；;]{0,16}(?:正确|符合规定|准确无误)|(?:审核|核对|是否)[^。；;]{0,20}(?:处方剂量|配伍禁忌|过敏试验)|认知功能[^。；;]{0,80}(?:忘记|难以记住|混淆)[^。；;]{0,25}(?:服药|药品)|(?:给药|服药)[^。；;]{0,25}(?:误选|误用|错误)', scope)
            if use_control:
                acc.add(dim, unit, 'S_current_medication_error_control', '当前核验处方/给药正确性、禁忌或明确服药错误风险，具有直接药物使用风险关系；一般剂量模型或药代术语不凭名称纳入。', obj, {'current_use_control': use_control.group()})
        else:
            if re.search(NONDIM['E'], scope) and (not re.search(SE_EFFECT + '|' + SE_BENEFIT_RISK, scope)):
                acc.exclude(dim, unit, '当前有效性是证件、格式或行政事项，没有药物效果内容。')
                continue
            effect = re.search(SE_EFFECT + '|' + SE_BENEFIT_RISK, scope)
            general = re.search('有效性', scope) and (_drug_effectiveness_topic(scope) or re.search('临床数据的有效性', scope))
            qualified = re.search('(?:安全[、,]?有效|更安全[、,]?有效|安全、有效)[^。；;]{0,25}(?:药物治疗方案|重要|条件)|(?:符合|满足)[^。；;]{0,15}安全[、,]?有效|(?:药品|药物|治疗方案)[^。；;]{0,18}(?:安全[、,]?有效|有效(?:的)?药物治疗)|(?:有效性)[^。；;]{0,15}(?:缺陷|不足)', scope)
            pd_change = re.search('(?:变化|减退|衰退|降低|下降|增强)[^。；;]{0,80}(?:影响|改变)[^。；;]{0,25}药物[^。；;]{0,25}药效学(?:和|与|、|特征)|(?:人群|患者)[^。；;]{0,60}药物作用反应[^。；;]{0,15}(?:差异|变化)', scope)
            if effect or qualified or pd_change or (general and (governed or re.search(SE_ACTION + '|缺陷|不足|影响|特征|期望', scope))) or re.search('(?:结局|报告|测定|指标|终点)[^。；;]{0,65}健康相关(?:的)?生活质量|健康相关(?:的)?生活质量[^。；;]{0,30}(?:报告|测定|指标|终点)', scope) or _current_overall_health_effect(scope):
                acc.add(dim, unit, 'E_actual_drug_effect_or_effect_evidence', '当前表达药物治疗反应、健康/临床获益、实质效果证据或被实际使用的疗效标准；否定与不确定仍保留议题，不将无标准治疗或孤立PK-PD术语转换为有效性。', obj, {'scope': 'current_or_explicit_bounded_relation', 'isolated_PK_PD_not_used': True})
            elif re.search('药效学|PK.?PD|标准治疗|临床价值|终点|有效性', text):
                acc.exclude(dim, unit, '孤立PK/PD、无标准治疗、笼统临床价值或一般终点方法尚未建立对应效果内容。')

def _economics(acc, unit, obj):
    if not _se_parent_consumer_scope(acc.view, unit):
        return
    if unit.details.get('only_IF_consumers') or 'Ec' not in unit.details.get('affected_dimensions', SE_DIMS):
        return
    if unit.kind == 'price_arrangement':
        if unit.details.get('relation_subtype') == 'same_edition_price_node_content_definition' and unit.details.get('version_binding', {}).get('established') and unit.details.get('direct_mapping') and unit.contexts:
            acc.add('Ec', unit, 'Ec_same_edition_actual_price_node', '当前实际价格节点承接同版有限价格定义，不继承普通目录或承保身份。', obj)
        return
    if not _se_allowed(unit, 'Ec'):
        return
    obj = _se_object(acc.view, unit, obj)
    if not obj.get('established'):
        return
    text = unit.text
    inherited = unit.inherited if unit.kind == 'parent_predicate' else ''
    if _ec_identity_only(text, inherited) or _payment_route_only(text + '。' + inherited):
        acc.exclude('Ec', unit, '当前为支付调整的申报对象身份、类别选择或目录分类，没有价格/支付内容核验或实际支付授权。')
        return
    if _se_form_or_status(text, 'Ec') or PURE_STRUCTURE.fullmatch(text):
        acc.exclude('Ec', unit, '只有字段非空、签章、格式或递交手续，没有实际经济内容。')
        return
    scope = text + ('。' + inherited if unit.details.get('relation_subtype', '').startswith('SE_') or (unit.kind == 'parent_predicate' and re.search('(?:费用|药费).{0,50}(?:符合|满足).{0,20}(?:以下|下列).{0,40}(?:基金支付|报销)', inherited)) else '')
    if re.search(NONDIM['Ec'], scope) and (not re.search('药价|药费|药品价格|治疗费用|诊疗费用|支付标准|支付范围|基金(?:支出|支付)|收入损失|社会经济负担', scope)):
        return
    topic = re.search(SE_ECON, scope)
    price_action = re.search('(?:现场价格协商|价格协商意见|价格协商[^。；;]{0,15}(?:决策权|决定权)|(?:按[^。；;]{0,15})?报价|(?:协商|确定|形成|提出|比较|对比|调整|控制|限制|测算|核验|说明|介绍|计算|降低|减少|下调|上调|不高于|不低于)[^。；;，,]{0,25}(?:价格|结算价|费用|成本|预算|支付意愿|支付标准|医保底价|下调比例|降幅)|(?:价格|结算价|费用|成本|报价|支付意愿|支付标准)[^。；;，,]{0,25}(?:高于|低于|合理|不超过|不能高于|降低|作为|比较|对比|下降|下调|上调|不计入))', scope)
    financial_constraint = re.search('以(?:医保)?基金(?:运行)?安全(?:为|作为)(?:底线|前提|约束)', scope)
    governed = unit.kind in {'substantive_list', 'cited_standard'} and re.search(SE_ACTION + '|符合|满足|条件|调出|续约', unit.inherited)
    info = re.search('(?:统计)[^。；;]{0,25}基金实际支出|(?:医保自费率|基金实际支出)[^。；;]{0,20}(?:不计入|统计)|(?:不计入)[^。；;]{0,20}(?:医保自费率)|(?:控制|确定|降低)[^。；;]{0,25}降价幅度|(?:统筹|结合|根据|依据|以)[^。；;]{0,25}基金支付能力[^。；;]{0,35}(?:约束|开展|确定|调整)|(?:介绍|包括|含|信息)[^。；;]{0,35}(?:市场价格|销售金额)|(?:医保|基金)支付[^。；;]{0,25}(?:情况|挂钩)|(?:掌握|监测)[^。；;]{0,25}(?:医保|基金)支付|(?:内容|信息|资料)[^。；;]{0,30}(?:费用|价格)|(?:包括|提供|核验|核对|确认|说明|阐述)[^。；;]{0,35}(?:费用信息|价格信息|费用|支付范围|支付标准|药物经济)|(?:基金实际支出|支付标准|支付范围|费用)[^。；;]{0,30}(?:分歧|核验|核对|确认|测算|计算|口径|合理|变化|调整|不调整|确定)|共同支付的费用|承担[^。；;]{0,20}诊疗费用|(?:个人|患者)[^。；;]{0,15}自付[^。；;]{0,20}(?:比例|确定)|(?:纳入|不纳入|豁免|排除)[^。；;]{0,15}(?:医保支付|按病种付费|DRG|DIP)', scope)
    cost_scope = re.search('(?:带来|增加|造成|减轻|减少)[^。；;]{0,30}(?:费用|误工|收入损失|社会经济负担)|(?:成本|价格|费用|预算|降幅|基金支出|收入损失|社会经济负担)[^。；;]{0,30}(?:不超过|不得|不低于|合理|较高|较低|比例|变化|增加|减少|降低|影响|计算|赔偿|补偿|测算|共同支付)|(?:合理|较高|较低)[^。；;]{0,12}(?:价格|费用|预算)', scope)
    parent_payment = unit.kind == 'parent_predicate' and re.search('支付标准|支付范围|支付责任|基金预算|基金支付|报销', inherited) and re.search('方可|可以|可申请|须|限制|确定|调整|计算|条件|可由', inherited)
    parent_payment = parent_payment or (unit.kind == 'parent_predicate' and unit.details.get('relation_subtype') == 'SE_elliptical_payment_adjustment_member' and unit.details.get('elliptical_payment_object_from_current') and unit.details.get('parent_scope_binding') and re.search('调整(?:医保|限定)?支付范围', text))
    authorization = re.search('(?:方可|才能|可以|允许|不得|不能|须)[^。；;，,]{0,20}(?:调整|变更|确定|支付|报销)[^。；;，,]{0,15}(?:支付范围|支付标准|支付责任|药费|药品费用)', scope)
    if topic and (price_action or financial_constraint or info or cost_scope or governed or parent_payment or authorization or re.search('评价|评估|分析|测算|核验|核对|确认|比较|预算影响|成本效果|成本效用', scope) or (unit.details.get('relation_subtype') == 'SE_same_cost_data_reference' and re.search('科学性|及时性|准确性', text))):
        acc.add('Ec', unit, 'Ec_actual_price_cost_payment_content', '当前形成、评价、核验药品报价/价格/费用/支付信息，或以具体经济条件决定实质机会；无需数字金额或最终获批，不从归类、签章和一般流程推出支付后果。', obj, {'matched_economic_content': topic.group(), 'scope': 'current_or_explicit_bounded_relation'})

def _classification(acc: Accumulator, unit: Unit, obj: dict):
    text = unit.text
    if not re.search('注册分类|注册类别|[1-5一二三四五]类(?:创新药|化学药|治疗用生物制品|预防用生物制品|中药)', text):
        return
    technical_definition = re.search('(?:创新药|改良型新药|创新型|改良型)[^。；;]{0,20}(?:是指|指的是|定义为|具体条件)', text)
    define = bool(technical_definition and re.search('新作用机制|新靶点|新颖|原创|未[^。；;]{0,10}上市|活性成分|临床优势|实质改良', text) or re.search('(?:注册分类|注册类别)[^。；;]{0,20}(?:评价|判定|比较|说明)|(?:[12一二]类)[^。；;]{0,15}(?:为创新|为改良)', text))
    consequence = bool(re.search('允许|可申请|可以申请|可不|可以|续约|重新谈判|给予[^。；;]{0,15}(?:待遇|权利|保护)|差异[^。；;]{0,12}(?:待遇|准入)|条件', text + unit.inherited) and re.search('续约|谈判|支付|准入|待遇|权利|保护|支持机会', text + unit.inherited))
    if not (define or consequence):
        acc.exclude('I', unit, '分类/创新药仅界定对象或儿童、罕见病用途，没有技术分类内容或当前资格—实质后果关系。')
        return
    drug_types = re.findall('化学药品?|治疗用生物制品|预防用生物制品|中药', text)
    if not drug_types:
        acc.request('I', '明确使用分类资格，但缺对应药品种类，不能凭类别号判创新/改良含义。')
        return
    period = bool(re.search('现行药品注册管理办法及注册分类标准|202[0-9]年|202[0-9]-|202[0-9]年起', text + unit.inherited + _context_text(unit)) or unit.details.get('classification_period_verified'))
    if not period:
        acc.request('I', '当前分类的適用时期未明确；需同版药类分类定义，不能套用手册2020起类别。')
        return
    qualifies = re.search('(?:[12一二]类(?:化学药品?|治疗用生物制品|预防用生物制品|中药|创新药|改良型新药)|[12一二]类和[3三]类中药)', text)
    if qualifies:
        acc.add('I', unit, 'I4_classification_content_or_treatment', '当前使用已限定药类/时期的创新或改良分类内容/资格决定实质待遇；分类定义据共同手册§九，混合中药3类不因此成为技术创新，也不证明临床优越。', obj, {'classification_source': 'supplied common manual §九', 'drug_types': drug_types, 'classification_anchor': qualifies.group(), 'definition_or_consequence': 'definition' if define else 'qualification_consequence'})
    else:
        acc.exclude('I', unit, '已知类别未明确对应创新/实质改良，不能把所有新药类别纳入I。')

def _finite_reference_qualification(acc: Accumulator, unit: Unit, obj: dict):
    """Consume only a source-resolved finite current condition→right relation."""
    if unit.kind != 'cited_standard' or unit.details.get('relation_subtype') != 'finite_operational_article_reference':
        return
    condition = _norm(_literal(unit.details.get('current_condition_anchor')))
    consequence = _norm(_literal(unit.details.get('current_consequence_anchor')))
    chain = unit.details.get('reference_chain')
    if not (condition and consequence and (condition in acc.view.norm) and (consequence in acc.view.norm) and isinstance(chain, list) and (1 <= len(chain) <= 2) and re.search('符合|满足|不符合|未满足|条件', condition) and re.search('数据保护期[^。；;，,]{0,15}(?:为|给予|享受)|(?:给予|享受|授予|维持|限制|取消|不予)[^。；;，,]{0,25}(?:保护|权利|许可|准入|待遇)', consequence)):
        return
    qualified_contexts = unit.details.get('qualification_context_evidence') or []
    if qualified_contexts and (not any((_norm(_literal(c)) == unit.text for c in qualified_contexts))):
        return
    comparative_new_data = re.search('已知活性成[分份]|既有活性成[分份]|已上市生物制品', unit.text) and re.search('相比|比较|相较', unit.text) and re.search('明显临床优势|实质临床优势', unit.text) and re.search('新(?:的)?临床试验数据', unit.text)
    innovation_object = re.search(INNOVATION_OBJECT + '|改良型药品', unit.text + '。' + str(unit.details.get('object_definition', '')) + '。' + str(unit.details.get('qualification_text', '')))
    technical_condition = re.search(TECHNICAL_QUALIFICATION, unit.text)
    if not (comparative_new_data or (innovation_object and technical_condition)):
        return
    acc.add('I', unit, 'I4_finite_operative_improvement_data_scope', '当前精确条款条件决定保护/准入等实质权利，有限同源条件范围明确技术创新或相较已知活性产品的临床优势新数据资格；记录资格的制度使用，不因原研身份或权利存在赋I，也不称已证优效或I3。', obj, {'current_condition': unit.details['current_condition_anchor'], 'current_consequence': unit.details['current_consequence_anchor'], 'reference_chain': chain, 'qualification_source': 'source-resolved finite operative condition scope', 'technical_or_comparative_condition': unit.text})

def _innovation_qualification(acc: Accumulator, unit: Unit, obj: dict):
    """Nonnumeric technical/comparative eligibility, not program identity."""
    if unit.kind in {'named_mechanism', 'policy_explanation'}:
        return
    qualification = re.search(TECHNICAL_QUALIFICATION, unit.text)
    if not qualification:
        return
    obj_text = str(obj.get('object_text', ''))
    innovation = re.search(INNOVATION_OBJECT, unit.text + '。' + unit.inherited + '。' + obj_text)
    if not innovation:
        return
    bound = unit.kind in {'parent_predicate', 'substantive_list', 'cited_standard'}
    relation_text = unit.text + ('。' + unit.inherited if bound else '')
    consequence = re.search(QUALIFICATION_CONSEQUENCE, relation_text)
    if not consequence:
        return
    details = {'innovation_object': innovation.group(), 'technical_or_comparative_condition': qualification.group(), 'qualification_consequence': consequence.group(), 'qualification_source': 'legally linked complete same-version standard' if unit.kind == 'cited_standard' else 'current or direct member content'}
    acc.add('I', unit, 'I1_innovation_linked_comparative_value', '当前具体技术/临床比较条件与明确创新或改良对象相连，并用于当前支持资格或实质机会；这是属性/价值内容，不宣称条件已经满足或药品已经优效。', obj, details)
    acc.add('I', unit, 'I4_substantive_qualification_opportunity', '当前技术/临床比较资格决定申请、授予、维持或限制具体支持/准入待遇；合法操作性援引可读取同版完整条件，无须把资格缩为数字注册类别。', obj, details)

def _administrative_innovation_owner(text):
    """Novelty of administrative organization is not drug technical content."""
    technical = re.search('新作用机制|新靶点|新化合物|新分子实体|实质改良|实质改进|(?:药品|药物|新药|制剂)(?:的)?(?:技术)?(?:新颖性|原创性|创新性)', text)
    if technical:
        return False
    return bool(re.search('(?:办公室|监管会议|排班|值班|会议流程|管理工作|组织方式)[^。；;]{0,45}(?:创新|新颖|原创)|(?:创新|新颖|原创)[^。；;]{0,25}(?:排班|会议|值班|管理工作|组织方式)', text))

def _current_RND_support(unit: Unit):
    """Current beneficiary/action/service or explicit comparative convenience.

    No object is taken from programme roles here. Numbers do not establish
    acceleration, and a later different beneficiary blocks the connection.
    """
    if unit.kind != 'current' or _administrative_innovation_owner(unit.text):
        return None
    text = unit.text
    object_match = re.search('(?:' + INNOVATION_OBJECT + ')[^。；;，,]{0,15}?(?:研发|研制)(?:项目|工作|活动)?', text)
    if not object_match:
        return None
    before = text[:object_match.start()]
    subject = re.search('项目|工作|活动$', object_match.group())
    beneficiary = re.search('(?:为|向|对|针对)[^。；;]{0,25}$', before)
    if not (subject or beneficiary):
        return None
    service = re.search('(?:研究|试验|研发)(?:方案|设计|技术|项目)?[^。；;，,]{0,12}(?:反馈|意见|建议|咨询|指导|服务)', text[object_match.end():])
    operation = None
    if service:
        service_start = object_match.end()+service.start()
        operation = re.search('开放|提供|给予|安排|实施|设置|建立|允许[^。；;，,]{0,8}(?:使用|获得)|可(?:以)?获得|撤回|取消|终止|不再提供', text[object_match.end():service_start+1])
        if not operation:
            service = None
    convenience = re.search('(?:审评|审批)(?:时限|期限)[^。；;]{0,45}(?:缩短|减少)|(?:缩短|减少)[^。；;]{0,15}(?:审评|审批)(?:时限|期限)', text[object_match.end():])
    baseline = re.search('(?:相较|相比|比较|较|由)[^。；;]{0,20}(?:普通|常规|一般|现行)(?:程序|审评|审批)|(?:普通|常规|一般)程序[^。；;]{0,20}(?:相比|比较)', text[object_match.end():])
    if not service and not (convenience and baseline):
        return None
    selected = service or convenience
    end = object_match.end()+selected.end()
    if re.search('其他(?:药品|药物|项目)|另一(?:药品|药物|项目)|另一个(?:药品|药物|项目)', text[object_match.end():end]):
        return None
    return {'object':object_match.group(),'arrangement':selected.group(),'operation':operation.group() if operation else '当前相对普通程序明确缩短审评时限','connection':'current explicit same beneficiary and service/convenience; no parallel programme role inheritance','numeric_deadline_alone_not_sufficient':True}

def _same_current_RND_comparative_support(view, unit: Unit):
    """One immediate current antecedent + explicit anaphor and comparison.

    Only the semicolon-separated continuation of the same proposition can
    bind; different objects, ordinary common deadlines and source siblings
    cannot donate an innovation support beneficiary.
    """
    if unit.kind!='current' or not re.match('(?:本条(?:将)?)?(?:其|该(?:项目|药品|通道)|上述(?:项目|通道))',unit.text):
        return None
    prefix=view.norm[:unit.a]
    previous=re.search('[^。；;]+(?=[；;]$)',prefix)
    if previous is None:
        return None
    antecedent=previous.group()
    objects=list(re.finditer('(?:'+INNOVATION_OBJECT+')[^。；;，,]{0,15}?(?:研发|研制)(?:项目|工作|活动)?',antecedent))
    if len(objects)!=1 or re.search('其他(?:药品|药物|项目)|另一(?:个|种)?(?:药品|药物|项目)',antecedent+unit.text):
        return None
    available=re.search('(?:可(?:以)?申请|开放|设置|提供)[^。；;]{0,20}专(?:门|用)[^。；;]{0,12}(?:通道|程序|审评)',antecedent)
    convenience=re.search('(?:审评|审批)(?:时限|期限)[^。；;]{0,45}(?:缩短|减少)|(?:缩短|减少)[^。；;]{0,15}(?:审评|审批)(?:时限|期限)',unit.text)
    baseline=re.search('(?:相较|相比|相对|比较|较)[^。；;]{0,30}(?:普通|常规|一般)(?:程序|审评|审批)',unit.text)
    if not available or not convenience or not baseline:
        return None
    obj=objects[0]
    return {'object':obj.group(),'arrangement':convenience.group(),'operation':'同一当前命题的明确相对审评时限安排',
            'connection':'one immediate same-current innovation RND beneficiary, actual special-channel opportunity, explicit anaphor and ordinary baseline',
            'numeric_deadline_alone_not_sufficient':True,'object_current_anchor':view.current_anchor(previous.start()+obj.start(),previous.start()+obj.end()),
            'available_current_anchor':view.current_anchor(previous.start()+available.start(),previous.start()+available.end()),'not_claiming_shortening_already_achieved':True}

def _innovation(acc: Accumulator, unit: Unit, obj: dict):
    if unit.kind in {'policy_explanation', 'price_arrangement'}:
        return
    text = unit.text
    if not obj.get('established') and re.search('药液(?:浓度|黏度|装量)|给药装置|创新(?:型)?疫苗', text):
        match = re.search('药液(?:浓度|黏度|装量)|给药装置|创新(?:型)?疫苗', text)
        obj = {'established': True, 'current_anchors': [acc.view.current_anchor(unit.a + match.start(), unit.a + match.end())], 'context_evidence': [], 'object_text': match.group(), 'role': 'current_concrete_drug_administration_object', 'reason': '当前药液/给药装置直接建立药物给药对象；仅本I判据使用，不改变S/E/Ec对象门槛。'}
    if not obj.get('established'):
        return
    if _form_only(text, 'I') or PURE_STRUCTURE.fullmatch(text):
        acc.exclude('I', unit, '创新候选只处于字段、手续或结构引导，没有实质内容关系。')
        return
    direct_support = _current_RND_support(unit) or _same_current_RND_comparative_support(acc.view,unit)
    if direct_support:
        acc.add('I', unit, 'I3_current_explicit_RND_support', '当前明确创新研发对象直接获得技术反馈服务，或相较普通程序缩短审评时限；对象—实际可用安排—直接联系均在当前，不借程序名称、数字或其他对象分支。', obj, {'I3_object': direct_support['object'], 'I3_arrangement': direct_support['arrangement'], 'I3_connection': direct_support['connection'], 'support_action': direct_support['operation'], 'numeric_deadline_alone_not_sufficient': True, **({'same_current_support_roles':direct_support} if direct_support.get('object_current_anchor') else {})})
    if unit.kind != 'named_mechanism':
        if re.search('新作用机制|新靶点|新化合物|新分子实体|原创(?:性)?|新颖(?:性)?|原始创新', text) and _substantive(text, 'I') and (not _administrative_innovation_owner(text)):
            acc.add('I', unit, 'I1_technical_novelty', '当前实质讨论、定义或要求技术新颖性/原创性内容；否定或待证判断不被改写为已具优势。', obj)
        if re.search('创新(?:性|程度|价值)', text) and re.search('主要(?:纳入|聚焦)|选择|遴选|准入(?:条件|要求)|评价|比较', text) and (not re.search('创新性[^。；;]{0,20}(?:系统性|工作)', text)) and (not _administrative_innovation_owner(text)):
            acc.add('I', unit, 'I1_innovation_value_selection_content', '当前药品选择/评价以创新程度或创新价值为实质内容；未由目录名称或工作方式推定药品创新。', obj)
        if re.search('已知活性成[分份]|已上市生物制品', text) and re.search('相比|比较|相较', text) and re.search('明显临床优势', text) and re.search('新(?:的)?临床试验数据', text) and re.search('保护范围|资格|条件', text):
            acc.add('I', unit, 'I1_comparative_new_clinical_data_qualification', '当前明确将相较已知活性产品的临床优势新试验数据用于实质资格/保护范围，表达与具体改良价值相连的比较内容；不把一般疗效子项都当创新。', obj)
        change = re.search(MODIFICATION_CHANGE, text)
        obstacle = re.search('吞咽困难|吞咽障碍|难以吞咽|掰断[^。；;]{0,12}(?:困难|不便|障碍)|难以掰断|操作障碍|操作困难|使用障碍|现有[^。；;]{0,15}(?:局限|不足)|难以(?:打开|使用|操作)|(?:手指灵活性|手指功能|手部功能)[^。；;]{0,45}(?:影响|限制)[^。；;]{0,20}(?:掰断|片剂|操作)|(?:掰断|片剂操作)[^。；;]{0,35}(?:受[^。；;]{0,12}(?:手指|手部)|手指灵活性[^。；;]{0,12}影响)', text + '。' + unit.inherited)
        improvement = re.search('缓解|改善|减少|解决|克服|便利|便于|更易|提高[^。；;]{0,8}(?:表现|能力)|实质改良', text)
        if re.search('实质改良|实质改进', text) or (change and obstacle and improvement):
            acc.add('I', unit, 'I2_substantive_modification', '当前具体设计/改变与原文明确的治疗或使用局限、操作障碍及改善关系相连；这记录改良议题，不证明已有效或优效。', obj)
        elif change:
            acc.exclude('I', unit, '仅产品属性变化或一般设计优化，未表达实质改良或明确局限—改变—改善关系。')
        product_change = re.search('(?:优化|改善|改进|设计|开发|选用|具备)[^。；;]{0,40}(?:药液浓度|黏度|装量|推注速度|针头|规格|隐藏保护机制|片剂|剂型|装置|口崩|给药途径)|(?:掰断|压碎|咀嚼|打开)[^。；;]{0,12}(?:片剂|胶囊)|(?:新剂型|新给药途径)', text)
        limitation = re.search('现有[^。；;]{0,25}(?:均不适用|不适合|局限|不足)|吞咽困难|吞咽障碍|注射时间过长[^。；;]{0,10}不适|疼痛|恐针|误刺|操作负担|难以吞咽', text + ('。' + unit.inherited if unit.kind == 'parent_predicate' else ''))
        bridge = re.search('(?:避免|降低|缓解|预防|减少|便于|有利于|改善|解决)[^。；;]{0,35}(?:不适|疼痛|恐针|误刺|负担|吞咽|掰断|操作)|(?:新剂型)[^。；;]{0,15}(?:(?:适宜|适用)[^。；;]{0,12}(?:儿童|人群)|(?:儿童|人群)[^。；;]{0,12}(?:适宜|适用))|(?:对于|针对)[^。；;]{0,20}吞咽[^。；;]{0,15}(?:困难|障碍)[^。；;]{0,35}(?:掰断|压碎|咀嚼|打开)|(?:这种|该)(?:灵活性|设计|改变)[^。；;]{0,10}对[^。；;]{0,12}吞咽困难[^。；;]{0,15}有益', text)
        if product_change and limitation and bridge:
            acc.add('I', unit, 'I2_concrete_limitation_change_bridge', '当前具体产品/给药设计操作与明确既有不适用或使用障碍及改善目的直接相连；普通剂型身份与泛化优化不充分。', obj, {'product_change': product_change.group(), 'limitation': limitation.group(), 'improvement_bridge': bridge.group(), 'claimed_already_superior': False})
        if unit.details.get('relation_subtype') == 'bounded_IF_modification_bridge' and re.search('实质改良|实质改进|改良给药途径', unit.inherited) and re.search('开发[^。；;]{0,20}(?:制剂|剂型)|改变[^。；;]{0,20}给药途径', text) and re.search('改善[^。；;]{0,15}便利|减少[^。；;]{0,15}(?:给药频次|治疗负担)', text):
            acc.add('I', unit, 'I2_direct_example_of_defined_modification', '当前具体给药产品改变及便利/频次/负担改善以显式例示词直接承接同段实质改良定义；未把一般剂型知识转为创新。', obj)
        _classification(acc, unit, obj)
        _finite_reference_qualification(acc, unit, obj)
        _innovation_qualification(acc, unit, obj)
        if re.search('纳入[^。；;]{0,15}\\d+日通道[^。；;]{0,35}应当为[^。；;]{0,40}[1一]类创新药', text) and re.search('中药|化学药|生物制品', text):
            acc.add('I', unit, 'I4_explicit_innovation_qualification_timed_channel', '当前明称创新药的药类资格被用于实际有时限的办理通道准入；不是仅从裸类别号或通道名称推断创新。', obj)
        if unit.details.get('relation_subtype') == 'bounded_IF_table_qualification_consequence':
            acc.add('I', unit, 'I4_current_table_qualification_right', '当前完整表行按原始行列关系直接把明文创新/改良药品资格用于数据保护等实质待遇；非由类别号或表名推定。', obj, {'qualification': unit.details['current_table_subject'], 'consequence': unit.details['current_table_right'], 'consequence_column': unit.details['table_header'], 'table_row_structure': unit.details['table_row_structure']})
        if re.search(INNOVATION_OBJECT, text) and unit.kind in {'parent_predicate', 'substantive_list', 'cited_standard'} and re.search('指定[^。；;]{0,20}药品检验机构[^。；;]{0,20}承担|中检院[^。；;]{0,35}承担[^。；;]{0,20}注册检验', unit.inherited):
            acc.add('I', unit, 'I4_innovation_category_regulatory_consequence', '创新/改良资格在当前直接父谓词下决定指定机构承担注册检验的实质监管后果；不称该后果是研发资助。', obj, {'category': re.search(INNOVATION_OBJECT, text).group(), 'consequence': unit.inherited})
    public_guidance = bool(re.search('本指导原则|技术指导原则|技术指南|本指南', text) and re.search('起草|制定|提出[^。；;]{0,20}考虑|提供指导|设计考虑|(?:可|可以|建议)[^。；;]{0,8}(?:参考|参照)', text) and (not re.search('反馈|审评团队|人员培训|技术培训|咨询服务|可申请[^。；;]{0,15}(?:反馈|技术服务)', text)))
    if public_guidance:
        acc.exclude('I', unit, '公共指南的设计/风险规范未另设创新研发可使用的服务、反馈或支持机会，不能以普遍指导功能记I3。')
        return
    if _publication_purpose(text) and unit.kind != 'named_mechanism':
        acc.exclude('I', unit, '当前仅说明制定/发布文件的创新宗旨，没有本句独立的可用支持安排。')
        return
    obj_text = str(obj.get('object_text', ''))
    combined = text + '。' + unit.inherited
    innovation = re.search(INNOVATION_OBJECT, text + '。' + obj_text + '。' + unit.inherited)
    resource = re.search(SUPPORT, combined)
    if innovation and resource and (innovation.end() <= resource.start() <= len(text)) and re.search('其他(?:药品|药物|产品)|另(?:一|外)[^。；;，,]{0,10}(?:药品|药物|产品)', text[innovation.end():resource.start()]):
        acc.exclude('I', unit, '资源/服务属于另一个药品对象，创新对象与支持内容未直接相连。')
        return
    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_IF_actual_support':
        resource = re.search('沟通交流|沟通|技术咨询|专家咨询会|研究方案|试验方案|反馈|审评[^。；;]{0,20}(?:时限|期限|工作日)|\\d+(?:个)?(?:工作)?日内完成审评|单独序列|协调和督导|研究资料|研发', _norm(unit.details.get('direct_mechanism', '')))
        innovation = re.search(INNOVATION_OBJECT, _norm(unit.details.get('object_definition', '')))
        if innovation is None:
            definition = _norm(unit.details.get('object_definition', ''))
            innovation = re.search('(?:化学药品?|生物制品|中药)[^。；;]{0,45}(?:注册)?[1一]类', definition)
    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_primary_postadmission_technical_support':
        resource = re.search('(?:补充提交技术资料|研究方案反馈|试验方案反馈|研发技术咨询)[^。；;]{0,20}(?:沟通交流申请|技术咨询申请)', _norm(unit.details.get('direct_mechanism', '')))
        if resource is None:
            resource = re.search('(?:在审评中|审评过程中)[^。；;]{0,65}(?:沟通交流|技术咨询|研究反馈)[^。；;]{0,30}优先(?:安排|处理|提供)', _norm(unit.details.get('direct_mechanism', '')))
        innovation = re.search(INNOVATION_OBJECT, '。'.join((_norm(_literal(e)) for e in unit.details.get('innovation_eligible_branches', []))))
    if resource is None and unit.kind == 'named_mechanism' and (unit.details.get('relation_subtype') == 'bounded_primary_qualification_support_roles'):
        resource = re.search('优先配置[^。；;]{0,15}资源[^。；;]{0,20}(?:沟通交流|技术服务|研究方案反馈|研发)', _norm(unit.details.get('direct_mechanism', '')))
    action = re.search(SUPPORT_ACTION, text + ('。' + unit.inherited if unit.kind == 'parent_predicate' else ''))
    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_IF_actual_support':
        action = re.search('可|应|自愿申报|审评时限为|完成|保持|维持|退出|终止|撤回|不再|协助|决定|组织|设立|开展|提供|安排|反馈', text)
    actual_rnd = bool(re.search('研发|研制|研究方案|试验方案|临床试验|上市前|申报前|上市许可申请', text + obj_text + unit.inherited))
    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_primary_postadmission_technical_support':
        action = re.search('进行|开展|提供|安排', text)
        actual_rnd = bool(resource and unit.details.get('research_stage') and unit.details.get('current_service_anchor'))
    routine_after_marketing = bool(re.search('上市后[^。；;]{0,18}(?:常规|日常)[^。；;]{0,18}(?:用药监测|临床服务|处方|治疗管理)|常规(?:用药监测|临床服务)', text) and (not re.search('(?:进一步|继续|后续)[^。；;]{0,15}(?:创新|改良)?(?:研发|研制)|服务于[^。；;]{0,20}(?:创新|改良)[^。；;]{0,12}(?:研发|研制)', text)))
    if routine_after_marketing:
        acc.exclude('I', unit, '当前实际用途是上市后常规监测/临床服务，没有进一步创新研发支持联系，不能从创新适用范围继承I3。')
        return
    team_resource = resource and re.search('审评团队|审评人员', resource.group())
    if team_resource:
        explicit_service = re.search('(?:审评团队|审评人员|团队)[^。；;]{0,30}(?:负责|承担|提供)[^。；;]{0,40}(?:研究方案反馈|试验方案反馈|研发技术服务|研发技术咨询)', combined)
        whole_review_service = re.search('(?:负责|承担)[^。；;]{0,40}申报前[^。；;]{0,30}沟通[^。；;]{0,35}技术审评[^。；;]{0,15}全过程', combined) and re.search('相对稳定|保持稳定|人员稳定|团队稳定', combined)
        if not (explicit_service or whole_review_service or unit.details.get('relation_subtype') == 'bounded_IF_actual_support'):
            acc.exclude('I', unit, '组建/配置团队只是资源候选，尚无当前或确指同段的具体研发技术服务定义；创新scope不能代替服务内容。')
            resource = None
    if unit.kind == 'parent_predicate' and resource and (not re.search(SUPPORT, text)):
        if not re.search(INNOVATION_OBJECT + '|' + TECHNICAL_QUALIFICATION, text):
            resource = None
    scientific_function = bool(re.search('(?:本|该)(?:项目|计划|试点工作)[^。；;]{0,35}(?:核心目的|目的)|试点工作的核心目的', text) and re.search('(?:解决|探讨解决|帮助解决)[^。；;]{0,45}(?:研发|研究)[^。；;]{0,15}科学问题', text))
    if innovation and actual_rnd and (resource and action or scientific_function):
        if re.search('申请人[^。；;]{0,30}(?:收集|更新|报送|提交)[^。；;]{0,25}(?:安全资料|风险管理|文件)', text) and (not re.search('(?:给予|配置|提供)[^。；;]{0,20}(?:反馈|团队|资源|技术服务)', text)):
            acc.exclude('I', unit, '当前是申请人的一般义务，不因创新对象转为研发支持。')
            return
        acc.add('I', unit, 'I3_actual_innovative_research_support', '当前设立、实施、开放、限制或撤回明确创新/改良研发可使用的资源、服务、反馈、便利或支持机会；当前行动与支持对象直接相连。', obj, {'I3_object': innovation.group(), 'I3_arrangement': resource.group() if resource else '项目明确解决创新研发科学问题的支持功能', 'I3_connection': 'current and legally linked quoted object/arrangement', 'support_action': action.group() if action else '具体项目支持功能', **({'I3_role_evidence': {'current_service_bridge': unit.details['current_service_bridge'], 'object': unit.details['innovation_eligible_branches'], 'object_applicability_scope': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'object_and_need_eligibility'], 'priority_is_not_required_for_I3': True, 'technical_material_branch_is_not_required_for_F': True, 'postadmission_priority_technical_communication': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'postadmission_priority_technical_communication'], 'postadmission_technical_material_feedback': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'postadmission_technical_material_feedback'], 'preapplication_mechanism_inherited': False}} if unit.details.get('relation_subtype') == 'bounded_primary_postadmission_technical_support' else {}), **({'I3_role_evidence': {'current_bridge': unit.details['current_qualification_bridge'], 'object': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'object_and_eligibility_definition'], 'available_priority_support': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'priority_research_support'], 'direct_withdrawal': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'withdrawal_direct_mechanism']}} if unit.details.get('relation_subtype') == 'bounded_primary_qualification_support_roles' else {})})
    elif re.search('创新药|支持|鼓励|研发|研制|数据保护', text):
        acc.exclude('I', unit, '只有创新身份、一般鼓励、程序/沟通形式或权利存在，未同时建立创新研发对象、可用安排及直接联系。')
    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_IF_qualified_right_operation' and re.search(INNOVATION_OBJECT, unit.details.get('object_definition', '')):
        acc.add('I', unit, 'I4_qualified_innovation_right_operation', '当前实际开放、维持、限制或终止同一权利/待遇，有限同版定义明确创新或改良资格及其权利后果；不从原研身份推定创新。', obj, {'qualified_object': unit.details.get('object_definition'), 'right_operation': text, 'I3_not_inferred': True})

def _fairness(acc: Accumulator, unit: Unit, obj: dict):
    text = unit.text
    if unit.kind == 'price_arrangement':
        return
    if not obj.get('established') or _form_only(text, 'F'):
        return
    if re.search(NONDIM['F'], text):
        acc.exclude('F', unit, '公平指向企业竞争、廉政或办理程序，未表达患者药品机会关系。')
        return
    combined = text + '。' + unit.inherited
    if re.search('(?:不限定|不限制)[^。；;]{0,25}(?:申报药品的)?治疗领域', text) and re.search('满足[^。；;]{0,15}(?:各|不同)治疗领域[^。；;]{0,12}用药需求', text):
        acc.add('F', unit, 'F_different_treatment_needs_open_opportunity', '当前以不同治疗领域用药需要为明确对象，实质开放药品申报机会而不限定治疗领域；不是单有渠道或目录名称。', obj, {'need': '各治疗领域用药需求', 'allocation': '申报机会不按治疗领域限制'})
    affordability = re.search('(?:患者|家庭|人群|参保人)[^。；;]{0,25}(?:可负担|能否负担|是否负担|负担不起|无力支付|买不起)|(?:药品|药物|用药|治疗)[^。；;]{0,12}可负担性|可负担性[^。；;]{0,20}(?:药品|药物|用药|治疗)', text)
    if affordability and _substantive(text, 'F'):
        acc.add('F', unit, 'F_patient_affordability', '当前实质涉及患者能否负担所需药品治疗；该命题已含费用与支付能力关系，不补造收入或已改善效果。', obj, {'F_object': '患者药品治疗及持续接受', 'F_relation': affordability.group()})
    barrier = re.search('(?:同等|相同)治疗需要[^。；;]{0,40}(?:差异|不平等|不公平|机会)|(?:患者|人群)[^。；;]{0,20}(?:无法|不能|难以|未能)(?:持续|及时)?(?:获得|取得|获取|得到|接受)[^。；;]{0,12}(?:所需|必要)(?:药品|药物|治疗)|(?:地区|基层|区域|收入|保障身份)[^。；;]{0,20}(?:用药差异|获取差异|极不平衡)', text)
    if barrier:
        acc.add('F', unit, 'F_identified_treatment_opportunity_barrier', '当前明确所需药品治疗的获取障碍或同等需要的机会差异，未由一般人群名称或渠道信息推定公平。', obj, {'F_object': '患者获得/持续接受所需药品', 'F_relation': barrier.group()})
    gaps = [(name, re.search(pattern, combined)) for name, pattern in GAPS.items()]
    gaps = [(name, match) for name, match in gaps if match]
    opportunity = re.search(OPPORTUNITY, combined)
    if re.search('境外已上市[^。；;]{0,8}境内未上市', text) and opportunity and (not any((re.search(pattern, text) for pattern in GAPS.values()))):
        # This is the only changed v7 branch. Product access and universal
        # indication/alternative gaps remain separate; list names are no need proof.
        product_gap = re.search('境外已上市[^。；;，,]{0,8}境内未上市(?:的)?[^。；;，,]{0,12}(?:药品|药物|产品|新药)', text)
        current_need = re.search('临床急需(?:的)?境外已上市[^。；;，,]{0,8}境内未上市(?:的)?[^。；;，,]{0,12}(?:药品|药物|产品|新药)', text)
        priority_action = '(?:可|可以|允许)(?:在|于)?[^。；;]{0,120}(?:提出|申请)(?:适用)?优先审评(?:审批)?(?:申请|程序)?|(?:直接|应当|可以|可)(?:予以)?纳入[^。；;，,]{0,12}优先审评(?:审批)?(?:程序)?'
        current_opportunity = re.search(priority_action, text)
        parents = [acc.view.by_id.get(q.get('context_id')) for q in unit.contexts]
        parent_closed = bool(unit.kind == 'parent_predicate' and parents and all(c and c.get('kind') == 'parent_paragraph' and acc.view._se_parent_binding(c) for c in parents))
        parent_need = re.search('临床急需(?:的)?(?:以下|下列|这些)(?:药品|药物|产品|新药)', unit.inherited) if parent_closed else None
        parent_opportunity = re.search(priority_action, unit.inherited) if parent_closed else None
        negated_need = re.search('(?:并非|不是|不属(?:于)?|不构成|未达到|非)临床急需', text + ('。' + unit.inherited if parent_closed else ''))
        same_current_subject = bool(product_gap and current_opportunity and product_gap.end() <= current_opportunity.start() and not re.search('另(?:一|外)[^。；;，,]{0,10}(?:药品|药物|产品)|其他(?:药品|药物|产品)', text[product_gap.start():current_opportunity.end()]))
        same_parent_subject = bool(product_gap and parent_need and parent_opportunity and not re.search('另(?:一|外)[^。；;，,]{0,10}(?:药品|药物|产品)|其他(?:药品|药物|产品)', text + '。' + unit.inherited))
        if product_gap and not negated_need and ((current_need and same_current_subject) or same_parent_subject or (parent_need and same_current_subject)):
            acc.add('F', unit, 'F_needed_product_domestic_marketing_gap_priority', '当前或合法直接父谓词把真实临床急需目标、同一所需产品境外已上市而境内未上市的取得缺口，与针对性优先申请或直接纳入机会连接；仅认定该产品的境内通常上市取得选项缺口，不推定全部替代治疗不存在或患者已取得药品。', obj, {'F_object': '临床急需的同一所需药品', 'F_gap_branches': [{'kind': 'needed_product_domestic_marketing_access_gap', 'text': product_gap.group()}], 'F_need': current_need.group() if current_need else parent_need.group(), 'F_arrangement': current_opportunity.group() if same_current_subject else parent_opportunity.group(), 'direct_parent_consumed': bool(not current_need or not same_current_subject), 'all_effective_alternatives_absent_inferred': False, 'all_indication_approved_options_absent_inferred': False, 'physical_supply_shortage_inferred': False, 'access_or_priority_outcome_realized_inferred': False})
        else:
            acc.boundary('F', unit, '单品种未上市与按需优先机会', '该品种境内未上市不证明对应治疗选项缺口；临床急需/罕见病及差别时限是否独立构成按需机会关系须按冻结手册统一，不能沿用错误等同。')
    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_IF_actual_support' and re.search('优先(?:配置|安排|处理)[^。；;]{0,30}(?:沟通|资源|技术|申请)', unit.details.get('direct_mechanism', '')):
        opportunity = re.search('优先(?:配置|安排|处理)[^。；;]{0,30}(?:沟通|资源|技术|申请)', unit.details['direct_mechanism'])
    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_primary_postadmission_technical_support':
        gap_scope = _norm(unit.details.get('object_definition', ''))
        gaps = [(name, re.search(pattern, gap_scope)) for name, pattern in GAPS.items()]
        gaps = [(name, match) for name, match in gaps if match]
        opportunity = re.search('(?:在审评中|审评过程中)[^。；;]{0,65}(?:沟通交流|技术咨询|研究反馈)[^。；;]{0,30}优先(?:安排|处理|提供)', _norm(unit.details.get('direct_mechanism', '')))
    if gaps and opportunity and _publication_purpose(text) and (unit.kind not in {'named_mechanism', 'policy_explanation'}):
        acc.exclude('F', unit, '当前短缺/优先词处于制定或发布文件的宗旨，未实际设置以该缺口为条件的申请、优先资源或保障机会。')
        return
    bound_relation = unit.kind in {'parent_predicate', 'substantive_list', 'cited_standard', 'named_mechanism'}
    current_action = re.search(ACTUAL_ALLOCATION, text)
    target_priority = re.search('(?:对|针对|对于)[^。；;]{0,65}(?:药品|药物)[^。；;]{0,10}(?:予以)?优先(?:审评|保障|配置|支持)(?!程序(?:简介|名称))', text)
    distinct_subject = False
    if current_action and gaps:
        first_gap = min((match.start() for _, match in gaps))
        between = combined[first_gap:current_action.end()]
        distinct_subject = bool(re.search('另(?:一|外)[^。；;，,]{0,10}(?:药品|药物|产品)|其他(?:药品|药物|产品)', between))
    direct_mapping = bound_relation or bool((current_action or target_priority) and (not distinct_subject))
    if gaps and opportunity and direct_mapping:
        acc.add('F', unit, 'F_need_linked_opportunity_allocation', '原文明示治疗选项或供药缺口，并以该缺口连接针对性申请、优先资源或保障安排；三类缺口分别留痕，未假定已经兑现。', obj, {'F_object': '目标患者所需药品治疗', 'F_gap_branches': [{'kind': name, 'text': match.group()} for name, match in gaps], 'F_arrangement': opportunity.group(), 'branch_scope': 'only the quoted qualifying branches', **({'F_role_evidence': {'current_service_bridge': unit.details['current_service_bridge'], 'need_eligibility': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'object_and_need_eligibility'], 'postadmission_priority_communication': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'postadmission_priority_technical_communication'], 'gap_branches_only': [{'kind': name, 'text': match.group()} for name, match in gaps], 'preapplication_mechanism_inherited': False}} if unit.details.get('relation_subtype') == 'bounded_primary_postadmission_technical_support' else {}), **({'F_role_evidence': {'current_bridge': unit.details['current_qualification_bridge'], 'need_and_application_definition': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'object_and_eligibility_definition'], 'priority_support': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'priority_research_support'], 'withdrawal': [r['evidence'] for r in unit.details['source_roles'] if r['role'] == 'withdrawal_direct_mechanism'], 'gap_branches_only': [{'kind': name, 'text': match.group()} for name, match in gaps], 'clinical_advantage_safety_and_other_termination_branches_not_fairness_by_inheritance': True}} if unit.details.get('relation_subtype') == 'bounded_primary_qualification_support_roles' else {})})
    elif unit.kind in {'named_mechanism', 'policy_explanation'} and gaps and re.search('优化[^。；;]{0,20}(?:配送|用药衔接)|完善[^。；;]{0,20}供应|提高[^。；;]{0,20}配送', text):
        mapping = bool(unit.details.get('direct_mapping') or unit.details.get('problem_action_mapping') or re.search('针对[^。；;]{0,45}(?:衔接不畅|配送能力弱|供应不稳定|断供)', unit.inherited))
        if mapping:
            acc.add('F', unit, 'F_source_mapped_supply_gap_correction', '同版确指官方解释把当前药品配送/衔接措施直接连接所需治疗的获取或持续供给缺口；只使用相应问题—措施片段。', obj, {'F_gap_branches': [{'kind': name, 'text': match.group()} for name, match in gaps], 'F_arrangement': text})
    elif re.search(TOPICS['F'], text):
        acc.exclude('F', unit, '最接近候选为需要、可及性、普通供给/目录/渠道、价格责任、管理便利或比喻导向，未建立具体公平关系或明确公平评价要求。')

def judge(view) -> dict:
    """Return five independently evidenced DimensionDecision mappings."""
    acc = Accumulator(view)
    for unit in _units(view):
        obj = _object(view, unit)
        consumers = set(unit.details.get('affected_dimensions', DIMENSIONS))
        if unit.details.get('only_IF_consumers'):
            consumers &= {'I', 'F'}
        _generic(acc, unit, obj)  # Each generic consumer independently intersects its typed permissions.
        if consumers.intersection({'S', 'E'}):
            _safety_effect(acc, unit, obj)
        if 'Ec' in consumers:
            _economics(acc, unit, obj)
        if 'I' in consumers:
            _innovation(acc, unit, obj)
        if 'F' in consumers:
            _fairness(acc, unit, obj)
    decisions = acc.finish()
    if _publication_purpose(view.norm):
        for dimension, decision in decisions.items():
            if decision['value'] == 0:
                decision.update(basis_path='pure_document_enactment_purpose', current_anchor=view.current_anchor(0, len(view.norm)), current_proposition=view.proposition(0, len(view.norm)), reason='当前完整记录仅说明制定或印发文件的宗旨，没有本句独立的实质问题、评价/证据要求或可使用措施；不展开该文件后文内容。')
                decision['details']['purpose_boundary'] = 'complete_current_proposition; no_downstream_document_inheritance'
    return decisions
SE_DIMS = ('S', 'E', 'Ec')
SE_ACTION = '评价|评估|分析|比较|测算|计算|考察|说明|阐述|收集|整理|汇总|呈现|撰写|审阅|核对|核验|验证|确认|提供|要求|应包括|内容涉及|应当|应|需|建议|鼓励|判定|确定|监测|预防|控制|避免|降低|减少|识别|不列入|排序|发生率'
SE_RISK = '(?:风险控制|风险管理)[^。；;]{0,100}(?:给药|用药)|不良(?:反应|事件)|肝损伤|副作用|神经毒性|预防接种异常反应|治疗窗窄|(?<![A-Za-z])(?:AESI|ADR|SAE|AE)(?![A-Za-z])|毒性|毒理(?:结果|数据|证据)|药物风险|用药风险|已识别[^。；;]{0,8}风险|潜在风险|安全性事件|过敏|皮试|禁忌|药物相互作用|配伍禁忌|误(?:选|用|刺|吸)|呛咳|窒息|暴露[^。；;]{0,12}风险|用药差错|用药错误|超剂量|无指征'
SE_BENEFIT_RISK = '获益[-—–/]?风险|获益[^。；;，,]{0,12}(?:大于|小于|不大于|超过|高于|低于)[^。；;，,]{0,5}风险|风险[^。；;，,]{0,8}(?:大于|超过|高于)[^。；;，,]{0,5}(?:获益|收益)|风险获益(?:不确定|平衡|比)'
SE_EFFECT = '疗效(?!一致性评价[^。；;，,]{0,12}(?:的)?(?:药品|化学药))|治疗效果|治疗效应|疾病控制(?:效果|要求|证据)?|防治效果|临床获益|健康(?:收益|获益)|(?:患者|受试者)[^。；;，,]{0,18}获益|获益[^。；;，,]{0,12}(?:患者|受试者)|(?:从|通过|接受)[^。；;，,]{0,18}治疗[^。；;，,]{0,12}获益|(?:治疗|试验)[^。；;，,]{0,15}(?:没有|无|不具)[^。；;，,]{0,6}预期获益|治疗(?:的)?反应|治疗应答|药物作用反应|明显(?:临床|治疗)优势|显著(?:临床|治疗)优势|临床比较优势|(?:改善|延长|提高|降低|减少)[^。；;，,]{0,20}(?:生存|生命质量|生活质量|死亡|复发|症状|疼痛)|(?:尚无|没有|缺乏|不存在)有效(?:防治|治疗)(?:手段|药物|措施|选择|选项)|无效(?:剂量|治疗)|非充足剂量治疗'
SE_ECON = '经济性|药物经济(?:学|性)|成本[-—]?效果|成本[-—]?效用|药价|价格|费用|成本|预算|报价|结算价|中标价|零售价格|医保底价|支付意愿|支付标准|支付范围|支付责任|医保支付|基金支付|基金(?:运行)?安全(?:为|作为)(?:底线|前提|约束)|医保自费率|降价幅度|基金(?:实际)?支出|基金(?:支出)?预算|预算增幅|预算影响|销售金额|销售预算|药费|治疗费用|诊疗费用|药品费用|费用信息|自付(?:率|比例|费用)?|报销|下调比例|降幅|(?:供药|供应)[^。；;]{0,6}(?:价格|成本)|费用口径|收入损失|误工|社会经济负担|无法单独收费|按病种付费|DRG|DIP'

def _se_form_or_status(text, dim):
    topic = {'S': SE_RISK + '|' + SE_BENEFIT_RISK + '|安全性|用药安全', 'E': SE_EFFECT + '|' + SE_BENEFIT_RISK + '|有效性|安全[、,]?有效', 'Ec': SE_ECON}[dim]
    parts = re.split('[。；;，,]', text)
    actual = any((re.search(topic, p) and re.search('评价|评估|比较|核验|核对|说明|测算|确认|分析|证明|解释|估计|结算|合理|预算|监测|控制|承担|提供', p) and (not re.search('(?:仅|只)(?:检查|确认|审核)[^。；;]{0,20}(?:格式|位数|命名|文件名)|(?:命名|格式|文件名|包名)[^。；;]{0,15}(?:须|应|必须|采用|改为)', p)) for p in parts))
    actual = actual or bool(re.search('(?:提交|递交|补充|提供)[^。；;，,]{0,18}(?:安全性|药物风险|疗效|疾病控制效果|治疗效果)[^。；;，,]{0,8}(?:证据|数据|分析)', text))
    if re.search('(?:已经|已)(?:获得|取得|登记|列为)[^。；;]{0,30}(?:称号|名号|产品名|名称)|(?:安全有效)[^。；;]{0,15}(?:称号|名称)', text) and (not re.search('核验|评价|评估|比较|证明', text)):
        return True
    if dim == 'Ec' and re.search('(?:按|按照|依)[^。；;，,]{0,15}(?:要求|规定|规则)[^。；;，,]{0,8}报价', text) and (not re.search('报价字段|报价栏目|报价文件名', text)):
        actual = True
    forms = re.search('字段|栏目|格式|签字|签章|盖章|文件名|包名|命名|压缩包|上传|归档|递交|提交|编号填写|填写申报表', text)
    if forms and (not actual):
        return True
    if dim == 'S':
        residue = re.sub('(?:药物)?研发期间安全性更新报告', '报告', text)
        if residue != text and (not re.search(SE_RISK + '|' + SE_BENEFIT_RISK + '|安全性(?:内容|信息|数据|证据|分析|评价)', residue)):
            return True
        if re.search('药物警戒工作经验[^。；;]{0,10}说明', text):
            return True
        if re.search('药理毒理学|非临床安全性评价研究|药理毒理', text) and (not re.search(SE_RISK + '|安全性(?:结果|数据|证据|内容|信息)|获益[^。；;]{0,10}风险', re.sub('药理毒理学|非临床安全性评价研究|药理毒理', '学科', text))):
            return bool(re.search('完成|开展|进行|计划|机构|认证|资料|研究工作', text))
    if dim == 'E' and re.search('(?:建立|收载|公开|更新)[^。；;]{0,80}目录集|目录集[^。；;]{0,80}(?:载明|公开|更新)', text):
        return not bool(re.search('(?:核验|评价|比较|分析|验证)[^。；;]{0,15}(?:疗效|治疗效果|有效性)', text))
    return False

def _ec_identity_only(text, inherited=''):
    if re.search('(?:申报|填报|填写).{0,20}(?:选择|勾选|填写).{0,30}(?:条件编号|编号|类别|分类)', text) and (not re.search('核验|核对|测算|确认|方可|才能', text)):
        return True
    stripped = re.sub('^\\s*(?:第[一二三四五六七八九十百千0-9]+条|[（(]?[一二三四五六七八九十0-9]+[）)、.．])\\s*', '', text).rstrip('。:：')
    if re.fullmatch('(?:不)?调整支付范围的药品', stripped):
        return True
    if re.search('支付标准有效期到期后[^。；;]{0,40}纳入常规目录乙类', text):
        return not bool(re.search('(?:执行|制定|确定|核验|调整)[^。；;]{0,15}支付标准', text))
    identity = re.search('(?:主动|企业主动)(?:申请|申报)调整(?:医保|限定)?支付范围[^。；;]{0,20}药品', text)
    actual = re.search('方可|才能|不得|不予|须[^。；;]{0,8}(?:调整|重定)|(?:核验|核对|确认|测算|确定|授权|允许)[^。；;]{0,20}(?:支付范围|支付标准)|(?:费用|价格|预算)[^。；;]{0,15}(?:不超过|合理|变化|核验)', text)
    parent_payment = re.search('(?:方可|才能|可以|允许|须)[^。；;]{0,25}(?:调整|确定|支付|报销)[^。；;]{0,18}(?:范围|标准|费用)', inherited)
    elliptical_payment = bool(identity and re.search('(?:以下|下列|这些).{0,12}(?:情况|情形).{0,15}(?:须|需|应|必须).{0,12}(?:申报|申请).{0,12}(?:方可|才能).{0,8}调整[:：]?$', inherited))
    return bool(identity and (not actual) and (not parent_payment) and (not elliptical_payment))

def _se_allowed(unit, dim):
    consumers = unit.details.get('affected_dimensions')
    if consumers is not None and dim not in consumers:
        return False
    if unit.details.get('only_IF_consumers'):
        return False
    if unit.kind in {'substantive_list', 'cited_standard'}:
        return bool(unit.details.get('SE_scope_verified'))
    return unit.kind not in {'named_mechanism', 'policy_explanation', 'price_arrangement'}

def _se_general(acc, unit, obj):
    return

def _se_object(view, unit, obj):
    if obj.get('established'):
        return obj
    for c in view.contexts:
        raw = c.get('text', '')
        primary = view.unit.get('source_ref', {}).get('sha256')
        if c.get('source_ref', {}).get('sha256') != primary:
            continue
        current_component = view.unit.get('source_ref', {}).get('locator', {}).get('component_id')
        component = c.get('structure', {}).get('component_id') or c.get('source_ref', {}).get('locator', {}).get('component_id')
        if current_component and component and (current_component != component):
            continue
        same_paragraph = c.get('kind') == 'paragraph' and _norm(view.norm) in _norm(raw)
        scope = c.get('kind') == 'source_paragraph' and re.search('针对|适用(?:于)?|以[^。；;]{0,15}为对象|对[^。；;]{0,25}(?:药物|药品)[^。；;]{0,18}(?:临床研发|研究|用药)', raw)
        direct_parent = c.get('kind') == 'parent_paragraph'
        if (same_paragraph or scope or direct_parent) and re.search(DRUG, raw):
            q = view._quote(c, '只补当前药物对象或本段确指对象，不继承宗旨、评价和措施')
            return {'established': True, 'current_anchors': [], 'context_evidence': [q], 'object_text': raw, 'role': 'same_paragraph_or_explicit_scope_drug_object', 'reason': '明确同段或适用范围仅解释药物对象'}
    if re.search('处方[^。；;]{0,25}(?:剂量|用法|配伍)|配伍禁忌|预防接种异常反应', unit.text):
        return {'established': True, 'current_anchors': [view.current_anchor(unit.a, unit.b)], 'context_evidence': [], 'role': 'explicit_medication_or_vaccine_harm_object'}
    return obj

def _se_parent_consumer_scope(view, unit):
    if unit.kind != 'parent_predicate':
        return True
    parents = [view.by_id.get(q.get('context_id')) for q in unit.contexts]
    parents = [c for c in parents if c and c.get('kind') == 'parent_paragraph']
    return not parents or all((view._se_parent_binding(c) for c in parents))
