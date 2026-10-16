"""Bounded, source-offset-preserving I/F relation recognizers.

Only the Python standard library is used.  Inputs must already be resolved
current propositions, not unfiltered documents or inherited context.  An empty
list means no supported grammar matched; it is not a semantic proof of zero.
"""

from __future__ import annotations

import re

COMMON_RULES_SHA256 = "6b902fd7518379d5edc8e100c1192b627202a0069e69d6e40fea72cad7880a28"
VERSION = "common-if-relations-bounded-01"

# Commas are a boundary by default.  J is used only in explicitly connected
# target/tool, need/allocation, or cause/access constructions below.
C = r"[^。！？!?；;\n，,：:]"
J = r"[^。！？!?；;\n]"
DRUG = r"(?:药品|药物|创新药|改良型新药|该药|本药|本品|该品种|制剂|治疗药|用药|药费)"
PATIENT = r"(?:患者|病人|参保人(?:员)?|参保者)"
INNOVATIVE = r"(?:创新药(?:物)?|改良型新药|原创药物|新靶点药物|新机制药物)"
RD = r"(?:早期)?(?:临床)?(?:研发|研究|试验|开发)"
TARGET = rf"{INNOVATIVE}(?:的)?{C}{{0,6}}{RD}"
TOOL = r"(?:技术指导|科学指导|研发指导|风险管理指导|沟通支持|沟通交流|研究方案建议|研发便利|专项资金|研发资金|资金支持|研发资源|研发平台|专门通道|专门支持资格)"
NOVEL = r"(?:技术新颖性|新颖性|原创性|技术原创性|技术创新性|创新程度|创新价值|创新点|新颖机制|全新作用机制|全新靶点)"
EVALUATE = r"(?:评价|评估|比较|分析|判断|说明|阐明|论证|考察|验证|研究|证明|确定)"
REGION_GROUP = r"(?:基层|农村|偏远地区|边远地区|不同地区|地区间|不同人群|人群间|不同收入|低收入|贫困|困难群众|老年|残障|行动不便)"
ACCESS = rf"(?:(?:获得|获取|接受|持续接受){C}{{0,10}}(?:药品|药物|该药|本药)(?:治疗)?|(?:持续|继续)用药|(?:购药|取药|用药)(?:机会|保障))"

_TITLE = re.compile(r"《[^》\n]*》")
_HARD_SEGMENT = re.compile(r"[^。！？!?；;\n]+")
_DRUG = re.compile(DRUG)
_WRONG_OBJECT = re.compile(
    r"(?:药品|药物|用药)(?:管理|配送|追溯|信息|申报|采购|审核)(?:系统|软件|平台|流程)"
    r"|(?:软件|设备|器械|信息系统|数据接口|行政制度|办公流程)(?:自身|本身|的)?"
    r"[^，,。；;]{0,8}(?:新颖性|原创性|创新性|实质改良)"
)
_NONDRUG_COST = re.compile(r"设备费|器械费|检查费|挂号费|服务费|交通费|差旅费|项目经费")
_EXPLICIT_OTHER = re.compile(r"器械|设备|办公|试验参与机会|研究参与机会|数据共享|数据获取")
_CARRIER = re.compile(r"保密|文件名|命名|字体|字号|排版|上传格式|填写格式|模板|封面|盖章|签字|页码|栏目名称")
_CONTENT_REQUIREMENT = re.compile(
    rf"(?:应当|应|须|需|要求|开展|进行|组织|另需){C}{{0,8}}{EVALUATE}"
    rf"|(?:提交|提供|补充){C}{{0,24}}(?:证据|研究结果|评价结果|分析结果|可负担性数据)"
)


def _masked(text: str) -> str:
    # Length preserving: no normalization, punctuation conversion or deletion.
    return _TITLE.sub(lambda m: "□" * len(m.group()), text)


def _local_clause(text: str, start: int, end: int) -> str:
    left = max((text.rfind(ch, 0, start) for ch in "。！？!?；;\n，,"), default=-1)
    ends = [text.find(ch, end) for ch in "。！？!?；;\n，,"]
    right = min((n for n in ends if n >= 0), default=len(text))
    return text[left + 1:right]


def _allowed(text: str, start: int, end: int, drug_scope: bool) -> bool:
    quote = text[start:end]
    if quote.count("，") + quote.count(",") > 2:
        return False
    if _WRONG_OBJECT.search(quote):
        return False
    # A certified drug subject cannot override an explicit different cost object.
    if _NONDRUG_COST.search(quote):
        return False
    if _EXPLICIT_OTHER.search(quote):
        return False
    if not drug_scope and not _DRUG.search(_masked(quote)):
        return False
    local = _local_clause(text, start, end)
    if _CARRIER.search(local) and not _CONTENT_REQUIREMENT.search(local):
        return False
    return True


def _collect(text: str, patterns: tuple, drug_scope: bool) -> list[dict]:
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if type(drug_scope) is not bool:
        raise TypeError("drug_scope must be bool")
    masked = _masked(text)
    found = []
    seen = set()
    for segment in _HARD_SEGMENT.finditer(masked):
        for pattern, kind, subtype, basis in patterns:
            for match in re.finditer(pattern, segment.group()):
                start = segment.start() + match.start()
                end = segment.start() + match.end()
                if not _allowed(text, start, end, drug_scope):
                    continue
                key = (start, end, kind, subtype)
                if key in seen:
                    continue
                seen.add(key)
                found.append({"start": start, "end": end, "quote": text[start:end],
                              "kind": kind, "subtype": subtype, "basis": basis})
    return sorted(found, key=lambda r: (r["start"], r["end"], r["kind"]))


_I_PATTERNS = (
    # Attribute content requests, including uncertainty/negative assessment.
    (rf"(?:尚不能|不能|尚未|未能)?{EVALUATE}{C}{{0,22}}{NOVEL}",
     "novelty_attribute", "attribute", "I路径1：局部实质讨论或要求评价药物技术新颖性／原创性；否定和不确定不排除。"),
    (rf"{DRUG}{C}{{0,12}}(?:具有|具备|缺乏|不具有|不具备|尚不能确定是否具有|尚不能证明具有){C}{{0,6}}{NOVEL}",
     "novelty_attribute", "attribute", "I路径1：药物对象与新颖属性的直接陈述；不把一般机制或身份作为新颖性。"),
    (rf"{DRUG}{C}{{0,10}}(?:采用|基于|具有){C}{{0,4}}(?:全新|原创|首创)(?:作用机制|靶点|分子结构|治疗原理)",
     "novelty_attribute", "attribute", "I路径1：当前明确讨论药物采用的全新／原创技术。"),
    (rf"(?:采用|基于)(?:全新|原创|首创|新)(?:靶点|作用机制|分子结构){C}{{0,6}}(?:研发|开发){C}{{0,6}}(?:药品|药物)",
     "novelty_attribute", "attribute", "I路径1：新颖技术与药物研发直接连接。"),
    (rf"(?:药品|药物|该药|本药)?(?:的)?注册(?:分类|类别){C}{{0,5}}(?:为|是|属于|判定为|认定为)(?:创新药|改良型新药)",
     "novelty_attribute", "attribute", "I路径1：实际创新／改良注册分类，不外推单独类别序号。"),
    (rf"(?:按|按照)(?:创新药|改良型新药)注册(?:分类|类别){C}{{0,6}}(?:申报|注册)",
     "novelty_attribute", "attribute", "I路径1：明确采用实际创新／改良型注册分类。"),
    (rf"(?:研发|开发|设计|评价|评估|研究|论证){C}{{0,10}}(?:改良剂型|改良制剂|实质(?:性)?改良|创新性改良|实质(?:性)?改进){C}{{0,18}}",
     "substantive_improvement", "attribute", "I路径2：明确改良／实质改进关系；不从普通剂型规格变化推定改良。"),
    (rf"(?:对)?{DRUG}{C}{{0,12}}(?:剂型|释放特征|给药方式|治疗属性|配方|结构){C}{{0,6}}(?:作|做|实现|进行|具有)(?:了)?实质(?:性)?(?:改良|改进|改善)",
     "substantive_improvement", "attribute", "I路径2：药物产品／治疗属性与实质改良的明确连接。"),
    # Support must link an innovative R&D target to an actual instrument/action.
    (rf"(?:为|面向|针对){TARGET}{J}{{0,18}}(?:提供|配置|投入|拨付|安排|给予|资助|不再提供|不予提供|停止提供){C}{{0,15}}{TOOL}",
     "targeted_rnd_support", "research_support", "I路径3：特定创新／改良研发对象＋实际供给安排；安全技术指导亦可纳入。"),
    (rf"(?:建立|设立|建设|提供|安排|取消|停止){C}{{0,8}}{TOOL}{J}{{0,12}}(?:用于|以支持|服务于|支持|面向){TARGET}",
     "targeted_rnd_support", "research_support", "I路径3：支持工具与创新研发用途直接连接。"),
    (rf"(?:支持|资助|扶持|鼓励){C}{{0,12}}{TARGET}{C}{{0,10}}(?:开展|参与|进行|实施|合作|项目|活动)",
     "targeted_rnd_support", "research_support", "I路径3：明确支持创新研发项目或参与实施安排，非只有对象身份。"),
    (rf"(?:支持|鼓励|安排){C}{{0,10}}(?:机构|研究者|研发人员|研究人员){C}{{0,6}}(?:参与|开展|承担|实施){C}{{0,4}}{TARGET}",
     "targeted_rnd_support", "research_support", "I路径3：面向特定创新研发的实际参与／实施安排，非泛指创新身份。"),
    (rf"{TARGET}{C}{{0,12}}(?:可获得|享有|可申请适用|获得|不再享有|不予给予){C}{{0,8}}{TOOL}",
     "targeted_rnd_support", "research_support", "I路径3：创新研发对象实际获得／申请具体支持工具的资格。"),
    # Qualifications need both an innovative object and substantive comparison.
    (rf"{INNOVATIVE}{C}{{0,10}}(?:申请|适用|认定|获得){C}{{0,10}}(?:资格|程序|支持){C}{{0,6}}(?:须|需|应|要求|条件为){C}{{0,12}}(?:较|与|相比){C}{{0,12}}(?:既有|现有|已有){C}{{0,14}}(?:创新优势|技术创新|临床优势|实质改良|原创性|新颖性)",
     "qualification_comparison", "qualification_advantage", "I路径4：创新／改良对象＋当前支持资格条件＋与既有产品／治疗的比较条件。"),
    (rf"(?:与|较)(?:现有|既有|已有){C}{{0,14}}(?:相比)?{C}{{0,14}}(?:明显临床优势|技术创新优势|实质改良){C}{{0,8}}{INNOVATIVE}{C}{{0,12}}(?:可以|可|能够)(?:申请|适用){C}{{0,10}}(?:程序|支持资格)",
     "qualification_comparison", "qualification_advantage", "I路径4：比较条件被明确作为创新／改良对象申请支持程序的条件。"),
)


def inspect_innovation(text: str, *, drug_scope: bool = False) -> list[dict]:
    """Return supported current I relations; no inference from IDs or old labels."""
    found = _collect(text, _I_PATTERNS, drug_scope)
    # A title may identify the recipient only when linked to a current, actual
    # guideline supply AND its R&D guidance function.  Titles are otherwise masked.
    pattern = (rf"(?:制定|编制|发布|印发)《(?P<title>{INNOVATIVE}[^》\n]{{0,35}}(?:指南|指导原则))》"
               rf"{J}{{0,10}}(?:为|向){C}{{0,12}}(?:研发|研究|试验){C}{{0,8}}提供{C}{{0,10}}(?:技术指导|风险管理指导|科学指导)")
    for m in re.finditer(pattern, text):
        if _CARRIER.search(m.group()):
            continue
        found.append({"start": m.start(), "end": m.end(), "quote": m.group(),
                      "kind": "targeted_rnd_support", "subtype": "research_support",
                      "basis": "I路径3：具体创新研发指南的制定／供给行为与当前研发指导功能相连；标题仅识别对象。"})
    unique = {(r["start"], r["end"], r["kind"], r["subtype"]): r for r in found}
    return sorted(unique.values(), key=lambda r: (r["start"], r["end"], r["kind"]))


_F_PATTERNS = (
    (rf"(?:评价|评估|比较|分析|考察|研究|说明|提高|改善|保障){C}{{0,18}}(?:患者|参保人(?:员)?){C}{{0,12}}(?:可负担性|支付能力)",
     "patient_affordability", "patient_affordability", "F患者可负担性：当前实质讨论或评价患者支付能力／可负担性，而非普通自付责任。"),
    (rf"(?:提交|提供|补充|报告){C}{{0,12}}(?:患者|参保人(?:员)?){C}{{0,12}}可负担性(?:证据|数据|评价结果|分析结果|研究结果)",
     "patient_affordability", "patient_affordability", "F患者可负担性：明确要求患者可负担性证据，不另要求重复收入或已证实障碍。"),
    (rf"{PATIENT}{C}{{0,10}}(?:能否|是否能够|能够|不能|难以|无法|无力)(?:承担|负担|支付){C}{{0,10}}(?:药费|药品费用|该药费用|用药费用|药物费用)",
     "patient_affordability", "patient_affordability", "F患者可负担性：患者支付能力与药品费用直接连接，包括否定及不确定判断。"),
    (rf"(?:降低|减轻|缓解|补助|补贴|资助|救助){C}{{0,8}}(?:低收入|贫困|经济困难){PATIENT}{C}{{0,16}}(?:药费|用药费用|药品费用|自付负担|自付费用)",
     "patient_affordability", "patient_affordability", "F支付障碍：费用减免／救助明确指向经济困难患者的药品负担。"),
    (rf"(?:按|按照|依据|根据|以){C}{{0,10}}(?:临床用药需求|患者治疗需要|治疗需要|患者用药需求|用药需求|用药需要|疾病谱){C}{{0,12}}(?:配置|配备|供应|保障|调整|遴选){C}{{0,12}}(?:药品|药物|用药目录|保障范围)",
     "needs_based_allocation", "needs_based_guarantee", "F按需保障：明确治疗／用药需要与实际药品配置、供给或范围安排相连。"),
    (rf"(?:按需|按临床需要){C}{{0,6}}(?:配置|配备|供应|保障){C}{{0,10}}(?:药品|药物|用药)",
     "needs_based_allocation", "needs_based_guarantee", "F按需保障：原文明确按需配置或保障药品，不从普通覆盖自动推定。"),
    (rf"(?:开展|组织|进行){C}{{0,8}}用药需求评估[，,]{C}{{0,10}}(?:指导|据此|并据此){C}{{0,12}}(?:制定|调整){C}{{0,10}}(?:用药遴选|药品遴选|用药目录|药品供应)(?:和调整)?(?:规则)?",
     "needs_based_allocation", "needs_based_guarantee", "F按需保障：需求评估以明确连接谓词指导药品选择／供给规则，而非孤立需求调查。"),
    (rf"(?:保障|确保|保证|满足){C}{{0,8}}(?:患者|参保人(?:员)?){C}{{0,10}}(?:治疗所需|所需|必要){C}{{0,6}}(?:药品|药物|用药)",
     "needs_based_guarantee", "needs_based_guarantee", "F按需保障：具体患者所需药品与保障行为直接连接，不把治疗需要作为所有政策天然背景。"),
    (rf"(?:按|按照|根据)治疗需要{C}{{0,8}}保障{C}{{0,8}}{PATIENT}{C}{{0,8}}(?:持续)?(?:获得|接受){C}{{0,8}}(?:药品|药物)(?:治疗)?",
     "needs_based_guarantee", "needs_based_guarantee", "F按需保障：治疗需要与患者获得或持续药物治疗的保障关系明确。"),
    (rf"(?:保障|确保|满足){C}{{0,8}}(?:临床急需|治疗必需)(?:的)?(?:药品|药物){C}{{0,8}}(?:供应|配备|获取)",
     "needs_based_guarantee", "needs_based_guarantee", "F按需保障：临床必需用药与具体供给／获取保障相连。"),
    (rf"(?:弥补|填补|消除|解决|缩小|评价|评估){C}{{0,12}}(?:用药|药品)保障(?:缺口|空白|不足)",
     "guarantee_gap", "needs_based_guarantee", "F保障缺口：当前实质处理明确的药品／用药保障不足，非临床研发疗效缺口。"),
    (rf"{REGION_GROUP}{C}{{0,24}}(?:缺药|缺乏{C}{{0,10}}条件|支付能力不足|无力支付|未获保障){C}{{0,8}}(?:导致|致使|使|造成){C}{{0,15}}(?:难以|不能|无法){ACCESS}",
     "population_region_access_barrier", "opportunity_barrier", "F机会障碍：地区／人群条件通过明确因果谓词影响获得或持续药物治疗。"),
    (rf"(?:评价|评估|比较|分析|减少|消除|缩小|解决){C}{{0,8}}{REGION_GROUP}{C}{{0,20}}(?:药品|药物|用药){C}{{0,14}}(?:机会差异|保障差异|获取障碍|不平等|机会不均等)",
     "population_region_access_barrier", "opportunity_barrier", "F差异评价／改善：地区人群与药物治疗获取或保障差异属于同一局部关系。"),
    (rf"(?:不得|不应|禁止)(?:因|以){C}{{0,16}}(?:户籍|地区|医保身份|保障身份|所在机构|收入){C}{{0,12}}(?:限制|拒绝|阻碍){C}{{0,10}}(?:患者|参保人(?:员)?)?{C}{{0,8}}(?:用药|购药|获得药品|获得药物治疗)",
     "unreasonable_access_restriction", "opportunity_barrier", "F不合理障碍：明确禁止身份／地区／机构条件限制药品治疗获取。"),
    (rf"(?:解除|取消|消除){C}{{0,8}}(?:不合理|非临床需要){C}{{0,8}}(?:用药|药品获取|购药|取药){C}{{0,6}}(?:限制|障碍)",
     "unreasonable_access_restriction", "opportunity_barrier", "F不合理障碍：当前明确解除非临床或不合理的药品获取限制。"),
    (rf"(?:评价|评估|比较|分析|研究|提高|促进|保障|改善){C}{{0,12}}(?:药品保障|用药保障|药物治疗获取|药品获取|购药机会){C}{{0,8}}(?:公平性|公平可及|机会均等|公平(?!竞争|招标|采购|交易))",
     "equity_goal_or_evaluation", "guarantee_equity", "F公平目标／评价：当前公平要求明确作用于药品治疗获取或保障，不把栏目或一般公平竞争传入。"),
    (rf"(?:药品保障|用药保障|药物治疗获取|药品获取){C}{{0,5}}(?:应当|应|要|更加|实现|达到){C}{{0,5}}(?:公平可及|机会均等|公平(?!竞争|招标|采购|交易))",
     "equity_goal_or_evaluation", "guarantee_equity", "F公平目标：药品保障本身与公平目标直接连接；不解释为措施已经有效。"),
)


def inspect_fairness(text: str, *, drug_scope: bool = False) -> list[dict]:
    """Return supported F relations; ordinary access/payment/management is absent."""
    return _collect(text, _F_PATTERNS, drug_scope)
