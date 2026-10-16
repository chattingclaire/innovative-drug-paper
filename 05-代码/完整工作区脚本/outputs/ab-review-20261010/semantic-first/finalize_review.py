import json, hashlib
from pathlib import Path
from collections import Counter
root=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
out=root/'outputs/ab-review-20261010/semantic-first'
source=json.loads((out/'extracted.json').read_text())
annotations=json.loads((out/'annotations.json').read_text())
dims=['S','E','Ec','I','F']
sp=root/'outputs/goal-calibration-20261010/02-methods/source-supplements/prospective-common-supplements.jsonl'
supp={}
for line,text in enumerate(sp.read_text().splitlines(),1):
    o=json.loads(text)
    if o.get('supplement_id')=='SUP-NMPA2024-PILOT': supp[o['record_id']]={**o,'file':str(sp),'line':line}
triples={
0:['创新/改良型新药临床研发','在I、II期、通常III期前申请突破性程序的机会','同句将创新/改良及疾病/效果条件连接申请机会'],
1:['创新/改良型新药临床研发','突破性程序中的关键阶段沟通及下一步方案反馈','当前以资格不再满足决定终止同一支持程序'],
2:['创新/改良型新药临床研发','突破性程序的方案反馈及申请机会','当前第二或支按资格决定终止该支持'],
37:['规范所指儿童专用、罕见病、突破性程序创新药研发（保留除外）','具体品种团队负责申报前沟通至受理后技术审评全过程','当前明确按具体品种实际组建团队，规范范围补足服务对象']}
fair={
0:['严重疾病所需药物','尚无有效防治手段支的目标选项缺口','基于缺口的早期突破性程序申请机会'],
1:['严重疾病所需药物','纳入条件中的无有效防治手段分支','按是否继续符合条件终止按需研发机会'],
2:['严重疾病所需药物','纳入条件中的无有效防治手段分支','第二或支按资格不符终止按需研发机会'],
3:['严重疾病所需药物','纳入标准中的无有效防治手段分支','资格审核并决定程序终止'],
5:['临床急需短缺药品','现实药品供给缺口','首家纳入后限制同成分/途径后续优先申请'],
6:['急需罕见病目标药品','该目标产品境内未上市','优先审评申请机会'],
7:['急需罕见病目标药品','该目标产品境内未上市','直接纳入优先程序并免公示'],
16:['目标罕见疾病药品','第二项中境内无获批目标适应症药物的或支','申请试点须满足该条件组'],
17:['目标罕见疾病药品','第二或支境内无获批目标适应症药物','直接父句规定试点申请资格']}
reviews=[]
for a,r in zip(annotations,source):
    assert a['i']==r['index']
    i=a['i']
    current=''.join(c['text'] for c in r['contexts'] if c['kind']=='当前条款')
    rs={'index':i,'id':r['id'],'coding_rows':[r['coding_start_row'],r['coding_start_row']+4],'current_text':current,
        'current_context_rows':[c['row'] for c in r['contexts'] if c['kind']=='当前条款'],'review_labels':{},'original_labels':{'A':{},'B':{}},'dimensions':[],
        'rule_note':a.get('rule_note'),'source_material_issue':('两份表的原文语境缺SUP-NMPA2024-PILOT；本次已读共同补材验证标签，建议补入交付包。' if a.get('supplement') else None)}
    for n,d in enumerate(dims):
        rv=int(a['values'][n]); confirm=d in a.get('confirm_dims',[])
        av=r['A'][n][3]; bv=r['B'][n][3]
        assert int(av)==int(bv)==rv, (i,d,av,bv,rv)
        entry={'dimension':d,'review_value':None if confirm else rv,'suggested_value':rv,'original_A':av,'original_B':bv,
            'classification':'需确认' if confirm else '维持','coding_cell':f'D{r["coding_start_row"]+n}',
            'reason_cell':f'E{r["coding_start_row"]+n}','current_quote':current,'reason':a['reasons'][n],
            'original_A_reason':r['A'][n][4],'original_B_reason':r['B'][n][4],
            'contexts_used':[{'sheet':'原文语境','cell':f'E{c["row"]}',**c} for c in r['contexts'] if c['row'] in a['ctx'].get(d,[])],
            'manual_sections':a.get('manual',[])}
        if i in [14,15] and d in ['S','E','Ec','F']:
            # These complete same-version qualification standards were independently read.
            prefixes=('1.独家药品。','2.本协议期实际发生','3.未来两年的纳入','（1）不调整支付范围','（2）调整支付范围','4.市场环境未发生','5.不符合纳入常规','1.非独家药品','2.截至目录调整当年12月31日，连续纳入目录')
            for c in r['contexts']:
                if c['text'] and c['text'].startswith(prefixes) and c['kind']=='same_snapshot_referenced_source_paragraph':
                    entry['contexts_used'].append({'sheet':'原文语境','cell':f'E{c["row"]}',**c})
        if d=='I' and i in triples: entry['I3_evidence']=dict(zip(['support_object','usable_arrangement','direct_link'],triples[i]))
        if d=='F' and i in fair: entry['F_evidence']=dict(zip(['medicine_object','equity_link','arrangement'],fair[i]))
        if d=='I' and a.get('supplement'):
            s=supp[r['id']]
            quotes=['试点项目范围为1类创新药（细胞和基因治疗产品、疫苗产品等除外）临床试验申请。','经确认的试点项目，药审中心在受理临床试验申请后30个工作日内完成审评审批，并通过药审中心网站通知申请人审批结果。','实现30个工作日内完成创新药临床试验申请审评审批，缩短药物临床试验启动用时。']
            assert all(q in s['text'] for q in quotes)
            entry['supplement_used']={'file':str(sp),'line':s['line'],'id':s['supplement_id'],'source_title':s['source_title'],'source_date':s['source_date'],'source_sha256':s['source_sha256'],'source_url':s['source_url'],'quotes':quotes}
            entry['I3_evidence']={'support_object':quotes[0],'usable_arrangement':quotes[1],'direct_link':current}
        rs['dimensions'].append(entry)
        rs['review_labels'][d]=entry['review_value']
        rs['original_labels']['A'][d]=av;rs['original_labels']['B'][d]=bv
    reviews.append(rs)
counts=Counter(d['classification'] for r in reviews for d in r['dimensions'])
result={'schema_version':'semantic-ab-review-v1','identity':'AI事后语义复核，不是真人独立首判','scope':'编码表顺序索引0–38（39条，195个独立条款维度，A/B共390个编码值）','manual':'v1.3-development，已比较v1.3F-frozen，第一至七节及第九至十节判据未变','summary':{'records':39,'dimensions':195,'workbook_cells_reviewed':390,'confirmed_value_changes':0,'maintained_dimensions':counts['维持'],'needs_confirmation_dimensions':counts['需确认'],'source_delivery_gap_records':3},'limitations':['本次逐条实读当前原文与表内必要语境；未重新逐页认证所有来源图像，原文真实性/语境导出完整性由并行追溯复核。','03415 E的null表示真实规则边界待统一，建议值仍为1，不是将原件改为空。','SUP-NMPA2024-PILOT原共同补材已实读，三条I维持；工作簿本身的证据缺失另列。'],'source_files':[{'path':str(root/'outputs/goal-calibration-20261010/09-delivery/agent-review-20261010'/f'编码复核表-{k}.xlsx'),'sha256':hashlib.sha256((root/'outputs/goal-calibration-20261010/09-delivery/agent-review-20261010'/f'编码复核表-{k}.xlsx').read_bytes()).hexdigest()} for k in 'AB'],'records':reviews}
(out/'semantic-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
lines=['A/B前39条语义复核','覆盖：39条、195个条款维度、两表390个值。确定改值0；194维维持；03415 E一维需统一边界（原A/B=1，建议暂保留1）。','01729、02233、02269的I已核共同补材后维持1，交付表需补SUP-NMPA2024-PILOT原文。','按v1.3共同手册复判，v1.3F判据同内容；不把A/B一致性当分类真值；未改动原件。','']
for r in reviews:
    lines.extend([f'{r["index"]:02d} {r["id"]} 编码表 {r["coding_rows"][0]}–{r["coding_rows"][1]}行',f'当前原文（原文语境行{r["current_context_rows"]}）：{r["current_text"]}'])
    for d in r['dimensions']:
        lines.append(f'{d["dimension"]} {d["coding_cell"]} A={d["original_A"]}, B={d["original_B"]}；复核={d["review_value"]}（建议={d["suggested_value"]}）；{d["classification"]}。{d["reason"]}')
        for c in d['contexts_used']: lines.append(f'  语境 {c["cell"]} {c["context_id"]}：{c["text"]}')
        if 'supplement_used' in d:
            s=d['supplement_used'];lines.append(f'  共同补材 {s["file"]} 第{s["line"]}行 {s["id"]}：'+''.join(s['quotes']))
    if r['rule_note']: lines.append('口径说明：'+r['rule_note'])
    if r['source_material_issue']: lines.append('交付问题：'+r['source_material_issue'])
    lines.append('')
(out/'semantic-review.txt').write_text('\n'.join(lines))
print(json.dumps(result['summary'],ensure_ascii=False))
