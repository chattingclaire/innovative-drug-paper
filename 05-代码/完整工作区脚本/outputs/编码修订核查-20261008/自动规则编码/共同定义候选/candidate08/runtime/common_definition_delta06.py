"""Bounded implementation of the finalized E and I-path2 clarifications.

Relation anchors, not corpus IDs or expected labels, govern these additions.
This does not claim exhaustive natural-language coverage of the manual.
"""
from __future__ import annotations

import hashlib
import re

from common_if_extensions03 import _current_paragraphs
from common_scope08 import is_format_payload, select_active_frame, has_substantive_payload_use

RULES_SHA256 = "5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c"
C = r"[^，,。！？!?；;\n]"
_TITLE = re.compile(r"《[^》\n]*》|〈[^〉\n]*〉")
_DRUG = re.compile(r"药品|药物|用药|该药|本药|本品|制剂")
_OTHER = re.compile(r"设备|器械|软件|信息系统|物流|配送|办公|外科手术|放射治疗|物理治疗|心理治疗|康复训练")
_DISENGAGED = re.compile(r"另行规定|另行处理|转入|转向|改为|仅供存档|仅存档|不涉及")
_CARRIER = re.compile(r"文件名|栏目|上传格式|填写格式|排版|模板|字体")
_ABSENT = r"(?:尚无|仍无|并无|没有|缺乏|缺少|不存在|无)"
_NO_OPTION = re.compile(
    rf"{_ABSENT}(?:其他)?有效(?:的)?(?:药物|药品)?(?:治疗|防治)(?:措施|手段|方案|选项|方法|药物|药品)"
    rf"|{_ABSENT}(?:能够|可以)?(?:达到|满足)(?:预期)?(?:疾病控制|防治|治疗)(?:效果)?要求的(?:药物|药品)(?:治疗)?(?:选项|方案)?"
)
_ACTIVE_DRUG_FRAME = re.compile(r"(?:讨论|适用|用于|针对|关于|开展|进行|组织|实施)(?:的)?(?:药物|药品)(?:临床)?(?:试验|研究|治疗|防治)")
_ACCESS = re.compile(r"(?:未能|无法|不能|难以)(?:得到|获得|接受)有效治疗")
_BARRIER = re.compile(r"费用|支付|药价|供应|缺货|断供|渠道|缺药")
_ATTRIBUTE = r"(?:释放特征|释放方式|给药方式|给药途径|给药频次|给药频率|剂型|配方|药物结构|治疗属性|制剂颜色)"
_EXISTING = r"(?:现有|既有|原有|已上市)(?:的)?(?:药物制剂|药品制剂|药物|药品|制剂|药物治疗方案|治疗方案)"
_BASE_PATTERNS = (
    re.compile(rf"(?:在|基于)(?P<object>{_EXISTING})(?:的)?基础上"),
    re.compile(rf"(?:与|相较于)(?P<object>{_EXISTING})(?:相比)?"),
)
_QUALIFIED_OBJECT = r"改良型(?:新药|药品|生物制品)(?:的)?(?:临床)?(?:研发|开发|研究)"
_QUALIFIED = re.compile(rf"(?:针对|对于|面向|在)(?P<object>{_QUALIFIED_OBJECT})(?:中)?")
_BASE_FRAME = re.compile(rf"(?:以|将)(?P<object>{_EXISTING})(?:作为|确定为)(?:本项目的)?(?:改良|研发|开发)?基准")
_QUALIFIED_FRAME = re.compile(rf"(?:开展|实施|进行)(?P<object>{_QUALIFIED_OBJECT})")
_BRIDGE = re.compile(r"在此基础上|据此|在该研发中|在上述研发中")
_CHANGE = re.compile(rf"(?:改变|调整|优化|改造)(?:该药|该制剂|药物|药品)?(?:的)?{_ATTRIBUTE}")
_SELF_IMPROVEMENT = re.compile(
    rf"(?P<object>药物产品|药品|药物|该药|本药|该制剂)(?:的)?(?P<attribute>{_ATTRIBUTE})"
    r"(?:是否|并未|尚未|未|已经|是否已经)?(?:达到|构成|实现|取得|具有)(?:了)?"
    r"(?P<improvement>实质(?:性)?(?:改良|改进))"
)
_BENEFIT = re.compile(
    r"(?:以|从而|旨在|进而)(?:进一步)?(?:"
    r"(?:减少|降低)(?:该药|药物)?(?:给药频次|给药次数|给药负担|吞咽困难)"
    r"|(?:改善|提高)(?:该药|药物)?(?:治疗效果|治疗表现|用药依从性|依从性|给药便利性|使用便利性)"
    r")"
)


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _mask(text):
    return _TITLE.sub(lambda m: " " * len(m.group()), text)


def _clause(text, start, end):
    left = max(text.rfind(c, 0, start) for c in "，,。！？!?；;\n") + 1
    right = min((p for c in "，,。！？!?；;\n" if (p := text.find(c, end)) >= 0), default=len(text))
    return left, text[left:right]


def _previous_frame(record, kind):
    """A reproduced, exact same-paragraph immediate antecedent, never a title.

    Incompatible actual topics are semantic nonmatches. Supplied necessary
    material that fails source binding raises; it is not encoded as zero.
    """
    text = record["unit_text"]
    for paragraph in _current_paragraphs(record):
        body = paragraph["text"]
        if body.count(text) != 1:
            raise ValueError("COMMON06: ambiguous current paragraph membership")
        unit_start = body.index(text)
        prefix = _mask(body[:unit_start]).rstrip("。！？!?；;\n \t")
        left = max(prefix.rfind(c) for c in "。！？!?；;\n") + 1
        previous = prefix[left:]
        if not previous:
            continue
        auth = paragraph.get("authentication_v34") or {}
        if not (auth.get("literal_reproduced_in_current_runtime") is True or
                auth.get("layout_reconstructed_literal_reproduced") is True):
            raise ValueError("COMMON06: necessary context requires actual literal or layout source reproduction")
        if len(previous) > 300 or _OTHER.search(previous) or _DISENGAGED.search(previous) or _CARRIER.search(previous):
            continue
        if kind == "drug_effect_object":
            # The final comma clause must carry the current drug frame.
            final = list(re.finditer(r"[^，,]+", previous))[-1]
            match = select_active_frame(final.group(), _ACTIVE_DRUG_FRAME)
            if not match:
                continue
            a, b = left + final.start() + match.start(), left + final.start() + match.end()
            role = "drug_treatment_or_research_object"
        else:
            match = _BASE_FRAME.search(previous) or _QUALIFIED_FRAME.search(previous)
            if not match:
                continue
            if is_format_payload(previous, *match.span()):
                continue
            if re.search(r"不|未|并非|无需", previous[max(0, match.start() - 3):match.start()]):
                continue
            if _BASE_FRAME.search(previous) and not _DRUG.search(match.group("object")):
                continue
            a, b = left + match.start(), left + match.end()
            role = "existing_improvement_baseline" if _BASE_FRAME.search(previous) else "actual_improved_drug_rd_qualification"
        return {"kind": "COMMON06_authenticated_current_relation_scope",
                "scope_role": role, "antecedent_text": body[a:b],
                "antecedent_start_in_paragraph": a, "antecedent_end_in_paragraph": b,
                "current_unit_start_in_paragraph": unit_start,
                "current_unit_end_in_paragraph": unit_start + len(text),
                "current_unit_sha256": _sha(text), "paragraph_id": paragraph["paragraph_id"],
                "paragraph_text_sha256": _sha(body),
                "source_path": paragraph["source_path"], "source_sha256": paragraph["source_sha256"],
                "candidate_path": paragraph["candidate_path"], "candidate_sha256": paragraph["candidate_sha256"],
                "source_authentication": auth, "actual_source_reproduction_required": True,
                "scope_usage": "current object/baseline/qualification only; no neighboring labels inherited"}
    return None


def _anchor(text, role, start, end):
    return {"role": role, "start": start, "end": end, "text": text[start:end]}


def _evidence(text, dimension, start, end, rule, anchors, dependency=None):
    evidence = {"dimension": dimension, "rule": "COMMON06_" + rule,
                "start": start, "end": end, "text": text[start:end],
                "subtype": "attribute" if dimension == "I" else None,
                "common_rules_sha256": RULES_SHA256,
                "protocol_basis": "COMMON-5D-20261009-FINAL",
                "current_relation_anchors": anchors}
    if dependency:
        evidence["context_dependency"] = dependency
    return evidence


def inspect_effective_options(record):
    text = record["unit_text"]
    masked, found = _mask(text), []
    for match in _NO_OPTION.finditer(masked):
        left, clause = _clause(masked, *match.span())
        if _OTHER.search(clause) or (_CARRIER.search(clause)
                and not has_substantive_payload_use(text, *match.span())):
            continue
        # Lack of supply of effective drugs is not lack of effective options.
        if _BARRIER.search(clause) and re.search(r"获得|获取|供给|供应|可及", clause):
            continue
        # The drug must be the treatment option or an active treatment/research
        # frame; an administrative drug noun elsewhere is not enough.
        drug = _DRUG.search(match.group())
        dependency = None
        anchors = [_anchor(text, "current_no_effective_option_proposition", *match.span())]
        if drug:
            anchors.append(_anchor(text, "current_drug_object", match.start() + drug.start(), match.start() + drug.end()))
        elif (frame := select_active_frame(clause, _ACTIVE_DRUG_FRAME)) is not None:
            anchors.append(_anchor(text, "current_active_drug_frame", left + frame.start(), left + frame.end()))
        else:
            # A present but rejected current frame cannot be repaired by
            # borrowing a different preceding discussion. Only an absent
            # local frame permits necessary-object completion.
            if _ACTIVE_DRUG_FRAME.search(clause):
                continue
            dependency = _previous_frame(record, "drug_effect_object")
            if dependency is None:
                continue
        evidence = _evidence(text, "E", *match.span(), "E_no_effective_drug_option", anchors, dependency)
        evidence["effect_statement_kind"] = "no_effective_drug_option"
        evidence["effect_statement_nature"] = "negative_state"
        evidence["common_definition_basis"] = "新定稿E：当前明确不存在达到防治效果要求的药物选项；不要求逐一证明全部药物无效，实际药物对象独立留痕。"
        found.append(evidence)
    return found


def inspect_baseline_improvement(record):
    text = record["unit_text"]
    found = []
    for sentence in re.finditer(r"[^。！？!?；;\n]+", _mask(text)):
        value = sentence.group()
        for change in _CHANGE.finditer(value):
            benefits = [m for m in _BENEFIT.finditer(value) if change.end() <= m.start()]
            if not benefits:
                continue
            benefit = benefits[0]
            if not re.fullmatch(r"(?:为[^，,。；;]{1,20})?\s*[，,]?\s*", value[change.end():benefit.start()]):
                continue
            candidates = [(m, "existing_improvement_baseline") for p in _BASE_PATTERNS for m in p.finditer(value)
                          if m.end() <= change.start()]
            candidates += [(m, "actual_improved_drug_rd_qualification") for m in _QUALIFIED.finditer(value)
                           if m.end() <= change.start()]
            dependency = None
            parallel_anchor = None
            if candidates:
                basis, role = max(candidates, key=lambda x: x[0].end())
                gap = value[basis.end():change.start()]
                if not re.fullmatch(r"\s*[，,]?\s*(?:应当|应|可以|可|需|需要|建议)?", gap):
                    # A parallel action can retain the baseline when it
                    # explicitly says it acts on the same drug/formulation.
                    # '另行' alone neither proves nor disproves that identity.
                    parallel = re.fullmatch(
                        rf"(?:改变|调整|优化|改造)(?:该药|该制剂)?(?:的)?(?:颜色|{_ATTRIBUTE})"
                        r"[，,]\s*(?:并|并且|同时)?对(?P<same>同一(?:药物制剂|药品制剂|药物|药品|制剂))"
                        r"(?:另行|继续|再)?", gap)
                    if not parallel:
                        continue
                    parallel_anchor = _anchor(text, "current_explicit_same_baseline_parallel_object",
                        sentence.start() + basis.end() + parallel.start("same"),
                        sentence.start() + basis.end() + parallel.end("same"))
                start = basis.start()
                basis_anchor = _anchor(text, role, sentence.start() + basis.start(), sentence.start() + basis.end())
            else:
                bridges = [m for m in _BRIDGE.finditer(value) if m.end() <= change.start()]
                if not bridges:
                    continue
                bridge = bridges[-1]
                if not re.fullmatch(r"\s*[，,]?\s*(?:应当|应|可以|可|需|需要|建议)?", value[bridge.end():change.start()]):
                    continue
                if not record.get("paragraph_context"):
                    raise ValueError("COMMON06: explicit improvement reference lacks necessary paragraph source")
                dependency = _previous_frame(record, "improvement_baseline_or_qualification")
                if dependency is None:
                    continue
                start = bridge.start()
                basis_anchor = _anchor(text, "current_explicit_baseline_or_rd_reference",
                                       sentence.start() + bridge.start(), sentence.start() + bridge.end())
            relation = value[start:benefit.end()]
            if not dependency and role == "existing_improvement_baseline" and not _DRUG.search(relation):
                continue
            if (len(relation) > 180 or relation.count("，") + relation.count(",") > 2
                    or _OTHER.search(relation) or _DISENGAGED.search(relation) or _CARRIER.search(relation)):
                continue
            anchors = [basis_anchor,
                       _anchor(text, "current_product_attribute_change", sentence.start() + change.start(), sentence.start() + change.end()),
                       _anchor(text, "explicit_treatment_or_use_improvement_link", sentence.start() + benefit.start(), sentence.start() + benefit.end())]
            if parallel_anchor:
                anchors.append(parallel_anchor)
            evidence = _evidence(text, "I", sentence.start() + start, sentence.start() + benefit.end(),
                                 "I_baseline_attribute_improvement_relation", anchors, dependency)
            evidence["improvement_basis_kind"] = dependency["scope_role"] if dependency else role
            evidence["common_definition_basis"] = "新定稿I路径2：明确既有药物改良基准或实际改良研发资格、当前属性改变、原文治疗或使用改善关系三者绑定；一般优化和身份单独不成立。"
            found.append(evidence)
    return found


def inspect_self_contained_improvement(record):
    text = record["unit_text"]
    found = []
    for match in _SELF_IMPROVEMENT.finditer(_mask(text)):
        _, clause = _clause(text, *match.span())
        if (_CARRIER.search(clause) and not has_substantive_payload_use(text, *match.span())) or _OTHER.search(match.group()):
            continue
        anchors = [_anchor(text, name, *match.span(name)) for name in ("object", "attribute", "improvement")]
        evidence = _evidence(text, "I", *match.span(), "I_self_contained_substantive_improvement", anchors)
        evidence["improvement_basis_kind"] = "self_contained_substantive_improvement"
        evidence["common_definition_basis"] = "新定稿I路径2：当前药物对象、产品属性和实质改良命题自足，包括否定、不确定或评价要求；不再额外强制既有基准或优效证明。"
        found.append(evidence)
    return found


def revise(record, result):
    if result.get("judgement_status") == "undetermined":
        return result
    text = record["unit_text"]
    masked = _mask(text)
    access_ranges = []
    for match in _ACCESS.finditer(masked):
        _, clause = _clause(masked, *match.span())
        if _BARRIER.search(clause):
            access_ranges.append(match.span())
    retained = []
    option_ranges = [m.span() for m in _NO_OPTION.finditer(masked)]
    for evidence in result.get("evidence", []):
        if (evidence["dimension"] == "E" and
                any(a <= evidence["start"] < evidence["end"] <= b for a, b in option_ranges)):
            result.setdefault("suppressions", []).append({"rule": "COMMON06_E_rebind_no_effective_option",
                "dimensions": ["E"], "start": evidence["start"], "end": evidence["end"],
                "text": evidence["text"], "suppressed_rule": evidence["rule"],
                "reason": "无有效选项命题按当前实际药物对象重新绑定；旧短词命中不能绕过来源和对象校验。"})
            continue
        # A local access noun cannot supply an effect proposition. Independent
        # effect evidence anywhere else in the current sentence is preserved.
        if (evidence["dimension"] == "E" and evidence["text"] == "有效治疗"
                and any(a <= evidence["start"] < evidence["end"] <= b for a, b in access_ranges)):
            result.setdefault("suppressions", []).append({"rule": "COMMON06_E_access_only_effective_treatment_noun",
                "dimensions": ["E"], "start": evidence["start"], "end": evidence["end"],
                "text": evidence["text"], "suppressed_rule": evidence["rule"],
                "reason": "当前只是费用／供应等障碍造成治疗不可获取，未由该名词片段陈述药物效果；独立效果依据保留。"})
        else:
            retained.append(evidence)
    additions = (inspect_effective_options(record) + inspect_baseline_improvement(record)
                 + inspect_self_contained_improvement(record))
    option_spans = [(e["start"], e["end"]) for e in additions if e["dimension"] == "E"]
    # Distinct effect propositions retain their own statement provenance.
    for evidence in retained:
        if evidence["dimension"] == "E":
            _, clause = _clause(masked, evidence["start"], evidence["end"])
            is_option = any(a <= evidence["start"] < evidence["end"] <= b for a, b in option_spans)
            specific_ineffective = bool(re.search(r"(?:药物|药品|该药|本药|本品)(?:绝对|完全|显著)?无效", clause))
            evidence["effect_statement_kind"] = (
                "no_effective_drug_option" if is_option else
                "specific_drug_ineffectiveness" if specific_ineffective else "drug_effect_or_effect_evidence")
            evidence["effect_statement_nature"] = evidence.get("survival_statement_nature08") or (
                "negative_state" if is_option else "uncertain" if re.search(r"不确定|不能确定|尚不能|尚待|能否|是否", clause)
                else "negative" if re.search(r"无效|未证实|未被证实|不足|未能", clause)
                else "evidence_requirement" if re.search(r"补充|提交|提供|要求|评价|评估|比较", clause)
                else "effect_statement")
            evidence["target_common_rules_sha256"] = RULES_SHA256
        if evidence["dimension"] == "I" and (
                evidence.get("rule", "").endswith("substantive_improvement") or
                evidence.get("rule", "").startswith("COMMON03_I_current_explicit_substantive")):
            evidence["improvement_basis_kind"] = "self_contained_substantive_improvement"
            evidence["current_relation_anchors"] = [_anchor(text, "self_contained_drug_improvement_proposition", evidence["start"], evidence["end"])]
    result["evidence"] = retained + additions
    result["implementation_scope_note"] = "candidate06依据新定稿手册有界实施E需求/效果边界、有效药物选项缺失、I路径2基准/资格—属性改变—改善关系；保留自足实质改良及其他既有关系。不声称穷尽自然语言覆盖或已通过真实效度验证。"
    result["final_manual_delta06"] = {"manual_sha256": RULES_SHA256,
        "E_no_effective_option_evidence_n": sum(e.get("effect_statement_kind") == "no_effective_drug_option" for e in result["evidence"]),
        "I_baseline_improvement_evidence_n": sum(e.get("rule") == "COMMON06_I_baseline_attribute_improvement_relation" for e in additions),
        "coverage": "bounded_relation_grammar_not_exhaustive_semantic_implementation"}
    return result
