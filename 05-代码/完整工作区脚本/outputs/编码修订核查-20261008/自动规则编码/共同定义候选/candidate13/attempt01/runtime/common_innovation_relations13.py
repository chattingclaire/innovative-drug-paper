"""Finite current innovation-support relations under the unchanged manual.

Only source material enters these rules. Scientific advice and technical
communication need their own current predicates; neutral context resolves an
object only. Decimal references must adopt substantive requirements, bind the
actual chapter and complete section, and stop there (no recursive expansion).
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

from common_guideline_scope11 import (GuidelineScopeUnavailable,
    resolve_guideline_scope, _paragraph_context)
from source_context_adapter_v33 import candidate, file_sha, norm, digest
from source_context_adapter_v34 import authenticate_target, authenticate_context
from common_cited_list_conditions12 import _content_evidence, _source_anchor

VERSION = 'common-current-innovation-support-finite-13'
MANUAL_SHA256 = '5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c'
INNOVATIVE = r'(?:创新药(?:物)?|改良型新药|改良型药品)'
J = r'[^。；;\n]'
_CARRIER = re.compile(r'文件名|栏目名称|字样|字符串|排版|上传格式|填写格式|模板')
_TITLE = re.compile(r'《[^》\n]*》')
_DECIMAL = r'[0-9]+(?:\.[0-9]+){1,4}'


def _require(ok, reason, **details):
    if not ok:
        raise GuidelineScopeUnavailable(reason, **details)


def _document(record):
    authenticate_target(record)
    doc = candidate(record['candidate_file'])
    source = record.get('unit_source') or record.get('source')
    sha = record.get('unit_source_sha256') or record.get('source_sha256')
    _require(doc.get('source') == source and doc.get('source_sha256') == sha,
             'current candidate/source identity differs')
    paragraphs = doc.get('paragraphs', [])
    unit = next(u for u in doc['unit_candidates'] if u['id'] == record['unit_id'])
    indexes = [i for i,p in enumerate(paragraphs) if p['id'] == unit.get('paragraph_id')]
    _require(len(indexes) == 1, 'current paragraph is not unique')
    i = indexes[0]
    _require(paragraphs[i]['text'].count(record['unit_text']) == 1,
             'current unit is not unique in its actual paragraph')
    return doc, paragraphs, i


def _authenticate_paragraph(record, paragraph, doc=None):
    """Actual bytes and ordered physical lines; prior-review fallback rejected."""
    doc = doc or candidate(record['candidate_file'])
    source = record.get('unit_source') or record.get('source')
    sha = record.get('unit_source_sha256') or record.get('source_sha256')
    _require(file_sha(source) == sha and file_sha(record['candidate_file']) == record['candidate_sha256'],
             'source/candidate bytes changed')
    if Path(source).suffix.lower() == '.pdf':
        raw = subprocess.run(['pdftotext','-layout','-enc','UTF-8',source,'-'],
                             check=True,capture_output=True,text=True).stdout
        pages = raw.split('\f')
        if pages and not pages[-1].strip():
            pages.pop()
        return _paragraph_context(record, paragraph,
            {line['id']:line for line in doc['lines']}, pages)
    ids = paragraph.get('line_ids') or []
    line_map = {line['id']:line for line in doc.get('lines', [])}
    _require(ids and all(i in line_map for i in ids), 'bound source lines absent')
    _require(norm(''.join(line_map[i]['text'] for i in ids)) == norm(paragraph['text']),
             'bound source lines do not reproduce the paragraph')
    suffix = Path(source).suffix.lower()
    if suffix == '.txt':
        raw_lines = Path(source).read_text().splitlines()
        numbers = paragraph.get('source_lines') or [line_map[i].get('line') for i in ids]
        _require(all(type(n) is int and 1 <= n <= len(raw_lines) for n in numbers),
                 'actual TXT line positions unavailable')
        _require(norm(''.join(raw_lines[n-1] for n in numbers)) == norm(paragraph['text']),
                 'actual TXT lines differ from the bound paragraph')
    elif suffix == '.json':
        source_doc = json.loads(Path(source).read_text())
        values = source_doc.get('normative_paragraphs', [])
        indexes = [int(m.group(1))-1 for key in ids
                   if (m := re.fullmatch(r'normative_paragraphs:([0-9]+)', key))]
        _require(len(indexes) == len(ids) and all(0 <= i < len(values) for i in indexes),
                 'actual JSON normative paragraph positions unavailable')
        _require(norm(''.join(values[i] for i in indexes)) == norm(paragraph['text']),
                 'actual JSON normative paragraphs differ')
    else:
        raise GuidelineScopeUnavailable('unsupported actual source locator for new finite relation')
    cert = dict(text=paragraph['text'], paragraph_id=paragraph['id'],
        source_path=source,source_sha256=sha,candidate_path=record['candidate_file'],
        candidate_sha256=record['candidate_sha256'],pages=paragraph.get('pages',[]),
        source_lines=paragraph.get('source_lines') or ids)
    cert = authenticate_context(cert)
    auth = cert['authentication_v34']
    _require(auth.get('literal_reproduced_in_current_runtime') is True or
             auth.get('layout_reconstructed_literal_reproduced') is True,
             'actual source reproduction absent; prior review not accepted')
    cert['actual_bound_locator_reproduced'] = True
    return cert


def _pending(result, error, relation):
    result.setdefault('common13_pending_dimensions', {}).setdefault('I', []).append(
        dict(relation=relation,reason=error.reason,details=error.details,
             unknown_is_zero=False))
    result.setdefault('review_flags', []).append('COMMON13 necessary I source relation unresolved; not zero')


def _emit(result, text, kind, match, roles, dependency, basis, subtype='research_support'):
    a,b = match.span()
    if _CARRIER.search(text[a:b]):
        return
    anchors = [dict(role=role,start=match.start(name),end=match.end(name),
                    text=text[match.start(name):match.end(name)]) for name,role in roles.items()]
    result['evidence'].append(dict(dimension='I',rule='COMMON13_I_'+kind,
        start=a,end=b,text=text[a:b],subtype=subtype,current_relation_anchors=anchors,
        context_dependency=dependency,common_definition_basis=basis,
        common_rules_sha256=MANUAL_SHA256,rule_release=VERSION))


def current_scientific_guidance(text):
    """Current scientific design advice, not facility/service/PV obligations."""
    masked = _TITLE.sub(lambda m:' '*len(m.group()),text)
    patterns = [
      (r'(?P<task>在设计过程中)[，,]\s*(?P<action>应(?:当)?(?:充分)?结合)'
       rf'(?P<method>{J}{{1,35}}(?:工程|科学|设计)原则)[，,]\s*'
       rf'(?P<advice>考虑{J}{{1,100}}(?:能力|特征|需求))',
       {'task':'current_design_task','action':'current_technical_guidance',
        'method':'specified_scientific_method','advice':'specified_design_consideration'}),
      (rf'(?P<action>鼓励|建议)(?P<task>在临床(?:研究|试验)过程中)'
       rf'(?P<data>{J}{{0,40}}(?:收集|采集){J}{{1,70}}数据)[，,]\s*'
       rf'(?P<use>并可(?:参考|基于|依据)数据(?:改善|优化|调整){J}{{1,65}})'
       rf'(?:[，,]或者(?P<development>开发{J}{{1,65}}(?:片剂|规格|剂型|制剂)))?',
       {'action':'current_guidance_predicate','task':'clinical_research_task',
        'data':'specified_research_data_collection','use':'data_linked_product_design'}),
      (rf'(?P<action>可将|应将)(?P<aim>减少{J}{{0,20}}试验参与者负担)'
       rf'作为(?P<design>访视形式和内容安排)的考虑要素[，,]\s*'
       rf'(?P<advice>(?:尽可能地)?(?:优化|调整)试验流程)[，,]\s*'
       rf'(?P<method>(?:仅保留|减少){J}{{0,85}}面对面访视{J}{{0,85}}操作程序)',
       {'action':'current_guidance_predicate','aim':'trial_participant_design_constraint',
        'design':'specific_clinical_visit_design','advice':'current_trial_design_guidance',
        'method':'specified_visit_and_operation_method'})]
    return [(m,roles) for pattern,roles in patterns for m in re.finditer(pattern,masked)
            if not _CARRIER.search(text[m.start():m.end()])]


def _scientific(record,result):
    text=record['unit_text']; matches=current_scientific_guidance(text)
    if not matches:
        return
    try:
        scope=resolve_guideline_scope(record)
        if scope is None:
            result.setdefault('common13_scope_observations', []).append(
                dict(kind='current_design_advice_without_resolved_innovative_rnd_object',innovation_assigned=False))
            return
        current=scope['current_paragraph_context'];ptext=current['text'];start=ptext.index(text)
        for match,roles in matches:
            # An omitted design object must be a current explicitly continued
            # drug/device-use design, not some other design in the guideline.
            if match.groupdict().get('task')=='在设计过程中':
                prefix=ptext[:start]
                _require(re.search(r'(?:注射|给药|药物|制剂|片剂)'+J+r'{0,110}(?:装置|设计|需求)',prefix),
                         'omitted current design object lacks same-paragraph drug-use antecedent')
                scope=copy.deepcopy(scope)
                scope['current_design_object_antecedent']=_source_anchor(current,0,start)
            _emit(result,text,'authenticated_current_scientific_design_guidance',match,roles,
                  scope,'I路径3：当前具体研发/临床设计指导与实际认证的创新研发指南对象相连；不据普通改善赋产品创新。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'current_scientific_design_guidance')


def _communication(record,result):
    text=record['unit_text'];masked=_TITLE.sub(lambda m:' '*len(m.group()),text)
    direct=re.search(r'(?P<action>鼓励)(?P<recipient>(?:新药)?研发人员)与'
        r'(?P<provider>药品技术审评机构)(?P<support>密切沟通)',masked)
    problem=re.search(r'(?P<issue>如有未能阐明的个性化问题)[，,]\s*'
        r'(?P<action>可采用)(?P<support>沟通交流)的方式(?P<solution>解决)',masked)
    if not direct and not problem:
        return
    try:
        doc,paras,i=_document(record);current=_authenticate_paragraph(record,paras[i],doc)
        start=current['text'].index(text);prefix=current['text'][:start]
        if direct:
            obj=re.search(INNOVATIVE+J+r'{0,50}(?:安全性(?:数据)?(?:的)?评价|研发|开发|临床试验)',masked)
            if not obj:
                return
            dependency=dict(kind='actual_current_rnd_regulator_communication',
                current_source_context=current,innovation_object_current_anchor=
                dict(start=obj.start(),end=obj.end(),text=text[obj.start():obj.end()]),
                labels_may_be_copied=False)
            _emit(result,text,'current_regulatory_technical_communication',direct,
                {'action':'actual_communication_offer','recipient':'research_recipient',
                 'provider':'technical_review_provider','support':'technical_communication'},dependency,
                'I路径3：当前明确向创新药研发人员安排/鼓励与技术审评机构沟通；安全评价内容不排除实际支持。')
        if problem:
            antecedent=re.search(r'本指导原则'+J+r'{0,130}针对'+J+r'{0,45}'+INNOVATIVE+
                r'产品[，,]'+J+r'{0,100}提供建议',prefix)
            if not antecedent:
                return
            dependency=dict(kind='same_paragraph_current_technical_issue_and_innovation_guidance_object',
                current_source_context=current,necessary_object_antecedent=
                _source_anchor(current,*antecedent.span()),max_relation_edges=1,labels_may_be_copied=False)
            _emit(result,text,'specified_guideline_technical_issue_communication',problem,
                {'issue':'current_unresolved_technical_issue','action':'actual_support_offer',
                 'support':'technical_communication','solution':'issue_resolution'},dependency,
                'I路径3：当前实际提供未阐明技术问题的沟通解决方式；同段认证前文仅补全该创新研发指导对象。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'technical_communication')


def _first_communication(record,result):
    text=record['unit_text']
    match=re.search(r'(?P<support>首次沟通交流)的(?P<arrangement>沟通形式包括)'
                    rf'(?P<form>{J}{{1,95}}(?:会议|回复))',text)
    if not match:
        return
    try:
        doc,paras,i=_document(record)
        _require(i>0,'first communication has no immediate source antecedent')
        current=_authenticate_paragraph(record,paras[i],doc)
        previous=_authenticate_paragraph(record,paras[i-1],doc)
        parent=re.search(r'首次沟通交流[。.]*在纳入(?P<program>[^，,。；;]{1,35}程序)'
                         +J+r'{0,75}首次沟通交流申请',previous['text'])
        _require(parent and re.search(r'研发情况|药学研发|临床试验',previous['text']) and
                 re.search(r'药审中心|药品审评机构',previous['text']),
                 'current first communication lacks identified research-program support antecedent')
        cert=record.get('verified_innovation_scope_v27') or {}
        loc=cert.get('locator') or {};pid=loc.get('paragraph_id')
        scope=[p for p in paras if p['id']==pid]
        _require(len(scope)==1 and norm(cert.get('text',''))==norm(scope[0]['text']),
                 'innovation program scope is unbound to actual candidate paragraph')
        scope=scope[0];qualified=_authenticate_paragraph(record,scope,doc)
        program=parent['program']
        _require(re.search(INNOVATIVE,qualified['text']) and '临床试验' in qualified['text'] and
                 re.search(r'申请适用'+re.escape(program),qualified['text']),
                 'actual program scope does not name the current program and innovative R&D')
        _require(Path(current['source_path']).suffix.lower()=='.txt',
                 'finite program-component binding currently requires actual TXT attachment source')
        raw=Path(current['source_path']).read_text().splitlines()
        boundaries=[i+1 for i,line in enumerate(raw) if re.fullmatch(r'附件[0-9一二三四五六七八九十]+',line.strip())]
        positions=[]
        for context in (qualified,previous,current):
            numbers=context['source_lines'];_require(all(type(n)is int for n in numbers),'program source lines not numeric')
            positions.extend(numbers)
        first=max((n for n in boundaries if n<=min(positions)),default=None)
        last=min((n for n in boundaries if n>first),default=len(raw)+1) if first else None
        _require(first and max(positions)<last,'program relation crosses an actual attachment boundary')
        actualtitle=raw[first].strip()
        stem=re.sub(r'药物|审评|工作|程序','',program)
        _require(stem and stem in actualtitle and actualtitle.endswith(('程序（试行）','程序(试行)','程序')),
                 'actual attachment title does not identify the named program')
        dependency=dict(kind='first_technical_communication_actual_program_three_anchors',
            current_source_context=current,actual_immediate_support_antecedent=previous,
            actual_innovation_program_scope=qualified,actual_attachment_title=actualtitle,
            actual_attachment_start_line=first,actual_next_attachment_line=last,
            old_supplied_verified_boolean_accepted=False,max_relation_edges=2,
            labels_may_be_copied=False,recursive_program_qualification_expansion=False)
        _emit(result,text,'first_technical_communication_modalities',match,
            {'support':'specified_research_communication','arrangement':'actual_support_arrangement',
             'form':'concrete_communication_options'},dependency,
            'I路径3：当前具体安排首次研发沟通形式，前段及同一实际附件资格原文仅解析其创新研发程序对象。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'first_technical_communication')


def _protection_comparison(record,result):
    text=record['unit_text']
    match=re.search(r'(?P<reference>本条款中药品)的(?P<qualification>数据保护范围包括证明其)'
                    rf'(?P<comparison>与{J}{{1,85}}相比具有明显临床优势)的'
                    r'(?P<evidence>新的临床试验数据)',text)
    if not match:
        return
    try:
        doc,paras,i=_document(record);_require(i>0,'protection comparison has no previous source paragraph')
        current=_authenticate_paragraph(record,paras[i],doc)
        previous=_authenticate_paragraph(record,paras[i-1],doc)
        actual=re.search(r'(?:改良型药品|改良型新药)'+J+r'{0,70}给予[0-9一二三四五六七八九十]+年数据保护期',previous['text'])
        if not actual:
            return
        _require(paras[i].get('article') and paras[i].get('article')==paras[i-1].get('article'),
                 'protection antecedent is not in the same actual article')
        # JSON source positions above are reproduced, including actual order.
        a=int(paras[i-1]['source_key'].split(':')[-1]);b=int(paras[i]['source_key'].split(':')[-1])
        _require(b==a+1,'source protection paragraphs are not immediately adjacent')
        dependency=dict(kind='current_comparison_of_authenticated_improved_drug_qualification',
            current_source_context=current,actual_immediate_improved_qualification=
            _source_anchor(previous,*actual.span()),article=paras[i]['article'],
            max_relation_edges=1,labels_may_be_copied=False,protection_period_alone_used=False)
        _emit(result,text,'improved_drug_protected_data_comparison',match,
            {'reference':'current_explicit_drug_reference','qualification':'actual_qualification_evidence_scope',
             'comparison':'substantive_drug_comparison','evidence':'required_clinical_evidence'},dependency,
            'I路径4：当前数据保护范围实质讨论已明确改良药资格的比较证据条件；不由保护期限或一般临床优势单独推定。',
            'qualification_advantage')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'improved_qualification_comparison')


def _decimal_requirements(record,result):
    text=record['unit_text']
    match=re.search(r'(?P<requirement>资料要求)(?P<action>同|按|按照)'
       rf'(?P<chapter>[^，,。；;]{{2,45}}资料要求)\s*'
       rf'(?P<addresses>{_DECIMAL}(?:\s*[、，,及和]\s*{_DECIMAL}){{0,8}})\s*(?P<relation>项下)',text)
    if not match or _CARRIER.search(match.group()):
        return
    try:
        doc,paras,i=_document(record);current=_authenticate_paragraph(record,paras[i],doc)
        addresses=re.findall(_DECIMAL,match['addresses'])
        groups=[g for g in record.get('typed_contexts_v34',[]) if g.get('field') in
            {'explicitly_cited_articles_v10','explicitly_cited_qualifications_v12'}]
        for address in addresses:
            selected=[g for g in groups if address in re.findall(_DECIMAL,g.get('reference_address') or '') and
                      norm(match['chapter']) in norm(g.get('reference_address') or '')]
            _require(len(selected)==1,'explicit decimal target absent or ambiguous',address=address)
            group=selected[0];contexts=group['contexts']
            _require(group.get('complete_interval_authenticated') is True and
                     all(c['candidate_path']==record['candidate_file'] and c['source_path']==current['source_path']
                         for c in contexts),'decimal reference requires complete same-document actual section',address=address)
            indexes=[k for k,p in enumerate(paras) if p['id']==contexts[0]['paragraph_id']]
            _require(len(indexes)==1,'decimal first paragraph absent',address=address)
            first=indexes[0]
            interval=paras[first:first+len(contexts)]
            _require([p['id'] for p in interval]==[c['paragraph_id'] for c in contexts] and
                     re.search(r'(?<![0-9.])'+re.escape(address)+r'(?![0-9.])',interval[0]['text']),
                     'decimal exact section heading/interval differs',address=address)
            headings=[p for p in paras[:first] if re.match(r'^[一二三四五六七八九十]+[、.\s]?',p['text'])
                      and not re.search(_DECIMAL,p['text'])]
            _require(headings,'decimal actual chapter heading absent',address=address)
            heading=headings[-1];topic=re.sub(r'^[一二三四五六七八九十]+[、.\s]*','',heading['text'])
            _require(norm(topic)==norm(match['chapter'].removesuffix('资料要求')),
                     'same-number reference belongs to a different actual source chapter',address=address)
            chapter=_authenticate_paragraph(record,heading,doc)
            actual=[_authenticate_paragraph(record,p,doc) for p in interval]
            _require(first+len(actual)<len(paras),'complete decimal section has no actual next boundary',address=address)
            boundary=_authenticate_paragraph(record,paras[first+len(actual)],doc)
            substantive=[]
            for content in actual:
                for detected in _content_evidence(content['text']):
                    # Current adoption preserves existing concept boundaries.
                    substantive.append((detected,_source_anchor(content,detected['start'],detected['end'])))
            # Existing fixed detector recognises explicit innovative support
            # objects. The neutral application scope resolves the section's
            # pronoun only; actual research qualifications remain in section.
            scope_inputs=record.get('source_application_scope04') or []
            shared_scope=record.get('llm_v29_shared_context',{}).get('source_application_scope04')
            _require(shared_scope is None or shared_scope==scope_inputs,
                     'neutral application scope differs across shared materials')
            scopes=[]
            for supplied in scope_inputs:
                if not re.search(INNOVATIVE,supplied.get('text','')):
                    continue
                ps=[p for p in paras if p['id']==supplied.get('paragraph_id') and p['text']==supplied.get('text')]
                _require(len(ps)==1 and supplied.get('source_path')==current['source_path'] and
                         supplied.get('source_sha256')==current['source_sha256'] and
                         supplied.get('candidate_path')==record['candidate_file'] and
                         supplied.get('candidate_sha256')==record['candidate_sha256'],
                         'neutral innovative application scope supplied version differs')
                scope=_authenticate_paragraph(record,ps[0],doc)
                if re.search(r'纳入\s*[0-9]+\s*日临床试验审评审批的创新药',scope['text']):
                    scopes.append(scope)
            qualifications=[(c,m) for c in actual if (m:=re.search(
                r'申请人应提供符合条件的说明及相关证明性材料',c['text']))]
            scientific_requirements=[(c,m) for c in actual if (m:=re.search(
                r'申请人应提供全球同步研发的研发计划等证明性材料',c['text']))]
            if len(qualifications)==len(scientific_requirements)==len(scopes)==1:
                # Manual path3 support-qualification grammar, anchored to actual
                # specified research requirements, not an innovation title.
                scope=scopes[0]
                qc,qm=qualifications[0];sc,sm=scientific_requirements[0]
                anchor=_source_anchor(sc,*sm.span())
                anchor['actual_support_qualification_antecedent']=_source_anchor(qc,*qm.span())
                anchor['necessary_innovation_support_object']=_source_anchor(scope)
                substantive.append((dict(dimension='I',rule='COMMON13_I_actual_innovative_support_research_qualification',
                    subtype='research_support',common_definition_basis='I路径3：明确创新研发审评支持资格的实质同步研发计划要求。'),
                    anchor))
                result.setdefault('common13_source_field_consumption',[]).append(dict(
                    field='source_application_scope04',paragraph_id=scope['paragraph_id'],
                    usage='identified_innovative_review_support_object_only',dimension_assignment=False,
                    source_path=scope['source_path'],source_sha256=scope['source_sha256']))
            for detected,anchor in substantive:
                dim=detected['dimension']
                e=copy.deepcopy(detected);e.update(dimension=dim,rule='COMMON13_'+dim+'_exact_decimal_requirement',
                    start=match.start(),end=match.end(),text=match.group(),rule_release=VERSION,
                    common_rules_sha256=MANUAL_SHA256,current_relation_anchors=[dict(role=role,
                    start=match.start(name),end=match.end(name),text=text[match.start(name):match.end(name)])
                    for name,role in [('requirement','current_content_requirement'),('action','actual_requirement_adoption'),
                    ('chapter','explicit_actual_source_chapter'),('addresses','exact_section_addresses')]],
                    context_dependency=dict(kind='current_adopted_complete_decimal_section_three_anchors',
                        current_source_context=current,actual_source_chapter=chapter,exact_section_address=address,
                        complete_actual_section_contexts=[_source_anchor(c) for c in actual],actual_next_boundary=boundary,
                        cited_substantive_content=anchor,max_relation_edges=2,recursive_reference_expansion=False,
                        labels_may_be_copied=False,old_reference_role=group['role']),cited_substantive_anchors=[anchor])
                e.pop('matching_text',None);result['evidence'].append(e)
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'adopted_decimal_substantive_requirements')


def revise(record,result):
    if result.get('judgement_status')=='undetermined':
        return result
    for handler in (_scientific,_communication,_first_communication,_protection_comparison,_decimal_requirements):
        try:
            handler(record,result)
        except (ValueError,KeyError,StopIteration,OSError,subprocess.CalledProcessError) as error:
            # A triggered new relation with bad necessary bytes/locators must
            # remain unresolved; it is neither a positive nor a negative test.
            _pending(result,GuidelineScopeUnavailable('actual source relation failed',
                exception_type=type(error).__name__,exception_message=str(error)),handler.__name__)
    result['common13_relation_scope']=dict(version=VERSION,manual_sha256=MANUAL_SHA256,
        labels_from_other_units_used=False,identity_semantic_features_used=False,
        recursive_scope_expansion=False,development_candidate_not_adopted=True)
    return result
