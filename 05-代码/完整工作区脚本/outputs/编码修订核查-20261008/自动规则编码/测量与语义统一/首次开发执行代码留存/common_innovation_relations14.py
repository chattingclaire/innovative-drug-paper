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
from current_unit_role import permits_content_expansion
from current_innovation_support import current_support_relations

VERSION = 'measurement-semantic-innovation-01'
MANUAL_SHA256 = '24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
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
        try:
            return _paragraph_context(record, paragraph,
                {line['id']:line for line in doc['lines']}, pages)
        except GuidelineScopeUnavailable:
            from visual_source_reader import authenticate_visual_paragraph
            recovered=authenticate_visual_paragraph(record,paragraph)
            if recovered is None: raise
            return recovered
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
    result.setdefault('common14_pending_dimensions', {}).setdefault('I', []).append(
        dict(relation=relation,reason=error.reason,details=error.details,
             unknown_is_zero=False))
    result.setdefault('review_flags', []).append('COMMON14 necessary I source relation unresolved; not zero')


def _emit(result, text, kind, match, roles, dependency, basis, subtype='research_support'):
    a,b = match.span()
    if _CARRIER.search(text[a:b]):
        return
    anchors = [dict(role=role,start=match.start(name),end=match.end(name),
                    text=text[match.start(name):match.end(name)]) for name,role in roles.items()]
    result['evidence'].append(dict(dimension='I',rule='COMMON14_I_'+kind,
        start=a,end=b,text=text[a:b],subtype=subtype,current_relation_anchors=anchors,
        context_dependency=dependency,common_definition_basis=basis,
        common_rules_sha256=MANUAL_SHA256,rule_release=VERSION))


def _atom(text, match, role):
    a,b=match.span();return dict(start=a,end=b,text=text[a:b],role=role)


def _role_evidence(result,text,kind,anchors,dependency,basis,subtype='research_support'):
    if not anchors or _CARRIER.search(text):
        return
    a=min(x['start'] for x in anchors);b=max(x['end'] for x in anchors)
    for x in anchors:
        assert text[x['start']:x['end']]==x['text']
    result['evidence'].append(dict(dimension='I',rule='COMMON14_I_'+kind,
        start=a,end=b,text=text[a:b],subtype=subtype,current_relation_anchors=anchors,
        context_dependency=dependency,common_definition_basis=basis,
        common_rules_sha256=MANUAL_SHA256,rule_release=VERSION))


_GUIDANCE_MODAL=re.compile(r'建议|鼓励|应当|应该|应|宜|可将|可以|可')
_TECH_ACT=re.compile(r'考虑|结合|参考|基于|依据|收集|采集|设计|优化|调整|改善|开发|选择|确定|评估')
_RD_TASK=re.compile(r'临床(?:研究|试验)|设计过程|研发过程|访视|剂量|给药|制剂|片剂|剂型|用药装置')
_TECH_DETAIL=re.compile(r'(?:人因|科学|工程|统计|研究)原则|(?:操作|记忆|视力|握力)[^。；;]{0,18}能力|'
    r'(?:便利性|药代|药效|剂量|操作|访视)[^。；;]{0,28}(?:数据|方法|安排|程序)|'
    r'数据[^。；;]{0,25}(?:改善|优化|调整)|(?:片剂|制剂)(?:易碎性|强度|规格)|'
    r'面对面访视|其他规格或剂型|不同[^。；;]{0,8}(?:剂型|规格|剂量)')
_GENERAL_DUTY=re.compile(r'(?:提交|上报|报告|报送|更新)[^。；;]{0,25}(?:安全性报告|不良反应|药物警戒)|'
    r'药物警戒[^。；;]{0,15}(?:职责|义务|管理)|设施|场地|设备租赁|检测服务|诊疗服务')
_OWN_FUNCTION=re.compile(r'(?:AI|人工智能|设备|系统|软件)[^。；;]{0,25}(?:具有|具备|实现|能够)[^。；;]{0,25}(?:监测|检测|识别)')


def current_scientific_guidance(text):
    """Enumerate modal-governed actions in one current substantive sentence."""
    masked=_TITLE.sub(lambda m:' '*len(m.group()),text)
    out=[]
    for part in re.finditer(r'[^。；;\n]+',masked):
        value=part.group()
        # Current activity controls scope; a broad innovative title cannot
        # turn routine marketed-drug monitoring or a tool capability into RD.
        if (_CARRIER.search(value) or _GENERAL_DUTY.search(value) or _OWN_FUNCTION.search(value)):
            continue
        if re.search(r'上市后[^。；;]{0,20}(?:监测|用药)|常规(?:用药)?监测|临床服务',value) and not re.search(r'(?:用于|服务于|支持)[^。；;]{0,20}(?:创新|改良)[^。；;]{0,8}(?:研发|开发)',value):
            continue
        tasks=list(_RD_TASK.finditer(value));details=list(_TECH_DETAIL.finditer(value))
        for modal in _GUIDANCE_MODAL.finditer(value):
            actions=[m for m in _TECH_ACT.finditer(value,modal.end())
                     if m.start()-modal.end()<=90 and not re.match(r'(?:过程|任务|阶段|方案名称)',value[m.end():])]
            for act in actions:
                # A comma may introduce a coordinated technical choice; a
                # separate directive before this action changes its governor.
                if _GUIDANCE_MODAL.search(value,modal.end(),act.start()):
                    continue
                relevant=[m for m in details if act.start()<=m.start() and m.start()-act.end()<=140]
                if not tasks or not relevant: continue
                task=min(tasks,key=lambda m:min(abs(m.end()-modal.start()),abs(m.start()-act.end())))
                detail=relevant[0]
                anchors=[dict(start=part.start()+m.start(),end=part.start()+m.end(),
                    text=text[part.start()+m.start():part.start()+m.end()],role=role)
                    for m,role in [(modal,'current_guidance_predicate'),(act,'current_scientific_action'),
                                  (task,'specified_research_design_task'),(detail,'specified_technical_advice')]]
                out.append(anchors)
                break
    return out

def _innovative_object(record,current=None):
    doc,paras,i=_document(record)
    current=current or _authenticate_paragraph(record,paras[i],doc)
    text=record['unit_text'];ptext=current['text'];start=ptext.index(text)
    objects=[]
    masked=_TITLE.sub(lambda m:' '*len(m.group()),ptext)
    for m in re.finditer(INNOVATIVE+J+r'{0,65}(?:研发|开发|临床(?:研究|试验)|安全性(?:数据)?(?:的)?评价|产品)',masked):
        # Object is current, or a same-paragraph explicit self-scope. No
        # background/title identity or arbitrary preceding parent is enough.
        if m.end()>start and m.start()<start+len(text):
            objects.append(_source_anchor(current,*m.span()))
        elif m.end()<=start and re.search(r'本(?:技术)?指导原则|针对|适用于|旨在',ptext[:m.start()]):
            objects.append(_source_anchor(current,*m.span()))
    if objects:
        return dict(kind='actual_current_or_same_paragraph_innovative_research_object',
            current_source_context=current,innovation_object_anchors=objects,
            labels_may_be_copied=False,dimension_assignment=False,max_relation_edges=1)
    return resolve_guideline_scope(record)


def _scientific(record,result):
    text=record['unit_text'];matches=current_support_relations(text)
    if not matches:
        return
    try:
        scope=_innovative_object(record)
        if scope is None:
            result.setdefault('common14_scope_observations',[]).append(dict(
                kind='current_support_without_identified_innovative_research_object',innovation_assigned=False))
            return
        for anchors in matches:
            _role_evidence(result,text,'current_specific_research_support',anchors,scope,
                'I路径3：当前资源、具体方案反馈或研发便利安排联系实际创新研发对象；普通研究技术建议不是支持。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'current_specific_research_support')


_COMM_MODAL=re.compile(r'鼓励|建议|可以|可采用|可通过|可|安排|提供')
_COMM_SUPPORT=re.compile(r'沟通交流|沟通|交流|咨询')
_COMM_ACTOR=re.compile(r'(?:新药)?研发人员|申请人|研究者|药品技术审评机构|药审中心|技术审评机构')
_COMM_ISSUE=re.compile(r'(?:未能阐明|尚未明确|未解决|个性化|具体)[^。；;]{0,15}(?:技术)?问题')


def current_communication(text):
    masked=_TITLE.sub(lambda m:' '*len(m.group()),text)
    if (_CARRIER.search(masked) or _GENERAL_DUTY.search(masked) or
        re.search(r'(?:申报|申请|报送|填报)(?:材料|文件)?(?:格式|填写|上传|程序)',masked)):
        return []
    support=_COMM_SUPPORT.search(masked);modal=_COMM_MODAL.search(masked)
    actor=_COMM_ACTOR.search(masked);issue=_COMM_ISSUE.search(masked)
    if not support or not modal or modal.start()>support.start() or not (actor or issue):
        return []
    anchors=[_atom(text,modal,'technical_support_arrangement_mentioned'),_atom(text,support,'technical_communication')]
    if actor: anchors.append(_atom(text,actor,'technical_support_actor'))
    if issue: anchors.append(_atom(text,issue,'current_unresolved_technical_issue'))
    return anchors


def _communication(record,result):
    text=record['unit_text'];anchors=current_communication(text)
    if not anchors:
        return
    try:
        scope=_innovative_object(record)
        if scope is None:
            return
        _role_evidence(result,text,'current_technical_communication',anchors,scope,
            'I路径3：当前具体技术问题的沟通机会或其撤回联系指定创新研发对象；语境仅解析对象，二元presence不证明仍在供给。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'current_technical_communication')


_POINTER=re.compile(r'(?:以下|下列|这些)[^。；;\n]{0,30}(?:条件|要求|问题|方面|药品|范围)|'
    r'(?:包括|包含|涵盖|讨论)[^。；;\n]{0,30}(?:以下|下列)|'
    r'同时满足\s*[(（]一[)）]\s*[(（]二[)）]')
_POINTER_PREDICATE=re.compile(r'包括|包含|涵盖|讨论|满足|符合|要求|列出|申请适用|可以申请|给予|适用|安排|享受')
_REQUIRED=re.compile(r'满足|符合|要求')


def current_pointer(text):
    return bool(_POINTER.search(text) and _POINTER_PREDICATE.search(text) and not _CARRIER.search(text))


def resolve_current_contents(record):
    """Authenticate one expressly pointed complete interval; emits no labels.

    Returned member slices retain their full certified paragraph plus offsets.
    No downstream paragraph or its old label enters through a name/title.
    """
    text=record['unit_text']
    if not current_pointer(text) or not permits_content_expansion(text):
        return None
    doc,paras,i=_document(record);current=_authenticate_paragraph(record,paras[i],doc)
    cert=record.get('complete_following_list_v11')
    if cert:
        contexts=cert.get('contexts') or [];boundary=cert.get('structure_boundary') or {}
        _require(cert.get('original_unit_sha256')==digest(text) and contexts and
                 cert.get('source_sha256')==current['source_sha256'],
                 'explicit complete list version/current anchor differs')
        _require(cert.get('contexts_sha256')==digest(json.dumps(contexts,ensure_ascii=False,sort_keys=True)),
                 'explicit complete list content hash differs')
        actual=paras[i:i+len(contexts)]
        _require([p['id'] for p in actual]==[c.get('paragraph_id') for c in contexts] and
                 [p['text'] for p in actual]==[c.get('text') for c in contexts],
                 'explicit complete list is not the current contiguous actual interval')
        _require(boundary.get('all_paragraphs_in_interval_included') is True and
                 boundary.get('first_paragraph')==actual[0]['id'] and
                 boundary.get('last_paragraph')==actual[-1]['id'] and i+len(actual)<len(paras),
                 'explicit complete list boundary unavailable')
        nxt=paras[i+len(actual)]
        _require(nxt['id']==boundary.get('next_paragraph_id') and nxt['text']==boundary.get('next_paragraph_text'),
                 'actual complete list next boundary differs')
        certified=[_authenticate_paragraph(record,p,doc) for p in actual]
        nextcert=_authenticate_paragraph(record,nxt,doc)
        members=[dict(context=c,start=0,end=len(c['text']),text=c['text']) for c in certified[1:]]
        return dict(kind='actual_current_explicit_complete_interval',current_source_context=current,
            current_pointer_anchor=dict(start=0,end=len(text),text=text),
            complete_actual_contexts=certified,actual_next_boundary=nextcert,members=members,
            max_relation_edges=1,recursive_list_expansion=False,labels_may_be_copied=False)
    # Inline required conditions are bounded by contiguous numeric enumeration
    # in this actual paragraph. An external navigation sentence ends the list.
    ptext=current['text'];start=ptext.index(text)
    if not _REQUIRED.search(text):
        return None
    first=re.search(r'[(（]1[)）]',ptext[start:])
    if not first:
        return None
    first=start+first.start()
    stop=re.search(r'(?:有关|具体)[^。；;]{0,35}(?:详见|参见)|详见|参见',ptext[first:])
    end=first+stop.start() if stop else len(ptext)
    matches=list(re.finditer(r'[(（]([0-9]+)[)）]',ptext[first:end]))
    numbers=[int(m.group(1)) for m in matches]
    _require(len(matches)>=2 and numbers==list(range(1,len(matches)+1)),
             'inline required condition list is incomplete or non-contiguous')
    members=[]
    for n,m in enumerate(matches):
        a=first+m.start();b=first+matches[n+1].start() if n+1<len(matches) else end
        members.append(dict(context=current,start=a,end=b,text=ptext[a:b]))
    return dict(kind='actual_current_inline_required_conditions',current_source_context=current,
        current_pointer_anchor=dict(start=0,end=len(text),text=text),members=members,
        complete_actual_contexts=[current],actual_inline_interval=_source_anchor(current,first,end),
        external_navigation_expanded=False,max_relation_edges=1,labels_may_be_copied=False)


def _required_innovation_list(record,result):
    text=record['unit_text']
    if not current_pointer(text) or not permits_content_expansion(text) or not _REQUIRED.search(text):
        return
    try:
        dependency=resolve_current_contents(record)
        if dependency is None: return
        for member in dependency['members']:
            match=re.search(r'(?:具有|具备|须有|要求)[^。；;]{0,12}(?:较强|显著|充分)?创新性',member['text'])
            if not match: continue
            anchor=_source_anchor(member['context'],member['start']+match.start(),member['start']+match.end())
            d=copy.deepcopy(dependency);d.pop('members',None);d['actual_required_innovation_attribute']=anchor
            _role_evidence(result,text,'current_required_innovation_attribute',
                [dict(start=0,end=len(text),text=text,role='current_explicit_required_conditions')],d,
                'I路径1：当前明确要求的完整实际条件含实质创新属性；不由罕见病或创新药名单独赋值。',
                subtype='innovation_attribute')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'current_required_innovation_attribute')


def _current_support_qualification_list(record,result):
    text=record['unit_text']
    if not current_pointer(text) or not permits_content_expansion(text): return
    action=re.search(r'(?:不再|不予|停止|取消)?(?:可以|可|允许)?(?:申请适用|适用|给予|享受|获得|取消|停止)[^。；;]{0,12}(?:优先审评审批(?:程序)?|加快审评(?:程序)?|专门审评通道)',text)
    if not action: return
    try:
        dependency=resolve_current_contents(record)
        if dependency is None: return
        objects=[]
        for member in dependency['members']:
            for obj in re.finditer(INNOVATIVE,member['text']):
                # Identity exclusions do not select an innovative beneficiary.
                clause=member['text'][max(member['text'].rfind(c,0,obj.start()) for c in '，,。；;')+1:]
                if re.search(r'(?:不属于|不包括|不含|并非|除外|除[^。；;]*外)',clause): continue
                objects.append(_source_anchor(member['context'],member['start']+obj.start(),member['start']+obj.end()))
        if not objects: return
        d=copy.deepcopy(dependency);d.pop('members',None)
        d['actual_innovative_beneficiary_conditions']=objects
        _role_evidence(result,text,'current_explicit_support_qualification',
            [dict(start=action.start(),end=action.end(),text=text[action.start():action.end()],role='current_specific_support_qualification_arrangement')],d,
            'I路径3/4：当前实质总领句安排具体审评便利；完整确指条件只补其创新/改良受益对象，不汇总成员维度。',
            subtype='research_support')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'current_explicit_support_qualification')


def _first_communication(record,result):
    # Forms/meeting media alone do not give the current unit the programme's
    # innovative support status. Independent current technical opportunities
    # are handled by _communication/_scientific, not reverse inheritance.
    text=record['unit_text']
    if re.search(r'首次沟通交流的沟通形式包括',text):
        result.setdefault('common14_scope_observations',[]).append(dict(
            kind='communication_forms_only_no_programme_support_inheritance',
            innovation_assigned=False))


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
                substantive.append((dict(dimension='I',rule='COMMON14_I_actual_innovative_support_research_qualification',
                    subtype='research_support',common_definition_basis='I路径3：明确创新研发审评支持资格的实质同步研发计划要求。'),
                    anchor))
                result.setdefault('common14_source_field_consumption',[]).append(dict(
                    field='source_application_scope04',paragraph_id=scope['paragraph_id'],
                    usage='identified_innovative_review_support_object_only',dimension_assignment=False,
                    source_path=scope['source_path'],source_sha256=scope['source_sha256']))
            for detected,anchor in substantive:
                dim=detected['dimension']
                e=copy.deepcopy(detected);e.update(dimension=dim,rule='COMMON14_'+dim+'_exact_decimal_requirement',
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


def trigger_reasons(record):
    """Content-only envelope, shared with dispatch. Never consumes labels/IDs."""
    text=record.get('unit_text','')
    checks={
        'scientific_guidance_roles':bool(current_support_relations(text)),
        'technical_communication_roles':bool(current_communication(text)),
        'first_communication_bounded_program':bool(re.search(r'首次沟通交流的沟通形式包括',text)),
        'qualified_protection_comparison':bool(re.search(r'本条款中药品的数据保护范围包括证明其',text)),
        'adopted_decimal_requirement':bool(re.search(r'资料要求(?:同|按|按照)',text) and re.search(_DECIMAL,text) and '项下' in text),
        'required_innovation_conditions':bool(current_pointer(text) and permits_content_expansion(text) and _REQUIRED.search(text)),
        'current_support_qualification_conditions':bool(current_pointer(text) and permits_content_expansion(text) and re.search(r'优先审评审批|加快审评|专门审评通道',text))}
    return [k for k,v in checks.items() if v]


def revise(record,result):
    if result.get('judgement_status')=='undetermined':
        return result
    owned={'COMMON14_I_current_scientific_guidance','COMMON14_I_current_specific_research_support','COMMON14_I_first_technical_communication_modalities','COMMON14_I_current_required_innovation_attribute','COMMON14_I_current_explicit_support_qualification'}
    removed=[e for e in result.get('evidence',[]) if e.get('rule') in owned]
    result['evidence']=[e for e in result.get('evidence',[]) if e.get('rule') not in owned]
    result.setdefault('family_migration_trace',[]).append(dict(owner=VERSION,dimension='I',removed_rules=[e['rule'] for e in removed],retired_families=['ordinary_technical_advice_plus_innovation_guideline_scope','communication_forms_reverse_programme_inheritance']))
    dispatch=[('scientific_guidance_roles',_scientific),('technical_communication_roles',_communication),
        ('first_communication_bounded_program',_first_communication),('qualified_protection_comparison',_protection_comparison),
        ('adopted_decimal_requirement',_decimal_requirements),('required_innovation_conditions',_required_innovation_list),
        ('current_support_qualification_conditions',_current_support_qualification_list)]
    triggers=trigger_reasons(record)
    for gate,handler in dispatch:
        if gate not in triggers: continue
        try:
            handler(record,result)
        except (ValueError,KeyError,StopIteration,OSError,subprocess.CalledProcessError) as error:
            # A triggered new relation with bad necessary bytes/locators must
            # remain unresolved; it is neither a positive nor a negative test.
            _pending(result,GuidelineScopeUnavailable('actual source relation failed',
                exception_type=type(error).__name__,exception_message=str(error)),handler.__name__)
    result['common14_relation_scope']=dict(version=VERSION,manual_sha256=MANUAL_SHA256,
        labels_from_other_units_used=False,identity_semantic_features_used=False,
        recursive_scope_expansion=False,development_candidate_not_adopted=True)
    return result
