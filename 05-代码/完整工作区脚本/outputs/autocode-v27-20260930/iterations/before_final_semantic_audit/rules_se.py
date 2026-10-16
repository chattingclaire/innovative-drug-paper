"""Bounded CAL-5D v1.3 review layer for safety (S) and effectiveness (E).

``revise`` mutates only S/E evidence plus suppression and review-flag trails.
The caller owns label rebuilding.  Matching uses ``RuleView`` so document
titles are blanked without changing offsets into the supplied original text.
"""
from __future__ import annotations

import re

from rule_support import RuleView


VERSION = "v27-se-protocol-review-2"

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
    r"治疗(?:方案|药物|措施|手段)?|患者|受试者"
)
_HARM = re.compile(
    r"不良反应|不良事件|毒性|禁忌|副作用|用药错误|药物警戒|"
    r"药物相互作用|药物相关风险|安全信号|非预期严重损害|"
    r"死亡与治疗的相关性|安全性风险|潜在治疗风险"
)
_EFFECT = re.compile(
    r"有效性|疗效|药效(?:学)?|临床获益|治疗获益|治疗效果|临床效果|"
    r"临床优势|治疗优势|治疗价值|药物效果|抗肿瘤活性|干预效果|"
    r"有效治疗|疾病控制率|客观缓解(?:率)?|总缓解率|完全缓解|部分缓解|"
    r"无进展生存(?:期)?|总生存(?:期)?|无病生存(?:期)?|事件无发生生存(?:期)?|"
    r"缓解持续时间|生存率|生存期|健康效用|QALY"
)
_BENEFIT_RISK = re.compile(r"获益\s*[-—－、/与和]?\s*风险|风险\s*[-—－、/与和]?\s*获益")
_ABBREVIATION = re.compile(r"(?<![A-Za-z])(?:SAE|SUSAR|ADR|AE)(?![A-Za-z])", re.I)
_ABBREVIATION_USE = re.compile(
    r"发生(?:率|情况)?|分级|严重|致死|死亡|停药|减量|相关性|列表|报告|"
    r"呈现|汇总|统计|分析|评价|监测|信号"
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
    return bool(_LOCAL_DRUG.search(value) or view.drug_scope)


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
        r"(?:数据|网络|信息系统|服务器|计算机|软件|基金|生产|施工|消防|食品)"
        r"[^。；;，,]{0,18}(?:安全性|安全风险|风险控制|风险管理|风险最小化)",
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
                    or re.search(r"用药错误|药物警戒|药物相互作用|药物相关风险", match.group())):
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
        if not (_LOCAL_DRUG.search(value) or dependency or object_dependencies):
            a, b = view.raw_span(match.start(), match.end())
            _flag(view.result, "V27_S_adverse_event_abbreviation",
                  "缩写有安全性用法但缺药物对象或同段释义", a, b, view.original[a:b])
            continue
        if dependency is None and object_dependencies and not _LOCAL_DRUG.search(value):
            dependency = {
                "kind": "verified_drug_object_scope",
                "scopes": object_dependencies,
            }
        view.add("V27_S_adverse_event_abbreviation", "S", match.start(), match.end(),
                 basis=S_BASIS, dependency=dependency, safety_basis="other_safety")

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
        if _scoped(view, match.group()) or view.drug_scope:
            view.add("V27_E_patient_outcome", "E", match.start(), match.end(), basis=E_BASIS)

    for match in re.finditer(
            r"(?:药品|药物|用药|治疗方案)[^。；;]{0,24}(?:指南|诊疗规范)(?:推荐|建议)"
            r"|(?:指南|诊疗规范)(?:推荐|建议)[^。；;]{0,24}(?:药品|药物|用药|治疗方案)",
            view.text):
        view.add("V27_E_guideline_drug_recommendation", "E", match.start(), match.end(), basis=E_BASIS)

    for match in re.finditer(
            r"(?:收集|提交|提供|补充|报告|呈现|汇总|分析|评价|评估|比较|判断)"
            r"[^。；;，,]{0,55}?(?P<content>有效性|疗效|药效|临床获益|治疗效果|临床优势)"
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


def revise(record, result):
    """Mutate only S/E evidence and the suppression/review trails."""
    if result.get("judgement_status") == "undetermined":
        return result
    view = RuleView(record, result)
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
    # Apply local exclusions after additions so new synonyms cannot revive
    # already-rejected administrative, personnel or wrong-object evidence.
    _drop_transactions_and_titles(view)
    _drop_known_wrong_objects(view)
    for exclusion in prior_exclusions:
        # Respect inherited semantic masks (e.g. a named policy, institution,
        # disclosure clause). A new synonym cannot undo their local boundary.
        view.drop(lambda e: e["dimension"] in {"S", "E"}
                  and e["dimension"] in exclusion["dimensions"]
                  and exclusion["start"] <= e["start"] < e["end"] <= exclusion["end"]
                  and e["rule"].startswith("V27_"),
                  "V27_SE_inherited_semantic_exclusion",
                  "保留既有局部语义排除：" + exclusion["rule"])
    return result
