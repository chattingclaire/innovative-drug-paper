"""CAL-5D v1.3 economic-dimension revision.

``revise`` mutates only Ec evidence/suppressions/review_flags in a completed
v26.2-style result.  It deliberately leaves labels and every other dimension
for the root pipeline's shared rebuild step.
"""

import hashlib
import re

from rule_support import RuleView


RELEASE = "v28-ec-semantic-review-20261004"
EC_BASIS = (
    "CAL-5D-20260926-v1.3 Ec: drug price, medicine/treatment cost, payment "
    "standard, reimbursement or fee responsibility, related sales/amount, "
    "cost-effectiveness, budget impact, or drug-payment impact on funds."
)

DRUG_LOCAL = re.compile(
    r"药品|药物|用药|药费|药价|新药|该药|制剂|中药饮片|中成药|西药|处方|"
    r"同通用名|治疗药|谈判药品|目录药品"
)

PRESERVED_CONTEXT_RULES = {
    "Ec05",                         # verified ratio A/B definition
    "term_material_market_change", # same-paragraph explicit definition
    "V25_multidimension_use_requirement",
}

DISCLOSURE_OR_FILE = re.compile(
    r"公示|公开|保密|不含|除[^。；;，,]{0,12}以外|文件名|命名|幻灯片|PPT|"
    r"上传|归档|格式|版本"
)
SUBSTANTIVE_ECON_ACTION = re.compile(
    r"评价|评估|比较|测算|分析|核算|确定|调整|下调|降低|提高|承担|支付|报销|"
    r"补偿|预算|影响|报价|定价|成本效果|成本效益|成本效用"
)
PROCEDURE_WORDS = re.compile(r"组织|开展|参与|进入|安排|确认|签署|阶段|流程|环节|会议|进行|负责")
PROCEDURE_NAMES = re.compile(r"谈判|竞价|价格协商")
PRICE_OUTCOME = re.compile(
    r"报价|底价|支付标准|结算价|挂网价|零售价|采购价|价格(?:为|高于|低于|"
    r"不超过|不低于|下调|降低|提高|调整|的?评估意见|水平|差异|合理|偏高|较高|较低)|"
    r"降价|降幅|底价测算|评估确定的协商价格"
)
NON_DRUG_RESOURCE = re.compile(
    r"科研经费|项目经费|研究经费|机构运行经费|工作经费|行政经费|会议经费|"
    r"办公经费|设备采购|医疗设备|医用耗材|办公设备|办公用品|软件|信息系统|"
    r"门诊大楼|基础设施|交通费|住宿费|差旅费|研究成本|研发成本|办公成本"
)
ADMIN_FEE = re.compile(
    r"(?:注册|申报|申请|审评|审批|检验|认证|会议|培训)[^。；;，,]{0,16}"
    r"(?:收费|费用|缴费|缴纳|交纳)|(?:收费|缴费)标准"
)
GENERAL_SERVICE = re.compile(
    r"医疗服务(?:项目)?价格|医疗服务费用|门诊费用|住院费用|诊疗费用|护理费用|"
    r"医院运营成本|医疗机构运行成本"
)
EXPERT_ONLY = re.compile(r"药物经济学(?:专家(?:组)?|专业(?:背景|人员)?|背景|组别)")
EXPLICIT_DRUG_ECONOMICS = re.compile(
    r"药品费用|药物费用|药费|药价|用药(?:费用|成本)|药物治疗成本|"
    r"药品(?:挂网|采购|销售|零售|谈判|结算)?价格|"
    r"药品[、和及](?:高值)?医用耗材价格|"
    r"(?:申报)?药品基本信息[、及与和]+费用信息|"
    r"(?:药品|药物)(?:的)?(?:成本效果|报销|支付标准)"
)
DRUG_ECONOMIC_EVALUATION = re.compile(
    r"(?:该)?(?:药品|药物|用药)[^。；;，,]{0,24}"
    r"(?:经济性(?:评价|研究|证据|方面的?优势|方面的?不足)|"
    r"成本[-—–]?(?:效果|效益|效用)(?:分析|评价)?)"
)
DRUG_EXPENSE_INFORMATION = re.compile(
    r"(?:申报)?(?:药品|药物|用药)(?:基本)?信息[、及与和]+费用信息|"
    r"(?:药品|药物|用药)(?:的)?(?:费用|价格|药费)信息"
)


def _absolute(clause, match):
    return clause.start() + match.start(), clause.start() + match.end()


def _append_suppression(view, rule, start, end, reason):
    """Record an excluded normalized span against the exact original."""
    a, b = view.raw_span(start, end)
    item = {
        "rule": rule,
        "dimensions": ["Ec"],
        "start": a,
        "end": b,
        "text": view.original[a:b],
        "reason": reason,
        "rule_release": RELEASE,
    }
    if not any(
        old.get("rule") == rule and old.get("start") == a and old.get("end") == b
        for old in view.result.setdefault("suppressions", [])
    ):
        view.result["suppressions"].append(item)


def _flag(view, rule, start, end, reason):
    a, b = view.raw_span(start, end)
    item = {
        "rule": rule,
        "dimension": "Ec",
        "start": a,
        "end": b,
        "text": view.original[a:b],
        "reason": reason,
        "action": "review_economic_object_or_meaning_before_release",
        "rule_release": RELEASE,
    }
    if not any(
        old.get("rule") == rule and old.get("start") == a and old.get("end") == b
        for old in view.result.setdefault("review_flags", [])
    ):
        view.result["review_flags"].append(item)


def _is_file_or_disclosure_only(value):
    if re.search(r"归档|命名|文件名|上传格式|格式编号", value) and not re.search(
        r"(?:评价|评估|比较|测算|核算|调整|降低|提高|承担|报销)[^。；;，,]{0,16}"
        r"(?:药品|药物|药费|价格|成本|费用|支付标准)|"
        r"(?:提交|补充|提供)[^。；;，,]{0,16}(?:成本效果分析|经济性评价)", value
    ):
        return True
    if re.search(r"公示|公开|保密", value) and not re.search(
        r"提交|补充|提供|评价|评估|比较|测算|分析|核算|确定|调整|降低|提高|承担|报销", value
    ):
        return True
    return bool(DISCLOSURE_OR_FILE.search(value) and not SUBSTANTIVE_ECON_ACTION.search(value))


def _is_negotiation_procedure_only(value):
    independent = re.search(r"药品费用|药费|基金(?:实际)?支出|基金支付情况|"
                            r"成本[-—－]?(?:效果|效益|效用)|支付标准|"
                            r"拟价格协商的药品开展测算", value)
    return bool(PROCEDURE_NAMES.search(value) and PROCEDURE_WORDS.search(value)
                and not PRICE_OUTCOME.search(value) and not independent)


def _excluded_reason(value):
    # An independent medicine-cost/price proposition survives in a mixed
    # clause; broad non-drug cost words never generate evidence themselves.
    independent = (EXPLICIT_DRUG_ECONOMICS.search(value)
                   or DRUG_ECONOMIC_EVALUATION.search(value)
                   or DRUG_EXPENSE_INFORMATION.search(value))
    if (re.search(r"价格|费用|汇率", value)
            and re.search(r"(?:以截至|截至|均以|以)\s*20\d{2}\s*年[^。；;，,]{0,25}(?:为准|最新数据)", value)
            and not re.search(r"核算|测算|评价|比较|调整支付标准|降低药价", value)):
        return "economic_data_cutoff_date_only"
    if NON_DRUG_RESOURCE.search(value) and not independent:
        return "non_drug_research_institution_or_asset_resource"
    if ADMIN_FEE.search(value) and not independent:
        return "administrative_registration_or_service_fee"
    if GENERAL_SERVICE.search(value) and not independent:
        return "general_medical_service_cost_without_drug_treatment_relation"
    if EXPERT_ONLY.search(value) and not re.search(r"成本效果|预算影响|测算|评价|评估|分析|"
                                                r"(?:确定|计算|调整)支付标准", value):
        return "expert_specialty_or_background_only"
    if _is_negotiation_procedure_only(value):
        return "price_negotiation_procedure_without_price_or_payment_content"
    if _is_file_or_disclosure_only(value):
        return "file_disclosure_confidentiality_or_format_only"
    return None


def _add_matches(view, clause, rule, pattern, require_local_drug=False, require_scope=False):
    value = clause.group()
    if _excluded_reason(value):
        return 0
    if require_local_drug and not DRUG_LOCAL.search(value):
        return 0
    # Current-unit directory/payment relations may resolve a medicine object;
    # filenames, prior headings and unbound preceding paragraphs never do.
    directory_payment = bool(
        re.search(r"适应症|功能主治", view.text) and re.search(r"医保支付标准", view.text)
        or re.search(r"谈判专家[^。；;]{0,35}企业[^。；;]{0,35}医保支付标准", view.text)
        or re.search(r"重新谈判[^。；;]{0,20}支付标准[^。；;]{0,20}常规目录", view.text)
    )
    if require_scope and not (DRUG_LOCAL.search(value) or view.drug_scope or directory_payment):
        return 0
    if require_scope and not DRUG_LOCAL.search(value):
        sentence_match = next(s for s in view.sentences()
                              if s.start() <= clause.start() < s.end())
        sentence = sentence_match.group()
        if (not DRUG_LOCAL.search(sentence)
                and re.search(r"医疗服务|病床|床日|机构总额|"
                              r"(?:DRG|DIP|疾病诊断相关分组|病种分值)[^。；;]{0,20}(?:付费)?改革", sentence)):
            return 0
        if (GENERAL_SERVICE.search(sentence) or NON_DRUG_RESOURCE.search(sentence)) and not DRUG_LOCAL.search(sentence):
            return 0
        prefix = view.text[sentence_match.start():clause.start()]
        objects = [(m.start(), "drug") for m in DRUG_LOCAL.finditer(prefix)]
        objects += [(m.start(), "other") for p in (NON_DRUG_RESOURCE, GENERAL_SERVICE)
                    for m in p.finditer(prefix)]
        if objects and max(objects)[1] == "other":
            return 0
    count = 0
    for match in re.finditer(pattern, value):
        if rule == "V27_Ec_price_outcome" and match.group() == "降价" and re.match(
            r"专项(?:工作)?(?:药品|品种)", value[match.end():]
        ):
            continue
        if rule == "V27_Ec_price_outcome" and not DRUG_LOCAL.search(value):
            sentence = next((s.group() for s in view.sentences()
                             if s.start() <= clause.start() < s.end()), value)
            if NON_DRUG_RESOURCE.search(sentence) or GENERAL_SERVICE.search(sentence):
                continue
        if rule == "V27_Ec_payment_standard" and re.match(
            r"有效期(?:到期|届满|截止)", value[match.end():]
        ):
            continue
        # A generic matched outcome in a mixed clause still belongs to its
        # immediate named non-drug object, even when independent drug costs
        # elsewhere let the clause pass the exclusion gate.
        if not EXPLICIT_DRUG_ECONOMICS.search(match.group()):
            if NON_DRUG_RESOURCE.search(match.group()) or GENERAL_SERVICE.search(match.group()):
                continue
            prefix = value[:match.start()]
            nearest = re.split(r"(?:以及|同时|并且|且|和|及|与)", prefix)[-1]
            if NON_DRUG_RESOURCE.search(nearest) or GENERAL_SERVICE.search(nearest) or ADMIN_FEE.search(nearest):
                continue
        start, end = _absolute(clause, match)
        view.add(rule, "Ec", start, end, basis=EC_BASIS)
        count += 1
    return count


def _add_ratio_dependencies(view, record):
    """Resolve only an explicit A/B reference using verified same-source text."""
    for match in re.finditer(r"比值\s*[AB]", view.text):
        clause = next(c.group() for c in view.clauses()
                      if c.start() <= match.start() < c.end())
        if _excluded_reason(clause):
            continue
        for item in record.get("verified_supplemental_context", []):
            if item.get("kind") != "same_source_ratio_definition":
                continue
            if item.get("original_unit_sha256") != hashlib.sha256(view.original.encode()).hexdigest():
                continue
            for context in item.get("contexts", []):
                expected_source = record.get("unit_source_sha256") or record.get("source_sha256")
                if expected_source and context.get("source_sha256") != expected_source:
                    continue
                definition = context.get("text", "")
                letter = re.search(r"[AB]", match.group()).group()
                if not re.search(rf"比值\s*{letter}", definition):
                    continue
                if not re.search(r"药品费用|基金(?:实际)?支出", definition) or "预算" not in definition:
                    continue
                dependency = {
                    "kind": "same_source_ratio_definition",
                    "paragraph_id": context.get("paragraph_id"),
                    "source_sha256": context.get("source_sha256"),
                    "pages": context.get("pages", []),
                    "definition_text": definition,
                }
                view.add("V27_Ec_ratio_reference", "Ec", match.start(), match.end(),
                         basis=EC_BASIS, dependency=dependency)
                break


def _add_same_paragraph_anaphora(view):
    """Allow an explicit data reference, never silent paragraph propagation."""
    for current in re.finditer(
        r"(?:上述|相关|该等)(?:数据|数值|金额)[^。；;]{0,24}(?:续约|测算|支付标准|目录调整)",
        view.text,
    ):
        sentence = next(s.group() for s in view.sentences()
                        if s.start() <= current.start() < s.end())
        if _is_file_or_disclosure_only(sentence):
            continue
        for paragraph, prefix in view.paragraph_prefixes():
            antecedents = re.findall(
                r"(?:纳入支付范围的)?药品费用|药费|销售金额|使用金额|基金支出|预算影响",
                prefix,
            )
            if not antecedents:
                continue
            antecedent = antecedents[-1]
            view.add(
                "V27_Ec_explicit_data_anaphora", "Ec", current.start(), current.end(),
                basis=EC_BASIS,
                dependency=view.dependency(paragraph, "same_paragraph_explicit_economic_data", antecedent),
            )
            break


def _add_comparative_drug_price(view):
    """A comma may separate the compared medicines from their price/cost."""
    for sentence in view.sentences():
        value = sentence.group()
        if _is_file_or_disclosure_only(value):
            continue
        for match in re.finditer(r"(?:价格|费用)(?:\s*[/或、]\s*(?:价格|费用))?"
                                 r"[^。；;，,]{0,10}(?:偏高|较高|偏低|较低|高于|低于)", value):
            prefix = value[:match.start()]
            if not re.search(r"(?:与|同)[^。；;]{0,32}(?:药品|药物)[^。；;]{0,12}相比\s*[,，]?\s*$", prefix):
                continue
            if _excluded_reason(value[match.start():match.end()]):
                continue
            start, end = sentence.start() + match.start(), sentence.start() + match.end()
            view.add("V27_Ec_comparative_drug_price_or_cost", "Ec", start, end, basis=EC_BASIS)


def _add_drug_economic_dimension(view):
    """Catch an explicit drug evaluation dimension even across list commas."""
    for sentence in view.sentences():
        value = sentence.group()
        if _is_file_or_disclosure_only(value):
            continue
        drug_anchors = list(re.finditer(r"(?:药品|药物|用药)临床(?:使用|应用|综合评价)", value))
        if not drug_anchors:
            continue
        if not re.search(r"评价|证据|研判|分析", value):
            continue
        for match in re.finditer(r"经济性[^。；;]{0,32}(?:维度|相关证据)", value):
            if not re.search(r"维度|证据", match.group()):
                continue
            preceding = [anchor for anchor in drug_anchors if anchor.end() <= match.start()]
            if not preceding:
                continue
            relation = value[preceding[-1].end():match.start()]
            if NON_DRUG_RESOURCE.search(relation) or GENERAL_SERVICE.search(relation):
                continue
            start, end = sentence.start() + match.start(), sentence.start() + match.end()
            view.add("V27_Ec_drug_economic_dimension", "Ec", start, end, basis=EC_BASIS)


def _add_contextual_economic_study(view):
    """A study in a drug-economic paragraph can refer to that same object."""
    for match in re.finditer(r"经济性研究", view.text):
        sentence = next(s.group() for s in view.sentences()
                        if s.start() <= match.start() < s.end())
        if _is_file_or_disclosure_only(sentence):
            continue
        if NON_DRUG_RESOURCE.search(sentence) or GENERAL_SERVICE.search(sentence):
            continue
        for paragraph, prefix in view.paragraph_prefixes():
            antecedents = re.findall(
                r"(?:药品|药物)[^。；;]{0,40}(?:成本|经济价值|经济性评价|经济性研究)",
                prefix,
            )
            if not antecedents:
                continue
            view.add(
                "V27_Ec_contextual_economic_study", "Ec", match.start(), match.end(),
                basis=EC_BASIS,
                dependency=view.dependency(paragraph, "same_paragraph_drug_economic_evaluation",
                                           antecedents[-1]),
            )
            break


def _add_linked_economic_content(view):
    """Retain explicit drug anaphors across commas, with local carrier gates."""
    for sentence in view.sentences():
        value = sentence.group()
        if not DRUG_LOCAL.search(value):
            continue
        for pattern in (
            r"(?:对)?拟价格协商的药品开展测算(?:并提出评估意见)?",
            r"(?:掌握|监测|统计)其[^。；;，,]{0,18}(?:使用金额|销售金额|销售量|使用量)",
            r"用药合理性和费用审核",
        ):
            for match in re.finditer(pattern, value):
                clause = next(c.group() for c in view.clauses()
                              if c.start() <= sentence.start() + match.start() < c.end())
                # The price-measurement phrase is substantive despite its
                # program name; pure archival uses remain excluded.
                if _is_file_or_disclosure_only(clause):
                    continue
                if NON_DRUG_RESOURCE.search(clause) or GENERAL_SERVICE.search(clause):
                    continue
                view.add("V27_Ec_linked_drug_economic_content", "Ec",
                         sentence.start()+match.start(), sentence.start()+match.end(), basis=EC_BASIS)
        if re.search(r"医保用药(?:行为|费用)", value):
            for match in re.finditer(r"(?:结算和支付|结算|支付)医保费用", value):
                if not _is_file_or_disclosure_only(value):
                    view.add("V27_Ec_linked_drug_economic_content", "Ec",
                             sentence.start()+match.start(), sentence.start()+match.end(), basis=EC_BASIS)


def _add_payment_relations_v28(view):
    """Concrete payer/condition relations, not payment-range names alone."""
    patterns = (
        ("V28_Ec_separate_drug_payment", r"(?:医疗服务(?:与|和))?药品分开支付"),
        ("V28_Ec_insurance_payment_responsibility",
         r"商业(?:健康)?保险(?:产品)?[^。；;，,]{0,12}(?:扩大|扩展|拓宽)"
         r"[^。；;，,]{0,12}(?:创新药|药品|药物)支付范围|"
         r"(?:同通用名)?药品自动属于(?:基本医疗保险|医保)基金支付范围"),
        ("V28_Ec_quality_risk_compensation",
         r"药品质量风险[^。；;，,]{0,16}经济补偿(?:机制|责任)?"),
        ("V28_Ec_drug_case_payment_exception",
         r"创新药应用(?:病例)?可不纳入按病种付费范围|"
         r"(?:创新药|药品)的?病例[,，](?:不适合|不能)按病种标准支付"),
    )
    for sentence in view.sentences():
        value = sentence.group()
        for rule, pattern in patterns:
            for match in re.finditer(pattern, value):
                part = next(c.group() for c in view.clauses()
                            if c.start() <= sentence.start()+match.start() < c.end())
                if _is_file_or_disclosure_only(part):
                    continue
                view.add(rule, "Ec", sentence.start()+match.start(),
                         sentence.start()+match.end(), basis=EC_BASIS)
        if DRUG_LOCAL.search(value) and not _is_file_or_disclosure_only(value):
            for match in re.finditer(
                r"支付范围与说明书的(?:适应症|功能主治)[^。；;，,]{0,12}一致", value
            ):
                view.add("V28_Ec_indication_payment_condition", "Ec",
                         sentence.start()+match.start(), sentence.start()+match.end(), basis=EC_BASIS)
            if re.search(r"公共卫生事件|紧急情况", value):
                for match in re.finditer(r"临时调整医保药品支付范围", value):
                    view.add("V28_Ec_emergency_payment_condition", "Ec",
                             sentence.start()+match.start(), sentence.start()+match.end(), basis=EC_BASIS)
            if re.search(r"药品[、和及与医用耗材]{0,12}集中带量采购", value):
                for match in re.finditer(r"量价挂钩", value):
                    view.add("V28_Ec_procurement_volume_price", "Ec",
                             sentence.start()+match.start(), sentence.start()+match.end(), basis=EC_BASIS)

    # Only a verified parent stating medicine-cost reimbursement can turn a
    # child purpose statement into a payment condition. Other parent labels
    # and other child statements remain outside this relation.
    for parent in view.record.get("verified_parent_context", []):
        text = parent.get("text", "")
        if not (re.search(r"药品[^。；;]{0,18}费用", text)
                and re.search(r"符合以下条件", text)
                and re.search(r"(?:基本医疗保险|医保)基金支付", text)):
            continue
        for match in re.finditer(r"以疾病(?:诊断或治疗|治疗或诊断|诊断|治疗)为目的", view.text):
            if _is_file_or_disclosure_only(view.text):
                continue
            view.add("V28_Ec_parent_bound_payment_condition", "Ec", *match.span(),
                     basis=EC_BASIS,
                     dependency=view.dependency(parent, "verified_medicine_cost_payment_condition", text))


def _add_verified_renewal_fund_content(view):
    """A supplied verified renewal branch resolves scope, never the trigger."""
    branch = view.record.get("verified_rule_branch_context")
    if not isinstance(branch, dict) or not re.search(r"简易续约", branch.get("text", "")):
        return
    if not branch.get("paragraph_id") or not branch.get("pages"):
        return
    source = view.record.get("unit_source_sha256") or view.record.get("source_sha256")
    if not source or (branch.get("source_sha256") and branch["source_sha256"] != source):
        return
    if NON_DRUG_RESOURCE.search(view.text) or GENERAL_SERVICE.search(view.text):
        return
    for clause in view.clauses():
        value = clause.group()
        if _is_file_or_disclosure_only(value):
            continue
        for match in re.finditer(r"(?:医保)?基金(?:年均)?(?:实际)?支出(?:预算增幅|预算|金额)?", value):
            view.add("V28_Ec_verified_renewal_fund_content", "Ec",
                     clause.start()+match.start(), clause.start()+match.end(), basis=EC_BASIS,
                     dependency=view.dependency(branch, "verified_renewal_object_scope", branch["text"]))
    for match in re.finditer(r"以医保方数据为准", view.text):
        if _is_file_or_disclosure_only(view.text):
            continue
        for paragraph, prefix in view.paragraph_prefixes():
            last = list(re.finditer(r"[^。；;]+", prefix))
            if not last:
                continue
            antecedent = last[-1].group()
            if not re.search(r"企业(?:方)?和医保方对基金实际支出", antecedent):
                continue
            if NON_DRUG_RESOURCE.search(antecedent) or GENERAL_SERVICE.search(antecedent):
                continue
            dependency = view.dependency(paragraph, "same_paragraph_actual_fund_amount_reference", antecedent)
            dependency["verified_renewal_branch"] = view.dependency(branch, "verified_renewal_object_scope", branch["text"])
            view.add("V28_Ec_verified_fund_data_reference", "Ec", *match.span(),
                     basis=EC_BASIS, dependency=dependency)
            break


def revise(record, result):
    """Revise only Ec traces in-place; pending results are returned untouched."""
    if result.get("judgement_status") == "undetermined":
        return result

    view = RuleView(record, result)

    # Add/drop helpers deduplicate new traces. Retain earlier Ec audit entries
    # on repeated calls, including the legacy evidence removal record.
    result.setdefault("suppressions", [])
    result.setdefault("review_flags", [])

    expected_source = record.get("unit_source_sha256") or record.get("source_sha256")
    if expected_source:
        view.drop(
            lambda evidence: evidence.get("dimension") == "Ec"
            and evidence.get("rule") == "Ec05"
            and evidence.get("context_dependency", {}).get("source_sha256") != expected_source,
            "V27_Ec_ratio_source_mismatch", "ratio_definition_does_not_match_current_source",
        )

    # First give known false-positive propositions a specific audit reason.
    for clause in view.clauses():
        value = clause.group()
        reason = _excluded_reason(value)
        if not reason:
            continue
        view.drop_within(
            "Ec", clause.start(), clause.end(), "V27_Ec_excluded_proposition",
            reason,
        )
        _append_suppression(
            view, "V27_Ec_excluded_proposition", clause.start(), clause.end(), reason,
        )

    # Broad legacy lexical evidence is rebuilt. Verified cross-text relations
    # and the explicit multidimension-use rule remain available.
    view.drop(
        lambda evidence: (
            evidence.get("dimension") == "Ec"
            and evidence.get("rule") not in PRESERVED_CONTEXT_RULES
            and not str(evidence.get("rule", "")).startswith(("V27_Ec_", "V28_Ec_"))
        ),
        "V27_Ec_legacy_rebuild",
        "legacy_broad_economic_lexeme_reassessed_under_complete_Ec_review",
    )

    for clause in view.clauses():
        value = clause.group()
        excluded = _excluded_reason(value)
        if excluded:
            continue

        # Explicit evaluation/information requirements and pharmacoeconomics.
        _add_matches(
            view, clause, "V27_Ec_economic_evaluation_information",
            r"药物经济学(?:评价|评估|分析|证据|资料|信息|研究|测算|报告)|"
            r"药物经济学(?:等)?(?:报告|资料|原则|方法)|药物经济性|经济学效益|"
            r"经济性(?:评价|评估|比较|分析|证据|资料|信息|研究)|"
            r"(?:评价|评估|比较|分析)[^。；;，,]{0,18}经济性|"
            r"经济性[^。；;，,]{0,45}(?:综合评价|整合分析|综合研判|比较优势|相关证据|条件)|"
            r"(?:考虑|提升)[^。；;，,]{0,20}经济性|"
            r"(?:成本[-—–]?(?:效果|效益|效用)|最小成本)"
            r"(?:分析(?:法|材料)?|评价|评估|结果|证据|研究)?|"
            r"增量成本效果比|ICER",
            require_scope=True,
        )
        _add_matches(
            view, clause, "V27_Ec_drug_economic_evaluation",
            DRUG_ECONOMIC_EVALUATION,
        )
        _add_matches(
            view, clause, "V27_Ec_drug_expense_information_requirement",
            DRUG_EXPENSE_INFORMATION,
        )

        # Drug prices and price outcomes; generic process names are excluded.
        _add_matches(
            view, clause, "V27_Ec_drug_price",
            r"(?:药品|药物|药剂|制剂|中药饮片|中成药|西药|同通用名药品|品种)"
            r"[^。；;，,]{0,12}(?:挂网|零售|销售|采购|谈判|结算|执行)?价格|"
            r"(?:药价|药品挂网价|药品零售价|药品采购价|药品结算价|医保底价)|"
            r"(?:药品|药物)(?:的)?(?:报价|定价)|短缺药品[^。；;，,]{0,8}稳价",
        )
        _add_matches(
            view, clause, "V27_Ec_price_outcome",
            r"(?:报价|底价|挂网价|零售价|采购价|结算价|价格)"
            r"[^。；;，,]{0,12}(?:高于|低于|不超过|不低于|等于|下调|降低|提高|调整|为)"
            r"[^。；;，,]{0,12}(?:元|%|标准|水平)?|"
            r"(?:降价|降幅|价格降幅|价格下调比例)|"
            r"价格(?:[/或]|\()?(?:费用\)?)?[^。；;，,]{0,24}"
            r"(?:合理|偏高|较高|较低|相当|较大影响)|"
            r"价格(?:高|低)(?=[、，,。;；]|的|而)|"
            r"(?:协商价格(?:的)?评估意见|评估确定的协商价格|底价测算|自主合理定价)",
            require_scope=True,
        )

        # Medicine charges and drug-treatment cost.
        _add_matches(
            view, clause, "V28_Ec_quotation_requirement_or_minimum",
            r"(?:提交|给出|要求)报价|报价并提交承诺书|最低报价",
            require_scope=True,
        )
        _add_matches(
            view, clause, "V27_Ec_medicine_cost",
            r"(?:纳入支付范围的?|实际发生的?|年均实际)?药品费用|药费|用药费用|"
            r"药物费用|药品治疗费用|药物治疗成本|用药成本|药品成本|治疗药品费用|"
            r"药品(?:的)?成本|药品[^。；;，,]{0,10}发生的费用",
        )
        _add_matches(
            view, clause, "V27_Ec_treatment_cost",
            r"治疗费用|治疗成本|疗程费用",
            require_scope=True,
        )

        # Payment standard, reimbursement, and allocation of fee liability.
        _add_matches(
            view, clause, "V27_Ec_payment_standard",
            r"(?:医保|药品|药物)?支付标准(?:的)?(?:下调比例|调整幅度|调整|下调|确定|水平)?",
            require_scope=True,
        )
        _add_matches(
            view, clause, "V27_Ec_reimbursement",
            r"(?:药品|药物|用药)[^。；;，,]{0,12}(?:报销|报销比例|报销范围|报销金额)|"
            r"(?:报销|报销比例|报销范围|报销金额)[^。；;，,]{0,12}(?:药品|药物|药费|用药)|"
            r"报销(?:比例|金额)(?:为|达到|提高至|降低至)?[0-9一二三四五六七八九十百]+(?:元|%)",
            require_scope=True,
        )
        _add_matches(
            view, clause, "V27_Ec_fee_responsibility",
            r"(?:患者|参保人员|参保人)[^。；;，,]{0,12}(?:自付|自费|承担)"
            r"[^。；;，,]{0,12}(?:药品费用|药费|用药费用|费用)|"
            r"(?:药品费用|药费|用药费用)[^。；;，,]{0,12}"
            r"(?:由[^。；;，,]{0,10}承担|患者自付|个人自付|基金支付)|"
            r"基金(?:和|与)(?:患者|参保人员|参保人)[^。；;，,]{0,8}共同支付"
            r"[^。；;，,]{0,8}(?:药品)?费用|"
            r"免费[^。；;，,]{0,20}(?:提供|供应)[^。；;，,]{0,12}(?:药品|药物|用药)|"
            r"(?:提供|供应)[^。；;，,]{0,12}(?:免费药品|免费药物)",
            require_scope=True,
        )
        _add_matches(
            view, clause, "V27_Ec_payment_conditions",
            r"医保支付意愿|(?:药品|药物|创新药)[^。；;，,]{0,35}"
            r"(?:(?:DRG|DIP)[^。；;，,]{0,12})?除外支付|"
            r"(?:药品|药物)[^。；;，,]{0,24}(?:符合|满足|限定|限于|仅限)"
            r"[^。；;，,]{0,20}(?:支付条件|报销条件|方可支付|方可报销)|"
            r"符合药品法定适应症及医保限定支付范围",
            require_scope=True,
        )

        # Sales/use volume must remain explicitly connected to medicines.
        _add_matches(
            view, clause, "V27_Ec_drug_sales_amount",
            r"(?:药品|药物|品种)[^。；;，,]{0,16}"
            r"(?:销量|销售量|销售金额|销售额|预计销售情况|使用量|使用金额|交易量|业务收入)|"
            r"(?:销量|销售量|销售金额|销售额|使用量|使用金额|交易量|业务收入)"
            r"[^。；;，,]{0,12}(?:药品|药物|品种)|"
            r"(?:医保信息平台|药品交易平台)[^。；;，,]{0,8}交易量",
            require_scope=True,
        )

        # Budget and fund effects require a drug/payment relation or an
        # intrinsically drug-economic compound.
        _add_matches(
            view, clause, "V27_Ec_budget_impact",
            r"(?:药品|药费|用药)[^。；;，,]{0,16}预算(?:影响|增加值|增幅)?|"
            r"预算影响(?:分析|评价|评估|测算)",
            require_scope=True,
        )
        _add_matches(
            view, clause, "V27_Ec_fund_impact",
            r"(?:医保)?基金(?:年均)?(?:实际)?支出(?:金额|预算|增加值|增幅)?|"
            r"基金支付能力|基金承受能力|基金可持续(?:性)?|药品支付对基金的影响|基金测算|"
            r"(?:医保)?基金支付情况|占用基金量|(?:医保|基本医疗保险)基金影响",
            require_scope=True,
        )

        # Insurance, mutual aid, or charity must actually bear drug costs or
        # place medicines within a payment/coverage responsibility.
        _add_matches(
            view, clause, "V27_Ec_insurance_or_assistance_payment",
            r"(?:商业健康保险|商业保险|医疗互助|慈善(?:援助|捐赠|项目))"
            r"[^。；;，,]{0,35}(?:药品费用|药费|用药费用)|"
            r"(?:商业健康保险|商业保险|医疗互助)[^。；;，,]{0,28}"
            r"(?:药品|药物|创新药)[^。；;，,]{0,10}纳入保障范围|"
            r"慈善捐赠[^。；;，,]{0,25}支持困难群众[^。；;，,]{0,12}(?:用药|使用[^。；;，,]{0,6}药)",
        )

        # Rational-use statements explicitly containing economic use are an
        # evaluation requirement, not the administrative word "efficiency".
        _add_matches(
            view, clause, "V27_Ec_economic_rational_use",
            r"安全[、,，]有效[、,，]经济(?:[、,，]适宜)?(?:的)?合理用药|"
            r"安全[、,，]有效[、,，]经济(?:[、,，]适宜)?(?:的)?用药",
        )

    _add_comparative_drug_price(view)
    _add_drug_economic_dimension(view)
    _add_contextual_economic_study(view)
    _add_linked_economic_content(view)
    _add_payment_relations_v28(view)
    _add_verified_renewal_fund_content(view)
    _add_ratio_dependencies(view, record)
    _add_same_paragraph_anaphora(view)

    # Ambiguous "burden" language is retained for review rather than forced
    # into Ec without a monetary/payment proposition.
    for match in re.finditer(r"(?:疾病|治疗|照护|护理)负担", view.text):
        sentence = next(
            (s.group() for s in view.sentences() if s.start() <= match.start() < s.end()),
            match.group(),
        )
        if not re.search(r"经济|费用|成本|支付|药费|自付|报销", sentence):
            _flag(
                view, "V27_Ec_ambiguous_burden", match.start(), match.end(),
                "burden_word_without_explicit_monetary_or_payment_meaning",
            )

    for evidence in result["evidence"]:
        if evidence.get("dimension") == "Ec" and str(evidence.get("rule", "")).startswith("V28_Ec_"):
            evidence["rule_release"] = RELEASE
    return result
