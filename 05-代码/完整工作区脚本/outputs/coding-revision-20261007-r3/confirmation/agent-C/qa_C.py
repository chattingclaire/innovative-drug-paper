import json,hashlib,datetime
from pathlib import Path
from jsonschema import Draft202012Validator
B=Path(__file__).resolve().parent
schema=json.loads((B.parent/'结果schema.json').read_text())
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
errors=[];packets=[];subtype_evidence=[];allids=[]
for i in range(1,9):
 inp=B/f'材料-{i:02}.json';res=B/f'结果-{i:02}.json';m=json.loads(inp.read_text());r=json.loads(res.read_text())
 for e in Draft202012Validator(schema).iter_errors(r):errors.append(f'{i}: {e.message}')
 assert r['input_packet_sha256']==hashlib.sha256(inp.read_bytes()).hexdigest()
 assert [x['id'] for x in r['rows']]==[x['id'] for x in m['rows']]
 assert len(r['rows'])==30
 for a,c in zip(m['rows'],r['rows']):
  allids.append(c['id']);ctx=list(strings(a['contexts']))
  for e in c['evidence']:
   assert e['quote'] in a['text'] if e['source']=='unit' else any(e['quote'] in z for z in ctx),(c['id'],e)
  for d,v in c['labels'].items():
   if v==1:assert any(e['dimension']==d and e['source']=='unit' for e in c['evidence'])
  assert bool(c['innovation_subtypes'])==(c['labels']['I']==1)
  assert bool(c['fairness_subtypes'])==(c['labels']['F']==1)
  if c['labels']['S']=='待定':assert c['safety_quality_basis']=='undetermined'
  else:assert c['safety_quality_basis']!='undetermined'
  if c['innovation_subtypes'] or c['fairness_subtypes']:
   subtype_evidence.append({'id':c['id'],'innovation_subtypes':c['innovation_subtypes'],'fairness_subtypes':c['fairness_subtypes'],'evidence':[e for e in c['evidence'] if e['dimension'] in ('I','F')]})
 packets.append({'packet':i,'rows':len(r['rows']),'input_sha256':hashlib.sha256(inp.read_bytes()).hexdigest(),'first_result_sha256':hashlib.sha256(res.read_bytes()).hexdigest(),'id_order_exact':True,'schema_valid':True,'all_positive_unit_quotes_exact':True,'all_context_quotes_exact_recursive_leaf':True,'subtype_label_consistent':True,'safety_quality_status_consistent':True})
assert not errors,errors
assert len(set(allids))==240
readpaths=[B.parent.parent/'protocol/完整五维手册-v1.3.md',B.parent.parent/'protocol/共用操作说明-v1.4.md',B.parent/'任务说明.md',B.parent/'结果schema.json',B/'任务说明.md']+[B/f'材料-{i:02}.json' for i in range(1,9)]
qa={'coder':'C','executor':'AI agent','model':'GPT-6 family; concrete underlying model revision unavailable','completed_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'protocol_version':'CAL-5D-20260926-v1.3','operational_version':'v1.4','material_version':'v9','first_submission_preserved':True,'read_scope':[{'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in readpaths],'packets':packets,'total_rows':240,'unresolved_material_ids':['AV3-C-0037','AV3-C-0126'],'technical_corrections_file':'技术订正记录.json','technical_corrections_change_labels':False,'subtype_evidence_trace':subtype_evidence,'workflow_notes':['All current texts and recursive textual contexts were individually read, including all supplied version-suffixed context branches, parent predicates, following items, document object certificates, and table headers/cells. Exact duplicate text was displayed again or identified by its context path. Context metadata and string-array cells were also reviewed.','Labels and five-dimension reasons were semantically authored row by row by this AI agent; programs only displayed source text, serialized author judgments, and checked IDs, schema, literal evidence and SHA256.','No other coder, machine result, admin, reference, statistics, training answer, or paper conclusion was accessed. Source titles and policy wording remained visible; source identity was not completely blinded.','No expected positive rates, ordering, agreement statistics, precision, recall or F1 were used to produce judgments.']}
with (B/'完成清单与QA-首次.json').open('x') as f:json.dump(qa,f,ensure_ascii=False,indent=2)
print('240 rows: schema, order, SHA256, literal evidence and subtype/quality consistency checks passed; 0037 and 0126 await symmetric supplementation.')
