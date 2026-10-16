import json, hashlib
from pathlib import Path
B=Path(__file__).resolve().parent
D=['S','E','Ec','I','F']
def emit(packet, specs):
 p=B/f'材料-{packet:02}.json'; material=json.loads(p.read_text()); out=[]
 assert len(specs)==len(material['rows'])
 for row,s in zip(material['rows'], specs):
  num,bits,reasons,ev,ist,fst,q,issues=s
  assert row['id']==f'AV3-C-{num:04}'
  labels=dict(zip(D,map(int,bits))) if bits!='待定' else dict.fromkeys(D,'待定')
  assert len(reasons)==5
  evidence=[]
  for dim,source,quote in ev:
   if source=='unit': assert quote in row['text'], (num,quote)
   else: assert quote in json.dumps(row['contexts'],ensure_ascii=False), (num,quote)
   evidence.append(dict(dimension=dim,source=source,quote=quote))
  for dim,v in labels.items():
   if v==1: assert any(x['dimension']==dim and x['source']=='unit' for x in evidence), (num,dim)
  assert bool(ist)==(labels['I']==1)
  assert bool(fst)==(labels['F']==1)
  out.append(dict(id=row['id'],labels=labels,dimension_reasons=dict(zip(D,reasons)),evidence=evidence,innovation_subtypes=ist,fairness_subtypes=fst,safety_quality_basis=q,issues=issues))
 target=B/f'结果-{packet:02}.json'
 with target.open('x') as f: json.dump(dict(coder='C',protocol_version='CAL-5D-20260926-v1.3',operational_version='v1.4',material_version='v9',input_packet_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),rows=out),f,ensure_ascii=False,indent=2)
 print(target.name,len(out))
