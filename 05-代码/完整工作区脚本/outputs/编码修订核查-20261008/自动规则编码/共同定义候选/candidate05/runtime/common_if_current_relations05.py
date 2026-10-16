"""Current I/F relations and narrowly authenticated object resolution.

No IDs, department names, file identity or reference labels are criteria.
Necessary paragraph material resolves a current object's scope only. It is
never classified wholesale, and no neighboring dimensions are inherited.
"""
from __future__ import annotations

import hashlib
import re

from common_if_extensions03 import _current_paragraphs

VERSION = "common-if-current-relations-bounded-05"
COMMON_RULES_SHA256 = "6b902fd7518379d5edc8e100c1192b627202a0069e69d6e40fea72cad7880a28"
C = r"[^，,。！？!?；;\n]"
J = r"[^。！？!?；;\n]"
_TITLES = re.compile(r"《[^》\n]*》|〈[^〉\n]*〉")
_DRUG = r"(?:药品|药物|该药|本药|本品)"
_INNOVATIVE = r"(?:创新药(?:物|品种)?|改良型(?:新药|药品|生物制品))"
_EVALUATION = re.compile(
    rf"(?:开展|进行|组织|实施)(?:对)?(?P<object>{_DRUG})?(?:的)?创新性(?:评价|评估)"
)
_ANTECEDENT_EVALUATION = re.compile(rf"{_DRUG}(?:的)?创新性(?:评价|评估)")
_CARRIER = re.compile(r"文件名|文件标题|栏目(?:名称)?|上传格式|填写格式|排版|模板|盖章|签字")
_SCOPE_OTHER_TOPIC = re.compile(r"设备|器械|物流|配送|软件|信息系统")
_SCOPE_DISENGAGEMENT = re.compile(r"仅(?:供)?存档|仅(?:作|做)(?:为)?记录|另行规定|另行处理|不适用|不涉及|转入|转向|改为|改用")
_EVALUATION_OBJECT_FIRST = re.compile(
    rf"{_ANTECEDENT_EVALUATION.pattern}(?:应当|应|须|需|要)?(?:依法)?(?:开展|进行|组织|实施)"
)
_REGULATORY_ACTION = re.compile(
    r"(?:优化|完善|建立|设立|实施|提供|加快|推进|调整|明确|开展)"
    r"(?:(?:药品|药物|创新药)(?:的)?)?(?:审评审批|审评|审批)(?:机制|程序|通道|时限)"
)
_INNOVATION_DEVELOPMENT_SUPPORT = re.compile(
    rf"(?:支持|助推|促进|推动|保障|服务|便利){C}{{0,8}}创新药(?:物)?{C}{{0,8}}(?:发展|研发|开发)"
)
_CHANNEL = re.compile(
    rf"(?P<object>{_INNOVATIVE}){C}{{0,16}}"
    r"(?:将|可|可以|应当|应|予以)?(?:依申请|根据申请|经申请)?"
    r"(?:纳入|进入|获得|适用)"
    r"(?P<channel>(?:[0-9一二三四五六七八九十百]+\s*(?:日|天)|优先审评|加快审评|加快审批|专门审评)通道|优先审评程序|加快审评程序)"
)
_CLASS_DEFINITION = re.compile(
    rf"{_INNOVATIVE}(?:是指|指的是|定义为)[，,]?\s*{J}{{0,80}}?"
    rf"(?P<category>[0-9一二三四五六七八九十]+\s*类\s*{_INNOVATIVE})"
)
_DIRECTORY_NEED = re.compile(
    rf"(?:用药目录|药品目录|药品保障范围)(?:应当|应|须|需|要)?"
    r"(?:根据|依据|按照)(?:临床用药需求|患者用药需求|用药需求|用药需要|治疗需要)"
    rf"(?P<bases>{C}{{0,100}}?)(?P<action>"
    r"(?:实行|实施|进行|予以)(?:动态)?(?:调整|修订|更新)|动态(?:调整|修订|更新)|"
    r"(?:调整|修订|更新)(?=$|[，,。；;]))"
)
_URGENT_DRUG_GUARANTEE = re.compile(
    rf"(?P<availability>(?:保障|确保|保证){C}{{0,10}}(?:抢救|急救)"
    r"(?:(?:设备|器械|物资)(?:、|和|及|与)){0,3}(?:药品|药物)(?:可用|供应|配备|充足))"
    r"[，,]\s*"
    r"(?P<priority>(?:确保|保障|保证)(?:急危重|急难危重|危重|急救)(?:患者|病人)优先(?:救治|治疗))"
)


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _mask(text):
    return _TITLES.sub(lambda m: " " * len(m.group()), text)


def _local_clause(text, start, end):
    left = max(text.rfind(c, 0, start) for c in "，,。；;\n") + 1
    right = min((n for c in "，,。；;\n" if (n := text.find(c, end)) >= 0), default=len(text))
    return left, text[left:right]


def _scope_relation_anchors(previous, scope_kind):
    """Require an active, compatible topic rather than a phrase anywhere.

    Omitted evaluation objects continue the immediately preceding final
    clause's drug-evaluation frame. A numeric review channel needs an active
    regulatory arrangement with an explicit drug target, or that arrangement
    and an explicit innovative-drug development support action in this same
    sentence. Mixed incompatible topics are outside this bounded resolver.
    """
    if _SCOPE_OTHER_TOPIC.search(previous) or _SCOPE_DISENGAGEMENT.search(previous):
        return []
    if scope_kind == "drug_innovation_evaluation":
        clauses = list(re.finditer(r"[^，,]+", previous))
        if not clauses:
            return []
        final = clauses[-1]
        matches = [m for m in _EVALUATION.finditer(final.group()) if m["object"]]
        match = matches[-1] if matches else _EVALUATION_OBJECT_FIRST.search(final.group())
        if not match:
            return []
        return [{"role": "actual_drug_innovation_evaluation_topic",
                 "start": final.start() + match.start(), "end": final.start() + match.end()}]
    if scope_kind != "innovative_drug_review_support":
        raise ValueError("current I/F relation: unsupported scope kind")
    actions = list(_REGULATORY_ACTION.finditer(previous))
    if not actions:
        return []
    action = actions[-1]
    anchors = [{"role": "actual_regulatory_arrangement", "start": action.start(), "end": action.end()}]
    if re.search(r"药品|药物|创新药", action.group()):
        return anchors
    support = _INNOVATION_DEVELOPMENT_SUPPORT.search(previous)
    if not support:
        return []
    return anchors + [{"role": "explicit_innovative_drug_development_support",
                       "start": support.start(), "end": support.end()}]


def _previous_sentence_context(record, scope_kind):
    """Only the exact current paragraph's immediately preceding sentence.

    The caller supplies a scope relation kind, not a dimension recognizer.
    Actual literal/layout source reproduction and unique current-unit
    membership are mandatory. A prior-review fallback is a source error here,
    not a semantic zero; the older authenticator is unchanged for other paths.
    """
    text = record["unit_text"]
    for paragraph in _current_paragraphs(record):
        body = paragraph["text"]
        if body.count(text) != 1:
            raise ValueError("current I/F relation: ambiguous current paragraph membership")
        unit_start = body.index(text)
        prefix = _mask(body[:unit_start]).rstrip("。！？!?；;\n \t")
        left = max(prefix.rfind(c) for c in "。！？!?；;\n") + 1
        previous = prefix[left:]
        if not previous:
            continue
        authentication = paragraph.get("authentication_v34") or {}
        if not (authentication.get("literal_reproduced_in_current_runtime") is True or
                authentication.get("layout_reconstructed_literal_reproduced") is True):
            raise ValueError("current I/F relation: necessary preceding scope requires actual literal or layout source reproduction; prior verification alone is insufficient")
        if len(previous) > 300:
            continue
        anchors = _scope_relation_anchors(previous, scope_kind)
        if not anchors or _CARRIER.search(previous):
            continue
        a = left + min(anchor["start"] for anchor in anchors)
        b = left + max(anchor["end"] for anchor in anchors)
        bound_anchors = [{"role": anchor["role"], "start_in_paragraph": left + anchor["start"],
                          "end_in_paragraph": left + anchor["end"],
                          "text": body[left + anchor["start"]:left + anchor["end"]]}
                         for anchor in anchors]
        return {"kind": "authenticated_immediately_preceding_same_paragraph_scope",
                "scope_relation_kind": scope_kind, "scope_relation_anchors": bound_anchors,
                "actual_source_reproduction_required": True,
                "scope_usage": "object_or_regulatory_channel_only_no_dimension_inheritance",
                "current_unit_sha256": _sha(text), "current_unit_start_in_paragraph": unit_start,
                "current_unit_end_in_paragraph": unit_start + len(text),
                "paragraph_id": paragraph["paragraph_id"], "paragraph_text_sha256": _sha(body),
                "antecedent_start_in_paragraph": a, "antecedent_end_in_paragraph": b,
                "antecedent_text": body[a:b], "source_path": paragraph["source_path"],
                "source_sha256": paragraph["source_sha256"],
                "candidate_path": paragraph["candidate_path"], "candidate_sha256": paragraph["candidate_sha256"],
                "pages": paragraph.get("pages", []), "source_lines": paragraph.get("source_lines", []),
                "source_authentication": paragraph["authentication_v34"]}
    return None


def _evidence(text, match, dimension, rule, subtype, basis, dependency=None):
    a, b = match.span()
    out = {"dimension": dimension, "rule": "COMMON05_" + dimension + "_" + rule,
           "start": a, "end": b, "text": text[a:b], "subtype": subtype,
           "basis": basis, "common_rules_sha256": COMMON_RULES_SHA256}
    if dependency is not None:
        out["context_dependency"] = dependency
    return out


def inspect_current_relations(record, result=None):
    text = record["unit_text"]
    if result and result.get("judgement_status") == "undetermined":
        return []
    masked, out = _mask(text), []
    for match in _EVALUATION.finditer(masked):
        left, clause = _local_clause(masked, *match.span())
        if _CARRIER.search(clause):
            continue
        dependency = None
        if not match["object"]:
            # An omitted object is eligible only in a subjectless continuation
            # of the exact same preceding drug-innovation evaluation topic.
            prefix = masked[left:match.start()].strip()
            if prefix not in {"", "应当", "应", "须", "需", "必须"}:
                continue
            dependency = _previous_sentence_context(record, "drug_innovation_evaluation")
            if dependency is None:
                continue
        out.append(_evidence(text, match, "I", "actual_drug_innovation_evaluation", "attribute",
            "I路径1：当前实际开展药品创新性评价；语境只补同一评价对象，栏目或创新对象名称不单独成立。", dependency))

    for match in _CHANNEL.finditer(masked):
        _, clause = _local_clause(masked, *match.span())
        if _CARRIER.search(clause) or re.search(r"拟提名|建议提名|推荐|物流|配送|采购|报销", clause):
            continue
        dependency = None
        if not re.search(r"审评|审批", match["channel"]):
            dependency = _previous_sentence_context(record, "innovative_drug_review_support")
            if dependency is None:
                continue
        out.append(_evidence(text, match, "I", "actual_innovative_review_channel_support", "research_support",
            "I路径3：明确创新／改良对象实际纳入专门审评通道；数字通道另需已认证的当前审评审批语境，不从普通身份推定支持。", dependency))

    for match in _CLASS_DEFINITION.finditer(masked):
        _, clause = _local_clause(masked, *match.span())
        if _CARRIER.search(clause):
            continue
        out.append(_evidence(text, match, "I", "explicit_innovative_class_definition", "attribute",
            "I路径1：当前定义明确限定创新／改良药物的实际类别；类别数字与创新类别共同出现，不从类别数字或普通对象名称推定。"))

    for match in _DIRECTORY_NEED.finditer(masked):
        _, clause = _local_clause(masked, *match.span())
        if _CARRIER.search(clause) or re.search(r"格式|名称|字段|版式|填报|上传", match.group()):
            continue
        out.append(_evidence(text, match, "F", "needs_based_current_directory_adjustment", "needs_based_guarantee",
            "F按需保障：当前用药目录／保障范围作为主语，临床用药或治疗需要明确支配实际调整；普通周期更新不成立。"))

    for match in _URGENT_DRUG_GUARANTEE.finditer(masked):
        if _CARRIER.search(match.group()):
            continue
        evidence = _evidence(text, match, "F", "urgent_need_linked_drug_availability", "needs_based_guarantee",
            "F按需保障：当前抢救药品可用与急危重患者优先救治直接相连；设备并列项不作为药品保障依据。")
        evidence["current_relation_anchors"] = [{"role": name, "start": match.start(name),
            "end": match.end(name), "text": text[match.start(name):match.end(name)]}
            for name in ("availability", "priority")]
        out.append(evidence)
    return out
