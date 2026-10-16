"""Finite AI development review of reference compatibility; never rewrite labels."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json

HERE = Path(__file__).resolve().parent
R3 = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/coding-revision-20261007-r3')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def binding(p):
    return {'path': str(Path(p).resolve()), 'sha256': sha(p)}


def bound(b):
    p = Path(b['path']); assert p.is_absolute() and sha(p) == b['sha256'], str(p)
    return p


def read(b):
    return json.loads(bound(b).read_text())


def jl(b):
    rr = [json.loads(x) for x in bound(b).read_text().splitlines() if x.strip()]
    out = {r['id']: r for r in rr}; assert len(out) == len(rr)
    return out


def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


# These are the present assistant's stated work interpretations, not a model run,
# new human result, corrected prediction, or new statistical reference.
EXAMPLES = [
    {'dimension': 'I', 'short': '00086', 'cause': 'LLM过度推断候选', 'working_reading': '倾向I=0',
     'unit_quote': '为鼓励研究和创制新药,规范临床急需短缺药品等优先审评审批',
     'context_quotes': [], 'manual': '共同I路径3；旧操作I第1/5条',
     'reason': '当前是制定工作程序的目的，未给出本句实际供给的指导、资源、便利内容或支持资格。LLM把“规范优先程序”补成研发便利；旧操作说明同样排除一般宗旨，因此不能只归因于定义变化。',
     'expert_question': '若将制定特定程序本身视作实际供给，需要统一目的句与实际措施句的界线；不能仅为本条放宽。'},
    {'dimension': 'I', 'short': '00442', 'cause': '必要语境使用过宽／LLM过度推断候选', 'working_reading': '倾向I=0',
     'unit_quote': '在药物上市后的监测阶段,AI能够处理和分析大规模的真实世界数据',
     'context_quotes': ['本指导原则旨在完全实施ICH E7的前提下,提出老年人群参与的创新药临床试验所涉及的一些关键要素及试验设计中的要点'],
     'manual': '共同I路径3及一般安全义务排除；旧操作I第1条',
     'reason': '补充语境可以确定指南对象，但当前仅说明上市后AI监测功能，未讨论药物技术新颖、改良，也未独立给出面向创新研发的实际支持供给。LLM把整个创新药研发指导体系传入上市后监测陈述。',
     'expert_question': '技术指南中的每项方法建议是否都构成支持，还是须当前有实际供给关系？现手册的实际支持门槛仍应遵守。'},
    {'dimension': 'I', 'short': '01446', 'cause': '规则漏检候选／明确清单关系', 'working_reading': '倾向I=1',
     'unit_quote': '因此申请品种需同时满足以下条件:(1)拟开发的适应症为罕见疾病。',
     'context_quotes': ['(2)具有较强创新性。', '与药审中心就该适应症的开发计划进行讨论'],
     'manual': '共同必要语境第2条；I路径1/3；旧I研发支持',
     'reason': '该句明确引导“同时满足以下条件”，实际完整段落含“具有较强创新性”；前段给出与药审中心讨论研发计划的试点支持。无需把罕见病名称本身当创新。A/C与LLM均为1，规则无I证据、为0，属于有实质条件和当前关系锚点的漏检候选。',
     'expert_question': '本条I的依据应固定为明确创新条件及对应试点支持；不能把所有“本试点旨在”句一律纳入。'},
    {'dimension': 'I', 'short': '04164', 'cause': '必要语境／规则漏检候选／支持与事务边界待专家', 'working_reading': '倾向I=1，保留专家边界核对',
     'unit_quote': '围绕支持上市申请的临床试验方案开展沟通交流',
     'context_quotes': ['(一)适用范围:儿童专用创新药、用于治疗罕见病的创新药以及纳入突破性治疗药物程序的创新药,特别审评审批品种除外。'],
     'manual': '共同I路径3；旧操作I第1条',
     'reason': '实际适用范围限定创新药，当前除申请形式外还指定临床试验方案的技术沟通内容。新路径3允许面向创新研发的沟通支持，不要求额外证明优先资源；规则0可能未覆盖该关系。旧A/C把整句当申请方式事务，表明实际支持与申请通道界线存在参照解释分歧。',
     'expert_question': '本句提供了技术交流机会，还是只告知申请途径？需统一认定“围绕方案开展沟通”的实际供给性质，而非按LLM=1倒推。'},
    {'dimension': 'I', 'short': '01955', 'cause': '旧／新定义边界改变，兼既有参照分歧', 'working_reading': '按当前手册倾向I=0',
     'unit_quote': '适应症或功能主治发生重大变化', 'context_quotes': ['2.以下情况须申报后方可调整:'],
     'manual': '共同I路径2及修订重点；旧操作I第2条',
     'reason': '旧操作把相对既有产品的具体属性变化作为可计I条件，C据重大变化赋1而A为0。共同手册撤回变化本身的充分性；当前只规定申请调整支付范围，未建立技术创新或实质改良联系。两机器0不能直接称遗漏。',
     'expert_question': '若仍要将此类变化作为产品创新，需要另行论证和改构念，不能用旧C标签作为当前规则错误证据。'},
    {'dimension': 'I', 'short': '02220', 'cause': '既有参照边界分歧／新手册澄清支持路径', 'working_reading': '倾向I=1',
     'unit_quote': '专门起草了《创新药研发期间风险管理计划撰写技术指导原则(试行)》,为临床试验各方将全生命周期风险管理理念贯穿药物研发全过程提供指导',
     'context_quotes': [], 'manual': '共同I路径3；旧I与操作I第1条',
     'reason': '当前同时写明创新药研发对象和提供风险管理技术指导，符合共同手册，且旧手册也已纳入实体研发指导。A仅按标题排除、C按实际指导纳入；两机器1符合现明示边界。这不是证明旧手册仅测技术新颖性的例子。',
     'expert_question': '应保留研发支持子类，与产品新颖／改良分开解释；不据本条宣布A历史标签错误或本轮真人参照已兼容。'},
    {'dimension': 'F', 'short': '00172', 'cause': '旧／新构念范围收窄', 'working_reading': '按当前手册倾向F=0',
     'unit_quote': '不断发掘肿瘤患者未满足的临床需求',
     'context_quotes': ['对抗肿瘤药物的临床研发提出建议'], 'manual': '共同F公平联系；旧操作F第6条',
     'reason': '旧操作纳入明确的未满足治疗需求；当前段落谈研发需求动态，未写无法获得所需药物、支付能力或机会障碍。共同手册要求可指认的药物获取公平联系，机器双0体现收窄候选，不能据A=C=1认定双漏检。',
     'expert_question': '研究构念应是一般未满足临床需求／可及性还是公平获取；两者应在框架层面明确，不逐条凭分数选择。'},
    {'dimension': 'F', 'short': '01187', 'cause': '旧／新构念范围收窄', 'working_reading': '按当前手册倾向F=0',
     'unit_quote': '持续跟踪已完成评价药品的实际供应与应用情况',
     'context_quotes': ['不断累积相关数据验证评价结果'], 'manual': '共同F纳入条件及普通管理排除；旧操作F第4条',
     'reason': '旧操作明确把供应状况信息要求计入F。当前为评价结果跟踪，未联系治疗需要保障、患者支付能力或不合理差异；在新公平联系构念中不足。它不是临床管理难度标签被撤回的例子。',
     'expert_question': '若论文希望测量一般可及性，应在构念名称及整套定义上处理，而非把供应信息硬称公平联系。'},
    {'dimension': 'F', 'short': '04886', 'cause': '真实待专家决定／保障与患者负担边界', 'working_reading': '不作兼容定论',
     'unit_quote': '对使用周期较长、疗程费用较高的谈判药品,可探索建立单独的药品保障机制。',
     'context_quotes': ['要根据基金承受能力、住院补偿水平等情况,确定适宜的保障水平。'],
     'manual': '共同F按需保障／患者可负担及普通费用排除；旧F实际保障',
     'reason': 'A/C据实际单独保障安排纳入。现条款将长疗程高费用与专门保障相连，可能已表达持续治疗的费用获取障碍；但完整语境随后强调基金承受能力，也可能只是支付管理。两机器排除并不足以解决这一边界。',
     'expert_question': '定性的“高费用—单独药品保障”是否已经是按需治疗获取／金融障碍联系，还是必须明示患者支付能力？这是精确构念分歧，不应默认为旧参照错。'},
    {'dimension': 'F', 'short': '00292', 'cause': 'LLM过度推断候选／治疗获益与公平机会区分', 'working_reading': '倾向F=0，保留试验获取边界',
     'unit_quote': '有机会交叉至试验组接受该治疗,从而尽可能确保受试者接受更有效的治疗',
     'context_quotes': ['对于抗肿瘤药物,提高疗效和延长患者的生存时间仍是当下追求的主要目标'],
     'manual': '共同F可指认公平联系；旧操作F第3条',
     'reason': '当前给出试验内交叉治疗安排与效果目的，未说明对照组原本无法获得所需药物或存在不合理获取障碍。旧操作明确排除一般试验分组机会；新公平门槛也不能仅从“更有效”补出公平获取。LLM把效果／交叉机会直接当按需保障，存在过度推断。',
     'expert_question': '如将疾病进展后的交叉治疗本身视作按需获取保障，需明示它与一般试验分配的分界，不能仅有患者有治疗需要这一常识。'},
    {'dimension': 'F', 'short': '00919', 'cause': '必要语境／真实待专家决定', 'working_reading': '不作兼容定论',
     'unit_quote': '符合《基本医疗保险用药管理暂行办法》第七条、第八条规定',
     'context_quotes': ['并符合临床必需、安全有效、价格合理等基本条件。'],
     'manual': '共同必要语境第3条及F公平联系；旧操作F第1条',
     'reason': '援引范围真实完整，第七条临床必需是确指实质条件，不能说LLM凭空编造。争议是它与“可以申报”结合，是否已经构成按治疗需要的药品保障关系，还是仅普通资格的临床标准。A/C按尚未实际给付排除；新手册未要求措施已经有效，但也不允许以所有药物天然有需要为公平依据。',
     'expert_question': '必须统一“申报资格+直接临床必需条件”能否满足按需保障，不能一边允许实质条款传入S/E/Ec、一边不说明F为何能或不能成立。'},
    {'dimension': 'F', 'short': '04894', 'cause': '既有参照分歧／新获取公平范围收窄', 'working_reading': '按当前材料倾向F=0',
     'unit_quote': '部署处方流转中心,连通医保经办机构、定点医疗机构、定点零售药店,保证电子处方顺畅流转',
     'context_quotes': ['以处方流转为核心,落实“定机构、定医师、可追溯”等要求,实现患者用药行为全过程监管。'],
     'manual': '共同F药品治疗获取范围及一般物流信息排除；旧F常规获取渠道',
     'reason': 'A按常规获取渠道计F，C按结算／信息系统排除。当前给定段落着重流转监管、防骗保与基金安全，未写按需用药、支付障碍或地区机会差异；不把“双通道”标题的全部保障目的传入本句。新构念下双0较有依据，旧分歧仍原样保留。',
     'expert_question': '仅渠道建设与有明确治疗获取障碍的外配处方保障应分别界定；若需要未给的目的段落，应另标必要语境而非想象补全。'},
]


def main():
    cfg = json.loads((HERE / 'actual_bindings01.json').read_text())
    old = read(cfg['adopted_final_manifest']); assert cfg['references'] == old['references']
    packet_freeze = R3 / 'admin/confirmation_packet_freeze.json'; frozen = json.loads(packet_freeze.read_text())
    manuals = {'current': cfg['current_manual']}
    for name, filename in [('old_handbook', '完整五维手册-v1.3.md'), ('old_operations', '共用操作说明-v1.4.md')]:
        p = R3 / 'protocol' / filename
        manuals[name] = {'path': str(p), 'sha256': frozen['source_sha256'][str(p)]}; bound(manuals[name])
    for b in manuals.values():
        bound(b).read_text()  # Entire actual manuals, not a manuscript appendix.
    A, C = (jl(cfg['references'][k]) for k in ('A', 'C'))
    R, L = (jl(cfg['methods'][k]['output']) for k in ('rules', 'LLM'))
    material = jl(cfg['current_material']); rule_material = jl(cfg['current_rule_material'])
    design = read(cfg['sampling_design'])
    sample = {r['original_id']: r for r in design['sample'] if r['component'] == 'probability_canonical'}
    assert len(sample) == 180
    label = lambda rr, rid, d: rr[rid].get('prediction', rr[rid])['labels'][d]
    original_cache = {}; origin_files = {}; original_rows = {}; original_packet_rows = {}
    for name, refs in [('A', A), ('C', C)]:
        for rid in sample:
            eff = refs[rid]['annotation_provenance']['effective']
            for kind in ('result', 'packet'):
                b = {'path': eff[kind + '_path'], 'sha256': eff[kind + '_sha256']}
                origin_files[b['path']] = b['sha256']
                if b['path'] not in original_cache:
                    original_cache[b['path']] = read(b)
            result = original_cache[eff['result_path']]; packet = original_cache[eff['packet_path']]
            assert result['protocol_version'] == 'CAL-5D-20260926-v1.3' and result['operational_version'] == 'v1.4'
            rawrow = next(r for r in result['rows'] if r['id'] == eff['blind_id'])
            inp = next(r for r in packet['rows'] if r['id'] == eff['blind_id'])
            assert rawrow['labels'] == refs[rid]['labels'] and inp['text'] == material[rid]['text']
            original_rows[name, rid] = rawrow; original_packet_rows[name, rid] = inp
    classes = {}; rows_out = []
    for d in ('I', 'F'):
        classes[d] = {k: [] for k in ('A=C=1且两机器=0', 'A=C=0且至少一机器=1', 'A≠C')}
        for rid in sorted(sample):
            a, c, r, l = [label(rr, rid, d) for rr in (A, C, R, L)]
            category = ('A=C=1且两机器=0' if a == c == 1 and r == l == 0 else
                        'A=C=0且至少一机器=1' if a == c == 0 and (r == 1 or l == 1) else
                        'A≠C' if a != c else None)
            if category:
                record = {'dimension': d, 'category': category, 'id': rid, 'group': sample[rid]['group'],
                          'A': a, 'C': c, 'rules': r, 'LLM': l, 'text': material[rid]['text']}
                classes[d][category].append(record); rows_out.append(record)
    counts = {d: {k: {'n': len(v), 'by_group': dict(Counter(r['group'] for r in v)),
                      'ids': [r['id'] for r in v]} for k, v in groups.items()} for d, groups in classes.items()}
    subtype_counts = {}
    for name, refs in [('A', A), ('C', C)]:
        subtype_counts[name] = {}
        for d, field in [('I', 'innovation_subtypes'), ('F', 'fairness_subtypes')]:
            hits = [rid for rid in sample if refs[rid]['labels'][d] == 1]
            subtype_counts[name][d] = {'positive_n': len(hits), 'subtype_occurrences': dict(Counter(
                t for rid in hits for t in refs[rid].get(field, []))), 'ids': hits}
    write('实际问题条目清单01.json', {'scope': 'probability180 only; diagnostic counts, no new performance metric',
          'counts': counts, 'items': rows_out, 'existing_reference_positive_subtypes': subtype_counts,
          'supplement': {'id': 'RECODE25-01446', 'dimension': 'I', 'A': 1, 'C': 1, 'rules': 0, 'LLM': 1,
                         'reason': 'Three requested categories omit consensus-positive single-machine misses'}})
    with (HERE / '实际问题条目清单01.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['dimension', 'category', 'id', 'group', 'A', 'C', 'rules', 'LLM', 'text'])
        w.writeheader(); w.writerows(rows_out)
    examples = []
    for work in EXAMPLES:
        rid = 'RECODE25-' + work['short']; d = work['dimension']; assert rid in sample
        unit = material[rid]; assert work['unit_quote'] in unit['text']
        located = []
        for quote in work['context_quotes']:
            matches = [c for c in unit['contexts'] if quote in c.get('text', '')]
            assert matches, (rid, quote)
            located.append({'quote': quote, 'matched_context_ids': [c['context_id'] for c in matches]})
        rawinput = rule_material[rid]['input']
        p = Path(rawinput.get('unit_source', rawinput['source']))
        expected = rawinput.get('unit_source_sha256', rawinput['source_sha256'])
        assert sha(p) == expected
        row = {**work, 'id': rid, 'group': sample[rid]['group'],
               'labels_unchanged': {n: label(rr, rid, d) for n, rr in [('A', A), ('C', C), ('rules', R), ('LLM', L)]},
               'current_material_row': unit, 'source': {'path': str(p), 'sha256': expected,
                   'unit_id': rawinput['unit_id'], 'pages': unit.get('pages', [])},
               'located_context_quotes': located, 'adopted_A_record': A[rid], 'adopted_C_record': C[rid],
               'original_effective_A_record': original_rows['A', rid],
               'original_effective_C_record': original_rows['C', rid],
               'original_effective_A_packet_row': original_packet_rows['A', rid],
               'original_effective_C_packet_row': original_packet_rows['C', rid],
               'actual_rule_record': R[rid], 'actual_LLM_record': L[rid],
               'AI_development_interpretation_only': True, 'not_a_new_reference_label': True}
        examples.append(row)
    for d in ('I', 'F'):
        selected = [r for r in examples if r['dimension'] == d]
        assert len(selected) <= 6 and len({r['group'] for r in selected}) >= 2
    write('参照兼容逐条来源证据01.json', {'status': 'AI development source review, not new human result',
          'manuals': manuals, 'examples': examples, 'labels_modified': False})
    provenance = {'status': 'finite_read_only_compatibility_diagnosis', 'manuals': manuals,
                  'old_manual_binding_source': binding(packet_freeze), 'adopted_manifest': cfg['adopted_final_manifest'],
                  'references': cfg['references'], 'methods': {k: v['output'] for k, v in cfg['methods'].items()},
                  'current_material': cfg['current_material'], 'calculation_binding': binding(HERE / 'actual_bindings01.json'),
                  'effective_original_record_checked_n': 360, 'original_effective_files_sha256': origin_files,
                  'original_protocol_version': 'CAL-5D-20260926-v1.3', 'original_operational_version': 'v1.4',
                  'source_generation_identity': 'Historical A/C files contain AI-agent generation and rereview records',
                  'human_post_review_fact': 'User-confirmed historical post review, preserved; no new reviewer identity invented',
                  'new_common_manual_human_review': '尚待确认', 'new_independent_human_review': False,
                  'model_calls': 0, 'machine_reference_paper_modified': False, 'build_script': binding(Path(__file__))}
    write('诊断来源绑定01.json', provenance)
    lines = ['# 创新性与公平性参照兼容：有限 AI 开发核查', '',
             '这不是新增真人结果、独立验证或参照改标。既有真人事后复核事实保留；共同手册兼容仍待确认。A/C原文件具有AI生成与复读沿革，未将其改称新真人盲评。', '',
             '旧手册来源已核定：原A/C材料冻结记录绑定完整v1.3及操作v1.4，实际SHA分别为75ff8ebd…、1b894ea4…。180条每位的最终采用标签均回到effective原始提交及对应材料，360条记录标签与正文核对相等；不是从论文旧附录代替手册。当前手册SHA为5abee1f2…。', '',
             '## 实际问题数量与条目', '', '| 维度 | A=C=1且两机器=0 | A=C=0且至少一机器=1 | A≠C |', '|---|---:|---:|---:|']
    for d in ('I', 'F'):
        lines.append('| ' + d + ' | ' + ' | '.join(str(v['n']) for v in counts[d].values()) + ' |')
    for d in ('I', 'F'):
        for category, info in counts[d].items():
            lines += ['', f"{d}，{category}：" + ('无。' if not info['ids'] else '、'.join(x.replace('RECODE25-', '') for x in info['ids']) + '。')]
    lines += ['', 'I另有共正单机器漏检01446：A/C=1、规则=0、LLM=1，前三类不包含它，故在六例中补充，不增加样本。', '',
              '## 构念范围诊断', '',
              'I不是现在才加入研发支持。旧v1.3和操作v1.4已同时纳入药物创新属性及明确实体研发支持；本批A的唯一I正标签01446就是research_support，C的3个正标签为研发支持2、属性1。当前路径1/2/4与路径3仍混合产品属性、资格及政策支持，其子类应分别解释，不能把所有I当产品技术新颖性。01955涉及旧“具体属性变化”充分条件被撤回；02220显示既有支持/标题解释分歧；01446是真实实现遗漏候选，00086/00442则显示LLM把目的或创新指南背景传播为支持的风险。不能把本批I的低κ全部归因于定义改变。', '',
              'F的旧A与C各12个正标签全部为access，clinical_management均为0。本批高F/低兼容不能归因于撤回临床管理难度独立条件。旧操作纳入一般供应信息、实际覆盖和未满足治疗需求，新手册追加可指认公平联系；7条共正双零中供应跟踪、普通目录范围、目录目的和赠药资料等，说明一般保障获取向公平获取收窄是主要兼容问题候选。04886及00919的精确边界仍未解决，不能把机器零当概念正确的证明。若研究真正要测一般可及性/药物保障，需在框架名称与整套定义层面决定；若坚持公平联系构念，则旧access参照不宜直接当同口径金标准。', '',
              '## 中文精简原因矩阵', '', '| 维度/条目 | 部门 | A/C/规则/LLM | AI工作倾向 | 可能原因 |', '|---|---|---|---|---|']
    for r in examples:
        vals = r['labels_unchanged']
        lines.append('| ' + ' | '.join([r['dimension'] + '/' + r['short'], r['group'],
                     '/'.join(str(vals[n]) for n in ('A','C','rules','LLM')), r['working_reading'], r['cause']]) + ' |')
    lines += ['', '## 逐条来源与具体争点', '']
    for r in examples:
        lines += ['### ' + r['dimension'] + '/' + r['short'] + '（' + r['group'] + '）', '',
                  '当前连续原文：“' + r['unit_quote'] + '”。']
        for q in r['located_context_quotes']:
            lines.append('必要语境：“' + q['quote'] + '”（' + '、'.join(q['matched_context_ids']) + '）。')
        lines += ['', '手册关系：' + r['manual'] + '。' + r['reason'],
                  '须确认的具体边界：' + r['expert_question'],
                  '来源：[' + Path(r['source']['path']).name + '](' + r['source']['path'] + ')；单元' + r['source']['unit_id'] +
                  '；页码' + str(r['source']['pages']) + '。完整当前语境、A/C原提交、原材料及机器原记录另存逐条来源证据JSON。', '']
    lines += ['没有把这些AI工作倾向写回任何标签、机器、人工参照或论文。12条例子是定向诊断材料，不能外推为独立错误率或代表整套算法的效度。']
    (HERE / '参照兼容原因矩阵01.md').write_text('\n'.join(lines) + '\n')
    for b in [*cfg['references'].values(), *[v['output'] for v in cfg['methods'].values()]]:
        bound(b)
    print(json.dumps({'status': 'finite_diagnosis_saved', 'counts': counts, 'example_n': len(examples),
                      'old_handbook_found': True, 'all_original_labels_unchanged': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
