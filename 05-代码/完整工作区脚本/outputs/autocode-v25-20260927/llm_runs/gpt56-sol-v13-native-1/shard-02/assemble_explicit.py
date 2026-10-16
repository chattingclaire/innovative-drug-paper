import json,sys
from pathlib import Path
D=['S','E','Ec','I','F']
ZR={'S':'本单元未实质讨论药物或用药安全。','E':'本单元未实质讨论药物疗效或临床获益。','Ec':'本单元未实质讨论药品价格、费用或支付资源。','I':'本单元未实质讨论药物创新属性或研发创新支持。','F':'本单元未实质讨论药品保障获取、患者负担或临床管理难度。'}
def build(inp,spec):
 out=[]
 for src,x in zip(inp,spec):
  assert src['id']==x['id']
  labs=dict(zip(D,x['labels']))
  rs={d:ZR[d] for d in D};rs.update(x.get('reasons',{}))
  ev=[]
  for d,q in x.get('evidence',{}).items(): ev.append({'dimension':d,'source':'unit','quote':q})
  out.append({'id':x['id'],'labels':labs,'dimension_reasons':rs,'evidence':ev,'material_issue':x.get('issue',''),'fairness_subtypes':x.get('fsub',[]),'innovation_subtypes':x.get('isub',[]),'safety_quality_basis':x.get('sq','undetermined' if '待定' in labs.values() else 'no_quality_basis')})
 return {'protocol_version':'CAL-5D-20260926-v1.3','rows':out}
if __name__=='__main__':
 p=Path(sys.argv[1]);s=Path(sys.argv[2]);o=Path(sys.argv[3])
 inp=json.loads(p.read_text())['rows'];spec=json.loads(s.read_text())
 o.write_text(json.dumps(build(inp,spec),ensure_ascii=False,indent=2)+'\n')
