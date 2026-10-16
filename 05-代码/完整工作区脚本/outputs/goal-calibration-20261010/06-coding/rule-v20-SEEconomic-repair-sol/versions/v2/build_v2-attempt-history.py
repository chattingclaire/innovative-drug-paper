"""Build isolated v2 from sealed v1; never mutate origin."""
from pathlib import Path
import re
P=Path(__file__).resolve().parent; V1=P.parents[1]
d=(V1/'dimensions.py').read_text(); s=(V1/'se_predicates.inc').read_text()
s=s.replace(r'\b(?:AE|ADR|SAE|AESI)\b',r'(?<![A-Za-z])(?:AESI|ADR|SAE|AE)(?![A-Za-z])')
s=s.replace('不良(?:反应|事件)|','不良(?:反应|事件)|肝损伤|副作用|神经毒性|预防接种异常反应|治疗窗窄|')
s=s.replace('(?:大于|小于|不大于)','(?:大于|小于|不大于|超过|高于|低于)')
s=s.replace('治疗效果|防治效果|','治疗效果|治疗效应|疾病控制(?:效果|要求|证据)?|防治效果|')
s=s.replace('(?:患者|受试者)[^。；;，,]{0,18}获益','(?:患者|受试者)[^。；;，,]{0,18}获益|获益[^。；;，,]{0,12}(?:患者|受试者)')
s=s.replace('基金(?:实际)?支出|','医保支付|基金支付|基金(?:实际)?支出|')
s=s.replace('    return unit.kind not in {"named_mechanism", "policy_explanation", "price_arrangement"}','    if unit.kind in {"substantive_list", "cited_standard"}:\n        return bool(unit.details.get("SE_scope_verified"))\n    return unit.kind not in {"named_mechanism", "policy_explanation", "price_arrangement"}')
start=s.index('def _se_form_or_status(');end=s.index('\n\ndef _se_object',start)
s=s[:start]+'''def _se_form_or_status(text, dim):
    # Evaluate the actual content action separately from titles and file nouns.
    topic = {"S": SE_RISK + "|" + SE_BENEFIT_RISK + r"|安全性|用药安全", "E": SE_EFFECT + "|" + SE_BENEFIT_RISK + r"|有效性|安全[、,]?有效", "Ec":SE_ECON}[dim]
    parts = re.split(r"[。；;，,]", text)
    actual = any(re.search(topic, p) and re.search(r"评价|评估|比较|核验|核对|说明|测算|确认|分析|证明|解释|估计|结算|合理|预算|监测|控制|承担|提供", p)
                 and not re.search(r"(?:仅|只)(?:检查|确认|审核)[^。；;]{0,20}(?:格式|位数|命名|文件名)|(?:命名|格式|文件名|包名)[^。；;]{0,15}(?:须|应|必须|采用|改为)", p) for p in parts)
    actual = actual or bool(re.search(r"(?:提交|递交|补充|提供)[^。；;，,]{0,18}(?:安全性|药物风险|疗效|疾病控制效果|治疗效果)[^。；;，,]{0,8}(?:证据|数据|分析)",text))
    if re.search(r"(?:已经|已)(?:获得|取得|登记|列为)[^。；;]{0,30}(?:称号|名号|产品名|名称)|(?:安全有效)[^。；;]{0,15}(?:称号|名称)",text) and not re.search(r"核验|评价|评估|比较|证明",text): return True
    forms = re.search(r"字段|栏目|格式|签字|签章|盖章|文件名|包名|命名|压缩包|上传|归档|递交|提交|编号填写|填写申报表", text)
    if forms and not actual:
        # A report name or declared approved status does not establish content.
        return True
    if dim == "S":
        residue = re.sub(r"(?:药物)?研发期间安全性更新报告", "报告", text)
        if residue != text and not re.search(SE_RISK + "|" + SE_BENEFIT_RISK + r"|安全性(?:内容|信息|数据|证据|分析|评价)", residue): return True
        if re.search(r"药物警戒工作经验[^。；;]{0,10}说明",text): return True
        if re.search(r"药理毒理学|非临床安全性评价研究|药理毒理",text) and not re.search(SE_RISK + r"|安全性(?:结果|数据|证据|内容|信息)|获益[^。；;]{0,10}风险",re.sub(r"药理毒理学|非临床安全性评价研究|药理毒理","学科",text)):
            return bool(re.search(r"完成|开展|进行|计划|机构|认证|资料|研究工作",text))
    if dim == "E" and re.search(r"(?:建立|收载|公开|更新)[^。；;]{0,80}目录集|目录集[^。；;]{0,80}(?:载明|公开|更新)",text):
        return not bool(re.search(r"(?:核验|评价|比较|分析|验证)[^。；;]{0,15}(?:疗效|治疗效果|有效性)",text))
    return False
''' +s[end:]
s=s.replace('view.norm in _norm(raw)','_norm(view.norm) in _norm(raw)')
s=s.replace('r"针对|适用(?:于)?|以[^。；;]{0,15}为对象"','r"针对|适用(?:于)?|以[^。；;]{0,15}为对象|对[^。；;]{0,25}(?:药物|药品)[^。；;]{0,18}(?:临床研发|研究|用药)"')
s=s.replace('    return obj\n\n\ndef _se_general','''    # An actual prescription correctness or vaccine-harm proposition already
    # supplies a medication object. This does not import an outcome from headings.
    if re.search(r"处方[^。；;]{0,25}(?:剂量|用法|配伍)|预防接种异常反应",unit.text):
        return {"established":True,"current_anchors":[view.current_anchor(unit.a,unit.b)],"context_evidence":[],"role":"explicit_medication_or_vaccine_harm_object"}
    return obj


def _se_general''')
s=s.replace('        scope = text + ("。" + unit.inherited if direct_parent else "")','''        scope = text + ("。" + unit.inherited if direct_parent else "")
        if re.search(r"^(?:为了|为)[^。；;]{0,100}(?:现将|予以)[^。；;]{0,80}(?:印发|发布)$",scope) and not re.search(r"(?:应|必须|须|要求)[^。；;]{0,30}(?:核验|评价|评估|监测|控制)|(?:药物|药品)[^。；;]{0,15}(?:造成|导致|存在)[^。；;]{0,15}(?:损伤|不良反应|风险)",scope):
            acc.exclude(dim,unit,"当前仅印发文件的宗旨，未规定实质风险或效果内容。")
            continue''')
s=s.replace('            risk = re.search(SE_RISK + "|" + SE_BENEFIT_RISK, scope)','''            comparison = re.search(SE_BENEFIT_RISK, scope)
            specific_risk = re.search(SE_RISK, scope)
            generic_risk = re.search(r"(?:药品|药物|用药)[^。；;，,]{0,15}风险",scope)
            non_drug_owner = re.search(r"(?:基础疾病|疾病进展|病情进展|数据丢失|申报数据|网络|消防|车间)[^。；;]{0,18}(?:风险|安全)",scope)
            linked_risk = re.search(r"风险控制|风险管理",text) if unit.details.get("relation_subtype")=="SE_same_drug_risk_control_example" and re.search(r"给药|用药",unit.inherited) else None
            risk = comparison or specific_risk or linked_risk or (generic_risk if not non_drug_owner else None)''')
s=s.replace('|(?:药品|药物|用药)[^。；;，,]{0,15}风险|安全性(?!更新报告)','|(?:耐受性)[^。；;，,]{0,10}(?:较差|不足|降低)|安全性(?!更新报告)')
s=s.replace('            if risk and substance or safety_content and (substance or governed or re.search(r"重要|更高|较大|缺陷", scope)):','''            if comparison or risk and (substance or re.search(r"严重|危害|不鼓励|不得|信号",scope)) or safety_content and (substance or governed or re.search(r"重要|更高|较大|缺陷|排除", scope)):''')
s=s.replace('SE_RISK = r"', 'SE_RISK = r"(?:风险控制|风险管理)[^。；;]{0,100}(?:给药|用药)|')
s=s.replace('or re.search(r"导致|造成|发生|存在|可能|特征|期望|担忧|变化|减退|混淆", scope)', 'or re.search(r"符合|满足|条件|导致|造成|发生|存在|可能|特征|期望|担忧|变化|减退|混淆", scope)')
s=s.replace('scope = text + ("。" + inherited if unit.details.get("relation_subtype", "").startswith("SE_") else "")', 'scope = text + ("。" + inherited if unit.details.get("relation_subtype", "").startswith("SE_") or unit.kind == "parent_predicate" and re.search(r"(?:费用|药费).{0,50}(?:符合|满足).{0,20}(?:以下|下列).{0,40}(?:基金支付|报销)",inherited) else "")')
s=s.replace('分歧|核验|核对|确认|测算|计算|口径|合理|变化|不调整|确定', '分歧|核验|核对|确认|测算|计算|口径|合理|变化|调整|不调整|确定')
s=s.replace('(?:安全[、,]?有效|更安全[、,]?有效|安全、有效)[^。；;]{0,25}(?:药物治疗方案|重要|条件)','(?:安全[、,]?有效|更安全[、,]?有效|安全、有效)[^。；;]{0,25}(?:药物治疗方案|重要|条件)|(?:符合|满足)[^。；;]{0,15}安全[、,]?有效')
s=s.replace('(?:药品|药物)[^。；;，,]{0,15}(?:安全、?有效|更安全)','(?:药品|药物)[^。；;，,]{0,15}(?:安全、?有效|更安全)|(?:符合|满足)[^。；;]{0,15}安全[、,]?有效')
s=s.replace('or _current_overall_health_effect(scope):','or re.search(r"(?:结局|报告|测定|指标|终点)[^。；;]{0,65}健康相关(?:的)?生活质量|健康相关(?:的)?生活质量[^。；;]{0,30}(?:报告|测定|指标|终点)",scope) or _current_overall_health_effect(scope):')
s=s.replace('r"药价|药费|药品价格|治疗费用|诊疗费用|支付标准|支付范围|基金支出|收入损失|社会经济负担"','r"药价|药费|药品价格|治疗费用|诊疗费用|支付标准|支付范围|基金(?:支出|支付)|收入损失|社会经济负担"')
s=s.replace('(?:确定|形成|提出|比较|对比|调整|控制|限制|测算|核验|说明|计算|不高于|不低于)','(?:协商|确定|形成|提出|比较|对比|调整|控制|限制|测算|核验|说明|介绍|计算|不高于|不低于)')
s=s.replace('(?:价格|费用|成本|支付意愿|支付标准|医保底价)','(?:价格|结算价|费用|成本|预算|支付意愿|支付标准|医保底价)')
s=s.replace('(?:价格|费用|成本|报价|支付意愿)[^。；;，,]{0,25}', '(?:价格|结算价|费用|成本|报价|支付意愿)[^。；;，,]{0,25}')
s=s.replace('info = re.search(r"','info = re.search(r"(?:介绍|包括|含|信息)[^。；;]{0,35}(?:市场价格|销售金额)|(?:医保|基金)支付[^。；;]{0,25}(?:情况|挂钩)|(?:掌握|监测)[^。；;]{0,25}(?:医保|基金)支付|')
s=s.replace('(?:纳入|不纳入|豁免|排除)[^。；;]{0,15}', '(?:纳入|不纳入|豁免|排除)[^。；;]{0,15}')
s=s.replace('governed = unit.kind in {"substantive_list", "cited_standard"} and re.search(SE_ACTION + r"|符合|满足|条件", unit.inherited)','governed = unit.kind in {"substantive_list", "cited_standard"} and re.search(SE_ACTION + r"|符合|满足|条件|调出|续约", unit.inherited)')
s=s.replace('and re.search(r"方可|可以|可申请|须|限制|确定|调整|计算|条件", inherited))','and re.search(r"方可|可以|可申请|须|限制|确定|调整|计算|条件|可由", inherited))')
s=s.replace('authorization or re.search(r"评价|评估|分析|测算|核验|核对|确认|比较|预算影响|成本效果|成本效用", scope)','authorization or re.search(r"评价|评估|分析|测算|核验|核对|确认|比较|预算影响|成本效果|成本效用|合理|科学性|及时性|准确性|挂钩", scope)')
s=s.replace('def _ec_identity_only(text, inherited=""):\n', 'def _ec_identity_only(text, inherited=""):\n    if re.search(r"(?:申报|填报|填写).{0,20}(?:选择|勾选|填写).{0,30}(?:条件编号|编号|类别|分类)",text) and not re.search(r"核验|核对|测算|确认|方可|才能",text):\n        return True\n')
s=s.replace('r"支付标准|支付范围|支付责任|基金预算|报销", inherited', 'r"支付标准|支付范围|支付责任|基金预算|基金支付|报销", inherited')

s=s.replace('        raw = c.get("text", "")\n        same_paragraph', '        raw = c.get("text", "")\n        primary = view.unit.get("source_ref", {}).get("sha256")\n        if c.get("source_ref", {}).get("sha256") != primary: continue\n        current_component = view.unit.get("source_ref", {}).get("locator", {}).get("component_id")\n        component = c.get("structure", {}).get("component_id") or c.get("source_ref", {}).get("locator", {}).get("component_id")\n        if current_component and component and current_component != component: continue\n        same_paragraph')
s=s.replace('数据丢失|申报数据|网络|消防|车间', '数据丢失|数据泄漏|数据库损毁|申报数据|网络|消防|车间')
s=s.replace('            risk = comparison or specific_risk or linked_risk or (generic_risk if not non_drug_owner else None)', '            risk = comparison or specific_risk or linked_risk or (generic_risk if not non_drug_owner else None)\n            if non_drug_owner and not re.search(r"不良反应|肝损伤|副作用|毒性|过敏|用药错误|用药差错|获益.{0,15}风险",scope):\n                risk = None')

s=s.replace('准确性|挂钩", scope)', '准确性|挂钩", scope)')
s=s.replace('|合理|科学性|及时性|准确性|挂钩", scope)', '|科学性|及时性|准确性", scope)')
s=s.replace('if re.search(r"处方[^。；;]{0,25}(?:剂量|用法|配伍)|预防接种异常反应",unit.text)', 'if re.search(r"处方[^。；;]{0,25}(?:剂量|用法|配伍)|配伍禁忌|预防接种异常反应",unit.text)')
s=s.replace('|基金支付|基金(?:实际)?支出', '|基金支付|医保自费率|降价幅度|基金(?:实际)?支出')
s=s.replace('安全性(?!更新报告)", scope)', '更安全[、,]?有效(?:的)?药物治疗方案|安全性(?!更新报告)", scope)')
s=s.replace('risk = comparison or specific_risk or linked_risk or (generic_risk if not non_drug_owner else None)', 'direct_monitor = re.search(r"风险(?:发现|识别).{0,12}(?:干预|控制)",scope) if re.search(r"用药指导|服药后不适",scope) else None\n            risk = comparison or specific_risk or linked_risk or direct_monitor or (generic_risk if not non_drug_owner else None)')
s=s.replace('info = re.search(r"', 'info = re.search(r"(?:医保自费率|基金实际支出)[^。；;]{0,20}(?:不计入|统计)|(?:不计入)[^。；;]{0,20}(?:医保自费率)|(?:控制|确定|降低)[^。；;]{0,25}降价幅度|(?:统筹|结合|根据|依据|以)[^。；;]{0,25}基金支付能力[^。；;]{0,35}(?:约束|开展|确定|调整)|')
s=s.replace('re.search(r"评价|评估|分析|测算|核验|核对|确认|比较|预算影响|成本效果|成本效用|科学性|及时性|准确性", scope)', 're.search(r"评价|评估|分析|测算|核验|核对|确认|比较|预算影响|成本效果|成本效用", scope) or unit.details.get("relation_subtype")=="SE_same_cost_data_reference" and re.search(r"科学性|及时性|准确性",text)')

# Old unverified list inheritance is never opened for S/E/Ec.
(P/'se_predicates.inc').write_text(s)
d=d[:d.index('# S/E/Ec candidate predicates.')]+s+'\n\n'+d[d.index('def judge(view)'):]
# Bounded relation context evidence keeps complete scope, while boundary text
# is used only as closure proof and cannot donate dimensional content.
d=d.replace('for ctx in contexts:\n                        content = _norm(_literal(ctx))','for ctx in contexts:\n                        if ctx.get("context_id") in {q["context_id"] for q in details.get("closure_proof", {}).get("boundary_quotes", [])}:\n                            continue\n                        content = _norm(_literal(ctx))')
d=d.replace('Unit(content[left:right], a + start, a + end, [ctx], kind, details, operative)','Unit(content[left:right], a + start, a + end, contexts if details.get("SE_scope_verified") else [ctx], kind, details, operative)')
# Consumer intersection compatible with I/F v2. No broadening through IF marker.
d=d.replace('        consumers = unit.details.get("affected_dimensions")\n        if consumers is None or "I" in consumers:','        consumers = set(unit.details.get("affected_dimensions", DIMENSIONS))\n        if unit.details.get("only_IF_consumers"):\n            consumers &= {"I", "F"}\n        if "I" in consumers:').replace('        if consumers is None or "F" in consumers:', '        if "F" in consumers:')
(P/'dimensions.py').write_text(d)
# Relations are rebuilt from sealed v1 prefix plus the v2 bounded resolver.
r=(V1/'relations.py').read_text();r=r[:r.index('    def _se_bounded_content(')]+(P/'se_relations.inc').read_text()
r=r.replace("signature = (kind, tuple((e['text'], e['source_ref'].get('sha256')) for e in evidence))", "signature = (kind, tuple((e['context_id'], e['start'], e['end'], e['text'], e['source_ref'].get('sha256')) for e in evidence), details.get('relation_subtype'), tuple(sorted(details.get('affected_dimensions', ['S','E','Ec','I','F']))), bool(details.get('only_IF_consumers')), details.get('norm_start'), details.get('norm_end'), details.get('shared_predicate'))")
r=r.replace('        self._se_bounded_content()' ,'        self._se_bounded_content()\n        self._se_direct_content_parents()\n        self._se_complete_lists()')
(P/'relations.py').write_text(r)
