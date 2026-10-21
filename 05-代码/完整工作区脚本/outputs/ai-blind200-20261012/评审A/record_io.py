from pathlib import Path
import json, sys
BASE=Path('/PROJECT_ROOT/outputs/goal-calibration-20261010/09-delivery/human200-independent-preparation-root/coder-A')
OUT=Path(__file__).parent
ORDER=json.loads((OUT/'order.json').read_text())
def read(a,b):
 for n in range(a,b+1):
  bid=ORDER[n-1];d=json.loads((BASE/'materials'/f'{bid}.json').read_text());r=d['source_record']
  print(f'\nITEM {n} {bid}\nCURRENT: {r["text"]}')
  seen=set()
  for i,c in enumerate(r['contexts'][:3]):
   t=c.get('text','')
   if t and t not in seen:
    print(f'C{i} {c["context_id"]}: {t}');seen.add(t)
  print('EXTRA_CONTEXTS',[(i,c.get('context_id'),len(c.get('text',''))) for i,c in enumerate(r['contexts']) if i>=3]); print('RESOURCE_FIELDS',[(k,len(v)) for k,v in d.items() if isinstance(v,list) and v and k!='source_documents'])
def append(rows):
 path=OUT/'judgments.jsonl';existing=[json.loads(x)['blind_id'] for x in path.read_text().splitlines()] if path.exists() else []
 with path.open('a') as f:
  for row in rows:
   n,vals,reasons,ctx=row
   bid=ORDER[n-1];assert bid not in existing
   assert n==len(existing)+1,(n,len(existing))
   r=json.loads((BASE/'materials'/f'{bid}.json').read_text())['source_record']
   answer={'blind_id':bid,'judgments':{}}
   for i,dim in enumerate(['S','E','Ec','I','F']):
    indices=ctx.get(dim,ctx.get('*',[]))
    contexts=[k if isinstance(k,dict) else {'context_id':r['contexts'][k]['context_id'],'quote':r['contexts'][k]['text'],'locator':r['contexts'][k].get('source_ref',{}).get('locator',{})} for k in indices]
    answer['judgments'][dim]={'value':vals[i],'evidence':r['text'],'context':{'material':f'coder-A/materials/{bid}.json','current_locator':r['source_ref']['locator'],'used_contexts':contexts},'reason':reasons[i]}
   f.write(json.dumps(answer,ensure_ascii=False)+'\n');f.flush();existing.append(bid)
 print('Saved',len(existing),'records')
if __name__=='__main__':
 if sys.argv[1]=='read':read(int(sys.argv[2]),int(sys.argv[3]))
 elif sys.argv[1]=='append':append(json.load(sys.stdin))
