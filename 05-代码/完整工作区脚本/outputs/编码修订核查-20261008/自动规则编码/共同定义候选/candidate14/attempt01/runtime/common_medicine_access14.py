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

from common_innovation_relations14 import (_document,_authenticate_paragraph,
    _require,GuidelineScopeUnavailable,MANUAL_SHA256,
    current_pointer,resolve_current_contents)
from common_cited_list_conditions12 import _source_anchor
from source_context_adapter_v33 import digest

VERSION='common-current-medicine-need-access-finite-14'
J=r'[^。；;\n]'
_TITLE=re.compile(r'《[^》\n]*》')
_CARRIER=re.compile(r'文件名|栏目名称|字样|字符串|排版|上传格式|填写格式|模板')
_SHORTAGE=re.compile(r'(?P<need>临床急需)(?:的)?(?P<barrier>短缺(?:药品|药物))')
_PRIORITY=re.compile(r'(?:可以申请适用|申请适用|符合)?(?P<action>优先审评审批)(?:程序|范围)?')


def _pending(result,error,relation):
    result.setdefault('common14_pending_dimensions',{}).setdefault('F',[]).append(
        dict(relation=relation,reason=error.reason,details=error.details,unknown_is_zero=False))
    result.setdefault('review_flags',[]).append('COMMON14 necessary F source relation unresolved; not zero')


def _emit(result,text,start,end,kind,anchors,dependency,basis):
    if _CARRIER.search(text[start:end]):
        return
    for anchor in anchors:
        assert text[anchor['start']:anchor['end']]==anchor['text']
    result['evidence'].append(dict(dimension='F',rule='COMMON14_F_'+kind,
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


def _atom(text,match,role):
    a,b=match.span();return dict(start=a,end=b,text=text[a:b],role=role)


_DRUG=re.compile(r'药品|药物|用药|试验治疗|药物治疗')
_GROUP=re.compile(r'老年(?:人群|患者|人)|高龄(?:患者|人群|老年患者)|未[^。；;]{0,12}富集[^。；;]{0,10}人群|'
    r'肝功能(?:异常|不全)(?:人群|患者)?|伴有[^。；;]{0,25}(?:患者|人群)|对照组患者|'
    r'(?:特殊|特定|目标)[^。；;]{0,12}(?:人群|患者)')
_GAP=re.compile(r'(?:数据|证据)[^。；;]{0,8}(?:缺失|不足|缺乏)|(?:缺乏|缺失|不足)[^。；;]{0,35}(?:数据|证据)')
_LIMIT=re.compile(r'限制[^。；;]{0,12}(?:临床)?治疗|无法满足[^。；;]{0,55}治疗需求|'
    r'难以[^。；;]{0,25}(?:接受|获得|持续)[^。；;]{0,20}(?:用药|药物治疗)')
_SOCIAL=re.compile(r'经济状况|经济条件|社会经济(?:因素|条件|状况)|家庭支持|社会参与度')
_IMPACT=re.compile(r'影响|限制|妨碍|降低|阻碍|难以')
_CONTINUITY=re.compile(r'药物治疗[^。；;]{0,15}(?:接受度|接受|持续性|持续)|(?:接受|持续)[^。；;]{0,15}(?:药物治疗|用药)')
_EVENT=re.compile(r'(?:疾病)?(?:进展|复发|恶化)')
_CROSS=re.compile(r'交叉(?:至|到|进入|转入)[^。；;]{0,18}(?:试验|治疗)组')
_RECEIPT=re.compile(r'接受(?:该|这一|试验药物|研究药物)?治疗|接受(?:试验|研究)药物|获得(?:试验|研究)药物')
_LONG=re.compile(r'(?:使用|治疗|用药)(?:周期|疗程|时间)[^。；;]{0,8}(?:较长|长期|长期性)|长(?:期|疗程)(?:治疗|用药)')
_COST=re.compile(r'(?:疗程|治疗|用药)?费用[^。；;]{0,8}(?:较高|高昂|过高)|高(?:额)?(?:治疗|用药)?费用')
_EXTRA=re.compile(r'(?:建立|实行|提供|探索)[^。；;]{0,15}(?:单独|专门|额外|专项)[^。；;]{0,15}(?:药品|药物|用药|治疗)?保障|'
    r'(?:单独|专门|额外|专项)[^。；;]{0,12}(?:药品|药物|用药|治疗)?保障机制')


def current_medicine_relations(text):
    """Return current-role frames; each has an explicit fairness relation.

    General speed/efficacy/representation or a drug/programme name alone has
    no frame. A described barrier can count without a proposed intervention.
    Object-only context may resolve an anaphor, never supply a missing barrier.
    """
    masked=_TITLE.sub(lambda m:' '*len(m.group()),text)
    if _CARRIER.search(masked): return []
    frames=[]
    drug=_DRUG.search(masked)
    group=_GROUP.search(masked);gap=_GAP.search(masked);limit=_LIMIT.search(masked)
    if group and gap and limit and gap.start()<limit.start():
        frames.append(dict(kind='group_evidence_gap_limits_medicine_treatment',
            anchors=[_atom(text,group,'specified_treatment_group'),_atom(text,gap,'stated_evidence_gap'),
                     _atom(text,limit,'actual_or_conditional_treatment_limit')],requires_drug_object=True))
    social=_SOCIAL.search(masked);impact=_IMPACT.search(masked);continuity=_CONTINUITY.search(masked)
    if social and impact and continuity and social.start()<impact.start()<continuity.end():
        frames.append(dict(kind='social_conditions_affect_medicine_receipt_continuity',
            anchors=[_atom(text,social,'specified_social_economic_condition'),_atom(text,impact,'explicit_barrier_relation'),
                     _atom(text,continuity,'medicine_receipt_or_continuity')],requires_drug_object=True))
    need=re.search(r'(?:未[^。；;]{0,15}富集[^。；;]{0,15}人群|其他[^。；;]{0,15}人群)[^。；;]{0,25}治疗需求',masked)
    expansion=re.search(r'(?:扩大|扩展|拓展)[^。；;]{0,12}治疗人群(?:范围)?',masked)
    if need and expansion and need.start()<expansion.start() and drug:
        frames.append(dict(kind='uncovered_group_need_and_expanded_medicine_treatment',
            anchors=[_atom(text,need,'specific_uncovered_group_treatment_need'),
                     _atom(text,expansion,'actual_medicine_treatment_population_expansion')],requires_drug_object=True))
    event=_EVENT.search(masked);control=re.search(r'对照组(?:患者|受试者)',masked)
    cross=_CROSS.search(masked);receipt=_RECEIPT.search(masked[cross.start():]) if cross else None
    if event and control and cross and receipt and control.start()<cross.start() and event.start()<cross.start():
        a=cross.start()+receipt.start();b=cross.start()+receipt.end()
        frames.append(dict(kind='disease_event_control_group_actual_crossover_treatment',
            anchors=[_atom(text,control,'previous_control_group'),_atom(text,event,'specified_disease_trigger'),
                     _atom(text,cross,'conditional_treatment_group_crossover'),
                     dict(start=a,end=b,text=text[a:b],role='actual_drug_treatment_receipt')],requires_drug_object=True))
    long=_LONG.search(masked);cost=_COST.search(masked);extra=_EXTRA.search(masked)
    if long and cost and extra and drug and max(long.start(),cost.start())<extra.start():
        frames.append(dict(kind='long_high_cost_medicine_additional_guarantee',
            anchors=[_atom(text,long,'specific_long_treatment_need'),_atom(text,cost,'stated_high_treatment_burden'),
                     _atom(text,drug,'specified_medicine'),_atom(text,extra,'additional_medicine_guarantee')],requires_drug_object=True))
    # Identified domestic authorisation gap plus an actual priority/time
    # arrangement. General earlier marketing is deliberately absent.
    need=re.search(r'临床急需',masked);barrier=re.search(r'境外已上市境内未上市',masked)
    action=re.search(r'审评时限为[0-9零一二三四五六七八九十百]+日|优先审评审批',masked)
    if need and barrier and drug and action and need.start()<action.start() and barrier.start()<action.start():
        frames.append(dict(kind='needed_unmarketed_medicine_actual_authorization_support',
            anchors=[_atom(text,need,'specific_clinical_medicine_need'),_atom(text,barrier,'domestic_market_access_gap'),
                     _atom(text,drug,'needed_medicine'),_atom(text,action,'actual_authorization_arrangement')],requires_drug_object=True))
    barrier=re.search(r'无药可治|无(?:其他)?治疗药物|缺乏(?:其他)?治疗药物',masked)
    need=re.search(r'急迫的治疗需求|急需治疗|迫切治疗需求',masked)
    access=re.search(r'(?:入组的)?受试者(?:均|都)(?:能|可|可以)?接受(?:试验|药物)治疗',masked)
    if barrier and need and access and drug and barrier.start()<access.start() and need.start()<access.start():
        frames.append(dict(kind='no_medicine_need_uniform_actual_trial_treatment',
            anchors=[_atom(text,barrier,'no_medicine_treatment_option'),_atom(text,need,'urgent_treatment_need'),
                     _atom(text,access,'actual_uniform_medicine_treatment_opportunity')],requires_drug_object=True))
    return frames


def _medicine_object(current,text,frames):
    direct=_DRUG.search(text)
    if direct:
        return dict(kind='current_medicine_object',start=direct.start(),end=direct.end(),text=direct.group())
    # Only current paragraph explicitly resolves a treatment anaphor. Context
    # cannot create a gap, social condition, need or action missing in current.
    ptext=current['text'];start=ptext.find(text)
    if start<0: return None
    candidates=list(re.finditer(r'(?:药物|药品|用药)(?:治疗|研发|开发)?',ptext))
    if not candidates: return None
    match=min(candidates,key=lambda m:min(abs(m.start()-start),abs(m.start()-start-len(text))))
    return dict(kind='same_actual_paragraph_medicine_object_only',
                actual_object_anchor=_source_anchor(current,*match.span()),dimension_assignment=False)


def _direct_access(record,result):
    text=record['unit_text'];frames=current_medicine_relations(text)
    if not frames: return
    try:
        doc,paras,i=_document(record);current=_authenticate_paragraph(record,paras[i],doc)
        obj=_medicine_object(current,text,frames)
        if obj is None:
            result.setdefault('common14_scope_observations',[]).append(dict(
                kind='fairness_relation_without_identified_medicine_object',fairness_assigned=False))
            return
        for frame in frames:
            anchors=frame['anchors'];a=min(x['start'] for x in anchors);b=max(x['end'] for x in anchors)
            _emit(result,text,a,b,frame['kind'],anchors,
                dict(kind='actual_current_medicine_fairness_relation',current_source_context=current,
                    necessary_medicine_object=obj,labels_may_be_copied=False,general_trial_participation_used=False),
                'F：当前特定治疗需要/药物治疗障碍或按需实际受药机会的明确关系；描述性及条件性障碍无需另有干预。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'current_medicine_fairness_relation')


def _required_access_list(record,result):
    text=record['unit_text']
    if not current_pointer(text): return
    try:
        dependency=resolve_current_contents(record)
        if dependency is None: return
        substantive=[]
        for member in dependency['members']:
            content=member['text'];current=member['context']
            frames=current_medicine_relations(content)
            obj=_medicine_object(current,content,frames) if frames else None
            if obj:
                for frame in frames:
                    substantive.append(dict(relation=frame['kind'],necessary_medicine_object=obj,
                        actual_content_anchors=[_source_anchor(current,member['start']+x['start'],member['start']+x['end'])
                                               for x in frame['anchors']]))
            # Existing shortage approval semantics: a required actual shortage
            # member links the current specified priority arrangement, not a
            # copied dimension from the member's other unit.
            shortage=_SHORTAGE.search(content)
            if shortage and _PRIORITY.search(text):
                substantive.append(dict(relation='required_shortage_priority_condition',
                    actual_content_anchors=[_source_anchor(current,member['start']+shortage.start(),
                                                         member['start']+shortage.end())]))
        if substantive:
            d=copy.deepcopy(dependency);d.pop('members',None);d['actual_substantive_fairness_relations']=substantive
            _emit(result,text,0,len(text),'current_explicit_complete_content_fairness',
                [dict(start=0,end=len(text),text=text,role='current_explicit_substantive_content_pointer')],d,
                'F：当前确指完整实际内容包含药物治疗保障/障碍关系，当前引导句、实际成员和完整实际区间分别留锚；不复制成员标签。')
    except GuidelineScopeUnavailable as error:
        _pending(result,error,'current_explicit_complete_content_fairness')


def retired_speed_trigger(text):
    # Exact envelope of the two removed candidate13 time-only families. This
    # records possible removals for review; it emits no dimension evidence.
    return bool(re.search(r'提前终止'+J+r'{1,60}试验[，,]\s*可以缩短药物上市时间[，,]\s*及早满足患者对有效药物可及性的需求',text)
        or re.search(r'为了缩短临床试验时间[，,]\s*使药物及早上市满足'+J+r'{0,15}患者的治疗需求[，,]\s*(?:可能|可以|可)?选择'+J+r'{1,85}(?:研究终点|试验终点)',text))


def trigger_reasons(record):
    text=record.get('unit_text','')
    checks={'clinical_shortage_priority':bool(_SHORTAGE.search(_TITLE.sub(lambda m:' '*len(m.group()),text)) and not _CARRIER.search(text)),
        'explicit_complete_content_pointer':current_pointer(text),
        'current_medicine_fairness_roles':bool(current_medicine_relations(text)),
        'retired_time_only_candidate13':retired_speed_trigger(text)}
    return [k for k,v in checks.items() if v]


def revise(record,result):
    if result.get('judgement_status')=='undetermined':
        return result
    dispatch=[('clinical_shortage_priority',_shortage_priority),
        ('explicit_complete_content_pointer',_required_access_list),('current_medicine_fairness_roles',_direct_access)]
    triggers=trigger_reasons(record)
    for gate,handler in dispatch:
        if gate not in triggers: continue
        try:
            handler(record,result)
        except (ValueError,KeyError,StopIteration,OSError,subprocess.CalledProcessError) as error:
            _pending(result,GuidelineScopeUnavailable('actual source relation failed',
                exception_type=type(error).__name__,exception_message=str(error)),handler.__name__)
    result['common14_medicine_access_scope']=dict(version=VERSION,manual_sha256=MANUAL_SHA256,
        nonzero_target_used=False,department_feature_used=False,labels_from_other_units_used=False,
        development_candidate_not_adopted=True)
    return result
