"""Five construct predicates for the common v1.1 development manual.

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


DIMENSIONS = ("S", "E", "Ec", "I", "F")
MANUAL = {
    "S": "v1.1 §一、§二、§三",
    "E": "v1.1 §一、§二、§四",
    "Ec": "v1.1 §一、§二、§五",
    "I": "v1.1 §一、§二、§六、§九",
    "F": "v1.1 §一、§二、§七",
}
DRUG = r"药品|药物|用药|给药|制剂|片剂|胶囊|药费|新药|化学药|生物制品|中药|该药|本药|研究药|试验药|治疗药"
CONTENT_ACTION = r"评价|评估|比较|分析|研判|量化|分级|考察|测算|说明|描述|提供|提交|补充|报告|收集|核实|核对|确认|验证|证明|关注|讨论|要求|应包括|内容涉及"
FORM = r"字段[^。；;，,]{0,18}(?:不能为空|不得为空|非空|已填|填写完整)|(?:字符|文件|材料|字段|数据)(?:的)?格式|(?:签字|签章|盖章|账号|命名|归档|上传时间|递交时间|截止日期|截止时间)"
PURE_STRUCTURE = re.compile(r"^\s*(?:[（(]?[一二三四五六七八九十0-9]+[）)、.．]?\s*)?(?:如下|具体如下|包括以下内容|包括下列内容|包括以下|包括下列|具体包括|下列条件|以下条件|适用范围|申请资格|申请条件|申报流程|安全性|有效性|经济性|创新性|公平性)[:：]?\s*$")
TOPICS = {
    "S": r"安全性|用药安全|安全用药|药物风险|用药风险|不良反应|不良事件|毒性|毒理|肝损伤|禁忌|相互作用|药物警戒|用药差错|用药错误|风险管理|风险评估|风险识别|过敏史",
    "E": r"有效性|疗效|治疗效果|防治效果|临床获益|健康收益|健康获益|生存(?:期|率|获益)?|生命质量|生活质量|临床优势|疾病控制|有效(?:防治|治疗)(?:手段|药物|选择|选项)|药效|主要终点|药物作用反应|整体健康水平",
    "Ec": r"经济性|药价|药品价格|价格|药费|费用|成本|成本效果|成本效用|支付标准|支付范围|支付责任|报销|自付|基金支出|基金预算|预算影响|基金承受能力|基金(?:运行)?安全(?:为|作为)(?:底线|前提|约束)|支付资源|资源约束|按病种付费|DRG|DIP|销售金额|下调比例|降幅|供应成本",
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
MODIFICATION_CHANGE = r"(?:改善|改良|改进|优化|改变|设计|开发)[^。；;]{0,25}(?:片剂|剂型|强度|给药途径|给药频次|释放|结构|包装|装置|口崩|掰断)|(?:片剂|剂型|给药途径|给药频次|释放|结构|包装|装置)[^。；;]{0,15}(?:改善|改良|改进|优化)"
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
    if not re.search(FORM, text):
        return False
    candidates = [p for p in re.split(r"[，,]|或者|或(?=申报|字段|材料|文件|格式)", text)
                  if re.search(TOPICS[dimension], p)]
    if any(not re.search(FORM, part) for part in candidates):
        return False
    # A separate substantive requirement must target content, not a form noun.
    content = rf"(?:评价|评估|比较|分析|说明|核对|核验|确认|验证|补充|提供)[^。；;，,]{{0,20}}(?:{TOPICS[dimension]})"
    action = re.search(content, text)
    return action is None or bool(re.search(r"字段|格式|签章|签字|盖章", action.group()))


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
    publication = re.search(r"(?:特)?(?:制定|印发|发布)(?:本|该)[^。；;，,]{0,25}(?:指导原则|办法|程序|方案|规则|指南|规范|规定|规程|文件)", text)
    if not publication:
        return None
    spans = []
    # Earlier clauses may already assert a concrete problem or requirement.
    # Unmodalized purpose lists such as 促进/保障/提高 remain the document's
    # reasons, not independently enacted content or achieved outcomes.
    for part in re.finditer(r"[^，,。；;]+", text[:publication.start()]):
        s = part.group()
        requirement = re.search(r"(?:应当|应|须|必须|不得|禁止|要求)[^。；;]{0,35}(?:" + CONTENT_ACTION + r"|审核|监测|控制|拒绝|调配|限制|配置|给予|开放)", s)
        problem = re.search(r"(?:" + DRUG + r")[^。；;]{0,25}(?:导致|造成|存在|发生)[^。；;]{0,25}(?:风险|不良反应|损伤|缺口|障碍|费用|成本|疗效|治疗效果)", s)
        if requirement or problem or re.search(ACTUAL_ALLOCATION, s):
            spans.append((part.start(), part.end()))
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
        return bool(re.search(r"改善|提高|提升|获益|优势|不足|尚无有效|没有有效|疗效|治疗效果|防治效果|疾病控制", text))
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
    for kind in ("parent_predicate", "substantive_list", "cited_standard", "named_mechanism", "policy_explanation"):
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
    return units


class Accumulator:
    def __init__(self, view):
        self.view = view
        self.positive = {d: [] for d in DIMENSIONS}
        self.excluded = {d: [] for d in DIMENSIONS}
        self.material = {d: [] for d in DIMENSIONS}
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
            if not isinstance(request, dict):
                continue
            dims = request.get("dimensions") or request.get("affected_dimensions")
            if not dims:
                if request.get("path") == "named_mechanism":
                    dims = ["I"]
                else:
                    trigger = str(request.get("current_text") or self.view.text)
                    dims = [d for d in DIMENSIONS if re.search(TOPICS[d], trigger)]
            for dim in dims or []:
                if dim in self.material:
                    self.request(dim, request)
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
                details["implementation_errors"] = self.errors[dim]
                out[dim] = make_decision(1, first["basis_path"], first["current_anchor"],
                    first["current_proposition"], first["context_evidence"], first["reason"], details=details)
            elif self.material[dim]:
                out[dim] = make_decision(None, "material_insufficient", None, None, [],
                    "当前确指关系所必需的来源内容缺失，不能将未知记为0。",
                    needed_material=self.material[dim], details={"manual": MANUAL[dim], "implementation_errors": self.errors[dim]})
            else:
                reason = "；".join(self.excluded[dim][:4]) or "当前完整命题未表达本维的实质内容、证据要求或直接制度关系。"
                out[dim] = make_decision(0, "no_substantive_relation", None, None, [], reason,
                    details={"manual": MANUAL[dim], "near_candidate_exclusions": self.excluded[dim]})
        return out


def _generic(acc: Accumulator, unit: Unit, obj: dict):
    if unit.kind in {"named_mechanism", "policy_explanation"}:
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
        content = _substantive(text, dim) or (governed and re.search(CONTENT_ACTION + r"|符合|满足|条件|终止", unit.inherited))
        general_word = {"S": r"安全性", "E": r"有效性", "Ec": r"经济性", "I": r"创新性|创新程度|创新价值", "F": r"公平性"}[dim]
        topic_content = re.search(general_word, text) and (dim != "E" or _drug_effectiveness_topic(text))
        if topic_content and content and (re.search(CONTENT_ACTION, text) or governed):
            if dim == "F" and re.search(NONDIM["F"], text):
                continue
            acc.add(dim, unit, "general_evaluation_or_information", "当前以药物/治疗为对象要求本维评价、比较或实质信息；具体机制未由概括词补写。", obj)


def _safety_effect(acc: Accumulator, unit: Unit, obj: dict):
    if unit.kind in {"named_mechanism", "policy_explanation"} or not obj.get("established"):
        return
    text = unit.text
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
        elif re.search(r"疗效|治疗效果|防治效果|临床获益|健康收益|健康获益|药效|疾病控制|明显临床优势|临床比较优势|(?:尚无|没有|不存在)有效(?:防治|治疗)(?:手段|药物|选择|选项)|整体健康水平|(?:改善|延长|提高|降低|减少)[^。；;]{0,15}(?:生存|生命质量|生活质量|死亡|复发)", text):
            acc.add("E", unit, "drug_effect_or_effect_evidence", "当前涉及药物效果、健康收益、效果比较或有效治疗选项缺失；否定和不确定不改变议题在场。", obj)
        elif re.search(r"(?:该|本)研究的主要终点[^。；;]{0,25}(?:验证|核实|确认)|效果估计[^。；;]{0,25}(?:验证|核实|确认)", text):
            if obj.get("context_evidence") and re.search(r"疗效|治疗效果|临床获益|有效性|减少[^。；;]{0,15}(?:骨折|死亡|复发)", str(obj.get("object_text", ""))):
                acc.add("E", unit, "explicit_effect_study_anaphor", "当前核验确指药物效果研究的实质终点，使用限定的同研究来源。", obj)
        else:
            acc.exclude("E", unit, "方法、疾病需要、用途或笼统临床价值未建立药物效果内容关系。")


def _economics(acc: Accumulator, unit: Unit, obj: dict):
    if unit.kind in {"named_mechanism", "policy_explanation"} or not obj.get("established"):
        return
    text = unit.text
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
    price_relation = re.search(r"(?:价格|费用|成本)[^。；;，,]{0,20}(?:合理|偏高|偏低|不超过|不低于|降低|增加|比较|为[0-9]|患者自付)|(?:降低|调整|确定|核验|确认|说明|比较|计算)[^。；;，,]{0,20}(?:价格|费用|成本)|明确(?:药品|药物|治疗|用药|该药|本药)?(?:的)?(?:预算|费用)", text)
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
    if unit.kind == "policy_explanation":
        return
    text = unit.text
    if not obj.get("established") or not re.search(TOPICS["I"] + "|" + SUPPORT + "|" + MODIFICATION_CHANGE + "|" + TECHNICAL_QUALIFICATION, text + (unit.inherited if unit.kind == "named_mechanism" else "")):
        return
    if _form_only(text, "I") or PURE_STRUCTURE.fullmatch(text):
        acc.exclude("I", unit, "创新候选只处于字段、手续或结构引导，没有实质内容关系。")
        return
    if unit.kind != "named_mechanism":
        if re.search(r"新作用机制|新靶点|新化合物|新分子实体|原创(?:性)?|新颖(?:性)?|原始创新", text) and _substantive(text, "I"):
            acc.add("I", unit, "I1_technical_novelty", "当前实质讨论、定义或要求技术新颖性/原创性内容；否定或待证判断不被改写为已具优势。", obj)
        change = re.search(MODIFICATION_CHANGE, text)
        obstacle = re.search(r"吞咽困难|吞咽障碍|难以吞咽|掰断[^。；;]{0,12}(?:困难|不便|障碍)|难以掰断|操作障碍|操作困难|使用障碍|现有[^。；;]{0,15}(?:局限|不足)|难以(?:打开|使用|操作)|(?:手指灵活性|手指功能|手部功能)[^。；;]{0,45}(?:影响|限制)[^。；;]{0,20}(?:掰断|片剂|操作)|(?:掰断|片剂操作)[^。；;]{0,35}(?:受[^。；;]{0,12}(?:手指|手部)|手指灵活性[^。；;]{0,12}影响)", text + "。" + unit.inherited)
        improvement = re.search(r"缓解|改善|减少|解决|克服|便利|便于|更易|提高[^。；;]{0,8}(?:表现|能力)|实质改良", text)
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
    action = re.search(SUPPORT_ACTION, text + ("。" + unit.inherited if unit.kind == "parent_predicate" else ""))
    actual_rnd = bool(re.search(r"研发|研制|研究方案|试验方案|临床试验|上市前|申报前", text + obj_text + unit.inherited))
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
        if not (explicit_service or whole_review_service):
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
                 "I3_connection": "current and legally linked quoted object/arrangement", "support_action": action.group() if action else "具体项目支持功能"})
    elif re.search(r"创新药|支持|鼓励|研发|研制|数据保护", text):
        acc.exclude("I", unit, "只有创新身份、一般鼓励、程序/沟通形式或权利存在，未同时建立创新研发对象、可用安排及直接联系。")


def _fairness(acc: Accumulator, unit: Unit, obj: dict):
    text = unit.text
    if not obj.get("established") or _form_only(text, "F"):
        return
    if re.search(NONDIM["F"], text):
        acc.exclude("F", unit, "公平指向企业竞争、廉政或办理程序，未表达患者药品机会关系。")
        return
    combined = text + "。" + unit.inherited
    affordability = re.search(r"(?:患者|家庭|人群|参保人)[^。；;]{0,25}(?:可负担|能否负担|是否负担|负担不起|无力支付|买不起)|(?:药品|药物|用药|治疗)[^。；;]{0,12}可负担性|可负担性[^。；;]{0,20}(?:药品|药物|用药|治疗)", text)
    if affordability and _substantive(text, "F"):
        acc.add("F", unit, "F_patient_affordability", "当前实质涉及患者能否负担所需药品治疗；该命题已含费用与支付能力关系，不补造收入或已改善效果。", obj,
                {"F_object": "患者药品治疗及持续接受", "F_relation": affordability.group()})
    barrier = re.search(r"(?:同等|相同)治疗需要[^。；;]{0,40}(?:差异|不平等|不公平|机会)|(?:患者|人群)[^。；;]{0,20}(?:无法|不能|难以|未能)(?:持续|及时)?(?:获得|取得|获取)[^。；;]{0,12}(?:所需|必要)(?:药品|药物|治疗)|(?:地区|基层|区域|收入|保障身份)[^。；;]{0,20}(?:用药差异|获取差异|极不平衡)", text)
    if barrier:
        acc.add("F", unit, "F_identified_treatment_opportunity_barrier", "当前明确所需药品治疗的获取障碍或同等需要的机会差异，未由一般人群名称或渠道信息推定公平。", obj,
                {"F_object": "患者获得/持续接受所需药品", "F_relation": barrier.group()})
    gaps = [(name, re.search(pattern, combined)) for name, pattern in GAPS.items()]
    gaps = [(name, match) for name, match in gaps if match]
    opportunity = re.search(OPPORTUNITY, combined)
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
                 "F_arrangement": opportunity.group(), "branch_scope": "only the quoted qualifying branches"})
    elif unit.kind in {"named_mechanism", "policy_explanation"} and gaps and re.search(r"优化[^。；;]{0,20}(?:配送|用药衔接)|完善[^。；;]{0,20}供应|提高[^。；;]{0,20}配送", text):
        mapping = bool(unit.details.get("direct_mapping") or unit.details.get("problem_action_mapping") or re.search(r"针对[^。；;]{0,45}(?:衔接不畅|配送能力弱|供应不稳定|断供)", unit.inherited))
        if mapping:
            acc.add("F", unit, "F_source_mapped_supply_gap_correction", "同版确指官方解释把当前药品配送/衔接措施直接连接所需治疗的获取或持续供给缺口；只使用相应问题—措施片段。", obj,
                    {"F_gap_branches": [{"kind": name, "text": match.group()} for name, match in gaps], "F_arrangement": text})
    elif re.search(TOPICS["F"], text):
        acc.exclude("F", unit, "最接近候选为需要、可及性、普通供给/目录/渠道、价格责任、管理便利或比喻导向，未建立具体公平关系或明确公平评价要求。")


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
