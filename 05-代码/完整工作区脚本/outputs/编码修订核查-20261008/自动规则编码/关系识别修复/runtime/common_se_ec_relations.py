"""Bounded current-text relations for S and Ec under the frozen common rules.

No file, department, document identity, labels, corpus lookup, or inherited
evaluation dimensions are used. ``drug_scope`` may only supply a previously
verified drug/medication object; it cannot supply the relation being detected.
Offsets refer to the original Python Unicode string; ``end`` is exclusive.
This module deliberately favors an explicit local predicate over a keyword.
"""

from __future__ import annotations

import re
from typing import Iterator


_TITLES = re.compile(r"《[^》\r\n]*》|〈[^〉\r\n]*〉")
_SENTENCES = re.compile(r"[^。！？!?；;\r\n]+")
_CLAUSES = re.compile(r"[^，,]+")
_DRUG = re.compile(r"药品|药物|用药|服药|给药|该药|此药|本品|药剂|制剂|疫苗|药费|药价")
_QUALITY = re.compile(r"药品质量|药物质量|质量(?:安全|风险|可控|标准|控制|管理|问题|检验|评价)|纯度|杂质|稳定性|生产工艺|制剂工艺")
_SAFETY_OBJECT = re.compile(
    r"(?:药品|药物|用药)(?:的)?安全(?:性)?|不良(?:药物)?反应|药(?:品|物)不良事件|"
    r"药(?:品|物)警戒|药(?:品|物)相互作用|用药(?:禁忌|错误|差错)|药(?:品|物)误用"
)
_GENERIC_SAFETY = re.compile(r"安全性|毒性|毒副作用|禁忌|禁用|慎用|误用|风险(?:识别|评价|评估|监测|预防|控制|管理)")
_NON_DRUG_SAFETY = re.compile(r"(?:数据|网络|信息|系统|基金|资金|生产|施工|实验室|生物)安全|(?:基金|资金|财务|申报|合规|网络|数据)风险")
_SAFETY_ACTION = (
    r"(?:补充|提供|提交|收集|报告|更新|评价|评估|研究|分析|监测|识别|预防|控制|管理|"
    r"建立|制定|实施|开展|进行|加强|完善|说明|记录|关注|发现|发生|出现|存在|导致|引起|造成|"
    r"增加|降低|减少|防止|避免|未见|未发现|无明显|没有)"
)
_QUALITY_HARM = re.compile(
    r"不良(?:药物)?反应|毒(?:性|副作用)|用药安全|(?:药物|药品)损害|"
    r"(?:危害|损害|伤害|危及).{0,10}(?:患者|病人|人体|健康|生命)|"
    r"(?:患者|病人|人体|健康|生命).{0,10}(?:损害|伤害|损伤|危险|风险)|"
    r"(?:肝|肾|心脏|肝脏|肾脏|器官)损伤"
)

_EVAL = (
    r"(?:开展|进行|补充|提供|提交|评估|评价|比较|分析|测算|估计|估算|说明|"
    r"证明|报告|核算|披露|公开|收集|研究|审查|考察|计算|统计|预计|填写|报送)"
)
_GAP = r"[^，,。！？!?；;\r\n]{0,24}?"
_PRICE = r"(?:价格(?:水平|合理性|降幅|涨幅|调整幅度)?|药价|药费|治疗(?:成本|费用)|用药(?:成本|费用)|药品费用|药物费用|销售(?:金额|额|收入|数量|量))"
_PAY = r"(?:(?:医保|医疗保险|基金)?支付(?:标准|范围|责任)|报销(?:范围|比例|标准)|自付(?:比例|金额|费用|部分|负担)?|费用承担)"
_BUDGET = r"(?:基金预算影响|预算影响|医保预算|基金(?:总)?支出|药品支出|药费支出|基金可负担性|基金承受能力|预算(?:资源|约束|额度|限额))"
_COST_OUTCOME = r"(?:成本[－—\-]?(?:效果|效用|效益|收益)|药物经济学|增量成本(?:效果|效用)比|成本和健康产出|成本与健康产出)"
_ADMIN_FEE = re.compile(r"行政收费|服务费|申报费|申请费|审评费|科研(?:项目)?经费|设备采购|系统收费")
_APPLICATION_PROCESS = re.compile(
    r"(?:可|可以|允许|有资格|符合.{0,12}条件|具备.{0,12}资格|有权).{0,12}(?:申请|申报)|"
    r"(?:申请|申报).{0,8}(?:调整|变更|扩大|缩小).{0,10}(?:支付范围|支付标准)|"
    r"(?:支付范围|支付标准).{0,10}(?:调整|变更)?(?:申请|申报)|"
    r"(?:支付范围|支付标准).{0,12}(?:申请条件|申报条件|办理流程|申报资格|申请资格)"
)
_PROCESS_TAIL = re.compile(r"^.{0,10}(?:申请|申报|资格|流程|办理|栏目|列名|字段名|保密)")
_COLUMN_ONLY = re.compile(
    r"^(?:[（(]?[一二三四五六七八九十\d]+[）).、]?\s*)?"
    r"(?:安全性|经济性|不良反应|药物警戒|基金可负担性|患者可负担性|"
    r"(?:医保)?支付标准|(?:医保)?支付范围|价格|药品价格)(?:[：:]|栏目|列|字段|名称|评价栏目|材料栏目)?$"
)


def mask_document_titles(text: str) -> str:
    """Mask bracketed document titles without changing Unicode offsets."""
    return _TITLES.sub(lambda match: " " * len(match.group()), text)


def _parts(text: str) -> Iterator[tuple[int, str, int, str]]:
    """Yield sentence offset/text and clause offset/text (titles already masked)."""
    masked = mask_document_titles(text)
    for sentence in _SENTENCES.finditer(masked):
        for clause in _CLAUSES.finditer(sentence.group()):
            value = clause.group()
            left = len(value) - len(value.lstrip())
            right = len(value.rstrip())
            if right > left:
                yield sentence.start(), sentence.group(), sentence.start() + clause.start() + left, value[left:right]


def _record(text: str, start: int, value: str, kind: str, subtype: str, basis: str) -> dict:
    return {"start": start, "end": start + len(value), "quote": text[start:start + len(value)],
            "kind": kind, "subtype": subtype, "basis": basis}


def _append(records: list[dict], record: dict) -> None:
    key = (record["start"], record["end"], record["kind"], record["subtype"])
    if not any((item["start"], item["end"], item["kind"], item["subtype"]) == key for item in records):
        records.append(record)


def _local_scope(sentence: str, clause_start: int, sentence_start: int, clause: str, drug_scope: bool) -> bool:
    if drug_scope or _DRUG.search(clause):
        return True
    # A drug object may precede a predicate after a comma in the same sentence.
    # The 80-character bound prevents unrelated distant objects propagating.
    relative = clause_start - sentence_start
    return bool(_DRUG.search(sentence[max(0, relative - 80):relative]))


def _safety_matches(clause: str, scoped: bool) -> list[tuple[str, str]]:
    if _COLUMN_ONLY.fullmatch(clause.strip()):
        return []
    intrinsic = _SAFETY_OBJECT.search(clause)
    generic = _GENERIC_SAFETY.search(clause) if scoped else None
    harm = _QUALITY_HARM.search(clause) if scoped else None
    if not intrinsic and not generic and not harm:
        return []
    # Quality content alone is not a drug-harm/use-safety relation, even when
    # the word "安全" occurs in a phrase such as "药品质量安全".
    quality = bool(_QUALITY.search(clause))
    explicit_harm = bool(_QUALITY_HARM.search(clause))
    if quality and not explicit_harm:
        # Independent drug safety requirements may coexist with quality.
        independent = re.search(r"(?:药品|药物|用药)(?:的)?安全(?:性)?|药(?:品|物)警戒|药(?:品|物)相互作用|用药(?:禁忌|错误|差错)", clause)
        if not independent:
            return []
    if not _has_safety_relation(clause, scoped):
        return []
    # A non-drug risk beside a generic "安全性" does not become drug safety
    # simply because the sentence also mentions a drug application.
    if _NON_DRUG_SAFETY.search(clause) and not intrinsic and not explicit_harm:
        return []
    result = []
    if re.search(r"不良(?:药物)?反应|药(?:品|物)不良事件|毒性|毒副作用", clause):
        result.append(("adverse_effects", "当前句段实质识别、评价或要求提供药物损害证据"))
    if re.search(r"药(?:品|物)警戒|风险(?:识别|评价|评估|监测|预防|控制|管理)", clause):
        result.append(("pharmacovigilance_risk", "当前句段实质安排药物警戒或药物安全风险识别与控制"))
    if re.search(r"相互作用|禁忌|误用|用药错误|用药差错|禁用|慎用", clause):
        result.append(("use_harm_prevention", "当前句段实质涉及用药禁忌、误用、相互作用或损害预防"))
    if not result:
        if harm and not intrinsic and not generic:
            result.append(("drug_harm", "当前句段明确连接药物或药品质量问题与患者损害"))
        else:
            result.append(("drug_safety_evaluation", "当前句段明确讨论药物或用药安全性及其评价证据"))
    return result


def _has_safety_relation(clause: str, scoped: bool) -> bool:
    candidates = list(_SAFETY_OBJECT.finditer(clause))
    if scoped:
        candidates += list(_GENERIC_SAFETY.finditer(clause))
        candidates += list(_QUALITY_HARM.finditer(clause))
    for candidate in candidates:
        prefix = clause[max(0, candidate.start() - 40):candidate.start()]
        suffix = clause[candidate.end():candidate.end() + 30]
        if re.search(r"^.{0,10}(?:专家组|委员会|栏目|列名|字段|名称|模板|格式|文件名|流程|阶段)", suffix):
            continue
        if re.search(_SAFETY_ACTION + r"[^，,。！？!?；;\r\n]{0,24}$", prefix):
            return True
        if re.search(
            r"^.{0,10}(?:应|须|需|必须|需要).{0,10}" + _SAFETY_ACTION + r"|"
            r"^.{0,8}(?:尚不能确定|不能确定|尚未确定|不确定|尚不明确|未明确|"
            r"尚未证实|未证实|较好|较差|较高|较低|良好|可接受|不可接受|不可控|可控|"
            r"尚待验证|有待验证|尚待确定|有待确定|增加|降低|减少)|"
            r"^(?:评价|评估|研究|监测|分析)?(?:结果|证据|数据).{0,6}(?:显示|表明|提示)|"
            r"^[：:为是](?!栏目|名称|字段)", suffix
        ):
            return True
        if scoped and re.search(r"危及|危害|损害|伤害|损伤", candidate.group()):
            return True
    return bool(scoped and re.search(r"(?:患者|人群|孕妇|儿童|老年人|哺乳期).{0,8}(?:禁用|慎用)", clause))


def inspect_safety(text: str, *, drug_scope: bool = False) -> list[dict]:
    """Return explicit current-text drug-harm/safety relations, including negatives."""
    records: list[dict] = []
    for sentence_start, sentence, start, clause in _parts(text):
        scoped = _local_scope(sentence, start, sentence_start, clause, drug_scope)
        for subtype, basis in _safety_matches(clause, scoped):
            # Include the sentence object when it supplies required local scope.
            evidence_start, evidence = start, clause
            if not drug_scope and not _DRUG.search(clause) and not _SAFETY_OBJECT.search(clause) and scoped:
                evidence_start, evidence = sentence_start, sentence
            _append(records, _record(text, evidence_start, evidence, "S", subtype, basis))
    return sorted(records, key=lambda item: (item["start"], item["end"], item["subtype"]))


def _eval_relation(clause: str, concept: str) -> bool:
    # The object cannot be separated from the predicate by a process noun.
    for match in re.finditer(concept, clause):
        prefix = clause[max(0, match.start() - 40):match.start()]
        relation = re.search(_EVAL + _GAP + r"$", prefix)
        suffix = clause[match.end():match.end() + 18]
        if relation and not re.search(r"申请|申报|资格|流程|栏目|保密", relation.group()):
            if re.match(r"(?:谈判|协商|协议|有效期)", suffix):
                continue
            if not re.search(r"^.{0,10}(?:申请|申报|资格|流程|阶段|栏目|字段|名称|模板|格式|文件名|保密|会议|成功|失败)", suffix):
                return True
    return bool(re.search(concept + _GAP + r"(?:的)?(?:评价|评估|比较|分析|测算|核算|统计)(?:结果|证据|数据|资料|报告|要求)", clause))


def _price_relation(clause: str) -> bool:
    if _eval_relation(clause, _PRICE):
        return True
    change = r"(?:降低|提高|下调|上调|调整|控制|限制|限定|制定|合理确定|协商确定|形成|维持|减少|增加)"
    assertion = r"(?:应|须|需|将|已经|已|仍|不得|不应|不宜)?(?:不高于|不低于|高于|低于|不超过|不大于|不小于|为|是|达到|超过|保持|下降|上升|上涨|降低|提高|下调|上调|调整为|合理|不合理|较高|较低|偏高|偏低|过高|过低|过重|较重|可负担|不可负担)"
    for match in re.finditer(_PRICE, clause):
        prefix = clause[max(0, match.start() - 40):match.start()]
        suffix = clause[match.end():match.end() + 25]
        if re.search(r"^.{0,5}(?:谈判|协商|协议|流程|阶段|申请|资格|栏目|字段|名称|文件|格式|有效期)", suffix):
            continue
        if re.search(change + _GAP + r"$", prefix) or re.search(r"^.{0,10}?" + assertion, suffix):
            return True
    return False


def _payment_relation(clause: str) -> bool:
    # Permission/eligibility to lodge an adjustment application is a process
    # relation. A separate actual responsibility/rate/standard can still count.
    application = bool(_APPLICATION_PROCESS.search(clause))
    actual = bool(re.search(
        _PAY + r"(?:应|须|需|将|已|仍)?(?:为|是|包括|仅限|限定为|不包括|不超过|不低于|不高于|调整为|确定为)|"
        r"(?:患者|个人|医保基金|基金|医疗保险|医保|保险机构).{0,12}(?:承担|自付|报销|支付).{0,12}(?:药费|药品费用|药物费用|治疗费用|用药费用)|"
        r"(?:药费|药品费用|药物费用|治疗费用|用药费用).{0,10}由.{0,10}(?:承担|自付|报销|支付)|"
        r"(?:患者|个人).{0,8}按.{1,14}(?:比例|%).{0,6}自付|"
        r"(?:减免|免除|免于).{0,8}(?:自付|药费)|"
        r"(?:按照|依据|按).{0,14}支付标准.{0,10}(?:结算|报销|支付)", clause
    ))
    # A payment object can govern a nested economic attribute before the
    # current change/assertion predicate: standard -> reduction rate -> rise.
    # The local attribute is substantive, not a spelling/format operation.
    nested = re.compile(_PAY + r"(?:的)?"
        r"(?P<attribute>(?:下调|上调|调整|报销|自付)?(?:比例|幅度|金额|额度|水平))"
        r"(?:(?:应当|应|须|需|将|已经|已|仍|是否|能否|可能|不|未|不得|不应|不宜)\s*){0,3}"
        r"(?P<predicate>增加|减少|提高|降低|扩大|缩小|上调|下调|调整为|维持|保持|不变|为|是)")
    for match in nested.finditer(clause):
        prefix=clause[:match.start()]
        if _ADMIN_FEE.search(prefix) and not re.search(r'药品|药物|药费|治疗费用|用药费用',prefix):
            continue
        tail=clause[match.end():match.end()+24]
        if not re.search(r'字符|字数|位数|小数|字体|排版|字段|格式|签章|盖章|签字|字样|字符串',tail):
            return True
    if actual:
        return True
    if application:
        return False
    if _eval_relation(clause, _PAY):
        return True
    for match in re.finditer(r"(?:明确|规定|设定|确定|调整|扩大|缩小|限制|取消|统一|降低|提高|维持|执行)" + _GAP + _PAY, clause):
        if not _PROCESS_TAIL.search(clause[match.end():]):
            return True
    return bool(re.search(
        r"(?:药品|药物|该药|本品).{0,12}(?:纳入|不纳入|排除于).{0,8}(?:医保|基金|医疗保险)支付范围|"
        r"(?:降低|提高|调整|控制).{0,10}(?:自付|报销比例)", clause
    ))


def _budget_relation(clause: str) -> bool:
    return _eval_relation(clause, _BUDGET) or bool(re.search(
        r"(?:控制|限制|降低|减少|增加|设定|确定|不得突破|不超过|纳入)" + _GAP + _BUDGET + r"|" +
        _BUDGET + r".{0,10}(?:增加|减少|下降|上升|过高|过低|可承受|不可承受|可负担|不可负担|为|不超过|受限|有限|不足|充足)", clause
    ))


def inspect_economics(text: str, *, drug_scope: bool = False) -> list[dict]:
    """Return substantive current-text drug treatment/payment resource relations."""
    records: list[dict] = []
    # Read explicit economic content checks before comma enumeration splits
    # their fields away from the governing predicate (including bracket lists).
    for sentence in _SENTENCES.finditer(mask_document_titles(text)):
        value=sentence.group()
        if not (drug_scope or _DRUG.search(value)): continue
        for action in re.finditer(r'核验|核对|核实|确认|验证|检查',value):
            tail=value[action.end():]
            if re.match(r'是否参与|是否进入|材料已收到|文件已签',tail): continue
            fields=list(re.finditer(r'(?:医保)?支付(?:标准|范围)|药品价格|药价|药费|治疗费用|基金预算影响',tail))
            substantive=[]
            for field in fields:
                nearby=tail[max(0,field.start()-12):field.end()+30]
                if re.search(r'字段[^。；;]{0,18}(?:不能为空|已填|填写|字符|格式)|(?:字符|格式|签章|盖章|签字)[^。；;]{0,12}(?:核验|确认|正确)|(?:是否)?(?:为空|已填写|填写完整|格式正确)',nearby):
                    continue
                substantive.append(field)
            if substantive:
                end=action.end()+substantive[-1].end()
                _append(records,_record(text,sentence.start()+action.start(),value[action.start():end],
                    'Ec','specified_economic_content_verification',
                    '当前明确核验或确认指定药品价格/支付标准或范围等实质内容；无需内容新生成或数值改变，纯字段格式及签章排除。'))
    for sentence_start, sentence, start, clause in _parts(text):
        if _COLUMN_ONLY.fullmatch(clause.strip()):
            continue
        scoped = _local_scope(sentence, start, sentence_start, clause, drug_scope)
        # Drug-specific economic language supplies its own object. Generic
        # price/cost/payment expressions need a verified drug object.
        inherent = bool(re.search(r"药费|药价|治疗(?:成本|费用)|用药(?:成本|费用)|药物经济学", clause))
        if not scoped and not inherent:
            continue
        relations = []
        if _price_relation(clause):
            # Pure administrative/research/equipment spending is out of scope.
            if not _ADMIN_FEE.search(clause) or re.search(r"药费|药价|药品价格|药物价格|治疗(?:成本|费用)|用药(?:成本|费用)", clause):
                relations.append(("price_cost", "当前句段实质规定、比较、评价或要求提供药品价格、治疗费用或相关销售用量"))
        if _payment_relation(clause):
            relations.append(("payment_responsibility", "当前句段实质规定、比较、评价或要求提供支付责任、范围、标准、报销或自付"))
        if _budget_relation(clause):
            relations.append(("budget_resource", "当前句段实质涉及药品支付的基金预算、支出、承受能力或资源约束"))
        if _eval_relation(clause, _COST_OUTCOME) or re.search(
            _COST_OUTCOME + r".{0,10}(?:较高|较低|合理|不合理|优于|劣于|尚不明确|不确定|未证实)|"
            r"(?:比较|分析|评价|评估).{0,20}(?:费用|成本).{0,12}(?:和|与|及).{0,12}(?:质量调整生命年|健康产出|健康收益|生存|疗效)", clause
        ):
            relations.append(("cost_health_outcome", "当前句段评价成本与健康产出的关系或要求药物经济学证据"))
        for subtype, basis in relations:
            evidence_start, evidence = start, clause
            if not drug_scope and not _DRUG.search(clause) and not inherent and scoped:
                evidence_start, evidence = sentence_start, sentence
            _append(records, _record(text, evidence_start, evidence, "Ec", subtype, basis))
    return sorted(records, key=lambda item: (item["start"], item["end"], item["subtype"]))


def inspect_quality_content(text: str) -> list[dict]:
    """Content markers only; these neither assign S nor add an attention dimension."""
    records: list[dict] = []
    for sentence_start, sentence, start, clause in _parts(text):
        if not _QUALITY.search(clause):
            continue
        scoped = _local_scope(sentence, start, sentence_start, clause, False)
        linked = bool(_safety_matches(clause, scoped))
        _append(records, _record(
            text, start, clause, "quality_content",
            "quality_with_safety_relation" if linked else "quality_without_safety_relation",
            "质量内容及其当前明确的药物安全联系留痕；不新增注意力维度" if linked else "质量内容但未建立药物损害或用药安全联系；不据此赋S",
        ))
    return records


__all__ = ["inspect_safety", "inspect_economics", "inspect_quality_content", "mask_document_titles"]
