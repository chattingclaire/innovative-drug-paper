from pathlib import Path
import json
import hashlib
import re

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ADMIN = HERE / '材料整理记录'
ADMIN.mkdir(exist_ok=True)
W = ROOT / 'outputs/编码修订核查-20261008'
R3 = ROOT / 'outputs/coding-revision-20261007-r3'

def read_jsonl(p):
    return {r['id']: r for r in map(json.loads, p.read_text().splitlines())}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def norm(s):
    return re.sub(r'\s+', '', s)

frame_path = W / '统计复算/来源读取与图示校正/同材料目标框4481.jsonl'
source_path = W / 'LLM编码/统一判据编码准备/共用纯来源材料04/source_only_with_scope04.jsonl'
frame = read_jsonl(frame_path)
sources = read_jsonl(source_path)
A = read_jsonl(R3 / 'reference/agent_A_final_v14.jsonl')
B = read_jsonl(R3 / 'reference/agent_C_final_v14.jsonl')
diff = json.loads((HERE / '既有AB创新性公平性分歧材料.json').read_text())
audit = {r['id']: r for r in json.loads((HERE / '校准原文语境核查.json').read_text())['records']}
initial_review_ids = set(audit)
extra_review_file = ADMIN / '校准追加原文语境核查.json'
if extra_review_file.exists():
    extra_report = json.loads(extra_review_file.read_text())
    for r in extra_report['records']:
        audit[r['evidence']['original_id']] = r
selected = {}
for r in diff['records']:
    selected[r['id']] = '既有创新性或公平性分歧'
reserved = ['RECODE25-00650', 'RECODE25-00791', 'RECODE25-03474', 'RECODE25-03710']
for rid in reserved:
    assert rid not in selected
    selected[rid] = '候选手册新增边界教学材料'
used_families = {frame[r]['normalized_text_family']['family_id'] for r in selected}

def select_joint(condition, n, reason):
    pool = [r for r in A if r in B and r not in selected and A[r]['labels'] == B[r]['labels'] and condition(A[r]['labels'])]
    pool.sort(key=lambda r: hashlib.sha256(('calibration-20261010:' + r).encode()).hexdigest())
    picked = []
    counts = {g: 0 for g in ['NMPA','NHSA','NHC']}
    while len(picked) < n:
        available = [r for r in pool if frame[r]['normalized_text_family']['family_id'] not in used_families]
        assert available, (reason, n, len(picked))
        rid = min(available, key=lambda r: (counts[frame[r]['analysis_group']], pool.index(r)))
        pool.remove(rid)
        picked.append(rid)
        counts[frame[rid]['analysis_group']] += 1
        used_families.add(frame[rid]['normalized_text_family']['family_id'])
        selected[rid] = reason

select_joint(lambda v: v['I'] == 1, 5, '既有双方一致：创新性涉及')
select_joint(lambda v: v['F'] == 1, 5, '既有双方一致：公平性涉及')
select_joint(lambda v: not any(v.values()), 4, '既有双方一致：五维均未涉及')
for d in ['S','E','Ec']:
    select_joint(lambda v, d=d: v[d] == 1, 1, f'既有双方一致：{d}涉及')
assert len(selected) == 40
order = sorted(selected, key=lambda r: hashlib.sha256(('presentation-20261010:' + r).encode()).hexdigest())
candidate_cache = {}
packets = []
checks = []

def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from strings(value)

for index, rid in enumerate(order, 1):
    fr = frame[rid]
    pos = fr['source_position']
    candidate_path = Path(pos['candidate_file'])
    if candidate_path not in candidate_cache:
        candidate_cache[candidate_path] = json.loads(candidate_path.read_text())
    candidate = candidate_cache[candidate_path]
    unit = next(x for x in candidate['unit_candidates'] if x['id'] == pos['unit_id'])
    assert unit['text'] == fr['unit_text'] == sources[rid]['text'], rid
    assert digest(candidate_path) == pos['candidate_sha256_recorded'], rid
    actual_source = Path(pos.get('unit_source_file') or pos['source_file'])
    recorded_source_hash = pos.get('unit_source_sha256_recorded') or pos['source_sha256_recorded']
    assert digest(actual_source) == recorded_source_hash, rid
    paragraphs = [p for p in candidate['paragraphs'] if p['id'] in pos['paragraph_ids']]
    if rid in audit:
        contexts = list(audit[rid]['recommended_neutral_context'])
        context_origin = '逐条来源语境核查'
    else:
        # Additional examples start with the exact source paragraph; the scope reviewer adds verified parents.
        contexts = [p['text'] for p in paragraphs]
        context_origin = '原段；待专项复核补充必要父条款'
    contexts = list(dict.fromkeys(contexts))
    context_descriptors = [{'kind':'语境原文', 'source_name':actual_source.name,
                            'source_locator':'、'.join(pos['paragraph_ids'])} for _ in contexts]
    # Match context quotes to the candidate source texts, not model rationales.
    candidate_strings = [norm(s) for s in strings(candidate)]
    source_text = actual_source.read_text() if actual_source.suffix.lower() in ['.txt','.html','.md'] else ''
    for i, context in enumerate(contexts):
        matches = [p for p in candidate['paragraphs'] if norm(context) in norm(p['text'])]
        if matches:
            context_descriptors[i]['source_locator'] = '、'.join(p['id'] for p in matches)
            context_descriptors[i]['pages'] = sorted({page for p in matches for page in p.get('pages',[])})
        elif source_text and norm(context) in norm(source_text):
            positions = [i for i,ch in enumerate(source_text) if not ch.isspace()]
            start = norm(source_text).index(norm(context))
            finish = start + len(norm(context)) - 1
            first_line = source_text[:positions[start]].count('\n')+1
            last_line = source_text[:positions[finish]].count('\n')+1
            context_descriptors[i]['source_locator'] = f'原文第{first_line}至{last_line}行'
        else:
            context_descriptors[i]['source_locator'] = '来源结构记录；见原文件对应表或图'
    quote_checks = [{'text_sha256':hashlib.sha256(s.encode()).hexdigest(), 'candidate_match':any(norm(s) in t for t in candidate_strings), 'plain_source_match':bool(source_text and norm(s) in norm(source_text))} for s in contexts]
    # Table headings are separate source cells. A column separator is presentation,
    # not a verbatim sentence; verify it against both actual structured sources.
    if rid == 'RECODE25-01419':
        table_paragraph = next(p for p in paragraphs if p.get('type') == 'table_row')
        actual_json = json.loads(actual_source.read_text())
        source_table = next(t for t in actual_json['tables'] if t['title'] == table_paragraph['table_title'])
        assert source_table['columns'] == table_paragraph['columns']
        assert table_paragraph['cells'] in source_table['rows']
        assert digest(Path(source_table['source_image'])) == source_table['source_sha256']
        for i, s in enumerate(contexts):
            if s == ' | '.join(table_paragraph['columns']):
                quote_checks[i]['structure_match'] = True
                quote_checks[i]['verbatim_sentence'] = False
                quote_checks[i]['source_columns'] = source_table['columns']
                context_descriptors[i]['kind'] = '表格列名（按列排列）'
                context_descriptors[i]['source_locator'] = '附表1；原图四列表头'
                context_descriptors[i]['source_name'] = Path(source_table['source_image']).name
            elif s == source_table['title']:
                context_descriptors[i]['kind'] = '表格名称（结构记录）'
                context_descriptors[i]['source_locator'] = 'tables[0].title；表名不作为图中文字'
            elif s == table_paragraph['text']:
                context_descriptors[i]['kind'] = '表格行（按列转写）'
    if not all(x['candidate_match'] or x['plain_source_match'] or x.get('structure_match') for x in quote_checks):
        raise ValueError(f'Context quotation requires verification: {rid} {quote_checks}')
    if rid == 'RECODE25-02233':
        # The current 2025 introduction explicitly names the 2024 pilot. Supply
        # that exact policy to both coders, rather than borrowing the 2025 channel.
        pilot = Path('/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区/原文补全/网页正文/NMPA-优化创新药临床试验审评审批试点-2024.txt')
        pilot_lines = pilot.read_text().splitlines()
        additions = [
            (pilot_lines[0], '通知名称；国药监药注〔2024〕21号'),
            (pilot_lines[4], '附件方案名称'),
            (pilot_lines[5], '方案开篇'),
            (pilot_lines[pilot_lines.index('一、工作目标')+1], '一、工作目标'),
            (pilot_lines[pilot_lines.index('（二）试点项目')+1], '二、（二）试点项目'),
            (pilot_lines[pilot_lines.index('（四）审评审批')+1], '三、（四）审评审批'),
        ]
        assert additions[-1][0].startswith('经确认的试点项目，药审中心在受理临床试验申请后30个工作日内')
        assert additions[4][0].startswith('试点项目范围为1类创新药')
        for text, locator in additions:
            assert text in pilot.read_text()
            contexts.append(text)
            context_descriptors.append({'kind':'2024年援引文件原文', 'source_name':pilot.name, 'source_locator':locator})
            quote_checks.append({'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                                 'plain_source_match':True, 'external_source':str(pilot),
                                 'external_source_sha256':digest(pilot), 'source_locator':locator,
                                 'source_url':'https://www.gov.cn/zhengce/zhengceku/202408/content_6965736.htm',
                                 'verified_republication_url':'https://yjj.sh.gov.cn/qtgzwj/20240801/6ecaa45852a44aaea6d8f45f36fb7c78.html'})
    material_id = f'校准{index:02d}'
    packets.append({
        'material_id':material_id,
        'current_text':fr['unit_text'],
        'contexts':contexts,
        'context_descriptors':context_descriptors,
        'current_kind':'当前表格行（按列转写）' if unit.get('type') == 'table_row' or any(p.get('type') == 'table_row' for p in paragraphs) else '当前句段',
        'source_name':actual_source.name,
        'pages':fr['pages'],
        'source_locator':'、'.join(pos['paragraph_ids']),
        'department':fr['department_name'],
        'conditional_reference_note':audit[rid].get('material_gap') if rid in audit else None,
    })
    checks.append({
        'material_id':material_id, 'original_id':rid, 'selection_purpose':selected[rid],
        'unit_text_sha256':fr['unit_text_sha256'], 'source':str(actual_source), 'source_sha256':recorded_source_hash,
        'candidate':str(candidate_path), 'candidate_sha256':pos['candidate_sha256_recorded'],
        'context_origin':context_origin,'context_quotes':quote_checks,
        'source_position':pos,
    })

manual = HERE / '共用编码手册.md'
payload = {'purpose':'手册开发校准，尚未冻结；40条有目的材料不代表总体', 'units':packets, 'manual':manual.read_text(), 'manual_sha256':digest(manual), 'context_review_complete':all(r in audit for r in selected)}
payload['context_review_meaning'] = '40条语境核查流程已完成；并不表示所有可能的外部援引内容均已提供，条件性需求另列。'
(ADMIN/'无答案校准内容.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
manifest = {
    'selection_rule':'既有19条I/F分歧+4条新边界教学+5条既有共同I1+5条共同F1+4条共同全0+S/E/Ec各1条；共同标签案例优先部门覆盖和不同正文族，固定SHA排序',
    'purpose':'开发材料，不用于总体推断；旧标签仅选择案例，不作为候选手册答案',
    'bindings':{str(p):digest(p) for p in [frame_path,source_path,manual,R3/'reference/agent_A_final_v14.jsonl',R3/'reference/agent_C_final_v14.jsonl']},
    'units':checks,
    'label_cells':'空白；未生成任何新判定或κ',
    'context_review_complete':payload['context_review_complete'],
    'pending':'A/B实际试填与手册讨论；条件性援引需求按当前句段任务记录，不视为已完成新人工检验',
}
(ADMIN/'校准案例选择与来源记录.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'units':len(packets),'additional_cases':[c['original_id'] for c in checks if c['original_id'] not in initial_review_ids],'context_review_complete':payload['context_review_complete'],'packet_path':str(ADMIN/'无答案校准内容.json')},ensure_ascii=False))
