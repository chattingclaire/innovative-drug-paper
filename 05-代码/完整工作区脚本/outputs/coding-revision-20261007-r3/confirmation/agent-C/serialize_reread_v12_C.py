import json,hashlib,datetime
from pathlib import Path
from jsonschema import Draft202012Validator
B=Path(__file__).resolve().parent; p=B/'补充材料-v12.json';m=json.loads(p.read_text());D=['S','E','Ec','I','F']
protected=[B/f'结果-{i:02}.json' for i in range(1,9)]+[B/'补料复读结果-v11.json',B/'补料复读变更说明-v11.json',B/'补料复读QA-v11.json',B/'技术订正记录.json']
before={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in protected}
rows=[
{'id':'AV3-C-0169','labels':{'S':0,'E':0,'Ec':0,'I':1,'F':0},'dimension_reasons':{'S':'当前表行实质规定改良型生物制品及特定新适应症的数据保护期限；所引第七条与第五条的安全性数据范围用于消解权利适用条件，不把其安全证明内容复制为本行独立风险评价。','E':'当前表行未独立讨论治疗效果、临床优势或要求效果评价；已完整阅读所引有效性试验数据范围，不把被引段落的有效性内容直接转移为本行标签。','Ec':'4年或6年为专有数据保护时间，没有药价、药费、治疗成本或支付责任。','I':'明确将改良型生物制品的注册属性与4年保护期对应，并规定特定新适应症按明确引用条件适用6年保护期，属于药物属性及专有试验数据权利范围和期限。','F':'境外已上市境内未上市为数据保护适用身份；当前没有明确急需且缺乏治疗选择的获取缺口、给付供应安排、患者负担或药物管理难度。'},'evidence':[{'dimension':'I','source':'unit','quote':'改良型生物制品'},{'dimension':'I','source':'unit','quote':'并符合本办法第七条第一款的，数据保护期为6年。'},{'dimension':'I','source':'context','quote':'治疗用生物制品注册分类和数据保护期；列名：分类 | 内容 | 数据保护期 | 备注'},{'dimension':'I','source':'context','quote':'对全部试验数据给予6年数据保护期。'}],'innovation_subtypes':['attribute'],'fairness_subtypes':[],'safety_quality_basis':'no_quality_basis','issues':['边界争议：所引第七条及再引第五条完整解释权利适用条件和保护范围；当前表行命题仍为分类及保护期限，不复制被引安全性、有效性数据范围的全部维度。']},
{'id':'AV3-C-0209','labels':{'S':0,'E':0,'Ec':0,'I':0,'F':0},'dimension_reasons':{'S':'完整第五条明确药师职称、调剂经验及岗位培训资格；当前审核人员资格符合性未实质讨论药物损害或风险证据。','E':'人员资格、3年经验和培训考核不等于药物疗效或临床获益评价。','Ec':'人员资格要求没有药价、药费、药品支付或治疗成本内容。','I':'人员职称和经验培训符合性不是药物创新属性、创新资格或针对创新药研发的实体支持。','F':'当前为一般处方审核人员资质管理，没有实际药物保障范围、患者药费负担或药品使用复杂性和监测负担评价。'},'evidence':[],'innovation_subtypes':[],'fairness_subtypes':[],'safety_quality_basis':'no_quality_basis','issues':[]}
]
assert [r['id'] for r in rows]==[r['id'] for r in m['rows']]
out={'coder':'C','protocol_version':'CAL-5D-20260926-v1.3','operational_version':'v1.4','material_version':'v12','input_packet_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':rows}
schema_path=B.parent/'结果schema-v12.json';Draft202012Validator(json.loads(schema_path.read_text())).validate(out)
def leaves(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from leaves(v)
 elif isinstance(x,list):
  for v in x:yield from leaves(v)
for a,r in zip(m['rows'],rows):
 ctx=list(leaves(a['contexts']))
 for e in r['evidence']:assert e['quote'] in a['text'] if e['source']=='unit' else any(e['quote'] in x for x in ctx)
 for d,v in r['labels'].items():
  if v==1:assert any(e['dimension']==d and e['source']=='unit' for e in r['evidence'])
 assert bool(r['innovation_subtypes'])==(r['labels']['I']==1)
 assert bool(r['fairness_subtypes'])==(r['labels']['F']==1)
result=B/'补料复读结果-v12.json'
with result.open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2)
changes={'coder':'C','material_version':'v12','input_packet_sha256':out['input_packet_sha256'],'standard_unchanged':True,'first_results_preserved':True,'changes':[{'id':'AV3-C-0169','before':{'S':0,'E':0,'Ec':0,'I':1,'F':0},'after':rows[0]['labels'],'change_kind':'标签和子类不变，独立复读理由更新','source_basis':['第七条 境外已上市境内未上市的原研药品,首次提交境内外均未获批的新适应症的注册申请,并提交本办法第五条第三款规定的用于证明药品安全性、有效性和质量可控性的全部试验数据的,按照本办法第五条执行,对全部试验数据给予6年数据保护期。','本条款中药品的数据保护范围包括药品上市许可申报资料中用于证明药品安全性、有效性和质量可控性的全部试验数据。'],'reason':'新增明确引用及再引用范围，完整解释6年权利条件；当前仍为改良注册属性和保护期限，未将所引安全/有效内容整段复制。'},{'id':'AV3-C-0209','before':dict.fromkeys(D,0),'after':rows[1]['labels'],'change_kind':'标签不变，独立复读理由更新','source_basis':['(一)取得药师及以上药学专业技术职务任职资格。','(二)具有3年及以上门急诊或病区处方调剂工作经验,接受过处方审核相应岗位的专业知识培训并考核合格。'],'reason':'明确第五条为职称、经验和岗位培训资质；未产生五维实质命题。'}]}
with (B/'补料复读变更说明-v12.json').open('x') as f:json.dump(changes,f,ensure_ascii=False,indent=2)
for x in protected:assert hashlib.sha256(x.read_bytes()).hexdigest()==before[x.name]
qa={'coder':'C','executor':'AI agent','model_revision':'unknown','completed_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'material_version':'v12','protocol_version':out['protocol_version'],'operational_version':'v1.4','rows':2,'row_ids':[r['id'] for r in rows],'id_order_exact':True,'all_rows_binary':True,'schema_valid':True,'input_sha256_verified':True,'current_and_recursive_context_quotes_exact':True,'every_positive_has_unit_evidence':True,'subtype_label_consistent':True,'safety_quality_status_consistent':True,'unresolved_material_gaps':[],'read_scope':[{'path':str(x.resolve()),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in [p,B.parent/'补料任务说明-v12.json',schema_path]],'result_sha256':hashlib.sha256(result.read_bytes()).hexdigest(),'protected_files_unchanged':[{'file':x.name,'sha256':before[x.name],'unchanged':True} for x in protected],'read_notes':'完整阅读两条当前正文及全部递归语境、表头/列值、明确引用及再引用、来源和边界证书；未读另一位、机器、统计或私人映射。判断为本AI agent逐条语义判读，程序仅序列化及技术校验。'}
with (B/'补料复读QA-v12.json').open('x') as f:json.dump(qa,f,ensure_ascii=False,indent=2)
print('C v12: 2 rows complete; both label vectors retained; literal evidence, schema, SHA, order, subtype and protected-file preservation QA passed.')
