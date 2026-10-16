"""Minimum explicit-reference coding using two independently recorded anchors.

No source paragraph is classified as a unit and no dimension vector is copied.
Each addition requires an actual current substantive predicate, an authenticated
referenced content phrase, and a relation-specific dimension permission.
"""
import hashlib
import re
from baseline_candidate17 import matching_view
from rule_support import RuleView
from rules_se import S_BASIS,E_BASIS
from rules_ec import EC_BASIS
from rules_if import BASIS_I,BASIS_F

BASES={'S':S_BASIS,'E':E_BASIS,'Ec':EC_BASIS,'I':BASIS_I,'F':BASIS_F}
REFERENCE=r'(?:第[零一二三四五六七八九十百0-9]+条|本(?:办法|规范|规则|指南|方案)|上述|前述|所列)'
DIMENSION_CONTENT={
    'S':r'安全有效|安全性|不良反应|不良事件|毒性|毒理|用药风险|药物风险|药品质量(?:安全|风险)',
    'E':r'安全有效|有效性|疗效|临床获益|治疗效果|防治效果|临床比较优势',
    'Ec':r'价格合理|药品价格|药价|药费|药品费用|治疗费用|治疗成本|支付标准|下调比例|降幅|医保基金(?:支付|支出)',
    'I':r'创新属性|原创性|专有试验数据保护|试验数据保护|数据保护期|市场独占期',
    'F':r'(?:不)?纳入[^。；;，,]{0,15}(?:《?药品目录》?|医保支付范围)|(?:调出|移出|退出)[^。；;，,]{0,15}(?:《?药品目录》?|医保支付范围)|(?:保障|保证|确保)[^。；;，,]{0,12}药品供应|患者药费负担',
}


def current_relation(text):
    """Return only a current substantive relation, never a route or identity."""
    if not re.search(REFERENCE,text):return None
    if re.search(r'拟新增|评审范围|调整范围|申报范围|申报条件|申报资格',text):
        # A separate actual predicate remains eligible only when explicitly
        # anchored below; a mere listing/category never does.
        assessment_scope=True
    else:assessment_scope=False
    actual_coverage=re.search(r'(?:应当|应|将|予以|决定|直接|可以|可)[^。；;，,]{0,12}(?:纳入|调出|移出|退出)[^。；;，,]{0,12}(?:《?药品目录》?|医保支付范围)|确定[^。；;，,]{0,12}药品[^。；;，,]{0,12}(?:纳入|退出|调出)[^。；;，,]{0,15}(?:标准|条件)',text)
    if actual_coverage and not assessment_scope:
        return 'actual_coverage_standard',set(BASES)
    economic=re.search(r'(?:按|按照|参照|依据|根据)[^。；;]{0,35}(?:计算|确定|调整|下调)[^。；;]{0,18}(?:支付标准|下调比例|降幅|药品价格)',text)
    if economic:return 'current_drug_payment_standard',{'Ec'}
    rights=re.search(r'(?:给予|享有|保护范围|保护期限)[^。；;]{0,25}(?:数据保护期|试验数据保护|市场独占期)|(?:数据保护期|试验数据保护)[^。；;]{0,20}(?:给予|享有|保护范围|保护期限)',text)
    if rights:return 'current_proprietary_drug_data_right',{'I'}
    assessment=re.search(r'(?:按照|按|依据|根据|参照)[^。；;]{0,35}(?:评价|评估|比较|审查|验证|证明)[^。；;]{0,30}',text)
    if not assessment:return None
    # Explicitly restricted evaluation content cannot borrow unrelated criteria
    # in the same cited article. Generic drug-value evaluation can read all.
    explicit={d for d,p in DIMENSION_CONTENT.items() if re.search(p,text)}
    if re.search(r'临床优势',text):explicit.add('E')
    return 'current_dimension_evaluation_requirement',explicit or set(BASES)


def content_matches(text,dimension):
    normalized,offsets=matching_view(text)
    for m in re.finditer(DIMENSION_CONTENT[dimension],normalized):
        left=max(normalized.rfind(c,0,m.start()) for c in '。；;，,')+1
        stops=[normalized.find(c,m.end()) for c in '。；;，,']
        right=min((x for x in stops if x>=0),default=len(normalized))
        clause=normalized[left:right]
        if dimension=='E' and m.group()=='有效性' and re.search(r'(?:数据|证据|软件|系统)(?:的)?$',normalized[:m.start()]):continue
        if dimension=='S' and m.group()=='安全性' and re.search(r'(?:数据|网络|基金|生产)(?:的)?$',normalized[:m.start()]):continue
        if re.search(r'公开|公示|保密|文件名|归档|上传格式',clause) and not re.search(r'评价|评估|比较|分析|收集|补充|监测|(?:提交|提供)[^。；;]{0,20}(?:信息|数据|证据|资料)',clause):continue
        a,b=offsets[left][0],offsets[right-1][1]
        yield a,b,text[a:b]


def revise(record,result):
    if result.get('judgement_status')=='undetermined':return result
    v=RuleView(record,result)
    for group in record.get('typed_contexts_v34',[]):
        if group.get('role')!='current_local_list_predicate' or not group.get('target_is_list_child'):continue
        parent=group['parent_predicate'];value=parent['text']
        if (not re.search(r'药品|药物|创新药|新药|该药',value) or
                not re.search(r'收集|关注|汇总|报告|提交|提供|来源',value) or
                not re.search(r'来源|临床试验|病例|文献|研究',v.normalized)):
            continue
        for dimension in ('S','E','Ec'):
            for a,b,quoted in content_matches(value,dimension):
                dependency={'kind':'authenticated_local_predicate_current_evidence_source',
                            'source_context_field':group['field'],'cited_paragraph_id':parent['paragraph_id'],
                            'cited_source_sha256':parent['source_sha256'],'cited_start':a,'cited_end':b,
                            'cited_text':quoted,'source_authentication':parent['authentication_v34']}
                e=v.add('V34_'+dimension+'_authenticated_local_evidence_source_list',dimension,0,len(v.text),
                        None,BASES[dimension],dependency=dependency,
                        safety_basis='other_safety' if dimension=='S' else None)
                actual=next(x for x in result['evidence'] if x['rule']==e['rule'] and x['dimension']==dimension)
                actual['current_relation_anchor']={'start':actual['start'],'end':actual['end'],'text':actual['text']}
                anchor={'start':a,'end':b,'text':quoted,'paragraph_id':parent['paragraph_id'],
                        'source_path':parent['source_path'],'source_sha256':parent['source_sha256'],
                        'candidate_sha256':parent['candidate_sha256'],'pages':parent.get('pages',[]),
                        'paragraph_sha256':hashlib.sha256(value.encode()).hexdigest(),
                        'source_authentication':parent['authentication_v34']}
                if anchor not in actual.setdefault('cited_substantive_anchors',[]):actual['cited_substantive_anchors'].append(anchor)
    for sentence in re.finditer(r'[^。；;]+',v.normalized):
        relation=current_relation(sentence.group())
        if relation is None:continue
        kind,allowed=relation
        if not (v.drug_scope or re.search(r'药品|药物|药费|该药',sentence.group())):continue
        for group in record.get('typed_contexts_v34',[]):
            if group.get('field') not in {'explicitly_cited_articles_v10','explicitly_cited_qualifications_v12'}:continue
            if group.get('role')=='navigation_preview_only':continue
            for c in group.get('contexts',[]):
                auth=c.get('authentication_v34')
                if not auth:continue
                address=group.get('reference_address') or c.get('article') or ''
                articles=re.findall(r'第[零一二三四五六七八九十百0-9]+条',address)
                if articles and not any(x in sentence.group() for x in articles):continue
                for dimension in allowed:
                    for a,b,quoted in content_matches(c['text'],dimension):
                        dependency={'kind':'explicit_cited_substantive_two_anchor_relation',
                            'current_relation_kind':kind,'current_unit_sha256':hashlib.sha256(v.original.encode()).hexdigest(),
                            'source_context_field':group['field'],'reference_address':group.get('reference_address'),
                            'cited_paragraph_id':c.get('paragraph_id'),'cited_source_path':c.get('source_path'),
                            'cited_source_sha256':c.get('source_sha256'),'cited_candidate_sha256':c.get('candidate_sha256'),
                            'cited_paragraph_sha256':hashlib.sha256(c['text'].encode()).hexdigest(),
                            'cited_start':a,'cited_end':b,'cited_text':quoted,'pages':c.get('pages',[]),
                            'source_authentication':auth}
                        subtype=('affordability' if '患者药费负担' in quoted else 'access') if dimension=='F' else 'attribute' if dimension=='I' else None
                        quality=(dimension=='S' and bool(re.search(r'药品质量(?:安全|风险)',quoted)) and not re.search(r'不良反应|不良事件|毒性|用药风险|药物风险',quoted))
                        rule='V34_'+dimension+'_explicit_cited_'+kind+('_quality' if quality else '')
                        e=v.add(rule,dimension,*sentence.span(),
                                subtype,BASES[dimension],dependency=dependency,
                                safety_basis=('quality_safety' if quality else 'other_safety') if dimension=='S' else None)
                        # One current relation can cite distinct content anchors.
                        # RuleView deduplicates current spans; retain every exact
                        # source anchor without duplicating a dimension label.
                        existing=next(x for x in result['evidence'] if x['rule']==e['rule'] and x['dimension']==dimension and x['start']==e['start'] and x['end']==e['end'])
                        anchor={'start':a,'end':b,'text':quoted,'paragraph_id':c.get('paragraph_id'),
                                'source_path':c.get('source_path'),'source_sha256':c.get('source_sha256'),
                                'candidate_sha256':c.get('candidate_sha256'),'pages':c.get('pages',[]),
                                'paragraph_sha256':hashlib.sha256(c['text'].encode()).hexdigest(),
                                'source_authentication':auth}
                        if anchor not in existing.setdefault('cited_substantive_anchors',[]):existing['cited_substantive_anchors'].append(anchor)
                        existing['current_relation_anchor']={'start':existing['start'],'end':existing['end'],'text':existing['text']}
    return result
