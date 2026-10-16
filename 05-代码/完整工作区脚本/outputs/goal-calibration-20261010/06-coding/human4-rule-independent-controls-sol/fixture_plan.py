"""Independent toy source and prior expectation builder; no candidate imports."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIMS = ('S', 'E', 'Ec', 'I', 'F')
ZERO = {d: 0 for d in DIMS}


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode('utf8')).hexdigest()


def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def save(path, value):
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def ctx(cid, kind, text, ref, structure=None):
    return {'context_id': cid, 'kind': kind, 'text': text,
            'source_document': ref['source_resource_id'], 'source_ref': copy.deepcopy(ref),
            'structure': structure or {}}


def bundle(cid, current, raw=None, seed=False):
    source = raw if raw is not None else 'TOY SOURCE for independent audit\n' + current
    ref = {'sha256': sha(source), 'source_resource_id': 'SOURCE-' + sha(source), 'locator': {}}
    b = {'common_source_bundle_version': 'independent-TOY-only-no-study',
         'source_record': {'id': 'TOY-' + cid, 'text': current, 'source_ref': ref, 'contexts': []},
         'source_documents': [], 'explicit_or_primary_source_resources': [],
         'preserved_historical_neutral_source_supplements': [], 'source_full_text_resources': [],
         'source_asset_locations': [], 'source_locator_bases': {}, 'source_reference_index': [],
         'source_provenance_addenda': []}
    if seed:
        b['source_record']['contexts'] = [ctx('TOY-SEED-' + cid, 'source_paragraph', current, ref),
            ctx('TOY-RELATION-' + cid, 'structural_relation', '', ref,
                {'related_context_ids': ['TOY-SEED-' + cid]})]
    if raw is not None:
        snapshot = HERE / ('toy-source-' + cid + '.utf8.txt')
        snapshot.write_bytes(raw.encode('utf8'))
        b['source_full_text_resources'] = [leaf(cid, raw, ref['sha256'], 0, 0, snapshot)]
    return b


def leaf(cid, text, source_sha, start, byte_start, snapshot):
    return {'kind': 'verbatim_UTF8_snapshot_text', 'source_resource_id': 'TOY-LITERAL-' + cid,
            'source_sha256': source_sha, 'source_version_id': 'TOY-edition-2026', 'text': text,
            'text_utf8_sha256': sha(text), 'text_unicode_code_points': len(text),
            'text_utf8_bytes': len(text.encode('utf8')),
            'locator': {'snapshot_absolute_path': str(snapshot),
                'unicode_code_point_interval_half_open': [start, start + len(text)],
                'utf8_byte_interval_half_open': [byte_start, byte_start + len(text.encode('utf8'))]}}


def fullsource(cid, current, page, wrong=False):
    b = bundle(cid, current)
    snapshot = HERE / ('toy-pdf-identity-' + cid + '.bin')
    raw = ('TOY source document identity, deliberately not a real PDF: ' + cid).encode('utf8')
    snapshot.write_bytes(raw)
    source_sha = sha(raw)
    b['source_record']['source_ref'].update(sha256=source_sha, source_resource_id='SOURCE-' + source_sha)
    payload_sha = sha('TOY other edition ' + cid) if wrong else source_sha
    payload = {'source_resource_id': 'SOURCE-' + payload_sha, 'source_sha256': payload_sha,
        'source_pdf_sha256': payload_sha, 'representation': 'TOY-original-same-source-page-text-payload',
        'physical_pages': [6], 'paragraphs': [{'source_paragraph_id': 'TOY-PAGE-' + cid,
            'source_sha256': payload_sha, 'text': page, 'text_sha256': sha(page),
            'source_locator': {'physical_page': 6, 'extraction_provenance': 'TOY text authored for audit'}}]}
    payload_path = HERE / ('toy-fullsource-' + cid + '.json')
    payload_path.write_text(cj(payload) + '\n', encoding='utf8')
    b['source_full_text_resources'] = [payload]
    if wrong:
        other_snapshot = HERE / ('toy-pdf-identity-other-' + cid + '.bin')
        other_snapshot.write_bytes(('TOY other edition ' + cid).encode('utf8'))
        doc_snapshot = other_snapshot
    else:
        doc_snapshot = snapshot
    b['source_documents'] = [{'source_resource_id': 'SOURCE-' + payload_sha, 'source_sha256': payload_sha,
        'snapshot': str(doc_snapshot), 'source_text_resource': {'relative_path': payload_path.name,
            'sha256': sha(payload_path.read_bytes()), 'bytes': payload_path.stat().st_size,
            'source_pdf_sha256': payload_sha}}]
    return b


VALUE = '与现有治疗手段相比有足够证据表明具有明显临床优势的创新药，申请人可以申请适用海舟重点治疗药物程序。'


def value_source(current=VALUE, safety=True, severity=False):
    definition = ('（2）与现有治疗手段相比，该药物具有显著的安全性优势。\n' if safety else '')
    if severity:
        definition += '（2）该药物用于防治严重危及生命的疾病。\n'
    return ('海舟重点治疗药物工作程序（试行）\n一、适用范围和适用条件\n（一）适用范围\n'
        + current + '\n（二）适用条件\n药物申请适用海舟重点治疗药物程序时，应同时满足以下条件：\n'
        '1.该药物用于防治目标疾病。\n2.该药物具有明显临床优势，即在主要临床终点显著改善。具体包括以下任一情形：\n'
        '（1）该药物显著提高疗效。\n' + definition + '二、工作程序\n申请人递交文件。\n')


SERVICE = '专家机构对纳入青岚药物支持程序的品种，与申请人开展沟通交流。'


def support_source(current=SERVICE, innovation=True, gap=True, priority=True, feedback=True,
                   pre=False, name='青岚药物支持程序'):
    obj = '创新药和改良型新药' if innovation else '普通药品'
    need = '临床急需的短缺药品和' if gap else ''
    before = ('申报前，申请人可申请研究方案反馈和优先沟通交流。\n' if pre else '')
    pri = ('专家机构在审评中发现需要与申请人开展沟通交流的，可根据具体情况优先安排。\n' if priority else '')
    tech = ('（三）技术资料。对纳入' + name + '的药品上市许可申请，在审评过程中，申请人可以提出补充提交技术资料的沟通交流申请。\n' if feedback else '')
    return (name.replace('程序', '工作程序') + '（试行）\n一、适用范围\n药品上市许可申请时，'
        + need + obj + '可以申请适用' + name + '。\n二、适用条件\n应具有临床价值。\n'
        '三、工作程序\n（一）申报前沟通。\n' + before + '（二）技术审评。专家机构对纳入'
        + name + '的药品上市许可申请配置资源进行审评。\n' + pri + tech
        + '四、工作要求\n' + current + '\n')


PRICE = '药品目录配置分支：价格协商→协商成功：纳入《山海药品目录》；协商失败：该药品不纳入。'
PAGE = '对于申请调入山海药品目录的药品，进入价格协商环节。依据评估确定的协商价格开展现场价格协商，成功后登记目录结果。'


def build():
    cases = []
    def add(cid, b, expected, reason, **extra):
        cases.append({'case_id': cid, 'source_bundle': b, 'expected': expected,
                      'prior_reason': reason, 'constructed_only': True, **extra})
    add('S01', bundle('S01', VALUE, value_source(), True), {'S': 1}, '同版完整临床优势定义含药物安全优势分支，当前实际将该优势作为申请条件。')
    negative = VALUE.replace('申请人可以', '申请人不可以')
    add('S02', bundle('S02', negative, value_source(negative), True), {'S': 1}, '申请限制仍以同一价值条件决定后果；S记录议题，证据必须保留不可以。', must_preserve='不可以')
    add('S03', bundle('S03', VALUE, value_source(safety=False, severity=True), True), {'S': 0}, '完整定义仅疗效与疾病严重，没有药物损害或安全分支。')
    goal = '为促进药物研发并保障用药安全，制定海舟重点治疗药物程序。'
    add('S04', bundle('S04', goal, value_source() + goal), ZERO, '制定宗旨不继承定义中的五维。')
    add('S05', bundle('S05', '海舟重点治疗药物程序。', value_source()), ZERO, '只有程序名称。')
    other = '甲药物具有明显临床优势。另一药物的申请人可以申请适用海舟重点治疗药物程序。'
    add('S06', bundle('S06', other, value_source() + other, True), {'S': 0}, '不同药物、不同命题不能把甲药优势接到另一药的申请。')
    wrong = bundle('S07', VALUE, value_source(), True)
    wrong['source_full_text_resources'][0]['source_sha256'] = sha('TOY other clinical edition')
    add('S07', wrong, {'S': None}, '确指同版条件定义仅有错版文本，材料未知。', expected_request='cited_standard')
    add('S08', bundle('S08', VALUE, value_source() + VALUE + '\n', True), {'S': None}, '完整来源有两个同文位置，当前锚点不唯一，不能选择其一。', expected_request='cited_standard')
    for cid, kw, expect, reason in [
        ('IF01', {}, {'I': 1, 'F': 1}, '创新对象、实际技术支持、当前连接和按短缺需要的本项优先均完整。'),
        ('IF02', {'priority': False}, {'I': 1, 'F': 0}, '技术资料反馈已构成创新技术支持；没有本项优先配置不能F。'),
        ('IF03', {'innovation': False, 'feedback': False}, {'I': 0, 'F': 1}, '只有缺口与实际技术审评沟通的优先配置可F；没有创新对象不I，F无须技术资料反馈。'),
        ('IF04', {'priority': False, 'feedback': False}, {'I': 0, 'F': 0}, '创新对象与一般沟通不能替代真实技术支持；缺口无本项优先不能F。'),
        ('IF05', {'innovation': False, 'gap': False, 'priority': False}, {'I': 0, 'F': 0}, '技术反馈服务没有创新/改良选择对象，也没有缺口优先关系。'),
        ('IF06', {'gap': False, 'feedback': False}, {'I': 1, 'F': 0}, '同一实际技术审评沟通的优先机会支持创新对象，F仍需独立缺口。'),
        ('IF07', {'priority': False, 'feedback': False, 'pre': True}, {'I': 0, 'F': 0}, '申报前研究反馈不能借给纳入后当前服务。')]:
        add(cid, bundle(cid, SERVICE, support_source(**kw)), expect, reason)
    form = '专家机构对纳入青岚药物支持程序的品种，安排电话、视频等沟通交流形式。'
    add('IF08', bundle('IF08', form, support_source(current=form)), {'I': 0, 'F': 0}, '当前只列形式，不能由同版别处的技术服务补I/F。')
    wrong = bundle('IF09', SERVICE, support_source())
    wrong['source_full_text_resources'][0]['source_sha256'] = sha('TOY other support edition')
    add('IF09', wrong, {'I': None, 'F': None}, '错版完整程序不能补当前服务。', expected_request='named_mechanism')
    add('IF10', bundle('IF10', SERVICE, support_source(name='澄川药物支持程序') + SERVICE), {'I': None, 'F': None}, '同源另一程序不能补当前程序，题名相似不是身份。', expected_request='named_mechanism')
    unrelated = '专家机构对纳入青岚药物支持程序的品种归档。专家机构与另一药品的申请人开展沟通交流。'
    add('IF11', bundle('IF11', unrelated, support_source(current=unrelated)), {'I': 0, 'F': 0}, '另一对象的服务没有当前同一程序直接连接。')
    paperwork = '专家机构对纳入青岚药物支持程序的药品，将申请表归档。'
    allthemes = support_source(current=paperwork).replace('应具有临床价值。', '应提交安全性、有效性、经济性、创新性和公平性材料。')
    add('IF12', bundle('IF12', paperwork, allthemes), ZERO, '整篇所有主题和创新题名均不能给当前归档操作赋维度。')
    renamed = SERVICE.replace('青岚', '槐序')
    add('IF13', bundle('IF13', renamed, support_source(current=renamed, name='槐序药物支持程序')), {'I': 1, 'F': 1}, '另一自造程序名称及全新source SHA仍按相同关系成立，不能白名单指定题名。')
    add('Ec01', fullsource('Ec01', PRICE, PAGE), {**ZERO, 'Ec': 1}, '完整同源FULLSOURCE对象—节点—评估价—实际磋商直连，目录结果没有医保支付。', require_identity=True, require_fullsource_use=True)
    add('Ec02', bundle('Ec02', PRICE), {**ZERO, 'Ec': None}, '实质纳入分支的价格节点缺必要定价定义，只有Ec未知。', expected_request='price_arrangement')
    add('Ec03', bundle('Ec03', '药品目录申报流程包括价格协商阶段。'), ZERO, '纯价格阶段无当前定价内容。')
    add('Ec04', bundle('Ec04', '药品价格协商成功，纳入山海药品目录。'), ZERO, '单独成功和目录结果没有定价内容或可补的明确操作节点。')
    add('Ec05', fullsource('Ec05', PRICE, PAGE, True), {**ZERO, 'Ec': None}, '同类错版FULLSOURCE不补当前定价。', expected_request='price_arrangement', require_identity=True)
    add('Ec06', fullsource('Ec06', PRICE, PAGE.replace('山海药品目录', '远汀药品目录')), {**ZERO, 'Ec': None}, '同文件另一目录的定价对象不能继承。', expected_request='price_arrangement', require_identity=True)
    beds = '对于医院床位，进入价格协商环节。依据评估确定的协商价格开展现场价格协商。'
    add('Ec07', fullsource('Ec07', PRICE, beds), {**ZERO, 'Ec': None}, '另一对象价格安排没有药品对象链。', expected_request='price_arrangement', require_identity=True)
    sprice = '药物应评价其安全性证据。' + PRICE
    add('Ec08', bundle('Ec08', sprice), {**ZERO, 'S': 1, 'Ec': None}, '独立当前S证据不被Ec材料请求清空。', expected_request='price_arrangement')
    contaminated = PAGE + '本说明同时概述药物安全性、有效性、创新药研发和短缺保障，但未把这些议题设为当前价格节点的条件。'
    add('Ec09', fullsource('Ec09', PRICE, contaminated), {**ZERO, 'Ec': 1}, '价格关系仅消费直接定价两句，不把全文其他主题复制给S/E/I/F。', require_identity=True, require_fullsource_use=True)
    add('Ec10', bundle('Ec10', '对于药品，依据评估确定的药品价格开展现场价格协商。'), {**ZERO, 'Ec': 1}, '当前自足的实际价格内容无需目录成功或金额。')
    malformed = bundle('ENG01', SERVICE, support_source())
    malformed['source_full_text_resources'][0]['locator']['unicode_code_point_interval_half_open'][1] += 1
    add('ENG01', malformed, {}, '已递交同源叶坐标长度矛盾，必须技术失败，不能普通0或null。', expected_error=True)
    overlap = bundle('ENG02', SERVICE, support_source())
    duplicate = copy.deepcopy(overlap['source_full_text_resources'][0])
    duplicate['source_resource_id'] += '-OVERLAP'
    overlap['source_full_text_resources'].append(duplicate)
    add('ENG02', overlap, {}, '两个同源文字叶重叠，必须技术失败并保留异常audit。', expected_error=True)
    split = bundle('ENG03', SERVICE, support_source())
    whole = split['source_full_text_resources'][0]
    raw = whole['text']; cut = raw.index('（二）技术审评') + 8
    snapshot = Path(whole['locator']['snapshot_absolute_path'])
    split['source_full_text_resources'] = [leaf('ENG03-A', raw[:cut], whole['source_sha256'], 0, 0, snapshot),
        leaf('ENG03-B', raw[cut:], whole['source_sha256'], cut, len(raw[:cut].encode('utf8')), snapshot)]
    add('ENG03', split, {'I': 1, 'F': 1}, '同版连续v14文字叶切开技术审评句也应实际执行与完整单叶一致。', require_literal_integrity=True)
    generic = bundle('ENG04', '药品应评价安全性、有效性、经济性、创新性和公平性。')
    add('ENG04', generic, {d: 1 for d in DIMS}, '旧v12原始当前正文形状按原概括评价门槛实际运行五维。')
    add('ENG05', bundle('ENG05', SERVICE), {'I': None, 'F': None}, '仅当前服务，缺完整同版程序，不伪造complete或programmeClosed。', expected_request='named_mechanism')
    forged = bundle('ENG06', SERVICE, support_source())
    forged['source_full_text_resources'][0]['text'] = forged['source_full_text_resources'][0]['text'].replace('普通', '虚假') + '伪同源后添文字。'
    fake = forged['source_full_text_resources'][0]
    fake['text_utf8_sha256'] = sha(fake['text']); fake['text_unicode_code_points'] = len(fake['text']); fake['text_utf8_bytes'] = len(fake['text'].encode('utf8'))
    fake['locator']['unicode_code_point_interval_half_open'][1] = len(fake['text'])
    fake['locator']['utf8_byte_interval_half_open'][1] = len(fake['text'].encode('utf8'))
    add('ENG06', forged, {}, '伪造同源叶局部自校验不够；与冻结完整snapshot不一致必须技术失败。', expected_error=True, integrity_before_semantics=True)
    files = [p for p in HERE.iterdir() if p.name.startswith('toy-') and p.is_file()]
    bindings = [{'path': str(p), 'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size} for p in sorted(files)]
    prior = {'prepared_without_candidate_imports': True, 'case_N': len(cases), 'cases': cases,
             'toy_material_bindings': bindings, 'study_record_body_read_N': 0,
             'real_77_800_4481_inference_runs': 0, 'purpose': 'finite independent AI engineering and semantic counterexamples; not human or formal validation'}
    save(HERE / 'prior-expectations-and-toy-source-chains.json', prior)
    print(json.dumps({'case_N': len(cases), 'prior_sha256': sha((HERE / 'prior-expectations-and-toy-source-chains.json').read_bytes())}))


if __name__ == '__main__':
    build()
