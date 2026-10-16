import json,sys
from pathlib import Path
base=Path(__file__).resolve().parent
for n in range(int(sys.argv[1]),int(sys.argv[2])+1):
 bid=f'A-{n:06}'
 p=base/'source-A/coder-A/materials'/f'{bid}.json'
 d=json.loads(p.read_text());r=d['source_record']
 print('\n'+bid+' '+r['id']+' pages='+str(r['pages']))
 print('当前：'+r['text'])
 for c in r.get('contexts',[]):
  if c.get('kind','').startswith('same_snapshot_') and '--supplements' not in sys.argv: continue
  if 'text' not in c:print(c.get('context_id','')+' '+c.get('kind','')+': '+json.dumps(c.get('structure',{}),ensure_ascii=False))
  elif c['text']!=r['text']:print(c['context_id']+' '+c['kind']+': '+c['text'])
 for k in ['source_full_text_resources','source_reference_index','source_provenance_addenda','explicit_or_primary_source_resources','preserved_historical_neutral_source_supplements']:
  if d.get(k):
   if '--resources' in sys.argv:print(k+': '+json.dumps(d[k],ensure_ascii=False))
   else:print(k+': 存在'+str(len(d[k]))+'项，未在本次输出全文；若需要按确指关系另读。')
