import json,sys,hashlib
from pathlib import Path
base=Path('outputs/ai-audit800-20261010/source-A/coder-A/materials')
out=Path('outputs/ai-audit800-20261010/reviews/part-001-267.jsonl')
for a in json.load(sys.stdin):
 i,vals,reasons=a[:3]; p=base/f'A-{i:06}.json'; d=json.loads(p.read_text()); r=d['source_record']; text=r['text']; extra=a[3] if len(a)>3 else {}
 j={}
 for k,v,reason in zip(['S','E','Ec','I','F'],vals,reasons):
  j[k]={'value':v,'evidence':text,'locator':'source_record.text；原文位置 '+str(r.get('source_ref',{}).get('locator',{})),'reason':reason}
  if k in extra: j[k].update(extra[k])
 record={'blind_id':f'A-{i:06}','source_id':r['id'],'source_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'judgments':j,'read_sources':[str(p)+'#source_record.text']+[str(p)+'#'+c['context_id'] for c in r.get('contexts',[]) if c.get('text')!=text and ('text' in c or 'headers' in c or 'row_cells' in c) and (i<25 or (not c.get('kind','').startswith('same_snapshot') and c.get('kind') not in ['source_fragment','document_context','ordered_members']))]+extra.get('read_sources',[]),'reviewer':'AI-Codex','review_status':'completed'}
 with out.open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
