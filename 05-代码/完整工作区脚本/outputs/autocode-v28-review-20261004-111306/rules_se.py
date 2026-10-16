"""Bounded CAL-5D v1.3 review layer for safety (S) and effectiveness (E).

``revise`` mutates only S/E evidence plus suppression and review-flag trails.
The caller owns label rebuilding.  Matching uses ``RuleView`` so document
titles are blanked without changing offsets into the supplied original text.
"""
from __future__ import annotations

import re

from rule_support import RuleView, baseline


VERSION = "v28-se-directed-review-1"

S_BASIS = (
    "CAL-5D v1.3 S: 药物或用药损害及其识别、评价、预防和控制；"
    "安全性资料要求计入，非药物安全与纯事务性提及排除。"
)
E_BASIS = (
    "CAL-5D v1.3 E: 药物防治效果、临床获益、治疗优势、疗效终点、"
    "相关生活质量及其研究证据；否定或不确定陈述仍计入。"
)

_LOCAL_DRUG = re.compile(
    r"药品|药物|用药|新药|仿制药|制剂|本品|该药|试验药|研究药|"
    r"药效|中药|中成药|西药|疫苗|某药|处方|片剂|胶囊"
)
_NON_DRUG_OBJECT = re.compile(
    r"员工培训|人员培训|培训活动|培训|外科手术|手术治疗|放射治疗|放疗|"
    r"心理治疗|心理干预|康复训练|康复治疗|营养治疗|运动干预|物理治疗|护理措施|员工福利|"
    r"医疗质量[（(]安全[）)]|软件|(?:信息|申报|管理|数据|计算机化)系统|管理制度"
)
_DIMENSION_CONTENT = re.compile(
    r"安全性|不良事件|不良反应|毒性|禁忌|副作用|风险控制|风险管理|"
    r"有效性|疗效|治疗效果|干预效果|临床获益|"
    r"治疗获益|生活质量|生命质量|临床终点|生存期|缓解率|获益[-—－]?风险"
)
_HARM = re.compile(
    r"不良反应|不良事件|毒性|禁忌|副作用|(?:用药|给药)错误|药物警戒|"
    r"药物相互作用|药物相关风险|安全信号|非预期严重损害|"
    r"死亡与治疗的相关性|安全性风险|潜在治疗风险"
)
_EFFECT = re.compile(
    r"有效性|疗效|药效(?:学)?(?!动力学)|临床获益|治疗获益|治疗效果|临床效果|"
    r"临床优势|治疗优势|治疗价值|药物效果|抗肿瘤活性|干预效果|"
    r"有效治疗|疾病控制率|客观缓解(?:率)?|总缓解率|完全缓解|部分缓解|"
    r"无进展生存(?:期)?|总生存(?:期)?|无病生存(?:期)?|事件无发生生存(?:期)?|"
    r"缓解持续时间|生存率|生存期|健康效用|QALY"
)
_BENEFIT_RISK = re.compile(r"获益\s*[-—－、/与和]?\s*风险|风险\s*[-—－、/与和]?\s*获益")
_ABBREVIATION = re.compile(r"(?<![A-Za-z])(?:SAE|SUSAR|ADR|AE)(?![A-Za-z])", re.I)
_ABBREVIATION_USE = re.compile(
    r"发生(?:率|情况)?|分级|严重|致死|死亡|停药|减量|相关性|列表|报告|"
    r"呈现|汇总|统计|分析|评价|监测|信号|判定|识别|相关|无关|不列入|分级|级"
)
_ABBREVIATION_DEFINITION = re.compile(
    r"(?:严重不良事件|非预期严重不良反应|药品不良反应|不良事件)\s*"
    r"[（(]?(?:SAE|SUSAR|ADR|AE)[）)]?"
    r"|(?:SAE|SUSAR|ADR|AE)\s*[（(]?(?:严重不良事件|非预期严重不良反应|"
    r"药品不良反应|不良事件)[）)]?",
    re.I,
)


def _clause_at(view, start):
    return next((m for m in view.clauses() if m.start() <= start < m.end()), None)


def _scoped(view, value=""):
    if _non_drug_proposition(value):
        return False
    if _mixed_treatment_parents(view) and not _LOCAL_DRUG.search(value):
        return False
    return bool(_LOCAL_DRUG.search(value) or view.drug_scope or _verified_scope(view))


def _parent_texts(view):
    return [baseline.matching_view(p["text"])[0]
            for p in view.record.get("verified_parent_context", []) if p.get("text")]


def _mixed_treatment_parents(view):
    qualifications = [baseline.matching_view(p["text"])[0]
                      for p in view.record.get("verified_scope_qualifications_v28", [])
                      if p.get("text")]
    return any(re.search(r"治疗选择[^。]*(?:用药|药物|非处方药)[^。]*"
                         r"(?:替代和支持疗法|非药物治疗)", text)
               for text in _parent_texts(view) + qualifications)


def _data_risk_parents(view):
    # A governing subsection, not a paragraph that merely mentions both risks.
    return any(re.fullmatch(r"(?:[（(]?[一二三四五六七八九十0-9]+[）).、]?)?"
                            r"数据(?:可靠性|质量)(?:的)?(?:相关)?风险控制措施", text.strip())
               for text in _parent_texts(view))


def _verified_scope(view):
    # The inherited input gate validates source/target/text hashes for every
    # supplied scope. Its old lexical activation window is not an additional
    # semantic requirement: scope resolves the object, never creates a label.
    return next((s for s in view.record.get("verified_object_scope", [])
                 if s.get("kind") in {"drug_clinical_trial", "drug_regulatory_research",
                                      "anticancer_drug_development",
                                      "anticancer_drug_safety_dossier"}), None)


def _review_add(view, rule, dimension, start, end, dependency=None, safety_basis=None):
    scope = _verified_scope(view)
    if dependency is None and scope and not _LOCAL_DRUG.search(view.text):
        dependency = {"kind": "verified_drug_object_scope", "scope_kind": scope["kind"],
                      "source_sha256": scope["source_sha256"],
                      "scope_text_sha256": scope["text_sha256"],
                      "scope_text": scope["text"], "locator": scope["locator"]}
    added = view.add(rule, dimension, start, end, basis=S_BASIS if dimension == "S" else E_BASIS,
                     dependency=dependency, safety_basis=safety_basis)
    if rule.startswith("V28_"):
        added["rule_release"] = VERSION
    return added


def _non_drug_proposition(value):
    """An explicit competing object defeats a remote drug noun, not patients.

    A later drug object or an explicit drug/non-drug comparison can retain a
    drug-effect relation within the same proposition.
    """
    for obj in _NON_DRUG_OBJECT.finditer(value):
        if _LOCAL_DRUG.search(value[:obj.start()]) and re.search(
                r"与|和|比较|相比|对照", value[:obj.start()]):
            continue
        content = _DIMENSION_CONTENT.search(value, obj.end())
        if content and not _LOCAL_DRUG.search(value[obj.end():content.start()]):
            return True
    return False


def _flag(result, rule, reason, start=None, end=None, text=None):
    item = {
        "rule": rule,
        "reason": reason,
        "action": "manual_scope_review_no_positive_added",
        "rule_release": VERSION,
    }
    if start is not None:
        item.update(start=start, end=end, text=text)
    if not any(all(existing.get(k) == v for k, v in item.items())
               for existing in result.setdefault("review_flags", [])):
        result["review_flags"].append(item)


def _drop_pattern(view, dimension, pattern, rule, reason, source=None):
    value = view.text if source is None else source
    removed = []
    for match in re.finditer(pattern, value, re.I):
        removed.extend(view.drop_within(dimension, match.start(), match.end(), rule, reason))
    return removed


def _drop_known_wrong_objects(view):
    # Each pattern is deliberately local.  A second, genuine S/E proposition
    # elsewhere in the same unit is outside the dropped span and survives.
    s_wrong = [
        r"(?:数据库|软件|信息平台|服务器|计算机)[^。；;，,]{0,18}"
        r"(?<![A-Za-z])(?:SAE|SUSAR|ADR|AE)(?![A-Za-z])",
        r"(?:网络|信息系统|服务器|计算机|软件|基金|生产|施工|消防|食品)"
        r"[^。；;，,、]{0,18}(?:安全性|安全风险|风险控制|风险管理|风险最小化)",
        r"(?:电子数据|元数据|数据)(?:的)?"
        r"(?:(?:可靠性|可追溯性|完整性|保密性)[、和与及]*)*安全性",
        r"(?:安全性|安全风险|风险控制|风险管理|风险最小化)"
        r"(?:检查|校验|验证)(?:针对|用于)?(?:网络|信息系统|服务器|计算机|软件)",
        r"(?:质量管理活动|质量管理体系|质量体系|工作流程|项目管理)"
        r"[^。；;，,]{0,30}(?:风险控制|风险管理|风险最小化)",
        r"(?:风险控制|风险管理|风险最小化)"
        r"[^。；;，,]{0,30}(?:质量管理活动|质量管理体系|质量体系|工作流程|项目管理)",
        r"(?:人员|专家|研究者|评审员|工作人员)[^。；;，,]{0,28}"
        r"安全性(?:评价|研究|审评)?(?:经验|经历|专业|背景|资质|能力)",
        r"(?:人员|专家|研究者|评审员|工作人员)[^。；;，,]{0,28}"
        r"安全性[^。；;，,]{0,20}(?:经验|经历|专业|背景|资质|能力)",
        r"安全性(?:评价|研究|审评)?(?:经验|经历|专业|背景|资质|能力)"
        r"[^。；;，,]{0,20}(?:人员|专家|研究者|评审员|工作人员)",
        r"药物非临床安全性评价研究机构",
        r"药物运输中的安全性",
        r"医疗用毒性药品",
        r"安全性(?:评价|研究|审评)?(?:经验|经历|专业背景|专业知识|资质)",
        r"安全性(?:和|与|及|、)(?:有效性|疗效)(?:评价|研究|审评)?"
        r"(?:经验|经历|专业背景|专业知识|资质)",
    ]
    for pattern in s_wrong:
        _drop_pattern(view, "S", pattern, "V27_S_wrong_semantic_object",
                      "安全或风险的对象不是药物/用药损害，按局部片段抑制。")

    e_wrong = [
        r"(?:质量管理活动|质量管理体系|管理体系|管理制度|归档制度|会议制度|"
        r"工作流程|信息系统|管理系统|软件|算法|模型|账号|身份|方法)"
        r"[^。；;，,]{0,18}(?:的)?有效性",
        r"(?:数据|证据|统计|科学)(?:的)?(?:有效性|效度)",
        r"有效期|有效账号|有效身份|行政效率|工作效率|运行效率",
        r"(?:培训|宣传|教育|管理|流程|软件)[^。；;，,]{0,18}干预效果",
        r"(?:人员|专家|研究者|评审员|工作人员)[^。；;，,]{0,28}"
        r"(?:有效性|疗效)(?:评价|研究|审评)?(?:经验|经历|专业|背景|资质|能力)",
        r"(?:人员|专家|研究者|评审员|工作人员)[^。；;，,]{0,28}"
        r"(?:有效性|疗效)[^。；;，,]{0,20}(?:经验|经历|专业|背景|资质|能力)",
        r"(?:有效性|疗效)(?:评价|研究|审评)?(?:经验|经历|专业|背景|资质|能力)"
        r"[^。；;，,]{0,20}(?:人员|专家|研究者|评审员|工作人员)",
        r"(?:员工|工作人员|一般居民)[^。；;，,]{0,15}(?:生活质量|生命质量)",
        r"以药品临床价值为导向",
        r"(?:有效性|疗效)(?:评价|研究|审评)?(?:经验|经历|专业背景|专业知识|资质)",
    ]
    for pattern in e_wrong:
        _drop_pattern(view, "E", pattern, "V27_E_wrong_semantic_object",
                      "有效/效果的对象不是药物防治效果或临床获益，按局部片段抑制。")
    for dim in ("S", "E"):
        _drop_pattern(view, dim,
                      r"(?:软件|信息系统|数据库|信息平台)[^。；;，,]{0,18}"
                      r"(?:获益[-—－、/与和]?风险|风险[-—－、/与和]?获益)",
                      "V27_SE_non_drug_benefit_risk", "获益风险评价的局部对象为非药物系统。")
    for part in re.finditer(r"(?:(?!并|同时|另须|且)[^。；;，,])+", view.text):
        if _non_drug_proposition(part.group()):
            for dim in ("S", "E"):
                view.drop_within(dim, part.start(), part.end(),
                                 "V27_SE_explicit_non_drug_proposition",
                                 "当前评价对象明确为非药物活动或干预，不借用其他命题的药物对象。")


def _drop_transactions_and_titles(view):
    # v25 already masks titles, but this makes the S/E contract explicit and
    # also handles inherited evidence from older result variants.
    for title in re.finditer(r"《[^》]+》", view.normalized):
        for dim in ("S", "E"):
            view.drop_within(dim, title.start(), title.end(), "V27_SE_document_title",
                             "书名本身不构成当前单元的安全性或有效性命题。")

    # Work at the proposition level: a coordinated substantive requirement
    # survives even when the adjacent proposition archives its report.
    for part in re.finditer(r"(?:(?!并|同时|另须|且)[^。；;，,])+", view.text):
        value = part.group()
        operation = re.search(r"归档|文件命名|文件名|改名|编号整理|格式转换|上传格式|"
                              r"文件格式|PDF格式|保密|公开|公示|每年提交一次|提交时点", value)
        action_view = re.sub(r"(?:安全性|有效性|疗效)(?:评价|研究|分析)(?:报告|资料|文件)",
                             "", value)
        content = re.search(r"评价|评估|比较|分析|收集|补充|研究|监测|汇总|"
                            r"报告[^。；;，,]*(?:发生率|发生情况|严重程度)|"
                            r"提交[^。；;，,]*(?:数据|证据|信息|资料)", action_view)
        if operation and not content:
            for dim in ("S", "E"):
                view.drop_within(dim, part.start(), part.end(),
                                 "V27_SE_carrier_operation_only",
                                 "仅处理文件载体、格式、披露或时点，未新增维度内容要求。")


def _add_safety(view):
    # Explicit drug harms and safety evidence, including negated findings.
    patterns = [
        ("V27_S_drug_harm", _HARM),
        ("V27_S_explicit_safety_content", re.compile(
            r"(?:药品|药物|用药|本品|该药|试验药|研究药)(?:的)?"
            r"(?:安全性|安全风险|安全特征|安全数据|安全信息|安全证据)"
            r"|(?:安全性|安全风险|安全特征)(?:尚不明确|尚不确定|未明确|无明显问题|良好|可控)")),
        ("V27_S_evidence_requirement", re.compile(
            r"(?:收集|提交|提供|补充|报告|呈现|汇总|分析|评价|评估|监测|审查|总结)"
            r"[^。；;，,]{0,45}?(?P<content>安全性|不良反应|不良事件|毒性|安全信号)"
            r"(?:数据|信息|证据|资料|结果|发生率|情况)?")),
    ]
    for rule, pattern in patterns:
        for match in pattern.finditer(view.text):
            clause = _clause_at(view, match.start())
            value = clause.group() if clause else match.group()
            if rule != "V27_S_drug_harm" and not _scoped(view, value):
                continue
            if rule == "V27_S_drug_harm" and not (_scoped(view, value)
                    or re.search(r"(?:用药|给药)错误|药物警戒|药物相互作用|药物相关风险", match.group())):
                _flag(view.result, rule, "药物/用药对象未建立", *view.raw_span(match.start(), match.end()),
                      view.original[slice(*view.raw_span(match.start(), match.end()))])
                continue
            start, end = match.span("content") if rule == "V27_S_evidence_requirement" else match.span()
            view.add(rule, "S", start, end, basis=S_BASIS,
                     safety_basis="other_safety")

    for match in re.finditer(r"(?:药品|药物)(?:的)?质量(?:安全|风险)", view.text):
        view.add("V27_S_drug_quality_safety", "S", match.start(), match.end(), basis=S_BASIS,
                 safety_basis="quality_safety")

    # Benefit-risk explicitly contains a risk assessment.  Its benefit side is
    # handled under E below, with the same object requirement.
    for match in _BENEFIT_RISK.finditer(view.text):
        clause = _clause_at(view, match.start())
        value = clause.group() if clause else match.group()
        if _scoped(view, value):
            view.add("V27_S_benefit_risk", "S", match.start(), match.end(), basis=S_BASIS,
                     safety_basis="other_safety")
        else:
            a, b = view.raw_span(match.start(), match.end())
            _flag(view.result, "V27_S_benefit_risk", "获益风险的药物对象未建立", a, b,
                  view.original[a:b])

    # AE-family abbreviations require both a safety use and an established
    # drug/safety scope.  A same-paragraph expansion is recorded as dependency.
    for match in _ABBREVIATION.finditer(view.text):
        clause = _clause_at(view, match.start())
        value = clause.group() if clause else view.text
        if not _ABBREVIATION_USE.search(value):
            continue
        # A drug word in a different proposition cannot resolve an explicit
        # database/software object; carrier operations are suppressed below.
        if re.search(r"数据库|软件|信息平台|服务器|计算机", value):
            continue
        dependency = None
        for paragraph, prefix in view.paragraph_prefixes():
            definition = next((d for d in _ABBREVIATION_DEFINITION.finditer(prefix)
                               if re.search(r"(?<![A-Za-z])" + re.escape(match.group()) +
                                            r"(?![A-Za-z])", d.group(), re.I)), None)
            if definition:
                dependency = view.dependency(paragraph, "same_paragraph_adverse_event_abbreviation",
                                             definition.group())
                break
        object_dependencies = view.result.get("object_scope_dependencies") or []
        if not (_LOCAL_DRUG.search(value) or dependency or object_dependencies or _verified_scope(view)):
            a, b = view.raw_span(match.start(), match.end())
            _flag(view.result, "V27_S_adverse_event_abbreviation",
                  "缩写有安全性用法但缺药物对象或同段释义", a, b, view.original[a:b])
            continue
        if dependency is None and object_dependencies and not _LOCAL_DRUG.search(value):
            dependency = {
                "kind": "verified_drug_object_scope",
                "scopes": object_dependencies,
            }
        _review_add(view, "V27_S_adverse_event_abbreviation", "S", match.start(), match.end(),
                    dependency=dependency, safety_basis="other_safety")

    # A generic control phrase inherits S only from an explicit, same-clause
    # harm anchor or an unambiguous same-paragraph antecedent.
    for match in re.finditer(r"风险(?:控制|管理|最小化)(?:措施|计划)?", view.text):
        clause = _clause_at(view, match.start())
        value = clause.group() if clause else match.group()
        if (_HARM.search(value) or re.search(r"药品质量风险|药物[^。；;，,]{0,12}风险", value)):
            safety_basis = ("quality_safety" if re.search(r"药品质量风险", value)
                            and not _HARM.search(value) else "other_safety")
            view.add("V27_S_harm_control_relation", "S", match.start(), match.end(), basis=S_BASIS,
                     safety_basis=safety_basis)
            continue
        linked = False
        for paragraph, prefix in view.paragraph_prefixes():
            antecedents = list(_HARM.finditer(prefix))
            if antecedents:
                antecedent = antecedents[-1].group()
                view.add("V27_S_harm_control_context", "S", match.start(), match.end(), basis=S_BASIS,
                         dependency=view.dependency(paragraph, "same_paragraph_drug_harm_antecedent",
                                                    antecedent),
                         safety_basis="other_safety")
                linked = True
                break
        if not linked and not any(e.get("dimension") == "S" and e.get("start") <= view.raw_span(
                match.start(), match.end())[0] < e.get("end") for e in view.result["evidence"]):
            a, b = view.raw_span(match.start(), match.end())
            _flag(view.result, "V27_S_harm_control_relation",
                  "风险控制未与药物损害或质量安全锚点绑定", a, b, view.original[a:b])


def _add_effectiveness(view):
    # Direct effects, negative findings and uncertainty all discuss E.
    for match in _EFFECT.finditer(view.text):
        clause = _clause_at(view, match.start())
        value = clause.group() if clause else match.group()
        if re.search(r"以药品临床价值为导向", value) and not re.search(
                r"评价|评估|比较|数据|证据|结果|优势|获益", value):
            continue
        if not _scoped(view, value) and not re.search(r"药效|药物效果", match.group()):
            a, b = view.raw_span(match.start(), match.end())
            _flag(view.result, "V27_E_effect_claim", "泛化效果词缺少药物治疗对象", a, b,
                  view.original[a:b])
            continue
        view.add("V27_E_effect_claim", "E", match.start(), match.end(), basis=E_BASIS)

    # Named clinical endpoints and common abbreviations.  Abbreviations need a
    # drug/clinical endpoint context so OS cannot mean an operating system.
    endpoint = re.compile(
        r"(?:主要|次要|关键|替代)?(?:疗效|有效性|临床)(?:终点|结局指标)"
        r"|客观缓解率|总缓解率|疾病控制率|完全缓解率|部分缓解率|"
        r"无进展生存期|总生存期|无病生存期|事件无发生生存期|缓解持续时间"
        r"|(?<![A-Za-z])(?:ORR|PFS|OS|DFS|EFS|DOR)(?![A-Za-z])"
    , re.I)
    for match in endpoint.finditer(view.text):
        clause = _clause_at(view, match.start())
        value = clause.group() if clause else match.group()
        abbreviation = re.fullmatch(r"(?:ORR|PFS|OS|DFS|EFS|DOR)", match.group(), re.I)
        if not _scoped(view, value):
            continue
        if abbreviation and not (_scoped(view, value) and re.search(
                r"终点|生存|缓解|疗效|肿瘤|患者|受试者|试验", value)):
            a, b = view.raw_span(match.start(), match.end())
            _flag(view.result, "V27_E_clinical_endpoint", "终点缩写缺少临床药效语境", a, b,
                  view.original[a:b])
            continue
        view.add("V27_E_clinical_endpoint", "E", match.start(), match.end(), basis=E_BASIS)

    for match in re.finditer(r"(?:患者报告结局|健康相关的生活质量|患者[^。；;，,]{0,18}(?:生活质量|生命质量))",
                             view.text):
        clause = _clause_at(view, match.start())
        value = clause.group() if clause else match.group()
        clinical_link = (match.group() != "患者报告结局" or re.search(
            r"疗效|治疗效果|临床获益|生存|缓解|临床终点|评估终点|治疗后|用药后", value))
        if _scoped(view, value) and clinical_link:
            view.add("V27_E_patient_outcome", "E", match.start(), match.end(), basis=E_BASIS)

    for match in re.finditer(
            r"(?:药品|药物|用药|治疗方案)[^。；;]{0,24}(?:指南|诊疗规范)(?:推荐|建议)"
            r"|(?:指南|诊疗规范)(?:推荐|建议)[^。；;]{0,24}(?:药品|药物|用药|治疗方案)",
            view.text):
        view.add("V27_E_guideline_drug_recommendation", "E", match.start(), match.end(), basis=E_BASIS)

    for match in re.finditer(
            r"(?:收集|提交|提供|补充|报告|呈现|汇总|分析|评价|评估|比较|判断)"
            r"[^。；;，,]{0,55}?(?P<content>有效性|疗效|药效(?!动力学)|临床获益|治疗效果|临床优势)"
            r"(?:数据|信息|证据|资料|结果|终点)?",
            view.text):
        clause = _clause_at(view, match.start())
        value = clause.group() if clause else match.group()
        if _scoped(view, value):
            view.add("V27_E_evidence_requirement", "E", *match.span("content"), basis=E_BASIS)

    # Within a drug-scoped benefit-risk assessment, "benefit" denotes the
    # therapeutic side of the balance and therefore supports E as well as S.
    for match in _BENEFIT_RISK.finditer(view.text):
        clause = _clause_at(view, match.start())
        value = clause.group() if clause else match.group()
        if _scoped(view, value):
            view.add("V27_E_benefit_risk_clinical_benefit", "E", match.start(), match.end(), basis=E_BASIS)
        else:
            a, b = view.raw_span(match.start(), match.end())
            _flag(view.result, "V27_E_benefit_risk_clinical_benefit",
                  "获益风险的药物治疗对象未建立", a, b, view.original[a:b])

    for match in re.finditer(
            r"(?:人群|样本|研究对象)(?:的)?代表性[^。；;]{0,30}"
            r"(?:支持|用于|影响)[^。；;]{0,24}(?:疗效|有效性|治疗效果|临床获益)(?:判断|评价|评估|外推)?"
            r"|(?:疗效|有效性|治疗效果|临床获益)(?:判断|评价|评估|外推)"
            r"[^。；;]{0,24}(?:依赖|需要)[^。；;]{0,20}(?:人群|样本|研究对象)(?:的)?代表性",
            view.text):
        view.add("V27_E_representativeness_effect_link", "E", match.start(), match.end(), basis=E_BASIS)


def _review_direct_content(view):
    """Protocol groups recovered in the directed review; no source-ID routing."""
    # 高警示/高危 are drug-class names, not medication-error evidence. Keep
    # explicit confusion/error or safety predicates; never infer harm control
    # merely from a class name plus administrative handling/channel controls.
    safety = [
        ("V28_S_medication_error_prevention",
         r"(?:药物|药品)[^。；;，,]{0,12}(?:误吸|误服|误选|误用)(?:或误服)?(?:风险)?"
         r"|(?:识别|评估|防范)(?:用药|给药)风险|配伍禁忌"
         r"|(?:混淆不同|易混淆)药品"
         r"|(?:电解质|辅料)(?:和辅料)?过量(?:问题)?"
         r"|(?:处方剂量|用法用量|药品给药速度)[、和用法]{0,5}是否(?:正确|适宜)"
         r"|(?:药品[^。；;，,]{0,18})?过敏试验(?:及结果的判定)?"),
        ("V28_S_patient_harm_control",
         r"(?:患者|受试者|试验参与者)(?:的)?(?:权益和|利益和)?安全"
         r"|(?:患者|受试者|试验参与者)(?:的)?紧急危害"
         r"|患者风险分层和管理|风险损害发生的可能性"
         r"|安全(?:合理)?用药|风险管控(?:计划|措施)"
         r"|(?:根据|依据)试验的风险程度"
         r"|紧急医学状态[^。；;，,]{0,24}识别临床试验用药品"),
        ("V28_S_safety_evidence_content", r"安全性(?:信息|数据|研究)|毒理试验"),
    ]
    for rule, pattern in safety:
        for match in re.finditer(pattern, view.text):
            part = _clause_at(view, match.start())
            value = part.group() if part else match.group()
            if _scoped(view, value) or match.group() == "配伍禁忌":
                _review_add(view, rule, "S", *match.span(), safety_basis="other_safety")

    for match in re.finditer(r"药品(?:和|与|及|、)?医疗器械质量安全", view.text):
        _review_add(view, "V28_S_coordinated_drug_quality_safety", "S", *match.span(),
                    safety_basis="quality_safety")
    for match in re.finditer(r"(?:安全[、,，]有效[、,，]经济(?:的)?用药原则|"
                             r"药品(?:和|与|及|、)?医疗器械质量安全[、,，]有效)", view.text):
        for dim in ("S", "E"):
            if dim == "S" and "质量安全" in match.group():
                continue
            _review_add(view, "V28_SE_drug_use_value_requirement", dim, *match.span(),
                        safety_basis="other_safety" if dim == "S" else None)

    # Comparative wording can separate benefit and risk by more than a dash.
    for match in re.finditer(r"获益(?:明显|显著)?(?:大于|超过)[^。；;，,]{0,35}风险", view.text):
        if _scoped(view, match.group()):
            for dim in ("S", "E"):
                _review_add(view, "V28_SE_benefit_exceeds_risk", dim, *match.span(),
                            safety_basis="other_safety" if dim == "S" else None)
    if re.search(r"片剂|胶囊|制剂|剂型", view.text) and re.search(
            r"吞咽|黏附|吸收|释放|口腔", view.text):
        for match in re.finditer(r"影响(?:治疗|疗效)[^。；;，,]{0,20}(?:风险|损害)", view.text):
            for dim in ("S", "E"):
                _review_add(view, "V28_SE_formulation_clinical_impact", dim, *match.span(),
                            safety_basis="other_safety" if dim == "S" else None)

    effect_patterns = [
        ("V28_E_therapeutic_response", r"治疗应答(?:者)?|(?:肿瘤)?耐药|生存获益"
         r"|(?:该|试验|治疗)?药物(?:绝对|完全|显著)?无效"
         r"|药物治疗的重要受益者|(?:没有|无)预期获益"
         r"|试验药物(?:显著)?优于安慰剂(?:/阳性对照药)?"
         r"|疼痛感[^。；;，,]{0,20}(?:改善|缓解)"
         r"|(?:减少|避免)[^。；;，,]{0,12}无效暴露"),
        ("V28_E_effect_judgement_link", r"实效比较研究(?:的结果)?"
         r"|药物暴露的效应|有偏倚的效应估计"
         r"|临床结局(?:定义|相关|的评估)|与临床结局相关的重要变量和信息"
         r"|临床实际意义|临床试验终点"
         r"|(?:药品与参比药品)?满足临床需求程度"
         r"|产品用于目标适应症的立题依据"
         r"|新增适应症[^。；;，,]{0,18}(?:RCT|随机对照试验)支持"
         r"|评估这些干预对健康相关的[^。；;，,]{0,20}结局的影响"),
    ]
    for rule, pattern in effect_patterns:
        for match in re.finditer(pattern, view.text):
            part = _clause_at(view, match.start())
            if _scoped(view, part.group() if part else match.group()):
                _review_add(view, rule, "E", *match.span())

    # Title content may establish the identity of a treatment guideline in an
    # explicit inclusion relation. Evidence is the current predicate/object,
    # never a dimension word found only inside a document title.
    for match in re.finditer(r"纳入(?:最新(?:版)?)?《[^》]*(?:诊疗方案|用药指南|药物治疗指南)"
                             r"[^》]*》(?:的)?药品", view.normalized):
        start, end = match.end() - 2, match.end()
        _review_add(view, "V28_E_guideline_inclusion_relation", "E", start, end)


def _review_bound_references(view):
    """Explicit current predicates plus a unique same-paragraph referent."""
    for paragraph in view.record.get("paragraph_context", []):
        full = baseline.matching_view(paragraph["text"])[0]
        if full.count(view.normalized) != 1:
            continue
        prefix = full.split(view.normalized, 1)[0]
        antecedents = [s for s in re.findall(r"[^。]+", prefix) if s.strip()]
        previous = antecedents[-1] if antecedents else ""
        specs = [
            ("V28_S_adverse_event_decision_reference", "S",
             r"修正判定结果", r"(?:AE|ADR|不良事件|不良反应)[^。]{0,100}判定依据", prefix),
            ("V28_S_safety_summary_reference", "S",
             r"相关信息进行简述", r"概述非临床研究的安全性发现[^。]*", previous),
            ("V28_S_adverse_event_coding_reference", "S",
             r"MedDRA\s*低位语", r"不良事件[^。]{0,100}术语标准化", previous),
            ("V28_S_error_prevention_example", "S",
             r"用于精准计量的装置", r"药品[^。]{0,100}减少用药错误", previous),
            ("V28_S_label_safety_reference", "S",
             r"采用简单清晰[^。；;]{0,35}表述方式", r"药品说明书[^。]{0,100}安全用药", previous),
            ("V28_E_combination_factorial_reference", "E",
             r"联合用药析因分析", r"疗效析因[^。]{0,40}联合开发评价", full),
        ]
        for rule, dim, current_pattern, antecedent_pattern, source in specs:
            antecedent = re.search(antecedent_pattern, source, re.I)
            if antecedent:
                for current in re.finditer(current_pattern, view.text, re.I):
                    _review_add(view, rule, dim, *current.span(),
                                dependency=view.dependency(paragraph, "same_paragraph_explicit_reference",
                                                           antecedent.group()),
                                safety_basis="other_safety" if dim == "S" else None)
        # A demonstrative result comparison points to the one named study,
        # whose current paragraph states its exact drug evaluation outcomes.
        if re.search(r"该(?:真实世界)?研究的结果[^。]*(?:相近|重现)", view.text):
            study = re.search(r"(?:某药|药物|药品)[^。]{0,140}有效性和安全性研究", prefix)
            if study:
                current = re.search(r"该(?:真实世界)?研究的结果", view.text)
                for dim in ("S", "E"):
                    _review_add(view, "V28_SE_named_study_result_reference", dim, *current.span(),
                                dependency=view.dependency(paragraph, "same_paragraph_named_study_result",
                                                           study.group()),
                                safety_basis="other_safety" if dim == "S" else None)


def _review_exclusions(view):
    exclusions = [
        ("S", r"药物警戒(?:工作)?(?:经验|经历|资历)(?:相关说明)?", "personnel_experience"),
        ("E", r"(?:促进)?药品回归临床价值", "policy_orientation"),
        ("E", r"(?:风险管理|风险控制|信号评价)(?:工作)?(?:的)?有效性", "risk_process_validity"),
        ("S", r"本(?:指导原则|指南)[^。；;]{0,25}(?:不能|无法|未能)涵盖[^。；;]*安全性资料[^。；;]*",
         "guideline_coverage_statement"),
        ("E", r"(?:疾病|慢性病)[^。；;，,]{0,25}(?:影响|降低)生活质量", "disease_burden"),
        ("E", r"(?:治疗或改善)?严重影响生活质量的(?:慢性|反复|或|发作性|疾病)+", "disease_burden"),
    ]
    for dim, pattern, reason in exclusions:
        _drop_pattern(view, dim, pattern, "V28_SE_" + reason,
                      "按v1.3排除资历、资料管理、政策目的或非药物结局，局部独立内容保留。")
    if _mixed_treatment_parents(view) and not _LOCAL_DRUG.search(view.text):
        view.drop(lambda e: e["dimension"] == "E", "V28_E_mixed_treatment_scope",
                  "已核验上位列表包括药物及替代/支持疗法，当前泛称治疗获益未独立绑定药物。")
    if _data_risk_parents(view) and not re.search(
            r"不良反应|毒性|(?:用药|给药)错误|药物相互作用|药品质量(?:安全|风险)", view.text):
        view.drop(lambda e: e["dimension"] == "S", "V28_S_verified_data_risk_branch",
                  "已核验当前所属数据可靠性风险控制分支，未独立陈述药物损害；不把受试者安全目的词作为药物风险。")
    for sentence in view.sentences():
        value = sentence.group()
        if (re.search(r"档案|编码管理", value) and re.search(r"汇集|归集|归档", value)
                and not re.search(r"评价|分析|监测|识别", value)):
            view.drop_within("S", *sentence.span(), "V28_S_existing_report_archive",
                             "汇集既有报告并管理档案，未新增安全评价内容要求。")
        if (re.search(r"依法依规查处|移交司法|追究刑事责任", value)
                and not _HARM.search(value) and not re.search(r"药品质量(?:安全|风险)", value)):
            for risk in re.finditer(r"风险控制(?:措施)?", value):
                view.drop_within("S", sentence.start()+risk.start(), sentence.start()+risk.end(),
                                 "V28_S_enforcement_process_risk",
                                 "当前控制对象为监管检查/违法处置，不自动等于药物损害。")


def revise(record, result):
    """Mutate only S/E evidence and the suppression/review trails."""
    if result.get("judgement_status") == "undetermined":
        return result
    view = RuleView(record, result)
    view.drug_scope = bool(view.drug_scope or _LOCAL_DRUG.search(view.text) or _verified_scope(view))
    result.setdefault("suppressions", [])
    result.setdefault("review_flags", [])
    prior_exclusions = [s for s in result["suppressions"]
                        if s.get("rule") != "quality_risk_duplicate_basis"
                        and set(s.get("dimensions", [])) & {"S", "E"}]
    for match in re.finditer(r"(?:药品|药物|用药)(?:的|应当|应|必须|需要|须|应保证)?"
                             r"安全[、,，]?有效(?!期)", view.text):
        view.add("V27_SE_safe_effective_drug_requirement", "S", *match.span(),
                 basis=S_BASIS, safety_basis="other_safety")
        view.add("V27_SE_safe_effective_drug_requirement", "E", *match.span(), basis=E_BASIS)
    _add_safety(view)
    _add_effectiveness(view)
    _review_direct_content(view)
    _review_bound_references(view)
    # Apply local exclusions after additions so new synonyms cannot revive
    # already-rejected administrative, personnel or wrong-object evidence.
    _drop_transactions_and_titles(view)
    _drop_known_wrong_objects(view)
    _review_exclusions(view)
    for exclusion in prior_exclusions:
        # Respect inherited semantic masks (e.g. a named policy, institution,
        # disclosure clause). A new synonym cannot undo their local boundary.
        view.drop(lambda e: e["dimension"] in {"S", "E"}
                  and e["dimension"] in exclusion["dimensions"]
                  and exclusion["start"] <= e["start"] < e["end"] <= exclusion["end"]
                  and e["rule"].startswith(("V27_", "V28_")),
                  "V27_SE_inherited_semantic_exclusion",
                  "保留既有局部语义排除：" + exclusion["rule"])
    return result
