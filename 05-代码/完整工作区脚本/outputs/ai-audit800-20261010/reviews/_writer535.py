import json,hashlib
from pathlib import Path
ROOT=Path('outputs/ai-audit800-20261010/source-A/coder-A/materials')
OUT=Path('outputs/ai-audit800-20261010/reviews/part-535-800.jsonl')
DIMS=['S','E','Ec','I','F']
MISSING=['药物损害或风险控制','药物效果或获益证据','药品费用或支付内容','技术新颖改良或创新研发支持','患者负担能力或按需获取差异']
def save(rows):
 with OUT.open('a') as out:
  for n,vals,focus,overrides,*extra in rows:
   p=ROOT/f'A-{n:06}.json'; d=json.load(p.open());r=d['source_record'];ctx=extra[0] if extra else {}
   j={}
   for i,k in enumerate(DIMS):
    j[k]={'value':vals[i], 'evidence':r['text'], 'locator':'当前命题；source_record.source_ref.locator='+json.dumps(r['source_ref']['locator'],ensure_ascii=False), 'reason':overrides.get(k,f'当前为{focus}，未表达{MISSING[i]}。')}
    if k in ctx:
     for cid in ctx[k]:
      c=next(c for c in r['contexts'] if c['context_id']==cid)
      j[k]['evidence']+='\n'+c['text'];j[k]['locator']+='；'+cid
   out.write(json.dumps({'blind_id':f'A-{n:06}','source_id':r['id'],'source_text_sha256':hashlib.sha256(r['text'].encode()).hexdigest(),'judgments':j,'read_sources':[str(p)+'#source_record.text']+[str(p)+'#'+c for c in dict.fromkeys(y for x in ctx.values() for y in x)],'reviewer':'AI-Codex','review_status':'completed'},ensure_ascii=False)+'\n')
 print('saved',len(rows),rows[0][0],rows[-1][0])
