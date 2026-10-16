import json,sys
from pathlib import Path
out=Path(__file__).parent
rows=json.loads(sys.stdin.read())
res=[]
for n,values,*reasons in rows:
 assert len(values)==5 and len(reasons)==5
 res.append({'blind_id':f'A-{n:03d}','judgments':{d:{'value':None if v=='?' else int(v),'reason':r} for d,v,r in zip(['S','E','Ec','I','F'],values,reasons)}})
f=out/f'batch_{rows[0][0]:03d}_{rows[-1][0]:03d}.json';f.write_text(json.dumps(res,ensure_ascii=False,indent=2));print(f.name,len(res))
