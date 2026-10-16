import json,hashlib,pathlib,datetime
from zoneinfo import ZoneInfo
import jsonschema
B=pathlib.Path(__file__).parent
P=B.parent.parent/'protocol'
S=json.loads((B.parent/'结果schema.json').read_text())
D=['S','E','Ec','I','F']
def leaves(x,path=''):
 if isinstance(x,str): yield path,x
 elif isinstance(x,dict):
  for k,v in x.items(): yield from leaves(v,path+'.'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x): yield from leaves(v,path+f'[{i}]')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
packets=[];ids=[];pending=[];evidence_audit=[]
for n in range(1,9):
 inp=B/f'材料-{n:02d}.json';out=B/f'结果-{n:02d}.json'
 m=json.loads(inp.read_text());r=json.loads(out.read_text());jsonschema.validate(r,S)
 assert r['input_packet_sha256']==h(inp)
 assert [x['id'] for x in m['rows']]==[x['id'] for x in r['rows']]
 assert len(r['rows'])==30
 for u,v in zip(m['rows'],r['rows']):
  ids.append(v['id']); assert set(v['labels'])==set(D)
  assert all(v['dimension_reasons'][d].strip() for d in D)
  assert bool(v['innovation_subtypes'])==(v['labels']['I']==1)
  assert bool(v['fairness_subtypes'])==(v['labels']['F']==1)
  if '待定' in v['labels'].values():
   assert all(z=='待定' for z in v['labels'].values());assert v['safety_quality_basis']=='undetermined';assert v['issues'];pending.append(v['id'])
  else:assert v['safety_quality_basis']!='undetermined'
  if v['safety_quality_basis'] in ['quality_only','quality_and_other']:assert v['labels']['S']==1
  for d in D:
   if v['labels'][d]==1:assert any(e['dimension']==d and e['source']=='unit' for e in v['evidence'])
  for e in v['evidence']:
   if e['source']=='unit':matches=['text'] if e['quote'] in u['text'] else []
   else:matches=[p for p,s in leaves(u['contexts'],'contexts') if e['quote'] in s]
   assert matches,(v['id'],e)
   evidence_audit.append({'id':v['id'],**e,'matched_paths':matches})
 packets.append({'packet':n,'rows':30,'input_sha256':h(inp),'first_result_sha256':h(out),'first_result_time_local':datetime.datetime.fromtimestamp(out.stat().st_mtime,ZoneInfo('Asia/Shanghai')).isoformat(),'schema':'passed','id_order':'passed','verbatim_evidence':'passed','subtypes_and_quality':'passed'})
assert ids==[f'AV3-A-{n:04d}' for n in range(1,241)]
files=[P/'完整五维手册-v1.3.md',P/'共用操作说明-v1.4.md',B.parent/'任务说明.md',B.parent/'结果schema.json',B/'任务说明.md']+[B/f'材料-{n:02d}.json' for n in range(1,9)]
report={'coder':'A','executor_identity':'AI agent；不代表真人编码员验证','model_revision':'Codex / 基于GPT-6；具体底层模型修订号未知','protocol_version':'CAL-5D-20260926-v1.3','operational_version':'v1.4','material_version':'v9','qa_completed_at_local':datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'coverage':{'packets':8,'rows':240,'dimension_records':1200,'all_ids_in_original_order':True,'each_row_current_text_and_recursive_context_semantics_reviewed':True},'pending_material_ids':pending,'packets':packets,'reading_range':[{'path':str(p.resolve()),'sha256':h(p)} for p in files],'qa':{'json_schema':'passed','input_packet_sha256':'passed','id_coverage_order':'passed','five_dimension_reasons':'passed','every_positive_has_verbatim_current_unit_quote':'passed','context_quotes_match_recursive_context_strings':'passed','innovation_subtype_presence':'passed','fairness_subtype_presence':'passed','safety_quality_marker_structure':'passed'},'semantic_qa_note':'逐条语义由本AI独立判读；程序仅显示材料、序列化已作判断及核对ID、SHA、逐字引文、schema与子类结构，未用词表、正则或脚本产生标签及理由。子类依据已逐条人工流程复核；结构核对不证明语义无误。','blindness_note':'未读取其他编码员或机器判定。政策措辞及source_title可透露来源，不能称来源身份完全盲法；同源相邻/父级语境可能曾被接触。本批不是新政策文件外部验证。','excluded_reading':'未读取admin、agent-C、reference、statistics、机器规则/提示/结果、旧训练答案或论文结论；来源定位器仅作随包语境元数据，未打开所链接来源。','preservation':'结果-01至08为首次提交，独占创建，未覆盖；补料复读须另存。'}
with (B/'完成清单及QA.json').open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)
with (B/'逐字引文核对.json').open('x') as f:json.dump(evidence_audit,f,ensure_ascii=False,indent=2)
print(json.dumps({'qa':'passed','rows':len(ids),'packets':8,'pending_material_ids':pending,'completed_at_local':report['qa_completed_at_local']},ensure_ascii=False))
