"""CAL-5D v1.3 relation repairs found in exposed development review.

Only text, validated same-unit context, and current evidence are used.
No sample ID, department, file title, A/C label, or target metric is consulted.
The new rules distinguish a substantive instrument/eligibility relation from
procedure identity. This module does not change any construct definition.
"""
import re
from rule_support import RuleView
from rules_if import (_has_drug_object, _carrier_only, _disclosure_only,
                      _norm, _context_object, _verified_innovation_scope, BASIS_I, BASIS_F)

RELEASE='v31-recall-boundary-review-20261007'

def _add(v, sentence, rule, dimension, match, subtype, dependency=None):
    if _carrier_only(sentence.group()) or _disclosure_only(sentence.group()):
        return
    item=v.add(rule,dimension,sentence.start()+match.start(),sentence.start()+match.end(),
               subtype,BASIS_I if dimension=='I' else BASIS_F,dependency=dependency)
    item['rule_release']=RELEASE


def revise(record,result):
    if result.get('judgement_status')=='undetermined':return result
    v=RuleView(record,result)
    innovation_scope=_verified_innovation_scope(v)
    for s in v.sentences():
        x=s.group()
        # A concrete institution or instrument and an explicit drug-innovation
        # target form one support proposition. A generic preamble or publishing
        # a document titled about innovation supplies neither instrument.
        instrument=r'(?:建立|完善|实施|健全)(?:药品加快上市注册制度|药品试验数据保护制度|药物研发资助制度|药品研发资助制度|药品市场独占制度)'
        innovation_goal=r'(?:支持|促进|鼓励|激励|推动)(?:以[^。；;，,]{1,25}为导向的)?(?:药物|药品)创新'
        for m in re.finditer(rf'{instrument}[^。；;]{{0,50}}?{innovation_goal}',x):
            if not re.search(r'软件|办公|另行|另一个|与此同时',m.group()):
                _add(v,s,'V31_I_concrete_instrument_innovation_goal','I',m,'research_support')
        # Next generation plus an explicit product-directed resistance change
        # is attribute/development content, rather than the category 新药 alone.
        for m in re.finditer(r'(?:寻找|研制|研发|开发|创制)新一代(?:能|可以|可)?克服[^。；;，,]{0,12}耐药(?:的)?[^。；;，,]{0,12}(?:新药|药物|制剂)',x):
            _add(v,s,'V31_I_specific_next_generation_change','I',m,'attribute')
        # Management category of an already-covered drug is distinct from
        # actual drug inclusion/exclusion or payment eligibility. A move from
        # agreement-period to ordinary-category management alone supplies no F.
        parents='。'.join(_norm(p['text']) for p in record.get('verified_parent_context',[]))
        known_covered=bool(re.search(r'协议期内谈判药品|目录内[^。；;]{0,35}药品|竞价药品支付标准有效期到期',x)
                           or re.search(r'协议期内谈判药品',parents))
        category=re.search(r'纳入(?:常规目录(?:乙类)?|[“\"]?乙类药品[”\"]?)(?:管理)?|列入目录乙类',x)
        if category and known_covered:
            a,b=v.raw_span(s.start()+category.start(),s.start()+category.end())
            v.drop(lambda e:e['dimension']=='F' and any(k in e['rule'] for k in ('membership','directory_decision','directory_category'))
                   and e['start']<b and a<e['end'],
                   'V31_F_existing_coverage_management_category',
                   '当前只规定已有保障药品的协议/常规或乙类管理归属，未改变药品给付覆盖、患者负担或具体使用障碍。')
        # A category proposition may explicitly describe its medicines as
        # already listed, followed by an ethnic-medicine/preparation class.
        prior_listing=re.search(r'(?:按国家规定)?纳入(?:《药品目录》|药品目录)的(?:民族药|医疗机构制剂)',v.normalized[s.start():s.end()])
        if category and prior_listing:
            a,b=v.raw_span(s.start()+prior_listing.start(),s.start()+prior_listing.end())
            c,d=v.raw_span(s.start()+category.start(),s.start()+category.end())
            v.drop(lambda e:e['dimension']=='F' and any(k in e['rule'] for k in ('membership','directory_decision','directory_category'))
                   and (e['start']<b and a<e['end'] or e['start']<d and c<e['end']),
                   'V31_F_prior_listed_product_category_only',
                   '当前仅把按规定已入目录的民族药/机构制剂归入乙类管理，先前目录身份不等于当前给付覆盖决定。')
        if innovation_scope:
            for m in re.finditer(r'对纳入突破性治疗药物程序的药物[^。；;]{0,35}优先配置资源[^。；;]{0,30}(?:促进|支持|指导)药物研发',x):
                _add(v,s,'V31_I_verified_innovation_object_research_support','I',m,'research_support',
                     {'kind':'verified_innovation_object_for_current_substantive_research_support','innovation_object_scope':innovation_scope})

        # Assessing who will organise a later membership decision is procedural
        # responsibility, without an actual criterion or content requirement.
        for m in re.finditer(r'(?:组织|安排|召开)专家(?:评审|论证)(?:是否|能否)将(?:该)?药品纳入(?:常规|基本|医保|药品)目录管理|(?:评审专家|专家)对药品进行评审[^。；;]{0,12}确定该药品是否纳入常规目录管理',x):
            a,b=v.raw_span(s.start()+m.start(),s.start()+m.end())
            v.drop(lambda e:e['dimension']=='F' and ('membership' in e['rule'] or 'directory_decision' in e['rule'])
                   and a<=e['start'] and e['end']<=b,
                   'V31_F_future_decision_procedure_not_membership',
                   '当前仅规定组织专家论证是否转类的办理职责，未规定覆盖条件、归属或保障获取内容。')
        # An already-listed drug is the eligible object of a price obligation.
        # Remove only the membership phrase; any independent supply/access
        # obligation elsewhere in the sentence survives.
        for m in re.finditer(r'药品通过(?:竞价|谈判)纳入(?:医保|基本|药品)目录的',x):
            if not re.search(r'(?:供应|销售|采购)[^。；;]{0,45}价格[^。；;]{0,25}(?:不高于|不低于|不得高于|不超过)',x[m.end():]):continue
            a,b=v.raw_span(s.start()+m.start(),s.start()+m.end())
            v.drop(lambda e:e['dimension']=='F' and ('membership' in e['rule'] or 'directory_decision' in e['rule'])
                   and a<=e['start'] and e['end']<=b,
                   'V31_F_listed_identity_as_price_condition',
                   '已纳入目录只限定价格承诺的适用药品；当前实质约束供应价格，不重新规定保障归属。')

    for p,prefix in v.paragraph_prefixes():
        antecedent=_norm(prefix)
        # The same paragraph must explicitly establish innovative-drug R&D.
        # Current unit must itself grant a concrete fast-track instrument or
        # explain a specified collaboration requirement, not just name a class.
        innovative_rnd=bool(re.search(r'(?:支持|鼓励)[^。；;]{0,55}参与创新药(?:物)?(?:早期)?(?:临床)?研发',antecedent))
        if innovative_rnd:
            for s in v.sentences():
                x=s.group()
                for m in re.finditer(r'支持符合条件的全球同步研发品种[^。；;]{0,50}纳入[0-9一二三四五六七八九十]+日通道',x):
                    _add(v,s,'V31_I_bound_innovative_rnd_fast_track','I',m,'research_support',
                         v.dependency(p,'same_paragraph_explicit_innovative_drug_rnd_object',antecedent))
                if re.search(r'纳入[0-9一二三四五六七八九十]+日通道',antecedent):
                    for m in re.finditer(r'(?:主要)?研究者早期参与(?:临床)?研发[,，](?:有助于|有利于|促进)创新药(?:物)?(?:全球)?同步研发',x):
                        if re.search(r'应当[^。；;]{0,80}(?:牵头|共同牵头)',x):
                            _add(v,s,'V31_I_innovative_rnd_support_participation_condition','I',m,'research_support',
                                 v.dependency(p,'same_paragraph_explicit_support_instrument_and_innovative_rnd_object',antecedent))
        # Trial access requires all three anchors: unavailable standard therapy
        # for the population, trial as its treatment route, and an actual
        # arrangement aimed at obtaining treatment in this current unit.
        no_standard=bool(re.search(r'(?:没有|已无|尚无)(?:标准|有效|可用)?治疗(?:可供选择|可选|手段|方案|药物)',antecedent))
        if no_standard:
            for s in v.sentences():
                x=s.group()
                if not re.search(r'临床试验(?:即|就)?是重要的治疗手段',x):continue
                for m in re.finditer(r'(?:为了)?使[^。；;，,]{0,18}患者在临床试验中[^。；;，,]{0,15}获得(?:潜在)?治疗',x):
                    if re.search(r'推荐[^。；;]{0,30}试验[^。；;]{0,70}进行',x):
                        _add(v,s,'V31_F_no_standard_therapy_trial_treatment_arrangement','F',m,'access',
                             v.dependency(p,'same_paragraph_no_standard_treatment_population',antecedent))
    return result
