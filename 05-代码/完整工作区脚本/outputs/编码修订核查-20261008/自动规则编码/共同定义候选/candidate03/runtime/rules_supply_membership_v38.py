"""Bounded current drug membership in an institution's routine supply scope.

Unchanged CAL-5D v1.3 / operation v1.4 F1.  This adds only access evidence.
Substantive proposals/recommendations count; implementation is not required.
It consumes current text, never identifiers, departments, filenames, answers
or agreement/quality scores.  Unrecognized grammar is a coverage limitation,
not a negative definition of F.  This is exposed development.
"""
import re
from rule_support import RuleView

RELEASE = 'v38-institution-routine-drug-supply-membership-development'
BASIS = 'CAL-5D-20260926-v1.3 公平性保障获取；共用操作说明v1.4 F1实际药物配备/供应范围、纳入退出及条件'
RULE = 'V38_F_current_institution_routine_drug_supply_membership'
DRUG = r'(?:(?:上述|相关|该|本)?(?:药品|药物)|该药|本药|新药)'
INSTITUTION = r'(?:(?:本|该)?(?:医疗机构|医药机构|机构|医院)|本院|该院|院内)'
SCOPE = (INSTITUTION + r'(?:的)?(?:'
         r'(?:常规|临床)?用药(?:供应)?(?:目录|范围)|'
         r'(?:常规|临床)?(?:药品|药物)(?:配备|供应)(?:目录|范围)|'
         r'常规配备(?:目录|范围))')
OBJECT = r'(?:《' + SCOPE + r'》|' + SCOPE + r')'
MODAL = (r'(?:(?:应当|必须|不得|不予|不能|不可|不再|已经|现已|可以|拟予|建议|提议|计划|准备|应|须|要|可|已|现|将|拟)'
         r'(?:再)?)?')
ADVERB = r'(?:(?:及时|依法依规|依法|依规|立即|直接|予以))*'
MODE = MODAL + ADVERB
DECISION = r'(?:清退出|调出|移出|退出|纳入|调入|列入)'
EXIT = r'(?:清退|剔除|调出|移出|退出)'
NONOPERATIVE = re.compile(r'申请|申报|是否|能否|可否|如何|(?:研究|讨论|论证)(?:将|把)|仅记录|仅统计|仅归档|文件名|命名为')
NOUN_TAIL = re.compile(r'企业|公司|资料|材料|数据|信息|报告|档案|文件|申请|申报|价格|费用|名称|编码|目录')
SCOPE_TAIL = re.compile(r'的|后|之后|以后|前|之前|名称|编码|文件|档案|格式|价格|上限|申请|申报|工作|调整申请')


def _object_matching_view(v):
    # Restore only a complete known formulary name as a possible OBJECT.
    # All other document titles stay masked, so a title cannot supply a drug
    # subject or an operative predicate.  Restoration preserves raw offsets.
    chars = list(v.text)
    for m in re.finditer(r'《' + SCOPE + r'》', v.normalized):
        chars[m.start():m.end()] = v.normalized[m.start():m.end()]
    return ''.join(chars)


def _emit(v, clause, match, relation):
    drug = match.group('drug')
    scope = match.group('scope')
    e = v.add(RULE, 'F', clause.start()+match.start(), clause.start()+match.end(),
              'access', BASIS, dependency={
                  'kind': 'current_clause_actual_drug_and_institution_supply_scope',
                  'relation': relation, 'drug_object': drug,
                  'operative_predicate': match.group('decision'),
                  'actual_supply_scope': scope,
                  'scope_usage': 'Explicit destination/source of the substantive membership proposition, including proposals/recommendations; never merely a price/applicant/document premise.'})
    e['rule_release'] = RELEASE


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    v = RuleView(record, result)
    text = _object_matching_view(v)
    patterns = (
        ('drug_then_membership', re.compile(
            r'(?P<drug>' + DRUG + r')(?P<mode>' + MODE + r')'
            r'(?P<decision>' + DECISION + r')(?P<scope>' + OBJECT + r')')),
        ('drug_then_exit_from_scope', re.compile(
            r'(?P<drug>' + DRUG + r')(?P<mode>' + MODE + r')从'
            r'(?P<scope>' + OBJECT + r')(?:中|内)?'
            r'(?P<decision>' + EXIT + r')')),
        ('scope_then_exit_drug', re.compile(
            r'从(?P<scope>' + OBJECT + r')(?:中|内)?'
            r'(?P<decision>' + EXIT + r')'
            r'(?:(?:不符合|符合|未满足|满足|存在|出现)[^。；;，,]{0,30}的)?'
            r'(?P<drug>' + DRUG + r')')),
    )
    for clause in re.finditer(r'[^。；;，,]+', text):
        local = clause.group()
        for relation, pattern in patterns:
            for m in pattern.finditer(local):
                prefix = local[:m.start()]
                # Application routes and pure later-study/procedure roles do
                # not establish a substantive coverage proposition.  Proposed
                # or recommended membership itself is NOT excluded.  This is
                # a local guard, never whole-unit deletion of independent F.
                if NONOPERATIVE.search(prefix):
                    continue
                if NOUN_TAIL.match(local[m.end('drug'):]):
                    continue
                if SCOPE_TAIL.match(local[m.end():]):
                    continue
                if relation == 'scope_then_exit_drug':
                    operative = re.search(MODAL + ADVERB + r'$', prefix)
                    if not operative or not operative.group():
                        continue
                else:
                    # Normative/actual/proposal marker belongs to the predicate,
                    # or 将/把 explicitly introduces this drug as its object.
                    mode = m.group('mode')
                    marked = bool(re.match(MODAL, mode).group())
                    introduced = bool(re.search(r'(?:将|把)[^。；;，,]{0,45}$', prefix))
                    if not (marked or introduced):
                        continue
                _emit(v, clause, m, relation)
    return result
