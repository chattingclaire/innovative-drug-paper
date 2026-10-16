import json, hashlib, pathlib
BASE=pathlib.Path(__file__).parent
DIMS=['S','E','Ec','I','F']
def row(n,labels,reasons,ev=(),I=(),F=(),q='no_quality_basis',issues=()):
 return {'id':f'AV3-A-{n:04d}','labels':dict(zip(DIMS,labels)),'dimension_reasons':dict(zip(DIMS,reasons)),'evidence':[{'dimension':d,'source':s,'quote':v} for d,s,v in ev],'innovation_subtypes':list(I),'fairness_subtypes':list(F),'safety_quality_basis':q,'issues':list(issues)}
def save(packet,rows):
 p=BASE/f'材料-{packet:02d}.json'; raw=p.read_bytes(); m=json.loads(raw)
 assert [r['id'] for r in rows]==[r['id'] for r in m['rows']]
 def strs(o):
  if isinstance(o,str): yield o
  elif isinstance(o,dict):
   for v in o.values(): yield from strs(v)
  elif isinstance(o,list):
   for v in o: yield from strs(v)
 for r,u in zip(rows,m['rows']):
  for d in DIMS:
   assert r['dimension_reasons'][d]
   if r['labels'][d]==1: assert any(e['dimension']==d and e['source']=='unit' for e in r['evidence']),(r['id'],d)
  for e in r['evidence']:
   hay=[u['text']] if e['source']=='unit' else list(strs(u['contexts']))
   assert any(e['quote'] in s for s in hay),(r['id'],e)
  assert bool(r['innovation_subtypes'])==(r['labels']['I']==1),r['id']
  assert bool(r['fairness_subtypes'])==(r['labels']['F']==1),r['id']
 out={'coder':'A','protocol_version':'CAL-5D-20260926-v1.3','operational_version':'v1.4','material_version':'v9','input_packet_sha256':hashlib.sha256(raw).hexdigest(),'rows':rows}
 with (BASE/f'结果-{packet:02d}.json').open('x') as f: json.dump(out,f,ensure_ascii=False,indent=2)
 print(f'首次提交 {packet:02d}: {len(rows)}条; SHA256={out["input_packet_sha256"]}; 引文/ID/子类结构核对通过')
