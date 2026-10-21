"""Read-only finite AI development review; no statistical/model run or label edit."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / '最新机器与既有AC参照比较'
R3 = Path('/PROJECT_ROOT/outputs/coding-revision-20261007-r3')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def bd(p):
    return {'path': str(Path(p).resolve()), 'sha256': sha(p)}


def read(b):
    p = Path(b['path']); assert p.is_absolute() and sha(p) == b['sha256'], str(p)
    return json.loads(p.read_text())


def jl(b):
    p = Path(b['path']); assert sha(p) == b['sha256'], str(p)
    rr = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    out = {r['id']: r for r in rr}; assert len(rr) == len(out)
    return out


def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


# Current assistant's semantic work readings, never replacement labels.
WORK = [
    ('E', '00919', '参照分歧／明确条文援引', '倾向E=1；不据C=0记机器错',
     '符合《基本医疗保险用药管理暂行办法》第七条、第八条规定', ['并符合临床必需、安全有效、价格合理等基本条件。'],
     '共同必要语境第3条；E效果要求',
     '当前直接要求符合确指条文，完整第七条包含安全有效这一实质条件。不是把新上市或一般法律背景当疗效；A与C分歧在允许内容援引与否，现手册明确允许，不能自动以C作金标准。'),
    ('E', '01152', '需要专家边界／LLM泛化风险', '倾向E=0，指南规范与治疗推荐边界待确认',
     '临床使用是否符合用药指南规范', [], '共同E指南推荐与实质效果联系',
     '当前评价用药适宜性与规范符合性，未给特定药物效果、治疗推荐内容或效果证据。LLM把规范符合性等同治疗推荐。需明确“一般用药规范符合”是否足以纳入指南推荐路径，不能只因NHC κ低判错。'),
    ('E', '01616', '真实机器错候选：LLM背景身份过度传入', '倾向E=0',
     '对纳入《新型冠状病毒感染诊疗方案》的药品', ['该次续约可予不降价。'], '共同必要语境第1条；E仅文件名排除',
     '当前实质规定需求难预测及超预算后的不降价例外，诊疗方案归属用于界定对象，未展开药物治疗推荐或效果评价。LLM由归属身份推出效果关注；对象背景不应传入全部评价维度。'),
    ('E', '02158', '参照分歧／明确条文援引', '倾向E=1；不据C=0记机器错',
     '符合《基本医疗保险用药管理暂行办法》第九条、第十条规定的药品', ['(二)临床价值不确切,可以被更好替代的药品;', '(三)其他不符合安全性、有效性、经济性等条件的药品。'],
     '共同必要语境第3条；E否定及效果条件',
     '完整第九/十条确有临床价值、替代及有效性条件，当前直接按这些规定识别对象。标签表示对效果条件关注，不表示有效或已经调出；机器与A的1符合明示援引规则，C的0是参照解释分歧。'),
    ('E', '03101', '真实机器错：LLM效果证据漏检', '倾向E=1',
     '该研究的主要终点通过病历审查进行验证', ['评价其在中国女性中减少临床骨质疏松性骨折的有效性和安全性研究'],
     '共同E支持效果判断的证据；必要语境明确指代',
     '“该研究”确指药物减少骨折的效果研究，当前验证主要终点并检验分析稳健性，实质提供效果判断证据。使用语境是消解研究对象，并非复制效果结果；LLM仅因句子述方法而一概排除，遗漏了效果证据路径。'),
    ('E', '03157', '参照分歧／规则过度传入候选', '倾向E=0，方法证据界线需专家确认',
     '其未观测的协变量可能会导致接受治疗的概率完全不同', ['敏感性分析可以检测未观测的协变量对疗效估计偏倚的影响'],
     '共同E纯方法排除；必要语境不复制相邻命题',
     '当前例子说明治疗分配概率差异，后句才陈述疗效估计偏倚。C及规则将后句效果估计目的传入，A与LLM仅编码当前分配命题。与03101直接验证明确效果研究终点不同，本句是否已独立讨论效果证据仍需统一边界。'),
    ('E', '04368', '真实机器错：LLM诊断匹配过度推断', '倾向E=0',
     '处方用药与诊断是否相符', ['(一)西药及中成药处方,应当审核以下项目:'],
     '共同E效果命题与一般使用规范区分',
     '仅核处方与诊断匹配，没有效果、获益或药物治疗推荐内容。LLM把“用于相应疾病”推成防治效果适用性，等于由药物用途背景增补效果判断；A/C和规则的0较有依据。'),
    ('E', '04875', '需要专家边界／既有参照兼容', '不作E兼容定论',
     '综合考虑临床价值、患者合理的用药需求等因素', ['对于临床价值高、患者急需、替代性不高的品种,要及时纳入“双通道”管理。'],
     '共同E临床获益；一般临床价值与综合价值区分',
     '当前确实将药品临床价值作为分类标准，语境又提替代性；不能当纯文件名。争点是未细分的临床综合价值是否已经对应药物效果/获益，或还可能是综合属性和供应优先级。旧A/C要求更明确药效，LLM纳入；应由框架边界决定，不按κ选择。'),
    ('S', '00008', '真实机器错：规则疾病风险误作药物风险', '倾向S=0',
     '严重危及生命是指病情严重、不可治愈或者发展不可逆', ['用于防治严重危及生命或者严重影响生存质量的疾病'],
     '共同S药物／用药损害对象',
     '完整句和上位条件都是疾病严重程度及疾病后果，不是药物造成的损害。规则实际证据却声称“药物或药品质量问题与患者损害”并赋drug_harm，原文没有这条因果关系；这是对象/关系误识别。'),
    ('S', '00529', '需要专家边界：用药服务安全与一般质量', '倾向S=1；可能LLM过度收窄',
     '加强门诊手术、门诊化疗、门诊输液等门诊服务的质量安全管理', [],
     '共同S用药风险控制；质量边界',
     '当前明确点名化疗、输液的安全管理，可能已经是药物治疗风险控制，无需列出每种不良反应；但仍与一般门诊服务质量并列。须统一是否足够建立用药安全联系。它不是单纯药品工艺/质量可控案例，不能机械以新版排质量就把A/C=1视为不兼容。'),
    ('S', '00919', '参照分歧／明确条文援引', '倾向S=1；不据C=0记机器错',
     '符合《基本医疗保险用药管理暂行办法》第七条、第八条规定', ['并符合临床必需、安全有效、价格合理等基本条件。'],
     '共同必要语境第3条；S安全条件',
     '当前确指第七条并要求符合，安全是实际纳入条件，不是从药品监管身份推定。A/两机器为1与共同规则相容，C采用不传入引用条件的不同解释；这不是证明药物已安全。'),
    ('S', '01768', '需要专家边界：安全证据指导还是沟通事务', '不作S兼容定论；LLM有范围扩大风险',
     '如有未能阐明的个性化问题,可采用沟通交流的方式解决', ['本指导原则不能涵盖在安全性资料准备过程中遇到的所有情况。'],
     '共同S安全证据要求；必要语境对象与当前行为区分',
     '个性化问题确实指安全资料准备问题，不能说语境无关；但当前行为只给沟通渠道与指南完善，没有新增安全内容要求。LLM将资料准备指导视作安全关注，A/C及规则只认事务方式。须界定解答明确安全资料问题是否属于证据指导，而非只按背景标签。'),
    ('S', '02158', '参照分歧／明确条文援引', '倾向S=1；不据C=0记机器错',
     '符合《基本医疗保险用药管理暂行办法》第九条、第十条规定的药品', ['(三)综合考虑临床价值、不良反应、药物经济性等因素,经评估认为风险大于收益的药品;', '(三)其他不符合安全性、有效性、经济性等条件的药品。'],
     '共同必要语境第3条；S风险及否定条件',
     '给定完整条文含不良反应、风险收益及安全性条件，直接符合关系允许传入这些实质要求。C仅看当前短句未独立风险评价是不同操作范围；不能据其0反判两机器错。'),
    ('S', '03950', '真实机器错：LLM伦理保护泛化为药物安全', '倾向S=0',
     '审查针对未成年人的知情同意信息', ['审查对试验参与者的权益和安全保护是否充分'],
     '共同S药物损害；必要语境不传播父段全部维度',
     '当前审查同意能力、认知成熟度及伦理法规，父句安全保护为宽泛目的。材料虽属药物试验，仍未在本句建立药物损害、用药风险或安全证据联系。LLM由父句泛安全目的和试验身份继承S，属于过度传播。'),
    ('S', '04346', '参照分歧：具体风险资料要求', '倾向S=1',
     '用药史、过敏史等电子病历信息', ['药师发现严重不合理用药或者用药错误时,应当拒绝调配'],
     '共同S风险识别及相关证据',
     '当前明确要求处方审核获得用药和过敏史，给定前段又规定发现严重不合理用药／用药错误的控制动作。依据是具体风险资料与处方审查用途，不是信息系统名称。C把一切病史信息仅当数据，A和两机器按风险识别纳入；新旧S都允许风险证据，主要是参照解释分歧。'),
    ('Ec', '00637', '真实机器错：规则确认字段误作支付实质要求', '倾向Ec=0',
     '通过目录调整模块确认协议信息(药品名称、主规格、支付标准、支付范围及其他附加条款等)', [],
     '共同Ec既有标准／范围作为流程对象排除',
     '当前只确认既有协议字段并签署，前面的价格测算是另一个步骤，不能复制给当前“六是”。规则将字段列表直接标为payment_responsibility，但未识别实质价格、支付责任或标准改变；其余三方0较有依据。'),
    ('Ec', '00919', '参照分歧／明确条文援引', '倾向Ec=1；不据C=0记机器错',
     '符合《基本医疗保险用药管理暂行办法》第七条、第八条规定', ['并符合临床必需、安全有效、价格合理等基本条件。'],
     '共同必要语境第3条；Ec定性价格条件',
     '当前直接要求符合第七条，其中价格合理是实际价格水平条件。不是由普通医保申报资格名称补出经济内容；定性价格要求无须金额。C不传入引文条件，与A和两机器形成参照解释差异。'),
    ('Ec', '01575', '真实机器错：规则明确调价漏检', '倾向Ec=1',
     '支付标准的下调比例增加 4 个百分点', ['支付标准的下调比例同时与基金年均实际支出挂钩'],
     '共同Ec支付标准／基金预算资源',
     '当前明确把基金支出区间与支付标准下调幅度联系，远超流程名称或字段确认。A/C和LLM均识别，规则未留下任何Ec证据而为0；是有限关系覆盖的真实漏检。'),
    ('Ec', '02144', '参照分歧：宗旨与实质经济内容', '倾向Ec=0',
     '建立管用高效的医保支付机制', [], '共同Ec实质价格／支付资源；一般宗旨区分',
     '当前为制定工作方案的概括性目标，未规定支付责任、标准、费用或资源约束。C按支付机制名称纳入，A与两机器排除；不能把一般建立制度的目的直接当实质药品经济内容。'),
    ('Ec', '02158', '参照分歧／明确条文援引', '倾向Ec=1；不据C=0记机器错',
     '符合《基本医疗保险用药管理暂行办法》第九条、第十条规定的药品', ['(一)在同治疗领域中,价格或费用明显偏高且没有合理理由的药品;'],
     '共同必要语境第3条；Ec价格费用比较',
     '第九条的药物经济性与第十条价格费用明显偏高均是具体经济条件，当前明确要求符合。三方1有可核查关系和引文，C的0源于排除条文展开的操作解释；不把泛父段基金能力作为依据。'),
    ('Ec', '02462', '需要专家边界：证据更新与资料时点', '倾向Ec=0，保留更新证据解释',
     '汇率、价格费用数据等信息以截至 2026 年 5 月31 日最新数据为准', [],
     '共同Ec价格证据；共同一般格式／对象名称排除；旧评价要求与事务性提及',
     '本句规定信息截止日与说明书版本，未新增价格评价或经济资料内容范围，A/C按时点元数据排除。LLM按最新价格数据证据要求纳入也有明确文字，不能说虚构来源；需统一仅规定证据版本/时效是否算对经济证据的实质关注。'),
    ('Ec', '03763', '参照分歧：明确价格测算内容', '倾向Ec=1',
     '谈判材料则主要用于测算工作', ['是医保底价测算的重要参考'],
     '共同Ec药品价格测算及价格证据',
     '当前除模板准备外，实质说明材料用于医保底价测算这一价格内容，不是仅文件名或专业身份。A和两机器1有明确经济用途，C将其全部看作模板事务的排除过宽；旧手册同样允许药价内容，宜记录参照分歧而非定性全部为新定义改变。'),
]


def main():
    cfg = json.loads((PREVIOUS / 'actual_bindings01.json').read_text())
    A, C = (jl(cfg['references'][k]) for k in ('A', 'C'))
    R, L = (jl(cfg['methods'][k]['output']) for k in ('rules', 'LLM'))
    material = jl(cfg['current_material']); rule_input = jl(cfg['current_rule_material'])
    design = read(cfg['sampling_design']); sample = {r['original_id']: r for r in design['sample'] if r['component'] == 'probability_canonical'}
    assert len(sample) == 180
    oldfreeze = read(bd(R3 / 'admin/confirmation_packet_freeze.json'))
    manuals = {'current': cfg['current_manual']}
    for key, fn in [('old_handbook', '完整五维手册-v1.3.md'), ('old_operations', '共用操作说明-v1.4.md')]:
        p = R3 / 'protocol' / fn; manuals[key] = {'path': str(p), 'sha256': oldfreeze['source_sha256'][str(p)]}
    for b in manuals.values():
        assert sha(b['path']) == b['sha256']; Path(b['path']).read_text()
    lab = lambda rr, rid, d: rr[rid].get('prediction', rr[rid])['labels'][d]
    work = {(d, 'RECODE25-' + short): (category, judgement, unit_quote, contexts, manual, reason)
            for d, short, category, judgement, unit_quote, contexts, manual, reason in WORK}
    actual_keys = {(d, rid) for d in ('E', 'S', 'Ec') for rid in sample
                   if len({lab(rr, rid, d) for rr in (A, C, R, L)}) > 1}
    assert set(work) == actual_keys, 'Review must cover every actual dimension disagreement'
    summary = {}; items = []; sources = {}; original_cache = {}
    for d in ('E', 'S', 'Ec'):
        ids = sorted(r for dd, r in actual_keys if dd == d)
        assert len(ids) <= 30
        pairs = {}
        for method, rr in [('rules', R), ('LLM', L)]:
            for ref, refs in [('A', A), ('C', C)]:
                differing = [rid for rid in sorted(sample) if lab(rr, rid, d) != lab(refs, rid, d)]
                pairs[method + '-' + ref] = {'n': len(differing), 'ids': differing,
                    'by_group': dict(Counter(sample[r]['group'] for r in differing))}
        summary[d] = {'unique_disagreement_n': len(ids), 'by_group': dict(Counter(sample[r]['group'] for r in ids)),
                      'ids': ids, 'pairwise_disagreements': pairs, 'all_reviewed': True}
        for rid in ids:
            category, judgement, quote, context_quotes, manual, reason = work[d, rid]
            unit = material[rid]; assert quote in unit['text'], (rid, quote)
            located = []
            for q in context_quotes:
                matched = [c['context_id'] for c in unit['contexts'] if q in c.get('text', '')]
                assert matched, (rid, q); located.append({'quote': q, 'context_ids': matched})
            items.append({'dimension': d, 'id': rid, 'group': sample[rid]['group'],
                'labels': {name: lab(rr, rid, d) for name, rr in [('A', A), ('C', C), ('rules', R), ('LLM', L)]},
                'category': category, 'AI_work_reading': judgement, 'unit_quote': quote,
                'context_quotes': located, 'manual_relation': manual, 'reason': reason,
                'no_replacement_label': True})
            if rid in sources:
                continue
            inp = rule_input[rid]['input']; p = Path(inp.get('unit_source', inp['source']))
            expected = inp.get('unit_source_sha256', inp['source_sha256']); assert sha(p) == expected
            originals = {}
            for name, refs in [('A', A), ('C', C)]:
                eff = refs[rid]['annotation_provenance']['effective']; entry = {}
                for kind in ('result', 'packet'):
                    b = {'path': eff[kind + '_path'], 'sha256': eff[kind + '_sha256']}
                    if b['path'] not in original_cache:
                        original_cache[b['path']] = read(b)
                    data = original_cache[b['path']]
                    entry[kind + '_binding'] = b
                    entry[kind + '_row'] = next(r for r in data['rows'] if r['id'] == eff['blind_id'])
                assert entry['result_row']['labels'] == refs[rid]['labels'] and entry['packet_row']['text'] == unit['text']
                originals[name] = entry
            sources[rid] = {'current_full_row': unit, 'source': {'path': str(p), 'sha256': expected,
                'unit_id': inp['unit_id'], 'pages': unit.get('pages', [])},
                'adopted_A_record': A[rid], 'adopted_C_record': C[rid], 'original_effective_records': originals,
                'actual_rules_record': R[rid], 'actual_LLM_record': L[rid]}
    write('全部分歧与紧凑原因01.json', {'status': 'AI development review, not new human results',
          'scope': 'original probability180 only', 'summary': summary, 'items': items,
          'all_disagreements_reviewed': True, 'dimension_item_n': len(items), 'unique_unit_n': len(sources),
          'no_sampling_of_disagreements': True, 'no_new_validation_claim': True})
    write('逐条完整来源证据01.json', {'manuals': manuals, 'sources': sources, 'current_material_binding': cfg['current_material']})
    # Counts explain denominators only. Reuse prior actual metrics rather than recomputing κ.
    prior = read(bd(PREVIOUS / '实际点估计结果01.json'))
    denominators = []
    for r in prior['records']:
        if r['component'] != 'probability_canonical' or r['dimension'] not in ('S', 'E', 'Ec'):
            continue
        if r['comparison'] == 'A_C':
            continue
        n11, n10, n01, n00 = r['raw_cells']
        denominators.append({'group': r['group'], 'comparison': r['comparison'], 'dimension': r['dimension'],
            'unit_n': r['unit_n'], 'raw_cells_11_10_01_00': r['raw_cells'],
            'machine_positive_n': n11 + n10, 'reference_positive_n': n11 + n01,
            'precision_denominator_n': n11 + n10, 'recall_denominator_n': n11 + n01,
            'f1_denominator_n': 2 * n11 + n10 + n01,
            'kappa_NA_condition': 'both streams same constant class; expected agreement=1',
            'previous_actual_point': r['point'], 'metrics_source': bd(PREVIOUS / '实际点估计结果01.json')})
    write('阳性数量与零分母说明01.json', {'scope': 'denominator diagnostics, no new metric run',
          'records': denominators, 'missing_as_zero': False,
          'NA_rules': 'precision pred+0; recall ref+0; F1 2TP+FP+FN=0; kappa expected agreement=1; NA never1',
          'rarity_does_not_excuse_semantic_errors': True})
    with (HERE / '全部分歧紧凑原因表01.csv').open('w', newline='', encoding='utf-8-sig') as f:
        fields = ['dimension', 'id', 'group', 'A', 'C', 'rules', 'LLM', 'category', 'AI_work_reading', 'reason']
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in items:
            w.writerow({**{k: r[k] for k in fields if k in r}, **r['labels']})
    lines = ['# S/E/Ec其余低项：全分歧有限AI核查', '',
             '仅AI开发判读，非新增真人结果或新共同手册效度检验。全部机器、A/C、手册、既有统计及论文保持原样。', '',
             '实际概率180内E分歧8、S7、Ec7，均≤30，因此22个维度条目全部核查，涉及18个实际单元；未抽取有利例子，也未扩样本。四方标签原样列出，来源证据含完整当前句、全部必要语境和A/C原提交材料。', '',
             '## 全部分歧原因表', '', '| 维度/ID | 部门 | A/C/规则/LLM | AI工作倾向 | 分类与原因 |', '|---|---|---|---|---|']
    for r in items:
        vals = '/'.join(str(r['labels'][n]) for n in ('A', 'C', 'rules', 'LLM'))
        lines.append('| ' + ' | '.join([r['dimension'] + '/' + r['id'].replace('RECODE25-', ''), r['group'], vals,
                     r['AI_work_reading'], r['category'] + '：' + r['reason']]) + ' |')
    lines += ['', '## 为什么不能只用低κ归因', '',
              '有效性LLM—C的8个分歧中，00919和02158是直接条文内容援引，当前手册明确允许；它们与C=0不一致并不自动构成机器错。03101却有“该研究”的明确效果研究指代和当前终点验证，属于漏检；04368把诊断匹配补成疗效，属于过度推断。01152、03157、04875仍有规范/方法/临床综合价值边界，需逐一澄清，不能将“临床”统一当有效或无效。', '',
              '安全性00008把疾病后果当药物损害，是规则对象关系错误；03950把知情同意的广义安全保护继承为药物风险，是LLM语境过度传入。00529是明确化疗/输液安全管理与一般服务质量的精确边界，不应机械归成旧“药品质量安全”被新版撤回；01768是安全资料指导与沟通事务的边界。', '',
              '经济性00637将协议确认字段当支付责任，01575漏掉明确支出区间对应支付降幅，均有具体实现问题。00919/02158/03763主要是参照对内容援引或价格测算的解释差异；02462需要统一仅证据日期与实质价格证据的范围。这里没有充分依据把所有分歧都归为旧新定义改变，旧A/C也不能直接当现轮统一手册金标准。', '',
              '## 阳性稀少与零分母', '']
    nhc = next(r for r in denominators if r['group'] == 'NHC' and r['comparison'] == 'LLM_C' and r['dimension'] == 'E')
    lines += [f"NHC E，LLM—C：参照正例{nhc['reference_positive_n']}、LLM正例{nhc['machine_positive_n']}，四格11/10/01/00={nhc['raw_cells_11_10_01_00']}；既有实际κ={nhc['previous_actual_point']['kappa']:.6f}。两个额外正标签就是01152、04368，均已逐条核查。正例稀少使少数分歧对κ影响大，不使标签错误免于核查。", '',
              '所有部门及三维的原正例与四格、已计算点值另存分母说明JSON。Precision在机器正例为0时NA，recall在参照正例为0时NA；F1仅2TP+FP+FN为0时NA；κ在双方同为常数且期望一致率为1时NA。仅一方为常数而另一方变化时κ不自动NA；高原始一致率不保证κ已定义。未将未知作0或零分母作1。', '',
              '## 连续引文与来源', '']
    for r in items:
        src = sources[r['id']]['source']
        lines += ['### ' + r['dimension'] + '/' + r['id'].replace('RECODE25-', ''), '',
                  '当前：“' + r['unit_quote'] + '”。']
        for q in r['context_quotes']:
            lines.append('必要语境：“' + q['quote'] + '”（' + '、'.join(q['context_ids']) + '）。')
        lines += ['手册关系：' + r['manual_relation'] + '。',
                  '来源：[' + Path(src['path']).name + '](' + src['path'] + ')；单元' + src['unit_id'] + '，页码' + str(src['pages']) + '。', '']
    (HERE / '三维全分歧原因表01.md').write_text('\n'.join(lines) + '\n')
    for b in [*cfg['references'].values(), *[v['output'] for v in cfg['methods'].values()], *manuals.values()]:
        assert sha(b['path']) == b['sha256']
    write('诊断来源绑定与交付01.json', {'status': 'finite_read_only_AI_diagnosis_completed',
          'previous_calculation_binding': bd(PREVIOUS / 'actual_bindings01.json'), 'manuals': manuals,
          'references': cfg['references'], 'methods': {k: v['output'] for k, v in cfg['methods'].items()},
          'sampling_design': cfg['sampling_design'], 'current_material': cfg['current_material'],
          'build_script': bd(Path(__file__)), 'artifacts_sha256': {p.name: sha(p) for p in HERE.iterdir()
                if p.is_file() and p.name != '诊断来源绑定与交付01.json'},
          'labels_manual_statistics_and_paper_modified': False, 'new_human_results': False,
          'model_calls': 0, 'new_metric_run': False, 'all_dimension_disagreements_reviewed': True})
    print(json.dumps({'status': 'saved_all_disagreements', 'dimension_item_n': len(items),
                      'unique_unit_n': len(sources), 'summary': summary}, ensure_ascii=False))


if __name__ == '__main__':
    main()
