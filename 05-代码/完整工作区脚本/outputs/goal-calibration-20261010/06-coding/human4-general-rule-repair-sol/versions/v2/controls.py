"""Constructed semantic controls only; never open or infer a real study packet."""
import ast
import copy
import hashlib
import json
import os
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if p.name == 'goal-calibration-20261010')
BASE = ROOT / '05-validation/rule-request-routing-repair-sol'
OUTPUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else 'control-results-attempt01.json')
if OUTPUT.parent != HERE or OUTPUT.exists():
    raise ValueError('each constructed attempt requires a distinct new output')
CODE_NAMES = ('source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions')
allowed = {HERE / (n + '.py') for n in CODE_NAMES} | {BASE / (n + '.py') for n in CODE_NAMES}
allowed |= {HERE / 'controls.py', HERE / 'rule_driver.py', BASE / 'rule_driver.py'}
stdlib = Path(os.__file__).resolve().parent
reads = []
loaded_code = []


def audit(event, args):
    if event != 'open' or not args or isinstance(args[0], int):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    mode = args[1] if len(args) > 1 else None
    flags = args[2] if len(args) > 2 else 0
    writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or bool(
        flags and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
    if writing:
        if path.parent != HERE:
            raise PermissionError('write outside new isolated candidate directory')
    else:
        if path not in allowed and stdlib not in path.parents:
            raise PermissionError('constructed controls cannot read study materials: ' + str(path))
        reads.append(str(path))


sys.addaudithook(audit)


def load(name, path):
    module = types.ModuleType(name)
    module.__file__, module.__package__ = str(path), ''
    sys.modules[name] = module
    payload = path.read_bytes()
    loaded_code.append({'module':name,'path':str(path),
                        'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)})
    exec(compile(payload, str(path), 'exec'), module.__dict__)
    return module


mods = {n: load(n, HERE / (n + '.py')) for n in CODE_NAMES}
old_relations = load('baseline_relations', BASE / 'relations.py')
old_dimensions = load('baseline_dimensions', BASE / 'dimensions.py')
DIMS = mods['dimensions'].DIMENSIONS
cases, checks = [], []


def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def check(name, passed, details=None):
    checks.append({'name': name, 'passed': bool(passed), 'details': details})


def ctx(cid, kind, text, ref, structure=None):
    return {'context_id': cid, 'kind': kind, 'text': text,
            'source_document': ref['source_resource_id'], 'source_ref': copy.deepcopy(ref),
            'structure': structure or {}}


def bundle(current, raw=None, structural=False):
    source_sha = sha(raw) if raw is not None else sha('constructed-source:' + current)
    ref = {'sha256': source_sha, 'source_resource_id': 'CONSTRUCTED-SOURCE', 'locator': {}}
    b = {'common_source_bundle_version': 'constructed-not-study',
         'source_record': {'id': 'CONSTRUCTED', 'text': current, 'source_ref': ref, 'contexts': []},
         'source_documents': [], 'explicit_or_primary_source_resources': [],
         'preserved_historical_neutral_source_supplements': [], 'source_full_text_resources': [],
         'source_asset_locations': [], 'source_locator_bases': {}, 'source_reference_index': [],
         'source_provenance_addenda': []}
    if structural:
        b['source_record']['contexts'] = [ctx('CONSTRUCTED-SEED', 'source_paragraph', current, ref),
            ctx('CONSTRUCTED-RELATION', 'structural_relation', '', ref,
                {'related_context_ids': ['CONSTRUCTED-SEED']})]
    if raw is not None:
        b['source_full_text_resources'] = [{
            'kind': 'verbatim_UTF8_snapshot_text', 'source_resource_id': 'CONSTRUCTED-LITERAL',
            'source_sha256': source_sha, 'source_version_id': 'constructed-only', 'text': raw,
            'text_utf8_sha256': sha(raw), 'text_unicode_code_points': len(raw),
            'text_utf8_bytes': len(raw.encode()),
            'locator': {'unicode_code_point_interval_half_open': [0, len(raw)],
                        'utf8_byte_interval_half_open': [0, len(raw.encode())]}}]
    return b


def fullsource_page(b, text, same_source=True):
    """Normal PDF FULLSOURCE+paragraph shape, not false UTF8-snapshot identity."""
    source_sha = b['source_record']['source_ref']['sha256'] if same_source else sha('other-source')
    b['source_full_text_resources'] = [{
        'source_resource_id': 'SOURCE-' + source_sha, 'source_sha256': source_sha,
        'source_pdf_sha256': source_sha, 'document_title': '构造目录说明', 'document_year': '2026',
        'paragraphs': [{'source_paragraph_id': 'CONSTRUCTED-PAGE', 'source_sha256': source_sha,
                        'text': text, 'text_sha256': sha(text),
                        'source_locator': {'physical_page': 9, 'extraction_provenance': 'constructed only'}}]}]
    return b


def control_receipts(b, view):
    inventory = {r['resource_id']: r for r in mods['source_packet'].source_inventory(b)}
    receipts = []
    for event in view.source_view_events:
        resource = inventory.get(event['resource_id'])
        bound = bool(resource and resource['source_sha256'] == event['source_sha256']
                     and resource['available_views'].get(event['view']) == event['view_sha256'])
        check('receipt-bound:' + str(len(cases)) + ':' + str(len(receipts)), bound)
        receipts.append({'receipt_id': 'CONSTRUCTED-READ-' + str(len(receipts)),
                         **copy.deepcopy(event), 'verified_against_constructed_inventory': bound,
                         'constructed_only': True, 'pixel_interpretation': False})
    by_key = {(r['resource_id'], r['view']): r for r in receipts}
    uses = []
    for trace in view.source_relation_traces:
        for use in trace.get('used_source_views', []):
            receipt = by_key.get((use['resource_id'], use['view']))
            check('use-has-read:' + str(len(cases)) + ':' + str(len(uses)), receipt is not None)
            uses.append({**copy.deepcopy(use), 'receipt_id': receipt['receipt_id'] if receipt else None})
    return receipts, uses


def run(name, b, expected, note, expected_kinds=None, expected_request=None):
    semantic = mods['source_packet'].semantic_unit(b)
    old_view = old_relations.RelationView(copy.deepcopy(semantic))
    new_view = mods['relations'].RelationView(copy.deepcopy(semantic))
    before = old_dimensions.judge(old_view)
    after = mods['dimensions'].judge(new_view)
    mods['evidence'].validate_decisions(semantic, before)
    mods['evidence'].validate_decisions(semantic, after)
    values = {d: after[d]['value'] for d in DIMS}
    check(name + ':expected', all(values[d] == value for d, value in expected.items()),
          {'expected_dimensions': expected, 'actual': values})
    if expected_kinds is not None:
        check(name + ':relations', {r['kind'] for r in new_view.relations} == set(expected_kinds))
    if expected_request is not None:
        check(name + ':requests', {r['path'] for r in new_view.material_requests} == set(expected_request))
    # Execute only the original driver's unchanged dependency guard on these
    # artificial mappings. The real driver main/cohort loop is never imported.
    if new_view.material_requests:
        exec(guard_code, {'view': new_view, 'decisions': after, 'stops': ['required_reference_unresolved']})
        check(name + ':guard-accepted-concrete-request-propagation', True)
    receipts, uses = control_receipts(b, new_view)
    cases.append({'name': name, 'hand_calculated_expectation': expected, 'prior_reason': note,
                  'constructed_bundle': b, 'baseline_values': {d: before[d]['value'] for d in DIMS},
                  'candidate_values': values, 'candidate_decisions': after,
                  'candidate_relations': new_view.traces(), 'requests': new_view.material_requests,
                  'source_consumer_read_receipts': receipts, 'source_use_receipts': uses,
                  'constructed_only': True, 'real_cohort_inference': False})


old_driver = (BASE / 'rule_driver.py').read_text()
new_driver = (HERE / 'rule_driver.py').read_text()
def guard_text(text):
    a = text.index('            if stops:\n')
    b = text.index('            prediction.update(labels=', a)
    return text[a:b]
check('dependency_guard_exact_bytes_retained', guard_text(old_driver) == guard_text(new_driver))
guard_code = compile('\n'.join(line[12:] for line in guard_text(new_driver).splitlines()),
                     str(HERE / 'rule_driver.py') + ':constructed-guard', 'exec')
for protected in ["raise ValueError('first output exists; use a distinct authorized round, never overwrite')",
                  "if scope.get('max_actual_cohort_inference_runs')!=1:",
                  "if target.name=='reference.jsonl' or '/04-calibration/' in str(target):raise PermissionError('reference/calibration prohibited')",
                  "if target not in allowed and out not in target.parents and stdlib not in target.parents:raise PermissionError('unapproved read '+str(target))"]:
    check('retained-guard:' + sha(protected)[:12], protected in new_driver)
for name in ['source_packet.py', 'source_receipts.py', 'evidence.py', 'interface_common.py']:
    if name != 'interface_common.py':
        check('unchanged-module:' + name, (BASE/name).read_bytes() == (HERE/name).read_bytes())
check('development-only-driver', "scope.get('execution_purpose') != 'development'" in new_driver)

all_zero = {d: 0 for d in DIMS}
value_current = '药物临床试验期间，与现有治疗手段相比有足够证据表明具有明显临床优势的创新药，申请人可以申请适用重点治疗药物程序。'
def value_source(safety=True):
    branch = '（2）与现有治疗手段相比，该药物具有显著的安全性优势。\n' if safety else ''
    return ('重点治疗药物审评工作程序（试行）\n一、适用范围和适用条件\n（一）适用范围\n'
            + value_current + '\n（二）适用条件\n药物临床试验期间，申请适用重点治疗药物程序的，应当同时满足以下条件：\n'
            '1.该药物用于防治目标疾病。\n2.该药物具有明显临床优势，即在重要临床终点显著改善。具体包括以下任一情形：\n'
            '（1）该药物显著提高疗效。\n' + branch + '二、工作程序\n申请人提交文件。\n')
run('operative-value-definition-with-safety-branch', bundle(value_current, value_source(), True),
    {'S': 1}, '操作性申请条件明确临床优势；同版完整定义含具体药物安全优势分支。', ['cited_standard'], [])
run('operative-value-definition-complete-without-safety', bundle(value_current, value_source(False), True),
    {'S': 0}, '完整定义未含安全分支，不由临床优势自动补S。', ['cited_standard'], [])
run('operative-value-definition-missing-full-group', bundle(value_current, structural=True),
    {'S': None}, '当前确指条件缺少完整同版定义，安全内容未知而不是0。', [], ['cited_standard'])
run('value-programme-name-alone', bundle('重点治疗药物程序。', value_source(), False),
    all_zero, '只有名称，不实际适用临床优势标准。', [], [])
unrelated_value = '甲药物具有明显临床优势。另一药物的申请人可以申请适用重点治疗药物程序。'
run('unrelated-product-criterion-does-not-govern-application', bundle(unrelated_value, value_source()+unrelated_value, True),
    {'S': 0}, '不同命题和另一药物不能借用甲药的临床优势条件。', [], [])
run('disease-severity-is-not-drug-safety', bundle('严重疾病是指显著缩短患者生命的疾病。'),
    {'S': 0}, '疾病本身的严重程度不等于药物安全。', [], [])

support_current = '药审机构对纳入重点药品支持程序的品种，与申请人开展沟通交流。'
def support_source(innovation=True, gap=True, priority=True, technical=True, pre_only=False, current=support_current):
    obj = '创新药和改良型新药' if innovation else '药品'
    need = '临床急需的短缺药品和' if gap else ''
    prioritization = '药审机构在审评中发现需要与申请人进行沟通交流的，可根据具体情况优先安排。\n' if priority else ''
    feedback = ('（三）技术资料。对纳入重点药品支持程序的药品上市许可申请，在审评过程中，申请人可以提出补充提交技术资料的沟通交流申请。\n'
                if technical and not pre_only else '')
    pre = ('申请人在申报前可以申请研究方案反馈和优先沟通交流。\n' if pre_only else '')
    return ('重点药品支持工作程序（试行）\n一、适用范围\n药品上市许可申请时，' + need + obj + '可以申请适用重点药品支持程序。\n'
            '二、适用条件\n应具有临床价值。\n三、工作程序\n（一）申报前沟通。\n' + pre
            + '（二）技术审评。药审机构对纳入重点药品支持程序的药品上市许可申请优先配置资源进行审评。\n'
            + prioritization + feedback + '四、工作要求\n' + current + '\n')
run('postadmission-tech-support-object-service-need-priority', bundle(support_current, support_source()),
    {'I': 1, 'F': 1, 'S': 0, 'E': 0, 'Ec': 0}, '创新/改良对象、真实技术资料反馈及优先沟通均明确，短缺需要直连这同一服务。', ['named_mechanism'], [])
run('postadmission-service-innovation-without-gap', bundle(support_current, support_source(gap=False)),
    {'I': 1, 'F': 0}, '真实创新技术支持成立，但没有患者治疗缺口。', ['named_mechanism'], [])
run('postadmission-service-gap-without-innovation', bundle(support_current, support_source(innovation=False)),
    {'I': 0, 'F': 1}, '按短缺需要优先配置服务可F；未明确创新/改良对象不可I。', ['named_mechanism'], [])
run('technical-feedback-support-without-current-service-priority', bundle(support_current, support_source(priority=False)),
    {'I': 1, 'F': 0}, '明确创新对象与纳入后技术资料反馈足够I3；没有本项服务优先配置，F为0。', ['named_mechanism'], [])
run('priority-technical-review-communication-without-material-feedback', bundle(support_current, support_source(technical=False)),
    {'I': 1, 'F': 1}, '同一技术审评章节的实际优先沟通机会可支持I3；缺口与本项优先服务相接足够F，不要求另外补技术资料段。', ['named_mechanism'], [])
run('gap-priority-communication-no-innovation-no-material-feedback', bundle(support_current, support_source(innovation=False, technical=False)),
    {'I': 0, 'F': 1}, '缺口与这项实际优先沟通相接可F；没有创新对象仍不可I，不要求技术资料反馈段。', ['named_mechanism'], [])
run('closed-source-no-priority-no-technical-feedback', bundle(support_current, support_source(priority=False, technical=False)),
    {'I': 0, 'F': 0}, '同版完整程序没有实质技术支持和本项优先机会，分别语义0，不无限补材。', [], [])
feedback_without_review_heading = support_source(priority=False).replace('（二）技术审评。', '（二）一般办理。')
run('explicit-postadmission-technical-feedback-without-review-heading', bundle(support_current, feedback_without_review_heading),
    {'I': 1, 'F': 0}, '技术资料反馈原句已明确同程序纳入后与审评阶段，I3不额外要求优先或固定章节名称。', ['named_mechanism'], [])
closed_without_mechanism = support_source(priority=False, technical=False).replace('（二）技术审评。', '（二）一般办理。')
run('closed-complete-source-without-substantive-service', bundle(support_current, closed_without_mechanism),
    {'I': 0, 'F': 0}, '完整同版原件没有实质服务或优先沟通；分别0，不请求想象中的技术章节。', [], [])
innovative_name_current = support_current.replace('重点药品支持程序', '创新药重点支持程序')
innovative_name_source = support_source(innovation=False).replace('重点药品支持', '创新药重点支持')
run('innovative-programme-name-does-not-establish-innovative-object', bundle(innovative_name_current, innovative_name_source),
    {'I': 0, 'F': 1}, '程序名称含创新药不能代替对象证据；缺口与真实优先技术沟通仍可独立F。', ['named_mechanism'], [])
excluded_object_source = support_source(innovation=False).replace('二、适用条件\n', '本程序不适用于创新药和改良型新药。\n二、适用条件\n')
run('excluded-innovative-object-is-not-current-support-object', bundle(support_current, excluded_object_source),
    {'I': 0, 'F': 1}, '完整适用范围明确排除创新对象时，当前服务不继承I3；按缺口优先配置独立F。', ['named_mechanism'], [])
run('preapplication-service-cannot-fill-postadmission', bundle(support_current, support_source(priority=False, pre_only=True)),
    {'I': 0, 'F': 0}, '申请前技术反馈不能替代当前纳入后服务。', [], [])
form_current = '药审机构对纳入重点药品支持程序的品种，安排电话、视频等沟通交流形式。'
run('communication-forms-alone', bundle(form_current, support_source(current=form_current)),
    {'I': 0, 'F': 0}, '当前只设置沟通形式，不能借同版别处实质服务。', [], [])
run('postadmission-current-service-missing-source', bundle(support_current),
    {'I': None, 'F': None}, '当前实质沟通缺少同版程序组件，具体支持与需要关系未知。', [], ['named_mechanism'])
name_current = '纳入重点药品支持程序的品种名称应归档。'
run('programme-status-paperwork-alone', bundle(name_current, support_source(current=name_current)),
    {'I': 0, 'F': 0}, '身份和归档本身不授予/实施该服务。', [], [])
other_service = '药审机构对纳入重点药品支持程序的品种归档。药审机构与另一药品的申请人开展沟通交流。'
run('other-product-communication-cannot-inherit-programme', bundle(other_service, support_source(current=other_service)),
    {'I': 0, 'F': 0}, '其他药品的沟通不承接当前程序对象和优先安排。', [], [])
purpose = '为鼓励创新药研发并关注临床急需的短缺药品，制定本工作程序。'
run('general-purpose-no-downstream-inheritance', bundle(purpose, support_source(current=purpose)),
    all_zero, '制定宗旨不展开后文对象或支持。', [], [])

price_current = '药品目录分支：价格协商→协商成功：纳入《构造药品目录》；协商失败：该药品不纳入。'
price_page = '对于申请调入构造药品目录的药品，进入价格协商环节。\n依据评估确定的协商价格开展现场价格协商，成功后记录结果。'
run('workflow-price-node-same-edition-assessed-price', fullsource_page(bundle(price_current), price_page),
    {'Ec': 1, 'S': 0, 'E': 0, 'I': 0, 'F': 0}, '当前操作分支与同版评估价和实际磋商直接相连；推荐目录没有自动支付后果。', ['price_arrangement'], [])
run('workflow-price-node-missing-price-content', bundle(price_current),
    {'Ec': None, 'S': 0, 'E': 0, 'I': 0, 'F': 0}, '节点实质内容需补同版定价解释，缺少时Ec未知。', [], ['price_arrangement'])
run('workflow-price-node-wrong-edition', fullsource_page(bundle(price_current), price_page, False),
    {'Ec': None}, '不同来源版本不能补定价内容。', [], ['price_arrangement'])
unrelated_page = '对于医院床位，进入价格协商环节。依据评估确定的协商价格开展现场价格协商。'
run('same-file-unrelated-price-object-cannot-transfer', fullsource_page(bundle(price_current), unrelated_page),
    {'Ec': None}, '同文件的另一对象不足；须同版药品对象及当前节点相接。', [], ['price_arrangement'])
run('price-stage-name-alone', bundle('药品目录申报包括价格协商阶段。'),
    {'Ec': 0}, '仅阶段名没有当前价格配置/内容关系。', [], [])
run('price-success-name-alone', bundle('药品价格协商成功。'),
    {'Ec': 0}, '只有成功状态，不据此虚构金额或配置内容。', [], [])
run('qualification-process-without-price-content', bundle('药品目录申报资格应审核材料完整性并签章。'),
    {'Ec': 0}, '纯资格手续没有价格、费用或支付内容。', [], [])
run('assessed-price-current-content', bundle('对于该药品，依据评估确定的协商价格开展现场价格协商。'),
    {'Ec': 1, 'F': 0}, '当前直接规定评估价与实际价格磋商；不要求金额。', [], [])
run('category-priority-basic-drugs-without-price', bundle('药品目录分甲、乙两类，优先选择基本药物。'),
    {'Ec': 0}, '甲乙分类与优先基本药物没有明示价格费用支付内容。', [], [])
run('independent-drug-risk-preserved', bundle('应报告该药物导致的肝损伤。'),
    {'S': 1}, '独立药物风险正向证据保持。', [], [])
run('independent-drug-effect-preserved', bundle('应比较该药物改善生存期的证据。'),
    {'E': 1}, '独立药物效果正向证据保持。', [], [])

# Closed route keeps only Ec uncertain and retains an independent S positive.
mixed = fullsource_page(bundle('应报告该药物导致的肝损伤。' + price_current), '')
run('price-dependency-preserves-independent-safety', mixed,
    {'S': 1, 'Ec': None, 'E': 0, 'I': 0, 'F': 0}, '缺定价来源只路由Ec；充分S证据不被null清空。', [], ['price_arrangement'])
route = mods['dimensions']._material_request_route({'path': 'price_arrangement', 'reference': '价格协商', 'missing': '定价内容缺失'})
check('price-request-closed-Ec-consumer', route['dimensions'] == ['Ec'])
try:
    mods['dimensions']._material_request_route({'path': 'price_arrangement', 'reference': '价格协商', 'missing': '定价内容缺失', 'dimensions': ['F']})
except mods['dimensions'].MaterialRequestRoutingError:
    check('incompatible-price-request-is-technical-error', True)
else:
    check('incompatible-price-request-is-technical-error', False)
malformed = bundle(support_current, support_source())
malformed['source_full_text_resources'][0]['locator']['unicode_code_point_interval_half_open'][1] += 1
try:
    mods['relations'].RelationView(mods['source_packet'].semantic_unit(malformed))
except mods['relations'].SourceDependencyStop:
    check('malformed-delivered-source-is-technical-error-not-zero-or-null', True)
else:
    check('malformed-delivered-source-is-technical-error-not-zero-or-null', False)

result = {'status': 'passed' if all(r['passed'] for r in checks) else 'failed',
          'constructed_case_N': len(cases), 'check_N': len(checks), 'passed_check_N': sum(c['passed'] for c in checks),
          'actual_cohort_inference_runs': 0, 'formal_validation_complete': False,
          'calibration_labels_already_disclosed': True, 'blind_validation': False,
          'new_candidate_more_accurate_than_old_claimed': False,
          'code_only_file_audit_allowlist': sorted(str(p) for p in allowed),
          'code_bindings_at_control_import': loaded_code,
          'control_script_binding': {'path':str(HERE/'controls.py'),
              'sha256':hashlib.sha256((HERE/'controls.py').read_bytes()).hexdigest(),
              'bytes':(HERE/'controls.py').stat().st_size},
          'actual_read_paths': sorted(set(reads)), 'checks': checks, 'cases': cases}
with OUTPUT.open('x') as stream:
    stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['status','constructed_case_N','check_N','passed_check_N','actual_cohort_inference_runs']}, ensure_ascii=False))
for c in checks:
    if not c['passed']:
        print(json.dumps(c, ensure_ascii=False))
