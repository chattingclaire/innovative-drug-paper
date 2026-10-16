"""Finite medicine-need/access relations under the unchanged F definition.

An unmet clinical medicine need/identified supply barrier must govern an
actual priority approval or medicine-treatment opportunity arrangement.
General research participation, representation and safety duties are absent.
Supplied parents/lists are reauthenticated and provide the current predicate
only; there is no propagation from a programme's name or document title.
"""
import copy
import re
import subprocess

from common_innovation_relations13 import (_document,_authenticate_paragraph,
    _require,GuidelineScopeUnavailable,MANUAL_SHA256)
from common_cited_list_conditions12 import _source_anchor
from source_context_adapter_v33 import digest

VERSION='common-current-medicine-need-access-finite-13'
J=r'[^。；;\n]'
_TITLE=re.compile(r'《[^》\n]*》')
_CARRIER=re.compile(r'文件名|栏目名称|字样|字符串|排版|上传格式|填写格式|模板')
_SHORTAGE=re.compile(r'(?P<need>临床急需)(?:的)?(?P<barrier>短缺(?:药品|药物))')
_PRIORITY=re.compile(r'(?:可以申请适用|申请适用|符合)?(?P<action>优先审评审批)(?:程序|范围)?')


def _pending(result,error,relation):
    result.setdefault('common13_pending_dimensions',{}).setdefault('F',[]).append(
        dict(relation=relation,reason=error.reason,details=error.details,unknown_is_zero=False))
    result.setdefault('review_flags',[]).append('COMMON13 necessary F source relation unresolved; not zero')


def _emit(result,text,start,end,kind,anchors,dependency,basis):
    if _CARRIER.search(text[start:end]):
        return
    for anchor in anchors:
        assert text[anchor['start']:anchor['end']]==anchor['text']
    result['evidence'].append(dict(dimension='F',rule='COMMON13_F_'+kind,
        start=start,end=end,text=text[start:end],subtype='needs_based_guarantee',
        current_relation_anchors=anchors,context_dependency=dependency,
        common_definition_basis=basis,common_rules_sha256=MANUAL_SHA256,rule_release=VERSION))


def _anchor(text,match,name,role):
    a,b=match.span(name);return dict(start=a,end=b,text=text[a:b],role=role)


def _actual_priority_parent(record,doc,paras,current_index):
    """At most two supplied actual controlling predicates, no parent search."""
    supplied=record.get('verified_parent_context') or []
    if not supplied:
        return None
    _require(len(supplied)<=2,'more than two priority predicate relations unsupported')
    actual=[];indexes=[]
    for item in supplied:
        matches=[(i,p) for i,p in enumerate(paras) if p['id']==item.get('paragraph_id') and p['text']==item.get('text')]
        _require(len(matches)==1,'supplied priority predicate not bound to actual paragraph')
        i,p=matches[0];_require(i<current_index,'priority predicate does not precede current item')
        actual.append(_authenticate_paragraph(record,p,doc));indexes.append(i)
    _require(indexes==sorted(indexes) and indexes[-1]+1==current_index,
             'current shortage item does not immediately follow its actual controlling list predicate')
    _require(any(_PRIORITY.search(c['text']) for c in actual),
             'supplied actual predicate lacks priority-approval arrangement')
    _require(all(re.search(r'以下|下列|同时满足|应满足|相关条件',c['text']) for c in actual),
             'actual priority predicate lacks bounded list/requirement relation')
    if len(actual)==2:
        # A parent expressly requires the two same-level conditions; the
        # current item follows the second condition's own list lead.
        _require(re.search(r'同时满足\s*[(（]一[)）]\s*[(（]二[)）]',actual[0]['text']) and
                 re.match(r'^[(（]二[)）]',actual[1]['text']),
                 'two-parent relation is not the actual two-condition/list structure')
    return dict(kind='actual_current_shortage_item_priority_predicate',actual_control_contexts=actual,
        current_paragraph_id=paras[current_index]['id'],max_relation_edges=len(actual),
        recursive_parent_expansion=False,labels_may_be_copied=False)


def _shortage_priority(record,result):
    text=record['unit_text'];masked=_TITLE.sub(lambda m:' '*len(m.group()),text)
    shortage=_SHORTAGE.search(masked)
    if not shortage or _CARRIER.search(text):
        return
    try:
        doc,paras,i=_document(record);current=_authenticate_paragraph(record,paras[i],doc)
        action=_PRIORITY.search(masked)
        if action:
            # An actual programme creation/regulation for clinical shortages
            # is substantive; a name alone is not a medicine access action.
            _require(re.search(r'规范|制定|给予|纳入|可以申请适用|申请适用',masked),
                     'priority programme name lacks actual current arrangement')
            dependency=dict(kind='current_clinical_shortage_priority_approval_arrangement',
                current_source_context=current,labels_may_be_copied=False)
            anchors=[_anchor(text,shortage,'need','specified_clinical_medicine_need'),
                     _anchor(text,shortage,'barrier','actual_medicine_supply_shortage'),
                     _anchor(text,action,'action','priority_market_authorization_arrangement')]
            _emit(result,text,0,len(text),'clinical_shortage_priority_arrangement',anchors,dependency,
                'F：当前临床急需短缺药品与实际优先上市审评安排相连，保存需要、供药障碍及动作；一般程序名称不赋F。')
        else:
            dependency=_actual_priority_parent(record,doc,paras,i)
            if dependency is None:
                return
            dependency['current_source_context']=current
            anchors=[_anchor(text,shortage,'need','specified_clinical_medicine_need'),
                     _anchor(text,shortage,'barrier','actual_medicine_supply_shortage')]
            dependency['actual_action_anchors']=[_source_anchor(c,*m.span('action'))
                for c in dependency['actual_control_contexts'] if (m:=_PRIORITY.search(c['text']))]
            _emit(result,text,0,len(text),'current_shortage_priority_condition',anchors,dependency,
                'F：当前枚举项明确临床急需及短缺障碍；经来源认证的实际控制谓词仅补全其优先上市审批安排。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'clinical_shortage_priority_arrangement')


def _required_shortage_list(record,result):
    text=record['unit_text']
    if not (_PRIORITY.search(text) and re.search(r'以下|下列|同时满足|应满足|相关条件',text)):
        return
    lists=[g for g in record.get('typed_contexts_v34',[]) if g.get('field')=='complete_following_list_v11'
           and g.get('role')=='current_following_conditions_only']
    if not lists:
        return
    try:
        doc,paras,i=_document(record);current=_authenticate_paragraph(record,paras[i],doc)
        for group in lists:
            contexts=group['contexts'];_require(contexts and contexts[0]['paragraph_id']==paras[i]['id'],
                'required priority list does not start in current paragraph')
            matches=[]
            for content in contexts[1:]:
                shortage=_SHORTAGE.search(content['text'])
                if not shortage:
                    continue
                ps=[p for p in paras if p['id']==content['paragraph_id'] and p['text']==content['text']]
                _require(len(ps)==1,'required shortage member differs from actual paragraph')
                certified=_authenticate_paragraph(record,ps[0],doc)
                matches.append(dict(member=_source_anchor(certified),
                    need=_source_anchor(certified,*shortage.span('need')),
                    barrier=_source_anchor(certified,*shortage.span('barrier'))))
            if not matches:
                continue
            action=_PRIORITY.search(text)
            dependency=dict(kind='current_priority_requirement_complete_shortage_list',
                current_source_context=current,actual_member_need_access_anchors=matches,
                complete_list_contexts=copy.deepcopy(contexts),max_relation_edges=1,
                recursive_list_expansion=False,labels_may_be_copied=False)
            _emit(result,text,0,len(text),'current_required_shortage_priority_list',
                [_anchor(text,action,'action','current_priority_market_authorization_arrangement')],dependency,
                'F：当前明确指定完整优先审批范围/条件，实际被要求的成员包括临床急需及短缺障碍；按三锚重新判断而不复制成员标签。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'required_clinical_shortage_list')


def current_direct_access(text):
    """Relations with current need, medicine-access barrier and actual action."""
    masked=_TITLE.sub(lambda m:' '*len(m.group()),text)
    patterns=[
      (rf'(?P<need>临床急需)(?:的)?(?P<barrier>境外已上市境内未上市)(?:的)?'
       rf'(?P<drug>{J}{{0,20}}(?:药品|药物))[，,]\s*'
       r'(?P<action>审评时限为[0-9零一二三四五六七八九十百]+日)',
       {'need':'specified_clinical_medicine_need','barrier':'domestic_market_access_gap',
        'drug':'needed_medicine','action':'actual_review_time_arrangement'}),
      (rf'(?P<action>提前终止{J}{{1,60}}试验)[，,]\s*'
       rf'(?P<access>可以缩短药物上市时间)[，,]\s*'
       rf'(?P<need>及早满足患者对有效药物可及性的需求)',
       {'action':'specified_research_arrangement','access':'earlier_medicine_market_access',
        'need':'explicit_patient_medicine_access_need'}),
      (rf'(?P<barrier>为了缩短临床试验时间)[，,]\s*'
       rf'(?P<need>使药物及早上市满足{J}{{0,15}}患者的治疗需求)[，,]\s*'
       rf'(?P<action>(?:可能|可以|可)?选择{J}{{1,85}}(?:研究终点|试验终点))',
       {'barrier':'specified_medicine_market_access_time_barrier',
        'need':'earlier_medicine_access_linked_patient_need','action':'actual_endpoint_design_option'})]
    out=[]
    for pattern,roles in patterns:
        for match in re.finditer(pattern,masked):
            if not _CARRIER.search(text[match.start():match.end()]):
                out.append((match,roles))
    # An actual alternative design may explicitly preserve every participant's
    # medicine treatment opportunity for urgently untreated patients. This
    # requires the medicine-treatment relation, not participation alone.
    need=re.search(r'(?P<barrier>无药可治)'+J+r'{0,55}(?P<need>急迫的治疗需求)',masked)
    access=re.search(r'(?P<access>入组的受试者均能接受试验治疗)'+J+r'{0,60}治疗机会',masked)
    action=re.search(r'(?P<action>不再要求采用安慰剂/BSC对照)[，,]\s*(?:可以|可)采用单臂试验设计',masked)
    if need and access and action and need.start()<access.start()<action.start() and re.search(r'试验药物',masked):
        out.append((None,dict(need=need,access=access,action=action)))
    return out


def _direct_access(record,result):
    text=record['unit_text'];matches=current_direct_access(text)
    if not matches:
        return
    try:
        doc,paras,i=_document(record);current=_authenticate_paragraph(record,paras[i],doc)
        for match,roles in matches:
            if match:
                anchors=[_anchor(text,match,name,role) for name,role in roles.items()]
                start,end=match.span()
            else:
                anchors=[_anchor(text,roles['need'],'barrier','no_medicine_treatment_option'),
                    _anchor(text,roles['need'],'need','urgent_patient_treatment_need'),
                    _anchor(text,roles['access'],'access','actual_uniform_medicine_treatment_opportunity'),
                    _anchor(text,roles['action'],'action','specified_alternative_trial_arrangement')]
                start=roles['need'].start();end=roles['action'].end()
            _emit(result,text,start,end,'current_need_linked_medicine_access_arrangement',anchors,
                dict(kind='authenticated_current_medicine_need_access_action',
                     current_source_context=current,labels_may_be_copied=False,
                     general_trial_participation_used=False),
                'F：当前具体治疗/药物可及需要经明确关系联系到更早取得药物或实际试验药物治疗机会的安排；不从效率、人群或试验参与身份单独推定。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'current_medicine_need_access_action')


def revise(record,result):
    if result.get('judgement_status')=='undetermined':
        return result
    for handler in (_shortage_priority,_required_shortage_list,_direct_access):
        try:
            handler(record,result)
        except (ValueError,KeyError,StopIteration,OSError,subprocess.CalledProcessError) as error:
            _pending(result,GuidelineScopeUnavailable('actual source relation failed',
                exception_type=type(error).__name__,exception_message=str(error)),handler.__name__)
    result['common13_medicine_access_scope']=dict(version=VERSION,manual_sha256=MANUAL_SHA256,
        nonzero_target_used=False,department_feature_used=False,labels_from_other_units_used=False,
        development_candidate_not_adopted=True)
    return result
