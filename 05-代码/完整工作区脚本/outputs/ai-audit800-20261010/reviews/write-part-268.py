import json,hashlib,sys
from pathlib import Path
root=Path('outputs/ai-audit800-20261010');p=root/'source-A/coder-A/materials';out=root/'reviews/part-268-534.jsonl'
rows=json.loads(sys.stdin.read())
with out.open('a') as f:
 for row in rows:
  n,vals,reasons,*extra=row
  d=json.loads((p/f'A-{n:06}.json').read_text());s=d['source_record']; ext=extra[0] if extra else {};ctx=ext.get('contexts',[]);extra_sources=ext.get('sources',[])
  r={'blind_id':f'A-{n:06}','source_id':s['id'],'source_text_sha256':hashlib.sha256(s['text'].encode()).hexdigest(),'judgments':{},'read_sources':[str(p/f'A-{n:06}.json')+'#source_record.text']+[str(p/f'A-{n:06}.json')+'#'+c for c in ctx]+extra_sources,'reviewer':'AI-Codex','review_status':'completed'}
  for k,v,reason in zip(['S','E','Ec','I','F'],vals,reasons):
   ev=ext.get('evidence',{}).get(k,s['text']);loc=ext.get('locator',{}).get(k,'当前命题')
   r['judgments'][k]={'value':v,'evidence':ev,'locator':loc,'reason':reason}
  if 'reuse' in ext:r['reuse_log']=ext['reuse']
  f.write(json.dumps(r,ensure_ascii=False)+'\n')
print('stored',len(rows))
