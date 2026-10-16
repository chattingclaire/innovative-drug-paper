"""Record ROOT's actual source-based I/F review, preserving all original zeros."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'common-negative30-root'

REASONS = {
 'A-000055': ('药价比较与医保报销后的实际支付水平，未评价技术新颖性/实质改良或创新研发支持。', '当前是价格及实际支付水平，不等于患者能否负担；同段另句收入比重的可负担性不能倒借给此句。'),
 'A-000101': ('批准名称、新活性化合物的专利药品名称是处方命名要求，不是技术新颖性评价或创新资格决定关系。', '规定药品名称书写，未表达患者获取、按需保障或负担关系。'),
 'A-000409': ('医疗机构流程、门诊服务质量和人员配置不构成药物属性创新或明确创新研发支持。', '门急诊一般质量管理未表达所需药品获取差异/缺口与针对保障关系。'),
 'A-000458': ('评价证据质量分级与全行业共建共享是一般方法和组织安排，未连接创新/实质改良研发对象。', '面向评价证据使用者的共享安排，不是患者药品按需获取或负担关系。'),
 'A-000542': ('处方审核依据要求安全、有效、经济、依从性，当前未提出创新评价或实际创新支持。', '一般临床规范与依从性不自动等于患者获取差异或支付能力。'),
 'A-000002': ('宣传先进典型和推广质量管理经验，未表达药物技术创新或研发支持。', '宣传组织行动，未有患者药品获取/按需保障关系。'),
 'A-000004': ('静脉输液规范使用率及指标导向是临床使用质量指标，不是药品技术创新。', '规范使用率提升未表达药品获取机会差异或保障缺口。'),
 'A-000274': ('优化要素和运行机制、同段诊疗组织创新不等于药物产品技术创新。', '重大疾病和异地就医流向属于医疗资源配置背景，当前未建立所需药品获取差异及对应保障。'),
 'A-000366': ('制定临床综合评价指南及专家组织过程，没有当前药物创新内容或I3支持关系。', '指南制定过程没有当前患者获取/按需资源或负担关系，不从全文评价维度倒借。'),
 'A-000590': ('溶媒、剂量和给药速度适宜性审核未讨论创新/实质改良或相应资格。', '一般给药适宜性不表达患者药品机会差异；兄弟禁忌项的人群名称不继承F。'),
 'A-000005': ('适应症或功能主治重大变化作为医保申报范围，未明确创新/改良资格、具体局限—改变—改善关系。', '普通目录申报条件及时间范围，未由临床需要缺口决定按需保障机会。'),
 'A-000057': ('比值B、基金预算和支付标准降幅是支付计算条件，未承接创新分类或实质改良条件。', '基金支出与支付降幅不等于患者支付能力；当前并未确指治疗需要差别或保障缺口。'),
 'A-000370': ('谈判药品提交销量、预算、国际价格及赠药资料是支付内容信息，未设创新评价或研发支持。', '泛称慈善赠药资料没有明确患者负担能力/获取缺口及其资格关系，不能从慈善名称补写。'),
 'A-000711': ('报价与支付意愿决定竞价药品纳入目录，未有技术创新/改良条件。', '医保支付意愿是准入价格门槛，不是患者支付能力；无当前按需缺口保障关系。'),
 'A-000102': ('公布常用问答及创新药品目录文件名称，未实质设创新资格或研发支持。', '发布政策说明不展开各文件全部待遇，未有当前患者获取/负担关系。'),
 'A-000144': ('基金影响与药物经济学专家评估未提出创新评价或创新研发支持。', '基金影响分析未表达患者获取差异、缺口或支付能力；专家地域安排不继承F。'),
 'A-000434': ('当前实质纳入目录调整范围，可读完整成员与确指9/10条；这些内容涉及风险、临床价值和费用，没有创新/改良资格。', '完整成员及9/10条为风险收益、费用、临床价值的目录调整标准，未表达患者获取差异/保障缺口及按需资源关系。'),
 'A-000497': ('独家药品认定和最新数据口径不等于技术创新或实质创新分类。', '价格费用资料截至日期未表达患者负担能力或按需机会关系。'),
 'A-000731': ('仿制药同通用名上市自动入目录是医保待遇关系，未实质创新条件。', '一般医保名单扩展与付款安排不自动表达患者获取障碍/按需缺口。'),
 'A-000205': ('安全风险导致方案调整或暂停是风险控制，不由临床研发背景转成药物创新。', '安全暂停/终止本身不表达不合理机会差异或按需保障缺口。'),
 'A-000264': ('AE/ADR判定方法是安全证据方法，创新药指南范围不使一般方法成为I3。', '不良反应相关性判定没有患者药品获取/负担关系。'),
 'A-000492': ('既有肝肾研究用于老年入排标准和风险计划，是一般风险证据设计，不含实质改良或创新支持。', '老年人群试验参与与风险管理不等于患者所需药物获取差异或按需保障。'),
 'A-000517': ('将老年反馈纳入研发全过程未指明具体产品改变、明确局限及改善对应；一般患者反馈并非创新对象的专门支持。', '满足老年健康需要、治疗效果和风险是设计目的，没有所需药品获取差异、支付能力或保障缺口。'),
 'A-000665': ('稽查试验管理是否符合规范属一般质量合规，非药物属性创新或研发支持机会。', '试验合规稽查未表达患者药品获取/负担关系。'),
 'A-000132': ('研究阶段入排标准安排是一般研究设计，未形成创新/改良内容或支持关系。', '当前保持大部分入排标准；相邻对老年参与限制的说明是试验参与，未表达所需药品治疗获取/按需保障。'),
 'A-000250': ('患者访谈/调研了解需求是申请人一般研究安排，无明确创新/实质改良对象及可用专门服务；指南指导功能不等于I3。', '患者需求和疗效/不良反应相关负担没有明确支付能力、药品获取限制或按需保障关系。'),
 'A-000379': ('敏感性和偏倚分析属于一般证据方法，不是药物技术创新或明确创新研发支持。', '研究混杂和模型假设评估不含药品获取/负担关系。'),
 'A-000471': ('早期纳入老年群体以提供后续数据是研究设计；创新药背景不使其成为创新属性或专门服务。', '一般临床试验参与及代表性要求不自动等于F，当前没有所需药品获取差异或按需保障关系。'),
 'A-000487': ('观察性研究的定义没有药物技术创新或实质研发支持。', '暴露/治疗与结局因果研究定义未含药品获取/负担关系。')}


def binding(p):
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b),
            'sha256': hashlib.sha256(b).hexdigest()}


def save(p, d):
    with p.open('x') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    freeze_path = OUT / 'draw-freeze.json'
    draw = json.loads(freeze_path.read_text())
    for entry in draw['inputs'] + [draw['manual']]:
        assert binding(Path(entry['path'])) == entry
    rows, materials = [], []
    for selection in draw['selected_records']:
        path = Path(selection['material_path'])
        packet = json.loads(path.read_text())
        current = packet['source_record']['text']
        bid = selection['blind_id']
        assert packet['source_record']['id'] == selection['source_id']
        read = [i for i, c in enumerate(packet['source_record']['contexts'])
                if isinstance(c.get('text'), str) and
                not c['context_id'].startswith(('CTX-F2', 'CTX-SRCFULL'))]
        used = [0]
        if bid == 'A-000005':
            used += [3]
        if bid == 'A-000434':
            used += list(range(4, 12)) + [21]
        contexts = []
        for i in used:
            c = packet['source_record']['contexts'][i]
            assert i in read and isinstance(c.get('text'), str)
            contexts.append({'context_id': c['context_id'],
                             'json_pointer': f'/source_record/contexts/{i}/text',
                             'quote': c['text'], 'source_ref': c['source_ref']})
        materials.append(binding(path))
        for d, column in [('I', 0), ('F', 1)]:
            pending = bid == 'A-000647'
            reason = ('当前要求申报资料重点注意内容，末尾进入“一是突出药品特点”；同一完整答复第二点明确要求创新性、公平性等比较优势。需统一固定记录应作为承载完整内容要求的总领命题，还是仅引入第一点而不能继承后续兄弟项。不能从双方0直接认定正确，暂不硬判。'
                      if pending else REASONS[bid][column])
            rows.append({**selection, 'dimension': d, 'ai': 0, 'rule': 0,
                         'review_value': None if pending else 0,
                         'assessment': '总领与成员边界待核' if pending else '共同阴性有据',
                         'current_text': current, 'current_quote': current,
                         'current_location': {'file': str(path),
                                              'json_pointer': '/source_record/text',
                                              'source_ref': packet['source_record']['source_ref']},
                         'used_context_quotes': contexts,
                         'read_regular_text_context_ids': [packet['source_record']['contexts'][i]['context_id'] for i in read],
                         'additional_contexts_or_assets_not_read_or_used': [c['context_id'] for i, c in enumerate(packet['source_record']['contexts']) if i not in read],
                         'reason': reason, 'needs_human_review': pending,
                         'human_review_question': '这条承载整份申报内容要求，还是只引入第一点？按同一总领/成员规则核I/F，原值保留。' if pending else '',
                         'identity': 'ROOT nonblind AI source-based diagnostic review, not human reference'})
    assert len(rows) == 60 and len(REASONS) == 29
    assert sum(r['review_value'] is None for r in rows) == 2
    # Independent mechanical verification of all current and used context anchors.
    for row in rows:
        packet = json.loads(Path(row['material_path']).read_text())
        assert row['current_quote'] == packet['source_record']['text']
        for q in row['used_context_quotes']:
            index = int(q['json_pointer'].split('/')[3])
            assert q['quote'] == packet['source_record']['contexts'][index]['text']
    save(OUT / 'reviews.json', rows)
    save(OUT / 'validation-and-summary.json', {
        'frame_N': 739, 'records_reviewed': 30, 'dimension_slots_reviewed': 60,
        'review_value_counts': dict(Counter(str(r['review_value']) for r in rows)),
        'complete_current_and_used_context_quotes_match': True,
        'source_bindings': materials, 'frozen_draw': binding(freeze_path),
        'all_30_current_and_regular_text_contexts_actually_read': True,
        'all_available_fragments_originals_or_images_read': False,
        'confirmed_shared_positive_omissions_found': 0,
        'unresolved_record': 'A-000647 / RECODE25-00690',
        'zero_confirmed_misses_proves_population_recall': False,
        'scope': 'I/F diagnostic only; no S/E/Ec judgments or formal accuracy estimate',
        'original_values_or_frozen_production_changed': False})
    save(OUT / 'future-development-exposure-overlay.json', {
        'reason': 'these30 auxiliary sample records were inspected for general rule repair',
        'source_ids': sorted({r['source_id'] for r in rows}),
        'historical_domain_counts': dict(Counter(r['historical_domain'] for r in draw['selected_records'])),
        'old_frozen_primary_domains_retroactively_changed': False,
        'new_candidate_independence_must_use_accumulated_exposure': True})
    print(json.dumps({'actual_records_reviewed': 30, 'I_F_slots': 60,
                      'supported_zero_slots': 58, 'undetermined_slots': 2,
                      'population_recall_claimed': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
