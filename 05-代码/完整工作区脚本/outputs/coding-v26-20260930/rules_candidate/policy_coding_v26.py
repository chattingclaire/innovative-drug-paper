"""Bounded I/F candidate layered on the frozen v25 development engine.

This module preserves v25 S/E/Ec decisions and adds only relation-bound I/F
evidence.  It does not inspect IDs, departments, filenames, or reference labels.
Development references informed the error mechanisms but are not validation.
"""
from __future__ import annotations

import copy
import hashlib
import re
import sys
from pathlib import Path

OLD_ROOT = Path(__file__).resolve().parents[2] / "autocode-v25-20260927"
if str(OLD_ROOT) not in sys.path:
    sys.path.insert(0, str(OLD_ROOT))
import policy_coding_v25 as v25

VERSION = "v26-candidate-1-if-relation-generalization"
DIMENSIONS = v25.DIMENSIONS

RULE_SPEC = {
    "V26_I_non_drug_system_object": {
        "manual_basis": "CAL-5D v1.3 I: 系统性工作、管理创新和信息系统不等于药物创新属性。",
        "required": "创新性必须以药物属性或研发支持为对象。",
        "excluded": "创新性修饰信息、数据、申报、办公或管理系统时，只抑制该局部 I 证据。",
    },
    "V26_F_data_access_object": {
        "manual_basis": "CAL-5D v1.3 F: 数据可获得性不属于药品保障获取。",
        "required": "可及/可获得必须以药品、用药或治疗为对象。",
        "excluded": "数据、证据、文献或系统的可及性；只抑制该局部证据。",
    },
    "V26_I_product_modification_relation": {
        "manual_basis": "CAL-5D v1.3 I: 原创或改良；v1.2: 相对既有产品的具体变化。",
        "required": "明确改良/改善/优化/改进与给药途径或具体药品/制剂属性构成直接关系。",
        "excluded": "仅列新品种、规格、剂型、便利性、适老化或一般药物设计。",
    },
    "V26_I_data_protection_support_relation": {
        "manual_basis": "CAL-5D v1.3 I: 明确针对药物研发创新的激励；research_support。",
        "required": "同一命题明确把药品创新目标与试验数据保护制度措施连接。",
        "excluded": "仅出现制度标题、发布/归档事务或无药品创新目标的数据保护。",
    },
    "V26_I_drug_research_support_relation": {
        "manual_basis": "CAL-5D v1.3 I: 明确规定、提供、扩大或讨论药物研发创新支持措施。",
        "required": "支持动作直接支配创新药/新药研发对象，或明确对/为该对象给予支持或提供资源。",
        "excluded": "一般产业创新、机构创新、仅以创新药命名、纯登记归档，或支持动作指向其他宾语。否定或取消仍表示讨论该维度。",
    },
    "V26_F_treatment_gap_relation": {
        "manual_basis": "CAL-5D v1.3 F: 未满足治疗需求与保障获取。",
        "required": "明确否定现有/标准/有效治疗手段、选择、方案或药物，并有药物对象范围。",
        "excluded": "仅疾病严重、低缓解率、试验设计或研究参与。",
    },
    "V26_F_treatment_opportunity_from_gap": {
        "manual_basis": "CAL-5D v1.3: 使原本无法获得治疗的人群获得研究药物或治疗机会。",
        "required": "同一单元同时明确既往治疗缺口和患者/人群实际获得药物或治疗机会。",
        "excluded": "没有既往缺口的普通入组、给药、研究参与或访视便利。",
    },
    "V26_F_drug_use_obstacle_relation": {
        "manual_basis": "CAL-5D v1.3 F clinical_management: 药品使用的具体管理障碍、复杂性或负担。",
        "required": "同一命题把具体药品操作任务与困难、障碍、无法完成或复杂性直接连接。",
        "excluded": "一般老年特征、便利性建议、医院管理、合理用药口号或仅特殊储存/专科给药。",
    },
    "V26_F_anaphoric_management_complexity": {
        "manual_basis": "CAL-5D v1.3: 上下文只用于消解指代；具体用药管理复杂性可记 clinical_management。",
        "required": "当前句的‘此类用药行为’在同一核验段落中唯一出现，前文明确不同服药时间/给药途径等复杂性。",
        "excluded": "多病共存、多重用药名称本身，或无法唯一绑定的邻近文本。",
    },
}

_MOD_ACTION = r"(?:改良|改善|优化|改进)"
_MOD_TARGET = (r"(?:给药(?:途径|方式)|(?:药物|药品|制剂)(?:的)?(?:结构|特征|释放特征|释放行为)"
               r"|片剂(?:的)?易碎性)")
_MOD_RELATION = re.compile(
    rf"(?:{_MOD_ACTION}(?:了|其|该|相应|有关|具体|有针对性地|\s)*{_MOD_TARGET}"
    rf"|{_MOD_TARGET}(?:得到|进行|予以|实施|作|做)?(?:了)?{_MOD_ACTION})"
)

_GAP = re.compile(
    r"(?:已无|尚无|并无|没有|缺乏|缺少|不存在)"
    r"(?:现有(?:的)?|标准(?:的)?|有效(?:的)?|可用(?:的)?|其他(?:的)?|\s)*"
    r"(?:治疗|防治)(?:措施|手段|选择|方案|药物)"
    r"|(?:晚期)?无药可治"
    r"|未能(?:得到|获得)(?:充分[、,，]?)?有效治疗"
)
_OPPORTUNITY = re.compile(
    r"(?:(?:使|让|保障|确保|希望)?(?:[^。；;，,]{0,16})?"
    r"(?:患者|人群|受试者)(?:均能|都能|均|都|能够|可以|得以|可)?"
    r"(?:接受|获得|得到|用上)(?:[^。；;，,]{0,16})?"
    r"(?:试验药物|研究药物|治疗药物|试验治疗|药物治疗|抗肿瘤治疗|治疗机会))"
)
_USE_TASK = (r"(?:打开(?:药品|药物)?包装|(?:准确)?量取(?:及|和|并)?(?:使用)?药物|"
             r"(?:吞咽|服用|使用|管理)药物|给药(?:时点|频次|途径|方式))")
_USE_OBSTACLE = re.compile(
    rf"(?:{_USE_TASK}(?:时|方面)?[^。；;]*?(?:遇到|存在|面临)?(?:困难|障碍|复杂性|难以|无法)"
    rf"|(?:难以|无法)[^。；;]*?{_USE_TASK})"
)
_RND_TARGET = r"(?:创新药(?:物)?|新药|药物创新)(?:的)?(?:研发|研制|开发)"
_RND_SUPPORT = re.compile(
    rf"(?:(?:不再)?(?:支持|鼓励|促进|推动|激励|加快)(?:对|为)?{_RND_TARGET}"
    rf"|取消(?:了)?对{_RND_TARGET}(?:的)?支持"
    rf"|对{_RND_TARGET}(?:予以|给予|提供|加大|加强)?(?:支持|鼓励|激励)"
    rf"|{_RND_TARGET}(?:获得|得到|接受|享有)(?:了)?(?:政策|资金|资源|平台|数据服务)?支持"
    rf"|为{_RND_TARGET}提供[^。；;，,]*(?:资金|投资|数据服务|平台|资源|政策支持|支持))"
)


def _sentences(text):
    yield from re.finditer(r"[^。；;]+", text)


def _raw_span(offsets, start, end):
    return offsets[start][0], offsets[end - 1][1]


def _cover(matches):
    return min(m.start() for m in matches), max(m.end() for m in matches)


def _drug_scope(result, text):
    return bool(v25.DRUG.search(text) or result.get("drug_object_evidence"))


def _dependency(record, paragraph, kind, antecedent):
    return {
        "kind": kind,
        "paragraph_id": paragraph.get("paragraph_id"),
        "source_sha256": record.get("unit_source_sha256") or record.get("source_sha256"),
        "paragraph_sha256": hashlib.sha256(paragraph["text"].encode()).hexdigest(),
        "antecedent_text": antecedent,
        "pages": paragraph.get("pages", []),
    }


def code_unit(record):
    """Return the v25 result plus bounded I/F relation evidence."""
    result = copy.deepcopy(v25.code_unit(record))
    result["version"] = VERSION
    result["parent_version"] = v25.VERSION
    result["v26_if_rule_spec"] = copy.deepcopy(RULE_SPEC)
    result["v26_if_suppressions"] = []
    if result.get("judgement_status") == "undetermined":
        return result

    locked = {d: result["labels"][d] for d in ("S", "E", "Ec")}
    original = record["unit_text"]
    text, offsets = v25.baseline.matching_view(original)
    has_drug_scope = _drug_scope(result, text)

    def add(rule, dim, start, end, subtype, dependency=None):
        raw_start, raw_end = _raw_span(offsets, start, end)
        if any(e.get("rule") == rule and e.get("start") == raw_start and e.get("end") == raw_end
               for e in result["evidence"]):
            return
        evidence = {
            "rule": rule, "dimension": dim, "start": raw_start, "end": raw_end,
            "text": original[raw_start:raw_end], "matching_text": text[start:end],
            "subtype": subtype, "protocol_basis": RULE_SPEC[rule]["manual_basis"],
            "required_relation": RULE_SPEC[rule]["required"],
        }
        if dependency:
            evidence["context_dependency"] = dependency
        result["evidence"].append(evidence)

    def suppress(rule, reason, match=None):
        item = {"rule": rule, "reason": reason, "excluded": RULE_SPEC[rule]["excluded"]}
        if match is not None:
            a, b = _raw_span(offsets, match.start(), match.end())
            item.update(start=a, end=b, text=original[a:b])
        result["v26_if_suppressions"].append(item)

    def suppress_existing(rule, dim, pattern):
        """Drop inherited evidence only where its span has a wrong object."""
        for match in re.finditer(pattern, text):
            raw_start, raw_end = _raw_span(offsets, match.start(), match.end())
            dropped = [e for e in result["evidence"] if e["dimension"] == dim
                       and raw_start <= e["start"] and e["end"] <= raw_end]
            if not dropped:
                continue
            result["evidence"] = [e for e in result["evidence"] if e not in dropped]
            for evidence in dropped:
                result["suppressions"].append({
                    "rule": rule, "dimensions": [dim], "start": evidence["start"],
                    "end": evidence["end"], "text": evidence["text"],
                    "suppressed_rule": evidence["rule"], "reason": RULE_SPEC[rule]["excluded"],
                })
            result["v26_if_suppressions"].append({
                "rule": rule, "reason": "wrong_semantic_object",
                "excluded": RULE_SPEC[rule]["excluded"],
                "start": raw_start, "end": raw_end, "text": original[raw_start:raw_end],
            })

    # Repair inherited object leakage span by span. Independent genuine drug
    # evidence elsewhere in a mixed unit remains intact.
    suppress_existing(
        "V26_I_non_drug_system_object", "I",
        r"(?:创新性(?:的)?(?:信息|数据|申报|办公|管理)(?:管理)?系统|"
        r"(?:信息|数据|申报|办公|管理)(?:管理)?系统(?:的)?创新性)",
    )
    suppress_existing(
        "V26_F_data_access_object", "F",
        r"(?:数据|证据|文献|模型参数|信息系统)(?:的)?(?:可及性|可获得性)"
        r"|(?:可及|可获得)(?:性)?(?:的)?(?:数据|证据|文献|模型参数)",
    )

    # I: direct modification-to-product-attribute relations.  The grammar is
    # anchored to the action and target, not a fixed word distance or one order.
    modification_matches = list(_MOD_RELATION.finditer(text))
    # Every target in _MOD_TARGET is itself a drug/product attribute, so the
    # direct action-target relation establishes the needed object scope.
    for match in modification_matches:
        add("V26_I_product_modification_relation", "I", match.start(), match.end(), "attribute")
    if (not modification_matches and re.search(r"改良|改善|优化|改进|开发", text)
            and re.search(r"剂型|规格|适老|便利", text)):
        suppress("V26_I_product_modification_relation", "specific_modified_drug_attribute_not_stated")

    # I: policy purpose and data-protection mechanism must co-occur in the
    # same proposition after document titles are blanked.
    for sentence in _sentences(text):
        value = v25._without_titles(sentence.group())
        goal = re.search(r"(?:促进|支持|鼓励|推动|激励|服务于|有利于)[^。；;]*(?:药品|药物|新药)(?:的)?创新(?:发展|研发)?", value)
        mechanism = re.search(r"(?:完善|建立|健全|实施|制定|强化|扩大)[^。；;]*(?:药品)?(?:试验)?数据保护(?:制度|机制|办法|政策)", value)
        if goal and mechanism:
            a, b = _cover((goal, mechanism))
            if re.search(r"归档|文件命名|编号整理|格式转换", value[a:b]):
                suppress("V26_I_data_protection_support_relation", "document_carrier_operation_only", sentence)
            else:
                add("V26_I_data_protection_support_relation", "I", sentence.start()+a, sentence.start()+b, "research_support")
        elif re.search(r"数据保护(?:制度|机制|办法|政策|文件)", value):
            suppress("V26_I_data_protection_support_relation", "explicit_drug_innovation_goal_missing", sentence)

    # I: use direct grammatical relations rather than mere sentence-level
    # co-occurrence. Negative/cancelled support still discusses I; only pure
    # registration/archiving is excluded from this research-support subtype.
    for match in _RND_SUPPORT.finditer(text):
        sentence = next(s for s in _sentences(text) if s.start() <= match.start() < s.end())
        value = v25._without_titles(sentence.group())
        if re.search(r"仅(?:统计|登记|询问|归档)|按编号归档|材料填报", value):
            suppress("V26_I_drug_research_support_relation", "support_identity_or_carrier_record_only", match)
        else:
            add("V26_I_drug_research_support_relation", "I", match.start(), match.end(), "research_support")

    # F: flexible modifier order for an explicit lack of treatment, still
    # requiring the drug-treatment object resolved by the inherited engine.
    gaps = list(_GAP.finditer(text))
    if gaps:
        for match in gaps:
            gap_has_scope = has_drug_scope or "无药可治" in match.group()
            if not gap_has_scope:
                suppress("V26_F_treatment_gap_relation", "drug_treatment_object_not_established", match)
                continue
            add("V26_F_treatment_gap_relation", "F", match.start(), match.end(), "access")

    # F: treatment opportunity is not enough by itself.  It must be linked to
    # an explicit pre-existing gap in this same analysis unit.
    opportunities = list(_OPPORTUNITY.finditer(text))
    for match in opportunities:
        if gaps and (has_drug_scope or any("无药可治" in g.group() for g in gaps)):
            add("V26_F_treatment_opportunity_from_gap", "F", match.start(), match.end(), "access")
        else:
            suppress("V26_F_treatment_opportunity_from_gap", "preexisting_treatment_gap_missing", match)

    # F: task and obstacle are grammatically joined, so general convenience or
    # a patient-group name cannot create clinical-management evidence.
    obstacle_matches = list(_USE_OBSTACLE.finditer(text))
    if has_drug_scope:
        for match in obstacle_matches:
            add("V26_F_drug_use_obstacle_relation", "F", match.start(), match.end(), "clinical_management")
    else:
        for match in obstacle_matches:
            suppress("V26_F_drug_use_obstacle_relation", "drug_use_object_not_established", match)
    if (not obstacle_matches and re.search(_USE_TASK, text)
            and re.search(r"便利|方便|适宜|建议|可考虑", text)):
        suppress("V26_F_drug_use_obstacle_relation", "explicit_obstacle_or_complexity_missing")

    # F: resolve only the narrow same-paragraph anaphor documented in the
    # development mechanism.  Context supplies the antecedent, never a label.
    if re.search(r"此类用药行为", text) and re.search(r"多病共存|多重用药", text):
        linked = False
        for paragraph in record.get("paragraph_context", []):
            whole = v25.baseline.matching_view(paragraph["text"])[0]
            if whole.count(text) != 1:
                continue
            prefix = whole.split(text, 1)[0]
            antecedents = list(re.finditer(r"多种药物同时使用|不同药物[^。；;]*不同时间服用|不同(?:的)?给药途径", prefix))
            if not antecedents:
                continue
            current = re.search(r"此类用药行为[^。；;]*(?:多病共存|多重用药)[^。；;]*问题", text)
            if current:
                antecedent = "；".join(m.group() for m in antecedents)
                add("V26_F_anaphoric_management_complexity", "F", current.start(), current.end(),
                    "clinical_management", _dependency(record, paragraph,
                    "same_paragraph_drug_use_complexity_antecedent", antecedent))
                linked = True
                break
        if not linked:
            suppress("V26_F_anaphoric_management_complexity", "same_paragraph_complexity_antecedent_missing")

    result["labels"]["I"] = int(any(e["dimension"] == "I" for e in result["evidence"]))
    result["labels"]["F"] = int(any(e["dimension"] == "F" for e in result["evidence"]))
    result["innovation_subtypes"] = sorted({e["subtype"] for e in result["evidence"]
                                             if e["dimension"] == "I" and e.get("subtype")})
    result["innovation_unclassified_evidence"] = [e for e in result["evidence"]
                                                    if e["dimension"] == "I" and not e.get("subtype")]
    result["innovation_subtype_status"] = ("needs_review" if result["innovation_unclassified_evidence"]
                                            else "complete" if result["labels"]["I"] else "not_applicable")
    result["fairness_subtypes"] = sorted({e["subtype"] for e in result["evidence"]
                                           if e["dimension"] == "F" and e.get("subtype")})
    assert {d: result["labels"][d] for d in ("S", "E", "Ec")} == locked
    return result
