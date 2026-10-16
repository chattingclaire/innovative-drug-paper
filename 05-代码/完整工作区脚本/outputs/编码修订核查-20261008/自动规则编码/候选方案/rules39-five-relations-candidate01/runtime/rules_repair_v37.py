"""Six bounded repairs under the unchanged CAL-5D v1.3 / operation v1.4.

Only current propositions and authenticated object scope are coding features.
No case ID, department, filename meaning, reference label or score is read.
This is an exposed-development candidate, not independent validation.
"""
import re
from rule_support import RuleView
from rules_ec import EC_BASIS
from rules_se import S_BASIS
from rules_if import BASIS_I, _carrier_only, _disclosure_only, _verified_innovation_scope

RELEASE = 'v37.2-complete-scientific-and-price-objects-development'
DRUG = r'(?:参照药|参考药|对照药|药品|药物|新药|该药|本药)'
WRONG = r'办公|软件|信息系统|数据库|网络|设备|日志数据|文件命名|文件名'
FORM = r'(?:肌肉注射|静脉注射|皮下注射|口服|注射|外用|吸入)(?:制剂|剂型)'
NUMBER = r'[0-9一二两三四五六七八九十百]+'
DURATION = (rf'(?:给予|享有|赋予|延长|限定|规定)(?:最长|最短)?'
            rf'(?:不超过|不少于|至少|至多|为)?{NUMBER}(?:年|个月|月)(?:的)?(?:试验)?数据保护期|'
            rf'(?:试验)?数据保护期(?:最长|最短)?(?:为|是|不超过|不少于|至少|至多){NUMBER}(?:年|个月|月)')


def _emit(v, rule, dim, start, end, dependency=None):
    e = v.add(rule, dim, start, end,
              'attribute' if dim == 'I' and 'formulation' in rule else 'research_support' if dim == 'I' else None,
              {'Ec': EC_BASIS, 'S': S_BASIS, 'I': BASIS_I}[dim],
              dependency=dependency, safety_basis='other_safety' if dim == 'S' else None)
    e['rule_release'] = RELEASE


def _eligible(text):
    return not (_carrier_only(text) or _disclosure_only(text) or re.search(WRONG, text))


def _procurement_price(v):
    # Drug and price-taking predicate must be a single local grammar. A drug
    # in an earlier clause cannot lend its object to a later procurement.
    price = (r'(?:(?:集采|集中带量采购|集中采购)(?:中选|中标|成交)?|中选|中标|成交|采购)'
             r'(?:的)?(?:最高|最低|加权平均|平均)?(?:价格|价)')
    taking = r'(?:取|采用|按照|按|以)'
    patterns = [
        DRUG + r'(?:的(?:参照)?价格)?(?:应当|应|可|原则上|则)?(?P<taking>' + taking + r')'
        + r'(?:其|该药|本药)?(?:的)?' + price,
        r'(?P<taking>' + taking + r')' + DRUG + r'(?:的)?' + price,
    ]
    value_use = re.compile(
        r'(?:计算|测算|计价|结算|执行)|'
        r'(?:计算|测算|确定)(?:其|该药|本药|参照药|参考药|对照药)?(?:的)?(?:参照)?(?:价格|药价|参照值|取值)|'
        r'作为(?:参照价格|参照值|药品价格|药品报价)')
    for s in v.clauses():
        if not _eligible(s.group()):
            continue
        for pattern in patterns:
            for m in re.finditer(pattern, s.group()):
                suffix = s.group()[m.end():].strip()
                # 取/采用 governs a price object at a true clause ending.
                # 按/按照/以 is only a prepositional phrase until an actual
                # value-use predicate follows. Any unparsed tail, such as a
                # clause's layout/order, makes this bounded route abstain.
                if not (value_use.fullmatch(suffix)
                        or (not suffix and m.group('taking') in {'取', '采用'})):
                    continue
                _emit(v, 'V37_Ec_current_drug_procurement_price_selection', 'Ec',
                      s.start()+m.start(), s.end())


def _medication_error(v):
    # Bridge commas only from a medication-process time/setting phrase to an
    # explicit prevention predicate. Semicolons/periods stop the relation.
    process = re.compile(r'(?:在|当)?(?:药品|药物)(?:的)?'
                         r'(?:调配|配发|发放|给药|服用|使用|交接)[^。；;，,]{0,24}?'
                         r'(?:时|过程中|环节中)')
    error = r'(?:误|错)(?:选|用|服|吸)(?:[、及和或]?(?:误|错)(?:选|用|服|吸))*'
    # Inspect the whole error predicate, including its following object. The
    # inherited medication-process object may be omitted at a clause ending;
    # an overt object must itself be a drug, not money/data/etc after 误用.
    complete_target = (error + r'(?:(?:上述|相关|该|本)?(?:药品|药物))?'
                       r'(?:的?(?:风险|情况|问题|事件|行为))?(?=[。；;，,]|$)')
    medical_actor = r'(?:医务人员|医师|药师|护士|患者)'
    prevention = re.compile(r'(?:' + medical_actor + r')?(?:应当|必须|应|须|要)?(?:注意)?'
                            r'(?:避免|防止|预防|减少|防范)' + complete_target)
    # Intermediate control actions must continue the drug-use setting. An
    # arbitrary new subject (including an omitted error object) cannot cross
    # this bridge merely because the initial clause mentioned a medicine.
    control = re.compile(
        r'(?:' + medical_actor + r')?(?:应当|必须|应|须|要)?(?:互相|相互)?提醒|'
        r'(?:向|对)?(?:患者|病人)(?:做好|开展|进行)?用药教育|'
        + medical_actor + r'(?:应当|应|要)?(?:认真)?(?:核对|检查)(?:患者|病人|给药|用药|药品)[^。；;，,]{0,12}')
    for s in v.sentences():
        parts = list(re.finditer(r'[^，,]+', s.group()))
        for index, part in enumerate(parts):
            if not process.fullmatch(part.group().strip()) or not _eligible(part.group()):
                continue
            for target in parts[index+1:index+6]:
                text = target.group().strip()
                m = prevention.fullmatch(text)
                if m and _eligible(text):
                    _emit(v, 'V37_S_current_medication_process_error_prevention', 'S',
                          s.start()+part.start(), s.start()+target.end())
                    break
                if not control.fullmatch(text) or not _eligible(text):
                    break


def _formulation_change(v):
    # Both relative-product endpoints are explicit drug formulations; no
    # innovation adjective or positive approval decision is required.
    pattern = rf'(?P<before>{FORM})(?:改(?:为)?|变更为|转为)(?P<after>{FORM})'
    for s in v.sentences():
        for m in re.finditer(pattern, s.group()):
            if (m.group('before') != m.group('after') and _eligible(s.group())
                    and not re.match(r'名称|编码|文件', s.group()[m.end():])):
                _emit(v, 'V37_I_explicit_between_formulation_change', 'I',
                      s.start()+m.start(), s.start()+m.end())


def _trial_data_right(v):
    # An undisclosed/self-generated trial-data right is distinct from ordinary
    # confidentiality or a file-retention period. Bind its beneficiary,
    # protected object and quantified legal term in the same current sentence.
    proprietary = (r'(?:自行|自主)取得[^。；;，,]{0,20}未披露[^。；;，,]{0,12}试验数据|'
                   r'(?:专有|排他|独占)(?:的)?(?:药品)?试验数据')
    for s in v.sentences():
        x = s.group()
        obj = re.search(proprietary, x)
        if obj is None or not _eligible(x):
            continue
        beneficiary = list(re.finditer(DRUG, x[:obj.start()]))
        if not beneficiary:
            continue
        start = beneficiary[0].start()
        for term in re.finditer(DURATION, x):
            if (obj.end() <= term.start() and term.end()-start <= 300
                    and re.search(r'实施保护|受到保护|予以保护|给予|享有|赋予', x[obj.end():term.end()])):
                _emit(v, 'V37_I_proprietary_trial_data_quantified_right', 'I',
                      s.start()+start, s.start()+term.end())


def _explicit_trial_data_right(v):
    # A direct drug beneficiary plus data-protection term is already a right;
    # I3 does not require repeating the unpublished/self-generated condition
    # in every substantive grant or change-of-scope proposition.
    beneficiary = r'(?:创新药(?:物)?|改良型新药|新药|药品|药物)'
    term = (rf'(?:最长|最短)?(?:不超过|不少于|至少|至多)?{NUMBER}'
            r'(?:年|个月|月)(?:的)?(?:试验)?数据保护期')
    right_scope = r'(?:药品|药物)(?:试验)?数据保护(?:制度)?(?:的)?(?:适用|保护)?范围'
    patterns = [
        r'(?:给予|赋予)(?:符合条件的)?' + beneficiary + term,
        beneficiary + r'(?:享有|获得)' + term,
        beneficiary + rf'(?:的)?(?:试验)?数据保护期(?:最长|最短)?(?:为|是|不超过|不少于){NUMBER}(?:年|个月|月)',
        r'(?:扩大|扩展|缩小|调整)' + right_scope + r'(?:至|为|到)' + beneficiary,
        right_scope + r'(?:扩大|扩展|缩小|调整)(?:至|为|到)' + beneficiary,
    ]
    for s in v.clauses():
        for pattern in patterns:
            for m in re.finditer(pattern, s.group()):
                if (_eligible(s.group())
                        and not re.match(r'企业|公司|资料|数据|文件|目录', s.group()[m.end():])):
                    _emit(v, 'V371_I_current_explicit_drug_data_right', 'I',
                          s.start()+m.start(), s.start()+m.end())


def _remove_purpose_only_evidence(v):
    # Restrict this repair to an explicit purpose-preface/publication role.
    # Operative establishment/expansion/cancellation of a specific instrument
    # without that publication role is left for separate substantive review.
    # Remove the purpose route alone; independent rights/resources survive.
    for s in v.sentences():
        x = s.group()
        purpose = re.match(r'\s*(?:为|为了)(?:促进|支持|鼓励|推动|激励)(?:药品|药物|新药)(?:的)?创新', x)
        publication = re.search(r'现(?:予|将|予以)?(?:发布|印发)|予以发布|自发布之日起施行', x)
        if not (purpose and publication):
            continue
        a, b = v.raw_span(*s.span())
        # Do not destructively classify an unrecognized substantive measure
        # as a mere purpose. Recognized independent rights are emitted first.
        concrete = re.search(r'给予|赋予|享有|延长|终止|撤销|取消|扩大|缩小|调整|适用范围(?:至|为|包括)', x)
        independent = any(e['dimension'] == 'I' and e['rule'] != 'V27_I_data_protection_purpose'
                          and a <= e['start'] and e['end'] <= b for e in v.result['evidence'])
        if concrete and not independent:
            v.result.setdefault('review_flags', []).append({
                'rule': 'V371_I_unresolved_substantive_protection_measure', 'dimensions': ['I'],
                'action': 'legacy_evidence_preserved_pending_substantive_review',
                'reason': '存在具体保护措施谓词但独立关系未解析；不以发布角色删除可能的实体支持。'})
            continue
        v.drop(lambda e: e['dimension'] == 'I' and e['rule'] == 'V27_I_data_protection_purpose'
               and a <= e['start'] and e['end'] <= b,
               'V37_I_publication_purpose_not_substantive_support',
               '明确发布句的制定目的与数据保护制度名称不构成实体研发支持；独立保护范围、期限、条件或资源措施证据保留。')


def _authenticated_innovation_object(v, scope):
    # Existing certificate checks bind the object to this unit/component.
    # Additionally reproduce the actual target and the quoted source bytes.
    from source_context_adapter_v34 import authenticate_target, authenticate_context
    from source_context_adapter_v33 import candidate
    authenticate_target(v.record)
    paragraphs = [p for p in candidate(v.record['candidate_file']).get('paragraphs', [])
                  if p.get('id') == scope['locator']['paragraph_id']]
    if len(paragraphs) != 1 or scope['text'] not in paragraphs[0].get('text', ''):
        raise ValueError('v37 innovation-object scope does not match actual candidate paragraph')
    current = {'text': scope['text'], 'source_path': v.record.get('unit_source') or v.record.get('source'),
               'source_sha256': scope['source_sha256'], 'candidate_path': v.record['candidate_file'],
               'candidate_sha256': v.record['candidate_sha256'],
               'paragraph_id': scope['locator']['paragraph_id'],
               'source_lines': scope['locator']['source_lines'], 'pages': paragraphs[0].get('pages', [])}
    return authenticate_context(current)['authentication_v34']


def _professional_guidance(v):
    # The actor is an actual review institution. An applicant's request for
    # a meeting is not that institution's staffing/guidance proposition.
    actor = r'(?:药审中心|药品审评中心|审评机构|审评部门)'
    staffing = re.compile(actor + r'(?:(?:根据|依据|针对)[^。；;，,]{0,45}(?:问题|资料|阶段|需求))?'
                          r'(?:应当|可以|不再|不予|应|可|将|负责)?(?:安排|组织|配置)'
                          r'(?:相关|相应|专门|专业|有关)?(?:审评人员|审评专家|审评团队)'
                          r'(?:进行|开展)?(?:沟通交流|沟通|咨询|指导)')
    basis = r'(?:基于|依据|根据)(?:已有|现有)?(?:研究|试验)资料'
    # The complete object of the advice must be the scientific plan itself
    # or a stated scientific constituent. A plan name cannot lend scientific
    # meaning to a deadline, upload format or another administrative head.
    plan = r'(?:下一步|后续)?(?:研究|研发|试验)(?:方案|设计)'
    constituent = (r'(?:研究|试验)?(?:主要|次要)?终点(?:设置|选择)?|'
                   r'剂量(?:选择|方案|设计)|给药方案|对照(?:选择|设计)|'
                   r'研究人群|受试人群|样本量(?:设计|估计)?|'
                   r'统计分析(?:方法|方案)|风险管理(?:措施|计划)')
    scientific_object = (plan + r'(?:的?(?:' + constituent + r'|科学性|合理性|可行性))?|'
                         r'(?:下一步|后续)?(?:研究|试验)(?:主要|次要)?终点(?:设置|选择)?')
    advice = (r'对(?:' + scientific_object + r')(?:应当|应|可以|可)?'
              r'提出(?:意见(?:或者|或|和|及)建议|意见|建议)')
    continuing_actor = actor + r'|(?:相关)?(?:审评人员|审评专家|审评团队)'
    continuation = re.compile(r'(?:同时|并且|并|且|随后)?(?:' + continuing_actor + r')?'
                              r'(?:' + basis + r'(?:' + advice + r')?|' + advice + r')')
    for s in v.sentences():
        parts = list(re.finditer(r'[^，,]+', s.group()))
        for index, part in enumerate(parts):
            m = staffing.fullmatch(part.group().strip())
            if m is None or not _eligible(part.group()):
                continue
            basis_seen = bool(re.search(basis, part.group()))
            for step in range(index, min(index+6, len(parts))):
                current = parts[step]
                text = current.group().strip()
                if step > index and (not continuation.fullmatch(text) or not _eligible(text)):
                    break
                basis_seen = basis_seen or bool(re.search(basis, text))
                scientific_advice = re.search(advice, text)
                if not (basis_seen and scientific_advice):
                    continue
                scope = _verified_innovation_scope(v)
                if scope is None:
                    break
                authenticated = _authenticated_innovation_object(v, scope)
                dependency = {'kind': 'authenticated_innovation_object_and_current_scientific_guidance',
                              'innovation_object_scope': scope, 'source_authentication': authenticated,
                              'usage': 'Scope resolves the drug only. Each cross-comma step has the same explicit institution/reviewer or an accepted subjectless continuation; any other subject/claim breaks this branch.'}
                _emit(v, 'V37_I_actual_professional_scientific_guidance', 'I',
                      s.start()+part.start(), s.start()+current.start()
                      + len(current.group())-len(current.group().lstrip())+scientific_advice.end(), dependency)
                break


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    v = RuleView(record, result)
    _explicit_trial_data_right(v)
    _remove_purpose_only_evidence(v)
    _procurement_price(v)
    _medication_error(v)
    _formulation_change(v)
    _trial_data_right(v)
    _professional_guidance(v)
    return result
