from pathlib import Path
import hashlib, json

OUT=Path(__file__).resolve().parent
W=OUT.parents[1]
MANUAL=W/'定义溯源核查/共同判据定稿/共用编码手册.md'
SOURCE=W/'LLM编码/统一判据编码准备/共用纯来源材料03/source_only_with_scope03.jsonl'
IDS=['RECODE25-00929','RECODE25-01956','RECODE25-02286']
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(MANUAL.read_bytes())=='5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c'
raw_lines={};rows={}
with SOURCE.open(encoding='utf-8') as stream:
    for line in stream:
        record=json.loads(line)
        if record['id'] in IDS:
            rows[record['id']]=record
            raw_lines[record['id']]=line
assert set(rows)==set(IDS)

group_ids={
    'RECODE25-00929':'CTX-48fc693e1da24434304f',
    'RECODE25-01956':'CTX-4aedbe6b2e7151532291',
    'RECODE25-02286':'CTX-889afcc6736a4530e5d0'
}
relation_readings={
    'RECODE25-00929':'当前句“具有以下情况之一”明确前指紧随的三项情形。第三项不是“按有关规定”的一般指引，而是以“符合”将药品与第九条、第十条具体调出条件相连。因而关系链为当前明确指代→第三项确指→第九、十条完整列举的实质条件。',
    'RECODE25-01956':'当前句“调出目录重点考虑的情形：”以冒号引出紧随的三个编号情形，清单在“(三)其他”之前闭合。它没有自足地定义一个对象后再独立另列项目，而是提出调出资格命题、由后列成员完成具体条件。第三项以“符合”直接援引第九条、第十条。因此按明确指代及实质条件规则完成此清单命题；不是凭普通栏目标题传入下文全部维度。',
    'RECODE25-02286':'当前句“具有以下情况之一”明确前指紧随的四项情形。第一项以“符合”直接援引第九条、第十条，第四项还直接列出禁忌、不良反应、注意事项未按期完善的安全证据条件。关系链止于这些当前明确指向的条件，不扩展《中药注册管理专门规定》全文。'
}
manual_rules=[
    {'section':'分析单位与共同规则','quote':'每个1应有当前句段的原文依据；必要语境只用于解释对象、指代、适用条件或被明确援引的实质要求，不将标题或父段的全部维度复制给子项。'},
    {'section':'必要语境与外部引用的范围/2.明确指代','quote':'当前使用“应包括下列”“同时满足以下条件”“上述安全要求”等关系时，补全被具体指向的内容，并保留当前关系锚点及实际用于标签的语境引文。自足定义之后另列项目，与当前没有该关系时，不复制相邻维度。'},
    {'section':'必要语境与外部引用的范围/3.当前实质要求','quote':'当前直接要求药品符合某条、某款的实质条件时，须提供并核验确指的原文范围；仅“详见工作方案”“按有关规定”或程序名称属于一般指引，不能由此逐层展开全部政策并传播标签。没有数字不影响定性要求被编码。'}
]
manual_text=MANUAL.read_text()
assert all(rule['quote'] in manual_text for rule in manual_rules)

readings=[]
for rid in IDS:
    record=rows[rid];nodes={n['context_id']:n for n in record['contexts']}
    group=nodes[group_ids[rid]]
    children=group['structure']['child_groups'][0]['ordered_context_ids']
    members=[nodes[c] for c in children]
    assert members[0]['text']==record['text']
    cited=[n for n in record['contexts'] if n['kind']=='cited_article']
    assert len(cited)==10
    cite_by={n['structure']['paragraph_id']:n for n in cited}
    reference_member=next(n for n in members[1:] if '第九条、第十条' in n['text'])
    safety_member=next((n for n in members[1:] if '“禁忌”' in n.get('text','')),None)
    anchor=record['text']
    dimension_specs={
      'S':(1,[cite_by['p0011_item03'],cite_by['p0012_item03']]+([safety_member] if safety_member else []),
           '第九条（三）明确要求综合考虑不良反应及风险收益，第十条（三）又明确安全性不符合条件。当前清单所列药品资格确指这些实质条件，按药物损害、风险及评价要求纳入S。'+('本条第四成员还直接列出禁忌、不良反应、注意事项的未明及未按期完善，可单独支持S。' if safety_member else '')+'未凭撤销批准文件或负面清单等程序状态推定S。'),
      'E':(1,[cite_by['p0012_item02'],cite_by['p0012_item03']],
           '第十条（二）实质讨论临床价值不确切及更好替代，第十条（三）直接规定有效性条件。当前清单通过确指成员将这些药物效果/临床价值条件纳入调出考虑。依手册，否定、不确定及比较要求仍是有效性关注，故E=1；不表示这些药品已经有效。'),
      'Ec':(1,[cite_by['p0012_item01'],cite_by['p0011_item03'],cite_by['p0012_item03']],
           '第十条（一）直接规定同治疗领域价格或费用明显偏高且无合理理由，第九条（三）明确药物经济性，第十条（三）直接规定经济性条件。当前清单确指这些药品经济实质条件，符合价格费用/药物经济评价判据，故Ec=1。依据来自这些具体条件，不是从目录调出、谈判名称或普通医保申报资格补出支付责任。'),
      'I':(0,[],
           '当前引导句、它所指的完整成员及第九、十条未实质讨论药物新颖性、实质改良、创新研发支持或创新资格比较。撤销批准文件、负面清单和违规进入目录等一般管理资格不足以赋I。前一段适应症或功能主治变化不属于当前所指清单，也不能单凭属性变化赋I。'),
      'F':(0,[],
           '清单含市场供应、向医保定点医药机构供应等一般获取内容；第十条有药价或费用偏高，但完整必要范围没有把它们具体联系到按治疗需要保障、患者支付能力、群体/地区保障机会差异或不合理获取限制。市场供应不足及普通价格条件本身均不自动满足手册的公平联系；故F=0。不能把“医保”“保障市场供应”或“价格无合理理由”直接改写为患者可负担性。')
    }
    dimensions={}
    for dimension,(label,evidence,reason) in dimension_specs.items():
        dimensions[dimension]={'value':label,'current_anchor':anchor,
            'current_relation':relation_readings[rid],
            'direct_reference_member':reference_member,
            'necessary_evidence_quotes':evidence,'reason':reason}
    readings.append({'id':rid,'current_text':record['text'],'current_pages':record['pages'],
      'current_anchor_quote':'调出目录重点考虑的情形:' if rid.endswith('01956') else '具有以下情况之一的药品将重点考虑调出基本目录:',
      'relation_reading':relation_readings[rid],
      'bounded_ordered_list':{'container':group,'members':members},
      'complete_directly_cited_articles':cited,
      'labels':{d:dimensions[d]['value'] for d in ['S','E','Ec','I','F']},
      'dimensions':dimensions,
      'applicability_note':('“情形：”是否构成当前明确承接关系是此条的具体适用边界。本工作判读认为它同有界编号成员共同完成调出条件命题，满足手册明确指代规则；采用的是语义和原文清单关系，不以机器节点类型作为赋值理由。' if rid.endswith('01956') else '“具有以下情况之一”是当前明示清单关系锚点，具体成员中的确指条件可被补全。'),
      'unresolved_material_gap_for_this_reading':[],
      'duplicate_context_handling':'完整所读来源保留全部重复发生；相同成员仅作为同一关系证据使用，不重复计维度。'
    })

result={'identity':'AI独立工作判读，限三条清单引导句的手册适用核对',
    'input_scope':'本次仅读固定手册和指定材料03的三条完整来源行；未读机器输出、旧标签、指标或其他判读答案。',
    'manual':{'path':str(MANUAL),'sha256':sha(MANUAL.read_bytes())},
    'source':{'path':str(SOURCE),'selected_ids':IDS,
      'selected_raw_line_sha256':{rid:sha(raw_lines[rid].encode()) for rid in IDS}},
    'manual_relation_rules':manual_rules,'readings':readings,
    'scope_note':'本结果不修改人工包，不构成真人复核或效度检验；只记录本次AI对所给完整必要语境的规则适用。'}
(OUT/'独立AI工作判读01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'判读所读来源三条03.jsonl').write_text(''.join(raw_lines[rid] for rid in IDS),encoding='utf-8')
lines=['清单援引三条独立AI工作判读01','',result['identity'],result['scope_note'],
       '固定手册SHA：'+result['manual']['sha256'],
       '所读来源：'+str(SOURCE),'', '编号                    S  E  Ec I  F']
for reading in readings:
    lines.append(reading['id']+'      '+'  '.join(str(reading['labels'][d]) for d in ['S','E','Ec','I','F']))
lines.extend(['','共同规则依据：'])
for rule in manual_rules:lines.extend([rule['section'],rule['quote'],''])
for reading in readings:
    lines.extend(['','【'+reading['id']+'】','当前句：'+reading['current_text'],
       '关系判断：'+reading['relation_reading'],'适用边界：'+reading['applicability_note'],
       '完整当前清单成员：'])
    for n in reading['bounded_ordered_list']['members']:
        lines.extend([n['context_id']+' / '+n['structure']['paragraph_id'],n['text']])
    lines.append('成员直接援引的第九、十条完整范围：')
    for n in reading['complete_directly_cited_articles']:
        lines.extend([n['context_id']+' / '+n['structure']['paragraph_id'],n['text']])
    lines.append('逐维工作判读：')
    for dimension in ['S','E','Ec','I','F']:
        judgment=reading['dimensions'][dimension]
        lines.extend([dimension+'='+str(judgment['value']), '当前锚点：'+judgment['current_anchor'],judgment['reason']])
        for n in judgment['necessary_evidence_quotes']:
            lines.extend(['实际语境依据 '+n['context_id'],n['text']])
lines.extend(['','来源限定：完整所读三行及全部contexts另存于判读所读来源三条03.jsonl；JSON保存每维当前锚点、清单成员、完整第九/十条范围和实际引文。'])
(OUT/'独立AI工作判读01.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'output_directory':str(OUT),'labels':{r['id']:r['labels'] for r in readings},
      'files':['独立AI工作判读01.json','独立AI工作判读01.txt','判读所读来源三条03.jsonl']},ensure_ascii=False))
