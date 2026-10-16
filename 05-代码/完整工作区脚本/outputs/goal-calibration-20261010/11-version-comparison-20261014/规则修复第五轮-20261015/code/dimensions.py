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

from evidence import make_decision, matching_view, raw_span
from relations import same_component


DIMENSIONS = ("S", "E", "Ec", "I", "F")
# Closed consumer contract, derived from _units and the predicates below.
# Missing linked content cannot be classified by words in the current clause.
# These are possible consumers, not inferred topics of the absent material.
MATERIAL_REQUEST_CONSUMERS = {
    "substantive_list": DIMENSIONS,
    "cited_standard": DIMENSIONS,
    "named_mechanism": ("I", "F"),
    "price_arrangement": ("Ec",),
}
REQUEST_ROUTING_VERSION = "relation-consumer-routing-2-with-price-content"


class MaterialRequestRoutingError(ValueError):
    """An unresolved request without an exact consumer route is technical failure."""


def _material_request_route(request):
    if not isinstance(request, dict):
        raise MaterialRequestRoutingError("material request must be a concrete object")
    for key in ("path", "reference", "missing"):
        if not isinstance(request.get(key), str) or not request[key].strip():
            raise MaterialRequestRoutingError("material request lacks concrete " + key)
    path = request["path"]
    if path not in MATERIAL_REQUEST_CONSUMERS:
        raise MaterialRequestRoutingError("unallocated material request path: " + path)
    if (request.get("status", "unresolved") != "unresolved"
            or request.get("dependency_status", "stopped") != "stopped"
            or request.get("necessary_dependency", True) is not True):
        raise MaterialRequestRoutingError("material request is not a necessary unresolved dependency")
    consumers = MATERIAL_REQUEST_CONSUMERS[path]
    declared = []
    for key in ("dimensions", "affected_dimensions"):
        if key not in request:
            continue
        dims = request[key]
        if (not isinstance(dims, list) or not dims
                or any(not isinstance(dim, str) or dim not in consumers for dim in dims)
                or len(set(dims)) != len(dims)):
            raise MaterialRequestRoutingError("invalid material request " + key)
        declared.append(tuple(dim for dim in DIMENSIONS if dim in dims))
    if len(declared) == 2 and declared[0] != declared[1]:
        raise MaterialRequestRoutingError("conflicting material request dimension declarations")
    dims = declared[0] if declared else consumers
    return {"version": REQUEST_ROUTING_VERSION, "request": request,
            "relation_kind": path, "dimensions": list(dims),
            "basis": "validated_explicit_consumer_subset" if declared else "closed_relation_consumer_contract",
            "necessary_dependency_unresolved": True, "absent_source_topics_inferred": False}


MANUAL = {
    "S": "v1.3F-r1（2026-10-10冻结） §一、§二、§三",
    "E": "v1.3F-r1（2026-10-10冻结） §一、§二、§四",
    "Ec": "v1.3F-r1（2026-10-10冻结） §一、§二、§五",
    "I": "v1.3F-r1（2026-10-10冻结） §一、§二、§六、§九",
    "F": "v1.3F-r1（2026-10-10冻结） §一、§二、§七",
}
DRUG = r"药品|药物|用药|给药|制剂|片剂|胶囊|药费|新药|化学药|生物制品|中药|该药|本药|研究药|试验药|治疗药"
CONTENT_ACTION = r"评价|评估|比较|分析|研判|量化|分级|考察|测算|说明|描述|提供|提交|补充|报告|收集|核实|核对|确认|验证|证明|关注|讨论|要求|应包括|内容涉及"
FORM = r"字段[^。；;，,]{0,18}(?:不能为空|不得为空|非空|已填|填写完整)|(?:字符|文件|材料|字段|数据)(?:的)?格式|(?:签字|签章|盖章|账号|命名|归档|上传时间|递交时间|截止日期|截止时间)"
PURE_STRUCTURE = re.compile(r"^\s*(?:[（(]?[一二三四五六七八九十0-9]+[）)、.．]?\s*)?(?:如下|具体如下|包括以下内容|包括下列内容|包括以下|包括下列|具体包括|下列条件|以下条件|适用范围|申请资格|申请条件|申报流程|安全性|有效性|经济性|创新性|公平性)[:：]?\s*$")
TOPICS = {
    "S": r"安全性|用药安全|安全用药|药物风险|用药风险|不良反应|不良事件|毒性|毒理|肝损伤|禁忌|相互作用|药物警戒|用药差错|用药错误|风险管理|风险评估|风险识别|过敏史",
    "E": r"有效性|疗效|治疗效果|防治效果|临床获益|健康收益|健康获益|生存(?:期|率|获益)?|生命质量|生活质量|临床优势|疾病控制|有效(?:防治|治疗)(?:手段|药物|选择|选项)|药效|主要终点|药物作用反应|整体健康水平|无效(?:药物)?暴露",
    "Ec": r"经济性|药价|药品价格|价格|药品降价|药品涨价|药费|费用|成本|成本效果|成本效用|支付标准|支付范围|支付责任|报销|自付|基金支出|基金预算|预算影响|基金承受能力|基金(?:运行)?安全(?:为|作为)(?:底线|前提|约束)|支付资源|资源约束|按病种付费|DRG|DIP|销售金额|下调比例|降幅|供应成本",
    "I": r"创新性|创新点|创新程度|创新价值|原创|新颖|新作用机制|新靶点|新化合物|新分子实体|改良|改进|优化|创新药|首创新药|注册分类|[1-5一二三四五]类(?:化学药|治疗用生物制品|预防用生物制品|中药)|研发|研制|数据保护|市场独占",
    "F": r"公平|可及|可获得|可负担|负担不起|无力支付|买不起|治疗需要|用药需求|短缺|尚无有效|尚无药物获批|未满足|保障缺口|保障空白|断供|供应不稳定|配送|临床管理|吞咽|给药便利|目录|处方流转|雪中送炭|锦上添花",
}
NONDIM = {
    "S": r"基金安全|网络安全|信息安全|数据安全|一般生产安全|消防安全|办公安全",
    "E": r"账号有效期|协议有效期|文件有效期|数据有效性|格式有效|行政效能|审批效能|审评审批效能",
    "Ec": r"科研(?:项目)?经费|研究经费|设备采购(?:费|成本)?|行政收费|办公费用",
    "I": r"管理创新|制度创新|企业创新能力|产业创新发展|新质生产力",
    "F": r"企业竞争公平|公平竞争|廉政风险|利益冲突|工作纪律|程序公平|程序公正",
}
INNOVATION_OBJECT = r"创新药(?:物)?|创新型药物|改良型新药|首创新药|源头性创新[^。；;]{0,12}药物|药物创新|药品创新"
SUPPORT = r"资金|经费|研发资源|研究资源|审评资源|数据服务|数据产品|技术服务|技术培训|人员培训|专门审评团队|审评团队|审评人员|研究方案反馈|方案反馈|提出意见|提出建议|技术指导|支持机会|申请机会|研发便利|优先审评|加快通道|单独序列管理|缩短[^。；;]{0,12}(?:启动|审评)|(?:研究|试验|研发)(?:方案|设计)[^。；;]{0,15}(?:反馈|意见|建议)"
SUPPORT_ACTION = r"设立|建立|安排|组建|配置|提供|给予|开放|允许|可以|可申请|申请适用|纳入|组织开展|组织实施|实施|开展|终止|停止|取消|撤回|不再|不予|不得|禁止|不可|不能|限制|不适用|同意"
PAYMENT_CONTENT = r"支付标准|支付范围|支付责任|药品价格|药价|药费|治疗费用|药品费用|基金支出|基金预算|预算增幅|下调比例|降幅|成本|费用|报销|自付|销售金额"
PAYMENT_ACTION = r"制定|确定|调整|下调|上调|计算|测算|评价|分析|说明|确认|核对|核验|验证|提供|承担|支付|补偿|报销|限制|允许|可申请|方可|须申报|不超过|超过|不低于|降价|降低|控制|变化|负担"
OPPORTUNITY = r"优先审评|优先配置|优先保障|优先支持|针对性支持|可申请|可以申请|申请适用|申请加入|申请[^。；;]{0,15}(?:试点|支持|程序)|治疗机会|保障安排|资源配置|资源分配|补偿|援助|填补|弥补|保证[^。；;]{0,12}所需|保障[^。；;]{0,12}所需"
MODIFICATION_CHANGE = r"(?:改善|改良|改进|优化|改变|设计|开发)[^。；;]{0,25}(?:片剂|剂型|强度|给药途径|给药频次|释放|结构|包装|装置|口崩|掰断|注射器|给药器|吸入器)|(?:片剂|剂型|给药途径|给药频次|释放|结构|包装|装置|注射器|给药器|吸入器)[^。；;]{0,15}(?:改善|改良|改进|优化)|(?:注射|给药|吸入)(?:操作)?步骤[^。；;，,]{0,8}(?:简化|减少)|(?:注射器|给药器|吸入器)[^。；;，,]{0,12}(?:应易于|便于|可配有)"
TECHNICAL_QUALIFICATION = r"新作用机制|新靶点|新化合物|新分子实体|原创(?:性)?|新颖(?:性)?|原始创新|实质改良|实质改进|(?:与|相较|较)[^。；;，,]{0,30}(?:现有|已有|既有|对照|原有)[^。；;，,]{0,35}(?:临床优势|临床获益|疗效优势|治疗优势|安全性优势)|(?:现有|已有|既有|对照|原有)[^。；;，,]{0,20}(?:相比|比较)[^。；;，,]{0,30}(?:临床优势|临床获益|疗效优势|治疗优势|安全性优势)"
QUALIFICATION_CONSEQUENCE = r"(?:可|可以|允许|不得|不予|不再)[^。；;，,]{0,12}申请[^。；;]{0,30}(?:支持|反馈|优先|试点|程序|计划|机会|通道)|申请(?:适用|加入)[^。；;]{0,30}(?:支持|反馈|试点|程序|计划|通道)|(?:授予|给予|开放|终止|取消|撤回|限制|维持)[^。；;]{0,25}(?:支持机会|支持|待遇|权利|保护|准入|申请资格)|(?:支持|待遇|权利|保护|准入)[^。；;]{0,15}(?:终止|取消|撤回|限制|维持)"
PAYMENT_MODE = r"按病种付费|按疾病诊断(?:相关)?分组付费|DRG|DIP"
ACTUAL_ALLOCATION = r"(?:安排|配置|给予|予以|实行|实施|允许|开放|应当|可以|可)[^。；;，,]{0,25}(?:优先审评|优先保障|优先配置|优先支持|资源|资金|技术服务|反馈|支持机会|申请机会)|(?:可|可以|允许|不得|不予|不再)[^。；;，,]{0,8}申请|(?:直接|应当|可以|可|不得|不予|不再)(?:予以)?纳入[^。；;，,]{0,18}(?:优先审评|优先保障|优先配置|优先支持)|(?:可|可以|允许|不得|不予|不再)(?:在|于)[^。；;]{0,120}申请(?:适用|加入|优先|技术支持|研发支持|研究反馈|临床急需)"
GAPS = {
    "no_effective_option": r"(?:尚无|没有|不存在)有效(?:防治|治疗)(?:手段|药物|选择|选项)|(?:尚无|没有|已无)(?:标准|有效|可用)治疗(?:可供选择|选择|手段|方案|药物)",
    "no_domestic_approved_option": r"境内[^。；;]{0,12}尚无药物获批[^。；;]{0,20}适应症|境外已上市[^。；;]{0,8}境内未上市[^。；;]{0,15}药品|境内(?:无|尚无|未有)[^。；;]{0,12}获批[^。；;]{0,15}(?:药物|治疗选项)",
    "supply_gap": r"临床急需[^。；;]{0,12}短缺药品|药品(?:供应)?短缺|供药不足|药品供应不足|供应不稳定|时常断供|药品断供|药物断供|供药中断",
}


@dataclass
class Unit:
    text: str
    a: int
    b: int
    contexts: list[dict] = field(default_factory=list)
    kind: str = "current"
    details: dict = field(default_factory=dict)
    inherited: str = ""


def _hits(pattern: str, text: str):
    return list(re.finditer(pattern, text))


def _literal(anchor: Any) -> str:
    if isinstance(anchor, str):
        return anchor
    if isinstance(anchor, dict):
        return str(anchor.get("text", anchor.get("quote", "")))
    return ""


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def _context_text(unit: Unit) -> str:
    return "。".join(_norm(_literal(c)) for c in unit.contexts if _literal(c))


def _form_only(text: str, dimension: str) -> bool:
    # Filing compliance is not the substantive content of a safety report.
    # Do not suppress an independent risk/evidence assertion in another clause.
    if (dimension == "S" and re.search(
            r"(?:未|没有|未能)[^。；;，,]{0,12}(?:提交|报送|递交)[^。；;，,]{0,15}安全性(?:更新|总结)?报告", text)
            and not re.search(r"不良反应|不良事件|毒性|毒理|用药差错|药物风险|用药风险|"
                              r"(?:报告|资料)[^。；;，,]{0,8}(?:包括|应含|须含|缺少|显示)|(?:评价|评估|分析)[^。；;，,]{0,12}(?:药物|药品|安全性|风险|报告内容)", text)):
        return True
    # A content-scope requirement remains substantive even when its reporting
    # window is specified. A deadline attached only to submission does not.
    safety_cases = re.search(r"(?:死亡|SAE|严重不良事件|严重不良反应)病例", text, re.I)
    if (dimension == "S" and safety_cases
            and re.search(r"报告|小结|总结", text)
            and re.search(r"包括|纳入|覆盖|应酌情提供", text)):
        return False
    if not re.search(FORM, text):
        return False
    # Choosing a redacted file version is not an assessment of that content.
    topic_clauses = [part for part in re.split(r"[，,。；;]", text)
                     if re.search(TOPICS[dimension], part)]
    if (re.search(r"幻灯片|文件|材料", text) and re.search(r"版本|命名", text)
            and topic_clauses
            and all(re.search(r"(?:不含|删去|隐去|删除)[^。；;，,]{0,20}(?:" + TOPICS[dimension] + r")", part)
                    for part in topic_clauses)
            and not re.search(r"评价|评估|比较|分析|测算|核验", text)):
        return True
    candidates = [p for p in re.split(r"[，,]|或者|或(?=申报|字段|材料|文件|格式)", text)
                  if re.search(TOPICS[dimension], p)]
    if any(not re.search(FORM, part) for part in candidates):
        return False
    # A separate substantive requirement must target content, not a form noun.
    content = rf"(?:评价|评估|比较|分析|说明|核对|核验|确认|验证|补充|提供)[^。；;，,]{{0,20}}(?:{TOPICS[dimension]})"
    action = re.search(content, text)
    return action is None or bool(re.search(r"字段|格式|签章|签字|盖章", action.group()))


def _drug_safety_standard(text: str):
    """An actual criterion-setting action with drug risk and its test content."""
    return re.search(r"(?:制定|规定|确定|采用|执行|应当|须|必须)[^《》。；;，,]{0,20}(?:" + DRUG + r")"
                     r"[^《》。；;，,]{0,20}(?:风险|安全性|不良反应|毒性|毒理|禁忌|相互作用)"
                     r"[^《》。；;，,]{0,12}(?:评价|评估|监测|检验|检测|审核)"
                     r"[^《》。；;，,]{0,18}(?:标准|要求|指标|阈值|判据)", text)


def _publication_content_spans(text: str):
    """Return independent current content, or None for a non-enactment clause.

    Numbering is only stripped to locate the proposition; it never excludes a
    substantive clause. Purpose words without an actual document enactment are
    outside this boundary. Exact span offsets retain the full original record
    as current_proposition while nominating only its operative content.
    """
    prefix = r"(?:第[零〇一二两三四五六七八九十百千0-9]+条(?:第[零〇一二两三四五六七八九十百千0-9]+款)?|[（(]?[一二三四五六七八九十0-9]+[）)、.．])?"
    if not re.match(r"^\s*" + prefix + r"\s*(?:为了|为)", text):
        return None
    document_kind = r"指导原则|办法|程序|方案|规则|指南|规范|规定|规程|文件|通知|意见|细则|标准"
    # Publication may refer to this/that document or to its literal title.
    # A quoted title is consumed as a title, not as independently enacted
    # risk/evaluation content. The bounded unquoted name stops at its first
    # document noun so later operative requirements remain current content.
    document = (r"《[^《》。；;，,]{0,80}(?:" + document_kind + r")[^《》。；;，,]{0,12}》"
                r"|(?:本|该)[^《》。；;，,]{0,40}?(?:" + document_kind + r")"
                r"|[^《》。；;，,]{1,60}?(?:" + document_kind + r")")
    publication = re.search(r"(?:特)?(?:制定|印发|发布)(?:" + document + r")", text)
    if not publication:
        return None
    spans = []
    # Concrete standards are a current content relation when the clause
    # actually sets an evaluation/monitoring/testing criterion for drug risk.
    # Merely issuing a document whose title contains those words is distinct.
    # Earlier clauses may already assert a concrete problem or requirement.
    # Unmodalized purpose lists such as 促进/保障/提高 remain the document's
    # reasons, not independently enacted content or achieved outcomes.
    for part in re.finditer(r"[^，,。；;]+", text[:publication.start()]):
        s = part.group()
        requirement = re.search(r"(?:应当|应|须|必须|不得|禁止|要求|需要|需)[^。；;]{0,35}(?:" + CONTENT_ACTION + r"|审核|监测|控制|拒绝|调配|限制|配置|给予|开放)", s)
        problem = re.search(r"(?:" + DRUG + r")[^。；;]{0,25}(?:导致|造成|存在|发生)[^。；;]{0,25}(?:风险|不良反应|损伤|缺口|障碍|费用|成本|疗效|治疗效果)", s)
        enacted_action = re.search(r"(?:决定|同意|批准)(?:组织)?(?:开展|实施|设立|建立|开放|组建|配置|提供|给予)[^。；;]+", s)
        if requirement or problem or enacted_action or re.search(ACTUAL_ALLOCATION, s) or _drug_safety_standard(s):
            spans.append((part.start(), part.end()))
    if _drug_safety_standard(publication.group()):
        spans.append(publication.span())
    # A statement after enactment is independently current; the ordinary five
    # predicates still decide whether it expresses substantive content.
    for part in re.finditer(r"[^，,。；;]+", text[publication.end():]):
        spans.append((publication.end() + part.start(), publication.end() + part.end()))
    return spans


def _publication_purpose(text: str) -> bool:
    return _publication_content_spans(text) == []


def _substantive(text: str, dimension: str) -> bool:
    if _form_only(text, dimension) or PURE_STRUCTURE.fullmatch(text):
        return False
    if re.search(CONTENT_ACTION, text):
        return True
    if dimension == "S":
        return bool(re.search(r"导致|造成|减少|预防|控制|识别|监测|管理|警戒|不良反应|毒性|毒理|禁忌|用药差错|过敏史", text))
    if dimension == "E":
        return bool(re.search(r"改善|提高|提升|获益|优势|不足|尚无有效|没有有效|疗效|治疗效果|防治效果|疾病控制|(?:减少|避免|降低)[^。；;，,]{0,25}无效(?:药物)?暴露", text))
    if dimension == "Ec":
        return bool(re.search(PAYMENT_ACTION, text))
    if dimension == "I":
        return bool(re.search(r"具有|具备|缺乏|不同于|新作用机制|新靶点|新颖|原创|改良|改善|改进|设立|组建|提供|实施|开展|申请|续约|谈判|给予", text))
    return bool(re.search(r"负担不起|无力支付|买不起|可负担|不能获得|无法获得|难以获得|不平衡|差异|限制|保障|优先|申请|改善|优化", text))


def _payment_route_only(text: str) -> bool:
    """A current option routing action does not change its drug subject's payment.

    This is a proposition boundary, not a ban on selection/application words.
    Substantive payment selection, content checking, or authorization survives.
    A caller may include an actually direct parent payment-consequence predicate.
    """
    route = re.search(r"(?:选择|勾选|选用|填报|填写|进入)[^。；;，,]{0,20}(?:申报|申请)(?:条件|类别|模块|选项|渠道)|(?:申报|申请)(?:时|应|须)[^。；;，,]{0,15}(?:选择|勾选)[^。；;，,]{0,15}(?:条件|类别|模块|选项)", text)
    if not route:
        return False
    # A document noun is not its internal 说明 predicate. Keep real content
    # statements and direct budget/cost clarification as operative actions.
    content_action = r"核验|核对|确认|说明(?!书)|提供|提交|补充|评价|评估|比较|分析|测算|计算|制定|确定|承担|报销|补偿|控制|降低"
    actual_content = (re.search(rf"(?:{content_action})[^。；;，,]{{0,20}}(?:{PAYMENT_CONTENT})|(?:{PAYMENT_CONTENT})[^。；;，,]{{0,20}}(?:{content_action})", text)
                      or re.search(r"明确(?:药品|药物|治疗|用药|该药|本药)?(?:的)?(?:预算|费用)", text))
    authorization = re.search(rf"(?:可(?:以)?|允许|准许|不得|不能|方可|才能)[^。；;，,]{{0,18}}(?:调整|变更|制定|确定)[^。；;，,]{{0,18}}(?:{PAYMENT_CONTENT})", text)
    payment_selection = re.search(rf"(?:选择|选用|适用)[^。；;，,]{{0,15}}(?:{PAYMENT_CONTENT})", text)
    return not (actual_content or authorization or payment_selection)


def _non_drug_validity_spans(text: str):
    """Local noun→validity binding; a drug mentioned earlier is not its target."""
    nominal_target = r"注册证书|证书|文书|文件|资料|材料|数据|记录|字段|账号|账户|协议"
    return list(re.finditer(rf"(?:{nominal_target})(?:的|本身的|自身的)?有效性", text))


def _current_overall_health_effect(text: str) -> bool:
    """Require a current drug-effect relation for a broad overall-health phrase.

    General product-design/experience goals and baseline patient descriptions
    are not independent efficacy claims. Uncertain, negative or prospective
    drug-effect claims and explicit effect-evaluation requirements remain in.
    """
    if "整体健康水平" not in text:
        return False
    for part in re.findall(r"[^，,。；;]+", text):
        if "整体健康水平" not in part:
            continue
        baseline_only = re.search(r"入组前|治疗前|给药前|基线", part) and not re.search(r"治疗前后|给药前后|治疗后|给药后|用药后|服药后", part)
        if baseline_only:
            continue
        direct = re.search(r"(?:该药|本品|这种药物|该药物|药物治疗|药物|该治疗(?:方案)?)(?P<bridge>[^，,。；;]{0,25}?)(?:改善|提升|提高|降低|减少)[^，,。；;]{0,25}整体健康水平", part)
        if direct and not re.search(r"研发|开发|设计|体验|偏好", direct.group("bridge")):
            return True
        assessment = re.search(r"(?:评价|评估|比较|验证|确认|核实|测量)[^，,。；;]{0,20}(?:该药|本品|药物|该治疗|治疗前后|给药前后|治疗后|给药后)[^，,。；;]{0,35}整体健康水平", part)
        if assessment and re.search(r"影响|变化|改善|提高|提升|效果|差异", part) and not re.search(r"研发|开发|设计|体验|偏好", assessment.group()):
            return True
        if re.search(r"治疗前后|给药前后|治疗后|给药后|用药后|服药后", part) and re.search(r"整体健康水平[^，,。；;]{0,10}(?:变化|改善|提高|提升|差异)|(?:改善|提高|提升)[^，,。；;]{0,25}整体健康水平", part):
            return True
    return False


def _drug_effectiveness_topic(text: str) -> bool:
    administrative = _non_drug_validity_spans(text)
    return any(not any(span.start() <= topic.start() and topic.end() <= span.end() for span in administrative)
               for topic in re.finditer("有效性", text))


def _drug_content_determination(text: str, topic: str):
    pattern = rf"(?:确定|探明|查明|判明|判断)[^。；;，,]{{0,12}}(?:{DRUG})(?P<target_gap>[^。；;，,]{{0,12}}){topic}"
    non_drug_target = r"注册(?:证书|文件|资料|记录)|证书|文书|文件|资料|材料|数据|记录|字段|账号|账户|协议"
    for match in re.finditer(pattern, text):
        if re.search(non_drug_target, match.group("target_gap")):
            continue
        if topic == "有效性" and any(span.start() < match.end() and span.end() >= match.end()
                                    for span in _non_drug_validity_spans(text)):
            continue
        return match
    return None


def _object(view, unit: Unit) -> dict:
    obj = view.object_evidence(unit.a, unit.b)
    if not isinstance(obj, dict):
        raise TypeError("RelationView.object_evidence must return its source evidence")
    if obj.get("established"):
        return obj
    # Resolve the object of an actual adverse-case report through an explicit
    # same-source safety-report applicability statement. This adds the object
    # only; it never imports the document's topics into an unrelated clause.
    if (re.search(r"(?:死亡|SAE|严重不良事件|严重不良反应)病例", unit.text, re.I)
            and re.search(r"安全性(?:总结|更新)?报告", unit.text)
            and not re.search(r"医疗器械|器械研究", unit.text)):
        sha = view.unit.get("source_ref", {}).get("sha256")
        for ctx in view.contexts:
            scope = _norm(ctx.get("text", ""))
            if (sha and ctx.get("source_ref", {}).get("sha256") == sha
                    and ctx.get("kind") == "source_paragraph"
                    and same_component(view.unit, ctx)
                    and any(not re.search(r"医疗器械|不适用|不包括|不含|而非", m.group())
                            for m in re.finditer(r"(?<!不)(?:针对|适用于|面向)[^。；;，,]{0,60}(?:药品|药物|创新药|试验药)", scope))
                    and re.search(r"安全性资料|安全性(?:总结|更新)?报告", scope)):
                quote = view._quote(ctx, "同源明示安全性报告适用对象，仅用于解释当前病例报告对象")
                return {"established": True, "current_anchors": [],
                        "context_evidence": [quote], "object_text": ctx["text"],
                        "role": "explicit_same_source_safety_report_object",
                        "reason": "当前安全病例报告直接承接同源明示的药品安全资料适用对象。"}
    # Only linked quotations, never arbitrary available contexts, may resolve it.
    text = unit.text + "。" + unit.inherited + "。" + _context_text(unit)
    if unit.kind != "current" and re.search(DRUG, text):
        return {"established": True, "current_anchors": [],
                "context_evidence": unit.contexts, "object_text": text,
                "role": "legally_linked_drug_object", "reason": "对象由当前关系实际使用的来源引文补足。"}
    return obj


def _unique_contexts(items: list[dict]) -> list[dict]:
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def _review_condition_units(view):
    """A drug approval condition consumes the explicitly defined same review.

    Only a same-source adjacent definition is eligible. A general approval,
    title, or mention of another review never imports its evaluation topics.
    """
    condition = re.search(r"(?P<review>综合审评|技术审评)结论(?:不)?通过", view.norm)
    if not condition or not re.search(r"(?:综合审评|技术审评)结论(?:不)?通过[^。；;]{0,35}(?:批准|不予批准)药品上市", view.norm):
        return []
    sha = view.unit.get("source_ref", {}).get("sha256")
    if not sha:
        return []
    review = condition.group("review")
    matches = []
    for ctx in view.contexts:
        text = _norm(ctx.get("text", ""))
        if (ctx.get("kind") != "preceding_paragraph"
                or ctx.get("source_ref", {}).get("sha256") != sha
                or not same_component(view.unit, ctx)):
            continue
        definition = re.search(r"对药品(?:的)?(?:安全性|有效性)[^。；;]{0,65}进行" + re.escape(review), text)
        if not definition:
            continue
        _, offsets = matching_view(ctx["text"])
        quote = view._quote(ctx, "当前上市决定使用的同名审评结论，其直接前段明示实质评价内容",
                            raw_span(offsets, definition.start(), definition.end()))
        matches.append(Unit(definition.group(), 0, len(view.norm), [quote], "cited_standard",
                            {"relation_subtype": "adjacent_same_review_approval_condition",
                             "current_condition": condition.group(),
                             "source_sha256": sha}, view.norm))
    return matches if len(matches) == 1 else []


def _units(view) -> list[Unit]:
    # A pure enactment purpose cannot unfold the document's downstream rules.
    if _publication_purpose(view.norm):
        return []
    units = []
    for m in re.finditer(r"[^。；;]+", view.norm):
        text = _norm(m.group())
        spans = _publication_content_spans(text)
        if spans is None:
            units.append(Unit(text, m.start(), m.end()))
        else:
            units.extend(Unit(text[a:b], m.start() + a, m.start() + b)
                         for a, b in spans)
    for kind in ("parent_predicate", "substantive_list", "cited_standard", "named_mechanism", "policy_explanation", "price_arrangement"):
        for rel in view.linked(kind):
            details = dict(rel.get("details") or {})
            anchor = rel.get("current_anchor") or {}
            a = anchor.get("norm_start", details.get("norm_start", 0))
            b = anchor.get("norm_end", details.get("norm_end", len(view.norm)))
            if not isinstance(a, int) or not isinstance(b, int) or not 0 <= a < b <= len(view.norm):
                a, b = 0, len(view.norm)
            contexts = rel.get("context_evidence") or []
            current = view.norm[a:b]
            spans = _publication_content_spans(current)
            current_parts = [(0, len(current))] if spans is None else spans
            for start, end in current_parts:
                operative = current[start:end]
                if kind == "parent_predicate":
                    governing = _norm(details.get("shared_predicate") or details.get("content") or "。".join(_literal(c) for c in contexts))
                    units.append(Unit(operative, a + start, a + end, contexts, kind, details, governing))
                elif kind in {"substantive_list", "cited_standard"}:
                    for ctx in contexts:
                        content = _norm(_literal(ctx))
                        content_spans = _publication_content_spans(content)
                        parts = [(0, len(content))] if content_spans is None else content_spans
                        for left, right in parts:
                            if content[left:right]:
                                units.append(Unit(content[left:right], a + start, a + end, [ctx], kind, details, operative))
                else:
                    # Only I3 and concrete F inspect a named arrangement. The
                    # current operative projection cannot borrow purpose goals.
                    units.append(Unit(operative, a + start, a + end, contexts, kind, details,
                                      _norm(details.get("content") or "。".join(_literal(c) for c in contexts))))
    units.extend(_review_condition_units(view))
    return units


class Accumulator:
    def __init__(self, view):
        self.view = view
        self.positive = {d: [] for d in DIMENSIONS}
        self.excluded = {d: [] for d in DIMENSIONS}
        self.material = {d: [] for d in DIMENSIONS}
        self.material_routes = {d: [] for d in DIMENSIONS}
        self.errors = {d: [] for d in DIMENSIONS}

    def exclude(self, dim, unit, reason):
        if re.search(TOPICS[dim], unit.text) and reason not in self.excluded[dim]:
            self.excluded[dim].append(reason)

    def add(self, dim, unit, path, reason, obj, details=None):
        ce = _unique_contexts(unit.contexts + list(obj.get("context_evidence") or []))
        record = {"basis_path": path, "current_anchor": self.view.current_anchor(unit.a, unit.b),
                  "current_proposition": self.view.proposition(unit.a, unit.b),
                  "context_evidence": ce, "reason": reason,
                  "details": {"manual": MANUAL[dim], "relation_kind": unit.kind,
                              "object_evidence": obj, **(details or {})}}
        if record not in self.positive[dim]:
            self.positive[dim].append(record)

    def request(self, dim, reason):
        if reason not in self.material[dim]:
            self.material[dim].append(reason)

    def error(self, dim, reason):
        if reason not in self.errors[dim]:
            self.errors[dim].append(reason)

    def finish(self):
        # Material requests are generated by the shared relation resolver, not
        # by wishing for extra context for an otherwise complete proposition.
        for request in getattr(self.view, "material_requests", []):
            route = _material_request_route(request)
            for dim in route["dimensions"]:
                self.request(dim, request)
                if route not in self.material_routes[dim]:
                    self.material_routes[dim].append(route)
        for error in getattr(self.view, "implementation_errors", []):
            dims = error.get("dimensions", DIMENSIONS) if isinstance(error, dict) else DIMENSIONS
            for dim in dims:
                if dim in self.errors:
                    self.error(dim, error)
        failures = {d: errors for d, errors in self.errors.items() if errors}
        if failures:
            raise ValueError("implementation_error: " + repr(failures))
        out = {}
        for dim in DIMENSIONS:
            positives = self.positive[dim]
            if positives:
                first = positives[0]
                details = dict(first["details"])
                details["additional_evidence"] = positives[1:]
                details["near_candidate_exclusions"] = self.excluded[dim]
                details["unresolved_material_requests"] = self.material[dim]
                details["material_request_routes"] = self.material_routes[dim]
                details["implementation_errors"] = self.errors[dim]
                out[dim] = make_decision(1, first["basis_path"], first["current_anchor"],
                    first["current_proposition"], first["context_evidence"], first["reason"], details=details)
            elif self.material[dim]:
                specific = "；".join(
                    f"{item['path']}确指{item['reference']}：{item['missing']}"
                    if isinstance(item, dict) else str(item) for item in self.material[dim])
                out[dim] = make_decision(None, "material_insufficient", None, None, [],
                    "当前确指关系所必需的来源内容缺失，不能将未知记为0。" + specific,
                    needed_material=self.material[dim], details={"manual": MANUAL[dim],
                        "material_request_routes": self.material_routes[dim],
                        "implementation_errors": self.errors[dim]})
            else:
                reason = "；".join(self.excluded[dim][:4]) or "当前完整命题未表达本维的实质内容、证据要求或直接制度关系。"
                out[dim] = make_decision(0, "no_substantive_relation", None, None, [], reason,
                    details={"manual": MANUAL[dim], "near_candidate_exclusions": self.excluded[dim]})
        return out


def _generic(acc: Accumulator, unit: Unit, obj: dict):
    if unit.kind in {"named_mechanism", "policy_explanation", "price_arrangement"}:
        return
    text = unit.text
    for dim in DIMENSIONS:
        if not re.search(TOPICS[dim], text):
            continue
        if dim == "Ec" and _payment_route_only(text + ("。" + unit.inherited if unit.kind == "parent_predicate" else "")):
            acc.exclude(dim, unit, "当前只选择申报条件/类别等流程选项；支付调整属于对象身份，没有支付内容核验或授权后果。")
            continue
        if _form_only(text, dim):
            acc.exclude(dim, unit, "仅为字段、格式、签章或材料手续，未提出本维实质内容要求。")
            continue
        if PURE_STRUCTURE.fullmatch(text):
            acc.exclude(dim, unit, "只有栏目或组织性引导，没有本记录独立的实质要求。")
            continue
        if not obj.get("established"):
            acc.exclude(dim, unit, "候选词未建立药物、用药或药品治疗/支付对象。")
            continue
        if re.search(NONDIM[dim], text) and not re.search(rf"(?:药品|药物|用药)[^。；;，,]{{0,15}}(?:{TOPICS[dim]})", text):
            acc.exclude(dim, unit, "候选词指向行政、信息、基金、一般机构或程序对象。")
            continue
        # Information lists and contextual members can use their exact governing
        # content predicate. They cannot donate labels to unrelated siblings.
        governed = unit.kind in {"substantive_list", "cited_standard"}
        content = (_substantive(text, dim)
                   or (governed and re.search(CONTENT_ACTION + r"|符合|满足|条件|终止", unit.inherited))
                   or (unit.kind == "cited_standard" and unit.details.get("relation_subtype") == "adjacent_same_review_approval_condition"))
        general_word = {"S": r"安全性", "E": r"有效性", "Ec": r"经济性", "I": r"创新性|创新程度|创新价值", "F": r"公平性"}[dim]
        topic_content = re.search(general_word, text) and (dim != "E" or _drug_effectiveness_topic(text))
        if topic_content and content and (re.search(CONTENT_ACTION, text) or governed):
            if dim == "F" and re.search(NONDIM["F"], text):
                continue
            acc.add(dim, unit, "general_evaluation_or_information", "当前以药物/治疗为对象要求本维评价、比较或实质信息；具体机制未由概括词补写。", obj)


def _safety_effect(acc: Accumulator, unit: Unit, obj: dict):
    if unit.kind in {"named_mechanism", "policy_explanation", "price_arrangement"} or not obj.get("established"):
        return
    text = unit.text
    safety_standard = _drug_safety_standard(text)
    if safety_standard:
        acc.add("S", unit, "current_drug_safety_standard",
                "当前实际规定药物风险评价、监测或安全性检验标准；这是当前内容要求，不从制定文件的宗旨或书名推定。", obj,
                {"current_safety_standard": safety_standard.group()})
    if (unit.kind == "cited_standard"
            and unit.details.get("relation_subtype") == "operative_value_complete_definition"):
        safety_branch = re.search(r"(?:该药物|该药品|新药|药物|药品)[^。；;]{0,25}(?:具有|具备)[^。；;]{0,12}安全性优势", text)
        if safety_branch:
            acc.add("S", unit, "S_operative_value_condition_safety_branch",
                "当前操作性临床优势申请条件承接同版完整定义中的药物安全性优势分支；该安全条件用于资格判断，不从疾病严重程度或整篇宗旨推定安全议题。", obj,
                {"S_definition_branch": safety_branch.group(),
                 "S_current_condition": unit.details["current_criterion_anchor"],
                 "S_current_opportunity": unit.details["current_application_anchor"],
                 "S_connection": "operative criterion consumes exact same-edition complete definition"})
    # General goals and definitions are judged on what the current clause says.
    # These do not consume a full document purpose or donate labels to children.
    safety_goal = re.search(r"(?:保障|保证|确保|维护|保护|提升|提高|关注|强调)[^。；;，,]{0,18}(?:用药安全|安全用药)|(?:用药安全|安全用药)[^。；;，,]{0,15}(?:目标|要求|保障)", text)
    if safety_goal and not _form_only(text, "S"):
        acc.add("S", unit, "current_medication_safety_goal", "当前命题自身明示药物使用安全目标或要求；不由总则目的传播至程序成员，不推定损害或目标已实现。", obj,
                {"current_safety_goal": safety_goal.group()})
    for dim, topic in (("S", "安全性"), ("E", "有效性")):
        determination = _drug_content_determination(text, topic)
        form_target = re.search(rf"{topic}(?:的)?(?:资料|材料|文件|字段|名称|栏目|章节)[^。；;，,]{{0,18}}(?:收到|接收|已填|完整|非空|签字|签章|格式|名称|存在)", text)
        if determination and not _form_only(text, dim) and not form_target:
            acc.add(dim, unit, "current_drug_dimension_research_content", "当前定义或研究目标明确确定药物本维实质内容；一般试验名称、注册目的或研究身份不足，也不说明结论已成立。", obj,
                    {"current_content_determination": determination.group()})
    if re.search(TOPICS["S"], text) and _substantive(text, "S"):
        if re.search(NONDIM["S"], text) and not re.search(r"药物风险|用药风险|不良反应|用药差错|毒性|肝损伤", text):
            acc.exclude("S", unit, "安全指向基金、数据或一般机构，而非药物损害。")
        elif re.search(r"风险|不良反应|不良事件|毒性|毒理|禁忌|药物警戒|用药差错|用药错误|肝损伤|过敏史|相互作用", text):
            acc.add("S", unit, "drug_risk_content", "当前识别、评价、形成证据或控制药物/用药风险；议题成立不证明风险已经发生或控制已经有效。", obj)
    if re.search(TOPICS["E"], text) and _substantive(text, "E"):
        disease_definition = bool(re.search(r"(?:危及生命|影响生存质量|严重疾病)[^。；;]{0,20}是指", text)
                                  and not re.search(DRUG, text))
        if disease_definition:
            acc.exclude("E", unit, "疾病严重程度定义中的未治疗后果，没有判断药物防治效果。")
        elif re.search(NONDIM["E"], text) and not re.search(r"疗效|治疗效果|临床获益|防治效果", text):
            acc.exclude("E", unit, "有效性候选实际为有效期、格式或行政效能。")
        elif re.search(r"疗效|治疗效果|防治效果|临床获益|健康收益|健康获益|药效|疾病控制|明显临床优势|临床比较优势|(?:尚无|没有|不存在)有效(?:防治|治疗)(?:手段|药物|选择|选项)|(?:改善|延长|提高|降低|减少)[^。；;]{0,15}(?:生存|生命质量|生活质量|死亡|复发)", text) or _current_overall_health_effect(text):
            acc.add("E", unit, "drug_effect_or_effect_evidence", "当前涉及药物效果、健康收益、效果比较或有效治疗选项缺失；否定和不确定不改变议题在场。", obj)
        elif (re.search(r"给药方案|药物治疗|药品治疗", text)
              and (exposure := re.search(r"(?:减少|避免|降低)[^。；;，,]{0,12}(?:患者|受试者)[^。；;，,]{0,8}无效(?:药物)?暴露", text))
              and not _formal_relation_target(text, exposure)):
            acc.add("E", unit, "avoid_ineffective_drug_exposure",
                    "当前明确将患者的给药或药物治疗方案与减少无效暴露相连，属于治疗效果讨论，不表示已证明有效。", obj)
        elif re.search(r"(?:该|本)研究的主要终点[^。；;]{0,25}(?:验证|核实|确认)|效果估计[^。；;]{0,25}(?:验证|核实|确认)", text):
            if obj.get("context_evidence") and re.search(r"疗效|治疗效果|临床获益|有效性|减少[^。；;]{0,15}(?:骨折|死亡|复发)", str(obj.get("object_text", ""))):
                acc.add("E", unit, "explicit_effect_study_anaphor", "当前核验确指药物效果研究的实质终点，使用限定的同研究来源。", obj)
        else:
            acc.exclude("E", unit, "方法、疾病需要、用途或笼统临床价值未建立药物效果内容关系。")



def _formal_relation_target(text: str, relation) -> bool:
    """A cited economic/effect phrase labels a form or modifies a receipt.

    Inspect its immediate grammatical tail only: a separate substantive clause
    survives even when the same sentence also asks to upload a receipt.
    """
    tail = text[relation.end():]
    return bool(re.match(r"[’'\"”）)]*(?:的|这一|相关|相应)?(?:系统)?(?:凭证|票据|单据|字段|按钮|栏目|标题|名称|操作步骤|流程说明)", tail))


def _economics(acc: Accumulator, unit: Unit, obj: dict):
    if unit.kind in {"named_mechanism", "policy_explanation"} or not obj.get("established"):
        return
    text = unit.text
    payment_execution = re.search(
        r"(?:结算|支付|报销)[^。；;，,]{0,12}(?:药品费用|药费|用药费用|治疗费用)", text)
    drug_insurance_execution = (re.search(r"医保用药|药品目录|药品费用", text)
        and re.search(r"(?:结算|支付|报销)[^。；;，,]{0,12}医保费用", text))
    payment_expansion = re.search(
        r"(?:为|对)(?:相关|有关|这些|该类)?(?:创新药|药品|药物|新药)[^。；;，,]{0,8}(?:拓展|扩展|扩大|增加)[^。；;，,]{0,8}(?:支付空间|支付来源|支付渠道|支付资源)", text)
    if (payment_execution or drug_insurance_execution or payment_expansion) and not _form_only(text, "Ec"):
        for_payment = payment_execution or drug_insurance_execution or payment_expansion
        if _formal_relation_target(text, for_payment):
            payment_execution = drug_insurance_execution = payment_expansion = None
    if (payment_execution or drug_insurance_execution or payment_expansion) and not _form_only(text, "Ec"):
        relation = payment_execution or drug_insurance_execution or payment_expansion
        acc.add("Ec", unit, "current_drug_payment_execution_or_expansion",
                "当前直接规定药品治疗费用的结算支付，或明确扩展药品支付来源与资源；不推定患者公平或创新研发支持。", obj,
                {"current_payment_relation": relation.group()})
    # Deferring a separate rule does not enact its price/payment content.
    # This is a complete-proposition boundary, not an exclusion of future tense.
    specified_payment_content = re.search(
        r"不超过|不得超过|不能超过|不低于|高于|低于|合理|偏高|偏低|成本效果|成本效用|"
        r"(?:价格|费用|支付标准)[^。；;]{0,15}(?:上限|下限)|"
        r"(?:患者|家庭)[^。；;]{0,15}(?:收入|负担|自付)|"
        r"(?:评价|评估|比较|分析|测算|核验)[^。；;]{0,20}(?:价格|费用|成本|支付)|"
        r"(?:为|至)[0-9一二三四五六七八九十百千万]+(?:元|%|％)|百分之", text)
    if (re.fullmatch(r"[^。；;，,]{0,70}(?:规则|办法|细则)(?:另行|另作)(?:制定|规定|发布)[。]?", text)
            and not specified_payment_content):
        acc.exclude("Ec", unit, "当前仅说明另行制定规则，未设置具体价格、费用或支付内容。")
        return
    if unit.kind == "price_arrangement":
        if (unit.details.get("relation_subtype") == "same_edition_price_node_content_definition"
                and unit.details.get("version_binding", {}).get("established")
                and unit.details.get("direct_mapping") and unit.contexts):
            acc.add("Ec", unit, "Ec_actual_price_configuration_with_same_edition_definition",
                "当前价格协商分支承接同版评估确定协商价格并开展实际价格磋商的内容，属于药品价格配置；不要求给出新金额，不由推荐目录推定承保或支付范围。", obj,
                {"Ec_price_content": unit.details["price_definition"],
                 "Ec_current_price_branch": unit.details["current_branch_anchor"],
                 "Ec_connection": "same edition literal price-node/content mapping",
                 "Ec_source_object_content_chains": unit.details["price_object_content_chains"],
                 "payment_coverage_inferred": False})
        return
    direct_price = re.search(r"(?:根据|依据)[^。；;]{0,35}(?:评估|测算|确定)[^。；;]{0,20}(?:协商价格|药品价格)[^。；;]{0,25}(?:开展|进行)[^。；;]{0,15}(?:现场)?价格(?:协商|谈判|磋商)", text)
    if direct_price and not _form_only(text, "Ec"):
        acc.add("Ec", unit, "Ec_current_assessed_price_configuration",
            "当前明确依据评估/测算确定的药品价格开展实际协商或磋商，表达价格配置内容；金额缺省不使其变为普通资格手续，也不推出患者支付能力或支付范围。", obj,
            {"Ec_price_configuration": direct_price.group(), "payment_coverage_inferred": False})
        return
    binding = unit.details.get("table_cell_binding")
    if binding and re.fullmatch(r"\s*[¥￥]?[0-9]+(?:\.[0-9]+)?\s*(?:元|万元|亿元|%|％)?\s*", text):
        columns = binding.get("columns", [])
        if re.search(r"价格|单价|药费|费用|支付标准", unit.inherited + "。" + "。".join(str(c) for c in columns)):
            acc.add("Ec", unit, "same_column_treatment_price_value", "当前数值经同表、同列绑定属于药品价格/支付内容；不要求每个数据格重复制定或调整动词。", obj,
                    {"table_cell_binding": binding})
            return
    payment_parent = unit.kind == "parent_predicate" and re.search(r"支付标准|支付范围|支付责任|下调比例|" + PAYMENT_MODE, unit.inherited)
    if not re.search(TOPICS["Ec"], text) and not payment_parent:
        return
    payment_scope = text + ("。" + unit.inherited if unit.kind == "parent_predicate" else "")
    if _payment_route_only(payment_scope):
        acc.exclude("Ec", unit, "当前主行为仅为选择申报条件/类别，支付调整只界定药品对象；不继承相邻续约或协议的支付后果。")
        return
    if _form_only(text, "Ec"):
        acc.exclude("Ec", unit, "只要求经济字段的非空、格式或签约手续。")
        return
    if re.search(NONDIM["Ec"], text) and not re.search(r"药价|药费|药品价格|药品费用|支付标准|支付范围|基金支出", text):
        acc.exclude("Ec", unit, "费用是一般科研、设备或行政资源，未连接药品治疗/支付。")
        return
    payment_selection = re.search(r"(?:选择|选用|适用)[^。；;，,]{0,15}(?:药品价格|药价|支付标准|支付范围|支付责任)", text)
    if payment_selection:
        acc.add("Ec", unit, "current_substantive_payment_selection", "当前选择的直接对象是药品支付标准、范围、责任或价格内容，而非申报类别或模块；选择动词本身不构成排除。", obj,
                {"payment_content_selection": payment_selection.group()})
    mode = re.search(PAYMENT_MODE, payment_scope)
    mode_content = re.search(r"(?:不纳入|纳入|不适用|适用|豁免|排除)[^。；;，,]{0,20}(?:" + PAYMENT_MODE + r")|(?:" + PAYMENT_MODE + r")[^。；;，,]{0,12}(?:范围|标准|责任|范围外|例外)|(?:审核|评议|符合条件)[^。；;]{0,30}(?:支付|报销|补偿)", payment_scope)
    if mode and mode_content:
        acc.add("Ec", unit, "conditional_treatment_payment_mode", "当前规定药品治疗按病种等支付制度的范围、例外或审核条件后的支付安排；记录支付内容，不推定患者支付能力或已经获批。", obj,
                {"payment_mode": mode.group(), "payment_relation": mode_content.group()})
        return
    fund_capacity = re.search(r"(?:医保)?基金[^。；;，,]{0,12}(?:承受能力|支付能力|预算约束|资源约束|资金约束|预算压力)|(?:支付|基金)资源(?:有限|不足|约束)|(?:承受能力|预算约束|资源约束)[^。；;，,]{0,12}(?:医保)?基金|(?:以|将)?(?:医保)?基金(?:运行)?安全(?:为|作为)(?:底线|前提|约束)", text)
    directory_selection = re.search(r"药品目录[^。；;，,]{0,15}(?:选择|遴选|准入|纳入|调整|取舍|编制|制定)|(?:选择|遴选|纳入|进入|调整|准入|取舍)[^。；;，,]{0,20}(?:药品目录|目录[^。；;，,]{0,12}药品)", text)
    if fund_capacity and directory_selection:
        acc.add("Ec", unit, "fund_resource_constraint_drug_selection", "当前把明确基金承受/支付资源约束或基金安全底线连接药品目录选择或准入，属于药品支付资源内容；孤立基金安全或保基本导向不替代该关系，也不推出S/F。", obj,
                {"fund_constraint": fund_capacity.group(), "drug_selection": directory_selection.group()})
        return
    substantive_content = re.search(r"药费|药品价格|药价|治疗费用|药品费用|本药费用|该药费用|基金(?:实际)?支出|基金预算|预算增幅|预算影响|支付标准|支付范围|支付责任|下调比例|降幅|成本效果|成本效用|经济性|供应成本|患者自付|报销|销售金额", text)
    price_relation = re.search(r"(?:价格|费用|成本)[^。；;，,]{0,20}(?:合理|偏高|偏低|不超过|不得超过|不能超过|不低于|降低|增加|比较|为[0-9]|患者自付)|(?:降低|调整|确定|核验|确认|说明|比较|计算)[^。；;，,]{0,20}(?:价格|费用|成本)|明确(?:药品|药物|治疗|用药|该药|本药)?(?:的)?(?:预算|费用)|(?:控制|限定|限制|确定|调整)[^。；;，,]{0,25}(?:降价|涨价|降幅)(?:幅度)?", text)
    governed_information = (unit.kind in {"substantive_list", "cited_standard"}
                             and re.search(CONTENT_ACTION + r"|符合|满足|条件", unit.inherited)
                             and re.search(PAYMENT_CONTENT + r"|经济性|成本效果|成本效用", text))
    if ((substantive_content and _substantive(text, "Ec")) or price_relation or governed_information):
        acc.add("Ec", unit, "treatment_payment_content", "当前规定、讨论、比较或核验药品治疗/支付的价格、费用、责任、标准、范围或预算内容；已有内容核验无需新金额或变化。", obj)
    elif unit.kind == "parent_predicate" and re.search(r"支付标准|支付范围|支付责任|下调比例|" + PAYMENT_MODE, text + unit.inherited) and re.search(r"方可|可申请|须申报|确定|调整|支付|条件", unit.inherited):
        acc.add("Ec", unit, "condition_payment_consequence", "当前成员与直接父谓词组成指定支付内容的条件—变更/限制关系；必要条件不必充分，未假定已经批准。", obj)
    else:
        acc.exclude("Ec", unit, "只有谈判阶段、普通申报身份或未展开的协议/经济名称。")


def _classification(acc: Accumulator, unit: Unit, obj: dict):
    text = unit.text
    if not re.search(r"注册分类|注册类别|[1-5一二三四五]类(?:创新药|化学药|治疗用生物制品|预防用生物制品|中药)", text):
        return
    technical_definition = re.search(r"(?:创新药|改良型新药|创新型|改良型)[^。；;]{0,20}(?:是指|指的是|定义为|具体条件)", text)
    define = bool((technical_definition and re.search(r"新作用机制|新靶点|新颖|原创|未[^。；;]{0,10}上市|活性成分|临床优势|实质改良", text))
                  or re.search(r"(?:注册分类|注册类别)[^。；;]{0,20}(?:评价|判定|比较|说明)|(?:[12一二]类)[^。；;]{0,15}(?:为创新|为改良)", text))
    # A child may complete only a directly bound substantive consequence.
    consequence = bool(re.search(r"允许|可申请|可以申请|可不|可以|续约|重新谈判|给予[^。；;]{0,15}(?:待遇|权利|保护)|差异[^。；;]{0,12}(?:待遇|准入)|条件", text + unit.inherited)
                       and re.search(r"续约|谈判|支付|准入|待遇|权利|保护|支持机会", text + unit.inherited))
    if not (define or consequence):
        acc.exclude("I", unit, "分类/创新药仅界定对象或儿童、罕见病用途，没有技术分类内容或当前资格—实质后果关系。")
        return
    drug_types = re.findall(r"化学药品?|治疗用生物制品|预防用生物制品|中药", text)
    if not drug_types:
        acc.request("I", "明确使用分类资格，但缺对应药品种类，不能凭类别号判创新/改良含义。")
        return
    # The supplied manual §九 expressly binds this round's present registration
    # standard references to the 2020-onward definitions. No private registry is
    # loaded; a bare number or unspecified historical standard is not covered.
    period = bool(re.search(r"现行药品注册管理办法及注册分类标准|202[0-9]年|202[0-9]-|202[0-9]年起", text + unit.inherited + _context_text(unit))
                  or unit.details.get("classification_period_verified"))
    if not period:
        acc.request("I", "当前分类的適用时期未明确；需同版药类分类定义，不能套用手册2020起类别。")
        return
    qualifies = re.search(r"(?:[12一二]类(?:化学药品?|治疗用生物制品|预防用生物制品|中药|创新药|改良型新药)|[12一二]类和[3三]类中药)", text)
    if qualifies:
        acc.add("I", unit, "I4_classification_content_or_treatment", "当前使用已限定药类/时期的创新或改良分类内容/资格决定实质待遇；分类定义据共同手册§九，混合中药3类不因此成为技术创新，也不证明临床优越。", obj,
                {"classification_source": "supplied common manual §九", "drug_types": drug_types,
                 "classification_anchor": qualifies.group(), "definition_or_consequence": "definition" if define else "qualification_consequence"})
    else:
        acc.exclude("I", unit, "已知类别未明确对应创新/实质改良，不能把所有新药类别纳入I。")


def _finite_reference_qualification(acc: Accumulator, unit: Unit, obj: dict):
    """Consume only a source-resolved finite current condition→right relation."""
    if unit.kind != "cited_standard" or unit.details.get("relation_subtype") != "finite_operational_article_reference":
        return
    condition = _norm(_literal(unit.details.get("current_condition_anchor")))
    consequence = _norm(_literal(unit.details.get("current_consequence_anchor")))
    chain = unit.details.get("reference_chain")
    if not (condition and consequence and condition in acc.view.norm and consequence in acc.view.norm
            and isinstance(chain, list) and 1 <= len(chain) <= 2
            and re.search(r"符合|满足|不符合|未满足|条件", condition)
            and re.search(r"数据保护期[^。；;，,]{0,15}(?:为|给予|享受)|(?:给予|享受|授予|维持|限制|取消|不予)[^。；;，,]{0,25}(?:保护|权利|许可|准入|待遇)", consequence)):
        return
    qualified_contexts = unit.details.get("qualification_context_evidence") or []
    if qualified_contexts and not any(_norm(_literal(c)) == unit.text for c in qualified_contexts):
        return
    # A comparative new-data scope tied to known active products expresses the
    # improvement qualification itself, rather than assigning novelty to every
    # drug with a protection right or general efficacy advantage.
    comparative_new_data = (re.search(r"已知活性成[分份]|既有活性成[分份]|已上市生物制品", unit.text)
                            and re.search(r"相比|比较|相较", unit.text)
                            and re.search(r"明显临床优势|实质临床优势", unit.text)
                            and re.search(r"新(?:的)?临床试验数据", unit.text))
    innovation_object = re.search(INNOVATION_OBJECT + r"|改良型药品",
                                  unit.text + "。" + str(unit.details.get("object_definition", ""))
                                  + "。" + str(unit.details.get("qualification_text", "")))
    technical_condition = re.search(TECHNICAL_QUALIFICATION, unit.text)
    if not (comparative_new_data or (innovation_object and technical_condition)):
        return
    acc.add("I", unit, "I4_finite_operative_improvement_data_scope", "当前精确条款条件决定保护/准入等实质权利，有限同源条件范围明确技术创新或相较已知活性产品的临床优势新数据资格；记录资格的制度使用，不因原研身份或权利存在赋I，也不称已证优效或I3。", obj,
            {"current_condition": unit.details["current_condition_anchor"],
             "current_consequence": unit.details["current_consequence_anchor"],
             "reference_chain": chain, "qualification_source": "source-resolved finite operative condition scope",
             "technical_or_comparative_condition": unit.text})


def _innovation_qualification(acc: Accumulator, unit: Unit, obj: dict):
    """Nonnumeric technical/comparative eligibility, not program identity."""
    if unit.kind in {"named_mechanism", "policy_explanation"}:
        return
    qualification = re.search(TECHNICAL_QUALIFICATION, unit.text)
    if not qualification:
        return
    obj_text = str(obj.get("object_text", ""))
    innovation = re.search(INNOVATION_OBJECT, unit.text + "。" + unit.inherited + "。" + obj_text)
    if not innovation:
        return
    bound = unit.kind in {"parent_predicate", "substantive_list", "cited_standard"}
    relation_text = unit.text + ("。" + unit.inherited if bound else "")
    consequence = re.search(QUALIFICATION_CONSEQUENCE, relation_text)
    if not consequence:
        return
    # The member/source itself supplies the technical/comparative condition.
    # The parent/current operative reference supplies only its current consequence.
    details = {"innovation_object": innovation.group(),
               "technical_or_comparative_condition": qualification.group(),
               "qualification_consequence": consequence.group(),
               "qualification_source": "legally linked complete same-version standard" if unit.kind == "cited_standard" else "current or direct member content"}
    acc.add("I", unit, "I1_innovation_linked_comparative_value", "当前具体技术/临床比较条件与明确创新或改良对象相连，并用于当前支持资格或实质机会；这是属性/价值内容，不宣称条件已经满足或药品已经优效。", obj, details)
    acc.add("I", unit, "I4_substantive_qualification_opportunity", "当前技术/临床比较资格决定申请、授予、维持或限制具体支持/准入待遇；合法操作性援引可读取同版完整条件，无须把资格缩为数字注册类别。", obj, details)


def _innovation(acc: Accumulator, unit: Unit, obj: dict):
    if unit.kind in {"policy_explanation", "price_arrangement"}:
        return
    text = unit.text
    if unit.details.get("relation_subtype") == "bounded_pilot_research_service_scope":
        roles = _pilot_support_roles(acc.view, unit)
        if obj.get("established") and roles:
            acc.add("I", unit, "I3_bounded_pilot_service_or_exclusion",
                    "当前要求同一创新药试点具备申请前实质服务制度，或规定不满足确认条件者不获得该试点支持机会；完整同版对象及例外、缩短启动安排均已核明。限制不表示项目已经获得支持，普通申请渠道不被说成试点待遇。", obj,
                    {"mode": roles["mode"], "current_action": unit.details["current_action_anchor"],
                     "complete_eligibility": unit.details["complete_eligibility_quotes"],
                     "innovation_objects": unit.details["innovation_object_quotes"],
                     "support_quotes": unit.details["support_quotes"],
                     "action_scope": unit.details["action_scope_quotes"],
                     "excluded_from_pilot_support": unit.details.get("excluded_from_pilot_support", False)})
        return
    if unit.details.get("relation_subtype") == "bounded_statutory_postadmission_support":
        roles = _statutory_support_roles(acc.view, unit)
        if obj.get("established") and roles and re.search(r"(?<!非)(?:创新药|改良型新药|创新疫苗)", roles["innovation"]):
            acc.add("I", unit, "I3_current_statutory_research_support",
                    "当前对已纳入同一程序的对象规定技术沟通、研究反馈或经同对象普通时限对照确认的优先待遇；同版完整资格明确包含创新研发分支。" + roles["direction_reason"] + "不将全部纳入对象均认定创新，也不把期限数字本身当支持证据。", obj,
                    {"current_support_mode": roles["mode"], "current_support_anchor": unit.details["current_support_anchor"],
                     "support_direction": roles["direction"], "positive_delivery": unit.details.get("positive_delivery"),
                     "current_restriction_quotes": unit.details.get("current_restriction_quotes", []),
                     "complete_eligibility": unit.details["complete_eligibility_quotes"], "admission_bridge": unit.details["admission_bridge_quotes"],
                     "current_support_quotes": unit.details["current_support_quotes"], "deadline_comparison": unit.details["deadline_comparison_quotes"]})
        return
    if unit.details.get("relation_subtype") == "bounded_trial_admission_support":
        roles = _trial_admission_roles(acc.view, unit)
        if (obj.get("established") and roles
                and re.search(r"(?<!非)(?:首创新药|创新药|改良型新药)|新作用机制/新靶点", roles["innovation"])):
            acc.add("I", unit, "I3_actual_admission_to_defined_research_support",
                    "当前实际授予同一试点纳入机会，同版完整资格包含明确创新研发对象、早期阶段和例外，纳入后可使用持续研发技术沟通。记录支持机会，不称已完成技术创新或所有对象均无药可用。", obj,
                    {"current_admission": unit.details["current_admission_anchor"],
                     "support_quotes": unit.details["support_quotes"],
                     "complete_eligibility": unit.details["eligibility_quotes"],
                     "research_stage_quotes": unit.details["research_stage_quotes"]})
        return
    if (unit.kind == "named_mechanism"
            and unit.details.get("relation_subtype") == "bounded_data_protection_rights_consequence"):
        details = unit.details
        current = _norm(_literal(details.get("current_rights_anchor", {})))
        definition = "。".join(_norm(_literal(q)) for q in details.get("definition_quotes", []))
        entitlement = "。".join(_norm(_literal(q)) for q in details.get("innovation_entitlement_quotes", []))
        if (obj.get("established") and details.get("version_binding", {}).get("established") is True
                and details.get("scope_binding", {}).get("context_ids")
                and current and current in acc.view.norm
                and details.get("action_mode") in {"protection_application", "expiry_conditioned_market_permission", "termination_releases_market_permission"}
                and re.search(r"数据保护|受保护数据", definition)
                and re.search(r"(?<!非)(?:创新药|改良型新药)", entitlement)
                and re.search(r"保护期|保护期限|数据保护", entitlement)):
            acc.add("I", unit, "I4_same_protection_rights_consequence",
                    "当前实际申请、维持届满前限制或在终止后解除同一药品数据保护的准入权利；同源完整定义及创新权益分支明确该权利与创新资格的联系。不把竞争申请认定为创新，不把权利咨询说成研发技术反馈。", obj,
                    {"action_mode": details["action_mode"], "current_rights_anchor": details["current_rights_anchor"],
                     "definition_quotes": details["definition_quotes"], "innovation_entitlement_quotes": details["innovation_entitlement_quotes"],
                     "scope_binding": details["scope_binding"], "version_binding": details["version_binding"]})
        return
    if not obj.get("established") or not re.search(TOPICS["I"] + "|" + SUPPORT + "|" + MODIFICATION_CHANGE + "|" + TECHNICAL_QUALIFICATION, text + (unit.inherited if unit.kind == "named_mechanism" else "")):
        return
    if _form_only(text, "I") or PURE_STRUCTURE.fullmatch(text):
        acc.exclude("I", unit, "创新候选只处于字段、手续或结构引导，没有实质内容关系。")
        return
    if unit.kind != "named_mechanism":
        if re.search(r"新作用机制|新靶点|新化合物|新分子实体|原创(?:性)?|新颖(?:性)?|原始创新", text) and _substantive(text, "I"):
            acc.add("I", unit, "I1_technical_novelty", "当前实质讨论、定义或要求技术新颖性/原创性内容；否定或待证判断不被改写为已具优势。", obj)
        change = re.search(MODIFICATION_CHANGE, text)
        obstacle = re.search(r"吞咽困难|吞咽障碍|难以吞咽|掰断[^。；;]{0,12}(?:困难|不便|障碍)|难以掰断|操作障碍|操作困难|使用障碍|(?:记忆和)?操作负担|现有[^。；;]{0,15}(?:局限|不足)|难以(?:打开|使用|操作)|(?:手指灵活性|手指功能|手部功能)[^。；;]{0,45}(?:影响|限制)[^。；;]{0,20}(?:掰断|片剂|操作)|(?:掰断|片剂操作)[^。；;]{0,35}(?:受[^。；;]{0,12}(?:手指|手部)|手指灵活性[^。；;]{0,12}影响)", text + "。" + unit.inherited)
        improvement = re.search(r"缓解|改善|减少|降低|解决|克服|便利|便于|更易|提高[^。；;]{0,8}(?:表现|能力)|实质改良", text)
        if re.search(r"实质改良|实质改进", text) or (change and obstacle and improvement):
            acc.add("I", unit, "I2_substantive_modification", "当前具体设计/改变与原文明确的治疗或使用局限、操作障碍及改善关系相连；这记录改良议题，不证明已有效或优效。", obj)
        elif change:
            acc.exclude("I", unit, "仅产品属性变化或一般设计优化，未表达实质改良或明确局限—改变—改善关系。")
        _classification(acc, unit, obj)
        _finite_reference_qualification(acc, unit, obj)
        _innovation_qualification(acc, unit, obj)
    # A guideline's general instruction is not a service supplied to projects.
    public_guidance = bool(re.search(r"本指导原则|技术指导原则|技术指南|本指南", text)
                           and re.search(r"起草|制定|提出[^。；;]{0,20}考虑|提供指导|设计考虑", text)
                           and not re.search(r"反馈|审评团队|人员培训|技术培训|咨询服务|可申请[^。；;]{0,15}(?:反馈|技术服务)", text))
    if public_guidance:
        acc.exclude("I", unit, "公共指南的设计/风险规范未另设创新研发可使用的服务、反馈或支持机会，不能以普遍指导功能记I3。")
        return
    if _publication_purpose(text) and unit.kind != "named_mechanism":
        acc.exclude("I", unit, "当前仅说明制定/发布文件的创新宗旨，没有本句独立的可用支持安排。")
        return
    obj_text = str(obj.get("object_text", ""))
    combined = text + "。" + unit.inherited
    innovation = re.search(INNOVATION_OBJECT, text + "。" + obj_text + "。" + unit.inherited)
    resource = re.search(SUPPORT, combined)
    if (unit.kind == "named_mechanism"
            and unit.details.get("relation_subtype") == "bounded_primary_postadmission_technical_support"):
        # The resolver proves current postadmission service and a direct bounded
        # technical opportunity. I3 support and F priority use separate gates.
        resource = re.search(r"(?:补充提交技术资料|研究方案反馈|试验方案反馈|研发技术咨询)[^。；;]{0,20}(?:沟通交流申请|技术咨询申请)",
                             _norm(unit.details.get("direct_mechanism", "")))
        if resource is None:
            resource = re.search(r"(?:在审评中|审评过程中)[^。；;]{0,65}(?:沟通交流|技术咨询|研究反馈)[^。；;]{0,30}优先(?:安排|处理|提供)",
                                 _norm(unit.details.get("direct_mechanism", "")))
        # A programme title containing 创新药 is not its eligible support object.
        # Only positive branches under the programme's actual applicability
        # predicate can establish this I3 object; exclusion branches cannot.
        innovation = re.search(INNOVATION_OBJECT, "。".join(
            _norm(_literal(e)) for e in unit.details.get("innovation_eligible_branches", [])))
    if (resource is None and unit.kind == "named_mechanism"
            and unit.details.get("relation_subtype") == "bounded_primary_qualification_support_roles"):
        # This literal resource form is accepted only after the resolver proves
        # same-programme object, current review and explicit withdrawal bridge.
        resource = re.search(r"优先配置[^。；;]{0,15}资源[^。；;]{0,20}(?:沟通交流|技术服务|研究方案反馈|研发)",
                             _norm(unit.details.get("direct_mechanism", "")))
    action = re.search(SUPPORT_ACTION, text + ("。" + unit.inherited if unit.kind == "parent_predicate" else ""))
    actual_rnd = bool(re.search(r"研发|研制|研究方案|试验方案|临床试验|上市前|申报前", text + obj_text + unit.inherited))
    bounded_team_execution = (
        unit.kind == "named_mechanism"
        and unit.details.get("relation_subtype") == "bounded_specialized_team_execution"
        and unit.details.get("version_binding", {}).get("established") is True
        and bool(unit.details.get("scope_binding", {}).get("context_ids"))
        and bool(unit.details.get("current_execution_anchor"))
        and bool(unit.details.get("research_stage"))
    )
    if bounded_team_execution:
        # Consume only the resolver's same-component innovation scope and
        # technical execution. An arbitrary team or administrative workflow
        # cannot use the scope of the entire source document as support.
        innovation = re.search(INNOVATION_OBJECT, _norm(unit.details.get("object_definition", "")))
        resource = re.search(r"审评团队|审评人员", text)
        action = re.search(r"解决[^。；;，,]{0,15}技术问题", text)
        actual_rnd = bool(re.search(r"上市前|申报前|研发|研制|临床试验", _norm(unit.details.get("research_stage", ""))))
    if (unit.kind == "named_mechanism"
            and unit.details.get("relation_subtype") == "bounded_primary_postadmission_technical_support"):
        action = re.search(r"进行|开展|提供|安排|(?:提出|提交)[^。；;]{0,35}(?:沟通交流|技术咨询)(?:的)?申请", text)
        mode = unit.details.get("current_service_mode")
        bounded_current = (unit.details.get("scope_binding", {}).get("context_ids")
                           and unit.details.get("current_service_anchor"))
        if bounded_current and mode == "confirmed_technical_submission":
            action = re.search(r"(?:同意|确认)[^。；;]{0,25}(?:提交|补充)[^。；;]{0,12}技术资料", text)
        elif bounded_current and mode == "programme_admission":
            action = re.search(r"(?:即|将|应|予以|可以)[^。；;，,]{0,4}纳入", text)
        actual_rnd = bool(resource and unit.details.get("research_stage")
                          and unit.details.get("current_service_anchor"))
    routine_after_marketing = bool(re.search(r"上市后[^。；;]{0,18}(?:常规|日常)[^。；;]{0,18}(?:用药监测|临床服务|处方|治疗管理)|常规(?:用药监测|临床服务)", text)
                                   and not re.search(r"(?:进一步|继续|后续)[^。；;]{0,15}(?:创新|改良)?(?:研发|研制)|服务于[^。；;]{0,20}(?:创新|改良)[^。；;]{0,12}(?:研发|研制)", text))
    if routine_after_marketing:
        acc.exclude("I", unit, "当前实际用途是上市后常规监测/临床服务，没有进一步创新研发支持联系，不能从创新适用范围继承I3。")
        return
    team_resource = resource and re.search(r"审评团队|审评人员", resource.group())
    if team_resource:
        explicit_service = re.search(r"(?:审评团队|审评人员|团队)[^。；;]{0,30}(?:负责|承担|提供)[^。；;]{0,40}(?:研究方案反馈|试验方案反馈|研发技术服务|研发技术咨询)", combined)
        whole_review_service = (re.search(r"(?:负责|承担)[^。；;]{0,40}申报前[^。；;]{0,30}沟通[^。；;]{0,35}技术审评[^。；;]{0,15}全过程", combined)
                                and re.search(r"相对稳定|保持稳定|人员稳定|团队稳定", combined))
        if not (explicit_service or whole_review_service or bounded_team_execution):
            acc.exclude("I", unit, "组建/配置团队只是资源候选，尚无当前或确指同段的具体研发技术服务定义；创新scope不能代替服务内容。")
            resource = None
    if unit.kind == "parent_predicate" and resource and not re.search(SUPPORT, text):
        # A general disease or process subcondition is not itself an arrangement.
        if not re.search(INNOVATION_OBJECT + "|" + TECHNICAL_QUALIFICATION, text):
            resource = None
    scientific_function = bool(re.search(r"(?:本|该)(?:项目|计划|试点工作)[^。；;]{0,35}(?:核心目的|目的)|试点工作的核心目的", text)
                               and re.search(r"(?:解决|探讨解决|帮助解决)[^。；;]{0,45}(?:研发|研究)[^。；;]{0,15}科学问题", text))
    if innovation and actual_rnd and ((resource and action) or scientific_function):
        if re.search(r"申请人[^。；;]{0,30}(?:收集|更新|报送|提交)[^。；;]{0,25}(?:安全资料|风险管理|文件)", text) and not re.search(r"(?:给予|配置|提供)[^。；;]{0,20}(?:反馈|团队|资源|技术服务)", text):
            acc.exclude("I", unit, "当前是申请人的一般义务，不因创新对象转为研发支持。")
            return
        acc.add("I", unit, "I3_actual_innovative_research_support", "当前设立、实施、开放、限制或撤回明确创新/改良研发可使用的资源、服务、反馈、便利或支持机会；当前行动与支持对象直接相连。", obj,
                {"I3_object": innovation.group(), "I3_arrangement": resource.group() if resource else "项目明确解决创新研发科学问题的支持功能",
                 "I3_connection": "current and legally linked quoted object/arrangement", "support_action": action.group() if action else "具体项目支持功能",
                 **({"I3_role_evidence": {"current_service_bridge": unit.details["current_service_bridge"],
                     "object": unit.details["innovation_eligible_branches"],
                     "object_applicability_scope": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "object_and_need_eligibility"],
                     "priority_is_not_required_for_I3": True,
                     "technical_material_branch_is_not_required_for_F": True,
                     "postadmission_priority_technical_communication": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "postadmission_priority_technical_communication"],
                     "postadmission_technical_material_feedback": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "postadmission_technical_material_feedback"],
                     "preapplication_mechanism_inherited": False}}
                    if unit.details.get("relation_subtype") == "bounded_primary_postadmission_technical_support" else {}),
                 **({"I3_role_evidence": {"current_bridge": unit.details["current_qualification_bridge"],
                     "object": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "object_and_eligibility_definition"],
                     "available_priority_support": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "priority_research_support"],
                     "direct_withdrawal": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "withdrawal_direct_mechanism"]}}
                    if unit.details.get("relation_subtype") == "bounded_primary_qualification_support_roles" else {})})
    elif re.search(r"创新药|支持|鼓励|研发|研制|数据保护", text):
        acc.exclude("I", unit, "只有创新身份、一般鼓励、程序/沟通形式或权利存在，未同时建立创新研发对象、可用安排及直接联系。")


def _fairness(acc: Accumulator, unit: Unit, obj: dict):
    if unit.details.get("relation_subtype") == "bounded_pilot_research_service_scope":
        return
    text = unit.text
    if unit.details.get("relation_subtype") == "bounded_statutory_postadmission_support":
        roles = _statutory_support_roles(acc.view, unit)
        if (obj.get("established") and roles
                and re.search(r"尚无有效(?:防治|治疗)手段|临床急需的短缺药品|疾病预防[、,，]控制急需", roles["need"])):
            acc.add("F", unit, "current_statutory_support_with_unmet_need_branch",
                    "当前同一程序支持的设置或限制承接完整资格中明确的无有效治疗、短缺或防控急需分支。" + roles["direction_reason"] + "保留其他适用分支和例外，不称全部对象均有治疗缺口，也不以一般提速单独推出公平。", obj,
                    {"current_support_mode": roles["mode"], "current_support_anchor": unit.details["current_support_anchor"],
                     "support_direction": roles["direction"], "positive_delivery": unit.details.get("positive_delivery"),
                     "current_restriction_quotes": unit.details.get("current_restriction_quotes", []),
                     "complete_eligibility": unit.details["complete_eligibility_quotes"], "need_branches": unit.details["need_eligible_branches"],
                     "current_support_quotes": unit.details["current_support_quotes"], "deadline_comparison": unit.details["deadline_comparison_quotes"]})
        return
    if unit.details.get("relation_subtype") == "bounded_trial_admission_support":
        roles = _trial_admission_roles(acc.view, unit)
        if (obj.get("established") and roles
                and re.search(r"境内尚无药物获批[^。；;]{0,20}适应症", roles["need"])
                and unit.details.get("all_participants_have_unmet_need") is False):
            acc.add("F", unit, "actual_trial_admission_with_unmet_need_branch",
                    "当前实际纳入机会承接同一试点完整资格，其中一项明确面向境内尚无获批药物的治疗缺口，并提供持续研发服务；保留其他OR分支和共同限定，不称所有纳入者都缺少治疗。", obj,
                    {"current_admission": unit.details["current_admission_anchor"],
                     "complete_need_branches": unit.details["need_eligible_branches"],
                     "complete_eligibility": unit.details["eligibility_quotes"],
                     "support_quotes": unit.details["support_quotes"],
                     "all_participants_have_unmet_need": False})
        return
    if unit.kind == "price_arrangement":
        return
    if not obj.get("established") or _form_only(text, "F"):
        return
    if re.search(NONDIM["F"], text):
        acc.exclude("F", unit, "公平指向企业竞争、廉政或办理程序，未表达患者药品机会关系。")
        return
    combined = text + "。" + unit.inherited
    affordability = re.search(r"(?:患者|家庭|人群|参保人)[^。；;]{0,25}(?:可负担|能否负担|是否负担|负担不起|无力支付|买不起)|(?:药品|药物|用药|治疗)[^。；;]{0,12}可负担性|可负担性[^。；;]{0,20}(?:药品|药物|用药|治疗)|(?:药费|药品费用|治疗费用|用药费用)[^。；;]{0,20}(?:低收入|困难|贫困)(?:患者|家庭)[^。；;]{0,12}负担", text)
    if affordability and _substantive(text, "F"):
        acc.add("F", unit, "F_patient_affordability", "当前实质涉及患者能否负担所需药品治疗；该命题已含费用与支付能力关系，不补造收入或已改善效果。", obj,
                {"F_object": "患者药品治疗及持续接受", "F_relation": affordability.group()})
    if (unit.kind == "named_mechanism"
            and unit.details.get("relation_subtype") == "bounded_need_linked_inspection_deferral"
            and unit.details.get("version_binding", {}).get("established") is True
            and unit.details.get("scope_binding", {}).get("context_ids")
            and unit.details.get("current_deferral_anchor")
            and unit.details.get("scope_binding", {}).get("inspection_kind") == "药品注册核查"):
        object_scope = _norm(unit.details.get("object_definition", ""))
        baseline = _norm(_literal(unit.details.get("baseline_before_review_quote", {})))
        scope_gaps = [(k, re.search(p, object_scope)) for k, p in GAPS.items()]
        scope_gaps = [(k, m) for k, m in scope_gaps if m]
        after = re.search(r"上市审批后[^。；;]{0,30}(?:可以|可)[^。；;]{0,30}药品注册核查", text)
        before = re.search(r"审评时限届满[^。；;]{0,20}日前完成核查", baseline)
        if scope_gaps and after and before and "药品注册核查" in baseline:
            acc.add("F", unit, "F_need_linked_inspection_deferral",
                    "同源同段明确治疗缺口对象，当前允许上市审批后核查；同源一般安排要求审批前完成同一核查，构成按需设置的前置要求豁免，不借用药品检验时限。", obj,
                    {"F_gap_branches": [{"kind": k, "text": m.group()} for k, m in scope_gaps],
                     "F_current_deferral": unit.details["current_deferral_anchor"],
                     "F_before_review_baseline": unit.details["baseline_before_review_quote"],
                     "F_object_scope": unit.details.get("object_scope_quote"),
                     "scope_binding": unit.details["scope_binding"]})
    barrier = re.search(r"(?:同等|相同)治疗需要[^。；;]{0,40}(?:差异|不平等|不公平|机会)|(?:患者|人群)[^。；;]{0,20}(?:无法|不能|难以|未能)(?:持续|及时)?(?:获得|取得|获取)[^。；;]{0,12}(?:所需|必要)(?:药品|药物|治疗)|(?:地区|基层|区域|收入|保障身份)[^。；;]{0,20}(?:用药差异|获取差异|极不平衡)", text)
    if barrier:
        acc.add("F", unit, "F_identified_treatment_opportunity_barrier", "当前明确所需药品治疗的获取障碍或同等需要的机会差异，未由一般人群名称或渠道信息推定公平。", obj,
                {"F_object": "患者获得/持续接受所需药品", "F_relation": barrier.group()})
    gaps = [(name, re.search(pattern, combined)) for name, pattern in GAPS.items()]
    gaps = [(name, match) for name, match in gaps if match]
    opportunity = re.search(OPPORTUNITY, combined)
    if (unit.kind == "named_mechanism"
            and unit.details.get("relation_subtype") == "bounded_primary_postadmission_technical_support"):
        # The F opportunity is this very technical communication service. The
        # broader programme name/application rights cannot replace this role.
        gap_scope = _norm(unit.details.get("object_definition", ""))
        gaps = [(name, re.search(pattern, gap_scope)) for name, pattern in GAPS.items()]
        gaps = [(name, match) for name, match in gaps if match]
        opportunity = re.search(r"(?:在审评中|审评过程中)[^。；;]{0,65}(?:沟通交流|技术咨询|研究反馈)[^。；;]{0,30}优先(?:安排|处理|提供)",
                                _norm(unit.details.get("direct_mechanism", "")))
    if gaps and opportunity and _publication_purpose(text) and unit.kind not in {"named_mechanism", "policy_explanation"}:
        acc.exclude("F", unit, "当前短缺/优先词处于制定或发布文件的宗旨，未实际设置以该缺口为条件的申请、优先资源或保障机会。")
        return
    # A parent may supply the direct opportunity predicate. A named mechanism
    # may supplement the issue only through the resolver's direct mapping.
    bound_relation = unit.kind in {"parent_predicate", "substantive_list", "cited_standard", "named_mechanism"}
    current_action = re.search(ACTUAL_ALLOCATION, text)
    target_priority = re.search(r"(?:对|针对|对于)[^。；;]{0,65}(?:药品|药物)[^。；;]{0,10}(?:予以)?优先(?:审评|保障|配置|支持)(?!程序(?:简介|名称))", text)
    # A declared condition followed by an actual application opportunity is a
    # direct relation even without a fixed 对/为/因此 connective. A distinct
    # other-product subject between the condition and action cannot borrow it.
    distinct_subject = False
    if current_action and gaps:
        first_gap = min(match.start() for _, match in gaps)
        between = combined[first_gap:current_action.end()]
        distinct_subject = bool(re.search(r"另(?:一|外)[^。；;，,]{0,10}(?:药品|药物|产品)|其他(?:药品|药物|产品)", between))
    direct_mapping = bound_relation or bool((current_action or target_priority) and not distinct_subject)
    if gaps and opportunity and direct_mapping:
        acc.add("F", unit, "F_need_linked_opportunity_allocation", "原文明示治疗选项或供药缺口，并以该缺口连接针对性申请、优先资源或保障安排；三类缺口分别留痕，未假定已经兑现。", obj,
                {"F_object": "目标患者所需药品治疗", "F_gap_branches": [{"kind": name, "text": match.group()} for name, match in gaps],
                 "F_arrangement": opportunity.group(), "branch_scope": "only the quoted qualifying branches",
                 **({"F_role_evidence": {"current_service_bridge": unit.details["current_service_bridge"],
                     "need_eligibility": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "object_and_need_eligibility"],
                     "postadmission_priority_communication": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "postadmission_priority_technical_communication"],
                     "gap_branches_only": [{"kind": name, "text": match.group()} for name, match in gaps],
                     "preapplication_mechanism_inherited": False}}
                    if unit.details.get("relation_subtype") == "bounded_primary_postadmission_technical_support" else {}),
                 **({"F_role_evidence": {"current_bridge": unit.details["current_qualification_bridge"],
                     "need_and_application_definition": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "object_and_eligibility_definition"],
                     "priority_support": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "priority_research_support"],
                     "withdrawal": [r["evidence"] for r in unit.details["source_roles"] if r["role"] == "withdrawal_direct_mechanism"],
                     "gap_branches_only": [{"kind": name, "text": match.group()} for name, match in gaps],
                     "clinical_advantage_safety_and_other_termination_branches_not_fairness_by_inheritance": True}}
                    if unit.details.get("relation_subtype") == "bounded_primary_qualification_support_roles" else {})})
    elif unit.kind in {"named_mechanism", "policy_explanation"} and gaps and re.search(r"优化[^。；;]{0,20}(?:配送|用药衔接)|完善[^。；;]{0,20}供应|提高[^。；;]{0,20}配送", text):
        mapping = bool(unit.details.get("direct_mapping") or unit.details.get("problem_action_mapping") or re.search(r"针对[^。；;]{0,45}(?:衔接不畅|配送能力弱|供应不稳定|断供)", unit.inherited))
        if mapping:
            acc.add("F", unit, "F_source_mapped_supply_gap_correction", "同版确指官方解释把当前药品配送/衔接措施直接连接所需治疗的获取或持续供给缺口；只使用相应问题—措施片段。", obj,
                    {"F_gap_branches": [{"kind": name, "text": match.group()} for name, match in gaps], "F_arrangement": text})
    elif re.search(TOPICS["F"], text):
        acc.exclude("F", unit, "最接近候选为需要、可及性、普通供给/目录/渠道、价格责任、管理便利或比喻导向，未建立具体公平关系或明确公平评价要求。")


def _current_paragraph(view):
    """The current unit's own same-source paragraph, not a document theme."""
    sha = view.unit.get("source_ref", {}).get("sha256")
    if not sha:
        return None
    loc = view.unit.get("source_ref", {}).get("locator", {})
    pids = set(loc.get("paragraph_ids", []))
    eligible = []
    for ctx in view.contexts:
        pid = (ctx.get("structure", {}).get("paragraph_id")
               or ctx.get("source_ref", {}).get("locator", {}).get("paragraph_id"))
        normalized = _norm(ctx.get("text", ""))
        if (ctx.get("kind") == "paragraph"
                and ctx.get("source_ref", {}).get("sha256") == sha
                and same_component(view.unit, ctx)
                and (not pids or pid in pids)
                and normalized.count(view.norm) == 1):
            eligible.append(ctx)
    return eligible[0] if len(eligible) == 1 else None


def _form_container_mention(text, match):
    """The matched act is only the label quoted inside a form instruction."""
    if re.search(r"(?:栏目|字段|标题|按钮)(?:名称|内容|文字)?[：:]\s*$", text[max(0, match.start() - 35):match.start()]):
        return True
    for quoted in re.finditer(r'“[^”]*”|‘[^’]*’|"[^"]*"', text):
        if quoted.start() <= match.start() and match.end() <= quoted.end():
            after = text[quoted.end():quoted.end() + 35]
            before = text[max(0, quoted.start() - 30):quoted.start()]
            if re.search(r"(?:栏目|字段|标题|按钮|选项|名称)", after):
                return True
            if (re.match(r"(?:的|这一|这些)?(?:文件|材料|模板|表格)", after)
                    and re.search(r"上传|提交|递交|报送|填写|编排|写有|复制", before)):
                return True
            if re.search(r"标点|字体|排版|文字格式", after) and re.search(r"咨询|检查|核对|修改", before + after):
                return True
    return bool(re.match(r"[^。；;，,]{0,6}(?:作为|设为|命名为)[^。；;，,]{0,20}(?:栏目|字段|标题|按钮|选项|名称)", text[match.end():]))


def _affirmative_scope(pattern, text):
    for clause in re.split(r"[。；;]", text):
        match = re.search(pattern, clause)
        if match and not re.search(r"并非|不是|不(?:为|用于|建立|加强|规范|强化)|无需|无须|否认", clause[:match.end()]):
            return True
    return False


def _local_operative_relations(acc):
    """Bounded current acts and their directly governing paragraph definitions."""
    view = acc.view
    text = view.norm
    if _publication_purpose(text):
        return
    current = Unit(text, 0, len(text))
    obj = _object(view, current)
    if not obj.get("established"):
        return
    # An expressly innovation-defined class changes a concrete inspection
    # obligation relative to the adjacent generally risk-dependent rule.
    categories = re.finditer(r"(?:对于|对)(?P<category>创新药(?:、改良型新药)?|改良型新药)[^。；;]{0,20}[，,](?:应当|必须)进行药品注册生产现场核查", text)
    for category in categories:
        if _form_container_mention(text, category):
            continue
        for ctx in view.contexts:
            scope = _norm(ctx.get("text", ""))
            if (ctx.get("kind") == "preceding_paragraph"
                    and view.unit.get("source_ref", {}).get("sha256")
                    and ctx.get("source_ref", {}).get("sha256") == view.unit["source_ref"]["sha256"]
                    and same_component(view.unit, ctx)
                    and re.search(r"根据[^。；;]{0,60}(?:因素|情况)[^。；;]{0,15}(?:基于风险)?决定是否启动药品注册生产现场核查", scope)):
                quote = view._quote(ctx, "相邻一般核查启动规则；当前创新或改良类别明确改变同一核查义务")
                linked = Unit(text, 0, len(text), [quote], "current")
                acc.add("I", linked, "I4_innovation_category_mandatory_inspection",
                        "当前以明示的创新或改良类别决定必须履行的具体注册核查义务，区别于紧前一般风险决定是否启动的规则；记录资格的制度使用，不推定临床优越或研发支持。", obj,
                        {"current_category_consequence": category.group(), "classification": "literal innovation/improvement category, not inferred numerical class"})
                break
    ctx = _current_paragraph(view)
    if not ctx:
        return
    paragraph = _norm(ctx["text"])
    # Only the part before this unit supplies a directly governing definition.
    prefix = paragraph[:paragraph.index(text)]
    choices = re.finditer(r"(?:选择|选用|申请使用)(?P<route>[0-9一二三四五六七八九十百]{1,6}日通道)", text)
    for choice in choices:
        clause_start = max(text.rfind("。", 0, choice.start()), text.rfind("；", 0, choice.start()), text.rfind(";", 0, choice.start())) + 1
        if (not re.search(r"根据[^。；;，,]{0,15}研发[^。；;，,]{0,12}(?:实际需求|需要)", text[clause_start:choice.start()])
                or _formal_relation_target(text, choice) or _form_container_mention(text, choice)):
            continue
        definition = re.search(re.escape(choice.group("route")) + r"是[^。；;]{0,35}将[^。；;]{0,20}审评审批资源向[^。；;]{0,20}(?:创新药|改良型新药)临床试验申请倾斜[^。；;]*", prefix)
        if definition:
            _, offsets = matching_view(ctx["text"])
            quote = view._quote(ctx, "当前选择的同名研发通道在本段明确定义为创新研发审评资源倾斜", raw_span(offsets, definition.start(), definition.end()))
            linked = Unit(text, 0, len(text), [quote], "current")
            acc.add("I", linked, "I3_current_choice_of_defined_rnd_resource",
                    "当前按研发需要选择同段明确提供创新研发审评资源的同名通道，构成实际可用支持机会；不把另一并列通道或一般提速自动记为创新支持。", obj,
                    {"current_choice": choice.group(), "defined_route": choice.group("route"), "resource_definition": definition.group()})
    for prevention in re.finditer(r"(?:避免|防止)[^。；;，,]{0,6}过期药品", text):
        clause_start = max(text.rfind("。", 0, prevention.start()), text.rfind("；", 0, prevention.start()), text.rfind(";", 0, prevention.start())) + 1
        if (not _formal_relation_target(text, prevention)
                and not _form_container_mention(text, prevention)
                and re.search(r"近效期先出|近效期药品先出", text[clause_start:prevention.start()])
                and _affirmative_scope(r"(?:加强|规范|强化)[^。；;]{0,12}药品安全管理", prefix)
                and _affirmative_scope(r"药品(?:采购|贮存)[^。；;]{0,45}(?:调配|使用)[^。；;]{0,20}监测", prefix)
                and not re.search(r"(?:不涉及|不适用|不属于|不承接)[^。；;]{0,25}药品安全管理|(?:以下|下文|本句|本节)[^。；;]{0,12}(?:仅|只)[^。；;]{0,15}(?:财务|报损|核算)", prefix)):
            quote = view._quote(ctx, "当前近效期先出措施所在段明确界定药品全过程安全管理范围")
            linked = Unit(text, 0, len(text), [quote], "current")
            acc.add("S", linked, "same_paragraph_expired_drug_prevention",
                    "当前以近效期先出预防过期药品，直接处于同段明示的药品安全管理范围；不把普通库存统计或有效期信息本身当安全内容。", obj)
    # A current conclusion may consume an explicit same-paragraph need→trial
    # opportunity→removal of the control requirement chain, never 'single arm'
    # or a rare-disease label alone.
    if (re.match(r"因此[，,](?:原则上[，,])?单臂试验适用于", text)
            and re.search(r"缺乏有效标准治疗手段", text)
            and re.search(r"突出疗效", text)
            and (opportunity := re.search(r"无药可治[^。；;]{0,45}急迫的治疗需求[；;，,](?:一旦|当)早期数据(?:已)?(?:提示|显示)(?:试验药物)?(?:存在)?(?:非常)?(?:突出(?:的)?疗效|疗效突出)(?:时)?[，,]则希望入组的受试者均能接受试验治疗[^。；;]{0,30}治疗机会[，,]因此不再要求采用[^。；;]{0,20}对照[，,]可以采用单臂试验设计", prefix))
            and re.fullmatch(r"(?:[，,]以历史数据作为对照)?[。\s]*", prefix[opportunity.end():])):
        quote = view._quote(ctx, "当前适用条件以因此承接本段治疗缺口、全部入组者治疗机会和取消对照要求的完整关系")
        linked = Unit(text, 0, len(text), [quote], "current")
        acc.add("F", linked, "same_paragraph_unmet_need_trial_opportunity",
                "当前单臂适用条件承接同段无可用治疗且急需治疗的需要，并明确让全部入组者获得试验治疗机会、据此取消对照要求；不表示疗效已证实，也不从罕见病或单臂名称单独推出公平性。", obj)


def _pilot_support_roles(view, unit):
    d = unit.details
    current = _norm(_literal(d.get("current_action_anchor", {})))
    objects = "。".join(_norm(_literal(q)) for q in d.get("innovation_object_quotes", []))
    support = "。".join(_norm(_literal(q)) for q in d.get("support_quotes", []))
    if not (unit.kind == "named_mechanism" and current and current in view.norm
            and d.get("version_binding", {}).get("established") is True
            and d.get("scope_binding") and d.get("complete_eligibility_quotes")
            and d.get("action_scope_quotes") and re.search(r"试点项目范围为[^。；;]{0,10}[1一]类创新药", objects)
            and re.search(r"缩短药物临床试验启动用时", support)):
        return None
    mode = d.get("mode")
    if mode == "preapplication_service_requirement":
        if not re.search(r"申请前提供临床试验项目立项[、,]伦理审查[、,]合同审查服务", current):
            return None
    elif mode == "conditional_support_exclusion":
        if not (re.search(r"未收到项目确认书[^。；;]{0,18}不纳入试点", current)
                and d.get("excluded_from_pilot_support") is True):
            return None
    else:
        return None
    return {"mode": mode}


def _statutory_support_roles(view, unit):
    d = unit.details
    current = _norm(_literal(d.get("current_support_anchor", {})))
    if not (unit.kind == "named_mechanism" and d.get("relation_subtype") == "bounded_statutory_postadmission_support"
            and d.get("version_binding", {}).get("established") is True
            and d.get("scope_binding", {}).get("context_ids")
            and d.get("eligibility_or_and_exceptions_preserved") is True
            and current and current in view.norm
            and d.get("complete_eligibility_quotes") and d.get("admission_bridge_quotes")
            and d.get("current_support_quotes")):
        return None
    support = "。".join(_norm(_literal(q)) for q in d["current_support_quotes"])
    mode = d.get("current_support_mode")
    direction = d.get("direction", "provided")
    if direction not in {"provided", "restricted", "mixed"}:
        return None
    restrictions = d.get("current_restriction_quotes", [])
    if direction in {"restricted", "mixed"} and (not restrictions or any(
            not _norm(_literal(q)) or _norm(_literal(q)) not in support for q in restrictions)):
        return None
    if mode == "complete_technical_support_list":
        if not (re.search(r"给予以下政策支持", current)
                and re.search(r"研究方案[^。；;]{0,20}(?:意见|建议)", support)
                and re.search(r"沟通交流申请[^。；;]{0,40}安排审评人员", support)):
            return None
    elif mode == "priority_review_deadline":
        if not (re.search(r"药品上市许可申请的审评时限", current) and d.get("deadline_comparison_quotes")):
            return None
    else:
        return None
    return {"innovation": "。".join(_norm(_literal(q)) for q in d.get("innovation_eligible_branches", [])),
            "need": "。".join(_norm(_literal(q)) for q in d.get("need_eligible_branches", [])),
            "support": support, "mode": mode, "direction": direction,
            "direction_reason": {"provided": "原文规定可用支持，不表示项目已经取得研发成效。",
                                 "restricted": "当前明示限制这些支持，记录限制议题，不称仍在实际提供。",
                                 "mixed": "当前含提供与限制的不同支持分支，分别保留，不把受限分支称为已提供。"}[direction]}


def _trial_admission_roles(view, unit):
    details = unit.details
    if not (unit.kind == "named_mechanism" and details.get("relation_subtype") == "bounded_trial_admission_support"):
        return None
    current = _norm(_literal(details.get("current_admission_anchor", {})))
    support = "。".join(_norm(_literal(q)) for q in details.get("support_quotes", []))
    innovation = "。".join(_norm(_literal(q)) for q in details.get("innovation_eligible_branches", []))
    need = "。".join(_norm(_literal(q)) for q in details.get("need_eligible_branches", []))
    stage = "。".join(_norm(_literal(q)) for q in details.get("research_stage_quotes", []))
    if not (details.get("version_binding", {}).get("established") is True
            and details.get("scope_binding", {}).get("context_ids")
            and details.get("eligibility_or_and_exceptions_preserved") is True
            and details.get("admission_is_current_action_not_status") is True
            and current and current in view.norm
            and re.search(r"(?:最终将|即|将|予以)纳入", current)
            and re.search(r"(?:整个开发过程|临床研发)[^。；;]{0,70}(?:沟通交流|技术反馈)", support)
            and re.search(r"早期临床研发阶段", stage)):
        return None
    return {"current": current, "support": support, "innovation": innovation, "need": need,
            "stage": stage, "details": details}


def _clinical_trial_risk_content(acc):
    """An explicit identified-risk anaphor consumes adjacent participant safety.

    A clinical-trial title, generic risk, or data-reliability aim is insufficient.
    """
    view = acc.view
    text = view.norm
    actions = list(re.finditer(r"申办者(?:应当|应|须|必须)记录已识别的风险和相应的缓解措施", text))
    actions = [m for m in actions if not _form_container_mention(text, m)]
    if not actions or not re.match(r"[（(]三[）)]", text):
        return
    # This path only resolves the identified-risk anaphor. An explicit local
    # restriction to data quality defeats that inherited safety object; other
    # independent current drug-risk predicates remain untouched.
    local_exclusion = r"(?:本项|本条|第三项|已识别的风险)[^。；;]{0,25}(?:仅|只)[^。；;]{0,20}(?:数据|试验结果)(?:可靠性|质量)|(?:不包括|不含|不涉及|不适用)[^。；;]{0,20}(?:试验参与者|参与者|受试者)安全"
    if re.search(local_exclusion, text):
        surviving = []
        for action in actions:
            left = max(text.rfind("。", 0, action.start()), text.rfind("；", 0, action.start()), text.rfind(";", 0, action.start())) + 1
            branch = text[left:action.start()]
            if (re.search(r"(?:另|针对|对于)[^。；;]{0,30}(?:试验参与者|参与者|受试者)安全风险", branch)
                    and not re.search(local_exclusion, branch)):
                surviving.append(action)
        actions = surviving
        if not actions:
            return
    sha = view.unit.get("source_ref", {}).get("sha256")
    if not sha:
        return
    scopes = []
    definitions = []
    for ctx in view.contexts:
        if ctx.get("source_ref", {}).get("sha256") != sha or not same_component(view.unit, ctx):
            continue
        t = _norm(ctx.get("text", ""))
        if (ctx.get("kind") == "source_paragraph"
                and re.search(r"本规范适用于[^。；;]{0,60}为研制药品而进行的药物临床试验", t)
                and not re.search(r"不适用于|仅作为示例|不包括药物临床试验", t)):
            scopes.append(ctx)
        if (ctx.get("kind") == "preceding_paragraph"
                and re.match(r"[（(]二[）)]风险控制应当与风险对试验参与者权益和安全", t)
                and re.search(r"申办者应当预先设定风险控制可接受范围", t)
                and not re.search(local_exclusion, t)
                and not re.search(r"(?:以上|上述|本段|这些|表述|文字|内容)[^。；;]{0,15}(?:作为|用于|是|为)[^。；;]{0,15}(?:栏目|字段|标题|模板)|不构成实质要求", t)):
            definitions.append(ctx)
    if len(scopes) != 1 or len(definitions) != 1:
        return
    quotes = [view._quote(scopes[0], "明示当前规范适用的药物临床试验对象"),
              view._quote(definitions[0], "当前第三项已识别风险承接紧前第二项明示的参与者安全风险及控制范围")]
    obj = {"established": True, "current_anchors": [], "context_evidence": [quotes[0]],
           "object_text": scopes[0]["text"], "role": "same_source_explicit_drug_trial_scope",
           "reason": "同源明示药物临床试验适用范围，仅用于当前具体风险控制对象。"}
    for action in actions:
        # The current risk record is the operation; the source retains the
        # mixed safety/data branches without treating data quality as safety.
        linked = Unit(text, 0, len(text), quotes, "current")
        acc.add("S", linked, "same_source_identified_participant_risk_control",
                "当前要求记录已识别风险及相应缓解措施，直接承接紧前条项明示的试验参与者安全风险控制；药物试验对象由同源适用条款核明。数据可靠性并列内容不单独构成安全性。", obj,
                {"current_risk_action": action.group(), "risk_object": "explicit preceding participant-safety branch", "adjacent_item_relation": "second-to-third"})


def _support_contexts(view, kind):
    sha = view.unit.get("source_ref", {}).get("sha256")
    return [c for c in view.contexts if sha and c.get("kind") == kind
            and c.get("source_ref", {}).get("sha256") == sha
            and same_component(view.unit, c) and c.get("text")]


def _support_branch(text, match):
    """Keep the operative clause and its qualifications; exclude form mentions."""
    a = max(text.rfind(p, 0, match.start()) for p in "。；;") + 1
    ends = [i for p in "。；;" if (i := text.find(p, match.end())) >= 0]
    b = min(ends) if ends else len(text)
    branch = text[a:b]
    # A separate secretary's record-keeping duty does not restrict the already
    # complete substantive service. Remove only that explicitly separate clause;
    # later qualifications on the service itself remain visible to the guards.
    guard_branch = branch
    after_action = match.end() - a
    guard_branch = branch[:after_action] + re.sub(
        r"[,，](?:会议)?秘书(?:仅|只)(?:记录|填写)(?:会议)?(?:开始时间|召开时间|签到名单|会议记录)[^,，。；;]*",
        "", branch[after_action:])
    for quoted in re.finditer(r'“[^”]*”|‘[^’]*’|"[^"]*"', text):
        if (quoted.start() <= match.start() and match.end() <= quoted.end()
                and re.search(r"(?:栏目|字段|标题|按钮)(?:名称|内容|文字)?[:：]$", text[max(0, quoted.start() - 30):quoted.start()])):
            return None
    if (_form_container_mention(text, match) or _formal_relation_target(text, match)
            or re.search(r"(?:表格|字段|栏目)[^。；;，,]{0,12}(?:填写|登记|记载|写入)[:：]", text[a:match.start()])
            or re.search(r"仅(?:记录|填写|上传|转发)|只(?:记录|填写|上传)|仅为(?:栏目|字段|标题)|不构成[^。；;]{0,12}(?:支持|服务|实际)|不涉及[^。；;]{0,12}(?:研发|研究方案)|仅[^。；;]{0,15}(?:签到|签章|报销|会议室|网络账号)", guard_branch)
            or re.search(r"并非|不是|不属于|不适用|不(?:提供|开展|邀请|组织|讨论)|未(?:提供|开展|邀请|组织)", guard_branch)
            or re.search(r"(?<!批准)上市后[^。；;]{0,15}(?:常规|服务|监测|沟通)", guard_branch)):
        return None
    if re.match(r"[。；;]*(?:上述|本次|该|这些)(?:机构|沟通|会议|支持安排|服务)[^。；;]{0,10}(?:仅|只|不涉及|不包括)[^。；;]{0,20}(?:签到|手续|常规|研发|研究方案)", text[b:]):
        return None
    return a, b


def _closed_innovation_service_scope(view):
    """Consume every member of the supplied, closed applicability component."""
    sha = view.unit.get("source_ref", {}).get("sha256")
    groups = []
    for boundary in _support_contexts(view, "following_heading"):
        st = boundary.get("structure", {})
        ids = st.get("scope_context_ids", [])
        if not ids or len(ids) != len(set(ids)) or st.get("follows_context_id") != ids[-1]:
            continue
        members = [view.by_id.get(cid) for cid in ids]
        if any(not c or c.get("kind") != "source_paragraph" or not c.get("text")
               or c.get("source_ref", {}).get("sha256") != sha
               or not same_component(view.unit, c) for c in members):
            continue
        order = [c.get("structure", {}).get("sequence_index") for c in members]
        if order != list(range(len(members))):
            continue
        first, last = st.get("component_first_paragraph"), st.get("component_last_paragraph")
        containers = [c for c in view.contexts if c.get("kind") == "source_paragraph"
                      and c.get("source_ref", {}).get("sha256") == sha and same_component(view.unit, c)
                      and c.get("structure", {}).get("first_paragraph") == first
                      and c.get("structure", {}).get("last_paragraph") == last]
        if not first or not last or len(containers) != 1:
            continue
        objects = []
        for c in members:
            match = re.search(r"适用范围[:：](.*)", _norm(c["text"]))
            if match and any(re.search(r"创新药|改良型新药", part)
                             and not re.search(r"不包括|不含|不适用|非[^。；;]{0,12}(?:创新药|改良型新药)", part)
                             for part in re.split(r"[、,，。；;]|以及", match.group(1))):
                objects.append(c)
        stages = [c for c in members if re.search(r"适用条件及研发阶段[:：].*至批准上市前.*按照本工作规范开展后续沟通交流及审评审批", _norm(c["text"]))]
        if (len(objects) != 1 or len(stages) != 1
                or re.search(r"不适用|仅作为示例|不是适用", _norm(objects[0]["text"]))
                or re.search(r"不适用|仅作为示例|不再按照", _norm(stages[0]["text"]))):
            continue
        groups.append((boundary, members, objects[0], stages[0]))
    return groups[0] if len(groups) == 1 else None


def _add_bounded_support(acc, span, path, reason, contexts, details):
    a, b = span
    quotes = [acc.view._quote(c, usage) for c, usage in contexts]
    obj = {"established": True, "current_anchors": [], "context_evidence": quotes,
           "object_text": "。".join(c["text"] for c, _ in contexts),
           "role": "bounded_same_source_innovation_research_object",
           "reason": "仅由当前支持行动直接承接的同源对象与技术服务片段核明。"}
    acc.add("I", Unit(acc.view.norm[a:b], a, b, quotes), path, reason, obj, details)


def _bounded_local_innovation_support(acc):
    """Four current support acts; source titles and generic communication fail."""
    view, text = acc.view, acc.view.norm
    previous = _support_contexts(view, "preceding_paragraph")
    # Historical operation uses the same named route in the adjacent account;
    # the later faster route is never read to supply its innovation purpose.
    for action in re.finditer(r"(?P<route>[0-9一二三四五六七八九十百]+日默示许可)(?:制度)?的实施[,，][^。；;]{0,20}满足[^。；;]{0,25}(?:生物医药|药物)研发需求", text):
        span = _support_branch(text, action)
        if not span:
            continue
        sources = []
        for ctx in previous:
            t = _norm(ctx["text"])
            implementation = re.search(r"实施" + re.escape(action.group("route")) + r"后[^。；;]*", t)
            if (implementation and _support_branch(t, implementation)
                    and re.search(r"(?:推动|促进|支持)了?创新药研发(?:提速|加快)", implementation.group())
                    and not re.search(r"未能|并未|不能|不曾|并非|不(?:推动|促进|支持)", implementation.group())):
                sources.append(ctx)
        if len(sources) == 1:
            _add_bounded_support(acc, span, "I3_same_route_historical_rnd_support",
                "当前陈述同名默示许可制度的实施及研发用途，紧前同版说明将该历史安排与创新药研发提速相连；记录原文支持议题，不把一系列改革效果全部归因于该制度，也不借后续其他通道的资源安排。",
                [(sources[0], "同名历史制度实施及其明确创新研发联系")], {"route": action.group("route"), "historical_support_not_causal_effect_estimate": True})
    # Actual regulatory discussion of concrete study design, not the public
    # guidance function or the mere word 'innovative' applied to a trial mode.
    for action in re.finditer(r"优化试验设计和实施[^。；;]{0,230}(?:是|也是)监管机构与(?:申办方|申办者)(?:或研究者)?[^。；;]{0,12}沟通交流的重要内容", text):
        span = _support_branch(text, action)
        scopes = [c for c in _support_contexts(view, "source_fragment")
                  if c.get("structure", {}).get("source_role") == "self_declared_scope"
                  and re.search(r"提出创新药研发中的[^。；;]{0,20}设计考虑", _norm(c["text"]))
                  and not re.search(r"不适用|不涉及创新药|仅作为示例", _norm(c["text"]))]
        links = [c for c in previous if re.search(r"及时调整试验方案[^。；;]*研发的推进", _norm(c["text"]))
                 and not re.search(r"仅[^。；;]{0,20}(?:形式|签字|上传)|不涉及研发|不用于研发", _norm(c["text"]))]
        if span and len(scopes) == 1 and len(links) == 1:
            _add_bounded_support(acc, span, "I3_regulatory_research_design_discussion",
                "当前把具体试验设计和实施问题设为监管机构与申办方或研究者的技术交流内容；同源明确创新药研发适用对象，紧前讨论研究方案及研发推进。依据是实际技术沟通，不是指南整体指导作用或试验模式的新颖名称。",
                [(scopes[0], "自声明创新研发对象，只用于对象范围"), (links[0], "同一研究方案技术沟通的研发用途")], {"current_technical_discussion": action.group()})
    # These two services require the complete applicable group, including its
    # exceptions and research stage, not just its first innovation keyword.
    invitations = list(re.finditer(r"沟通交流过程中[,，](?:必要时)?(?:应当|应|可以|可)?邀请[^。；;]{0,35}(?:中检院|核查中心|检验机构|核查机构|专业机构|技术专家)[^。；;]{0,20}参加", text))
    consultations = list(re.finditer(r"专业审评过程中[,，][^。；;]{0,60}技术委员会讨论需要召开专家咨询会[^。；;]{0,60}(?:可由|由)专业审评部门提出召开会议", text))
    candidates = [("invitation", m) for m in invitations] + [("consultation", m) for m in consultations]
    candidates = [(mode, m, span) for mode, m in candidates if (span := _support_branch(text, m))]
    if not candidates:
        return
    closed = _closed_innovation_service_scope(view)
    if closed is None:
        # A supplied but broken explicit scope component is a known dependency;
        # no invented background is requested when no such component exists.
        if any(c.get("structure", {}).get("scope_context_ids") for c in _support_contexts(view, "following_heading")):
            view.material_requests.append({"path": "named_mechanism", "reference": "当前技术服务对应的适用范围及研发阶段",
                "missing": "同源完整范围成员、例外及组件闭合不能核明", "dimensions": ["I"]})
        return
    boundary, members, obj_scope, stage = closed
    scope_quotes = [(c, "完整同源服务适用范围、条件、排除项及研发阶段") for c in members]
    headings = [_norm(c["text"]) for c in _support_contexts(view, "heading")]
    for mode, action, span in candidates:
        if mode == "invitation":
            # Only an unqualified continuation of the immediately preceding
            # discussion can inherit that discussion's research object. A new
            # project or administrative activity is not the same event.
            prefix = text[span[0]:action.start()]
            if not re.fullmatch(r"(?:在)?(?:(?:本次|该|上述)(?:的)?)?", prefix):
                continue
            if not any(re.search(r"早期介入", h) for h in headings):
                continue
            services = [c for c in previous if re.search(r"药审中心与申请人[^。；;]{0,40}咨询问题[^。；;]{0,130}对下一步研究方案提出意见或者建议", _norm(c["text"]))
                        and not re.search(r"不(?:提供|开展|提出)|未(?:提供|开展)|仅[^。；;]{0,15}(?:手续|签到|签章|报销)", _norm(c["text"]))]
            if len(services) != 1:
                continue
            _add_bounded_support(acc, span, "I3_professional_participation_in_research_feedback",
                "当前邀请专业机构加入紧前已明确的下一步研究方案技术反馈，完整同版范围核明创新研发对象与上市前阶段；记录该具体技术服务的专业参与，不从机构名称或普通会议手续推定支持。",
                scope_quotes + [(services[0], "当前参加的是同一研究方案反馈活动")], {"scope_context_ids": boundary["structure"]["scope_context_ids"], "current_professional_participation": action.group()})
        else:
            if not any(re.search(r"专业审评", h) for h in headings):
                continue
            ctx = _current_paragraph(view)
            if ctx is None:
                continue
            paragraph = _norm(ctx["text"])
            suffix = paragraph[paragraph.index(text) + len(text):]
            service = re.match(r"[。\s]*药审中心优先组织专家咨询会[^。；;]*", suffix)
            if not service or not _support_branch(suffix, service):
                continue
            # A named priority service can expressly concern a different
            # project. Preserve such object restrictions instead of borrowing
            # the service for the current meeting merely by adjacency.
            if re.search(r"(?:仅|只)(?:适用|用于|针对|面向)[^。；;]{0,10}(?:其他|另[一个项])|(?:当前|本次|该)会议[^。；;]{0,10}(?:普通流程|不享受|不适用|不予优先)", service.group()):
                continue
            _add_bounded_support(acc, span, "I3_priority_expert_consultation_in_review",
                "当前以专业审评的技术需要触发专家咨询，同段紧接明确优先组织该会议；完整同版对象及阶段将该机会连接创新研发。依据是优先技术咨询，非期限数字或线上会议形式。",
                scope_quotes + [(ctx, "当前条件与同段紧接的优先专家咨询安排")], {"scope_context_ids": boundary["structure"]["scope_context_ids"], "current_consultation_trigger": action.group(), "priority_service": service.group()})


def judge(view) -> dict:
    """Return five independently evidenced DimensionDecision mappings."""
    acc = Accumulator(view)
    for unit in _units(view):
        obj = _object(view, unit)
        _generic(acc, unit, obj)
        _safety_effect(acc, unit, obj)
        _economics(acc, unit, obj)
        _innovation(acc, unit, obj)
        _fairness(acc, unit, obj)
    _local_operative_relations(acc)
    _clinical_trial_risk_content(acc)
    _bounded_local_innovation_support(acc)
    decisions = acc.finish()
    if _publication_purpose(view.norm):
        for dimension, decision in decisions.items():
            if decision['value'] == 0:
                decision.update(basis_path='pure_document_enactment_purpose',
                    current_anchor=view.current_anchor(0, len(view.norm)),
                    current_proposition=view.proposition(0, len(view.norm)),
                    reason='当前完整记录仅说明制定或印发文件的宗旨，没有本句独立的实质问题、评价/证据要求或可使用措施；不展开该文件后文内容。')
                decision['details']['purpose_boundary'] = 'complete_current_proposition; no_downstream_document_inheritance'
    return decisions
