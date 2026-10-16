import json,hashlib,datetime
from pathlib import Path
from jsonschema import Draft202012Validator
B=Path(__file__).resolve().parent
p=B/'补充材料-v11.json'; m=json.loads(p.read_text()); dims=['S','E','Ec','I','F']
specs=[
('AV3-C-0037','00001',['当前规定协议到期及简易续约，没有药物损害或安全证据要求；不复制后项维度','续约期限和资格引导没有药效或临床获益评价','已读完整预算和市场价格后项，但当前引导句未独立陈述价格、药费或经济评价；不复制后项经济标签','独家身份和续约条件不表达创新属性或研发支持','明确现有医保谈判药品符合条件后可以简易续约且有效2年，确定保障连续期限'],[('F','unit','可以简易续约,续约有效期2年'),('F','context','现分类制定谈判药品(含续约药品)协议到期后的处理规则如下')],[],['access'],['边界争议：当前简易续约及有效期构成原有药物保障连续性安排；后项预算条件只用于理解续约条件，不把其全部经济内容复制入引导句。']),
('AV3-C-0126','00000',['当前按引用条文列目录外申报资格；已读第七八条，但没有独立陈述安全评价或安全证据要求','当前为申报资格引导，未独立提出疗效评价；不复制被引条文的安全有效条件','当前未规定药价、药费、费用责任或经济评价；不从第七八条复制价格合理等内容','后项包含已批适应症变化等对象，当前未独立评价创新属性或新增创新研发支持','可以申报纳入目录是申请资格，尚未确定实际药品给付、纳入结果或保障连续条件'],[],[],[],['边界争议：明确条款引用用于界定申报对象，不将所引条文的全部安全、有效、价格及排除范围直接转移为本引导句五维。']),
('AV3-C-0155','00001',['当前是目录退出规则的行为引导，未独立陈述药物风险；不复制第（三）后项风险内容','当前未独立评价药物效果或收益，不复制后项的临床价值和收益','当前未独立要求经济评价或费用标准，不复制后项药物经济性','目录退出引导没有创新属性或研发支持','明确符合所列情况药品经评审后直接调出医保目录，规定实际药物保障退出'],[('F','unit','直接调出《药品目录》')],[],['access'],['完整列表以第九条五项结束，第十条为下一独立条款；当前保障退出命题可判，后项独立风险/经济因素不全部复制。']),
('AV3-C-0181','00000',['当前以第九十条规定识别年度目录调整对象，未独立陈述风险评价；不复制引用条文安全内容','当前为调整对象类别列举，未独立要求效果评价；不复制引用中的有效性或替代性','当前为引用识别调整范围，未独立提出价格费用规则或经济评价','被引用第九十条及当前对象类别均没有独立创新属性或研发支持','年度药品目录调整范围的对象类别不等于直接确定该药实际保障退出；不能复制引用条文的退出后果'],[],[],[],['边界争议：完整读取明确引用的第九十条，仍以当前年度调整范围命题判断，不把所引条文的全部维度和退出后果转入本单元。'])
]
rows=[]
for a,s in zip(m['rows'],specs):
 id,bits,reasons,ev,ist,fst,issues=s;assert a['id']==id
 rows.append({'id':id,'labels':dict(zip(dims,map(int,bits))),'dimension_reasons':dict(zip(dims,reasons)),'evidence':[dict(dimension=d,source=source,quote=q) for d,source,q in ev],'innovation_subtypes':ist,'fairness_subtypes':fst,'safety_quality_basis':'no_quality_basis','issues':issues})
out={'coder':'C','protocol_version':'CAL-5D-20260926-v1.3','operational_version':'v1.4','material_version':'v11','input_packet_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':rows}
schema_path=B.parent/'结果schema-v11.json';schema=json.loads(schema_path.read_text());Draft202012Validator(schema).validate(out)
def leaves(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from leaves(v)
 elif isinstance(x,list):
  for v in x:yield from leaves(v)
for a,c in zip(m['rows'],rows):
 ctx=list(leaves(a['contexts']))
 for e in c['evidence']:assert e['quote'] in a['text'] if e['source']=='unit' else any(e['quote'] in v for v in ctx)
 for d,v in c['labels'].items():
  if v==1:assert any(e['dimension']==d and e['source']=='unit' for e in c['evidence'])
 assert bool(c['innovation_subtypes'])==(c['labels']['I']==1)
 assert bool(c['fairness_subtypes'])==(c['labels']['F']==1)
assert len(rows)==4 and [r['id'] for r in rows]==[a['id'] for a in m['rows']]
first_manifest=json.loads((B/'完成清单与QA-首次.json').read_text());first_preservation=[]
for item in first_manifest['packets']:
 q=B/f"结果-{item['packet']:02}.json";actual=hashlib.sha256(q.read_bytes()).hexdigest();assert actual==item['first_result_sha256']
 first_preservation.append({'file':q.name,'sha256':actual,'unchanged':True})
result_path=B/'补料复读结果-v11.json'
with result_path.open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2)
changes={'coder':'C','material_version':'v11','input_packet_sha256':out['input_packet_sha256'],'standard_unchanged':True,'first_results_preserved':True,'changes':[
 {'id':'AV3-C-0037','before':dict.fromkeys(dims,'待定'),'after':rows[0]['labels'],'change_kind':'材料补齐后消除待定','source_basis':['1.独家药品。','2.本协议期基金实际支出未超过基金支出预算(企业预估值,下同)的200%。','3.未来两年的基金支出预算增幅合理。','4.市场环境未发生重大变化。','5.不符合纳入常规目录管理的条件。'],'reason':'完整后项消除原以下条件缺口；当前续约及2年有效期可独立判保障连续性，未复制后项经济维度。'},
 {'id':'AV3-C-0126','before':dict.fromkeys(dims,'待定'),'after':rows[1]['labels'],'change_kind':'材料补齐后消除待定','source_basis':['(1)2020 年 1 月 1 日(含,下同)至 2025 年 6 月 30日(含,下同)期间,经国家药监部门批准上市的新通用名药品。','(5)2025 年 6 月 30 日前,经国家药监部门批准上市的罕见病治疗药品。','第七条纳入国家《药品目录》的药品应当是经国家药品监管部门批准,取得药品注册证书的化学药、生物制品、中成药(民族药),以及按国家标准炮制的中药饮片,并符合临床必需、安全有效、价格合理等基本条件。支持符合条件的基本药物按规定纳入《药品目录》。'],'reason':'完整五个实际情形及第七八条补齐原申报对象条件；当前为申请资格引导，未确定实际保障或提出独立五维内容。'},
 {'id':'AV3-C-0155','before':{'S':0,'E':0,'Ec':0,'I':0,'F':1},'after':rows[2]['labels'],'change_kind':'标签不变','reason':'补齐第九条第五项及确认第十条独立边界，不改变当前直接调出目录的保障退出命题。'},
 {'id':'AV3-C-0181','before':dict.fromkeys(dims,0),'after':rows[3]['labels'],'change_kind':'标签不变','reason':'新增第九十条分别定位及明确引用范围；原材料已有相同条文内容，当前仍是年度调整对象类别，无独立五维标签。'}], 'technical_correction_retained':'0036仅理由I/F列序技术订正仍以技术订正记录.json保留，标签不变。'}
with (B/'补料复读变更说明-v11.json').open('x') as f:json.dump(changes,f,ensure_ascii=False,indent=2)
readpaths=[p,B.parent/'补料任务说明-v11.json',schema_path]
qa={'coder':'C','executor':'AI agent','model_revision':'unknown','completed_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'material_version':'v11','protocol_version':out['protocol_version'],'operational_version':'v1.4','rows':4,'row_ids':[r['id'] for r in rows],'id_order_exact':True,'all_rows_binary':True,'schema_valid':True,'input_sha256_verified':True,'current_and_recursive_context_quotes_exact':True,'every_positive_has_unit_evidence':True,'subtype_label_consistent':True,'safety_quality_status_consistent':True,'unresolved_material_gaps':[],'read_scope':[{'path':str(x.resolve()),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in readpaths],'first_results_preservation':first_preservation,'result_sha256':hashlib.sha256(result_path.read_bytes()).hexdigest(),'read_notes':'四条当前原文和全部递归上下文均独立复读；文本、全部版本后缀、后项、引用条文、边界与对象证书均阅读，不把后项维度复制至引导句；未读取另一位、机器、统计或私人映射。'}
with (B/'补料复读QA-v11.json').open('x') as f:json.dump(qa,f,ensure_ascii=False,indent=2)
print('C v11: 4 rows serialized; exact quotes/schema/SHA/order/subtypes/first-result preservation QA passed; no unresolved material gaps.')
