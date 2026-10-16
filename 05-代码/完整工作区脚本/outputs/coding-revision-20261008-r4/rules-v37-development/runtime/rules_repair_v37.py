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

RELEASE = 'v37-six-bounded-proposition-repairs-development'
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
    # A procurement identity is not enough: an explicit price-taking predicate
    # must govern a compound procurement-price noun in the current sentence.
    price = (r'(?:(?:集采|集中带量采购|集中采购)(?:中选|中标|成交)?|中选|中标|成交|采购)'
             r'(?:的)?(?:最高|最低|加权平均|平均)?(?:价格|价)')
    pattern = (DRUG + r'[^。；;]{0,80}?(?:取|采用|按照|按|以)'
               r'[^。；;，,]{0,18}?' + price)
    for s in v.sentences():
        for m in re.finditer(pattern, s.group()):
            if _eligible(s.group()):
                _emit(v, 'V37_Ec_current_drug_procurement_price_selection', 'Ec',
                      s.start()+m.start(), s.start()+m.end())


def _medication_error(v):
    # Bridge commas only from a medication-process time/setting phrase to an
    # explicit prevention predicate. Semicolons/periods stop the relation.
    process = (r'(?:在|当)?(?:药品|药物)(?:的)?'
               r'(?:调配|配发|发放|给药|服用|使用|交接)[^。；;，,]{0,24}?'
               r'(?:时|过程中|环节中)[,，]')
    error = r'(?:误|错)(?:选|用|服|吸)(?:[、及和或]?(?:误|错)(?:选|用|服|吸))*'
    pattern = process + r'[^。；;]{0,100}?(?:避免|防止|预防|减少|防范)[^。；;，,]{0,12}?' + error
    for s in v.sentences():
        for m in re.finditer(pattern, s.group()):
            if _eligible(m.group()):
                _emit(v, 'V37_S_current_medication_process_error_prevention', 'S',
                      s.start()+m.start(), s.start()+m.end())


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
    pattern = (r'(?:^|[,，])(?P<relation>' + actor + r'[^。；;，,]{0,55}?'
               r'(?:安排|组织|配置)[^。；;，,]{0,12}(?:审评人员|审评专家|审评团队)'
               r'[^。；;]{0,100}?(?:基于|依据|根据)(?:已有|现有)?(?:研究|试验)资料'
               r'[^。；;]{0,45}?对(?:下一步|后续)(?:研究|研发|试验)(?:方案|设计)'
               r'[^。；;，,]{0,12}?提出(?:意见(?:或者|或|和|及)建议|意见|建议))')
    for s in v.sentences():
        for m in re.finditer(pattern, s.group()):
            relation = m.group('relation')
            if not _eligible(relation):
                continue
            scope = _verified_innovation_scope(v)
            if scope is None:
                continue
            authenticated = _authenticated_innovation_object(v, scope)
            dependency = {'kind': 'authenticated_innovation_object_and_current_scientific_guidance',
                          'innovation_object_scope': scope, 'source_authentication': authenticated,
                          'usage': 'Scope resolves the innovation-qualified drug only; current institutional staffing, study basis and scientific advice supply the support proposition.'}
            _emit(v, 'V37_I_actual_professional_scientific_guidance', 'I',
                  s.start()+m.start('relation'), s.start()+m.end('relation'), dependency)


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    v = RuleView(record, result)
    _remove_purpose_only_evidence(v)
    _procurement_price(v)
    _medication_error(v)
    _formulation_change(v)
    _trial_data_right(v)
    _professional_guidance(v)
    return result
